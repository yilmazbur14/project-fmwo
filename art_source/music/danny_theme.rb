# DANNY — "Four Hundred Pounds of Nap", draft 2 (the intense version)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 ran at 80 bpm and committed hard to the joke: enormous, late, asleep.
# The problem is that it stayed asleep. The half that was meant to be the
# hundred-hand slap could not get anywhere, because the tempo it had to start
# from was a nap.
#
# The fix is the oldest one there is: THE WHOLE PIECE IS AT 160 AND THE FIRST
# HALF IS WRITTEN IN HALF TIME. Every sleeping bar has notes twice as long as
# the grid, so it still drags exactly the way draft 1 dragged and still feels
# like 80. Then he wakes up, the writing switches to the real grid, and the
# second half is twice the speed of the first without a single tempo change —
# and the slap roll on top of that runs sixteenths and then thirty-seconds.
#
# Reference, for intensity: ASGORE, for the way the slow half can still have
# pressure underneath it instead of being empty, and MEGALOVANIA, for the
# sixteenth-note floor under the fast half that never once lets up. Written in
# that spirit, never copied from anything: every note here is ours, so it can
# ship in a public repo.
#
# Danny walks in at the same tiny size he was in the training room, rips his
# shirt and evolves into a mountain who would rather be in bed. So the first
# half is enormous and late, with a breath under it you can feel in your chest
# and an audible snore with a bubble popping in it. Then he opens his eyes.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. Any voice can be commented out to hear the rest.
#
# 160 bpm, D hirajoshi (D E F A Bb) — the Japanese pentatonic with the two
# half-steps that make a shamisen sound like a shamisen. 16-bar cycle:
#   Bars 1-6    THE WEIGHT        — D D Bb Bb F F, written in half time: lazy,
#                                   dragged, snoring, with a sub underneath.
#   Bars 7-8    THE SHIRT         — he stirs. The roll starts, the breath goes
#                                   ragged, and the pitch climbs out of the nap.
#   Bars 9-16   THE HUNDRED HANDS — D D Bb Bb C C D D at full speed. The C
#                                   natural is new, and it is him opening his
#                                   eyes. The slap runs 16ths, then 32nds.

use_bpm 160

# ------------------------------------------------------------------- taiko
# The big drum. Asleep it plays twice a bar with a drag in front of the second
# hit, which is the swagger: he gets there, just late. Awake it squares up and
# hits everything.
live_loop :danny_taiko do
  bar = tick(:bar) % 16
  awake = bar >= 8
  stirring = bar == 6 || bar == 7
  sample :drum_splash_hard, amp: 0.3, rate: 0.5 if bar == 0    # the bow
  sample :drum_splash_hard, amp: 0.95, rate: 0.45 if bar == 8  # the shirt goes
  16.times do |s|
    if awake
      sample :bd_boom, amp: 1.85, rate: 0.6 if s % 4 == 0
      sample :bd_boom, amp: 1.0, rate: 0.7 if [6, 14].include?(s)
      sample :drum_snare_hard, amp: 0.6, rate: 0.85 if s == 4 || s == 12
      sample :drum_cymbal_closed, amp: 0.2, rate: 0.8 if s.odd?
      sample :drum_tom_lo_hard, amp: 0.8, rate: 0.7 if bar == 15 && s >= 12
    elsif stirring
      sample :bd_boom, amp: 1.7, rate: 0.55 if s == 0 || s == 8
      sample :drum_tom_lo_hard, amp: 0.5 + s * 0.02, rate: 0.65 if s % 2 == 0
      sample :drum_cymbal_closed, amp: 0.15, rate: 0.7 if bar == 7 && s.odd?
    else
      sample :bd_boom, amp: 1.75, rate: 0.55 if s == 0
      sample :drum_tom_lo_hard, amp: 0.4, rate: 0.6 if s == 9    # the drag
      sample :bd_boom, amp: 1.3, rate: 0.6 if s == 10            # the late one
      sample :drum_tom_mid_hard, amp: 0.26, rate: 0.7 if s == 6 && bar.even?
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- sub
# What draft 1 was missing under the sleeping half: a breath. Long, low and
# slow while he is out, sixteenths once he is up. The slow half is not quiet
# any more, it is just still — there is a difference, and it is this loop.
live_loop :danny_sub, sync: :danny_taiko do
  root = note((ring :d1, :d1, :bb0, :bb0, :f1, :f1, :d1, :d1,
               :d1, :d1, :bb0, :bb0, :c1, :c1, :d1, :d1).tick(:sub))
  bar = look(:bar) % 16
  use_synth :tb303
  with_fx :distortion, distort: 0.3, mix: 0.4 do
    if bar >= 8
      # Awake: a floor that never stops moving.
      [0, 0, 12, 0, 0, 7, 0, 0, 0, 0, 12, 0, 7, 5, 3, 0].each_with_index do |off, s|
        play root + off, amp: (s % 4 == 0 ? 0.9 : 0.58),
          attack: 0.004, sustain: 0.05, release: 0.13, res: 0.85,
          cutoff: 80 + (s % 4 == 0 ? 16 : 0)
        sleep 0.25
      end
    elsif bar == 6 || bar == 7
      # Stirring: the breath goes ragged and starts climbing.
      8.times do |i|
        play root + (i >= 4 ? 12 : 0), amp: 0.5 + i * 0.04,
          attack: 0.01, sustain: 0.18, release: 0.2, res: 0.8, cutoff: 62 + i * 5
        sleep 0.5
      end
    else
      # Asleep: two enormous breaths a bar, in and out.
      play root, amp: 0.75, attack: 0.5, sustain: 1.0, release: 0.5, res: 0.7, cutoff: 58
      sleep 2
      play root, amp: 0.5, attack: 0.5, sustain: 0.8, release: 0.7, res: 0.7, cutoff: 52
      sleep 2
    end
  end
end

# ---------------------------------------------------------------- shamisen
# The tune, struck hard and left to decay. Asleep it is written in half time, so
# every note is twice the length of the grid and the line sags. Awake it plays
# on the grid, doubled an octave down, and stops sagging entirely.
live_loop :danny_shamisen, sync: :danny_taiko do
  weight = [
    [:d4, 3], [:f4, 1],                                                    # D  — one note, held
    [:e4, 2], [:d4, 2],                                                    # D  — and down
    [:bb3, 3], [:a3, 1],                                                   # Bb — lower still
    [:f4, 2], [:e4, 2],                                                    # Bb — barely awake
    [:f4, 2], [:a4, 1.5], [:f4, 0.5],                                      # F  — a flicker
    [:e4, 3], [nil, 1],                                                    # F  — gone again
    [:a4, 2], [:bb4, 1], [:a4, 1],                                         # A  — the half-step
    [:f4, 2], [:e4, 1], [:d4, 1]                                           # A  — and out
  ]
  hands = [
    [:d5, 0.5], [:f5, 0.5], [:e5, 0.5], [:d5, 0.5], [:a4, 1], [:d5, 1],    # D  — eyes open
    [:f5, 0.5], [:e5, 0.5], [:d5, 0.5], [:c5, 0.5], [:d5, 2],              # D  — the C arrives
    [:bb4, 0.5], [:d5, 0.5], [:f5, 0.5], [:bb5, 0.5], [:a5, 1], [:f5, 1],  # Bb — climbing
    [:e5, 0.5], [:f5, 0.5], [:d5, 1], [:bb4, 2],                           # Bb — held
    [:c5, 0.5], [:e5, 0.5], [:g5, 0.5], [:c6, 0.5], [:bb5, 1], [:g5, 1],   # C  — the new chord
    [:a5, 0.5], [:g5, 0.5], [:e5, 1], [:c5, 2],                            # C  — driving
    [:d5, 0.5], [:e5, 0.5], [:f5, 0.5], [:a5, 0.5], [:bb5, 1], [:a5, 1],   # D  — hammering
    [:f5, 1], [:e5, 1], [:d5, 2]                                           # D  — and again
  ]
  bar = look(:bar) % 16
  awake = bar >= 8
  use_synth :pluck
  with_fx :reverb, room: 0.6, mix: 0.25 do
    (awake ? hands : weight).each do |n, dur|
      unless n.nil?
        play n, amp: awake ? 0.7 : 0.5, coef: awake ? 0.3 : 0.6
        if awake
          synth :dsaw, note: note(n) - 12, amp: 0.24, attack: 0.01,
            sustain: dur * 0.4, release: 0.22, cutoff: 96, detune: 0.16
        end
      end
      sleep dur
    end
  end
end

# ------------------------------------------------------------------- snore
# Bars 1-6 only. In, out, and a bubble popping on the way out. This is the joke,
# and it is funnier now that there is something enormous breathing under it.
live_loop :danny_snore, sync: :danny_taiko do
  bar = look(:bar) % 16
  if bar < 6 && bar.even?
    use_synth :hollow
    breathe_in = play :d3, amp: 0.34, attack: 0.9, sustain: 0.3, release: 0.6,
      note_slide: 1.2, res: 0.5, noise: 2, cutoff: 70
    control breathe_in, note: :f3
    sleep 2
    play :bb2, amp: 0.26, attack: 0.5, sustain: 0.4, release: 0.9,
      res: 0.4, noise: 2, cutoff: 60
    sleep 1.5
    sample :elec_blup, amp: 0.3, rate: 0.55   # the bubble
    sleep 0.5
  else
    sleep 4
  end
end

# -------------------------------------------------------------------- slap
# THE HUNDRED HANDS. It starts in bar 7 as a stir, and from bar 9 it is the
# loudest thing in the piece: sixteenths for four bars, then thirty-seconds,
# and bar 16 is one long roll into the top of the loop.
live_loop :danny_slap, sync: :danny_taiko do
  bar = look(:bar) % 16
  if bar == 7
    # The stir. Slow, then not slow.
    [0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5].each_with_index do |gap, i|
      sample :elec_hi_snare, amp: 0.3 + i * 0.03, rate: 1.1
      sleep gap
    end
  elsif bar >= 8 && bar < 12
    16.times do |s|
      sample :elec_hi_snare, amp: s.even? ? 0.5 : 0.32, rate: 1.15 + (s % 4) * 0.04
      sleep 0.25
    end
  elsif bar >= 12 && bar < 15
    32.times do |s|
      sample :elec_hi_snare, amp: s.even? ? 0.42 : 0.24, rate: 1.2 + (s % 8) * 0.03
      sleep 0.125
    end
  elsif bar == 15
    # One roll, accelerating, and a hit that starts the whole thing over.
    gaps = [0.25] * 4 + [0.125] * 8 + [0.0625] * 16
    gaps.each_with_index do |gap, i|
      sample :elec_hi_snare, amp: 0.3 + i * 0.012, rate: 1.2
      sleep gap
    end
    sample :drum_heavy_kick, amp: 1.9
    sample :drum_splash_hard, amp: 0.8, rate: 0.5
    sleep 4 - gaps.sum
  else
    sleep 4
  end
end
