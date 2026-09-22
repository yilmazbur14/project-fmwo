extends Node2D

# ONE OF COMPUTAH'S MINE PODS. He fires it out of his cannon, it lands on the mat, unfolds, and from
# then on it sits there with its ring lit until something steps in it or it runs out of charge.
#
# THE DRAWN RING IS THE TRIGGER AREA, to the texel. The shape below is built from
# ComputahArtLayout.mine_ring(), which is the measured bounding box of the cyan on the armed frames,
# and art_source/computah_redesign/checks.py mine_ring() fails the build if a single cyan pixel
# strays outside it. A player standing clear of the ring they can see is never caught by it. This is
# NuggetMeteorScript's HIT_SIZE == MARKER_SIZE rule, with the marker drawn into the sheet instead of
# laid on top of it - and it is why the pod's body is drawn so much smaller than its ring.
#
# IT IS NOT IN THE "enemy projectile" GROUP. It reports its own overlap, so it can tell the player's
# hurtbox from their dodge ghost and so Computah's own body is never even looked at: he cannot set
# one off, and a punch cannot clear one, because a punch's hitbox is not a hurtbox and a pod is not
# in "boss_target".
#
# IT STAYS IN HAZARD_GROUP, unlike Eric's dropped sword, which opts out because it is harmless
# scenery. A live minefield surviving a Break or the end of the fight would trap the player during
# something they cannot answer.
#
# FREEZE SAFETY: the phase clock is a Physics_Update accumulator and the lob is a node-bound tween,
# both of which a finisher's FightFreeze stops. A hit-stop must hold a laid mine.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/ComputahArtLayout.gd")

const MINE_ID := &"computah_mine"

@export var pod: Node2D
@export var lift: Node2D
@export var sprite: Sprite2D
@export var trigger: Area2D
@export var trigger_shape: CollisionShape2D

# The oval's rim, drawn off the measured ring rather than a capsule, which would bulge past its
# shoulders exactly as the nugget's would.
const TRIGGER_OVAL_POINTS := 32

enum Phase { FLIGHT, ARMING, ARMED, FADING, SPRUNG }

# Set by ComputahLayMines before the pod goes in, the way ComputahChase sets Caught's grabber. Every
# duration a pod runs on is one of the fight's own numbers, read through here.
var state_machine: Node = null

var phase := Phase.FLIGHT
var clock := 0.0
var caught := false


func _ready() -> void:
	sprite.texture = load(Layout.C_DIR + "computah_mine.png")
	sprite.hframes = roundi(sprite.texture.get_width() / Layout.MINE_FRAME.x)
	sprite.vframes = 1
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.offset = Layout.mine_offset()

	var ring := Layout.mine_ring()
	trigger_shape.position = ring.get_center()
	var oval := PackedVector2Array()
	for i in TRIGGER_OVAL_POINTS:
		oval.append(Vector2.from_angle(TAU * i / TRIGGER_OVAL_POINTS) * ring.size / 2.0)
	(trigger_shape.shape as ConvexPolygonShape2D).points = oval
	_show_phase()


# Fired out of his cannon and lobbed onto the spot this node already stands on. The arc is the pod's
# own offset coming back to nothing, so the node - and with it the trigger and the y-sort - is on the
# landing spot from the first frame.
func lob(from: Vector2) -> void:
	pod.position = from - global_position
	var flight: float = state_machine.mine_flight
	var arc := pod.position.length() * Layout.MINE_ARC_LIFT
	var throw := create_tween()
	throw.tween_property(pod, "position", Vector2.ZERO, flight)
	throw.parallel().tween_method(
		func(along: float) -> void: lift.position.y = -sin(along * PI) * arc, 0.0, 1.0, flight)


func _physics_process(delta: float) -> void:
	clock += delta
	match phase:
		Phase.FLIGHT:
			if clock >= state_machine.mine_flight:
				_set_phase(Phase.ARMING)
		Phase.ARMING:
			if clock >= state_machine.mine_arm:
				_set_phase(Phase.ARMED)
		Phase.ARMED:
			_check_player()
			if not caught and clock >= state_machine.mine_life:
				_set_phase(Phase.FADING)
		Phase.FADING:
			if clock >= state_machine.mine_fade:
				queue_free()
				return
		Phase.SPRUNG:
			pass
	_show_phase()


# Armed and waiting: the only phase that catches anything. A pod whose ring is breaking up has
# stopped promising a catch, and the promise the whole attack rests on is that the ring is the truth.
func is_armed() -> bool:
	return phase == Phase.ARMED and not caught


# Still worth keeping out of another pod's way. A fading pod is not: the lane it holds open is about
# to be free anyway.
func is_live() -> bool:
	return phase != Phase.FADING and not caught


# THE ONLY TRIGGER. Only the player's hurtbox counts: the dodge ghost is skipped without reporting a
# near miss, because computah_mine carries no dash_through and a perfect dodge would be a badge for a
# move the attack does not have.
func _check_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	for area in trigger.get_overlapping_areas():
		if area != player.hurtBox:
			continue
		if not state_machine.trap_allowed():
			# Refused, and NOT consumed: the pod stays armed for whatever the player does next.
			return
		# Reported through the player's own door, so the catch ends a parry streak and shows up in
		# the hit log like anything else that touches them. The result is deliberately not asked
		# for: the only IGNORED a pod can come back with is the i-frames from an earlier hit, and a
		# mine is a state rather than damage - being hit a moment ago is not a reason to walk
		# through one. A player who is already held is refused by trap_allowed() above instead.
		player.receive_hit(HitInfo.make(MINE_ID, self, global_position, state_machine.boss))
		caught = true
		state_machine.trap_player(self)
		return


# CUT SHORT. The ring breaks up and the pod frees itself on exactly the path running out of charge
# takes, so the end of a pod always looks the same however it was reached. The trigger goes with the
# phase, so it stops being able to catch anything on the instant while the picture plays out.
# A pod that is already breaking up, or one holding the player, is left alone: the trap owns that one.
func expire() -> void:
	if phase == Phase.FADING or caught:
		return
	_set_phase(Phase.FADING)
	_show_phase()


# The jaws shut. The trigger goes with them: a sprung pod is scenery until the trap lets go.
func spring() -> void:
	caught = true
	_set_phase(Phase.SPRUNG)
	_show_phase()


func _set_phase(new_phase: Phase) -> void:
	phase = new_phase
	clock = 0.0
	trigger.set_deferred("monitoring", new_phase == Phase.ARMED)


func _show_phase() -> void:
	var frames: Array = Layout.MINE_FRAMES[_phase_key()]
	var step := 0
	match phase:
		Phase.ARMING:
			step = mini(int(clock / maxf(state_machine.mine_arm, 0.01) * frames.size()), frames.size() - 1)
		Phase.ARMED:
			step = int(clock / Layout.MINE_PULSE_TIME) % frames.size()
		Phase.FADING:
			step = mini(int(clock / maxf(state_machine.mine_fade, 0.01) * frames.size()), frames.size() - 1)
		Phase.SPRUNG:
			step = int(clock / Layout.MINE_SPRUNG_FRAME_TIME) % frames.size()
	sprite.frame = frames[step]


func _phase_key() -> StringName:
	match phase:
		Phase.ARMING:
			return &"arming"
		Phase.ARMED:
			return &"armed"
		Phase.FADING:
			return &"fading"
		Phase.SPRUNG:
			return &"sprung"
	return &"flight"
