# MASON — "Snack Run", draft 2 (the intense version)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 was a circus band running for its life: quirky, restless, and light on
# its feet. The restlessness was right and it stays. What it did not have was
# weight — it was a chase, but nothing in it could hurt you, and Mason is still
# a boss. This is the same band at 165 with a stomp under it, a distorted bass
# running sixteenths the whole way, and a nugget storm at the end that is
# genuinely a threat instead of a punchline.
#
# Reference, for intensity: MEGALOVANIA, for a low end that never stops moving
# and accents that land off where you brace for them, and ASGORE, for the way a
# theme can be enormous and still be a tune you can hum. Written in that spirit,
# never copied from anything: every note here is ours, so it can ship in a
# public repo, unlike the track Mason borrows today (the user's own
# mason_theme_local.mp3, gitignored because those rights are not ours).
#
# That placeholder measures 115 bpm on a steady grid — measured, not guessed, by
# art_source/mason_tuning/measure_mason_theme.gd. Draft 1 sat just above it at
# 132. This sits well above it, because what the user likes about the original
# is the restlessness, and restlessness at 165 with sixteenths under it is a
# different animal from restlessness at 132 with an oompah under it.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run twice through the 16 bars,
# hit Rec again to save a WAV.
#
# 165 bpm, B minor, with the A# of the harmonic minor saved for the F# chords —
# that raised note is the whole comedy-sinister flavour, so it only shows up
# when the music is winding up to do something.
#
# 16-bar cycle, written to Mason's actual cycle:
#   Bars 1-8    THE LINE   — Bm Bm G G Em Em F# F#. The waddle, now a stomp:
#                            four on the floor, the bass in sixteenths, brass
#                            stabs on the offbeats. Bars 4 and 8 still STOP
#                            DEAD on the last beat — that is the squat — and a
#                            ripple of pops runs the line off before the band
#                            bolts back in. Eight bars is roughly one phase-one
#                            cycle of bomb lines.
#   Bars 9-12   THE SLAM   — Bm Bm Bb Bb. He is on the phone. Two telegraph-and-
#                            land pairs a bar, the kit doubles, and the harmony
#                            slips down a semitone to Bb halfway, which is the
#                            cheapest joke in music and exactly right here.
#   Bars 13-16  THE STORM  — Am Am G F#. The nugget meteor. Falling cascades
#                            over a bass walking chromatically down, a tom roll
#                            under all of it, and a wind-up on F# — the A# lands
#                            here — that throws you back to bar 1.
# Every voice is a live_loop synced to the kit, so you can comment one out.

use_bpm 165

# --------------------------------------------------------------------- kit
# Draft 1 skipped off the beat and kept the low end out of it. This one plants
# four on the floor and lets the woodblock keep the joke. Still shuts up for the
# last beat of bars 4 and 8, because the squat is the funniest thing he does.
live_loop :mason_kit do
  bar = tick(:bar) % 16
  slam = bar >= 8 && bar < 12
  storm = bar >= 12
  squat = bar == 3 || bar == 7
  sample :drum_cymbal_open, amp: 0.45, rate: 1.2 if bar == 0
  sample :drum_splash_hard, amp: 0.7, rate: 0.75 if bar == 8 || bar == 12
  16.times do |s|
    quiet = squat && s >= 12
    unless quiet
      sample :bd_haus, amp: 1.5 if s % 4 == 0
      sample :bd_haus, amp: 0.85 if (slam || storm) && [6, 14].include?(s)
      sample :drum_snare_hard, amp: 0.6, rate: 1.1 if s == 4 || s == 12
      sample :drum_snare_soft, amp: 0.25, rate: 1.4 if slam && [7, 15].include?(s)
      sample :drum_cymbal_closed, amp: 0.2, rate: 1.25 if s.odd?
      sample :elec_blip2, amp: 0.3, rate: 1.6 if !slam && !storm && [2, 10].include?(s)
      sample :drum_tom_lo_hard, amp: 0.7, rate: 0.8 if storm && s % 4 == 2
      sample :drum_tom_mid_hard, amp: 0.75, rate: 0.9 if bar == 15 && s >= 12
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# Sixteenths all the way through, and the only rest it takes is the squat. In
# the storm it walks down chromatically, which is what turns the joke sinister.
live_loop :mason_bass, sync: :mason_kit do
  root = note((ring :b1, :b1, :g1, :g1, :e1, :e1, :fs1, :fs1,
               :b1, :b1, :bb1, :bb1, :a1, :a1, :g1, :fs1).tick(:bass))
  bar = look(:bar) % 16
  squat = bar == 3 || bar == 7
  # Semitones off the bar root; nil is a rest.
  waddle = [0, nil, 0, 12, 0, nil, 7, 0, 0, nil, 0, 12, 0, 7, 0, nil]
  heavy  = [0, 0, 12, 0, 0, 0, 12, 7, 0, 0, 12, 0, 7, 5, 3, 0]
  walk   = [0, 0, 12, 0, 3, 2, 1, 0, 0, 0, 12, 0, 5, 3, 2, 1]
  pattern = if bar >= 12 then walk elsif bar >= 8 then heavy else waddle end
  use_synth :tb303
  with_fx :distortion, distort: 0.32, mix: 0.45 do
    pattern.each_with_index do |off, s|
      if squat && s >= 12
        sleep 0.25
        next
      end
      unless off.nil?
        play root + off, amp: (s % 4 == 0 ? 0.88 : 0.56),
          attack: 0.004, sustain: 0.045, release: 0.12, res: 0.82,
          cutoff: 76 + (bar >= 8 ? 20 : 0) + (s % 4 == 0 ? 14 : 0)
      end
      sleep 0.25
    end
  end
end

# ------------------------------------------------------------------ oompah
# The band. Draft 1 put this on the offbeats and left it there; it still lands
# off the beat in the line, because that is the waddle, but in the slam and the
# storm it squares up onto the downbeats and gets a fifth added underneath.
live_loop :mason_oompah, sync: :mason_kit do
  root = note((ring :b3, :b3, :g3, :g3, :e3, :e3, :fs3, :fs3,
               :b3, :b3, :bb3, :bb3, :a3, :a3, :g3, :fs3).tick(:oom))
  bar = look(:bar) % 16
  squat = bar == 3 || bar == 7
  use_synth :dsaw
  with_fx :reverb, room: 0.45, mix: 0.18 do
    8.times do |i|
      if squat && i >= 6
        sleep 0.5
        next
      end
      on = bar >= 8 ? [0, 2, 4, 6].include?(i) : i.odd?
      if on
        chord_notes = bar >= 8 ? [root, root + 7, root + 12] : [root, root + 7]
        play chord_notes, amp: 0.3, attack: 0.004, sustain: 0.05,
          release: 0.22, cutoff: 94, detune: 0.18
      end
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- lead
# The tune, and the one thing that must stay funny. Skipping in the line,
# barking in the slam, and falling out of the sky in the storm. Doubled an
# octave down on a saw from the slam onward. [note, beats]; nil is a rest.
live_loop :mason_lead, sync: :mason_kit do
  waddle = [
    [:b4, 0.5], [:d5, 0.5], [:fs5, 0.5], [:d5, 0.5], [:b4, 1], [:fs4, 1],   # Bm — the waddle
    [:b4, 0.5], [:cs5, 0.5], [:d5, 1], [:b4, 1], [nil, 1],                  # Bm — the squat
    [:g4, 0.5], [:b4, 0.5], [:d5, 0.5], [:g5, 0.5], [:fs5, 1], [:d5, 1],    # G  — off again
    [:e5, 0.5], [:d5, 0.5], [:b4, 1], [:d5, 2],                             # G  — coasting
    [:e4, 0.5], [:g4, 0.5], [:b4, 0.5], [:e5, 0.5], [:d5, 1], [:b4, 1],     # Em — climbing
    [:g5, 0.5], [:fs5, 0.5], [:e5, 1], [:b4, 2],                            # Em — dropping
    [:fs4, 0.5], [:as4, 0.5], [:cs5, 0.5], [:fs5, 0.5], [:e5, 1], [:cs5, 1],# F# — the raised 7th
    [:as4, 1], [:cs5, 1], [:fs5, 1], [nil, 1]                               # F# — and the squat
  ]
  slam = [
    [:b5, 0.5], [:b5, 0.5], [:fs5, 1], [:d5, 1], [:b4, 1],                  # Bm — answer it
    [:d5, 1], [:fs5, 1], [:b5, 2],                                          # Bm — held
    [:bb5, 0.5], [:bb5, 0.5], [:f5, 1], [:db5, 1], [:bb4, 1],               # Bb — a semitone down
    [:db5, 1], [:f5, 1], [:bb5, 2]                                          # Bb — the joke lands
  ]
  storm = [
    [:a5, 0.5], [:g5, 0.5], [:e5, 0.5], [:c5, 0.5], [:a4, 1], [:e5, 1],     # Am — first cascade
    [:a5, 0.5], [:g5, 0.5], [:e5, 0.5], [:c5, 0.5], [:a4, 2],               # Am — second
    [:g5, 0.5], [:d5, 0.5], [:b4, 0.5], [:g4, 0.5], [:d5, 1], [:b4, 1],     # G  — third
    [:fs5, 1], [:as5, 1], [:cs6, 1], [:fs6, 1]                              # F# — the wind-up
  ]
  bar = look(:bar) % 16
  table = if bar >= 12 then storm elsif bar >= 8 then slam else waddle end
  big = bar >= 8
  use_synth :blade
  with_fx :reverb, room: 0.5, mix: 0.2 do
    table.each do |n, dur|
      unless n.nil?
        play n, amp: 0.58, attack: 0.01, sustain: dur * 0.5, release: 0.22,
          cutoff: 106, vibrato_rate: 6
        if big
          synth :dsaw, note: note(n) - 12, amp: 0.26, attack: 0.01,
            sustain: dur * 0.45, release: 0.24, cutoff: 98, detune: 0.16
        end
      end
      sleep dur
    end
  end
end

# ----------------------------------------------------------------- moments
# The four things the fight does, and the only bars where this stops being a
# groove and becomes an event.
live_loop :mason_moments, sync: :mason_kit do
  bar = look(:bar) % 16
  if bar == 3 || bar == 7
    # THE SQUAT. The band stops dead and a ripple of pops runs the line off.
    sleep 3
    6.times do |i|
      sample :elec_blup, amp: 0.45, rate: 0.7 + i * 0.12
      sleep 1.0 / 6
    end
  elsif bar == 8 || bar == 10
    # THE PHONE. Two rings, then he swings.
    sleep 2
    use_synth :chiplead
    2.times do
      play :b5, amp: 0.3, release: 0.12
      sleep 0.25
      play :fs5, amp: 0.3, release: 0.12
      sleep 0.25
    end
    sample :drum_heavy_kick, amp: 1.5
    sleep 1
  elsif bar >= 12 && bar < 15
    # THE NUGGETS. Three impacts a bar, landing where the cascades land.
    3.times do |i|
      sample :bd_boom, amp: 1.3 - i * 0.1, rate: 0.75
      sample :drum_splash_hard, amp: 0.3, rate: 1.3
      sleep i == 2 ? 2 : 1
    end
  elsif bar == 15
    # THE WIND-UP. He leans back, and the whole thing goes again.
    use_synth :dsaw
    rise = play :fs3, amp: 0.4, attack: 0.02, sustain: 3.2, release: 0.5,
      note_slide: 3.2, cutoff: 92, detune: 0.2
    control rise, note: :fs5
    sleep 3.5
    sample :drum_heavy_kick, amp: 1.7
    sample :drum_cymbal_open, amp: 0.6, rate: 1.1
    sleep 0.5
  else
    sleep 4
  end
end
