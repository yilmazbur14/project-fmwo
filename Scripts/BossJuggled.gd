extends State

# A boss thrown into the air by the tiered finisher's uppercuts (PlayerFinisher), then down on the mat:
# MasonJuggled made general, for the bosses whose bodies animate in code. The finisher lifts him
# (juggle_lift) and picks his poses (juggle_pose); this draws them from his juggle clips, with his leap
# shadow on the mat while he is up. His body, hurtbox and y-sort stay where the first uppercut caught
# him: only sprite.offset rises. After the crash, alive, he lies a beat and gets up (_after_juggle).
# Killed in the air, he lands into his defeat (_land) and lies there on the `down` loop (lingering).
# A boss subclasses it (extends "res://Scripts/BossJuggled.gd") and overrides _art(); every other hook
# is optional. His state machine builds it in code and sets body, hurtbox and state_machine. A subclass
# that overrides _ready() or _process() calls super.
# THE JUGGLE OWNS HIS SPRITE: texture, hframes, vframes, offset and frame, from Enter until he is up.
# His body's own animator is halted rather than driven, because it re-derives hframes from his main
# frame, and some bodies reset sprite.offset per animation, the offset lift() writes. The clips run on
# this node's own _process, not its state machine's Update, so a machine that stops updating once the
# fight is decided can't leave him mid-crash.

const FightOutro := preload("res://Scripts/FightOutro.gd")

# At the top of his flight his top stays at least this far below the top of the arena, as far up as the
# view goes (headroom).
const JUGGLE_TOP_MARGIN := 12.0
# A three-uppercut juggle is drawn at least this much of its planned height wherever he is Broken:
# BossBroken slides a boss standing higher than floor_y() down to it first.
const JUGGLE_MIN_LIFT_SCALE := 0.5
# The three-uppercut apex in px (PlayerFinisher.planned_apex), for when there is no player to ask.
const FALLBACK_APEX := 310.0

@export var body : CharacterBody2D
@export var hurtbox : Area2D
@export var state_machine : Node

# Set by his state machine when he's killed in the air (its _end_fight): he lands into this state.
var final_state := ""
# His height over his ground line as drawn, in px.
var drawn_lift := 0.0
# The clip showing: &"launch", &"tumble", &"crash", &"down", or &"" before the first pose.
var clip_name := &""
# Whether the finisher has asked for his recovery, which it does as he crashes.
var recovering := false
# Killed in the air, he stays on the juggle sheet looping `down` after this state has gone, until
# stop_lingering().
var lingering := false

var sheet_texture: Texture2D
var sheet_hframes := 1
var sheet_vframes := 1
var sheet_offset := Vector2.ZERO
var shadow: Sprite2D
var crash_sound: AudioStreamPlayer
var drawing := false
var clip: Dictionary = {}
var clip_step := 0
var clip_clock := 0.0
# After the crash: the lying beat left, then whether it's over.
var lying_left := -1.0
var lying_done := false
var recovery_delay := 0.0
var recovery_clock := 0.0


func _ready() -> void:
	var spec: Dictionary = _art().crash_sfx
	crash_sound = AudioStreamPlayer.new()
	crash_sound.stream = load(spec.stream)
	crash_sound.pitch_scale = spec.pitch
	crash_sound.volume_db = spec.volume_db
	add_child(crash_sound)


func Enter() -> void:
	final_state = ""
	drawn_lift = 0.0
	clip_name = &""
	clip = {}
	recovering = false
	lingering = false
	lying_left = -1.0
	lying_done = false
	var art := _art()
	var sprite: Sprite2D = body.sprite
	sheet_texture = sprite.texture
	sheet_hframes = sprite.hframes
	sheet_vframes = sprite.vframes
	sheet_offset = sprite.offset
	_halt_body_anim()
	# His last frame on the sheet before may not exist on this one.
	sprite.frame = 0
	sprite.vframes = 1
	sprite.hframes = art.hframes
	sprite.texture = load(art.texture)
	sprite.offset = art.offset
	sprite.rotation = 0.0
	sprite.visible = true
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	_spawn_shadow()
	drawing = true
	_own_shadow(&"air")
	_on_enter()


func Exit() -> void:
	drawing = false
	_free_shadow()
	if not final_state.is_empty():
		lingering = true
		_play_clip(&"down")
		return
	_restore_sheet()
	_own_shadow(&"restore")
	_on_exit()


func Physics_Update(delta: float) -> void:
	if recovering:
		recovery_clock += delta
	if lying_left > 0.0:
		lying_left -= delta
		if lying_left <= 0.0:
			lying_done = true
			_get_up()


# In game time like the finisher's arc, so the two stay in step through every hit-stop.
func _process(delta: float) -> void:
	if not (drawing or lingering) or clip.is_empty():
		return
	clip_clock += delta
	var times: Array = clip.times
	while clip_clock >= times[clip_step]:
		clip_clock -= times[clip_step]
		if clip_step < times.size() - 1:
			clip_step += 1
		elif clip.loop:
			clip_step = 0
		else:
			_clip_ended()
			return
		body.sprite.frame = clip.frames[clip_step]


# px over his ground line, on his sprite alone: never his position, or his hurtbox, his y-sort and every
# point measured off his frames would ride up with him.
func lift(px: float) -> void:
	drawn_lift = px
	var sprite: Sprite2D = body.sprite
	sprite.offset.y = _art().offset.y - px / sprite.global_scale.y
	if not is_instance_valid(shadow):
		return
	var spec: Dictionary = _art().shadow
	shadow.visible = px > 0.0
	shadow.frame = clampi(int(px / spec.step), 0, spec.hframes - 1)
	shadow.global_position = feet_point().round()


# &"launch" at each uppercut's contact and &"crash" as he lands, as the finisher asks. There is no crash
# crater art, so `crater` draws nothing.
func pose(which: StringName, _crater := false) -> void:
	_play_clip(which)
	if which != &"crash":
		return
	crash_sound.play()
	if is_instance_valid(shadow):
		shadow.visible = false
	_own_shadow(&"ground")


# The finisher's recovery, as he crashes: he lies a beat, then gets up, and his next attack comes
# `delay` after now.
func recover(delay: float) -> void:
	recovering = true
	recovery_delay = delay
	recovery_clock = 0.0
	_get_up()


# His middle in the air, which the finisher's camera follows.
func air_point() -> Vector2:
	return texel_point(_art().tumble_centre) - Vector2(0, drawn_lift)


# The most he can be lifted and still be seen whole, measured on the juggle sheet's own rows.
func headroom() -> float:
	var art := _art()
	return feet_point().y - (art.feet.y - art.top_row) * body.sprite.global_scale.y - JUGGLE_TOP_MARGIN


# The highest line his feet can stand on for a three-uppercut juggle to be drawn at least
# JUGGLE_MIN_LIFT_SCALE of its planned height.
func floor_y() -> float:
	var art := _art()
	var finisher: Node = _finisher()
	var apex: float = finisher.planned_apex(3) if finisher else FALLBACK_APEX
	return (art.feet.y - art.top_row) * body.sprite.global_scale.y + JUGGLE_TOP_MARGIN + JUGGLE_MIN_LIFT_SCALE * apex


func feet_point() -> Vector2:
	return texel_point(_art().feet)


# The world point of the centre of a texel on his juggle sheet as it hangs on him: through the sprite's
# parent (his body, or the node he flies on), from sprite_base_position rather than the position a hit
# shake moves, mirrored with him about the frame's middle, and never through the offset lift() raises.
# The juggle frame is not his main one and its origin is not his feet, which is what makes this easy
# to get wrong by hand.
func texel_point(texel: Vector2) -> Vector2:
	var art := _art()
	var sprite: Sprite2D = body.sprite
	var local: Vector2 = texel + Vector2(0.5, 0.5) - art.frame_size / 2.0
	if sprite.flip_h:
		local.x = -local.x
	return sprite.get_parent().to_global(body.sprite_base_position + (local + art.offset) * sprite.scale)


# The kill's `down` loop ends, and his own sheet goes back for whatever he plays next.
func stop_lingering() -> void:
	if not lingering:
		return
	lingering = false
	clip = {}
	_restore_sheet()


# REQUIRED: his layout's FINAL_JUGGLE.
func _art() -> Dictionary:
	return {}


# His body's animator stops where it is, so nothing but the juggle writes his sprite.
func _halt_body_anim() -> void:
	if "anim_done" in body:
		body.anim_done = true
	if "anim_next" in body:
		body.anim_next = &""


# His own shadow, where he has one: &"air" as the juggle starts, &"ground" as he crashes, &"restore" as
# he gets up. The leap shadow is this state's and is drawn whatever this does.
func _own_shadow(_mode: StringName) -> void:
	pass


func _on_enter() -> void:
	pass


# Only on the way out alive. Killed, he never leaves the juggle sheet.
func _on_exit() -> void:
	pass


# Where the leap shadow lies.
func _ground_layer() -> Node:
	if "floor_layer" in body and body.floor_layer:
		return body.floor_layer
	var scene := get_tree().current_scene
	var ground: Node = scene.get_node_or_null("Arena/GroundFx") if scene else null
	return ground if ground else body.get_parent()


func _after_juggle(delay: float) -> void:
	state_machine.after_juggle(delay)


func _land(final_state_name: String) -> void:
	state_machine.land_juggled(final_state_name)


func _play_clip(which: StringName) -> void:
	clip_name = which
	clip = _art().clips[which]
	clip_step = 0
	clip_clock = 0.0
	body.sprite.frame = clip.frames[0]


# A clip that doesn't loop holds its last frame.
func _clip_ended() -> void:
	var ended := clip_name
	clip = {}
	if ended == &"launch":
		_play_clip(&"tumble")
	elif ended == &"crash":
		if not final_state.is_empty():
			_land(final_state)
		else:
			lying_left = _art().lying_time


func _get_up() -> void:
	if recovering and lying_done:
		_after_juggle(maxf(recovery_delay - recovery_clock, 0.0))


func _restore_sheet() -> void:
	var sprite: Sprite2D = body.sprite
	sprite.frame = 0
	sprite.texture = sheet_texture
	sprite.hframes = sheet_hframes
	sprite.vframes = sheet_vframes
	sprite.offset = sheet_offset
	# So the next state's animation starts over even if it is the one he was halted on.
	if "current_anim" in body:
		body.current_anim = &""


func _spawn_shadow() -> void:
	var spec: Dictionary = _art().shadow
	shadow = Sprite2D.new()
	shadow.texture = load(spec.texture)
	shadow.hframes = spec.hframes
	shadow.scale = Vector2.ONE * spec.scale
	shadow.offset = spec.offset
	shadow.modulate.a = spec.alpha
	shadow.visible = false
	_ground_layer().add_child(shadow)
	shadow.global_position = feet_point().round()


func _free_shadow() -> void:
	if is_instance_valid(shadow):
		shadow.queue_free()
	shadow = null


func _finisher() -> Node:
	var scene := get_tree().current_scene
	var player: Node = scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null
	return player.finisher if player else null
