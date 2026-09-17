extends State

# He goes down and the deck goes with him: a burst of cards scatters across the floor and stays there.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")

@export var body : CharacterBody2D

const SCATTER_CARDS := 14
const SCATTER_REACH := Vector2(420, 150)
const SCATTER_TIME := 0.55
const SCATTER_HOP := 90.0


func Enter() -> void:
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	body.play_anim(&"defeat")
	_scatter()


func _scatter() -> void:
	if JoshArtLayout.USE_FINAL_CARD_BURST:
		_rain_the_deck()
		return
	var spec := JoshArtLayout.PLACEHOLDER_CARD_BURST
	for i in SCATTER_CARDS:
		var card := Node2D.new()
		var face := Polygon2D.new()
		face.polygon = JoshArtLayout.centred_rect(spec.size)
		face.color = spec.color
		card.add_child(face)
		var rim := Line2D.new()
		rim.points = face.polygon
		rim.closed = true
		rim.width = spec.edge_width
		rim.default_color = spec.edge_color
		card.add_child(rim)

		body.floor_layer.add_child(card)
		var from := body.global_position
		card.global_position = from
		var to := from + Vector2(randf_range(-SCATTER_REACH.x, SCATTER_REACH.x),
			randf_range(-SCATTER_REACH.y, SCATTER_REACH.y))
		var turn := randf_range(-PI, PI)
		var fling := card.create_tween()
		fling.tween_method(func(weight: float) -> void:
			card.global_position = (from.lerp(to, weight)
				- Vector2(0, SCATTER_HOP * 4.0 * weight * (1.0 - weight))).round()
			card.rotation = turn * weight
		, 0.0, 1.0, SCATTER_TIME).set_delay(i * 0.02)


# The deck comes down over him and settles flat along the ground line, and stays there.
func _rain_the_deck() -> void:
	var spec := JoshArtLayout.FINAL_CARD_BURST
	var rain := Sprite2D.new()
	rain.texture = load(spec.rain)
	rain.hframes = spec.hframes
	rain.scale = Vector2.ONE * spec.scale
	rain.offset = spec.frame_size / 2.0 - spec.pivot
	body.floor_layer.add_child(rain)
	rain.global_position = body.global_position
	var times: Array = spec.rain_frame_times
	var play := rain.create_tween()
	for i in range(1, spec.hframes):
		play.tween_interval(times[i - 1])
		play.tween_callback(func() -> void: rain.frame = i)
