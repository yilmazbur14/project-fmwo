extends State

# Holding still up on his pillar: the beat before his next attack (beat_left), or wherever the player's loss left him.

var body: CharacterBody2D
var state_machine: Node
# Seconds until the next attack; below 0, none comes.
var beat_left := -1.0


func Enter() -> void:
	if body.height > 0.0 and body.current_anim != &"perch_idle":
		body.play_anim(&"perch_idle")


func Physics_Update(delta: float) -> void:
	if beat_left < 0.0:
		return
	beat_left -= delta
	if beat_left <= 0.0:
		beat_left = -1.0
		state_machine.start_attack()
