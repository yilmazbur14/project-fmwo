extends State

# The pillar's hits_to_topple-th hit: it crumbles, the row with it, and he tumbles off it to LAND_SPOT over fall_time, his floor point
# sliding down the ring as his height drops, landing on his back. The floor stays as it is for the attack after his
# window (addendum 4), though the player's footing on any ice is normal while he's down (normal_footing_when_down); the
# steam clears so the window reads; the HUD is back. On the mat he is a target again, and lands in Downed, or in Broken
# if a Break was banked while he was up there.

const ScreenView := preload("res://Scripts/ScreenView.gd")

const LANDING_SHAKE := 12.0
const LANDING_SHAKE_STEPS := 5
const LANDING_SHAKE_STEP_TIME := 0.028

var body: CharacterBody2D
var state_machine: Node
var clock := 0.0
var from := Vector2.ZERO
var start_height := 0.0
var landed := false


func Enter() -> void:
	clock = 0.0
	landed = false
	from = body.global_position
	start_height = body.height
	if state_machine.normal_footing_when_down:
		state_machine.set_player_ice(false)
	body.pillar.crumble(state_machine.crumble_time)
	body.row.crumble(state_machine.crumble_time)
	body.steam.set_density(0.0, state_machine.fall_steam_clear)
	body.leave_perch()
	body.play_anim(&"fall")


func Physics_Update(delta: float) -> void:
	if landed:
		return
	clock += delta
	var weight := clampf(clock / state_machine.fall_time, 0.0, 1.0)
	body.global_position = from.lerp(state_machine.LAND_SPOT, weight).round()
	body.height = start_height * (1.0 - weight * weight)
	body.place()
	if weight < 1.0:
		return
	landed = true
	body.stand_on_floor(state_machine.LAND_SPOT)
	body.play_sfx(&"slam")
	ScreenView.shake(get_tree(), LANDING_SHAKE, LANDING_SHAKE_STEPS, LANDING_SHAKE_STEP_TIME)
	state_machine.landed(self)
