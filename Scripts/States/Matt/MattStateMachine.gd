extends Node

# Matt's fight, boss 4. Intro once, then a repeating cycle: Idle (a breath), then the next attack in
# attack_rotation, ending in Recover, his punish window: three landed hits daze him into the finisher. After a landed
# yell he idles a second and starts the next cycle.
#   The Ezreal set: MysticVolley -> TrueshotBarrage -> Spent -> EchoRoars -> Recover at HOME (echo_after_ezreal;
#   with it off, Spent -> Recover).
#   The Glass Row: GlassRow -> Recover where he stands, over the player (recover_spot).
#   The Echo Roars (the user's pick, 2026-10-04): strings of roars on his theme's beat, every ring a parry, each
#   string ended by BOOMBURSTs to dash through (echo_boombursts, two since 2026-10-06); phase two plays more strings.
#   No silent X in either phase since 2026-10-06 (echo_feints_phase_one, echo_feints_phase_two). MattEchoRoars, built
#   here rather than in his scene.
#   The Deafening Yell is a Glass Row with cycle_deafen on. Phase two starts from phase_two_ratio of his health down
#   (or at his first Break with phase_two_at_break on), only ever at a cycle boundary: once a plain Glass Row has
#   been seen, the next cycle is forced to be one with the yell - unless the last was a Glass Row, so two never come
#   together - and every Glass Row after it has the yell too. So the fight runs Ezreal set -> Glass Row and round
#   again, every Glass Row in phase two after the first plain one Deafening.
# EVERY WINDOW PAYS A FINISHER (MattScript.can_be_dazed, daze_in_recover, since 2026-10-05): three landed hits in
# Recover daze him into the plain finisher. A full Break gauge stops any of it dead - Broken, the window that pays out
# the tiered finisher, then Juggled if it does. Both are built here, not in his scene.
#
# THE DIFFICULTY DIAL IS tier(): his health's third, read by the Mystic casts and the booms, and locked
# at the top of each cycle with the plan (plan_next) so a hit landing mid-attack can't change what the
# rest of it does. The glass has a dial of its own on his health's share (G12), locked with it.
#
# THE GLASS ROW'S RULES (MattGlassRow):
#   G1  the root costs nothing and lands on the slam's step, never earlier.
#   G2  one boom at a time; the arrow shows from its birth; the window is at least 0.40 s at row F
#       (0.51 s dizzy), phase_two_charge_extra more in phase two, and grows each row down.
#   G3  the first press decides; a wrong one fails only that boom; presses between booms do nothing.
#   G4  the timing is the same whatever the answer.
#   G5  a fail knocks the player a row toward the glass; the knock that reaches it is the glass: 2 damage
#       once, the barrage ends and the player bounces back to the row in front of it. From row F three
#       fails are free over two rows of glass, two over three and one over four (G12).
#   G6  the glass can't be reached any other way: the player can't move, and it is gone before they are
#       free.
#   G7  the lock, pose, facing, prompt, wobble and FX all go back through one release().
#   G8  the wobble lengthens the charge, never changes a colour, and never touches the fight HUD, menus,
#       pause or lines; the input always takes the true direction, whatever the view shows.
#   G9  no yell in the fight's first Glass Row, and a mash passed means no wobble.
#   G10 the window opens where he stands, straight over the player, with the usual yell rules.
#   G11 phase two's booms come in phase_two_boom_sets sets with a stomp between each two, which brings
#       shards down onto the glass's front row, their shadows first. It lays no glass, so the glass never
#       moves under the player. The pattern is locked at the cycle's top.
#   G12 the fury lays glass_rows_by_share rows of glass by his health's share, locked at the cycle's top:
#       two above three quarters of it, three above half, four from half down. Glass past the drawn bed's
#       two rows grows on in front of it a row at a time.
#
# FAIRNESS, AND WHERE EACH RULE LIVES:
#   R1  a parry answers from any facing and one press parries everything in its window: the hit's
#       origin is the player's own hurtbox centre (the projectiles), and a success re-arms at once
#       (PlayerDefense).
#   R2  the coincidence guard: a Trueshot never latches while a bolt is about to arrive
#       (MattTrueshotBarrage).
#   R3  Spent holds the window - and so the yell - until no projectile is alive (MattSpent).
#   R4  bolts spawn at least 450 px out, so every one has its badge and more than half a second of
#       flight (MattMysticVolley).
#   R5  the lattice: no bolt ever skims a rope (MattMysticBoltScript).
#   R6  at most five bolts at once.
#   R7  every Matt hit respects the i-frames (AttackCatalog).
#   R8  the yell's throw happens only in Recover and lands inside the ropes, and his next bolt is at
#       least 1.75 s behind it: post_yell_beat plus a cast's teleport and wind-up.
#   R9  standing on a station still gets shot, answerable by a parry at the release or a dash.
#
# THE ECHO ROARS' RULES (MattEchoRoars and MattEchoRingScript), each held by its mode:
#   E1  two first touches in a row on the player are at least parry_window and a step apart however they walk -
#       a beat times v / (v + the walk's diagonal) - and a red ring and a BOOMBURST three beats (matt_echo_gaps).
#   E2  a ring's whole disc touches for echo_birth_disc_time: no pocket on or under him (matt_echo_disc).
#   E3  echo_ring_end_radius reaches every point of the player's floor from HOME, and the band can't be stepped
#       over (matt_echo_disc).
#   E4  one answer a ring, inside the i-frames; the parry re-armed echo_rearm_delay after every touch but a ghost's,
#       so a whiffed or late press never locks the next ring out, while mashing still loses (matt_echo_parry).
#   E5  the stamina bar held at echo_stamina_floor from the lead-in to the end of the outro (matt_echo_stamina).
#   E6  no X in either phase since 2026-10-06: with both feint knobs off no ghost, X or punish ever spawns
#       (matt_echo_feint). With a knob on: one X a string, never the instance's first roar, locked at the cycle's
#       top (plan_echo); a press from echo_bite_grace past the ring before it to echo_bite_grace past its own bites,
#       and its echo is a punish.
#   E7  badge leads: a roar's echo_red_lead_beats, a string's first roar's echo_first_lead_beats, the BOOMBURST's
#       echo_yellow_lead_beats in yellow; an X's the same as the red it stands in for (matt_echo).
#   E8  nothing else of his alive under the rings: Spent and the Glass Row's release() see to it (matt_echo).
#   E9  his badges and Xs over his crown at HOME, whole in the view and clear of the boss bar (matt_badge).
#
# Every wait in this fight is a Timer, a Physics_Update accumulator or a node-bound tween, so a pause
# and a finisher's freeze hold all of it. Nothing may use get_tree().create_timer() or a tree-level
# create_tween().

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var MattCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer
@export var beat_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const BOLT_SCRIPT := preload("res://Scripts/MattMysticBoltScript.gd")
const WAVE_SCRIPT := preload("res://Scripts/MattTrueshotScript.gd")
const ECHO_RING_SCRIPT := preload("res://Scripts/MattEchoRingScript.gd")
const MattBroken := preload("res://Scripts/States/Matt/MattBroken.gd")
const MattJuggled := preload("res://Scripts/States/Matt/MattJuggled.gd")
const MattEchoRoars := preload("res://Scripts/States/Matt/MattEchoRoars.gd")
const PRE_FIGHT_DIALOGUE := "res://Dialogue/MattPreFight.dialogue"
const HAZARD_GROUP := "matt_hazard"

#WHERE THINGS ARE (feet points, px)
# His mark in the entrance, and where he recovers: the middle, so the walk to the window is fair from
# anywhere in the ring and "the other end of the ring" is well defined for the yell.
const HOME := Vector2(960, 620)
# The Trueshot's four stations, in the order he visits them: the middle of each side, facing in.
const STATIONS := [
	{"name": &"top", "feet": Vector2(960, 470), "normal": Vector2.DOWN},
	{"name": &"left", "feet": Vector2(250, 700), "normal": Vector2.RIGHT},
	{"name": &"bottom", "feet": Vector2(960, 955), "normal": Vector2.UP},
	{"name": &"right", "feet": Vector2(1670, 700), "normal": Vector2.LEFT},
]
# Where his feet may land on a Mystic cast, both edges included.
const STAND_RECT := Rect2(200, 470, 1520, 485)
# The inside edges of the ropes, as every other fight measures them.
const ROPES := Rect2(113, 114, 1692, 853)
# A badge over his crown in here is inside the boss bar, which fades while he is there.
const HUD_FADE_RECT := Rect2(680, -1080, 560, 1280)
# The 12 lattice headings a bolt flies on: 22.5, 45 and 67.5 degrees off each axis, never along one.
const LATTICE_STEP := 22.5
# The Glass Row's floor plan, from the user's sketch (2026-09-23): six rows across the ring under him,
# F at the top to A at the bottom. The player starts in F; the glass lies in the last rows, rope to rope,
# as many as his health gives it (glass_rows_by_share): B and A while he has over three quarters of it.
# Every px here is a y line or an x span; nothing else in the fight may hardcode a row.
const GLASS_ROW := {
	"station": Vector2(960, 350),      # his feet: top centre, above row F
	"lane": Vector2(677, 1241),        # the sketch's dashed lines: the middle third of the ropes
	"lane_x": 960.0,                   # where the player is put and the booms run
	"rows_top": 427.0,                 # row F's top edge
	"row_height": 90.0,                # about one player body length
	"row_names": ["F", "E", "D", "C", "B", "A"],
	"start_row": 0,                    # F
	"bed_rows": 2,                     # the drawn glass tile's height; more grows on in front a row at a time
	"glass_span": Vector2(113, 1805),  # rope to rope
}
# The player's origin stands this far over their soles.
const BODY_OVER_FEET := 36.0

#MYSTIC VOLLEY (seconds and px)
# His 8/10 (2026-10-06) came from here, up from [3, 4, 4] and five bounces: a bolt pays one read however many
# passes it makes, so more of them, living longer, is risk that never feeds his Break. Seven bounces at 750 still
# burst within 11.2 s, inside the bolt's SAFETY_LIFE.
@export var mystic_casts_by_tier: Array[int] = [5, 5, 5]
@export var mystic_max_alive := 5
@export var mystic_speed := 750.0
@export var mystic_bounces := 7
@export var mystic_hit_radius := 12.0
@export var mystic_windup := 0.45
@export var mystic_after := 0.15
@export var teleport_out := 0.15
@export var teleport_in := 0.15
# The ranges a spot may put his mouth at from the player, evenly spaced from x to y.
@export var mystic_range := Vector2(450, 750)
@export var mystic_range_steps := 5
# The last fallback lets the range down to here.
@export var mystic_range_floor := 380.0
@export var mystic_spot_gap := 350.0
@export var mystic_bolt_clearance := 150.0

#TRUESHOT BARRAGE (seconds, px and degrees)
@export var trueshot_charge := 0.90
@export var trueshot_lock_lead := 0.35
@export var trueshot_guard_hold := 0.2
@export var trueshot_speed := 1500.0
@export var trueshot_after := 0.35
@export var trueshot_max_turn := 67.5
# Half the wave's 270 px chord, so the crescent still visibly leaves him.
@export var trueshot_offset_max := 135.0
# Every heading the wave is drawn at (MattArtLayout.WAVE_ART_STEP), and a dead band the same share of a
# step as the plan's 13 degrees was of 22.5.
@export var trueshot_step := 11.25
@export var trueshot_hysteresis := 6.5
# The burst where the wave leaves him (R9): his body grown by this, back to the rope behind him and on
# to the wave's first position, live this long.
@export var trueshot_burst_margin := 30.0
@export var trueshot_burst_time := 0.1
# The coincidence guard's reach: a bolt this close to the player and this near straight at them.
@export var trueshot_guard_range := 220.0
@export var trueshot_guard_angle := 30.0
# The wave's middle starts this far along the heading from where it leaves him.
@export var trueshot_lead := 40.0
@export var trueshot_view_margin := 160.0

#THE GLASS ROW (seconds, px and counts)
@export var glass_stomp_tell := 0.45
@export var glass_root_time := 0.15
@export var glass_drag_time := 0.25
@export var glass_drag_hold := 0.10
@export var glass_fury_time := 1.40
@export var glass_segments := 9
@export var glass_shards_per_segment := 2
@export var glass_shard_fall := 0.40
# When in the fury the shards start falling, as shares of it.
@export var glass_shard_spawn := Vector2(0.05, 0.95)
@export var glass_winded := 0.50
@export var glass_clear_time := 0.50
@export var glass_clean_bonus := 1.0
@export var glass_hit_stop := 0.10
@export var glass_bounce_time := 0.13
@export var glass_edge_overshoot := 10.0
# How many rows of glass a Glass Row lays by his health share (the user, 2026-09-27): two above
# glass_row_shares.x of it, three above glass_row_shares.y, four from there down, all of them by the fury.
@export var glass_rows_by_share: Array[int] = [2, 3, 4]
@export var glass_row_shares := Vector2(0.75, 0.5)
# Phase two's Glass Row (the user, 2026-09-24): its booms in this many even sets, and between each two a
# short stomp - the knee up, the slam, then the stamping while shards fall onto the glass's front row. Its
# stomps laid a row of glass each until the user's 2026-09-27 playtest; now the fury lays all four.
@export var phase_two_boom_sets := 3
@export var glass_spread_tell := 0.20
@export var glass_spread_slam := 0.15
@export var glass_spread_time := 0.65
@export var glass_spread_shards_per_segment := 1
@export var stomp_shake := 14.0
@export var fury_shake := 5.0
@export var glass_shake := 18.0

#THE BOOMS
# The user's pace (2026-09-24, faster again after a playtest): fifteen a row at every tier, 29 physics steps
# (0.48 s) from one boom's birth to the next's. The window (the charge plus the flight to row F, 0.43 s as
# the steps fall) stays at the 0.40 s floor a person needs to read the arrow, so the gap is what gave; the
# wobble's longer charge pays for reading it through the phase-two wobble. The knock and the bounce are
# scaled with it. Phase two's charges, plain and dizzy, are phase_two_charge_extra longer on top.
@export var boom_counts_by_tier: Array[int] = [15, 15, 15]
@export var boom_charge := 0.32
@export var boom_charge_wobble := 0.43
# Phase two's booms charge this much longer, dizzy or not, and every window with them (the user, 2026-09-27):
# its four rows of glass leave one miss free from row F.
@export var phase_two_charge_extra := 0.05
@export var boom_speed := 1800.0
@export var boom_spawn_drop := 20.0
@export var boom_charge_drift := 50.0
@export var boom_gap := 0.04
@export var boom_knock_time := 0.10
@export var boom_hype_each := 4.0
@export var boom_hype_clean := 10.0
@export var boom_hit_shake := 10.0

#THE DEAFENING YELL
@export var phase_two_ratio := 0.5
# Phase two also starts at his first Break. It was on with the Break-only rule, where an unhyped first Break left him
# at about 52%; off since that rule went (2026-10-05), so his health alone starts it again.
@export var phase_two_at_break := false
@export var deafen_tell := 0.50
@export var deafen_time := 3.0
@export var deafen_after := 0.40
# RESIST!'s mash, bent by MashCurve. The user asked for it harder twice: on 2026-09-27 the drain went from 0.14
# to 0.20, taking the steady alternating presses a second that mash through the yell from 5.7 to 7.3; on
# 2026-09-28 the gain came down from 0.107 as the drain went up again, to 8.9 a second, 9 winning in 2.7 s and
# 10 in 2.0 s. The gain came down with it so the bar sits over 95% no longer than it did at 7.3. On 2026-10-04 the
# game's mashes were reset round about 6, 8 and 10 a second for the finisher's three bars, and RESIST! came down to
# the second: the drain from 0.215 to 0.175, so a steady 7.64 a second wins, 8 wins in 2.5 s (2.75 s from a
# reaction 0.25 s late), 9 in 2.0 s, and 7 never does.
@export var deafen_gain := 0.095
@export var deafen_drain := 0.175
@export var deafen_rumble := 4.0
@export var deafen_rumble_step := 0.12
@export var deafen_ring_every := 0.30

#THE ECHO ROARS (beats of his theme, seconds and px)
# His theme's tempo (art_source/music/matt_theme.rb, use_bpm 152): one beat is 60 / echo_bpm, 0.3947 s. The grid
# runs on game time, not the music's clock: a parry's hit-stop slows Engine.time_scale, and a grid locked to the
# music would drift off it after the first parry.
@export var echo_bpm := 152.0
# At least 1800, for E1: never a fairness lever.
@export var echo_ring_speed := 1800.0
@export var echo_ring_start_radius := 40.0
@export var echo_ring_end_radius := 1050.0
@export var echo_band := 14.0
@export var echo_birth_disc_time := 0.05
@export var echo_strings := 3
@export var echo_strings_phase_two := 4
# A string's beats from its first roar: roars on 0, 2 and 4, their echoes a beat behind, the BOOMBURSTs from
# echo_boomburst_beat, and the next string's first roar on echo_string_beats.
@export var echo_string_beats := 14.0
@export var echo_boomburst_beat := 8.0
# How many BOOMBURSTs end a string, echo_boomburst_spacing_beats apart from echo_boomburst_beat on. Past one, the
# string needs echo_string_beats at least three beats past the last (E1, a ring three beats from a BOOMBURST).
# Two since 2026-10-06 (one, in 11 beats, before): his 8/10 back once the X went, the gold dash being the read in his
# kit that costs most when missed.
@export var echo_boombursts := 2
@export var echo_boomburst_spacing_beats := 3.0
# How long each badge leads its ring, in beats: a roar's, a string's first roar's, the BOOMBURST's.
@export var echo_red_lead_beats := 1.0
@export var echo_first_lead_beats := 2.0
@export var echo_yellow_lead_beats := 1.5
# A press this soon after the ring before an X touches is a late press for that ring, not a bite; and one up to this
# long after the X's own touch still bites.
@export var echo_bite_grace := 0.10
# The parry is re-armed this long after every touch but a ghost's (Carter's messatsu_rearm_delay): a press up to here
# is a late one for the ring that touched, and never locks out the next. Kept short enough that mashing at 10 a
# second still has no credited press whose window reaches the next ring a beat later.
@export var echo_rearm_delay := 0.05
@export var echo_stamina_floor := 34.0
# The silent fake under the pale X (E6), by phase: one a string, never the instance's first roar. Both off since
# 2026-10-06, the user: "the parrying vs dodging is difficult enough". Phase one's was on from 2026-10-05.
@export var echo_feints_phase_one := false
@export var echo_feints_phase_two := false
# The Ezreal set runs straight on into the Echo Roars: Spent, with nothing of his left alive, hands over to them
# instead of to the window, so the set and the roars share the one window after them (MattSpent). On since
# 2026-10-05: two attacks to the window, his 7/10 by his own kit once every window paid a finisher again.
@export var echo_after_ezreal := true
@export var echo_gasp := 0.30
@export var echo_outro_cap := 1.5

#THE WOBBLE
@export var wobble_in := 0.6
@export var wobble_out := 0.8

#PACING (seconds)
@export var spent_min := 0.3
@export var spent_max := 3.0
# Back to 4.5 with the finisher in every window (2026-10-05); 3.0 while the Break-only rule had it pay three punches.
@export var recover_time := 4.5
@export var idle_beat := 0.9
@export var post_yell_beat := 1.0

#THE YELL (seconds and px)
# Off by the user's call (2026-10-04, "lets remove matts push away potentially when the player is hitting matt"):
# the yell's ring threw a player punching him across the ring. On, it plays as it did; off, no window plans one, and
# its draws off his rng still happen so every other seeded roll stays where it was (MattRecover._plan_yell).
@export var yell_counter_enabled := false
@export var yell_chance := 0.5
# The punish window it may first come in: never the fight's first.
@export var yell_from_window := 2
# The badge goes up the step after the punch that sets it off, 7 steps before that swing's arm is back, and a
# swing locks the player for 24 steps, dropping any dash pressed in it. At 0.40 a second punch chained as the arm
# came back - pressed before anyone could react to the badge - held them past the blast, and 93% of first-time
# yells landed (the 2026-10-04 playtest). 0.58 lets that chained punch end and a dash pressed after it still clear
# the ring from every punch spot (matt_yell_chain); a punch pressed once the badge has been seen, or a third
# chained swing, still gets the player hit.
@export var yell_tell := 0.58
@export var yell_start_radius := 60.0
@export var yell_radius := 270.0
@export var yell_band := 15.0
@export var yell_expand_time := 0.18
@export var yell_landing_time := 0.05
@export var yell_after := 0.35
@export var yell_whiff_bonus := 0.75
@export var yell_launch_time := 0.45
@export var yell_shake := 12.0
# Where the throw lands: out by the ropes on the player's side of him, and pushed on along the line
# from his mouth by this share of how far they were.
@export var launch_left_x := 155.0
@export var launch_right_x := 1763.0
@export var launch_follow := 0.5
@export var launch_y_range := Vector2(178, 903)

#THE SCREAM
# A punch short of the POW landed in his window, then a swing that whiffs or is refused, and he screams the
# player back at once (the user, 2026-09-27; MattRecover): no damage, no daze, no uppercut, and the combo's
# count gone with it. Off, he never screams, and a miss in his window is a miss like anywhere else. Off in the
# live game by the user's call (2026-10-05, "remove matts whiff screm shove"); the knob brings it back.
@export var scream_on_miss := false
# Where it leaves them: this many px from his mouth, just past the reach of his yell's ring.
@export var scream_clear := 320.0

#HUD
@export var hud_fade_alpha := 0.3

# Seedable, so a test or a bot can replay a fight.
var rng := RandomNumberGenerator.new()

var player_defeated := false
var cycles_started := 0
# His attacks in the order the cycles take them, the Ezreal set first. A var, so a test can pin it.
# The Echo Roars come chained after the Ezreal set (echo_after_ezreal), so they aren't a cycle of their own.
var attack_rotation: Array[String] = ["MysticVolley", "GlassRow"]
var last_attack := ""
var glass_rows_done := 0
# The Glass Row's hint goes up under the first boom of the fight, and never again.
var glass_hint_shown := false
# Whether phase two's forced opener has been played.
var deafen_opened := false
# Locked at the top of each cycle.
var cycle_casts := 3
var cycle_booms := 5
var cycle_deafen := false
# How many sets the cycle's Glass Row splits its booms into: phase two's stomps come between them.
var cycle_sets := 1
# The rows of glass the cycle's Glass Row comes to (glass_rows_for).
var cycle_glass_rows := 2
# The cycle's Echo Roars: how many strings, and each string's X - the slot of its silent roar, 0 to 2, or -1.
var cycle_echo_strings := 3
var cycle_echo_feints: Array[int] = []
# The fight's first BOOMBURST puts up the dash hint, and no other.
var echo_hint_shown := false
# What the cycle adds to every boom's charge: phase_two_charge_extra in phase two, else nothing.
var cycle_boom_charge_extra := 0.0
var windows_opened := 0
# His Breaks this fight (enter_broken): the first starts phase two (phase_two_at_break).
var breaks_taken := 0
# Where the next window opens and what extra time it gets: an attack that ends somewhere other than HOME
# sets them, and Recover takes them, which puts them back.
var recover_spot := HOME
var recover_bonus := 0.0
var warned := {}
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false


func _ready() -> void:
	rng.randomize()
	_check_glass_row()
	_add_down_state(MattBroken.new(), "Broken")
	_add_down_state(MattJuggled.new(), "Juggled")
	_add_echo_state()
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the scene is up: his entrance moves him, the player and the gates, and reads
		# all three off the fight scene.
		current_state.Enter.call_deferred()


# His body's own ready comes after this node's, so its hurtbox is looked up rather than read off it.
func _add_down_state(state: Node, state_name: String) -> void:
	state.name = state_name
	state.body = MattCharacterBody
	state.hurtbox = MattCharacterBody.get_node("Hurtbox")
	state.state_machine = self
	add_child(state)


# Attack 3 is built here rather than in his scene, as his Broken and Juggled are.
func _add_echo_state() -> void:
	var echo: Node = MattEchoRoars.new()
	echo.name = "EchoRoars"
	echo.body = MattCharacterBody
	add_child(echo)


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)


func on_child_transition(state, new_state_name):
	if state != current_state:
		return

	# Defeat, his or the player's, is terminal: a late timer must never restart the fight.
	if current_state == states.get("Defeated") or player_defeated:
		return

	var new_state = states.get(new_state_name)
	if !new_state:
		return

	if current_state:
		current_state.Exit()

	new_state.Enter()
	current_state = new_state


#THE LINES

# His entrance's lines call its beats, so it passes itself along to the dialogue.
func show_pre_fight_dialogue(intro: State) -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start", [intro])


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over
# their own end makes, made from here instead. pre_fight_over keeps it to once - the lines can end on
# their own inside the skip, on the beat it ran out.
func end_pre_fight_dialogue() -> void:
	if pre_fight_over:
		return
	if DialogueManager.dialogue_ended.is_connected(_on_dialogue_ended):
		DialogueManager.dialogue_ended.disconnect(_on_dialogue_ended)
	_on_dialogue_ended(null)


func _on_dialogue_ended(_dialogue: Object) -> void:
	pre_fight_over = true
	var intro = states.get("Intro")
	if intro:
		intro.lines_over()
	VsCard.play_intro(self, "matt", post_dialogue_pre_fight_timer.start)


# The fight opens on the cycle's own breath.
func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	MattCharacterBody.start_music()
	on_child_transition(current_state, "Idle")


#THE CYCLE

func start_cycle() -> void:
	cycles_started += 1
	var plan := plan_next()
	cycle_casts = mystic_casts()
	cycle_booms = boom_counts_by_tier[tier()]
	cycle_deafen = plan.deafen
	cycle_sets = phase_two_boom_sets if in_phase_two() else 1
	cycle_glass_rows = glass_rows_for(MattCharacterBody.get_health_ratio())
	cycle_boom_charge_extra = phase_two_charge_extra if in_phase_two() else 0.0
	if plan.deafen:
		deafen_opened = true
	if plan.attack == "EchoRoars":
		plan_echo(in_phase_two())
	last_attack = plan.attack
	on_child_transition(current_state, plan.attack)


# What the next cycle is, asked only by start_cycle: phase two's forced opener - a Glass Row with the
# yell, once a plain one has been seen and the last cycle wasn't one - or the attack after the last one in
# the rotation.
func plan_next() -> Dictionary:
	var two := in_phase_two()
	if two and glass_rows_done > 0 and not deafen_opened and last_attack != "GlassRow":
		return {"attack": "GlassRow", "deafen": true}
	var attack: String = attack_rotation[0]
	var at := attack_rotation.find(last_attack)
	if at >= 0:
		attack = attack_rotation[(at + 1) % attack_rotation.size()]
	return {"attack": attack, "deafen": attack == "GlassRow" and two and glass_rows_done > 0}


func next_attack() -> String:
	return plan_next().attack


# The Echo Roars' cycle lock: how many strings, and with the phase's feint knob on each string's X (E6) - one a
# string, never the instance's first roar - drawn off his rng. Drawn only for a cycle that plays it, so the other
# attacks' draws are the ones they always were.
func plan_echo(two: bool) -> void:
	cycle_echo_strings = echo_strings_phase_two if two else echo_strings
	cycle_echo_feints.clear()
	var feints_on: bool = echo_feints_phase_two if two else echo_feints_phase_one
	for s in cycle_echo_strings:
		if not feints_on:
			cycle_echo_feints.append(-1)
		elif s == 0:
			cycle_echo_feints.append(rng.randi_range(1, 2))
		else:
			cycle_echo_feints.append(rng.randi_range(0, 2))


func in_phase_two() -> bool:
	return (phase_two_at_break and breaks_taken >= 1) or MattCharacterBody.get_health_ratio() <= phase_two_ratio


# The difficulty dial: 0 above two thirds of his health, 1 above a third, 2 below.
func tier() -> int:
	var ratio: float = MattCharacterBody.get_health_ratio()
	if ratio > 0.66:
		return 0
	if ratio > 0.33:
		return 1
	return 2


func mystic_casts() -> int:
	return mystic_casts_by_tier[tier()]


# The rows of glass a Glass Row comes to at `ratio` of his health.
func glass_rows_for(ratio: float) -> int:
	if ratio > glass_row_shares.x:
		return glass_rows_by_share[0]
	if ratio > glass_row_shares.y:
		return glass_rows_by_share[1]
	return glass_rows_by_share[2]


# The window opens where the attack before it left him, with whatever extra time it earned; both go
# back to HOME and nothing as Recover takes them.
func take_recover_spot() -> Vector2:
	var spot := recover_spot
	recover_spot = HOME
	return spot


func take_recover_bonus() -> float:
	var bonus := recover_bonus
	recover_bonus = 0.0
	return bonus


#THE GLASS ROW'S FLOOR PLAN

# Where the player stands in row k: in the lane's middle with their soles on the row's middle line, so
# their origin is BODY_OVER_FEET above it.
func row_body_point(k: int) -> Vector2:
	var feet: float = GLASS_ROW.rows_top + GLASS_ROW.row_height * (k + 0.5)
	return Vector2(GLASS_ROW.lane_x, feet - BODY_OVER_FEET)


# The glass's first row: the fury lays all of the cycle's rows, the last ones.
func glass_top_row() -> int:
	return GLASS_ROW.row_names.size() - cycle_glass_rows


# The first row of its bed: the drawn tile's rows at the bottom, or all of the glass if it is less. The fury
# grows any row past the bed on in front of it at once.
func bed_top_row() -> int:
	return maxi(glass_top_row(), GLASS_ROW.row_names.size() - int(GLASS_ROW.bed_rows))


# The glass, rope to rope.
func glass_band() -> Rect2:
	return rows_band(glass_top_row())


# Rows k to the last, rope to rope.
func rows_band(k: int) -> Rect2:
	var span: Vector2 = GLASS_ROW.glass_span
	var rows: int = GLASS_ROW.row_names.size() - k
	return Rect2(span.x, GLASS_ROW.rows_top + GLASS_ROW.row_height * k, span.y - span.x, GLASS_ROW.row_height * rows)


# Row k rope to rope: each row of glass the fury grows on past the bed, and the front row a stomp's shards
# fall on.
func row_band(k: int) -> Rect2:
	var span: Vector2 = GLASS_ROW.glass_span
	return Rect2(span.x, GLASS_ROW.rows_top + GLASS_ROW.row_height * k, span.y - span.x, GLASS_ROW.row_height)


# The fail that reaches the glass as the row starts: one row a fail from the start row, the last row
# before the glass and then the glass itself.
func fails_to_glass() -> int:
	return glass_top_row() - int(GLASS_ROW.start_row)


# A floor plan that doesn't hold together is a warning, not a crash: the fight still plays.
func _check_glass_row() -> void:
	var rows: Array = GLASS_ROW.row_names
	var bottom: float = GLASS_ROW.rows_top + GLASS_ROW.row_height * rows.size()
	if absf(bottom - ROPES.end.y) > 1.0:
		push_warning("Matt: the Glass Row's rows end at %.0f, not on the bottom rope (%.0f)" % [bottom, ROPES.end.y])
	if GLASS_ROW.rows_top - GLASS_ROW.station.y < 60.0:
		push_warning("Matt: the Glass Row's station is under 60 px above row F")
	# The most glass must leave the start row clear.
	if rows.size() - glass_rows_by_share.max() <= int(GLASS_ROW.start_row):
		push_warning("Matt: the Glass Row's glass would reach its start row")


# The 12 lattice headings, in order round the circle.
func lattice_headings() -> Array[Vector2]:
	var out: Array[Vector2] = []
	var steps := roundi(360.0 / LATTICE_STEP)
	for k in steps:
		if k % 4 != 0:
			out.append(Vector2.from_angle(deg_to_rad(k * LATTICE_STEP)))
	return out


# His one punish window per cycle.
func is_recovering() -> bool:
	return current_state == states.get("Recover")


func is_yelling() -> bool:
	return is_recovering() and current_state.is_yelling()


# A punch in his window or his Break. Never in the air: the juggle draws every frame of that itself.
func flinch() -> void:
	if is_recovering() or current_state == states.get("Broken"):
		current_state.flinch()


func punch_landed(count: int) -> void:
	if is_recovering():
		current_state.on_punch_landed(count)


# The finisher ended his recovery early: he stays down, staggered, then starts the next cycle.
func stagger_then_start_cycle(stagger_time: float) -> void:
	recover_timer.stop()
	on_child_transition(current_state, "Idle")
	# Idle starts the breath before the next cycle; the stagger replaces it.
	beat_timer.stop()
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	MattCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


# A yell that landed: he is out of his window at once, holds the roar through its after-pose, and
# starts again post_yell_beat after the hit.
func idle_after_yell() -> void:
	var idle: State = states["Idle"]
	idle.hold_left = yell_after
	on_child_transition(current_state, "Idle")
	beat_timer.start(post_yell_beat)


# Null between two scenes, which is where a Glass Row cut short by a scene change lets go.
func get_player() -> Node2D:
	var scene := get_tree().current_scene
	return scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null


#THE PLAYER (every call guarded, CarterStateMachine's way: a player scene without one is a warning)

# Held and unable to answer at all - no move, dash, punch, guard or parry.
func seal_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions_sealed"):
		player.lock_actions_sealed()
	else:
		_warn_once("seal", "Matt: player has no lock_actions_sealed(); the Glass Row can't hold them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


func pose_player(on: bool) -> void:
	var player := get_player()
	if player and player.has_method("set_scripted_pose"):
		player.set_scripted_pose(on)


func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


func hold_player_pose(sheet: Dictionary) -> bool:
	var player := get_player()
	if player and player.has_method("hold_pose"):
		return player.hold_pose(sheet)
	_warn_once("pose", "Matt: player has no hold_pose(); the Glass Row's poses stay off")
	return false


func play_player_pose(frames: Array, times: Array, loop: bool) -> void:
	var player := get_player()
	if player and player.has_method("play_pose"):
		player.play_pose(frames, times, loop)


func end_player_pose() -> void:
	var player := get_player()
	if player and player.has_method("end_pose"):
		player.end_pose()


func add_player_hype(amount: float) -> void:
	var player := get_player()
	var hype: Node = player.get_node_or_null("Hype") if player else null
	if hype and hype.has_method("add"):
		hype.add(amount)
	else:
		_warn_once("hype", "Matt: player has no Hype node; a clean Glass Row pays nothing")


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)


# Everything he sends out lives under his scene, so a finisher's freeze holds it and the end of the
# fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	hazard.position = layer.to_local(at.round())
	layer.add_child(hazard)


func live_bolts() -> Array[Node]:
	return _live(BOLT_SCRIPT)


func live_waves() -> Array[Node]:
	return _live(WAVE_SCRIPT)


func live_echo_rings() -> Array[Node]:
	var out: Array[Node] = []
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		if hazard.get_script() == ECHO_RING_SCRIPT and hazard.is_live():
			out.append(hazard)
	return out


func live_projectiles() -> Array[Node]:
	return live_bolts() + live_waves() + live_echo_rings()


# One beat of his theme, in seconds.
func echo_beat() -> float:
	return 60.0 / echo_bpm


#THE PLAYER'S DEFENCE (the Echo Roars' parry rules, CarterStateMachine's and JoshCardsStateMachine's way)

# Called a beat's rearm delay after every ring's touch but a ghost's: a whiffed or late press never locks the next
# ring out (PlayerDefense.parry_mash_lockout outlasts a beat).
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Matt: PlayerDefense has no rearm_parry(); a whiffed ring can lock out the next")


func end_parry_streak() -> void:
	var defense := _defense()
	if defense and defense.has_method("end_parry_streak"):
		defense.end_parry_streak()
	else:
		_warn_once("streak", "Matt: PlayerDefense has no end_parry_streak(); a bitten X keeps the streak")


# Returns whether the signal was there.
func connect_block_presses(handler: Callable) -> bool:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed"):
		if not defense.block_pressed.is_connected(handler):
			defense.block_pressed.connect(handler)
		return true
	_warn_once("presses", "Matt: PlayerDefense has no block_pressed signal; an X can't be bitten")
	return false


func disconnect_block_presses(handler: Callable) -> void:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed") and defense.block_pressed.is_connected(handler):
		defense.block_pressed.disconnect(handler)


# Tops the stamina bar up to `amount` (E5): a parry press or the BOOMBURST's dash is never refused mid-string.
func hold_stamina_floor(amount: float) -> void:
	var defense := _defense()
	if defense == null or not defense.has_method("refund"):
		_warn_once("floor", "Matt: PlayerDefense has no refund(); the Echo Roars' stamina floor is off")
		return
	if defense.stamina < amount:
		defense.refund(amount - defense.stamina)


# The floor again on every change of the bar, not just each step: a whiff or the dash paid in the player's own step
# after his would otherwise leave the bar under it until the next one.
func watch_stamina(handler: Callable) -> void:
	var defense := _defense()
	if defense and defense.has_signal("stamina_changed") and not defense.stamina_changed.is_connected(handler):
		defense.stamina_changed.connect(handler)


func unwatch_stamina(handler: Callable) -> void:
	var defense := _defense()
	if defense and defense.has_signal("stamina_changed") and defense.stamina_changed.is_connected(handler):
		defense.stamina_changed.disconnect(handler)


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _live(script: Script) -> Array[Node]:
	var out: Array[Node] = []
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		if hazard.get_script() == script and not hazard.is_queued_for_deletion() and not hazard.get("spent"):
			out.append(hazard)
	return out


#THE BREAK AND THE JUGGLE

# A full Break gauge (BossBreakGauge): whatever he was doing stops, everything he sent out goes, the
# player is let go, and he is Broken until his time is up or the finisher's uppercut ends it.
func enter_broken() -> void:
	if MattCharacterBody.defeated or MattCharacterBody.boss_health <= 0 or player_defeated:
		return
	var unbreakable := [states.get("Intro"), states.get("Defeated"), states.get("Victory"), states.get("Broken"), states.get("Juggled")]
	if current_state in unbreakable:
		return
	breaks_taken += 1
	_stop_everything()
	# Insurance: a Glass Row cut short must not leave its station and bonus to the next window.
	recover_spot = HOME
	recover_bonus = 0.0
	on_child_transition(current_state, "Broken")
	_stop_timers()


# The finisher's uppercut ends the Break window instead of its own clock: he staggers, then starts the
# next cycle `delay` after now.
func end_break(delay: float) -> void:
	stagger_then_start_cycle(maxf(delay, 0.01))


# The tiered finisher's first uppercut (MattScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if MattCharacterBody.defeated or current_state == juggled:
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed, on the recoil frame, and his next cycle
# starts `delay` after this. The recoil is the get-up: the juggle hands back no animation to finish.
func after_juggle(delay: float) -> void:
	stagger_then_start_cycle(maxf(delay, 0.01))


# The one switch past the fight being decided: a juggled Matt, killed in the air, lands into his defeat
# rather than snapping to its pose mid-flight. It goes round on_child_transition's terminal guard.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# The floor under both fighters, where his juggle's shadow lies.
func ground_layer() -> Node2D:
	return MattCharacterBody.floor_layer


#THE END OF THE FIGHT

func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stands where he is, pleased with himself.
func enter_player_defeated() -> void:
	_end_fight("Victory")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	# A fight decided over the top of his entrance still leaves the ring set.
	var intro = states.get("Intro")
	if intro:
		intro.finish_entrance()
	_stop_everything()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled).
	if juggled and current_state == juggled:
		juggled.final_state = final_state_name
	else:
		on_child_transition(current_state, final_state_name)
	# After the transition, not before: entering Idle starts the beat timer, which must not survive the
	# end of the fight.
	_stop_timers()


# Whatever he is doing, stopped where it is: the throw, every attack's hold on the player and its badges,
# the wobble and its sounds, and everything he sent out.
func _stop_everything() -> void:
	MattCharacterBody.cancel_launch()
	for state_name in ["MysticVolley", "TrueshotBarrage", "Spent", "Recover", "GlassRow", "EchoRoars"]:
		var state: State = states.get(state_name)
		if state:
			state.release()
	ParryTell.clear(MattCharacterBody)
	MattCharacterBody.restore_hud()
	MattCharacterBody.clear_wobble()
	MattCharacterBody.stop_sfx(&"ear_ring")
	MattCharacterBody.stop_sfx(&"deafen_yell")
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()


func _stop_timers() -> void:
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer, beat_timer]:
		timer.stop()
		timer.paused = false
