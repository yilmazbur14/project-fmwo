extends Node2D

# The practice floor on the Controls screen. Danny finishes his lines, the balloon closes and the
# player is left alone with a sparring dummy to punch, combo, parry, dodge, guard-break and mash for
# as long as they like before walking into Arena #1.
# Everything here is the real system: the room switches the player onto feel_v2 exactly as
# BossOneScript does, because its only exit is Eric's fight, and the dummy answers every contract a
# boss does. The two things it changes are that the dummy cannot die and neither can the player.
#
# The player MUST NOT be able to lose in here. PlayerScript._process fires FightOutro.finish_fight
# at zero health, and FightOutro.PLAYER_PATH is hard-coded to "Arena/MainPlayer/CharacterBody2D",
# which this scene does not have: a death would both end the room with a defeat screen and crash on
# the way out. That is what the health floor below is for, and why it runs at a lower priority than
# the player's own _process.

const TrainingDummyArtLayout := preload("res://Scripts/TrainingDummyArtLayout.gd")
const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")
const UI_THEME := "res://Assets/UI/ui_theme.tres"
const ERIC_FIGHT := "res://Scenes/Bosses/EricBossFightScene.tscn"

# What a pad confirms with. Y is the only face button free in both layouts: A is punch and
# ui_accept, B is dodge and ui_cancel, X is punch in the old layout, LB is block and mash_left, RB
# is dodge and mash_right, Start is pause (InputSettings). It is read here rather than registered as
# an action, because it is this room's way out and not a thing the game does anywhere else - so it
# is deliberately not rebindable and not in the bindings file.
const CONFIRM_PAD_BUTTON := JOY_BUTTON_Y
# The glyph is 96 px square; the button's content box is 67 px tall.
const CONFIRM_GLYPH_WIDTH := 64

# The tiled floor between the cards and the bottom of the screen. The walls box exactly this.
const PLAY_BAND := Rect2(130, 730, 1760, 330)
const WALL_THICKNESS := 80.0

# Walking into the post flips the dummy; it has to be left and re-entered before it flips back, and
# not inside this many seconds either way, so brushing its edge can't strobe the mode.
const MODE_COOLDOWN := 0.5
# The strip under the Arena #1 door. A walk crosses it in about half a second and a dash in 0.05, so
# only a deliberate walk holds it long enough.
const DOOR_DWELL := 0.35

const REFILL_TIME := 1.2
const FULL_HEALTH := 6

# The cards own the top 40% of the screen, and they are reference art: worth reading, not worth
# reading mid-combo. So they get out of the way while the player is practising and come back when
# they stop. Nothing new is bound and there is no new verb to learn - playing hides them, stopping
# brings them back, which is the only rule anyone has to work out.
# The wait before they go is what keeps one stray punch from wiping the screen; the wait before they
# return is what keeps a beat between combos from flapping them.
const CARDS_DIM := 0.15
const CARDS_DIM_AFTER := 1.5
const CARDS_BACK_AFTER := 1.2
const CARDS_FADE := 0.35
# What counts as practising. Polled rather than bound: every button is already taken, and on a pad
# ui_accept is JOY_BUTTON_A, which is punch.
const ACTION_INPUTS: Array[StringName] = [&"punch", &"dodge", &"block", &"mash_left", &"mash_right"]

# A finisher takes the cards out at once, whatever the idle clock says: its zoom throws the dummy to
# screen y 127, measured, where a card covers it whole. This fade has to finish inside the settle
# beat before the fight freezes, which stops this node: 0.18 s against the finisher's 0.2 s.
# SCREEN_DIM at 1.0 turns that half off, CARDS_DIM at 1.0 the other.
const SCREEN_DIM := 0.0
const SCREEN_FADE := 0.18

const CALLOUT_HOLD := 1.4
const CALLOUT_FADE := 0.35
const BARK_HOLD := 2.6
const BARK_FADE := 0.4

# The explanatory half only: CombatPopupUI already pops PARRY!, PERFECT! and GUARD BREAK! over the
# player's head, so these say what to do about it rather than repeating the word.
const CALLOUTS := {
	parried = "it's staggered - punch it",
	blocked = "that cost stamina",
	hit = "too slow - press block as it lands",
	early = "too early",
	guard_broken = "wait it out",
	dodged = "the dash went straight through it",
	sparring = "SPARRING - parry the red, dash the yellow",
	bag = "BAG - it just stands there now",
}

# What the post says about itself, by state. It is the only way into the half of the room that
# teaches the red and yellow reads, so it has to read as a switch rather than as scenery.
const POST_SIGN := {
	off = ["SPAR MODE: OFF", "WALK INTO ME"],
	on = ["SPAR MODE: ON", "WALK INTO ME"],
}
const POST_SIGN_FONT := 30
# Read as text against the lockers, not matched to the lamp: the lamp carries the colour code, the
# sign carries the words, and the words have to be legible in both states.
const POST_SIGN_OFF_COLOUR := Color("cbdbfc")
const POST_SIGN_ON_COLOUR := Color("d95763")
# Landed punches on a bag that has never been switched on before Danny points at the post. Once,
# never again: the sign and his hand-over line are the standing invitations, this is one nudge for a
# player who has settled into punching and not looked up.
const NUDGE_AFTER_PUNCHES := 6

# One each, the first time the player does the thing. Deliberately not dialogue lines: a balloon
# would cover the floor and set player.is_talking, which freezes the player mid-practice.
const BARKS := {
	punch = "There you go. Three of those in rhythm and the third one HURTS.",
	daze = "It's gone dizzy! MASH the two on the prompt, dum dum!",
	parry = "THAT'S a parry. It's wide open. Hit it.",
	dodge = "Dashed clean through it. Do that to the yellow ones.",
	guard_broken = "Bar's empty, guard's gone. Stop blocking and MOVE.",
	spar = "Bored? Walk into that post and it'll hit BACK. Red you parry, yellow you dash through.",
}

@export var player: CharacterBody2D
# Only the card wall fades. Everything the player still has to be able to read and press - the Ready
# button above all - lives in a sibling group that nothing here touches.
@export var cards: Control
@export var dummy: CharacterBody2D
@export var danny: Sprite2D
@export var walls: StaticBody2D
@export var mode_post: Area2D
@export var post_art: Node2D
@export var door_exit: Area2D
@export var callout: Label
@export var danny_bark: Label
@export var door_prompt: Label
@export var ready_button: Button

var room_open := false
var leaving := false
# Seconds since the last action input, and seconds of practice since the last real break in it.
var idle_for := 0.0
var active_for := 0.0
var door_dwell := 0.0
var post_armed := true
var post_cooldown := 0.0
var barked := {}

var punches_landed := 0
var ever_sparred := false

var finisher: Node
var refill_timer: Timer
var post_lamp: Polygon2D
var post_sprite: Sprite2D
var post_state_label: Label
var post_hint_label: Label
var callout_tween: Tween
var bark_tween: Tween


func _ready() -> void:
	# Ahead of PlayerScript's own _process, whose death check reads the health this floors, and of
	# the dummy's physics step, which is what can take it down there.
	process_priority = -10
	process_physics_priority = -10

	# The room's only exit is Eric's fight, so it teaches Eric's feel: the V2 dash, the V2 punch
	# reach and the finisher's own mash pair. Exactly what BossOneScript does as that fight starts.
	player.feel_v2 = true
	dummy.player = player
	dummy.set_sparring(false)

	_build_walls()
	_build_post()
	callout.modulate.a = 0.0
	danny_bark.modulate.a = 0.0
	door_prompt.visible = false

	refill_timer = Timer.new()
	refill_timer.name = "RefillTimer"
	refill_timer.one_shot = true
	refill_timer.timeout.connect(_refill_health)
	add_child(refill_timer)

	var defense: Node = player.get_node("Defense")
	defense.parried.connect(_on_parried)
	defense.blocked.connect(_on_blocked)
	defense.perfect_dodged.connect(_on_perfect_dodged)
	defense.hit_taken.connect(_on_hit_taken)
	defense.guard_broken.connect(_on_guard_broken)
	defense.block_pressed.connect(_on_block_pressed)
	player.get_node("Combo").punch_landed.connect(_on_punch_landed)
	finisher = player.get_node("Finisher")
	finisher.prompt_shown.connect(_bark.bind("daze"))

	mode_post.body_entered.connect(_on_post_entered)
	mode_post.body_exited.connect(_on_post_exited)

	DialogueManager.dialogue_ended.connect(_on_dialogue_ended)
	InputSettings.device_changed.connect(_sync_exit.unbind(1))


func _process(delta: float) -> void:
	_floor_health()
	_step_cards(delta)


# The card wall's alpha, and the only thing that reads it. Held at full while Danny is still talking
# about them: on a pad his balloon is advanced with A, which is also punch, and that must not be
# read as practice.
func _step_cards(delta: float) -> void:
	if not room_open:
		return
	idle_for = 0.0 if _acting() else idle_for + delta
	# Short pauses inside a bout of practice don't count as stopping, so the cards stay down.
	active_for = 0.0 if idle_for >= CARDS_BACK_AFTER else active_for + delta
	var finishing: bool = finisher.phase != 0
	var target: float = SCREEN_DIM if finishing else (CARDS_DIM if active_for >= CARDS_DIM_AFTER else 1.0)
	var fade: float = SCREEN_FADE if finishing else CARDS_FADE
	cards.modulate.a = move_toward(cards.modulate.a, target, delta / fade)


func _acting() -> bool:
	if InputSettings.move_vector() != Vector2.ZERO:
		return true
	return ACTION_INPUTS.any(func(action: StringName) -> bool: return Input.is_action_pressed(action))


func _physics_process(delta: float) -> void:
	_floor_health()
	post_cooldown = maxf(post_cooldown - delta, 0.0)
	_step_door(delta)


# The one rule the room cannot break.
func _floor_health() -> void:
	player.playerHealth = maxi(player.playerHealth, 1)


func _refill_health() -> void:
	player.playerHealth = FULL_HEALTH
	player.healthUI.update_health(FULL_HEALTH)


func _on_dialogue_ended(_resource: Object) -> void:
	room_open = true
	# Deferred: ControlsSceneScript hands the button its focus on this same signal, and its _ready
	# runs after this node's, so its handler runs second.
	_sync_exit.call_deferred()


# ui_accept carries JOY_BUTTON_A, which is also punch (InputSettings). A focused Ready button would
# launch Eric's fight on every pad punch thrown at the dummy, so on a pad the button takes no focus
# and Y confirms instead - drawn on the button, so nobody has to be told. On a keyboard ui_accept is
# Enter and Space, which nothing in the room uses, so the approved screen keeps its focus and its
# bare button exactly as they were.
func _sync_exit() -> void:
	var pad := InputSettings.device == InputSettings.Device.GAMEPAD
	ready_button.icon = ControlsArtLayout.pad_glyph_frame(InputSettings.PAD_BUTTON_FRAMES[CONFIRM_PAD_BUTTON]) if pad else null
	ready_button.add_theme_constant_override("icon_max_width", CONFIRM_GLYPH_WIDTH)
	if pad:
		ready_button.focus_mode = Control.FOCUS_NONE
		ready_button.release_focus()
	elif not ready_button.disabled:
		ready_button.focus_mode = Control.FOCUS_ALL
		if room_open and not ready_button.has_focus():
			ready_button.grab_focus()


# Below the GUI, so the device tracker in the InputSettings autoload has already seen the press and
# the prompts stay on the right device. Nothing else in the game reads Y, so it is left unhandled.
func _unhandled_input(event: InputEvent) -> void:
	if leaving or not room_open or not event.is_pressed():
		return
	if event is InputEventJoypadButton and event.button_index == CONFIRM_PAD_BUTTON:
		leaving = true
		get_tree().change_scene_to_file(ERIC_FIGHT)


#THE MODE POST

func _on_post_entered(body: Node2D) -> void:
	if body != player or not post_armed or post_cooldown > 0.0:
		return
	post_armed = false
	post_cooldown = MODE_COOLDOWN
	var sparring: bool = not dummy.is_sparring()
	ever_sparred = ever_sparred or sparring
	dummy.set_sparring(sparring)
	_paint_post(sparring)
	_say(CALLOUTS.sparring if sparring else CALLOUTS.bag)


func _on_post_exited(body: Node2D) -> void:
	if body == player:
		post_armed = true


#THE DOOR

func _step_door(delta: float) -> void:
	if leaving or not room_open:
		return
	if not door_exit.overlaps_body(player):
		door_dwell = 0.0
		door_prompt.visible = false
		return
	door_dwell += delta
	door_prompt.visible = true
	if door_dwell < DOOR_DWELL:
		return
	leaving = true
	door_prompt.visible = false
	get_tree().change_scene_to_file(ERIC_FIGHT)


#WHAT THE ROOM SAYS

func _on_parried(_hit: RefCounted, _point: Vector2, _staggered: bool, _streak: int) -> void:
	_say(CALLOUTS.parried)
	_bark("parry")


func _on_blocked(_hit: RefCounted, _point: Vector2) -> void:
	_say(CALLOUTS.blocked)


func _on_perfect_dodged(_hit: RefCounted) -> void:
	_say(CALLOUTS.dodged)
	_bark("dodge")


func _on_hit_taken(_hit: RefCounted) -> void:
	_say(CALLOUTS.hit)
	refill_timer.start(REFILL_TIME)


func _on_guard_broken() -> void:
	_say(CALLOUTS.guard_broken)
	_bark("guard_broken")


# A press that got no parry credit came too soon after one that whiffed. Only worth saying while
# something is actually coming at them; in BAG mode there is nothing it could have been early for.
func _on_block_pressed(credited: bool) -> void:
	if not credited and dummy.is_sparring():
		_say(CALLOUTS.early)


func _on_punch_landed(_target: Node, _dealt: int, _charged: bool) -> void:
	_bark("punch")
	punches_landed += 1
	if punches_landed >= NUDGE_AFTER_PUNCHES and not ever_sparred:
		_bark("spar")


func _say(text: String) -> void:
	callout.text = text
	callout.modulate.a = 1.0
	if callout_tween:
		callout_tween.kill()
	callout_tween = callout.create_tween()
	callout_tween.tween_interval(CALLOUT_HOLD)
	callout_tween.tween_property(callout, "modulate:a", 0.0, CALLOUT_FADE)


func _bark(key: String) -> void:
	if barked.has(key) or not room_open:
		return
	barked[key] = true
	danny_bark.text = BARKS[key]
	danny_bark.modulate.a = 1.0
	var animation: AnimationPlayer = danny.get_node("AnimationPlayer")
	animation.play("talk")
	if bark_tween:
		bark_tween.kill()
	bark_tween = danny_bark.create_tween()
	bark_tween.tween_interval(BARK_HOLD)
	bark_tween.tween_property(danny_bark, "modulate:a", 0.0, BARK_FADE)
	bark_tween.tween_callback(animation.play.bind("RESET"))


#THE ROOM ITSELF

func _build_walls() -> void:
	var t := WALL_THICKNESS
	var sides := [
		Rect2(PLAY_BAND.position.x - t, PLAY_BAND.position.y - t, PLAY_BAND.size.x + t * 2.0, t),
		Rect2(PLAY_BAND.position.x - t, PLAY_BAND.end.y, PLAY_BAND.size.x + t * 2.0, t),
		Rect2(PLAY_BAND.position.x - t, PLAY_BAND.position.y, t, PLAY_BAND.size.y),
		Rect2(PLAY_BAND.end.x, PLAY_BAND.position.y, t, PLAY_BAND.size.y),
	]
	for side in sides:
		var shape := CollisionShape2D.new()
		var box := RectangleShape2D.new()
		box.size = side.size
		shape.shape = box
		shape.position = side.get_center()
		walls.add_child(shape)


func _build_post() -> void:
	if TrainingDummyArtLayout.USE_FINAL_SWITCH:
		post_sprite = Sprite2D.new()
		post_sprite.texture = load(TrainingDummyArtLayout.SWITCH_SHEET)
		post_sprite.hframes = 2
		post_sprite.centered = false
		post_sprite.scale = Vector2.ONE * TrainingDummyArtLayout.SWITCH_SCALE
		post_sprite.offset = Vector2(-TrainingDummyArtLayout.SWITCH_FRAME_SIZE.x / 2.0, -TrainingDummyArtLayout.SWITCH_FRAME_SIZE.y)
		post_art.add_child(post_sprite)
	else:
		var spec: Dictionary = TrainingDummyArtLayout.PLACEHOLDER_SWITCH
		_add_post_piece(spec.column, spec.column_colour)
		_add_post_piece(spec.plate, spec.plate_colour)
		post_lamp = _add_post_piece(spec.lamp, spec.bag_colour)
	# The placard. It is the standing answer to "how do I practise parrying": the post has to say
	# what it is and what to do with it without anyone having to be told first.
	post_state_label = _add_post_label(-56.0)
	post_hint_label = _add_post_label(-18.0)
	post_hint_label.text = POST_SIGN.off[1]
	_paint_post(false)


# A centred line bolted to the post, `top` texels-times-scale above its floor point.
func _add_post_label(top: float) -> Label:
	var line := Label.new()
	line.theme = load(UI_THEME)
	line.add_theme_font_size_override("font_size", POST_SIGN_FONT)
	line.add_theme_color_override("font_color", POST_SIGN_OFF_COLOUR)
	line.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	line.add_theme_constant_override("outline_size", 6)
	line.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.position = Vector2(-145.0, top)
	line.size = Vector2(290.0, 38.0)
	post_art.add_child(line)
	return line


func _add_post_piece(box: Rect2, colour: Color) -> Polygon2D:
	var piece := Polygon2D.new()
	piece.polygon = TrainingDummyArtLayout.rect_polygon(Rect2(box.position * TrainingDummyArtLayout.SWITCH_SCALE, box.size * TrainingDummyArtLayout.SWITCH_SCALE))
	piece.color = colour
	post_art.add_child(piece)
	return piece


func _paint_post(sparring: bool) -> void:
	var spec: Dictionary = TrainingDummyArtLayout.PLACEHOLDER_SWITCH
	var lit: Color = spec.spar_colour if sparring else spec.bag_colour
	post_state_label.text = POST_SIGN.on[0] if sparring else POST_SIGN.off[0]
	post_state_label.add_theme_color_override("font_color", POST_SIGN_ON_COLOUR if sparring else POST_SIGN_OFF_COLOUR)
	if post_sprite:
		post_sprite.frame = 1 if sparring else 0
		return
	post_lamp.color = lit
