extends RefCounted

# greyson_race (coder C): the hype race (plan section 4) run by three bots in his test fight, each on a fresh load,
# his cycle running on its own from Idle. None of them parries; each waits clear of him and, from the pose it
# "reaches him" at, lands a combo on the beat and mashes the finisher's uppercut, once a cycle.
#   idle    never answers: his meter fills in cycle 1 and the spirit bomb takes the fight.
#   slow    reaches him at pose 4: 12 damage a cycle and the meter still gaining, so the bomb takes the fight in
#           cycle 3 with him on 6 HP.
#   decent  reaches him at pose 3: 12 a cycle and the meter gaining less, so he is at 0 HP in cycle 3 with his
#           meter short of full, and the fight goes on into the brawl.
# Every cycle is the real attack 1: four plates thrown and five slams before the poses.

const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const SEED := 20260924
const WAIT := Vector2(400, 880)
# The most game time a bot gets: past cycle 3 by a margin.
const LIMIT := 75.0
# name: the pose it punishes from (-1 for never), and the outcome, cycle and his HP it should end on (-1 for any).
const BOTS := {
	"idle": {"from": -1, "outcome": "loss", "cycle": 1, "health": 30},
	"slow": {"from": 3, "outcome": "loss", "cycle": 3, "health": 6},
	"decent": {"from": 2, "outcome": "brawl", "cycle": 3, "health": 0},
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
	var plates_by_cycle := {}
	var slams_by_cycle := {}
	var first_spoiled := {}
	var note_spoil := func():
		if t.sm.current_state == pose and pose.pose_index >= 0 and pose.spoiled and not first_spoiled.has(t.sm.cycles_started):
			first_spoiled[t.sm.cycles_started] = pose.pose_index + 1
	var throw: Node = t.sm.states["Throw"]
	var slams: Node = t.sm.states["Slams"]
	var start: float = t.clock
	while t.clock - start < LIMIT:
		await t.wait(1)
		if t.sm.current_state == pose and pose.pose_index == 0:
			meter_by_cycle[t.sm.cycles_started] = t.boss.hype
			plates_by_cycle[t.sm.cycles_started] = throw.thrown
			slams_by_cycle[t.sm.cycles_started] = slams.slam_clocks.size()
		note_spoil.call()
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
	t.log_p("%s: %s in cycle %d after %.1f s, his HP %d, his meter at each cycle's first pose %s, now %.1f; the first pose spoiled each cycle %s; plates %s and slams %s a cycle; the outro %s" % [bot, outcome, cycle, t.clock - start, health, meter_by_cycle, t.boss.hype, first_spoiled, plates_by_cycle, slams_by_cycle, "none" if outro == null else ("player_won" if outro.player_won else "player_lost")])
	var plates: int = throw.release_at.size()
	var slammed: int = slams.slams
	t.check(not plates_by_cycle.is_empty() and plates_by_cycle.values().all(func(n): return n == plates) and slams_by_cycle.values().all(func(n): return n == slammed),
		"%s: every cycle the real attack, %d plates and %d slams before the poses" % [bot, plates, slammed])
	t.check(first_spoiled.values().all(func(at): return at == spec.from + 1), "%s: nothing spoils a pose before it reaches him, at pose %d (%s)" % [bot, spec.from + 1, first_spoiled])
	t.check(outcome == spec.outcome and cycle == spec.cycle, "%s: %s in cycle %d (%s in cycle %d)" % [bot, spec.outcome, spec.cycle, outcome, cycle])
	t.check(health == spec.health, "%s: his HP %d at the end (%d)" % [bot, spec.health, health])
	if outcome == "loss":
		t.check(outro != null and not outro.player_won, "%s: the bomb's loss, player_lost" % bot)
	elif outcome == "brawl":
		t.check(t.boss.hype < t.boss.HYPE_MAX, "%s: his meter short of full (%.1f)" % [bot, t.boss.hype])
