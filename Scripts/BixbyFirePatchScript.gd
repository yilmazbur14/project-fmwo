extends StaticBody2D

# A patch of ground set burning by beast Bixby's fire breath. It catches, burns as a solid obstacle the
# player can't walk or dash through, burns out and leaves a scorch mark before freeing itself. It never
# hurts on its own. Its timing all runs in _physics_process, so the finisher's time-stop holds it.

enum Phase { IGNITE, BURNING, BURN_OUT, SCORCH }

#ART (bixby_fire_trail.png and bixby_fire_scorch.png: 40x40 frames at 3x, around the bed's centre, texel (20, 31))
const SHEET := preload("res://Assets/Characters/Bixby/bixby_fire_trail.png")
const SCORCH_SHEET := preload("res://Assets/Characters/Bixby/bixby_fire_scorch.png")
const FRAME_WIDTH := 40
# The collision box, centred on the patch: the burning bed, texels (4, 26) to (35, 35).
const SIZE := Vector2(96, 30)
const IGNITE_FRAMES := [0, 1, 2]
const IGNITE_TIMES := [0.07, 0.07, 0.09]
const BURN_LOOP_FRAMES := [3, 4, 5, 6]
const BURN_LOOP_TIME := 0.11
const BURN_OUT_FRAMES := [7, 8, 9]
const BURN_OUT_TIMES := [0.12, 0.14, 0.18]
# Solid from ignite frame 1 until burn-out frame 2 starts.
const SOLID_FROM_IGNITE_STEP := 1
const SOLID_UNTIL_BURN_OUT_STEP := 2
# The scorch smoulders on frame 0, then fades out on frame 1.
const SCORCH_SMOULDER_TIME := 0.4
const SCORCH_FADE_TIME := 1.0

# The player's body has to be this far clear of the bed before the patch turns solid, so turning solid can
# never catch them or push them.
const PLAYER_CLEARANCE := 4.0

# Set by the state machine before the patch enters the tree.
var burn_time := 6.0
# Its slot in the trail: neighbours are mirrored in turn and start their burn loops on different frames,
# so a row doesn't flicker in step.
var trail_slot := 0
var player: Node2D
# Asked before turning solid; false means the patch would wall part of the floor off, and it burns out.
var may_turn_solid: Callable

var phase := Phase.IGNITE
var step := 0
var frame_clock := 0.0
var phase_clock := 0.0
var solid := false

@onready var collision: CollisionShape2D = $CollisionShape2D
@onready var sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	sprite.flip_h = posmod(trail_slot, 2) == 1
	_show(IGNITE_FRAMES[0])


func footprint() -> Rect2:
	return Rect2(global_position - SIZE / 2.0, SIZE)


# Burning, or about to.
func is_active() -> bool:
	return phase == Phase.IGNITE or phase == Phase.BURNING


func burn_out() -> void:
	if not is_active():
		return
	_start(Phase.BURN_OUT, 0)
	_show(BURN_OUT_FRAMES[0])


func _physics_process(delta: float) -> void:
	frame_clock += delta
	phase_clock += delta
	match phase:
		Phase.IGNITE:
			while phase == Phase.IGNITE and frame_clock >= IGNITE_TIMES[step]:
				frame_clock -= IGNITE_TIMES[step]
				if step + 1 < IGNITE_FRAMES.size():
					step += 1
					_show(IGNITE_FRAMES[step])
				else:
					_start(Phase.BURNING, posmod(3 * trail_slot, BURN_LOOP_FRAMES.size()))
					_show(BURN_LOOP_FRAMES[step])
		Phase.BURNING:
			if phase_clock >= burn_time:
				burn_out()
			else:
				while frame_clock >= BURN_LOOP_TIME:
					frame_clock -= BURN_LOOP_TIME
					step = (step + 1) % BURN_LOOP_FRAMES.size()
					_show(BURN_LOOP_FRAMES[step])
		Phase.BURN_OUT:
			while phase == Phase.BURN_OUT and frame_clock >= BURN_OUT_TIMES[step]:
				frame_clock -= BURN_OUT_TIMES[step]
				if step + 1 < BURN_OUT_FRAMES.size():
					step += 1
					_show(BURN_OUT_FRAMES[step])
				else:
					_start(Phase.SCORCH, 0)
					sprite.texture = SCORCH_SHEET
					sprite.hframes = roundi(SCORCH_SHEET.get_width() / float(FRAME_WIDTH))
					sprite.frame = 0
		Phase.SCORCH:
			if phase_clock >= SCORCH_SMOULDER_TIME + SCORCH_FADE_TIME:
				queue_free()
			elif phase_clock >= SCORCH_SMOULDER_TIME:
				sprite.frame = 1
				sprite.modulate.a = 1.0 - (phase_clock - SCORCH_SMOULDER_TIME) / SCORCH_FADE_TIME
	_update_solid()


func _start(new_phase: Phase, first_step: int) -> void:
	phase = new_phase
	step = first_step
	frame_clock = 0.0
	phase_clock = 0.0


func _show(frame: int) -> void:
	sprite.frame = frame


# A patch that caught under the player stays passable until they've stepped fully off it.
func _update_solid() -> void:
	var in_solid_window := (phase == Phase.IGNITE and step >= SOLID_FROM_IGNITE_STEP) \
		or phase == Phase.BURNING \
		or (phase == Phase.BURN_OUT and step < SOLID_UNTIL_BURN_OUT_STEP)
	if not in_solid_window:
		if solid:
			_set_solid(false)
		return
	if solid or _player_too_close():
		return
	if may_turn_solid.is_valid() and not may_turn_solid.call(self):
		burn_out()
		return
	_set_solid(true)


func _player_too_close() -> bool:
	if not is_instance_valid(player):
		return false
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	var body := shape.global_transform * shape.shape.get_rect()
	return body.grow(PLAYER_CLEARANCE).intersects(footprint())


func _set_solid(on: bool) -> void:
	solid = on
	# Deferred: this can run inside a physics flush.
	collision.set_deferred("disabled", not on)
