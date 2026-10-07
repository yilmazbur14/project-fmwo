extends RefCounted

# josh_hands (the user, 2026-09-29): Josh's Hand Slam (JoshCardsHandSlam) and the portals and card hands it plays on
# (JoshHandsRig), in his fight, on whichever art is in. --fixed-fps 60, one tier a run (tier=; normal is parry). Each
# string starts from Idle, after a reset that cuts his summon through its Exit, with his order pinned to Wild Cards
# (the gauge spec's reset) so nothing but the string under test starts.
#   parry     a press 4 frames before each landing: every one PARRIED (hand_slams, six since 2026-10-04), each
#             parried hand formed on deck before its next turn, his gauge up a read each, unhurt, a streak of all of
#             them, the clean hype paid, then his Recover (attacks_per_window pinned to one by the gauge spec's reset).
#   dash      a dash across the spot 3 frames before each landing, the way alternating: no HIT (each DODGED or a near
#             miss through the dash's ghost), perfect dodges on every landing the 1.5 s cooldown lets pay (the first,
#             third and fifth at 0.81 s apart) with the dash given back on those, unhurt and clean.
#   walk      a player still at each lock walking down, then up, for 0.2 s from it: every landing finds the feet
#             outside, IGNORED; unhurt, no perfect dodge, not clean. (One already walking at the lock is led: tier lead.)
#   hit       nothing at all: HIT, IGNORED and so on, the i-frames taking every second landing; the catalogue's damage
#             a hit, and a read off his gauge each.
#   edges     after each lock the feet put a pixel inside the footprint's edge (left, right, top, bottom, in turn),
#             then a string a pixel outside it, i-frames cleared: inside hits, outside doesn't.
#   track     a player walking a square and standing 0.3 s before each lock: the mark never goes faster than the
#             hand tracks and, the player still, is on the feet at every lock with no lead (a walker's lock leaps
#             ahead of them: tier lead), the locked spot never moves, one mark at a time and never
#             the waiting hand's, the red badge from each lock to its landing and never otherwise, landings at command +
#             fly + first track + lock + drop (1.96 s) and every track + lock + drop (0.81 s) after, to the frame; the
#             WINDUP_READS entry is lock to landing. A player at (960, 400) fades his bars to 0.3, and at (960, 800)
#             they come back.
#   portals   every frame through a string, a Recover, a Wild Cards, a forced Break and the next string: the portals
#             at PORTAL_POINTS, the rest points where they were, nothing of theirs in the hazard group, and each drawn
#             where it sorts: resting and portals z 0 on y 100 / 100.5, in the air z 2, landed z 0 on its floor point.
#   break     a Break on the first track, with a hand pinned, and with a hand shattered: Broken, no hazard or badge
#             left, no Timer running, both hands gone into their portals, the portals looping; the next cycle forms
#             them again, resting before the Hand Slam's flight.
#   release   the player beaten mid-string: the hands home, hovering, no hazards; paused mid-drop for 60 frames:
#             nothing moves and the landing keeps its time; the scene reloaded mid-string; him beaten mid-string: the
#             hands shatter and the portals close, all four gone within a second.
#   rotation  the order as it ships: Hand Slam, Wild Cards, Hand Slam; a Break in Wild Cards, then the Hand Slam.
#   back_rope the player standing still at (960, 150), (300, 150), (1620, 150) and (140, 600), a string each (the
#             addendum's Part 1): every frame every hand in the air keeps its box 8 px inside the view, but for the one
#             dropping, whose lean fades so it lands on its floor point; at (960, 150) the bars fade to 0.3; landings on
#             the track tier's beat, HIT and IGNORED in turn; the badge's tip never above 84; each landed hand on
#             its locked spot and drawn on it; and wherever the hand whose turn it is covers the player (off their
#             i-frames, whose flicker the copy trails by a frame), its x-ray: the mask on the hand's own frame, clipping
#             only its children, and in it the player's sprite, frame, flip and transform at 0.8 of their alpha.
#   lead      the lock aims where the player is heading (the user, 2026-10-04), once their path over the last
#             hand_lead_window is at least hand_lead_straightness straight. A player walking from 0.3 s before each
#             lock on through its landing, across, down and on the diagonal (the way alternating), is under every
#             landing, led hand_lead_time of their walk; loops walked without a thought for it are slammed, the big
#             ones (round the rim, a 600 px square, across and back) at least LEAD_LOOPS' least, a 120 px wiggle,
#             never led, on all four, and none of them, the tight boxes too, on fewer than with the lead off (each
#             logged both ways); the same walkers who, 0.20 s (learned) or 0.25 s (first time) after each lock, stop,
#             double back, turn a quarter and stop are never hit, every landing ESCAPE_MARGIN (25 px) clear of the
#             footprint at the learned reaction and clear of it at the first-time one (since the 0.36 s read of
#             2026-10-04 a first-time stop clears it by 8 px); a dash through the lock is led no further than
#             hand_lead_max; and a walker heading into the
#             right rope is led only as far as the ropes and still slammed there.
#   art       the final sheets, where they are in: frame counts and sizes as JoshHandsLayout has them, the impact's
#             contact frame filling the footprint, the mark's rim the footprint on every frame, his own new sheets
#             80x80. "placeholders in use" and a pass for any that aren't. art_approval runs it on the art pass's
#             approval folder instead, read off disk.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")

# His park (the gauge spec's home).
const HOME := Vector2(960, 640)
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
const PARRY_LEAD := 4.0 / 60.0
const DASH_LEAD := 3.0 / 60.0
const WALK_TIME := 0.2
const STILL_TIME := 0.3
const STARTS := {"parry": Vector2(600, 760), "dash": Vector2(600, 760), "walk": Vector2(700, 300), "hit": Vector2(600, 760),
	"edges": Vector2(600, 700), "track": Vector2(600, 500)}
const HUD_HIGH := Vector2(960, 400)
const HUD_LOW := Vector2(960, 800)
const TIERS := ["parry", "dash", "walk", "hit", "edges", "track", "portals", "break", "release", "rotation", "back_rope",
	"lead", "art", "art_approval"]
# The lead tier's walkers: the way slam 1 is walked (the next the other way, and so on), and where each starts.
const LEAD_WALKS := {"across": Vector2(1, 0), "down": Vector2(0, 1), "diagonal": Vector2(1, 1)}
const LEAD_STARTS := {"across": Vector2(760, 600), "down": Vector2(960, 300), "diagonal": Vector2(760, 300)}
const LEAD_WALK_IN := 0.3
const LEAD_REACTIONS: Array[float] = [0.20, 0.25]
const LEAD_ANSWERS: Array[String] = ["stop", "back", "turn", "stop"]
# Loops walked without a thought for the slam (the playtest's, 2026-10-04), each from its first point as the string
# starts, and the fewest landings on the feet each must take with the lead. The wiggle never heads anywhere, so it is
# locked on its feet; the two tight boxes turn inside the lock's read whatever the aim, so they are only held to the
# lead never sparing them.
const LEAD_LOOPS := {
	"rim_loop": {"points": [Vector2(200, 220), Vector2(1720, 220), Vector2(1720, 880), Vector2(200, 880)], "least": 2},
	"square_600": {"points": [Vector2(660, 340), Vector2(1260, 340), Vector2(1260, 840), Vector2(660, 840)], "least": 1},
	"h_line_800": {"points": [Vector2(560, 640), Vector2(1360, 640)], "least": 1},
	"wiggle_120": {"points": [Vector2(900, 640), Vector2(1020, 640)], "least": 4},
	"square_300": {"points": [Vector2(810, 490), Vector2(1110, 490), Vector2(1110, 790), Vector2(810, 790)], "least": 0},
	"corner_box": {"points": [Vector2(140, 170), Vector2(300, 170), Vector2(300, 330), Vector2(140, 330)], "least": 0},
}
const LOOP_TOL := 10.0
const RING_START := Vector2(1450, 600)
const BACK_ROPE_SPOTS: Array[Vector2] = [Vector2(960, 150), Vector2(300, 150), Vector2(1620, 150), Vector2(140, 600)]
const APPROVAL_DIR := "res://art_source/josh_hands/approval/"
const SUMMON_SHEET := "res://Assets/Characters/Josh/josh_summon.png"
const COMMAND_SHEET := "res://Assets/Characters/Josh/josh_command.png"


static func run(t) -> void:
	var tier: String = "parry" if t.tier == "normal" else t.tier
	if not tier in TIERS:
		t.check(false, "tier is one of %s (%s)" % [TIERS, tier])
		return
	if tier.begins_with("art"):
		_art(t, tier == "art_approval")
		return
	t.fight = "josh"
	if not await t.load_gauged():
		return
	match tier:
		"parry", "dash", "walk", "hit":
			await _answered(t, tier)
		"edges":
			await _edges(t)
		"track":
			await _track(t)
		"portals":
			await _portals(t)
		"break":
			await _break(t)
		"release":
			await _release(t)
		"rotation":
			await _rotation(t)
		"back_rope":
			await _back_rope(t)
		"lead":
			await _lead(t)


#SETTING UP

# At his home, idle, his hands home, the player fresh at `start` with every key up, a full bar and no hype.
static func _reset(t, start: Vector2) -> void:
	await t.reset_gauged(HOME)
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	t.defense._set_stamina(t.defense.max_stamina)
	t.player.get_node("Hype")._set_hype(0.0)
	t.player.playerHealth = 1000
	await t.settle_player(start)
	await t.wait(40)


static func _hand_slam(t) -> Node:
	return t.sm.states["HandSlam"]


# When slam `number`'s beat `beat` is due, on the state's own clock.
static func _due_at(hs: Node, beat: int, number: int) -> float:
	for entry in hs.schedule:
		if entry[1] == beat and entry[2] == number:
			return entry[0]
	return INF


static func _feet(t) -> Vector2:
	var rect: Rect2 = t.area_rect(t.player.hurtBox)
	return Vector2(rect.get_center().x, rect.end.y)


static func _marks(t) -> Array:
	return t.hazards_of("JoshHandMark.gd")


static func _names(hs: Node) -> Array:
	return hs.results.map(func(r): return HitInfo.Result.keys()[r.result])


# A whole string on a player it reaches every time: HIT, then IGNORED inside the i-frames, and so on.
static func _hit_then_ignored(t) -> Array:
	var names: Array = []
	for k in t.sm.hand_slams:
		names.append("HIT" if k % 2 == 0 else "IGNORED")
	return names


# The landings a perfect dodge pays on, dodging every one: the first, and each one perfect_dodge_cooldown after the
# last that paid.
static func _paying_dodges(t, impacts: Array) -> Array:
	var paid: Array = []
	var last := -INF
	for k in impacts.size():
		if impacts[k] - last >= t.defense.perfect_dodge_cooldown - SLACK:
			paid.append(k + 1)
			last = impacts[k]
	return paid


static func _hold(t, held: Dictionary, code: int, down: bool) -> void:
	if held.get(code, false) == down:
		return
	held[code] = down
	if down:
		t.press(code)
	else:
		t.release(code)


# Held for `seconds` of the fight's own time.
static func _walk(t, code: int, seconds: float) -> void:
	t.press(code)
	var until: float = t.defense.clock + seconds
	await t.wait_until(func(): return t.defense.clock >= until - SLACK, 600)
	t.release(code)


#ONE STRING, WATCHED

# Every step of a string, from its start in Idle to his Recover: what the red badge and the mark did against the
# beats, each beat's first step, the hands' draw order, and the bars' fade. `answer` is called with the slam's number
# as its turn comes, and does whatever the answer is.
static func _string(t, answer: Callable) -> Dictionary:
	var hs := _hand_slam(t)
	var rig: Node = t.sm.hands
	var seen := {"badge_gaps": [], "stray_badges": [], "most_marks": 0, "deck_marks": [], "mark_speed": 0.0,
		"spot_moves": [], "lock_feet": [], "formed_on_turn": [], "alphas": [], "last_beat": -1, "last_slam": 0,
		"mark": null, "mark_at": Vector2.INF, "spot": Vector2.INF, "states": [], "hype_before_done": -1.0,
		"hype_after_done": -1.0, "done_clock": -1.0, "sorts": []}
	var watch := func():
		var state := str(t.sm.current_state.name)
		if seen.states.is_empty() or seen.states[-1] != state:
			seen.states.append(state)
			if state == "Recover" and seen.hype_after_done < 0.0:
				seen.hype_after_done = t.player.get_node("Hype").hype
		if t.sm.current_state != hs:
			return
		seen.hype_before_done = t.player.get_node("Hype").hype
		seen.done_clock = hs.clock
		var covered: bool = hs.beat == hs.Beat.LOCK or hs.beat == hs.Beat.DROP
		var badge: bool = not t.live_tells().is_empty()
		if covered and not badge:
			seen.badge_gaps.append([hs.slam, snappedf(hs.clock, 0.001)])
		elif badge and not covered:
			seen.stray_badges.append([hs.slam, hs.Beat.keys()[hs.beat], snappedf(hs.clock, 0.001)])
		var marks := _marks(t)
		seen.most_marks = maxi(seen.most_marks, marks.size())
		var mark = hs.mark
		if is_instance_valid(mark) and not mark.landed:
			if hs.mark_side != hs.active_side:
				seen.deck_marks.append([hs.slam, hs.mark_side, hs.active_side])
			if mark == seen.mark and seen.mark_at != Vector2.INF:
				seen.mark_speed = maxf(seen.mark_speed, mark.global_position.distance_to(seen.mark_at) / FRAME)
			seen.mark = mark
			seen.mark_at = mark.global_position
		else:
			seen.mark = null
			seen.mark_at = Vector2.INF
		if covered:
			if seen.spot != Vector2.INF and hs.slam == seen.last_slam and hs.target != seen.spot:
				seen.spot_moves.append([hs.slam, seen.spot, hs.target])
			seen.spot = hs.target
		else:
			seen.spot = Vector2.INF
		if hs.beat != seen.last_beat or hs.slam != seen.last_slam:
			if hs.beat == hs.Beat.LOCK:
				seen.lock_feet.append({"slam": hs.slam, "spot": hs.target, "mark": mark.global_position if is_instance_valid(mark) else Vector2.INF, "feet": _feet(t).clamp(t.sm.ROPES.position, t.sm.ROPES.end)})
			if hs.beat == hs.Beat.TRACK and hs.slam >= 2:
				var hand: Node2D = rig.hand_of(hs.active_side)
				seen.formed_on_turn.append({"slam": hs.slam, "formed": hand != null and hand.visible and hand.mode == JoshHand.Mode.AIR and hand.clip == &"hover"})
			seen.last_beat = hs.beat
			seen.last_slam = hs.slam
		seen.alphas.append(t.boss.health_bar.modulate.a)
		for side in Layout.SIDES:
			var hand: Node2D = rig.hand_of(side)
			if hand != null:
				seen.sorts.append(_sort_problem(t, hand))
	t.physics_frame.connect(watch)
	t.sm.on_child_transition(t.sm.current_state, "HandSlam")
	for k in range(1, t.sm.hand_slams + 1):
		await answer.call(k)
		if t.sm.current_state != hs:
			break
	await t.wait_until(func(): return t.sm.current_state != hs, 240)
	await t.wait(3)
	t.physics_frame.disconnect(watch)
	t.stop_boss_timers()
	seen.sorts = seen.sorts.filter(func(p): return p != "")
	return seen


# What is wrong with where `hand` is drawn and sorted, or "".
static func _sort_problem(t, hand: Node2D) -> String:
	if hand.is_in_group(t.sm.HAZARD_GROUP):
		return "%s is in the hazard group" % hand.name
	match hand.mode:
		JoshHand.Mode.REST:
			if hand.z_index != 0 or hand.global_position.y != Layout.HAND_REST_SORT_Y or hand.drawn_point().distance_to(Layout.rest_point(hand.side)) > 0.5:
				return "%s resting at %s z %d, drawn %s" % [hand.name, hand.global_position, hand.z_index, hand.drawn_point()]
		JoshHand.Mode.AIR:
			if hand.z_index != Layout.HAND_AIR_Z:
				return "%s in the air at z %d" % [hand.name, hand.z_index]
		JoshHand.Mode.GROUND:
			if hand.z_index != 0 or hand.global_position != hand.floor_at.round():
				return "%s landed at %s z %d, its floor point %s" % [hand.name, hand.global_position, hand.z_index, hand.floor_at]
	return ""


#THE ANSWERS

static func _answered(t, answer: String) -> void:
	var hs := _hand_slam(t)
	var gauge: Node = t.boss.break_gauge
	await _reset(t, STARTS[answer])
	gauge.value = 50.0 if answer == "hit" else 0.0
	var gauge_from: float = gauge.value
	var health: int = t.player.playerHealth
	var dodges: Array = []
	var on_dodge := func(hit: RefCounted) -> void:
		dodges.append({"slam": hs.results.size() + 1, "id": hit.attack_id, "stamina": t.defense.stamina})
	t.defense.perfect_dodged.connect(on_dodge)
	var held := {}
	var before_dash: Array = []
	var answer_slam := func(k: int) -> void:
		var landing := _due_at(hs, hs.Beat.IMPACT, k)
		match answer:
			"parry":
				await t.wait_until(func(): return t.sm.current_state != hs or hs.clock >= landing - PARRY_LEAD - SLACK, 600)
				t.press(KEY_SHIFT)
				await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 60)
				t.release(KEY_SHIFT)
				# Six parries fill the meter on their own; emptied after the last, the clean string's pay shows whole.
				if k == t.sm.hand_slams:
					t.player.get_node("Hype")._set_hype(0.0)
			"dash":
				await t.wait_until(func(): return t.sm.current_state != hs or hs.clock >= landing - DASH_LEAD - SLACK, 600)
				t.defense._set_stamina(t.defense.max_stamina)
				before_dash.append(t.defense.stamina)
				var way: int = KEY_RIGHT if k % 2 == 1 else KEY_LEFT
				_hold(t, held, way, true)
				t.tap(KEY_W)
				await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 60)
				await t.wait_until(func(): return not t.player.is_dodging, 30)
				_hold(t, held, way, false)
			"walk":
				await t.wait_until(func(): return t.sm.current_state != hs or hs.lock_times.size() >= k, 600)
				await _walk(t, KEY_DOWN if k % 2 == 1 else KEY_UP, WALK_TIME)
			"hit":
				await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 600)
	t.log_p("-- the string, answered: %s" % answer)
	var seen := await _string(t, answer_slam)
	t.defense.perfect_dodged.disconnect(on_dodge)
	var names := _names(hs)
	var streak: int = t.defense.parry_streak
	t.log_p("landings %s at %s; states %s; health %d -> %d; gauge %.1f -> %.1f; clean %s; streak %d; perfect dodges %s; hype at the end %.1f -> %.1f; formed on their turns %s" % [
		names, hs.impact_times.map(func(x): return snappedf(x, 0.001)), seen.states, health, t.player.playerHealth, gauge_from,
		gauge.value, hs.clean, streak, dodges, seen.hype_before_done, seen.hype_after_done, seen.formed_on_turn])
	t.check(hs.results.size() == t.sm.hand_slams, "%d landings (%d)" % [t.sm.hand_slams, hs.results.size()])
	t.check(seen.states.has("Recover") and seen.states[seen.states.find("HandSlam") + 1] == "Recover", "then his Recover (%s)" % [seen.states])
	t.check(seen.sorts.is_empty(), "every hand drawn where it sorts, never a hazard (%s)" % [seen.sorts.slice(0, 4)])
	var clean_paid: float = seen.hype_after_done - seen.hype_before_done
	match answer:
		"parry":
			t.check(names.size() == t.sm.hand_slams and names.all(func(n): return n == "PARRIED"), "every one PARRIED (%s)" % [names])
			t.check(seen.formed_on_turn.size() == t.sm.hand_slams - 1 and seen.formed_on_turn.all(func(f): return f.formed), "each parried hand formed on deck before its next turn (%s)" % [seen.formed_on_turn])
			t.check(is_equal_approx(gauge.value, t.sm.hand_slams * t.boss.BREAK_READ), "his gauge up a read a landing, %.2f (%.2f)" % [t.sm.hand_slams * t.boss.BREAK_READ, gauge.value])
			t.check(t.player.playerHealth == health and streak == t.sm.hand_slams, "unhurt, a streak of %d (%d)" % [t.sm.hand_slams, streak])
			t.check(hs.clean and is_equal_approx(clean_paid, t.sm.hand_clean_hype), "the clean hype paid, %.0f (%.2f)" % [t.sm.hand_clean_hype, clean_paid])
			t.check(absf(seen.done_clock - _due_at(hs, hs.Beat.DONE, t.sm.hand_slams)) <= FRAME + SLACK, "his Recover at the string's end (%.3f)" % seen.done_clock)
		"dash":
			var answered: bool = hs.results.all(func(r): return r.result == HitInfo.Result.DODGED or (r.ghost_inside and not r.feet_inside and r.result == HitInfo.Result.IGNORED))
			t.check(not names.has("HIT") and answered, "no HIT: each DODGED, or a near miss through the dash's ghost (%s, %s)" % [names, hs.results.map(func(r): return [r.feet_inside, r.ghost_inside])])
			var slams_dodged: Array = dodges.map(func(d): return d.slam)
			var paying := _paying_dodges(t, hs.impact_times)
			t.check(slams_dodged == paying and dodges.all(func(d): return d.id == &"josh_hand_slam"), "perfect dodges on every landing the %.1f s cooldown lets pay, %s (%s)" % [t.defense.perfect_dodge_cooldown, paying, slams_dodged])
			t.check(dodges.size() == paying.size() and dodges.all(func(d): return absf(d.stamina - t.defense.max_stamina) < 0.5), "each giving the dash back (%s)" % [dodges.map(func(d): return snappedf(d.stamina, 0.01))])
			t.check(t.player.playerHealth == health and hs.clean, "unhurt, and clean")
		"walk":
			t.check(hs.results.all(func(r): return not r.feet_inside) and names.all(func(n): return n == "IGNORED"), "every landing finds the feet outside: IGNORED (%s)" % [names])
			t.check(t.player.playerHealth == health and dodges.is_empty() and not hs.clean, "unhurt, no perfect dodge, and not clean")
		"hit":
			var hits: int = names.count("HIT")
			var damage: int = AttackCatalog.get_attack(&"josh_hand_slam").damage
			t.check(names == _hit_then_ignored(t), "HIT and IGNORED in turn (%s)" % [names])
			t.check(health - t.player.playerHealth == hits * damage, "exactly %d half-hearts, %d a hit (%d)" % [hits * damage, damage, health - t.player.playerHealth])
			t.check(is_equal_approx(gauge_from - gauge.value, hits * gauge.hit_loss), "and a read off his gauge a hit (%.2f -> %.2f)" % [gauge_from, gauge.value])
			t.check(not hs.clean and is_equal_approx(clean_paid, 0.0), "no clean hype")


#THE EDGES

static func _edges(t) -> void:
	var hs := _hand_slam(t)
	var ways := [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]
	for side in ["inside", "outside"]:
		await _reset(t, STARTS.edges)
		t.hold_break_gauge(t.boss)
		var put: Array = []
		var answer_slam := func(k: int) -> void:
			await t.wait_until(func(): return t.sm.current_state != hs or hs.lock_times.size() >= k, 600)
			var way: Vector2 = ways[(k - 1) % ways.size()]
			var reach: float = absf(way.dot(Layout.FOOTPRINT)) + (-1.0 if side == "inside" else 1.0)
			var spot: Vector2 = hs.target.round()
			var feet: Vector2 = spot + way * reach
			t.player.global_position += feet - _feet(t)
			t.player.velocity = Vector2.ZERO
			t.clear_iframes()
			put.append([spot, _feet(t)])
			await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 60)
		t.log_p("-- a pixel %s the footprint's edge" % side)
		await _string(t, answer_slam)
		var names := _names(hs)
		t.log_p("%s: feet put at %s against spots; landings %s" % [side, put.map(func(p): return p[1] - p[0]), names])
		if side == "inside":
			t.check(names.size() == t.sm.hand_slams and names.all(func(n): return n == "HIT"), "a pixel inside its edge, left, right, top and bottom, each hits (%s)" % [names])
		else:
			t.check(names.size() == t.sm.hand_slams and names.all(func(n): return n == "IGNORED") and hs.results.all(func(r): return not r.feet_inside), "a pixel outside it, none does (%s)" % [names])


#THE TRACK, THE BADGE AND THE BARS

static func _track(t) -> void:
	var hs := _hand_slam(t)
	await _reset(t, STARTS.track)
	t.hold_break_gauge(t.boss)
	var ways := [KEY_RIGHT, KEY_DOWN, KEY_LEFT, KEY_UP]
	var answer_slam := func(k: int) -> void:
		var turn := _due_at(hs, hs.Beat.TRACK, k)
		var lock := _due_at(hs, hs.Beat.LOCK, k)
		await t.wait_until(func(): return t.sm.current_state != hs or hs.clock >= turn - SLACK, 600)
		await _walk(t, ways[(k - 1) % ways.size()], lock - turn - STILL_TIME)
		await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 120)
	t.log_p("-- a player walking a square, still for %.1f s before each lock" % STILL_TIME)
	var seen := await _string(t, answer_slam)
	var off_feet: Array = seen.lock_feet.filter(func(l): return l.spot.distance_to(l.feet) > 1.0 or l.mark.distance_to(l.feet) > 1.0)
	var on_beat: bool = hs.lead == 0.0 and hs.impact_times.size() == t.sm.hand_slams
	for k in hs.impact_times.size():
		var want: float = t.sm.hand_command_time + t.sm.hand_fly_time + t.sm.hand_first_track + t.sm.hand_lock_time + t.sm.hand_drop_time + k * (t.sm.hand_track_time + t.sm.hand_lock_time + t.sm.hand_drop_time)
		on_beat = on_beat and hs.impact_times[k] >= want - SLACK and hs.impact_times[k] < want + FRAME + SLACK
	var reads: float = t.WINDUP_READS.get(&"josh_hand_slam", -1.0)
	t.log_p("locks %s; fastest mark %.0f px/s; spot moves %s; most marks %d; deck marks %s; badge gaps %s, stray %s; landings %s" % [seen.lock_feet, seen.mark_speed, seen.spot_moves, seen.most_marks, seen.deck_marks, seen.badge_gaps, seen.stray_badges, hs.impact_times.map(func(x): return snappedf(x, 0.001))])
	t.check(seen.mark_speed <= t.sm.hand_track_speed + 1.0 / FRAME, "the mark never outruns the hand's tracking, %.0f px/s and a px a frame (%.0f)" % [t.sm.hand_track_speed, seen.mark_speed])
	t.check(seen.lock_feet.size() == t.sm.hand_slams and off_feet.is_empty(), "at every lock, still for %.1f s, the spot and its mark are within a px of the feet (%s)" % [STILL_TIME, off_feet])
	t.check(seen.spot_moves.is_empty(), "the locked spot never moves (%s)" % [seen.spot_moves])
	t.check(seen.most_marks == 1 and seen.deck_marks.is_empty(), "one mark at a time, never the waiting hand's (%d, %s)" % [seen.most_marks, seen.deck_marks])
	t.check(seen.badge_gaps.is_empty() and seen.stray_badges.is_empty(), "the red badge up from each lock to its landing, and never otherwise (%s, %s)" % [seen.badge_gaps, seen.stray_badges])
	var first_landing: float = t.sm.hand_command_time + t.sm.hand_fly_time + t.sm.hand_first_track + t.sm.hand_lock_time + t.sm.hand_drop_time
	t.check(on_beat, "landings at %.2f s and every %.2f s after, on its own clock, to the frame (%s)" % [first_landing, t.sm.hand_track_time + t.sm.hand_lock_time + t.sm.hand_drop_time, hs.impact_times.map(func(x): return snappedf(x, 0.001))])
	t.check(is_equal_approx(reads, t.sm.hand_lock_time + t.sm.hand_drop_time), "the suite's WINDUP_READS entry is lock to landing, %.2f s (%.3f)" % [t.sm.hand_lock_time + t.sm.hand_drop_time, reads])

	t.log_p("-- the bars, with the player at the back and then at the front")
	await _reset(t, HUD_HIGH)
	var moved := {"at": -1}
	var answer_hud := func(k: int) -> void:
		await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 600)
		if k == 2:
			moved.at = t.boss.health_bar.modulate.a
			await t.settle_player(HUD_LOW)
	var hud := await _string(t, answer_hud)
	var lowest: float = hud.alphas.min() if not hud.alphas.is_empty() else 1.0
	var at_end: float = hud.alphas[-1] if not hud.alphas.is_empty() else -1.0
	t.log_p("the bar's alpha: lowest %.3f, as the player moved %.3f, at the end of the string %.3f" % [lowest, moved.at, at_end])
	t.check(is_equal_approx(lowest, t.boss.HUD_FADE_ALPHA), "with the player at %s the bars fade to %.1f (%.3f)" % [HUD_HIGH, t.boss.HUD_FADE_ALPHA, lowest])
	t.check(is_equal_approx(at_end, 1.0), "and at %s they come back (%.3f)" % [HUD_LOW, at_end])


#THE PORTALS AND THE DRAW ORDER, THROUGH A WHOLE STRETCH OF THE FIGHT

static func _portals(t) -> void:
	var rig: Node = t.sm.hands
	await _reset(t, STARTS.hit)
	t.hold_break_gauge(t.boss)
	t.sm.ATTACK_ORDER.assign(["HandSlam", "WildCards"])
	t.sm.cycles_started = 1
	var seen := {"frames": 0, "problems": [], "states": [], "broke": false}
	var watch := func():
		seen.frames += 1
		var state := str(t.sm.current_state.name)
		if seen.states.is_empty() or seen.states[-1] != state:
			seen.states.append(state)
		for side in Layout.SIDES:
			var portal: Node2D = rig.portal_of(side)
			if portal == null:
				seen.problems.append("no %s portal" % side)
				continue
			if portal.pivot_point().distance_to(Layout.PORTAL_POINTS[side]) > 0.5 or portal.z_index != 0 or portal.global_position.y != Layout.PORTAL_SORT_Y:
				seen.problems.append("%s portal at %s, z %d, sorted on %.1f" % [side, portal.pivot_point(), portal.z_index, portal.global_position.y])
			if portal.is_in_group(t.sm.HAZARD_GROUP):
				seen.problems.append("%s portal in the hazard group" % side)
			if rig.rest_point(side) != Layout.PORTAL_POINTS[side] + Layout.REST_OFFSET:
				seen.problems.append("%s rest point moved" % side)
			var hand: Node2D = rig.hand_of(side)
			if hand != null:
				var problem := _sort_problem(t, hand)
				if problem != "":
					seen.problems.append(problem)
		if seen.problems.size() > 20:
			seen.problems.resize(20)
	t.physics_frame.connect(watch)
	t.log_p("-- a string, his Recover, Wild Cards, his Recover, a forced Break and the next string")
	t.sm.on_child_transition(t.sm.current_state, "HandSlam")
	var wild_back: bool = await t.wait_until(func(): return str(t.sm.current_state.name) == "WildCards", 900)
	var recovering: bool = await t.wait_until(func(): return str(t.sm.current_state.name) == "Recover", 1200)
	await t.wait(30)
	t.boss.break_gauge.locked = false
	t.boss.break_gauge.set_physics_process(true)
	await t.force_break()
	seen.broke = await t.wait_until(func(): return str(t.sm.current_state.name) == "Broken", 30)
	var next_string: bool = await t.wait_until(func(): return str(t.sm.current_state.name) == "HandSlam", 900)
	var hs := _hand_slam(t)
	await t.wait_until(func(): return t.sm.current_state != hs or hs.impact_times.size() >= 2, 900)
	t.physics_frame.disconnect(watch)
	t.log_p("%d frames through %s; problems %s" % [seen.frames, seen.states, seen.problems])
	t.check(wild_back and recovering and seen.broke and next_string, "through a string, Wild Cards, a Break and the next string (%s)" % [seen.states])
	t.check(seen.problems.is_empty(), "every frame: the portals at PORTAL_POINTS, the rest points where they were, nothing of theirs a hazard, and each drawn where it sorts (%s)" % [seen.problems])


#HIS BREAK

static func _break(t) -> void:
	var hs := _hand_slam(t)
	var rig: Node = t.sm.hands
	var moments := {
		"on the first track": func(): return hs.beat == hs.Beat.TRACK and hs.slam == 1,
		"with a hand pinned": func(): return hs.impact_times.size() == 1 and rig.hand_of(hs.order[0]) != null and rig.hand_of(hs.order[0]).mode == JoshHand.Mode.GROUND,
		"with a hand shattered": func(): return hs.impact_times.size() == 1 and hs.results[0].result == HitInfo.Result.PARRIED and rig.hand_of(hs.order[0]).clip == &"shatter",
	}
	for moment in moments:
		await _reset(t, STARTS.parry)
		t.sm.on_child_transition(t.sm.current_state, "HandSlam")
		if moment == "with a hand shattered":
			var landing := _due_at(hs, hs.Beat.IMPACT, 1)
			await t.wait_until(func(): return hs.clock >= landing - PARRY_LEAD - SLACK, 600)
			t.press(KEY_SHIFT)
		var reached: bool = await t.wait_until(moments[moment], 600)
		t.release(KEY_SHIFT)
		await t.force_break()
		var broke: bool = await t.wait_until(func(): return str(t.sm.current_state.name) == "Broken", 30)
		await t.wait(2)
		var left: Array = t.live_hazards()
		var tells: Array = t.live_tells()
		var running: Array = t.break_timers().filter(func(timer): return not timer.is_stopped())
		var gone: bool = await t.wait_until(func(): return Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and hand.retracted and not hand.visible), 60)
		var looping: bool = Layout.SIDES.all(func(side): return rig.portal_of(side) != null and rig.portal_of(side).sequence == &"loop")
		t.log_p("%s: reached %s, now %s; hazards %s, tells %d, timers %s; hands %s" % [moment, reached, t.sm.current_state.name, left.map(func(h): return h.name), tells.size(), running.map(func(timer): return timer.name), Layout.SIDES.map(func(side): return [rig.hand_of(side).mode, rig.hand_of(side).retracted, rig.hand_of(side).visible])])
		t.check(reached and broke, "%s: Broken" % moment)
		t.check(left.is_empty() and tells.is_empty() and running.is_empty(), "%s: no hazard, badge or Timer left" % moment)
		t.check(gone and looping, "%s: both hands gone into their portals, which stay open" % moment)
		await t.wait_until(func(): return not t.player.is_action_locked, 120)

	t.log_p("-- the next cycle forms them again")
	t.sm.ATTACK_ORDER.assign(["HandSlam"])
	var before_flight := {"rest": false, "formed_first": false}
	var seen_form := {}
	var watch := func():
		if t.sm.current_state != hs:
			return
		for side in Layout.SIDES:
			var hand: Node2D = rig.hand_of(side)
			if hand != null and hand.clip == &"form" and hand.mode == JoshHand.Mode.REST:
				seen_form[side] = true
		if hs.beat == hs.Beat.COMMAND:
			before_flight.rest = Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and hand.mode == JoshHand.Mode.REST and hand.visible and not hand.retracted and hand.drawn_point().distance_to(Layout.rest_point(side)) <= 0.5 and (hand.clip == &"hover" or hand.clip == &"windup"))
	t.physics_frame.connect(watch)
	t.stop_boss_timers()
	t.sm.start_cycle()
	await t.wait_until(func(): return t.sm.current_state != hs or hs.beat == hs.Beat.FLY, 300)
	t.physics_frame.disconnect(watch)
	t.log_p("formed %s; lead %.2f s; resting as the flight began %s" % [seen_form, hs.lead, before_flight.rest])
	t.check(seen_form.size() == 2 and hs.lead > 0.0, "the next start_cycle() forms them at their portals, and the Hand Slam waits for it (%.2f s)" % hs.lead)
	t.check(before_flight.rest, "resting at their portals, formed, before its flight")


#LETTING GO

static func _release(t) -> void:
	var hs := _hand_slam(t)
	var rig: Node = t.sm.hands

	t.log_p("-- paused mid-drop for 60 frames")
	await _reset(t, STARTS.hit)
	t.hold_break_gauge(t.boss)
	t.sm.on_child_transition(t.sm.current_state, "HandSlam")
	await t.wait_until(func(): return hs.beat == hs.Beat.DROP and hs.clock >= _due_at(hs, hs.Beat.DROP, 1) + 0.08, 600)
	var pause: Node = t.pause_menu()
	await t.tap_pause()
	var still := func() -> Dictionary:
		return {"clock": hs.clock, "hands": Layout.SIDES.map(func(side): return [rig.hand_of(side).global_position, rig.hand_of(side).drawn_point(), rig.hand_of(side).frame_index, rig.hand_of(side).into]),
			"mark": [hs.mark.global_position, hs.mark.frame] if is_instance_valid(hs.mark) else [], "portals": Layout.SIDES.map(func(side): return [rig.portal_of(side).step, rig.portal_of(side).clock])}
	var at_pause: Dictionary = still.call()
	await t.wait(60)
	var after: Dictionary = still.call()
	t.check(pause.is_open() and t.paused and str(at_pause) == str(after), "paused, nothing of it moves for 60 frames")
	await t.tap_pause()
	await t.wait_until(func(): return hs.impact_times.size() >= 1, 120)
	var landing := _due_at(hs, hs.Beat.IMPACT, 1)
	t.log_p("paused at %.3f s; the landing, due at %.2f s, came at %.3f s" % [at_pause.clock, landing, hs.impact_times[0] if not hs.impact_times.is_empty() else -1.0])
	t.check(not hs.impact_times.is_empty() and hs.impact_times[0] >= landing - SLACK and hs.impact_times[0] < landing + FRAME + SLACK, "and after the resume the landing keeps its time")

	t.log_p("-- the player beaten mid-string")
	await _reset(t, STARTS.hit)
	t.sm.on_child_transition(t.sm.current_state, "HandSlam")
	await t.wait_until(func(): return hs.beat == hs.Beat.LOCK and hs.slam == 2, 600)
	t.boss.on_player_defeated()
	var home: bool = await t.wait_until(func(): return Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and hand.mode == JoshHand.Mode.REST and hand.visible and hand.clip == &"hover" and hand.drawn_point().distance_to(Layout.rest_point(side)) <= 0.5), 90)
	t.log_p("state %s; hands %s; hazards %s" % [t.sm.current_state.name, Layout.SIDES.map(func(side): return [rig.hand_of(side).mode, rig.hand_of(side).clip]), t.live_hazards().map(func(h): return h.name)])
	t.check(home and t.live_hazards().is_empty() and t.live_tells().is_empty(), "the hands fly home and hover, and nothing of the string is left")

	t.log_p("-- the scene reloaded mid-string")
	await t.load_gauged()
	hs = _hand_slam(t)
	rig = t.sm.hands
	await _reset(t, STARTS.hit)
	t.sm.on_child_transition(t.sm.current_state, "HandSlam")
	await t.wait_until(func(): return hs.beat == hs.Beat.DROP and hs.slam == 1, 600)
	var old_scene: Node = t.current_scene
	var reloaded: bool = await t.load_gauged()
	await t.wait(10)
	t.check(reloaded and not is_instance_valid(old_scene) and t.current_scene != old_scene, "reloaded under a slam coming down (its script errors are the runner's to count)")

	t.log_p("-- him beaten mid-string")
	hs = _hand_slam(t)
	rig = t.sm.hands
	await _reset(t, STARTS.hit)
	t.sm.on_child_transition(t.sm.current_state, "HandSlam")
	await t.wait_until(func(): return hs.beat == hs.Beat.TRACK and hs.slam == 2, 600)
	var nodes: Array = []
	for side in Layout.SIDES:
		nodes.append(rig.portal_of(side))
		nodes.append(rig.hand_of(side))
	t.sm.enter_defeated()
	var shattered: bool = Layout.SIDES.all(func(side): var hand = rig.hands.get(side); return not is_instance_valid(hand) or hand.clip == &"shatter")
	var closing: bool = Layout.SIDES.all(func(side): var portal = rig.portals.get(side); return is_instance_valid(portal) and portal.sequence == &"close")
	var freed: bool = await t.wait_until(func(): return nodes.all(func(n): return not is_instance_valid(n)), 60)
	t.log_p("state %s; shattered %s, closing %s, all four freed within a second %s" % [t.sm.current_state.name, shattered, closing, freed])
	t.check(shattered and closing, "the hands shatter and the portals close")
	t.check(freed and rig.collapsed, "all four are gone within a second, and nothing forms again")


#THE ORDER

static func _rotation(t) -> void:
	await _reset(t, STARTS.hit)
	t.hold_break_gauge(t.boss)
	t.sm.ATTACK_ORDER.assign(["HandSlam", "WildCards"])
	t.sm.cycles_started = 0
	var attacks: Array = []
	var watch := func():
		var state := str(t.sm.current_state.name)
		if (state == "HandSlam" or state == "WildCards" or state == "Broken") and (attacks.is_empty() or attacks[-1] != state):
			attacks.append(state)
	t.physics_frame.connect(watch)
	t.log_p("-- his order as it ships, from the first cycle")
	t.sm.start_cycle()
	await t.wait_until(func(): return attacks.size() >= 3, 2400)
	var shipped: Array = attacks.slice(0, 3)
	t.log_p("-- a Break in Wild Cards")
	await t.wait_until(func(): return str(t.sm.current_state.name) == "WildCards", 1200)
	await t.wait(30)
	t.boss.break_gauge.locked = false
	t.boss.break_gauge.value = 0.0
	t.boss.break_gauge.set_physics_process(true)
	await t.force_break()
	await t.wait_until(func(): return attacks.size() >= 6, 900)
	t.physics_frame.disconnect(watch)
	t.log_p("attacks in turn %s" % [attacks])
	t.check(shipped == ["HandSlam", "WildCards", "HandSlam"], "Hand Slam, Wild Cards, Hand Slam (%s)" % [shipped])
	t.check(attacks.slice(3, 6) == ["WildCards", "Broken", "HandSlam"], "a Break in Wild Cards, then the Hand Slam (%s)" % [attacks.slice(3)])


#THE BACK ROPE

static func _back_rope(t) -> void:
	var hs := _hand_slam(t)
	var rig: Node = t.sm.hands
	var inside: Rect2 = JoshArtLayout.VIEW_RECT.grow(-Layout.AIR_SIDE_MIN + 0.5)
	for spot in BACK_ROPE_SPOTS:
		await _reset(t, spot)
		t.hold_break_gauge(t.boss)
		var seen := {"off": [], "deck_off": [], "tips": [], "contacts": [], "xray_frames": 0, "xray_bad": [], "impacts": 0,
			"last_look": []}
		var watch := func():
			if t.sm.current_state != hs:
				return
			for side in Layout.SIDES:
				var hand: Node2D = rig.hand_of(side)
				if hand == null or hand.mode != JoshHand.Mode.AIR:
					continue
				var dropping: bool = side == hs.active_side and hs.beat == hs.Beat.DROP
				if not dropping and not inside.encloses(hand.drawn_rect()):
					seen.off.append([side, hs.Beat.keys()[hs.beat], hand.drawn_rect()])
					if side != hs.active_side:
						seen.deck_off.append([side, hand.drawn_rect()])
			for tell in t.live_tells():
				if tell.boss == t.boss:
					seen.tips.append(tell.global_position.y)
			if hs.impact_times.size() > seen.impacts:
				seen.impacts = hs.impact_times.size()
				var landed: Node2D = rig.hand_of(hs.order[seen.impacts - 1])
				seen.contacts.append({"mode": landed.mode, "floor": landed.floor_at.round(), "spot": hs.results[seen.impacts - 1].at, "drawn": landed.drawn_point()})
			# Tweens run after every _process, so a copy made there trails a tweened alpha or shake by a frame: those
			# frames (a hit's flicker and shake, and their tails) are left out.
			var look := [t.player.sprite.modulate, t.player.sprite.position]
			var steady: bool = not t.player.is_invincible and look == seen.last_look
			seen.last_look = look
			var active: Node2D = rig.hand_of(hs.active_side) if hs.active_side != &"" else null
			if active != null and steady and active.xray_mask.visible and _canvas_rect(_hand_art(active)).intersects(_canvas_rect(t.player.sprite)):
				seen.xray_frames += 1
				var problem := _xray_problem(t, active)
				if problem != "":
					seen.xray_bad.append(problem)
		t.physics_frame.connect(watch)
		var answer := func(k: int) -> void:
			await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 600)
		t.log_p("-- a player standing still at %s" % spot)
		var string := await _string(t, answer)
		t.physics_frame.disconnect(watch)
		var names := _names(hs)
		var on_beat: bool = hs.lead == 0.0 and hs.impact_times.size() == t.sm.hand_slams
		for k in hs.impact_times.size():
			var want: float = t.sm.hand_command_time + t.sm.hand_fly_time + t.sm.hand_first_track + t.sm.hand_lock_time + t.sm.hand_drop_time + k * (t.sm.hand_track_time + t.sm.hand_lock_time + t.sm.hand_drop_time)
			on_beat = on_beat and hs.impact_times[k] >= want - SLACK and hs.impact_times[k] < want + FRAME + SLACK
		var off_spot: Array = seen.contacts.filter(func(c): return c.mode != JoshHand.Mode.GROUND or c.floor != c.spot or c.drawn != c.floor)
		var highest: float = seen.tips.min() if not seen.tips.is_empty() else INF
		var lowest_alpha: float = string.alphas.min() if not string.alphas.is_empty() else 1.0
		t.log_p("%s: landings %s at %s; off screen %s; badge tip at least y %.0f; contacts %s; x-ray checked on %d frames, off %s; bars down to %.2f" % [spot, names, hs.impact_times.map(func(x): return snappedf(x, 0.001)), seen.off.slice(0, 3), highest, seen.contacts, seen.xray_frames, seen.xray_bad.slice(0, 3), lowest_alpha])
		t.check(seen.off.is_empty(), "%s: every hand in the air keeps its box %.0f px inside the view but for the one dropping (%s)" % [spot, Layout.AIR_SIDE_MIN, seen.off.slice(0, 3)])
		t.check(names == _hit_then_ignored(t) and on_beat, "%s: still slammed, on the track tier's beat: HIT and IGNORED in turn (%s)" % [spot, names])
		t.check(not seen.tips.is_empty() and highest >= Layout.BADGE_TOP_MIN - SLACK, "%s: the badge's tip never above %.0f (%.0f)" % [spot, Layout.BADGE_TOP_MIN, highest])
		t.check(seen.contacts.size() == t.sm.hand_slams and off_spot.is_empty(), "%s: each landed hand on its locked spot, drawn on it (%s)" % [spot, off_spot])
		t.check(seen.xray_frames > 0 and seen.xray_bad.is_empty(), "%s: the x-ray over the player wherever the hand covers them (%d frames, %s)" % [spot, seen.xray_frames, seen.xray_bad.slice(0, 3)])
		if spot == BACK_ROPE_SPOTS[0]:
			t.check(is_equal_approx(lowest_alpha, t.boss.HUD_FADE_ALPHA), "%s: the bars fade to %.1f (%.3f)" % [spot, t.boss.HUD_FADE_ALPHA, lowest_alpha])
		if spot == BACK_ROPE_SPOTS[3]:
			t.check(seen.deck_off.is_empty(), "%s: the waiting hand keeps its box inside the view too (%s)" % [spot, seen.deck_off])


# What draws the hand: its sheet, or the placeholder's glove.
static func _hand_art(hand: Node2D) -> CanvasItem:
	return hand.sprite if hand.drawn else hand.look.get_node("Glove")


# Where a sprite or a polygon is drawn, px.
static func _canvas_rect(item: CanvasItem) -> Rect2:
	if item is Sprite2D:
		return item.global_transform * item.get_rect()
	var points: PackedVector2Array = item.global_transform * item.polygon
	var rect := Rect2(points[0], Vector2.ZERO)
	for point in points:
		rect = rect.expand(point)
	return rect


# What is wrong with a hand's x-ray over the player this frame, or "".
static func _xray_problem(t, hand: Node2D) -> String:
	var mask: CanvasItem = hand.xray_mask
	var ghost: Sprite2D = hand.xray_ghost
	var source: Sprite2D = t.player.sprite
	if mask.clip_children != CanvasItem.CLIP_CHILDREN_ONLY:
		return "the mask clips %d" % mask.clip_children
	if hand.drawn and (mask.texture != hand.sprite.texture or mask.frame != hand.sprite.frame or mask.hframes != hand.sprite.hframes):
		return "the mask on %s frame %d, the hand on %s frame %d" % [mask.texture, mask.frame, hand.sprite.texture, hand.sprite.frame]
	if not hand.drawn and (mask.get_parent() != hand.look or mask.polygon != hand.look.get_node("Glove").polygon):
		return "the mask isn't the glove"
	if not ghost.visible or ghost.texture != source.texture or ghost.frame != source.frame or ghost.flip_h != source.flip_h:
		return "the ghost on frame %d flip %s, the player on %d flip %s" % [ghost.frame, ghost.flip_h, source.frame, source.flip_h]
	var a: Transform2D = ghost.global_transform
	var b: Transform2D = source.global_transform
	if a.origin.distance_to(b.origin) > 0.01 or a.x.distance_to(b.x) > 0.01 or a.y.distance_to(b.y) > 0.01:
		return "the ghost at %s, the player at %s" % [a, b]
	if not is_equal_approx(ghost.modulate.a, Layout.XRAY_ALPHA * source.modulate.a):
		return "the ghost's alpha %.3f against the player's %.3f" % [ghost.modulate.a, source.modulate.a]
	return ""


#THE LEAD

static func _lead(t) -> void:
	var hs := _hand_slam(t)
	var ropes: Rect2 = t.sm.ROPES
	var led: float = t.sm.hand_lead_time * Layout.WALK_SPEED

	for walk in LEAD_WALKS:
		var way: Vector2 = LEAD_WALKS[walk]
		await _reset(t, LEAD_STARTS[walk])
		t.hold_break_gauge(t.boss)
		t.log_p("-- walking %s on through every landing" % walk)
		await _string(t, _walker(t, hs, way, [], 0.0))
		var names := _names(hs)
		var off_lead: Array = []
		for k in hs.leads.size():
			var want: Vector2 = (way if k % 2 == 0 else -way) * led
			if hs.leads[k].distance_to(want) > 1.0:
				off_lead.append([k + 1, hs.leads[k], want])
		var outside: Array = hs.results.filter(func(r): return r.at != r.at.clamp(ropes.position, ropes.end))
		t.log_p("%s: landings %s, feet inside %s, leads %s, off the spot by %s" % [walk, names, hs.results.map(func(r): return r.feet_inside), hs.leads, hs.results.map(func(r): return (r.feet - r.at).round())])
		t.check(hs.results.size() == t.sm.hand_slams and hs.results.all(func(r): return r.feet_inside), "%s: walking on, every landing comes down on the feet (%s)" % [walk, hs.results.map(func(r): return r.feet_inside)])
		t.check(names == _hit_then_ignored(t), "%s: HIT and IGNORED in turn, the i-frames between (%s)" % [walk, names])
		t.check(off_lead.is_empty() and outside.is_empty(), "%s: each lock led %.0f px along the walk, inside the ropes (%s)" % [walk, led, off_lead])

	t.log_p("-- loops, with the lead off (every lock on the feet) and on")
	for loop in LEAD_LOOPS:
		var spec: Dictionary = LEAD_LOOPS[loop]
		var kept: float = t.sm.hand_lead_time
		t.sm.hand_lead_time = 0.0
		var off: int = await _loop(t, hs, spec.points)
		t.sm.hand_lead_time = kept
		var on: int = await _loop(t, hs, spec.points)
		t.log_p("%s: feet inside with the lead off %d, on %d (of %d); leads %s" % [loop, off, on, t.sm.hand_slams, hs.leads])
		t.check(on >= spec.least and on >= off, "%s: walking the loop, at least %d of the landings come down on the feet, and no fewer than with the lead off (%d, off %d)" % [loop, spec.least, on, off])
		if loop == "wiggle_120":
			t.check(hs.leads.all(func(l): return l == Vector2.ZERO), "%s: zigzagging on the spot, never led (%s)" % [loop, hs.leads])

	for reaction in LEAD_REACTIONS:
		for walk in LEAD_WALKS:
			var way: Vector2 = LEAD_WALKS[walk]
			await _reset(t, LEAD_STARTS[walk])
			t.hold_break_gauge(t.boss)
			t.log_p("-- walking %s into each lock, then %.2f s after it: %s" % [walk, reaction, LEAD_ANSWERS])
			var health: int = t.player.playerHealth
			await _string(t, _walker(t, hs, way, LEAD_ANSWERS, reaction))
			var names := _names(hs)
			var clear: Array = hs.results.map(func(r): return snappedf(_clearance(r.at, r.feet), 0.1))
			t.log_p("%s at %.2f s: landings %s, clear of the footprint by %s px, leads %s" % [walk, reaction, names, clear, hs.leads])
			t.check(hs.results.size() == t.sm.hand_slams and names.all(func(n): return n == "IGNORED") and t.player.playerHealth == health, "%s, %.2f s: stopping, doubling back or turning, never hit (%s)" % [walk, reaction, names])
			# The margin is held at the learned reaction (JoshHandsLayout.REACTION, the invariants'); a first-time one only has
			# to come out clear.
			var margin: float = Layout.ESCAPE_MARGIN if reaction <= Layout.REACTION + SLACK else 0.0
			t.check(clear.all(func(c): return c > margin), "%s, %.2f s: every landing more than %.0f px clear of the footprint (%s)" % [walk, reaction, margin, clear])

	t.log_p("-- a dash through the lock")
	await _reset(t, LEAD_STARTS.across)
	t.hold_break_gauge(t.boss)
	var dash_first := func(k: int) -> void:
		if k == 1:
			var lock := _due_at(hs, hs.Beat.LOCK, 1)
			await t.wait_until(func(): return t.sm.current_state != hs or hs.clock >= lock - 3.0 * FRAME - SLACK, 600)
			t.press(KEY_RIGHT)
			t.tap(KEY_W)
			await t.wait_until(func(): return t.sm.current_state != hs or hs.lock_times.size() >= 1, 30)
			await t.wait(2)
			t.release(KEY_RIGHT)
		await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 600)
	await _string(t, dash_first)
	var dash_heading: Vector2 = hs.headings[0] if not hs.headings.is_empty() else Vector2.ZERO
	var dash_lead: Vector2 = hs.leads[0] if not hs.leads.is_empty() else Vector2.INF
	t.log_p("the dash read at the lock %s, its lead %s" % [dash_heading, dash_lead])
	t.check(dash_heading.x > 2.0 * Layout.WALK_SPEED, "the lock read the dash, faster than twice a walk (%s)" % dash_heading)
	t.check(is_equal_approx(dash_lead.x, t.sm.hand_lead_max) and is_zero_approx(dash_lead.y), "and led it no further than hand_lead_max, %.0f px (%s)" % [t.sm.hand_lead_max, dash_lead])

	t.log_p("-- walking on into the right rope")
	await _reset(t, RING_START)
	t.hold_break_gauge(t.boss)
	var into_rope := func(k: int) -> void:
		if k == 1:
			await _walker(t, hs, Vector2.RIGHT, [], 0.0).call(1)
		await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 600)
	await _string(t, into_rope)
	var first: Dictionary = hs.results[0] if not hs.results.is_empty() else {}
	t.log_p("into the rope: led %s, the spot %s, the feet %s" % [hs.leads[0] if not hs.leads.is_empty() else Vector2.INF, first.get("at"), first.get("feet")])
	t.check(not first.is_empty() and first.at.x == roundf(ropes.end.x) and first.feet_inside, "led only as far as the ropes (x %.0f), and still slammed there (%s)" % [ropes.end.x, first])


# Slam k's answer for a player walking `way` (slam 1; each next the other way) from LEAD_WALK_IN before its lock: on
# through its landing, or, `reaction` after its lock, its answer in `answers` - stop, back (double back) or turn (a
# quarter turn).
static func _walker(t, hs: Node, way: Vector2, answers: Array, reaction: float) -> Callable:
	return func(k: int) -> void:
		var lock := _due_at(hs, hs.Beat.LOCK, k)
		var going: Vector2 = way if k % 2 == 1 else -way
		await t.wait_until(func(): return t.sm.current_state != hs or hs.clock >= lock - LEAD_WALK_IN - SLACK, 600)
		_walk_keys(t, going, true)
		if not answers.is_empty():
			await t.wait_until(func(): return t.sm.current_state != hs or hs.clock >= lock + reaction - SLACK, 120)
			_walk_keys(t, going, false)
			match answers[(k - 1) % answers.size()]:
				"back":
					_walk_keys(t, -going, true)
				"turn":
					_walk_keys(t, Vector2(-going.y, going.x), true)
		await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 120)
		for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
			t.release(code)


static func _walk_keys(t, way: Vector2, down: bool) -> void:
	var codes: Array = []
	if way.x != 0.0:
		codes.append(KEY_RIGHT if way.x > 0.0 else KEY_LEFT)
	if way.y != 0.0:
		codes.append(KEY_DOWN if way.y > 0.0 else KEY_UP)
	for code in codes:
		if down:
			t.press(code)
		else:
			t.release(code)


# A string walked round `points` from the first, steering at each step; how many landings found the feet inside.
static func _loop(t, hs: Node, points: Array) -> int:
	await _reset(t, points[0])
	t.hold_break_gauge(t.boss)
	var held := {}
	var at := {"next": 1}
	var steer := func():
		if t.sm.current_state != hs:
			return
		var d: Vector2 = points[at.next] - t.player.global_position
		_hold(t, held, KEY_RIGHT, d.x > LOOP_TOL)
		_hold(t, held, KEY_LEFT, d.x < -LOOP_TOL)
		_hold(t, held, KEY_DOWN, d.y > LOOP_TOL)
		_hold(t, held, KEY_UP, d.y < -LOOP_TOL)
		if absf(d.x) <= LOOP_TOL and absf(d.y) <= LOOP_TOL:
			at.next = (at.next + 1) % points.size()
	t.physics_frame.connect(steer)
	var answer := func(k: int) -> void:
		await t.wait_until(func(): return t.sm.current_state != hs or hs.results.size() >= k, 600)
	await _string(t, answer)
	t.physics_frame.disconnect(steer)
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		t.release(code)
	return hs.results.filter(func(r): return r.feet_inside).size()


# How far outside the footprint round `spot` the feet stand: the most both its radii can grow and still leave them
# outside it (below zero, inside).
static func _clearance(spot: Vector2, feet: Vector2) -> float:
	var low := -Layout.FOOTPRINT.y + 0.5
	var high := 2000.0
	for i in 40:
		var mid := (low + high) / 2.0
		if ((feet - spot) / (Layout.FOOTPRINT + Vector2.ONE * mid)).length_squared() >= 1.0:
			low = mid
		else:
			high = mid
	return low


#THE ART

# The final sheets, where they are in, held to JoshHandsLayout's numbers; or the art pass's approval sheets, read off
# disk, with `approval`.
static func _art(t, approval: bool) -> void:
	var sheet := func(path: String) -> String:
		return APPROVAL_DIR + path.get_file() if approval else path
	var exists := func(path: String) -> bool:
		return FileAccess.file_exists(sheet.call(path)) if approval else ResourceLoader.exists(path)
	var image := func(path: String) -> Image:
		return Image.load_from_file(ProjectSettings.globalize_path(sheet.call(path)))
	t.log_p("-- the art, %s" % ("the approval sheets" if approval else "as shipped"))

	var hand_in: bool = approval or Layout.final_hand()
	if not hand_in:
		t.log_p("the hands: placeholders in use")
	else:
		var bad: Array = []
		for clip in Layout.HAND_CLIPS:
			for path in [Layout.hand_sheet(clip), Layout.hand_glow_sheet(clip)]:
				if not exists.call(path):
					if path == Layout.hand_sheet(clip):
						bad.append([clip, "missing"])
					continue
				var img: Image = image.call(path)
				var frames: int = Layout.HAND_CLIPS[clip].times.size()
				if img.get_width() != frames * int(Layout.HAND.frame.x) or img.get_height() != int(Layout.HAND.frame.y):
					bad.append([path.get_file(), img.get_size(), frames])
		t.check(bad.is_empty(), "every hand clip %s, as many frames as JoshHandsLayout.HAND_CLIPS has (%s)" % [Layout.HAND.frame, bad])
		var contact := _contact(image.call(Layout.hand_sheet(&"impact")))
		t.log_p("the impact's contact frame fills %.3f of the footprint, reaching %.0f texels left and %.0f right of the pivot" % [contact.fill, contact.left, contact.right])
		t.check(contact.fill >= 0.8 and contact.left <= Layout.FOOTPRINT_TEXELS.x + 4.0 and contact.right <= Layout.FOOTPRINT_TEXELS.x + 4.0, "its contact frame fills the footprint and stays within 4 texels of it sideways")
	if not (approval or Layout.final_portal()):
		t.log_p("the portals: placeholders in use")
	else:
		var bad: Array = []
		for sequence in Layout.PORTAL_SEQUENCES:
			for layer in Layout.PORTAL_LAYERS:
				var path := Layout.portal_sheet(sequence, layer)
				if not exists.call(path):
					if Layout.PORTAL_REQUIRED.has(sequence):
						bad.append([path.get_file(), "missing"])
					continue
				var img: Image = image.call(path)
				var frames: int = Layout.PORTAL_SEQUENCES[sequence].size()
				if img.get_width() != frames * int(Layout.PORTAL.frame.x) or img.get_height() != int(Layout.PORTAL.frame.y):
					bad.append([path.get_file(), img.get_size(), frames])
		t.check(bad.is_empty(), "every portal sheet %s, as many frames as JoshHandsLayout.PORTAL_SEQUENCES has (%s)" % [Layout.PORTAL.frame, bad])
	if not (approval or Layout.final_mark()):
		t.log_p("the mark: placeholders in use")
	else:
		var img: Image = image.call(Layout.MARK.texture)
		var frame: Vector2 = Layout.MARK.frame
		t.check(img.get_width() == Layout.MARK.frames * int(frame.x) and img.get_height() == int(frame.y), "the mark: %d frames of %s (%s)" % [Layout.MARK.frames, frame, img.get_size()])
		var rims: Array = []
		for f in Layout.MARK.frames:
			rims.append(_rim_is_footprint(img, f))
		t.check(rims.all(func(r): return r), "its rim is the footprint on every frame, its land frame too (%s)" % [rims])
	if not (approval or Layout.final_impact()):
		t.log_p("the impact: the fan of cards in use")
	else:
		var img: Image = image.call(Layout.IMPACT_FX.texture)
		var frames: int = Layout.IMPACT_FX.frame_times.size()
		t.check(img.get_width() == frames * int(Layout.IMPACT_FX.frame.x) and img.get_height() == int(Layout.IMPACT_FX.frame.y), "the impact burst: %d frames of %s (%s)" % [frames, Layout.IMPACT_FX.frame, img.get_size()])
	for path in [SUMMON_SHEET, COMMAND_SHEET]:
		if not exists.call(path):
			t.log_p("%s: placeholder in use" % path.get_file())
			continue
		var img: Image = image.call(path)
		var most := 0
		for anim_name in JoshArtLayout.FINAL_ANIMS:
			var spec: Dictionary = JoshArtLayout.FINAL_ANIMS[anim_name]
			if spec.sheet == path:
				most = maxi(most, spec.frames.max() + 1)
		t.check(img.get_height() == 80 and img.get_width() == most * 80, "%s: %d frames of 80x80 (%s)" % [path.get_file(), most, img.get_size()])


# How much of the footprint, texel centres inside its ellipse round the pivot, the impact's contact frame covers, and
# how far its drawn texels reach left and right of the pivot.
static func _contact(img: Image) -> Dictionary:
	var frame: Vector2 = Layout.HAND.frame
	var pivot: Vector2 = Layout.HAND.pivot
	var radii: Vector2 = Layout.FOOTPRINT_TEXELS
	var x0: int = Layout.HAND_CONTACT_FRAME * int(frame.x)
	var inside := 0
	var covered := 0
	var reach := Vector2.ZERO
	for y in int(frame.y):
		for x in int(frame.x):
			var solid: bool = img.get_pixel(x0 + x, y).a > 0.0
			var d := (Vector2(x, y) + Vector2(0.5, 0.5) - pivot)
			if (d / radii).length_squared() <= 1.0:
				inside += 1
				if solid:
					covered += 1
			if solid:
				reach.x = maxf(reach.x, pivot.x - x)
				reach.y = maxf(reach.y, x + 1.0 - pivot.x)
	return {"fill": float(covered) / maxf(inside, 1.0), "left": reach.x, "right": reach.y}


# The art pass's rule: the rim is the edge ring of the texels whose centres are inside the footprint's ellipse round
# the pivot, every one of them drawn, and nothing drawn outside it.
static func _rim_is_footprint(img: Image, f: int) -> bool:
	var frame: Vector2 = Layout.MARK.frame
	var pivot: Vector2 = Layout.MARK.pivot
	var radii: Vector2 = Layout.FOOTPRINT_TEXELS
	var inside := func(x: int, y: int) -> bool:
		return ((Vector2(x, y) + Vector2(0.5, 0.5) - pivot) / radii).length_squared() <= 1.0
	for y in int(frame.y):
		for x in int(frame.x):
			var solid: bool = img.get_pixel(f * int(frame.x) + x, y).a > 0.0
			var ins: bool = inside.call(x, y)
			if solid and not ins:
				return false
			var edge: bool = ins and not (inside.call(x + 1, y) and inside.call(x - 1, y) and inside.call(x, y + 1) and inside.call(x, y - 1))
			if edge and not solid:
				return false
	return true
