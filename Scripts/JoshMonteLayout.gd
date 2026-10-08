extends RefCounted

# Josh's Portal Monte (JoshCardsPortalMonte; the user, 2026-09-29: "he dives into a portal and bursts out of one of three
# small portals around you. The red one is real, so parry it. The yellow ones are fakes, so don't, same as Carter's
# clones"): every number that depends on how its pieces are drawn or where they stand, so the art only needs this file.
# Texel numbers are on a frame, origin top-left; world numbers are px. Pivots are in Josh's corner convention: a
# sprite's offset is frame / 2 - pivot.
#
# THE ART SWITCHES IN ON ITS OWN. Each piece plays its final sheets once every sheet it needs is in and imported
# (final_small_portal, final_slash, final_dive, and the scatter's), and its placeholder until then. Nothing ships into
# Assets/ before the user approves, so shipping the approved sheets is wiring them. The numbers are the art pass's
# (art_source/josh_hands/approval_monte/contract.json, 2026-09-29); the totals, the pivots' meaning, the slash's contact
# frame and the file names are the gameplay's.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshHandsLayout := preload("res://Scripts/JoshHandsLayout.gd")

const SCALE := 3.0

#THE SMALL GATES (JoshPortal, kind small)
# Redrawn small in the big gate's language, upright and facing the camera, never mirrored, in neutral colours only:
# never red or yellow, which are the marks'. Its pivot is the opening's centre and the frame's, FLOOR_DROP texels over
# the floor point it stands and sorts on; DRAWN is what any frame of either layer draws round the pivot - the open's and
# the burst's flares reach 26 texels, past the loop's 45x42 (47x46 with its glow), and a keep-out has to hold for them
# too. Back and an additive glow, synced: open (from the dealt card flipping open), a seamless loop, burst (the flare
# as a figure comes out, back into the loop) and close, which ends empty.
const SMALL_PORTAL_DIR := "res://Assets/Characters/Josh/Portals/"
const SMALL_PORTAL := {frame = Vector2(56, 56), pivot = Vector2(28, 28), opening = 9.5, rim = 12.5, ring = 20.0}
const SMALL_PORTAL_DRAWN := Rect2(-26, -26, 52, 52)
const SMALL_FLOOR_DROP := 22.0
const SMALL_PORTAL_SEQUENCES := {
	&"open": [0.06, 0.07, 0.08, 0.09],
	&"loop": [0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10],
	&"burst": [0.05, 0.06, 0.07],
	&"close": [0.05, 0.05, 0.05, 0.05],
}
const SMALL_PORTAL_REQUIRED: Array[StringName] = [&"open", &"loop", &"burst", &"close"]
const SMALL_PORTAL_LAYERS: Array[StringName] = [&"back", &"glow"]
# The placeholder: the big gate's, at the small radius, in the neutral colours.
const PLACEHOLDER_SMALL_PORTAL := {points = 24, grown_from = 0.05, flecks = 6, fleck_size = Vector2(2, 3), fleck_orbit = 17.0,
	fleck_turns = 0.5, flare_time = 0.12, flare_glow = 0.5}
const SMALL_COLOURS := {card = Color(1.0, 0.95, 0.85), edge = Color("#5E5A66"), vortex = Color("#1C1A24"),
	rim = Color("#C9C3B6"), glow = Color("#3E3A4E")}

#THE DIVE AND THE EMERGE (his dive and emerge anims are in JoshArtLayout)
# He dives up into a big gate: his floor point slides under it, DIVE_UNDER px below its opening, while his height rises
# until his middle on the dive's airborne frames (DIVE_CENTRE, texels in its cell) meets the opening - not his feet -
# and over the dive's last DIVE_SHRINK_TIME he shrinks to DIVE_SHRINK about it and fades out. He comes back out the
# same way: the drawn emerge's first frame has his middle on EMERGE_CENTRE_ROW of its cell, up in the gate, and he is
# on the floor from its EMERGE_LANDING_STEP; until it is in, the dive backwards, on the floor as it ends.
# DIVE_UNDER is where he comes back down, so it is measured off the art: standing there - through his Recover and the
# Hand Slam after it, his tallest pose the hit flinch, 78 texels over his feet - his head clears the resting hand's
# lowest finger (38 texels under its pivot, 170 px under the gate; 39 with its glow) by 7 px.
const DIVE_UNDER := 525.0
const DIVE_CENTRE := Vector2(42, 41)
const EMERGE_CENTRE_ROW := 24.0
const EMERGE_LANDING_STEP := 2
const DIVE_SHRINK := 0.3
const DIVE_SHRINK_TIME := 0.15

#THE BURST-OUT SLASH (JoshMonteFigure): the real Josh, the fakes and a punish alike
# Drawn facing right with the blade reaching right, its feet on the frame's centre column so flip_h mirrors about
# them. Frames 0-1 are the dash, 2 the contact, 3 the follow-through a figure that struck holds before it scatters.
# `contact` is where its cut lands, texels from its feet: it lunges to put that on the player's hurtbox centre, not its
# feet (which would put the blade past them); `centre` is its middle, texels from its feet. Until it is in, the throw's
# release and follow-through, the cards leaving its hand (JoshArtLayout.HAND_THROW) as its cut.
const SLASH := {texture = "res://Assets/Characters/Josh/josh_monte_slash.png", frame = Vector2(128, 80),
	feet = Vector2(64, 79), times = [0.08, 0.10, 0.10, 0.16], dash_frames = [0, 1], contact_frame = 2, follow_frame = 3,
	contact = Vector2(47.8, -23.1), centre = Vector2(4, -32)}
const PLACEHOLDER_SLASH := {texture = JoshArtLayout.THROW_SHEET, frame = Vector2(80, 80), feet = Vector2(40, 79),
	steps = [1, 2, 2, 3], times = [0.08, 0.10, 0.10, 0.16], dash_frames = [0, 1], contact_frame = 2, follow_frame = 3,
	contact = Vector2(32, -34), centre = Vector2(0, -40)}
# It sorts this far in front of its gate, whose floor point it bursts out on, so it is drawn over it.
const FIGURE_SORT_BUMP := 1.0
# A fake bursting into cards at the contact instant (optional; the fan of cards on its feet until then), on the figure's
# centre.
const SCATTER := {texture = "res://Assets/Characters/Josh/Cards/josh_monte_scatter.png", frame = Vector2(96, 96),
	pivot = Vector2(48, 48), frame_times = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]}

#THE MARKS, over each small gate: the only thing that tells them apart
# Their tip stands MARK_OVER_PIVOT px over the gate's pivot (6 px over its loop's top). Red is the game's own parry badge
# (ParryTell, its strong look); a fake wears Carter's pale X (USE_FEINT_X), stepped through ignite, peak and a hold that
# never pulses (his clones' rule: a tell that flickers gets re-read instead of acted on), with the yellow ring standing
# in until the X is imported or with it off; a punish is a hot white glow that beats, and no badge. Each clears at its
# contact and is gone in MARK_OUT. With FAKES_ALIKE a fake's figure is the real one's to the frame until its contact;
# off, a fake is drawn tinted as Wild Cards' clones. Both are the art pass's picks, waiting on the user.
const MARK_OVER_PIVOT := 69.0
const USE_FEINT_X := true
const FEINT_MARK := {texture = "res://Assets/Characters/Carter/Demon/demon_feint.png", hframes = 4,
	frame_size = Vector2(24, 24), pivot = Vector2(12, 12), scale = 3.0, steps = {ignite = 0, peak = 1, hold = 2, fade = 3},
	ignite_time = 0.05, peak_time = 0.04}
const FEINT_RING := {radius = 46.0, width = 11.0, points = 20, color = Color(1.0, 0.85, 0.15)}
const FAKES_ALIKE := true
const FAKE_TINT := JoshArtLayout.WILD_CLONE_TINT
const PUNISH := {tint = Color(2.2, 2.0, 1.8), glow = Color(1.0, 1.0, 1.0, 0.55), glow_radius = 60.0, points = 24,
	beat = [0.82, 1.18], beat_time = 0.07}
const MARK_OUT := 0.05
# What any of the three marks covers round its tip: the badge (JoshArtLayout.TELL_BADGE), the X and the ring.
const MARK_RECT := Rect2(-52, -104, 104, 104)

#THE DEAL: a card flicked from the nearer hand to each spot, up an arc DEAL_ARC px high at its middle
const DEAL_ARC := 90.0

#THE WORD a bitten fake puts up, as Carter's
# On his spot unless that would cover one of the round's gates or its mark - it is up 1.2 s, over the next burst or two
# - else on the first of WORD_MOVES off it that is WORD_CLEARANCE clear of them all, a move's x turned away from the gate
# that was bitten; failing every one, the least covered. `box` is the word as drawn at full size, outline included
# ("FEINT!" at 92 draws 258x63 inside its outline). Every move is in view and clear of the HUD.
const WORD := {centre = Vector2(960, 300), time = 0.9, font_size = 92, color = Color(1.0, 0.36, 0.3), outline = 10,
	from_scale = 0.7, to_scale = 1.0, grow_time = 0.16, box = Vector2(300, 100)}
const WORD_MOVES: Array[Vector2] = [Vector2(0, 0), Vector2(710, 0), Vector2(0, 580), Vector2(-710, 0), Vector2(710, 340),
	Vector2(-710, 340)]
const WORD_CLEARANCE := 12.0

#WHERE THE SMALL GATES OPEN (place)
# Three round the locked player. Each is at least monte_min_radius from them, its floor point inside the ropes by
# PLACE_ROPE_MARGIN, its drawn rect and its mark inside the view by PLACE_VIEW_MARGIN and HUD_CLEARANCE clear of the
# HUD, never on a hand resting at a big gate (RESTING_HAND, what hover and its glow draw, measured off the shipped
# sheets), and PLACE_MIN_GAP from the others. A gate and its mark stand 254 px tall, so round the ring's middle a mark
# above the player lands in the boss bar's block, and in a corner there is no 120 degrees of floor: the shapes are
# tried in PLACE_SHAPES' order - the ring, 120 degrees apart, then a fan facing the ring's middle, then a narrow fan -
# each at the state machine's monte_radius and then the PLACE_RADIUS_STEPS off it, the ring's turn from a random one
# round the circle and a fan's from the ring's middle outward, PLACE_TURN_STEP apart; and when no shape fits, any three
# spots that do (a scatter). Whatever is also clear of the big gates themselves comes first - a red badge over his wine
# vortex can't be read - but the floor is too tight to insist on it everywhere; and before even that, a set whose marks
# each stand clear of the other two gates (marks_owned), whenever one fits anywhere. A re-deal turns at least
# REDEAL_MIN_TURN off the last round's shape whenever one fits (a ring repeats every 120 degrees). Failing all of it,
# the fan drawn in along its bearings until it fits the ropes and the view (the plan's last resort).
const PLACE_TURNS := 24
const PLACE_TURN_STEP := 15.0
const PLACE_SHAPES := {&"ring": [0.0, 120.0, 240.0], &"fan": [-60.0, 0.0, 60.0], &"narrow": [-30.0, 0.0, 30.0]}
const PLACE_SHAPE_ORDER: Array[StringName] = [&"ring", &"fan", &"narrow"]
const PLACE_RADIUS_STEPS: Array[float] = [0.0, -40.0, -80.0, 80.0, 160.0]
const PLACE_SCATTER_STEP := 40.0
const PLACE_ROPE_MARGIN := 40.0
const PLACE_VIEW_MARGIN := 8.0
const PLACE_MIN_GAP := 150.0
const REDEAL_MIN_TURN := 40.0
const FAN_RADIUS := 240.0
# Within this of the ring's middle it has no bearing to face: the fans face down, away from the bars.
const FAN_MIDDLE_RADIUS := 60.0
const RESTING_HAND_TEXELS := Rect2(-41, -41, 80, 80)

#FAIRNESS (invariants): Carter's floor for reading red from yellow, and the parry window (PlayerDefense's)
const READ_FLOOR := 0.36
const PARRY_WINDOW := 0.24
const MIN_RADIUS_FLOOR := 220.0


#THE SMALL GATES' SHEETS

static func small_portal_sheet(sequence: StringName, layer: StringName) -> String:
	return SMALL_PORTAL_DIR + "josh_small_portal_%s_%s.png" % [sequence, layer]


static func final_small_portal() -> bool:
	for sequence in SMALL_PORTAL_REQUIRED:
		for layer in SMALL_PORTAL_LAYERS:
			if not ResourceLoader.exists(small_portal_sheet(sequence, layer)):
				return false
	return true


# Its pivot, px over the floor point.
static func small_drop() -> float:
	return SMALL_FLOOR_DROP * SCALE


#THE FIGURE AND HIM

static func final_slash() -> bool:
	return ResourceLoader.exists(SLASH.texture)


static func slash() -> Dictionary:
	return SLASH if final_slash() else PLACEHOLDER_SLASH


# Where the slash's cut lands, px from its feet, facing the way it does: its feet go this far short of the player's
# hurtbox centre.
static func contact_offset(flipped: bool) -> Vector2:
	var cut: Vector2 = slash().contact * SCALE
	return Vector2(-cut.x if flipped else cut.x, cut.y)


# The figure's middle, px from its feet, facing the way it does: where the scatter is centred.
static func figure_centre(flipped: bool) -> Vector2:
	var middle: Vector2 = slash().centre * SCALE
	return Vector2(-middle.x if flipped else middle.x, middle.y)


# How long a figure that struck stays before it scatters: its cut (the contact frame) and then its follow-through,
# each for its own time.
static func follow_time() -> float:
	var spec := slash()
	return spec.times[spec.contact_frame] + spec.times[spec.follow_frame]


static func final_dive() -> bool:
	var dive: Dictionary = JoshArtLayout.FINAL_ANIMS.get(&"dive", {})
	return not dive.is_empty() and ResourceLoader.exists(dive.sheet)


# Whether his drawn emerge plays (it is in, and switched on), rather than the dive backwards.
static func final_emerge() -> bool:
	return JoshArtLayout.anim(&"emerge") == JoshArtLayout.FINAL_ANIMS.get(&"emerge")


# His middle as he dives, px from his feet, facing the way he does: what goes up to meet the gate's opening.
static func dive_centre(flipped: bool) -> Vector2:
	return JoshArtLayout.local(DIVE_CENTRE, flipped)


# How far over his feet his middle is on the emerge's first frame, px, and how far into it he is on the floor, seconds:
# the drawn emerge's, or the dive's backwards.
static func emerge_start_lift() -> float:
	if final_emerge():
		return (JoshArtLayout.ANCHOR.y - EMERGE_CENTRE_ROW) * SCALE
	return -dive_centre(false).y


static func emerge_landing(emerge_time: float) -> float:
	if not final_emerge():
		return emerge_time
	var times: Array = JoshArtLayout.anim(&"emerge").times
	var total := 0.0
	for i in EMERGE_LANDING_STEP:
		total += times[mini(i, times.size() - 1)]
	return total


# The scatter's sheet in the fan of cards' shape (JoshArtLayout.FINAL_CARD_BURST), and whether it is centred on the
# figure (its own) or stood on its feet (the fan).
static func scatter() -> Dictionary:
	if not ResourceLoader.exists(SCATTER.texture):
		return JoshArtLayout.FINAL_CARD_BURST.merged({centred = false})
	return {texture = SCATTER.texture, hframes = SCATTER.frame_times.size(), frame_size = SCATTER.frame, pivot = SCATTER.pivot,
		scale = SCALE, frame_times = SCATTER.frame_times, centred = true}


# The fake's X once it is imported and picked; empty for the ring.
static func feint_mark() -> Dictionary:
	return FEINT_MARK if USE_FEINT_X and ResourceLoader.exists(FEINT_MARK.texture) else {}


#WHERE THINGS STAND

# The tip the marks over the small gate standing on `floor_point` stand on.
static func mark_tip(floor_point: Vector2) -> Vector2:
	return floor_point - Vector2(0.0, small_drop() + MARK_OVER_PIVOT)


# What the small gate standing on `floor_point` draws, and what any of its marks does.
static func gate_body(floor_point: Vector2) -> Rect2:
	var gate := Rect2(SMALL_PORTAL_DRAWN.position * SCALE, SMALL_PORTAL_DRAWN.size * SCALE)
	gate.position += floor_point - Vector2(0.0, small_drop())
	return gate


static func mark_rect(floor_point: Vector2) -> Rect2:
	return Rect2(mark_tip(floor_point) + MARK_RECT.position, MARK_RECT.size)


# What the small gate standing on `floor_point` and its mark cover.
static func gate_rect(floor_point: Vector2) -> Rect2:
	return gate_body(floor_point).merge(mark_rect(floor_point))


# Whether each of `spots`' marks stands clear of the other gates: a mark over the gate above it reads as that one's.
static func marks_owned(spots: Array[Vector2]) -> bool:
	for a in spots.size():
		if not _owns_with(spots[a], spots.slice(a + 1)):
			return false
	return true


# Whether a gate on `spot` and the gates on `others` are clear of each other's marks.
static func _owns_with(spot: Vector2, others: Array[Vector2]) -> bool:
	var mark := mark_rect(spot)
	var body := gate_body(spot)
	for other in others:
		if mark.intersects(gate_body(other)) or mark_rect(other).intersects(body):
			return false
	return true


# The hands resting at the big gates, as they are drawn: the right one's box, mirrored for the left.
static func resting_hands() -> Array[Rect2]:
	var box := Rect2(RESTING_HAND_TEXELS.position * SCALE, RESTING_HAND_TEXELS.size * SCALE)
	var hands: Array[Rect2] = []
	for side in JoshHandsLayout.SIDES:
		var drawn := box if side == &"right" else Rect2(-box.end.x, box.position.y, box.size.x, box.size.y)
		hands.append(Rect2(JoshHandsLayout.rest_point(side) + drawn.position, drawn.size))
	return hands


# The big gates as they are drawn.
static func big_gates() -> Array[Rect2]:
	var half: Vector2 = JoshHandsLayout.PORTAL.frame * JoshHandsLayout.SCALE / 2.0
	var gates: Array[Rect2] = []
	for side in JoshHandsLayout.SIDES:
		gates.append(Rect2(JoshHandsLayout.PORTAL_POINTS[side] - half, half * 2.0))
	return gates


# Whether a small gate on `spot` can be read from the player at `player_pos`: far enough, on the floor, in view, clear
# of the HUD and off the resting hands.
static func gate_fits(spot: Vector2, player_pos: Vector2, min_radius: float, ropes: Rect2) -> bool:
	if spot.distance_to(player_pos) < min_radius - 0.5:
		return false
	if not ropes.grow(-PLACE_ROPE_MARGIN).has_point(spot):
		return false
	var rect := gate_rect(spot)
	if not JoshArtLayout.VIEW_RECT.grow(-PLACE_VIEW_MARGIN).encloses(rect):
		return false
	for block in JoshArtLayout.HUD_KEEP_OUT:
		if block.grow(JoshArtLayout.HUD_CLEARANCE).intersects(rect):
			return false
	return resting_hands().all(func(hand: Rect2) -> bool: return not hand.intersects(rect))


# Whether a small gate on `spot` and its mark are clear of the big gates themselves too.
static func clear_of_stage(spot: Vector2) -> bool:
	var rect := gate_rect(spot)
	return big_gates().all(func(gate: Rect2) -> bool: return not gate.intersects(rect))


# What the word covers centred on `centre`, at full size.
static func word_box(centre: Vector2) -> Rect2:
	return Rect2(centre - WORD.box / 2.0, WORD.box)


# Where the word goes when the fake on `spots[bitten]` is bitten (WORD_MOVES), and each of the moves it can take.
static func word_centre(spots: Array[Vector2], bitten: int) -> Vector2:
	var best: Vector2 = WORD.centre
	var least := INF
	for centre in word_spots(spots, bitten):
		var covered := word_cover(centre, spots)
		if covered <= 0.0:
			return centre
		if covered < least:
			least = covered
			best = centre
	return best


static func word_spots(spots: Array[Vector2], bitten: int) -> Array[Vector2]:
	var away := -1.0 if bitten >= 0 and bitten < spots.size() and spots[bitten].x > WORD.centre.x else 1.0
	var centres: Array[Vector2] = []
	for move in WORD_MOVES:
		centres.append(WORD.centre + Vector2(move.x * away, move.y))
	return centres


# How much of the gates on `spots` and their marks the word centred on `centre` covers, px squared, with its clearance.
static func word_cover(centre: Vector2, spots: Array[Vector2]) -> float:
	var box := word_box(centre).grow(WORD_CLEARANCE)
	var covered := 0.0
	for spot in spots:
		covered += box.intersection(gate_rect(spot)).get_area()
	return covered


# How far apart two turns of a ring are, degrees: it repeats every 120.
static func turn_gap(a: float, b: float) -> float:
	var d := fposmod(a - b, 120.0)
	return minf(d, 120.0 - d)


# Whether a shape at `turn` is turned far enough off the last round's placement (`prev`, empty for none) to be a
# re-deal: any other shape is, a ring by REDEAL_MIN_TURN on its 120 degrees, a fan by REDEAL_MIN_TURN.
static func turned_enough(shape: StringName, turn: float, prev: Dictionary) -> bool:
	if prev.is_empty() or prev.how != shape:
		return true
	if shape == &"ring":
		return turn_gap(turn, prev.turn) >= REDEAL_MIN_TURN - 0.001
	return absf(rad_to_deg(angle_difference(deg_to_rad(turn), deg_to_rad(prev.turn)))) >= REDEAL_MIN_TURN - 0.001


# Where the three small gates open round the player standing at `player_pos`: {spots, turn, how, clear, owned}. `how` is
# the shape (PLACE_SHAPES), &"scatter" or &"drawn_in"; `turn` the bearing, degrees, of a ring's first gate or a fan's
# middle one; `clear` whether they are clear of the big gates; `owned` whether every mark is clear of the other gates
# (marks_owned). A ring's turns start at `first_step` (a random one if -1); with a last round's placement (`prev`), only
# shapes turned enough off it (turned_enough) are tried first, then any. All of that is tried first for sets whose
# marks are owned, and only when none fits for any (`prefer_owned` off skips straight to that, for a test's before).
static func place(player_pos: Vector2, prev: Dictionary, radius: float, min_radius: float, ropes: Rect2, first_step := -1, prefer_owned := true) -> Dictionary:
	var first := first_step if first_step >= 0 else randi() % PLACE_TURNS
	var middle := ropes.get_center()
	var toward := 90.0 if player_pos.distance_to(middle) < FAN_MIDDLE_RADIUS else rad_to_deg((middle - player_pos).angle())
	var passes: Array[bool] = [false]
	if not prev.is_empty():
		passes = [true, false]
	var owning: Array[bool] = [false]
	if prefer_owned:
		owning = [true, false]
	for owned in owning:
		for clear in [true, false]:
			for redeal in passes:
				for shape in PLACE_SHAPE_ORDER:
					for step in PLACE_RADIUS_STEPS:
						for i in PLACE_TURNS:
							var turn := fposmod((first + i) * PLACE_TURN_STEP if shape == &"ring" else toward + _outward(i) * PLACE_TURN_STEP, 360.0)
							if redeal and not turned_enough(shape, turn, prev):
								continue
							var spots := shape_spots(player_pos, shape, turn, radius + step)
							if _fit(spots, player_pos, min_radius, ropes) and (not clear or spots.all(clear_of_stage)) and (not owned or marks_owned(spots)):
								return {spots = spots, turn = turn, how = shape, clear = clear, owned = marks_owned(spots)}
			var scattered := _scatter(player_pos, toward, radius, min_radius, ropes, clear, owned)
			if scattered.size() == 3:
				return {spots = scattered, turn = toward, how = &"scatter", clear = clear, owned = marks_owned(scattered)}
	var bounds := fit_bounds(ropes)
	var drawn_in: Array[Vector2] = []
	for spread in PLACE_SHAPES[&"fan"]:
		drawn_in.append(_along(player_pos, Vector2.from_angle(deg_to_rad(toward + spread)), FAN_RADIUS, bounds))
	return {spots = drawn_in, turn = toward, how = &"drawn_in", clear = false, owned = marks_owned(drawn_in)}


# A shape's three floor points round `player_pos`, turned `turn` degrees, at `reach`.
static func shape_spots(player_pos: Vector2, shape: StringName, turn: float, reach: float) -> Array[Vector2]:
	var spots: Array[Vector2] = []
	for bearing in PLACE_SHAPES[shape]:
		spots.append((player_pos + Vector2.from_angle(deg_to_rad(turn + bearing)) * reach).round())
	return spots


# Any three spots that fit round `player_pos`, from monte_min_radius out to the farthest shape's reach, PLACE_TURN_STEP
# apart: the first the nearest toward the ring's middle, each next the one farthest from those already chosen. With
# `owned`, only spots clear of the chosen ones' marks, and each candidate in turn tried first until three are found.
# Fewer than three if they aren't there.
static func _scatter(player_pos: Vector2, toward: float, radius: float, min_radius: float, ropes: Rect2, clear: bool, owned := false) -> Array[Vector2]:
	var candidates: Array[Vector2] = []
	var reach := min_radius + PLACE_SCATTER_STEP / 2.0
	while reach <= radius + PLACE_RADIUS_STEPS.max() + 0.5:
		for i in PLACE_TURNS:
			var spot := (player_pos + Vector2.from_angle(deg_to_rad(toward + _outward(i) * PLACE_TURN_STEP)) * reach).round()
			if gate_fits(spot, player_pos, min_radius, ropes) and (not clear or clear_of_stage(spot)):
				candidates.append(spot)
		reach += PLACE_SCATTER_STEP
	var chosen: Array[Vector2] = []
	for first in (candidates.size() if owned else mini(candidates.size(), 1)):
		chosen = [candidates[first]]
		while chosen.size() < 3:
			var best := Vector2.INF
			var best_gap := -1.0
			for spot in candidates:
				var gap := INF
				for other in chosen:
					gap = minf(gap, spot.distance_to(other))
				if gap >= PLACE_MIN_GAP and gap > best_gap and (not owned or _owns_with(spot, chosen)):
					best = spot
					best_gap = gap
			if best == Vector2.INF:
				break
			chosen.append(best)
		if chosen.size() == 3:
			return chosen
	return chosen


# 0, 1, -1, 2, -2 ...: steps off the ring's middle, outward both ways.
static func _outward(i: int) -> int:
	return (i + 1) / 2 if i % 2 == 1 else -i / 2


# The floor points a small gate fits on with the ropes and the view alone (the drawn-in fallback's bounds).
static func fit_bounds(ropes: Rect2) -> Rect2:
	var local := gate_rect(Vector2.ZERO)
	var view: Rect2 = JoshArtLayout.VIEW_RECT.grow(-PLACE_VIEW_MARGIN)
	var inside: Rect2 = ropes.grow(-PLACE_ROPE_MARGIN)
	var top_left := Vector2(maxf(inside.position.x, view.position.x - local.position.x), maxf(inside.position.y, view.position.y - local.position.y))
	var bottom_right := Vector2(minf(inside.end.x, view.end.x - local.end.x), minf(inside.end.y, view.end.y - local.end.y))
	return Rect2(top_left, bottom_right - top_left)


static func _fit(spots: Array[Vector2], player_pos: Vector2, min_radius: float, ropes: Rect2) -> bool:
	for a in spots.size():
		if not gate_fits(spots[a], player_pos, min_radius, ropes):
			return false
		for b in range(a + 1, spots.size()):
			if spots[a].distance_to(spots[b]) < PLACE_MIN_GAP:
				return false
	return true


# Along `direction` from `from` by `reach`, shortened rather than clamped per axis so the gate still comes from its
# bearing (CarterRagingDemon._spawn_point).
static func _along(from: Vector2, direction: Vector2, reach: float, bounds: Rect2) -> Vector2:
	var inside := from.clamp(bounds.position, bounds.end)
	for axis in 2:
		if absf(direction[axis]) < 0.001:
			continue
		var edge: float = bounds.end[axis] if direction[axis] > 0.0 else bounds.position[axis]
		reach = minf(reach, (edge - inside[axis]) / direction[axis])
	return (inside + direction * maxf(reach, 0.0)).round()


#FAIRNESS

# Each mark is up long enough to tell red from yellow, the dash to its contact fits inside the parry window, only one
# mark is ever up (the next comes after the last has gone), and no gate opens close enough to the player to be melee.
static func invariants(sm: Node) -> Array[String]:
	var broken: Array[String] = []
	if sm.monte_show < READ_FLOOR - 0.0001:
		broken.append("monte_show (%.2f) is under the %.2f s it takes to read red from yellow" % [sm.monte_show, READ_FLOOR])
	if sm.monte_dash > PARRY_WINDOW + 0.0001:
		broken.append("monte_dash (%.2f) is longer than the parry window" % sm.monte_dash)
	if sm.monte_show + sm.monte_dash + MARK_OUT > sm.monte_cadence() + 0.0001:
		broken.append("two marks can be up at once: show + dash + the mark's fade is over the cadence")
	if sm.monte_min_radius < MIN_RADIUS_FLOOR - 0.0001:
		broken.append("monte_min_radius (%.0f) lets a gate open under %.0f px from the player" % [sm.monte_min_radius, MIN_RADIUS_FLOOR])
	return broken


static func assert_invariants(sm: Node) -> void:
	var broken := invariants(sm)
	assert(broken.is_empty(), "JoshMonteLayout: %s" % [broken])
