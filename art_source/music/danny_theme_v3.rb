# DANNY — "Four Hundred Pounds of Nap", draft 3 (the one you can hear)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# READ THIS FIRST: MOST OF THIS PIECE HAS NEVER BEEN HEARD.
#
# Draft 2 shipped (Assets/Audio/Music/danny_theme.wav), but four of its five
# voices branch on `bar = look(:bar) % 16`, reading a counter danny_taiko owns.
# Sonic Pi tick counters are live_loop-local and are NOT inherited — verified in
# the installed engine at app/server/ruby/core.rb:265, where
# ThreadLocalCounter.get_or_create_counters stores them with
# __thread_locals.set_local, the non-inherited setter, keyed on Thread.current,
# and look returns (val || 0). A live_loop is a thread. So those four loops read
# bar == 0 on every iteration, forever, deterministically. In the shipped WAV:
#
#     danny_slap       0 events   (should be 201) — THE HUNDRED-HAND SLAP,
#                                 the thing the piece is named after, has
#                                 never played a single note.
#     danny_shamisen  36 events   (should be 98)  — plays the sleeping tune
#                                 sixteen bars running; the `hands` tune has
#                                 never played.
#     danny_sub       32 events   (should be 156) — the asleep breath forever;
#                                 the awake sixteenth floor has never played.
#     danny_snore     48 events   (should be 9)   — bar 0 satisfies
#                                 `bar < 6 && bar.even?`, so he snores on every
#                                 other bar of the whole loop, straight through
#                                 the part where he is supposed to be awake.
#
# So bars 9-16 of this piece are UNRELEASED, not revised. There is no "before"
# to A/B the back half against, because nobody has ever heard it. The first
# thing to do with this file is record it and listen to the second half for the
# first time; everything below is a small correction to a thing that until now
# existed only on paper.
#
# This is still NOT a rewrite. The idea draft 2 was built on is right and is
# measurably right: the whole piece is at 160 and the sleeping half is written
# in half time, so it drags like 80 and then doubles when he wakes without a
# tempo change. Draft 3 changes five things and leaves everything else exactly
# as it was. Tempo, key, mode, both tunes, the snore, the taiko patterns and the
# form are untouched.
#
# THE TRICK IS WORKING. I checked before touching anything. Autocorrelating the
# onset-strength envelope of the shipped WAV at fixed musical subdivisions:
#
#                        half-note   2-beat    BEAT(160)   8th    16th
#     bars 1-6 asleep      0.45       0.32       0.19      0.27   0.24
#     bars 9-16 awake      0.80       0.82       0.43      0.40   0.35
#
# Asleep, the notated 160 bpm beat is the WEAKEST periodicity in the music and
# the half-note is the strongest. Awake, the beat more than doubles. That is
# exactly the half-time illusion doing its job, and it is why nothing in this
# draft goes near the rhythm of either half.
# This measurement survives the dead-branch bug above, which is why it is worth
# trusting: the illusion lives in danny_taiko, and danny_taiko is the one loop
# that ticks :bar itself, so both of its halves really did play. What the number
# does NOT yet include is the slap, the awake sub and the awake tune, none of
# which have ever sounded. The trick works with the drums alone; it should only
# get stronger once the rest of the arrangement joins in.
# (My first pass at this counted thresholded onsets instead and reported that
# the sleeping half was BUSIER than the awake half — 17.4 vs 14.2 events a bar.
# That was the detector, not the music: a quiet half full of noise-based synths
# walks straight through a threshold with a constant floor. Counting events is
# not the same measurement as feeling a pulse, and only one of them is the
# question. Good thing to have learned before "fixing" the best idea in the
# piece.)
#
# WHAT CHANGED, AND WHY
#
# 1. THE SUB MOVES UP AN OCTAVE, SO IT IS AUDIBLE AND SO IT JOINS IN.
#    Per-band RMS of the shipped file at its in-game gain:
#      20-40 Hz -22.2 (56.8% of ALL power) | 40-80 -25.5 | 80-160 -31.9
#      160-315 -30.9 | 315-630 -39.9 | 630-1.25k -44.3 | 1.25-2.5k -42.6
#    The loudest band in the piece by a wide margin is 20-40 Hz, and its crest
#    factor is 7.0 dB at a duty cycle of 0.85 — that is a sustained synth, not a
#    drum. (I had assumed it was bd_boom at rate 0.55; the 40-80 band is the
#    drum, crest 12.0 at duty 0.31. Measuring settled it the other way round.)
#    So it is this loop, sitting on bb0 (29 Hz) and d1 (37 Hz).
#    Three things are wrong with that. It is below what a laptop, a phone, a TV
#    or ordinary headphones reproduce at all, so most of the record's power is
#    inaudible where it will actually be played. The file peaks at -0.1 dBFS, so
#    that inaudible power is eating every dB of headroom the rest of the mix
#    could have used. And it is FLAT: the 20-40 band reads
#      -22.7 -21.3 -21.6 -22.2 -22.4 -22.3 -22.5 -22.6 | -21.3 -21.9 -22.1
#      -22.9 -23.0 -22.9 -23.0 -21.8
#    across the sixteen bars — a range of 1.7 dB. The lowest voice in a piece
#    whose entire subject is a man waking up does not notice him waking up.
#    That flatness is the dead-branch bug, not a compositional choice: the
#    asleep branch is the only one that has ever run, so of course it never
#    changes. Fixing the counter will make the awake floor appear for the first
#    time. The octave problem is separate and survives the fix untouched —
#    the asleep branch genuinely did play, on bb0 and d1, for every one of those
#    sixteen bars, and that is genuinely where 56.8% of the record's power went.
#    Both need doing, and they are independent.
#    Moved up one octave to d2/bb1/f2/c2, which is exactly where Eric's bass
#    sits (his 40-80 band is -18.0 and his 20-40 is -46.0, a 28 dB gap; Danny
#    currently has that gap inverted by 3 dB). Same notes, same rhythm, same
#    synth, same distortion, same contour — one octave. A breath you feel in
#    your chest is 50-80 Hz; 29 Hz is a breath you feel in the building.
#    The sleeping half also drops its cutoff a little further below the awake
#    half, so the wake-up opens the filter as well as doubling the rhythm.
#
# 2. THE THIRTY-SECONDS STOP GETTING QUIETER THAN THE SIXTEENTHS.
#    READ FROM THE SCORE, NOT MEASURED — and it has to be, because danny_slap
#    has never produced a sound. The slap escalates 16ths (bars 9-12) -> 32nds
#    (bars 13-15), and draft 2 escalates it downwards: amp 0.5/0.32 for the
#    sixteenths, 0.42/0.24 for the thirty-seconds. The hardest four bars of the
#    fight are written quieter than the four before them. That is the textbook
#    "back half gets busier rather than bigger": more notes, less music. The
#    32nds now hold the 16ths' level and crescendo across bars 13-16 instead of
#    ducking, so the subdivision doubling reads as an escalation. Not one extra
#    note was added; the notes that were already there stopped apologising.
#    I first justified this with a measurement — b9 at -33 dBFS against b11-b15
#    at -46 to -48 across 1.25-5 kHz — and then found the slap is silent, so
#    that gap cannot be the slap. It is danny_taiko's drum_splash_hard at the
#    wake-up against its closed hats afterwards. Right conclusion, wrong
#    evidence; the evidence is now the score, and it will need re-measuring once
#    this loop has been recorded for the first time.
#
# 3. THE LOOP'S LAST CYMBAL NO LONGER GETS GUILLOTINED.
#    All eight themes now import with edit/loop_mode=2, loop_begin=0,
#    loop_end=-1 — the loop point is exactly the file boundary, so whatever is
#    ringing at the last sample is cut dead and restarted. Draft 2 fires
#    drum_splash_hard at rate 0.5 (a cymbal played at half speed, which decays
#    for seconds) on beat 4 of bar 16. Mean |x| over the final 5 ms of the
#    shipped file is 0.338 — a third of full scale, chopped. The splash moves to
#    bar 1's downbeat, where there is already one: the cymbal now STARTS at the
#    loop point instead of being killed by it, which costs nothing, since a
#    crash on the downbeat is what the bar wanted anyway.
#
# 4. THE AWAKE HALF OPENS WITH THE SLEEPING TUNE, PLAYED TWICE AS FAST.
#    This is one bar, and it is the only note change in the draft. Draft 2's two
#    halves share a key and a chord loop and no melodic material at all, so the
#    hundred hands arrive as a different piece rather than as the same man at
#    twice the speed — which is a shame, because doubling the speed of one thing
#    is precisely what the whole piece is about. Bar 9 is now bars 1-2 of the
#    sleeping tune compressed into a single bar: D held, up to F, E, D. It is
#    the same four pitches draft 2 already had in bar 9; they just take the
#    sleeping tune's dotted rhythm now instead of four flat eighths, so you can
#    hear that it IS the nap, awake. Bars 10-16 are untouched.
#
# 5. EVERY LOOP NOW OWNS ITS OWN BAR COUNTER. This is the one that matters.
#    See the top of this file for what it costs: four of five voices pinned to
#    bar 0 forever, the title gesture never played, the snore running through
#    the whole loop. danny_sub, danny_shamisen, danny_snore and danny_slap each
#    tick their own key now (:sub, :sham, :snore, :slap) instead of reading
#    danny_taiko's :bar, which is exactly the fix Eric's draft 3 uses.
#    Worth being precise about the failure mode, because I had it wrong myself
#    at first and "race" is the intuitive guess: it is not a race. There is no
#    window, no interleaving, nothing timing-dependent and nothing that differs
#    between runs. look() on a key the calling thread has never ticked returns
#    a flat 0, every time, by construction. That is worse than a race in every
#    way except one — being deterministic, it is trivially catchable by running
#    the file, which is what the harness now does.
#    Verified by scratchpad/check_fmwo.rb, which simulates each live_loop with
#    its own counters, runs every loop twice (once as Sonic Pi really behaves,
#    once as the comments intend) and fails the file when the two performances
#    differ. Its negative control catches thirteen injected fault classes
#    including this one, and eric_theme_v3.rb passes it clean.
#
# WHAT WAS DELIBERATELY LEFT ALONE
#   160 bpm. D hirajoshi (D E F A Bb). The half-time writing of bars 1-6 and the
#   real-grid writing of bars 9-16 — measured working, see the table above, and
#   the single thing this piece cannot afford to lose. The `weight` tune, note
#   for note. Bars 10-16 of `hands`. The snore, the bubble, and the joke. The
#   taiko's drag-and-late-kick swagger. The C natural at bar 13 that is him
#   opening his eyes. bd_boom at rate 0.55. The 16-bar form.
#   Also left alone on purpose: the fact that the awake half is only 0.8 dB
#   louder than the sleeping half. Danny's arc is carried by BRIGHTNESS, not
#   level — 2.5-5k goes from -60 dB in bars 3-6 to -33 dB at bar 9, a 27 dB
#   lift — and that is the right way round. A giant who wakes up should change
#   colour, not just volume, and the level headroom belongs to the fight's
#   sound effects.
#
# ONE THING I FOUND AND DID NOT FIX HERE, BECAUSE IT IS NOT A COMPOSITION BUG
#   The shipped danny_theme.wav was cut from the FIRST cycle of the take, and in
#   the first cycle every `sync:`ed loop has not started yet — a live_loop that
#   syncs to another one waits for that loop's next cue, which does not arrive
#   until a bar later. Comparing cycles of danny_theme_raw.wav directly:
#     cycle 1  bar 1 is -4.0 dB against the mean of bars 2-8
#     cycle 2  bar 1 is -0.0 dB against the mean of bars 2-8
#   So bar 1 of the shipped loop is missing most of its arrangement, and with
#   loop_mode=2 that hole now repeats forever. Danny's is the mild case (Liam's
#   cycle 1 bar 1 is -14.4 dB and Jordan's is -18.9 dB; Eric got away with it
#   because his take happened to start at 0.000 s already in progress). The fix
#   is in the pipeline, not in the notes: cut from the SECOND cycle or later.
#     python cut_loop.py danny_theme_v3_raw.wav 160 --offset 1.5 --out ...
#   Re-cutting costs nothing and is worth more than anything in this file.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run at least THREE times
# through the 16 bars, hit Rec again to save a WAV, and cut a middle cycle. The
# cycle is unchanged at 16 bars x 4 beats / 160 bpm = 24.0000 s, so:
#   python cut_loop.py danny_theme_v3_raw.wav 160 --out <somewhere>/danny_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B.
#
# 160 bpm, D hirajoshi (D E F A Bb) — the Japanese pentatonic with the two
# half-steps that make a shamisen sound like a shamisen. 16-bar cycle:
#   Bars 1-6    THE WEIGHT        — D D Bb Bb F F, written in half time: lazy,
#                                   dragged, snoring, with a sub underneath.
#   Bars 7-8    THE SHIRT         — he stirs. The roll starts, the breath goes
#                                   ragged, and the pitch climbs out of the nap.
#   Bars 9-16   THE HUNDRED HANDS — D D Bb Bb C C D D at full speed, opening
#                                   with the nap played at double speed. The C
#                                   natural is him opening his eyes. The slap
#                                   runs 16ths, then 32nds, and gets LOUDER.

use_bpm 160

# ---------------------------------------------------------------- the tunes
# Written out one bar at a time so the arithmetic is visible and checkable.
# [note, beats]; nil is a rest. Every bar must sum to 4.
define :danny_weight do
  [
    [[:d4, 3], [:f4, 1]],                       # 1  D  — one note, held. In half
                                                #    time this is a whole note
                                                #    and a quarter: he is a man
                                                #    asleep on a grid he is not
                                                #    using.
    [[:e4, 2], [:d4, 2]],                       # 2  D  — and down
    [[:bb3, 3], [:a3, 1]],                      # 3  Bb — lower still
    [[:f4, 2], [:e4, 2]],                       # 4  Bb — barely awake
    [[:f4, 2], [:a4, 1.5], [:f4, 0.5]],         # 5  F  — a flicker. The only
                                                #    short values in the half,
                                                #    and they are a twitch.
    [[:e4, 3], [nil, 1]],                       # 6  F  — gone again
    [[:a4, 2], [:bb4, 1], [:a4, 1]],            # 7  A  — the half-step
    [[:f4, 2], [:e4, 1], [:d4, 1]]              # 8  A  — and out
  ]
end

define :danny_hands do
  [
    [[:d5, 1.5], [:f5, 0.5], [:e5, 1], [:d5, 1]],                          # 9  D — THE NAP AT
                                                                           #    DOUBLE SPEED.
                                                                           #    Bars 1-2 of the
                                                                           #    sleeping tune,
                                                                           #    compressed into
                                                                           #    one bar. Same
                                                                           #    four pitches
                                                                           #    draft 2 had; the
                                                                           #    rhythm is now the
                                                                           #    nap's, so you can
                                                                           #    hear what it is.
    [[:f5, 0.5], [:e5, 0.5], [:d5, 0.5], [:c5, 0.5], [:d5, 2]],            # 10 D — the C arrives
    [[:bb4, 0.5], [:d5, 0.5], [:f5, 0.5], [:bb5, 0.5], [:a5, 1], [:f5, 1]],# 11 Bb — climbing
    [[:e5, 0.5], [:f5, 0.5], [:d5, 1], [:bb4, 2]],                         # 12 Bb — held
    [[:c5, 0.5], [:e5, 0.5], [:g5, 0.5], [:c6, 0.5], [:bb5, 1], [:g5, 1]], # 13 C — the new chord
    [[:a5, 0.5], [:g5, 0.5], [:e5, 1], [:c5, 2]],                          # 14 C — driving
    [[:d5, 0.5], [:e5, 0.5], [:f5, 0.5], [:a5, 0.5], [:bb5, 1], [:a5, 1]], # 15 D — hammering
    [[:f5, 1], [:e5, 1], [:d5, 2]]                                         # 16 D — and again
  ]
end

# Bar-length check. Runs once, prints nothing when the tunes are correct.
(danny_weight + danny_hands).each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "danny_theme_v3: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# ------------------------------------------------------------------- taiko
# The big drum. Asleep it plays twice a bar with a drag in front of the second
# hit, which is the swagger: he gets there, just late. Two hits a bar at 160 is
# a pulse at 80, and that is the whole half-time illusion in one line.
# Awake it squares up and hits everything.
#
# Unchanged from draft 2 except that the bar 16 splash has moved to bar 1 — see
# change 3. Everything about the sleeping pattern is deliberately untouched.
live_loop :danny_taiko do
  bar = tick(:bar) % 16
  awake = bar >= 8
  stirring = bar == 6 || bar == 7
  # The bow, and the crash that used to be guillotined at the end of bar 16.
  # A cymbal at rate 0.5 rings for seconds; starting it here means the loop
  # point is the front of a crash instead of the middle of one.
  sample :drum_splash_hard, amp: 0.85, rate: 0.5 if bar == 0
  sample :drum_splash_hard, amp: 0.95, rate: 0.45 if bar == 8  # the shirt goes
  16.times do |s|
    if awake
      sample :bd_boom, amp: 1.85, rate: 0.6 if s % 4 == 0
      sample :bd_boom, amp: 1.0, rate: 0.7 if [6, 14].include?(s)
      sample :drum_snare_hard, amp: 0.6, rate: 0.85 if s == 4 || s == 12
      sample :drum_cymbal_closed, amp: 0.2, rate: 0.8 if s.odd?
      sample :drum_tom_lo_hard, amp: 0.8, rate: 0.7 if bar == 15 && s >= 12
    elsif stirring
      sample :bd_boom, amp: 1.7, rate: 0.55 if s == 0 || s == 8
      sample :drum_tom_lo_hard, amp: 0.5 + s * 0.02, rate: 0.65 if s % 2 == 0
      sample :drum_cymbal_closed, amp: 0.15, rate: 0.7 if bar == 7 && s.odd?
    else
      sample :bd_boom, amp: 1.75, rate: 0.55 if s == 0
      sample :drum_tom_lo_hard, amp: 0.4, rate: 0.6 if s == 9    # the drag
      sample :bd_boom, amp: 1.3, rate: 0.6 if s == 10            # the late one
      sample :drum_tom_mid_hard, amp: 0.26, rate: 0.7 if s == 6 && bar.even?
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- sub
# The breath. Long, low and slow while he is out, sixteenths once he is up.
#
# CHANGED: up one octave, from d1/bb0/f1/c1 to d2/bb1/f2/c2. bb0 is 29 Hz and
# d1 is 37 Hz — below what almost anything this ships to can reproduce — and the
# measurement found 56.8% of the whole record's power sitting down there, flat
# to within 1.7 dB across all sixteen bars, on a file that peaks at -0.1 dBFS.
# It was the loudest thing in the piece, nobody could hear it, it was using all
# the headroom, and it was the one voice that did not notice him waking up.
# d2/bb1/f2/c2 is exactly where Eric's bass sits. Same notes, same rhythm, same
# synth, same distortion, same offsets — one octave, and the piece gets its
# bottom end back in the band that plays it.
# 2 + 2 = 4 asleep; 8 x 0.5 = 4 stirring; 16 x 0.25 = 4 awake.
live_loop :danny_sub, sync: :danny_taiko do
  bar = tick(:sub) % 16
  root = note([:d2, :d2, :bb1, :bb1, :f2, :f2, :d2, :d2,
               :d2, :d2, :bb1, :bb1, :c2, :c2, :d2, :d2][bar])
  use_synth :tb303
  with_fx :distortion, distort: 0.3, mix: 0.4 do
    if bar >= 8
      # Awake: a floor that never stops moving.
      [0, 0, 12, 0, 0, 7, 0, 0, 0, 0, 12, 0, 7, 5, 3, 0].each_with_index do |off, s|
        play root + off, amp: (s % 4 == 0 ? 0.9 : 0.58),
          attack: 0.004, sustain: 0.05, release: 0.13, res: 0.85,
          cutoff: 80 + (s % 4 == 0 ? 16 : 0)
        sleep 0.25
      end
    elsif bar == 6 || bar == 7
      # Stirring: the breath goes ragged and starts climbing.
      8.times do |i|
        play root + (i >= 4 ? 12 : 0), amp: 0.5 + i * 0.04,
          attack: 0.01, sustain: 0.18, release: 0.2, res: 0.8, cutoff: 58 + i * 6
        sleep 0.5
      end
    else
      # Asleep: two enormous breaths a bar, in and out. The cutoff sits lower
      # than draft 2's now that the fundamental is an octave higher — the point
      # is that he is muffled, not that he is inaudible, and the wake-up opens
      # the filter as well as doubling the rhythm.
      play root, amp: 0.75, attack: 0.5, sustain: 1.0, release: 0.5, res: 0.7, cutoff: 50
      sleep 2
      play root, amp: 0.5, attack: 0.5, sustain: 0.8, release: 0.7, res: 0.7, cutoff: 44
      sleep 2
    end
  end
end

# ---------------------------------------------------------------- shamisen
# The tune, struck hard and left to decay. Asleep it is written in half time, so
# every note is twice the length of the grid and the line sags. Awake it plays
# on the grid, doubled an octave down, and stops sagging entirely — and it now
# opens by playing the nap at double speed, so the two halves are one piece.
live_loop :danny_shamisen, sync: :danny_taiko do
  bar = tick(:sham) % 16
  awake = bar >= 8
  phrase = awake ? danny_hands[bar - 8] : danny_weight[bar]
  use_synth :pluck
  with_fx :reverb, room: 0.6, mix: 0.25 do
    phrase.each do |n, dur|
      unless n.nil?
        play n, amp: awake ? 0.7 : 0.5, coef: awake ? 0.3 : 0.6
        if awake
          synth :dsaw, note: note(n) - 12, amp: 0.24, attack: 0.01,
            sustain: dur * 0.4, release: 0.22, cutoff: 96, detune: 0.16
        end
      end
      sleep dur
    end
  end
end

# ------------------------------------------------------------------- snore
# Bars 1-6 only. In, out, and a bubble popping on the way out. This is the joke,
# and it is funnier now that there is something enormous breathing under it.
# Unchanged from draft 2 apart from deriving its own bar.
#
# noise: on :hollow is an enumerated opt, not a continuous one — Sonic Pi
# declares it type :float but bounds it to the option list [0, 1, 2, 3, 4] and
# validates with Array#include?. Measured against the real validator:
#     noise: 2     Integer -> accepted
#     noise: 2.0   Float   -> accepted, same source (2.0 == 2 in Ruby)
#     noise: 0.5   Float   -> RAISES "must be one of [0, 1, 2, 3, 4]"
# So a whole-number Float is harmless-but-latent and a fractional one is fatal:
# the raise happens inside this live_loop, kills this live_loop and only this
# one, and every other loop plays on — so the recording sounds fine and is
# silently missing a layer. That is the bug that shipped in three themes.
# (eric_theme_v3.rb's note on this says a fractional value "gets truncated to a
# different source instead of raising". That is backwards; it raises. Worth
# correcting there too, since it is the file everyone is copying from.)
# 2 is white noise. Pass an Integer.
live_loop :danny_snore, sync: :danny_taiko do
  bar = tick(:snore) % 16
  if bar < 6 && bar.even?
    use_synth :hollow
    breathe_in = play :d3, amp: 0.34, attack: 0.9, sustain: 0.3, release: 0.6,
      note_slide: 1.2, res: 0.5, noise: 2, cutoff: 70
    control breathe_in, note: :f3
    sleep 2
    play :bb2, amp: 0.26, attack: 0.5, sustain: 0.4, release: 0.9,
      res: 0.4, noise: 2, cutoff: 60
    sleep 1.5
    sample :elec_blup, amp: 0.3, rate: 0.55   # the bubble
    sleep 0.5
  else
    sleep 4
  end
end

# -------------------------------------------------------------------- slap
# THE HUNDRED HANDS. It starts in bar 8 as a stir, and from bar 9 it is the
# loudest thing in the piece: sixteenths for four bars, then thirty-seconds.
#
# CHANGED: the thirty-seconds are no longer quieter than the sixteenths.
# Draft 2 went from amp 0.5/0.32 at the sixteenth to 0.42/0.24 at the
# thirty-second, and the measurement is brutal about it — in the two bands the
# slap owns, bar 9 reads -33 dBFS and bars 11-15 read -46 to -48. The hardest
# four bars of the fight were fifteen decibels below the moment he woke up. That
# is the classic back-half failure: the subdivision doubles, the arrangement
# gets busier, and the music gets smaller.
# Now the 32nds hold the 16ths' level and crescendo into bar 16, so doubling the
# speed reads as an escalation. No notes were added. The same hits are simply no
# longer apologising for being there.
# Bar 16's terminal splash has moved to bar 1's downbeat (change 3): the roll
# still accelerates into the loop point, but what lands there is the start of a
# cymbal rather than the middle of one being cut in half.
live_loop :danny_slap, sync: :danny_taiko do
  bar = tick(:slap) % 16
  if bar == 7
    # The stir. Slow, then not slow.
    [0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5].each_with_index do |gap, i|
      sample :elec_hi_snare, amp: 0.3 + i * 0.03, rate: 1.1
      sleep gap
    end
  elsif bar >= 8 && bar < 12
    16.times do |s|
      sample :elec_hi_snare, amp: s.even? ? 0.5 : 0.32, rate: 1.15 + (s % 4) * 0.04
      sleep 0.25
    end
  elsif bar >= 12 && bar < 15
    # Thirty-seconds. Level held against the sixteenths above, and lifting a
    # little each bar so three bars of roll go somewhere.
    lift = (bar - 12) * 0.04
    32.times do |s|
      sample :elec_hi_snare, amp: (s.even? ? 0.5 : 0.32) + lift, rate: 1.2 + (s % 8) * 0.03
      sleep 0.125
    end
  elsif bar == 15
    # One roll, accelerating, straight into the top of the loop.
    gaps = [0.25] * 4 + [0.125] * 8 + [0.0625] * 16
    gaps.each_with_index do |gap, i|
      sample :elec_hi_snare, amp: 0.42 + i * 0.012, rate: 1.2
      sleep gap
    end
    sample :drum_heavy_kick, amp: 1.9
    sleep 4 - gaps.sum
  else
    sleep 4
  end
end
