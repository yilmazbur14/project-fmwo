# JORDAN — "The Last Name on the List", draft 3 (the one with a bass in it)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# READ THIS FIRST: THE FINAL BOSS HAS NO BASS, NO TUNE AND NO SUMMON.
#
# Draft 2 shipped (Assets/Audio/Music/jordan_theme.wav), but five of its six
# voices branch on `bar = look(:bar) % 16`, reading a counter jordan_drums owns.
# Sonic Pi tick counters are live_loop-local and are NOT inherited — verified in
# the installed engine at app/server/ruby/core.rb:265, where
# ThreadLocalCounter.get_or_create_counters stores them with
# __thread_locals.set_local, the non-inherited setter, keyed on Thread.current,
# and look returns (val || 0). A live_loop is a thread. So those five loops read
# bar == 0 on every iteration, forever, deterministically. In the shipped WAV:
#
#     jordan_bass    0 events  (should be 132) — no bass. Not a thin bass, not
#                              a quiet bass. None, at any point, ever.
#     jordan_lead    0 events  (should be 42)  — THE LAST NAME never plays. The
#                              big statement of the phrase, the thing the whole
#                              piece is built to arrive at, is not on the record.
#     jordan_fuses   0 events  (should be 54)  — the summon never lights.
#     jordan_box    96 events  (96 expected, but all the SHELF version) — the
#                              box never gets buried, never transposes, and
#                              plays the identical bar sixteen times.
#     jordan_hall   16 events  (16 expected, but all the SHELF drone) — the
#                              fuse's opening pad and the climb's harmony have
#                              never sounded.
#
# What is actually on that WAV is: a drum machine, one unchanging music box, and
# one unchanging high drone. That is the final boss of the game.
#
# I found this the slow way before it was pointed out to me, which is worth
# recording because it is the only reason I trust it. Hunting for the fuse in
# the spectrum — elec_tick at 4, then 8, then 16, then 24 hits a bar, a doubling
# ramp that should be unmistakable — I could not find it. Bars 2-8 of the 2-8 kHz
# band all read about six onsets, flat. I wrote it off as "the fuses are
# inaudible or my band is wrong". They were neither. They were absent.
# Two other anomalies had the same cause: 630-1250 Hz DROPS 4 dB across bars
# 9-12, where a distorted saw lead in octaves ought to be the loudest thing in
# the mix, and the box's C6 measures dead flat across all sixteen bars.
#
# SO: BARS 5-16 OF THIS PIECE ARE UNRELEASED, NOT REVISED. There is no "before"
# to A/B against for three quarters of the track. The first thing to do with
# this file is record it and hear the piece for the first time. Everything below
# is a small correction to something that until now existed only on paper, and
# several of the notes say plainly which of my claims are measurements and which
# are only readings of the score — because for this theme, most of them are
# readings.
#
# THE ONE IDEA, UNCHANGED: the entire piece is built out of ONE eight-note
# music-box phrase with a broken tooth. Every time it reaches for its fifth it
# lands on Gb instead of G, and two of its teeth are worn enough to skip.
# jordan_lead plays that phrase at a quarter of the speed and eight times the
# size, jordan_hall harmonises the climb on the broken note itself, and the box
# never stops. In THE LAST NAME the worn teeth fill in; the flaw that stays is
# the Gb. The toy has become the man. Not one note of any of that is altered.
#
# WHAT CHANGED, AND WHY
#
# 1. EVERY LOOP OWNS ITS OWN BAR COUNTER.
#    This is the change. The other four are housekeeping next to it, and they
#    only matter because this one lets anybody hear them. jordan_box,
#    jordan_hall, jordan_bass, jordan_lead and jordan_fuses each tick their own
#    key now (:box, :hall, :bass, :lead, :fuse) instead of reading jordan_drums'
#    :bar, which is the fix eric_theme_v3.rb uses.
#    Being exact about the failure mode, because "race" is the intuitive guess
#    and it is wrong: there is no window, no interleaving, nothing that varies
#    between runs. look() on a key the calling thread has never ticked returns a
#    flat 0 by construction, so `bar >= 8` is not occasionally false, it is never
#    true. Deterministic total failure — which at least means running the file
#    catches it, and scratchpad/check_fmwo.rb now does: it simulates each loop
#    with its own counters, runs every loop twice (once as Sonic Pi really
#    behaves, once as the comments intend) and fails the file when the two
#    performances differ. eric_theme_v3.rb passes it clean.
#
# 2. THE BASS MOVES UP AN OCTAVE, SO THE FINAL BOSS IS ACTUALLY THE BIGGEST.
#    Measured, and the most alarming number in the set. Per-band RMS of the four
#    shipped themes at the in-game gain, then again through rolloffs standing in
#    for what people actually listen on:
#
#                     full     >60 Hz   >100 Hz  >150 Hz   % power <40 Hz
#        ERIC (b1)   -22.2     -25.2     -29.0    -31.2          0.1%
#        LIAM        -18.4     -22.8     -25.4    -27.8         27.3%
#        JORDAN      -14.1     -22.8     -29.1    -31.9         96.2%
#
#    Full-band, Jordan is 8.1 dB above boss 1: the ladder climbs. Through
#    anything resembling a laptop, a phone or a TV, Jordan is 0.1 dB QUIETER
#    than boss 1 and 3.7 dB quieter than Liam. The ladder inverts at the top.
#    96.2% of the final boss's power is below 40 Hz.
#    Where that comes from is not where I first said it came from. I blamed
#    jordan_bass on c1/ab0/gb0 — and jordan_bass produces zero events, so it
#    cannot be. It is jordan_drums: bd_boom at rate 0.6, six hits a bar, whose
#    overlapping pitched-down decays smear into something that measures like a
#    drone (crest 4.5 dB at duty 0.53, which is why the transient/sustained
#    heuristic pointed me at a synth).
#    That makes the octave change MORE necessary, not less. The bass is about to
#    play for the first time, and it is written on c1 (33 Hz), ab0 (26 Hz) and
#    gb0 (23 Hz) — an octave BELOW even the pitched-down kick, into a band that
#    is already carrying 96% of the record and reproducing none of it. Adding it
#    as written would compound the exact problem the table above describes.
#    Moved to c2/ab1/gb1 (65 / 52 / 46 Hz). For scale: Eric puts his low end
#    28 dB ABOVE his sub-40 band (40-80 at -18.0, 20-40 at -46.0). Jordan is
#    about to put his 16 dB below it. Same notes, same rhythm, same chromatic
#    walk-down, same synth, same distortion — one octave, and the floor lands
#    where a floor is heard.
#
# 3. WHEN THE BOX GETS BURIED IT GOES UP, NOT DOWN.
#    Read from the score, and it is the one place I have changed the direction
#    of an existing idea rather than its degree, so here is the whole argument.
#    Draft 2 buries the box by dropping it an octave and down to amp 0.16. The
#    lead's big statement is
#        whole = [:c6, :eb6, :gb6, :eb6, :c6, :ab5, :gb5, :c6]
#    played at amp 0.7 with an octave doubling at note - 12 at amp 0.4. So in
#    bars 9-12 the lead occupies exactly C5 and C6 — and C5 is precisely where
#    draft 2 sends the box. The box would be doubled, note for note, in its own
#    octave, by a distorted saw at two and a half times its amplitude playing
#    the same phrase. That is Eric's chant-and-shields fault in its purest form:
#    same pitch class, same octave, same downbeat, so the "voice that never
#    stops" is a voice nobody can confirm ever started.
#    The measurement agrees as far as it can: a narrowband probe at C5 reads
#    -51.7 dBFS over bars 9-12 against -50.6 dBFS everywhere else — the box's
#    burial band is QUIETER than the rest of the piece. (With the lead silent
#    that number proves less than it looks, but it rules out the hopeful reading
#    that the box is faintly poking through.)
#    So the box now goes UP an octave when everything else lands. Three reasons.
#    It is the only register the lead leaves free. It lands in 1.25-2.5 kHz,
#    which measures -44 dB in the back half against -38 in the lead's own band —
#    a 6 dB hole. And it is a better idea: a music box you cannot hear over the
#    noise is just an absent music box, whereas one you can still hear, shrill
#    and small and directly on top of the biggest thing in the game, is the
#    actual frightening version. The toy does not get muffled. It gets
#    inescapable. "The box never stops" becomes a thing a listener can verify
#    rather than a thing the source code asserts.
#    The phrase, the rhythm, the Gb and the worn teeth are untouched.
#
# 4. THE SHELF STOPS BEING A HOLE, AND THE LOOP STOPS DEPENDING ON AN ACCIDENT.
#    Measured on cycle 2 of the raw take (see the note below on why cycle 1 is
#    unusable), per-bar RMS:
#       -14.1 -27.7 -31.3 -31.4 -27.8 -25.0 -23.2 -21.6 | -12.5 -10.9 -10.9
#       -11.2 -11.1 -10.9 -11.0 -11.2
#    Bars 2-4 sit twenty decibels below bar 16. The music effectively disappears
#    for 5.3 seconds of every 21.3-second loop, in a fight the player is losing.
#    And that is the flattering version, with a box and a drone in it; once the
#    lead and the bass arrive the contrast gets bigger, not smaller.
#    Note bar 1 measures -14.1 while bars 2-4 measure -31: bar 1 is only
#    survivable because it inherits the ring-out of the previous cycle's bar 16.
#    That is an accident of cutting a loop out of a continuous performance, and
#    it evaporates the moment anyone cuts from a cycle that has no ring-in.
#    jordan_bass's shelf branch was `sleep 4` — literally nothing. It now holds
#    one long low note across bars 1-2, decaying: the room ringing after the
#    explosion. It fills the measured hole exactly where the hole is, it makes
#    the return read as aftermath rather than as a track restarting, and it
#    makes the loop robust instead of lucky.
#
# 5. THE TAIL STOPS BEING GUILLOTINED QUITE SO HARD.
#    All eight themes now import with edit/loop_mode=2, loop_begin=0,
#    loop_end=-1, so the loop point is exactly the file boundary and whatever is
#    ringing at the last sample is cut dead. Mean |x| over Jordan's final 5 ms
#    is 0.526 — over half of full scale, by far the worst in the set (Eric 0.147,
#    Liam 0.109, Danny 0.338). Bar 16's tom fill now shortens as it goes so the
#    last hit has decayed further by the cut.
#    This is a dent, not a fix. The real fix is three milliseconds of fade at the
#    boundary in cut_loop.py, which would solve it for all eight themes at once
#    and cost nothing musically. Worth doing there rather than bending every
#    theme's last bar around a tooling limitation.
#
# WHAT I GOT WRONG, AND WHAT THE MEASUREMENTS CORRECTED
#   I had a rewrite of bar 16 written before I had measured anything. The brief
#   flagged Jordan's seam as the interesting case in the set — a loop that
#   returns from the biggest moment in the game to a music box on a shelf — and
#   the shipped file backed that up violently: last 5 ms at -11.5 dB, first 5 ms
#   at -34.5 dB, a 23 dB cliff. So I wrote a new bar 16 that descended out of the
#   climb and handed the phrase back to the box.
#   Then I compared cycles of the raw take. The shipped WAV was cut from cycle 1,
#   and in cycle 1 every `sync:`ed loop has not started yet, so bar 1 is nearly
#   empty — cycle 1's bar 1 is -18.9 dB against bars 2-8, cycle 2's is -0.7 dB.
#   Measured on cycle 2, the seam is bar 16 -11.2 dB into bar 1 -14.1 dB: a drop
#   of 2.9 dB, and +0.4 dB comparing the last and first 200 ms. The 23 dB cliff
#   was a cut error. The joint itself is fine.
#   So the rewrite went in the bin, and what replaced it is change 4, which
#   addresses the real hole — one bar LATER than the seam, in bars 2-4, which is
#   not where I was looking. Bar 16 is untouched in this draft. Restraint here
#   was not a stylistic preference; it was the measurement refusing to support
#   the change I had already written.
#
# ON THE "PLAYABLE BY A CHILD ON ONE FINGER" TEST
#   The brief asked whether the big statements still pass it. They do.
#   `whole` is eight notes at two beats each — 0.667 s a note at 180 — which is
#   slower and more singable than the box's own version of the same phrase.
#   The climb is thirteen notes across four bars, all quarters and halves, and
#   every one of its four bars is drawn from the phrase: bar 2 is the box's
#   first three notes backwards, bar 4 is them forwards plus the octave, and
#   bars 1 and 3 are triads rooted on the phrase's own Ab and Gb. Nothing in the
#   piece needs more than one finger, which is the point — the flaw is in the
#   interval, not the difficulty.
#
# WHAT WAS DELIBERATELY LEFT ALONE
#   180 bpm. C minor with a flat five. The eight-note phrase and its Gb. The two
#   worn teeth, and their filling-in in THE LAST NAME — including the fact that
#   both are filled with C, which gives three C6s in eight notes and makes the
#   phrase cyclic rather than repetitive. The lead at quarter speed in octaves.
#   The climb's derivation. The fuse's doubling, doubling, and going off. The
#   16-bar form and its four-part shape. Bar 16. bd_boom at rate 0.6 — it is the
#   reason the kit reads as enormous on anything with a woofer, and change 2
#   adds the audible weight rather than taking that away.
#
# ONE THING I FOUND AND DID NOT FIX HERE, BECAUSE IT IS NOT A COMPOSITION BUG
#   The shipped jordan_theme.wav was cut from the FIRST cycle of the take.
#   cut_loop.py takes the first transient in the file and cuts one cycle from
#   there, and a `sync:`ed live_loop waits for the loop it syncs to to cue
#   again — a bar later — so cycle 1 is missing most of its arrangement.
#   Comparing cycles of jordan_theme_raw.wav directly:
#     cycle 1  bar 1 is -18.9 dB against the mean of bars 2-8
#     cycle 2  bar 1 is  -0.7 dB against the mean of bars 2-8
#   Bar 1 of the shipped loop is nearly empty, and with loop_mode=2 that hole
#   now repeats forever. Eric escaped it only because his take happened to start
#   at 0.000 s already in progress. The fix is in the pipeline: record at least
#   three cycles and cut a middle one, e.g. with --offset one cycle length.
#   It costs nothing and it is worth more than anything in this file except
#   change 1.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run at least THREE times
# through the 16 bars, hit Rec again, and cut a middle cycle. The cycle is
# unchanged at 16 bars x 4 beats / 180 bpm = 21.3333 s, so:
#   python cut_loop.py jordan_theme_v3_raw.wav 180 --out <somewhere>/jordan_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B — though
# for bars 5-16 there is nothing to A/B against, only something to hear.
#
# 180 bpm, C minor with a flat five. 16-bar cycle, in four:
#   Bars 1-4    THE SHELF     — the box, a clockwork tick, a cold high drone,
#                               and the last low note of the climb dying away.
#   Bars 5-8    THE FUSE      — a heartbeat starts, the pad opens, the ticks
#                               double, double again, and go off on bar 9.
#   Bars 9-12   THE LAST NAME — everything lands. The phrase in octaves, at
#                               quarter speed, over the biggest kit in the game,
#                               with the box still going, an octave up.
#   Bars 13-16  THE CLIMB     — Ab, then Gb (the broken note, now the whole
#                               harmony), then the turn back to the shelf.

use_bpm 180

# THE PHRASE, which everything in this file is built from:
#   c6  eb6  gb6  eb6  --  ab5  gb5  --
# The gb is the broken tooth where the fifth should be; the two gaps are the
# worn teeth. It is written out inside each loop that plays it rather than held
# in a constant up here, so re-running the buffer never complains.
#
# ------------------------------------------------------------------- drums
# Three states, not two. The shelf is a tick and a boxed-in little kick with no
# low end at all. The fuse brings a heartbeat that gets louder every bar. From
# bar 9 it is the biggest kit in the game and it does not get smaller again.
# This is the only loop in draft 2 that worked, because it is the only one that
# ticked its own counter. Unchanged apart from the bar 16 fill — see change 5.
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
      if (bar == 11 || bar == 15) && s >= 12
        # Bar 16's fill shortens as it goes, so less of it is still ringing
        # when loop_mode=2 cuts the file dead on the next sample.
        step = s - 12
        rate = bar == 15 ? 0.7 + step * 0.12 : 0.7
        sample :drum_tom_lo_hard, amp: 0.85, rate: rate
      end
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
# never once stops. Until now that was a claim the source code made and the
# recording could not support — the loop was pinned to bar 0, so it played the
# identical shelf bar sixteen times and never buried at all.
#
# CHANGED: when everything else lands, the box goes UP an octave, not down.
# Draft 2 dropped it to C5, which is exactly where jordan_lead's octave doubling
# plays, at two and a half times the amplitude, on the same notes of the same
# phrase — so "buried" meant "doubled into inaudibility" and the best idea in
# the piece could not be verified by ear. Up an octave it owns C7, the only
# register the lead leaves free, and it lands in 1.25-2.5 kHz, which measures a
# 6 dB hole in the back half. A music box nobody can hear is an absent music
# box; one that is still going, shrill and small, directly on top of the loudest
# thing in the game, is the frightening version.
# 8 x 0.5 = 4 beats.
live_loop :jordan_box, sync: :jordan_drums do
  bar = tick(:box) % 16
  buried = bar >= 8
  phrase = [:c6, :eb6, :gb6, :eb6, nil, :ab5, :gb5, nil]
  use_synth :pretty_bell
  with_fx :reverb, room: buried ? 0.4 : 0.85, mix: buried ? 0.18 : 0.5 do
    phrase.each do |n|
      unless n.nil?
        play (buried ? note(n) + 12 : note(n)),
          amp: buried ? 0.22 : 0.42,
          attack: 0.001,
          release: buried ? 0.25 : 0.6
      end
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- hall
# The cold room the shelf sits in. A high drone on the shelf, opening through
# the fuse, and from bar 13 it harmonises the climb on the broken note itself.
# Unchanged from draft 2 apart from owning its counter — which means the fuse
# pad and the climb harmony will be heard here for the first time.
#
# noise: on :hollow is enumerated, not continuous — Sonic Pi types it :float but
# bounds it to [0, 1, 2, 3, 4] and validates with Array#include?. Measured
# against the real validator: 1 is accepted, 1.0 is accepted (1.0 == 1 in Ruby)
# and lands on the same source, and 0.5 RAISES. The raise happens inside this
# live_loop and kills this live_loop only — every other loop plays on, so the
# recording sounds fine and is silently short a layer. That is the bug that
# shipped in three themes. 1 is brown noise. Pass an Integer.
live_loop :jordan_hall, sync: :jordan_drums do
  bar = tick(:hall) % 16
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
# The floor the rest of the piece stands on — and, in draft 2, a floor that has
# never once been under anything.
#
# CHANGED (2): up one octave, c1/ab0/gb0 -> c2/ab1/gb1. ab0 is 26 Hz and gb0 is
# 23 Hz. The shipped record already puts 96.2% of its power below 40 Hz (that is
# the kit, not this loop, which is silent), and through a 100 Hz rolloff the
# final boss measures 0.1 dB QUIETER than boss 1. Adding this line as written
# would have poured the one voice that is supposed to make him the biggest thing
# in the game into the one band nobody can hear. Eric keeps his low end 28 dB
# above his sub-40; this was about to sit 16 dB below it.
# CHANGED (4): the shelf is no longer silent. It was `sleep 4` for four bars —
# a measured 20 dB hole against bar 16, 5.3 seconds long, every 21 seconds. Bars
# 1-2 now hold the last low note of the climb, decaying: the room after the
# explosion. It also stops the loop depending on inheriting a ring-out from the
# previous cycle, which is luck rather than composition.
# 16 x 0.25 = 4 beats when big; 4 beats flat otherwise.
live_loop :jordan_bass, sync: :jordan_drums do
  bar = tick(:bass) % 16
  if bar < 2
    # Aftermath. Nothing is played here; this is bar 16 still dying.
    use_synth :tb303
    play :c2, amp: 0.46 - bar * 0.2, attack: 0.02, sustain: 0.8,
      release: 2.8, res: 0.45, cutoff: 58
    sleep 4
  elsif bar < 4
    sleep 4                                    # and now he is just standing there
  elsif bar < 8
    use_synth :tb303
    with_fx :lpf, cutoff: 60 + (bar - 4) * 8 do
      play :c2, amp: 0.5 + (bar - 4) * 0.1, attack: 0.02, sustain: 2,
        release: 1.5, res: 0.7
    end
    sleep 4
  else
    root = note([:c2, :c2, :ab1, :ab1, :c2, :c2, :gb1, :gb1][bar % 8])
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
#
# Not one note of this is changed. It has simply never played, so this is its
# first outing rather than its second draft.
# bar < 8: 4 beats. Bars 9-12: 2 x 2 = 4 beats a bar. Bars 13-16: see `climb`.
live_loop :jordan_lead, sync: :jordan_drums do
  bar = tick(:lead) % 16
  if bar < 8
    sleep 4
  elsif bar < 12
    # The phrase, whole, at quarter speed: eight notes, two beats each, spread
    # across four bars — two notes a bar.
    whole = [:c6, :eb6, :gb6, :eb6, :c6, :ab5, :gb5, :c6]
    pair = whole[(bar - 8) * 2, 2]
    use_synth :dsaw
    with_fx :distortion, distort: 0.4, mix: 0.5 do
      with_fx :reverb, room: 0.7, mix: 0.25 do
        pair.each do |n|
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
      [[:ab5, 1], [:c6, 1], [:eb6, 2]],                  # 13 Ab — lifting
      [[:gb6, 1], [:eb6, 1], [:c6, 2]],                  # 14 Gb — the broken
                                                         #    note, on top
      [[:gb5, 1], [:bb5, 1], [:db6, 2]],                 # 15 Gb — and it is the
                                                         #    harmony now
      [[:c6, 1], [:eb6, 1], [:gb6, 1], [:c7, 1]]         # 16 turn — the phrase
                                                         #    forwards, plus the
                                                         #    octave, back to
                                                         #    the shelf
    ][bar - 12]
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
#
# Unchanged from draft 2, and never once heard: searching the shipped WAV for
# this exact 4 -> 8 -> 16 -> 24 ramp is what led to finding the counter bug.
# 4 x 1 = 4; 8 x 0.5 = 4; 16 x 0.25 = 4; 24 x 0.125 + 1 = 4.
live_loop :jordan_fuses, sync: :jordan_drums do
  bar = tick(:fuse) % 16
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
