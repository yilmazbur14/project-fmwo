extends CanvasLayer

# The shared half of a boss entrance: the hold on the player while it plays, the walk that brings
# them into the ring, and the "hold to skip" hint. A boss's own entrance State instantiates one,
# calls begin(), drives its own beats around it, and calls end() once the ring is set.
#
# Eric (Scripts/States/Eric/EricIntro.gd) is the only fight using it. Liam's older entrance
# (BixbyBeastIntro) predates it and is deliberately left alone.
#
# THE HOLD IS `is_talking`, NOT lock_actions(). A locked player emits actions_locked, which
# PlayerCombatFx draws as a grey body tint - wrong for a walk-in. is_talking is the flag the
# pre-fight lines already hold the player with: it stops movement, punches, the guard and the dash
# alike. end() hands the hold straight on to the lines, and from them to the VS card.
#
# Everything here waits on node-bound tweens, so a pause stops the entrance where it is and a
# freeze or a hit-stop carries it with the fight. No get_tree().create_timer(), no tree-level tween.

signal skipped

# Under the dialogue balloon (100), the VS card (110) and the pause screen (120).
const LAYER := 90

# Seconds ui_cancel has to be held to skip. A hold rather than a press because the dialogue balloon
# already takes a ui_cancel press as "skip this line's typing" (balloon.gd's skip_action), and the
# lines play inside the entrance.
const SKIP_HOLD := 0.4
# ui_cancel on either device; it is never rebindable, so the names are fixed. Same wording as the
# intro cutscene's hint, with the hold spelled out.
const SKIP_HINT_KEYBOARD := "Hold ESC: skip"
const SKIP_HINT_GAMEPAD := "Hold B: skip"
const HINT_FADE := 0.3
const HINT_FONT_SIZE := 33
const HINT_COLOR := Color(0.60784316, 0.6784314, 0.7176471)
const HINT_SHADOW_COLOR := Color(0.078431375, 0.07058824, 0.12941177)
const HINT_BACKING := Color(0.043137256, 0.039215688, 0.07058824, 0.55)
const HINT_MARGIN := Vector2(21, 21)
const HINT_PADDING := 12.0
const UI_THEME := "res://Assets/UI/ui_theme.tres"

var player: Node
var hint: Label
var held := 0.0
var skip_sent := false
# A ui_cancel that is also the pause key is being held: this node owns it until it is let go, and
# decides then whether it was a skip or a pause.
var arbitrating := false


# Fights whose entrance has already played in this run. Kept on GameProgress, which is an autoload,
# so it survives the scene reload a retry after a loss goes through: nobody watches the same walk-in
# twice in a row.
static func already_seen(fight_scene: String) -> bool:
	return GameProgress.entrances_seen.has(fight_scene)


static func mark_seen(fight_scene: String) -> void:
	GameProgress.entrances_seen[fight_scene] = true


func _ready() -> void:
	layer = LAYER
	process_mode = Node.PROCESS_MODE_PAUSABLE
	set_process_input(false)
	_build_hint()


# The player is held where they stand and their state machine stopped, exactly as
# PlayerScript._stand_still() stops it: otherwise PlayerIdle would read a held direction and play
# the walk animation over the one the entrance is playing.
func begin(host_player: Node) -> void:
	player = host_player
	if player != null:
		player.is_talking = true
		player.velocity = Vector2.ZERO
		player.state_machine.set_process(false)
		player.state_machine.set_physics_process(false)
	set_process_input(true)
	_fade_hint(1.0)


# The ring is set and the lines are about to start. `is_talking` is deliberately left on: the lines
# own it from here, and the VS card takes it back when they end.
func end() -> void:
	if player != null and is_instance_valid(player):
		player.state_machine.set_process(true)
		player.state_machine.set_physics_process(true)
		play_player_anim(&"idle_down")
		player.clear_face_point()
	player = null
	if hint != null:
		_fade_hint(0.0)
	set_process(false)
	# Before the fade, not after it: this node takes the Escape key off the pause screen while it is
	# playing, and an entrance that is over must hand it straight back rather than eat it for another
	# 0.3 seconds.
	set_process_input(false)
	# After the fade, so the hint doesn't vanish on the skipping frame.
	var gone := create_tween()
	gone.tween_interval(HINT_FADE)
	gone.tween_callback(queue_free)


# Walks the player to `to` on rails. Awaitable; the tween is this node's, so a pause holds the walk.
func walk_player(to: Vector2, seconds: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	var from: Vector2 = player.global_position
	player.face_point(to)
	play_player_anim(&"walking")
	var walk := create_tween()
	walk.tween_method(_step_walk.bind(from, to), 0.0, 1.0, seconds)
	await walk.finished
	if not is_instance_valid(player):
		return
	player.global_position = to
	play_player_anim(&"idle_down")


# Whole pixels, so the pixel-art body doesn't shimmer as it walks.
func _step_walk(weight: float, from: Vector2, to: Vector2) -> void:
	if is_instance_valid(player):
		player.global_position = from.lerp(to, weight).round()


func play_player_anim(anim: StringName) -> void:
	if player == null or not is_instance_valid(player):
		return
	var animation_player: AnimationPlayer = player.get_node_or_null(^"AnimationPlayer")
	if animation_player != null:
		animation_player.play(anim)


# ESC IS BOTH KEYS. It is bound to ui_cancel, which skips an entrance, and to pause, which opens the
# pause screen - and the pause screen would take the press before the hold was ever long enough to
# count. So while an entrance is playing this node takes that one press itself: held past SKIP_HOLD
# it is a skip, let go before that it is a pause, and it opens the screen on the way out. A pad has
# no conflict to arbitrate - B is ui_cancel and Start is pause - so nothing there is touched.
#
# _input rather than _unhandled_input: the dialogue balloon swallows every unhandled event while a
# line is up, and the lines play inside the entrance.
func _input(event: InputEvent) -> void:
	if skip_sent or not event.is_action(&"ui_cancel") or not event.is_action(&"pause"):
		return
	if event.is_action_pressed(&"ui_cancel"):
		arbitrating = true
		InputSettings.note_device(event)
		get_viewport().set_input_as_handled()
	elif event.is_action_released(&"ui_cancel") and arbitrating:
		arbitrating = false
		get_viewport().set_input_as_handled()
		if held < SKIP_HOLD:
			_open_pause()


# Polled rather than read from an event: it is a hold, and a held key sends no repeats worth
# counting. PROCESS_MODE_PAUSABLE, so a pause mid-hold stops the clock instead of skipping under it.
func _process(delta: float) -> void:
	if skip_sent:
		return
	if not Input.is_action_pressed(&"ui_cancel"):
		held = 0.0
		return
	held += delta
	if held >= SKIP_HOLD:
		skip_sent = true
		arbitrating = false
		skipped.emit()


# The press this node took off the pause screen, handed back to it.
func _open_pause() -> void:
	var arena := get_tree().current_scene.get_node_or_null(^"Arena")
	var pause: Node = arena.get_node_or_null(^"PauseMenu") if arena != null else null
	if pause != null and pause.can_open():
		pause.open()


func _build_hint() -> void:
	hint = Label.new()
	hint.theme = load(UI_THEME)
	hint.text = SKIP_HINT_KEYBOARD
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hint.modulate.a = 0.0
	hint.add_theme_font_size_override("font_size", HINT_FONT_SIZE)
	hint.add_theme_color_override("font_color", HINT_COLOR)
	hint.add_theme_color_override("font_shadow_color", HINT_SHADOW_COLOR)
	hint.add_theme_constant_override("shadow_offset_x", 3)
	hint.add_theme_constant_override("shadow_offset_y", 3)
	var backing := StyleBoxFlat.new()
	backing.bg_color = HINT_BACKING
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
		backing.set_content_margin(side, HINT_PADDING)
	hint.add_theme_stylebox_override("normal", backing)
	add_child(hint)
	_place_hint()
	InputSettings.device_changed.connect(_place_hint.unbind(1))


# Top right, on the same margin whichever device's wording is showing.
func _place_hint() -> void:
	var gamepad: bool = InputSettings.device == InputSettings.Device.GAMEPAD
	hint.text = SKIP_HINT_GAMEPAD if gamepad else SKIP_HINT_KEYBOARD
	hint.size = hint.get_combined_minimum_size()
	hint.position = Vector2(get_viewport().get_visible_rect().size.x - hint.size.x - HINT_MARGIN.x, HINT_MARGIN.y)


func _fade_hint(to_alpha: float) -> void:
	var fade := hint.create_tween()
	fade.tween_property(hint, "modulate:a", to_alpha, HINT_FADE)
