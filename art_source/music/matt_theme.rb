# MATT — "Top One, By The Way"
# Original music for Project FMWO, written for Sonic Pi 4.x / 5.x.
#
# Boss 4: the loudest man in the server, and a nice guy about it. The piece is
# his temper in sixteen bars. A friendly brass hook bounces along in B-flat
# major, with a lute underneath it because he will tell you which MMO is the
# best. Then he draws a breath and SNAPS: B-flat minor, the kit doubles up, the
# tune gets yelled through a blown speaker, and the ROAR. Then he catches
# himself. The lute comes back first, the brass after it, and the two borrowed
# chords that were so ugly a moment ago (Gb and Ab) turn into the heroic
# bVI-bVII-I that walks him straight back into the hook, grinning.
#
# 152 bpm. B-flat major; B-flat minor for the snap. 16-bar cycle:
#   Bars 1-8    THE HELLO  — Bb Eb Gm F | Bb Eb Cm F7. The hook, twice. Its
#                            signature is the scoop: a pickup, up a fourth,
#                            onto a long held shout. The second time it climbs
#                            to F6 and stops on the Eb that wants to resolve.
#   Bars 9-12   ENOUGH     — Bbm Gb/Bb Ebm F. That Eb resolves DOWN, to the
#                            minor third. The kit goes double time, the bass
#                            goes to distorted sixteenths, the brass hammers
#                            3+3+2, and the hook's own shape comes back yelled.
#                            Bar 12 is THE ROAR, over the dominant.
#   Bars 13-14  HONG       — Gb Ab, quiet. The roar's tail and one breath out,
#                            then the groove creeping back, with the scoop
#                            played gently on the lute.
#   Bars 15-16  COOL       — Gb Ab again, loud: the same scoop on the brass, a
#                            harp run under each, and a pickup of F G A that
#                            lands on bar 1's B-flat. The loop point is the
#                            biggest arrival in the piece.
#
# Bar 1 is where the fight starts: MattIntro starts this track on his roar, so
# the downbeat is a crash, a tuned speaker thump and a held brass shout. That
# shout sits under the roar sound effect for the two seconds it lasts, and the
# hook's moving part only starts once the roar has died away.
#
# HOW TO RECORD: never through the GUI. See music-recording-pipeline:
#   python record_theme.py matt_theme.rb 152 --out <scratch>/matt_theme_raw.wav
#   python measure_take.py <scratch>/matt_theme_raw.wav 152
#   python cut_loop.py <scratch>/matt_theme_raw.wav 152 --out <scratch>/matt_theme.wav
# One cycle is 16 bars x 4 beats / 152 bpm = 25.2632 s.

use_bpm 152

# ------------------------------------------------------------------ harmony
# One chord a bar: [bass root, brass voicing, lute strings]. The lute has no
# strings in the snap because he has put it down.
define :matt_harmony do
  [
    [:bb1, [:bb3, :d4, :f4, :bb4],   [:bb3, :f4, :bb4, :d5]],   # 1  Bb
    [:eb2, [:bb3, :eb4, :g4, :bb4],  [:eb4, :g4, :bb4, :eb5]],  # 2  Eb
    [:g1,  [:bb3, :d4, :g4, :bb4],   [:g3, :d4, :g4, :bb4]],    # 3  Gm
    [:f1,  [:a3, :c4, :f4, :a4],     [:f3, :c4, :f4, :a4]],     # 4  F
    [:bb1, [:bb3, :d4, :f4, :bb4],   [:bb3, :f4, :bb4, :d5]],   # 5  Bb
    [:eb2, [:bb3, :eb4, :g4, :bb4],  [:eb4, :g4, :bb4, :eb5]],  # 6  Eb
    [:c2,  [:g3, :c4, :eb4, :g4],    [:g3, :c4, :g4, :c5]],     # 7  Cm
    [:f1,  [:a3, :c4, :eb4, :f4],    [:f3, :c4, :eb4, :a4]],    # 8  F7
    [:bb1, [:bb3, :db4, :f4, :bb4],  nil],                      # 9  Bbm ENOUGH
    [:bb1, [:bb3, :db4, :gb4, :bb4], nil],                      # 10 Gb/Bb
    [:eb2, [:bb3, :eb4, :gb4, :bb4], nil],                      # 11 Ebm
    [:f2,  [:a3, :c4, :f4, :a4],     nil],                      # 12 F   THE ROAR
    [:gb1, [:gb3, :bb3, :db4, :gb4], [:gb3, :db4, :gb4, :bb4]], # 13 Gb  HONG
    [:ab1, [:ab3, :c4, :eb4, :ab4],  [:ab3, :eb4, :ab4, :c5]],  # 14 Ab
    [:gb1, [:gb3, :bb3, :db4, :gb4], [:gb3, :db4, :gb4, :bb4]], # 15 Gb  COOL
    [:ab1, [:ab3, :c4, :eb4, :ab4],  [:ab3, :eb4, :ab4, :c5]]   # 16 Ab
  ]
end

# --------------------------------------------------------------------- tune
# [note, beats]; every bar sums to 4. A pickup is written at the END of the
# bar before its downbeat, so bar 16's F G A belongs to bar 1's shout and bar
# 4's F to bar 5's.
#
# The shout is always followed by the same bounce: up a third, step, step, and
# back up the third (Bb, D C Bb, D). It bounces UP off the held note rather than
# leaning on the note below it, because the brass stab on the and-of-2 is
# sounding the root at that exact moment and a leading note there rubs a
# semitone against it, every scoop, forever.
define :matt_tune do
  [
    # ---- THE HELLO
    [[:bb5, 1.5], [:d6, 0.5], [:c6, 0.5], [:bb5, 0.5], [:d6, 1]],                     # 1
    [[:eb6, 0.5], [:d6, 0.5], [:c6, 0.5], [:bb5, 0.5], [:g5, 1.5], [:d5, 0.5]],       # 2
    [[:g5, 1.5], [:bb5, 0.5], [:a5, 0.5], [:g5, 0.5], [:bb5, 1]],                     # 3
    [[:c6, 0.5], [:bb5, 0.5], [:a5, 0.5], [:g5, 0.5], [:a5, 1], [:c6, 0.5], [:f5, 0.5]], # 4
    [[:bb5, 1.5], [:d6, 0.5], [:c6, 0.5], [:bb5, 0.5], [:d6, 1]],                     # 5
    [[:eb6, 0.5], [:d6, 0.5], [:c6, 0.5], [:bb5, 0.5], [:g5, 1.5], [:g5, 0.5]],       # 6
    [[:c6, 1.5], [:eb6, 0.5], [:d6, 0.5], [:c6, 0.5], [:eb6, 1]],                     # 7
    [[:f6, 1], [:eb6, 0.5], [:c6, 0.5], [:a5, 0.5], [:c6, 0.5], [:eb6, 1]],           # 8
    # ---- ENOUGH: the same shapes in minor, written at the yell's lower octave
    [[:db5, 1.5], [:f5, 0.5], [:eb5, 0.5], [:db5, 0.5], [:f5, 1]],                    # 9
    [[:gb5, 0.5], [:f5, 0.5], [:eb5, 0.5], [:db5, 0.5], [:bb4, 1.5], [:f4, 0.5]],     # 10
    [[:bb4, 1.5], [:db5, 0.5], [:c5, 0.5], [:bb4, 0.5], [:db5, 1]],                   # 11
    [[:c5, 0.5], [:eb5, 0.5], [:f5, 3]],                                              # 12
    # ---- HONG, then COOL: one scoop per chord, soft and then loud
    [[:db5, 0.5], [:gb5, 1.5], [:bb5, 0.5], [:ab5, 0.5], [:gb5, 0.5], [:bb5, 0.5]],   # 13
    [[:eb5, 0.5], [:ab5, 1.5], [:c6, 0.5], [:bb5, 0.5], [:ab5, 0.5], [:c6, 0.5]],     # 14
    [[:db5, 0.5], [:gb5, 1.5], [:bb5, 0.5], [:ab5, 0.5], [:gb5, 0.5], [:bb5, 0.5]],   # 15
    [[:eb5, 0.5], [:ab5, 0.5], [:c6, 1.5], [:f5, 0.5], [:g5, 0.5], [:a5, 0.5]]        # 16
  ]
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
matt_tune.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "matt_theme: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# ------------------------------------------------------------------- brass
# A saw through the tb303's own filter envelope, so every attack opens with a
# "bwah" and settles, with a detuned saw under it for the section. Each note of
# a chord gets its own spot in the stereo field.
define :matt_brass do |notes, len, amp|
  notes.each_with_index do |n, i|
    pan = (i - (notes.size - 1) / 2.0) * 0.14
    synth :tb303, note: n, amp: amp, attack: 0.012, sustain: len * 0.55,
      release: 0.14 + len * 0.1, wave: 0, res: 0.12, cutoff_min: 62,
      cutoff: 106, cutoff_attack: 0.03, cutoff_decay: 0.18,
      cutoff_sustain_level: 0.45, pan: pan
    synth :dsaw, note: n, amp: amp * 0.45, attack: 0.02, sustain: len * 0.5,
      release: 0.2, cutoff: 96, detune: 0.12, pan: -pan
  end
end

# -------------------------------------------------------------------- clock
# Plays nothing, on purpose. A live_loop that syncs to another joins on that
# loop's NEXT cue, one iteration late. In the other eight themes the drums are
# the clock, so every other voice counts its bars one behind the kit (measured
# on jordan_theme_v3_raw.wav: his big drums arrive a bar before his lead).
# Here every audible voice, the drums included, syncs to this, so they all join
# on the same cue, count the same bars, and the take's first transient is a
# real bar 1 with everyone in it.
live_loop :matt_clock do
  sleep 4
end

# ------------------------------------------------------------------- drums
# THE HELLO bounces: kick on 1, the and-of-2 and 3, a snare-and-clap backbeat,
# and an open hat on every off-beat. ENOUGH doubles up: four on the floor, a
# snare on every off-beat as well as the backbeat, sixteenth hats, and a roll
# into the roar. HONG nearly stops, then picks back up. Bar 16 fills into the
# crash on bar 1.
live_loop :matt_drums, sync: :matt_clock do
  bar = tick(:drums) % 16
  enough = bar >= 8 && bar < 12
  hong = bar == 12 || bar == 13
  sample :drum_cymbal_hard, amp: 0.6, rate: 0.95 if bar == 0 || bar == 14
  sample :drum_cymbal_hard, amp: 0.38, rate: 1.05 if bar == 4
  sample :drum_splash_hard, amp: 0.65, rate: 0.8 if bar == 8
  sample :drum_cymbal_hard, amp: 0.5, rate: 0.85 if bar == 10
  16.times do |s|
    if enough
      roar = bar == 11
      sample :bd_haus, amp: 1.35 if s % 4 == 0 || s == 3 || s == 11 || (roar && s.even?)
      sample :drum_snare_hard, amp: 0.3, rate: 1.1 if !roar && [2, 6, 10, 14].include?(s)
      if s == 4 || s == 12
        sample :drum_snare_hard, amp: 0.62
        synth :sc808_clap, amp: 0.5
      end
      sample :drum_cymbal_closed, amp: (s.even? ? 0.2 : 0.12), pan: 0.2
      sample :drum_snare_hard, amp: 0.22 + (s - 8) * 0.07, rate: 1.05 if roar && s >= 8
    elsif hong
      if bar == 12
        sample :bd_haus, amp: 1.0 if s == 0
        sample :drum_cymbal_closed, amp: 0.1, pan: 0.2 if s.even? && s >= 4
      else
        sample :bd_haus, amp: 1.15 if [0, 6, 8].include?(s)
        if s == 12
          sample :drum_snare_hard, amp: 0.4
          synth :sc808_clap, amp: 0.4
        end
        sample :drum_cymbal_closed, amp: 0.14, pan: 0.2 if s.even?
        synth :sc808_open_hihat, amp: 0.22, decay: 0.25, pan: 0.25 if s == 14
      end
    elsif bar == 7 && s >= 12
      # Bar 8's last beat is the breath he draws before he snaps. Nothing else.
    elsif bar == 15 && s >= 8
      # The fill: low tom to high, snare to finish, climbing into bar 1.
      step = s - 8
      sample :bd_haus, amp: 1.2 if s == 8
      tom = [:drum_tom_lo_hard, :drum_tom_lo_hard, :drum_tom_mid_hard, :drum_tom_mid_hard,
             :drum_tom_hi_hard, :drum_tom_hi_hard, :drum_snare_hard, :drum_snare_hard][step]
      sample tom, amp: 0.4 + step * 0.06
    else
      sample :bd_haus, amp: 1.3 if [0, 6, 8].include?(s) || (s == 14 && (bar == 3 || bar == 14))
      if s == 4 || s == 12
        sample :drum_snare_hard, amp: 0.5
        synth :sc808_clap, amp: 0.45
      end
      sample :drum_cymbal_closed, amp: 0.18, pan: 0.2 if s % 4 == 0
      synth :sc808_open_hihat, amp: 0.24, decay: 0.25, pan: 0.25 if s % 4 == 2
      sample :drum_cymbal_closed, amp: 0.06, pan: 0.2 if s.odd?
    end
    sleep 0.25
  end
end

# ----------------------------------------------------------------- speaker
# The sub he is built around: a tuned 808 thump on the chord root. One on each
# downbeat of the hello, a double punch into bar 5 and into bar 1, on every
# beat while he is shouting, and one long one that rings out after the roar.
live_loop :matt_speaker, sync: :matt_clock do
  bar = tick(:speaker) % 16
  root = note(matt_harmony[bar][0])
  root -= 12 while root > 40
  16.times do |s|
    if bar < 8 || bar >= 14
      if s == 0
        big = bar == 0 || bar == 4 || bar == 14
        synth :sc808_bassdrum, note: root, amp: (big ? 0.75 : 0.55), decay: (big ? 1.4 : 0.9)
      elsif (bar == 3 || bar == 15) && (s == 12 || s == 14)
        # the double punch, on the leading note the bass is walking into B-flat on
        synth :sc808_bassdrum, note: :a1, amp: 0.55, decay: 0.45
      end
    elsif bar < 11
      synth :sc808_bassdrum, note: root, amp: (bar == 8 && s == 0 ? 0.7 : 0.6),
        decay: (bar == 8 && s == 0 ? 1.5 : 0.5) if s % 4 == 0
    elsif bar == 11
      synth :sc808_bassdrum, note: root, amp: 0.85, decay: 2.5 if s == 0
    elsif bar == 12
      synth :sc808_bassdrum, note: root, amp: 0.6, decay: 3.0 if s == 0
    else
      synth :sc808_bassdrum, note: root, amp: 0.45, decay: 0.8 if s == 0 || s == 8
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# The bounce: root on the beat, octave on the off-beat, with a walk into bars
# 3, 5 and 7 and the leading note A into every B-flat. In the snap it is
# distorted sixteenths that climb chromatically into each new root, then one
# held F under the roar that dives an octave as the air goes out of him.
live_loop :matt_bass, sync: :matt_clock do
  bar = tick(:bass) % 16
  root = note(matt_harmony[bar][0])
  use_synth :tb303
  if bar >= 8 && bar <= 10
    riff = [[0, 0, 12, 0, 0, 0, 12, 0, 0, 0, 12, 0, 3, 0, 12, 0],
            [0, 0, 12, 0, 0, 0, 12, 0, 0, 0, 12, 0, 1, 2, 3, 4],
            [0, 0, 12, 0, 0, 0, 12, 0, 0, 0, 12, 0, 0, 12, 0, 1]][bar - 8]
    # The fx amp: pulls the level back down without taking the drive out.
    with_fx :distortion, distort: 0.65, mix: 0.6, amp: 0.8 do
      riff.each_with_index do |off, s|
        accent = s % 4 == 0
        play root + off, amp: (accent ? 0.85 : 0.58), attack: 0.003,
          sustain: (accent ? 0.08 : 0.04), release: 0.1, res: 0.3,
          cutoff_min: 50, cutoff: (accent ? 84 : 90), wave: 0
        sleep 0.25
      end
    end
  elsif bar == 11
    with_fx :distortion, distort: 0.6, mix: 0.55, amp: 0.7 do
      held = play root, amp: 0.8, attack: 0.01, sustain: 3.4, release: 0.5,
        res: 0.25, cutoff_min: 55, cutoff: 80, cutoff_attack: 0.5,
        cutoff_sustain_level: 0.6, note_slide: 0.9, wave: 0
      sleep 3
      control held, note: root - 12
      sleep 1
    end
  elsif bar == 12
    play root, amp: 0.7, attack: 0.03, sustain: 2.4, release: 1.4, res: 0.2,
      cutoff_min: 40, cutoff: 70, cutoff_attack: 0.4, cutoff_sustain_level: 0.5, wave: 0
    sleep 4
  else
    walk = {1 => :d2, 3 => :a1, 5 => :bb1, 15 => :a1}
    8.times do |e|
      if bar == 7 && e >= 6
        sleep 0.5
        next
      end
      base = e >= 6 && walk[bar] ? note(walk[bar]) : root
      low = e.even?
      pitch = low ? base : base + 12
      play pitch, amp: (low ? 1.1 : 0.72), attack: 0.005,
        sustain: (low ? 0.12 : 0.06), release: (low ? 0.2 : 0.14), res: 0.22,
        cutoff_min: 45, cutoff: (low ? 88 : 92), cutoff_attack: 0.005,
        cutoff_decay: 0.1, cutoff_sustain_level: 0.35, wave: 0
      sleep 0.5
    end
  end
end

# ------------------------------------------------------------------- brass
# THE HELLO: stabs on the and-of-2 and the and-of-4, every bar, which is where
# the bass's octave and the open hat already are, and a long "bwah" under the
# shout at the top of each phrase. ENOUGH: minor chords hammered 3+3+2,
# distorted. THE ROAR: one swelling chord and then out of its way. HONG: a
# soft pad for the breath out, then the stabs creeping back in. COOL: the
# fanfare, and silence under bar 16's pickup.
live_loop :matt_brass, sync: :matt_clock do
  bar = tick(:brass) % 16
  ch = matt_harmony[bar][1]
  if bar < 8
    8.times do |e|
      if e == 0 && (bar == 0 || bar == 4)
        matt_brass ch, 1.0, 0.42
      elsif e == 3 || (e == 7 && bar != 1 && bar != 7)
        # not under bar 2's pickup, whose D is a semitone off this bar's E-flat
        matt_brass ch, 0.25, 0.36
      end
      sleep 0.5
    end
  elsif bar < 11
    with_fx :distortion, distort: 0.45, mix: 0.5, amp: 0.8 do
      8.times do |e|
        matt_brass ch, 0.4, 0.26 if e == 0 || e == 3 || e == 6
        sleep 0.5
      end
    end
  elsif bar == 11
    with_fx :distortion, distort: 0.5, mix: 0.5, amp: 0.75 do
      matt_brass ch, 2.0, 0.28
      sleep 4
    end
  elsif bar == 12
    use_synth :prophet
    with_fx :reverb, room: 0.8, mix: 0.4 do
      play ch, amp: 0.35, attack: 1.2, sustain: 1.8, release: 1.2, cutoff: 80, res: 0.2
      sleep 4
    end
  elsif bar == 13
    8.times do |e|
      matt_brass ch, 0.25, 0.28 if e == 3 || e == 7
      sleep 0.5
    end
  else
    hits = bar == 14 ? {0 => 1.25, 3 => 0.25, 4 => 1.0, 7 => 0.25} : {0 => 1.25, 3 => 0.25}
    8.times do |e|
      matt_brass ch, hits[e], (e == 0 ? 0.45 : 0.37) if hits[e]
      sleep 0.5
    end
  end
end

# --------------------------------------------------------------------- lute
# The RuneScape in him: a plucked string, rolling up the chord in threes
# (3+3+2 over the eighths) under the hello, gone while he shouts, back first
# when he calms down, and running up the chord like a harp under the fanfare.
live_loop :matt_lute, sync: :matt_clock do
  bar = tick(:lute) % 16
  strings = matt_harmony[bar][2]
  use_synth :pluck
  if strings.nil?
    sleep 4
  elsif bar >= 14
    base = note(strings[0])
    with_fx :reverb, room: 0.7, mix: 0.3 do
      8.times do |i|
        play base + [0, 4, 7][i % 3] + 12 * (i / 3), amp: 0.6 + i * 0.06, coef: 0.25, pan: -0.2
        sleep 0.25
      end
      if bar == 14
        [2, 3, 2, 1].each do |k|
          play strings[k], amp: 0.6, coef: 0.3, pan: -0.2
          sleep 0.5
        end
      else
        sleep 2
      end
    end
  else
    soft = bar == 12 || bar == 13 ? 0.7 : 1.0
    with_fx :reverb, room: (soft < 1 ? 0.8 : 0.6), mix: (soft < 1 ? 0.4 : 0.28) do
      [0, 1, 2, 1, 2, 3, 2, 1].each_with_index do |k, e|
        unless bar == 7 && e >= 6
          play strings[k], amp: ([0, 3, 6].include?(e) ? 0.84 : 0.56) * soft, coef: 0.35, pan: -0.25
        end
        sleep 0.5
      end
    end
  end
end

# --------------------------------------------------------------------- lead
# THE HELLO and COOL: the tune on the brass, doubled an octave below. ENOUGH:
# the same shapes yelled, a detuned saw pushed through a narrow resonant band
# and distortion so it honks like a voice through a speaker, doubled an octave
# up. HONG: the scoop, quietly, on the lute.
live_loop :matt_lead, sync: :matt_clock do
  bar = tick(:lead) % 16
  phrase = matt_tune[bar]
  if bar >= 8 && bar < 12
    # :nrbpf normalises its output to full scale, so the level is set here, at
    # the very end, not by the synths going in.
    with_fx :distortion, distort: 0.55, mix: 0.6, amp: 0.34 do
      with_fx :nrbpf, centre: 86, res: 0.25, mix: 0.65 do
        phrase.each do |n, dur|
          synth :dsaw, note: n, amp: 0.5, attack: 0.015, sustain: dur * 0.7,
            release: 0.15, cutoff: 112, detune: 0.2
          synth :dsaw, note: note(n) + 12, amp: 0.26, attack: 0.015,
            sustain: dur * 0.65, release: 0.15, cutoff: 110, detune: 0.15
          sleep dur
        end
      end
    end
  elsif bar == 12 || bar == 13
    with_fx :reverb, room: 0.8, mix: 0.4 do
      phrase.each do |n, dur|
        synth :pluck, note: n, amp: 0.78, coef: 0.2, release: 1.2
        sleep dur
      end
    end
  else
    lift = bar >= 14 ? 1.08 : 1.0
    with_fx :reverb, room: 0.55, mix: 0.22 do
      phrase.each do |n, dur|
        synth :tb303, note: n, amp: 0.65 * lift, attack: 0.02, sustain: dur * 0.6,
          release: 0.22, wave: 0, res: 0.15, cutoff_min: 70, cutoff: 110,
          cutoff_attack: 0.05, cutoff_decay: 0.3, cutoff_sustain_level: 0.5
        synth :prophet, note: note(n) - 12, amp: 0.37 * lift, attack: 0.02,
          sustain: dur * 0.55, release: 0.25, cutoff: 96, res: 0.2
        sleep dur
      end
    end
  end
end

# -------------------------------------------------------------------- roar
# His voice. Bar 8's last beat is the breath in, a filtered noise swell. Bar 9
# is ENOUGH: a detuned power chord and a noise burst through a resonant band
# that closes as the pitch falls. Bar 11 sweeps up at him. Bar 12 is THE ROAR,
# a whole bar of it that swells, peaks and falls away. Bar 13 is the breath
# out, which is the first thing he does to calm down.
live_loop :matt_roar, sync: :matt_clock do
  bar = tick(:roar) % 16
  if bar == 7
    sleep 3
    inhale = synth :bnoise, amp: 0.3, attack: 0.9, sustain: 0, release: 0.06,
      cutoff: 70, cutoff_slide: 0.9
    control inhale, cutoff: 112
    sleep 1
  elsif bar == 8
    sample :misc_cineboom, amp: 0.45, sustain: 2, release: 2
    with_fx :distortion, distort: 0.7, mix: 0.75, amp: 0.6 do
      with_fx :nrbpf, centre: 88, res: 0.35, centre_slide: 1.6 do |band|
        low = synth :dsaw, note: :bb2, amp: 0.55, attack: 0.01, sustain: 0.7,
          release: 0.9, detune: 0.3, cutoff: 112, note_slide: 1.6
        high = synth :dsaw, note: :f3, amp: 0.45, attack: 0.01, sustain: 0.7,
          release: 0.9, detune: 0.3, cutoff: 112, note_slide: 1.6
        synth :bnoise, amp: 0.35, attack: 0.01, sustain: 0.3, release: 1.0, cutoff: 112
        control low, note: :eb2
        control high, note: :bb2
        control band, centre: 74
        sleep 4
      end
    end
  elsif bar == 10
    with_fx :distortion, distort: 0.6, mix: 0.6, amp: 0.6 do
      with_fx :nrbpf, centre: 74, res: 0.3, centre_slide: 2 do |band|
        low = synth :dsaw, note: :eb3, amp: 0.4, attack: 1.2, sustain: 0.6,
          release: 0.5, detune: 0.3, cutoff: 110, note_slide: 2
        high = synth :dsaw, note: :bb3, amp: 0.34, attack: 1.2, sustain: 0.6,
          release: 0.5, detune: 0.3, cutoff: 110, note_slide: 2
        swell = synth :bnoise, amp: 0.28, attack: 1.4, sustain: 0.3, release: 0.4,
          cutoff: 80, cutoff_slide: 2
        control low, note: :f3
        control high, note: :c4
        control swell, cutoff: 118
        control band, centre: 90
        sleep 4
      end
    end
  elsif bar == 11
    with_fx :distortion, distort: 0.75, mix: 0.7, amp: 0.45 do
      with_fx :nrbpf, centre: 76, res: 0.35, centre_slide: 1.5 do |band|
        voices = [:f2, :c3, :f3].map do |n|
          synth :dsaw, note: n, amp: 0.4, attack: 0.25, sustain: 3.0, release: 0.8,
            detune: 0.35, cutoff: 115, note_slide: 1.5
        end
        breath = synth :bnoise, amp: 0.3, attack: 0.3, sustain: 2.8, release: 0.9,
          cutoff: 90, cutoff_slide: 1.5
        control band, centre: 92
        control breath, cutoff: 120
        voices.zip([:c3, :g3, :c4]).each { |v, n| control v, note: n }
        sleep 2
        # and down an octave, with the bass's dive, as the air goes out of him
        control band, centre: 70, centre_slide: 2
        voices.zip([:f1, :c2, :f2]).each { |v, n| control v, note: n, note_slide: 2 }
        control breath, cutoff: 80, cutoff_slide: 2
        sleep 2
      end
    end
  elsif bar == 12
    with_fx :reverb, room: 0.8, mix: 0.45 do
      out = synth :bnoise, amp: 0.22, attack: 0.08, sustain: 0.6, release: 1.6,
        cutoff: 100, cutoff_slide: 2.2
      control out, cutoff: 62
      sleep 4
    end
  else
    sleep 4
  end
end
