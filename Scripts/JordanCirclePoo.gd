extends Node2D

# One of Mason's poo bombs in Jordan's circle (JordanComboCircle), dropped from his feet as he flies: it falls to its
# floor point, lies armed and `live` for the layout's POO_LIVE, then fades and is gone, harmless as it fades. A hit
# squashes it (pop): PooBombScene's burst, and gone. The attack steps it a physics step at a time on its own game time,
# so a pause and a finisher's freeze hold it, and does its contact test off `live` and where it lies. The node is its
# floor point, with the bomb's drawn base on it, on the god's Stage layer, y-sorted with the player.

const Layout := preload("res://Scripts/JordanCircleLayout.gd")

# Summed 1/60 s steps fall a hair short of a round number.
const CLOCK_SLACK := 0.0001

var live := false
var popped := false
var clock := 0.0
var fall_from := 0.0
var fall_time := 0.0
# Its clock when it landed, when it started to fade and when it was squashed; -1 until then.
var landed_at := -1.0
var fade_at := -1.0
var fade_time := 0.0
var popped_at := -1.0
var bomb: Sprite2D
var burst: Sprite2D


func _ready() -> void:
	var spec: Dictionary = Layout.POO_SHEET
	bomb = Sprite2D.new()
	bomb.name = "Bomb"
	bomb.texture = load(spec.texture)
	bomb.hframes = spec.hframes
	bomb.offset = spec.offset
	bomb.scale = Vector2.ONE * spec.scale
	add_child(bomb)


# From `lift` px over its floor point, landing `time` later.
func drop(lift: float, time: float) -> void:
	fall_from = lift
	fall_time = time
	clock = 0.0
	_place_fall(0.0)


func step(delta: float) -> void:
	clock += delta
	if popped:
		var frame := int((clock - popped_at + CLOCK_SLACK) / Layout.POP_SHEET.frame_time)
		if frame >= burst.hframes:
			queue_free()
			return
		burst.frame = frame
		return
	bomb.frame = int((clock + CLOCK_SLACK) / Layout.POO_SHEET.frame_time) % bomb.hframes
	if landed_at < 0.0:
		var share := 1.0 if clock + CLOCK_SLACK >= fall_time else clampf(clock / maxf(fall_time, 0.0001), 0.0, 1.0)
		_place_fall(share)
		if share >= 1.0:
			landed_at = clock
			live = fade_at < 0.0
	elif live and clock + CLOCK_SLACK >= landed_at + Layout.POO_LIVE:
		fade(Layout.POO_FADE)
	if fade_at >= 0.0:
		var left := 1.0 - (clock - fade_at) / maxf(fade_time, 0.0001)
		if left <= CLOCK_SLACK:
			queue_free()
			return
		modulate.a = left


# Harmless from here, out over `seconds`, and gone.
func fade(seconds: float) -> void:
	live = false
	if fade_at >= 0.0 or popped:
		return
	fade_at = clock
	fade_time = seconds


# Stepped in: squashed where it lies, its burst over it, and gone.
func pop() -> void:
	if popped:
		return
	popped = true
	live = false
	popped_at = clock
	bomb.visible = false
	var spec: Dictionary = Layout.POP_SHEET
	burst = Sprite2D.new()
	burst.name = "Burst"
	burst.texture = load(spec.texture)
	burst.hframes = spec.hframes
	burst.scale = Vector2.ONE * spec.scale
	burst.position = Vector2(0, -Layout.POP_RISE)
	burst.z_index = 1
	add_child(burst)


# Falling as a dropped thing does, faster as it goes.
func _place_fall(share: float) -> void:
	bomb.position.y = -roundf(fall_from * (1.0 - share * share))
