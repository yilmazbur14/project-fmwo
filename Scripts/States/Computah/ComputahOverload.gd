extends State

# ATTACK 3: THE OVERLOAD, and it is a DPS CHECK. He plants, arches back over his heels and winds
# himself up. The player has to RUSH HIM AND PUNCH - overload_threshold half-hearts before his clock
# runs out. Land them and the charge breaks and drops him, which is the uppercut. Miss them and the
# charge goes off over the whole mat for a full heart, and there is nowhere to be.
#
# EVERY OTHER ATTACK IN THIS FIGHT ASKS FOR A DEFENSIVE READ. THIS ONE ASKS FOR OFFENCE, and that is
# why it carries NO TELL OF EITHER COLOUR. Red means parry and yellow means dodge; both are wrong
# answers here, and a player who does either loses a heart. A badge is an answer key naming a button
# and this has no button - carter_clone_punish already sets that precedent.
#
# WHAT SAYS IT INSTEAD IS A QUANTITY, IN TWO PLACES:
#   THE RACE GAUGE over his head. Top row his charge on a fixed clock, bottom row the player's damage
#     in one cell per half-heart. Whichever fills first wins. Two rows and never one tug-of-war bar: a
#     single bar punches pushed back would make the effective threshold shrink with time, which is a
#     different and worse attack. A colour cannot carry a quantity, and the quantity IS the attack -
#     the player does not need to know something is coming, they need to know HOW MUCH MORE DAMAGE.
#   HIS OWN BODY. computah_overload_charge is 4 frames x 3 rows, so stepping charge_state 0 -> 1 -> 2
#     as the charge fills tells the same story for free. On THIS sheet row 0 is barely charged and row
#     2 is white-hot, the INVERSE of the battery sheets where row 0 is full.
#
# HE WIPES THE MAT AS HE STARTS. Refusing to start on a live pod would have been the same fairness
# rule, but the mine field is built to overlap itself and measured over a whole fight the mat is clear
# on 2 cycles in 35 - so the rule is kept by making it true rather than by waiting for it. See
# ComputahStateMachine.sweep_field().
#
# THE SILHOUETTE IS THE INVITATION. Both arms swept down and back, body arched, cannon hanging at his
# side with the muzzle on the mat - unmistakably not aiming at anybody. computah_mm.py asserts at
# build time that the muzzle never rises above the floor line, so the pose can never quietly start
# aiming, because that is the whole thing separating this from the braced beam: one says dodge, this
# one says come here and hit me.
#
# THE THRESHOLD ENDS THE CHARGE, NEVER THE HIT CAP. The window opens on overload_hit_cap, well above
# the punches the threshold needs, and it exists only so nothing is unbounded.
#
# THE THRESHOLD IS READ IN Physics_Update AND NEVER INSIDE take_punch(). The body increments a
# counter, this reads it the next physics step. That deliberately loses the race against
# PlayerFinisher._try_begin's deferred call, so the charged punch that breaks the charge can never
# also fire the finisher.
#
# FREEZE SAFETY: the clock is a Physics_Update accumulator and the blast's burst is a node-bound
# tween. Nothing here may use get_tree().create_timer() or a tree-level create_tween().

const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/ComputahArtLayout.gd")

const BLAST_ID := &"computah_overload_blast"

@export var body : CharacterBody2D
@export var fx_layer : Node2D
@export var charge_sfx_player : AudioStreamPlayer
@export var release_sfx_player : AudioStreamPlayer
@export var break_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

enum Phase { CHARGE, BROKEN, RELEASE, DISARM }

# The fractions of the charge his own rows step at. The chase's CHARGE_STEPS are these two numbers
# read the other way round, because its sheet is the other way round.
const CHARGE_STEPS := [0.34, 0.67]
# How long the fizzle and the discharge are held before what follows them: each is its own sheet's
# run time, so a redrawn animation is the only thing that moves them.
const BREAK_HOLD := 0.36
const RELEASE_HOLD := 0.38

const BLAST_SHAKE := 26.0
const BLAST_SHAKE_STEPS := 10
const BLAST_SHAKE_STEP_TIME := 0.03

var phase := Phase.CHARGE
var clock := 0.0
# Whether the blast was actually delivered to the player, as opposed to disarmed or broken first.
var blast_fired := false
# Set once the beat this state ends on has handed the fight on; it is already out of the machine.
var done := false

var burst: Node2D


func Enter() -> void:
	phase = Phase.CHARGE
	clock = 0.0
	blast_fired = false
	done = false
	body.velocity = Vector2.ZERO
	body.set_solid(true)
	body.set_target_active(true)
	# The standing chassis, as every pose that isn't kneeling or flat on the mat takes: the cannon is
	# scenery, and here it is pointing at the floor beside his leg.
	body.set_body_box(&"overload_charge")
	body.show_battery(false)
	body.set_charge_state(0)
	body.play_anim(&"overload_brace", &"overload_charge")
	# THE MAT IS WIPED AS HE PLANTS. The player is never asked to cross a minefield to reach him,
	# because by the time the charge starts there is no minefield; the pods break up through their own
	# expiring frames, so it reads as him pulling the charge back out of them.
	state_machine.sweep_field()

	# HE IS PUNCHABLE FROM THE FIRST FRAME, on a cap that is not the limiter.
	body.begin_window(state_machine.overload_hit_cap)
	body.set_hurtbox_active(true)
	state_machine.set_open(true)

	body.show_overload(true, state_machine.overload_threshold)
	body.show_aura(true)
	body.show_word("OVERLOAD")
	charge_sfx_player.play()


func Exit() -> void:
	charge_sfx_player.stop()
	_close_window()
	body.show_overload(false)
	body.show_aura(false)
	# Back to a FULL battery, which is what charge_state 0 means on every other sheet he has. Left at
	# 2 he would stand in the next beat looking flat.
	body.set_charge_state(Layout.Charge.FULL)
	body.set_body_box(&"idle")
	if is_instance_valid(burst):
		burst.queue_free()
	burst = null


func Physics_Update(delta: float) -> void:
	if done:
		return
	clock += delta
	match phase:
		Phase.CHARGE:
			_charge()
		Phase.BROKEN:
			if clock >= BREAK_HOLD:
				_drop()
		Phase.RELEASE:
			if clock >= RELEASE_HOLD:
				_vent()
		Phase.DISARM:
			if clock >= BREAK_HOLD:
				_vent()


# NO FINISHER MAY START MID-CHARGE, in any phase of this. A charged punch landing into the charge
# would otherwise freeze the fight and hand out the uppercut for NOT completing the check.
# ComputahStateMachine.allows_daze() asks this; ComputahScript.can_be_dazed() consults that.
func allows_daze() -> bool:
	return false


# HE DOES NOT RECOIL OUT OF THE CHARGE. The three-row read on his chest is the second half of what
# this attack says, and a 0.21 s recoil per punch would have it off screen for most of a charge that
# is being punched properly. The white flash, the sprite shake and the hit-stop that come with every
# landed punch are the feedback, and the gauge's bottom row is the one that matters.
func flinch() -> void:
	pass


#THE CHARGE

func _charge() -> void:
	if body.damage_this_window >= state_machine.overload_threshold:
		_broken()
		return
	if not state_machine.player_can_answer():
		_disarm()
		return
	# Faced every step, unlike the beam: nothing here is latched to his barrel, and the core on his
	# chest is the read, so having his back to a player who has run round him would hide it.
	var player: Node2D = state_machine.get_player()
	if player:
		body.face_toward(player.global_position)
	var along := clampf(clock / maxf(state_machine.overload_time, 0.01), 0.0, 1.0)
	body.set_charge_state(_charge_state(along))
	body.set_overload(along, mini(body.damage_this_window, state_machine.overload_threshold))
	if clock >= state_machine.overload_time:
		_release()


func _charge_state(along: float) -> int:
	if along >= CHARGE_STEPS[1]:
		return 2
	return 1 if along >= CHARGE_STEPS[0] else 0


#THE BREAK
# The reward, and it goes down the Break gauge's own road rather than a second one of its own: the
# sting, the lock and the daze behind it are all the gauge's, and there is only ever one kind of
# Break in this fight to keep in step.

func _broken() -> void:
	_set_phase(Phase.BROKEN)
	_close_window()
	body.show_overload(false)
	body.show_aura(false)
	body.play_anim(&"overload_break")
	charge_sfx_player.stop()
	break_sfx_player.play()


func _drop() -> void:
	done = true
	# Filled to the top, so BossBreakGauge._break() runs and his fight's Broken path opens the window.
	if body.break_now():
		return
	# No gauge, or it refused: the same window by hand, so the reward exists either way.
	state_machine.open_window(state_machine.overload_break_window, body.MAX_HITS_PER_WINDOW,
		&"collapse", &"down", &"reboot")


#THE DISARM
# THE BLAST IS ARMED WHEN THE CHARGE STARTS AND DISARMED BY ANYTHING THAT TAKES THE PLAYER'S INPUTS
# AWAY. Failing a check the player was never given a turn in is not their fault, so he vents it into
# the floor - NO BLAST, NO DAMAGE - on the same fizzle the broken charge uses. It does NOT drop him:
# being guard-broken is not a thing to be rewarded for.

func _disarm() -> void:
	_set_phase(Phase.DISARM)
	_close_window()
	body.show_overload(false)
	body.show_aura(false)
	body.play_anim(&"overload_break")
	charge_sfx_player.stop()
	break_sfx_player.play()


#THE BLAST
# IT COVERS THE WHOLE ARENA. No guard, no parry, no dash, and it carries neither tell because none of
# them is the answer: the answer was the punches, and they were not there.

func _release() -> void:
	_set_phase(Phase.RELEASE)
	_close_window()
	body.show_overload(false)
	body.show_aura(false)
	body.set_charge_state(2)
	body.play_anim(&"overload_release")
	charge_sfx_player.stop()
	release_sfx_player.play()
	body.shake_screen(BLAST_SHAKE, BLAST_SHAKE_STEPS, BLAST_SHAKE_STEP_TIME)
	_show_burst()
	_hit_player()


# The origin is the player's own hurtbox centre: the wave is everywhere, so there is no direction to
# face and nothing for a facing rule to be measured against.
func _hit_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	blast_fired = true
	var shape: Node = player.hurtBox.get_node_or_null("CollisionShape2D")
	var centre: Vector2 = shape.global_position if shape else player.global_position
	player.receive_hit(HitInfo.make(BLAST_ID, self, centre, body))


func _vent() -> void:
	done = true
	state_machine.open_window(state_machine.overload_vent, body.MAX_HITS_PER_WINDOW,
		&"vent", &"vent_hold", &"vent_up")


#DRAWING

func _show_burst() -> void:
	if Layout.USE_FINAL_OVERLOAD_BURST:
		return
	var spec := Layout.PLACEHOLDER_OVERLOAD_BURST
	var wave := Polygon2D.new()
	wave.polygon = Layout.ellipse(spec.radii, spec.points)
	wave.color = spec.color
	wave.material = Layout.additive()
	wave.global_position = body.frame_point(Layout.C_CORE).round()
	wave.scale = Vector2.ONE * float(spec.from_scale)
	wave.modulate.a = float(spec.from_alpha)
	fx_layer.add_child(wave)
	burst = wave
	# Node-bound, so a finisher's freeze holds it with the rest of the fight.
	var grow := wave.create_tween()
	grow.set_parallel(true)
	grow.tween_property(wave, "scale", Vector2.ONE * float(spec.to_scale), spec.time)
	grow.tween_property(wave, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(wave.queue_free)


#PLUMBING

func _set_phase(next: Phase) -> void:
	phase = next
	clock = 0.0


func _close_window() -> void:
	body.set_hurtbox_active(false)
	state_machine.set_open(false)
