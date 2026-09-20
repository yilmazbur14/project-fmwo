# JOSH — "Three Card Trick", draft 2 (the intense version)
#
# ----------------------------------------------------------------------------
# THIS FILE IS DRAFT 2 WITH ONE BUG FIXED AND NOTHING ELSE CHANGED.
#
# Draft 2 has one loop, :josh_table, that owns the bar counter via tick(:bar),
# and five loops that read it back with look(:bar). That read does not work.
# Sonic Pi's tick counters are live_loop-local and are not inherited: core.rb's
# ThreadLocalCounter stores them with __thread_locals.set_local, and look on a
# key THIS loop has never ticked returns (val || 0) — 0, forever. It is not a
# race; it is deterministic. So in the shipped recording:
#
#   josh_shuffle  played the `deal` voicing for all sixteen bars, never `switch`
#   josh_deck     played the `deal` pattern for all sixteen bars, and never
#                 rested, so the fan had no room even if it had fired
#   josh_hook     `big` was never true: it played the 4-bar DEAL phrase four
#                 times over, and THE ENTIRE SWITCH — six bars of melody, the
#                 reveal, the climb — has never been heard
#   josh_flourish [3,7,11].include?(0) is false, so it never fired once
#   josh_fan      neither bar 14 nor bar 15 ever arrived: no run up the deck,
#                 no twelve cards, no landing
#
# The fix is mechanical. josh_shuffle and josh_deck already tick their own key
# to walk a chord ring, and that tick counts bars, so the bar is read from it
# and the ring indexed with it. josh_flourish and josh_fan get counters of their
# own. josh_hook's iterations are phrases rather than single bars, so it walks a
# ring of its own phrase starts.
#
# NOT ONE NOTE, TEMPO, KEY, SYNTH OR OPT IS CHANGED. Everything you hear that
# you have not heard before was already written below; it just never ran.
# ----------------------------------------------------------------------------# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 had the right idea and not enough weight: a clean pluck arpeggio and
# a light hand on the drums. Pretty, but you could have put it under a menu.
# Draft 2 keeps every structural idea — the riffled deck, the syncopated bass,
# the hook that keeps climbing, the flourish every fourth bar — and gives them
# teeth: 168 bpm, a distorted saw bass doubling the low end, a hard kit, and a
# lead that plays in octaves instead of politely on its own.
#
# Reference: the energy of N's theme from Pokemon Black and White for the
# clockwork arpeggios and the climbing hook, and MEGALOVANIA for what this
# draft was missing — a low end that never stops moving and accents that land
# where you are not braced for them. Written in that spirit, never copied: every
# note here is ours, so it can ship in a public repo.
#
# Josh is a card thrower: sleight of hand, misdirection, a smirk. So the
# arpeggios run like a shuffled deck, the lead keeps sidestepping the beat, and
# the last two bars are the fan — the whole deck thrown at once.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run twice through the 16 bars,
# hit Rec again to save a WAV.
#
# 168 bpm, A minor. 16-bar cycle:
#   Bars 1-8    THE DEAL   — Am F C G, the hook over the shuffle
#   Bars 9-14   THE SWITCH — Am F Dm E, same hook a third higher, and the
#                            harmony turns under it: the trick is revealed
#   Bars 15-16  THE FAN    — the run up the deck, then every card at once
# Every voice is a live_loop synced to the shuffle, so you can comment one out.

use_bpm 168

# ------------------------------------------------------------ the shuffle
# Sixteenth-note arpeggios, like a deck being riffled. This is the engine, and
# in the switch it climbs an octave every second beat instead of staying put.
live_loop :josh_shuffle do
  bar = tick(:sh) % 16
  ch = (ring chord(:a4, :minor), chord(:f4, :major), chord(:c5, :major), chord(:g4, :major),
        chord(:a4, :minor), chord(:f4, :major), chord(:d4, :minor), chord(:e4, :major))[bar]
  deal = [0, 1, 2, 1, 2, 1, 0, 2]
  switch = [0, 2, 1, 2, 0, 1, 2, 1]
  use_synth :pluck
  with_fx :reverb, room: 0.5, mix: 0.18 do
    16.times do |i|
      n = ch[(bar >= 8 ? switch : deal)[i % 8]]
      n += 12 if bar >= 8 ? i % 4 >= 2 : i % 8 >= 6
      play n, amp: (i % 4 == 0 ? 0.55 : 0.34), coef: 0.4
      sleep 0.25
    end
  end
end

# --------------------------------------------------------------- the deck
# The low end draft 1 did not have. A distorted saw under the bass, running
# sixteenths with the octave snapping up into the gaps, so the floor is always
# moving even when the hook is resting.
live_loop :josh_deck, sync: :josh_shuffle do
  bar = tick(:deck) % 16
  root = note((ring :a1, :f1, :c2, :g1, :a1, :f1, :d1, :e1,
               :a1, :f1, :c2, :g1, :a1, :f1, :d1, :e1)[bar])
  # Semitones off the bar root; nil is a rest.
  deal   = [0, nil, 0, 12, 0, nil, 0, 7, 0, nil, 0, 12, 0, 7, 0, nil]
  switch = [0, 0, 12, 0, 7, 0, 12, 0, 0, 0, 12, 7, 0, 12, 7, 0]
  use_synth :tb303
  with_fx :distortion, distort: 0.35, mix: 0.45 do
    if bar >= 14
      sleep 4
    else
      (bar >= 8 ? switch : deal).each_with_index do |off, s|
        unless off.nil?
          play root + off, amp: (s % 4 == 0 ? 0.85 : 0.55),
            attack: 0.004, sustain: 0.04, release: 0.12, res: 0.8,
            cutoff: 74 + (bar >= 8 ? 20 : 0) + (s % 4 == 0 ? 14 : 0)
        end
        sleep 0.25
      end
    end
  end
end

# --------------------------------------------------------------- the bass
# Kept from draft 1, because the syncopation is the misdirection: it never
# lands on the beat you brace for. It sits on top of the deck now.
live_loop :josh_bass, sync: :josh_shuffle do
  root = (ring :a2, :f2, :c3, :g2, :a2, :f2, :d2, :e2).tick(:bass)
  use_synth :fm
  with_fx :lpf, cutoff: 92 do
    [0.75, 0.25, 0.5, 0.75, 0.5, 0.25, 1.0].each do |dur|
      play root, amp: 0.7, attack: 0.005, release: dur * 0.8, divisor: 1.2, depth: 1.5
      sleep dur
    end
  end
end

# -------------------------------------------------------------- the table
# Draft 1 tapped a rim. This one hits the table: four on the floor under the
# deal, offbeat kicks in the switch, and a snap where every card lands.
live_loop :josh_table, sync: :josh_shuffle do
  bar = tick(:bar) % 16
  switch = bar >= 8
  sample :drum_cymbal_open, amp: 0.45, rate: 1.15 if bar == 0 || bar == 8
  if bar >= 14
    sleep 4
  else
    16.times do |s|
      sample :bd_haus, amp: 1.45 if s % 4 == 0
      sample :bd_haus, amp: 0.8 if switch && [6, 14].include?(s)
      sample :drum_snare_hard, amp: 0.62, rate: 1.1 if s == 4 || s == 12
      sample :perc_snap, amp: 0.5, rate: 0.95 if s == 8
      sample :perc_snap, amp: 0.3, rate: 1.35 if switch && [3, 11].include?(s)
      sample :drum_cymbal_closed, amp: 0.2, rate: 1.2 if s.odd?
      sample :drum_tom_hi_hard, amp: 0.55, rate: 1.1 if bar == 13 && s >= 12
      sleep 0.25
    end
  end
end

# -------------------------------------------------------------------- hook
# The tune. It climbs, hesitates, then climbs further, never resolving where you
# expect. Doubled an octave down on a saw from the switch, which is the moment
# he stops performing and starts winning. [note, beats]; nil is a rest.
live_loop :josh_hook, sync: :josh_shuffle do
  deal = [
    [:a4, 0.5], [:c5, 0.5], [:e5, 0.75], [:d5, 0.25], [:c5, 1], [:b4, 1],      # Am
    [:c5, 0.5], [:f5, 0.5], [:e5, 1], [:c5, 1], [:b4, 0.5], [:c5, 0.5],        # F
    [:g4, 0.5], [:c5, 0.5], [:g5, 0.75], [:f5, 0.25], [:e5, 1], [:d5, 1],      # C
    [:b4, 1], [:d5, 1], [:g5, 1], [:b5, 1]                                     # G
  ]
  switch = [
    [:a5, 0.5], [:g5, 0.5], [:e5, 0.75], [:d5, 0.25], [:c5, 1], [:e5, 1],      # Am
    [:f5, 0.5], [:a5, 0.5], [:g5, 1], [:f5, 1], [:e5, 0.5], [:f5, 0.5],        # F
    [:d5, 0.5], [:f5, 0.5], [:a5, 0.75], [:g5, 0.25], [:f5, 1], [:e5, 1],      # Dm
    [:e5, 1], [:gs5, 1], [:a5, 1], [:c6, 1],                                   # E  — the reveal
    [:d6, 0.5], [:c6, 0.5], [:b5, 1], [:a5, 1], [:gs5, 1],                     # E  — pressing
    [:a5, 2], [:e5, 2]                                                         # E  — into the fan
  ]
  # Draft 2 read the drum loop's :bar counter here, which is pinned to 0 for
  # the reason given in the header. This loop's iterations are phrases, not
  # bars — deal (bars 1-4), deal (5-8), switch (9-14), rest (15-16) — so it
  # counts its own phrase starts. Every branch below then reads
  # exactly as it always did, and the with_fx block is entered once per phrase
  # as before.
  bar = (ring 0, 4, 8, 14).tick(:hook)
  if bar >= 14
    sleep 8
  else
    big = bar >= 8
    use_synth :blade
    with_fx :reverb, room: 0.55, mix: 0.22 do
      (big ? switch : deal).each do |n, dur|
        unless n.nil?
          play n, amp: 0.62, attack: 0.01, sustain: dur * 0.5, release: 0.25,
            cutoff: 110, vibrato_rate: 5
          if big
            synth :dsaw, note: note(n) - 12, amp: 0.26, attack: 0.01,
              sustain: dur * 0.45, release: 0.25, cutoff: 100, detune: 0.16
          end
        end
        sleep dur
      end
    end
  end
end

# ----------------------------------------------------------- the flourish
# Every fourth bar of the deal, a fast run up the deck. Pure show-off, and the
# only thing in draft 1 that already had the right energy.
live_loop :josh_flourish, sync: :josh_shuffle do
  bar = tick(:flourish) % 16
  if [3, 7, 11].include?(bar)
    use_synth :pluck
    deck_run = scale(:a4, :minor_pentatonic, num_octaves: 2).to_a.take(8)
    sleep 4 - deck_run.length * 0.125
    deck_run.each_with_index do |n, i|
      play n, amp: 0.45 - i * 0.02, coef: 0.55
      sleep 0.125
    end
  else
    sleep 4
  end
end

# --------------------------------------------------------------- the fan
# BARS 15-16. The deck goes up and every card comes down at once.
#
# The table and the deck are written to drop out here, so the run has room:
# two octaves up the scale in thirty-seconds, a held breath, and then twelve
# cards landing in a bar — accelerating, because he is not dealing any more.
live_loop :josh_fan, sync: :josh_shuffle do
  bar = tick(:fan) % 16
  if bar == 14
    use_synth :pluck
    sample :perc_swash, amp: 0.5, rate: 1.2
    deck_run = scale(:a4, :minor, num_octaves: 2).to_a
    deck_run.each do |n|
      play n, amp: 0.5, coef: 0.5
      sleep 0.125
    end
    sample :drum_cymbal_open, amp: 0.4, rate: 1.3
    sleep 4 - deck_run.length * 0.125
  elsif bar == 15
    use_synth :dsaw
    with_fx :distortion, distort: 0.4, mix: 0.5 do
      gaps = [0.3, 0.28, 0.26, 0.24, 0.22, 0.2, 0.18, 0.16, 0.14, 0.12, 0.1, 0.1]
      cards = [:a4, :c5, :e5, :a5, :g5, :e5, :c5, :a4, :e4, :c5, :e5, :a5]
      gaps.each_with_index do |gap, i|
        sample :perc_snap, amp: 0.4 + i * 0.03, rate: 1.0 + i * 0.05
        play cards[i], amp: 0.3 + i * 0.02, attack: 0.002, release: 0.1,
          cutoff: 100, detune: 0.2
        sleep gap
      end
      sample :drum_heavy_kick, amp: 1.6
      sample :drum_splash_hard, amp: 0.6, rate: 1.0
      play [:a2, :e3, :a3], amp: 0.5, attack: 0.002, release: 1.4,
        cutoff: 112, detune: 0.25
      sleep 4 - gaps.sum
    end
  else
    sleep 4
  end
end
