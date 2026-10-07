extends "res://Scripts/States/Jordan/JordanIntro.gd"

# Jordan's entrance on the kaiju (JordanKaijuLayout.USE_KAIJU; scratchpad jordan_kaiju/PLAN.md section 3), the standard
# BossEntrance pattern: he opens his gold collector box, tosses the toy kaiju to the left ropes, it grows giant and
# roars, and he leaps onto its head; then his two lines (the same ones) and the VS card. A retry starts him riding
# already. JordanStateMachine builds this in place of JordanIntro while the switch is on, so with it off his old
# intro, which has no walk-in and no finish_entrance(), is exactly what it was.
#
#   0.00  he idles at his spot holding the box, the skip hint up     2.00  it grows (1.20, the shake ramping up)
#   0.40  the box opens (0.60), the toy in his hands from 0.80        3.20  it roars (0.80)
#   1.00  the toss (0.30), the toy leaving his hand at 1.08           4.00  his backflip onto its seat (0.60)
#   1.85  the toy lands at the ropes (0.15)                           4.60  his cheer up there (0.50)
#   5.10  finish_entrance(): its walls up, the entrance seen, his lines
# The toy is in his hands on his box sheet's TOY anchors (TOY_HELD_SCALE of its size) and leaves from his toss sheet's
# HAND; with his stand-in sheets it isn't seen until it flies.
#
# Every wait is a node-bound tween in `waits` and every beat bails on `finished`, so a held skip (skip_to_fight) runs
# them all out and finish_entrance() leaves exactly the end state a watched run does.

const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const FIGHT_SCENE := "res://Scenes/Bosses/JordanBossFightScene.tscn"
# His hand with the toy in it, from his soles.
const TOY_HAND := Vector2(36, -150)
# His climb sheet's frames before its seat frames: the arc's length.
const CLIMB_ARC_TIME := 0.4

@export var open_at := 0.40
@export var open_time := 0.60
@export var toss_time := 0.30
# Into the box's opening, when the toy is in his hands (his box sheet's f4), and into the toss, its release (f1).
@export var toy_in_hands := 0.40
@export var toss_release := 0.08
@export var toy_flight := 0.77
@export var toy_apex := 180.0
@export var toy_land_time := 0.15
@export var grow_time := 1.20
@export var shake_from := 2.0
@export var shake_to := 10.0
@export var shake_beats := 6
@export var roar_time := 0.80
@export var climb_time := 0.60
@export var climb_arc := 160.0
@export var cheer_time := 0.50

var finished := false
var lines_started := false
var waits: Array[Tween] = []
# For a test: when each beat started, on the fight's clock.
var beat_times := {}
var holding := false


func Enter() -> void:
	if finished:
		return
	entered = true
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin()
	if BossEntrance.already_seen(FIGHT_SCENE):
		finish_entrance()
		_start_lines()
		return
	var kaiju: Node2D = state_machine.kaiju
	kaiju.visible = false
	kaiju.play_anim(&"toy")
	state_machine.set_mounted(false)
	body.global_position = KaijuLayout.JORDAN_START
	body.play_state_anim(&"idle")
	_play()


func Exit() -> void:
	finish_entrance()
	finished = true
	super()


func _play() -> void:
	var kaiju: Node2D = state_machine.kaiju
	await _beat(open_at)
	if finished:
		return
	_mark(&"box_open")
	body.play_anim(&"box_open")
	await _beat(toy_in_hands)
	if finished:
		return
	_hold_toy()
	await _beat(open_time - toy_in_hands)
	if finished:
		return
	_mark(&"toss")
	body.play_anim(&"toss", &"idle")
	await _beat(toss_release)
	if finished:
		return
	_mark(&"toy_flight")
	var hand := _toy_point()
	holding = false
	kaiju.visible = true
	if kaiju.current_anim != &"toy":
		kaiju.play_anim(&"toy")
	kaiju.z_index = 1
	kaiju.shadow_on = false
	var flight := create_tween()
	flight.tween_method(_step_toy.bind(hand, KaijuLayout.HOME, kaiju.art_scale), 0.0, 1.0, toy_flight)
	await _wait(flight)
	if finished:
		return
	kaiju.place(KaijuLayout.HOME)
	kaiju.set_lift(0.0)
	_toy_down()
	await _beat(toy_land_time)
	if finished:
		return
	_mark(&"grow")
	kaiju.play_anim(&"grow")
	get_tree().call_group("arena_crowd", "cheer", 1.0)
	var quake := create_tween()
	for i in shake_beats:
		var strength := lerpf(shake_from, shake_to, float(i) / maxf(shake_beats - 1, 1))
		quake.tween_callback(_shake.bind(strength))
		quake.tween_interval(grow_time / shake_beats)
	await _wait(quake)
	if finished:
		return
	_mark(&"roar")
	kaiju.play_anim(&"roar", &"idle")
	state_machine.play_sfx(&"roar")
	await _beat(roar_time)
	if finished:
		return
	_mark(&"climb")
	body.play_anim(&"climb")
	var from := body.to_global(JordanArtLayout.FLOOR_POINT)
	var climb := create_tween()
	climb.tween_method(_step_climb.bind(from), 0.0, 1.0, climb_time)
	await _wait(climb)
	if finished:
		return
	state_machine.set_mounted(true)
	_mark(&"cheer")
	body.play_anim(&"ride_taunt")
	await _beat(cheer_time)
	if finished:
		return
	finish_entrance()
	_start_lines()


func _step_toy(weight: float, from: Vector2, to: Vector2, from_scale: float) -> void:
	if finished:
		return
	var kaiju: Node2D = state_machine.kaiju
	kaiju.place(from.lerp(to, weight))
	kaiju.set_lift(4.0 * toy_apex * weight * (1.0 - weight))
	kaiju.art_scale = lerpf(from_scale, 1.0, weight)


# The toy in his hands, on his box sheet's TOY: drawn over him, small, with no shadow under it.
func _hold_toy() -> void:
	if body.anchor(&"toy") == null:
		return
	var kaiju: Node2D = state_machine.kaiju
	holding = true
	kaiju.visible = true
	kaiju.play_anim(&"toy")
	kaiju.art_scale = KaijuLayout.TOY_HELD_SCALE
	kaiju.z_index = 1
	kaiju.shadow_on = false
	kaiju.place(_toy_point())


# Where the toy is on him: his sheet's TOY, its release HAND, or his hand on a stand-in.
func _toy_point() -> Vector2:
	var at = body.anchor(&"toy")
	if at == null:
		at = body.anchor(&"hand")
	if at == null:
		return body.to_global(JordanArtLayout.FLOOR_POINT) + TOY_HAND
	return body.global_position + JordanArtLayout.frame_local(at)


func _toy_down() -> void:
	var kaiju: Node2D = state_machine.kaiju
	kaiju.art_scale = 1.0
	kaiju.z_index = 0
	kaiju.shadow_on = true


func _process(_delta: float) -> void:
	if holding and not finished:
		state_machine.kaiju.place(_toy_point())


func _step_climb(weight: float, from: Vector2) -> void:
	if finished:
		return
	var seat: Vector2 = state_machine.kaiju.seat_point()
	# His climb sheet: its hips on the arc from his soles, then its seat on the seat.
	if body.place_anchor(&"seat", seat) or body.place_on_arc(from, &"soles", 0, seat, &"seat", 4,
			weight * climb_time / CLIMB_ARC_TIME, climb_arc):
		state_machine.kaiju.update_hud_fade()
		return
	var soles: Vector2 = from.lerp(seat, weight) - Vector2(0, 4.0 * climb_arc * weight * (1.0 - weight))
	body.global_position = (soles - JordanArtLayout.FLOOR_POINT).round()
	state_machine.kaiju.update_hud_fade()


func _shake(strength: float) -> void:
	if finished:
		return
	ScreenView.shake(get_tree(), strength, 4, grow_time / shake_beats / 4.0)


func _mark(beat_name: StringName) -> void:
	beat_times[beat_name] = body.fight_clock


# The one way the entrance ends: its last beat, a skip, a retry, or the fight started over the top of it. Idempotent:
# the kaiju grown at home on its idle with its walls up, him riding it on his, the view level.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	holding = false
	var kaiju: Node2D = state_machine.kaiju
	_toy_down()
	kaiju.visible = true
	kaiju.place(KaijuLayout.HOME)
	kaiju.set_lift(0.0)
	kaiju.aim_head(0.0)
	kaiju.play_anim(&"idle")
	kaiju.set_walls(true)
	state_machine.set_mounted(true)
	body.state_anim = &"ride_idle"
	body.play_anim(&"ride_idle")
	kaiju.update_hud_fade()
	if is_instance_valid(entrance):
		entrance.release_player()
	BossEntrance.mark_seen(FIGHT_SCENE)


# The entrance cut on the spot and the lines started, as a retry does it: the defence suite's way past it.
func skip() -> void:
	if cut:
		return
	ScreenView.reset(get_tree())
	finish_entrance()
	_start_lines()


# The hold: whatever is left of the entrance, the lines and the card's build-up, all at once.
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


func _start_lines() -> void:
	if lines_started or cut:
		return
	lines_started = true
	state_machine.show_pre_fight_dialogue()


func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)
