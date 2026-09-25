# DANNY (SUMO) — "Five More Minutes"
# Original music for Project FMWO, written for Sonic Pi 4.x / 5.x.
#
# Boss 7: the training-room helper, evolved into the biggest, sleepiest sumo in
# the game. The piece is his fight: he naps, snores, snorts himself awake,
# throws his weight around, and yawns his way straight back to sleep. One brass
# voice carries all of it: low and sliding while he sleeps, high and fierce
# once he's up, and it's the same voice that yawns at the end.
#
# Not to be confused with danny_theme*.rb ("Four Hundred Pounds of Nap", D
# hirajoshi at 160), which the training room plays. This is a separate piece.
#
# 96 bpm, F minor with the blues in it. 16-bar cycle:
#   Bars 1-6    THE NAP    — Fm Fm Db Db Bbm C7, a heavy lazy shuffle. Taiko
#                            on the slow beats, a wood block ticking like a
#                            clock, and the low brass lumbering up and sliding
#                            back down. Every other bar he snores; the third
#                            snore catches in his nose - HNK! - and stops dead.
#   Bars 7-14   AWAKE      — Fm Fm Db C7, twice, dead straight and twice as
#                            busy: the taiko ensemble in sixteenths, a stomp on
#                            1 and 3, a distorted bass riff, and the brass hook.
#                            The hook opens on the snore's own interval, a
#                            fourth from C up to F, ripped up in a sixteenth
#                            instead of dragged over two beats.
#   Bars 15-16  THE YAWN   — Bbm C7. The brass yawns down an octave, the kit
#                            falls back into the shuffle, and he is asleep again
#                            by bar 1.
#
# HOW TO RECORD: never through the GUI. See music-recording-pipeline:
#   python record_theme.py danny_sumo_theme.rb 96 --out <scratch>/danny_sumo_raw.wav
#   python measure_take.py <scratch>/danny_sumo_raw.wav 96
#   python cut_loop.py <scratch>/danny_sumo_raw.wav 96 --out <scratch>/danny_sumo.wav
# One cycle is 16 bars x 4 beats / 96 bpm = 40.0 s.

use_bpm 96

# ------------------------------------------------------------------ harmony
# One row per bar: [bass root, chord for the haze and the stabs].
define :danny_harmony do
  [
    [:f2,  [:f3, :ab3, :c4]],     # 1  Fm   THE NAP
    [:f2,  [:f3, :ab3, :c4]],     # 2  Fm   snore
    [:db2, [:f3, :ab3, :db4]],    # 3  Db
    [:db2, [:f3, :ab3, :db4]],    # 4  Db   snore
    [:bb1, [:f3, :bb3, :db4]],    # 5  Bbm
    [:c2,  [:e3, :bb3, :c4]],     # 6  C7   snore, HNK!
    [:f2,  [:f3, :ab3, :c4]],     # 7  Fm   AWAKE
    [:f2,  [:f3, :ab3, :c4]],     # 8  Fm
    [:db2, [:f3, :ab3, :db4]],    # 9  Db
    [:c2,  [:e3, :bb3, :c4]],     # 10 C7
    [:f2,  [:f3, :ab3, :c4]],     # 11 Fm
    [:f2,  [:f3, :ab3, :c4]],     # 12 Fm
    [:db2, [:f3, :ab3, :db4]],    # 13 Db
    [:c2,  [:e3, :bb3, :c4]],     # 14 C7
    [:bb1, [:f3, :bb3, :db4]],    # 15 Bbm  THE YAWN
    [:c2,  [:e3, :bb3, :c4]]      # 16 C7
  ]
end

# --------------------------------------------------------------------- tune
# One row per bar: [grid, notes]. The grid is how many steps make a beat: 3 for
# the shuffle's triplets, 4 for the awake sixteenths. Each note is
# [note, steps] or [note, steps, :slide] (glide in from the previous note, the
# sluggish way) or [note, steps, :rip] (fly up to it from a fourth below, the
# awake way). nil is a rest. Every bar is exactly 4 beats of its own grid.
define :danny_tune do
  [
    # ---- THE NAP: the low brass, answered by a snore every other bar
    [3, [[:f3, 6], [:ab3, 3, :slide], [:bb3, 2], [:c4, 1]]],                                  # 1
    [3, [[nil, 12]]],                                                                           # 2
    [3, [[:ab3, 6], [:f3, 3, :slide], [:eb3, 2], [:db3, 1]]],                                 # 3
    [3, [[nil, 12]]],                                                                           # 4
    [3, [[:bb3, 6], [:db4, 3, :slide], [:f4, 2], [:e4, 1]]],                                  # 5
    [3, [[nil, 12]]],                                                                           # 6
    # ---- AWAKE: the hook, twice
    [4, [[:c5, 1], [:f5, 3, :rip], [:eb5, 2], [:c5, 2], [:bb4, 1], [:c5, 1], [:eb5, 2], [:f5, 4]]],       # 7
    [4, [[:ab5, 2], [:f5, 1], [:eb5, 1], [:c5, 2], [:eb5, 2], [:c5, 1], [:bb4, 1], [:ab4, 2], [:f4, 4]]], # 8
    [4, [[:db5, 1], [:f5, 3, :slide], [:ab5, 2], [:f5, 2], [:eb5, 1], [:f5, 1], [:ab5, 2], [:bb5, 4]]],     # 9
    [4, [[:c6, 2], [:bb5, 1], [:g5, 1], [:e5, 2], [:g5, 2], [:bb5, 2], [:g5, 1], [:e5, 1], [:c5, 4]]],    # 10
    [4, [[:c5, 1], [:f5, 3, :rip], [:eb5, 2], [:c5, 2], [:bb4, 1], [:c5, 1], [:eb5, 2], [:f5, 4]]],       # 11
    [4, [[:ab5, 2], [:f5, 1], [:eb5, 1], [:c5, 2], [:eb5, 2], [:c5, 1], [:bb4, 1], [:ab4, 2], [:f4, 4]]], # 12
    [4, [[:db5, 1], [:f5, 3, :slide], [:ab5, 2], [:f5, 2], [:eb5, 1], [:f5, 1], [:ab5, 2], [:bb5, 4]]],     # 13
    [4, [[:c6, 3, :rip], [:bb5, 1], [:g5, 2], [:e5, 2], [:f5, 1], [:g5, 1], [:bb5, 2], [:c6, 4]]],        # 14
    # ---- THE YAWN: down an octave and back into the low brass
    [3, [[:db6, 3], [:f5, 6, :slide], [nil, 3]]],                                             # 15
    [3, [[:c4, 6], [:e4, 3, :slide], [:g4, 2], [:bb3, 1]]]                                    # 16
  ]
end

# Bar-length check, in whole steps so it is exact. Prints nothing when right.
danny_tune.each_with_index do |(grid, phrase), i|
  total = phrase.inject(0) { |t, n| t + n[1] }
  puts "danny_sumo_theme: BAR #{i + 1} is #{total} steps, not #{4 * grid}" unless total == 4 * grid
end

# -------------------------------------------------------------------- brass
# His voice: a saw through the tb303's own filter envelope with a detuned saw
# under it. Asleep it is dark and slow to speak; awake it is bright and quick.
# `from` is where a :slide or :rip starts, and it glides to `n` from there over
# `glide` beats (nil: quick when awake, lazy when not).
define :danny_horn do |n, beats, amp, awake, from, glide|
  target = note(n)
  start = from ? note(from) : target
  glide ||= awake ? 0.08 : 0.35
  a = synth :tb303, note: start, amp: amp, attack: (awake ? 0.01 : 0.08),
    sustain: beats * (awake ? 0.6 : 0.75), release: (awake ? 0.15 : 0.4),
    wave: 0, res: 0.12, cutoff_min: (awake ? 70 : 50), cutoff: (awake ? 110 : 88),
    cutoff_attack: (awake ? 0.02 : 0.25), cutoff_decay: 0.3,
    cutoff_sustain_level: (awake ? 0.5 : 0.35), note_slide: glide
  b = synth :dsaw, note: start, amp: amp * 0.45, attack: (awake ? 0.01 : 0.1),
    sustain: beats * (awake ? 0.55 : 0.7), release: (awake ? 0.15 : 0.4),
    cutoff: (awake ? 100 : 80), detune: 0.14, note_slide: glide
  if start != target
    control a, note: target
    control b, note: target
  end
end

# -------------------------------------------------------------------- clock
# Plays nothing, on purpose: every voice syncs to this and joins on the same
# cue, so they all count the same bars. With the drums as the clock, every
# synced voice would join a bar late and count one bar behind the kit.
live_loop :danny_clock do
  sleep 4
end

# -------------------------------------------------------------------- taiko
# Asleep: a slow shuffle. The big drum on 1 and 3 with a small one dragging in
# behind beat 2, a rim click, and a wood block on every beat like a clock in a
# quiet room. Awake: the ensemble in sixteenths, a big drum on 1 and 3, the
# rim on 2 and 4, a tight small drum running underneath, and hand cymbals on
# the off-beats. The HNK! stops everything for a beat; the yawn rolls off.
live_loop :danny_taiko, sync: :danny_clock do
  bar = tick(:taiko) % 16
  awake = bar >= 6 && bar < 14
  sample :drum_cymbal_hard, amp: 0.6, rate: 0.85 if bar == 6
  sample :drum_cymbal_hard, amp: 0.4, rate: 0.95 if bar == 10
  if awake
    16.times do |s|
      if s == 0 || s == 8
        sample :bd_boom, amp: 1.5, rate: 0.8
        sample :drum_tom_lo_hard, amp: 0.8, rate: 0.65
      end
      sample :drum_tom_mid_hard, amp: 0.45, rate: 0.8 if [3, 6, 11, 14].include?(s)
      if s == 4 || s == 12
        synth :sc808_rimshot, amp: 0.55
        sample :drum_snare_hard, amp: 0.45, rate: 0.9
      end
      sample :drum_tom_hi_hard, amp: (s.even? ? 0.14 : 0.08), rate: 1.45, pan: 0.2
      sample :drum_cymbal_closed, amp: 0.2, rate: 0.8, pan: -0.25 if s % 4 == 2
      if (bar == 9 || bar == 13) && s >= 12
        sample :drum_tom_mid_hard, amp: 0.5 + (s - 12) * 0.12, rate: 0.75
      end
      sleep 0.25
    end
  elsif bar == 14
    12.times do |t|
      sample :drum_tom_lo_hard, amp: 0.7 - t * 0.05, rate: 0.65 if t < 7
      sample :bd_boom, amp: 1.3, rate: 0.75 if t == 0
      sleep 1.0 / 3
    end
  else
    12.times do |t|
      snort = bar == 5 && t >= 6
      unless snort
        if t == 0 || t == 6
          sample :bd_boom, amp: (t == 0 ? 1.5 : 1.2), rate: 0.75
          sample :drum_tom_lo_hard, amp: 0.7, rate: 0.6
        end
        sample :drum_tom_mid_hard, amp: 0.4, rate: 0.75 if t == 5
        synth :sc808_rimshot, amp: 0.4 if t == 6 || t == 11
        synth :sc808_claves, amp: 0.22, pan: -0.3 if t % 3 == 0
      end
      if bar == 5 && t >= 9
        # the eyes open: two big hits into bar 7
        sample :bd_boom, amp: 1.2 + (t - 9) * 0.2, rate: 0.8 if t == 9 || t == 11
        sample :drum_tom_lo_hard, amp: 0.8, rate: 0.7 if t == 9 || t == 11
      end
      sleep 1.0 / 3
    end
  end
end

# -------------------------------------------------------------------- stomp
# The shiko: his weight landing, a tuned 808 on the root. Once a bar while he
# sleeps, on 1 and 3 while he is up.
live_loop :danny_stomp, sync: :danny_clock do
  bar = tick(:stomp) % 16
  root = note(danny_harmony[bar][0])
  root -= 12 while root > 40
  awake = bar >= 6 && bar < 14
  if awake
    synth :sc808_bassdrum, note: root, amp: 0.7, decay: 0.6
    sleep 2
    synth :sc808_bassdrum, note: root, amp: 0.6, decay: 0.6
    sleep 2
  else
    synth :sc808_bassdrum, note: root, amp: 0.6, decay: 1.2 unless bar == 14
    sleep 4
  end
end

# --------------------------------------------------------------------- bass
# Asleep: a lopsided shuffle strut, the root dragged and the fifth or octave
# dropped in on the last triplet. Awake: a distorted sixteenth riff that
# stomps with the kit. The yawn holds one long note.
live_loop :danny_bass, sync: :danny_clock do
  bar = tick(:bass) % 16
  root = note(danny_harmony[bar][0])
  use_synth :tb303
  if bar >= 6 && bar < 14
    # One shape, bent to the chord's third: minor on F, major on Db and C7.
    riff = {
      :f2 => [0, nil, 0, 12, nil, 0, 3, nil, 0, nil, 0, 12, 10, nil, 7, 5],
      :db2 => [0, nil, 0, 12, nil, 0, 4, nil, 0, nil, 0, 12, 7, nil, 4, 2],
      :c2 => [0, nil, 0, 12, nil, 0, 4, nil, 0, nil, 0, 12, 10, nil, 7, 4]
    }[danny_harmony[bar][0]]
    with_fx :distortion, distort: 0.55, mix: 0.5, amp: 0.8 do
      riff.each_with_index do |off, s|
        unless off.nil?
          play root + off, amp: (s % 4 == 0 ? 0.95 : 0.65), attack: 0.004,
            sustain: 0.08, release: 0.12, res: 0.25, cutoff_min: 48,
            cutoff: (s % 4 == 0 ? 82 : 88), wave: 0
        end
        sleep 0.25
      end
    end
  elsif bar == 14
    play root, amp: 0.9, attack: 0.05, sustain: 2.8, release: 1.0, res: 0.2,
      cutoff_min: 40, cutoff: 72, cutoff_attack: 0.5, cutoff_sustain_level: 0.4, wave: 0
    sleep 4
  else
    [[0, 5], [7, 1], [0, 5], [12, 1]].each_with_index do |(off, steps), i|
      if bar == 5 && i >= 2
        sleep steps / 3.0
        next
      end
      play root + off, amp: (off.zero? ? 1.0 : 0.7), attack: 0.01,
        sustain: steps / 3.0 * 0.6, release: 0.25, res: 0.2, cutoff_min: 45,
        cutoff: 80, cutoff_attack: 0.02, cutoff_decay: 0.25, cutoff_sustain_level: 0.4, wave: 0
      sleep steps / 3.0
    end
  end
end

# -------------------------------------------------------------------- brass
# The tune. Asleep it lumbers in a trombone's range, sliding into the notes it
# is too tired to reach properly: an octave above the shuffle bass, because in
# the bass's own octave the two masked each other. Awake it is an octave and a
# half higher with its lower octave under it, and it rips up into the long
# notes. The yawn slides down from the top of it.
live_loop :danny_brass, sync: :danny_clock do
  bar = tick(:brass) % 16
  grid, phrase = danny_tune[bar]
  awake = bar >= 6 && bar < 14
  prev = nil
  with_fx :reverb, room: (awake ? 0.5 : 0.7), mix: (awake ? 0.2 : 0.3) do
    phrase.each do |n, steps, how|
      beats = steps / grid.to_f
      unless n.nil?
        from = case how
               when :slide then prev
               when :rip then note(n) - 5
               end
        if awake
          danny_horn n, beats, 0.54, true, from, nil
          danny_horn note(n) - 12, beats, 0.32, true, (from ? note(from) - 12 : nil), nil
        elsif bar == 14
          # the yawn: still in his awake voice, but the slide takes its time
          danny_horn n, beats, 0.48, true, from, 1.6
        else
          danny_horn n, beats, 0.6, false, from, nil
        end
        prev = n
      end
      sleep beats
    end
  end
end

# -------------------------------------------------------------------- snore
# Bars 2 and 4: in through the nose, a growl sliding up a fourth with a rattle
# in it, then out as a hiss, and the sleep bubble pops. Bar 6's snore goes a
# whole octave, catches - HNK! - on beat 3, and everything stops for a beat.
live_loop :danny_snore, sync: :danny_clock do
  bar = tick(:snore) % 16
  if bar == 1 || bar == 3 || bar == 5
    big = bar == 5
    with_fx :lpf, cutoff: 84 do
      with_fx :slicer, phase: 0.04, mix: 0.6 do
        inhale = synth :dsaw, note: :c2, amp: (big ? 0.78 : 0.62), attack: (big ? 1.7 : 1.5),
          sustain: (big ? 0.3 : 0.2), release: (big ? 0.05 : 0.3), detune: 0.25,
          cutoff: 90, note_slide: (big ? 1.9 : 1.6)
        control inhale, note: (big ? :c3 : :f2)
        sleep 2
      end
    end
    if big
      # HNK!
      synth :tb303, note: :c3, amp: 0.9, attack: 0.005, sustain: 0.08, release: 0.1,
        wave: 0, res: 0.6, cutoff_min: 70, cutoff: 100
      synth :bnoise, amp: 0.45, attack: 0.003, sustain: 0.05, release: 0.12, cutoff: 105
      sleep 2
    else
      exhale = synth :bnoise, amp: 0.3, attack: 0.25, sustain: 0.4, release: 0.8,
        cutoff: 92, cutoff_slide: 1.4
      control exhale, cutoff: 62
      sleep 1.5
      pop = synth :sine, note: :c6, amp: 0.35, attack: 0.002, sustain: 0.02, release: 0.1,
        note_slide: 0.06
      control pop, note: :c7
      sleep 0.5
    end
  else
    sleep 4
  end
end

# --------------------------------------------------------------------- haze
# Asleep: a soft breathy chord, the room he is dreaming in. Awake: short power
# chords on the off-beats, pushing the stomp along.
# noise: on :hollow is enumerated (0-4); it must be an Integer.
live_loop :danny_haze, sync: :danny_clock do
  bar = tick(:haze) % 16
  ch = danny_harmony[bar][1]
  awake = bar >= 6 && bar < 14
  if awake
    root = note(danny_harmony[bar][0]) + 12
    16.times do |s|
      if [2, 7, 10, 15].include?(s)
        [root, root + 7, root + 12].each do |n|
          synth :dsaw, note: n, amp: 0.27, attack: 0.005, sustain: 0.08, release: 0.12,
            cutoff: 96, detune: 0.12
        end
      end
      sleep 0.25
    end
  elsif bar == 5
    use_synth :hollow
    play ch, amp: 0.19, attack: 0.6, sustain: 0.8, release: 0.3, res: 0.3, noise: 1, cutoff: 90
    sleep 4
  else
    use_synth :hollow
    play ch, amp: 0.19, attack: 0.8, sustain: 2.2, release: 1.0, res: 0.3, noise: 1, cutoff: 90
    sleep 4
  end
end
