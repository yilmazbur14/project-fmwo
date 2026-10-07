extends Node2D

# Jordan's room, the rest of his finale (JordanFinale.dialogue's room), after the walk-out has brought the player
# here: a room to walk about in, and the moustache gag at his desk. Then the room shakes itself apart into the void
# under it, he wipes the other bosses out of his server and rises as a demon god, and says his last line. Every number
# it plays on is JordanFinaleLayout's, and the art behind its USE_FINAL_* flags.
#
#   arrive     out of black, the player walks in through the door; Jordan at his desk, gaming (his theme muffled under
#              it only with JordanFinaleLayout.MUSIC_UNDER on, which it isn't)
#   roam       the player walks about; inside the talk zone a TALK prompt comes up over him, and accept or punch
#              starts the talk
#   talk       the player walks to the talk spot and faces him, and the lines start: each "do" line is a beat here
#              (bosses, gag, fall, tremble, zap_liam, zap_rest, collapse, ascend), then his last line
#   leaving    the fade to the TO BE CONTINUED card - or, with his final theme's intro on and in, the smash cut to it on the
#              intro's last downbeat, his last line holding through its wind-up with no press able to rush it. With
#              his last phase switched on (JordanFinaleLayout.USE_GOD_FIGHT) every end lands on that fight instead
#              (after_finale_scene), wherever "the card" is said below.
#
# A HELD ESC ANYWHERE (a BossEntrance, begun with no player) lands on the card too, the sequence's own last beat: it
# closes the balloon, runs every wait out and leaves. So it follows GreysonTakeover: every wait a node-bound tween in
# `waits`, and every beat bailing on `cut` after each await. The talk pairs are read off the live balloon - its
# speaker, its tags and whether it is typing - as the takeover's are.
#
# THE TESTS READ: beat, walker, jordan, cameos (name -> actor, in ladder order), moustache, gag_frame, crumble,
# god_shown, intro (and intro_time()), intro_cues, holding_line and leaving.

const Layout := preload("res://Scripts/JordanFinaleLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const Disintegrate := preload("res://Scripts/Disintegrate.gd")
const StoryActor := preload("res://Scripts/StoryActor.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const ControlsArtLayout := preload("res://Scripts/ControlsArtLayout.gd")

const DIALOGUE := "res://Dialogue/JordanFinale.dialogue"
const UI_THEME := "res://Assets/UI/ui_theme.tres"
const SILENT_DB := -60.0
# StoryPlayer's facings.
const DOWN := 0
const UP := 1
const LEFT := 2
const RIGHT := 3

@onready var void_layer: Node2D = $Void
@onready var crumble: Node2D = $Room
@onready var actors: Node2D = $Actors
@onready var jordan: Node2D = $Actors/Jordan
@onready var chair: Node2D = $Actors/Chair
@onready var walker: CharacterBody2D = $Actors/StoryPlayer
@onready var walls: StaticBody2D = $Walls
@onready var talk_zone: Area2D = $TalkZone
@onready var talk_prompt: Node2D = $TalkPrompt
@onready var fx: Node2D = $Fx
@onready var flash: ColorRect = $FlashLayer/Flash
@onready var fade: ColorRect = $FadeLayer/Fade
@onready var music: AudioStreamPlayer = $Music

var beat := &"arrive"
var cameos := {}
# The moustache as the gag has it: on his lip, then the prop that falls off it.
var moustache: Node2D
# The moustache frame the player is on (JordanFinaleLayout.MOUSTACHE_FRAMES), for a test; &"" before the gag.
var gag_frame := &""
# Where the fallen moustache comes to rest.
var moustache_landing := Vector2.INF
var god: Node2D
var god_shown := false
# Which of the approved desk and gag art is in and imported, taken once as the room is built, so an import landing
# mid-scene can't mix it with its stand-ins.
var final_seated := false
var final_moustache := false
var final_prop := false
var final_standing := false
# The drawn god on one clock (_step_god): his hover, or his talk while his line types, and the aura on the hover's frame.
var god_body: Sprite2D
var god_aura: Sprite2D
var god_hover: Texture2D
var god_talk: Texture2D
var god_clock := 0.0
var god_talking := false
# His final theme's intro, from the flash he becomes the god in; null until then, and without its file.
var intro: AudioStreamPlayer
# His last line is up and holding for the intro's wind-up: presses go nowhere.
var holding_line := false
# Where the intro was when his last line was cued and when the cut began, for a test.
var intro_cues := {}
var leaving := false
var cut := false
var entrance: CanvasLayer
var balloon: Node
var waits: Array[Tween] = []
var sounds := {}
var last_line: RefCounted
var burak_lines := 0
# Jordan's mood off his lines' `jordan` tags, and whether the stand-in pulses red for it.
var mood := &""
# A beat owns Jordan's frames until his next line: his talk pairs leave him alone meanwhile.
var busy := false
# In his chair until he leaps out of it (room_trembles). The glare line he said in it is still up as he leaps, and its
# seated pair must not sit him back down.
var seated := true
var tremble_dust: CPUParticles2D
var pulse_clock := 0.0
var prompt_key: Label
var prompt_glyph: TextureRect


func _ready() -> void:
	ScreenView.reset(get_tree())
	HitStop.clear()
	_build_void()
	_build_room()
	_build_walls()
	_build_talk_zone()
	_build_prompt()
	_build_sounds()
	final_seated = Layout.final_seated()
	final_moustache = Layout.final_moustache()
	final_prop = Layout.final_prop()
	final_standing = Layout.final_standing()
	_set_up_jordan()
	walker.global_position = Layout.DOOR_POINT
	walker.face(DOWN)
	# His last phase loads on threads while this plays, so the cut at its end lands on the fight rather than on its load.
	if Layout.after_finale_scene() == Layout.GOD_FIGHT_SCENE:
		GodLayout.prefetch()
	_start_music()
	entrance = BossEntrance.new()
	entrance.name = "FinaleCut"
	add_child(entrance)
	entrance.skipped.connect(skip)
	entrance.begin()
	_arrive()


#ARRIVAL AND THE ROAM

func _arrive() -> void:
	beat = &"arrive"
	var light := create_tween()
	light.tween_property(fade, "color:a", 0.0, Layout.ARRIVE_FADE)
	waits.append(light)
	await _walk_player(Layout.ENTRY_MARK, Layout.DOOR_POINT.distance_to(Layout.ENTRY_MARK) / PlayerScript.SPEED)
	if not _live():
		return
	if light.is_valid() and light.is_running():
		await light.finished
	waits.erase(light)
	if not _live():
		return
	beat = &"roam"
	walker.controllable = true


func _physics_process(_delta: float) -> void:
	if beat != &"roam" or cut:
		talk_prompt.visible = false
		return
	talk_prompt.visible = talk_zone.get_overlapping_bodies().has(walker)


# While his last line holds for the intro's wind-up, a press does nothing: it neither skips the typing nor ends the
# line. The hold-to-skip polls ui_cancel (BossEntrance), so it still skips.
func _input(event: InputEvent) -> void:
	if not holding_line:
		return
	if event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"ui_cancel") \
			or (event is InputEventMouseButton and event.pressed):
		get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	InputSettings.note_device(event)
	if beat != &"roam" or cut or not talk_prompt.visible:
		return
	if event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"punch"):
		get_viewport().set_input_as_handled()
		_talk()


func _talk() -> void:
	beat = &"talk"
	walker.controllable = false
	walker.velocity = Vector2.ZERO
	talk_prompt.visible = false
	await _walk_player(Layout.TALK_SPOT, Layout.TALK_STEP)
	if not _live():
		return
	walker.face(RIGHT)
	DialogueManager.dialogue_ended.connect(_on_lines_ended, CONNECT_ONE_SHOT)
	balloon = DialogueManager.show_dialogue_balloon(load(DIALOGUE), "room", [self])
	balloon.input_lock_time = Layout.TALK_INPUT_LOCK


func _on_lines_ended(_resource = null) -> void:
	_leave(Layout.after_finale_scene(), Layout.END_FADE)


#THE BEATS THE DIALOGUE CALLS

# He doesn't even turn round: he just keeps clicking.
func no_answer() -> void:
	if not _live():
		return
	await _beat(Layout.NO_ANSWER)


# The other nine come in through the door one after another, in ladder order, each to his mark facing the talk spot,
# as the player glances round at them.
func bosses_walk_in() -> void:
	if not _live():
		return
	beat = &"bosses"
	walker.face(LEFT)
	var arrivals: Array[Tween] = []
	for i in Layout.CAMEOS.size():
		if i > 0:
			await _beat(Layout.BOSS_STEP)
			if not _live():
				return
		arrivals.append(_enter_cameo(Layout.CAMEOS[i], Layout.BOSS_MARKS[i]))
	for arrival in arrivals:
		if arrival.is_valid() and arrival.is_running():
			await _wait(arrival)
			if not _live():
				return
	walker.face(RIGHT)


# The moustache goes on facing the camera - reach, press, done - and the player turns back to him.
func moustache_on() -> void:
	if not _live():
		return
	beat = &"gag"
	walker.face(DOWN)
	var times: Array = Layout.MOUSTACHE_ON
	for i in 3:
		var frame_name: StringName = [&"reach", &"press", &"done"][i]
		_gag_pose(frame_name)
		if frame_name == &"press":
			_put_on_moustache()
		await _beat(times[i])
		if not _live():
			return
	_gag_pose(&"on")
	walker.face(RIGHT)
	await _beat(times[3])


# Two taps at his elbow, and on the second he snaps round and swivels, pulling his headset down. The talk spot is a
# little behind his chair, where y-sort draws the player under him and would hide the glove, so the player is drawn
# over him while he taps.
func tap_shoulder() -> void:
	if not _live():
		return
	walker.z_index = 1
	var times: Array = Layout.TAP
	for i in times.size():
		var tapping := i % 2 == 1
		_gag_pose(&"tap" if tapping else &"tap_windup")
		if tapping:
			_play(&"tink")
		# The stand-in's frames have no tap: a texel's jab says it.
		if not final_moustache:
			walker.sprite.position.x = Layout.SCALE if tapping else 0.0
		if i == times.size() - 1:
			jordan.play(Layout.seated(&"swivel", final_seated), Layout.seated(&"talk_shut", final_seated))
			jordan.sprite.modulate = Color.WHITE
			jordan.face_toward(walker.global_position.x)
		await _beat(times[i])
		if not _live():
			return
	walker.sprite.position.x = 0.0
	walker.z_index = 0
	_gag_pose(&"on")
	await _beat(Layout.SWIVEL - times[-1])


# The moustache comes off his lip and flutters down to the floor, and they stare at each other.
func moustache_falls() -> void:
	if not _live():
		return
	beat = &"fall"
	_gag_pose(&"caught")
	var from: Vector2 = walker.lip_point(Layout.MOUSTACHE_LIP) if final_moustache else walker.lip_point()
	var rest: Vector2 = _prop_rest(walker.global_position + Layout.PROP_FLOOR_OFFSET, from)
	moustache_landing = rest
	_take_off_moustache(from)
	var fall := create_tween()
	fall.tween_method(_flutter.bind(from, rest), 0.0, 1.0, Layout.FALL_TIME)
	await _wait(fall)
	if not _live():
		return
	_land_prop(rest)
	_play(&"tink")
	crumble.add_piece(moustache, &"clutter")
	await _beat(Layout.STARE)


# He leaps up out of his chair, the view comes back out, and the room starts to shake, props coming off the walls.
func room_trembles() -> void:
	if not _live():
		return
	beat = &"tremble"
	seated = false
	jordan.global_position = Layout.JORDAN_STAND_POINT
	jordan.play(Layout.standing(&"rage_shut", final_standing))
	jordan.face_toward(walker.global_position.x)
	jordan.sprite.modulate = Color.WHITE
	if final_seated:
		_show_chair_empty()
	_dust_pop(Layout.JORDAN_STAND_POINT)
	ScreenView.zoom_to(get_tree(), 1.0, Layout.VIEW_SIZE / 2.0, Layout.UNZOOM_TIME)
	crumble.tremble(1)
	_play(&"rumble")
	_start_tremble_dust()
	crumble.drop(&"props", Layout.TREMBLE_DROPS)
	crumble.add_piece(chair, &"furniture")
	await _beat(Layout.LEAP)


# Liam first: a zap, and he dissolves while the others flinch.
func disintegrate_liam() -> void:
	if not _live():
		return
	beat = &"zap_liam"
	var liam: Node2D = cameos.get(&"liam")
	if liam == null:
		return
	busy = true
	jordan.face_toward(liam.global_position.x)
	var zap: Dictionary = Layout.standing(&"zap", final_standing)
	jordan.play(zap)
	await _beat(Layout.ZAP_GESTURE)
	if not _live():
		return
	_zap_line(_off_feet(jordan, zap.hand), liam.global_position + Vector2(0, -90))
	_play(&"dark")
	for other in cameos.values():
		if other != liam:
			_flinch(other)
	var dissolve := Disintegrate.start(self, liam.sprite, Layout.ZAP_DISSOLVE)
	await _wait(dissolve)
	cameos.erase(&"liam")
	liam.queue_free()
	busy = false
	if not _live():
		return
	jordan.play(Layout.standing(&"rage_shut", final_standing))


# The rest of them at once: his arms go up, a ring goes out, and the eight are gone, the nearest first.
func disintegrate_the_rest() -> void:
	if not _live():
		return
	beat = &"zap_rest"
	busy = true
	var arms_up: Dictionary = Layout.standing(&"arms_up", final_standing)
	jordan.play(arms_up)
	await _beat(Layout.ARMS_UP)
	if not _live():
		return
	_ring(_off_feet(jordan, arms_up.ring))
	await _beat(Layout.RING_TIME)
	if not _live():
		return
	crumble.tremble(2)
	_play(&"dark")
	var rest: Array = cameos.values()
	rest.sort_custom(func(a, b): return a.global_position.distance_to(jordan.global_position) < b.global_position.distance_to(jordan.global_position))
	var last: Tween
	for i in rest.size():
		if i > 0:
			await _beat(Layout.REST_STEP)
			if not _live():
				return
		last = Disintegrate.start(self, rest[i].sprite, Layout.REST_DISSOLVE)
		waits.append(last)
	if last != null:
		await _wait(last)
	for actor in rest:
		if is_instance_valid(actor):
			actor.queue_free()
	cameos.clear()
	busy = false
	if not _live():
		return
	jordan.play(Layout.standing(&"rage_shut", final_standing))


# The room falls away into the void under it, layer by layer, the player drifting down with it; then silence.
func room_comes_apart() -> void:
	if not _live():
		return
	beat = &"collapse"
	music.create_tween().tween_property(music, "volume_db", SILENT_DB, Layout.MUSIC_FADE_OUT)
	var drift := create_tween()
	drift.tween_property(walker, "global_position", Layout.VOID_PLAYER_MARK, Layout.VOID_DRIFT)
	waits.append(drift)
	_play(&"rumble")
	if is_instance_valid(tremble_dust):
		tremble_dust.emitting = false
	crumble.collapse(Layout.COLLAPSE_WAVES)
	await _wait(crumble.collapsing)
	if drift.is_valid() and drift.is_running():
		await _wait(drift)
	waits.erase(drift)
	if not _live():
		return
	_stop(&"rumble")
	music.stop()
	await _beat(Layout.COLLAPSE_SILENCE)


# He rises under a growing red aura as the void shakes, a flash, and he is the god, hovering with his rune circle
# coming in behind him.
func ascend() -> void:
	if not _live():
		return
	beat = &"ascend"
	busy = true
	walker.face(UP)
	var from: Vector2 = jordan.global_position
	var aura := _aura(from + Vector2(0, -130))
	var rise := create_tween()
	rise.tween_property(jordan, "global_position", from + Vector2(0, -Layout.RISE_PX), Layout.RISE_TIME)
	rise.parallel().tween_property(aura, "scale", Vector2.ONE, Layout.RISE_TIME).from(Vector2.ONE * 0.3)
	rise.parallel().tween_property(aura, "position", from + Vector2(0, -130 - Layout.RISE_PX), Layout.RISE_TIME)
	ScreenView.shake(get_tree(), Layout.RISE_SHAKE, int(Layout.RISE_TIME / 0.05), 0.05)
	_play(&"roar")
	await _wait(rise)
	if not _live():
		return
	var burst := create_tween()
	burst.tween_property(flash, "color:a", 1.0, Layout.FLASH_UP)
	await _wait(burst)
	if not _live():
		return
	jordan.hide()
	aura.queue_free()
	_show_god()
	# The intro's own hit and roar are the flash's sound: the stand-in sting and drone only play without it.
	_start_intro()
	if intro == null:
		_play(&"sting")
		_play(&"drone")
	var clear := create_tween()
	clear.tween_property(flash, "color:a", 0.0, Layout.FLASH_DOWN)
	await _wait(clear)
	if not _live():
		return
	if intro == null:
		await _beat(Layout.GOD_SETTLE)
		busy = false
		return
	# The hymn under his first hover, and his last line on the quiet stretch after it.
	await _until_intro(Layout.INTRO_LINE_AT)
	if not _live():
		return
	intro_cues[&"line"] = intro_time()
	busy = false
	holding_line = true
	# The balloon's "press on" arrow would ask for a press that does nothing.
	balloon.progress.modulate.a = 0.0
	_cut_on_intro()


# His final theme's intro, from the flash, if it is on (JordanFinaleLayout.USE_INTRO, off) and in and imported.
func _start_intro() -> void:
	if not Layout.USE_INTRO or not ResourceLoader.exists(Layout.INTRO):
		return
	intro = AudioStreamPlayer.new()
	intro.name = "Intro"
	intro.stream = load(Layout.INTRO)
	intro.volume_db = Layout.INTRO_DB
	add_child(intro)
	intro.play()


# Where the intro is, as heard: the last mix's position, the time since it, less the output's latency.
func intro_time() -> float:
	return intro.get_playback_position() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()


# Until the intro, by its own clock, is within a frame of `at`, so what this sets going shows and sounds on it rather
# than a frame late. A beat at a time, each this node's own, so a skip runs it out and a scene change leaves nothing
# waiting; and it ends if the intro does.
func _until_intro(at: float) -> void:
	while _live() and intro.playing:
		var left := at - intro_time() - get_process_delta_time()
		if left <= 0.0:
			return
		await _beat(minf(left, 0.05))


# His last line holds through the wind-up, and the card smashes in on the downbeat the intro ends on.
func _cut_on_intro() -> void:
	await _until_intro(Layout.INTRO_TAIL_AT)
	if not _live():
		return
	intro_cues[&"cut"] = intro_time()
	holding_line = false
	if DialogueManager.dialogue_ended.is_connected(_on_lines_ended):
		DialogueManager.dialogue_ended.disconnect(_on_lines_ended)
	BossEntrance.close_balloon(balloon)
	_leave(Layout.after_finale_scene(), Layout.INTRO_TAIL)


#HIS LINES

func _process(delta: float) -> void:
	_read_lines()
	_pulse(delta)
	_step_god(delta)
	if moustache != null and beat in [&"gag", &"talk", &"bosses"] and is_instance_valid(moustache) and moustache.get_parent() == walker:
		_place_moustache()


# The talk pairs, off the live balloon: who is speaking, how they say it, and whether it is still typing.
func _read_lines() -> void:
	# Untyped: the balloon frees itself when the lines end.
	var live = balloon
	if cut or not is_instance_valid(live) or not live.is_inside_tree():
		return
	var line: RefCounted = live.dialogue_line
	if line == null:
		return
	var typing: bool = live.dialogue_label.is_typing
	if line != last_line:
		last_line = line
		_line_begins(line)
	match line.character:
		"Jordan":
			if not busy:
				_jordan_talks(line.get_tag_value("jordan"), typing)
		"Aiden":
			_gag_pose(&"talk" if typing else &"on")


func _line_begins(line: RefCounted) -> void:
	mood = StringName(line.get_tag_value("jordan")) if line.character == "Jordan" else &""
	if line.character == "Liam":
		var liam: Node2D = cameos.get(&"liam")
		if liam != null:
			var spec: Dictionary = _cameo_spec(&"liam")
			liam.play(spec.talk, spec.idle)
	elif line.character == "Burak":
		burak_lines += 1
		# The second: the gag is coming, and the view closes in on the pair.
		if burak_lines == 2:
			ScreenView.zoom_to(get_tree(), Layout.GAG_ZOOM, Layout.GAG_FOCUS, Layout.GAG_ZOOM_TIME)


func _jordan_talks(how: String, typing: bool) -> void:
	match how:
		"friendly":
			var want: Dictionary = Layout.seated(&"talk" if typing else &"talk_shut", final_seated)
			if seated and jordan.spec != want:
				jordan.play(want)
		"glare":
			var want: Dictionary = Layout.seated(&"glare" if typing else &"glare_shut", final_seated)
			if seated and jordan.spec != want:
				jordan.play(want)
		"rage":
			var want: Dictionary = Layout.standing(&"rage" if typing else &"rage_shut", final_standing)
			if jordan.spec != want:
				jordan.play(want)
		"god":
			god_talking = typing


# The stand-ins have no glare or rage of their own: a red pulse over his idle says it instead.
func _pulse(delta: float) -> void:
	var angry := mood in [&"glare", &"rage"] and not (final_seated and mood == &"glare") \
		and not (final_standing and mood == &"rage") and jordan.visible
	if not angry:
		if pulse_clock > 0.0:
			pulse_clock = 0.0
			jordan.sprite.modulate = Color.WHITE
		return
	pulse_clock += delta
	var weight := 0.5 - 0.5 * cos(TAU * pulse_clock / Layout.PULSE)
	jordan.sprite.modulate = Color.WHITE.lerp(Layout.PULSE_TINT, weight)


#THE CAMEOS

# One boss in: through the door on his walk, or teleported in on his mark. The wait on him getting there.
func _enter_cameo(cameo: Dictionary, mark: Vector2) -> Tween:
	var actor: Node2D = StoryActor.new()
	actor.name = String(cameo.name)
	actors.add_child(actor)
	cameos[cameo.name] = actor
	var arrived := create_tween()
	match cameo.enter:
		&"teleport":
			actor.global_position = mark
			actor.face_toward(Layout.TALK_SPOT.x)
			actor.play(cameo.arrive, cameo.idle)
			arrived.tween_interval(_spec_length(cameo.arrive))
		_:
			actor.global_position = Layout.DOOR_POINT
			if cameo.enter == &"bob":
				actor.play(cameo.idle)
			actor.walk_to(mark, Layout.CAMEO_SPEED, cameo.get("walk", {}))
			arrived.tween_interval(Layout.DOOR_POINT.distance_to(mark) / Layout.CAMEO_SPEED)
	arrived.tween_callback(_cameo_arrived.bind(actor, cameo))
	waits.append(arrived)
	return arrived


func _cameo_arrived(actor: Node2D, cameo: Dictionary) -> void:
	if not is_instance_valid(actor):
		return
	if actor.rails != null and actor.rails.is_valid():
		actor.rails.custom_step(BossEntrance.RUN_OUT_TIME)
	actor.face_toward(Layout.TALK_SPOT.x)
	if cameo.enter == &"glide":
		actor.play(cameo.arrive, cameo.idle)
	elif cameo.enter != &"teleport":
		actor.play(cameo.idle)
	actor.face_toward(Layout.TALK_SPOT.x)


func _cameo_spec(cameo_name: StringName) -> Dictionary:
	for cameo in Layout.CAMEOS:
		if cameo.name == cameo_name:
			return cameo
	return {}


func _flinch(actor: Node2D) -> void:
	var hop := actor.create_tween()
	hop.tween_property(actor.sprite, "position:y", -2.0 * Layout.SCALE, Layout.FLINCH / 2.0)
	hop.tween_property(actor.sprite, "position:y", 0.0, Layout.FLINCH / 2.0)


#THE MOUSTACHE

# The moustache frame the player is on: the drawn sheet's, or the player's own idle under the stand-in.
func _gag_pose(frame_name: StringName) -> void:
	if gag_frame == frame_name:
		return
	gag_frame = frame_name
	if final_moustache:
		walker.pose(Layout.MOUSTACHE_SHEET, [Layout.MOUSTACHE_FRAMES[frame_name]], [1.0])


func _put_on_moustache() -> void:
	if final_moustache:
		return
	moustache = _placeholder_moustache()
	walker.add_child(moustache)
	_place_moustache()


# On the lip of the frame the player is on, and not from behind.
func _place_moustache() -> void:
	moustache.position = walker.lip_point() - walker.global_position
	moustache.visible = walker.facing != UP


func _take_off_moustache(from: Vector2) -> void:
	if is_instance_valid(moustache) and moustache.get_parent() == walker:
		moustache.queue_free()
	if final_prop:
		var spec: Dictionary = Layout.MOUSTACHE_PROP
		var prop := Sprite2D.new()
		prop.texture = load(spec.sheet)
		prop.hframes = roundi(prop.texture.get_width() / spec.frame.x)
		prop.scale = Vector2.ONE * Layout.SCALE
		prop.frame = spec.flutter[0]
		moustache = prop
	else:
		moustache = _placeholder_moustache()
	moustache.global_position = from
	fx.add_child(moustache)


# The prop's resting point: its flat frame's lowest row on the floor line, or the stand-in lying on it.
func _prop_rest(floor_point: Vector2, from: Vector2) -> Vector2:
	var at := Vector2(from.x + Layout.PROP_FLOOR_OFFSET.x, floor_point.y)
	if final_prop:
		var spec: Dictionary = Layout.MOUSTACHE_PROP
		at.y -= (spec.rest_row + 1 - spec.pivot.y) * Layout.SCALE
	return at.round()


# Down from his lip to the floor line, swaying side to side and fluttering. Leftward first, so the prop's flutter,
# once a sway, tips its left end up at the left of the swing and its right end up at the right.
func _flutter(weight: float, from: Vector2, rest: Vector2) -> void:
	if not is_instance_valid(moustache):
		return
	var phase := weight * Layout.FALL_SWAY_CYCLES
	var sway: float = -sin(phase * TAU) * Layout.FALL_SWAY_TEXELS * Layout.SCALE
	moustache.global_position = (from.lerp(rest, weight) + Vector2(sway * (1.0 - weight), 0.0)).round()
	if moustache is Sprite2D:
		var flutter: Array = Layout.MOUSTACHE_PROP.flutter
		moustache.frame = flutter[roundi(phase * flutter.size()) % flutter.size()]
	else:
		moustache.rotation = sin(phase * TAU) * 0.5 * (1.0 - weight)


func _land_prop(rest: Vector2) -> void:
	moustache.global_position = rest
	moustache.rotation = 0.0
	if moustache is Sprite2D:
		moustache.frame = Layout.MOUSTACHE_PROP.flat


func _placeholder_moustache() -> Polygon2D:
	var spec: Dictionary = Layout.PLACEHOLDER_MOUSTACHE
	var shape := Polygon2D.new()
	var points := PackedVector2Array()
	for point in spec.points:
		points.append(point * Layout.SCALE)
	shape.polygon = points
	shape.color = spec.color
	shape.z_index = 1
	return shape


#THE ROOM

# The drawn room in the artist's own pieces, or cut into chunks here if they aren't in yet, or the stand-in's rects.
func _build_room() -> void:
	var specs := []
	if Layout.final_room():
		var pieces := _room_pieces()
		if not pieces.is_empty():
			crumble.build_pieces(Layout.ROOM_LAYERS, pieces)
			return
		for layer_name in Layout.ROOM_LAYERS:
			var texture: Texture2D = load(Layout.room_layer_path(layer_name))
			specs.append({"name": layer_name, "texture": texture, "image": texture.get_image()})
	else:
		for layer_name in Layout.ROOM_LAYERS:
			var image := Image.create(Layout.ROOM_SIZE.x, Layout.ROOM_SIZE.y, false, Image.FORMAT_RGBA8)
			for rect in Layout.PLACEHOLDER_ROOM[layer_name]:
				image.fill_rect(Rect2i(rect[0], rect[1], rect[2], rect[3]), rect[4])
			specs.append({"name": layer_name, "texture": ImageTexture.create_from_image(image), "image": image})
	crumble.build(specs)


# The room artist's pieces, once they are in and every one imported: layer -> its pieces.
func _room_pieces() -> Dictionary:
	if not ResourceLoader.exists(Layout.ROOM_PIECES):
		return {}
	var pieces: Dictionary = load(Layout.ROOM_PIECES).PIECES
	for layer_name in pieces:
		for piece in pieces[layer_name]:
			if not ResourceLoader.exists(piece.texture):
				return {}
	return pieces


func _build_void() -> void:
	if Layout.final_void():
		var back := Sprite2D.new()
		back.texture = load(Layout.VOID_BG)
		back.centered = false
		back.scale = Vector2.ONE * Layout.SCALE
		void_layer.add_child(back)
		return
	var spec: Dictionary = Layout.PLACEHOLDER_VOID
	var back := ColorRect.new()
	back.color = spec.color
	back.size = Layout.VIEW_SIZE
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	void_layer.add_child(back)
	var motes := CPUParticles2D.new()
	motes.amount = spec.amount
	motes.lifetime = 6.0
	motes.preprocess = 6.0
	motes.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	motes.emission_rect_extents = Layout.VIEW_SIZE / 2.0
	motes.position = Layout.VIEW_SIZE / 2.0
	motes.direction = Vector2.UP
	motes.spread = 20.0
	motes.gravity = Vector2.ZERO
	motes.initial_velocity_min = 12.0
	motes.initial_velocity_max = 30.0
	motes.scale_amount_min = Layout.SCALE
	motes.scale_amount_max = Layout.SCALE * 2.0
	motes.color = spec.motes
	motes.texture = _dot()
	void_layer.add_child(motes)


# The room's walkable outline and what stands on its floor, for the walker's foot box.
func _build_walls() -> void:
	var outline := CollisionPolygon2D.new()
	outline.build_mode = CollisionPolygon2D.BUILD_SEGMENTS
	var points := PackedVector2Array()
	for point in Layout.WALK_POLYGON + [Layout.WALK_POLYGON[0]]:
		points.append(point * Layout.SCALE)
	outline.polygon = points
	walls.add_child(outline)
	for rect in Layout.BLOCKERS:
		var shape := CollisionShape2D.new()
		var box := RectangleShape2D.new()
		box.size = rect.size
		shape.shape = box
		shape.position = rect.get_center()
		walls.add_child(shape)


func _build_talk_zone() -> void:
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = Layout.TALK_ZONE.size
	shape.shape = box
	shape.position = Layout.TALK_ZONE.get_center()
	talk_zone.add_child(shape)


# TALK, with the pad's A or ENTER beside it, whichever the player last touched.
func _build_prompt() -> void:
	talk_prompt.position = Layout.PROMPT_POINT
	var panel := PanelContainer.new()
	panel.theme = load(UI_THEME)
	var backing := StyleBoxFlat.new()
	backing.bg_color = Layout.PROMPT_BACKING
	backing.set_content_margin_all(10)
	panel.add_theme_stylebox_override("panel", backing)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	panel.add_child(row)
	prompt_glyph = TextureRect.new()
	prompt_glyph.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	row.add_child(prompt_glyph)
	prompt_key = Label.new()
	prompt_key.text = Layout.PROMPT_KEY
	prompt_key.add_theme_font_size_override("font_size", Layout.PROMPT_FONT_SIZE)
	prompt_key.add_theme_color_override("font_color", Layout.PROMPT_COLOR)
	row.add_child(prompt_key)
	var talk := Label.new()
	talk.text = Layout.PROMPT_TEXT
	talk.add_theme_font_size_override("font_size", Layout.PROMPT_FONT_SIZE)
	talk.add_theme_color_override("font_color", Layout.PROMPT_COLOR)
	row.add_child(talk)
	talk_prompt.add_child(panel)
	_show_prompt_device()
	InputSettings.device_changed.connect(_show_prompt_device.unbind(1))
	panel.position = -panel.get_combined_minimum_size() / 2.0


func _show_prompt_device() -> void:
	if not is_instance_valid(prompt_glyph):
		return
	var pad: bool = InputSettings.device == InputSettings.Device.GAMEPAD
	prompt_glyph.visible = pad
	prompt_key.visible = not pad
	if pad:
		prompt_glyph.texture = ControlsArtLayout.pad_glyph_frame(InputSettings.PAD_BUTTON_FRAMES[JOY_BUTTON_A])


func _build_sounds() -> void:
	var holder := Node.new()
	holder.name = "Sounds"
	add_child(holder)
	var specs: Dictionary = Layout.SOUNDS.duplicate()
	# The god's drone: the rumble, low and held.
	specs[&"drone"] = {"stream": Layout.SOUNDS[&"rumble"].stream, "volume_db": -8.0, "pitch": 0.5}
	for sound_name in specs:
		var spec: Dictionary = specs[sound_name]
		var player := AudioStreamPlayer.new()
		player.name = String(sound_name)
		player.stream = load(spec.stream)
		player.volume_db = spec.volume_db
		player.pitch_scale = spec.pitch
		holder.add_child(player)
		sounds[sound_name] = player


func _start_music() -> void:
	if not Layout.MUSIC_UNDER:
		return
	var theme := JordanArtLayout.theme()
	music.stream = theme.stream
	music.volume_db = theme.volume_db + Layout.MUSIC_UNDER_DB
	music.pitch_scale = Layout.MUSIC_PITCH
	music.play()


func _play(sound_name: StringName) -> void:
	var player: AudioStreamPlayer = sounds.get(sound_name)
	if player != null:
		player.play()


func _stop(sound_name: StringName) -> void:
	var player: AudioStreamPlayer = sounds.get(sound_name)
	if player != null:
		player.stop()


#JORDAN

func _set_up_jordan() -> void:
	jordan.global_position = Layout.CHAIR_POINT
	jordan.play(Layout.seated(&"gaming", final_seated))
	if not final_seated:
		jordan.sprite.modulate = Layout.SEATED_TINT
		_draw_placeholder_chair()
	chair.global_position = Layout.CHAIR_POINT + Vector2(0, 1)


# The stand-in chair: its back to the camera, drawn over him.
func _draw_placeholder_chair() -> void:
	var spec: Dictionary = Layout.PLACEHOLDER_CHAIR
	for part in ["base", "stem", "seat", "back"]:
		var rect: Rect2 = spec[part]
		var piece := Polygon2D.new()
		piece.polygon = PackedVector2Array([rect.position, Vector2(rect.end.x, rect.position.y), rect.end,
			Vector2(rect.position.x, rect.end.y)])
		piece.scale = Vector2.ONE * Layout.SCALE
		piece.position = Vector2(0, -1)
		piece.color = spec.trim if part == "back" else spec.color
		chair.add_child(piece)


func _show_chair_empty() -> void:
	var empty: Node2D = StoryActor.new()
	chair.add_child(empty)
	empty.position = Vector2(0, -1)
	empty.play(Layout.SEATED[&"empty"])


func _show_god() -> void:
	if Layout.final_god():
		god = Node2D.new()
		god.name = "God"
		actors.add_child(god)
		god.global_position = Layout.GOD_POINT
		god_hover = load(Layout.GOD[&"hover"].sheet)
		if ResourceLoader.exists(Layout.GOD[&"talk"].sheet):
			god_talk = load(Layout.GOD[&"talk"].sheet)
		god_body = _god_sheet(Layout.GOD[&"hover"])
		god_body.name = "Body"
		god.add_child(god_body)
		_god_aura()
		_god_runes()
	else:
		var spec: Dictionary = Layout.PLACEHOLDER_GOD
		god = StoryActor.new()
		god.name = "God"
		actors.add_child(god)
		god.global_position = Layout.GOD_POINT
		_placeholder_runes(spec)
		god.play(spec.spec)
		god.sprite.scale = Vector2.ONE * Layout.SCALE * spec.scale
		god.sprite.modulate = spec.tint
		var bob := god.create_tween().set_loops()
		bob.tween_property(god.sprite, "position:y", -spec.bob_px, spec.bob_time / 2.0).set_trans(Tween.TRANS_SINE)
		bob.tween_property(god.sprite, "position:y", 0.0, spec.bob_time / 2.0).set_trans(Tween.TRANS_SINE)
	god_shown = true


# One of his strips, as the artist placed it: its anchor texel's top-left corner on the god's origin.
func _god_sheet(spec: Dictionary) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.sheet)
	sheet.hframes = spec.frames
	sheet.centered = false
	sheet.offset = -spec.anchor
	sheet.scale = Vector2.ONE * Layout.SCALE
	return sheet


# The drawn god's frames. A switch between the hover and the talk starts the new one on its first frame: the talk's
# shut mouth, or hover frame 0, the pose the talk is drawn in.
func _step_god(delta: float) -> void:
	if god_body == null:
		return
	god_clock += delta
	var talking := god_talking and god_talk != null
	var sheet: Texture2D = god_talk if talking else god_hover
	if god_body.texture != sheet:
		god_body.frame = 0
		god_body.texture = sheet
		god_body.hframes = Layout.GOD[&"talk" if talking else &"hover"].frames
		god_clock = 0.0
	god_body.frame = int(god_clock / Layout.GOD_FRAME_TIME) % god_body.hframes
	if god_aura != null:
		god_aura.frame = 0 if talking else god_body.frame


# His aura over him, added, if it is drawn.
func _god_aura() -> void:
	var spec: Dictionary = Layout.GOD[&"aura"]
	if not ResourceLoader.exists(spec.sheet):
		return
	god_aura = _god_sheet(spec)
	god_aura.name = "Aura"
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	god_aura.material = added
	god.add_child(god_aura)


# His rune circle on his chest core, its turn drawn into its frames, faded in as he appears. In the void layer, so it is
# behind him and the player.
func _god_runes() -> void:
	if not ResourceLoader.exists(Layout.GOD_RUNES):
		_placeholder_runes(Layout.PLACEHOLDER_GOD)
		return
	var runes := Sprite2D.new()
	runes.name = "Runes"
	runes.texture = load(Layout.GOD_RUNES)
	runes.hframes = Layout.RUNES_FRAMES
	runes.scale = Vector2.ONE * Layout.SCALE
	runes.position = Layout.GOD_POINT + Layout.RUNES_OFFSET
	runes.modulate.a = 0.0
	void_layer.add_child(runes)
	var turn := runes.create_tween().set_loops()
	for i in Layout.RUNES_FRAMES:
		turn.tween_callback(runes.set_frame.bind(i))
		turn.tween_interval(Layout.RUNES_FRAME_TIME)
	runes.create_tween().tween_property(runes, "modulate:a", 1.0, Layout.RUNES_IN)


# The stand-in's: a red glow, and a blue ring turning in over it for the runes, both in the void layer behind him.
func _placeholder_runes(spec: Dictionary) -> void:
	var glow := Polygon2D.new()
	glow.polygon = _circle(spec.ring_radius * 0.8, 32)
	glow.color = spec.glow
	glow.position = Layout.GOD_POINT + Layout.RUNES_OFFSET
	void_layer.add_child(glow)
	var ring := Line2D.new()
	ring.points = _circle(spec.ring_radius, 48)
	ring.width = 3.0 * Layout.SCALE
	ring.default_color = spec.ring
	ring.closed = true
	ring.position = glow.position
	ring.modulate.a = 0.0
	void_layer.add_child(ring)
	var turn := ring.create_tween().set_loops()
	turn.tween_property(ring, "rotation", TAU, 8.0).from(0.0)
	var come_in := ring.create_tween()
	come_in.tween_property(ring, "modulate:a", 1.0, Layout.RUNES_IN)
	come_in.parallel().tween_property(ring, "scale", Vector2.ONE, Layout.RUNES_IN).from(Vector2.ONE * 0.6)


#EFFECTS

# A point `offset` px off an actor's feet, drawn facing right, where it is now: mirrored if he is.
func _off_feet(actor: Node2D, offset: Vector2) -> Vector2:
	var mirrored: bool = actor.facing_left and actor.spec.get("flips", false)
	return actor.global_position + Vector2(-offset.x if mirrored else offset.x, offset.y)


func _zap_line(from: Vector2, to: Vector2) -> void:
	var line := Line2D.new()
	line.points = PackedVector2Array([from, to])
	line.width = 2.0 * Layout.SCALE
	line.default_color = Layout.ZAP_COLOR
	fx.add_child(line)
	var gone := line.create_tween()
	gone.tween_interval(Layout.ZAP_FLASH)
	gone.tween_callback(line.queue_free)


func _ring(at: Vector2) -> void:
	var ring := Line2D.new()
	ring.points = _circle(Layout.RING_TEXELS * Layout.SCALE, 48)
	ring.width = 3.0 * Layout.SCALE
	ring.default_color = Layout.RING_COLOR
	ring.closed = true
	ring.position = at
	ring.scale = Vector2.ONE * 0.05
	fx.add_child(ring)
	var grow := ring.create_tween()
	grow.tween_property(ring, "scale", Vector2.ONE, Layout.RING_TIME)
	grow.parallel().tween_property(ring, "modulate:a", 0.0, Layout.RING_TIME)
	grow.tween_callback(ring.queue_free)


func _dust_pop(at: Vector2) -> void:
	var puff := CPUParticles2D.new()
	puff.one_shot = true
	puff.amount = 24
	puff.lifetime = Layout.DUST_POP
	puff.explosiveness = 1.0
	puff.direction = Vector2.UP
	puff.spread = 90.0
	puff.initial_velocity_min = 60.0
	puff.initial_velocity_max = 160.0
	puff.scale_amount_min = Layout.SCALE
	puff.scale_amount_max = Layout.SCALE * 2.0
	puff.color = Color(0.8, 0.75, 0.7)
	puff.texture = _dot()
	puff.position = at
	fx.add_child(puff)
	puff.emitting = true
	var gone := puff.create_tween()
	gone.tween_interval(Layout.DUST_POP + 0.1)
	gone.tween_callback(puff.queue_free)


# Dust shaken down off the ceiling while the room trembles, over the whole of it.
func _start_tremble_dust() -> void:
	tremble_dust = CPUParticles2D.new()
	tremble_dust.amount = 70
	tremble_dust.lifetime = 1.6
	tremble_dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	tremble_dust.emission_rect_extents = Vector2(Layout.VIEW_SIZE.x / 2.0, 4.0)
	tremble_dust.position = Vector2(Layout.VIEW_SIZE.x / 2.0, 0.0)
	tremble_dust.direction = Vector2.DOWN
	tremble_dust.spread = 10.0
	tremble_dust.gravity = Vector2(0, 400)
	tremble_dust.initial_velocity_min = 40.0
	tremble_dust.initial_velocity_max = 120.0
	tremble_dust.scale_amount_min = Layout.SCALE
	tremble_dust.scale_amount_max = Layout.SCALE
	tremble_dust.color = Color(0.75, 0.7, 0.65, 0.8)
	tremble_dust.texture = _dot()
	fx.add_child(tremble_dust)
	tremble_dust.emitting = true


# The red aura round him as he rises.
func _aura(at: Vector2) -> Polygon2D:
	var aura := Polygon2D.new()
	aura.polygon = _circle(Layout.AURA_RADIUS, 32)
	aura.color = Layout.AURA_COLOR
	aura.position = at
	aura.z_index = -1
	fx.add_child(aura)
	return aura


func _circle(radius: float, points: int) -> PackedVector2Array:
	var circle := PackedVector2Array()
	for i in points:
		circle.append(Vector2.from_angle(TAU * i / points) * radius)
	return circle


func _dot() -> Texture2D:
	var image := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	image.fill(Color.WHITE)
	return ImageTexture.create_from_image(image)


#LEAVING

# What a held ESC does anywhere in the room: whatever is left of it, gone at once, and a quick fade to the card.
func skip() -> void:
	if cut or leaving:
		return
	cut = true
	if DialogueManager.dialogue_ended.is_connected(_on_lines_ended):
		DialogueManager.dialogue_ended.disconnect(_on_lines_ended)
	BossEntrance.close_balloon(balloon)
	BossEntrance.run_out(waits)
	_leave(Layout.after_finale_scene(), Layout.SKIP_FADE)


# The screen and every sound fade out together, the view comes level, and on to the card.
func _leave(to: String, fade_time: float) -> void:
	if leaving:
		return
	leaving = true
	beat = &"leaving"
	walker.controllable = false
	var out := create_tween()
	out.tween_property(fade, "color:a", 1.0, fade_time)
	for player in find_children("*", "AudioStreamPlayer", true, false):
		if player.playing:
			out.parallel().tween_property(player, "volume_db", SILENT_DB, fade_time)
	await out.finished
	for player in find_children("*", "AudioStreamPlayer", true, false):
		player.stop()
	crumble.tremble(0)
	ScreenView.reset(get_tree())
	HitStop.clear()
	var tree := get_tree()
	# The black stays up across the change: off this scene, which goes, onto the root until the next scene is in. The
	# change is made from this tween's end, after this frame's scene flush, so the frame drawn before the next scene
	# comes in has no scene in it at all, and without the black would show the viewport's grey.
	var cover := fade.get_parent()
	cover.reparent(tree.root)
	tree.scene_changed.connect(cover.queue_free, CONNECT_ONE_SHOT)
	var fight: PackedScene = GodLayout.take_prefetch() if to == Layout.GOD_FIGHT_SCENE else null
	if fight != null:
		tree.change_scene_to_packed(fight)
	else:
		tree.change_scene_to_file(to)


#PIECES

# Every beat asks this after each wait, so one that a skip ran out stops there.
func _live() -> bool:
	return not cut and not leaving


# Waits `seconds` on this node's own clock. A skip runs it out, and the caller's own check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	if tween == null or not tween.is_valid():
		return
	if not waits.has(tween):
		waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _walk_player(to: Vector2, seconds: float) -> void:
	walker.walk_to(to, seconds)
	await _wait(walker.rails)


func _spec_length(spec: Dictionary) -> float:
	var total := 0.0
	var times: Array = spec.times
	for i in spec.frames.size():
		total += times[mini(i, times.size() - 1)]
	return total
