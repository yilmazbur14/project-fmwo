# LIAM & BIXBY — "Carried In, Swallowed Whole", draft 2 (the intense version)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 had the best idea in the set and the least force behind it. The idea
# stays exactly as it was: ONE TUNE PLAYED TWICE. The court states it — bright,
# dotted, pleased with itself, with a harpsichord that never shuts up. Then the
# beast plays the SAME tune, note for note, except every note that reached for
# the fifth, the second or the leading note now falls a half step short, and the
# whole line drops two octaves onto a distorted saw. That is the joke in the
# code too: `beast` is literally built by mapping over `court`, so you can hear
# what it used to be.
#
# What changes in draft 2 is everything underneath. 96 bpm made the court
# stately and the beast slow, and a slow dragon is not frightening. At 144 the
# court is a processional you have to keep up with, and the beast is the thing
# the processional was always afraid of: sixteenths on a distorted bass, a kit
# that limps in threes and hits like a building, wingbeats you feel, and a roar
# in the last two bars.
#
# Reference, for intensity: ASGORE, for a theme that gets enormous by stacking
# rather than by speeding up, and MEGALOVANIA, for a bass that never rests for
# a single sixteenth. Written in that spirit, never copied from anything: every
# note here is ours, so it can ship in a public repo.
#
# Liam is carried in on a throne, tells you Bixby will make quick work of you,
# and keeps slapping Bixby until Bixby swallows him whole.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. Any voice can be commented out to hear the rest.
#
# 144 bpm, G. 16-bar cycle:
#   Bars 1-8    THE COURT — G minor with its proper leading note: Gm D Cm Gm
#                           Eb D Gm D, a processional you could carry a chair to
#   Bars 9-14   THE BEAST — the same G with the fifth, the second and the
#                           leading note all bent flat (G Ab Bb C Db Eb F).
#                           Chords go G dim / Db / Ab; the gait limps 3+3+2.
#   Bars 15-16  THE ROAR  — he pulls up, and everything lands at once. This is
#                           roughly where his recovery window opens.
# Written to the fight: the court half is the throne entrance and the slapping,
# the beast half is hover, fire breath and the landing.

use_bpm 144

# THE BEND, which is the whole piece: three pitch classes fall a half step once
# Bixby swallows him — D (the fifth), A (the second) and F# (the leading note).
# Everything else is untouched, which is why the beast is recognisably the same
# tune and completely wrong. It is written out inside the loop that uses it, so
# re-running the buffer never complains about redefining anything.
#
# ------------------------------------------------------------------- drums
# Court: a kick on 1 and 3 with the dotted snap that courts have always used to
# sound expensive. Beast: nothing lands square any more — the kick limps three,
# three, two, and the toms come down on the last of it.
live_loop :liam_drums do
  bar = tick(:bar) % 16
  beast = bar >= 8
  roar = bar >= 14
  sample :drum_cymbal_open, amp: 0.35, rate: 0.9 if bar == 0
  sample :drum_splash_hard, amp: 0.95, rate: 0.45 if bar == 8   # the swallow
  16.times do |s|
    if roar
      sample :bd_boom, amp: 1.9, rate: 0.45 if s % 8 == 0
      sample :drum_tom_lo_hard, amp: 0.8, rate: 0.6 if bar == 15 && s % 2 == 0
    elsif beast
      sample :bd_boom, amp: 1.95, rate: 0.5 if [0, 6, 12].include?(s)
      sample :bd_boom, amp: 0.9, rate: 0.6 if [3, 9].include?(s)
      sample :drum_snare_hard, amp: 0.62, rate: 0.8 if s == 4 || s == 12
      sample :drum_cymbal_closed, amp: 0.22, rate: 0.7 if s.odd?
      sample :drum_tom_lo_hard, amp: 0.7, rate: 0.65 if bar == 13 && s >= 12
    else
      sample :bd_boom, amp: 1.6, rate: 0.7 if s == 0 || s == 8
      sample :drum_snare_soft, amp: 0.55, rate: 1.0 if s == 4 || s == 12
      sample :drum_snare_soft, amp: 0.22, rate: 1.3 if [3, 11].include?(s)
      sample :drum_cymbal_closed, amp: 0.2, rate: 1.1 if s % 2 == 0
      sample :drum_tom_mid_hard, amp: 0.5, rate: 0.95 if bar == 7 && s >= 12
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# Court: a walking bass with the dotted push, polite and certain. Beast: the
# floor. Sixteenths, distorted, with the bent fifth shoving against the root.
live_loop :liam_bass, sync: :liam_drums do
  step = tick(:bass)
  court_root = (ring :g2, :d2, :c2, :g2, :eb2, :d2, :g2, :d2)[step]
  bar = look(:bar) % 16
  if bar >= 8
    root = note((ring :g1, :g1, :db2, :db2, :ab1, :ab1, :g1, :g1)[step])
    use_synth :tb303
    with_fx :distortion, distort: 0.45, mix: 0.55 do
      [0, 0, 12, 0, 6, 0, 12, 0, 0, 0, 12, 6, 0, 11, 10, 0].each_with_index do |off, s|
        play root + off, amp: (s % 4 == 0 ? 0.92 : 0.6),
          attack: 0.004, sustain: 0.05, release: 0.13, res: 0.88,
          cutoff: 82 + (s % 4 == 0 ? 18 : 0)
        sleep 0.25
      end
    end
  else
    use_synth :tri
    with_fx :lpf, cutoff: 88 do
      [[0, 1.5], [7, 0.5], [12, 1], [7, 1]].each do |off, dur|
        play note(court_root) + off, amp: 0.8, attack: 0.01, release: dur * 0.85
        sleep dur
      end
    end
  end
end

# -------------------------------------------------------------- harpsichord
# The court, and the only voice that does not survive the swallow. Sixteenths
# that fill every gap, because that is what a harpsichord is for. From bar 9 it
# is gone — there is nothing left to be polite about.
live_loop :liam_court, sync: :liam_drums do
  ch = (ring chord(:g4, :minor), chord(:d4, :major), chord(:c4, :minor), chord(:g4, :minor),
        chord(:eb4, :major), chord(:d4, :major), chord(:g4, :minor), chord(:d4, :major)).tick(:hc)
  bar = look(:bar) % 16
  if bar >= 8
    sleep 4
  else
    use_synth :pluck
    with_fx :reverb, room: 0.5, mix: 0.2 do
      16.times do |i|
        n = ch[[0, 1, 2, 1, 2, 1, 0, 1][i % 8]]
        n += 12 if i % 8 >= 4
        play n, amp: (i % 4 == 0 ? 0.42 : 0.26), coef: 0.35
        sleep 0.25
      end
    end
  end
end

# -------------------------------------------------------------------- tune
# ONE TUNE, TWICE. `court` is written out; `beast` is `court` with the three
# bent pitch classes dropped a half step and the whole line two octaves down on
# a distorted saw. Same rhythm, same shape, nothing left of the dignity.
live_loop :liam_theme, sync: :liam_drums do
  court = [
    [:g4, 1.5], [:a4, 0.5], [:bb4, 1], [:d5, 1],       # Gm — carried in
    [:d5, 1.5], [:c5, 0.5], [:bb4, 1], [:a4, 1],       # D  — and set down
    [:c5, 1.5], [:d5, 0.5], [:eb5, 1], [:g5, 1],       # Cm — he stands up
    [:fs5, 1], [:g5, 1], [:d5, 2],                     # Gm — the leading note
    [:eb5, 1.5], [:d5, 0.5], [:c5, 1], [:bb4, 1],      # Eb — pleased with itself
    [:a4, 1], [:bb4, 1], [:cs5, 2],                    # D  — the flourish
    [:g5, 1.5], [:fs5, 0.5], [:g5, 1], [:bb5, 1],      # Gm — the last slap
    [:a5, 2], [:d5, 2]                                 # D  — and Bixby has had enough
  ]
  bar = look(:bar) % 16
  if bar >= 14
    sleep 8
  elsif bar >= 8
    # THE BEAST. The same tune, bent, two octaves down, on a saw. Bars 9-14, so
    # the last two phrases are cut: he does not finish the sentence, he roars.
    bent = [2, 9, 6]   # D, A, F# — the fifth, the second and the leading note
    beast = court.map do |n, dur|
      pitch = note(n)
      pitch -= 1 if bent.include?(pitch % 12)
      [pitch - 24, dur]
    end
    # Six bars, not eight: he does not get to finish the sentence. Counted in
    # beats rather than in notes, so editing the tune above cannot desync this.
    left = 24.0
    use_synth :dsaw
    with_fx :distortion, distort: 0.4, mix: 0.5 do
      with_fx :reverb, room: 0.8, mix: 0.3 do
        beast.take_while { |_, dur| (left -= dur) >= 0 }.each do |n, dur|
          play n, amp: 0.62, attack: 0.01, sustain: dur * 0.55, release: 0.3,
            cutoff: 94, detune: 0.22
          play n + 12, amp: 0.3, attack: 0.01, sustain: dur * 0.5, release: 0.25,
            cutoff: 88, detune: 0.2
          sleep dur
        end
      end
    end
  else
    use_synth :blade
    with_fx :reverb, room: 0.6, mix: 0.25 do
      court.each do |n, dur|
        play n, amp: 0.6, attack: 0.02, sustain: dur * 0.5, release: 0.28,
          cutoff: 104, vibrato_rate: 4
        sleep dur
      end
    end
  end
end

# ------------------------------------------------------------------- wings
# Bars 9-14: two wingbeats a bar, down low where you feel them rather than hear
# them, with the fire breath arriving on the bars the fight breathes fire.
live_loop :liam_wings, sync: :liam_drums do
  bar = look(:bar) % 16
  if bar >= 8 && bar < 14
    2.times do |i|
      sample :perc_swash, amp: 0.55, rate: 0.5
      synth :noise, amp: 0.2, attack: 0.15, sustain: 0.1, release: 0.5, cutoff: 70
      sleep 1
      if bar.odd? && i == 1
        # The fire. A noise sweep that opens up and closes on you.
        breath = synth :cnoise, amp: 0.35, attack: 0.25, sustain: 0.5, release: 0.5,
          cutoff: 60, cutoff_slide: 0.9
        control breath, cutoff: 118
        sleep 1
      else
        sleep 1
      end
    end
  else
    sleep 4
  end
end

# -------------------------------------------------------------------- roar
# BARS 15-16. Every other voice is written to drop away, so this is the only
# thing left. He pulls up, hangs there, and lands — and the landing is the
# window you get to hit him.
live_loop :liam_roar, sync: :liam_drums do
  bar = look(:bar) % 16
  if bar == 14
    # The pull-up. Everything rises and nothing resolves.
    use_synth :dsaw
    rise = play :g2, amp: 0.55, attack: 0.05, sustain: 3.2, release: 0.6,
      note_slide: 3.4, cutoff: 70, cutoff_slide: 3.4, detune: 0.3
    control rise, note: :g4, cutoff: 115
    sample :perc_swash, amp: 0.6, rate: 0.4
    sleep 4
  elsif bar == 15
    # The roar, and the landing.
    use_synth :growl
    with_fx :distortion, distort: 0.55, mix: 0.6 do
      play [:g1, :db2, :g2], amp: 0.7, attack: 0.08, sustain: 1.4, release: 1.0
      sample :drum_heavy_kick, amp: 1.9
      sleep 2
      sample :drum_heavy_kick, amp: 2.0
      sample :drum_splash_hard, amp: 0.85, rate: 0.4
      play [:g1, :ab1, :db2], amp: 0.6, attack: 0.01, sustain: 0.8, release: 1.2
      sleep 2
    end
  else
    sleep 4
  end
end
