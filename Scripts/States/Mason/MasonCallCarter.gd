extends State

@export var animation_player : AnimationPlayer
@export var phone_sfx_player : AudioStreamPlayer
@export var phone_timer : Timer

const CARTER_ELBOW_DROP_SCENE := "res://Scenes/Bosses/CarterElbowDropScene.tscn"
const ParryTell := preload("res://Scripts/ParryTell.gd")
# The inside edges of the ropes. Carter's landings are kept within them, and his landed pose below the
# back rope, clear of the crowd and the health bar.
const ROPES := Rect2(113, 114, 1692, 853)

# Mason on the phone before the first drop comes down.
@export var phone_duration := 0.9

@onready var state_machine = get_parent()

var carter: Node2D
# Under phase two's shower Carter is set up before Mason makes the call, so being there is not the same
# as being on his way.
var sent := false
var telling := false


# Phase two's shower makes this same call while it rains (MasonNuggetShower), through the functions
# below, so the phone, the badge and the drops are one piece of code whichever attack makes the call.
func Enter() -> void:
	pick_up_phone()
	phone_timer.start(phone_duration)


# Leaving before Carter is done must not leave him dropping on the player.
func Exit() -> void:
	hang_up()


func Physics_Update(_delta: float) -> void:
	follow_drops()


func pick_up_phone() -> void:
	animation_player.play("phone")
	phone_sfx_player.play()
	# Up from the moment he picks up the phone, counting down to the first slam. His bombs and his
	# nuggets each say what they are; this was the one attack of his that said nothing, and a heavy
	# slam nobody knows is parryable is just a hit.
	telling = false
	var phase: int = state_machine.cycle_phase
	_tell(phone_duration + state_machine.elbow_telegraph[phase] + state_machine.elbow_dive[phase])


func hang_up() -> void:
	phone_timer.stop()
	_clear_tell()
	if is_instance_valid(carter):
		carter.queue_free()
	carter = null
	sent = false


# The badge follows the drops themselves: it stands over Mason while a marked slam is on its way, and
# goes out while Carter is picking himself up, when there is nothing to parry. The drop's own tween
# is the only clock the timings live on, so the marker it raises is what's read rather than a second
# count of the same cadence.
func follow_drops() -> void:
	if not sent or not is_instance_valid(carter):
		return
	var incoming: bool = carter.target_sprite.visible
	if incoming == telling:
		return
	if incoming:
		var phase: int = state_machine.cycle_phase
		_tell(state_machine.elbow_telegraph[phase] + state_machine.elbow_dive[phase])
	else:
		_clear_tell()


# Carter, set up for this phase's drops but not yet on his way.
func summon_carter(player: Node2D) -> Node2D:
	var phase: int = state_machine.cycle_phase
	carter = state_machine.spawn_hazard(CARTER_ELBOW_DROP_SCENE, player.global_position)
	sent = false
	# Before the footprint and the bounds are read off him: they follow the size he lands at.
	carter.hit_scale = state_machine.elbow_hit_scale
	carter.telegraph_time = state_machine.elbow_telegraph[phase]
	carter.dive_time = state_machine.elbow_dive[phase]
	carter.sit_up_time = state_machine.elbow_sit_up[phase]
	carter.leap_out_time = state_machine.elbow_leap_out[phase]
	carter.gap_between_drops = state_machine.elbow_gap[phase]
	carter.finished.connect(_on_carter_finished)
	return carter


# The call is made: Carter comes down on the player.
func send_carter() -> void:
	animation_player.play("idle")

	var player = state_machine.get_player()
	if not player:
		hang_up()
		state_machine.next_attack(self)
		return

	if not is_instance_valid(carter):
		summon_carter(player)
	# A landing whose footprint would touch Mason's sprite is kept away from him.
	var keep_out: Rect2 = state_machine.keep_out_around_mason(carter.footprint())
	carter.begin(state_machine.elbow_drops[state_machine.cycle_phase], player, carter.landing_bounds(ROPES), keep_out)
	sent = true


func _tell(lead: float) -> void:
	telling = true
	ParryTell.telegraph(state_machine.MasonCharacterBody, &"carter_elbow_drop", lead, _tell_anchor)


func _clear_tell() -> void:
	telling = false
	ParryTell.clear(state_machine.MasonCharacterBody)


# Over his hat, where the finisher's daze stars circle. Not the clearance ParryTell adds on top of
# that by default: at his top walk limit it would push the badge off the top of the screen.
func _tell_anchor() -> Vector2:
	return state_machine.MasonCharacterBody.get_daze_anchor()


func _on_phone_timer_timeout() -> void:
	send_carter()


func _on_carter_finished() -> void:
	# Carter frees himself once his last slam stops ringing.
	carter = null
	sent = false
	# Under the shower this is not the current state, so this leaves the cycle to the shower.
	state_machine.next_attack(self)
