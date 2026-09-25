extends State

# Matt's entrance: a friendly walk-in and a RuneScape argument that ends in an arena-shaking roar. The
# ropes open and the player walks up into the ring, then he strolls down through the top gate waving to
# the crowd, waves at the player, and the gates slam behind him. MattPreFight.dialogue takes it from
# there, and calls the beats below between its lines - composes_himself(), pulls_out_hong(),
# screams_at_hong(), small_pause() and roars() - waiting for each. The VS card and the fight hang off
# dialogue_ended as they always have.
#
# HIS POSE IS THE LINES' TAGS, read off the live balloon every frame, so balloon.gd knows nothing about
# him: `matt` sets his talk pose on any speaker's line, `glance` turns him toward a heckler until the
# next `matt`, and `shout` jolts the ring and hushes the crowd as the line comes up. While one of his
# own lines is typing his mouth flaps between the pose's two frames. A beat owns his frames from its
# first call until the next line comes up, so nothing flickers between two beats in a row.
#
# THE HOLD SKIPS ALL OF IT (BossEntrance). Every wait is a node-bound tween in `waits`, every beat checks
# _intro_is_live() after each one - never `finished`, so the beats replay on a retry, where the walk-in
# does not - and _after_roar() is the end state of every beat the lines could still call. A skip, a
# watched entrance and a fight started over the top of it all leave the same ring at the VS card's
# flash: him idling at HOME and unflipped, the HUD up, the gates shut, the player on their mark, the
# view level, the crowd at rest, his theme started once, and no doll or ring left anywhere.
#
# Nothing here uses get_tree().create_timer() or a tree-level tween, and his lines never use [wait=N] or
# "do wait(N)": both run on a SceneTree timer, which ticks through the pause screen and which a skip
# can't run out.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const RING_SCENE := preload("res://Scenes/Bosses/MattYellRingScene.tscn")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/MattBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const GATES_PATH := "Arena/Gates"

#THE WALK-IN
# Both fighters are moved by written global_position, so nothing collides and nothing desyncs. He starts
# this far above his mark, the whole of him off the top of the screen, and comes straight down through
# the top gate's doorway; the player rises from this far below theirs.
const WALK_IN_RISE := 700.0
const PLAYER_WALK_DROP := 260.0
const PLAYER_WALK_TIME := 1.6
const MATT_WALK_TIME := 2.4

#BEATS, IN SECONDS
const OPEN_BEAT := 0.4
const PLAYER_BEAT := 0.4
# He waves at the player on arrival: the friendly pose talking.
const ARRIVE_WAVE := 0.5
const SETTLE_BEAT := 0.4
const PLAYER_CHEER := 1.6
const MATT_CHEER := 2.4
# The shout tag's jolt as its line comes up.
const SHOUT_SHAKE := 6.0
const SHOUT_SHAKE_STEPS := 4
const SHOUT_SHAKE_STEP_TIME := 0.04

#THE BEATS THE LINES CALL
# "NO I DID NOT." and the two seconds it takes him to pull it back: the snap held, then the sheepish.
const COMPOSE_TIME := 2.0
const COMPOSE_SNAP_HOLD := 1.2
# Reach, pull, and Hong held out at arm's length, with a squeak as it comes out (matt_doll 0-2).
const PULL_TIME := 0.64
const PULL_SQUEAK_AT := 0.24
# The scream at Hong (matt_doll 3-5 cycling).
const SCREAM_TIME := 1.6
const SCREAM_SHAKE := 5.0
const SCREAM_SHAKE_STEPS := 32
const SCREAM_SHAKE_STEP_TIME := 0.05
# Hong back in the pocket, a deep breath out, then the forced smile held.
const PAUSE_TIME := 1.5
const STOW_TIME := 0.15
const EXHALE_TIME := 0.30
# The roar: the brace, the roar itself, then the idle he settles back into.
const INHALE_TIME := 0.35
const ROAR_TIME := 1.8
const ROAR_SETTLE := 0.4
const ROAR_HIT_STOP := 0.08
const ROAR_SHAKE := 26.0
const ROAR_SHAKE_STEPS := 14
const ROAR_SHAKE_STEP_TIME := 0.045
# The first shake's end, where the second takes over.
const ROAR_AFTERSHAKE_AT := 0.63
const ROAR_AFTERSHAKE := 12.0
const ROAR_AFTERSHAKE_STEPS := 10
const ROAR_AFTERSHAKE_STEP_TIME := 0.05
const ROAR_ZOOM := 1.12
const ROAR_ZOOM_IN := 0.12
const ROAR_ZOOM_BACK_AT := 1.2
const ROAR_ZOOM_BACK := 0.6
# Sound rings off his mouth, for the picture only: nothing in the entrance can hurt anyone.
const ROAR_RING_TIMES := [0.0, 0.3, 0.6]
const ROAR_CHEER := 2.5

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# The entrance layer: the hold on the player, their walk, and the skip and its hint through the lines.
var entrance: CanvasLayer
# Where the two of them end up: his is HOME, the player's is read off the scene.
var home := Vector2.ZERO
var player_home := Vector2.ZERO
# The walk-in is over, one way or another. finish_entrance() and Exit() are the only things that set it.
var finished := false
var dialogue_started := false
# Enter() is deferred, so anything that can reach in from outside checks this first.
var entered := false
# A held skip took everything up to the VS card: the lines are gone, and a beat they would still have
# called does nothing.
var cut := false
# The tweens the walk-in and the beats are waiting on, for the skip to run out.
var waits: Array[Tween] = []
# A beat is playing and owns his frames until the next line comes up.
var beat_running := false
# The pose the lines last asked for, and the line it came from.
var pose := &"friendly"
var last_line: RefCounted
# The stand-in doll and the roar's rings: his entrance's own effects, never in the fight's hazard group.
var intro_fx: Array[Node] = []
# Beats seen through to their end, for a test: name -> game seconds it took.
var beat_times := {}


func Enter() -> void:
	# Deferred, so the fight may already have been started over the top of this state (Exit).
	if finished:
		return
	entered = true
	home = state_machine.HOME
	var player := _player()
	player_home = player.global_position if player != null else Vector2.ZERO
	body.set_hurtbox_active(false)
	# On the retry path too: the walk-in is skipped there, but the lines still play and the hold still
	# skips them.
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin(player)
	if BossEntrance.already_seen(FIGHT_SCENE):
		finish_entrance()
		_start_dialogue()
		return
	# Both of them are put outside the ring here, in the frame the state is entered, rather than when
	# their own walk comes round: anywhere later and they are seen standing on their marks first.
	body.play_anim(&"walk")
	body.global_position = home - Vector2(0, WALK_IN_RISE)
	if player != null:
		player.global_position = player_home + Vector2(0, PLAYER_WALK_DROP)
	_play()


# The fight starts here. A harness that starts it over the top of the entrance leaves through here too,
# so this is also what guarantees the ring is set however the entrance ended.
func Exit() -> void:
	finish_entrance()
	finished = true
	_after_roar()
	if is_instance_valid(entrance):
		entrance.queue_free()
	entrance = null


func Update(_delta: float) -> void:
	_read_lines()


#THE WALK-IN

func _play() -> void:
	# His bar comes up with the gates, not before him: announcing a boss who hasn't walked in is the wrong
	# way round.
	if body.hud_layer != null:
		body.hud_layer.hide()
	var gates := _gates()
	if gates != null:
		gates.open()
	await _beat(OPEN_BEAT)
	if finished:
		return

	var player := _player()
	if player != null:
		get_tree().call_group("arena_crowd", "cheer", PLAYER_CHEER)
		await entrance.walk_player(player_home, PLAYER_WALK_TIME)
	if finished:
		return
	await _beat(PLAYER_BEAT)
	if finished:
		return

	get_tree().call_group("arena_crowd", "cheer", MATT_CHEER)
	await _walk_matt_in()
	if finished:
		return

	body.show_talk(&"friendly", true)
	await _beat(ARRIVE_WAVE)
	if finished:
		return
	body.show_talk(&"friendly", false)

	if gates != null:
		await gates.close()
	if finished:
		return
	if body.hud_layer != null:
		body.hud_layer.show()
	await _beat(SETTLE_BEAT)
	if finished:
		return
	finish_entrance()
	_start_dialogue()


# A friendly stroll straight down to his mark, waving to the crowd the whole way.
func _walk_matt_in() -> void:
	var from := home - Vector2(0, WALK_IN_RISE)
	body.play_anim(&"walk")
	var walk := create_tween()
	walk.tween_method(_step_matt.bind(from, home), 0.0, 1.0, MATT_WALK_TIME)
	await _wait(walk)
	if finished:
		return
	body.global_position = home


# Whole pixels, so the pixel-art body doesn't shimmer as it walks.
func _step_matt(weight: float, from: Vector2, to: Vector2) -> void:
	if finished:
		return
	body.global_position = from.lerp(to, weight).round()


#THE LINES' TAGS

func _read_lines() -> void:
	if cut or not entered:
		return
	# Untyped: the balloon frees itself when the lines end, and a freed object can't be held in a typed
	# variable long enough to ask is_instance_valid about it.
	var balloon = state_machine.pre_fight_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line == null:
		return
	if line != last_line:
		last_line = line
		beat_running = false
		_apply_tags(line)
	if beat_running:
		return
	var talking: bool = line.character == "Matt" and balloon.dialogue_label.is_typing
	body.show_talk(pose, talking)


func _apply_tags(line: RefCounted) -> void:
	if line.has_tag("matt"):
		pose = StringName(line.get_tag_value("matt"))
		body.sprite.flip_h = false
	if line.has_tag("glance"):
		# His sheets face screen-right unflipped, the way every flip in this game reads.
		body.sprite.flip_h = line.get_tag_value("glance") == "left"
	if line.has_tag("shout"):
		ScreenView.shake(get_tree(), SHOUT_SHAKE, SHOUT_SHAKE_STEPS, SHOUT_SHAKE_STEP_TIME)
		get_tree().call_group("arena_crowd", "hush")


#THE BEATS THE DIALOGUE CALLS

# Two seconds of him pulling it back together, with the balloon down: the snap held, then the sheepish.
func composes_himself() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	get_tree().call_group("arena_crowd", "hush")
	body.show_talk(&"snap", false)
	var started := _now()
	var hold := create_tween()
	hold.tween_interval(COMPOSE_SNAP_HOLD)
	hold.tween_callback(_hold_pose.bind(&"sheepish"))
	hold.tween_interval(COMPOSE_TIME - COMPOSE_SNAP_HOLD)
	await _wait(hold)
	if _intro_is_live():
		beat_times[&"composes_himself"] = _now() - started


func pulls_out_hong() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	var started := _now()
	body.sprite.flip_h = false
	body.play_anim(&"doll_pull")
	_show_doll()
	var pull := create_tween()
	pull.tween_interval(PULL_SQUEAK_AT)
	pull.tween_callback(_squeak)
	pull.tween_interval(PULL_TIME - PULL_SQUEAK_AT)
	await _wait(pull)
	if _intro_is_live():
		beat_times[&"pulls_out_hong"] = _now() - started


func screams_at_hong() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	var started := _now()
	body.play_anim(&"doll_scream")
	body.play_sfx(&"scream_hong")
	ScreenView.shake(get_tree(), SCREAM_SHAKE, SCREAM_SHAKE_STEPS, SCREAM_SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "hush")
	await _beat(SCREAM_TIME)
	if _intro_is_live():
		beat_times[&"screams_at_hong"] = _now() - started


# Hong back in his pocket and a deep breath out, then the forced smile, held.
func small_pause() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	var started := _now()
	body.play_anim(&"doll_stow")
	var pause := create_tween()
	pause.tween_interval(STOW_TIME)
	pause.tween_callback(_stow_doll)
	pause.tween_interval(EXHALE_TIME)
	pause.tween_callback(_hold_pose.bind(&"forced"))
	pause.tween_interval(PAUSE_TIME - STOW_TIME - EXHALE_TIME)
	await _wait(pause)
	if _intro_is_live():
		beat_times[&"small_pause"] = _now() - started


# The brace, then the roar that shakes the arena: a dead stop, a hard jolt and a punch-in on his mouth,
# rings of sound, the crowd going off - and his theme, which starts here and nowhere else in a watched
# entrance.
func roars() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	var started := _now()
	get_tree().call_group("arena_crowd", "hush")
	body.sprite.flip_h = false
	body.play_anim(&"roar_inhale")
	body.play_sfx(&"roar_inhale")
	await _beat(INHALE_TIME)
	if not _intro_is_live():
		return

	var mouth: Vector2 = body.mouth_point(&"roar")
	body.play_anim(&"roar")
	body.play_sfx(&"roar")
	HitStop.freeze(get_tree(), ROAR_HIT_STOP)
	ScreenView.shake(get_tree(), ROAR_SHAKE, ROAR_SHAKE_STEPS, ROAR_SHAKE_STEP_TIME)
	ScreenView.zoom_to(get_tree(), ROAR_ZOOM, mouth, ROAR_ZOOM_IN)
	get_tree().call_group("arena_crowd", "cheer", ROAR_CHEER)
	body.start_music()
	var roar := create_tween()
	var at := 0.0
	var marks := []
	for ring_at: float in ROAR_RING_TIMES:
		marks.append([ring_at, _roar_ring])
	marks.append([ROAR_AFTERSHAKE_AT, _aftershake])
	marks.append([ROAR_ZOOM_BACK_AT, _zoom_back])
	marks.sort_custom(func(a, b): return a[0] < b[0])
	for mark in marks:
		roar.tween_interval(maxf(mark[0] - at, 0.0))
		roar.tween_callback(mark[1])
		at = maxf(mark[0], at)
	roar.tween_interval(ROAR_TIME - at)
	await _wait(roar)
	if not _intro_is_live():
		return

	body.play_state_anim(&"idle")
	await _beat(ROAR_SETTLE)
	if not _intro_is_live():
		return
	beat_times[&"roars"] = _now() - started
	_after_roar()


func _roar_ring() -> void:
	if not _intro_is_live():
		return
	var ring: Node2D = RING_SCENE.instantiate()
	ring.start_radius = state_machine.yell_start_radius
	ring.end_radius = state_machine.yell_radius
	ring.band = state_machine.yell_band
	ring.expand_time = state_machine.yell_expand_time
	ring.landing_time = state_machine.yell_landing_time
	body.projectile_layer.add_child(ring)
	ring.global_position = body.mouth_point(&"roar").round()
	intro_fx.append(ring)


func _aftershake() -> void:
	if _intro_is_live():
		ScreenView.shake(get_tree(), ROAR_AFTERSHAKE, ROAR_AFTERSHAKE_STEPS, ROAR_AFTERSHAKE_STEP_TIME)


# Back to level on the view's own middle, which is where a skip's reset leaves it too.
func _zoom_back() -> void:
	if _intro_is_live():
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.VIEW_SIZE / 2.0, ROAR_ZOOM_BACK)


func _hold_pose(held: StringName) -> void:
	if _intro_is_live():
		body.show_talk(held, false)


func _squeak() -> void:
	if _intro_is_live():
		body.play_sfx(&"doll_squeak")


# Where every beat the lines could still call leaves him, all at once: idling at HOME, whole and
# unflipped, nothing of the doll or the rings left, and his theme on. Idempotent; a watched entrance
# comes through here at the end of its roar, a skip on its way to the card, and the fight starting.
func _after_roar() -> void:
	beat_running = false
	for node in intro_fx:
		if is_instance_valid(node):
			node.queue_free()
	intro_fx.clear()
	if not is_instance_valid(body):
		return
	body.global_position = home
	body.show_body()
	if body.current_anim != &"idle":
		body.state_anim = &"idle"
		body.play_anim(&"idle")
	body.start_music()


#THE DOLL
# Hong is drawn into the doll sheet, in his fist; this stand-in is only for when that sheet is off.

func _show_doll() -> void:
	if MattArtLayout.USE_FINAL_ANIMS[&"doll_pull"]:
		return
	var spec: Dictionary = MattArtLayout.fx(&"doll")
	var size: Vector2 = spec.size
	var doll := Node2D.new()
	doll.name = "Hong"
	var parts := [
		[Rect2(-size.x / 2.0, -size.y, size.x, size.y * 0.3), spec.skin],
		[Rect2(-size.x / 2.0, -size.y, size.x, size.y * 0.1), spec.hair],
		[Rect2(-size.x / 2.0, -size.y * 0.7, size.x, size.y * 0.35), spec.shirt],
		[Rect2(-size.x / 2.0, -size.y * 0.35, size.x, size.y * 0.35), spec.trousers],
	]
	for part in parts:
		var rect: Rect2 = part[0]
		var panel := Polygon2D.new()
		panel.polygon = PackedVector2Array([rect.position, rect.position + Vector2(rect.size.x, 0),
			rect.position + rect.size, rect.position + Vector2(0, rect.size.y)])
		panel.color = part[1]
		doll.add_child(panel)
	body.add_child(doll)
	doll.position = MattArtLayout.frame_local(MattArtLayout.DOLL_HAND)
	intro_fx.append(doll)


func _stow_doll() -> void:
	if not _intro_is_live():
		return
	for node in intro_fx:
		if is_instance_valid(node) and node.name == "Hong":
			node.queue_free()


#ENDING IT

# The one way the walk-in ends: its last beat, a skip, or the fight being started over the top of it.
# Idempotent - it leaves the ring exactly as the lines expect it whichever of those got here.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	body.global_position = home
	body.show_body()
	body.show_talk(&"friendly", false)
	if body.hud_layer != null:
		body.hud_layer.show()
	var gates := _gates()
	if gates != null:
		gates.shut_now()
	var player := _player()
	if player != null:
		player.global_position = player_home
	if is_instance_valid(entrance):
		entrance.release_player()
	BossEntrance.mark_seen(FIGHT_SCENE)


# The walk-in cut on the spot and the lines started: where a second go at the fight starts on its own.
# Public, so the defence suite can cut the entrance this way - its modes are about the fight, and read
# the lines or throw them away themselves.
func skip() -> void:
	if cut:
		return
	ScreenView.reset(get_tree())
	finish_entrance()
	_start_dialogue()


# What a held ui_cancel does: the walk-in, whatever is left of the lines and their beats, and the card's
# build-up, all at once, landing on the card's flash with the ring a watched entrance leaves.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	finish_entrance()
	BossEntrance.run_out(waits)
	_after_roar()
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


# The lines have handed over to the VS card, and the skip goes with them.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue(self)


# The lines can be ended from outside - the defence suite frees the balloon and ends the dialogue by
# hand - which starts the fight under whichever beat is in flight, and a held skip ends them too. Every
# beat asks this before it touches him, so a beat that outlived the entrance leaves the fight alone.
func _intro_is_live() -> bool:
	return not cut and is_instance_valid(body) and state_machine.current_state == self


#PIECES

# Waits `seconds` on this node's own clock. A cut-short entrance lets it run out rather than killing it,
# and the caller's own check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


# The fight's own clock, for timing the beats in game seconds.
func _now() -> float:
	return body.fight_clock


func _player() -> Node:
	return get_tree().current_scene.get_node_or_null(PLAYER_PATH)


func _gates() -> Node:
	return get_tree().current_scene.get_node_or_null(GATES_PATH)
