extends State

# The kaiju winded by its own breath (the user, 2026-10-04: "jordan on [the kaiju] needs more openings to be hit"):
# JordanBreath hands over here once its last pass is out. It lowers its head and pants, and Jordan, riding it, clings on
# the lowered head within the player's reach for `window` seconds. Its POW dazes him for the single-bar finisher, as a
# knock-off's does (dazeable; the user, 2026-10-06: "yes give the kaiju breath opening the uppercut too"). Its back
# wall stands back to the front wall's edge for it (JordanKaijuLayout.RECOIL_WALL_X), so the floor in front of the
# lowered head can be stood on. As the head comes up a player still standing there is slid back out before the wall
# returns. An uppercut that lands shuts the opening at once (end_window) but keeps the head down until the finisher is
# over, so that slide never moves the player mid-uppercut. The line of fire the breath left burns on through it, but
# never on the floor in front of the head (JordanBurnLine.MOUTH_CLEAR). JordanStateMachine builds it when the kaiju is
# on.

const KaijuLayout := preload("res://Scripts/JordanKaijuLayout.gd")

enum Beat { LOWER, OPEN, LIFT }

# The head going down (the bow's first three frames), the opening, and the head coming back up. The opening is long
# enough to walk to him from the far corner of the ring (1.8 s) and land a 3-punch chain.
@export var lower_time := 0.3
@export var window := 3.0
@export var lift_time := 0.4
@export var pant_amount := 0.012
@export var pant_period := 0.5
@export var dazeable := true
@export var slide_time := 0.15

var body: CharacterBody2D
var hurtbox: Area2D
var state_machine: Node

var beat := Beat.LOWER
var clock := 0.0
var opened_at := -1.0
var lift_at := -1.0
var open := false
# An uppercut landed: the head comes up once the player's finisher is over.
var uppercut_landed := false
var slid: Node2D
var slide_from := Vector2.ZERO
var slide_to := Vector2.ZERO
var slide_left := 0.0
# For a test: when the opening opened and shut on this state's clock, and whether a player was slid out.
var opened := -1.0
var shut := -1.0
var slid_out := false


func Enter() -> void:
	beat = Beat.LOWER
	clock = 0.0
	opened_at = -1.0
	lift_at = -1.0
	opened = -1.0
	shut = -1.0
	slid_out = false
	uppercut_landed = false
	body.hits_this_window = 0
	body.daze_used = false
	var kaiju: Node2D = state_machine.kaiju
	kaiju.light_spines(0)
	kaiju.set_charge(0.0)
	kaiju.aim_head(0.0)
	kaiju.play_anim(&"bow")
	body.play_anim(&"ride_brace")


# Cut short (a Break, his defeat or theirs): a player still in front of the lowered head is put clear of the wall at once.
func Exit() -> void:
	_shut()
	_end_slide()
	var player: Node2D = state_machine.get_player()
	var spot := _outside_wall(player)
	if spot != Vector2.INF:
		player.global_position = spot.round()
	state_machine.kaiju.close_back_wall()
	state_machine.kaiju.art_scale = 1.0


func Physics_Update(delta: float) -> void:
	clock += delta
	var kaiju: Node2D = state_machine.kaiju
	match beat:
		Beat.LOWER:
			if clock >= lower_time:
				_open()
		Beat.OPEN:
			kaiju.art_scale = 1.0 + pant_amount * sin(TAU * (clock - opened_at) / pant_period)
			if uppercut_landed:
				if not _player_finishing():
					_lift()
			elif clock >= opened_at + window:
				_lift()
		Beat.LIFT:
			_step_slide(delta)
			if clock >= lift_at + lift_time and slide_left <= 0.0:
				state_machine.on_child_transition(self, "Idle")


func _open() -> void:
	beat = Beat.OPEN
	opened_at = clock
	opened = clock
	open = true
	state_machine.kaiju.open_back_wall(KaijuLayout.RECOIL_WALL_X)
	var box = body.anchor(&"body_box")
	if box != null:
		body.set_body_box(box)
	hurtbox.set_deferred("monitoring", true)
	hurtbox.set_deferred("monitorable", true)
	body.taunt_sfx_player.play()


func _lift() -> void:
	beat = Beat.LIFT
	lift_at = clock
	_shut()
	var kaiju: Node2D = state_machine.kaiju
	kaiju.art_scale = 1.0
	kaiju.play_anim(&"bow", &"idle", true)
	body.play_anim(&"ride_idle")
	_slide_player_out()


# The finisher's uppercut landed (JordanStateMachine.end_taunt): no more punches, and the head up once it is over.
func end_window() -> void:
	_shut()
	uppercut_landed = true


func _player_finishing() -> bool:
	var player: Node2D = state_machine.get_player()
	return player != null and player.finisher.is_active()


func _shut() -> void:
	if not open:
		return
	open = false
	shut = clock
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	body.restore_body_box()


# A player standing where the back wall comes back to is slid out in front of it, held for the slide, and then it comes
# back.
func _slide_player_out() -> void:
	var player: Node2D = state_machine.get_player()
	var spot := _outside_wall(player)
	if spot == Vector2.INF:
		state_machine.kaiju.close_back_wall()
		return
	slid = player
	slid_out = true
	slide_from = player.global_position
	slide_to = spot
	slide_left = slide_time
	player.lock_actions()


func _step_slide(delta: float) -> void:
	if slide_left <= 0.0:
		return
	slide_left -= delta
	if is_instance_valid(slid):
		var w := clampf(1.0 - slide_left / slide_time, 0.0, 1.0)
		slid.global_position = slide_from.lerp(slide_to, w).round()
	if slide_left <= 0.0:
		_end_slide()
		state_machine.kaiju.close_back_wall()


func _end_slide() -> void:
	if not is_instance_valid(slid):
		slid = null
		slide_left = 0.0
		return
	slid.global_position = slide_to.round()
	slid.unlock_actions()
	slid = null
	slide_left = 0.0


# Where the player stands clear of the whole back wall, or INF if they already do.
func _outside_wall(player: Node2D) -> Vector2:
	if player == null or not is_instance_valid(player):
		return Vector2.INF
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var wall: Rect2 = KaijuLayout.WALLS[0]
	if not wall.intersects(box):
		return Vector2.INF
	return Vector2(player.global_position.x + wall.end.x - box.position.x + 1.0, player.global_position.y)
