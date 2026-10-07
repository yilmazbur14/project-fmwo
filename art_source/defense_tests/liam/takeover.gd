extends RefCounted

# liam_takeover: his takeover (LiamTakeover) in the real fight, Bixby beaten and Liam coughed up.
#   hand-over  Bixby out of the boss group and boss_target, no outro, and LiamScene in the arena
#   watched    every line read the way a player reads it: his lines and Burak's "ew." verbatim, tags stripped; the
#              beats in order (the swap and his getting up, the laugh, the staff, the pillar, the ride); his sprite
#              swapped in exactly where frame 9 drew him; the dog hopping off the screen; his talk gestures while his
#              lines type; then the end state, and his first attack 1.0 s later
#   paused     the pause screen holds the cut where it is
#   held       a hold mid-way through every beat and every line lands on the same end state
# The end state (plan section 2): Liam on his parked pillar at PERCH, 150 up, on perch_idle facing down the screen; the
# pillar solid, shielded and the only boss target; the row up and solid either side of it (it rises inside the ride),
# the player's box top at its face + 2 or below; his bar full at 0.30 and Bixby's gone; the beast hidden and the dog
# gone; the player free, clear of the pillar's footprint; his theme started once; no balloon, the view level, nothing
# in his hazard group.

const Layout := preload("res://Scripts/LiamArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BIXBY := "Arena/BixbyBeastScene/BixbyBeastCharacterBody"
const BODY := "Arena/LiamScene/LiamCharacterBody"
const LINES := [
	"*cough* *hack*... Ugh. Thanks for getting me out of there, newcomer. I owe you one.",
	"But don't get too excited. Bixby's my student... and the only element he ever mastered was fire.",
	"Me? I've mastered all four. Water. Earth. Fire. Air.",
	"This fight just got a whole lot harder.",
	"Nyahahahaha!",
	"Kept it somewhere safe.",
	"ew.",
]
const BEATS := [&"liam_gets_up", &"anime_laugh", &"staff_from_mouth", &"earth_pillar", &"ride_to_the_top"]
# Well past the 0.4 s hold.
const HOLD_FRAMES := 90
# A line is tapped every this many frames it is up, never on the frame it comes up.
const TAP_EVERY := 8


static func run(t) -> void:
	await watched(t)
	await paused(t)
	for point in BEATS:
		await held(t, point)
	for k in LINES.size():
		await held(t, "line%d" % k)


# Bixby's fight on and Bixby beaten where `at` puts him, if given: [Bixby, Liam, the takeover] once its cut is up, or
# nothing.
static func into_takeover(t, at := Vector2.INF) -> Array:
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	t.fight = "liam"
	await t.load_fight("liam", true)
	await t.clear_intro("liam")
	await t.wait_until(func(): return t.vs_card() != null and t.vs_card().is_playing(), t.VS_CARD_WAIT_FRAMES)
	await t.skip_vs_card()
	await t.wait(10)
	var bixby: Node = t.current_scene.get_node(BIXBY)
	if not ("liam_follows" in bixby) or not bixby.liam_follows:
		t.check(false, "Bixby hands over to Liam (liam_follows)")
		return []
	var sm: Node = bixby.state_machine
	sm.on_child_transition(sm.current_state, "Idle")
	for timer in bixby.find_children("*", "Timer", true, false):
		timer.stop()
	if at != Vector2.INF:
		bixby.height = 0.0
		bixby.ground_position = at
		bixby.place()
	bixby._apply_damage(bixby.boss_health)
	var handed: bool = await t.wait_until(func(): return t.current_scene.get_node_or_null(BODY) != null, 240)
	var body: Node = t.current_scene.get_node_or_null(BODY)
	t.check(handed and not bixby.is_in_group("fight_boss") and not bixby.hurtbox.is_in_group("boss_target") and not t.root.has_node("FightOutro"),
		"Bixby beaten: out of the boss group and boss_target, LiamScene in, and no outro")
	if body == null:
		return []
	var takeover: Node = body.state_machine.states["Takeover"]
	var cut_up: bool = await t.wait_until(func(): return takeover.cut != null, 240)
	t.check(cut_up, "the KO beat, then the cut")
	if not cut_up:
		return []
	t.player.playerHealth = 1000
	return [bixby, body, takeover]


static func watched(t) -> void:
	t.log_p("-- watched through")
	var parts: Array = await into_takeover(t)
	if parts.is_empty():
		return
	var bixby: Node = parts[0]
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var lines: Array[String] = []
	var anims_by_line := {}
	var beat_order := []
	var swap_gap := Vector2.INF
	var dog_left := false
	var last_line: Object = null
	var line_age := 0
	for i in 60 * 60:
		if takeover.finished:
			break
		var balloon: Node = t.live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			lines.append(balloon.dialogue_line.text)
			line_age = 0
		var index := lines.size() - 1
		if not anims_by_line.has(index):
			anims_by_line[index] = {}
		anims_by_line[index][body.current_anim] = true
		for beat in takeover.beat_times:
			if not beat_order.has(beat):
				beat_order.append(beat)
		if swap_gap == Vector2.INF and body.air.visible and body.current_anim == &"slimed_sit":
			swap_gap = body.global_position - Layout.liam_handover(bixby.air.global_position)
		if is_instance_valid(takeover.dog) and (takeover.dog.global_position.x < -60.0 or takeover.dog.global_position.x > 1980.0):
			dog_left = true
		# A line types out to its end before a tap moves on.
		if balloon != null and not balloon.dialogue_label.is_typing and line_age % TAP_EVERY == TAP_EVERY - 1:
			t.tap(KEY_ENTER)
		line_age += 1
		await t.physics_frame
	# The last beat's end and the cut's come on the same frame.
	beat_order = takeover.beat_times.keys()
	t.log_p("lines %d, beats %s in %s" % [lines.size(), beat_order, takeover.beat_times])
	t.check(lines == LINES, "his lines and Burak's, verbatim and tags stripped (%s)" % [lines])
	t.check(beat_order == BEATS, "the beats in order")
	t.check(swap_gap == Vector2.ZERO, "his sprite swapped in on frame 9's feet (%s)" % swap_gap)
	t.check(dog_left, "the dog hopped off the screen")
	var talked: bool = anims_by_line.get(0, {}).has(&"talk_thanks") and anims_by_line.get(1, {}).has(&"talk_explain") \
		and anims_by_line.get(2, {}).has(&"talk_elements") and anims_by_line.get(3, {}).has(&"talk_smug") \
		and anims_by_line.get(4, {}).has(&"laugh") and anims_by_line.get(5, {}).has(&"talk_staff")
	t.check(talked, "each line's gesture as it types (%s)" % [anims_by_line.values().map(func(a): return a.keys())])
	# On the frame it ends, before his wind's reset has done anything: the reset goes straight on for a player already
	# on its spot.
	var diffs := end_state_diffs(t, bixby, body, takeover)
	t.check(diffs.is_empty(), "the end state (%s)" % ", ".join(diffs))
	var sm: Node = body.state_machine
	var reset: bool = await t.wait_until(func(): return String(sm.current_state.name) == "RoundBlast", 30)
	var skipped: bool = reset and sm.current_state.skip
	var attacking: bool = await t.wait_until(func(): return String(sm.current_state.name) == "Tsunami", 60 * 3)
	var landed: Vector2 = t.player.global_position
	t.log_p("then %s (skipped %s), the player at %s, then %s" % ["his wind's reset" if reset else "no reset", skipped, landed, sm.current_state.name])
	t.check(reset and attacking and landed.distance_to(sm.RESET_SPOT) <= (sm.launch_skip if skipped else 1.0), "then his wind's reset to %s and the Tsunami" % sm.RESET_SPOT)


static func paused(t) -> void:
	t.log_p("-- the pause screen holds it")
	var parts: Array = await into_takeover(t)
	if parts.is_empty():
		return
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	await read_until(t, func() -> bool: return body.current_anim == &"laugh", 60 * 30)
	var pause: Node = t.pause_menu()
	await t.tap_pause()
	var clock_at: float = body.fight_clock
	var step_at: int = body.anim_step
	var waits_at: int = takeover.waits.size()
	await t.wait(90)
	var held_still: bool = t.paused and body.fight_clock == clock_at and body.anim_step == step_at and takeover.waits.size() == waits_at and not takeover.finished
	await t.tap_pause()
	await t.wait(20)
	t.check(held_still, "90 paused frames: nothing of the cut moved")
	t.check(not t.paused and body.fight_clock > clock_at, "and it goes on once the pause is closed")
	t.press(KEY_ESCAPE)
	await t.wait_until(func(): return takeover.finished, HOLD_FRAMES)
	t.release(KEY_ESCAPE)
	await t.wait(10)


static func held(t, point: String) -> void:
	t.log_p("-- held mid-%s" % point)
	var parts: Array = await into_takeover(t)
	if parts.is_empty():
		return
	var bixby: Node = parts[0]
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var reached := func() -> bool: return at_point(t, point, body, takeover)
	await read_until(t, func() -> bool: return takeover.finished or reached.call(), 60 * 40)
	t.check(reached.call() and not takeover.finished, "reached mid-%s (on %s)" % [point, body.current_anim])
	t.press(KEY_ESCAPE)
	var skipped: bool = await t.wait_until(func(): return takeover.finished, HOLD_FRAMES)
	t.release(KEY_ESCAPE)
	t.check(skipped, "the hold skips it")
	# Held there: his wind's reset and attack 1 would otherwise start on it.
	var sm: Node = body.state_machine
	sm.states["Idle"].beat_left = -1.0
	sm.on_child_transition(sm.current_state, "Idle")
	await t.wait(20)
	var diffs := end_state_diffs(t, bixby, body, takeover)
	t.check(diffs.is_empty(), "the end state (%s)" % ", ".join(diffs))


# Mid-beat: running, a few frames in. Mid-line: that line up and still typing.
static func at_point(t, point: String, body: Node, takeover: Node) -> bool:
	if point.begins_with("line"):
		var k := int(point.substr(4))
		var balloon: Node = t.live_balloon()
		return balloon != null and balloon.dialogue_line != null and balloon.dialogue_line.text == LINES[k] \
			and balloon.dialogue_label.is_typing
	match point:
		"liam_gets_up":
			return takeover.beat_running and body.air.visible and body.current_anim in [&"get_up", &"wipe"]
		"anime_laugh":
			return takeover.beat_running and body.current_anim == &"laugh"
		"staff_from_mouth":
			return takeover.beat_running and body.current_anim == &"staff_pull" and body.anim_step >= 1
		"earth_pillar":
			return takeover.beat_running and body.pillar.standing and body.pillar.risen > 0.2 and body.pillar.risen < 0.8
		"ride_to_the_top":
			return takeover.beat_running and body.current_anim == &"ride" and body.pillar.global_position.distance_to(body.state_machine.PERCH) > 20.0
	return false


# Reads whatever lines come up, the way a player does, until `done` says so.
static func read_until(t, done: Callable, max_frames: int) -> void:
	var last_line: Object = null
	var line_age := 0
	for i in max_frames:
		if done.call():
			return
		var balloon: Node = t.live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			line_age = 0
		if balloon != null and line_age % TAP_EVERY == TAP_EVERY - 1 and line_age > 3 * TAP_EVERY:
			t.tap(KEY_ENTER)
		line_age += 1
		await t.physics_frame


# Everything the end state isn't, in words: empty when it is exactly the end state.
static func end_state_diffs(t, bixby: Node, body: Node, takeover: Node) -> Array[String]:
	var sm: Node = body.state_machine
	var pillar: Node = body.pillar
	var diffs: Array[String] = []
	if body.global_position != sm.PERCH or body.height != Layout.STAND_HEIGHT or body.air.position.y != -Layout.STAND_HEIGHT:
		diffs.append("Liam at %s, %.0f up" % [body.global_position, body.height])
	if body.current_anim != &"perch_idle" or body.facing_left or not body.air.visible:
		diffs.append("on %s, facing left %s, shown %s" % [body.current_anim, body.facing_left, body.air.visible])
	if pillar.global_position != sm.PERCH or not pillar.parked or pillar.body_shape.disabled or not pillar.shielded or pillar.risen != 1.0:
		diffs.append("the pillar at %s, parked %s, solid %s, shielded %s" % [pillar.global_position, pillar.parked, not pillar.body_shape.disabled, pillar.shielded])
	var row: Node = body.row
	if not row.is_up() or row.body_shape.disabled or row.risen.any(func(up_by): return up_by < 1.0):
		diffs.append("the row not all up and solid")
	var shape: CollisionShape2D = t.player.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	if box.position.y < row.band().end.y + Layout.ROW_NUDGE_GAP - 0.5:
		diffs.append("the player's box top at %.1f, in or behind the row" % box.position.y)
	var targets: Array = t.get_nodes_in_group("boss_target")
	if targets != [pillar.hurtbox]:
		diffs.append("the targets are %s" % [targets.map(func(a): return a.get_parent().name)])
	var bosses: Array = t.get_nodes_in_group("fight_boss")
	if bosses != [body]:
		diffs.append("the boss group is %s" % [bosses])
	if body.health_bar == null or not is_equal_approx(body.health_bar.rows[0].value, body.max_health) or not is_equal_approx(body.hud_alpha(), sm.pillar_hud_fade_alpha):
		diffs.append("his bar not full at %.2f" % sm.pillar_hud_fade_alpha)
	if bixby.hud_layer.visible or bixby.air.visible or bixby.shadow.visible:
		diffs.append("Bixby still shown (bar %s, beast %s)" % [bixby.hud_layer.visible, bixby.air.visible])
	if is_instance_valid(takeover.dog):
		diffs.append("the dog still there")
	if t.player.is_talking or t.player.is_action_locked or Rect2(t.area_rect(t.player.hurtBox)).intersects(pillar.footprint()):
		diffs.append("the player held or in the pillar")
	if body.music_starts != 1 or not body.music_player.playing:
		diffs.append("his theme started %d times, playing %s" % [body.music_starts, body.music_player.playing])
	if t.live_balloon() != null:
		diffs.append("a balloon up")
	if ScreenView.zoom != 1.0 or ScreenView.shake_offset != Vector2.ZERO:
		diffs.append("the view not level")
	if not t.get_nodes_in_group(sm.HAZARD_GROUP).is_empty():
		diffs.append("hazards left")
	if not String(sm.current_state.name) in ["Idle", "RoundBlast", "Tsunami"]:
		diffs.append("in %s" % sm.current_state.name)
	return diffs
