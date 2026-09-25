extends Node2D

# The target on the mat under Danny's Sumo Smash (DannyBossSlams), and his shadow under the leap to the gate
# (DannyBossSumo): danny_slam_target.png (DannyBossArtLayout's slam_target), on the spot he'll come down on.
# While he hovers and tracks, its two smallest frames flicker; the rest of the time its size says how high
# he is, a frame bigger the lower he comes, and full size (his seated footprint) on the frame before he lands.
# It knows nothing of where he is or how high: the attack places it and pushes his lift in every step
# (hover() or set_height()), so it can't drift from him and it stops dead wherever he does. The flicker runs
# on its own physics clock, so a freeze or the pause screen holds that too.
# It lies on the fight's floor layer, under everyone, and whoever made it frees it.

const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

# [share of full_height, frame]: the first share his lift is over picks the frame, and under them all it is
# the landing frame. The plan's drop: f2 over 0.75, f3 over 0.45, f4 over 0.12, then f5.
const HEIGHT_FRAMES := [[0.75, 2], [0.45, 3], [0.12, 4]]

# The lift the frames are measured against: the smash's hover, or the peak of the arc it is a shadow for.
var full_height := 380.0
var hovering := false
var hover_clock := 0.0
var spec: Dictionary = Layout.fx(&"slam_target")
var sprite: Sprite2D


# Built here rather than in _ready, so the attack can set it up before adding it.
func _init() -> void:
	sprite = Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.offset = spec.offset
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.frame = spec.land_frame
	add_child(sprite)


# He's up at full height, tracking or latched. A mark already flickering carries on where it was.
func hover() -> void:
	if hovering:
		return
	hovering = true
	hover_clock = 0.0
	sprite.frame = spec.hover_frames[0]


# He's rising or coming down, `px` over the mat.
func set_height(px: float) -> void:
	hovering = false
	sprite.frame = spec.land_frame
	for step in HEIGHT_FRAMES:
		if px > step[0] * full_height:
			sprite.frame = step[1]
			return


func _physics_process(delta: float) -> void:
	if not hovering:
		return
	hover_clock += delta
	var frames: Array = spec.hover_frames
	sprite.frame = frames[int(hover_clock / spec.frame_time) % frames.size()]
