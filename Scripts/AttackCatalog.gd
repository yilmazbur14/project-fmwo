extends RefCounted

# How every attack that can hurt the player can be defended against, keyed by attack id. Attackers
# pass the id to the player through HitInfo; PlayerDefense decides the outcome from these entries.
# Keys left out of an entry take the value in DEFAULTS:
#     damage                half-hearts on a hit; 0 for a grab, whose caller does the rest
#     blockable             a fresh press parries it, and a guard facing it absorbs it while
#                           PlayerDefense.BLOCKING_ENABLED is on (it ships off, so nothing is absorbed)
#     parryable             a fresh press parries it even though a held guard can't absorb it
#     weight                the stamina a block costs, with blocking on
#     tell                  it warns over the boss's head while it winds up (ParryTell)
#     dodge_tell            it warns in yellow instead: don't parry it, dodge it (ParryTell)
#     parry_stagger         a parry may stagger the boss (its can_parry_stagger() decides)
#     from_above            blockable from any facing
#     dash_through          dash immunity dodges it
#     grab                  a hit means the caller grabs the player
#     bypass_invincibility  lands inside the i-frames
#     hype_loss             a hit costs hype
#     no_perfect_dodge      never pays a PERFECT DODGE: a hazard lying still on the floor, which a dash
#                           may still carry the player safely across, but nobody dodged it
#     parry_pass_through    a parry or a block negates it without stopping it; it flies on, whole,
#                           through the player, and its own script keeps it off them for the rest of
#                           that pass

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
	"no_perfect_dodge": false,
	"parry_pass_through": false,
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
	# The red bear hug: only a parry answers it. A dash gives no immunity, and there is no stepping out
	# of it either: its rush homes on the player from anywhere in the ring (EricBearHug).
	&"eric_bear_hug_grab_v2": {"damage": 0, "grab": true, "parryable": true, "parry_stagger": true, "tell": true},
	# The yellow bear hug, a shoulder charge on the same art and timing: no guard or parry stops it, a
	# dash goes through it.
	&"eric_shoulder_charge": {"dash_through": true, "dodge_tell": true},
	# The sparring dummy in the controls room, which teaches the same red-and-yellow vocabulary Eric's
	# fight is built on, one attack each.
	# Red: the padded arm. HEAVY is deliberate - with blocking on, three blocks in a row empty the bar,
	# so the guard break teaches itself - and a parry leaves the arm out, which is the punish window.
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
	# no_perfect_dodge: a pod lies still on the floor, and dashing past something that never moves is not
	# a dodge (the user's rule, 2026-09-23). ComputahMineScript already skips the dodge ghost; this holds
	# whatever reports it.
	&"computah_mine": {"damage": 0, "grab": true, "hype_loss": false, "no_perfect_dodge": true},
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
	# Mason himself while he lays a poo line, from the squat that starts it to the step that ends it
	# (MasonScript.set_contact_live). A body, not a wind-up, so no guard and no badge: he is his own
	# warning. A dash through him is the way past, and for a player who stays in him the i-frames are
	# what space the hits out.
	&"mason_poo_contact": {"dash_through": true},
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
	# The quake rings his pounds and his spin send rolling out across the floor from under him:
	# eric_quake_ring's flags. The crest is its own warning, and it moves, so a dash through it pays a
	# PERFECT DODGE.
	&"bixby_quake_ring": {"dash_through": true},
	# The Inferno's shower: mason_nugget's flags exactly, for the same reasons. It comes down on a marked
	# spot, so the answer is to be elsewhere, and a guard still takes it from any facing. Its marker is
	# the warning, so dodge_tell stays unwired.
	&"bixby_fireball": {"blockable": true, "weight": Weight.LIGHT, "from_above": true, "dodge_tell": true},
	# The Inferno's breath, one cone down roughly three quarters of the ring: josh_card_fall's shape. It can
	# only be moved out of, into the upper corners beside him, and the yellow ring on his mouth times the
	# wind-up. No dash_through: a dash is a way out of it, not through it.
	&"bixby_inferno": {"damage": 2, "dodge_tell": true},
	# The embers it leaves burning: floor to stay off, not an attack, so no guard and no badge - the fire
	# is its own warning. A dash through one is the way across, and for a player who stands in one the
	# i-frames are what space the hits out, as with mason_poo_contact. It lies still on the floor, so a
	# dash across it is safe but pays no PERFECT DODGE (no_perfect_dodge, the user's rule, 2026-09-23).
	&"bixby_ember": {"dash_through": true, "no_perfect_dodge": true},
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
	# Carter's Beam Rush, his second attack. Once in it the real Carter materialises beside the player and
	# strikes: a held guard absorbs it heavily and a fresh press parries it.
	# Its origin is the player's own hurtbox centre, inside PlayerDefense.block_omni_radius, so any
	# facing answers it. The player is FREE to move here, unlike the barrage, so a facing test would make
	# it an aiming check instead of a timing one.
	# NOT bypass_invincibility, and that is the difference from carter_clone_rush. The barrage roots the
	# player and every one of its fifteen clones must count; here the player can walk out of a strike.
	&"carter_teleport_strike": {"blockable": true, "weight": Weight.HEAVY, "tell": true},
	# Carter's Messatsu: charged in the dark, fired as the lights come back, one hit as it lands and one per
	# surge after. Each hit is its own parry - a held guard absorbs it heavily, a fresh press parries it -
	# and its origin is the player's own hurtbox centre, so any facing answers it: timing, not aim.
	# bypass_invincibility because the hits come 0.50 s apart against 1.0 s of i-frames: without it one
	# missed hit would swallow the next one AND its parry. Walking or dashing out of the beam caps the bill.
	# No dash_through: the only dodge is not being in it.
	&"carter_messatsu_beam": {"blockable": true, "weight": Weight.HEAVY, "tell": true, "bypass_invincibility": true},
	# The Beam Rush's four beams: the Messatsu's look, but nothing guards or parries them, by the user's
	# call - they are escaped, so their badge is the yellow one. They hurt on contact for as long as they
	# are out, so the i-frames are what space their hits, and a dash's immunity carries the player through
	# one: a timed dash across a line is a way out as well as walking.
	&"carter_rush_beam": {"dash_through": true, "dodge_tell": true},
	# Matt's Ezreal set. His bolts come back off the ropes from every side and the facing is aimed at
	# him, so their origin is the player's own hurtbox centre and any facing answers them, as Carter's
	# clones are answered. A parry or a block lets them fly on through the player: blocking stops
	# nothing, so it can never beat parrying, and it still costs the stamina.
	&"matt_mystic_shot": {"blockable": true, "weight": Weight.LIGHT, "tell": true, "parry_pass_through": true},
	# The wave passes through the player whatever they do - a hit consumes a bolt but never a wave.
	&"matt_trueshot": {"blockable": true, "weight": Weight.HEAVY, "tell": true, "dash_through": true, "parry_pass_through": true},
	# The yell in his punish window: no guard or parry stops it, a dash through it or distance does.
	&"matt_yell": {"dash_through": true, "dodge_tell": true},
	# Matt's Glass Row: the bed of glass his stomps bring down on the last two rows, reached only by being
	# knocked into it while held. Nothing answers it - the player is sealed - so it carries no tell of
	# either colour: the glass on the floor is its own warning. A whole heart, and inside the i-frames,
	# because it is the bill for four missed arrows and must arrive.
	&"matt_glass": {"damage": 2, "bypass_invincibility": true},
	# Captain Burak (boss 1, the tutorial). His powder kegs: once he has loaded, every keg still standing
	# is shot and fills the whole arena. Nothing answers it - the answer was the punches that broke the kegs
	# in time - so it carries no tell of either colour, and it lands inside the i-frames because the bill is
	# half a heart per keg left, one blast after another.
	&"burak_barrel_blast": {"bypass_invincibility": true},
	# His pistol pair: a guard absorbs a shot lightly, a fresh press parries it, and only a parry pays toward
	# his Break (half the gauge). Inside the i-frames so a hit on the first never swallows the second's parry.
	&"burak_shot": {"blockable": true, "weight": Weight.LIGHT, "tell": true, "bypass_invincibility": true},
	# His cutlass string: parry-only like Eric's red bear hug - a held guard is not an answer - and a dash
	# through it is the dodge. The swings are 1.10 s apart, past the i-frames, so each is its own read.
	&"burak_cutlass": {"parryable": true, "tell": true, "dash_through": true},
	# Danny (boss 7). His Sumo Smash: he tracks the player from the air, latches, and comes down on a marked
	# spot. Red, told by the tracking shadow and a badge over the spot, as Mason's called-in Carter is: a held
	# guard takes it heavily from any facing, a fresh press parries it, a dash timed to the landing goes through
	# it. Five land 0.90 s apart, inside the 1.0 s i-frames, so a hit buys the next one.
	&"danny_butt_slam": {"blockable": true, "weight": Weight.HEAVY, "from_above": true, "tell": true, "dash_through": true},
	# The quake ring each landing sends rolling out: bixby_quake_ring's flags.
	&"danny_quake_ring": {"dash_through": true},
	# His Sumo Headbutt at a player his worms have rooted. Parry-only: a guard held through
	# the wind-up must not beat the read. A whole heart; a parry bonks him dizzy. The root took the dash away.
	&"danny_headbutt": {"damage": 2, "parryable": true, "parry_stagger": true, "tell": true},
	# Greyson's thrown weight plates, off the ropes three times. His parryable attack and the only thing that
	# builds his daze meter. Parry-only (a held guard is hit); the origin is the player's own hurtbox centre, so
	# a plate coming back off a rope is answered from any facing; a dash goes through it.
	&"greyson_plate": {"parryable": true, "tell": true, "dash_through": true},
	# The eruption his barbell slam plants under the player: moved out of, or dashed through as it goes off
	# (a PERFECT DODGE). Never parried. The zone on the floor is its warning; the yellow ring its last beat.
	&"greyson_eruption": {"damage": 2, "dodge_tell": true, "dash_through": true},
	# Greyson's final brawl (GreysonFinalBrawl): the player is rooted and answers each punch with one input.
	# The hooks are slipped (left hook LEFT, right hook RIGHT, under a gold arrow the brawl draws itself);
	# nothing guards or parries them. Every brawl punch lands inside the i-frames: each one is its own read.
	&"greyson_brawl_hook_l": {"bypass_invincibility": true},
	&"greyson_brawl_hook_r": {"bypass_invincibility": true},
	# The straight, under the red badge: only a parry answers it. Its origin is the player's own hurtbox centre.
	&"greyson_brawl_straight": {"parryable": true, "tell": true, "bypass_invincibility": true},
	# The same straight once the player has answered it with anything but the guard: the first answer decides,
	# so a guard press after a wrong one can't parry it.
	&"greyson_brawl_straight_unguarded": {"bypass_invincibility": true},
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
