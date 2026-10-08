extends RefCounted

# liam_zip: the tsunami's corner zip (addendum part 2), on his test scene. Two waves stacked the way LiamTsunami stacks
# them: S on the player's half with its front coming down on them, and the other half's wave O with its top wave_gap
# under S's front, beside them. The player stands with their hurtbox centre `d` px from x 960 on S's half (y 600), holds the diagonal and
# dashes as S's front is `lead` frames (10 px each) above their hurtbox top, one trial per lead, the diagonal held on
# through the second after it (the addendum's "direction held"). A clean trial: no HIT from either wave and their health
# unchanged a second after the press.
#   sweep   d 8..240 every 8 px, up-left from the right half and up-right from the left half: the clean counts match at
#           every d, at least 30 clean frames at 80 px, and a lane at least 200 px wide with at least 12 clean frames at
#           every d across it. Down-left and down-right (every 32 px) are only reported. The table is printed.
#   sideways  Left and W from 40 px right of the seam, straight across the middle: at least 14 clean frames (80 px logged)
#   grace   holding Up, W tapped and Left pressed 1, 2 or 3 frames later: 1 and 2 end on the clean diagonal (+-2 px), 3
#           is a straight dash; with the grace at 0, all three are today's straight dash, frame for frame
#   chain   logged only: the Tsunami's own stack of four, a zip up-left and the next corner's zip up-right 48 frames
#           later (a corner every (wave_height + wave_gap) / wave_speed), whether both come out clean

const Common := preload("res://art_source/defense_tests/liam/common.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const Y := 600.0
const DISTANCES := [8, 240, 8]
const REPORT_EVERY := 32
const LEADS := [-3, 44]
const WATCH_FRAMES := 60
# [S's half, the side key, the up/down key, name], asserted first.
const ZIPS := [
	[&"right", KEY_LEFT, KEY_UP, "up-left"],
	[&"left", KEY_RIGHT, KEY_UP, "up-right"],
	[&"right", KEY_LEFT, KEY_DOWN, "down-left"],
	[&"left", KEY_RIGHT, KEY_DOWN, "down-right"],
]
# Straight across the middle: Left alone (trial's up/down key is Left too).
const SIDEWAYS := [&"right", KEY_LEFT, KEY_LEFT, "sideways"]
const DASH_LENGTH := 250.0


static func run(t) -> void:
	await Common.enter(t)
	t.track()
	await sweep(t)
	await sideways(t)
	await grace(t)
	await chain(t)


# Two corners in a row: S (right) coming down on the player 80 px right of the seam, O (left) under it, N (left) over the
# band the first zip lands in and M (right) over the band the second one does. Up-left at `lead`, up-right 42 frames on.
static func chain(t) -> void:
	var step: float = t.sm.wave_height + t.sm.wave_gap
	var between := roundi(step / t.sm.wave_speed * 60.0)
	for lead in [4, 10, 16]:
		await Common.fresh(t, Vector2(1040, Y), 0)
		t.player.global_position.x += 1040.0 - t.area_rect(t.player.hurtBox).get_center().x
		await t.wait(1)
		var top: float = Common.hurtbox_top(t)
		var front: float = top - lead * 10.0 - 40.0
		var waves: Array = [Common.spawn_wave(t, &"right", front), Common.spawn_wave(t, &"left", front + step),
			Common.spawn_wave(t, &"left", front - step), Common.spawn_wave(t, &"right", front - 2.0 * step)]
		await t.wait(3)
		var health: int = t.player.playerHealth
		t.press(KEY_UP)
		t.press(KEY_LEFT)
		t.tap(KEY_W)
		# Let go once it has landed, rather than walking up into the next wave.
		await t.wait(6)
		Common.keys_up(t)
		await t.wait(between - 6)
		var after_first: int = t.player.playerHealth
		t.press(KEY_UP)
		t.press(KEY_RIGHT)
		t.tap(KEY_W)
		await t.wait(6)
		Common.keys_up(t)
		await t.wait(54)
		var hits := 0
		for wave in waves:
			if is_instance_valid(wave):
				hits += wave.results.count(HitInfo.Result.HIT)
		t.log_p("chain from lead %d: the second zip %d frames after the first; first %s, second %s, %d wave hits in all" % [lead, between, "clean" if after_first == health else "hit", "clean" if t.player.playerHealth == after_first else "hit", hits])
		await Common.clear(t)


static func sweep(t) -> void:
	t.log_p("-- the corner zip, clean press frames by distance from the seam")
	var counts := {}
	for zip in ZIPS:
		counts[zip[3]] = {}
		for d in range(DISTANCES[0], DISTANCES[1] + 1, DISTANCES[2]):
			if zip[2] == KEY_DOWN and (d - DISTANCES[0]) % REPORT_EVERY != 0:
				continue
			var clean := 0
			for lead in range(LEADS[0], LEADS[1] + 1):
				if await trial(t, zip, float(d), lead):
					clean += 1
			counts[zip[3]][d] = clean
	var rows := ["   d  up-left  up-right  down-left  down-right"]
	for d in range(DISTANCES[0], DISTANCES[1] + 1, DISTANCES[2]):
		rows.append("%4d  %7d  %8d  %9s  %10s" % [d, counts["up-left"][d], counts["up-right"][d], str(counts["down-left"].get(d, "")), str(counts["down-right"].get(d, ""))])
	t.log_p("clean press frames (leads %d..%d):\n%s" % [LEADS[0], LEADS[1], "\n".join(rows)])
	var unequal := []
	for d in counts["up-left"]:
		if counts["up-left"][d] != counts["up-right"][d]:
			unequal.append(d)
	var lane := 0
	var widest := 0
	for d in range(DISTANCES[0], DISTANCES[1] + 1, DISTANCES[2]):
		lane = lane + DISTANCES[2] if counts["up-left"][d] >= 12 and counts["up-right"][d] >= 12 else 0
		widest = maxi(widest, lane)
	t.check(unequal.is_empty(), "up-left and up-right clean counts equal at every distance (unequal at %s)" % [unequal])
	t.check(counts["up-left"][80] >= 30 and counts["up-right"][80] >= 30, "at least 30 clean frames at 80 px (%d, %d)" % [counts["up-left"][80], counts["up-right"][80]])
	t.check(widest >= 200, "a lane of at least 200 px with at least 12 clean frames (%d px)" % widest)


static func sideways(t) -> void:
	var clean := {}
	for d in [40, 80]:
		clean[d] = 0
		for lead in range(LEADS[0], LEADS[1] + 1):
			if await trial(t, SIDEWAYS, float(d), lead):
				clean[d] += 1
	t.log_p("a sideways dash across the middle, clean press frames: %d from 40 px right of the seam, %d from 80 px" % [clean[40], clean[80]])
	t.check(clean[40] >= 14, "a sideways dash from 40 px right of the seam: at least 14 clean frames (%d)" % clean[40])


# One press: whether it came out clean.
static func trial(t, zip: Array, d: float, lead: int) -> bool:
	var side: StringName = zip[0]
	var toward := 1.0 if side == &"right" else -1.0
	await Common.fresh(t, Vector2(960.0 + toward * d, Y), 0)
	t.player.global_position.x += 960.0 + toward * d - t.area_rect(t.player.hurtBox).get_center().x
	await t.wait(1)
	var top: float = Common.hurtbox_top(t)
	var other := &"left" if side == &"right" else &"right"
	var s_wave: Node2D = Common.spawn_wave(t, side, top - lead * 10.0 - 40.0)
	var o_wave: Node2D = Common.spawn_wave(t, other, top - lead * 10.0 - 40.0 + t.sm.wave_height + t.sm.wave_gap)
	await t.wait(3)
	var health: int = t.player.playerHealth
	t.press(zip[2])
	t.press(zip[1])
	t.tap(KEY_W)
	# The whole second every time, hit or not: it also keeps the next trial's dash clear of this one's re-dash and
	# immunity cooldowns.
	var hit := false
	for f in WATCH_FRAMES:
		await t.physics_frame
		for wave in [s_wave, o_wave]:
			if is_instance_valid(wave) and wave.results.has(HitInfo.Result.HIT):
				hit = true
	Common.keys_up(t)
	var clean: bool = not hit and t.player.playerHealth == health
	await Common.clear(t)
	return clean


static func grace(t) -> void:
	for grace_frames in [t.player.dash_diagonal_grace, 0]:
		t.player.dash_diagonal_grace = grace_frames
		var straight: Array = await dash(t, -1)
		for late in [1, 2, 3]:
			var path: Array = await dash(t, late)
			var start: Vector2 = path[0]
			var end: Vector2 = path[-1]
			var diagonal := start + Vector2(-1, -1).normalized() * DASH_LENGTH
			var up := start + Vector2(0, -DASH_LENGTH)
			t.log_p("grace %d, Left %d frames late: %s -> %s (diagonal %s, straight %s)" % [grace_frames, late, start, end, diagonal, up])
			if grace_frames > 0 and late <= grace_frames:
				t.check(end.distance_to(diagonal) <= 2.0, "grace %d, Left %d frames late: the clean diagonal" % [grace_frames, late])
			elif grace_frames > 0:
				t.check(end.distance_to(up) <= 2.0, "grace %d, Left %d frames late: a straight dash" % [grace_frames, late])
			else:
				t.check(path == straight, "grace 0, Left %d frames late: today's straight dash, frame for frame" % late)
	t.player.dash_diagonal_grace = t.boss.dash_diagonal_grace


# Up held and W tapped together, Left pressed `late` frames later (never, below 0): where the dash started and where
# each of its frames left the player. Past the re-dash cooldown afterwards.
static func dash(t, late: int) -> Array:
	await Common.fresh(t, Vector2(1300, 700), 0)
	t.press(KEY_UP)
	t.tap(KEY_W)
	var origin := Vector2.INF
	var path: Array = []
	for f in 12:
		if f == late:
			t.press(KEY_LEFT)
		await t.physics_frame
		if origin == Vector2.INF and t.player.is_dodging:
			origin = t.player.dash_origin
		if origin != Vector2.INF:
			path.append(t.player.global_position)
			if not t.player.is_dodging:
				break
	Common.keys_up(t)
	await t.wait(40)
	return [origin] + path
