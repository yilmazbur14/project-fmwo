extends State

const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var hurtbox : Area2D

# Set by the state machine when a juggle killed him (EricStateMachine.land_juggled): he stays lying where
# he crashed, rather than slumped over his sword.
var lying := false
var sheet_texture: Texture2D
var sheet_frames := 0


# Called when the node enters the scene tree for the first time.
func Enter() -> void:
	var body: Node = hurtbox.get_parent()
	if lying:
		var art := EricArtLayout.juggle()
		var sprite: Sprite2D = body.sprite
		sheet_texture = sprite.texture
		sheet_frames = sprite.hframes
		if art.has("texture"):
			sprite.frame = 0
			sprite.hframes = art.hframes
			sprite.texture = load(art.texture)
		animation_player.play(art.down)
		# At once: this comes from inside his AnimationPlayer's own step, which would otherwise leave the
		# new clip's first frame to its next one and draw frame 0 in between.
		animation_player.advance(0.0)
	else:
		animation_player.play("downed")
	# Beaten, he's past punching: punches still on their way mustn't land.
	var beaten: bool = body.defeated or body.boss_health <= 0
	hurtbox.monitoring = not beaten
	hurtbox.monitorable = not beaten
	body.daze_used = false


func Exit() -> void:
	if not lying:
		return
	lying = false
	var sprite: Sprite2D = hurtbox.get_parent().sprite
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
