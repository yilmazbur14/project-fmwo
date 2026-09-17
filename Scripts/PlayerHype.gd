extends Node

# The crowd's hype. Landing punches and good defence fill it, taking hits empties it, and a full
# meter supercharges the next uppercut finisher (PlayerFinisher) while the crowd keeps cheering.
# It resets with every fight, since each fight builds a new player.
# In a fight with no boss a finisher can daze, Carter & Josh's, there's nothing to spend it on: hype
# is inert and HypeMeterUI hides itself.

signal hype_changed(value: float, max_value: float)
signal hype_full_changed(full: bool)
signal hype_spent

const FightOutro := preload("res://Scripts/FightOutro.gd")
const CROWD_GROUP := "arena_crowd"

@export var max_hype := 100.0
@export var punch_gain := 5.0
# Instead of punch_gain, not on top of it.
@export var charged_punch_gain := 12.0
# By parry streak tier: the first parry, the second, then the third and up.
@export var parry_gains: Array = [25.0, 30.0, 35.0]
@export var perfect_dodge_gain := 15.0
# A punched figure's blast catching Jordan.
@export var explosion_redirect_gain := 8.0
@export var hit_loss := 20.0
@export var guard_break_loss := 30.0
@export var decay_per_second := 0.0
@export var full_cheer := 2.5

@onready var player: CharacterBody2D = get_parent()

var hype := 0.0
var full := false
# -1 until a boss has joined the fight group, which happens after the player's _ready.
var spendable := -1


func _ready() -> void:
	var combo: Node = player.get_node("Combo")
	combo.punch_landed.connect(_on_punch_landed)
	var defense: Node = player.get_node("Defense")
	defense.parried.connect(_on_parried)
	defense.perfect_dodged.connect(_on_perfect_dodged)
	defense.hit_taken.connect(_on_hit_taken)
	defense.guard_broken.connect(_on_guard_broken)


func _process(delta: float) -> void:
	if decay_per_second > 0.0:
		add(-decay_per_second * delta)


func add(amount: float) -> void:
	if amount == 0.0 or is_inert():
		return
	_set_hype(clampf(hype + amount, 0.0, max_hype))


func drain(amount: float) -> void:
	add(-amount)


func is_full() -> bool:
	return full


func spend() -> void:
	if hype <= 0.0:
		return
	_set_hype(0.0)
	hype_spent.emit()


func reward_explosion_redirect() -> void:
	add(explosion_redirect_gain)


# Nothing carries over, and the hyped crowd goes quiet.
func on_fight_over() -> void:
	_set_hype(0.0)


func is_inert() -> bool:
	if spendable < 0:
		var bosses := get_tree().get_nodes_in_group(FightOutro.BOSS_GROUP)
		for boss in bosses:
			if boss.has_method("can_be_dazed"):
				spendable = 1
				break
		if spendable < 0 and not bosses.is_empty():
			spendable = 0
	return spendable == 0


func _on_punch_landed(_target: Node, _dealt: int, charged: bool) -> void:
	add(charged_punch_gain if charged else punch_gain)


func _on_parried(_hit: RefCounted, _contact_point: Vector2, _staggered: bool, streak: int) -> void:
	add(parry_gains[clampi(streak - 1, 0, parry_gains.size() - 1)])


func _on_perfect_dodged(_hit: RefCounted) -> void:
	add(perfect_dodge_gain)


func _on_hit_taken(hit: RefCounted) -> void:
	if hit.hype_loss:
		drain(hit_loss)


func _on_guard_broken() -> void:
	drain(guard_break_loss)


func _set_hype(value: float) -> void:
	if is_equal_approx(value, hype):
		return
	hype = value
	hype_changed.emit(hype, max_hype)
	var now_full := hype >= max_hype
	if now_full == full:
		return
	full = now_full
	hype_full_changed.emit(full)
	get_tree().call_group(CROWD_GROUP, "set_hyped", full)
	if full:
		get_tree().call_group(CROWD_GROUP, "cheer", full_cheer)
