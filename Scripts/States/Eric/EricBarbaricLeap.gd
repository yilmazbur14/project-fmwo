extends State

# Eric's phase-two leap: five jumps at wherever the player is standing, each landing sending an
# earthquake tremor out in a ring from the spot he came down on, then a rest he can be punched in.
# Target locked at takeoff and re-aimed for every leap, so running is answered by the next one.
#
# The arc drives his global_position along the ground path and puts the LIFT ON sprite.offset ALONE,
# never on position: frame_point() and the fight's y-sort both hang off his position, and lifting it
# would move his ground point into the air with him. PlayerFinisher._hop() is the precedent.
#
# The tell is the floor marker (EricSwordMark), not a badge over his head - he is in the air, and the
# thing the player needs to read is where he is coming down, not that he exists. The mark runs off the
# flight's own progress, so it cannot drift from him and it stops dead wherever he does, and it lights
# its commit frame exactly PlayerDefense.parry_window before he touches down.
#
# FAIRNESS RULE, NON-NEGOTIABLE: landing to landing never comes in under
# AttackCatalog.DASH_IMMUNITY_COOLDOWN + p2_leap_dodge_lead, so every one of the five tremors can be
# dashed. A dash is only immune that long after the last one started, so two tremors closer together
# than the cooldown would hand the player a tremor with no answer at all. The crouch holds until the
# next landing clears it - the same rule and the same reasoning as EricWhirlwind's whirl_dodge_lead.

const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const EricPhaseTwoPose := preload("res://Scripts/EricPhaseTwoPose.gd")
const EricSwordMark := preload("res://Scripts/EricSwordMark.gd")
const RING_SCENE := preload("res://Scenes/Bosses/EricQuakeRingScene.tscn")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node

# Where his origin may come down: his body inside the ropes, the whirlwind's own lunge area.
const LEAP_AREA := Rect2(240, 180, 1440, 590)
# How high the arc carries his sprite, in px.
const LEAP_HEIGHT := 420.0

enum Phase { CROUCH, AIR, LAND, REST }

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var phase := Phase.CROUCH
var phase_left := 0.0
var rage := 0.0
var leaps_left := 0
var clock := 0.0
# When the last tremor went out, so the next landing can be held back until it can be dashed; -1
# before the first one.
var landed_at := -1.0
var from_ground := Vector2.ZERO
var to_ground := Vector2.ZERO
var air_time := 0.0
var mark: Node2D
var shadow: Sprite2D
var sheet_texture: Texture2D
var sheet_frames := 0
var rest_offset := Vector2.ZERO
var pose_frames: Array = []
var pose_clock := 0.0


func Enter() -> void:
	rage = eric_state_machine.rage
	clock = 0.0
	landed_at = -1.0
	leaps_left = EricPacing.value("p2_leaps")
	animation_player.stop()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	rest_offset = sprite.offset
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	_spawn_shadow()
	_start_crouch()


func Exit() -> void:
	_clear_mark()
	if is_instance_valid(shadow):
		shadow.queue_free()
	shadow = null
	var sprite: Sprite2D = character_body.sprite
	sprite.offset = rest_offset
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	boss_collision_shape.disabled = false


func Physics_Update(delta: float) -> void:
	clock += delta
	_step_pose(delta)
	phase_left -= delta
	match phase:
		Phase.CROUCH:
			if phase_left <= 0.0 and _next_landing_dodgeable():
				_take_off()
		Phase.AIR:
			var t: float = clampf(1.0 - phase_left / air_time, 0.0, 1.0)
			character_body.global_position = from_ground.lerp(to_ground, t)
			_set_lift(LEAP_HEIGHT * 4.0 * t * (1.0 - t))
			if is_instance_valid(mark):
				mark.set_progress(t)
			if phase_left <= 0.0:
				_land()
		Phase.LAND:
			if phase_left <= 0.0:
				if leaps_left > 0:
					_start_crouch()
				else:
					_start_rest()
		Phase.REST:
			if phase_left <= 0.0:
				eric_state_machine.attack_finished()


# Off the mat and through the air he is untouchable, and he passes over the player rather than
# shoving them around the ring.
func _start_crouch() -> void:
	phase = Phase.CROUCH
	phase_left = EricPacing.p2("p2_leap_crouch", rage)
	boss_collision_shape.disabled = true
	_set_lift(0.0)
	_show("crouch")


# A dash is only immune AttackCatalog.DASH_IMMUNITY_COOLDOWN after the last one, so a tremor landing
# too soon after the one before it could not be dodged at all. The crouch holds until the next
# landing clears that cooldown plus its lead.
func _next_landing_dodgeable() -> bool:
	if landed_at < 0.0:
		return true
	var ready_at: float = landed_at + AttackCatalog.DASH_IMMUNITY_COOLDOWN + EricPacing.value("p2_leap_dodge_lead")
	return clock + EricPacing.p2("p2_leap_air", rage) >= ready_at


# He comes down feet on the player's feet, so the tremor's ring is centred where they were standing
# when he left the mat rather than a body's height below it.
func _take_off() -> void:
	leaps_left -= 1
	from_ground = character_body.global_position
	to_ground = (_player_feet() - _ground_offset()).clamp(LEAP_AREA.position, LEAP_AREA.end)
	character_body.sprite.flip_h = to_ground.x < from_ground.x
	air_time = EricPacing.p2("p2_leap_air", rage)
	phase = Phase.AIR
	phase_left = air_time
	_mark_landing()
	_show("air")


# The floor marker under where he is coming down, on the fight's floor layer with his other ground
# marks. Its commit frame lights a parry window before he arrives, which is what the player reads.
func _mark_landing() -> void:
	_clear_mark()
	mark = EricSwordMark.new()
	mark.name = "LeapMark"
	mark.commit_at = maxf(1.0 - player.defense.parry_window / air_time, 0.0)
	eric_state_machine.add_hazard(mark, to_ground + _ground_offset())
	mark.set_progress(0.0)


func _player_feet() -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var rect: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(rect.get_center().x, rect.end.y)


# From his origin to the mat under his feet. Constant: FEET_ANCHOR is the middle of his frame, so it
# does not move when he is drawn mirrored.
func _ground_offset() -> Vector2:
	return EricArtLayout.pixel_offset(Vector2(EricArtLayout.FEET_ANCHOR.x, EricArtLayout.FEET_ROW))


func _land() -> void:
	character_body.global_position = to_ground
	_set_lift(0.0)
	landed_at = clock
	if is_instance_valid(mark):
		mark.land()
	mark = null
	phase = Phase.LAND
	phase_left = EricPacing.p2("p2_leap_land", rage)
	_show("land")
	_send_tremor()


func _send_tremor() -> void:
	var ring = RING_SCENE.instantiate()
	ring.attack_id = &"eric_p2_tremor"
	ring.speed = EricPacing.p2("p2_tremor_speed", rage)
	ring.player = player
	eric_state_machine.add_hazard(ring, _feet())


# The five are over: he is blown, on the mat and open to punches.
func _start_rest() -> void:
	phase = Phase.REST
	phase_left = EricPacing.p2("p2_leap_rest", rage)
	boss_collision_shape.disabled = false
	hurtbox.monitoring = true
	hurtbox.monitorable = true
	if is_instance_valid(shadow):
		shadow.visible = false
	_show("rest")


# On his sprite alone: his position is his ground point, and the y-sort and frame_point() both read it.
func _set_lift(px: float) -> void:
	var sprite: Sprite2D = character_body.sprite
	sprite.offset.y = rest_offset.y - px / sprite.global_scale.y
	if not is_instance_valid(shadow):
		return
	var spec := EricArtLayout.JUGGLE_SHADOW
	shadow.visible = px > 0.0
	shadow.frame = clampi(int(px / spec.step), 0, spec.hframes - 1)
	shadow.global_position = _feet().round()


func _feet() -> Vector2:
	return character_body.frame_point(Vector2(EricArtLayout.FEET_ANCHOR.x, EricArtLayout.FEET_ROW))


func _spawn_shadow() -> void:
	var spec := EricArtLayout.JUGGLE_SHADOW
	shadow = Sprite2D.new()
	shadow.texture = load(spec.texture)
	shadow.hframes = spec.hframes
	shadow.scale = Vector2.ONE * spec.scale
	shadow.modulate.a = spec.alpha
	shadow.visible = false
	eric_state_machine.ground_layer().add_child(shadow)
	shadow.global_position = _feet().round()


func _clear_mark() -> void:
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null


func _show(key: String) -> void:
	pose_frames = EricPhaseTwoPose.show(character_body.sprite, key)
	pose_clock = 0.0


func _step_pose(delta: float) -> void:
	pose_clock += delta
	character_body.sprite.frame = EricPhaseTwoPose.frame_at(pose_frames, pose_clock)
