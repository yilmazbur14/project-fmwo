extends State

# The punish window, and the only place punches reach him outside a Break (MattBroken): recover_time on
# RecoverTimer, three punches at most, and a charged one dazes him once (MattScript.can_be_dazed). It
# opens at HOME unless the attack before it left a recover_spot (the Glass Row: where he stands, over
# the player) and a bonus.
# Enter() needs nothing from the state before it, so a bare transition into it opens a working window.
#
# THE YELL is a sub-phase INSIDE it, decided once as the window opens: never in the fight's first
# window, then yell_chance. If it is on, it goes off the frame after landed punch 1 or 2 (even odds):
#   TELL   0.40 s  the yellow ring over his head, a sharp inhale. Punches still land and count, and
#                  flash him without flinching him.
#   BLAST  0.18 s  MattYellRingScript blown out from his mouth, 60 to 270 px, and the roar frames.
#   AFTER  0.35 s  the roar held.
# The window's timer is paused through all three and he can't be dazed in any of them. If it lands he
# is out of the window at once: the player is thrown across the ring and he starts again a second
# later (MattStateMachine.idle_after_yell). If it doesn't - dodged, or walked away from - the window
# gets yell_whiff_bonus back on top of what it had left, and its hit count starts again, so a whole
# combo into the daze is still there to be had.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const RING_SCENE := preload("res://Scenes/Bosses/MattYellRingScene.tscn")

const YELL_ID := &"matt_yell"
const YELL_SHAKE_STEPS := 6
const YELL_SHAKE_STEP_TIME := 0.03

@export var body : CharacterBody2D
@export var recover_timer : Timer

@onready var state_machine = get_parent()

enum Yell { NONE, TELL, BLAST, AFTER }

var yell := Yell.NONE
var yell_clock := 0.0
var yell_planned := false
# The landed punch it goes off after: 1 or 2.
var yell_on_hit := 0
# Due on the next physics step after the punch that triggers it. The punch resolves in the player's
# branch, which steps before his, so without the frame it would start on the same step.
var yell_due := false
var yell_due_frame := -1
var yell_result := HitInfo.Result.IGNORED
var ring: Node2D
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# Yells blown this window, for a test.
var yells := 0


func Enter() -> void:
	released = false
	body.global_position = state_machine.take_recover_spot()
	body.velocity = Vector2.ZERO
	body.show_body()
	body.hits_this_window = 0
	body.daze_used = false
	state_machine.windows_opened += 1
	yell = Yell.NONE
	yell_due = false
	yells = 0
	yell_result = HitInfo.Result.IGNORED
	_plan_yell()
	body.play_state_anim(&"recover")
	body.set_hurtbox_active(true)
	body.play_sfx(&"recover")
	recover_timer.paused = false
	recover_timer.start(state_machine.recover_time + state_machine.take_recover_bonus())


func Exit() -> void:
	release()


# Idempotent. The window's timer is never left paused, and nothing of the yell outlives it but a ring
# already blown, which is a hazard like any other.
func release() -> void:
	if released:
		return
	released = true
	yell = Yell.NONE
	yell_due = false
	recover_timer.paused = false
	recover_timer.stop()
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.set_hurtbox_active(false)
	if is_instance_valid(ring) and ring.answered.is_connected(_on_ring_answered):
		ring.answered.disconnect(_on_ring_answered)
	ring = null


func _plan_yell() -> void:
	var roll: float = state_machine.rng.randf()
	yell_planned = state_machine.windows_opened >= state_machine.yell_from_window and roll < state_machine.yell_chance
	var pick: int = state_machine.rng.randi_range(1, 2)
	yell_on_hit = pick if yell_planned else 0


func is_yelling() -> bool:
	return yell != Yell.NONE or yell_due


func on_punch_landed(count: int) -> void:
	if yell_planned and yell == Yell.NONE and yells == 0 and count == yell_on_hit:
		yell_due = true
		yell_due_frame = Engine.get_physics_frames()


func flinch() -> void:
	if not is_yelling():
		body.play_anim(&"hit", &"recover")


func Physics_Update(delta: float) -> void:
	if yell_due:
		if Engine.get_physics_frames() > yell_due_frame:
			yell_due = false
			_tell()
		return
	if yell == Yell.NONE:
		return
	yell_clock += delta
	match yell:
		Yell.TELL:
			if yell_clock >= state_machine.yell_tell:
				_blast()
		Yell.BLAST:
			if yell_clock >= state_machine.yell_expand_time:
				yell = Yell.AFTER
				yell_clock = 0.0
		Yell.AFTER:
			if yell_clock >= state_machine.yell_after:
				_missed()


func _tell() -> void:
	yell = Yell.TELL
	yell_clock = 0.0
	yells += 1
	recover_timer.paused = true
	body.play_anim(&"yell_tell")
	body.play_sfx(&"yell_tell")
	ParryTell.telegraph(body, YELL_ID, state_machine.yell_tell, _tell_anchor)


func _tell_anchor() -> Vector2:
	return body.tell_anchor(&"yell_tell")


func _blast() -> void:
	yell = Yell.BLAST
	yell_clock = 0.0
	ParryTell.clear(body)
	body.play_anim(&"roar")
	body.play_sfx(&"yell")
	ScreenView.shake(get_tree(), state_machine.yell_shake, YELL_SHAKE_STEPS, YELL_SHAKE_STEP_TIME)
	ring = RING_SCENE.instantiate()
	ring.player = state_machine.get_player()
	ring.start_radius = state_machine.yell_start_radius
	ring.end_radius = state_machine.yell_radius
	ring.band = state_machine.yell_band
	ring.expand_time = state_machine.yell_expand_time
	ring.landing_time = state_machine.yell_landing_time
	ring.answered.connect(_on_ring_answered)
	state_machine.add_hazard(ring, body.mouth_point(&"roar"), body.projectile_layer)


# The ring's one answer. A hit throws the player unless it killed them, and ends the window; a dodge is a
# miss like any other and waits for the after-pose.
func _on_ring_answered(result: int) -> void:
	yell_result = result
	if result != HitInfo.Result.HIT:
		return
	var player: Node2D = state_machine.get_player()
	if player != null and player.playerHealth > 0:
		body.launch_player(player, launch_point(player.global_position))
	state_machine.idle_after_yell()


# The far side of the ring on the player's side of his mouth, pushed on along the line they were
# thrown down, inside the ropes.
func launch_point(from: Vector2) -> Vector2:
	var mouth: Vector2 = body.mouth_point(&"roar")
	var x: float = state_machine.launch_left_x if from.x < mouth.x else state_machine.launch_right_x
	var y: float = from.y + state_machine.launch_follow * (from.y - mouth.y)
	return Vector2(x, clampf(y, state_machine.launch_y_range.x, state_machine.launch_y_range.y))


# Nothing landed: the window carries on with what it had left and the bonus, and its punches count
# again from nothing.
func _missed() -> void:
	yell = Yell.NONE
	yell_clock = 0.0
	if is_instance_valid(ring) and ring.answered.is_connected(_on_ring_answered):
		ring.answered.disconnect(_on_ring_answered)
	ring = null
	body.hits_this_window = 0
	var left := recover_timer.time_left
	recover_timer.paused = false
	recover_timer.start(left + state_machine.yell_whiff_bonus)
	body.play_state_anim(&"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Idle")
