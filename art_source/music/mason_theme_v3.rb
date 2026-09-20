# MASON — "Snack Run", draft 3 (the one where the jokes actually fire)
# Original music for Project FMWO, written for Sonic Pi 4.x / 5.x.
#
# This is NOT a rewrite of draft 2. The tempo, the key, the chord loop, the
# synth palette, the whole eight-bar opening tune and every one of the four
# "moments" are carried over untouched. Draft 3 changes six things, listed
# below, and leaves everything else alone so the two can be A/B'd fairly.
#
# One of those six is not a taste call. It is a bug, and it is the reason the
# other five are hard to judge by ear against the shipped WAV. Read change 1
# before listening to anything.
#
# ---------------------------------------------------------------------------
# WHAT CHANGED, AND WHY
#
# 1. THE BAR NUMBER NOW COMES FROM EACH LOOP'S OWN TICK. THIS IS THE BIG ONE.
#    Draft 2 has `bar = look(:bar) % 16` in mason_bass, mason_oompah,
#    mason_lead and mason_moments. Only mason_kit ever calls tick(:bar).
#    Sonic Pi tick counters are live_loop-local and are NOT inherited by other
#    threads: in sonicpi/core.rb, ThreadLocalCounter.get_or_create_counters
#    stores them with __thread_locals.set_local, and look returns (val || 0).
#    Measured against the installed engine, two threads:
#        the loop that ticks :bar eight times    look(:bar) => 7
#        any other live_loop                     look(:bar) => 0
#        a thread spawned from the ticker        look(:bar) => 0
#    So in draft 2 `bar` is 0 in four of the five loops, on every iteration,
#    forever. It is not a race and it is not intermittent. Every branch keyed
#    off it is dead code. Simulated over one full cycle, draft 2 actually does
#    this:
#        mason_moments    0 events, where the file intends 43
#        mason_lead       78 events, where the file intends 113
#        mason_oompah / mason_bass  pinned to the bar-1 pattern all cycle
#    In plain terms, NONE of these have ever been heard:
#        - the ripple of pops that runs the band off after the squat
#        - the phone ringing in bars 9 and 11
#        - the three nugget impacts a bar in the storm
#        - the wind-up riser in bar 16
#        - the entire SLAM and STORM melody; the lead has only ever played the
#          eight-bar LINE, twice, the second time over the wrong chords
#        - the bass's heavy and walk patterns, and its chromatic descent
#        - the squat, in the bass and the oompah (only the kit stopped)
#    The harmony still moved, because the bass and oompah take their root from
#    their own ring tick, which is why the shipped WAV sounds like a finished
#    piece rather than an obviously broken one. It is a finished piece of the
#    first eight bars.
#    CONSEQUENCE FOR REVIEWING THIS DRAFT: bars 9-16 are not a revision of
#    something you have heard. They are unreleased. Judge them as new.
#
# 2. THE SQUAT IS THE SAME GAG BOTH TIMES.
#    The squat is Mason's best joke — the band stops dead on the last beat of
#    bars 4 and 8 and a ripple of pops runs the line off. Bar 8's melody ends
#    [:fs5, 1], [nil, 1], so it gets out of the way. Bar 4's ended [:d5, 2],
#    a note that starts on beat 3 and is still ringing when the band stops.
#    A gag has to be the same gag the second time or it is not a callback, it
#    is a mistake. Bar 4 now ends [:d5, 1], [nil, 1]. That is a one-note change
#    and it is the only edit to the eight-bar LINE in this draft.
#    With change 1 in place the bass and the oompah now stop for the squat too,
#    which they were always written to do and have never done.
#
# 3. THE BAND STAYS A BAND IN THE SLAM.
#    Draft 2 squares the oompah onto all four downbeats from bar 9 to the end.
#    Two problems. Musically, that puts the oompah in unison with bd_haus (on
#    every beat) and the bass root (on every beat) — a third voice arriving on
#    a downbeat that already has two, adding weight but no information. That is
#    the same collision Eric's chant and shield stabs had.
#    And characterfully it is worse: a tuba on all four beats is a march. OOM-
#    pah OOM-pah is a circus band. Squaring it up in the slam makes Mason
#    competent, and competent is the one thing he must never be — he is on the
#    phone while he fights you.
#    So the slam keeps the "pah" off the beat and gets its weight the way
#    weight is actually made, from voicing and duration: the fifth gains an
#    octave on top and the chord rings twice as long. Only the STORM squares
#    up. That way the square-up means something — it is the single moment the
#    band stops being a band, which is exactly when the nugget meteor lands.
#
# 4. THE PHONE CAN BE HEARD.
#    Two rings in bars 9 and 11, on :chiplead at amp 0.3, underneath bd_haus at
#    1.5 and a distorted tb303 running sixteenths. It is a comedy beat: if it
#    does not land it is not a joke, it is a texture. It moves up an octave to
#    b6/fs6 — a real telephone is thin and high, and that register is the least
#    occupied part of this mix — comes up in level, and the closed hat gets out
#    of its way for those two beats. Nothing else changes; the rhythm of the
#    rings and the kick that answers them are draft 2's.
#
# 5. THE TOM FILL GOES SOMEWHERE.
#    Bar 16's fill was drum_tom_mid_hard four times at one level and one pitch,
#    twice a loop, forever. It now rises in level and pitch across the beat, so
#    it is a fill and not a stutter. Same fix Eric's draft 3 made, same reason.
#
# 6. ROBUSTNESS.
#    Every loop derives its bar from its own tick (change 1). The melody is one
#    16-bar table instead of three tables selected by a bar test, so the tune
#    cannot fall out of step with the harmony even if someone edits a bar
#    length later — and the bar arithmetic is checked out loud at startup.
#
# ---------------------------------------------------------------------------
# WHAT THE SHIPPED WAV MEASURES, AND WHAT I DID NOT DO ABOUT IT
#
#   Per-band RMS of Assets/Audio/Music/mason_theme.wav, whole file, and the
#   share of total power in each band:
#     40-80 Hz   -16.9  65.3% | 80-160    -23.3  15.0%
#     160-315    -27.3   6.0% | 315-630   -28.1   4.9%
#     630-1250   -28.2   4.8% | 1250-2500 -33.9   1.3%
#     2500-5000  -34.0   1.3% | 5000-10k  -36.5   0.7%
#   80.3% of the power is below 160 Hz. Peak is -0.1 dBFS, so it is already
#   against the ceiling.
#   READ THAT NUMBER WITH THE CAVEAT IT DESERVES: because of change 1, this
#   file is missing mason_moments entirely and has the bass and oompah pinned
#   to their bar-1 patterns, so it characterises the LINE and not the slam or
#   the storm. It is a measurement of eight of the sixteen bars.
#   What it did decide: the phone's octave. b5/fs5 are 988 and 740 Hz, which
#   sit in the 630-1250 band — 4.8% of the power, the busiest thing above the
#   bass. b6/fs6 are 1976 and 1480 Hz, in the 1250-2500 band at 1.3%. Moving
#   the rings up an octave puts them 5.7 dB further out of the way of the rest
#   of the mix, in the register the ear is most sensitive to and this track has
#   almost nothing in. That is measurement, not taste.
#   What I did NOT do: nothing about the low end, even though 65% of the power
#   sits in 40-80 Hz and the file is peaking at -0.1. bd_haus at 1.5 and the
#   distorted tb303 are the approved sound of this track and thinning either
#   would confound the A/B against the shipped file. If the user wants headroom
#   the honest fix is a Music bus with its own gain, not a quiet rewrite here.
#
# ---------------------------------------------------------------------------
# WHAT WAS DELIBERATELY LEFT ALONE, AND WHY
#
#   165 bpm. B minor with the A# saved for the F# chords. The chord loop. The
#   tb303 sixteenth bass and its distortion. :blade for the lead. bd_haus at
#   1.5. The 16-bar form. All four moments, in their draft 2 form.
#
#   THE EIGHT-BAR TUNE, apart from the one note in change 2. It is already the
#   thing Eric's draft 3 had to be taught. Bars 1, 3, 5 and 7 are one idea —
#   run up the chord in four eighths, then step down twice — stated at four
#   pitches (B, G, E, F#). Four statements of one figure, and the vocabulary is
#   tiny: you could play it with one finger. It does not need fixing.
#
#   THE STORM'S RELATIONSHIP TO THE LINE. Bar 15 is g5 d5 b4 g4; bar 3 is
#   g4 b4 d5 g5. The meteor is the waddle backwards. That was already there and
#   it is the best joke in the back half, so it stays exactly as written.
#
#   THE SLAM'S SEMITONE SLIP. Bars 11-12 are bars 9-10 moved down a semitone to
#   Bb, note for note. It is the cheapest joke in music. Untouched.
#
#   THE LOOP SEAM, AND THIS ONE IS A DELIBERATE DISAGREEMENT WITH THE BRIEF'S
#   CHECKLIST. Eric's bar 16 was a genuine cliff: highest sustained note, then
#   silence, then a drop of a minor 13th. Mason's bar 16 looks superficially
#   similar — it also ends on the highest note of the piece, fs6, and bar 1
#   also starts a twelfth below on b4 — but it is the opposite situation and it
#   needs no repair. Bar 16 is an F# chord with the raised 7th (a#5) inside it,
#   which is to say a dominant with its leading tone, and bar 1 is the tonic.
#   V to i with the leading tone resolving up a semitone is the strongest
#   turn-around in tonal music; the register drop is not a deflation, it is the
#   resolution landing where the tune lives. On top of that the wind-up riser
#   slides fs3 to fs5 underneath it and the kick lands on the "and" of 4 as a
#   pickup, so there is no hole in front of the downbeat — there is a ramp.
#   The fix here was not to rewrite the seam. It was change 1, which makes the
#   seam audible for the first time.
#
# ---------------------------------------------------------------------------
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: press Rec FIRST, then Run, let it go round
# twice, press Rec again. The cycle is unchanged at 16 bars x 4 beats / 165 bpm
# = 23.2727 s, so the existing cut command still applies:
#   python cut_loop.py mason_theme_v3_raw.wav 165 --out <somewhere>/mason_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B.
#
# 16-bar cycle, written to Mason's actual fight cycle:
#   Bars 1-8    THE LINE   — Bm Bm G G Em Em F# F#. The waddle as a stomp.
#                            Bars 4 and 8 stop dead on the last beat.
#   Bars 9-12   THE SLAM   — Bm Bm Bb Bb. He is on the phone, and the harmony
#                            slips down a semitone halfway.
#   Bars 13-16  THE STORM  — Am Am G F#. The nugget meteor, over a bass walking
#                            chromatically down, winding up on F# to go again.
# Every voice is a live_loop synced to the kit, so you can comment one out.

use_bpm 165

# ---------------------------------------------------------------- the tune
# One 16-bar table, written a bar at a time so the arithmetic is visible.
# [note, beats]; nil is a rest. Every bar must sum to 4.
define :mason_bars do
  [
    # ---- THE LINE -----------------------------------------------------------
    [[:b4, 0.5], [:d5, 0.5], [:fs5, 0.5], [:d5, 0.5],
     [:b4, 1], [:fs4, 1]],                           # 1  Bm — the waddle. Run
                                                     #    up the chord, step
                                                     #    down twice. This is
                                                     #    the whole vocabulary.
    [[:b4, 0.5], [:cs5, 0.5], [:d5, 1], [:b4, 1], [nil, 1]],  # 2  Bm — answered
    [[:g4, 0.5], [:b4, 0.5], [:d5, 0.5], [:g5, 0.5],
     [:fs5, 1], [:d5, 1]],                           # 3  G  — the same figure
                                                     #    from G
    [[:e5, 0.5], [:d5, 0.5], [:b4, 1], [:d5, 1], [nil, 1]],
                                                     # 4  G  — THE SQUAT. The
                                                     #    d5 used to be 2 beats
                                                     #    and hung over the
                                                     #    stop. Now it lets go
                                                     #    on beat 4, the way
                                                     #    bar 8 always did.
    [[:e4, 0.5], [:g4, 0.5], [:b4, 0.5], [:e5, 0.5],
     [:d5, 1], [:b4, 1]],                            # 5  Em — the figure again,
                                                     #    from E
    [[:g5, 0.5], [:fs5, 0.5], [:e5, 1], [:b4, 2]],   # 6  Em — dropping
    [[:fs4, 0.5], [:as4, 0.5], [:cs5, 0.5], [:fs5, 0.5],
     [:e5, 1], [:cs5, 1]],                           # 7  F# — the figure from
                                                     #    F#, and the a#4 is the
                                                     #    raised 7th. It only
                                                     #    ever appears over F#,
                                                     #    which is what makes it
                                                     #    sound like he is
                                                     #    winding up to do
                                                     #    something.
    [[:as4, 1], [:cs5, 1], [:fs5, 1], [nil, 1]],     # 8  F# — and the squat
    # ---- THE SLAM -----------------------------------------------------------
    [[:b5, 0.5], [:b5, 0.5], [:fs5, 1], [:d5, 1], [:b4, 1]],
                                                     # 9  Bm — bar 1's chord run
                                                     #    upside down and an
                                                     #    octave up: he answers
                                                     #    his own waddle by
                                                     #    barking it downward.
    [[:d5, 1], [:fs5, 1], [:b5, 2]],                 # 10 Bm — held
    [[:bb5, 0.5], [:bb5, 0.5], [:f5, 1], [:db5, 1], [:bb4, 1]],
                                                     # 11 Bb — bar 9, a semitone
                                                     #    down, note for note
    [[:db5, 1], [:f5, 1], [:bb5, 2]],                # 12 Bb — the joke lands
    # ---- THE STORM ----------------------------------------------------------
    [[:a5, 0.5], [:g5, 0.5], [:e5, 0.5], [:c5, 0.5],
     [:a4, 1], [:e5, 1]],                            # 13 Am — first cascade
    [[:a5, 0.5], [:g5, 0.5], [:e5, 0.5], [:c5, 0.5], [:a4, 2]],
                                                     # 14 Am — second
    [[:g5, 0.5], [:d5, 0.5], [:b4, 0.5], [:g4, 0.5],
     [:d5, 1], [:b4, 1]],                            # 15 G  — bar 3 backwards.
                                                     #    The meteor is the
                                                     #    waddle in retrograde,
                                                     #    which is why the storm
                                                     #    sounds like the same
                                                     #    man and not a new one.
    [[:fs5, 1], [:as5, 1], [:cs6, 1], [:fs6, 1]]     # 16 F# — the wind-up. F#
                                                     #    major with the raised
                                                     #    7th: a dominant, with
                                                     #    its leading tone, and
                                                     #    bar 1 is the tonic. It
                                                     #    hands off upward.
  ]
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
mason_bars.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "mason_theme_v3: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# --------------------------------------------------------------------- kit
# Four on the floor with the woodblock keeping the joke. Shuts up for the last
# beat of bars 4 and 8, because the squat is the funniest thing he does.
# Unchanged from draft 2 except the bar 16 fill, which used to be four
# identical hits, and the hat stepping aside for the phone.
live_loop :mason_kit do
  bar = tick(:bar) % 16
  slam = bar >= 8 && bar < 12
  storm = bar >= 12
  squat = bar == 3 || bar == 7
  phone = bar == 8 || bar == 10
  sample :drum_cymbal_open, amp: 0.45, rate: 1.2 if bar == 0
  sample :drum_splash_hard, amp: 0.7, rate: 0.75 if bar == 8 || bar == 12
  16.times do |s|
    quiet = squat && s >= 12
    unless quiet
      sample :bd_haus, amp: 1.5 if s % 4 == 0
      sample :bd_haus, amp: 0.85 if (slam || storm) && [6, 14].include?(s)
      sample :drum_snare_hard, amp: 0.6, rate: 1.1 if s == 4 || s == 12
      sample :drum_snare_soft, amp: 0.25, rate: 1.4 if slam && [7, 15].include?(s)
      # The hat runs all the way through except across the phone's two beats,
      # where it would be sitting right on top of the rings.
      unless phone && s >= 8 && s < 12
        sample :drum_cymbal_closed, amp: 0.2, rate: 1.25 if s.odd?
      end
      sample :elec_blip2, amp: 0.3, rate: 1.6 if !slam && !storm && [2, 10].include?(s)
      sample :drum_tom_lo_hard, amp: 0.7, rate: 0.8 if storm && s % 4 == 2
      if bar == 15 && s >= 12
        step = s - 12                                # 0, 1, 2, 3 across beat 4
        sample :drum_tom_mid_hard, amp: 0.5 + step * 0.16, rate: 0.82 + step * 0.06
      end
    end
    sleep 0.25
  end
end

# -------------------------------------------------------------------- bass
# Sixteenths all the way through, and the only rest it takes is the squat. In
# the storm it walks down chromatically, which is what turns the joke sinister.
# Unchanged from draft 2 except that it now knows what bar it is in, so the
# heavy and walk patterns and the squat rest actually happen.
live_loop :mason_bass, sync: :mason_kit do
  bar = tick(:bass) % 16
  root = note([:b1, :b1, :g1, :g1, :e1, :e1, :fs1, :fs1,
               :b1, :b1, :bb1, :bb1, :a1, :a1, :g1, :fs1][bar])
  squat = bar == 3 || bar == 7
  # Semitones off the bar root; nil is a rest.
  waddle = [0, nil, 0, 12, 0, nil, 7, 0, 0, nil, 0, 12, 0, 7, 0, nil]
  heavy  = [0, 0, 12, 0, 0, 0, 12, 7, 0, 0, 12, 0, 7, 5, 3, 0]
  walk   = [0, 0, 12, 0, 3, 2, 1, 0, 0, 0, 12, 0, 5, 3, 2, 1]
  pattern = if bar >= 12 then walk elsif bar >= 8 then heavy else waddle end
  use_synth :tb303
  with_fx :distortion, distort: 0.32, mix: 0.45 do
    pattern.each_with_index do |off, s|
      if squat && s >= 12
        sleep 0.25
        next
      end
      unless off.nil?
        play root + off, amp: (s % 4 == 0 ? 0.88 : 0.56),
          attack: 0.004, sustain: 0.045, release: 0.12, res: 0.82,
          cutoff: 76 + (bar >= 8 ? 20 : 0) + (s % 4 == 0 ? 14 : 0)
      end
      sleep 0.25
    end
  end
end

# ------------------------------------------------------------------ oompah
# The band. This is the voice that decides whether Mason is funny, so it is the
# one place in the arrangement worth being fussy about.
#
# THE LINE  — "pah" on the offbeats, root and fifth. Draft 2, untouched.
# THE SLAM  — still off the beat. Draft 2 squared it onto all four downbeats,
#             where bd_haus and the bass root already are; three voices hitting
#             the same instant is louder, not bigger, and it turns an oompah
#             band into a march. It gets its weight from the octave on top and
#             from ringing twice as long instead.
# THE STORM — NOW it squares up, and because it is the only place that does,
#             the square-up reads as the band breaking formation. That is the
#             meteor landing.
live_loop :mason_oompah, sync: :mason_kit do
  bar = tick(:oom) % 16
  root = note([:b3, :b3, :g3, :g3, :e3, :e3, :fs3, :fs3,
               :b3, :b3, :bb3, :bb3, :a3, :a3, :g3, :fs3][bar])
  squat = bar == 3 || bar == 7
  storm = bar >= 12
  slam = bar >= 8 && bar < 12
  use_synth :dsaw
  with_fx :reverb, room: 0.45, mix: 0.18 do
    8.times do |i|                                   # i counts eighth notes
      if squat && i >= 6
        sleep 0.5
        next
      end
      on = storm ? [0, 2, 4, 6].include?(i) : i.odd?
      if on
        chord_notes = bar >= 8 ? [root, root + 7, root + 12] : [root, root + 7]
        if slam
          # Planted rather than clipped: about a beat of ring, off the beat.
          play chord_notes, amp: 0.34, attack: 0.004, sustain: 0.12,
            release: 0.42, cutoff: 98, detune: 0.18
        else
          play chord_notes, amp: 0.3, attack: 0.004, sustain: 0.05,
            release: 0.22, cutoff: 94, detune: 0.18
        end
      end
      sleep 0.5
    end
  end
end

# -------------------------------------------------------------------- lead
# The tune, and the one thing that must stay funny. Skipping in the line,
# barking in the slam, falling out of the sky in the storm. Doubled an octave
# down on a saw from the slam onward, which is where it stops being a waddle
# and starts being a threat.
live_loop :mason_lead, sync: :mason_kit do
  use_synth :blade
  with_fx :reverb, room: 0.5, mix: 0.2 do
    mason_bars.each_with_index do |phrase, bar|
      big = bar >= 8
      phrase.each do |n, dur|
        unless n.nil?
          play n, amp: 0.58, attack: 0.01, sustain: dur * 0.5, release: 0.22,
            cutoff: 106, vibrato_rate: 6
          if big
            synth :dsaw, note: note(n) - 12, amp: 0.26, attack: 0.01,
              sustain: dur * 0.45, release: 0.24, cutoff: 98, detune: 0.16
          end
        end
        sleep dur
      end
    end
  end
end

# ----------------------------------------------------------------- moments
# The four things the fight does, and the only bars where this stops being a
# groove and becomes an event. Every one of these is draft 2's, unchanged in
# rhythm and placement; until change 1 none of them had ever played.
live_loop :mason_moments, sync: :mason_kit do
  bar = tick(:moment) % 16
  if bar == 3 || bar == 7
    # THE SQUAT. The band stops dead and a ripple of pops runs the line off.
    sleep 3
    6.times do |i|
      sample :elec_blup, amp: 0.45, rate: 0.7 + i * 0.12
      sleep 1.0 / 6
    end
  elsif bar == 8 || bar == 10
    # THE PHONE. Two rings, then he swings. Up an octave from draft 2 and
    # louder: a telephone is thin and high, that register is the emptiest part
    # of this mix, and the hat steps aside for these two beats. A comedy beat
    # that cannot be heard is not a joke, it is a texture.
    sleep 2
    use_synth :chiplead
    2.times do
      play :b6, amp: 0.52, release: 0.12
      sleep 0.25
      play :fs6, amp: 0.52, release: 0.12
      sleep 0.25
    end
    sample :drum_heavy_kick, amp: 1.5
    sleep 1
  elsif bar >= 12 && bar < 15
    # THE NUGGETS. Three impacts a bar, landing where the cascades land.
    3.times do |i|
      sample :bd_boom, amp: 1.3 - i * 0.1, rate: 0.75
      sample :drum_splash_hard, amp: 0.3, rate: 1.3
      sleep i == 2 ? 2 : 1
    end
  elsif bar == 15
    # THE WIND-UP. He leans back, and the whole thing goes again. The riser and
    # the melody climb together and the kick lands on the "and" of 4, so the
    # loop point is a ramp into bar 1 rather than a hole in front of it.
    use_synth :dsaw
    rise = play :fs3, amp: 0.4, attack: 0.02, sustain: 3.2, release: 0.5,
      note_slide: 3.2, cutoff: 92, detune: 0.2
    control rise, note: :fs5
    sleep 3.5
    sample :drum_heavy_kick, amp: 1.7
    sample :drum_cymbal_open, amp: 0.6, rate: 1.1
    sleep 0.5
  else
    sleep 4
  end
end
