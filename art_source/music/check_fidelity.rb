# check_fidelity.rb — precise "is this a correctness fix, or a revision?" diff.
#
# Compares the ORIGINAL performed in :intended mode (the music as written on
# the page — what the tick fix is meant to make audible) against a CANDIDATE
# performed in :written mode (what will actually come out of the speakers).
#
# Normalises away two things that are notation, not music:
#   * `synth :x, note: n` and `use_synth :x; play n` are the same sound.
#   * with_fx nesting is reported as its own stream, not mixed into the notes,
#     because restructuring a 32-beat iteration into eight 4-beat ones changes
#     how often the fx block is entered without changing a single note.
HERE = File.dirname(File.expand_path(__FILE__))  # check_fmwo.rb sits beside this file
$LOAD_PATH.unshift HERE
require 'check_fmwo'

class Checker
  def now; (@elapsed + @acc).round(6); end
  def bpm; @bpm; end
  def misc; @misc ||= []; end
  def use_bpm(v); @bpm = v; end
  def use_octave(v); misc << [:octave, v]; end
  def use_transpose(v); misc << [:transpose, v]; end
  def norm(o); o.map { |k, v| [k.to_s, v.is_a?(Float) ? v.round(6) : v] }.sort; end

  def play(n, *_r, **opts)
    check_notes(n); check_opts("play on :#{@synth}", @synth, opts)
    @log << [now, :sound, @synth, Array(n).map { |x| safe_midi(x) }, norm(opts)]
    Node.new
  end

  def synth(name, **opts)
    return err("unknown synth #{name.inspect}") unless TABLE.key?(name)
    check_notes(opts[:note]) if opts.key?(:note)
    check_opts("synth #{name.inspect}", name, opts)
    @log << [now, :sound, name, Array(opts[:note]).map { |x| safe_midi(x) },
             norm(opts.reject { |k, _| k == :note })]
    Node.new
  end

  def sample(name, *_r, **opts); @log << [now, :smp, name, [], norm(opts)]; end
  def control(_n, **opts); @log << [now, :ctl, nil, [], norm(opts)]; end

  def with_fx(name, **opts, &blk)
    (@fxlog ||= []) << [now, name, norm(opts)]
    blk.call
  end
  def fxlog; @fxlog ||= []; end
  def reset_fx!; @fxlog = []; end
end

def perform(path, mode)
  c = Checker.new
  c.instance_eval(File.read(path), path)
  loops = {}
  c.loops.each_key do |n|
    c.reset_fx!
    r = c.run_loop(n, mode)
    loops[n] = { log: r[:log], total: r[:total], iters: r[:iters], fx: c.fxlog.dup }
  end
  { loops: loops, bpm: c.bpm, misc: c.misc }
end

def fmt(e)
  t, kind, name, notes, opts = e
  format('beat %-7s %-4s %-16s %-20s %s', t, kind, name.inspect, notes.inspect,
         opts.map { |k, v| "#{k}:#{v}" }.join(' '))
end

ok_all = true
summary = []
ARGV.each_slice(2) do |orig, cand|
  puts "\n#{'=' * 96}\n#{File.basename(orig)} (as written on the page)  vs  #{File.basename(cand)} (as it will play)\n#{'=' * 96}"
  a = perform(orig, :intended)
  b = perform(cand, :written)
  file_ok = true
  changed_loops = []

  if a[:bpm] != b[:bpm]
    puts "  !! TEMPO CHANGED: #{a[:bpm]} -> #{b[:bpm]}"; file_ok = false
  end
  puts "  !! use_octave/use_transpose CHANGED" if a[:misc] != b[:misc]

  gone  = a[:loops].keys - b[:loops].keys
  added = b[:loops].keys - a[:loops].keys
  puts "  !! LOOP REMOVED: #{gone.inspect}"  unless gone.empty?
  puts "  !! LOOP ADDED:   #{added.inspect}" unless added.empty?
  file_ok = false unless gone.empty? && added.empty?

  (a[:loops].keys & b[:loops].keys).each do |ln|
    la = a[:loops][ln][:log]
    lb = b[:loops][ln][:log]
    fa = a[:loops][ln][:fx]
    fb = b[:loops][ln][:fx]
    notes_same = (la == lb)
    fx_same = (fa.map { |t, n, o| [n, o] }.uniq == fb.map { |t, n, o| [n, o] }.uniq)

    if notes_same && fx_same
      printf("  same  %-18s %4d sounding events\n", ln, la.size)
      next
    end

    if notes_same && !fx_same
      printf("  fx    %-18s notes identical; with_fx entered %d x -> %d x (%s -> %s)\n",
             ln, fa.size, fb.size, fa.map { |x| x[1] }.uniq.inspect, fb.map { |x| x[1] }.uniq.inspect)
      next
    end

    file_ok = false
    changed_loops << ln
    diffs = (0...[la.size, lb.size].max).select { |i| la[i] != lb[i] }
    printf("  DIFF  %-18s page: %d events, candidate: %d events, %d differing slots\n",
           ln, la.size, lb.size, diffs.size)
    diffs.first(3).each do |i|
      puts "          page      : #{la[i] ? fmt(la[i]) : '(nothing)'}"
      puts "          candidate : #{lb[i] ? fmt(lb[i]) : '(nothing)'}"
    end
  end

  if file_ok
    puts '  VERDICT: FAITHFUL — plays exactly the music the original page describes.'
  else
    puts "  VERDICT: REVISED — #{changed_loops.size} loop(s) changed: #{changed_loops.join(', ')}"
  end
  summary << [File.basename(cand), file_ok, changed_loops]
  ok_all &&= file_ok
end

puts "\n#{'=' * 96}\nSUMMARY\n#{'=' * 96}"
summary.each { |n, ok, ch| printf("  %-26s %s%s\n", n, ok ? 'faithful correctness fix' : 'CHANGES THE MUSIC', ok ? '' : " (#{ch.join(', ')})") }
puts "\n#{ok_all ? 'EVERY CANDIDATE IS A PURE CORRECTNESS FIX' : 'AT LEAST ONE CANDIDATE CHANGES THE MUSIC'}"

# USAGE
#   ruby check_fidelity.rb <original.rb> <candidate.rb> [<original.rb> <candidate.rb> ...]
