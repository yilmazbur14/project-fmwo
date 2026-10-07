extends RefCounted

# Every number of beast Bixby's Flyby (BixbyBeastFlyby) that depends on how it is drawn or where it runs: the line he
# crosses on, where each pass's fire can fall and the safe column it leaves at the far edge, and the placeholder until
# his pass pose is drawn. Each pass's fire (BixbyFlybyFireScript) works out its projection, its curtain, the floor it
# sets burning and its hits from the spans here, so what burns is always exactly what was lit up first. Screen px
# unless a number says texels; a span is Vector2(lo, hi) in screen x, empty once lo >= hi.
#
# THE ART SWITCHES IN ON ITS OWN: his pass pose once its sheet is in and its contract.json's numbers are copied below
# (final_flyby), the curtain once its sheet is in (final_curtain). Shipping approved art IS wiring it, and nothing may
# ship into Assets/ before the user approves.

const BixbyBeastArtLayout := preload("res://Scripts/BixbyBeastArtLayout.gd")
const InfernoLayout := preload("res://Scripts/BixbyInfernoArtLayout.gd")

const SCALE := 3.0
const BREATH_ID := &"bixby_flyby_breath"
const FIRE_ID := &"bixby_flyby_fire"

# The floor the fire can reach, inside the arena walls, and the screen.
const FLOOR := InfernoLayout.INFERNO_AREA
const VIEW := Rect2(0, 0, 1920, 1080)

#ON A PASS
# His anchor texel (96, 151) crosses at this y, which puts his mouths at the top rope and his top off the screen: none
# of him hangs over the floor ahead of the fire. His floor point is the rope line, as on the perch (it must be), so he
# sorts behind everyone on the mat.
const PASS_ANCHOR_Y := 300.0
const PASS_SORT_Y := 114.0
# The fire's layers: the floor under everyone and over the mat; the curtain falling from his mouths over him; the safe
# column's rim over him too, as the Inferno's markers are, so the edge is never hidden. All under the player, who is
# never above y 145.5.
const FLOOR_LAYER_Y := InfernoLayout.FLOOR_LAYER_Y
const CURTAIN_SORT_Y := 114.5
const RIM_SORT_Y := InfernoLayout.MARKER_LAYER_Y
# The texel row of his frames that lies on the ring floor's top edge (y 105) with his anchor on PASS_ANCHOR_Y.
const FLOOR_ROW := 86
# Off the top of the screen, his feet are this high: his whole sprite above it. Off a side, his whole drawn box is this
# far clear of it.
const OFF_TOP_FEET_Y := -48.0
const OFF_SIDE_MARGIN := 40.0

#THE CURTAIN: the fire falling at the front, as wide as it hurts
const CURTAIN_WIDTH_TEXELS := 32.0
const CURTAIN_WIDTH := CURTAIN_WIDTH_TEXELS * SCALE

#HIS PASS POSE (BixbyBeastArtLayout.FLYBY_SHEET)
# From the art pass's contract.json (art_source/bixby_flyby/approval, 2026-09-29), played once the sheet ships: the lead
# exit (the fire's front column, the same column on every frame), each breath frame's exits (the lead one first), how
# far anything above FLOOR_ROW leads the lead exit, and how far his drawn box trails behind it, px.
const USE_FINAL_FLYBY := true
const FINAL_LEAD_EXIT := Vector2(179, 84)
const FINAL_EXITS := {
	4: [Vector2(179, 84), Vector2(166, 84), Vector2(153, 84)],
	5: [Vector2(179, 83), Vector2(166, 83), Vector2(153, 83)],
	6: [Vector2(179, 82), Vector2(166, 82), Vector2(153, 82)],
	7: [Vector2(179, 83), Vector2(166, 83), Vector2(153, 83)],
}
const FINAL_LEAD_PX := 33.0
const FINAL_TRAIL_PX := 495.0
# The placeholder is the fly frames: the front falls from the last column of their drawn box (bixby_beast_fly.png's
# columns 2 to 189), which nothing of him leads.
const PLACEHOLDER_EXIT := Vector2(189, 86)
const PLACEHOLDER_LEAD_PX := 0.0
const PLACEHOLDER_TRAIL_PX := 564.0

#THE CURTAIN'S ART (optional): frames of 32x48 texels, seamless stacked, a loop, the leading edge on column 31, drawn
# flying right and mirrored flying left. Until it is in, a gradient down from his mouths, pulsing.
const USE_FINAL_CURTAIN := true
const CURTAIN_SHEET := "res://Assets/Characters/Bixby/bixby_flyby_curtain.png"
const CURTAIN := {frame = Vector2(32, 48), frames = 4, frame_time = 0.06}
const PLACEHOLDER_CURTAIN := {top = Color(1, 0.95, 0.6, 0.95), bottom = Color(1, 0.42, 0.08, 0.6), pulse = 0.1, rate = 9.0}

# The safe column is bare mat with a gold rim down its edge: faint with the faint projection, full from the warning
# until the pass's fire stops hurting, then faded out.
const RIM := {width = 6.0, colour = Color(1, 0.85, 0.35), faint_alpha = 0.45, fade_time = 0.15}

#FAIRNESS (invariants): the player's walk (PlayerScript.SPEED), half their hurtbox's width, their i-frames, a dash's
# reach and the time it takes out of a walk (its frames and its landing beat); the reaction a read is given, what a
# dash back through the front has to land short of, the lead on foot a projection leaves, the room in the column past a
# body, and the most of the ring the column may take; how long before the front a walk into a column has to get there,
# the slack left a caught player who goes on, and the fewest physics frames the curtain has to cover a spot for.
const PLAYER_WALK := 600.0
const PLAYER_HALF_WIDTH := 18.0
const PLAYER_IFRAMES := 1.0
const DASH_DISTANCE := 250.0
const DASH_SPENT := 8.0 / 60.0
const REACTION := 0.25
const DASH_SLACK := 40.0
const LEAD_MIN := 150.0
const SAFE_ROOM_MIN := 120.0
const SAFE_SHARE_MAX := 0.25
# 0.15 s, 0.4 until the user asked for a faster Flyby (2026-10-04): the crossing is a whole ring's walk, so its length
# comes out of this spare. 0.15 s still covers a first-timer's slow reaction (0.25 s and two deviations of 0.05) with
# the experienced-player model's 25 px of margin.
const CROSS_SPARE := 0.15
const CAUGHT_SLACK := 0.02
const CURTAIN_STEPS_MIN := 3


static func final_flyby() -> bool:
	return USE_FINAL_FLYBY and FINAL_LEAD_EXIT.x >= 0.0 and ResourceLoader.exists(BixbyBeastArtLayout.FLYBY_SHEET)


static func final_curtain() -> bool:
	return USE_FINAL_CURTAIN and ResourceLoader.exists(CURTAIN_SHEET)


static func lead_exit() -> Vector2:
	return FINAL_LEAD_EXIT if final_flyby() else PLACEHOLDER_EXIT


static func lead_px() -> float:
	return FINAL_LEAD_PX if final_flyby() else PLACEHOLDER_LEAD_PX


static func trail_px() -> float:
	return FINAL_TRAIL_PX if final_flyby() else PLACEHOLDER_TRAIL_PX


# From his anchor to the fire's front, px, flying `dir` (1 left to right, -1 right to left). The lead exit is the
# front's own column, drawn, so the front is that column's far side; he is mirrored about the anchor's column flying
# left, which keeps it the far side.
static func exit_offset(dir: float) -> float:
	return (lead_exit().x + 1.0 - BixbyBeastArtLayout.ANCHOR.x) * SCALE * dir


# The y the lead exit crosses at on a pass, which the curtain hangs from.
static func exit_y() -> float:
	return PASS_ANCHOR_Y + (lead_exit().y - BixbyBeastArtLayout.ANCHOR.y) * SCALE


# The rope a pass flies in over, and the one it flies toward.
static func entry_x(dir: float) -> float:
	return FLOOR.position.x if dir > 0.0 else FLOOR.end.x


static func far_x(dir: float) -> float:
	return FLOOR.end.x if dir > 0.0 else FLOOR.position.x


# The safe column's inner edge, `width` in from the far rope.
static func safe_edge(dir: float, width: float) -> float:
	return far_x(dir) - dir * width


# What a pass can set burning, and the column it leaves.
static func lightable(dir: float, width: float) -> Vector2:
	return ordered(entry_x(dir), safe_edge(dir, width))


static func safe_span(dir: float, width: float) -> Vector2:
	return ordered(safe_edge(dir, width), far_x(dir))


# How long the front takes from the entry rope to the column's edge.
static func sweep_time(width: float, speed: float) -> float:
	return (FLOOR.size.x - width) / speed


# Where his lead exit waits for a pass to fly in: `lead` seconds of flight short of the entry rope.
static func start_mouth_x(dir: float, speed: float, lead: float) -> float:
	return entry_x(dir) - dir * speed * lead


# Where a pass's exit leaves his lead exit: his whole drawn box OFF_SIDE_MARGIN past the far side of the screen.
static func off_mouth_x(dir: float) -> float:
	if dir > 0.0:
		return VIEW.end.x + OFF_SIDE_MARGIN + trail_px()
	return VIEW.position.x - OFF_SIDE_MARGIN - trail_px()


static func ordered(a: float, b: float) -> Vector2:
	return Vector2(minf(a, b), maxf(a, b))


static func span_empty(span: Vector2) -> bool:
	return span.x >= span.y


# Whether `rect` is in `span` anywhere on the floor. Strictly in x: a box flush with a span's edge is clear of it.
static func span_touches(rect: Rect2, span: Vector2) -> bool:
	return not span_empty(span) and rect.position.x < span.y and rect.end.x > span.x \
		and rect.position.y < FLOOR.end.y and rect.end.y > FLOOR.position.y


# The walk from a player standing at `from_x` into the column a pass flying `dir` leaves, their hurtbox just inside it.
static func walk_to_column(from_x: float, dir: float, width: float) -> float:
	return absf(safe_edge(dir, width) + dir * PLAYER_HALF_WIDTH - from_x)


# How long before the front reaches the column a player gets into it, walking `distance` from the reaction to a
# projection up for `telegraph`.
static func arrival_spare(telegraph: float, distance: float, sm: Node) -> float:
	return telegraph + sweep_time(sm.flyby_safe_width, sm.flyby_speed) - REACTION - distance / PLAYER_WALK


# The fire sweeps faster than a walk, so each projection is long enough to walk to its column first, CROSS_SPARE ahead
# of the front: pass 0's from the worst start its side rule leaves (A), the crossing's from the far rope (B). A spot
# burns for less than the i-frames, so a player standing still is hit once a pass, and one caught mid-run who keeps
# going, on foot or with a dash, is past the fire by the time their i-frames end (C). The band burning behind the front
# is wider than a dash, a body and the slack, so a dash back through the front lands in fire; the curtain is inside it,
# and covers every spot for CURTAIN_STEPS_MIN physics frames at least, so it can't step over a hurtbox (D). Every
# projection leaves a lead on foot after the reaction, and holds its warning and his flight in; the column holds a body
# with room to spare and is under a quarter of the ring; he waits to fly in off the screen, his exit never turns back,
# and he sorts on the rope line.
static func invariants(sm: Node) -> Array[String]:
	var broken: Array[String] = []
	var speed: float = sm.flyby_speed
	var burn: float = sm.flyby_burn_time
	var width: float = sm.flyby_safe_width
	var band := speed * burn
	var worst_start := FLOOR.get_center().x if sm.flyby_start_side == &"away" else entry_x(1.0) + PLAYER_HALF_WIDTH
	var first := arrival_spare(sm.flyby_telegraph_time, walk_to_column(worst_start, 1.0, width), sm)
	if first < CROSS_SPARE - 0.0001:
		broken.append("A: pass 0's walk to its column arrives %.2f s before the front, under %.2f" % [first, CROSS_SPARE])
	var from_rope := walk_to_column(far_x(1.0) - PLAYER_HALF_WIDTH, -1.0, width)
	var crossing := arrival_spare(sm.flyby_return_telegraph_time, from_rope, sm)
	if crossing < CROSS_SPARE - 0.0001:
		broken.append("B: the crossing from the rope arrives %.2f s before the front, under %.2f" % [crossing, CROSS_SPARE])
	if speed > PLAYER_WALK:
		var going_on := PLAYER_IFRAMES - (DASH_DISTANCE + PLAYER_WALK * (PLAYER_IFRAMES - DASH_SPENT)) / speed - CAUGHT_SLACK
		if burn > going_on + 0.0001:
			broken.append("C: flyby_burn_time %.2f is over the %.3f s a caught player going on is safe with" % [burn, going_on])
	if CURTAIN_WIDTH < CURTAIN_STEPS_MIN * speed / Engine.physics_ticks_per_second - 0.0001:
		broken.append("D: the curtain %.0f px covers a spot for under %d frames at %.0f px/s" % [CURTAIN_WIDTH, CURTAIN_STEPS_MIN, speed])
	if burn >= PLAYER_IFRAMES:
		broken.append("flyby_burn_time %.2f is not under the %.1f s i-frames" % [burn, PLAYER_IFRAMES])
	if band < DASH_DISTANCE + 2.0 * PLAYER_HALF_WIDTH + DASH_SLACK - 0.0001:
		broken.append("the burning band %.0f px is under a dash, a body and the slack" % band)
	if CURTAIN_WIDTH >= band:
		broken.append("the curtain %.0f px is not inside the burning band %.0f px" % [CURTAIN_WIDTH, band])
	for telegraph: float in [sm.flyby_telegraph_time, sm.flyby_return_telegraph_time]:
		if (telegraph - REACTION) * PLAYER_WALK < LEAD_MIN - 0.0001:
			broken.append("a %.2f s projection leaves under %.0f px of lead after the reaction" % [telegraph, LEAD_MIN])
		if sm.flyby_warn_time >= telegraph:
			broken.append("flyby_warn_time %.2f is not under the %.2f s projection" % [sm.flyby_warn_time, telegraph])
		if sm.flyby_entry_lead > telegraph + 0.0001:
			broken.append("flyby_entry_lead %.2f is over the %.2f s projection" % [sm.flyby_entry_lead, telegraph])
	if width < 2.0 * PLAYER_HALF_WIDTH + SAFE_ROOM_MIN - 0.0001 or width > SAFE_SHARE_MAX * FLOOR.size.x + 0.0001:
		broken.append("flyby_safe_width %.0f is outside %.0f to %.0f" % [width, 2.0 * PLAYER_HALF_WIDTH + SAFE_ROOM_MIN, SAFE_SHARE_MAX * FLOOR.size.x])
	if sm.flyby_entry_lead * speed < FLOOR.position.x + lead_px() + OFF_SIDE_MARGIN - 0.0001:
		broken.append("he is still on the screen as he waits to fly in")
	if absf(off_mouth_x(1.0) - safe_edge(1.0, width)) < speed * sm.flyby_exit_time / 2.0 - 0.0001:
		broken.append("his exit would turn back before it leaves the screen")
	if not is_equal_approx(PASS_SORT_Y, sm.ROPES.position.y):
		broken.append("PASS_SORT_Y %.1f is not the rope line %.1f" % [PASS_SORT_Y, sm.ROPES.position.y])
	if sm.flyby_rise_time <= 0.0 or sm.flyby_return_time <= 0.0:
		broken.append("flyby_rise_time and flyby_return_time have to be over 0")
	return broken


static func assert_invariants(sm: Node) -> void:
	var broken := invariants(sm)
	assert(broken.is_empty(), "BixbyFlybyLayout: %s" % [broken])
