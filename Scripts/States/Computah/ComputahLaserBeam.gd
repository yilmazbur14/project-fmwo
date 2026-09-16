extends State

@export var animation_player : AnimationPlayer
@export var laser_beam_left_hitbox : CollisionShape2D
@export var laser_beam_right_hitbox : CollisionShape2D
@export var laser_beam_left_area : Area2D
@export var laser_beam_right_area : Area2D
@export var laser_sfx_player : AudioStreamPlayer

var beam_length = 0.0
var beam_growth_speed := 1000.0
var max_beam_length := 400.0
var beam_finished_growing = false

func Enter():
	beam_length = 0.0
	beam_finished_growing = false

	animation_player.play("laserBeam")
	animation_player.seek(0.1, true)
	animation_player.pause()

	var left_rect := laser_beam_left_hitbox.shape as RectangleShape2D
	var right_rect := laser_beam_right_hitbox.shape as RectangleShape2D
	left_rect.size.x = 0.0
	right_rect.size.x = 0.0
	laser_beam_left_hitbox.position.x = 0.0
	laser_beam_right_hitbox.position.x = 0.0

	if laser_beam_left_area:
		laser_beam_left_area.monitoring = false
		laser_beam_left_area.monitorable = true
	if laser_beam_right_area:
		laser_beam_right_area.monitoring = false
		laser_beam_right_area.monitorable = true

	if laser_sfx_player:
		laser_sfx_player.play()

func Exit():
	if laser_beam_left_area:
		laser_beam_left_area.monitorable = false
	if laser_beam_right_area:
		laser_beam_right_area.monitorable = false

func Update(_delta: float):
	pass

func Physics_Update(_delta: float):
	if beam_finished_growing:
		return

	beam_length += beam_growth_speed * _delta

	var left_rect := laser_beam_left_hitbox.shape as RectangleShape2D
	var right_rect := laser_beam_right_hitbox.shape as RectangleShape2D

	left_rect.size.x = beam_length
	right_rect.size.x = beam_length

	laser_beam_left_hitbox.position.x = -beam_length / 2.0
	laser_beam_right_hitbox.position.x = beam_length / 2.0

	if beam_length >= max_beam_length:
		beam_finished_growing = true

		# Continue the animation
		animation_player.seek(0.2, true)
		animation_player.pause()
