extends State

# The base of every combination attack in Jordan's last phase, the Puppet Master: he raises two of the bosses he erased
# as marionettes (JordanPuppet), one on each hand, and works them together, and the attack ends on its uppercut into one
# of them, the damage running up the strings into him. A subclass overrides pair() - the two puppets, where they stand,
# which hand works each - and run(), the attack, which awaits the pieces here and calls finish() at its end. His state
# machine builds one of each in code, off JordanGodLayout.COMBOS, and takes them in turn.
#
# THE FROZEN CONTRACT (the build plan's section 2): god, state_machine, puppets, cut; pair(), run(), summon(), recall(),
# warp_player(), hud(), darken(), lift_above_dark(), arrow(), hide_arrow(), punch_out(), hint(), hide_hint(), wait(),
# add_hazard(), player(), finish(), release(). The rest is its own.
#
# TWO AT ONCE: exactly two puppets an attack, one a hand. Only one player lock at a time, the combo's; no two red or
# yellow tells overlapping; and one release() owns everything both puppets made.
#
# RELEASE: whichever way an attack ends - finish(), the player's death, Jordan's defeat, the scene going (Exit(),
# _exit_tree(), his on_player_defeated() and _on_defeated()) - release() puts back everything it touched: the lock, the
# pose and the facing point, what it lifted over the dark and the player's z among them, the darkness, the HUD's alpha,
# the puppets and their strings (unless his defeat has taken them to play out: adopt_puppets()), the rifts, every node
# in the hazard group, the hint, the arrow, and the waits. It is idempotent.
#
# WAITS: every wait is a node-bound tween in `waits` (wait()), so a finisher's freeze and the pause hold it; release()
# runs them out, and a subclass bails on `cut` after every await. Never create_timer() or a tree tween.

const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const PuppetLayout := preload("res://Scripts/JordanPuppetLayout.gd")
const JordanPuppet := preload("res://Scripts/JordanPuppet.gd")
const JordanRift := preload("res://Scripts/JordanRift.gd")
const JordanArrowBadge := preload("res://Scripts/JordanArrowBadge.gd")
const PunchComboArtLayout := preload("res://Scripts/PunchComboArtLayout.gd")
const FightOutro := preload("res://Scripts/FightOutro.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")

# PlayerScript.Facing's order.
const FACINGS: Array[Vector2] = [Vector2.DOWN, Vector2.UP, Vector2.LEFT, Vector2.RIGHT]

var god: Node2D
var state_machine: Node
# The puppets up, by their JordanPuppetLayout key.
var puppets := {}
var cut := false
var waits: Array[Tween] = []
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var rifts: Array[Node2D] = []
# [item, its own z_index before lift_above_dark()].
var lifted: Array = []
var player_held := false
var arrow_badge: Node2D
var hint_node: Node2D
var dark_fade: Tween
# The punch-out under way: the puppet, the presses so far and when the last one counted, on this state's own clock.
var punch_target: Node2D
var punching := false
var punch_presses := 0
var last_press_at := -INF
var clock := 0.0
var pose_back: Tween
# The punch-out's finisher, waiting on its payoff: -1 until it comes.
var payoff_bars := -1


func Enter() -> void:
	cut = false
	released = false
	player_held = false
	punching = false
	punch_presses = 0
	payoff_bars = -1
	clock = 0.0
	run()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func _process(delta: float) -> void:
	clock += delta


#WHAT A SUBCLASS OVERRIDES

# The two puppets: [{boss, feet, face_left, hand, hooks: [&"back"], strings: 2}, {...}]. `feet` are screen px, `hand`
# &"left" or &"right" (screen-left and -right), `face_left` whether it faces screen-left.
func pair() -> Array[Dictionary]:
	return []


# The attack. It awaits the pieces below, bails on `cut` after every await, and calls finish() at its end.
func run() -> void:
	finish()


#THE PUPPETS

# Jordan's summon: his hands dip as a rift cracks open under each puppet's feet and the strings are cast down into
# it, then the yank, and each puppet rises through its rift, clipped at the floor line, and settles on its strings.
# Awaitable; the puppets are in `puppets` from its start.
func summon() -> void:
	if cut:
		return
	var entries := pair()
	var beats: Dictionary = GodLayout.summon_beats(god.final_puppeteer)
	god.play(&"summon", &"control")
	god.play_sound(&"summon")
	var raised: Array = []
	for entry in entries:
		var puppet = JordanPuppet.make(entry.boss, entry.feet, entry.get("face_left", false), god)
		god.layer(&"stage").add_child(puppet)
		puppet.hide_under_floor()
		puppet.play(puppet.spec.limp)
		puppets[puppet.boss] = puppet
		raised.append([puppet, entry])
	await wait(beats.rift)
	if cut:
		return
	god.play_sound(&"rift")
	for up in raised:
		_open_rift(up[0], &"summon")
	await wait(beats.strings - beats.rift)
	if cut:
		return
	var strings: Node2D = god.layer(&"strings")
	for i in raised.size():
		var entry: Dictionary = raised[i][1]
		strings.attach(raised[i][0], entry.get("hand", &"left" if i == 0 else &"right"), entry.get("hooks", [&"back"]),
			entry.get("strings", 2))
	await wait(beats.rise - beats.strings)
	if cut:
		return
	god.play_sound(&"yank")
	for up in raised:
		strings.set_tension(up[0], GodLayout.TENSION_YANK, 0.0)
		up[0].rise(beats.rise_time)
	await wait(beats.rise_time)
	if cut:
		return
	var closing := 0.0
	for up in raised:
		up[0].play(up[0].spec.idle)
		strings.set_tension(up[0], GodLayout.TENSION_WORK, GodLayout.SETTLE_TIME)
	for rift in rifts:
		if is_instance_valid(rift):
			closing = maxf(closing, rift.close())
	rifts.clear()
	await wait(maxf(GodLayout.SETTLE_TIME, closing))


# The summon backwards: a rift opens under each puppet, it sinks back into it on its slackening strings, and it is gone.
# Awaitable.
func recall() -> void:
	if cut:
		return
	var beats: Dictionary = GodLayout.summon_beats(god.final_puppeteer)
	var strings: Node2D = god.layer(&"strings")
	god.play(&"summon", &"control")
	god.play_sound(&"rift")
	for puppet in puppets.values():
		if not is_instance_valid(puppet):
			continue
		puppet.set_punchable(false)
		puppet.play(puppet.spec.limp)
		strings.set_tension(puppet, GodLayout.TENSION_LIMP)
		_open_rift(puppet, &"despawn")
	await wait(beats.rise)
	if cut:
		return
	for puppet in puppets.values():
		if is_instance_valid(puppet):
			puppet.sink(GodLayout.RECALL_SINK)
	await wait(GodLayout.RECALL_SINK)
	if cut:
		return
	var closing := 0.0
	for puppet in puppets.values():
		if is_instance_valid(puppet):
			strings.detach(puppet)
			puppet.queue_free()
	puppets.clear()
	for rift in rifts:
		if is_instance_valid(rift):
			closing = maxf(closing, rift.close())
	rifts.clear()
	await wait(closing)


func _open_rift(puppet: Node2D, sequence: StringName) -> void:
	var rift := JordanRift.new()
	rift.name = "Rift_%s" % puppet.boss
	rift.setup(puppet.spec.rift, PuppetLayout.rift_radius(puppet.boss), god.layer(&"stage"))
	var floor_layer: Node2D = god.layer(&"floor")
	rift.position = floor_layer.to_local(puppet.global_position)
	floor_layer.add_child(rift)
	rift.open(sequence)
	rifts.append(rift)


# Hands every puppet over to his defeat (JordanGodDefeated plays them out): release() leaves them and their strings.
func adopt_puppets() -> Array:
	var out: Array = puppets.values().filter(func(puppet) -> bool: return is_instance_valid(puppet))
	puppets.clear()
	return out


#THE PLAYER

# Sealed, blinked to `soles` (warp_to), turned to `facing` (PlayerScript.Facing) and stood in the base pose.
func warp_player(soles: Vector2, facing: int) -> void:
	var p := player()
	if p == null or cut:
		return
	_seal(p)
	p.warp_to(soles - Vector2(0.0, GodLayout.SOLES_BELOW_ORIGIN))
	p.face_point(p.global_position + FACINGS[clampi(facing, 0, FACINGS.size() - 1)] * 100.0)
	_base_pose(p)


func _seal(p: CharacterBody2D) -> void:
	if not p.is_action_locked:
		p.lock_actions_sealed()
	player_held = true


func _base_pose(p: CharacterBody2D) -> void:
	if p.hold_pose(GodLayout.PLAYER_SHEET):
		p.play_pose(GodLayout.BASE_POSE.frames, GodLayout.BASE_POSE.times, GodLayout.BASE_POSE.loop)


func player() -> CharacterBody2D:
	if not is_inside_tree():
		return null
	var scene := get_tree().current_scene
	return scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null


#THE SCREEN

func hud(on: bool) -> void:
	god.set_hud(on, GodLayout.HUD_FADE)


# Pitch black over everything under it (the Dark layer), or back again.
func darken(on: bool, seconds := GodLayout.DARK_TIME) -> void:
	var dark: CanvasItem = god.darkness
	if dark_fade != null and dark_fade.is_valid():
		dark_fade.kill()
	if on:
		dark.visible = true
	dark_fade = dark.create_tween()
	dark_fade.tween_property(dark, "modulate:a", 1.0 if on else 0.0, maxf(seconds, 0.001))
	if not on:
		dark_fade.tween_callback(dark.hide)


# Over the darkness, keeping the layers' order (JordanGodLayout.LIFT_Z); release() puts it back.
func lift_above_dark(item: CanvasItem) -> void:
	if item == null or lifted.any(func(entry: Array) -> bool: return entry[0] == item):
		return
	lifted.append([item, item.z_index])
	item.z_index += GodLayout.LIFT_Z


# The arrow over the player: `dir` &"up", &"right", &"down" or &"left", `state` &"live", &"answered" or &"cracked".
func arrow(dir: StringName, state := &"live") -> void:
	if cut:
		return
	if not is_instance_valid(arrow_badge):
		arrow_badge = JordanArrowBadge.new()
		arrow_badge.name = "ArrowBadge"
		arrow_badge.player = player()
		god.layer(&"fx").add_child(arrow_badge)
	arrow_badge.show_arrow(dir, state)


func hide_arrow() -> void:
	if is_instance_valid(arrow_badge):
		arrow_badge.visible = false


# A line under the player, in the Glass Row hint's style, until hide_hint(); drawn 1.5x so it reads at its own size in
# the fight's 2/3 view (JordanGodLayout.ui_scale).
func hint(text: String) -> void:
	if cut:
		return
	hide_hint()
	var spec: Dictionary = GodLayout.HINT
	hint_node = Node2D.new()
	hint_node.name = "Hint"
	var label := Label.new()
	label.theme = UI_THEME
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_constant_override("outline_size", spec.outline)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", spec.outline_color)
	label.size = Vector2(spec.width, spec.font_size * 2)
	label.position = Vector2(-spec.width / 2.0, 0.0)
	hint_node.add_child(label)
	hint_node.modulate.a = 0.0
	hint_node.scale = Vector2.ONE * GodLayout.ui_scale()
	god.layer(&"fx").add_child(hint_node)
	_follow_hint()
	hint_node.create_tween().tween_property(hint_node, "modulate:a", 1.0, spec.fade)


func hide_hint() -> void:
	if not is_instance_valid(hint_node):
		return
	var gone := hint_node
	hint_node = null
	var fade := gone.create_tween()
	fade.tween_property(gone, "modulate:a", 0.0, GodLayout.HINT.fade)
	fade.tween_callback(gone.queue_free)


func _physics_process(_delta: float) -> void:
	_follow_hint()


func _follow_hint() -> void:
	var p := player()
	if is_instance_valid(hint_node) and p != null:
		hint_node.global_position = (p.global_position + GodLayout.HINT.offset).round()


# Put in the arena, in the hazard group release() and his defeat empty.
func add_hazard(node: Node2D, at: Vector2, on: Node2D) -> void:
	node.add_to_group(GodLayout.HAZARD_GROUP)
	node.position = on.to_local(at.round())
	on.add_child(node)


#THE PUNCH-OUT

# The player takes `puppet` apart: sealed and turned to it, three punch presses at least PUNCH_GAP apart - hit 1, the
# other hand, the body blow, each flinching it - then FINISHER_DELAY and the finisher on it, tiered: the three-bar mash
# and its juggle, every uppercut one off Jordan. Awaitable; the bars that landed, 0 for none (a fizzle or a whiff).
func punch_out(puppet: Node2D) -> int:
	var p := player()
	if cut or p == null or not is_instance_valid(puppet):
		return 0
	_seal(p)
	p.face_point(puppet.get_finisher_hurtbox().get_node("CollisionShape2D").global_position)
	_base_pose(p)
	puppet.set_punchable(true)
	punch_target = puppet
	punch_presses = 0
	last_press_at = -INF
	punching = true
	while punch_presses < GodLayout.PUNCH_OUT_PRESSES:
		await wait(0.0)
		if cut:
			return 0
	punching = false
	await wait(GodLayout.FINISHER_DELAY)
	if cut or not is_instance_valid(puppet):
		return 0
	_kill_pose_back()
	payoff_bars = -1
	puppet.payoff_done.connect(_on_payoff_done, CONNECT_ONE_SHOT)
	puppet.open_for_uppercut()
	if not p.finisher.begin(puppet):
		if puppet.payoff_done.is_connected(_on_payoff_done):
			puppet.payoff_done.disconnect(_on_payoff_done)
		return 0
	while payoff_bars < 0:
		await wait(0.0)
		if cut:
			return 0
	return payoff_bars


func _on_payoff_done(bars: int) -> void:
	payoff_bars = bars


func _input(event: InputEvent) -> void:
	if not punching or released or not event.is_action_pressed(&"punch"):
		return
	if clock - last_press_at < GodLayout.PUNCH_GAP or not is_instance_valid(punch_target):
		return
	last_press_at = clock
	punch_presses += 1
	_throw_punch(punch_presses)
	punch_target.flinch()


# Hit 1 off the player's own sheet, hits 2 and 3 off the combo sheet (when it is on and in), in the facing's row; then
# back to the base pose once the swing is over.
func _throw_punch(hit: int) -> void:
	var p := player()
	if p == null:
		return
	var swing := _swing_frames(p)
	var sheet: Dictionary = GodLayout.PLAYER_SHEET
	var frames: Array = swing.frames
	if hit > 1 and PunchComboArtLayout.COMBO_ANIMS_ENABLED and ResourceLoader.exists(PunchComboArtLayout.SHEET):
		sheet = GodLayout.COMBO_SHEET
		var first: int = PunchComboArtLayout.FIRST_COLUMNS[PunchComboArtLayout.OTHER_HAND if hit == 2 else PunchComboArtLayout.BODY_BLOW]
		frames = []
		for k in swing.frames.size():
			frames.append(first + k)
	if not p.hold_pose(sheet):
		return
	p.play_pose(frames, swing.times, false)
	_kill_pose_back()
	var length := 0.0
	for time in swing.times:
		length += float(time)
	pose_back = create_tween()
	pose_back.tween_interval(length)
	pose_back.tween_callback(_base_pose.bind(p))


# MainPlayer's own punch: its columns and seconds, off its AnimationPlayer at the speed PlayerPunching plays it.
func _swing_frames(p: CharacterBody2D) -> Dictionary:
	var animation: Animation = p.animation_player.get_animation(GodLayout.PUNCH_ANIM)
	var track := animation.find_track(^"Sprite2D:frame_coords:x", Animation.TYPE_VALUE)
	var frames: Array = []
	var times: Array = []
	var count := animation.track_get_key_count(track)
	for k in count:
		frames.append(int(animation.track_get_key_value(track, k)))
		var start := animation.track_get_key_time(track, k)
		var end := animation.track_get_key_time(track, k + 1) if k + 1 < count else animation.length
		times.append((end - start) / GodLayout.PUNCH_SPEED)
	return {frames = frames, times = times}


func _kill_pose_back() -> void:
	if pose_back != null and pose_back.is_valid():
		pose_back.kill()
	pose_back = null


#WAITS AND THE END

# `seconds` on this state's own clock: a node-bound tween, in `waits` for release() to run out. Bail on `cut` after it.
func wait(seconds: float) -> void:
	if cut or not is_inside_tree():
		return
	var tween := create_tween()
	tween.tween_interval(maxf(seconds, 0.0))
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


# The attack is over: back to his Idle, which release()s it on the way out.
func finish() -> void:
	if released:
		return
	state_machine.on_child_transition(self, "Idle")


func release() -> void:
	if released:
		return
	released = true
	cut = true
	punching = false
	_kill_pose_back()
	while not waits.is_empty():
		var tween: Tween = waits.pop_back()
		if tween.is_valid():
			tween.custom_step(3600.0)
	var p := player()
	if p != null and player_held:
		p.unlock_actions()
	player_held = false
	for i in range(lifted.size() - 1, -1, -1):
		var item: CanvasItem = lifted[i][0]
		if is_instance_valid(item):
			item.z_index = lifted[i][1]
	lifted.clear()
	if dark_fade != null and dark_fade.is_valid():
		dark_fade.kill()
	if is_instance_valid(god):
		if is_instance_valid(god.darkness):
			god.darkness.modulate.a = 0.0
			god.darkness.visible = false
		god.set_hud(true, 0.0)
		var strings: Node2D = god.layer(&"strings")
		for puppet in puppets.values():
			if is_instance_valid(strings):
				strings.detach(puppet)
			if is_instance_valid(puppet):
				puppet.queue_free()
	puppets.clear()
	for rift in rifts:
		if is_instance_valid(rift):
			rift.queue_free()
	rifts.clear()
	if is_instance_valid(arrow_badge):
		arrow_badge.queue_free()
	arrow_badge = null
	if is_instance_valid(hint_node):
		hint_node.queue_free()
	hint_node = null
	if is_inside_tree():
		for hazard in get_tree().get_nodes_in_group(GodLayout.HAZARD_GROUP):
			hazard.queue_free()
	punch_target = null
	payoff_bars = 0
