extends State

# His punish window, on his back at LAND_SPOT for downed_time: three punches' worth (PunchAllowance), one daze and its
# single-bar uppercut. A finisher ends it early into a stagger (LiamStateMachine.end_window); either way he gets up.
# A parried lunge opens it where he was knocked down, his fall there played first (opening_anim, used once).

var body: CharacterBody2D
var state_machine: Node
var time_left := 0.0
var opening_anim := &""


func Enter() -> void:
	body.begin_window()
	body.set_body_box(&"downed")
	body.set_hurtbox_active(true)
	if opening_anim != &"":
		body.play_anim(opening_anim, &"downed")
		opening_anim = &""
	else:
		body.play_anim(&"downed")
	body.play_sfx(&"window")
	time_left = state_machine.downed_time


# His hurtbox stays the one he lies in until he stands (LiamGetUp).
func Exit() -> void:
	body.set_hurtbox_active(false)


func Physics_Update(delta: float) -> void:
	time_left -= delta
	if time_left <= 0.0:
		state_machine.window_over(self)


func flinch() -> void:
	body.play_anim(&"downed_hit", &"downed")
