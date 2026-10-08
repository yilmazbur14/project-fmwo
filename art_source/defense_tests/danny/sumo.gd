extends RefCounted

# danny_sumo (coder C): Danny's 0 HP (DannyBossSumo) in his fight. REAL TIME (--max-fps 60): the mash counts
# a press only 0.03 real seconds after the last (MashInput), which --fixed-fps would starve. He is put in his nap
# and knocked out by a punch at 1 HP, and the cut is watched through, its line read the way a player reads it,
# or held past, into the tug.
#   win    a bot at 7 presses a second, the target: the tug won when the model wins it, him skidding whenever the
#          rope is the player's way outside his surges and leaning in with his end of the meter lit through every
#          surge; him out through the top gate, the gates shut behind him, `defeated`, one player_won outro,
#          Defeated.
#   loss   no presses: the tug lost when the model loses it, and a pause mid-mash holds the rope; the player out
#          through the bottom gate, their sprite hidden under the prop, one player_lost outro, Victory.
#   skip   the clinch a watched cut lands on, then a hold in the stir, the leap, the line and the walk: each lands
#          on the same clinch.
#   table  the model's table, 0 to 11 presses a second, against the user's asks (2026-09-27): 5 a second loses,
#          7 wins in 8-11 s, no rate sprints it, the rope moves the same wherever it stands, every surge takes
#          ground back from the target and from flat out, a stop that loses the lead is won back and so is a
#          deep deficit; then bots at 5 a second and at 7 with a second's stop matching it live.
# Every run that watches the cut also checks its beats against the plan's times.

const BODY := "Arena/DannyBossScene/DannyBossCharacterBody"
const TUG := "res://Scripts/DannyBossTugOfWar.gd"
const SCREEN_VIEW := "res://Scripts/ScreenView.gd"
const HIT_STOP := "res://Scripts/HitStop.gd"
const FIGHT_FREEZE := "res://Scripts/FightFreeze.gd"
const START := Vector2(960, 800)
# A live bout's result time against the model's: a press lands a frame after its time, and real frames jitter.
const TIME_SLACK := 0.25
const BEAT_SLACK := 3.0 / 60.0
const PLAN_BEATS := {&"false_victory": 1.8, &"stir": 0.5, &"leap": 0.9, &"rise": 0.49, &"call": 0.8, &"clinch": 0.3}
# Frames Escape is held for a skip: past BossEntrance.SKIP_HOLD, 0.4 real seconds.
const ESCAPE_HOLD := 32
# The tug's target rate, and the stop the slacking bot takes from it midway.
const TARGET := 7.0
const SLACK_AT := 4.0
const SLACK_FOR := 1.0


static func run(t) -> void:
	match t.tier:
		"win", "normal":
			await test_win(t)
		"loss":
			await test_loss(t)
		"skip":
			await test_skip(t)
		"table":
			await test_table(t)
		_:
			t.check(false, "tier is win, loss, skip or table (%s)" % t.tier)


static func test_win(t) -> void:
	var sumo: Node = await into_sumo(t)
	if sumo == null:
		return
	t.check(await through_cut(t, sumo), "the cut, watched through, reaches the mash")
	check_beats(t, sumo)
	t.check(not t.boss.defeated and not t.player.fight_over, "nothing has ended the fight yet: not defeated, no fight_over")
	var glyphs: Array = key_glyphs(sumo)
	t.check(glyphs == ["qte_key_left_3x.png", "qte_key_right_3x.png"] and sumo.meter.key_actions == sumo.pair,
		"the mash keys stand either side of the meter: the finisher's glyphs for its pair (%s, %s)" % [glyphs, sumo.pair])
	var lowest := [INF]
	var watch := func():
		if sumo.phase == sumo.Phase.WON or sumo.phase == sumo.Phase.DONE:
			lowest[0] = minf(lowest[0], t.boss.global_position.y)
	t.physics_frame.connect(watch)
	var looks := {"skid": 0, "not_skid": 0, "surges": 0, "surge_steps": 0, "surge_off": 0, "lit": []}
	var was_surging := [false]
	var look_watch := func():
		if sumo.phase != sumo.Phase.MASH:
			return
		var surging: bool = sumo.tug.surging()
		if surging:
			looks.surge_steps += 1
			if t.boss.current_anim != &"push_win" or not sumo.meter.surging:
				looks.surge_off += 1
			if not was_surging[0]:
				looks.surges += 1
		elif sumo.rope > 0.0:
			looks["skid" if t.boss.current_anim == &"push_skid" else "not_skid"] += 1
		was_surging[0] = surging
		if is_instance_valid(sumo.meter) and not looks.lit.has(sumo.meter.lit_action):
			looks.lit.append(sumo.meter.lit_action)
	t.physics_frame.connect(look_watch)
	var model: Dictionary = model_bout(sumo, TARGET)
	var bout: Dictionary = await mash_at(t, sumo, TARGET)
	t.physics_frame.disconnect(look_watch)
	t.log_p("7 a second: live %s, model %s; his looks %s" % [bout, model, looks])
	t.check(bout.result == &"win" and model.result == &"win" and absf(bout.time - model.time) <= TIME_SLACK,
		"a bot at 7 a second wins, when the model does (%.2f s live, %.2f s model)" % [bout.time, model.time])
	t.check(looks.skid > 0 and looks.not_skid == 0, "outside his surges he skids on every step the rope is the player's way (%d skidding, %d not)" % [looks.skid, looks.not_skid])
	t.check(looks.surges >= 2 and looks.surge_off == 0,
		"he surges %d times, leaning in with his end of the meter lit on every step of each (%d of %d steps not)" % [looks.surges, looks.surge_off, looks.surge_steps])
	t.check(looks.lit.has(sumo.pair[0]) and looks.lit.has(sumo.pair[1]), "the presses light the next key in turn (%s)" % [looks.lit])
	await t.wait_until(func(): return t.sm.current_state == t.sm.states["Defeated"], 300)
	t.physics_frame.disconnect(watch)
	var outros: Array = t.root.get_children().filter(func(c): return str(c.name).begins_with("FightOutro"))
	t.check(t.sm.current_state == t.sm.states["Defeated"] and t.boss.defeated and not t.boss.sprite.visible,
		"him defeated and gone (%s)" % t.sm.current_state.name)
	t.check(lowest[0] <= sumo.danny_out_feet_y + 1.0, "pushed out through the top gate (feet up to %.0f)" % lowest[0])
	var gates: Node = t.sm.gates()
	t.check(gates != null and not gates.is_open(), "the gates shut behind him")
	t.check(outros.size() == 1 and outros[0].player_won, "one outro, the player's win")
	t.check(await t.wait_until(func(): return t.live_balloon() != null, 200) and _line_text(t).begins_with("...ow"),
		"his player_won line (%s)" % _line_text(t))
	t.check(is_zero_approx(t.boss.health_bar.modulate.a), "his finished bar stays gone")
	leave(t)


static func test_loss(t) -> void:
	var sumo: Node = await into_sumo(t)
	if sumo == null:
		return
	t.check(await through_cut(t, sumo), "the cut, watched through, reaches the mash")
	check_beats(t, sumo)
	var model: Dictionary = model_bout(sumo, 0.0)
	var his_way := {"skid": 0, "strain": 0}
	var look_watch := func():
		if sumo.phase == sumo.Phase.MASH and sumo.rope < 0.0:
			his_way["skid" if t.boss.current_anim == &"push_skid" else "strain"] += 1
	t.physics_frame.connect(look_watch)
	await t.wait_until(func(): return sumo.tug != null and sumo.tug.clock >= 1.0, 200)
	var held_rope: float = sumo.rope
	var held_clock: float = sumo.tug.clock
	t.paused = true
	await t.wait(60)
	var held: bool = sumo.rope == held_rope and sumo.tug.clock == held_clock and sumo.tug.result == &""
	t.paused = false
	t.check(held, "a pause mid-mash holds the rope (%.4f, then %.4f after a paused second)" % [held_rope, sumo.rope])
	var bout: Dictionary = await mash_at(t, sumo, 0.0)
	t.physics_frame.disconnect(look_watch)
	t.check(his_way.strain > 0 and his_way.skid == 0, "with the rope going his way he strains and never skids (%s)" % [his_way])
	t.log_p("no presses: live %s, model %s" % [bout, model])
	t.check(bout.result == &"loss" and model.result == &"loss" and absf(bout.time - model.time) <= TIME_SLACK,
		"no presses loses, when the model does (%.2f s live, %.2f s model)" % [bout.time, model.time])
	var deepest := [-INF]
	var watch := func():
		if is_instance_valid(t.player):
			deepest[0] = maxf(deepest[0], t.sm.player_feet().y)
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return t.sm.current_state == t.sm.states["Victory"], 300)
	t.physics_frame.disconnect(watch)
	var outros: Array = t.root.get_children().filter(func(c): return str(c.name).begins_with("FightOutro"))
	t.check(deepest[0] >= sumo.player_out_feet_y - 1.0, "the player pushed out through the bottom gate (feet down to %.0f)" % deepest[0])
	t.check(is_instance_valid(sumo.prop) and sumo.prop.visible and not t.player.sprite.visible,
		"their sprite hidden under the prop of their last frame")
	var gates: Node = t.sm.gates()
	t.check(gates != null and not gates.is_open(), "the gates shut behind them")
	t.check(outros.size() == 1 and not outros[0].player_won, "one outro, the player's loss")
	t.check(t.sm.current_state == t.sm.states["Victory"] and not t.boss.defeated, "he sits down for his nap (Victory)")
	t.check(await t.wait_until(func(): return t.live_balloon() != null, 200) and _line_text(t).begins_with("out of the ring"),
		"his player_lost line (%s)" % _line_text(t))
	leave(t)


static func test_skip(t) -> void:
	var sumo: Node = await into_sumo(t)
	if sumo == null:
		return
	t.check(await through_cut(t, sumo), "the cut, watched through, reaches the mash")
	check_beats(t, sumo)
	var watched: Dictionary = snapshot(t, sumo)
	t.log_p("watched, at the clinch: %s" % [watched])
	t.check(watched.danny == t.sm.GATE_BLOCK and not watched.flip and watched.lift == 0.0 and watched.player == sumo._clinch_position()
		and watched.sealed and watched.posed and watched.facing_point == t.sm.GATE_BLOCK and not watched.talking
		and watched.gates_open and watched.bar_alpha == 0.0 and watched.meter and watched.rope == 0.0
		and watched.music_restarts == 1 and watched.music and not watched.balloon and watched.zoom == 1.0
		and watched.shake == Vector2.ZERO and watched.time_scale == 1.0, "the clinch is set the plan's way")
	for skip_at in [sumo.Phase.STIR, sumo.Phase.LEAP, sumo.Phase.LINE, sumo.Phase.WALK]:
		sumo = await into_sumo(t)
		if sumo == null:
			return
		var reached: bool = await through_cut(t, sumo, skip_at)
		var skipped: Dictionary = snapshot(t, sumo)
		var diffs := diff(skipped, watched)
		t.check(reached and diffs.is_empty(), "a hold in the %s lands on the same clinch %s" % [str(sumo.Phase.keys()[skip_at]).to_lower(), diffs])
	leave(t)


static func test_table(t) -> void:
	var sumo: Node = await into_sumo(t)
	if sumo == null:
		return
	var model = _model(sumo)
	t.log_p(model.table())
	var rows := {}
	for rate in [0, 4, 5, 6, 7, 8, 9, 11]:
		rows[rate] = model.steady(rate)
	var need: float = model.needed_rate()
	var fastest: float = model.press_speed / model.press_gain
	t.check(rows[0].result == &"loss" and rows[0].time >= 1.5 and rows[0].time <= 2.5, "0 a second loses in 1.5-2.5 s (%.2f)" % rows[0].time)
	t.check(rows[4].result == &"loss" and rows[5].result == &"loss" and rows[5].time <= 12.0,
		"4 and 5 a second lose, 5 inside 12 s (%.2f, %.2f)" % [rows[4].time, rows[5].time])
	t.check(rows[6].result == &"loss", "6 a second is not enough (%s at %.2f s)" % [rows[6].result, rows[6].time])
	t.check(need >= 6.0 and need <= 6.6, "the slowest steady rate that wins at all is 6.0-6.6 a second (%.2f)" % need)
	t.check(rows[7].result == &"win" and rows[7].time >= 8.0 and rows[7].time <= 11.0, "7 a second, the target, wins in 8-11 s (%.2f)" % rows[7].time)
	var even: bool = [8, 9, 11].all(func(rate): return rows[rate].result == &"win" and absf(rows[rate].time - rows[8].time) <= 0.02)
	t.check(even and rows[8].time >= 5.5 and rows[8].time < rows[7].time,
		"8, 9 and 11 a second all win in the same %.2f s: the rope takes no more than %.1f a second, so it can't be sprinted" % [rows[8].time, fastest])

	check_flat(t, model)

	var slack_schedule := func(clock: float) -> float: return 0.0 if clock >= SLACK_AT and clock < SLACK_AT + SLACK_FOR else TARGET
	for rate in [TARGET, 11.0]:
		var run: Dictionary = model_run(sumo, func(_clock: float) -> float: return rate)
		var heaves: Array = surge_heaves(run.trace)
		t.check(run.result == &"win" and heaves.size() >= 2 and heaves.all(func(h): return h >= 0.2),
			"at %.0f a second every surge takes at least 0.2 of the rope back, and it is won all the same (%s)" % [rate, heaves])
	var slacked: Dictionary = model_run(sumo, slack_schedule)
	var lead: float = slacked.trace.filter(func(step): return step.t < SLACK_AT).map(func(step): return step.rope).max()
	var dip: float = slacked.trace.filter(func(step): return step.t >= SLACK_AT).map(func(step): return step.rope).min()
	t.check(slacked.result == &"win" and lead > 0.3 and dip < 0.0,
		"7 a second with a second's stop at %.0f s: the lead lost (%.2f, down to %.2f) and won back at the same rate, a win at %.2f s" % [SLACK_AT, lead, dip, slacked.time])
	var comeback: Dictionary = model_run(sumo, func(clock: float) -> float: return 0.0 if clock < 1.2 else 7.5)
	var deepest: float = comeback.trace.map(func(step): return step.rope).min()
	t.check(comeback.result == &"win" and deepest < -0.6,
		"down to %.2f on his side with nothing pressed for 1.2 s, 7.5 a second still wins it back (at %.2f s): no spiral at his end" % [deepest, comeback.time])

	var bots := [["5 a second", func(_clock: float) -> float: return 5.0], ["7 a second with a second's stop", slack_schedule]]
	for i in bots.size():
		if i > 0:
			sumo = await into_sumo(t)
			if sumo == null:
				return
		await through_cut(t, sumo, sumo.Phase.STIR)
		var want: Dictionary = model_run(sumo, bots[i][1])
		var bout: Dictionary = await mash_with(t, sumo, bots[i][1])
		t.log_p("%s: live %s, model %s at %.2f s" % [bots[i][0], bout, want.result, want.time])
		t.check(bout.result == want.result and absf(bout.time - want.time) <= TIME_SLACK,
			"a bot at %s against the live tug: %s at %.2f s, the model's %s at %.2f s" % [bots[i][0], bout.result, bout.time, want.result, want.time])
		await t.wait_until(func(): return t.sm.current_state != sumo, 300)
		leave(t)


# The same effort wherever the rope stands: from -0.5, the line and +0.5, a press and half a second of his push,
# into a surge, move it exactly the same.
static func check_flat(t, model) -> void:
	var moved := []
	for at in [-0.5, 0.0, 0.5]:
		var bout = model.fresh()
		bout.rope = at
		bout.clock = model.surge_first
		bout.press()
		for i in 30:
			bout.advance(1.0 / 60.0)
		moved.append(snappedf(bout.rope - at, 0.0001))
	t.check(moved[0] == moved[1] and moved[1] == moved[2], "a press and his push move the rope the same wherever it stands (%s)" % [moved])


#GETTING THERE

# His fight, loaded past his entrance and the card and parked; then his nap, and a punch at 1 HP. The Sumo, once
# the KO has taken him into it, or null.
static func into_sumo(t) -> Node:
	leave(t)
	await t.load_fight("danny")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_ESCAPE]:
		t.release(code)
	await t.settle_player(START)
	var sumo: Node = t.sm.states["Sumo"]
	t.sm.on_child_transition(t.sm.current_state, "Sleep")
	await t.wait(3)
	t.stop_boss_timers()
	t.boss.boss_health = 1
	var dealt: int = t.boss.take_punch(1)
	var entered: bool = await t.wait_until(func(): return t.sm.current_state == sumo, 30)
	t.check(dealt == 1 and entered, "a punch at 1 HP in his nap takes him into the sumo (%s)" % t.sm.current_state.name)
	return sumo if entered else null


# The cut from the KO to the mash, its line read; `skip_at`, a Phase, holds Escape from the moment that beat
# starts. Whether the mash was reached.
static func through_cut(t, sumo: Node, skip_at := -1) -> bool:
	var held := -1
	for i in 4000:
		if t.sm.current_state != sumo or sumo.phase >= sumo.Phase.MASH:
			break
		if skip_at >= 0 and held < 0 and sumo.phase == skip_at:
			t.press(KEY_ESCAPE)
			held = 0
		if held >= 0:
			held += 1
			if held == ESCAPE_HOLD:
				t.release(KEY_ESCAPE)
		elif sumo.phase == sumo.Phase.LINE and t.live_balloon() != null:
			await t.read_line()
			continue
		await t.physics_frame
	if held >= 0 and held < ESCAPE_HOLD:
		t.release(KEY_ESCAPE)
	return t.sm.current_state == sumo and sumo.phase == sumo.Phase.MASH


# A steady `rate` of alternating presses from the mash's start, on its own clock, until the tug has a result.
static func mash_at(t, sumo: Node, rate: float) -> Dictionary:
	return await mash_with(t, sumo, func(_clock: float) -> float: return rate)


# Alternating presses at `schedule`'s rate for the tug's clock (0 for none), on its own clock, until the tug has
# a result.
static func mash_with(t, sumo: Node, schedule: Callable) -> Dictionary:
	await t.wait_until(func(): return sumo.phase == sumo.Phase.MASH and sumo.tug != null, 200)
	if sumo.tug == null:
		return {"result": &"", "time": -1.0, "presses": 0}
	var pair: Array = sumo.pair
	var next := 0.0
	var taps := 0
	while t.sm.current_state == sumo and sumo.tug.result == &"":
		var rate: float = schedule.call(sumo.tug.clock)
		if rate <= 0.0:
			next = sumo.tug.clock
		elif sumo.tug.clock >= next - 0.0001:
			t.tap(t.MASH_KEYS[pair[taps % 2]])
			taps += 1
			next += 1.0 / rate
		await t.physics_frame
	return {"result": sumo.tug.result, "time": snappedf(sumo.tug.clock, 0.001), "presses": sumo.tug.presses, "taps": taps}


# The model on this Sumo's own knobs.
static func _model(sumo: Node):
	var model = load(TUG).new()
	for knob in model.KNOBS:
		model.set(knob, sumo.get(knob))
	return model


static func model_bout(sumo: Node, rate: float) -> Dictionary:
	return _model(sumo).steady(rate)


# The model pressed the way mash_with() presses the live tug: {result, time, presses, trace}, with a
# {t, rope, surging} for every step.
static func model_run(sumo: Node, schedule: Callable) -> Dictionary:
	var bout = _model(sumo)
	var next := 0.0
	var trace := []
	while bout.result == &"":
		var rate: float = schedule.call(bout.clock)
		if rate <= 0.0:
			next = bout.clock
		else:
			while bout.result == &"" and bout.clock >= next - 1e-9:
				bout.press()
				next += 1.0 / rate
		bout.advance(1.0 / 60.0)
		trace.append({"t": bout.clock, "rope": bout.rope, "surging": bout.surge() > 0.0})
	return {"result": bout.result, "time": bout.clock, "presses": bout.presses, "trace": trace}


# How much of the rope each surge took back: from where it stood as the surge began to the lowest it went in it.
static func surge_heaves(trace: Array) -> Array:
	var heaves := []
	var from := 0.0
	var low := 0.0
	var in_surge := false
	for step in trace:
		if step.surging and not in_surge:
			in_surge = true
			from = step.rope
			low = step.rope
		elif in_surge:
			low = minf(low, step.rope)
			if not step.surging:
				in_surge = false
				heaves.append(snappedf(from - low, 0.01))
	return heaves


# Out of whatever the last run left: its outro, a hit-stop, a freeze and the view.
static func leave(t) -> void:
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	t.paused = false
	load(HIT_STOP).clear()
	load(FIGHT_FREEZE).unfreeze(t)
	load(SCREEN_VIEW).reset(t)


#WHAT IS CHECKED

static func check_beats(t, sumo: Node) -> void:
	var times: Dictionary = sumo.beat_times
	var off := []
	for beat in PLAN_BEATS:
		if not times.has(beat) or absf(times[beat] - PLAN_BEATS[beat]) > BEAT_SLACK:
			off.append([beat, snappedf(times.get(beat, -1.0), 0.001), PLAN_BEATS[beat]])
	t.check(off.is_empty(), "the cut's beats on the plan's times (%s)" % [off if not off.is_empty() else times])
	var walk: float = times.get(&"walk", -1.0)
	t.check(walk >= 0.3 - BEAT_SLACK and walk <= 1.4 + BEAT_SLACK, "the walk onto the clinch in 0.3-1.4 s (%.3f)" % walk)


# The ring at the clinch: everything a watched cut and a held one must agree on, taken as the mash starts.
static func snapshot(t, sumo: Node) -> Dictionary:
	var boss: Node = t.boss
	var player: Node = t.player
	var gates: Node = t.sm.gates()
	var screen: GDScript = load(SCREEN_VIEW)
	var hazards: Array = t.get_nodes_in_group(t.sm.HAZARD_GROUP).filter(func(h): return not h.is_queued_for_deletion())
	return {
		"danny": boss.global_position, "anim": boss.current_anim, "flip": boss.sprite.flip_h, "lift": boss.lift_px,
		"visible": boss.sprite.visible, "white": boss.sprite.material != null, "hurtbox": boss.hurtbox.monitoring,
		"player": player.global_position, "locked": player.is_action_locked, "sealed": player.lock_seals_guard,
		"posed": player.is_posed(), "facing_point": player.facing_point, "talking": player.is_talking,
		"player_sm": player.state_machine.is_processing(),
		"gates_open": gates != null and gates.is_open(),
		"bar_alpha": snappedf(boss.health_bar.modulate.a, 0.01),
		"gauge_alpha": snappedf(boss.gauge_bar.modulate.a, 0.01) if boss.gauge_bar else -1.0,
		"meter": is_instance_valid(sumo.meter), "rope": sumo.meter.rope if is_instance_valid(sumo.meter) else -9.0,
		"keys": key_glyphs(sumo),
		"music_restarts": boss.music_restarts, "music": boss.music_player.playing,
		"hazards": hazards.size(), "balloon": t.live_balloon() != null, "cut": is_instance_valid(sumo.cut),
		"call": is_instance_valid(sumo.call_label), "zoom": snappedf(screen.zoom, 0.0001), "shake": screen.shake_offset,
		"time_scale": snappedf(Engine.time_scale, 0.01), "defeated": boss.defeated, "fight_over": player.fight_over,
	}


static func diff(got: Dictionary, want: Dictionary) -> Array:
	var diffs := []
	for k in want:
		if got.get(k) != want[k]:
			diffs.append("%s %s (watched %s)" % [k, got.get(k), want[k]])
	return diffs


# The mash keys either side of the meter, by what each shows: a key sheet's file, or a keycap's text.
static func key_glyphs(sumo: Node) -> Array:
	if not is_instance_valid(sumo.meter):
		return []
	return sumo.meter.keys.values().map(func(key): return key.texture.resource_path.get_file() if key is Sprite2D else str(key.text))


static func _line_text(t) -> String:
	var balloon: Node = t.live_balloon()
	if balloon == null or balloon.dialogue_line == null:
		return ""
	return balloon.dialogue_line.text
