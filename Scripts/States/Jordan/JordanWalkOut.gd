extends State

# Jordan's walk-out, the start of his finale (the walk_out title of JordanFinale.dialogue). He has lost and won't have
# it: FightOutro hands him the won outro (JordanScript.take_won_outro), and this plays in place of the lines and the
# Victory screen. The KO plays out first - the defeat, the fanfare, the cheer, a juggle kill's crash - then a
# BossEntrance for the hold on the player and the skip hint. He gets up and storms off out through the top gate, his
# line typing as he goes, the crowd boos him out, and the player follows him through it on rails as the screen fades
# into his room (JordanFinaleScene).
#
# The same pieces as GreysonTakeover: every wait a node-bound tween in `waits`, every beat bailing on `cut`, and the
# lines calling the beats (storms_off, gone). A held skip closes the balloon, runs the waits out and fades to the TO
# BE CONTINUED card, the finale's own last beat, so a skipped run ends where a watched one does. It is terminal, as
# Defeated is: JordanStateMachine.enter_walk_out() is the only way in, and nothing leaves it. JordanStateMachine
# builds it, as it builds his intro: it needs nothing the scene would have to wire.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const JordanFinaleLayout := preload("res://Scripts/JordanFinaleLayout.gd")
const JordanGodLayout := preload("res://Scripts/JordanGodLayout.gd")

const FINALE_DIALOGUE := "res://Dialogue/JordanFinale.dialogue"
const ROOM_SCENE := "res://Scenes/Core/JordanFinaleScene.tscn"
const CARD_SCENE := "res://Scenes/Core/ToBeContinuedScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const GATES_PATH := "Arena/Gates"

#THE WALK-OUT (seconds; px in the arena's screen space)
const GETUP_TIME := 0.5
# His body's origin walks from where he knelt out through the top gate and off the screen.
const WALK_TO := Vector2(960, -110)
const WALK_SPEED := 200.0
# A player standing in his way out - in this lane of x, anywhere above his soles - is walked this far aside first.
const LANE := Vector2(840, 1080)
const ASIDE := 160.0
const BOO_TIME := 2.0
const HUD_FADE := 0.4
# The player after him, at their own walking pace: to the gate, then out through it as the screen fades.
const FOLLOW_TO := Vector2(960, 230)
const EXIT_TO := Vector2(960, -90)
# A held skip's fade to the card.
const SKIP_FADE := 0.5

var body: CharacterBody2D

@onready var state_machine = get_parent()

# begin() has handed him the won outro.
var begun := false
# Enter() has run: the walk-out is under way.
var entered := false
# A held skip took whatever was left of it.
var cut := false
var outro: Node
# The hold on the player and the skip hint, up from the hand-over to the scene change.
var entrance: CanvasLayer
var balloon: Node
var waits: Array[Tween] = []
var walk: Tween
var waiting_ko := false
var ko_left := 0.0
var clock := 0.0
# Beats seen through to their end, for a test: name -> game seconds it took.
var beat_times := {}


# FightOutro's won outro, handed over (JordanStateMachine.begin_walk_out): the walk-out takes him `line_delay` - the
# outro's own wait before its first line - after the KO is over, so a juggle kill has him land and lie there a beat
# before he gets up.
func begin(fight_outro: Node, line_delay: float) -> void:
	if begun:
		return
	begun = true
	outro = fight_outro
	ko_left = line_delay
	waiting_ko = true


func _physics_process(delta: float) -> void:
	clock += delta
	if not waiting_ko:
		return
	if not _ko_over():
		return
	ko_left -= delta
	if ko_left <= 0.0:
		waiting_ko = false
		state_machine.enter_walk_out()


# The finisher that beat him has played out, and a juggle kill has crashed.
func _ko_over() -> bool:
	var player := _player()
	if player != null and player.finisher.is_active():
		return false
	return not body.is_juggled()


func Enter() -> void:
	if entered or not begun:
		return
	entered = true
	BossEntrance.settle_arena(get_tree())
	entrance = BossEntrance.new()
	entrance.name = "WalkOutCut"
	add_child(entrance)
	entrance.skipped.connect(skip)
	entrance.begin(_player())
	GameProgress.record_victory()
	# His last phase loads on threads from here, for a skip straight to it and for his room's own cut into it.
	if JordanFinaleLayout.after_finale_scene() == JordanFinaleLayout.GOD_FIGHT_SCENE:
		JordanGodLayout.prefetch()
	_fade_hud()
	DialogueManager.dialogue_ended.connect(_on_lines_ended, CONNECT_ONE_SHOT)
	balloon = DialogueManager.show_dialogue_balloon(load(FINALE_DIALOGUE), "walk_out", [self])
	balloon.input_lock_time = FightOutro.LINE_INPUT_LOCK


#THE BEATS THE DIALOGUE CALLS

# Up off the floor and away for the top gate. Back once he is walking, so his line types as he goes.
func storms_off() -> void:
	if not _live():
		return
	var started := clock
	# A juggle kill left him lying on its own loop.
	var juggled = state_machine.states.get("Juggled")
	if juggled != null:
		juggled.stop_lingering()
	body.play_anim(&"getup")
	await _beat(GETUP_TIME)
	if not _live():
		return
	await _clear_his_way()
	if not _live():
		return
	var gates := _gates()
	if gates != null:
		gates.open()
	var from: Vector2 = body.global_position
	body.play_anim(&"walk_away")
	walk = create_tween()
	walk.tween_method(_step_walk.bind(from, WALK_TO), 0.0, 1.0, maxf(from.distance_to(WALK_TO) / WALK_SPEED, 0.01))
	waits.append(walk)
	beat_times[&"storms_off"] = clock - started


# Out through the gate and off the screen, and the crowd boos him out.
func gone() -> void:
	if not _live():
		return
	var started := clock
	if walk != null and walk.is_valid() and walk.is_running():
		await walk.finished
		if not _live():
			return
	waits.erase(walk)
	body.global_position = WALK_TO
	get_tree().call_group("arena_crowd", "boo", BOO_TIME)
	beat_times[&"gone"] = clock - started


# His line is dismissed: the player goes after him, to the gate and out through it as the screen fades into his room.
func _on_lines_ended(_resource = null) -> void:
	if cut:
		return
	var started := clock
	var player := _player()
	if player != null:
		await entrance.walk_player(FOLLOW_TO, player.global_position.distance_to(FOLLOW_TO) / PlayerScript.SPEED)
		if cut:
			return
	outro.leave_to(ROOM_SCENE if ResourceLoader.exists(ROOM_SCENE) else CARD_SCENE)
	beat_times[&"follow"] = clock - started
	if player != null and is_instance_valid(player):
		entrance.walk_player(EXIT_TO, FOLLOW_TO.distance_to(EXIT_TO) / PlayerScript.SPEED)


# A player in his lane, anywhere above his soles, is walked aside so he can get past.
func _clear_his_way() -> void:
	var player := _player()
	if player == null:
		return
	var at: Vector2 = player.global_position
	var soles: float = body.global_position.y + JordanArtLayout.FLOOR_POINT.y
	if at.x < LANE.x or at.x > LANE.y or at.y >= soles:
		return
	var to := Vector2(at.x - ASIDE if at.x < WALK_TO.x else at.x + ASIDE, at.y)
	await entrance.walk_player(to, ASIDE / PlayerScript.SPEED)


#ENDING IT

# What a held ui_cancel does: whatever is left of the walk-out, gone at once, and a quick fade to the card (or to his
# last phase, once it is switched on: JordanFinaleLayout.after_finale_scene).
func skip() -> void:
	if cut or not entered:
		return
	cut = true
	if DialogueManager.dialogue_ended.is_connected(_on_lines_ended):
		DialogueManager.dialogue_ended.disconnect(_on_lines_ended)
	BossEntrance.close_balloon(balloon)
	BossEntrance.run_out(waits)
	outro.leave_to(JordanFinaleLayout.after_finale_scene(), SKIP_FADE)


# Every beat asks this before it touches anything, so one that outlived a skip leaves it alone.
func _live() -> bool:
	return entered and not cut and is_instance_valid(body)


#PIECES

func _fade_hud() -> void:
	if body.hud_layer == null:
		return
	for part in body.hud_layer.get_children():
		if part is CanvasItem:
			part.create_tween().tween_property(part, "modulate:a", 0.0, HUD_FADE)


# Waits `seconds` on this node's own clock. A skip lets it run out rather than killing it, and the caller's own check
# is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


# Whole pixels, so the pixel-art body doesn't shimmer as he walks.
func _step_walk(weight: float, from: Vector2, to: Vector2) -> void:
	if is_instance_valid(body):
		body.global_position = from.lerp(to, weight).round()


func _gates() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(GATES_PATH) if scene else null


func _player() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(PLAYER_PATH) if scene else null
