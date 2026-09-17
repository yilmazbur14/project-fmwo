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
	&"eric_whirlwind": {"blockable": true, "weight": Weight.HEAVY, "parry_stagger": true, "tell": true},
	&"eric_thrown_sword": {"blockable": true, "weight": Weight.HEAVY},
	&"eric_quake_ring": {"dash_through": true},
	# A guard doesn't stop the grab, but a parry does, and it staggers him.
	&"eric_bear_hug_grab": {"damage": 0, "dash_through": true, "grab": true, "parryable": true, "parry_stagger": true, "tell": true},
	# The player is held and can't defend; the grab already cost the hype.
	&"eric_bear_hug_squeeze": {"bypass_invincibility": true, "hype_loss": false},
	&"computah_rocket": {"blockable": true, "weight": Weight.LIGHT},
	&"computah_laser": {"dash_through": true},
	&"mech_shockwave": {"dash_through": true},
	&"wrestler_charge": {"blockable": true, "weight": Weight.HEAVY},
	# Punching Carter or Josh hurts the player by design.
	&"wrestler_punish": {},
	&"mason_poo_blast": {"blockable": true, "weight": Weight.LIGHT},
	&"mason_nugget": {"blockable": true, "weight": Weight.LIGHT, "from_above": true},
	&"carter_elbow_drop": {"blockable": true, "weight": Weight.HEAVY, "from_above": true},
	&"funko_blast": {"blockable": true, "weight": Weight.LIGHT},
	&"bixby_fire_breath": {"blockable": true, "weight": Weight.LIGHT},
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
