extends State

@export var body : CharacterBody2D
@export var windup_sfx_player : AudioStreamPlayer
@export var breath_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { APPROACH, WINDUP, BREATH }

var phase := Phase.APPROACH
var elapsed := 0.0
# Where his feet breathe from.
var aim := Vector2.ZERO


func Enter() -> void:
	body.play_anim(&"fly")
	_start(Phase.APPROACH)


func Exit() -> void:
	breath_sfx_player.stop()


func Physics_Update(delta: float) -> void:
	elapsed += delta
	var player = state_machine.get_player()
	match phase:
		# The telegraph: he flies over the player, following them until he's lined up.
		Phase.APPROACH:
			if player:
				aim = body.breath_aim(player.global_position)
			var off_aim: float = body.fly_toward(_ground_under(aim), state_machine.breath_approach_speed, delta)
			if off_aim <= state_machine.breath_align_distance or elapsed >= state_machine.breath_approach_time:
				_start(Phase.WINDUP)
				body.play_anim(&"windup")
				windup_sfx_player.play()
		# The aim is locked: he only settles onto it.
		Phase.WINDUP:
			body.fly_toward(_ground_under(aim), state_machine.breath_approach_speed, delta)
			if elapsed >= state_machine.breath_windup:
				_start(Phase.BREATH)
				aim = body.feet_position()
				body.fly_velocity = Vector2.ZERO
				body.play_anim(&"burst")
				breath_sfx_player.play()
		Phase.BREATH:
			_breathe(player, delta)


func _start(new_phase: Phase) -> void:
	phase = new_phase
	elapsed = 0.0


# The stream bursts out, runs at full length, and dies back to a burst before it stops, following the
# player sideways at breath_drift_speed. The fire hitbox follows the frames.
func _breathe(player: Node2D, delta: float) -> void:
	var burst: float = state_machine.breath_burst_time
	var full: bool = elapsed >= burst and elapsed < state_machine.breath_time - burst
	var frame_anim := &"stream" if full else &"burst"
	if body.current_anim != frame_anim:
		body.play_anim(frame_anim)

	if player:
		aim.x = move_toward(aim.x, body.breath_aim(player.global_position).x, state_machine.breath_drift_speed * delta)
		body.ground_position = _ground_under(aim)
		body.place()
		# Not dash-immune. Standing in it hurts again as soon as the player's invincibility runs out.
		if body.fire_touches(player.hurtBox):
			player.take_damage()

	if elapsed >= state_machine.breath_time:
		state_machine.attack_finished(self)


func _ground_under(feet: Vector2) -> Vector2:
	return feet + Vector2(0, body.height)
