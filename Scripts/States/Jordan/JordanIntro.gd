extends State

# Jordan's entrance is his pre-fight lines and nothing else: he stands idling in the ring while
# JordanPreFight.dialogue plays, and the VS card and the fight hang off dialogue_ended as they always
# have. This state is where he waits under them, and it carries the hold to skip over them.
#
# HE HAS NO WALK-IN, so there is nothing to cut on a second go at the fight: the lines play every time,
# and the hold takes them and the card's build-up in one go. They call no beats either, so the skip has
# no waits to run out and no end state to set but the idle he is already in.
#
# JordanStateMachine builds it rather than his scene: it needs nothing the scene would have to wire.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")

var body: CharacterBody2D

@onready var state_machine = get_parent()

# The skip and its hint, up through the lines.
var entrance: CanvasLayer
# Enter() is deferred, so anything that can reach in from outside checks this first.
var entered := false
# A held skip took the lines and the card's build-up.
var cut := false


func Enter() -> void:
	entered = true
	body.play_state_anim(&"idle")
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin()


func Exit() -> void:
	if is_instance_valid(entrance):
		entrance.queue_free()
	entrance = null


# What a held ui_cancel does: whatever is left of the lines and the card's build-up, all at once,
# landing on the card's flash with him idling as the lines leave him.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


# The lines have handed over to the VS card, and the skip goes with them.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()
