extends RefCounted

# danny_slams (coder C, then Danny D for Addendum 1): Danny's dodge-first Sumo Smash string (DannyBossSlams,
# DannyBossSplash, DannyBossOnBack) in his fight, his cycle parked and the string started from Idle. The first four
# landings are hops: yellow, dodge only, each throwing a worm splash round it that roots a player still in its zone.
# The fifth is the big one: red, the one parry, and the one quake ring.
#   walk       0.25 s straight down from each hop's latch, then out of the fifth sideways and a dash through its
#              ring: no hit and no root.
#   step       hop 1 walked, then 50 px down at hop 2's latch, off the footprint but in the splash: rooted at
#              landing 2 with STUCK!, the third lands on them, and they are free again the step after it.
#   trap       hops 1-3 walked, then splashed at the fourth: the big one's badge withheld, it hits for 2, its ring
#              spares them, then his nap.
#   parry5     the hops walked up from low on the floor, the big one parried by the top rope: no ring, the bounce onto
#              his back beside them and lower than it landed, his lying box under the top rope and the boss bar and
#              level with them, his back for 3.0 s with a cap of 6 and no regen, then back_roll, Idle and the Spit,
#              with no nap.
#   finisher5  the big one parried, then a combo on his back, its third charged: the single-bar finisher's uppercut
#              ends his time on his back early.
#   dash       dashes through hops 1 and 3 and the big one, walks 2 and 4: three DODGED, at least two reads, no root,
#              and the ring spares them.
#   hit        nothing at all: the first, third and fifth land, 1 + 1 + 2 half-hearts.
#   press      a fresh press as hop 1 lands: HIT, not PARRIED, and the press's whiff paid.
#   top        (the 2026-10-04 playtest) nothing at all, feet at y 190 under the top rope, where the hops' spots used to
#              stop at WALK_RECT's top (y 300) and never reach them: every hop now comes down with them in its footprint
#              (the first and third land, the i-frames cover the second and fourth), each yellow ring whole on screen,
#              and the big one still lands on WALK_RECT, off them, its ring left to answer.
#   far_left   (the 2026-10-04 tuning) nothing at all, feet in the bottom-left corner, him by the right rope: the first
#              hop, which set off at track_speed from where he stood and came down short of them, leaps the whole
#              ring and lands on them, and every hop after it does too (the first and third land).
#   far_right  the same mirrored: feet in the top-right corner under the top rope, him by the left rope.
#   step_off   (the 2026-10-06 tuning, puddle_grace 0.35) still until hop 1 lands on them, then walking off its spot from
#              the model's reaction to a new tell, 0.25 s after the landing: the puddle it leaves there never roots them.
#   trail      (the 2026-10-06 tuning) a Spit, then a nine-hop string, roots held off: every hop lays its puddle, never
#              more than trail_max of the string's live at once (older ones dry), and never more than eight in all.
#   react      (the 2026-10-04 tuning, the splash at its tuned splash_radius) walk's answer from the experienced-player
#              model's learned reaction, 0.20 s after each hop's latch: every splash still cleared on foot before its
#              landing, so no hit and no root.
# Every tier: the landings at 1.45, 2.35, 3.25, 4.15 and 5.45 s on his own clock, to the frame; the tuck and the
# landings whole on screen side to side (his spot kept Layout.STRING_REACH in from the screen's sides); a yellow ring over
# latches 1-4 and the strong red badge over the fifth, unless the player is stuck, and never outside a latch or a
# drop; exactly one ring, and only after an unparried fifth; never more than eight puddles live. After an unparried
# fifth his nap, a player his footprint caught slid out beside him, the floor round him clear, and a way to him.

const Spit := preload("res://art_source/defense_tests/danny/spit.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const RING_SCRIPT := "res://Scripts/DannyBossQuakeRingScript.gd"
const HIT_INFO := "res://Scripts/HitInfo.gd"
const SEED := 20260924
const FRAME := 1.0 / 60.0
const LANDINGS: Array[float] = [1.45, 2.35, 3.25, 4.15, 5.45]
# Where each answer starts: the walkers high on the floor, with room for four walks down under them; parry5 low,
# to walk up them, so the big one lands by the top rope.
const STARTS := {
	"walk": Vector2(760, 330), "step": Vector2(760, 330), "trap": Vector2(760, 330), "parry5": Vector2(760, 900),
	"finisher5": Vector2(760, 330), "dash": Vector2(500, 420), "hit": Vector2(960, 800), "press": Vector2(960, 800),
	"top": Vector2(960, 148),
	"far_left": Vector2(130, 918), "far_right": Vector2(1790, 148), "react": Vector2(760, 330),
	"step_off": Vector2(960, 518),
}
# step_off: the playtests' experienced player's reaction to a new tell (playtest_1004/BRIEF.md), and the walk.
const NEW_REACTION := 0.25
# trail: where the player is put at each latch, feet points far apart round the ring.
const TRAIL_SPOTS := [Vector2(450, 380), Vector2(1450, 820), Vector2(450, 820), Vector2(1450, 380), Vector2(960, 560)]
const STEP_OFF_TIME := 0.20
# The playtests' experienced player's reaction to a learned tell (playtest_1004/BRIEF.md): `react` walks this late.
const LEARNED_REACTION := 0.20
# Where he stands for the string when it isn't HOME: by the rope across the ring from the player, on WALK_RECT's side.
const FAR_FROM := {"far_left": Vector2(1720, 600), "far_right": Vector2(200, 600)}
# The far tiers' first hop sets off at least this far from the feet: more than twice what track_speed covers by its latch.
const FAR_LEAP := 1400.0
# The animations of the tuck and the landings, which must stay whole on screen side to side.
const STRING_ANIMS := [&"air", &"slam_drop", &"slam_impact", &"slam_rebound"]
# The yellow ring stands this far over its anchor (DefenseHypeArtLayout.FINAL_DODGE_TELL: 24 texels at 3x).
const DODGE_BADGE_HEIGHT := 72.0
# How far ahead of a landing the bots move: a guard press inside the parry window, and a dash whose immunity covers
# the landing while the feet are still in his footprint.
const PARRY_LEAD := 4.0 / 60.0
const DASH_LEAD := 3.0 / 60.0
# Clear of a hop's splash zone (ry 97 since the 2026-10-04 tuning): 150 px at the player's 600 px/s. A step 50 px down
# is off the footprint (ry 33) and still in the zone.
const WALK_TIME := 0.25
const STEP_TIME := 50.0 / 600.0
# Out of the big one's footprint sideways (rx 198): 240 px.
const WALK_OUT_TIME := 0.40
const RING_DASH_AHEAD := 12.0
const GAUGE_READ := 100.0 / 8.0
# A spit's four and the string's four.
const MOST_PUDDLES := 8
const ANSWERS := ["walk", "step", "trap", "parry5", "finisher5", "dash", "hit", "press", "top", "far_left", "far_right", "react", "counts", "step_off", "trail"]
# `counts`: this many strings, each with its hop count drawn as the fight draws it.
const COUNT_STRINGS := 8
# How far from each latched spot `counts` puts the player, out of its splash zone.
const COUNT_CLEAR := 320.0


static func run(t) -> void:
	var answer: String = "walk" if t.tier == "normal" else t.tier
	if not answer in ANSWERS:
		t.check(false, "tier is one of %s (%s)" % [ANSWERS, answer])
		return
	var drawn: Array = await enter(t)
	if answer == "counts":
		await counts(t, drawn)
		return
	if answer == "trail":
		await trail(t)
		return
	var slams: Node = t.sm.states["Slams"]
	var gauge: Node = t.boss.break_gauge
	gauge.locked = false
	gauge.value = 0.0
	await reset(t, STARTS[answer])
	if FAR_FROM.has(answer):
		t.boss.global_position = FAR_FROM[answer]
		await t.wait(2)
	var health: int = t.player.playerHealth
	var boss_health: int = t.boss.boss_health
	var hit_info: GDScript = load(HIT_INFO)
	t.log_p("-- the string, answered: %s" % answer)
	var run: Dictionary = await run_string(t, answer)
	var results: Array = slams.results
	var names: Array = results.map(func(r): return hit_info.Result.keys()[r.result])
	var landed: Array = slams.impact_times
	t.log_p("landings %s at %s, ids %s; latches %s; badges %s; health %d -> %d; gauge %.1f; clean %s" % [names,
		landed.map(func(x): return snappedf(x, 0.001)), slams.slam_ids, slams.latch_times.map(func(x): return snappedf(x, 0.001)),
		run.badges, health, t.player.playerHealth, gauge.value, slams.clean])
	t.log_p("splashes %d, rooted %d; stuck at %s; badges withheld %s; STUCK! %d; squelches %d; rings %d (born %d), ring contacts %s; bounced %s; most puddles %d; then %s" % [
		slams.splashes, slams.splash_roots, slams.seal_times.map(func(x): return snappedf(x, 0.001)), slams.badges_withheld,
		slams.stuck_words, slams.squelches, slams.rings, run.rings_born, run.ring_contacts, slams.bounced, run.most_puddles, run.after])

	var on_beat: bool = landed.size() == 5
	for k in landed.size():
		on_beat = on_beat and absf(landed[k] - LANDINGS[k]) <= FRAME + 0.0001
	t.check(on_beat, "five landings, at 1.45, 2.35, 3.25, 4.15 and 5.45 s, to the frame (%s)" % [landed.map(func(x): return snappedf(x, 0.001))])
	t.check(run.art_x.x >= 0.0 and run.art_x.y <= ScreenView.VIEW_SIZE.x,
		"the tuck and the landings whole on screen side to side (their art from x %.0f to %.0f)" % [run.art_x.x, run.art_x.y])
	t.check(slams.slam_ids == [&"danny_hop_slam", &"danny_hop_slam", &"danny_hop_slam", &"danny_hop_slam", &"danny_butt_slam"],
		"four hops and the big one (%s)" % [slams.slam_ids])
	var badges_right := true
	for k in range(1, 6):
		if slams.badges_withheld.has(k):
			badges_right = badges_right and run.badges.get(k, "none") == "none"
		else:
			badges_right = badges_right and run.badges.get(k, "none") == ("strong red" if k == 5 else "yellow")
	t.check(badges_right, "a yellow ring over latches 1-4 and the strong red badge over the fifth, none while stuck (%s)" % [run.badges])
	var gaps: Array = run.badge_gaps.filter(func(gap): return not slams.badges_withheld.has(gap[0]))
	t.check(gaps.is_empty() and run.stray_badges.is_empty(), "each badge up from its latch to its landing and never outside one (%s, %s)" % [gaps, run.stray_badges])
	var parried: bool = results.size() == 5 and results[4].result == hit_info.Result.PARRIED
	t.check(slams.rings == (0 if parried else 1) and run.rings_born == slams.rings and run.ring_after_fifth,
		"exactly one ring, and only after an unparried fifth (%d, %d born)" % [slams.rings, run.rings_born])
	t.check(run.most_puddles <= MOST_PUDDLES, "never more than %d puddles live (%d)" % [MOST_PUDDLES, run.most_puddles])

	var never_stuck: bool = slams.seal_times.is_empty() and slams.splash_roots == 0 and slams.badges_withheld.is_empty()
	match answer:
		"walk", "react":
			t.check(names == ["IGNORED", "IGNORED", "IGNORED", "IGNORED", "IGNORED"] and t.player.playerHealth == health,
				"no landing reaches them and nothing hurts them (%s)" % [names])
			t.check(never_stuck and slams.splashes == 4 and slams.clean, "four splashes, none rooting them: never stuck, a clean string")
			t.check(run.ring_dash.get("touched_in_dash", false) and run.ring_dash.get("unhurt", false),
				"the big one's ring, dashed through: touched inside the dash's immunity, unhurt (%s)" % [run.ring_dash])
		"step":
			var rooted_at: float = slams.seal_times[0] - landed[1] if not slams.seal_times.is_empty() and landed.size() > 1 else -1.0
			t.check(slams.splash_roots >= 1 and rooted_at >= 0.0 and rooted_at <= FRAME + 0.0001 and slams.stuck_words >= 1,
				"rooted by landing 2's splash on its own step, with STUCK! (%.3f)" % rooted_at)
			t.check(names.size() >= 3 and names[1] == "IGNORED" and names[2] == "HIT", "hop 2 off them, hop 3 on them: %s" % [names])
			t.check(run.freed_after.has(3), "free again the step after hop 3 lands (%s)" % [run.freed_after])
		"trap":
			t.check(names.size() == 5 and names[3] == "IGNORED" and names[4] == "HIT" and slams.splash_roots == 1,
				"splashed at the fourth, and the big one lands on them (%s, %d rooted)" % [names, slams.splash_roots])
			t.check(slams.badges_withheld.has(5), "the big one's badge withheld (%s)" % [slams.badges_withheld])
			t.check(health - t.player.playerHealth == 2 and run.ring_contacts.is_empty(), "a whole heart, and its ring spares them (%d, %s)" % [health - t.player.playerHealth, run.ring_contacts])
			t.check(run.after.begins_with("Sleep"), "then his nap (%s)" % run.after)
		"parry5", "finisher5":
			t.check(names == ["IGNORED", "IGNORED", "IGNORED", "IGNORED", "PARRIED"] and t.player.playerHealth == health and never_stuck,
				"the hops walked and the big one parried, unhurt (%s)" % [names])
			t.check(slams.bounced and slams.rings == 0, "no ring: he bounces onto his back")
			var back: Dictionary = run.back
			t.check(back.get("entered", false) and is_equal_approx(back.get("open_for", 0.0), 3.0) and back.get("cap", 0) == 6 and back.get("dazeable", false),
				"his back: a 3.0 s window, a cap of 6, the finisher on offer (%s)" % [back])
			t.check(back.get("beside", false), "beside the player, his lying box clear of them (%s)" % [back.get("gap", -1.0)])
			t.check(back.get("top", -INF) >= t.sm.lying_top_min - 0.5 and back.get("level", false),
				"his lying box under the top rope and the boss bar (top at y %.0f, %.0f at the highest) and level with them" % [
				back.get("top", -INF), t.sm.lying_top_min])
			if answer == "parry5":
				t.check(back.get("lowered", 0.0) > 0.0, "by the top rope he lies lower than the big one landed (%.0f px)" % back.get("lowered", 0.0))
				t.check(absf(back.get("window", 0.0) - 3.0) <= FRAME + 0.0001, "the window held 3.0 s (%.3f)" % back.get("window", 0.0))
				t.check(back.get("hp_open", -1) == back.get("hp_close", -2) and back.get("hp_open", -1) == boss_health,
					"no regen across an unhit window: %d -> %d" % [back.get("hp_open", -1), back.get("hp_close", -2)])
				t.check(back.get("rolled", false) and run.after == "OnBack>Idle>Spit", "then back_roll, Idle and the Spit, no nap (%s)" % run.after)
			else:
				t.check(back.get("dazed", false), "the combo's charged third dazes him on his back")
				t.check(back.get("finisher_dealt", 0) == int(roundf(t.boss.get_max_health() * 0.25)),
					"the single-bar finisher: %d (%d)" % [roundi(t.boss.get_max_health() * 0.25), back.get("finisher_dealt", 0)])
				t.check(back.get("window", 9.0) < 3.0 - 0.1 and run.after.begins_with("OnBack>Idle"), "and its uppercut ends his window early (%.3f s, %s)" % [back.get("window", 9.0), run.after])
		"dash":
			var dodged := [0, 2, 4].all(func(k): return names.size() > k and names[k] == "DODGED" and results[k].feet_inside)
			t.check(dodged and names[1] == "IGNORED" and names[3] == "IGNORED", "hops 1 and 3 and the big one DODGED in his footprint, 2 and 4 walked (%s)" % [names])
			t.check(gauge.value >= 2.0 * GAUGE_READ - 0.001, "at least two reads (%.1f)" % gauge.value)
			t.check(never_stuck and run.ring_contacts.is_empty() and t.player.playerHealth == health, "no root, and the ring spares them")
		"hit":
			t.check(names == ["HIT", "IGNORED", "HIT", "IGNORED", "HIT"], "the first, third and fifth land (%s)" % [names])
			t.check(health - t.player.playerHealth == 4, "1 + 1 + 2 half-hearts (%d)" % (health - t.player.playerHealth))
		"press":
			t.check(names.size() > 0 and names[0] == "HIT", "a fresh press as hop 1 lands: HIT, not PARRIED (%s)" % [names])
			t.check(run.whiff_paid, "and the press's whiff paid out of the bar (%.1f)" % run.stamina_after_press)
		"top":
			var inside: Array = results.slice(0, 4).map(func(r): return r.feet_inside)
			t.check(inside == [true, true, true, true] and names.slice(0, 4) == ["HIT", "IGNORED", "HIT", "IGNORED"],
				"every hop comes down on feet under the top rope: in each footprint %s, %s" % [inside, names.slice(0, 4)])
			t.check(run.hop_badge_top >= 0.0, "each hop's yellow ring whole on screen (its top at y %.0f)" % run.hop_badge_top)
			t.check(results.size() == 5 and not results[4].feet_inside and slams.target.y >= t.sm.WALK_RECT.position.y,
				"the big one still lands on WALK_RECT (y %.0f), off them" % slams.target.y)
			t.check(health - t.player.playerHealth >= 2, "the first and third hops' half-hearts at least (%d)" % (health - t.player.playerHealth))
		"far_left", "far_right":
			var inside: Array = results.slice(0, 4).map(func(r): return r.feet_inside)
			t.check(run.first_leap >= FAR_LEAP and inside[0], "the first hop leaps %.0f px across the ring and comes down on them" % run.first_leap)
			t.check(inside == [true, true, true, true] and names.slice(0, 4) == ["HIT", "IGNORED", "HIT", "IGNORED"],
				"every hop comes down with them in its footprint: %s, %s" % [inside, names.slice(0, 4)])
		"step_off":
			var first_seal: float = slams.seal_times[0] if not slams.seal_times.is_empty() else INF
			t.check(names.size() > 0 and names[0] == "HIT", "hop 1 lands on them (%s)" % [names])
			t.check(first_seal > LANDINGS[1] - FRAME, "walked off its spot %.2f s after it landed: its puddle, armed %.2f s after the landing, never roots them (first root %.3f)" % [NEW_REACTION, slams.puddle_grace, first_seal])

	if not parried:
		t.check(run.after.begins_with("Sleep"), "an unparried fifth ends in his nap (%s)" % run.after)
		if run.inside_at_settle:
			var box: Rect2 = run.settle_box
			var feet: Vector2 = run.feet_at_nap
			t.check(slams.nudged and (feet.x <= box.position.x or feet.x >= box.end.x),
				"a player the fifth caught in his footprint is slid out beside him (%s, box %s)" % [feet, box])
		t.check(run.round_him == 0, "no puddle left on the floor round him (%d)" % run.round_him)
		t.check(run.way and (not run.b_floor.feet_open or run.b_floor.side), "a way from the player to a side of him (%s, %s)" % [run.way, run.b_floor])
	park(t)


# `counts` (the 2026-10-06 tuning): COUNT_STRINGS strings from Idle, each with its hop count drawn as the fight draws it,
# the player put COUNT_CLEAR px off each latched spot and the floor's puddles cleared, so nothing hits or roots them.
# Every count one of `drawn`, more than one of them seen, and in each string every landing on its scheduled beat to a
# frame, the hops yellow and the last landing alone the big red one.
static func counts(t, drawn: Array) -> void:
	var slams: Node = t.sm.states["Slams"]
	t.check(drawn.size() >= 2, "his strings draw their hop counts from more than one (%s)" % [drawn])
	if drawn.is_empty():
		return
	slams.hop_counts.assign(drawn)
	var hit_info: GDScript = load(HIT_INFO)
	var seen_counts: Array = []
	for n in COUNT_STRINGS:
		await reset(t, Vector2(960, 560))
		var badges := {}
		var watch := func():
			if t.sm.current_state != slams or slams.beat != slams.Beat.LATCH or badges.has(slams.slam):
				return
			var tells: Array = t.live_tells()
			badges[slams.slam] = "none" if tells.is_empty() else ("yellow" if tells[0].dodge else ("strong red" if tells[0].strong else "red"))
		t.physics_frame.connect(watch)
		t.sm.on_child_transition(t.sm.current_state, "Slams")
		var count: int = slams.slams
		seen_counts.append(count - 1)
		for k in count:
			await until_latch(t, slams, k)
			t.sm.clear_puddles()
			var spot: Vector2 = slams.target
			var away := Vector2(0.0, COUNT_CLEAR if spot.y < 600.0 else -COUNT_CLEAR)
			t.player.global_position = spot + away - Vector2(0.0, t.sm.PLAYER_FEET_OFFSET)
		await t.wait_until(func(): return t.sm.current_state != slams or slams.beat == slams.Beat.SETTLE, 200)
		t.physics_frame.disconnect(watch)
		var on_beat: bool = slams.impact_times.size() == count
		var want_badges := {}
		for k in range(1, count + 1):
			on_beat = on_beat and absf(slams.impact_times[k - 1] - slams.landing_time(k)) <= FRAME + 0.0001
			want_badges[k] = "strong red" if k == count else "yellow"
		var ids: Array = []
		for k in count - 1:
			ids.append(&"danny_hop_slam")
		ids.append(&"danny_butt_slam")
		var names: Array = slams.results.map(func(r): return hit_info.Result.keys()[r.result])
		t.log_p("string %d: %d hops, landings %s, badges %s, %s" % [n + 1, count - 1, slams.impact_times.map(func(x): return snappedf(x, 0.001)), badges, names])
		t.check(on_beat and slams.slam_ids == ids and badges == want_badges and not names.has("HIT"),
			"string %d, %d hops: every landing on its beat, the hops yellow and the last alone the big red one, nothing landing on them" % [n + 1, count - 1])
		park(t)
	var all_drawn: bool = seen_counts.all(func(c): return drawn.has(c))
	var kinds := {}
	for c in seen_counts:
		kinds[c] = true
	t.check(all_drawn and kinds.size() >= 2, "every string's hops one of %s, and more than one count over %d strings (%s)" % [drawn, COUNT_STRINGS, seen_counts])


# `trail`: a Spit's four puddles down, then the longest string there is, the player standing still with every root
# held off (root_grace_left), watched every step.
static func trail(t) -> void:
	var slams: Node = t.sm.states["Slams"]
	var hops := 9
	slams.hop_counts.assign([hops])
	await reset(t, Vector2(960, 560))
	t.sm.on_child_transition(t.sm.current_state, "Spit")
	var spat: bool = await t.wait_until(func(): return t.sm.live_puddles().size() == 4 and t.sm.live_puddles().all(func(p): return p.armed), 200)
	var most := {"trail": 0, "all": 0}
	var watch := func():
		t.sm.root_grace_left = 1.0
		var live_trail: int = slams.puddles_left.filter(func(p): return is_instance_valid(p) and not p.gone).size()
		most.trail = maxi(most.trail, live_trail)
		most.all = maxi(most.all, t.sm.live_puddles().size())
	t.physics_frame.connect(watch)
	t.sm.on_child_transition(t.sm.current_state, "Slams")
	# Moved round the ring at each latch, so the landings spread out instead of each one splatting the last one's puddle.
	for k in hops + 1:
		await until_latch(t, slams, k)
		t.player.global_position = TRAIL_SPOTS[k % TRAIL_SPOTS.size()] - Vector2(0.0, t.sm.PLAYER_FEET_OFFSET)
	await t.wait_until(func(): return t.sm.current_state != slams or slams.beat == slams.Beat.SETTLE, 900)
	t.physics_frame.disconnect(watch)
	t.log_p("a Spit's four, then %d hops: %d puddles laid, at most %d of the trail and %d in all live" % [hops, slams.puddles_left.size(), most.trail, most.all])
	t.check(spat and slams.slams == hops + 1 and slams.puddles_left.size() == hops, "every one of the %d hops laid its puddle (%d)" % [hops, slams.puddles_left.size()])
	t.check(most.trail <= slams.trail_max and most.all <= MOST_PUDDLES,
		"never more than %d of the trail (%d) and %d puddles in all (%d) live at once" % [slams.trail_max, most.trail, MOST_PUDDLES, most.all])
	park(t)


# His fight, loaded past his entrance and the card, parked in Idle with his cycle held off. Every tier but `counts` is
# written for the five-beat string, so the hop count each string draws (hop_counts) is pinned to four hops: what it
# drew from, for `counts`.
static func enter(t) -> Array:
	await t.load_fight("danny")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = SEED
	park(t)
	var slams: Node = t.sm.states["Slams"]
	var drawn: Array = slams.hop_counts.duplicate()
	slams.hop_counts.clear()
	slams.slams = LANDINGS.size()
	return drawn


static func park(t) -> void:
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()


# At HOME and parked, nothing of his on the mat, the player fresh at `start` with every key up, and the Spit next.
static func reset(t, start: Vector2) -> void:
	park(t)
	t.boss.global_position = t.sm.HOME
	t.sm.clear_puddles()
	t.sm.attacks_started = 0
	for hazard in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		hazard.queue_free()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT]:
		t.release(code)
	t.clear_iframes()
	t.player.playerHealth = 100
	t.defense._set_stamina(t.defense.max_stamina)
	await t.settle_player(start)
	await t.wait(40)


# Held for `seconds` of the fight's own time: a parry's hit-stop and slow-down hold the walk with everything else,
# as they do a player's.
static func walk(t, codes: Array, seconds: float) -> void:
	for code in codes:
		t.press(code)
	await game_wait(t, seconds)
	for code in codes:
		t.release(code)


static func game_wait(t, seconds: float) -> void:
	var until: float = t.defense.clock + seconds
	await t.wait_until(func(): return t.defense.clock >= until - 0.0001, 600)


static func until_latch(t, slams: Node, k: int) -> void:
	await t.wait_until(func(): return t.sm.current_state != slams or slams.latch_times.size() > k, 400)


static func until_landed(t, slams: Node, k: int) -> void:
	await t.wait_until(func(): return t.sm.current_state != slams or slams.results.size() > k, 400)


static func until_before_landing(t, slams: Node, k: int, lead: float) -> void:
	var landing: float = slams.landing_time(k + 1)
	await t.wait_until(func(): return t.sm.current_state != slams or slams.clock >= landing - lead, 400)


static func press_parry(t, slams: Node, k: int) -> void:
	await until_before_landing(t, slams, k, PARRY_LEAD)
	t.press(KEY_SHIFT)
	await until_landed(t, slams, k)
	t.release(KEY_SHIFT)


static func dash_through(t, slams: Node, k: int) -> void:
	await until_before_landing(t, slams, k, DASH_LEAD)
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await until_landed(t, slams, k)
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(KEY_RIGHT)


# The string from Idle, each landing answered by `answer`, watched every physics step: the badge up and which
# beat he is in, each latch's badge, each ring born and its first touch on the player, the puddles live, and,
# after the string, where he went and his time on his back.
static func run_string(t, answer: String) -> Dictionary:
	var slams: Node = t.sm.states["Slams"]
	var on_back: Node = t.sm.states["OnBack"]
	var ring_script: GDScript = load(RING_SCRIPT)
	var watched := {"badge_gaps": [], "stray_badges": [], "badges": {}, "ring_contacts": {}, "rings_born": 0,
		"ring_after_fifth": true, "most_puddles": 0, "freed_after": [], "inside_at_settle": false, "settle_box": Rect2(),
		"feet_at_nap": Vector2.ZERO, "ring_dash": {}, "after": "", "back": {}, "round_him": 0, "way": false,
		"b_floor": {}, "whiff_paid": false, "stamina_after_press": -1.0, "hop_badge_top": INF,
		"art_x": Vector2(INF, -INF), "first_leap": -1.0}
	var stood: Vector2 = t.boss.global_position
	var images := {}
	var seen_rings := {}
	var states_after: Array = []
	var back: Dictionary = watched.back
	var watch := func():
		for ring in t.boss.ring_layer.get_children():
			if ring.get_script() != ring_script or ring.is_queued_for_deletion():
				continue
			var id: int = ring.get_instance_id()
			if not seen_rings.has(id):
				seen_rings[id] = true
				watched.rings_born += 1
				watched.ring_after_fifth = watched.ring_after_fifth and slams.impact_times.size() == 5
			if not watched.ring_contacts.has(id) and t.defense.sources.has(id):
				watched.ring_contacts[id] = ring.elapsed
		watched.most_puddles = maxi(watched.most_puddles, t.sm.live_puddles().size())
		var name: String = t.sm.current_state.name
		if states_after.is_empty() or states_after[-1] != name:
			if name != "Slams" or not states_after.is_empty():
				states_after.append(name)
		if t.sm.current_state == on_back:
			back.entered = true
			back.open_for = on_back.open_for
			back.cap = on_back.hit_cap
			back.dazeable = on_back.dazeable
			if on_back.is_window() and not back.has("hp_open"):
				back.hp_open = t.boss.boss_health
				back.opened = on_back.window_at
				var lying: Rect2 = t.boss.hurtbox_rect()
				var hurt: Rect2 = t.player.hurtBox.get_node("CollisionShape2D").global_transform * t.player.hurtBox.get_node("CollisionShape2D").shape.get_rect()
				back.gap = maxf(lying.position.x - hurt.end.x, hurt.position.x - lying.end.x)
				back.beside = back.gap >= 50.0 and back.gap <= 70.0
				back.top = lying.position.y
				back.level = lying.position.y < hurt.end.y and lying.end.y > hurt.position.y
				back.lowered = t.boss.global_position.y - slams.target.y
			if on_back.is_window():
				back.hp_close = t.boss.boss_health
			if not on_back.is_window() and back.has("hp_open") and not back.has("window"):
				back.window = t.boss.fight_clock - back.opened
			back.rolled = back.get("rolled", false) or t.boss.current_anim == &"back_roll"
		elif back.has("hp_open") and not back.has("window"):
			back.window = t.boss.fight_clock - back.opened
		if t.sm.current_state != slams:
			return
		if t.boss.current_anim in STRING_ANIMS:
			var drawn := drawn_x(t, images)
			watched.art_x = Vector2(minf(watched.art_x.x, drawn.x), maxf(watched.art_x.y, drawn.y))
		if watched.first_leap < 0.0 and slams.impact_times.size() >= 1:
			watched.first_leap = stood.distance_to(slams.target)
		var badge: bool = not t.live_tells().is_empty()
		var covered: bool = slams.beat == slams.Beat.LATCH or slams.beat == slams.Beat.DROP
		if covered and not badge:
			watched.badge_gaps.append([slams.slam, snappedf(slams.clock, 0.001)])
		elif badge and not covered:
			watched.stray_badges.append([slams.slam, str(slams.Beat.keys()[slams.beat]), snappedf(slams.clock, 0.001)])
		if badge and slams.slam < slams.slams:
			watched.hop_badge_top = minf(watched.hop_badge_top, t.live_tells()[0].global_position.y - DODGE_BADGE_HEIGHT)
		if slams.beat == slams.Beat.LATCH and not watched.badges.has(slams.slam):
			var tells: Array = t.live_tells()
			watched.badges[slams.slam] = "none" if tells.is_empty() else ("yellow" if tells[0].dodge else ("strong red" if tells[0].strong else "red"))
	t.sm.on_child_transition(t.sm.current_state, "Slams")
	t.physics_frame.connect(watch)
	var finisher: Node = t.player.get_node("Finisher")
	# The prompt gates presses on real seconds, and this runs on fixed frames.
	finisher.min_press_interval = 0.0
	match answer:
		"walk", "parry5", "finisher5", "react":
			var way: int = KEY_UP if answer == "parry5" else KEY_DOWN
			for k in 4:
				await until_latch(t, slams, k)
				if answer == "react":
					await game_wait(t, LEARNED_REACTION)
				await walk(t, [way], WALK_TIME)
			if answer == "walk" or answer == "react":
				await until_latch(t, slams, 4)
				await walk(t, [KEY_RIGHT], WALK_OUT_TIME)
			else:
				await press_parry(t, slams, 4)
		"step":
			await until_latch(t, slams, 0)
			await walk(t, [KEY_DOWN], WALK_TIME)
			await until_latch(t, slams, 1)
			await walk(t, [KEY_DOWN], STEP_TIME)
			await until_landed(t, slams, 2)
			await t.wait(1)
			if not t.player.is_action_locked:
				watched.freed_after.append(3)
			await walk(t, [KEY_DOWN], WALK_TIME)
			await until_latch(t, slams, 3)
			await walk(t, [KEY_DOWN], WALK_TIME)
			await until_latch(t, slams, 4)
			await walk(t, [KEY_RIGHT], WALK_OUT_TIME)
		"trap":
			for k in 3:
				await until_latch(t, slams, k)
				await walk(t, [KEY_DOWN], WALK_TIME)
			await until_latch(t, slams, 3)
			await walk(t, [KEY_DOWN], STEP_TIME)
		"dash":
			for k in 5:
				if k % 2 == 0:
					await dash_through(t, slams, k)
				else:
					await until_latch(t, slams, k)
					await walk(t, [KEY_DOWN], WALK_TIME)
		"step_off":
			await until_landed(t, slams, 0)
			await game_wait(t, NEW_REACTION)
			await walk(t, [KEY_DOWN], STEP_OFF_TIME)
		"press":
			await press_parry(t, slams, 0)
			await t.wait(20)
			watched.stamina_after_press = t.defense.stamina
			watched.whiff_paid = t.defense.stamina <= t.defense.max_stamina - t.defense.parry_whiff_cost + 0.01
	await t.wait_until(func(): return t.sm.current_state != slams or slams.beat == slams.Beat.SETTLE, 200)
	if t.sm.current_state == slams and slams.beat == slams.Beat.SETTLE:
		watched.inside_at_settle = slams.results.size() == 5 and slams.results[4].feet_inside
		watched.settle_box = t.boss.body_box_rect(&"sleep")
	if answer == "walk" or answer == "step" or answer == "react":
		watched.ring_dash = await dash_through_last_ring(t)
	await t.wait_until(func(): return t.sm.current_state != slams, 200)
	if answer == "finisher5":
		await t.wait_until(func(): return on_back.is_window(), 60)
		t.player.global_position = t._bot_punch_spot()
		await t.wait(2)
		var before: int = t.boss.boss_health
		for n in 3:
			await t.swing()
			if n < 2:
				await t.wait(6)
		back.dazed = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
		var combo: int = before - t.boss.boss_health
		await t.mash_finisher()
		await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 300)
		back.finisher_dealt = before - t.boss.boss_health - combo
	if answer == "parry5" or answer == "finisher5":
		await t.wait_until(func(): return t.sm.current_state.name == "Spit", 400)
	else:
		await t.wait(20)
	watched.feet_at_nap = t.sm.player_feet()
	t.physics_frame.disconnect(watch)
	watched.after = ">".join(states_after)
	# The nap: the floor round him as a spit keeps it, and the way from the player to him.
	var spit: Node = t.sm.states["Spit"]
	var danny: Vector2 = t.boss.global_position
	var around: Vector2 = spit.radii + spit.clear_of_danny
	var live: Array = t.sm.live_puddles()
	watched.round_him = live.filter(func(p): return ((p.global_position - danny) / around).length_squared() < 1.0).size()
	watched.way = slams.way_to_sides(t.sm.player_feet(), danny)
	watched.b_floor = Spit.open_floor(t, spit.radii, live.map(func(p): return p.global_position), t.sm.player_feet(), danny)
	return watched


# The opaque columns of the frame his sprite is drawing, read off its sheet on disk: their left and right on the screen,
# mirrored with him.
static func drawn_x(t, images: Dictionary) -> Vector2:
	var sprite: Sprite2D = t.boss.sprite
	var path: String = sprite.texture.resource_path
	if not images.has(path):
		images[path] = Image.load_from_file(ProjectSettings.globalize_path(path))
	var image: Image = images[path]
	var size := Vector2i(image.get_width() / sprite.hframes, image.get_height() / sprite.vframes)
	var used: Rect2i = image.get_region(Rect2i(sprite.frame_coords * size, size)).get_used_rect()
	var from: float = used.position.x
	var to: float = used.end.x
	if sprite.flip_h:
		from = size.x - used.end.x
		to = size.x - used.position.x
	var left: float = sprite.get_rect().position.x
	return Vector2((sprite.global_transform * Vector2(left + from, 0.0)).x, (sprite.global_transform * Vector2(left + to, 0.0)).x)


# The walker is out beside the big one's landing: as its ring's band is about to reach them they dash in across it,
# back toward where he landed.
static func dash_through_last_ring(t) -> Dictionary:
	var ring_script: GDScript = load(RING_SCRIPT)
	var rings: Array = t.boss.ring_layer.get_children().filter(func(r): return r.get_script() == ring_script and not r.is_queued_for_deletion())
	if rings.is_empty():
		return {"error": "no ring"}
	var last: Node2D = rings[-1]
	t.clear_iframes()
	var health: int = t.player.playerHealth
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	var half: float = shape.shape.size.x * shape.global_scale.x / 2.0
	var ring_id: int = last.get_instance_id()
	var reached := func() -> bool:
		if not is_instance_valid(last):
			return true
		var gap: float = absf(t.sm.player_feet().x - last.global_position.x) - half
		return last.radius + 36.0 + RING_DASH_AHEAD >= gap
	await t.wait_until(reached, 120)
	var inward: int = KEY_LEFT if t.sm.player_feet().x > last.global_position.x else KEY_RIGHT
	var untouched: bool = not t.defense.sources.has(ring_id)
	t.press(inward)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	var dash_at: float = t.defense.dash_start_time
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(inward)
	await t.wait(20)
	var touched_at: float = t.defense.sources.get(ring_id, {}).get("contact", -INF)
	return {"untouched_before": untouched, "touched_in_dash": untouched and touched_at >= dash_at and touched_at - dash_at <= 0.18,
		"unhurt": t.player.playerHealth == health, "touch_after_dash": snappedf(touched_at - dash_at, 0.001)}
