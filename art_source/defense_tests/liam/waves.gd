extends RefCounted

# liam_waves: attack 1, his tsunami (LiamTsunami, LiamWave), on his test scene.
#   bands     a whole Tsunami with the player out of it: wave_count() waves (12), sides alternating from the player's half,
#             each band exactly its half (x 105..966 or 954..1815, 360 tall, 12 px of overlap at the seam), wave_gap
#             (120 +-1 px) between one wave's top and the next one's front on every frame, each coming out of the row's
#             foot 0.39 s (the rope-to-face fall) after its swell ends, the flood up 1 / flood_waves on the frame each
#             front crashes on the bottom rope, full by the flood_waves-th; run out, his wind blows the player to
#             RESET_SPOT (+-1), unhurt, and then Tremors
#   tell      each wave's swell showing until its front crosses the top rope, and the red badge on its half's anchor;
#             the pillar still shielded through the first one (it opens on the gate wave's crash: liam_tsunami_gate)
#   dash      a dash straight up into a wave is hit (liam_tsunami's damage), whenever it is timed, with its 0.21 s dash
#             immunity
#   corner    a diagonal dash through the seam's corner is DODGED, a perfect dodge, and the dash's stamina comes back
#   inset     a player standing 17 px inside a wave's seam end is not hit (it hurts 18 px short of it); at 19 px they are
#   parry     a parry is PARRIED and the wave rolls on through the player without a second hit
#   hit       a hit is liam_tsunami's damage (half a heart) and carries the player down the ring for 0.35 s
#   collapse  the pillar's first hit of a round (as it opens) collapses every wave still rolling, harmlessly, each not
#             yet crashed adding its water

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")


static func wave_damage() -> int:
	return HitInfo.make(&"liam_tsunami", null, Vector2.ZERO).damage


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	t.track_dodges()
	t.track_parries()
	await bands(t)
	await tell(t)
	await dash(t)
	await corner(t)
	await inset(t)
	await parry(t)
	await hit(t)
	await collapse(t)


static func bands(t) -> void:
	t.log_p("-- a whole Tsunami")
	await Common.fresh(t, Vector2(1500, 900))
	var tsunami: Node = t.sm.states["Tsunami"]
	var height: float = t.sm.wave_height
	var gap: float = t.sm.wave_gap
	var worst_gap := [0.0]
	var worst_water := [0.0]
	var full_at := [-1.0]
	var bad_band := [0]
	# Each wave's clock when its front crossed the top rope (its swell gone) and when it came out of the row's foot.
	var crossed := {}
	var out_of_row := {}
	var watch := func():
		t.player.is_invincible = true
		if Common.state(t) != "Tsunami":
			return
		var waves: Array = tsunami.waves
		var spent := 0
		for k in waves.size():
			var wave = waves[k]
			if not is_instance_valid(wave):
				spent += 1
				continue
			if wave.spent:
				spent += 1
			var band: Rect2 = wave.band()
			var across: Vector2 = Layout.wave_x(wave.side)
			if band.position.x != across.x or band.end.x != across.y or band.size.y != height:
				bad_band[0] += 1
			if k + 1 < waves.size() and is_instance_valid(waves[k + 1]):
				worst_gap[0] = maxf(worst_gap[0], absf(wave.front_y - height - gap - waves[k + 1].front_y))
			if not crossed.has(k) and wave.front_y >= t.sm.ROPES.position.y:
				crossed[k] = tsunami.clock
			if not out_of_row.has(k) and wave.front_y >= t.boss.row.band().end.y:
				out_of_row[k] = tsunami.clock
		worst_water[0] = maxf(worst_water[0], absf(t.boss.flood.coverage - minf(spent / float(t.sm.flood_waves), 1.0)))
		if full_at[0] < 0.0 and t.boss.flood.coverage >= 1.0:
			full_at[0] = tsunami.clock
	t.physics_frame.connect(watch)
	Common.start(t, "Tsunami")
	var ended: bool = await t.wait_until(func(): return Common.state(t) != "Tsunami", 60 * 16)
	t.physics_frame.disconnect(watch)
	t.player.is_invincible = false
	var sides: Array = tsunami.spawn_log.map(func(entry): return entry.side)
	var alternating := sides.size() > 1
	for k in range(1, sides.size()):
		alternating = alternating and sides[k] != sides[k - 1]
	var seam: float = Layout.WAVE_LEFT_X.y - Layout.WAVE_RIGHT_X.x
	# Out of the row's foot the rope-to-face fall after the swell goes: (348 - 114) / 600, 0.39 s.
	var behind_row: float = (t.boss.row.band().end.y - t.sm.ROPES.position.y) / t.sm.wave_speed
	var worst_out := 0.0
	for k in crossed:
		if out_of_row.has(k):
			worst_out = maxf(worst_out, absf(out_of_row[k] - crossed[k] - behind_row))
	# The flood_waves-th wave's front crashes on the bottom rope: its spawn, plus its fall from where it spawned.
	var nth: Dictionary = tsunami.spawn_log[t.sm.flood_waves - 1] if tsunami.spawn_log.size() >= t.sm.flood_waves else {}
	var full_due: float = nth.t + (t.sm.ROPES.end.y - nth.front) / t.sm.wave_speed if not nth.is_empty() else -1.0
	t.log_p("%d waves %s..., worst gap off %.0f %.2f px, out of the row's foot %.2f s after the swell (worst %.3f off), worst water %.4f, full at %.2f s (the %dth crash due %.2f), next %s" % [sides.size(), sides.slice(0, 4), gap, worst_gap[0], behind_row, worst_out, worst_water[0], full_at[0], t.sm.flood_waves, full_due, Common.state(t)])
	t.check(sides.size() == tsunami.wave_count() and tsunami.wave_count() == 12, "%d waves (%d)" % [tsunami.wave_count(), sides.size()])
	t.check(alternating and sides[0] == &"right", "one side then the other, the first on the player's half (%s)" % [sides.slice(0, 4)])
	t.check(bad_band[0] == 0 and is_equal_approx(seam, 12.0), "every band exactly its half, 360 tall, 12 px over the seam")
	t.check(worst_gap[0] <= 1.0, "%.0f px between one wave's top and the next one's front on every frame (worst %.2f px off)" % [gap, worst_gap[0]])
	t.check(out_of_row.size() == crossed.size() and worst_out <= 2.5 / 60.0, "every wave comes out of the row's foot %.2f s after its swell" % behind_row)
	t.check(worst_water[0] <= 0.0001, "the flood up 1/%d as each wave's front crashes on the bottom rope (worst %.4f off)" % [t.sm.flood_waves, worst_water[0]])
	t.check(full_at[0] >= 0.0 and absf(full_at[0] - full_due) <= 1.0 / 60.0 + 0.001, "full on the %dth crash (%.2f s, due %.2f)" % [t.sm.flood_waves, full_at[0], full_due])
	var reset: bool = Common.state(t) == "RoundBlast"
	var health: int = t.player.playerHealth
	var next: bool = await t.wait_until(func(): return Common.state(t) == "Tremors", 60 * 3)
	var landed: Vector2 = t.player.global_position
	t.log_p("then %s: the player at %s, health %d -> %d, then %s" % ["his wind's reset" if reset else "no reset", landed, health, t.player.playerHealth, Common.state(t)])
	t.check(ended and reset and next and landed.distance_to(t.sm.RESET_SPOT) <= 1.0 and t.player.playerHealth == health, "run out: his wind blows the player to %s, unhurt, then Tremors" % t.sm.RESET_SPOT)
	await Common.clear(t)


static func tell(t) -> void:
	t.log_p("-- the tell")
	await Common.fresh(t, Vector2(400, 900))
	Common.start(t, "Tsunami")
	await t.wait(1)
	var tsunami: Node = t.sm.states["Tsunami"]
	var wave: Node2D = tsunami.waves[0]
	var badges: Array = t.live_tells()
	var at: Vector2 = badges[0].global_position if badges.size() == 1 else Vector2.INF
	var telling_before: bool = wave.tell.visible
	var shielded_in_tell: bool = t.boss.pillar.shielded
	await t.wait_until(func(): return wave.front_y >= t.sm.ROPES.position.y, 60)
	await t.wait(1)
	t.log_p("badge at %s (%s), tell up %s, then %s" % [at, wave.side, telling_before, wave.tell.visible])
	t.check(badges.size() == 1 and at == Layout.WAVE_BADGE[wave.side] and not badges[0].dodge, "one red badge on the half's anchor %s" % Layout.WAVE_BADGE[wave.side])
	t.check(telling_before and not wave.tell.visible, "the swell behind the top rope until the front crosses it")
	t.check(not t.sm.states["Tsunami"].waves.is_empty() and shielded_in_tell and t.boss.pillar.shielded, "and the pillar stays shielded through the first tell (liam_tsunami_gate: it opens on the gate wave's crash)")
	await Common.clear(t)


# Straight up into a wave, the dash kicking off with its front this far over the player's hurtbox.
static func dash(t) -> void:
	var immunity: float = HitInfo.make(&"liam_tsunami", null, Vector2.ZERO).dash_immunity
	t.check(is_equal_approx(immunity, 0.21), "liam_tsunami's dash immunity is 0.21 s (%.2f)" % immunity)
	for lead in [4.0, 40.0, 110.0]:
		t.log_p("-- a dash straight up, the front %.0f px over the player" % lead)
		await Common.fresh(t, Vector2(500, 880))
		var wave: Node2D = Common.spawn_wave(t, &"left", Common.hurtbox_top(t) - lead - 200.0)
		await t.wait_until(func(): return wave.front_y >= Common.hurtbox_top(t) - lead, 60)
		var health: int = t.player.playerHealth
		t.press(KEY_UP)
		t.tap(KEY_W)
		await t.wait_until(func(): return not is_instance_valid(wave) or wave.front_y - wave.height > t.area_rect(t.player.hurtBox).end.y, 90)
		t.release(KEY_UP)
		var results: Array = wave.results if is_instance_valid(wave) else []
		t.log_p("results %s, health %d -> %d" % [results.map(func(r): return HitInfo.Result.keys()[r]), health, t.player.playerHealth])
		t.check(results.has(HitInfo.Result.HIT) and t.player.playerHealth == health - wave_damage(), "hit, whatever the timing")
		await Common.clear(t)


# The left wave below and the right one stacked on it, the player beside the left one on the right, the right one's front
# about to reach them: a dash up and left through the corner where they meet.
static func corner(t) -> void:
	t.log_p("-- a diagonal dash through the corner")
	# Past the last perfect dodge's cooldown, which the dashes up paid.
	await t.wait_until(func(): return t.defense.clock - t.defense.last_perfect_dodge_time >= t.defense.perfect_dodge_cooldown + 0.1, 180)
	await Common.fresh(t, Vector2(1100, 600), 60)
	var top: float = Common.hurtbox_top(t)
	var right: Node2D = Common.spawn_wave(t, &"right", top - 45.0)
	var left: Node2D = Common.spawn_wave(t, &"left", top - 45.0 + t.sm.wave_height + t.sm.wave_gap)
	# The dash kicks off on the next frame, a wave's step closer: its front then 5 px over the player.
	await t.wait_until(func(): return right.front_y >= top - 15.0, 20)
	var stamina: float = t.defense.stamina
	var health: int = t.player.playerHealth
	var dodges_before: int = t.dodges.size()
	t.press(KEY_UP)
	t.press(KEY_LEFT)
	t.tap(KEY_W)
	await t.wait(6)
	t.release(KEY_UP)
	t.release(KEY_LEFT)
	await t.wait(60)
	var right_results: Array = right.results.duplicate() if is_instance_valid(right) else []
	var left_results: Array = left.results.duplicate() if is_instance_valid(left) else []
	t.log_p("right wave %s, left wave %s, perfect dodges %d, stamina %.1f -> %.1f, health %d -> %d" % [right_results.map(func(r): return HitInfo.Result.keys()[r]), left_results, t.dodges.size() - dodges_before, stamina, t.defense.stamina, health, t.player.playerHealth])
	t.check(right_results == [HitInfo.Result.DODGED] and left_results.is_empty(), "DODGED through the corner, and the other wave never touched")
	t.check(t.dodges.size() - dodges_before == 1 and t.dodges[-1].id == &"liam_tsunami", "a perfect dodge")
	t.check(is_equal_approx(t.defense.stamina, stamina) and t.player.playerHealth == health, "the dash's stamina back, unhurt")
	await Common.clear(t)


# A wave rolling over a player standing across its seam end, their hurtbox reaching `inside` px into the drawn band.
static func inset(t) -> void:
	for side in [&"left", &"right"]:
		for inside in [17.0, 19.0]:
			t.log_p("-- a %s wave over a player %.0f px inside its seam end" % [side, inside])
			await Common.fresh(t, Vector2(500, 880), 60)
			var across := Layout.wave_x(side)
			var box: Rect2 = t.area_rect(t.player.hurtBox)
			var edge: float = across.y - inside if side == &"left" else across.x + inside
			t.player.global_position.x += edge - (box.position.x if side == &"left" else box.end.x)
			await t.wait(1)
			var health: int = t.player.playerHealth
			var wave: Node2D = Common.spawn_wave(t, side, Common.hurtbox_top(t) - 60.0)
			await t.wait_until(func(): return not is_instance_valid(wave) or wave.front_y - wave.height > t.area_rect(t.player.hurtBox).end.y, 90)
			var results: Array = wave.results.duplicate() if is_instance_valid(wave) else []
			var hit: bool = results.has(HitInfo.Result.HIT)
			t.log_p("hurtbox %s, results %s, health %d -> %d" % [t.area_rect(t.player.hurtBox), results.map(func(r): return HitInfo.Result.keys()[r]), health, t.player.playerHealth])
			if inside < Layout.WAVE_SEAM_INSET:
				t.check(not hit and t.player.playerHealth == health, "%s wave, %.0f px inside its seam end: not hit" % [side, inside])
			else:
				t.check(hit and t.player.playerHealth == health - wave_damage(), "%s wave, %.0f px inside its seam end: hit" % [side, inside])
			await Common.clear(t)


static func parry(t) -> void:
	t.log_p("-- a parry")
	await Common.fresh(t, Vector2(500, 850), 60)
	var wave: Node2D = Common.spawn_wave(t, &"left", Common.hurtbox_top(t) - 200.0)
	var parries_before: int = t.parries.size()
	var health: int = t.player.playerHealth
	await t.wait_until(func(): return wave.front_y >= Common.hurtbox_top(t) - 30.0, 60)
	t.press(KEY_SHIFT)
	await t.wait(4)
	t.release(KEY_SHIFT)
	await t.wait_until(func(): return not is_instance_valid(wave) or wave.front_y - wave.height > t.area_rect(t.player.hurtBox).end.y, 90)
	var results: Array = wave.results if is_instance_valid(wave) else []
	t.log_p("results %s, parries %d, health %d -> %d" % [results.map(func(r): return HitInfo.Result.keys()[r]), t.parries.size() - parries_before, health, t.player.playerHealth])
	t.check(results == [HitInfo.Result.PARRIED] and t.parries.size() - parries_before == 1, "PARRIED, once")
	t.check(t.player.playerHealth == health, "and it rolls on through the player without a second hit")
	await Common.clear(t)


static func hit(t) -> void:
	t.log_p("-- a hit")
	await Common.fresh(t, Vector2(500, 600), 60)
	var wave: Node2D = Common.spawn_wave(t, &"left", Common.hurtbox_top(t) - 60.0)
	var health: int = t.player.playerHealth
	await t.wait_until(func(): return t.player.playerHealth < health, 30)
	var y0: float = t.player.global_position.y
	await t.wait(roundi(t.sm.wave_carry * 60.0) + 4)
	var carried: float = t.player.global_position.y - y0
	t.log_p("health %d -> %d, carried %.1f px" % [health, t.player.playerHealth, carried])
	t.check(t.player.playerHealth == health - wave_damage() and wave.results == [HitInfo.Result.HIT], "%d half-hearts" % wave_damage())
	var want: float = t.sm.wave_speed * t.sm.wave_carry
	t.check(absf(carried - want) <= 15.0, "carried %.0f px down the ring, 0.35 s at the wave's speed (%.1f)" % [want, carried])
	await Common.clear(t)


static func collapse(t) -> void:
	t.log_p("-- the pillar's first hit")
	await Common.fresh(t, t.sm.FRONT_SPOT, 60)
	var keep_safe := func(): t.player.is_invincible = true
	t.physics_frame.connect(keep_safe)
	t.boss.flood.drain(0.0)
	Common.start(t, "Tsunami")
	# As it opens on the gate wave's crash: waves rolling, the gate wave with its water already spent, and no other
	# crash due until the punch has landed.
	await t.wait_until(func(): return not t.boss.pillar.shielded, 60 * 8)
	var tsunami: Node = t.sm.states["Tsunami"]
	var rolling: Array = tsunami.waves.filter(func(w): return is_instance_valid(w) and not w.finished)
	var unspent: int = rolling.filter(func(w): return not w.spent).size()
	var water: float = t.boss.flood.coverage
	var took: bool = await Common.punch_pillar(t)
	await t.wait(2)
	var collapsing: bool = rolling.all(func(w): return not is_instance_valid(w) or w.collapsing)
	await t.wait(24)
	var gone: bool = rolling.all(func(w): return not is_instance_valid(w))
	var water_now: float = t.boss.flood.coverage
	t.physics_frame.disconnect(keep_safe)
	t.player.is_invincible = false
	t.log_p("%d rolling, took %s, now %s, collapsing %s, gone %s, water %.3f -> %.3f" % [rolling.size(), took, Common.state(t), collapsing, gone, water, water_now])
	t.check(took and Common.state(t) == "Wobble", "the pillar took it and he wobbles")
	t.check(rolling.size() >= 2 and collapsing and gone, "every wave still rolling collapsed and is gone")
	var due: float = minf(water + unspent / float(t.sm.flood_waves), 1.0)
	t.check(unspent >= 2 and absf(water_now - due) <= 0.0001, "each not yet crashed adding its 1/%d to the flood, up to full (%d of them)" % [t.sm.flood_waves, unspent])
	await Common.clear(t)
