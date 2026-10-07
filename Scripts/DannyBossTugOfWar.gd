extends RefCounted

# The rope of the sumo Danny drags the fight into at 0 HP (DannyBossSumo), as numbers, so the fight and its
# tests step the same model: the Sumo state calls press() for every press MashInput counts and advance()
# every physics step, and stands both fighters off `rope`.
# `rope` runs from -1 to +1 from the tachiai line at 0. At +1 Danny's feet are out past the top rope and the
# player has won; at -1 the player's are out past the bottom one.
#
# THE ONE MASH OFF MashCurve, on the user's word (2026-09-27): the effort it takes is the same wherever the
# rope stands, and it is a back-and-forth. So nothing here reads the rope: a press is worth press_gain from
# anywhere, and Danny pushes the same from anywhere. Every press queues its worth, and the queue feeds the
# rope at up to press_speed, so mashing faster than press_speed / press_gain presses a second wins no sooner:
# the demand is a steady rate, not a sprint. At most BACKLOG_PRESSES presses' worth waits, so a quick pair
# between slower presses still counts whole. Danny pushes danny_push all the time and surges on a beat: from
# surge_first, every surge_every, a surge_time heave (a sin^2 bump) peaking surge_push harder, which takes
# ground back from even the fastest masher, so the rope swings both ways. From sumo_max he surges for good,
# his push climbing final_surge more every second, and a bout still going that long is his in a second or
# two, wherever the rope is.
#
# THE FIT (table(): steady alternating presses, the first as the clinch lands, stepped 60 times a second).
# 7 a second, the target, wins in about 9.4 s; 7.5 or faster in 6.3 s; 5 loses in about 11 s:
#   presses/s   0     1     2     3     4     5     6     7     8     9     10    11
#   result      loss  loss  loss  loss  loss  loss  loss  win   win   win   win   win
#   seconds     1.72  1.85  2.25  4.00  4.80  10.68 31.53 9.37  6.30  6.30  6.30  6.30
#   the rate it takes: 6.26 a second, winning at about 30 s; 6.5 wins in 16 s and 6.75 in 10 s
# Every row holds with the first press up to a whole interval late, and at 120 steps a second. At 7 a second
# each surge takes a third of the rope back, and a stop of a second at 4 s, which loses the lead, is won back
# by 15.4 s. Re-run table() whenever a knob here moves.

# Every knob fresh() copies. The Sumo state exports its own and writes them in.
const KNOBS: Array[StringName] = [&"press_gain", &"press_speed", &"danny_push", &"surge_push", &"surge_time",
	&"surge_every", &"surge_first", &"sumo_max", &"final_surge"]
const BACKLOG_PRESSES := 2.0
# table()'s steps a second (the fight's physics rate) and its rates, 0 to 11 a second.
const TABLE_STEPS := 60
const TABLE_RATES := 12

# A press's worth of rope, and the most rope a second the presses move it.
var press_gain := 0.1
var press_speed := 0.75
# His push, rope a second, and his surges' extra at their peak, their length and their beat, in seconds from
# the clinch.
var danny_push := 0.40
var surge_push := 1.2
var surge_time := 1.0
var surge_every := 3.0
var surge_first := 1.2
var sumo_max := 30.0
var final_surge := 1.0

var rope := 0.0
# Pressed rope on its way into the rope.
var pending := 0.0
var clock := 0.0
var presses := 0
# &"" while the bout is on, then &"win" or &"loss".
var result := &""


func fill() -> float:
	return clampf(rope, 0.0, 1.0)


# How far into a surge he is, 0 between surges and 1 at a surge's peak.
func surge() -> float:
	if clock < surge_first:
		return 0.0
	var into := fmod(clock - surge_first, surge_every)
	if into >= surge_time:
		return 0.0
	return pow(sin(PI * into / surge_time), 2.0)


func surging() -> bool:
	return surge() > 0.0 or clock >= sumo_max


# His push now, rope a second.
func push() -> float:
	return danny_push + surge_push * surge() + final_surge * maxf(clock - sumo_max, 0.0)


func press() -> void:
	if result != &"":
		return
	presses += 1
	pending = minf(pending + press_gain, press_gain * BACKLOG_PRESSES)


func advance(delta: float) -> void:
	if result != &"":
		return
	clock += delta
	var moved := minf(pending, press_speed * delta)
	pending -= moved
	rope += moved - push() * delta
	if rope >= 1.0:
		rope = 1.0
		result = &"win"
	elif rope <= -1.0:
		rope = -1.0
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
