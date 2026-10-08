extends State

# The takeover (plan section 6): Computah is down, and Greyson storms the ring, tears Computah's cannon arm off,
# straps it on and takes the fight over. GreysonTakeover.dialogue carries the user's lines and calls the beats
# between them, waiting on each; its natural end hands over to the fight (finish_cut, then begin_fight).
#
# The KO first: the finisher that beat Computah plays out, and a juggle kill's crash, then a beat with the crowd
# cheering and the player free. Then the cut: a BossEntrance for the hold on the player and the skip hint, with
# the laugh cut's skip (BurakBossLaugh) - every wait is a node-bound tween in `waits`, so a pause holds the cut
# where it is, and a held skip closes the balloon and runs the waits out. It never has a finish_entrance(): the
# defence suite finds a fight's entrance by that method.
#
# THE BEATS, on the shipped takeover sheets (art_source/greyson_fight/gf_ship.py's timings): he shouts off the
# screen ("COMPUTAH NOOO", the shout sound in place of his blips), walks in in tears through the top gate as the
# player walks onto their mark under HOME (PLAYER_MARK), clear of the tear and the hurl to come, says the
# upset line in three beats (grief, fond, fury, a sentence at a time as it types), walks to Computah's cannon side
# and tears the arm off one-handed - his node on Computah's floor point plus TEAR_SPOT, where his fist lands on the
# arm's grip, drawn over Computah and over the torn arm (ComputahArtLayout.ARM_PROP) - jams it on, grabs the
# armless Computah and hurls him over his head, over the far rope and off the screen (the user, 2026-09-24: "so hes
# no longer in the way"), walks back HOME smug, roars, and pulls out the barbell as his bar sweeps to full and his
# theme starts.
#
# EVERY WAY OUT LANDS ON ONE END STATE (_settle), and finish_cut() is the only way out: the lines' end, the hold,
# the test scene's start_active, and the fight ending over the top of it (GreysonStateMachine._end_fight). Computah
# gone from the ring (hidden, out of the fight); Greyson at HOME wearing the cannon, facing the player, targetable, on his own z;
# Computah's HUD gone and his full, gauge and meter empty; the gates shut; the player free on their mark (but not when
# the fight ended over the top of it: there they stay where they stood); his
# theme started once; the view level, the crowd at rest, no balloon, and nothing of the takeover's own left (the
# torn arm, the thrown Computah, the roar's FX). A retry plays it all again.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const ComputahLayout := preload("res://Scripts/ComputahArtLayout.gd")
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
# The name his lines go under.
const SPEAKER := "Greyson"

#THE KO
const KO_BEAT := 0.8

#THE PLAYER'S MARK (px, px/s and seconds; the brawl's walk onto its own mark, GreysonFinalBrawl._walk_player)
# Under HOME, on the arena's own spawn, so the fight opens as his test scene does: him facing them, and his first
# plate with a real first leg to fly to them. Left where they finished Computah, beside his hand, it touched them as
# it left it (the playtest, 2026-10-04; the user's default (f): "the cutscene walks you to a spot below him").
const PLAYER_MARK := Vector2(959, 900)
const PLAYER_WALK_SPEED := 650.0
const PLAYER_WALK_MIN := 0.3
const PLAYER_WALK_MAX := 1.2
# Nearer than this to the mark, they are put on it.
const PLAYER_SNAP := 5.0

#THE WALK IN (seconds and px)
# He comes in from above the top gate, off the screen, straight down to HOME.
const ENTER_FROM := Vector2(960, -160)
const ENTER_TIME := 2.2
const WALK_SPEED := 360.0
# The walk sheets' contacts, each a thump in the view and a stomp.
const STEP_FRAMES := [0, 3]
const STEP_SHAKE := 2.0
const STEP_SHAKE_STEPS := 2
const STEP_SHAKE_STEP_TIME := 0.03

#HIS LINES
# The upset line's three beats, one a sentence as it types: grief at the loss, fond through the memory, fury at the
# end ("Now you've really messed up.").
const UPSET_GESTURES := [&"talk_grief", &"talk_fond", &"talk_fond", &"talk_fury"]
# The smug ones, by their lines' `greyson` tags.
const SMUG_GESTURES := {"show": &"talk_cannon_show", "stance": &"talk_cannon_stance"}

#THE TEAR (the coordinator's placement: his node here from Computah's floor point, on the same floor line)
const TEAR_SPOT := Vector2(156.3, -1.2)
# Closer than this to the right rope, he stands on Computah's left instead, the two of them drawn flipped.
const TEAR_ROOM := 60.0
const GRIP_TIME := 0.25
const STRAIN_TIME := 0.60
const STRAIN_SHAKE := 3.0
const STRAIN_SHAKE_STEPS := 10
const RIP_TIME := 0.15
const RIP_SHAKE := 12.0
const RIP_SHAKE_STEPS := 6
const RIP_SHAKE_STEP_TIME := 0.03
const RIP_HIT_STOP := 0.06
const HOLD_TIME := 0.40
# Bottom to top at the tear: Computah, the torn arm, him.
const PROP_Z := 1
const GREYSON_Z := 2

#THE ATTACH (the attach sheet's own timings: the prop on his fist, the CLANK, the flex)
const FIT_TIME := 0.30
const CLANK_TIME := 0.25
const FLEX_TIME := 0.45
const CLANK_SHAKE := 8.0
const CLANK_SHAKE_STEPS := 5
const CLANK_SHAKE_STEP_TIME := 0.03
# One green pulse over him as it locks on: a single flicker, well under 3 a second.
const CLANK_TINT := Color(0.6, 1.45, 0.6)
const CLANK_TINT_TIME := 0.25

#THE ROAR (the inhale, the roar alternated under a shake decaying over its 1.2 s, and the settle)
const INHALE_TIME := 0.40
const ROAR_TIME := 1.20
const SETTLE_TIME := 0.20
const ROAR_SHAKE := 16.0
const ROAR_SHAKE_STEPS := 12
const ROAR_SHAKE_STEP_TIME := 0.1

#THE HURL (after the attach, about 1.55 s: a step to Computah, the grab, the heave overhead, the release, and the
# flight off the screen while he recovers, then the crash out there. His four beats are the hurl rows' own times.)
# The flight, from the release: it ends as Computah leaves the screen, where the crash plays.
const HURL_FLIGHT_TIME := 0.55
const HURL_CRASH_TIME := 0.10
# How high the arc rises over the straight line at its middle, and how much lower it ends.
const HURL_ARC := 150.0
const HURL_DROP := 60.0
const HURL_CRASH_SHAKE := 6.0
const HURL_CRASH_SHAKE_STEPS := 4
const HURL_CRASH_SHAKE_STEP_TIME := 0.03
const HURL_CHEER := 1.5
# Behind him while he holds and lets go of him, then over the ropes and the ringside crowd as he flies out.
const HURL_BEHIND_Z := 1
const HURL_Z := 10

#THE BAR SWAP
const PULL_TIME := 0.5
const COMPUTAH_HUD_FADE := 0.4

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# The hold on the player and the skip hint, up from the cut to the end.
var cut: CanvasLayer
# Enter() has run, so there is a takeover to end.
var entered := false
# The takeover is over, one way or another. finish_cut() is the only thing that sets it.
var finished := false
# Waiting for the KO to play out before the cut starts.
var waiting_ko := false
var waits: Array[Tween] = []
# A beat owns his frames until the next line comes up.
var beat_running := false
var last_line: RefCounted
var last_walk_frame := -1
# +1 when he stands on Computah's right at the tear, -1 on his left.
var side := 1.0
# The torn arm, from the RIP to the CLANK, and the takeover's own FX.
var prop: Sprite2D
var fx: Array[Node] = []
var roar_fx: Sprite2D
# Computah in the air, from the heave to the crash: the real one is hidden from the heave on.
var hurled: Sprite2D
# Beats seen through to their end, for a test: name -> game seconds it took.
var beat_times := {}
# For a test: the hurl's beat as it plays (&"step", &"grab", &"heave", &"flight", &"crash", then &"done"), which way
# he was thrown (-1 left, +1 right), the flight's arc (the middle of Computah's body from, to), and the game seconds
# the whole of it took.
var hurl_beat := &""
var hurl_toward := 0.0
var hurl_arc: Array[Vector2] = []
var hurl_time := -1.0


func Enter() -> void:
	# Deferred, so the fight may already have been ended over the top of this state (Exit).
	if finished:
		return
	entered = true
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	if body.start_active:
		finish_cut.call_deferred()
		return
	# Off the screen and out of the fight until he walks in.
	body.set_target_active(false)
	body.sprite.visible = false
	body.global_position = ENTER_FROM
	waiting_ko = true


func Exit() -> void:
	finish_cut(false)


func Update(_delta: float) -> void:
	if finished:
		return
	_read_lines()
	_walk_steps()


func Physics_Update(_delta: float) -> void:
	if waiting_ko and _ko_over():
		waiting_ko = false
		_after_ko()


#THE KO

# The finisher that beat Computah has played out, and a juggle kill has crashed.
func _ko_over() -> bool:
	var player := _player()
	if player != null and player.finisher.is_active():
		return false
	var computah = body.computah
	return not (is_instance_valid(computah) and computah.is_juggled())


func _after_ko() -> void:
	await _beat(KO_BEAT)
	if finished:
		return
	cut = BossEntrance.new()
	cut.name = "TakeoverCut"
	add_child(cut)
	cut.skipped.connect(skip_cut)
	cut.begin(_player())
	state_machine.crowd(&"hush")
	var computah = body.computah
	if is_instance_valid(computah):
		computah.rest_on_defeat()
	state_machine.show_takeover_dialogue(self)


#THE BEATS THE DIALOGUE CALLS

# In tears through the top gate to HOME, and the gates slam behind him.
func greyson_enters() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	var gates = state_machine.gates()
	if gates != null:
		gates.open()
	body.show_body()
	body.set_facing(false)
	body.global_position = ENTER_FROM
	body.play_anim(&"walk")
	var walk := create_tween()
	walk.tween_method(_step_walk.bind(ENTER_FROM, state_machine.HOME), 0.0, 1.0, ENTER_TIME)
	_walk_player()
	await _wait(walk)
	if not _cut_is_live():
		return
	body.global_position = state_machine.HOME
	body.set_target_active(true)
	body.play_anim(&"talk_grief_shut")
	if gates != null:
		await gates.close()
	if not _cut_is_live():
		return
	beat_running = false
	beat_times[&"greyson_enters"] = body.fight_clock - started


# Over to Computah's cannon side; the one-handed tear; the arm jammed on; back HOME, smug.
func take_the_cannon() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	var computah = body.computah
	var has_computah := is_instance_valid(computah)
	var anchor: Vector2 = computah.global_position if has_computah else state_machine.HOME
	side = _tear_side(anchor)
	await _walk_to((anchor + Vector2(TEAR_SPOT.x * side, TEAR_SPOT.y)).round(), &"walk")
	if not _cut_is_live():
		return
	# Face to face, as the tear is drawn: Computah on his left, or both flipped.
	body.set_facing(side > 0.0)
	if has_computah:
		computah.set_facing(side < 0.0)
	body.sprite.z_index = GREYSON_Z
	body.play_anim(&"tear_grip")
	if has_computah:
		computah.haul_arm()
	await _beat(GRIP_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"tear_strain")
	ScreenView.shake(get_tree(), STRAIN_SHAKE, STRAIN_SHAKE_STEPS, STRAIN_TIME / STRAIN_SHAKE_STEPS)
	await _beat(STRAIN_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"tear_rip")
	body.play_sfx(&"cannon_rip")
	body.play_sfx(&"spark")
	ScreenView.shake(get_tree(), RIP_SHAKE, RIP_SHAKE_STEPS, RIP_SHAKE_STEP_TIME)
	HitStop.freeze(get_tree(), RIP_HIT_STOP)
	if has_computah:
		computah.lose_arm()
		var handoff: Vector2 = ComputahLayout.ARM_PROP.handoff
		_show_prop(&"torn", anchor + Vector2(handoff.x * side, handoff.y))
	await _beat(RIP_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"tear_hold")
	_prop_on_fist(&"lift")
	await _beat(HOLD_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"attach")
	_prop_on_fist(&"fit")
	await _beat(FIT_TIME)
	if not _cut_is_live():
		return
	# CLANK: the arm is his from here, drawn on him.
	_free_prop()
	body.play_sfx(&"cannon_clamp")
	ScreenView.shake(get_tree(), CLANK_SHAKE, CLANK_SHAKE_STEPS, CLANK_SHAKE_STEP_TIME)
	body.sprite.modulate = CLANK_TINT
	body.sprite.create_tween().tween_property(body.sprite, "modulate", Color.WHITE, CLANK_TINT_TIME)
	body.put_on_cannon()
	await _beat(CLANK_TIME + FLEX_TIME)
	if not _cut_is_live():
		return
	if has_computah and is_instance_valid(computah):
		await _hurl(computah)
		if not _cut_is_live():
			return
	body.sprite.z_index = 0
	await _walk_to(state_machine.HOME, &"walk_cannon")
	if not _cut_is_live():
		return
	_face_player()
	body.play_anim(&"talk_cannon_show_shut")
	beat_running = false
	beat_times[&"take_the_cannon"] = body.fight_clock - started


# The roar that shakes the arena: the inhale, the roar under its FX and the screen's, and the settle.
func roar() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	body.play_anim(&"roar_inhale")
	await _beat(INHALE_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"roar")
	body.play_sfx(&"roar")
	state_machine.crowd(&"roar", ROAR_TIME)
	ScreenView.shake(get_tree(), ROAR_SHAKE, ROAR_SHAKE_STEPS, ROAR_SHAKE_STEP_TIME)
	_start_roar_fx()
	fx.append(body.play_fx(&"roar_screen", Vector2.ZERO, body.fx_layer, false, Callable(), false))
	await _beat(ROAR_TIME)
	if not _cut_is_live():
		return
	_stop_roar_fx()
	body.play_anim(&"roar_settle")
	await _beat(SETTLE_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"talk_cannon_stance_shut")
	beat_running = false
	beat_times[&"roar"] = body.fight_clock - started


# The barbell comes out, Computah's bar goes and his sweeps to full, and his theme starts.
func swap_the_bar() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	body.play_anim(&"barbell_pull", &"idle")
	var computah = body.computah
	if is_instance_valid(computah):
		computah.retire_hud(COMPUTAH_HUD_FADE)
	await _beat(PULL_TIME)
	if not _cut_is_live():
		return
	body.show_hud(Layout.HUD_SWEEP_TIME)
	body.start_music()
	await _beat(Layout.HUD_SWEEP_TIME)
	if not _cut_is_live():
		return
	if body.current_anim != &"idle":
		body.play_anim(&"idle")
	beat_running = false
	beat_times[&"swap_the_bar"] = body.fight_clock - started


#HIS LINES

func _read_lines() -> void:
	# Untyped: the balloon frees itself when the lines end, and a freed object can't be held in a typed variable
	# long enough to ask is_instance_valid about it.
	var balloon = state_machine.takeover_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line == null:
		return
	if line != last_line:
		last_line = line
		if line.has_tag("shout"):
			body.play_sfx(&"shout")
	if beat_running or not body.sprite.visible or line.character != SPEAKER or not line.has_tag("greyson"):
		return
	var label = balloon.dialogue_label
	var typing: bool = label.is_typing
	var gesture := _gesture(line, label)
	var want := gesture if typing else StringName(String(gesture) + "_shut")
	if body.current_anim != want:
		body.play_anim(want)
	# On the stand-in sheet his mouth doesn't move, so his whole body squashes while he talks instead.
	body.set_talking(typing and not Layout.uses_final(want))


# The talk pair for the line, and for the upset line the sentence it has typed up to.
func _gesture(line: RefCounted, label: Node) -> StringName:
	var mood: String = line.get_tag_value("greyson")
	if SMUG_GESTURES.has(mood):
		return SMUG_GESTURES[mood]
	var text: String = label.get_parsed_text()
	# -1 is the whole line showing.
	var shown: int = label.visible_characters if label.visible_characters >= 0 else text.length()
	return UPSET_GESTURES[mini(text.substr(0, shown).count(". "), UPSET_GESTURES.size() - 1)]


# A thump and a stomp on each contact of either walk.
func _walk_steps() -> void:
	if not beat_running or not (body.current_anim in [&"walk", &"walk_cannon"]):
		last_walk_frame = -1
		return
	var frame: int = body.sprite.frame
	if frame == last_walk_frame:
		return
	last_walk_frame = frame
	if frame in STEP_FRAMES:
		ScreenView.shake(get_tree(), STEP_SHAKE, STEP_SHAKE_STEPS, STEP_SHAKE_STEP_TIME)
		body.play_sfx(&"stomp")


#THE TORN ARM AND THE ROAR'S FX

# The side of Computah he tears from: his right, unless the ropes are too close.
func _tear_side(anchor: Vector2) -> float:
	return 1.0 if anchor.x + TEAR_SPOT.x <= state_machine.ROPES.end.x - TEAR_ROOM else -1.0


# The arm on `frame_name`'s frame, centred on `at`, mirrored with the tear.
func _show_prop(frame_name: StringName, at: Vector2) -> void:
	var spec: Dictionary = ComputahLayout.ARM_PROP
	if prop == null:
		prop = Sprite2D.new()
		prop.texture = load(spec.texture)
		prop.hframes = spec.hframes
		prop.scale = Vector2.ONE * Layout.SCALE
		prop.z_index = PROP_Z
		body.get_parent().add_child(prop)
	prop.flip_h = side < 0.0
	prop.frame = spec.frames[frame_name]
	prop.global_position = at.round()


# The arm on `frame_name`'s frame with its grip on his fist.
func _prop_on_fist(frame_name: StringName) -> void:
	if prop == null:
		return
	var spec: Dictionary = ComputahLayout.ARM_PROP
	var grip: Vector2 = (spec.grip - spec.frame_size / 2.0) * Layout.SCALE
	if side < 0.0:
		grip.x = -grip.x
	_show_prop(frame_name, body.hand_point() - grip)


func _free_prop() -> void:
	if is_instance_valid(prop):
		prop.queue_free()
	prop = null


#THE HURL

# A step to Computah, and he grabs him by the collar, heaves him overhead and throws him over his head - away from
# where he lay, over the rope on that side: the hurl sheet is drawn grabbing him on the left and throwing him right,
# and flips for the other side - tumbling off the screen while he recovers, and the crash comes back from out past the
# crowd as he leaves it. From the heave on the real Computah is hidden and `hurled` is thrown in his place; every way
# out of here leaves him hidden (_settle).
func _hurl(computah: Node) -> void:
	var started: float = body.fight_clock
	var final := Layout.uses_final_hurl()
	hurl_toward = side
	if final:
		hurl_beat = &"step"
		await _walk_to(_grab_spot(computah), &"walk_cannon")
		if not _cut_is_live():
			return
		body.set_facing(side > 0.0)
	hurl_beat = &"grab"
	body.play_anim(Layout.hurl_anim(&"hurl_grab"))
	body.play_sfx(&"hurl_grab")
	await _beat(_hurl_time(&"hurl_grab"))
	if not _cut_is_live():
		return
	hurl_beat = &"heave"
	body.play_anim(Layout.hurl_anim(&"hurl_heave"))
	_lift(computah, final)
	await _beat(_hurl_time(&"hurl_heave"))
	if not _cut_is_live():
		return
	hurl_beat = &"flight"
	body.play_anim(Layout.hurl_anim(&"hurl_release"))
	body.play_sfx(&"hurl_whoosh")
	var flight := _launch(final)
	await _beat(_hurl_time(&"hurl_release"))
	if not _cut_is_live():
		return
	hurled.z_index = HURL_Z
	body.play_anim(Layout.hurl_anim(&"hurl_recover"))
	if flight.is_valid():
		await flight.finished
	waits.erase(flight)
	if not _cut_is_live():
		return
	hurl_beat = &"crash"
	_free_hurled()
	body.play_sfx(&"hurl_crash")
	state_machine.crowd(&"cheer", HURL_CHEER)
	ScreenView.shake(get_tree(), HURL_CRASH_SHAKE, HURL_CRASH_SHAKE_STEPS, HURL_CRASH_SHAKE_STEP_TIME)
	await _beat(HURL_CRASH_TIME)
	if not _cut_is_live():
		return
	hurl_beat = &"done"
	hurl_time = body.fight_clock - started


# The hurl row's own time, which its stand-in holds for too.
func _hurl_time(anim_name: StringName) -> float:
	return Layout.loop_length(Layout.FINAL_ANIMS[anim_name])


# Where he stands for the grab: his fist on the grab frame over Computah's collar, his feet on the line they are on.
func _grab_spot(computah: Node) -> Vector2:
	var fist: Vector2 = Layout.texel_local(Layout.HANDS[&"hurl"][0], &"hurl_grab", Layout.mirrored(&"hurl_grab", body.facing_left))
	var collar: Vector2 = computah.frame_point(ComputahLayout.C_ARMLESS_COLLAR)
	return Vector2(collar.x - fist.x, body.global_position.y).round()


# Computah up off the mat and in his fist, behind him, and the real one hidden: the tumble's held cell, or the
# stand-in, his own frame as he lay.
func _lift(computah: Node, final: bool) -> void:
	var look: Sprite2D = computah.sprite
	hurled = Sprite2D.new()
	if final:
		var tumble: Dictionary = ComputahLayout.ARMLESS_TUMBLE
		hurled.texture = load(tumble.texture)
		hurled.hframes = tumble.hframes
		hurled.frame = tumble.held
		hurled.flip_h = hurl_toward < 0.0
	else:
		hurled.texture = look.texture
		hurled.hframes = look.hframes
		hurled.vframes = look.vframes
		hurled.frame = look.frame
		hurled.flip_h = look.flip_h
	hurled.scale = Vector2.ONE * ComputahLayout.SCALE
	hurled.z_index = HURL_BEHIND_Z
	body.get_parent().add_child(hurled)
	_hold_in_fist(final)
	computah.visible = false


# The held cell's grip on the fist of the frame he is on, or the stand-in's middle.
func _hold_in_fist(final: bool) -> void:
	var grip: Vector2 = _cell_local(ComputahLayout.ARMLESS_TUMBLE.grip) if final else Vector2.ZERO
	hurled.global_position = (body.hand_point() - grip).round()


# The flight, from his fist on the release: the held cell there on its first tick, then over his head along an arc
# past the screen's edge on the throw's side, ending as Computah leaves the screen. It is a wait, so a hold runs it
# out.
func _launch(final: bool) -> Tween:
	_hold_in_fist(final)
	var tumble: Dictionary = ComputahLayout.ARMLESS_TUMBLE
	var middle: Vector2 = hurled.global_position + (_cell_local(tumble.middles[tumble.held]) if final else Vector2.ZERO)
	var half: float = tumble.frame_size.x / 2.0 * ComputahLayout.SCALE
	var edge: float = -half if hurl_toward < 0.0 else get_viewport().get_visible_rect().size.x + half
	hurl_arc = [middle, Vector2(edge, middle.y + HURL_DROP)]
	var flight := create_tween()
	flight.tween_method(_fly.bind(final), 0.0, 1.0, HURL_FLIGHT_TIME)
	waits.append(flight)
	return flight


# One step of the flight: the body's middle on the arc - each tumble cell's own middle (ARMLESS_TUMBLE.middles), so
# the spin stays steady - or the stand-in turned a quarter a step.
func _fly(weight: float, final: bool) -> void:
	if not is_instance_valid(hurled):
		return
	var middle: Vector2 = hurl_arc[0].lerp(hurl_arc[1], weight) + Vector2(0.0, -4.0 * HURL_ARC * weight * (1.0 - weight))
	var flown := weight * HURL_FLIGHT_TIME
	if final:
		var tumble: Dictionary = ComputahLayout.ARMLESS_TUMBLE
		var cell: int = tumble.held if weight <= 0.0 else tumble.spin[int(flown / tumble.spin_time) % tumble.spin.size()]
		hurled.frame = cell
		hurled.global_position = (middle - _cell_local(tumble.middles[cell])).round()
	else:
		var spin: Dictionary = Layout.PLACEHOLDER_HURL_TUMBLE
		hurled.global_position = middle.round()
		hurled.rotation = deg_to_rad(spin.turn * int(flown / spin.step) * hurl_toward)


# A texel on a tumble cell from the cell's middle, in px, mirrored with the throw.
func _cell_local(point: Vector2) -> Vector2:
	var size: Vector2 = ComputahLayout.ARMLESS_TUMBLE.frame_size
	if hurl_toward < 0.0:
		point.x = size.x - 1.0 - point.x
	return (point - size / 2.0) * ComputahLayout.SCALE


func _free_hurled() -> void:
	if is_instance_valid(hurled):
		hurled.queue_free()
	hurled = null


# greyson_roar on his mouth: its opening frames once, then its roar frames looping until the settle.
func _start_roar_fx() -> void:
	var spec := Layout.fx(&"roar")
	roar_fx = Sprite2D.new()
	roar_fx.texture = load(spec.texture)
	roar_fx.hframes = spec.hframes
	roar_fx.scale = Vector2.ONE * Layout.SCALE
	roar_fx.offset = spec.offset
	body.fx_layer.add_child(roar_fx)
	roar_fx.global_position = body.roar_mouth_point().round()
	fx.append(roar_fx)
	var hold: Array = spec.hold
	var opening := roar_fx.create_tween()
	for i in hold[0]:
		opening.tween_callback(roar_fx.set_frame.bind(i))
		opening.tween_interval(spec.frame_time)
	opening.tween_callback(_loop_roar_fx.bind(hold, spec.frame_time))


func _loop_roar_fx(hold: Array, frame_time: float) -> void:
	if not is_instance_valid(roar_fx):
		return
	var loop := roar_fx.create_tween().set_loops()
	for i in hold:
		loop.tween_callback(roar_fx.set_frame.bind(i))
		loop.tween_interval(frame_time)


func _stop_roar_fx() -> void:
	if is_instance_valid(roar_fx):
		roar_fx.queue_free()
	roar_fx = null


func _free_fx() -> void:
	_stop_roar_fx()
	for node in fx:
		if is_instance_valid(node):
			node.queue_free()
	fx.clear()


#ENDING IT

# The one way the takeover ends. Idempotent. `route` is false when the fight ended under it, which then goes
# wherever the fight's end sends it rather than into the fight.
func finish_cut(route := true) -> void:
	if finished or not entered:
		return
	finished = true
	waiting_ko = false
	beat_running = false
	BossEntrance.close_balloon(state_machine.takeover_balloon)
	BossEntrance.run_out(waits)
	state_machine.end_takeover_dialogue()
	# Before _settle(), which turns him to face them where they end up.
	if route:
		_settle_player()
	_settle()
	if is_instance_valid(cut):
		cut.end()
	cut = null
	var player := _player()
	if player != null:
		player.is_talking = false
	BossEntrance.settle_arena(get_tree())
	if route:
		state_machine.begin_fight()


# What a held ui_cancel does: whatever is left of the lines and the beats, all at once, landing where their own
# end lands.
func skip_cut() -> void:
	if finished or not entered:
		return
	finish_cut()


# The end state every way out lands on. Idempotent.
func _settle() -> void:
	_free_prop()
	_free_hurled()
	_free_fx()
	var computah = body.computah
	if is_instance_valid(computah):
		computah.lose_arm(true)
		computah.retire_hud(0.0)
		# Thrown out of the ring: nothing of him is left in the way of the fight or the brawl's rubble.
		computah.visible = false
	body.show_body()
	body.set_talking(false)
	body.global_position = state_machine.HOME
	body.put_on_cannon()
	body.state_anim = &"idle"
	body.play_anim(&"idle")
	_face_player()
	body.set_target_active(true)
	body.set_hurtbox_active(false)
	body.show_hud(0.0)
	body.start_music()
	var gates = state_machine.gates()
	if gates != null:
		gates.shut_now()


# Every beat asks this before it touches him, so one that outlived the takeover leaves the fight alone.
func _cut_is_live() -> bool:
	return not finished and is_instance_valid(body) and state_machine.current_state == self


#PIECES

# Waits `seconds` on this node's own clock. A cut-short takeover lets it run out rather than killing it, and the
# caller's own check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


# Walks him to `to` at WALK_SPEED on `anim_name`, facing where he goes.
func _walk_to(to: Vector2, anim_name: StringName) -> void:
	var from: Vector2 = body.global_position
	body.face_toward(to)
	body.play_anim(anim_name)
	var walk := create_tween()
	walk.tween_method(_step_walk.bind(from, to), 0.0, 1.0, maxf(from.distance_to(to) / WALK_SPEED, 0.01))
	await _wait(walk)
	if _cut_is_live():
		body.global_position = to


# Whole pixels, so the pixel-art body doesn't shimmer as it walks.
func _step_walk(weight: float, from: Vector2, to: Vector2) -> void:
	if finished:
		return
	body.global_position = from.lerp(to, weight).round()


func _face_player() -> void:
	var player := _player()
	if player != null:
		body.face_toward(player.global_position)


#THE PLAYER'S MARK

# Onto their mark on rails while he walks in, then facing up at him: on this node's own tween, so a skip runs it out.
func _walk_player() -> void:
	var player := _player()
	if player == null or not is_instance_valid(cut):
		return
	var distance: float = player.global_position.distance_to(PLAYER_MARK)
	if distance <= PLAYER_SNAP:
		_player_on_mark()
		return
	player.face_point(PLAYER_MARK)
	cut.play_player_anim(&"walking")
	var walk := create_tween()
	walk.tween_method(_step_player.bind(player.global_position), 0.0, 1.0,
		clampf(distance / PLAYER_WALK_SPEED, PLAYER_WALK_MIN, PLAYER_WALK_MAX))
	walk.tween_callback(_player_on_mark)
	waits.append(walk)
	walk.finished.connect(func() -> void: waits.erase(walk))


func _step_player(weight: float, from: Vector2) -> void:
	var player := _player()
	if _cut_is_live() and player != null:
		player.global_position = from.lerp(PLAYER_MARK, weight).round()


func _player_on_mark() -> void:
	var player := _player()
	if not _cut_is_live() or player == null or not is_instance_valid(cut):
		return
	player.global_position = PLAYER_MARK
	cut.play_player_anim(&"idle_down")
	player.face_point(state_machine.HOME)


# The end state's player, however the takeover ended up there: on their mark, still.
func _settle_player() -> void:
	var player := _player()
	if player == null:
		return
	player.global_position = PLAYER_MARK
	player.velocity = Vector2.ZERO


func _player() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(PLAYER_PATH) if scene else null
