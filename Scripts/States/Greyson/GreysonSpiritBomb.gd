extends State

# Greyson's spirit bomb (plan section 3.6), the fight's loss: his meter is full, the cannon is loaded, and nothing
# the player does now matters. His HUD goes (the sphere covers the top of the screen) and he teleports to his cast
# spot, which the bomb's light layer was drawn for; the cannon arm goes up, the crowd's energy gathers into a
# sphere over it, he grins and throws it onto the player, and the whole screen goes off white and blue while the
# player comes apart over it (GreysonSpiritBombFx). Then the loss (FightOutro).
# A held skip (BossEntrance) lands where the watched bomb does: the player gone, the light out, the view level,
# then the loss. With playtest_invincible the bomb spares the player instead: his meter empties, his HUD comes
# back, he teleports home and the fight goes on.
# Every beat is an accumulator on this state's physics step, so a pause holds it.

const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const SpiritBombFx := preload("res://Scripts/GreysonSpiritBombFx.gd")

enum Beat { NONE, OUT, IN, ARM, GATHER, GRIN, LAUNCH, BLAST, HOME_OUT, HOME_IN, DONE }

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

#THE BEATS (seconds): about 6.4 s from the full meter to the loss
@export var hud_time := 0.25
# The teleport's out sheet and its in sheet. He shows from the in sheet's f3, and his arm goes up there.
@export var teleport_time := 0.3
@export var show_time := 0.15
# His spirit animations: the arm going up and held through the gather (spirit), the grin, the throw.
@export var arm_time := 0.5
@export var gather_time := 2.5
@export var grin_time := 0.5
@export var launch_time := 0.6

#THE REST
@export var duck_db := -10.0
# The rumble while the sphere grows, px, renewed every rumble_every seconds; the blast's shake.
@export var rumble := 3.0
@export var rumble_every := 0.5
@export var blast_shake := 24.0
# The view pushed in on the player for the explosion so their coming apart reads (FX_FOR_CODER's suggestion), and
# eased back out over the blast's tail. 1 leaves the view alone.
@export var blast_zoom := 2.0
@export var zoom_time := 0.3

var beat := Beat.NONE
var beat_left := 0.0
var clock := 0.0
var blast_clock := 0.0
var rumble_left := 0.0
var spared := false
var zoomed := false
var disintegrate_sounded := false
var player: Node2D
var cut: CanvasLayer
var fx: Node2D

# For the tests.
var entered_count := 0
# This bomb's clock as each beat began, by the beat's name, and at its end.
var beat_times := {}
var ended_at := -1.0
var skipped := false


func Enter() -> void:
	entered_count += 1
	beat_times.clear()
	clock = 0.0
	beat_left = 0.0
	ended_at = -1.0
	skipped = false
	zoomed = false
	disintegrate_sounded = false
	spared = GameProgress.playtest_invincible
	player = state_machine.get_player()
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	cut = BossEntrance.new()
	cut.name = "SpiritBombCut"
	add_child(cut)
	cut.skipped.connect(skip)
	cut.begin(player)
	cut.play_player_anim(&"idle_down")
	state_machine.face_player_at(body.global_position)
	# teleport_out() brings his HUD back, so the hide comes after it.
	body.teleport_out()
	body.hide_boss_hud(hud_time)
	body.duck_music(duck_db, hud_time)
	state_machine.crowd(&"roar", total_time(), false)
	_to(Beat.OUT, teleport_time)


func Exit() -> void:
	release()


func Physics_Update(delta: float) -> void:
	if beat == Beat.NONE or beat == Beat.DONE:
		return
	clock += delta
	match beat:
		Beat.GATHER:
			rumble_left -= delta
			if rumble_left <= 0.0:
				rumble_left += rumble_every
				ScreenView.shake(get_tree(), rumble, 10, rumble_every / 10.0)
		Beat.BLAST:
			_step_blast(delta)
	beat_left -= delta
	if beat_left <= 0.0:
		_next()


# The hold: straight to where the watched bomb ends.
func skip() -> void:
	if beat in [Beat.NONE, Beat.DONE, Beat.HOME_OUT, Beat.HOME_IN]:
		return
	skipped = true
	# The teleport's sheets would go on hiding and showing him as their frames came up.
	for sheet in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		sheet.free()
	body.global_position = state_machine.BOMB_CAST
	body.show_body()
	body.play_anim(&"spirit_throw")
	if fx == null:
		_add_fx()
	fx.settle(null if spared or player == null else player.sprite)
	ScreenView.reset(get_tree())
	zoomed = false
	beat_left = 0.0
	_end()


func release() -> void:
	beat = Beat.NONE
	_let_go()
	if zoomed and is_inside_tree():
		ScreenView.reset(get_tree())
	zoomed = false
	if is_instance_valid(fx):
		fx.queue_free()
	fx = null


# From the full meter to the loss, watched.
func total_time() -> float:
	return teleport_time + show_time + arm_time + gather_time + grin_time + launch_time + SpiritBombFx.blast_length()


func _to(next: Beat, seconds: float) -> void:
	beat = next
	beat_left += seconds
	beat_times[Beat.keys()[next]] = clock


func _next() -> void:
	match beat:
		Beat.OUT:
			body.teleport_in(state_machine.BOMB_CAST)
			state_machine.face_player_at(state_machine.BOMB_CAST)
			_to(Beat.IN, show_time)
		Beat.IN:
			body.play_anim(&"spirit")
			_to(Beat.ARM, arm_time)
		Beat.ARM:
			_add_fx()
			fx.gather(body.muzzle_point(&"spirit"), gather_time, _cooled())
			body.play_sfx(&"spirit_charge")
			rumble_left = 0.0
			_to(Beat.GATHER, gather_time)
		Beat.GATHER:
			body.play_anim(&"spirit_grin")
			_to(Beat.GRIN, grin_time)
		Beat.GRIN:
			body.play_anim(&"spirit_throw")
			fx.launch(state_machine.player_hurtbox_centre(), launch_time)
			body.play_sfx(&"spirit_launch")
			_to(Beat.LAUNCH, launch_time)
		Beat.LAUNCH:
			_blast()
			_to(Beat.BLAST, SpiritBombFx.blast_length())
		Beat.BLAST:
			_end()
		Beat.HOME_OUT:
			body.teleport_in(state_machine.HOME)
			_to(Beat.HOME_IN, teleport_time)
		Beat.HOME_IN:
			beat = Beat.DONE
			state_machine.on_child_transition(self, "Idle")


func _add_fx() -> void:
	fx = SpiritBombFx.new()
	body.floor_layer.add_child(fx)


# What the bomb's light falls on: everything drawn over its layer - the fighters, Computah lying in the ring, and
# the ropes and gates round it, which would stand out white against the blue.
func _cooled() -> Array:
	var cooled: Array = [body]
	if player != null:
		cooled.append(player)
	if is_instance_valid(body.computah):
		cooled.append(body.computah)
	for item in [get_tree().current_scene.get_node_or_null(^"Arena/wallBoundaries"), state_machine.gates()]:
		if item != null:
			cooled.append(item)
	return cooled


func _blast() -> void:
	blast_clock = 0.0
	# The sheet the player comes apart on is drawn from their standing frame.
	cut.play_player_anim(&"idle_down")
	fx.blast(null if spared else player.sprite, player.facing)
	body.play_sfx(&"spirit_explosion")
	if blast_zoom > 1.0:
		zoomed = true
		ScreenView.zoom_to(get_tree(), blast_zoom, player.global_position, zoom_time)
	ScreenView.shake(get_tree(), blast_shake, 12, 0.05)


func _step_blast(delta: float) -> void:
	blast_clock += delta
	if not spared and not disintegrate_sounded and blast_clock >= SpiritBombFx.blast_start(SpiritBombFx.LAYOUT.remains_from):
		disintegrate_sounded = true
		body.play_sfx(&"disintegrate")
	var tail := SpiritBombFx.blast_start(SpiritBombFx.LAYOUT.light_out_from)
	if zoomed and blast_clock >= tail:
		zoomed = false
		ScreenView.zoom_to(get_tree(), 1.0, player.global_position, SpiritBombFx.blast_length() - tail)


func _end() -> void:
	ended_at = clock
	if spared:
		_spare()
		return
	beat = Beat.DONE
	_let_go()
	FightOutro.finish_fight(get_tree(), false)


# The bomb spared a playtest-invincible player: his meter empty, his HUD back, the player free, and him home.
func _spare() -> void:
	body.reset_hype()
	body.duck_music(0.0, hud_time)
	_let_go()
	if player != null:
		player.is_talking = false
		state_machine.clear_player_facing()
	# teleport_out() brings his HUD back.
	body.teleport_out()
	_to(Beat.HOME_OUT, teleport_time)


func _let_go() -> void:
	if is_instance_valid(cut):
		cut.end()
	cut = null
