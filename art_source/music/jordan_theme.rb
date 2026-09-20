# JORDAN — "The Last Name on the List", draft 2 (the intense version)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Draft 1 had the right structure and the wrong nerve. It opened on a music box
# and a clockwork tick, built a fuse, and then "everything landed" — at 126 bpm,
# which is not a landing, it is an arrival. This is the last name on the ladder.
# It should be the loudest thing in the game.
#
# Draft 2 keeps every idea and raises the whole piece to 180. The shelf still
# feels slow, because the box is written in long notes over a fast grid; that is
# the trick, and it means the fuse can double and double again without a tempo
# change until the thing goes off.
#
# THE ONE IDEA, unchanged: the entire piece is built out of ONE eight-note
# music-box phrase with a broken tooth. Every time it reaches for its fifth it
# lands on Gb instead of G, and two of its teeth are worn enough to skip.
# `jordan_lead` plays that phrase at a quarter of the speed and eight times the
# size, `jordan_hall` harmonises the climb on the broken note itself, and the
# box never actually stops — it just gets buried, an octave down, under the
# rest. One new thing in draft 2: in THE LAST NAME the worn teeth are filled in.
# The flaw that stays is the Gb. The toy has become the man.
#
# Reference, for intensity: MEGALOVANIA, for the chromatic sixteenth bass and a
# lead that does not stop to breathe, and ASGORE, for a final theme that earns
# its size by stacking one pulse until there is no room left. Written in that
# spirit, never copied from anything: every note here is ours, so it can ship in
# a public repo.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. Any voice can be commented out to hear the rest.
#
# 180 bpm, C minor with a flat five. 16-bar cycle, in four:
#   Bars 1-4    THE SHELF     — the box, a clockwork tick, a cold high drone.
#                               Written for Jordan standing there doing nothing.
#   Bars 5-8    THE FUSE      — a heartbeat starts, the pad opens, the ticks
#                               double, double again, and go off on bar 9. This
#                               is the summon: figures out, fuses lit.
#   Bars 9-12   THE LAST NAME — everything lands. The phrase in octaves, at
#                               quarter speed, over the biggest kit in the game.
#   Bars 13-16  THE CLIMB     — Ab, then Gb (the broken note, now the whole
#                               harmony), then the turn back to the shelf.

use_bpm 180

# THE PHRASE, for reference, since everything in this file is built from it:
#   c6  eb6  gb6  eb6  --  ab5  gb5  --
# The gb is the broken tooth where the fifth should be; the two gaps are the
# worn teeth. It is written out inside each loop that plays it rather than held
# in a constant up here, so re-running the buffer never complains.
#
# ------------------------------------------------------------------- drums
# Three states, not two. The shelf is a tick and a boxed-in little kick with no
# low end at all. The fuse brings a heartbeat that gets louder every bar. From
# bar 9 it is the biggest kit in the game and it does not get smaller again.
live_loop :jordan_drums do
  bar = tick(:bar) % 16
  big = bar >= 8
  rising = bar >= 4 && bar < 8
  sample :drum_cymbal_open, amp: 0.6, rate: 0.8 if bar == 8
  sample :drum_cymbal_open, amp: 0.45, rate: 0.9 if bar == 12
  16.times do |s|
    if big
      sample :bd_boom, amp: 1.95, rate: 0.6 if [0, 3, 6, 8, 11, 14].include?(s)
      sample :drum_snare_hard, amp: 0.75, rate: 0.85 if s == 4 || s == 12
      sample :drum_snare_soft, amp: 0.3, rate: 1.25 if [7, 15].include?(s)
      sample :drum_cymbal_closed, amp: 0.22, rate: 0.9 if s.odd?
      sample :drum_tom_lo_hard, amp: 0.85, rate: 0.7 if (bar == 11 || bar == 15) && s >= 12
    elsif rising
      # The heartbeat. Two hits a bar, closer and louder every bar.
      beat_amp = 0.7 + (bar - 4) * 0.28
      sample :bd_boom, amp: beat_amp, rate: 0.55 if s == 0
      sample :bd_boom, amp: beat_amp * 0.8, rate: 0.55 if s == 3
      sample :drum_cymbal_closed, amp: 0.12 + (bar - 4) * 0.03, rate: 1.4 if s.even?
      sample :drum_snare_soft, amp: 0.3, rate: 1.1 if bar >= 6 && (s == 8 || s == 12)
    else
      sample :elec_blip2, amp: 0.2, rate: 1.8 if s % 4 == 0
      sample :bd_tek, amp: 0.35 if s == 0
    end
    sleep 0.25
  end
end

# --------------------------------------------------------------------- box
# The music box itself. It plays the phrase every bar for the whole sixteen and
# never once stops — from bar 9 it is simply buried an octave down under
# everything else, which is the quietest frightening idea in the piece.
live_loop :jordan_box, sync: :jordan_drums do
  bar = look(:bar) % 16
  buried = bar >= 8
  phrase = [:c6, :eb6, :gb6, :eb6, nil, :ab5, :gb5, nil]
  use_synth :pretty_bell
  with_fx :reverb, room: buried ? 0.5 : 0.85, mix: buried ? 0.2 : 0.5 do
    phrase.each do |n|
      unless n.nil?
        play (buried ? note(n) - 12 : note(n)),
          amp: buried ? 0.16 : 0.42, attack: 0.001, release: buried ? 0.3 : 0.6
      end
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- hall
# The cold room the shelf sits in. A high drone on the shelf, opening through
# the fuse, and from bar 13 it harmonises the climb on the broken note itself.
live_loop :jordan_hall, sync: :jordan_drums do
  bar = look(:bar) % 16
  use_synth :hollow
  with_fx :reverb, room: 0.95, mix: 0.6 do
    if bar >= 12
      play [:gb3, :bb3, :db4], amp: 0.34, attack: 0.3, sustain: 2.5, release: 1.2,
        res: 0.4, noise: 1, cutoff: 92
    elsif bar >= 4
      play [:c3, :eb3, :gb3], amp: 0.18 + (bar - 4) * 0.02, attack: 0.5,
        sustain: 2.2, release: 1.3, res: 0.35, noise: 1, cutoff: 70 + (bar - 4) * 4
    else
      play :c6, amp: 0.14, attack: 1.0, sustain: 1.8, release: 1.2,
        res: 0.3, noise: 1, cutoff: 96
    end
  end
  sleep 4
end

# -------------------------------------------------------------------- bass
# Nothing at all on the shelf. A single low note per bar through the fuse. From
# bar 9, sixteenths that walk down chromatically and never once rest — this is
# the floor the rest of the piece stands on.
live_loop :jordan_bass, sync: :jordan_drums do
  bar = look(:bar) % 16
  if bar < 4
    sleep 4
  elsif bar < 8
    use_synth :tb303
    with_fx :lpf, cutoff: 60 + (bar - 4) * 8 do
      play :c1, amp: 0.5 + (bar - 4) * 0.1, attack: 0.02, sustain: 2, release: 1.5, res: 0.7
    end
    sleep 4
  else
    root = note((ring :c1, :c1, :ab0, :ab0, :c1, :c1, :gb0, :gb0).look(:bar))
    use_synth :tb303
    with_fx :distortion, distort: 0.5, mix: 0.6 do
      [0, 0, 12, 0, 3, 2, 1, 0, 0, 0, 12, 0, 6, 5, 3, 0].each_with_index do |off, s|
        play root + off, amp: (s % 4 == 0 ? 0.95 : 0.62),
          attack: 0.004, sustain: 0.05, release: 0.12, res: 0.9,
          cutoff: 84 + (s % 4 == 0 ? 18 : 0)
        sleep 0.25
      end
    end
  end
end

# -------------------------------------------------------------------- lead
# THE LAST NAME. The same eight notes, at a quarter of the speed and eight times
# the size, in octaves on a distorted saw — and with the two worn teeth filled
# in, because at this size nothing is missing any more. Only the Gb stays wrong.
# Then THE CLIMB takes the broken note and makes it the whole harmony.
live_loop :jordan_lead, sync: :jordan_drums do
  bar = look(:bar) % 16
  if bar < 8
    sleep 4
  elsif bar < 12
    # The phrase, whole, at quarter speed: eight notes, two beats each.
    whole = [:c6, :eb6, :gb6, :eb6, :c6, :ab5, :gb5, :c6]
    use_synth :dsaw
    with_fx :distortion, distort: 0.4, mix: 0.5 do
      with_fx :reverb, room: 0.7, mix: 0.25 do
        whole.each do |n|
          play note(n), amp: 0.7, attack: 0.02, sustain: 1.2, release: 0.6,
            cutoff: 104, detune: 0.22
          play note(n) - 12, amp: 0.4, attack: 0.02, sustain: 1.1, release: 0.5,
            cutoff: 94, detune: 0.2
          sleep 2
        end
      end
    end
  else
    climb = [
      [:ab5, 1], [:c6, 1], [:eb6, 2],                    # Ab — lifting
      [:gb6, 1], [:eb6, 1], [:c6, 2],                    # Gb — the broken note, on top
      [:gb5, 1], [:bb5, 1], [:db6, 2],                   # Gb — and it is the harmony now
      [:c6, 1], [:eb6, 1], [:gb6, 1], [:c7, 1]           # turn — back to the shelf
    ]
    use_synth :dsaw
    with_fx :distortion, distort: 0.45, mix: 0.55 do
      with_fx :reverb, room: 0.75, mix: 0.28 do
        climb.each do |n, dur|
          play note(n), amp: 0.72, attack: 0.01, sustain: dur * 0.6, release: 0.35,
            cutoff: 108, detune: 0.24
          play note(n) - 12, amp: 0.4, attack: 0.01, sustain: dur * 0.55,
            release: 0.3, cutoff: 96, detune: 0.2
          sleep dur
        end
      end
    end
  end
end

# ------------------------------------------------------------------- fuses
# THE SUMMON. Bars 5-8 only: the ticks that double, double again, and go off.
# Written to phase one of the fight — figures out, fuses lit, and then they
# chase you until they explode.
live_loop :jordan_fuses, sync: :jordan_drums do
  bar = look(:bar) % 16
  case bar
  when 4
    4.times { sample :elec_tick, amp: 0.4, rate: 1.2; sleep 1 }
  when 5
    8.times { sample :elec_tick, amp: 0.45, rate: 1.3; sleep 0.5 }
  when 6
    16.times { sample :elec_tick, amp: 0.5, rate: 1.4; sleep 0.25 }
  when 7
    # The last bar of the fuse: thirty-seconds, and then it goes off.
    24.times { |i| sample :elec_tick, amp: 0.5 + i * 0.012, rate: 1.5; sleep 0.125 }
    sample :drum_heavy_kick, amp: 2.0
    sample :drum_splash_hard, amp: 0.9, rate: 0.5
    sleep 1
  else
    sleep 4
  end
end
