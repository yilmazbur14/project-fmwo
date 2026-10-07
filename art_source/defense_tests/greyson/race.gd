extends RefCounted

# greyson_race (coder C; coder B since the 2026-09-30 pace): the hype race (plan section 4) run by three bots in his
# test fight, each on a fresh load, his cycle running on its own from Idle. None of them parries; each waits clear of
# him and, from the pose it "reaches him" at, lands a combo and mashes the finisher's uppercut, once a cycle. His
# meter banks two cells a clean pose, so three clean poses fire the spirit bomb, and any hit that lands empties it.
#   idle    never answers: his meter fills at the end of pose 3 of cycle 1 and the spirit bomb takes the fight.
#   slow    reaches him at pose 4: too late, the bomb goes at the end of pose 3 of cycle 1, him untouched.
#   decent  reaches him at pose 3: two banks (4 cells), then its first punch empties the meter and the combo and the
#           uppercut take 23 a cycle, so he is at 0 HP in cycle 4, the meter never over 4 cells, and the fight goes
#           on into the brawl.
# Every cycle is the real attack 1: six plates thrown and four slams (eight zones) before the poses. The plates fly on
# into the poses (the user, 2026-09-28); the next throw cuts short any still flying as it begins
# (GreysonStateMachine.plate_wait_cap), and none is left flying into the brawl or the outro.

const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const SEED := 20260924
const WAIT := Vector2(400, 880)
# The most game time a bot gets: past cycle 4 by a margin (a punished cycle is about 12 s at the 2026-09-30 pace).
const LIMIT := 70.0
# name: the pose it punishes from (-1 for never), and the outcome, cycle and his HP it should end on (-1 for any).
const BOTS := {
	"idle": {"from": -1, "outcome": "loss", "cycle": 1, "health": 75},
	"slow": {"from": 3, "outcome": "loss", "cycle": 1, "health": 75},
	"decent": {"from": 2, "outcome": "brawl", "cycle": 4, "health": 0},
}


static func run(t) -> void:
	for bot in BOTS:
		await race(t, bot, BOTS[bot])


static func enter(t) -> void:
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	await t.load_fight("greyson")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = SEED
	t.player.playerHealth = 1000000
	t.player.get_node("Finisher").min_press_interval = 0.0
	t.player.global_position = WAIT
	await t.wait(3)


static func race(t, bot: String, spec: Dictionary) -> void:
	await enter(t)
	t.log_p("-- the %s bot" % bot)
	var pose: Node = t.sm.states["Pose"]
	var bomb: Node = t.sm.states["SpiritBomb"]
	var finisher: Node = t.player.get_node("Finisher")
	var punished_in := -1
	var bomb_cycle := -1
	var bomb_health := -1
	var meter_by_cycle := {}
	var high_water := [0.0]
	var plates_by_cycle := {}
	var slams_by_cycle := {}
	var first_spoiled := {}
	var note_spoil := func():
		if t.sm.current_state == pose and pose.pose_index >= 0 and pose.spoiled and not first_spoiled.has(t.sm.cycles_started):
			first_spoiled[t.sm.cycles_started] = pose.pose_index + 1
	var throw: Node = t.sm.states["Throw"]
	var slams: Node = t.sm.states["Slams"]
	var idle: Node = t.sm.states["Idle"]
	var throws_seen := [throw.entered_count]
	var flying_at_throw := {}
	var flying_at_poses := {}
	var held_for_plates := {}
	var start: float = t.clock
	while t.clock - start < LIMIT:
		await t.wait(1)
		if throw.entered_count != throws_seen[0]:
			throws_seen[0] = throw.entered_count
			flying_at_throw[t.sm.cycles_started] = t.hazards_of("GreysonPlateScript.gd").filter(func(p): return not p.down).size()
		# His breath over and the throw held back for his last throw's plates (GreysonStateMachine.throw_ready).
		if t.sm.current_state == idle and not t.sm.throw_ready() and is_equal_approx(t.sm.beat_timer.wait_time, t.sm.gauge_wait_step):
			held_for_plates[t.sm.cycles_started] = held_for_plates.get(t.sm.cycles_started, 0.0) + 1.0 / 60.0
		if t.sm.current_state == pose and pose.pose_index == 0:
			if not flying_at_poses.has(t.sm.cycles_started):
				flying_at_poses[t.sm.cycles_started] = t.sm.flying_plates().size()
			meter_by_cycle[t.sm.cycles_started] = t.boss.hype
			plates_by_cycle[t.sm.cycles_started] = throw.thrown
			slams_by_cycle[t.sm.cycles_started] = slams.slam_clocks.size()
		note_spoil.call()
		high_water[0] = maxf(high_water[0], t.boss.hype)
		if t.sm.current_state == bomb and bomb_cycle < 0:
			bomb_cycle = t.sm.cycles_started
			bomb_health = t.boss.boss_health
		if t.root.has_node("FightOutro") or t.sm.final_brawl_entered:
			break
		if spec.from >= 0 and t.sm.current_state == pose and pose.pose_index == spec.from and punished_in != t.sm.cycles_started:
			punished_in = t.sm.cycles_started
			t.player.global_position = t._bot_punch_spot()
			for n in 3:
				await t.swing()
				note_spoil.call()
				if n < 2:
					await t.wait(6)
			if await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120):
				await t.mash_finisher()
			await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 300)
			t.player.global_position = WAIT
	await t.wait(2)
	var lingering: int = load("res://art_source/defense_tests/greyson/plates.gd").flying_anywhere(t).size()
	var outcome := "none"
	var cycle: int = t.sm.cycles_started
	var health: int = t.boss.boss_health
	if t.sm.final_brawl_entered:
		outcome = "brawl"
	elif bomb_cycle >= 0:
		outcome = "loss"
		cycle = bomb_cycle
		health = bomb_health
	var outro: Node = t.root.get_node_or_null("FightOutro")
	t.log_p("%s: %s in cycle %d after %.1f s, his HP %d, his meter at each cycle's first pose %s, at most %.1f, now %.1f; the first pose spoiled each cycle %s; plates %s and slams %s a cycle; plates still flying as each throw began %s and as its poses began %s, the throw held for them %s s, cut short at each throw %s (their ropes %s); %d left flying at the end; the outro %s" % [bot, outcome, cycle, t.clock - start, health, meter_by_cycle, high_water[0], t.boss.hype, first_spoiled, plates_by_cycle, slams_by_cycle, flying_at_throw, flying_at_poses, held_for_plates, t.sm.plates_cut, t.sm.cut_plate_ropes, lingering, "none" if outro == null else ("player_won" if outro.player_won else "player_lost")])
	var plates: int = throw.release_at.size()
	var slammed: int = slams.slams
	t.check(not plates_by_cycle.is_empty() and plates_by_cycle.values().all(func(n): return n == plates) and slams_by_cycle.values().all(func(n): return n == slammed),
		"%s: every cycle the real attack, %d plates and %d slams before the poses" % [bot, plates, slammed])
	t.check(not flying_at_throw.is_empty() and flying_at_throw.values().all(func(n): return n == 0),
		"%s: no plate still flying as a throw begins (%s)" % [bot, flying_at_throw])
	t.check(lingering == 0, "%s: none left flying into the %s (%d)" % [bot, "brawl" if outcome == "brawl" else "outro", lingering])
	t.check(first_spoiled.values().all(func(at): return at == spec.from + 1), "%s: nothing spoils a pose before it reaches him, at pose %d (%s)" % [bot, spec.from + 1, first_spoiled])
	t.check(outcome == spec.outcome and cycle == spec.cycle, "%s: %s in cycle %d (%s in cycle %d)" % [bot, spec.outcome, spec.cycle, outcome, cycle])
	t.check(health == spec.health, "%s: his HP %d at the end (%d)" % [bot, spec.health, health])
	if outcome == "loss":
		t.check(outro != null and not outro.player_won, "%s: the bomb's loss, player_lost" % bot)
	elif outcome == "brawl":
		t.check(high_water[0] < t.boss.HYPE_MAX, "%s: his meter never full (at most %.1f)" % [bot, high_water[0]])
