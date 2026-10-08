extends RefCounted

# stamina_costs: what the stamina bar charges and when, as the game ships, blocking off (the user's
# playtest, 2026-09-27). On Eric's fight with him parked, so every hit is a scripted one. --fixed-fps 60.
#   dash      a dash is a third of the bar: three from a full bar, and the fourth refused, with the bar's
#             red flash and the tired breath, and no dash.
#   regen     after the last spend the bar holds for stamina_regen_delay, then refills at
#             max_stamina / stamina_refill_time, empty to full in stamina_refill_time.
#   whiff     a press with nothing to parry costs nothing until its window is over, then parry_whiff_share of
#             the bar, once, and the refill's delay runs from then.
#   early     a press whose window ran out before the hit: the hit lands, and the press paid its whiff.
#   late      the hit lands, then the press: the press pays its whiff.
#   parry     a press that parries is free: not a point off the bar, and the refill's delay not restarted.
#   rearmed   a fight's rearm_parry() (Carter's clone lights) ends a press's window, so it pays on the next step.
#   mash      presses a few frames apart each pay as the next one ends them: five from a full bar, the sixth
#             refused, and the bar empty once the fifth's window is over.
#   refused   below the whiff a press is refused: the flash and the breath, no block_pressed, no guard, no
#             window, and the hit it would have parried lands.
#   priced    a fight that charges for a press itself in its answer to block_pressed (Carter's bitten feint)
#             charges its own price in place of the whiff, not both.
#   blocking  with blocking on a missed press costs nothing: it buys a block, whose cost is its price.
#   bar       the HUD bar follows the stamina to the texel, shows its low look below the dash cost and not
#             above it, and never dims with blocking off.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

const FRAME := 1.0 / 60.0
const PLAYER_AT := Vector2(960, 800)
# A light projectile any fresh press parries from the front.
const PARRYABLE := &"mason_poo_blast"


static func run(t) -> void:
	load(t.PLAYER_DEFENSE).BLOCKING_ENABLED = false
	await t.load_eric()
	t.park_eric()
	t.health_ok()
	t.track()
	t.track_parries()
	var defense: Node = t.defense
	var refusals := [0]
	defense.stamina_refused.connect(func(): refusals[0] += 1)
	var presses := []
	defense.block_pressed.connect(func(credited: bool): presses.append(credited))
	await t.settle_player(PLAYER_AT)
	t.log_p("dash %.4f of the bar (%.2f), a missed parry %.4f (%.2f), the refill held %.2f s after a spend, then empty to full in %.2f s"
		% [defense.dash_stamina_share, defense.dash_stamina_cost, defense.parry_whiff_share, defense.parry_whiff_cost, defense.stamina_regen_delay, defense.stamina_refill_time])
	t.check(is_equal_approx(defense.dash_stamina_cost * 3.0, defense.max_stamina), "a dash is a third of the bar (%.2f)" % defense.dash_stamina_cost)

	t.log_p("-- dash: three from a full bar, the fourth refused")
	await dashes(t, refusals)
	var spent_at: float = defense.last_spend_time
	await regen(t, spent_at)

	t.log_p("-- whiff: a press with nothing to parry")
	await whiff(t)

	t.log_p("-- early: the window ran out before the hit")
	await fresh(t)
	t.tap(KEY_SHIFT)
	await t.past_window()
	t.check(is_equal_approx(defense.stamina, defense.max_stamina - defense.parry_whiff_cost), "the press paid its whiff as its window closed (%.1f)" % defense.stamina)
	t.clear_iframes()
	var early: int = t.front_hit(PARRYABLE, t.dummy_source())
	await t.wait(3)
	t.check(early == HitInfo.Result.HIT and is_equal_approx(defense.stamina, defense.max_stamina - defense.parry_whiff_cost),
		"the hit lands, and nothing more comes off (%s, %.1f)" % [HitInfo.Result.keys()[early], defense.stamina])

	t.log_p("-- late: the hit, then the press")
	await fresh(t)
	t.clear_iframes()
	var late: int = t.front_hit(PARRYABLE, t.dummy_source())
	t.tap(KEY_SHIFT)
	await t.wait(2)
	var owed: bool = defense.whiff_owed and is_equal_approx(defense.stamina, defense.max_stamina)
	await t.past_window()
	t.check(late == HitInfo.Result.HIT and owed and is_equal_approx(defense.stamina, defense.max_stamina - defense.parry_whiff_cost),
		"the hit lands, and the press after it pays its whiff once its window is over (%s, %s, %.1f)" % [HitInfo.Result.keys()[late], owed, defense.stamina])

	t.log_p("-- parry: a press that parries is free")
	await fresh(t)
	t.clear_iframes()
	var held_until: float = defense.last_spend_time
	# Held through the hit: without blocking the guard is only up while the key is down, inside the window.
	t.press(KEY_SHIFT)
	await t.wait(2)
	var parried: int = t.front_hit(PARRYABLE, t.dummy_source())
	t.release(KEY_SHIFT)
	await t.past_window()
	await t.wait(20)
	t.check(parried == HitInfo.Result.PARRIED and not defense.whiff_owed, "it parries (%s)" % HitInfo.Result.keys()[parried])
	t.check(is_equal_approx(defense.stamina, defense.max_stamina) and defense.last_spend_time == held_until,
		"not a point off the bar, and the refill's delay untouched (%.1f)" % defense.stamina)

	t.log_p("-- rearmed: a fight opening the next read ends the press's window, and it pays then")
	await fresh(t)
	t.tap(KEY_SHIFT)
	await t.wait(3)
	var owed_before: bool = defense.whiff_owed and is_equal_approx(defense.stamina, defense.max_stamina)
	defense.rearm_parry()
	await t.wait(2)
	t.check(owed_before and not defense.whiff_owed and is_equal_approx(defense.stamina, defense.max_stamina - defense.parry_whiff_cost),
		"paid on the step after the rearm, not at the window's end (%.1f)" % defense.stamina)

	t.log_p("-- mash: a press every few frames")
	await mash(t, refusals, presses)

	t.log_p("-- refused: below the whiff")
	await refused(t, refusals, presses)

	t.log_p("-- priced: a fight's own price for a press stands in for the whiff")
	await fresh(t)
	var feint_price := 40.0
	var price := func(_credited: bool): defense.drain_stamina(feint_price)
	defense.block_pressed.connect(price)
	t.tap(KEY_SHIFT)
	await t.past_window()
	await t.wait(3)
	defense.block_pressed.disconnect(price)
	t.check(is_equal_approx(defense.stamina, defense.max_stamina - feint_price), "%.0f off the bar, its price alone (%.1f)" % [feint_price, defense.stamina])

	t.log_p("-- blocking on: a missed press buys a block, and costs nothing itself")
	await fresh(t)
	load(t.PLAYER_DEFENSE).BLOCKING_ENABLED = true
	t.tap(KEY_SHIFT)
	await t.wait(2)
	var owed_with_blocking: bool = defense.whiff_owed
	await t.wait(roundi(defense.parry_window / FRAME) + 10)
	load(t.PLAYER_DEFENSE).BLOCKING_ENABLED = false
	t.check(not owed_with_blocking and is_equal_approx(defense.stamina, defense.max_stamina), "nothing owed and nothing paid (%.1f)" % defense.stamina)

	t.log_p("-- bar: blocking off")
	await bar(t)


# A full bar, the refill held off so every cost reads exactly, and the last press's lockout run out.
static func fresh(t) -> void:
	var defense: Node = t.defense
	await t.wait_until(func(): return not defense.whiff_owed and t.defense.clock - defense.last_press_time > defense.parry_mash_lockout, 120)
	defense._set_stamina(defense.max_stamina)
	defense.last_spend_time = defense.clock + 100.0
	await t.wait(2)


static func dashes(t, refusals: Array) -> void:
	var defense: Node = t.defense
	var player: Node = t.player
	defense._set_stamina(defense.max_stamina)
	defense.last_spend_time = -INF
	var costs := []
	for i in 3:
		await t.wait_until(func(): return not defense.is_dash_cooling_down() and not defense.is_dash_recovering() and not player.is_dodging, 120)
		var way: int = KEY_RIGHT if i % 2 == 0 else KEY_LEFT
		var before: float = defense.stamina
		t.press(way)
		t.tap(KEY_W)
		await t.wait(1)
		costs.append(snappedf(before - defense.stamina, 0.001))
		await t.wait_until(func(): return not player.is_dodging, 30)
		t.release(way)
	t.log_p("three dashes cost %s, leaving %.4f" % [costs, defense.stamina])
	t.check(costs.all(func(c): return is_equal_approx(c, snappedf(defense.dash_stamina_cost, 0.001))) and defense.stamina < 0.01,
		"each a third of the bar, and the three empty it (%s, %.4f left)" % [costs, defense.stamina])
	await t.wait_until(func(): return not defense.is_dash_cooling_down() and not defense.is_dash_recovering(), 120)
	var bar: Control = t.current_scene.get_node("Arena/MainPlayer/CanvasLayer/StaminaBar")
	var breath: AudioStreamPlayer = player.get_node("CombatFx/TiredSfxPlayer")
	var refused_before: int = refusals[0]
	var frame_before: int = player.last_dodge_physics_frame
	var stamina_before: float = defense.stamina
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait(1)
	t.release(KEY_RIGHT)
	t.check(refusals[0] == refused_before + 1 and not player.is_dodging and player.last_dodge_physics_frame == frame_before and defense.stamina == stamina_before,
		"the fourth is refused: no dash, nothing spent (%d refusals, dodging %s)" % [refusals[0] - refused_before, player.is_dodging])
	check_refusal_feedback(t, bar, breath)


# The bar's red flash and the tired breath, on the voice of its own.
static func check_refusal_feedback(t, bar: Control, breath: AudioStreamPlayer) -> void:
	var sound: Dictionary = DefenseHypeArtLayout.TIRED_SFX
	var stream_path: String = breath.stream.resource_path if breath.stream else ""
	t.check(bar.modulate != Color.WHITE, "the bar flashes (%s)" % bar.modulate)
	t.check(breath.playing and stream_path == sound.stream and is_equal_approx(breath.pitch_scale, sound.pitch),
		"and the tired breath plays (%s at %.2f, playing %s)" % [stream_path.get_file(), breath.pitch_scale, breath.playing])


# From the last spend: the delay, the rate, and empty to full.
static func regen(t, spent_at: float) -> void:
	var defense: Node = t.defense
	var first := -1.0
	var samples := {}
	for i in 90:
		var before: float = defense.stamina
		await t.physics_frame
		var since: float = defense.clock - spent_at
		if first < 0.0 and defense.stamina > before:
			first = since
		samples[snappedf(since, 0.0001)] = defense.stamina
	var delay: float = defense.stamina_regen_delay
	t.log_p("the refill first seen %.4f s after the spend" % first)
	t.check(first >= delay - 0.001 and first <= delay + FRAME + 0.001, "the refill starts %.2f s after the spend (%.4f)" % [delay, first])
	var rate: float = defense.max_stamina / defense.stamina_refill_time
	var at := 0.0
	for since in samples:
		if since >= delay + 0.5 and at == 0.0:
			at = since
	var want: float = rate * (at - delay + FRAME)
	t.check(absf(samples[at] - want) <= rate * FRAME + 0.01, "then refills at %.2f a second (%.2f at %.3f s, want %.2f)" % [rate, samples[at], at, want])
	var full: bool = await t.wait_until(func(): return defense.stamina >= defense.max_stamina, roundi(defense.stamina_refill_time / FRAME) + 60)
	var took: float = defense.clock - spent_at - delay
	t.check(full and absf(took - defense.stamina_refill_time) <= 2.0 * FRAME, "empty to full in %.2f s of refilling (%.3f)" % [defense.stamina_refill_time, took])


static func whiff(t) -> void:
	var defense: Node = t.defense
	await fresh(t)
	t.press(KEY_SHIFT)
	await t.wait(2)
	var pressed_at: float = defense.last_press_time
	t.check(defense.whiff_owed and defense.is_guarding() and is_equal_approx(defense.stamina, defense.max_stamina), "pressed and held: owed, the guard up, nothing paid yet")
	var drops := []
	for i in 40:
		var before: float = defense.stamina
		await t.physics_frame
		if defense.stamina < before:
			drops.append({"since": defense.clock - pressed_at, "amount": before - defense.stamina})
	t.release(KEY_SHIFT)
	t.log_p("drops %s" % [drops])
	t.check(drops.size() == 1 and is_equal_approx(drops[0].amount, defense.parry_whiff_cost), "paid once, the whiff (%s)" % [drops])
	if drops.size() == 1:
		t.check(drops[0].since > defense.parry_window and drops[0].since <= defense.parry_window + FRAME + 0.001,
			"on the step after its %.2f s window ran out (%.4f)" % [defense.parry_window, drops[0].since])
	t.check(defense.clock - defense.last_spend_time < 40.0 * FRAME, "and the refill's delay runs from the payment")


static func mash(t, refusals: Array, presses: Array) -> void:
	var defense: Node = t.defense
	await fresh(t)
	presses.clear()
	var refused_before: int = refusals[0]
	for i in 6:
		t.tap(KEY_SHIFT)
		await t.wait(3)
	var refused_now: int = refusals[0] - refused_before
	var taken: Array = presses.duplicate()
	await t.past_window()
	await t.wait(3)
	t.log_p("presses taken %s, refused %d, bar %.3f" % [taken, refused_now, defense.stamina])
	t.check(taken == [true, false, false, false, false] and refused_now == 1, "five taken, the first the only one credited, and the sixth refused (%s, %d)" % [taken, refused_now])
	t.check(defense.stamina < 0.01, "five whiffs, the bar empty (%.3f)" % defense.stamina)


static func refused(t, refusals: Array, presses: Array) -> void:
	var defense: Node = t.defense
	var player: Node = t.player
	await fresh(t)
	defense._set_stamina(defense.parry_whiff_cost - 5.0)
	await t.wait(20)
	presses.clear()
	var bar: Control = t.current_scene.get_node("Arena/MainPlayer/CanvasLayer/StaminaBar")
	var breath: AudioStreamPlayer = player.get_node("CombatFx/TiredSfxPlayer")
	var refused_before: int = refusals[0]
	var last_press: float = defense.last_press_time
	t.clear_iframes()
	# Held, so a guard would be up for the hit if the press had been taken.
	t.press(KEY_SHIFT)
	await t.wait(2)
	var result: int = t.front_hit(PARRYABLE, t.dummy_source())
	var guard_state: String = player.state_machine.current_state.name
	var guarding: bool = defense.is_guarding()
	t.release(KEY_SHIFT)
	t.check(refusals[0] == refused_before + 1 and presses.is_empty() and defense.last_press_time == last_press and not defense.whiff_owed,
		"refused: no block_pressed, no window, nothing owed (%d refusals, %d presses)" % [refusals[0] - refused_before, presses.size()])
	t.check(not guarding and guard_state != "Blocking", "and no guard, the key held (%s)" % guard_state)
	t.check(result == HitInfo.Result.HIT and is_equal_approx(defense.stamina, defense.parry_whiff_cost - 5.0),
		"the hit it would have parried lands, and nothing is spent (%s, %.1f)" % [HitInfo.Result.keys()[result], defense.stamina])
	check_refusal_feedback(t, bar, breath)


static func bar(t) -> void:
	var defense: Node = t.defense
	var bar_ui: Control = t.current_scene.get_node("Arena/MainPlayer/CanvasLayer/StaminaBar")
	var spec: Dictionary = DefenseHypeArtLayout.stamina()
	var texel: float = defense.max_stamina / spec.get("fill_texels", 1000000)
	await fresh(t)
	t.tap(KEY_SHIFT)
	await t.wait(2)
	var dimmed: bool = bar_ui.bar.self_modulate != Color.WHITE
	await t.past_window()
	await t.wait(12)
	t.check(not dimmed, "the guard up dims nothing")
	t.check(absf(bar_ui.bar.value - defense.stamina) <= texel + 0.001, "it shows the bar after the whiff (%.2f for %.2f)" % [bar_ui.bar.value, defense.stamina])
	var looks := {}
	for value in [defense.dash_stamina_cost + 5.0, defense.dash_stamina_cost - 5.0]:
		defense._set_stamina(value)
		await t.wait(3)
		looks[value] = bar_ui.low_textures.has(bar_ui.bar.texture_progress) if bar_ui.broken_overlay else bar_ui.fill_style.bg_color == spec.low_color
	t.check(looks.values() == [false, true], "its low look below the dash cost and not above it (%s)" % [looks])
