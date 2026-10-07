extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var JoshCardsCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer

const VsCard := preload("res://Scripts/VsCard.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const JoshCardsBroken := preload("res://Scripts/States/JoshCards/JoshCardsBroken.gd")
const JoshCardsJuggled := preload("res://Scripts/States/JoshCards/JoshCardsJuggled.gd")
const JoshCardsWildCards := preload("res://Scripts/States/JoshCards/JoshCardsWildCards.gd")
const JoshCardsSummon := preload("res://Scripts/States/JoshCards/JoshCardsSummon.gd")
const JoshCardsHandSlam := preload("res://Scripts/States/JoshCards/JoshCardsHandSlam.gd")
const JoshCardsPortalMonte := preload("res://Scripts/States/JoshCards/JoshCardsPortalMonte.gd")
const JoshHandsRig := preload("res://Scripts/JoshHandsRig.gd")
const JoshHandsLayout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshMonteLayout := preload("res://Scripts/JoshMonteLayout.gd")

const PRE_FIGHT_DIALOGUE := "res://Dialogue/JoshPreFight.dialogue"
const HAZARD_GROUP := "josh_cards_hazard"

#THE ARENA
# The inside edges of the ropes, as Mason's Carter call-in measures them: his clones stand inside them,
# his cards leave the floor at them, and his own bounds (JoshCardsScript.ground_bounds) are cut from them.
const ROPES := Rect2(113, 114, 1692, 853)

# The fight opens on his Summon (JoshCardsSummon) behind the VS card: his two card-gate portals and the card
# hands that come out of them (JoshHandsRig), there for the rest of the fight. Then the cycle, since 2026-09-29:
# the next attack in ATTACK_ORDER, his Hand Slam (JoshCardsHandSlam), Wild Cards (JoshCardsWildCards) and his
# Portal Monte (JoshCardsPortalMonte) in turn, each followed by his Recover, the punish window, then the next. A Break
# carries the order on.

#TUNING (seconds, px and px/s)
# How high above the floor his feet rode his card. Nothing rides it now, but his shadow's frames are
# still scaled against it (JoshCardsScript.place).
@export var glider_height := 140.0
# How fast a Break far from where it drives him slides him there (JoshCardsBroken).
@export var dive_speed := 1400.0
# The punish window.
@export var recover_time := 3.0
# How many of his attacks run back to back before his Recover opens a window (the user, 2026-10-04; three, his whole
# rotation, since 2026-10-06): each before the last goes straight on into the next in ATTACK_ORDER (end_attack). A
# Portal Monte whose real him was parried opens him at once, and a window - his Recover or a Break - starts the count
# again.
@export var attacks_per_window := 3

#WILD CARDS (JoshCardsWildCards)
# Six clones (five until the tuning round of 2026-10-04) a hop apart, spread across the floor
# (JoshCardsWildCards.SPOT_CHOICES) and never nearer the player than wild_player_clearance.
@export var wild_clones := 6
@export var wild_hop_time := 0.7
@export var wild_player_clearance := 250.0
# From the last clone to the volley (0.7 s until the tuning round of 2026-10-04); he gates off the screen
# wild_exit_beat into it. Drawn out, up to the cap, when the player needs longer than the warning, less
# wild_escape_reaction to see the last lanes, to walk clear of them all.
@export var wild_warning := 0.5
@export var wild_exit_beat := 0.2
@export var wild_warning_cap := 1.4
@export var wild_escape_reaction := 0.2
# Three lanes a clone, this far apart; the cards' speed and the square of each that hurts.
@export var wild_spread_degrees := 20.0
@export var wild_card_speed := 1100.0
@export var wild_card_size := 60.0
# The clones scatter this long after they throw; he gates back in this long after the last card has
# gone, this far from the player.
@export var wild_clone_linger := 0.25
@export var wild_return_beat := 0.3
@export var wild_return_range := Vector2(420, 720)

#HAND SLAM (JoshCardsHandSlam)
# Six slams (four until the tuning round of 2026-10-04), the hands taking turns. Landing to landing is track + lock +
# drop, inside the player's i-frames and a lead over the dash immunity's cooldown, and lock + drop is the red badge's
# read (JoshHandsLayout.invariants).
@export var hand_slams := 6
@export var hand_command_time := 0.5
@export var hand_fly_time := 0.5
@export var hand_first_track := 0.6
@export var hand_track_time := 0.45
@export var hand_lock_time := 0.13
@export var hand_drop_time := 0.23
# A landed hand is pinned, then rises back to deck; a parried one shatters, then re-forms on deck: either before
# its next turn. The last one stays down through the settle, and then both fly home.
@export var hand_pin_time := 0.15
@export var hand_rise_time := 0.25
@export var hand_settle_time := 0.35
@export var hand_home_time := 0.5
@export var hand_shatter_time := 0.3
@export var hand_reform_time := 0.45
# How high they hover, how far one rears up as it locks, how fast the spot under it chases the player's feet, how
# far beside the player the other waits, and how far over the locked spot the badge's tip stands.
@export var hand_hover_height := 210.0
@export var hand_lock_rise := 36.0
@export var hand_track_speed := 1100.0
@export var hand_deck_offset := 240.0
@export var hand_badge_rise := 150.0
# The lock aims where the player is heading (the user, 2026-10-04): their feet led by hand_lead_time of how fast they
# were moving, at most hand_lead_max px on either axis, a walk's own lead, so a dash never throws it further. Walking
# on lands under it; stopping, turning or doubling back a reaction after the lock clears it (JoshHandsLayout.invariants).
# Only a player heading somewhere is led: one whose feet got less than hand_lead_straightness as far as they walked over
# the last hand_lead_window - zigzagging on the spot - is locked on their feet, so a wiggle never throws it off them.
@export var hand_lead_time := 0.42
@export var hand_lead_max := 252.0
@export var hand_lead_window := 0.5
@export var hand_lead_straightness := 0.5
# A string with every slam parried or dodged pays this, and the crowd cheers; each landing shakes the view, and a
# parry stops the fight dead a beat.
@export var hand_clean_hype := 10.0
@export var hand_clean_cheer := 2.0
@export var hand_impact_shake := 10.0
@export var hand_parry_hit_stop := 0.06

#GUN HANDS (JoshGunHands, a layer inside Wild Cards)
# Out to the sides as finger guns, a sweep up and down, a stop and a charge under the yellow badge, one volley of two
# beams, and home; Wild Cards holds its fifth clone until gun_clear_gap after the beams are gone. The stop is at
# out + sweep, the volley a charge later (JoshHandsLayout.invariants).
@export var wild_guns := true
@export var gun_out_time := 0.40
@export var gun_sweep_time := 1.50
@export var gun_sweep_period := 1.00
@export var gun_glide_time := 0.15
@export var gun_charge_time := 1.00
@export var gun_beam_live := 0.35
@export var gun_beam_fade := 0.20
@export var gun_back_time := 0.50
@export var gun_clear_gap := 0.15
# How far from the aimed row the other hand's row is cut off, and how hard the volley shakes the view.
@export var gun_row_offset := 220.0
@export var gun_fire_shake := 6.0

#PORTAL MONTE (JoshCardsPortalMonte)
# He dives up into a big gate and three small ones open round the player, each bursting in turn: the one under the red
# badge is really him (parry it), the two under the pale X are fakes (don't). Up to monte_rounds rounds of three (five
# since 2026-10-06, three before); each burst is monte_show under its mark, then a monte_dash lunge to its contact, the
# next mark monte_gap after (monte_cadence). The read and the dash are held to their floors in
# JoshMonteLayout.invariants.
@export var monte_rounds := 5
@export var monte_dive_time := 0.50
@export var monte_deal_time := 0.25
@export var monte_open_time := 0.30
@export var monte_show := 0.36
@export var monte_dash := 0.18
@export var monte_gap := 0.08
# How far out the small gates open, and never nearer than (JoshMonteLayout.place).
@export var monte_radius := 320.0
@export var monte_min_radius := 220.0
# A parried real him staggers out onto the floor, knocked monte_knock px back toward his gate, and his Recover is
# monte_parry_recover_bonus longer; with no parry he drops back out of his gate after the last round.
@export var monte_stagger_time := 0.35
@export var monte_knock := 150.0
@export var monte_emerge_time := 0.50
@export var monte_parry_recover_bonus := 1.0
# What a bitten fake costs (Carter's).
@export var monte_feint_stamina := 40.0
# The user's four questions on it (2026-09-29), each on its default until they answer: the player held in place for
# it (off: free to move, every burst homing in on them); a parried real him ends it and opens him (off: every round
# plays out, a parried figure breaking as Carter's clones do); the hands deal the small gates (off: they just rest); a
# bitten fake makes the next burst a punish nothing answers (off: it costs only the stamina and the streak). The user
# answered the second on 2026-10-04: off, every round plays out (a parried real him still opens him once it is over,
# end_attack).
@export var monte_lock_player := true
@export var monte_parry_ends := false
@export var monte_hands_deal := true
@export var monte_feint_punishes := true

# His attacks in turn, one a cycle, from the first after his Summon (start_cycle).
var ATTACK_ORDER: Array[String] = ["HandSlam", "WildCards", "PortalMonte"]
# Each of the player wrappers' missing-method warnings, once.
var warned := {}
var player_defeated := false
var cycles_started := 0
# His attacks since his last window.
var attacks_since_window := 0
# His portals and his card hands.
var hands: Node
# The pre-fight lines' balloon, which a held skip takes down, and whether those lines have handed
# over to the VS card yet.
var pre_fight_balloon: Node
var pre_fight_over := false


func _ready() -> void:
	# The Break window, the juggle it pays out, his hands, his summon and his attacks are built here rather than in
	# his scene.
	_add_down_state(JoshCardsBroken.new(), "Broken")
	_add_down_state(JoshCardsJuggled.new(), "Juggled")
	hands = JoshHandsRig.new()
	hands.name = "HandsRig"
	hands.body = JoshCardsCharacterBody
	hands.state_machine = self
	add_child(hands)
	var wild_cards := JoshCardsWildCards.new()
	wild_cards.name = "WildCards"
	wild_cards.body = JoshCardsCharacterBody
	add_child(wild_cards)
	var summon := JoshCardsSummon.new()
	summon.name = "Summon"
	summon.body = JoshCardsCharacterBody
	add_child(summon)
	var hand_slam := JoshCardsHandSlam.new()
	hand_slam.name = "HandSlam"
	hand_slam.body = JoshCardsCharacterBody
	add_child(hand_slam)
	var portal_monte := JoshCardsPortalMonte.new()
	portal_monte.name = "PortalMonte"
	portal_monte.body = JoshCardsCharacterBody
	add_child(portal_monte)
	JoshHandsLayout.assert_invariants(self)
	JoshMonteLayout.assert_invariants(self)

	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the body is ready, since the intro moves and draws him.
		current_state.Enter.call_deferred()


# His body's own ready comes after this node's, so its hurtbox is looked up rather than read off it.
func _add_down_state(state: Node, state_name: String) -> void:
	state.name = state_name
	state.body = JoshCardsCharacterBody
	state.hurtbox = JoshCardsCharacterBody.get_node("Air/Hurtbox")
	state.state_machine = self
	add_child(state)


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


#THE CYCLE

# His lines call no beats, so the intro hands the dialogue over and waits for it to end.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	pre_fight_balloon = DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


# A held skip's way past the lines (BossEntrance), whether they were ever put up or not: the hand-over
# their own end makes, made from here instead. pre_fight_over keeps it to once.
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
	VsCard.play_intro(self, "josh", post_dialogue_pre_fight_timer.start)


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	JoshCardsCharacterBody.start_music()
	on_child_transition(current_state, "Summon")


# His next attack in ATTACK_ORDER; a Break or a finisher carries the order on rather than starting it again. Hands
# his Break took away form again first, which the Hand Slam waits for and Wild Cards doesn't need.
func start_cycle() -> void:
	var attack: String = ATTACK_ORDER[cycles_started % ATTACK_ORDER.size()]
	cycles_started += 1
	hands.ensure_formed()
	on_child_transition(current_state, attack)


# An attack is over: his Recover, or the next attack until attacks_per_window have run since his last window.
# `earned` - the real him parried in his Portal Monte - opens the window at once.
func end_attack(state, earned := false) -> void:
	if state != current_state:
		return
	attacks_since_window += 1
	if attacks_since_window < attacks_per_window and not earned:
		start_cycle()
		return
	attacks_since_window = 0
	on_child_transition(state, "Recover")


# The Break gauge's one read for a volley's perfect dodges (JoshCardsScript.BREAK_EARNS).
func pay_volley_read(hit: RefCounted) -> bool:
	return states["WildCards"].pay_read(hit)


# His one punish window per cycle.
func is_recovering() -> bool:
	return current_state == states.get("Recover")


# A punch landing in either of his windows; not in the juggle, which is drawn off its own sheet.
func flinch() -> void:
	if is_recovering() or current_state == states.get("Broken"):
		current_state.flinch()


# The finisher ended his recovery early: he stays down, staggered, then starts the next cycle.
func stagger_then_start_cycle(stagger_time: float) -> void:
	recover_timer.stop()
	on_child_transition(current_state, "Idle")
	# Held on the recoil frame through the stagger instead of the idle loop Idle starts.
	JoshCardsCharacterBody.play_anim(&"hit", &"idle")
	finisher_stagger_timer.start(stagger_time)


func _on_finisher_stagger_timer_timeout() -> void:
	start_cycle()


# One burst of his Portal Monte, whole: its mark, its dash and the gap to the next mark.
func monte_cadence() -> float:
	return monte_show + monte_dash + monte_gap


#THE PLAYER, FOR HIS PORTAL MONTE (CarterStateMachine's, each guarded so a player without it only loses that part)

# Held for a parry-only sequence: no walking, no dash, no punch, while the guard, its parry window and the streak
# behind it all keep working. Never is_grabbed or is_talking, which PlayerScript._input returns on before the block
# branch: the sequence would be unparryable with no error at all.
func lock_player() -> void:
	var player := get_player()
	if player and player.has_method("lock_actions"):
		player.lock_actions()
	else:
		_warn_once("lock", "Josh: player has no lock_actions(); the Monte can't root them")


func unlock_player() -> void:
	var player := get_player()
	if player and player.has_method("unlock_actions"):
		player.unlock_actions()


# Turned to meet each burst as its mark comes up. It changes nothing about the parry - the hit's origin is the
# player's own hurtbox centre - and unlock_actions() clears it.
func face_player_at(point: Vector2) -> void:
	var player := get_player()
	if player and player.has_method("face_point"):
		player.face_point(point)


func clear_player_facing() -> void:
	var player := get_player()
	if player and player.has_method("clear_face_point"):
		player.clear_face_point()


# On the exact frame each mark comes up: a press that parried nothing counts against the next one
# (PlayerDefense.parry_mash_lockout), so without it a whiff on one burst can leave the next unparryable. It
# deliberately does not excuse mashing within one burst.
func rearm_parry() -> void:
	var defense := _defense()
	if defense and defense.has_method("rearm_parry"):
		defense.rearm_parry()
	else:
		_warn_once("rearm", "Josh: PlayerDefense has no rearm_parry(); a whiffed burst can lock out the next")


func end_parry_streak() -> void:
	var defense := _defense()
	if defense and defense.has_method("end_parry_streak"):
		defense.end_parry_streak()
	else:
		_warn_once("streak", "Josh: PlayerDefense has no end_parry_streak(); a bitten fake keeps the streak")


func drain_stamina(amount: float) -> void:
	var defense := _defense()
	if defense and defense.has_method("drain_stamina"):
		defense.drain_stamina(amount)
	else:
		_warn_once("stamina", "Josh: PlayerDefense has no drain_stamina(); a bitten fake costs nothing")


# Whether the signal was there. When it wasn't, the caller polls the block action in Physics_Update instead - and only
# there, since polling in both would bill one press twice.
func connect_block_presses(handler: Callable) -> bool:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed"):
		if not defense.block_pressed.is_connected(handler):
			defense.block_pressed.connect(handler)
		return true
	_warn_once("presses", "Josh: PlayerDefense has no block_pressed signal; fakes fall back to polling")
	return false


func disconnect_block_presses(handler: Callable) -> void:
	var defense := _defense()
	if defense and defense.has_signal("block_pressed") and defense.block_pressed.is_connected(handler):
		defense.block_pressed.disconnect(handler)


func _defense() -> Node:
	var player := get_player()
	return player.get("defense") if player else null


func _warn_once(key: String, message: String) -> void:
	if warned.has(key):
		return
	warned[key] = true
	push_warning(message)


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


# Everything he sends out lives under the fight scene, so a finisher's freeze holds it and the end of
# the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)
	hazard.global_position = at.round()


#HIS BREAK AND THE JUGGLE

# A full Break gauge (BossBreakGauge): whatever he was doing stops, everything he sent out goes, his hands
# dissolve into their portals, and he is Broken until his time is up or the finisher's uppercut ends it.
func enter_broken() -> void:
	var body := JoshCardsCharacterBody
	if body.defeated or body.boss_health <= 0 or player_defeated:
		return
	if current_state in [states.get("Intro"), states.get("Summon"), states.get("Defeated"), states.get("Broken"), states.get("Juggled")]:
		return
	_stop_everything()
	attacks_since_window = 0
	on_child_transition(current_state, "Broken")
	hands.retract()


# The finisher's uppercut ends the Break window instead of its own clock, as it ends his recovery.
func end_break(delay: float) -> void:
	stagger_then_start_cycle(maxf(delay, 0.01))


# The tiered finisher's first uppercut (JoshCardsScript.begin_juggle).
func enter_juggled() -> void:
	var juggled = states["Juggled"]
	if JoshCardsCharacterBody.defeated or current_state == juggled:
		return
	on_child_transition(current_state, "Juggled")


# Down after a juggle, he picks himself up where he crashed, on the recoil frame a finisher leaves him
# on, and his next cycle starts `delay` after this.
func after_juggle(delay: float) -> void:
	stagger_then_start_cycle(maxf(delay, 0.01))


# The one switch past the fight being decided: a juggled Josh, killed in the air, lands into his defeat
# rather than snapping to its pose mid-flight.
func land_juggled(final_state_name: String) -> void:
	var final_state = states.get(final_state_name)
	if final_state == states.get("Defeated"):
		final_state.lying = true
	current_state.Exit()
	final_state.Enter()
	current_state = final_state


# Where his juggle's shadow lies: on his floor layer, under his cards' lanes.
func ground_layer() -> Node2D:
	return JoshCardsCharacterBody.floor_layer


# Beaten, he takes his hands and his portals with him, killed in the air or not.
func enter_defeated() -> void:
	hands.collapse()
	_end_fight("Defeated")


# The player lost: he stops where he is.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	_stop_everything()
	var juggled = states.get("Juggled")
	# In the air, he finishes his fall and his crash first (land_juggled). The juggle draws itself on its
	# own clock, so it plays out whatever state the fight is in.
	if current_state == juggled:
		juggled.final_state = final_state_name
		return
	on_child_transition(current_state, final_state_name)


# Everything of his still running: his clocks, a tell over his head and everything he has sent out. The
# attack's own release() gives back the rest as it exits.
func _stop_everything() -> void:
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer]:
		timer.stop()
	ParryTell.clear(JoshCardsCharacterBody)
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
