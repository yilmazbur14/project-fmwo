extends RefCounted

# Jordan's phase 1 on the kaiju (the 2026-10-04 redesign, scratchpad jordan_kaiju/PLAN.md): every number the fight's
# layout depends on, so the tuning pass and the final art only ever touch this file and the states' exports. Points
# are screen px; the kaiju's own points are px from its feet (its y-sort point), facing screen-right, unlifted.
#
# USE_KAIJU is the master switch, on since the user approved the art and the fight (2026-10-04). A static var rather
# than a const so a test can set it for its own process before the fight loads (JordanStateMachine reads it in _ready).
# Off, the fight is exactly the funko summon it was.
#
# THE ART, best first, per animation (#ANIMATIONS): its own sheet once imported, read with its contract's per-frame
# anchors (JordanKaijuSheets); else the idle's first frame, or the approved stand-in, posed in code; else a kaiju drawn in
# code from the numbers below. Those numbers are the approved sprite's (scratchpad jordan_kaiju/approval/anchors.json,
# 2026-10-04), which wave 1's idle reproduces: at home its soles' centre on (330, 800), its seat on (454, 342) and its
# mouth on (637, 429).

static var USE_KAIJU := true

const SCALE := 3.0

#THE FIGHT (plan section 4; calibrated to the 7.5 the user set)
# Both openings pay the uppercut (the user: a parried stomp's knock-off 2026-10-05, the breath's opening 2026-10-06), so
# three of them end his phase, about 27 s in for the model tier, and the pressure in those turns is the difficulty:
# at 2026-10-05's numbers he went from about 9.8 attempts to a first clear to 1.0. Back at 7.5 by his figures: a whole
# heart a blast (JordanFunkoThrow.ATTACK_ID), nine a breath and six a stomp (more there crowd its parry: eight had the
# model's stomp hit more than half the time), and lines of fire burning on through the next turn's figures
# (JordanBreath's burn_time).
# Two breaths to a stomp (JordanStateMachine's cycles) and 88 health stay from 2026-10-05; health hardly matters now,
# the uppercut being a share of it.
const MAX_HEALTH := 88
const PHASE_B_AT := 0.5
const BREAK_READS := 11
# Figures a throw: [the breath's, the stomp's] in Phase A, then in Phase B.
const FUNKOS := [[9, 6], [9, 6]]

#THE RING
const ROPES := Rect2(113, 114, 1692, 853)
const HOME := Vector2(330, 800)
# The player's no-walk walls at home, up from the intro to his defeat even while the kaiju is away: its back is to
# the rope, so nothing is ever behind it there. The approved sprite's right edge is x 636 (the snout) above y 534 and
# x 555 (the front foot) below it; each wall stops the player's body 34 to 35 px short of it, where the plan's
# provisional 710 and 640 left up to 145 px of empty floor nobody could walk on in front of its belly.
const WALLS: Array[Rect2] = [Rect2(113, 114, 557, 420), Rect2(113, 534, 477, 433)]
# While it is winded after its breath (JordanRecoil) the back wall stands back to the front wall's edge, so the floor
# in front of its lowered head - where he rides within a punch's reach - can be stood on.
const RECOIL_WALL_X := 590.0
# The front of its legs at home, 40 px past the front wall, so a tumbling figure reaches it before the wall stops it.
const LEG_BOX := Rect2(500, 560, 130, 260)
# The boss bar and the gauge under it fade while either crown is in here (DannyBossStateMachine's rect).
const HUD_FADE_RECT := Rect2(680, -1080, 560, 1280)
const HUD_FADE_ALPHA := 0.3
const HUD_FADE_TIME := 0.25
# A badge's anchor no higher than this, so the ring over it stays whole on screen (Danny's badge_top).
const BADGE_TOP := 84.0

#THE KAIJU (px from its feet)
# The approved beam origin, (637, 429), and with the jaw open on the charge frame (637, 441). Until the head-aim
# layer lands the drawn sheets keep the mouth there and the beam is aimed in code; the code-drawn stand-in turns its
# head about NECK, MOUTH_REACH to the mouth.
const MOUTH := Vector2(307, -371)
const MOUTH_OPEN := Vector2(307, -359)
const NECK := Vector2(195, -371)
const MOUTH_REACH := 112.0
# His seat on the head's top and back at the neck base, (454, 342) at home: his body stands its soles here.
const SEAT := Vector2(124, -458)
# His crown riding (y 159 at home) and the head's top (y 312).
const RIDER_CROWN := Vector2(120, -641)
# The box in his raised hand riding (the approved rider's, (516, 242) at home): his throws leave from it.
const RIDER_HAND := Vector2(186, -558)
const CROWN := Vector2(210, -488)
const HIP := Vector2(-130, -160)
# The front foot's sole: the stomp's mark is where this comes down.
const FOOT_IMPACT := Vector2(150, 0)
# The seven rows of plates from the tail to the neck (where the code-drawn stand-in grows them, and the glow the charge
# lights them with on the sheets): centre, outward normal, size.
const PLATE_ROWS := [
	[Vector2(-190, -125), Vector2(-0.9, -0.4), 34.0],
	[Vector2(-205, -195), Vector2(-0.95, -0.3), 44.0],
	[Vector2(-200, -265), Vector2(-0.9, -0.45), 54.0],
	[Vector2(-175, -330), Vector2(-0.8, -0.6), 60.0],
	[Vector2(-120, -390), Vector2(-0.65, -0.75), 58.0],
	[Vector2(-50, -432), Vector2(-0.45, -0.9), 50.0],
	[Vector2(30, -450), Vector2(-0.25, -0.97), 40.0],
]
# The head's drawn aims, degrees screen-clockwise from level.
const AIM_FRAMES := [-60.0, -40.0, -20.0, 0.0, 20.0, 40.0, 65.0, 90.0]
# The beam's own range: it can point past the head's last frames, so every walkable spot is in reach.
const BEAM_AIM_MIN := -85.0
const BEAM_AIM_MAX := 100.0
# Off the top of the screen at its stomp's highest, whatever spot it hangs over.
const LEAP_HEIGHT := 1400.0

#JORDAN
# Where he stands at the start of the intro (his origin), and where a bare transition into Dismounted puts him: left of
# the ring's middle, so whatever is measured from him toward the middle is on open floor, clear of the kaiju's walls.
const JORDAN_START := Vector2(960, 410)
const BARE_KNOCK_OFF := Vector2(900, 410)
# The knock-off: his body box this far past the player's hurtbox, soles inside this band of y.
const KNOCK_OFF_GAP := 60.0
const KNOCK_OFF_SOLES_Y := Vector2(500, 930)
# His soles after a mounted Break at home, and after a mounted KO.
const BREAK_THROW_OFF := Vector2(900, 600)
const DEFEAT_LANDING := Vector2(900, 560)
# Where his soles may land: inside the ropes, the soles' own margin.
const SOLES_BOUNDS := Rect2(200, 300, 1520, 640)

#THE FIGURES
const FUNKO_FROM_PLAYER := 280.0
const FUNKO_APART := 140.0
const FUNKO_OFF_BURN := 60.0

#THE CODE-DRAWN STAND-IN'S COLOURS (the approved hide, belly, plates and eyes; the beam's ice-blue)
const HIDE := Color("2b5552")
const HIDE_DARK := Color("1d3a39")
const BELLY := Color("b3aa90")
const PLATE := Color("d6cfb5")
const PLATE_LIT := Color("9be8ff")
const PLATE_FLASH := Color("ffffff")
const EYE := Color("ffc93c")
const KEYLINE := Color("000000")
const BEAM_CORE := Color("f2fdff")
const BEAM_EDGE := Color("3aa8ff")
const BURN := Color("6fd0ff")

#ANIMATIONS
# Its sheets and their per-frame anchors are the artist's contracts (JordanKaijuSheets, approved 2026-10-04: wave 1, the
# body, its head and plates, and the fx); a sheet is drawn once its flag is on and the editor has imported it (or a test
# has handed in its own copy, test_textures). Until then, and for the beats wave 2 hasn't drawn yet, a stand-in posed in
# code: the idle's first frame, or the approved sprite split into the kaiju and him riding it (the coordinator's stand-in,
# art_source/jordan_kaiju/shipped_standin.json), or the code-drawn kaiju if neither is in.
const Sheets := preload("res://Scripts/JordanKaijuSheets.gd")
const SHEET_DIR := "res://Assets/Characters/Jordan/Kaiju/"
const USE_FINAL_KAIJU := {
	&"idle": true, &"charge": true, &"rear": true, &"leap": true, &"drop": true, &"stomp": true, &"stumble": true,
	&"kneel": true, &"stand": true, &"land": true, &"grow": true, &"shrink": true, &"toy": true,
	&"roar": true, &"bow": true, &"hit": true, &"tail_windup": true, &"tail_spin": true, &"collapse": true,
	&"down": true,
}
# The layers over its charge stance (its head at its NECK, turned by aim; its plates lit row by row, normal blend) and
# the effects.
const USE_FINAL_HEAD := true
const USE_FINAL_SPINES := true
# Every plate lit over its Phase B roar (normal blend), the wave-2 contract's optional overlay.
const USE_FINAL_ROAR_SPINES := true
const USE_FINAL_FX := {
	&"shadow": true, &"stomp_mark": true, &"stomp_impact": true, &"beam_body": true, &"beam_mouth": true,
	&"beam_end": true, &"mouth_charge": true, &"burn_flame": true, &"burn_out": true, &"tail_arc": true, &"puff": true,
}
# The toy in his hands before the toss, a share of its own size: it sits in the box's tray (the rider contract's
# box_open note, about 0.4 to 0.5), and grows to full toy size on its way to the ropes.
const TOY_HELD_SCALE := 0.5
const USE_STANDIN := true
const STANDIN_SHEET := SHEET_DIR + "kaiju_standin.png"
const RIDER_STANDIN_SHEET := SHEET_DIR + "jordan_ride_standin.png"
# The stand-in's frames: 200x240 with its soles' centre on (86, 218), f0 the mounted idle and f1 the breath charge;
# the rider's sheet shares that geometry.
const STANDIN := {
	frame = Vector2(200, 240), pivot = Vector2(86, 218), count = 2,
	anchors = [
		{rider_seat = Vector2(127, 65), mouth = Vector2(188, 94), crown = Vector2(156, 55), hip = Vector2(43, 165), foot_impact = Vector2(136, 218)},
		{rider_seat = Vector2(127, 65), mouth = Vector2(188, 98), crown = Vector2(156, 55), hip = Vector2(43, 165), foot_impact = Vector2(136, 218)},
	],
}
const STANDIN_IDLE := 0
const STANDIN_CHARGE := 1
# Every animation's length where it is posed in code (JordanKaiju._pose).
const POSED := {
	&"idle": {time = 0.96, loop = true}, &"charge": {time = 0.40, loop = true},
	&"rear": {time = 0.50, loop = false}, &"leap": {time = 0.30, loop = false}, &"drop": {time = 0.22, loop = false},
	&"stomp": {time = 0.15, loop = false}, &"stumble": {time = 0.45, loop = false}, &"kneel": {time = 0.60, loop = true},
	&"stand": {time = 0.35, loop = false}, &"land": {time = 0.30, loop = false}, &"grow": {time = 1.20, loop = false},
	&"shrink": {time = 0.88, loop = false}, &"toy": {time = 0.40, loop = false}, &"roar": {time = 0.80, loop = false},
	&"bow": {time = 0.40, loop = false}, &"hit": {time = 0.22, loop = false},
	&"tail_windup": {time = 0.40, loop = false}, &"tail_spin": {time = 0.70, loop = false},
	&"collapse": {time = 0.30, loop = false}, &"down": {time = 0.60, loop = true},
}
# The grow's baked sizes, one a step; the shrink's, its last the toy; and the toy's.
const GROW_STEPS := [0.12, 0.18, 0.26, 0.36, 0.48, 0.60, 0.72, 0.84, 0.94, 1.0]
const SHRINK_STEPS := [1.0, 0.84, 0.66, 0.48, 0.32, 0.20, 0.12, 0.06]
const TOY_SCALE := 0.06

# A test's own textures for sheets the editor hasn't imported yet, by path: loaded off their PNGs, so the drawn path can
# be run before the import (which no headless run may do). Empty in play.
static var test_textures := {}


static func has_sheet(path: String) -> bool:
	return test_textures.has(path) or ResourceLoader.exists(path)


static func texture(path: String) -> Texture2D:
	return test_textures[path] if test_textures.has(path) else load(path)


# A drawn sheet of the contract's as the kaiju uses it - its path, frame, offset, pivot, frames, times, loop and
# anchors - or {} until it is in.
static func sheet(sheet_name: StringName, flag := true) -> Dictionary:
	if not flag or not Sheets.SHEETS.has(sheet_name):
		return {}
	var spec: Dictionary = Sheets.SHEETS[sheet_name]
	var path: String = SHEET_DIR + spec.file
	if not has_sheet(path):
		return {}
	var out := spec.duplicate()
	out.sheet = path
	out.offset = (spec.frame as Vector2) / 2.0 - (spec.pivot as Vector2)
	out.frames = range(spec.count)
	return out


static func fx(fx_name: StringName) -> Dictionary:
	return sheet(fx_name, USE_FINAL_FX.get(fx_name, false))


# How `anim_name` is drawn: a sheet ({sheet, frame, offset, pivot, frames, times, loop, anchors}), `posed` where its motion
# is the code's and `time` its length then; no `sheet` for the code-drawn kaiju.
static func anim(anim_name: StringName) -> Dictionary:
	var drawn := sheet(anim_name, USE_FINAL_KAIJU.get(anim_name, false))
	if not drawn.is_empty():
		drawn.posed = false
		return drawn
	var posed: Dictionary = POSED[anim_name].duplicate()
	posed.posed = true
	var idle := sheet(&"idle", USE_FINAL_KAIJU[&"idle"])
	if anim_name != &"charge" and not idle.is_empty():
		_stand_in(posed, idle, 0)
	elif USE_STANDIN and has_sheet(STANDIN_SHEET):
		var standin: Dictionary = STANDIN.duplicate()
		standin.sheet = STANDIN_SHEET
		standin.offset = (STANDIN.frame as Vector2) / 2.0 - (STANDIN.pivot as Vector2)
		_stand_in(posed, standin, STANDIN_CHARGE if anim_name == &"charge" else STANDIN_IDLE)
	return posed


# One frame of a sheet held for a posed animation's length.
static func _stand_in(posed: Dictionary, spec: Dictionary, frame: int) -> void:
	posed.sheet = spec.sheet
	posed.frame = spec.frame
	posed.offset = spec.offset
	posed.pivot = spec.pivot
	posed.frames = [frame]
	posed.times = [posed.time]
	posed.anchors = [spec.anchors[frame]] if frame < spec.anchors.size() else []


static func rider_standin() -> String:
	return RIDER_STANDIN_SHEET if USE_STANDIN and has_sheet(RIDER_STANDIN_SHEET) else ""


# The head's drawn frame nearest an aim, in degrees.
static func aim_frame(degrees: float) -> int:
	var best := 0
	for i in AIM_FRAMES.size():
		if absf(AIM_FRAMES[i] - degrees) < absf(AIM_FRAMES[best] - degrees):
			best = i
	return best


static func in_walls(point: Vector2) -> bool:
	for wall in WALLS:
		if wall.has_point(point):
			return true
	return false


static func box_in_walls(box: Rect2) -> bool:
	for wall in WALLS:
		if wall.intersects(box):
			return true
	return false


# How far a ray from `from` at `angle` (radians) runs before it leaves the ropes.
static func reach_to_ropes(from: Vector2, angle: float) -> float:
	var direction := Vector2.from_angle(angle)
	var best := INF
	for axis in 2:
		var d: float = direction[axis]
		if absf(d) < 0.00001:
			continue
		var edge: float = ROPES.end[axis] if d > 0.0 else ROPES.position[axis]
		var t: float = (edge - from[axis]) / d
		if t > 0.0:
			best = minf(best, t)
	return best if best < INF else 0.0
