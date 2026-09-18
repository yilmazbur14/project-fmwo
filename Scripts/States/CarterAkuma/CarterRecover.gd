extends State

@export var body : CharacterBody2D
@export var recover_timer : Timer
@export var recover_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Handed over by RagingDemon as it ends, and read once here.
var reds_parried := 0
var reds_missed := 0
var feints_parried := 0
var reds_total := 0


# The punish window: the only place punches reach him. How long it lasts is what the round earned -
# a parry's real reward is this, not the chip damage below.
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
	recover_timer.start(state_machine.recover_window(reds_parried, reds_missed))


func Exit() -> void:
	body.set_hurtbox_active(false)


# Three parries is a round read well; every red stopped with no feint bitten on is a perfect one.
func banked_damage() -> int:
	if reds_parried < 2:
		return 0
	if reds_total > 0 and reds_parried >= reds_total and feints_parried == 0:
		return 2
	return 1


func flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Idle")
