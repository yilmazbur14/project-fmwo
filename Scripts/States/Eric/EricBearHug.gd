extends State

# Eric plants his sword and charges a command grab. If the lunge catches the player he squeezes
# them, one damage per squeeze, and tosses them; a miss leaves him stumbling, open to punches.
# Either way he goes back to the sword and pulls it out.
# In the reworked fight (EricPacing V2) the charge is red or yellow, on the same art and timing: red is
# the grab, which only a parry answers, and yellow a shoulder charge, which only a dash answers and
# which ends in the stumble whether it hit or not.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")

# Over his head on the charge frames, on the same side as the whirlwind's tell and clear of his
# planted sword; his head tops out 8 texels below it.
const TELL_HEAD_PIXEL := Vector2(150, 114)
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const HUG_TEXTURE := preload("res://Assets/Characters/Eric/eric_bearhug_v2.png")
const PLANTED_SWORD_TEXTURE := preload("res://Assets/Characters/Eric/eric_bearhug_planted_sword_v2.png")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var grab_area : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node

const EricPacing := preload("res://Scripts/EricPacing.gd")
const TOSS_DIRECTION := Vector2(0.7071, -0.7071)
# Where the player's centre can be inside the ropes: the floor their body fits on, kept 3 px further
# in again so a toss never parks them flush against a rope.
const PLAYER_AREA := Rect2(126, 148.5, 1668, 783)

enum Phase { PLANT, CHARGE, LUNGE, WHIFF, STUMBLE, HOLD, RETURN, RETRIEVE }

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var phase := Phase.PLANT
var plant_spot: Vector2
var lunge_target: Vector2
var lunge_speed_now := 0.0
var charge_left := 0.0
var squeezes_left := 0
var holding := false
var planted_sword: Sprite2D
var sheet_texture: Texture2D
var sheet_frames := 0
# V2: this hug is the yellow shoulder charge rather than the red grab; the colours of the last two.
var yellow := false
var hugs_started := 0
var recent_yellows: Array[bool] = []


func Enter() -> void:
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	sprite.texture = HUG_TEXTURE
	sprite.hframes = EricArtLayout.HUG_FRAMES
	plant_spot = character_body.global_position
	lunge_speed_now = EricPacing.raged("hug_lunge_speed", eric_state_machine.rage)
	yellow = EricPacing.is_v2() and _next_is_yellow()
	hugs_started += 1
	phase = Phase.PLANT
	animation_player.play("hug_plant")


# The fight's first hug is red, never three of one colour in a row, and otherwise a coin toss.
func _next_is_yellow() -> bool:
	var pick := false
	if hugs_started > 0:
		pick = randf() < EricPacing.value("hug_yellow_chance")
		if recent_yellows.size() == 2 and recent_yellows[0] == recent_yellows[1]:
			pick = not recent_yellows[1]
	recent_yellows.append(pick)
	if recent_yellows.size() > 2:
		recent_yellows.pop_front()
	return pick


func Exit() -> void:
	ParryTell.clear(character_body)
	animation_player.speed_scale = 1.0
	if holding:
		_release_player()
	grab_area.monitoring = false
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	boss_collision_shape.disabled = false
	_remove_planted_sword()
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture


func Physics_Update(delta: float) -> void:
	match phase:
		Phase.CHARGE:
			charge_left -= delta
			if charge_left <= 0.0:
				_start_lunge()
		Phase.LUNGE:
			# Overlaps are from the last physics step, so the lunge's final position still gets
			# checked on the frame after it arrives.
			if _catches_player():
				_grab()
			elif character_body.global_position == lunge_target:
				grab_area.monitoring = false
				phase = Phase.WHIFF
				animation_player.play("hug_whiff")
			else:
				character_body.global_position = character_body.global_position.move_toward(lunge_target, lunge_speed_now * delta)
		Phase.RETURN:
			character_body.global_position = character_body.global_position.move_toward(plant_spot, EricPacing.value("hug_return_speed") * delta)
			if character_body.global_position == plant_spot and not animation_player.is_playing():
				_retrieve()
	if holding:
		# Kept where he draws them, so anything placed on the player lines up with the art.
		var frame: int = character_body.sprite.frame
		var centre: Vector2 = EricArtLayout.HUG_RELEASE_CENTRE if frame == 11 else EricArtLayout.HUG_PLAYER_CENTRES.get(frame, EricArtLayout.HUG_PLAYER_CENTRES[7])
		player.global_position = _player_point(EricArtLayout.feet_offset(centre))
		player.velocity = Vector2.ZERO


# The lunge is the hitbox: the warning has done its job by now.
func _start_lunge() -> void:
	ParryTell.clear(character_body)
	var grab_offset: Vector2 = grab_area.get_node("CollisionShape2D").global_position - character_body.global_position
	var to_player: Vector2 = player.global_position - grab_offset - character_body.global_position
	lunge_target = character_body.global_position + to_player.limit_length(EricPacing.value("hug_lunge_max_distance"))
	# Like the whirlwind, he passes through the player instead of being blocked by them.
	boss_collision_shape.disabled = true
	grab_area.monitoring = true
	_add_planted_sword()
	phase = Phase.LUNGE
	animation_player.play("hug_lunge")


func _catches_player() -> bool:
	var near_miss := false
	for area in grab_area.get_overlapping_areas():
		if area == player.hurtBox:
			# The shoulder charge hits and carries on through: it never holds anyone.
			if yellow:
				player.receive_hit(_hit())
				return false
			return player.receive_hit(_hit()) == HitInfo.Result.HIT
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: the lunge closing on the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())
	return false


# His daze anchor is tuned for his downed frames, too low for a standing tell.
func _tell_anchor() -> Vector2:
	return character_body.to_global(EricArtLayout.frame_local(TELL_HEAD_PIXEL + Vector2(0.5, 0.5), character_body.sprite.flip_h))


func _hit() -> RefCounted:
	var centre: Vector2 = grab_area.get_node("CollisionShape2D").global_position
	return HitInfo.make(hit_id(), self, centre, character_body)


# What this hug's lunge is: the grab, or V2's yellow shoulder charge. Its tell follows from the id.
func hit_id() -> StringName:
	return &"eric_shoulder_charge" if yellow else EricPacing.value("hug_grab_id")


func _grab() -> void:
	holding = true
	grab_area.monitoring = false
	player.grab()
	phase = Phase.HOLD
	animation_player.play("hug_grab")


# Frame 8, the first of each squeeze.
func _squeeze() -> void:
	squeezes_left -= 1
	animation_player.play("hug_squeeze")
	player.take_grab_damage()


func _release_player() -> void:
	holding = false
	player.global_position = _player_point(EricArtLayout.feet_offset(EricArtLayout.HUG_RELEASE_CENTRE))
	player.release_grab(TOSS_DIRECTION)


func _player_point(offset: Vector2) -> Vector2:
	return (character_body.global_position + offset).clamp(PLAYER_AREA.position, PLAYER_AREA.end)


# The planted sword isn't in his frames while he's away from it; it lines up with his sprite
# where he planted it, and sorts where his feet were, as his sprite does.
func _add_planted_sword() -> void:
	planted_sword = Sprite2D.new()
	planted_sword.texture = PLANTED_SWORD_TEXTURE
	planted_sword.scale = character_body.scale
	planted_sword.offset = EricArtLayout.SPRITE_OFFSET - EricArtLayout.SORT_POINT
	planted_sword.flip_h = character_body.sprite.flip_h
	eric_state_machine.add_hazard(planted_sword, plant_spot + EricArtLayout.SORT_POINT * character_body.scale, false)


func _remove_planted_sword() -> void:
	if is_instance_valid(planted_sword):
		planted_sword.queue_free()
	planted_sword = null


func _retrieve() -> void:
	boss_collision_shape.disabled = false
	# Frame 13 draws the sword itself as he pulls it out.
	_remove_planted_sword()
	phase = Phase.RETRIEVE
	animation_player.play("hug_retrieve")


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if eric_state_machine.current_state != self:
		return
	match anim_name:
		&"hug_plant":
			charge_left = EricPacing.raged("hug_charge_time", eric_state_machine.rage)
			phase = Phase.CHARGE
			# The charge frames are the grab's wind-up: a parry during the lunge staggers him. V2's
			# yellow charge warns in yellow on the same frames.
			ParryTell.telegraph(character_body, hit_id(), charge_left, _tell_anchor)
			animation_player.play("hug_charge")
		&"hug_whiff":
			hurtbox.monitoring = true
			hurtbox.monitorable = true
			phase = Phase.STUMBLE
			# The stumble frame is held for hug_stumble_time, whatever the clip's own length.
			animation_player.speed_scale = animation_player.get_animation(&"hug_stumble").length / EricPacing.value("hug_stumble_time")
			animation_player.play("hug_stumble")
		&"hug_stumble":
			animation_player.speed_scale = 1.0
			hurtbox.monitoring = false
			hurtbox.monitorable = false
			phase = Phase.RETURN
			animation_player.play("hug_return")
		&"hug_grab":
			squeezes_left = EricPacing.value("hug_squeezes")
			_squeeze()
		&"hug_squeeze":
			if squeezes_left > 0:
				_squeeze()
			else:
				animation_player.play("hug_toss")
		&"hug_toss":
			_release_player()
			phase = Phase.RETURN
			animation_player.play("hug_toss_end")
		&"hug_retrieve":
			eric_state_machine.attack_finished()
