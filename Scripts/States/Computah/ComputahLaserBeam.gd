extends State

# Emitter origins are wherever these two LaserBeamProjectileScene instances
# are placed; their parent's scale sets the on-screen beam thickness.
@export var laser_beam_left : Area2D
@export var laser_beam_right : Area2D
@export var animation_player : AnimationPlayer
@export var charge_animation := &"laserCharge"
@export var fire_animation := &"laserBeam"
@export var laser_sfx_player : AudioStreamPlayer

@export var telegraph_duration := 0.5
# Overwritten by the state machine's rage scaling each cycle.
@export var sweep_duration := 2.0
@export var fade_duration := 0.2

# Beams start tilted up so hugging the top rope isn't safe, then sweep down
# past vertical so they cross under the attacker.
@export var start_angle_up_degrees := 10.0
@export var cross_past_vertical_degrees := 20.0

# In the beam scene's local units. The art is 23 px tall with a 1 px dark
# outline on each side; 21 skips the outline so grazing the edge doesn't hurt.
@export var hitbox_thickness := 21.0

enum Phase { TELEGRAPH, SWEEP, FADE }

const HitInfo := preload("res://Scripts/HitInfo.gd")

const BEAM_EXTEND_DURATION := 0.08
const BEAM_TEXTURE_HEIGHT := 23.0
const BEAM_TEXTURE_WIDTH := 16.0
# Beam and hitbox start slightly behind the emitter (hidden under the flare)
# so the gap between each emitter and the attacker's body isn't a safe pocket.
const BEAM_BACK_LENGTH := 6.0
const AIM_TEXTURE_WIDTH := 12.0

const AIM_FLICKER_TIME := 0.05
const AIM_DIM_ALPHA := 0.6
const AIM_SCROLL_SPEED := 40.0
const SHIMMER_FRAME_TIME := 0.06
const SHIMMER_SCROLL_SPEED := 90.0

# Recomputed on Enter so the beams always reach the screen edge.
var beam_length := 0.0

var phase := Phase.TELEGRAPH
var elapsed := 0.0


func get_total_duration() -> float:
	return telegraph_duration + sweep_duration + fade_duration


func Enter():
	elapsed = 0.0
	phase = Phase.TELEGRAPH
	animation_player.play(charge_animation)
	beam_length = ceilf(laser_beam_left.get_viewport_rect().size.length() / absf(laser_beam_left.global_scale.x))

	for beam in _beams():
		beam.monitoring = false
		beam.modulate.a = 1.0
		var aim_line := beam.get_node("AimLine") as Sprite2D
		aim_line.region_rect.size.x = beam_length
		aim_line.visible = true
		beam.get_node("EmitterFlare").visible = true
		beam.get_node("Beam").visible = false

	_set_sweep(0.0)
	_set_beam_length(0.0)
	_update_telegraph_fx()


func Exit():
	for beam in _beams():
		beam.monitoring = false
		beam.modulate.a = 1.0
		for part in ["AimLine", "Beam", "EmitterFlare"]:
			beam.get_node(part).visible = false
	_set_sweep(0.0)
	_set_beam_length(0.0)


func Update(_delta: float):
	pass


func Physics_Update(_delta: float):
	elapsed += _delta

	if phase == Phase.TELEGRAPH and elapsed >= telegraph_duration:
		_start_sweep()
	if phase == Phase.SWEEP and elapsed >= telegraph_duration + sweep_duration:
		_start_fade()

	match phase:
		Phase.TELEGRAPH:
			_update_telegraph_fx()
		Phase.SWEEP:
			var sweep_time := elapsed - telegraph_duration
			var progress := clampf(sweep_time / sweep_duration, 0.0, 1.0)
			_set_sweep((1.0 - cos(PI * progress)) / 2.0)
			_set_beam_length(floorf(beam_length * clampf(sweep_time / BEAM_EXTEND_DURATION, 0.0, 1.0)))
			_update_beam_fx()
			_damage_players_in_beams()
		Phase.FADE:
			var fade_time := elapsed - telegraph_duration - sweep_duration
			for beam in _beams():
				beam.modulate.a = clampf(1.0 - fade_time / fade_duration, 0.0, 1.0)
			_update_beam_fx()


func _start_sweep() -> void:
	phase = Phase.SWEEP
	animation_player.play(fire_animation)
	for beam in _beams():
		beam.get_node("AimLine").visible = false
		beam.get_node("Beam").visible = true
		beam.monitoring = true
	if laser_sfx_player:
		laser_sfx_player.play()


func _start_fade() -> void:
	phase = Phase.FADE
	_set_sweep(1.0)
	_set_beam_length(beam_length)
	for beam in _beams():
		beam.monitoring = false


# The beams aren't in the "enemy projectile" group (that damages dashing players too): they report
# their own hits, and PlayerDefense applies the dash-through rule the laser is built around.
func _damage_players_in_beams() -> void:
	for beam in _beams():
		for area in beam.get_overlapping_areas():
			var player := area.get_parent()
			if player.get("hurtBox") == area:
				player.receive_hit(HitInfo.make(&"computah_laser", beam, beam.global_position))


func _beams() -> Array[Area2D]:
	return [laser_beam_left, laser_beam_right]


func _set_sweep(amount: float) -> void:
	var start_up := deg_to_rad(start_angle_up_degrees)
	var total_angle := start_up + PI / 2.0 + deg_to_rad(cross_past_vertical_degrees)
	laser_beam_left.rotation = PI + start_up - total_angle * amount
	laser_beam_right.rotation = -start_up + total_angle * amount
	# Keep the round flare upright so it stays pixel-crisp.
	for beam in _beams():
		beam.get_node("EmitterFlare").rotation = -beam.rotation


func _set_beam_length(length: float) -> void:
	for beam in _beams():
		var beam_sprite := beam.get_node("Beam") as Sprite2D
		beam_sprite.position.x = -BEAM_BACK_LENGTH
		beam_sprite.region_rect.size = Vector2(BEAM_BACK_LENGTH + length, BEAM_TEXTURE_HEIGHT)

		var hitbox := beam.get_node("CollisionShape2D") as CollisionShape2D
		var rect := hitbox.shape as RectangleShape2D
		rect.size = Vector2(BEAM_BACK_LENGTH + length, hitbox_thickness)
		hitbox.position.x = (length - BEAM_BACK_LENGTH) / 2.0


func _flicker_on(interval: float) -> bool:
	return int(elapsed / interval) % 2 == 0


func _update_telegraph_fx() -> void:
	var flicker_on := _flicker_on(AIM_FLICKER_TIME)
	var scroll := fposmod(-floorf(elapsed * AIM_SCROLL_SPEED), AIM_TEXTURE_WIDTH)
	for beam in _beams():
		var aim_line := beam.get_node("AimLine") as Sprite2D
		aim_line.modulate.a = 1.0 if flicker_on else AIM_DIM_ALPHA
		aim_line.region_rect.position.x = scroll
		beam.get_node("EmitterFlare").frame = 0 if flicker_on else 1


func _update_beam_fx() -> void:
	var shimmer_on := _flicker_on(SHIMMER_FRAME_TIME)
	var scroll := fposmod(-floorf(elapsed * SHIMMER_SCROLL_SPEED), BEAM_TEXTURE_WIDTH)
	for beam in _beams():
		var beam_sprite := beam.get_node("Beam") as Sprite2D
		beam_sprite.region_rect.position = Vector2(scroll, 0.0 if shimmer_on else BEAM_TEXTURE_HEIGHT)
		beam.get_node("EmitterFlare").frame = 0 if shimmer_on else 1
