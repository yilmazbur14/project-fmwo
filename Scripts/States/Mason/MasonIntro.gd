extends State

# Mason's entrance, and the joke the whole fight opens on: he is lured into the ring with food. The
# ropes open, the player walks up into them, and a trail of dropped fries runs out of the dark down
# to the spot Mason fights from. He waddles in along it with his head down, stopping at every pile,
# and each one goes as he reaches it - so he is still chewing when the gates slam behind him and the
# only thing that tells him he has been had is the door. MasonPreFight.dialogue takes it from there,
# and the VS card and the fight hang off dialogue_ended exactly as they did before.
#
# Every wait is a node-bound tween, so a pause stops the entrance where it is and a hit-stop carries
# it with the fight. Nothing here uses get_tree().create_timer() or a tree-level tween.
#
# A cut-short entrance never kills a tween something is waiting on: `finished` makes every beat bail
# and every stepping callback a no-op instead, so nothing is left half-drawn and nothing hangs. A
# held skip runs those waits out on the spot rather than letting them run their time
# (BossEntrance.run_out).

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")
# This fight's place in the order, for the entrance's once-per-run flag.
const FIGHT_SCENE := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const GATES_PATH := "Arena/Gates"

#THE WALK-IN
# Both fighters are moved by written global_position, so nothing collides and nothing desyncs. He
# starts this far above his mark, which puts the whole of him off the top of the screen; the player
# rises from this far below theirs.
const WALK_IN_RISE := 400.0
const PLAYER_WALK_DROP := 260.0
const PLAYER_WALK_TIME := 1.6
# The walk down out of the dark to the first pile, which is the only part of his walk in that has no
# fries on it (MasonArtLayout.FRY_TRAIL_SPAN).
const APPROACH_TIME := 0.8
# One stop on the trail: the waddle up to the next pile, then the gobble he stands still for.
const LEG_TIME := 0.2
const GOBBLE_TIME := 0.3
# What the stand-in's pieces do instead of the drawn ones' residue frames (MasonArtLayout.FRY_EATEN).
const CRUMB_FADE := 0.16
const CRUMB_ALPHA := 0.45
const CRUMB_SHRINK := 0.4

#BEATS, IN SECONDS
# The ring sits open on the trail before anything moves, so the fries are read before he is.
const OPEN_BEAT := 0.4
# The player, in the ring, looking at the trail.
const PLAYER_BEAT := 0.5
# After the slam and his jolt, before his first line.
const SETTLE_BEAT := 0.45
const PLAYER_CHEER := 1.6

#THE PENNY DROPPING
# He hears the gates before he understands them: the chewing stops, he jolts on the spot, and he is
# looking up by the time the line starts.
const STARTLE_RISE := 14.0
const STARTLE_UP_TIME := 0.06
const STARTLE_DOWN_TIME := 0.1

@export var animation_player : AnimationPlayer
@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# The entrance layer: the hold on the player, their walk, and the skip and its hint through the lines.
var entrance: CanvasLayer
# The trail on the floor, and the pile standing at each stop of it.
var trail: Node2D
var piles: Array[Node2D] = []
# Where the two of them end up, read off the scene so nothing here hardcodes a mark.
var home := Vector2.ZERO
var player_home := Vector2.ZERO
# The entrance is over, one way or another. Every beat checks it; finish_entrance() and Exit() are
# the only things that set it.
var finished := false
var dialogue_started := false
# Enter() is deferred, so anything that can reach in from outside checks this first: there is no ring
# to set before it has run.
var entered := false
# A held skip took everything up to the VS card, and the lines are gone.
var cut := false
# The tweens the walk-in is waiting on, for the skip to run out.
var waits: Array[Tween] = []
var startle: Tween
var sfx_players := {}
# Piles eaten, so a test can see that every one of them went.
var gobbles := 0


func Enter() -> void:
	# Deferred, so the fight may already have been started over the top of this state (Exit): there
	# is nothing left to walk in if it has.
	if finished:
		return
	entered = true
	home = body.global_position
	var player := _player()
	player_home = player.global_position if player != null else Vector2.ZERO
	_build_sfx()
	# On the retry path too: the walk-in is skipped there, but the lines still play and the hold
	# still skips them.
	entrance = BossEntrance.new()
	entrance.name = "BossEntrance"
	add_child(entrance)
	entrance.skipped.connect(_on_skipped)
	entrance.begin(player)
	if BossEntrance.already_seen(FIGHT_SCENE):
		animation_player.play("idle")
		finish_entrance()
		_start_dialogue()
		return
	# Both of them are put outside the ring here, in the frame the state is entered, rather than when
	# their own walk comes round: anywhere later and they are seen standing on their marks first and
	# sliding back out to the entrance.
	animation_player.play("waddle")
	body.global_position = _stop_point(-1)
	if player != null:
		player.global_position = player_home + Vector2(0, PLAYER_WALK_DROP)
	_play()


# The fight starts here. A harness that starts it over the top of the entrance leaves through here
# too, so this is also what guarantees the ring is set however the entrance ended.
func Exit() -> void:
	finish_entrance()
	finished = true
	_clear_trail()
	if is_instance_valid(entrance):
		entrance.queue_free()
	entrance = null


#THE WALK-IN

func _play() -> void:
	# HIS BARS COME UP WITH THE GATES, NOT BEFORE HIM. They sit across the top of the ring, which is
	# where his mark is: left up they cover the top rope, both the doorway he comes through and the
	# gate that shuts it, and the whole first half of the trail - the gobbles nobody could see were
	# what the first capture of this showed. Announcing a boss who has not walked in yet was the
	# wrong way round anyway.
	if body.hud_layer != null:
		body.hud_layer.hide()
	var gates := _gates()
	if gates != null:
		gates.open()
	_lay_trail()
	await _beat(OPEN_BEAT)
	if finished:
		return

	# The player walks up into the ring, and stands over the end of the trail.
	var player := _player()
	if player != null:
		get_tree().call_group("arena_crowd", "cheer", PLAYER_CHEER)
		await entrance.walk_player(player_home, PLAYER_WALK_TIME)
	if finished:
		return
	await _beat(PLAYER_BEAT)
	if finished:
		return

	# Nobody cheers a man eating chips off the floor, and the quiet is what the slam breaks.
	get_tree().call_group("arena_crowd", "hush")
	await _walk_the_trail()
	if finished:
		return

	if gates != null:
		await gates.close()
	if finished:
		return
	_startle()
	await _beat(SETTLE_BEAT)
	if finished:
		return
	# The ring is set, so the player goes straight on to the lines, and the skip with them. His own
	# last beat does this where Eric's last dialogue beat does it: Mason's lines call nothing.
	finish_entrance()
	_start_dialogue()


# Pile by pile down the trail: a waddle up to the next one, then a stop to gobble it. The first leg
# is the longer walk out of the dark to where the fries start. He is left chewing on the last pile -
# the slam is meant to catch him mid-mouthful.
func _walk_the_trail() -> void:
	var march := create_tween()
	for stop in MasonArtLayout.FRY_TRAIL.size():
		march.tween_callback(_show_waddle)
		var leg := APPROACH_TIME if stop == 0 else LEG_TIME
		march.tween_method(_step.bind(_stop_point(stop - 1), _stop_point(stop)), 0.0, 1.0, leg)
		march.tween_callback(_gobble.bind(stop))
		march.tween_interval(GOBBLE_TIME)
	await _wait(march)
	if finished:
		return
	body.global_position = home


# Whole pixels, so the pixel-art body doesn't shimmer as it walks.
func _step(weight: float, from: Vector2, to: Vector2) -> void:
	if finished:
		return
	body.global_position = from.lerp(to, weight).round()


func _show_waddle() -> void:
	if finished:
		return
	animation_player.play("waddle")


# He reaches a piece: it is crumbs by the time he has stepped over it, and he stands there chewing.
func _gobble(stop: int) -> void:
	if finished:
		return
	gobbles += 1
	animation_player.play("eat")
	_play_sfx("gobble")
	_eat_piece(stop)


# The door he did not hear open, shutting: he stops dead, jolts, and is standing up looking at it.
func _startle() -> void:
	animation_player.play("idle")
	var sprite: Sprite2D = body.sprite
	startle = sprite.create_tween()
	startle.tween_property(sprite, "position", body.sprite_base_position - Vector2(0, STARTLE_RISE), STARTLE_UP_TIME)
	startle.tween_property(sprite, "position", body.sprite_base_position, STARTLE_DOWN_TIME)


#THE TRAIL

# One piece per stop, on the floor under where his feet will be when he reaches it.
func _lay_trail() -> void:
	trail = Node2D.new()
	trail.name = "FryTrail"
	# Y-sorted with the rest of the arena rather than a flat layer of its own: a piece then sorts on
	# its own row, so the end of the trail lies on the mat, the far end goes behind the crowd band it
	# comes out of, and the one he is standing over draws at his feet.
	trail.y_sort_enabled = true
	body.get_parent().add_child(trail)
	for stop in MasonArtLayout.FRY_TRAIL.size():
		var piece := _build_piece(stop)
		trail.add_child(piece)
		piece.global_position = _stop_point(stop) + MasonArtLayout.frame_local(MasonArtLayout.FEET_PIXEL)
		piles.append(piece)


# The piece he has just reached, left as what he left of it. The drawn pieces have their own residue
# frames; the stand-in has none, so it keeps a dimmed crumb of itself in the same spot for the same
# reason - the line has to visibly turn to crumbs behind him rather than empty.
func _eat_piece(index: int) -> void:
	if index < 0 or index >= piles.size() or not is_instance_valid(piles[index]):
		return
	var drawn := piles[index] as Sprite2D
	if drawn != null:
		drawn.frame = MasonArtLayout.FRY_EATEN[MasonArtLayout.FRY_TRAIL[index].frame]
		return
	var piece: Node2D = piles[index]
	var crumbs := piece.create_tween()
	crumbs.tween_property(piece, "modulate:a", CRUMB_ALPHA, CRUMB_FADE)
	crumbs.parallel().tween_property(piece, "scale", piece.scale * CRUMB_SHRINK, CRUMB_FADE)


# Whatever he never reached, left as if he had: a skipped entrance leaves the same mat a watched one
# does.
func _eat_the_rest() -> void:
	for index in range(gobbles, piles.size()):
		_eat_piece(index)
	gobbles = piles.size()


func _clear_trail() -> void:
	piles.clear()
	if is_instance_valid(trail):
		trail.queue_free()
	trail = null


func _build_piece(index: int) -> Node2D:
	if MasonArtLayout.USE_FINAL_FRY_TRAIL:
		return _drawn_piece(index)
	return _placeholder_piece()


# Centred, because every frame of the sheet is drawn centred on its own middle texel: the sprite's
# position is the floor point and there is no offset to keep in step with a redraw.
func _drawn_piece(index: int) -> Node2D:
	var art := MasonArtLayout.FINAL_FRY_TRAIL
	var spec: Dictionary = MasonArtLayout.FRY_TRAIL[index]
	var piece := Sprite2D.new()
	piece.texture = load(art.texture)
	piece.hframes = art.hframes
	piece.frame = spec.frame
	piece.flip_h = spec.flip
	piece.scale = Vector2.ONE * art.scale
	return piece


# A dropped pile in his own palette: a blob of ketchup with loose sticks fanned over it, each one a
# yellow rect with a darker end, keylined the way his sheet keylines them.
func _placeholder_piece() -> Node2D:
	var art := MasonArtLayout.PLACEHOLDER_FRY_TRAIL
	var pile := Node2D.new()
	pile.scale = Vector2.ONE * art.scale
	pile.add_child(_keylined(art.ketchup, art.ketchup_color, art.keyline))
	for spec in art.fries:
		var fry := Node2D.new()
		fry.position = spec.at
		fry.rotation = spec.turn * TAU
		fry.add_child(_keylined(art.fry, art.fry_color, art.keyline))
		fry.add_child(_panel(Rect2(-art.tip.x / 2.0, art.fry.y / 2.0 - art.tip.y, art.tip.x, art.tip.y), art.tip_color))
		pile.add_child(fry)
	return pile


# One shape centred on its own origin, drawn over a keyline a texel proud of it on every side.
func _keylined(size: Vector2, colour: Color, keyline: Color) -> Node2D:
	var shape := Node2D.new()
	shape.add_child(_panel(Rect2(-size.x / 2.0 - 1.0, -size.y / 2.0 - 1.0, size.x + 2.0, size.y + 2.0), keyline))
	shape.add_child(_panel(Rect2(-size.x / 2.0, -size.y / 2.0, size.x, size.y), colour))
	return shape


func _panel(rect: Rect2, colour: Color) -> Polygon2D:
	var panel := Polygon2D.new()
	panel.polygon = PackedVector2Array([
		rect.position,
		rect.position + Vector2(rect.size.x, 0),
		rect.position + rect.size,
		rect.position + Vector2(0, rect.size.y),
	])
	panel.color = colour
	return panel


# Where his body stands at stop `index` of the trail, -1 being the spot off the top of the screen he
# starts from. The stops are evenly spaced down the trail's own span and the last one is his mark;
# the start is further up than the trail reaches, so the walk out of the dark has no fries on it.
func _stop_point(index: int) -> Vector2:
	if index < 0:
		return home - Vector2(0, WALK_IN_RISE)
	var span: float = MasonArtLayout.FRY_TRAIL_SPAN
	var stops: Array = MasonArtLayout.FRY_TRAIL
	var along: float = span * float(index + 1) / float(stops.size())
	return Vector2(home.x + stops[index].across, home.y - span + along).round()


#ENDING IT

# The one way the entrance ends: its last beat, a skip, or the fight being started over the top of
# it. Idempotent - it leaves the ring exactly as the fight expects it whichever of those got here.
func finish_entrance() -> void:
	if finished or not entered:
		return
	finished = true
	if startle != null and startle.is_valid():
		startle.kill()
	body.sprite.position = body.sprite_base_position
	body.global_position = home
	animation_player.play("idle")
	# Not cleared here: the crumbs stay on the mat through his lines, and the fight starting (Exit) is
	# what takes them off it.
	_eat_the_rest()
	if body.hud_layer != null:
		body.hud_layer.show()
	var gates := _gates()
	if gates != null:
		gates.shut_now()
	var player := _player()
	if player != null:
		player.global_position = player_home
	if is_instance_valid(entrance):
		entrance.release_player()
	BossEntrance.mark_seen(FIGHT_SCENE)


# The walk-in cut on the spot and the lines started: where a second go at the fight starts on its
# own. Public, so the defence suite can cut the entrance this way - its modes are about the fight,
# and read the lines or throw them away themselves.
func skip() -> void:
	if cut:
		return
	finish_entrance()
	_start_dialogue()


# What a held ui_cancel does: the walk-in, whatever is left of the lines and the card's build-up, all
# at once, landing on the card's flash. His lines call no beats, so the ring finish_entrance() sets
# is all there is to leave.
func skip_to_fight() -> void:
	if not entered or cut:
		return
	cut = true
	BossEntrance.close_balloon(state_machine.pre_fight_balloon)
	finish_entrance()
	BossEntrance.run_out(waits)
	state_machine.end_pre_fight_dialogue()
	BossEntrance.settle_arena(get_tree())
	BossEntrance.card_to_flash(get_tree())


func _on_skipped() -> void:
	skip_to_fight()


# The lines have handed over to the VS card, and the skip goes with them.
func lines_over() -> void:
	if is_instance_valid(entrance):
		entrance.end()


func _start_dialogue() -> void:
	if dialogue_started or cut:
		return
	dialogue_started = true
	state_machine.show_pre_fight_dialogue()


#PIECES

# Built here rather than wired into the scene, the way MasonScript builds its Break stings: the table
# in MasonArtLayout is the only place they are named.
func _build_sfx() -> void:
	if not sfx_players.is_empty():
		return
	for key in MasonArtLayout.INTRO_SFX:
		var spec: Dictionary = MasonArtLayout.INTRO_SFX[key]
		var sfx := AudioStreamPlayer.new()
		sfx.stream = load(spec.stream)
		sfx.pitch_scale = spec.pitch
		sfx.volume_db = spec.volume_db
		add_child(sfx)
		sfx_players[key] = sfx


func _play_sfx(key: String) -> void:
	var sfx: AudioStreamPlayer = sfx_players.get(key)
	if sfx != null and sfx.stream != null:
		sfx.play()


# Waits `seconds` on this node's own clock. A cut-short entrance lets it run out rather than killing
# it, and the caller's own `finished` check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _player() -> Node:
	return get_tree().current_scene.get_node_or_null(PLAYER_PATH)


func _gates() -> Node:
	return get_tree().current_scene.get_node_or_null(GATES_PATH)
