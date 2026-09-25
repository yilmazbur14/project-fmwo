extends RefCounted

# The rope of the sumo Danny drags the fight into at 0 HP (DannyBossSumo), as numbers, so the fight and its
# tests step the same model: the Sumo state calls press() for every press MashInput counts and advance()
# every physics step, and stands both fighters off `rope`.
# `rope` runs from -1 to +1 from the tachiai line at 0. At +1 Danny's feet are out past the top rope and the
# player has won; at -1 the player's are out past the bottom one. The ground the player has won off the line
# is their bar, and MashCurve bends it the way it bends every mash in the game: the first presses off the
# line come easy and the last ones before the rope are work. Danny pushes back the whole time, harder every
# second once push_grace is up, and `bulldoze` times as hard while the rope is on the player's side of the
# line, so a player who stops is out in about three seconds. At sumo_max he surges and wins wherever the rope
# is, unless the player already has.
#
# THE FIT (table(): steady alternating presses, the first as the clinch lands, stepped 60 times a second).
# The plan's rows: 0 a second loses in 2.5-3.5 s, 4 and 5 lose inside 10 and 12 s, it takes 6 a second
# (+-10%), 7 wins in 3.0-4.5 s, 9 inside 3.0 s, 11 inside 2.3 s.
#   presses/s   0     1     2     3     4     5     6     7     8     9     10    11
#   result      loss  loss  loss  loss  loss  loss  loss  win   win   win   win   win
#   seconds     3.33  7.53  8.40  9.08  9.70  10.35 11.08 4.00  3.00  2.45  2.10  1.83
#   the rate it takes: 6.45 a second
# Every row holds with the first press up to a whole interval late, and at 120 steps a second.
# The plan's starting knobs (gain 0.085, grace 4.0, ramp 0.17) won at 7 a second in 2.87 s. The smaller
# gain slows every win; the later grace gives that time back at the rate it takes, so it stays at 6; the
# steeper ramp brings the losses the later grace put off back inside their bounds. push_drain is small
# because Danny's own push is what fights back at the rope, and MashCurve's drain climbs hard at the top:
# any more of it and 7 a second stops winning inside the plan's 4.5 s. Re-run table() whenever a knob here
# or in MashCurve moves.

const MashCurve := preload("res://Scripts/MashCurve.gd")

# Every knob fresh() copies. The Sumo state exports its own and writes them in.
const KNOBS: Array[StringName] = [&"push_gain", &"push_drain", &"push_base", &"push_grace", &"push_ramp",
	&"bulldoze", &"sumo_max"]
# table()'s steps a second (the fight's physics rate) and its rates, 0 to 11 a second.
const TABLE_STEPS := 60
const TABLE_RATES := 12

# A press's worth off the line, and the bar's own drain a second, before MashCurve bends them.
var push_gain := 0.08
var push_drain := 0.02
# Danny's push, rope a second: push_base until push_grace seconds after the clinch, then push_ramp more for
# every second after that.
var push_base := 0.10
var push_grace := 5.0
var push_ramp := 0.22
var bulldoze := 3.0
var sumo_max := 15.0

var rope := 0.0
var clock := 0.0
var presses := 0
# &"" while the bout is on, then &"win" or &"loss".
var result := &""


func fill() -> float:
	return clampf(rope, 0.0, 1.0)


func danny_push() -> float:
	return push_base + push_ramp * maxf(clock - push_grace, 0.0)


func press() -> void:
	if result != &"":
		return
	presses += 1
	rope += MashCurve.gain(push_gain, fill())
	if rope >= 1.0:
		rope = 1.0
		result = &"win"


func advance(delta: float) -> void:
	if result != &"":
		return
	clock += delta
	rope -= (MashCurve.drain(push_drain, fill()) + danny_push() * (bulldoze if rope < 0.0 else 1.0)) * delta
	if rope <= -1.0:
		rope = -1.0
		result = &"loss"
	elif clock >= sumo_max:
		result = &"loss"


# A new bout on these knobs.
func fresh() -> RefCounted:
	var bout: RefCounted = get_script().new()
	for knob in KNOBS:
		bout.set(knob, get(knob))
	return bout


# A fresh bout at a steady `rate` alternating presses a second, the first as the clinch lands, stepped
# `steps` times a second: {result, time, presses}.
func steady(rate: float, steps := TABLE_STEPS) -> Dictionary:
	var bout = fresh()
	var next_press := 0.0 if rate > 0.0 else INF
	while bout.result == &"":
		# The summed press intervals and the summed steps drift apart by a hair, which would slip a press
		# that is due on a step to the step after.
		while bout.result == &"" and bout.clock >= next_press - 1e-9:
			bout.press()
			next_press += 1.0 / rate
		bout.advance(1.0 / steps)
	return {"result": bout.result, "time": bout.clock, "presses": bout.presses}


# The slowest steady rate that wins, to within 0.005 a second.
func needed_rate(steps := TABLE_STEPS) -> float:
	var low := 0.0
	var high := 20.0
	while high - low > 0.005:
		var rate := (low + high) / 2.0
		if steady(rate, steps).result == &"win":
			high = rate
		else:
			low = rate
	return high


# Every rate from 0 to 11 a second, and the rate it takes, as lines for the log.
func table(steps := TABLE_STEPS) -> String:
	var lines := PackedStringArray(["presses/s  result  seconds  presses"])
	for rate in TABLE_RATES:
		var bout := steady(rate, steps)
		lines.append("%9d  %-6s  %7.2f  %7d" % [rate, bout.result, bout.time, bout.presses])
	lines.append("the rate it takes: %.2f a second" % needed_rate(steps))
	return "\n".join(lines)
