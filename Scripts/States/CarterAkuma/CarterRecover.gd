extends State

@export var body : CharacterBody2D
@export var recover_timer : Timer
@export var recover_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Handed over by the attack that ended, through prepare(), and read once here.
var reds_parried := 0
var reds_missed := 0
var feints_parried := 0
var reds_total := 0
# The window in seconds when the attack decides it itself, or negative to earn it from the tally
# above. The Beam Rush sets it: what it earned is a Break, not a count of parried reds.
var window_override := -1.0


# EVERY attack hands over through here, and never by writing the fields directly. The tally below is
# plain state that survives the state being left, so an attack that set only some of it would cash in
# the previous attack's banked damage on top of its own.
func prepare(parried: int, missed: int, feints: int, total: int, window := -1.0) -> void:
	reds_parried = parried
	reds_missed = missed
	feints_parried = feints
	reds_total = total
	window_override = window


# The punish window: the only place punches reach him. How long it lasts is what the round earned -
# a parry's real reward is this, not the chip damage below.
# Gating his hurtbox to this state survives feel_v2's punch, which resolves at arm extension rather
# than on his report: a swing keeps retrying every frame until it ends, so a punch pressed up to 21
# frames (0.35 s) before the window opens still lands, against V1's 22. One frame of a 22-frame
# swing is the whole cost of the change.
func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	body.velocity = Vector2.ZERO
	body.show_body(true)
	body.play_anim(&"recover")
	# Before the hurtbox opens. Parries are banked and cashed here rather than applied as they land,
	# because a hit resolving mid-sequence would fire flinch() or the whole defeat sequence with the
	# player still locked and the arena still dark. is_recovering() is false until Enter() returns,
	# so this shows his hit flash without the recoil frame fighting the recovery pose.
	var banked := banked_damage()
	if banked > 0:
		body._apply_damage(banked)
	body.set_hurtbox_active(true)
	recover_sfx_player.play()
	recover_timer.start(window_override if window_override > 0.0 else state_machine.recover_window(reds_parried, reds_missed))


func Exit() -> void:
	body.set_hurtbox_active(false)


# One half-heart per bank_per_parries reds stopped, and a bonus on top for a barrage with every red
# stopped and no feint bitten on. Fifteen clones is roughly ten seconds of standing still, so a
# barrage read well is worth several times what the old five-clone one was.
func banked_damage() -> int:
	var banked := reds_parried / maxi(state_machine.bank_per_parries, 1)
	if reds_total > 0 and reds_parried >= reds_total and feints_parried == 0:
		banked += state_machine.bank_perfect_bonus
	return banked


func flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Idle")
