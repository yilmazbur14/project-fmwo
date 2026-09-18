extends State

@export var animation_player : AnimationPlayer
@export var phone_sfx_player : AudioStreamPlayer
@export var phone_timer : Timer

const CARTER_ELBOW_DROP_SCENE := "res://Scenes/Bosses/CarterElbowDropScene.tscn"
# The inside edges of the ropes. Carter's landings are kept within them, and his landed pose below the
# back rope, clear of the crowd and the health bar.
const ROPES := Rect2(113, 114, 1692, 853)

# Mason on the phone before the first drop comes down.
@export var phone_duration := 0.9

@onready var state_machine = get_parent()

var carter: Node2D


func Enter() -> void:
	animation_player.play("phone")
	phone_sfx_player.play()
	phone_timer.start(phone_duration)


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
	# Before the footprint and the bounds are read off him: they follow the size he lands at.
	carter.hit_scale = state_machine.elbow_hit_scale
	carter.telegraph_time = state_machine.elbow_telegraph[phase]
	carter.dive_time = state_machine.elbow_dive[phase]
	carter.sit_up_time = state_machine.elbow_sit_up[phase]
	carter.leap_out_time = state_machine.elbow_leap_out[phase]
	carter.gap_between_drops = state_machine.elbow_gap[phase]
	carter.finished.connect(_on_carter_finished)
	# A landing whose footprint would touch Mason's sprite is kept away from him.
	var keep_out: Rect2 = state_machine.keep_out_around_mason(carter.footprint())
	carter.begin(state_machine.elbow_drops[phase], player, carter.landing_bounds(ROPES), keep_out)


func _on_carter_finished() -> void:
	# Carter frees himself once his last slam stops ringing.
	carter = null
	state_machine.next_attack(self)
