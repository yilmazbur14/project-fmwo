extends CharacterBody2D

# One of Jordan's summoned vinyl figures. It pops in, chases the player and blows up when its fuse
# runs out. A punch knocks it tumbling away, and from then on its blast can hurt Jordan as well.

const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

# The figures still in play, for spreading a swarm out. A figure leaves it once it goes off.
const FIGURE_GROUP := "funko_figure"

# Art swap point: the designer's sheets in Assets/Characters/Jordan/Funkos/, all at ART_SCALE. A figure
# sheet is one row of SHEET_FRAMES frames facing right: chase 0-3, fuse 4-5 (flash and shake drawn in),
# punched 6-7. Each spawned figure picks a sheet at random. Frame sizes follow from the textures and the
# frame counts; the frame times are the designer's.
const FIGURE_SHEETS := [
	preload("res://Assets/Characters/Jordan/Funkos/funko_plumber.png"),
	preload("res://Assets/Characters/Jordan/Funkos/funko_hedgehog.png"),
	preload("res://Assets/Characters/Jordan/Funkos/funko_mascot.png"),
	preload("res://Assets/Characters/Jordan/Funkos/funko_gamer.png"),
]
const SHEET_FRAMES := 8
const CHASE_FRAMES := [0, 1, 2, 3]
const FUSE_FRAMES := [4, 5]
const PUNCHED_FRAMES := [6, 7]
const CHASE_FRAME_TIME := 0.07
const FUSE_FRAME_TIME := 0.08
const PUNCHED_FRAME_TIME := 0.06
const POP_TEXTURE := preload("res://Assets/Characters/Jordan/Funkos/funko_spawn_pop.png")
const POP_FRAME_TIMES := [0.05, 0.07, 0.08, 0.1]
const EXPLOSION_TEXTURE := preload("res://Assets/Characters/Jordan/Funkos/funko_explosion.png")
const EXPLOSION_FRAME_TIMES := [0.05, 0.06, 0.08, 0.09, 0.1, 0.12]
const ART_SCALE := 3.0
# Texels each sheet is shifted by so its body centre sits on the node: (12, 14) on a figure frame, which the
# tumble spins around, and (16, 17) on a pop frame.
const SPRITE_OFFSET := Vector2(0, -2)
const POP_OFFSET := Vector2(0, -1)
# The drawn figure in screen px, centred on the node with its feet on the bottom edge: the ropes stop a body
# this size, and it's what touches Jordan.
const BODY_SIZE := Vector2(51, 39)
# What a punch has to reach into, and what the player turns to face. Taller than the body, so a figure right
# on top of the player is always in reach of the punch the player turns to it.
const HURTBOX_SIZE := Vector2(54, 54)
# The sheets face right. Slower than this sideways, a figure keeps facing the way it was.
const FLIP_MIN_SPEED := 30.0

#SPAWN
# Seconds from popping in to giving chase.
const SPAWN_GRACE := 0.35
const POP_GROW_TIME := 0.2

#CHASE
# Top speed as a share of the player's walk speed.
const CHASE_SPEED_RATIO := 0.9
# px/s², spent on both speeding up and turning.
const ACCELERATION := 2400.0
# Inside this many px of the player a figure eases off, so it settles on them instead of overshooting.
const ARRIVE_RADIUS := 80.0
# Figures nearer each other than this push apart, harder the nearer they are.
const SEPARATION_RADIUS := 90.0
# How hard they push apart, relative to the pull toward the player.
const SEPARATION_WEIGHT := 1.5

#FUSE
# Seconds from popping in to going off, give or take FUSE_VARIANCE for each figure.
const FUSE_TIME := 2.8
const FUSE_VARIANCE := 0.4
# For the fuse's last seconds the figure plays its fuse frames and slows to FUSE_SPEED_RATIO of its top speed.
const FUSE_WARNING_TIME := 0.8
const FUSE_SPEED_RATIO := 0.8

#EXPLOSION
# The blast hurts the player if they stand within this many px of the figure, and Jordan if any of his
# hurtbox is that close.
const EXPLOSION_RADIUS := 90.0
# The blast hurts while these explosion frames (first, last) show, as the smoke ring spreads out to
# EXPLOSION_RADIUS, so a dash into it still gets hit.
const EXPLOSION_HIT_FRAMES := Vector2i(1, 3)
const EXPLOSION_BOSS_DAMAGE := 1
const SHAKE_STEPS := 4
const SHAKE_STEP_TIME := 0.03
const SHAKE_STRENGTH := 5.0

#PUNCHED
# How far a punch sends a figure if nothing stops it, over the tumble.
const KNOCKBACK_DISTANCE := 480.0
const TUMBLE_TIME := 0.6
const TUMBLE_TURNS := 1.0
const PUNCH_FLASH := Color(3, 3, 3)
const PUNCH_FLASH_TIME := 0.08
# A figure flies away from the player, but no more than this many degrees off the way the punch
# faces, so one standing on top of the player isn't sent out behind them.
const KNOCKBACK_FACING_SPREAD := 60.0
# A knockback aimed within this many degrees of Jordan is bent straight at him.
const AIM_ASSIST_DEGREES := 25.0
# A tumbling figure that reaches Jordan's hurtbox goes off right there.
const DETONATE_ON_BOSS_CONTACT := true

const FACING_DIRECTIONS := {
	PlayerScript.Facing.DOWN: Vector2.DOWN,
	PlayerScript.Facing.UP: Vector2.UP,
	PlayerScript.Facing.LEFT: Vector2.LEFT,
	PlayerScript.Facing.RIGHT: Vector2.RIGHT,
}

# The ropes' collision edges.
const ROPES := Rect2(105, 105, 1710, 870)

enum Phase { SPAWNING, CHASING, TUMBLING, EXPLODING }

@export var visual: Node2D
@export var figure_sprite: Sprite2D
@export var pop_sprite: Sprite2D
@export var explosion_sprite: Sprite2D
@export var body_shape: CollisionShape2D
@export var hurtbox: Area2D
@export var punch_sfx: AudioStreamPlayer
@export var explode_sfx: AudioStreamPlayer

# Set by Jordan before the figure is added.
var player: CharacterBody2D
var jordan: CharacterBody2D

var phase := Phase.SPAWNING
var phase_time := 0.0
var age := 0.0
var fuse := FUSE_TIME
# Set by the first punch and kept until the figure goes off: only a punched figure's blast hurts Jordan.
var redirected := false
var knockback := Vector2.ZERO
var blast_hit_jordan := false


# The nearest spot to `point` where a figure's body fits inside the ropes.
static func inside_ropes(point: Vector2) -> Vector2:
	return point.clamp(ROPES.position + BODY_SIZE / 2.0, ROPES.end - BODY_SIZE / 2.0)


func _ready() -> void:
	add_to_group(FIGURE_GROUP)
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	fuse = FUSE_TIME + randf_range(-FUSE_VARIANCE, FUSE_VARIANCE)

	figure_sprite.texture = FIGURE_SHEETS.pick_random()
	figure_sprite.hframes = SHEET_FRAMES
	figure_sprite.offset = SPRITE_OFFSET
	pop_sprite.texture = POP_TEXTURE
	pop_sprite.hframes = POP_FRAME_TIMES.size()
	pop_sprite.offset = POP_OFFSET
	pop_sprite.scale = Vector2(ART_SCALE, ART_SCALE)
	explosion_sprite.texture = EXPLOSION_TEXTURE
	explosion_sprite.hframes = EXPLOSION_FRAME_TIMES.size()
	explosion_sprite.scale = Vector2(ART_SCALE, ART_SCALE)

	(body_shape.shape as RectangleShape2D).size = BODY_SIZE
	(hurtbox.get_node("CollisionShape2D").shape as RectangleShape2D).size = HURTBOX_SIZE
	# Visual sits at the figure's feet, where it depth-sorts against the player, and holds the art up at the
	# figure's centre.
	visual.position = Vector2(0, BODY_SIZE.y / 2.0)
	figure_sprite.position = -visual.position
	pop_sprite.position = -visual.position

	figure_sprite.scale = Vector2.ZERO
	create_tween().tween_property(figure_sprite, "scale", Vector2(ART_SCALE, ART_SCALE), POP_GROW_TIME).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_animate()


func _physics_process(delta: float) -> void:
	age += delta
	phase_time += delta
	match phase:
		Phase.SPAWNING:
			if phase_time >= SPAWN_GRACE:
				_set_phase(Phase.CHASING)
				# Only a figure coming for the player turns them to face it: not while it pops in, and never
				# again once punched or going off. The fuse warning doesn't count, since a flashing figure is
				# the one most worth punching away.
				hurtbox.add_to_group(PlayerScript.THREAT_GROUP)
		Phase.CHASING:
			_chase(delta)
		Phase.TUMBLING:
			_tumble()
		Phase.EXPLODING:
			_explode_step()
			return

	if phase == Phase.EXPLODING:
		return
	if age >= fuse:
		_detonate()
		return
	_animate()


func _set_phase(new_phase: Phase) -> void:
	phase = new_phase
	phase_time = 0.0


func _body_rect() -> Rect2:
	return Rect2(global_position - BODY_SIZE / 2.0, BODY_SIZE)


func _fuse_warning() -> bool:
	return age >= fuse - FUSE_WARNING_TIME


func _chase(delta: float) -> void:
	var top_speed := PlayerScript.SPEED * CHASE_SPEED_RATIO
	if _fuse_warning():
		top_speed *= FUSE_SPEED_RATIO
	var pull := (player.global_position - global_position).limit_length(ARRIVE_RADIUS) / ARRIVE_RADIUS
	var desired := ((pull + _separation() * SEPARATION_WEIGHT) * top_speed).limit_length(top_speed)
	velocity = velocity.move_toward(desired, ACCELERATION * delta)
	move_and_slide()


func _separation() -> Vector2:
	var push := Vector2.ZERO
	for other: Node2D in get_tree().get_nodes_in_group(FIGURE_GROUP):
		if other == self:
			continue
		var away := global_position - other.global_position
		var distance := away.length()
		if distance >= SEPARATION_RADIUS:
			continue
		# Figures on exactly the same spot would otherwise steer identically and never come apart.
		if distance == 0.0:
			away = Vector2.from_angle(randf() * TAU)
			distance = 1.0
		push += away / distance * (1.0 - distance / SEPARATION_RADIUS)
	return push


# The hurtbox has to stay on collision layer 0 and not monitorable. A punch hitbox and an area that
# can each see the other, like a boss hurtbox, only report a punch on something already in front of the
# player once the hitbox switches off, a whole swing late; one-way, the report comes on the next frame.
# Not a boss, so the punch never reaches the combo.
func _on_hurtbox_entered(area: Area2D) -> void:
	if phase == Phase.TUMBLING or phase == Phase.EXPLODING or not area.is_in_group("player attack"):
		return
	hurtbox.remove_from_group(PlayerScript.THREAT_GROUP)
	redirected = true
	knockback = _knockback_direction(area.get_parent()) * 2.0 * KNOCKBACK_DISTANCE / TUMBLE_TIME
	_set_phase(Phase.TUMBLING)
	punch_sfx.play()


func _knockback_direction(puncher: Node2D) -> Vector2:
	var facing: Vector2 = FACING_DIRECTIONS[puncher.facing]
	var spread := deg_to_rad(KNOCKBACK_FACING_SPREAD)
	var away := global_position - puncher.global_position
	return _aim_assist(facing.rotated(clampf(facing.angle_to(away), -spread, spread)))


func _aim_assist(direction: Vector2) -> Vector2:
	var box: Rect2 = jordan.hurtbox_rect()
	var to_jordan := box.get_center() - global_position
	if absf(direction.angle_to(to_jordan)) <= deg_to_rad(AIM_ASSIST_DEGREES):
		return to_jordan.normalized()
	return direction


# Slows evenly to a stop over the tumble, so it covers KNOCKBACK_DISTANCE unless the ropes stop it first.
func _tumble() -> void:
	var left := 1.0 - phase_time / TUMBLE_TIME
	if left <= 0.0:
		velocity = Vector2.ZERO
		_set_phase(Phase.CHASING)
		return
	velocity = knockback * left
	move_and_slide()
	var box: Rect2 = jordan.hurtbox_rect()
	if DETONATE_ON_BOSS_CONTACT and _body_rect().intersects(box):
		_detonate()
	elif get_slide_collision_count() > 0:
		velocity = Vector2.ZERO
		_set_phase(Phase.CHASING)


func _detonate() -> void:
	_set_phase(Phase.EXPLODING)
	remove_from_group(FIGURE_GROUP)
	hurtbox.remove_from_group(PlayerScript.THREAT_GROUP)
	velocity = Vector2.ZERO
	visual.hide()
	explosion_sprite.frame = 0
	explosion_sprite.show()
	explode_sfx.play()
	_shake_screen()


func _explode_step() -> void:
	var frame := _frame_at(EXPLOSION_FRAME_TIMES, phase_time)
	if frame < 0:
		queue_free()
		return
	explosion_sprite.frame = frame
	if frame >= EXPLOSION_HIT_FRAMES.x and frame <= EXPLOSION_HIT_FRAMES.y:
		_blast()


# The frame of a one-shot animation with these frame times that shows `time` in, or -1 once it's over.
static func _frame_at(frame_times: Array, time: float) -> int:
	var end := 0.0
	for i in frame_times.size():
		end += frame_times[i]
		if time < end:
			return i
	return -1


func _blast() -> void:
	if global_position.distance_to(player.global_position) <= EXPLOSION_RADIUS:
		player.take_damage()
	if not redirected or blast_hit_jordan:
		return
	var box: Rect2 = jordan.hurtbox_rect()
	if global_position.distance_to(global_position.clamp(box.position, box.end)) <= EXPLOSION_RADIUS:
		blast_hit_jordan = true
		jordan.take_explosion_hit(EXPLOSION_BOSS_DAMAGE)


func _animate() -> void:
	var tumbling := phase == Phase.TUMBLING
	var frames: Array = CHASE_FRAMES
	var frame_time := CHASE_FRAME_TIME
	if tumbling:
		frames = PUNCHED_FRAMES
		frame_time = PUNCHED_FRAME_TIME
	elif _fuse_warning():
		frames = FUSE_FRAMES
		frame_time = FUSE_FRAME_TIME
	figure_sprite.frame = frames[int(age / frame_time) % frames.size()]
	if absf(velocity.x) >= FLIP_MIN_SPEED:
		figure_sprite.flip_h = velocity.x < 0.0

	var pop_frame := _frame_at(POP_FRAME_TIMES, age)
	pop_sprite.visible = pop_frame >= 0
	if pop_sprite.visible:
		pop_sprite.frame = pop_frame

	figure_sprite.modulate = PUNCH_FLASH if tumbling and phase_time < PUNCH_FLASH_TIME else Color.WHITE
	figure_sprite.rotation = 0.0
	if tumbling:
		# Eases out with the knockback, which slows evenly.
		var unspun := 1.0 - minf(phase_time / TUMBLE_TIME, 1.0)
		var spin_direction := 1.0 if knockback.x >= 0.0 else -1.0
		figure_sprite.rotation = spin_direction * TAU * TUMBLE_TURNS * (1.0 - unspun * unspun)


# Offsets the canvas instead of moving nodes, so physics bodies and the UI layers stay put. Through
# ScreenView, so it adds to the finisher's zoom instead of snapping the view back to identity, and a new
# blast's shake takes over from the last.
func _shake_screen() -> void:
	ScreenView.shake(get_tree(), SHAKE_STRENGTH, SHAKE_STEPS, SHAKE_STEP_TIME)
