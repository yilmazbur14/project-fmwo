# ERIC — "Ride for the King", draft 2 (the war version)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 was a stately procession. This is the army moving out: 138 bpm, a
# galloping war drum, open fifths instead of full chords (the martial sound),
# a horn theme that declaims instead of sings, and a shouted chant when the
# charge starts. Same key and the same medieval mode, so it still reads as
# Eric, but it's a boss fight now.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run twice through the
# 16 bars, hit Rec again to save a WAV.
#
# The form is a 16-bar cycle at 138 bpm that loops:
#   Bars 1-8   THE MARCH   — Dm Dm Bb Bb F F C C, the horn call over the gallop
#   Bars 9-16  THE CHARGE  — Dm Dm Bb Bb C C Dm Dm, melody an octave up,
#                            chant on the downbeats, drums doubling
# Every voice is a live_loop synced to the drums, so you can comment one out
# to hear the rest. Draft 1 is beside this file as eric_theme_v1_march.rb.

use_bpm 138

# --------------------------------------------------------------- war drums
# A gallop, not a march: DUM-da-DUM in each half bar, snare on the backbeats,
# and a tom roll into each new phrase. The charge adds off-beat hits.
live_loop :war_drums do
  bar = tick(:bar) % 16
  charge = bar >= 8
  sample :drum_cymbal_open, amp: 0.5, rate: 0.8 if bar == 0 || bar == 8
  16.times do |s|
    sample :bd_boom, amp: 1.7, rate: 0.85 if [0, 3, 4, 8, 11, 12].include?(s)
    sample :bd_boom, amp: 1.1, rate: 0.9 if charge && [6, 14].include?(s)
    sample :drum_snare_soft, amp: 0.7 if s == 4 || s == 12
    sample :drum_snare_soft, amp: 0.35, rate: 1.2 if charge && [7, 15].include?(s)
    sample :drum_tom_lo_hard, amp: 0.8 if (bar == 7 || bar == 15) && s >= 12
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# The horses. Root on the gallop rhythm, with the fifth pushing into the bar.
live_loop :war_bass, sync: :war_drums do
  root = (ring :d2, :d2, :bb1, :bb1, :f2, :f2, :c2, :c2,
          :d2, :d2, :bb1, :bb1, :c2, :c2, :d2, :d2).tick(:bass)
  use_synth :tri
  with_fx :lpf, cutoff: 85 do
    [[0.75, 1.0], [0.25, 0.5], [1.0, 0.9], [0.75, 1.0], [0.25, 0.5], [1.0, 0.9]].each do |dur, amp|
      play root, amp: amp * 0.9, attack: 0.01, release: dur * 0.9
      sleep dur
    end
  end
end

# ------------------------------------------------------- shields (stabs)
# Open fifths, no thirds. Thirds sound courtly; fifths sound like armour.
live_loop :war_stabs, sync: :war_drums do
  root = (ring :d3, :d3, :bb2, :bb2, :f3, :f3, :c3, :c3,
          :d3, :d3, :bb2, :bb2, :c3, :c3, :d3, :d3).tick(:stab)
  bar = look(:bar) % 16
  use_synth :dsaw
  with_fx :reverb, room: 0.6, mix: 0.25 do
    8.times do |i|
      on = bar < 8 ? [1, 3, 5, 7].include?(i) : [0, 2, 3, 5, 6, 7].include?(i)
      play [root, root + 7, root + 12], amp: 0.34, attack: 0.005, release: 0.22, cutoff: 92, detune: 0.15 if on
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- horn
# The theme. Dotted and declamatory: a call you could shout orders over.
# [note, beats]; nil is a rest.
live_loop :war_horn, sync: :war_drums do
  march = [
    [:a4, 1.5], [:d5, 0.5], [:f5, 1], [:e5, 1],          # Dm — the call
    [:d5, 1.5], [:e5, 0.5], [:f5, 2],                    # Dm — answered
    [:g5, 1.5], [:f5, 0.5], [:e5, 1], [:d5, 1],          # Bb — pressing
    [:c5, 2], [:d5, 2],                                  # Bb — gathering
    [:f5, 1.5], [:g5, 0.5], [:a5, 1], [:g5, 1],          # F  — lifting
    [:f5, 1.5], [:e5, 0.5], [:d5, 2],                    # F  — settling
    [:e5, 1], [:f5, 1], [:g5, 1], [:a5, 1],              # C  — the climb
    [:g5, 2], [nil, 2]                                   # C  — room for the roll
  ]
  charge = [
    [:d6, 1], [:c6, 0.5], [:bb5, 0.5], [:a5, 2],         # Dm — the charge
    [:a5, 1], [:bb5, 0.5], [:c6, 0.5], [:d6, 2],         # Dm — rising
    [:f6, 1.5], [:e6, 0.5], [:d6, 2],                    # Bb — the banner
    [:c6, 1], [:d6, 1], [:e6, 2],                        # Bb — held
    [:f6, 1.5], [:e6, 0.5], [:d6, 1], [:c6, 1],          # C  — driving
    [:bb5, 2], [:a5, 2],                                 # C  — the turn
    [:d6, 1], [:a5, 1], [:d6, 1], [:f6, 1],              # Dm — hammering
    [:e6, 2], [nil, 2]                                   # Dm — and again
  ]
  use_synth :prophet
  with_fx :reverb, room: 0.8, mix: 0.3 do
    (march + charge).each do |n, dur|
      unless n.nil?
        play n, amp: 0.78, attack: 0.02, sustain: dur * 0.55, release: 0.35, cutoff: 104
        play n - 12, amp: 0.3, attack: 0.02, sustain: dur * 0.5, release: 0.3, cutoff: 80
      end
      sleep dur
    end
  end
end

# ------------------------------------------------------------------- chant
# Bars 9-16 only: a shout on every downbeat, the way an army answers a horn.
live_loop :war_chant, sync: :war_drums do
  bar = look(:bar) % 16
  if bar >= 8
    use_synth :hollow
    with_fx :reverb, room: 0.9, mix: 0.55 do
      4.times do |i|
        if i.even?
          play [:d4, :a4], amp: 0.4, attack: 0.01, sustain: 0.25, release: 0.35, res: 0.4
          sample :drum_tom_mid_hard, amp: 0.35, rate: 0.9
        end
        sleep 1
      end
    end
  else
    sleep 4
  end
end

# ---------------------------------------------------------------- fanfare
# Optional opener: the herald's call before the first gallop. Uncomment,
# press Run, then comment it out again so the loop stays clean.
#
# use_synth :blade
# with_fx :reverb, room: 0.9 do
#   [[:d4, 0.5], [:a4, 0.25], [:d5, 0.75], [:c5, 0.5], [:d5, 1.5], [:a5, 1.5]].each do |n, dur|
#     play n, amp: 0.85, attack: 0.01, sustain: dur * 0.6, release: 0.4
#     play n - 12, amp: 0.4, attack: 0.01, sustain: dur * 0.6, release: 0.4
#     sleep dur
#   end
# end
