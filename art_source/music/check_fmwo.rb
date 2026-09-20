# check_fmwo.rb — run a Project FMWO theme silently and prove it is sound.
#
# Lineage: check_theme.rb hard-coded Eric's loop names and a hand-typed opt
# table; harness.rb simulated bars but never looked at an opt; check_theme2.rb
# merged them and had the good idea of reading Sonic Pi's own synthinfo.rb
# instead of transcribing it, which this keeps.
#
# THIS FILE DELIBERATELY DISAGREES WITH check_theme2.rb ON TWO POINTS, because
# both were measured against the installed Sonic Pi 5.0.0 rather than reasoned
# about. Keeping the wrong model would hide the largest bug in the two themes.
#
#   1. CROSS-THREAD TICKS ARE NOT A RACE. check_theme2.rb models tick counters
#      as shared between live_loops and calls a foreign read "rare, and
#      invisible in a listen". eric_theme_v3.rb calls it "a same-timestep read
#      race between threads". Both are wrong, and the truth is much worse.
#      In sonicpi/core.rb, ThreadLocalCounter.get_or_create_counters stores the
#      counter hash with __thread_locals.set_local — the NON-inherited variant —
#      and look returns (val || 0). Measured, two threads, real engine code:
#           thread that ticks :bar eight times   look(:bar) => 7
#           any other live_loop                  look(:bar) => 0
#           a thread spawned from the ticker     look(:bar) => 0
#      So `bar = look(:bar) % 16` in a loop that does not tick :bar itself is
#      not occasionally off by one. It is pinned to 0 for the life of the
#      track, every run, deterministically. Every `if bar >= 8` under it is
#      dead code and every `if bar == 15` never fires. That is why this file
#      simulates each live_loop with its OWN counters, and why it runs each
#      loop twice — once as Sonic Pi really behaves, once as the comments
#      assume — and diffs the two performances.
#
#   2. A WHOLE-NUMBER FLOAT IN AN ENUMERATED OPT IS NOT TRUNCATED TO A
#      DIFFERENT SOURCE. eric_theme_v3.rb says a fractional value "gets
#      truncated to a different source instead of raising". It is the other way
#      round. Measured against :hollow's real validator:
#           noise: 1    Integer -> accepted
#           noise: 1.0  Float   -> accepted, same source (Array#include?, 1.0 == 1)
#           noise: 0.5  Float   -> RAISES "must be one of [0,1,2,3,4]"
#           noise: 2.5  Float   -> RAISES
#           noise: 5    Integer -> RAISES
#      A raise inside a live_loop kills that loop and only that loop; the rest
#      of the track plays on, so the recording sounds fine and is silently
#      missing a layer. So: fractional float = ERROR (this is the shipping bug),
#      whole-number float = WARNING (harmless today, one edit from fatal).
#
# WHAT IT CHECKS
#   1. Tick scoping, as above, statically and by divergence of the two runs.
#   2. Bar arithmetic: every iteration a whole number of bars, one cycle 64.
#   3. Opt names, per synth/fx/sample, from Sonic Pi's own arg_info.
#   4. Enumerated opts (bounds[:options]) get Integers that are members.
#   5. Numeric bounds (e.g. tb303 cutoff <= 130).
#   6. Note names resolve, and land inside MIDI 0..127.
#   7. Sample names exist in the installed sample pack.
#
# USAGE
#   ruby check_fmwo.rb --selftest            # negative control; run this first
#   ruby check_fmwo.rb <theme.rb> [...]

SONIC_PI = 'C:/Program Files/Sonic Pi/app/server/ruby'
$LOAD_PATH.unshift SONIC_PI, "#{SONIC_PI}/lib"
require 'sonicpi/synths/synthinfo'
require 'stringio'
require 'tmpdir'
SI = SonicPi::Synths::SynthInfo

# ---------------------------------------------------------------- opt tables
TABLE = {}
(SI.all_synths + SI.all_fx.map { |f| :"fx_#{f}" }).each do |n|
  info = begin
    SI.get_info(n)
  rescue StandardError
    nil
  end
  next unless info
  ai = info.arg_info
  opts = ai.keys.to_a
  ai.each { |k, s| opts += [:"#{k}_slide", :"#{k}_slide_shape", :"#{k}_slide_curve"] if s[:modulatable] }
  TABLE[n] = {
    opts: opts.uniq,
    enums: ai.each_with_object({}) { |(k, s), h| h[k] = s[:bounds][:options] if s[:bounds].is_a?(Hash) && s[:bounds][:options] },
    bounds: ai.each_with_object({}) { |(k, s), h| h[k] = s[:bounds] if s[:bounds].is_a?(Hash) && (s[:bounds][:min] || s[:bounds][:max]) }
  }
end

SAMPLE_OPTS = begin
  base = %i[mono_player stereo_player basic_mono_player basic_stereo_player].flat_map do |n|
    i = begin
      SI.get_info(n)
    rescue StandardError
      nil
    end
    i ? i.arg_info.keys.to_a : []
  end
  (base + base.map { |k| :"#{k}_slide" } +
   %i[rate beat_stretch pitch_stretch rpitch onset num_slices slice on path]).uniq
end

SAMPLE_NAMES = Dir.glob("#{File.dirname(SONIC_PI)}/../../etc/samples/*.flac")
                  .map { |p| File.basename(p, '.flac').to_sym }

LETTER = { 'c' => 0, 'd' => 2, 'e' => 4, 'f' => 5, 'g' => 7, 'a' => 9, 'b' => 11 }.freeze
NOTE_RE = /\A([a-g])([sb#]*)(-?\d+)?\z/

def midi_of(x)
  return x if x.is_a?(Numeric)
  m = x.to_s.downcase.match(NOTE_RE) or raise "bad note name #{x.inspect}"
  v = LETTER[m[1]]
  m[2].each_char { |c| v += (c == 's' || c == '#') ? 1 : -1 }
  v + ((m[3] || '4').to_i + 1) * 12
end

class Symbol
  def +(o); midi_of(self) + (o.is_a?(Symbol) ? midi_of(o) : o); end
  def -(o); midi_of(self) - (o.is_a?(Symbol) ? midi_of(o) : o); end
end

class Node; end

class Ring
  include Enumerable
  def initialize(a, h); @a = a; @h = h; end
  def [](i); @a[i.to_i % @a.size]; end
  def each(&b); @a.each(&b); end
  def size; @a.size; end
  def to_a; @a.dup; end
  def tick(k = :__default__); @a[@h.tick(k) % @a.size]; end
  def look(k = :__default__); @a[@h.look(k) % @a.size]; end
end

class Checker
  attr_reader :loops, :problems

  def initialize
    @loops = {}
    @problems = []
    @synth = :beep
    @acc = 0.0        # beats slept inside the current iteration
    @elapsed = 0.0    # beats completed in earlier iterations of this loop
    @counters = {}    # THIS loop's tick counters: key => [look_val, next_val]
    @mode = :written
    @log = []
    @where = 'top level'
  end

  def err(m);   @problems << [:error, "#{@where}: #{m}"]; end
  def warn!(m); @problems << [:warn,  "#{@where}: #{m}"]; end

  # -------------------------------------------------------------- DSL stubs
  def use_bpm(*); end
  def use_octave(*); end
  def use_transpose(*); end
  def comment(*); end
  def live_loop(name, **_o, &blk); @loops[name] = blk; end
  def define(name, &blk); define_singleton_method(name, &blk); end
  def one_in(_n); false; end
  def rrand(a, b); (a + b) / 2.0; end
  def rrand_i(a, b); ((a + b) / 2).to_i; end
  def dice(_n = 6); 3; end
  def choose(a); a.respond_to?(:to_a) ? a.to_a.first : a; end
  def ring(*a); Ring.new(a.flatten(0), self); end
  def knit(*a); Ring.new(a.each_slice(2).flat_map { |v, n| [v] * n }, self); end
  def note(x); x.nil? ? nil : midi_of(x); end

  QUAL = { major: [0, 4, 7], minor: [0, 3, 7], diminished: [0, 3, 6], dim: [0, 3, 6],
           augmented: [0, 4, 8], aug: [0, 4, 8], major7: [0, 4, 7, 11], M7: [0, 4, 7, 11],
           minor7: [0, 3, 7, 10], m7: [0, 3, 7, 10], dom7: [0, 4, 7, 10],
           minor_major7: [0, 3, 7, 11], half_diminished: [0, 3, 6, 10], dim7: [0, 3, 6, 9],
           sus2: [0, 2, 7], sus4: [0, 5, 7], '5': [0, 7], '1': [0] }.freeze
  MODE = { major: [0, 2, 4, 5, 7, 9, 11], minor: [0, 2, 3, 5, 7, 8, 10],
           aeolian: [0, 2, 3, 5, 7, 8, 10], phrygian: [0, 1, 3, 5, 7, 8, 10],
           dorian: [0, 2, 3, 5, 7, 9, 10], lydian: [0, 2, 4, 6, 7, 9, 11],
           mixolydian: [0, 2, 4, 5, 7, 9, 10], locrian: [0, 1, 3, 5, 6, 8, 10],
           harmonic_minor: [0, 2, 3, 5, 7, 8, 11], minor_pentatonic: [0, 3, 5, 7, 10],
           major_pentatonic: [0, 2, 4, 7, 9], blues_minor: [0, 3, 5, 6, 7, 10],
           whole_tone: [0, 2, 4, 6, 8, 10], chromatic: (0..11).to_a }.freeze

  def chord(root, quality = :major, **_o)
    iv = QUAL[quality]
    (err("unknown chord quality #{quality.inspect}"); iv = [0, 4, 7]) unless iv
    Ring.new(iv.map { |i| midi_of(root) + i }, self)
  end

  def scale(root, name = :major, num_octaves: 1, **_o)
    iv = MODE[name]
    (err("unknown scale #{name.inspect}"); iv = MODE[:major]) unless iv
    all = (0...num_octaves).flat_map { |o| iv.map { |i| midi_of(root) + i + o * 12 } }
    Ring.new(all + [midi_of(root) + num_octaves * 12], self)
  end

  def use_synth(s)
    err("unknown synth #{s.inspect}") unless TABLE.key?(s)
    @synth = s
  end

  def sleep(n)
    return err("non-numeric sleep #{n.inspect}") unless n.is_a?(Numeric)
    err("negative sleep #{n}") if n < 0
    @acc += n
  end

  # Faithful Sonic Pi semantics: counters are per-live_loop and not inherited;
  # the first tick returns 0; look on an un-ticked key returns 0.
  def tick(k = :__default__, **_o)
    if @counters[k]
      _, nxt = @counters[k]
      @counters[k] = [nxt, nxt + 1]
      nxt
    else
      @counters[k] = [0, 1]
      0
    end
  end

  def look(k = :__default__, **_o)
    return @counters[k][0] if @counters[k]
    # Un-ticked in this loop. Sonic Pi returns 0. :intended asks the other
    # question — what the file's comments assume this would have been.
    @mode == :intended ? ((@elapsed + @acc) / 4).floor % 16 : 0
  end

  def play(n, *_r, **opts)
    check_notes(n)
    check_opts("play on :#{@synth}", @synth, opts)
    @log << [:play, Array(n).map { |x| safe_midi(x) }, opts[:amp]]
    Node.new
  end

  # check_notes has already reported anything unresolvable; the log must not
  # raise a second time on the same bad name.
  def safe_midi(x)
    return nil if x.nil?
    midi_of(x)
  rescue StandardError
    nil
  end

  def synth(name, **opts)
    return err("unknown synth #{name.inspect}") unless TABLE.key?(name)
    check_notes(opts[:note]) if opts.key?(:note)
    check_opts("synth #{name.inspect}", name, opts)
    @log << [:synth, name, safe_midi(opts[:note])]
    Node.new
  end

  def sample(name, *_r, **opts)
    if name.is_a?(Symbol) && !SAMPLE_NAMES.empty? && !SAMPLE_NAMES.include?(name)
      err("sample #{name.inspect} is not in the installed sample pack")
    end
    opts.each_key { |k| err("sample #{name.inspect}: opt #{k.inspect} is not accepted by the sample player") unless SAMPLE_OPTS.include?(k) }
    @log << [:sample, name, opts[:amp]]
  end

  def control(_node, **opts)
    opts.each_key do |k|
      base = k.to_s.sub(/_slide(_shape|_curve)?\z/, '').to_sym
      err("control: opt #{k.inspect} is not a modulatable opt") unless TABLE.values.any? { |t| t[:opts].include?(base) }
    end
  end

  def with_fx(name, **opts, &blk)
    t = TABLE[:"fx_#{name}"]
    if t.nil?
      err("unknown fx #{name.inspect}")
    else
      opts.each do |k, v|
        next err("with_fx #{name.inspect}: opt #{k.inspect} is not accepted") unless t[:opts].include?(k)
        check_enum("with_fx #{name.inspect}", k, v, t[:enums][k]) if t[:enums][k]
        check_bounds("with_fx #{name.inspect}", k, v, t[:bounds][k]) if t[:bounds][k]
      end
    end
    blk.call
  end

  # ---------------------------------------------------------------- checks
  def check_notes(n)
    Array(n).each do |x|
      next if x.nil?
      v = begin
        midi_of(x)
      rescue StandardError => e
        next err(e.message)
      end
      err("note #{x.inspect} is MIDI #{v}, outside 0..127") if v < 0 || v > 127
    end
  end

  def check_opts(where, synth_sym, opts)
    t = TABLE[synth_sym] or return err("#{where}: no such synth")
    opts.each do |k, v|
      next err("#{where}: opt #{k.inspect} is not accepted by :#{synth_sym} (value #{v.inspect})") unless t[:opts].include?(k)
      check_enum(where, k, v, t[:enums][k]) if t[:enums][k]
      check_bounds(where, k, v, t[:bounds][k]) if t[:bounds][k]
      err("#{where}: #{k.inspect} is negative (#{v.inspect})") if %i[amp attack decay sustain release].include?(k) && v.is_a?(Numeric) && v < 0
    end
  end

  # The silent-layer-death check. Measured behaviour is in the header.
  def check_enum(where, k, v, options)
    case v
    when Integer
      err("#{where}: #{k.inspect} must be one of #{options.inspect}, got #{v.inspect}") unless options.include?(v)
    when Float
      if v == v.to_i && options.include?(v.to_i)
        warn!("#{where}: #{k.inspect} is the Float #{v.inspect} where an enumerated Integer belongs. " \
              "Sonic Pi accepts it today only because Array#include? sees #{v.inspect} == #{v.to_i}. Write #{v.to_i}.")
      else
        err("#{where}: #{k.inspect} is the Float #{v.inspect}. Enumerated opts RAISE on a non-member, and a raise " \
            "inside a live_loop kills THAT LOOP ONLY while the rest of the track plays on — the recording then " \
            "sounds fine and is silently missing a layer. Use one of #{options.inspect}.")
      end
    else
      err("#{where}: #{k.inspect} must be an Integer in #{options.inspect}, got #{v.inspect} (#{v.class})")
    end
  end

  def check_bounds(where, k, v, b)
    return unless v.is_a?(Numeric)
    if b[:min] && (b[:min_incl] ? v < b[:min] : v <= b[:min])
      err("#{where}: #{k.inspect} is #{v}, below the permitted minimum #{b[:min]}")
    end
    if b[:max] && (b[:max_incl] ? v > b[:max] : v >= b[:max])
      err("#{where}: #{k.inspect} is #{v}, above the permitted maximum #{b[:max]}")
    end
  end

  # ------------------------------------------------------------ simulation
  def run_loop(name, mode)
    @mode = mode
    @counters = {}
    @log = []
    @elapsed = 0.0
    @where = "#{name} (#{mode})"
    blk = @loops[name]
    iters = []
    300.times do
      @acc = 0.0
      blk.call
      break if @acc <= 0
      iters << @acc.round(6)
      @elapsed = (@elapsed + @acc).round(6)
      break if @elapsed >= 64
    end
    { total: @elapsed, iters: iters, log: @log.dup }
  end
end

# Split the source into live_loop bodies so look/tick scoping can be read
# statically as well as simulated. Relies on the house style: live_loop at
# column 0, its `end` at column 0.
def live_loop_bodies(src)
  out = []
  lines = src.lines
  lines.each_with_index do |line, i|
    next unless line =~ /\Alive_loop\s+:(\w+)/
    name = Regexp.last_match(1)
    body = [line]
    lines[(i + 1)..].each do |l|
      break if l =~ /\A\S/ && l !~ /\A\s*end\b/ && body.size > 1 && l !~ /\Aend\b/
      body << l
      break if l =~ /\Aend\b/
    end
    out << [name, body.join]
  end
  out
end

def check_file(path)
  src = File.read(path)
  puts "\n=== #{File.basename(path)}"
  c = Checker.new
  begin
    c.instance_eval(src, path)
  rescue StandardError, ScriptError => e
    puts "  LOAD FAILED: #{e.class}: #{e.message}"
    puts "    #{e.backtrace.first(3).join("\n    ")}"
    return false
  end

  errors = []
  warns = []

  # 1. tick scoping, read statically off the text
  live_loop_bodies(src).each do |lname, body|
    looked = body.scan(/\blook\(\s*:(\w+)/).flatten.uniq
    ticked = body.scan(/\btick\(\s*:(\w+)/).flatten.uniq
    (looked - ticked).each do |k|
      errors << "#{lname}: reads look(:#{k}) but never ticks :#{k} itself. Sonic Pi tick counters are " \
                "live_loop-local and are not inherited, so this returns 0 on every iteration, forever. " \
                "Every branch keyed off it is dead."
    end
  end

  # 2 + 3. bar arithmetic, and what the pinning actually costs musically
  c.loops.each_key do |lname|
    w = c.run_loop(lname, :written)
    i = c.run_loop(lname, :intended)
    mine = []
    mine << "#{lname}: one cycle is #{w[:total]} beats, not 64 (bar drift)." if w[:total] != 64.0
    off = w[:iters].reject { |x| x.positive? && ((x * 4).round % 16).zero? }
    mine << "#{lname}: iteration(s) of #{off.uniq.inspect} beats are not a whole number of bars." unless off.empty?
    same = w[:log] == i[:log] && w[:iters] == i[:iters]
    unless same
      mine << "#{lname}: what plays is NOT what the file describes. As written: #{w[:log].size} events, " \
              "iteration shapes #{w[:iters].uniq.sort.inspect}. As the comments intend: #{i[:log].size} events, " \
              "shapes #{i[:iters].uniq.sort.inspect}."
    end
    errors.concat(mine)
    printf("  %s %-18s cycle=%-6s iters=%-3d shapes=%-13s %s\n", mine.empty? ? 'ok  ' : 'FAIL',
           lname, w[:total], w[:iters].size, w[:iters].uniq.sort.inspect,
           same ? 'plays as written' : 'DIVERGES from its own comments')
  end

  c.problems.each { |sev, m| (sev == :error ? errors : warns) << m }

  unless warns.empty?
    puts "\n  #{warns.uniq.size} WARNING(S):"
    warns.uniq.each { |w| puts "    ! #{w}" }
  end
  if errors.empty?
    puts "\n  OK: tick scoping, bar arithmetic, opt names, enumerated opts, bounds and note ranges all check out."
    true
  else
    puts "\n  #{errors.uniq.size} PROBLEM(S):"
    errors.uniq.each { |e| puts "    - #{e}" }
    false
  end
end

# ------------------------------------------------------------- self test
CLEAN = <<~'RB'
  use_bpm 120
  live_loop :drums do
    bar = tick(:bar) % 16
    4.times { sample :bd_haus, amp: 1.0; sleep 1 }
  end
  live_loop :tune, sync: :drums do
    bar = tick(:tune) % 16
    use_synth :hollow
    play :e5, amp: 0.5, noise: 1, res: 0.3
    sleep 4
  end
RB

CASES = {
  'bar drift (a bar summing to 3.5)' =>
    [CLEAN.sub('4.times { sample :bd_haus, amp: 1.0; sleep 1 }',
               '3.times { sample :bd_haus, amp: 1.0; sleep 1 }; sleep 0.5'),
     /bar drift|not a whole number of bars/],
  'fatal enum: noise: 0.5 on :hollow' => [CLEAN.sub('noise: 1', 'noise: 0.5'), /kills THAT LOOP ONLY/],
  'latent enum: noise: 1.0 on :hollow' => [CLEAN.sub('noise: 1', 'noise: 1.0'), /Float 1\.0 where an enumerated Integer/],
  'enum out of range: noise: 7' => [CLEAN.sub('noise: 1', 'noise: 7'), /must be one of/],
  'opt the synth rejects: detune: on :hollow' => [CLEAN.sub('noise: 1', 'detune: 0.2'), /not accepted by :hollow/],
  'numeric bound: cutoff 200' => [CLEAN.sub('noise: 1', 'cutoff: 200'), /above the permitted maximum/],
  'cross-thread look(:bar)' => [CLEAN.sub('bar = tick(:tune) % 16', 'bar = look(:bar) % 16'), /never ticks :bar itself/],
  'structural divergence it causes' => [CLEAN.sub('bar = tick(:tune) % 16', 'bar = look(:bar) % 16')
                                             .sub('play :e5, amp: 0.5, noise: 1, res: 0.3',
                                                  'play :e5, amp: 0.5, noise: 1, res: 0.3 if bar >= 8'),
                                        /NOT what the file describes/],
  'note off the keyboard' => [CLEAN.sub('play :e5', 'play :e11'), /outside 0\.\.127/],
  'misspelled note name' => [CLEAN.sub('play :e5', 'play :h5'), /bad note name/],
  'unknown fx' => [CLEAN.sub('play :e5, amp: 0.5, noise: 1, res: 0.3',
                             'with_fx :sparkle do; play :e5, amp: 0.5, noise: 1; end'), /unknown fx/],
  'unknown synth' => [CLEAN.sub('use_synth :hollow', 'use_synth :trombone'), /unknown synth/],
  'sample that does not exist' => [CLEAN.sub(':bd_haus', ':bd_kaboom'), /not in the installed sample pack/],
}

def capture
  old = $stdout
  $stdout = StringIO.new
  yield
  $stdout.string
ensure
  $stdout = old
end

def selftest
  puts "NEGATIVE CONTROL — the clean file must PASS and every injected fault must be CAUGHT.\n\n"
  all = true
  Dir.mktmpdir do |dir|
    f = File.join(dir, 'clean.rb')
    File.write(f, CLEAN)
    out = capture { check_file(f) }
    good = out.include?('OK:')
    all &&= good
    printf("  %-44s %s\n", 'clean control', good ? 'PASSES (correct)' : 'FAILED — checker is too strict')
    puts out.gsub(/^/, '      ') unless good
    CASES.each do |label, (body, pat)|
      g = File.join(dir, 'case.rb')
      File.write(g, body)
      out = capture { check_file(g) }
      caught = !(out =~ pat).nil?
      all &&= caught
      printf("  %-44s %s\n", label, caught ? 'CAUGHT (correct)' : 'MISSED — checker is blind to this')
      puts out.gsub(/^/, '      ') unless caught
    end
  end
  puts "\n#{all ? 'NEGATIVE CONTROL PASSED — the checker catches what it claims to.' : 'NEGATIVE CONTROL FAILED — do not trust it yet.'}"
  all
end

# Only act as a command when run directly, so other scripts can require this
# for its Checker without tripping the CLI.
if __FILE__ == $PROGRAM_NAME
  if ARGV.first == '--selftest'
    exit(selftest ? 0 : 1)
  else
    abort 'usage: ruby check_fmwo.rb <theme.rb> [...] | --selftest' if ARGV.empty?
    ok = ARGV.map { |f| check_file(f) }.all?
    puts "\n#{ok ? 'ALL CLEAR' : 'SOMETHING IS WRONG'}"
    exit(ok ? 0 : 1)
  end
end
