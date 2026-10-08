extends RefCounted

# mason_pitch (the user's pick, 2026-10-04): Mason's Nugget Fastball (MasonPitch), on whatever art is in. --fixed-fps
# 60, one tier a run (tier=; normal is home_run). Each run turns the pitch on for itself (pitch_enabled) and runs it
# on its own from Idle (MasonStateMachine.run_attack), its set pinned with forced_slots unless a tier says otherwise,
# Mason on his wall column. Presses are scripted on the pitch's own clock.
#   home_run     a real cycle's set of fastball, changeup and hesitation, every red pressed 0.12 s before its contact
#                and the X left alone: each red PARRIED and batted back into his head, 2 off him a home run, HOME RUN!
#                up, his gauge up a parry_gain each parry, the streak counting 1, 2, 3; Broken within 0.3 s of the
#                third arriving; no delivery and no eat, and his next cycle once his Break is over.
#   reads        each phase: the badge to the contact 0.42 s for a fastball and 0.64 s for a changeup and the release
#                0.30 s after the badge (each to a frame); a changeup's kind known as its wind-up starts, 0.55 s or
#                more before its badge; the live window: a player put on the ball's path where it passes 0.09 s
#                before its contact or 0.20 s after is untouched, and 0.10 s after it is hit; a press at a
#                fastball's timing whiffs on a changeup and it lands, a press 0.52 s after the badge parries it; a
#                walker at walking speed in each of 8 directions is hit by every fastball; and walkers that turn off
#                his line (away from him) 0.20 +-0.04 s after the release are hit by 95% of fastballs or more and get
#                out of 90% of changeups.
#   fake         a press while the X is up: exactly 40 stamina, no whiff on top, both streaks ended, FEINT! and the
#                glow on his hand; the quick pitch 0.10 s after the press, landing through a fresh press timed to it;
#                and with no press on the X, a whiff in the hitch doesn't keep the red after it from being parried.
#   knockdown    home run, home run, hit: no knockdown; a bite ends the streak; phase two's miss, then three home
#                runs: Broken on the fourth's arrival; with his gauge locked, three home runs are just home runs and
#                the set plays on.
#   release      a Break 0.05 s after a bite (X, glow, FEINT! and the quick pitch out) and one with a fastball in
#                the air, a pause with a changeup in the air (40 frames move nothing, then it plays out), then the
#                player killed by a pitch: each leaves no badge, X, glow, word or ball, his sheet back as it was and
#                no press listener; one outro.
#   release_won  the same, ending on Mason killed by a phase-two home run instead.
#   fair         an ideal player from 12 spots, 6 standing and 6 walking (tapping the parry without stopping), on
#                both wall columns and both phases' sets as dealt: every red parried, no press on an X, no hit, and
#                the knockdown every set.
#   grace        a player standing in him as a cycle starts is untouched for its contact grace and hit as it runs
#                out; one walking into his squat inside the grace is hit.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")

const AT := Vector2(1660, 480)
const AT_LEFT := Vector2(260, 480)
const SPOT := Vector2(760, 640)
const WALK_FROM := Vector2(960, 540)
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
const PRESS_LEAD := 0.12
const SEED := 20261004
const F := &"fastball"
const C := &"changeup"
const H := &"hesitation"
const PITCH_IDS := [&"mason_fastball", &"mason_changeup", &"mason_quick_pitch"]
const TIERS := ["home_run", "reads", "fake", "knockdown", "release", "release_won", "fair", "grace"]
const DIRS := [Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1), Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1), Vector2(1, -1)]
const AXES := [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]
const TURN_TRIALS := 10
const TURN_AT := 0.20
const TURN_JITTER := 0.04
const FAIR_SPOTS := [Vector2(760, 640), Vector2(400, 820), Vector2(1200, 300), Vector2(560, 300), Vector2(960, 860), Vector2(1300, 760)]
const SET_FRAMES := 900


static func run(t) -> void:
	var tier: String = "home_run" if t.tier == "normal" else t.tier
	if not tier in TIERS:
		t.check(false, "tier is one of %s (%s)" % [TIERS, tier])
		return
	t.fight = "mason"
	if not await t.load_gauged():
		return
	seed(SEED)
	match tier:
		"home_run":
			await _home_run(t)
		"reads":
			await _reads(t)
		"fake":
			await _fake(t)
		"knockdown":
			await _knockdown(t)
		"release":
			await _release(t, false)
		"release_won":
			await _release(t, true)
		"fair":
			await _fair(t)
		"grace":
			await _grace(t)


#SETTING UP

static func _pitch(t) -> Node:
	return t.sm.states["Pitch"]


# Idle on `mason_at` in `phase`, his pitch on with `slots` forced, and the player fresh at `spot` with every key up, a
# full bar and no streak.
static func _ready_pitch(t, phase: int, slots: Array, spot := SPOT, mason_at := AT) -> Node:
	await t.reset_gauged(t.fight_spec.home)
	t.boss.global_position = mason_at
	t.sm.rest_point = mason_at + t.sm.BOMB_SPAWN_OFFSET
	t.boss.phase_two = phase == 1
	t.boss.boss_health = floori(t.boss.get_max_health() * t.boss.PHASE_TWO_RATIO) if phase == 1 else t.boss.get_max_health()
	t.sm.cycle_phase = phase
	t.sm.finishers = []
	t.sm.pitch_enabled = true
	t.sm.pitch_sets_started = 1
	var pitch := _pitch(t)
	pitch.forced_slots = slots.duplicate()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	t.defense._set_stamina(t.defense.max_stamina)
	t.defense.end_parry_streak()
	t.defense.rearm_parry()
	t.player.get_node("Hype")._set_hype(0.0)
	t.player.playerHealth = 1000
	await t.settle_player(spot)
	t.clear_iframes()
	await t.wait(2)
	return pitch


#THE WATCH: what the set did, on the pitch's own clock, and the scripted presses and walks

# policy: "reds" an offset per red in order, from its contact (or from its badge with "from_badge"), null for no press;
# "red_default" for the reds past the list; "x" an offset from the X going up (a bite); "hitch" one from the X coming
# down; "quick" one from the quick pitch's contact; "rearm" re-arms the parry before each press. "walk" a direction
# held from the start, "walk_from_badge" held from the first badge or X, "turn" [delay after the release, direction].
static func _new_log(policy: Dictionary) -> Dictionary:
	return {"policy": policy, "told": false, "x_up": false, "seen": {}, "badges": [], "xs": [], "balls": [], "drops": [],
		"words": [], "states": [], "state": "", "hp": -1, "hits": [], "parries": [], "presses": [], "press_at": INF,
		"release_at": INF, "badge_seen": -INF, "x_seen": -INF, "kind_seen": -INF, "kinds": [], "reds": 0,
		"quick_planned": false, "walking": Vector2.ZERO, "held": {}, "turned": false, "gauge": [], "callbacks": []}


static func _start_watch(t, pitch: Node, w: Dictionary) -> void:
	w.hp = t.boss.boss_health
	var on_hit := func(hit) -> void:
		w.hits.append({"pc": pitch.clock, "t": t.defense.clock, "id": hit.attack_id})
	var on_parry := func(hit, _point, _staggered, _streak) -> void:
		w.parries.append({"pc": pitch.clock, "t": t.defense.clock, "id": hit.attack_id})
		w.gauge.append(t.boss.break_gauge.value)
	var frame := _watch(t, pitch, w)
	t.defense.hit_taken.connect(on_hit)
	t.defense.parried.connect(on_parry)
	t.physics_frame.connect(frame)
	w.callbacks = [on_hit, on_parry, frame]


static func _stop_watch(t, w: Dictionary) -> void:
	t.defense.hit_taken.disconnect(w.callbacks[0])
	t.defense.parried.disconnect(w.callbacks[1])
	t.physics_frame.disconnect(w.callbacks[2])
	_hold(t, w, Vector2.ZERO)
	t.release(KEY_SHIFT)


static func _watch(t, pitch: Node, w: Dictionary) -> Callable:
	return func() -> void:
		var now: float = t.defense.clock
		var pc: float = pitch.clock
		var pitching: bool = t.sm.current_state == pitch
		var st := str(t.sm.current_state.name)
		if st != w.state:
			w.states.append({"t": now, "pc": pc, "state": st})
			w.state = st
		var told: bool = pitching and not t.live_tells().is_empty()
		if told and not w.told:
			w.badges.append({"t": now, "pc": pc, "kind": pitch.kind, "badge_at": pitch.badge_at, "contact_at": pitch.contact_at})
		w.told = told
		var x_up: bool = is_instance_valid(pitch.mark)
		if x_up and not w.x_up:
			w.xs.append({"t": now, "pc": pc})
		w.x_up = x_up
		if pitching and pitch.kind_at != w.kind_seen:
			w.kind_seen = pitch.kind_at
			w.kinds.append({"kind": pitch.kind, "at": pitch.kind_at})
		for ball in t.hazards_of("MasonPitchBall.gd"):
			var id: int = ball.get_instance_id()
			if not w.seen.has(id):
				w.seen[id] = true
				w.balls.append({"t": now, "pc": pc, "kind": ball.kind, "node": ball, "flight": ball.flight, "badge_at": pitch.badge_at, "contact_at": pitch.contact_at})
		var hp: int = t.boss.boss_health
		if hp < w.hp:
			w.drops.append({"t": now, "pc": pc, "amount": w.hp - hp, "streak": pitch.streak})
		w.hp = hp
		for word in t.boss.hud_layer.get_children():
			var home_run: bool = word.has_meta(&"home_run")
			if (home_run or (word is Label and word.text == "FEINT!")) and not w.seen.has(word.get_instance_id()):
				w.seen[word.get_instance_id()] = true
				w.words.append({"t": now, "pc": pc, "text": "HOME RUN!" if home_run else "FEINT!"})
		_plan_presses(t, pitch, w, pitching)
		_steer(t, pitch, w, pitching)
		if pc + FRAME >= w.press_at - SLACK:
			if w.policy.get("rearm", false):
				t.defense.rearm_parry()
			t.press(KEY_SHIFT)
			w.presses.append(pc)
			w.press_at = INF
			w.release_at = pc + 2.0 * FRAME
		elif pc >= w.release_at:
			t.release(KEY_SHIFT)
			w.release_at = INF


static func _plan_presses(t, pitch: Node, w: Dictionary, pitching: bool) -> void:
	if not pitching:
		return
	var policy: Dictionary = w.policy
	if pitch.badge_at != w.badge_seen and pitch.badge_at > -INF:
		w.badge_seen = pitch.badge_at
		var reds: Array = policy.get("reds", [])
		var offset: Variant = reds[w.reds] if w.reds < reds.size() else policy.get("red_default")
		w.reds += 1
		if offset != null:
			w.press_at = (pitch.badge_at if policy.get("from_badge", false) else pitch.contact_at) + offset
	if pitch.x_at != w.x_seen and pitch.x_at > -INF:
		w.x_seen = pitch.x_at
		if policy.get("x") != null:
			w.press_at = pitch.x_at + policy.x
		elif policy.get("hitch") != null:
			w.press_at = pitch.x_at + pitch.feint_show + policy.hitch
	if pitch.beat == pitch.Beat.BITTEN and not w.quick_planned and policy.get("quick") != null:
		w.quick_planned = true
		w.press_at = pitch.contact_at + policy.quick


static func _steer(t, pitch: Node, w: Dictionary, pitching: bool) -> void:
	var policy: Dictionary = w.policy
	if not policy.has("walk"):
		return
	var dir: Vector2 = policy.walk
	if policy.get("walk_from_badge", false) and w.badges.is_empty() and w.xs.is_empty():
		dir = Vector2.ZERO
	if policy.has("turn") and not w.balls.is_empty():
		var released: float = w.balls[0].pc
		if pitch.clock >= released + policy.turn[0] - SLACK:
			dir = policy.turn[1]
			w.turned = true
	if not pitching:
		dir = Vector2.ZERO
	_hold(t, w, dir)


static func _hold(t, w: Dictionary, dir: Vector2) -> void:
	var want := {KEY_LEFT: dir.x < 0.0, KEY_RIGHT: dir.x > 0.0, KEY_UP: dir.y < 0.0, KEY_DOWN: dir.y > 0.0}
	for code in want:
		if want[code] == w.held.get(code, false):
			continue
		if want[code]:
			t.press(code)
		else:
			t.release(code)
		w.held[code] = want[code]


# Runs the pitch from Idle and watches it until `done` or the frames run out.
static func _throw(t, pitch: Node, policy: Dictionary, done: Callable, frames := SET_FRAMES) -> Dictionary:
	var w := _new_log(policy)
	_start_watch(t, pitch, w)
	t.sm.run_attack("Pitch")
	w.ended = await t.wait_until(done, frames)
	_stop_watch(t, w)
	return w


static func _left_pitch(t, pitch: Node) -> Callable:
	return func() -> bool: return t.sm.current_state != pitch


static func _ids(list: Array) -> Array:
	return list.map(func(e): return str(e.id))


static func _results(pitch: Node) -> Array:
	return pitch.results.map(func(r): return "%s %s" % [r.kind, HitInfo.Result.keys()[r.result] if r.result is int else r.result])


#HOME RUN

static func _home_run(t) -> void:
	var pitch := await _ready_pitch(t, 0, [F, C, H])
	t.log_p("-- a real cycle's set, every red pressed %.2f s before its contact, the X left alone" % PRESS_LEAD)
	t.sm.start_cycle()
	t.stop_boss_timers()
	t.sm.finishers = ["Pitch"]
	var w := _new_log({"red_default": -PRESS_LEAD})
	_start_watch(t, pitch, w)
	t.sm.next_attack(t.sm.current_state)
	var broke: bool = await t.wait_until(func() -> bool: return t.sm.current_state.name == "Broken" or t.sm.current_state.name == "AwaitDelivery", SET_FRAMES)
	var broken_at: float = t.defense.clock
	var through: bool = await t.wait_until(func() -> bool: return t.sm.current_state.name == "PooSquat", 600)
	_stop_watch(t, w)
	var gain: float = t.boss.break_gauge.parry_gain
	t.log_p("slots %s; results %s; parried %s; health off him %s; HOME RUN! %d; gauge at each parry %s; states %s" % [pitch.slots, _results(pitch), _ids(w.parries), w.drops.map(func(d): return d.amount), w.words.filter(func(x): return x.text == "HOME RUN!").size(), w.gauge, w.states.map(func(s): return s.state)])
	t.check(w.parries.size() == 3 and w.parries.all(func(p): return p.id == &"mason_fastball" or p.id == &"mason_changeup") and w.hits.is_empty(), "every red parried, nothing landing (%s, %s)" % [_ids(w.parries), _ids(w.hits)])
	t.check(w.drops.size() == 3 and w.drops.all(func(d): return d.amount == pitch.home_run_chip), "each batted back into his head for %d (%s)" % [pitch.home_run_chip, w.drops.map(func(d): return d.amount)])
	t.check(w.words.filter(func(x): return x.text == "HOME RUN!").size() == 3, "HOME RUN! up for each")
	t.check(w.gauge.size() == 3 and absf(w.gauge[0] - gain) < 0.01 and absf(w.gauge[1] - 2.0 * gain) < 0.01 and absf(w.gauge[2] - 3.0 * gain) < 0.01, "his gauge up a parry_gain (%.1f) each parry (%s)" % [gain, w.gauge])
	t.check(w.drops.map(func(d): return d.streak) == [1, 2, 3], "the streak counting 1, 2, 3 (%s)" % [w.drops.map(func(d): return d.streak)])
	var down: Array = w.states.filter(func(s): return s.state == "Broken")
	var third: float = w.drops[2].t if w.drops.size() >= 3 else INF
	t.check(broke and not down.is_empty() and down[0].t - third <= 0.3 + 0.001 and down[0].t >= third - 0.001, "Broken within 0.3 s of the third home run arriving (%.3f s)" % (down[0].t - third if not down.is_empty() else -1.0))
	var after: Array = w.states.map(func(s): return s.state)
	t.check(not after.has("AwaitDelivery") and not after.has("Eat"), "no delivery and no eat that cycle (%s)" % [after])
	t.check(through and after.has("PooSquat") and after.find("PooSquat") > after.find("Broken"), "his next cycle once the Break is over (%.2f s down)" % (t.defense.clock - broken_at))


#READS

static func _reads(t) -> void:
	for phase in 2:
		var pitch := await _ready_pitch(t, phase, [F, C])
		var w := await _throw(t, pitch, {}, _left_pitch(t, pitch))
		t.log_p("-- phase %d, a still player: badges %s, balls %s, hits %s" % [phase + 1, w.badges.map(func(b): return "%s %.3f" % [b.kind, b.pc]), w.balls.map(func(b): return "%s %.3f" % [b.kind, b.pc]), w.hits.map(func(h): return "%s %.3f" % [h.id, h.pc])])
		t.check(w.ended and w.badges.size() == 2 and w.hits.size() == 2, "phase %d: both pitches badged and landing on a still player" % [phase + 1])
		for i in mini(w.hits.size(), w.badges.size()):
			var want: float = pitch.release_after + (pitch.changeup_flight if w.badges[i].kind == C else pitch.fastball_flight)
			var read: float = w.hits[i].pc - w.badges[i].badge_at
			t.check(absf(read - want) <= FRAME + 0.001, "phase %d: the %s's badge to its contact %.3f s, %.2f to a frame" % [phase + 1, w.badges[i].kind, read, want])
		for i in mini(w.balls.size(), w.badges.size()):
			var out: float = w.balls[i].pc - w.badges[i].badge_at
			t.check(absf(out - pitch.release_after) <= FRAME + 0.001, "phase %d: the %s leaves his hand %.3f s after its badge (%.2f)" % [phase + 1, w.balls[i].kind, out, pitch.release_after])
		var change: Array = w.kinds.filter(func(k): return k.kind == C)
		var change_badge: Array = w.badges.filter(func(b): return b.kind == C)
		var known: float = change_badge[0].badge_at - change[0].at if not change.is_empty() and not change_badge.is_empty() else -1.0
		t.check(known >= 0.55 - 0.001, "phase %d: a changeup's kind is known as its wind-up starts, %.2f s before its badge" % [phase + 1, known])

	t.log_p("-- the live window: put on the ball's path where it passes")
	for kind in [F, C]:
		for dt in [-0.09, 0.10, 0.20]:
			var pitch := await _ready_pitch(t, 0, [kind])
			var w := _new_log({})
			var pin := {"at": Vector2.INF}
			var hold := func() -> void:
				if pin.at == Vector2.INF and not w.balls.is_empty():
					var ball: Node2D = w.balls[0].node
					var offset: Vector2 = t.player.hurtBox.get_node("CollisionShape2D").global_position - t.player.global_position
					pin.at = ball.point_at(ball.flight + dt) - offset
				if pin.at != Vector2.INF:
					t.player.global_position = pin.at
					t.player.velocity = Vector2.ZERO
			_start_watch(t, pitch, w)
			t.physics_frame.connect(hold)
			t.sm.run_attack("Pitch")
			await t.wait_until(_left_pitch(t, pitch), SET_FRAMES)
			t.physics_frame.disconnect(hold)
			_stop_watch(t, w)
			var landed: Array = w.hits.filter(func(h): return PITCH_IDS.has(h.id))
			var late: float = landed[0].pc - pitch.contact_at if not landed.is_empty() else INF
			t.log_p("%s, on its path where it passes %+.2f s from its contact: %d hits%s" % [kind, dt, landed.size(), "" if landed.is_empty() else " at %+.3f s" % late])
			if dt > -pitch.live_lead and dt < pitch.live_tail:
				t.check(landed.size() == 1 and late >= dt - 0.03 and late <= dt + FRAME + 0.001, "%s: there %+.2f s, inside its live window, it hits (%+.3f s)" % [kind, dt, late])
			else:
				t.check(landed.is_empty(), "%s: there %+.2f s, outside its live window (%.2f before to %.2f after), it never hits" % [kind, dt, pitch.live_lead, pitch.live_tail])

	t.log_p("-- a changeup pressed at a fastball's timing, then at its own")
	var pitch := await _ready_pitch(t, 0, [C, C])
	var w := await _throw(t, pitch, {"from_badge": true, "reds": [pitch.release_after, 0.52]}, _left_pitch(t, pitch))
	t.log_p("presses at %s; badges at %s; hits %s; parried %s" % [w.presses, w.badges.map(func(b): return b.badge_at), _ids(w.hits), _ids(w.parries)])
	t.check(w.hits.size() == 1 and w.hits[0].id == &"mason_changeup" and w.hits[0].pc < w.badges[1].badge_at, "a press %.2f s after the badge (a fastball's) whiffs, and the changeup lands" % pitch.release_after)
	t.check(w.parries.size() == 1 and w.parries[0].id == &"mason_changeup", "a press 0.52 s after its badge parries it")

	t.log_p("-- walkers at walking speed in 8 directions, from the badge on")
	var walked := []
	for dir in DIRS:
		pitch = await _ready_pitch(t, 0, [F], WALK_FROM)
		w = await _throw(t, pitch, {"walk": dir, "walk_from_badge": true}, _left_pitch(t, pitch))
		walked.append(w.hits.filter(func(h): return h.id == &"mason_fastball").size())
	t.log_p("fastball hits per direction %s: %s" % [DIRS, walked])
	t.check(walked.all(func(n): return n == 1), "every walker is hit by the fastball (%s)" % [walked])

	t.log_p("-- walkers that turn %.2f +-%.2f s after the release" % [TURN_AT, TURN_JITTER])
	var caught := {F: 0, C: 0}
	for trial in TURN_TRIALS * 2:
		var kind: StringName = F if trial % 2 == 0 else C
		var axis: Vector2 = AXES[(trial / 2) % AXES.size()]
		# Turned off his line rather than across it, as a player stepping out of a pitch does.
		var turn := Vector2(-axis.y, axis.x)
		if turn.dot(AT - WALK_FROM) > 0.0 or (turn.dot(AT - WALK_FROM) == 0.0 and randf() < 0.5):
			turn = -turn
		var delay := clampf(randfn(TURN_AT, TURN_JITTER), TURN_AT - 2.0 * TURN_JITTER, TURN_AT + 2.0 * TURN_JITTER)
		pitch = await _ready_pitch(t, 0, [kind], WALK_FROM)
		w = await _throw(t, pitch, {"walk": axis, "walk_from_badge": true, "turn": [delay, turn]}, _left_pitch(t, pitch))
		var landed: Array = w.hits.filter(func(h): return PITCH_IDS.has(h.id))
		if not landed.is_empty():
			caught[kind] += 1
		t.log_p("  %s walking %s, turning %s %.3f s after the release: %s" % [kind, axis, turn, delay, "hit %+.3f s from its contact" % (landed[0].pc - pitch.contact_at) if not landed.is_empty() else "clear"])
	t.log_p("of %d each: fastballs that hit %d, changeups that hit %d" % [TURN_TRIALS, caught[F], caught[C]])
	t.check(caught[F] >= ceili(TURN_TRIALS * 0.95), "fastballs hit 95%% of the walkers that turn (%d of %d)" % [caught[F], TURN_TRIALS])
	t.check(TURN_TRIALS - caught[C] >= ceili(TURN_TRIALS * 0.9), "90%% get out of the changeup by turning (%d of %d)" % [TURN_TRIALS - caught[C], TURN_TRIALS])


#THE FAKE

static func _fake(t) -> void:
	t.log_p("-- a fastball home run, then a press on the hesitation's X")
	var pitch := await _ready_pitch(t, 0, [F, H])
	var w := _new_log({"reds": [-PRESS_LEAD], "x": 0.20, "quick": -PRESS_LEAD, "rearm": true})
	_start_watch(t, pitch, w)
	t.sm.run_attack("Pitch")
	await t.wait_until(func() -> bool: return w.xs.size() >= 1, SET_FRAMES)
	var before: float = t.defense.stamina
	var streak_before: int = pitch.streak
	var parry_streak_before: int = t.defense.parry_streak
	await t.wait_until(func() -> bool: return pitch.bitten, 120)
	var bitten_pc: float = pitch.clock
	await t.wait(1)
	var glowing: bool = is_instance_valid(pitch.glow)
	var streaks := [pitch.streak, t.defense.parry_streak]
	await t.wait_until(func() -> bool: return t.defense.clock - w.xs[0].t > 0.20 + t.defense.parry_window + 0.05, 120)
	var after: float = t.defense.stamina
	await t.wait_until(_left_pitch(t, pitch), SET_FRAMES)
	_stop_watch(t, w)
	var bite: Array = pitch.results.filter(func(r): return r.result is StringName and r.result == &"bitten")
	var quick: Array = w.balls.filter(func(b): return b.kind == &"quick")
	t.log_p("streaks before the bite %d and %d, after %s; stamina %.1f -> %.1f; words %s; glow %s; results %s; presses %s; quick out at %s; hits %s" % [streak_before, parry_streak_before, streaks, before, after, w.words.map(func(x): return x.text), glowing, _results(pitch), w.presses, quick.map(func(b): return b.pc), _ids(w.hits)])
	t.check(streak_before == 1 and parry_streak_before == 1 and streaks == [0, 0], "the bite ends both streaks, the home run's and the parry's")
	t.check(absf(before - after - pitch.feint_stamina) < 0.01, "it costs exactly %.0f stamina, and no whiff on top (%.1f)" % [pitch.feint_stamina, before - after])
	t.check(w.words.any(func(x): return x.text == "FEINT!") and glowing, "FEINT! and the glow on his hand")
	var out: float = quick[0].pc - bite[0].at if not quick.is_empty() and not bite.is_empty() else INF
	t.check(bite.size() == 1 and quick.size() == 1 and absf(out - pitch.quick_delay) <= FRAME + 0.001, "the quick pitch %.2f s after the press (%.3f)" % [pitch.quick_delay, out])
	t.check(not is_instance_valid(pitch.glow), "the glow gone once it has left his hand")
	t.check(w.hits.size() == 1 and w.hits[0].id == &"mason_quick_pitch" and w.parries.size() == 1, "it lands through a fresh press timed to it (%s)" % [_ids(w.hits)])

	t.log_p("-- the X left alone, a whiff in the hitch, then the red")
	pitch = await _ready_pitch(t, 0, [H])
	w = await _throw(t, pitch, {"hitch": 0.05, "red_default": -PRESS_LEAD}, _left_pitch(t, pitch))
	t.log_p("presses %s, X up at %s, results %s, parried %s, hits %s" % [w.presses, w.xs.map(func(x): return x.pc), _results(pitch), _ids(w.parries), _ids(w.hits)])
	t.check(w.presses.size() == 2 and not pitch.results.any(func(r): return r.result is StringName and r.result == &"bitten"), "the whiff in the hitch is no bite")
	t.check(w.parries.size() == 1 and w.parries[0].id == &"mason_fastball" and w.hits.is_empty(), "and the red after it is parried (rearm_parry at its badge)")


#THE KNOCKDOWN

static func _knockdown(t) -> void:
	t.log_p("-- home run, home run, hit")
	var pitch := await _ready_pitch(t, 0, [F, F, F])
	var w := await _throw(t, pitch, {"reds": [-PRESS_LEAD, -PRESS_LEAD, null]}, _left_pitch(t, pitch))
	t.log_p("results %s, states %s" % [_results(pitch), w.states.map(func(s): return s.state)])
	t.check(w.parries.size() == 2 and w.hits.size() == 1 and t.sm.current_state.name == "AwaitDelivery" and pitch.streak == 0, "no knockdown: the set plays out into the delivery, the streak 0")

	t.log_p("-- phase two: home run, a bite, then two home runs")
	pitch = await _ready_pitch(t, 1, [F, H, F, F])
	w = _new_log({"red_default": -PRESS_LEAD, "x": 0.15})
	_start_watch(t, pitch, w)
	t.sm.run_attack("Pitch")
	await t.wait_until(func() -> bool: return pitch.bitten, SET_FRAMES)
	var after_bite: int = pitch.streak
	await t.wait_until(_left_pitch(t, pitch), SET_FRAMES)
	_stop_watch(t, w)
	t.log_p("streak after the bite %d; results %s; now %s" % [after_bite, _results(pitch), t.sm.current_state.name])
	t.check(after_bite == 0 and t.sm.current_state.name == "AwaitDelivery", "the bite ends the streak, and two home runs after it are no knockdown")

	t.log_p("-- phase two: a miss, then three home runs")
	pitch = await _ready_pitch(t, 1, [F, F, F, F])
	w = await _throw(t, pitch, {"reds": [null], "red_default": -PRESS_LEAD}, _left_pitch(t, pitch))
	var down: Array = w.states.filter(func(s): return s.state == "Broken")
	var fourth: float = w.drops[2].t if w.drops.size() >= 3 else INF
	t.log_p("results %s; home runs arriving at %s; Broken at %s" % [_results(pitch), w.drops.map(func(d): return d.t), down.map(func(s): return s.t)])
	t.check(w.hits.size() == 1 and w.drops.size() == 3 and not down.is_empty() and down[0].t - fourth <= 0.3 + 0.001 and down[0].t >= fourth - 0.001, "knocked down on the fourth pitch's arrival")

	t.log_p("-- his gauge locked: three home runs and the set plays on")
	pitch = await _ready_pitch(t, 0, [F, F, F, F])
	t.hold_break_gauge(t.boss)
	w = await _throw(t, pitch, {"red_default": -PRESS_LEAD}, _left_pitch(t, pitch))
	t.log_p("results %s; now %s" % [_results(pitch), t.sm.current_state.name])
	t.check(w.parries.size() == 4 and w.drops.size() == 4 and t.sm.current_state.name == "AwaitDelivery" and not w.states.any(func(s): return s.state == "Broken"), "no Break: four home runs, and the set plays out into the delivery")


#RELEASE

# Nothing of the pitch left: no badge, X, glow, word or ball, his sheet back and nobody listening for presses.
static func _check_released(t, pitch: Node, case: String, sheet: Dictionary) -> void:
	var balls: Array = t.current_scene.get_children().filter(func(n): return n.get_script() != null and str(n.get_script().resource_path).ends_with("MasonPitchBall.gd") and not n.is_queued_for_deletion())
	var words: Array = t.boss.hud_layer.get_children().filter(func(n): return not n.is_queued_for_deletion() and (n.has_meta(&"home_run") or (n is Label and n.text == "FEINT!")))
	var sprite: Sprite2D = t.boss.sprite
	var listening: bool = t.defense.block_pressed.is_connected(pitch._on_block_pressed)
	t.log_p("%s: now %s; badges %d, X %s, glow %s, words %d, balls %d; sheet %s x%d flip %s; listening %s" % [case, t.sm.current_state.name, t.live_tells().size(), is_instance_valid(pitch.mark), is_instance_valid(pitch.glow), words.size(), balls.size(), sprite.texture.resource_path.get_file(), sprite.hframes, sprite.flip_h, listening])
	t.check(t.live_tells().is_empty() and not is_instance_valid(pitch.mark) and not is_instance_valid(pitch.glow), "%s: no badge, X or glow left" % case)
	t.check(words.is_empty() and balls.is_empty(), "%s: no word or ball left (%d, %d)" % [case, words.size(), balls.size()])
	# Broken wears its own sheet once it is in (MasonArtLayout.broken), and gives his back as it ends.
	var want: Dictionary = sheet
	var broken: Dictionary = MasonArtLayout.broken()
	if t.sm.current_state.name == "Broken" and broken.has("texture"):
		want = {"texture": load(broken.texture), "hframes": broken.hframes, "flip_h": false}
	t.check(sprite.texture == want.texture and sprite.hframes == want.hframes and sprite.flip_h == want.flip_h, "%s: his sheet back as it was (%s)" % [case, sprite.texture.resource_path.get_file()])
	t.check(not listening and pitch.released, "%s: released, and no longer listening for presses" % case)


static func _sheet(t) -> Dictionary:
	var sprite: Sprite2D = t.boss.sprite
	return {"texture": sprite.texture, "hframes": sprite.hframes, "flip_h": sprite.flip_h}


static func _release(t, won: bool) -> void:
	t.log_p("-- a Break 0.05 s after a bite")
	var pitch := await _ready_pitch(t, 0, [H])
	var sheet := _sheet(t)
	var w := _new_log({"x": 0.10})
	_start_watch(t, pitch, w)
	t.sm.run_attack("Pitch")
	await t.wait_until(func() -> bool: return pitch.bitten, SET_FRAMES)
	await t.wait(3)
	var up := [is_instance_valid(pitch.glow), not w.words.is_empty()]
	t.boss.break_gauge.add(t.boss.break_gauge.max_value)
	await t.wait(2)
	_stop_watch(t, w)
	t.check(up == [true, true] and t.sm.current_state.name == "Broken", "Broken with the glow and FEINT! up (%s)" % [up])
	_check_released(t, pitch, "a Break after a bite", sheet)
	await t.wait(30)
	t.check(t.hazards_of("MasonPitchBall.gd").is_empty() and w.hits.is_empty(), "a Break after a bite: the quick pitch never comes")

	t.log_p("-- a Break with a fastball in the air")
	pitch = await _ready_pitch(t, 0, [F])
	w = _new_log({})
	_start_watch(t, pitch, w)
	t.sm.run_attack("Pitch")
	await t.wait_until(func() -> bool: return not t.hazards_of("MasonPitchBall.gd").is_empty(), SET_FRAMES)
	var flying: bool = not t.hazards_of("MasonPitchBall.gd").is_empty()
	t.boss.break_gauge.add(t.boss.break_gauge.max_value)
	await t.wait(2)
	t.check(flying and t.sm.current_state.name == "Broken", "Broken with the fastball in the air")
	_check_released(t, pitch, "a Break mid-flight", sheet)
	await t.wait(30)
	_stop_watch(t, w)
	t.check(w.hits.is_empty(), "a Break mid-flight: nothing lands after")

	t.log_p("-- paused with a changeup in the air")
	pitch = await _ready_pitch(t, 0, [C])
	w = _new_log({})
	_start_watch(t, pitch, w)
	t.sm.run_attack("Pitch")
	await t.wait_until(func() -> bool: return not t.hazards_of("MasonPitchBall.gd").is_empty(), SET_FRAMES)
	await t.tap_pause()
	var ball: Node2D = t.hazards_of("MasonPitchBall.gd")[0] if not t.hazards_of("MasonPitchBall.gd").is_empty() else null
	var held := [pitch.clock, ball.global_position if ball else Vector2.INF, ball.clock if ball else -1.0, t.live_tells().map(func(x): return x.time_left)]
	await t.wait(40)
	var still := [pitch.clock, ball.global_position if is_instance_valid(ball) else Vector2.INF, ball.clock if is_instance_valid(ball) else -1.0, t.live_tells().map(func(x): return x.time_left)]
	t.check(ball != null and t.pause_menu().is_open() and t.paused and held == still, "paused with the changeup in the air, 40 frames move none of it (%s)" % [held])
	await t.tap_pause()
	t.pause_menu().grace_until_msec = 0
	var ended: bool = await t.wait_until(_left_pitch(t, pitch), SET_FRAMES)
	_stop_watch(t, w)
	t.check(ended and not t.paused and w.hits.size() == 1 and t.sm.current_state.name == "AwaitDelivery", "and the resume plays it out: it lands, and the set ends")
	_check_released(t, pitch, "paused and resumed", sheet)

	if won:
		t.log_p("-- Mason killed by a phase-two home run")
		pitch = await _ready_pitch(t, 1, [F])
		t.boss.boss_health = pitch.home_run_chip
		w = await _throw(t, pitch, {"red_default": -PRESS_LEAD}, func() -> bool: return t.sm.current_state.name == "Defeated")
		await t.wait(20)
		t.check(w.ended and w.parries.size() == 1 and t.boss.boss_health == 0, "beaten by the home run (%s)" % t.sm.current_state.name)
		_check_released(t, pitch, "Mason beaten", sheet)
	else:
		t.log_p("-- the player killed by a pitch")
		pitch = await _ready_pitch(t, 0, [F, F])
		t.player.playerHealth = 1
		w = await _throw(t, pitch, {}, func() -> bool: return t.player.fight_over)
		await t.wait(20)
		t.check(w.ended and w.hits.size() == 1 and t.player.playerHealth == 0 and t.sm.current_state.name == "Idle" and t.sm.player_defeated, "killed by the fastball, and the outro stands him down (%s)" % t.sm.current_state.name)
		_check_released(t, pitch, "the player's death", sheet)
	await t.wait(60)
	t.check(t.root.get_children().filter(func(n): return n.name == "FightOutro").size() == 1, "exactly one outro")


#FAIR

# The ideal player: every red pressed 0.12 s before its contact and never an X; walking ones keep walking through
# it, along an axis, tapping the parry, and turn round only as a wind-up starts.
static func _fair(t) -> void:
	var sets := 0
	var knocked := 0
	for i in FAIR_SPOTS.size() * 2:
		var walking: bool = i >= FAIR_SPOTS.size()
		var spot: Vector2 = FAIR_SPOTS[i % FAIR_SPOTS.size()]
		var phase: int = i % 2
		var mason_at: Vector2 = AT if (i / 2) % 2 == 0 else AT_LEFT
		var pitch := await _ready_pitch(t, phase, [], spot, mason_at)
		var w := _new_log({"red_default": -PRESS_LEAD})
		_start_watch(t, pitch, w)
		var walker := {"dir": Vector2.ZERO, "kind_at": -INF, "walked": 0.0, "last": t.player.global_position}
		var walk := func() -> void:
			walker.walked += t.player.global_position.distance_to(walker.last)
			walker.last = t.player.global_position
			if not walking or t.sm.current_state != pitch:
				_hold(t, w, Vector2.ZERO)
				return
			if pitch.kind_at != walker.kind_at:
				walker.kind_at = pitch.kind_at
				var room: Rect2 = Rect2(260, 260, 1400, 560)
				var options := AXES.filter(func(a): return room.has_point(t.player.global_position + a * 360.0))
				walker.dir = options[randi() % options.size()] if not options.is_empty() else Vector2.ZERO
			_hold(t, w, walker.dir)
		t.physics_frame.connect(walk)
		t.sm.run_attack("Pitch")
		var ended: bool = await t.wait_until(_left_pitch(t, pitch), SET_FRAMES)
		t.physics_frame.disconnect(walk)
		_stop_watch(t, w)
		var reds: Array = pitch.results.filter(func(r): return r.kind == F or r.kind == C)
		var parried: Array = reds.filter(func(r): return r.result is int and r.result == HitInfo.Result.PARRIED)
		var bites: int = pitch.results.filter(func(r): return r.result is StringName and r.result == &"bitten").size()
		var down: bool = t.sm.current_state.name == "Broken"
		sets += 1
		if down:
			knocked += 1
		t.log_p("%s at %s (%.0f px walked), Mason at %s, phase %d, set %s: %d of %d reds parried, %d bites, %d hits, %s" % ["walking" if walking else "standing", spot, walker.walked, mason_at, phase + 1, pitch.slots, parried.size(), reds.size(), bites, w.hits.size(), t.sm.current_state.name])
		t.check(ended and parried.size() == reds.size() and bites == 0 and w.hits.is_empty() and down, "%s at %s, phase %d: every red parried, no X pressed, no hit, and the knockdown" % ["walking" if walking else "standing", spot, phase + 1])
	t.log_p("knocked down in %d of %d sets" % [knocked, sets])


#GRACE

static func _grace(t) -> void:
	var grace: float = t.sm.cycle_contact_grace
	var hits := []
	var on_hit := func(hit) -> void:
		if hit.attack_id == &"mason_poo_contact":
			hits.append(t.defense.clock)
	t.defense.hit_taken.connect(on_hit)
	t.log_p("-- standing in him as a cycle starts")
	await t.reset_gauged(t.fight_spec.home)
	t.sm.rest_point = t.boss.global_position + t.sm.BOMB_SPAWN_OFFSET
	await t.hold_in_him(0.2)
	hits.clear()
	var start: float = t.defense.clock
	t.sm.start_cycle()
	t.sm.squat_timer.stop()
	await t.hold_in_him(grace + 0.3)
	var first: float = hits[0] - start if not hits.is_empty() else INF
	t.log_p("held in him: hits at %s s" % [hits.map(func(h): return snappedf(h - start, 0.001))])
	t.check(first >= grace - 0.001 and first <= grace + 2.0 * FRAME + 0.001, "untouched for the %.2f s grace, and hit as it runs out (%.3f s)" % [grace, first])

	t.log_p("-- walking into his squat inside the grace")
	await t.reset_gauged(t.fight_spec.home)
	t.sm.rest_point = t.boss.global_position + t.sm.BOMB_SPAWN_OFFSET
	var box: Rect2 = t.area_rect_any(t.boss.contact_hitbox)
	var hurt: Rect2 = t.area_rect_any(t.player.hurtBox)
	await t.settle_player(t.player.global_position + Vector2(box.position.x - 30.0 - hurt.end.x, box.get_center().y - hurt.get_center().y))
	t.clear_iframes()
	hits.clear()
	start = t.defense.clock
	t.sm.start_cycle()
	t.sm.squat_timer.stop()
	await t.wait(4)
	t.press(KEY_RIGHT)
	await t.wait_until(func() -> bool: return not hits.is_empty(), 30)
	t.release(KEY_RIGHT)
	first = hits[0] - start if not hits.is_empty() else INF
	t.log_p("walked in: hit at %.3f s" % first)
	t.check(first < grace, "walking into him is hit inside the grace (%.3f s)" % first)
	t.defense.hit_taken.disconnect(on_hit)
