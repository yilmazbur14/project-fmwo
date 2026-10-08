extends State

# God-form Jordan's last kill, with JordanGodLayout.USE_FINAL_BEAM on (JordanGodScript._on_defeated): instead of his
# defeat, a five-bar charge mash and a beam. The KO plays out (the finisher lands, a juggled puppet comes down), the
# player is sealed and his HUD goes; the strings snap and the puppets crumple and dissolve; a white cut puts the player
# on the staging's mark; then the mash (FinisherTierMeter on FinalBeamLayout's bars, the presses MashInput's), every
# bar closing the camera in a step, growing the ball and adding a syllable of the shout. Five bars fire the beam and
# he disintegrates, and the fight is won (JordanGodScript.finish_beam_won). Fewer, and a weak beam half-dissolves him -
# or none, and the charge fizzles - he laughs, pulls himself back together with REVIVE_HEALTH, and the rotation goes
# on; his next kill brings the beam back, a little easier each time it failed (MERCY_PER_FAIL).
#
# Nothing in it is skippable, and the pause holds all of it: every wait a node-bound tween in `waits`, the meter on the
# physics step, the camera on the process step, and the input isn't delivered while paused; his shout over the
# disintegration (FinalBeamLayout.SHOUT) is a balloon it puts up and takes down on those waits. Entered once a kill,
# so a run cut short never resumes into the next (generation). release() puts back everything it touched; on a win he
# stays gone.
#
# THE TESTS READ: beat (&"ko", &"collapse", &"stage", &"mash", then &"release", &"dissolve", &"fade", &"settle", &"won",
# or &"weak" / &"fizzle", &"reform", &"revived"), meter, bars, fails, result (&"won", &"weak", &"fizzle"), entries,
# min_press_interval (real seconds; a test sets 0), fx, ui and shout_balloon.

const Layout := preload("res://Scripts/FinalBeamLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const FinalBeamFx := preload("res://Scripts/FinalBeamFx.gd")
const FinalBeamMeterUI := preload("res://Scripts/FinalBeamMeterUI.gd")
const FinisherTierMeter := preload("res://Scripts/FinisherTierMeter.gd")
const MashInput := preload("res://Scripts/MashInput.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")

# PlayerScript.Facing's order.
const FACINGS: Array[Vector2] = [Vector2.DOWN, Vector2.UP, Vector2.LEFT, Vector2.RIGHT]

var god: Node2D
var state_machine: Node

var beat := &""
var meter: RefCounted
var bars := 0
var fails := 0
var result := &""
var entries := 0
var min_press_interval := Layout.MIN_PRESS_INTERVAL
var fx: Node2D
var ui: CanvasLayer
var shout_dialogue: Resource
var shout_balloon: Node

var generation := 0
var waits: Array[Tween] = []
var released := true
var mashing := false
var player_held := false
var last_action := &""
var last_press_usec := 0
var voices := {}
var humming := false
var roaring := false
var crackling := false
var shattered := false
var roar_left := 0.0
var crackle_left := 0.0
var music_db := 0.0
var music_saved := false
var music_tween: Tween
var camera_on := false
var cam_zoom_from := 1.0
var cam_zoom_to := 1.0
var cam_focus_from := Vector2.ZERO
var cam_focus_to := Vector2.ZERO
var cam_time := 0.0
var cam_length := 0.0
var rumble_px := 0.0
var rumble_left := 0.0
var kick_left := 0.0


func Enter() -> void:
	generation += 1
	entries += 1
	released = false
	beat = &"ko"
	result = &""
	bars = 0
	meter = null
	mashing = false
	camera_on = false
	rumble_px = 0.0
	god.play(&"hit")
	_run(generation)


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func Update(delta: float) -> void:
	_step_camera(delta)
	_step_rumble(delta)
	_step_sounds(delta)


func Physics_Update(delta: float) -> void:
	if not mashing:
		return
	meter.advance(delta)
	if meter.resolved:
		_resolve()


#THE FLOW

func _run(run_of: int) -> void:
	while not _ko_over():
		await _wait(0.0)
		if _stale(run_of):
			return
	await _wait(Layout.KO_HOLD)
	var p := _player()
	if _stale(run_of) or p == null:
		return
	p.lock_actions_sealed()
	player_held = true
	god.set_hud(false, GodLayout.HUD_FADE)
	_duck_music()
	beat = &"collapse"
	# Staggered, held on his hit's last frame until the beam lands: the kill's own flinch has handed him back to his loop.
	god.play(&"hit")
	_build(p)
	await _collapse(run_of)
	if _stale(run_of):
		return
	beat = &"stage"
	fx.white_cut(Layout.STAGE)
	await _wait(Layout.STAGE.white_in)
	if _stale(run_of):
		return
	_stage(p)
	await _wait(Layout.STAGE.white_hold + Layout.STAGE.white_out)
	if _stale(run_of):
		return
	meter = FinisherTierMeter.new(Layout.GAIN, Layout.drains(fails), Layout.WINDOWS, Layout.START_GRACE, Layout.IDLE_STOP)
	fx.pose(&"enter")
	fx.begin_charge()
	ui.show_meter(meter)
	await _wait(fx.pose_length(&"enter"))
	if _stale(run_of):
		return
	beat = &"mash"
	last_action = &""
	last_press_usec = 0
	rumble_px = Layout.RUMBLES[0]
	fx.pose(&"charge")
	_hum(true)
	mashing = true


# The KO is over once the finisher that killed him has landed and no puppet is still in the air (as his defeat waits).
func _ko_over() -> bool:
	var p := _player()
	if p != null and p.finisher.is_active():
		return false
	return not god.defeat_puppets.any(func(puppet) -> bool: return is_instance_valid(puppet) and puppet.is_juggled())


# Every texture loads here, in a beat with nothing else to draw, never in a preload: the fight's states load on a thread.
func _build(p: CharacterBody2D) -> void:
	fx = FinalBeamFx.new()
	fx.name = "FinalBeamFx"
	god.layer(&"fx").add_child(fx)
	fx.setup(god, p)
	ui = FinalBeamMeterUI.new()
	ui.name = "FinalBeamMeter"
	add_child(ui)
	ui.setup(p)
	if voices.is_empty():
		_build_sounds()
	if shout_dialogue == null:
		shout_dialogue = load(Layout.SHOUT.dialogue)


# The strings snap, the puppets crumple and dissolve, and they are gone.
func _collapse(run_of: int) -> void:
	var strings: Node2D = god.layer(&"strings")
	var puppets: Array = god.defeat_puppets.filter(func(puppet) -> bool: return is_instance_valid(puppet))
	if not puppets.is_empty():
		god.play_sound(&"snap")
	for puppet in puppets:
		strings.snap(puppet)
		puppet.crumple()
	await _wait(Layout.COLLAPSE.snap + Layout.COLLAPSE.crumple)
	if _stale(run_of):
		return
	for puppet in puppets:
		if is_instance_valid(puppet):
			puppet.dissolve(Layout.COLLAPSE.dissolve)
	if not puppets.is_empty():
		god.play_sound(&"dissolve")
	await _wait(Layout.COLLAPSE.dissolve)
	if _stale(run_of):
		return
	for puppet in puppets:
		if is_instance_valid(puppet):
			puppet.queue_free()
	god.defeat_puppets.clear()


# Under the white: on the mark, turned, drawn, and the camera on its first step at once.
func _stage(p: CharacterBody2D) -> void:
	var spec: Dictionary = Layout.staging()
	p.warp_to(spec.mark)
	p.face_point(spec.mark + FACINGS[clampi(spec.facing, 0, FACINGS.size() - 1)] * 100.0)
	fx.stage_player()
	_camera_snap(0)


#THE MASH

func _input(event: InputEvent) -> void:
	if not mashing or released:
		return
	var p := _player()
	if p == null:
		return
	var action := MashInput.pressed_action(p, event)
	var attack_or_dash := event.is_action_pressed(&"punch") or event.is_action_pressed(&"dodge")
	if action.is_empty() and not attack_or_dash and not (p.feel_v2 and MashInput.swallows(event)):
		return
	# Before the event is marked handled: the autoload's device tracker sits below this node in the propagation order.
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()
	if not action.is_empty():
		_press(action)


func _press(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	if not MashInput.counts(action, last_action, now, last_press_usec, min_press_interval):
		return
	last_action = action
	last_press_usec = now
	var banked: int = meter.press()
	ui.pressed(action)
	if banked > 0:
		_on_bank(banked)
	if meter.resolved:
		_resolve()


func _on_bank(count: int) -> void:
	bars = count
	fx.set_bars(count)
	fx.bank_burst()
	ui.bank(count)
	_play(StringName("bank_%d" % count))
	_play(&"swell", 1.0 + 0.2 * count)
	if count >= Layout.BARS:
		return
	_camera_to(Layout.staging().zooms[count], Layout.staging().focus, Layout.STEP_TIME)
	_kick(Layout.KICKS[count - 1], Layout.KICK_STEPS)
	rumble_px = Layout.RUMBLES[count]
	_hum_level()


func _resolve() -> void:
	if not mashing:
		return
	mashing = false
	bars = meter.banked
	_hum(false)
	if bars >= Layout.BARS:
		_win(generation)
	else:
		_fail(generation)


#SUCCESS

func _win(run_of: int) -> void:
	result = &"won"
	beat = &"release"
	rumble_px = 0.0
	ui.release_won()
	fx.release_flash()
	_kick(Layout.KICKS[Layout.BARS - 1], Layout.RELEASE_KICK_STEPS)
	# Punched in on the beam leaving the muzzle, not on the charge's focus between the two of them.
	_camera_to(Layout.RELEASE_ZOOM, fx.muzzle_point(), 0.0)
	HitStop.freeze(get_tree(), Layout.RELEASE_HIT_STOP)
	_play(&"release")
	fx.pose(&"release")
	fx.fire(1.0, Layout.BEAM_TRAVEL)
	await _wait_real(Layout.RELEASE_PUNCH)
	if _stale(run_of):
		return
	_camera_to(1.0, ScreenView.base_focus, Layout.RELEASE_PULL)
	await _wait(Layout.MUZZLE_OPEN + Layout.BEAM_TRAVEL)
	if _stale(run_of):
		return
	_impact(true)
	beat = &"dissolve"
	_shout()
	fx.pose(&"hold")
	fx.begin_end(true)
	fx.fade_runes()
	fx.dissolve(Layout.DISSOLVE_TIME)
	_play(&"disintegrate")
	_beam_sounds(true)
	rumble_px = Layout.HOLD_RUMBLE
	await _wait(Layout.DISSOLVE_TIME)
	if _stale(run_of):
		return
	_end_shout()
	beat = &"fade"
	_beam_sounds(false)
	rumble_px = 0.0
	fx.hide_god()
	ui.fade_all()
	fx.punch_through()
	_kick(Layout.PUNCH_THROUGH.burst, Layout.PUNCH_THROUGH.burst_steps)
	await _wait(Layout.PUNCH_THROUGH.time + Layout.BODY_FADE)
	if _stale(run_of):
		return
	beat = &"settle"
	fx.pose(&"settle")
	await _wait(fx.pose_length(&"settle"))
	if _stale(run_of):
		return
	fx.reveal_player()
	beat = &"won"
	await _wait(Layout.EMPTY_HOLD)
	if _stale(run_of):
		return
	# Nothing of the view, the time scale or the lock may reach the ending.
	camera_on = false
	ScreenView.reset(get_tree())
	HitStop.clear()
	_restore_music(0.0)
	_unlock()
	god.finish_beam_won()


# Up over the disintegration with no press to move it on: its input lock, on the real clock, outlasts it.
func _shout() -> void:
	shout_balloon = DialogueManager.show_dialogue_balloon(shout_dialogue, Layout.SHOUT.title)
	shout_balloon.input_lock_time = Layout.DISSOLVE_TIME + 1.0


func _end_shout() -> void:
	if is_instance_valid(shout_balloon):
		shout_balloon.queue_free()
	shout_balloon = null


func _impact(full: bool) -> void:
	if full:
		HitStop.freeze(get_tree(), Layout.IMPACT_HIT_STOP)
	_kick(Layout.IMPACT_SHAKE * (1.0 if full else 0.5), Layout.IMPACT_SHAKE_STEPS)
	fx.impact_at_core(full)
	god.play(&"hit")
	_play(&"impact")


#FAIL

func _fail(run_of: int) -> void:
	fails += 1
	rumble_px = 0.0
	ui.release_failed()
	if bars == 0:
		result = &"fizzle"
		beat = &"fizzle"
		fx.fizzle_at(fx.ball_point(), 0)
		fx.pose(&"fail")
		_play(&"fizzle")
		await _wait(Layout.POP_TIME)
		if _stale(run_of):
			return
		god.play(&"laugh")
		_play(&"laugh")
		await _wait(Layout.LAUGH_TIME)
		if _stale(run_of):
			return
		await _reform(run_of, 0.0)
		return
	result = &"weak"
	beat = &"weak"
	var reached: float = Layout.FAIL_DISSOLVE[bars]
	_play(&"release", 1.1)
	fx.pose(&"release")
	fx.fire(Layout.FAIL_WIDTH[bars], Layout.BEAM_TRAVEL)
	_camera_to(1.0, ScreenView.base_focus, Layout.RELEASE_PULL)
	await _wait(Layout.MUZZLE_OPEN + Layout.BEAM_TRAVEL)
	if _stale(run_of):
		return
	_impact(false)
	fx.pose(&"hold")
	fx.begin_end(false)
	fx.come_apart(reached, Layout.FAIL_HOLD)
	_beam_sounds(true)
	rumble_px = Layout.HOLD_RUMBLE * 0.5
	await _wait(Layout.FAIL_HOLD)
	if _stale(run_of):
		return
	_beam_sounds(false)
	rumble_px = 0.0
	fx.sputter(Layout.FAIL_SPUTTER)
	_play(&"fizzle")
	await _wait(Layout.FAIL_SPUTTER)
	if _stale(run_of):
		return
	fx.pose(&"fail")
	god.play(&"laugh")
	_play(&"laugh")
	await _reform(run_of, reached)


# He laughs and pulls himself back together with REVIVE_HEALTH, the view easing back to the fight's own, and the
# rotation goes on.
func _reform(run_of: int, reached: float) -> void:
	beat = &"reform"
	_play(&"reform")
	var seconds := Layout.REFORM_TIME
	if result == &"weak":
		seconds = maxf(seconds, fx.reform(reached))
	god.revive(GodLayout.REVIVE_HEALTH, Layout.REVIVE_REFILL)
	_camera_to(1.0, ScreenView.base_focus, Layout.CAMERA_BACK)
	_restore_music(Layout.CAMERA_BACK)
	await _wait(seconds)
	if _stale(run_of):
		return
	beat = &"revived"
	camera_on = false
	fx.restore_god()
	fx.reveal_player()
	ui.fade_all()
	_unlock()
	state_machine.on_child_transition(self, "Idle")


#THE CAMERA (the only writer of the view while it runs, as the finisher's charge is)

func _camera_snap(step: int) -> void:
	if ScreenView.zoom_tween:
		ScreenView.zoom_tween.kill()
	_camera_to(Layout.staging().zooms[step], Layout.staging().focus, 0.0)
	_step_camera(0.0)


# Eased out over `seconds` of game time, from where the view is; at once for 0.
func _camera_to(zoom: float, focus: Vector2, seconds: float) -> void:
	camera_on = true
	cam_zoom_from = ScreenView.zoom
	cam_focus_from = ScreenView.focus
	cam_zoom_to = zoom
	cam_focus_to = focus
	cam_time = 0.0
	cam_length = seconds


func _step_camera(delta: float) -> void:
	if not camera_on:
		return
	cam_time = minf(cam_time + delta, cam_length)
	var share := 1.0 if cam_length <= 0.0 else cam_time / cam_length
	var eased := 1.0 - (1.0 - share) * (1.0 - share)
	ScreenView.zoom = lerpf(cam_zoom_from, cam_zoom_to, eased)
	ScreenView.focus = cam_focus_from.lerp(cam_focus_to, eased)
	ScreenView.apply(get_tree())


# A px rattle every RUMBLE_STEP real seconds, held off while a kick plays.
func _step_rumble(delta: float) -> void:
	var real := delta / maxf(Engine.time_scale, 0.001)
	kick_left -= real
	rumble_left -= real
	if rumble_px <= 0.0 or kick_left > 0.0 or rumble_left > 0.0:
		return
	ScreenView.shake(get_tree(), rumble_px, 1, Layout.RUMBLE_STEP, Vector2.ZERO, true)
	rumble_left = Layout.RUMBLE_STEP


func _kick(strength: float, steps: int) -> void:
	ScreenView.shake(get_tree(), strength, steps, Layout.KICK_STEP_TIME, Vector2.ZERO, true)
	kick_left = steps * Layout.KICK_STEP_TIME


#SOUND

func _build_sounds() -> void:
	var holder := Node.new()
	holder.name = "Sounds"
	add_child(holder)
	for cue in Layout.SOUNDS:
		var list := []
		for layer: Dictionary in Layout.SOUNDS[cue]:
			if not ResourceLoader.exists(layer.stream):
				continue
			var voice := AudioStreamPlayer.new()
			voice.stream = load(layer.stream)
			holder.add_child(voice)
			list.append([voice, layer])
		voices[cue] = list


func _play(cue: StringName, pitch := 1.0) -> void:
	for pair in voices.get(cue, []):
		pair[0].pitch_scale = pair[1].pitch * pitch
		pair[0].volume_db = pair[1].volume_db
		pair[0].play()


func _hum(on: bool) -> void:
	humming = on
	for pair in voices.get(&"hum", []):
		if on:
			pair[0].play()
		else:
			pair[0].stop()
	_hum_level()


func _hum_level() -> void:
	var share := clampf(bars / float(Layout.BARS - 1), 0.0, 1.0)
	for pair in voices.get(&"hum", []):
		pair[0].pitch_scale = lerpf(pair[1].pitch, pair[1].to_pitch, share)
		pair[0].volume_db = lerpf(pair[1].volume_db, pair[1].to_db, share)


func _beam_sounds(on: bool) -> void:
	roaring = on
	crackling = on and result == &"won"
	shattered = false
	roar_left = 0.0
	crackle_left = 0.0


func _step_sounds(delta: float) -> void:
	if humming:
		for pair in voices.get(&"hum", []):
			if not pair[0].playing:
				pair[0].play()
	if roaring:
		roar_left -= delta
		if roar_left <= 0.0:
			roar_left = Layout.ROAR_EVERY
			_play(&"roar")
	if crackling:
		crackle_left -= delta
		if crackle_left <= 0.0:
			crackle_left = Layout.CRACKLE_EVERY
			_play(&"crackle")
		if not shattered and is_instance_valid(fx) and fx.progress >= Layout.SHATTER_AT:
			shattered = true
			_play(&"shatter")


func _duck_music() -> void:
	var music: AudioStreamPlayer = god.music
	if not music_saved:
		music_db = music.volume_db
		music_saved = true
	_kill_music_tween()
	music_tween = music.create_tween()
	music_tween.tween_property(music, "volume_db", music_db + Layout.MUSIC_DUCK_DB, Layout.MUSIC_DUCK_TIME)


# Back to its level over `seconds`; release() sets it exactly.
func _restore_music(seconds: float) -> void:
	if not music_saved:
		return
	_kill_music_tween()
	if seconds <= 0.0:
		god.music.volume_db = music_db
		return
	music_tween = god.music.create_tween()
	music_tween.tween_property(god.music, "volume_db", music_db, seconds)


func _kill_music_tween() -> void:
	if music_tween != null and music_tween.is_valid():
		music_tween.kill()


#WAITS AND THE END

func _player() -> CharacterBody2D:
	if not is_inside_tree():
		return null
	var scene := get_tree().current_scene
	return scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null


func _unlock() -> void:
	var p := _player()
	if p != null and player_held:
		p.unlock_actions()
	player_held = false


# `seconds` on this state's own clock: a node-bound tween, in `waits` for release() to run out.
func _wait(seconds: float) -> void:
	if released or not is_inside_tree():
		return
	var tween := create_tween()
	tween.tween_interval(maxf(seconds, 0.0))
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


# The same in real seconds, for what plays out inside a hit-stop.
func _wait_real(seconds: float) -> void:
	if released or not is_inside_tree():
		return
	var tween := create_tween().set_ignore_time_scale(true)
	tween.tween_interval(maxf(seconds, 0.0))
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _stale(run_of: int) -> bool:
	return released or run_of != generation


func release() -> void:
	if released:
		return
	released = true
	generation += 1
	mashing = false
	camera_on = false
	humming = false
	roaring = false
	crackling = false
	rumble_px = 0.0
	while not waits.is_empty():
		var tween: Tween = waits.pop_back()
		if tween.is_valid():
			tween.custom_step(3600.0)
	for list in voices.values():
		for pair in list:
			if is_instance_valid(pair[0]):
				pair[0].stop()
	if is_instance_valid(fx):
		if result != &"won":
			fx.restore_god()
		fx.reveal_player()
		fx.queue_free()
	fx = null
	if is_instance_valid(ui):
		ui.queue_free()
	ui = null
	_end_shout()
	_unlock()
	var p := _player()
	if p != null:
		p.sprite.visible = true
		p.clear_face_point()
	if music_saved and is_instance_valid(god):
		_kill_music_tween()
		god.music.volume_db = music_db
	music_saved = false
	HitStop.clear()
	if is_inside_tree():
		ScreenView.reset(get_tree())
