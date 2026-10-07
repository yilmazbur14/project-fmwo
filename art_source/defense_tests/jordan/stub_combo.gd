extends "res://Scripts/States/JordanGod/JordanCombo.gd"

# jordan_god's stand-in attack (god.gd), for the framework's own tests: JordanGodLayout.COMBOS pointed at this file
# runs it in the rotation like a real one. Greyson on the left hand and Matt on the right, where attack 1 stands them
# in the user's staging (option B), or PAIR when a test sets one. MODE, set by the test before the fight loads, says
# what it does:
#   &"quick"  the summon, a beat, the recall, the end: for the rotation
#   &"hold"   the player warped and posed, the summon, and everything an attack can put up - the HUD down, lights
#             out with the player, the god and the strings lifted over the dark, an arrow, a hint and a hazard - then
#             a wait that only release() ends: for release
#   &"punch"  the player warped under the left puppet, the summon, the punch-out on him, the recall, the end: for
#             damage and the pairings

const LEFT := {boss = &"greyson", feet = Vector2(768, 870), face_left = false, hand = &"left"}
const RIGHT := {boss = &"matt", feet = Vector2(1344, 870), face_left = true, hand = &"right"}
# Right under Greyson, as the maze's goal is: in the finisher's reach.
const PLAYER_SOLES := Vector2(768, 930)
# Where the punch-out puts the player's soles from the left puppet's.
const UNDER := Vector2(0, 60)
const UP := 1

static var MODE := &"quick"
# The two to summon, in pair()'s shape, when a test wants others than Greyson and Matt.
static var PAIR: Array[Dictionary] = []
# What its runs did, for the test: how many started, how far the last got, and its punch-out's bars.
static var runs := 0
static var reached := &""
static var bars := -1


func pair() -> Array[Dictionary]:
	if not PAIR.is_empty():
		return PAIR
	return [LEFT, RIGHT]


func run() -> void:
	runs += 1
	reached = &"start"
	match MODE:
		&"hold":
			await _hold()
		&"punch":
			await _punch()
		_:
			await _quick()


func _quick() -> void:
	await summon()
	if cut:
		return
	reached = &"summoned"
	await wait(0.2)
	if cut:
		return
	await recall()
	if cut:
		return
	reached = &"done"
	finish()


func _hold() -> void:
	warp_player(PLAYER_SOLES, UP)
	await summon()
	if cut:
		return
	hud(false)
	darken(true)
	lift_above_dark(player())
	lift_above_dark(god)
	lift_above_dark(god.layer(&"strings"))
	lift_above_dark(god.layer(&"stage"))
	arrow(&"up")
	hint("STUB")
	var marker := Node2D.new()
	marker.name = "StubHazard"
	add_hazard(marker, Vector2(960, 540), god.layer(&"floor"))
	reached = &"holding"
	await wait(9999.0)


func _punch() -> void:
	var first: Dictionary = pair()[0]
	warp_player(first.feet + UNDER, UP)
	await summon()
	if cut:
		return
	reached = &"punch_out"
	bars = await punch_out(puppets[first.boss])
	if cut:
		return
	reached = &"paid"
	await recall()
	if cut:
		return
	reached = &"done"
	finish()
