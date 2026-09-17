extends Node

@export var initial_state : State

@export var states : Dictionary = {}
@export var current_state : State
@export var JoshCardsCharacterBody : CharacterBody2D

#TIMERS
@export var post_dialogue_pre_fight_timer: Timer
@export var recover_timer: Timer
@export var finisher_stagger_timer: Timer

const ParryTell := preload("res://Scripts/ParryTell.gd")
const CARD_BOMB_SCENE := preload("res://Scenes/Bosses/JoshCardBombScene.tscn")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")

const PRE_FIGHT_DIALOGUE := "res://Dialogue/JoshPreFight.dialogue"
const HAZARD_GROUP := "josh_cards_hazard"

#THE ARENA, IN THIRDS
# The inside edges of the ropes, as Mason's Carter call-in measures them, split into three equal
# columns. Every giant card, its floor shadow, its hitbox and the monte's reveal lookup derive from
# these, so what is drawn and what hurts can never drift apart. Nothing else may hardcode them.
const ROPES := Rect2(113, 114, 1692, 853)
const THIRDS := 3
const THIRD_WIDTH := 564.0

# The cycle: he mounts his card, lays three giant ones over the arena, works the crowd from the air,
# drops off in front of the player, throws three cards and is open while he gets his breath back.
# The phase is locked once, at the top of the cycle, so a hit landing mid-cycle never changes what
# the rest of it does.

#TUNING (seconds, px and px/s)
# How high above the floor his feet ride. Low enough that a high pass row still leaves his whole
# sprite on screen: JoshArtLayout.RIDE_HEADROOM is how far his riding frames reach above his feet, so
# every pass row has to be at least glider_height + that or the top of the screen cuts his hat off.
@export var glider_height := 140.0
# Mounting: the card grows under him, then he rises.
@export var mount_grow_time := 0.4
@export var mount_rise_time := 0.5
@export var mount_settle := 0.3
# His passes across the arena: the row he lays the cards from, how fast he crosses, and the x he
# turns around at, well off either side of the screen.
# These are his floor point, and he is drawn glider_height above it, so the top rows put him behind
# his own health bar for a moment. That is fine - the bar is on a CanvasLayer and draws over him -
# and keeping the rows high is what stops the top of the arena becoming a bomb-free lane.
@export var pass_y := 365.0
@export var glide_speed := 950.0
@export var pass_left_edge := -300.0
@export var pass_right_edge := 2220.0
# The rows the card storm's passes run along, in turn.
@export var pass_rows: Array[float] = [365.0, 620.0, 460.0, 780.0]
# How far above its resting place a laid card waits, off the top of the screen, and slides down from
# through its warning. Three full-height cards hanging in view would hide the whole fight, so only
# their floor shadows mark the thirds until one drops.
@export var card_hover_height := 900.0
# Phase two: how long he holds each card up face-out before laying it flat.
@export var face_show_time := 0.8
# A bomb every this many px of travel, except over the third that is warning or slamming.
@export var bomb_spacing := 480.0
@export var monte_bomb_spacing := 380.0
@export var fast_bomb_spacing := 260.0
@export var fast_bomb_time := 3.0
@export var bomb_fuse := 1.1
# The drawn fireball's radius: the blast hurts exactly as far as it reads.
@export var bomb_blast_radius := 75.0
# The falling cards, strictly one at a time: the warning each gets, and the beat after it lands.
@export var card_warning := 1.4
@export var card_gap := 0.5
# The three-card monte. Trackability budget: raising swap_count above 6 or dropping swap_time below
# 0.3 makes it a coin flip.
@export var swap_count := 5
@export var swap_arc := 90.0
@export var swap_time_first := 0.5
@export var swap_time_last := 0.35
@export var swap_time_cycles := 3
@export var swap_gap := 0.15
@export var lock_in_time := 0.7
# The reveal burst's own length, so the call lands on its last frame.
@export var reveal_flip_time := 0.32
@export var reveal_hold := 0.8
@export var reveal_dismiss := 0.4
@export var status_time := 6.0
# Dropping off: where he lands relative to the player, and how fast he dives there.
@export var throw_distance := 520.0
@export var dive_speed := 1400.0
@export var dismount_land_time := 0.35
# The three thrown cards. throw_interval is release to release; PlayerDefense.parry_mash_lockout is
# 0.5 s, so a player who whiffs card 1 still has a credited press in time for card 2. Do not shorten
# it below 0.65 without re-reading PlayerDefense.on_block_pressed().
@export var throw_tell := 0.45
@export var throw_interval := 0.9
@export var throw_cards := 3
@export var card_speed := 900.0
@export var card_hit_size := Vector2(90, 90)
# Off: the thrown cards fly straight. Kept as a knob in case they ever need to lead the player.
@export var card_homing_time := 0.0
@export var throw_recovery_delay := 0.35
# The punish window.
@export var recover_time := 3.5

# How close to the turning point off-screen counts as having reached it.
const PASS_TURN_DISTANCE := 40.0

var player_defeated := false
var cycles_started := 0
# 0 for the card storm, 1 for the monte. Read from the body once, at the top of each cycle.
var cycle_phase := 0
var phase_two_cycles := 0
var warned_no_status := false

# The three giant cards this cycle laid, and what is under each one. Both are indexed by third, so a
# monte swap swaps them together and the reveal can just look up where the player is standing.
var slots: Array[int] = [0, 1, 2]
var cards: Array = [null, null, null]

# His passes across the arena, shared by the card storm and the monte.
var pass_row := 0
var pass_edge := 0.0
var pass_travel := 0.0


func _ready() -> void:
	for child in get_children():
		if child is State:
			states[child.name] = child

	if initial_state:
		current_state = initial_state
		# Deferred until the body is ready, since the intro moves and draws him.
		current_state.Enter.call_deferred()


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


#THE ARENA, IN THIRDS

static func third_rect(index: int) -> Rect2:
	return Rect2(ROPES.position.x + index * THIRD_WIDTH, ROPES.position.y, THIRD_WIDTH, ROPES.size.y)


static func third_centre(index: int) -> Vector2:
	return third_rect(index).get_center()


static func third_at(x: float) -> int:
	return clampi(floori((x - ROPES.position.x) / THIRD_WIDTH), 0, THIRDS - 1)


#THE CYCLE

# His lines call no beats, so the intro hands the dialogue over and waits for it to end.
func show_pre_fight_dialogue() -> void:
	# One-shot: the outro's lines end a dialogue too, and must not start the fight again.
	DialogueManager.dialogue_ended.connect(_on_dialogue_ended, CONNECT_ONE_SHOT)
	DialogueManager.show_dialogue_balloon(load(PRE_FIGHT_DIALOGUE), "start")


func _on_dialogue_ended(_dialogue: Object) -> void:
	post_dialogue_pre_fight_timer.start()


func _on_post_dialogue_pre_fight_timer_timeout() -> void:
	JoshCardsCharacterBody.start_music()
	start_cycle()


func start_cycle() -> void:
	cycle_phase = 1 if JoshCardsCharacterBody.phase_two else 0
	cycles_started += 1
	if cycle_phase == 1:
		phase_two_cycles += 1
	on_child_transition(current_state, "Mount")


# The shuffle tightens over the phase-two cycles, up to its cap.
func swap_time() -> float:
	var along := clampf(float(phase_two_cycles - 1) / float(maxi(swap_time_cycles, 1)), 0.0, 1.0)
	return lerpf(swap_time_first, swap_time_last, along)


# His one punish window per cycle.
func is_recovering() -> bool:
	return current_state == states.get("Recover")


func flinch() -> void:
	if is_recovering():
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


func get_player() -> Node2D:
	return get_tree().current_scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D")


# Everything he sends out lives under the fight scene, so a finisher's freeze holds it and the end of
# the fight takes it away.
func add_hazard(hazard: Node2D, at: Vector2, layer: Node2D) -> void:
	hazard.add_to_group(HAZARD_GROUP)
	layer.add_child(hazard)
	hazard.global_position = at.round()


#HIS PASSES OVER THE ARENA

func begin_passes() -> void:
	pass_row = 0
	pass_travel = 0.0
	pass_edge = pass_right_edge if JoshCardsCharacterBody.fly_velocity.x >= 0.0 else pass_left_edge


# He keeps crossing the arena, turning around well off-screen and dropping a row each pass, and leaves
# a bomb behind him every `spacing` px of travel. `keep_out_third` is the third that is warning or
# slamming, which never gets a bomb; -1 when none is.
func advance_pass(delta: float, spacing: float, keep_out_third: int) -> void:
	var body := JoshCardsCharacterBody
	var before: Vector2 = body.ground_position
	var row: float = pass_rows[pass_row % pass_rows.size()]
	var left: float = body.fly_toward(Vector2(pass_edge, row), glide_speed, delta)
	pass_travel += before.distance_to(body.ground_position)
	if left < PASS_TURN_DISTANCE:
		pass_edge = pass_left_edge if pass_edge > 0.0 else pass_right_edge
		pass_row += 1
	while pass_travel >= spacing:
		pass_travel -= spacing
		drop_bomb(keep_out_third)


func drop_bomb(keep_out_third: int) -> void:
	var body := JoshCardsCharacterBody
	var point: Vector2 = body.ground_position
	if not ROPES.has_point(point) or third_at(point.x) == keep_out_third:
		return
	var bomb := CARD_BOMB_SCENE.instantiate()
	bomb.fuse = bomb_fuse
	bomb.blast_radius = bomb_blast_radius
	# From his hand on the drop frame, down to the floor point he is over.
	bomb.fall_offset = (JoshArtLayout.local(JoshArtLayout.HAND_BOMB, body.sprite.flip_h)
		- Vector2(0, body.height))
	add_hazard(bomb, point, body.floor_layer)
	body.play_anim(&"bomb", &"glide")


# The monte's prize. The defence coder owns apply_status; until it lands the reveal still reads and
# the fight carries on.
func apply_status(kind: StringName, seconds: float) -> void:
	var player := get_player()
	if player and player.has_method("apply_status"):
		player.apply_status(kind, seconds)
	elif not warned_no_status:
		warned_no_status = true
		push_warning("JoshCards: player has no apply_status(); '%s' had no effect" % kind)


func enter_defeated() -> void:
	_end_fight("Defeated")


# The player lost: he stops where he is.
func enter_player_defeated() -> void:
	_end_fight("Idle")
	player_defeated = true


func _end_fight(final_state_name: String) -> void:
	for timer in [post_dialogue_pre_fight_timer, recover_timer, finisher_stagger_timer]:
		timer.stop()
	ParryTell.clear(JoshCardsCharacterBody)
	for hazard in get_tree().get_nodes_in_group(HAZARD_GROUP):
		hazard.queue_free()
	on_child_transition(current_state, final_state_name)
