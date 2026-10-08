extends RefCounted

# liam_ice: the ice under the player (PlayerScript.set_ice, the floor LiamTremors freezes), on Liam's test scene with
# him parked on his pillar and the player well clear of it, on his state machine's ice knobs. At 60 fps:
#   accel   from rest, full speed (600) in 20 frames +-1, having travelled 100 px +-8
#   slide   let go at full speed: 150 px +-8 to a stop
#   brake   the other way held from full speed: stopped in 100 px +-8
#   turn    a 90 degree turn at full speed: 141 px +-10 on past the corner
#   dash    a dash: its 250 px and then about 84 more sliding, 334 px +-10 in all
#   coast   a punch, the dash's landing beat and a guard break each slide on under the player
#   off     the ice off again: a scripted run matches one made before the floor was ever iced, frame for frame
#   clears  begin_finisher, end_fight and a death each take the ice away

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const START := Vector2(420, 760)
const KEYS := [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W, KEY_Q]
const FULL_SPEED := 600.0
const SETTLE_FRAMES := 60


static func run(t) -> void:
	await enter(t)
	t.log_p("-- a run on a floor never iced, for the last check")
	var never_iced: Array = await scripted_run(t)
	await accel(t)
	await slide(t)
	await brake(t)
	await turn(t)
	await dash(t)
	await coast(t)
	await off(t, never_iced)
	await clears(t)


static func enter(t) -> void:
	await Common.enter(t)
	t.hold_break_gauge(t.boss)


# Keys up, the last move's cooldowns run out, then the player at `at`, still, on a full bar.
static func fresh(t, at: Vector2, iced: bool) -> void:
	for code in KEYS:
		t.release(code)
	await t.wait(SETTLE_FRAMES)
	t.player.set_ice(false)
	t.player.global_position = at
	t.player.velocity = Vector2.ZERO
	t.defense._set_stamina(t.defense.max_stamina)
	t.clear_iframes()
	if iced:
		ice_on(t)
	await t.wait(2)


static func ice_on(t) -> void:
	t.player.set_ice(true, t.sm.ice_accel, t.sm.ice_friction, t.sm.ice_dash_carry)


# Holds `code` until the player is at full speed along x, then a few frames more.
static func to_full_speed(t, code: int) -> void:
	t.press(code)
	await t.wait_until(func(): return absf(t.player.velocity.x) >= FULL_SPEED - 0.01, 60)
	await t.wait(3)


static func accel(t) -> void:
	t.log_p("-- from rest to full speed")
	await fresh(t, START, true)
	var x0: float = t.player.global_position.x
	t.press(KEY_RIGHT)
	var moving := 0
	var travelled := -1.0
	for i in 60:
		await t.physics_frame
		if t.player.velocity.x > 0.0:
			moving += 1
		if t.player.velocity.x >= FULL_SPEED - 0.01:
			travelled = t.player.global_position.x - x0
			break
	t.release(KEY_RIGHT)
	t.log_p("full speed after %d frames, %.1f px" % [moving, travelled])
	t.check(absi(moving - 20) <= 1, "600 px/s in 20 frames +-1 (%d)" % moving)
	t.check(absf(travelled - 100.0) <= 8.0, "having travelled 100 px +-8 (%.1f)" % travelled)


static func slide(t) -> void:
	t.log_p("-- let go at full speed")
	await fresh(t, START, true)
	await to_full_speed(t, KEY_RIGHT)
	t.release(KEY_RIGHT)
	var slid: float = await x_until_stopped(t)
	t.log_p("slid %.1f px" % slid)
	t.check(absf(slid - 150.0) <= 8.0, "slides 150 px +-8 to a stop (%.1f)" % slid)


static func brake(t) -> void:
	t.log_p("-- braking by holding the other way")
	await fresh(t, START, true)
	await to_full_speed(t, KEY_RIGHT)
	t.release(KEY_RIGHT)
	t.press(KEY_LEFT)
	var stopped_in: float = await x_until_stopped(t)
	t.release(KEY_LEFT)
	t.log_p("stopped in %.1f px" % stopped_in)
	t.check(absf(stopped_in - 100.0) <= 8.0, "stops in 100 px +-8 (%.1f)" % stopped_in)


static func turn(t) -> void:
	t.log_p("-- a 90 degree turn at full speed")
	await fresh(t, Vector2(300, 400), true)
	await to_full_speed(t, KEY_RIGHT)
	t.release(KEY_RIGHT)
	t.press(KEY_DOWN)
	var past: float = await x_until_stopped(t)
	t.release(KEY_DOWN)
	t.log_p("carried %.1f px past the corner" % past)
	t.check(absf(past - 141.0) <= 10.0, "carries 141 px +-10 past the corner (%.1f)" % past)


# How far right the player goes from the last frame at full speed, which is when the new input took, until they stop
# going right.
static func x_until_stopped(t) -> float:
	var x0 := [t.player.global_position.x]
	await t.wait_until(func():
		if t.player.velocity.x >= FULL_SPEED - 0.01:
			x0[0] = t.player.global_position.x
		return t.player.velocity.x <= 0.0, 120)
	return t.player.global_position.x - x0[0]


static func dash(t) -> void:
	t.log_p("-- a dash")
	await fresh(t, START, true)
	var x0: float = t.player.global_position.x
	var recovering := {"frames": 0, "moved": 0.0}
	var last := [x0]
	var watch := func():
		var x: float = t.player.global_position.x
		if t.player.state_machine.current_state.name == "DashRecovery":
			recovering.frames += 1
			recovering.moved += x - last[0]
		last[0] = x
	t.physics_frame.connect(watch)
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	t.release(KEY_RIGHT)
	await t.wait_until(func(): return not t.player.is_dodging, 20)
	var dashed: float = t.player.global_position.x - x0
	await t.wait_until(func(): return t.player.velocity.x <= 0.0, 120)
	t.physics_frame.disconnect(watch)
	var total: float = t.player.global_position.x - x0
	t.log_p("dash %.1f px, %.1f in all; %.1f px over %d frames of its landing beat" % [dashed, total, recovering.moved, recovering.frames])
	t.check(absf(total - 334.0) <= 10.0, "250 px and then about 84 more sliding: 334 +-10 (%.1f)" % total)
	t.check(recovering.frames > 0 and recovering.moved > 20.0, "the landing beat slides on (%.1f px)" % recovering.moved)


static func coast(t) -> void:
	t.log_p("-- a punch slides on")
	await fresh(t, START, true)
	await to_full_speed(t, KEY_RIGHT)
	var punching := {"frames": 0, "moved": 0.0, "first_speed": -1.0}
	var last := [t.player.global_position.x]
	var watch := func():
		var x: float = t.player.global_position.x
		if t.player.state_machine.current_state.name == "Punching":
			if punching.frames == 0:
				punching.first_speed = t.player.velocity.x
			punching.frames += 1
			punching.moved += x - last[0]
		last[0] = x
	t.physics_frame.connect(watch)
	t.release(KEY_RIGHT)
	t.tap(KEY_Q)
	await t.wait_until(func(): return t.player.state_machine.current_state.name == "Punching", 20)
	await t.wait_until(func(): return t.player.state_machine.current_state.name != "Punching", 60)
	t.physics_frame.disconnect(watch)
	t.log_p("punching %d frames: slid %.1f px, from %.0f px/s" % [punching.frames, punching.moved, punching.first_speed])
	t.check(punching.frames > 0 and punching.moved > 80.0 and punching.first_speed > 500.0, "the player slides on through the punch")

	t.log_p("-- a guard break slides on")
	await fresh(t, START, true)
	await to_full_speed(t, KEY_RIGHT)
	t.release(KEY_RIGHT)
	var x0: float = t.player.global_position.x
	t.defense._start_guard_break()
	await t.wait_until(func(): return t.player.state_machine.current_state.name == "GuardBroken", 10)
	var stunned_at: float = t.player.global_position.x
	await t.wait(20)
	var stunned_moved: float = t.player.global_position.x - stunned_at
	t.defense.clear_guard_break()
	t.log_p("stunned from %.1f px in, slid %.1f px in 20 frames of it" % [stunned_at - x0, stunned_moved])
	t.check(stunned_moved > 60.0, "the player slides on through the stun (%.1f px)" % stunned_moved)


# The same presses as the run before the floor was ever iced, with the ice on and back off in between.
static func off(t, never_iced: Array) -> void:
	t.log_p("-- the ice off again")
	var after: Array = await scripted_run(t)
	var first_diff := -1
	for i in mini(after.size(), never_iced.size()):
		if after[i] != never_iced[i]:
			first_diff = i
			break
	if first_diff >= 0:
		t.log_p("first different frame %d: %s against %s" % [first_diff, after[first_diff], never_iced[first_diff]])
	t.check(after.size() == never_iced.size() and first_diff < 0, "a scripted run with the ice off matches the never-iced one, frame for frame (%d frames)" % after.size())


static func clears(t) -> void:
	t.log_p("-- what takes the ice away")
	await fresh(t, START, true)
	t.player.begin_finisher()
	var after_finisher: bool = t.player.on_ice
	t.player.end_finisher(false)
	ice_on(t)
	t.player.end_fight()
	var after_end: bool = t.player.on_ice
	ice_on(t)
	t.player.playerHealth = 1
	t.player._apply_damage(load("res://Scripts/HitInfo.gd").make(&"liam_tremor", t.dummy_source(), t.player.global_position))
	var after_death: bool = t.player.on_ice
	t.check(not after_finisher, "begin_finisher takes it away")
	t.check(not after_end, "end_fight takes it away")
	t.check(t.player.playerHealth == 0 and not after_death, "and a death does")


# Walks, a diagonal, a dash, a punch standing and one walking, a dash left and a parry press, from START: each frame's
# position, velocity and state.
static func scripted_run(t) -> Array:
	await fresh(t, START, false)
	var frames := []
	var watch := func():
		frames.append("%s %s %s %s" % [t.player.global_position, t.player.velocity, t.player.state_machine.current_state.name, t.player.is_dodging])
	t.physics_frame.connect(watch)
	t.press(KEY_RIGHT)
	await t.wait(24)
	t.release(KEY_RIGHT)
	await t.wait(12)
	t.press(KEY_UP)
	t.press(KEY_RIGHT)
	await t.wait(18)
	t.release(KEY_UP)
	t.release(KEY_RIGHT)
	await t.wait(10)
	t.press(KEY_DOWN)
	t.tap(KEY_W)
	await t.wait(8)
	t.release(KEY_DOWN)
	await t.wait(36)
	t.tap(KEY_Q)
	await t.wait(28)
	t.press(KEY_LEFT)
	await t.wait(10)
	t.tap(KEY_Q)
	await t.wait(18)
	t.release(KEY_LEFT)
	await t.wait(30)
	t.press(KEY_LEFT)
	t.tap(KEY_W)
	await t.wait(5)
	t.release(KEY_LEFT)
	await t.wait(36)
	t.press(KEY_SHIFT)
	await t.wait(4)
	t.release(KEY_SHIFT)
	await t.wait(24)
	t.physics_frame.disconnect(watch)
	return frames
