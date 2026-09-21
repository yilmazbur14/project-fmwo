extends RefCounted

# The player numbers the Eric pacing rework (EricPacing V2) changed with the reworked feel, today's
# beside feel_v2's as {key: [today, feel_v2]}, read through the player's own flag
# (PlayerScript.feel_v2, which every fight is on). The dash's and the punch reach's own pairs stay
# where their reworks put them (PlayerDefense, PlayerScript).
# With feel_v2 a punch also lands the moment the arm is out (PlayerPunching), not when the boss's
# hurtbox reports it after the swing: a hit needs his hurtbox open 0.27 s after the press, not 0.40 s.

const TABLE := {
	# PlayerCombo: seconds of game time after a swing ends before the beat window opens, and how long
	# it stays open.
	"combo_window_offset": [0.05, 0.04],
	"combo_window_length": [0.35, 0.25],
	# PlayerHype's gains. The charged punch pays instead of the plain one, not on top of it. The parry's
	# go by streak tier: the first parry, the second, then the third and up.
	"hype_punch_gain": [5.0, 4.0],
	"hype_charged_punch_gain": [12.0, 10.0],
	"hype_parry_gains": [[25.0, 30.0, 35.0], [15.0, 20.0, 25.0]],
	"hype_perfect_dodge_gain": [15.0, 10.0],
}


static func value(key: String, feel_v2: bool) -> Variant:
	return TABLE[key][1 if feel_v2 else 0]
