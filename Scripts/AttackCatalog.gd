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
#     dash_immunity         seconds a dash is immune to this attack; 0 takes DASH_IMMUNITY_TIME

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
	"dash_immunity": 0.0,
}

const ATTACKS := {
	&"eric_quake_wave": {"blockable": true, "weight": Weight.LIGHT},
	&"eric_whirlwind": {"blockable": true, "weight": Weight.HEAVY},
	# A parry flings the sword back at him, and it staggers him where he threw it when it arrives. It
	# only ever hurts where it lands, coming down point first on its mark, so it has no side to face.
	&"eric_thrown_sword": {"blockable": true, "weight": Weight.HEAVY, "parry_stagger": true, "tell": true, "from_above": true},
	&"eric_quake_ring": {"dash_through": true},
	# A guard doesn't stop the grab, but a parry does, and it staggers him.
	&"eric_bear_hug_grab": {"damage": 0, "dash_through": true, "grab": true, "parryable": true, "parry_stagger": true, "tell": true},
	# The player is held and can't defend; the grab already cost the hype.
	&"eric_bear_hug_squeeze": {"bypass_invincibility": true, "hype_loss": false},
	# Eric's reworked fight (EricPacing V2). Red is a parry, yellow a dodge.
	# The slam's waves, with the standard red tell timing the read. A whole heart since 2026-10-05: his
	# greatsword through the floor is the fight's most readable hit, so it is the one that costs most.
	&"eric_quake_wave_v2": {"damage": 2, "blockable": true, "weight": Weight.LIGHT, "tell": true},
	# The whirlwind's lunges, behind a yellow wind-up: dashed through, or blocked at a heavy cost.
	&"eric_whirlwind_v2": {"blockable": true, "weight": Weight.HEAVY, "dash_through": true, "dodge_tell": true},
	# The red bear hug: only a parry answers it. A dash gives no immunity, and there is no stepping out
	# of it either: its rush homes on the player from anywhere in the ring (EricBearHug).
	&"eric_bear_hug_grab_v2": {"damage": 0, "grab": true, "parryable": true, "parry_stagger": true, "tell": true},
	# The yellow bear hug, a shoulder charge on the same art and timing: no guard or parry stops it, a
	# dash goes through it. A whole heart since 2026-10-06, when a parried red hug began paying a POW's mash:
	# the charge he leads with more often (EricPacing's hug_yellow_chance) is the one that costs.
	&"eric_shoulder_charge": {"damage": 2, "dash_through": true, "dodge_tell": true},
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
	# Mason's Nugget Fastball (MasonPitch): pitched where the player will be when it arrives, under the strong red badge
	# that goes up as he comes set, 0.42 s before contact. A fresh press parries it from any facing (origin: the player's
	# own hurtbox centre) and bats it back into his head, a HOME RUN. No dash_through: a dash only helps by leaving the line
	# after the release. A full heart, as Danny's red reads are: the fight's one read the feet can't answer, and at half a
	# heart the model player cleared him at 100% (the 2026-10-04 calibration, scratchpad tuning_1004/mason).
	&"mason_fastball": {"damage": 2, "blockable": true, "weight": Weight.LIGHT, "tell": true, "parry_stagger": true},
	# His changeup: the same flags and damage; its own rocking wind-up tells it, and it lands 0.64 s after the badge.
	&"mason_changeup": {"damage": 2, "blockable": true, "weight": Weight.LIGHT, "tell": true, "parry_stagger": true},
	# The quick pitch after a bitten hesitation (carter_clone_punish's rule): nothing answers it, no badge. Half a heart.
	&"mason_quick_pitch": {"weight": Weight.LIGHT},
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
	# The ground wave an erupting crack sends out.
	&"bixby_quake_burst": {"blockable": true, "weight": Weight.LIGHT, "tell": true},
	# Swept beams, like the other ones: dashing through is the dodge. A full heart since the tuning round of 2026-10-04
	# (difficulty 7), as are his rings and his shower.
	&"bixby_sonic_beam": {"damage": 2, "dash_through": true, "dodge_tell": true},
	# The quake rings his pounds and his spin send rolling out across the floor from under him:
	# eric_quake_ring's flags, at a full heart. The crest is its own warning, and it moves, so a dash through it pays a
	# PERFECT DODGE.
	&"bixby_quake_ring": {"damage": 2, "dash_through": true},
	# The Inferno's shower: mason_nugget's flags, for the same reasons, at a full heart. It comes down on a marked
	# spot, so the answer is to be elsewhere, and a guard still takes it from any facing. Its marker is
	# the warning, so dodge_tell stays unwired.
	&"bixby_fireball": {"damage": 2, "blockable": true, "weight": Weight.LIGHT, "from_above": true, "dodge_tell": true},
	# The Inferno's breath, one cone down roughly three quarters of the ring. It can only be moved out of,
	# into the upper corners beside him, and the yellow ring on his mouth times the wind-up. No
	# dash_through: a dash is a way out of it, not through it.
	&"bixby_inferno": {"damage": 2, "dodge_tell": true},
	# The embers it leaves burning: floor to stay off, not an attack, so no guard and no badge - the fire
	# is its own warning. A dash through one is the way across, and for a player who stands in one the
	# i-frames are what space the hits out, as with mason_poo_contact. It lies still on the floor, so a
	# dash across it is safe but pays no PERFECT DODGE (no_perfect_dodge, the user's rule, 2026-09-23).
	&"bixby_ember": {"dash_through": true, "no_perfect_dodge": true},
	# Beast Bixby's Flyby (BixbyBeastFlyby): the wall of fire falling at the front of each pass. It moves, so a dash
	# through it is dodged and a PERFECT DODGE (a Break read); nothing guards or parries it. Yellow if it had a badge,
	# but the floor projection is its warning, so none is raised (bixby_fireball's rule). A spot hurts for less than
	# the i-frames, so it lands once a pass at most.
	&"bixby_flyby_breath": {"dash_through": true, "dodge_tell": true},
	# The floor it leaves burning behind the front for flyby_burn_time: floor to keep off, as the embers are. A dash
	# carries the player across it, but it lies still, so it pays no PERFECT DODGE.
	&"bixby_flyby_fire": {"dash_through": true, "no_perfect_dodge": true},
	# Josh's Wild Cards: fifteen at once, three down each of the lanes his clones laid on the floor. Nothing
	# guards or parries them, so their badge is the yellow ring: the answer is to stand in a gap or walk out
	# of the lanes, or to dash through a card - the dash's immunity carries the player through it, for a
	# PERFECT DODGE that gives the dash back. A hit's i-frames cover whatever else of the volley reaches the
	# player inside them. A whole heart (the user, 2026-10-04), as are all of his.
	&"josh_wild_card": {"damage": 2, "dash_through": true, "dodge_tell": true},
	# Josh's Hand Slam: a card hand tracks the player from the air, locks under the red badge and comes down on
	# the marked spot. Parry-only, like Eric's red bear hug - blocking ships off, and a held guard must never
	# absorb it - and a dash timed to the landing goes through it. Its origin is the player's own hurtbox centre
	# (JoshHandSlamHit), so any facing answers it. Six land 0.81 s apart, inside the 1.0 s i-frames, so a hit
	# buys the next one. A whole heart.
	&"josh_hand_slam": {"damage": 2, "parryable": true, "tell": true, "from_above": true, "dash_through": true},
	# Josh's Gun Hands, inside his Wild Cards: the two hands, turned into finger guns at the sides of the ring, stop and
	# charge, then fire a laser across it along the band they showed. carter_rush_beam's flags: nothing guards or parries
	# it, so its badge is the yellow one - the answer is to step out of the band, or a dash through the beam, which is a
	# PERFECT DODGE. It appears and is gone, so it pays one (not no_perfect_dodge). A whole heart.
	&"josh_gun_beam": {"damage": 2, "dash_through": true, "dodge_tell": true},
	# Josh's Portal Monte: he dives into a portal and bursts out of one of three small ones round the locked player, one
	# at a time, and the red one is really him. Parry-only, like his Hand Slam: the origin is the player's own hurtbox
	# centre (JoshMonteFigure), so any facing answers it. parry_stagger only picks the strong red badge - he has no
	# can_parry_stagger, and the Monte staggers him itself on the PARRIED result. As Carter's clones, none of them stop
	# at the i-frames, so a hit never hands over the bursts behind it. A whole heart.
	&"josh_monte_strike": {"damage": 2, "parryable": true, "tell": true, "parry_stagger": true, "bypass_invincibility": true},
	# The burst right after a fake the player bit on (carter_clone_punish's rule): nothing answers it. Half a heart, so
	# a first Portal Monte isn't the whole bar (the user, 2026-10-04).
	&"josh_monte_punish": {"weight": Weight.HEAVY, "bypass_invincibility": true},
	# Carter's Raging Demon. One clone rush: a held guard absorbs it heavily, a fresh press parries it.
	# Its origin is the player's own hurtbox centre, inside PlayerDefense.block_omni_radius, so any
	# facing can answer it - the check is timing, not aim. The yellow feints never reach here at all,
	# and the lights are drawn by the clone, not ParryTell, so `tell` stays false.
	# It lands inside the i-frames on purpose: fifteen of these come 0.70 s apart, and being hit must
	# never hand the player the clones behind it for free. Every one of them counts.
	&"carter_clone_rush": {"blockable": true, "weight": Weight.HEAVY, "bypass_invincibility": true},
	# The clone right after a feint the player bit on. Nothing answers it - that is the whole point -
	# so it is neither blockable nor parryable. The bait was the mistake; this is the bill: a whole heart
	# since 2026-10-05, so the pale X is the read that matters most in his barrage.
	&"carter_clone_punish": {"damage": 2, "weight": Weight.HEAVY, "bypass_invincibility": true},
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
	# nothing, so it can never beat parrying, and it still costs the stamina. A whole heart since 2026-10-05, his 7/10 by
	# his own kit once every window paid a finisher again.
	&"matt_mystic_shot": {"damage": 2, "blockable": true, "weight": Weight.LIGHT, "tell": true, "parry_pass_through": true},
	# The wave passes through the player whatever they do - a hit consumes a bolt but never a wave. His heavy shot, a
	# whole heart (2026-10-05, his 7/10 by his own kit once every window paid a finisher again).
	&"matt_trueshot": {"damage": 2, "blockable": true, "weight": Weight.HEAVY, "tell": true, "dash_through": true, "parry_pass_through": true},
	# The yell in his punish window: no guard or parry stops it, a dash through it or distance does.
	&"matt_yell": {"dash_through": true, "dodge_tell": true},
	# Matt's Glass Row: the bed of glass his stomps bring down on the last two rows, reached only by being
	# knocked into it while held. Nothing answers it - the player is sealed - so it carries no tell of
	# either colour: the glass on the floor is its own warning. A whole heart, and inside the i-frames,
	# because it is the bill for four missed arrows and must arrive.
	&"matt_glass": {"damage": 2, "bypass_invincibility": true},
	# Matt's Echo Roars (MattEchoRoars): each roar and its echo is a ring of sound over the whole ring, parried, and it
	# passes on through. Every ring is its own read, so all of them land inside the i-frames: eating one never buys
	# the next (Carter's barrage's rule).
	&"matt_echo": {"parryable": true, "tell": true, "parry_pass_through": true, "bypass_invincibility": true},
	# The echo behind a pale X the player pressed on (carter_clone_punish's rule): nothing answers it, and it wears
	# no badge. A whole heart (half until 2026-10-05).
	&"matt_echo_punish": {"damage": 2, "weight": Weight.HEAVY, "bypass_invincibility": true},
	# The BOOMBURST that ends each string: too loud to parry, dashed through. Its dash window is the immunity
	# itself, since only the first touch counts. A heart and a half (a whole heart until 2026-10-05).
	&"matt_boomburst": {"damage": 3, "dash_through": true, "dodge_tell": true, "dash_immunity": 0.21, "bypass_invincibility": true},
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
	# Danny (boss 7). His Sumo Smash string: he tracks the player from the air, latches, and comes down on a marked
	# spot, told by the tracking shadow and a badge over the spot. The fifth and biggest: the one red slam and the
	# one quake ring. A fresh press as it lands bounces him off the fists onto his back (DannyBossOnBack); a dash
	# timed to the landing goes through it. A whole heart.
	&"danny_butt_slam": {"damage": 2, "parryable": true, "parry_stagger": true, "tell": true, "dash_through": true},
	# The quake ring the big one sends rolling out: bixby_quake_ring's flags.
	&"danny_quake_ring": {"dash_through": true},
	# His Sumo Headbutt at a player his worms have rooted. Parry-only: a guard held through
	# the wind-up must not beat the read. A whole heart; a parry bonks him dizzy. The root took the dash away.
	&"danny_headbutt": {"damage": 2, "parryable": true, "parry_stagger": true, "tell": true},
	# Danny's hop slams, all but the last of his Sumo Smash string: yellow, dodge them. Each throws his worms out round
	# where it lands (DannyBossSplash), so a step off the mark isn't enough: clear the splash, or dash through. From the
	# second on they home in on the player until he has all but landed (2026-10-07): those only a dash as he lands beats.
	&"danny_hop_slam": {"dash_through": true, "dodge_tell": true},
	# His ring-out belly bump: a charge along the player's line. A fresh press as the belly meets them holds their
	# ground (he rebounds, dizzy); a dash timed to it goes through. A hit carries them into the ropes.
	&"danny_belly_bump": {"parryable": true, "parry_stagger": true, "tell": true, "dash_through": true},
	# The ropes the bump drove them into: the rest of the heart. Carried and sealed, so it lands inside the
	# bump's own i-frames; the bump already cost the hype.
	&"danny_rope_slam": {"bypass_invincibility": true, "hype_loss": false},
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
	# so a guard press after a wrong one can't parry it. A full heart, the hooks' half doubled: the cannon arm is the heavy
	# punch, and missing its red badge costs like it (tuning, 2026-10-04).
	&"greyson_brawl_straight_unguarded": {"damage": 2, "bypass_invincibility": true},
	# His counter-jab when the guard comes up for his feint (the straight's wind-up, cocked but never charged): the
	# guard was spent on nothing, so nothing answers it. A heart and a half: biting the feint is the brawl's costly
	# mistake, costlier than missing the straight it mimics (tuning, 2026-10-04).
	&"greyson_brawl_counter": {"damage": 3, "bypass_invincibility": true},
	# Jordan's last phase, the Puppet Master: his dark maze with Greyson and Matt (JordanComboMaze). The player is
	# sealed for the whole of it, so nothing answers either, and both land inside the i-frames: the glass a wrong
	# arrow throws them onto is half a heart, and Greyson's beam down the path at a full meter a heart and a half.
	&"jordan_maze_glass": {"damage": 1, "bypass_invincibility": true},
	&"jordan_maze_beam": {"damage": 3, "bypass_invincibility": true},
	# His kegs with Burak and Danny (JordanComboKegs): Danny's butt slam on the centre. Its own entry, on the flags
	# danny_butt_slam had until Danny's addendum (2026-09-29) made his own fight's slam a whole heart: here it stays half.
	&"jordan_keg_slam": {"blockable": true, "weight": Weight.HEAVY, "from_above": true, "tell": true, "dash_through": true},
	# His portals with Josh and Eric (JordanComboPortals): Eric's planted greatsword shot up out of Josh's floor portals
	# as a spike. Nothing guards or parries it and it carries no badge: the portal opening under it is its warning, so
	# the answer is to step out of it, or to dash through it as it erupts (a PERFECT DODGE).
	&"jordan_portal_spike": {"damage": 1, "dash_through": true},
	# Jordan's attack 4, Carter + Mason's circle (JordanComboCircle): the clones' beams sweep the circle one after another,
	# a heart each; nothing guards, parries or dashes through them - running ahead of them is the answer - so no tell
	# (the aim lines are their warning) and the i-frames space the hits. Mason's bombs lie on the floor: half a heart
	# stepped in, a dash carries the player across, and lying still they never pay a PERFECT DODGE.
	&"jordan_circle_beam": {"damage": 2},
	&"jordan_circle_poo": {"dash_through": true, "no_perfect_dodge": true},
	# Jordan's phase 1 on the kaiju (JordanKaijuLayout.USE_KAIJU). Its Atomic Breath, a beam swept across the floor behind
	# a yellow ring: nothing guards it, a dash through it is the dodge. A whole heart.
	&"jordan_kaiju_breath": {"damage": 2, "dash_through": true, "dodge_tell": true},
	# The line of fire the breath leaves on the mat: a dash carries the player across, but lying still it never pays a
	# PERFECT DODGE.
	&"jordan_burn_line": {"dash_through": true, "no_perfect_dodge": true},
	# The stomp out of the sky under the strong red badge: a fresh press parries it from any facing (origin: the
	# player's own hurtbox centre) and knocks Jordan off; a dash through it is dodged too. A whole heart.
	&"jordan_kaiju_stomp": {"damage": 2, "parryable": true, "parry_stagger": true, "tell": true, "from_above": true, "dash_through": true},
	# The quake ring a dodged stomp sends out: bixby_quake_ring's flags.
	&"jordan_kaiju_quake": {"dash_through": true},
	# The tail whipped round after a dodged stomp, behind a yellow ring: dashed through, or stepped out of. A whole heart.
	&"jordan_kaiju_tail": {"damage": 2, "dash_through": true, "dodge_tell": true},
	# The figures it throws down from its head (JordanFunkoThrow): funko_blast's flags at a whole heart. Both its openings
	# pay the uppercut (the user, 2026-10-05 and 10-06), so three of them end his phase and its figures carry the fight.
	&"jordan_kaiju_funko": {"damage": 2, "blockable": true, "weight": Weight.LIGHT, "from_above": true, "tell": true},
	# Jordan's attack 5, Liam + Bixby's Elemental Wheel (JordanComboWheel). Fire: Bixby's fly-by curtain and the floor
	# burning behind it, the Flyby's flags, a heart each; the gap in it is the answer.
	&"jordan_wheel_breath": {"damage": 2, "dash_through": true, "dodge_tell": true},
	&"jordan_wheel_fire": {"damage": 2, "dash_through": true, "no_perfect_dodge": true},
	# Water: the thin wave under the yellow badge, dashed through standing (its immunity 0.21 s, as Liam's tsunami's). A heart.
	&"jordan_wheel_wave": {"damage": 2, "dash_through": true, "dodge_tell": true, "dash_immunity": 0.21},
	# Earth: the quake ring each slam sends out, half a heart; a heart on the magma double.
	&"jordan_wheel_ring": {"damage": 1, "dash_through": true},
	&"jordan_wheel_fire_ring": {"damage": 2, "dash_through": true},
	# Air: the bite under the red badge, parry-only, from any facing (its origin is the player's own hurtbox centre); a
	# parry never staggers him. The maw's swallow is a grab, and its one chomp lands through the i-frames and costs no hype.
	&"jordan_wheel_bite": {"damage": 3, "parryable": true, "tell": true},
	&"jordan_wheel_swallow": {"damage": 0, "grab": true},
	&"jordan_wheel_chomp": {"damage": 3, "bypass_invincibility": true, "hype_loss": false},
	# Water: the shark's snap once the wave is off the floor (the user, 2026-10-07): the jaws' bite, out of the water.
	&"jordan_wheel_breach": {"damage": 3, "parryable": true, "tell": true},
	# Liam's own phase, attack 1 (LiamTsunami): half-width waves rolling down from the top rope, one side at a time.
	# josh_hand_slam's and matt_trueshot's flags: parry-only, since blocking ships off and a held guard must never absorb
	# it, and a parried wave rolls on whole through the player (its own latch keeps it off them for that pass). A dash
	# through one is dodged, but a wave is taller than a dash can clear straight up: the seam's corners are the way.
	# Its dash immunity runs 0.21 s, not 0.18, to widen the corner zip; straight up still falls 23 px short. Half a heart:
	# a full heart for a day of the tuning round of 2026-10-04 made a first-timer's first Tsunami cost about all four
	# hearts (the user's call: soften it).
	&"liam_tsunami": {"parryable": true, "tell": true, "from_above": true, "dash_through": true, "parry_pass_through": true, "dash_immunity": 0.21},
	# Attack 2's tremor ridges (LiamTremorBlock): solid walls that hurt to touch. Nothing guards, parries or dashes
	# through them and they carry no badge: the cracks glowing across the ice are the warning. They lie still on the
	# floor, so a dash into one pays no PERFECT DODGE. A full heart since the tuning round of 2026-10-04 (difficulty 7), in
	# place of the Tsunami's.
	&"liam_tremor": {"damage": 2, "no_perfect_dodge": true},
	# Attack 3's fire tornados (LiamTornado): touching a core burns and flings the player out. Nothing answers it and
	# it stands still on the floor, so a dash into one pays no PERFECT DODGE.
	&"liam_fire_tornado": {"no_perfect_dodge": true},
	# Attack 3's fire quake rings (BixbyQuakeRingScript with Liam's settings): bixby_quake_ring's flags, a dash through
	# the band is the dodge.
	&"liam_fire_quake": {"damage": 2, "dash_through": true},
	# Attack 4's lunge out of the steam (LiamLunge): eric_bear_hug_grab's command grab, a reaction check on its badge.
	# It costs nothing itself (the impale that follows does), a held guard never stops it, a dash through it is dodged,
	# and it lands inside i-frames so a hit just before can't make the player safe from it.
	&"liam_lunge": {"damage": 0, "grab": true, "parryable": true, "tell": true, "dash_through": true, "bypass_invincibility": true},
	# The impale's burns (Bixby's fire on the player hung on his staff): eric_bear_hug_squeeze's flags, landing through
	# the last one's i-frames and costing no hype.
	&"liam_impale_burn": {"bypass_invincibility": true, "hype_loss": false},
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
