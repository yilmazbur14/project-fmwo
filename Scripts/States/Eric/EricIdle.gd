extends State

# Eric's stand between the attacks of a chain.
# In phase two it is neither a stand nor his usual frames. It can't be his usual frames, because every
# one of them draws the sword that was thrown out of the ring; and it isn't a stand, because he walks
# the gap down onto the player instead of waiting it out. That closing walk, on top of p2_attack_gap
# being not much more than half phase one's, is the clearest reading of "much faster and much more
# agile since he's lost his big sword" the fight has.

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")
const EricPhaseTwoPose := preload("res://Scripts/EricPhaseTwoPose.gd")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D

# Where his body may walk: the whirlwind's own lunge area, his body inside the ropes.
const STALK_AREA := Rect2(240, 180, 1440, 590)
# He presses in to here and no further, measured between his body's centre and theirs, so the stalk
# never ends with him standing inside the player.
const STALK_GAP := 240.0

@onready var player = get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")

var stalking := false
var sheet_texture: Texture2D
var sheet_frames := 0
var pose_frames: Array = []
var pose_clock := 0.0


func Enter() -> void:
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	stalking = character_body != null and character_body.phase_two
	if not stalking:
		animation_player.play("idle")
		return
	# The stalk drives his frames itself; an animation still running would fight it for them.
	animation_player.stop()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	pose_frames = EricPhaseTwoPose.show(sprite, "idle")
	pose_clock = 0.0


func Exit() -> void:
	if not stalking:
		return
	stalking = false
	var sprite: Sprite2D = character_body.sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture


func Physics_Update(delta: float) -> void:
	if not stalking or player == null or not is_instance_valid(player):
		return
	pose_clock += delta
	var sprite: Sprite2D = character_body.sprite
	sprite.frame = EricPhaseTwoPose.frame_at(pose_frames, pose_clock)
	var to_player: Vector2 = player.global_position - character_body.global_position
	sprite.flip_h = to_player.x < 0.0
	if to_player.length() <= STALK_GAP:
		return
	var speed: float = EricPacing.p2("p2_stalk_speed", character_body.state_machine.rage)
	var step: float = minf(speed * delta, to_player.length() - STALK_GAP)
	character_body.global_position = (character_body.global_position + to_player.normalized() * step).clamp(STALK_AREA.position, STALK_AREA.end)
