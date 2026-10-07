extends RefCounted

# Every number and switch Jordan's last phase plays on - the Puppet Master (JordanGodScript, its state machine and
# JordanCombo, the base of every combination attack): his health, the flow, the layers and their z, the summon, the
# strings, the rifts, the punch-out, his animations and fingertips, his defeat and his sounds. Points are screen px
# (1920x1080); texel points are on his own 320x224 frame, which is drawn with its ANCHOR texel's top-left corner on
# GOD_POINT at SCALE, as the finale draws him. The puppets' own numbers are JordanPuppetLayout's.
#
# THE ART (approved by the user 2026-09-28: "blue, strings on back only, bigger hands, defaults fine"): his puppeteer
# sheets, the strings and the rifts are the puppeteer artist's (art_source/jordan_puppeteer/). Each piece is on its
# USE_FINAL_* switch and plays only once its files - and for his sheets the generated fingertip table,
# Scripts/JordanGodTips.gd - are in and imported; until then its stand-in plays, as listed with it.

const FinaleLayout := preload("res://Scripts/JordanFinaleLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")

const SCALE := 3.0
# How big he is drawn, px a texel, apart from the world's SCALE (the puppets, the strings' grid, the rifts): his body,
# his aura, his rune circle and where it sits on him, his fingertips and his flinch all go through it, so drawing him
# smaller - the puppets hanging clearly below him - is this and GOD_POINT. The finale draws its own god at 3x.
const GOD_SCALE := 3.0
const VIEW_SIZE := Vector2(1920, 1080)
const FIGHT_SCENE := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const CARD_SCENE := "res://Scenes/Core/ToBeContinuedScene.tscn"

#THE FIGHT
# Every uppercut on a puppet takes exactly one off him, whatever the finisher's share would have been: the one knob on
# how long the fight is. 20 until the user raised every boss's health 25% (2026-09-30); 30 since the new mash
# (2026-10-04), which pays about two uppercuts a payoff, landed the fight back on the user's 9/10.
const UPPERCUTS_TO_BEAT := 30
const HUD_KEY := &"jordan"
const HUD_PLATE := &"jordan"
const HUD_TEXT := "JORDAN"
# Where the finale leaves them: the god hovering on his point (his anchor texel's top-left corner, as the finale places
# him: the same point today, a knob of this fight's own), the player on the void's mark facing UP. The finale's mark is
# its story player's soles, 39 px under the middle of its frame, and MainPlayer's origin is the middle of its own: so
# the player stands 39 px up from the mark, drawn on exactly the finale's last frame.
const GOD_POINT := Vector2(960, 600)
const PLAYER_START := FinaleLayout.VOID_PLAYER_MARK - Vector2(0, 39)

#THE VIEW (the user's staging option B, 2026-09-28: art_source/jordan_puppeteer/staging/staging.json)
# The whole fight is drawn at 2/3 - every 3x sprite at 2 px a texel - centred on VIEW_FOCUS, so the view shows world x
# -480 to 2400 and y -6 to 1614: Jordan across the top at 2x on the screen and his puppets hanging well below him
# (ScreenView.set_base). It opens framed exactly as the finale's last frame, at 1, and pulls back to it over PULL_BACK,
# easing out, as the fight begins. The staging's screen px are world = screen x 1.5 + (-480, -6).
const VIEW_ZOOM := 2.0 / 3.0
const VIEW_FOCUS := Vector2(960, 804)
const PULL_BACK := 1.2
# The floor the player walks, the arena's invisible walls moved out to it (VoidArena.dress): the inner faces of the
# four walls, the staging's floor (screen 70, 70 to 1850, 1010).
const FLOOR := Rect2(-375, 99, 2670, 1410)
# Open: the loop from the fight's first frame, the HUD fading in, then the player is theirs. Idle between attacks.
const OPEN_TIME := 1.0
const HUD_FADE_IN := 0.5
const HUD_FADE := 0.3
# His boss bar stays at the top centre and goes see-through while he is behind it (the user, 2026-09-28: "keep it at
# the top centre but make it see-through when he's behind it"): while his body's drawn pixels on screen overlap the
# block's, the whole block eases to HUD_SEE_THROUGH_ALPHA, and back to 1 once he is clear, over HUD_SEE_THROUGH_FADE
# real seconds (JordanGodScript._step_see_through). It multiplies with the HUD's own fades.
const HUD_SEE_THROUGH_ALPHA := 0.45
const HUD_SEE_THROUGH_FADE := 0.2
# 2.0 until the tuning of 2026-10-04: every attack opens on its own warp and summon, a second and more with nothing to
# dodge, so the second hover between them was dead time.
const IDLE_TIME := 1.0
# His fight's theme, and his alone since 2026-10-06 (the user: "when the jordan god fight starts you can use neo tokyo
# for the remainder of it"; his kaiju fight went back to his original theme, JordanArtLayout.theme(), and the cutscene
# between them plays no music): the user's own track, "Neo Tokyo", kept in Assets/Audio/SFX/local/, which is
# gitignored: those rights aren't ours and the repo is public. It starts on the fight's first frame (JordanGodOpen) and
# runs to the end of it, ducked under the final beam. Without it - a fresh clone has none - his final theme plays
# instead, kept in Music/OriginalThemes/: loop Forward over the whole file by its import, -6 dB like its intro.
# THE LEVEL IS MEASURED, NOT GUESSED (decoded offline): the track is mastered hot, its body at -4.6 to -5.0 dBFS
# RMS with decoded peaks over full scale, against -9.3 for his original. At -12 dB its body sits around -17, level
# with the original's average at its -7 and a little under its loud half, so the hits and parries stay on top.
# IT IS A SONG, NOT A LOOP: 140 BPM on a steady grid from its first sample and an 8-bar intro, then after bar 144
# (246.857 s) one last hit rings out into silence by 251 s. Looped end to start that is a five-second hole, so it
# loops early instead: after 576 beats, the bar line the ring-out starts on, the stream goes straight back to the
# top, outro into intro on the beat (checked offline: the audio after the seam is the file from 0, no gap). Only
# for the file it was measured on: a different track dropped in at this path loops end to start.
const MUSIC_LOCAL := {
	"stream": "res://Assets/Audio/SFX/local/jordan_theme_local.mp3",
	"volume_db": -12.0,
	"bpm": 140.0,
	"loop_beats": 576,
	"length": 253.15,
}
const MUSIC_FALLBACK := {stream = "res://Assets/Audio/Music/OriginalThemes/jordan_final_theme.wav", volume_db = -6.0}


# The stream and level the fight plays, set to loop: {stream, volume_db}.
static func music() -> Dictionary:
	if not ResourceLoader.exists(MUSIC_LOCAL.stream):
		return {"stream": load(MUSIC_FALLBACK.stream), "volume_db": MUSIC_FALLBACK.volume_db}
	var stream = load(MUSIC_LOCAL.stream)
	if stream is AudioStreamWAV:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		stream.loop_begin = 0
		stream.loop_end = int(stream.get_length() * stream.mix_rate)
	elif stream is AudioStreamMP3:
		stream.loop = true
		if absf(stream.get_length() - MUSIC_LOCAL.length) < 0.1:
			stream.bpm = MUSIC_LOCAL.bpm
			stream.beat_count = MUSIC_LOCAL.loop_beats
	return {"stream": stream, "volume_db": MUSIC_LOCAL.volume_db}


# The attacks in turn: BASE_COMBOS, and the wheel last while USE_ELEMENT_WHEEL is on.
static func rotation() -> Array[String]:
	var out: Array[String] = BASE_COMBOS.duplicate()
	if USE_ELEMENT_WHEEL:
		out.append(WHEEL_COMBO)
	return out

#THE ROTATION
# The combination attacks in turn, by path, each a JordanCombo: attack 1, then attack 2, then 1 again... A path whose
# script isn't there yet (or won't load) is skipped, so the fight runs while they are still being written. A static var
# rather than a const so the defence suite can point it at its stub (jordan_god's rotation).
const BASE_COMBOS: Array[String] = [
	"res://Scripts/States/JordanGod/JordanComboMaze.gd",
	"res://Scripts/States/JordanGod/JordanComboKegs.gd",
	"res://Scripts/States/JordanGod/JordanComboPortals.gd",
	"res://Scripts/States/JordanGod/JordanComboCircle.gd",
]
# Attack 5, Liam + Bixby's Elemental Wheel (JordanComboWheel), last in the rotation while switched on; off, the rotation
# is exactly BASE_COMBOS. On since the user approved the wheel's art and asked for approved work wired (2026-10-06).
static var USE_ELEMENT_WHEEL := true
const WHEEL_COMBO := "res://Scripts/States/JordanGod/JordanComboWheel.gd"
static var COMBOS: Array[String] = rotation()
# What an attack puts in the arena (JordanCombo.add_hazard): release() and his defeat take every node in it.
const HAZARD_GROUP := "jordan_god_hazard"

#COMING UP FROM THE FINALE
# Loaded on threads while the finale plays (prefetch), so its smash cut lands on the fight at once instead of on the
# load (measured 2026-09-29: ~0.7 s, most of it the attack scripts' own preloads as the state machine builds them). The
# scene and those scripts are held here across the scene change - the finale's own references go with it - until the
# fight has built its attacks (release_prefetch).
static var prefetch_paths: Array[String] = []
static var prefetched := {}

#THE LAYERS (JordanGodScene's children, and their z)
const LAYERS := {&"void": "Void", &"floor": "Floor", &"strings": "Strings", &"stage": "Stage", &"dark": "Dark",
	&"fx": "Fx"}
# Attack 1's darkness: pitch black over everything below DARK_Z, reaching a whole view past the screen each way, so
# neither a shake nor a view drawn further out ever shows an edge. Whatever must show is lifted above it by LIFT_Z
# (JordanCombo.lift_above_dark), which keeps the layers' order: the god -5 to 6, the floor -3 to 8, the strings -2 to
# 9, the stage and the player 0 to 11.
const DARK_Z := 5
const LIFT_Z := 11
const DARK_COLOR := Color(0, 0, 0, 1)
const DARK_BORDER := Rect2(-1920, -1080, 5760, 3240)
const DARK_TIME := 0.3

#THE PLAYER
# MainPlayer's soles are this far under its origin (its collision box's bottom edge).
const SOLES_BELOW_ORIGIN := 42.0
# The base pose a held player stands in: the idle column of their own sheet, their facing's row.
const PLAYER_SHEET := {texture = "res://Assets/Characters/MainPlayer/player_4dir_sheet.png", hframes = 10, vframes = 4}
const BASE_POSE := {frames = [0], times = [1.0], loop = true}
# The punch-out: three punch presses at least PUNCH_GAP apart, each a swing and a flinch; hit 1 is MainPlayer's own
# `punch` animation read off its AnimationPlayer (PlayerPunching plays it at PUNCH_SPEED), hits 2 and 3 its columns
# on the combo sheet (PunchComboArtLayout). Then the finisher, FINISHER_DELAY after the third.
const PUNCH_OUT_PRESSES := 3
const PUNCH_GAP := 0.10
const PUNCH_ANIM := "punch"
const PUNCH_SPEED := 2.0
const COMBO_SHEET := {texture = "res://Assets/Characters/MainPlayer/player_combo_sheet.png", hframes = 8, vframes = 4}
const FINISHER_DELAY := 0.15
# The arrow over the player (JordanArrowBadge), from their origin, just over ARROW_HEAD, the top of their head. The
# world is drawn at 2/3, so the arrow and the hint are drawn 1.5x (ui_scale) to read at their own size, the arrow's gap
# over the head growing with it (arrow_over).
const ARROW_OVER := Vector2(0, -84)
const ARROW_HEAD := -48.0
# A first-run hint under the player, in the Glass Row hint's style (MattArtLayout.GLASS_HINT).
const HINT := {font_size = 33, outline = 6, color = Color("#F2F3FF"), outline_color = Color("#332F68"), offset = Vector2(0, 66),
	fade = 0.2, width = 1200.0}

#THE SUMMON AND THE RECALL (seconds from his summon starting)
# The rift cracks open under each puppet and the strings are cast down into it; then the yank, and each puppet rises
# through its rift from one puppet height under the floor, clipped at the floor line, easing out; then it settles.
# The recall is the same backwards: the rifts open, the puppets sink, the strings come away, the rifts close. On his
# drawn summon the beats are its frames (FINAL_SUMMON: the artist's sync); on the stand-in, the plan's own.
const PLACEHOLDER_SUMMON := {rift = 0.0, strings = 0.0, rise = 0.45, rise_time = 0.5}
const FINAL_SUMMON := {rift_frame = 1, strings_frame = 1, rise_frame = 3, rise_time = 0.30}
const SETTLE_TIME := 0.3
const RECALL_SINK := 0.5

#THE RIFT (JordanRift)
# The drawn one: three synced layers - back (behind the puppet), front and an additive glow (over it) - in two sizes,
# its anchor the texel the puppet's feet stand on, the puppet clipped at that row while it is in the rift. `summon` opens
# it and holds `hold` while the puppet rises, then plays out; `despawn` the same for the recall.
const USE_FINAL_RIFT := true
const RIFT_DIR := "res://Assets/Characters/Jordan/God/Rift/"
const RIFTS := {
	&"standard": {stem = "puppet_rift_", frame = Vector2(144, 96), anchor = Vector2(72, 72)},
	&"wide": {stem = "puppet_rift_wide_", frame = Vector2(224, 112), anchor = Vector2(112, 84)},
}
const RIFT_SEQUENCES := {
	&"summon": {times = [0.08, 0.08, 0.10, 0.10, 0.10, 0.10, 0.08, 0.12], hold = [3, 4, 5]},
	&"despawn": {times = [0.06, 0.08, 0.12, 0.12, 0.08, 0.14], hold = [2, 3]},
}
const RIFT_LAYERS: Array[StringName] = [&"back", &"front", &"glow"]
# Until it is in: an ellipse - the dark of the hole, a red rim and a glow - with embers rising off it, grown in and
# shrunk away.
const PLACEHOLDER_RIFT := {depth = Color("#0B0610"), rim = Color("#B3202A"), glow = Color(1.0, 0.35, 0.15, 0.55),
	rim_width = 6.0, points = 32, height_ratio = 0.28, embers = 24, ember_color = Color(1.0, 0.5, 0.2, 0.9),
	ember_speed = Vector2(30, 90), open_time = 0.3, close_time = 0.3}

#THE STRINGS (JordanStrings), the user's blue take
# Two a puppet, from a pair of one hand's fingertips (STRING_PAIRS: the artist's inner pair, index and middle, for a
# puppet under or inside the hand, the outer pair, ring and little, for one further out) to its back hook. Drawn as the
# art draws them (art_source/jordan_puppeteer/jp_strings.py), on the 640x360-texel grid: a quadratic from the fingertip
# to the hook whose middle sags (1 - tension) x SAG_OF_SPAN of its span, rastered a texel wide in the core colour; a
# texel of glow ADDED either side, joined into one band where strings run side by side and left dark between two; and
# at each fingertip its knot, added round a hot texel - the drawn knot sprite once in (USE_FINAL_STRINGS), the same in
# code until then.
const USE_FINAL_STRINGS := true
const STRING_KNOT := "res://Assets/Characters/Jordan/God/Strings/puppet_string_knot_blue.png"
const STRING_COLORS := {core = Color("#66C6EC"), glow = Color("#17385A"), knot = Color("#2B6C99"), hot = Color("#D2F6FF"),
	bright = Color("#9ADCF4")}
const SAG_OF_SPAN := 0.12
const STRING_PAIRS := {&"greyson": [0, 1], &"matt": [2, 3], &"burak": [2, 3], &"danny": [2, 3], &"liam": [0, 1],
	&"bixby": [2, 3]}
# Taut on a yank, easy while he works them, slack when they hang. His drawn frames carry their own (JordanGodTips).
const TENSION_YANK := 1.0
const TENSION_WORK := 0.6
const TENSION_LIMP := 0.2
const TENSION_TIME := 0.2
# The damage going up them: a hot bead from the hook to the fingertip, then his flinch.
const PULSE_TIME := 0.25
# His defeat: each string parts at the hook and whips up to his hand as it fades.
const SNAP_TIME := 0.35

#HIS ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats), whether it loops, and what follows a
# one-shot. His hover is the finale's (FinaleLayout.GOD); the rest are his puppeteer sheets.
const FRAME: Vector2 = FinaleLayout.GOD[&"hover"].frame
const ANCHOR: Vector2 = FinaleLayout.GOD[&"hover"].anchor
const HOVER_SHEET: String = FinaleLayout.GOD[&"hover"].sheet
const TALK_SHEET: String = FinaleLayout.GOD[&"talk"].sheet
const AURA_SHEET: String = FinaleLayout.GOD[&"aura"].sheet
const HOVER := {sheet = HOVER_SHEET, aura = AURA_SHEET, frames = [0, 1, 2, 3, 4, 5], times = [0.14], loop = true}
# The drawn set: every sheet on the hover's frame and anchor, each with its additive aura strip on the aura's, frame
# for frame; `tips` names its fingertip rows in the generated table. Plays once USE_FINAL_PUPPETEER is on and every
# sheet, every aura and Scripts/JordanGodTips.gd are in and imported (final_puppeteer).
const USE_FINAL_PUPPETEER := true
const GOD_DIR := "res://Assets/Characters/Jordan/God/"
const TIPS_SCRIPT := "res://Scripts/JordanGodTips.gd"
const SUMMON_TIMES := [0.10, 0.08, 0.16, 0.05, 0.14, 0.14, 0.10]
const YANK_TIMES := [0.06, 0.05, 0.12, 0.08]
const FINAL_ANIMS := {
	&"control": {sheet = GOD_DIR + "jordan_god_puppeteer_control.png", aura = GOD_DIR + "jordan_god_puppeteer_control_aura.png",
		tips = &"puppeteer_control", frames = [0, 1, 2, 3, 4, 5], times = [0.14], loop = true},
	&"summon": {sheet = GOD_DIR + "jordan_god_puppeteer_summon_both.png",
		aura = GOD_DIR + "jordan_god_puppeteer_summon_both_aura.png", tips = &"puppeteer_summon_both",
		frames = [0, 1, 2, 3, 4, 5, 6], times = SUMMON_TIMES, loop = false, next = &"control"},
	&"summon_left": {sheet = GOD_DIR + "jordan_god_puppeteer_summon_left.png",
		aura = GOD_DIR + "jordan_god_puppeteer_summon_left_aura.png", tips = &"puppeteer_summon_left",
		frames = [0, 1, 2, 3, 4, 5, 6], times = SUMMON_TIMES, loop = false, next = &"control"},
	&"summon_right": {sheet = GOD_DIR + "jordan_god_puppeteer_summon_right.png",
		aura = GOD_DIR + "jordan_god_puppeteer_summon_right_aura.png", tips = &"puppeteer_summon_right",
		frames = [0, 1, 2, 3, 4, 5, 6], times = SUMMON_TIMES, loop = false, next = &"control"},
	# Yank frame 1 is the jerk: Danny's leap starts on it.
	&"yank_left": {sheet = GOD_DIR + "jordan_god_puppeteer_yank_left.png", aura = GOD_DIR + "jordan_god_puppeteer_yank_left_aura.png",
		tips = &"puppeteer_yank_left", frames = [0, 1, 2, 3], times = YANK_TIMES, loop = false, next = &"control"},
	&"yank_right": {sheet = GOD_DIR + "jordan_god_puppeteer_yank_right.png",
		aura = GOD_DIR + "jordan_god_puppeteer_yank_right_aura.png", tips = &"puppeteer_yank_right", frames = [0, 1, 2, 3],
		times = YANK_TIMES, loop = false, next = &"control"},
	&"hit": {sheet = GOD_DIR + "jordan_god_hit.png", aura = GOD_DIR + "jordan_god_hit_aura.png", tips = &"hit", frames = [0, 1],
		times = [0.08, 0.16], loop = false},
}
# Until it is in: every puppeteer animation off his hover and talk sheets; `hands` moves the stand-in's fingertips on
# a step, in texels, so a dip and a yank still read in the strings.
const PLACEHOLDER_ANIMS := {
	&"control": {sheet = HOVER_SHEET, aura = AURA_SHEET, frames = [0, 1, 2, 3, 4, 5], times = [0.14], loop = true},
	&"summon": {sheet = TALK_SHEET, frames = [0, 1], times = [PLACEHOLDER_SUMMON.rise, 0.25], loop = false, next = &"control",
		hands = [{&"left": Vector2(0, 8), &"right": Vector2(0, 8)}, {&"left": Vector2(0, -6), &"right": Vector2(0, -6)}]},
	&"summon_left": {sheet = TALK_SHEET, frames = [0, 1], times = [PLACEHOLDER_SUMMON.rise, 0.25], loop = false,
		next = &"control", hands = [{&"left": Vector2(0, 8)}, {&"left": Vector2(0, -6)}]},
	&"summon_right": {sheet = TALK_SHEET, frames = [0, 1], times = [PLACEHOLDER_SUMMON.rise, 0.25], loop = false,
		next = &"control", hands = [{&"right": Vector2(0, 8)}, {&"right": Vector2(0, -6)}]},
	&"yank_left": {sheet = TALK_SHEET, frames = [1, 1], times = [0.06, 0.25], loop = false, next = &"control",
		hands = [{&"left": Vector2(0, 4)}, {&"left": Vector2(0, -6)}]},
	&"yank_right": {sheet = TALK_SHEET, frames = [1, 1], times = [0.06, 0.25], loop = false, next = &"control",
		hands = [{&"right": Vector2(0, 4)}, {&"right": Vector2(0, -6)}]},
	&"hit": {sheet = HOVER_SHEET, aura = AURA_SHEET, frames = [0], times = [0.2], loop = false},
}
# The stand-in's fingertips: the claw at the top joint of each wing, two points a hand, on each hover frame (the bob
# is drawn in, so they move with it). Row 43 at most, 61 px on the screen: well above every puppet's back hook (y 220
# to 300), so the strings always run down to their puppets. The talk sheet is drawn in hover frame 0's pose.
const PLACEHOLDER_FINGERTIPS := [
	{&"left": [Vector2(85, 43), Vector2(88, 47)], &"right": [Vector2(234, 43), Vector2(231, 47)]},
	{&"left": [Vector2(85, 43), Vector2(88, 47)], &"right": [Vector2(234, 43), Vector2(231, 47)]},
	{&"left": [Vector2(85, 42), Vector2(88, 46)], &"right": [Vector2(234, 42), Vector2(231, 46)]},
	{&"left": [Vector2(85, 40), Vector2(88, 44)], &"right": [Vector2(234, 40), Vector2(231, 44)]},
	{&"left": [Vector2(85, 39), Vector2(88, 43)], &"right": [Vector2(234, 39), Vector2(231, 43)]},
	{&"left": [Vector2(85, 40), Vector2(88, 44)], &"right": [Vector2(234, 40), Vector2(231, 44)]},
]
# His flinch as the damage reaches him on the stand-in, which has no hit of its own: a white flash and a shake, `shake`
# px at 3 px a texel, scaled with him (GOD_SCALE).
const HIT := {flash = Color(3, 3, 3), flash_time = 0.15, shake = 4.0, steps = 4, step_time = 0.025}

#HIS DEFEAT (the 20th uppercut; seconds)
# He waits out the juggle that killed him and the outro's line delay, then: every string snaps, the puppets crumple and
# dissolve, he dissolves, a beat, and FightOutro fades to TO BE CONTINUED.
const DEFEAT := {snap = 0.35, crumple = 0.5, puppet_dissolve = 1.0, god_dissolve = 1.6, hold = 0.6}

#THE FINAL BEAM (JordanGodFinalBeam; its numbers are FinalBeamLayout's)
# On, his last kill is a five-bar charge mash and a beam instead of his defeat above: five bars and he disintegrates
# and the fight is won; fewer and he pulls himself back together with REVIVE_HEALTH of his bar (out of
# UPPERCUTS_TO_BEAT), and while he is revived the first uppercut that lands takes all he has. Off, or with the state's
# script missing, his defeat plays as it always has. On since the user approved its art (2026-10-06).
static var USE_FINAL_BEAM := true
const FINAL_BEAM_STATE := "res://Scripts/States/JordanGod/JordanGodFinalBeam.gd"
const REVIVE_HEALTH := 5
const REVIVE_ONE_UPPERCUT := true
# His laugh as he reforms: his talk sheet.
const LAUGH := {sheet = TALK_SHEET, frames = [0, 1], times = [0.10], loop = true}

#HIS SOUNDS (stand-ins off the shared set; nothing of his last phase has been recorded)
const SOUNDS := {
	&"hit": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", volume_db = 0.0, pitch = 0.8},
	&"summon": {stream = "res://Assets/Audio/SFX/carter_dark.wav", volume_db = -4.0, pitch = 0.8},
	&"yank": {stream = "res://Assets/Audio/SFX/whirlwind_whoosh.ogg", volume_db = -4.0, pitch = 1.3},
	&"rift": {stream = "res://Assets/Audio/SFX/earthquake_slam.ogg", volume_db = -8.0, pitch = 0.7},
	&"pulse": {stream = "res://Assets/Audio/SFX/parry_tink_1.wav", volume_db = -6.0, pitch = 0.7},
	&"snap": {stream = "res://Assets/Audio/SFX/carter_parry_break.wav", volume_db = -2.0, pitch = 1.2},
	&"dissolve": {stream = "res://Assets/Audio/SFX/greyson_disintegrate.wav", volume_db = -2.0, pitch = 0.8},
}


# What world-space UI - the arrow over the player, the hint under them - is drawn at, to read at its own size under
# the fight's base view.
static func ui_scale() -> float:
	return 1.0 / ScreenView.base_zoom


# The arrow's point off the player's origin, its gap over their head grown with it.
static func arrow_over() -> Vector2:
	return Vector2(ARROW_OVER.x, ARROW_HEAD + (ARROW_OVER.y - ARROW_HEAD) * ui_scale())


# The fight's scene and its attack scripts, requested on the loader's threads. Once each.
static func prefetch() -> void:
	var paths: Array[String] = [FIGHT_SCENE]
	paths.append_array(COMBOS)
	for path in paths:
		if prefetch_paths.has(path) or prefetched.has(path) or not ResourceLoader.exists(path):
			continue
		if ResourceLoader.load_threaded_request(path) == OK:
			prefetch_paths.append(path)


# Everything prefetched, loaded (waiting for whatever is still loading) and held; the fight's scene, or null if it was
# never prefetched.
static func take_prefetch() -> PackedScene:
	for path in prefetch_paths:
		prefetched[path] = ResourceLoader.load_threaded_get(path)
	prefetch_paths.clear()
	return prefetched.get(FIGHT_SCENE) as PackedScene


# The fight holds what it uses itself once its attacks are built: let go of the rest, and close any request never
# taken (a way in that loaded the scene on its own).
static func release_prefetch() -> void:
	for path in prefetch_paths:
		ResourceLoader.load_threaded_get(path)
	prefetch_paths.clear()
	prefetched.clear()


# His generated fingertip table, if it is in: a guarded load, since it may not be.
static func tips_table() -> GDScript:
	if not ResourceLoader.exists(TIPS_SCRIPT):
		return null
	var table = load(TIPS_SCRIPT)
	return table if table is GDScript and table.can_instantiate() else null


# His drawn puppeteer set, once it is switched on and every sheet, aura and the fingertip table are in and imported.
static func final_puppeteer() -> bool:
	if not USE_FINAL_PUPPETEER or tips_table() == null:
		return false
	for spec in FINAL_ANIMS.values():
		if not ResourceLoader.exists(spec.sheet) or not ResourceLoader.exists(spec.aura):
			return false
	return true


static func god_anim(anim_name: StringName, drawn: bool) -> Dictionary:
	if anim_name == &"hover":
		return HOVER
	if anim_name == &"laugh":
		return LAUGH
	var table: Dictionary = FINAL_ANIMS if drawn else PLACEHOLDER_ANIMS
	return table.get(anim_name, HOVER)


# Seconds from an animation's start to its frame `step`.
static func step_start(spec: Dictionary, step: int) -> float:
	var times: Array = spec.times
	var total := 0.0
	for i in mini(step, spec.frames.size()):
		total += float(times[mini(i, times.size() - 1)])
	return total


# The summon's beats, in seconds from its start: the rifts, the strings, the rise and how long it takes.
static func summon_beats(drawn: bool) -> Dictionary:
	if not drawn:
		return PLACEHOLDER_SUMMON
	var spec: Dictionary = FINAL_ANIMS[&"summon"]
	return {rift = step_start(spec, FINAL_SUMMON.rift_frame), strings = step_start(spec, FINAL_SUMMON.strings_frame),
		rise = step_start(spec, FINAL_SUMMON.rise_frame), rise_time = FINAL_SUMMON.rise_time}


static func final_rift(profile: StringName) -> bool:
	if not USE_FINAL_RIFT:
		return false
	for sequence in RIFT_SEQUENCES:
		for layer in RIFT_LAYERS:
			if not ResourceLoader.exists(rift_sheet(profile, sequence, layer)):
				return false
	return true


static func rift_sheet(profile: StringName, sequence: StringName, layer: StringName) -> String:
	return RIFT_DIR + "%s%s_%s.png" % [RIFTS[profile].stem, sequence, layer]


static func final_knot() -> bool:
	return USE_FINAL_STRINGS and ResourceLoader.exists(STRING_KNOT)
