extends RefCounted

# jordan_god (coder F): Jordan's last phase, the Puppet Master - the framework and the fight shell (the build plan's
# sections 1, 2 and 9). --max-fps 60, since the mash and the balloon's and the card's input locks are real time. The
# attacks are the stub combo (jordan/stub_combo.gd, JordanGodLayout.COMBOS pointed at it) or none at all. tier=
#   open      the ring art hidden and the void drawn in screen space under the world; the first frame framed as the
#             finale's last (the view at 1), then a smooth, plain pull-back to 2/3 on (960, 804); the bar see-through
#             over him (Open's reveal 1 x HUD_SEE_THROUGH_ALPHA), easing back to 1 with him hidden and see-through
#             again once he's back; the god at (960, 600), the player at (620, 761) facing UP, their floor the
#             staging's (JordanGodLayout.FLOOR); is_talking true through Open and false after it; his final theme
#             looping at -6 dB; the bar full (UPPERCUTS_TO_BEAT) and the HUD faded in; the pause screen opens and
#             fight_index is 9
#   handoff   with the switch on (JordanFinaleLayout.USE_GOD_FIGHT): the room's last line (on the intro's clock), a
#             hold in the room and a hold in the walk-out each land on the god fight, never the card, and its view
#             settles on the fight's 2/3 base once it has pulled back; with it off, a hold in the room lands on the
#             card as today
#   menu      the boss select's GOD row, inside the panel and the panel inside BOSS_SELECT_RECT, opens the fight
#             straight from the menu, no finale scene visited
#   rotation  COMBOS = [stub, a missing file, stub]: the missing one skipped, the two stubs taking turns through Idle
#   damage    the stub's punch-out: three presses and a three-bar mash, each take_juggle_hit exactly 1 off him and
#             his bar 3 lower; a supercharged three-bar mash spends the hype and takes 4, the last uppercut
#             one more (PlayerFinisher.uppercut_count); at 1 left one
#             uppercut: exactly one FightOutro (won), his defeat played out (strings snapped, puppets gone), then
#             the card and the menu
#   lost      his player_lost lines verbatim, his and in the demon portrait; the player at 0 health: the first in that
#             portrait and his voice, held until a press, then a press a line, all three shown, the third's press into
#             the Defeat screen reading #arena-10
#   release   the stub held mid-attack (sealed and posed, lights out, the player lifted over the dark, the HUD down,
#             an arrow, a hint, a hazard, both puppets on their strings), cut by the player's death and again by his
#             defeat: no lock, no Posed state, no darkness, no rifts or hazards, the player's z back and the HUD at
#             alpha 1 at once; no puppets or strings (on his defeat, once his defeat beat has played them out)
#   pairings  the concept pass's display pairings, Eric + Josh and Mason + Carter, through the stub: both rise and
#             hang on his hands with two strings each on their back hooks; the punch-out on the left one and a
#             one-bar mash: one uppercut, a juggle, exactly 1 off him and the payoff's 1 bar; then the recall leaves
#             no puppets, strings or rifts
#   normal    all of them in turn.

const GOD_SCENE := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const ROOM := "res://Scenes/Core/JordanFinaleScene.tscn"
const CARD := "res://Scenes/Core/ToBeContinuedScene.tscn"
const MENU := "res://Scenes/Core/MainMenuScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const GOD_PATH := "Arena/JordanGodScene/God"
const STAGE_PATH := "Arena/JordanGodScene/Stage"
const FLOOR_PATH := "Arena/JordanGodScene/Floor"
const STRINGS_PATH := "Arena/JordanGodScene/Strings"
const VOID_PATH := "Arena/JordanGodScene/Void"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const STUB := "res://art_source/defense_tests/jordan/stub_combo.gd"
const MISSING := "res://art_source/defense_tests/jordan/no_such_combo.gd"
const Layout := preload("res://Scripts/JordanGodLayout.gd")
const FinaleLayout := preload("res://Scripts/JordanFinaleLayout.gd")
const ChampionEndingLayout := preload("res://Scripts/ChampionEndingLayout.gd")
const Finale := preload("res://art_source/defense_tests/jordan/finale.gd")
const JordanPuppet := preload("res://Scripts/JordanPuppet.gd")
const JordanRift := preload("res://Scripts/JordanRift.gd")
const TIERS := ["open", "handoff", "menu", "rotation", "damage", "lost", "release", "pairings"]
const FINISHER_DAZED := 2
const FINISHER_CHARGING := 3
# The concept pass's two display pairings (art_source/jordan_puppets/concepts/notes.json, "mocks"): each on the hand
# and where the mock hangs it, in world px.
const PAIRINGS := [
	[{boss = &"eric", feet = Vector2(420, 1029), face_left = false, hand = &"left"},
		{boss = &"josh", feet = Vector2(1515, 1029), face_left = true, hand = &"right"}],
	[{boss = &"mason", feet = Vector2(480, 1029), face_left = false, hand = &"left"},
		{boss = &"carter", feet = Vector2(1470, 1029), face_left = true, hand = &"right"}],
]
const UP := 1
const HIT_SILENT := 2
const LAST_LINE := "Welcome to my world, Burak."
const LOST_LINES := ["Kneel, Burak. In my world you don't even get a role.", "Banned. Permanently. No appeals.",
	"...And I'm deleting all your messages."]
const DialogueVoices := preload("res://Scripts/DialogueVoices.gd")


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	var combos: Array[String] = Layout.COMBOS.duplicate()
	var god_fight: bool = FinaleLayout.USE_GOD_FIGHT
	var final_beam: bool = Layout.USE_FINAL_BEAM
	# His defeat's checks wait for TO BE CONTINUED and then the menu: the champion ending in its place is
	# champion_ending's to test.
	var champion_ending: bool = ChampionEndingLayout.USE_CHAMPION_ENDING
	ChampionEndingLayout.USE_CHAMPION_ENDING = false
	t.check(ChampionEndingLayout.after_jordan_god() == CARD, "with the champion ending off, his defeat goes to the card")
	for tier in tiers:
		t.log_p("-- jordan_god %s" % tier)
		# These two play his kill out as his defeat; jordan_final_beam covers the beam.
		Layout.USE_FINAL_BEAM = final_beam and tier != "damage" and tier != "release"
		match tier:
			"open":
				await tier_open(t)
			"handoff":
				await tier_handoff(t)
			"menu":
				await tier_menu(t)
			"rotation":
				await tier_rotation(t)
			"damage":
				await tier_damage(t)
			"lost":
				await tier_lost(t)
			"release":
				await tier_release(t)
			"pairings":
				await tier_pairings(t)
			_:
				t.check(false, "jordan_god has no tier %s" % tier)
	Layout.COMBOS = combos
	FinaleLayout.USE_GOD_FIGHT = god_fight
	Layout.USE_FINAL_BEAM = final_beam
	ChampionEndingLayout.USE_CHAMPION_ENDING = champion_ending


#GETTING THERE

# His last phase straight in, the way the GOD row opens it, with `combos` for its attacks and the stub on `mode`,
# summoning `pair` (Greyson and Matt when it is empty).
static func open_god(t, combos: Array[String], mode := &"quick", pair: Array[Dictionary] = []) -> Node:
	Layout.COMBOS = combos
	var stub: GDScript = load(STUB)
	stub.MODE = mode
	stub.PAIR = pair
	stub.runs = 0
	stub.reached = &""
	stub.bars = -1
	t.root.get_node("GameProgress").reset_progress()
	await t.open_scene(GOD_SCENE)
	await t.wait(2)
	t.player = t.current_scene.get_node(PLAYER_PATH)
	t.defense = t.player.get_node("Defense")
	return t.current_scene.get_node(GOD_PATH)


static func scene_is(t, path: String) -> bool:
	return t.current_scene != null and t.current_scene.scene_file_path == path


# Idle frames, not physics ones: a scene's first frame is long enough (his theme and sheets loading) for several physics
# steps to run inside it, and a Watch steps on process_frame.
static func idle_frames(t, count: int) -> void:
	for i in count:
		await t.process_frame


static func puppets_up(t) -> Array:
	var stage: Node = t.current_scene.get_node_or_null(STAGE_PATH) if t.current_scene else null
	if stage == null:
		return []
	return stage.get_children().filter(func(node: Node) -> bool:
		return node.get_script() == JordanPuppet and not node.is_queued_for_deletion())


static func rifts_up(t) -> Array:
	var floor_layer: Node = t.current_scene.get_node_or_null(FLOOR_PATH)
	var stage: Node = t.current_scene.get_node_or_null(STAGE_PATH)
	var rifts: Array = floor_layer.get_children().filter(func(node: Node) -> bool:
		return node.get_script() == JordanRift and not node.is_queued_for_deletion()) if floor_layer else []
	if stage:
		rifts.append_array(stage.get_children().filter(func(node: Node) -> bool:
			return node.name.begins_with("RiftFront") and not node.is_queued_for_deletion()))
	return rifts


static func hazards_up(t) -> Array:
	return t.get_nodes_in_group(Layout.HAZARD_GROUP).filter(func(node: Node) -> bool: return not node.is_queued_for_deletion())


#OPEN

static func tier_open(t) -> void:
	# The view on every idle frame of the fight's first two seconds, from its first, however soon the harness sees it.
	var seen := {"views": []}
	var sample := func():
		if scene_is(t, GOD_SCENE) and seen.views.size() < 120:
			seen.views.append(t.root.canvas_transform)
	t.process_frame.connect(sample)
	var god: Node = await open_god(t, [] as Array[String])
	var player: CharacterBody2D = t.player
	var arena: Node = t.current_scene.get_node("Arena")
	var ring_hidden := ["Ringside", "RingsideCrowd", "Sprite2D", "Mat", "ColorRect"].all(func(node_name: String) -> bool:
		return not arena.get_node(node_name).visible)
	var ropes: Array = arena.get_node("wallBoundaries").find_children("*", "Sprite2D", true, false)
	t.check(ring_hidden and not ropes.is_empty() and ropes.all(func(rope: CanvasItem) -> bool: return not rope.visible),
		"the ring art is hidden: the ringside, both crowds, the mat, the black backing and the %d rope and pole sprites" % ropes.size())
	var void_screen: CanvasLayer = t.current_scene.get_node_or_null(VOID_PATH + "/VoidScreen")
	var void_bg: CanvasItem = void_screen.get_node_or_null("VoidBg") if void_screen else null
	t.check(void_screen != null and void_screen.layer < 0 and void_bg != null and void_bg.visible and void_bg.position == Vector2.ZERO,
		"the void is drawn in screen space under the world, from the screen's corner (%s)" % [void_bg])
	var opening: Transform2D = seen.views[0] if not seen.views.is_empty() else Transform2D()
	t.log_p("the first frame's view: %s" % [opening])
	t.check(not seen.views.is_empty() and opening == Transform2D.IDENTITY,
		"it opens framed exactly as the finale's last frame: the view at 1, level (%.3f, %s)" % [opening.x.x, opening.origin])
	t.check(god.global_position == Vector2(960, 600), "the god at (960, 600) (%s)" % god.global_position)
	t.check(player.global_position == Layout.PLAYER_START and Layout.PLAYER_START == Vector2(620, 761) and player.facing == UP,
		"the player on the finale's mark, drawn as it drew them - origin (620, 761) - facing UP (%s, facing %d)" % [player.global_position, player.facing])
	t.check(player.is_talking and god.state_machine.current_state.name == "Open", "held through Open (%s)" % god.state_machine.current_state.name)
	var opened: bool = await t.wait_until(func(): return god.state_machine.current_state.name == "Idle", 120)
	var pulled: bool = await t.wait_until(func(): return absf(t.root.canvas_transform.x.x - Layout.VIEW_ZOOM) < 0.0001, 120)
	await t.wait(10)
	t.process_frame.disconnect(sample)
	var view: Transform2D = t.root.canvas_transform
	var shown := Rect2(view.affine_inverse() * Vector2.ZERO, Vector2(1920, 1080) / view.x.x)
	t.log_p("after the pull-back: %s, showing %s" % [view, shown])
	t.check(opened and not player.is_talking, "Open hands to Idle with is_talking false")
	t.check(pulled and view.origin == Vector2(320, 4) and shown.position.is_equal_approx(Vector2(-480, -6)) \
		and shown.size.is_equal_approx(Vector2(2880, 1620)),
		"the view pulls back to 2/3 on (960, 804): world -480 to 2400 and -6 to 1614 (%s)" % [shown])
	# The way there: a plain pull-back, its top edge's middle held (within the 6 px between the two views' tops and
	# a rounded pixel), and no step bigger than a few frames' worth - none from the fight's long first frame.
	var biggest := 0.0
	var off_x := 0.0
	var top_y := Vector2(INF, -INF)
	for i in seen.views.size():
		var frame_view: Transform2D = seen.views[i]
		var top_middle: Vector2 = frame_view.affine_inverse() * Vector2(960, 0)
		off_x = maxf(off_x, absf(top_middle.x - 960.0))
		top_y = Vector2(minf(top_y.x, top_middle.y), maxf(top_y.y, top_middle.y))
		if i > 0:
			biggest = maxf(biggest, absf(frame_view.x.x - seen.views[i - 1].x.x))
	t.log_p("the pull-back over %d frames: the biggest step %.4f; the top edge's middle at x 960 +- %.2f, y %.2f to %.2f" % [
		seen.views.size(), biggest, off_x, top_y.x, top_y.y])
	var whole: bool = seen.views.size() >= 2 and absf(seen.views[-1].x.x - Layout.VIEW_ZOOM) < 0.0001
	t.check(whole and biggest > 0.0 and biggest < 0.04 and off_x <= 0.8 and top_y.x >= -6.8 and top_y.y <= 0.8,
		"a smooth, plain pull-back: no jump (biggest step %.4f), the top edge's middle held" % biggest)
	# His bar at the top centre, over him: see-through while he is behind it, multiplied with its own reveal.
	var see: Control = god.hud_see_through
	var reveal: float = god.health_bar.modulate.a
	t.log_p("the bar's block on screen %s; him on screen %s" % [god.hud_block, god._body_on_screen()])
	t.check(god.see_through_on and is_equal_approx(see.modulate.a, Layout.HUD_SEE_THROUGH_ALPHA) and is_equal_approx(reveal, 1.0)
		and god.health_bar.get_parent() == see,
		"with him behind it the bar settles see-through: Open's reveal %.2f x the see-through %.2f = %.2f" % [reveal,
			see.modulate.a, reveal * see.modulate.a])
	god.body.visible = false
	await t.wait(3)
	var easing: float = see.modulate.a
	await t.wait(20)
	var clear: float = see.modulate.a
	god.body.visible = true
	await t.wait(20)
	t.check(easing > Layout.HUD_SEE_THROUGH_ALPHA and easing < 1.0 and is_equal_approx(clear, 1.0) \
		and is_equal_approx(see.modulate.a, Layout.HUD_SEE_THROUGH_ALPHA),
		"with him hidden it eases back (%.2f three frames in) to 1 (%.2f), and see-through again once he's back (%.2f)" % [
			easing, clear, see.modulate.a])
	var floor_rect: Rect2 = Layout.FLOOR
	var want_ring := Rect2(floor_rect.position + Vector2(18, 39), floor_rect.size - Vector2(36, 81))
	t.check(player.ring_origins.is_equal_approx(want_ring), "the player's floor is the staging's (%s)" % [player.ring_origins])
	player.global_position = Vector2(-340, 800)
	await t.wait(3)
	var inside: Vector2 = player.global_position
	player.global_position = Vector2(-600, 1700)
	await t.wait(3)
	var outside: Vector2 = player.global_position
	player.global_position = Layout.PLAYER_START
	await t.wait(2)
	# To within the walls' collision margin, which leaves a body held against them a fraction of a pixel off.
	t.check(inside == Vector2(-340, 800) and outside.distance_to(Vector2(want_ring.position.x, want_ring.end.y)) < 0.5,
		"they walk well past the old ropes (%s) and no further than the new walls (%s)" % [inside, outside])
	# His fight's theme (the user's own track, when it is in) or, without it, his final theme: whichever it is, playing,
	# looping and at its own level.
	var music: AudioStreamPlayer = god.music
	var want: Dictionary = Layout.music()
	var loops: bool = (music.stream is AudioStreamWAV and music.stream.loop_mode == AudioStreamWAV.LOOP_FORWARD) \
		or (music.stream is AudioStreamMP3 and music.stream.loop)
	t.check(music.playing and music.stream.resource_path == want.stream.resource_path
			and is_equal_approx(music.volume_db, want.volume_db) and loops,
		"his theme is playing, looping, at its own level (%s, %.1f dB, loops %s)" % [music.stream.resource_path, music.volume_db, loops])
	var row: Dictionary = god.health_bar.rows[0]
	var full: int = Layout.UPPERCUTS_TO_BEAT
	t.check(god.boss_health == full and god.max_health == full and is_equal_approx(row.value, float(full))
			and is_equal_approx(row.max, float(full)),
		"the bar at %d of %d (%d of %d, drawn %.0f of %.0f)" % [full, full, god.boss_health, god.max_health, row.value, row.max])
	t.check(is_equal_approx(god.health_bar.modulate.a, 1.0), "and the HUD faded in (%.2f)" % god.health_bar.modulate.a)
	var pause: Node = t.pause_menu()
	t.check(pause.can_open(), "the pause screen can open in it")
	await t.tap_pause()
	t.check(pause.is_open() and t.paused, "and Escape opens it")
	await t.tap_pause()
	t.check(not pause.is_open() and not t.paused, "and closes it")
	var progress: Node = t.root.get_node("GameProgress")
	t.check(progress.fight_index == 9, "fight_index is 9 (%d)" % progress.fight_index)


#THE HANDOFF

static func tier_handoff(t) -> void:
	Layout.COMBOS = [] as Array[String]
	var god_fight: bool = FinaleLayout.USE_GOD_FIGHT
	FinaleLayout.USE_GOD_FIGHT = true
	t.check(FinaleLayout.after_finale_scene() == GOD_SCENE, "with the switch on the finale ends on his last phase")
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	await t.open_scene(ROOM)
	var room: Node = t.current_scene
	var talk: Dictionary = await Finale.start_talk(t, room)
	var landed: bool = await Finale.read_until(t, func(): return scene_is(t, GOD_SCENE) or scene_is(t, CARD))
	t.process_frame.disconnect(watch.step)
	var last: Dictionary = watch.lines[-1] if not watch.lines.is_empty() else {}
	t.log_p("the room's last line: %s; scenes %s" % [last, watch.scenes.map(func(s: String) -> String: return s.get_file())])
	t.check(talk.talking and landed and scene_is(t, GOD_SCENE) and last.get("text", "") == LAST_LINE and not watch.scenes.has(CARD),
		"his last line lands on the god fight, never the card")
	await check_god_up(t, "after his last line")
	await held_room(t, GOD_SCENE)
	await held_walk_out(t)
	FinaleLayout.USE_GOD_FIGHT = false
	t.check(FinaleLayout.after_finale_scene() == CARD, "with the switch off the finale ends on the card")
	await held_room(t, CARD)
	FinaleLayout.USE_GOD_FIGHT = god_fight


# A hold in the room, at the roam: where it lands.
static func held_room(t, want: String) -> void:
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	await t.open_scene(ROOM)
	var room: Node = t.current_scene
	await t.wait_until(func(): return room.beat == &"roam", 300)
	await Finale.hold_escape(t)
	var landed: bool = await t.wait_until(func(): return scene_is(t, want), 240)
	await idle_frames(t, 3)
	t.process_frame.disconnect(watch.step)
	var other := CARD if want == GOD_SCENE else GOD_SCENE
	t.check(landed and not watch.scenes.has(other), "a hold in the room lands on %s (%s)" % [want.get_file(),
		watch.scenes.map(func(s: String) -> String: return s.get_file())])
	if want == GOD_SCENE:
		await check_god_up(t, "after a hold in the room")
	else:
		await t.wait_until(func(): return scene_is(t, MENU), 60 * 12)


# A hold in the walk-out, as his line types: the god fight, never the card.
static func held_walk_out(t) -> void:
	var watch = await Finale.into_fight(t)
	Finale.kill(t)
	await t.wait_until(func(): return t.sm.states["WalkOut"].entered, 300)
	await t.wait_until(func(): return Finale.balloon_in(t.current_scene) != null and Finale.balloon_in(t.current_scene).dialogue_label.is_typing, 300)
	await Finale.hold_escape(t)
	var landed: bool = await t.wait_until(func(): return scene_is(t, GOD_SCENE), 240)
	await idle_frames(t, 3)
	t.process_frame.disconnect(watch.step)
	t.check(landed and not watch.scenes.has(CARD) and not watch.scenes.has(ROOM),
		"a hold in the walk-out lands on the god fight (%s)" % [watch.scenes.map(func(s: String) -> String: return s.get_file())])
	await check_god_up(t, "after a hold in the walk-out")


static func check_god_up(t, label: String) -> void:
	await t.wait(3)
	var god: Node = t.current_scene.get_node_or_null(GOD_PATH) if scene_is(t, GOD_SCENE) else null
	var outro_gone: bool = await t.wait_until(func(): return not t.root.has_node("FightOutro"), 30)
	t.check(god != null and god.state_machine.current_state != null and outro_gone and is_equal_approx(Engine.time_scale, 1.0),
		"%s: his last phase is up (%s), no FightOutro, time_scale 1" % [label, god.state_machine.current_state.name if god else "none"])
	var settled: Dictionary = await Finale.settled_god_view(t)
	t.check(settled.ok, "%s: once it has pulled back, the view is the fight's 2/3 base, still (%s)" % [label, settled])


#THE MENU

static func tier_menu(t) -> void:
	await t.open_scene(MENU)
	await t.wait(40)
	var menu: Node = t.current_scene
	var rows: Array = menu.find_children("*", "Button", true, false).filter(func(button: Button) -> bool:
		return button.text == "    GOD")
	var row: Button = rows[0] if rows.size() == 1 else null
	t.check(row != null and not row.disabled, "the boss select has one GOD row, enabled")
	if row == null:
		return
	var panel: Control = row
	while panel != null and not (panel is PanelContainer):
		panel = panel.get_parent()
	var rect: Rect2 = menu.BOSS_SELECT_RECT
	t.check(panel != null and panel.get_combined_minimum_size().y <= rect.size.y and panel.get_global_rect().encloses(row.get_global_rect()),
		"inside the panel, and the panel inside BOSS_SELECT_RECT (%s needed of %s)" % [panel.get_combined_minimum_size() if panel else Vector2.ZERO, rect.size])
	var watch = Finale.Watch.new(t)
	watch.step()
	t.process_frame.connect(watch.step)
	row.pressed.emit()
	var opened: bool = await t.wait_until(func(): return scene_is(t, GOD_SCENE), 300)
	await idle_frames(t, 3)
	t.process_frame.disconnect(watch.step)
	var progress: Node = t.root.get_node("GameProgress")
	t.check(opened and watch.scenes == [MENU, GOD_SCENE] and progress.fight_index == 9 and not progress.start_at_finale,
		"the GOD row opens the fight with no finale scene first (%s), fight 10's" % [watch.scenes.map(func(s: String) -> String: return s.get_file())])


#THE ROTATION

static func tier_rotation(t) -> void:
	var god: Node = await open_god(t, [STUB, MISSING, STUB] as Array[String], &"quick")
	var machine: Node = god.state_machine
	var names: Array = machine.combos.map(func(combo: Node) -> StringName: return StringName(combo.name))
	t.check(names == [&"stub_combo", &"stub_combo_2"], "the missing script is skipped: two attacks built (%s)" % [names])
	var states: Array = []
	var track := func():
		if not is_instance_valid(machine) or machine.current_state == null:
			return
		var state := String(machine.current_state.name)
		if states.is_empty() or states[-1] != state:
			states.append(state)
	t.process_frame.connect(track)
	var four: bool = await t.wait_until(func(): return machine.rotation_log.size() >= 5, 60 * 30)
	t.process_frame.disconnect(track)
	t.log_p("states %s, the rotation %s" % [states, machine.rotation_log])
	t.check(four and machine.rotation_log.slice(0, 4) == [&"stub_combo", &"stub_combo_2", &"stub_combo", &"stub_combo_2"],
		"the two take turns (%s)" % [machine.rotation_log])
	t.check(states.slice(0, 9) == ["Open", "Idle", "stub_combo", "Idle", "stub_combo_2", "Idle", "stub_combo", "Idle", "stub_combo_2"],
		"through Idle each time, from Open")


#THE DAMAGE

# One of the stub's punch-outs: three punch presses, then the mash every `every` frames, the hype full first if
# `supercharge`. What it saw.
static func punch_out(t, god: Node, supercharge := false, every := 3) -> Dictionary:
	var combo: Node = god.state_machine.combos[0]
	var finisher: Node = t.player.finisher
	var ready: bool = await t.wait_until(func(): return combo.punching and not combo.released, 60 * 20)
	if supercharge:
		t.player.hype.add(t.player.hype.max_hype)
	var seen := {"hits": []}
	var on_hit := func(_index: int, _last: bool) -> void:
		if is_instance_valid(god):
			seen.hits.append(god.boss_health)
	finisher.juggle_hit.connect(on_hit)
	var before: int = god.boss_health
	for i in 3:
		t.tap(KEY_Q)
		await t.wait(8)
	var prompt: bool = await t.wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120)
	var supercharged: bool = finisher.supercharged
	var presses: int = await t.mash_tiered(every)
	var banked: int = finisher.juggle_tiers
	await t.wait_until(func(): return not finisher.is_active(), 600)
	finisher.juggle_hit.disconnect(on_hit)
	return {"ready": ready, "prompt": prompt, "supercharged": supercharged, "presses": presses, "banked": banked,
		"hits": seen.hits, "before": before}


static func tier_damage(t) -> void:
	var god: Node = await open_god(t, [STUB] as Array[String], &"punch")
	var stub: GDScript = load(STUB)
	# The view through the punch-out: the finisher's zooms are over the fight's own 2/3, and it goes back to it.
	var scales := {"low": INF, "high": -INF}
	var watch_view := func():
		if scene_is(t, GOD_SCENE) and t.current_scene.get_node(GOD_PATH).state_machine.current_combo() != null:
			scales.low = minf(scales.low, t.root.canvas_transform.x.x)
			scales.high = maxf(scales.high, t.root.canvas_transform.x.x)
	t.process_frame.connect(watch_view)
	var plain: Dictionary = await punch_out(t, god)
	await t.wait_until(func(): return stub.reached == &"done", 60 * 10)
	await t.wait(20)
	t.process_frame.disconnect(watch_view)
	var after_view: Transform2D = t.root.canvas_transform
	t.log_p("the view through the punch-out: %.4f to %.4f; after it %s" % [scales.low, scales.high, after_view])
	t.check(is_equal_approx(scales.low, Layout.VIEW_ZOOM) and scales.high > Layout.VIEW_ZOOM * 1.2 \
		and is_equal_approx(after_view.x.x, Layout.VIEW_ZOOM) and after_view.origin == Vector2(320, 4),
		"the finisher's zoom is closer than the fight's 2/3 (to %.3f), never further out, and back on it after" % scales.high)
	t.log_p("a three-bar punch-out: %s; him %d -> %d, the stub's bars %d" % [plain, plain.before, god.boss_health, stub.bars])
	t.check(plain.ready and plain.prompt and not plain.supercharged and plain.banked == 3,
		"three presses daze the puppet and the mash is tiered: 3 bars banked (%d)" % plain.banked)
	t.check(plain.hits == [plain.before - 1, plain.before - 2, plain.before - 3] and god.boss_health == plain.before - 3,
		"each uppercut takes exactly 1 off him (%s), 3 in all (%d -> %d)" % [plain.hits, plain.before, god.boss_health])
	t.check(is_equal_approx(god.health_bar.rows[0].value, float(god.boss_health)) and stub.bars == 3,
		"his bar shows it (%.0f) and the punch-out reports its 3 bars (%d)" % [god.health_bar.rows[0].value, stub.bars])
	var hyped: Dictionary = await punch_out(t, god, true)
	await t.wait_until(func(): return stub.reached == &"done", 60 * 10)
	t.log_p("a supercharged punch-out: %s; him %d -> %d, hype %.1f" % [hyped, hyped.before, god.boss_health, t.player.hype.hype])
	t.check(hyped.supercharged and hyped.banked == 3 and hyped.hits == [hyped.before - 1, hyped.before - 2, hyped.before - 4],
		"a supercharged three-bar mash takes 1, 1, then 2 for the hype on the last (%s)" % [hyped.hits])
	t.check(not t.player.hype.is_full() and is_equal_approx(t.player.hype.hype, 0.0), "and spends the hype (%.1f)" % t.player.hype.hype)
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	var defeat: Dictionary = {"beats": [], "puppets_at_leaving": -1, "strings_at_leaving": -1}
	var track := func():
		if not scene_is(t, GOD_SCENE):
			return
		var state: Node = t.current_scene.get_node(GOD_PATH).state_machine.states["Defeated"]
		if defeat.beats.is_empty() or defeat.beats[-1] != state.beat:
			defeat.beats.append(state.beat)
			if state.beat == &"leaving":
				defeat.puppets_at_leaving = puppets_up(t).size()
				defeat.strings_at_leaving = t.current_scene.get_node(STRINGS_PATH).line_count()
	t.process_frame.connect(track)
	await t.wait_until(func(): return god.state_machine.combos[0].punching, 60 * 20)
	god.boss_health = 1
	god.health_bar.set_value(0, 1, HIT_SILENT)
	var kill: Dictionary = await punch_out(t, god)
	var carded: bool = await t.wait_until(func(): return scene_is(t, CARD), 60 * 20)
	var at_menu: bool = await t.wait_until(func(): return scene_is(t, MENU), 60 * 15)
	await idle_frames(t, 3)
	t.process_frame.disconnect(watch.step)
	t.process_frame.disconnect(track)
	var after: Array = watch.scenes.slice(watch.scenes.find(GOD_SCENE) + 1)
	t.log_p("the 25th uppercut: %s; his defeat's beats %s; scenes after the fight %s; outros %d" % [kill, defeat.beats,
		after.map(func(s: String) -> String: return s.get_file()), watch.outros.size()])
	t.check(kill.hits.size() == 1 and kill.hits[0] == 0, "the 25th uppercut is the last (%s)" % [kill.hits])
	t.check(watch.outros.size() == 1, "exactly one FightOutro (%d)" % watch.outros.size())
	t.check(defeat.beats == [&"", &"snap", &"crumple", &"dissolve", &"god", &"leaving"] and defeat.puppets_at_leaving == 0 and defeat.strings_at_leaving == 0,
		"his defeat plays out - strings snapped, puppets gone - before he leaves (%s)" % [defeat.beats])
	t.check(carded and at_menu and after == [CARD, MENU] and not t.root.has_node("FightOutro"),
		"then the card, then the menu (%s)" % [after.map(func(s: String) -> String: return s.get_file())])


#THE LOSS

# His player_lost (JordanFinale.dialogue, through his OUTRO_DIALOGUE): every line his, in the demon portrait. FightOutro
# holds each of a loss's lines 0.3 s, then a press moves on one line, so a player sees all three.
static func tier_lost(t) -> void:
	var god: Node = await open_god(t, [] as Array[String])
	await t.wait_until(func(): return god.state_machine.current_state.name == "Idle", 120)
	var manager: Node = t.root.get_node("DialogueManager")
	var dialogue: Resource = load(god.OUTRO_DIALOGUE)
	var titled: Array = []
	var line = await manager.get_next_dialogue_line(dialogue, "player_lost")
	while line != null:
		titled.append({"character": line.character, "text": line.text, "portrait": line.get_tag_value("portrait")})
		line = await manager.get_next_dialogue_line(dialogue, line.next_id)
	t.log_p("lost: player_lost %s" % [titled])
	t.check(titled.map(func(entry: Dictionary) -> String: return entry.text) == LOST_LINES
		and titled.all(func(entry: Dictionary) -> bool: return entry.character == "Jordan" and entry.portrait == "demon"),
		"his player_lost lines verbatim, every one his in the demon portrait")
	var watch = Finale.Watch.new(t)
	t.process_frame.connect(watch.step)
	t.player.playerHealth = 0
	var shown: bool = await t.wait_until(func(): return not watch.lines.is_empty(), 60 * 5)
	var balloon: Node = Finale.Watch.balloon_in(t.current_scene)
	var typed: bool = shown and await t.wait_until(func(): return not balloon.dialogue_label.is_typing, 60 * 5)
	var portrait: String = balloon.portrait.texture.resource_path if typed and balloon.portrait.texture != null else ""
	var voiced: bool = typed and balloon._voice == DialogueVoices.for_character("Jordan")
	# Nothing moves a loss's line on but a press.
	await t.wait(60)
	var held: bool = watch.lines.size() == 1 and scene_is(t, GOD_SCENE)
	# A press a line, each once the line has typed out and its lock is past: the last one's goes to Defeat.
	var presses := 0
	for i in LOST_LINES.size():
		if i > 0:
			await t.wait_until(func(): return watch.lines.size() > i, 60 * 2)
			balloon = Finale.Watch.balloon_in(t.current_scene)
			if balloon != null:
				await t.wait_until(func(): return not balloon.dialogue_label.is_typing, 60 * 5)
			await t.wait(30)
		t.tap(KEY_ENTER)
		presses += 1
	var defeated: bool = await t.wait_until(func(): return scene_is(t, DEFEAT), 60 * 10)
	await t.wait(10)
	t.process_frame.disconnect(watch.step)
	var message: String = t.current_scene.message_label.text if defeated else ""
	t.log_p("lost: %s; lines %s; portrait %s" % [message, watch.lines, portrait])
	t.check(shown and watch.lines[0].character == "Jordan" and watch.lines[0].text == LOST_LINES[0] and portrait.ends_with("portrait_demon.png")
		and voiced, "health to 0: his first loss line, in his demon portrait and his own voice")
	t.check(held and defeated and watch.outros.size() == 1 and presses == LOST_LINES.size()
		and watch.lines.map(func(entry: Dictionary) -> String: return entry.text) == LOST_LINES,
		"it holds until a press, then a press a line shows all three and the third's goes to the Defeat screen, one FightOutro")
	t.check(message.contains("#arena-10"), "reading #arena-10 (%s)" % message)


#RELEASE

static func tier_release(t) -> void:
	for cut_by in ["death", "defeat"]:
		var god: Node = await open_god(t, [STUB] as Array[String], &"hold")
		var stub: GDScript = load(STUB)
		var player: CharacterBody2D = t.player
		var z_before := player.z_index
		var holding: bool = await t.wait_until(func(): return stub.reached == &"holding", 60 * 12)
		await t.wait(20)
		var combo: Node = god.state_machine.combos[0]
		var strings: Node = t.current_scene.get_node(STRINGS_PATH)
		var held := {"locked": player.is_action_locked, "posed": player.is_posed(), "dark": god.darkness.visible and god.darkness.modulate.a > 0.99,
			"lifted": player.z_index == z_before + Layout.LIFT_Z, "hud": god.health_bar.modulate.a < 0.01,
			"puppets": puppets_up(t).size(), "strings": strings.line_count(), "hazards": hazards_up(t).size(),
			"arrow": is_instance_valid(combo.arrow_badge) and combo.arrow_badge.visible, "hint": is_instance_valid(combo.hint_node)}
		t.log_p("cut by %s, held: %s" % [cut_by, held])
		t.check(holding and held.locked and held.posed and held.dark and held.lifted and held.hud and held.puppets == 2 \
			and held.strings == 4 and held.hazards >= 1 and held.arrow and held.hint,
			"%s: the stub holds everything an attack puts up" % cut_by)
		var left := {"puppets": -1, "strings": -1}
		# Looked up each frame: a lambda holding a node of the fight would be called with it freed once the scene goes.
		var at_leaving := func():
			if left.puppets >= 0 or not scene_is(t, GOD_SCENE):
				return
			if t.current_scene.get_node(GOD_PATH).state_machine.states["Defeated"].beat == &"leaving":
				left.puppets = puppets_up(t).size()
				left.strings = t.current_scene.get_node(STRINGS_PATH).line_count()
		t.process_frame.connect(at_leaving)
		var puppet: Node = combo.puppets.get(&"greyson")
		if cut_by == "death":
			player.playerHealth = 0
			await t.wait_until(func(): return t.root.has_node("FightOutro"), 30)
		else:
			god.boss_health = 1
			god.take_uppercut(puppet)
			await t.wait_until(func(): return god.defeated, 30)
		await t.wait(3)
		var gone := {"locked": player.is_action_locked, "posed": player.is_posed(),
			"dark": god.darkness.visible or god.darkness.modulate.a > 0.0, "z": player.z_index, "hud": god.health_bar.modulate.a,
			"rifts": rifts_up(t).size(), "hazards": hazards_up(t).size(), "released": combo.released,
			"puppets": puppets_up(t).size(), "strings": strings.line_count()}
		t.log_p("cut by %s, left: %s" % [cut_by, gone])
		t.check(gone.released and not gone.locked and not gone.posed and not gone.dark and gone.z == z_before \
			and is_equal_approx(gone.hud, 1.0) and gone.rifts == 0 and gone.hazards == 0,
			"%s: no lock, no Posed state, no darkness, no rifts or hazards, the player's z back, the HUD at alpha 1" % cut_by)
		if cut_by == "death":
			t.check(gone.puppets == 0 and gone.strings == 0, "death: no puppets and no strings")
			await t.wait_until(func(): return scene_is(t, DEFEAT), 60 * 10)
		else:
			t.check(gone.puppets == 2, "his defeat: the puppets kept for his defeat to play out (%d)" % gone.puppets)
			await t.wait_until(func(): return scene_is(t, CARD), 60 * 15)
			t.check(left.puppets == 0 and left.strings == 0,
				"his defeat: no puppets and no strings once it has played them out (%d, %d)" % [left.puppets, left.strings])
			await t.wait_until(func(): return scene_is(t, MENU), 60 * 15)
		t.process_frame.disconnect(at_leaving)
		await t.wait(5)


#THE PAIRINGS

static func tier_pairings(t) -> void:
	for pairing in PAIRINGS:
		var pair: Array[Dictionary] = []
		pair.assign(pairing)
		var names: Array = pair.map(func(entry: Dictionary) -> StringName: return entry.boss)
		var god: Node = await open_god(t, [STUB] as Array[String], &"punch", pair)
		var stub: GDScript = load(STUB)
		# Looked up each frame, never held: each puppet seen rising (clipped, its rise running), and one juggled.
		var seen := {"rose": [], "juggled": false}
		var watch := func():
			for puppet in puppets_up(t):
				if puppet.is_clipped() and puppet.move_tween != null and puppet.move_tween.is_running() \
					and not seen.rose.has(puppet.boss):
					seen.rose.append(puppet.boss)
				if puppet.is_juggled():
					seen.juggled = true
		t.process_frame.connect(watch)
		var summoned: bool = await t.wait_until(func(): return stub.reached == &"punch_out", 60 * 20)
		await t.wait(5)
		var strings: Node = t.current_scene.get_node(STRINGS_PATH)
		var up: Array = puppets_up(t)
		var hung := []
		for puppet in up:
			var hook: Vector2 = puppet.hook_point(&"back")
			var shape: RectangleShape2D = puppet.hurt_shape.shape
			var body := Rect2(puppet.hurt_shape.global_position - shape.size / 2.0, shape.size)
			var up_on_strings: bool = not puppet.is_clipped() and puppet.sprite.position == puppet.sprite_base_position \
				and puppet.current_anim == puppet.spec.idle and strings.is_attached(puppet)
			hung.append({"boss": puppet.boss, "hook": hook, "on_back": body.has_point(hook), "up": up_on_strings,
				"flipped": puppet.sprite.flip_h, "sheet": puppet.sprite.texture.resource_path.get_file()})
		t.log_p("%s: summoned %s, rose %s, hanging %s, %d strings" % [names, summoned, seen.rose, hung, strings.line_count()])
		t.check(summoned and up.size() == 2 and up.all(func(puppet: Node) -> bool: return names.has(puppet.boss))
			and seen.rose.size() == 2, "%s: both rise through their rifts" % [names])
		t.check(hung.size() == 2 and hung.all(func(h: Dictionary) -> bool: return h.up and h.on_back) and strings.line_count() == 4,
			"%s: both hang on his hands, two strings each on their back hooks" % [names])
		var finisher: Node = t.player.finisher
		var before: int = god.boss_health
		var hits := {"count": 0}
		var on_hit := func(_index: int, _last: bool) -> void: hits.count += 1
		finisher.juggle_hit.connect(on_hit)
		for i in 3:
			t.tap(KEY_Q)
			await t.wait(8)
		var prompt: bool = await t.wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120)
		var presses: int = await mash_bars(t, 1)
		var banked: int = finisher.juggle_tiers
		await t.wait_until(func(): return not finisher.is_active(), 600)
		finisher.juggle_hit.disconnect(on_hit)
		var recalled: bool = await t.wait_until(func(): return stub.reached == &"done", 60 * 10)
		await t.wait(10)
		t.process_frame.disconnect(watch)
		t.log_p("%s: the punch-out's mash %d presses, %d bar, %d uppercut, juggled %s; him %d -> %d, the payoff %d" % [
			names, presses, banked, hits.count, seen.juggled, before, god.boss_health, stub.bars])
		t.check(prompt and banked == 1 and hits.count == 1 and seen.juggled and god.boss_health == before - 1 and stub.bars == 1,
			"%s: three punches and a one-bar mash: one uppercut, a juggle, exactly 1 off him, the payoff's 1 bar" % [names])
		t.check(recalled and puppets_up(t).is_empty() and strings.line_count() == 0 and rifts_up(t).is_empty(),
			"%s: the recall leaves no puppets, strings or rifts (%s: %d, %d, %d)" % [names, stub.reached, puppets_up(t).size(),
				strings.line_count(), rifts_up(t).size()])
	load(STUB).PAIR = [] as Array[Dictionary]


# The mash until `want` bars are banked, then not a press more, so the finisher resolves on them. The presses.
static func mash_bars(t, want: int, every := 3) -> int:
	var finisher: Node = t.player.finisher
	finisher.min_press_interval = 0.0
	var pair: Array = finisher.mash_actions()
	var presses := 0
	var i := 0
	while finisher.phase == FINISHER_DAZED or finisher.phase == FINISHER_CHARGING:
		if finisher.tier_meter.banked < want and i % every == 0:
			t.tap(t.MASH_KEYS[pair[presses % 2]])
			presses += 1
		i += 1
		await t.physics_frame
	return presses
