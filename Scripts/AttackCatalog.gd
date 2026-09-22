extends RefCounted

# How every attack that can hurt the player can be defended against, keyed by attack id. Attackers
# pass the id to the player through HitInfo; PlayerDefense decides the outcome from these entries.
# Keys left out of an entry take the value in DEFAULTS:
#     damage                half-hearts on a hit; 0 for a grab, whose caller does the rest
#     blockable             a guard facing it absorbs it, and a fresh press parries it
#     parryable             a fresh press parries it even though a held guard can't absorb it
#     weight                the stamina a block costs
#     tell                  it warns over the boss's head while it winds up (ParryTell)
#     dodge_tell            it warns in yellow instead: don't parry it, dodge it (ParryTell)
#     parry_stagger         a parry may stagger the boss (its can_parry_stagger() decides)
#     from_above            blockable from any facing
#     dash_through          dash immunity dodges it
#     grab                  a hit means the caller grabs the player
#     bypass_invincibility  lands inside the i-frames
#     hype_loss             a hit costs hype

enum Weight { NONE, LIGHT, HEAVY }

# For dash-through attacks: a dash is immune this long, if the previous dash started at least the
# cooldown before it, so mashing dash can't chain immunity windows.
const DASH_IMMUNITY_TIME := 0.18
const DASH_IMMUNITY_COOLDOWN := 0.6

const DEFAULTS := {
	"damage": 1,
	"blockable": false,
	"parryable": false,
	"weight": Weight.NONE,
	"tell": false,
	"dodge_tell": false,
	"parry_stagger": false,
	"from_above": false,
	"dash_through": false,
	"grab": false,
	"bypass_invincibility": false,
	"hype_loss": true,
}

const ATTACKS := {
	&"eric_quake_wave": {"blockable": true, "weight": Weight.LIGHT},
	&"eric_whirlwind": {"blockable": true, "weight": Weight.HEAVY},
	# A parry flings the sword back at him, and it staggers him where he threw it when it arrives.
	&"eric_thrown_sword": {"blockable": true, "weight": Weight.HEAVY, "parry_stagger": true, "tell": true},
	&"eric_quake_ring": {"dash_through": true},
	# A guard doesn't stop the grab, but a parry does, and it staggers him.
	&"eric_bear_hug_grab": {"damage": 0, "dash_through": true, "grab": true, "parryable": true, "parry_stagger": true, "tell": true},
	# The player is held and can't defend; the grab already cost the hype.
	&"eric_bear_hug_squeeze": {"bypass_invincibility": true, "hype_loss": false},
	# Eric's reworked fight (EricPacing V2). Red is a parry, yellow a dodge.
	# The slam's waves, with the standard red tell timing the read.
	&"eric_quake_wave_v2": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	# The whirlwind's lunges, behind a yellow wind-up: dashed through, or blocked at a heavy cost.
	&"eric_whirlwind_v2": {"blockable": true, "weight": Weight.HEAVY, "dash_through": true, "dodge_tell": true},
	# The red bear hug: only a parry answers it. A dash gives no immunity, though stepping out of its
	# line still makes it whiff.
	&"eric_bear_hug_grab_v2": {"damage": 0, "grab": true, "parryable": true, "parry_stagger": true, "tell": true},
	# The yellow bear hug, a shoulder charge on the same art and timing: no guard or parry stops it, a
	# dash goes through it.
	&"eric_shoulder_charge": {"dash_through": true, "dodge_tell": true},
	# Eric, phase two: he has lost the sword and the colours have swapped sides. Red is now the
	# haymaker, yellow the grab - the same two answers the fight taught, behind the opposite attacks.
	# Parry-only, exactly as the phase-one grab was: a held guard is not an answer to the red branch,
	# or hedging with the guard up would beat the read for free.
	&"eric_p2_haymaker": {"damage": 2, "parryable": true, "parry_stagger": true, "tell": true},
	# The grab: no range cutoff and no parry. A dash through it is the dodge - the flag V1's
	# eric_bear_hug_grab carried and the V2 rework took off.
	&"eric_p2_grab": {"damage": 0, "grab": true, "dash_through": true, "dodge_tell": true},
	# The hold's crush, ticking while the player mashes out. eric_bear_hug_squeeze's flags exactly.
	&"eric_p2_crush": {"bypass_invincibility": true, "hype_loss": false},
	# The leap's shockwave. Red, and a dash also beats it - computah_chase is the precedent for a red
	# tell with dash_through. Its tell is the floor marker (EricSwordMark), not a badge: he is airborne.
	&"eric_p2_tremor": {"blockable": true, "weight": Weight.LIGHT, "tell": true, "dash_through": true},
	# The sparring dummy in the controls room, which teaches the same red-and-yellow vocabulary Eric's
	# fight is built on, one attack each.
	# Red: the padded arm. HEAVY is deliberate - three blocks in a row empty the bar, so the guard
	# break teaches itself - and a parry leaves the arm out, which is the punish window to punch into.
	&"dummy_swing": {"blockable": true, "weight": Weight.HEAVY, "parry_stagger": true, "tell": true},
	# Yellow: the torso lunge. Nothing guards or parries it; a dash through it is a perfect dodge.
	&"dummy_lunge": {"dash_through": true, "dodge_tell": true},
	# Boss 2. Computah's cannon beam: it tracks while it charges, latches its aim, and fires down a
	# fixed line. No guard and no parry answers it, so the badge is yellow and a dash is the dodge.
	&"computah_beam": {"dash_through": true, "dodge_tell": true},
	# His pounce, the grab at the end of his chase: a held guard does not stop it, a parry does and
	# sparks him out early, and a dash through it is a perfect dodge.
	# bypass_invincibility because he does not care about i-frames while he chases: the mine field is
	# meant to herd the player into him, and a catch that fell out of the last hit's i-frames would
	# make being hit the safest place to stand. Both counters survive - only the passive window goes.
	&"computah_chase": {"damage": 0, "grab": true, "parryable": true, "parry_stagger": true, "tell": true, "dash_through": true, "bypass_invincibility": true},
	# A landed pounce: he holds the player and slams them himself. Two rather than three, because a
	# catch now also costs 30 stamina and 30 Break gauge, and three half-hearts on top of that is a
	# fight-losing bill for one mistake on an attack built to herd you into it.
	&"computah_slam": {"damage": 2, "bypass_invincibility": true, "hype_loss": false},
	# Computah's mine pods. Once one closes there is no answer at all - that is what the attack IS - so
	# it is neither blockable nor parryable and carries no tell of either colour. Its warning is the pod
	# on the floor, drawn from the moment it lands, exactly as Mason's nugget marker is its own warning.
	# `grab` is the honest shape: the caller takes the player, a held guard does not stop it, and a
	# player who is already grabbed is IGNORED by resolve_hit for free.
	# NO dash_through, deliberately: a spatial threat is answered by not being there, and one dash
	# clearing any minefield would end the attack.
	&"computah_mine": {"damage": 0, "grab": true, "hype_loss": false},
	# The charged uppercut on a player who failed the mash. Unblockable and unparryable BY CONSTRUCTION,
	# so the total lock never has to be load-bearing for correctness. It lands inside the i-frames
	# because the trap can follow a hit and the bill must arrive.
	&"computah_uppercut": {"damage": 2, "bypass_invincibility": true},
	# Boss 2. The overload blast: the punish for failing his charge check. It covers the whole arena, so
	# there is nowhere to be - no guard, no parry, no dash. It carries NEITHER tell: a badge is an answer
	# key and this has no answer, exactly as carter_clone_punish has none. One full heart (damage 2 of the
	# player's six halves). hype_loss stays true: no grab took a toll first, so the blast IS the toll, and
	# the Break gauge it drains is the thing the player failed to fill.
	# NOT bypass_invincibility: it closes no exploit, since the only way to be in i-frames is to have been
	# hit moments earlier and trading a heart to avoid a heart is not a trade. What it protects is the one
	# genuinely unfair case - being hit just before an undodgeable blast and eating both.
	&"computah_overload_blast": {"damage": 2},
	&"wrestler_charge": {"blockable": true, "weight": Weight.HEAVY},
	# Punching Carter or Josh hurts the player by design.
	&"wrestler_punish": {},
	&"mason_poo_blast": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	# Yellow rather than red, though a guard does absorb it: it lands on a marked spot, so the answer
	# is to be somewhere else by the time it does. No dash immunity - stepping out is the dodge.
	&"mason_nugget": {"blockable": true, "weight": Weight.LIGHT, "from_above": true, "dodge_tell": true},
	# Red, and told over Mason rather than over the landing spot: the floor marker already says where
	# it lands, the badge says the slam can be answered. Only Mason's called-in Carter uses this id.
	&"carter_elbow_drop": {"blockable": true, "weight": Weight.HEAVY, "from_above": true, "tell": true},
	# from_above because a funko's blast is a radius with no direction to face, exactly like the
	# nugget and the elbow drop above it. Without it the guard only answers a blast inside +/-60 deg
	# of facing, and facing auto-aims at the NEAREST figure while the one detonating usually is not
	# it - measured, a standing player parried 0-1 of 7-10 landing blasts. That made the red tell a
	# lie: it promised an answer the fight did not offer. Omni-blockable is what the attack already
	# was in every other respect.
	&"funko_blast": {"blockable": true, "weight": Weight.LIGHT, "from_above": true, "tell": true},
	&"bixby_fire_breath": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	# The ground wave an erupting crack sends out.
	&"bixby_quake_burst": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	# Swept beams, like the other ones: dashing through is the dodge.
	&"bixby_sonic_beam": {"dash_through": true, "dodge_tell": true},
	# Josh's cards.
	# A giant card slamming down on a third of the arena: it can only be moved out of.
	&"josh_card_fall": {"damage": 2, "dodge_tell": true},
	&"josh_card_bomb": {"blockable": true, "weight": Weight.LIGHT, "from_above": true},
	# Three in a row, each with its own tell; a parry negates but never staggers him.
	&"josh_card_throw": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	# Carter's Raging Demon. One clone rush: a held guard absorbs it heavily, a fresh press parries it.
	# Its origin is the player's own hurtbox centre, inside PlayerDefense.block_omni_radius, so any
	# facing can answer it - the check is timing, not aim. The yellow feints never reach here at all,
	# and the lights are drawn by the clone, not ParryTell, so `tell` stays false.
	# It lands inside the i-frames on purpose: fifteen of these come 0.70 s apart, and being hit must
	# never hand the player the clones behind it for free. Every one of them counts.
	&"carter_clone_rush": {"blockable": true, "weight": Weight.HEAVY, "bypass_invincibility": true},
	# The clone right after a feint the player bit on. Nothing answers it - that is the whole point -
	# so it is neither blockable nor parryable. The bait was the mistake; this is the bill.
	&"carter_clone_punish": {"weight": Weight.HEAVY, "bypass_invincibility": true},
	# Carter's Beam Rush, his second attack. The real Carter materialises beside the player and strikes:
	# a held guard absorbs it heavily, a fresh press parries it, and only a parry feeds his Break gauge,
	# which is the only thing that ends the attack.
	# Its origin is the player's own hurtbox centre, inside PlayerDefense.block_omni_radius, so any
	# facing answers it. The player is FREE to move here, unlike the barrage, so a facing test would make
	# it an aiming check instead of a timing one.
	# NOT bypass_invincibility, and that is the difference from carter_clone_rush. The barrage roots the
	# player and every one of its fifteen clones must count; here the player can walk out of a strike, so
	# the standard i-frames are what keeps twelve strikes 0.50 s apart from being unsurvivable.
	&"carter_teleport_strike": {"blockable": true, "weight": Weight.HEAVY, "tell": true},
	# The four clones' beams, live from the charge to the end. No badge on purpose: a tell is for
	# something about to change, and these are 96 px of light standing still for ten seconds. No
	# dash_through either - a dash across one is MEANT to cost, since that is what stops the player
	# outrunning the attack.
	&"carter_beam": {},
	# Anything that hits without an id: exactly the old behaviour.
	&"untagged": {},
}

static var warned_ids := {}


static func get_attack(id: StringName) -> Dictionary:
	if not ATTACKS.has(id):
		if not warned_ids.has(id):
			warned_ids[id] = true
			push_warning("AttackCatalog: unknown attack id '%s', treated as untagged" % id)
		id = &"untagged"
	return DEFAULTS.merged(ATTACKS[id], true)
