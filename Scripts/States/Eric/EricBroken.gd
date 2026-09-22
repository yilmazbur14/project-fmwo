extends State

# Eric with his Break gauge full (BossBreakGauge, EricPacing V2). Whatever he was doing has stopped
# (EricStateMachine.enter_broken): the fight stops dead for a beat, the Break knocks his sword out of
# his grip into the mat, and he reels and drops to his knees, dazed and open to punches, driving the
# player in beside him so there's no walk-up. A 3-hit combo landed there starts the finisher
# (EricScript.can_be_dazed). When his time is up, or the finisher's uppercut ends it (recover()), he
# gets up and calls his sword back to his hand before his next chain. A juggle (EricJuggled) takes him
# out of here and hands him back for that last part alone (EricStateMachine.after_juggle).

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const SWORD_SCENE := preload("res://Scenes/Bosses/EricThrownSwordScene.tscn")

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
# And this much below it, so the y-sort draws them in front of him and his sword, not behind. It has
# to cover the gap between this offset and the player's own sort point, which don't move together
# when his size does: 1 px was enough while he drew at 2x and left him half a pixel behind at 3x.
const PLAYER_IN_FRONT := 3.0
# The finisher's effects layer: the stars draw over both fighters.
const STARS_Z_INDEX := 2

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var boss_collision_shape : CollisionShape2D
@export var eric_state_machine : Node

@onready var player = get_tree().current_scene.get_node("Arena/MainPlayer/CharacterBody2D")

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
# His sword on its way back to his hand; while it stands in the mat it's EricStateMachine.dropped_sword.
var flying_sword: Node2D
# Set by the state machine as it hands him back from a juggle: he's down already and only gets up.
var retrieve_only := false
# Set by the state machine as it hands him on to a juggle, which keeps his sword where it stands.
var keep_sword := false
# Getting up: no longer dazed or open, the time since it began, the reach beat left, and the wait
# asked for before his next chain.
var retrieving := false
var retrieve_clock := 0.0
var reach_left := 0.0
var chain_delay := 0.0


func Enter() -> void:
	time_left = EricPacing.raged("broken_time", eric_state_machine.rage)
	retrieving = false
	keep_sword = false
	stars_shown = true
	var art := EricArtLayout.broken()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	if art.has("texture"):
		# His last frame on the main sheet may not exist on this one.
		sprite.frame = 0
		sprite.hframes = art.hframes
		sprite.texture = load(art.texture)
	boss_collision_shape.disabled = true
	if retrieve_only:
		retrieve_only = false
		character_body.daze_used = true
		recover(chain_delay)
		return
	character_body.daze_used = false
	animation_player.play(art.intro if not art.intro.is_empty() else art.loop)
	# The player is driven in beside him, and may be standing in him already.
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	if art.has("sword"):
		eric_state_machine.drop_sword()
	_spawn_stars()
	_break_frame()
	_drive_player_in()


func Exit() -> void:
	_end_drive()
	_clear_stars()
	if is_instance_valid(flying_sword):
		flying_sword.queue_free()
	flying_sword = null
	if not keep_sword:
		eric_state_machine.clear_dropped_sword()
	keep_sword = false
	retrieving = false
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	boss_collision_shape.disabled = false
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
	if retrieving:
		retrieve_clock += delta
		if reach_left > 0.0:
			reach_left -= delta
			if reach_left <= 0.0:
				_recall_sword()
		return
	time_left -= delta
	if time_left <= 0.0:
		var rest: float = EricPacing.value("recovery_rest")
		if not recover(rest):
			eric_state_machine.start_chain(rest)


# He gets up on one knee, reaches for his sword and calls it back to his hand. His next chain starts
# `delay` after now, as the finisher's stagger expects, but never less than recovery_rest after he
# has it. False when the Break left the sword in his hands (the placeholder art): there's nothing to
# get up for, and the caller starts his chain.
func recover(delay: float) -> bool:
	if retrieving:
		return true
	if not is_instance_valid(eric_state_machine.dropped_sword):
		return false
	retrieving = true
	retrieve_clock = 0.0
	chain_delay = delay
	_clear_stars()
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	var art := EricArtLayout.broken()
	animation_player.stop()
	character_body.sprite.frame = art.reach_frame
	reach_left = art.reach_time
	return true


# The finisher's daze draws its own stars over the same head.
func show_stars(shown: bool) -> void:
	stars_shown = shown
	_step_stars(0.0)


# Just above his head on the frame he's showing, where the stars circle; the art's own point where
# the frame has none.
func head_point() -> Vector2:
	var art := EricArtLayout.broken()
	var head: Vector2 = art.get("heads", {}).get(character_body.sprite.frame, art.head)
	return character_body.to_global(EricArtLayout.frame_local(head + Vector2(0.5, 0.5), character_body.sprite.flip_h))


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if eric_state_machine.current_state != self:
		return
	var art := EricArtLayout.broken()
	if not retrieving and anim_name == art.intro:
		animation_player.play(art.loop)
	elif retrieving and anim_name == &"recall_catch":
		eric_state_machine.start_chain(maxf(chain_delay - retrieve_clock, EricPacing.value("recovery_rest")))


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
	if not player.fight_over and not player.finisher.is_active():
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, ZOOM_OUT_TIME, true)


# Beside him, feet on his ground line and punching range from his hurtbox: on the side away from his
# sword where it stands on one, or else on the side the player is on, unless the ropes are in the way.
func _drive_player_in() -> void:
	if player.fight_over or player.is_grabbed:
		return
	var shape: CollisionShape2D = hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var area: Rect2 = EricArtLayout.PLAYER_AREA
	var side := signf(player.global_position.x - box.get_center().x)
	if is_instance_valid(eric_state_machine.dropped_sword):
		side = -1.0 if eric_state_machine.dropped_sword.flip_h else 1.0
	elif side == 0.0:
		side = 1.0
	var spot := _spot_beside(box, side)
	if not area.has_point(spot):
		spot = _spot_beside(box, -side)
	driven = player
	drive_from = player.global_position
	drive_to = spot.clamp(area.position, area.end)
	drive_left = DRIVE_TIME
	player.lock_actions()


# The punch the player throws from that side reaches over his hurtbox's edge by half its length.
func _spot_beside(box: Rect2, side: float) -> Vector2:
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


# His recall reach on his own sheet, and the sword flying back into his hand from its crossguard on the
# return flight his thrown sword makes. It's the end of a punish window, not an attack: with no player
# to hit, it can't touch them on the way.
func _recall_sword() -> void:
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
	animation_player.play("recall_reach")
	var dropped: Node2D = eric_state_machine.dropped_sword
	var guard: Vector2 = dropped.guard_point()
	var entry: Vector2 = dropped.mat_point()
	flying_sword = SWORD_SCENE.instantiate()
	flying_sword.speed = EricPacing.raged("sword_speed", eric_state_machine.rage)
	flying_sword.thrower = character_body
	flying_sword.returned.connect(_on_sword_returned)
	eric_state_machine.add_hazard(flying_sword, entry, false)
	flying_sword.lay_shadow_on(eric_state_machine.ground_layer())
	eric_state_machine.clear_dropped_sword()
	var flipped: bool = sprite.flip_h
	var lean := deg_to_rad(EricArtLayout.THROW_CATCH_ANGLE)
	var catch_centre: Vector2 = character_body.to_global(EricArtLayout.frame_local(EricArtLayout.THROW_CATCH_CENTRE, flipped))
	var ground_y: float = character_body.frame_point(Vector2(0, EricArtLayout.FEET_ROW)).y
	flying_sword.recall(catch_centre, ground_y, -lean if flipped else lean, not flipped, entry.y - guard.y)
	var whoosh = character_body.get_node_or_null("WhirlwindSfxPlayer")
	if whoosh:
		if not whoosh.stream:
			whoosh.stream = load("res://Assets/Audio/SFX/whirlwind_whoosh.ogg")
		whoosh.play()


func _on_sword_returned() -> void:
	if eric_state_machine.current_state != self:
		return
	flying_sword.queue_free()
	flying_sword = null
	animation_player.play("recall_catch")


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


# On his head as it moves through his frames. The reel has no head point: the stars wait for his knees.
func _step_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes
	var art := EricArtLayout.broken()
	var frame: int = character_body.sprite.frame
	var placed: bool = not art.has("heads") or art.heads.has(frame)
	stars.visible = stars_shown and placed
	if placed:
		stars.global_position = head_point().round()


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null
