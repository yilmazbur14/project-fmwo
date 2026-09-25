extends State

# Danny's entrance (plan section 1). The ropes open and the player walks up into the ring, then the tiny
# training-room Danny ambles down through the top gate to HOME and the gates slam behind him.
# DannyBossPreFight.dialogue takes it from there, calls evolve() between its lines and waits for it: FireRed
# style, he grips his shirt, tears it off and flexes, the arena drains to dark, he flashes white between his
# two forms faster and faster behind a burst, the screen whites out, and he lands as the sumo, his theme
# starting on the landing. The VS card and the fight hang off dialogue_ended as they always have.
#
# While one of his lines is typing his sprite squashes in time with it (DannyBossScript.set_talking): there
# are no mouth frames, and it has to work on the small form as well as the sumo.
#
# THE HOLD SKIPS ALL OF IT (BossEntrance). Every wait is a node-bound tween in `waits`, every beat checks
# _intro_is_live() after each one - never `finished`, so the evolve replays on a retry, where the walk-in
# does not - and _after_intro() is the end state of every beat the lines could still call. A skip, a watched
# entrance and a fight started over the top of it all leave the same ring at the VS card's flash: the evolved
# sumo idling at HOME, unflipped, not white, on z 0, his hurtbox off, the HUD up, the gates shut, the player
# on their mark, the view level, the crowd at rest, his theme started exactly once, and nothing of the
# evolve left anywhere. None of it can hurt anyone: its dim, burst and dust are the entrance's own
# (intro_fx), never in the fight's hazard group.
#
# Nothing here uses get_tree().create_timer() or a tree-level tween, and his lines never use [wait=N] or
# "do wait(N)": both run on a SceneTree timer, which ticks through the pause screen and which a skip can't
# run out. THE STROBE: the approved flash comes down to 50 ms holds, then a 0.12 s full-screen white-out.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const VsCardArtLayout := preload("res://Scripts/VsCardArtLayout.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/DannyBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const GATES_PATH := "Arena/Gates"
# The name his lines go under.
const SPEAKER := "Danny"

#THE WALK-IN
# Both fighters are moved by written global_position, so nothing collides and nothing desyncs. He starts this
# far above his mark, off the top of the screen, and comes straight down through the top gate's doorway; the
# player rises from this far below theirs.
const WALK_IN_RISE := 700.0
const PLAYER_WALK_DROP := 260.0
const PLAYER_WALK_TIME := 1.6
const DANNY_WALK_TIME := 2.2

#BEATS, IN SECONDS
const OPEN_BEAT := 0.4
const PLAYER_BEAT := 0.4
# He arrives with both feet down, arms at his sides.
const ARRIVE_BEAT := 0.5
const SETTLE_BEAT := 0.4
const PLAYER_CHEER := 1.6
const DANNY_CHEER := 2.2

#THE EVOLVE (art_source/danny_sumo/transform.py's approved beat list, about 6.0 s)
# Grip, tear and flex are the small form's own animations; the tear shakes the view through its first two
# frames.
const TEAR_SHAKE := 2.0
const TEAR_SHAKE_STEPS := 6
const TEAR_SHAKE_STEP_TIME := 0.043
# The colour drains out of him as the arena drops away: his flat white and the dim, a step each.
const DRAIN_WHITE := [0.35, 0.70, 1.0]
const DRAIN_STEP := 0.11
# The dim is black over the whole arena, at this much of full black when fully down (the preview's 88%).
const DIM_ALPHA := 0.88
# The flash: evolve frames 0 (the small form) and 1 (the sumo), both flat white, the small form first,
# each held this long; the burst behind him grows to full from its first hold.
const FLASH_HOLDS := [0.34, 0.30, 0.26, 0.22, 0.18, 0.145, 0.115, 0.09, 0.07, 0.06, 0.055, 0.05, 0.05, 0.05]
const BURST_ALPHA_START := 0.25
const BURST_ALPHA_STEP := 0.09
# The burst's middle over his feet: 46 texels up, where the preview centres it.
const BURST_RISE := 138.0
const WHITE_OUT := 0.12
const LAND_TIME := 0.16
const LAND_SHAKE := 4.0
const LAND_SHAKE_STEPS := 4
const LAND_SHAKE_STEP_TIME := 0.04
# Over before the card's flash even on a quick read of his last line, so a watched entrance leaves the crowd at
# rest the way a skip's settle_arena() does.
const LAND_CHEER := 2.0
# A puff of his sumo dust off each foot as he lands, this far out from his feet.
const LAND_DUST_OUT := 150.0
const SETTLE_TIME := 0.40
const IDLE_TIME := 0.70
# On the fight's own projectile layer (z 2), under the HUD: the dim, then the burst over it, then him
# over both until he lands.
const DIM_Z := 20
const BURST_Z := 25
const FLASH_Z := 30

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
# A held skip took everything up to the VS card: the lines are gone, and a beat they would still have called
# does nothing.
var cut := false
# The tweens the walk-in and the beats are waiting on, for the skip to run out.
var waits: Array[Tween] = []
# The evolve is playing and owns his frames until the next line comes up.
var beat_running := false
# The evolve's dim, burst and dust: the entrance's own effects, never in the hazard group.
var intro_fx: Array[Node] = []
var dim: ColorRect
var burst: Polygon2D
# He has evolved: the lines called it, or a skip or the fight starting made it so.
var evolved := false
# Beats seen through to their end, for a test: name -> game seconds it took, and the landing's time on the
# fight's clock, which is when his theme starts.
var beat_times := {}
var evolve_started := -1.0
var landed_at := -1.0


func Enter() -> void:
	# Deferred, so the fight may already have been started over the top of this state (Exit).
	if finished:
		return
	entered = true
	home = state_machine.HOME
	var player := _player()
	player_home = player.global_position if player != null else Vector2.ZERO
	body.set_hurtbox_active(false)
	# On the retry path too: the walk-in is skipped there, but the lines and the evolve still play and the
	# hold still skips them.
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin(player)
	if BossEntrance.already_seen(FIGHT_SCENE):
		finish_entrance()
		_start_dialogue()
		return
	# Both of them are put outside the ring here, in the frame the state is entered, rather than when their
	# own walk comes round: anywhere later and they are seen standing on their marks first.
	body.play_anim(&"walk_small")
	body.global_position = home - Vector2(0, WALK_IN_RISE)
	if player != null:
		player.global_position = player_home + Vector2(0, PLAYER_WALK_DROP)
	_play()


# The fight starts here. A harness that starts it over the top of the entrance leaves through here too, so this
# is also what guarantees the ring is set however the entrance ended.
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

	get_tree().call_group("arena_crowd", "cheer", DANNY_CHEER)
	await _walk_danny_in()
	if finished:
		return

	body.play_anim(&"walk_hold")
	await _beat(ARRIVE_BEAT)
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


# The tiny helper ambling straight down to his mark.
func _walk_danny_in() -> void:
	var from := home - Vector2(0, WALK_IN_RISE)
	body.play_anim(&"walk_small")
	var walk := create_tween()
	walk.tween_method(_step_danny.bind(from, home), 0.0, 1.0, DANNY_WALK_TIME)
	await _wait(walk)
	if finished:
		return
	body.global_position = home


# Whole pixels, so the pixel-art body doesn't shimmer as it walks.
func _step_danny(weight: float, from: Vector2, to: Vector2) -> void:
	if finished:
		return
	body.global_position = from.lerp(to, weight).round()


#HIS LINES

func _read_lines() -> void:
	if cut or not entered or beat_running:
		return
	# Untyped: the balloon frees itself when the lines end, and a freed object can't be held in a typed
	# variable long enough to ask is_instance_valid about it.
	var balloon = state_machine.pre_fight_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line == null:
		return
	body.set_talking(line.character == SPEAKER and balloon.dialogue_label.is_typing)


#THE BEAT THE DIALOGUE CALLS

# The training room's Danny becomes the sumo. His theme starts as he lands. One tween runs every beat, each a
# callback and its hold: a tween carries the time a hold overran into the next, where awaiting a tween a beat
# would lose up to a frame at each of these 26 steps.
func evolve() -> void:
	if not _intro_is_live():
		return
	beat_running = true
	body.set_talking(false)
	evolve_started = _now()
	body.show_body()
	body.global_position = home
	var beats := create_tween()
	beats.tween_callback(_grip)
	beats.tween_interval(Layout.loop_length(Layout.anim(&"grip")))
	beats.tween_callback(_tear)
	beats.tween_interval(Layout.loop_length(Layout.anim(&"tear")))
	beats.tween_callback(_flex)
	beats.tween_interval(Layout.loop_length(Layout.anim(&"flex")))
	for i in DRAIN_WHITE.size():
		beats.tween_callback(_drain.bind(i))
		beats.tween_interval(DRAIN_STEP)
	for i in FLASH_HOLDS.size():
		beats.tween_callback(_flash.bind(i))
		beats.tween_interval(FLASH_HOLDS[i])
	beats.tween_callback(_white_out)
	beats.tween_interval(WHITE_OUT)
	beats.tween_callback(_land)
	beats.tween_interval(LAND_TIME)
	beats.tween_callback(_settle)
	beats.tween_interval(SETTLE_TIME)
	beats.tween_callback(_idle)
	beats.tween_interval(IDLE_TIME)
	await _wait(beats)
	if not _intro_is_live():
		return
	beat_running = false
	beat_times[&"evolve"] = _now() - evolve_started


# GRIP, TEAR, FLEX: the small form getting serious.
func _grip() -> void:
	if _intro_is_live():
		body.play_anim(&"grip")


func _tear() -> void:
	if _intro_is_live():
		body.play_anim(&"tear")
		ScreenView.shake(get_tree(), TEAR_SHAKE, TEAR_SHAKE_STEPS, TEAR_SHAKE_STEP_TIME)


func _flex() -> void:
	if _intro_is_live():
		body.play_anim(&"flex")


# DRAIN: the crowd goes quiet, his bar goes, the arena drops away and the colour drains out of him.
func _drain(step: int) -> void:
	if not _intro_is_live():
		return
	if step == 0:
		get_tree().call_group("arena_crowd", "hush")
		if body.hud_layer != null:
			body.hud_layer.hide()
		_build_dim()
		body.play_anim(&"evolve_small")
		body.sprite.z_index = FLASH_Z
	body.set_white(DRAIN_WHITE[step])
	dim.color = Color(0, 0, 0, DIM_ALPHA * float(step + 1) / float(DRAIN_WHITE.size()))


# FLASH: the two forms in flat white, faster and faster, the burst growing behind him.
func _flash(step: int) -> void:
	if not _intro_is_live():
		return
	if step == 0:
		_build_burst()
	body.play_anim(&"evolve_small" if step % 2 == 0 else &"evolve_awake")
	body.set_white(1.0)
	burst.color = Color(1, 1, 1, minf(1.0, BURST_ALPHA_START + BURST_ALPHA_STEP * step))


func _white_out() -> void:
	if _intro_is_live():
		dim.color = Color.WHITE


# LAND: the sumo, his colours back, the arena back, the view shaken, dust, a roar and his theme.
func _land() -> void:
	if not _intro_is_live():
		return
	_free_fx()
	body.show_body()
	body.play_anim(&"evolve_land")
	ScreenView.shake(get_tree(), LAND_SHAKE, LAND_SHAKE_STEPS, LAND_SHAKE_STEP_TIME)
	_land_dust()
	get_tree().call_group("arena_crowd", "cheer", LAND_CHEER)
	body.start_music()
	landed_at = _now()
	beat_times[&"land"] = landed_at - evolve_started
	if body.hud_layer != null:
		body.hud_layer.show()


# SETTLE, then IDLE, and the lines go on.
func _settle() -> void:
	if _intro_is_live():
		body.play_anim(&"evolve_awake")


func _idle() -> void:
	if not _intro_is_live():
		return
	evolved = true
	body.state_anim = &"idle"
	body.play_anim(&"idle")


# Black over the whole arena, on his projectile layer under the HUD, a little past the screen's edges so a
# shake never shows one.
func _build_dim() -> void:
	dim = ColorRect.new()
	dim.color = Color(0, 0, 0, 0)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	dim.z_index = DIM_Z
	var view: Vector2 = get_viewport().get_visible_rect().size
	dim.size = view + Vector2(80, 80)
	body.projectile_layer.add_child(dim)
	dim.global_position = Vector2(-40, -40)
	intro_fx.append(dim)


# The VS card's spiked star behind him, flat white.
func _build_burst() -> void:
	burst = Polygon2D.new()
	burst.polygon = VsCardArtLayout.burst_points()
	burst.color = Color(1, 1, 1, BURST_ALPHA_START)
	burst.z_index = BURST_Z
	body.projectile_layer.add_child(burst)
	burst.global_position = (home - Vector2(0, BURST_RISE)).round()
	intro_fx.append(burst)


# One puff of his sumo dust off each foot, played once. The sheet is drawn for a foot sliding left, so the
# right-hand one is flipped.
func _land_dust() -> void:
	var spec: Dictionary = Layout.fx(&"sumo_dust")
	for side in [-1.0, 1.0]:
		var dust := Sprite2D.new()
		dust.texture = load(spec.texture)
		dust.hframes = spec.hframes
		dust.vframes = spec.vframes
		dust.frame_coords = Vector2i(0, spec.danny_row)
		dust.flip_h = side > 0.0
		dust.offset = Layout.flipped_offset(spec.offset, dust.flip_h)
		dust.scale = Vector2.ONE * Layout.SCALE
		body.floor_layer.add_child(dust)
		dust.global_position = home + Vector2(side * LAND_DUST_OUT, 0)
		intro_fx.append(dust)
		var play := dust.create_tween()
		for i in range(1, spec.hframes):
			play.tween_interval(spec.frame_time)
			play.tween_callback(dust.set_frame_coords.bind(Vector2i(i, spec.danny_row)))
		play.tween_interval(spec.frame_time)
		play.tween_callback(dust.queue_free)


func _free_fx() -> void:
	for node in intro_fx:
		if is_instance_valid(node):
			node.queue_free()
	intro_fx.clear()
	dim = null
	burst = null


func _become_sumo() -> void:
	evolved = true
	body.show_body()
	body.global_position = home
	body.state_anim = &"idle"
	body.play_anim(&"idle")


# Where every beat the lines could still call leaves him, all at once: the evolved sumo idling at HOME, whole,
# unflipped, not white and on his own z, nothing of the evolve left, the HUD up, and his theme on.
# Idempotent; a watched entrance comes through here as the fight starts, a skip on its way to the card, and
# the fight started over the top of it too.
func _after_intro() -> void:
	beat_running = false
	_free_fx()
	if not is_instance_valid(body):
		return
	body.set_hurtbox_active(false)
	body.set_talking(false)
	if not evolved or body.current_anim != &"idle":
		_become_sumo()
	else:
		body.global_position = home
		body.show_body()
	if body.hud_layer != null:
		body.hud_layer.show()
	body.start_music()


#ENDING IT

# The one way the walk-in ends: its last beat, a skip, or the fight being started over the top of it.
# Idempotent - it leaves the ring exactly as the lines expect it whichever of those got here. Before the
# evolve he is still the small form.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	body.global_position = home
	body.show_body()
	if not evolved:
		body.state_anim = &"walk_hold"
		body.play_anim(&"walk_hold")
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
# Public, so the defence suite can cut the entrance this way - its modes are about the fight, and read the
# lines or throw them away themselves.
func skip() -> void:
	if cut:
		return
	ScreenView.reset(get_tree())
	finish_entrance()
	_start_dialogue()


# What a held ui_cancel does: the walk-in, whatever is left of the lines and the evolve, and the card's
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


# The lines have handed over to the VS card, and the skip goes with them. His last line leaves him mid-squash,
# so this is also where a watched entrance comes to the end state a skip lands on.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()
	_after_intro()


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue(self)


# The lines can be ended from outside - the defence suite frees the balloon and ends the dialogue by hand -
# which starts the fight under whichever beat is in flight, and a held skip ends them too. Every beat asks
# this before it touches him, so a beat that outlived the entrance leaves the fight alone.
func _intro_is_live() -> bool:
	return not cut and is_instance_valid(body) and state_machine.current_state == self


#PIECES

# Waits `seconds` on this node's own clock. A cut-short entrance lets it run out rather than killing it, and
# the caller's own check is what bails.
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
