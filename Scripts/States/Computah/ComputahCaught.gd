extends State

# THE CATCH: his pounce landed, so he holds the player, slams them and puts them down.
#
#   0.00  the grab lands - lock_actions(), hit-stop, the crowd
#   0.30  the slam
#   0.55  unlock_actions(), then release_grab() for the toss and the i-frames, and straight back to
#         Idle with no punish window - the catch is the punishment.
#
# IT REACHES HERE ONLY FROM THE CHASE, which is not in the rotation yet (see ComputahChase).
#
# IT IS ONE STATE WITH ONE release() FUNNEL, CALLED FROM Exit() AND FROM _exit_tree(). A player left
# locked can never move again, which is the worst bug this fight can have, and a single idempotent
# funnel is the only way every failure path - a win, a loss, a finisher, a scene change - is provably
# safe. DO NOT SPLIT THIS INTO THREE STATES.
#
# The slam is unblockable by construction rather than by a new kind of lock: the player keeps the
# parry-only lock, and with nothing blockable or parryable there is nothing for the guard to answer.
# The player also keeps their own sprite - grab() is never called, which is why release_grab() below
# is called without one.
#
# FREEZE SAFETY: every beat is a Physics_Update accumulator. Nothing here may use
# get_tree().create_timer() or a tree-level create_tween().

const HitStop := preload("res://Scripts/HitStop.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/ComputahArtLayout.gd")

@export var fx_layer : Node2D
@export var catch_sfx_player : AudioStreamPlayer
@export var punch_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Set by ComputahChase before the transition.
var grabber: Node = null

# When he shakes them and puts them down, measured from the grab.
const SLAM_AT := 0.3
const SLAM_END := 0.55
const GRAB_HIT_STOP := 0.1
const FINISH_HIT_STOP := 0.18
const FINISH_SHAKE := 18.0
const FINISH_SHAKE_STEPS := 7
const SHAKE_STEP_TIME := 0.03
# Up and away from him, so the launch clears his reach.
const TOSS_LIFT := 0.7

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
var slammed := false
var hold_point := Vector2.ZERO


func Enter() -> void:
	released = false
	clock = 0.0
	slammed = false

	state_machine.lock_player()
	var player: Node2D = state_machine.get_player()
	hold_point = grabber.global_position if is_instance_valid(grabber) else Vector2.ZERO
	if player:
		hold_point = player.global_position
	if is_instance_valid(grabber):
		grabber.velocity = Vector2.ZERO
		grabber.set_grab_active(false)
		grabber.play_anim(&"grab_hold")
	HitStop.freeze(get_tree(), GRAB_HIT_STOP)
	get_tree().call_group("arena_crowd", "cheer", 1.2)
	catch_sfx_player.play()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent, and called from both Exit() and _exit_tree(). Every way out of this state runs through
# here, including the terminal ones that skip Exit() (ComputahStateMachine._end_fight).
func release() -> void:
	if released:
		return
	released = true
	if state_machine and is_instance_valid(state_machine):
		state_machine.unlock_player()
		state_machine.clear_player_facing()
		state_machine.note_release()
	if is_instance_valid(grabber):
		grabber.set_grab_active(false)
		grabber.show_battery(false)


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	_hold_player()
	if not slammed and clock >= SLAM_AT:
		slammed = true
		_slam()
	if clock >= SLAM_END:
		_let_go()


# He shakes them and puts them down.
func _slam() -> void:
	var player: Node2D = state_machine.get_player()
	if is_instance_valid(grabber):
		grabber.play_anim(&"toss", &"idle")
	if player:
		player.receive_hit(HitInfo.make(&"computah_slam", self, hold_point, grabber))
	# THE OTHER TWO THIRDS OF WHAT A CATCH COSTS. The damage is the catalog's; the stamina is spent
	# here, and the Break gauge drains through BossBreakGauge's own hit_loss off the same hit - which
	# is why there is no gauge call in this function. Two sources for one number is how they drift.
	state_machine.drain_player_stamina(state_machine.catch_stamina_drain)
	state_machine.note_catch()
	_burst(hold_point)
	punch_sfx_player.pitch_scale = 0.8
	punch_sfx_player.play()
	HitStop.freeze(get_tree(), FINISH_HIT_STOP)
	if is_instance_valid(grabber):
		grabber.shake_screen(FINISH_SHAKE, FINISH_SHAKE_STEPS, SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", 2.0)


# Kept where he holds them, so the burst lines up with the art. A locked player's _physics_process
# returns before anything moves them, so writing the position here is what carries.
func _hold_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	player.global_position = hold_point.round()
	player.velocity = Vector2.ZERO


# The player is freed first and only then tossed: release_grab() is called without a preceding
# grab(), which looks odd but is deliberate. It is the only existing way to hand back the post-grab
# i-frames and the launch, and calling it unpaired is harmless - is_grabbed is already false and the
# sprite is already shown, since this fight never took either away.
func _let_go() -> void:
	var away := Vector2(-1.0 if (is_instance_valid(grabber) and grabber.facing_left) else 1.0, -TOSS_LIFT)
	release()
	state_machine.release_player(away)
	# Straight back to the beat: the catch was the punishment, so it opens no window.
	state_machine.on_child_transition(self, "Idle")


func _burst(at: Vector2) -> void:
	if Layout.USE_FINAL_COMBO_IMPACT:
		return
	var spec := Layout.PLACEHOLDER_COMBO_IMPACT
	var burst := Polygon2D.new()
	burst.polygon = Layout.star(spec.points, spec.radius, spec.inner_ratio)
	burst.color = spec.finish_color
	burst.scale = Vector2.ONE * spec.from_scale
	burst.material = Layout.additive()
	fx_layer.add_child(burst)
	burst.global_position = at.round()
	var play := burst.create_tween()
	play.tween_property(burst, "scale", Vector2.ONE * float(spec.finish_scale), spec.finish_time)
	play.parallel().tween_property(burst, "modulate:a", 0.0, spec.finish_time)
	play.tween_callback(burst.queue_free)
