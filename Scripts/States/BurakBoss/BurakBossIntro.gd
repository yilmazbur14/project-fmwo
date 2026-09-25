extends State

# Captain Burak's entrance: a swagger and a warning shot. The ropes open and the player walks up into the
# ring, then he swaggers down through the top gate to HOME, smirks at the player, and the gates slam
# behind him. BurakBossPreFight.dialogue takes it from there, calls warning_shot() between its lines and
# waits for it. The VS card and the fight hang off dialogue_ended as they always have.
#
# HIS POSE IS THE LINES' TAGS, read off the live balloon every frame, so balloon.gd knows nothing about
# him: `captain` sets his talk pose on any speaker's line, and `glance` turns him toward ringside until the
# next `captain`. While one of his own lines is typing his mouth flaps between the pose's two frames. The
# warning shot owns his frames from its first call until the next line comes up.
#
# THE HOLD SKIPS ALL OF IT (BossEntrance). Every wait is a node-bound tween in `waits`, every beat checks
# _intro_is_live() after each one - never `finished`, so the shot replays on a retry, where the walk-in
# does not - and _after_intro() is the end state of every beat the lines could still call. A skip, a
# watched entrance and a fight started over the top of it all leave the same ring at the VS card's flash:
# him idling at HOME, whole and unflipped, the HUD up, the gates shut, the player on their mark, the view
# level, the crowd at rest, his theme started once, and nothing of the shot left anywhere. Nothing in the
# entrance can hurt anyone: the shot's ball is harmless and its effects are the entrance's own
# (intro_fx), never in the fight's hazard group.
#
# Nothing here uses get_tree().create_timer() or a tree-level tween, and his lines never use [wait=N] or
# "do wait(N)": both run on a SceneTree timer, which ticks through the pause screen and which a skip
# can't run out.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")
const BALL_SCENE := preload("res://Scenes/Bosses/BurakBossBallScene.tscn")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/BurakBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const GATES_PATH := "Arena/Gates"
# The name his lines go under.
const SPEAKER := "Captain Burak"

#THE WALK-IN
# Both fighters are moved by written global_position, so nothing collides and nothing desyncs. He starts
# this far above his mark, the whole of him off the top of the screen, and comes straight down through
# the top gate's doorway; the player rises from this far below theirs.
const WALK_IN_RISE := 700.0
const PLAYER_WALK_DROP := 260.0
const PLAYER_WALK_TIME := 1.6
const BURAK_WALK_TIME := 2.2

#BEATS, IN SECONDS
const OPEN_BEAT := 0.4
const PLAYER_BEAT := 0.4
# He smirks at the player on arrival, mouth shut.
const ARRIVE_SMIRK := 0.5
const SETTLE_BEAT := 0.4
const PLAYER_CHEER := 1.6
const BURAK_CHEER := 2.2

#THE WARNING SHOT (1.35 s)
# He aims at the player, fires, the ball smacks into the mat just short of them, he rides the recoil and
# holds the smug pose.
const SHOT_AIM := 0.40
const SHOT_FLIGHT := 0.25
const SHOT_RECOIL := 0.30
const SHOT_SMUG := 0.40
# The ball lands this far short of the player's feet, on the line from his muzzle.
const SHOT_SHORT := 60.0
# The player's origin stands this far over their soles.
const PLAYER_BODY_OVER_FEET := 36.0
const SHOT_HIT_STOP := 0.05
const SHOT_SHAKE := 8.0
const SHOT_SHAKE_STEPS := 4
const SHOT_SHAKE_STEP_TIME := 0.04
const LAND_CHEER := 1.0

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
var pose := &"smug"
var last_line: RefCounted
# The warning shot's ball, muzzle flash and dust: the entrance's own effects, never in the hazard group.
var intro_fx: Array[Node] = []
# Where the warning shot's ball lands.
var shot_mark := Vector2.ZERO
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
	_after_intro()
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

	get_tree().call_group("arena_crowd", "cheer", BURAK_CHEER)
	await _walk_burak_in()
	if finished:
		return

	body.show_talk(&"smug", false)
	await _beat(ARRIVE_SMIRK)
	if finished:
		return

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


# A swagger straight down to his mark.
func _walk_burak_in() -> void:
	var from := home - Vector2(0, WALK_IN_RISE)
	body.play_anim(&"walk")
	var walk := create_tween()
	walk.tween_method(_step_burak.bind(from, home), 0.0, 1.0, BURAK_WALK_TIME)
	await _wait(walk)
	if finished:
		return
	body.global_position = home


# Whole pixels, so the pixel-art body doesn't shimmer as it walks.
func _step_burak(weight: float, from: Vector2, to: Vector2) -> void:
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
	var talking: bool = line.character == SPEAKER and balloon.dialogue_label.is_typing
	body.show_talk(pose, talking)


func _apply_tags(line: RefCounted) -> void:
	if line.has_tag("captain"):
		pose = StringName(line.get_tag_value("captain"))
		body.sprite.flip_h = false
	if line.has_tag("glance"):
		# His sheets face screen-right unflipped, the way every flip in this game reads.
		body.sprite.flip_h = line.get_tag_value("glance") == "left"


#THE BEAT THE DIALOGUE CALLS

# Aimed at the player, fired, and the ball smacks into the mat just short of their feet: a warning, and
# the start of his theme. Nothing in it can hurt.
func warning_shot() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	var started := _now()
	body.sprite.flip_h = false
	var player := _player()
	if player != null:
		body.face_toward(player.global_position)
	body.play_anim(&"fire_aim")
	var shot := create_tween()
	shot.tween_interval(SHOT_AIM)
	shot.tween_callback(_fire)
	shot.tween_interval(SHOT_FLIGHT)
	shot.tween_callback(_land)
	shot.tween_interval(SHOT_RECOIL)
	shot.tween_callback(_hold_pose.bind(&"smug"))
	shot.tween_interval(SHOT_SMUG)
	await _wait(shot)
	if _intro_is_live():
		beat_times[&"warning_shot"] = _now() - started


# FIRE: the flash and the bang, and the ball on its way to the mark just short of the player.
func _fire() -> void:
	if not _intro_is_live():
		return
	body.play_anim(&"fire")
	var muzzle: Vector2 = body.muzzle_point(&"fire")
	shot_mark = _shot_mark(muzzle)
	_muzzle_flash(muzzle, muzzle.direction_to(shot_mark))
	body.play_sfx(&"gunshot")
	HitStop.freeze(get_tree(), SHOT_HIT_STOP)
	ScreenView.shake(get_tree(), SHOT_SHAKE, SHOT_SHAKE_STEPS, SHOT_SHAKE_STEP_TIME)
	body.start_music()
	var ball: Node2D = BALL_SCENE.instantiate()
	ball.harmless = true
	# Flown in exactly SHOT_FLIGHT, however far it has to go.
	ball.max_speed = INF
	ball.min_flight = SHOT_FLIGHT
	ball.ropes = state_machine.ROPES
	ball.body = body
	ball.aim(muzzle, shot_mark)
	body.projectile_layer.add_child(ball)
	ball.global_position = muzzle.round()
	intro_fx.append(ball)


# Where the ball lands: SHOT_SHORT short of the player's feet on the line from the muzzle.
func _shot_mark(muzzle: Vector2) -> Vector2:
	var player := _player()
	if player == null:
		return home + Vector2(0, 300)
	var feet: Vector2 = player.global_position + Vector2(0, PLAYER_BODY_OVER_FEET)
	return (feet - muzzle.direction_to(feet) * SHOT_SHORT).round()


# The ball smacks into the mat: dust and a thud where it landed, and the crowd goes up.
func _land() -> void:
	if not _intro_is_live():
		return
	var spec: Dictionary = Layout.fx(&"barrel_land")
	var dust := Sprite2D.new()
	dust.texture = load(spec.texture)
	dust.hframes = spec.hframes
	dust.offset = spec.offset
	dust.scale = Vector2.ONE * Layout.SCALE
	body.floor_layer.add_child(dust)
	dust.global_position = shot_mark
	intro_fx.append(dust)
	_play_frames(dust, spec.frame_time)
	body.play_sfx(&"barrel_land")
	get_tree().call_group("arena_crowd", "cheer", LAND_CHEER)


# The flash and the smoke off his muzzle, at the drawn heading nearest the shot's: flipped across for a
# shot going left, never up and down, because the smoke always rises.
func _muzzle_flash(at: Vector2, heading: Vector2) -> void:
	var spec: Dictionary = Layout.fx(&"muzzle")
	var pick: Array = Layout.art_frame(Vector2(heading.x, absf(heading.y)), spec.headings)
	var flash := Sprite2D.new()
	flash.texture = load(spec.texture)
	flash.hframes = spec.hframes
	flash.flip_h = pick[1]
	flash.scale = Vector2.ONE * Layout.SCALE
	var first: int = pick[0] * spec.frames_per_heading
	flash.frame = first
	body.projectile_layer.add_child(flash)
	flash.global_position = at.round()
	intro_fx.append(flash)
	var play := flash.create_tween()
	for i in range(1, spec.frames_per_heading):
		play.tween_interval(spec.frame_time)
		play.tween_callback(flash.set_frame.bind(first + i))
	play.tween_interval(spec.frame_time)
	play.tween_callback(flash.queue_free)


# Through a sheet's frames once, then gone.
func _play_frames(sheet: Sprite2D, frame_time: float) -> void:
	var play := sheet.create_tween()
	for i in range(1, sheet.hframes):
		play.tween_interval(frame_time)
		play.tween_callback(sheet.set_frame.bind(i))
	play.tween_interval(frame_time)
	play.tween_callback(sheet.queue_free)


func _hold_pose(held: StringName) -> void:
	if _intro_is_live():
		body.sprite.flip_h = false
		body.show_talk(held, false)


# Where every beat the lines could still call leaves him, all at once: idling at HOME, whole and
# unflipped, nothing of the shot left, and his theme on. Idempotent; a watched entrance comes through here
# as the fight starts, a skip on its way to the card, and the fight started over the top of it too.
func _after_intro() -> void:
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


#ENDING IT

# The one way the walk-in ends: its last beat, a skip, or the fight being started over the top of it.
# Idempotent - it leaves the ring exactly as the lines expect it whichever of those got here.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	body.global_position = home
	body.show_body()
	body.show_talk(&"smug", false)
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


# What a held ui_cancel does: the walk-in, whatever is left of the lines and the shot, and the card's
# build-up, all at once, landing on the card's flash with the ring a watched entrance leaves.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	finish_entrance()
	BossEntrance.run_out(waits)
	_after_intro()
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


# The lines have handed over to the VS card, and the skip goes with them. His last line leaves him in a
# talk pose, so this is also where a watched entrance comes to the end state a skip lands on.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()
	_after_intro()


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue(self)


# The lines can be ended from outside - the defence suite frees the balloon and ends the dialogue by hand
# - which starts the fight under whichever beat is in flight, and a held skip ends them too. Every beat
# asks this before it touches him, so a beat that outlived the entrance leaves the fight alone.
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
