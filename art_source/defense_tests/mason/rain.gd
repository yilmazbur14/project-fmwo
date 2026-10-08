extends RefCounted

# mason_rain (2026-10-04, the Nugget Fastball plan's P1 fix): phase one's Carter call with a light nugget rain under it
# (MasonNuggetShower run as "CarterRain", MasonStateMachine.carter_rain and rain_*), turned on for itself, Mason on his
# wall column, --fixed-fps 60.
#   - stood through by a still player, it is mason_combined's attack on phase one's numbers (mason_check_attack): all
#     six of Carter's drops, nuggets landing before his first slam and between every two, none within
#     slam_clear_before of a slam or slam_clear_after past its hitbox, somewhere free to stand at every moment and in
#     reach of every marker, his badge up through the call, and nothing left behind;
#   - walking loops steered on the arrow keys, which used to come through his call untouched: rect, horiz,
#     horiz_bottom, back_rope and vert each take 1 hit a call or more on average over 3 seeds (circle and big_circle
#     are logged only: lead aim only catches a straight walk);
#   - the parrying bot (mason_combined's), planted in Carter's marker from 4 spots: never hit by Carter, and at most
#     one nugget a call; the dodging bot at most MASON_BOT_MAX_HITS;
#   - the impact sounds of his bombs and nuggets (MasonImpactThrottle) start at most 11 times in any second, through
#     the rain and through phase two's combined attack.

const STAND_AT := Vector2(760, 640)
const LOOPS := ["rect", "horiz", "horiz_bottom", "back_rope", "vert", "circle", "big_circle"]
const GATED := ["rect", "horiz", "horiz_bottom", "back_rope", "vert"]
const SEEDS := 3
const LOOP_SPEED := 600.0
const STEER_DEADZONE := 8.0
const MAX_NUGGETS_PLANTED := 1
const MAX_STARTS_PER_SECOND := 11
const ATTACK_FRAMES := 1200


static func run(t) -> void:
	t.fight = "mason"
	if not await t.load_gauged():
		return
	await _stood(t)
	await _loops(t)
	await _bots(t)
	await _sounds(t)


# Idle on his wall column in phase one with the rain on, the player at `at`.
static func _ready_rain(t, at: Vector2) -> void:
	await t.reset_gauged(t.fight_spec.home)
	t.hold_break_gauge(t.boss)
	t.boss.global_position = t.MASON_COMBINED_AT
	t.sm.rest_point = t.boss.global_position + t.sm.BOMB_SPAWN_OFFSET
	t.sm.carter_rain = true
	t.sm.cycle_phase = 0
	t.sm.finishers = []
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	t.player.playerHealth = 1000
	await t.settle_player(at)
	t.clear_iframes()


static func _rain(t) -> bool:
	t.sm.run_attack("CarterRain")
	return await t.wait_until(func() -> bool: return t.sm.current_state.name != "NuggetShower", ATTACK_FRAMES)


static func _stood(t) -> void:
	t.log_p("-- a still player through the call and its rain")
	await _ready_rain(t, STAND_AT)
	var hits := []
	var on_hit := func(hit) -> void: hits.append(hit.attack_id)
	t.defense.hit_taken.connect(on_hit)
	t.mason_new_log()
	t.physics_frame.connect(t.mason_record)
	t.sm.run_attack("CarterRain")
	var shower: Node = t.sm.states["NuggetShower"]
	var raining: bool = shower.rain and shower.with_carter
	var ended: bool = await t.wait_until(func() -> bool: return t.sm.current_state.name != "NuggetShower", ATTACK_FRAMES)
	t.physics_frame.disconnect(t.mason_record)
	t.defense.hit_taken.disconnect(on_hit)
	var landed: int = t.mason_log.nuggets.values().filter(func(n): return n.landed >= 0.0).size()
	t.log_p("standing still: %d hits %s; %d nuggets landed of %d markers" % [hits.size(), hits, landed, t.sm.rain_count])
	t.check(raining, "run as CarterRain it is the shower with Carter called in and the rain's numbers")
	t.mason_check_attack("the rain", ended, false)


# Where a loop has got to `elapsed` seconds in, walking at LOOP_SPEED (the playtest's loops, scratchpad
# playtest_1004/mason/probes/sweep.gd).
static func loop_at(loop_name: String, elapsed: float) -> Vector2:
	var d := elapsed * LOOP_SPEED
	match loop_name:
		"rect":
			var r := Rect2(240, 250, 1440, 580)
			var u := fposmod(d, 2.0 * (r.size.x + r.size.y))
			if u < r.size.x:
				return r.position + Vector2(u, 0)
			u -= r.size.x
			if u < r.size.y:
				return Vector2(r.end.x, r.position.y + u)
			u -= r.size.y
			if u < r.size.x:
				return Vector2(r.end.x - u, r.end.y)
			u -= r.size.x
			return Vector2(r.position.x, r.end.y - u)
		"horiz":
			var u := fposmod(d, 2.0 * 1520.0)
			return Vector2(200 + (u if u < 1520.0 else 3040.0 - u), 540)
		"horiz_bottom":
			var u := fposmod(d, 2.0 * 1600.0)
			return Vector2(160 + (u if u < 1600.0 else 3200.0 - u), 920)
		"back_rope":
			var u := fposmod(d, 2.0 * 1600.0)
			return Vector2(160 + (u if u < 1600.0 else 3200.0 - u), 150)
		"vert":
			var u := fposmod(d, 2.0 * 720.0)
			return Vector2(960, 190 + (u if u < 720.0 else 1440.0 - u))
		"circle":
			return Vector2(960, 560) + Vector2.from_angle(d / 160.0) * 160.0
		"big_circle":
			return Vector2(960, 560) + Vector2.from_angle(d / 330.0) * Vector2(330.0 * 2.2, 330.0)
	return Vector2(960, 540)


# Walked on the arrow keys, so the player's own velocity is what his lead aim reads.
static func _steer(t, held: Dictionary, to: Vector2) -> void:
	var gap: Vector2 = to - t.player.global_position
	var want := {KEY_LEFT: gap.x < -STEER_DEADZONE, KEY_RIGHT: gap.x > STEER_DEADZONE, KEY_UP: gap.y < -STEER_DEADZONE, KEY_DOWN: gap.y > STEER_DEADZONE}
	for code in want:
		if want[code] == held.get(code, false):
			continue
		if want[code]:
			t.press(code)
		else:
			t.release(code)
		held[code] = want[code]


static func _loops(t) -> void:
	t.log_p("-- walking loops at %.0f px/s through it, %d seeds" % [LOOP_SPEED, SEEDS])
	var hits := []
	var on_hit := func(hit) -> void:
		if hit.attack_id == &"mason_nugget" or hit.attack_id == &"carter_elbow_drop":
			hits.append(hit.attack_id)
	t.defense.hit_taken.connect(on_hit)
	for loop_name in LOOPS:
		var per := []
		for s in SEEDS:
			seed(20261004 + s * 13)
			var offset := s * 1.37
			await _ready_rain(t, loop_at(loop_name, offset))
			var held := {}
			var t0: float = t.defense.clock
			var walk := func() -> void: _steer(t, held, loop_at(loop_name, t.defense.clock - t0 + offset))
			hits.clear()
			t.physics_frame.connect(walk)
			await _rain(t)
			t.physics_frame.disconnect(walk)
			_steer(t, held, t.player.global_position)
			per.append(hits.size())
		var mean: float = float(per.reduce(func(a, b): return a + b, 0)) / per.size()
		t.log_p("%s: hits per call %s, %.2f on average" % [loop_name, per, mean])
		if loop_name in GATED:
			t.check(mean >= 1.0, "%s: the loop no longer comes through it, %.2f hits a call (%s)" % [loop_name, mean, per])
	t.defense.hit_taken.disconnect(on_hit)


static func _bots(t) -> void:
	var timed := []
	var on_hit := func(hit) -> void: timed.append({"t": t.defense.clock, "id": hit.attack_id})
	t.defense.hit_taken.connect(on_hit)
	for parry in [true, false]:
		t.log_p("-- the %s bot, at a person's pace" % ["parrying" if parry else "dodging"])
		for i in t.MASON_BOT_SPOTS.size():
			seed(20261004 + i)
			await _ready_rain(t, t.MASON_BOT_SPOTS[i])
			t.player.playerHealth = t.MASON_FULL_HEALTH
			timed.clear()
			t.mason_bot_reset(parry)
			t.sm.run_attack("CarterRain")
			t.physics_frame.connect(t.mason_bot_frame)
			var through: bool = await t.wait_until(func() -> bool: return t.sm.current_state.name != "NuggetShower" or t.player.fight_over, ATTACK_FRAMES)
			t.physics_frame.disconnect(t.mason_bot_frame)
			t.mason_bot_hold(Vector2.ZERO)
			t.release(KEY_SHIFT)
			var carter: int = timed.filter(func(h): return h.id == &"carter_elbow_drop").size()
			var nuggets: int = timed.filter(func(h): return h.id == &"mason_nugget").size()
			t.log_p("from %s: Carter %d, nuggets %d, %d presses, %d dashes" % [t.MASON_BOT_SPOTS[i], carter, nuggets, t.mason_bot.presses, t.mason_bot.dashes])
			if parry:
				t.check(through and carter == 0 and nuggets <= MAX_NUGGETS_PLANTED, "from %s the parrying bot is never hit by Carter, and by at most %d nugget (%d)" % [t.MASON_BOT_SPOTS[i], MAX_NUGGETS_PLANTED, nuggets])
			else:
				t.check(through and carter + nuggets <= t.MASON_BOT_MAX_HITS, "from %s the dodging bot is hit at most %d times (%d)" % [t.MASON_BOT_SPOTS[i], t.MASON_BOT_MAX_HITS, carter + nuggets])
			if t.player.fight_over:
				return
	t.defense.hit_taken.disconnect(on_hit)


static func _sounds(t) -> void:
	for attack in ["the rain", "phase two's combined attack"]:
		await _ready_rain(t, STAND_AT)
		t.root.get_node("GameProgress").playtest_invincible = true
		var starts := []
		var was := {}
		var count := func() -> void:
			for hazard in t.live_hazards():
				for sfx in hazard.find_children("*", "AudioStreamPlayer", false, false):
					var id: int = sfx.get_instance_id()
					if sfx.playing and not was.get(id, false) and str(sfx.stream.resource_path).ends_with("hit_impact.ogg"):
						starts.append(t.defense.clock)
					was[id] = sfx.playing
		t.physics_frame.connect(count)
		if attack == "the rain":
			await _rain(t)
		else:
			t.boss.phase_two = true
			t.boss.boss_health = floori(t.boss.get_max_health() * t.boss.PHASE_TWO_RATIO)
			t.sm.cycle_phase = 1
			t.sm.run_attack("NuggetShower")
			await t.wait_until(func() -> bool: return t.sm.current_state.name != "NuggetShower", ATTACK_FRAMES)
		t.physics_frame.disconnect(count)
		t.root.get_node("GameProgress").playtest_invincible = false
		var peak := 0
		for i in starts.size():
			peak = maxi(peak, starts.filter(func(s): return s >= starts[i] and s - starts[i] < 1.0).size())
		t.log_p("%s: %d impact sounds started, at most %d in any one second" % [attack, starts.size(), peak])
		t.check(not starts.is_empty() and peak <= MAX_STARTS_PER_SECOND, "%s: the impact sounds start at most %d times a second (%d)" % [attack, MAX_STARTS_PER_SECOND, peak])
