extends State

# Eric's entrance, as named beats: it walks both fighters in first, then EricPreFight.dialogue calls
# the rest between its lines and waits for each one - the same shape as Liam's entrance
# (BixbyBeastIntro). The ring opens on his sword planted in the mat, the gates slam behind them, he
# says his line, hauls the sword out of the ground and levels it at the player for the second one.
# The VS card and the fight hang off dialogue_ended exactly as they did before.
#
# Every wait is a node-bound tween, so a pause stops the entrance where it is and a hit-stop carries
# it with the fight. Nothing here uses get_tree().create_timer() or a tree-level tween.
#
# A cut-short entrance never kills a tween something is waiting on: `finished` makes every beat bail
# and every stepping callback a no-op instead, so nothing is left half-drawn and nothing hangs. A
# held skip runs those waits out on the spot rather than letting them run their time
# (BossEntrance.run_out), so nothing of it surfaces again once the fight is on.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const EricEntranceLayout := preload("res://Scripts/EricEntranceLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/EricBossFightScene.tscn"
# The planted sword draws over both fighters; the ropes and the gates are above it at 1 and 2.
const PLANTED_Z_INDEX := 1
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const GATES_PATH := "Arena/Gates"

@export var animation_player: AnimationPlayer
@export var character_body: CharacterBody2D
@export var hurtbox: Area2D

@onready var state_machine = get_parent()

# The entrance layer: the hold on the player, their walk, and the skip and its hint through the lines.
var entrance: CanvasLayer
# His sword standing in the mat, until his own drawn one takes over on the grip frame.
var planted: Sprite2D
# Where the two of them end up, read off the scene so nothing here hardcodes a mark.
var home := Vector2.ZERO
var player_home := Vector2.ZERO
# The entrance is over, one way or another. Every beat checks it; finish_entrance() is the only
# thing that sets it.
var finished := false
var dialogue_started := false
# Enter() is deferred, so anything that can reach in from outside checks this first: there is no
# ring to set before it has run.
var entered := false
# A held skip took everything up to the VS card: the lines are gone, and a beat they would still
# have called does nothing.
var cut := false
# The tweens a beat is waiting on, for the skip to run out.
var waits: Array[Tween] = []
var point_loop: Tween
var sfx_players := {}
# What his body is drawn from in the fight, put back when the fight starts (Exit).
var fight_texture: Texture2D
var fight_hframes := 0
# Plants landed, so a test can see that every one of them fired.
var footfalls := 0


func Enter() -> void:
	entered = true
	home = character_body.global_position
	var player := _player()
	player_home = player.global_position if player != null else Vector2.ZERO
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	fight_texture = character_body.sprite.texture
	fight_hframes = character_body.sprite.hframes
	# The entrance drives his frames itself; an animation still running would fight it for them.
	animation_player.stop()
	_build_sfx()
	# On the retry path too: the walk-in is skipped there, but the lines still play and the hold
	# still skips them.
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin(player)
	if BossEntrance.already_seen(FIGHT_SCENE):
		_show_pose("arrive")
		finish_entrance()
		_start_dialogue()
		return
	# Both of them are put outside the ring here, in the frame the state is entered, rather than when
	# their own walk comes round: anywhere later and they are seen standing on their marks first and
	# sliding back out to the entrance.
	_show_pose("walk")
	character_body.global_position = home - Vector2(0, EricEntranceLayout.WALK_IN_RISE)
	if player != null:
		player.global_position = player_home + Vector2(0, EricEntranceLayout.PLAYER_WALK_DROP)
	_play()


# The fight starts here: his sheet goes back, the breathing loop stops and the view is level.
func Exit() -> void:
	_stop_point_loop()
	character_body.sprite.texture = fight_texture
	character_body.sprite.hframes = fight_hframes
	ScreenView.reset(get_tree())
	if is_instance_valid(entrance):
		entrance.queue_free()
	entrance = null


#THE WALK-IN

func _play() -> void:
	# His bar comes up with the gates, as Captain Burak's does: up from the start, it drew over him for the
	# first steps of his walk in from the top gate (playtest 2026-10-04).
	if character_body.hud_layer != null:
		character_body.hud_layer.hide()
	var gates := _gates()
	if gates != null:
		gates.open()
	planted = _plant_sword()
	await _beat(EricEntranceLayout.OPEN_BEAT)
	if finished:
		return

	# The player walks up into the ring, and stands looking at the sword.
	var player := _player()
	if player != null:
		get_tree().call_group("arena_crowd", "cheer", EricEntranceLayout.PLAYER_CHEER)
		await entrance.walk_player(player_home, EricEntranceLayout.PLAYER_WALK_TIME)
	if finished:
		return
	await _beat(EricEntranceLayout.PLAYER_BEAT)
	if finished:
		return

	get_tree().call_group("arena_crowd", "cheer", EricEntranceLayout.ERIC_CHEER)
	await _walk_eric_in()
	if finished:
		return

	if gates != null:
		await gates.close()
	if finished:
		return
	if character_body.hud_layer != null:
		character_body.hud_layer.show()
	await _beat(EricEntranceLayout.SETTLE_BEAT)
	if finished:
		return
	_start_dialogue()


# One heavy step at a time: he pushes forward, plants, and the plant jolts the ring.
func _walk_eric_in() -> void:
	var from := home - Vector2(0, EricEntranceLayout.WALK_IN_RISE)
	var steps: int = EricEntranceLayout.WALK_STEPS
	_show_pose("walk")
	var march := create_tween()
	for step in steps:
		var leg_from := from.lerp(home, float(step) / float(steps)).round()
		var leg_to := from.lerp(home, float(step + 1) / float(steps)).round()
		march.tween_method(_step_eric.bind(leg_from, leg_to, step), 0.0, 1.0, EricEntranceLayout.WALK_STEP_TIME)
		march.tween_callback(_footfall.bind(step))
		march.tween_interval(EricEntranceLayout.WALK_STEP_DWELL)
	await _wait(march)
	if finished:
		return
	character_body.global_position = home
	_show_pose("arrive")


# Whole pixels, so the pixel-art body doesn't shimmer as it walks. Each step plays half the walk
# cycle, so consecutive steps lead with opposite legs and the last frame of the half is the one the
# plant lands on. A two-frame stand-in takes the same path: half of it is one frame.
func _step_eric(weight: float, leg_from: Vector2, leg_to: Vector2, step: int) -> void:
	if finished:
		return
	character_body.global_position = leg_from.lerp(leg_to, weight).round()
	var frames: Array = EricEntranceLayout.pose("walk").frames
	var half := maxi(frames.size() / 2, 1)
	character_body.sprite.frame = frames[half * (step % 2) + mini(int(weight * half), half - 1)]


# The boot lands: he drops back onto the mat, and the ring takes it. Each plant is heavier than the
# one before it, so the last one before he reaches the blade is the one the player feels.
func _footfall(step: int) -> void:
	if finished:
		return
	footfalls += 1
	var plant: Array = EricEntranceLayout.footfall(step)
	_play_sfx("step", plant[1])
	ScreenView.shake(get_tree(), plant[0], EricEntranceLayout.WALK_STEP_SHAKE_STEPS,
		EricEntranceLayout.WALK_STEP_SHAKE_STEP_TIME)


#THE BEATS THE DIALOGUE CALLS

# He grips the hilt, heaves, tears the blade out of the mat and raises it. His theme starts on the
# pull, so it is already under the point, the card and his first attack.
func pull_sword() -> void:
	if finished:
		return
	_play_sfx("grip")
	_show_pose("grip")
	_hide_planted()
	await _beat(EricEntranceLayout.GRIP_HOLD)
	if finished:
		return

	_play_sfx("heave")
	get_tree().call_group("arena_crowd", "hush")
	var heave: Array = EricEntranceLayout.pose("heave").frames
	var strain := create_tween()
	var steps := maxi(roundi(EricEntranceLayout.HEAVE_TIME / EricEntranceLayout.HEAVE_FRAME_TIME), 1)
	for step in steps:
		strain.tween_callback(_show_frame.bind(heave[step % heave.size()]))
		strain.tween_interval(EricEntranceLayout.HEAVE_FRAME_TIME)
	await _wait(strain)
	if finished:
		return

	# The blade tears out: a dead stop, a hard upward jolt and a punch-in, all on the real clock so
	# the hit-stop holds the frame rather than crawling through the shake.
	_show_pose("pull")
	_play_sfx("pull")
	HitStop.freeze(get_tree(), EricEntranceLayout.PULL_HIT_STOP)
	ScreenView.shake(get_tree(), EricEntranceLayout.PULL_SHAKE, EricEntranceLayout.PULL_SHAKE_STEPS,
		EricEntranceLayout.PULL_SHAKE_STEP_TIME, Vector2.UP, true)
	ScreenView.zoom_to(get_tree(), EricEntranceLayout.PULL_ZOOM, home,
		EricEntranceLayout.PULL_ZOOM_TIME, true)
	get_tree().call_group("arena_crowd", "cheer", EricEntranceLayout.PULL_CHEER)
	_start_music()
	await _beat(EricEntranceLayout.PULL_HOLD)
	if finished:
		return
	_show_pose("raise")
	ScreenView.zoom_to(get_tree(), 1.0, home, EricEntranceLayout.PULL_ZOOM_OUT_TIME)
	await _beat(EricEntranceLayout.RAISE_HOLD)


# He levels the blade at the player and the view leans in on him: the shot the entrance is for. It
# runs even on the retry path - it is only a pose, a camera and the crowd, and the line under it
# still needs its beat. Not after a skip, which has already left him pointing.
func point_at_player() -> void:
	if cut:
		return
	_show_pose("point")
	_play_sfx("point")
	get_tree().call_group("arena_crowd", "cheer", EricEntranceLayout.POINT_CHEER)
	ScreenView.zoom_to(get_tree(), EricEntranceLayout.POINT_ZOOM,
		home - Vector2(0, EricEntranceLayout.POINT_FOCUS_RISE), EricEntranceLayout.POINT_ZOOM_TIME)
	_start_point_loop()
	await _beat(EricEntranceLayout.POINT_HOLD)
	finish_entrance()


# The lines have handed over to the VS card: the view levels off before the card takes the screen,
# and the skip goes with them.
func lines_over() -> void:
	ScreenView.zoom_to(get_tree(), 1.0, home, EricEntranceLayout.POINT_ZOOM_OUT_TIME)
	if is_instance_valid(entrance):
		entrance.end()


#ENDING IT

# The one way the entrance ends: its last beat, a skip, or the fight being decided over the top of
# it. Idempotent - it leaves the ring exactly as the fight expects it whichever of those got here.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	_stop_point_loop()
	character_body.global_position = home
	_show_pose("point")
	_hide_planted()
	if character_body.hud_layer != null:
		character_body.hud_layer.show()
	var gates := _gates()
	if gates != null:
		gates.shut_now()
	var player := _player()
	if player != null:
		player.global_position = player_home
	if is_instance_valid(entrance):
		entrance.release_player()
	_start_music()
	BossEntrance.mark_seen(FIGHT_SCENE)


# The entrance cut on the spot and the lines started: where a second go at the fight starts on its
# own. Public, so the defence suite can cut the entrance this way - its modes are about the fight,
# and read the lines or throw them away themselves.
func skip() -> void:
	if cut:
		return
	ScreenView.reset(get_tree())
	finish_entrance()
	_start_dialogue()


# What a held ui_cancel does: the entrance, whatever is left of the lines and the card's build-up,
# all at once, landing on the card's flash. finish_entrance() is where the pull and the point leave
# him - the sword out of the mat and levelled at the player, his theme playing - so the ring is the
# one a watched entrance leaves.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	finish_entrance()
	BossEntrance.run_out(waits)
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue(self)


#PIECES

# His sword standing in the mat where he will stop. Added the way EricDroppedSword adds its own and
# then taken straight back out of the hazard group, so _stop_everything() can't free it mid-entrance.
func _plant_sword() -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(EricEntranceLayout.PLANTED_SWORD)
	sprite.scale = character_body.scale
	sprite.offset = EricEntranceLayout.planted_offset(sprite.texture)
	# Over him, not under. Its ground contact is 5 texels behind his feet, so the y-sort would draw
	# it behind his body - and at hip height, 30 px inside his drawn edge, that hides the thing the
	# whole entrance is about. Fifteen px of depth is noise next to that. It goes away on the grip
	# frame anyway, where his own drawn sword takes over.
	sprite.z_index = PLANTED_Z_INDEX
	state_machine.add_hazard(sprite, home + EricEntranceLayout.plant_offset(), false)
	sprite.remove_from_group(state_machine.HAZARD_GROUP)
	return sprite


# From the grip frame on, the sword he is drawn holding is the one that was in the ground.
func _hide_planted() -> void:
	if is_instance_valid(planted):
		planted.queue_free()
	planted = null


# `key` names one of the entrance's poses; a pose drawn as several frames shows its first. The
# sheet comes with it: the drawn sheet is only partly finished, so which one a pose is on is the
# pose's own business, and the swap has to land with the frame or he is drawn on the wrong index.
func _show_pose(key: String) -> void:
	var pose: Dictionary = EricEntranceLayout.pose(key)
	character_body.sprite.texture = load(pose.texture)
	character_body.sprite.hframes = pose.hframes
	character_body.sprite.frame = pose.frames[0] if pose.frames is Array else pose.frames


# Queued by the heave and the point loop, so it checks the entrance is still running itself.
func _show_frame(index: int) -> void:
	if finished:
		return
	character_body.sprite.frame = index


# He breathes on the point while the line runs. Never awaited, so killing it is safe.
func _start_point_loop() -> void:
	var point: Array = EricEntranceLayout.pose("point").frames
	if point.size() < 2:
		return
	point_loop = create_tween().set_loops()
	for index in point:
		point_loop.tween_callback(_show_frame.bind(index))
		point_loop.tween_interval(EricEntranceLayout.POINT_FRAME_TIME)


func _stop_point_loop() -> void:
	if point_loop != null and point_loop.is_valid():
		point_loop.kill()
	point_loop = null


func _start_music() -> void:
	var boss = state_machine.boss
	if boss != null and boss.has_method("start_music"):
		boss.start_music()


# Built here rather than wired into the scene, the way EricScript builds its Break stings: the
# table in EricEntranceLayout is the only place they are named.
func _build_sfx() -> void:
	if not sfx_players.is_empty():
		return
	for key in EricEntranceLayout.ENTRANCE_SFX:
		var spec: Dictionary = EricEntranceLayout.ENTRANCE_SFX[key]
		var sfx := AudioStreamPlayer.new()
		sfx.stream = load(spec.stream)
		sfx.pitch_scale = spec.pitch
		sfx.volume_db = spec.volume_db
		add_child(sfx)
		sfx_players[key] = sfx


func _play_sfx(key: String, volume_db := INF) -> void:
	var sfx: AudioStreamPlayer = sfx_players.get(key)
	if sfx == null or sfx.stream == null:
		return
	if volume_db != INF:
		sfx.volume_db = volume_db
	sfx.play()


# Waits `seconds` on this node's own clock. A cut-short entrance lets it run out rather than killing
# it, and the caller's own `finished` check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _player() -> Node:
	return get_tree().current_scene.get_node_or_null(PLAYER_PATH)


func _gates() -> Node:
	return get_tree().current_scene.get_node_or_null(GATES_PATH)
