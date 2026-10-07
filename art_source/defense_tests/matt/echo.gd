extends RefCounted

# matt_echo (the Echo Roars, 2026-10-04): his third attack's shape. --fixed-fps 60, the gauge held.
#   strings   a phase-one instance is echo_strings strings and phase two's echo_strings_phase_two, each three roars,
#             three echoes and echo_boombursts BOOMBURSTs (two since 2026-10-06), with one ghost a string only in a phase whose feint knob is on
#             (MattStateMachine.echo_feints_phase_one/two): none in the live game since 2026-10-06
#   grid      every ring born on its beat (MattStateMachine.echo_beat): roars on 0, 2 and 4 of a string, their echoes a
#             beat behind, the BOOMBURSTs from echo_boomburst_beat echo_boomburst_spacing_beats apart, strings
#             echo_string_beats apart after a lead-in of
#             echo_first_lead_beats; each spawned on the step its beat falls in, so no more than a step late
#   badges    each up for its lead and gone at its ring's birth: a roar's 1 beat, a string's first roar's 2, the
#             BOOMBURST's 1.5 in yellow, and an X's the same as the red it stands in for
#   HOME      he stands at HOME, unflipped, his hurtbox off, through every step of the strings
#   end       into Recover only once every ring is gone
#   Break     a Break mid-string frees every ring, the badge, the X, the press listener and the stamina floor

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	await shape(t, false)
	await shape(t, true)
	await break_mid_string(t)


static func shape(t, two: bool) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var echo: Node = await Lib.start(t, two)
	var label := "phase two" if two else "phase one"
	var at_home := true
	var hurtbox_off := true
	var badge_seen := {}
	var badge_gone_at_birth := true
	var badges_logged := 0
	var births_logged := 0
	var ended_clean := false
	var gone_in := 0
	for f in 2400:
		await t.physics_frame
		if sm.current_state != echo:
			ended_clean = sm.current_state.name == "Recover" and echo.rings.all(func(r): return not is_instance_valid(r) or not r.is_live())
			break
		if echo.beat == echo.Beat.STRINGS:
			at_home = at_home and boss.global_position == sm.HOME and not boss.sprite.flip_h
			hurtbox_off = hurtbox_off and not boss.hurtbox.monitoring
		# A badge event this step: its badge (or the X) up on this step.
		while badges_logged < echo.badges.size():
			var badge: Array = echo.badges[badges_logged]
			badges_logged += 1
			var up: bool = is_instance_valid(echo.mark) if badge[0] == &"x" else live_tell(t) != null
			badge_seen[badges_logged - 1] = up
		while births_logged < echo.births.size():
			var birth: Array = echo.births[births_logged]
			births_logged += 1
			if birth[0] != &"echo" and birth[0] != &"punish" and live_tell(t) != null:
				badge_gone_at_birth = false
	var b: float = sm.echo_beat()
	var expect_strings: int = sm.echo_strings_phase_two if two else sm.echo_strings
	var xs_on: bool = sm.echo_feints_phase_two if two else sm.echo_feints_phase_one
	var kinds := {}
	for birth in echo.births:
		kinds[birth[0]] = kinds.get(birth[0], 0) + 1
	var grid_ok := true
	var late_max := 0.0
	var expected := []
	for s in expect_strings:
		var first: float = (sm.echo_first_lead_beats + s * sm.echo_string_beats) * b
		for slot in 3:
			expected.append(first + 2.0 * slot * b)
			expected.append(first + (2.0 * slot + 1.0) * b)
		for i in sm.echo_boombursts:
			expected.append(first + (sm.echo_boomburst_beat + i * sm.echo_boomburst_spacing_beats) * b)
	expected.sort()
	for i in echo.births.size():
		var birth: Array = echo.births[i]
		late_max = maxf(late_max, birth[2] - birth[1])
		if i >= expected.size() or absf(birth[1] - expected[i]) > 0.0001 or birth[2] < birth[1] - 0.0001 or birth[2] - birth[1] > 1.0 / 60.0 + 0.0001:
			grid_ok = false
	var leads_ok := true
	for badge in echo.badges:
		var want: float = 1.5 * b if badge[0] == &"yellow" else b
		# A string's first roar leads by two beats.
		if badge[0] != &"yellow":
			var into: float = fposmod(badge[1] + 2.0 * b - sm.echo_first_lead_beats * b, sm.echo_string_beats * b)
			if absf(into) < 0.001 or absf(into - sm.echo_string_beats * b) < 0.001:
				want = sm.echo_first_lead_beats * b
		if absf(badge[2] - want) > 0.0001:
			leads_ok = false
	var xs: int = echo.badges.filter(func(x): return x[0] == &"x").size()
	t.log_p("%s: %d strings, births %s, latest spawn %.4f s past its beat; %d badges (%d Xs), up on their step %s; ended clean %s" % [
		label, echo.strings, kinds, late_max, echo.badges.size(), xs, badge_seen.values().all(func(v): return v), ended_clean])
	t.check(echo.strings == expect_strings and kinds.get(&"red", 0) + kinds.get(&"ghost", 0) == 3 * expect_strings \
		and kinds.get(&"echo", 0) == 3 * expect_strings and kinds.get(&"boomburst", 0) == expect_strings * sm.echo_boombursts \
		and kinds.get(&"ghost", 0) == (expect_strings if xs_on else 0),
		"%s: %d strings of three roars, three echoes and %d BOOMBURSTs, with %s ghosts (%s)" % [label, expect_strings, sm.echo_boombursts,
			"one a string" if xs_on else "no", kinds])
	t.check(grid_ok, "%s: every ring born on its beat of %.4f s, spawned no more than a step past it (%.4f s)" % [label, b, late_max])
	t.check(leads_ok and xs == (expect_strings if xs_on else 0), "%s: badges lead by a beat, a string's first roar's by %.0f, the BOOMBURST's by %.1f, an X's as the red it stands in for" % [
		label, sm.echo_first_lead_beats, sm.echo_yellow_lead_beats])
	t.check(badge_seen.values().all(func(v): return v) and badge_gone_at_birth, "%s: each badge up on its step and gone at its ring's birth" % label)
	t.check(at_home and hurtbox_off, "%s: at HOME, unflipped, his hurtbox off through every step" % label)
	t.check(ended_clean, "%s: into Recover only once every ring is gone" % label)


# His live badge (ParryTell), if one is up and not on its way out.
static func live_tell(t) -> Node:
	for child in t.boss.get_parent().get_children():
		var named := str(child.name)
		if named.begins_with("ParryTell") and not named.ends_with("Spent") and not child.fading:
			return child
	return null


static func break_mid_string(t) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var echo: Node = await Lib.start(t, true, [1, 0, 2, 1])
	var gauge: Node = boss.break_gauge
	# Into the first string's X: its mark up, a ring or two out.
	await t.wait_until(func(): return is_instance_valid(echo.mark) and not sm.live_echo_rings().is_empty(), 600)
	var before := {"rings": sm.live_echo_rings().size(), "mark": is_instance_valid(echo.mark), "listening": echo.listening}
	gauge.locked = false
	gauge.add(gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state.name == "Broken", 30)
	await t.wait(2)
	t.defense._set_stamina(5.0)
	await t.wait(3)
	var after := {"rings": sm.live_echo_rings().size(), "badge": live_tell(t) != null, "mark": is_instance_valid(echo.mark),
		"listening": t.defense.block_pressed.is_connected(echo._on_block_pressed), "stamina": snappedf(t.defense.stamina, 0.1),
		"hint": is_instance_valid(echo.hint), "marks": boss.get_parent().find_children("EchoMark", "", true, false).size()}
	t.log_p("a Break mid-string: before %s, after %s" % [before, after])
	t.check(broke and before.rings > 0 and before.mark and before.listening, "a Break lands mid-string, rings out and the X up")
	t.check(after.rings == 0 and not after.badge and not after.mark and after.marks == 0 and not after.listening and after.stamina < sm.echo_stamina_floor and not after.hint,
		"and frees every ring, the badge, the X, the press listener and the stamina floor (%s)" % [after])
	gauge.locked = true
	await Lib.reset(t)
