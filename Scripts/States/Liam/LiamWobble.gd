extends State

# A round (plan section 4): the pillar took its first hit of the round and he wobbles on top of it, open to more, for up
# to wobble_time and up to round_hits hits in all (LiamStateMachine.take_pillar_hit counts them). Over its last
# steady_time he has his balance back. The timeout ends the round with the pillar shielded and his air blast.

var body: CharacterBody2D
var state_machine: Node
var clock := 0.0
var steadied := false


func Enter() -> void:
	clock = 0.0
	steadied = false
	body.pillar.set_shielded(false)
	body.play_anim(&"wobble")


func Physics_Update(delta: float) -> void:
	clock += delta
	if not steadied and clock >= state_machine.wobble_time - state_machine.steady_time:
		steadied = true
		body.play_anim(&"steady")
	if clock >= state_machine.wobble_time:
		state_machine.round_over(self)
