extends Node2D

# A spot of floor left burning by beast Bixby's Inferno (BixbyBeastInferno): it catches, burns for
# burn_time and burns out to a scorch mark, on the fire trail's frames. Unlike the trail's patches it is no
# wall, it hurts: from the frame it catches until it is burning out, standing in it costs a hit whenever the
# player's invincibility runs out, and a dash through it is safe (AttackCatalog: bixby_ember). His landing
# burns out any that would stand between the player and his punish window
# (BixbyBeastStateMachine.clear_fire_for_landing). Its timing all runs in _physics_process, so a freeze
# holds it.

const FirePatch := preload("res://Scripts/BixbyFirePatchScript.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

enum Phase { IGNITE, BURNING, BURN_OUT, SCORCH }

# What hurts, centred on the ember: the fire trail's burning bed.
const SIZE := FirePatch.SIZE
# Hurts from ignite frame 1 until burn-out frame 2 starts: the frames the trail's patches are solid on.
const HURTS_FROM_IGNITE_STEP := FirePatch.SOLID_FROM_IGNITE_STEP
const HURTS_UNTIL_BURN_OUT_STEP := FirePatch.SOLID_UNTIL_BURN_OUT_STEP

# Set by the attack before the ember enters the tree.
var burn_time := 10.0
# Neighbours are mirrored in turn and start their burn loops on different frames, so they don't flicker in
# step.
var slot := 0
var player: Node2D

var phase := Phase.IGNITE
var step := 0
var frame_clock := 0.0
var phase_clock := 0.0
var hurting := false

@onready var sprite: Sprite2D = $Sprite2D
@onready var hitbox: Area2D = $Hitbox


func _ready() -> void:
	hitbox.set_meta(HitInfo.META_ATTACK, &"bixby_ember")
	sprite.flip_h = posmod(slot, 2) == 1
	sprite.frame = FirePatch.IGNITE_FRAMES[0]


# What hurts, in px.
func footprint() -> Rect2:
	return Rect2(global_position - SIZE / 2.0, SIZE)


# Burning, or about to.
func is_active() -> bool:
	return phase == Phase.IGNITE or phase == Phase.BURNING


func is_hurting() -> bool:
	return hurting


func burn_out() -> void:
	if not is_active():
		return
	_start(Phase.BURN_OUT, 0)
	sprite.frame = FirePatch.BURN_OUT_FRAMES[0]


func _physics_process(delta: float) -> void:
	frame_clock += delta
	phase_clock += delta
	match phase:
		Phase.IGNITE:
			while phase == Phase.IGNITE and frame_clock >= FirePatch.IGNITE_TIMES[step]:
				frame_clock -= FirePatch.IGNITE_TIMES[step]
				if step + 1 < FirePatch.IGNITE_FRAMES.size():
					step += 1
					sprite.frame = FirePatch.IGNITE_FRAMES[step]
				else:
					_start(Phase.BURNING, posmod(3 * slot, FirePatch.BURN_LOOP_FRAMES.size()))
					sprite.frame = FirePatch.BURN_LOOP_FRAMES[step]
		Phase.BURNING:
			if phase_clock >= burn_time:
				burn_out()
			else:
				while frame_clock >= FirePatch.BURN_LOOP_TIME:
					frame_clock -= FirePatch.BURN_LOOP_TIME
					step = (step + 1) % FirePatch.BURN_LOOP_FRAMES.size()
					sprite.frame = FirePatch.BURN_LOOP_FRAMES[step]
		Phase.BURN_OUT:
			while phase == Phase.BURN_OUT and frame_clock >= FirePatch.BURN_OUT_TIMES[step]:
				frame_clock -= FirePatch.BURN_OUT_TIMES[step]
				if step + 1 < FirePatch.BURN_OUT_FRAMES.size():
					step += 1
					sprite.frame = FirePatch.BURN_OUT_FRAMES[step]
				else:
					_start(Phase.SCORCH, 0)
					sprite.texture = FirePatch.SCORCH_SHEET
					sprite.hframes = roundi(FirePatch.SCORCH_SHEET.get_width() / float(FirePatch.FRAME_WIDTH))
					sprite.frame = 0
		Phase.SCORCH:
			if phase_clock >= FirePatch.SCORCH_SMOULDER_TIME + FirePatch.SCORCH_FADE_TIME:
				queue_free()
				return
			elif phase_clock >= FirePatch.SCORCH_SMOULDER_TIME:
				sprite.frame = 1
				sprite.modulate.a = 1.0 - (phase_clock - FirePatch.SCORCH_SMOULDER_TIME) / FirePatch.SCORCH_FADE_TIME
	_update_hurting()
	_touch_player()


func _start(new_phase: Phase, first_step: int) -> void:
	phase = new_phase
	step = first_step
	frame_clock = 0.0
	phase_clock = 0.0


# The group is what the player's hurtbox and dodge ghost answer to (HitInfo), so it is the switch.
func _update_hurting() -> void:
	var now := (phase == Phase.IGNITE and step >= HURTS_FROM_IGNITE_STEP) \
		or phase == Phase.BURNING \
		or (phase == Phase.BURN_OUT and step < HURTS_UNTIL_BURN_OUT_STEP)
	if now == hurting:
		return
	hurting = now
	if hurting:
		hitbox.add_to_group("enemy projectile")
	else:
		hitbox.remove_from_group("enemy projectile")


# The group only reports a player walking in. One already standing in it as it catches, or still in it as
# the last hit's i-frames run out, has to be looked for, and the i-frames space those hits out.
func _touch_player() -> void:
	if hurting and is_instance_valid(player) and player.hurtBox.overlaps_area(hitbox):
		player.receive_hit(HitInfo.from_area(hitbox))
