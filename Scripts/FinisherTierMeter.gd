extends RefCounted

# The tiered finisher's meter (PlayerFinisher, against a boss that can be juggled): three bars, filled
# by alternating presses against a drain, each bar with its own window. The finisher and the mash_tiers
# test both drive this, press by press and step by step.
# The meter runs from 0 to 3, and bar k covers k-1 to k. A press adds `gain` and the meter drains at the
# current bar's rate, both bent by MashCurve on how full the current bar is, so every bar starts easy and
# ends hard; it never drains below the bars already banked. Reaching k banks bar k and snaps the meter to
# exactly k, throwing any overshoot away. Bar 1 has to fill within its window of the first press, or of
# `start_grace` after the prompt if nothing was pressed by then; each later bar within its own window of
# the one before it banking. The mash resolves as bar 3 banks, when the current bar's window runs out,
# or once presses have stopped for `idle_stop` with a bar banked. The player gets what they banked.
# Times are the finisher's own seconds from the prompt.

const MashCurve := preload("res://Scripts/MashCurve.gd")

# A press that lands a hair short of a bar's top still banks it.
const BANK_EPSILON := 1e-6
# Summed frame deltas land a hair short of a window's length, which would close it a frame late.
const STEP_TOLERANCE := 0.0001

var gain: float
var drains: Array
var windows: Array
var start_grace: float
var idle_stop: float

var meter := 0.0
var banked := 0
var clock := 0.0
# When the current bar's window opened; -1 before bar 1's has.
var window_from := -1.0
var last_press := -1.0
var resolved := false


func _init(press_gain: float, bar_drains: Array, bar_windows: Array, grace: float, stop_after: float, banked_at_start := 0) -> void:
	gain = press_gain
	drains = bar_drains
	windows = bar_windows
	start_grace = grace
	idle_stop = stop_after
	banked = banked_at_start
	meter = float(banked)


# Returns the bar this press banked, or 0.
func press() -> int:
	if resolved:
		return 0
	if window_from < 0.0:
		window_from = clock
	last_press = clock
	meter += MashCurve.gain(gain, meter - banked)
	if meter < banked + 1 - BANK_EPSILON:
		return 0
	banked += 1
	meter = float(banked)
	window_from = clock
	resolved = banked == windows.size()
	return banked


func advance(delta: float) -> void:
	if resolved:
		return
	clock += delta
	meter = maxf(meter - MashCurve.drain(drains[banked], meter - banked) * delta, float(banked))
	if window_from < 0.0 and clock >= start_grace - STEP_TOLERANCE:
		window_from = start_grace
	if window_from >= 0.0 and clock - window_from >= windows[banked] - STEP_TOLERANCE:
		resolved = true
	elif banked > 0 and last_press >= 0.0 and clock - last_press >= idle_stop - STEP_TOLERANCE:
		resolved = true
