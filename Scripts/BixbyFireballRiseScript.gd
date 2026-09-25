extends Node2D

# One of the fireballs beast Bixby's Inferno spits up off the top of the screen (BixbyBeastInferno). Only a
# picture: nothing hurts until the shower brings them back down as BixbyFireball. It flies in
# _physics_process, so a freeze holds it, and frees itself once it is off the screen.

const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")

var velocity := Vector2.ZERO
var at := Vector2.ZERO
var clock := 0.0
var frames: Array = []
var frame_time := 0.06

@onready var sprite: Sprite2D = $Sprite


# Before it enters the tree.
func launch(from: Vector2, with_velocity: Vector2) -> void:
	at = from
	velocity = with_velocity
	position = at.round()


func _ready() -> void:
	if InfernoLayout.USE_FINAL_FIREBALL:
		var spec := InfernoLayout.FINAL_FIREBALL
		sprite.texture = load(spec.ball)
		sprite.hframes = spec.ball_frames
		sprite.vframes = 2
		sprite.offset = spec.rise_offset
		# Row 0, the rising one.
		frames = range(spec.ball_frames)
		frame_time = spec.ball_frame_time
	else:
		var spec := InfernoLayout.PLACEHOLDER_FIREBALL
		sprite.texture = load(InfernoLayout.FIRE_TRAIL_SHEET)
		sprite.hframes = InfernoLayout.FIRE_TRAIL_FRAMES
		sprite.offset = spec.ball_offset
		# Upside down, so its flames trail below it on the way up.
		sprite.flip_v = true
		frames = spec.ball_frames
		frame_time = spec.ball_frame_time
	sprite.frame = frames[0]


func _physics_process(delta: float) -> void:
	clock += delta
	at += velocity * delta
	position = at.round()
	sprite.frame = frames[int(clock / frame_time) % frames.size()]
	if at.y < InfernoLayout.RISE_OFF_SCREEN_Y:
		queue_free()
