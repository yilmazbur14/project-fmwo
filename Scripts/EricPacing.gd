extends RefCounted

# Eric's pacing, today's fight (V1) beside the reworked one (V2), as {key: [v1, v2]}. Every Eric script
# reads its numbers from here, so switching `version` switches the whole fight: V1 is exactly the fight
# as it was, kept for A/B and the tests pinned to it, and V2 is the one that ships. A key V1 has no use
# for holds null there.
# `rage_` keys are the same number with no health left; raged() blends the pair by EricStateMachine.rage.
# Times are seconds of game time, speeds are on-screen px/s.

static var version := 2

const TABLE := {
	"max_health": [24, 56],

	#CHAIN
	"attacks_per_chain": [3, 3],
	"rage_attacks_per_chain": [4, 4],
	# At or below this health ratio every chain gets its rage attack count.
	"rage_chain_health_ratio": [0.34, 0.40],
	# Idle between attacks in a chain. V2's decisions sit on the tells, so its short gaps only punish
	# hesitation.
	"attack_gap": [0.45, 0.25],
	"rage_attack_gap": [0.3, 0.15],
	# Idle after the window, before the next chain.
	"recovery_rest": [0.6, 0.25],
	# The window a chain ends in, and how long it lasts. V1's Downed is long enough to walk up to him
	# and land two full three-punch combos, and dazes; V2's Winded is a short punish with no daze,
	# since the Break gauge (BossBreakGauge) is how he is dazed there.
	"window_state": ["Downed", "Winded"],
	"window_time": [6.0, 2.0],
	"rage_window_time": [6.0, 1.6],

	#EARTHQUAKE
	"slams": [2, 2],
	"rage_slams": [3, 3],
	"slam_animation_speed": [1.6, 1.6],
	# Capped so the raised sword is up long enough to be read: his waves radiate from where he stands,
	# so anyone in the slam is hit with no travel at all. `earthquake` calls enable_hitbox 0.667 s in,
	# which at 1.85x leaves 0.36 s of wind-up, comfortably past PlayerDefense.parry_window. Raising this
	# back toward 2.1 takes that below it.
	"rage_slam_animation_speed": [1.85, 1.85],
	"wave_speed": [1150.0, 1150.0],
	"rage_wave_speed": [1400.0, 1400.0],
	"wave_id": [&"eric_quake_wave", &"eric_quake_wave_v2"],
	# V2's standard red tell comes up exactly this long before the waves exist, delayed or not: 1.5x
	# the parry window, and Carter's floor. The player reads the tell, not the raise.
	"slam_tell_time": [null, 0.36],
	# The share of slams that hold the frame before impact, and the holds. Never in the fight's first
	# slam attack and at most one slam per attack, so an attack with more slams than 1 / chance can't
	# reach the share.
	"delayed_slam_chance": [0.0, 0.4],
	"delayed_slam_holds": [[], [0.20, 0.35]],

	#WHIRLWIND
	"spin_animation_speed": [1.5, 1.5],
	"rage_spin_animation_speed": [2.1, 2.1],
	"whirlwind_id": [&"eric_whirlwind", &"eric_whirlwind_v2"],
	# V1: he chases the player for chase_time, then spins back to where he started.
	"chase_speed": [420.0, null],
	"rage_chase_speed": [540.0, null],
	"chase_time": [3.0, null],
	# V2: a yellow wind-up, straight lunges with a re-aim between them, then he lets the sword go at
	# the player and the throw takes it from there (EricWhirlwind, EricSwordThrow). The wind-up is a
	# single-answer read, at or above the 0.40 s floor.
	"whirl_windup": [null, 0.45],
	"rage_whirl_windup": [null, 0.40],
	"whirl_lunges": [null, 2],
	"rage_whirl_lunges": [null, 3],
	"whirl_lunge_time": [null, 0.5],
	"whirl_lunge_speed": [null, 1000.0],
	"rage_whirl_lunge_speed": [null, 1150.0],
	"whirl_reaim_time": [null, 0.35],
	"rage_whirl_reaim_time": [null, 0.30],
	# A re-aim also holds until the next lunge can't reach the player sooner than the dash rule's gap
	# (AttackCatalog.DASH_IMMUNITY_COOLDOWN) plus this after the last lunge met them, so every lunge can
	# be dashed through, with this much lead, even when the next one starts on top of them.
	"whirl_dodge_lead": [null, 0.15],
	# The dizzy stop the sword release replaced: unused in V2, and kept so restoring it is a revert of
	# EricWhirlwind rather than a retune.
	"whirl_dizzy_time": [null, 0.8],
	"rage_whirl_dizzy_time": [null, 0.6],

	#SWORD THROW
	"sword_speed": [1400.0, 1400.0],
	"rage_sword_speed": [1700.0, 1700.0],
	"ring_speed": [950.0, 950.0],
	"rage_ring_speed": [1200.0, 1200.0],
	# How long the sword stays planted before he recalls it.
	"planted_time": [0.7, 0.5],
	"rage_planted_time": [0.45, 0.35],
	# A parried sword comes back faster than he threw it, since the player sent it.
	"reflect_speed": [1600.0, 1600.0],
	# Added to the parry's own stagger window. He is struck at throwing range, not standing over the
	# player, so there is further to run before the punish.
	"reflect_stagger_bonus": [0.5, 0.5],

	#BEAR HUG
	# The charge is the grab's telegraph. V2's has to leave a colour decision time: at least 0.40 s and
	# a margin.
	"hug_charge_time": [0.9, 0.55],
	"rage_hug_charge_time": [0.65, 0.45],
	"hug_lunge_speed": [1500.0, 1500.0],
	"rage_hug_lunge_speed": [1800.0, 1800.0],
	"hug_lunge_max_distance": [650.0, 650.0],
	"hug_return_speed": [900.0, 900.0],
	"hug_squeezes": [3, 3],
	# The whiff's stumble, open to punches.
	"hug_stumble_time": [0.9, 0.7],
	"hug_grab_id": [&"eric_bear_hug_grab", &"eric_bear_hug_grab_v2"],
	# V2's charge is red, the grab only a parry answers, or yellow, a shoulder charge only a dash
	# answers, on the same art and timing. The fight's first hug is red, and never three of one colour
	# in a row.
	"hug_yellow_chance": [0.0, 0.5],

	#PHASE TWO (EricPacing V2 only)
	# At or below this health ratio his sword is knocked out of the ring (EricPhaseTwo) and he fights
	# on with his fists. EricScript latches the phase the first time a hit takes him across it; nothing
	# reads the ratio again afterwards.
	"phase_two_health_ratio": [null, 0.5],
	# Everything below is read through p2(), not raged(): rage only spans 0.5 -> 1.0 inside phase two,
	# so raged() would leave every one of these numbers stuck in the top half of its own range.
	# Much faster than phase one's 0.25/0.15: the sword was what made him slow.
	"p2_attack_gap": [null, 0.18],
	"rage_p2_attack_gap": [null, 0.10],
	# He walks the gap down onto the player instead of standing in it. The clearest "agile" tell there is.
	"p2_stalk_speed": [null, 360.0],
	"rage_p2_stalk_speed": [null, 480.0],
	# The mixup's wind-up, identical to hug_charge_time so phase one's colour training transfers whole.
	"p2_windup": [null, 0.55],
	"rage_p2_windup": [null, 0.45],
	# THE NUMBER THE MIXUP STANDS ON. Both branches leave his hand and reach the player after exactly
	# this long, at any range: the rush is fixed-duration and homes, so the answer window never shrinks
	# with distance, and the moment of contact carries no information about which branch it is. Only
	# the badge's colour does. It has no rage twin ON PURPOSE - the haymaker and the grab must arrive
	# together at every rage, and a twin is an invitation to move one of them.
	# Red must never land AFTER yellow: if it did, a dash for the grab followed by a press for the
	# haymaker would beat both, because the press lands after the grab resolved and so cannot give up
	# the dash's i-frames (DashImmunity reads player.dash_cancelled at contact).
	"p2_strike_travel": [null, 0.30],
	# How long his arms stay live once he arrives. A single frame would be a coin toss against a moving
	# player; much longer and the dash answer stops being fair, since a dash has to cover the whole of
	# it out of AttackCatalog.DASH_IMMUNITY_TIME (0.1833 s at 60 fps) and what is left is the window
	# the player has to hit. At 0.05 that window is 0.133 s, eight frames.
	"p2_strike_hot": [null, 0.05],
	# The whiffed grab's stumble, open to punches, and the haymaker's own follow-through.
	"p2_stumble_time": [null, 0.7],
	"p2_recover_time": [null, 0.45],
	# The hold: a crush every interval, up to p2_crush_ticks, then he lets go whether they got out or
	# not. Three ticks of 1 against six half-hearts, so never mashing is most of a health bar and
	# getting out on the first tick is one. PlayerGrabEscape's meter fills in about 0.8 s at ten
	# alternating presses a second and 1.2 s at seven, which is what sets this interval.
	"p2_crush_ticks": [null, 3],
	"p2_crush_interval": [null, 0.8],
	"rage_p2_crush_interval": [null, 0.65],
	# The chance a mixup comes out yellow (the grab). Same rule as the phase-one hug: the first is
	# always red, and never three of one colour in a row (EricColourRule).
	"p2_yellow_chance": [null, 0.5],

	#BARBARIC LEAP
	"p2_leaps": [null, 5],
	"p2_leap_crouch": [null, 0.35],
	"rage_p2_leap_crouch": [null, 0.28],
	"p2_leap_air": [null, 0.55],
	"rage_p2_leap_air": [null, 0.48],
	# The landing beat the tremor goes out on, before the next crouch.
	"p2_leap_land": [null, 0.12],
	"rage_p2_leap_land": [null, 0.10],
	# A dash is only immune AttackCatalog.DASH_IMMUNITY_COOLDOWN after the last one, so two tremors
	# closer together than that could not both be dashed. Landing to landing is leap_land + leap_crouch
	# + leap_air, and the crouch holds until it clears the cooldown plus this lead - the same rule and
	# the same reasoning as whirl_dodge_lead. At full health that sum is 1.02 s and enraged 0.86 s,
	# both already clear of 0.6 + 0.15, so the hold is the floor rather than the usual case.
	"p2_leap_dodge_lead": [null, 0.15],
	# The rest at the end of the five, open to punches.
	"p2_leap_rest": [null, 1.8],
	"rage_p2_leap_rest": [null, 1.5],
	"p2_tremor_speed": [null, 1100.0],
	"rage_p2_tremor_speed": [null, 1350.0],

	#STAGGER AND BREAK
	# How fast a parry-staggered Eric glides back to where his attack started. V1 borrowed the
	# whirlwind's chase speed, which V2 no longer has.
	"stagger_glide_speed": [420.0, 420.0],
	# How long a Break (BossBreakGauge) leaves him on his knees.
	"broken_time": [null, 3.0],
	"rage_broken_time": [null, 2.6],
}


static func is_v2() -> bool:
	return version == 2


static func value(key: String) -> Variant:
	return TABLE[key][version - 1]


# `key` at `rage` (0 at full health, 1 at none), between it and its rage_ twin.
static func raged(key: String, rage: float) -> float:
	return lerpf(value(key), value("rage_" + key), rage)


# A phase-two number at `rage`. Phase two only ever runs from phase_two_health_ratio downwards, so
# rage there spans 0.5 -> 1.0 and never the bottom half: raged() would hand back a number already
# past the middle of its range on the very first phase-two attack. This remaps that half onto the
# whole, so a phase-two key reads its plain value the moment the sword goes and its rage_ twin at
# his last half-heart.
static func p2(key: String, rage: float) -> float:
	var entry_ratio: float = value("phase_two_health_ratio")
	var t := 1.0 if entry_ratio <= 0.0 else clampf((rage - (1.0 - entry_ratio)) / entry_ratio, 0.0, 1.0)
	return raged(key, t)
