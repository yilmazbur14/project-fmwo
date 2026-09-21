extends Node

# A boss's Break gauge. Reading his fight fills it: parries, perfect dodges, punches that land and
# anything of his own the player turns around. Being hit and having the guard broken drain it. Full, it
# breaks him (his fight script, then his state machine's Break), which is the daze the player's
# finisher needs. It never decays. After a Break it empties and takes nothing until unlock_delay after
# the finisher that followed has ended, or after he got up again if none came.
# It listens only to signals the player already has, and counts only the attacks its fight owns: the
# fight sets owns_attack and strong_parry_ids before the gauge is added. Eric's (BossOneScript,
# EricPacing V2) is the fight on it today, and the gains below are still the ones he was tuned on, so a
# second fight taking one wants its own.

signal changed(value: float, max_value: float)
signal broke
signal locked_changed(locked: bool)

# Which attack ids are this boss's, answered by the fight itself: a prefix test where his ids are
# regular, a list where they aren't.
var owns_attack: Callable
# The parries that stagger him on the spot, worth grab_parry_gain instead of parry_gain.
var strong_parry_ids: Array[StringName] = []

@export var max_value := 100.0
@export var parry_gain := 15.0
@export var grab_parry_gain := 20.0
# Something of his own reaching him after a parry flung it back (Eric's sword, EricSwordThrow).
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


func _is_own(hit: RefCounted) -> bool:
	return owns_attack.call(hit.attack_id)


func _on_parried(hit: RefCounted, _contact_point: Vector2, _staggered: bool, _streak: int) -> void:
	if _is_own(hit):
		add(grab_parry_gain if hit.attack_id in strong_parry_ids else parry_gain)


func _on_perfect_dodged(hit: RefCounted) -> void:
	if _is_own(hit):
		add(perfect_dodge_gain)


# A grab's squeezes cost nothing more, the way they cost no hype: the grab itself was the hit.
func _on_hit_taken(hit: RefCounted) -> void:
	if _is_own(hit) and hit.hype_loss:
		add(-hit_loss)


func _on_guard_broken() -> void:
	add(-guard_break_loss)


func _on_punch_landed(target: Node, dealt: int, charged: bool) -> void:
	if target == boss and dealt > 0:
		add(charged_punch_gain if charged else punch_gain)
