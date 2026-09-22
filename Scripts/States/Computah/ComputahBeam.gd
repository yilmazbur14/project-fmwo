extends State

# ATTACK 1: THE CANNON BEAM. Four phases off one Physics_Update accumulator.
#
#   TRACK  beam_charge   braced, cannon charging, the aim line DIM, FLICKERING and SCROLLING and
#                        following the player every frame. No badge: nothing is answerable yet.
#   LOCK   instant       the origin AND the angle latch, and he snaps upright out of the brace.
#                        The line goes solid, bright and still, and the YELLOW dodge ring goes up
#                        for exactly beam_lock.
#   FIRE   beam_fire     the ring clears, the beam fires from the LATCHED origin down the LATCHED
#                        angle to the screen edge, hitbox live.
#   FADE   beam_fade     hitbox off, alpha to nothing. Then the vent window.
#
# THE RING'S LIFETIME IS THE LOCK-TO-FIRE WINDOW, AND THAT IS THE WHOLE READ. Raising it during the
# track would say "dodge now", the player would dodge, the aim would follow them, and the attack
# would have no read at all. Bixby's fire breath already tracks-then-locks the same way; this is
# that shape with a beam on the end of it.
#
# THE ORIGIN IS LATCHED AS WELL AS THE ANGLE, so what fires is a decided world-space ray and not a
# ray that still hangs off him: nothing the player does after the lock moves either. The drawn beam
# does ride the barrel back and out through the three recoil frames (_follow_barrel), because a beam
# left at the point it was fired from hangs in mid-air while the weapon kicks away from it.
#
# THE BEAM IS NOT IN THE "enemy projectile" GROUP. It reports its own hits by walking its overlaps
# and matching the player's hurtbox, which is the only thing that makes `dash_through` work on it -
# that group damages dashing players too. The same walk reports the near miss that pays a perfect
# dodge, exactly as the chase's catch does.
#
# FREEZE SAFETY: the clock is a Physics_Update accumulator and nothing here is on a tree timer.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/ComputahArtLayout.gd")

const BEAM_ID := &"computah_beam"

@export var body : CharacterBody2D
# The Node2D the beam hangs off: its scale is the on-screen beam thickness, its position the muzzle.
@export var rig : Node2D
# One LaserBeamProjectileScene instance, reused unchanged: its AimLine is what gives the tracking
# and locked looks their difference.
@export var beam : Area2D
@export var fx_layer : Node2D
@export var charge_sfx_player : AudioStreamPlayer
@export var lock_sfx_player : AudioStreamPlayer
@export var fire_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { TRACK, LOCKED, FIRE, FADE }

# JITTER SMOOTHING, NOT A DIFFICULTY KNOB. A player walking 600 px/s straight across the aim needs
# the line to turn 86 deg/s at 400 px of range, 344 deg/s at 100 px and 688 deg/s at 50 px, so 900
# never lets anybody outrun it at any range they can reach him from. All it does is stop the line
# snapping between frames and reading as a glitch. LOWERING IT WOULD MAKE THE CHARGE DODGEABLE and
# take the read off the lock, which is where the whole attack lives.
const BEAM_TRACK_TURN_RATE := 900.0

# In the beam scene's local units. The art is 23 px tall with a 1 px dark outline on each side; 21
# skips the outline so grazing the edge doesn't hurt.
const HITBOX_THICKNESS := 21.0
const BEAM_TEXTURE_HEIGHT := 23.0
const BEAM_TEXTURE_WIDTH := 16.0
const AIM_TEXTURE_WIDTH := 12.0
# Beam and hitbox start slightly behind the muzzle (hidden under the flare) so the gap between the
# cannon and his body isn't a safe pocket.
const BEAM_BACK_LENGTH := 6.0
# How long the fired beam takes to reach full length.
const BEAM_EXTEND_DURATION := 0.08

const AIM_FLICKER_TIME := 0.05
const AIM_DIM_ALPHA := 0.6
const AIM_SCROLL_SPEED := 40.0
const SHIMMER_FRAME_TIME := 0.06
const SHIMMER_SCROLL_SPEED := 90.0

const FIRE_SHAKE := 14.0
const FIRE_SHAKE_STEPS := 6
const FIRE_SHAKE_STEP_TIME := 0.03

# Recomputed on Enter so the beam always reaches the screen edge.
var beam_length := 0.0

var phase := Phase.TRACK
var elapsed := 0.0
# Latched at the lock and never touched again: what fires is this ray, not a ray off his arm.
var locked_origin := Vector2.ZERO
var locked_angle := 0.0

var glow: Node2D


func Enter() -> void:
	elapsed = 0.0
	phase = Phase.TRACK
	body.velocity = Vector2.ZERO
	body.set_solid(true)
	body.set_target_active(true)
	body.set_body_box(&"beam_brace")
	body.show_battery(false)
	# Faced once, here, and not again while he charges: the muzzle is on his cannon arm, so a flip
	# mid-charge would teleport the origin out from under the line the player is reading.
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(_aim_point(player))
	body.play_anim(&"beam_brace")

	beam_length = ceilf(beam.get_viewport_rect().size.length() / absf(beam.global_scale.x))
	locked_origin = body.muzzle_point()
	locked_angle = (_aim_point(player) - locked_origin).angle() if player else 0.0

	rig.global_position = locked_origin.round()
	beam.rotation = locked_angle
	beam.monitoring = false
	beam.modulate.a = 1.0
	var aim_line := beam.get_node("AimLine") as Sprite2D
	aim_line.region_rect.size.x = beam_length
	aim_line.visible = true
	beam.get_node("EmitterFlare").visible = true
	beam.get_node("Beam").visible = false
	rig.show()
	_set_beam_length(0.0)
	_update_track_fx()

	_show_glow(true)
	charge_sfx_player.play()


func Exit() -> void:
	charge_sfx_player.stop()
	ParryTell.clear(body)
	beam.monitoring = false
	beam.modulate.a = 1.0
	for part in ["AimLine", "Beam", "EmitterFlare"]:
		beam.get_node(part).visible = false
	rig.hide()
	_set_beam_length(0.0)
	_show_glow(false)


func Physics_Update(delta: float) -> void:
	elapsed += delta
	match phase:
		Phase.TRACK:
			_track(delta)
			if elapsed >= state_machine.beam_charge:
				_lock()
		Phase.LOCKED:
			if elapsed >= state_machine.beam_charge + _lock_time():
				_fire()
		Phase.FIRE:
			var fire_time: float = elapsed - state_machine.beam_charge - _lock_time()
			_follow_barrel()
			_set_beam_length(floorf(beam_length * clampf(fire_time / BEAM_EXTEND_DURATION, 0.0, 1.0)))
			_update_beam_fx()
			_damage_player()
			if fire_time >= state_machine.beam_fire:
				_start_fade()
		Phase.FADE:
			var fade_time: float = elapsed - state_machine.beam_charge - _lock_time() - state_machine.beam_fire
			_follow_barrel()
			beam.modulate.a = clampf(1.0 - fade_time / state_machine.beam_fade, 0.0, 1.0)
			_update_beam_fx()
			if fade_time >= state_machine.beam_fade:
				_vent()


# The lock-to-fire hold, never under the floor: this is the entire read the attack offers.
func _lock_time() -> float:
	return maxf(state_machine.beam_lock, state_machine.BEAM_LOCK_FLOOR)


# Past the point where being somewhere else is the only answer left. A mine may not close on the
# player from here (ComputahStateMachine.trap_allowed): the tracking charge is fine, because nothing
# is answerable yet, but once the aim has latched a hold would make the shot unanswerable.
func is_committed() -> bool:
	return phase != Phase.TRACK


#TRACKING

func _track(delta: float) -> void:
	var player: Node2D = state_machine.get_player()
	var origin: Vector2 = body.muzzle_point()
	rig.global_position = origin.round()
	if player:
		var wanted: float = (_aim_point(player) - origin).angle()
		beam.rotation = _turn_toward(beam.rotation, wanted, deg_to_rad(BEAM_TRACK_TURN_RATE) * delta)
	_update_track_fx()
	_grow_glow()


# The shortest way round, capped at `most` radians.
func _turn_toward(from: float, to: float, most: float) -> float:
	return from + clampf(angle_difference(from, to), -most, most)


# AIMED AT THE HURTBOX'S CENTRE, NEVER AT global_position: the player's origin is at their feet, and
# a beam laid along the floor reads as aimed at the floor rather than at them.
func _aim_point(player: Node2D) -> Vector2:
	if player == null:
		return Vector2.ZERO
	var box: Node = player.get("hurtBox")
	var shape: Node = box.get_node_or_null("CollisionShape2D") if box else null
	return shape.global_position if shape else player.global_position


#THE LOCK
# Everything the beam will do is decided in this one call and nothing after it moves.

func _lock() -> void:
	phase = Phase.LOCKED
	# THE POSE FIRST: he snaps upright out of the brace, which is the silhouette change the whole
	# read hangs on, and the muzzle below is read off the frame it leaves him on.
	body.play_anim(&"beam_ready")
	locked_origin = body.muzzle_point()
	locked_angle = beam.rotation
	rig.global_position = locked_origin.round()
	# Solid, bright, no flicker, no scroll: the line has stopped being a suggestion.
	var aim_line := beam.get_node("AimLine") as Sprite2D
	aim_line.modulate.a = 1.0
	aim_line.region_rect.position.x = 0.0
	beam.get_node("EmitterFlare").frame = 0
	_hold_glow()
	charge_sfx_player.stop()
	lock_sfx_player.play()
	# YELLOW, and only now. computah_beam carries `dodge_tell`, so ParryTell draws the dodge ring: no
	# guard and no parry answers a beam, and a player reading a red badge here would hold a guard
	# into it. It lives exactly as long as the hold does.
	ParryTell.telegraph(body, BEAM_ID, _lock_time(), body.tell_anchor)


func _fire() -> void:
	phase = Phase.FIRE
	ParryTell.clear(body)
	beam.get_node("AimLine").visible = false
	beam.get_node("Beam").visible = true
	beam.monitoring = true
	_show_glow(false)
	body.play_anim(&"beam_fire")
	# On the shot's own frame, not the one after it: the discharge pose has the barrel further out
	# than the lock did.
	_follow_barrel()
	fire_sfx_player.play()
	body.shake_screen(FIRE_SHAKE, FIRE_SHAKE_STEPS, FIRE_SHAKE_STEP_TIME)


# THE ANGLE IS LATCHED, THE BARREL IS NOT. The recoil drives the muzzle back into his shoulder and
# out again over three frames, and a beam left hanging at the point it was fired from comes away
# from the weapon for the whole of it. Only where the beam is drawn from moves; what it is aimed
# along was decided at the lock and is never touched again.
func _follow_barrel() -> void:
	rig.global_position = body.muzzle_point().round()


func _start_fade() -> void:
	phase = Phase.FADE
	_set_beam_length(beam_length)
	beam.monitoring = false


func _vent() -> void:
	state_machine.open_window(state_machine.beam_window, body.MAX_HITS_PER_WINDOW,
		&"vent", &"vent_hold", &"vent_up")


#HITS
# The beam is not in the "enemy projectile" group (that damages dashing players too): it reports its
# own hits, and PlayerDefense applies the dash-through rule the beam is built around.

func _damage_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	var near_miss := false
	for area in beam.get_overlapping_areas():
		if area == player.hurtBox:
			player.receive_hit(_hit())
			return
		if player.is_dodge_ghost(area):
			near_miss = true
	# Only where the player isn't: a beam through the spot a dash left is a perfect dodge.
	if near_miss:
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	return HitInfo.make(BEAM_ID, beam, rig.global_position, body)


#DRAWING

func _set_beam_length(length: float) -> void:
	var beam_sprite := beam.get_node("Beam") as Sprite2D
	beam_sprite.position.x = -BEAM_BACK_LENGTH
	beam_sprite.region_rect.size = Vector2(BEAM_BACK_LENGTH + length, BEAM_TEXTURE_HEIGHT)

	var hitbox := beam.get_node("CollisionShape2D") as CollisionShape2D
	var rect := hitbox.shape as RectangleShape2D
	rect.size = Vector2(BEAM_BACK_LENGTH + length, HITBOX_THICKNESS)
	hitbox.position.x = (length - BEAM_BACK_LENGTH) / 2.0


func _flicker_on(interval: float) -> bool:
	return int(elapsed / interval) % 2 == 0


func _update_track_fx() -> void:
	var flicker_on := _flicker_on(AIM_FLICKER_TIME)
	var aim_line := beam.get_node("AimLine") as Sprite2D
	aim_line.modulate.a = 1.0 if flicker_on else AIM_DIM_ALPHA
	aim_line.region_rect.position.x = fposmod(-floorf(elapsed * AIM_SCROLL_SPEED), AIM_TEXTURE_WIDTH)
	beam.get_node("EmitterFlare").frame = 0 if flicker_on else 1
	# The round flare stays upright so it keeps its pixel grid.
	beam.get_node("EmitterFlare").rotation = -beam.rotation


func _update_beam_fx() -> void:
	var shimmer_on := _flicker_on(SHIMMER_FRAME_TIME)
	var beam_sprite := beam.get_node("Beam") as Sprite2D
	beam_sprite.region_rect.position = Vector2(
		fposmod(-floorf(elapsed * SHIMMER_SCROLL_SPEED), BEAM_TEXTURE_WIDTH),
		0.0 if shimmer_on else BEAM_TEXTURE_HEIGHT)
	beam.get_node("EmitterFlare").frame = 0 if shimmer_on else 1
	beam.get_node("EmitterFlare").rotation = -beam.rotation


#THE CHARGE GLOW
# It swells at the muzzle over the whole track and then holds, so the charge is readable off his arm
# and not only off the aim line.

func _show_glow(on: bool) -> void:
	if not on:
		if glow:
			glow.hide()
		return
	if Layout.USE_FINAL_CHARGE_GLOW:
		return
	if glow == null:
		var spec := Layout.PLACEHOLDER_CHARGE_GLOW
		var shape := Polygon2D.new()
		shape.polygon = Layout.ellipse(spec.radii, spec.points)
		shape.material = Layout.additive()
		fx_layer.add_child(shape)
		glow = shape
	glow.color = Layout.PLACEHOLDER_CHARGE_GLOW.color
	glow.show()
	_grow_glow()


func _grow_glow() -> void:
	if glow == null or not glow.visible:
		return
	var spec := Layout.PLACEHOLDER_CHARGE_GLOW
	var along := clampf(elapsed / maxf(state_machine.beam_charge, 0.01), 0.0, 1.0)
	glow.global_position = body.frame_point(Layout.C_CHARGE_BALL).round()
	glow.scale = Vector2.ONE * lerpf(spec.from_scale, spec.to_scale, along)
	glow.modulate.a = lerpf(spec.from_alpha, spec.to_alpha, along)


func _hold_glow() -> void:
	if glow == null or not glow.visible:
		return
	var spec := Layout.PLACEHOLDER_CHARGE_GLOW
	# The soft ball collapses to the blown-out point the lock frame is drawn around.
	glow.global_position = body.frame_point(Layout.C_LOCK_BALL).round()
	glow.color = spec.locked_color
	glow.scale = Vector2.ONE * float(spec.locked_scale)
	glow.modulate.a = float(spec.to_alpha)
