# ERIC — "Ride for the King", draft 3 (the loop that turns over)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# This is NOT a rewrite of draft 2. Draft 2 was approved, recorded and shipped
# (Assets/Audio/Music/eric_theme.wav) and most of it is right: the tempo, the
# key, the chord loop, the gallop, the synth palette and the opening horn call
# are all carried over untouched. Draft 3 changes six things, listed below, and
# leaves everything else exactly as it was so the two can be A/B'd fairly.
#
# WHAT CHANGED, AND WHY
#
# 1. THE LOOP NOW TURNS OVER INSTEAD OF STOPPING AND RESTARTING.
#    Draft 2's bar 16 was [:e6, 2], [nil, 2] — the highest sustained note in the
#    piece, then two beats of silence, then a drop of a minor 13th to bar 1's
#    A4. Three deflations stacked in two beats: register falls off a cliff, the
#    lead goes quiet, and the texture drops from charge back to march. The fight
#    runs 35-90 s against a 27.8 s loop, so the player crosses that seam two or
#    three times per attempt and hears the track *restart* rather than continue.
#    Bar 16 is now a stepwise descent D6-C6-Bb5-A5 that lands its last beat on
#    A5 — the octave of bar 1's opening A4 — so the loop point is an anacrusis
#    into the call instead of a hole in front of it. The chant shouts on all
#    four beats of bar 16 (elsewhere it is on two) and the tom fill crescendos
#    underneath, so the bar drives into the downbeat instead of emptying out.
#
# 2. THE MARCH'S HORN IS NOW ONE IDEA STATED THREE TIMES, NOT SIX SCALES.
#    Bar 1's call — long note, leap up a fourth, step down, step down — is the
#    best thing in the piece and arrives on beat 1. But bars 3, 5, 6 and 7 were
#    stepwise runs around D-E-F-G, near-interchangeable with each other, and by
#    the twentieth listen they are wallpaper. Bars 3 and 5 now restate the call
#    with the same rhythm and the same rising fourth, starting on A4, D5, F5 —
#    the notes of the D minor triad, spelled out across the phrase. Nothing was
#    added: the melodic vocabulary got *smaller*, which is the point. Bars 2, 4,
#    6, 7 and 8 are untouched, so the phrase still breathes and still climbs
#    into the charge.
#
# 3. THE CHARGE NOW ESCALATES THE CALL INSTEAD OF REPLACING IT.
#    Draft 2's two halves share a key and a chord loop but no melodic material,
#    which is why the back half read as busier rather than bigger. Bar 15 is now
#    bar 1 transposed up an exact octave — the call hurled back at you at full
#    height, over the charge drums, immediately before the turn-around. Bars
#    9-14 are untouched, so the charge keeps its own identity; only its last two
#    bars come home.
#
# 4. THE CHANT AND THE SHIELDS NO LONGER FIGHT EACH OTHER.
#    Draft 2 had the stabs playing [d3, a3, d4] and the chant shouting [d4, a4]
#    on the same downbeats — the same pitch classes in the same octave at the
#    same instant, so the new voice did not read as a new voice, it just made
#    the mid-band louder. Worse, the chant was a fixed D-A over a moving
#    progression: over the Bb bars that is a major seventh and over the C bars a
#    thirteenth, which is far too colouristic for the loudest, most brutal part
#    of a war theme. Now: the chant follows the chord in root-plus-octave (no
#    third, no seventh, nothing to clash), it moves to beats 2 and 4, and the
#    charge stabs move to beats 1 and 3 and get long instead of numerous. The
#    charge is a hocket — SHIELD, shout, SHIELD, shout — which is both more
#    martial and, in a game, more useful: it opens a hole on every other beat in
#    the 500 Hz - 2.5 kHz band, which is where the finisher's mash riser
#    (finisher_charge_loop, 74% of its energy in that band) and the Knight
#    Breaker sting both live. Those are the two moments the music most needs to
#    step back for. The parry needs no help — it is a 2.8 kHz metallic clink and
#    this track has nothing up there at all, which is exactly right.
#
# 5. THE BASS FINALLY PLAYS THE FIFTH ITS OWN COMMENT PROMISED.
#    Draft 2's bass is commented "with the fifth pushing into the bar" and then
#    plays the root six times a bar, for all sixteen bars, forever. The two
#    short notes of the gallop (the "da" of DUM-da-DUM) are now the fifth in the
#    march and the octave in the charge — the same rhythm, but the line has a
#    shape, and the octave lift is one more thing that escalates in the back
#    half without adding a single extra note.
#    The long notes are also articulated now (release 0.6 of the note instead of
#    0.9) so there is daylight between the hoofbeats. See the measurement note
#    below: draft 2's 40-80 Hz band never drops below -18 dBFS anywhere in the
#    loop, because the bass ties every note into the next one. A gallop is
#    separate hits, not a drone, and separating them is also the only low-end
#    change in this draft.
#
# 6. SMALL MIX AND ROBUSTNESS WORK.
#    The horn's octave doubling ran at cutoff 80 — low-passed to almost nothing
#    but the fundamental, which is thickening rather than layering. It is now at
#    cutoff 92, so it reads as a horn, and it leans louder under the
#    declamations (notes of 1.5 beats or more) than under the running eighths.
#    It is still on every note: see the measurement note. The bar 8 and bar 16
#    tom fills were four identical hard hits; they now crescendo in level and
#    pitch. The stabs and the chant get a little stereo width, because the
#    centre of this mix belongs to the kick and the bass and the tune has to
#    compete with them. And every loop now derives its bar number from its own
#    tick instead of reading the drum loop's counter with look(:bar), which
#    removes a same-timestep read race between threads.
#
# WHAT THE SHIPPED WAV ACTUALLY MEASURES, AND WHAT I DID NOT DO ABOUT IT
#   Before changing anything for "mix" reasons I had the shipped file analysed
#   rather than guessing. Per-band RMS at its real in-game gain (-7 dB):
#     40-80 Hz  -23.0 | 80-160 -33.5 | 160-315 -44.1 | 315-630 -39.5
#     630-1.25k -38.0 | 1.25-2.5k -39.3 | 2.5-5k -37.5 | 5-10k -53.7
#   Roughly 90% of the power is under 160 Hz. That killed two changes I had
#   already written and was about to justify as mix work:
#   - I had thinned the horn's octave doubling on the assumption the midrange
#     was crowded. It is the *thinnest* part of this track, and the tune lives
#     there. Thinning it was exactly backwards, so the doubling stayed.
#   - I considered adding air, because 5-10 kHz sits at -53.7 and the track is
#     dark. Left alone deliberately: the parry sting is a 2.8 kHz clink with 97%
#     of its energy in 2-4 kHz, and it reads over this music precisely because
#     the music is empty up there. That separation is worth more than sparkle.
#   The one thing I did not fix here, because it is not a composition problem:
#   break_sting and eric_crash_thud put ~75-80% of their energy below 60 Hz and
#   arrive 4-6 dB HOTTER than this track's dominant 40-80 Hz band, on a single
#   Master bus with one hard limiter. Every guard break and every juggle crash
#   therefore ducks the music. The bass articulation above helps a little; the
#   real fixes are a separate Music bus, or a high-pass on those two stings, or
#   dropping bd_boom from amp 1.7. I left bd_boom alone on purpose — it is the
#   approved war-drum sound and changing it would confound the A/B.
#
# WHAT WAS DELIBERATELY LEFT ALONE
#   138 bpm. D Aeolian. The chord loop (i VI III VII | i VI VII i). The gallop.
#   :tri / :dsaw / :prophet / :hollow. Bars 1-2 — the hook, which arrives on
#   beat 1 and needed nothing. Bars 9-14. bd_boom at 1.7. The 16-bar form. The
#   optional fanfare. Eric is the slowest theme in the set at 138 and that is
#   correct: he is boss 1 and a man in armour, and the ladder climbs from here.
#   The percussion already runs sixteenths (9.2 hits/sec, within 14% of
#   Greyson's at 160 bpm), so the *subdivision* is fast even though the tempo is
#   not; a slow melody over fast feet is what heavy cavalry sounds like.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: hit Rec, let it run twice through the
# 16 bars, hit Rec again to save a WAV. The cycle is unchanged at 16 bars x 4
# beats / 138 bpm = 27.8261 s, so the existing cut command still applies:
#   python cut_loop.py eric_theme_v3_raw.wav 138 --out <somewhere>/eric_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B.
#
# The form is a 16-bar cycle at 138 bpm that loops:
#   Bars 1-8   THE MARCH   — Dm Dm Bb Bb F F C C, the call stated three times
#   Bars 9-16  THE CHARGE  — Dm Dm Bb Bb C C Dm Dm, melody an octave up, the
#                            shields and the army trading beats, and the call
#                            returning at full height in bar 15
# Every voice is a live_loop synced to the drums, so you can comment one out to
# hear the rest. Draft 1 is eric_theme_v1_march.rb; draft 2 is eric_theme.rb.

use_bpm 138

# ---------------------------------------------------------------- the tune
# Written out one bar at a time so the arithmetic is visible and checkable.
# [note, beats]; nil is a rest. Every bar must sum to 4 — two themes drifted
# today because a run of notes did not, so the check below is not decoration.
define :horn_bars do
  [
    # ---- THE MARCH ----------------------------------------------------------
    [[:a4, 1.5], [:d5, 0.5], [:f5, 1], [:e5, 1]],   # 1  Dm — THE CALL. Long A,
                                                    #    up a 4th to D, F, E.
                                                    #    Four notes, one finger.
    [[:d5, 1.5], [:e5, 0.5], [:f5, 2]],             # 2  Dm — answered
    [[:d5, 1.5], [:g5, 0.5], [:f5, 1], [:d5, 1]],   # 3  Bb — THE CALL AGAIN,
                                                    #    from D, up a 4th to G.
                                                    #    Same rhythm, same leap.
    [[:c5, 2], [:d5, 2]],                           # 4  Bb — gathering
    [[:f5, 1.5], [:bb5, 0.5], [:a5, 1], [:g5, 1]],  # 5  F  — THE CALL A THIRD
                                                    #    TIME, from F up a 4th
                                                    #    to Bb. Bb over F is an
                                                    #    11th that falls to the
                                                    #    3rd: a 4-3 suspension,
                                                    #    and the phrase's peak.
    [[:f5, 1.5], [:e5, 0.5], [:d5, 2]],             # 6  F  — settling
    [[:e5, 1], [:f5, 1], [:g5, 1], [:a5, 1]],       # 7  C  — the climb. Left as
                                                    #    plain forward motion on
                                                    #    purpose: after three
                                                    #    statements of the call
                                                    #    the ear wants a runway.
    [[:g5, 2], [nil, 2]],                           # 8  C  — the breath, and
                                                    #    room for the tom fill.
                                                    #    The only rest in the
                                                    #    loop, and it earns its
                                                    #    place here because the
                                                    #    charge lands after it.
    # ---- THE CHARGE ---------------------------------------------------------
    [[:d6, 1], [:c6, 0.5], [:bb5, 0.5], [:a5, 2]],  # 9  Dm — the charge, from
                                                    #    the top down
    [[:a5, 1], [:bb5, 0.5], [:c6, 0.5], [:d6, 2]],  # 10 Dm — bar 9 backwards
    [[:f6, 1.5], [:e6, 0.5], [:d6, 2]],             # 11 Bb — the banner
    [[:c6, 1], [:d6, 1], [:e6, 2]],                 # 12 Bb — held
    [[:f6, 1.5], [:e6, 0.5], [:d6, 1], [:c6, 1]],   # 13 C  — driving. Shares its
                                                    #    head with 11 on purpose:
                                                    #    that repeat is the
                                                    #    charge's own hook.
    [[:bb5, 2], [:a5, 2]],                          # 14 C  — the turn, and it
                                                    #    parks on A, which is
                                                    #    where the call begins
    [[:a5, 1.5], [:d6, 0.5], [:f6, 1], [:e6, 1]],   # 15 Dm — THE CALL, OCTAVE
                                                    #    UP. Bar 1 exactly, at
                                                    #    full charge. The A it
                                                    #    starts on is the A bar
                                                    #    14 was already holding,
                                                    #    so it arrives rather
                                                    #    than interrupts.
    [[:d6, 1.5], [:c6, 0.5], [:bb5, 1], [:a5, 1]]   # 16 Dm — THE TURN-AROUND.
                                                    #    Straight down the mode
                                                    #    to A5 on beat 4, which
                                                    #    is bar 1's A4 an octave
                                                    #    up. No hole, no cliff:
                                                    #    the loop hands off.
  ]
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
horn_bars.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "eric_theme_v3: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# --------------------------------------------------------------- war drums
# A gallop, not a march: DUM-da-DUM in each half bar, snare on the backbeats,
# and a tom fill into each new phrase. The charge adds off-beat hits.
# Unchanged from draft 2 apart from the fill, which used to be four identical
# hard toms — the same thud four times, twice a loop, forever. It now rises in
# level and pitch, so it is a fill that goes somewhere rather than a stutter.
live_loop :war_drums do
  bar = tick(:bar) % 16
  charge = bar >= 8
  sample :drum_cymbal_open, amp: 0.5, rate: 0.8 if bar == 0 || bar == 8
  16.times do |s|
    sample :bd_boom, amp: 1.7, rate: 0.85 if [0, 3, 4, 8, 11, 12].include?(s)
    sample :bd_boom, amp: 1.1, rate: 0.9 if charge && [6, 14].include?(s)
    sample :drum_snare_soft, amp: 0.7 if s == 4 || s == 12
    sample :drum_snare_soft, amp: 0.35, rate: 1.2 if charge && [7, 15].include?(s)
    if (bar == 7 || bar == 15) && s >= 12
      step = s - 12                                  # 0, 1, 2, 3 across beat 4
      sample :drum_tom_lo_hard, amp: 0.45 + step * 0.18, rate: 0.85 + step * 0.05
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# The horses. Draft 2's comment promised "the fifth pushing into the bar" and
# then played the root six times a bar for all sixteen bars. It does now: the
# two short notes of the gallop take the fifth in the march and the octave in
# the charge. Same rhythm, same weight, but the line has a contour, and the
# octave is one more thing that lifts in the back half without adding notes.
#
# The release is 0.6 of the note rather than 0.9, so the gallop is separate
# hoofbeats instead of a tied drone. This is the only change in the draft that
# touches the low end, and it is there because the shipped file's 40-80 Hz band
# never drops below -18 dBFS across the whole loop — it is the one part of this
# mix that genuinely never gets out of its own way.
# 0.75 + 0.25 + 1.0 + 0.75 + 0.25 + 1.0 = 4.0 beats, one bar.
live_loop :war_bass, sync: :war_drums do
  bar = tick(:bass) % 16
  root = [:d2, :d2, :bb1, :bb1, :f2, :f2, :c2, :c2,
          :d2, :d2, :bb1, :bb1, :c2, :c2, :d2, :d2][bar]
  lift = bar >= 8 ? 12 : 7                           # octave in the charge
  use_synth :tri
  with_fx :lpf, cutoff: 85 do
    [[0.75, 1.0, 0], [0.25, 0.5, lift], [1.0, 0.9, 0],
     [0.75, 1.0, 0], [0.25, 0.5, lift], [1.0, 0.9, 0]].each do |dur, amp, off|
      play root + off, amp: amp * 0.9, attack: 0.01, release: dur * 0.6
      sleep dur
    end
  end
end

# ---------------------------------------------------------- shields (stabs)
# Open fifths, no thirds. Thirds sound courtly; fifths sound like armour.
#
# The march is unchanged: four short stabs on the off-beats, which is what
# gives the first half its lift.
#
# The charge is the real change. Draft 2 went from four off-beat stabs to six
# on-beat ones — busier, not bigger, and it put the shields on top of the chant
# and the horn's downbeats at once. Two long stabs on beats 1 and 3 read as far
# more weight than six short ones, because weight comes from duration and space,
# and it leaves beats 2 and 4 to the army. SHIELD, shout, SHIELD, shout.
live_loop :war_stabs, sync: :war_drums do
  bar = tick(:stab) % 16
  root = [:d3, :d3, :bb2, :bb2, :f3, :f3, :c3, :c3,
          :d3, :d3, :bb2, :bb2, :c3, :c3, :d3, :d3][bar]
  charge = bar >= 8
  hit = 0
  use_synth :dsaw
  with_fx :reverb, room: 0.6, mix: 0.25 do
    8.times do |i|                                   # i counts eighth notes
      on = charge ? [0, 4].include?(i) : [1, 3, 5, 7].include?(i)
      if on
        side = hit.even? ? -1 : 1
        hit += 1
        if charge
          # Planted, not ticked: about 1.25 beats of ring. Narrow pan, because
          # a long chord that lurches side to side is distracting.
          play [root, root + 7, root + 12], amp: 0.38, attack: 0.01,
            sustain: 0.7, release: 0.55, cutoff: 98, detune: 0.15,
            pan: side * 0.15
        else
          # Short and wide — the width is free here and it keeps the centre
          # clear for the horn and the kick.
          play [root, root + 7, root + 12], amp: 0.34, attack: 0.005,
            release: 0.22, cutoff: 92, detune: 0.15, pan: side * 0.26
        end
      end
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- horn
# The theme. Dotted and declamatory: a call you could shout orders over.
#
# The octave doubling is the one place I changed my mind after measuring. Draft
# 2 runs it at cutoff 80, which strips it to little more than a fundamental —
# thickening rather than layering. My first pass cut it back to the long notes
# only, on the assumption that the midrange was crowded. It is not: 315-630 Hz
# sits at -39.5 dBFS and 630-1.25k at -38.0, against -23.0 in the bass. The
# midrange is the thinnest part of this track and the tune is what lives there,
# so cutting it was backwards and the doubling stayed on every note. What it got
# instead is cutoff 92 — enough harmonics to read as a horn — and more weight
# under the declamations (1.5 beats or longer) than under the running eighths.
# A second timbre on top was the other option, and it is still the better long
# term answer if the user wants more body; it is a bigger change than this draft
# should make to an approved track.
live_loop :war_horn, sync: :war_drums do
  use_synth :prophet
  with_fx :reverb, room: 0.8, mix: 0.3 do
    horn_bars.each_with_index do |phrase, bar|
      # The march keeps draft 2's level exactly; the charge steps up 0.6 dB.
      # It can afford to: the charge stabs went from six hits a bar to two.
      lead = bar < 8 ? 0.78 : 0.84
      phrase.each do |n, dur|
        unless n.nil?
          play n, amp: lead, attack: 0.02, sustain: dur * 0.55,
            release: 0.35, cutoff: 104
          play n - 12, amp: (dur >= 1.5 ? 0.38 : 0.26), attack: 0.02,
            sustain: dur * 0.5, release: 0.3, cutoff: 92
        end
        sleep dur
      end
    end
  end
end

# ------------------------------------------------------------------- chant
# Bars 9-16 only: the army answering the horn.
#
# Three changes from draft 2, all of them about getting out of the way.
# PITCH: it was a fixed [d4, a4] over a moving progression — a major seventh
# over the Bb bars and a thirteenth over the C bars, which is a lovely colour
# and completely wrong for a war chant. It now takes the root of the bar and its
# octave. Octaves add no new pitch class, so a crowd in octaves cannot clash
# with anything, and against a texture made entirely of fifths the octave reads
# as one fat voice rather than another harmony.
# PLACE: it was on beats 1 and 3, in unison with the horn's attack, the stabs,
# the bass and the kick. It is on 2 and 4 now — the backbeat, with the snare,
# answering the call instead of shouting over it.
# SPACE: room 0.9 / mix 0.55 on a noisy mid-register synth is a permanent fog
# across the loudest half of the track, and fog is what makes music fight sound
# effects: it fills the gaps the effects need. Cut to a hall slap, and the
# envelope shortened so a shout is a shout.
#
# noise: on :hollow is an enumerated opt, not a continuous one — Sonic Pi
# validates it with v_one_of(:noise, [0, 1, 2, 3, 4]). Pass an Integer.
# Worth knowing while hunting the version of this bug that shipped in three
# themes today: that validator is Array#include?, and 1.0 == 1 in Ruby, so a
# whole-number float slips straight through, and a fractional one gets truncated
# to a different source instead of raising. Either way you get the wrong layer
# or no layer and never see an error, which is exactly why it has to be checked
# by reading rather than by running.
# 1 is brown noise — the darkest of the five, and the closest thing here to a
# room full of people. 0 is pink, 2 is white.
live_loop :war_chant, sync: :war_drums do
  bar = tick(:chant) % 16
  root = [nil, nil, nil, nil, nil, nil, nil, nil,
          :d3, :d3, :bb2, :bb2, :c3, :c3, :d3, :d3][bar]
  if root.nil?
    sleep 4                                          # the march: one bar of rest
  else
    last = bar == 15                                 # bar 16: shout on all four
    use_synth :hollow
    with_fx :reverb, room: 0.6, mix: 0.3 do
      4.times do |i|                                 # i counts beats, 0-3
        if last || i.odd?
          play root, amp: 0.42, attack: 0.005, sustain: 0.14, release: 0.22,
            cutoff: 95, res: 0.35, noise: 1, pan: -0.18
          play root + 12, amp: 0.34, attack: 0.005, sustain: 0.12, release: 0.2,
            cutoff: 98, res: 0.3, noise: 1, pan: 0.18
          # A tom under the backbeat shouts, but not in bar 16 — the fill owns
          # that bar and two sets of toms in one bar is just noise.
          sample :drum_tom_mid_hard, amp: 0.3, rate: 0.9 if i.odd? && !last
        end
        sleep 1
      end
    end
  end
end

# ---------------------------------------------------------------- fanfare
# Optional opener: the herald's call before the first gallop. Uncomment,
# press Run, then comment it out again so the loop stays clean.
#
# use_synth :blade
# with_fx :reverb, room: 0.9 do
#   [[:d4, 0.5], [:a4, 0.25], [:d5, 0.75], [:c5, 0.5], [:d5, 1.5], [:a5, 1.5]].each do |n, dur|
#     play n, amp: 0.85, attack: 0.01, sustain: dur * 0.6, release: 0.4
#     play n - 12, amp: 0.4, attack: 0.01, sustain: dur * 0.6, release: 0.4
#     sleep dur
#   end
# end
