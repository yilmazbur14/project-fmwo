extends State

# Eric's phase-two cut: half his health is gone, the ring stops dead, his greatsword is knocked clean
# out of the arena, and he fights the rest of it with his fists. Its beats are named the way his
# entrance's are (EricIntro), and EricPhaseTwo.dialogue calls the rest between its lines and waits for
# each one - same shape, same rules.
#
# Every wait is a node-bound tween, so a pause stops the cut where it is and a hit-stop carries it
# with the fight. Nothing here uses get_tree().create_timer() or a tree-level tween.
#
# A cut-short cut never kills a tween something is waiting on: `finished` makes every beat bail and
# every stepping callback a no-op instead, so nothing is left half-drawn and nothing hangs.
#
# It is NOT the entrance and it does NOT use BossEntrance.already_seen()/mark_seen(): that is the
# entrance's once-per-run rule, and this plays every single fight. It deliberately has no
# finish_entrance() either - skip_entrance() finds the first node with one, and EricIntro is that node.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricEntranceLayout := preload("res://Scripts/EricEntranceLayout.gd")
const EricPhaseTwoPose := preload("res://Scripts/EricPhaseTwoPose.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const SWORD_SCENE := preload("res://Scenes/Bosses/EricThrownSwordScene.tscn")

@export var animation_player: AnimationPlayer
@export var character_body: CharacterBody2D
@export var hurtbox: Area2D
@export var boss_collision_shape: CollisionShape2D
@export var eric_state_machine: Node

# The break frame, in real seconds so it plays out through its own hit-stop: EricBroken._break_frame()'s
# shape, since this is the same kind of moment and must read as one.
const HIT_STOP := 0.35
const FLASH := Color(1, 1, 1, 0.6)
const FLASH_TIME := 0.14
const SHAKE := 26.0
const SHAKE_STEPS := 9
const SHAKE_STEP_TIME := 0.03
const ZOOM := 1.25
const ZOOM_IN_TIME := 0.05
const ZOOM_OUT_TIME := 0.4
const CHEER := 3.5
# The beats: he reels while the blade leaves, then the lines take over.
const REEL_HOLD := 0.45
const STARE_HOLD := 0.7
const SET_HOLD := 0.5
# Before his first phase-two chain, so the last line is off the screen before he moves.
const CHAIN_DELAY := 0.6

# The cut is over, one way or another. Every beat checks it; finish_phase() is the only thing that
# sets it.
var finished := false
var dialogue_started := false
# Enter() can be reached from a physics flush, so anything reaching in from outside checks this
# first: there is nothing to cut before it has run.
var entered := false
# Where he stands when it starts, which his first phase-two chain begins from.
var home := Vector2.ZERO
# The shared entrance layer: the hold on the player and the skip hint.
var cut: CanvasLayer
var sword: Node2D
var sword_flight: Tween
var ringside: Sprite2D
var sheet_texture: Texture2D
var sheet_frames := 0
var pose_frames: Array = []
var pose_loop: Tween


func Enter() -> void:
	entered = true
	finished = false
	dialogue_started = false
	home = character_body.global_position
	animation_player.stop()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	boss_collision_shape.disabled = true
	# A Break that landed on the crossing punch may have left his sword standing in the mat. It is
	# about to be thrown out of the arena, so it goes now rather than being retrieved first.
	eric_state_machine.clear_dropped_sword()
	# A gauge that filled on the same punch would fight the cut for the state machine. Locked the way
	# a Break locks it - the wait has to be set too, or the gauge's own physics step unlocks it again
	# on the very next frame - so it takes nothing until unlock_delay after he is fighting again.
	if character_body.break_gauge:
		character_body.break_gauge.locked = true
		character_body.break_gauge.unlock_left = character_body.break_gauge.unlock_delay
	_play()


# The cut is over however it got here, including the fight being decided over the top of it: the
# player gets their own state machine back either way.
func Exit() -> void:
	finished = true
	_stop_pose_loop()
	if is_instance_valid(cut):
		cut.end()
	cut = null
	boss_collision_shape.disabled = false
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
	ScreenView.reset(get_tree())


#THE BEATS

func _play() -> void:
	cut = BossEntrance.new()
	cut.name = "PhaseTwoCut"
	add_child(cut)
	cut.skipped.connect(skip)
	cut.begin(_player())
	_break_frame()
	_show("reel")
	_throw_sword_clear()
	await _beat(REEL_HOLD)
	if finished:
		return
	_start_dialogue()


# He turns his empty hand over and looks at it. Called by the dialogue between its lines.
func look_at_hands() -> void:
	if finished:
		return
	_show("stare")
	ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, ZOOM_OUT_TIME)
	await _beat(STARE_HOLD)


# Fists up: from here the fight is his hands. Called by the dialogue between its lines.
func set_fists() -> void:
	if finished:
		return
	_show("set")
	get_tree().call_group("arena_crowd", "cheer", CHEER)
	await _beat(SET_HOLD)


#ENDING IT

# The one way the cut ends: its last line, a skip, or the fight being decided over the top of it.
# Idempotent - it leaves the ring exactly as phase two expects it whichever of those got here.
func finish_phase() -> void:
	if finished or not entered:
		return
	finished = true
	_stop_pose_loop()
	if sword_flight != null and sword_flight.is_valid():
		sword_flight.kill()
	sword_flight = null
	if is_instance_valid(sword):
		sword.queue_free()
	sword = null
	_plant_ringside()
	character_body.global_position = home
	_show("set")
	ScreenView.reset(get_tree())
	if is_instance_valid(cut):
		cut.end()
	cut = null
	if eric_state_machine.defeated or character_body.boss_health <= 0:
		return
	eric_state_machine.start_chain(CHAIN_DELAY)


# What a held ui_cancel does to an entrance, for this cut: the ring set at once and the lines started.
# Public, so a test can cut it exactly the way a player cuts it.
func skip() -> void:
	if finished:
		return
	ScreenView.reset(get_tree())
	_start_dialogue()


func _start_dialogue() -> void:
	if dialogue_started or finished:
		return
	dialogue_started = true
	eric_state_machine.show_phase_two_dialogue(self)


#PIECES

# The sword goes over the ropes and out of frame, spinning. It is the thrown sword's art but not its
# flight: this one is never a hazard, never plants and never comes back, so it is driven from here
# rather than through throw(), and its hitbox is left shut.
func _throw_sword_clear() -> void:
	sword = SWORD_SCENE.instantiate()
	sword.plants = false
	var hand: Vector2 = character_body.frame_point(EricArtLayout.P2_SWORD_HAND_PIXEL)
	eric_state_machine.add_hazard(sword, hand, false)
	sword.remove_from_group(eric_state_machine.HAZARD_GROUP)
	sword.get_node("Shadow").visible = false
	sword.get_node("Planted").visible = false
	# Never a hazard: it is not flying under its own script (nothing calls throw() or recall(), so
	# `flying` stays false and _resolve_hits() is never reached), it has no player to resolve against,
	# and its hitbox is shut here as well. Three locks, because a live blade with no tell in the
	# middle of a cutscene would be unanswerable.
	sword.player = null
	sword.get_node("Hitbox").monitoring = false
	sword.get_node("Hitbox").monitorable = false
	var away := 1.0 if hand.x <= EricArtLayout.P2_ARENA_MIDDLE else -1.0
	var exit_point := hand + Vector2(EricArtLayout.P2_SWORD_EXIT.x * away, EricArtLayout.P2_SWORD_EXIT.y)
	sword_flight = create_tween()
	sword_flight.tween_method(_step_sword.bind(hand, exit_point), 0.0, 1.0, EricArtLayout.P2_SWORD_FLIGHT)
	sword_flight.tween_callback(_drop_sword)


func _step_sword(t: float, from: Vector2, to: Vector2) -> void:
	if finished or not is_instance_valid(sword):
		return
	sword.global_position = from.lerp(to, t)
	var blade: Sprite2D = sword.get_node("Sword")
	blade.frame = int(t * EricArtLayout.P2_SWORD_FLIGHT / EricArtLayout.P2_SWORD_SPIN_TIME) % EricArtLayout.SPIN_FRAMES


func _drop_sword() -> void:
	if is_instance_valid(sword):
		sword.queue_free()
	sword = null
	_plant_ringside()


# The blade in the boards outside the ring, left standing there for the rest of the fight. Added the
# way EricIntro plants its own and then taken straight back out of the hazard group, so
# _stop_everything() can't free it.
func _plant_ringside() -> void:
	if is_instance_valid(ringside):
		return
	ringside = Sprite2D.new()
	ringside.name = "EricRingsideSword"
	ringside.texture = load(EricEntranceLayout.PLANTED_SWORD)
	ringside.scale = character_body.scale
	ringside.offset = EricEntranceLayout.planted_offset(ringside.texture)
	ringside.z_index = EricArtLayout.P2_SWORD_RINGSIDE_Z
	var spot := EricArtLayout.P2_SWORD_RINGSIDE
	if home.x > EricArtLayout.P2_ARENA_MIDDLE:
		spot.x = 2.0 * EricArtLayout.P2_ARENA_MIDDLE - spot.x
		ringside.flip_h = true
	eric_state_machine.add_hazard(ringside, spot, false)
	ringside.remove_from_group(eric_state_machine.HAZARD_GROUP)


# EricBroken._break_frame()'s shape: the fight stops dead, the HUD flashes, the view shakes and punches
# in, and the crowd roars.
func _break_frame() -> void:
	var tree := get_tree()
	HitStop.freeze(tree, HIT_STOP)
	ScreenView.shake(tree, SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME, Vector2.ZERO, true)
	ScreenView.zoom_to(tree, ScreenView.zoom * ZOOM, character_body.global_position, ZOOM_IN_TIME, true)
	tree.call_group("arena_crowd", "cheer", CHEER)
	character_body.flash_hud(FLASH, FLASH_TIME)
	character_body.play_break_sting()


func _show(key: String) -> void:
	_stop_pose_loop()
	pose_frames = EricPhaseTwoPose.show(character_body.sprite, key)
	if pose_frames.size() < 2:
		return
	pose_loop = create_tween().set_loops()
	for index in pose_frames:
		pose_loop.tween_callback(_show_frame.bind(index))
		pose_loop.tween_interval(EricArtLayout.phase_two_frame_time())


# Queued by the pose loop, so it checks the cut is still running itself.
func _show_frame(index: int) -> void:
	if finished:
		return
	character_body.sprite.frame = index


func _stop_pose_loop() -> void:
	if pose_loop != null and pose_loop.is_valid():
		pose_loop.kill()
	pose_loop = null


# Waits `seconds` on this node's own clock. A cut-short cut lets it run out rather than killing it,
# and the caller's own `finished` check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished


func _player() -> Node:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")
