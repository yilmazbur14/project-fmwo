extends RefCounted

# How every attack that can hurt the player can be defended against, keyed by attack id. Attackers
# pass the id to the player through HitInfo; PlayerDefense decides the outcome from these entries.
# Keys left out of an entry take the value in DEFAULTS:
#     damage                half-hearts on a hit; 0 for a grab, whose caller does the rest
#     blockable             a guard facing it absorbs it, and a fresh press parries it
#     parryable             a fresh press parries it even though a held guard can't absorb it
#     weight                the stamina a block costs
#     tell                  it warns over the boss's head while it winds up (ParryTell)
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
	&"computah_laser": {"dash_through": true},
	# Boss 2. Computah's pounce is the grab at the end of his chase: a held guard does not stop it,
	# a parry does and sparks him out early, and a dash through it is a perfect dodge.
	&"computah_chase": {"damage": 0, "grab": true, "parryable": true, "parry_stagger": true, "tell": true, "dash_through": true},
	# The junk Greyson throws over the chase, and the phase-two burst that costs more to block. A
	# parry negates either but never staggers him - he is standing still to begin with, Josh's rule.
	&"greyson_throw": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	&"greyson_throw_hard": {"blockable": true, "weight": Weight.HEAVY, "tell": true},
	# The five-hit combo a caught player is put through. It is unblockable BY CONSTRUCTION rather
	# than by a new kind of lock: the player keeps the parry-only lock, and with nothing blockable or
	# parryable there is nothing for the guard to answer. The first four deal nothing and the fifth
	# launches. Neither costs hype - the pounce that caught them already did, exactly as Eric's
	# squeeze leaves the cost on his grab.
	&"greyson_combo_jab": {"damage": 0, "bypass_invincibility": true, "hype_loss": false},
	&"greyson_combo_finish": {"damage": 3, "bypass_invincibility": true, "hype_loss": false},
	# Phase two with Greyson gone: a landed pounce has nobody to hand the player to, so Computah
	# slams them himself for what the fifth punch would have dealt.
	&"computah_slam": {"damage": 3, "bypass_invincibility": true, "hype_loss": false},
	&"wrestler_charge": {"blockable": true, "weight": Weight.HEAVY},
	# Punching Carter or Josh hurts the player by design.
	&"wrestler_punish": {},
	&"mason_poo_blast": {"blockable": true, "weight": Weight.LIGHT},
	&"mason_nugget": {"blockable": true, "weight": Weight.LIGHT, "from_above": true},
	&"carter_elbow_drop": {"blockable": true, "weight": Weight.HEAVY, "from_above": true},
	&"funko_blast": {"blockable": true, "weight": Weight.LIGHT},
	&"bixby_fire_breath": {"blockable": true, "weight": Weight.LIGHT},
	# The ground wave an erupting crack sends out.
	&"bixby_quake_burst": {"blockable": true, "weight": Weight.LIGHT},
	# Swept beams, like the other ones: dashing through is the dodge.
	&"bixby_sonic_beam": {"dash_through": true},
	# Josh's cards.
	# A giant card slamming down on a third of the arena: it can only be moved out of.
	&"josh_card_fall": {"damage": 2},
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
