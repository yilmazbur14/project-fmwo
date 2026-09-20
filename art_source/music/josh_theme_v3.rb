# JOSH — "Three Card Trick", draft 3 (the trick actually works now)
# Original music for Project FMWO, written for Sonic Pi 4.x.
#
# This is NOT a rewrite. Draft 2's tempo, key, palette, drums, every note of
# the tune and every structural idea are carried over. But draft 2 had two
# faults that between them meant more than half of what is written in the file
# has never been heard, and the best idea in it — "the reveal" — was landing on
# the wrong chord. Four things change.
#
# WHAT CHANGED, AND WHY
#
# 1. THE SWITCH, THE FLOURISH AND THE FAN NOW EXIST.
#    Draft 2 has one loop, :josh_table, that owns the bar counter with
#    `tick(:bar)`, and five loops that read it back with `look(:bar)`. That read
#    does not work. Sonic Pi's ticks are live_loop-local — core.rb's
#    ThreadLocalCounter keeps them in a thread variable, and `look` on a key
#    THIS loop has never ticked returns `(val || 0)`, i.e. 0, forever. So in the
#    shipped recording:
#      :josh_hook     `big` is never true, so it plays the 4-bar DEAL phrase
#                     four times and THE ENTIRE SWITCH — six bars of melody,
#                     the reveal, the climb — has never played
#      :josh_flourish `[3,7,11].include?(0)` is false, so it never fires once
#      :josh_fan      neither bar 15 nor bar 16 ever arrives: no run up the
#                     deck, no twelve cards, no landing
#      :josh_deck     never rests, so the fan would have had no room anyway
#      :josh_shuffle  never takes the switch's octave climb
#    Measured, not assumed. The shipped josh_theme.wav is 0.901 chroma
#    self-similar at an 8-bar lag; Eric's, which genuinely changes material
#    halfway, is 0.199. And there is no splash cymbal anywhere in the file — the
#    loudest four bars sit within 0.3 dB of each other — where the fan's
#    :drum_splash_hard would tower over everything. The back half of this track
#    is simply the front half again.
#    Every loop now derives its bar from its own tick. :josh_hook is one 64-beat
#    pass over sixteen written-out bars, which is also how draft 2's phrases
#    stopped lining up with the chords — see change 2.
#
#    WHICH MEANS MOST OF THIS IS UNRELEASED, NOT REVISED. Be exact about what
#    the shipped recording actually contains: the chord ROOTS are right in all
#    sixteen bars (every voice takes its root from its own .tick, not from
#    :bar) and :josh_table has always played its full sixteen. But the TUNE is
#    the four-bar deal phrase four times over — the switch, the flourish and the
#    fan have never sounded at all. So any judgement anyone has formed about
#    this theme's melody is a judgement about bars 1-4. Changes 3 and 4 touch
#    the flourish and the fan, which nobody has heard, so there is no "before"
#    to A/B them against; change 2 moves chords under a tune that has been
#    heard, and that is the one to listen to critically.
#
# 2. THE HARMONY NOW ARRIVES WHERE THE MELODY EXPECTS IT. This is the musical
#    change, and it is the one that matters.
#    Draft 2's accompaniment runs an EIGHT-bar chord ring, Am F C G Am F Dm E,
#    twice. Its melody is a FOUR-bar phrase played twice and then a SIX-bar
#    phrase. Those do not line up, and the melody's own bar labels say so:
#      melody says    bar 11 "Dm"   bar 12 "E"   bar 13 "E"   bar 14 "E"
#      ring plays     bar 11  C     bar 12  G    bar 13  Am   bar 14  F
#    Four of the switch's six bars were written against chords that were not
#    playing. The damage is concentrated on exactly the note the section is
#    named for: bar 12's G#5, "the reveal", sounds against a G MAJOR chord — the
#    shuffle's G4, the deck's G1 and the bass's G2 at once. G against G# is a
#    minor ninth, the harshest interval available, on the money note. Bar 8 had
#    the same cross-relation the other way round: the melody's G natural against
#    the E major chord's G#.
#    The fix is not to touch the melody. The melody is right and its labels are
#    the composer's own statement of intent; the ring is what is wrong. The
#    progression is now sixteen bars written out in full, and every bar of tune
#    sits on the chord it was written for. The real E major chord — the one the
#    whole switch is aiming at — now arrives at bar 12 underneath the G#,
#    instead of at bar 16 where nothing is playing over it.
#    A side effect worth naming: bars 5-8 become Am F C G, the same as 1-4,
#    where draft 2 had Am F Dm E. The deal is now a four-bar phrase stated twice
#    over the same chords. That is more repetitive on paper and better in the
#    ear, because the alternative was keeping the bar 8 clash; and change 3
#    gives those two statements different tails anyway.
#
# 3. THE FLOURISH IS ONE IDEA AT THREE HEIGHTS INSTEAD OF THE SAME RUN THRICE.
#    Draft 2's flourish fires at bars 4, 8 and 12 and plays the identical eight
#    notes every time — the same gesture three times a loop, twenty-odd times an
#    attempt. That is the "four interchangeable phrases become wallpaper" fault
#    from Eric's draft 3, in its purest form. It now starts from A, then C, then
#    E — the notes of the A minor triad spelled out across the loop — with the
#    same rhythm, the same shape and the same scale. Nothing was added: it tops
#    out at D6, then E6, then A6, so it also climbs into the switch's climax.
#
# 4. THE LOOP NOW TURNS OVER INSTEAD OF STOPPING DEAD.
#    Draft 2's bar 16 accelerates twelve cards across 2.2 beats, lands a low A
#    power chord with a splash and a heavy kick, and then holds 1.8 beats of
#    ring-out before the loop point. Harmonically that is tonic arriving on
#    tonic; structurally it is the biggest gesture in the piece happening, and
#    then the track coasting into its own restart. A fight runs several loops
#    long, so the player hears that full stop over and over.
#    The twelve cards now accelerate across three full beats — the same
#    accelerando, stretched — so the landing falls ON beat 4 and its 1.4-beat
#    release rings across the bar line into bar 1's downbeat. And the last card
#    before the landing is G#5, the leading tone, resolving up into the A. The
#    landing pitches, the splash, the kick and the card rhythm's character are
#    all unchanged; what changed is where in the bar it happens.
#    That G# is also the second statement of the reveal's note. It is the only
#    accidental in the piece and it now appears twice — at the reveal, and as
#    the last thing you hear before the loop turns — which makes it Josh's tell
#    rather than a one-off.
#
# WHAT THE SHIPPED WAV ACTUALLY MEASURES
#   Per-band RMS at the in-game gain (-7 dB), with Eric's beside it:
#     band        JOSH    ERIC
#     40-80 Hz    -21.1  -23.0
#     80-160      -25.4  -33.5
#     160-315     -29.2  -44.1
#     315-630     -31.8  -39.5
#     630-1.25k   -32.1  -38.0
#     1.25-2.5k   -38.2  -39.3
#     2.5-5k      -38.3  -37.5
#     5-10k       -42.4  -53.7
#   What this stopped me doing: I had a note written about brightening the deck,
#   because :tb303 through :distortion reads as thin on small speakers. It is
#   not thin — 160-1.25k is 7 to 15 dB hotter here than in Eric, and this is
#   already the most midrange-forward theme of the three. What it is, is BUSY:
#   the shuffle runs sixteenths on :pluck through the whole loop and the deck
#   runs sixteenths under it. Adding brightness would have been adding a fourth
#   thing to a band with three things in it.
#   Left alone deliberately: 2.5-5k at -38.3, which is where the parry lives.
#   Measured: parry_hit_1.wav puts 97.3% of its energy in 2.5-5 kHz, and this
#   track sits within a decibel of Eric there, over which the parry reads fine.
#   Nothing to fix, and no reason to add air.
#   Read the whole table with a caveat, though: it is measured off a recording
#   whose melody is bars 1-4 four times and which contains no flourish and no
#   fan. It characterises this arrangement's floor, not its ceiling. A take made
#   from this file will read hotter, especially in the back half.
#
# WHAT THIS FIGHT'S OWN SOUNDS NEED — WHICH IS NOT WHAT ERIC'S NEEDED
#   Eric's draft 3 opened a hole on alternate beats in 500 Hz - 2.5 kHz for the
#   finisher's mash riser and the Knight Breaker sting. I did not copy that, and
#   it would have been a mistake to: finisher_charge_loop, finisher_bar_1/2/3
#   and knight_breaker_sting are all gated on the player's feel_v2 flag, which
#   only Eric's fight and the training room set. In Josh's fight the daze and
#   the Q/W mash make NO sound at all, and neither does the dash whoosh or the
#   punch whoosh. Thinning this mix for them would have been making room for
#   sounds that never arrive.
#   What this fight does play, constantly, is whirlwind_whoosh.ogg on three
#   separate players pitched to 1.3, 1.6 and 1.8 — the glide, the card throw and
#   the monte shuffle. A whoosh pitched up by that much is bright, and this
#   track's 5-10 kHz sits at -42.4 against Eric's -53.7: 11 dB hotter in exactly
#   the region Josh's most frequent sound effect occupies. That is the one
#   genuine spectral risk in this theme and I have NOT acted on it, for two
#   reasons. The whooshes are shared placeholders — Josh has no sounds of his
#   own yet — and there is no Ogg decoder on this machine, so I could not
#   measure where that file's energy actually sits and will not cut a mix on an
#   assumption. Worth re-checking the moment real Josh SFX exist; if it does
#   turn out to be a problem the cheap lever is :drum_cymbal_closed at amp 0.2
#   on every odd sixteenth, which is the only continuous thing up there.
#   One more thing to know rather than act on: every sound in this game, music
#   included, goes through ONE bus — Master, with a single AudioEffectHard-
#   Limiter. There is no Music bus, and unlike the Greyson fight this one does
#   no ducking at all. Change 1 restores a fan that fires drum_heavy_kick at 1.6
#   into that limiter once a loop, so check the peaks on the new take.
#   Worth knowing and NOT a composition problem: the shipped josh_theme.wav is
#   not cut on a downbeat. Its first bar is nearly silent for three beats and
#   then slams — that is the tail of :josh_table's two-bar rest, so the cut
#   landed inside the breakdown rather than on bar 1. Re-record with Rec pressed
#   BEFORE Run so cut_loop.py finds the true downbeat.
#
# WHAT WAS DELIBERATELY LEFT ALONE
#   168 bpm. A minor. Every pitch and duration in the hook, in both phrases.
#   The riffled-deck shuffle and its two patterns. The syncopated :fm bass, whose
#   seven-note bar (0.75 0.25 0.5 0.75 0.5 0.25 1.0) is the misdirection and is
#   the best thing in the arrangement. :pluck / :tb303 / :fm / :blade / :dsaw.
#   The distortion on the deck. The drum kit and every amp in it. The two-bar
#   breakdown for the fan. The 16-bar form. Josh is the fastest theme in the set
#   at 168 and stays that way.
#
# NOT DONE, ON PURPOSE: a shared motif with Eric's theme. See the report; the
# natural landing spot here is bar 9, and unlike Greyson it is nearly free.
#
# HOW TO PLAY IT: paste this whole file into a Sonic Pi buffer and press Run.
# Press Stop to end it. To record: press Rec FIRST, then Run, let it go round
# twice, then Rec again to save a WAV — that ordering is what makes the cut land
# on the downbeat. The cycle is unchanged at 16 bars x 4 beats / 168 bpm =
# 22.8571 s, so the existing cut command still applies:
#   python cut_loop.py josh_theme_v3_raw.wav 168 --out <somewhere>/josh_theme_v3.wav
# Do not overwrite the shipped WAV with this; it is a proposal to A/B.
#
# The form, at 168 bpm, 16 bars:
#   Bars 1-8    THE DEAL   — Am F C G, twice. The hook over the shuffle.
#   Bars 9-14   THE SWITCH — Am F Dm E E E. The same hook a third higher and
#                            the harmony turning under it: the trick revealed.
#   Bars 15-16  THE FAN    — the run up the deck, then every card at once.
# Every voice is a live_loop synced to the shuffle, so you can comment one out.
# Draft 2 is beside this file as josh_theme.rb.

use_bpm 168

# ------------------------------------------------------- the shared harmony
# Sixteen bars written out in full, read by every voice. Draft 2 kept this as an
# eight-bar ring and the melody drifted against it; a list this length cannot
# silently disagree with a sixteen-bar tune, which is the whole point of writing
# it this way rather than as a clever short ring.
#
# Am F C G | Am F C G | Am F Dm E | E E Am Am
JOSH_CHORDS = [%i[a4 minor], %i[f4 major], %i[c5 major], %i[g4 major],
               %i[a4 minor], %i[f4 major], %i[c5 major], %i[g4 major],
               %i[a4 minor], %i[f4 major], %i[d4 minor], %i[e4 major],
               %i[e4 major], %i[e4 major], %i[a4 minor], %i[a4 minor]].freeze

JOSH_BASS = [:a2, :f2, :c3, :g2, :a2, :f2, :c3, :g2,
             :a2, :f2, :d2, :e2, :e2, :e2, :a2, :a2].freeze

# The deck is the bass an octave down — the floor under the floor.
JOSH_DECK = JOSH_BASS.map { |n| n - 12 }.freeze

# ---------------------------------------------------------------- the tune
# Written one bar at a time so the arithmetic is visible and, more to the point,
# so each bar sits next to the chord it is played over. Every bar sums to 4.
# Not one pitch or duration differs from draft 2. [note, beats]; nil is a rest.
define :josh_hook_bars do
  deal = [
    [[:a4, 0.5], [:c5, 0.5], [:e5, 0.75], [:d5, 0.25], [:c5, 1], [:b4, 1]],
    # Am — it climbs, then hesitates on the B.
    [[:c5, 0.5], [:f5, 0.5], [:e5, 1], [:c5, 1], [:b4, 0.5], [:c5, 0.5]],
    # F  — the same climb from a step up, and it will not resolve.
    [[:g4, 0.5], [:c5, 0.5], [:g5, 0.75], [:f5, 0.25], [:e5, 1], [:d5, 1]],
    # C  — bar 1's shape again, wider: the leap is a fifth now, not a third.
    [[:b4, 1], [:d5, 1], [:g5, 1], [:b5, 1]]
    # G  — straight up the chord. The only bar with no sidestep in it, which is
    #      why it works as the phrase's exit.
  ]
  switch = [
    [[:a5, 0.5], [:g5, 0.5], [:e5, 0.75], [:d5, 0.25], [:c5, 1], [:e5, 1]],
    #  9 Am — the hook from the top down instead of the bottom up.
    [[:f5, 0.5], [:a5, 0.5], [:g5, 1], [:f5, 1], [:e5, 0.5], [:f5, 0.5]],
    # 10 F  — answered.
    [[:d5, 0.5], [:f5, 0.5], [:a5, 0.75], [:g5, 0.25], [:f5, 1], [:e5, 1]],
    # 11 Dm — and the floor moves: this is the first bar the deal never had.
    #    Draft 2 played this over a C major chord.
    [[:e5, 1], [:gs5, 1], [:a5, 1], [:c6, 1]],
    # 12 E  — THE REVEAL. The G# is the only accidental in the piece and the
    #    whole switch exists to get to it. Draft 2 sounded it against a G major
    #    chord, a minor ninth; it is the third of the chord now, which is what
    #    it was written to be.
    [[:d6, 0.5], [:c6, 0.5], [:b5, 1], [:a5, 1], [:gs5, 1]],
    # 13 E  — pressing. Straight down the E7 and back onto the G#.
    [[:a5, 2], [:e5, 2]]
    # 14 E  — into the fan. An eleventh falling to the root: the suspension
    #    holds the whole bar and then gives way, which is the hand-off.
  ]
  rest = [[[nil, 4]], [[nil, 4]]]   # 15-16: the fan owns these two bars
  deal + deal + switch + rest
end

# Bar-length check. Runs once, prints nothing when the tune is correct.
josh_hook_bars.each_with_index do |phrase, i|
  total = phrase.inject(0.0) { |t, (_, dur)| t + dur }
  puts "josh_theme_v3: BAR #{i + 1} sums to #{total}, not 4" unless total == 4.0
end

# ------------------------------------------------------------ the shuffle
# Sixteenth-note arpeggios, like a deck being riffled. This is the engine, and
# in the switch it climbs an octave every second beat instead of staying put —
# which it never did before, because the branch was chosen by a frozen look().
live_loop :josh_shuffle do
  bar = tick(:bar) % 16
  ch = chord(*JOSH_CHORDS[bar])
  deal   = [0, 1, 2, 1, 2, 1, 0, 2]
  switch = [0, 2, 1, 2, 0, 1, 2, 1]
  use_synth :pluck
  with_fx :reverb, room: 0.5, mix: 0.18 do
    16.times do |i|
      n = ch[(bar >= 8 ? switch : deal)[i % 8]]
      n += 12 if bar >= 8 ? i % 4 >= 2 : i % 8 >= 6
      play n, amp: (i % 4 == 0 ? 0.55 : 0.34), coef: 0.4
      sleep 0.25
    end
  end
end

# --------------------------------------------------------------- the deck
# The low end draft 1 did not have. A distorted saw under the bass, running
# sixteenths with the octave snapping up into the gaps, so the floor is always
# moving even when the hook is resting. It steps aside for the fan — which it
# also never did, so the fan would have had nowhere to land even if it had run.
live_loop :josh_deck, sync: :josh_shuffle do
  bar = tick(:deck) % 16
  root = JOSH_DECK[bar]
  # Semitones off the bar root; nil is a rest.
  deal   = [0, nil, 0, 12, 0, nil, 0, 7, 0, nil, 0, 12, 0, 7, 0, nil]
  switch = [0, 0, 12, 0, 7, 0, 12, 0, 0, 0, 12, 7, 0, 12, 7, 0]
  use_synth :tb303
  with_fx :distortion, distort: 0.35, mix: 0.45 do
    if bar >= 14
      sleep 4
    else
      (bar >= 8 ? switch : deal).each_with_index do |off, s|
        unless off.nil?
          play root + off, amp: (s % 4 == 0 ? 0.85 : 0.55),
            attack: 0.004, sustain: 0.04, release: 0.12, res: 0.8,
            cutoff: 74 + (bar >= 8 ? 20 : 0) + (s % 4 == 0 ? 14 : 0)
        end
        sleep 0.25
      end
    end
  end
end

# --------------------------------------------------------------- the bass
# Kept from draft 1, because the syncopation is the misdirection: it never
# lands on the beat you brace for. Seven notes to the bar, none of them where
# the kick is. It sits on top of the deck.
live_loop :josh_bass, sync: :josh_shuffle do
  bar = tick(:bassbar) % 16
  root = JOSH_BASS[bar]
  use_synth :fm
  with_fx :lpf, cutoff: 92 do
    # 0.75 + 0.25 + 0.5 + 0.75 + 0.5 + 0.25 + 1.0 = 4.0 beats, one bar.
    [0.75, 0.25, 0.5, 0.75, 0.5, 0.25, 1.0].each do |dur|
      play root, amp: 0.7, attack: 0.005, release: dur * 0.8, divisor: 1.2, depth: 1.5
      sleep dur
    end
  end
end

# -------------------------------------------------------------- the table
# Four on the floor under the deal, offbeat kicks in the switch, and a snap
# where every card lands. This loop ticked its own :bar and was the one voice
# in draft 2 that always behaved.
live_loop :josh_table, sync: :josh_shuffle do
  bar = tick(:table) % 16
  switch = bar >= 8
  sample :drum_cymbal_open, amp: 0.45, rate: 1.15 if bar == 0 || bar == 8
  if bar >= 14
    sleep 4
  else
    16.times do |s|
      sample :bd_haus, amp: 1.45 if s % 4 == 0
      sample :bd_haus, amp: 0.8 if switch && [6, 14].include?(s)
      sample :drum_snare_hard, amp: 0.62, rate: 1.1 if s == 4 || s == 12
      sample :perc_snap, amp: 0.5, rate: 0.95 if s == 8
      sample :perc_snap, amp: 0.3, rate: 1.35 if switch && [3, 11].include?(s)
      sample :drum_cymbal_closed, amp: 0.2, rate: 1.2 if s.odd?
      sample :drum_tom_hi_hard, amp: 0.55, rate: 1.1 if bar == 13 && s >= 12
      sleep 0.25
    end
  end
end

# -------------------------------------------------------------------- hook
# The tune. It climbs, hesitates, then climbs further, never resolving where you
# expect. Doubled an octave down on a saw from the switch, which is the moment
# he stops performing and starts winning.
#
# One 64-beat pass over the sixteen written bars. Draft 2 ran three different
# iteration lengths (16, 16, 24 and 8 beats) and picked between them by reading
# another loop's tick, which is both why the switch never played and why the
# phrases could drift against the chords without anything complaining.
live_loop :josh_hook, sync: :josh_shuffle do
  with_fx :reverb, room: 0.55, mix: 0.22 do
    use_synth :blade
    josh_hook_bars.each_with_index do |phrase, bar|
      big = bar >= 8
      phrase.each do |n, dur|
        unless n.nil?
          play n, amp: 0.62, attack: 0.01, sustain: dur * 0.5, release: 0.25,
            cutoff: 110, vibrato_rate: 5
          if big
            synth :dsaw, note: note(n) - 12, amp: 0.26, attack: 0.01,
              sustain: dur * 0.45, release: 0.25, cutoff: 100, detune: 0.16
          end
        end
        sleep dur
      end
    end
  end
end

# ----------------------------------------------------------- the flourish
# Every fourth bar of the deal and the switch, a fast run up the deck. Pure
# show-off, and the only thing in draft 1 that already had the right energy.
#
# Draft 2 played the identical eight notes at bars 4, 8 and 12. Same scale, same
# rhythm, same shape — but it now starts on A, then C, then E, the notes of the
# A minor triad, so one gesture is stated three times at three heights instead
# of three times at one. It tops out at D6, E6 and then A6, which also means the
# flourish climbs into the switch's climax rather than marking time through it.
live_loop :josh_flourish, sync: :josh_shuffle do
  bar = tick(:flourish) % 16
  at = [3, 7, 11].index(bar)
  if at.nil?
    sleep 4
  else
    use_synth :pluck
    deck = scale(:a4, :minor_pentatonic, num_octaves: 3).to_a
    run = deck[[0, 1, 3][at], 8]                 # from A, then C, then E
    sleep 4 - run.length * 0.125                 # the run is the bar's last beat
    run.each_with_index do |n, i|
      play n, amp: 0.45 - i * 0.02, coef: 0.55
      sleep 0.125
    end
  end
end

# --------------------------------------------------------------- the fan
# BARS 15-16. The deck goes up and every card comes down at once.
#
# The table and the deck drop out here, so the run has room: two octaves up the
# scale in thirty-seconds, a held breath, and then twelve cards landing in a bar,
# accelerating, because he is not dealing any more.
#
# The acceleration now spans three beats rather than 2.2, so the landing falls
# on beat 4 and rings over the bar line into bar 1 instead of stopping 1.8 beats
# short of it. Same twelve cards, same landing, same splash — later, and leaning
# forward. The last card before it is G#5, the reveal's note, resolving up into
# the A: the loop's final gesture is a leading tone, not a full stop.
live_loop :josh_fan, sync: :josh_shuffle do
  bar = tick(:fan) % 16
  if bar == 14
    use_synth :pluck
    sample :perc_swash, amp: 0.5, rate: 1.2
    deck_run = scale(:a4, :minor, num_octaves: 2).to_a
    deck_run.each do |n|
      play n, amp: 0.5, coef: 0.5
      sleep 0.125
    end
    sample :drum_cymbal_open, amp: 0.4, rate: 1.3
    sleep 4 - deck_run.length * 0.125
  elsif bar == 15
    use_synth :dsaw
    with_fx :distortion, distort: 0.4, mix: 0.5 do
      # Twelve gaps falling 0.36 -> 0.14 by a steady 0.02: sums to exactly 3.0,
      # so card twelve lands on beat 4 and the chord gets the last beat.
      gaps  = [0.36, 0.34, 0.32, 0.30, 0.28, 0.26, 0.24, 0.22, 0.20, 0.18, 0.16, 0.14]
      cards = [:a4, :c5, :e5, :a5, :g5, :e5, :c5, :a4, :e4, :c5, :e5, :gs5]
      gaps.each_with_index do |gap, i|
        sample :perc_snap, amp: 0.4 + i * 0.03, rate: 1.0 + i * 0.05
        play cards[i], amp: 0.3 + i * 0.02, attack: 0.002, release: 0.1,
          cutoff: 100, detune: 0.2
        sleep gap
      end
      sample :drum_heavy_kick, amp: 1.6
      sample :drum_splash_hard, amp: 0.6, rate: 1.0
      play [:a2, :e3, :a3], amp: 0.5, attack: 0.002, release: 1.4,
        cutoff: 112, detune: 0.25
      sleep 4 - gaps.sum
    end
  else
    sleep 4
  end
end
