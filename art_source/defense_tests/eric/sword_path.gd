extends RefCounted

# sword_path: his thrown sword hurts nobody on its way to the mark it lands on (EricThrownSwordScript), and
# the mark's lit ring is drawn the size of what it lands on (EricSwordMark). --fixed-fps 60, on EricPacing
# V2. Each throw is aimed at a player standing on the scenario's spot, who is moved the moment it leaves his
# hand and held where STANDS puts them until it lands: on its path at points between him and the mark,
# beside that path, beside the mark, and on the mark itself.
#   in the air   no hit of any kind while the blade is still flying, wherever they stand - including the
#                spots its reach passes right through, which are counted, so the mode can't pass for want
#                of a blade there to hold back.
#   landing      its own hit lands only on the frame it goes into the mark, and only on whoever its reach
#                covers there; one standing on the mark takes it.
#   the ring     read off the lit frame as it is drawn: every spot the player can stand on that the landing
#                reaches lies inside the ring, and every spot inside the ring is reached. The ring's band is
#                its edge, so a spot on the band may go either way.
# Across the ring at his usual speed, and close in with him enraged, where the flight is stretched to its
# 0.72 s floor and the blade dives the whole way.

const SWORD := &"eric_thrown_sword"
const SCENARIOS := [
	{"name": "across the ring", "eric": Vector2(300, 450), "spot": Vector2(1700, 800), "rage": 0.0},
	{"name": "close in, enraged", "eric": Vector2(960, 380), "spot": Vector2(1150, 720), "rage": 1.0},
]
const ON_THE_MARK := "on the mark"
# Where the player is held, as [what, how far along from his hand's ground point to the mark, px back
# from there along the path, offset in the picture]. Behind is up the screen, where the lobbed blade
# passes over them in the picture; in front is down it.
const STANDS := [
	["on its path, a quarter of the way", 0.25, 0.0, Vector2.ZERO],
	["on its path, halfway", 0.5, 0.0, Vector2.ZERO],
	["on its path, three quarters of the way", 0.75, 0.0, Vector2.ZERO],
	["on its path, just out of the mark's reach", 1.0, 180.0, Vector2.ZERO],
	["behind its path, halfway, where it passes over them", 0.5, 0.0, Vector2(0, -280)],
	["in front of its path, halfway", 0.5, 0.0, Vector2(0, 160)],
	["behind the mark, clear of its ring", 1.0, 0.0, Vector2(0, -190)],
	[ON_THE_MARK, 1.0, 0.0, Vector2.ZERO],
]
# The lit ring's texels: clear of it, on its band, or enclosed by it.
enum Cell { OUTSIDE, BAND, INSIDE }
# How far round the mark the ring is swept, and how finely: half a texel of the mark's 3x art.
const RING_REACH := 240.0
const RING_STEP := 1.5
const WAYS_OUT := {"right": Vector2.RIGHT, "left": Vector2.LEFT, "down": Vector2.DOWN, "up": Vector2.UP}


static func run(t) -> void:
	await t.load_eric_v2()
	t.hold_gauge()
	t.player.playerHealth = 100000
	var covered := 0
	for scenario in SCENARIOS:
		t.log_p("-- %s" % scenario.name)
		t.boss.global_position = scenario.eric
		t.sm.rage = scenario.rage
		for stand in STANDS:
			var on_mark: bool = stand[0] == ON_THE_MARK
			var seen: Dictionary = await throw_at(t, scenario.spot, stand, on_mark)
			var early: Array = seen.hits.filter(func(h): return h.flying)
			var own: Array = seen.hits.filter(func(h): return h.id == SWORD)
			var what := "%s, %s" % [scenario.name, stand[0]]
			t.log_p("%s: held at %s on a %.0f px, %.2f s throw at %.0f px/s; its reach over them in the air from %.3f to %.3f of the flight, over them as it lands %s; hits %s" % [what, seen.at, seen.length, seen.duration, seen.speed, seen.cover[0], seen.cover[1], seen.landed_on, seen.hits])
			t.check(early.is_empty(), "%s: nothing hits them while the blade is in the air (%s)" % [what, early])
			t.check(own.all(func(h): return not h.flying and h.progress == 1.0), "%s: the blade's own hit only ever lands as it goes into the mark (%s)" % [what, own])
			t.check(own.size() == (1 if seen.landed_on else 0), "%s: and it lands on them exactly when its reach covers them there (%d hits, covered %s)" % [what, own.size(), seen.landed_on])
			if on_mark:
				t.check(seen.landed_on and own.size() == 1, "%s: standing on the mark, they take it as it lands" % what)
				t.check(seen.cover[0] >= 0.0 and seen.cover[0] < 1.0, "%s: though its reach was already over them from %.3f of the flight: it is held back all the way down" % [what, seen.cover[0]])
				check_ring(t, scenario.name, seen)
			if seen.cover[0] >= 0.0:
				covered += 1
	t.sm.rage = 0.0
	t.log_p("its reach passed through the player in the air at %d of the %d spots" % [covered, SCENARIOS.size() * STANDS.size()])
	t.check(covered >= SCENARIOS.size() * 2, "the blade does pass through them on its way at several spots, so there is something to hold back (%d)" % covered)


# One throw aimed at `spot`, the player moved to `stand` as it leaves his hand and held there until it has
# gone into the mark. What it saw: every hit, with whether the blade was still in the air and how far
# through its flight it was; the progress its reach first and last covered them in the air; and whether
# its reach covers them as it lands. With `measure_ring`, also the ring as it was lit, and where the
# landing and that ring disagree.
static func throw_at(t, spot: Vector2, stand: Array, measure_ring := false) -> Dictionary:
	t.clear_iframes()
	await t.settle_player(spot)
	var sword: Node2D = await t.throw_sword()
	var path: Vector2 = sword.to_ground - sword.from_ground
	var at: Vector2 = sword.from_ground + path * stand[1] - path.normalized() * stand[2] + stand[3]
	var seen := {"at": at, "length": path.length(), "duration": sword.duration, "speed": sword.speed, "hits": [], "cover": [-1.0, -1.0], "landed_on": false, "ring": {}, "gaps": {}}
	var on_hit := func(hit):
		var live: bool = is_instance_valid(sword)
		seen.hits.append({"id": hit.attack_id, "flying": live and sword.flying, "progress": sword.elapsed / sword.duration if live else -1.0})
	t.defense.hit_taken.connect(on_hit)
	# Before anything moves in the frame, so the blade is only ever tested against them where they are held.
	var hold := func(): t.player.global_position = at
	t.physics_frame.connect(hold)
	while is_instance_valid(sword) and sword.flying:
		await t.physics_frame
		if measure_ring and seen.ring.is_empty() and is_instance_valid(sword) and is_instance_valid(sword.mark) and t.mark_lit(sword.mark):
			seen.ring = lit_ring(sword.mark)
		if is_instance_valid(sword) and sword.flying and sword._reaches(t.player.hurtBox):
			var progress: float = sword.elapsed / sword.duration
			if seen.cover[0] < 0.0:
				seen.cover[0] = progress
			seen.cover[1] = progress
	# Planted, its reach is on the mark, where it was tested as it went in.
	seen.landed_on = is_instance_valid(sword) and sword._reaches(t.player.hurtBox)
	if measure_ring and is_instance_valid(sword) and not seen.ring.is_empty():
		seen.gaps = ring_gaps(t, sword, seen.ring)
	await t.wait(2)
	t.physics_frame.disconnect(hold)
	t.defense.hit_taken.disconnect(on_hit)
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	for hazard in t.live_hazards():
		hazard.queue_free()
	t.clear_iframes()
	await t.wait(2)
	return seen


static func check_ring(t, what: String, seen: Dictionary) -> void:
	if seen.ring.is_empty() or seen.gaps.is_empty():
		t.check(false, "%s: the lit ring is drawn off its sheet, so it can be measured" % what)
		return
	var gaps: Dictionary = seen.gaps
	var ways := []
	for way in WAYS_OUT:
		var along: Dictionary = gaps.ways[way]
		ways.append("%s: reaches %.1f, band %.1f-%.1f" % [way, along.reach, along.band_from, along.band_to])
	t.log_p("%s: the landing against the lit ring, px from the mark - %s" % [what, ", ".join(ways)])
	var farthest := func(spots: Array) -> String:
		if spots.is_empty():
			return "none"
		var worst: Vector2 = spots[0]
		for spot in spots:
			if spot.length() > worst.length():
				worst = spot
		return "%s, %.0f px out" % [worst, worst.length()]
	t.check(gaps.outside.is_empty(), "%s: every spot the landing reaches lies inside the lit ring (%d of %d spots reached outside it; farthest %s)" % [what, gaps.outside.size(), gaps.spots, farthest.call(gaps.outside)])
	t.check(gaps.unreached.is_empty(), "%s: and every spot inside the ring is reached (%d not; farthest %s)" % [what, gaps.unreached.size(), farthest.call(gaps.unreached)])


# The lit ring as it is drawn: its frame's texels sorted into outside it, its band and inside it, and the
# transform from the floor to those texels. Empty for a mark that draws no sprite.
static func lit_ring(mark: Node2D) -> Dictionary:
	var sprite: Sprite2D = mark.sprite
	if sprite == null:
		return {}
	var sheet: Image = sprite.texture.get_image()
	if sheet.is_compressed():
		sheet.decompress()
	sheet.convert(Image.FORMAT_RGBA8)
	var size := Vector2i(sheet.get_width() / sprite.hframes, sheet.get_height() / sprite.vframes)
	var frame := sheet.get_region(Rect2i(Vector2i(sprite.frame_coords.x * size.x, sprite.frame_coords.y * size.y), size))
	return {"cells": sort_cells(frame), "size": size, "to_texel": sprite.global_transform.affine_inverse(), "offset": sprite.offset}


# Outside: every clear texel reached from the frame's border through clear ones. The band: every drawn
# texel reached through drawn ones from one beside the outside. Inside: the rest, all that the band
# encloses, the lit frame's ticks included.
static func sort_cells(frame: Image) -> PackedByteArray:
	var w := frame.get_width()
	var h := frame.get_height()
	var data := frame.get_data()
	var drawn := PackedByteArray()
	drawn.resize(w * h)
	for i in w * h:
		drawn[i] = 1 if data[i * 4 + 3] > 0 else 0
	var cells := PackedByteArray()
	cells.resize(w * h)
	cells.fill(Cell.INSIDE)
	var todo: Array[Vector2i] = []
	for x in w:
		todo.append(Vector2i(x, 0))
		todo.append(Vector2i(x, h - 1))
	for y in h:
		todo.append(Vector2i(0, y))
		todo.append(Vector2i(w - 1, y))
	while not todo.is_empty():
		var p: Vector2i = todo.pop_back()
		var i := p.y * w + p.x
		if drawn[i] == 1 or cells[i] == Cell.OUTSIDE:
			continue
		cells[i] = Cell.OUTSIDE
		todo.append_array(beside(p, w, h))
	for y in h:
		for x in w:
			var p := Vector2i(x, y)
			if drawn[y * w + x] == 1 and beside(p, w, h).any(func(q): return cells[q.y * w + q.x] == Cell.OUTSIDE):
				todo.append(p)
	while not todo.is_empty():
		var p: Vector2i = todo.pop_back()
		var i := p.y * w + p.x
		if drawn[i] == 0 or cells[i] == Cell.BAND:
			continue
		cells[i] = Cell.BAND
		todo.append_array(beside(p, w, h))
	return cells


static func beside(p: Vector2i, w: int, h: int) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for q in [p + Vector2i.LEFT, p + Vector2i.RIGHT, p + Vector2i.UP, p + Vector2i.DOWN]:
		if q.x >= 0 and q.y >= 0 and q.x < w and q.y < h:
			out.append(q)
	return out


static func cell_at(ring: Dictionary, spot: Vector2) -> int:
	var texel: Vector2 = ring.to_texel * spot - ring.offset
	var x := floori(texel.x)
	var y := floori(texel.y)
	if x < 0 or y < 0 or x >= ring.size.x or y >= ring.size.y:
		return Cell.OUTSIDE
	return ring.cells[y * ring.size.x + x]


# Where the planted blade's landing and the lit ring disagree, over every spot round the mark the player's
# origin can be on (EricArtLayout.PLAYER_AREA): spots it reaches that lie outside the ring, and spots inside
# the ring it doesn't reach. The landing is the sword's own test, _reaches, against the player put on each
# spot. And, along each way out from the mark, how far it reaches and where the ring's band runs.
static func ring_gaps(t, sword: Node2D, ring: Dictionary) -> Dictionary:
	var area: Rect2 = load("res://Scripts/EricArtLayout.gd").PLAYER_AREA
	var home: Vector2 = t.player.global_position
	var mark: Vector2 = sword.to_ground
	var gaps := {"outside": [], "unreached": [], "spots": 0, "ways": {}}
	var steps := roundi(RING_REACH / RING_STEP)
	for iy in range(-steps, steps + 1):
		for ix in range(-steps, steps + 1):
			var spot := mark + Vector2(ix, iy) * RING_STEP
			if not area.has_point(spot):
				continue
			gaps.spots += 1
			t.player.global_position = spot
			var reached: bool = sword._reaches(t.player.hurtBox)
			var cell := cell_at(ring, spot)
			if reached and cell == Cell.OUTSIDE:
				gaps.outside.append(spot - mark)
			elif cell == Cell.INSIDE and not reached:
				gaps.unreached.append(spot - mark)
	for way in WAYS_OUT:
		var along := {"reach": 0.0, "band_from": -1.0, "band_to": -1.0}
		var d := 0.0
		while d <= RING_REACH:
			var spot: Vector2 = mark + WAYS_OUT[way] * d
			t.player.global_position = spot
			if sword._reaches(t.player.hurtBox):
				along.reach = d
			var cell := cell_at(ring, spot)
			if cell != Cell.INSIDE and along.band_from < 0.0:
				along.band_from = d
			if cell == Cell.OUTSIDE and along.band_to < 0.0:
				along.band_to = d
			d += 0.5
		gaps.ways[way] = along
	t.player.global_position = home
	return gaps
