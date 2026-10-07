extends Node2D

# One figure of Josh's Portal Monte (JoshCardsPortalMonte): the real Josh, a fake, or - only ever right after a fake the
# player bit on - a punish, bursting out of a small gate and lunging at the player with his gold card blade. All three
# are the same sheet on the same timing, drawn the same, so only the mark over its gate tells them apart until the
# contact: the real one's hit is parried or lands, a fake bursts into cards, a punish lands (hot white: it is the bill
# for the bait, never a parry that failed).
# It reports its own hit rather than letting the player's hurtbox find it (CarterCloneScript's rule): the contact
# instant is a number the Monte owns, and the hit's origin is the player's own hurtbox centre, so any facing answers
# it. Each figure is its own node and so its own hit source. A hazard on the stage, y-sorted on its feet, or over its
# gate while they are above it (_place); its motion and its frames step on physics, so a pause or a finisher's freeze
# holds them.

const Monte := preload("res://Scripts/JoshMonteLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const STRIKE_ID := &"josh_monte_strike"
const PUNISH_ID := &"josh_monte_punish"

# Set before it is added: what it is, where its feet burst out and where they end - short of the player by where its
# cut lands (JoshMonteLayout.contact_offset), so the cut is on them - which way it faces, and who.
var is_feint := false
var is_punish := false
var from_point := Vector2.ZERO
var to_point := Vector2.ZERO
var facing_left := false
var player: Node2D
var body: Node
# With the player free to move (JoshCardsStateMachine.monte_lock_player off), it follows them as it lunges.
var homing := false

var spec: Dictionary
var sprite: Sprite2D
var glow: Polygon2D
var launched := false
var spent := false
var travel_time := 0.0
var travel_clock := 0.0
# From its contact: the cut and follow-through it holds before it scatters, -1 until then.
var follow_clock := -1.0
var glow_clock := 0.0
var feet_at := Vector2.ZERO


func _ready() -> void:
	spec = Monte.slash()
	sprite = Sprite2D.new()
	sprite.name = "Figure"
	sprite.texture = load(spec.texture)
	sprite.hframes = roundi(sprite.texture.get_width() / spec.frame.x)
	sprite.scale = Vector2.ONE * Monte.SCALE
	sprite.offset = spec.frame / 2.0 - spec.feet
	sprite.flip_h = facing_left
	if is_punish:
		sprite.modulate = Monte.PUNISH.tint
	elif is_feint and not Monte.FAKES_ALIKE:
		sprite.modulate = Monte.FAKE_TINT
	add_child(sprite)
	if is_punish:
		_build_glow()
	_place(from_point)
	_show(spec.dash_frames[0])


func launch(seconds: float) -> void:
	travel_time = maxf(seconds, 0.001)
	travel_clock = 0.0
	launched = true


func _physics_process(delta: float) -> void:
	if glow:
		glow_clock += delta
		var spec_glow: Dictionary = Monte.PUNISH
		var beat := 0.5 + 0.5 * sin(TAU * glow_clock / (spec_glow.beat_time * 2.0))
		glow.scale = Vector2.ONE * lerpf(spec_glow.beat[0], spec_glow.beat[1], beat)
	if follow_clock >= 0.0:
		follow_clock += delta
		_show(spec.contact_frame if follow_clock < spec.times[spec.contact_frame] else spec.follow_frame)
		if follow_clock >= Monte.follow_time():
			_scatter()
			queue_free()
		return
	if not launched or spent:
		return
	travel_clock += delta
	if homing and is_instance_valid(player):
		to_point = _player_hurtbox_centre() - Monte.contact_offset(facing_left)
	var p := clampf(travel_clock / travel_time, 0.0, 1.0)
	_place(from_point.lerp(to_point, p))
	# The dash's two frames split it as the slash's own times do.
	var times: Array = spec.times
	var first: float = times[spec.dash_frames[0]]
	_show(spec.dash_frames[0 if p < first / (first + times[spec.dash_frames[1]]) else 1])


# The contact. Red: the hit, built from the player's own hurtbox centre, and the result - parried, it is gone (the
# Monte shows him where it stood); landed, it follows through and scatters. A punish: the same under an id nothing
# answers. A fake: it never reaches them and bursts into cards on the spot.
func strike() -> int:
	if spent:
		return HitInfo.Result.IGNORED
	spent = true
	_place(to_point)
	_show(spec.contact_frame)
	if is_feint or not is_instance_valid(player):
		_scatter()
		queue_free()
		return HitInfo.Result.IGNORED
	var result: int = player.receive_hit(HitInfo.make(PUNISH_ID if is_punish else STRIKE_ID, self, _player_hurtbox_centre(), body))
	if result == HitInfo.Result.PARRIED:
		queue_free()
		return result
	follow_clock = 0.0
	return result


# One of the slash's steps (JoshMonteLayout.SLASH): the sheet's own frame, or the stand-in's.
func _show(step: int) -> void:
	sprite.frame = spec.steps[step] if spec.has("steps") else step


# Its feet at `feet`. Its node sorts FIGURE_SORT_BUMP in front of them, or of its gate's floor point while they are
# above it - a lunge up-screen sorts behind the gate it is coming out of otherwise - and it draws at its feet.
func _place(feet: Vector2) -> void:
	feet_at = feet.round()
	global_position = Vector2(feet_at.x, maxf(feet_at.y, from_point.y) + Monte.FIGURE_SORT_BUMP)
	var lift := Vector2(0.0, feet_at.y - global_position.y)
	if sprite:
		sprite.position = lift
	if glow:
		glow.position = Monte.figure_centre(facing_left) + lift


func _feet() -> Vector2:
	return feet_at


func _player_hurtbox_centre() -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


# Left on the stage where it was, played once and gone (JoshCardsWildCards._flurry's pattern): its own sheet centred on
# the figure once it is in, else the fan of cards on its feet.
func _scatter() -> void:
	var parent := get_parent()
	if parent == null or not is_instance_valid(body):
		return
	var burst := Monte.scatter()
	var fan := Sprite2D.new()
	fan.name = "MonteScatter"
	fan.texture = load(burst.texture)
	fan.hframes = burst.hframes
	fan.scale = Vector2.ONE * burst.scale
	fan.offset = burst.frame_size / 2.0 - burst.pivot
	var at := _feet() + Monte.figure_centre(facing_left) if burst.centred else _feet()
	body.state_machine.add_hazard(fan, at, parent)
	var times: Array = burst.frame_times
	var play := fan.create_tween()
	for i in range(1, burst.hframes):
		play.tween_interval(times[i - 1])
		play.tween_callback(fan.set_frame.bind(i))
	play.tween_interval(times[times.size() - 1])
	play.tween_callback(fan.queue_free)


# A punish burns white-hot over the figure, beating: a tint alone barely lifts his dark keyline and coat.
func _build_glow() -> void:
	var look: Dictionary = Monte.PUNISH
	glow = Polygon2D.new()
	glow.name = "PunishGlow"
	var points := PackedVector2Array()
	for i in look.points:
		points.append(Vector2.from_angle(TAU * i / look.points) * look.glow_radius)
	glow.polygon = points
	glow.color = look.glow
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow.material = added
	add_child(glow)
