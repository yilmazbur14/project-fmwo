extends Node2D

# The game's last scene, after god-Jordan is beaten (JordanGodDefeated, through ChampionEndingLayout.after_jordan_god):
# the player walks back into the ring and lifts the trophy waiting in the middle of it, the lift peaking on the song's
# drop; the crowd erupts; an unseen announcer begins the line that would name the new champion, and the crowd's
# biggest roar swallows the name; then a slow fade to black and the credits roll over the same song, and the menu.
# Every number is ChampionEndingLayout's, and the art plays its stand-ins until its flags are on.
#
# IT RUNS ON THE SONG'S OWN CLOCK (music_time): the user's track as heard, or - without it - a scene clock started with
# the fallback. Every beat is a cue on that clock, fired a frame ahead (`at` - delta) so what it sets going shows and
# sounds on it; and the walker's place, the lift's frame, the cup and the art's effects are worked out from the clock
# every frame, so a hitch can never push the lift off the drop. Only the looks that aren't on a beat - sound fades,
# the stand-in's flash and confetti, the cup's shine loop - run on the frame clock.
#
# A HELD ESC in the cutscene goes to the credits, the song playing on; a held ESC in the credits goes to the menu. Each
# is a BossEntrance (its hint, its hold and the ESC/pause arbitration), armed only once ui_cancel has been let go - the
# credits' a second after they come up as well - so a key still held from the fight can't skip.
#
# THE TESTS READ: beat, cues (cue name -> the music_time it fired at), schedule, lift_frame, drop_shown_at, own_track,
# music_time(), music, walker, walk_at, walk_speed, trophy and stand (the stand-ins), stand_idle and champion (the
# art's), art_fx, crowds, fade, flash, shower, balloon, entrance, credits_skip, cut, leaving and credits.

const Layout := preload("res://Scripts/ChampionEndingLayout.gd")
const Credits := preload("res://Scripts/ChampionCredits.gd")
const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const StoryPlayer := preload("res://Scripts/StoryPlayerScript.gd")

const STORY_PLAYER_SCENE := "res://Scenes/Player/StoryPlayerScene.tscn"

var beat := &""
var cues := {}
var lift_frame := &""
# The song time on the first frame the lift's DROP frame showed, the drop as seen; -1 before it.
var drop_shown_at := -1.0
var own_track := false
var walker: CharacterBody2D
var trophy: Sprite2D
var champion: Sprite2D
var balloon: Node
var cut := false
var leaving := false
var credits: Control

var arena: Node2D
var crowds: Array[Sprite2D] = []
var dim: Polygon2D
var lights: Node2D
var stand_spot: Node2D
var follow_spot: Node2D
var actors: Node2D
var stand: Sprite2D
var stand_idle: Sprite2D
var fx: Node2D
var art_fx := {}
var confetti_layer: CanvasLayer
var shower: Sprite2D
var flash: ColorRect
var fade_layer: CanvasLayer
var fade: ColorRect
var credits_layer: CanvasLayer
var music: AudioStreamPlayer
var music_db := 0.0
# name -> [{player, trim, at}]: a sound's file, or its stand-in's layers.
var sounds := {}
var level_tweens := {}
# The cutscene's hold-to-skip and the credits', each built once it is armed.
var entrance: CanvasLayer
var credits_skip: CanvasLayer
var credits_shown_msec := 0
# Which of the approved art is in and imported, taken once as the scene is built.
var final_champion := false
var final_fx := false
var final_burst := false
var final_roar := false

# The walk: where it starts, when, and when it is on the mark.
var entry := Vector2.ZERO
var walk_at := 0.0
var arrive_at := 0.0
var walk_speed := 0.0
# The cue table, [{name, at, run}] in time order, and the next one due.
var schedule: Array[Dictionary] = []
var next_cue := 0
var started := false
var scene_clock := 0.0
var clock_last := 0.0
# The cup's shine loop (the waiting cup's frames, or the stand-in's sparkle as each shine starts).
var shine_step := 0
var shine_clock := 0.0
var next_sparkle_at := INF
var sparkle_textures: Array[Texture2D] = []
var roaring := false
var roar_clock := 0.0
var pops_on := false
var pop_clock := 0.0
var shower_clock := 0.0
# The latest confetti burst's start, on the song's clock: the drop's, then the name's.
var burst_at := INF
var fading_from := {}
# Every node-bound tween of the cutscene's looks, for a skip to kill.
var tweens: Array[Tween] = []


func _ready() -> void:
	ScreenView.clear_base(get_tree())
	HitStop.clear()
	own_track = Layout.own_track()
	final_champion = Layout.final_champion()
	final_fx = Layout.final_fx()
	final_burst = Layout.final_burst()
	final_roar = Layout.final_crowd_roar()
	entry = Layout.entry_override if Layout.entry_override != Vector2.INF else Layout.ENTRY_POINT
	_build_arena()
	_build_dim()
	_build_lights()
	_build_actors()
	_build_fx()
	_build_layers()
	_build_music()
	_build_sounds()
	_build_schedule()


func _process(delta: float) -> void:
	if not started:
		_start()
	elif not own_track:
		scene_clock += delta
	_arm_skips()
	if credits != null or cut or leaving:
		return
	var t := music_time()
	var ahead := t + delta
	# The lift's frame first, so a cue on the same frame (the drop's pop and sparkle) finds the cup where it is drawn.
	_step_lift(ahead, t)
	_place_trophy()
	while next_cue < schedule.size() and ahead >= schedule[next_cue].at:
		var cue: Dictionary = schedule[next_cue]
		next_cue += 1
		cues[cue.name] = t
		beat = cue.name
		cue.run.call()
		if credits != null:
			return
	_place_walker(ahead)
	_step_shine(delta)
	_step_hold(ahead, delta)
	_step_art_fx(ahead)
	_step_roar(delta)
	_step_fade(ahead)
	_step_shower(delta)
	if is_instance_valid(balloon) and balloon.is_inside_tree() and balloon.progress.modulate.a > 0.0:
		# The balloon's "press on" arrow would ask for a press that does nothing.
		balloon.progress.modulate.a = 0.0


# Where the song is, as heard: the last mix's position, the time since it, less the output's latency - or, without the
# user's track, the scene clock started with the fallback. Never under 0 and never backwards.
func music_time() -> float:
	var now := scene_clock
	if own_track and music.playing:
		now = music.get_playback_position() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()
	clock_last = maxf(clock_last, now)
	return clock_last


func _start() -> void:
	started = true
	music.play()


#THE BEATS

func _build_schedule() -> void:
	var distance := entry.distance_to(Layout.LIFT_MARK)
	walk_at = Layout.walk_start(distance)
	walk_speed = Layout.walk_pace(distance)
	arrive_at = Layout.arrive_time()
	var appear_at := walk_at
	if entry.y < Layout.APPEAR_Y:
		appear_at += (Layout.APPEAR_Y - entry.y) / (Layout.LIFT_MARK.y - entry.y) * (arrive_at - walk_at)
	var nothing := func() -> void: pass
	var table := [
		[&"fade_in", 0.0, _cue_fade_in],
		[&"gate", maxf(walk_at - Layout.GATE_LEAD, 0.0), _cue_gate],
		[&"walk", walk_at, _cue_walk],
		[&"appear", appear_at, _cue_appear],
		[&"arrive", arrive_at, _cue_arrive],
		[&"hush", Layout.hush_time(), _cue_hush],
		[&"reach", Layout.reach_time(), nothing],
		[&"grip", Layout.grip_time(), _cue_grip],
		[&"drop", Layout.DROP_TIME, _cue_drop],
		[&"settle", Layout.SETTLE_AT, _cue_settle],
		[&"announce", Layout.ANNOUNCE_AT, _cue_announce],
		[&"name", Layout.NAME_AT, _cue_name],
		[&"line_off", Layout.NAME_AT + Layout.NAME_HOLD, _cue_line_off],
		[&"fade", Layout.FADE_AT, _cue_fade],
		[&"credits", Layout.FADE_AT + Layout.FADE_TIME, _start_credits],
	]
	for i in table.size():
		schedule.append({"name": table[i][0], "at": table[i][1], "run": table[i][2], "order": i})
	# By time, and by the table's order where two fall together.
	schedule.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a.at < b.at or (a.at == b.at and a.order < b.order))


func _cue_fade_in() -> void:
	_play(&"murmur")
	get_tree().call_group("arena_crowd", "hush")


func _cue_gate() -> void:
	arena.get_node(^"Gates").open()


func _cue_walk() -> void:
	walker.show()
	walker.face(StoryPlayer.Facing.DOWN)
	walker.pose(StoryPlayer.SHEET, StoryPlayer.WALK_FRAMES, [Layout.WALK_FRAME_TIME], true)
	follow_spot.show()


func _cue_appear() -> void:
	get_tree().call_group("arena_crowd", "cheer", Layout.APPEAR_CHEER)
	_play(&"appear")


func _cue_arrive() -> void:
	walker.end_pose()
	walker.face(StoryPlayer.Facing.DOWN)
	_tween_light(follow_spot, 0.0, Layout.FOLLOW_FADE)
	ScreenView.zoom_to(get_tree(), Layout.PUSH_ZOOM, Layout.FOCUS, maxf(Layout.DROP_TIME - music_time(), 0.05))


func _cue_hush() -> void:
	get_tree().call_group("arena_crowd", "hush")
	_level(&"murmur", Layout.MURMUR_HUSH_DB, Layout.MURMUR_HUSH_TIME)


func _cue_grip() -> void:
	_shake(Layout.GRIP_SHAKE)
	_level(&"murmur", Layout.MURMUR_STRAIN_DB, maxf(Layout.DROP_TIME - music_time(), 0.05))


func _cue_drop() -> void:
	var lift := _tween()
	lift.tween_property(dim, "color:a", 0.0, Layout.DIM_LIFT)
	_tween_light(stand_spot, 0.0, Layout.SPOTS_OUT)
	_tween_light(follow_spot, 0.0, Layout.SPOTS_OUT)
	if not final_fx:
		var white := _tween()
		flash.color.a = Layout.FLASH_ALPHA
		white.tween_property(flash, "color:a", 0.0, Layout.FLASH_TIME)
		shower.show()
		var rain := _tween()
		rain.tween_property(shower, "modulate:a", 1.0, Layout.SHOWER.fade)
	_burst(Layout.DROP_TIME)
	if not final_champion:
		_sparkle()
	_roar(true)
	pops_on = true
	_play(&"roar")
	_play(&"cheer_loop")
	_level(&"murmur", Layout.SILENT_DB, Layout.MURMUR_OUT)
	_punch(Layout.DROP_ZOOM, Layout.DROP_PUNCH, Layout.DROP_SETTLE)
	_shake(Layout.DROP_SHAKE)
	next_sparkle_at = Layout.DROP_TIME + Layout.SPARKLE_EVERY


func _cue_settle() -> void:
	pops_on = false
	_roar(false)
	get_tree().call_group("arena_crowd", "hush")
	_level(&"cheer_loop", Layout.SOUNDS[&"murmur"].volume_db, Layout.CHEER_SETTLE_TIME)
	_music_level(music_db + Layout.MUSIC_DUCK_DB, Layout.MUSIC_DUCK_TIME)


func _cue_announce() -> void:
	var text := "~ start\n%s: [speed=%s]%s\n=> END" % [Layout.ANNOUNCER_NAME, Layout.ANNOUNCE_SPEED, Layout.ANNOUNCER_LINE]
	balloon = DialogueManager.show_dialogue_balloon(DialogueManager.create_resource_from_text(text), "start")
	balloon.input_lock_time = Layout.ANNOUNCER_INPUT_LOCK


# Where the name would be. A line still typing is finished on the spot, so it is never cut off mid-word.
func _cue_name() -> void:
	if is_instance_valid(balloon) and balloon.is_inside_tree() and balloon.dialogue_label.is_typing:
		balloon.dialogue_label.skip_typing()
	_play(&"roar", Layout.NAME_ROAR_BOOST)
	_level(&"cheer_loop", Layout.NAME_CHEER_DB, Layout.MUSIC_BACK_TIME)
	_music_level(music_db, Layout.MUSIC_BACK_TIME)
	_roar(true)
	pops_on = true
	_burst(Layout.NAME_AT)
	_shake(Layout.NAME_SHAKE)
	_punch(Layout.NAME_ZOOM, Layout.NAME_PUNCH, Layout.NAME_SETTLE)


func _cue_line_off() -> void:
	BossEntrance.close_balloon(balloon)


# The picture goes to black on the song's clock (_step_fade), the crowd with it; the music plays on.
func _cue_fade() -> void:
	for sound_name in sounds:
		for layer in sounds[sound_name]:
			fading_from[layer.player] = layer.player.volume_db
		_kill_level(sound_name)
	ScreenView.zoom_to(get_tree(), Layout.FADE_ZOOM, Layout.FOCUS, Layout.FADE_TIME)


#EVERY FRAME, OFF THE CLOCK

func _place_walker(t: float) -> void:
	if not walker.visible:
		return
	var weight := clampf((t - walk_at) / maxf(arrive_at - walk_at, 0.001), 0.0, 1.0)
	walker.global_position = entry.lerp(Layout.LIFT_MARK, weight).round()
	follow_spot.global_position = walker.global_position


# From the arrival, the lift's frame: the art's sheet in place of the player and the waiting cup (its frame 0 is the
# two of them, so the swap doesn't show), or the player's own idle sinking and heaving under the stand-in.
func _step_lift(t: float, now: float) -> void:
	var frame_name := Layout.lift_frame_at(t)
	if frame_name == &"lift" and drop_shown_at < 0.0:
		drop_shown_at = now
	if frame_name == lift_frame:
		return
	lift_frame = frame_name
	if final_champion:
		var lifting := lift_frame != &""
		walker.sprite.visible = not lifting
		stand_idle.visible = not lifting
		champion.visible = lifting
		if lifting:
			champion.frame = Layout.LIFT_FRAMES.find(lift_frame)
	else:
		walker.sprite.position = Layout.PLACEHOLDER_LIFT_SHIFT.get(lift_frame, Vector2.ZERO) * Layout.SCALE


# The stand-in cup where the art's is: on the stand's seat until the drop, over the player there; overhead after it,
# under them.
func _place_trophy() -> void:
	if final_champion:
		return
	trophy.global_position = Layout.at_cell(_cup_bottom())
	trophy.z_index = Layout.TROPHY_UNDER_Z if lift_frame != &"" and not Layout.TROPHY_ON_STAND.has(lift_frame) \
		else Layout.TROPHY_OVER_Z


func _cup_bottom() -> Vector2:
	return Layout.TROPHY_BOTTOM.get(lift_frame, Layout.TROPHY_REST)


# The waiting cup's shine loop on its own times: the art's frames, or on the stand-in a sparkle as each shine starts.
# The stand-in's stops at the drop, where the hold's own sparkles take over.
func _step_shine(delta: float) -> void:
	var times: Array = Layout.CHAMPION.stand_idle_times
	shine_clock += delta
	while shine_clock >= times[shine_step]:
		shine_clock -= times[shine_step]
		shine_step = (shine_step + 1) % times.size()
		if not final_champion and shine_step == 1 and next_sparkle_at == INF:
			_sparkle()
	if final_champion:
		stand_idle.frame = shine_step


# Through the hold: a sparkle every SPARKLE_EVERY, and while the crowd is up, cameras flashing in the crowd.
func _step_hold(t: float, delta: float) -> void:
	if t >= next_sparkle_at:
		next_sparkle_at += Layout.SPARKLE_EVERY
		_sparkle()
	if not pops_on:
		return
	pop_clock += delta * Layout.FLASH_POPS.per_second
	while pop_clock >= 1.0:
		pop_clock -= 1.0
		_flash_pop()


# The art's effects, all from the drop on the song's clock: the lift flash once, the burst once from its latest start,
# the rain from a beat after, and the spot sweep in and then looping.
func _step_art_fx(t: float) -> void:
	if final_burst:
		var burst_spec: Dictionary = Layout.FX[&"confetti_burst"]
		var burst := t - burst_at
		_show_fx(&"confetti_burst", burst >= 0.0 and burst < burst_spec.frames * burst_spec.step,
			int(burst / burst_spec.step))
	if not final_fx:
		return
	var since := t - Layout.DROP_TIME
	var flash_spec: Dictionary = Layout.FX[&"lift_flash"]
	_show_fx(&"lift_flash", since >= 0.0 and since < flash_spec.frames * flash_spec.step, int(since / flash_spec.step))
	var rain_spec: Dictionary = Layout.FX[&"confetti_rain"]
	var raining: float = since - rain_spec.from
	_show_fx(&"confetti_rain", raining >= 0.0, int(raining / rain_spec.step) % rain_spec.frames)
	var sweep_spec: Dictionary = Layout.FX[&"spot_sweep"]
	var intro: float = sweep_spec.intro * sweep_spec.step
	var sweep_frame: int = int(since / sweep_spec.step) if since < intro \
		else sweep_spec.intro + int((since - intro) / sweep_spec.loop_step) % (sweep_spec.frames - sweep_spec.intro)
	_show_fx(&"spot_sweep", since >= 0.0, sweep_frame)


func _show_fx(fx_name: StringName, on: bool, frame_index: int) -> void:
	var sheet: Sprite2D = art_fx[fx_name]
	sheet.visible = on
	if on:
		sheet.frame = clampi(frame_index, 0, Layout.FX[fx_name].frames - 1)


# The crowd's roar while it is up, on both crowd sheets: the stand-in's cheer held on, or the art's roar frames looping,
# the crowd's own script stood down meanwhile so its moods don't play over them.
func _roar(on: bool) -> void:
	if not final_roar:
		get_tree().call_group("arena_crowd", "set_hyped", on)
		return
	roaring = on
	roar_clock = 0.0
	for crowd in crowds:
		crowd.set_process(not on)


func _step_roar(delta: float) -> void:
	if not roaring:
		return
	roar_clock += delta
	for crowd in crowds:
		crowd.frame = Layout.ROAR_FRAMES[int(roar_clock / Layout.ROAR_STEP) % Layout.ROAR_FRAMES.size()]


# Out of black over FADE_IN from the song's start, and back into it over FADE_TIME from FADE_AT, the crowd going with
# it: both on the song's clock, so the black lands on the credits' cue.
func _step_fade(t: float) -> void:
	if t < Layout.FADE_IN:
		fade.color.a = 1.0 - clampf(t / Layout.FADE_IN, 0.0, 1.0)
		return
	if not cues.has(&"fade"):
		fade.color.a = 0.0
		return
	var weight := clampf((t - Layout.FADE_AT) / Layout.FADE_TIME, 0.0, 1.0)
	fade.color.a = weight
	for player in fading_from:
		player.volume_db = lerpf(fading_from[player], Layout.SILENT_DB, weight)


func _step_shower(delta: float) -> void:
	if not shower.visible:
		return
	shower_clock += delta
	shower.frame = int(shower_clock / Layout.SHOWER.frame_time) % Layout.SHOWER.frames


#THE CREDITS, THE SKIPS AND LEAVING

func _arm_skips() -> void:
	if leaving or Input.is_action_pressed(&"ui_cancel"):
		return
	if credits == null:
		if entrance == null and not cut:
			entrance = _skip_entrance("CutsceneSkip", BossEntrance.LAYER)
			entrance.skipped.connect(skip)
	elif credits_skip == null and Time.get_ticks_msec() - credits_shown_msec >= Layout.CREDITS_SKIP_AFTER * 1000.0:
		credits_skip = _skip_entrance("CreditsSkip", Layout.CREDITS_SKIP_LAYER)
		credits_skip.skipped.connect(_leave_to_menu.bind(Layout.SKIP_FADE))


func _skip_entrance(node_name: String, layer_index: int) -> CanvasLayer:
	var node: CanvasLayer = BossEntrance.new()
	node.name = node_name
	add_child(node)
	node.layer = layer_index
	node.begin()
	return node


# What a held ESC does in the cutscene: whatever is left of it, gone, a quick fade to black - or what's left of the
# fade already under way - and the credits, the song playing on.
func skip() -> void:
	if cut or leaving or credits != null:
		return
	cut = true
	BossEntrance.close_balloon(balloon)
	for tween in tweens:
		if tween.is_valid():
			tween.kill()
	tweens.clear()
	for sound_name in sounds:
		_kill_level(sound_name)
	ScreenView.reset(get_tree())
	pops_on = false
	_roar(false)
	get_tree().call_group("arena_crowd", "hush")
	var left := Layout.SKIP_FADE * (1.0 - fade.color.a)
	if left <= 0.0:
		_start_credits()
		return
	var out := create_tween()
	out.tween_property(fade, "color:a", 1.0, left)
	for player in _crowd_players():
		if player.playing:
			out.parallel().tween_property(player, "volume_db", Layout.SILENT_DB, left)
	out.tween_callback(_start_credits)


# Black: the world hidden and the view level, and the credits up over it, the song still playing.
func _start_credits() -> void:
	if credits != null:
		return
	beat = &"credits"
	fade.color.a = 1.0
	for node in [arena, dim, lights, actors, fx]:
		node.hide()
	confetti_layer.hide()
	flash.color.a = 0.0
	ScreenView.reset(get_tree())
	for player in _crowd_players():
		player.stop()
	if is_instance_valid(entrance):
		entrance.end()
	credits_layer = CanvasLayer.new()
	credits_layer.name = "CreditsLayer"
	credits_layer.layer = Layout.CREDITS_LAYER
	add_child(credits_layer)
	credits = Credits.new()
	credits.name = "Credits"
	credits.own_track_played = own_track
	credits.ended.connect(_leave_to_menu.bind(Layout.CREDITS_FADE_OUT))
	credits_layer.add_child(credits)
	credits_shown_msec = Time.get_ticks_msec()


# The text and every sound fade out together, and on to the menu; the black stays up across the change.
func _leave_to_menu(fade_time: float) -> void:
	if leaving:
		return
	leaving = true
	beat = &"leaving"
	if is_instance_valid(credits_skip):
		credits_skip.end()
	if credits != null:
		credits.leave(fade_time)
	var out := create_tween()
	out.tween_interval(fade_time)
	for player in find_children("*", "AudioStreamPlayer", true, false):
		if player.playing:
			out.parallel().tween_property(player, "volume_db", Layout.SILENT_DB, fade_time)
	await out.finished
	for player in find_children("*", "AudioStreamPlayer", true, false):
		player.stop()
	ScreenView.reset(get_tree())
	HitStop.clear()
	var tree := get_tree()
	# The black stays up across the change: off this scene, which goes, onto the root until the menu is in, so the frame
	# drawn between them has no scene in it and would otherwise show the viewport's grey.
	fade.color.a = 1.0
	fade_layer.reparent(tree.root)
	tree.scene_changed.connect(fade_layer.queue_free, CONNECT_ONE_SHOT)
	tree.change_scene_to_file(Layout.MENU_SCENE)


#BUILDING IT

# The normal ring - its mat and centre crest, the ringside and the crowd - with nobody in it and no pause screen. With
# the crowd's roar in, its two crowd sheets become the roar sheets: the same seven frames first, so nothing changes until
# the roar plays.
func _build_arena() -> void:
	arena = load(Layout.ARENA_SCENE).instantiate()
	for drop in Layout.ARENA_DROPS:
		var node := arena.get_node_or_null(drop)
		if node != null:
			arena.remove_child(node)
			node.free()
	arena.name = "Arena"
	add_child(arena)
	for crowd in get_tree().get_nodes_in_group("arena_crowd"):
		if crowd is Sprite2D and arena.is_ancestor_of(crowd):
			crowds.append(crowd)
			if final_roar and Layout.CROWD_ROAR.has(crowd.texture.resource_path):
				crowd.texture = load(Layout.CROWD_ROAR[crowd.texture.resource_path])
				crowd.hframes = Layout.ROAR_HFRAMES


func _build_dim() -> void:
	dim = Polygon2D.new()
	dim.name = "Dim"
	var rect := Layout.DIM_BORDER
	dim.polygon = PackedVector2Array([rect.position, Vector2(rect.end.x, rect.position.y), rect.end,
		Vector2(rect.position.x, rect.end.y)])
	dim.color = Color(0, 0, 0, Layout.DIM_ALPHA)
	dim.z_index = Layout.DIM_Z
	add_child(dim)


func _build_lights() -> void:
	lights = Node2D.new()
	lights.name = "Lights"
	lights.z_index = Layout.LIGHTS_Z
	add_child(lights)
	stand_spot = _spotlight()
	stand_spot.name = "StandSpot"
	stand_spot.global_position = Layout.at_cell(Layout.STAND_FLOOR)
	follow_spot = _spotlight()
	follow_spot.name = "FollowSpot"
	follow_spot.hide()


# Carter's Demon spotlight drawn as light, its anchor texel on this node's origin, or a glowing ellipse.
func _spotlight() -> Node2D:
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	var light: Node2D
	if ResourceLoader.exists(Layout.SPOTLIGHT.texture):
		var sprite := Sprite2D.new()
		sprite.texture = load(Layout.SPOTLIGHT.texture)
		sprite.centered = false
		sprite.offset = -Layout.SPOTLIGHT.anchor
		sprite.scale = Vector2.ONE * Layout.SCALE
		light = sprite
	else:
		var spec: Dictionary = Layout.PLACEHOLDER_SPOTLIGHT
		var glow := Polygon2D.new()
		glow.polygon = _ellipse(spec.radii, spec.points)
		glow.color = spec.color
		light = glow
	light.material = added
	light.modulate.a = Layout.SPOT_ALPHA
	lights.add_child(light)
	return light


# The walker, and in front of where they stop the waiting cup on its stand: the art's - its shine loop, and the lift
# sheet that takes over from the two of them on the arrival - or the stand-ins.
func _build_actors() -> void:
	actors = Node2D.new()
	actors.name = "Actors"
	actors.z_index = Layout.ACTORS_Z
	add_child(actors)
	walker = load(STORY_PLAYER_SCENE).instantiate()
	walker.name = "Walker"
	walker.z_index = Layout.WALKER_Z
	actors.add_child(walker)
	walker.global_position = entry
	walker.face(StoryPlayer.Facing.DOWN)
	walker.hide()
	if final_champion:
		stand_idle = _cell_sheet(Layout.CHAMPION.stand_idle, Layout.CHAMPION.stand_idle_times.size())
		stand_idle.name = "StandIdle"
		stand_idle.z_index = Layout.STAND_Z
		actors.add_child(stand_idle)
		champion = _cell_sheet(Layout.CHAMPION.lift, Layout.LIFT_FRAMES.size())
		champion.name = "Champion"
		champion.hide()
		actors.add_child(champion)
	var stand_spec: Dictionary = Layout.PLACEHOLDER_STAND
	stand = _stand_in(stand_spec.size, stand_spec.anchor, stand_spec.rects)
	stand.name = "Stand"
	stand.z_index = Layout.STAND_Z
	stand.global_position = Layout.at_cell(Layout.STAND_FLOOR)
	actors.add_child(stand)
	trophy = _stand_in(Layout.TROPHY.size, Layout.TROPHY.anchor, Layout.PLACEHOLDER_TROPHY)
	trophy.name = "Trophy"
	trophy.z_index = Layout.TROPHY_OVER_Z
	trophy.global_position = Layout.at_cell(Layout.TROPHY_REST)
	actors.add_child(trophy)
	stand.visible = not final_champion
	trophy.visible = not final_champion


# One of the art's 40x64 strips, the contract's way: on MARK, centred, at SCALE, offset CELL_OFFSET.
func _cell_sheet(path: String, frames: int) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(path)
	sheet.hframes = frames
	sheet.offset = Layout.CELL_OFFSET
	sheet.scale = Vector2.ONE * Layout.SCALE
	sheet.global_position = Layout.MARK
	return sheet


# A stand-in drawn here from its rects on a canvas of `size` texels, with a pure-black keyline round them, its
# `anchor` texel's top-left corner on the node's origin, as the art's anchors are.
func _stand_in(size: Vector2, anchor: Vector2, rects: Array) -> Sprite2D:
	var canvas := Vector2i(size)
	var image := Image.create(canvas.x, canvas.y, false, Image.FORMAT_RGBA8)
	for rect in rects:
		image.fill_rect(Rect2i(rect[0], rect[1], rect[2], rect[3]), rect[4])
	var keyline := image.duplicate() as Image
	for y in canvas.y:
		for x in canvas.x:
			if image.get_pixel(x, y).a > 0.0:
				continue
			for step in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var other: Vector2i = Vector2i(x, y) + step
				if other.x >= 0 and other.y >= 0 and other.x < canvas.x and other.y < canvas.y \
						and image.get_pixel(other.x, other.y).a > 0.0:
					keyline.set_pixel(x, y, Layout.KEYLINE)
					break
	var sprite := Sprite2D.new()
	sprite.texture = ImageTexture.create_from_image(keyline)
	sprite.centered = false
	sprite.offset = -anchor
	sprite.scale = Vector2.ONE * Layout.SCALE
	return sprite


# The fx over everything, and the art's full-screen effects, each at its own depth, hidden until the drop.
func _build_fx() -> void:
	fx = Node2D.new()
	fx.name = "Fx"
	fx.z_index = Layout.FX_Z
	add_child(fx)
	for size in [1, 3]:
		var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
		var middle := int(size / 2.0)
		for i in size:
			image.set_pixel(i, middle, Layout.SPARKLE.color)
			image.set_pixel(middle, i, Layout.SPARKLE.color)
		sparkle_textures.append(ImageTexture.create_from_image(image))
	for fx_name in Layout.FX:
		if not (final_burst if fx_name == &"confetti_burst" else final_fx):
			continue
		var spec: Dictionary = Layout.FX[fx_name]
		var sheet := Sprite2D.new()
		sheet.name = String(fx_name)
		sheet.texture = load(spec.sheet)
		var columns: int = spec.get("columns", spec.frames)
		sheet.hframes = columns
		sheet.vframes = ceili(float(spec.frames) / columns)
		sheet.centered = false
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.z_index = spec.z
		sheet.hide()
		add_child(sheet)
		art_fx[fx_name] = sheet


func _build_layers() -> void:
	confetti_layer = CanvasLayer.new()
	confetti_layer.name = "ConfettiLayer"
	confetti_layer.layer = Layout.CONFETTI_LAYER
	add_child(confetti_layer)
	shower = Sprite2D.new()
	shower.name = "Shower"
	shower.texture = load(Layout.SHOWER.sheet)
	shower.hframes = Layout.SHOWER.frames
	shower.centered = false
	shower.scale = Vector2.ONE * Layout.SCALE
	shower.modulate.a = 0.0
	shower.hide()
	confetti_layer.add_child(shower)
	var flash_layer := CanvasLayer.new()
	flash_layer.name = "FlashLayer"
	flash_layer.layer = Layout.FLASH_LAYER
	add_child(flash_layer)
	flash = _cover(Color(1, 1, 1, 0))
	flash.name = "Flash"
	flash_layer.add_child(flash)
	fade_layer = CanvasLayer.new()
	fade_layer.name = "FadeLayer"
	fade_layer.layer = Layout.FADE_LAYER
	add_child(fade_layer)
	fade = _cover(Color(0, 0, 0, 1))
	fade.name = "Fade"
	fade_layer.add_child(fade)


func _cover(color: Color) -> ColorRect:
	var rect := ColorRect.new()
	rect.color = color
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	return rect


func _build_music() -> void:
	music = AudioStreamPlayer.new()
	music.name = "Music"
	music.stream = load(Layout.MUSIC_LOCAL if own_track else Layout.MUSIC_FALLBACK)
	music_db = Layout.MUSIC_LOCAL_DB if own_track else Layout.MUSIC_FALLBACK_DB
	music.volume_db = music_db
	add_child(music)


func _build_sounds() -> void:
	var holder := Node.new()
	holder.name = "Sounds"
	add_child(holder)
	for sound_name in Layout.SOUNDS:
		var spec: Dictionary = Layout.SOUNDS[sound_name]
		var layers: Array = []
		if ResourceLoader.exists(spec.final):
			layers.append({stream = spec.final, volume_db = spec.volume_db, pitch = 1.0, at = 0.0, stand_in = false})
		else:
			for layer in spec.stand_in:
				layers.append({stream = layer.stream, volume_db = layer.volume_db, pitch = layer.pitch, at = layer.at,
					stand_in = true})
		sounds[sound_name] = []
		for i in layers.size():
			var layer: Dictionary = layers[i]
			var player := AudioStreamPlayer.new()
			player.name = "%s_%d" % [sound_name, i]
			var stream: AudioStream = load(layer.stream)
			# A stand-in is someone else's sound (crowd_cheer.wav is Greyson's too): looped on a copy, never on it.
			if spec.loop and layer.stand_in:
				stream = stream.duplicate()
				if stream is AudioStreamWAV:
					stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
					stream.loop_begin = 0
					stream.loop_end = int(stream.get_length() * stream.mix_rate)
			player.stream = stream
			player.pitch_scale = layer.pitch
			player.volume_db = layer.volume_db
			holder.add_child(player)
			sounds[sound_name].append({"player": player, "trim": layer.volume_db - spec.volume_db, "at": layer.at})


#SOUNDS, LOOKS AND FX

# A sound from the top, each layer at its own offset, `boost` dB over its level.
func _play(sound_name: StringName, boost := 0.0) -> void:
	_kill_level(sound_name)
	for layer in sounds[sound_name]:
		var player: AudioStreamPlayer = layer.player
		player.volume_db = Layout.SOUNDS[sound_name].volume_db + layer.trim + boost
		if layer.at <= 0.0:
			player.play()
		else:
			var later := _tween()
			later.tween_interval(layer.at)
			later.tween_callback(player.play)


# A sound's level (a final level: each stand-in layer keeps its trim) over `seconds`.
func _level(sound_name: StringName, to_db: float, seconds: float) -> void:
	_kill_level(sound_name)
	var tween := create_tween().set_parallel()
	for layer in sounds[sound_name]:
		tween.tween_property(layer.player, "volume_db", to_db + layer.trim, seconds)
	level_tweens[sound_name] = tween


func _kill_level(sound_name: StringName) -> void:
	var tween: Tween = level_tweens.get(sound_name)
	if tween != null and tween.is_valid():
		tween.kill()
	level_tweens.erase(sound_name)


func _music_level(to_db: float, seconds: float) -> void:
	var tween := _tween()
	tween.tween_property(music, "volume_db", to_db, seconds)


func _crowd_players() -> Array[AudioStreamPlayer]:
	var players: Array[AudioStreamPlayer] = []
	for sound_name in sounds:
		for layer in sounds[sound_name]:
			players.append(layer.player)
	return players


func _tween() -> Tween:
	var tween := create_tween()
	tweens.append(tween)
	return tween


func _tween_light(light: Node2D, to_alpha: float, seconds: float) -> void:
	_tween().tween_property(light, "modulate:a", to_alpha, seconds)


func _shake(spec: Array) -> void:
	ScreenView.shake(get_tree(), spec[0], spec[1], spec[2])


# A camera punch in to `to_zoom` and back to the push's.
func _punch(to_zoom: float, punch: float, settle: float) -> void:
	ScreenView.zoom_to(get_tree(), to_zoom, Layout.FOCUS, punch)
	var back := _tween()
	back.tween_interval(punch)
	back.tween_callback(func() -> void: ScreenView.zoom_to(get_tree(), Layout.PUSH_ZOOM, Layout.FOCUS, settle))


# A burst of confetti from `at` on the song's clock: the art's, or the stand-in's, and the pop's sound either way.
func _burst(at: float) -> void:
	_play(&"pop")
	if final_burst:
		burst_at = at
		return
	_confetti()


# The stand-in confetti: both cannons from below the frame, and a pop of bits off the cup's top.
func _confetti() -> void:
	var spec: Dictionary = Layout.CANNON
	for i in Layout.CANNONS.size():
		var cannon := _bits(spec.amount, spec.lifetime, spec.bit, Layout.CONFETTI_COLORS)
		cannon.position = Layout.CANNONS[i]
		var inward := 1.0 if Layout.CANNONS[i].x < Layout.FOCUS.x else -1.0
		cannon.direction = Vector2.UP.rotated(deg_to_rad(spec.lean * inward))
		cannon.spread = spec.spread
		cannon.explosiveness = spec.explosiveness
		cannon.initial_velocity_min = spec.velocity.x
		cannon.initial_velocity_max = spec.velocity.y
		cannon.gravity = Vector2(0, spec.gravity)
		cannon.damping_min = spec.damping.x
		cannon.damping_max = spec.damping.y
		cannon.angular_velocity_min = -spec.spin
		cannon.angular_velocity_max = spec.spin
		_fire(cannon)
	var pop_spec: Dictionary = Layout.TROPHY_POP
	var pop := _bits(pop_spec.amount, pop_spec.lifetime, pop_spec.bit, Layout.POP_COLORS)
	pop.position = Layout.at_cell(_cup_bottom() - Vector2(0, Layout.TROPHY.size.y))
	pop.direction = Vector2.UP
	pop.spread = pop_spec.spread
	pop.explosiveness = 1.0
	pop.initial_velocity_min = pop_spec.velocity.x
	pop.initial_velocity_max = pop_spec.velocity.y
	pop.gravity = Vector2(0, pop_spec.gravity)
	_fire(pop)


func _bits(amount: int, lifetime: float, bit: Vector2, colors: Array[Color]) -> CPUParticles2D:
	var bits := CPUParticles2D.new()
	bits.one_shot = true
	bits.amount = amount
	bits.lifetime = lifetime
	var image := Image.create(int(bit.x), int(bit.y), false, Image.FORMAT_RGBA8)
	image.fill(Color.WHITE)
	bits.texture = ImageTexture.create_from_image(image)
	bits.scale_amount_min = Layout.SCALE
	bits.scale_amount_max = Layout.SCALE
	var palette := Gradient.new()
	palette.interpolation_mode = Gradient.GRADIENT_INTERPOLATE_CONSTANT
	var offsets := PackedFloat32Array()
	for i in colors.size():
		offsets.append(float(i) / colors.size())
	palette.offsets = offsets
	palette.colors = PackedColorArray(colors)
	bits.color_initial_ramp = palette
	return bits


func _fire(bits: CPUParticles2D) -> void:
	fx.add_child(bits)
	bits.emitting = true
	var gone := bits.create_tween()
	gone.tween_interval(bits.lifetime + 0.2)
	gone.tween_callback(bits.queue_free)


# A sparkle off the cup's highlight texel, wherever the cup is on this frame: a dot, a cross, a dot, added.
func _sparkle() -> void:
	var texel: Vector2 = _cup_bottom() - Layout.TROPHY.anchor + Layout.TROPHY.sparkle
	var star := Sprite2D.new()
	star.texture = sparkle_textures[0]
	star.scale = Vector2.ONE * Layout.SCALE
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	star.material = added
	star.global_position = Layout.at_cell(texel) + Vector2.ONE * Layout.SCALE / 2.0
	fx.add_child(star)
	var twinkle := star.create_tween()
	for size in Layout.SPARKLE.steps:
		twinkle.tween_callback(star.set_texture.bind(sparkle_textures[0 if size == 1 else 1]))
		twinkle.tween_interval(Layout.SPARKLE.step)
	twinkle.tween_callback(star.queue_free)


# A camera going off somewhere in the crowd.
func _flash_pop() -> void:
	var spec: Dictionary = Layout.FLASH_POPS
	var bands: Array[Rect2] = Layout.CROWD_BANDS
	var total := 0.0
	for band in bands:
		total += band.get_area()
	var pick := randf() * total
	var band: Rect2 = bands[-1]
	for candidate in bands:
		pick -= candidate.get_area()
		if pick <= 0.0:
			band = candidate
			break
	var side: float = spec.size * Layout.SCALE
	var at := (band.position + Vector2(randf() * band.size.x, randf() * band.size.y)).snapped(Vector2.ONE * Layout.SCALE)
	var pop := Polygon2D.new()
	pop.polygon = PackedVector2Array([Vector2.ZERO, Vector2(side, 0), Vector2(side, side), Vector2(0, side)])
	pop.color = spec.color
	pop.position = at
	fx.add_child(pop)
	var gone := pop.create_tween()
	gone.tween_property(pop, "modulate:a", 0.0, spec.life)
	gone.tween_callback(pop.queue_free)


func _ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var shape := PackedVector2Array()
	for i in points:
		shape.append(Vector2(cos(TAU * i / points) * radii.x, sin(TAU * i / points) * radii.y))
	return shape
