extends Node

# The mash that gets the player out of a hold. A boss holding them calls begin(); from there the
# prompt comes up in alarm red, ESCAPE!, and alternating presses fill a meter that drains on its own.
# Full, `escaped` goes true and the hold's owner lets go. The hold's owner also decides everything
# else: what the crush costs, how many ticks it has, and when it gives up on its own - this only
# reports whether the player got out first.
#
# It is NOT the finisher's mash (PlayerFinisher), which is welded to the freeze, the daze, the juggle
# and the uppercut behind it. What the two do share is the input plumbing (MashInput): the same pair
# of keys, the same swallow list, the same alternation rule. They must agree, because those keys are
# also movement and the guard.
#
# The prompt is FinisherPromptUI, driven through the same small surface the finisher gives it:
# prompt_shown/meter_changed/charge_ended/finished, mash_actions(), `meter`, `tiered` and
# `prompt_key`. Gold MASH! means "you have won, cash it in"; red ESCAPE! means "you are in trouble",
# and that difference is the whole point of using the other word.

signal prompt_shown
signal meter_changed(meter: float, next_action: StringName)
signal charge_ended(filled: bool)
signal finished
# Never emitted here: the prompt connects them because the finisher has them, and a tiered mash is
# the finisher's alone.
signal tier_banked(tier: int)
signal juggle_hit(index: int, last: bool)

const MashInput := preload("res://Scripts/MashInput.gd")

@onready var player: CharacterBody2D = get_parent()

# Deliberately NOT the finisher's 0.107/0.25. Those fill in about 2.0 s at seven alternating presses
# a second, which is longer than the whole hold: nobody would ever get out. These fill in about 1.2 s
# at seven and 0.8 s at ten, which is what EricPacing's p2_crush_interval is set against.
@export var gain_per_press := 0.16
@export var drain_per_second := 0.30
# Real seconds, as the finisher's: both keys pressed together arrive in one input flush however long
# the frame took, and count once.
@export var min_press_interval := 0.03
# After the hold, while any mash key is still held, up to this long, movement reads nothing and a held
# guard stays down (PlayerScript), so the key the player was last hammering doesn't walk them off.
@export var mash_release_latch := 1.0

# What FinisherPromptUI shows: the alarm-red ESCAPE! already written for exactly this.
var prompt_key := &"escape"
# The prompt asks; a grab escape is never the tiered mash.
var tiered := false
var meter := 0.0
var active := false
# Set the moment the meter fills, and read by the hold's owner. It stays set until the next begin(),
# so a hold that checks it on its own physics step can't miss the frame it happened on.
var escaped := false
var last_action := &""
var last_press_usec := 0
var latch_left := 0.0


func is_active() -> bool:
	return active


func is_mash_latched() -> bool:
	return latch_left > 0.0


func mash_actions() -> Array[StringName]:
	return MashInput.actions(player)


# The hold has them. Called by the boss as it closes its grip.
func begin() -> void:
	active = true
	escaped = false
	meter = 0.0
	last_action = &""
	last_press_usec = 0
	latch_left = 0.0
	prompt_shown.emit()


# The hold is over, escaped or not. Idempotent: the owner calls it on every path out.
func cancel() -> void:
	if not active:
		return
	active = false
	charge_ended.emit(escaped)
	finished.emit()
	if MashInput.keys_held(player):
		latch_left = mash_release_latch


func _process(delta: float) -> void:
	if not active:
		# Letting go of every mash key ends the latch early: from then on a press is meant.
		if latch_left > 0.0:
			latch_left = maxf(latch_left - delta, 0.0) if MashInput.keys_held(player) else 0.0
		return
	if player.fight_over or not player.is_grabbed:
		cancel()
		return
	meter = maxf(meter - drain_per_second * delta, 0.0)


func _input(event: InputEvent) -> void:
	if not active:
		return
	var action := MashInput.pressed_action(player, event)
	if action.is_empty() and not MashInput.swallows(event):
		return
	# Before the event is marked handled: the autoload's device tracker sits below this node in the
	# propagation order and would never see the presses that drive the mash.
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()
	if not action.is_empty():
		_press(action)


func _press(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	if not MashInput.counts(action, last_action, now, last_press_usec, min_press_interval):
		return
	last_action = action
	last_press_usec = now
	meter = minf(meter + gain_per_press, 1.0)
	var pair := mash_actions()
	meter_changed.emit(meter, pair[1] if action == pair[0] else pair[0])
	get_tree().call_group("arena_crowd", "cheer", 0.4)
	if meter >= 1.0:
		escaped = true
