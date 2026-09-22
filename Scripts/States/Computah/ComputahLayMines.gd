extends State

# ATTACK 2, PART ONE: HE SEEDS THE MAT. He stands his ground and fires mine pods out of the cannon in
# an arc, one every mine_lay_interval, and then goes straight into a high-speed chase. The pods are
# not the attack - the CHASE is - and the pods are what make running away from it cost something.
#
# PLACEMENT IS REJECTION SAMPLING INSIDE runner_bounds(), NOT INSIDE ROPES. The bounds are where a
# runner's feet may be, so a pod is never laid somewhere the player cannot be herded onto, and never
# half off the mat. A spot is refused if it is inside mine_spacing of a live pod or inside
# mine_min_from_player of the player: nothing is ever dropped on top of somebody, and the field stays
# a field instead of a pile. About twenty tries, then that pod is skipped rather than forced - a
# forced pod would land on one of the two rules this attack's fairness rests on.
#
# THAT LEAVES A GUARANTEED CLEAR LANE OF ABOUT 80 PX DOWN THE SIDES: narrow enough to be a real test
# against a 720 px/s chaser, wide enough that there is always an out.
#
# FREEZE SAFETY: the cadence is a Physics_Update accumulator and the lob is a node-bound tween.

const MineScene := preload("res://Scenes/Bosses/ComputahMineScene.tscn")

@export var body : CharacterBody2D
@export var hazard_layer : Node2D
@export var lay_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Tries per pod before it is given up on. Twenty on a 1532 x 513 box with at most eight 200 px
# exclusions leaves a skipped pod vanishingly rare, and a skip is the safe failure.
const PLACEMENT_TRIES := 20

var clock := 0.0
var laid := 0
var next_at := 0.0


func Enter() -> void:
	clock = 0.0
	laid = 0
	next_at = 0.0
	body.velocity = Vector2.ZERO
	body.set_solid(true)
	body.set_target_active(true)
	body.set_body_box(&"beam_brace")
	body.show_battery(false)
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	body.play_anim(&"beam_brace")


func Physics_Update(delta: float) -> void:
	clock += delta
	while laid < state_machine.mine_count and clock >= next_at:
		_lay_one()
		laid += 1
		next_at += state_machine.mine_lay_interval
	if laid >= state_machine.mine_count and clock >= next_at:
		_start_chase()


func _lay_one() -> void:
	var spot := _free_spot()
	if spot == Vector2.INF:
		return
	# Read off the pose on screen before the recoil takes over, so the pod leaves the barrel where
	# the barrel currently is.
	var from: Vector2 = body.muzzle_point()
	var mine: Node2D = MineScene.instantiate()
	# Before it goes in: every duration a pod runs on is one of the fight's own numbers, read back
	# through here, and its first physics step can come on the frame it is added.
	mine.state_machine = state_machine
	state_machine.add_hazard(mine, spot, hazard_layer)
	mine.lob(from)
	body.play_anim(&"beam_fire", &"beam_brace")
	lay_sfx_player.play()


# A spot inside the runner's box, clear of every live pod and of the player. Vector2.INF means twenty
# tries found nothing, which skips the pod: the field being one short is nothing, and a pod forced on
# top of the player would be a trap with no warning at all.
func _free_spot() -> Vector2:
	var live: Array = state_machine.live_mines()
	if live.size() >= state_machine.mine_cap:
		return Vector2.INF
	var bounds: Rect2 = state_machine.runner_bounds()
	var player: Node2D = state_machine.get_player()
	for i in PLACEMENT_TRIES:
		var spot := Vector2(randf_range(bounds.position.x, bounds.end.x),
			randf_range(bounds.position.y, bounds.end.y)).round()
		if player and spot.distance_to(player.global_position) < state_machine.mine_min_from_player:
			continue
		var clear := true
		for mine in live:
			if spot.distance_to(mine.global_position) < state_machine.mine_spacing:
				clear = false
				break
		if clear:
			return spot
	return Vector2.INF


# Straight into the chase, on the mine field's own numbers rather than the standalone chase's: this
# one is faster and longer, because its job is to herd the player over their own minefield.
func _start_chase() -> void:
	state_machine.start_chase(state_machine.mine_chase_speed_from,
		state_machine.mine_chase_speed_to, state_machine.mine_chase_time)
