extends RefCounted

# slam_point: the ground right round his slam's blade (EricEarthquake._strike_inside, the playtest of
# 2026-10-04). His waves set off 60 px out from the blade and take a physics step before they meet anyone,
# so a player standing at its tip, flush against his lower left, was safe from every slam. --fixed-fps 60,
# on EricPacing V2, Eric parked, each slam's waves spawned the way his animation spawns them, a straight
# and a tilted one, with the i-frames cleared after every hit so each one counts:
#   the pocket   standing on the tip with no input, each slam lands exactly one hit there: the blade's own,
#                of the waves' id, from the slam point.
#   parried      a fresh press just before the blade comes down parries that hit, once, and nothing lands;
#                the two slams come less than blocked_rehit_interval apart, so one parried can't cover the next.
#   no doubles   on the ground round the tip, every spot the player can stand on is struck by each pattern,
#                and never by both the blade and a wave in one slam.
#   far off      a spot well clear of the blade is never struck by the blade itself.

const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const EricArtLayout := preload("res://Scripts/EricArtLayout.gd")
const EricPacing := preload("res://Scripts/EricPacing.gd")

# The player's feet from the slam point: the middle of the pocket the playtest found.
const POCKET := Vector2(-15, 30)
# The ground swept round the tip, feet from the slam point, and how finely.
const SWEEP_X := Vector2i(-90, 30)
const SWEEP_Y := Vector2i(-30, 90)
const SWEEP_STEP := 15
# Well clear of the blade, out along his left.
const FAR_OFF := Vector2(-320, 0)
# Long enough for every wave to have passed the ground swept round the tip.
const SLAM_FRAMES := 24


static func run(t) -> void:
	await t.load_eric_v2()
	t.hold_gauge()
	t.park_eric()
	t.player.playerHealth = 100000
	var slam_point: Vector2 = t.boss.frame_point(EricArtLayout.SLAM_PIXEL)
	t.log_p("Eric at %s, the slam point %s" % [t.boss.global_position, slam_point])
	# The blade's hit lands inside enable_hitbox() itself; a wave's only on a physics step after it.
	var seen := {"landing": 0, "waves": 0, "parried": 0, "origin": Vector2.INF, "ids": [], "in_slam": false}
	t.defense.hit_taken.connect(func(hit):
		if str(hit.attack_id).begins_with("eric_quake"):
			if not seen.in_slam:
				seen.waves += 1
			else:
				seen.landing += 1
				seen.origin = hit.origin
			seen.ids.append(hit.attack_id)
		t.clear_iframes())
	var parried_at: Array[float] = []
	t.defense.parried.connect(func(hit, _point, _staggered, _streak):
		if str(hit.attack_id).begins_with("eric_quake"):
			seen.parried += 1
			parried_at.append(t.defense.clock))

	t.log_p("-- the pocket: no input")
	for tilted in [false, true]:
		await stand(t, slam_point, POCKET)
		await slam(t, tilted, seen)
		var pattern := "tilted" if tilted else "straight"
		t.log_p("%s: blade %d, waves %d, ids %s, from %s" % [pattern, seen.landing, seen.waves, seen.ids, seen.origin])
		t.check(seen.landing == 1 and seen.waves == 0, "the %s slam strikes the player on its tip exactly once, with the blade (%d, %d)" % [pattern, seen.landing, seen.waves])
		t.check(seen.ids.all(func(id): return id == EricPacing.value("wave_id")), "as the waves' own attack (%s)" % [seen.ids])
		t.check(seen.origin.distance_to(slam_point) < 0.5, "from the slam point (%s)" % [seen.origin])

	t.log_p("-- the pocket: a fresh press just before each of two slams in a row")
	await stand(t, slam_point, POCKET)
	for tilted in [false, true]:
		t.press(KEY_SHIFT)
		await t.wait(2)
		await slam(t, tilted, seen)
		t.release(KEY_SHIFT)
		var pattern := "tilted" if tilted else "straight"
		t.check(seen.parried == 1 and seen.landing == 0 and seen.waves == 0, "the %s slam is parried there once, and nothing lands (parried %d, hit %d)" % [pattern, seen.parried, seen.landing + seen.waves])
		await t.wait(2)
	var gap: float = parried_at[-1] - parried_at[0] if parried_at.size() == 2 else INF
	t.check(gap < t.defense.blocked_rehit_interval, "%.2f s apart, inside the %.1f s a parried source is absorbed for: one parried slam never covers the next" % [gap, t.defense.blocked_rehit_interval])
	await t.past_window()

	t.log_p("-- the ground round the tip")
	var missed := []
	var doubled := []
	var blade_spots := 0
	var spots := 0
	for dy in range(SWEEP_Y.x, SWEEP_Y.y + 1, SWEEP_STEP):
		for dx in range(SWEEP_X.x, SWEEP_X.y + 1, SWEEP_STEP):
			var feet := Vector2(dx, dy)
			if not await stand(t, slam_point, feet):
				continue
			spots += 1
			for tilted in [false, true]:
				await stand(t, slam_point, feet)
				await slam(t, tilted, seen)
				if seen.landing + seen.waves == 0:
					missed.append([feet, "tilted" if tilted else "straight"])
				if seen.landing > 0 and seen.waves > 0:
					doubled.append([feet, "tilted" if tilted else "straight"])
				if seen.landing > 0:
					blade_spots += 1
	t.log_p("%d spots, %d slams struck with the blade, missed %s, doubled %s" % [spots, blade_spots, missed, doubled])
	t.check(spots > 40 and blade_spots > 0, "the sweep stood on %d spots and met the blade on %d slams" % [spots, blade_spots])
	t.check(missed.is_empty(), "every spot round the tip is struck by both patterns (%s)" % [missed])
	t.check(doubled.is_empty(), "and none by both the blade and a wave in one slam (%s)" % [doubled])

	t.log_p("-- far off")
	for tilted in [false, true]:
		await stand(t, slam_point, FAR_OFF)
		await slam(t, tilted, seen)
		t.check(seen.landing == 0, "%s px off the blade, the %s slam's blade never reaches (waves %d)" % [FAR_OFF.length(), "tilted" if tilted else "straight", seen.waves])


# The player's feet `feet` from the slam point, still, out of their i-frames. False where his body won't
# let them stand.
static func stand(t, slam_point: Vector2, feet: Vector2) -> bool:
	var at: Vector2 = slam_point + feet - FinisherArtLayout.PLAYER_FEET
	await t.settle_player(at)
	t.clear_iframes()
	return t.player.global_position.distance_to(at) <= 3.0


# One slam's waves, spawned as enable_hitbox spawns them, run until they are past the ground round the tip.
static func slam(t, tilted: bool, seen: Dictionary) -> void:
	seen.landing = 0
	seen.waves = 0
	seen.parried = 0
	seen.origin = Vector2.INF
	seen.ids = []
	var quake: Node = t.sm.states["Earthquake"]
	quake.tilted_next = tilted
	quake.projectile_speed_now = EricPacing.raged("wave_speed", 0.0)
	seen.in_slam = true
	quake.enable_hitbox()
	seen.in_slam = false
	for i in SLAM_FRAMES:
		await t.physics_frame
	for hazard in t.live_hazards():
		hazard.free()
	await t.wait(1)
