# LIAM & BIXBY — "Carried In, Swallowed Whole", draft 3 (the beast gets heavier)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# READ THIS FIRST: THE BEAST HAS NEVER PLAYED. NOT ONCE.
#
# Draft 2 shipped (Assets/Audio/Music/liam_theme.wav), but five of its six
# voices branch on `bar = look(:bar) % 16`, reading a counter liam_drums owns.
# Sonic Pi tick counters are live_loop-local and are NOT inherited — verified in
# the installed engine at app/server/ruby/core.rb:265, where
# ThreadLocalCounter.get_or_create_counters stores them with
# __thread_locals.set_local, the non-inherited setter, keyed on Thread.current,
# and look returns (val || 0). A live_loop is a thread. So those five loops read
# bar == 0 on every iteration, forever, deterministically. In the shipped WAV:
#
#     liam_theme    56 events  (should be 72)  — the court tune, sixteen bars
#                              running. THE BEAST TUNE HAS NEVER SOUNDED. The
#                              one idea this piece exists for — the same tune
#                              coming back bent and two octaves down — is not
#                              on the record.
#     liam_bass     64 events  (should be 160) — the polite walking bass
#                              forever; the distorted sixteenth floor never.
#     liam_court   256 events  (should be 128) — the harpsichord plays TWICE
#                              what it should, straight through the dragon. The
#                              one voice written not to survive the swallow is
#                              the one voice that never stops.
#     liam_wings     0 events  (should be 27)  — no wingbeats, no fire breath.
#     liam_roar      0 events  (should be 7)   — no pull-up, no roar, no
#                              landing. The window the player gets to hit him
#                              has never been scored.
#
# So bars 9-16 are UNRELEASED, not revised: there is no "before" to A/B the
# beast against, because nobody has ever heard it. The first thing to do with
# this file is record it and listen to the swallow for the first time.
#
# This is still NOT a rewrite. The idea is the best in the set and it is intact:
# ONE TUNE PLAYED TWICE. The court states it — bright, dotted, pleased with
# itself. Then the beast plays the SAME tune with every note that reached for
# the fifth, the second or the leading note bent a half step flat, two octaves
# down on a distorted saw. `beast_bars` is still literally built by mapping over
# `court_bars`, and the court tune is not altered by one note in this draft —
# which means the beast tune is not either, automatically. That is the point of
# writing it that way, and it is why this draft can leave the tune alone
# entirely and still be a revision.
#
# Draft 3 changes four things. Tempo, key, the court tune, the bend, the
# harpsichord's part, the 3+3+2 limp, the wings and the form are all untouched.
#
# WHAT THE SHIPPED WAV MEASURES — AND WHAT THAT CAN AND CANNOT TELL US
#   Per-bar RMS across the whole cycle at the in-game gain (-7 dB, the value
#   BixbyBeastScript.gd actually sets):
#     -18.8 -18.1 -18.2 -18.1 -18.0 -18.2 -18.2 -17.8 | -18.1 -18.6 -18.6
#     -18.5 -18.4 -17.9 -20.5 -18.4
#   The entire piece lives inside 2.7 dB, and band by band, court (bars 2-8)
#   against beast (bars 9-14):
#     20-40 Hz   -41 -> -20   (+21)
#     40-80 Hz   -19 -> -27   (-8)
#     1.25-2.5k  -46 -> -42   (+4)
#     5-10k      -56 -> -46   (+10)
#   Read this carefully, because it is not the piece: with five loops pinned to
#   bar 0, everything that changes between the two halves of that recording is
#   liam_drums, which is the one loop that ticks :bar itself. The +21 dB in
#   20-40 Hz is bd_boom moving from rate 0.7 to rate 0.5, and the -8 dB in
#   40-80 Hz is the same kick vacating that band on its way down. The walking
#   bass and the harpsichord play identically across all sixteen bars, which is
#   exactly what the measurement shows.
#   So the honest summary is: the shipped file is a drum arrangement with a
#   court on top, and the reason the dragon is no louder than the throne is that
#   there is no dragon. What the measurement DOES establish, and what change 1
#   below acts on, is where the kit puts its weight — and that the band the
#   beast is about to arrive in is already the thinnest part of the mix.
#
# WHAT CHANGED, AND WHY
#
# 1. THE BEAST BASS GETS A FUNDAMENTAL.
#    READ FROM THE SCORE, NOT MEASURED — it cannot be measured, because the
#    beast bass has never played. Draft 2 runs it at
#    `cutoff: 82 + (s % 4 == 0 ? 18 : 0)`, so the ACCENTED sixteenths — the ones
#    carrying the weight — get cutoff 100, the brightest notes in the line.
#    tb303's cutoff is in MIDI note numbers, so that is 2.6 kHz, with res 0.88
#    putting a resonant peak up there and a distortion stage on top. There is no
#    fundamental left; it is a buzz where a floor should be. And it is about to
#    arrive into the emptiest part of the mix: 40-80 Hz in bars 9-16 of the
#    shipped file measures -24 to -30 dB, because the kit's kick has moved down
#    to rate 0.5 and left that band. The beast's first appearance should not be
#    the moment the bottom falls out.
#    Inverted: the accents now get a LOW cutoff, a lower resonance and a longer
#    note, so they land with weight, and the fifteen other sixteenths keep the
#    high cutoff and all the buzz. Same notes, same rhythm, same offsets, same
#    synth, same distortion. A dragon should be felt on the beat and heard
#    between them, which is the other way round from how draft 2 had it.
#
# 2. THE BEAST'S TUNE STOPS BEING PLAYED BY THE BEAST'S BASS.
#    `beast` is `court` dropped 24 semitones, so its main line starts on G2 —
#    98 Hz. The beast bass is rooted on g1 and its offset pattern includes +12,
#    which is also G2. The tune and the floor are on the same pitch, in the same
#    octave, on the same sixteenths. That is the same fault Eric's draft 2 had
#    between its chant and its shields, and it has the same consequence: the
#    "new voice" is not a new voice, it just makes one band louder. Again this
#    is read from the score rather than heard: a narrowband probe at G2 on the
#    shipped file reads -32.5 dBFS over bars 9-14 and -32.5 dBFS over the rest
#    of the piece, which at first looked like proof of the collision and is in
#    fact proof of the silence — neither voice is there, so of course the two
#    halves match to a tenth of a decibel. The collision is real but it is a
#    fact about the notes, not about the recording, and it should be re-measured
#    the first time this piece is rendered whole.
#    The drop is UNCHANGED: `pitch - 24` is still `pitch - 24`, the derivation
#    is untouched and the tune is still two octaves down. What moved is the
#    balance between the lead's own two octaves. Draft 2 had the G2 line at
#    amp 0.62 and its G3 doubling at 0.3; now the G3 carries the tune and the
#    G2 is the reinforcement underneath it, low-passed so it is felt rather than
#    heard. The beast is in the same place, growling in the register where
#    Liam's mix has room (160-315 Hz sits at -30 to -38) instead of wrestling
#    its own bass for 98 Hz.
#
# 3. THE PULL-UP ACTUALLY PULLS UP.
#    Bars 15-16 are THE ROAR, and draft 2's comment claims "every other voice is
#    written to drop away, so this is the only thing left". It is not true:
#    liam_bass branches on `bar >= 8`, so it keeps hammering sixteenths straight
#    through the pull-up. Measured, bar 15 is already the quietest bar in the
#    piece (-20.5 dB against an -18.3 average), so the arrangement is half
#    committing to a gesture and then refusing to finish it. The bass now rests
#    for the pull-up bar and slams back in on the landing. One bar with nothing
#    underneath a rising siren is worth more than any number of added notes, and
#    the landing is the window the player gets to hit him — it should arrive out
#    of space, not out of more of the same.
#
# 4. EVERY LOOP NOW OWNS ITS OWN BAR COUNTER. This is the one that matters, and
#    it is the reason the other three are worth making at all — without it none
#    of them can be heard. See the top of this file for the cost: five of six
#    voices pinned to bar 0, the beast tune never sounded, the harpsichord
#    playing double. liam_bass, liam_court, liam_theme, liam_wings and liam_roar
#    each tick their own key now (:bass, :hc, :tune, :wing, :roar), which is the
#    fix Eric's draft 3 uses.
#    It is worth being exact about the failure mode, because "race" is the
#    intuitive guess and it is wrong — I made it myself. There is no window, no
#    interleaving, nothing timing-dependent, nothing that varies between runs.
#    look() on a key the calling thread has never ticked returns a flat 0 by
#    construction, so `bar >= 8` is not occasionally false, it is never true.
#    Deterministic total failure, which is at least trivially catchable by
#    running the file — scratchpad/check_fmwo.rb runs every loop twice, once as
#    Sonic Pi really behaves and once as the comments intend, and fails the file
#    when the two performances differ.
#    While fixing it, the tune loop was regrouped bar by bar. Draft 2 truncated
#    the beast to six bars with `beast.take_while { |_, d| (left -= d) >= 0 }`
#    and a comment claiming that editing the tune could not desync it. That is
#    only true while some note happens to land exactly on beat 24: give bar 6 a
#    note that straddles the boundary and the loop sleeps 23.5 beats and the
#    whole piece walks off the grid. Writing the tune as bars makes "the first
#    six bars" exact by construction, and makes the bar arithmetic checkable.
#
# WHAT WAS DELIBERATELY LEFT ALONE
#   144 bpm. G. THE COURT TUNE, note for note — and therefore the beast tune,
#   note for note, because it is derived and nothing derived was touched. The
#   bend list [D, A, F#] and the two-octave drop. The harpsichord, including the
#   fact that it is the only voice that does not survive the swallow. The
#   3+3+2 limp. The wings and the fire breath. The roar's synths and its
#   landing. bd_boom at rate 0.5 in the beast half — it is inaudible on small
#   speakers but it is right on anything with a woofer, and removing it would
#   confound the A/B; change 1 adds the audible weight rather than moving that.
#   Also left alone: the loop seam, but with an honest caveat about why. On the
#   piece as actually recorded the seam is healthy — bar 16 -18.4 dB into bar 1
#   -18.8 dB, and +2.9 dB comparing the last and first 200 ms, so it rises into
#   the loop rather than deflating. But that seam is the harpsichord handing
#   over to the harpsichord, because the roar never played. What bars 15-16 will
#   actually sound like against bar 1 is unknown until this file is rendered.
#   The shape on paper is good — the landing is the heaviest moment in the
#   piece and bar 1 is the lightest, which is a real drop — so this is the first
#   thing to listen for and the most likely place a fifth change will be needed.
#   I am not going to pre-emptively rewrite a bar I have never heard; that is
#   exactly the mistake the measurements caught me making on Jordan.
#
# ONE THING I FOUND AND DID NOT FIX HERE, BECAUSE IT IS NOT A COMPOSITION BUG
#   The shipped liam_theme.wav was cut from the FIRST cycle of the take, and in
#   the first cycle the `sync:`ed loops have not started yet — a live_loop that
#   syncs to another waits for that loop's NEXT cue, a bar later. Comparing
#   cycles of liam_theme_raw.wav directly:
#     cycle 1  bar 1 is -14.4 dB against the mean of bars 2-8
#     cycle 2  bar 1 is  -0.7 dB against the mean of bars 2-8
#   Bar 1 of the shipped loop is nearly empty — the harpsichord shows zero
#   onsets there and sixteen per bar everywhere else — and with loop_mode=2 that
#   hole now repeats forever. The fix is in the pipeline, not the notes: cut a
#   LATER cycle. It is worth more than anything else in this file.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run at least THREE times
# through the 16 bars, hit Rec again, and cut a middle cycle. The cycle is
# unchanged at 16 bars x 4 beats / 144 bpm = 26.6667 s, so:
#   python cut_loop.py liam_theme_v3_raw.wav 144 --out <somewhere>/liam_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B.
#
# 144 bpm, G. 16-bar cycle:
#   Bars 1-8    THE COURT — G minor with its proper leading note: Gm D Cm Gm
#                           Eb D Gm D, a processional you could carry a chair to
#   Bars 9-14   THE BEAST — the same G with the fifth, the second and the
#                           leading note all bent flat (G Ab Bb C Db Eb F).
#                           Chords go G dim / Db / Ab; the gait limps 3+3+2.
#   Bars 15-16  THE ROAR  — he pulls up into nothing, and lands. This is
#                           roughly where his recovery window opens.

use_bpm 144

# ------------------------------------------------------------------ the tune
# ONE TUNE, TWICE. Written out one bar at a time so the arithmetic is visible
# and so "the first six bars" is exact rather than arrived at by subtraction.
# [note, beats]. Every bar must sum to 4.
define :court_bars do
  [
    [[:g4, 1.5], [:a4, 0.5], [:bb4, 1], [:d5, 1]],    # 1 Gm — carried in
    [[:d5, 1.5], [:c5, 0.5], [:bb4, 1], [:a4, 1]],    # 2 D  — and set down
    [[:c5, 1.5], [:d5, 0.5], [:eb5, 1], [:g5, 1]],    # 3 Cm — he stands up
    [[:fs5, 1], [:g5, 1], [:d5, 2]],                  # 4 Gm — the leading note
    [[:eb5, 1.5], [:d5, 0.5], [:c5, 1], [:bb4, 1]],   # 5 Eb — pleased with itself
    [[:a4, 1], [:bb4, 1], [:cs5, 2]],                 # 6 D  — the flourish
    [[:g5, 1.5], [:fs5, 0.5], [:g5, 1], [:bb5, 1]],   # 7 Gm — the last slap
    [[:a5, 2], [:d5, 2]]                              # 8 D  — Bixby has had enough
  ]
end

# THE BEND, which is the whole piece: three pitch classes fall a half step once
# Bixby swallows him — D (the fifth), A (the second) and F# (the leading note).
# Everything else is untouched, which is why the beast is recognisably the same
# tune and completely wrong.
#
# Derived, not transcribed. Change a note in court_bars above and the beast
# follows automatically; that is the joke in the code as well as in the music,
# and it is the one thing in this file that must never be hand-written out.
define :beast_bars do
  bent = [2, 9, 6]                                    # D, A, F#
  court_bars.map do |phrase|
    phrase.map do |n, dur|
      pitch = note(n)
      pitch -= 1 if bent.include?(pitch % 12)
      [pitch - 24, dur]                               # two octaves down
    end
  end
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
court_bars.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "liam_theme_v3: COURT BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# ------------------------------------------------------------------- drums
# Court: a kick on 1 and 3 with the dotted snap that courts have always used to
# sound expensive. Beast: nothing lands square any more — the kick limps three,
# three, two, and the toms come down on the last of it. Unchanged from draft 2.
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
#
# CHANGED (1): the accents are no longer the brightest notes in the line. Draft
# 2 gave `s % 4 == 0` a cutoff of 100 — in MIDI note numbers, 2.6 kHz — so every
# accented sixteenth was a resonant buzz with no fundamental, and the band a
# listener actually hears bass in measured 8 dB QUIETER in the beast half than
# in the court half. Now the accent is low, long and less resonant, and the
# other fifteen sixteenths keep all the buzz.
# CHANGED (3): the bass rests for the pull-up.
# 16 x 0.25 = 4 beats in the beast; 1.5 + 0.5 + 1 + 1 = 4 in the court.
live_loop :liam_bass, sync: :liam_drums do
  bar = tick(:bass) % 16
  if bar == 14
    # THE PULL-UP. Nothing underneath it. The roar has this bar.
    sleep 4
  elsif bar >= 8
    root = note([:g1, :g1, :db2, :db2, :ab1, :ab1, :g1, :g1][bar % 8])
    use_synth :tb303
    with_fx :distortion, distort: 0.45, mix: 0.55 do
      [0, 0, 12, 0, 6, 0, 12, 0, 0, 0, 12, 6, 0, 11, 10, 0].each_with_index do |off, s|
        accent = (s % 4).zero?
        play root + off,
          amp: accent ? 0.95 : 0.58,
          attack: 0.004,
          sustain: accent ? 0.13 : 0.05,
          release: accent ? 0.2 : 0.13,
          res: accent ? 0.7 : 0.88,
          cutoff: accent ? 68 : 92
        sleep 0.25
      end
    end
  else
    root = note([:g2, :d2, :c2, :g2, :eb2, :d2, :g2, :d2][bar])
    use_synth :tri
    with_fx :lpf, cutoff: 88 do
      [[0, 1.5], [7, 0.5], [12, 1], [7, 1]].each do |off, dur|
        play root + off, amp: 0.8, attack: 0.01, release: dur * 0.85
        sleep dur
      end
    end
  end
end

# -------------------------------------------------------------- harpsichord
# The court, and the only voice that does not survive the swallow. Sixteenths
# that fill every gap, because that is what a harpsichord is for. From bar 9 it
# is gone — there is nothing left to be polite about.
# 16 x 0.25 = 4 beats.
live_loop :liam_court, sync: :liam_drums do
  bar = tick(:hc) % 16
  if bar >= 8
    sleep 4
  else
    ch = [chord(:g4, :minor), chord(:d4, :major), chord(:c4, :minor), chord(:g4, :minor),
          chord(:eb4, :major), chord(:d4, :major), chord(:g4, :minor), chord(:d4, :major)][bar]
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
# ONE TUNE, TWICE. The court states it on a blade; the beast plays the derived
# version on a distorted saw, two octaves down, for six bars — he does not get
# to finish the sentence, he roars.
#
# CHANGED (2): the balance between the lead's two octaves. The drop is still
# exactly `pitch - 24`; what changed is which of the lead's own octaves carries
# the tune. Draft 2 put the melody on the G2 line at amp 0.62 and its octave
# doubling at 0.3, and the G2 line is precisely where the beast bass already
# plays (root g1, offset +12). Same pitch, same octave, same sixteenths: a
# narrowband probe at G2 measures -32.5 dBFS in the beast half and -32.5 dBFS
# everywhere else, which is to say dropping the tune two octaves added nothing
# audible at all. The upper octave now carries and the lower one reinforces
# under a low filter — felt, not fought for.
live_loop :liam_theme, sync: :liam_drums do
  bar = tick(:tune) % 16
  if bar >= 14
    sleep 4                                   # bars 15-16 belong to the roar
  elsif bar >= 8
    phrase = beast_bars[bar - 8]              # bars 9-14 = the first six bars
    use_synth :dsaw
    with_fx :distortion, distort: 0.4, mix: 0.5 do
      with_fx :reverb, room: 0.8, mix: 0.3 do
        phrase.each do |n, dur|
          # The tune, up where there is room for it.
          play n + 12, amp: 0.66, attack: 0.01, sustain: dur * 0.5,
            release: 0.25, cutoff: 100, detune: 0.2
          # And the two-octaves-down line underneath, felt rather than heard,
          # so it stops competing with its own bass for 98 Hz.
          play n, amp: 0.34, attack: 0.01, sustain: dur * 0.55,
            release: 0.3, cutoff: 76, detune: 0.22
          sleep dur
        end
      end
    end
  else
    use_synth :blade
    with_fx :reverb, room: 0.6, mix: 0.25 do
      court_bars[bar].each do |n, dur|
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
# Unchanged from draft 2 apart from deriving its own bar.
# 2 x (1 + 1) = 4 beats.
live_loop :liam_wings, sync: :liam_drums do
  bar = tick(:wing) % 16
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
# BARS 15-16. He pulls up, hangs there with nothing underneath him, and lands —
# and the landing is the window you get to hit him. Now that the bass rests for
# bar 15 (change 3) the claim this loop's comment has always made is finally
# true: this really is the only thing left.
# 4 beats in the pull-up; 2 + 2 = 4 in the landing.
live_loop :liam_roar, sync: :liam_drums do
  bar = tick(:roar) % 16
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
