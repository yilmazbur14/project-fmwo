extends Node

# Eric's Break gauge (EricPacing V2). Reading his fight fills it: parries, perfect dodges, punches that
# land and his own sword flung back into him. Being hit and having the guard broken drain it. Full, it
# breaks him (BossOneScript, then EricStateMachine.enter_broken), which is the daze the player's
# finisher needs. It never decays. After a Break it empties and takes nothing until unlock_delay after
# the finisher that followed has ended, or after he got up again if none came.
# It listens only to signals the player already has, and counts only Eric's own attacks.

signal changed(value: float, max_value: float)
signal broke
signal locked_changed(locked: bool)

const ATTACK_PREFIX := "eric_"
# The one parry that staggers him on the spot.
const RED_GRAB := &"eric_bear_hug_grab_v2"

@export var max_value := 100.0
@export var parry_gain := 15.0
@export var grab_parry_gain := 20.0
# His own sword reaching him after a parry flung it back (EricSwordThrow).
@export var reflect_gain := 35.0
@export var perfect_dodge_gain := 12.0
@export var punch_gain := 8.0
# Instead of punch_gain, not on top of it.
@export var charged_punch_gain := 14.0
@export var hit_loss := 20.0
@export var guard_break_loss := 35.0
# Game seconds.
@export var unlock_delay := 3.0

# Both set by BossOneScript before the gauge is added.
var boss: Node
var player: Node

var value := 0.0
var locked := false
var unlock_left := 0.0


func _ready() -> void:
	var defense: Node = player.get_node("Defense")
	defense.parried.connect(_on_parried)
	defense.perfect_dodged.connect(_on_perfect_dodged)
	defense.hit_taken.connect(_on_hit_taken)
	defense.guard_broken.connect(_on_guard_broken)
	player.get_node("Combo").punch_landed.connect(_on_punch_landed)


# The wait only starts once he is up again and no finisher is running.
func _physics_process(delta: float) -> void:
	if not locked:
		return
	if boss.is_down() or player.finisher.is_active():
		unlock_left = unlock_delay
		return
	unlock_left -= delta
	if unlock_left <= 0.0:
		locked = false
		locked_changed.emit(false)


# Returns whether this filled the gauge and broke him. Nothing moves it once he is beaten: the punch
# that kills him must not shatter it over his defeat.
func add(amount: float) -> bool:
	if amount == 0.0 or (amount > 0.0 and locked) or boss.defeated or boss.boss_health <= 0:
		return false
	var before := value
	value = clampf(value + amount, 0.0, max_value)
	if value == before:
		return false
	if value >= max_value:
		_break()
		return true
	changed.emit(value, max_value)
	return false


func _break() -> void:
	value = 0.0
	locked = true
	unlock_left = unlock_delay
	changed.emit(value, max_value)
	locked_changed.emit(true)
	broke.emit()


func _is_eric(hit: RefCounted) -> bool:
	return str(hit.attack_id).begins_with(ATTACK_PREFIX)


func _on_parried(hit: RefCounted, _contact_point: Vector2, _staggered: bool, _streak: int) -> void:
	if _is_eric(hit):
		add(grab_parry_gain if hit.attack_id == RED_GRAB else parry_gain)


func _on_perfect_dodged(hit: RefCounted) -> void:
	if _is_eric(hit):
		add(perfect_dodge_gain)


# A grab's squeezes cost nothing more, the way they cost no hype: the grab itself was the hit.
func _on_hit_taken(hit: RefCounted) -> void:
	if _is_eric(hit) and hit.hype_loss:
		add(-hit_loss)


func _on_guard_broken() -> void:
	add(-guard_break_loss)


func _on_punch_landed(target: Node, dealt: int, charged: bool) -> void:
	if target == boss and dealt > 0:
		add(charged_punch_gain if charged else punch_gain)
