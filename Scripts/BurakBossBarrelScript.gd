extends Node2D

# One of Captain Burak's powder kegs (attack 1, BurakBossBarrels). The node stands on the keg's floor point
# from the moment he throws it, so it depth-sorts with the fighters by where it will land even while it is
# in the air, and it has no collision: the player walks through it. Its marker shows where it will come
# down; landing doesn't hurt. A punch breaks it - hits_to_break of them, cracking through the damage frames
# between - into the burst, whose last frame is left on the floor as debris until the attack ends. Once he
# has loaded, the kegs left are armed: they pulse, and a punch only tonks off them. The keg draws itself
# and reports; BurakBossBarrels decides when it is thrown, lands, lights, arms and goes up
# (BurakBossBlastScript). Every number of how it is drawn is BurakBossArtLayout's KEG block.

signal broken(keg: Node2D)

const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")

# The keg's own wood, light to dark, measured from burak_barrel.png: what a punch knocks off it.
const CHIP_COLORS := [Color("#D79864"), Color("#BE8254"), Color("#7C5438")]

#LANDING
const LAND_SHAKE := 4.0
const LAND_SHAKE_STEPS := 3
const LAND_SHAKE_STEP_TIME := 0.03

#A PUNCH
const PUNCH_FLASH := Color(3, 3, 3)
const PUNCH_FLASH_TIME := 0.08
# Whole-px steps rather than a slide, so the pixel art jumps the way a hit does.
const JOLT_STEPS := 3
const JOLT_PX := 4.0
const JOLT_STEP_TIME := 0.025
# barrel_hit's pitch for the first and the second crack; the third is the break's own sound.
const HIT_PITCHES := [1.0, 1.12]
const PUNCH_HIT_STOP := 0.03
# One texel each, off the struck side and up, falling back under gravity.
const CHIP_COUNT := Vector2i(2, 3)
const CHIP_SIZE := 3.0
const CHIP_SPEED := Vector2(150, 260)
const CHIP_SPREAD_DEGREES := 50.0
const CHIP_LIFT := 140.0
const CHIP_GRAVITY := 900.0
const CHIP_LIFE := 0.28

#THE BREAK
const BREAK_HIT_STOP := 0.05
const BREAK_CHEER := 0.4
const DEBRIS_FADE := 0.3

#ARMED
const ARM_FLASH := Color(3, 3, 3)
const ARM_FLASH_TIME := 0.1
const ARM_PULSE_HZ := 4.0
const ARM_PULSE_PEAK := 1.35

enum Phase { INCOMING, STANDING, ARMED, BROKEN, GONE }

@export var visual: Node2D
@export var body_sprite: Sprite2D
@export var fuse_sprite: Sprite2D
@export var burst_sprite: Sprite2D
@export var hurtbox: Area2D

# Set by BurakBossBarrels before the keg is added: his body, whose play_sfx() plays the keg's sounds, and
# the floor layer the debris is left on, under everyone walking over it.
var boss: Node2D
var floor_layer: Node2D
# Game seconds in which a second report is the same punch again, and the punches that break it;
# BurakBossBarrels sets both from its knobs.
var same_swing_guard := 0.2
var hits_to_break := 1

var phase := Phase.INCOMING
var hits := 0
# Game time, so hit-stop stretches the guard with the swing it guards.
var clock := 0.0
var last_punch_time := -INF
var fuse_lit := false
var fuse_clock := 0.0
var armed_clock := 0.0
var flash_tween: Tween
var jolt_tween: Tween
# On the floor layer, from the throw until it lands.
var marker: Sprite2D


func _ready() -> void:
	for sprite: Sprite2D in [body_sprite, fuse_sprite]:
		sprite.texture = load(Layout.KEG.texture)
		sprite.hframes = Layout.KEG.hframes
		sprite.offset = Layout.KEG.offset
		sprite.scale = Vector2.ONE * Layout.SCALE
	body_sprite.frame = Layout.KEG.damage_frames[0]
	fuse_sprite.frame = Layout.KEG.fuse_frames[0]
	var burst: Dictionary = Layout.fx(&"barrel_break")
	burst_sprite.texture = load(burst.texture)
	burst_sprite.hframes = burst.hframes
	burst_sprite.offset = burst.offset
	burst_sprite.scale = Vector2.ONE * Layout.SCALE
	var box := Layout.keg_rect(Layout.KEG.hurtbox)
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	shape.position = box.get_center()
	(shape.shape as RectangleShape2D).size = box.size
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	# Still in his hand: it shows once it is thrown (carry) or put down (land).
	visual.hide()


func _physics_process(delta: float) -> void:
	clock += delta


func _process(delta: float) -> void:
	if fuse_lit:
		fuse_clock += delta
		var frames: Array = Layout.KEG.fuse_frames
		fuse_sprite.frame = frames[int(fuse_clock / Layout.KEG.fuse_frame_time) % frames.size()]
	if phase == Phase.ARMED:
		armed_clock += delta
		visual.modulate = _armed_modulate(armed_clock)


# The marker and the debris lie on the floor layer, outside this node, so they go with the keg however the
# keg is freed.
func _exit_tree() -> void:
	if is_instance_valid(marker):
		marker.queue_free()
	if is_instance_valid(burst_sprite) and burst_sprite.get_parent() != self:
		burst_sprite.queue_free()


#WHAT BurakBossBarrels CALLS

# As he starts the throw: where it will come down, looping on the floor until it does.
func show_marker() -> void:
	var spec: Dictionary = Layout.fx(&"barrel_marker")
	marker = _floor_sprite(spec)
	var loop := marker.create_tween().set_loops()
	for f in range(1, spec.hframes + 1):
		loop.tween_interval(spec.frame_time)
		loop.tween_callback(marker.set_frame.bind(f % spec.hframes))


# In the air from `from`, `weight` of the way to its spot, on an arc `height` over the chord between them.
# It is drawn f0 the whole way: no tumble was drawn.
func carry(from: Vector2, weight: float, height: float) -> void:
	visual.show()
	var lift := Vector2(0, -4.0 * height * weight * (1.0 - weight))
	visual.position = ((from - global_position) * (1.0 - weight) + lift).round()


# Down on its spot: dust and a thud, and breakable from this step, the player turning to it. Nothing else:
# a keg landing on the player doesn't hurt.
func land() -> void:
	phase = Phase.STANDING
	visual.position = Vector2.ZERO
	visual.show()
	if is_instance_valid(marker):
		marker.queue_free()
	marker = null
	_play_on_floor(Layout.fx(&"barrel_land"))
	boss.play_sfx(&"barrel_land")
	ScreenView.shake(get_tree(), LAND_SHAKE, LAND_SHAKE_STEPS, LAND_SHAKE_STEP_TIME)
	hurtbox.add_to_group(PlayerScript.THREAT_GROUP)


# From the load's start the fuse burns over whichever damage frame shows.
func light_fuse() -> void:
	fuse_lit = true
	fuse_clock = 0.0
	fuse_sprite.show()


# The lock: it can't be broken any more, only shot. It stops turning the player and flashes, then pulses.
func arm() -> void:
	phase = Phase.ARMED
	armed_clock = 0.0
	hurtbox.remove_from_group(PlayerScript.THREAT_GROUP)
	_stop_punch_feedback()
	visual.modulate = ARM_FLASH


func is_breakable() -> bool:
	return phase == Phase.STANDING


func is_armed() -> bool:
	return phase == Phase.ARMED


# Its blast's first frame covers it (BurakBossBlastScript), so it goes on that frame.
func blow() -> void:
	phase = Phase.GONE
	hurtbox.remove_from_group(PlayerScript.THREAT_GROUP)
	hide()
	queue_free()


# The attack is over: whatever is left of it fades out, then it goes.
func fade_away() -> void:
	if phase == Phase.GONE:
		return
	phase = Phase.GONE
	hurtbox.remove_from_group(PlayerScript.THREAT_GROUP)
	_stop_punch_feedback()
	var fade := create_tween().set_parallel()
	fade.tween_property(visual, "modulate:a", 0.0, DEBRIS_FADE)
	fade.tween_property(burst_sprite, "modulate:a", 0.0, DEBRIS_FADE)
	fade.chain().tween_callback(queue_free)


#PUNCHES

# The hurtbox has to stay on collision layer 0 and not monitorable, FunkoFigure's rule: one-way, a punch is
# reported on the physics step after its press. Not a boss either, so the punch never reaches the combo.
func _on_hurtbox_entered(area: Area2D) -> void:
	if not area.is_in_group("player attack"):
		return
	if phase != Phase.STANDING and phase != Phase.ARMED:
		return
	if clock - last_punch_time < same_swing_guard:
		return
	last_punch_time = clock
	if phase == Phase.ARMED:
		boss.play_sfx(&"barrel_tonk")
		return
	hits += 1
	if hits >= hits_to_break:
		_break()
		return
	var damage_frames: Array = Layout.KEG.damage_frames
	body_sprite.frame = damage_frames[mini(hits, damage_frames.size() - 1)]
	boss.play_sfx(&"barrel_hit", HIT_PITCHES[mini(hits - 1, HIT_PITCHES.size() - 1)])
	HitStop.freeze(get_tree(), PUNCH_HIT_STOP)
	_flash_and_jolt()
	_throw_chips(area.global_position)


func _flash_and_jolt() -> void:
	_stop_punch_feedback()
	visual.modulate = PUNCH_FLASH
	flash_tween = create_tween()
	flash_tween.tween_property(visual, "modulate", Color.WHITE, PUNCH_FLASH_TIME)
	jolt_tween = create_tween()
	for i in JOLT_STEPS:
		var offset := Vector2(randf_range(-JOLT_PX, JOLT_PX), randf_range(-JOLT_PX, JOLT_PX)).round()
		jolt_tween.tween_callback(visual.set_position.bind(offset))
		jolt_tween.tween_interval(JOLT_STEP_TIME)
	jolt_tween.tween_callback(visual.set_position.bind(Vector2.ZERO))


func _stop_punch_feedback() -> void:
	for tween in [flash_tween, jolt_tween]:
		if tween:
			tween.kill()
	visual.modulate = Color.WHITE
	visual.position = Vector2.ZERO


# From the edge of the drawn keg facing the puncher, back out that way.
func _throw_chips(puncher: Vector2) -> void:
	var box := Layout.keg_rect(Layout.KEG.hurtbox)
	var centre := box.get_center()
	var toward := (to_local(puncher) - centre).normalized()
	var edge := centre + toward * minf(box.size.x, box.size.y) / 2.0
	var square := PackedVector2Array([Vector2.ZERO, Vector2(CHIP_SIZE, 0), Vector2(CHIP_SIZE, CHIP_SIZE),
		Vector2(0, CHIP_SIZE)])
	for i in randi_range(CHIP_COUNT.x, CHIP_COUNT.y):
		var chip := Polygon2D.new()
		chip.polygon = square
		chip.color = CHIP_COLORS.pick_random()
		chip.position = edge.round()
		add_child(chip)
		var heading := toward.rotated(deg_to_rad(randf_range(-CHIP_SPREAD_DEGREES, CHIP_SPREAD_DEGREES)))
		var velocity := heading * randf_range(CHIP_SPEED.x, CHIP_SPEED.y) + Vector2(0, -CHIP_LIFT)
		var start := chip.position
		var fly := chip.create_tween()
		fly.tween_method(func(t: float) -> void:
			chip.position = (start + velocity * t + Vector2(0, CHIP_GRAVITY * t * t / 2.0)).round(),
			0.0, CHIP_LIFE, CHIP_LIFE)
		fly.parallel().tween_property(chip, "modulate:a", 0.0, CHIP_LIFE / 2.0).set_delay(CHIP_LIFE / 2.0)
		fly.tween_callback(chip.queue_free)


#THE BREAK

func _break() -> void:
	phase = Phase.BROKEN
	hurtbox.remove_from_group(PlayerScript.THREAT_GROUP)
	fuse_lit = false
	_stop_punch_feedback()
	visual.hide()
	boss.play_sfx(&"barrel_break")
	HitStop.freeze(get_tree(), BREAK_HIT_STOP)
	get_tree().call_group("arena_crowd", "cheer", BREAK_CHEER)
	_play_burst()
	broken.emit(self)


func _play_burst() -> void:
	var spec: Dictionary = Layout.fx(&"barrel_break")
	burst_sprite.frame = 0
	burst_sprite.show()
	var play := burst_sprite.create_tween()
	for f in range(1, spec.debris_frame):
		play.tween_interval(spec.frame_time)
		play.tween_callback(burst_sprite.set_frame.bind(f))
	play.tween_interval(spec.frame_time)
	play.tween_callback(_lay_debris)


# Held until the attack ends. The burst over it sorted with the fighters; the pieces lying on the floor go
# under anyone standing on them.
func _lay_debris() -> void:
	burst_sprite.frame = Layout.fx(&"barrel_break").debris_frame
	burst_sprite.reparent(floor_layer)


#ON THE FLOOR

# One of the KEG block's sheets on the floor layer, on the keg's floor point, under anyone standing there.
func _floor_sprite(spec: Dictionary) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.offset = spec.offset
	sprite.scale = Vector2.ONE * Layout.SCALE
	floor_layer.add_child(sprite)
	sprite.global_position = global_position
	return sprite


func _play_on_floor(spec: Dictionary) -> void:
	var sprite := _floor_sprite(spec)
	var play := sprite.create_tween()
	for f in range(1, spec.hframes):
		play.tween_interval(spec.frame_time)
		play.tween_callback(sprite.set_frame.bind(f))
	play.tween_interval(spec.frame_time)
	play.tween_callback(sprite.queue_free)


#ARMED

func _armed_modulate(t: float) -> Color:
	if t < ARM_FLASH_TIME:
		return ARM_FLASH.lerp(Color.WHITE, t / ARM_FLASH_TIME)
	var wave := 0.5 - 0.5 * cos(TAU * ARM_PULSE_HZ * (t - ARM_FLASH_TIME))
	var level := lerpf(1.0, ARM_PULSE_PEAK, wave)
	return Color(level, level, level)
