extends State

# Beast Bixby's Flyby, to the user's spec and sketches of 2026-09-29, in place of his chasing fire breath: he flies up
# off the screen; the floor lights up where his fire will fall, all of it but one safe column at the far edge; after a
# beat he flies across the top of the ring breathing a wall of fire down onto exactly that; he comes back the other way
# with the pattern mirrored, the column at the other edge; then he swoops back in on his start side and lands for the
# usual punish window. Each pass's fire is a node of its own (BixbyFlybyFireScript), the geometry BixbyFlybyLayout's and
# the timings the state machine's flyby_* exports. In seconds from Enter, at the defaults:
#   RISE         0.00  the fly frames, straight up, easing in until his feet are at y -48, his shadow fading out; the
#                      boss bar and its gauge fade to inferno_hud_fade_alpha
#   TELEGRAPH 0  0.35  the start side is picked (flyby_start_side, away from the player), pass 0's projection goes up
#                      faint with its column's rim, and every ember burns out; he waits off the screen on the entry side.
#                      The projection goes strong for the warning at 0.58, flyby_warn_time before the sweep
#   ENTER 0      0.88  he flies in at flyby_speed, his wings whooshing
#   SWEEP 0      1.08  his lead mouth crosses the entry rope: the front sweeps to the column's edge with the curtain
#                      falling at it, and the floor burns behind it for flyby_burn_time
#   EXIT 0       1.87  the front is at the column's edge: he speeds off the far side
#   TELEGRAPH 1  2.22  pass 0's fire has stopped hurting; the mirrored projection goes up, for flyby_return_telegraph_time,
#                      and he waits off the side he just left
#   ENTER 1, SWEEP 1, EXIT 1  4.14, 4.34, 5.14: the crossing, from pass 0's column to the far edge
#   RETURN       5.49  back from off the screen (end_pass), the bar coming back, he swoops to hover over his landing
#                      point, flyby_landing_inset in from his start side's rope
#   DONE         5.99  Land, then Recover (7.81 until the user asked for a faster Flyby, 2026-10-04)
# It all runs on one clock against a schedule worked out as it enters (DannyBossSlams' pattern), and each pass's fire on
# its own clock from its projection beat.
#
# FAIRNESS (BixbyFlybyLayout.invariants): the fire sweeps at over three times a walk, so each projection is long
# enough to walk to its column before the front gets there: he starts from the side away from the player, putting pass
# 0's column on their half with 0.16 s to spare from the centre line, and the crossing's longer projection leaves 0.15 s
# to spare from the rope. A spot burns for less than the i-frames, so a player who stands takes one hit a pass, and one
# caught mid-run who goes on, walking or dashing, is past the fire when their i-frames end; the band burning behind the
# front is wider than a dash, so a dash back through it lands in fire, while a close dash forward through the curtain
# into the column is a PERFECT DODGE, a Break read. Pass 0's fire has stopped hurting before the crossing's projection
# goes up, and he waits off the screen through each projection until he flies in.
#
# RELEASE: the fires and his flight go back through release(), which Exit() and _exit_tree() call. The breath stops, a
# fire still warning or hurting goes, one dying down plays out by itself, and unless the scene is being torn down,
# end_pass() puts him back hovering with his shadow and brings the bar back.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const FlybyLayout := preload("res://Scripts/BixbyFlybyLayout.gd")
const FlybyFire := preload("res://Scripts/BixbyFlybyFireScript.gd")

enum Beat { RISE, TELEGRAPH, ENTER, SWEEP, EXIT, RETURN, DONE }

# Summed steps land a hair short of a scheduled time, which would start its beat a step late.
const STEP_TOLERANCE := 0.0001
# The sweep going off: a light shake, where the Inferno's breath is a heavy one.
const SWEEP_SHAKE := 6.0
const SWEEP_SHAKE_STEPS := 4
const SWEEP_SHAKE_STEP_TIME := 0.03

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clock := 0.0
# [seconds from Enter, Beat, pass], in order.
var schedule: Array = []
var next_entry := 0
var beat := Beat.RISE
var beat_start := 0.0
var pass_index := 0
# 1 flies pass 0 left to right, -1 right to left.
var start_dir := 1.0
var fires: Array = [null, null]
var pass_starts: Array[float] = [INF, INF]
var rise_from := 0.0
var rise_ground := Vector2.ZERO
var return_from := Vector2.ZERO
var landing := Vector2.ZERO
# For a test: every beat as it began, {beat, pass, at: when it was due, clock: when it came}.
var beat_times: Array[Dictionary] = []


func Enter() -> void:
	released = false
	clock = 0.0
	next_entry = 0
	pass_index = 0
	fires = [null, null]
	pass_starts = [INF, INF]
	beat_times.clear()
	rise_ground = body.ground_position
	rise_from = body.height
	body.fly_velocity = Vector2.ZERO
	schedule = _schedule()
	_run_due()


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	_run_due()
	if released:
		return
	for k in fires.size():
		var fire = fires[k]
		if is_instance_valid(fire) and fire.driven:
			fire.drive(clock - pass_starts[k])
	# The breath is a one-shot: it keeps going as long as the sweep does.
	if beat == Beat.SWEEP and not body.breath_sfx_player.playing:
		body.breath_sfx_player.play()
	_place()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent. At a scene's teardown the bar has already left the tree ahead of this state, so it touches nothing of his
# then.
func release() -> void:
	if released:
		return
	released = true
	if not is_instance_valid(body):
		return
	if is_instance_valid(body.breath_sfx_player):
		body.breath_sfx_player.stop()
	for fire in fires:
		if not is_instance_valid(fire):
			continue
		if fire.is_warning() or fire.is_hurting():
			fire.queue_free()
		else:
			fire.driven = false
	if body.health_bar == null or not body.health_bar.is_inside_tree():
		return
	body.end_pass()


func pass_dir(k: int) -> float:
	return start_dir if k == 0 else -start_dir


# Whether the pass going now has fire falling from his mouths.
func curtain_live() -> bool:
	var fire = fires[pass_index]
	return is_instance_valid(fire) and not FlybyLayout.span_empty(fire.curtain_span())


# The side pass 0 flies in from: away from the player (the default), so their half holds its column; from the one it
# didn't use last time if they are dead in the middle; the first ever from the left.
func pick_start_dir() -> float:
	var last: float = state_machine.last_flyby_dir
	var other := -last if last != 0.0 else 1.0
	var dir := other
	match state_machine.flyby_start_side:
		&"left":
			dir = 1.0
		&"right":
			dir = -1.0
		&"random":
			dir = 1.0 if randf() < 0.5 else -1.0
		&"away":
			var player = state_machine.get_player()
			var middle := FlybyLayout.FLOOR.get_center().x
			if player and not is_equal_approx(player.global_position.x, middle):
				dir = 1.0 if player.global_position.x > middle else -1.0
	state_machine.last_flyby_dir = dir
	return dir


#THE SCHEDULE

func _schedule() -> Array:
	var sm = state_machine
	var sweep := FlybyLayout.sweep_time(sm.flyby_safe_width, sm.flyby_speed)
	# The next beat waits for this pass's fire to stop hurting and for him to be off the screen.
	var gap: float = maxf(sm.flyby_exit_time, sm.flyby_burn_time)
	var entries := []
	var at := 0.0
	entries.append([at, Beat.RISE, 0])
	at += sm.flyby_rise_time
	for k in 2:
		var telegraph := _telegraph_time(k)
		entries.append([at, Beat.TELEGRAPH, k])
		entries.append([at + telegraph - sm.flyby_entry_lead, Beat.ENTER, k])
		at += telegraph
		entries.append([at, Beat.SWEEP, k])
		at += sweep
		entries.append([at, Beat.EXIT, k])
		at += gap
	entries.append([at, Beat.RETURN, 1])
	at += sm.flyby_return_time
	entries.append([at, Beat.DONE, 1])
	return entries


func _run_due() -> void:
	while not released and next_entry < schedule.size() and clock >= schedule[next_entry][0] - STEP_TOLERANCE:
		var entry: Array = schedule[next_entry]
		next_entry += 1
		_begin(entry[1], entry[2], entry[0])


func _begin(new_beat: int, k: int, at: float) -> void:
	beat = new_beat
	beat_start = at
	pass_index = k
	beat_times.append({"beat": new_beat, "pass": k, "at": at, "clock": clock})
	match new_beat:
		Beat.RISE:
			body.play_anim(&"fly")
			body.wing_sfx_player.play()
			body.roar_sfx_player.play()
			body.set_hud_faded(true)
		Beat.TELEGRAPH:
			if k == 0:
				start_dir = pick_start_dir()
				for ember in state_machine.embers():
					ember.burn_out()
			pass_starts[k] = at
			fires[k] = _lay_fire(k)
			body.windup_sfx_player.play()
			body.flying_left = pass_dir(k) < 0.0
			body.play_anim(_pass_clip(false))
			_place_on_pass(k)
		Beat.ENTER:
			body.wing_sfx_player.play()
		Beat.SWEEP:
			_switch_clip(true)
			body.breath_sfx_player.play()
			body.shake_screen(SWEEP_SHAKE, SWEEP_SHAKE_STEPS, SWEEP_SHAKE_STEP_TIME)
		Beat.EXIT:
			_switch_clip(false)
			body.breath_sfx_player.stop()
		Beat.RETURN:
			body.end_pass()
			return_from = body.ground_position
			landing = _landing()
			body.flying_left = landing.x < return_from.x
			body.play_anim(&"fly")
			body.wing_sfx_player.play()
		Beat.DONE:
			# The swoop's last step comes after this beat's, which ends the state: he is put on his landing point here.
			body.ground_position = landing
			body.place()
			state_machine.attack_finished(self)


func _telegraph_time(k: int) -> float:
	return state_machine.flyby_telegraph_time if k == 0 else state_machine.flyby_return_telegraph_time


func _lay_fire(k: int) -> Node2D:
	var sm = state_machine
	var fire := FlybyFire.new()
	fire.name = "FlybyFire"
	fire.direction = pass_dir(k)
	fire.telegraph_time = _telegraph_time(k)
	fire.warn_time = sm.flyby_warn_time
	fire.speed = sm.flyby_speed
	fire.safe_width = sm.flyby_safe_width
	fire.burn_time = sm.flyby_burn_time
	fire.player = sm.get_player()
	fire.boss = body
	fire.add_to_group(sm.HAZARD_GROUP)
	get_tree().current_scene.add_child(fire)
	return fire


# Where he lands for his window: on his start side, by the column the crossing ended in.
func _landing() -> Vector2:
	var sm = state_machine
	var bounds: Rect2 = body.ground_bounds(0.0)
	var x: float = FlybyLayout.entry_x(start_dir) + start_dir * sm.flyby_landing_inset
	return Vector2(x, sm.flyby_landing_y).clamp(bounds.position, bounds.end)


#HIS FLIGHT

func _pass_clip(breathing: bool) -> StringName:
	if not FlybyLayout.final_flyby():
		return &"fly"
	return &"flyby_breath" if breathing else &"flyby_glide"


# The two clips beat their wings frame for frame, so a switch keeps his place in the beat.
func _switch_clip(breathing: bool) -> void:
	var clip := _pass_clip(breathing)
	if body.current_anim == clip:
		return
	var frames: int = BixbyBeastArtLayout.ANIMS[clip].frames.size()
	body.play_anim(clip, &"", mini(body.anim_step, frames - 1))


func _place() -> void:
	var t := clock - beat_start
	match beat:
		Beat.RISE:
			var u := clampf(t / state_machine.flyby_rise_time, 0.0, 1.0)
			body.ground_position = rise_ground
			body.height = lerpf(rise_from, rise_ground.y - FlybyLayout.OFF_TOP_FEET_Y, u * u)
			body.place()
			body.shadow.modulate.a = BixbyBeastArtLayout.SHADOW_ALPHA * (1.0 - u)
			body.shadow.visible = u < 1.0
		Beat.TELEGRAPH, Beat.ENTER, Beat.SWEEP, Beat.EXIT:
			_place_on_pass(pass_index)
		Beat.RETURN:
			var u := clampf(t / state_machine.flyby_return_time, 0.0, 1.0)
			body.ground_position = return_from.lerp(landing, u * u * (3.0 - 2.0 * u))
			body.place()


func _place_on_pass(k: int) -> void:
	body.place_on_pass(Vector2(_mouth(k) - FlybyLayout.exit_offset(pass_dir(k)), FlybyLayout.PASS_ANCHOR_Y))


# Where his lead exit is on pass `k`: waiting off the screen until he flies in, then on the fire's own mouth, then
# speeding off the far side from the column's edge, starting at the sweep's speed and never turning back.
func _mouth(k: int) -> float:
	var sm = state_machine
	var dir := pass_dir(k)
	var speed: float = sm.flyby_speed
	var telegraph := _telegraph_time(k)
	var sweep := FlybyLayout.sweep_time(sm.flyby_safe_width, speed)
	var t: float = clock - pass_starts[k]
	if t < telegraph - sm.flyby_entry_lead:
		return FlybyLayout.start_mouth_x(dir, speed, sm.flyby_entry_lead)
	if t < telegraph + sweep:
		return FlybyLayout.entry_x(dir) + dir * speed * (t - telegraph)
	var edge := FlybyLayout.safe_edge(dir, sm.flyby_safe_width)
	var exit: float = sm.flyby_exit_time
	var u := clampf((t - telegraph - sweep) / exit, 0.0, 1.0)
	var run := absf(FlybyLayout.off_mouth_x(dir) - edge)
	return edge + dir * (speed * exit * u + (run - speed * exit) * u * u)
