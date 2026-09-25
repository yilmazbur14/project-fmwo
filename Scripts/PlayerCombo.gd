extends Node

# Punches that land on the beat build a combo, and the last punch of a full combo is charged.
# After a landed hit the next press has to come inside a timing window that opens a beat after
# the swing ends; any press before it (mashing) or no press until it closes breaks the combo.
# A boss whose hurtbox a punch reaches passes it to resolve_punch(), which asks the boss to
# take_punch() and counts the damage the boss reports back. With the player's feel_v2 the punch
# resolves itself on contact instead (PlayerPunching), so no swing waits on a report.
signal combo_changed(count: int, charged: bool)
signal beat_window_changed(open: bool)
# A charged punch dealt damage to `target`. Emitted inside the physics flush that reported the hit.
signal charged_hit_landed(target: Node)
# Any punch that dealt damage.
signal punch_landed(target: Node, dealt: int, charged: bool)
# A punch that reached a boss and dealt nothing: he isn't open, or this opening's allowance is spent
# (PunchAllowance). PlayerCombatFx answers it with a dull deflect, so it is never silent.
signal punch_refused(target: Node)

const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const PlayerFeel := preload("res://Scripts/PlayerFeel.gd")
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")

# The beat window's offset and length are PlayerFeel's. A swing lasts 22 physics frames (0.37s) from
# the press to its hitbox switching off, so today's window runs 0.42s-0.77s after the press that
# started it, feel_v2's 0.41s-0.66s: any press rhythm faster than about 2.7 a second lands a press
# mid-swing.
# PunchAllowance's, which every boss's per-opening allowance is worked out from.
@export var hits_to_charge := PunchAllowance.HITS_TO_CHARGE
@export var charged_damage := PunchAllowance.CHARGED_DAMAGE
@export var charged_hit_stop := 0.1
@export var shake_strength := 10.0

const CHARGED_FLASH := Color(3.0, 2.4, 0.9)
const CHARGED_FLASH_TIME := 0.35
const SHAKE_STEPS := 6
const SHAKE_STEP_TIME := 0.03

# A hurtbox reports a punch at the start of the second physics frame after the hitbox switches
# off: one step for the physics server to see the change, then the flush that reports it.
const REPORT_FRAMES := 2

var count := 0
# Game time, so hit-stop doesn't count toward the window.
var clock := 0.0

# A swing stays open until the boss reports it or it's known to have missed.
var swing_open := false
# -1 while a swing is in progress.
var swing_end_frame := -1
var swing_end_time := 0.0
var swing_on_beat := false
var press_on_beat := false
# A press outside the window since the current swing started: the swing can't be followed on the beat.
var beat_missed := false
var window_open := false

@onready var player: CharacterBody2D = get_parent()


func _physics_process(delta: float) -> void:
	clock += delta
	if swing_open and swing_end_frame >= 0 and Engine.get_physics_frames() - swing_end_frame >= REPORT_FRAMES:
		swing_open = false
		reset()

	if count == 0 or beat_missed or swing_open or swing_end_frame < 0:
		_set_window(false)
		return
	var since_end := clock - swing_end_time
	var offset: float = PlayerFeel.value("combo_window_offset", player.feel_v2)
	if since_end > offset + PlayerFeel.value("combo_window_length", player.feel_v2):
		reset()
	else:
		_set_window(since_end >= offset)


# Called on every punch press, judged by when it was pressed, including presses mid-swing that
# don't start a punch and presses held back until the last swing's report is in.
func register_press() -> void:
	press_on_beat = window_open
	if window_open:
		_set_window(false)
		return
	beat_missed = true
	# A swing still waiting on its report breaks the combo once it lands instead.
	if not swing_open:
		reset()


# Starting a punch before the last one's report is in would cancel the report: the hitbox would
# switch back on before the physics server saw it switch off. A feel_v2 punch has no report to wait on.
func report_pending() -> bool:
	if player.feel_v2:
		return false
	return swing_end_frame >= 0 and Engine.get_physics_frames() - swing_end_frame < REPORT_FRAMES


func start_swing() -> void:
	swing_on_beat = press_on_beat
	press_on_beat = false
	beat_missed = false
	swing_open = true
	swing_end_frame = -1


func end_swing() -> void:
	swing_end_frame = Engine.get_physics_frames()
	swing_end_time = clock
	# A feel_v2 punch resolves on contact while the arm is out: one still open as it ends missed.
	if player.feel_v2 and swing_open:
		swing_open = false
		reset()


func reset() -> void:
	_set_window(false)
	if count == 0:
		return
	count = 0
	combo_changed.emit(0, false)


# Returns the damage the punch dealt. Only the first report of a swing counts: a hurtbox that
# starts monitoring mid-swing reports the punch again when the hitbox switches off.
func resolve_punch(target: Node) -> int:
	if not swing_open:
		return 0
	swing_open = false
	if not swing_on_beat:
		reset()

	var charged := count == hits_to_charge - 1
	var dealt: int = target.take_punch(charged_damage if charged else 1)
	if dealt <= 0:
		reset()
		punch_refused.emit(target)
		return 0

	count += 1
	combo_changed.emit(count, charged)
	punch_landed.emit(target, dealt, charged)
	if charged:
		count = 0
		_charged_feedback(target.sprite)
		charged_hit_landed.emit(target)
	elif beat_missed:
		reset()
	return dealt


# A punch on a boss outside his windows, whose hurtbox is switched off, so no take_punch() ever hears it
# (PlayerPunching): refused the same way.
func refuse_punch(target: Node) -> void:
	if not swing_open:
		return
	swing_open = false
	reset()
	punch_refused.emit(target)


func _set_window(open: bool) -> void:
	if open == window_open:
		return
	window_open = open
	beat_window_changed.emit(open)


func _charged_feedback(sprite: CanvasItem) -> void:
	HitStop.freeze(get_tree(), charged_hit_stop)

	# self_modulate stacks on the boss's own white flash, which tweens modulate. A SceneTree tween:
	# one bound to the boss would stop mid-glow if the hit dazes it and the fight freezes.
	sprite.self_modulate = CHARGED_FLASH
	get_tree().create_tween().tween_property(sprite, "self_modulate", Color(1, 1, 1), CHARGED_FLASH_TIME)

	_shake_screen()
	get_tree().call_group("arena_crowd", "cheer", 1.5)


# Offsets the canvas instead of moving nodes, so physics bodies and the UI layers stay put.
func _shake_screen() -> void:
	ScreenView.shake(get_tree(), shake_strength, SHAKE_STEPS, SHAKE_STEP_TIME)
