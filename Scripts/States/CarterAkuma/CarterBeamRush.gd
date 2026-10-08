extends State

# Carter's second attack, the Beam Rush, in a single state:
#   SUMMON  0.70 s  four clones gather across the top of the ring, a fifth of it apart, and stay there.
#   CHARGE  1.20 s  each takes his Messatsu stance and gathers the ball at its palms; a violet line from
#                   each tracks the player and one lock ring closes on them.
#   LOCK    0.80 s  all four latch onto the player's hurtbox centre on one frame, run out to their full
#                   length and light up, and the yellow badge goes up over the lock on that same frame:
#                   dodge this. All of it is the escape.
#   STRING  1.30 s  all four fire on one frame. The heads land messatsu_travel later, and from then until
#                   the fade, beam_live, touching a band hurts.
#   FADE    0.30 s  the beams fade, then the next volley's charge: beam_volleys in all.
#   END     0.40 s  the four dissolve and he is left standing there, spent.
# Once in the attack, at a random moment in one of the charges, he teleports in beside the player and
# strikes - the badge, the read and the lunge his strike has always had - then warps back to where he
# stood.
#
# THE BEAMS ARE ESCAPED, NEVER PARRIED, by the user's call. They wear the Messatsu's sheets - its head,
# its flare and its body, but none of the surges that run down it - and they are their own attack,
# carter_rush_beam: no guard and no parry answers them, so the badge over the lock is the yellow one,
# and his strike is the one parry in the attack. With nothing running down them to time a hit by, a
# beam hurts on contact for as long as it is out, and the i-frames space the hits; a dash's immunity
# carries the player through one.
# Drawn as paint, nothing as light: the Messatsu's ball and lock are light only because they show in the
# dark, and violet added to the lit green mat washes to grey. The badge stands over the lock rather than
# over a clone: two of the four stand under the health bar, and the heads of all four are at the top
# edge of the view.
#
# ONE HIT AT A TIME, HOWEVER MANY BEAMS THE PLAYER STANDS IN: the first band holding them lands it, and
# the i-frames after it cover the rest. The four lock on one frame and fire on one frame, which is one
# read and one escape, where a staggered lock would be four.
#
# THE STRIKE NEVER LANDS WITH A BEAM. It comes in a charge, when nothing else hurts, and its blow is at
# least strike_clear before the lock (CarterStateMachine.strike_latest), so a player who stood rooted to
# parry it still has the whole escape ahead of them.
#
# A Break ends the attack on the spot and hands him straight to his Break's window, where the parried
# strike left him (on_broke): the four, their beams, the lines, the ring and both badges go with it.
# IF THE PLAYER NEVER MOVES THEY DIE, and that is the design: two hits a volley against the i-frames,
# beam_volleys volleys, and the strike. The player is NOT locked.
#
# IT IS ONE STATE ON PURPOSE, for the reason RagingDemon is one: the four, their beams, the hit sources
# and both badges have to be taken and given back as a unit, and a single release() funnel is the only
# way every failure path - a win, a loss, a finisher, a scene change - is provably safe. Do not split
# it into beats.
#
# FREEZE SAFETY: every wait here is a Physics_Update accumulator and every ramp a node-bound tween, both
# of which a pause and a finisher's FightFreeze stop with the rest of the fight. Nothing here may use
# get_tree().create_timer() or a tree-level create_tween().

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const STRIKE_ID := &"carter_teleport_strike"
const BEAM_ID := &"carter_rush_beam"

# How far inside the ropes he may materialise.
const WARP_MARGIN := 90.0
# He pulls up this far short of the point he latched onto, so the blow lands beside the player rather
# than with him standing inside them.
const LUNGE_STANDOFF := 96.0
# The badge sits here over his feet. NOT get_daze_anchor(), which is tuned for the kneeling recovery
# pose and would put it in the middle of his chest while he is standing.
const TELL_ANCHOR := Vector2(0, -300)
# The badge over the lock stands on the closed ring's top edge, over the head of a player still in it.
const LOCK_TELL_RISE := 48.0
# Where his strike's badge goes when over his head would be under the HUD or off the view: beside his
# head, clear of his body, and failing that under his feet (CarterArtLayout.clear_tell_anchor).
const TELL_BESIDE := Vector2(158, -198)
const TELL_BELOW := Vector2(0, 88)
# The four gather one after another rather than all at once, so the ring fills from one side.
const CLONE_FORM_TIME := 0.22
const CLONE_FORM_STAGGER := 0.08
const CLONE_GO_TIME := 0.18
# As CarterMessatsu's: summed 1/60 s steps fall a hair short of a round number, which would land every
# beat a frame after the time it is written at.
const CLOCK_SLACK := 0.0001

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { SUMMON, CHARGE, LOCK, STRING, FADE, END }
enum Strike { WAITING, SHOW, LUNGE, HOLD, DONE }


# One of the four at the top and the beam it fires. The volley's clock and the lock are the attack's;
# the aim is each one's own.
class Caster:
	var figure: Sprite2D
	var pose := &""
	var pose_since := 0.0
	var ball: Node2D
	var aim_line: Line2D
	var beam_root: Node2D
	var beam_parts: Array[Node2D] = []
	var flare: Node2D
	var head: Node2D
	# The one hit source a beam reports as, all the time it is out.
	var source: Node2D
	var aim_origin := Vector2.ZERO
	var aim_angle := 0.0
	# From its palms to the lock: the head covers it in messatsu_travel.
	var head_distance := 0.0


var beat := Beat.SUMMON
var beat_clock := 0.0
# What every looping sheet steps off, each from the moment it was made.
var fx_clock := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# Whether the gauge broke here, which decides the window this hands over to.
var broke := false
var volley := 0

var casters: Array[Caster] = []
var lock_ring: Node2D
# The player's hurtbox centre on the frame the four locked, which is where their lines cross.
var lock_point := Vector2.ZERO
var beam_frames: Array[Texture2D] = []
# The one parent of every hit source here, with nothing drawn in it: see _hit_source().
var source_holder: Node2D

# From the frame the four fire.
var fire_clock := 0.0
# Whether the beams are out and hurting: from the heads landing to the fade.
var live := false

# Where he stands through the attack, and goes back to after the strike.
var home := Vector2.ZERO
var strike := Strike.WAITING
var strike_clock := 0.0
var strike_volley := 0
var strike_at := 0.0
# Which side of the player he comes in on: +1 their right, -1 their left.
var strike_side := 1.0
# Where he came in, and the point the strike was latched to when the badge came down.
var lunge_from := Vector2.ZERO
var strike_point := Vector2.ZERO
# Where each badge's tip stands, picked clear of the HUD as it goes up: nothing it hangs over moves
# while it is up.
var lock_tell_at := Vector2.ZERO
var strike_tell_at := Vector2.ZERO
# For a test or a still that has to know when the strike comes; -1 picks it at random.
var forced_strike_volley := -1
var forced_strike_at := -1.0


func Enter() -> void:
	released = false
	broke = false
	beat = Beat.SUMMON
	beat_clock = 0.0
	fx_clock = 0.0
	volley = 0
	live = false
	home = body.global_position
	strike = Strike.WAITING
	strike_clock = 0.0
	strike_side = 1.0 if randi() % 2 == 0 else -1.0
	strike_volley = forced_strike_volley if forced_strike_volley >= 0 else randi() % state_machine.beam_volleys
	strike_at = forced_strike_at if forced_strike_at >= 0.0 else randf_range(state_machine.strike_from, state_machine.strike_latest())

	body.velocity = Vector2.ZERO
	body.show_body(true)
	# His emblem stays out for this one: its offset is measured on the frame where his back is turned,
	# and every pose here faces the player.
	body.show_mark_glow(false)
	body.play_anim(&"summon")
	body.flash_sfx_player.play()
	_build_casters()
	_build_lock_ring()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent, and called from Exit(), _exit_tree() and CarterStateMachine._end_fight(). A terminal
# path that skips Exit() would otherwise leave four beams standing and a badge over a boss who has
# already lost the fight.
func release() -> void:
	if released:
		return
	released = true
	live = false
	strike = Strike.DONE
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.charge_sfx_player.stop()
		body.show_body(true)
		body.show_mark_glow(false)
		body.sprite.flip_h = false
	if is_instance_valid(lock_ring):
		ParryTell.clear(lock_ring)
	_clear_beams()
	for caster in casters:
		for node in [caster.figure, caster.ball, caster.aim_line]:
			if is_instance_valid(node):
				node.queue_free()
	casters.clear()
	for node in [lock_ring, source_holder]:
		if is_instance_valid(node):
			node.queue_free()


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	fx_clock += delta
	_step_poses()
	_step_sheets()
	_step_see_through(delta)
	_advance_strike(delta)
	if beat != Beat.END and not _striking():
		_face(body.sprite, body.global_position.x)
	match beat:
		Beat.SUMMON:
			if _due(beat_clock, state_machine.beam_summon):
				body.play_anim(&"idle")
				_begin_charge()
		Beat.CHARGE:
			for caster in casters:
				_face(caster.figure, caster.figure.global_position.x)
				_track(caster)
			_draw_charge()
			if _due(beat_clock, state_machine.beam_charge):
				_lock()
		Beat.LOCK:
			if _due(beat_clock, state_machine.beam_escape):
				_fire()
		Beat.STRING:
			_advance_string(delta)
		Beat.FADE:
			_advance_fade()
		Beat.END:
			if _due(beat_clock, state_machine.beam_end):
				_hand_over()


func _due(clock: float, at: float) -> bool:
	return clock >= at - CLOCK_SLACK


#THE GAUGE
# It is his fight-long gauge, not this attack's: it comes in holding whatever the attacks before it put
# there. His strike is the one read this attack offers, and a beam's hit costs one.

# His Break, deferred here from CarterAkumaScript._on_break through the state machine. The gauge fills
# inside a physics flush, where states cannot switch. No END beat: the user wants him hittable at once
# (2026-09-27), so release() takes everything of the attack as he is handed over.
func on_broke() -> void:
	if released:
		return
	broke = true
	_hand_over()


#THE FOUR AT THE TOP
# No light over the head and no hurtbox. This fight already teaches one clone read - red parry, yellow
# feint - and those lights stay the barrage's.

func _build_casters() -> void:
	var player := _player()
	for i in CarterArtLayout.BEAM_COUNT:
		var caster := Caster.new()
		var figure := Sprite2D.new()
		figure.scale = Vector2.ONE * CarterArtLayout.SCALE
		figure.z_index = CarterArtLayout.BEAM_CLONE_Z
		figure.modulate = CarterArtLayout.BEAM_CLONE_TINT
		figure.modulate.a = 0.0
		var at := Vector2(CarterArtLayout.BEAM_X[i], CarterArtLayout.BEAM_CLONE_Y)
		figure.flip_h = player != null and player.global_position.x < at.x
		caster.figure = figure
		_pose(caster, &"messatsu_charge")
		state_machine.add_hazard(figure, at, body.clone_layer)
		var form := figure.create_tween()
		form.tween_interval(i * CLONE_FORM_STAGGER)
		form.tween_property(figure, "modulate:a", CarterArtLayout.BEAM_CLONE_TINT.a, CLONE_FORM_TIME)
		caster.ball = _build_ball()
		caster.aim_line = _build_aim_line()
		casters.append(caster)


func _pose(caster: Caster, anim_name: StringName) -> void:
	var anim := CarterArtLayout.anim(anim_name)
	var sheet: Texture2D = load(anim.sheet)
	var frame_size: Vector2 = anim.get("frame_size", CarterArtLayout.FRAME_SIZE)
	caster.pose = anim_name
	caster.pose_since = fx_clock
	# Back to the first frame before the frame count changes, so the current one can't be out of range.
	caster.figure.frame = 0
	caster.figure.texture = sheet
	caster.figure.hframes = roundi(sheet.get_width() / frame_size.x)
	caster.figure.offset = CarterArtLayout.sheet_offset(frame_size)
	caster.figure.frame = anim.frames[0]


func _step_poses() -> void:
	for caster in casters:
		caster.figure.frame = _pose_frame(CarterArtLayout.anim(caster.pose), fx_clock - caster.pose_since)


# The frame `anim` is on `clock` seconds in, `times` repeating its last value as every animation in
# CarterArtLayout does. One that doesn't loop holds its last frame, as his own do.
func _pose_frame(anim: Dictionary, clock: float) -> int:
	var frames: Array = anim.frames
	var times: Array = anim.times
	var total := 0.0
	for i in frames.size():
		total += times[mini(i, times.size() - 1)]
	var into := clock + CLOCK_SLACK
	if anim.loop:
		into = fposmod(into, maxf(total, 0.0001))
	for i in frames.size():
		into -= times[mini(i, times.size() - 1)]
		if into < 0.0:
			return frames[i]
	return frames[frames.size() - 1]


# A figure the player's sprite overlaps goes see-through (CarterArtLayout.BEAM_CLONE_SEE_THROUGH): the four are
# on the clone layer, over every fighter, and the whole top strip of the ring is behind one of them. On
# self_modulate, so it multiplies with the fades in and out their own modulate runs.
func _step_see_through(delta: float) -> void:
	var player := _player()
	var seen := Rect2()
	if player != null:
		seen = player.sprite.get_global_transform() * player.sprite.get_rect()
	var step := delta / CarterArtLayout.BEAM_CLONE_SEE_THROUGH_TIME
	for caster in casters:
		var drawn: Rect2 = caster.figure.get_global_transform() * caster.figure.get_rect()
		var target := CarterArtLayout.BEAM_CLONE_SEE_THROUGH if player != null and drawn.intersects(seen) else 1.0
		caster.figure.self_modulate.a = move_toward(caster.figure.self_modulate.a, target, step)


# Round to the player only once they are well past the centre line, so walking across in front of one
# can't flicker it.
func _face(sprite: Sprite2D, from_x: float) -> void:
	var player := _player()
	if player == null:
		return
	var past: float = player.global_position.x - from_x
	var hysteresis := CarterArtLayout.MESSATSU_FACE_HYSTERESIS
	if sprite.flip_h and past > hysteresis:
		sprite.flip_h = false
	elif not sprite.flip_h and past < -hysteresis:
		sprite.flip_h = true


#A VOLLEY

func _begin_charge() -> void:
	beat = Beat.CHARGE
	beat_clock = 0.0
	for caster in casters:
		_pose(caster, &"messatsu_charge")
		_track(caster)
		caster.ball.show()
		caster.aim_line.default_color = CarterArtLayout.PLACEHOLDER_MESSATSU_LINE.color
		caster.aim_line.show()
	lock_ring.show()
	_draw_charge()
	body.charge_sfx_player.play()


# Straight onto the player's hurtbox centre, every step, with no turn rate.
func _track(caster: Caster) -> void:
	caster.aim_origin = _muzzle(caster)
	var to := _player_centre() - caster.aim_origin
	if to.length() >= CarterArtLayout.MESSATSU_MIN_AIM:
		caster.aim_angle = to.angle()


func _draw_charge() -> void:
	var grown := clampf(beat_clock / maxf(state_machine.beam_charge, 0.0001), 0.0, 1.0)
	var ball_spec := CarterArtLayout.messatsu_ball()
	var drawn_at: float = ball_spec.get("scale", 1.0)
	var line := CarterArtLayout.PLACEHOLDER_MESSATSU_LINE
	var dim := int(beat_clock / line.flicker_time) % 2 == 1
	var target := _player_centre()
	for caster in casters:
		caster.ball.global_position = caster.aim_origin.round()
		caster.ball.scale = Vector2.ONE * drawn_at * lerpf(ball_spec.from_scale, 1.0, grown)
		caster.aim_line.global_position = caster.aim_origin.round()
		caster.aim_line.points = PackedVector2Array([Vector2.ZERO, (target - caster.aim_line.global_position).round()])
		caster.aim_line.default_color.a = line.flicker_alpha if dim else line.color.a
	_draw_lock(grown, target)


# The sheet's frames are the lock clicking shut and its scale the squeeze on top of them; the
# placeholder only squeezes.
func _draw_lock(grown: float, at: Vector2) -> void:
	var spec := CarterArtLayout.messatsu_lock()
	if spec.has("texture"):
		var frames: int = spec.hframes
		(lock_ring as Sprite2D).frame = mini(int(grown * frames), frames - 1)
		lock_ring.scale = Vector2.ONE * spec.scale * lerpf(spec.from_scale, 1.0, grown)
	else:
		(lock_ring as Line2D).points = CarterArtLayout.ellipse(Vector2.ONE * lerpf(spec.from, spec.to, grown), spec.points)
	lock_ring.global_position = at.round()


# From here on nothing of the four moves: each line runs out along its latched aim to the length its
# beam will have, so the player sees all of what is about to fire, past them as well as up to them.
# THE BADGE GOES UP ON THE LOCK, NOT AFTER IT. The lock is when the escape starts, so it is the real
# cue; a badge that came messatsu_tell before the fire, 0.50 s after the lock, only taught a player
# who waited for it to start late (the 2026-10-04 playtest: a first attempt's wins fell from 55% to
# 30%). The beams can't be parried, so nothing is re-armed here: this is a cue to be gone, not a
# timing.
func _lock() -> void:
	beat = Beat.LOCK
	beat_clock = 0.0
	lock_point = _player_centre()
	_draw_lock(1.0, lock_point)
	var ball_spec := CarterArtLayout.messatsu_ball()
	var drawn_at: float = ball_spec.get("scale", 1.0)
	for caster in casters:
		_track(caster)
		caster.ball.global_position = caster.aim_origin.round()
		caster.ball.scale = Vector2.ONE * drawn_at
		caster.aim_line.global_position = caster.aim_origin.round()
		caster.aim_line.points = PackedVector2Array([Vector2.ZERO,
			(Vector2.from_angle(caster.aim_angle) * CarterArtLayout.MESSATSU_LENGTH).round()])
		caster.aim_line.default_color = CarterArtLayout.PLACEHOLDER_MESSATSU_LINE.lit_color
	lock_tell_at = CarterArtLayout.clear_tell_anchor(_lock_tell_anchors())
	ParryTell.telegraph(lock_ring, BEAM_ID, state_machine.beam_escape, _lock_tell_anchor)
	body.charge_sfx_player.stop()
	body.lights_sfx_player.play()


func _lock_tell_anchor() -> Vector2:
	return lock_tell_at


# Over the closed ring, under it, or beside it, right then left.
func _lock_tell_anchors() -> Array:
	var badge := CarterArtLayout.TELL_BADGE
	return [
		lock_point + Vector2(0.0, -LOCK_TELL_RISE),
		lock_point + Vector2(0.0, LOCK_TELL_RISE + badge.size.y),
		lock_point + Vector2(LOCK_TELL_RISE - badge.position.x, badge.size.y / 2.0),
		lock_point + Vector2(-LOCK_TELL_RISE - badge.end.x, badge.size.y / 2.0),
	]


func _fire() -> void:
	beat = Beat.STRING
	beat_clock = 0.0
	fire_clock = 0.0
	live = false
	ParryTell.clear(lock_ring)
	lock_ring.hide()
	for caster in casters:
		caster.head_distance = maxf(caster.aim_origin.distance_to(lock_point), CarterArtLayout.MESSATSU_MIN_AIM)
		caster.source = _hit_source(caster.aim_origin)
		caster.ball.hide()
		caster.aim_line.hide()
		_pose(caster, &"messatsu_fire")
	# In draw order on the floor layer: the four bodies, the flares over their flat starts, and the heads
	# over all of it, so where two cross neither buries the other's head as it lands.
	for caster in casters:
		_build_beam(caster)
	for caster in casters:
		_build_flare(caster)
	for caster in casters:
		_build_head(caster)
	_step_beams()
	body.shake_screen(CarterArtLayout.MESSATSU_FIRE_SHAKE, CarterArtLayout.MESSATSU_FIRE_SHAKE_STEPS,
		CarterArtLayout.MESSATSU_FIRE_SHAKE_STEP_TIME)
	body.fire_sfx_player.play()


# Harmless until the heads land, then touching a band hurts until the fade. On the frame they land, a
# band reaching the spot a dash has just left is a perfect dodge.
func _advance_string(delta: float) -> void:
	fire_clock += delta
	_step_beams()
	if not _due(fire_clock, state_machine.messatsu_travel):
		return
	var landing := not live
	live = true
	if not _beam_contact() and landing:
		_near_miss()
	if _due(fire_clock, state_machine.messatsu_travel + state_machine.beam_live):
		live = false
		beat = Beat.FADE
		beat_clock = 0.0
		_fade_beams(state_machine.messatsu_fade)


func _advance_fade() -> void:
	if not _due(beat_clock, state_machine.messatsu_fade):
		return
	_clear_beams()
	volley += 1
	if volley < state_machine.beam_volleys:
		_begin_charge()
	else:
		_begin_end()


# Each head crosses to the lock in messatsu_travel, and once they are there the beams run out to full
# length. A body only starts MESSATSU_BEAM_START out, under its flare.
func _step_beams() -> void:
	var arrived := _due(fire_clock, state_machine.messatsu_travel)
	var spec := CarterArtLayout.messatsu_beam()
	for caster in casters:
		var reach: float = CarterArtLayout.MESSATSU_LENGTH
		if not arrived:
			reach = caster.head_distance * fire_clock / maxf(state_machine.messatsu_travel, 0.0001)
		var length := maxf(reach - CarterArtLayout.MESSATSU_BEAM_START, 0.0)
		for part in caster.beam_parts:
			part.visible = length > 0.0
			if spec.has("texture"):
				(part as Sprite2D).region_rect = Rect2(CarterArtLayout.MESSATSU_BEAM_START / spec.scale, 0.0,
					length / spec.scale, spec.frame_size.y)
			elif part.visible:
				part.scale.x = length
		caster.head.global_position = (caster.aim_origin + Vector2.from_angle(caster.aim_angle) * reach).round()
		caster.head.visible = not arrived


# Whether a band holds the player this step. The first one that does reports the hit for all four; not
# while they flash, since the beams don't pass the i-frames and reporting into them would only be noise.
# The hit's origin is the player's own hurtbox centre, as the Messatsu's is.
func _beam_contact() -> bool:
	var player := _player()
	if player == null or player.playerHealth <= 0:
		return false
	var box := _rect_of(player.hurtBox.get_node("CollisionShape2D"))
	for caster in casters:
		if not _in_band(caster, box):
			continue
		if not player.is_invincible:
			var contact := box.get_center()
			if player.receive_hit(HitInfo.make(BEAM_ID, caster.source, contact, body)) == HitInfo.Result.HIT:
				body.spawn_burst(false, contact)
				body.strike_sfx_player.play()
				body.shake_screen(CarterArtLayout.MESSATSU_HIT_SHAKE, CarterArtLayout.MESSATSU_HIT_SHAKE_STEPS,
					CarterArtLayout.MESSATSU_HIT_SHAKE_STEP_TIME)
		return true
	return false


func _near_miss() -> void:
	var player := _player()
	if player == null or player.dodge_ghost_position() == Vector2.INF:
		return
	var ghost := _rect_of(player.dodge_ghost.get_node("CollisionShape2D"))
	for caster in casters:
		if _in_band(caster, ghost):
			player.receive_near_miss(HitInfo.make(BEAM_ID, caster.source, ghost.get_center(), body))
			return


# The Messatsu's band against a box: within half the hit width of the latched axis, the box's own reach
# across it included, and not wholly more than MESSATSU_BACK behind the palms.
func _in_band(caster: Caster, box: Rect2) -> bool:
	var dir := Vector2.from_angle(caster.aim_angle)
	var n := dir.orthogonal()
	var c := box.get_center() - caster.aim_origin
	var half := box.size / 2.0
	var across := CarterArtLayout.MESSATSU_HIT_WIDTH / 2.0 + half.x * absf(n.x) + half.y * absf(n.y)
	var reach := c.dot(dir) + half.x * absf(dir.x) + half.y * absf(dir.y)
	return absf(c.dot(n)) <= across and reach >= -CarterArtLayout.MESSATSU_BACK


func _fade_beams(seconds: float) -> void:
	for caster in casters:
		for node in [caster.beam_root, caster.flare, caster.head]:
			if is_instance_valid(node):
				var out: Tween = node.create_tween()
				out.tween_property(node, "modulate:a", 0.0, seconds)


func _clear_beams() -> void:
	for caster in casters:
		for node in [caster.beam_root, caster.flare, caster.head, caster.source]:
			if is_instance_valid(node):
				node.queue_free()
		caster.beam_parts.clear()


#THE END

func _begin_end() -> void:
	beat = Beat.END
	beat_clock = 0.0
	live = false
	strike = Strike.DONE
	ParryTell.clear(body)
	ParryTell.clear(lock_ring)
	lock_ring.hide()
	for caster in casters:
		caster.ball.hide()
		caster.aim_line.hide()
		var gone := caster.figure.create_tween()
		gone.tween_property(caster.figure, "modulate:a", 0.0, CLONE_GO_TIME)
	_fade_beams(state_machine.beam_end)
	body.charge_sfx_player.stop()
	# His punish pose's hurtbox is laid out facing right.
	body.sprite.flip_h = false
	body.play_anim(&"idle")
	body.finish_sfx_player.play()


func _hand_over() -> void:
	var owed: bool = state_machine.take_break_owed()
	var recover: State = state_machine.states.get("Recover")
	if recover:
		# Nothing is banked here: what the attack read well earns is a Break's window, and prepare()
		# zeroes the barrage's own tally so its banked damage cannot be cashed in a second time.
		recover.prepare(0, 0, 0, 0,
			state_machine.recover_break if broke else state_machine.recover_spent, broke or owed)
		if state_machine.chains_on(self, recover):
			state_machine.chain_on(recover)
			return
	state_machine.on_child_transition(self, "Recover")


#THE STRIKE

func _striking() -> bool:
	return strike == Strike.SHOW or strike == Strike.LUNGE or strike == Strike.HOLD


func _advance_strike(delta: float) -> void:
	match strike:
		Strike.WAITING:
			if beat == Beat.CHARGE and volley == strike_volley and _due(beat_clock, strike_at):
				_start_strike()
		Strike.SHOW:
			strike_clock += delta
			if _due(strike_clock, state_machine.strike_show):
				strike = Strike.LUNGE
				_launch_strike()
				_drive_lunge()
		Strike.LUNGE:
			strike_clock += delta
			_drive_lunge()
			if _due(strike_clock, state_machine.strike_show + state_machine.strike_dash):
				strike = Strike.HOLD
				_contact()
		Strike.HOLD:
			strike_clock += delta
			if _due(strike_clock, state_machine.strike_show + state_machine.strike_dash + state_machine.strike_gap):
				strike = Strike.DONE
				_go_home()


func _start_strike() -> void:
	strike = Strike.SHOW
	strike_clock = 0.0
	var player := _player()
	var at: Vector2 = player.global_position if player else state_machine.ARENA_CENTRE
	body.global_position = _warp_spot(at)
	lunge_from = body.global_position
	body.play_anim(&"rush")
	_face_strike()
	body.play_rush(strike_volley)
	# The badge comes up on the frame he does, and the parry is re-armed on that same frame, as it is for
	# every read in this fight: a press whiffed on anything before it can't make it unparryable.
	strike_tell_at = CarterArtLayout.clear_tell_anchor(_strike_tell_anchors())
	ParryTell.telegraph(body, STRIKE_ID, state_machine.strike_show, _tell_anchor)
	state_machine.rearm_parry()


# Beside the player, jittered off their line and always inside the ropes.
func _warp_spot(at: Vector2) -> Vector2:
	var bounds: Rect2 = state_machine.ROPES.grow(-WARP_MARGIN)
	var reach := randf_range(state_machine.strike_range.x, state_machine.strike_range.y)
	var y: float = at.y + randf_range(-state_machine.strike_y_jitter, state_machine.strike_y_jitter)
	var spot := Vector2(at.x + strike_side * reach, y).clamp(bounds.position, bounds.end)
	# Against the ropes the clamp can drop him in their lap, so the SIDE gives way rather than the
	# distance: he is meant to arrive a read away, never already on top of them.
	if absf(spot.x - at.x) < state_machine.strike_range.x:
		strike_side = -strike_side
		spot = Vector2(at.x + strike_side * reach, y).clamp(bounds.position, bounds.end)
	return spot.round()


# Both rush sheets are drawn travelling right, so the strike from the player's right mirrors them.
func _face_strike() -> void:
	body.sprite.flip_h = strike_side > 0.0


# The badge comes down and the lunge starts. The destination is LATCHED here, on the player's hurtbox
# centre this frame, and nothing moves it afterwards. What the player does with the 0.08 s after this
# is the whole of their second answer.
func _launch_strike() -> void:
	ParryTell.clear(body)
	strike_point = _player_centre()
	body.play_anim(&"rush_pass")
	_face_strike()


func _drive_lunge() -> void:
	var weight := clampf((strike_clock - state_machine.strike_show) / maxf(state_machine.strike_dash, 0.0001), 0.0, 1.0)
	var toward := strike_point + Vector2(strike_side * LUNGE_STANDOFF, 0.0)
	body.global_position = lunge_from.lerp(toward, weight).round()


# The contact instant. The player is free to move, so a strike can WHIFF: out of the box around the
# point it latched onto, nothing lands and nothing feeds the gauge. The hit's origin is the player's own
# hurtbox centre, inside PlayerDefense.block_omni_radius, so any facing answers it.
func _contact() -> void:
	var player := _player()
	if player == null:
		return
	var centre := _player_centre()
	var reach: float = state_machine.strike_reach
	if absf(centre.x - strike_point.x) > reach or absf(centre.y - strike_point.y) > reach:
		return
	var result: int = player.receive_hit(HitInfo.make(STRIKE_ID, _hit_source(centre), centre, body))
	if result == HitInfo.Result.PARRIED:
		body.break_sfx_player.play()
	elif result != HitInfo.Result.IGNORED:
		body.strike_sfx_player.play()


# Back where he stood, the way he came: at once.
func _go_home() -> void:
	var player := _player()
	body.global_position = home
	body.sprite.flip_h = player != null and player.global_position.x < home.x
	body.play_anim(&"idle")
	body.yank_sfx_player.play()


func _tell_anchor() -> Vector2:
	return strike_tell_at


# Over his head, beside it on the side away from the player, beside it on the near side, or under his
# feet.
func _strike_tell_anchors() -> Array:
	var feet: Vector2 = body.global_position
	return [
		feet + TELL_ANCHOR,
		feet + Vector2(TELL_BESIDE.x * strike_side, TELL_BESIDE.y),
		feet + Vector2(-TELL_BESIDE.x * strike_side, TELL_BESIDE.y),
		feet + TELL_BELOW,
	]


#WHAT IS DRAWN
# The Messatsu's sheets, or their placeholders while its USE_FINAL_MESSATSU_* flags are off, all of it
# paint (see the header), and none of its surges. The balls, the lines and the lock are on the clone
# layer; the beams, flares and heads on the floor layer, under both fighters.

func _build_ball() -> Node2D:
	var spec := CarterArtLayout.messatsu_ball()
	var ball: Node2D
	if spec.has("texture"):
		ball = _sheet(spec)
	else:
		ball = _ellipse(Vector2.ONE * spec.radius, spec.points, spec.color)
	ball.z_index = CarterArtLayout.BEAM_BALL_Z
	ball.hide()
	state_machine.add_hazard(ball, Vector2.ZERO, body.clone_layer)
	return ball


func _build_aim_line() -> Line2D:
	var spec := CarterArtLayout.PLACEHOLDER_MESSATSU_LINE
	var line := Line2D.new()
	line.width = spec.width
	line.default_color = spec.color
	line.hide()
	state_machine.add_hazard(line, Vector2.ZERO, body.clone_layer)
	return line


func _build_lock_ring() -> void:
	var spec := CarterArtLayout.messatsu_lock()
	if spec.has("texture"):
		lock_ring = _sheet(spec)
	else:
		var ring := Line2D.new()
		ring.width = spec.width
		ring.default_color = spec.color
		ring.closed = true
		lock_ring = ring
	lock_ring.hide()
	state_machine.add_hazard(lock_ring, Vector2.ZERO, body.clone_layer)


# Along the latched axis from the palms, from MESSATSU_BEAM_START out, and stretched to the beam's reach
# every step. The sheet's body is one frame repeated down the region, swapped for the next as the beam
# flows; the placeholder's is a body and a core, quads one px long.
func _build_beam(caster: Caster) -> void:
	var spec := CarterArtLayout.messatsu_beam()
	caster.beam_root = Node2D.new()
	caster.beam_root.rotation = caster.aim_angle
	caster.beam_parts.clear()
	if spec.has("texture"):
		var pivot: Vector2 = spec.pivot
		var tiled := Sprite2D.new()
		tiled.texture = _beam_frames(spec)[0]
		tiled.centered = false
		tiled.offset = -pivot
		tiled.scale = Vector2.ONE * spec.scale
		tiled.region_enabled = true
		tiled.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
		tiled.set_meta(&"since", fx_clock)
		caster.beam_parts.append(tiled)
	else:
		for part in [[CarterArtLayout.MESSATSU_DRAW_WIDTH, spec.color], [spec.core_width, spec.core_color]]:
			var width: float = part[0]
			var quad := Polygon2D.new()
			quad.polygon = CarterArtLayout.rect_polygon(Rect2(0.0, -width / 2.0, 1.0, width))
			quad.color = part[1]
			caster.beam_parts.append(quad)
	for part in caster.beam_parts:
		part.position.x = CarterArtLayout.MESSATSU_BEAM_START
		caster.beam_root.add_child(part)
	state_machine.add_hazard(caster.beam_root, caster.aim_origin, body.floor_layer)


# Cut apart the first time they fire: region repeat tiles a whole texture, so the sheet's four frames
# side by side would tile as one.
func _beam_frames(spec: Dictionary) -> Array[Texture2D]:
	if beam_frames.is_empty():
		var sheet := (load(spec.texture) as Texture2D).get_image()
		var size := Vector2i(spec.frame_size)
		for k in spec.hframes:
			beam_frames.append(ImageTexture.create_from_image(sheet.get_region(Rect2i(Vector2i(k * size.x, 0), size))))
	return beam_frames


func _build_flare(caster: Caster) -> void:
	var spec := CarterArtLayout.messatsu_flare()
	if spec.has("texture"):
		caster.flare = _sheet(spec)
	else:
		caster.flare = _ellipse(spec.radii, spec.points, spec.color)
		(caster.flare as Polygon2D).offset = Vector2(spec.radii.x, 0.0)
	caster.flare.rotation = caster.aim_angle
	state_machine.add_hazard(caster.flare, caster.aim_origin, body.floor_layer)


func _build_head(caster: Caster) -> void:
	var spec := CarterArtLayout.messatsu_head()
	if spec.has("texture"):
		caster.head = _sheet(spec)
	else:
		caster.head = _ellipse(spec.radii, spec.points, spec.color)
	caster.head.rotation = caster.aim_angle
	state_machine.add_hazard(caster.head, caster.aim_origin, body.floor_layer)


func _ellipse(radii: Vector2, points: int, color: Color) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = CarterArtLayout.ellipse(radii, points)
	shape.color = color
	return shape


# One of the sheets, its pivot texel on the origin, stepping from the moment it is made.
func _sheet(spec: Dictionary) -> Sprite2D:
	var pivot: Vector2 = spec.pivot
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.centered = false
	sheet.offset = -pivot
	sheet.scale = Vector2.ONE * spec.scale
	sheet.set_meta(&"since", fx_clock)
	return sheet


# Every looping sheet. The lock is not a loop - its frames are its progress over the charge - so
# _draw_lock sets it.
func _step_sheets() -> void:
	var beam := CarterArtLayout.messatsu_beam()
	for caster in casters:
		_step_sheet(caster.ball, CarterArtLayout.messatsu_ball())
		_step_sheet(caster.flare, CarterArtLayout.messatsu_flare())
		_step_sheet(caster.head, CarterArtLayout.messatsu_head())
		if not beam.has("texture"):
			continue
		for part in caster.beam_parts:
			if is_instance_valid(part):
				(part as Sprite2D).texture = beam_frames[_looped_frame(beam, fx_clock - part.get_meta(&"since"))]


# Untyped on purpose: between two volleys these still hold the last one's freed pieces, and a freed
# object passed as a typed argument is a script error before is_instance_valid can see it.
func _step_sheet(sheet, spec: Dictionary) -> void:
	if is_instance_valid(sheet) and spec.has("texture"):
		(sheet as Sprite2D).frame = _looped_frame(spec, fx_clock - sheet.get_meta(&"since"))


# The frame a looping sheet is on `clock` seconds after it was made: `frame_time` a frame, or one of
# `frame_times` each.
func _looped_frame(spec: Dictionary, clock: float) -> int:
	if spec.has("frame_time"):
		return int((clock + CLOCK_SLACK) / spec.frame_time) % int(spec.hframes)
	var times: Array = spec.frame_times
	var loop := 0.0
	for time: float in times:
		loop += time
	var into := fposmod(clock + CLOCK_SLACK, loop)
	for i in times.size():
		if into < times[i]:
			return i
		into -= times[i]
	return times.size() - 1


#WHERE THINGS ARE

func _player() -> Node2D:
	var player: Node2D = state_machine.get_player()
	return player if is_instance_valid(player) else null


func _player_centre() -> Vector2:
	var player := _player()
	if player == null:
		return lock_point
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


func _muzzle(caster: Caster) -> Vector2:
	return caster.figure.global_position + CarterArtLayout.local(CarterArtLayout.MESSATSU_MUZZLE, caster.figure.flip_h)


# One bare node per source, under a holder with no sprite in it: PlayerCombatFx._attack_art flicks the
# first visible Sprite2D among a parried source's siblings, and PlayerDefense keeps its records per
# source - the strike's own, and each beam's for as long as it is out.
func _hit_source(at: Vector2) -> Node2D:
	if not is_instance_valid(source_holder):
		source_holder = Node2D.new()
		state_machine.add_hazard(source_holder, Vector2.ZERO, body.clone_layer)
	var source := Node2D.new()
	source_holder.add_child(source)
	source.global_position = at.round()
	return source


func _rect_of(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)
