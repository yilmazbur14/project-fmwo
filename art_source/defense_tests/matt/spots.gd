extends RefCounted

# matt_spots (playtest 2026-10-04): the Mystic volley never skips a cast for want of a spot. --fixed-fps 60.
#   sweep     every spot on a SWEEP_STEP grid over the player's floor, with him standing at HOME, at the Glass
#             Row's station, on his juggle floor under it, at each Trueshot station and on a few spots between:
#             a cast finds a spot every time, on a lattice line through the player (his mouth the player's
#             hurtbox centre less the heading times the range), his feet inside STAND_RECT and the range at
#             least mystic_range_floor. From HOME a player 400-600 px to his side at his height found none
#             until the spot gap got a last pass of its own (MattMysticVolley.PASSES), and a skipped cast
#             skipped the rest of the volley with it, since he hadn't moved: the fight's first volley fired
#             nothing at a player standing there.
#   first     the fight's real first cycle, from his first Idle at HOME, the player standing from the start on the
#             old dead zone's middle each side, (443, 600) and (1483, 604), and on the walk-in's mark: the volley
#             fires every cast it planned.
#   tier=trueshot (slow, not in the default run): every spot on a TRUESHOT_STEP grid against each of the four
#             stations' real shot, the player standing still: none is missed by more than two of them (the top
#             station can't shoot up past his mouth, the bottom one down, and a corner is behind two).

const SWEEP_STEP := 40.0
const TRUESHOT_STEP := 160.0
const FIRST_SPOTS := [Vector2(443, 600), Vector2(1483, 604)]


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	if t.tier == "trueshot":
		await trueshot(t)
	else:
		await sweep(t)
		await first(t)


static func floor_grid(t, step: float) -> Array:
	var floor_rect: Rect2 = t.player.ring_origins
	var spots := []
	var y := floor_rect.position.y
	while y <= floor_rect.end.y + 0.1:
		var x := floor_rect.position.x
		while x <= floor_rect.end.x + 0.1:
			spots.append(Vector2(roundf(x), roundf(y)))
			x += step
		y += step
	return spots


static func sweep(t) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var volley: Node = sm.states["MysticVolley"]
	var froms: Array = [sm.HOME, sm.GLASS_ROW.station, Vector2(960, 485)]
	for station in sm.STATIONS:
		froms.append(station.feet)
	froms.append_array([Vector2(400, 900), Vector2(1500, 520), Vector2(600, 760), Vector2(1320, 760)])
	var spots := floor_grid(t, SWEEP_STEP)
	var headings: Array[Vector2] = sm.lattice_headings()
	var skipped := []
	var wrong := []
	var gapless := 0
	for spot in spots:
		t.player.global_position = spot
		var aim: Vector2 = t.player.hurtBox.get_node("CollisionShape2D").global_position
		for from in froms:
			boss.global_position = from
			volley.last_heading = Vector2.ZERO
			var picked: Dictionary = volley._choose_spot()
			if picked.is_empty():
				skipped.append([spot, from])
				continue
			var on_lattice: bool = headings.any(func(h): return h.is_equal_approx(picked.heading))
			var stand: Rect2 = sm.STAND_RECT
			var feet: Vector2 = picked.feet
			var inside := feet.x >= stand.position.x and feet.x <= stand.end.x and feet.y >= stand.position.y and feet.y <= stand.end.y
			if not on_lattice or not inside or picked.range < sm.mystic_range_floor - 0.01 \
					or not (picked.mouth as Vector2).is_equal_approx(aim - picked.heading * picked.range):
				wrong.append([spot, from, picked])
			if feet.distance_to(from) < sm.mystic_spot_gap:
				gapless += 1
	boss.global_position = sm.HOME
	var cases: int = spots.size() * froms.size()
	t.log_p("sweep: %d player spots x %d of his = %d casts; %d needed the gap let go; skipped %s; wrong %s" % [spots.size(), froms.size(), cases, gapless, skipped.slice(0, 8), wrong.slice(0, 4)])
	t.check(skipped.is_empty(), "every cast from every spot of his finds a spot of its own, whatever the player's (%d of %d skipped)" % [skipped.size(), cases])
	t.check(wrong.is_empty(), "each on a lattice line through the player, his feet in STAND_RECT, at least %.0f px out (%d wrong)" % [sm.mystic_range_floor, wrong.size()])


static func first(t) -> void:
	var spots: Array = FIRST_SPOTS.duplicate()
	# Where the fight itself puts them.
	spots.append(Vector2.INF)
	for spot in spots:
		await t.load_matt()
		t.hold_break_gauge(t.boss)
		if spot == Vector2.INF:
			spot = t.player.global_position
		var sm: Node = t.sm
		var volley: Node = sm.states["MysticVolley"]
		t.player.playerHealth = 1000
		var at_home: bool = t.boss.global_position == sm.HOME
		sm._on_post_dialogue_pre_fight_timer_timeout()
		var bolts := {}
		var planned := -1
		for f in 600:
			t.player.global_position = spot
			t.player.velocity = Vector2.ZERO
			if planned < 0 and sm.current_state == volley:
				planned = sm.cycle_casts
			for bolt in sm.live_bolts():
				bolts[bolt.get_instance_id()] = true
			await t.physics_frame
			if sm.current_state.name == "TrueshotBarrage":
				break
		t.log_p("first cycle, the player on %s: %d casts planned, %d spots, %d skipped, %d bolts" % [spot, planned, volley.spots.size(), volley.skipped, bolts.size()])
		t.check(at_home and planned > 0 and volley.skipped == 0 and bolts.size() == planned,
			"from HOME, a player on %s from the start meets every cast of the first volley (%d of %d)" % [spot, bolts.size(), planned])


static func trueshot(t) -> void:
	var sm: Node = t.sm
	var barrage: Node = sm.states["TrueshotBarrage"]
	var landed := []
	t.defense.hit_taken.connect(func(hit): landed.append(hit.attack_id))
	t.player.playerHealth = 100000
	var spots := floor_grid(t, TRUESHOT_STEP)
	var by_count := {}
	var worst := []
	for spot in spots:
		var missed_by := []
		for s in sm.STATIONS.size():
			landed.clear()
			t.clear_iframes()
			for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
				hazard.queue_free()
			sm.on_child_transition(sm.current_state, "Idle")
			sm.beat_timer.stop()
			await t.wait(1)
			sm.on_child_transition(sm.current_state, "TrueshotBarrage")
			barrage.station_index = s
			var released := false
			for f in 150:
				t.player.global_position = spot
				t.player.velocity = Vector2.ZERO
				await t.physics_frame
				released = released or barrage.beat == barrage.Beat.FIRE
				if released and (barrage.beat != barrage.Beat.FIRE or barrage.beat_clock > 0.34):
					break
			for f in 60:
				t.player.global_position = spot
				await t.physics_frame
				if not landed.is_empty() or sm.live_waves().is_empty():
					break
			if not landed.has(&"matt_trueshot"):
				missed_by.append(str(sm.STATIONS[s].name))
		by_count[missed_by.size()] = by_count.get(missed_by.size(), 0) + 1
		if missed_by.size() >= 2:
			worst.append("%s %s" % [spot, missed_by])
	t.log_p("trueshot: spots by how many stations miss them %s (of %d); missed by two or more: %s" % [by_count, spots.size(), worst])
	t.check(not by_count.has(3) and not by_count.has(4), "no standing spot is missed by more than two of the four stations")
