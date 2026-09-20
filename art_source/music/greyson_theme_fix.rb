# GREYSON & COMPUTAH — "Two Bars", draft 1
#
# ----------------------------------------------------------------------------
# THIS FILE IS DRAFT 1 WITH ONE BUG FIXED AND NOTHING ELSE CHANGED.
#
# Draft 1 has one loop, :gc_stomp, that owns the bar counter via tick(:bar), and
# four loops that read it back with look(:bar). That read does not work. Sonic
# Pi's tick counters are live_loop-local and are not inherited: core.rb's
# ThreadLocalCounter stores them with __thread_locals.set_local, and look on a
# key THIS loop has never ticked returns (val || 0) — 0, forever. It is not a
# race; it is deterministic. So in the shipped recording every `bar >= 8` branch
# below was dead and every `bar == 15` branch never fired:
#
#   gc_bass    played the `chase` pattern for all sixteen bars, never `caught`,
#              and never took the +18 cutoff of the second half
#   gc_servo   never tightened onto the chord tones, never took the octave
#   gc_iron    never moved onto the downbeats — "the catch" never landed
#   gc_moments never played AT ALL: no flat battery, no five-punch combo
#
# The fix is mechanical. Each of those loops already ticks its own key to walk
# its chord ring (:bass, :servo, :iron), and that tick counts bars — so the bar
# is read from it and the ring is indexed with it. gc_moments had no ring, so it
# gets a counter of its own, :moments.
#
# NOT ONE NOTE, TEMPO, KEY, SYNTH OR OPT IS CHANGED. Everything you hear that
# you have not heard before was already written below; it just never ran.
# ----------------------------------------------------------------------------# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Reference feeling: the industrial drive of a robot-master stage crossed with the
# four-on-the-floor stomp of a gym playlist — a machine and a meathead on the same
# track. Written in that spirit, never copied from it: every note here is ours, so
# it can ship in a public repo, unlike the shared placeholder (boss2_theme.ogg)
# the fight loads today.
#
# The title is the fight's own joke: two health bars, two gym bars, sixteen bars
# of music.
#
# TWO BODIES, TWO VOICES. Computah is the bleeping sixteenth-note arpeggio
# (:chiplead) — the robot thinking while he runs you down. Greyson is the blunt
# open-fifth stab (:hoover) — no thirds, no subtlety, just weight. In the first
# half they trade the tune four bars each; in the second half they play it
# together in octaves, which is exactly what the fight does once the catch lands.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run twice through the 16 bars,
# hit Rec again to save a WAV.
#
# 160 bpm, C minor — the fastest thing in the set so far, because this is the
# fight you spend running. The 16-bar cycle is written to the fight's strict A-B
# alternation (laser sweep, then chase, forever); it is not locked to it, since
# the track loops free of the state machine.
#   Bars 1-8   THE CHASE  — Cm Cm Ab Ab Eb Eb Bb Bb. The arp runs, Greyson throws
#                           junk over the top of it on the offbeats, and the tune
#                           is traded: Computah asks (1-4), Greyson answers (5-8).
#                           Bar 8 is the battery going flat — the pitch slides
#                           down and he hits the mat, which is the punish window.
#   Bars 9-16  THE CATCH  — Cm Cm Ab Ab Fm Fm G G. Everything locks onto the same
#                           grid, the tune doubles in octaves, the stabs move onto
#                           the downbeats, and bar 16 is the five-punch combo:
#                           four jabs that do nothing and a fifth that launches
#                           you. G is the only chord here with a natural B in it,
#                           so the wind-up is the one moment that bites.
# Every voice is a live_loop synced to the drums, so you can comment one out to
# hear the rest.

use_bpm 160

# ------------------------------------------------------------------- stomp
# Four on the floor, because this fight never stops moving. The second half adds
# the offbeat kick and a clank on the backbeat: the two of them in step.
live_loop :gc_stomp do
  bar = tick(:bar) % 16
  catch_half = bar >= 8
  sample :drum_cymbal_open, amp: 0.45, rate: 1.1 if bar == 0 || bar == 8
  16.times do |s|
    sample :bd_haus, amp: 1.5 if s % 4 == 0
    sample :bd_haus, amp: 0.85 if catch_half && [6, 14].include?(s)
    sample :drum_snare_hard, amp: 0.65, rate: 1.05 if s == 4 || s == 12
    sample :drum_cymbal_closed, amp: 0.22, rate: 1.2 if s.odd?
    sample :elec_hi_snare, amp: 0.3, rate: 0.8 if catch_half && [2, 10].include?(s)
    sample :drum_tom_lo_hard, amp: 0.65, rate: 0.85 if bar == 13 && s >= 12
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# :tb303, because the engine of this fight is a machine. Sixteenths, accented off
# the kick, with the octave dropping into the gaps so the line never sits flat.
live_loop :gc_bass, sync: :gc_stomp do
  bar = tick(:bass) % 16
  root = note((ring :c2, :c2, :ab1, :ab1, :eb2, :eb2, :bb1, :bb1,
               :c2, :c2, :ab1, :ab1, :f2, :f2, :g2, :g2)[bar])
  # Semitones off the bar's root; nil is a rest.
  chase = [0, nil, 0, 0, nil, 12, 0, nil, 0, nil, 0, 7, 0, nil, 12, 0]
  caught = [0, 0, nil, 0, 12, nil, 0, 0, 0, nil, 7, 0, 12, 0, nil, 0]
  use_synth :tb303
  (bar >= 8 ? caught : chase).each_with_index do |off, s|
    unless off.nil?
      play root + off, amp: (s % 4 == 0 ? 0.85 : 0.58),
        attack: 0.005, sustain: 0.04, release: 0.14, res: 0.85,
        cutoff: 76 + (bar >= 8 ? 18 : 0) + (s % 4 == 0 ? 14 : 0)
    end
    sleep 0.25
  end
end

# ------------------------------------------------------------------- servo
# COMPUTAH. Sixteenths that wander and never resolve, like something counting. In
# the second half the pattern tightens onto the chord tones and stops wandering:
# he has you. He drops out halfway through bar 8 so the battery can die in peace.
live_loop :gc_servo, sync: :gc_stomp do
  bar = tick(:servo) % 16
  ch = (ring chord(:c4, :minor), chord(:c4, :minor), chord(:ab3, :major), chord(:ab3, :major),
        chord(:eb4, :major), chord(:eb4, :major), chord(:bb3, :major), chord(:bb3, :major),
        chord(:c4, :minor), chord(:c4, :minor), chord(:ab3, :major), chord(:ab3, :major),
        chord(:f4, :minor), chord(:f4, :minor), chord(:g4, :major), chord(:g4, :major))[bar]
  chase = [0, 1, 2, 1, 2, 1, 0, 1]
  caught = [0, 2, 1, 2, 0, 2, 1, 2]
  use_synth :chiplead
  with_fx :reverb, room: 0.4, mix: 0.15 do
    16.times do |i|
      n = ch[(bar >= 8 ? caught : chase)[i % 8]]
      n += 12 if bar >= 8 && i % 8 >= 4
      # Bar 8, second half: his battery is going, so the arp is not.
      play n, amp: (i % 4 == 0 ? 0.4 : 0.25), release: 0.12 unless bar == 7 && i >= 8
      sleep 0.25
    end
  end
end

# -------------------------------------------------------------------- iron
# GREYSON. Open fifths, no third — the same trick Eric's shields use, for the same
# reason: thirds sound like music, fifths sound like weight. First half he is
# throwing junk over the top of the chase, so the stabs land off the beat; second
# half he is holding you still, so they land on it.
# :hoover is the heaviest synth in this file. If the machine struggles, swap it
# for :dsaw — same notes, a fraction of the cost.
live_loop :gc_iron, sync: :gc_stomp do
  bar = tick(:iron) % 16
  root = note((ring :c3, :c3, :ab2, :ab2, :eb3, :eb3, :bb2, :bb2,
               :c3, :c3, :ab2, :ab2, :f2, :f2, :g2, :g2)[bar])
  use_synth :hoover
  with_fx :reverb, room: 0.5, mix: 0.2 do
    8.times do |i|
      on = bar >= 8 ? [0, 2, 3, 4, 6, 7].include?(i) : [1, 3, 5, 7].include?(i)
      if on
        play [root, root + 7], amp: 0.24, attack: 0.008,
          sustain: 0.05, release: 0.2, cutoff: 92
      end
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- hook
# The tune, handed back and forth and then shared. [note, beats]; nil is a rest.
live_loop :gc_hook, sync: :gc_stomp do
  # Bars 1-4 — COMPUTAH ASKS. High, clipped, mechanical.
  call = [
    [:c5, 0.5], [:eb5, 0.5], [:g5, 0.5], [:c6, 0.5], [:bb5, 1], [:g5, 1],   # Cm — the question
    [:ab5, 0.5], [:g5, 0.5], [:f5, 1], [:eb5, 2],                           # Cm — and it drops
    [:ab4, 0.5], [:c5, 0.5], [:eb5, 0.5], [:ab5, 0.5], [:g5, 1], [:eb5, 1], # Ab — asked again
    [:f5, 0.5], [:eb5, 0.5], [:c5, 1], [nil, 2]                             # Ab — room to answer
  ]
  # Bars 5-8 — GREYSON ANSWERS. An octave down, half the notes, no argument.
  answer = [
    [:eb4, 1], [:eb4, 0.5], [:g4, 0.5], [:bb4, 2],                          # Eb — flat
    [:bb4, 0.5], [:ab4, 0.5], [:g4, 1], [:eb4, 2],                          # Eb — flatter
    [:bb3, 1], [:d4, 1], [:f4, 1], [:bb4, 1],                               # Bb — climbing
    [:ab4, 1], [:g4, 1], [nil, 2]                                           # Bb — and the battery goes
  ]
  # Bars 9-16 — BOTH OF THEM, in octaves. The catch.
  locked = [
    [:c5, 0.5], [:c5, 0.5], [:eb5, 0.5], [:f5, 0.5], [:g5, 1], [:f5, 1],    # Cm — locked in
    [:eb5, 0.5], [:f5, 0.5], [:g5, 1], [:c6, 2],                            # Cm — and up
    [:bb5, 0.5], [:ab5, 0.5], [:g5, 1], [:eb5, 1], [:ab5, 1],               # Ab — pressing
    [:g5, 1], [:f5, 1], [:eb5, 2],                                          # Ab — held
    [:f5, 0.5], [:ab5, 0.5], [:c6, 1], [:bb5, 1], [:ab5, 1],                # Fm — the grab
    [:g5, 2], [:f5, 2],                                                     # Fm — dragged over
    [:g5, 0.5], [:b5, 0.5], [:d6, 1], [:c6, 1], [:b5, 1],                   # G  — the wind-up
    [nil, 4]                                                                # G  — five punches
  ]

  with_fx :reverb, room: 0.55, mix: 0.22 do
    use_synth :chiplead
    call.each do |n, dur|
      play n, amp: 0.5, release: dur * 0.75 unless n.nil?
      sleep dur
    end
    use_synth :hoover
    answer.each do |n, dur|
      play n, amp: 0.3, attack: 0.01, sustain: dur * 0.5, release: 0.3, cutoff: 96 unless n.nil?
      sleep dur
    end
    locked.each do |n, dur|
      unless n.nil?
        synth :chiplead, note: n, amp: 0.42, release: dur * 0.75
        synth :hoover, note: note(n) - 12, amp: 0.2, attack: 0.01,
          sustain: dur * 0.45, release: 0.28, cutoff: 98
      end
      sleep dur
    end
  end
end

# ----------------------------------------------------------------- moments
# The two things the fight does at the end of each half, and the only two bars
# where this track stops being a groove and becomes an event.
live_loop :gc_moments, sync: :gc_stomp do
  bar = tick(:moments) % 16
  if bar == 7
    # THE BATTERY GOES FLAT. He could not catch you, so the pitch slides out from
    # under him and he hits the mat. That thud is the punish window.
    sleep 2
    use_synth :pulse
    dying = play :c6, amp: 0.45, attack: 0.01, sustain: 1.1, release: 0.5,
      note_slide: 1.1, cutoff: 105, pulse_width: 0.2
    control dying, note: :c3
    sleep 1.5
    sample :drum_tom_lo_hard, amp: 0.9, rate: 0.7
    sample :elec_blup, amp: 0.5, rate: 0.6
    sleep 0.5
  elsif bar == 15
    # THE FIVE-PUNCH COMBO. Four jabs that deal nothing, a fifth that launches
    # you, and the swoosh is you leaving. Then straight back to bar 1.
    use_synth :dsaw
    4.times do |i|
      sample :elec_hi_snare, amp: 0.8, rate: 1.0 + i * 0.06
      play [:c4, :g4], amp: 0.28, attack: 0.002, release: 0.12, cutoff: 100, detune: 0.2
      sleep 0.5
    end
    sample :drum_heavy_kick, amp: 1.6
    sample :drum_splash_hard, amp: 0.65, rate: 0.9
    play [:c3, :g3, :c4], amp: 0.42, attack: 0.002, release: 1.2, cutoff: 110, detune: 0.25
    sleep 1
    sample :perc_swash, amp: 0.45, rate: 0.7
    sleep 1
  else
    sleep 4
  end
end

# ------------------------------------------------------------------- intro
# Optional cold open: the rig powering up before the first stomp. Uncomment,
# press Run, then comment it out again so the loop stays clean.
#
# use_synth :pulse
# booting = play :c3, amp: 0.4, attack: 0.01, sustain: 1.2, release: 0.4,
#   note_slide: 1.2, cutoff: 100, pulse_width: 0.25
# control booting, note: :c5
# sleep 1.5
# sample :elec_ping, amp: 0.5
# sleep 0.5
