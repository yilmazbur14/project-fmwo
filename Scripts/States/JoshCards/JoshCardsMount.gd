extends State

# He flicks a card to the floor in front of him, it grows, he steps on and rises to riding height.

@export var body : CharacterBody2D
@export var card_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

var clock := 0.0


func Enter() -> void:
	clock = 0.0
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.play_anim(&"mount")
	body.set_air_draw(true)
	body.grow_glider(state_machine.mount_grow_time)
	card_sfx_player.play()


func Physics_Update(delta: float) -> void:
	clock += delta
	var rise_start: float = state_machine.mount_grow_time
	var rise_time: float = state_machine.mount_rise_time
	var along := clampf((clock - rise_start) / rise_time, 0.0, 1.0)
	body.height = state_machine.glider_height * along * along * (3.0 - 2.0 * along)
	body.place()
	if clock >= rise_start + rise_time + state_machine.mount_settle:
		state_machine.on_child_transition(self, "LayCards")
