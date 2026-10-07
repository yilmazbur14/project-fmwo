extends RefCounted

# The fill curve every alternating mash in the game shares: the finisher's (PlayerFinisher: its one bar,
# its tiered bars in FinisherTierMeter and its scripted charge), the grab escape's (PlayerGrabEscape), the
# mine trap's (ComputahTrapped) and Matt's Deafening Yell (MattGlassRow). Danny's sumo rope
# (DannyBossTugOfWar) is the one mash off it, on the user's word: the same effort wherever the rope is.
# Each mash keeps its own gain per press and drain per second, and this bends them by how
# full the bar already is: the first half comes in a few presses, and the last quarter is the push, each
# press a sliver of the first ones against a drain that stays low until then and climbs hard at the top.
# A tiered mash bends each bar on its own fill, so every bar starts easy again.
# At a steady 7 presses a second on the finisher, half the bar comes in the first 3 of 16 presses and the
# last fifth takes 9 of them, where a flat mash took 7 of its 14 and 3.
# DRAIN_AT_FULL is 1, so a mash's own drain is what it pulls back at a full bar. Those drains are fitted
# so every mash asks about 5.5 to 7 steady presses a second (a tiered one for its first bar), and 8 wins
# them all. Moving any number here moves those rates, so re-measure them with it (mash_tiers, mine_mash,
# matt_deafen).

# A press is worth GAIN_AT_EMPTY of the mash's own gain on an empty bar and GAIN_AT_FULL at the top.
# GAIN_FALL is how soon it falls between them: higher drops it sooner.
const GAIN_AT_EMPTY := 2.4
const GAIN_AT_FULL := 0.25
const GAIN_FALL := 1.35
# The drain runs at DRAIN_AT_EMPTY of the mash's own on an empty bar and DRAIN_AT_FULL at the top.
# DRAIN_RISE is how late it rises between them: higher keeps it low for longer.
const DRAIN_AT_EMPTY := 0.1
const DRAIN_AT_FULL := 1.0
const DRAIN_RISE := 3.0


# What one press adds to a bar `fill` full (0 to 1), for a mash whose own gain is `base`.
static func gain(base: float, fill: float) -> float:
	return base * lerpf(GAIN_AT_FULL, GAIN_AT_EMPTY, pow(1.0 - clampf(fill, 0.0, 1.0), GAIN_FALL))


# The drain per second on a bar `fill` full, for a mash whose own drain is `base`.
static func drain(base: float, fill: float) -> float:
	return base * lerpf(DRAIN_AT_EMPTY, DRAIN_AT_FULL, pow(clampf(fill, 0.0, 1.0), DRAIN_RISE))
