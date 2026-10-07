extends RefCounted

# liam_loop: his four attacks as one loop (addendum 3 D, addendum 4), on his test scene. Light: the player is kept
# unhurt and only dashes each lunge.
#   loop      from the Tsunami, every attack running out on its own: Tsunami, Tremors, Firestorm, Lunge (three dodges),
#             each ended by his wind's reset to RESET_SPOT (+-1, or a skip for a player already within launch_skip of
#             it), and back to the Tsunami. Each attack's length is logged.
#   topples   a sixth pillar hit in each of attacks 1-3: after his window the loop goes on with the next attack, and
#             the floor is as the topple left it (the flood in the Tsunami, the ice in Tremors)

const Common := preload("res://art_source/defense_tests/liam/common.gd")

const ORDER := ["Tsunami", "Tremors", "Firestorm", "Lunge", "Tsunami"]
# The lunge's dash: this long after each badge, straight at him.
const DODGE_AT := 0.3


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	await loop(t)
	for attack in ["Tsunami", "Tremors", "Firestorm"]:
		await topple(t, attack)


static func loop(t) -> void:
	t.log_p("-- one whole loop, every attack running out")
	await Common.clear(t)
	await Common.fresh(t, t.sm.RESET_SPOT)
	var lunge: Node = t.sm.states["Lunge"]
	var seen := []
	var started := {}
	var lengths := []
	var landings := []
	var badges := [lunge.tells.size()]
	var dodge_frame := [-1]
	var watch := func():
		t.player.is_invincible = true
		t.player.playerHealth = 1000
		var state: String = Common.state(t)
		if seen.is_empty() or seen[-1] != state:
			if not seen.is_empty() and seen[-1] == "RoundBlast":
				var skipped: bool = t.player.global_position.distance_to(t.sm.RESET_SPOT) <= t.sm.launch_skip
				landings.append([t.player.global_position, skipped])
			if state == "RoundBlast" and not seen.is_empty():
				lengths.append("%s %.2f s" % [seen[-1], t.defense.clock - started.get(seen[-1], t.defense.clock)])
			seen.append(state)
			started[state] = t.defense.clock
		# Each badge: a dash straight at him DODGE_AT later.
		if lunge.tells.size() > badges[0]:
			badges[0] = lunge.tells.size()
			dodge_frame[0] = Engine.get_physics_frames() + roundi(DODGE_AT * 60.0) - 1
		if dodge_frame[0] >= 0 and Engine.get_physics_frames() >= dodge_frame[0]:
			dodge_frame[0] = -1
			t.clear_iframes()
			t.tap(KEY_W)
	t.physics_frame.connect(watch)
	Common.start(t, "Tsunami")
	var back: bool = await t.wait_until(func(): return seen.size() >= 9, 60 * 90)
	t.physics_frame.disconnect(watch)
	t.player.is_invincible = false
	var attacks: Array = seen.filter(func(s): return s != "RoundBlast")
	var resets: Array = seen.filter(func(s): return s == "RoundBlast")
	var off: Array = landings.filter(func(l): return not l[1] and l[0].distance_to(t.sm.RESET_SPOT) > 1.0)
	t.log_p("the loop: %s; lengths %s; reset landings %s; lunge results %s" % [seen, lengths, landings.map(func(l): return "%s%s" % [l[0], " (skipped)" if l[1] else ""]), lunge.results])
	t.check(back and attacks.slice(0, 5) == ORDER, "Tsunami, Tremors, Firestorm, Lunge, then the Tsunami again (%s)" % [attacks])
	t.check(resets.size() >= 4 and seen.slice(0, 9) == ["Tsunami", "RoundBlast", "Tremors", "RoundBlast", "Firestorm", "RoundBlast", "Lunge", "RoundBlast", "Tsunami"], "his wind's reset between every two")
	t.check(landings.size() >= 4 and off.is_empty(), "each reset puts the player on %s (+-1), or skips one already there" % t.sm.RESET_SPOT)
	Common.hold(t)


# A sixth hit in `attack`: his window, then the attack after it, the floor as the topple left it.
static func topple(t, attack: String) -> void:
	t.log_p("-- a topple in %s" % attack)
	await Common.clear(t)
	t.boss.pillar.stand_up_now()
	t.boss.pillar.set_shielded(true)
	t.boss.stand_on_pillar()
	t.boss.perch()
	await Common.fresh(t, t.sm.FRONT_SPOT)
	var keep := func():
		t.player.is_invincible = true
		t.player.playerHealth = 1000
	t.physics_frame.connect(keep)
	if attack == "Tsunami":
		t.boss.flood.add_water(0.5)
	Common.start(t, attack)
	await t.wait_until(func(): return not t.boss.pillar.shielded, 60 * 8)
	# Not Common.fresh, whose clearing of the i-frames comes after this frame's `keep`: the Tsunami opens with a wave
	# over the front spot (liam_tsunami_gate).
	t.player.unlock_actions()
	t.player.set_ice(false)
	t.player.global_position = t.sm.FRONT_SPOT
	t.player.velocity = Vector2.ZERO
	await t.wait(2)
	var iced: bool = t.boss.flood.is_iced()
	var water: float = t.boss.flood.coverage
	t.sm.pillar_hits = t.sm.hits_to_topple - 1
	var toppled: bool = await Common.punch_pillar(t)
	var downed: bool = await t.wait_until(func(): return Common.state(t) == "Downed", 90)
	var after: String = String(t.sm.ATTACK_ROTATION[(t.sm.ATTACK_ROTATION.find(StringName(attack)) + 1) % t.sm.ATTACK_ROTATION.size()])
	var next: bool = await t.wait_until(func(): return Common.state(t) == after, 60 * 14)
	t.physics_frame.disconnect(keep)
	t.player.is_invincible = false
	var still_iced: bool = t.boss.flood.is_iced()
	var water_now: float = t.boss.flood.coverage
	t.log_p("toppled %s, down %s, then %s (want %s); the flood %.3f -> %.3f, iced %s -> %s" % [toppled, downed, Common.state(t), after, water, water_now, iced, still_iced])
	t.check(toppled and downed and next, "a topple in %s: his window, then %s" % [attack, after])
	match attack:
		"Tsunami":
			t.check(water_now >= water and water >= 0.5, "the flood kept")
		"Tremors":
			t.check(iced and still_iced, "the ice kept")
	Common.hold(t)
