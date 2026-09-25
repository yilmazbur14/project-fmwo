extends Node

# A boss's Break gauge. Reading his fight fills it: parries, perfect dodges, punches that land and
# anything of his own the player turns around. Being hit and having the guard broken drain it. Full, it
# breaks him (his fight script, then his state machine's Break), which is the daze the player's
# finisher needs. It never decays. After a Break it empties and takes nothing until unlock_delay after
# the finisher that followed has ended, or after he got up again if none came.
# It listens only to signals the player already has, and counts only the attacks its fight owns: the
# fight sets owns_attack (and earns_from, where fewer of his attacks fill it than drain it),
# strong_parry_ids and its own numbers before the gauge is added. Every fight with a Break has one. The
# defaults below are the ones Eric (EricScript, EricPacing V2) was tuned on; the others set theirs from
# a BREAK table on their body, most of them on one rule: N clean reads from empty is a Break.

signal changed(value: float, max_value: float)
signal broke
signal locked_changed(locked: bool)

# "N reads" makes a read max_value / N, and N of those can sum to a hair under max_value in floating
# point: twelve twelfths make 99.99999999999999. This is the gauge's one tolerance for that, so a fight
# gives max_value / N as it is and never rounds its gains to make the fraction land.
const BREAK_EPSILON := 1e-4

# Which attack ids are this boss's, answered by the fight itself: a prefix test where his ids are
# regular, a list where they aren't. Hits and guard breaks from these drain the gauge.
var owns_attack: Callable
# Which parries and perfect dodges fill it: func(hit: RefCounted) -> bool, handed the whole HitInfo so a
# fight can pay once per bolt or per breath. Unset, owns_attack on the hit's id. Nothing is deduplicated
# here: which hits are the same read is the fight's call.
var earns_from: Callable
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

# Both set by the fight before the gauge is added.
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
	if value >= max_value - BREAK_EPSILON:
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


func _earns(hit: RefCounted) -> bool:
	if earns_from.is_null():
		return _is_own(hit)
	return earns_from.call(hit)


func _on_parried(hit: RefCounted, _contact_point: Vector2, _staggered: bool, _streak: int) -> void:
	if _earns(hit):
		add(grab_parry_gain if hit.attack_id in strong_parry_ids else parry_gain)


func _on_perfect_dodged(hit: RefCounted) -> void:
	if _earns(hit):
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
