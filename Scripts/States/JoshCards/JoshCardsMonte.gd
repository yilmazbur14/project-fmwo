extends State

# Phase two's three-card monte. The three cards are lying flat on the floor with their faces known;
# he shuffles them from the air, holds them still for a beat, and then turns over whichever one the
# player is standing on. What it says is what the player gets.
# The trackability budget is the whole point: five swaps, half a second each, arcing in opposite
# directions, with a lock-in the player can still run through. Do not raise swap_count above 6 or drop
# swap_time below 0.3 - real three-card monte is about 0.4 s a swap and is meant to be unwinnable.

const GiantCard := preload("res://Scripts/JoshGiantCardScript.gd")

@export var body : CharacterBody2D
@export var glide_sfx_player : AudioStreamPlayer
@export var shuffle_sfx_player : AudioStreamPlayer
@export var reveal_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Stage { SHUFFLE, LOCK, FLIP, HOLD, FAST }

const SAFE_CHEER := 1.0
const CLEAR_TIME := 0.4

var stage := Stage.SHUFFLE
var clock := 0.0
var swaps_done := 0
var sliding := false
var swap_from := 0
var swap_to := 0
var revealed_third := 0
var revealed_kind := 0


func Enter() -> void:
	body.play_anim(&"glide")
	glide_sfx_player.play()
	state_machine.begin_passes()
	stage = Stage.SHUFFLE
	clock = 0.0
	swaps_done = 0
	sliding = false


# Anything still on the board when the monte ends goes with it.
func Exit() -> void:
	for card in state_machine.cards:
		if is_instance_valid(card):
			card.dismiss(CLEAR_TIME)
	state_machine.cards = [null, null, null]


func Physics_Update(delta: float) -> void:
	var spacing: float = state_machine.fast_bomb_spacing if stage == Stage.FAST else state_machine.monte_bomb_spacing
	state_machine.advance_pass(delta, spacing, -1)
	clock += delta
	match stage:
		Stage.SHUFFLE:
			_run_shuffle()
		Stage.LOCK:
			_run_lock()
		Stage.FLIP:
			_run_flip()
		Stage.HOLD:
			_run_hold()
		Stage.FAST:
			_run_fast()


func _run_shuffle() -> void:
	if sliding:
		if clock < state_machine.swap_time():
			return
		_finish_swap()
		clock = 0.0
		sliding = false
		swaps_done += 1
		return
	if clock < state_machine.swap_gap:
		return
	if swaps_done >= state_machine.swap_count:
		stage = Stage.LOCK
		clock = 0.0
		_pulse_all(state_machine.lock_in_time)
		return
	_start_swap()


# Two of the three trade places, one bowing up-screen and one down, so the eye has to pick one.
func _start_swap() -> void:
	swap_from = randi() % state_machine.THIRDS
	swap_to = (swap_from + 1 + randi() % (state_machine.THIRDS - 1)) % state_machine.THIRDS
	var seconds: float = state_machine.swap_time()
	var arc: float = state_machine.swap_arc
	var first = state_machine.cards[swap_from]
	var second = state_machine.cards[swap_to]
	if is_instance_valid(first):
		first.slide_to(swap_to, arc, seconds)
	if is_instance_valid(second):
		second.slide_to(swap_from, -arc, seconds)
	shuffle_sfx_player.play()
	sliding = true
	clock = 0.0


# What is where only changes once the slide is over, so the reveal reads the board the player saw.
func _finish_swap() -> void:
	var kind: int = state_machine.slots[swap_from]
	state_machine.slots[swap_from] = state_machine.slots[swap_to]
	state_machine.slots[swap_to] = kind
	var card = state_machine.cards[swap_from]
	state_machine.cards[swap_from] = state_machine.cards[swap_to]
	state_machine.cards[swap_to] = card


func _run_lock() -> void:
	if clock < state_machine.lock_in_time:
		return
	# Sampled the instant the flip starts: the player can run right up to here.
	var player: Node2D = state_machine.get_player()
	revealed_third = state_machine.third_at(player.global_position.x) if player else 0
	revealed_kind = state_machine.slots[revealed_third]
	var card = state_machine.cards[revealed_third]
	if is_instance_valid(card):
		card.flip_up(state_machine.reveal_flip_time)
	reveal_sfx_player.play()
	stage = Stage.FLIP
	clock = 0.0


func _run_flip() -> void:
	if clock < state_machine.reveal_flip_time:
		return
	_call_it()
	stage = Stage.HOLD
	clock = 0.0


# The card is face up: what it says lands on the player now.
func _call_it() -> void:
	match revealed_kind:
		GiantCard.Kind.SAFE:
			body.show_banner("SAFE")
			get_tree().call_group("arena_crowd", "cheer", SAFE_CHEER)
		GiantCard.Kind.DRAIN:
			body.show_banner("STAMINA DRAIN")
			state_machine.apply_status(&"stamina_drain", state_machine.status_time)
		GiantCard.Kind.INVERT:
			body.show_banner("CONTROLS FLIPPED")
			state_machine.apply_status(&"inverted_controls", state_machine.status_time)


func _run_hold() -> void:
	if clock < state_machine.reveal_hold:
		return
	for card in state_machine.cards:
		if is_instance_valid(card):
			card.dismiss(state_machine.reveal_dismiss)
	state_machine.cards = [null, null, null]
	stage = Stage.FAST
	clock = 0.0


# He works the floor over while the call is still running.
func _run_fast() -> void:
	if clock >= state_machine.fast_bomb_time:
		state_machine.on_child_transition(self, "Dismount")


func _pulse_all(seconds: float) -> void:
	for card in state_machine.cards:
		if is_instance_valid(card):
			card.pulse(seconds)
