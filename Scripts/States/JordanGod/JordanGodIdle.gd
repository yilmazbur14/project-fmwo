extends State

# Between Jordan's attacks: he hovers, the player is free, and IDLE_TIME later the next attack in turn starts. With
# none built yet he hovers on, and asks again each IDLE_TIME. After the player's loss nothing more starts.

const Layout := preload("res://Scripts/JordanGodLayout.gd")

var god: Node2D
var state_machine: Node
var clock := 0.0


func Enter() -> void:
	clock = 0.0
	god.play(&"hover")


func Physics_Update(delta: float) -> void:
	if state_machine.player_defeated or god.defeated:
		return
	clock += delta
	if clock < Layout.IDLE_TIME:
		return
	clock = 0.0
	state_machine.start_next_attack()
