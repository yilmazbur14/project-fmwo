extends State

# Eric plants his sword and charges a command grab. If the lunge catches the player he squeezes
# them, one damage per squeeze, and tosses them; a miss leaves him stumbling, open to punches.
# Either way he goes back to the sword and pulls it out.

const DashImmunity := preload("res://Scripts/DashImmunity.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const HUG_TEXTURE := preload("res://Assets/Characters/Eric/eric_bearhug_v2.png")
const PLANTED_SWORD_TEXTURE := preload("res://Assets/Characters/Eric/eric_bearhug_planted_sword_v2.png")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var grab_area : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node

# Telegraph length and lunge speed in px/s, at full health and at none.
@export var charge_time := 0.9
@export var rage_charge_time := 0.65
@export var lunge_speed := 1500.0
@export var rage_lunge_speed := 1800.0
@export var lunge_max_distance := 650.0
@export var return_speed := 900.0
@export var squeezes := 3
@export var dash_immunity_time := 0.18
@export var dash_immunity_cooldown := 0.6

const TOSS_DIRECTION := Vector2(0.7071, -0.7071)
# Where the player's centre can be inside the ropes.
const PLAYER_AREA := Rect2(120, 135, 1680, 810)

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


func Enter() -> void:
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	sprite.texture = HUG_TEXTURE
	sprite.hframes = EricArtLayout.HUG_FRAMES
	plant_spot = character_body.global_position
	lunge_speed_now = lerpf(lunge_speed, rage_lunge_speed, eric_state_machine.rage)
	phase = Phase.PLANT
	animation_player.play("hug_plant")


func Exit() -> void:
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
			character_body.global_position = character_body.global_position.move_toward(plant_spot, return_speed * delta)
			if character_body.global_position == plant_spot and not animation_player.is_playing():
				_retrieve()
	if holding:
		# Kept where he draws them, so anything placed on the player lines up with the art.
		var frame: int = character_body.sprite.frame
		var centre: Vector2 = EricArtLayout.HUG_RELEASE_CENTRE if frame == 11 else EricArtLayout.HUG_PLAYER_CENTRES.get(frame, EricArtLayout.HUG_PLAYER_CENTRES[7])
		player.global_position = _player_point(EricArtLayout.feet_offset(centre))
		player.velocity = Vector2.ZERO


func _start_lunge() -> void:
	var grab_offset: Vector2 = grab_area.get_node("CollisionShape2D").global_position - character_body.global_position
	var to_player: Vector2 = player.global_position - grab_offset - character_body.global_position
	lunge_target = character_body.global_position + to_player.limit_length(lunge_max_distance)
	# Like the whirlwind, he passes through the player instead of being blocked by them.
	boss_collision_shape.disabled = true
	grab_area.monitoring = true
	_add_planted_sword()
	phase = Phase.LUNGE
	animation_player.play("hug_lunge")


func _catches_player() -> bool:
	if player.is_invincible or player.is_grabbed:
		return false
	for area in grab_area.get_overlapping_areas():
		if area == player.hurtBox:
			return not DashImmunity.is_immune(player, dash_immunity_time, dash_immunity_cooldown)
	return false


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
# where he planted it.
func _add_planted_sword() -> void:
	planted_sword = Sprite2D.new()
	planted_sword.texture = PLANTED_SWORD_TEXTURE
	planted_sword.scale = character_body.scale
	planted_sword.offset = EricArtLayout.SPRITE_OFFSET
	planted_sword.flip_h = character_body.sprite.flip_h
	eric_state_machine.add_hazard(planted_sword, plant_spot)


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
			charge_left = lerpf(charge_time, rage_charge_time, eric_state_machine.rage)
			phase = Phase.CHARGE
			animation_player.play("hug_charge")
		&"hug_whiff":
			hurtbox.monitoring = true
			hurtbox.monitorable = true
			phase = Phase.STUMBLE
			animation_player.play("hug_stumble")
		&"hug_stumble":
			hurtbox.monitoring = false
			hurtbox.monitorable = false
			phase = Phase.RETURN
			animation_player.play("hug_return")
		&"hug_grab":
			squeezes_left = squeezes
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
