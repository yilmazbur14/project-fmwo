extends State

# ONE PARAMETERISED PUNISH WINDOW, SERVING ALL FOUR OF THEM. Greyson's crank after the laser,
# Computah's flat battery after the chase, and both of the phase-two ones go through here, so the
# rules of a window - the hit cap, the daze, the finisher's early end, what the body is drawn as -
# cannot drift apart between them.
# GcStateMachine.open_window() fills the fields in before the transition.
#
# A body held on the brink by the near-death clamp still gets its beat, but nothing opens: it holds
# the brink pose and takes nothing. That silence is the lever - it is the fight saying "stop hitting
# this one" in the only place the player is looking.

const Layout := preload("res://Scripts/GreysonComputahArtLayout.gd")

@export var greyson : CharacterBody2D
@export var computah : CharacterBody2D
@export var window_timer : Timer
@export var window_sfx_player : AudioStreamPlayer
@export var spark_layer : Node2D

@onready var state_machine = get_parent()

# Set by GcStateMachine.open_window() before the transition.
var window_body: Node = null
var window_time := 3.0
var window_cap := 3
var enter_anim := &""
var hold_anim := &""
var exit_anim := &""


func Enter() -> void:
	window_body.velocity = Vector2.ZERO
	if window_body == computah:
		computah.set_solid(true)
		computah.set_target_active(true)
		computah.show_battery(false)
		computah.set_down_box(enter_anim == &"collapse")

	if window_body.on_brink:
		window_body.play_anim(&"brink")
	else:
		window_body.begin_window(window_cap)
		window_body.play_anim(enter_anim, hold_anim)
		window_body.set_hurtbox_active(true)
		state_machine.set_open_body(window_body)
		window_sfx_player.play()
		# Greyson's window is him hauling on Computah's battery, so it happens over Computah.
		if window_body == greyson and state_machine.fight.is_alive(computah):
			_spark(computah)
	window_timer.start(window_time)


func Exit() -> void:
	window_timer.stop()
	if is_instance_valid(window_body):
		window_body.set_hurtbox_active(false)
		if window_body == computah:
			computah.set_down_box(false)
	state_machine.set_open_body(null)


func flinch(_body: Node) -> void:
	window_body.play_anim(&"hit", hold_anim)


func _on_window_timer_timeout() -> void:
	# The crank worked: Computah comes back on full cells, which is what the next chase runs on.
	if window_body == greyson and state_machine.fight.is_alive(computah) and not window_body.on_brink:
		computah.set_charge_state(0)
	if not window_body.on_brink and exit_anim != &"":
		window_body.play_anim(exit_anim, state_machine.rest_anim(window_body))
	state_machine.on_child_transition(self, "Idle")


# The battery throwing sparks, cranked or overheating. A coded placeholder with its own flag.
func _spark(over: Node2D) -> void:
	if Layout.USE_FINAL_BATTERY_SPARKS:
		return
	var spec := Layout.PLACEHOLDER_BATTERY_SPARKS
	var from: Vector2 = over.global_position + Layout.C_BEAM_ORIGIN
	for i in spec.count:
		var spark := Polygon2D.new()
		spark.polygon = Layout.centred_rect(Vector2.ONE * spec.size)
		spark.color = spec.color
		spark.material = Layout.additive()
		spark_layer.add_child(spark)
		spark.global_position = from
		var to := from + Vector2(randf_range(-spec.reach.x, spec.reach.x), randf_range(-spec.reach.y, spec.reach.y))
		var fly := spark.create_tween()
		fly.tween_method(func(weight: float) -> void:
			spark.global_position = (from.lerp(to, weight) - Vector2(0, spec.rise * 4.0 * weight * (1.0 - weight))).round()
			spark.modulate.a = 1.0 - weight
		, 0.0, 1.0, spec.time).set_delay(i * 0.04)
		fly.tween_callback(spark.queue_free)
