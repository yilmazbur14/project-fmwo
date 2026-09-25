extends State

# Carter's third attack, the Messatsu - Akuma's Messatsu Gou Hadou, the multi-hit super fireball 3rd
# Strike players parry one hit at a time. Not "blackout": blackout and ko_blackout() already mean the
# KO's black quad. Beats CUT to END in a single state:
#   CUT     0.40 s  lit, he makes the lights die (`lights_out`). As it ends the curtain comes down in
#                   0.10 s, the crowd hushes, the music ducks, the player is lifted over the dark, and he
#                   goes with the lights: only his eyes are left glinting where he stood.
#   VANISH  0.28 s  his eyes fade where he stood.
#   WARP    0.30 s  they come back somewhere across the ring, facing the player.
#   CHARGE  1.20 s  the ball gathers at his palms, a dim violet line tracks the player and a lock ring
#                   closes on them.
#   TELL    0.30 s  the lights SNAP back on, and him with them, with the badge already over his head.
#   STRING  2.60 s  it fires. The aim latches on the fire frame and the head crosses to the latched point
#                   in 0.10 s - hit 1 - then five surges run down the beam 0.50 s apart, one hit each.
#   END     0.50 s  a 0.20 s hold, then the beam fades out over 0.30 s and he is left there, spent.
# 5.58 s of game time, and each parry's freeze adds about 0.25 s of real time on top. CUT is read off
# lights_out's own length (CarterArtLayout.time_to_step); VANISH and WARP are the eyes' own fades.
#
# IT IS ONE STATE ON PURPOSE, for the reason the other two are: the dark, the player's draw order, the
# duck, the badge and every hazard have to be taken and given back as a unit, and a single release()
# funnel - from Exit(), _exit_tree() and CarterStateMachine._end_fight() - is the only way every failure
# path is provably safe. Do not split it into beats. The player is never locked.
#
# THE DARK IS THE DEMON'S AND NOTHING NEW IS LAYERED FOR IT. The curtain is at DARK_Z (5), so everything
# from z 0 to 4 is under it. The player's stage is lifted to PLAYER_Z from the lights going out to them
# coming back on.
# NOTHING OF HIM SHOWS IN THE DARK BUT HIS EYES, by the user's call. His body, his aura and his mark go
# down with the curtain, on its own clock, and are hidden - not dimmed - from the frame it is fully down
# to the lights coming back on: left drawn, about 7% of him would show through demon_darkness. The eyes,
# the ball, the aim line and the lock ring are on the clone layer at z 10, and the last three are the
# beam's, not his. The eyes are laid on his drawn eyes on both sides of the dark, since they take over
# from them and hand back to them: on the flared eyes of the lights going out until they have faded,
# then on the charge pose's slits, to the texel, from where they come back.
# LIGHTS-ON IS A ONE-FRAME SNAP, AND THE BADGE POPS ON THE SAME FRAME. This is load-bearing: ParryTell
# draws at z 3, under the curtain, so a fade-in would dim the tell.
#
# THE AIM tracks the player's hurtbox centre every physics step with no turn-rate cap, holds its angle
# while they are within MESSATSU_MIN_AIM of his palms, and LATCHES ON THE FIRE FRAME, not when the
# lights come on. The band starts MESSATSU_BACK behind his palms, so hugging him or getting behind him is
# not a safe spot. A dash THROUGH him from within about 170 px of his palms at the fire does come out of
# the back of the band: that is kept on purpose, and no invisible hit region is added to close it.
# To tune the dodge, change messatsu_travel, not the width (CarterArtLayout has the arithmetic).
#
# THE STRING. Every hit is its own parry and its own hit source: a bare node under an EMPTY holder on
# the clone layer. PlayerDefense keeps absorbed_until per source for a second against a half-second
# cadence, and PlayerCombatFx._attack_art flicks the first visible Sprite2D among a source's siblings -
# so one shared source would hand out free hits, and a source with a sprite beside it would knock that
# sprite on every parry. Contact is analytic, against the player's own hurtbox, and the hit's origin is
# that hurtbox's centre, so any facing answers it. There is no Area2D.
# The 0.50 s cadence equals parry_mash_lockout, so rearm_parry() is load-bearing: as the lights come on
# and messatsu_rearm_delay after each hit, and nowhere else. Do not widen this into a per-press rearm or
# the string becomes a mash-fest.
# A parry pays hype the usual way and staggers nothing, a hit costs a half-heart, a block costs HEAVY
# stamina - a turtle guard-breaks on the third - and walking or dashing out of the band caps the bill.
# Each parry is also a read of his fight-long Break gauge and each hit costs one back; a Break here is
# banked and cashed as the string hands over (CarterStateMachine.on_break). The Beam Rush's clones fire
# beams drawn on these sheets, without the surges, as an attack of their own that can't be parried.
#
# FREEZE SAFETY: every wait here is a Physics_Update accumulator and every ramp a node-bound tween, both
# of which a pause and a finisher's FightFreeze stop with the rest of the fight. Nothing here may use
# get_tree().create_timer() or a tree-level create_tween().

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const BEAM_ID := &"carter_messatsu_beam"
# Where he reappears: this many uniform picks inside MESSATSU_SPOT_AREA, the first SPOT_LEVEL_TRIES of
# which also have to be more across from the player than above or below them, so the beam tends to come
# in level. Failing all of them, the corner of the area farthest from the player.
const SPOT_TRIES := 24
const SPOT_LEVEL_TRIES := 16
const PULSE_SFX := [&"pulse_1", &"pulse_2", &"pulse_3"]
# Summing 1/60 s steps falls a hair short of a round number - six of them come to 0.09999999999999999 -
# which would land every hit a frame after the time it is written at, and the dodge is four frames
# long. Far under one step, even at a hit-stop's 0.05 time scale.
const CLOCK_SLACK := 0.0001

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { CUT, VANISH, WARP, CHARGE, TELL, STRING, END }

var beat := Beat.CUT
var beat_clock := 0.0
# From the fire frame, and never reset inside the string, so every hit lands on its own frame.
var fire_clock := 0.0
# The hit the string is on: 0 is the head arriving, 1 to 5 the surges; messatsu_hits once all are in.
var tick_index := 0
var latched := false
var aim_origin := Vector2.ZERO
var aim_angle := 0.0
var parried := 0
var missed := 0
var blocked := 0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# Where he reappears, for a test or a still that has to know; Vector2.INF picks a spot.
var spot_override := Vector2.INF

var beam_root: Node2D
var ball: Node2D
var eyes: Node2D
var aim_line: Line2D
var lock_ring: Node2D
var surges: Array[Node2D] = []

var flare: Node2D
var head: Node2D
var beam_parts: Array[Node2D] = []
var beam_frames: Array[Texture2D] = []
var source_holder: Node2D
var eyes_fade: Tween
var player_stage_z := 0
# From his palms to the point the aim latched on: the head covers it in messatsu_travel.
var head_distance := 0.0
# The next hit whose rearm and whose surge are still to come.
var rearm_index := 1
var surge_index := 1
var faded := false
# What every looping sheet steps off, each from the moment it was made.
var fx_clock := 0.0
# His body going down with the curtain, and the alphas it is put back to once it is hidden.
var body_fade: Tween
var body_alphas: Array = []
# The point between his eyes on the pose the glow is laid on, and a slide across begun when he turned
# in the charge.
var eyes_at := Vector2.ZERO
var eyes_turned_at := -INF
var eyes_turned_from := Vector2.ZERO


func Enter() -> void:
	released = false
	beat = Beat.CUT
	beat_clock = 0.0
	fire_clock = 0.0
	fx_clock = 0.0
	tick_index = 0
	latched = false
	parried = 0
	missed = 0
	blocked = 0
	rearm_index = 1
	surge_index = 1
	faded = false
	player_stage_z = state_machine.player_stage_z()
	body.velocity = Vector2.ZERO
	body.show_body(true)
	body.show_mark_glow(false)
	body.play_anim(&"lights_out")


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent. `keep_dark` is the Demon's stay-dark rule for his own win: the dark, the duck and the
# player's draw order are handed on to his victory pose rather than given back. The player can only be
# hurt once the lights are on, so in practice there is nothing left to hand on; everything else - the
# badge, the hum, his facing and every hazard - goes whichever way it ended.
func release(keep_dark := false) -> void:
	if released:
		return
	released = true
	if is_instance_valid(body):
		ParryTell.clear(body)
		if not keep_dark:
			body.snap_dark_clear()
			body.snap_music_level()
		body.charge_sfx_player.stop()
		body.sprite.flip_h = false
		if body_fade:
			body_fade.kill()
		_restore_body_alphas()
		body.show_body(true)
	for node in [beam_root, flare, head, ball, eyes, aim_line, lock_ring, source_holder]:
		if is_instance_valid(node):
			node.queue_free()
	for surge in surges:
		if is_instance_valid(surge):
			surge.queue_free()
	surges.clear()
	beam_parts.clear()
	if is_instance_valid(state_machine) and not keep_dark:
		state_machine.set_player_stage_z(player_stage_z)


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	fx_clock += delta
	_step_sheets()
	match beat:
		Beat.CUT:
			if _due(beat_clock, _anim_length(&"lights_out")):
				_lights_out()
		Beat.VANISH:
			if _due(beat_clock, CarterArtLayout.MESSATSU_EYES_OUT):
				_warp()
		Beat.WARP:
			if _due(beat_clock, CarterArtLayout.MESSATSU_EYES_IN):
				_begin_charge()
		Beat.CHARGE:
			_face_player()
			_track()
			_draw_charge()
			if _due(beat_clock, state_machine.messatsu_charge):
				_lights_on()
		Beat.TELL:
			_track()
			_draw_aim()
			if _due(beat_clock, state_machine.messatsu_tell):
				_fire()
		Beat.STRING:
			_advance_string(delta)
		Beat.END:
			_step_surges(delta)
			_advance_end()


func _due(clock: float, at: float) -> bool:
	return clock >= at - CLOCK_SLACK


func _anim_length(anim_name: StringName) -> float:
	return CarterArtLayout.time_to_step(anim_name, CarterArtLayout.anim(anim_name).frames.size())


#THE LIGHTS GOING OUT

func _lights_out() -> void:
	beat = Beat.VANISH
	beat_clock = 0.0
	body.darken(CarterArtLayout.MESSATSU_DARKEN)
	_fade_body_out()
	body.dark_sfx_player.play()
	get_tree().call_group("arena_crowd", "hush")
	body.duck_music(CarterArtLayout.MESSATSU_DUCK_DB, CarterArtLayout.MESSATSU_DUCK_TIME)
	state_machine.set_player_stage_z(CarterArtLayout.PLAYER_Z)
	_build_eyes()
	eyes_fade = eyes.create_tween()
	eyes_fade.tween_property(eyes, "modulate:a", 0.0, CarterArtLayout.MESSATSU_EYES_OUT)


# On the curtain's own clock, so the dark swallows him rather than him popping out in plain view: he is
# gone the frame it is fully down. Then hidden, with his alphas put back for the lights coming up on him.
func _fade_body_out() -> void:
	body_alphas = [body.sprite.modulate.a, body.aura.modulate.a]
	body_fade = body.create_tween().set_parallel()
	body_fade.tween_property(body.sprite, "modulate:a", 0.0, CarterArtLayout.MESSATSU_DARKEN)
	body_fade.tween_property(body.aura, "modulate:a", 0.0, CarterArtLayout.MESSATSU_DARKEN)
	body_fade.chain().tween_callback(func() -> void:
		body.show_body(false)
		_restore_body_alphas())


func _restore_body_alphas() -> void:
	if body_alphas.is_empty():
		return
	body.sprite.modulate.a = body_alphas[0]
	body.aura.modulate.a = body_alphas[1]
	body_alphas.clear()


# Unseen: only the sound and his eyes coming back say where he went.
func _warp() -> void:
	beat = Beat.WARP
	beat_clock = 0.0
	body.global_position = _pick_spot()
	var player := _player()
	if player:
		body.sprite.flip_h = player.global_position.x < body.global_position.x
	aim_angle = PI if body.sprite.flip_h else 0.0
	_track()
	body.yank_sfx_player.play()
	if eyes_fade:
		eyes_fade.kill()
	# Faded right out by now, so moving them onto the charge pose's slits can't be seen.
	_lay_eyes(CarterArtLayout.MESSATSU_EYES, CarterArtLayout.MESSATSU_EYE_GAP)
	eyes_fade = eyes.create_tween()
	eyes_fade.tween_property(eyes, "modulate:a", 1.0, CarterArtLayout.MESSATSU_EYES_IN)


# Anywhere in the spot area where his badge is clear of the HUD and at least messatsu_min_range from
# the player, preferring spots more across from them than above or below.
func _pick_spot() -> Vector2:
	if spot_override != Vector2.INF:
		return spot_override
	var player := _player()
	var at: Vector2 = player.global_position if player else state_machine.ARENA_CENTRE
	var area := CarterArtLayout.MESSATSU_SPOT_AREA
	for i in SPOT_TRIES:
		var spot := Vector2(randf_range(area.position.x, area.end.x), randf_range(area.position.y, area.end.y)).round()
		if not _tell_clear_at(spot):
			continue
		var offset := spot - at
		if offset.length() < state_machine.messatsu_min_range:
			continue
		if i < SPOT_LEVEL_TRIES and absf(offset.x) < absf(offset.y):
			continue
		return spot
	var corners := [area.position, Vector2(area.end.x, area.position.y), area.end, Vector2(area.position.x, area.end.y)]
	var farthest: Vector2 = corners[0]
	for corner: Vector2 in corners:
		if corner.distance_to(at) > farthest.distance_to(at):
			farthest = corner
	return farthest.round()


# His badge from `spot` clear of the HUD and in view whichever way he ends up facing: he may turn in the
# charge, and the badge mirrors with him.
func _tell_clear_at(spot: Vector2) -> bool:
	var badge := CarterArtLayout.TELL_BADGE
	var anchor := CarterArtLayout.MESSATSU_TELL_ANCHOR
	for offset: Vector2 in [anchor, Vector2(-anchor.x, anchor.y)]:
		if not CarterArtLayout.clear_of_hud(Rect2(spot + offset + badge.position, badge.size)):
			return false
	return true


#THE CHARGE

# His body takes the stance unseen, so the lights come up on it.
func _begin_charge() -> void:
	beat = Beat.CHARGE
	beat_clock = 0.0
	body.play_anim(&"messatsu_charge")
	# Its fade in is on the idle clock and this beat on the physics one, so it can be a frame short.
	if eyes_fade:
		eyes_fade.kill()
	eyes.modulate.a = 1.0
	_build_ball()
	_build_aim_line()
	_build_lock_ring()
	_draw_charge()
	body.charge_sfx_player.play()


# Only here, and only once the player is well past his centre line: never after the lights are on. His
# eyes set off across from wherever they are.
func _face_player() -> void:
	var player := _player()
	if player == null:
		return
	var past: float = player.global_position.x - body.global_position.x
	var hysteresis := CarterArtLayout.MESSATSU_FACE_HYSTERESIS
	var round_to_right: bool = body.sprite.flip_h and past > hysteresis
	var round_to_left: bool = not body.sprite.flip_h and past < -hysteresis
	if not round_to_right and not round_to_left:
		return
	body.sprite.flip_h = round_to_left
	eyes_turned_from = eyes.global_position
	eyes_turned_at = beat_clock


# Straight onto the player's hurtbox centre, every step, with no turn rate.
func _track() -> void:
	aim_origin = _muzzle()
	var to := _player_centre() - aim_origin
	if to.length() >= CarterArtLayout.MESSATSU_MIN_AIM:
		aim_angle = to.angle()


func _draw_charge() -> void:
	var grown := clampf(beat_clock / maxf(state_machine.messatsu_charge, 0.0001), 0.0, 1.0)
	var ball_spec := CarterArtLayout.messatsu_ball()
	var drawn_at: float = ball_spec.get("scale", 1.0)
	ball.global_position = aim_origin.round()
	ball.scale = Vector2.ONE * drawn_at * lerpf(ball_spec.from_scale, 1.0, grown)
	_draw_lock(grown)
	_place_eyes()
	_draw_aim()
	var line := CarterArtLayout.PLACEHOLDER_MESSATSU_LINE
	var dim := int(beat_clock / line.flicker_time) % 2 == 1
	aim_line.default_color.a = line.flicker_alpha if dim else line.color.a


# The sheet's frames are the lock clicking shut and its scale the squeeze on top of them; the
# placeholder only squeezes.
func _draw_lock(grown: float) -> void:
	var spec := CarterArtLayout.messatsu_lock()
	if spec.has("texture"):
		var frames: int = spec.hframes
		(lock_ring as Sprite2D).frame = mini(int(grown * frames), frames - 1)
		lock_ring.scale = Vector2.ONE * spec.scale * lerpf(spec.from_scale, 1.0, grown)
	else:
		(lock_ring as Line2D).points = CarterArtLayout.ellipse(Vector2.ONE * lerpf(spec.from, spec.to, grown), spec.points)
	lock_ring.global_position = _player_centre().round()


func _draw_aim() -> void:
	aim_line.global_position = aim_origin.round()
	aim_line.points = PackedVector2Array([Vector2.ZERO, (_player_centre() - aim_line.global_position).round()])


#THE LIGHTS COMING BACK

func _lights_on() -> void:
	beat = Beat.TELL
	beat_clock = 0.0
	# One frame, and the badge on the same one: ParryTell draws at z 3, under the curtain, so a fade-in
	# would dim the tell. He comes back on the same frame too, his drawn eyes exactly where the glow was.
	body.snap_dark_clear()
	body.show_body(true)
	body.pop_flash(CarterArtLayout.MESSATSU_FLASH_PEAK, CarterArtLayout.MESSATSU_FLASH_TIME)
	body.charge_sfx_player.stop()
	body.lights_sfx_player.play()
	state_machine.set_player_stage_z(player_stage_z)
	lock_ring.hide()
	eyes.hide()
	aim_line.default_color = CarterArtLayout.PLACEHOLDER_MESSATSU_LINE.lit_color
	ParryTell.telegraph(body, BEAM_ID, state_machine.messatsu_tell, _tell_anchor)
	state_machine.rearm_parry()


func _tell_anchor() -> Vector2:
	return body.global_position + _mirrored(CarterArtLayout.MESSATSU_TELL_ANCHOR)


#THE STRING

# The aim is already on this frame's player; from here the origin and the angle never move again.
func _fire() -> void:
	beat = Beat.STRING
	beat_clock = 0.0
	fire_clock = 0.0
	tick_index = 0
	rearm_index = 1
	surge_index = 1
	latched = true
	head_distance = maxf(aim_origin.distance_to(_player_centre()), CarterArtLayout.MESSATSU_MIN_AIM)
	ParryTell.clear(body)
	body.play_anim(&"messatsu_fire")
	body.shake_screen(CarterArtLayout.MESSATSU_FIRE_SHAKE, CarterArtLayout.MESSATSU_FIRE_SHAKE_STEPS,
		CarterArtLayout.MESSATSU_FIRE_SHAKE_STEP_TIME)
	body.fire_sfx_player.play()
	ball.hide()
	aim_line.hide()
	# In draw order on the floor layer: the body, the flare over its flat start, the head over both.
	_build_beam()
	_build_flare()
	_build_head()
	_step_beam()


func _advance_string(delta: float) -> void:
	fire_clock += delta
	_step_beam()
	_step_surges(delta)
	var hits: int = state_machine.messatsu_hits
	if rearm_index < hits and _due(fire_clock, state_machine.messatsu_hit_time(rearm_index - 1) + state_machine.messatsu_rearm_delay):
		rearm_index += 1
		state_machine.rearm_parry()
	if surge_index < hits and _due(fire_clock, state_machine.messatsu_hit_time(surge_index) - state_machine.messatsu_pulse_travel):
		_launch_surge(surge_index)
		surge_index += 1
	if tick_index < hits and _due(fire_clock, state_machine.messatsu_hit_time(tick_index)):
		_land(tick_index)
		tick_index += 1
		if tick_index >= hits:
			_begin_end()


# The head crosses to the latched point in messatsu_travel, and once it is there the beam runs out to
# its full length. The body only starts MESSATSU_BEAM_START out, under the flare.
func _step_beam() -> void:
	var arrived := _due(fire_clock, state_machine.messatsu_travel)
	var reach: float = CarterArtLayout.MESSATSU_LENGTH
	if not arrived:
		reach = head_distance * fire_clock / maxf(state_machine.messatsu_travel, 0.0001)
	var spec := CarterArtLayout.messatsu_beam()
	var length := maxf(reach - CarterArtLayout.MESSATSU_BEAM_START, 0.0)
	for part in beam_parts:
		part.visible = length > 0.0
		if spec.has("texture"):
			(part as Sprite2D).region_rect = Rect2(CarterArtLayout.MESSATSU_BEAM_START / spec.scale, 0.0,
				length / spec.scale, spec.frame_size.y)
		elif part.visible:
			part.scale.x = length
	head.global_position = (aim_origin + Vector2.from_angle(aim_angle) * reach).round()
	head.visible = not arrived


# Each surge leaves his palms messatsu_pulse_travel before its hit and lands on the player on it,
# wherever down the beam they have walked to. One the player was out of the band for carries on past
# them and off the end.
func _step_surges(delta: float) -> void:
	var dir := Vector2.from_angle(aim_angle)
	var along := _along()
	var gone: Array[Node2D] = []
	for surge in surges:
		if not is_instance_valid(surge):
			gone.append(surge)
			continue
		var distance: float
		if surge.has_meta(&"speed"):
			distance = surge.get_meta(&"distance") + surge.get_meta(&"speed") * delta
		else:
			var left: float = state_machine.messatsu_hit_time(surge.get_meta(&"hit")) - fire_clock
			distance = along * clampf(1.0 - left / state_machine.messatsu_pulse_travel, 0.0, 1.0)
		surge.set_meta(&"distance", distance)
		surge.global_position = (aim_origin + dir * distance).round()
		if distance > CarterArtLayout.MESSATSU_LENGTH:
			gone.append(surge)
	for surge in gone:
		_drop_surge(surge)


func _launch_surge(k: int) -> void:
	var surge := _build_pulse()
	surge.set_meta(&"hit", k)
	surge.set_meta(&"distance", 0.0)
	surge.rotation = aim_angle
	state_machine.add_hazard(surge, aim_origin, body.floor_layer)
	surges.append(surge)
	_pulse_sfx(k)


# The surge's own take once its file exists; until then his rush, pitched down under the beam.
func _pulse_sfx(k: int) -> void:
	var key: StringName = PULSE_SFX[k % PULSE_SFX.size()]
	var path := CarterArtLayout.messatsu_sfx(key)
	if path == CarterArtLayout.MESSATSU_SFX[key].fallback:
		body.play_rush(k, CarterArtLayout.MESSATSU_PULSE_FALLBACK_PITCH)
		return
	body.rush_sfx_player.stream = load(path)
	body.rush_sfx_player.pitch_scale = 1.0
	body.rush_sfx_player.play()


# The contact instant for hit `k`. The player is free to move, so the band is tested against where
# they are now, not where the beam was aimed: out of it, nothing lands - and on the head's hit, the
# band reaching the spot a dash left is a perfect dodge.
func _land(k: int) -> void:
	var surge := _surge_for(k)
	var player := _player()
	if player == null or player.playerHealth <= 0:
		_drop_surge(surge)
		return
	var box := _rect_of(player.hurtBox.get_node("CollisionShape2D"))
	if not _in_band(box):
		if k == 0:
			_near_miss(player)
		if surge:
			surge.set_meta(&"speed", surge.get_meta(&"distance") / maxf(state_machine.messatsu_pulse_travel, 0.0001))
		return
	var contact := box.get_center()
	var result: int = player.receive_hit(HitInfo.make(BEAM_ID, _hit_source(contact), contact, body))
	match result:
		HitInfo.Result.PARRIED:
			parried += 1
			body.spawn_burst(true, contact)
			body.break_sfx_player.play()
		HitInfo.Result.BLOCKED:
			blocked += 1
			body.spawn_burst(true, contact)
			body.strike_sfx_player.play()
		HitInfo.Result.HIT:
			missed += 1
			body.spawn_burst(false, contact)
			body.strike_sfx_player.play()
	if result != HitInfo.Result.IGNORED:
		body.shake_screen(CarterArtLayout.MESSATSU_HIT_SHAKE, CarterArtLayout.MESSATSU_HIT_SHAKE_STEPS,
			CarterArtLayout.MESSATSU_HIT_SHAKE_STEP_TIME)
	_drop_surge(surge)


func _near_miss(player: Node2D) -> void:
	if player.dodge_ghost_position() == Vector2.INF:
		return
	var ghost := _rect_of(player.dodge_ghost.get_node("CollisionShape2D"))
	if _in_band(ghost):
		player.receive_near_miss(HitInfo.make(BEAM_ID, _hit_source(ghost.get_center()), ghost.get_center(), body))


# The band against a box: within half the hit width of the latched axis, the box's own reach across
# it included, and not wholly more than MESSATSU_BACK behind his palms. It runs on past the view.
func _in_band(box: Rect2) -> bool:
	var dir := Vector2.from_angle(aim_angle)
	var n := dir.orthogonal()
	var c := box.get_center() - aim_origin
	var half := box.size / 2.0
	var across := CarterArtLayout.MESSATSU_HIT_WIDTH / 2.0 + half.x * absf(n.x) + half.y * absf(n.y)
	var reach := c.dot(dir) + half.x * absf(dir.x) + half.y * absf(dir.y)
	return absf(c.dot(n)) <= across and reach >= -CarterArtLayout.MESSATSU_BACK


# One bare node per hit, under a holder with no sprite in it: see the header.
func _hit_source(at: Vector2) -> Node2D:
	if not is_instance_valid(source_holder):
		source_holder = Node2D.new()
		state_machine.add_hazard(source_holder, Vector2.ZERO, body.clone_layer)
	var source := Node2D.new()
	source_holder.add_child(source)
	source.global_position = at.round()
	return source


func _surge_for(k: int) -> Node2D:
	for surge in surges:
		if is_instance_valid(surge) and surge.get_meta(&"hit") == k:
			return surge
	return null


func _drop_surge(surge: Node2D) -> void:
	if surge == null:
		return
	surges.erase(surge)
	if is_instance_valid(surge):
		surge.queue_free()


#THE END

func _begin_end() -> void:
	beat = Beat.END
	beat_clock = 0.0
	faded = false


func _advance_end() -> void:
	if not faded and _due(beat_clock, state_machine.messatsu_end_hold):
		faded = true
		for node in [beam_root, flare] + surges:
			if is_instance_valid(node):
				var out: Tween = node.create_tween()
				out.tween_property(node, "modulate:a", 0.0, state_machine.messatsu_fade)
		body.restore_music(CarterArtLayout.MESSATSU_MUSIC_BACK)
		get_tree().call_group("arena_crowd", "cheer", CarterArtLayout.MESSATSU_CHEER)
		body.finish_sfx_player.play()
	if _due(beat_clock, state_machine.messatsu_end_hold + state_machine.messatsu_fade):
		_hand_over()


# The spent pose stands over his feet where the fire's hold has him slid back, so his feet go back by
# the difference - away from where he fired - and he doesn't pop forward into it. Inside the ropes.
func _hand_over() -> void:
	var back := CarterArtLayout.MESSATSU_RECOIL * CarterArtLayout.SCALE
	var ropes: Rect2 = state_machine.ROPES
	body.global_position.x = clampf(body.global_position.x + (back if body.sprite.flip_h else -back),
		ropes.position.x, ropes.end.x)
	body.sprite.flip_h = false
	var recover: State = state_machine.states.get("Recover")
	if recover:
		recover.prepare(parried, missed, 0, state_machine.messatsu_hits, -1.0, state_machine.take_break_owed())
	state_machine.on_child_transition(self, "Recover")


#WHAT IS DRAWN
# Each piece is its sheet, or its placeholder while its USE_FINAL_MESSATSU_* flag in CarterArtLayout is
# off. The ball, the eyes, the aim line and the lock are light on the clone layer, over the dark. The
# beam, the flare, the head and the surges are paint on the floor layer, under both fighters.

# Laid out facing right, around the point between his eyes. The sheet's slits are closer together than
# his, so it goes down as two halves, each moved out onto its own eye: frame k's left half is sheet
# frame 2k and its right half 2k + 1. It starts on the eyes of the lights going out.
func _build_eyes() -> void:
	var spec := CarterArtLayout.messatsu_eyes()
	eyes = Node2D.new()
	if spec.has("texture"):
		for _half in 2:
			var half := _sheet(spec)
			half.hframes = spec.hframes * 2
			eyes.add_child(half)
	else:
		var size: Vector2 = spec.size
		for side in [-0.5, 0.5]:
			var slit := Polygon2D.new()
			slit.polygon = CarterArtLayout.rect_polygon(Rect2(Vector2(side * spec.spacing, 0.0) - size / 2.0, size))
			slit.color = spec.color
			eyes.add_child(slit)
	eyes.set_meta(&"since", fx_clock)
	state_machine.add_hazard(eyes, body.global_position, body.clone_layer)
	_lay_eyes(CarterArtLayout.MESSATSU_LIGHTS_OUT_EYES, CarterArtLayout.MESSATSU_LIGHTS_OUT_EYE_GAP)


# Onto one of his poses' eyes: the point between them, as a texel corner, and the gap between them
# that the two halves spread to.
func _lay_eyes(point: Vector2, gap: float) -> void:
	eyes_at = point
	eyes_turned_at = -INF
	var spec := CarterArtLayout.messatsu_eyes()
	if spec.has("texture"):
		var pivot: Vector2 = spec.pivot
		var split: float = spec.split
		var spread: float = (gap - spec.gap) / 2.0
		for i in eyes.get_child_count():
			var side := -1.0 if i == 0 else 1.0
			(eyes.get_child(i) as Sprite2D).offset = Vector2(split * (side + 1.0) / 2.0 - pivot.x + side * spread, -pivot.y)
	_place_eyes()


# Mirrored with him as a whole, so each half lands on his mirrored eye and the glint on the right one.
# Not rounded: it has to share his sprite's pixel grid, wherever that falls. If he has just turned,
# they are still sliding across.
func _place_eyes() -> void:
	var target := _eye_point()
	var slid := (beat_clock - eyes_turned_at) / CarterArtLayout.MESSATSU_EYES_TURN
	eyes.global_position = target if slid >= 1.0 else eyes_turned_from.lerp(target, slid)
	eyes.scale.x = -1.0 if body.sprite.flip_h else 1.0


func _build_ball() -> void:
	var spec := CarterArtLayout.messatsu_ball()
	if spec.has("texture"):
		ball = _sheet(spec)
	else:
		ball = _ellipse(Vector2.ONE * spec.radius, spec.points, spec.color)
	var drawn_at: float = spec.get("scale", 1.0)
	ball.scale = Vector2.ONE * drawn_at * spec.from_scale
	state_machine.add_hazard(ball, aim_origin, body.clone_layer)


func _build_aim_line() -> void:
	var spec := CarterArtLayout.PLACEHOLDER_MESSATSU_LINE
	aim_line = Line2D.new()
	aim_line.width = spec.width
	aim_line.default_color = spec.color
	state_machine.add_hazard(aim_line, aim_origin, body.clone_layer)


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
	state_machine.add_hazard(lock_ring, _player_centre(), body.clone_layer)


# Along the latched axis from his palms, from MESSATSU_BEAM_START out, and stretched to the beam's
# reach every step. The sheet's body is one frame repeated down the region, swapped for the next as the
# beam flows; the placeholder's is a body and a core, quads one px long.
func _build_beam() -> void:
	var spec := CarterArtLayout.messatsu_beam()
	beam_root = Node2D.new()
	beam_root.rotation = aim_angle
	beam_parts.clear()
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
		beam_parts.append(tiled)
	else:
		for part in [[CarterArtLayout.MESSATSU_DRAW_WIDTH, spec.color], [spec.core_width, spec.core_color]]:
			var width: float = part[0]
			var quad := Polygon2D.new()
			quad.polygon = CarterArtLayout.rect_polygon(Rect2(0.0, -width / 2.0, 1.0, width))
			quad.color = part[1]
			quad.material = CarterArtLayout.additive()
			beam_parts.append(quad)
	for part in beam_parts:
		part.position.x = CarterArtLayout.MESSATSU_BEAM_START
		beam_root.add_child(part)
	state_machine.add_hazard(beam_root, aim_origin, body.floor_layer)


# Cut apart the first time he fires: region repeat tiles a whole texture, so the sheet's four frames
# side by side would tile as one.
func _beam_frames(spec: Dictionary) -> Array[Texture2D]:
	if beam_frames.is_empty():
		var sheet := (load(spec.texture) as Texture2D).get_image()
		var size := Vector2i(spec.frame_size)
		for k in spec.hframes:
			beam_frames.append(ImageTexture.create_from_image(sheet.get_region(Rect2i(Vector2i(k * size.x, 0), size))))
	return beam_frames


# The beam's tapered start, out of his palms and pointing down it. On the floor layer over the body's
# flat start, so it can never cover him or the player.
func _build_flare() -> void:
	var spec := CarterArtLayout.messatsu_flare()
	if spec.has("texture"):
		flare = _sheet(spec)
	else:
		flare = _ellipse(spec.radii, spec.points, spec.color)
		(flare as Polygon2D).offset = Vector2(spec.radii.x, 0.0)
	flare.rotation = aim_angle
	state_machine.add_hazard(flare, aim_origin, body.floor_layer)


# On the beam's front end while it crosses, over the flare.
func _build_head() -> void:
	var spec := CarterArtLayout.messatsu_head()
	if spec.has("texture"):
		head = _sheet(spec)
	else:
		head = _ellipse(spec.radii, spec.points, spec.color)
	head.rotation = aim_angle
	state_machine.add_hazard(head, aim_origin, body.floor_layer)


# Across the beam, so its long side spans it. Painted rather than drawn as light, like the beam under
# it: light would wash its red rim out, and it is the only red in the beam.
func _build_pulse() -> Node2D:
	var spec := CarterArtLayout.messatsu_pulse()
	if spec.has("texture"):
		return _sheet(spec)
	var pulse := Node2D.new()
	for part in [[spec.size, spec.color], [spec.core_size, spec.core_color]]:
		var size: Vector2 = part[0]
		var quad := Polygon2D.new()
		quad.polygon = CarterArtLayout.rect_polygon(Rect2(-size / 2.0, size))
		quad.color = part[1]
		pulse.add_child(quad)
	return pulse


func _ellipse(radii: Vector2, points: int, color: Color) -> Polygon2D:
	var shape := Polygon2D.new()
	shape.polygon = CarterArtLayout.ellipse(radii, points)
	shape.color = color
	shape.material = CarterArtLayout.additive()
	return shape


# One of the sheets: its pivot texel on the origin, drawn as light or as paint as its spec says, and
# stepping from the moment it is made.
func _sheet(spec: Dictionary) -> Sprite2D:
	var pivot: Vector2 = spec.pivot
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.centered = false
	sheet.offset = -pivot
	sheet.scale = Vector2.ONE * spec.scale
	if spec.additive:
		sheet.material = CarterArtLayout.additive()
	sheet.set_meta(&"since", fx_clock)
	return sheet


# Every looping sheet. The lock is not a loop - its frames are its progress over the charge - so
# _draw_lock sets it.
func _step_sheets() -> void:
	_step_sheet(ball, CarterArtLayout.messatsu_ball())
	var eyes_spec := CarterArtLayout.messatsu_eyes()
	if is_instance_valid(eyes) and eyes_spec.has("texture"):
		var frame := _looped_frame(eyes_spec, fx_clock - eyes.get_meta(&"since"))
		for half in eyes.get_child_count():
			(eyes.get_child(half) as Sprite2D).frame = frame * 2 + half
	_step_sheet(flare, CarterArtLayout.messatsu_flare())
	_step_sheet(head, CarterArtLayout.messatsu_head())
	for surge in surges:
		_step_sheet(surge, CarterArtLayout.messatsu_pulse())
	var beam := CarterArtLayout.messatsu_beam()
	if not beam.has("texture"):
		return
	for part in beam_parts:
		if is_instance_valid(part):
			(part as Sprite2D).texture = beam_frames[_looped_frame(beam, fx_clock - part.get_meta(&"since"))]


# Untyped on purpose: between two Messatsus these still hold the last one's freed pieces, and a freed
# object passed as a typed argument is a script error before is_instance_valid can see it.
func _step_sheet(sheet, spec: Dictionary) -> void:
	if is_instance_valid(sheet) and spec.has("texture"):
		(sheet as Sprite2D).frame = _looped_frame(spec, fx_clock - sheet.get_meta(&"since"))


# The frame a looping sheet is on `clock` seconds after it was made: `frame_time` a frame, or one of
# `frame_times` each. CLOCK_SLACK for the same reason the hits take it, so a 0.05 s frame is three
# steps every time rather than four then two.
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
		return aim_origin
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


# How far down the beam the player is, from his palms. Never under MESSATSU_MIN_AIM, so a surge still
# travels to someone standing on top of him.
func _along() -> float:
	var down := (_player_centre() - aim_origin).dot(Vector2.from_angle(aim_angle))
	return maxf(down, CarterArtLayout.MESSATSU_MIN_AIM)


func _muzzle() -> Vector2:
	return body.global_position + CarterArtLayout.local(CarterArtLayout.MESSATSU_MUZZLE, body.sprite.flip_h)


func _eye_point() -> Vector2:
	return body.global_position + _mirrored(CarterArtLayout.local(eyes_at))


# An offset from his feet mirrored exactly with him, which is how his sprite flips. local()'s own flip
# mirrors a texel, so a point between texels, like the one between his eyes, lands a texel off.
func _mirrored(offset: Vector2) -> Vector2:
	return Vector2(-offset.x, offset.y) if body.sprite.flip_h else offset


func _rect_of(shape: CollisionShape2D) -> Rect2:
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)
