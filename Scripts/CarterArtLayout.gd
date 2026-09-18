extends RefCounted

# Every number that depends on how Carter, his clones and his darkness are drawn, so a redraw only
# needs this file. Points and boxes are in texels on one of his frames, origin top-left.
# Each asset has its own USE_FINAL_* flag: placeholder and final art go through the same code, so the
# fight is playable before a sheet lands and turning a flag off brings the placeholder back.
# This is the Akuma Carter, boss 5. The wrestler Carter that Mason calls in is a different character
# with his own script and art (Scripts/CarterScript.gd); nothing here belongs to him.

const SCALE := 3.0

#CARTER (horizontal strips of 96x96 frames, feet on row 95, x = 47.5 the symmetry axis)
const FRAME_SIZE := Vector2(96, 96)
const ANCHOR := Vector2(48, 95)
# The approved sheet: frame 0 standing, frame 1 arms crossed (his signature), frame 2 his back.
# Every placeholder pose below is one of those three.
const AKUMA_SHEET := "res://Assets/Characters/Carter/carter_akuma.png"

# What the player can punch while he is down recovering: the mass of carter_spent, the pose he holds
# through the punish window. It hunches, so the box sits well below the standing one.
const RECOVER_BODY_BOX := Rect2(8, 22, 74, 74)
# Where the finisher's daze stars circle, in px from the floor point he stands on: just over the head
# of that same spent pose, whose crown sits at texel (47, 20).
const DAZE_ANCHOR := Vector2(-3, -259)

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# Optional: turn, the degrees the sprite is rotated (the defeat placeholder is his standing pose
# keeled over). The final sheets are 96x96 strips drawn facing right with the feet on row 95.
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"intro": true,
	&"eye_flash": true,
	&"summon": true,
	&"vanish": true,
	&"reappear": true,
	&"recover": true,
	&"hit": true,
	&"defeat": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = AKUMA_SHEET, frames = [1], times = [1.0], loop = true},
	&"intro": {sheet = AKUMA_SHEET, frames = [1], times = [1.2], loop = false},
	# The eyes go: he drops the crossed arms and squares up.
	&"eye_flash": {sheet = AKUMA_SHEET, frames = [1, 0], times = [0.18, 0.37], loop = false},
	&"summon": {sheet = AKUMA_SHEET, frames = [0], times = [0.35], loop = false},
	&"vanish": {sheet = AKUMA_SHEET, frames = [2], times = [0.45], loop = false},
	&"reappear": {sheet = AKUMA_SHEET, frames = [2, 1], times = [0.18, 0.32], loop = false},
	&"recover": {sheet = AKUMA_SHEET, frames = [0], times = [1.0], loop = true},
	&"hit": {sheet = AKUMA_SHEET, frames = [0], times = [0.22], loop = false},
	&"defeat": {sheet = AKUMA_SHEET, frames = [0], times = [1.0], loop = false, turn = 90.0},
}

const FINAL_ANIMS := {
	# The standing pose, not the arms-crossed one: frame 0 is byte-identical to the entrance's last
	# frame, so the entrance cuts to it with no blend. Changing one means changing both.
	&"idle": {sheet = "res://Assets/Characters/Carter/carter_idle.png",
		frames = [0, 1, 2, 3], times = [0.18], loop = true},
	&"intro": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
		times = [0.10, 0.10, 0.10, 0.12, 0.14, 0.09, 0.07, 0.07, 0.16, 0.11, 0.11, 0.11, 0.13, 0.20,
			0.30, 0.14, 0.60], loop = false},
	# Frame 3 is the control-loss frame, held for its full 260 ms: the beat ends on it and the yank
	# carries it straight on.
	&"eye_flash": {sheet = "res://Assets/Characters/Carter/carter_eye_flash.png",
		frames = [0, 1, 2, 3], times = [0.12, 0.09, 0.09, 0.26], loop = false},
	# No summon sheet was ever drawn. The yank holds eye_flash's control-loss frame, which is already
	# a hard downward glare with the jaw open: it reads as him doing this to you.
	&"summon": {sheet = "res://Assets/Characters/Carter/carter_eye_flash.png",
		frames = [3], times = [0.4], loop = false},
	# No vanish sheet either. The entrance draws him materialising out of his aura, so its first five
	# frames run backwards are him dissolving back into it, retimed to the length of the blackout.
	&"vanish": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [4, 3, 2, 1, 0], times = [0.11, 0.10, 0.08, 0.08, 0.08], loop = false},
	# And the same five forwards for him reforming, retimed to the length of the lights coming up.
	&"reappear": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [0, 1, 2, 3, 4], times = [0.09, 0.09, 0.10, 0.10, 0.10], loop = false},
	# The punish window's pose: hunched and blowing, the one the player punches.
	&"recover": {sheet = "res://Assets/Characters/Carter/carter_spent.png",
		frames = [0, 1, 2, 3], times = [0.2, 0.17, 0.17, 0.2], loop = true},
	&"hit": {sheet = "res://Assets/Characters/Carter/carter_hit.png",
		frames = [0, 1], times = [0.07, 0.09], loop = false},
	# Never advances past frame 5.
	&"defeat": {sheet = "res://Assets/Characters/Carter/carter_defeat.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.11, 0.11, 0.10, 0.13, 0.18, 0.7], loop = false},
}

# carter_rush.png and carter_rush_pass.png are also drawn, and nothing here plays them: they are his
# full-size lunge, and the clones are half his height by the user's own call. Demon/demon_clone.png
# is that same lunge redrawn at 48x48 with its own gather and scatter frames, and that is what the
# clones use. The full-size pair is there for a later attack that has HIM rush.

#HIS AURA
# Drawn UNDER him on its own node, a sibling of his sprite rather than a child: boss.sprite has to
# stay the body sprite, which PlayerFinisher._flash and PlayerCombo._charged_feedback both write to.
const USE_FINAL_AURA := true
const FINAL_AURA := {
	"texture": "res://Assets/Characters/Carter/carter_aura.png",
	"hframes": 6,
	"frame_size": Vector2(96, 96),
	"frame_time": 0.11,
	"scale": 3.0,
}
const AURA_ALPHA := 0.75

#THE MARK ON HIS BACK
# Additive, hidden until the eyes go. Its frame size and its offset inside his 96x96 frame are
# printed by art_source/carter_akuma/build_intro.py; they are copied here rather than guessed.
const USE_FINAL_MARK_GLOW := true
const FINAL_MARK_GLOW := {
	"texture": "res://Assets/Characters/Carter/carter_mark_glow.png",
	"hframes": 6,
	"frame_size": Vector2(70, 57),
	# The glow's top-left texel, on his 96x96 frame.
	"offset": Vector2(13, 23),
	"frame_time": 0.09,
	"scale": 3.0,
}

#THE GROUND RING HIS ENTRANCE LANDS ON
const USE_FINAL_INTRO_FLASH := true
const FINAL_INTRO_FLASH := {
	"texture": "res://Assets/Characters/Carter/carter_intro_flash.png",
	"frame_size": Vector2(144, 52),
	# Its centre sits on his floor point.
	"pivot": Vector2(72, 26),
	"scale": 3.0,
	"time": 0.45,
}
# The step of `intro` the ring and the mark's glare land on: the stomp, before the pose settles.
const INTRO_FLASH_STEP := 8

#THE DARKNESS
# World-space Node2Ds, NEVER a CanvasLayer: a CanvasLayer would black out the HUD, his health bar
# and the dialogue balloon along with the arena.
# THE LAYERING IS THE EFFECT AND IT INVERTS IF IT IS WRONG. The darkness sits above the floor and the
# crowd but BELOW the fighters, which is what makes the player and the clones read as lit rather than
# as tinted. The player's own stage (MainPlayer) is z 0, so the sequence lifts it to PLAYER_Z while
# it runs and puts it back after: that one write is the only thing this fight does to a node it
# doesn't own, and CarterRagingDemon.release() is what undoes it.
const DARK_Z := 5
const POOL_Z := 6
const PLAYER_Z := 10
const CLONE_Z := 10
# Relative to a clone: its trail one below it, its light well above it.
const CLONE_GHOST_Z := -1
const CLONE_LIGHT_Z := 10
# Relative to the clone layer: the hit and the parry break over everything, the bloom over those.
const BURST_Z := 15
const FINISH_Z := 20

const DARKEN_TIME := 0.35
const CLEAR_TIME := 0.40
const POOL_OPEN_TIME := 0.25
# The pool blooms open from this much of its size.
const POOL_OPEN_FROM := 0.3
# A parry lifts the dark by this much of its alpha for this long, so the hit landing reads through it.
const CURTAIN_PARRY_LIFT := 0.09
const CURTAIN_PARRY_TIME := 0.08

# Drawn at exactly 3x from its top-left corner. Its alpha is already dithered per band - 150 over the
# crowd, 236 over the floor - so nothing may modulate it beyond the ramp in and out.
const USE_FINAL_DARKNESS := true
const FINAL_DARKNESS := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_darkness.png",
	"size": Vector2(640, 360),
	"scale": 3.0,
	# What it settles to over the floor and the sides, which is what the border quads below match.
	"edge_alpha": 0.926,
}
const PLACEHOLDER_DARKNESS := {
	"color": Color(0, 0, 0, 0.86),
}
# The sheet is exactly the view, so a screen shake - a parry's, say - would show an undarkened strip
# at one edge. Black quads fill the border it can be shaken into; only ever a few px of them is on
# screen.
const DARK_BORDER := Rect2(-400, -400, 2720, 1880)
const VIEW_RECT := Rect2(0, 0, 1920, 1080)

# ONE node under the fighters, drawn as light. The pool and the cone also ship split in two, but the
# combined sheet already contains both: never draw the combined one AND the cone, or the shaft is
# laid down twice.
const USE_FINAL_SPOTLIGHT := true
const PLACEHOLDER_SPOTLIGHT := {
	"radii": Vector2(330, 210),
	"points": 28,
	"color": Color(1, 0.95, 0.8, 0.22),
}
const FINAL_SPOTLIGHT := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_spotlight.png",
	# The texel that goes on the player's feet.
	"anchor": Vector2(80, 186),
	"scale": 3.0,
}

#THE CLONES
# MUCH SMALLER THAN CARTER - about half his height and twice the player's - and they materialise out
# of the dark and dissolve back into it rather than appearing and vanishing, the way Akuma's Oboro
# throw does. They have their own frame size and their own feet anchor, not his, and they are drawn
# at a whole 3x: the size comes from the art, never from a fractional scale on a bigger sheet.
# The art is authored dark and translucent, so nothing here tints it - that would double up.
const CLONE_FRAME_SIZE := Vector2(48, 48)
const CLONE_ANCHOR := Vector2(24, 47)
const CLONE_SCALE := 3.0

const USE_FINAL_CLONE := true
# Constant, never ramped: the fade is authored into the frames (100/140/172/196 gathering, 212
# rushing, 186/150/112/72 scattering) and an alpha tween on top of that turns it to mush. This is
# only here to take the whole set down a notch if they read too strongly.
const CLONE_ALPHA := 1.0
# A wraith outline in texels around the feet anchor, for when the sheet is turned off.
const PLACEHOLDER_CLONE := {
	"color": Color(0.14, 0.05, 0.19, 0.82),
	"rim_color": Color(0.66, 0.22, 0.54, 0.9),
	"rim_width": 3.0,
	"shape": [
		Vector2(0, -47), Vector2(5, -43), Vector2(6, -37), Vector2(13, -32), Vector2(12, -21),
		Vector2(16, -9), Vector2(7, -3), Vector2(3, 0), Vector2(-3, 0), Vector2(-7, -3),
		Vector2(-16, -9), Vector2(-12, -21), Vector2(-13, -32), Vector2(-6, -37), Vector2(-5, -43),
	],
}
# Three phases off one 12-frame strip: it gathers out of nothing, holds full strength while it
# commits and travels, then scatters away behind. The gather is 200 ms, which fits inside the FRONT
# of the 0.44 s read window: the clone is fully resolved while the player is still deciding, which is
# the whole reason the window is that long. Never let it creep toward clone_show.
const FINAL_CLONE := {
	"sheet": "res://Assets/Characters/Carter/Demon/demon_clone.png",
	"appear": [0, 1, 2, 3],
	"appear_times": [0.05, 0.05, 0.05, 0.05],
	"rush": [4, 5, 6, 7],
	"rush_time": 0.045,
	"dissipate": [8, 9, 10, 11],
	"dissipate_times": [0.05, 0.05, 0.05, 0.05],
}
# Only the placeholder uses these: the sheet's own frames carry both fades.
const CLONE_FADE_IN := 0.2
const CLONE_PASS_TIME := 0.2

# The trail behind it: four ages of one streak, not four poses. It is 48 texels wider than the clone
# so the tail has room, and it erases the clone's own footprint - it is purely the tail, and the
# clone on top of it provides the figure. Both share clone_sheet_offset(), which is what lines the
# two frames up with no further maths.
const USE_FINAL_CLONE_GHOST := true
const FINAL_CLONE_GHOST := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_clone_ghost.png",
	"hframes": 4,
	"frame_size": Vector2(96, 48),
	"frame_time": 0.055,
	"scale": 3.0,
}

#THE LIGHT OVER A CLONE
# Red means parry it, yellow means a feint that punishes a parry. The two are timed identically, so
# the only thing separating them is what they look like: red is the same diamond-and-exclamation as
# the game's existing parry tell, yellow a wide hollow ring with a bar through it. They differ in
# silhouette, aspect, solid against hollow and light-on-dark against dark-on-light, so the read
# survives colourblindness. A redraw has to keep all of that, not just the hue.
# THE HOLD FRAME IS HELD STEADY FOR THE WHOLE REACTION WINDOW. It must never pulse or loop: a tell
# that flickers gets re-read instead of acted on.
# It sits this far over the clone's head, so its height follows the clone's frame rather than being
# written down: the clones shrank once already. Its own drawn size does NOT follow - it is a tell and
# has to stay big enough to read.
const CLONE_LIGHT_GAP := 34.0
# How far the light reaches above its anchor, which is half its own drawn height. A clone is never
# spawned high enough for this to leave the top of the view: a colour that can't be seen isn't a read.
const CLONE_LIGHT_REACH := 36.0
const USE_FINAL_CLONE_LIGHT := true
const PLACEHOLDER_CLONE_LIGHT := {
	"red": {"shape": "diamond", "radius": 46.0, "color": Color(1.0, 0.16, 0.2)},
	"yellow": {"shape": "ring", "radius": 46.0, "width": 11.0, "points": 20, "color": Color(1.0, 0.85, 0.15)},
}
const FINAL_CLONE_LIGHT := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_light.png",
	"hframes": 8,
	"frame_size": Vector2(24, 24),
	# The texture's centre, which sits on CLONE_LIGHT_ANCHOR.
	"pivot": Vector2(12, 12),
	"scale": 3.0,
	"red": {"ignite": 0, "peak": 1, "hold": 2, "fade": 3},
	"yellow": {"ignite": 4, "peak": 5, "hold": 6, "fade": 7},
	"ignite_time": 0.05,
	"peak_time": 0.04,
	"fade_time": 0.08,
}

#WHAT A CLONE LEAVES BEHIND
# Both are drawn as light, on the contact point, which is the player's own hurtbox centre.
# The break is the parry's reward, so it is spawned on the frame the parry resolves, not the one
# after; its first frame is already the full burst.
const USE_FINAL_CLONE_SHATTER := true
const PLACEHOLDER_CLONE_SHATTER := {
	"points": 7,
	"inner_ratio": 0.42,
	"radius": 70.0,
	"color": Color(1.0, 0.94, 0.78),
	"from_scale": 0.4,
	"to_scale": 1.3,
	"time": 0.22,
}
const FINAL_CLONE_SHATTER := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_parry_break.png",
	"hframes": 6,
	"frame_times": [0.04, 0.04, 0.033, 0.033, 0.033, 0.066],
	"frame_size": Vector2(96, 96),
	"pivot": Vector2(48, 48),
	"scale": 3.0,
	"additive": true,
}

# A clone that wasn't stopped: it landed, and this is the hit.
const USE_FINAL_CLONE_HIT := true
const PLACEHOLDER_CLONE_HIT := {
	"radii": Vector2(52, 34),
	"points": 18,
	"color": Color(0.5, 0.3, 0.52, 0.7),
	"from_scale": 0.6,
	"to_scale": 1.25,
	"time": 0.26,
}
const FINAL_CLONE_HIT := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_strike.png",
	"hframes": 6,
	"frame_times": [0.033, 0.033, 0.033, 0.033, 0.033, 0.05],
	"frame_size": Vector2(96, 96),
	"pivot": Vector2(48, 48),
	"scale": 3.0,
	"additive": true,
}

#THE LIGHTS COMING UP
# A 672 px bloom in the middle of the ring, not a screen white-out: what actually blows the screen
# out is the flash rect, stepped alongside it one alpha per frame.
const USE_FINAL_FINISH := true
const FINAL_FINISH := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_finish.png",
	"hframes": 5,
	"frame_times": [0.05, 0.05, 0.083, 0.066, 0.1],
	"frame_size": Vector2(224, 224),
	"pivot": Vector2(112, 112),
	"scale": 3.0,
	"at": Vector2(960, 540),
	"flash": [0.15, 0.45, 0.8, 0.3, 0.06],
}

#THE YANK
# The ghosts of the player dragged to the middle, and the dust where they land. PlayerCombatFx draws
# its own trail for warp_to(), but this yank is a drive rather than a blink, so it leaves its own.
const YANK_GHOSTS := 3
const YANK_GHOST_TINT := Color(0.72, 0.5, 1.0, 0.55)
const YANK_GHOST_FADE := 0.22
const YANK_DUST := {
	"radii": Vector2(120, 42),
	"points": 20,
	"color": Color(0.86, 0.8, 0.92, 0.5),
	"from_scale": 0.35,
	"to_scale": 1.3,
	"time": 0.3,
}

#THE FEINT PUNISH
# Its own word over his health bar rather than a PlayerDefense popup: the popup set is the defence
# coder's, and a word only this fight says doesn't belong in it.
const WORD_CENTRE := Vector2(960, 300)
const WORD_TIME := 0.9
const WORD_FONT_SIZE := 92
const WORD_COLOR := Color(1.0, 0.36, 0.3)
const WORD_OUTLINE := 10
const WORD_FROM_SCALE := 0.7
const WORD_TO_SCALE := 1.0
const WORD_GROW_TIME := 0.16
# The red pulse that runs the screen edge with it.
const EDGE_PULSE := {
	"color": Color(1.0, 0.15, 0.15, 0.55),
	"thickness": 90.0,
	"time": 0.35,
}


static func anim(anim_name: StringName) -> Dictionary:
	if USE_FINAL_ANIMS.get(anim_name, false):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS[anim_name]


# Seconds from the start of an animation to the start of its frame at `step`.
static func time_to_step(anim_name: StringName, step: int) -> float:
	var times: Array = anim(anim_name).times
	var total := 0.0
	for i in step:
		total += times[mini(i, times.size() - 1)]
	return total


# Sprite offset, in texels, that puts ANCHOR on the sprite's origin.
static func sheet_offset(frame_size: Vector2) -> Vector2:
	return frame_size / 2.0 - ANCHOR


# Screen-px offset from his feet of a point on his frames. Mirroring flips the texel column, so a
# point measured on a pose follows that pose when it faces the other way.
static func local(point: Vector2, flipped := false) -> Vector2:
	var column: float = (FRAME_SIZE.x - 1.0 - point.x) if flipped else point.x
	return (Vector2(column, point.y) - ANCHOR) * SCALE


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(local(rect.position), rect.size * SCALE)


# Sprite offset, in texels, for an effect sheet drawn at `offset` inside his 96x96 frame.
static func inset_offset(frame_size: Vector2, offset: Vector2) -> Vector2:
	return frame_size / 2.0 - (ANCHOR - offset)


# Sprite offset, in texels, that puts CLONE_ANCHOR on a clone's origin.
static func clone_sheet_offset() -> Vector2:
	return CLONE_FRAME_SIZE / 2.0 - CLONE_ANCHOR


# Over the clone's head, which is the top row of its own frame.
static func clone_light_anchor() -> Vector2:
	return Vector2(0, -CLONE_ANCHOR.y * CLONE_SCALE - CLONE_LIGHT_GAP)


# The placeholder wraith, in px around its feet.
static func clone_shape() -> PackedVector2Array:
	var shape := PackedVector2Array()
	for point in PLACEHOLDER_CLONE.shape:
		shape.append(point * CLONE_SCALE)
	return shape


static func clone_light() -> Dictionary:
	return FINAL_CLONE_LIGHT if USE_FINAL_CLONE_LIGHT else PLACEHOLDER_CLONE_LIGHT


static func clone_shatter() -> Dictionary:
	return FINAL_CLONE_SHATTER if USE_FINAL_CLONE_SHATTER else PLACEHOLDER_CLONE_SHATTER


static func clone_hit() -> Dictionary:
	return FINAL_CLONE_HIT if USE_FINAL_CLONE_HIT else PLACEHOLDER_CLONE_HIT


static func spotlight() -> Dictionary:
	return FINAL_SPOTLIGHT if USE_FINAL_SPOTLIGHT else PLACEHOLDER_SPOTLIGHT


# A filled ellipse, points on its rim, centred on the origin.
static func ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var rim := PackedVector2Array()
	for i in points:
		var angle := TAU * i / points
		rim.append(Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	return rim


# A star, for the placeholder bursts: `points` spikes out to `radius`, the dips at `inner_ratio` of it.
static func star(points: int, radius: float, inner_ratio: float) -> PackedVector2Array:
	var shape := PackedVector2Array()
	for i in points * 2:
		var angle := TAU * i / (points * 2) - PI / 2.0
		var reach := radius if i % 2 == 0 else radius * inner_ratio
		shape.append(Vector2(cos(angle), sin(angle)) * reach)
	return shape


# The four corners of a rect, for the darkness and its border.
static func rect_polygon(rect: Rect2) -> PackedVector2Array:
	return PackedVector2Array([
		rect.position, Vector2(rect.end.x, rect.position.y), rect.end,
		Vector2(rect.position.x, rect.end.y),
	])


# The border the view can be shaken into: DARK_BORDER with the view cut out of it.
static func border_rects() -> Array[Rect2]:
	var whole := DARK_BORDER
	var hole := VIEW_RECT
	return [
		Rect2(whole.position, Vector2(whole.size.x, hole.position.y - whole.position.y)),
		Rect2(Vector2(whole.position.x, hole.end.y), Vector2(whole.size.x, whole.end.y - hole.end.y)),
		Rect2(Vector2(whole.position.x, hole.position.y), Vector2(hole.position.x - whole.position.x, hole.size.y)),
		Rect2(Vector2(hole.end.x, hole.position.y), Vector2(whole.end.x - hole.end.x, hole.size.y)),
	]


# The mark's glow, the spotlight and every burst in the sequence are drawn as light, not as paint:
# flat bright shapes that have to add to what is under them rather than cover it.
static func additive() -> CanvasItemMaterial:
	var material := CanvasItemMaterial.new()
	material.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return material


# The placeholder red light: a solid diamond standing on its bottom point, which is the pivot.
static func diamond(radius: float) -> PackedVector2Array:
	return PackedVector2Array([
		Vector2(0, -radius * 2.0), Vector2(radius, -radius), Vector2(0, 0), Vector2(-radius, -radius),
	])
