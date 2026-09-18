extends State

# Carter's one move, beats 0 to 4 in a single state:
#   FLASH  0.55 s  his eyes go, the mark flares, the room shakes. The player is locked on frame 1 of
#                  this and not a frame later - someone mid-dash has to stop BEFORE the yank.
#   YANK   0.35 s  he drags them to the middle of the ring. Driven, not teleported: the drive and the
#                  ghosts behind it are what make it read as him grabbing you rather than as a bug.
#   DARKEN 0.45 s  the crowd hushes, the music ducks, the dark comes in, a pool opens under them and
#                  he is swallowed by it.
#   RUSH  10.50 s  fifteen clones, one at a time and 0.70 s apart, each with a RED light (parry it)
#                  or a YELLOW one (a feint - parrying it punishes you). Identical timing either way;
#                  only the colour and the outcome differ, or the player would read the timing
#                  instead of the colour and the move would die. Bite on a feint and the clone after
#                  it comes in as a PUNISH, which nothing answers.
#                  None of them stop at the i-frames: being hit never hands the player the clones
#                  behind it for free.
#   CLEAR  0.50 s  the lights come up and he is standing there, open.
#
# IT IS ONE STATE ON PURPOSE. The lock, the player's draw order and the darkness have to be taken and
# given back as a unit, and a single Exit() funnel into release() is the only way every failure path -
# a win, a loss, a finisher, a scene change - is provably safe. Do not split it into three.
#
# FREEZE SAFETY: every wait here is a Physics_Update accumulator and every ramp is a node-bound
# tween, both of which a finisher's FightFreeze stops with the rest of the fight. Nothing here may
# use get_tree().create_timer() or a tree-level create_tween(): a freeze wouldn't hold them and the
# dark would ramp on in a stopped fight. A finisher can't start during this sequence today, but a
# second attack that allowed one would meet exactly that.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const CLONE_SCENE := preload("res://Scenes/Bosses/CarterCloneScene.tscn")
const HitInfo := preload("res://Scripts/HitInfo.gd")

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { FLASH, YANK, DARKEN, RUSH, CLEAR }

# The eight compass points a clone can come from, written out because a const can't call normalized().
const COMPASS: Array[Vector2] = [
	Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1),
	Vector2(0.70710678, 0.70710678), Vector2(-0.70710678, 0.70710678),
	Vector2(0.70710678, -0.70710678), Vector2(-0.70710678, -0.70710678),
]
# Reshuffles before the no-two-adjacent rule is given up on.
const PATTERN_TRIES := 20
# How far inside the ropes a clone and the spot he comes back at have to stay.
const SPAWN_MARGIN := 40.0
const RECOVER_MARGIN := 120.0
# carter_eye_flash.wav takes this long to inhale before its hit, so the sound starts first and the
# jolt lands on it.
const FLASH_LEAD := 0.04
const FLASH_SHAKE := 6.0
const FLASH_SHAKE_STEPS := 3
const FLASH_SHAKE_STEP_TIME := 0.06
const YANK_SHAKE := 11.0
const YANK_SHAKE_STEPS := 4
const YANK_SHAKE_STEP_TIME := 0.03
const MUSIC_DUCK_DB := -8.0
const MUSIC_DUCK_TIME := 0.2
const MUSIC_BACK_TIME := 0.25
# The clone that can't be answered arrives lower and heavier than the other fourteen.
const PUNISH_RUSH_PITCH := 0.78

var beat := Beat.FLASH
var beat_clock := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var listening := false
var flash_jolted := false
var player_stage_z := 0

# Locked at the top of the cycle: which clones lie and where each one comes from.
var feints: Array[bool] = []
var directions: Array[Vector2] = []
var reds_total := 0

var clone_index := -1
var clone_clock := 0.0
var clone: Node2D
var clone_launched := false
var clone_struck := false
var clone_punished := false
# What the live clone actually is. A feint the player bites on turns the NEXT one into a punish,
# whatever the pattern had planned for it, so this can't be read off `feints` alone.
var clone_is_feint := false
var clone_is_punish := false
var punish_next := false

var reds_parried := 0
var reds_missed := 0
var feints_parried := 0
var punishes_landed := 0

var yank_from := Vector2.ZERO
var yank_landed := false
var last_direction := Vector2.RIGHT
var ghosts: Array[Node2D] = []


func Enter() -> void:
	released = false
	beat = Beat.FLASH
	beat_clock = 0.0
	flash_jolted = false
	clone_index = -1
	clone_clock = 0.0
	clone = null
	clone_is_feint = false
	clone_is_punish = false
	punish_next = false
	reds_parried = 0
	reds_missed = 0
	feints_parried = 0
	punishes_landed = 0
	_build_pattern()
	listening = state_machine.connect_block_presses(_on_block_pressed)
	# On the first frame of the eye flash, not at the end of it.
	state_machine.lock_player()
	player_stage_z = state_machine.player_stage_z()
	state_machine.set_player_stage_z(CarterArtLayout.PLAYER_Z)

	body.velocity = Vector2.ZERO
	body.show_body(true)
	body.show_mark_glow(true)
	body.play_anim(&"eye_flash")
	body.flash_sfx_player.play()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent, and called from both Exit() and _exit_tree(). A player left locked in a sequence that
# ended is an unrecoverable bug - they can never move again - so every way out of this state runs
# through here, including the terminal ones that skip Exit() (CarterStateMachine._end_fight).
func release() -> void:
	if released:
		return
	released = true
	if state_machine and is_instance_valid(state_machine):
		state_machine.unlock_player()
		state_machine.clear_player_facing()
		state_machine.set_player_stage_z(player_stage_z)
		if listening:
			state_machine.disconnect_block_presses(_on_block_pressed)
	listening = false
	if is_instance_valid(body):
		body.snap_dark_clear()
		body.snap_music_level()
		body.show_body(true)
		body.show_mark_glow(false)
	_clear_clones()
	_clear_ghosts()
	clone = null


func Physics_Update(delta: float) -> void:
	# Polled here and only here, and only when PlayerDefense has no block_pressed signal to give:
	# polling in Update as well would punish one press twice.
	if not listening and beat == Beat.RUSH and Input.is_action_just_pressed("block"):
		_on_block_pressed(false)

	beat_clock += delta
	match beat:
		Beat.FLASH:
			if not flash_jolted and beat_clock >= FLASH_LEAD:
				flash_jolted = true
				body.shake_screen(FLASH_SHAKE, FLASH_SHAKE_STEPS, FLASH_SHAKE_STEP_TIME)
				body.shake_sprite(4.0, 3, FLASH_SHAKE_STEP_TIME)
			if beat_clock >= state_machine.flash_time:
				_begin_yank()
		Beat.YANK:
			_drive_yank()
		Beat.DARKEN:
			if beat_clock >= state_machine.darken_time:
				_begin_rush()
		Beat.RUSH:
			_advance_rush(delta)
		Beat.CLEAR:
			if beat_clock >= state_machine.clear_time:
				_hand_over()


#THE PATTERN

# Locked once, here, so a hit landing mid-sequence can never change what the rest of it does.
func _build_pattern() -> void:
	var count: int = maxi(state_machine.clone_count, 1)
	var yellows: int = clampi(state_machine.cycle_yellows, 0, maxi(count - 1, 0))
	reds_total = count - yellows

	feints.clear()
	feints.resize(count)
	feints.fill(false)
	# Clone 1 is never a feint: it teaches the rhythm at the top of every barrage.
	var slots: Array[int] = []
	for i in range(1, count):
		slots.append(i)
	var pick: Array = slots.slice(0, yellows)
	for attempt in PATTERN_TRIES:
		slots.shuffle()
		pick = slots.slice(0, yellows)
		# No two feints adjacent, at every tier. At a 0.70 s cadence two lies back to back are
		# unreadable rather than hard, and a bitten feint turns the clone after it into a punish -
		# which would eat the second feint and waste it. yellow_count() is capped so this always has
		# an answer.
		if not _adjacent(pick):
			break
	for index in pick:
		feints[index] = true

	# The first clone always comes from the left or the right - the reading the player already has.
	# After that: eight compass points and fifteen clones, so the deck is shuffled, dealt out and
	# shuffled again. The rule that survives the repeats is the one that matters, which is that no
	# two clones in a row ever come from the same side.
	var first: Vector2 = Vector2.LEFT if randi() % 2 == 0 else Vector2.RIGHT
	directions = [first]
	var deck: Array[Vector2] = []
	while directions.size() < count:
		if deck.is_empty():
			deck = COMPASS.duplicate()
			deck.shuffle()
			if deck[0] == directions[-1]:
				deck.push_back(deck.pop_front())
		directions.append(deck.pop_front())


func _adjacent(picked: Array) -> bool:
	for a in picked:
		for b in picked:
			if a != b and absi(a - b) == 1:
				return true
	return false


#THE YANK

func _begin_yank() -> void:
	beat = Beat.YANK
	beat_clock = 0.0
	yank_landed = false
	var player: Node2D = state_machine.get_player()
	yank_from = player.global_position if is_instance_valid(player) else state_machine.ARENA_CENTRE
	body.play_anim(&"summon")
	# Its arrival transient is 195 ms in, which is where yank_time puts the landing.
	body.yank_sfx_player.play()
	_spawn_yank_ghosts()


# Driven along a straight line with an ease-in, so he reads as pulling them in rather than blinking
# them across the ring. A locked player's _physics_process returns before anything moves them and
# never calls move_and_slide(), so writing the position here is what carries them.
func _drive_yank() -> void:
	var player: Node2D = state_machine.get_player()
	var weight := clampf(beat_clock / maxf(state_machine.yank_time, 0.0001), 0.0, 1.0)
	if is_instance_valid(player):
		player.global_position = yank_from.lerp(state_machine.ARENA_CENTRE, weight * weight).round()
	if not yank_landed and weight >= 1.0:
		yank_landed = true
		_land_yank()
	if beat_clock >= state_machine.yank_time + state_machine.yank_hold:
		_begin_darken()


func _land_yank() -> void:
	body.shake_screen(YANK_SHAKE, YANK_SHAKE_STEPS, YANK_SHAKE_STEP_TIME)
	_spawn_dust(state_machine.ARENA_CENTRE)


func _spawn_yank_ghosts() -> void:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player):
		return
	var count: int = CarterArtLayout.YANK_GHOSTS
	for i in count:
		var ghost := Sprite2D.new()
		ghost.texture = player.sprite.texture
		ghost.hframes = player.sprite.hframes
		ghost.vframes = player.sprite.vframes
		ghost.frame = player.sprite.frame
		ghost.scale = player.sprite.global_scale
		ghost.modulate = CarterArtLayout.YANK_GHOST_TINT
		body.floor_layer.add_child(ghost)
		ghost.global_position = yank_from.lerp(state_machine.ARENA_CENTRE, float(i) / count).round()
		ghosts.append(ghost)
		var fade := ghost.create_tween()
		fade.tween_interval(i * 0.04)
		fade.tween_property(ghost, "modulate:a", 0.0, CarterArtLayout.YANK_GHOST_FADE)
		fade.tween_callback(ghost.queue_free)


func _spawn_dust(at: Vector2) -> void:
	var spec := CarterArtLayout.YANK_DUST
	var puff := Polygon2D.new()
	puff.polygon = CarterArtLayout.ellipse(spec.radii, spec.points)
	puff.color = spec.color
	puff.scale = Vector2.ONE * spec.from_scale
	body.floor_layer.add_child(puff)
	puff.global_position = at.round()
	var play := puff.create_tween()
	play.tween_property(puff, "scale", Vector2.ONE * spec.to_scale, spec.time)
	play.parallel().tween_property(puff, "modulate:a", 0.0, spec.time)
	play.tween_callback(puff.queue_free)


#THE DARK

func _begin_darken() -> void:
	beat = Beat.DARKEN
	beat_clock = 0.0
	get_tree().call_group("arena_crowd", "hush")
	body.duck_music(MUSIC_DUCK_DB, MUSIC_DUCK_TIME)
	body.place_pool(state_machine.ARENA_CENTRE)
	body.darken(CarterArtLayout.DARKEN_TIME)
	body.open_pool(CarterArtLayout.POOL_OPEN_TIME)
	# Its spotlight clack is 38 ms in, so it starts as the dark does rather than when it has landed.
	body.dark_sfx_player.play()
	body.play_anim(&"vanish")


#THE FIVE RUSHES

func _begin_rush() -> void:
	beat = Beat.RUSH
	beat_clock = 0.0
	# He is swallowed by the dark: everything that follows is the clones.
	body.show_body(false)
	clone_index = -1
	_next_clone()


func _advance_rush(delta: float) -> void:
	clone_clock += delta
	if not clone_launched and clone_clock >= state_machine.clone_show:
		clone_launched = true
		if is_instance_valid(clone):
			clone.launch(state_machine.clone_dash)
		# The one that can't be answered comes in heavier than the rest.
		body.play_rush(clone_index, PUNISH_RUSH_PITCH if clone_is_punish else 1.0)
	if not clone_struck and clone_clock >= state_machine.clone_show + state_machine.clone_dash:
		clone_struck = true
		_strike()
	if clone_clock < state_machine.clone_interval():
		return
	if clone_index + 1 >= feints.size():
		_begin_clear()
	else:
		_next_clone()


func _next_clone() -> void:
	clone_index += 1
	clone_clock = 0.0
	clone_launched = false
	clone_struck = false
	clone_punished = false
	# A feint bitten on the clone before overrides whatever this one was going to be.
	clone_is_punish = punish_next
	punish_next = false
	clone_is_feint = feints[clone_index] and not clone_is_punish

	var player: Node2D = state_machine.get_player()
	var to_point: Vector2 = player.global_position if is_instance_valid(player) else state_machine.ARENA_CENTRE
	last_direction = directions[clone_index]
	var from_point := _spawn_point(to_point, last_direction)

	var rush := CLONE_SCENE.instantiate()
	rush.is_feint = clone_is_feint
	rush.is_punish = clone_is_punish
	rush.from_point = from_point
	rush.to_point = to_point
	rush.player = player
	rush.body = body
	state_machine.add_hazard(rush, from_point, body.clone_layer)
	clone = rush
	# The light comes up on the frame the clone appears, and the parry is re-armed on that same
	# frame, all five, every round. Without it a whiffed press on one clone can leave the next one
	# mathematically unparryable (PlayerDefense.parry_mash_lockout).
	clone.show_light()
	state_machine.rearm_parry()
	state_machine.face_player_at(from_point)


# Along the direction it was dealt, shortened rather than clamped per axis, so the clone still comes
# from its compass point. The bounds keep the whole clone AND the light over its head inside the
# view: at the full clone_radius a clone from due north would have its colour off the top of the
# screen, and a colour that can't be read is not a read.
func _spawn_point(to_point: Vector2, direction: Vector2) -> Vector2:
	var bounds := _clone_bounds()
	var inside := to_point.clamp(bounds.position, bounds.end)
	var reach: float = state_machine.clone_radius
	for axis in 2:
		if absf(direction[axis]) < 0.001:
			continue
		var edge: float = bounds.end[axis] if direction[axis] > 0.0 else bounds.position[axis]
		reach = minf(reach, (edge - inside[axis]) / direction[axis])
	return (inside + direction * maxf(reach, 0.0)).round()


func _clone_bounds() -> Rect2:
	var bounds: Rect2 = state_machine.ROPES.grow(-SPAWN_MARGIN)
	var headroom: float = -CarterArtLayout.clone_light_anchor().y + CarterArtLayout.CLONE_LIGHT_REACH
	var top := maxf(bounds.position.y, headroom)
	return Rect2(bounds.position.x, top, bounds.size.x, bounds.end.y - top)


# The contact instant. A red asks the player's defence for the outcome and is tallied by it; a yellow
# never reaches them at all and passes through.
func _strike() -> void:
	if not is_instance_valid(clone):
		return
	var result: int = clone.strike()
	clone = null
	if clone_is_feint:
		return
	# A punish clone was always going to land: it isn't a read the player failed, it is the bill for
	# the bait they already paid for, so it doesn't shorten the punish window on top.
	if clone_is_punish:
		if result == HitInfo.Result.HIT:
			punishes_landed += 1
		body.strike_sfx_player.play()
		return
	match result:
		HitInfo.Result.PARRIED:
			reds_parried += 1
			# The dark lifts for a moment, so the hit landing on him reads through it.
			body.lift_curtain()
			body.break_sfx_player.play()
		HitInfo.Result.BLOCKED:
			body.strike_sfx_player.play()
		HitInfo.Result.HIT:
			reds_missed += 1
			body.strike_sfx_player.play()


# A block press while a yellow's light is up: the colour was read wrong. It costs stamina and the
# streak and never health - they were never touched - and 40 stamina is more than any block in the
# game, so a player who keeps biting guard-breaks themselves.
# AND IT ARMS THE NEXT CLONE. Whatever that one was going to be, it comes in as a punish: hot, white
# and beating, and nothing the player does answers it. The bait is the mistake; the clone after it is
# the bill. It is drawn differently on purpose, so this never reads as a parry that failed.
func _on_block_pressed(_credited := false) -> void:
	if beat != Beat.RUSH or clone_index < 0 or clone_punished:
		return
	if not clone_is_feint:
		return
	if clone_clock > state_machine.clone_show + state_machine.clone_dash:
		return
	clone_punished = true
	feints_parried += 1
	punish_next = true
	state_machine.drain_stamina(state_machine.feint_stamina)
	state_machine.end_parry_streak()
	body.show_word("FEINT!")
	body.edge_pulse()
	body.feint_sfx_player.play()


#THE LIGHTS COMING UP

func _begin_clear() -> void:
	beat = Beat.CLEAR
	beat_clock = 0.0
	# The frame the dark starts clearing, so the player has their moves back before he is drawn.
	state_machine.unlock_player()
	state_machine.clear_player_facing()
	if listening:
		state_machine.disconnect_block_presses(_on_block_pressed)
		listening = false
	body.clear_dark(CarterArtLayout.CLEAR_TIME)
	body.finish_bloom()
	body.restore_music(MUSIC_BACK_TIME)
	body.finish_sfx_player.play()
	get_tree().call_group("arena_crowd", "cheer", 1.0)
	body.global_position = _recover_spot()
	body.show_body(true)
	body.show_mark_glow(false)
	body.play_anim(&"reappear")
	# Back under the ropes now that there is nothing to be lit against.
	state_machine.set_player_stage_z(player_stage_z)


# Out along the axis the last clone came from, so the eye already knows where to look.
func _recover_spot() -> Vector2:
	var axis := last_direction if last_direction != Vector2.ZERO else Vector2.RIGHT
	var bounds: Rect2 = state_machine.ROPES.grow(-RECOVER_MARGIN)
	return (state_machine.ARENA_CENTRE + axis * state_machine.recover_offset).clamp(bounds.position, bounds.end).round()


func _hand_over() -> void:
	var recover: State = state_machine.states.get("Recover")
	if recover:
		recover.reds_parried = reds_parried
		recover.reds_missed = reds_missed
		recover.feints_parried = feints_parried
		recover.reds_total = reds_total
	state_machine.on_child_transition(self, "Recover")


func _clear_clones() -> void:
	if not is_inside_tree():
		return
	for hazard in get_tree().get_nodes_in_group(state_machine.HAZARD_GROUP):
		hazard.queue_free()


func _clear_ghosts() -> void:
	for ghost in ghosts:
		if is_instance_valid(ghost):
			ghost.queue_free()
	ghosts.clear()
