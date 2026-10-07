extends RefCounted

# josh_wild_cards (the user, 2026-09-28): Josh's Wild Cards (JoshCardsWildCards), his first attack since the
# rework. --fixed-fps 60.
#   hud      every drawn piece of his live HUD inside JoshArtLayout.HUD_KEEP_OUT, the keep-out his clones and
#            their badges are placed against.
#   setups   SETUPS whole cycles with the player wandering about: every clone inside the ropes with its
#            throwing hand, never nearer the player than wild_player_clearance, its figure and its badge
#            clear of the live HUD and in view, and in all but CRAMPED_SETUPS of them all of them PLAN_FLOOR
#            apart, and never under SPREAD_FLOOR (both scaled from five to wild_clones); three lanes each, the middle
#            one on where the player's hurtbox was as
#            it appeared and the others wild_spread_degrees either side, from its hand to the ropes, drawn as
#            exactly the box its cards sweep, and unmoved when they leave; the way out from where the player
#            stood as the fifth locked inside the warning, less wild_escape_reaction, and never nearer than a
#            brute-force search of the floor finds; a player who walks there on foot takes nothing from the
#            volley; and he gates back in wild_return_range from the player, clear of the HUD. Over PLANS
#            plans from random player spots, the planner's spread is never under PLAN_FLOOR and at least
#            SPACING at the median; its cost is logged.
#   volley   all the cards on one frame, three down each clone's lanes; a player who never moves is hit,
#            a hit costs a read, and the i-frames keep it to one hit a second.
#   edges    from lanes laid on a still player, one of them a pixel inside its edge is hit, and a pixel
#            outside it isn't.
#   dash     a dash into the first card that reaches a still player is a perfect dodge: no hit, the dash's
#            stamina back and one read; another card of the same volley pays nothing more, and anything
#            else is a read of its own. While he is gone nothing turns the player toward him.
#   window   back in, he is recovering, in view and punchable for recover_time, and a clean combo lands
#            and is a read.
# These test Wild Cards alone: its Gun Hands (JoshGunHands, the addendum of 2026-09-29) are pinned off
# through the gauge spec's reset. josh_guns runs setups() again with them on (its escape tier).

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const BossBroken := preload("res://Scripts/BossBroken.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const CARD_ID := &"josh_wild_card"
const HOME := Vector2(960, 640)
const SEED := 20260928
const SETUPS := 12
# The user's "about 450 px" between five clones. A plan is kept to it at the median and PLAN_FLOOR at the
# least; the setups that may come under PLAN_FLOOR are the ones where the last clone's planned spot was swapped,
# for the player standing by it or for a way out, and SPREAD_FLOOR is the least any of them may come to. Six
# share the same floor since 2026-10-04 (wild_clones): the median spacing scales with the floor each has, by
# sqrt(5 / count), and the two floors with the count (_scaled).
const SPACING := 450.0
const SPACING_COUNT := 5
const CRAMPED_SETUPS := 3
const SPREAD_FLOOR := 300.0
const PLAN_FLOOR := 400.0
# How often the wandering player picks a new way to walk.
const WANDER_STEP := 0.35
# The brute-force search's grid, px. The walk to a gap goes in whole frames of walking, so it stops within
# half a step of the gap, which the gap's own room (JoshCardsWildCards.ESCAPE_ROOM) covers. The wandering
# stops QUIET_FRAMES before the last clone, so no step the keys still owe is left when the walk begins.
const GRID := 4.0
const QUIET_FRAMES := 3
const PLANS := 50
# How much nearer than the game's the brute-force search's way out may be before the game's is called
# optimistic: a step of either grid.
const ESCAPE_AGREE := 0.02
const STILL_SPOT := Vector2(960, 560)
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
# A dash's press lands on the next input flush: pressed this long before the card reaches the player,
# its immunity is up when it does (as test_beam_rush's dash-through).
const DASH_LEAD := 3.5 / 60.0
const DASH_STAMINA := 60.0


static func run(t) -> void:
	# His spec's hooks (reset_gauged, park) are keyed on the fight.
	t.fight = "josh"
	if not await t.load_gauged():
		return
	seed(SEED)
	var wild: Node = t.sm.states["WildCards"]
	t.track()
	await _hud(t)
	await setups(t, wild)
	await _volley(t, wild)
	await _edges(t, wild)
	await _dash(t, wild)
	await _window(t, wild)


#THE HUD

static func _hud(t) -> void:
	t.log_p("-- the live HUD, held to his keep-out")
	await t.reset_gauged(HOME)
	var hud: Array = t.carter_hud_rects()
	var loose: Array = hud.filter(func(r: Rect2) -> bool: return not JoshArtLayout.HUD_KEEP_OUT.any(func(k: Rect2) -> bool: return k.encloses(r)))
	t.log_p("%d pieces of HUD drawn: %s" % [hud.size(), hud])
	t.check(hud.size() > 5 and loose.is_empty(), "every piece of his HUD is inside JoshArtLayout.HUD_KEEP_OUT (outside it: %s)" % [loose])


#WHOLE SETUPS

# With `guns`, his Gun Hands are turned back on after each reset.
static func setups(t, wild: Node, guns := false) -> void:
	var sm: Node = t.sm
	var art_hud: Array = t.carter_hud_rects()
	var speed: float = t.player.SPEED
	var reaction: float = sm.wild_escape_reaction
	var spot_area: Rect2 = sm.ROPES.grow_individual(-(absf(JoshArtLayout.local(JoshArtLayout.HAND_THROW).x) + wild.SPOT_HAND_MARGIN), 0.0, -(absf(JoshArtLayout.local(JoshArtLayout.HAND_THROW).x) + wild.SPOT_HAND_MARGIN), -wild.SPOT_BOTTOM_MARGIN)
	var bad_spots: Array = []
	var near_player: Array = []
	var off_hud: Array = []
	var bad_aims: Array = []
	var bad_lanes: Array = []
	var bad_bands: Array = []
	var moved_lanes: Array = []
	var cramped: Array = []
	var escapes: Array = []
	var bad_escapes: Array = []
	var disagree: Array = []
	var cautious: Array = []
	var search_us: Array = []
	var hit_in_gap: Array = []
	var late_walks: Array = []
	var returns: Array = []
	var bad_returns: Array = []
	var gone_target: Array = []
	for s in SETUPS:
		await t.reset_gauged(HOME)
		if guns:
			sm.wild_guns = true
		t.hold_break_gauge(t.boss)
		await t.settle_player(Vector2(randf_range(400, 1500), randf_range(300, 850)))
		var held := {}
		var seen := {"spawns": [], "dirs": [], "standing": Vector2.INF, "warn": false, "hits": 0, "badges": [], "gone_target": false, "walk": Vector2.INF, "steps": Vector2i.ZERO, "arrived": INF, "clear_at_fire": false}
		var on_hit := func(hit: RefCounted) -> void:
			if hit.attack_id == CARD_ID:
				seen.hits += 1
		t.defense.hit_taken.connect(on_hit)
		var wander := Vector2.ZERO
		var wander_left := 0.0
		var before: Vector2 = _hurt_centre(t)
		sm.start_cycle()
		_note_spawns(t, wild, seen, before)
		var fired := false
		for i in 900:
			before = _hurt_centre(t)
			if wild.beat == wild.Beat.HOP:
				wander_left -= FRAME
				if wander_left <= 0.0:
					wander_left = WANDER_STEP
					wander = Vector2(randi_range(-1, 1), randi_range(-1, 1))
				var quiet: bool = wild.clones.size() == sm.wild_clones - 1 and wild.beat_clock >= sm.wild_hop_time - QUIET_FRAMES * FRAME
				_steer(t, held, Vector2.ZERO if quiet else wander)
			elif wild.beat == wild.Beat.WARN:
				if not seen.warn:
					seen.warn = true
					seen.standing = t.player.global_position
					seen.walk = _nearest_gap(t, wild, t.player.global_position, wild.ESCAPE_ROOM, speed * wild.warn_time)
					seen.steps = _steps_to(t, seen.walk)
				if wild.gone and not seen.gone_target:
					seen.gone_target = true
					if t.boss.hurtbox.is_in_group("boss_target"):
						gone_target.append(s)
				if seen.badges.is_empty():
					for tell in t.live_tells():
						if tell.sprite:
							seen.badges.append(t.carter_drawn_rect(tell.sprite))
				_step_walk(t, held, seen)
				if seen.arrived == INF and seen.walk != Vector2.INF and seen.steps == Vector2i.ZERO:
					seen.arrived = wild.beat_clock
			else:
				_steer(t, held, Vector2.ZERO)
				if not fired:
					fired = true
					seen.clear_at_fire = wild.lane_boxes().all(func(b): return not wild.box_hits(b, t.area_rect(t.player.hurtBox)))
					for k in wild.clones.size():
						var clone: Object = wild.clones[k]
						for j in clone.lanes.size():
							if not seen.dirs[k][j].is_equal_approx(clone.lanes[j].dir):
								moved_lanes.append([s, k, j])
			if sm.current_state.name == "Recover":
				returns.append(t.boss.ground_position.distance_to(t.player.global_position))
				if not JoshArtLayout.clear_of_hud(JoshArtLayout.standing_rect(t.boss.ground_position)) or not t.boss.ground_bounds(0.0).has_point(t.boss.ground_position):
					bad_returns.append([s, t.boss.ground_position])
				break
			await t.physics_frame
			_note_spawns(t, wild, seen, before)
		t.defense.hit_taken.disconnect(on_hit)
		_steer(t, held, Vector2.ZERO)

		var spawns: Array = seen.spawns
		t.check(spawns.size() == sm.wild_clones and fired, "setup %d: five clones, and the volley" % s)
		for k in spawns.size():
			var sp: Dictionary = spawns[k]
			if not spot_area.grow(0.5).has_point(sp.feet) or not sm.ROPES.has_point(sp.hand):
				bad_spots.append([s, k, sp.feet])
			if sp.feet.distance_to(sp.player) < sm.wild_player_clearance - SLACK:
				near_player.append([s, k, snappedf(sp.feet.distance_to(sp.player), 0.1)])
			if not JoshArtLayout.clear_of_hud(JoshArtLayout.standing_rect(sp.feet)) or t.carter_hud_gap(sp.drawn, art_hud) <= 0.0:
				off_hud.append([s, k, sp.feet])
			if sp.aim_off > 0.5:
				bad_aims.append([s, k, snappedf(sp.aim_off, 0.01)])
			if not sp.lanes_ok:
				bad_lanes.append([s, k])
			if not sp.band_ok:
				bad_bands.append([s, k])
		for badge in seen.badges:
			if t.carter_hud_gap(badge, art_hud) <= 0.0:
				off_hud.append([s, "badge", badge])
		var spread := INF
		for a in spawns.size():
			for b in range(a + 1, spawns.size()):
				spread = minf(spread, spawns[a].feet.distance_to(spawns[b].feet))
		if spread < _scaled(sm, PLAN_FLOOR):
			cramped.append([s, snappedf(spread, 0.1)])

		# The way out, from where the player stood as the fifth locked.
		var boxes: Array[Dictionary] = []
		for clone in wild.clones:
			for lane in clone.lanes:
				boxes.append(wild.lane_box(lane.origin, lane.dir, lane.length, sm.wild_card_size))
		var searched_at: int = Time.get_ticks_usec()
		wild.escape_time_from(boxes, seen.standing, sm.wild_warning_cap)
		search_us.append(Time.get_ticks_usec() - searched_at)
		var brute: Vector2 = _nearest_gap(t, wild, seen.standing, wild.ESCAPE_ROOM, speed * sm.wild_warning_cap, boxes)
		var brute_time: float = INF if brute == Vector2.INF else _walk_distance(seen.standing, brute) / speed
		escapes.append([snappedf(wild.escape_time, 0.001), snappedf(wild.warn_time, 0.001)])
		if wild.escape_time > wild.warn_time - reaction + SLACK:
			bad_escapes.append([s, wild.escape_time, wild.warn_time])
		if wild.escape_time < brute_time - ESCAPE_AGREE:
			disagree.append([s, snappedf(wild.escape_time, 0.001), snappedf(brute_time, 0.001)])
		elif wild.escape_time > brute_time + ESCAPE_AGREE:
			cautious.append([s, snappedf(wild.escape_time, 0.001), snappedf(brute_time, 0.001)])
		if seen.hits > 0 or not seen.clear_at_fire:
			hit_in_gap.append([s, seen.hits, seen.walk, t.player.global_position])
		# The last step held moves the player a frame later.
		if seen.arrived == INF or seen.arrived + FRAME > wild.warn_time + SLACK:
			late_walks.append([s, seen.arrived, wild.warn_time])
		t.log_p("setup %d: spots %s, spread %.0f, escape %.3f s (brute %.3f) of a %.3f s warning, walked %s in %.3f s, %d hits" % [s, spawns.map(func(sp): return sp.feet), spread, wild.escape_time, brute_time, wild.warn_time, seen.walk, seen.arrived, seen.hits])

	t.log_p("-- %d setups" % SETUPS)
	t.check(bad_spots.is_empty(), "every clone stands inside the ropes with its throwing hand (%s)" % [bad_spots])
	t.check(near_player.is_empty(), "never nearer the player than %.0f px (%s)" % [sm.wild_player_clearance, near_player])
	t.check(off_hud.is_empty(), "every clone and every badge clear of the live HUD and in view (%s)" % [off_hud])
	t.check(cramped.size() <= CRAMPED_SETUPS and cramped.all(func(c): return c[1] >= _scaled(sm, SPREAD_FLOOR)), "all %d at least %.0f px apart in all but %d setups, and never under %.0f (closer: %s)" % [sm.wild_clones, _scaled(sm, PLAN_FLOOR), CRAMPED_SETUPS, _scaled(sm, SPREAD_FLOOR), cramped])
	t.check(bad_aims.is_empty(), "each clone's middle lane runs through where the player's hurtbox was as it appeared (%s)" % [bad_aims])
	t.check(bad_lanes.is_empty(), "three lanes, %.0f degrees apart, from its hand to the ropes (%s)" % [sm.wild_spread_degrees, bad_lanes])
	t.check(bad_bands.is_empty(), "each drawn as exactly the box its cards sweep (%s)" % [bad_bands])
	t.check(moved_lanes.is_empty(), "and none has moved when the cards leave, wherever the player went (%s)" % [moved_lanes])
	t.log_p("escapes and warnings: %s" % [escapes])
	t.check(bad_escapes.is_empty(), "from where the player stood as the fifth locked, a way out on foot inside the warning less %.2f s (%s)" % [reaction, bad_escapes])
	t.check(disagree.is_empty(), "the game never counts on a way out nearer than a brute-force search of the floor finds (%s)" % [disagree])
	search_us.sort()
	t.log_p("where it was more cautious than the brute force by over %.2f s: %s; its search took %d to %d us" % [ESCAPE_AGREE, cautious, search_us[0], search_us[-1]])
	t.check(late_walks.is_empty(), "a player walking there gets there in time (%s)" % [late_walks])
	t.check(hit_in_gap.is_empty(), "and standing there, clear of every lane as the cards leave, no card touches them (%s)" % [hit_in_gap])
	t.check(gone_target.is_empty(), "while he is gone the player has nothing of his to face (%s)" % [gone_target])
	t.log_p("he came back %s px from the player" % [returns.map(func(d): return roundi(d))])
	var span: Vector2 = sm.wild_return_range
	t.check(returns.size() == SETUPS and returns.all(func(d: float) -> bool: return d >= span.x - SLACK and d <= span.y + SLACK), "he gates back in %.0f to %.0f px from the player" % [span.x, span.y])
	t.check(bad_returns.is_empty(), "on his floor, in view and clear of the HUD (%s)" % [bad_returns])

	var spreads: Array = []
	var took: Array = []
	for i in PLANS:
		var from := Vector2(randf_range(300, 1600), randf_range(250, 900))
		var start: int = Time.get_ticks_usec()
		var plan: Array[Vector2] = wild.plan_spots(from)
		took.append(Time.get_ticks_usec() - start)
		spreads.append(roundi(wild.spread_of(plan)) if plan.size() == sm.wild_clones else -1)
	spreads.sort()
	took.sort()
	t.log_p("%d plans from a random player spot: spreads %s; %d to %d us, median %d" % [PLANS, spreads, took[0], took[-1], took[PLANS / 2]])
	var median_spacing: float = SPACING * sqrt(float(SPACING_COUNT) / sm.wild_clones)
	t.check(spreads[0] >= _scaled(sm, PLAN_FLOOR) and spreads[PLANS / 2] >= median_spacing, "every plan places all %d at least %.0f px apart, %.0f at the median (%d, %d)" % [sm.wild_clones, _scaled(sm, PLAN_FLOOR), median_spacing, spreads[0], spreads[PLANS / 2]])


# A distance the user gave for five clones, for however many there are: each has 5/count of the floor's spots.
static func _scaled(sm: Node, five: float) -> float:
	return five * SPACING_COUNT / sm.wild_clones


# A clone that appeared since the last look: where it stands, where the player was, and whether its lanes are
# what they should be.
static func _note_spawns(t, wild: Node, seen: Dictionary, before: Vector2) -> void:
	var sm: Node = t.sm
	while seen.spawns.size() < wild.clones.size():
		var clone: Object = wild.clones[seen.spawns.size()]
		var now: Vector2 = _hurt_centre(t)
		var aim_off: float = minf(clone.aimed_at.distance_to(now), clone.aimed_at.distance_to(before))
		var hand: Vector2 = clone.feet + JoshArtLayout.local(JoshArtLayout.HAND_THROW, clone.flip)
		var lanes_ok: bool = clone.lanes.size() == 3
		var band_ok := true
		var dirs: Array = []
		for j in clone.lanes.size():
			var lane: Object = clone.lanes[j]
			dirs.append(lane.dir)
			var want_angle: float = (clone.aimed_at - hand).angle() + deg_to_rad(sm.wild_spread_degrees) * (j - 1)
			var end: Vector2 = lane.origin + lane.dir * lane.length
			var on_edge: bool = sm.ROPES.grow(0.5).has_point(end) and not sm.ROPES.grow(-0.5).has_point(end)
			lanes_ok = lanes_ok and lane.origin.distance_to(hand) < 0.01 and absf(angle_difference(lane.dir.angle(), want_angle)) < 0.0005 and on_edge
			var corners: PackedVector2Array = wild.box_corners(wild.lane_box(lane.origin, lane.dir, lane.length, sm.wild_card_size))
			band_ok = band_ok and is_instance_valid(lane.band) and _same_points(lane.band.polygon, corners) and _same_points(lane.rim.points, corners)
		seen.dirs.append(dirs)
		seen.spawns.append({"feet": clone.feet, "hand": hand, "player": t.player.global_position, "aim_off": aim_off,
			"lanes_ok": lanes_ok, "band_ok": band_ok, "drawn": t.carter_drawn_rect(clone.figure)})


#THE VOLLEY

static func _volley(t, wild: Node) -> void:
	var sm: Node = t.sm
	var gauge: Node = t.boss.break_gauge
	t.log_p("-- a player who never moves")
	var per_volley: Array = []
	var losses: Array = []
	var together := true
	var counts: Array = []
	for v in 3:
		await t.reset_gauged(HOME)
		await t.settle_player(STILL_SPOT)
		gauge.value = 50.0
		var hits: Array = []
		var on_hit := func(hit: RefCounted) -> void:
			if hit.attack_id == CARD_ID:
				hits.append(t.defense.clock)
		t.defense.hit_taken.connect(on_hit)
		var cards_seen: Array = []
		var watch := func(node: Node) -> void:
			if node.get_child_count() > 0 and node.get_child(0) is Sprite2D and (node.get_child(0) as Sprite2D).texture.resource_path.ends_with("card_projectile.png"):
				cards_seen.append(Engine.get_physics_frames())
		t.boss.sky_layer.child_entered_tree.connect(watch)
		sm.start_cycle()
		await t.wait_until(func(): return sm.current_state.name == "Recover", 900)
		t.boss.sky_layer.child_entered_tree.disconnect(watch)
		t.defense.hit_taken.disconnect(on_hit)
		counts.append(cards_seen.size())
		together = together and cards_seen.size() == 3 * sm.wild_clones and cards_seen.all(func(f): return f == cards_seen[0])
		per_volley.append(hits.size())
		losses.append(50.0 - gauge.value)
		var apart := true
		for k in range(1, hits.size()):
			apart = apart and hits[k] - hits[k - 1] >= t.player.invincibility_timer.wait_time - FRAME
		t.check(apart, "volley %d: its hits a second of i-frames apart (%s)" % [v, hits])
	t.log_p("cards seen %s; hits a volley %s; gauge lost %s" % [counts, per_volley, losses])
	t.check(together, "all %d cards, three a clone, leave on one frame" % (3 * sm.wild_clones))
	t.check(per_volley.all(func(n): return n >= 1), "a player who never moves is hit every volley")
	var read: float = gauge.hit_loss
	var drained := true
	for v in per_volley.size():
		drained = drained and is_equal_approx(losses[v], read * per_volley[v])
	t.check(drained, "and each hit takes a read back off his gauge (%s)" % [losses])


#ONE LANE'S EDGE

static func _edges(t, wild: Node) -> void:
	var sm: Node = t.sm
	t.log_p("-- a pixel inside a lane's edge, and a pixel outside it")
	var results := {}
	var used := []
	for side in ["inside", "outside"]:
		await t.reset_gauged(HOME)
		t.hold_break_gauge(t.boss)
		await t.settle_player(STILL_SPOT)
		wild.forced_spots.assign([Vector2(560, 640), Vector2(1500, 820), Vector2(1400, 420), Vector2(640, 380), Vector2(1600, 600)])
		sm.start_cycle()
		await t.wait_until(func(): return wild.beat == wild.Beat.WARN, 600)
		var pair: Array = _edge_pair(t, wild)
		if pair.is_empty():
			t.check(false, "a lane with an edge clear of the others")
			return
		used.append(pair)
		await t.settle_player(pair[0] if side == "inside" else pair[1])
		var hits: Array = []
		var on_hit := func(hit: RefCounted) -> void:
			if hit.attack_id == CARD_ID:
				hits.append(hit.source)
		t.defense.hit_taken.connect(on_hit)
		await t.wait_until(func(): return wild.beat == wild.Beat.RETURN or sm.current_state.name != "WildCards", 600)
		t.defense.hit_taken.disconnect(on_hit)
		results[side] = hits.size()
		t.log_p("%s at %s: %d hits" % [side, t.player.global_position, hits.size()])
	t.check(used.size() == 2 and used[0] == used[1], "the same lanes both times, so the same edge (%s)" % [used])
	t.check(results.get("inside", 0) == 1, "a pixel inside it, the card hits (%d)" % results.get("inside", 0))
	t.check(results.get("outside", -1) == 0, "a pixel outside it, nothing does (%d)" % results.get("outside", -1))


# A row on which one lane's edge is clear of every other lane: the player's body positions a pixel inside it
# and a pixel outside it, [inside, outside], found with box_hits alone. [] if no lane has one.
static func _edge_pair(t, wild: Node) -> Array:
	var sm: Node = t.sm
	var offset: Rect2 = _hurt_offset(t)
	var area: Rect2 = BossBroken.PLAYER_AREA
	var boxes: Array = []
	for clone in wild.clones:
		for lane in clone.lanes:
			boxes.append(wild.lane_box(lane.origin, lane.dir, lane.length, sm.wild_card_size))
	for index in boxes.size():
		var own: Dictionary = boxes[index]
		var others: Array = boxes.filter(func(b): return b != own)
		for step in range(4, 17):
			var along: Vector2 = own.centre + own.dir * own.half.x * (step / 10.0 - 1.0)
			var centre: Vector2 = along - offset.get_center()
			for way in [-1.0, 1.0]:
				var inside: Vector2 = centre
				var outside: Vector2 = centre + Vector2(way * 300.0, 0.0)
				if wild.box_hits(own, Rect2(outside + offset.position, offset.size)):
					continue
				for i in 50:
					var mid: Vector2 = (inside + outside) / 2.0
					if wild.box_hits(own, Rect2(mid + offset.position, offset.size)):
						inside = mid
					else:
						outside = mid
				var a: Vector2 = outside - Vector2(way, 0.0)
				var b: Vector2 = outside + Vector2(way, 0.0)
				var ra := Rect2(a + offset.position, offset.size)
				var rb := Rect2(b + offset.position, offset.size)
				if not area.has_point(a) or not area.has_point(b):
					continue
				if not wild.box_hits(own, ra) or wild.box_hits(own, rb):
					continue
				if others.any(func(o): return wild.box_hits(o, ra) or wild.box_hits(o, rb)):
					continue
				return [a, b]
	return []


#A DASH THROUGH A CARD

static func _dash(t, wild: Node) -> void:
	var sm: Node = t.sm
	var defense: Node = t.defense
	var gauge: Node = t.boss.break_gauge
	t.log_p("-- a dash into the first card to reach a still player")
	await t.reset_gauged(HOME)
	await t.settle_player(STILL_SPOT)
	await t.dash_ready()
	var dodges: Array = []
	var on_dodge := func(hit: RefCounted) -> void:
		dodges.append({"id": hit.attack_id, "source": hit.source, "stamina": defense.stamina, "gauge": gauge.value})
	defense.perfect_dodged.connect(on_dodge)
	var hits := [0]
	var on_hit := func(hit: RefCounted) -> void:
		if hit.attack_id == CARD_ID:
			hits[0] += 1
	defense.hit_taken.connect(on_hit)
	sm.start_cycle()
	await t.wait_until(func(): return wild.beat == wild.Beat.VOLLEY, 600)
	var first: Array = _first_contact(t, wild)
	var health: int = t.player.playerHealth
	defense._set_stamina(DASH_STAMINA)
	defense.last_spend_time = defense.clock
	var toward: Vector2 = -first[1]
	var held := {}
	var pressed := false
	var after_dash := INF
	for i in 240:
		var into: float = wild.fx_clock - wild.fired_at
		if not pressed and into >= first[0] - DASH_LEAD:
			pressed = true
			_steer(t, held, Vector2(signf(roundf(toward.x * 2.0) / 2.0), signf(roundf(toward.y * 2.0) / 2.0)))
			t.tap(KEY_W)
		if pressed and after_dash == INF and t.player.is_dodging:
			after_dash = defense.stamina
		if pressed and not t.player.is_dodging and after_dash != INF:
			_steer(t, held, Vector2.ZERO)
		if not dodges.is_empty() or wild.beat != wild.Beat.VOLLEY:
			break
		await t.physics_frame
	_steer(t, held, Vector2.ZERO)
	var dodge: Dictionary = dodges[0] if not dodges.is_empty() else {}
	t.log_p("first contact %.3f s in, from %s; perfect dodges %s; stamina %.2f before, %.2f dashing; health %d -> %d" % [first[0], first[1], dodges.map(func(d): return [d.id, snappedf(d.stamina, 0.01), d.gauge]), DASH_STAMINA, after_dash, health, t.player.playerHealth])
	t.check(not dodges.is_empty() and dodge.id == CARD_ID, "a perfect dodge")
	t.check(hits[0] == 0 and t.player.playerHealth == health, "and no hit")
	t.check(not dodges.is_empty() and absf(after_dash - (DASH_STAMINA - defense.dash_stamina_cost)) < 0.5 and absf(dodge.stamina - DASH_STAMINA) < 0.5, "the dash cost its %.1f stamina and the perfect dodge gave it back (%.2f)" % [defense.dash_stamina_cost, dodge.get("stamina", -1.0)])
	t.check(not dodges.is_empty() and is_equal_approx(gauge.value, gauge.perfect_dodge_gain), "one read on his gauge (%.3f)" % gauge.value)

	var other: Object = null
	for card in wild.cards:
		if card.node != dodge.get("source"):
			other = card
			break
	var paid: float = gauge.value
	gauge._on_perfect_dodged(HitInfo.make(CARD_ID, other.node if other else null, Vector2.ZERO))
	var again: float = gauge.value
	var elsewhere: Node2D = t.dummy_source()
	gauge._on_perfect_dodged(HitInfo.make(CARD_ID, elsewhere, Vector2.ZERO))
	t.log_p("another card of the volley: %.3f -> %.3f; something else: -> %.3f" % [paid, again, gauge.value])
	t.check(other != null and again == paid, "another card of the same volley dodged pays nothing more")
	t.check(is_equal_approx(gauge.value, paid + gauge.perfect_dodge_gain), "anything that isn't one of its cards is a read of its own")
	defense.perfect_dodged.disconnect(on_dodge)
	defense.hit_taken.disconnect(on_hit)
	await t.wait_until(func(): return sm.current_state.name != "WildCards", 600)


# When the first card's square reaches the still player's hurtbox, in seconds from the volley, and which way
# it is flying: [time, dir].
static func _first_contact(t, wild: Node) -> Array:
	var hurt: Rect2 = t.area_rect(t.player.hurtBox)
	var best := [INF, Vector2.RIGHT]
	for card in wild.cards:
		var lane: Object = card.lane
		var d := 0.0
		while d <= lane.length:
			if wild.box_hits(wild.card_box(lane.origin, lane.dir, d, t.sm.wild_card_size), hurt):
				var at: float = d / t.sm.wild_card_speed
				if at < best[0]:
					best = [at, lane.dir]
				break
			d += 1.0
	return best


#HIS WINDOW

static func _window(t, wild: Node) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var gauge: Node = boss.break_gauge
	t.log_p("-- back in, winded")
	await t.reset_gauged(HOME)
	await t.settle_player(Vector2(500, 800))
	sm.start_cycle()
	var back: bool = await t.wait_until(func(): return sm.current_state.name == "Recover", 900)
	var back_at: float = t.defense.clock
	await t.wait(2)
	var shown: bool = boss.air.visible and boss.shadow.visible and boss.hurtbox.is_in_group("boss_target")
	var open: bool = boss.hurtbox.monitorable and boss.can_be_dazed() and not sm.recover_timer.is_stopped()
	t.log_p("back at %s, the player at %s; recover timer %.2f s" % [boss.ground_position, t.player.global_position, sm.recover_timer.wait_time])
	t.check(back and shown, "he gates back in, in view, and the player faces him again")
	t.check(open and is_equal_approx(sm.recover_timer.wait_time, sm.recover_time), "his punish window is open, for %.1f s" % sm.recover_time)
	t.place_under(boss.get_finisher_hurtbox())
	await t.wait(6)
	var health: int = boss.boss_health
	var gauge_before: float = gauge.value
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)
	var landed_at: float = t.defense.clock - back_at
	t.log_p("the combo: %d -> %d health, gauge %.3f -> %.3f, %.2f s into the window" % [health, boss.boss_health, gauge_before, gauge.value, landed_at])
	t.check(boss.boss_health < health, "a punish lands")
	t.check(is_equal_approx(gauge.value - gauge_before, 2.0 * gauge.punch_gain + gauge.charged_punch_gain) and is_equal_approx(2.0 * gauge.punch_gain + gauge.charged_punch_gain, 100.0 / t.fight_spec.reads_to_break), "and a clean combo is a read (%.3f)" % (gauge.value - gauge_before))
	t.check(landed_at < sm.recover_time, "inside his window (%.2f s)" % landed_at)
	await t.wait_until(func(): return t.player.get_node("Finisher").phase == t.FINISHER_OFF, 600)


#WHERE THINGS ARE

static func _hurt_centre(t) -> Vector2:
	return t.area_rect(t.player.hurtBox).get_center()


static func _hurt_offset(t) -> Rect2:
	var rect: Rect2 = t.area_rect(t.player.hurtBox)
	return Rect2(rect.position - t.player.global_position, rect.size)


# The body position nearest `from` - walked, so a square - where the hurtbox, grown by `margin`, touches none
# of the lanes, on the floor and no further than `reach`: a GRID-px search ring by ring. INF if none.
static func _nearest_gap(t, wild: Node, from: Vector2, margin: float, reach: float, boxes: Array = []) -> Vector2:
	if boxes.is_empty():
		boxes = []
		for clone in wild.clones:
			for lane in clone.lanes:
				boxes.append(wild.lane_box(lane.origin, lane.dir, lane.length, t.sm.wild_card_size))
	var offset: Rect2 = _hurt_offset(t).grow(margin)
	var area: Rect2 = BossBroken.PLAYER_AREA
	var start: Vector2 = from.clamp(area.position, area.end)
	for r in int(ceilf(reach / GRID)) + 1:
		var best := Vector2.INF
		var ring: Array = []
		if r == 0:
			ring.append(Vector2.ZERO)
		else:
			for i in range(-r, r + 1):
				ring.append(Vector2(i, -r))
				ring.append(Vector2(i, r))
			for j in range(-r + 1, r):
				ring.append(Vector2(-r, j))
				ring.append(Vector2(r, j))
		for cell in ring:
			var at: Vector2 = start + cell * GRID
			if not area.has_point(at):
				continue
			var rect := Rect2(at + offset.position, offset.size)
			if boxes.all(func(b): return not wild.box_hits(b, rect)):
				best = at
				break
		if best != Vector2.INF:
			return best
	return Vector2.INF


static func _walk_distance(from: Vector2, to: Vector2) -> float:
	return maxf(absf(to.x - from.x), absf(to.y - from.y))


static func _same_points(a: PackedVector2Array, b: PackedVector2Array) -> bool:
	if a.size() != b.size():
		return false
	for i in a.size():
		if a[i].distance_to(b[i]) > 0.01:
			return false
	return true


#THE PLAYER'S KEYS

static func _steer(t, held: Dictionary, way: Vector2) -> void:
	_hold(t, held, KEY_RIGHT, way.x > 0.0)
	_hold(t, held, KEY_LEFT, way.x < 0.0)
	_hold(t, held, KEY_DOWN, way.y > 0.0)
	_hold(t, held, KEY_UP, way.y < 0.0)


# The whole frames of walking each axis takes to `point`, signed: a frame a key is held is a step of
# SPEED / 60 px, so the walk stops within half a step of it.
static func _steps_to(t, point: Vector2) -> Vector2i:
	if point == Vector2.INF:
		return Vector2i.ZERO
	var step: float = t.player.SPEED / 60.0
	var go: Vector2 = point - t.player.global_position
	return Vector2i(roundi(go.x / step), roundi(go.y / step))


# A frame of the walk: the keys for the steps left held, and counted off.
static func _step_walk(t, held: Dictionary, seen: Dictionary) -> void:
	var left: Vector2i = seen.steps
	var way := Vector2i(signi(left.x), signi(left.y))
	_steer(t, held, Vector2(way))
	seen.steps = left - way


static func _hold(t, held: Dictionary, code: int, down: bool) -> void:
	if held.get(code, false) == down:
		return
	held[code] = down
	if down:
		t.press(code)
	else:
		t.release(code)
