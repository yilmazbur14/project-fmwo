# CARTER — "The Mark Burns", draft 3 (the one where the silence exists)
# Original music for Project FMWO, written for Sonic Pi 4.x / 5.x.
#
# This is NOT a rewrite of draft 2. 150 bpm, E phrygian, the chord loop, the
# taiko, the sixteenth-note engine, the drone, :hollow for the lead, and the
# whole eight-bar STARE are carried over untouched. Draft 3 changes six things,
# listed below, and leaves everything else alone so the two can be A/B'd.
#
# Two of the six are not taste calls. Change 1 is a bug, and change 2 is the
# consequence of a unit mistake. Between them they mean the most important
# eight seconds of this track have never been heard. Read both before
# listening to anything.
#
# ---------------------------------------------------------------------------
# WHAT CHANGED, AND WHY
#
# 1. THE BAR NUMBER NOW COMES FROM EACH LOOP'S OWN TICK. THIS IS THE BIG ONE.
#    Draft 2 has `bar = look(:bar) % 16` in carter_engine, carter_lead,
#    carter_stabs and carter_demon. Only carter_taiko ever calls tick(:bar).
#    Sonic Pi tick counters are live_loop-local and are NOT inherited: in
#    sonicpi/core.rb, ThreadLocalCounter.get_or_create_counters stores them
#    with __thread_locals.set_local, and look returns (val || 0). Measured
#    against the installed engine, two threads:
#        the loop that ticks :bar eight times    look(:bar) => 7
#        any other live_loop                     look(:bar) => 0
#        a thread spawned from the ticker        look(:bar) => 0
#    So `bar` is 0 in four of the five voices, on every iteration, forever. It
#    is not a race and it is not intermittent — every branch keyed off it is
#    dead. Simulated over a full cycle, draft 2 actually does this:
#        carter_demon    0 events, where the file intends 22
#        carter_lead     52 events, where the file intends 72
#        carter_engine   pinned to the STARE pattern for all sixteen bars
#        carter_stabs    pinned to the off-beat pattern for all sixteen bars
#    THE ENTIRE SHUN GOKU SATSU HAS NEVER PLAYED. Not the footstep, not the
#    held breath, not the eight clones, not the mark burning. Nor has the
#    silence, because the three voices that were written to fall silent for
#    bars 15-16 all test `bar >= 14`, which is never true, so they play
#    straight through it. What the shipped WAV has at bars 15-16 is the taiko
#    dropping out — a breakdown — under an engine that never stops. The one
#    structural idea in this piece, the one that mirrors the fight, is absent
#    from the recording.
#    Also gone: the whole HADO. The lead has only ever played the eight-bar
#    STARE, twice, the second time over the wrong chords (its bars 5-8 sit over
#    the C and Em of the back half instead of the Em and C it was written for).
#    E phrygian is forgiving enough that this reads as brooding rather than
#    wrong, which is why it shipped.
#    CONSEQUENCE FOR REVIEWING THIS DRAFT: bars 9-16 are unreleased, not
#    revised. Judge them as new.
#
# 2. THE SILENCE IS NOW ACTUALLY SILENT.
#    Fixing change 1 makes the engine, the stabs and the lead stop for bars
#    15-16 as written. The drone does not, because the drone has no bar test at
#    all — it just plays and sleeps 16. That 16 is sixteen BEATS, which is four
#    bars, not sixteen bars. So the drone retriggers on bars 1, 5, 9 and 13,
#    and the one that starts on bar 13 has an attack-sustain-release of
#    1 + 10 + 3 = 14 beats, so it is still sounding at beat 62 — straight
#    through bar 15 and most of bar 16 — with room: 0.9 reverb smeared over it.
#    Carter's silence is the load-bearing gesture in this track and it has a
#    pad and a large hall sitting in the middle of it.
#    It is now one note per 16-bar cycle, enveloped to be gone before the
#    silence: attack 2, sustain 42, release 6 is 50 beats, and bar 15 begins at
#    beat 56. The reverb comes down from room 0.9 to 0.7 so the tail clears
#    too. That leaves the drone dying away across bar 13 — the floor goes out
#    one bar before the band does, which is a better way into a stop than
#    everything ending at once.
#
# 3. THE HADO STATES ONE IDEA THREE TIMES INSTEAD OF RUNNING SCALES.
#    Bar 1's call is the best thing in the piece and it is four notes long: a
#    long E, a lean up a semitone to F, back to E, and a drop of a fourth to B.
#    Two pitches and a falling fourth — you could play it with one finger.
#    Draft 2's bars 9 and 10 were both "long note, two eighths down, held note",
#    descending, a third apart: near-interchangeable, and by the twentieth
#    listen they are wallpaper. Bars 9, 11 and 13 now state the call on each of
#    the hado's three chord roots — E, F and C — and nothing was added: the
#    vocabulary got smaller. Bars 10, 12 and 14 are draft 2's, untouched, so
#    they still answer.
#    Bar 13 states it in diminution, at exactly half length, twice. That is how
#    a back half gets bigger rather than merely busier: more notes per bar, but
#    they are the same notes, arriving faster.
#    ONE DELIBERATE INEXACTNESS. The call leans up to the next note of the
#    mode, not up a fixed semitone. Over E that is F (a half step, the phrygian
#    signature); over F it is G and over C it is D (whole steps). Transposing
#    the interval exactly would put an F# and a C# in the piece and would spend
#    the half-step everywhere, and the half-step is the only reason the E-F
#    lean means anything. It stays rare on purpose.
#
# 4. RED AND YELLOW ARE TOLD APART BY COLOUR, NOT BY VOLUME.
#    Bar 16's eight stabs are four real and four ghosts, mirroring the clones
#    in the fight. Draft 2 separated them almost entirely by level — about 11 dB
#    between the groups — which makes the ghosts trivial to ignore. In the
#    fight, red and yellow are equally visible; the whole demand is that you
#    discriminate by colour under time pressure, and you are punished for
#    parrying the wrong one. Music that makes the fakes quiet is not mirroring
#    that, it is solving it for you.
#    So the two groups are now about 3 dB apart and are separated by interval
#    and timbre instead: the real ones hit the E-F minor second, the phrygian
#    bite, bright and short; the ghosts hit an open E-B fifth, darker and
#    thinner. Same weight, different colour, and the ear has to do the work.
#
# 5. THE LOOP SEAM KEEPS THE IMPACT AND ADDS SOMETHING UNRESOLVED ON TOP.
#    This is the case the brief flagged as the harder one, so: the impact is
#    right and it stays. Eric's bar 16 was a cliff because a sustained high
#    note simply stopped and left a hole in front of the downbeat. Carter's is
#    not that. It ends on a deliberate blow, and a blow is allowed to decay —
#    it reads as punctuation, not as running out.
#    The problem was the note it punctuated on. Draft 2's burn is E2 and E3,
#    the tonic doubled: the most closed sound available, a full stop that has
#    to be re-opened from nothing on the other side. So the upper voice moves
#    to F3 — the flat second, the one note in E phrygian that cannot sit still
#    — and gets the longest release in the bar, so it is still ringing when
#    bar 1's engine comes back in on E and resolves it. The low E2 is untouched
#    and still lands the blow. The loop now hands off instead of stopping.
#    This matters more than it used to: all eight themes now import with
#    loop_mode=2, so the engine loops the file itself and the player crosses
#    this seam on every pass rather than only when the fight code forced it.
#
# 6. ROBUSTNESS.
#    Every loop derives its bar from its own tick (change 1). The lead is one
#    16-bar table rather than two tables chosen by a bar test, with its bar
#    arithmetic checked out loud at startup, so the tune cannot drift out of
#    step with the harmony. The silent bars no longer build and tear down an
#    FX node they put nothing into.
#
# ---------------------------------------------------------------------------
# A NOTE ON THE ENUMERATED-OPT BUG, SINCE THIS FILE HAD IT
#
#   `noise:` on :hollow is an index into a list of five noise sources, not a
#   continuous control. It was passed a float here and was fixed earlier today;
#   the whole file has been re-checked rather than just that line, and it is
#   clean. The behaviour is worth writing down correctly, because the note in
#   eric_theme_v3.rb has it backwards. Measured against :hollow's real
#   validator in the installed Sonic Pi:
#       noise: 1     Integer  accepted
#       noise: 1.0   Float    accepted, same source (v_one_of is Array#include?
#                             and 1.0 == 1 in Ruby)
#       noise: 0.5   Float    RAISES "must be one of [0, 1, 2, 3, 4]"
#       noise: 2.5   Float    RAISES
#   So a fractional value does NOT get truncated to a different source, as that
#   note claims — it throws, and a throw inside a live_loop kills that loop and
#   only that loop while every other layer keeps playing. The recording then
#   sounds finished and is silently missing a voice. A whole-number float is
#   the quieter hazard: harmless today, one edit away from fatal. Neither is
#   visible to `ruby -c`. Both are caught by reading, which is what
#   scratchpad/check_fmwo.rb does.
#   1 is brown noise, the darkest of the five, and the right one for breath.
#
# ---------------------------------------------------------------------------
# WHAT THE SHIPPED WAV MEASURES, AND THE CHANGE I DID NOT MAKE BECAUSE OF IT
#
#   Per-band RMS of Assets/Audio/Music/carter_theme.wav, whole file, and the
#   share of total power in each band:
#     40-80 Hz   -18.3  30.6% | 80-160    -25.9   5.3%
#     160-315    -23.6   8.9% | 315-630   -19.7  22.2%
#     630-1250   -23.1  10.0% | 1250-2500 -31.7   1.4%
#     2500-5000  -38.5   0.3% | 5000-10k  -38.2   0.3%
#   Only 35.8% of the power is below 160 Hz. Carter is a completely different
#   animal from the other two: Eric is 90% sub-160 and Mason 80%, and this is
#   the one track in the set whose centre of gravity is in the midrange. The
#   FULLEST band is 315-630 at -19.7; the thinnest are everything above 2.5 kHz.
#   CAVEAT, and it is a big one: because of change 1 this file is missing
#   carter_demon entirely, and its engine, stabs and lead are pinned to their
#   bar-1 behaviour, so this characterises the STARE and nothing else. It is a
#   measurement of eight of the sixteen bars, and the hado — where the lead
#   gains its saw doubling and the stabs square up — is not in it at all.
#   THE CHANGE I TALKED MYSELF OUT OF. Carter's lead runs G4-F6, which is
#   392-1397 Hz, straddling the fullest band in the track. My instinct was to
#   carve room for it by thinning the stabs or lifting the lead. I did not,
#   for three reasons: the back half that would decide the question is not in
#   the file I measured; a mix change stacked on top of five structural ones
#   makes the A/B unreadable; and this is exactly the shape of the mistake the
#   Eric draft caught itself making, in reverse — it assumed a crowded midrange
#   and found a thin one. Here the number says crowded, and the honest response
#   is still to listen to the new recording first. This is the one thing to
#   listen FOR: whether the lead reads over the stabs once the hado exists.
#   What the number did support: dropping the drone's reverb from room 0.9 to
#   0.7 in change 2. That was made for the silence, but a large hall on a pad
#   is also broadband wash landing in the one band this track cannot spare.
#
# ---------------------------------------------------------------------------
# WHAT WAS DELIBERATELY LEFT ALONE
#
#   150 bpm. E phrygian (E F G A B C D) and the flat second the bass leans on.
#   The chord loop. The taiko, including its sixteenths in the hado and its
#   silence in bars 15-16. The engine's two patterns and its distortion.
#   :hollow for the lead and the saw doubling from the hado on. The eight-bar
#   STARE, note for note — its call is the material everything else in this
#   draft is built out of, and it arrives on beat 1 of bar 1 needing nothing.
#   The footstep and the held breath in bar 15; the four-real-four-ghost
#   pattern of the stabs, which is [0, 2, 3, 6] and is asymmetric on purpose.
#   The 16-bar form.
#
#   THE BASS. The brief's checklist includes "a bass that never moves", which
#   was Eric's problem and is not Carter's: the engine already has two distinct
#   patterns, an octave lift, a flat-second push and a chromatic walk down into
#   every beat of the burn. It needed nothing and got nothing.
#
#   THE TEMPO. 150 is slower than Mason's 165 and faster than Eric's 138, and
#   the density is what does the work: sixteenths in the engine throughout,
#   doubled in the taiko once the mark lights. Fast subdivision rather than
#   fast tempo, which is the one idea from the reference video that transfers
#   cleanly to this track.
#
# ---------------------------------------------------------------------------
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: press Rec FIRST, then Run, let it go round
# twice, press Rec again. The cycle is unchanged at 16 bars x 4 beats / 150 bpm
# = 25.6 s, so the existing cut command still applies:
#   python cut_loop.py carter_theme_v3_raw.wav 150 --out <somewhere>/carter_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B. Note
# Carter is the one boss whose fight also plays the user's own reference track
# locally — the composed theme is what a fresh clone hears, and both ship.
#
# 16-bar cycle:
#   Bars 1-8    THE STARE  — Em Em F F Em Em C C. Coiled, not quiet: the engine
#                            is already running, the lead is still holding back.
#   Bars 9-14   THE HADO   — Em Em F F C C, the mark lights. The call comes
#                            back an octave up and then compresses.
#   Bars 15-16  THE DEMON  — everything stops. One footstep, one held breath.
#                            Then eight hits in two beats, four real and four
#                            ghosts, and the mark burns.
# Every voice is a live_loop synced to the taiko, so you can comment one out.

use_bpm 150

# ---------------------------------------------------------------- the tune
# One 16-bar table, written a bar at a time so the arithmetic is visible.
# [note, beats]; nil is a rest. Every bar must sum to 4.
define :carter_bars do
  [
    # ---- THE STARE ----------------------------------------------------------
    [[:e5, 1.5], [:f5, 0.5], [:e5, 1], [:b4, 1]],    # 1  Em — THE CALL. Long E,
                                                     #    lean up a semitone to
                                                     #    F, back, drop a 4th.
                                                     #    Two pitches and a
                                                     #    falling fourth.
    [[:e5, 1], [:g5, 1], [:f5, 1.5], [:e5, 0.5]],    # 2  Em — and it will not
                                                     #    drop the F
    [[:f5, 1.5], [:g5, 0.5], [:a5, 2]],              # 3  F  — leaning on the
                                                     #    flat two
    [[:g5, 1], [:f5, 1], [:e5, 2]],                  # 4  F  — back down
    [[:e5, 0.5], [:f5, 0.5], [:g5, 1], [:f5, 1], [:e5, 1]],
                                                     # 5  Em — circling the cell
    [[:b4, 2], [:e5, 2]],                            # 6  Em — held
    [[:c5, 1], [:b4, 1], [:a4, 1], [:g4, 1]],        # 7  C  — the descent. Left
                                                     #    as plain forward
                                                     #    motion: after all that
                                                     #    circling the ear wants
                                                     #    a straight line.
    [[:a4, 2], [nil, 2]],                            # 8  C  — room for the roll
    # ---- THE HADO -----------------------------------------------------------
    [[:e6, 1.5], [:f6, 0.5], [:e6, 1], [:b5, 1]],    # 9  Em — THE CALL, OCTAVE
                                                     #    UP. Bar 1 exactly, at
                                                     #    full height, the
                                                     #    moment the mark lights.
    [[:c6, 1], [:b5, 0.5], [:a5, 0.5], [:g5, 2]],    # 10 Em — coming down
    [[:f6, 1.5], [:g6, 0.5], [:f6, 1], [:c6, 1]],    # 11 F  — THE CALL FROM F.
                                                     #    Same rhythm, same
                                                     #    falling fourth. The
                                                     #    lean is a whole step
                                                     #    here, not a half —
                                                     #    see change 3.
    [[:b5, 1], [:c6, 1], [:e6, 2]],                  # 12 F  — and it lifts
    [[:c6, 0.75], [:d6, 0.25], [:c6, 0.5], [:g5, 0.5],
     [:c6, 0.75], [:d6, 0.25], [:c6, 0.5], [:g5, 0.5]],
                                                     # 13 C  — THE CALL IN
                                                     #    DIMINUTION. Half
                                                     #    length, stated twice.
                                                     #    Twice the notes, no
                                                     #    new ones.
    [[:e5, 1], [:f5, 1], [:g5, 2]],                  # 14 C  — the cell at its
                                                     #    plainest, walking into
                                                     #    the demon
    # ---- THE DEMON ----------------------------------------------------------
    [[nil, 4]],                                      # 15 — silence. The lead is
                                                     #    out of the way and
                                                     #    stays out.
    [[nil, 4]]                                       # 16 — the stabs and the
                                                     #    burn own this bar
  ]
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
carter_bars.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "carter_theme_v3: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# ------------------------------------------------------------------- taiko
# The body. Eighths in the stare, sixteenths once the mark lights, and a tom
# roll that drags you into each new phrase. Bars 15-16 are empty on purpose.
# Unchanged from draft 2; it was the only loop that already ticked its own bar.
live_loop :carter_taiko do
  bar = tick(:bar) % 16
  hado = bar >= 8
  demon = bar >= 14
  sample :drum_splash_hard, amp: 0.55, rate: 0.5 if bar == 0
  sample :drum_cymbal_open, amp: 0.7, rate: 0.7 if bar == 8
  16.times do |s|
    unless demon
      sample :bd_boom, amp: 1.8, rate: 0.62 if [0, 6, 8, 14].include?(s)
      sample :bd_boom, amp: 1.1, rate: 0.7 if hado && [3, 11].include?(s)
      sample :drum_snare_hard, amp: 0.66, rate: 0.85 if s == 4 || s == 12
      sample :drum_snare_soft, amp: 0.26, rate: 1.25 if hado && [7, 15].include?(s)
      sample :drum_cymbal_closed, amp: 0.2, rate: 0.75 if hado ? s.odd? : s % 4 == 2
      sample :drum_tom_lo_hard, amp: 0.85, rate: 0.7 if (bar == 7 || bar == 13) && s >= 12
    end
    sleep 0.25
  end
end

# ------------------------------------------------------------------ engine
# Sixteenths on the root with the flat second shoving in against it, resonant
# and distorted, accented off the kick. This is what makes the silence mean
# anything — which is why it has to actually stop for it, and now does.
live_loop :carter_engine, sync: :carter_taiko do
  bar = tick(:eng) % 16
  root = note([:e1, :e1, :f1, :f1, :e1, :e1, :c1, :c1,
               :e1, :e1, :f1, :f1, :c1, :c1, :e1, :e1][bar])
  # Semitones off the bar root; nil is a rest. The stare breathes; the burn
  # does not, and it walks down chromatically into every beat.
  stare = [0, nil, 0, 12, nil, 0, 0, nil, 0, nil, 0, 12, 0, nil, 1, 0]
  burn  = [0, 0, 12, 0, 1, 0, 12, 0, 0, 0, 12, 0, 3, 2, 1, 0]
  if bar >= 14
    sleep 4                                          # THE DEMON. Gone.
  else
    use_synth :tb303
    with_fx :distortion, distort: 0.42, mix: 0.55 do
      (bar >= 8 ? burn : stare).each_with_index do |off, s|
        unless off.nil?
          play root + off, amp: (s % 4 == 0 ? 0.9 : 0.6),
            attack: 0.004, sustain: 0.05, release: 0.13, res: 0.88,
            cutoff: 70 + (bar >= 8 ? 22 : 0) + (s % 4 == 0 ? 16 : 0)
        end
        sleep 0.25
      end
    end
  end
end

# ------------------------------------------------------------------- drone
# The low E under everything is Carter standing there. It is the floor, not the
# room. One note per 16-bar cycle now, rather than one every four bars with a
# fourteen-beat envelope, which is what used to leave a pad and a large hall
# sitting on top of the silence. It is written to be gone by bar 14: the floor
# goes out one bar before the band does.
live_loop :carter_drone, sync: :carter_taiko do
  # Was :dark_ambience with ring: 0.4. Its ring gives that synth a vocal formant
  # - a low muttering growl - and under a 42-beat sustain it sat there talking
  # through the whole cycle. The user heard it as demonic talking and wanted it
  # gone, which is right: the drone's job is to be the floor Carter stands on,
  # and a floor should not have a voice. :tri through a low-pass is the same
  # note with no character of its own.
  use_synth :tri
  with_fx :lpf, cutoff: 58 do
    with_fx :reverb, room: 0.5, mix: 0.2 do
      # 2 + 42 + 6 = 50 beats. Bar 15 starts at beat 56, and the smaller room
      # clears its tail well inside the four beats between.
      play :e1, amp: 0.34, attack: 2, sustain: 42, release: 6
    end
  end
  sleep 64
end

# -------------------------------------------------------------------- lead
# :hollow keeps the breathy shakuhachi edge; from the hado it is doubled an
# octave down on a saw, so there is a body behind the breath.
live_loop :carter_lead, sync: :carter_taiko do
  use_synth :hollow
  with_fx :reverb, room: 0.75, mix: 0.4 do
    carter_bars.each_with_index do |phrase, bar|
      big = bar >= 8
      phrase.each do |n, dur|
        unless n.nil?
          play n, amp: 0.5, attack: 0.05, sustain: dur * 0.5, release: dur * 0.35,
            res: 0.35, noise: 1
          if big
            synth :dsaw, note: note(n) - 12, amp: 0.3, attack: 0.02,
              sustain: dur * 0.45, release: 0.3, cutoff: 96, detune: 0.18
          end
        end
        sleep dur
      end
    end
  end
end

# ------------------------------------------------------------------- stabs
# Open fifths hit hard and cut short: someone appearing where he was not. Off
# the beat while he is staring, square on it once the mark is lit. Unchanged
# from draft 2 apart from knowing what bar it is in, which is what lets it
# square up at all and what lets it get out of the way for the demon.
live_loop :carter_stabs, sync: :carter_taiko do
  bar = tick(:stab) % 16
  if bar >= 14
    sleep 4
  else
    root = note([:e3, :e3, :f3, :f3, :e3, :e3, :c3, :c3,
                 :e3, :e3, :f3, :f3, :c3, :c3, :e3, :e3][bar])
    use_synth :dsaw
    with_fx :reverb, room: 0.6, mix: 0.22 do
      8.times do |i|
        on = bar >= 8 ? [0, 2, 3, 5, 6, 7].include?(i) : [3, 7].include?(i)
        play [root, root + 7], amp: 0.34, attack: 0.002, release: 0.2,
          cutoff: 98, detune: 0.2 if on
        sleep 0.5
      end
    end
  end
end

# ------------------------------------------------------------------- demon
# BARS 15-16. THE SHUN GOKU SATSU. Every other voice is written to fall silent
# here, and as of draft 3 every other voice actually does.
#
# One footstep, one held breath. Then eight hits land in two beats: four real
# and four ghosts, exactly like the clone sequence in the fight, where red must
# be parried and yellow must not. Then the mark burns and it starts again.
live_loop :carter_demon, sync: :carter_taiko do
  bar = tick(:demon) % 16
  if bar == 14
    sample :drum_tom_lo_hard, amp: 1.0, rate: 0.5   # the step
    sleep 2
    sample :ambi_dark_woosh, amp: 0.7, rate: 0.7    # the breath
    sleep 2
  elsif bar == 15
    use_synth :dsaw
    with_fx :distortion, distort: 0.5, mix: 0.6 do
      8.times do |i|
        real = [0, 2, 3, 6].include?(i)   # red: the ones you have to catch
        if real
          # The E-F minor second: the phrygian bite, bright and short.
          sample :elec_hi_snare, amp: 0.85, rate: 0.9
          play [:e3, :f3], amp: 0.46, attack: 0.001,
            release: 0.16, cutoff: 104, detune: 0.25
        else
          # An open E-B fifth: same weight, darker and hollower. Roughly 3 dB
          # down rather than draft 2's 11, so the ear has to tell them apart by
          # colour under time pressure, which is the whole point of the attack.
          sample :elec_hi_snare, amp: 0.6, rate: 1.35
          play [:e3, :b3], amp: 0.32, attack: 0.001,
            release: 0.13, cutoff: 86, detune: 0.25
        end
        sleep 0.25
      end
    end
    # And the mark burns. E2 lands the blow and is allowed to decay; the F3
    # above it is the flat second, left with the longest release in the piece
    # so it is still hanging when bar 1's engine comes back in on E and
    # resolves it. The loop hands off rather than stopping.
    sample :drum_heavy_kick, amp: 1.8
    sample :drum_splash_hard, amp: 0.8, rate: 0.55
    synth :dsaw, note: :e2, amp: 0.55, attack: 0.002, release: 1.8,
      cutoff: 110, detune: 0.3
    synth :dsaw, note: :f3, amp: 0.34, attack: 0.002, release: 3.0,
      cutoff: 98, detune: 0.3
    sleep 2
  else
    sleep 4
  end
end
