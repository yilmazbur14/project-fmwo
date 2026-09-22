extends State

# Mason thrown into the air by the tiered finisher's uppercuts (PlayerFinisher), then down on the mat.
# Deliberately inert, the way EricJuggled is: the finisher lifts him (MasonScript.juggle_lift) and
# picks his poses (juggle_pose), and this only draws them, with his shadow on the mat while he is up.
# Anything this state animated on its own clock would drift against the juggle's three hit-stops; his
# weight is in the art, not in here.
# His body, hurtbox and y-sort stay where the first uppercut caught him: only sprite.offset rises, so
# the frame point his shadow and his hazards are measured from never moves. After the crash, alive, he
# lies a beat and gets up (MasonStateMachine.after_juggle). Killed in the air, he lands into his
# defeat instead (MasonStateMachine.land_juggled).

const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")

@export var animation_player : AnimationPlayer
@export var character_body : CharacterBody2D
@export var hurtbox : Area2D
@export var mason_state_machine : Node

var sheet_texture: Texture2D
var sheet_frames := 0
# What his sprite hung at before, put back on the way out, and what the juggle sheet hangs at, which is
# the height lift() rises from. They are not the same number: the juggle frames are taller than his
# main ones and hang lower to stand him on the same ground line.
var sheet_offset := Vector2.ZERO
var rest_offset := Vector2.ZERO
var drawn_lift := 0.0
var shadow: Sprite2D
var crash_sound: AudioStreamPlayer
# After the crash: the lying beat left, then whether it's over.
var lying_left := -1.0
var lying_done := false
# The recovery the finisher asked for as he crashed, and the time since.
var recovering := false
var recovery_delay := 0.0
var recovery_clock := 0.0
# Set by the state machine when he's killed in the air (MasonStateMachine._end_fight).
var final_state := ""


func _ready() -> void:
	var spec := MasonArtLayout.CRASH_THUD_SFX
	crash_sound = AudioStreamPlayer.new()
	crash_sound.stream = load(spec.stream)
	crash_sound.pitch_scale = spec.pitch
	crash_sound.volume_db = spec.volume_db
	add_child(crash_sound)


func Enter() -> void:
	lying_left = -1.0
	lying_done = false
	recovering = false
	final_state = ""
	drawn_lift = 0.0
	var art := MasonArtLayout.juggle()
	var sprite: Sprite2D = character_body.sprite
	sheet_texture = sprite.texture
	sheet_frames = sprite.hframes
	sheet_offset = sprite.offset
	rest_offset = sprite.offset
	if art.has("texture"):
		# His last frame on the sheet before may not exist on this one.
		sprite.frame = 0
		sprite.hframes = art.hframes
		sprite.texture = load(art.texture)
		sprite.offset = art.offset
		rest_offset = art.offset
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	_spawn_shadow()


func Exit() -> void:
	var sprite: Sprite2D = character_body.sprite
	sprite.offset = sheet_offset
	sprite.hframes = sheet_frames
	sprite.texture = sheet_texture
	if is_instance_valid(shadow):
		shadow.queue_free()
	shadow = null


func Physics_Update(delta: float) -> void:
	if recovering:
		recovery_clock += delta
	if lying_left > 0.0:
		lying_left -= delta
		if lying_left <= 0.0:
			lying_done = true
			_get_up()


# px over his ground line, on his sprite alone: never his position, or his hurtbox, his y-sort and
# every point measured off his frames would ride up with him.
func lift(px: float) -> void:
	drawn_lift = px
	var sprite: Sprite2D = character_body.sprite
	sprite.offset.y = rest_offset.y - px / sprite.global_scale.y
	if not is_instance_valid(shadow):
		return
	var spec := MasonArtLayout.JUGGLE_SHADOW
	shadow.visible = px > 0.0
	shadow.frame = clampi(int(px / spec.step), 0, spec.hframes - 1)
	shadow.global_position = _feet().round()


func pose(which: StringName, crater: bool) -> void:
	var art := MasonArtLayout.juggle()
	match which:
		&"launch":
			animation_player.play(art.launch)
		&"crash":
			animation_player.play(art.crash)
			crash_sound.play()
			if is_instance_valid(shadow):
				shadow.visible = false
			if crater:
				_spawn_crater()
		&"down":
			animation_player.play(art.down)


# The finisher's recovery, as he crashes: he lies a beat, then gets up, and his next cycle comes
# `delay` after now.
func recover(delay: float) -> void:
	recovering = true
	recovery_delay = delay
	recovery_clock = 0.0
	_get_up()


# His middle in the air, which the finisher's camera follows.
func air_point() -> Vector2:
	return character_body.juggle_point(MasonArtLayout.juggle().tumble_centre) - Vector2(0, drawn_lift)


func _get_up() -> void:
	if recovering and lying_done:
		mason_state_machine.after_juggle(maxf(recovery_delay - recovery_clock, 0.0))


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if mason_state_machine.current_state != self:
		return
	var art := MasonArtLayout.juggle()
	if anim_name == art.launch:
		animation_player.play(art.tumble)
	elif anim_name == art.crash:
		if not final_state.is_empty():
			mason_state_machine.land_juggled(final_state)
		else:
			lying_left = MasonArtLayout.JUGGLE_LYING_TIME


# Under his feet on the mat, on the floor layer with his other ground marks.
func _spawn_shadow() -> void:
	var spec := MasonArtLayout.JUGGLE_SHADOW
	shadow = Sprite2D.new()
	shadow.texture = load(spec.texture)
	shadow.hframes = spec.hframes
	shadow.scale = Vector2.ONE * spec.scale
	shadow.modulate.a = spec.alpha
	shadow.visible = false
	mason_state_machine.ground_layer().add_child(shadow)
	shadow.global_position = _feet().round()


func _feet() -> Vector2:
	return character_body.juggle_point(MasonArtLayout.juggle().feet)


# Where he crashed, on the floor layer, then gone a while later. There is no Mason crater drawn yet,
# so today this never runs. Its `impact_pixel` is a point on the JUGGLE sheet's frame, which is the one
# showing when it would spawn.
func _spawn_crater() -> void:
	var spec := MasonArtLayout.crash_crater()
	if not spec.has("texture"):
		return
	var crater := Sprite2D.new()
	crater.texture = load(spec.texture)
	crater.hframes = spec.hframes
	crater.centered = false
	crater.offset = -spec.pivot
	crater.scale = Vector2.ONE * spec.scale
	crater.add_to_group(mason_state_machine.HAZARD_GROUP)
	var layer: Node2D = mason_state_machine.ground_layer()
	layer.add_child(crater)
	crater.global_position = character_body.juggle_point(spec.impact_pixel).round()
	var play := crater.create_tween()
	for i in range(1, spec.hframes):
		play.tween_interval(spec.frame_times[i - 1])
		play.tween_callback(crater.set_frame.bind(i))
	play.tween_interval(spec.hold)
	play.tween_property(crater, "modulate:a", 0.0, spec.fade_time)
	play.tween_callback(crater.queue_free)
