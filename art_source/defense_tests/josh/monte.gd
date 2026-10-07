extends RefCounted

# josh_monte (the user, 2026-09-29): Josh's Portal Monte (JoshCardsPortalMonte), his third attack, on whichever art is
# in. --fixed-fps 60, one tier a run (tier=; normal is parry). Each run starts from Idle after the gauge spec's reset,
# with his order pinned to the Monte alone.
#   parry     a bot pressing 4 frames before each red contact and never on a yellow. As it ships (monte_parry_ends
#             off, the user's answer of 2026-10-04): every round plays out, each red PARRIED, no stagger, he comes back
#             out under his gate after the last and his Recover is recover_time, a read up a parry, unhurt, no feint.
#             Then with monte_parry_ends on: round 1's red PARRIED, and the attack ends on that frame - the rest of the
#             round's gates closing, the player free, him in view - he is knocked monte_knock px back toward his gate,
#             and his Recover opens monte_stagger_time later, lasting recover_time + monte_parry_recover_bonus; one
#             read up, unhurt, no feint.
#   bite      a press on round 1's first yellow: FEINT!, where JoshMonteLayout.word_centre puts it clear of the round's
#             gates and marks, 40 stamina off and no whiff on top, the streak ended, and the next burst a punish that
#             lands; then a press on the attack's very last burst, a yellow: one read off his gauge and no punish.
#   hit       nothing pressed: every red HITs, one of them landing inside the i-frames; the yellows touch nothing; he
#             comes back out under his gate, and his Recover is recover_time; a read off his gauge a red.
#   timing    one mark up at a time; each contact 0.54 s after its mark and each mark 0.62 after the one before, to the
#             frame; the rounds (monte_rounds, five since 2026-10-06) at 0.50 s and every 2.41 s after; the gates yet to
#             burst drawn alike, and the real him drawn as a
#             fake is, frame for frame, until its contact; a whiff just before a red's mark doesn't lock it out
#             (rearm_parry); over 300 seeded rounds each burst is the real him 25-42% of the time.
#   placement from 41 player spots - the corners, the rope strips and the art pass's (900, 620) among them: three gates each monte_min_radius or
#             more from the player, PLACE_MIN_GAP apart, their rect and mark in view and clear of the HUD, never the
#             drawn-in last resort; a re-deal turned REDEAL_MIN_TURN off the last whenever one fits; no mark over
#             another gate on a deal or a re-deal (logged against place() without that preference); FEINT! clear of
#             every gate and mark of its round whichever fake is bitten, and each of its moves in view and off the HUD.
#   lock      locked from the dive's first frame, a dash in flight cut; let go after each ending: the parry, the last
#             round, a Break with a mark up, him beaten, the player beaten, the scene reloaded.
#   break     a Break with a mark up: Broken; no badge, X, gate, figure or card left, no Timer running, the Monte's hold
#             let go, him in view, the hands gone into their portals.
#   release   paused mid-show for 60 frames: no clock, mark, gate or figure moves, and the contact keeps its time.
#   rotation  the order as it ships: Hand Slam, Wild Cards, Portal Monte, then the Hand Slam again.
#   window    his windows (attacks_per_window, the user's of 2026-10-04; three since 2026-10-06): as it ships, that many
#             attacks back to back and then his Recover, twice, with the real him not parried; a Portal Monte with
#             the real him parried opens his Recover at once, the Hand Slam after it waiting for the window; a Break in
#             the first attack of a run starts the count again, the whole run then going before the next Recover; and
#             with attacks_per_window at 1, every attack its own Recover.
#   art       its sheets as shipped, read off disk: the small gate's sequences, the dive, the emerge, the slash and the
#             scatter, their frame sizes and counts; or "placeholders in use".

const Monte := preload("res://Scripts/JoshMonteLayout.gd")
const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const BossBroken := preload("res://Scripts/BossBroken.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const STRIKE_ID := &"josh_monte_strike"

# His park (the gauge spec's home), and where the player stands.
const HOME := Vector2(960, 640)
const STILL := Vector2(700, 760)
const SEED := 20260930
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
const PARRY_LEAD := 4.0 / 60.0
const SHIPPED_ORDER := ["HandSlam", "WildCards", "PortalMonte"]
const PATTERN_ROUNDS := 300
const SLOT_SHARE := Vector2(0.25, 0.42)
const PLACEMENT_GRID := Vector2i(6, 4)
const ARTIST_SPOT := Vector2(900, 620)
const LOGGED := 4
const TIERS := ["parry", "bite", "hit", "timing", "placement", "lock", "break", "release", "rotation", "window", "art"]
const SHIPPED_WINDOW := 3
const WINDOW_STATES := ["HandSlam", "WildCards", "PortalMonte", "Recover", "Broken"]


static func run(t) -> void:
	var tier: String = "parry" if t.tier == "normal" else t.tier
	if not tier in TIERS:
		t.check(false, "tier is one of %s (%s)" % [TIERS, tier])
		return
	if tier == "art":
		_art(t)
		return
	t.fight = "josh"
	if not await t.load_gauged():
		return
	var shipped: Array = t.sm.ATTACK_ORDER.duplicate()
	var shipped_window: int = t.sm.attacks_per_window
	seed(SEED)
	match tier:
		"parry":
			await _parry(t)
		"bite":
			await _bite(t)
		"hit":
			await _hit(t)
		"timing":
			await _timing(t)
		"placement":
			_placement(t)
		"lock":
			await _lock(t)
		"break":
			await _break(t)
		"release":
			await _release(t)
		"rotation":
			await _rotation(t, shipped)
		"window":
			await _window(t, shipped, shipped_window)


#SETTING UP

static func _monte(t) -> Node:
	return t.sm.states["PortalMonte"]


# At his home, idle, his order pinned to the Monte, the player fresh at `start` with every key up, a full bar, no hype
# and no streak; `pattern` pins the real him's burst a round and `rotation` the placement's first turn.
static func _reset(t, start: Vector2, pattern: Array = [], rotation := -1) -> void:
	await t.reset_gauged(HOME)
	t.sm.ATTACK_ORDER.assign(["PortalMonte"])
	t.sm.cycles_started = 0
	var monte := _monte(t)
	monte.forced_pattern.assign(pattern)
	monte.forced_rotation = rotation
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	t.defense._set_stamina(t.defense.max_stamina)
	t.defense.end_parry_streak()
	t.player.get_node("Hype")._set_hype(0.0)
	t.player.playerHealth = 1000
	await t.settle_player(start)
	await t.wait(40)


# When a beat of a round's burst is due, on the Monte's own clock.
static func _due(monte: Node, beat: int, number: int, burst: int) -> float:
	for entry in monte.schedule:
		if entry[1] == beat and entry[2] == number and entry[3] == burst:
			return entry[0]
	return INF


static func _on_beat(at: float, want: float) -> bool:
	return at >= want - SLACK and at < want + FRAME + SLACK


static func _kinds(monte: Node) -> Array:
	return monte.results.map(func(r): return "%s %s" % [r.kind, HitInfo.Result.keys()[r.result]])


static func _hurt_centre(t) -> Vector2:
	return t.area_rect(t.player.hurtBox).get_center()


# A press for a few frames of the fight's own time: a whiff.
static func _tap_parry(t) -> void:
	t.press(KEY_SHIFT)
	await t.wait(3)
	t.release(KEY_SHIFT)


# A press held until its burst has struck: with blocking off the guard is only up while the key is held (PlayerDefense
# guard_holds), so a key let go before the contact parries nothing.
static func _hold_parry(t, monte: Node) -> void:
	var struck: int = monte.results.size()
	t.press(KEY_SHIFT)
	await t.wait_until(func(): return monte.released or monte.results.size() > struck, 30)
	t.release(KEY_SHIFT)


# The bot: a press PARRY_LEAD before every red contact, held through it, never on a fake or a punish.
static func _parry_bot(t, monte: Node) -> Callable:
	var pressed := {}
	return func() -> void:
		if monte.released or not (monte.beat == monte.Beat.SHOW or monte.beat == monte.Beat.DASH) or monte.is_feint or monte.is_punish:
			return
		var key := "%d/%d" % [monte.round, monte.burst_index]
		var contact := _due(monte, monte.Beat.CONTACT, monte.round, monte.burst_index)
		if not pressed.has(key) and monte.clock >= contact - PARRY_LEAD - SLACK:
			pressed[key] = true
			_hold_parry(t, monte)


#ONE MONTE, WATCHED

# One Portal Monte from Idle, every step of it watched until he leaves it. `respond`, if any, is called on every
# physics frame the Monte is running and does whatever the answer is. Five rounds (since 2026-10-06) take about 13 s.
static func _run(t, respond := Callable(), max_frames := 1500) -> Dictionary:
	var sm: Node = t.sm
	var monte := _monte(t)
	var seen := {"states": [], "most_marks": 0, "deals": [], "locks": [], "stagger": {}, "left_at": -1.0, "recover": {},
		"gates_apart": [], "figures": {}, "first_locked": false, "first_dodging": true}
	var watch := func():
		var state := str(sm.current_state.name)
		if seen.states.is_empty() or seen.states[-1] != state:
			seen.states.append(state)
			if state == "Recover" and seen.recover.is_empty():
				seen.recover = {"wait": sm.recover_timer.wait_time, "at": t.boss.ground_position, "shown": t.boss.air.visible and t.boss.shadow.visible, "scale": t.boss.air.scale, "alpha": t.boss.air.modulate.a}
		if sm.current_state != monte:
			return
		seen.left_at = monte.clock
		if seen.locks.is_empty():
			seen.first_locked = t.player.is_action_locked
			seen.first_dodging = t.player.is_dodging
		var locked: bool = t.player.is_action_locked
		if seen.locks.is_empty() or seen.locks[-1][1] != locked:
			seen.locks.append([snappedf(monte.clock, 0.001), locked])
		if monte.beat == monte.Beat.DEAL and (seen.deals.size() <= monte.round):
			seen.deals.append(monte.clock)
		seen.most_marks = maxi(seen.most_marks, _marks_up(t, monte))
		if monte.staggering and seen.stagger.is_empty():
			var gates_closing: bool = range(monte.burst_index + 1, monte.gates.size()).all(func(k): var gate = monte.gates[k]; return not is_instance_valid(gate) or gate.closing)
			seen.stagger = {"clock": monte.clock, "locked": t.player.is_action_locked, "shown": t.boss.air.visible, "closing": gates_closing}
		if monte.beat == monte.Beat.SHOW and monte.clock - monte.beat_start < FRAME - SLACK:
			var waiting: Array = []
			for k in range(monte.burst_index, monte.gates.size()):
				if is_instance_valid(monte.gates[k]):
					waiting.append(_gate_look(monte.gates[k]))
			if not waiting.all(func(look): return look == waiting[0]):
				seen.gates_apart.append([monte.round, monte.burst_index, waiting])
		# By the figure's own clock: each dash starts on the first step past its scheduled time, a different part of a
		# frame late every time.
		if is_instance_valid(monte.figure) and monte.beat == monte.Beat.DASH:
			var step := roundi(monte.figure.travel_clock / FRAME)
			var look := _figure_look(monte.figure)
			var kind := "punish" if monte.is_punish else ("fake" if monte.is_feint else "red")
			var by_step: Dictionary = seen.figures.get(kind, {})
			var list: Array = by_step.get(step, [])
			list.append(look)
			by_step[step] = list
			seen.figures[kind] = by_step
		if respond.is_valid():
			respond.call()
	t.physics_frame.connect(watch)
	sm.start_cycle()
	await t.wait_until(func(): return sm.current_state != monte, max_frames)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	return seen


# The marks up now: a live badge on a small gate, or a fake's X or a punish's glow that isn't fading.
static func _marks_up(t, monte: Node) -> int:
	var count := 0
	for gate in monte.gates:
		if not is_instance_valid(gate):
			continue
		for tell in t.live_tells():
			if tell.boss == gate:
				count += 1
		for child in gate.get_children():
			if str(child.name).begins_with("MonteMark") and not child.is_queued_for_deletion() and child.modulate.a >= 1.0:
				count += 1
	return count


# What a small gate looks like, its mark aside.
static func _gate_look(gate: Node2D) -> String:
	var look := [gate.sequence, gate.step, gate.modulate, gate.art.scale]
	for layer in gate.sprites:
		look.append([gate.sprites[layer].texture, gate.sprites[layer].frame])
	return str(look)


static func _figure_look(figure: Node2D) -> String:
	var sprite: Sprite2D = figure.sprite
	return str([sprite.texture.resource_path, sprite.frame, sprite.modulate, figure.modulate])


#THE PARRY

# As it ships (monte_parry_ends off, the user's answer of 2026-10-04): every round plays out, each parried real him
# bursting into cards, and he comes back out of his gate after the last.
static func _parry(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	var gauge: Node = t.boss.break_gauge
	await _reset(t, STILL, [1, 0, 2])
	gauge.value = 0.0
	var health: int = t.player.playerHealth
	t.log_p("-- as it ships, monte_parry_ends %s: a bot pressing %d frames before each red contact" % [sm.monte_parry_ends, roundi(PARRY_LEAD / FRAME)])
	var seen := await _run(t, _parry_bot(t, monte))
	var kinds := _kinds(monte)
	var reds: Array = monte.results.filter(func(r): return r.kind == &"red")
	var under: Vector2 = Layout.PORTAL_POINTS[monte.dive_side] + Vector2(0.0, Monte.DIVE_UNDER)
	t.log_p("bursts %s; stagger %s; Recover %s; under his gate %s; gauge %.2f; health %d -> %d" % [kinds, seen.stagger, seen.recover, under, gauge.value, health, t.player.playerHealth])
	t.check(not sm.monte_parry_ends, "it ships with every round played out")
	t.check(monte.results.size() == 3 * sm.monte_rounds and reds.size() == sm.monte_rounds and reds.all(func(r): return r.result == HitInfo.Result.PARRIED) and monte.reds_parried == sm.monte_rounds, "every round plays out, its red PARRIED (%s)" % [kinds])
	t.check(seen.stagger.is_empty() and not seen.recover.is_empty() and seen.recover.at.distance_to(under) < 0.5 and seen.recover.shown, "no stagger: he comes back out on the floor under his gate after the last (%s)" % [seen.recover.get("at")])
	t.check(is_equal_approx(seen.recover.get("wait", -1.0), sm.recover_time), "his Recover is recover_time, %.1f s (%.2f)" % [sm.recover_time, seen.recover.get("wait", -1.0)])
	t.check(is_equal_approx(gauge.value, sm.monte_rounds * t.boss.BREAK_READ), "a read up on his gauge a parry (%.2f)" % gauge.value)
	t.check(t.player.playerHealth == health and monte.feints_bitten == 0, "unhurt, and no feint")
	await _parry_ends(t)


# monte_parry_ends on, the knob's other setting: the real him parried ends it there.
static func _parry_ends(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	var gauge: Node = t.boss.break_gauge
	await _reset(t, STILL, [1, 0, 2])
	var kept: bool = sm.monte_parry_ends
	sm.monte_parry_ends = true
	gauge.value = 0.0
	var health: int = t.player.playerHealth
	var centre := _hurt_centre(t)
	t.log_p("-- monte_parry_ends on: a bot pressing %d frames before each red contact" % roundi(PARRY_LEAD / FRAME))
	var seen := await _run(t, _parry_bot(t, monte))
	var kinds := _kinds(monte)
	var contact: float = monte.contact_times[-1] if not monte.contact_times.is_empty() else -1.0
	var ground: Rect2 = t.boss.ground_bounds(0.0)
	var gate_spot: Vector2 = monte.spots[1] if monte.spots.size() > 1 else Vector2.INF
	# The figure's feet end short of the player by where its cut lands, and he is shown there.
	var struck := (centre - Monte.contact_offset(centre.x < gate_spot.x)).round().clamp(ground.position, ground.end)
	var want_spot: Vector2 = (struck + (gate_spot - struck).normalized() * sm.monte_knock).clamp(ground.position, ground.end)
	t.log_p("bursts %s at %s; stagger %s; left the Monte at %.3f; Recover %s; stagger spot %s (wanted %s); gauge %.2f; health %d -> %d" % [
		kinds, monte.contact_times.map(func(x): return snappedf(x, 0.001)), seen.stagger, seen.left_at, seen.recover,
		monte.stagger_spot, want_spot, gauge.value, health, t.player.playerHealth])
	t.check(kinds == ["fake IGNORED", "red PARRIED"] and monte.reds_parried == 1, "round 1's fake passes, and its red is PARRIED (%s)" % [kinds])
	t.check(not seen.stagger.is_empty() and is_equal_approx(seen.stagger.clock, contact) and seen.stagger.closing and not seen.stagger.locked and seen.stagger.shown, "the attack ends on that frame: the rest of the round's gates close, the player is free, and he is in view (%s)" % [seen.stagger])
	t.check(monte.stagger_spot.distance_to(want_spot) < 0.5 and not seen.recover.is_empty() and seen.recover.at.distance_to(monte.stagger_spot) < 0.5, "he is knocked %.0f px back toward his gate, and stands there (%s)" % [sm.monte_knock, seen.recover.get("at")])
	t.check(absf(monte.clock - contact - sm.monte_stagger_time) <= FRAME + SLACK and seen.states.has("Recover"), "his Recover opens %.2f s after the parry, to the frame (%.3f)" % [sm.monte_stagger_time, monte.clock - contact])
	t.check(not seen.recover.is_empty() and is_equal_approx(seen.recover.wait, sm.recover_time + sm.monte_parry_recover_bonus) and seen.recover.shown and is_equal_approx(seen.recover.alpha, 1.0), "lasting recover_time + %.1f s, %.2f s, him whole and in view" % [sm.monte_parry_recover_bonus, seen.recover.get("wait", -1.0)])
	t.check(is_equal_approx(gauge.value, t.boss.BREAK_READ), "one read up on his gauge (%.2f)" % gauge.value)
	t.check(t.player.playerHealth == health and monte.feints_bitten == 0, "unhurt, and no feint")
	sm.monte_parry_ends = kept


#BITING A FAKE

static func _bite(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	var gauge: Node = t.boss.break_gauge
	t.log_p("-- a press on round 1's first fake")
	await _reset(t, STILL, [2, 0, 0])
	t.hold_break_gauge(t.boss)
	var health: int = t.player.playerHealth
	var bit := {"stamina_at": -1.0, "stamina_after": -1.0, "streak_before": -1, "streak_after": -1, "word": false,
		"word_at": Vector2.INF, "word_want": Vector2.ZERO, "word_cover": -1.0}
	var bite := func() -> void:
		if bit.stamina_at >= 0.0 or monte.round != 0 or monte.burst_index != 0 or monte.beat != monte.Beat.SHOW:
			return
		if monte.clock - monte.beat_start < 0.15:
			return
		t.defense._set_stamina(t.defense.max_stamina)
		t.defense.parry_streak = 3
		bit.streak_before = t.defense.parry_streak
		bit.stamina_at = t.defense.stamina
		t.press(KEY_SHIFT)
	var watch_after := func() -> void:
		if bit.stamina_at >= 0.0 and bit.stamina_after < 0.0 and monte.beat == monte.Beat.SHOW and monte.burst_index == 1:
			t.release(KEY_SHIFT)
			bit.stamina_after = t.defense.stamina
			bit.streak_after = t.defense.parry_streak
			for word in t.boss.hud_layer.get_children():
				if word is Label and word.text == "FEINT!":
					bit.word = true
					bit.word_at = word.position + word.size / 2.0
					bit.word_want = Monte.word_centre(monte.spots, 0)
					bit.word_cover = Monte.word_cover(bit.word_at, monte.spots)
	var respond := func() -> void:
		bite.call()
		watch_after.call()
	t.physics_frame.connect(respond)
	sm.start_cycle()
	await t.wait_until(func(): return monte.results.size() >= 2 or sm.current_state != monte, 300)
	t.physics_frame.disconnect(respond)
	var kinds := _kinds(monte)
	t.log_p("bursts %s; stamina %.1f -> %.1f past the window; streak %d -> %d; FEINT! up %s; health %d -> %d" % [kinds, bit.stamina_at, bit.stamina_after, bit.streak_before, bit.streak_after, bit.word, health, t.player.playerHealth])
	t.check(monte.feints_bitten == 1 and bit.word, "FEINT! (%d)" % monte.feints_bitten)
	t.check(bit.word_at.is_equal_approx(bit.word_want) and bit.word_cover == 0.0, "on %s, where it clears the round's gates and marks (%s wanted, covering %.0f px2)" % [bit.word_at, bit.word_want, bit.word_cover])
	t.check(is_equal_approx(bit.stamina_at - bit.stamina_after, sm.monte_feint_stamina), "%.0f stamina off, and no whiff on top (%.1f -> %.1f)" % [sm.monte_feint_stamina, bit.stamina_at, bit.stamina_after])
	t.check(bit.streak_before == 3 and bit.streak_after == 0, "the streak ended (%d -> %d)" % [bit.streak_before, bit.streak_after])
	var punish_damage: int = AttackCatalog.get_attack(&"josh_monte_punish").damage
	t.check(kinds.size() >= 2 and kinds[1] == "punish HIT" and monte.punishes_landed == 1 and health - t.player.playerHealth == punish_damage, "the next burst is a punish, and it lands for its %d half-hearts (%s, %d)" % [punish_damage, kinds, health - t.player.playerHealth])

	t.log_p("-- a press on the attack's very last burst, a fake")
	await _reset(t, STILL, [0, 0, 0])
	gauge.value = 75.0
	var last := {"before": -1.0, "after": -1.0}
	var bite_last := func() -> void:
		if last.before >= 0.0:
			if last.after < 0.0 and monte.beat != monte.Beat.SHOW:
				last.after = gauge.value
				t.release(KEY_SHIFT)
			return
		if monte.round == sm.monte_rounds - 1 and monte.burst_index == 2 and monte.beat == monte.Beat.SHOW and monte.clock - monte.beat_start >= 0.15:
			last.before = gauge.value
			t.press(KEY_SHIFT)
	var seen := await _run(t, bite_last)
	var kinds_last := _kinds(monte)
	t.log_p("bursts %s; the gauge %.2f -> %.2f at the bite; punishes %d; states %s" % [kinds_last, last.before, last.after, monte.punishes_landed, seen.states])
	t.check(monte.feints_bitten == 1 and is_equal_approx(last.before - last.after, gauge.hit_loss), "one read off his gauge for it (%.2f -> %.2f)" % [last.before, last.after])
	t.check(monte.punishes_landed == 0 and not kinds_last.has("punish HIT") and seen.states.has("Recover"), "and no punish: he comes back out, and his Recover")


#DOING NOTHING

static func _hit(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	var gauge: Node = t.boss.break_gauge
	await _reset(t, STILL, [0, 1, 2])
	gauge.value = 50.0
	var health: int = t.player.playerHealth
	var iframed := {"done": false, "at": -1.0}
	# Round 2's red lands with the player's i-frames running.
	var iframe := func() -> void:
		if iframed.done or monte.round != 1 or monte.burst_index != 1 or monte.beat != monte.Beat.DASH:
			return
		iframed.done = true
		iframed.at = monte.clock
		t.player.is_invincible = true
		t.player.invincibility_timer.start()
	t.log_p("-- nothing pressed")
	var seen := await _run(t, iframe)
	var kinds := _kinds(monte)
	var reds: Array = monte.results.filter(func(r): return r.kind == &"red")
	var fakes: Array = monte.results.filter(func(r): return r.kind == &"fake")
	var under: Vector2 = Layout.PORTAL_POINTS[monte.dive_side] + Vector2(0.0, Monte.DIVE_UNDER)
	t.log_p("bursts %s; i-frames up at %.3f; Recover %s; under his gate %s; gauge 50 -> %.2f; health %d -> %d" % [kinds, iframed.at, seen.recover, under, gauge.value, health, t.player.playerHealth])
	t.check(reds.size() == sm.monte_rounds and reds.all(func(r): return r.result == HitInfo.Result.HIT) and iframed.done, "every red HITs, the one landing in the i-frames too (%s)" % [kinds])
	t.check(fakes.size() == 2 * sm.monte_rounds and fakes.all(func(r): return r.result == HitInfo.Result.IGNORED), "the fakes touch nothing")
	var strike_damage: int = AttackCatalog.get_attack(STRIKE_ID).damage
	t.check(health - t.player.playerHealth == sm.monte_rounds * strike_damage, "%d hits of %d half-hearts (%d)" % [sm.monte_rounds, strike_damage, health - t.player.playerHealth])
	t.check(not seen.recover.is_empty() and seen.recover.at.distance_to(under) < 0.5 and seen.recover.shown, "he comes back out on the floor under his gate (%s)" % [seen.recover.get("at")])
	t.check(not seen.recover.is_empty() and is_equal_approx(seen.recover.wait, sm.recover_time), "his Recover is recover_time, %.1f s (%.2f)" % [sm.recover_time, seen.recover.get("wait", -1.0)])
	t.check(is_equal_approx(50.0 - gauge.value, sm.monte_rounds * gauge.hit_loss), "a read off his gauge a hit (%.2f)" % gauge.value)


#THE TIMING

static func _timing(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	await _reset(t, STILL, [0, 1, 2])
	t.hold_break_gauge(t.boss)
	t.log_p("-- a whole Monte, nothing pressed")
	var seen := await _run(t)
	var cadence: float = sm.monte_cadence()
	var reach: float = sm.monte_show + sm.monte_dash
	var off_contacts: Array = []
	for k in mini(monte.mark_times.size(), monte.contact_times.size()):
		if absf(monte.contact_times[k] - monte.mark_times[k] - reach) > FRAME + SLACK:
			off_contacts.append([k, snappedf(monte.contact_times[k] - monte.mark_times[k], 0.001)])
	var off_cadence: Array = []
	for k in range(1, monte.mark_times.size()):
		if k % 3 != 0 and absf(monte.mark_times[k] - monte.mark_times[k - 1] - cadence) > FRAME + SLACK:
			off_cadence.append([k, snappedf(monte.mark_times[k] - monte.mark_times[k - 1], 0.001)])
	var round_length: float = sm.monte_deal_time + sm.monte_open_time + 3.0 * cadence
	var round_wants: Array = []
	for r in sm.monte_rounds:
		round_wants.append(sm.monte_dive_time + r * round_length)
	var rounds_on_beat: bool = seen.deals.size() == sm.monte_rounds
	for r in mini(seen.deals.size(), round_wants.size()):
		rounds_on_beat = rounds_on_beat and _on_beat(seen.deals[r], round_wants[r])
	var red_looks: Dictionary = seen.figures.get("red", {})
	var fake_looks: Dictionary = seen.figures.get("fake", {})
	var unlike: Array = []
	for step in red_looks:
		for look in fake_looks.get(step, []):
			if look != red_looks[step][0]:
				unlike.append([step, red_looks[step][0], look])
	t.log_p("marks at %s; contacts at %s; rounds at %s (want %s); most marks up at once %d; gates apart %s; figures compared on %d dash steps, unlike %s" % [
		monte.mark_times.map(func(x): return snappedf(x, 0.001)), monte.contact_times.map(func(x): return snappedf(x, 0.001)),
		seen.deals.map(func(x): return snappedf(x, 0.001)), round_wants, seen.most_marks, seen.gates_apart.slice(0, LOGGED),
		red_looks.size(), unlike.slice(0, LOGGED)])
	t.check(seen.most_marks == 1, "one mark up at a time (%d)" % seen.most_marks)
	t.check(monte.contact_times.size() == 3 * sm.monte_rounds and off_contacts.is_empty(), "each contact %.2f s after its mark, to the frame (%s)" % [reach, off_contacts])
	t.check(monte.mark_times.size() == 3 * sm.monte_rounds and off_cadence.is_empty(), "each mark %.2f s after the one before in its round (%s)" % [cadence, off_cadence])
	t.check(rounds_on_beat, "the rounds start at %s s, to the frame (%s)" % [round_wants, seen.deals.map(func(x): return snappedf(x, 0.001))])
	t.check(seen.gates_apart.is_empty(), "the gates yet to burst all drawn alike as each mark comes up (%s)" % [seen.gates_apart.slice(0, LOGGED)])
	t.check(not red_looks.is_empty() and not fake_looks.is_empty() and unlike.is_empty(), "the real him drawn as a fake is, frame for frame, until its contact (%s)" % [unlike.slice(0, LOGGED)])

	t.log_p("-- a whiff just before a red's mark, then the press for it")
	await _reset(t, STILL, [1, 0, 2])
	t.hold_break_gauge(t.boss)
	var plan := {"whiffed": -1.0, "pressed": -1.0}
	var respond := func() -> void:
		if plan.whiffed < 0.0 and monte.clock >= _due(monte, monte.Beat.SHOW, 0, 1) - 0.02 - SLACK:
			plan.whiffed = t.defense.clock
			_tap_parry(t)
		elif plan.pressed < 0.0 and plan.whiffed >= 0.0 and monte.clock >= _due(monte, monte.Beat.CONTACT, 0, 1) - PARRY_LEAD - SLACK:
			plan.pressed = t.defense.clock
			_hold_parry(t, monte)
	await _run(t, respond)
	var gap: float = plan.pressed - plan.whiffed
	t.log_p("whiffed just before the mark, pressed %.4f s after the whiff (the mash lockout is %.2f s): %s" % [gap, t.defense.parry_mash_lockout, _kinds(monte)])
	t.check(gap < t.defense.parry_mash_lockout and _kinds(monte).slice(0, 2) == ["fake IGNORED", "red PARRIED"], "the red's mark re-arms the parry, so the whiff before it doesn't lock it out (%s)" % [_kinds(monte)])

	var counts := [0, 0, 0]
	for slot in monte.deal_pattern(PATTERN_ROUNDS):
		counts[slot] += 1
	var shares: Array = counts.map(func(c): return snappedf(float(c) / PATTERN_ROUNDS, 0.001))
	t.log_p("over %d seeded rounds the real him was burst 1, 2, 3 %s of the time" % [PATTERN_ROUNDS, shares])
	t.check(shares.all(func(s): return s >= SLOT_SHARE.x and s <= SLOT_SHARE.y), "each burst the real him %.0f-%.0f%% of the time (%s)" % [SLOT_SHARE.x * 100.0, SLOT_SHARE.y * 100.0, shares])


#WHERE THE GATES OPEN

static func _placement(t) -> void:
	var sm: Node = t.sm
	var area: Rect2 = BossBroken.PLAYER_AREA
	var spots: Array[Vector2] = [area.position, Vector2(area.end.x, area.position.y), Vector2(area.position.x, area.end.y), area.end]
	for k in 3:
		var s := (k + 1) / 4.0
		spots.append(Vector2(lerpf(area.position.x, area.end.x, s), area.position.y))
		spots.append(Vector2(lerpf(area.position.x, area.end.x, s), area.end.y))
		spots.append(Vector2(area.position.x, lerpf(area.position.y, area.end.y, s)))
		spots.append(Vector2(area.end.x, lerpf(area.position.y, area.end.y, s)))
	for i in PLACEMENT_GRID.x:
		for j in PLACEMENT_GRID.y:
			spots.append(Vector2(lerpf(area.position.x, area.end.x, (i + 0.5) / PLACEMENT_GRID.x), lerpf(area.position.y, area.end.y, (j + 0.5) / PLACEMENT_GRID.y)))
	# Where the art pass saw two gates open on the resting hands.
	spots.append(ARTIST_SPOT)
	var bad: Array = []
	var not_turned: Array = []
	var on_hands: Array = []
	var hows := {}
	var clear := 0
	var clear_before := 0
	var over_before: Array = []
	var over: Array = []
	var word_on: Array = []
	var word_moved := 0
	for p in spots:
		var first_step := randi() % Monte.PLACE_TURNS
		var before: Dictionary = Monte.place(p, {}, sm.monte_radius, sm.monte_min_radius, sm.ROPES, first_step, false)
		if not Monte.marks_owned(before.spots):
			over_before.append(p)
		if before.clear:
			clear_before += 1
		var first: Dictionary = Monte.place(p, {}, sm.monte_radius, sm.monte_min_radius, sm.ROPES, first_step)
		hows[first.how] = hows.get(first.how, 0) + 1
		if first.clear:
			clear += 1
		var problem := _placement_problem(first.spots, p, sm)
		if problem != "" or first.how == &"drawn_in":
			bad.append([p, first.how, problem])
		for spot in first.spots:
			if Monte.resting_hands().any(func(hand: Rect2) -> bool: return hand.intersects(Monte.gate_rect(spot))):
				on_hands.append([p, spot])
		var again: Dictionary = Monte.place(p, first, sm.monte_radius, sm.monte_min_radius, sm.ROPES, first_step)
		if not Monte.turned_enough(again.how, again.turn, first) and _any_turned(p, first, sm, again.clear, again.owned):
			not_turned.append([p, first.how, snappedf(first.turn, 0.1), again.how, snappedf(again.turn, 0.1)])
		for dealt: Dictionary in [first, again]:
			if not Monte.marks_owned(dealt.spots):
				over.append([p, dealt.how, dealt.spots])
			for k in 3:
				var at := Monte.word_centre(dealt.spots, k)
				if at != Monte.WORD.centre:
					word_moved += 1
				if Monte.word_cover(at, dealt.spots) > 0.0:
					word_on.append([p, k, at])
	var n := spots.size()
	t.log_p("%d player spots: shapes %s; clear of the big gates too %d (%d before marks were kept off the other gates)" % [n, hows, clear, clear_before])
	t.log_p("a mark over another gate: before %d of %d (%.0f%%), now %d of %d deals and re-deals; FEINT! moved off his spot %d of %d" % [over_before.size(), n, 100.0 * over_before.size() / n, over.size(), 2 * n, word_moved, 6 * n])
	t.check(spots.size() == 41 and bad.is_empty(), "from every spot three gates each %.0f px or more from the player, %.0f apart, their rect and mark in view and clear of the HUD, never drawn in (%s)" % [sm.monte_min_radius, Monte.PLACE_MIN_GAP, bad.slice(0, LOGGED)])
	t.check(on_hands.is_empty(), "none of them on a hand resting at a big gate, from %s too (%s)" % [ARTIST_SPOT, on_hands.slice(0, LOGGED)])
	t.check(not_turned.is_empty(), "a re-deal turned %.0f degrees off the last whenever one fits (%s)" % [Monte.REDEAL_MIN_TURN, not_turned.slice(0, LOGGED)])
	t.check(not over_before.is_empty() and over.is_empty(), "no mark over another gate, on a deal or a re-deal, where %d of %d had one before (%s)" % [over_before.size(), n, over.slice(0, LOGGED)])
	t.check(word_on.is_empty(), "FEINT! clear of every gate of its round and its mark, whichever fake is bitten (%s)" % [word_on.slice(0, LOGGED)])
	var off_view: Array = []
	for side in [Monte.WORD.centre.x - 100.0, Monte.WORD.centre.x + 100.0]:
		var one: Array[Vector2] = [Vector2(side, 500.0)]
		for at in Monte.word_spots(one, 0):
			var box := Monte.word_box(at)
			if not JoshArtLayout.VIEW_RECT.grow(-Monte.PLACE_VIEW_MARGIN).encloses(box) or JoshArtLayout.HUD_KEEP_OUT.any(func(block: Rect2) -> bool: return block.grow(JoshArtLayout.HUD_CLEARANCE).intersects(box)):
				off_view.append(at)
	t.check(off_view.is_empty(), "each of FEINT!'s moves, either way, in view and clear of the HUD (%s)" % [off_view])


# What is wrong with three gates round a player at `p`, or "".
static func _placement_problem(gates: Array, p: Vector2, sm: Node) -> String:
	if gates.size() != 3:
		return "%d gates" % gates.size()
	for a in 3:
		if not Monte.gate_fits(gates[a], p, sm.monte_min_radius, sm.ROPES):
			return "gate %s doesn't fit" % gates[a]
		for b in range(a + 1, 3):
			if gates[a].distance_to(gates[b]) < Monte.PLACE_MIN_GAP:
				return "gates %s and %s %.0f apart" % [gates[a], gates[b], gates[a].distance_to(gates[b])]
	return ""


# Whether any shape, turned far enough off `prev`, fits round `p` - and with `clear`, clear of the big gates and their
# hands, and with `owned`, every mark clear of the other gates, which placing puts first: a brute-force search of every
# shape, reach and turn.
static func _any_turned(p: Vector2, prev: Dictionary, sm: Node, clear: bool, owned := false) -> bool:
	var middle: Vector2 = sm.ROPES.get_center()
	var toward := 90.0 if p.distance_to(middle) < Monte.FAN_MIDDLE_RADIUS else rad_to_deg((middle - p).angle())
	for shape in Monte.PLACE_SHAPE_ORDER:
		for step in Monte.PLACE_RADIUS_STEPS:
			for i in Monte.PLACE_TURNS:
				var turn := fposmod(i * Monte.PLACE_TURN_STEP if shape == &"ring" else toward + (i - 12) * Monte.PLACE_TURN_STEP, 360.0)
				if not Monte.turned_enough(shape, turn, prev):
					continue
				var gates := Monte.shape_spots(p, shape, turn, sm.monte_radius + step)
				if _placement_problem(gates, p, sm) == "" and (not clear or gates.all(Monte.clear_of_stage)) and (not owned or Monte.marks_owned(gates)):
					return true
	return false


#THE LOCK

static func _lock(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)

	t.log_p("-- a dash in flight as he dives, then the parry")
	await _reset(t, STILL, [0, 1, 2])
	t.hold_break_gauge(t.boss)
	await t.dash_ready()
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 20)
	var dashing: bool = t.player.is_dodging
	var seen := await _run(t, _parry_bot(t, monte))
	t.release(KEY_RIGHT)
	t.log_p("dashing as it started %s; locked on its first frame %s, still dodging %s; locks %s; bursts %s" % [dashing, seen.first_locked, seen.first_dodging, seen.locks, _kinds(monte)])
	t.check(dashing and seen.first_locked and not seen.first_dodging, "locked from the dive's first frame, and the dash in flight is cut")
	t.check(_kinds(monte).has("red PARRIED") and not t.player.is_action_locked, "let go at the parry")

	t.log_p("-- through the last round")
	await _reset(t, STILL, [0, 1, 2])
	t.hold_break_gauge(t.boss)
	seen = await _run(t)
	t.check(seen.states.has("Recover") and not t.player.is_action_locked and monte.lock_times.size() == 2, "let go after the last round (%s)" % [monte.lock_times])

	t.log_p("-- a Break with a mark up")
	await _reset(t, STILL, [0, 1, 2])
	sm.start_cycle()
	await t.wait_until(func(): return monte.beat == monte.Beat.SHOW and monte.burst_index == 1, 300)
	await t.force_break()
	var broke: bool = await t.wait_until(func(): return str(sm.current_state.name) == "Broken", 30)
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 180)
	t.check(broke and driven and not monte.locked, "let go at a Break with a mark up")

	t.log_p("-- him beaten with a mark up")
	await _reset(t, STILL, [0, 1, 2])
	sm.start_cycle()
	await t.wait_until(func(): return monte.beat == monte.Beat.SHOW, 300)
	sm.enter_defeated()
	await t.wait(2)
	t.check(not t.player.is_action_locked and monte.released, "let go when he is beaten")

	t.log_p("-- the player beaten with a mark up")
	await t.load_gauged()
	monte = _monte(t)
	await _reset(t, STILL, [0, 1, 2])
	t.sm.start_cycle()
	await t.wait_until(func(): return monte.beat == monte.Beat.SHOW, 300)
	t.boss.on_player_defeated()
	await t.wait(2)
	t.check(not t.player.is_action_locked and monte.released, "let go when the player is beaten")

	t.log_p("-- the scene reloaded with a mark up")
	await t.load_gauged()
	monte = _monte(t)
	await _reset(t, STILL, [0, 1, 2])
	t.sm.start_cycle()
	await t.wait_until(func(): return monte.beat == monte.Beat.SHOW, 300)
	var old_scene: Node = t.current_scene
	var reloaded: bool = await t.load_gauged()
	await t.wait(10)
	t.check(reloaded and not is_instance_valid(old_scene) and not t.player.is_action_locked, "reloaded mid-Monte, the new fight's player is free (its script errors are the runner's to count)")


#HIS BREAK

static func _break(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	var rig: Node = sm.hands
	await _reset(t, STILL, [0, 1, 2])
	sm.start_cycle()
	var reached: bool = await t.wait_until(func(): return monte.beat == monte.Beat.SHOW and monte.burst_index == 1 and monte.clock - monte.beat_start >= 0.1, 300)
	var had: Array = [monte.gates.filter(func(g): return is_instance_valid(g)).size(), _marks_up(t, monte)]
	await t.force_break()
	var broke: bool = await t.wait_until(func(): return str(sm.current_state.name) == "Broken", 30)
	await t.wait(2)
	var left: Array = t.live_hazards()
	var tells: Array = t.live_tells()
	var marks: Array = t.current_scene.find_children("MonteMark*", "", true, false).filter(func(n): return not n.is_queued_for_deletion())
	var running: Array = t.break_timers().filter(func(timer): return not timer.is_stopped())
	var shown: bool = t.boss.air.visible and t.boss.shadow.visible and is_equal_approx(t.boss.air.modulate.a, 1.0) and t.boss.air.scale == Vector2.ONE
	var gone: bool = await t.wait_until(func(): return Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and hand.retracted and not hand.visible), 60)
	var free: bool = await t.wait_until(func(): return not t.player.is_action_locked, 180)
	t.log_p("reached %s with %s gates and marks; now %s; hazards %s, tells %d, marks %d, timers %s; him shown %s; hands gone %s; player free %s" % [reached, had, sm.current_state.name, left.map(func(h): return h.name), tells.size(), marks.size(), running.map(func(timer): return timer.name), shown, gone, free])
	t.check(reached and broke, "Broken with a mark up")
	t.check(left.is_empty() and tells.is_empty() and marks.is_empty() and running.is_empty(), "no badge, X, gate, figure or card left, and no Timer running")
	t.check(free and not monte.locked and shown, "the Monte's hold let go, and him in view")
	t.check(gone, "the hands gone into their portals")


#PAUSED

static func _release(t) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	await _reset(t, STILL, [1, 0, 2])
	t.hold_break_gauge(t.boss)
	sm.start_cycle()
	await t.wait_until(func(): return monte.beat == monte.Beat.SHOW and monte.burst_index == 1 and monte.clock - monte.beat_start >= 0.15, 300)
	var pause: Node = t.pause_menu()
	await t.tap_pause()
	var still := func() -> String:
		var badge: Array = t.live_tells().filter(func(tell): return monte.gates.has(tell.boss)).map(func(tell): return [tell.global_position, tell.clock, tell.modulate])
		return str({"clock": monte.clock, "badge": badge,
			"gates": monte.gates.map(func(g): return [g.sequence, g.step, g.clock, g.art.scale] if is_instance_valid(g) else []),
			"figure": [monte.figure.global_position, monte.figure.sprite.frame] if is_instance_valid(monte.figure) else []})
	var at_pause: String = still.call()
	await t.wait(60)
	var after: String = still.call()
	if at_pause != after:
		t.log_p("at the pause %s; 60 frames on %s" % [at_pause, after])
	t.check(pause.is_open() and t.paused and at_pause == after and at_pause.contains("badge"), "paused, nothing of it moves for 60 frames: no clock, mark, gate or figure")
	await t.tap_pause()
	var contact := _due(monte, monte.Beat.CONTACT, 0, 1)
	await t.wait_until(func(): return monte.contact_times.size() >= 2 or sm.current_state != monte, 120)
	var at: float = monte.contact_times[1] if monte.contact_times.size() >= 2 else -1.0
	t.log_p("paused mid-show; the contact, due at %.3f s, came at %.3f s" % [contact, at])
	t.check(_on_beat(at, contact), "and after the resume the contact keeps its time")


#THE ORDER

static func _rotation(t, shipped: Array) -> void:
	var sm: Node = t.sm
	await _reset(t, STILL)
	t.hold_break_gauge(t.boss)
	sm.ATTACK_ORDER.assign(shipped)
	sm.cycles_started = 0
	var attacks: Array = []
	var watch := func():
		var state := str(sm.current_state.name)
		if state in ["HandSlam", "WildCards", "PortalMonte"] and (attacks.is_empty() or attacks[-1] != state):
			attacks.append(state)
	t.physics_frame.connect(watch)
	sm.start_cycle()
	await t.wait_until(func(): return attacks.size() >= 4, 3600)
	t.physics_frame.disconnect(watch)
	t.log_p("shipped order %s; attacks in turn %s" % [shipped, attacks])
	t.check(shipped == SHIPPED_ORDER, "his order as it ships is %s (%s)" % [SHIPPED_ORDER, shipped])
	t.check(attacks.slice(0, 4) == ["HandSlam", "WildCards", "PortalMonte", "HandSlam"], "Hand Slam, Wild Cards, Portal Monte, then the Hand Slam again (%s)" % [attacks])


#HIS WINDOWS

static func _window(t, shipped: Array, shipped_window: int) -> void:
	var sm: Node = t.sm
	var monte := _monte(t)
	t.check(shipped_window == SHIPPED_WINDOW, "%d attacks a window as he ships (%d)" % [SHIPPED_WINDOW, shipped_window])

	t.log_p("-- as he ships, nothing answered")
	await _window_reset(t, shipped, shipped_window, true)
	var want_plain := _windows_of(shipped, 0, shipped_window, 2)
	var plain := await _window_run(t, want_plain.size())
	t.log_p("states %s; Recover waits %s" % [plain.states, plain.waits])
	t.check(plain.states.slice(0, want_plain.size()) == want_plain, "%d attacks back to back, then his Recover: %s (%s)" % [shipped_window, want_plain, plain.states])
	t.check(plain.waits.size() >= 2 and plain.waits.all(func(w): return is_equal_approx(w, sm.recover_time)), "each Recover lasting recover_time, %.1f s (%s)" % [sm.recover_time, plain.waits])

	t.log_p("-- a Portal Monte with the real him parried, the Hand Slam after it")
	await _window_reset(t, ["PortalMonte", "HandSlam"], shipped_window, true)
	var earned := await _window_run(t, 3, _parry_bot(t, monte))
	t.log_p("states %s; reds parried %d" % [earned.states, monte.reds_parried])
	t.check(monte.reds_parried > 0 and earned.states.slice(0, 3) == ["PortalMonte", "Recover", "HandSlam"], "the parried Monte opens his Recover at once, and the Hand Slam waits for it (%s)" % [earned.states])

	t.log_p("-- a Break in the first attack of a pair")
	await _window_reset(t, ["WildCards", "HandSlam"], shipped_window, false)
	var wild: Node = sm.states["WildCards"]
	var broke := {"done": false}
	var break_it := func() -> void:
		if not broke.done and sm.current_state == wild and wild.clones.size() >= 2:
			broke.done = true
			t.force_break()
	var want_break: Array = ["WildCards", "Broken"] + _windows_of(["WildCards", "HandSlam"], 1, shipped_window, 1)
	var after_break := await _window_run(t, want_break.size(), break_it)
	t.log_p("states %s" % [after_break.states])
	t.check(after_break.states.slice(0, want_break.size()) == want_break, "the Break starts the count again: %d attacks after it, then his Recover (%s)" % [shipped_window, after_break.states])

	t.log_p("-- attacks_per_window at 1")
	await _window_reset(t, ["WildCards", "HandSlam"], 1, true)
	var single := await _window_run(t, 4)
	t.log_p("states %s" % [single.states])
	t.check(single.states.slice(0, 4) == ["WildCards", "Recover", "HandSlam", "Recover"], "every attack its own Recover (%s)" % [single.states])


# `windows` windows' worth of his states with nothing parried: `window` attacks in `order` from `first`, then Recover.
static func _windows_of(order: Array, first: int, window: int, windows: int) -> Array:
	var states: Array = []
	var next := first
	for w in windows:
		for k in window:
			states.append(order[next % order.size()])
			next += 1
		states.append("Recover")
	return states


static func _window_reset(t, order: Array, window: int, hold_gauge: bool) -> void:
	await _reset(t, STILL)
	if hold_gauge:
		t.hold_break_gauge(t.boss)
	t.sm.ATTACK_ORDER.assign(order)
	t.sm.cycles_started = 0
	t.sm.attacks_per_window = window
	t.sm.attacks_since_window = 0


# His states from a start_cycle() until `count` of WINDOW_STATES have come, each Recover's wait, and `respond` called
# every physics frame meanwhile.
static func _window_run(t, count: int, respond := Callable()) -> Dictionary:
	var sm: Node = t.sm
	var seen := {"states": [], "waits": []}
	var watch := func():
		var state := str(sm.current_state.name)
		if state in WINDOW_STATES and (seen.states.is_empty() or seen.states[-1] != state):
			seen.states.append(state)
			if state == "Recover":
				seen.waits.append(sm.recover_timer.wait_time)
		if respond.is_valid():
			respond.call()
	t.physics_frame.connect(watch)
	sm.start_cycle()
	await t.wait_until(func(): return seen.states.size() >= count, 7200)
	t.physics_frame.disconnect(watch)
	sm.on_child_transition(sm.current_state, "Idle")
	t.stop_boss_timers()
	await t.wait(2)
	return seen


#THE ART

# Its sheets as shipped, read off disk, imported or not: the game plays each once it is imported.
static func _art(t) -> void:
	var image := func(path: String) -> Image:
		return Image.load_from_file(ProjectSettings.globalize_path(path))
	t.log_p("-- the Portal Monte's art, as shipped")
	var small_in: bool = Monte.SMALL_PORTAL_REQUIRED.all(func(sequence): return Monte.SMALL_PORTAL_LAYERS.all(func(layer): return FileAccess.file_exists(Monte.small_portal_sheet(sequence, layer))))
	if not small_in:
		t.log_p("the small gates: placeholders in use")
	else:
		var bad: Array = []
		for sequence in Monte.SMALL_PORTAL_SEQUENCES:
			for layer in Monte.SMALL_PORTAL_LAYERS:
				var path := Monte.small_portal_sheet(sequence, layer)
				if not FileAccess.file_exists(path):
					continue
				var img: Image = image.call(path)
				var frames: int = Monte.SMALL_PORTAL_SEQUENCES[sequence].size()
				if img.get_width() != frames * int(Monte.SMALL_PORTAL.frame.x) or img.get_height() != int(Monte.SMALL_PORTAL.frame.y):
					bad.append([path.get_file(), img.get_size(), frames])
		t.check(bad.is_empty(), "every small gate sheet %s frames, as many as SMALL_PORTAL_SEQUENCES has (%s)" % [Monte.SMALL_PORTAL.frame, bad])
	for anim_name in [&"dive", &"emerge"]:
		var spec: Dictionary = JoshArtLayout.FINAL_ANIMS[anim_name]
		if not FileAccess.file_exists(spec.sheet):
			t.log_p("%s: placeholder in use" % anim_name)
			continue
		var img: Image = image.call(spec.sheet)
		var most: int = spec.frames.max() + 1
		var total := 0.0
		for i in spec.frames.size():
			total += spec.times[mini(i, spec.times.size() - 1)]
		t.check(img.get_height() == int(JoshArtLayout.FRAME_SIZE.y) and img.get_width() == most * int(JoshArtLayout.FRAME_SIZE.x) and is_equal_approx(total, JoshArtLayout.DIVE_TIME), "%s: %d frames of 80x80, %.2f s in all (%s)" % [spec.sheet.get_file(), most, total, img.get_size()])
	for sheet in [{"spec": Monte.SLASH, "count": Monte.SLASH.times.size()}, {"spec": Monte.SCATTER, "count": Monte.SCATTER.frame_times.size()}]:
		var spec: Dictionary = sheet.spec
		if not FileAccess.file_exists(spec.texture):
			t.log_p("%s: placeholder in use" % spec.texture.get_file())
			continue
		var img: Image = image.call(spec.texture)
		t.check(img.get_height() == int(spec.frame.y) and img.get_width() == sheet.count * int(spec.frame.x), "%s: %d frames of %s (%s)" % [spec.texture.get_file(), sheet.count, spec.frame, img.get_size()])
