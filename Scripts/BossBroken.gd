extends State

# A boss with his Break gauge full (BossBreakGauge): MasonBroken made general. Whatever he was doing has
# stopped (his state machine's enter_broken). The fight stops dead for a beat, he goes down open to
# punches, and the player is driven in beside him so there is no walk-up. A boss standing too high for a
# juggle to be seen slides down to his juggle floor (BossJuggled.floor_y) over the same beat, and the
# player is driven in beside the spot he slides to. A 3-hit combo landed here starts the finisher, and
# this window is the only one that pays out the three-bar mash and the juggle (can_be_juggled). When his
# time is up, _time_up() says what he does next; when the finisher's uppercut ends it instead, his state
# machine's end_break does. A juggle takes him out of here and does not hand him back.
# A boss subclasses it (extends "res://Scripts/BossBroken.gd") and overrides the REQUIRED hooks below;
# the rest are optional. His state machine builds it in code beside his BossJuggled, and sets body,
# hurtbox and state_machine. A subclass that overrides _ready() calls super.

const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")

# The Break frame, in real seconds, so it plays out through its own hit-stop: the fight stops dead, the
# HUD flashes white, the view shakes and punches in, and the crowd roars.
const BREAK_HIT_STOP := 0.30
const FLASH := Color(1, 1, 1, 0.55)
const FLASH_TIME := 0.12
const SHAKE := 22.0
const SHAKE_STEPS := 8
const SHAKE_STEP_TIME := 0.03
const ZOOM := 1.3
const ZOOM_IN_TIME := 0.05
const ZOOM_HOLD := 0.10
const ZOOM_OUT_TIME := 0.3
const CHEER := 3.5
# Its level is baked in.
const BREAK_STING := "res://Assets/Audio/SFX/break_sting.wav"
# The drive that puts the player beside him, in game time. The actions stay locked for it.
const DRIVE_TIME := 0.18
# The player's feet on his ground line: their body's centre is this far above their hurtbox's bottom.
const PLAYER_FEET_OFFSET := 42.0
# And this much below it, so the y-sort draws them in front of him, not behind.
const PLAYER_IN_FRONT := 3.0
# Where the player's centre can be put inside the ropes: the floor their body fits on, kept 3 px
# further in again so a drive never parks them flush against a rope.
const PLAYER_AREA := Rect2(126, 148.5, 1668, 783)
# The finisher's effects layer: the stars draw over both fighters.
const STARS_Z_INDEX := 2

@export var body : CharacterBody2D
@export var hurtbox : Area2D
@export var state_machine : Node

var time_left := 0.0
var driven: Node2D
var drive_to := Vector2.ZERO
var stars: Sprite2D
var drive_left := 0.0
var drive_from := Vector2.ZERO
var slide_left := 0.0
var slide_time := 0.0
var slide_from := Vector2.ZERO
var slide_to := Vector2.ZERO
var stars_clock := 0.0
var stars_shown := true
var sting: AudioStreamPlayer


func _ready() -> void:
	sting = AudioStreamPlayer.new()
	sting.stream = load(BREAK_STING)
	add_child(sting)


func Enter() -> void:
	time_left = _broken_time()
	stars_shown = true
	# The Break window is worth exactly one 3-punch combo, wherever the hit cap stood when it landed.
	body.hits_this_window = 0
	body.daze_used = false
	_pose_in()
	# The player is driven in beside him, and may be standing in him already.
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	_break_frame()
	_start_slide()
	_drive_player_in()
	_spawn_stars()


func Exit() -> void:
	if slide_left > 0.0:
		_end_slide()
	_end_drive()
	_clear_stars()
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	_pose_out()


# After his body has stepped its animation, so the stars sit on the frame that's drawn.
func Update(delta: float) -> void:
	_step_stars(delta)


func Physics_Update(delta: float) -> void:
	if slide_left > 0.0:
		slide_left -= delta
		var w := clampf(1.0 - slide_left / slide_time, 0.0, 1.0)
		_set_feet(slide_from.lerp(slide_to, w).round(), w)
	if drive_left > 0.0 and is_instance_valid(driven):
		drive_left -= delta
		var t := clampf(1.0 - drive_left / DRIVE_TIME, 0.0, 1.0)
		driven.global_position = drive_from.lerp(drive_to, t * t).round()
		if drive_left <= 0.0:
			_end_drive()
	time_left -= delta
	if time_left <= 0.0:
		_time_up()


# The finisher's daze draws its own stars over the same head.
func show_stars(shown: bool) -> void:
	stars_shown = shown
	_step_stars(0.0)


# Just above his head, where the stars circle.
func head_point() -> Vector2:
	return _head_point()


# A punch landing on him while he's down.
func flinch() -> void:
	_on_flinch()


# REQUIRED: his Broken pose, and anything of his own a window needs open.
func _pose_in() -> void:
	pass


# REQUIRED: where his feet are, in the world.
func _feet() -> Vector2:
	return Vector2.ZERO


# REQUIRED: puts his feet on `point`. `weight` runs 0 to 1 across the slide, for a boss whose height
# comes down with it.
func _set_feet(_point: Vector2, _weight: float) -> void:
	pass


# REQUIRED: where his feet may be put.
func _feet_bounds() -> Rect2:
	return Rect2()


# REQUIRED: just above his head, about 34 px over it.
func _head_point() -> Vector2:
	return Vector2.ZERO


# REQUIRED: his time is up and nobody finished him: whatever he does next.
func _time_up() -> void:
	pass


# Undoes whatever _pose_in() opened.
func _pose_out() -> void:
	pass


func _on_flinch() -> void:
	pass


func _slide_time() -> float:
	return DRIVE_TIME


func _broken_time() -> float:
	return float(body.BREAK.broken_time)


# How far his hurtbox moves while his feet slide from `from` to `to`. A boss whose hurtbox rises with
# his height adds the height he comes down.
func _hurtbox_shift(from: Vector2, to: Vector2) -> Vector2:
	return to - from


func _break_frame() -> void:
	var tree := get_tree()
	HitStop.freeze(tree, BREAK_HIT_STOP)
	ScreenView.shake(tree, SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME, Vector2.ZERO, true)
	ScreenView.zoom_to(tree, ScreenView.zoom * ZOOM, head_point(), ZOOM_IN_TIME, true)
	# The zoom punch eases back out on a real-seconds timer, as the finisher's does. A method rather
	# than a closure: the timer outlives a scene change, the connection doesn't.
	tree.create_timer(ZOOM_IN_TIME + ZOOM_HOLD, false, false, true).timeout.connect(_ease_out_zoom)
	tree.call_group("arena_crowd", "cheer", CHEER)
	_flash_hud()
	sting.play()


# White over the whole view, fading in real time: it plays out through the Break's hit-stop.
func _flash_hud() -> void:
	var flash := ColorRect.new()
	flash.color = FLASH
	flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	body.hud_layer.add_child(flash)
	var fade := flash.create_tween().set_ignore_time_scale(true)
	fade.tween_property(flash, "modulate:a", 0.0, FLASH_TIME)
	fade.tween_callback(flash.queue_free)


func _ease_out_zoom() -> void:
	var player := _player()
	if player and not player.fight_over and not player.finisher.is_active():
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, ZOOM_OUT_TIME, true)


func _start_slide() -> void:
	slide_from = _feet()
	var to := slide_from
	to.y = maxf(to.y, state_machine.states["Juggled"].floor_y())
	var bounds := _feet_bounds()
	# Whole pixels, as the player's drive lands on: floor_y() is rarely one.
	slide_to = to.clamp(bounds.position, bounds.end).round()
	slide_time = _slide_time()
	slide_left = slide_time
	if slide_left <= 0.0:
		_end_slide()


func _end_slide() -> void:
	slide_left = 0.0
	_set_feet(slide_to, 1.0)


# Beside where he will be once he has slid, feet on his ground line and punching range from his
# hurtbox: on the side the player is already on, unless the ropes are in the way. Over a slide longer
# than the drive, the player is held where they are and driven in over its last DRIVE_TIME, so they
# arrive on the tick he lands rather than beside empty floor.
func _drive_player_in() -> void:
	var player := _player()
	if player == null or player.fight_over or player.is_grabbed:
		return
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	box.position += _hurtbox_shift(slide_from, slide_to)
	var side := signf(player.global_position.x - box.get_center().x)
	if side == 0.0:
		side = 1.0
	var spot := _spot_beside(player, box, side)
	if not PLAYER_AREA.has_point(spot):
		spot = _spot_beside(player, box, -side)
	driven = player
	drive_from = player.global_position
	drive_to = spot.clamp(PLAYER_AREA.position, PLAYER_AREA.end)
	# Physics_Update's weight stays at 0 until drive_left is down to DRIVE_TIME.
	drive_left = maxf(DRIVE_TIME, slide_time)
	player.lock_actions()


# The punch the player throws from that side reaches over his hurtbox's edge by half its length.
func _spot_beside(player: Node2D, box: Rect2, side: float) -> Vector2:
	var facing: int = player.Facing.LEFT if side > 0.0 else player.Facing.RIGHT
	var reach: Rect2 = player.punch_box(facing)
	var reach_middle: float = reach.get_center().x * player.global_scale.x
	var edge: float = box.end.x if side > 0.0 else box.position.x
	return Vector2(edge - reach_middle, box.end.y - PLAYER_FEET_OFFSET + PLAYER_IN_FRONT)


func _end_drive() -> void:
	drive_left = 0.0
	if is_instance_valid(driven):
		driven.global_position = drive_to.round()
		driven.unlock_actions()
	driven = null


func _spawn_stars() -> void:
	var spec := FinisherArtLayout.stars()
	stars = Sprite2D.new()
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	stars.z_index = STARS_Z_INDEX
	body.get_parent().add_child(stars)
	stars_clock = 0.0
	_step_stars(0.0)


# On his head as he moves, the slide included.
func _step_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes
	stars.visible = stars_shown
	stars.global_position = head_point().round()


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null


func _player() -> Node2D:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(FightOutro.PLAYER_PATH) as Node2D if scene else null
