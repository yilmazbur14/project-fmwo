# CAPTAIN BURAK — "Main Character Energy"
# Original music for Project FMWO, written for Sonic Pi 4.x / 5.x.
#
# Boss 1, the tutorial: a pirate captain who is sure this is his story. A
# stomping shanty in 6/8 on a squeezebox, crossed with a boss kit, and the
# whole thing is a strut. He struts the hook twice, lets the horns announce
# him as the hero, reaches for one note too high, falls flat on it, and laughs
# it off. It is the first fight in the game, so it is a party, not a threat.
#
# 120 dotted-quarter beats a minute. Every live_loop iteration is one bar of
# 12/8 (two bars of 6/8): four beats, twelve eighths of a third of a beat each.
# E Dorian for the hook, G major for the horns, B7 to turn round. 16-bar cycle:
#   Bars 1-4    THE HOOK      — Em A Em D-B7. On the squeezebox: a strut up the
#                               chord and a tumble back down, three times, then
#                               a cocky run and his laugh ("HA. HA. HA-ha").
#   Bars 5-8    AGAIN, LOUDER — the same, with horns under it; the last strut
#                               climbs instead of tumbling, and the laugh lands
#                               on a big "HA!" and a powder keg.
#   Bars 9-12   THE HERO      — G D Em C | G Em C D. The horns take a fanfare
#                               of their own: he is the main character now.
#   Bars 13-14  THE PRATFALL  — everyone climbs to a high G, which sags flat,
#                               a keg goes off, and he chuckles.
#   Bars 15-16  THE LAUGH     — the whole band laughs along in hits, then the
#                               squeezebox swirls round B7 into bar 1's E.
#
# HOW TO RECORD: never through the GUI. See music-recording-pipeline:
#   python record_theme.py burak_theme.rb 120 --out <scratch>/burak_theme_raw.wav
#   python measure_take.py <scratch>/burak_theme_raw.wav 120
#   python cut_loop.py <scratch>/burak_theme_raw.wav 120 --out <scratch>/burak_theme.wav
# One cycle is 16 bars x 4 beats / 120 bpm = 32.0 s.

use_bpm 120

# ------------------------------------------------------------------ harmony
# One bar per row: [bass on each of the four beats, squeezebox left-hand chord
# for the first half, and for the second]. nil means that hand rests: the climb
# and the swirl are single lines over the kit, so nothing sits under their
# passing notes.
define :burak_harmony do
  [
    [[:e2, :b1, :e2, :g2],   [:e3, :g3, :b3],   [:e3, :g3, :b3]],    # 1  Em Em
    [[:a1, :e2, :a1, :cs2],  [:e3, :a3, :cs4],  [:e3, :a3, :cs4]],   # 2  A  A
    [[:e2, :b1, :e2, :g2],   [:e3, :g3, :b3],   [:e3, :g3, :b3]],    # 3  Em Em
    [[:d2, :a1, :b1, :ds2],  [:d3, :fs3, :a3],  [:ds3, :fs3, :a3]],  # 4  D  B7
    [[:e2, :b1, :e2, :g2],   [:e3, :g3, :b3],   [:e3, :g3, :b3]],    # 5  Em Em
    [[:a1, :e2, :a1, :cs2],  [:e3, :a3, :cs4],  [:e3, :a3, :cs4]],   # 6  A  A
    [[:e2, :b1, :e2, :d2],   [:e3, :g3, :b3],   [:e3, :g3, :b3]],    # 7  Em Em
    [[:b1, :fs2, :e2, :b1],  [:ds3, :fs3, :a3], [:e3, :g3, :b3]],    # 8  B7 Em
    [[:g1, :d2, :d2, :a1],   [:d3, :g3, :b3],   [:d3, :fs3, :a3]],   # 9  G  D
    [[:e2, :b1, :c2, :g1],   [:e3, :g3, :b3],   [:e3, :g3, :c4]],    # 10 Em C
    [[:g1, :d2, :e2, :b1],   [:d3, :g3, :b3],   [:e3, :g3, :b3]],    # 11 G  Em
    [[:c2, :g1, :d2, :a1],   [:e3, :g3, :c4],   [:d3, :fs3, :a3]],   # 12 C  D
    [[:c2, :e2, :d2, :a1],   nil,               nil],                # 13 C  D  the climb
    [[:b1, :b1, :b1, :b1],   nil,               [:ds3, :fs3, :a3]],  # 14 B7    the pratfall
    [[:a1, :a1, :b1, :b1],   [:e3, :a3, :c4],   [:ds3, :fs3, :a3]],  # 15 Am B7 the laugh
    [[:b1, :fs2, :b1, :ds2], nil,               nil]                 # 16 B7    the swirl
  ]
end

# --------------------------------------------------------------------- tune
# [note, eighths]; every bar sums to 12. nil is a rest. A pickup sits at the end
# of the bar before its downbeat, so bar 16's last D# belongs to bar 1's E.
# The HOOK's cell is a strut (long-short, long-short, up the chord) and a
# tumble (four notes down to a held one). The LAUGH is chord notes with a rest
# after each: HA. HA. HA.
define :burak_tune do
  [
    # ---- THE HOOK
    [[:e5, 2], [:g5, 1], [:b5, 2], [:a5, 1], [:g5, 1], [:fs5, 1], [:e5, 1], [:d5, 3]],        # 1
    [[:e5, 2], [:a5, 1], [:cs6, 2], [:b5, 1], [:a5, 1], [:g5, 1], [:fs5, 1], [:e5, 3]],       # 2
    [[:e5, 2], [:g5, 1], [:b5, 2], [:a5, 1], [:g5, 1], [:fs5, 1], [:e5, 1], [:b5, 3]],        # 3
    [[:a5, 1], [:b5, 1], [:a5, 1], [:fs5, 2], [:d5, 1],
     [:b5, 1], [nil, 1], [:a5, 1], [nil, 1], [:fs5, 1], [:ds5, 1]],                           # 4
    # ---- AGAIN, LOUDER
    [[:e5, 2], [:g5, 1], [:b5, 2], [:a5, 1], [:g5, 1], [:fs5, 1], [:e5, 1], [:d5, 3]],        # 5
    [[:e5, 2], [:a5, 1], [:cs6, 2], [:b5, 1], [:a5, 1], [:g5, 1], [:fs5, 1], [:e5, 3]],       # 6
    [[:e5, 2], [:g5, 1], [:b5, 2], [:a5, 1], [:g5, 1], [:a5, 1], [:b5, 1], [:d6, 3]],         # 7
    [[:b5, 1], [:a5, 1], [:fs5, 1], [:a5, 1], [:fs5, 1], [:ds5, 1], [:e5, 3], [nil, 3]],      # 8
    # ---- THE HERO (on the horns)
    [[:d5, 3], [:g5, 2], [:a5, 1], [:a5, 3], [:fs5, 2], [:d5, 1]],                            # 9
    [[:g5, 2], [:e5, 1], [:b4, 2], [:e5, 1], [:g5, 3], [:e5, 3]],                             # 10
    [[:d5, 3], [:g5, 2], [:a5, 1], [:b5, 3], [:g5, 2], [:e5, 1]],                             # 11
    [[:e5, 2], [:g5, 1], [:c6, 3], [:b5, 1], [:a5, 1], [:g5, 1], [:fs5, 3]],                  # 12
    # ---- THE PRATFALL
    [[:g5, 1], [:a5, 1], [:b5, 1], [:c6, 1], [:d6, 1], [:e6, 1], [:fs6, 1], [:g6, 5]],        # 13
    [[:g6, 3], [nil, 3], [:b5, 1], [nil, 1], [:a5, 1], [nil, 1], [:fs5, 1], [nil, 1]],        # 14
    # ---- THE LAUGH, and round again
    [[:a5, 1], [nil, 1], [:e5, 1], [nil, 1], [:c5, 1], [nil, 1],
     [:b5, 1], [nil, 1], [:fs5, 1], [nil, 1], [:ds5, 1], [nil, 1]],                           # 15
    [[:b4, 1], [:ds5, 1], [:fs5, 1], [:b5, 1], [:a5, 1], [:fs5, 1],
     [:b5, 1], [:a5, 1], [:fs5, 1], [:a5, 1], [:fs5, 1], [:ds5, 1]]                           # 16
  ]
end

# Bar-length check, in whole eighths so it is exact. Prints nothing when right.
burak_tune.each_with_index do |phrase, i|
  total = phrase.inject(0) { |t, (_, n)| t + n }
  puts "burak_theme: BAR #{i + 1} is #{total} eighths, not 12" unless total == 12
end

# ------------------------------------------------------------- squeezebox
# Two pulse waves a few cents apart, the beating of a musette-tuned accordion,
# with a reed an octave below for the body.
define :burak_squeeze do |n, eighths, amp|
  len = eighths / 3.0
  synth :dpulse, note: n, amp: amp, attack: 0.02, sustain: len * 0.7,
    release: 0.08, detune: 0.12, pulse_width: 0.4, dpulse_width: 0.3, cutoff: 102
  synth :dpulse, note: note(n) - 12, amp: amp * 0.4, attack: 0.03,
    sustain: len * 0.7, release: 0.08, detune: 0.09, pulse_width: 0.35, cutoff: 92
end

# ------------------------------------------------------------------- horns
# A saw through the tb303's own filter envelope for the "bwah", warmer and
# lower than a pop brass section, with a detuned saw under it.
define :burak_horn do |notes, beats, amp|
  notes.each_with_index do |n, i|
    pan = (i - (notes.size - 1) / 2.0) * 0.16
    synth :tb303, note: n, amp: amp, attack: 0.04, sustain: beats * 0.6,
      release: 0.2 + beats * 0.1, wave: 0, res: 0.1, cutoff_min: 58,
      cutoff: 100, cutoff_attack: 0.08, cutoff_decay: 0.3,
      cutoff_sustain_level: 0.45, pan: pan
    synth :dsaw, note: n, amp: amp * 0.4, attack: 0.05, sustain: beats * 0.55,
      release: 0.25, cutoff: 90, detune: 0.1, pan: -pan
  end
end

# -------------------------------------------------------------------- clock
# Plays nothing, on purpose: every voice syncs to this and joins on the same
# cue, so they all count the same bars. With the drums as the clock, every
# synced voice would join a bar late and count one bar behind the kit.
live_loop :burak_clock do
  sleep 4
end

# ------------------------------------------------------------------- drums
# Boots on the deck. The hook stomps on 1 and 3 with a crew clap on 2 and 4 and
# a shaker on every eighth. The hero section stomps on every beat. The climb
# rolls, the pratfall crashes and stops, the laugh hits with the band, and bar
# 16 fills into the crash on bar 1.
live_loop :burak_drums, sync: :burak_clock do
  bar = tick(:drums) % 16
  hero = bar >= 8 && bar < 12
  sample :drum_cymbal_hard, amp: 0.55, rate: 0.95 if bar == 0 || bar == 8
  sample :drum_cymbal_hard, amp: 0.4, rate: 1.05 if bar == 4 || bar == 10
  12.times do |e|
    beat = e % 3 == 0
    if bar == 12
      sample :bd_fat, amp: 1.5 if beat
      sample :drum_snare_soft, amp: 0.3 + e * 0.06
    elsif bar == 13
      sample :drum_cymbal_hard, amp: 0.6, rate: 0.9 if e == 0
      sample :bd_fat, amp: 1.5 if e == 0
      if e >= 6
        sample :bd_fat, amp: 1.1 if beat
        synth :sc808_maracas, amp: 0.3 if beat
      end
    elsif bar == 14
      if e.even?
        sample :bd_fat, amp: 1.5
        sample :drum_snare_hard, amp: 0.7
        synth :sc808_clap, amp: 0.7
      end
    else
      stomp = hero ? beat : (e == 0 || e == 6)
      sample :bd_fat, amp: 1.6 if stomp
      sample :drum_bass_soft, amp: 0.9 if stomp
      sample :bd_fat, amp: 0.85 if !hero && e == 11 && bar != 15
      if e == 3 || e == 9
        synth :sc808_clap, amp: 0.8
        sample :drum_snare_soft, amp: (hero ? 0.9 : 0.7)
      end
      synth :sc808_maracas, amp: (beat ? 0.45 : 0.28), pan: 0.25
      sample :drum_cymbal_closed, amp: 0.2, rate: 1.2, pan: -0.2 if hero && !beat
      if bar == 7 && e == 6
        # "HA!"
        sample :drum_cymbal_hard, amp: 0.6, rate: 0.9
      end
      if bar == 11 && e >= 9
        tom = [:drum_tom_mid_hard, :drum_tom_lo_hard, :drum_tom_lo_hard][e - 9]
        sample tom, amp: 0.7 + (e - 9) * 0.12
      end
      if bar == 15 && e >= 6
        tom = [:drum_tom_hi_hard, :drum_tom_hi_hard, :drum_tom_mid_hard,
               :drum_tom_mid_hard, :drum_tom_lo_hard, :drum_snare_hard][e - 6]
        sample tom, amp: 0.6 + (e - 6) * 0.08
      end
    end
    sleep 1.0 / 3
  end
end

# ------------------------------------------------------------------- kegs
# Powder kegs going off: the "HA!" at the end of the second hook, the horns'
# entrance, the middle of the hero section, and the pratfall.
live_loop :burak_kegs, sync: :burak_clock do
  bar = tick(:kegs) % 16
  at = {7 => 6, 8 => 0, 10 => 0, 13 => 3}[bar]
  if at
    sleep at / 3.0
    sample :bd_boom, amp: 1.2, rate: 0.6
    sample :drum_splash_hard, amp: 0.45, rate: 0.55
    blast = synth :bnoise, amp: 0.3, attack: 0.005, sustain: 0.1, release: 0.9,
      cutoff: 110, cutoff_slide: 0.8
    control blast, cutoff: 60
    sleep (12 - at) / 3.0
  else
    sleep 4
  end
end

# -------------------------------------------------------------------- bass
# One note on each dotted-quarter beat, the stomping bass of a shanty. In the
# laugh it hits with the band instead.
# Not called `line`: that is a built-in, and Sonic Pi's pre-parser rejects the
# whole buffer when a built-in is used as a variable, so the take comes out
# silent without an error anywhere but its own log.
live_loop :burak_bass, sync: :burak_clock do
  bar = tick(:bass) % 16
  steps = burak_harmony[bar][0]
  use_synth :tb303
  if bar == 14
    [0, 2, 4, 6, 8, 10].each_with_index do |e, i|
      play steps[i < 3 ? 0 : 2], amp: 1.15, attack: 0.005, sustain: 0.12, release: 0.15,
        res: 0.2, cutoff_min: 45, cutoff: 85, cutoff_sustain_level: 0.4, wave: 0
      sleep 2 / 3.0
    end
  elsif bar == 13
    play steps[0], amp: 1.1, attack: 0.005, sustain: 0.5, release: 1.2, res: 0.2,
      cutoff_min: 40, cutoff: 78, cutoff_sustain_level: 0.3, wave: 0
    sleep 2
    [2, 3].each do |b|
      play steps[b], amp: 0.75, attack: 0.005, sustain: 0.15, release: 0.2, res: 0.2,
        cutoff_min: 45, cutoff: 80, cutoff_sustain_level: 0.3, wave: 0
      sleep 1
    end
  else
    steps.each do |n|
      play n, amp: 1.15, attack: 0.005, sustain: 0.3, release: 0.35, res: 0.2,
        cutoff_min: 45, cutoff: 85, cutoff_decay: 0.2, cutoff_sustain_level: 0.35, wave: 0
      sleep 1
    end
  end
end

# -------------------------------------------------------------------- vamp
# The squeezebox's left hand: a short chord on the last eighth of each group of
# three, "boom . chk boom . chk" against the bass. In the laugh it hits on the
# laugh's own eighths instead.
live_loop :burak_vamp, sync: :burak_clock do
  bar = tick(:vamp) % 16
  row = burak_harmony[bar]
  12.times do |e|
    ch = e < 6 ? row[1] : row[2]
    hit = bar == 14 ? e.even? : (bar == 13 ? (e >= 6 && e.even?) : e % 3 == 2)
    if ch && hit
      ch.each_with_index do |n, i|
        synth :dpulse, note: n, amp: 0.36, attack: 0.01, sustain: 0.1, release: 0.1,
          detune: 0.08, pulse_width: 0.35, cutoff: 90, pan: -0.3 + i * 0.1
      end
    end
    sleep 1.0 / 3
  end
end

# ------------------------------------------------------------------- horns
# Silent under the first hook. Under the second, long guide notes that move a
# step at a time. The hero section is theirs: the fanfare, doubled an octave
# down. They climb with the squeezebox, sag with it, laugh with the band, and
# swell on B7 into the top.
live_loop :burak_horns, sync: :burak_clock do
  bar = tick(:horns) % 16
  if bar < 4
    sleep 4
  elsif bar < 8
    guide = [[:e4, :b3], [:e4, :cs4], [:e4, :b3], [:ds4, :b3]][bar - 4]
    with_fx :reverb, room: 0.6, mix: 0.25 do
      burak_horn [guide[0]], 1.8, 0.26
      sleep 2
      burak_horn [guide[1]], 1.8, 0.26
      sleep 2
    end
  elsif bar < 12
    with_fx :reverb, room: 0.6, mix: 0.25 do
      burak_tune[bar].each do |n, eighths|
        burak_horn [n, note(n) - 12], eighths / 3.0, 0.5 unless n.nil?
        sleep eighths / 3.0
      end
    end
  elsif bar == 12
    burak_tune[bar].each do |n, eighths|
      burak_horn [note(n) - 12], eighths / 3.0, 0.34
      sleep eighths / 3.0
    end
  elsif bar == 13
    sag = synth :tb303, note: :g5, amp: 0.34, attack: 0.02, sustain: 0.8, release: 0.3,
      wave: 0, res: 0.1, cutoff_min: 58, cutoff: 96, note_slide: 1
    control sag, note: :ds5
    sleep 4
  elsif bar == 14
    [[:a3, :c4, :e4], [:b3, :ds4, :fs4]].each do |ch|
      3.times do
        burak_horn ch, 0.2, 0.3
        sleep 2 / 3.0
      end
    end
  else
    # A crescendo that is cut off by bar 1's downbeat rather than dying before it.
    [:b2, :fs3, :a3, :ds4].each do |n|
      synth :tb303, note: n, amp: 0.26, attack: 3.0, sustain: 0.7, release: 0.2,
        wave: 0, res: 0.1, cutoff_min: 58, cutoff: 96
      synth :dsaw, note: n, amp: 0.1, attack: 3.0, sustain: 0.7, release: 0.2,
        cutoff: 88, detune: 0.1
    end
    sleep 4
  end
end

# ------------------------------------------------------------------- squeeze
# The lead. The hook, the climb and the swirl are the squeezebox's; in the hero
# section it drops to its own left hand and lets the horns sing. At the top of
# the climb the high G sags a major third, the way a squeezebox does when the
# bellows run out.
live_loop :burak_squeezebox, sync: :burak_clock do
  bar = tick(:squeezebox) % 16
  phrase = burak_tune[bar]
  if bar >= 8 && bar < 12
    sleep 4
  else
    loud = bar >= 4 && bar < 8 ? 1.1 : 1.0
    with_fx :reverb, room: 0.4, mix: 0.18 do
      phrase.each_with_index do |(n, eighths), i|
        if n && bar == 13 && i == 0
          top = synth :dpulse, note: n, amp: 0.44, attack: 0.01, sustain: 0.9,
            release: 0.2, detune: 0.12, pulse_width: 0.4, dpulse_width: 0.3,
            cutoff: 102, note_slide: 1
          control top, note: :ds6
        elsif n
          burak_squeeze n, eighths, 0.44 * loud
        end
        sleep eighths / 3.0
      end
    end
  end
end
