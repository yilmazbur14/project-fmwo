extends "res://Scripts/BossBroken.gd"

# Jordan with his Break gauge full (BossBroken): down on one knee by the box he dropped, the defeat's
# kneel held. At his spot his soles are on y 506, already lower than his juggle floor (about 476), so
# the Break's slide leaves him where he is. JordanStateMachine builds it, beside his Juggled.
#
# On the kaiju (JordanKaijuLayout.USE_KAIJU): Broken while he rides it, it collapses where it stands and he is thrown
# off its seat onto the mat over the Break's slide - BREAK_THROW_OFF at home, beside it away from home - and kneels
# there; knocked off already, he goes down where he sits. Either way he gets back on it after (JordanRemount).

const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")

# The inside edges of the ropes, as every other fight measures them.
const FEET_BOUNDS := Rect2(113, 114, 1692, 853)

@export var topple_time := 0.55
@export var topple_arc := 160.0
# His topple's peak no higher than this, as the stomp's knock-off keeps it.
@export var topple_top := 140.0
# How far from the kaiju's feet he lands when it is away from home.
@export var throw_off_reach := 300.0

# Thrown off the kaiju's seat: the slide is his flight off it, from where he sat.
var toppling := false
var toppled_from := Vector2.INF


# Cut in at once, rather than through play_state_anim(), which lets a one-shot finish first: a Break
# out of the summon would otherwise crouch and punch the air before he went down. A redirected blast
# that fills the gauge has just leaned him back on a rotation tween, which would tip the kneel and
# leave the stars off his head.
func _pose_in() -> void:
	if body.stagger_tween:
		body.stagger_tween.kill()
	body.sprite.rotation = 0.0
	body.state_anim = &"broken"
	toppling = body.mounted
	if toppling:
		toppled_from = state_machine.kaiju.seat_point()
		state_machine.set_mounted(false)
		state_machine.kaiju.light_spines(0)
		state_machine.kaiju.set_charge(0.0)
		state_machine.kaiju.play_anim(&"collapse", &"down")
		body.play_anim(&"topple")
		return
	body.play_anim(&"broken")


func _start_slide() -> void:
	if not toppling:
		super()
		return
	slide_from = _feet()
	slide_to = _throw_off_spot()
	slide_time = topple_time
	slide_left = slide_time


# Where he comes down off its seat: his spot for it at home, or out toward the middle of the ring from it.
func _throw_off_spot() -> Vector2:
	var kaiju: Node2D = state_machine.kaiju
	var spot := KaijuLayout.BREAK_THROW_OFF
	if not kaiju.is_home():
		var side := 1.0 if kaiju.feet_point().x < 960.0 else -1.0
		spot = (kaiju.feet_point() + Vector2(side * throw_off_reach, 0.0)).clamp(KaijuLayout.SOLES_BOUNDS.position, KaijuLayout.SOLES_BOUNDS.end)
		if KaijuLayout.box_in_walls(state_machine._body_box_at(spot)):
			spot = KaijuLayout.BREAK_THROW_OFF
	spot.y = maxf(spot.y, state_machine.states["Juggled"].floor_y())
	return spot.round()


func _feet() -> Vector2:
	return body.to_global(JordanArtLayout.FLOOR_POINT)


func _set_feet(point: Vector2, weight: float) -> void:
	# His topple sheet: its seat on where he sat, its hips on the arc, its soles on where he lands.
	var apex := clampf(toppled_from.y - topple_top, 0.0, topple_arc) if toppling else 0.0
	if toppling and weight < 1.0 and body.place_on_arc(toppled_from, &"seat", 0, slide_to, &"soles", 5, weight, apex):
		return
	var arc := 4.0 * apex * weight * (1.0 - weight)
	body.global_position += point - Vector2(0, arc) - _feet()
	if toppling and weight >= 1.0:
		toppling = false
		body.play_anim(&"broken")


func _feet_bounds() -> Rect2:
	return FEET_BOUNDS


func _head_point() -> Vector2:
	return body.global_position + JordanArtLayout.broken_daze_anchor()


func _time_up() -> void:
	state_machine.on_child_transition(self, "Remount" if state_machine.kaiju_mode else "Idle")
