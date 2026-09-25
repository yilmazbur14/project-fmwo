extends RefCounted

# The rule that decides which colour a two-branch Eric attack comes out in: his bear hug (EricBearHug,
# red grab or yellow shoulder charge) draws from it.
# The fight's first of a kind is always red, never three of one colour in a row, and otherwise a coin
# toss at the attack's own chance.
# The caller keeps the counter and the run of colours, so a test can set up a colour it wants by
# poking them; this only holds the rule itself.


# `started` is how many of this attack have already come out, `recent` the last two colours (kept to
# two here), and `chance` the attack's own yellow share.
static func next_is_yellow(started: int, recent: Array[bool], chance: float) -> bool:
	var pick := false
	if started > 0:
		pick = randf() < chance
		if recent.size() == 2 and recent[0] == recent[1]:
			pick = not recent[1]
	recent.append(pick)
	if recent.size() > 2:
		recent.pop_front()
	return pick
