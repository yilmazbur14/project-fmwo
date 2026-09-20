extends Node2D

# The punch's own effects, part of "feel v2" (Eric's fight first), drawn at the player's 2x texel
# density:
# - the swoosh, a crescent in front of the fist on the swing's extension frames. Its full-extension
#   frame is the v2 punch hitbox drawn out (art_source/punch_fx/design.py, V2_BOXES): its far edge and
#   both sides are exactly what the punch hits. An afterimage holds the far edge for a beat once the
#   arm is back, which is when a landed punch reports;
# - the star, a small burst where a landed punch met the boss, gold for a combo's charged punch;
# - the whoosh, a short swing sound as the arm snaps out, 9 dB under hit_impact.ogg.
#
# A child of the player's CharacterBody2D (Scenes/Player/PunchFx.tscn). swing() is the one call a punch
# makes, as it starts; the star follows the combo's punch_landed signal by itself. Nothing shows or
# sounds unless the player's feel_v2 is on.
#
# Freeze-safe: the swoosh follows the player's own sheet column, so it holds whenever his
# AnimationPlayer holds, and the afterimage and the star count game-time delta in _process, so a
# hit-stop slows them with the fight. No SceneTree timers or tree tweens. A finisher's freeze keeps
# the player's branch running, and this with it, but nothing here is alive by then: the finisher
# settles for 0.2 s of game time after the charged hit reports, and the star, the last thing to go,
# is over 0.16 s after that same report.
# The sprites are top_level, so they stay where the punch was once the player moves on, and draw over
# the boss at FX_Z_INDEX, the finisher's effects layer: unlike the dash's effects (PlayerDashFx), which
# sit under the player, these have to show on top of whatever the fist reached.

# player_4dir_sheet.png's punch columns that show a swoosh frame: 7 the arm snapping out, 8 full extension.
const SWOOSH_FRAME_BY_COLUMN := {7: 0, 8: 1}
const FULL_EXTENSION_FRAME := 1
const AFTERIMAGE_FRAME := 2
# Game seconds the afterimage holds once the arm is back. The swing's report lands two physics frames
# after the swing ends, so a landed punch's star comes up on top of it.
const AFTERIMAGE_TIME := 0.07
# Game seconds per star frame. The first is held through the hit's hit-stop, which slows time to 5%.
const STAR_FRAME_TIMES := [0.05, 0.05, 0.06]
const STAR_ROW := 0
const STAR_ROW_CHARGED := 1
# The front of the glove on the full-extension frame, in texels from the frame centre, per facing
# (PlayerScript.Facing: down, up, left, right). A landed punch's star is never nearer the player than
# this. The down glove is drawn over the body, so its front is the glove's bottom edge.
const GLOVE_FRONTS := [Vector2(0.5, 11.0), Vector2(-4.0, -16.0), Vector2(-11.0, -6.0), Vector2(11.0, -6.0)]
const FX_Z_INDEX := 2
# Per swing, so a mashed jab doesn't sound like a loop.
const WHOOSH_PITCH_SPREAD := 0.06

@onready var player: CharacterBody2D = get_parent()
@onready var combo: Node = get_parent().get_node("Combo")
@onready var swoosh: Sprite2D = $Swoosh
@onready var star: Sprite2D = $Star
@onready var whoosh: AudioStreamPlayer = $WhooshSfxPlayer

var swinging := false
# The full-extension frame has shown this swing.
var reached := false
var whooshed := false
var afterimage_left := 0.0
var swing_facing := 0
# The punch hitbox's global rect and the player's transform, kept from the swing: the report lands
# after the swing, when the player may already be moving.
var reach_rect := Rect2()
var swing_transform := Transform2D.IDENTITY
# Game seconds into the star, or -1 while there is none.
var star_clock := -1.0


func _ready() -> void:
	for sprite in [swoosh, star]:
		sprite.top_level = true
		sprite.z_index = FX_Z_INDEX
		sprite.hide()
	combo.punch_landed.connect(_on_punch_landed)


func is_enabled() -> bool:
	return player.feel_v2


# Called as a punch starts (PlayerPunching.Enter). The swoosh then follows the swing by itself.
func swing() -> void:
	if not is_enabled():
		return
	swinging = true
	reached = false
	whooshed = false
	afterimage_left = 0.0
	swing_facing = player.facing
	_keep_reach()
	swoosh.hide()


func _process(delta: float) -> void:
	_step_swoosh(delta)
	_step_star(delta)


func _step_swoosh(delta: float) -> void:
	if swinging:
		if not _still_swinging():
			swinging = false
			# A swing cut off before it reached full extension, like a grab, leaves nothing behind.
			if reached and player.sprite.visible:
				afterimage_left = AFTERIMAGE_TIME
				_show_swoosh(AFTERIMAGE_FRAME)
			else:
				swoosh.hide()
			return
		_keep_reach()
		var frame: int = SWOOSH_FRAME_BY_COLUMN.get(player.sprite.frame_coords.x, -1)
		if frame < 0:
			swoosh.hide()
			return
		if frame == FULL_EXTENSION_FRAME:
			reached = true
		if not whooshed:
			whooshed = true
			whoosh.pitch_scale = 1.0 + randf_range(-WHOOSH_PITCH_SPREAD, WHOOSH_PITCH_SPREAD)
			whoosh.play()
		swoosh.global_position = player.sprite.global_position
		_show_swoosh(frame)
	elif afterimage_left > 0.0:
		afterimage_left -= delta
		if afterimage_left <= 0.0:
			swoosh.hide()


func _still_swinging() -> bool:
	return player.state_machine.current_state.name == "Punching" and player.sprite.visible and not player.is_grabbed


func _show_swoosh(frame: int) -> void:
	swoosh.frame_coords = Vector2i(frame, swing_facing)
	swoosh.scale = player.sprite.global_scale
	swoosh.offset = player.sprite.offset
	swoosh.show()


func _keep_reach() -> void:
	var shape: CollisionShape2D = player.punch_hitbox
	reach_rect = shape.global_transform * (shape.shape as RectangleShape2D).get_rect()
	swing_transform = player.global_transform


func _on_punch_landed(target: Node, dealt: int, charged: bool) -> void:
	if not is_enabled() or dealt <= 0:
		return
	# A swing that never called swing() still has its hitbox where it hit.
	if not reach_rect.has_area():
		_keep_reach()
		swing_facing = player.facing
	star.frame_coords = Vector2i(0, STAR_ROW_CHARGED if charged else STAR_ROW)
	star.scale = player.sprite.global_scale
	star.global_position = contact_point(target).round()
	star.show()
	star_clock = 0.0


func _step_star(delta: float) -> void:
	if star_clock < 0.0:
		return
	star_clock += delta
	var t := star_clock
	for i in STAR_FRAME_TIMES.size():
		if t < STAR_FRAME_TIMES[i]:
			star.frame_coords = Vector2i(i, star.frame_coords.y)
			return
		t -= STAR_FRAME_TIMES[i]
	star.hide()
	star_clock = -1.0


# Where the fist met the target: the near face of the target's hurtbox inside the reach, along the
# punch, but never nearer than the glove's front and never past the reach's far edge; centred across
# the part of the reach the hurtbox covers. With no hurtbox found, the glove's front.
func contact_point(target: Node) -> Vector2:
	var reach := reach_rect
	var overlap := reach.intersection(_target_rect(target, reach))
	if not overlap.has_area():
		overlap = reach
	var front: Vector2 = swing_transform * GLOVE_FRONTS[swing_facing]
	var middle := overlap.get_center()
	if swing_facing == player.Facing.RIGHT:
		return Vector2(clampf(overlap.position.x, front.x, reach.end.x), middle.y)
	if swing_facing == player.Facing.LEFT:
		return Vector2(clampf(overlap.end.x, reach.position.x, front.x), middle.y)
	if swing_facing == player.Facing.UP:
		return Vector2(middle.x, clampf(overlap.end.y, reach.position.y, front.y))
	return Vector2(middle.x, clampf(overlap.position.y, front.y, reach.end.y))


# The target's own face-able hurtbox (group boss_target, shaped by a child CollisionShape2D), or else
# any such hurtbox the reach overlaps.
func _target_rect(target: Node, reach: Rect2) -> Rect2:
	var fallback := Rect2()
	for area in get_tree().get_nodes_in_group(player.BOSS_TARGET_GROUP):
		var shape := area.get_node_or_null("CollisionShape2D") as CollisionShape2D
		if shape == null or shape.shape == null:
			continue
		var rect: Rect2 = shape.global_transform * shape.shape.get_rect()
		if is_instance_valid(target) and (area == target or target.is_ancestor_of(area)):
			return rect
		if not fallback.has_area() and rect.intersects(reach):
			fallback = rect
	return fallback
