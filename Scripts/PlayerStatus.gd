extends Node

# Temporary status effects a boss puts on the player, for Josh's phase 2: one drains their stamina,
# the other reverses their movement. A boss applies one with
#     player.apply_status(kind, duration)      duration 0 takes the kind's default
# and reads player.has_status(kind); player.clear_statuses() takes them all off.
# Each kind counts down in game time, so a hit-stop slows it with the fight. Applying a kind that is
# already running refreshes its time; nothing ever stacks. They come off when a finisher starts, when
# the player dies and when the fight ends, and a new fight builds a new player, so none carry over.

signal status_started(kind: StringName, duration: float)
signal status_ended(kind: StringName)

# The bar empties at stamina_drain_per_second and can't refill while it does. Emptying it breaks the
# guard of a player still holding block, exactly as the block that empties it does.
const STAMINA_DRAIN := &"stamina_drain"
# Both movement axes are reversed. Punching, dashing and blocking are not, and the facing still turns
# to the boss on its own; a dash goes where the reversed movement keys point.
const INVERTED_CONTROLS := &"inverted_controls"

@export var stamina_drain_per_second := 18.0
# What a caller gets for a kind when it passes no duration of its own.
@export var default_durations := {
	STAMINA_DRAIN: 5.0,
	INVERTED_CONTROLS: 4.0,
}

@onready var player: CharacterBody2D = get_parent()

# kind -> seconds of game time left.
var active := {}


func _physics_process(delta: float) -> void:
	if active.is_empty() or player.is_finishing or player.fight_over:
		return
	for kind in active.keys():
		active[kind] -= delta
		if active[kind] <= 0.0:
			_end(kind)
	if active.has(STAMINA_DRAIN):
		player.defense.drain_stamina(stamina_drain_per_second * delta)


# A kind with no default duration is not a status this knows, so a mistyped one does nothing rather
# than running an effect no rule reads.
func apply(kind: StringName, duration := 0.0) -> void:
	if not default_durations.has(kind):
		push_warning("PlayerStatus: no such status %s" % kind)
		return
	if player.fight_over or player.is_finishing or player.playerHealth <= 0:
		return
	var time: float = duration if duration > 0.0 else float(default_durations[kind])
	if time <= 0.0:
		return
	active[kind] = time
	status_started.emit(kind, time)


func has(kind: StringName) -> bool:
	return active.has(kind)


func time_left(kind: StringName) -> float:
	return active.get(kind, 0.0)


func kinds() -> Array:
	return active.keys()


# Movement input as the player should read it.
func steer(input: Vector2) -> Vector2:
	return -input if active.has(INVERTED_CONTROLS) else input


func clear_all() -> void:
	for kind in active.keys():
		_end(kind)


func _end(kind: StringName) -> void:
	if not active.erase(kind):
		return
	status_ended.emit(kind)
