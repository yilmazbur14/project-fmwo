extends State

# Mason with his Break gauge full (BossBreakGauge). Whatever he was doing has stopped
# (MasonStateMachine.enter_broken): the fight stops dead for a beat, he goes down winded and open to
# punches, and the player is driven in beside him so there is no walk-up. A 3-hit combo landed there
# starts the finisher (MasonScript.can_be_dazed), and this window is the only one that pays out the
# three-bar mash and the juggle (can_be_juggled). When his time is up he starts his next cycle; when
# the finisher's uppercut ends it instead, MasonStateMachine.end_break does. A juggle (MasonJuggled)
# takes him out of here and does not hand him back.
#
# Unlike EricBroken there is no sword half: Mason has nothing to knock out of his hands.

const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

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

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var mason_state_machine : Node

var time_left := 0.0
var drive_left := 0.0
var drive_from := Vector2.ZERO
var drive_to := Vector2.ZERO
var driven: Node2D
var stars: Sprite2D
var stars_clock := 0.0
var stars_shown := true
var sheet_texture: Texture2D
var sheet_frames := 0


func Enter() -> void:
	time_left = character_body.BREAK.broken_time[mason_state_machine.cycle_phase]
	stars_shown = true
	var art := MasonArtLayout.broken()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	if art.has("texture"):
		# His last frame on the main sheet may not exist on this one, and the AnimationPlayer would
		# index off the end of it.
		sprite.frame = 0
		sprite.hframes = art.hframes
		sprite.texture = load(art.texture)
	# The Break window is worth exactly one 3-punch combo, wherever the hit cap stood when it landed.
	character_body.hits_this_window = 0
	character_body.daze_used = false
	animation_player.play(art.intro if not art.intro.is_empty() else art.loop)
	# The player is driven in beside him, and may be standing in him already.
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	_spawn_stars()
	_break_frame()
	_drive_player_in()


func Exit() -> void:
	_end_drive()
	_clear_stars()
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture


# After his AnimationPlayer has stepped, so the stars sit on the frame that's drawn.
func Update(delta: float) -> void:
	_step_stars(delta)


func Physics_Update(delta: float) -> void:
	if drive_left > 0.0 and is_instance_valid(driven):
		drive_left -= delta
		var t := clampf(1.0 - drive_left / DRIVE_TIME, 0.0, 1.0)
		driven.global_position = drive_from.lerp(drive_to, t * t).round()
		if drive_left <= 0.0:
			_end_drive()
	time_left -= delta
	if time_left <= 0.0:
		mason_state_machine.start_cycle()


# The finisher's daze draws its own stars over the same head.
func show_stars(shown: bool) -> void:
	stars_shown = shown
	_step_stars(0.0)


# Just above his head on the frame he's showing, where the stars circle. The placeholder art has no
# head points of its own, so it uses the one his tell badge and the finisher already stand on.
func head_point() -> Vector2:
	var art := MasonArtLayout.broken()
	var head: Variant = art.get("heads", {}).get(character_body.sprite.frame, art.get("head"))
	if head == null:
		return character_body.get_daze_anchor()
	return character_body.frame_point(head)


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if mason_state_machine.current_state != self:
		return
	var art := MasonArtLayout.broken()
	if anim_name == art.intro:
		animation_player.play(art.loop)


func _break_frame() -> void:
	var tree := get_tree()
	HitStop.freeze(tree, BREAK_HIT_STOP)
	ScreenView.shake(tree, SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME, Vector2.ZERO, true)
	ScreenView.zoom_to(tree, ScreenView.zoom * ZOOM, head_point(), ZOOM_IN_TIME, true)
	# The zoom punch eases back out on a real-seconds timer, as the finisher's does. A method rather
	# than a closure: the timer outlives a scene change, the connection doesn't.
	tree.create_timer(ZOOM_IN_TIME + ZOOM_HOLD, false, false, true).timeout.connect(_ease_out_zoom)
	tree.call_group("arena_crowd", "cheer", CHEER)
	character_body.flash_hud(FLASH, FLASH_TIME)
	character_body.play_break_sting()


func _ease_out_zoom() -> void:
	var player: Node2D = mason_state_machine.get_player()
	if player and not player.fight_over and not player.finisher.is_active():
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, ZOOM_OUT_TIME, true)


# Beside him, feet on his ground line and punching range from his hurtbox: on the side the player is
# already on, unless the ropes are in the way.
func _drive_player_in() -> void:
	var player: Node2D = mason_state_machine.get_player()
	if player == null or player.fight_over or player.is_grabbed:
		return
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var side := signf(player.global_position.x - box.get_center().x)
	if side == 0.0:
		side = 1.0
	var spot := _spot_beside(player, box, side)
	if not PLAYER_AREA.has_point(spot):
		spot = _spot_beside(player, box, -side)
	driven = player
	drive_from = player.global_position
	drive_to = spot.clamp(PLAYER_AREA.position, PLAYER_AREA.end)
	drive_left = DRIVE_TIME
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
	character_body.get_parent().add_child(stars)
	stars_clock = 0.0
	_step_stars(0.0)


# On his head as it moves through his frames.
func _step_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes
	var art := MasonArtLayout.broken()
	var placed: bool = not art.has("heads") or art.heads.has(character_body.sprite.frame)
	stars.visible = stars_shown and placed
	if placed:
		stars.global_position = head_point().round()


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null
