extends State

@export var animation_player : AnimationPlayer
@export var phone_sfx_player : AudioStreamPlayer
@export var phone_timer : Timer

const CARTER_ELBOW_DROP_SCENE := "res://Scenes/Bosses/CarterElbowDropScene.tscn"
const PHONE_DURATION := 1.2
# The inside edges of the ropes. Carter's landings are kept within them, and his landed pose below the
# back rope, clear of the crowd and the health bar.
const ROPES := Rect2(113, 114, 1692, 853)

@onready var state_machine = get_parent()

var carter: Node2D


func Enter() -> void:
	animation_player.play("phone")
	phone_sfx_player.play()
	phone_timer.start(PHONE_DURATION)


# Leaving before Carter is done must not leave him dropping on the player.
func Exit() -> void:
	phone_timer.stop()
	if is_instance_valid(carter):
		carter.queue_free()


func _on_phone_timer_timeout() -> void:
	animation_player.play("idle")

	var player = state_machine.get_player()
	if not player:
		state_machine.next_attack(self)
		return

	var phase: int = state_machine.cycle_phase
	carter = state_machine.spawn_hazard(CARTER_ELBOW_DROP_SCENE, player.global_position)
	carter.telegraph_time = state_machine.ELBOW_TELEGRAPH[phase]
	carter.dive_time = state_machine.ELBOW_DIVE[phase]
	carter.sit_up_time = state_machine.ELBOW_SIT_UP[phase]
	carter.leap_out_time = state_machine.ELBOW_LEAP_OUT[phase]
	carter.gap_between_drops = state_machine.ELBOW_GAP[phase]
	carter.finished.connect(_on_carter_finished)
	# A landing whose footprint would touch Mason's sprite is kept away from him.
	var keep_out: Rect2 = state_machine.keep_out_around_mason(carter.footprint())
	carter.begin(state_machine.ELBOW_DROPS[phase], player, carter.landing_bounds(ROPES), keep_out)


func _on_carter_finished() -> void:
	# Carter frees himself once his last slam stops ringing.
	carter = null
	state_machine.next_attack(self)
