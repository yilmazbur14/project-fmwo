extends Node

# Every punch that lands adds one to the combo, and the last punch of a full combo is charged: the POW,
# which opens the finisher's mash on a boss that can be dazed then (PlayerFinisher). There is no beat to
# it (the user, 2026-09-30: "just have it so the user has to hit the boss 3 times for the uppercut mash to
# appear"): a mashed press and a slow one land the same, and the count carries through whiffs, refused
# punches and gaps, but only for COMBO_RESET_TIME after the last punch that landed. It starts again then,
# on the POW, as the finisher starts, when a punch lands on a different target from the last one that
# landed (counting as that target's first), on Matt's scream (MattRecover), and with each fight's new
# player. A hit taken, a guard break and an action lock keep it too, unless keep_count_when_hit is off.
# A boss whose hurtbox a punch reaches passes it to resolve_punch(), which asks the boss to
# take_punch() and counts the damage the boss reports back. With the player's feel_v2 the punch
# resolves itself on contact instead (PlayerPunching), so no swing waits on a report.
signal combo_changed(count: int, charged: bool)
# A charged punch dealt damage to `target`. Emitted inside the physics flush that reported the hit.
signal charged_hit_landed(target: Node)
# Any punch that dealt damage.
signal punch_landed(target: Node, dealt: int, charged: bool)
# A punch that reached a boss and dealt nothing: he isn't open, or this opening's allowance is spent
# (PunchAllowance). PlayerCombatFx answers it with a dull deflect, so it is never silent.
signal punch_refused(target: Node)
# A swing over with nothing reached: no boss took it or refused it. The count carries on through it.
signal punch_missed

const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")

# PunchAllowance's, which every boss's per-opening allowance is worked out from.
@export var hits_to_charge := PunchAllowance.HITS_TO_CHARGE
@export var charged_damage := PunchAllowance.CHARGED_DAMAGE
@export var charged_hit_stop := 0.1
@export var shake_strength := 10.0
# Whether the count lives through a hit taken, a guard break and an action lock (reset_unless_kept). Off,
# each of them starts it again, the way a hit broke a combo while it still had timing.
@export var keep_count_when_hit := true

# How long the count lives without a punch landing, in the same game time as `clock`: a pause stops it and
# a hit-stop all but stops it. Swings that miss or are refused don't keep it alive. The user, 2026-10-04:
# "make sure the combo resets after like a second of not hitting", because a count carried out of one
# opening made the next one's first punch a POW that came too late to daze him.
const COMBO_RESET_TIME := 1.0

const CHARGED_FLASH := Color(3.0, 2.4, 0.9)
const CHARGED_FLASH_TIME := 0.35
const SHAKE_STEPS := 6
const SHAKE_STEP_TIME := 0.03

# A hurtbox reports a punch at the start of the second physics frame after the hitbox switches
# off: one step for the physics server to see the change, then the flush that reports it.
const REPORT_FRAMES := 2

var count := 0
# Game time, so hit-stop doesn't count toward PlayerPunching's quick chain, which is measured on it.
var clock := 0.0
# What the last punch to land landed on, by instance id: one landing on anything else starts the count
# again.
var last_target_id := 0
# Game time since the last punch landed, counted while there is a count to lose.
var since_landed := 0.0

# A swing stays open until the boss reports it or it's known to have missed.
var swing_open := false
# -1 while a swing is in progress.
var swing_end_frame := -1

@onready var player: CharacterBody2D = get_parent()


func _physics_process(delta: float) -> void:
	clock += delta
	if count > 0:
		since_landed += delta
		if since_landed >= COMBO_RESET_TIME:
			reset()
	if swing_open and swing_end_frame >= 0 and Engine.get_physics_frames() - swing_end_frame >= REPORT_FRAMES:
		swing_open = false
		punch_missed.emit()


# Starting a punch before the last one's report is in would cancel the report: the hitbox would
# switch back on before the physics server saw it switch off. A feel_v2 punch has no report to wait on.
func report_pending() -> bool:
	if player.feel_v2:
		return false
	return swing_end_frame >= 0 and Engine.get_physics_frames() - swing_end_frame < REPORT_FRAMES


func start_swing() -> void:
	swing_open = true
	swing_end_frame = -1


# The place in the combo the swing just started takes if it lands on the last punch's target: 0 for a
# combo's first punch, hits_to_charge - 1 for its charged one. PlayerPunching draws the swing by it.
func swing_position() -> int:
	return count


func end_swing() -> void:
	swing_end_frame = Engine.get_physics_frames()
	# A feel_v2 punch resolves on contact while the arm is out: one still open as it ends missed.
	if player.feel_v2 and swing_open:
		swing_open = false
		punch_missed.emit()


func reset() -> void:
	if count == 0:
		return
	count = 0
	combo_changed.emit(0, false)


# A hit taken, a guard break or an action lock: the count lives through all three unless
# keep_count_when_hit is off.
func reset_unless_kept() -> void:
	if not keep_count_when_hit:
		reset()


# Returns the damage the punch dealt. Only the first report of a swing counts: a hurtbox that
# starts monitoring mid-swing reports the punch again when the hitbox switches off. One that deals
# nothing leaves the count where it was.
func resolve_punch(target: Node) -> int:
	if not swing_open:
		return 0
	swing_open = false

	var place := count if target.get_instance_id() == last_target_id else 0
	var charged := place == hits_to_charge - 1
	var dealt: int = target.take_punch(charged_damage if charged else 1)
	if dealt <= 0:
		punch_refused.emit(target)
		return 0

	last_target_id = target.get_instance_id()
	since_landed = 0.0
	count = place + 1
	combo_changed.emit(count, charged)
	punch_landed.emit(target, dealt, charged)
	if charged:
		count = 0
		_charged_feedback(target.sprite)
		charged_hit_landed.emit(target)
	return dealt


# A punch on a boss outside his windows, whose hurtbox is switched off, so no take_punch() ever hears it
# (PlayerPunching): refused the same way.
func refuse_punch(target: Node) -> void:
	if not swing_open:
		return
	swing_open = false
	punch_refused.emit(target)


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
