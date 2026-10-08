extends RefCounted

# matt_echo_feint (E6, the X): --fixed-fps 60, the gauge held, the player at the smoke spot.
#   live      the live game since 2026-10-06 (the user: "get rid of the fake boom in that attack"): both feint knobs
#             off, no X planned in either phase over many draws, and a whole instance of each phase spawns no ghost,
#             punish, X badge or mark, and listens for no press
# The rest is the code kept behind the knobs, with an X forced on the first string's second roar:
#   left      every red pressed 0.12 s before its touch and the X left alone: its ghost touches as nothing, its
#             echo is a red like any other and parried, and nothing hits
#   bitten    a press 0.12 s before the ghost's touch bites: PSYCH! goes up, and its echo is a punish that even a
#             press 0.12 s before its touch can't parry - exactly one hit
#   late      a press landing inside echo_bite_grace after the ring before the X touched is a late press for that
#             ring, not a bite
#   placing   over many draws with each phase's knob turned on: one X a string, never on the instance's first roar
#   word      the word stands clear of the badge (PSYCH_WORD.badge_rect round its tip) on either side

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const FEINTS := [1, -1, -1, -1]


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	await live(t)
	await first_string(t, "left")
	await first_string(t, "bitten")
	await first_string(t, "late")
	placing(t)
	word(t)


# The live knobs: no X planned in either phase, and an instance of each, its rings left to land, makes none of the X's
# pieces.
static func live(t) -> void:
	var sm: Node = t.sm
	var planned := []
	for draw in 100:
		for two in [false, true]:
			sm.plan_echo(two)
			if sm.cycle_echo_feints.any(func(x): return x != -1):
				planned.append(sm.cycle_echo_feints.duplicate())
	t.log_p("live: knobs %s / %s; X planned over 100 draws a phase %s" % [sm.echo_feints_phase_one, sm.echo_feints_phase_two, planned.slice(0, 4)])
	t.check(not sm.echo_feints_phase_one and not sm.echo_feints_phase_two and planned.is_empty(),
		"live: both feint knobs off, and no X planned in either phase")
	for two in [false, true]:
		var label := "phase two" if two else "phase one"
		var echo: Node = await Lib.start(t, two)
		var marked := false
		var listened := false
		var ended := false
		for f in 2400:
			t.player.global_position = t.SMOKE_SPOTS["matt"]
			await t.physics_frame
			if sm.current_state != echo:
				ended = true
				break
			marked = marked or is_instance_valid(echo.mark)
			listened = listened or echo.listening or t.defense.block_pressed.is_connected(echo._on_block_pressed)
		var kinds := {}
		for birth in echo.births:
			kinds[birth[0]] = kinds.get(birth[0], 0) + 1
		var xs: int = echo.badges.filter(func(b): return b[0] == &"x").size()
		t.log_p("live %s: births %s, X badges %d, Xs %d, mark seen %s, listened %s" % [label, kinds, xs, echo.xs.size(), marked, listened])
		t.check(ended and kinds.get(&"red", 0) == 3 * echo.strings and kinds.get(&"ghost", 0) == 0 and kinds.get(&"punish", 0) == 0
			and xs == 0 and echo.xs.is_empty() and not marked and not listened,
			"live %s: every roar a red ring, no ghost, punish, X badge or mark, no press listener" % label)
	await Lib.reset(t)


# The first string, its six rings: every red and echo pressed on time; the X as `how` says.
static func first_string(t, how: String) -> void:
	var echo: Node = await Lib.start(t, true, FEINTS)
	var touches := []
	Lib.watch_touches(echo, touches)
	var spot: Vector2 = t.SMOKE_SPOTS["matt"]
	var pressed := {}
	var x_pressed := false
	var word_at := Vector2.INF
	t.events.clear()
	for f in 900:
		t.player.global_position = spot
		t.clear_iframes()
		for ring in echo.rings:
			if not is_instance_valid(ring) or ring.answered or pressed.has(ring.get_instance_id()):
				continue
			if ring.kind == Lib.GHOST:
				continue
			var due: float = Lib.contact_in(t, ring)
			if due >= 0.0 and due <= 0.12:
				pressed[ring.get_instance_id()] = true
				t.tap(KEY_SHIFT)
		if not x_pressed and echo.xs.size() > 0:
			var x: Dictionary = echo.xs[0]
			if how == "bitten" and x.ring != null and is_instance_valid(x.ring) and not x.ring.answered:
				var due: float = Lib.contact_in(t, x.ring)
				if due >= 0.0 and due <= 0.12:
					x_pressed = true
					t.tap(KEY_SHIFT)
			elif how == "late" and x.prev_touch > 0.0 and t.defense.clock >= x.prev_touch + 0.06:
				x_pressed = true
				t.tap(KEY_SHIFT)
		await t.physics_frame
		if word_at == Vector2.INF:
			for node in t.boss.projectile_layer.get_children():
				if str(node.name).begins_with("PsychWord"):
					word_at = node.global_position
		if touches.size() >= 6:
			break
	var results: Array = touches.slice(0, 6).map(func(x): return [x[0], x[1]])
	var hits: int = touches.slice(0, 6).filter(func(x): return x[1] == Lib.HitInfo.Result.HIT).size()
	t.log_p("%s: the first string's rings [kind, result] %s; bites %d, hits %d, the word at %s" % [how, results, echo.bites, hits, word_at])
	var ghost: Array = results[2] if results.size() > 2 else []
	var after: Array = results[3] if results.size() > 3 else []
	match how:
		"left":
			t.check(echo.bites == 0 and hits == 0 and ghost == [Lib.GHOST, Lib.HitInfo.Result.IGNORED] and after == [Lib.ECHO, Lib.HitInfo.Result.PARRIED],
				"the X left alone: its ghost touches as nothing, its echo is parried, nothing hits")
		"bitten":
			t.check(echo.bites == 1 and word_at != Vector2.INF, "a press 0.12 s before the ghost's touch bites, and PSYCH! goes up")
			t.check(hits == 1 and after == [Lib.PUNISH, Lib.HitInfo.Result.HIT],
				"its echo is a punish a press on time can't parry: exactly one hit (%s)" % [after])
			t.check(word_at == echo.word_box(0).get_center(), "the word stands where word_box puts it (%s)" % word_at)
		"late":
			t.check(echo.bites == 0 and after == [Lib.ECHO, Lib.HitInfo.Result.PARRIED],
				"a press inside echo_bite_grace after the ring before the X is a late press for it, not a bite")
	await Lib.reset(t)


static func placing(t) -> void:
	var sm: Node = t.sm
	var knobs := [sm.echo_feints_phase_one, sm.echo_feints_phase_two]
	sm.echo_feints_phase_one = true
	sm.echo_feints_phase_two = true
	var wrong := []
	for draw in 300:
		sm.plan_echo(true)
		var f: Array = sm.cycle_echo_feints
		if f.size() != sm.echo_strings_phase_two or not (f[0] in [1, 2]) or f.any(func(x): return not (x in [0, 1, 2])):
			wrong.append(f.duplicate())
	var wrong_one := []
	for draw in 100:
		sm.plan_echo(false)
		var f: Array = sm.cycle_echo_feints
		if f.size() != sm.echo_strings or not (f[0] in [1, 2]) or f.any(func(x): return not (x in [0, 1, 2])):
			wrong_one.append(f.duplicate())
	sm.echo_feints_phase_one = knobs[0]
	sm.echo_feints_phase_two = knobs[1]
	t.log_p("the knobs on: 300 phase-two draws, wrong %s; 100 phase-one draws, wrong %s" % [wrong.slice(0, 4), wrong_one.slice(0, 4)])
	t.check(wrong.is_empty() and wrong_one.is_empty(), "with each phase's knob on, one X a string, never on the instance's first roar")


static func word(t) -> void:
	var sm: Node = t.sm
	var echo: Node = sm.states["EchoRoars"]
	t.boss.global_position = sm.HOME
	var tip: Vector2 = t.boss.tell_anchor(&"echo_inhale")
	var spec := MattArtLayout.PSYCH_WORD
	var badge := Rect2(tip + spec.badge_rect.position, spec.badge_rect.size)
	var boxes := [echo.word_box(0), echo.word_box(1)]
	t.log_p("the badge round its tip %s: %s; the word %s and %s" % [tip, badge, boxes[0], boxes[1]])
	t.check(not boxes[0].intersects(badge) and not boxes[1].intersects(badge) and Rect2(0, 0, 1920, 1080).encloses(boxes[0])
		and Rect2(0, 0, 1920, 1080).encloses(boxes[1]), "PSYCH! stands clear of the badge, in view, on either side")
