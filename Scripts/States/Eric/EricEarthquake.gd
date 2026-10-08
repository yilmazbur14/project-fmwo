extends State

# Eric raises his sword and slams it down, sending out eight ground waves, a few slams an attack. In
# the reworked fight (EricPacing V2) a standard red tell comes up exactly slam_tell_time before the
# waves exist, and some slams hold the frame before impact, so the player reads the tell, not the
# raise.

@export var earthquake_animation : String = "earthquake"
@export var recover_animation : String = "recover"
@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var eric_state_machine : Node
var EarthquakeAreas = preload("res://Scenes/Bosses/EarthquakeAreasScene.tscn")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

# Over his head on the raise: above the sword he holds across it on frames 3-5, under the arc of
# frame 6.
const TELL_HEAD_PIXEL := Vector2(136, 100)
# Summed frame deltas land a hair short of a hold's length, which would run it a frame long.
const STEP_TOLERANCE := 0.0001
# Further than any wave travels before it despawns, so a lane drawn this long is all of its path.
const LANE_LENGTH := 4000.0

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

var slams_left := 0
var projectile_speed_now := 0.0
var slam_speed := 1.0
# Slams alternate patterns, carrying on from one attack to the next.
var tilted_next := false
# V2: the fight's slam attacks so far, since the first never holds a slam; the slams_left count of this
# attack's delayed slam, or -1, and how long it holds.
var attacks_started := 0
var delayed_slam := -1
var hold_time := 0.0
var hold_left := 0.0
var held := false
var told := false
# Where `earthquake` shows the held frame and calls enable_hitbox, in its own time.
var hold_position := 0.0
var hit_position := 0.0


func Enter() -> void:
	var rage: float = eric_state_machine.rage
	slams_left = roundi(EricPacing.raged("slams", rage))
	projectile_speed_now = EricPacing.raged("wave_speed", rage)
	slam_speed = EricPacing.raged("slam_animation_speed", rage)
	animation_player.speed_scale = slam_speed
	if EricPacing.is_v2():
		_read_slam_keys()
		_pick_delayed_slam()
	attacks_started += 1
	_start_slam()


func Exit() -> void:
	animation_player.speed_scale = 1.0  # Reset back to normal for other animations
	ParryTell.clear(character_body)
	hold_left = 0.0


# In the idle step, after the AnimationPlayer has advanced this frame, so the frames it has left to
# enable_hitbox are counted exactly. The hold stops the animation at speed 0 rather than pausing it,
# since a resumed AnimationPlayer sits out a frame before it moves again.
func Update(delta: float) -> void:
	if not EricPacing.is_v2() or animation_player.assigned_animation != earthquake_animation:
		return
	if hold_left > 0.0:
		hold_left -= delta
		if hold_left <= STEP_TOLERANCE:
			hold_left = 0.0
			animation_player.speed_scale = slam_speed
	elif _delays_this_slam() and not held and animation_player.current_animation_position >= hold_position:
		held = true
		hold_left = hold_time
		animation_player.speed_scale = 0.0
	_update_tell(delta)


func _start_slam() -> void:
	held = false
	told = false
	hold_left = 0.0
	animation_player.play(earthquake_animation)
	if EricPacing.is_v2():
		# At his enraged speed the raise is no longer than the tell, so it goes up with the raise.
		_update_tell(get_process_delta_time())


# Up now if waiting for the next step would leave less than the whole tell before impact.
func _update_tell(delta: float) -> void:
	if told:
		return
	var left := _time_to_impact()
	if left - delta < EricPacing.value("slam_tell_time"):
		told = true
		ParryTell.telegraph(character_body, EricPacing.value("wave_id"), left, _tell_anchor)


# Game seconds until this slam's waves exist: the rest of the raise, and any hold still to come.
func _time_to_impact() -> float:
	var left := maxf(hit_position - animation_player.current_animation_position, 0.0) / slam_speed
	if _delays_this_slam():
		left += hold_left if held else hold_time
	return left


func _delays_this_slam() -> bool:
	return delayed_slam == slams_left


# At most one slam an attack holds, and none in the fight's first slam attack. The attack picks which
# at a chance scaled by its slam count, so that is the share of slams that hold wherever it can be.
func _pick_delayed_slam() -> void:
	delayed_slam = -1
	if attacks_started == 0:
		return
	if randf() < minf(EricPacing.value("delayed_slam_chance") * slams_left, 1.0):
		delayed_slam = randi_range(1, slams_left)
		hold_time = EricPacing.value("delayed_slam_holds").pick_random()


# Read off the animation, so retiming it keeps the hold and the tell where they belong.
func _read_slam_keys() -> void:
	var animation := animation_player.get_animation(earthquake_animation)
	for track in animation.get_track_count():
		for key in animation.track_get_key_count(track):
			if animation.track_get_type(track) == Animation.TYPE_METHOD:
				hit_position = animation.track_get_key_time(track, key)
			elif animation.track_get_path(track) == ^"Sprite2D:frame" and animation.track_get_key_value(track, key) == EricArtLayout.SLAM_HOLD_FRAME:
				hold_position = animation.track_get_key_time(track, key)


func _tell_anchor() -> Vector2:
	return character_body.to_global(EricArtLayout.frame_local(TELL_HEAD_PIXEL + Vector2(0.5, 0.5), character_body.sprite.flip_h))


# Called by the earthquake animation on frame 7.
func enable_hitbox():
	ParryTell.clear(character_body)
	var spawned_earthquake_areas = EarthquakeAreas.instantiate()
	spawned_earthquake_areas.tilted = tilted_next
	spawned_earthquake_areas.attack_id = EricPacing.value("wave_id")
	tilted_next = not tilted_next
	# The art is drawn at Eric's scale, one texel per hitbox unit.
	spawned_earthquake_areas.scale = character_body.scale
	spawned_earthquake_areas.move_speed = projectile_speed_now / character_body.scale.x
	eric_state_machine.add_hazard(spawned_earthquake_areas, character_body.frame_point(EricArtLayout.SLAM_PIXEL))
	spawned_earthquake_areas.enable_earthquake_areas()
	_strike_inside(spawned_earthquake_areas)

	var sfx = character_body.get_node_or_null("EarthquakeSfxPlayer")
	if sfx:
		if not sfx.stream:
			sfx.stream = load("res://Assets/Audio/SFX/earthquake_slam.ogg")
		sfx.play()


# The waves set off spawn_radius out from the blade and take a physics step before anyone is checked
# against them, so the ground right round its tip lies between all eight lanes and no wave ever crosses
# it: a player standing there was safe from every slam (playtest 2026-10-04). The blade coming down is the
# hit there instead, once, as the waves go out, and answered as they are. Only where no lane reaches, so
# nobody is struck or credited twice by one slam.
func _strike_inside(waves: Node2D) -> void:
	if not is_instance_valid(player):
		return
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var at: Vector2 = waves.global_position
	if at.clamp(box.position, box.end).distance_to(at) > _first_reach(waves):
		return
	var toward: Vector2 = box.get_center() - at
	var nearest: int = waves.collision_map.keys()[0]
	for numpad in waves.collision_map:
		if _lane_reaches(waves, numpad, box):
			return
		if absf(waves.directions[numpad].angle_to(toward)) < absf(waves.directions[nearest].angle_to(toward)):
			nearest = numpad
	# The source is the wave setting off toward them: a new one every slam, so a parry of one slam can't
	# cover the next, and it is the art a parry flashes, as on any wave's.
	player.receive_hit(HitInfo.make(EricPacing.value("wave_id"), waves.collision_map[nearest], at, character_body))


# How far from the blade a wave's middle is the first time it can meet anyone, in px.
func _first_reach(waves: Node2D) -> float:
	return (waves.spawn_radius + waves.move_speed / Engine.physics_ticks_per_second) * absf(waves.global_scale.x)


# Whether wave `numpad`'s path, from its first check to the end of the ring, crosses `box`.
func _lane_reaches(waves: Node2D, numpad: int, box: Rect2) -> bool:
	var area: Area2D = waves.collision_map[numpad]
	var size: Vector2 = (area.get_node("CollisionShape2D").shape as RectangleShape2D).size * absf(waves.global_scale.x)
	var direction: Vector2 = waves.directions[numpad]
	var across: Vector2 = direction.orthogonal() * size.x / 2.0
	var near: Vector2 = waves.global_position + direction * (_first_reach(waves) - size.y / 2.0)
	var far: Vector2 = near + direction * LANE_LENGTH
	var lane := PackedVector2Array([near - across, near + across, far + across, far - across])
	var body := PackedVector2Array([box.position, Vector2(box.end.x, box.position.y), box.end, Vector2(box.position.x, box.end.y)])
	return not Geometry2D.intersect_polygons(lane, body).is_empty()

func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if eric_state_machine.current_state != self:
		return
	if anim_name == earthquake_animation:
		animation_player.play(recover_animation)
	elif anim_name == recover_animation:
		slams_left -= 1
		if slams_left > 0:
			_start_slam()
		else:
			eric_state_machine.attack_finished()
