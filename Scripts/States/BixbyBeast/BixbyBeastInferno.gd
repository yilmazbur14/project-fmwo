extends State

# His Inferno. He flies up to the middle of the top rope and hangs off it facing down the ring, the boss bar
# fading out from over him, and spits a volley of fireballs up off the top of the screen. Then he inhales:
# the player is dragged toward his mouths while the fireballs rain back down on them, tracking them, and the
# pull ends as the last one lands. He rears back with no pull under a yellow ring, for longer than the
# longest run out of the fire takes, then breathes one giant cone straight down the ring over roughly three
# quarters of it, leaving the two upper corners beside him, and embers burning in it. Spent, he lets go and
# drops to the mat under the rope for a long recharge: the punish window, with the embers burnt out of the
# player's straight way to it.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Ember := preload("res://Scripts/BixbyEmberScript.gd")
const FIREBALL_SCENE := preload("res://Scenes/Bosses/BixbyFireballScene.tscn")
const RISE_SCENE := preload("res://Scenes/Bosses/BixbyFireballRiseScene.tscn")
const FLOOD_SCENE := preload("res://Scenes/Bosses/BixbyInfernoFloodScene.tscn")
const SUCTION_SCENE := preload("res://Scenes/Bosses/BixbySuctionScene.tscn")
const EMBER_SCENE := preload("res://Scenes/Bosses/BixbyEmberScene.tscn")

@export var body : CharacterBody2D
@export var inhale_sfx_player : AudioStreamPlayer
@export var spit_sfx_player : AudioStreamPlayer
@export var gulp_sfx_player : AudioStreamPlayer
@export var windup_sfx_player : AudioStreamPlayer
@export var roar_sfx_player : AudioStreamPlayer
@export var breath_sfx_player : AudioStreamPlayer
@export var rope_sfx_player : AudioStreamPlayer
@export var wing_sfx_player : AudioStreamPlayer
@export var flash : ColorRect

@onready var state_machine = get_parent()

enum Phase { APPROACH, PERCH, VOLLEY, SKY, INHALE, WINDUP, BREATH, SPENT }

# He takes the rope once he's this close to hanging from it.
const PERCH_ALIGN_DISTANCE := 8.0
# The spit sound on every third fireball, or the volley is one long hiss.
const SPIT_SOUND_EVERY := 3
# The breath going off.
const BREATH_SHAKE := 14.0
const BREATH_SHAKE_STEPS := 6
const BREATH_SHAKE_STEP_TIME := 0.03
const BREATH_FLASH_COLOR := Color(1.0, 0.78, 0.45)
const BREATH_FLASH_ALPHA := 0.55
const BREATH_FLASH_TIME := 0.1
const BREATH_CHEER := 1.5
# An ember goes down at least this far from the player, clear of his landed body by this much, and gets
# this many tries at a spot.
const EMBER_PLAYER_CLEARANCE := 140.0
const EMBER_LANDING_KEEP_OUT := 100.0
const EMBER_TRIES := 40

var phase := Phase.APPROACH
var elapsed := 0.0
var perch_feet := Vector2.ZERO
# Where the breath's cone comes to its point, in px.
var cone_apex := Vector2.ZERO
var spits := 0
var dropped := 0
var landed := 0
var released := false
var rising: Array = []
var fireballs: Array = []
var flood: Node2D
var suction: Node2D


func Enter() -> void:
	perch_feet = InfernoLayout.perch_point()
	cone_apex = InfernoLayout.cone_apex()
	spits = 0
	dropped = 0
	landed = 0
	released = false
	rising.clear()
	fireballs.clear()
	flood = null
	suction = null
	_start(Phase.APPROACH)
	body.play_anim(&"fly")
	wing_sfx_player.play()


# Nothing of the attack itself outlives it, and he always leaves the rope. The embers stay: they are fire
# on the floor, not his, and burn out on their own.
func Exit() -> void:
	ParryTell.clear(body)
	inhale_sfx_player.stop()
	breath_sfx_player.stop()
	for node in rising + fireballs:
		if is_instance_valid(node):
			node.queue_free()
	rising.clear()
	fireballs.clear()
	if is_instance_valid(suction):
		suction.queue_free()
	# The die-down is harmless, so only a flood cut off before it gets there goes with him.
	if phase != Phase.SPENT and is_instance_valid(flood):
		flood.queue_free()
	body.leave_rope(InfernoLayout.release_drop())


func Physics_Update(delta: float) -> void:
	elapsed += delta
	match phase:
		Phase.APPROACH:
			var off: float = body.fly_toward(perch_feet + Vector2(0, body.height), state_machine.inferno_perch_speed, delta)
			if off <= PERCH_ALIGN_DISTANCE or elapsed >= state_machine.inferno_perch_time:
				_perch()
		Phase.PERCH:
			if elapsed >= BixbyBeastArtLayout.anim_time(&"perch_land"):
				_start(Phase.VOLLEY)
				body.play_anim(&"volley")
		Phase.VOLLEY:
			var interval: float = state_machine.inferno_volley_time / maxi(state_machine.inferno_fireballs, 1)
			while spits < state_machine.inferno_fireballs and elapsed >= spits * interval:
				_spit()
			if elapsed >= state_machine.inferno_volley_time:
				_start(Phase.SKY)
				body.play_anim(&"perch")
		Phase.SKY:
			if elapsed >= state_machine.inferno_sky_beat:
				_start_inhale()
		Phase.INHALE:
			while dropped < state_machine.inferno_fireballs and elapsed >= state_machine.inferno_first_marker + dropped * state_machine.inferno_marker_interval:
				_drop_fireball()
			# The last landing ends the inhale itself (_on_fireball_landed); this is a shower of none.
			if landed >= state_machine.inferno_fireballs:
				_end_inhale()
			else:
				_pull()
		Phase.WINDUP:
			if elapsed >= state_machine.inferno_windup:
				_breathe()
		Phase.BREATH:
			if elapsed >= state_machine.inferno_breath_time:
				_spend()
		Phase.SPENT:
			if not released and elapsed >= state_machine.inferno_spent_time:
				released = true
				body.play_anim(&"release")
			if released and elapsed >= state_machine.inferno_spent_time + BixbyBeastArtLayout.anim_time(&"release"):
				_finish()


func is_pulling() -> bool:
	return phase == Phase.INHALE


# The pull on a player standing at `point` right now, in px/s.
func pull_at(point: Vector2) -> Vector2:
	return _pull_velocity(point, _ramp(elapsed)) if is_pulling() else Vector2.ZERO


func _start(new_phase: Phase) -> void:
	phase = new_phase
	elapsed = 0.0


func _perch() -> void:
	body.perch_on_rope(perch_feet)
	_start(Phase.PERCH)
	body.play_anim(&"perch_land", &"perch")
	rope_sfx_player.play()
	# The cone that will burn smoulders from the moment he has the rope.
	flood = FLOOD_SCENE.instantiate()
	flood.apex = cone_apex
	flood.half_angle = _half_angle()
	flood.player = state_machine.get_player()
	flood.boss = body
	get_tree().current_scene.add_child(flood)
	flood.warn_faint()


func _half_angle() -> float:
	return deg_to_rad(state_machine.inferno_cone_half_angle)


# One fireball up off the screen, out of each head in turn and scattered, not aimed. The volley has a frame
# per head spitting (middle, left, right), put up with the fireball it spits.
func _spit() -> void:
	var head := spits % 3
	body.play_anim(&"volley", &"", head)
	var spread := deg_to_rad(state_machine.inferno_rise_spread_degrees)
	var rise := RISE_SCENE.instantiate()
	rise.launch(_mouth(head), Vector2.UP.rotated(randf_range(-spread, spread)) * state_machine.inferno_rise_speed)
	get_tree().current_scene.add_child(rise)
	rising.append(rise)
	if spits % SPIT_SOUND_EVERY == 0:
		spit_sfx_player.play()
	spits += 1


func _start_inhale() -> void:
	_start(Phase.INHALE)
	body.play_anim(&"inhale")
	inhale_sfx_player.play()
	suction = SUCTION_SCENE.instantiate()
	suction.player = state_machine.get_player()
	var mouths: Array[Vector2] = []
	for head in 3:
		mouths.append(InfernoLayout.perch_mouth_point(InfernoLayout.INHALE_FRAME, head))
	suction.mouths = mouths
	suction.pull_speed = state_machine.inferno_pull_speed
	get_tree().current_scene.add_child(suction)


func _pull() -> void:
	var player = state_machine.get_player()
	if player:
		player.add_drift(pull_at(player.global_position))


# Where the pull converges: his middle mouth as he inhales, on the floor the player can stand on.
func pull_target() -> Vector2:
	var floor_area: Rect2 = state_machine.PLAYER_FLOOR
	return InfernoLayout.perch_mouth_point(InfernoLayout.INHALE_FRAME, 0).clamp(floor_area.position, floor_area.end)


# Toward his inhaling mouth, full strength once the ramp is over, fading out inside the dead zone.
func _pull_velocity(point: Vector2, ramp: float) -> Vector2:
	var to := pull_target() - point
	var distance := to.length()
	if distance <= 0.0:
		return Vector2.ZERO
	var dead_zone: float = state_machine.inferno_pull_dead_zone
	var fade := 1.0 if dead_zone <= 0.0 else minf(distance / dead_zone, 1.0)
	return to / distance * state_machine.inferno_pull_speed * ramp * fade


# How much of the pull is on `at` seconds into the inhale.
func _ramp(at: float) -> float:
	var ramp: float = state_machine.inferno_pull_ramp
	return 1.0 if ramp <= 0.0 else clampf(at / ramp, 0.0, 1.0)


# The next marker of the shower, on the player's feet as it appears, up to inferno_track_scatter off them at
# random so a trail of them doesn't stack on one pixel. It lands inferno_fireball_warning later where they
# were: a player who keeps moving leaves a trail of them landing behind, and one who stops is hit.
func _drop_fireball() -> void:
	var area := InfernoLayout.FIREBALL_AREA
	var spot := area.get_center()
	var player = state_machine.get_player()
	if player:
		spot = _feet(player) + Vector2.from_angle(randf() * TAU) * state_machine.inferno_track_scatter * sqrt(randf())
	var fireball := FIREBALL_SCENE.instantiate()
	fireball.position = spot.clamp(area.position, area.end).round()
	fireball.landed.connect(_on_fireball_landed)
	get_tree().current_scene.add_child(fireball)
	fireball.drop(state_machine.inferno_fireball_warning)
	fireballs.append(fireball)
	dropped += 1


# Where the player stands on the floor: the foot of their hurtbox.
func _feet(player: Node2D) -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)


# The pull ends on the frame the last one lands.
func _on_fireball_landed() -> void:
	landed += 1
	if state_machine.current_state == self and phase == Phase.INHALE and landed >= state_machine.inferno_fireballs:
		_end_inhale()


func _end_inhale() -> void:
	_start(Phase.WINDUP)
	inhale_sfx_player.stop()
	if is_instance_valid(suction):
		suction.stop()
	body.play_anim(&"rear_back")
	gulp_sfx_player.play()
	windup_sfx_player.play()
	if is_instance_valid(flood):
		flood.warn(state_machine.inferno_windup)
	ParryTell.telegraph(body, &"bixby_inferno", state_machine.inferno_windup, _tell_anchor)


# On the mouth the fire comes out of, not over his head: that is half off the top of the screen.
func _tell_anchor() -> Vector2:
	return _mouth(0)


func _breathe() -> void:
	# The fire is out: the warning has done its job.
	ParryTell.clear(body)
	_start(Phase.BREATH)
	body.play_anim(&"perch_breath")
	roar_sfx_player.play()
	breath_sfx_player.play()
	if is_instance_valid(flood):
		flood.ignite(state_machine.inferno_breath_time)
	body.shake_screen(BREATH_SHAKE, BREATH_SHAKE_STEPS, BREATH_SHAKE_STEP_TIME)
	flash.color = Color(BREATH_FLASH_COLOR, BREATH_FLASH_ALPHA)
	flash.create_tween().tween_property(flash, "color:a", 0.0, BREATH_FLASH_TIME)
	get_tree().call_group("arena_crowd", "cheer", BREATH_CHEER)


# The fire dies down on its own (the flood's die-down), leaving its embers.
func _spend() -> void:
	_start(Phase.SPENT)
	released = false
	body.play_anim(&"spent")
	breath_sfx_player.stop()
	_lay_embers()


# Up to inferno_lingering_patches embers inside the burnt cone, apart from each other, away from the player
# and clear of where he is about to land.
func _lay_embers() -> void:
	var player = state_machine.get_player()
	var keep_out := _landing_box().grow(EMBER_LANDING_KEEP_OUT)
	var half := Ember.SIZE / 2.0
	var area := InfernoLayout.INFERNO_AREA.intersection(state_machine.ROPES).grow_individual(-half.x, -half.y, -half.x, -half.y)
	var spots: Array[Vector2] = []
	for i in state_machine.inferno_lingering_patches:
		for attempt in EMBER_TRIES:
			var spot := Vector2(randf_range(area.position.x, area.end.x), randf_range(area.position.y, area.end.y)).round()
			if InfernoLayout.rect_inside_cone(Rect2(spot - half, Ember.SIZE), cone_apex, _half_angle()) and _ember_fits(spot, spots, keep_out, player):
				spots.append(spot)
				break
	for i in spots.size():
		var ember := EMBER_SCENE.instantiate()
		ember.position = spots[i]
		ember.burn_time = state_machine.inferno_lingering_time
		ember.slot = i
		ember.player = player
		get_tree().current_scene.add_child(ember)


func _ember_fits(spot: Vector2, others: Array[Vector2], keep_out: Rect2, player: Node2D) -> bool:
	if keep_out.intersects(Rect2(spot - Ember.SIZE / 2.0, Ember.SIZE)):
		return false
	if player and spot.distance_to(player.global_position) < EMBER_PLAYER_CLEARANCE:
		return false
	var spacing: float = state_machine.inferno_lingering_spacing
	return others.all(func(other: Vector2) -> bool: return other.distance_to(spot) >= spacing)


# His body where Land will put him down and he'll be punched: under his feet as the release drops him.
func _landing_box() -> Rect2:
	var bounds: Rect2 = body.ground_bounds(0.0)
	var point := (perch_feet + Vector2(0, InfernoLayout.release_drop() + body.HOVER_HEIGHT_PX)).clamp(bounds.position, bounds.end)
	var box := BixbyBeastArtLayout.local_rect(BixbyBeastArtLayout.RECOVER_BODY_BOX)
	return Rect2(point + box.position, box.size)


# His own window: the landing keeps the embers that aren't in the player's way, and the recharge is long.
func _finish() -> void:
	state_machine.landing_clearance_override = state_machine.inferno_landing_clearance
	state_machine.recover_time_override = state_machine.inferno_recover_time
	state_machine.attack_finished(self)


# Head `head`'s mouth on the frame he's drawing, in px: 0 middle, 1 left, 2 right.
func _mouth(head: int) -> Vector2:
	var texel := InfernoLayout.perch_mouth(body.sprite.frame, head)
	return body.air.global_position + BixbyBeastArtLayout.local(texel)
