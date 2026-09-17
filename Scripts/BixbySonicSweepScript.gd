extends Node2D

# The sonic scream beast Bixby spins with: one beam out of each of his three maws, sweeping the floor as he
# turns. The beams are glued to the mouths of the frame he is drawing, so his spin is what aims them: they
# come out where the art says, at the screen angle and the foreshortened length a beam fired that way along
# the floor reads at. Dashing through one is the dodge, so like the other sweeping beams it reports its own
# hits instead of joining "enemy projectile".
#
# Placing them follows his drawn frame, so it runs in _process; how long they take to grow, to die away and
# what they hurt runs in _physics_process, so a freeze holds it. Their hitboxes are kept on what is drawn,
# but the hit itself is a swept test against the arc each beam covered since the last physics frame, which
# an overlap test is too coarse for at the speed he turns.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const BEAM_SCENE := preload("res://Scenes/Bosses/BixbySonicBeamScene.tscn")

# Beams drawn over him and beams that pass behind him: his near maws are in front of his body.
const NEAR_Z := 1
const FAR_Z := 0

# The player's hurtbox is 12x27 next to a beam 78 thick, so the swept test treats them as a circle this
# big, which is within a few px of it either way.
const PLAYER_RADIUS := 13.0
# A beam sweeps further than its own thickness between two physics frames, so an overlap test steps clean
# over a player standing in its way: the arc is sampled at least this often instead, in px of tip travel.
const SWEEP_SAMPLE_PX := 48.0
const MAX_SWEEP_SAMPLES := 24

# Set by the attack before the sweep enters the tree. A beam stops at the ropes rather than screaming over
# the crowd, unless his maws are already outside them.
var player: CharacterBody2D
var body: CharacterBody2D
var arena := Rect2()

var clock := 0.0
var fading := false
var beams: Array[Area2D] = []
# The mouth each beam is on, as the azimuth of that head, so it can stay on it from frame to frame.
var was_azimuth: Array[float] = []
var aimed := false
# Where each beam was last physics frame, for the swept test.
var was_at: Array[Vector2] = []
var was_turned: Array[float] = []
var was_long: Array[float] = []
var tracking := false


func _ready() -> void:
	for i in CombinedLayout.SONIC_BEAMS:
		var beam: Area2D = BEAM_SCENE.instantiate()
		CombinedLayout.dress(beam.get_node("Sprite2D"), CombinedLayout.BEAM_SHEET,
			CombinedLayout.BEAM_FRAME_SIZE, CombinedLayout.BEAM_OFFSET)
		beam.hide()
		beams.append(beam)
		was_azimuth.append(0.0)
		was_at.append(Vector2.ZERO)
		was_turned.append(0.0)
		was_long.append(0.0)
		add_child(beam)


# He has stopped screaming: the beams die away and the sweep frees itself.
func stop() -> void:
	if fading:
		return
	fading = true
	clock = 0.0
	for beam in beams:
		beam.monitoring = false


func _process(_delta: float) -> void:
	if not is_instance_valid(body):
		return
	global_position = body.feet_position()
	var frame: int = body.drawn_frame_of(BixbyBeastArtLayout.SPIN_SHEET)
	if CombinedLayout.MOUTH_ANCHORS.has(frame):
		_aim(CombinedLayout.MOUTH_ANCHORS[frame])


func _physics_process(delta: float) -> void:
	clock += delta
	if fading:
		var left := 1.0 - clock / CombinedLayout.BEAM_FADE_TIME
		if left <= 0.0:
			queue_free()
			return
		modulate.a = left
		return
	_damage_player()


# One beam out of each mouth of the frame on screen, pointing the way that head faces.
func _aim(frame_anchors: Array) -> void:
	var anchors := _stay_on_their_heads(frame_anchors)
	var grown := clampf(clock / CombinedLayout.BEAM_GROW_TIME, 0.0, 1.0) if not fading else 1.0
	var step := int(clock / CombinedLayout.BEAM_FRAME_TIME)
	var full := CombinedLayout.BEAM_REACH * CombinedLayout.SCALE
	for i in beams.size():
		var anchor: Array = anchors[i]
		var azimuth := deg_to_rad(anchor[0])
		was_azimuth[i] = azimuth
		var beam := beams[i]
		beam.show()
		beam.position = BixbyBeastArtLayout.local(Vector2(anchor[1], anchor[2]))
		beam.rotation = CombinedLayout.beam_angle(azimuth)
		beam.z_index = NEAR_Z if anchor[3] else FAR_Z
		# How long it reads pointing that way, foreshortened by the arena's viewing angle and cut off at
		# the ropes.
		var stretch := CombinedLayout.beam_length(azimuth) * grown
		stretch = minf(stretch, _room_to_the_ropes(beam) / full)
		var sprite: Sprite2D = beam.get_node("Sprite2D")
		sprite.frame = (step + i) % sprite.hframes
		sprite.scale.x = CombinedLayout.SCALE * stretch
		_set_reach(beam, full * stretch)


# His three heads are alike, so the mouths of a frame are listed from whichever one is at the front. Each
# beam takes the mouth nearest the one it was on, so it turns with its own head instead of jumping back
# round the circle every time the loop comes round again.
func _stay_on_their_heads(anchors: Array) -> Array:
	if not aimed:
		aimed = true
		return anchors
	var best := 0
	var closest := INF
	for shift in anchors.size():
		var apart := 0.0
		for i in anchors.size():
			var azimuth := deg_to_rad(anchors[(i + shift) % anchors.size()][0])
			apart += absf(wrapf(azimuth - was_azimuth[i], -PI, PI))
		if apart < closest:
			closest = apart
			best = shift
	var ordered := []
	for i in anchors.size():
		ordered.append(anchors[(i + best) % anchors.size()])
	return ordered


# How far a beam out of this mouth runs before it is over the ropes. A mouth already outside them (he is
# drawn tall, and can stand right against the back rope) is left to scream as far as it likes.
func _room_to_the_ropes(beam: Area2D) -> float:
	var from := beam.global_position
	if not arena.has_point(from):
		return INF
	var along := Vector2.RIGHT.rotated(beam.global_rotation)
	var room := INF
	if absf(along.x) > 0.001:
		room = minf(room, ((arena.end.x if along.x > 0.0 else arena.position.x) - from.x) / along.x)
	if absf(along.y) > 0.001:
		room = minf(room, ((arena.end.y if along.y > 0.0 else arena.position.y) - from.y) / along.y)
	return room


func _set_reach(beam: Area2D, length: float) -> void:
	var shape: CollisionShape2D = beam.get_node("CollisionShape2D")
	(shape.shape as RectangleShape2D).size = Vector2(maxf(length, 1.0),
		CombinedLayout.BEAM_HIT_THICKNESS * CombinedLayout.SCALE)
	shape.position.x = length / 2.0
	beam.monitoring = not fading and length > 0.0


func _damage_player() -> void:
	var live := is_instance_valid(player)
	var struck: Area2D = null
	for i in beams.size():
		var beam := beams[i]
		var length: float = (beam.get_node("CollisionShape2D").shape as RectangleShape2D).size.x
		if tracking and live and struck == null and beam.monitoring and _swept_over_player(i, length):
			struck = beam
		was_at[i] = beam.global_position
		was_turned[i] = beam.global_rotation
		was_long[i] = length
	tracking = true
	if struck:
		player.receive_hit(HitInfo.make(&"bixby_sonic_beam", struck, global_position))


# Whether a beam crossed the player anywhere between where it was last physics frame and where it is now.
func _swept_over_player(i: int, length: float) -> bool:
	var beam := beams[i]
	var turned := wrapf(beam.global_rotation - was_turned[i], -PI, PI)
	var travelled := was_at[i].distance_to(beam.global_position) + absf(turned) * maxf(length, was_long[i])
	var samples := clampi(ceili(travelled / SWEEP_SAMPLE_PX), 1, MAX_SWEEP_SAMPLES)
	var across := CombinedLayout.BEAM_HIT_THICKNESS * CombinedLayout.SCALE / 2.0 + PLAYER_RADIUS
	for step in samples + 1:
		var weight := float(step) / samples
		var from := was_at[i].lerp(beam.global_position, weight)
		var along := (player.global_position - from).rotated(-(was_turned[i] + turned * weight))
		if absf(along.y) <= across and along.x >= -PLAYER_RADIUS \
				and along.x <= lerpf(was_long[i], length, weight) + PLAYER_RADIUS:
			return true
	return false
