extends RefCounted

# bixby_flyby (the user, 2026-09-29): beast Bixby's Flyby (BixbyBeastFlyby), the fire pass across the top of the ring
# that replaced his chasing fire breath, in his fight. --fixed-fps 60, one tier a run (tier=; normal is layout). Every
# Flyby here is forced from Idle after a reset, him parked hovering at (960, 640), pass 0 from flyby_start_side, his
# hovers held so nothing else of his starts, and his gauge held but in perfect and break. Every number is read off
# BixbyFlybyLayout and his flyby_* exports.
#   layout    invariants(sm) empty; the catalogue's two entries exactly as planned; his gauge fills from the curtain
#             and only drains on the burning floor; ATTACK_CYCLES as it ships, with no FireBreath; both ways, the safe
#             column at the far edge, flyby_safe_width wide, and with the burnable span the whole floor; the layout's
#             player numbers the game's. For pass 0 from its side rule's worst start and the crossing from the rope and
#             from the column's inner edge, logs when a walk from a 0.25 s reaction gets into the column, when the front
#             does, the spare and the walking reaction budget: every spare is CROSS_SPARE or more.
#   still     a player who never moves, at five spots, pass 0 from the left and then the right: every beat on its
#             scheduled frame; one bixby_flyby_breath a pass for a spot in its burnable span, on the frame the spans
#             predict (+-1), none in its column and none while only the projection is up, half a heart each; then Land,
#             and Recover on his landing point for recover_time. &"away" starts pass 0 from the side away from them.
#   edges     both ways, on the passes of one Flyby: a hurtbox 1 px inside the burnable span at the column's edge is
#             hit and one flush with it never is; one hugging the entry rope is hit on the front's first frame. Every
#             frame: the projection at its beat is the burnable span over the floor, the burn and die-down masks never
#             leave it, and the curtain's mask is curtain_span() (0.5 px) from exit_y() to the floor's bottom edge.
#   run       pass 0 from five starts, &"away" as it ships, walking into the column its start side leaves from a 0.25 s
#             reaction to its projection: never hit (the spare logged); pass 1 from the rope and from the column's inner
#             edge, walking across from a 0.25 s reaction to its projection: never hit, and in the column CROSS_SPARE
#             or more before the front reaches it from the rope, and from the inner edge that and the column's width
#             less a body's walk more (0.43 s since the faster Flyby of 2026-10-04; 0.7 s before), logged beside the
#             layout's arrival_spare.
#   late      the crossing's boundaries, at the arrival: from the rope, setting off 2 frames before the latest a walk
#             gets into the column first (sweep_end() less the walk) is never hit and 2 frames after is hit once, by the
#             curtain; from the column's inner edge the same. From the rope, setting off DASH_RUN_SET_OFF into the
#             projection, 0.6 s past a walk's budget, with three dashes on the way: never hit, the stamina's low logged.
#   perfect   his gauge live: from 1450, a dash forward into the column with the front 4 frames of it behind is no hit,
#             one PERFECT DODGE of the curtain, the dash given back and one read on his gauge; the same into pass 1's
#             column from 470 is a second read, one a pass. A dash back through the front from 4 frames of it ahead is
#             DODGED, then one hit of the floor as its immunity ends; hit at 1450, the i-frames cleared, a dash into the
#             column across the floor still burning is DODGED, no hit, no PERFECT DODGE, the dash paid for.
#   draw      every frame of a Flyby from each side: on a pass he sorts at the rope line with no shadow, his feet at
#             y 300, nothing drawn below y 321, and while the projection is up nothing of him from y 105 down ahead of
#             the front; the fire's layers sort at 101, 114.5 and 115, under the player, the rim on the column's edge;
#             the bar and the gauge at the fade from the rise and at full from the return, each once HUD_FADE_TIME has
#             run; no fire left half a second after the return.
#   break     a Break in the rise, on each projection, in each sweep with the curtain out and in the return: Broken
#             within 2 frames at hover height, no fire and no badge, the bar at full, his shadow back, his feet in
#             ground_bounds(0) once he is down, and Takeoff after the window.
#   release   paused and frozen mid-sweep (half the sweep in): nothing of it moves, and the front still reaches the
#             column's edge on the state's own clock as scheduled; through a hit-stop mid-sweep his lead exit stays on
#             the mouth every frame; last, a player at 1 health killed by the curtain: no fire or badge, Idle with
#             player_defeated, hovering with his shadow, the bar coming back and at full through the outro.
#   art       the pass pose's sheet and the curtain's, where they are in: 192x160 frames, as many as ANIMS plays,
#             FINAL_EXITS on every breath frame, the lead exit where FINAL_LEAD_EXIT says (its row +-2) in rows 78-112,
#             nothing below row 157 and nothing right of the lead exit from row 86 down; a curtain 32 texels wide.
#             "placeholders in use" and a pass for any that aren't. art_approval runs it on the art pass's approval
#             folder, read off disk, with its contract.json's numbers where it has them.

const Layout := preload("res://Scripts/BixbyFlybyLayout.gd")
const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const TIERS := ["layout", "still", "edges", "run", "late", "perfect", "draw", "break", "release", "art", "art_approval"]
# The gauge spec's home, and where he hovers as each Flyby starts.
const HOME := Vector2(960, 760)
const HOVER_AT := Vector2(960, 640)
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
# A press reaches the player on the next frame's input flush, so a bot presses this early to set off on the moment.
const PRESS_LEAD := FRAME
const KEYS := [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]
const STILL_SPOTS: Array[Vector2] = [Vector2(140, 540), Vector2(600, 300), Vector2(960, 640), Vector2(1400, 850),
	Vector2(1780, 540)]
const RUN_STARTS: Array[Vector2] = [Vector2(123, 540), Vector2(500, 850), Vector2(960, 640), Vector2(1300, 400),
	Vector2(1600, 900)]
const CROSSING_Y := 640.0
# The dashed crossing sets off this far into its projection, 0.6 s past a walk's budget (0.40 s since the faster Flyby
# of 2026-10-04; it was 1.3 against 0.69 before), with three dashes' 0.85 s of saving to make it up.
const DASH_RUN_SET_OFF := 1.0
# A close dash goes with the front this many frames from the hurtbox.
const PERFECT_FRAMES := 4.0
const PERFECT_HIT_X := 1450.0
const APPROVAL_DIR := "res://art_source/bixby_flyby/approval/"


static func run(t) -> void:
	var tier: String = "layout" if t.tier == "normal" else t.tier
	if not tier in TIERS:
		t.check(false, "tier is one of %s (%s)" % [TIERS, tier])
		return
	if tier.begins_with("art"):
		_art(t, tier == "art_approval")
		return
	t.fight = "liam"
	if not await t.load_gauged():
		return
	t.track()
	t.track_dodges()
	t.sm.hover_time = 600.0
	t.sm.hover_between_attacks = 600.0
	match tier:
		"layout":
			await _layout(t)
		"still":
			await _still(t)
		"edges":
			await _edges(t)
		"run":
			await _run(t)
		"late":
			await _late(t)
		"perfect":
			await _perfect(t)
		"draw":
			await _draw(t)
		"break":
			await _break(t)
		"release":
			await _release(t)


#SETTING UP

# A Flyby from his hover over HOVER_AT, pass 0 flying in from `side`, the player at `at` with every key up, a full bar
# and no i-frames.
static func _force(t, side: StringName, at: Vector2, hold := true) -> Node:
	await t.reset_gauged(HOME)
	if hold:
		t.hold_break_gauge(t.boss)
	for code in KEYS:
		t.release(code)
	t.defense._set_stamina(t.defense.max_stamina)
	await t.settle_player(at)
	t.clear_iframes()
	var boss: Node = t.boss
	boss.height = boss.HOVER_HEIGHT_PX
	boss.ground_position = HOVER_AT
	boss.fly_velocity = Vector2.ZERO
	boss.place()
	boss.play_anim(&"hover")
	t.sm.flyby_start_side = side
	t.sm.attacks = []
	t.sm.on_child_transition(t.sm.current_state, "Flyby")
	return t.sm.states["Flyby"]


# The player put where their hurtbox's left edge is at `left`, or its right edge at `right`, at `y`.
static func _put_hurtbox(t, y: float, left := NAN, right := NAN) -> Vector2:
	var box: Rect2 = t.hurtbox_rect()
	var at: Vector2 = t.player.global_position
	at.y = y
	if not is_nan(left):
		at.x += left - box.position.x
	elif not is_nan(right):
		at.x += right - box.end.x
	return at


static func _due(fb: Node, beat: int, k: int) -> float:
	for entry in fb.schedule:
		if entry[1] == beat and entry[2] == k:
			return entry[0]
	return INF


# Every hit taken from here on, with the state's clock, beat and pass as it landed. [log, the handler to disconnect].
static func _record(t, fb: Node) -> Array:
	var hits: Array = []
	var on_hit := func(hit: RefCounted) -> void:
		hits.append({"id": hit.attack_id, "clock": fb.clock, "beat": fb.beat, "pass": fb.pass_index, "at": t.defense.clock})
	t.defense.hit_taken.connect(on_hit)
	return [hits, on_hit]


static func _stop_recording(t, recording: Array) -> void:
	if t.defense.hit_taken.is_connected(recording[1]):
		t.defense.hit_taken.disconnect(recording[1])


static func _fire(fb: Node, k: int) -> Node:
	var fire = fb.fires[k]
	return fire if is_instance_valid(fire) else null


static func _lightable(t, dir: float) -> Vector2:
	return Layout.lightable(dir, t.sm.flyby_safe_width)


# The state clock at which pass `k`'s curtain first reaches `box` (strictly), or INF if the pass never lights under it.
static func _predicted_hit(t, fb: Node, k: int, box: Rect2) -> float:
	var dir: float = fb.pass_dir(k)
	var lit := _lightable(t, dir)
	if box.position.x >= lit.y or box.end.x <= lit.x:
		return INF
	var entry := Layout.entry_x(dir)
	var reach: float = maxf(box.position.x, lit.x) - entry if dir > 0.0 else entry - minf(box.end.x, lit.y)
	return _due(fb, fb.Beat.TELEGRAPH, k) + fb._telegraph_time(k) + reach / t.sm.flyby_speed


static func _names(hits: Array) -> Array:
	return hits.map(func(h): return [h.id, snappedf(h.clock, 0.001)])


static func _walk_until(t, code: int, arrived: Callable, give_up: Callable) -> bool:
	t.press(code)
	var got: bool = await t.wait_until(func(): return arrived.call() or give_up.call(), 900)
	t.release(code)
	return got and arrived.call()


#LAYOUT

static func _layout(t) -> void:
	var sm: Node = t.sm
	var broken: Array = Layout.invariants(sm)
	t.check(broken.is_empty(), "BixbyFlybyLayout.invariants(sm) is empty (%s)" % [broken])
	var breath: Dictionary = t.CATALOG.get_attack(Layout.BREATH_ID)
	var fire: Dictionary = t.CATALOG.get_attack(Layout.FIRE_ID)
	t.check(breath == t.CATALOG.DEFAULTS.merged({"dash_through": true, "dodge_tell": true}, true),
		"bixby_flyby_breath: half a heart, dashed through for a PERFECT DODGE, a yellow read, no guard or parry (%s)" % [breath])
	t.check(fire == t.CATALOG.DEFAULTS.merged({"dash_through": true, "no_perfect_dodge": true}, true),
		"bixby_flyby_fire: half a heart, dashed through, no PERFECT DODGE, no guard or parry (%s)" % [fire])
	var gauge: Node = t.boss.break_gauge
	var source: Node2D = t.dummy_source()
	t.check(gauge.earns_from.call(HitInfo.make(Layout.BREATH_ID, source, Vector2.ZERO)), "a read of the curtain fills his gauge")
	t.check(not gauge.earns_from.call(HitInfo.make(Layout.FIRE_ID, source, Vector2.ZERO)) and gauge.owns_attack.call(Layout.FIRE_ID),
		"the burning floor only drains it")
	var cycles: Array = sm.ATTACK_CYCLES
	t.check(cycles == [["Flyby"], ["Combined"], ["Flyby"], ["Combined"], ["Flyby"], ["Inferno"]] and cycles.all(func(c): return c.size() == 1 and not c.has("FireBreath")),
		"his rotation as it ships (the combined attack twice since 2026-10-06), a window after every attack, with no FireBreath in it (%s)" % [cycles])
	var width: float = sm.flyby_safe_width
	for dir in [1.0, -1.0]:
		var lit := Layout.lightable(dir, width)
		var safe := Layout.safe_span(dir, width)
		var far_edge: float = safe.y if dir > 0.0 else safe.x
		var whole := is_equal_approx(minf(lit.x, safe.x), Layout.FLOOR.position.x) and is_equal_approx(maxf(lit.y, safe.y), Layout.FLOOR.end.x) \
			and is_equal_approx(lit.y - lit.x + safe.y - safe.x, Layout.FLOOR.size.x)
		t.log_p("flying %s: burnable %s, safe column %s" % ["right" if dir > 0.0 else "left", lit, safe])
		t.check(is_equal_approx(far_edge, Layout.far_x(dir)) and is_equal_approx(safe.y - safe.x, width) and whole,
			"flying %s, the safe column is the far edge's %.0f px and the burnable span the rest of the floor" % ["right" if dir > 0.0 else "left", width])
	var walk: float = load("res://Scripts/PlayerScript.gd").SPEED
	var hurt: Rect2 = t.hurtbox_rect()
	t.check(is_equal_approx(Layout.PLAYER_WALK, walk), "PLAYER_WALK is the player's walk (%.0f)" % walk)
	t.check(is_equal_approx(2.0 * Layout.PLAYER_HALF_WIDTH, hurt.size.x), "PLAYER_HALF_WIDTH is half their hurtbox's width (%.1f)" % hurt.size.x)
	t.check(is_equal_approx(Layout.PLAYER_IFRAMES, t.player.invincibility_timer.wait_time), "PLAYER_IFRAMES is their i-frames")
	var speed: float = sm.flyby_speed
	var sweep := Layout.sweep_time(width, speed)
	var away: bool = sm.flyby_start_side == &"away"
	var worst_start: float = Layout.FLOOR.get_center().x if away else Layout.entry_x(1.0) + Layout.PLAYER_HALF_WIDTH
	# [the case, its projection, the walk into its column]
	var cases := [
		["pass 0 from %s" % ("the centre line (he starts away from the player)" if away else "the entry rope"), sm.flyby_telegraph_time,
			Layout.walk_to_column(worst_start, 1.0, width)],
		["the crossing from the rope", sm.flyby_return_telegraph_time,
			Layout.walk_to_column(Layout.far_x(1.0) - Layout.PLAYER_HALF_WIDTH, -1.0, width)],
		["the crossing from the column's inner edge", sm.flyby_return_telegraph_time,
			Layout.walk_to_column(Layout.safe_edge(1.0, width) + Layout.PLAYER_HALF_WIDTH, -1.0, width)],
	]
	t.log_p("the sweep %.3f s at %.0f px/s; walking into the column from a %.2f s reaction to the projection:" % [sweep, speed, Layout.REACTION])
	for case in cases:
		var distance: float = case[2]
		var spare := Layout.arrival_spare(case[1], distance, sm)
		t.log_p("  %s, %.0f px: they arrive %.3f s in, the front reaches the column at %.3f s, %.2f s spare; a walking reaction budget of %.2f s" % [case[0], distance, Layout.REACTION + distance / Layout.PLAYER_WALK, case[1] + sweep, spare, spare + Layout.REACTION])
		t.check(spare >= Layout.CROSS_SPARE - SLACK, "%s: in the column %.1f s or more before the front (%.2f s)" % [case[0], Layout.CROSS_SPARE, spare])


#STILL

static func _still(t) -> void:
	for side: StringName in [&"left", &"right"]:
		for spot in STILL_SPOTS:
			var fb := await _force(t, side, spot)
			var recording := _record(t, fb)
			var health: int = t.player.playerHealth
			var box: Rect2 = t.hurtbox_rect()
			var left_flyby: bool = await t.wait_until(func(): return t.sm.current_state != fb, 900)
			_stop_recording(t, recording)
			var hits: Array = recording[0]
			var ended_in := str(t.sm.current_state.name)
			var late: Array = fb.beat_times.filter(func(b): return b.clock < b.at - SLACK or b.clock > b.at + FRAME + SLACK)
			var wrong := []
			for k in 2:
				var in_pass := hits.filter(func(h): return h.pass == k)
				var predicted := _predicted_hit(t, fb, k, box)
				var sweep_at := _due(fb, fb.Beat.SWEEP, k)
				if predicted == INF:
					if not in_pass.is_empty():
						wrong.append("pass %d hit in its column: %s" % [k, _names(in_pass)])
				elif in_pass.size() != 1 or in_pass[0].id != Layout.BREATH_ID or absf(in_pass[0].clock - predicted) > 2.0 * FRAME + SLACK:
					wrong.append("pass %d: %s, predicted one breath at %.3f" % [k, _names(in_pass), predicted])
				if in_pass.any(func(h): return h.clock < sweep_at - SLACK):
					wrong.append("pass %d hit before its sweep" % k)
			var owed: int = hits.reduce(func(sum, h): return sum + t.catalogue_damage(h.id), 0)
			t.log_p("%s from %s: start dir %.0f, hits %s, lost %d; beats late %s; now %s" % [spot, side, fb.start_dir, _names(hits), health - t.player.playerHealth, late.size(), ended_in])
			t.check(left_flyby and late.is_empty(), "%s, %s: every beat on its scheduled frame" % [spot, side])
			t.check(wrong.is_empty(), "%s, %s: one curtain hit a pass over the burnable span, on the frame the spans predict, none in the column (%s)" % [spot, side, wrong])
			t.check(health - t.player.playerHealth == owed and hits.all(func(h): return t.catalogue_damage(h.id) == 1), "%s, %s: half a heart each" % [spot, side])
			var recovered := false
			if ended_in == "Land":
				recovered = await t.wait_until(func(): return str(t.sm.current_state.name) == "Recover", 120)
			var down_at: Vector2 = t.boss.ground_position
			var from: float = t.defense.clock
			await t.wait_until(func(): return str(t.sm.current_state.name) != "Recover", 600)
			var window: float = t.defense.clock - from
			t.check(recovered and down_at.distance_to(fb.landing) <= 1.0 and absf(window - t.sm.recover_time) <= 2.0 * FRAME + SLACK,
				"%s, %s: Land, then Recover on his landing point %s for %.1f s (%s, %.3f s)" % [spot, side, fb.landing, t.sm.recover_time, down_at, window])

	t.log_p("-- &\"away\"")
	for case in [[Vector2(600, 640), -1.0], [Vector2(1400, 640), 1.0]]:
		var fb := await _force(t, &"away", case[0])
		await t.wait_until(func(): return fb.beat == fb.Beat.TELEGRAPH, 120)
		t.check(is_equal_approx(fb.start_dir, case[1]), "the player at %s: pass 0 flies %s, from the side away from them" % [case[0], "right" if case[1] > 0.0 else "left"])
	var last: float = t.sm.last_flyby_dir
	var middle := await _force(t, &"away", Vector2(Layout.FLOOR.get_center().x, 640))
	await t.wait_until(func(): return middle.beat == middle.Beat.TELEGRAPH, 120)
	t.check(is_equal_approx(middle.start_dir, -last), "the player dead in the middle: the other side from last time (%.0f after %.0f)" % [middle.start_dir, last])


#EDGES

static func _edges(t) -> void:
	var seen := {"telegraph": [], "outside": [], "curtain": []}
	var watch := func() -> void:
		var fb: Node = t.sm.states["Flyby"]
		if t.sm.current_state != fb:
			return
		for k in 2:
			var fire := _fire(fb, k)
			if fire == null or fire.is_queued_for_deletion():
				continue
			var lit: Vector2 = fire._lightable()
			if fire.clock < fire.telegraph_time and fire.clock < FRAME + SLACK:
				var tele := _mask_rect(fire.telegraph_mask)
				var want := Rect2(lit.x, Layout.FLOOR.position.y, lit.y - lit.x, Layout.FLOOR.size.y)
				if not (fire.telegraph_mask.visible and tele.is_equal_approx(want)):
					seen.telegraph.append("pass %d: %s, not %s" % [k, tele, want])
			for mask in [fire.burn_mask, fire.die_mask]:
				if mask.visible:
					var rect := _mask_rect(mask)
					if rect.position.x < lit.x - 0.01 or rect.end.x > lit.y + 0.01:
						seen.outside.append("pass %d clock %.3f: %s outside %s" % [k, fire.clock, rect, lit])
			var span: Vector2 = fire.curtain_span()
			if Layout.span_empty(span) != not fire.curtain_mask.visible:
				seen.curtain.append("pass %d clock %.3f: span %s, mask shown %s" % [k, fire.clock, span, fire.curtain_mask.visible])
			elif fire.curtain_mask.visible:
				var rect := _mask_rect(fire.curtain_mask)
				if absf(rect.position.x - span.x) > 0.5 or absf(rect.end.x - span.y) > 0.5 \
						or not is_equal_approx(rect.position.y, Layout.exit_y()) or not is_equal_approx(rect.end.y, Layout.FLOOR.end.y):
					seen.curtain.append("pass %d clock %.3f: drawn %s, span %s" % [k, fire.clock, rect, span])
	t.physics_frame.connect(watch)
	var width: float = t.sm.flyby_safe_width
	var y := CROSSING_Y
	# [what, pass 0's hurtbox (its left edge), pass 1's (its right edge), whether each is hit]
	var cases := [
		["1 px inside the burnable span at the column's edge", Layout.safe_edge(1.0, width) - 1.0, Layout.safe_edge(-1.0, width) + 1.0, true],
		["flush with the column's edge", Layout.safe_edge(1.0, width), Layout.safe_edge(-1.0, width), false],
		["hugging the entry rope", Layout.entry_x(1.0), Layout.entry_x(-1.0), true],
	]
	for case in cases:
		var fb := await _force(t, &"left", Vector2(960, y))
		await t.settle_player(_put_hurtbox(t, y, case[1]))
		var recording := _record(t, fb)
		var got := [[], []]
		await t.wait_until(func(): return fb.beat == fb.Beat.TELEGRAPH and fb.pass_index == 1, 900)
		got[0] = recording[0].duplicate()
		t.clear_iframes()
		await t.settle_player(_put_hurtbox(t, y, NAN, case[2]))
		var boxes := [Rect2(), t.hurtbox_rect()]
		await t.wait_until(func(): return fb.beat == fb.Beat.RETURN, 900)
		_stop_recording(t, recording)
		got[1] = recording[0].filter(func(h): return h.pass == 1)
		for k in 2:
			var hits: Array = got[k]
			var fire_start := _due(fb, fb.Beat.SWEEP, k)
			if case[3]:
				var on_time := true
				if case[0] == "hugging the entry rope":
					on_time = not hits.is_empty() and hits[0].clock > fire_start and hits[0].clock <= fire_start + FRAME + SLACK
				t.check(hits.size() == 1 and hits[0].id == Layout.BREATH_ID and on_time,
					"pass %d, %s: hit by the curtain%s (%s)" % [k, case[0], " on the front's first frame" if case[0] == "hugging the entry rope" else "", _names(hits)])
			else:
				t.check(hits.is_empty(), "pass %d, %s: never hit (%s)" % [k, case[0], _names(hits)])
		t.log_p("%s: pass 1's hurtbox %s" % [case[0], boxes[1]])
	t.physics_frame.disconnect(watch)
	t.log_p("projection at its beat off by %s; burn or die-down outside on %s; curtain off on %s" % [seen.telegraph.slice(0, 3), seen.outside.slice(0, 3), seen.curtain.slice(0, 3)])
	t.check(seen.telegraph.is_empty(), "each projection as it goes up is the burnable span over the whole floor")
	t.check(seen.outside.is_empty(), "the burning floor and its die-down never go outside the burnable span")
	t.check(seen.curtain.is_empty(), "the curtain is drawn on curtain_span() to half a pixel, from exit_y() to the floor's bottom edge, and only while it has one")


# A mask's polygon on the screen.
static func _mask_rect(mask: Polygon2D) -> Rect2:
	var layer_y: float = (mask.get_parent() as Node2D).global_position.y
	var rect := Rect2(mask.polygon[0] + Vector2(0, layer_y), Vector2.ZERO)
	for point in mask.polygon:
		rect = rect.expand(point + Vector2(0, layer_y))
	return rect


#RUN

static func _run(t) -> void:
	var width: float = t.sm.flyby_safe_width
	t.log_p("-- pass 0 from the side away from them, into its column")
	for start in RUN_STARTS:
		var fb := await _force(t, &"away", start)
		var recording := _record(t, fb)
		await t.wait_until(func(): return _fire(fb, 0) != null and _fire(fb, 0).clock >= Layout.REACTION - PRESS_LEAD - SLACK, 120)
		var fire := _fire(fb, 0)
		var dir: float = fb.start_dir
		var edge := Layout.safe_edge(dir, width)
		var arrived: bool = await _walk_until(t, KEY_RIGHT if dir > 0.0 else KEY_LEFT, func(): return _in_column(t, dir, edge),
			func(): return fb.pass_index != 0 or fb.beat == fb.Beat.EXIT)
		var spare: float = fire.sweep_end() - fire.clock
		await t.wait_until(func(): return fb.pass_index == 1, 600)
		_stop_recording(t, recording)
		t.log_p("from %s, flying %s: in the column %s, %.2f s before the front reached its edge; hits %s" % [start, "right" if dir > 0.0 else "left", arrived, spare, _names(recording[0])])
		t.check(arrived and recording[0].is_empty(), "pass 0 from %s: walking to the column from a %.2f s reaction, never hit" % [start, Layout.REACTION])

	t.log_p("-- pass 1, the crossing")
	var edge := Layout.safe_edge(-1.0, width)
	# [where they start, the least they get there ahead of the front by]
	var inner_spare: float = Layout.CROSS_SPARE + (width - 2.0 * Layout.PLAYER_HALF_WIDTH) / Layout.PLAYER_WALK
	for case in [[Layout.far_x(1.0) - Layout.PLAYER_HALF_WIDTH, Layout.CROSS_SPARE], [Layout.safe_edge(1.0, width) + Layout.PLAYER_HALF_WIDTH, inner_spare]]:
		var from_x: float = case[0]
		var fb := await _force(t, &"left", Vector2(from_x, CROSSING_Y))
		var recording := _record(t, fb)
		await t.wait_until(func(): return _fire(fb, 1) != null and _fire(fb, 1).clock >= Layout.REACTION - PRESS_LEAD - SLACK, 900)
		var fire := _fire(fb, 1)
		var predicted := Layout.arrival_spare(fire.telegraph_time, t.hurtbox_rect().end.x - edge, t.sm)
		var arrived: bool = await _walk_until(t, KEY_LEFT, func(): return _in_column(t, -1.0, edge),
			func(): return fb.beat == fb.Beat.EXIT and fb.pass_index == 1)
		var spare: float = fire.sweep_end() - fire.clock
		await t.wait_until(func(): return fb.beat == fb.Beat.RETURN, 600)
		_stop_recording(t, recording)
		t.log_p("from %.0f: across %s, %.3f s before the front reached the column (the layout's arrival_spare %.3f); hits %s" % [from_x, arrived, spare, predicted, _names(recording[0])])
		t.check(arrived and recording[0].is_empty(), "the crossing from %.0f, from a %.2f s reaction: never hit" % [from_x, Layout.REACTION])
		# The bot sets off and is seen arriving on whole physics frames. The crossing's projection goes up 0.76 of a frame
		# into one (3.104 s), which sets it off 0.013 s late, and the walk's last frame rounds up: it measured 0.019 s
		# (rope) and 0.016 s (inner edge) under arrival_spare. Hence a frame of tolerance here; the layout's B stays strict.
		t.check(spare >= case[1] - FRAME - SLACK, "and in the column %.2f s or more, to a frame, before the front reaches it (%.3f s)" % [case[1], spare])


# Whether the player's hurtbox is inside the column a pass flying `dir` leaves, `edge` its inner edge.
static func _in_column(t, dir: float, edge: float) -> bool:
	var box: Rect2 = t.hurtbox_rect()
	return box.position.x >= edge if dir > 0.0 else box.end.x <= edge


# How far a pass flying `dir` has to go to reach the player's hurtbox: from its front to the edge it meets first.
static func _front_gap(t, fire: Node, dir: float) -> float:
	var box: Rect2 = t.hurtbox_rect()
	return box.position.x - fire.front_x() if dir > 0.0 else fire.front_x() - box.end.x


#LATE

static func _late(t) -> void:
	var width: float = t.sm.flyby_safe_width
	var edge := Layout.safe_edge(-1.0, width)
	for from_x in [Layout.far_x(1.0) - Layout.PLAYER_HALF_WIDTH, Layout.safe_edge(1.0, width) + Layout.PLAYER_HALF_WIDTH]:
		for early in [true, false]:
			var fb := await _force(t, &"left", Vector2(from_x, CROSSING_Y))
			var recording := _record(t, fb)
			await t.wait_until(func(): return _fire(fb, 1) != null, 900)
			var fire := _fire(fb, 1)
			# The latest a walk sets off and still gets into the column before the front does.
			var walk: float = t.hurtbox_rect().end.x - edge
			var set_off: float = fire.sweep_end() - walk / Layout.PLAYER_WALK + (-2.0 if early else 2.0) * FRAME
			await t.wait_until(func(): return fire.clock >= set_off - PRESS_LEAD - SLACK, 300)
			await _walk_until(t, KEY_LEFT, func(): return t.hurtbox_rect().end.x <= edge, func(): return fb.beat == fb.Beat.RETURN)
			await t.wait_until(func(): return fb.beat == fb.Beat.RETURN, 600)
			_stop_recording(t, recording)
			var hits: Array = recording[0].filter(func(h): return h.pass == 1)
			t.log_p("from %.0f, a %.0f px walk, setting off 2 frames %s the latest that gets there first (%.3f s into the projection): %s" % [from_x, walk, "before" if early else "after", set_off, _names(hits)])
			if early:
				t.check(hits.is_empty(), "from %.0f, 2 frames early: never hit" % from_x)
			else:
				t.check(hits.size() == 1 and hits[0].id == Layout.BREATH_ID, "from %.0f, 2 frames late: hit once, by the curtain" % from_x)

	t.log_p("-- setting off %.1f s into the crossing's projection, with three dashes on the way" % DASH_RUN_SET_OFF)
	var fb := await _force(t, &"left", Vector2(Layout.far_x(1.0) - Layout.PLAYER_HALF_WIDTH, CROSSING_Y))
	var recording := _record(t, fb)
	await t.wait_until(func(): return _fire(fb, 1) != null and _fire(fb, 1).clock >= DASH_RUN_SET_OFF - PRESS_LEAD - SLACK, 900)
	var fire := _fire(fb, 1)
	var budget: float = Layout.arrival_spare(fire.telegraph_time, t.hurtbox_rect().end.x - edge, t.sm) + Layout.REACTION
	var dashes := [0]
	var low := [t.defense.stamina]
	t.press(KEY_LEFT)
	await t.wait_until(func():
		low[0] = minf(low[0], t.defense.stamina)
		if dashes[0] < 3 and not t.player.is_dodging and not t.defense.is_dash_recovering() and not t.defense.is_dash_cooling_down() \
				and t.defense.stamina >= t.defense.dash_stamina_cost:
			t.tap(KEY_W)
			dashes[0] += 1
		return t.hurtbox_rect().end.x <= edge or fb.beat == fb.Beat.RETURN, 900)
	var spare: float = fire.sweep_end() - fire.clock
	t.release(KEY_LEFT)
	await t.wait_until(func(): return fb.beat == fb.Beat.RETURN, 600)
	_stop_recording(t, recording)
	t.log_p("from the rope, a walk's budget %.2f s: %d dashed, stamina at %.1f at the lowest, in the column %.2f s before the front, hits %s" % [budget, dashes[0], low[0], spare, _names(recording[0])])
	t.check(dashes[0] == 3 and recording[0].is_empty(), "a crossing setting off %.1f s in, with three dashes in it, is never hit" % DASH_RUN_SET_OFF)


#PERFECT

static func _perfect(t) -> void:
	var defense: Node = t.defense
	var gauge: Node = t.boss.break_gauge
	var width: float = t.sm.flyby_safe_width
	var cost: float = defense.dash_stamina_cost
	var gap: float = PERFECT_FRAMES * FRAME * t.sm.flyby_speed
	var starts := [PERFECT_HIT_X, Layout.FLOOR.position.x + Layout.FLOOR.end.x - PERFECT_HIT_X]

	t.log_p("-- a dash forward into the column with the front %.0f px behind, on each pass" % gap)
	var fb := await _force(t, &"left", Vector2(starts[0], CROSSING_Y), false)
	var recording := _record(t, fb)
	for k in 2:
		var dir: float = fb.pass_dir(k)
		if k == 1:
			await t.settle_player(Vector2(starts[1], CROSSING_Y))
			await t.dash_ready()
			t.clear_iframes()
		await t.wait_until(func(): return _fire(fb, k) != null and _fire(fb, k).clock >= _fire(fb, k).telegraph_time, 300)
		var ahead := _fire(fb, k)
		await t.wait_until(func(): return _front_gap(t, ahead, dir) <= gap, 300)
		var dodged: int = t.dodges.size()
		var gauge_before: float = gauge.value
		var hits_before: int = recording[0].size()
		var key: int = KEY_RIGHT if dir > 0.0 else KEY_LEFT
		t.press(key)
		t.tap(KEY_W)
		await t.wait_until(func(): return t.player.is_dodging, 10)
		await t.wait_until(func(): return not t.player.is_dodging and not defense.is_dash_cooling_down(), 60)
		t.release(key)
		var paid: Array = t.dodges.slice(dodged).map(func(d): return d.id)
		var gained: float = gauge.value - gauge_before
		var stamina: float = defense.stamina
		var in_column := _in_column(t, dir, Layout.safe_edge(dir, width))
		await t.wait_until(func(): return fb.pass_index != k or fb.beat == fb.Beat.RETURN, 600)
		var hits: Array = recording[0].slice(hits_before)
		t.log_p("pass %d from %.0f: in the column %s; hits %s, perfect dodges %s, gauge +%.2f to %.2f, stamina %.1f of %.1f" % [k, starts[k], in_column, _names(hits), paid, gained, gauge.value, stamina, defense.max_stamina])
		t.check(in_column and hits.is_empty() and paid == [Layout.BREATH_ID], "pass %d: into the column, no hit, and one PERFECT DODGE of the curtain" % k)
		t.check(stamina >= defense.max_stamina - 0.5 and is_equal_approx(gained, gauge.perfect_dodge_gain),
			"pass %d: the dash given back, and one read on his gauge (%.2f)" % [k, gauge.perfect_dodge_gain])
	t.check(is_equal_approx(gauge.value, 2.0 * gauge.perfect_dodge_gain), "one read a pass, two a Flyby (%.2f)" % gauge.value)
	_stop_recording(t, recording)

	t.log_p("-- a dash back through the front from %.0f px ahead" % gap)
	fb = await _force(t, &"left", Vector2(960, CROSSING_Y), false)
	recording = _record(t, fb)
	await t.wait_until(func(): return _fire(fb, 0) != null and _fire(fb, 0).clock >= _fire(fb, 0).telegraph_time, 300)
	var back := _fire(fb, 0)
	await t.wait_until(func(): return _front_gap(t, back, 1.0) <= gap, 300)
	t.press(KEY_LEFT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	var dash_start: float = t.defense.clock
	t.release(KEY_LEFT)
	await t.wait_until(func(): return fb.pass_index == 1, 600)
	_stop_recording(t, recording)
	var after: Array = recording[0].filter(func(h): return h.pass == 0)
	var dodged_back: Array = back.reports.filter(func(r): return r.result == HitInfo.Result.DODGED).map(func(r): return r.id)
	var immunity_end: float = dash_start + t.CATALOG.DASH_IMMUNITY_TIME
	t.log_p("dashed back through the front: reported %s; hits %s at %s, immunity over at %.3f" % [back.reports.map(func(r): return [r.id, HitInfo.Result.keys()[r.result], snappedf(r.clock, 0.001)]), _names(after), after.map(func(h): return snappedf(h.at, 0.001)), immunity_end])
	t.check(dodged_back.has(Layout.BREATH_ID), "the curtain crossed in the dash is DODGED")
	t.check(after.size() == 1 and after[0].id == Layout.FIRE_ID and after[0].at >= immunity_end - FRAME - SLACK,
		"then one hit of the burning floor, as the dash's immunity ends")

	t.log_p("-- pass 0: hit at %.0f, the i-frames cleared, a dash into the column" % PERFECT_HIT_X)
	fb = await _force(t, &"left", Vector2(PERFECT_HIT_X, CROSSING_Y), false)
	recording = _record(t, fb)
	await t.wait_until(func(): return not recording[0].is_empty(), 600)
	var hit_first: Array = recording[0].duplicate()
	var fire := _fire(fb, 0)
	var box: Rect2 = t.hurtbox_rect()
	# The curtain has slid into the column's edge, and the floor under them is still burning.
	var curtain_gone: float = fire.sweep_end() + Layout.CURTAIN_WIDTH / t.sm.flyby_speed
	var burning_until: float = fire.telegraph_time + t.sm.flyby_burn_time + (box.position.x - Layout.entry_x(1.0)) / t.sm.flyby_speed
	await t.wait_until(func(): return fire.clock >= (curtain_gone + burning_until) / 2.0, 300)
	var still_burning: bool = Layout.span_touches(t.hurtbox_rect(), fire.hurting_span()) and Layout.span_empty(fire.curtain_span())
	var dodged: int = t.dodges.size()
	var stamina_before: float = defense.stamina
	var reported: int = fire.reports.size()
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	t.clear_iframes()
	await t.wait_until(func(): return not t.player.is_dodging, 30)
	t.release(KEY_RIGHT)
	await t.wait(30)
	var into: Array = fire.reports.slice(reported).map(func(r): return [r.id, HitInfo.Result.keys()[r.result]])
	var later: Array = recording[0].slice(hit_first.size())
	t.log_p("hit %s; the floor still burning under them with the curtain gone %s; the dash: reported %s, hits %s, perfect dodges %s, stamina %.1f -> %.1f, in the column %s" % [_names(hit_first), still_burning, into, _names(later), t.dodges.slice(dodged).map(func(d): return d.id), stamina_before, defense.stamina, t.hurtbox_rect().position.x >= Layout.safe_edge(1.0, width)])
	t.check(hit_first.size() == 1 and hit_first[0].id == Layout.BREATH_ID and still_burning, "hit by the curtain, and later standing in the floor it left burning")
	t.check(into.has([Layout.FIRE_ID, "DODGED"]) and later.is_empty() and t.dodges.size() == dodged, "the dash into the column across it is DODGED, no hit and no PERFECT DODGE")
	t.check(defense.stamina < stamina_before - cost / 2.0, "and the dash is paid for")
	_stop_recording(t, recording)


#DRAW

static func _draw(t) -> void:
	for side: StringName in [&"left", &"right"]:
		var fb := await _force(t, side, Vector2(960, 800))
		var problems := {"on_pass": [], "ahead": [], "layers": [], "hud": [], "rim": []}
		var times := {"rise": -1.0, "return": -1.0}
		var frames_on_pass := [0]
		var images := {}
		var settle: float = t.boss.HUD_FADE_TIME + 2.0 * FRAME
		var watch := func() -> void:
			var now: float = t.defense.clock
			var on_state: bool = t.sm.current_state == fb
			if on_state and fb.beat == fb.Beat.RISE and times.rise < 0.0:
				times.rise = now
			if on_state and fb.beat == fb.Beat.RETURN and times["return"] < 0.0:
				times["return"] = now
			var bar: float = t.hud_alpha()
			var gauge_bar: float = t.boss.gauge_bar.modulate.a
			if times.rise >= 0.0 and times["return"] < 0.0 and now - times.rise >= settle \
					and not (is_equal_approx(bar, t.sm.inferno_hud_fade_alpha) and is_equal_approx(gauge_bar, t.sm.inferno_hud_fade_alpha)):
				problems.hud.append("%.2f s into the Flyby, bar %.3f gauge %.3f" % [now - times.rise, bar, gauge_bar])
			if times["return"] >= 0.0 and now - times["return"] >= settle and not (is_equal_approx(bar, 1.0) and is_equal_approx(gauge_bar, 1.0)):
				problems.hud.append("%.2f s after the return, bar %.3f gauge %.3f" % [now - times["return"], bar, gauge_bar])
			for fire in t.hazards_of("BixbyFlybyFireScript.gd"):
				var sorts := [fire.floor_layer.global_position.y, fire.curtain_layer.global_position.y, fire.rim_layer.global_position.y]
				if not (is_equal_approx(sorts[0], Layout.FLOOR_LAYER_Y) and is_equal_approx(sorts[1], Layout.CURTAIN_SORT_Y) \
						and is_equal_approx(sorts[2], Layout.RIM_SORT_Y)) or sorts.any(func(s): return s >= t.player.global_position.y) \
						or [fire, fire.floor_layer, fire.curtain_layer, fire.rim_layer].any(func(n): return n.z_index != 0):
					problems.layers.append("sorting at %s, the player at %.1f" % [sorts, t.player.global_position.y])
				var x_s: float = fire._safe_edge()
				if not (is_equal_approx(fire.rim.points[0].x, x_s) and is_equal_approx(fire.rim.points[1].x, x_s)):
					problems.rim.append("rim at %s, the column's edge %.0f" % [fire.rim.points, x_s])
			if not on_state or not fb.beat in [fb.Beat.TELEGRAPH, fb.Beat.ENTER, fb.Beat.SWEEP, fb.Beat.EXIT]:
				return
			frames_on_pass[0] += 1
			var drawn := _drawn(t, images, 0)
			if not (is_equal_approx(t.boss.global_position.y, Layout.PASS_SORT_Y) and not t.boss.shadow.visible \
					and is_equal_approx(t.boss.feet_position().y, Layout.PASS_ANCHOR_Y) and drawn.end.y <= 321.0 + 0.01):
				problems.on_pass.append("f%d sorting at %.1f, shadow %s, feet %s, drawn to y %.1f" % [Engine.get_physics_frames(), t.boss.global_position.y, t.boss.shadow.visible, t.boss.feet_position(), drawn.end.y])
			var current := _fire(fb, fb.pass_index)
			if current != null and fb.beat in [fb.Beat.ENTER, fb.Beat.SWEEP] and not Layout.span_empty(current.telegraph_span()):
				var low := _drawn(t, images, Layout.FLOOR_ROW)
				var dir: float = fb.pass_dir(fb.pass_index)
				var ahead: float = low.end.x - current.front_x() if dir > 0.0 else current.front_x() - low.position.x
				if low.size != Vector2.ZERO and ahead > 0.5:
					problems.ahead.append("f%d %.1f px ahead of the front at %.1f" % [Engine.get_physics_frames(), ahead, current.front_x()])
		t.physics_frame.connect(watch)
		await t.wait_until(func(): return t.sm.current_state != fb, 900)
		await t.wait_until(func(): return t.defense.clock - times["return"] >= 0.5, 120)
		var left: Array = t.hazards_of("BixbyFlybyFireScript.gd")
		await t.wait_until(func(): return str(t.sm.current_state.name) == "Recover", 120)
		await t.wait(20)
		t.physics_frame.disconnect(watch)
		t.log_p("from the %s: %d frames on a pass; wrong on a pass %s; ahead of the front %s; layers %s; rim %s; HUD %s; fire left 0.5 s after the return %d" % [side, frames_on_pass[0], problems.on_pass.slice(0, 3), problems.ahead.slice(0, 3), problems.layers.slice(0, 2), problems.rim.slice(0, 2), problems.hud.slice(0, 3), left.size()])
		t.check(frames_on_pass[0] > 0 and problems.on_pass.is_empty(), "from the %s, on a pass he sorts at the rope line with no shadow, his feet at y %.0f, nothing drawn below y 321" % [side, Layout.PASS_ANCHOR_Y])
		t.check(problems.ahead.is_empty(), "from the %s, while the projection is up nothing of him from y 105 down is ahead of the front" % side)
		t.check(problems.layers.is_empty() and problems.rim.is_empty(), "from the %s, the fire's layers sort at 101, 114.5 and 115, under the player, and the rim is on the column's edge" % side)
		t.check(problems.hud.is_empty(), "from the %s, the bar and the gauge at %.1f from the rise and at full from the return" % [side, t.sm.inferno_hud_fade_alpha])
		t.check(left.is_empty(), "from the %s, no fire left half a second after the return" % side)


# The opaque part of the frame he is drawing from texel row `row` down, px, mirrored with him.
static func _drawn(t, images: Dictionary, row: int) -> Rect2:
	var boss: Node = t.boss
	var sheet: String = boss.anim.sheet
	if not images.has(sheet):
		images[sheet] = Image.load_from_file(ProjectSettings.globalize_path(sheet))
	var image: Image = images[sheet]
	var size := Vector2i(BixbyBeastArtLayout.FRAME_SIZE)
	var used: Rect2i = image.get_region(Rect2i(boss.sprite.frame * size.x, row, size.x, size.y - row)).get_used_rect()
	if used.size == Vector2i.ZERO:
		return Rect2()
	var texels := Rect2(Vector2(used.position) + Vector2(0, row), Vector2(used.size))
	if boss.sprite.flip_h:
		texels.position.x = size.x - texels.end.x
	return Rect2(boss.air.global_position + BixbyBeastArtLayout.local(texels.position), texels.size * BixbyBeastArtLayout.SCALE)


#BREAK

static func _break(t) -> void:
	var fb: Node = t.sm.states["Flyby"]
	var moments := {
		"rising": func(): return fb.beat == fb.Beat.RISE and fb.clock >= 0.2,
		"the first projection": func(): return fb.beat == fb.Beat.TELEGRAPH and fb.pass_index == 0,
		"the first sweep, the curtain falling": func(): return fb.beat == fb.Beat.SWEEP and fb.pass_index == 0 and fb.curtain_live(),
		"the second projection, off the screen": func(): return fb.beat == fb.Beat.TELEGRAPH and fb.pass_index == 1,
		"the crossing's sweep": func(): return fb.beat == fb.Beat.SWEEP and fb.pass_index == 1 and fb.curtain_live(),
		"the return": func(): return fb.beat == fb.Beat.RETURN,
	}
	for moment in moments:
		await _force(t, &"left", Vector2(960, 800), false)
		var reached: bool = await t.wait_until(func(): return t.sm.current_state == fb and moments[moment].call(), 900)
		await t.force_break()
		var height := [-1.0]
		var broke: bool = await t.wait_until(func():
			if str(t.sm.current_state.name) == "Broken":
				height[0] = t.boss.height
				return true
			return false, 3)
		var broke_at: float = t.defense.clock
		await t.wait(1)
		var fires: Array = t.hazards_of("BixbyFlybyFireScript.gd")
		var tells: Array = t.live_tells()
		# The Break's own hit-stop slows the fight, and the bar's fade with it: the fade is timed in the fight's time.
		await t.wait_until(func(): return t.defense.clock - broke_at >= t.boss.HUD_FADE_TIME + 2.0 * FRAME, 600)
		var bar: float = t.hud_alpha()
		var gauge_bar: float = t.boss.gauge_bar.modulate.a
		var shadow_ok: bool = t.boss.shadow.visible and is_equal_approx(t.boss.shadow.modulate.a, BixbyBeastArtLayout.SHADOW_ALPHA)
		var broken: Node = t.sm.states["Broken"]
		await t.wait_until(func(): return broken.slide_left <= 0.0, 120)
		var bounds: Rect2 = t.boss.ground_bounds(0.0).grow(1.0)
		var feet_in: bool = bounds.has_point(t.boss.ground_position) and is_zero_approx(t.boss.height)
		var took_off: bool = await t.wait_until(func(): return str(t.sm.current_state.name) == "Takeoff", 600)
		t.log_p("%s: reached %s, Broken %s at height %.1f; fires %d, badges %d; bar %.3f gauge %.3f; shadow %s at %.2f; down at %s; took off %s" % [moment, reached, broke, height[0], fires.size(), tells.size(), bar, gauge_bar, t.boss.shadow.visible, t.boss.shadow.modulate.a, t.boss.ground_position, took_off])
		t.check(reached and broke and is_equal_approx(height[0], t.boss.HOVER_HEIGHT_PX), "%s: Broken within 2 frames, at hover height" % moment)
		t.check(fires.is_empty() and tells.is_empty(), "%s: no fire and no badge left" % moment)
		t.check(is_equal_approx(bar, 1.0) and is_equal_approx(gauge_bar, 1.0) and shadow_ok, "%s: the bar and the gauge at full, his shadow back" % moment)
		t.check(feet_in and took_off, "%s: down in ground_bounds(0), and Takeoff after the window" % moment)
		await t.wait_until(func(): return not t.player.is_action_locked, 120)


#RELEASE

static func _release(t) -> void:
	var width: float = t.sm.flyby_safe_width
	var sweep := Layout.sweep_time(width, t.sm.flyby_speed)
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	var hit_stop: GDScript = load("res://Scripts/HitStop.gd")
	var in_column := Vector2(Layout.far_x(1.0) - width / 2.0, CROSSING_Y)
	var snapshot := func(fb: Node) -> Array:
		var fire := _fire(fb, fb.pass_index)
		return [fb.clock, fire.clock if fire else -1.0, fire.mouth_x() if fire else -1.0, t.boss.feet_position(), t.hud_alpha()]

	t.log_p("-- paused mid-sweep, then frozen mid-sweep")
	var fb := await _force(t, &"left", in_column)
	await t.wait_until(func(): return fb.beat == fb.Beat.SWEEP and fb.pass_index == 0 and fb.clock >= _due(fb, fb.Beat.SWEEP, 0) + sweep / 2.0, 600)
	await t.tap_pause()
	var paused_at: Array = snapshot.call(fb)
	await t.wait(60)
	var paused_after: Array = snapshot.call(fb)
	var was_open: bool = t.pause_menu().is_open()
	await t.tap_pause()
	t.pause_menu().grace_until_msec = 0
	t.log_p("paused: %s -> %s" % [paused_at, paused_after])
	t.check(was_open and str(paused_at) == str(paused_after), "paused for 60 frames: its clock, the mouth, his feet and the bar don't move")
	await t.wait_until(func(): return fb.beat == fb.Beat.TELEGRAPH and fb.pass_index == 1, 600)
	var exit_0: Array = fb.beat_times.filter(func(b): return b.beat == fb.Beat.EXIT and b.pass == 0)
	t.check(exit_0.size() == 1 and exit_0[0].clock >= exit_0[0].at - SLACK and exit_0[0].clock <= exit_0[0].at + FRAME + SLACK,
		"and the front still reaches the column's edge at its scheduled time on the state's clock (%s)" % [exit_0])
	await t.settle_player(Vector2(Layout.far_x(-1.0) + width / 2.0, CROSSING_Y))
	await t.wait_until(func(): return fb.beat == fb.Beat.SWEEP and fb.pass_index == 1 and fb.clock >= _due(fb, fb.Beat.SWEEP, 1) + sweep / 2.0, 600)
	t.check(freeze.freeze(t, [t.player.get_parent()]), "the fight freezes around the player mid-sweep")
	await t.wait(1)
	var frozen_at: Array = snapshot.call(fb)
	await t.wait(30)
	var frozen_after: Array = snapshot.call(fb)
	freeze.unfreeze(t)
	t.log_p("frozen: %s -> %s" % [frozen_at, frozen_after])
	t.check(str(frozen_at) == str(frozen_after), "frozen for 30 frames: its clock, the mouth, his feet and the bar don't move")
	await t.wait_until(func(): return fb.beat == fb.Beat.RETURN, 600)
	var exit_1: Array = fb.beat_times.filter(func(b): return b.beat == fb.Beat.EXIT and b.pass == 1)
	t.check(exit_1.size() == 1 and exit_1[0].clock >= exit_1[0].at - SLACK and exit_1[0].clock <= exit_1[0].at + FRAME + SLACK,
		"and after it the front reaches the column's edge on time again (%s)" % [exit_1])

	t.log_p("-- a hit-stop mid-sweep")
	fb = await _force(t, &"left", in_column)
	await t.wait_until(func(): return fb.beat == fb.Beat.SWEEP and fb.pass_index == 0 and fb.clock >= _due(fb, fb.Beat.SWEEP, 0) + sweep / 2.0, 600)
	var worst := [0.0]
	var frames := [0]
	var on_mouth := func() -> void:
		var fire := _fire(fb, 0)
		if t.sm.current_state != fb or fb.beat != fb.Beat.SWEEP or fire == null:
			return
		frames[0] += 1
		worst[0] = maxf(worst[0], absf(t.boss.air.global_position.x + Layout.exit_offset(1.0) - fire.mouth_x()))
	t.physics_frame.connect(on_mouth)
	hit_stop.freeze(t, 0.1)
	await t.wait(30)
	t.physics_frame.disconnect(on_mouth)
	hit_stop.clear()
	t.log_p("through a 0.1 s hit-stop: %d frames, his lead exit %.6f px off the mouth at the most" % [frames[0], worst[0]])
	# He is placed on whole pixels, and the hit-stop's time scale puts the fast mouth on exact half pixels, so the
	# rounding's half a pixel comes out a float's hair over.
	t.check(frames[0] > 0 and worst[0] <= 0.5 + SLACK, "his lead exit stays on the mouth, to half a pixel, every frame")

	t.log_p("-- a player at 1 health killed by the curtain")
	fb = await _force(t, &"left", Vector2(960, CROSSING_Y))
	var recording := _record(t, fb)
	await t.wait_until(func(): return fb.beat == fb.Beat.SWEEP and fb.pass_index == 0, 600)
	t.clear_iframes()
	t.player.playerHealth = 1
	var lost: bool = await t.wait_until(func(): return t.player.fight_over, 400)
	await t.wait(3)
	_stop_recording(t, recording)
	var hits: Array = recording[0]
	var bar: float = t.hud_alpha()
	t.log_p("lost %s to %s; 3 frames on: fires %d, badges %d, %s, player_defeated %s, height %.1f, shadow %s, bar %.3f" % [lost, _names(hits), t.hazards_of("BixbyFlybyFireScript.gd").size(), t.live_tells().size(), t.sm.current_state.name, t.sm.player_defeated, t.boss.height, t.boss.shadow.visible, bar])
	t.check(lost and not hits.is_empty() and hits[-1].id == Layout.BREATH_ID, "the curtain is the killing blow")
	t.check(t.hazards_of("BixbyFlybyFireScript.gd").is_empty() and t.live_tells().is_empty(), "3 frames on, no fire and no badge")
	t.check(str(t.sm.current_state.name) == "Idle" and t.sm.player_defeated, "he stands down in Idle")
	t.check(is_equal_approx(t.boss.height, t.boss.HOVER_HEIGHT_PX) and t.boss.shadow.visible, "hovering at %.0f px, his shadow back" % t.boss.HOVER_HEIGHT_PX)
	t.check(bar > t.sm.inferno_hud_fade_alpha, "the bar on its way back (%.3f)" % bar)
	var outro: bool = await t.wait_until(func(): return t.root.has_node("FightOutro"), 300)
	await t.wait(roundi(t.boss.HUD_FADE_TIME / FRAME) + 2)
	t.check(outro and is_equal_approx(t.hud_alpha(), 1.0), "and at full through the outro (%.3f)" % t.hud_alpha())


#ART

static func _art(t, approval: bool) -> void:
	t.log_p("-- the art, %s" % ("the approval pass" if approval else "as shipped"))
	var contract := _contract(approval)
	var pose_path: String = APPROVAL_DIR + BixbyBeastArtLayout.FLYBY_SHEET.get_file() if approval else BixbyBeastArtLayout.FLYBY_SHEET
	var pose_in: bool = FileAccess.file_exists(pose_path) if approval else Layout.final_flyby()
	if not pose_in:
		t.log_p("the pass pose: placeholders in use (the fly frames)")
	else:
		var image := Image.load_from_file(ProjectSettings.globalize_path(pose_path))
		var lead: Vector2 = contract.get("lead_exit", Layout.FINAL_LEAD_EXIT)
		var exits: Dictionary = contract.get("exits", Layout.FINAL_EXITS)
		var frames := 0
		for clip in [&"flyby_glide", &"flyby_breath"]:
			frames = maxi(frames, BixbyBeastArtLayout.ANIMS[clip].frames.max() + 1)
		var size := Vector2i(BixbyBeastArtLayout.FRAME_SIZE)
		t.check(image.get_height() == size.y and image.get_width() == frames * size.x, "the pass pose: %d frames of %s, as ANIMS plays (%s)" % [frames, size, image.get_size()])
		var breath_frames: Array = BixbyBeastArtLayout.ANIMS[&"flyby_breath"].frames
		var missing := breath_frames.filter(func(f): return not exits.has(f) and not exits.has(str(f)))
		t.check(lead.x >= 0.0 and missing.is_empty(), "FINAL_LEAD_EXIT is set and FINAL_EXITS has every breath frame (missing %s)" % [missing])
		var off_lead := []
		for f in breath_frames:
			var listed: Array = exits.get(f, exits.get(str(f), []))
			if listed.is_empty():
				continue
			var first: Vector2 = _texel(listed[0])
			if not is_equal_approx(first.x, lead.x) or absf(first.y - lead.y) > 2.0 or listed.any(func(e): var p := _texel(e); return p.y < 78 or p.y > 112):
				off_lead.append([f, listed])
		t.check(off_lead.is_empty(), "every breath frame's lead exit on FINAL_LEAD_EXIT's column (its row +-2), and its exits in rows 78-112 (%s)" % [off_lead])
		var drawn_wrong := []
		for f in frames:
			var below := image.get_region(Rect2i(f * size.x, 158, size.x, size.y - 158)).get_used_rect()
			var right := Rect2i(f * size.x + int(lead.x) + 1, Layout.FLOOR_ROW, size.x - int(lead.x) - 1, size.y - Layout.FLOOR_ROW)
			var ahead := image.get_region(right).get_used_rect() if right.size.x > 0 else Rect2i()
			if below.size != Vector2i.ZERO or ahead.size != Vector2i.ZERO:
				drawn_wrong.append([f, below, ahead])
		t.check(drawn_wrong.is_empty(), "nothing drawn below row 157, nor right of the lead exit from row %d down (%s)" % [Layout.FLOOR_ROW, drawn_wrong])
	var curtain_path: String = APPROVAL_DIR + Layout.CURTAIN_SHEET.get_file() if approval else Layout.CURTAIN_SHEET
	var curtain_in: bool = FileAccess.file_exists(curtain_path) if approval else Layout.final_curtain()
	if not curtain_in:
		t.log_p("the curtain: placeholder in use")
	else:
		var image := Image.load_from_file(ProjectSettings.globalize_path(curtain_path))
		var frame: Vector2 = Layout.CURTAIN.frame
		t.check(int(frame.x) == int(Layout.CURTAIN_WIDTH_TEXELS) and image.get_width() == int(Layout.CURTAIN.frames * frame.x) and image.get_height() == int(frame.y),
			"the curtain: %d frames %s texels, 32 wide (%s)" % [Layout.CURTAIN.frames, frame, image.get_size()])


# The approval folder's contract.json numbers, where it has them: {lead_exit, exits}.
static func _contract(approval: bool) -> Dictionary:
	var path := APPROVAL_DIR + "contract.json"
	if not approval or not FileAccess.file_exists(path):
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		return {}
	var out := {}
	if parsed.has("FINAL_LEAD_EXIT"):
		out["lead_exit"] = _texel(parsed.FINAL_LEAD_EXIT)
	if parsed.has("FINAL_EXITS"):
		out["exits"] = parsed.FINAL_EXITS
	return out


static func _texel(value) -> Vector2:
	if value is Vector2:
		return value
	if value is Array and value.size() >= 2:
		return Vector2(value[0], value[1])
	return Vector2(-1, -1)
