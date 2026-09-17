extends State

# He rides off one side of the screen, turns, and crosses the arena, dealing a giant card over each
# third as his floor point passes its centre.
# In phase one the cards are dealt face down and left hanging, to fall one at a time during the storm.
# In phase two he holds each one up face-out first, then lays it flat on the floor for the monte.

const GIANT_CARD_SCENE := preload("res://Scenes/Bosses/JoshGiantCardScene.tscn")
const GiantCard := preload("res://Scripts/JoshGiantCardScript.gd")

@export var body : CharacterBody2D
@export var glide_sfx_player : AudioStreamPlayer
@export var card_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Leg { APPROACH, CROSS }

const LAND_CHEER := 0.5

var leg := Leg.APPROACH
var cross_dir := 1
var entry_edge := 0.0
var exit_edge := 0.0
var next_third := 0
var laid := 0
var hold_left := 0.0


func Enter() -> void:
	body.play_anim(&"glide")
	glide_sfx_player.play()
	leg = Leg.APPROACH
	laid = 0
	hold_left = 0.0

	# Out the nearer side, so the crossing that deals the cards runs the whole width of the arena.
	var middle: float = state_machine.ROPES.get_center().x
	if body.ground_position.x <= middle:
		entry_edge = state_machine.pass_left_edge
		exit_edge = state_machine.pass_right_edge
		cross_dir = 1
		next_third = 0
	else:
		entry_edge = state_machine.pass_right_edge
		exit_edge = state_machine.pass_left_edge
		cross_dir = -1
		next_third = state_machine.THIRDS - 1

	state_machine.slots = _deal_kinds()
	state_machine.cards = [null, null, null]


func Physics_Update(delta: float) -> void:
	if hold_left > 0.0:
		hold_left -= delta
		# Held still over the third he is showing, so the face has time to read.
		body.fly_toward(body.ground_position, state_machine.glide_speed, delta)
		if hold_left > 0.0:
			return
		body.play_anim(&"glide")
		get_tree().call_group("arena_crowd", "cheer", LAND_CHEER)

	if laid >= state_machine.THIRDS:
		state_machine.on_child_transition(self, "CardStorm" if state_machine.cycle_phase == 0 else "Monte")
		return

	var target := Vector2(entry_edge if leg == Leg.APPROACH else exit_edge, state_machine.pass_y)
	var left: float = body.fly_toward(target, state_machine.glide_speed, delta)

	if leg == Leg.APPROACH:
		# He eases into his target rather than landing on it, so arriving is a distance, not a line.
		if left < state_machine.PASS_TURN_DISTANCE:
			leg = Leg.CROSS
		return

	while laid < state_machine.THIRDS and _reached(next_third):
		_lay(next_third)
		next_third += cross_dir
		laid += 1
		if hold_left > 0.0:
			return


func _reached(index: int) -> bool:
	if index < 0 or index >= state_machine.THIRDS:
		return false
	return (body.ground_position.x - state_machine.third_centre(index).x) * cross_dir >= 0.0


func _lay(index: int) -> void:
	var airborne: bool = state_machine.cycle_phase == 0
	var card := GIANT_CARD_SCENE.instantiate()
	card.hover_height = state_machine.card_hover_height
	# Always the floor layer: the card lifts itself over everything while it falls and drops back to
	# floor depth once it has landed, so its shadow never leaves the floor.
	state_machine.add_hazard(card, state_machine.third_centre(index), body.floor_layer)
	card.lay(index, GiantCard.Mode.AIRBORNE if airborne else GiantCard.Mode.FLAT,
		state_machine.slots[index])
	state_machine.cards[index] = card
	card_sfx_player.play()

	if airborne:
		body.play_anim(&"lay", &"glide")
		return
	# The "read this" beat: he holds the card up face-out, then lays it flat.
	body.play_anim(&"show", &"show_hold")
	card.show_face(state_machine.face_show_time)
	hold_left = state_machine.face_show_time + GiantCard.FACE_SETTLE_TIME
	get_tree().call_group("arena_crowd", "hush")


# A random permutation of the three faces, indexed by third.
func _deal_kinds() -> Array[int]:
	var kinds: Array[int] = [GiantCard.Kind.SAFE, GiantCard.Kind.DRAIN, GiantCard.Kind.INVERT]
	kinds.shuffle()
	return kinds
