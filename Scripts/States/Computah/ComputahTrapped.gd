extends State

# THE MINE TRAP: a pod closed on the player, so he walks over and swings a charged uppercut at them
# while they mash their way out of it.
#
#   CLOSE   the jaws shut. The player is SEALED - no move, no dash, no punch, and the guard and its
#           parry are sealed off too, which is what makes this different from every other hold in the
#           fight. The ESCAPE prompt goes up and THE PRESSES START COUNTING HERE, not when he
#           arrives: the mash is the whole beat, and one that only opened once he was in position
#           would make the walk dead time.
#   WALK    he crosses at mine_walk_speed and stops at pounce_range. NO NEW ART - it is his run
#           cycle, which is what that speed reads as.
#   CHARGE  uppercut_wind and a glow at the muzzle, for mine_charge.
#   SWING   uppercut. If the player got out, IT SPAWNS NO HITBOX AT ALL and he overbalances through
#           it into a long punish window. If they did not, computah_uppercut lands, and the launch
#           that frees them is the knockdown.
#
# HE DOES NOT CANCEL WHEN THEY ESCAPE, and the swing does not "just miss": there is nothing on the
# end of it. If escaping could still clip the player, mashing would be a trap of its own.
#
# HE IS NOT PUNISHABLE FOR AN UPPERCUT THAT LANDED. The window is the reward for escaping; handing it
# out either way would delete the stakes.
#
# IT IS ONE STATE WITH ONE release() FUNNEL, CALLED FROM Exit() AND FROM _exit_tree(), exactly as
# ComputahCaught's is. A player left sealed can never move again, which is the worst bug this fight
# can have, and a single idempotent funnel is the only way every path out - escaping, the uppercut, a
# win, a loss, a finisher, a scene change - is provably safe. DO NOT SPLIT THIS INTO THREE STATES.
#
# THE MASH IS THIS STATE'S OWN, AND IT MUST NOT SWALLOW INPUT. Nothing here calls
# get_viewport().set_input_as_handled() or InputSettings.note_device(): PlayerFinisher._input returns
# early WITHOUT marking the event handled while its phase is OFF, which is exactly what lets this own
# the same keys alongside it.
#
# THE PROMPT IS FinisherPromptUI, the widget PlayerGrabEscape already drives, through the same small
# surface: prompt_shown/meter_changed/charge_ended/finished, mash_actions(), `meter`, `tiered` and
# `prompt_key`. Gold MASH! means "you have won, cash it in"; alarm-red ESCAPE! means "you are in
# trouble", and that difference is the whole reason for asking for the other word.
#
# FREEZE SAFETY: every beat is a Physics_Update accumulator and the meter drains on the same clock, so
# a hit-stop holds the trap, the walk, the charge and the mash together. Nothing here may use
# get_tree().create_timer() or a tree-level create_tween().

const HitStop := preload("res://Scripts/HitStop.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/ComputahArtLayout.gd")
const MashInput := preload("res://Scripts/MashInput.gd")
const MashCurve := preload("res://Scripts/MashCurve.gd")
const FinisherPromptUI := preload("res://Scripts/FinisherPromptUI.gd")

const UPPERCUT_ID := &"computah_uppercut"

#WHAT FinisherPromptUI READS. Never emitted below: the prompt connects them because the finisher has
# them, and a tiered mash is the finisher's alone.
signal prompt_shown
signal meter_changed(meter: float, next_action: StringName)
signal charge_ended(filled: bool)
signal finished
signal tier_banked(tier: int)
signal juggle_hit(index: int, last: bool)

@export var body : CharacterBody2D
@export var fx_layer : Node2D
@export var snap_sfx_player : AudioStreamPlayer
@export var charge_sfx_player : AudioStreamPlayer
@export var swing_sfx_player : AudioStreamPlayer
@export var punch_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { CLOSE, WALK, CHARGE, SWING, RECOVER }

# The jaws shutting, held on a hit-stop of the same length so the snap reads.
const CLOSE_TIME := 0.10
const CLOSE_HIT_STOP := 0.10
# REAL seconds, and PlayerFinisher.min_press_interval's value: both keys pressed together arrive in
# the same input flush however long the frame took, and must count once.
const MIN_PRESS_INTERVAL := 0.03
# Into the swing: contact is the apex (computah_uppercut frame 5), and the rise is over at the end.
const UPPERCUT_HIT_AT := 0.14
const UPPERCUT_END := 0.40
const HIT_STOP := 0.18
const HIT_SHAKE := 20.0
const FALL_SHAKE := 16.0
const SHAKE_STEPS := 7
const SHAKE_STEP_TIME := 0.03
# Up and away from him, so the launch clears his reach. ComputahCaught's toss.
const TOSS_LIFT := 0.7
# He has arrived once he cannot get any closer: the runner's box keeps his feet off the ropes, so a
# player backed into a corner can be further than pounce_range away and still unreachable.
const WALK_STALLED := 0.5

# Set by ComputahStateMachine.trap_player() before the transition.
var mine: Node2D = null

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# The state has handed the fight on; nothing below may fire again.
var done := false
var escaped := false
var swung := false
var phase := Phase.CLOSE
var clock := 0.0
var hold_point := Vector2.ZERO

#THE MASH
var meter := 0.0
var tiered := false
var prompt_key := &"escape"
# The pair the mash alternates between, READ FROM THE PLAYER'S OWN FINISHER rather than named here,
# and cached for the length of the hold so the prompt is never handed a different pair halfway
# through one. In a feel_v2 fight it is mash_left/mash_right - the arrows and the shoulder buttons.
var pair: Array[StringName] = []
var last_action := &""
var last_press_usec := 0

var prompt: Node2D
var glow: Node2D


func Enter() -> void:
	released = false
	done = false
	escaped = false
	swung = false
	meter = 0.0
	last_action = &""
	last_press_usec = 0
	clock = 0.0
	phase = Phase.CLOSE

	var player: Node2D = state_machine.get_player()
	_read_pair()
	hold_point = player.global_position if player else body.global_position
	if is_instance_valid(mine):
		mine.spring()

	state_machine.seal_player()
	state_machine.pose_player(true)
	state_machine.face_player_at(body.global_position)
	body.velocity = Vector2.ZERO
	body.set_grab_active(false)
	body.set_target_active(false)
	body.show_battery(false)
	body.set_body_box(&"idle")

	_build_prompt(player)
	prompt_shown.emit()
	HitStop.freeze(get_tree(), CLOSE_HIT_STOP)
	get_tree().call_group("arena_crowd", "cheer", 1.0)
	snap_sfx_player.play()


func Exit() -> void:
	release()
	_show_glow(false)
	body.set_solid(true)
	body.set_target_active(true)
	body.velocity = Vector2.ZERO


func _exit_tree() -> void:
	release()


# Idempotent, and called from both Exit() and _exit_tree(). Every way out of this state runs through
# here, including the terminal ones that skip Exit() (ComputahStateMachine._end_fight), and the
# escape, which frees the player WITHOUT ending the state - he still owes them the uppercut.
func release() -> void:
	if released:
		return
	released = true
	if state_machine and is_instance_valid(state_machine):
		state_machine.unlock_player()
		state_machine.clear_player_facing()
		state_machine.pose_player(false)
		state_machine.note_release()
	if is_instance_valid(mine):
		mine.queue_free()
	mine = null
	charge_ended.emit(escaped)
	finished.emit()


func Physics_Update(delta: float) -> void:
	if done:
		return
	clock += delta
	if not released:
		# Anything that took the player out from under the hold frees them here. The terminal paths
		# come through _end_fight and the funnel below, but this is the one that cannot be forgotten:
		# a player left sealed can never move again.
		var held: Node2D = state_machine.get_player()
		if held == null or held.fight_over or held.is_finishing:
			release()
		else:
			_hold_player()
			meter = maxf(meter - MashCurve.drain(state_machine.escape_drain, meter) * delta, 0.0)
	match phase:
		Phase.CLOSE:
			if clock >= CLOSE_TIME:
				_start_walk()
		Phase.WALK:
			_walk(delta)
		Phase.CHARGE:
			_grow_glow()
			if clock >= state_machine.mine_charge:
				_start_swing()
		Phase.SWING:
			_advance_swing()
		Phase.RECOVER:
			if clock >= state_machine.mine_uppercut_recover:
				done = true
				state_machine.start_cycle()


# Kept in the pod, and looking at him. A sealed player's _physics_process returns before anything
# moves them, so writing the position here is what carries.
func _hold_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	player.global_position = hold_point.round()
	player.velocity = Vector2.ZERO
	state_machine.face_player_at(body.global_position)


func _set_phase(new_phase: Phase) -> void:
	phase = new_phase
	clock = 0.0


#THE WALK

func _start_walk() -> void:
	_set_phase(Phase.WALK)
	# His shape off while he crosses, so he neither shoves the held player nor sticks to them. The
	# chase does the same.
	body.set_solid(false)
	body.play_anim(&"chase")


func _walk(delta: float) -> void:
	body.face_toward(hold_point)
	if body.global_position.distance_to(hold_point) <= state_machine.pounce_range:
		_start_charge()
		return
	var bounds: Rect2 = state_machine.runner_bounds()
	var before: Vector2 = body.global_position
	body.global_position = body.global_position.move_toward(hold_point,
		state_machine.mine_walk_speed * delta).clamp(bounds.position, bounds.end)
	if body.global_position.distance_to(before) < WALK_STALLED:
		_start_charge()


#THE CHARGE

func _start_charge() -> void:
	_set_phase(Phase.CHARGE)
	body.velocity = Vector2.ZERO
	body.face_toward(hold_point)
	body.play_anim(&"uppercut_wind")
	_show_glow(true)
	charge_sfx_player.play()


#THE SWING

func _start_swing() -> void:
	_set_phase(Phase.SWING)
	_show_glow(false)
	charge_sfx_player.stop()
	swung = false
	body.play_anim(&"uppercut")
	swing_sfx_player.play()


func _advance_swing() -> void:
	if not swung and clock >= UPPERCUT_HIT_AT:
		swung = true
		# A player who got out is swung at with NOTHING: no hitbox is spawned at all, rather than one
		# aimed to miss. An escape that could still clip them would be a trap of its own. `released`
		# covers the other way the hold can end early - the fight ending under it - where there is
		# nobody left being held to punch.
		if not escaped and not released:
			_land()
	if clock < UPPERCUT_END:
		return
	if escaped:
		_fall()
	else:
		_set_phase(Phase.RECOVER)


func _land() -> void:
	var player: Node2D = state_machine.get_player()
	if player:
		player.receive_hit(HitInfo.make(UPPERCUT_ID, self, hold_point, body))
	state_machine.note_catch()
	HitStop.freeze(get_tree(), HIT_STOP)
	body.shake_screen(HIT_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", 2.0)
	punch_sfx_player.pitch_scale = 0.8
	punch_sfx_player.play()
	# Freed first and only then tossed, exactly as ComputahCaught does it: release_grab() is the only
	# existing way to hand back the post-grab i-frames and the launch, and THAT LAUNCH IS THE
	# KNOCKDOWN this attack ends on.
	var away := Vector2(-1.0 if body.facing_left else 1.0, -TOSS_LIFT)
	release()
	state_machine.release_player(away)


# He overbalanced through a punch with nothing on the end of it. Longer and worth more than the
# beam's vent: that one arrives on the cycle whether the player did anything or not, and this one was
# earned under a charging uppercut. 3.6 s is reliably two full combos including a run-up, and the cap
# of four - rather than the usual three - is the concrete prize, because three caps a single combo and
# four lets the second combo's charged third punch land, which is where a finisher comes from.
func _fall() -> void:
	done = true
	body.velocity = Vector2.ZERO
	body.shake_screen(FALL_SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	get_tree().call_group("arena_crowd", "cheer", 2.5)
	state_machine.open_window(state_machine.mine_fall_window, state_machine.mine_fall_cap,
		&"uppercut_fall", &"fallen", &"uppercut_up")


#THE MASH
# Its own, because PlayerGrabEscape's runs off player.is_grabbed and this hold deliberately never
# grabs: the player stands in the pod in their own sprite, and he has to be able to hit them.

func mash_actions() -> Array[StringName]:
	return pair


func _read_pair() -> void:
	var player: Node2D = state_machine.get_player()
	if player and player.finisher:
		pair = player.finisher.mash_actions()


func _input(event: InputEvent) -> void:
	if released or done:
		return
	for action in pair:
		if event.is_action_pressed(action):
			_press(action)
			return


func _press(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	# PlayerFinisher._press()'s rule, through the plumbing the two share (MashInput): a press of the
	# same action as the last one is ignored, and two presses closer than MIN_PRESS_INTERVAL count
	# once.
	if not MashInput.counts(action, last_action, now, last_press_usec, MIN_PRESS_INTERVAL):
		return
	last_action = action
	last_press_usec = now
	meter = minf(meter + MashCurve.gain(state_machine.escape_gain, meter), 1.0)
	var pair := mash_actions()
	meter_changed.emit(meter, pair[1] if action == pair[0] else pair[0])
	get_tree().call_group("arena_crowd", "cheer", 0.4)
	if meter >= 1.0:
		_escape()


# Out of the pod, and free from this instant - but he is already committed to the swing.
func _escape() -> void:
	escaped = true
	release()
	get_tree().call_group("arena_crowd", "cheer", 1.5)


#THE PROMPT
# Built once, the first time a pod closes, and kept: the fight's own HUD layer, the way the health bar
# and the Break gauge are built there.

func _build_prompt(player: Node2D) -> void:
	if is_instance_valid(prompt) or player == null or body.hud_layer == null or pair.size() != 2:
		return
	var ui: Node2D = FinisherPromptUI.new()
	ui.name = "EscapePrompt"
	ui.finisher = self
	ui.player = player
	body.hud_layer.add_child(ui)
	prompt = ui


#THE MUZZLE GLOW
# The capacitor dumping into the punch, on its own node over the fight: the same placeholder the beam
# charges with, so his one power source reads the same wherever it is spent.

func _show_glow(on: bool) -> void:
	if not on:
		if glow:
			glow.hide()
		return
	if Layout.USE_FINAL_CHARGE_GLOW:
		return
	if glow == null:
		var spec := Layout.PLACEHOLDER_CHARGE_GLOW
		var shape := Polygon2D.new()
		shape.polygon = Layout.ellipse(spec.radii, spec.points)
		shape.material = Layout.additive()
		fx_layer.add_child(shape)
		glow = shape
	glow.color = Layout.PLACEHOLDER_CHARGE_GLOW.color
	glow.show()
	_grow_glow()


func _grow_glow() -> void:
	if glow == null or not glow.visible:
		return
	var spec := Layout.PLACEHOLDER_CHARGE_GLOW
	var along := clampf(clock / maxf(state_machine.mine_charge, 0.01), 0.0, 1.0)
	# The pose's OWN muzzle, not the lock's: uppercut_wind drops the barrel to his hip and keeps
	# dropping it, so a glow pinned to C_MUZZLE floated a body's width above the bore for the whole
	# charge.
	glow.global_position = body.muzzle_point().round()
	glow.scale = Vector2.ONE * lerpf(spec.from_scale, spec.to_scale, along)
	glow.modulate.a = lerpf(spec.from_alpha, spec.to_alpha, along)
