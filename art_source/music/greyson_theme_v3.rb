# GREYSON & COMPUTAH — "Two Bars", draft 3 (the half you have not heard)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# This is NOT a rewrite. Draft 1 was called great and it deserves it: the
# tempo, the key, the chord loop, the two-character split, every note of the
# tune, both synth voices and the whole drum design are carried over UNTOUCHED.
# Three things change, and one of them is not a musical decision at all — it is
# a bug that has been silently deleting half of this arrangement.
#
# WHAT CHANGED, AND WHY
#
# 1. THE SECOND HALF NOW ACTUALLY PLAYS. (This is the whole point of draft 3.)
#    Draft 1 has one loop, :gc_stomp, that owns the bar counter — `tick(:bar)` —
#    and four loops that read it back with `look(:bar)`. That read does not work.
#    Sonic Pi's ticks are live_loop-local: core.rb's ThreadLocalCounter keeps
#    them in a thread variable, and `look` on a key THIS loop has never ticked
#    returns `(val || 0)`, i.e. 0, forever. Sonic Pi's own docs say it outright —
#    "Ticks are in_thread and live_loop local, so the tick read will be the tick
#    of the current thread calling look."
#    So in the shipped recording:
#      :gc_bass    never plays the `caught` pattern and never gets its +18 cutoff
#      :gc_servo   never tightens onto the chord tones, never takes the octave,
#                  and never drops out for the battery death
#      :gc_iron    never moves onto the downbeats — "the catch" never lands
#      :gc_moments never fires AT ALL, so the battery going flat and the
#                  five-punch combo — the two events this file is built around —
#                  have never been heard by anyone
#    Only :gc_stomp (ticks its own :bar) and :gc_hook (one 64-beat pass, reads no
#    bar at all) were ever right, which is why the drums and the tune do change
#    at bar 9 and nothing else does.
#    Every loop now derives its bar from its own tick. No note changed to fix it.
#    Measured, not assumed: the shipped WAV was checked against the score bar by
#    bar and the five-punch is simply absent — see the measurement note below.
#
#    WHICH MEANS BARS 9-16 ARE UNRELEASED, NOT REVISED. This theme was called
#    great on the strength of a recording in which the catch's accompaniment
#    never arrived and neither moment fired. Nobody has heard those four voices
#    do what they were written to do. That is not a licence to redesign — the
#    composition is good and it is kept — but it does mean there is no honest
#    "before" to A/B the back half against. Judge bars 1-8 as a revision and
#    bars 9-16 as something new.
#    To be exact about what WAS heard, because it is not simply "the first half
#    twice": :gc_stomp ticks its own bar and :gc_hook reads no bar at all, so
#    the drums and the entire tune have always played all sixteen bars
#    correctly, and the chord ROOTS advance correctly everywhere too — they come
#    from each voice's own .tick, not from :bar. What was frozen is the
#    accompaniment's texture (which pattern, which octave, which cutoff) and the
#    two moments. So the harmony and the melody you have heard are real; the
#    back half's density is not.
#
# 2. GREYSON'S STABS GET THEIR OCTAVE BACK IN THE LAST FOUR BARS.
#    :gc_iron's root ring is the bass ring an octave up — c3 over c2, ab2 over
#    ab1, eb3 over eb2, bb2 over bb1 — for twelve of its sixteen entries. The
#    last four are `:f2, :f2, :g2, :g2`: the bass ring's own notes, not an octave
#    above them. So across "the grab", "dragged over", "the wind-up" and the
#    five-punch — the loudest and most triumphant four bars in the fight —
#    Greyson's voice drops to its lowest point in the entire loop and doubles
#    the bass at the fundamental. Counted: draft 1 has 28 exact bass/iron
#    unisons a cycle, rising from one a bar in the chase to three a bar in the
#    last four. Most of those are harmless — the bass's own +12 octave jump
#    touching the stab's root, which is by design — but the last four bars add
#    a root-on-root collision on top. f3/g3 is what the other twelve entries
#    imply, and it takes those bars from three unisons to two and the cycle
#    from 28 to 24. See the measurement note: I expected this to be a mud
#    problem and it is not, quite.
#
# 3. THE TOM FILL GOES SOMEWHERE.
#    Bar 14's fill was four hits of :drum_tom_lo_hard at one amp and one rate —
#    the same thud four times, twice a fight, forever. It now rises in level and
#    in pitch across the beat, so it pushes into the wind-up instead of marking
#    time. Same sample, same placement, same average level.
#
# WHAT THE SHIPPED WAV ACTUALLY MEASURES
#   Per-band RMS at the in-game gain (-7 dB), against Eric's for scale:
#     band        GREYSON   ERIC
#     40-80 Hz     -19.0   -23.0
#     80-160       -18.2   -33.5
#     160-315      -30.0   -44.1
#     315-630      -33.5   -39.5
#     630-1.25k    -34.7   -38.0
#     1.25-2.5k    -36.0   -39.3
#     2.5-5k       -39.5   -37.5
#     5-10k        -42.1   -53.7
#   Read those with the caveat above: they are measured off a recording whose
#   back-half accompaniment was frozen in chase mode and which is missing both
#   moments. The harmony and melody they characterise are the real sixteen bars;
#   the density of bars 9-16 is under-represented, and every figure here will
#   read hotter on a take made from this file. That caveat is exactly what
#   caught out the Eric review, which found a midrange mysteriously thin and
#   later learned a midrange voice had never been playing.
#   Two things this killed:
#   - I had written a low-mid cleanup on the assumption that dropping the iron
#     to f2/g2 was congesting 80-160 Hz, which is this track's loudest band.
#     Measured per bar, those four bars are only +1.3 dB above the other twelve
#     in that band. It is not a mix problem today. It is a problem about
#     REGISTER — Greyson's voice shrinking exactly when he is supposed to be
#     holding you still — and it gets worse the moment change 1 lands, because
#     unfreezing :gc_iron takes those bars from four offbeat stabs to six
#     on-beat ones. So the octave is fixed and nothing else in the low end is.
#   - I considered pulling 2.5-5k down for the parry sting. Measured:
#     parry_hit_1.wav puts 97.3% of its energy in 2.5-5 kHz, and at -39.5 this
#     track is already 2 dB QUIETER up there than Eric, over which the parry
#     reads fine. Greyson is the most forgiving of the three themes in the
#     parry's band and needed nothing.
#
# WHAT THIS FIGHT'S OWN SOUNDS NEED — WHICH IS NOT WHAT ERIC'S NEEDED
#   Eric's draft 3 opened a hole on alternate beats in 500 Hz - 2.5 kHz to make
#   room for the finisher's mash riser and the Knight Breaker sting. That
#   reasoning does NOT carry over here and I did not copy it. Those four sounds
#   — finisher_charge_loop, finisher_bar_1/2/3 and knight_breaker_sting — are
#   gated on the player's feel_v2 flag, which only Eric's fight and the training
#   room set. In this fight the daze and the Q/W mash are SILENT. So is the dash
#   whoosh and the punch whoosh, for the same reason. Copying Eric's hocket into
#   this track would have been thinning a mix to make room for sounds that never
#   arrive.
#   What this fight actually plays is low: earthquake_slam on the phase swap,
#   wrestler_collision on the grab, wrestler_charge under the chase, plus the
#   laser_charge sweep. They are all shared placeholders — the script says the
#   pair have no sounds of their own yet — so there is no point tuning a mix
#   against them until they are real.
#   Two things to know rather than act on. Everything in this game, music
#   included, runs through ONE bus: Master, carrying a single AudioEffectHard-
#   Limiter. There is no Music bus, so a loud sting pumps the music directly.
#   And this fight already ducks the music to -9 dB across the phase swap and
#   back over 0.5 s, which is the right instinct and the only ducking in the
#   project. Change 1 makes the back half denser than anything that has been
#   recorded from this file, and bar 16 adds a drum_heavy_kick at 1.6 into that
#   limiter, so check the peaks on the new take before deciding it is too loud.
#   Worth knowing and NOT a composition problem: the shipped greyson_theme.wav
#   is rotated. Its bar 1 is the score's bar 5 — confirmed on all sixteen bars
#   by pitch-class match, and by the open cymbal landing where score bars 1 and 9
#   are. The recording was started mid-piece, so cut_loop.py cut a true 24.000 s
#   cycle from the wrong downbeat. Re-record with Rec pressed BEFORE Run.
#
# WHAT WAS DELIBERATELY LEFT ALONE
#   160 bpm. C minor. The chord loop, which the harness confirms is correctly
#   aligned under every one of the sixteen bars — unlike Josh's, which was not.
#   Every note of the tune: the call already states one idea at two pitches
#   (bars 1 and 3 are the same arpeggio shape from C and from Ab), which is the
#   thing Eric's draft 3 had to be taught. :chiplead / :hoover / :tb303 / :pulse.
#   bd_haus at 1.5. The battery death and the five-punch exactly as written.
#   The loop seam, which is already good and simply has not been audible: bar 16
#   is a G chord, the fifth punch lands on a C tonic against it, and the last
#   sound before the loop point is :perc_swash at rate 0.7 spilling over the bar
#   line — an anacrusis into bar 1, not a hole in front of it. Bar 15's tune
#   ends on B5, the leading tone, and it resolves onto the punch. That is the
#   joke and it works; it just needed change 1 to happen at all.
#   The one minor 9th in the piece — C6 over the servo's B4 in bar 15 — stays.
#   The file's own comment calls the G chord "the one moment that bites" and it
#   is a passing note that resolves down to B on the next beat.
#
# NOT DONE, ON PURPOSE: a shared motif with Eric's theme. See the report; the
# cheapest landing spot here is bar 7, and it is a real change, not a free one.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: press Rec FIRST, then Run, let it go round
# twice, then Rec again to save a WAV — that ordering is what makes the cut land
# on the downbeat. The cycle is unchanged at 16 bars x 4 beats / 160 bpm =
# 24.0000 s, so the existing cut command still applies:
#   python cut_loop.py greyson_theme_v3_raw.wav 160 --out <somewhere>/greyson_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B.
#
# The form is unchanged, a 16-bar cycle at 160 bpm:
#   Bars 1-8   THE CHASE  — Cm Cm Ab Ab Eb Eb Bb Bb. Computah asks (1-4),
#                           Greyson answers (5-8), the battery goes flat in 8.
#   Bars 9-16  THE CATCH  — Cm Cm Ab Ab Fm Fm G G. Everything locks onto the
#                           same grid, the tune doubles in octaves, and bar 16
#                           is the five-punch combo.
# Every voice is a live_loop synced to the drums, so you can comment one out to
# hear the rest. Draft 1 is beside this file as greyson_theme.rb.

use_bpm 160

# ------------------------------------------------------- the shared harmony
# One list, read by every voice, so the chords cannot drift apart from the tune.
# Writing this out was how the equivalent misalignment got caught in Josh's
# theme, where the melody was written against chords the accompaniment was not
# playing. Greyson's was already correct; this just makes it checkable.
GC_ROOTS = [:c2, :c2, :ab1, :ab1, :eb2, :eb2, :bb1, :bb1,
            :c2, :c2, :ab1, :ab1, :f2,  :f2,  :g2,  :g2].freeze

# Greyson's stabs sit an octave above the bass. All sixteen of them now.
GC_IRON = GC_ROOTS.map { |n| n + 12 }.freeze

GC_CHORDS = [%i[c4 minor], %i[c4 minor], %i[ab3 major], %i[ab3 major],
             %i[eb4 major], %i[eb4 major], %i[bb3 major], %i[bb3 major],
             %i[c4 minor], %i[c4 minor], %i[ab3 major], %i[ab3 major],
             %i[f4 minor], %i[f4 minor], %i[g4 major], %i[g4 major]].freeze

# ---------------------------------------------------------------- the tune
# Written one bar at a time so the arithmetic is visible and checkable. Every
# bar must sum to 4. Not one pitch or duration here differs from draft 1 — the
# notes were only regrouped from three long lists into sixteen labelled bars.
# [note, beats]; nil is a rest.
define :gc_hook_bars do
  [
    # ---- THE CHASE: COMPUTAH ASKS (bars 1-4, :chiplead, high and clipped) ----
    [[:c5, 0.5], [:eb5, 0.5], [:g5, 0.5], [:c6, 0.5], [:bb5, 1], [:g5, 1]],
    #  1  Cm — the question. Up the triad and back down.
    [[:ab5, 0.5], [:g5, 0.5], [:f5, 1], [:eb5, 2]],
    #  2  Cm — and it drops.
    [[:ab4, 0.5], [:c5, 0.5], [:eb5, 0.5], [:ab5, 0.5], [:g5, 1], [:eb5, 1]],
    #  3  Ab — asked again: bar 1's shape from Ab instead of C. The G is a
    #     major 7th passing over the Ab and it is meant to be there.
    [[:f5, 0.5], [:eb5, 0.5], [:c5, 1], [nil, 2]],
    #  4  Ab — room to answer.
    # ---- THE CHASE: GREYSON ANSWERS (bars 5-8, :hoover, an octave down) -----
    [[:eb4, 1], [:eb4, 0.5], [:g4, 0.5], [:bb4, 2]],          #  5  Eb — flat
    [[:bb4, 0.5], [:ab4, 0.5], [:g4, 1], [:eb4, 2]],          #  6  Eb — flatter
    [[:bb3, 1], [:d4, 1], [:f4, 1], [:bb4, 1]],               #  7  Bb — climbing
    [[:ab4, 1], [:g4, 1], [nil, 2]],                          #  8  Bb — and the
    #                                                         #     battery goes
    # ---- THE CATCH: BOTH OF THEM, in octaves (bars 9-16) --------------------
    [[:c5, 0.5], [:c5, 0.5], [:eb5, 0.5], [:f5, 0.5], [:g5, 1], [:f5, 1]],
    #  9  Cm — locked in
    [[:eb5, 0.5], [:f5, 0.5], [:g5, 1], [:c6, 2]],            # 10  Cm — and up
    [[:bb5, 0.5], [:ab5, 0.5], [:g5, 1], [:eb5, 1], [:ab5, 1]],
    # 11  Ab — pressing
    [[:g5, 1], [:f5, 1], [:eb5, 2]],                          # 12  Ab — held
    [[:f5, 0.5], [:ab5, 0.5], [:c6, 1], [:bb5, 1], [:ab5, 1]],
    # 13  Fm — the grab
    [[:g5, 2], [:f5, 2]],                                     # 14  Fm — dragged
    [[:g5, 0.5], [:b5, 0.5], [:d6, 1], [:c6, 1], [:b5, 1]],
    # 15  G  — the wind-up. The only natural B in the piece, and it ends on it:
    #     a leading tone left hanging, which the fifth punch lands on.
    [[nil, 4]]
    # 16  G  — five punches. The tune gets out of the way for the only bar in
    #     the loop where the fight, not the music, is the event.
  ]
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
gc_hook_bars.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "greyson_theme_v3: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# ------------------------------------------------------------------- stomp
# Four on the floor, because this fight never stops moving. The second half adds
# the offbeat kick and a clank on the backbeat: the two of them in step.
# Unchanged from draft 1 except the bar 14 fill, which used to be four identical
# hard toms and now rises into the wind-up.
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
    if bar == 13 && s >= 12
      step = s - 12                                  # 0, 1, 2, 3 across beat 4
      sample :drum_tom_lo_hard, amp: 0.45 + step * 0.15, rate: 0.8 + step * 0.06
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# :tb303, because the engine of this fight is a machine. Sixteenths, accented off
# the kick, with the octave dropping into the gaps so the line never sits flat.
# Draft 1 chose its pattern with look(:bar), so it played `chase` for all sixteen
# bars and the catch never arrived. Its own tick now.
live_loop :gc_bass, sync: :gc_stomp do
  bar = tick(:bass) % 16
  root = GC_ROOTS[bar]
  # Semitones off the bar's root; nil is a rest.
  chase  = [0, nil, 0, 0, nil, 12, 0, nil, 0, nil, 0, 7, 0, nil, 12, 0]
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
# All three of those behaviours were switched off by the frozen look(:bar).
live_loop :gc_servo, sync: :gc_stomp do
  bar = tick(:servo) % 16
  ch = chord(*GC_CHORDS[bar])
  chase  = [0, 1, 2, 1, 2, 1, 0, 1]
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
# half he is holding you still, so they land on it. The on-beat half never
# happened before, because the pattern was chosen by a frozen look(:bar).
# The roots come from GC_IRON, which is the bass an octave up for all sixteen
# bars — draft 1's last four entries had lost that octave and doubled the bass.
# :hoover is the heaviest synth in this file. If the machine struggles, swap it
# for :dsaw — same notes, a fraction of the cost.
live_loop :gc_iron, sync: :gc_stomp do
  bar = tick(:iron) % 16
  root = GC_IRON[bar]
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
# The tune, handed back and forth and then shared. One 64-beat pass, so it never
# needed a bar counter and was the one melodic voice draft 1 got right.
live_loop :gc_hook, sync: :gc_stomp do
  with_fx :reverb, room: 0.55, mix: 0.22 do
    gc_hook_bars.each_with_index do |phrase, bar|
      phrase.each do |n, dur|
        unless n.nil?
          if bar < 4
            # COMPUTAH asks: bright, clipped, mechanical.
            synth :chiplead, note: n, amp: 0.5, release: dur * 0.75
          elsif bar < 8
            # GREYSON answers: an octave down, half the notes, no argument.
            synth :hoover, note: n, amp: 0.3, attack: 0.01,
              sustain: dur * 0.5, release: 0.3, cutoff: 96
          else
            # Both of them, in octaves. The catch.
            synth :chiplead, note: n, amp: 0.42, release: dur * 0.75
            synth :hoover, note: note(n) - 12, amp: 0.2, attack: 0.01,
              sustain: dur * 0.45, release: 0.28, cutoff: 98
          end
        end
        sleep dur
      end
    end
  end
end

# ----------------------------------------------------------------- moments
# The two things the fight does at the end of each half, and the only two bars
# where this track stops being a groove and becomes an event.
#
# NEITHER OF THESE HAS EVER PLAYED. Draft 1 selected them with look(:bar), which
# is always 0, so this loop took its `else` branch — sleep 4 — on all sixteen
# bars of every cycle. The code is unchanged; it can just reach itself now.
live_loop :gc_moments, sync: :gc_stomp do
  bar = tick(:moment) % 16
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
    # you, and the swoosh is you leaving. The swash rings past the bar line, so
    # the loop hands off into bar 1 instead of stopping in front of it.
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
