extends CanvasLayer

# The shared half of a boss entrance: the hold on the player while it plays, the walk that brings
# them into the ring, and hold-to-skip with its hint. Every fight's entrance State instantiates one -
# Eric's, Computah's, Carter's, Josh's, Liam and Bixby's and Mason's - calls begin(), drives its own
# beats around it, calls release_player() once the ring is set, and keeps it up through the
# pre-fight lines. end() retires it once the lines have handed over to the VS card.
#
# ONE HOLD SKIPS THE WHOLE PRE-FIGHT SEQUENCE: the entrance, whatever is left of the lines, and the
# card's build-up, landing on the card's flash exactly where a watched entrance ends. That is why the
# skip stays live through the lines, and why `skipped` goes to the entrance's own skip_to_fight():
# only the entrance knows the end state of the beats its lines would still have called. The fight's
# state machine owns the one hand-over to the card (end_pre_fight_dialogue()), and the statics at
# the bottom are the parts every entrance's skip shares. Captain Burak's laugh cut (BurakBossLaugh) uses
# the same node for its own hold and skip.
#
# THE HOLD IS `is_talking`, NOT lock_actions(). A locked player emits actions_locked, which
# PlayerCombatFx draws as a grey body tint - wrong for a walk-in. is_talking is the flag the
# pre-fight lines already hold the player with: it stops movement, punches, the guard and the dash
# alike. release_player() leaves it on for the lines, and they hand it to the VS card.
#
# Everything here waits on node-bound tweens, so a pause stops the entrance where it is and a
# freeze or a hit-stop carries it with the fight. No get_tree().create_timer(), no tree-level tween.
#
# A NEW FIGHT ADOPTS IT LIKE THIS. The models: EricIntro, a walk-in that moves the player and lines
# that call beats; CarterIntro, a walk-in that leaves the player where they stand; JordanIntro, no
# walk-in at all. With no walk-in the lines are the whole entrance: there is no finish_entrance(),
# skip() or once-per-run flag, the intro is simply the state the fight waits in until the card is
# gone, and its skip_to_fight() is what the list below leaves of it.
#   The intro State:
#   - Enter(), on every path the retry included: builds one, connects `skipped` to its own
#     skip_to_fight(), and calls begin(player) - or begin() if the entrance never moves the player.
#     If already_seen(its fight scene), finish_entrance() and start the lines at once; if not, play
#     the walk-in, ending it with finish_entrance() and then the lines.
#   - Every tween it awaits, the walk-in's and the beats', goes through a `waits` list (append,
#     await, erase), and every await is followed by a bail: `finished` in the walk-in, `cut` in a beat
#     the lines call. A beat called once `cut` is set returns without awaiting anything. Stepping
#     callbacks bail the same way. That is what lets run_out() end it all inside the skip.
#   - finish_entrance(): idempotent; the ring as the fight expects it, release_player(), mark_seen().
#   - skip(): finish_entrance() and the lines started, which is what a retry does on its own. The
#     defence suite and the capture scripts find an entrance by its finish_entrance(), wait on its
#     `entered` and cut it with skip() unless `finished`; skip() is not the hold.
#   - skip_to_fight(), the hold: set `cut`, close_balloon(state_machine.pre_fight_balloon),
#     finish_entrance(), run_out(waits), then the end state of every beat the lines would still have
#     called, then state_machine.end_pre_fight_dialogue(), settle_arena() and card_to_flash(). It must
#     leave exactly what a watched entrance leaves at the VS card: the boss's sheet, animation,
#     position and facing; the player on their mark with their state machine back and is_talking
#     still on for the card; the HUD up; the music started once and at the same point; every prop
#     freed or in its final place; the view level, time_scale 1, the crowd at rest, nothing in the
#     fight's hazard group; and the lines never shown again.
#   - lines_over(): end(). Exit(): the same end state again, for a fight started over the top of it.
#   The fight's state machine:
#   - show_pre_fight_dialogue(): connects _on_dialogue_ended CONNECT_ONE_SHOT, and keeps the balloon
#     DialogueManager.show_dialogue_balloon() returns in `pre_fight_balloon`.
#   - _on_dialogue_ended(): sets `pre_fight_over`, calls the intro's lines_over(), then
#     VsCard.play_intro() as before.
#   - end_pre_fight_dialogue(): returns if pre_fight_over; otherwise disconnects the one-shot and
#     calls _on_dialogue_ended(null). It is the skip's only way to the card, so the fight can never
#     start twice.

signal skipped

const VsCard := preload("res://Scripts/VsCard.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")

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
# Longer than any wait an entrance has. Tween.custom_step() takes a number, and INF is not one.
const RUN_OUT_TIME := 3600.0

var player: Node
var hint: Label
var held := 0.0
var skip_sent := false
var retired := false
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


# `host_player` is held where they stand and their state machine stopped, exactly as
# PlayerScript._stand_still() stops it: otherwise PlayerIdle would read a held direction and play the
# walk animation over the one the entrance is playing. An entrance that never moves the player passes
# nobody, and leaves them as the scene loaded them - held by is_talking, which PlayerScript sets in
# its _ready and the lines already clear.
func begin(host_player: Node = null) -> void:
	player = host_player
	if player != null:
		player.is_talking = true
		player.velocity = Vector2.ZERO
		player.state_machine.set_process(false)
		player.state_machine.set_physics_process(false)
		# A walk-in starts them past the bottom rope, where the ring's net would put them straight back.
		player.may_leave_ring = true
	set_process_input(true)
	_fade_hint(1.0)


# The ring is set: the player's own state machine back, standing idle, their facing free again.
# `is_talking` is deliberately left on - the lines own it from here, and the VS card takes it from
# them - and the hint and the skip stay up, since the lines are part of what the hold skips.
func release_player() -> void:
	if player != null and is_instance_valid(player):
		player.state_machine.set_process(true)
		player.state_machine.set_physics_process(true)
		play_player_anim(&"idle_down")
		player.clear_face_point()
		player.may_leave_ring = false
	player = null


# Retired: the lines have handed over to the VS card, or a skip has.
func end() -> void:
	release_player()
	if retired:
		return
	retired = true
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
# counting. It keeps counting while a line is up, since the balloon's own take on the press doesn't
# reach Input. PROCESS_MODE_PAUSABLE, so a pause mid-hold stops the clock instead of skipping under it.
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


#THE SKIP'S SHARED PARTS

# The pre-fight balloon, taken down on the spot. free(), not queue_free(): the beat the lines are
# waiting on is about to be run out in the same call (run_out), and a balloon still alive at the end
# of that would be handed the next line and put it up.
static func close_balloon(balloon: Node) -> void:
	if not is_instance_valid(balloon):
		return
	if balloon.is_inside_tree():
		balloon.free()
	else:
		# Still waiting on the deferred call that adds it to the scene, which has to find it alive.
		balloon.queue_free()


# Every tween an entrance is waiting on, run to its end on the spot: `finished` fires inside this
# call, so the beat waiting on it - and the dialogue waiting on the beat - carries on here and bails,
# rather than surfacing again a few seconds into the fight. A wait that starts while this runs is run
# out too. Only waits ever go in the list: a looping tween never ends.
static func run_out(waits: Array[Tween]) -> void:
	while not waits.is_empty():
		var wait: Tween = waits.pop_back()
		if wait.is_valid():
			wait.custom_step(RUN_OUT_TIME)


# Where every skip leaves the arena, whatever beat it cut into: the view level and still, the fight
# at full speed and the crowd at rest - which is where a watched entrance has left all three by the
# time the first attack starts.
static func settle_arena(tree: SceneTree) -> void:
	ScreenView.reset(tree)
	HitStop.clear()
	tree.call_group("arena_crowd", "hush")


# The card the lines hand over to, jumped to its flash the way a press during it jumps it, so the
# fight starts behind the same wipe a watched entrance ends on.
static func card_to_flash(tree: SceneTree) -> void:
	var card := VsCard.in_fight(tree)
	if card != null and card.is_playing():
		card.skip()
