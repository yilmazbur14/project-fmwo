# ERIC — "The King's Own", draft 1
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# Eric is a white knight, loyal to his king. This is a medieval march in the
# heroic style those themes share: a minor key with a bright sixth, a horn call
# built on rising fourths and fifths, a lute under it, and a war drum. Nothing
# here is quoted from an existing piece; it's our own, so it can ship with a
# public repo.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec in Sonic Pi, let it run two or three
# times through, hit Rec again to save a WAV.
#
# The form is 8 bars of 4/4 at 104 bpm, looping:
#   i  VI III VII | i  VI VII i      (Dm  Bb  F  C | Dm  Bb  C  Dm)
# Every voice is its own live_loop, synced to the drums, so you can comment one
# out to hear the rest.

use_bpm 104

# ---------------------------------------------------------------- war drums
# Low drum on 1 and 3, a soft snare on the backbeats, and a roll into the
# repeat. This is the "army on the move" floor everything else sits on.
live_loop :eric_drums do
  bar = tick(:bar) % 8
  8.times do |i|
    sample :bd_boom, amp: 1.5, rate: 0.9 if i == 0 || i == 4
    sample :drum_snare_soft, amp: 0.55 if i == 2 || i == 6
    sample :drum_tom_lo_hard, amp: 0.7 if i == 7 && bar % 4 == 3
    sample :drum_snare_soft, amp: 0.45, rate: 1.15 if bar == 7 && i >= 4
    sleep 0.5
  end
end

# --------------------------------------------------------------------- bass
# Root for three beats, then the fifth as a pickup into the next chord.
live_loop :eric_bass, sync: :eric_drums do
  root = (ring :d2, :bb1, :f2, :c2, :d2, :bb1, :c2, :d2).tick(:bass)
  use_synth :tri
  with_fx :lpf, cutoff: 78 do
    play root, amp: 0.9, attack: 0.02, release: 2.6
    sleep 3
    play root + 7, amp: 0.55, attack: 0.01, release: 0.8
    sleep 1
  end
end

# --------------------------------------------------------------------- lute
# Plucked arpeggios keep the pulse moving without crowding the horn.
live_loop :eric_lute, sync: :eric_drums do
  ch = (ring chord(:d4, :minor), chord(:bb3, :major), chord(:f4, :major), chord(:c4, :major),
        chord(:d4, :minor), chord(:bb3, :major), chord(:c4, :major), chord(:d4, :minor)).tick(:lute)
  use_synth :pluck
  with_fx :reverb, room: 0.7, mix: 0.3 do
    8.times do |i|
      n = ch[i % 3]
      n += 12 if i >= 6
      play n, amp: 0.45, coef: 0.35
      sleep 0.5
    end
  end
end

# --------------------------------------------------------------------- horn
# The theme itself: a call on rising fourths, answered by a falling line.
# [note, beats]; nil is a rest.
live_loop :eric_horn, sync: :eric_drums do
  theme = [
    [:d5, 1], [:e5, 0.5], [:f5, 0.5], [:a5, 1], [:f5, 1],      # Dm  — the call
    [:g5, 1], [:f5, 0.5], [:e5, 0.5], [:d5, 2],                # Bb  — the answer
    [:c5, 1], [:d5, 0.5], [:e5, 0.5], [:f5, 1], [:e5, 1],      # F   — climbing
    [:d5, 2], [nil, 2],                                        # C   — breath
    [:a5, 1], [:a5, 0.5], [:g5, 0.5], [:f5, 1], [:e5, 1],      # Dm  — the oath
    [:d5, 1], [:f5, 1], [:a5, 2],                              # Bb  — lifted
    [:g5, 1], [:f5, 0.5], [:e5, 0.5], [:d5, 1], [:c5, 1],      # C   — descent
    [:d5, 2], [nil, 2]                                         # Dm  — home
  ]
  use_synth :prophet
  with_fx :reverb, room: 0.85, mix: 0.35 do
    theme.each do |n, dur|
      play n, amp: 0.7, attack: 0.03, sustain: dur * 0.5, release: 0.4, cutoff: 96 unless n.nil?
      sleep dur
    end
  end
end

# -------------------------------------------------------------------- choir
# A held pad every two bars, roots and fifths only, for the hall it's sung in.
live_loop :eric_choir, sync: :eric_drums do
  root = (ring :d4, :f4, :d4, :c4).tick(:choir)
  use_synth :hollow
  with_fx :reverb, room: 0.9, mix: 0.5 do
    play [root, root + 7], amp: 0.35, attack: 1.2, sustain: 4, release: 2.5
  end
  sleep 8
end

# ------------------------------------------------------------------ fanfare
# Optional opener: uncomment to hear the herald's call before the march.
# Run it once, then comment it out again.
#
# use_synth :blade
# with_fx :reverb, room: 0.9 do
#   [[:d4, 0.75], [:a4, 0.25], [:d5, 1], [:c5, 0.5], [:d5, 1.5]].each do |n, dur|
#     play n, amp: 0.8, attack: 0.02, sustain: dur * 0.6, release: 0.5
#     sleep dur
#   end
# end
