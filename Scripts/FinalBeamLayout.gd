extends RefCounted

# Every number the final beam plays on (JordanGodFinalBeam, FinalBeamFx, FinalBeamMeterUI): god-form Jordan's last
# kill goes into a five-bar charge mash and a beam instead of his defeat. Points are world px unless named screen px;
# the player's texels and his are 3 px. Both stagings are data here, so picking one costs no code.
#
# THE ART (approved by the user 2026-10-06: "approve all, from side-on, blue-white"): the artist's sheets, assembled as
# art_source/god_final_beam/contract.json says. Each piece replaces its stand-in on its own once its file is in and
# imported (has_piece); USE_FINAL_ART off plays every stand-in. The back staging's own strip, aura and ash weren't
# shipped, so it plays those three on their stand-ins.

const GodLayout := preload("res://Scripts/JordanGodLayout.gd")

const SFX := "res://Assets/Audio/SFX/"
const EFFECTS := "res://Assets/Effects/FinalBeam/"
const GOD_DIR := "res://Assets/Characters/Jordan/God/"
const TEXEL := 3.0

static var USE_FINAL_ART := true

#THE STAGING (the user's pick: side-on)
static var STAGING := &"side"
# mark: the player's origin (their soles 39 px under it); facing: PlayerScript.Facing; angle: the beam's, fixed, in
# degrees; ball and muzzle: texels of the player's 48x48 cell (the contract's), on both the drawn and the stand-in
# player; shout and ken: where the drawn words hang off the origin, before and from the release.
const STAGINGS := {
	&"side": {mark = Vector2(266, 975), facing = 3, angle = -45.0, ball = Vector2(14.5, 29.0), muzzle = Vector2(36.5, 12.5),
		sheet = "res://Assets/Characters/MainPlayer/player_final_beam_side.png", aura = EFFECTS + "final_beam_aura_side.png",
		disintegrate_ash = GOD_DIR + "jordan_god_disintegrate_ash_side.png", reform_ash = GOD_DIR + "jordan_god_reform_ash_side.png",
		shout = Vector2(40, -105), ken = Vector2(400, 80)},
	&"back": {mark = Vector2(960, 1290), facing = 1, angle = -90.0, ball = Vector2(33.0, 28.0), muzzle = Vector2(23.5, 11.5),
		sheet = "res://Assets/Characters/MainPlayer/player_final_beam_back.png", aura = EFFECTS + "final_beam_aura_back.png",
		disintegrate_ash = GOD_DIR + "jordan_god_disintegrate_ash_back.png", reform_ash = GOD_DIR + "jordan_god_reform_ash_back.png",
		shout = Vector2(-250, -60), ken = Vector2(-360, -20)},
}
# His drawn white core on his hit and hover frame 0, which the beam is aimed at: not the rune circle's centre.
const CORE_TEXEL := Vector2(159.5, 117.5)

#THE MASH (FinisherTierMeter, unchanged: it resolves when every window's bar is banked)
# Fitted on the model tier (jordan_final_beam tier=model) to a steady 5.5 / 6.25 / 7.0 / 7.5 / 8.0 presses a second.
# Bar 5's window is longer than the plan's first fit (1.39): at 1.39 it was window-bound, and the mercy, which only
# eases the drains, left it at 7.07 a second after three fails instead of under 6.8.
const GAIN := 0.20
const DRAINS: Array[float] = [0.344, 0.384, 0.430, 0.461, 0.510]
const WINDOWS: Array[float] = [2.02, 1.78, 1.59, 1.48, 1.80]
const START_GRACE := 1.2
# Off: only a window ends the mash.
const IDLE_STOP := 10.0
const MERCY_PER_FAIL := 0.06
const MERCY_MAX_FAILS := 3
# Real seconds, as PlayerFinisher's: both keys in one input flush count once.
const MIN_PRESS_INTERVAL := 0.03
const BARS := 5

#THE CAMERA (a factor over the fight's 2/3 base, by bars banked; the stops are whole px a texel: 2 x zoom)
const ZOOMS: Array[float] = [1.5, 2.0, 2.5, 3.0, 3.5]
# From the muzzle toward his core.
const FOCUS_WEIGHTS: Array[float] = [0.30, 0.22, 0.15, 0.08, 0.0]
const STEP_TIME := 0.25
const RELEASE_ZOOM := 4.0
# Real seconds: it plays out inside the release's hit-stop.
const RELEASE_PUNCH := 0.08
const RELEASE_PULL := 0.45
# Real seconds, as the finisher's kicks and rumble are.
const KICKS: Array[float] = [6.0, 9.0, 12.0, 16.0, 34.0]
const KICK_STEPS := 6
const RELEASE_KICK_STEPS := 10
const KICK_STEP_TIME := 0.03
const RUMBLES: Array[float] = [1.5, 3.0, 4.5, 6.0, 7.5]
const RUMBLE_STEP := 0.05

#THE CHARGE (by bars banked)
const CHARGE_FRAME_TIMES: Array[float] = [0.12, 0.10, 0.085, 0.07, 0.06]
const VIGNETTE: Array[float] = [0.25, 0.35, 0.45, 0.55, 0.65]
const LIGHT_RADIUS: Array[float] = [260.0, 300.0, 340.0, 380.0, 420.0]
const VIGNETTE_SOFTNESS := 150.0
const VIGNETTE_BANDS := 5.0
# From these bars on: the aura, then its flames; debris lifts; lightning arcs, his aura flickers and he jitters.
const AURA_FROM := 1
const FLAMES_FROM := 2
const DEBRIS_FROM := 3
const ARCS_FROM := 4
const DEBRIS := [24, 48]
const ARC_COUNT := 3
const ARC_LENGTH := Vector2(42, 96)
const ARC_EVERY := 0.05
const GOD_JITTER := 1.0
const GOD_AURA_FLICKER := Vector2(0.55, 1.0)

#THE TIMELINE (seconds)
const KO_HOLD := 0.4
const COLLAPSE := {snap = 0.30, crumple = 0.35, dissolve = 0.6}
const STAGE := {white_in = 0.05, white_hold = 0.05, white_out = 0.25}
const MUSIC_DUCK_DB := -6.0
const MUSIC_DUCK_TIME := 0.4

#SUCCESS
# Real seconds for the flash: two frames.
const RELEASE_FLASH := 2.0 / 60.0
const RELEASE_HIT_STOP := 0.10
# The muzzle's flash before the beam leaves it, then the head to his core (the contract's ~2700 px/s).
const MUZZLE_OPEN := 0.06
const BEAM_TRAVEL := 0.35
const IMPACT_HIT_STOP := 0.15
const IMPACT_SHAKE := 28.0
const IMPACT_SHAKE_STEPS := 10
const IMPACT_FLASH := {white = 2.0 / 60.0, cyan = 0.08, fade = 0.2, cyan_alpha = 0.55}
const SHOCKWAVE := {from = 24.0, to = 300.0, width = 12.0, time = 0.4}
# The drawn sheet's 24 frames at 0.1; its core pops on frame 21.
const DISSOLVE_TIME := 2.4
const CORE_POP := 21.0 / 24.0
const CORE_POP_FLASH := {alpha = 0.55, time = 0.1}
const RUNES_FADE := 1.6
const RUNES_GROW := 1.2
const DISSOLVE_SWEEP := 0.65
const DISSOLVE_EDGE := 0.12
const DISSOLVE_EDGE_COLORS := [Color("#FFFFFF"), Color("#8FE3FF")]
const AURA_FADE := 1.3
const ASH := {amount = 160, life = 1.2, speed = Vector2(80, 260), spread = 28.0, gravity = 30.0}
const HOLD_RUMBLE := 5.0
const CRACKLE_EVERY := 0.12
const CRACK_FRAMES := 6
const ROAR_EVERY := 0.8
const SHATTER_AT := 0.6
# Once he is gone the tip carries on off the screen, then the whole beam thins out.
const PUNCH_THROUGH := {speed = 2600.0, time = 0.35, burst = 18.0, burst_steps = 6}
const BODY_FADE := 0.45
const BODY_FADE_ALPHA := 0.5
const EMPTY_HOLD := 0.5

#FAIL (by bars banked)
const FAIL_WIDTH: Array[float] = [0.0, 0.35, 0.5, 0.65, 0.8]
const FAIL_DISSOLVE: Array[float] = [0.0, 0.12, 0.22, 0.32, 0.42]
const FAIL_HOLD := 0.8
const FAIL_SPUTTER := 0.35
const POP_TIME := 0.3
const LAUGH_TIME := 1.2
const REFORM_TIME := 1.0
const AURA_FLARE := 2.0
const REFORM_FLASH := {color = Color(0.88, 0.16, 0.16, 0.16), time = 0.13}
const REVIVE_REFILL := 0.6
const CAMERA_BACK := 0.6

#THE SHOUT (UI text only; bar k adds SYLLABLES[k - 1], the release stamps FINAL_WORD, a weak one FAIL_WORD)
const SYLLABLES: Array[String] = ["SHIN...", "KU...", "HA...", "DO..."]
const FINAL_WORD := "KEN!!!!"
const FAIL_WORD := "KEN..."

#THE METER AND THE SHOUT ON SCREEN (screen px, 1920x1080; Pixelify Sans is crisp at multiples of 11)
const UI_LAYER := 20
const METER_CENTER := Vector2(960, 96)
const SLOT_SIZE := Vector2(72, 22)
const SLOT_GAP := 8.0
const SLOT_BORDER := 3.0
const SLOT_BG := Color("#10142A")
const SLOT_EDGE := Color("#000000")
const BANK_COLORS := [Color("#2F7BFF"), Color("#4FA3FF"), Color("#7FCBFF"), Color("#BFE9FF"), Color("#FFFFFF")]
const FILL_ALPHA := 0.7
const BANK_FLASH := 0.08
const FAIL_RED := Color("#FF3B3B")
# Until the first press the keys take turns lighting up; a press shows this long.
const KEY_FLASH_TIME := 0.12
const KEY_PULSE := 0.08
const SHOUT_CENTER := Vector2(960, 196)
const SHOUT_SIZE := 55
const FINAL_CENTER := Vector2(960, 300)
const FINAL_SIZE := 99
const TEXT_OUTLINE := 8
const TEXT_OUTLINE_COLOR := Color("#0A0E24")
const TEXT_COLORS := [Color("#FFFFFF"), Color("#8FE3FF")]
const TEXT_FRAME := 0.08
const STAMP := {from = 1.35, time = 0.1}
const FAIL_TEXT := {flash = 0.2, drop = 60.0, time = 0.4}
const UI_FADE := 0.25
# How long KEN!!!! stays up from the release.
const FINAL_HOLD := 1.1

#THE STAND-INS
# The ball's radius in the player's texels by size (bars), with a texel's pulse.
const BALL_RADII: Array[float] = [4.0, 7.0, 10.0, 14.0, 19.0, 26.0]
const BALL_PULSE_HZ := 8.0
const BALL_COLORS := {rim = Color("#123A9C"), mid = Color("#2F7BFF"), hot = Color("#9FE8FF"), core = Color("#FFFFFF")}
# Half the beam's thickness at full width, world px, layer by layer from the outside in.
const BEAM_LAYERS := [
	{half = 96.0, color = Color("#123A9C"), add = false},
	{half = 84.0, color = Color("#2F7BFF"), add = true},
	{half = 54.0, color = Color("#9FE8FF"), add = false},
	{half = 24.0, color = Color("#FFFFFF"), add = false},
]
const BEAM_WOBBLE := {amount = 0.06, hz = 11.0}
const BEAM_HEAD_RADIUS := 1.15
const MUZZLE_FLARE := 1.3
const AURA_COLOR := Color(0.3, 0.6, 1.0, 0.35)
const AURA_SIZE := Vector2(42, 60)
const FLAME_COLOR := Color(0.55, 0.85, 1.0, 0.55)
const ARC_COLOR := Color("#BFE9FF")
const DEBRIS_COLORS := [Color("#3A2E4A"), Color("#5A4A6E"), Color("#8A7AA0")]
const ASH_COLORS := [Color("#FF9A4A"), Color("#4A4458"), Color("#66C6EC")]
const CRACK_RAYS := 8
const CRACK_LENGTH := Vector2(60, 150)
const CRACK_COLOR := Color("#8FE3FF")
const IMPACT_COLOR := Color("#BFE9FF")
const FLASH_COLORS := {white = Color(1, 1, 1, 1), cyan = Color("#8FE3FF")}
# The punch's contact column, read off MainPlayer's own AnimationPlayer where a pose asks for it.
const CONTACT := -1
# On the player's own 4-direction sheet (JordanGodLayout.PLAYER_SHEET), in their facing's row.
const PLACEHOLDER_POSES := {
	&"enter": {frames = [0], times = [0.16], loop = false},
	&"charge": {frames = [0], times = [1.0], loop = true},
	&"release": {frames = [CONTACT], times = [0.13], loop = false},
	&"hold": {frames = [CONTACT], times = [1.0], loop = true},
	&"settle": {frames = [CONTACT, 0], times = [0.22, 0.45], loop = false},
	&"fail": {frames = [0], times = [1.6], loop = false},
}

#THE ART CONTRACT
# The player: a 12-cell strip of 48x48, centred on MainPlayer's origin exactly as their 32x32 sheet is (cells 0 idle,
# 1 step, 2-4 charge, 5-6 thrust, 7-8 hold, 9-11 fail). An empty `times` runs on the charge's frame time by bars.
const FINAL_PLAYER_CELL := Vector2(48, 48)
const FINAL_PLAYER_CELLS := 12
const FINAL_POSES := {
	&"enter": {frames = [1], times = [0.12], loop = false},
	&"charge": {frames = [2, 3, 4], times = [], loop = true},
	&"release": {frames = [5, 6], times = [0.05, 0.08], loop = false},
	&"hold": {frames = [7, 8], times = [0.06], loop = true},
	&"settle": {frames = [5, 1, 0], times = [0.10, 0.12, 0.45], loop = false},
	&"fail": {frames = [9, 10, 11], times = [0.15, 0.2, 1.25], loop = false},
}
# Behind the player, additive, on their origin: rows by strength (bars 1-2, 3-4, 5), columns the charge's three frames.
const FINAL_AURA := {frame = Vector2(64, 64), frames = 3, rows = 3, anchor = Vector2(32, 32), row_by_bars = [0, 0, 1, 1, 2]}
# Its pivot on the ball point, over the player, glow under it: row = bars - 1, the columns a pulse.
const FINAL_BALL := {sheet = EFFECTS + "final_beam_ball.png", glow = EFFECTS + "final_beam_ball_glow.png",
	frame = Vector2(64, 64), frames = 4, rows = 5, anchor = Vector2(32, 32), time = 0.07}
# The charge giving out: at the ball point for a fizzle, at the muzzle as a weak beam cuts.
const FINAL_FIZZLE := {sheet = EFFECTS + "final_beam_ball_fizzle.png", glow = EFFECTS + "final_beam_ball_fizzle_glow.png",
	frame = Vector2(64, 64), frames = 6, anchor = Vector2(32, 32), time = 0.08}
# The beam, drawn along +x and turned to the staging's angle: the muzzle on the muzzle point (0-1 once, then 2-5 on a
# loop); the start piece from it, cropped to the travelled length under 64 texels; body tiles every 32 texels from 64,
# all on one frame, the spiral added over them, stopping 30 texels short of the tip; the head on the tip.
const FINAL_MUZZLE := {sheet = EFFECTS + "final_beam_muzzle.png", glow = EFFECTS + "final_beam_muzzle_glow.png",
	frame = Vector2(80, 80), frames = 6, anchor = Vector2(40, 40), open = [0, 1], loop = [2, 3, 4, 5], time = 0.06}
const FINAL_START := {sheet = EFFECTS + "final_beam_start.png", glow = EFFECTS + "final_beam_start_glow.png",
	frame = Vector2(64, 104), glow_frame = Vector2(64, 144), frames = 4}
const FINAL_BODY := {sheet = EFFECTS + "final_beam_body.png", glow = EFFECTS + "final_beam_body_glow.png",
	spiral = EFFECTS + "final_beam_spiral.png", frame = Vector2(32, 104), glow_frame = Vector2(32, 144), frames = 4, time = 0.06,
	from = 64.0, short_of_tip = 30.0}
const FINAL_HEAD := {sheet = EFFECTS + "final_beam_head.png", glow = EFFECTS + "final_beam_head_glow.png",
	frame = Vector2(144, 144), frames = 4, anchor = Vector2(78, 72)}
# On his core, unrotated: 0-3 once, then 4-7 on a loop while the beam holds him.
const FINAL_IMPACT := {sheet = EFFECTS + "final_beam_impact.png", glow = EFFECTS + "final_beam_impact_glow.png",
	frame = Vector2(208, 208), frames = 8, anchor = Vector2(104, 104), open = [0, 1, 2, 3], loop = [4, 5, 6, 7], time = 0.07}
# In place of his body, his aura off, on his own anchor at his scale; the ash drawn streaming with the beam.
const FINAL_DISINTEGRATE := {sheet = GOD_DIR + "jordan_god_disintegrate.png", glow = GOD_DIR + "jordan_god_disintegrate_glow.png",
	frame = Vector2(320, 224), frames = 24, anchor = Vector2(160, 223), ash_frame = Vector2(480, 352), ash_anchor = Vector2(200, 335),
	time = 0.1}
# A weak beam's: forward to the tau the bars reached, held while the beam sputters, then the red pull back together
# from the first of frames 9-15 at or under it, so it never jumps.
const FINAL_REFORM := {sheet = GOD_DIR + "jordan_god_reform.png", glow = GOD_DIR + "jordan_god_reform_glow.png",
	frame = Vector2(320, 224), frames = 16, anchor = Vector2(160, 223), ash_frame = Vector2(480, 352), ash_anchor = Vector2(200, 335),
	time = 0.1, back_from = 9, taus = [0.0, 0.06, 0.12, 0.18, 0.24, 0.3, 0.36, 0.42, 0.45, 0.45, 0.4, 0.32, 0.22, 0.12, 0.04, 0.0]}
# One word at a time, in screen space but hung off the player's origin so it rides the zoom, centred on its ink and
# kept 16 px inside the screen; px a texel by word.
const FINAL_SHOUT := {sheet = EFFECTS + "final_beam_shout_words.png", frame = Vector2(96, 16), frames = 6,
	scales = [4.0, 4.5, 5.0, 5.5, 7.0, 3.5], final = 4, fail = 5, margin = 16.0, pop = 1.35, pop_time = 0.15}

#THE SOUND (stand-ins off the project's own set, layered; each played only if its file is in)
const SOUNDS := {
	&"hum": [
		{stream = SFX + "finisher_charge_loop.wav", pitch = 0.8, to_pitch = 1.52, volume_db = -8.0, to_db = -2.0},
		{stream = SFX + "greyson_eruption_rumble.wav", pitch = 0.5, to_pitch = 0.8, volume_db = -18.0, to_db = -8.0},
	],
	&"bank_1": [{stream = SFX + "finisher_bar_1.wav", pitch = 1.0, volume_db = 0.0}],
	&"bank_2": [{stream = SFX + "finisher_bar_2.wav", pitch = 1.0, volume_db = 0.0}],
	&"bank_3": [{stream = SFX + "finisher_bar_3.wav", pitch = 1.0, volume_db = 0.0}],
	&"bank_4": [{stream = SFX + "finisher_bar_3.wav", pitch = 1.15, volume_db = 0.0}],
	&"bank_5": [{stream = SFX + "finisher_bar_3.wav", pitch = 1.3, volume_db = 0.0}],
	# Its pitch climbs 0.2 a bar.
	&"swell": [{stream = SFX + "laser_charge.ogg", pitch = 1.0, volume_db = -10.0}],
	&"release": [
		{stream = SFX + "greyson_spirit_launch.wav", pitch = 0.9, volume_db = 0.0},
		{stream = SFX + "matt_trueshot_fire.wav", pitch = 0.6, volume_db = -2.0},
		{stream = SFX + "knight_breaker_sting.wav", pitch = 1.0, volume_db = 0.0},
	],
	&"roar": [
		{stream = SFX + "whirlwind_whoosh.ogg", pitch = 0.5, volume_db = -6.0},
		{stream = SFX + "greyson_eruption_rumble.wav", pitch = 0.7, volume_db = -8.0},
	],
	&"impact": [
		{stream = SFX + "greyson_spirit_explosion.wav", pitch = 0.9, volume_db = 2.0},
		{stream = SFX + "burak_blast.wav", pitch = 0.7, volume_db = 0.0},
		{stream = SFX + "hit_impact.ogg", pitch = 0.6, volume_db = -2.0},
	],
	&"disintegrate": [{stream = SFX + "greyson_disintegrate.wav", pitch = 0.8, volume_db = 0.0}],
	&"crackle": [{stream = SFX + "greyson_spark.wav", pitch = 1.4, volume_db = -10.0}],
	&"shatter": [{stream = SFX + "matt_glass_shatter.wav", pitch = 0.7, volume_db = -2.0}],
	&"fizzle": [
		{stream = SFX + "matt_mystic_fizzle.wav", pitch = 0.6, volume_db = -2.0},
		{stream = SFX + "burak_misfire.wav", pitch = 0.8, volume_db = 0.0},
	],
	&"laugh": [
		{stream = SFX + "burak_laugh.wav", pitch = 0.6, volume_db = 0.0},
		{stream = SFX + "carter_dark.wav", pitch = 0.8, volume_db = -4.0},
	],
	&"reform": [{stream = SFX + "matt_teleport_in.wav", pitch = 0.6, volume_db = -2.0}],
}


# The staging in play.
static func staging() -> Dictionary:
	return STAGINGS.get(STAGING, STAGINGS[&"side"])


# His drawn core, where the beam is aimed and lands.
static func core() -> Vector2:
	return GodLayout.GOD_POINT + (CORE_TEXEL - GodLayout.ANCHOR) * GodLayout.GOD_SCALE


static func beam_direction() -> Vector2:
	return Vector2.from_angle(deg_to_rad(staging().angle))


# From `muzzle` along the beam to the core's projection on it.
static func beam_length(muzzle: Vector2) -> float:
	return maxf((core() - muzzle).dot(beam_direction()), 0.0)


# The drains after `fails` failed beams.
static func drains(fails: int) -> Array[float]:
	var eased := 1.0 - MERCY_PER_FAIL * mini(fails, MERCY_MAX_FAILS)
	var out: Array[float] = []
	for drain in DRAINS:
		out.append(drain * eased)
	return out


# By bars banked, 0 to 5, clamped.
static func at_bars(table: Array, bars: int) -> Variant:
	return table[clampi(bars, 0, table.size() - 1)]


# A point of the player's 48x48 cell off their origin (the contract's origin + 3 x (point - (24, 24))).
static func cell_offset(texel: Vector2) -> Vector2:
	return (texel - FINAL_PLAYER_CELL / 2.0) * TEXEL


static func has_piece(path: String) -> bool:
	return USE_FINAL_ART and ResourceLoader.exists(path)


static func final_player() -> bool:
	return has_piece(staging().sheet)


static func poses() -> Dictionary:
	return FINAL_POSES if final_player() else PLACEHOLDER_POSES


static func final_god() -> bool:
	return has_piece(FINAL_DISINTEGRATE.sheet) and has_piece(FINAL_REFORM.sheet)


# The drawn reform for `reached` (FAIL_DISSOLVE's tau): the last forward frame at or under it, and the first frame of
# the pull back at or under it.
static func reform_frames(reached: float) -> Vector2i:
	var taus: Array = FINAL_REFORM.taus
	var back_from: int = FINAL_REFORM.back_from
	var forward := 0
	for i in back_from:
		if taus[i] <= reached + 0.0001:
			forward = i
	var back := taus.size() - 1
	for i in range(back_from, taus.size()):
		if taus[i] <= reached + 0.0001:
			back = i
			break
	return Vector2i(forward, back)
