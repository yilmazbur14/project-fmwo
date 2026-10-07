extends RefCounted

# jordan_kaiju tier=model: the experienced-player model of the 2026-10-04 playtests (scratchpad playtest_1004/BRIEF.md)
# playing his whole phase 1 on the kaiju, from his first turn to his KO or theirs. Reports only; it never fails.
#   reactions   a new tell 250 +/- 50 ms, learned (seen twice, or the learned kind) 200 +/- 40 ms
#   parries     first exposure: at the badge plus the reaction; learned: 0.12 s before contact, 85% of the time, else
#               0.25 s late
#   dashes      a perfect dodge 70% of the time (its window over 150 ms), else the dash goes 0.12 s early or late; never
#               below a third of the stamina bar unless forced
#   moving      600 px/s about a spot in the open ring, the burn lines crossed only by a dash
#   offence     every knock-off and Break punched to its POW, the finisher mashed at 8.5 presses a second, the interval
#               accumulated so a fixed-fps run doesn't round it down
# Its answers: the figures' blasts parried when one will be on them; the beam outrun along its sweep where there is room
# past its end, else dashed through; the stomp parried; the tail stepped out of up or down, else dashed through; a
# quake ring dashed through.
# Args after `--`: kinds=first,learned (both by default) and seeds=1-8 (a range or a single seed); for trying a lever
# without editing it, hp=<his health>, reads=<N to a Break>, funkos=<A breath>,<A stomp>,<B breath>,<B stomp>,
# cycle_a=<turn>,<turn>,... (Phase A's order; cycle_b= Phase B's) and set=<state>.<property>=<value> (any of his
# states' exports, or sm. for his state machine's; as many as wanted).

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")
const ArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const Breath := preload("res://Scripts/States/Jordan/JordanBreath.gd")
const Stomp := preload("res://Scripts/States/Jordan/JordanStomp.gd")
const Beam := preload("res://Scripts/JordanKaijuBeam.gd")
const BurnLine := preload("res://Scripts/JordanBurnLine.gd")
const TailSweep := preload("res://Scripts/JordanTailSweep.gd")
const FunkoFigure := preload("res://Scripts/FunkoFigureScript.gd")
const FunkoThrow := preload("res://Scripts/JordanFunkoThrow.gd")
const QuakeRing := preload("res://Scripts/BixbyQuakeRingScript.gd")
const K := preload("res://art_source/defense_tests/jordan/kaiju.gd")

const FRAME := 1.0 / 60.0
const MASH_RATE := 8.5
const STATION := Vector2(1350, 560)
const SAFETY := 25.0
const CAP_SECONDS := 240.0
const PLAYER_HEALTH := 8
const DASH_COST := 1.0 / 3.0


static func run(t) -> void:
	var kinds: Array = ["first", "learned"]
	var seeds: Array = range(1, 9)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("kinds="):
			kinds = arg.substr(6).split(",")
		elif arg.begins_with("seeds="):
			var spec := arg.substr(6)
			if spec.contains("-"):
				seeds = range(int(spec.get_slice("-", 0)), int(spec.get_slice("-", 1)) + 1)
			else:
				seeds = [int(spec)]
	var runs: Array = []
	for kind in kinds:
		for s in seeds:
			var result: Dictionary = await play(t, s, kind == "learned")
			result.kind = kind
			runs.append(result)
			t.log_p("MODEL %s" % JSON.stringify(result))
	summarise(t, runs)


static func play(t, seed_value: int, learned: bool) -> Dictionary:
	seed(seed_value)
	await t.load_fight("jordan")
	t.boss = t.current_scene.get_node(K.BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = seed_value
	t.player.playerHealth = PLAYER_HEALTH
	_levers(t)
	var bot := Bot.new(t, seed_value, learned)
	await t.wait_until(func(): return t.sm.fighting, 600)
	var started: float = t.boss.fight_clock
	while not t.boss.defeated and t.player.playerHealth > 0 and t.boss.fight_clock - started < CAP_SECONDS:
		bot.step()
		await t.physics_frame
	bot.keys.stop()
	t.release(KEY_SHIFT)
	var seconds: float = t.boss.fight_clock - started
	return {
		"seed": seed_value, "won": t.boss.defeated, "seconds": snappedf(seconds, 0.1),
		"jordan": t.boss.boss_health, "player": maxi(t.player.playerHealth, 0), "lost": bot.lost,
		"hits": bot.hits, "seen": bot.seen, "breaks": bot.breaks, "knockoffs": bot.knockoffs,
		"parries": bot.parries, "dodges": bot.dodges, "phase_b_at": snappedf(bot.phase_b_at, 0.1),
		"reads_in": snappedf(bot.gauge_in / t.boss.break_gauge.parry_gain, 0.1),
		"reads_out": snappedf(bot.gauge_out / t.boss.break_gauge.parry_gain, 0.1),
		"dealt": {"punches": bot.dealt_punch, "finisher": bot.dealt_finisher, "blasts": bot.dealt_blast},
	}


static func _levers(t) -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("hp="):
			t.boss.max_health = int(arg.substr(3))
			t.boss.boss_health = t.boss.max_health
		elif arg.begins_with("set="):
			var spec := arg.substr(4)
			var path := spec.get_slice("=", 0)
			var owner: Node = t.sm if path.get_slice(".", 0) == "sm" else t.sm.states[path.get_slice(".", 0)]
			owner.set(path.get_slice(".", 1), str_to_var(spec.get_slice("=", 1)))
		elif arg.begins_with("cycle_a=") or arg.begins_with("cycle_b="):
			var cycle: Array[String] = []
			for turn in arg.substr(8).split(","):
				cycle.append(turn)
			t.sm.set(arg.substr(0, 7), cycle)
		elif arg.begins_with("funkos="):
			var n: Array = Array(arg.substr(7).split(",")).map(func(v): return int(v))
			t.sm.funko_counts = [[n[0], n[1]], [n[2], n[3]]]
		elif arg.begins_with("reads="):
			var read := 100.0 / float(arg.substr(6))
			var gauge: Node = t.boss.break_gauge
			gauge.parry_gain = read
			gauge.grab_parry_gain = 2.0 * read
			gauge.reflect_gain = 2.0 * read
			gauge.perfect_dodge_gain = read
			gauge.punch_gain = read / 4.0
			gauge.charged_punch_gain = read / 2.0
			gauge.hit_loss = read
			gauge.guard_break_loss = 2.0 * read


static func summarise(t, runs: Array) -> void:
	for kind in ["first", "learned"]:
		var mine := runs.filter(func(r): return r.kind == kind)
		if mine.is_empty():
			continue
		var wins := mine.filter(func(r): return r.won)
		var seconds := 0.0
		var lost := 0
		var hits := {}
		var seen := {}
		for r in mine:
			seconds += r.seconds
			lost += r.lost
			for id in r.hits:
				hits[id] = hits.get(id, 0) + r.hits[id]
			for id in r.seen:
				seen[id] = seen.get(id, 0) + r.seen[id]
		var kill := 0.0
		for r in wins:
			kill += r.seconds
		var rate := float(wins.size()) / mine.size()
		t.log_p("MODEL SUMMARY %s: clear %d/%d (%.0f%%), %.1f half-hearts a minute, mean kill %s s, Jordan left on losses %s" % [
			kind, wins.size(), mine.size(), rate * 100.0, lost / seconds * 60.0,
			("%.1f" % (kill / wins.size())) if not wins.is_empty() else "-",
			mine.filter(func(r): return not r.won).map(func(r): return r.jordan)])
		var rows: Array = []
		for id in seen:
			rows.append("%s %d hit / %d seen (%.2f a time)" % [id, hits.get(id, 0), seen[id], float(hits.get(id, 0)) / maxf(seen[id], 1.0)])
		t.log_p("MODEL ATTACKS %s: %s" % [kind, rows])


# One fight played by the model, a physics step at a time.
class Bot:
	var t
	var rng := RandomNumberGenerator.new()
	var learned := false
	var keys
	var exposures := {}
	var clock := 0.0
	# Guard presses due: [game time, the figure it is for or null]. A figure's press is only made if it is still
	# within 150 px then (the playtest bot's rule). A press is let go 4 frames later.
	var presses: Array = []
	var release_at := -1.0
	# A dash due: [time, direction].
	var dash_due: Array = []
	var planned := {}
	var mash_next := 0.0
	var mash_count := 0
	var punch_next := 0.0
	var outrun_until := -1.0
	var outrun_plan: Dictionary = {}
	var step_out_until := -1.0
	var step_out_dir := Vector2.ZERO
	var hits := {}
	var seen := {}
	var lost := 0
	var breaks := 0
	var knockoffs := 0
	var parries := 0
	var dodges := 0
	var phase_b_at := -1.0
	var last_state := ""
	var debug := false
	var press_log: Array = []
	var gauge_in := 0.0
	var gauge_out := 0.0
	var gauge_was := 0.0
	var last_drop := 0.0
	var health_was := 0
	var dealt_punch := 0
	var dealt_finisher := 0
	var dealt_blast := 0

	func _init(tester, seed_value: int, is_learned: bool) -> void:
		t = tester
		learned = is_learned
		rng.seed = seed_value * 7919 + (1 if is_learned else 0)
		keys = K.Keys.new(t)
		t.defense.hit_taken.connect(_on_hit)
		t.defense.parried.connect(func(_h, _p, _s, _n): parries += 1)
		t.defense.perfect_dodged.connect(func(_h): dodges += 1)
		t.defense.block_pressed.connect(func(credited): press_log.append([snappedf(clock, 0.01), credited]))
		debug = OS.get_cmdline_user_args().has("debug=1")
		t.boss.break_gauge.changed.connect(_on_gauge)
		t.boss.break_gauge.broke.connect(_on_broke)
		health_was = t.boss.boss_health

	func _on_gauge(value: float, _max_value: float) -> void:
		last_drop = 0.0
		if value > gauge_was:
			gauge_in += value - gauge_was
		else:
			last_drop = gauge_was - value
			gauge_out += last_drop
		gauge_was = value

	# A Break empties it (changed to 0 first): that was the read that filled it, not a loss.
	func _on_broke() -> void:
		gauge_out -= last_drop
		gauge_in += t.boss.break_gauge.max_value - last_drop
		last_drop = 0.0

	# Where his health went: the finisher's, a punch's or a punched figure's blast, read off what he is in when it goes.
	func _track_damage() -> void:
		var now: int = t.boss.boss_health
		if now >= health_was:
			health_was = now
			return
		var lost_now := health_was - now
		health_was = now
		var finisher: Node = t.player.get_node("Finisher")
		if finisher.is_active() or t.boss.is_juggled():
			dealt_finisher += lost_now
		elif t.sm.is_open():
			dealt_punch += lost_now
		else:
			dealt_blast += lost_now

	func _on_hit(hit: RefCounted) -> void:
		hits[hit.attack_id] = hits.get(hit.attack_id, 0) + 1
		lost += hit.damage
		if debug and hit.attack_id == &"jordan_kaiju_stomp":
			t.log_p("  STOMP HIT at %.2f: presses %s, stamina %.0f, planned %s" % [clock, press_log.slice(-3), t.defense.stamina, presses])
		elif debug and hit.attack_id == &"jordan_kaiju_breath":
			t.log_p("  BREATH HIT at %.2f: outrun %s, dash due %s, stamina %.0f, feet %s" % [clock, outrun_until > clock, dash_due, t.defense.stamina, soles()])

	func _see(id: StringName, key: Variant) -> bool:
		if planned.has(key):
			return false
		planned[key] = true
		seen[id] = seen.get(id, 0) + 1
		return true

	func reaction(tell: StringName) -> float:
		var times: int = exposures.get(tell, 0)
		exposures[tell] = times + 1
		if learned or times >= 2:
			return maxf(0.12, rng.randfn(0.200, 0.040))
		return maxf(0.15, rng.randfn(0.250, 0.050))

	func is_new(tell: StringName) -> bool:
		return not learned and exposures.get(tell, 0) < 2

	func soles() -> Vector2:
		return t.sm.player_feet()

	func step() -> void:
		clock += FRAME
		_track_damage()
		var sm = t.sm
		var state: String = sm.current_state.name
		if state != last_state:
			if state == "Broken":
				breaks += 1
			if state == "Dismounted":
				knockoffs += 1
			last_state = state
		if phase_b_at < 0.0 and sm.phase_b:
			phase_b_at = t.boss.fight_clock
		var finisher: Node = t.player.get_node("Finisher")
		if finisher.is_active():
			keys.stop()
			_mash(finisher)
			return
		mash_count = 0
		_guard_presses()
		_watch_figures()
		_watch_breath(sm)
		_watch_stomp(sm)
		_watch_rings()
		if _dash_now() or clock < dash_hold_until:
			return
		if sm.is_open() and not t.player.is_action_locked:
			_punish()
			return
		if punishing:
			punishing = false
			t.player.clear_face_point()
		if outrun_until > clock and not outrun_plan.is_empty():
			var a: float = (soles() - outrun_plan.origin).angle()
			_move(Vector2.from_angle(a).rotated(PI / 2.0) * float(outrun_plan.dir), true)
			return
		if step_out_until > clock:
			_move(step_out_dir, true)
			return
		var to: Vector2 = STATION - soles()
		_move(to if to.length() > SAFETY else Vector2.ZERO, false)

	#MOVING

	func _move(direction: Vector2, urgent: bool) -> void:
		if direction == Vector2.ZERO:
			keys.stop()
			return
		var ahead: Vector2 = soles() + direction.normalized() * 60.0
		for burn in t.sm.live_burns():
			if burn.distance_to_point(ahead) <= BurnLine.HALF_WIDTH + Beam.FOOT_RADIUS + SAFETY:
				if _can_dash():
					_dash(direction)
					return
				if not urgent:
					keys.stop()
					return
		keys.toward(direction)

	func _can_dash() -> bool:
		return t.defense.stamina >= t.defense.max_stamina * DASH_COST - 0.01 and not t.defense.is_dash_recovering() and not t.defense.is_dash_cooling_down()

	# The dash reads its direction a frame on: the keys stay on it for the dash.
	func _dash(direction: Vector2) -> void:
		keys.toward(direction)
		t.tap(KEY_W)
		dash_hold_until = clock + 8.0 * FRAME

	func _dash_now() -> bool:
		if dash_due.is_empty() or clock < dash_due[0]:
			return false
		var direction: Vector2 = dash_due[1]
		dash_due.clear()
		_dash(direction)
		return true

	# A dash timed for an arrival `at`: on time 70% of the time, else 0.12 s early or late.
	func _plan_dash(at: float, direction: Vector2) -> void:
		var when := at - 2.0 * FRAME
		if rng.randf() >= 0.70:
			when += 0.12 if rng.randf() < 0.5 else -0.12
		dash_due = [maxf(when, clock), direction]

	#GUARDING

	func _guard_presses() -> void:
		if release_at > 0.0 and clock >= release_at:
			release_at = -1.0
			t.release(KEY_SHIFT)
		for i in range(presses.size() - 1, -1, -1):
			if clock >= presses[i][0]:
				var fig = presses[i][1]
				presses.remove_at(i)
				if fig != null and (not is_instance_valid(fig) or fig.global_position.distance_to(t.player.global_position) > 150.0):
					continue
				if release_at < 0.0:
					t.press(KEY_SHIFT)
					release_at = clock + 4.0 * FRAME

	# A press for a hit landing `in_seconds` from now, told `told` seconds ago.
	func _plan_parry(tell: StringName, in_seconds: float, figure: Node = null) -> void:
		var newbie := is_new(tell)
		var react := reaction(tell)
		var at := clock + react
		if not newbie:
			at = clock + in_seconds - 0.12 + (0.0 if rng.randf() < 0.85 else 0.25)
		presses.append([at, figure])

	func _watch_figures() -> void:
		for fig in t.get_nodes_in_group(FunkoFigure.FIGURE_GROUP):
			if not is_instance_valid(fig) or not fig.told:
				continue
			if not _see(FunkoThrow.ATTACK_ID, fig.get_instance_id()):
				continue
			var blast_in: float = fig.fuse - fig.age + FunkoFigure._first_hit_time()
			_plan_parry(FunkoThrow.ATTACK_ID, blast_in, fig)

	#THE BREATH

	func _watch_breath(sm) -> void:
		var breath: Node = sm.states["Breath"]
		if sm.current_state != breath:
			return
		for i in breath.plans.size():
			var plan: Dictionary = breath.plans[i]
			if not _see(&"jordan_kaiju_breath", "breath %d" % _fight_time(breath, plan.lock)):
				continue
			var react := reaction(&"jordan_kaiju_breath")
			var room: float = plan.room_plus if plan.dir > 0.0 else plan.room_minus
			# Past its end by its band and a margin.
			var outrun: bool = room >= breath.s_end + Beam.HALF_WIDTH + Beam.FOOT_RADIUS + SAFETY
			if outrun:
				outrun_plan = plan
				outrun_until = clock + (plan.fire - breath.clock) + breath.grow_time + absf(plan.end - plan.start) / plan.omega + 0.35
				# Moving starts after the reaction.
				step_out_until = -1.0
				dash_due.clear()
				outrun_until = maxf(outrun_until, clock + react)
				_delay_move(react)
			else:
				var edge: float = (Beam.HALF_WIDTH + Beam.FOOT_RADIUS) / float(plan.v_eff)
				var arrive: float = clock + (plan.contact - breath.clock) - edge
				var a: float = (soles() - plan.origin).angle()
				_plan_dash(arrive, -Vector2.from_angle(a).rotated(PI / 2.0) * float(plan.dir))

	var hold_until := -1.0
	var dash_hold_until := -1.0
	var punishing := false

	func _delay_move(seconds: float) -> void:
		hold_until = clock + seconds

	# A time on a turn's own clock, which starts over every turn, as centiseconds of the fight's: a key that tells this
	# turn's beat from the last one's.
	func _fight_time(state: Node, at: float) -> int:
		return roundi((t.boss.fight_clock - (state.clock - at)) * 100.0)

	#THE STOMP

	func _watch_stomp(sm) -> void:
		var stomp: Node = sm.states["Stomp"]
		if sm.current_state != stomp:
			return
		for i in stomp.latch_times.size():
			if not _see(&"jordan_kaiju_stomp", "stomp %d" % _fight_time(stomp, stomp.latch_times[i])):
				continue
			var impact_in: float = stomp.latch_time + stomp.drop_time - (stomp.clock - stomp.latch_times[i])
			_plan_parry(&"jordan_kaiju_stomp", impact_in)
		if stomp.beat == Stomp.Beat.TAIL_WINDUP and _see(&"jordan_kaiju_tail", "tail %d" % _fight_time(stomp, stomp.beat_at)):
			var react := reaction(&"jordan_kaiju_tail")
			var kaiju: Node2D = sm.kaiju
			var feet: Vector2 = soles()
			var up_room: float = feet.y - 192.0
			var down_room: float = 945.0 - feet.y
			var need_up: float = feet.y - (kaiju.feet_point().y - TailSweep.RADII.y - 30.0)
			var need_down: float = (kaiju.feet_point().y + TailSweep.RADII.y + 30.0) - feet.y
			var reach: float = (stomp.tail_windup + stomp.tail_lead - react) * 600.0
			if need_up <= up_room and need_up <= reach:
				step_out_dir = Vector2.UP
				step_out_until = clock + stomp.tail_windup + stomp.tail_spin
			elif need_down <= down_room and need_down <= reach:
				step_out_dir = Vector2.DOWN
				step_out_until = clock + stomp.tail_windup + stomp.tail_spin
			else:
				var arrive: float = clock + stomp.tail_windup + stomp.tail_lead - 0.05
				var away: Vector2 = (feet - kaiju.feet_point()).normalized()
				_plan_dash(arrive, away.rotated(PI / 2.0))

	#THE QUAKE RING

	func _watch_rings() -> void:
		for ring in t.get_nodes_in_group("jordan_hazard"):
			if ring.get_script() != QuakeRing or not is_instance_valid(ring.player):
				continue
			if not _see(&"jordan_kaiju_quake", ring.get_instance_id()):
				continue
			var feet: Vector2 = soles() - ring.global_position
			var floor_distance: float = Vector2(feet.x, feet.y / 0.36).length()
			var arrive: float = clock + maxf(floor_distance - ring.radius - 36.0, 0.0) / ring.speed
			_plan_dash(arrive, (soles() - ring.global_position).normalized() * -1.0)

	#OFFENCE

	# BossBroken's spot beside him, the punch reaching over his box's edge by half its length.
	func _punish() -> void:
		var box: Rect2 = t.boss.hurtbox_rect()
		var side := 1.0 if t.player.global_position.x >= box.get_center().x else -1.0
		var facing: int = t.player.Facing.LEFT if side > 0.0 else t.player.Facing.RIGHT
		var reach: Rect2 = t.player.punch_box(facing)
		var edge: float = box.end.x if side > 0.0 else box.position.x
		var spot := Vector2(edge - reach.get_center().x * t.player.global_scale.x, box.end.y - 42.0 + 3.0)
		var to: Vector2 = spot - t.player.global_position
		if to.length() > 10.0:
			_move(to, true)
			return
		keys.stop()
		punishing = true
		if clock >= punch_next:
			t.player.face_point(box.get_center())
			t.tap(KEY_Q)
			punch_next = clock + maxf(0.1, rng.randfn(0.16, 0.03))

	func _mash(finisher: Node) -> void:
		if not finisher.prompt_visible or not (finisher.phase == 2 or finisher.phase == 3):
			mash_next = clock + reaction(&"mash_prompt")
			return
		finisher.min_press_interval = 0.0
		if clock < mash_next:
			return
		var pair: Array = finisher.mash_actions()
		t.tap(t.MASH_KEYS[pair[mash_count % 2]])
		mash_count += 1
		mash_next += maxf(0.05, (1.0 / MASH_RATE) * (1.0 + rng.randfn(0.0, 0.15)))
