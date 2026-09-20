# CARTER — "The Mark Burns", draft 2 (the intense version)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 was dread with nothing under it: 92 bpm, a drone, and silence you
# could hear. Atmospheric, but it was a cutscene, not a fight. This is the same
# man at 150 with an engine under him — sixteenths that never stop, a taiko that
# hits like a body, and a lead that stops asking questions and starts screaming.
#
# What draft 1 got right and this keeps: E phrygian (E F G A B C D). That flat
# second, one half step above the root, is the whole mood, and the bass leans on
# it on purpose.
#
# Reference, for intensity: the way MEGALOVANIA never leaves a sixteenth empty,
# and the way ASGORE builds by stacking layers onto one relentless pulse instead
# of by changing what it is doing. Both are pressure that never releases.
# Written in that spirit, never copied: every note here is ours, so it can ship
# in a public repo, unlike the placeholder track Carter uses today.
#
# Carter is the Satsui-no-Hado one: bald, orange beard, a burning mark on his
# back, and one attack that ends the fight — a locked-in spotlight where red
# clones must be parried and yellow fakes must not. That sequence IS the end of
# this track: bar 15 kills every voice dead, and what comes back is eight stabs,
# four of them real and four of them ghosts. You have to tell them apart.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run twice through the 16 bars,
# hit Rec again to save a WAV. Draft 1 is beside this as carter_theme_v1_dread.rb.
#
# 150 bpm. 16-bar cycle:
#   Bars 1-8    THE STARE  — Em Em F F Em Em C C. Coiled, not quiet: the engine
#                            is already running, the lead is still holding back.
#   Bars 9-14   THE HADO   — Em Em F F C C, the mark lights. Lead in octaves,
#                            stabs on the beat, drums doubled, nothing held back.
#   Bars 15-16  THE DEMON  — everything stops. One footstep. Then the rush.
# Every voice is a live_loop synced to the drums, so you can comment one out.

use_bpm 150

# ------------------------------------------------------------------- taiko
# The body. Eighths in the stare, sixteenths once the mark lights, and a tom
# roll that drags you into each new phrase. Bars 15-16 are empty on purpose.
live_loop :carter_taiko do
  bar = tick(:bar) % 16
  hado = bar >= 8
  demon = bar >= 14
  sample :drum_splash_hard, amp: 0.55, rate: 0.5 if bar == 0
  sample :drum_cymbal_open, amp: 0.7, rate: 0.7 if bar == 8
  16.times do |s|
    unless demon
      sample :bd_boom, amp: 1.8, rate: 0.62 if [0, 6, 8, 14].include?(s)
      sample :bd_boom, amp: 1.1, rate: 0.7 if hado && [3, 11].include?(s)
      sample :drum_snare_hard, amp: 0.66, rate: 0.85 if s == 4 || s == 12
      sample :drum_snare_soft, amp: 0.26, rate: 1.25 if hado && [7, 15].include?(s)
      sample :drum_cymbal_closed, amp: 0.2, rate: 0.75 if hado ? s.odd? : s % 4 == 2
      sample :drum_tom_lo_hard, amp: 0.85, rate: 0.7 if (bar == 7 || bar == 13) && s >= 12
    end
    sleep 0.25
  end
end

# ------------------------------------------------------------------ engine
# The thing draft 1 did not have. Sixteenths on the root with the flat second
# shoving in against it, resonant and distorted, accented off the kick. This is
# what makes the silence in bar 15 mean anything.
live_loop :carter_engine, sync: :carter_taiko do
  root = note((ring :e1, :e1, :f1, :f1, :e1, :e1, :c1, :c1,
               :e1, :e1, :f1, :f1, :c1, :c1, :e1, :e1).tick(:eng))
  bar = look(:bar) % 16
  # Semitones off the bar root; nil is a rest. The stare breathes; the burn does
  # not, and it walks down chromatically into every beat.
  stare = [0, nil, 0, 12, nil, 0, 0, nil, 0, nil, 0, 12, 0, nil, 1, 0]
  burn  = [0, 0, 12, 0, 1, 0, 12, 0, 0, 0, 12, 0, 3, 2, 1, 0]
  use_synth :tb303
  with_fx :distortion, distort: 0.42, mix: 0.55 do
    if bar >= 14
      sleep 4
    else
      (bar >= 8 ? burn : stare).each_with_index do |off, s|
        unless off.nil?
          play root + off, amp: (s % 4 == 0 ? 0.9 : 0.6),
            attack: 0.004, sustain: 0.05, release: 0.13, res: 0.88,
            cutoff: 70 + (bar >= 8 ? 22 : 0) + (s % 4 == 0 ? 16 : 0)
        end
        sleep 0.25
      end
    end
  end
end

# ------------------------------------------------------------------- drone
# Kept from draft 1, because the low E under everything is Carter standing
# there. It is quieter now: it is the floor, not the room.
live_loop :carter_drone, sync: :carter_taiko do
  use_synth :dark_ambience
  with_fx :reverb, room: 0.9, mix: 0.45 do
    play :e1, amp: 0.3, attack: 1, sustain: 10, release: 3, ring: 0.4
  end
  sleep 16
end

# -------------------------------------------------------------------- lead
# Draft 1 asked a two-note question and left. This one answers it. :hollow
# keeps the breathy shakuhachi edge; from the hado it is doubled an octave down
# on a saw, so there is a body behind the breath. [note, beats]; nil is a rest.
live_loop :carter_lead, sync: :carter_taiko do
  stare = [
    [:e5, 1.5], [:f5, 0.5], [:e5, 1], [:b4, 1],           # Em — the two-note question
    [:e5, 1], [:g5, 1], [:f5, 1.5], [:e5, 0.5],           # Em — and it will not drop
    [:f5, 1.5], [:g5, 0.5], [:a5, 2],                     # F  — leaning on the flat two
    [:g5, 1], [:f5, 1], [:e5, 2],                         # F  — back down
    [:e5, 0.5], [:f5, 0.5], [:g5, 1], [:f5, 1], [:e5, 1], # Em — circling
    [:b4, 2], [:e5, 2],                                   # Em — held
    [:c5, 1], [:b4, 1], [:a4, 1], [:g4, 1],               # C  — the descent
    [:a4, 2], [nil, 2]                                    # C  — room for the roll
  ]
  hado = [
    [:e6, 1], [:d6, 0.5], [:c6, 0.5], [:b5, 2],           # Em — the mark lights
    [:c6, 1], [:b5, 0.5], [:a5, 0.5], [:g5, 2],           # Em — coming down
    [:f6, 1.5], [:e6, 0.5], [:d6, 1], [:c6, 1],           # F  — driving
    [:b5, 1], [:c6, 1], [:e6, 2],                         # F  — and it lifts
    [:c6, 0.5], [:b5, 0.5], [:a5, 1], [:g5, 1], [:f5, 1], # C  — hammering
    [:e5, 1], [:f5, 1], [:g5, 2]                          # C  — into the demon
  ]
  bar = look(:bar) % 16
  if bar >= 14
    sleep 8
  else
    big = bar >= 8
    use_synth :hollow
    with_fx :reverb, room: 0.75, mix: 0.4 do
      (big ? hado : stare).each do |n, dur|
        unless n.nil?
          play n, amp: 0.5, attack: 0.05, sustain: dur * 0.5, release: dur * 0.35,
            res: 0.35, noise: 1
          if big
            synth :dsaw, note: note(n) - 12, amp: 0.3, attack: 0.02,
              sustain: dur * 0.45, release: 0.3, cutoff: 96, detune: 0.18
          end
        end
        sleep dur
      end
    end
  end
end

# ------------------------------------------------------------------- stabs
# Open fifths hit hard and cut short: someone appearing where he was not. Off
# the beat while he is staring, square on it once the mark is lit.
live_loop :carter_stabs, sync: :carter_taiko do
  bar = look(:bar) % 16
  if bar >= 14
    sleep 4
  else
    root = note((ring :e3, :e3, :f3, :f3, :e3, :e3, :c3, :c3,
                 :e3, :e3, :f3, :f3, :c3, :c3, :e3, :e3).tick(:stab))
    use_synth :dsaw
    with_fx :reverb, room: 0.6, mix: 0.22 do
      8.times do |i|
        on = bar >= 8 ? [0, 2, 3, 5, 6, 7].include?(i) : [3, 7].include?(i)
        play [root, root + 7], amp: 0.34, attack: 0.002, release: 0.2,
          cutoff: 98, detune: 0.2 if on
        sleep 0.5
      end
    end
  end
end

# ------------------------------------------------------------------- demon
# BARS 15-16. THE SHUN GOKU SATSU. Every other voice is written to fall silent
# here, so this is the only thing in the room.
#
# One footstep, one held breath. Then eight hits land in two beats: four real
# and four ghosts, exactly like the clone sequence in the fight, where red must
# be parried and yellow must not. Then the mark burns and it starts again.
live_loop :carter_demon, sync: :carter_taiko do
  bar = look(:bar) % 16
  if bar == 14
    sample :drum_tom_lo_hard, amp: 1.0, rate: 0.5   # the step
    sleep 2
    sample :ambi_dark_woosh, amp: 0.7, rate: 0.7
    sleep 2
  elsif bar == 15
    use_synth :dsaw
    with_fx :distortion, distort: 0.5, mix: 0.6 do
      8.times do |i|
        real = [0, 2, 3, 6].include?(i)   # red: the ones you have to catch
        sample :elec_hi_snare, amp: real ? 0.9 : 0.25, rate: real ? 0.9 : 1.4
        play [:e3, :f3], amp: real ? 0.45 : 0.14, attack: 0.001,
          release: real ? 0.16 : 0.07, cutoff: real ? 104 : 80, detune: 0.25
        sleep 0.25
      end
    end
    # And the mark burns.
    sample :drum_heavy_kick, amp: 1.8
    sample :drum_splash_hard, amp: 0.8, rate: 0.55
    synth :dsaw, note: :e2, amp: 0.55, attack: 0.002, release: 1.8,
      cutoff: 110, detune: 0.3
    synth :dsaw, note: :e3, amp: 0.4, attack: 0.002, release: 1.6,
      cutoff: 105, detune: 0.3
    sleep 2
  else
    sleep 4
  end
end
