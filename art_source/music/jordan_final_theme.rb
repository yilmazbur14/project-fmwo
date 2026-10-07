# JORDAN, ASCENDED — "Welcome to My World"
# Original music for Project FMWO, written for Sonic Pi 5.x.
#
# The last fight. Jordan lost, called it cheating, deleted everyone else from his
# server, and came apart into what he always thought he was: a demon god in
# obsidian and lava, wings out, hanging in the void over blue runes. This is the
# fight with him. It has to be the biggest thing in the game, so it is a
# Cave-shooter last boss: fast, relentless, and dread and triumph at once.
#
# IT IS BUILT ON HIS PHRASE. In his first fight a music box plays
#     C  Eb  Gb  Eb  .  Ab  Gb  .
# over and over. It reaches for the fifth and lands on the flat fifth every
# time: the broken tooth. Here that tritone is the devil's interval and it is
# everywhere.
#   - The intro sings the phrase as a hymn, on the organ and the choir, while
#     the music box plays the real thing one last time and warps into nothing.
#   - The riff that opens the fight climbs Eb, F, Gb, and falls back. It never
#     reaches G until bar 8, when everything does.
#   - The breakdown chops the phrase into a distorted voice.
#   - The last four bars before the loop shout it, harmonised as a diminished
#     chord and then a German sixth, whose Gb finally falls to G and throws the
#     fight back to the top.
# The tune is the thing the music box never could do. It leaps a fourth and
# climbs PAST the fifth, to the octave and beyond. The second time round it does
# it a whole tone higher.
#
# THE STYLE, taken from the reference in words only, never its notes: a Cave
# last-boss theme at about 185 bpm; distorted vocals over a hard techno beat;
# choir "ahhs" over the electronics; a synth playing the electric guitar;
# orchestral hits; and one stretch where the rhythm changes and the electronic
# beat takes over, for sinister urgency. Nothing here is transcribed from it.
#
# 185 bpm, 4/4. C minor, with D minor for the climax.
#
# THE INTRO — 8 bars, played ONCE (10.378 s). It stands alone under his line.
#   1-4  THE ASCENSION  the hit, then his phrase as a hymn in half notes over
#                       Cm | Ab7 | Fm | Cdim7, the box playing it for real one
#                       last time and warping away.
#   5-6  THE LINE       Cm | Ab. The room for "Welcome to my world, Burak.": a
#                       low choir, a heartbeat, tremolo strings, nothing else.
#   7-8  THE WIND-UP    Db | G. The kit rolls in, the guitar and bass wind up,
#                       and the riser lands on the loop's first downbeat.
#
# THE LOOP — 64 bars (83.027 s), repeated for the whole fight.
#   1-8    A  THE VOID    the riff on a C pedal, the choir, the voice.
#                         Cm Cm Db/C Cm | Cm Cm Ab/C G
#   9-24   B  THE HYMN    the tune. Cm Bb Ab G | Cm Bb Ab G |
#                         Ab Bb Cm Cm7 | Ab Bb Gsus4 G
#   25-32  C  THE GLITCH  the rhythm changes. A breakbeat, a wobble bass, the
#                         phrase chopped in a distorted voice, the box haunting.
#                         Cdim Db/C Cdim Cdim7 | Ab Adim7 Bb Bdim7
#   33-40  D  THE ASCENT  the tune's first leap, one step higher each bar, then
#                         the build. Cm Ab Bb Cm | Ab Ab Bb A7
#   41-56  E  THE LIFT    the tune a whole tone up, in D minor, with the choir
#                         answering it and the organ under everything.
#   57-64  F  THE FALL    Dm Bb Ab G | Cdim Ab7 Db G. His phrase, shouted, and
#                         the fill back to the top. Bars 63-64 are the intro's
#                         bars 7-8, so the loop starts the same way both times.
#
# HOW TO RECORD: never through the GUI. See music-recording-pipeline.
# The intro and the loop come out of ONE take.
#   python record_theme.py jordan_final_theme.rb 185 --bars 64 --cycles 2.35 --out <s>/jf_raw.wav
#   python measure_take.py <s>/jf_raw.wav 185 --bars 64
#   python cut_loop.py <s>/jf_raw.wav 185 --bars 64 --offset 10.378378 --out <s>/jordan_final_theme.wav
#   python cut_intro.py <s>/jf_raw.wav 185 --out <s>/jordan_final_intro.wav
# The cut point is the first downbeat plus 8 bars (32 beats x 60 / 185 =
# 10.378378 s). cut_loop.py's --offset skips the intro, and its default --cycle 1
# then takes the loop's second pass. cut_intro.py takes the intro and blends its
# last 12 ms into the frames just before the loop's first frame. So intro -> loop
# is continuous in the game, just as the loop seam is.
# One loop is 64 bars x 4 beats / 185 bpm = 83.027 s. The take opens on a four-bar
# silent lead-in (see the clock), so 2.35 cycles covers the lead-in, the intro,
# two full laps and a tail. Read PERFORMANCE before adding anything busy.
#
# LEVEL, as recorded 2026-09-28 (K-weighted and ungated, as the other themes were
# measured): the loop is -16.0 LUFS, RMS -18.3 dBFS, peak -1.2 dBFS; the intro is
# -16.1 LUFS, peak -1.4 dBFS. Nothing reaches Sonic Pi's limiter. That is Matt's
# file level (-16.4 LUFS, THEME_DB -5). In game, about -6 dB puts it with the
# others: -5.5 matches them full-band, and -6.5 matches them above 100 Hz, which
# is what a laptop or phone plays and where this mix is denser than theirs.

use_bpm 185

# -------------------------------------------------------------------- mixer
# The balance, in dB, and it is measured, not guessed: every voice was recorded
# on its own and these are what the stems said it takes for the tune to lead, the
# drums to hit as hard as the tune, the guitar to sit three dB under them, and
# the loop to land at about -16 LUFS with its peaks under -1 dBFS (so Sonic Pi's
# limiter never touches it). Every loop sits inside a :level fx and sets it once
# a bar to fader + trim, so a change here is a clean gain applied after all of
# that voice's own distortion.
define :jf_faders do
  { drums: -1.5, bass: -1.5, gtr: -6.3, arps: 13.0, choir: 2.8, chant: 4.2,
    organ: 12.1, strings: 20.1, lead: -3.2, voice: -11.1, hits: -1.5, box: 7.2 }
end

# Where a voice sits differently in one part of the piece, also in dB. The
# synthetic choir needs the most help: a formant filter's gain swings by 15 dB
# with the vowel and the register, so each part of it is set from its own
# measurement.
define :jf_trims do
  { voice: { i1: 1.0 },
    bass:  { c: -7.3, f_motif: -2.0 },
    drums: { c: 2.0, f_motif: -3.5 },
    gtr:   { f_motif: -2.0 },
    choir: { i2: -3.0, f_motif: -3.0 },
    chant: { i1: 4.0, i2: 4.0, a: 2.0, a_hit: 2.0, d_hi: 13.0, e: -11.4, e_hit: -11.4,
             f_motif: -2.0 },
    hits:  { a_hit: 2.0, f_motif: -3.0 },
    box:   { c: 3.3 } }
end

# The part of the piece a bar belongs to, for the trims.
define :jf_section do |t|
  part, bb = jf_pos(t)
  case part
  when :intro then [:i1, :i2, :i2, :i2, :i5, :i5, :i7, :i7][t]
  when :a then (bb == 0 || bb == 4) ? :a_hit : :a
  when :d then bb < 36 ? :d_lo : :d_hi
  when :e then bb == 40 ? :e_hit : :e
  when :f then bb < 60 ? :f : (bb < 62 ? :f_motif : :f_end)
  else part
  end
end

define :jf_gain do |voice, t|
  db = jf_faders[voice] + (jf_trims.fetch(voice, {})[jf_section(t)] || 0)
  10 ** (db / 20.0)
end

# ---------------------------------------------------------------------- map
# Every loop counts its own bars (tick), from the first bar it plays. t = 0 is
# intro bar 1. The intro plays once, and after it the 64-bar body repeats.
# Returns [part, bar], where bar is the intro bar (0-7) or the loop bar (0-63).
define :jf_pos do |t|
  if t < 8
    [:intro, t]
  else
    bb = (t - 8) % 64
    part = if bb < 8 then :a
           elsif bb < 24 then :b
           elsif bb < 32 then :c
           elsif bb < 40 then :d
           elsif bb < 56 then :e
           else :f
           end
    [part, bb]
  end
end

define :jf_row do |t|
  jf_harmony[t < 8 ? t : 8 + (t - 8) % 64]
end

# ------------------------------------------------------------------ harmony
# One row a bar: [bass root, pad voicing, choir dyads]. A dyad is the LOWER note
# of a minor third, because that is what :ambi_choir sings (see jf_choir_ref):
# on a minor chord it sits on the root, on a major chord on the third.
define :jf_harmony do
  [
    # ---- INTRO
    [:c2,  [:c4, :eb4, :c5],        [:c4]],        # i1 Cm     the hit (no fifth: the
                                                   #    box's Gb has room to be wrong)
    [:ab1, [:ab3, :c4, :eb4, :gb4], [:c4, :eb4]],  # i2 Ab7    the German sixth
    [:f1,  [:f3, :ab3, :c4],        [:f3]],        # i3 Fm
    [:c2,  [:a3, :c4, :eb4, :gb4],  [:c4, :eb4]],  # i4 Cdim7
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # i5 Cm     "Welcome to my
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # i6 Ab      world, Burak."
    [:db2, [:db4, :f4, :ab4],       [:f4]],        # i7 Db
    [:g1,  [:d4, :g4, :b4],         [:b3]],        # i8 G
    # ---- A: THE VOID
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 1  Cm
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 2  Cm
    [:c2,  [:db4, :f4, :ab4],       [:f4]],        # 3  Db/C
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 4  Cm
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 5  Cm
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 6  Cm
    [:c2,  [:c4, :eb4, :ab4],       [:c4]],        # 7  Ab/C
    [:g1,  [:d4, :g4, :b4],         [:b3]],        # 8  G
    # ---- B: THE HYMN
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 9  Cm
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 10 Bb
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 11 Ab
    [:g1,  [:d4, :g4, :b4],         [:b3]],        # 12 G
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 13 Cm
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 14 Bb
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 15 Ab
    [:g1,  [:d4, :g4, :b4],         [:b3]],        # 16 G
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 17 Ab
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 18 Bb
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 19 Cm
    [:c2,  [:c4, :eb4, :g4, :bb4],  [:c4]],        # 20 Cm7
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 21 Ab
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 22 Bb
    [:g1,  [:d4, :g4, :c5],         []],           # 23 Gsus4
    [:g1,  [:d4, :g4, :b4],         [:b3]],        # 24 G
    # ---- C: THE GLITCH
    [:c2,  [:c4, :eb4, :gb4],       [:c4, :eb4]],  # 25 Cdim   the broken chord
    [:c2,  [:db4, :f4, :ab4],       [:f4]],        # 26 Db/C
    [:c2,  [:c4, :eb4, :gb4],       [:c4, :eb4]],  # 27 Cdim
    [:c2,  [:a3, :c4, :eb4, :gb4],  [:c4, :eb4]],  # 28 Cdim7
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 29 Ab
    [:a1,  [:a3, :c4, :eb4, :gb4],  [:c4, :eb4]],  # 30 Adim7
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 31 Bb
    [:b1,  [:b3, :d4, :f4, :ab4],   [:d4, :f4]],   # 32 Bdim7
    # ---- D: THE ASCENT
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 33 Cm
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 34 Ab
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 35 Bb
    [:c2,  [:c4, :eb4, :g4],        [:c4]],        # 36 Cm
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 37 Ab
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 38 Ab
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 39 Bb
    [:a1,  [:cs4, :e4, :g4, :a4],   [:cs4]],       # 40 A7     the pivot
    # ---- E: THE LIFT, in D minor
    [:d2,  [:d4, :f4, :a4],         [:d4]],        # 41 Dm
    [:c2,  [:e4, :g4, :c5],         [:e4]],        # 42 C
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 43 Bb
    [:a1,  [:e4, :a4, :cs5],        [:cs4]],       # 44 A
    [:d2,  [:d4, :f4, :a4],         [:d4]],        # 45 Dm
    [:c2,  [:e4, :g4, :c5],         [:e4]],        # 46 C
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 47 Bb
    [:a1,  [:e4, :a4, :cs5],        [:cs4]],       # 48 A
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 49 Bb
    [:c2,  [:e4, :g4, :c5],         [:e4]],        # 50 C
    [:d2,  [:d4, :f4, :a4],         [:d4]],        # 51 Dm
    [:d2,  [:d4, :f4, :a4, :c5],    [:d4]],        # 52 Dm7
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 53 Bb
    [:c2,  [:e4, :g4, :c5],         [:e4]],        # 54 C
    [:a1,  [:e4, :a4, :d5],         []],           # 55 Asus4
    [:a1,  [:e4, :a4, :cs5],        [:cs4]],       # 56 A
    # ---- F: THE FALL
    [:d2,  [:d4, :f4, :a4],         [:d4]],        # 57 Dm
    [:bb1, [:d4, :f4, :bb4],        [:d4]],        # 58 Bb
    [:ab1, [:c4, :eb4, :ab4],       [:c4]],        # 59 Ab
    [:g1,  [:d4, :g4, :b4],         [:b3]],        # 60 G
    [:c2,  [:c4, :eb4, :gb4],       [:c4, :eb4]],  # 61 Cdim   his phrase,
    [:ab1, [:c4, :eb4, :gb4, :ab4], [:c4, :eb4]],  # 62 Ab7    shouted
    [:db2, [:db4, :f4, :ab4],       [:f4]],        # 63 Db
    [:g1,  [:d4, :f4, :g4, :b4],    [:b3]]         # 64 G7
  ]
end

# ------------------------------------------------------------ his phrase
# The music box, as jordan_theme plays it: eight eighth notes, nil for a worn
# tooth.
define :jf_box_phrase do
  [:c6, :eb6, :gb6, :eb6, nil, :ab5, :gb5, nil]
end

# The same phrase whole, as the god sings it, with the worn teeth filled with C.
define :jf_hymn do
  [:c5, :eb5, :gb5, :eb5, :c5, :ab4, :gb4, :c5]
end

# --------------------------------------------------------------------- tune
# [note, beats], with nil for a rest, keyed by loop bar (0-63). A bar that isn't
# here has no tune. Every bar sums to 4; the check below says so if one doesn't.
# The tune leaps G up to C, climbs past the fifth, and cries on the flat sixth.
# Its middle is a climbing sequence in 3+3+2, and it comes down in steps onto the
# leading note, B, which the breakdown then refuses to resolve.
define :jf_tune do
  {
    7  => [[nil, 3], [:g5, 0.5], [:b5, 0.5]],                               # 8 pickup
    # ---- THE HYMN
    8  => [[:c6, 2.5], [:d6, 0.5], [:eb6, 0.5], [:d6, 0.5]],                # 9  Cm
    9  => [[:c6, 1], [:bb5, 1], [:f5, 2]],                                  # 10 Bb
    10 => [[:ab5, 0.5], [:bb5, 0.5], [:c6, 2], [:eb6, 1]],                  # 11 Ab
    11 => [[:d6, 2], [:c6, 0.5], [:b5, 0.5], [:g5, 1]],                     # 12 G
    12 => [[:c6, 2.5], [:d6, 0.5], [:eb6, 0.5], [:f6, 0.5]],                # 13 Cm
    13 => [[:g6, 1.5], [:f6, 1.5], [:d6, 1]],                               # 14 Bb
    14 => [[:eb6, 1], [:c6, 1], [:ab6, 2]],                                 # 15 Ab
    15 => [[:g6, 2], [:f6, 0.25], [:eb6, 0.25], [:d6, 0.25], [:c6, 0.25],
           [:b5, 0.5], [:d6, 0.5]],                                         # 16 G
    16 => [[:eb6, 1.5], [:c6, 1.5], [:eb6, 1]],                             # 17 Ab
    17 => [[:f6, 1.5], [:d6, 1.5], [:f6, 1]],                               # 18 Bb
    18 => [[:g6, 1.5], [:eb6, 1.5], [:g6, 1]],                              # 19 Cm
    19 => [[:bb6, 2], [:ab6, 1], [:g6, 1]],                                 # 20 Cm7
    20 => [[:ab6, 2], [:g6, 1], [:f6, 1]],                                  # 21 Ab
    21 => [[:f6, 2], [:eb6, 1], [:d6, 1]],                                  # 22 Bb
    22 => [[:c6, 2], [:d6, 1], [:eb6, 1]],                                  # 23 Gsus4
    23 => [[:d6, 1], [:b5, 3]],                                             # 24 G
    # ---- THE ASCENT: the leap, a step higher each bar, then a held cry
    32 => [[:g5, 1], [:c6, 3]],                                             # 33 Cm
    33 => [[:ab5, 1], [:c6, 1], [:eb6, 2]],                                 # 34 Ab
    34 => [[:bb5, 1], [:d6, 1], [:f6, 2]],                                  # 35 Bb
    35 => [[:c6, 1], [:eb6, 1], [:g6, 2]],                                  # 36 Cm
    36 => [[:ab6, 4]],                                                      # 37 Ab
    37 => [[:ab6, 2], [:g6, 1], [:eb6, 1]],                                 # 38 Ab
    38 => [[:f6, 2], [:d6, 1], [:bb5, 1]],                                  # 39 Bb
    39 => [[:e6, 2], [nil, 1], [:a5, 0.5], [:cs6, 0.5]],                    # 40 A7
    # ---- THE LIFT: the hymn a whole tone up
    40 => [[:d6, 2.5], [:e6, 0.5], [:f6, 0.5], [:e6, 0.5]],                 # 41 Dm
    41 => [[:d6, 1], [:c6, 1], [:g5, 2]],                                   # 42 C
    42 => [[:bb5, 0.5], [:c6, 0.5], [:d6, 2], [:f6, 1]],                    # 43 Bb
    43 => [[:e6, 2], [:d6, 0.5], [:cs6, 0.5], [:a5, 1]],                    # 44 A
    44 => [[:d6, 2.5], [:e6, 0.5], [:f6, 0.5], [:g6, 0.5]],                 # 45 Dm
    45 => [[:a6, 1.5], [:g6, 1.5], [:e6, 1]],                               # 46 C
    46 => [[:f6, 1], [:d6, 1], [:bb6, 2]],                                  # 47 Bb
    47 => [[:a6, 2], [:g6, 0.25], [:f6, 0.25], [:e6, 0.25], [:d6, 0.25],
           [:cs6, 0.5], [:e6, 0.5]],                                        # 48 A
    48 => [[:f6, 1.5], [:d6, 1.5], [:f6, 1]],                               # 49 Bb
    49 => [[:g6, 1.5], [:e6, 1.5], [:g6, 1]],                               # 50 C
    50 => [[:a6, 1.5], [:f6, 1.5], [:a6, 1]],                               # 51 Dm
    51 => [[:c7, 2], [:bb6, 1], [:a6, 1]],                                  # 52 Dm7
    52 => [[:bb6, 2], [:a6, 1], [:g6, 1]],                                  # 53 Bb
    53 => [[:g6, 2], [:f6, 1], [:e6, 1]],                                   # 54 C
    54 => [[:d6, 2], [:e6, 1], [:f6, 1]],                                   # 55 Asus4
    55 => [[:e6, 1], [:cs6, 3]],                                            # 56 A
    # ---- THE FALL
    56 => [[:d6, 4]],                                                       # 57 Dm
    57 => [[:f6, 2], [:d6, 2]],                                             # 58 Bb
    58 => [[:eb6, 2], [:c6, 2]],                                            # 59 Ab
    59 => [[:d6, 2], [:b5, 2]],                                             # 60 G
    60 => [[:c6, 1], [:eb6, 1], [:gb6, 1], [:eb6, 1]],                      # 61 his phrase
    61 => [[:c6, 1], [:ab5, 1], [:gb5, 1], [:c6, 1]],                       # 62
    62 => [[:db6, 2], [:f6, 1], [:ab6, 1]],                                 # 63 Db
    63 => [[:g6, 2], [:f6, 0.5], [:eb6, 0.5], [:d6, 0.5], [:b5, 0.5]]       # 64 G7
  }
end

# The choir's answer to the tune in THE LIFT: long notes that move by step
# against it.
define :jf_counter do
  {
    40 => [[:d5, 4]], 41 => [[:e5, 4]], 42 => [[:f5, 4]], 43 => [[:e5, 4]],
    44 => [[:d5, 4]], 45 => [[:e5, 4]], 46 => [[:f5, 4]], 47 => [[:e5, 2], [:cs5, 2]],
    48 => [[:d5, 4]], 49 => [[:e5, 4]], 50 => [[:f5, 4]], 51 => [[:f5, 4]],
    52 => [[:f5, 2], [:d5, 2]], 53 => [[:e5, 2], [:g5, 2]], 54 => [[:d5, 2], [:e5, 2]],
    55 => [[:cs5, 4]]
  }
end

# Bar-length check. Runs once and prints nothing when every bar is right.
[jf_tune, jf_counter].each do |parts|
  parts.each do |bar, notes|
    total = notes.inject(0.0) { |acc, (_, beats)| acc + beats }
    puts "jordan_final_theme: loop bar #{bar + 1} sums to #{total}, not 4" unless total == 4.0
  end
end

# The riff for A, one row a bar, in semitones above C for each sixteenth. 0 is
# the palm-muted pedal, any other number an accent, and nil a rest. The accents
# all sit off the kick (slots 0, 4, 8 and 12 belong to the kick), which is where
# the rolling bass plays, so the bass states the riff with the guitar. It climbs
# Eb, F, Gb and falls back. Bar 8 is G, and gets its own figure.
define :jf_riff do
  [
    [0, nil, 0, 3, 0, nil, 0, 5, 0, nil, 0, 6, 0, 5, 3, nil],   # 1 Cm
    [0, nil, 0, 3, 0, nil, 0, 5, 0, nil, 0, 6, 0, 6, 5, 3],     # 2 Cm
    [0, nil, 0, 1, 0, nil, 0, 5, 0, nil, 0, 8, 0, 5, 1, nil],   # 3 Db/C
    [0, nil, 0, 3, 0, nil, 0, 5, 0, nil, 0, 6, 0, 6, 5, 3],     # 4 Cm
    [0, nil, 0, 3, 0, nil, 0, 5, 0, nil, 0, 6, 0, 5, 3, nil],   # 5 Cm
    [0, nil, 0, 3, 0, nil, 0, 5, 0, nil, 0, 6, 0, 6, 5, 3],     # 6 Cm
    [0, nil, 0, 3, 0, nil, 0, 8, 0, nil, 0, 7, 0, 8, 7, 5]      # 7 Ab/C
  ]
end

# ------------------------------------------------------------ instruments
# The lower voice of :ambi_choir sings MIDI 72.55 at rate 1, and the upper voice
# a minor third above it. Both were measured off the sample's spectrum (the
# partials sit at 541 Hz and 638 Hz). So rpitch = target - 72.55. Pitched down,
# the choir's formants go down with it, and it sounds like something enormous
# singing. That is the point.
define :jf_choir_ref do
  72.55
end

define :jf_ah do |low, amp, beats, pan|
  sample :ambi_choir, rpitch: note(low) - jf_choir_ref, amp: amp,
    attack: 0.06, sustain: beats * 0.7, release: beats * 0.3, pan: pan
end

# The synthetic choir: :blade, a saw with a real vibrato, which is what a formant
# filter wants. It is played inside jf_chant's `:vowel` fx.
define :jf_voices do |notes, amp, beats|
  notes.each_with_index do |n, i|
    synth :blade, note: n, amp: amp, attack: beats * 0.15, sustain: beats * 0.6,
      release: beats * 0.3, cutoff: 100, vibrato_rate: 5, vibrato_depth: 0.1,
      vibrato_delay: 0.3, vibrato_onset: 0.4, pan: (i - (notes.size - 1) / 2.0) * 0.3
  end
end

# One side of the double-tracked synth guitar: a saw per string, a few cents off
# the other side, into that side's amp rig. `e` is [root, amp, beats, intervals],
# and anything a sixteenth or shorter is palm-muted.
define :jf_guitar_side do |e, pan, cents|
  root, amp, beats, ivs = e
  muted = beats <= 0.26
  ivs.each do |iv|
    synth :dsaw, note: root + iv + cents, amp: amp, attack: 0.003,
      sustain: (muted ? 0.04 : beats * 0.7), release: (muted ? 0.08 : beats * 0.3),
      cutoff: (muted ? 84 : 102), detune: 0.07, pan: pan
  end
end

# The bass: a saw through the 303's filter, clipped short.
define :jf_bass_hit do |n, amp, beats|
  synth :tb303, note: n, amp: amp, attack: 0.004, sustain: beats * 0.35,
    release: beats * 0.45, cutoff_min: 45, cutoff: 86, cutoff_attack: 0.004,
    cutoff_decay: 0.09, cutoff_sustain_level: 0.3, res: 0.22, wave: 0
end

# The rolling bass: nothing on the kick, then the three sixteenths after it.
# `offs` says what each of those three plays, above the root.
define :jf_roll do |root, amp, offs|
  16.times do |s|
    k = s % 4
    jf_bass_hit root + offs[k - 1], amp * (k == 1 ? 1.0 : 0.86), 0.25 if k != 0
    sleep 0.25
  end
end

# A long bass note, with a sine an octave under it.
define :jf_bass_long do |n, amp, beats|
  synth :tb303, note: n, amp: amp, attack: 0.01, sustain: beats * 0.6,
    release: beats * 0.38, cutoff_min: 40, cutoff: 72, cutoff_attack: 0.01,
    cutoff_decay: beats * 0.5, cutoff_sustain_level: 0.5, res: 0.15, wave: 0
  synth :sine, note: note(n) - 12, amp: amp * 0.55, attack: 0.01,
    sustain: beats * 0.6, release: beats * 0.38
end

# The chord tones the arps run over: the bar's voicing and the octave above it,
# the first five, an octave up (C5 and up, for C minor).
define :jf_five do |t|
  v = jf_row(t)[1].map { |n| note(n) + 12 }
  (v + v.map { |n| n + 12 })[0, 5]
end

define :jf_arp_note do |n, amp, cut|
  synth :dsaw, note: n, amp: amp, attack: 0.002, sustain: 0.03, release: 0.13,
    cutoff: cut, detune: 0.1, pan: 0.3
end

# The lead: a detuned saw for the edge, :blade for the singing vibrato on the
# long notes, and a saw an octave under for weight.
define :jf_lead_note do |n, beats, amp|
  # The ear is most sensitive around 2 kHz, so the top of the tune (F6 to C7) is
  # eased back a little per semitone, or its highest notes would jump out.
  over = note(n) - 88
  amp *= 1 - over * 0.03 if over > 0
  synth :dsaw, note: n, amp: amp, attack: 0.012, sustain: beats * 0.72,
    release: 0.28, cutoff: 112, detune: 0.12, pan: -0.1
  synth :blade, note: n, amp: amp * 0.8, attack: 0.02, sustain: beats * 0.72,
    release: 0.32, cutoff: 108, vibrato_rate: 5.5, vibrato_depth: 0.13,
    vibrato_delay: 0.45, vibrato_onset: 0.25, pan: 0.1
  synth :dsaw, note: note(n) - 12, amp: amp * 0.3, attack: 0.015,
    sustain: beats * 0.7, release: 0.22, cutoff: 96, detune: 0.1
end

# The cathedral: a tonewheel organ with nearly every drawbar out and the rotary
# speaker barely turning, in a big room.
define :jf_organ_chord do |notes, amp, beats|
  notes.each do |n|
    synth :organ_tonewheel, note: n, amp: amp, attack: 0.04, sustain: beats - 0.3,
      release: 0.3, bass: 4, quint: 6, fundamental: 8, oct: 8, nazard: 4,
      blockflute: 6, tierce: 2, larigot: 3, sifflute: 4, rs_freq: 0.7,
      rs_pitch_depth: 0.002, rs_amplitude_depth: 0.05, rs_pan_depth: 0.15
  end
end

# An orchestral hit on this bar's chord: a brass stab in two octaves, a low brass
# "bwah", the choir, a timpani, a splash, and for the big ones a cinematic boom.
define :jf_hit do |row, amp, big|
  row[1].each do |n|
    [0, 12].each do |o|
      synth :dsaw, note: note(n) + o, amp: amp * 0.11, attack: 0.004, sustain: 0.2,
        release: 1.0, cutoff: 110, detune: 0.2, pan: (o == 0 ? -0.2 : 0.2)
    end
  end
  synth :tb303, note: note(row[0]) + 12, amp: amp * 0.35, attack: 0.005, sustain: 0.2,
    release: 0.9, cutoff_min: 60, cutoff: 105, cutoff_attack: 0.01, cutoff_decay: 0.4,
    res: 0.1, wave: 0
  row[2].each_with_index { |d, i| jf_ah d, amp * 1.1, 4, (i.even? ? -0.3 : 0.3) }
  sample :drum_tom_lo_hard, rate: 0.5, amp: amp * 0.9
  sample :drum_splash_hard, amp: amp * 0.35, rate: 0.85
  sample :misc_cineboom, amp: amp * 0.6 if big
end

# A noise riser that opens as it swells.
define :jf_riser do |beats, amp|
  r = synth :bnoise, amp: amp, attack: beats * 0.95, sustain: 0, release: beats * 0.05,
    cutoff: 60, cutoff_slide: beats, res: 0.2
  control r, cutoff: 118
end

# A reversed splash, stretched to exactly two bars, so starting it two bars early
# lands its crack on the downbeat.
define :jf_swell do |amp|
  sample :drum_splash_hard, beat_stretch: 8, rate: -1, amp: amp
end

# His voice, as a god: a roar sliding down an octave, with the choir sample under
# it, played into jf_voice's rig (a bass formant and distortion). `ivs` stacks it:
# as he ascends it is root and TRITONE, the broken tooth as a scream; at THE LIFT
# it is root and fifth, a war cry.
define :jf_roar do |top, bottom, beats, amp, ivs|
  ivs.each do |iv|
    v = synth :dsaw, note: note(top) + iv, amp: amp * (iv == 12 ? 0.5 : 1.0),
      attack: 0.1, sustain: beats * 0.55, release: beats * 0.4, detune: 0.3,
      cutoff: 118, note_slide: beats * 0.85
    control v, note: note(bottom) + iv
  end
  sample :ambi_choir, rpitch: note(bottom) - jf_choir_ref, amp: amp * 2.2,
    attack: 0.05, sustain: beats * 0.6, release: beats * 0.4
end

# One chopped syllable, into jf_voice's rig, whose vowel is set just before it.
define :jf_chop do |n, amp|
  synth :dsaw, note: n, amp: amp, attack: 0.005, sustain: 0.12, release: 0.08,
    detune: 0.2, cutoff: 118
  synth :dsaw, note: note(n) + 12, amp: amp * 0.5, attack: 0.005, sustain: 0.1,
    release: 0.08, detune: 0.2, cutoff: 118
end

define :jf_bell do |n, amp|
  synth :pretty_bell, note: n, amp: amp, attack: 0.001, release: 0.6, pan: -0.35
end

# Every sample the piece plays. The clock plays each once, silently, before any
# voice starts: see PERFORMANCE.
define :jf_samples do
  [:bd_haus, :drum_cymbal_closed, :drum_snare_hard, :drum_snare_soft,
   :drum_tom_hi_hard, :drum_tom_mid_hard, :drum_tom_lo_hard, :drum_cymbal_hard,
   :drum_splash_hard, :glitch_perc1, :glitch_perc3, :glitch_perc5, :ambi_choir,
   :misc_cineboom, :bass_drop_c]
end

# -------------------------------------------------------------------- drums
# The whole kit is written ONCE, as a score: for a bar and a sixteenth, a list of
# [instrument, amp]. Three loops read it, and each plays only its own instruments
# (kick and hats; snares and toms; cymbals and percussion), so no single thread
# has to trigger the whole kit. See PERFORMANCE.
define :jf_drum do |name, amp|
  case name
  when :kick
    sample :bd_haus, amp: amp
    synth :sc808_bassdrum, note: 36, amp: amp * 0.3, decay: 0.3
  when :hat then sample :drum_cymbal_closed, amp: amp, pan: 0.22
  when :ohat then synth :sc808_open_hihat, amp: amp, decay: 0.2, pan: 0.25
  when :snare
    sample :drum_snare_hard, amp: amp
    synth :sc808_clap, amp: amp * 0.6
  when :ghost then sample :drum_snare_soft, amp: amp, pan: -0.1
  when :tom_hi then sample :drum_tom_hi_hard, amp: amp
  when :tom_mid then sample :drum_tom_mid_hard, amp: amp
  when :tom_lo then sample :drum_tom_lo_hard, amp: amp
  when :crash
    sample :drum_cymbal_hard, amp: amp, rate: 0.95
    sample :drum_splash_hard, amp: amp * 0.5, rate: 0.9
  when :timp then sample :drum_tom_lo_hard, rate: 0.5, amp: amp
  when :glitch1 then sample :glitch_perc1, amp: amp, pan: 0.3
  when :glitch3 then sample :glitch_perc3, amp: amp, pan: -0.3
  when :glitch5 then sample :glitch_perc5, amp: amp, pan: 0.3
  when :gabber then synth :gabberkick, amp: amp
  end
end

# The fill into a downbeat, shared by the intro's last bar, the ascent's last
# bar, the loop's last bar, and the way into the breakdown and THE FALL: kicks on
# three beats, a snare roll that swells, and the toms down to the one.
define :jf_fill_hits do |s, amp|
  h = []
  h << [:kick, amp] if s == 0 || s == 4 || s == 8
  if s < 12
    h << [:ghost, (0.18 + s * 0.035) * amp]
    h << [:snare, (0.12 + s * 0.035) * amp] if s.even?
  else
    h << [[:tom_hi, :tom_mid, :tom_lo, :tom_lo][s - 12], (0.55 + (s - 12) * 0.1) * amp]
  end
  h
end

# A, B and E: four on the floor, a backbeat, and the hats. His phrase in THE
# FALL is a hammer blow on every quarter.
define :jf_drive_hits do |part, bb, s|
  big = part == :e
  h = []
  h << [:crash, (big ? 0.55 : 0.45)] if s == 0 && [0, 4, 8, 12, 16, 20, 40, 44, 48, 52, 56].include?(bb)
  if bb == 60 || bb == 61
    if s % 4 == 0
      h << [:kick, 1.15]
      h << [:timp, 0.75]
    end
    h << [:crash, 0.4] if s == 0 && bb == 60
    h << [:snare, 0.55] if s == 4 || s == 12
  elsif [23, 55, 63].include?(bb) && s >= 8
    h += jf_fill_hits(s, 1.0)
  elsif [7, 15, 47].include?(bb) && s >= 13
    h << [:kick, 0.9] if s == 13
    h << [[:tom_mid, :tom_lo, :tom_lo][s - 13], 0.6]
  else
    h << [:kick, 1.1] if s % 4 == 0
    h << [:kick, 0.75] if big && s == 14 && bb.odd?
    h << [:snare, 0.6] if s == 4 || s == 12
    h << [:ghost, 0.12] if s == 15 && bb.even? && part != :a
    h << [:ohat, (big ? 0.19 : 0.16)] if s % 4 == 2
    h << [:hat, 0.06] if s.odd?
  end
  h
end

# C: the rhythm changes. The four on the floor stops, a breakbeat takes over,
# and the glitches come forward.
define :jf_break_hits do |bb, s|
  h = []
  if bb == 31
    h << [:kick, 1.0] if s == 0 || s == 10
    h << [:snare, 0.55] if s == 4
    if s >= 8
      h << [:ghost, 0.2 + s * 0.03]
      h << [:snare, 0.2 + (s - 8) * 0.06] if s.even?
    end
    h << [:hat, 0.1] if s < 8 && s.even?
  else
    kicks = bb.even? ? [0, 10] : [0, 3, 10]
    ghosts = bb.even? ? [7, 9, 14] : [6, 11, 15]
    h << [:kick, 1.05] if kicks.include?(s)
    h << [:gabber, 0.25] if s == 0 && (bb == 24 || bb == 28)
    h << [:snare, 0.62] if s == 4 || s == 12
    h << [:ghost, 0.16] if ghosts.include?(s)
    h << [:hat, (s.even? ? 0.11 : 0.05)]
    h << [:ohat, 0.12] if s == 6 && bb.even?
    h << [:glitch1, 0.28] if s == 2
    h << [:glitch3, 0.28] if s == 5
    h << [:glitch5, 0.28] if s == 13
  end
  h
end

# D: the build. The kick comes back, and the snare doubles, doubles and rolls.
define :jf_build_hits do |bb, s|
  if bb == 39
    jf_fill_hits s, 1.0
  else
    h = []
    h << [:kick, 1.05] if s % 4 == 0
    h << [:crash, 0.4] if s == 0 && bb == 32
    case bb
    when 32, 33
      h << [:snare, 0.55] if s == 4 || s == 12
      h << [:hat, 0.09] if s.even?
    when 34, 35
      h << [:snare, 0.55] if s == 4 || s == 12
      h << [:snare, 0.35] if bb == 35 && (s == 10 || s == 14)
      h << [:hat, (s.even? ? 0.1 : 0.05)]
    when 36
      h << [:snare, 0.25 + s * 0.012] if s.even?
    when 37
      h << [:snare, 0.42 + s * 0.012] if s.even?
    else
      h << [:snare, 0.3 + s * 0.02]
    end
    h
  end
end

# The intro: the hit, the timpani under the hymn, a heartbeat under the line,
# and the wind-up.
define :jf_intro_hits do |t, s|
  h = []
  case t
  when 0
    if s == 0
      h << [:kick, 1.3]
      h << [:crash, 0.6]
    end
    h << [:timp, 0.75] if s == 8
  when 1, 2
    h << [:timp, 0.7] if s == 0 || s == 8
  when 3
    h << [:timp, 0.7] if s == 0 || s == 8
    h << [:timp, 0.3 + (s - 12) * 0.12] if s >= 12
  when 4, 5
    # a heartbeat: lub-dub, twice a bar
    h << [:kick, 0.75] if s == 0 || s == 8
    h << [:kick, 0.5] if s == 3 || s == 11
  when 6
    h << [:kick, 0.95] if s == 0 || s == 8
    h << [:snare, 0.12 + s * 0.02] if s.even?
  else
    h = jf_fill_hits(s, 1.0)
  end
  h
end

define :jf_kit do |t, s|
  part, bb = jf_pos(t)
  case part
  when :intro then jf_intro_hits t, s
  when :c then jf_break_hits bb, s
  when :d then jf_build_hits bb, s
  else jf_drive_hits part, bb, s
  end
end

# ------------------------------------------------------------------ guitar
# The guitar's part, as a score: sixteen slots a bar, each nil or [root, amp,
# beats, intervals]. The riff in A, a ringing chord and chugs under the tune,
# octave stabs in the breakdown (its chords are diminished, and a power chord's
# perfect fifth would fight their flat fifth), a gallop in THE LIFT, and his
# phrase in octaves in THE FALL. Two loops play it, one per side.
define :jf_gtr_bar do |t|
  part, bb = jf_pos(t)
  groot = note(jf_row(t)[0]) + 12
  ev = Array.new(16)
  case part
  when :intro
    if t == 0
      ev[0] = [note(:c3), 0.22, 4, [0, 12]]       # octaves: no G under the box's Gb
    elsif t == 6
      8.times { |e| ev[e * 2] = [groot, 0.12 + e * 0.015, 0.25, [0, 7]] }
    elsif t == 7
      16.times { |s| ev[s] = [groot, 0.12 + s * 0.008, 0.25, [0, 7]] }
    end
  when :a
    if bb == 7
      jf_gtr_windup ev, groot
    else
      # The pedal is a C power chord, except under Db/C and Ab/C, where its G
      # would rub against the chord, so it drops to bare octaves. An accent keeps
      # its fifth only where the fifth belongs (on Db, Eb, F and Ab).
      rf = jf_riff[bb]
      pedal = (bb == 2 || bb == 6) ? [0, 12] : [0, 7]
      16.times do |s|
        off = rf[s]
        if off == 0
          ev[s] = [note(:c3), 0.14, 0.25, pedal]
        elsif off
          ev[s] = [note(:c3) + off, 0.17, 0.5, ([1, 3, 5, 8].include?(off) ? [0, 7, 12] : [0, 12])]
        end
      end
    end
  when :b
    ev[0] = [groot, 0.18, 1.5, [0, 7, 12]]
    (bb == 23 ? (8..15).to_a : [6, 8, 10, 12, 14]).each { |s| ev[s] = [groot, 0.12, 0.25, [0, 7]] }
  when :c
    if bb == 27
      ev[0] = [groot, 0.17, 1, [0, 12]]
    elsif bb < 28
      ev[0] = [groot, 0.17, 0.5, [0, 12]]
      ev[10] = [groot, 0.17, 0.5, [0, 12]]
    else
      16.times { |s| ev[s] = [groot, 0.08 + (bb - 28) * 0.012 + s * 0.002, 0.25, [0, 12]] }
    end
  when :d
    ev[0] = [groot, 0.18, (bb == 39 ? 2 : 1), [0, 7, 12]]
    (1..15).each do |s|
      on = bb == 39 ? s >= 8 : (bb < 36 ? s.even? : true)
      ev[s] = [groot, 0.11 + (bb >= 36 ? 0.02 : 0), 0.25, [0, 7]] if on
    end
  else
    if bb == 60 || bb == 61
      [[:c3, :eb3, :gb3, :eb3], [:c3, :ab2, :gb2, :c3]][bb - 60].each_with_index do |n, i|
        ev[i * 4] = [note(n), 0.19, 0.9, [0, 12]]
      end
    elsif bb == 63
      jf_gtr_windup ev, groot
    else
      # the gallop: one, and-a
      ev[0] = [groot, 0.19, 1, [0, 7, 12]]
      (4..15).each { |s| ev[s] = [groot, 0.12, 0.25, [0, 7]] if s % 4 != 1 }
    end
  end
  ev
end

# The wind-up into a downbeat (A's bar 8 and the loop's bar 64): the chord rings,
# then the chugs come in and close up.
define :jf_gtr_windup do |ev, groot|
  ev[0] = [groot, 0.2, 1.5, [0, 7, 12]]
  (6..15).each { |s| ev[s] = [groot, 0.13 + s * 0.005, 0.25, [0, 7]] if s.even? || s >= 12 }
end

# ------------------------------------------------------------- PERFORMANCE
# Measured on this machine's Sonic Pi 5: EVERY synth, sample or control call costs
# its thread about 15.6 ms of real time, one Windows timer tick, whatever its
# opts, and creating an fx costs 62 ms. It is a per-thread wait, not CPU: four
# threads making ten calls each finish in the time one thread takes to make ten.
# A bar here lasts 1.297 s, so any one thread can afford about 80 calls a bar,
# and the first draft of this file, which put whole sections in one loop and
# built its fx afresh every bar, fell a second behind in the intro and was killed
# ("thread got too far behind time"). Hence, throughout:
#   - every fx is built ONCE, around its loop, and changed with `control`;
#   - the busy parts are split across threads (the kit into three loops, the
#     guitar into its two sides, the arps' octave layer into its own loop), and
#     no loop makes more than about 35 calls in any bar;
#   - the samples are loaded during a silent lead-in, not on first use (a sample
#     loads the first time it is played, and that stalls whatever thread asked).
# Each live_loop stays at column 0 inside its fx, so the tools that read the file
# as text (check_fmwo.rb's tick-scope check, the stem recorder) still find it.

# -------------------------------------------------------------------- clock
# Plays nothing. Its first bar is a four-bar silent lead-in, in which it plays
# every sample once at amp 0 so that all of them are loaded before a note is
# due. Every audible voice syncs to this and joins on its SECOND cue, after the
# lead-in, so they all start together, and the take's first transient is intro
# bar 1 with everyone in it. (A synced loop joins on the NEXT cue; see
# matt_theme.rb for how the older themes got that wrong.)
live_loop :jf_clock do
  if tick(:clock) == 0
    jf_samples.each { |name| sample name, amp: 0 }
    sleep 16
  else
    sleep 4
  end
end

# ---------------------------------------------------------------------- kit
with_fx :level, amp: jf_gain(:drums, 0) do |lev|
live_loop :jf_kick, sync: :jf_clock do
  t = tick(:kick)
  control lev, amp: jf_gain(:drums, t), amp_slide: 0.1
  16.times do |s|
    jf_kit(t, s).each { |name, amp| jf_drum name, amp if [:kick, :hat, :ohat].include?(name) }
    sleep 0.25
  end
end
end

with_fx :level, amp: jf_gain(:drums, 0) do |lev|
with_fx :reverb, room: 0.5, mix: 0.22 do
live_loop :jf_snare, sync: :jf_clock do
  t = tick(:snare)
  control lev, amp: jf_gain(:drums, t), amp_slide: 0.1
  16.times do |s|
    jf_kit(t, s).each do |name, amp|
      jf_drum name, amp if [:snare, :ghost, :tom_hi, :tom_mid, :tom_lo].include?(name)
    end
    sleep 0.25
  end
end
end
end

with_fx :level, amp: jf_gain(:drums, 0) do |lev|
live_loop :jf_perc, sync: :jf_clock do
  t = tick(:perc)
  control lev, amp: jf_gain(:drums, t), amp_slide: 0.1
  16.times do |s|
    jf_kit(t, s).each do |name, amp|
      jf_drum name, amp if [:crash, :timp, :glitch1, :glitch3, :glitch5, :gabber].include?(name)
    end
    sleep 0.25
  end
end
end

# -------------------------------------------------------------------- bass
# The relentless part. Rolling sixteenths that duck every kick. In A it plays
# the riff with the guitar; in C the wobble opens and it becomes a distorted
# drone that crawls up the chromatic climb; in THE FALL it hammers his phrase.
with_fx :level, amp: jf_gain(:bass, 0) do |lev|
with_fx :distortion, distort: 0.35, mix: 0.4 do
with_fx :wobble, phase: 0.5, cutoff_min: 60, cutoff_max: 105, res: 0.35, wave: 3, mix: 0 do |wob|
live_loop :jf_bass, sync: :jf_clock do
  t = tick(:bass)
  control lev, amp: jf_gain(:bass, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  root = note(jf_row(t)[0])
  control wob, mix: (part == :c ? 1 : 0), phase: (part == :c && bb >= 28 ? 0.25 : 0.5)
  case part
  when :intro
    if t < 4
      jf_bass_long root, 0.75, 4
      sleep 4
    elsif t < 6
      jf_bass_long root, 0.45, 4
      sleep 4
    elsif t == 6
      8.times do |e|
        jf_bass_hit root, 0.5 + e * 0.04, 0.5
        sleep 0.5
      end
    else
      jf_roll root, 0.8, [0, 12, 0]
    end
  when :a
    if bb == 7
      jf_roll root, 0.8, [0, 12, 0]
    else
      rf = jf_riff[bb]
      16.times do |s|
        if s % 4 != 0
          off = rf[s]
          accent = !off.nil? && off > 0
          jf_bass_hit root + (accent ? off : 0), (accent ? 0.9 : 0.74), 0.25
        end
        sleep 0.25
      end
    end
  when :b, :e
    jf_roll root, (part == :e ? 0.85 : 0.8), [0, 12, 0]
  when :c
    if bb < 28
      [[0, 0], [1, 0], [0, 3], [6, 3]][bb - 24].each do |off|
        synth :dsaw, note: root + off, amp: 0.7, attack: 0.01, sustain: 1.7,
          release: 0.25, detune: 0.22, cutoff: 110
        synth :sine, note: root + off - 12, amp: 0.4, attack: 0.01, sustain: 1.7,
          release: 0.25
        sleep 2
      end
    else
      synth :dsaw, note: root, amp: 0.7, attack: 0.01, sustain: 3.7, release: 0.25,
        detune: 0.22, cutoff: 110
      synth :sine, note: root - 12, amp: 0.4, attack: 0.01, sustain: 3.7, release: 0.25
      sleep 4
    end
  when :d
    if bb < 36
      16.times do |s|
        jf_bass_hit root + (s == 6 || s == 14 ? 12 : 0), 0.85, 0.5 if s % 4 == 2
        sleep 0.25
      end
    else
      jf_roll root, 0.8, [0, 12, 0]
    end
  else
    if bb == 60 || bb == 61
      [[:c2, :eb2, :gb2, :eb2], [:c2, :ab1, :gb1, :c2]][bb - 60].each do |n|
        jf_bass_hit note(n), 0.95, 1
        sleep 1
      end
    else
      jf_roll root, 0.85, [0, 12, 0]
    end
  end
end
end
end
end

# ------------------------------------------------------------------ guitar
# Double-tracked: each side its own loop and its own amp rig (distortion, then a
# cabinet's worth of low-pass), a few cents apart and panned hard.
with_fx :level, amp: jf_gain(:gtr, 0) do |lev|
with_fx :hpf, cutoff: 38 do
with_fx :lpf, cutoff: 102 do
with_fx :distortion, distort: 0.88, mix: 1, amp: 0.55 do
live_loop :jf_gtr_l, sync: :jf_clock do
  t = tick(:gtr_l)
  control lev, amp: jf_gain(:gtr, t), amp_slide: 0.1
  ev = jf_gtr_bar(t)
  16.times do |s|
    jf_guitar_side ev[s], -0.55, 0.05 if ev[s]
    sleep 0.25
  end
end
end
end
end
end

with_fx :level, amp: jf_gain(:gtr, 0) do |lev|
with_fx :hpf, cutoff: 38 do
with_fx :lpf, cutoff: 102 do
with_fx :distortion, distort: 0.88, mix: 1, amp: 0.55 do
live_loop :jf_gtr_r, sync: :jf_clock do
  t = tick(:gtr_r)
  control lev, amp: jf_gain(:gtr, t), amp_slide: 0.1
  ev = jf_gtr_bar(t)
  16.times do |s|
    jf_guitar_side ev[s], 0.55, -0.05 if ev[s]
    sleep 0.25
  end
end
end
end
end
end

# ------------------------------------------------------------------- arps
# The racing arpeggio: sixteenths up and down the chord, with a dotted-eighth
# echo so it cascades. In A it runs five chord tones in a five-step cell, three
# against four. It is silent in the breakdown until its last two bars, climbs
# two octaves through the build, and in THE LIFT gains an octave layer
# (jf_sparkle).
with_fx :level, amp: jf_gain(:arps, 0) do |lev|
with_fx :echo, phase: 0.75, decay: 1.5, mix: 0.14 do
live_loop :jf_arp, sync: :jf_clock do
  t = tick(:arp)
  control lev, amp: jf_gain(:arps, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  five = jf_five(t)
  run = [0, 1, 2, 3, 4, 3, 2, 1]
  if part == :intro && t < 6
    sleep 4
  elsif part == :intro
    16.times do |s|
      jf_arp_note five[run[s % 8]], 0.05 + (t - 6) * 0.05 + s * 0.004, 82 + (t - 6) * 12 + s
      sleep 0.25
    end
  elsif part == :a
    cells = [0, 2, 4, 1, 3]
    16.times do |s|
      jf_arp_note five[cells[(bb * 16 + s) % 5]], (s % 4 == 0 ? 0.19 : 0.14), 100
      sleep 0.25
    end
  elsif part == :c && bb < 30
    sleep 4
  elsif part == :d && bb >= 36
    ten = five + five.map { |n| n + 12 }
    climb = [0, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1]
    16.times do |s|
      jf_arp_note ten[climb[s]], (s % 4 == 0 ? 0.19 : 0.14), 96 + (bb - 36) * 4 + s * 0.3
      sleep 0.25
    end
  else
    loud = part == :c ? 0.8 + (bb - 30) * 0.2 : 1.0
    16.times do |s|
      jf_arp_note five[run[s % 8]], (s % 4 == 0 ? 0.18 : 0.13) * loud, 104
      sleep 0.25
    end
  end
end
end
end

with_fx :level, amp: jf_gain(:arps, 0) do |lev|
with_fx :echo, phase: 0.75, decay: 1.5, mix: 0.14 do
live_loop :jf_sparkle, sync: :jf_clock do
  t = tick(:sparkle)
  control lev, amp: jf_gain(:arps, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  if part == :e
    five = jf_five(t)
    run = [0, 1, 2, 3, 4, 3, 2, 1]
    16.times do |s|
      jf_arp_note five[run[s % 8]] + 12, (s % 4 == 0 ? 0.18 : 0.13) * 0.45, 108
      sleep 0.25
    end
  else
    sleep 4
  end
end
end
end

# ------------------------------------------------------------------ choir
# Two choirs. The sampled one (jf_choir) sings the bar's chord as minor-third
# dyads, pitched down so it sounds enormous. The synthetic one (jf_chant),
# :blade through a formant filter, sings the hymn in the intro, holds the pads,
# answers the tune in THE LIFT, and shouts his phrase in THE FALL.
with_fx :level, amp: jf_gain(:choir, 0) do |lev|
with_fx :reverb, room: 0.85, mix: 0.4 do
live_loop :jf_choir, sync: :jf_clock do
  t = tick(:choir)
  control lev, amp: jf_gain(:choir, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  dy = jf_row(t)[2]
  case part
  when :intro
    if t < 4
      dy.each_with_index { |d, i| jf_ah d, 0.8, 4, (i.even? ? -0.25 : 0.25) }
      dy.each { |d| jf_ah note(d) - 12, 0.6, 4, 0 }
    else
      loud = [0.5, 0.5, 0.65, 0.85][t - 4]
      dy.each { |d| jf_ah d, loud, 4, -0.2 }
      dy.each { |d| jf_ah note(d) - 12, loud * 0.9, 4, 0.2 }
    end
  when :a then dy.each { |d| jf_ah d, (bb == 0 || bb == 4 ? 0.95 : 0.7), 4, -0.2 }
  when :b then dy.each { |d| jf_ah d, 0.55, 4, 0.2 }
  when :c then dy.each { |d| jf_ah note(d) - 12, 0.6, 8, 0 } if bb.even?
  when :d then dy.each { |d| jf_ah d, 0.6 + (bb - 32) * 0.04, 4, -0.2 }
  when :e then dy.each { |d| jf_ah d, 0.85, 4, -0.2 }
  else dy.each { |d| jf_ah d, (bb == 60 || bb == 61 ? 1.0 : (bb >= 62 ? 0.9 : 0.8)), 4, -0.2 }
  end
  sleep 4
end
end
end

with_fx :level, amp: jf_gain(:chant, 0) do |lev|
with_fx :reverb, room: 0.85, mix: 0.4 do
with_fx :vowel, vowel_sound: 1, voice: 2 do |vox|
live_loop :jf_chant, sync: :jf_clock do
  t = tick(:chant)
  control lev, amp: jf_gain(:chant, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  v = jf_row(t)[1]
  case part
  when :intro
    if t < 4
      control vox, vowel_sound: 1, voice: 2
      jf_hymn[t * 2, 2].each do |n|
        jf_voices [n, note(n) - 12], 0.18, 2
        sleep 2
      end
    else
      control vox, vowel_sound: (t < 6 ? 4 : 1), voice: (t < 6 ? 4 : 3)
      jf_voices v, 0.07 + (t - 4) * 0.025, 4
      sleep 4
    end
  when :a
    control vox, vowel_sound: 4, voice: 3
    jf_voices v, 0.1, 4
    sleep 4
  when :b
    control vox, vowel_sound: 1, voice: 2
    jf_voices v, 0.08, 4
    sleep 4
  when :c
    sleep 4
  when :d
    control vox, vowel_sound: 1, voice: 2
    jf_voices (bb >= 36 ? v.map { |n| note(n) + 12 } : v), 0.08 + (bb - 32) * 0.012, 4
    sleep 4
  when :e
    control vox, vowel_sound: 1, voice: 1
    jf_voices v, 0.07, 4
    jf_counter[bb].each do |n, beats|
      jf_voices [n, note(n) - 12], 0.16, beats
      sleep beats
    end
  else
    control vox, vowel_sound: 1, voice: 2
    if bb == 60 || bb == 61
      jf_hymn[(bb - 60) * 4, 4].each do |n|
        jf_voices [n, note(n) - 12], 0.2, 1
        sleep 1
      end
    else
      jf_voices v, 0.1, 4
      sleep 4
    end
  end
end
end
end
end

# ------------------------------------------------------------------ organ
# The cathedral under the hymn: the intro, the top of the ascent, THE LIFT and
# THE FALL. The chord, with the bass root doubled an octave up under it.
with_fx :level, amp: jf_gain(:organ, 0) do |lev|
with_fx :reverb, room: 0.9, mix: 0.45 do
live_loop :jf_organ, sync: :jf_clock do
  t = tick(:organ)
  control lev, amp: jf_gain(:organ, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  row = jf_row(t)
  amp = case part
        when :intro then [0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.07, 0.1][t]
        when :d then (bb >= 36 ? 0.06 + (bb - 36) * 0.015 : 0)
        when :e then 0.08
        when :f then 0.09
        else 0
        end
  jf_organ_chord [note(row[0]) + 12] + row[1].map { |n| note(n) }, amp, 4 if amp > 0
  sleep 4
end
end
end

# ---------------------------------------------------------------- strings
# Bowed tremolo, as held notes through a tremolo fx: high and cold under the
# hymn and the line, sinister through the breakdown, swelling under the build.
with_fx :level, amp: jf_gain(:strings, 0) do |lev|
with_fx :reverb, room: 0.8, mix: 0.4 do
with_fx :tremolo, phase: 0.25, depth: 0.7, wave: 3 do
live_loop :jf_strings, sync: :jf_clock do
  t = tick(:strings)
  control lev, amp: jf_gain(:strings, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  v = jf_row(t)[1].map { |n| note(n) + 12 }
  plan = if part == :intro
           [v.last(2), [0.05, 0.05, 0.05, 0.05, 0.04, 0.04, 0.06, 0.09][t]]
         elsif part == :c
           [v.last(2), 0.045 + (bb >= 28 ? (bb - 27) * 0.008 : 0)]
         elsif part == :d && bb >= 36
           [v.first(3), 0.04 + (bb - 36) * 0.015]
         end
  if plan
    plan[0].each do |n|
      synth :blade, note: n, amp: plan[1], attack: 0.3, sustain: 3.2, release: 0.6,
        cutoff: 96, vibrato_depth: 0.06, vibrato_delay: 0.3, vibrato_onset: 0.3, pan: -0.35
    end
  end
  sleep 4
end
end
end
end

# ------------------------------------------------------------------- lead
with_fx :level, amp: jf_gain(:lead, 0) do |lev|
with_fx :reverb, room: 0.7, mix: 0.28 do
with_fx :echo, phase: 0.75, decay: 2, mix: 0.16 do
live_loop :jf_lead, sync: :jf_clock do
  t = tick(:lead)
  control lev, amp: jf_gain(:lead, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  phrase = part == :intro ? nil : jf_tune[bb]
  if phrase
    lift = part == :e ? 1.1 : 1.0
    phrase.each do |n, beats|
      jf_lead_note n, beats, 0.4 * lift unless n.nil?
      sleep beats
    end
  else
    sleep 4
  end
end
end
end
end

# ------------------------------------------------------------------ voice
# The distorted voice, through one rig: a formant filter, distortion, a
# bitcrusher that only opens in the breakdown, and a room. It roars as he
# ascends and again at THE LIFT, barks "HAH!" at the top of the riff, chops his
# phrase to pieces in the breakdown, and shouts it in THE FALL.
with_fx :level, amp: jf_gain(:voice, 0) do |lev|
with_fx :reverb, room: 0.8, mix: 0.3 do
with_fx :bitcrusher, sample_rate: 11000, bits: 9, mix: 0 do |crush|
with_fx :distortion, distort: 0.78, mix: 0.72 do
with_fx :vowel, vowel_sound: 1, voice: 4 do |vox|
live_loop :jf_voice, sync: :jf_clock do
  t = tick(:voice)
  control lev, amp: jf_gain(:voice, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  if part == :intro && t == 0
    control vox, vowel_sound: 1, voice: 4
    jf_roar :c4, :c3, 4, 0.3, [0, 6, 12]
    sleep 4
  elsif part == :e && bb == 40
    control vox, vowel_sound: 1, voice: 4
    jf_roar :d4, :d3, 4, 0.26, [0, 7, 12]
    sleep 4
  elsif part == :a && (bb == 0 || bb == 4)
    control vox, vowel_sound: 1, voice: 4
    [:c3, :g3, :c4].each do |n|
      synth :dsaw, note: n, amp: 0.3, attack: 0.01, sustain: 0.3, release: 0.25,
        detune: 0.25, cutoff: 118
    end
    sample :ambi_choir, rpitch: note(:c4) - jf_choir_ref, amp: 1.4, attack: 0.01,
      sustain: 0.35, release: 0.3
    sleep 4
  elsif part == :c
    chops = case bb
            when 24, 26 then [[0, :c4, 1], [3, :c4, 4], [6, :eb4, 1], [10, :c4, 1], [12, :gb4, 4], [14, :eb4, 1]]
            when 25 then [[0, :db4, 1], [3, :c4, 4], [6, :db4, 1], [10, :c4, 1], [12, :f4, 4], [14, :eb4, 1]]
            when 27 then [[0, :c4, 1], [2, :eb4, 4], [3, :gb4, 1], [6, :a4, 4], [8, :gb4, 1], [10, :eb4, 4], [12, :c4, 1], [14, :a3, 4]]
            else
              v = jf_row(t)[1].map { |n| note(n) }
              [[0, v[0], 1], [3, v[1], 4], [6, v[2], 1], [8, v[0] + 12, 1], [11, v[2], 4], [14, v[1], 1]]
            end
    control crush, mix: 0.6
    control vox, voice: 3
    at = 0
    chops.each do |slot, n, vowel|
      sleep (slot - at) * 0.25
      at = slot
      control vox, vowel_sound: vowel
      jf_chop n, 0.28
    end
    sleep (16 - at) * 0.25
    control crush, mix: 0 if bb == 31
  elsif part == :f && (bb == 60 || bb == 61)
    control vox, vowel_sound: 1, voice: 3
    jf_hymn[(bb - 60) * 4, 4].each do |n|
      [0, -12].each do |o|
        synth :dsaw, note: note(n) - 12 + o, amp: 0.22, attack: 0.02, sustain: 0.65,
          release: 0.25, detune: 0.25, cutoff: 116
      end
      sleep 1
    end
  else
    sleep 4
  end
end
end
end
end
end
end

# ------------------------------------------------------------------- hits
# Orchestral hits on the big downbeats, reversed splashes that crack on them, and
# risers into the section changes. The loop's own bar 1 is a big one, so every
# lap of the fight starts with an impact.
with_fx :level, amp: jf_gain(:hits, 0) do |lev|
with_fx :reverb, room: 0.8, mix: 0.3 do
live_loop :jf_hits, sync: :jf_clock do
  t = tick(:hits)
  control lev, amp: jf_gain(:hits, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  row = jf_row(t)
  if part == :intro
    if t == 0
      jf_hit row, 1.0, true
      sample :bass_drop_c, amp: 0.5
    end
    jf_swell 0.45 if t == 6
    jf_riser 4, 0.2 if t == 7
  else
    hit = { 0 => [0.9, true], 4 => [0.6, false], 8 => [0.8, false], 16 => [0.7, false],
            24 => [0.9, true], 28 => [0.65, false], 32 => [0.7, false], 40 => [1.0, true],
            44 => [0.7, false], 48 => [0.75, false], 52 => [0.7, false], 56 => [0.85, false],
            60 => [0.8, false], 61 => [0.8, false] }[bb]
    jf_hit row, hit[0], hit[1] if hit
    jf_swell 0.4 if [6, 22, 30, 38, 54, 62].include?(bb)
    jf_riser 4, 0.18 if [7, 23, 55, 63].include?(bb)
    jf_riser 16, 0.2 if bb == 36
    sample :bass_drop_c, amp: 0.5 if bb == 24
    sample :bass_drop_c, rpitch: 2, amp: 0.55 if bb == 40
  end
  sleep 4
end
end
end

# --------------------------------------------------------------- the box
# The music box from his first fight, playing his phrase exactly as it did: twice.
# Then it warps flat note by note, and winds down an octave lower and gone. In
# the breakdown it comes back as a ghost, bitcrushed, behind the voice.
with_fx :level, amp: jf_gain(:box, 0) do |lev|
with_fx :reverb, room: 0.9, mix: 0.5 do
with_fx :bitcrusher, sample_rate: 7000, bits: 7, mix: 0 do |crush|
live_loop :jf_box, sync: :jf_clock do
  t = tick(:box)
  control lev, amp: jf_gain(:box, t), amp_slide: 0.1
  part, bb = jf_pos(t)
  if part == :intro && t < 2
    jf_box_phrase.each do |n|
      jf_bell n, 0.32 unless n.nil?
      sleep 0.5
    end
  elsif part == :intro && t == 2
    jf_box_phrase.each_with_index do |n, i|
      jf_bell note(n) - i * 0.3, 0.28 - i * 0.02 unless n.nil?
      sleep 0.5
    end
  elsif part == :intro && t == 3
    jf_box_phrase.take(4).each_with_index do |n, i|
      jf_bell note(n) - 14.4 - i * 0.6, 0.18 - i * 0.04
      sleep 1
    end
  elsif part == :c && bb < 28
    control crush, mix: 0.8
    jf_box_phrase.each do |n|
      jf_bell n, 0.16 unless n.nil?
      sleep 0.5
    end
  else
    sleep 4
  end
end
end
end
end
