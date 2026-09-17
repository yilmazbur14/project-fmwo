extends State

# Three cards in a row, each with its own wind-up. Held guard absorbs one for light stamina; a fresh
# press parries it for free, pays hype and builds the streak. Nothing here staggers him - the punish
# window comes after the third card either way.
# throw_interval is release to release. PlayerDefense.parry_mash_lockout is 0.5 s, so a press that
# misses card 1 still leaves a credited press in time for card 2. Do not shorten it below 0.65 s
# without re-reading PlayerDefense.on_block_pressed().

const THROWN_CARD_SCENE := preload("res://Scenes/Bosses/JoshThrownCardScene.tscn")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")

@export var body : CharacterBody2D
@export var throw_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# A card that never resolves must not hold the recovery up.
const FLIGHT_CAP := 2.0

var clock := 0.0
var told := 0
var thrown := 0
var waiting := false
var wait_clock := 0.0
var resolved_at := -1.0
var last_card: Node2D


func Enter() -> void:
	clock = 0.0
	told = 0
	thrown = 0
	waiting = false
	wait_clock = 0.0
	resolved_at = -1.0
	last_card = null
	body.fly_velocity = Vector2.ZERO
	_face_player()
	body.play_anim(&"idle")


func Exit() -> void:
	# A tell left standing would follow him into the next state.
	ParryTell.clear(body)


func Physics_Update(delta: float) -> void:
	if waiting:
		wait_clock += delta
		if resolved_at < 0.0:
			if not is_instance_valid(last_card) or wait_clock >= FLIGHT_CAP:
				resolved_at = wait_clock
		elif wait_clock - resolved_at >= state_machine.throw_recovery_delay:
			state_machine.on_child_transition(self, "Recover")
		return

	clock += delta
	while told < state_machine.throw_cards and clock >= told * state_machine.throw_interval:
		_tell()
		told += 1
	while thrown < state_machine.throw_cards and clock >= thrown * state_machine.throw_interval + state_machine.throw_tell:
		_release()
		thrown += 1
	if thrown >= state_machine.throw_cards:
		waiting = true
		wait_clock = 0.0


func _tell() -> void:
	_face_player()
	body.play_anim(&"throw")
	ParryTell.telegraph(body, &"josh_card_throw", state_machine.throw_tell, _tell_anchor)


func _release() -> void:
	ParryTell.clear(body)
	var player: Node2D = state_machine.get_player()
	var from: Vector2 = body.air.global_position + JoshArtLayout.local(JoshArtLayout.HAND_THROW, body.sprite.flip_h)
	var aim: Vector2 = _aim_point(player, from)
	var card := THROWN_CARD_SCENE.instantiate()
	card.speed = state_machine.card_speed
	card.direction = (aim - from).normalized()
	card.hit_size = state_machine.card_hit_size
	card.player = player
	state_machine.add_hazard(card, from, body.sky_layer)
	ParryTell.glow(card, &"josh_card_throw")
	throw_sfx_player.play()
	last_card = card


# Straight at where the player's hurtbox is the moment he lets go. No homing.
func _aim_point(player: Node2D, fallback: Vector2) -> Vector2:
	if not is_instance_valid(player):
		return fallback + Vector2(1, 0)
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


# His daze anchor is tuned for his downed frames, too low for a standing wind-up.
func _tell_anchor() -> Vector2:
	return body.tell_anchor()


# Set before the pose that uses it, so the throw is drawn toward the player.
func _face_player() -> void:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player):
		return
	body.flying_left = player.global_position.x < body.global_position.x
