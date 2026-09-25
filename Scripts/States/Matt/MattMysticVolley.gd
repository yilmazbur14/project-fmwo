extends State

# The Mystic volley: he teleports round the ring and fires a bouncing bolt from each spot, as many casts
# as his health's tier gives (MattStateMachine.mystic_casts, locked for the cycle). One cast, 0.90 s:
#   OUT     0.15 s  he squeezes out where he stands.
#   IN      0.15 s  he reforms on the spot chosen as he went.
#   WINDUP  0.45 s  the red badge, the cast's wind-up and a cyan glint at his mouth.
#   HOLD    0.15 s  the bolt leaves his mouth on the fire frame, and he holds the fire pose.
#
# THE SPOT IS ON A LATTICE LINE THROUGH THE PLAYER. A heading h from the lattice and a range r: his
# mouth goes at P - h * r, P being the player's hurtbox centre as he vanishes, so the bolt is aimed
# exactly without its art ever being turned. The spot is valid if his feet land in STAND_RECT, at
# least mystic_spot_gap from where he was, on a heading the last cast didn't use, with his mouth at
# least mystic_bolt_clearance from every live bolt; picked uniformly from all valid ones. Failing
# that, the heading rule goes, then the clearance, then the range may drop to mystic_range_floor. A
# cast with nowhere to go, or one that would put a sixth bolt in the air, is skipped.
#
# FREEZE SAFETY: every wait is a Physics_Update accumulator and every effect is node-bound.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const BOLT_SCENE := preload("res://Scenes/Bosses/MattMysticBoltScene.tscn")

const SHOT_ID := &"matt_mystic_shot"
# A spot is chosen off these passes in turn, each dropping one more rule.
const PASSES := [
	{"heading_rule": true, "clearance": true, "floor": false},
	{"heading_rule": false, "clearance": true, "floor": false},
	{"heading_rule": false, "clearance": false, "floor": false},
	{"heading_rule": false, "clearance": false, "floor": true},
]

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { CHOOSE, OUT, IN, WINDUP, HOLD }

var beat := Beat.CHOOSE
var beat_clock := 0.0
var casts_left := 0
# The cast in flight: {feet, mouth, heading, range, player, flip}.
var spot := {}
var last_heading := Vector2.ZERO
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var glint: Node2D
var glint_clock := 0.0
# Every spot this volley chose and every cast it skipped, for a test.
var spots: Array = []
var skipped := 0


func Enter() -> void:
	released = false
	casts_left = state_machine.cycle_casts
	last_heading = Vector2.ZERO
	spots.clear()
	skipped = 0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	# The choice waits for the first step, where a state may hand over.
	beat = Beat.CHOOSE
	beat_clock = 0.0


func Exit() -> void:
	release()


# Idempotent: the badge, the glint and the HUD go whichever way the volley ended.
func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.restore_hud()
	_drop_glint()


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	_step_glint(delta)
	match beat:
		Beat.CHOOSE:
			_next_cast()
		Beat.OUT:
			if beat_clock >= state_machine.teleport_out:
				beat = Beat.IN
				beat_clock = 0.0
				body.teleport_in(spot.feet, spot.flip)
				body.update_hud_fade(&"mystic_windup")
		Beat.IN:
			if beat_clock >= state_machine.teleport_in:
				_wind_up()
		Beat.WINDUP:
			if beat_clock >= state_machine.mystic_windup:
				_fire()
		Beat.HOLD:
			if beat_clock >= state_machine.mystic_after:
				beat = Beat.CHOOSE
				beat_clock = 0.0
				_next_cast()


func _next_cast() -> void:
	while casts_left > 0:
		casts_left -= 1
		spot = _choose_spot()
		if spot.is_empty():
			skipped += 1
			continue
		spots.append(spot)
		last_heading = spot.heading
		beat = Beat.OUT
		beat_clock = 0.0
		body.teleport_out()
		return
	state_machine.on_child_transition(self, "TrueshotBarrage")


func _wind_up() -> void:
	beat = Beat.WINDUP
	beat_clock = 0.0
	body.play_anim(&"mystic_windup")
	ParryTell.telegraph(body, SHOT_ID, state_machine.mystic_windup, _tell_anchor)
	_build_glint()


func _tell_anchor() -> Vector2:
	return body.tell_anchor(&"mystic_windup")


# The bolt leaves the fire frame's mouth, which is where the spot put it.
func _fire() -> void:
	beat = Beat.HOLD
	beat_clock = 0.0
	ParryTell.clear(body)
	_drop_glint()
	body.play_anim(&"mystic_fire")
	body.play_sfx(&"mystic_fire")
	var bolt: Node2D = BOLT_SCENE.instantiate()
	bolt.heading = spot.heading
	bolt.speed = state_machine.mystic_speed
	bolt.bounces = state_machine.mystic_bounces
	bolt.hit_radius = state_machine.mystic_hit_radius
	bolt.bounds = state_machine.ROPES.grow(-state_machine.mystic_hit_radius)
	bolt.player = state_machine.get_player()
	bolt.body = body
	state_machine.add_hazard(bolt, body.mouth_point(&"mystic_fire"), body.projectile_layer)


#THE SPOT

func _choose_spot() -> Dictionary:
	if state_machine.live_bolts().size() >= state_machine.mystic_max_alive:
		return {}
	var player: Node2D = state_machine.get_player()
	if player == null:
		return {}
	var aim: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var headings: Array[Vector2] = state_machine.lattice_headings()
	for rules: Dictionary in PASSES:
		var found := []
		for heading in headings:
			if rules.heading_rule and heading.is_equal_approx(last_heading):
				continue
			for reach in _ranges(rules.floor):
				var candidate := _spot(aim, heading, reach)
				if _valid(candidate, rules.clearance):
					found.append(candidate)
		if not found.is_empty():
			return found[state_machine.rng.randi_range(0, found.size() - 1)]
	return {}


func _ranges(with_floor: bool) -> Array[float]:
	var out: Array[float] = []
	if with_floor:
		out.append(state_machine.mystic_range_floor)
	var steps: int = maxi(state_machine.mystic_range_steps, 2)
	for i in steps:
		out.append(lerpf(state_machine.mystic_range.x, state_machine.mystic_range.y, float(i) / float(steps - 1)))
	return out


# His mouth on the line back from the player along the heading, and his feet under it for the pose the
# bolt leaves on, facing the way it flies.
func _spot(aim: Vector2, heading: Vector2, reach: float) -> Dictionary:
	var flip := heading.x < 0.0
	var mouth := aim - heading * reach
	var feet := mouth - MattArtLayout.mouth_offset(&"mystic_fire", flip)
	return {"feet": feet, "mouth": mouth, "heading": heading, "range": reach, "player": aim, "flip": flip}


func _valid(candidate: Dictionary, clearance: bool) -> bool:
	var feet: Vector2 = candidate.feet
	var stand: Rect2 = state_machine.STAND_RECT
	if feet.x < stand.position.x or feet.x > stand.end.x or feet.y < stand.position.y or feet.y > stand.end.y:
		return false
	if feet.distance_to(body.global_position) < state_machine.mystic_spot_gap:
		return false
	if clearance:
		for bolt in state_machine.live_bolts():
			if bolt.global_position.distance_to(candidate.mouth) < state_machine.mystic_bolt_clearance:
				return false
	return true


#THE GLINT
# A cyan spark at his mouth through the wind-up, over everything, in the hazard group.

func _build_glint() -> void:
	_drop_glint()
	var spec := MattArtLayout.fx(&"glint")
	glint = Polygon2D.new()
	(glint as Polygon2D).polygon = MattArtLayout.star(4, spec.radius, 0.3)
	(glint as Polygon2D).color = spec.color
	glint_clock = 0.0
	state_machine.add_hazard(glint, body.mouth_point(&"mystic_windup"), body.projectile_layer)


func _step_glint(delta: float) -> void:
	if not is_instance_valid(glint):
		return
	glint_clock += delta
	var spec := MattArtLayout.fx(&"glint")
	var pulse := 0.7 + 0.3 * absf(sin(glint_clock * PI / spec.pulse_time))
	glint.scale = Vector2.ONE * pulse
	glint.global_position = body.mouth_point(&"mystic_windup").round()


func _drop_glint() -> void:
	if is_instance_valid(glint):
		glint.queue_free()
	glint = null
