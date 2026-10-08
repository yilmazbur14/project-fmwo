extends RefCounted

# jordan_final_beam: god-form Jordan's last kill as a five-bar charge mash and a beam (JordanGodFinalBeam,
# FinalBeamLayout). --max-fps 60: the mash's press gate and the pause screen's grace are real time. The fight runs on
# jordan_god's stub combo (god.gd), him at 1 so its punch-out kills him. Each tier sets the switches it needs
# (JordanGodLayout.USE_FINAL_BEAM, FinalBeamLayout.STAGING and USE_FINAL_ART) and run() puts them back. tier=
#   model    the meter alone on the beam's numbers, presses on an accumulating clock: each bar's steady threshold within
#            0.2 of 5.5 / 6.25 / 7.0 / 7.5 / 8.0 a second; at 60 fps a press every 7 frames banks all five and every 8
#            doesn't; never pressed, it ends on 0 at START_GRACE + bar 1's window; 1000 seeded runs at +-15%: 8.5 a
#            second wins >= 85%, 7.5 <= 15%, 9.5 >= 99%; after three failed beams bar 5 asks <= 6.8 a second
#   win      a real three-bar punch-out kills him: the beam entered once, the KO over before it moves on, no puppets or
#            strings left, the player on the staging's mark facing its way and sealed, the HUD down; a press every 6
#            frames: after each bar the view settles at 2/3 x the staging's zooms[bar], the ball grows and the shout
#            builds; at bar 0's view and every bar's his head (HEAD) and the player's cell are whole on screen; he
#            dissolves all the way and his body is gone; one won FightOutro, his defeat's beats "", beam, leaving, the
#            scene the outro went to, and on it a still, level view at 1 and normal speed
#   fail     a press every 9 frames, two bars: the beam at FAIL_WIDTH[2], him coming apart to about FAIL_DISSOLVE[2] and
#            back whole, revived on 5 of his bar with the HUD back, the next attack in turn, the player free and drawn,
#            the view back on the fight's own; then one uppercut of a one-bar punch-out takes his 5, the beam comes
#            back, wins, and the game moves on. Then a mash never pressed: no beam, his laugh, revived
#   off      the switch off: his defeat as it was ("", snap, crumple, dissolve, god, leaving), the beam never entered
#   pause    paused mid-mash: the meter's clock and fill and the view held, a press while paused not counted; paused
#            mid-dissolve: it holds; and both finish
#   back     the win tier on the back staging (its own mark, the beam straight up; the player, aura and ash stand-ins)
#   standin  the win tier and a two-bar fail with every drawn piece off (FinalBeamLayout.USE_FINAL_ART)
#   normal   all of them in turn.

const God := preload("res://art_source/defense_tests/jordan/god.gd")
const Finale := preload("res://art_source/defense_tests/jordan/finale.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const Layout := preload("res://Scripts/FinalBeamLayout.gd")
const FinisherTierMeter := preload("res://Scripts/FinisherTierMeter.gd")
const MashInput := preload("res://Scripts/MashInput.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const TIERS := ["model", "win", "fail", "off", "pause", "back", "standin"]
const TARGETS := [5.5, 6.25, 7.0, 7.5, 8.0]
const HIT_SILENT := 2
const FINISHER_DAZED := 2
const BASE_ORIGIN := Vector2(320, 4)
# His head on his hit frames, the crown's flames to his chin, in his frame's texels: the charge's camera holds it.
const HEAD := Rect2(128, 46, 62, 62)
const SCREEN := Rect2(0, 0, 1920, 1080)
# His shout as the beam takes him apart, the user's line (2026-10-08).
const SHOUT_LINE := "NOOOOO! IMPOSSIBLE!"
const FRAME := 1.0 / 60.0
const DialogueVoices := preload("res://Scripts/DialogueVoices.gd")


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	var beam_on: bool = GodLayout.USE_FINAL_BEAM
	var staging: StringName = Layout.STAGING
	var art: bool = Layout.USE_FINAL_ART
	var combos: Array[String] = GodLayout.COMBOS.duplicate()
	for tier in tiers:
		t.log_p("-- jordan_final_beam %s" % tier)
		GodLayout.USE_FINAL_BEAM = tier != "off"
		Layout.STAGING = &"back" if tier == "back" else &"side"
		Layout.USE_FINAL_ART = tier != "standin"
		match tier:
			"model":
				tier_model(t)
			"win", "back":
				await tier_win(t, tier)
			"fail":
				await tier_fail(t)
				await tier_fizzle(t)
			"off":
				await tier_off(t)
			"pause":
				await tier_pause(t)
			"standin":
				await tier_win(t, tier)
				await tier_fail(t, false)
			_:
				t.check(false, "jordan_final_beam has no tier %s" % tier)
	GodLayout.USE_FINAL_BEAM = beam_on
	Layout.STAGING = staging
	Layout.USE_FINAL_ART = art
	GodLayout.COMBOS = combos


#THE MODEL

static func tier_model(t) -> void:
	t.log_p("gain %.2f, drains %s, windows %s, %.1f s to start" % [Layout.GAIN, Layout.DRAINS, Layout.WINDOWS, Layout.START_GRACE])
	for bar in Layout.BARS:
		var rate := threshold(Layout.drains(0), bar + 1)
		t.check(absf(rate - TARGETS[bar]) <= 0.2, "bar %d from about %.2f presses a second (%.3f)" % [bar + 1, TARGETS[bar], rate])
	var seven := by_frames(7)
	var eight := by_frames(8)
	t.check(seven == Layout.BARS and eight < Layout.BARS, "at 60 fps a press every 7 frames banks all five (%d), every 8 doesn't (%d)" % [
		seven, eight])
	var idle := FinisherTierMeter.new(Layout.GAIN, Layout.drains(0), Layout.WINDOWS, Layout.START_GRACE, Layout.IDLE_STOP)
	while not idle.resolved:
		idle.advance(1.0 / 60.0)
	var want: float = Layout.START_GRACE + Layout.WINDOWS[0]
	t.check(idle.banked == 0 and absf(idle.clock - want) <= 1.0 / 60.0 + 0.001,
		"never pressed, it ends on 0 bars at %.2f s (%.3f)" % [want, idle.clock])
	var bands := {8.5: [0.85, 1.0], 7.5: [0.0, 0.15], 9.5: [0.99, 1.0]}
	for rate in bands:
		var won := win_rate(Layout.drains(0), rate)
		t.check(won >= bands[rate][0] and won <= bands[rate][1], "%.1f a second +-15%%: wins %.1f%% of 1000 beams" % [rate, won * 100.0])
	for fails in [1, 2, 3]:
		t.log_p("after %d failed: bar 5 from %.3f a second; 7.5 +-15%% wins %.1f%%" % [fails, threshold(Layout.drains(fails), 5),
			win_rate(Layout.drains(fails), 7.5) * 100.0])
	var mercy := threshold(Layout.drains(3), Layout.BARS)
	t.check(mercy <= 6.8, "after three failed beams bar 5 asks %.3f a second (<= 6.8)" % mercy)


# The lowest steady rate that banks `bar`, presses on an accumulating clock.
static func threshold(drains: Array[float], bar: int) -> float:
	var low := 3.0
	var high := 20.0
	for i in 24:
		var rate := (low + high) / 2.0
		var meter := FinisherTierMeter.new(Layout.GAIN, drains, Layout.WINDOWS, Layout.START_GRACE, Layout.IDLE_STOP)
		var next_press := 0.0
		while not meter.resolved and meter.clock < 30.0:
			if meter.clock >= next_press - 1e-9:
				meter.press()
				next_press += 1.0 / rate
			meter.advance(1.0 / 1200.0)
		if meter.banked >= bar:
			high = rate
		else:
			low = rate
	return high


static func by_frames(every: int) -> int:
	var meter := FinisherTierMeter.new(Layout.GAIN, Layout.drains(0), Layout.WINDOWS, Layout.START_GRACE, Layout.IDLE_STOP)
	for f in 60 * 30:
		if meter.resolved:
			break
		if f % every == 0:
			meter.press()
		meter.advance(1.0 / 60.0)
	return meter.banked


# Of 1000 seeded beams at `rate` with each interval +-15%, on an accumulating clock: the share that bank all five.
static func win_rate(drains: Array[float], rate: float) -> float:
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var wins := 0
	for run_index in 1000:
		var meter := FinisherTierMeter.new(Layout.GAIN, drains, Layout.WINDOWS, Layout.START_GRACE, Layout.IDLE_STOP)
		var next_press := 0.0
		while not meter.resolved and meter.clock < 30.0:
			if meter.clock >= next_press - 1e-9:
				meter.press()
				next_press += rng.randf_range(0.85, 1.15) / rate
			meter.advance(1.0 / 1200.0)
		if meter.banked == Layout.BARS:
			wins += 1
	return wins / 1000.0


#GETTING THERE

# His last phase on the stub's punch-out, him at 1, `combos` its attacks. The god.
static func open_at_one(t, combos: Array[String]) -> Node:
	var god: Node = await God.open_god(t, combos, &"punch")
	await t.wait_until(func(): return god.state_machine.combos[0].punching, 60 * 20)
	god.boss_health = 1
	god.health_bar.set_value(0, 1, HIT_SILENT)
	return god


static func god_now(t) -> Node:
	if not God.scene_is(t, God.GOD_SCENE):
		return null
	return t.current_scene.get_node_or_null(God.GOD_PATH)


# Everything the beam and his defeat do, looked up each frame (never held: the scene goes), into `seen`.
static func watcher(t, seen: Dictionary) -> Callable:
	return func():
		var outro: Node = t.root.get_node_or_null("FightOutro")
		if outro != null:
			seen.won = outro.player_won
			if outro.leaving:
				seen.destination = outro.destination
		if seen.destination != "" and God.scene_is(t, seen.destination) and seen.arrival.is_empty():
			seen.arrival = {"view": t.root.canvas_transform, "time_scale": Engine.time_scale, "base": ScreenView.base_zoom,
				"zoom": ScreenView.zoom, "shake": ScreenView.shake_offset}
		var god: Node = god_now(t)
		if god == null:
			return
		var defeated: Node = god.state_machine.states["Defeated"]
		if seen.defeated.is_empty() or seen.defeated[-1] != defeated.beat:
			seen.defeated.append(defeated.beat)
		var beam: Node = god.state_machine.final_beam
		if beam == null:
			return
		if seen.beats.is_empty() or seen.beats[-1] != beam.beat:
			seen.beats.append(beam.beat)
			if is_instance_valid(beam.fx):
				seen.beat_clocks[beam.beat] = beam.fx.clock
			if beam.beat == &"collapse":
				var finisher: Node = t.player.finisher
				seen.ko_over = seen.ko_over and not finisher.is_active() \
					and not god.defeat_puppets.any(func(puppet) -> bool: return is_instance_valid(puppet) and puppet.is_juggled())
		var balloon: Node = beam.shout_balloon
		if is_instance_valid(balloon) and balloon.is_inside_tree() and not balloon.is_queued_for_deletion() \
				and balloon.dialogue_line != null and is_instance_valid(beam.fx):
			var shout: Dictionary = seen.shout
			var into: float = beam.fx.clock - seen.beat_clocks.get(&"dissolve", beam.fx.clock)
			if shout.is_empty():
				shout.merge({"from": beam.beat, "at": into, "typed": &"", "typed_at": -1.0, "beats": [], "arrow_frames": 0})
			shout.text = balloon.dialogue_label.get_parsed_text()
			shout.character = balloon.dialogue_line.character
			shout.portrait = balloon.portrait.texture.resource_path if balloon.portrait.texture != null else ""
			shout.voiced = balloon._voice == DialogueVoices.for_character("Jordan")
			if shout.typed == &"" and not balloon.dialogue_label.is_typing:
				shout.typed = beam.beat
				shout.typed_at = into
			if not shout.beats.has(beam.beat):
				shout.beats.append(beam.beat)
			if balloon.progress.is_visible_in_tree() and balloon.progress.modulate.a > 0.0:
				shout.arrow_frames += 1
		if god.current_anim == &"laugh":
			seen.laughed = true
		if is_instance_valid(beam.fx):
			seen.progress = maxf(seen.progress, beam.fx.progress)
			seen.length = maxf(seen.length, beam.fx.beam_length)
			if beam.beat == &"weak" or beam.beat == &"release":
				seen.width = maxf(seen.width, beam.fx.beam_width)
		if beam.beat == &"fade" or beam.beat == &"settle" or beam.beat == &"won":
			seen.body_hidden = not god.body.visible


static func new_seen() -> Dictionary:
	return {"beats": [], "defeated": [], "ko_over": true, "progress": 0.0, "length": 0.0, "width": 0.0, "laughed": false,
		"body_hidden": false, "won": false, "destination": "", "arrival": {}, "beat_clocks": {}, "shout": {}}


# A press every `every` physics frames, alternating, until the mash resolves; at most `want` bars. What it saw at each
# bar: the view's scale and framing settled just before the next bar (or the release), the ball's size and the shout;
# and the framing the mash opened on, bar 0's.
static func mash(t, beam: Node, every: int, want := Layout.BARS) -> Dictionary:
	beam.min_press_interval = 0.0
	var pair: Array = MashInput.actions(t.player)
	var out := {"presses": 0, "banks": [], "first": framing(t, beam)}
	var i := 0
	var last_bars := 0
	var last_scale: float = t.root.canvas_transform.x.x
	var last_framing: Dictionary = out.first
	var shout := {}
	while is_instance_valid(beam) and beam.mashing:
		if beam.bars < want and i % every == 0:
			t.tap(t.MASH_KEYS[pair[out.presses % 2]])
			out.presses += 1
		i += 1
		await t.physics_frame
		if not is_instance_valid(beam):
			break
		if beam.bars != last_bars:
			if last_bars > 0:
				out.banks.append({"bar": last_bars, "scale": last_scale, "ball": shout.ball, "shout": shout.shown,
					"framing": last_framing})
			last_bars = beam.bars
			shout = {"ball": beam.fx.ball_size, "shown": shout_shown(beam.ui)}
		last_scale = t.root.canvas_transform.x.x
		last_framing = framing(t, beam)
	if last_bars > 0 and last_bars < Layout.BARS:
		out.banks.append({"bar": last_bars, "scale": last_scale, "ball": shout.ball, "shout": shout.shown,
			"framing": last_framing})
	return out


# On screen this frame: his head (HEAD, on his body's frame) and the player's cell round their origin, and whether
# each is whole on the screen.
static func framing(t, beam: Node) -> Dictionary:
	var body: Sprite2D = beam.god.body
	var head: Rect2 = body.get_global_transform_with_canvas() * Rect2(body.get_rect().position + HEAD.position, HEAD.size)
	var size: Vector2 = Layout.FINAL_PLAYER_CELL * Layout.TEXEL
	var cell: Rect2 = t.root.canvas_transform * Rect2(t.player.global_position - size / 2.0, size)
	return {"head": head, "cell": cell, "whole": SCREEN.encloses(head) and SCREEN.encloses(cell)}


# What the shout shows: the drawn word's index, or the text line.
static func shout_shown(ui: Node) -> Variant:
	return ui.word if ui.drawn_words else ui.line


static func shout_wanted(ui: Node, bar: int) -> Variant:
	return bar - 1 if ui.drawn_words else " ".join(Layout.SYLLABLES.slice(0, bar))


# Three punches on `combo`'s puppet and a mash of `bars` bars: the finisher's payoff.
static func punch_out_on(t, combo: Node, bars: int) -> int:
	await t.wait_until(func(): return combo.punching and not combo.released, 60 * 20)
	for i in 3:
		t.tap(KEY_Q)
		await t.wait(8)
	var finisher: Node = t.player.finisher
	await t.wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120)
	return await God.mash_bars(t, bars)


#WIN

static func tier_win(t, label: String) -> void:
	var god: Node = await open_at_one(t, [God.STUB] as Array[String])
	var beam: Node = god.state_machine.final_beam
	var seen := new_seen()
	var watch = Finale.Watch.new(t)
	var track := watcher(t, seen)
	t.process_frame.connect(watch.step)
	t.process_frame.connect(track)
	var kill: Dictionary = await God.punch_out(t, god)
	var mashing: bool = await t.wait_until(func(): return beam.mashing, 60 * 10)
	t.log_p("%s: the killing punch-out %s; the beam's beats %s" % [label, kill, seen.beats])
	t.check(beam != null and kill.banked == 3 and mashing and beam.entries == 1 and seen.ko_over,
		"%s: a three-bar punch-out kills him and the beam takes it, once, with the KO over first" % label)
	var p: CharacterBody2D = t.player
	var spec: Dictionary = Layout.staging()
	var strings: Node = t.current_scene.get_node(God.STRINGS_PATH)
	t.check(God.puppets_up(t).is_empty() and strings.line_count() == 0, "%s: no puppets and no strings left (%d, %d)" % [label,
		God.puppets_up(t).size(), strings.line_count()])
	t.check(p.global_position == spec.mark and p.facing == spec.facing and p.is_action_locked and p.lock_seals_guard \
		and god.health_bar.modulate.a < 0.01,
		"%s: the player on the mark %s facing %d, sealed, the HUD down (%s, %d, %.2f)" % [label, spec.mark, spec.facing,
			p.global_position, p.facing, god.health_bar.modulate.a])
	t.check(beam.fx.final_player == Layout.final_player() and beam.fx.overlay_on == Layout.final_player()
		and beam.fx.final_god == Layout.final_god(),
		"%s: drawn player %s, drawn end %s, as the art in says" % [label, beam.fx.overlay_on, beam.fx.final_god])
	var mashed: Dictionary = await mash(t, beam, 6)
	t.log_p("%s: %d presses; at each bar %s" % [label, mashed.presses, mashed.banks])
	var bars_ok: bool = mashed.banks.size() == Layout.BARS - 1
	var framed: Array = [mashed.first]
	for bank in mashed.banks:
		var want: float = GodLayout.VIEW_ZOOM * spec.zooms[bank.bar]
		bars_ok = bars_ok and absf(bank.scale - want) <= 0.01 and bank.ball == bank.bar and bank.shout == shout_wanted(beam.ui, bank.bar)
		framed.append(bank.framing)
	t.check(bars_ok and beam.result == &"won", "%s: five bars; after each the view settles at 2/3 x the staging's zooms, the ball grows and the shout builds" % label)
	t.log_p("%s: framing at bars 0-4: %s" % [label, framed.map(func(f: Dictionary) -> String: return "head %s, cell %s" % [f.head, f.cell])])
	t.check(framed.size() == Layout.BARS and framed.all(func(f: Dictionary) -> bool: return f.whole),
		"%s: at every bar's step his head and the player are whole on screen (%s)" % [label, framed.map(func(f: Dictionary) -> bool: return f.whole)])
	var arrived: bool = await t.wait_until(func(): return seen.destination != "" and God.scene_is(t, seen.destination), 60 * 20)
	await God.idle_frames(t, 3)
	t.process_frame.disconnect(watch.step)
	t.process_frame.disconnect(track)
	t.log_p("%s: the beam's beats %s; his defeat's %s; progress %.2f, body hidden %s; outros %d to %s; arrival %s" % [label,
		seen.beats, seen.defeated, seen.progress, seen.body_hidden, watch.outros.size(), seen.destination.get_file(), seen.arrival])
	t.check(seen.beats.slice(-5) == [&"release", &"dissolve", &"fade", &"settle", &"won"] and is_equal_approx(seen.progress, 1.0)
		and seen.body_hidden, "%s: the beam fires and he dissolves all the way, his body gone" % label)
	check_shout(t, seen, label)
	t.check(watch.outros.size() == 1 and seen.won and seen.defeated == [&"", &"beam", &"leaving"],
		"%s: one won FightOutro, and his defeat goes straight out (%s)" % [label, seen.defeated])
	var arrival: Dictionary = seen.arrival
	t.check(arrived and not arrival.is_empty() and arrival.view == Transform2D.IDENTITY and arrival.time_scale == 1.0
		and arrival.base == 1.0 and arrival.zoom == 1.0 and arrival.shake == Vector2.ZERO,
		"%s: on to %s, the outro's own destination, with nothing of the view or the time scale carried over" % [label,
			seen.destination.get_file()])


# His shout over the disintegration: the user's line verbatim, his, in his demon portrait and voice, up as it starts,
# typed out inside it and gone as it ends, nothing pressed and no press-on arrow; and the disintegration and the fade after it on the beam's
# clock as before (2.41 s and 0.82 s measured without the shout, 2026-10-08).
static func check_shout(t, seen: Dictionary, label: String) -> void:
	var shout: Dictionary = seen.shout
	var clocks: Dictionary = seen.beat_clocks
	var dissolve: float = clocks.get(&"fade", 0.0) - clocks.get(&"dissolve", 0.0)
	var fade: float = clocks.get(&"settle", 0.0) - clocks.get(&"fade", 0.0)
	t.log_p("%s: his shout %s; the disintegration %.3f s, the fade %.3f s, the settle %.3f s" % [label, shout, dissolve, fade,
		clocks.get(&"won", 0.0) - clocks.get(&"settle", 0.0)])
	t.check(not shout.is_empty() and shout.text == SHOUT_LINE and shout.character == "Jordan" and shout.portrait.ends_with("portrait_demon.png")
		and shout.voiced, "%s: \"%s\" in his demon portrait and his voice" % [label, SHOUT_LINE])
	t.check(not shout.is_empty() and shout.from == &"dissolve" and shout.at <= 2.0 * FRAME and shout.typed == &"dissolve"
		and shout.beats == [&"dissolve"], "%s: up as the disintegration starts, typed out inside it (by %.2f s) with nothing pressed, and gone as it ends" % [
			label, shout.get("typed_at", -1.0)])
	# No press moves it on, so the balloon never shows its press-on arrow over it (balloon.gd: not while the input lock holds).
	t.check(not shout.is_empty() and shout.arrow_frames == 0, "%s: no press-on arrow on any frame it is up (%d)" % [label, shout.get("arrow_frames", -1)])
	t.check(absf(dissolve - Layout.DISSOLVE_TIME) <= 2.0 * FRAME and absf(fade - (Layout.PUNCH_THROUGH.time + Layout.BODY_FADE)) <= 2.0 * FRAME,
		"%s: the disintegration still %.2f s and the fade after it %.2f s on the beam's clock (%.3f, %.3f)" % [label,
			Layout.DISSOLVE_TIME, Layout.PUNCH_THROUGH.time + Layout.BODY_FADE, dissolve, fade])


#FAIL

static func tier_fail(t, drawn := true) -> void:
	var label := "fail" if drawn else "standin fail"
	var god: Node = await open_at_one(t, [God.STUB, God.STUB] as Array[String])
	var beam: Node = god.state_machine.final_beam
	var machine: Node = god.state_machine
	var seen := new_seen()
	var watch = Finale.Watch.new(t)
	var track := watcher(t, seen)
	t.process_frame.connect(watch.step)
	t.process_frame.connect(track)
	await God.punch_out(t, god)
	await t.wait_until(func(): return beam.mashing, 60 * 10)
	var mashed: Dictionary = await mash(t, beam, 9)
	var rotated: int = machine.rotation_log.size()
	var revived: bool = await t.wait_until(func(): return machine.current_state.name == "Idle", 60 * 10)
	await t.wait(30)
	var reached: float = Layout.FAIL_DISSOLVE[2]
	t.log_p("%s: %d presses, %d bars; beats %s; the beam's width %.2f, him apart to %.2f" % [label, mashed.presses, beam.bars,
		seen.beats, seen.width, seen.progress])
	t.check(beam.bars == 2 and beam.result == &"weak" and beam.fails == 1 and is_equal_approx(seen.width, Layout.FAIL_WIDTH[2])
		and absf(seen.progress - reached) <= 0.05,
		"%s: two bars, a weak beam at %.2f of its width, him coming apart to about %.2f" % [label, Layout.FAIL_WIDTH[2], reached])
	t.check(seen.shout.is_empty(), "%s: and no shout from him (%s)" % [label, seen.shout])
	var aura_back: bool = god.aura == null or (god.aura.visible and is_equal_approx(god.aura.modulate.a, 1.0))
	t.check(revived and god.body.material == null and god.body.visible and aura_back and god.body.position == Vector2.ZERO,
		"%s: and back whole: his body drawn, no material on it, his aura back" % label)
	t.check(god.boss_health == GodLayout.REVIVE_HEALTH
		and is_equal_approx(god.health_bar.rows[0].value, GodLayout.REVIVE_HEALTH) and god.revived
		and is_equal_approx(god.health_bar.modulate.a, 1.0),
		"%s: revived on %d of his bar, the HUD back (%d, %.0f, %.2f)" % [label, GodLayout.REVIVE_HEALTH, god.boss_health,
			god.health_bar.rows[0].value, god.health_bar.modulate.a])
	# Before the next attack, which seals the player again.
	var p: CharacterBody2D = t.player
	var view: Transform2D = t.root.canvas_transform
	t.check(not p.is_action_locked and p.sprite.visible and view.origin == BASE_ORIGIN and is_equal_approx(view.x.x, GodLayout.VIEW_ZOOM),
		"%s: the player free and drawn, the view on the fight's own (%s)" % [label, view])
	var next: bool = await t.wait_until(func(): return machine.rotation_log.size() > rotated, 60 * 5)
	t.check(next and machine.rotation_log[-1] == &"stub_combo_2", "%s: the next attack in turn (%s)" % [label, machine.rotation_log])
	if not drawn:
		t.process_frame.disconnect(watch.step)
		t.process_frame.disconnect(track)
		return
	await punch_out_on(t, machine.combos[1], 1)
	var again: bool = await t.wait_until(func(): return beam.entries == 2 and beam.mashing, 60 * 15)
	t.check(again and god.boss_health == 0, "fail: one uppercut of a one-bar punch-out takes his %d, and the beam is back (%d)" % [
		GodLayout.REVIVE_HEALTH, god.boss_health])
	await mash(t, beam, 6)
	var arrived: bool = await t.wait_until(func(): return seen.destination != "" and God.scene_is(t, seen.destination), 60 * 20)
	t.process_frame.disconnect(watch.step)
	t.process_frame.disconnect(track)
	t.check(arrived and watch.outros.size() == 1 and seen.won, "fail: the second beam wins and the game moves on to %s" % [
		seen.destination.get_file()])


# Never pressed: no beam, his laugh, and he is back.
static func tier_fizzle(t) -> void:
	var god: Node = await open_at_one(t, [God.STUB] as Array[String])
	var beam: Node = god.state_machine.final_beam
	var seen := new_seen()
	var track := watcher(t, seen)
	t.process_frame.connect(track)
	await God.punch_out(t, god)
	await t.wait_until(func(): return beam.mashing, 60 * 10)
	var revived: bool = await t.wait_until(func(): return god.state_machine.current_state.name == "Idle", 60 * 12)
	t.process_frame.disconnect(track)
	t.log_p("fizzle: beats %s, beam length %.0f, laughed %s, him %d" % [seen.beats, seen.length, seen.laughed, god.boss_health])
	t.check(revived and beam.result == &"fizzle" and beam.bars == 0 and seen.length == 0.0 and seen.laughed
		and god.boss_health == GodLayout.REVIVE_HEALTH and not t.player.is_action_locked and seen.shout.is_empty(),
		"fizzle: no presses, no beam, no shout; he laughs and is back on %d" % GodLayout.REVIVE_HEALTH)


#OFF

static func tier_off(t) -> void:
	var god: Node = await open_at_one(t, [God.STUB] as Array[String])
	var beam: Node = god.state_machine.final_beam
	var seen := new_seen()
	var track := watcher(t, seen)
	t.process_frame.connect(track)
	await God.punch_out(t, god)
	var entries: int = beam.entries if beam != null else 0
	await t.wait_until(func(): return seen.destination != "" and God.scene_is(t, seen.destination), 60 * 20)
	t.process_frame.disconnect(track)
	t.check(entries == 0 and seen.defeated == [&"", &"snap", &"crumple", &"dissolve", &"god", &"leaving"],
		"off: his defeat as it was (%s), the beam never entered" % [seen.defeated])


#PAUSE

static func tier_pause(t) -> void:
	var god: Node = await open_at_one(t, [God.STUB] as Array[String])
	var beam: Node = god.state_machine.final_beam
	var seen := new_seen()
	var track := watcher(t, seen)
	t.process_frame.connect(track)
	await God.punch_out(t, god)
	await t.wait_until(func(): return beam.mashing, 60 * 10)
	beam.min_press_interval = 0.0
	var pair: Array = MashInput.actions(t.player)
	var presses := 0
	while beam.bars < 1 and beam.mashing:
		t.tap(t.MASH_KEYS[pair[presses % 2]])
		presses += 1
		await t.wait(6)
	t.tap(t.MASH_KEYS[pair[presses % 2]])
	presses += 1
	await t.wait(2)
	await t.tap_pause()
	var held := {"clock": beam.meter.clock, "fill": beam.meter.meter, "zoom": ScreenView.zoom, "scale": t.root.canvas_transform.x.x}
	t.tap(t.MASH_KEYS[pair[presses % 2]])
	await t.wait(60)
	var after := {"clock": beam.meter.clock, "fill": beam.meter.meter, "zoom": ScreenView.zoom, "scale": t.root.canvas_transform.x.x}
	t.log_p("pause mid-mash: held %s, 60 frames on %s" % [held, after])
	t.check(t.paused and held == after, "paused mid-mash: the meter's clock and fill, and the view, hold; a press doesn't count")
	await t.tap_pause()
	await t.wait(12)
	var mashed: Dictionary = await mash(t, beam, 6)
	await t.wait_until(func(): return beam.beat == &"dissolve", 60 * 5)
	await t.wait(20)
	await t.tap_pause()
	var progress: float = beam.fx.progress
	var typed: int = beam.shout_balloon.dialogue_label.visible_characters if is_instance_valid(beam.shout_balloon) else -1
	await t.wait(60)
	var still: float = beam.fx.progress
	var still_typed: int = beam.shout_balloon.dialogue_label.visible_characters if is_instance_valid(beam.shout_balloon) else -1
	await t.tap_pause()
	t.check(beam.result == &"won" and progress > 0.0 and progress < 1.0 and still == progress,
		"paused mid-dissolve it holds (%.3f, then %.3f), after the mash finished (%d presses)" % [progress, still, mashed.presses])
	t.check(typed > 0 and typed < SHOUT_LINE.length() and still_typed == typed,
		"and his shout holds where it had typed to (%d letters, then %d)" % [typed, still_typed])
	var arrived: bool = await t.wait_until(func(): return seen.destination != "" and God.scene_is(t, seen.destination), 60 * 20)
	t.process_frame.disconnect(track)
	t.check(arrived, "and it finishes, on to %s" % seen.destination.get_file())
	check_shout(t, seen, "pause")
