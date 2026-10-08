extends RefCounted

# Jordan's attack 4, Carter + Mason's circle (JordanComboCircle): every number it plays on, so a retune only needs this
# file. The user's own design and sketch (2026-09-28): Carter rings the player with a circle of his clones, and they
# fire his beams one after another round it, each through the middle, a lap round; Mason, held up on Jordan's
# strings ahead of the beams, drops poo bombs on the path the player has to run. Then both are left open.
# "Circle", never "ring": the ring is the arena's ropes (ring_origins, _keep_in_ring).
#
# THE CIRCLE is a floor-perspective ellipse (ry/rx = FLOOR_RATIO), as big as the fight's 2/3 view lets it be (the user,
# 2026-09-28: "the circle needs to be bigger for carter"). Its clones' drawn pixels, in every pose, keep 12 screen px
# inside the view and off the HUD's keep-outs and Jordan's mask and core, and the HUD's bottom-left corner is what holds
# a wide circle this flat. A taller one - clones let over the HUD's corners or Jordan's legs - is CLONE_RADII, CENTRE
# and CLONES here, then Carter's and Mason's spots, and jordan_circle tier=layout checks it against the keep-outs.
#
# ANGLES: a FLOOR angle is degrees clockwise from screen-right with the floor's y stretched back out (floor_angle); a
# ROUND angle is how far round the ellipse that is by its length, in degrees (round_of). The clones stand an equal
# length apart, and everything that goes round the circle - the sweep, the leads, Mason, his bombs - goes round in
# round angles, so the beams chase the player at one screen speed all the way round. A floor radius is in x px. Every
# point is a WORLD px under staging option B (world = screen x 1.5 + (-480, -6)); a soles point is where a player
# standing there has their soles, a puppet's point its feet, a clone's its feet.
#
# THE USER'S PICKS (2026-09-28, "defaults are fine"), kept as knobs: an even 8 s lap (LAP_TIME, or LAP_TIMES for a
# lap-by-lap pace), the clones as see-through pale-violet ghosts of the Carter twin (CLONE_TINT), and his beams at their
# real size; and on 2026-09-29, "lets half the attack time": half the three laps first built, at the same pace (FIRES).
# The tuning of 2026-10-04 (the god fight to the user's 9/10) took it to one lap, still at the same pace, and Mason's
# peaks closer (ZIG_STEP 18 to 15): the second half lap was the attack's quietest time, and the denser bombs are what
# keep a practised run honest. jordan_circle tier=bot still clears the lap with no hit at all.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")

const BEAM_ID := &"jordan_circle_beam"
const POO_ID := &"jordan_circle_poo"
const HINT := "KEEP RUNNING AROUND THE CIRCLE, AHEAD OF THE BEAMS!"

#THE CIRCLE
const SOLES_OVER_ORIGIN := 42.0
# Under Jordan, and the warp point.
const CENTRE := Vector2(960, 1003)
# The clones' feet. Their spacing along it stays about the first circle's (20 on 704 x 440). Flatter and wider means a
# band across the middle takes more of its height: at the top and bottom the player's lane outside a level beam is
# SOLES_RADII.y - 221 px deep (157 here; 191 on the first circle).
const CLONE_RADII := Vector2(980, 406)
const CLONES := 24
const FLOOR_RATIO := CLONE_RADII.y / CLONE_RADII.x
const CLONE_STEP := 360.0 / CLONES
# A pair either side of each axis.
const FIRST_ROUND := CLONE_STEP / 2.0
# Every beam runs from its clone's palms through here, the player's hurtbox height over the floor's centre, and on
# BEAM_PAST beyond the far side.
const BEAM_CENTRE := CENTRE - Vector2(0, 40)
const BEAM_PAST := 60.0
# See-through pale-violet ghosts of the Carter twin: nothing here is parryable, so never demon_clone, his parry read.
const CLONE_TINT := Color(0.80, 0.62, 1.0, 0.80)
# They form nearest Carter first, one FORM_STAGGER after another, and dissolve together at the end.
const FORM_TIME := 0.22
const FORM_STAGGER := 0.03
const DISSOLVE_TIME := 0.3
# The length of the ellipse's table of round angles.
const ROUND_SAMPLES := 3600

#THE PLAYER'S AREA
# The soles move inside this ellipse on CENTRE, just inside the clones' feet. The wall that holds them there is an
# ellipse of segments round the player's 36x81 collision box, centred WALL_RISE over CENTRE (the box's middle over the
# soles).
const SOLES_INSET := Vector2(44, 28)
const SOLES_RADII := CLONE_RADII - SOLES_INSET
const WALL_POINTS := 64
const WALL_RISE := 40.5
const WALL_RADII := SOLES_RADII + Vector2(18, WALL_RISE)

#THE SWEEP (seconds)
# The clones fire in turn, clockwise, a lap in LAP_TIME, so a lap's cadence is LAP_TIME / CLONES: FIRES in all, a lap
# (8 s of beams), so each clone fires once. The attack is shortened by firing fewer, never faster: the
# beams chase at one pace. Each charges CHARGING cadences first (three charging at once), its aim line lit for the last
# TELL_TIME; its head crosses in TRAVEL, harmless, then the band hurts for one cadence, the next one's taking over as it
# goes, and fades over FADE. LAP_TIMES, when it has entries, is each lap's own time (its last entry for any lap past it).
const LAP_TIME := 8.0
const LAP_TIMES: Array[float] = []
const FIRES := CLONES
const CHARGING := 3
const TELL_TIME := 0.30
const TRAVEL := 0.10
const FADE := 0.30
# The beam's body flowing down it; off holds its first frame, if the flow shimmers at the fight's 2/3.
const BEAM_FLOW := true

#THE BEATS (seconds)
const TELEPORT_TIME := 0.35
const FLASH_TO_FORM := 0.30
# From the circle closing on the player to the first clone's charge.
const LOOP_DELAY := 0.30
# The first run's hint stays up this long from the circle closing.
const HINT_TIME := 4.0

#THE PAIR (feet)
# Carter conducts from the view's top-left corner, over the circle's left end, on Jordan's left hand; Mason waits in the
# top-right corner on his right, flies the circle, and is yanked back down beside Carter at the end.
const CARTER_FEET := Vector2(-200, 600)
const MASON_REST := Vector2(2120, 600)
const MASON_LANDING := Vector2(60, 640)

#MASON IN THE AIR
# His node is his floor point and his sprite rides MASON_LIFT over it. He flies the run line, RUN_SHARE of the clones'
# radius, zigzagging ZIG either side of it with a peak every ZIG_STEP of his round angle, and drops a bomb at each peak
# he crosses going forward: the line and its zigzag grow with the circle, so the bombs stay on the path it asks for.
const MASON_LIFT := 130.0
const RUN_SHARE := 520.0 / 704.0
const RUN_RADIUS := CLONE_RADII.x * RUN_SHARE
const ZIG_SHARE := 70.0 / 704.0
const ZIG := CLONE_RADII.x * ZIG_SHARE
const ZIG_STEP := 15.0
# In from his rest to the run line MASON_ENTRY_LEAD ahead of the first clone, swung up over MASON_ENTRY_ARC.
const MASON_ENTRY_TIME := 0.6
const MASON_ENTRY_ARC := 120.0
const MASON_ENTRY_LEAD := 130.0
# His lead over the beam chasing the player: MASON_AHEAD over the player's own lead, never under MASON_LEAD.x (the
# bombs always land ahead of the player on pace) nor over MASON_LEAD.y (clear of the beam's leading half). He flies the
# short way at up to MASON_SPEED degrees a second; more than MASON_TOLERANCE off it, he is catching up, and drops
# nothing.
const MASON_LEAD := Vector2(130, 155)
const MASON_AHEAD := 45.0
const MASON_SPEED := 150.0
const MASON_TOLERANCE := 10.0
# Nor while he is less than this ahead of the player: a player who dashed past the bombs gets none dropped on them.
const DROP_AHEAD := 40.0
const MASON_TENSION := 0.9
# Jordan's right hand yanks on a catch-up at most this often.
const YANK_GAP := 1.0
# Back down at the end, over MASON_RETURN_ARC.
const MASON_RETURN_TIME := 0.7
const MASON_RETURN_ARC := 120.0
const SHADOW := {texture = "res://Assets/Characters/Mason/mason_leap_shadow.png", hframes = 3, scale = 3.0, alpha = 0.35,
	step = 100.0, fade = 0.3}

#THE POO (JordanCirclePoo)
# From his feet to his floor point in POO_FALL, then POO_LIVE lying armed, then a harmless POO_FADE. Only soles inside
# POO_CONTACT's oval round its floor point step in it; a hit squashes it.
const POO_FALL := 0.25
const POO_LIVE := 3.0
const POO_FADE := 0.3
const POO_CONTACT := Vector2(48, 24)
# PooBombScene's own sheets: the bomb's drawn base on its floor point, its armed loop, and the burst centred where the
# scene centres it, POP_RISE over the base.
const POO_SHEET := {texture = "res://Assets/Characters/Mason/poo_bomb.png", hframes = 2, offset = Vector2(0, -14),
	frame_time = 0.13, scale = 3.0}
const POP_SHEET := {texture = "res://Assets/Characters/Mason/poo_explosion.png", hframes = 5, frame_time = 0.1, scale = 3.0}
const POP_RISE := 42.0

#THE END
const REACH_MARGIN := 8.0

#HYPE
# A lap with no beam hit, a part lap its share of it (the closing half lap, half), and the whole loop with no hit at all.
const HYPE_LAP := 4.0
const HYPE_CLEAN := 10.0

#SOUNDS (Carter's and Mason's own, at their fights' levels unless noted)
const SOUNDS := {
	&"flash": {stream = "res://Assets/Audio/SFX/carter_eye_flash.wav", volume_db = 0.0},
	&"warp": {stream = "res://Assets/Audio/SFX/carter_warp.wav", volume_db = 0.0},
	&"strike": {stream = "res://Assets/Audio/SFX/carter_strike.wav", volume_db = 0.0},
	&"spent": {stream = "res://Assets/Audio/SFX/carter_spent.wav", volume_db = 4.0},
	&"squat": {stream = "res://Assets/Audio/SFX/wrestler_charge.ogg", volume_db = 0.0},
	&"pop": {stream = "res://Assets/Audio/SFX/hit_impact.ogg", volume_db = -10.0, voices = 2},
}
# The Messatsu's charge as a loop under the whole sweep, and its fire on a pool of voices: thirty-six of them.
const HUM_DB := -12.0
const FIRE_DB := -8.0
const FIRE_VOICES := 3

# The ellipse's length so far at each of ROUND_SAMPLES steps of floor angle, on a floor radius of 1: built once.
static var round_table := PackedFloat64Array()


# Clone `i`'s round angle, and its floor angle.
static func clone_round(i: int) -> float:
	return FIRST_ROUND + CLONE_STEP * i


static func clone_angle(i: int) -> float:
	return floor_of(clone_round(i))


static func clone_feet(i: int) -> Vector2:
	var a := deg_to_rad(clone_angle(i))
	return (CENTRE + Vector2(CLONE_RADII.x * cos(a), CLONE_RADII.y * sin(a))).round()


# The left half faces right, into the circle; the right half is mirrored.
static func faces_left(i: int) -> bool:
	return clone_feet(i).x > CENTRE.x


static func palms(i: int) -> Vector2:
	return clone_feet(i) + CarterArtLayout.local(CarterArtLayout.MESSATSU_MUZZLE, faces_left(i))


# Radians, from the palms through BEAM_CENTRE.
static func beam_angle(i: int) -> float:
	return (BEAM_CENTRE - palms(i)).angle()


static func beam_length(i: int) -> float:
	return 2.0 * palms(i).distance_to(BEAM_CENTRE) + BEAM_PAST


static func floor_angle(p: Vector2) -> float:
	return rad_to_deg(atan2((p.y - CENTRE.y) / FLOOR_RATIO, p.x - CENTRE.x))


static func floor_radius(p: Vector2) -> float:
	return Vector2(p.x - CENTRE.x, (p.y - CENTRE.y) / FLOOR_RATIO).length()


static func floor_point(deg: float, r: float) -> Vector2:
	var a := deg_to_rad(deg)
	return CENTRE + Vector2(r * cos(a), FLOOR_RATIO * r * sin(a))


# How far round `p` is, as a round angle.
static func round_angle(p: Vector2) -> float:
	return round_of(floor_angle(p))


# The point `r` out at round angle `deg`.
static func round_point(deg: float, r: float) -> Vector2:
	return floor_point(floor_of(deg), r)


# A floor angle as a round angle, whole turns kept: every ellipse on CENTRE with FLOOR_RATIO shares them.
static func round_of(floor_deg: float) -> float:
	var table := _table()
	var turns := floorf(floor_deg / 360.0)
	var at := (floor_deg - turns * 360.0) / 360.0 * ROUND_SAMPLES
	var i := clampi(int(at), 0, ROUND_SAMPLES - 1)
	var length := lerpf(table[i], table[i + 1], at - i)
	return (turns + length / table[ROUND_SAMPLES]) * 360.0


# A round angle as a floor angle, whole turns kept.
static func floor_of(round_deg: float) -> float:
	var table := _table()
	var turns := floorf(round_deg / 360.0)
	var length := (round_deg - turns * 360.0) / 360.0 * table[ROUND_SAMPLES]
	var i := clampi(table.bsearch(length, false) - 1, 0, ROUND_SAMPLES - 1)
	var share := (length - table[i]) / maxf(table[i + 1] - table[i], 0.000001)
	return (turns + (i + share) / ROUND_SAMPLES) * 360.0


static func _table() -> PackedFloat64Array:
	if round_table.is_empty():
		var lengths := PackedFloat64Array()
		lengths.resize(ROUND_SAMPLES + 1)
		var step := TAU / ROUND_SAMPLES
		for i in ROUND_SAMPLES:
			var t := (i + 0.5) * step
			lengths[i + 1] = lengths[i] + Vector2(sin(t), FLOOR_RATIO * cos(t)).length() * step
		round_table = lengths
	return round_table


static func in_soles_area(soles: Vector2) -> bool:
	return ((soles - CENTRE) / SOLES_RADII).length_squared() <= 1.0


# Round CENTRE, which the wall is placed on.
static func wall_polygon() -> PackedVector2Array:
	var points := PackedVector2Array()
	for i in WALL_POINTS:
		var a := TAU * i / WALL_POINTS
		points.append(Vector2(WALL_RADII.x * cos(a), WALL_RADII.y * sin(a) - WALL_RISE))
	return points


# The clone nearest the soles fires first; a tie goes to the one nearest the way they face, and a tie on that to the
# one clockwise of it. From the warp that is the top-right clone, so the sweep runs down the right side.
static func first_clone(soles: Vector2, facing: Vector2) -> int:
	var best := -1
	var best_distance := INF
	var best_turn := INF
	var best_clockwise := INF
	for i in CLONES:
		var to := clone_feet(i) - soles
		var distance := to.length()
		var clockwise := fposmod(rad_to_deg(facing.angle_to(to)), 360.0)
		var turn := minf(clockwise, 360.0 - clockwise)
		var better := best < 0 or distance < best_distance - 0.5
		if not better and absf(distance - best_distance) <= 0.5:
			better = turn < best_turn - 0.01 or (absf(turn - best_turn) <= 0.01 and clockwise < best_clockwise)
		if better:
			best = i
			best_distance = distance
			best_turn = turn
			best_clockwise = clockwise
	return best


# Mason's zigzag off the run line, `angle_from_start` round degrees on from where he came in: a peak every ZIG_STEP,
# inside and outside by turns, inside at his start.
static func zig(angle_from_start: float) -> float:
	var x := angle_from_start / ZIG_STEP
	return ZIG * (1.0 - 2.0 * absf(fposmod(x, 2.0) - 1.0))


static func body_point(soles: Vector2) -> Vector2:
	return soles - Vector2(0, SOLES_OVER_ORIGIN)


# The laps the fires make, a part lap counting as one, and how many of the fires are lap `lap`'s.
static func lap_count() -> int:
	return ceili(float(FIRES) / CLONES)


static func lap_fires(lap: int) -> int:
	return clampi(FIRES - lap * CLONES, 0, CLONES)


# Fire `fire`'s lap's cadence: its own lap time when LAP_TIMES has one, LAP_TIME otherwise, over the clones.
static func cadence(fire: int) -> float:
	var lap_time := LAP_TIME
	if not LAP_TIMES.is_empty():
		lap_time = LAP_TIMES[mini(fire / CLONES, LAP_TIMES.size() - 1)]
	return lap_time / CLONES


static func charge_time(fire: int) -> float:
	return CHARGING * cadence(fire)
