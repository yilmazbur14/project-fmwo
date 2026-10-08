extends State

# Captain Burak's laugh cut: the fight's first volley of kegs landed all five blasts, and he can't hold it
# in. BurakBossBarrels owes it (state_machine.laugh_owed) and the state machine plays it once a fight,
# between that volley and the Taunt the volley opens. BurakBossLaugh.dialogue calls bursts_out_laughing()
# before its first line and waits for it; Danny heckles from ringside with his portrait only.
#
# A mid-fight cut on a BossEntrance - for the hold on the player and the skip hint - with MattIntro's
# skip: every wait is a node-bound tween in `waits`, so a pause holds the cut where it is, and a held skip
# closes the balloon, runs the waits out and ends it where its natural end would. Its tags are read off the
# live balloon as the intro's are: `captain` and `glance` pose him, and `deafened` rings Danny's ears for
# as long as that line is up - the ear ring, his portrait's frame jittering, and the music ducked.
#
# EVERY WAY OUT GOES THROUGH finish_cut(), which is idempotent: the lines' natural end, the hold, and the
# fight ending under it (BurakBossStateMachine._end_fight calls finish_cut(false)). It hands the player
# back, lays the ring flat and opens the Taunt. It never has a finish_entrance(): the defence suite finds a
# fight's entrance by that method.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
# The name his lines go under.
const SPEAKER := "Captain Burak"

#THE FIT (bursts_out_laughing)
const FIT_TIME := 1.40
const FIT_CHEER := 1.5
# A thump in the view on every knee slap: the laugh sheet's frames 1 and 3.
const SLAP_FRAMES := [1, 3]
const SLAP_SHAKE := 2.0
const SLAP_SHAKE_STEPS := 2
const SLAP_SHAKE_STEP_TIME := 0.03

#LEFT ALONE (the user, 2026-10-04)
# The one dialogue in the game that moves on by itself: a player who stands still through the kegs lands
# here, and the fight would otherwise wait on the cut for good. A line moves on AUTO_ADVANCE_TIME after it
# came up, and never sooner than AUTO_ADVANCE_READ after its last letter, so a long line still gets read.
# Accept still moves it on at once (the balloon's own input). Counted in Update, so a pause holds it.
const AUTO_ADVANCE_TIME := 4.5
const AUTO_ADVANCE_READ := 1.5

#DANNY, DEAFENED
const DEAF_DUCK_DB := -8.0
const DEAF_DUCK_TIME := 0.2
# His portrait's frame twitches, by rotation only.
const JITTER_DEGREES := 2.0
const JITTER_STEP := 0.05

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# The hold on the player and the skip hint, up for the whole cut.
var cut: CanvasLayer
# Enter() has run, so there is a cut to end.
var entered := false
# The cut is over, one way or another. finish_cut() is the only thing that sets it.
var finished := true
var waits: Array[Tween] = []
# The fit owns his frames until the next line comes up.
var beat_running := false
var pose := &"laugh"
var last_line: RefCounted
var last_slap_step := -1
# Danny's ringing ears: the line they are up for, the frame twitching, and the twitch itself.
var deaf_line: RefCounted
var jittered: Control
var jitter: Tween
var jitter_sign := 1.0
# Beats seen through to their end, for a test: name -> game seconds it took.
var beat_times := {}
# How long the current line has been up, and how long whole; the last line moved on by itself, and how
# many have been (a test reads it).
var line_clock := 0.0
var typed_clock := 0.0
var auto_advanced_line: RefCounted
var auto_advances := 0


func Enter() -> void:
	entered = true
	finished = false
	beat_running = false
	pose = &"laugh"
	last_line = null
	last_slap_step = -1
	auto_advanced_line = null
	auto_advances = 0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	cut = BossEntrance.new()
	cut.name = "LaughCut"
	add_child(cut)
	cut.skipped.connect(skip_cut)
	cut.begin(_player())
	state_machine.show_laugh_dialogue(self)


func Exit() -> void:
	finish_cut(false)


func Update(delta: float) -> void:
	if finished:
		return
	_read_lines()
	_slap()
	_auto_advance(delta)


#THE BEAT THE DIALOGUE CALLS

# Doubled over, slapping his knee, the crowd laughing along with him.
func bursts_out_laughing() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	body.sprite.flip_h = false
	body.play_anim(&"laugh")
	body.play_sfx(&"laugh")
	get_tree().call_group("arena_crowd", "cheer", FIT_CHEER)
	await _beat(FIT_TIME)
	if _cut_is_live():
		beat_times[&"bursts_out_laughing"] = body.fight_clock - started


func _slap() -> void:
	if not beat_running or body.current_anim != &"laugh" or body.anim_step == last_slap_step:
		return
	last_slap_step = body.anim_step
	if SLAP_FRAMES.has(body.anim_step):
		ScreenView.shake(get_tree(), SLAP_SHAKE, SLAP_SHAKE_STEPS, SLAP_SHAKE_STEP_TIME)


#THE LINES' TAGS

func _read_lines() -> void:
	# Untyped: the balloon frees itself when the lines end, and a freed object can't be held in a typed
	# variable long enough to ask is_instance_valid about it.
	var balloon = state_machine.laugh_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line == null:
		return
	if line != last_line:
		last_line = line
		line_clock = 0.0
		typed_clock = 0.0
		beat_running = false
		_stop_deafened()
		_apply_tags(line, balloon)
	if beat_running:
		return
	var talking: bool = line.character == SPEAKER and balloon.dialogue_label.is_typing
	body.show_talk(pose, talking)


# The balloon's own move-on, the one accept makes, once the line has been up long enough. Only on a line
# waiting for input with nothing to choose, and once a line.
func _auto_advance(delta: float) -> void:
	var balloon = state_machine.laugh_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line == null or line != last_line or line == auto_advanced_line:
		return
	line_clock += delta
	if not balloon.is_waiting_for_input:
		typed_clock = 0.0
		return
	typed_clock += delta
	if line.responses.is_empty() and line_clock >= AUTO_ADVANCE_TIME and typed_clock >= AUTO_ADVANCE_READ:
		auto_advanced_line = line
		auto_advances += 1
		balloon.next(line.next_id)


func _apply_tags(line: RefCounted, balloon: Node) -> void:
	if line.has_tag("captain"):
		pose = StringName(line.get_tag_value("captain"))
		body.sprite.flip_h = false
	if line.has_tag("glance"):
		# His sheets face screen-right unflipped, the way every flip in this game reads.
		body.sprite.flip_h = line.get_tag_value("glance") == "left"
	if line.has_tag("deafened"):
		_start_deafened(line, balloon)


# For as long as this line is up: the ring in his ears, his portrait twitching, the music ducked.
func _start_deafened(line: RefCounted, balloon: Node) -> void:
	deaf_line = line
	body.play_sfx(&"ear_ring")
	body.duck_music(DEAF_DUCK_DB, DEAF_DUCK_TIME)
	jittered = balloon.portrait_frame
	jittered.pivot_offset = jittered.size / 2.0
	jitter_sign = 1.0
	jitter = create_tween().set_loops()
	jitter.tween_callback(_twitch)
	jitter.tween_interval(JITTER_STEP)


func _twitch() -> void:
	if not is_instance_valid(jittered):
		return
	jittered.rotation = deg_to_rad(JITTER_DEGREES) * jitter_sign
	jitter_sign = -jitter_sign


func _stop_deafened() -> void:
	if deaf_line == null:
		return
	deaf_line = null
	if jitter != null and jitter.is_valid():
		jitter.kill()
	jitter = null
	if is_instance_valid(jittered):
		jittered.rotation = 0.0
	jittered = null
	if is_instance_valid(body):
		body.stop_sfx(&"ear_ring")
		body.duck_music(0.0, DEAF_DUCK_TIME)


#ENDING IT

# The one way the cut ends. Idempotent: the lines' natural end, a held skip and the fight ending under it
# all come through here, and leave the same ring. `route` is false when the fight ended under it.
func finish_cut(route := true) -> void:
	if finished or not entered:
		return
	finished = true
	beat_running = false
	if not route:
		# The fight ended under the cut: its lines go with it, before the outro's own come up.
		BossEntrance.close_balloon(state_machine.laugh_balloon)
		BossEntrance.run_out(waits)
		state_machine.end_laugh_dialogue()
	_stop_deafened()
	if is_instance_valid(body):
		body.stop_sfx(&"laugh")
	if is_instance_valid(cut):
		cut.end()
	cut = null
	var player := _player()
	if player != null:
		player.is_talking = false
	ScreenView.reset(get_tree())
	state_machine.laugh_played = true
	if route:
		state_machine.open_taunt()


# What a held ui_cancel does: the lines and whatever is left of the fit, all at once, landing where the
# lines' own end lands - the Taunt open and the player free.
func skip_cut() -> void:
	if finished or not entered:
		return
	BossEntrance.close_balloon(state_machine.laugh_balloon)
	BossEntrance.run_out(waits)
	state_machine.end_laugh_dialogue()
	finish_cut()


# Every beat asks this before it touches him, so one that outlived the cut leaves the fight alone.
func _cut_is_live() -> bool:
	return not finished and is_instance_valid(body) and state_machine.current_state == self


#PIECES

# Waits `seconds` on this node's own clock. A cut-short cut lets it run out rather than killing it, and the
# caller's own check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _player() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(PLAYER_PATH) if scene else null
