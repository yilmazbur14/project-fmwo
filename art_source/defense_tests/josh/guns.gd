extends RefCounted

# josh_guns (the user, 2026-09-29; the hands addendum's Part 2): the Gun Hands (JoshGunHands), a layer inside Josh's
# Wild Cards, on whichever art is in. --fixed-fps 60, one tier a run (tier=; normal is layer). Each run starts from
# Idle after the gauge spec's reset (his order pinned to Wild Cards, the guns pinned off), with the guns turned back on.
#   layer    one Wild Cards with the player standing mid-floor, then two with the rows pinned to the ends of their
#            ranges (each hand at its bottom once, the other at its top): the hands leave REST at Enter as guns-to-be,
#            are guns at their posts by 0.40 and sweep inside their row ranges in opposite phase; they stop at 1.90
#            and hold their rows after the glide, fire at 2.90 to the frame, stay live for 0.35, are freed by 3.45 and
#            are home in REST, hands again, by 3.75 and a frame; the clones at 0, 0.7, 1.4 and 2.1, the fifth on the
#            first step at or after 3.60; the yellow badge from the stop to the fire and never otherwise, its tip on
#            the aimed band's top edge over the player; every frame, every hand in the air has its box in view and
#            clear of the HUD keep-outs, the flights too; hands at z 2, each telegraph on the FloorLayer over the lanes
#            and exactly its band, each beam on the SkyLayer drawn over exactly its band, with no glow; the charge
#            effect growing through whole-number scales; the bars fading only while a band crosses them, and back.
#   rows     choose_rows over a 12 x 8 grid of player centres, the four corners and the rope strips: the far hand
#            aims (the right below the left's reach), at the centre's row clamped to its range; the other row is
#            gun_row_offset toward more floor, clamped, or the other way if that leaves no room; the rows at least a
#            band and a hurtbox apart; from every centre a band-free spot within WALK_REACH of walking; and the
#            aimed band holds the player everywhere but the corner behind the right muzzle (the addendum's).
#   hit      a still player in the aimed row: exactly one HIT, its catalogue damage (a whole heart since 2026-10-04)
#            and one read off his gauge.
#   walk     a step out of the aimed band, away from the other, 0.2 s after the stop, for 0.2 s: clear of both
#            bands at the fire, and no hit.
#   dash     a dash across the aimed band timed to the fire: DODGED or a near miss through the dash's ghost, one
#            perfect dodge giving the dash back, one read on his gauge, unhurt.
#   edges    the rows pinned (forced_rows): the hurtbox a pixel inside the aimed band's top edge, then its bottom
#            edge, is hit; a pixel outside either isn't.
#   escape   josh_wild_cards' setups with the guns on: every check of theirs passes, the guns fire in every setup,
#            and at the fifth hop and on every WARN and VOLLEY step no beam or telegraph of theirs is left.
#   break    a Break in the sweep, in the charge and with the beams live: Broken; no beam, telegraph, badge (the
#            aiming hand's too) or Timer left; the layer let go; both hands gone into their portals, which loop on;
#            the next cycle forms them again, and the guns wait for it.
#   release  paused mid-charge for 60 frames: no clock, hand, telegraph, charge or badge moves, and the fire keeps
#            its time; the player beaten mid-charge: the hands fly home, hands again, and nothing is left; the scene
#            reloaded with the beams live; him beaten mid-sweep: the hands shatter and the portals close, all four
#            gone within a second.
#   art      the gun art as shipped, read off disk: every gun clip and its glow 128x128 frames, as many as GUN_CLIPS
#            has, and gun_form's box on each frame, glow included, the one GUN_FORM_BOXES_TEXELS has for it (what a
#            hand's drawn_rect uses); the beam's pieces as GUN_BEAM has them, 20 texels tall (the hit band), and its glow;
#            the flash and the charge effect as JoshHandsLayout has them. What is shipped but not yet imported is
#            checked and named; the game plays the placeholders until it is imported.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const BossBroken := preload("res://Scripts/BossBroken.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const WildCardsTest := preload("res://art_source/defense_tests/josh/wild_cards.gd")

const BEAM_ID := &"josh_gun_beam"
# His park (the gauge spec's home), and where the player stands: left of the ring's middle, so the right hand aims,
# and mid-floor, so the other row is cut off above them.
const HOME := Vector2(960, 640)
const STILL := Vector2(600, 560)
const SEED := 20260929
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
const WALK_AFTER := 0.2
const WALK_TIME := 0.2
const DASH_LEAD := 3.0 / 60.0
const GAUGE_START := 50.0
# The edges tier's rows: the right hand aims on the player's row, the left well clear above it.
const EDGE_ROWS := {aimer = &"right", rows = {&"right": 560.0, &"left": 260.0}}
# The rows tier: the grid of player centres, the points along each rope strip, how far a player may walk to a
# band-free spot (the 1.0 s charge less a 0.2 s reaction, at 600 px/s), and the search's step.
const GRID := Vector2i(12, 8)
const STRIP_POINTS := 24
const WALK_REACH := 480.0
const SEARCH_STEP := 4.0
const LOGGED := 4
const TIERS := ["layer", "rows", "hit", "walk", "dash", "edges", "escape", "break", "release", "art"]


static func run(t) -> void:
	var tier: String = "layer" if t.tier == "normal" else t.tier
	if not tier in TIERS:
		t.check(false, "tier is one of %s (%s)" % [TIERS, tier])
		return
	if tier == "art":
		_art(t)
		return
	t.fight = "josh"
	if not await t.load_gauged():
		return
	seed(SEED)
	match tier:
		"layer":
			await _layer(t)
		"rows":
			_rows(t)
		"hit", "walk", "dash":
			await _answered(t, tier)
		"edges":
			await _edges(t)
		"escape":
			await _escape(t)
		"break":
			await _break(t)
		"release":
			await _release(t)


#SETTING UP

static func _wild(t) -> Node:
	return t.sm.states["WildCards"]


static func _guns(t) -> Node:
	return _wild(t).guns


# At his home, idle, his hands home and the guns on, the player fresh at `start` with every key up, a full bar and no
# hype.
static func _reset(t, start: Vector2) -> void:
	await t.reset_gauged(HOME)
	t.sm.wild_guns = true
	_guns(t).forced_rows = {}
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W]:
		t.release(code)
	t.defense._set_stamina(t.defense.max_stamina)
	t.player.get_node("Hype")._set_hype(0.0)
	t.player.playerHealth = 1000
	await t.settle_player(start)
	await t.wait(40)


# When `phase` is due, on the layer's own clock.
static func _due(guns: Node, phase: int) -> float:
	for entry in guns.schedule:
		if entry[1] == phase:
			return entry[0]
	return INF


static func _on_beat(at: float, want: float) -> bool:
	return at >= want - SLACK and at < want + FRAME + SLACK


static func _hurt(t) -> Rect2:
	return t.area_rect(t.player.hurtBox)


# The player's hurtbox round their body position.
static func _hurt_offset(t) -> Rect2:
	var rect := _hurt(t)
	return Rect2(rect.position - t.player.global_position, rect.size)


# Every beam and telegraph of the guns still in play.
static func _gun_nodes(t) -> Array:
	return t.live_hazards().filter(func(h): return str(h.name).contains("JoshGunBeam") or str(h.name).contains("JoshGunTell"))


# The key that walks the player away from the other hand's row.
static func _away_key(guns: Node) -> int:
	var other: StringName = Layout.other_side(guns.aimer)
	return KEY_DOWN if guns.rows[other] < guns.rows[guns.aimer] else KEY_UP


static func _names(guns: Node) -> Array:
	return guns.results.map(func(r): return "NEAR_MISS" if r.result == guns.NEAR_MISS else HitInfo.Result.keys()[r.result])


static func _corners(box: Rect2) -> PackedVector2Array:
	return PackedVector2Array([box.position, Vector2(box.end.x, box.position.y), box.end, Vector2(box.position.x, box.end.y)])


# Where a sprite or a polygon is drawn, px.
static func _canvas_rect(item: CanvasItem) -> Rect2:
	if item is Sprite2D:
		return item.global_transform * item.get_rect()
	var points: PackedVector2Array = item.global_transform * item.polygon
	var rect := Rect2(points[0], Vector2.ZERO)
	for point in points:
		rect = rect.expand(point)
	return rect


# What a live beam draws over, its glow left out: the placeholder's band, or the drawn start, tile and end.
static func _beam_drawn(beam: Node2D) -> Rect2:
	if not beam.drawn:
		return _canvas_rect(beam.visual.get_node("Band"))
	var rect := _canvas_rect(beam.start_piece)
	for piece in [beam.tile_piece, beam.end_piece]:
		rect = rect.merge(_canvas_rect(piece))
	return rect


static func _same(a: Rect2, b: Rect2) -> bool:
	return a.position.distance_to(b.position) < 0.01 and a.end.distance_to(b.end) < 0.01


#ONE LAYER, WATCHED

# One Wild Cards with the guns on, every step of it watched from its Enter until the layer is home and the fifth clone
# is down. `answer`, if any, is called once as it starts and does whatever the answer is.
static func _run(t, answer := Callable()) -> Dictionary:
	var sm: Node = t.sm
	var wild := _wild(t)
	var guns := _guns(t)
	var rig: Node = sm.hands
	var inside: Rect2 = JoshArtLayout.VIEW_RECT.grow(-Layout.AIR_SIDE_MIN + 0.5)
	var seen := {"frames": 0, "first": [], "phases": {}, "clones": [], "off": [], "hud": [], "z": [], "badge_frames": 0,
		"badge_gaps": [], "stray_badges": [], "bad_tips": [], "layers": [], "under_lanes": [], "bands": [], "drawn": [],
		"live": [], "sweep_out": [], "not_opposite": [], "sweep_span": {}, "posts": [], "held": [], "charges": {},
		"alphas": [], "home": [], "left_over": [], "glow": false}
	var watch := func():
		if sm.current_state != wild:
			return
		seen.frames += 1
		var clock: float = guns.clock
		var phase_name: String = guns.Phase.keys()[guns.phase]
		var hands := {}
		for side in Layout.SIDES:
			var hand: Node2D = rig.hand_of(side)
			if hand != null:
				hands[side] = hand
		if seen.frames == 1:
			for side in hands:
				var hand: Node2D = hands[side]
				seen.first.append([side, hand.mode == JoshHand.Mode.AIR, hand.driven, hand.gun, hand.clip])
		while seen.clones.size() < wild.clones.size():
			seen.clones.append(0.0 if seen.frames == 1 else clock)
		if not seen.phases.has(phase_name):
			seen.phases[phase_name] = clock
			if guns.phase == guns.Phase.SWEEP:
				for side in hands:
					var hand: Node2D = hands[side]
					seen.posts.append([side, hand.floor_at.x + Layout.gun_muzzle(side).x, Layout.gun_posts()[side], hand.gun, hand.clip])
			elif guns.phase == guns.Phase.CHARGE:
				for beam in guns.beams:
					var band: Rect2 = beam.band()
					var want := Layout.gun_band(beam.side, guns.rows[beam.side])
					var rims_ok: bool = beam.tell_rims.size() == 2 and beam.tell_rims[0].points[0].y == band.position.y and beam.tell_rims[1].points[0].y == band.end.y
					seen.bands.append([beam.side, band == want and beam.tell_fill.polygon == _corners(band) and rims_ok])
					seen.glow = seen.glow or beam.glow_piece != null
			elif guns.phase == guns.Phase.FIRE:
				for beam in guns.beams:
					seen.drawn.append([beam.side, beam.drawn, _same(_beam_drawn(beam), beam.band()), _beam_drawn(beam), beam.band()])
			elif guns.phase == guns.Phase.DONE:
				for side in hands:
					var hand: Node2D = hands[side]
					seen.home.append([side, hand.mode == JoshHand.Mode.REST, hand.driven, hand.gun, hand.clip, snappedf(hand.drawn_point().distance_to(Layout.rest_point(side)), 0.01)])
		for side in hands:
			var hand: Node2D = hands[side]
			if hand.mode != JoshHand.Mode.AIR or not hand.driven:
				continue
			if hand.z_index != Layout.HAND_AIR_Z:
				seen.z.append([side, phase_name, hand.z_index])
			var box: Rect2 = hand.drawn_rect()
			if not inside.encloses(box):
				seen.off.append([side, phase_name, snappedf(clock, 0.001), box, hand.clip])
			for k in JoshArtLayout.HUD_KEEP_OUT.size():
				var block: Rect2 = JoshArtLayout.HUD_KEEP_OUT[k].grow(JoshArtLayout.HUD_CLEARANCE)
				if block.intersects(box):
					seen.hud.append([side, phase_name, snappedf(clock, 0.001), k, snappedf(box.intersection(block).size.y, 0.1), hand.clip, hand.frame_index])
		if guns.active and guns.phase == guns.Phase.SWEEP and hands.size() == 2:
			var u := {}
			for side in hands:
				var row: float = hands[side].floor_at.y + Layout.gun_muzzle(side).y
				var span: Vector2 = Layout.gun_row_range(side)
				if row < span.x - 0.5 or row > span.y + 0.5:
					seen.sweep_out.append([side, snappedf(clock, 0.001), row])
				var had: Vector2 = seen.sweep_span.get(side, Vector2(INF, -INF))
				seen.sweep_span[side] = Vector2(minf(had.x, row), maxf(had.y, row))
				u[side] = (row - (span.x + span.y) / 2.0) / ((span.y - span.x) / 2.0)
			if absf(u[&"left"] + u[&"right"]) > 0.01:
				seen.not_opposite.append([snappedf(clock, 0.001), u])
		var stopped_at: float = _due(guns, guns.Phase.CHARGE)
		if guns.active and (guns.phase == guns.Phase.CHARGE or guns.phase == guns.Phase.FIRE) and clock >= stopped_at + sm.gun_glide_time - SLACK:
			for side in hands:
				var muzzle: Vector2 = hands[side].floor_at + Layout.gun_muzzle(side)
				if muzzle.distance_to(Vector2(Layout.gun_posts()[side], guns.rows[side])) > 0.01:
					seen.held.append([side, snappedf(clock, 0.001), muzzle, guns.rows[side]])
		var badge: Node = null
		for tell in t.live_tells():
			if hands.values().has(tell.boss):
				badge = tell
		var charging: bool = guns.active and guns.phase == guns.Phase.CHARGE
		if charging and badge == null:
			seen.badge_gaps.append(snappedf(clock, 0.001))
		elif badge != null and not charging:
			seen.stray_badges.append([phase_name, snappedf(clock, 0.001)])
		if badge != null:
			seen.badge_frames += 1
			if badge.global_position != guns.aim_point or not badge.dodge or badge.boss != hands.get(guns.aimer):
				seen.bad_tips.append([snappedf(clock, 0.001), badge.global_position, guns.aim_point, badge.dodge])
		for beam in guns.beams:
			if not is_instance_valid(beam):
				continue
			if beam.get_parent() != t.boss.sky_layer or not is_instance_valid(beam.tell) or beam.tell.get_parent() != t.boss.floor_layer:
				seen.layers.append([beam.side, snappedf(clock, 0.001)])
			elif beam.tell.visible:
				var after: Array = t.boss.floor_layer.get_children().slice(beam.tell.get_index() + 1).filter(func(n): return not str(n.name).contains("JoshGunTell") and not n.is_queued_for_deletion())
				if not after.is_empty():
					seen.under_lanes.append([beam.side, snappedf(clock, 0.001), after.size()])
		if guns.beams.any(func(beam): return is_instance_valid(beam) and beam.live):
			seen.live.append(clock)
		for side in guns.charges:
			var fx = guns.charges[side].node
			if is_instance_valid(fx):
				var list: Array = seen.charges.get(side, [])
				list.append([fx.scale.x, fx is Sprite2D])
				seen.charges[side] = list
		if guns.freed_at >= 0.0 and not _gun_nodes(t).is_empty():
			seen.left_over.append(snappedf(clock, 0.001))
		seen.alphas.append(t.boss.health_bar.modulate.a)
	t.physics_frame.connect(watch)
	sm.start_cycle()
	if answer.is_valid():
		await answer.call()
	await t.wait_until(func(): return sm.current_state != wild or (guns.phase == guns.Phase.DONE and wild.clones.size() >= sm.wild_clones), 480)
	await t.wait(2)
	t.physics_frame.disconnect(watch)
	return seen


#THE LAYER

static func _layer(t) -> void:
	var sm: Node = t.sm
	var guns := _guns(t)
	var spans := {}
	for side in Layout.SIDES:
		spans[side] = Layout.gun_row_range(side)
	var runs := [
		["the player standing mid-floor", {}],
		["the right hand at the bottom of its rows, the left at the top", {aimer = &"right", rows = {&"right": spans[&"right"].y, &"left": spans[&"left"].x}}],
		["the left hand at the bottom of its rows, the right at the top", {aimer = &"left", rows = {&"left": spans[&"left"].y, &"right": spans[&"right"].x}}],
	]
	var sweep_at: float = sm.gun_out_time
	var stop_at: float = sweep_at + sm.gun_sweep_time
	var fire_at: float = stop_at + sm.gun_charge_time
	var fade_at: float = fire_at + sm.gun_beam_live
	var freed_at: float = fade_at + sm.gun_beam_fade
	var home_at: float = fade_at + sm.gun_back_time
	var fifth_at: float = freed_at + sm.gun_clear_gap
	var wants := {"SWEEP": sweep_at, "CHARGE": stop_at, "FIRE": fire_at, "FADE": fade_at, "BACK": freed_at, "DONE": home_at}
	t.log_p("the guns' beats: %s; the fifth clone at %.2f s" % [wants, fifth_at])
	for run in runs:
		var label: String = run[0]
		await _reset(t, STILL)
		t.hold_break_gauge(t.boss)
		guns.forced_rows = run[1]
		t.log_p("-- one Wild Cards with its Gun Hands, %s" % label)
		var seen := await _run(t)
		var back: bool = await t.wait_until(func(): return is_equal_approx(t.boss.health_bar.modulate.a, 1.0), 60)
		var off_beat: Array = wants.keys().filter(func(key): return not seen.phases.has(key) or not _on_beat(seen.phases[key], wants[key]))
		var lowest: float = seen.alphas.min() if not seen.alphas.is_empty() else -1.0
		var crosses: bool = guns.rows.values().any(func(row): return Layout.gun_band(&"left", row).intersects(JoshArtLayout.HUD_KEEP_OUT[0].grow(JoshArtLayout.HUD_CLEARANCE)))
		t.log_p("%s: lead %.2f; first %s; phases %s; posts %s; sweep spans %s; rows %s aimed by %s, tip %s; fired %.3f, live %d frames from %.3f, freed %.3f; home %s; clones at %s; badge %d frames; bars down to %.2f" % [
			label, guns.lead, seen.first, seen.phases, seen.posts, seen.sweep_span, guns.rows, guns.aimer, guns.aim_point,
			guns.fired_at, seen.live.size(), seen.live[0] if not seen.live.is_empty() else -1.0, guns.freed_at, seen.home,
			seen.clones, seen.badge_frames, lowest])
		t.log_p("%s: off screen %s; over the HUD %s; charge scales %s; beams drawn %s" % [label, seen.off.slice(0, LOGGED),
			seen.hud.slice(0, LOGGED), seen.charges.values().map(func(list): return list.map(func(s): return snappedf(s[0], 0.001))), seen.drawn])
		t.check(guns.lead == 0.0 and seen.first.size() == 2 and seen.first.all(func(f): return f[1] and f[2] and f[3] and f[4] == &"gun_form"), "%s: the hands leave REST at Enter, turning into guns (%s)" % [label, seen.first])
		t.check(seen.posts.size() == 2 and seen.posts.all(func(p): return absf(p[1] - p[2]) < 0.5 and p[3] and p[4] == &"gun_idle"), "%s: guns at their posts by %.2f s (%s)" % [label, sweep_at, seen.posts])
		t.check(off_beat.is_empty(), "%s: each beat on its frame, the stop at %.2f s (%s)" % [label, stop_at, off_beat])
		t.check(seen.sweep_out.is_empty() and seen.not_opposite.is_empty(), "%s: the sweep inside each hand's rows, the two always going opposite ways (%s, %s)" % [label, seen.sweep_out.slice(0, LOGGED), seen.not_opposite.slice(0, LOGGED)])
		t.check(seen.held.is_empty(), "%s: after the glide each muzzle holds its post and its row (%s)" % [label, seen.held.slice(0, LOGGED)])
		t.check(_on_beat(guns.fired_at, fire_at) and seen.live.size() == roundi(sm.gun_beam_live / FRAME) and not seen.live.is_empty() and _on_beat(seen.live[0], fire_at), "%s: both fire at %.2f s to the frame and are live for %.2f s (%d frames)" % [label, fire_at, sm.gun_beam_live, seen.live.size()])
		t.check(_on_beat(guns.freed_at, freed_at) and seen.left_over.is_empty(), "%s: the beams and their telegraphs gone at %.2f s, and nothing of them after (%s)" % [label, freed_at, seen.left_over.slice(0, LOGGED)])
		t.check(seen.home.size() == 2 and seen.home.all(func(h): return h[1] and not h[2] and not h[3] and h[4] == &"hover" and h[5] <= 0.5), "%s: home at %.2f s and a frame, resting at their portals, hands again, the rig's (%s)" % [label, home_at, seen.home])
		var hops_ok: bool = seen.clones.size() == sm.wild_clones and seen.clones[0] == 0.0
		for k in range(1, mini(seen.clones.size(), 4)):
			hops_ok = hops_ok and _on_beat(seen.clones[k], k * sm.wild_hop_time)
		t.check(hops_ok and _on_beat(seen.clones[-1], fifth_at), "%s: the clones at 0, 0.7, 1.4 and 2.1 s, and the fifth held to the first step at or after %.2f s (%s)" % [label, fifth_at, seen.clones])
		t.check(seen.badge_frames > 0 and seen.badge_gaps.is_empty() and seen.stray_badges.is_empty(), "%s: the yellow badge from the stop to the fire, and never otherwise (%s, %s)" % [label, seen.badge_gaps.slice(0, LOGGED), seen.stray_badges.slice(0, LOGGED)])
		t.check(seen.bad_tips.is_empty(), "%s: on the aiming hand, its tip on the aimed band's top edge over the player (%s)" % [label, seen.bad_tips.slice(0, LOGGED)])
		t.check(seen.off.is_empty(), "%s: every frame every hand in the air keeps its box %.0f px inside the view, the flights too (%s)" % [label, Layout.AIR_SIDE_MIN, seen.off.slice(0, LOGGED)])
		t.check(seen.hud.is_empty(), "%s: and clear of every HUD keep-out (%s)" % [label, seen.hud.slice(0, LOGGED)])
		t.check(seen.z.is_empty() and seen.layers.is_empty() and seen.under_lanes.is_empty(), "%s: hands at z %d, each telegraph on the FloorLayer over the lanes, each beam on the SkyLayer (%s, %s, %s)" % [label, Layout.HAND_AIR_Z, seen.z.slice(0, LOGGED), seen.layers.slice(0, LOGGED), seen.under_lanes.slice(0, LOGGED)])
		t.check(seen.bands.size() == 2 and seen.bands.all(func(b): return b[1]), "%s: each telegraph is exactly its band, JoshHandsLayout.gun_band (%s)" % [label, seen.bands])
		t.check(seen.drawn.size() == 2 and seen.drawn.all(func(d): return d[2]) and not seen.glow, "%s: each live beam drawn over exactly its band, with no glow (%s)" % [label, seen.drawn])
		var steps: Array = Layout.GUN_CHARGE_SCALES
		var grown: bool = seen.charges.size() == 2
		for list in seen.charges.values():
			var sheet: bool = list[0][1]
			var scales: Array = list.map(func(s): return s[0] * (1.0 if sheet else Layout.SCALE))
			var whole: bool = scales.all(func(s): return absf(s - roundf(s)) < 0.0001 and steps.has(roundi(s)))
			var rising := true
			for k in range(1, scales.size()):
				rising = rising and scales[k] >= scales[k - 1]
			grown = grown and whole and rising and roundi(scales[0]) == steps[0] and roundi(scales[-1]) == steps[-1]
		t.check(grown, "%s: the charge effect grows through the whole-number scales %s over the charge" % [label, steps])
		if crosses:
			t.check(is_equal_approx(lowest, t.boss.HUD_FADE_ALPHA) and back, "%s: a band over the bars fades them to %.1f, and they come back (%.3f)" % [label, t.boss.HUD_FADE_ALPHA, lowest])
		else:
			t.check(is_equal_approx(lowest, 1.0), "%s: with no band over the bars they never fade (%.3f)" % [label, lowest])


#THE ROWS

static func _rows(t) -> void:
	var guns := _guns(t)
	var offset: float = t.sm.gun_row_offset
	var gap := Layout.gun_row_gap()
	var hurt := _hurt_offset(t)
	var area: Rect2 = BossBroken.PLAYER_AREA
	var low: Vector2 = area.position + hurt.get_center()
	var high: Vector2 = area.end + hurt.get_center()
	var centres: Array[Vector2] = []
	for i in GRID.x:
		for j in GRID.y:
			centres.append(Vector2(lerpf(low.x, high.x, (i + 0.5) / GRID.x), lerpf(low.y, high.y, (j + 0.5) / GRID.y)))
	for corner in [low, Vector2(high.x, low.y), Vector2(low.x, high.y), high]:
		centres.append(corner)
	for k in STRIP_POINTS:
		var s := (k + 0.5) / STRIP_POINTS
		centres.append(Vector2(lerpf(low.x, high.x, s), low.y))
		centres.append(Vector2(lerpf(low.x, high.x, s), high.y))
		centres.append(Vector2(low.x, lerpf(low.y, high.y, s)))
		centres.append(Vector2(high.x, lerpf(low.y, high.y, s)))
	var wrong_aimer: Array = []
	var wrong_aimed: Array = []
	var wrong_cut: Array = []
	var too_close: Array = []
	var no_way_out: Array = []
	var missed: Array = []
	var corner: Array = []
	var farthest := 0.0
	var closest := INF
	for centre in centres:
		var pick: Dictionary = guns.choose_rows(centre, offset)
		var far: StringName = &"right" if centre.x < Layout.GUN_RING_MID_X else &"left"
		var aimer: StringName = &"right" if far == &"left" and centre.y > Layout.gun_left_reach() else far
		var other := Layout.other_side(aimer)
		if pick.aimer != aimer:
			wrong_aimer.append([centre, pick.aimer])
			continue
		var aim_span := Layout.gun_row_range(aimer)
		var cut_span := Layout.gun_row_range(other)
		var aimed: float = pick.rows[aimer]
		var cut: float = pick.rows[other]
		if aimed != roundf(clampf(centre.y, aim_span.x, aim_span.y)):
			wrong_aimed.append([centre, aimed])
		var floor_span: Vector2 = Layout.GUN_FLOOR
		var way := -1.0 if aimed - floor_span.x > floor_span.y - aimed else 1.0
		var toward := roundf(clampf(aimed + way * offset, cut_span.x, cut_span.y))
		var want_cut := toward if absf(toward - aimed) >= gap else roundf(clampf(aimed - way * offset, cut_span.x, cut_span.y))
		if absf(cut - want_cut) > 0.001:
			wrong_cut.append([centre, cut, want_cut])
		closest = minf(closest, absf(cut - aimed))
		if absf(cut - aimed) < gap - 0.001:
			too_close.append([centre, aimed, cut])
		var bands: Array[Rect2] = [Layout.gun_band(aimer, aimed), Layout.gun_band(other, cut)]
		var body: Vector2 = centre - hurt.get_center()
		var box := Rect2(body + hurt.position, hurt.size)
		if not bands[0].intersects(box):
			if aimer == &"right" and box.position.x >= bands[0].end.x:
				corner.append(centre.round())
			else:
				missed.append([centre, aimer, aimed])
		var out := _band_free(body, hurt, bands, area)
		if out == INF:
			no_way_out.append(centre)
		else:
			farthest = maxf(farthest, out)
	t.log_p("%d player centres over %s: the rows at least %.0f px apart (closest %.0f); the farthest walk to a band-free spot %.0f px (%.2f s at %.0f px/s); the aimed band misses them only behind the right muzzle, at %s" % [
		centres.size(), Rect2(low, high - low), gap, closest, farthest, farthest / t.player.SPEED, t.player.SPEED, corner])
	t.check(wrong_aimer.is_empty(), "the far hand aims, the right below the left's reach (y %.1f) (%s)" % [Layout.gun_left_reach(), wrong_aimer.slice(0, LOGGED)])
	t.check(wrong_aimed.is_empty(), "at the player's row, clamped to its range (%s)" % [wrong_aimed.slice(0, LOGGED)])
	t.check(wrong_cut.is_empty(), "the other row %.0f px toward more floor, clamped, or the other way when that leaves no room (%s)" % [offset, wrong_cut.slice(0, LOGGED)])
	t.check(too_close.is_empty(), "the two rows at least a band and a hurtbox apart, %.0f px (%s)" % [gap, too_close.slice(0, LOGGED)])
	t.check(no_way_out.is_empty(), "from every centre a band-free spot within %.0f px of walking (%s)" % [WALK_REACH, no_way_out.slice(0, LOGGED)])
	t.check(missed.is_empty(), "the aimed band holds the player everywhere but the corner behind the right muzzle (%s)" % [missed.slice(0, LOGGED)])


# How far, walking both ways at once, the nearest body position on the floor is whose hurtbox touches no band: INF
# if none is within WALK_REACH.
static func _band_free(from: Vector2, hurt: Rect2, bands: Array[Rect2], area: Rect2) -> float:
	var start := from.clamp(area.position, area.end)
	for r in int(ceilf(WALK_REACH / SEARCH_STEP)) + 1:
		for cell in _ring(r):
			var at: Vector2 = start + cell * SEARCH_STEP
			if not area.has_point(at):
				continue
			var box := Rect2(at + hurt.position, hurt.size)
			if bands.all(func(band: Rect2) -> bool: return not band.intersects(box)):
				return r * SEARCH_STEP
	return INF


static func _ring(r: int) -> Array[Vector2]:
	var cells: Array[Vector2] = []
	if r == 0:
		cells.append(Vector2.ZERO)
		return cells
	for i in range(-r, r + 1):
		cells.append(Vector2(i, -r))
		cells.append(Vector2(i, r))
	for j in range(-r + 1, r):
		cells.append(Vector2(-r, j))
		cells.append(Vector2(r, j))
	return cells


#THE ANSWERS

static func _answered(t, answer: String) -> void:
	var guns := _guns(t)
	var gauge: Node = t.boss.break_gauge
	await _reset(t, STILL)
	gauge.value = GAUGE_START if answer == "hit" else 0.0
	var gauge_from: float = gauge.value
	var health: int = t.player.playerHealth
	var hits: Array = []
	var on_hit := func(hit: RefCounted) -> void:
		if hit.attack_id == BEAM_ID:
			hits.append(snappedf(guns.clock, 0.001))
	var dodges: Array = []
	var on_dodge := func(hit: RefCounted) -> void:
		dodges.append({"id": hit.attack_id, "stamina": t.defense.stamina})
	t.defense.hit_taken.connect(on_hit)
	t.defense.perfect_dodged.connect(on_dodge)
	var at_fire := {"hurt": Rect2(), "in_aimed": false, "clear": false, "before": -1.0}
	var respond := func() -> void:
		match answer:
			"walk":
				await t.wait_until(func(): return guns.phase == guns.Phase.CHARGE and guns.clock >= _due(guns, guns.Phase.CHARGE) + WALK_AFTER - SLACK, 400)
				var way := _away_key(guns)
				t.press(way)
				var until: float = t.defense.clock + WALK_TIME
				await t.wait_until(func(): return t.defense.clock >= until - SLACK, 60)
				t.release(way)
			"dash":
				await t.wait_until(func(): return guns.phase == guns.Phase.CHARGE and guns.clock >= _due(guns, guns.Phase.FIRE) - DASH_LEAD - SLACK, 400)
				t.defense._set_stamina(t.defense.max_stamina)
				at_fire.before = t.defense.stamina
				var way := _away_key(guns)
				t.press(way)
				t.tap(KEY_W)
				await t.wait_until(func(): return guns.fired_at >= 0.0, 30)
				await t.wait_until(func(): return not t.player.is_dodging, 30)
				t.release(way)
		await t.wait_until(func(): return guns.fired_at >= 0.0, 400)
		if at_fire.hurt == Rect2():
			var hurt := _hurt(t)
			at_fire.hurt = hurt
			at_fire.in_aimed = guns.beams.any(func(beam): return beam.side == guns.aimer and beam.band().intersects(hurt))
			at_fire.clear = guns.beams.all(func(beam): return not beam.band().intersects(hurt))
	t.log_p("-- the guns, answered: %s" % answer)
	var seen := await _run(t, respond)
	t.defense.hit_taken.disconnect(on_hit)
	t.defense.perfect_dodged.disconnect(on_dodge)
	var names := _names(guns)
	t.log_p("%s: rows %s aimed by %s; at the fire the hurtbox %s, in the aimed band %s; results %s; beam hits at %s; perfect dodges %s; health %d -> %d; gauge %.2f -> %.2f; fired %.3f" % [
		answer, guns.rows, guns.aimer, at_fire.hurt, at_fire.in_aimed, names, hits, dodges, health, t.player.playerHealth,
		gauge_from, gauge.value, guns.fired_at])
	t.check(_on_beat(guns.fired_at, _due(guns, guns.Phase.FIRE)) and seen.phases.has("DONE"), "the layer ran through, firing on its beat")
	match answer:
		"hit":
			t.check(at_fire.in_aimed, "the player stands in the aimed row as it fires")
			t.check(names == ["HIT"] and hits.size() == 1, "exactly one HIT (%s, %s)" % [names, hits])
			var damage: int = AttackCatalog.get_attack(BEAM_ID).damage
			t.check(health - t.player.playerHealth == damage, "its damage, %d half-hearts (%d)" % [damage, health - t.player.playerHealth])
			t.check(is_equal_approx(gauge_from - gauge.value, gauge.hit_loss), "and one read off his gauge (%.2f -> %.2f)" % [gauge_from, gauge.value])
		"walk":
			t.check(at_fire.clear, "stepped out, the hurtbox is clear of both bands as they fire (%s)" % at_fire.hurt)
			t.check(hits.is_empty() and names.is_empty() and t.player.playerHealth == health, "no hit (%s)" % [names])
		"dash":
			var answered: bool = not names.is_empty() and names.all(func(n): return n == "DODGED" or n == "NEAR_MISS")
			t.check(hits.is_empty() and answered and t.player.playerHealth == health, "DODGED or a near miss through the dash's ghost, unhurt (%s)" % [names])
			t.check(dodges.size() == 1 and dodges[0].id == BEAM_ID, "one perfect dodge (%s)" % [dodges])
			t.check(dodges.size() == 1 and absf(dodges[0].stamina - at_fire.before) < 0.5, "giving the dash back (%.2f before the dash)" % at_fire.before)
			t.check(is_equal_approx(gauge.value, gauge.perfect_dodge_gain), "and one read on his gauge (%.3f)" % gauge.value)


#THE EDGES

static func _edges(t) -> void:
	var guns := _guns(t)
	var band: Rect2 = Layout.gun_band(EDGE_ROWS.aimer, EDGE_ROWS.rows[EDGE_ROWS.aimer])
	var got := {}
	for place in [["top", "inside"], ["bottom", "inside"], ["top", "outside"], ["bottom", "outside"]]:
		await _reset(t, STILL)
		t.hold_break_gauge(t.boss)
		guns.forced_rows = EDGE_ROWS
		var put := {"hurt": Rect2()}
		var respond := func() -> void:
			await t.wait_until(func(): return guns.phase == guns.Phase.CHARGE and guns.clock >= _due(guns, guns.Phase.CHARGE) + t.sm.gun_glide_time + 0.1, 400)
			var hurt := _hurt(t)
			var reach: float = 1.0 if place[1] == "inside" else -1.0
			var move: float = (band.position.y + reach - hurt.end.y) if place[0] == "top" else (band.end.y - reach - hurt.position.y)
			t.player.global_position.y += move
			t.player.velocity = Vector2.ZERO
			t.clear_iframes()
			await t.wait_until(func(): return guns.fired_at >= 0.0, 120)
			put.hurt = _hurt(t)
		t.log_p("-- the hurtbox a pixel %s the aimed band's %s edge" % [place[1], place[0]])
		await _run(t, respond)
		var names := _names(guns)
		got["%s %s" % place] = names
		t.log_p("%s %s: the band %s, the hurtbox %s; results %s" % [place[0], place[1], band, put.hurt, names])
	t.check(got.get("top inside") == ["HIT"] and got.get("bottom inside") == ["HIT"], "a pixel inside its top edge, and its bottom edge, is hit (%s, %s)" % [got.get("top inside"), got.get("bottom inside")])
	t.check(got.get("top outside") == [] and got.get("bottom outside") == [], "a pixel outside either isn't (%s, %s)" % [got.get("top outside"), got.get("bottom outside")])


#THE WAY OUT OF THE CARDS

static func _escape(t) -> void:
	var sm: Node = t.sm
	var wild := _wild(t)
	var guns := _guns(t)
	var seen := {"fired": 0, "was_fired": false, "fifths": 0, "at_fifth": [], "in_volley": [], "clones": 0}
	var watch := func():
		if sm.current_state != wild:
			seen.clones = 0
			seen.was_fired = false
			return
		var fired: bool = guns.fired_at >= 0.0
		if fired and not seen.was_fired:
			seen.fired += 1
		seen.was_fired = fired
		var left: Array = _gun_nodes(t)
		if wild.clones.size() >= sm.wild_clones and seen.clones < sm.wild_clones:
			seen.fifths += 1
			if not left.is_empty():
				seen.at_fifth.append(left.map(func(n): return n.name))
		seen.clones = wild.clones.size()
		if (wild.beat == wild.Beat.WARN or wild.beat == wild.Beat.VOLLEY) and not left.is_empty():
			seen.in_volley.append([wild.Beat.keys()[wild.beat], left.map(func(n): return n.name)])
	t.physics_frame.connect(watch)
	t.log_p("-- josh_wild_cards' setups, with the Gun Hands on")
	await WildCardsTest.setups(t, wild, true)
	t.physics_frame.disconnect(watch)
	t.log_p("the guns fired in %d of %d setups; the fifth hop came %d times; left at it %s; in the warning or the volley %s" % [seen.fired, WildCardsTest.SETUPS, seen.fifths, seen.at_fifth, seen.in_volley.slice(0, LOGGED)])
	t.check(seen.fired == WildCardsTest.SETUPS, "the guns fired once in every setup (%d)" % seen.fired)
	t.check(seen.fifths == WildCardsTest.SETUPS and seen.at_fifth.is_empty(), "at every fifth hop no beam or telegraph of the guns is left (%s)" % [seen.at_fifth])
	t.check(seen.in_volley.is_empty(), "nor on any step of the warning or the volley (%s)" % [seen.in_volley.slice(0, LOGGED)])


#HIS BREAK

static func _break(t) -> void:
	var guns := _guns(t)
	var rig: Node = t.sm.hands
	var moments := {
		"in the sweep": func(): return guns.active and guns.phase == guns.Phase.SWEEP and guns.clock >= 1.0,
		"in the charge": func(): return guns.active and guns.phase == guns.Phase.CHARGE and guns.clock >= _due(guns, guns.Phase.CHARGE) + 0.5,
		"with the beams live": func(): return guns.active and guns.phase == guns.Phase.FIRE,
	}
	for moment in moments:
		await _reset(t, STILL)
		t.sm.start_cycle()
		var reached: bool = await t.wait_until(moments[moment], 400)
		var had: Array = [_gun_nodes(t).size(), t.live_tells().size()]
		await t.force_break()
		var broke: bool = await t.wait_until(func(): return str(t.sm.current_state.name) == "Broken", 30)
		await t.wait(2)
		var left: Array = t.live_hazards()
		var tells: Array = t.live_tells()
		var running: Array = t.break_timers().filter(func(timer): return not timer.is_stopped())
		var let_go: bool = not guns.active and guns.beams.is_empty() and Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and not hand.gun and not hand.driven)
		var gone: bool = await t.wait_until(func(): return Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and hand.retracted and not hand.visible), 60)
		var looping: bool = Layout.SIDES.all(func(side): return rig.portal_of(side) != null and rig.portal_of(side).sequence == &"loop")
		t.log_p("%s: reached %s with %d gun nodes and %d badges; now %s; hazards %s, tells %d, timers %s; hands %s" % [moment, reached, had[0], had[1], t.sm.current_state.name, left.map(func(h): return h.name), tells.size(), running.map(func(timer): return timer.name), Layout.SIDES.map(func(side): return [rig.hand_of(side).mode, rig.hand_of(side).retracted, rig.hand_of(side).visible])])
		t.check(reached and broke, "%s: Broken" % moment)
		t.check(left.is_empty() and tells.is_empty() and running.is_empty(), "%s: no beam, telegraph, badge or Timer left" % moment)
		t.check(let_go, "%s: the layer let go, the hands hands again" % moment)
		t.check(gone and looping, "%s: both hands gone into their portals, which stay open" % moment)
		await t.wait_until(func(): return not t.player.is_action_locked, 120)

	t.log_p("-- the next cycle forms them again, and the guns wait for it")
	var wild := _wild(t)
	var seen := {"formed": {}, "left_rest": -1.0}
	var watch := func():
		if t.sm.current_state != wild:
			return
		for side in Layout.SIDES:
			var hand: Node2D = rig.hand_of(side)
			if hand == null:
				continue
			if hand.mode == JoshHand.Mode.REST and hand.clip == &"form":
				seen.formed[side] = true
			if hand.mode == JoshHand.Mode.AIR and seen.left_rest < 0.0:
				seen.left_rest = guns.clock
	t.physics_frame.connect(watch)
	t.stop_boss_timers()
	t.sm.start_cycle()
	await t.wait_until(func(): return t.sm.current_state != wild or guns.phase == guns.Phase.SWEEP, 300)
	t.physics_frame.disconnect(watch)
	t.log_p("formed %s; lead %.2f s; left their portals at %.3f s" % [seen.formed, guns.lead, seen.left_rest])
	t.check(seen.formed.size() == 2 and guns.lead > 0.0, "the next start_cycle() forms them at their portals, and the guns wait for it (%.2f s)" % guns.lead)
	t.check(seen.left_rest >= guns.lead - SLACK, "they leave their portals only once formed (%.3f s)" % seen.left_rest)


#LETTING GO

static func _release(t) -> void:
	var guns := _guns(t)
	var rig: Node = t.sm.hands

	t.log_p("-- paused mid-charge for 60 frames")
	await _reset(t, STILL)
	t.hold_break_gauge(t.boss)
	t.sm.start_cycle()
	await t.wait_until(func(): return guns.active and guns.phase == guns.Phase.CHARGE and guns.clock >= _due(guns, guns.Phase.CHARGE) + 0.4, 400)
	var pause: Node = t.pause_menu()
	await t.tap_pause()
	var still := func() -> Dictionary:
		var badge: Array = t.live_tells().filter(func(tell): return Layout.SIDES.any(func(side): return tell.boss == rig.hand_of(side))).map(func(tell): return [tell.global_position, tell.clock, tell.modulate])
		return {"clock": guns.clock,
			"hands": Layout.SIDES.map(func(side): var hand: Node2D = rig.hand_of(side); return [hand.global_position, hand.drawn_point(), hand.frame_index, hand.into, hand.elapsed]),
			"tells": guns.beams.map(func(beam): return [beam.tell_fill.color, beam.tell_rims[0].default_color]),
			"charges": guns.charges.keys().map(func(side): return [guns.charges[side].node.scale, guns.charges[side].node.get("frame")]),
			"badge": badge}
	var at_pause: Dictionary = still.call()
	await t.wait(60)
	var after: Dictionary = still.call()
	var whole: bool = at_pause.tells.size() == 2 and at_pause.charges.size() == 2 and at_pause.badge.size() == 1
	if str(at_pause) != str(after) or not whole:
		t.log_p("at the pause %s; 60 frames on %s" % [at_pause, after])
	t.check(pause.is_open() and t.paused and whole and str(at_pause) == str(after), "paused, nothing of it moves for 60 frames: no clock, hand, telegraph, charge or badge")
	await t.tap_pause()
	await t.wait_until(func(): return guns.fired_at >= 0.0, 120)
	var fire := _due(guns, guns.Phase.FIRE)
	t.log_p("paused in the charge; the fire, due at %.2f s, came at %.3f s" % [fire, guns.fired_at])
	t.check(guns.lead == 0.0 and _on_beat(guns.fired_at, fire), "and after the resume the fire keeps its time")

	t.log_p("-- the player beaten mid-charge")
	await _reset(t, STILL)
	t.sm.start_cycle()
	await t.wait_until(func(): return guns.active and guns.phase == guns.Phase.CHARGE and guns.clock >= _due(guns, guns.Phase.CHARGE) + 0.3, 400)
	t.boss.on_player_defeated()
	var home: bool = await t.wait_until(func(): return Layout.SIDES.all(func(side): var hand: Node2D = rig.hand_of(side); return hand != null and hand.mode == JoshHand.Mode.REST and hand.visible and hand.clip == &"hover" and not hand.gun and hand.drawn_point().distance_to(Layout.rest_point(side)) <= 0.5), 90)
	t.log_p("state %s; hands %s; hazards %s; tells %d" % [t.sm.current_state.name, Layout.SIDES.map(func(side): return [rig.hand_of(side).mode, rig.hand_of(side).clip, rig.hand_of(side).gun]), t.live_hazards().map(func(h): return h.name), t.live_tells().size()])
	t.check(home and not guns.active and t.live_hazards().is_empty() and t.live_tells().is_empty(), "the hands fly home and hover, hands again, and nothing of the layer is left")

	t.log_p("-- the scene reloaded with the beams live")
	await t.load_gauged()
	guns = _guns(t)
	await _reset(t, STILL)
	t.sm.start_cycle()
	await t.wait_until(func(): return guns.active and guns.phase == guns.Phase.FIRE, 400)
	var old_scene: Node = t.current_scene
	var reloaded: bool = await t.load_gauged()
	await t.wait(10)
	t.check(reloaded and not is_instance_valid(old_scene) and t.current_scene != old_scene, "reloaded with the beams live (its script errors are the runner's to count)")

	t.log_p("-- him beaten mid-sweep")
	guns = _guns(t)
	rig = t.sm.hands
	await _reset(t, STILL)
	t.sm.start_cycle()
	await t.wait_until(func(): return guns.active and guns.phase == guns.Phase.SWEEP and guns.clock >= 1.0, 400)
	var nodes: Array = []
	for side in Layout.SIDES:
		nodes.append(rig.portal_of(side))
		nodes.append(rig.hand_of(side))
	t.sm.enter_defeated()
	var shattered: bool = Layout.SIDES.all(func(side): var hand = rig.hands.get(side); return not is_instance_valid(hand) or hand.clip == &"shatter")
	var closing: bool = Layout.SIDES.all(func(side): var portal = rig.portals.get(side); return is_instance_valid(portal) and portal.sequence == &"close")
	var freed: bool = await t.wait_until(func(): return nodes.all(func(n): return not is_instance_valid(n)), 60)
	t.log_p("state %s; shattered %s, closing %s, all four freed within a second %s; the layer active %s, gun nodes %d" % [t.sm.current_state.name, shattered, closing, freed, guns.active, _gun_nodes(t).size()])
	t.check(shattered and closing, "the hands shatter and the portals close")
	t.check(freed and rig.collapsed and not guns.active and _gun_nodes(t).is_empty(), "all four are gone within a second, nothing of the layer is left, and nothing forms again")


#THE ART

# The gun art as shipped, read off disk, whether or not it is imported yet: the game plays it once it is.
static func _art(t) -> void:
	var image := func(path: String) -> Image:
		return Image.load_from_file(ProjectSettings.globalize_path(path))
	var on_disk := func(path: String) -> bool:
		return FileAccess.file_exists(path)
	var waiting: Array = []
	var note := func(path: String) -> void:
		if not ResourceLoader.exists(path):
			waiting.append(path.get_file())
	t.log_p("-- the gun art, as shipped")
	var hand_frame: Vector2 = Layout.HAND.frame
	if not Layout.GUN_CLIPS.keys().all(func(clip): return on_disk.call(Layout.hand_sheet(clip))):
		t.log_p("the gun hands: not shipped, the approved hand clips stand in, turned")
	else:
		var bad: Array = []
		for clip in Layout.GUN_CLIPS:
			for path in [Layout.hand_sheet(clip), Layout.hand_glow_sheet(clip)]:
				if not on_disk.call(path):
					continue
				note.call(path)
				var img: Image = image.call(path)
				var frames: int = Layout.GUN_CLIPS[clip].times.size()
				if img.get_width() != frames * int(hand_frame.x) or img.get_height() != int(hand_frame.y):
					bad.append([path.get_file(), img.get_size(), frames])
		t.check(bad.is_empty(), "every gun clip and its glow %s frames, as many as JoshHandsLayout.GUN_CLIPS has (%s)" % [hand_frame, bad])
		var form_glow_path := Layout.hand_glow_sheet(&"gun_form")
		var form: Image = image.call(Layout.hand_sheet(&"gun_form"))
		var form_glow: Image = image.call(form_glow_path) if on_disk.call(form_glow_path) else null
		var boxes: Array[Rect2] = Layout.GUN_FORM_BOXES_TEXELS
		var form_frames: int = Layout.GUN_CLIPS[&"gun_form"].times.size()
		var drifted: Array = []
		for f in form_frames:
			var measured := _drawn_box(form, form_glow, f)
			if f >= boxes.size() or measured != boxes[f]:
				drifted.append([f, measured, boxes[f] if f < boxes.size() else null])
		t.check(boxes.size() == form_frames and drifted.is_empty(), "gun_form's box on each of its frames, glow included, is JoshHandsLayout.GUN_FORM_BOXES_TEXELS (%s)" % [drifted])
	var beam: Dictionary = Layout.GUN_BEAM
	if not [beam.start, beam.tile, beam.end].all(func(path): return on_disk.call(path)):
		t.log_p("the beam: not shipped, the placeholder band stands in")
	else:
		var bad: Array = []
		for path in [beam.start, beam.tile, beam.end]:
			note.call(path)
			var img: Image = image.call(path)
			if img.get_width() != int(beam.frames) * int(beam.frame.x) or img.get_height() != int(beam.frame.y):
				bad.append([path.get_file(), img.get_size()])
		t.check(bad.is_empty() and is_equal_approx(beam.frame.y * Layout.SCALE, 2.0 * Layout.BEAM_HALF), "the beam's start, tile and end: %d frames of %s, %d texels tall, the hit band (%s)" % [beam.frames, beam.frame, int(beam.frame.y), bad])
	if on_disk.call(beam.glow):
		note.call(beam.glow)
		var img: Image = image.call(beam.glow)
		t.check(img.get_height() == int(beam.glow_frame.y) and img.get_width() % int(beam.glow_frame.x) == 0, "the beam's glow: frames of %s (%s)" % [beam.glow_frame, img.get_size()])
	else:
		t.log_p("the beam's glow: not shipped (the user's pick), and nothing draws it")
	for spec in [{"name": "flash", "texture": Layout.GUN_FLASH.texture, "frames": Layout.GUN_FLASH.frame_times.size(), "frame": Layout.GUN_FLASH.frame},
			{"name": "charge effect", "texture": Layout.GUN_CHARGE_FX.texture, "frames": Layout.GUN_CHARGE_FX.frames, "frame": Layout.GUN_CHARGE_FX.frame}]:
		if not on_disk.call(spec.texture):
			t.log_p("the %s: not shipped, its placeholder stands in" % spec.name)
			continue
		note.call(spec.texture)
		var img: Image = image.call(spec.texture)
		t.check(img.get_width() == spec.frames * int(spec.frame.x) and img.get_height() == int(spec.frame.y), "the %s: %d frames of %s (%s)" % [spec.name, spec.frames, spec.frame, img.get_size()])
	if waiting.is_empty():
		t.log_p("all of it imported: final_gun %s, final_beam %s" % [Layout.final_gun(), Layout.final_beam()])
	else:
		t.log_p("shipped but not imported yet, so the game plays the placeholders until the editor imports them: %s" % [waiting])


# What frame `frame` of a hand sheet draws, with its glow sheet's if there is one, texels round the pivot.
static func _drawn_box(sheet: Image, glow: Image, frame: int) -> Rect2:
	var size := Vector2i(Layout.HAND.frame)
	var cell := Rect2i(Vector2i(frame * size.x, 0), size)
	var used := Rect2(sheet.get_region(cell).get_used_rect())
	if glow != null:
		var lit := Rect2(glow.get_region(cell).get_used_rect())
		if lit.has_area():
			used = used.merge(lit) if used.has_area() else lit
	return Rect2(used.position - Layout.HAND.pivot, used.size)
