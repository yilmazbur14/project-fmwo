extends State

# Danny's worm spit (plan section 3.1), facing the player and with no badge, because nothing in it hurts: a
# gulp that dries the old puddles, then four globs of worms lobbed from his mouth (DannyBossGlobScript) in two
# volleys of two, each landing as a puddle on one of the four spots picked at the gulp (section 3.2):
#   0     spit_windup, the gulp. The old puddles start to dry, and are out of play at once.
#   0.45  spit_fire, the first volley from that frame's mouth texel: a glob, and another 0.08 s behind it.
#   0.80  spit_fire2, the second volley the same.
#   0.91  spit_recover, and at 1.10 the attack is done.
# The sheet spits the first volley to his right as drawn and the second to his left, so the first goes to the
# two spots on that side as he faces. The globs are hazards of their own: the spit ending, or a root cutting it
# short, leaves them flying.
#
# WHERE THEY LAND, off the fight's seeded rng: round the player's feet at `distances`, each at least `spread`
# degrees round from the others while that can be had, then anywhere round them, then the nearest points of a
# lattice over the floor. Every puddle's trigger keeps rope_gap inside the ropes and `apart` from every other
# one's, so the floor between them stays one open piece with ways through at least that wide: there is always
# a clean path from the player to him, and no corner can be sealed off. None lands within clear_of_player of the
# player's feet, or on the floor round his (clear_of_danny).

const GLOB_SCRIPT := preload("res://Scripts/DannyBossGlobScript.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

@export var body : CharacterBody2D

#KNOBS (seconds and px)
@export var first_at := 0.45
@export var second_at := 0.80
# Globs a volley, and how far behind the one before it each goes, inside its spit frame.
@export var per_volley := 2
@export var volley_gap := 0.08
# The second spit frame's own time on the sheet, before he settles back.
@export var second_hold := 0.11
@export var done_at := 1.10
@export var dry_time := 0.4
@export var glob_flight := 0.70
@export var glob_arc := 200.0
# The candidates: headings x distances round the player's feet, squashed onto the floor.
@export var headings := 24
@export var distances: Array[float] = [260.0, 340.0, 420.0, 500.0, 580.0, 660.0]
@export var floor_squash := 0.6
# Each puddle at least this many degrees round the player's feet from the others, while that can be had.
@export var spread := 60.0
# Gaps from a puddle's trigger: to the player's feet, to the ropes, and to every other puddle's trigger.
@export var clear_of_player := 100.0
@export var rope_gap := 100.0
@export var apart := 100.0
# The floor kept clear round his feet, each way: his standing body's half-width and a punch's room beside it,
# and a step in front and behind.
@export var clear_of_danny := Vector2(240, 90)
# The last resort: columns x rows of points over the floor a puddle may take, the nearest the player first.
@export var fallback_lattice := Vector2i(9, 7)

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
var fired := 0
var settling := false
# The trigger's radii in px, as each puddle has them.
var radii: Vector2 = Layout.fx(&"puddle").trigger * Layout.SCALE
# The spots, in the order they're spat, and the globs sent to them.
var spots: Array[Vector2] = []
var globs: Array[Node2D] = []
# For tests: the fight_clock at each glob's release.
var release_times: Array[float] = []


func Enter() -> void:
	released = false
	clock = 0.0
	fired = 0
	settling = false
	globs.clear()
	release_times.clear()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	body.set_body_box(&"idle")
	body.play_anim(&"spit_windup")
	body.play_sfx(&"gulp")
	_dry_old_puddles()
	spots = _in_spit_order(pick_spots(state_machine.player_feet(), body.global_position))


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	while fired < spots.size() and clock >= _release_at(fired):
		_spit(fired)
	if not settling and fired >= spots.size() and clock >= second_at + second_hold:
		settling = true
		body.play_anim(&"spit_recover")
	if clock >= done_at:
		state_machine.attack_done(self)


func Exit() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true


func _exit_tree() -> void:
	released = true


# The spots for a spit with the player's feet and his where they are now. Public, so a test can sweep them.
func pick_spots(feet: Vector2, danny: Vector2) -> Array[Vector2]:
	var rng: RandomNumberGenerator = state_machine.rng
	var count := 2 * per_volley
	var candidates: Array[Vector2] = []
	for i in headings:
		var heading := Vector2.from_angle(TAU * i / headings)
		for distance in distances:
			var spot := feet + Vector2(heading.x * distance, heading.y * distance * floor_squash)
			if _allowed(spot, feet, danny):
				candidates.append(spot)
	var picked: Array[Vector2] = []
	for least_spread in [spread, 0.0]:
		while picked.size() < count:
			var keeps := func(spot: Vector2) -> bool: return _fits(spot, picked) and _spread_from(spot, picked, feet) >= least_spread
			var pool: Array = candidates.filter(keeps)
			if pool.is_empty():
				break
			picked.append(pool[rng.randi_range(0, pool.size() - 1)])
	if picked.size() < count:
		var field: Array = _lattice().filter(func(spot: Vector2) -> bool: return _allowed(spot, feet, danny))
		field.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.distance_squared_to(feet) < b.distance_squared_to(feet))
		for spot in field:
			if picked.size() < count and _fits(spot, picked):
				picked.append(spot)
	return picked


# Where a puddle's pivot may go: the ropes, less its trigger and rope_gap all round.
func puddle_area() -> Rect2:
	var inset := radii + Vector2.ONE * rope_gap
	var ropes: Rect2 = state_machine.ROPES
	return Rect2(ropes.position + inset, ropes.size - 2.0 * inset)


func _spit(index: int) -> void:
	var pose: StringName = &"spit_fire" if index < per_volley else &"spit_fire2"
	if index % per_volley == 0:
		body.play_anim(pose)
		body.play_sfx(&"spit")
	var mouth: Vector2 = body.mouth_point(pose)
	var glob: Node2D = GLOB_SCRIPT.new()
	glob.flight = glob_flight
	glob.arc = glob_arc
	glob.player = state_machine.get_player()
	glob.body = body
	glob.state_machine = state_machine
	glob.aim(mouth, spots[index], body.global_position.y)
	state_machine.add_hazard(glob, mouth, body.projectile_layer)
	globs.append(glob)
	release_times.append(body.fight_clock)
	fired += 1


func _release_at(index: int) -> float:
	var volley_at := first_at if index < per_volley else second_at
	return volley_at + (index % per_volley) * volley_gap


func _dry_old_puddles() -> void:
	var old: Array[Node] = state_machine.live_puddles()
	for puddle in old:
		puddle.dry(dry_time)
	if not old.is_empty():
		body.play_sfx(&"puddle_dry")


func _allowed(spot: Vector2, feet: Vector2, danny: Vector2) -> bool:
	return puddle_area().has_point(spot) and not _within(spot - feet, radii + Vector2.ONE * clear_of_player) \
		and not _within(spot - danny, radii + clear_of_danny)


# Clear of every picked puddle's trigger by `apart`.
func _fits(spot: Vector2, picked: Array[Vector2]) -> bool:
	for other in picked:
		if _within(spot - other, 2.0 * radii + Vector2.ONE * apart):
			return false
	return true


# The least angle round the feet between `spot` and any picked one, on the floor unsquashed; 360 for none.
func _spread_from(spot: Vector2, picked: Array[Vector2], feet: Vector2) -> float:
	var least := 360.0
	for other in picked:
		least = minf(least, rad_to_deg(absf(angle_difference(_bearing(spot, feet), _bearing(other, feet)))))
	return least


func _bearing(spot: Vector2, feet: Vector2) -> float:
	var offset := spot - feet
	return atan2(offset.y / floor_squash, offset.x)


# Inside the ellipse of radii `half` round the origin.
static func _within(offset: Vector2, half: Vector2) -> bool:
	return pow(offset.x / half.x, 2.0) + pow(offset.y / half.y, 2.0) < 1.0


# Its last row and column a pixel inside the area's far edges, which has_point leaves out.
func _lattice() -> Array[Vector2]:
	var area := puddle_area()
	var span := area.size - Vector2.ONE
	var points: Array[Vector2] = []
	for row in fallback_lattice.y:
		for column in fallback_lattice.x:
			var at := Vector2(float(column) / (fallback_lattice.x - 1), float(row) / (fallback_lattice.y - 1))
			points.append(area.position + span * at)
	return points


# The first volley to the spots on the side the first spit frame aims at as he faces, the second to the rest.
func _in_spit_order(picked: Array[Vector2]) -> Array[Vector2]:
	var order: Array[Vector2] = picked.duplicate()
	if body.sprite.flip_h:
		order.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
	else:
		order.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x > b.x)
	return order
