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

# The fire trail's slots run along the ground-contact line fire_trail_spacing apart, counted from slot 0
# under the middle of where the full stream first touched down. Slot 0 is never lit, so every trail has an
# opening in it.
var trail_started := false
var trail_origin_x := 0.0
var trail_slots := {}
var trail_patches := 0


func Enter() -> void:
	body.play_anim(&"fly")
	_start(Phase.APPROACH)
	trail_started = false


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

	# Only the full stream reaches the floor.
	if body.current_anim == &"stream":
		_lay_trail()

	if elapsed >= state_machine.breath_time:
		state_machine.attack_finished(self)


# Lights every slot the stream's ground contact has reached that isn't lit yet, up to max_trail_patches.
func _lay_trail() -> void:
	var contact: Rect2 = body.fire_ground_contact()
	if not trail_started:
		trail_started = true
		trail_origin_x = contact.get_center().x
		trail_slots = {0: true}
		trail_patches = 0
	var spacing: float = state_machine.fire_trail_spacing
	var first := ceili((contact.position.x - trail_origin_x) / spacing)
	var last := floori((contact.end.x - trail_origin_x) / spacing)
	for slot in range(first, last + 1):
		if trail_slots.has(slot) or trail_patches >= state_machine.max_trail_patches:
			continue
		trail_slots[slot] = true
		if state_machine.lay_fire_patch(Vector2(trail_origin_x + slot * spacing, contact.get_center().y), slot):
			trail_patches += 1


func _ground_under(feet: Vector2) -> Vector2:
	return feet + Vector2(0, body.height)
