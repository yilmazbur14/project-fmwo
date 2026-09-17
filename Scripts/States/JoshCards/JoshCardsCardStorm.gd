extends State

# Phase one's storm: he keeps crossing the arena leaving card bombs behind him while the three giant
# cards he dealt come down, strictly one at a time.
# One third at a time is the whole fairness budget: the other two are always clear, and no bomb is
# ever dropped over the third that is warning or slamming, so there is always somewhere to stand.

const GiantCard := preload("res://Scripts/JoshGiantCardScript.gd")

@export var body : CharacterBody2D
@export var glide_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

var drop_order: Array[int] = []
var drop_index := 0
var falling := false
var gap_left := 0.0
# The third that is warning or slamming, and how long it stays off limits once it has landed.
var danger_third := -1
var danger_left := 0.0

# How long the carpet of fallen cards takes to clear once the storm is over.
const CLEAR_TIME := 0.4


func Enter() -> void:
	body.play_anim(&"glide")
	glide_sfx_player.play()
	state_machine.begin_passes()
	drop_order = [0, 1, 2]
	drop_order.shuffle()
	drop_index = 0
	falling = false
	gap_left = 0.0
	danger_third = -1
	danger_left = 0.0


# The fallen cards stay where they landed for the whole storm; the deck clears when it ends.
func Exit() -> void:
	for card in state_machine.cards:
		if is_instance_valid(card):
			card.dismiss(CLEAR_TIME)
	state_machine.cards = [null, null, null]


func Physics_Update(delta: float) -> void:
	state_machine.advance_pass(delta, state_machine.bomb_spacing, danger_third)

	if danger_left > 0.0:
		danger_left -= delta
		if danger_left <= 0.0:
			danger_third = -1

	if falling:
		return
	gap_left -= delta
	if gap_left > 0.0:
		return
	if drop_index >= drop_order.size():
		state_machine.on_child_transition(self, "Dismount")
		return
	_drop_next()


func _drop_next() -> void:
	var third: int = drop_order[drop_index]
	var card = state_machine.cards[third]
	if not is_instance_valid(card):
		# Nothing to drop over that third; move on rather than stalling the cycle.
		drop_index += 1
		return
	card.slammed.connect(_on_card_slammed, CONNECT_ONE_SHOT)
	card.drop(state_machine.card_warning)
	falling = true
	danger_third = third
	danger_left = INF


func _on_card_slammed() -> void:
	falling = false
	drop_index += 1
	gap_left = state_machine.card_gap
	danger_left = GiantCard.SLAM_TIME
