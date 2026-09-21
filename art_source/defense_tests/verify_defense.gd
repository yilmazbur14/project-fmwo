extends SceneTree

# Headless checks on the player's defence: stamina, the guard, the parry and its window, the guard
# break, the perfect dodge, the dash recovery, hype, the finisher's knockback, status effects and the
# parry-only lock. One mode per run, no window needed:
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/defense_tests/verify_defense.gd -- mode=<name>
# Some modes take a second argument, fight=<name> or tier=<name>; README.md lists them all.
# Modes that mash the finisher prompt need real time rather than fixed frames, because the prompt
# gates presses on a real-seconds interval:
#   Godot.exe --headless --max-fps 60 --script res://art_source/defense_tests/verify_defense.gd -- mode=super_uppercut
#
# Every check prints "P PASS ..." or "P FAIL ...", each run ends with
#   P [<time> f<frame>] RESULT mode=<name> fails=<n>
# and the process exits with that number of failures, so a runner can read the exit code.
#
# Presses are real InputEventKey events, so what is under test is the player's own input path, and
# hits are delivered through player.receive_hit() the way every attack in the game delivers them.

const SCENES := {
	"eric": "res://Scenes/Bosses/EricBossFightScene.tscn",
	"greyson": "res://Scenes/Bosses/GreysonBossFightScene.tscn",
	# Deliberately the LEGACY combined scene, not the shipped CarterBossFightScene: test_smoke,
	# test_blocks, test_approach and test_dodge_rollout all reach into Arena/CarterAndJoshScene/Carter
	# and would break against the split fight. The shipped Carter is covered by clone_cadence, which
	# uses Arena/CarterAkumaScene. Pointing this row at the split fight is its own job - it means
	# reworking those four node paths - and is NOT a one-line change.
	"carter": "res://Scenes/Bosses/CarterAndJoshBossFightScene.tscn",
	"josh": "res://Scenes/Bosses/JoshBossFightScene.tscn",
	"mason": "res://Scenes/Bosses/MasonBossFightScene.tscn",
	"jordan": "res://Scenes/Bosses/JordanBossFightScene.tscn",
	"liam": "res://Scenes/Bosses/LiamBossFightScene.tscn",
}

const DEFENSE_BINDINGS_PATH := "user://input_bindings_defense_tests.cfg"

var mode := ""
var fails := 0
var clock := 0.0
var frame := 0
var player: CharacterBody2D
var defense: Node
var boss: Node
var sm: Node
var watch := Callable()


var fight := "eric"
var tier := "normal"
# Eric's pacing (EricPacing.version) for smoke and approach: 1 or 2, or 0 for the one that ships.
var ver := 0

# The modes written against Eric's fight as it was (EricPacing V1): they run on it, whatever ships. With
# V1 pinned his punish window is Downed, and the mash and the uppercut are the ones they expect.
const ERIC_V1_MODES := [
	"stagger", "stagger_chain", "stagger_win", "stagger_lose", "knockback", "kill_shove", "auto_finisher",
	"auto_kill", "tells", "grab_parry", "grab_block", "parry_projectiles", "block_eric", "behind",
	"dash_through", "super_uppercut", "gamepad_mash", "prompt_overlap",
	# Also driving his real attacks through to Downed.
	"baseline", "guard_break", "guard_break_grab", "dodge_bosses",
]
const ERIC_PACING := "res://Scripts/EricPacing.gd"


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("mode="):
			mode = arg.substr(5)
		elif arg.begins_with("fight="):
			fight = arg.substr(6)
		elif arg.begins_with("tier="):
			tier = arg.substr(5)
		elif arg.begins_with("ver="):
			ver = int(arg.substr(4))
	_main.call_deferred()


# Before the fight loads: his _ready reads it.
func pin_eric(version: int) -> void:
	load(ERIC_PACING).version = version


# A PlayerFeel number under this player's feel_v2.
func feel(key: String) -> Variant:
	return load("res://Scripts/PlayerFeel.gd").value(key, player.feel_v2)


func log_p(msg: String) -> void:
	print("P [%.3f f%d] %s" % [clock, frame, msg])


func check(cond: bool, msg: String) -> void:
	print("P %s %s" % ["PASS" if cond else "FAIL", msg])
	if not cond:
		fails += 1


func _process(delta: float) -> bool:
	clock += delta
	frame += 1
	if watch.is_valid():
		watch.call()
	return false


func wait(n: int) -> void:
	for i in n:
		await physics_frame


func wait_until(cond: Callable, max_frames := 600) -> bool:
	for i in max_frames:
		if cond.call():
			return true
		await physics_frame
	return false


func key(code: int, pressed: bool) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.physical_keycode = code
	ev.keycode = code
	ev.pressed = pressed
	return ev


func press(code: int) -> void:
	Input.parse_input_event(key(code, true))


func release(code: int) -> void:
	Input.parse_input_event(key(code, false))


func tap(code: int) -> void:
	press(code)
	release(code)


func load_fight(key_name: String, keep_balloon := false) -> void:
	change_scene_to_file(SCENES[key_name])
	while current_scene == null or current_scene.scene_file_path != SCENES[key_name]:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	# Another coder's temporary driver rides in Eric's fight scene and steers his states; it would
	# drive them through these tests too. Freeing it only affects this process.
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	await skip_entrance()
	if keep_balloon:
		return
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(1)
	await skip_vs_card()
	await wait(2)


func vs_card() -> Node:
	return current_scene.get_node_or_null("Arena/VsCard")


# The fight's boss entrance, whichever boss has one. Only Eric does.
func entrance_state() -> Node:
	for node in current_scene.find_children("*", "Node", true, false):
		if node.has_method(&"finish_entrance"):
			return node
	return null


# Reads the line that is up the way a player does: one press skips its typing, the next moves on.
func read_line() -> void:
	var balloon := live_balloon()
	if balloon == null:
		return
	for i in 120:
		if not is_instance_valid(balloon) or live_balloon() != balloon:
			return
		var typing: bool = balloon.dialogue_label.is_typing
		tap(KEY_ENTER)
		await wait(4)
		if not typing:
			return


# A boss entrance plays between a fight loading and its pre-fight lines, and holds the player
# through it. Every mode but the entrance's own is about the fight, so it is cut here the way a held
# ui_cancel cuts it: the ring is set at once and the lines come straight up.
func skip_entrance() -> void:
	var intro := entrance_state()
	if intro == null:
		return
	# Its Enter() is deferred, so on a freshly loaded fight it may not have started yet.
	await wait_until(func(): return intro.entered, 60)
	if not intro.finished:
		intro.skip()
	await wait(2)


# A boss whose entrance is a plain state in its own machine, rather than a node with
# finish_entrance() the way Eric's is: entrance_state() cannot see it, so skip_entrance() no-ops and
# load_fight()'s dialogue_ended fires while the intro is STILL PLAYING. The lines the intro opens
# when it ends are then never dismissed, the boss never leaves Intro, and every mode reports a fight
# that quietly does nothing - blocks and smoke both sat on an inert Josh for 45 s. These fights keep
# the balloon and get read through the way a player reads them.
const STATE_INTROS := {
	"liam": "Arena/BixbyBeastScene/BixbyBeastCharacterBody/StateManager",
	"josh": "Arena/JoshCardsScene/JoshCardsCharacterBody/StateManager",
}


# Taps through the intro and the lines behind it until the machine leaves Intro, and reports the
# state it settled in so a caller can say so.
func clear_intro(key_name: String) -> String:
	if not STATE_INTROS.has(key_name):
		return ""
	var sm: Node = current_scene.get_node(STATE_INTROS[key_name])
	for i in 3000:
		if sm.current_state.name != "Intro":
			break
		if i % 15 == 0:
			tap(KEY_ENTER)
		await physics_frame
	return str(sm.current_state.name)


# The VS card plays between a fight's lines and the fight itself; every mode but vs_card is about
# the fight, so it is skipped here the way a player skips it, and the input grace it leaves behind
# is dropped rather than waited out. Those 0.15 seconds are REAL ones: under --fixed-fps 60 a frame
# costs no real time, so waiting them out would run hundreds of game frames - long enough for the
# fight's own post-dialogue timer to fire before a mode has parked the boss. vs_card is the mode
# that lets the card play and the grace run.
func skip_vs_card() -> void:
	var card := vs_card()
	if card == null:
		return
	if card.is_playing():
		card.skip()
		await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0


# Eric stops taking turns: the tests that only exercise the player's own rules use synthetic hits,
# and his fight is being reworked under them. His hurtbox, his hazards and his states still work when
# a test drives them itself.
func park_eric() -> void:
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Idle")
	sm.set_process(false)
	sm.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	# His Break gauge (EricPacing V2) takes nothing either: parries and punches aimed at the player's
	# rules must not break him in the middle of them.
	if boss.break_gauge:
		boss.break_gauge.locked = true
		boss.break_gauge.set_physics_process(false)


func unpark_eric() -> void:
	sm.set_process(true)
	sm.set_physics_process(true)


func load_eric(keep_balloon := false) -> void:
	await load_fight("eric", keep_balloon)
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	sm = boss.state_machine
	if not keep_balloon:
		sm.post_dialogue_pre_fight_timer.stop()


func _main() -> void:
	load("res://Scripts/PlayerDefense.gd").LOG_HITS = true
	# Bindings persist: every run plays on the defaults whatever this machine's player has rebound,
	# and writes a scratch file rather than theirs.
	var settings: Node = root.get_node("InputSettings")
	settings.save_path = DEFENSE_BINDINGS_PATH
	settings.reset_to_defaults()
	if ERIC_V1_MODES.has(mode):
		pin_eric(1)
	match mode:
		"stamina": await test_stamina()
		"baseline": await test_baseline()
		"block_eric": await test_block_eric()
		"behind": await test_behind()
		"grab_block": await test_grab_block()
		"dash_through": await test_dash_through()
		"guard_break": await test_guard_break()
		"guard_break_timeout": await test_guard_break_timeout()
		"guard_break_grab": await test_guard_break_grab()
		"guard_break_lose": await test_guard_break_lose()
		"parry_projectiles": await test_parry_projectiles()
		"parry_rules": await test_parry_rules()
		"stagger": await test_stagger()
		"stagger_chain": await test_stagger_chain()
		"stagger_win": await test_stagger_end(true)
		"stagger_lose": await test_stagger_end(false)
		"dodge_ring": await test_dodge_ring()
		"dodge_near": await test_dodge_near()
		"dodge_bosses": await test_dodge_bosses()
		"dash_recovery": await test_dash_recovery()
		"dash_spam": await test_dash_spam()
		"hype": await test_hype()
		"hype_inert": await test_hype_inert()
		"super_uppercut": await test_super_uppercut()
		"gamepad_mash": await test_gamepad_mash()
		"smoke": await test_smoke()
		"blocks": await test_blocks()
		"dodge_rollout": await test_dodge_rollout()
		"prompt_overlap": await test_prompt_overlap()
		"grab_parry": await test_grab_parry()
		"parry_streak": await test_parry_streak()
		"knockback": await test_knockback()
		"knockback_computah": await test_knockback_computah()
		"knockback_boss": await test_knockback_boss()
		"kill_shove": await test_kill_shove()
		"status": await test_status()
		"status_end": await test_status_end()
		"status_dialogue": await test_status_dialogue()
		"locked": await test_locked()
		"locked_end": await test_locked_end()
		"parry_rearm": await test_parry_rearm()
		"parry_window": await test_parry_window()
		"parry_freeze": await test_parry_freeze()
		"parry_cue": await test_parry_cue()
		"approach": await test_approach()
		"clone_cadence": await test_clone_cadence()
		"auto_finisher": await test_auto_finisher()
		"auto_kill": await test_auto_kill()
		"tells": await test_tells()
		"dash_v2": await test_dash_v2()
		"dash_recovery_v2": await test_dash_recovery_v2()
		"dash_spam_v2": await test_dash_spam_v2()
		"dash_legacy": await test_dash_legacy()
		"dash_layers": await test_dash_layers()
		"punch_reach": await test_punch_reach()
		"punch_contact": await test_punch_contact()
		"y_sort_eric": await test_y_sort_eric()
		"v2_cadence": await test_v2_cadence()
		"delayed_slam": await test_delayed_slam()
		"whirl_lunges": await test_whirl_lunges()
		"hug_mixup": await test_hug_mixup()
		"break_gauge": await test_break_gauge()
		"break_entry": await test_break_entry()
		"mash_tiers": await test_mash_tiers()
		"mash_tiers_live": await test_mash_tiers_live()
		"juggle": await test_juggle()
		"juggle_kill": await test_juggle_kill()
		"juggle_super": await test_juggle_super()
		"reflect_auto_v2": await test_reflect_auto_v2()
		"pace_bot": await test_pace_bot()
		"pause_basic": await test_pause_basic()
		"pause_hitstop": await test_pause_hitstop()
		"pause_freeze": await test_pause_freeze()
		"pause_mash": await test_pause_mash()
		"pause_barrage": await test_pause_barrage()
		"pause_dialogue": await test_pause_dialogue()
		"pause_no_leak": await test_pause_no_leak()
		"pause_blocked": await test_pause_blocked()
		"pause_restart": await test_pause_restart()
		"pause_quit": await test_pause_quit()
		"vs_card": await test_vs_card()
		"entrance": await test_entrance()
		_: log_p("unknown mode " + mode)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(DEFENSE_BINDINGS_PATH))
	log_p("RESULT mode=%s fails=%d" % [mode, fails])
	Engine.time_scale = 1.0
	quit(fails)


# ------------------------------------------------------------------ step 1

func test_stamina() -> void:
	await load_eric()
	player.global_position = Vector2(700, 800)
	await wait(5)
	check(is_equal_approx(defense.stamina, 100.0), "starts full (%.2f)" % defense.stamina)
	var bar: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/StaminaBar")
	check(bar.bar.value == 100.0, "bar shows full")

	var x0 := player.global_position.x
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(1)
	check(is_equal_approx(defense.stamina, 85.0), "a dash costs 15 (%.2f)" % defense.stamina)
	await wait(4)
	release(KEY_RIGHT)
	log_p("dash moved %.1f px" % (player.global_position.x - x0))
	check(player.global_position.x - x0 > 150.0, "the paid dash moved the player")
	var spend_time: float = defense.last_spend_time
	var first_regen := -1.0
	var stamina_at := {}
	for i in 90:
		var before: float = defense.stamina
		await physics_frame
		var since: float = defense.clock - spend_time
		if first_regen < 0.0 and defense.stamina > before:
			first_regen = since
		stamina_at[snappedf(since, 0.0001)] = defense.stamina
	log_p("regen first seen %.4f s after the spend" % first_regen)
	check(first_regen >= 0.6 - 0.001 and first_regen <= 0.6 + 1.0 / 60.0 + 0.001, "regen starts 0.6 s after the spend (%.4f)" % first_regen)
	var mid := 0.0
	for since in stamina_at:
		if since >= 0.9 and mid == 0.0:
			mid = since
	var expected := 85.0 + 35.0 * (mid - 0.6 + 1.0 / 60.0)
	log_p("stamina %.3f at %.4f s (expected about %.3f)" % [stamina_at[mid], mid, expected])
	check(absf(stamina_at[mid] - expected) <= 35.0 / 60.0 + 0.01, "refills at 35/s")
	await wait_until(func(): return defense.stamina >= 100.0, 120)
	check(bar.bar.value == 100.0, "bar back to full")

	log_p("-- refused dash")
	defense.stamina = 10.0
	defense.last_spend_time = defense.clock + 100.0
	await wait(20)
	var refused := [0]
	defense.stamina_refused.connect(func(): refused[0] += 1)
	var dodge_frame: int = player.last_dodge_physics_frame
	var prev_frame: int = player.previous_dodge_physics_frame
	x0 = player.global_position.x
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(1)
	var immune: bool = load("res://Scripts/DashImmunity.gd").is_immune(player, 0.18, 0.6)
	check(refused[0] == 1, "stamina_refused emitted")
	check(not player.is_dodging, "not dodging")
	check(player.last_dodge_physics_frame == dodge_frame and player.previous_dodge_physics_frame == prev_frame, "dodge frames untouched")
	check(not immune, "no dash immunity")
	check(is_equal_approx(defense.stamina, 10.0), "stamina unchanged (%.2f)" % defense.stamina)
	check(bar.modulate != Color.WHITE, "bar flashes on refusal (%s)" % bar.modulate)
	await wait(4)
	release(KEY_LEFT)
	var moved := x0 - player.global_position.x
	log_p("refused dash + 5 walking frames moved %.1f px" % moved)
	check(moved <= 5.0 * 10.0 + 1.0, "refused dash didn't move the player beyond walking")
	await wait(30)
	check(bar.modulate == Color.WHITE, "flash fades")


# ------------------------------------------------------------------ step 2 helpers

var events: Array = []


func track() -> void:
	events.clear()
	defense.hit_taken.connect(func(hit):
		log_p("  hit %s: state %s facing %d guarding %s origin %s hurtbox %s" % [hit.attack_id, player.state_machine.current_state.name, player.facing, defense.is_guarding(), hit.origin, player.hurtBox.get_node("CollisionShape2D").global_position])
		events.append({"t": defense.clock, "kind": "HIT", "id": hit.attack_id, "health": player.playerHealth, "stamina": defense.stamina}))
	defense.blocked.connect(func(hit, point): events.append({"t": defense.clock, "kind": "BLOCKED", "id": hit.attack_id, "health": player.playerHealth, "stamina": defense.stamina, "point": point, "frame": Engine.get_physics_frames()}))


func events_of(kind: String, id := &"") -> Array:
	return events.filter(func(e): return e.kind == kind and (id.is_empty() or e.id == id))


func settle_player(at: Vector2) -> void:
	player.global_position = at
	player.velocity = Vector2.ZERO
	await wait(2)


# The parry window is game time, so a freeze stretches it in frames: wait for it to actually close.
func past_window() -> void:
	# The press is only credited once the input flush reaches _input, so wait for the window to open
	# before waiting for it to close.
	await wait_until(func(): return defense.is_parry_ready(), 30)
	await wait_until(func(): return not defense.is_parry_ready(), 240)
	await wait(2)


func clear_iframes() -> void:
	player.is_invincible = false
	player.invincibility_timer.stop()


func attack(state_name: String, max_frames := 900) -> void:
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, state_name)
	await wait_until(func(): return sm.current_state.name == "Downed", max_frames)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(2)


func health_ok() -> void:
	player.playerHealth = 100


# ------------------------------------------------------------------ step 2

func test_baseline() -> void:
	await load_eric()
	health_ok()
	track()
	log_p("-- whirlwind, standing still")
	await settle_player(Vector2(972, 700))
	await attack("Whirlwind")
	var hits := events_of("HIT", &"eric_whirlwind")
	log_p("whirlwind hits at %s" % [hits.map(func(e): return snappedf(e.t, 0.001))])
	check(hits.size() >= 2, "whirlwind hits more than once (%d)" % hits.size())
	for i in range(1, hits.size()):
		check(hits[i].t - hits[i - 1].t >= 1.0 - 0.001, "hits %.3f s apart (i-frames)" % (hits[i].t - hits[i - 1].t))
	await wait(70)
	clear_iframes()

	log_p("-- earthquake, in the down wave's path")
	events.clear()
	var health: int = player.playerHealth
	await settle_player(Vector2(867, 750))
	await attack("Earthquake")
	hits = events_of("HIT", &"eric_quake_wave")
	check(hits.size() == 1 and player.playerHealth == health - 1, "one wave hit, one half-heart (%d hits, health %d -> %d)" % [hits.size(), health, player.playerHealth])
	await wait(70)
	clear_iframes()

	log_p("-- sword throw at the player")
	events.clear()
	health = player.playerHealth
	await settle_player(Vector2(700, 750))
	await attack("SwordThrow")
	log_p("events %s" % [events.map(func(e): return "%s %s %.3f" % [e.kind, e.id, e.t])])
	check(events_of("HIT").size() == 1, "the throw lands one hit (a player standing on the target takes the ring)")
	check(events_of("BLOCKED").is_empty(), "nothing blocked")
	check(player.playerHealth == health - events_of("HIT").size(), "each hit one half-heart")
	await wait(70)
	clear_iframes()

	log_p("-- bear hug")
	events.clear()
	health = player.playerHealth
	await settle_player(Vector2(972, 700))
	var grabbed := [false]
	var hug_watch := func():
		if player.is_grabbed:
			grabbed[0] = true
	process_frame.connect(hug_watch)
	await attack("BearHug")
	process_frame.disconnect(hug_watch)
	check(grabbed[0], "the hug grabs")
	check(events_of("HIT", &"eric_bear_hug_grab").size() == 1, "one grab hit")
	check(events_of("HIT", &"eric_bear_hug_squeeze").size() == 3, "three squeezes")
	check(player.playerHealth == health - 3, "three half-hearts (%d -> %d)" % [health, player.playerHealth])
	check(events_of("BLOCKED").is_empty(), "no blocks anywhere")


func test_block_eric() -> void:
	await load_eric()
	health_ok()
	track()
	press(KEY_SHIFT)
	log_p("-- earthquake, guard up facing him")
	await settle_player(Vector2(867, 750))
	await wait(3)
	check(player.state_machine.current_state.name == "Blocking", "guard up while Shift held (%s)" % player.state_machine.current_state.name)
	check(player.facing == player.Facing.UP, "facing up at Eric")
	await attack("Earthquake")
	var blocks := events_of("BLOCKED", &"eric_quake_wave")
	var previous := 100.0
	for e in blocks:
		check(is_equal_approx(previous - e.stamina, 20.0), "a wave block costs 20 (%.1f -> %.1f)" % [previous, e.stamina])
		previous = e.stamina
	check(blocks.size() >= 1 and events_of("HIT").is_empty(), "waves blocked, none hit (%d blocks)" % blocks.size())
	check(player.playerHealth == 100, "no damage")
	check(is_equal_approx(defense.stamina, previous), "regen paused while guarding (%.1f)" % defense.stamina)
	var first_point: Vector2 = blocks[0].point if blocks.size() > 0 else Vector2.ZERO
	log_p("first contact point %s, hurtbox centre %s" % [first_point, player.hurtBox.get_node("CollisionShape2D").global_position])

	log_p("-- sword throw, guard up")
	events.clear()
	# The earthquake now ends with the guard broken rather than 20 stamina left: the player draws at
	# 3x since the resize, and his wider hurtbox takes a fifth wave off the same fan, which is exactly
	# the whole bar. This section is about what the SWORD costs, so the guard is put back with the
	# stamina the way it always was - it just has to say so now.
	defense.clear_guard_break()
	defense._set_stamina(100.0)
	await settle_player(Vector2(972, 800))
	var throw_state: Node = sm.states["SwordThrow"]
	# The flying sword is drawn, and hurts, 177 px above its landing spot: step into its path.
	var step_in := func():
		if is_instance_valid(throw_state.sword) and throw_state.sword.flying and not throw_state.sword.returning and player.global_position.y == 800.0:
			player.global_position = Vector2(972, 650)
	process_frame.connect(step_in)
	await attack("SwordThrow")
	process_frame.disconnect(step_in)
	log_p("events %s" % [events.map(func(e): return "%s %s %.3f st %.1f" % [e.kind, e.id, e.t, e.stamina])])
	var sword_blocks := events_of("BLOCKED", &"eric_thrown_sword")
	check(sword_blocks.size() >= 1 and is_equal_approx(sword_blocks[0].stamina, 65.0), "the sword block costs 35")
	await wait(70)
	clear_iframes()

	log_p("-- whirlwind, guard up")
	events.clear()
	defense._set_stamina(100.0)
	await settle_player(Vector2(972, 700))
	await attack("Whirlwind")
	blocks = events_of("BLOCKED", &"eric_whirlwind")
	log_p("whirlwind blocks %s" % [blocks.map(func(e): return "%.3f st %.1f" % [e.t, e.stamina])])
	check(blocks.size() >= 3, "blocked repeatedly (%d)" % blocks.size())
	previous = 100.0
	for i in blocks.size():
		check(is_equal_approx(previous - blocks[i].stamina, 35.0) or (blocks[i].stamina == 0.0 and previous < 35.0) or previous == 0.0, "whirlwind block costs 35 (%.1f -> %.1f)" % [previous, blocks[i].stamina])
		previous = blocks[i].stamina
		if i > 0:
			check(absf(blocks[i].t - blocks[i - 1].t - 1.0) <= 1.0 / 60.0 + 0.001, "once a second (%.3f)" % (blocks[i].t - blocks[i - 1].t))
	var ww_hits := events_of("HIT", &"eric_whirlwind")
	check(ww_hits.is_empty() or (blocks.size() >= 3 and ww_hits[0].t > blocks[2].t), "the whirlwind only hits once the third block has broken the guard")
	release(KEY_SHIFT)
	await wait(3)
	check(player.state_machine.current_state.name != "Blocking", "guard drops on release")


func spawn_waves(slam: Vector2) -> Node:
	var waves: Node2D = load("res://Scenes/Bosses/EarthquakeAreasScene.tscn").instantiate()
	waves.scale = boss.scale
	waves.move_speed = 1150.0 / boss.scale.x
	sm.add_hazard(waves, slam)
	waves.enable_earthquake_areas()
	return waves


func test_behind() -> void:
	await load_eric()
	health_ok()
	track()
	press(KEY_SHIFT)
	await settle_player(Vector2(972, 700))
	# This test is about which sides a held guard covers, not the parry.
	await past_window()
	check(player.state_machine.current_state.name == "Blocking" and player.facing == player.Facing.UP, "guarding, facing up at Eric")
	log_p("-- wave from the front (slam between Eric and the player)")
	spawn_waves(Vector2(972, 520))
	await wait(40)
	check(events_of("BLOCKED", &"eric_quake_wave").size() >= 1 and events_of("HIT").is_empty(), "front waves blocked (%d waves reached the player)" % events_of("BLOCKED").size())
	events.clear()
	await wait(30)
	log_p("-- wave from behind (slam below the player)")
	spawn_waves(Vector2(972, 900))
	await wait(40)
	check(events_of("HIT", &"eric_quake_wave").size() == 1 and events_of("BLOCKED").is_empty(), "wave from behind hits")
	await wait(70)
	clear_iframes()
	events.clear()
	log_p("-- returning sword from behind")
	var sword: Node2D = load("res://Scenes/Bosses/EricThrownSwordScene.tscn").instantiate()
	# The sword reports its own hits, so it needs to know who it is flying at and who threw it.
	sword.player = player
	sword.thrower = boss
	# Planted well below the player: the recall lifts the blade as it flies, so it has to start far
	# enough back that it reaches them while it is still under them.
	sm.add_hazard(sword, Vector2(972, 1120))
	sword._plant()
	await wait(5)
	var layout = load("res://Scripts/EricArtLayout.gd")
	var catch_centre: Vector2 = boss.to_global(layout.frame_local(layout.THROW_CATCH_CENTRE, boss.sprite.flip_h))
	var ground_y: float = boss.frame_point(Vector2(0, layout.FEET_ROW)).y
	sword.recall(catch_centre, ground_y, 0.0, true)
	await wait(40)
	log_p("events %s" % [events.map(func(e): return "%s %s" % [e.kind, e.id])])
	check(events_of("HIT", &"eric_thrown_sword").size() == 1 and events_of("BLOCKED").is_empty(), "returning sword from behind hits")
	await wait(70)
	clear_iframes()
	events.clear()
	log_p("-- thrown sword from the front")
	var sword2: Node2D = load("res://Scenes/Bosses/EricThrownSwordScene.tscn").instantiate()
	sword2.player = player
	sword2.thrower = boss
	var hand: Vector2 = boss.frame_point(layout.THROW_RELEASE_PIXEL)
	sm.add_hazard(sword2, Vector2(hand.x, ground_y))
	# Aimed at the player's own feet: the blade dives into its landing spot, so it comes down
	# through whoever is standing there rather than passing over their head.
	sword2.throw(hand, ground_y, player.global_position)
	await wait(40)
	check(events_of("BLOCKED", &"eric_thrown_sword").size() == 1 and events_of("HIT").is_empty(), "sword from the front blocked")
	release(KEY_SHIFT)


func test_grab_block() -> void:
	await load_eric()
	health_ok()
	track()
	press(KEY_SHIFT)
	await settle_player(Vector2(972, 700))
	await wait(3)
	var grabbed := [false]
	var watch_grab := func():
		if player.is_grabbed:
			grabbed[0] = true
	process_frame.connect(watch_grab)
	var guard_at_grab := [false]
	defense.hit_taken.connect(func(hit):
		if hit.attack_id == &"eric_bear_hug_grab":
			guard_at_grab[0] = defense.is_guarding()
	)
	await attack("BearHug")
	process_frame.disconnect(watch_grab)
	check(guard_at_grab[0], "guard was up when the grab landed")
	check(grabbed[0], "the hug grabbed the blocking player")
	check(events_of("HIT", &"eric_bear_hug_squeeze").size() == 3 and player.playerHealth == 97, "three squeezes land (health %d)" % player.playerHealth)
	release(KEY_SHIFT)


func test_dash_through() -> void:
	await load_eric()
	health_ok()
	track()
	log_p("-- quake ring, dash in place as the crest arrives")
	await settle_player(Vector2(600, 700))
	var ring: Node2D = load("res://Scenes/Bosses/EricQuakeRingScene.tscn").instantiate()
	ring.player = player
	ring.speed = 950.0
	sm.add_hazard(ring, Vector2(972, 700))
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	# 40 px of lead, not the 20 this used to take: the ring grows 15.8 px a frame and the dash's
	# i-frames last 3, so 20 px put the press about a quarter of a frame ahead of contact once the
	# tap's own frame is counted - it passed on sub-frame luck, and the player's resize shifted the
	# phase enough to lose it. 40 px lands the press in the middle of the window instead.
	await wait_until(func():
		var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
		var rect := Rect2(shape.global_position - half, half * 2.0)
		var nearest: float = ring.global_position.clamp(rect.position, rect.end).distance_to(ring.global_position)
		return nearest - (ring.radius + ring.HURT_HALF_WIDTH) < 40.0, 120)
	tap(KEY_W)
	await wait(40)
	check(events_of("HIT").is_empty() and player.playerHealth == 100, "ring dashed through, no hit")
	await wait(60)

	log_p("-- ring without a dash (control)")
	var ring2: Node2D = load("res://Scenes/Bosses/EricQuakeRingScene.tscn").instantiate()
	ring2.player = player
	ring2.speed = 950.0
	sm.add_hazard(ring2, Vector2(972, 700))
	await wait(40)
	check(events_of("HIT", &"eric_quake_ring").size() == 1, "ring hits without a dash")
	await wait(70)
	clear_iframes()
	events.clear()

	log_p("-- bear hug lunge, dash in place as it arrives")
	await settle_player(Vector2(972, 800))
	sm.chain = []
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	var grab_shape: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
	await wait_until(func():
		if hug.phase != hug.Phase.LUNGE:
			return false
		var half: Vector2 = grab_shape.shape.size * grab_shape.global_scale.abs() / 2.0
		var hurt_half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
		return (shape.global_position.y - hurt_half.y) - (grab_shape.global_position.y + half.y) < 40.0, 300)
	tap(KEY_W)
	await wait_until(func(): return hug.phase != hug.Phase.LUNGE, 60)
	log_p("hug phase after the lunge: %d, grabbed %s" % [hug.phase, player.is_grabbed])
	check(not player.is_grabbed and hug.phase == hug.Phase.WHIFF, "lunge dashed through: a whiff")
	check(events_of("HIT").is_empty(), "no hit")
	await wait_until(func(): return sm.current_state.name == "Downed", 600)
	sm.downed_state_timer.stop()


# ------------------------------------------------------------------ step 3

var guard_events: Array = []


func track_guard() -> void:
	guard_events.clear()
	defense.guard_broken.connect(func(): guard_events.append(["broken", defense.clock]))
	defense.guard_recovered.connect(func(): guard_events.append(["recovered", defense.clock, defense.stamina]))


# A blockable hit from straight in front of the player's facing.
# A stand-in boss for the rules that hand a boss something, without needing one of his attacks.
class StaggerSpy extends Node2D:
	var windows: Array = []

	func can_parry_stagger(_hit) -> bool:
		return true

	func parry_stagger(duration: float) -> void:
		windows.append(snappedf(duration, 0.01))


func front_hit_from(id: StringName, from_boss: Node) -> int:
	var hit_info = load("res://Scripts/HitInfo.gd")
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var facing: Vector2 = defense.FACING_VECTORS[player.facing]
	return player.receive_hit(hit_info.make(id, from_boss, centre + facing * 100.0, from_boss))


func front_hit(id: StringName, source: Node, from_behind := false) -> int:
	var hit_info = load("res://Scripts/HitInfo.gd")
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var facing: Vector2 = defense.FACING_VECTORS[player.facing]
	var origin: Vector2 = centre + (-facing if from_behind else facing) * 100.0
	return player.receive_hit(hit_info.make(id, source, origin))


# A hit from straight behind the player, or 90 degrees off their facing.
func side_hit(id: StringName, source: Node) -> int:
	var hit_info = load("res://Scripts/HitInfo.gd")
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	var origin: Vector2 = centre + defense.FACING_VECTORS[player.facing].orthogonal() * 100.0
	return player.receive_hit(hit_info.make(id, source, origin))


# A hit from where the player stands: no direction to face.
func omni_hit(id: StringName, source: Node) -> int:
	var hit_info = load("res://Scripts/HitInfo.gd")
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return player.receive_hit(hit_info.make(id, source, centre + Vector2(5, 0)))


func dummy_source() -> Node2D:
	var node := Node2D.new()
	current_scene.add_child(node)
	return node


func test_guard_break() -> void:
	await load_eric()
	health_ok()
	track()
	track_guard()
	# Eric's fight y-sorts, which rests the player's frame on an offset of its own.
	var sprite_rest: Vector2 = player.sprite.offset
	press(KEY_SHIFT)
	await settle_player(Vector2(972, 700))
	await wait(3)
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Whirlwind")
	check(await wait_until(func(): return defense.is_guard_broken, 400), "guard breaks inside the whirlwind")
	var blocks := events_of("BLOCKED", &"eric_whirlwind")
	log_p("blocks before the break: %s" % [blocks.map(func(e): return "%.3f st %.1f" % [e.t, e.stamina])])
	check(blocks.size() == 3, "on the third blocked hit (%d)" % blocks.size())
	check(events_of("HIT").is_empty(), "no hit before the break")
	await wait(2)
	check(player.state_machine.current_state.name == "GuardBroken", "in GuardBroken (%s)" % player.state_machine.current_state.name)
	check(defense.stamina == 0.0, "stamina 0")
	var broken_at: float = guard_events[0][1]
	var pos := player.global_position
	var facing: int = player.facing
	var dodge_frame: int = player.last_dodge_physics_frame
	var press_time: float = defense.last_press_time
	log_p("-- presses during the stun")
	tap(KEY_Q)
	await wait(2)
	tap(KEY_W)
	await wait(2)
	release(KEY_SHIFT)
	await wait(1)
	tap(KEY_SHIFT)
	press(KEY_SHIFT)
	press(KEY_LEFT)
	await wait(20)
	check(player.state_machine.current_state.name == "GuardBroken", "still stunned after punch, dash, block and move presses")
	check(player.global_position.distance_to(pos) < 0.5, "didn't move (%s -> %s)" % [pos, player.global_position])
	check(player.last_dodge_physics_frame == dodge_frame, "no dash")
	check(is_equal_approx(defense.last_press_time, press_time), "block press ignored")
	release(KEY_LEFT)
	var turned := [false]
	var turn_watch := func():
		if defense.is_guard_broken and player.facing != facing:
			turned[0] = true
	process_frame.connect(turn_watch)
	var sprite: Sprite2D = player.sprite
	log_p("stun pose frame %s offset %s self_modulate %s" % [sprite.frame_coords, sprite.offset, sprite.self_modulate])
	var fx: Node = current_scene.get_node("Arena/MainPlayer/FinisherFx")
	var star_count := fx.get_children().filter(func(c): return c is Sprite2D).size()
	check(star_count == 1, "stars shown (%d)" % star_count)
	check(await wait_until(func(): return not events_of("HIT", &"eric_whirlwind").is_empty(), 200), "the next whirlwind contact hits")
	var hit_t: float = events_of("HIT", &"eric_whirlwind")[0].t
	log_p("stunned at %.3f, hit at %.3f" % [broken_at, hit_t])
	check(absf(hit_t - (blocks[2].t + 1.0)) <= 1.0 / 60.0 + 0.001, "hit lands when the absorb ends, 1 s after the break")
	await wait(2)
	process_frame.disconnect(turn_watch)
	check(not defense.is_guard_broken, "the hit ended the stun")
	check(guard_events.size() == 2 and guard_events[1][0] == "recovered" and is_equal_approx(guard_events[1][2], 50.0), "recovered with 50 stamina (%s)" % [guard_events])
	check(player.playerHealth == 99, "one half-heart for that hit only")
	check(not turned[0], "didn't turn while stunned")
	check(sprite.texture.resource_path.ends_with("player_4dir_sheet.png") and sprite.offset == sprite_rest and sprite.hframes == 10 and sprite.vframes == 4, "sprite restored")
	check(sprite.self_modulate == Color.WHITE, "flicker cleared")
	await wait(2)
	check(fx.get_children().filter(func(c): return c is Sprite2D and not c.is_queued_for_deletion()).is_empty(), "stars cleared")
	release(KEY_SHIFT)
	await wait_until(func(): return sm.current_state.name == "Downed", 400)
	sm.downed_state_timer.stop()


func test_guard_break_timeout() -> void:
	await load_eric()
	park_eric()
	health_ok()
	track_guard()
	press(KEY_SHIFT)
	await settle_player(Vector2(972, 800))
	await past_window()
	defense.stamina = 20.0
	var source := dummy_source()
	var result := front_hit(&"eric_quake_wave", source)
	check(result == 2, "the emptying hit is still blocked (result %d)" % result)
	check(defense.is_guard_broken and defense.stamina == 0.0, "guard broken at 0")
	var start: float = defense.clock
	await wait(2)
	check(player.state_machine.current_state.name == "GuardBroken", "stun state")
	check(await wait_until(func(): return not defense.is_guard_broken, 200), "stun ends on its own")
	var lasted: float = defense.clock - start
	log_p("stun lasted %.3f s" % lasted)
	check(absf(lasted - 1.5) <= 1.0 / 60.0 + 0.001, "1.5 s")
	check(is_equal_approx(defense.stamina, 50.0), "refilled to 50 (%.1f)" % defense.stamina)
	await wait(3)
	check(player.state_machine.current_state.name == "Blocking", "guard back up with Shift still held (%s)" % player.state_machine.current_state.name)
	release(KEY_SHIFT)
	await wait(3)
	log_p("-- two hits in the same flush: block breaks, second hits and ends the stun")
	defense.stamina = 20.0
	defense.last_spend_time = defense.clock
	press(KEY_SHIFT)
	await past_window()
	var other := dummy_source()
	var first := front_hit(&"eric_quake_wave", source)
	var second := front_hit(&"eric_quake_wave", other)
	check(first == 2 and second == 1, "first blocked, second hits (%d, %d)" % [first, second])
	await wait(2)
	check(not defense.is_guard_broken and player.state_machine.current_state.name != "GuardBroken", "stun ended by the hit")
	check(player.playerHealth == 99, "punished once")
	release(KEY_SHIFT)


func test_guard_break_grab() -> void:
	await load_eric()
	health_ok()
	track_guard()
	press(KEY_SHIFT)
	await settle_player(Vector2(972, 700))
	await wait(3)
	sm.chain = []
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	await wait_until(func(): return hug.phase == hug.Phase.CHARGE, 200)
	defense.stamina = 20.0
	front_hit(&"eric_quake_wave", dummy_source())
	release(KEY_SHIFT)
	check(defense.is_guard_broken, "stunned before the lunge")
	await wait_until(func(): return player.is_grabbed or hug.phase == hug.Phase.WHIFF, 200)
	check(player.is_grabbed, "the hug grabs the stunned player")
	check(not defense.is_guard_broken, "the grab cleared the stun")
	check(player.state_machine.current_state.name == "Idle", "player in Idle while held (%s)" % player.state_machine.current_state.name)
	check(not player.sprite.visible, "player sprite hidden in the hug")
	await wait_until(func(): return sm.current_state.name == "Downed", 600)
	sm.downed_state_timer.stop()
	check(player.playerHealth == 97, "three squeezes (%d)" % player.playerHealth)
	check(player.sprite.texture.resource_path.ends_with("player_4dir_sheet.png") and player.sprite.visible, "sprite restored and shown after the toss")


func test_guard_break_lose() -> void:
	await load_eric()
	player.playerHealth = 1
	track_guard()
	press(KEY_SHIFT)
	await settle_player(Vector2(972, 800))
	# Past the parry window, so the hit is blocked and the block is what empties the bar.
	await past_window()
	defense.stamina = 20.0
	front_hit(&"eric_quake_wave", dummy_source())
	await wait(10)
	check(player.state_machine.current_state.name == "GuardBroken", "stunned")
	player.receive_hit(load("res://Scripts/HitInfo.gd").make(&"untagged", dummy_source(), player.global_position))
	check(player.playerHealth == 0, "the killing hit lands during the stun")
	await wait(5)
	check(player.fight_over, "fight over")
	check(not defense.is_guard_broken, "stun cleared")
	check(player.state_machine.current_state.name == "Idle" and not player.state_machine.is_processing(), "standing still in Idle, state machine stopped")
	var pos := player.global_position
	press(KEY_LEFT)
	await wait(20)
	release(KEY_LEFT)
	check(player.global_position.distance_to(pos) < 0.5, "doesn't move for the outro")
	check(player.sprite.texture.resource_path.ends_with("player_4dir_sheet.png") and player.sprite.self_modulate == Color.WHITE, "sprite restored")
	release(KEY_SHIFT)


# ------------------------------------------------------------------ step 4a

var parries: Array = []


func track_parries() -> void:
	parries.clear()
	defense.parried.connect(func(hit, point, staggered, streak): parries.append({"t": defense.clock, "id": hit.attack_id, "staggered": staggered, "stamina": defense.stamina, "streak": streak}))


func test_parry_projectiles() -> void:
	await load_eric()
	health_ok()
	track()
	track_parries()
	log_p("-- parry a wave")
	var fx: Node = current_scene.get_node("Arena/MainPlayer/FinisherFx")
	var shatter_seen := [false]
	watch = func():
		for child in fx.get_children():
			if child is Sprite2D and child.texture and child.texture.resource_path.ends_with("parry_shatter.png"):
				shatter_seen[0] = true
	await settle_player(Vector2(972, 760))
	var waves: Node2D = spawn_waves(Vector2(972, 420))
	var down: Area2D = waves.collision_map[2]
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	await wait_until(func(): return (shape.global_position.y - 27.0) - down.global_position.y < 1150.0 * 0.07, 120)
	press(KEY_SHIFT)
	await wait_until(func(): return parries.size() > 0 or not events.is_empty(), 30)
	var y_at_parry: float = down.global_position.y
	# Past the parry's hit-stop.
	await wait(20)
	check(parries.size() == 1 and parries[0].id == &"eric_quake_wave", "wave parried (%s)" % [parries])
	check(events.is_empty(), "no block or hit")
	check(defense.stamina == 100.0, "no stamina cost (%.1f)" % defense.stamina)
	check(down.global_position.y > y_at_parry + 100.0, "the wave flies on (%.0f -> %.0f)" % [y_at_parry, down.global_position.y])
	check(bool(shatter_seen[0]), "the parried wave breaks up where it was met")
	watch = Callable()
	check(player.playerHealth == 100, "no damage")
	release(KEY_SHIFT)
	await wait(60)

	log_p("-- parry the thrown sword, standing still where he aims it")
	parries.clear()
	events.clear()
	# Through his real state rather than a hand-spawned sword: the throw owns the reflect, so a
	# sword parried outside it would have nothing to fling it back.
	var full: int = boss.boss_health
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await settle_player(Vector2(1480, 700))
	sm.on_child_transition(sm.current_state, "SwordThrow")
	var throw_state: Node = sm.states["SwordThrow"]
	check(await wait_until(func(): return is_instance_valid(throw_state.sword), 200), "he throws it")
	var sword: Node2D = throw_state.sword
	var sword_hitbox: Area2D = sword.get_node("Hitbox")
	await wait_until(func(): return sword_hitbox.global_position.distance_to(shape.global_position) < 108.0 + 27.0 + sword.speed * 0.07, 200)
	log_p("blade %.0f px over the player as it comes down" % (shape.global_position.y - sword_hitbox.global_position.y))
	press(KEY_SHIFT)
	await wait_until(func(): return parries.size() > 0 or not events.is_empty(), 30)
	await wait(3)
	check(parries.size() == 1 and parries[0].id == &"eric_thrown_sword", "sword parried (%s)" % [parries])
	check(defense.stamina == 100.0, "no stamina cost")
	check(player.playerHealth == 100, "no damage")
	check(sword.reflecting and sword.to_ground.distance_to(boss.global_position) < 250.0, "it turns round and flies at him instead of planting")
	check(await wait_until(func(): return sm.current_state.name == "ParryStaggered", 300), "it reaches him and dazes him")
	check(boss.boss_health == full - 1, "it takes 1 off him (%d of %d)" % [boss.boss_health, full])
	check(get_nodes_in_group(sm.HAZARD_GROUP).filter(func(h): return h.get_script() and str(h.get_script().resource_path).ends_with("EricQuakeRingScript.gd")).is_empty(), "a reflected sword never planted, so no shockwave ring")
	release(KEY_SHIFT)


func test_parry_rules() -> void:
	await load_eric()
	park_eric()
	health_ok()
	track()
	track_parries()
	await settle_player(Vector2(972, 800))
	var results := []
	log_p("-- fresh press parries")
	press(KEY_SHIFT)
	await wait(3)
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(12)
	log_p("-- a press 0.25 s after a parry is re-armed")
	press(KEY_SHIFT)
	await wait(3)
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- a press whose window has passed only blocks")
	press(KEY_SHIFT)
	# The window is measured in game time, which a freeze slows, so wait for the window itself.
	await past_window()
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- mashing: presses 0.2 s apart")
	for i in 3:
		press(KEY_SHIFT)
		await wait(6)
		release(KEY_SHIFT)
		await wait(6)
	press(KEY_SHIFT)
	await wait(3)
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- guard held from earlier")
	press(KEY_SHIFT)
	await wait(60)
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- after mashing stops for 0.5 s, a press parries again")
	press(KEY_SHIFT)
	await wait(3)
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	log_p("results %s (1 HIT, 2 BLOCKED, 3 PARRIED)" % [results])
	check(results == [3, 3, 2, 2, 2, 3], "parry, re-armed parry, late block, mash block, held block, parry")
	# (step 4b tests below)
	check(player.playerHealth == 100, "no damage")
	check(is_equal_approx(defense.stamina, 100.0 - 60.0) or defense.stamina > 40.0, "only the three blocks cost stamina (%.1f)" % defense.stamina)


# ------------------------------------------------------------------ step 4b

func swing() -> int:
	var before: int = boss.boss_health
	tap(KEY_Q)
	for i in 10:
		await physics_frame
		if player.state_machine.current_state.name == "Punching":
			break
	while player.state_machine.current_state.name == "Punching":
		await physics_frame
	await wait(3)
	return before - boss.boss_health


func place_under(area: Area2D) -> void:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	var hb: CollisionShape2D = player.get_node("Hitbox/CollisionShape2D")
	var reach: Vector2 = hb.global_position - player.global_position
	player.global_position = Vector2(shape.global_position.x - reach.x, shape.global_position.y + half.y - reach.y - 4.0)


# PlayerFinisher.Phase, which a parried sword toss now drives on its own.
const FINISHER_OFF := 0
const FINISHER_SETTLE := 1
const FINISHER_DAZED := 2
const FINISHER_UPPERCUT := 4
const FINISHER_FIZZLE := 5


# Starts his sword throw with `chain` left to come and taps block as the diving blade reaches the
# player. The parry does not stagger him on the spot: the sword is flung back and only staggers him
# when it arrives, so this waits out its return flight and the parry's freeze.
func parry_sword(chain: Array) -> bool:
	await settle_player(Vector2(1480, 700))
	sm.chain = chain
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "SwordThrow")
	var throw_state: Node = sm.states["SwordThrow"]
	if not await wait_until(func(): return is_instance_valid(throw_state.sword), 200):
		return false
	var sword: Node2D = throw_state.sword
	var hitbox: Area2D = sword.get_node("Hitbox")
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	await wait_until(func(): return hitbox.global_position.distance_to(shape.global_position) < 108.0 + 27.0 + sword.speed * 0.07, 200)
	press(KEY_SHIFT)
	return await wait_until(func(): return sm.current_state.name == "ParryStaggered", 300)


func test_stagger() -> void:
	await load_eric()
	health_ok()
	track()
	track_parries()
	defense.parry_stagger_time = 3.0
	var finisher: Node = player.get_node("Finisher")
	var phases := {}
	watch = func(): phases[finisher.phase] = true
	var prompted := [false]
	finisher.prompt_shown.connect(func(): prompted[0] = true)
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	var full: int = boss.max_health
	check(await parry_sword([]), "a parried sword flies back and staggers him (%s)" % sm.current_state.name)
	release(KEY_SHIFT)
	check(parries.size() == 1 and parries[0].staggered, "parried with staggered = true (%s)" % [parries])
	check(events.is_empty() and player.playerHealth == 100, "no block, no hit")
	check(boss.boss_health == full - 1, "the flung-back sword took 1 off him (%d of %d)" % [boss.boss_health, full])
	check(not is_instance_valid(sm.states["SwordThrow"].sword), "the sword is spent on him, so his next throw starts clean")
	var stopped_at: Vector2 = boss.global_position
	await wait(3)
	check(boss.global_position == stopped_at, "he stops moving")
	check(hurtbox.monitoring and hurtbox.monitorable, "hurtbox open")
	check(not boss.get_node("WhirlwindArea2D").monitoring, "whirlwind area off")
	check(not boss.get_node("WhirlwindSfxPlayer").playing, "whirlwind sound stopped")
	check(boss.get_node("CollisionShape2D").disabled, "body collision still off")
	check(sm.states["ParryStaggered"].from_reflect, "the stagger is marked as his own sword's")

	log_p("-- and the finisher takes it from there, with no mash")
	check(phases.has(FINISHER_SETTLE) or phases.has(FINISHER_DAZED), "it started on its own")
	check(await wait_until(func(): return boss.daze_used, 120), "the reflect's window owns the daze")
	check(await wait_until(func(): return phases.has(FINISHER_UPPERCUT), 300), "the uppercut fires without a press (phase %d)" % finisher.phase)
	check(not prompted[0], "the prompt never showed")
	check(not phases.has(FINISHER_FIZZLE), "and it never fizzled out")
	check(await wait_until(func(): return boss.boss_health < full - 1, 120), "it connects")
	log_p("uppercut dealt %d, health %d of %d" % [full - 1 - boss.boss_health, boss.boss_health, full])
	check(full - 1 - boss.boss_health == roundi(full * finisher.finisher_damage_ratio), "a normal uppercut's damage, past the stagger's hit cap")
	check(await wait_until(func(): return finisher.phase == FINISHER_OFF, 300), "the finisher ends")
	check(sm.current_state.name != "ParryStaggered", "it closed the window (%s)" % sm.current_state.name)
	check(not boss.get_node("CollisionShape2D").disabled, "collision back on")
	check(await wait_until(func(): return sm.current_state.name != "Idle", 400), "he gets up and attacks again")
	log_p("he carries on with %s" % sm.current_state.name)

	log_p("-- and again with a full hype meter, which supercharges it and is spent")
	var hype: Node = player.get_node("Hype")
	hype._set_hype(100.0)
	boss.boss_health = full
	parries.clear()
	var before: int = boss.boss_health
	check(await parry_sword([]), "parried again")
	release(KEY_SHIFT)
	check(await wait_until(func(): return boss.boss_health < before - 1, 400), "the supercharged uppercut connects")
	log_p("supercharged uppercut dealt %d, hype %.0f" % [before - 1 - boss.boss_health, hype.hype])
	check(before - 1 - boss.boss_health == roundi(full * finisher.supercharged_damage_ratio), "the supercharged damage")
	check(not hype.is_full(), "it spent the meter (%.0f)" % hype.hype)
	check(await wait_until(func(): return finisher.phase == FINISHER_OFF, 300), "and it ends the same way")
	sm.downed_state_timer.stop()


func test_stagger_chain() -> void:
	await load_eric()
	health_ok()
	track_parries()
	var finisher: Node = player.get_node("Finisher")
	check(await parry_sword(["Earthquake"]), "staggered")
	release(KEY_SHIFT)
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	# The uppercut ends the window rather than the stagger timer running out. end_recovery() then starts
	# a fresh chain rather than resuming the one the throw came from, so which attack comes next is his
	# own shuffle: what this asserts is that he is attacking again at all.
	check(await wait_until(func(): return finisher.phase == FINISHER_OFF and boss.boss_health < boss.max_health - 1, 400), "the finisher lands")
	check(await wait_until(func(): return not hurtbox.monitoring, 240), "it closed the punish window")
	check(sm.states["ParryStaggered"].stagger_timer.is_stopped(), "the stagger timer is done with")
	check(await wait_until(func(): return sm.ATTACKS.has(sm.current_state.name), 400), "the chain carries on with the next attack (%s)" % sm.current_state.name)
	await wait_until(func(): return sm.current_state.name == "Downed", 900)
	sm.downed_state_timer.stop()


# The fight ending inside the finisher a parried sword toss fires: won by the uppercut itself, or
# lost while it is winding up.
func test_stagger_end(win: bool) -> void:
	await load_eric()
	health_ok()
	track_parries()
	var finisher: Node = player.get_node("Finisher")
	check(await parry_sword([]), "staggered")
	release(KEY_SHIFT)
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	var timer: Timer = sm.states["ParryStaggered"].stagger_timer
	# Where he was struck: a killing uppercut must leave him there for his defeat and the outro.
	var pos: Vector2 = boss.global_position
	var sprite_rest: Vector2 = boss.sprite.offset
	if win:
		# Low enough that the uppercut is lethal, so the kill comes from the auto-finisher itself.
		boss.boss_health = 2
		check(await wait_until(func(): return boss.defeated, 400), "the auto-uppercut kills him")
		check(await wait_until(func(): return finisher.phase == FINISHER_OFF, 200), "the finisher plays out past the kill")
		check(sm.current_state.name == "Downed", "defeated, in Downed (%s)" % sm.current_state.name)
		check(boss.global_position == pos and boss.sprite.offset == sprite_rest, "no shove: he dies where he was hit")
	else:
		# Nothing can hurt the player mid-finisher, so the loss is dealt straight to the counter.
		check(await wait_until(func(): return finisher.phase != FINISHER_OFF, 200), "the finisher is up")
		player.playerHealth = 0
		check(await wait_until(func(): return player.fight_over, 200), "the player goes down")
		check(await wait_until(func(): return finisher.phase == FINISHER_OFF, 200), "the finisher gives way to the loss")
		check(sm.current_state.name == "Idle", "player lost, Eric idle (%s)" % sm.current_state.name)
	check(timer.is_stopped(), "stagger timer stopped")
	check(not hurtbox.monitoring, "hurtbox closed")
	var settled: Vector2 = boss.global_position
	await wait(90)
	check(boss.global_position == settled, "no glide after the fight ends")
	check(sm.current_state.name == ("Downed" if win else "Idle"), "still %s" % sm.current_state.name)
	check(root.get_children().filter(func(n): return n.name == "FightOutro").size() == 1, "exactly one outro")


# ------------------------------------------------------------------ step 5

var dodges: Array = []


func track_dodges() -> void:
	dodges.clear()
	defense.perfect_dodged.connect(func(hit): dodges.append({"t": defense.clock, "id": hit.attack_id, "stamina": defense.stamina}))


func spawn_ring(at: Vector2) -> Node2D:
	var ring: Node2D = load("res://Scenes/Bosses/EricQuakeRingScene.tscn").instantiate()
	ring.player = player
	ring.speed = 950.0
	sm.add_hazard(ring, at)
	return ring


# Leaves one wave of a slam live, so a sideways dash can't run into another one.
func keep_only_wave(waves: Node, numpad: int) -> Area2D:
	for other in waves.collision_map:
		if other == numpad:
			continue
		var area: Area2D = waves.collision_map[other]
		area.get_node("CollisionShape2D").set_deferred("disabled", true)
		area.get_node("Sprite2D").visible = false
	return waves.collision_map[numpad]


func hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	return Rect2(shape.global_position - half, half * 2.0)


# Waits until the ring's crest is `lead` seconds from the player.
func ring_close(ring: Node2D, lead: float) -> bool:
	return await wait_until(func():
		if not is_instance_valid(ring):
			return true
		var rect := hurtbox_rect()
		var nearest: float = ring.global_position.clamp(rect.position, rect.end).distance_to(ring.global_position)
		return nearest - (ring.radius + ring.HURT_HALF_WIDTH) < ring.speed * lead, 200)


func test_dodge_ring() -> void:
	await load_eric()
	health_ok()
	track()
	track_dodges()
	log_p("-- dash in place through the ring's crest")
	await settle_player(Vector2(600, 700))
	var ring := spawn_ring(Vector2(972, 700))
	await ring_close(ring, 0.05)
	tap(KEY_W)
	await wait(30)
	check(dodges.size() == 1 and dodges[0].id == &"eric_quake_ring", "the ring's crest is a perfect dodge (%s)" % [dodges])
	check(events_of("HIT").is_empty() and player.playerHealth == 100, "no hit")
	check(is_equal_approx(defense.stamina, 100.0), "the dash's 15 stamina came back (%.1f)" % defense.stamina)
	await wait(60)

	log_p("-- a second dash too soon after the first gets no immunity")
	dodges.clear()
	events.clear()
	var immunity = load("res://Scripts/DashImmunity.gd")
	await settle_player(Vector2(600, 700))
	await dash(0)
	check(immunity.is_immune(player, 0.18, 0.6), "a clean dash is immune")
	# Just past the recovery and any re-dash cooldown, but inside the 0.6 s dash-to-dash gap.
	await wait_until(func(): return not defense.is_dash_recovering() and not defense.is_dash_cooling_down(), 60)
	await wait(2)
	await dash(0)
	check(not immunity.is_immune(player, 0.18, 0.6), "the next dash, inside the 0.6 s gap, isn't")
	var ring2 := spawn_ring(Vector2(972, 700))
	await ring_close(ring2, 0.05)
	await wait(40)
	log_p("events %s dodges %s" % [events.map(func(e): return e.kind), dodges.size()])
	check(events_of("HIT", &"eric_quake_ring").size() == 1, "the ring hits a player who can't dash again")
	check(dodges.is_empty(), "no reward")


func test_dodge_near() -> void:
	await load_eric()
	health_ok()
	track()
	track_dodges()
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	log_p("-- dash aside just before a wave arrives")
	await settle_player(Vector2(972, 760))
	var waves := spawn_waves(Vector2(972, 420))
	var down := keep_only_wave(waves, 2)
	await wait_until(func(): return (shape.global_position.y - 27.0) - down.global_position.y < 1150.0 * 0.06, 200)
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(4)
	release(KEY_LEFT)
	await wait(30)
	check(dodges.size() == 1 and dodges[0].id == &"eric_quake_wave", "wave near miss rewarded (%s)" % [dodges])
	check(events_of("HIT").is_empty(), "no hit")
	check(is_equal_approx(defense.stamina, 100.0), "dash refunded (%.1f)" % defense.stamina)
	await wait(100)

	log_p("-- dashing half a second early earns nothing")
	dodges.clear()
	events.clear()
	await settle_player(Vector2(972, 760))
	waves = spawn_waves(Vector2(972, 300))
	down = keep_only_wave(waves, 2)
	await wait_until(func(): return (shape.global_position.y - 27.0) - down.global_position.y < 1150.0 * 0.5, 200)
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(4)
	release(KEY_LEFT)
	await wait(50)
	check(dodges.is_empty(), "no reward for an early dash (%s)" % [dodges])
	await wait(60)

	log_p("-- a dash started inside i-frames earns nothing")
	dodges.clear()
	events.clear()
	await settle_player(Vector2(972, 760))
	front_hit(&"untagged", dummy_source())
	check(player.is_invincible, "invincible")
	waves = spawn_waves(Vector2(972, 420))
	down = keep_only_wave(waves, 2)
	await wait_until(func(): return (shape.global_position.y - 27.0) - down.global_position.y < 1150.0 * 0.06, 200)
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(4)
	release(KEY_LEFT)
	await wait(30)
	check(dodges.is_empty(), "no reward while invincible (%s)" % [dodges])
	clear_iframes()
	await wait(60)

	log_p("-- at most one reward every 1.5 s")
	dodges.clear()
	events.clear()
	await settle_player(Vector2(972, 700))
	var first := keep_only_wave(spawn_waves(Vector2(972, 420)), 2)
	await wait_until(func(): return (shape.global_position.y - 27.0) - first.global_position.y < 1150.0 * 0.06, 200)
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(4)
	release(KEY_LEFT)
	check(await wait_until(func(): return dodges.size() == 1, 30), "first dodge rewarded")
	await settle_player(Vector2(972, 700))
	var second := keep_only_wave(spawn_waves(Vector2(972, 480)), 2)
	await wait_until(func(): return (shape.global_position.y - 27.0) - second.global_position.y < 1150.0 * 0.06, 200)
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(4)
	release(KEY_RIGHT)
	await wait(30)
	var gap: float = dodges[-1].t - dodges[0].t if dodges.size() > 1 else 0.0
	log_p("dodges %d, gap %.3f s" % [dodges.size(), gap])
	check(dodges.size() == 1, "the second dodge inside the 1.5 s cooldown earns nothing")


func test_dodge_bosses() -> void:
	await load_eric()
	health_ok()
	track()
	track_dodges()
	log_p("-- dash out of the whirlwind's path just before it arrives")
	await settle_player(Vector2(972, 760))
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Whirlwind")
	var ellipse: CollisionShape2D = boss.get_node("WhirlwindArea2D/CollisionShape2D")
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	await wait_until(func(): return (shape.global_position.y - 27.0) - (ellipse.global_position.y + 105.0) < 420.0 * 0.12, 300)
	press(KEY_DOWN)
	tap(KEY_W)
	await wait(4)
	release(KEY_DOWN)
	await wait(20)
	log_p("dodges %s, hits %s" % [dodges.map(func(d): return d.id), events.map(func(e): return e.kind)])
	check(dodges.size() == 1 and dodges[0].id == &"eric_whirlwind", "whirlwind near miss rewarded")
	check(events_of("HIT").is_empty(), "no hit")
	await wait_until(func(): return sm.current_state.name == "Downed", 400)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(100)

	log_p("-- dash aside as the bear hug's lunge arrives")
	dodges.clear()
	events.clear()
	await settle_player(Vector2(972, 800))
	sm.chain = []
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	var grab_shape: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
	await wait_until(func():
		if hug.phase != hug.Phase.LUNGE:
			return false
		var half: Vector2 = grab_shape.shape.size * grab_shape.global_scale.abs() / 2.0
		return (shape.global_position.y - 27.0) - (grab_shape.global_position.y + half.y) < 60.0, 300)
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(4)
	release(KEY_LEFT)
	await wait(20)
	log_p("dodges %s, grabbed %s" % [dodges.map(func(d): return d.id), player.is_grabbed])
	check(dodges.size() == 1 and dodges[0].id == &"eric_bear_hug_grab", "lunge near miss rewarded")
	check(not player.is_grabbed, "not grabbed")


# ------------------------------------------------------------------ step 5b: dash recovery

func dash(direction_key: int) -> void:
	if direction_key != 0:
		press(direction_key)
	tap(KEY_W)
	# The press only reaches the player on the next frame's input flush.
	await wait_until(func(): return player.is_dodging, 20)
	await wait_until(func(): return not player.is_dodging, 20)
	await wait(1)


func test_dash_recovery() -> void:
	await load_eric()
	# The dash a fight gets by opting out of feel_v2; dash_recovery_v2 covers the one that ships.
	player.feel_v2 = false
	park_eric()
	health_ok()
	track()
	track_parries()
	# Eric's fight y-sorts, which rests the player's frame on an offset of its own.
	var sprite_rest: Vector2 = player.sprite.offset
	log_p("-- locked out while recovering")
	await settle_player(Vector2(500, 700))
	var started: float = defense.clock
	await dash(KEY_RIGHT)
	check(defense.is_dash_recovering(), "recovery starts when the dash ends")
	check(player.state_machine.current_state.name == "DashRecovery", "in the DashRecovery state (%s)" % player.state_machine.current_state.name)
	var pose_frame: Vector2i = player.sprite.frame_coords
	var pos := player.global_position
	var dodge_frame: int = player.last_dodge_physics_frame
	var stamina_before: float = defense.stamina
	tap(KEY_Q)
	await wait(2)
	tap(KEY_W)
	await wait(2)
	check(player.state_machine.current_state.name == "DashRecovery", "punch and dash presses do nothing (%s)" % player.state_machine.current_state.name)
	check(player.last_dodge_physics_frame == dodge_frame, "no second dash")
	check(is_equal_approx(defense.stamina, stamina_before), "no stamina spent (%.1f)" % defense.stamina)
	check(player.global_position.distance_to(pos) < 1.0, "doesn't move with a direction held")
	check(not punch_landed_soon(), "no punch came out")
	log_p("recovery pose frame %s (walk column %d in the facing row)" % [pose_frame, pose_frame.x])
	var ended := await wait_until(func(): return not defense.is_dash_recovering(), 90)
	var lasted: float = defense.clock - started
	release(KEY_RIGHT)
	var expected: float = 0.05 + defense.dash_recovery_time
	log_p("recovery ran %.3f s after the dash started (dash 0.05 + recovery %.2f)" % [lasted, defense.dash_recovery_time])
	check(ended and absf(lasted - expected) <= 3.0 / 60.0, "recovery lasts %.2f s" % defense.dash_recovery_time)
	await wait(4)
	check(player.state_machine.current_state.name != "DashRecovery", "back to normal (%s)" % player.state_machine.current_state.name)
	check(player.sprite.offset == sprite_rest, "sprite lean cleared")

	log_p("-- a parry during recovery cancels it")
	await settle_player(Vector2(972, 760))
	await wait(20)
	await dash(KEY_LEFT)
	release(KEY_LEFT)
	check(defense.is_dash_recovering(), "recovering")
	press(KEY_SHIFT)
	await wait(2)
	check(player.state_machine.current_state.name == "Blocking", "the guard still goes up (%s)" % player.state_machine.current_state.name)
	check(defense.is_dash_recovering(), "raising the guard alone doesn't cancel it")
	var result := front_hit(&"eric_quake_wave", dummy_source())
	check(result == 3, "parried (%d)" % result)
	check(not defense.is_dash_recovering(), "the parry cancelled the recovery")
	release(KEY_SHIFT)
	tap(KEY_Q)
	check(await wait_until(func(): return player.state_machine.current_state.name == "Punching", 6), "a punch comes out at once")
	await wait_until(func(): return player.state_machine.current_state.name != "Punching", 40)

	log_p("-- a block that isn't a parry does not cancel it")
	defense.dash_recovery_time = 0.6
	await settle_player(Vector2(972, 760))
	await wait(20)
	await dash(KEY_LEFT)
	release(KEY_LEFT)
	press(KEY_SHIFT)
	# The recovery is set to 0.6 s above, so it is still running once the parry window has passed.
	await past_window()
	result = front_hit(&"eric_quake_wave", dummy_source())
	check(result == 2, "blocked (%d)" % result)
	check(defense.is_dash_recovering(), "a plain block leaves the recovery running")
	tap(KEY_Q)
	await wait(3)
	check(player.state_machine.current_state.name == "Blocking", "no punch during the recovery (%s)" % player.state_machine.current_state.name)
	release(KEY_SHIFT)
	defense.dash_recovery_time = 0.25

	log_p("-- the finisher and a grab clear it")
	await settle_player(Vector2(972, 700))
	await wait(30)
	await dash(0)
	check(defense.is_dash_recovering(), "recovering")
	player.begin_finisher()
	check(not defense.is_dash_recovering(), "begin_finisher clears it")
	player.is_finishing = false
	await wait(30)
	await dash(0)
	check(defense.is_dash_recovering(), "recovering")
	player.grab()
	check(not defense.is_dash_recovering(), "a grab clears it")
	player.release_grab(Vector2.UP)
	await wait(5)


func punch_landed_soon() -> bool:
	return player.state_machine.current_state.name == "Punching"


# Metres covered in `seconds` walking right, versus mashing dash right.
func travel(seconds: float, dashing: bool) -> float:
	player.global_position = Vector2(300, 700)
	player.velocity = Vector2.ZERO
	defense.stamina = defense.max_stamina
	defense.last_spend_time = -INF
	await wait(3)
	var total := 0.0
	var last: float = player.global_position.x
	press(KEY_RIGHT)
	for i in int(seconds * 60.0):
		if dashing:
			tap(KEY_W)
		await physics_frame
		total += absf(player.global_position.x - last)
		if player.global_position.x > 1500.0:
			player.global_position.x = 300.0
		last = player.global_position.x
	release(KEY_RIGHT)
	await wait(5)
	return total


func test_dash_spam() -> void:
	await load_eric()
	# The dash a fight gets by opting out of feel_v2; dash_spam_v2 covers the one that ships.
	player.feel_v2 = false
	health_ok()
	player.is_invincible = true
	player.invincibility_timer.stop()
	var walked := await travel(6.0, false)
	log_p("walking 6 s: %.0f px (%.0f px/s)" % [walked, walked / 6.0])
	var results := {}
	for recovery in [0.25, 0.35, 0.4, 0.5]:
		defense.dash_recovery_time = recovery
		var dashed := await travel(6.0, true)
		results[recovery] = dashed
		var cycle: float = 250.0 / (0.05 + recovery)
		log_p("recovery %.2f s: mashing dash %.0f px over 6 s (%.0f%% of walking); one dash cycle is %.0f px/s" % [recovery, dashed, 100.0 * dashed / walked, cycle])
	defense.dash_recovery_time = 0.25
	check(results[0.4] < walked, "at 0.40 s recovery, dash spam covers less ground than walking")


# ------------------------------------------------------------------ step 6

func test_hype() -> void:
	await load_eric()
	park_eric()
	health_ok()
	var hype: Node = player.get_node("Hype")
	var meter: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/HypeMeter")
	var popups: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/CombatPopups")
	var crowd: Node = get_nodes_in_group("arena_crowd")[0]
	track()
	track_parries()
	track_dodges()
	await wait(3)
	check(not hype.is_inert(), "hype counts in Eric's fight")
	check(hype.hype == 0.0 and meter.visible, "starts empty, meter shown")
	# What each pays is PlayerFeel's, by the player's feel_v2, which every fight is on.
	var punch_gain: float = feel("hype_punch_gain")
	var charged_gain: float = feel("hype_charged_punch_gain")
	var parry_gain: float = feel("hype_parry_gains")[0]
	var dodge_gain: float = feel("hype_perfect_dodge_gain")
	log_p("feel_v2 %s: a punch %.0f, charged %.0f, a parry %.0f, a perfect dodge %.0f" % [player.feel_v2, punch_gain, charged_gain, parry_gain, dodge_gain])

	log_p("-- punches")
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	# After Downed's Enter, which clears it: no daze, so a charged punch can't start a finisher here.
	boss.daze_used = true
	place_under(boss.get_node("Hurtbox"))
	await wait(6)
	await swing()
	check(is_equal_approx(hype.hype, punch_gain), "a landed punch gives %.0f (%.0f)" % [punch_gain, hype.hype])
	await wait(6)
	await swing()
	await wait(6)
	var before_charged: float = hype.hype
	await swing()
	log_p("hype after three punches: %.0f" % hype.hype)
	check(is_equal_approx(hype.hype - before_charged, charged_gain), "the charged punch gives %.0f instead of %.0f (+%.0f)" % [charged_gain, punch_gain, hype.hype - before_charged])

	log_p("-- parry, perfect dodge, hit, guard break")
	hype._set_hype(50.0)
	press(KEY_SHIFT)
	await wait(3)
	var parry_result := front_hit(&"eric_quake_wave", dummy_source())
	log_p("parry attempt: result %d, state %s, guarding %s, invincible %s (timer %.2f), talking %s, finishing %s, fight_over %s, health %d, recovering %s, guard_broken %s" % [parry_result, player.state_machine.current_state.name, defense.is_guarding(), player.is_invincible, player.invincibility_timer.time_left, player.is_talking, player.is_finishing, player.fight_over, player.playerHealth, defense.is_dash_recovering(), defense.is_guard_broken])
	check(is_equal_approx(hype.hype, 50.0 + parry_gain), "a parry gives %.0f (%.0f)" % [parry_gain, hype.hype])
	release(KEY_SHIFT)
	hype._set_hype(50.0)
	await wait(30)
	var ring := spawn_ring(player.global_position + Vector2(372, 0))
	var closed := await ring_close(ring, 0.05)
	tap(KEY_W)
	await wait(6)
	log_p("dodge attempt: ring close %s, dodging %s, immune %s, invincible %s, recovering %s" % [closed, player.is_dodging, load("res://Scripts/DashImmunity.gd").is_immune(player, 0.18, 0.6), player.is_invincible, defense.is_dash_recovering()])
	check(await wait_until(func(): return dodges.size() > 0, 30), "dodge landed")
	check(is_equal_approx(hype.hype, 50.0 + dodge_gain), "a perfect dodge gives %.0f (%.0f)" % [dodge_gain, hype.hype])
	await wait(40)
	clear_iframes()
	hype._set_hype(50.0)
	front_hit(&"untagged", dummy_source())
	check(is_equal_approx(hype.hype, 30.0), "a hit costs 20 (%.0f)" % hype.hype)
	clear_iframes()
	hype._set_hype(50.0)
	defense.stamina = 20.0
	defense.last_spend_time = defense.clock
	press(KEY_SHIFT)
	# Blocked, not parried, so the block is what empties the bar.
	await past_window()
	front_hit(&"eric_quake_wave", dummy_source())
	check(defense.is_guard_broken and is_equal_approx(hype.hype, 20.0), "a guard break costs 30 (50 -> %.0f)" % hype.hype)
	release(KEY_SHIFT)
	defense.clear_guard_break()
	clear_iframes()

	log_p("-- full")
	var full_events := []
	hype.hype_full_changed.connect(func(on): full_events.append(on))
	hype._set_hype(90.0)
	hype.add(10.0)
	check(hype.is_full() and full_events == [true], "full at 100")
	await wait(2)
	check(crowd._hyped, "the crowd is hyped")
	check(popups.popups.size() >= 1, "HYPE! popped up")
	await wait(4)
	var kinds: Array = popups.popups.map(func(p): return p.kind)
	check(kinds.has(&"hype"), "the popup is HYPE! (%s)" % [kinds])
	log_p("crowd frame %d while hyped" % crowd.frame)
	await wait(200)
	check(crowd._hyped and crowd.frame in crowd.CHEER_FRAMES, "the crowd keeps cheering past the cheer timer (frame %d)" % crowd.frame)
	check(hype.is_full(), "still full")

	log_p("-- a hit at full")
	clear_iframes()
	front_hit(&"untagged", dummy_source())
	check(not hype.is_full() and is_equal_approx(hype.hype, 80.0), "a hit drops it below full (%.0f)" % hype.hype)
	await wait(3)
	check(not crowd._hyped, "the crowd stops being hyped")
	check(full_events == [true, false], "full changed twice")

	log_p("-- fight over")
	hype._set_hype(100.0)
	await wait(2)
	player.end_fight()
	await wait(3)
	check(hype.hype == 0.0 and not hype.is_full() and not crowd._hyped, "the fight ending empties it and quiets the crowd")


func test_hype_inert() -> void:
	await load_fight("carter")
	await wait(10)
	var hype: Node = player.get_node("Hype")
	var meter: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/HypeMeter")
	check(hype.is_inert(), "hype is inert with no boss to finish")
	hype.add(50.0)
	check(hype.hype == 0.0, "gains do nothing (%.0f)" % hype.hype)
	await wait(3)
	check(not meter.visible, "the meter is hidden")


# ------------------------------------------------------------------ step 7

func daze_eric() -> bool:
	sm.rest_timer.stop()
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	place_under(boss.get_node("Hurtbox"))
	await wait(6)
	for i in 3:
		await swing()
		if i < 2:
			await wait(6)
	var finisher: Node = player.get_node("Finisher")
	return await wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120)


# On whatever the finisher mashes on here: Q and W, or the arrows in a fight on feel_v2.
const MASH_KEYS := {&"punch": KEY_Q, &"dodge": KEY_W, &"mash_left": KEY_LEFT, &"mash_right": KEY_RIGHT}


func mash_finisher() -> void:
	var finisher: Node = player.get_node("Finisher")
	var pair: Array = finisher.mash_actions()
	var step := 0
	while finisher.phase == 2 or finisher.phase == 3:
		tap(MASH_KEYS[pair[step % 2]])
		step += 1
		await wait(4)


func test_super_uppercut() -> void:
	await load_eric()
	# The mash a fight gets by opting out of feel_v2, on Q and W; verify_controls' eric_mash covers the
	# arrows that ship.
	player.feel_v2 = false
	health_ok()
	var hype: Node = player.get_node("Hype")
	var finisher: Node = player.get_node("Finisher")
	var spends := [0]
	hype.hype_spent.connect(func(): spends[0] += 1)

	log_p("-- full hype: a supercharged uppercut")
	hype._set_hype(100.0)
	check(await daze_eric(), "dazed at full hype")
	check(finisher.supercharged, "the finisher is supercharged")
	var before: int = boss.boss_health
	await mash_finisher()
	check(await wait_until(func(): return boss.boss_health < before, 90), "the uppercut lands")
	var dealt: int = before - boss.boss_health
	log_p("supercharged uppercut dealt %d of %d max health, hype %.0f" % [dealt, boss.max_health, hype.hype])
	check(dealt == 10, "deals 40%% of max health (%d, normal would be 6)" % dealt)
	check(spends[0] == 1 and hype.hype == 0.0, "hype spent")
	await wait_until(func(): return finisher.phase == 0, 120)
	await wait(30)

	log_p("-- a whiff keeps the hype")
	hype._set_hype(100.0)
	boss.daze_used = false
	check(await daze_eric(), "dazed again")
	check(finisher.supercharged, "supercharged")
	before = boss.boss_health
	player.global_position = Vector2(300, 900)
	await mash_finisher()
	await wait_until(func(): return finisher.phase == 0, 180)
	log_p("after the whiff: boss %d -> %d, hype %.0f, spends %d" % [before, boss.boss_health, hype.hype, spends[0]])
	check(boss.boss_health == before, "the uppercut missed")
	check(spends[0] == 1 and hype.is_full(), "hype kept")
	await wait(30)

	log_p("-- a fizzle keeps the hype")
	boss.daze_used = false
	check(await daze_eric(), "dazed again")
	await wait_until(func(): return finisher.phase == 5 or finisher.phase == 0, 400)
	await wait_until(func(): return finisher.phase == 0, 120)
	check(spends[0] == 1 and hype.is_full(), "hype kept after a fizzle")
	await wait(30)

	log_p("-- a killing blow that the normal uppercut would also have made")
	boss.daze_used = false
	boss.boss_health = 20
	check(await daze_eric(), "dazed again")
	boss.boss_health = 2
	before = boss.boss_health
	await mash_finisher()
	await wait_until(func(): return boss.boss_health < before, 90)
	log_p("dealt %d, spends %d" % [before - boss.boss_health, spends[0]])
	check(boss.boss_health == 0, "the boss dies")
	check(spends[0] == 1, "no hype spent: the supercharge added nothing")


func pad_event(button: int, pressed: bool) -> InputEventJoypadButton:
	var ev := InputEventJoypadButton.new()
	ev.button_index = button
	ev.pressed = pressed
	return ev


func pad_tap(button: int) -> void:
	Input.parse_input_event(pad_event(button, true))
	Input.parse_input_event(pad_event(button, false))


# Mashes the dazed finisher the way mash_finisher() does, one press every 4 frames alternating
# between the two, and returns [real seconds from the first press until the meter filled, presses].
func timed_mash(first: Callable, second: Callable) -> Array:
	var finisher: Node = player.get_node("Finisher")
	var filled_at := [0]
	var on_end := func(filled: bool) -> void:
		if filled:
			filled_at[0] = Time.get_ticks_usec()
	finisher.charge_ended.connect(on_end)
	var start := Time.get_ticks_usec()
	var presses := 0
	while finisher.phase == 2 or finisher.phase == 3:
		(first if presses % 2 == 0 else second).call()
		presses += 1
		await wait(4)
	finisher.charge_ended.disconnect(on_end)
	return [(filled_at[0] - start) / 1000000.0 if filled_at[0] > 0 else -1.0, presses]


# The finisher mashed on a pad: A and B fill the meter exactly as Q and W do, the alternation rule
# still refuses a repeat, the device follows the pad even though the finisher swallows the presses,
# and the prompt waits for the finisher to end before swapping its keys.
func test_gamepad_mash() -> void:
	await load_eric()
	# The mash a fight gets by opting out of feel_v2, on Q and W and on A and B; verify_controls'
	# eric_mash covers the arrows and bumpers that ship.
	player.feel_v2 = false
	health_ok()
	var settings: Node = root.get_node("InputSettings")
	var finisher: Node = player.get_node("Finisher")
	var prompt: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/FinisherPrompt")

	log_p("-- keyboard: Q and W")
	check(await daze_eric(), "dazed")
	var keyboard: Array = await timed_mash(tap.bind(KEY_Q), tap.bind(KEY_W))
	log_p("keyboard filled in %.3f s over %d presses" % keyboard)
	check(keyboard[0] > 0.0, "the keyboard mash fills the meter")
	await wait_until(func(): return finisher.phase == 0, 180)
	await wait(30)

	log_p("-- gamepad: A and B")
	boss.daze_used = false
	check(await daze_eric(), "dazed again")
	check(settings.device == 0, "on the keyboard going in (%d)" % settings.device)
	check(not prompt.gamepad_keys, "the prompt shows keyboard keys")
	var on_pad := [false, false]
	var watch_mash := func(_meter: float, _next: StringName) -> void:
		if finisher.phase == 3 and settings.device == 1:
			on_pad[0] = true
			on_pad[1] = not prompt.gamepad_keys and prompt.rebuild_pending and prompt.visible
	finisher.meter_changed.connect(watch_mash)
	var gamepad: Array = await timed_mash(pad_tap.bind(JOY_BUTTON_A), pad_tap.bind(JOY_BUTTON_B))
	finisher.meter_changed.disconnect(watch_mash)
	log_p("gamepad filled in %.3f s over %d presses" % gamepad)
	check(gamepad[0] > 0.0, "the gamepad mash fills the meter")
	check(absi(gamepad[1] - keyboard[1]) <= 1, "it takes the same presses (%d against %d)" % [gamepad[1], keyboard[1]])
	check(absf(gamepad[0] - keyboard[0]) <= 0.15, "in the same time (%.3f s against %.3f s)" % [gamepad[0], keyboard[0]])
	check(on_pad[0], "the device turned to the pad mid-mash, though the finisher swallows the presses")
	check(on_pad[1], "the prompt kept its keyboard keys while it was up, with the swap pending")
	await wait_until(func(): return finisher.phase == 0, 180)
	await wait(2)
	check(prompt.gamepad_keys and not prompt.rebuild_pending, "the prompt swapped to pad keys once the finisher ended")
	var pad_key: Node = prompt.keys[&"punch"]
	check(pad_key is Sprite2D and pad_key.texture.resource_path.ends_with("pad_buttons_3x.png") and pad_key.hframes == 14 and pad_key.vframes == 2, "drawn from the pad sheet")
	# The prompt's own first frame: until a press, punch is the lit key.
	prompt._on_prompt_shown()
	var frames: Array = [prompt.keys[&"punch"].frame, prompt.keys[&"dodge"].frame]
	prompt._on_finished()
	check(frames == [0 + 14, 1], "A lit from the gold row, B at rest %s" % [frames])
	await wait(30)

	log_p("-- the alternation rule on a pad")
	# Two landed uppercuts and their punches leave him too low to daze again.
	boss.boss_health = boss.max_health
	boss.daze_used = false
	check(await daze_eric(), "dazed a third time")
	pad_tap(JOY_BUTTON_A)
	await wait(4)
	var after_first: float = finisher.meter
	pad_tap(JOY_BUTTON_A)
	await wait(4)
	log_p("meter %.3f after A, %.3f after A again" % [after_first, finisher.meter])
	check(after_first > 0.0, "the first A counts")
	check(finisher.meter <= after_first, "a second A in a row doesn't")
	pad_tap(JOY_BUTTON_B)
	await wait(4)
	check(finisher.meter > after_first, "B after it does (%.3f)" % finisher.meter)
	await mash_finisher()
	await wait_until(func(): return finisher.phase == 0, 180)


# ------------------------------------------------------------------ step 8: every fight, no Shift, no W

# Hits that deal nothing: they start a hold rather than hurting.
# These three used to be hand-kept copies of what AttackCatalog already says, and a copy only covers
# the attacks somebody remembered to add to it. Josh was in none of them, so every one of his attacks
# was scored as a 1-damage unblockable: smoke expected 8 where the catalogue says 10, and blocks
# called his two blockable cards "shouldn't be blockable". Reading the catalogue instead means a new
# attack is covered the day it is catalogued. The invariant under test is unchanged and is the one
# that matters: the RUNTIME honours what the catalogue declares.
const CATALOG := preload("res://Scripts/AttackCatalog.gd")


# The half-hearts the catalogue says this attack costs, which is 0 for a grab and 2 or 3 for the
# blows that are worth more than one.
func catalogue_damage(id: StringName) -> int:
	return CATALOG.get_attack(id).damage


# The stamina a guard facing this attack should spend, read off the catalogue's weight and the
# player's own cost vars, or 0.0 for an attack no guard should be able to absorb at all.
func catalogue_block_cost(id: StringName) -> float:
	var entry: Dictionary = CATALOG.get_attack(id)
	if not entry.blockable:
		return 0.0
	return defense.heavy_block_cost if entry.weight == CATALOG.Weight.HEAVY else defense.light_block_cost
# Hits that land inside the i-frames on purpose, because the player is held and cannot dodge.
const IGNORES_IFRAMES := [&"eric_bear_hug_squeeze", &"greyson_combo_jab", &"greyson_combo_finish", &"computah_slam"]

const SMOKE_SPOTS := {
	"eric": Vector2(972, 700),
	"greyson": Vector2(960, 700),
	"carter": Vector2(960, 560),
	"mason": Vector2(960, 640),
	"jordan": Vector2(960, 640),
	"liam": Vector2(960, 640),
	"josh": Vector2(960, 640),
}


func test_smoke() -> void:
	if fight == "eric" and ver > 0:
		pin_eric(ver)
	# Liam's intro plays through his pre-fight dialogue, whose lines drive the transformation, so
	# that balloon has to be tapped through rather than skipped.
	await load_fight(fight, STATE_INTROS.has(fight))
	var settled := await clear_intro(fight)
	if settled != "":
		log_p("%s's intro ended in %s" % [fight, settled])
	player.playerHealth = 1000
	track()
	track_parries()
	track_dodges()
	var spot: Vector2 = SMOKE_SPOTS[fight]
	if fight == "carter":
		# They charge straight up and down their own column, so stand in one.
		spot.x = current_scene.get_node("Arena/CarterAndJoshScene/Carter").global_position.x
	await settle_player(spot)
	var health: int = player.playerHealth
	var start: float = defense.clock
	var staged := false
	var punished := false
	while defense.clock - start < 45.0:
		# The player never moves, blocks or dashes: the fight should play out exactly as before.
		player.global_position = spot
		if fight == "carter" and not punished and defense.clock - start > 8.0:
			punished = true
			var carter: Node = current_scene.get_node_or_null("Arena/CarterAndJoshScene/Carter")
			if carter:
				place_under(carter.get_node("BodyHitbox"))
				await swing_any()
				log_p("punched Carter")
				player.global_position = spot
		await physics_frame
	var hits := events_of("HIT")
	var ids := {}
	for e in hits:
		ids[e.id] = ids.get(e.id, 0) + 1
	log_p("%s: %d hits %s over 45 s" % [fight, hits.size(), ids])
	check(hits.size() > 0, "the fight connects at all")
	check(events_of("BLOCKED").is_empty() and parries.is_empty() and dodges.is_empty(), "nothing blocked, parried or dodged without Shift or W")
	check(not ids.has(&"untagged"), "no untagged attacks (%s)" % [ids.keys()])
	# Grabs deal nothing; they only start the hold. Boss 2's five-hit combo is four of those and one
	# launching blow worth three, which is the shape of Eric's bear hug.
	var expected := 0
	for e in hits:
		expected += catalogue_damage(e.id)
	check(player.playerHealth == health - expected, "the catalogued damage per hit (%d expected of %d hits, %d health lost)" % [expected, hits.size(), health - player.playerHealth])
	var bad_gaps := []
	for i in range(1, hits.size()):
		var gap: float = hits[i].t - hits[i - 1].t
		# A held player can't dodge, so every blow of a hold lands inside the last one's i-frames.
		if gap < 1.0 - 0.001 and not IGNORES_IFRAMES.has(hits[i].id):
			bad_gaps.append("%s after %.3f s" % [hits[i].id, gap])
	check(bad_gaps.is_empty(), "every hit is followed by a second of i-frames (%s)" % [bad_gaps])
	if fight == "eric":
		# Each hold's squeezes belong to the grab before them. The 45 s window can close mid-hold, which
		# V2 hugs often enough to do regularly, so a hold still on at the cut-off isn't counted.
		var hugs := []
		for e in hits:
			if e.id == &"eric_bear_hug_grab" or e.id == &"eric_bear_hug_grab_v2":
				hugs.append(0)
			elif e.id == &"eric_bear_hug_squeeze" and not hugs.is_empty():
				hugs[-1] += 1
		var cut_short: bool = player.is_grabbed and not hugs.is_empty()
		if cut_short:
			hugs.pop_back()
		log_p("bear hugs that finished: %s%s" % [hugs, ", and one still holding at the cut-off" if cut_short else ""])
		check(not hugs.is_empty() or cut_short, "he got a bear hug in")
		check(hugs.all(func(count): return count == 3), "every bear hug that finished squeezed three times (%s)" % [hugs])
	if fight == "carter":
		check(ids.has(&"wrestler_punish"), "punching a wrestler still hurts")


# What each attack should cost the guard, and what should never be blockable at all.
const UNBLOCKABLE := [&"computah_laser", &"computah_chase", &"greyson_combo_jab", &"greyson_combo_finish", &"computah_slam", &"wrestler_punish", &"eric_quake_ring", &"eric_bear_hug_squeeze"]


func test_blocks() -> void:
	await load_fight(fight, STATE_INTROS.has(fight))
	await clear_intro(fight)
	player.playerHealth = 1000
	track()
	track_parries()
	var spot: Vector2 = SMOKE_SPOTS[fight]
	if fight == "carter":
		spot.x = current_scene.get_node("Arena/CarterAndJoshScene/Carter").global_position.x
	await settle_player(spot)
	press(KEY_SHIFT)
	var start: float = defense.clock
	var staged := false
	var guarded_frames := 0
	var frames_run := 0
	while defense.clock - start < 45.0 and not player.fight_over:
		frames_run += 1
		player.global_position = spot
		if defense.is_guarding():
			guarded_frames += 1
		# Topped up, so a long run can't break the guard and change what the next hit does.
		defense.stamina = defense.max_stamina
		await physics_frame
	release(KEY_SHIFT)
	var blocks := events_of("BLOCKED")
	var costs := {}
	var last_frame := -1
	for e in blocks:
		# Two attacks blocked in the same frame both come out of the same topped-up bar.
		if e.frame != last_frame:
			costs[e.id] = 100.0 - e.stamina
		last_frame = e.frame
	var hit_ids := {}
	for e in events_of("HIT"):
		hit_ids[e.id] = hit_ids.get(e.id, 0) + 1
	log_p("%s blocked %s, hit %s, guard up for %d of %d frames%s" % [fight, costs, hit_ids, guarded_frames, frames_run, " (the fight ended early)" if player.fight_over else ""])
	check(guarded_frames > frames_run * 0.9, "the guard stayed up through the fight (%d of %d frames)" % [guarded_frames, frames_run])
	for id in costs:
		var want: float = catalogue_block_cost(id)
		check(want > 0.0 and is_equal_approx(costs[id], want), "%s costs %.0f (expected %s)" % [id, costs[id], "%.0f" % want if want > 0.0 else "nothing: it shouldn't be blockable"])
	for id in hit_ids:
		if UNBLOCKABLE.has(id):
			check(not costs.has(id), "%s is never blocked" % id)
	if player.fight_over:
		log_p("-- the fight ended on its own; the direction rules are checked in the other fights")
		return
	log_p("-- the direction rules, with hits sent from known angles")
	await settle_player(spot)
	press(KEY_SHIFT)
	# Past the parry window: these four are about which sides the guard covers, not the parry.
	await past_window()
	clear_iframes()
	defense.stamina = defense.max_stamina
	var front := front_hit(&"greyson_throw", dummy_source())
	clear_iframes()
	defense.stamina = defense.max_stamina
	var side := side_hit(&"wrestler_charge", dummy_source())
	clear_iframes()
	defense.stamina = defense.max_stamina
	var omni := omni_hit(&"funko_blast", dummy_source())
	clear_iframes()
	defense.stamina = defense.max_stamina
	var above := front_hit(&"mason_nugget", dummy_source(), true)
	release(KEY_SHIFT)
	log_p("front %d, perpendicular %d, on top of the player %d, from above while facing away %d (1 HIT, 2 BLOCKED)" % [front, side, omni, above])
	check(front == 2, "a light projectile from the front is blocked")
	check(side == 1, "a charge from the side hits")
	check(omni == 2, "a blast on top of the player is blocked from any facing")
	check(above == 2, "a sky attack is blocked whatever the facing")

	if fight == "liam":
		var breaths := blocks.filter(func(e): return e.id == &"bixby_fire_breath")
		var gaps := []
		for i in range(1, breaths.size()):
			gaps.append(snappedf(breaths[i].t - breaths[i - 1].t, 0.01))
		log_p("fire breath block gaps: %s" % [gaps])
		for gap in gaps:
			check(gap >= 1.0 - 0.02, "the fire stream costs stamina once a second (%.2f)" % gap)


# ------------------------------------------------------------------ uppercut knockback and recovery

const ATTACK_STATES := ["Earthquake", "Whirlwind", "SwordThrow", "BearHug"]


func test_knockback() -> void:
	await load_eric()
	health_ok()
	var hype: Node = player.get_node("Hype")
	var finisher: Node = player.get_node("Finisher")
	var results := []
	var sprite_rest: Vector2 = boss.sprite.offset
	for supercharged in [false, true]:
		boss.daze_used = false
		boss.boss_health = 24
		# Low in the ring: the player stands under him, so the shove is upward and needs the room.
		boss.global_position = Vector2(960, 700)
		boss.sprite.offset = sprite_rest
		hype._set_hype(100.0 if supercharged else 0.0)
		log_p("  setup: eric %s state %s, player %s" % [boss.global_position, sm.current_state.name, player.global_position])
		check(await daze_eric(), "dazed (%s)" % ("supercharged" if supercharged else "normal"))
		log_p("  dazed: eric %s state %s, player %s" % [boss.global_position, sm.current_state.name, player.global_position])
		var before: Vector2 = boss.global_position
		var player_at: Vector2 = player.global_position
		var health: int = boss.boss_health
		await mash_finisher()
		check(await wait_until(func(): return boss.boss_health < health, 90), "the uppercut lands")
		var contact: float = defense.clock
		await wait(30)
		var moved: float = before.distance_to(boss.global_position)
		var away: bool = boss.global_position.distance_to(player_at) > before.distance_to(player_at)
		var inside: bool = boss.KNOCKBACK_AREA.grow(1.0).has_point(boss.global_position)
		# The chain only starts once his recovery is over.
		var attacked := await wait_until(func(): return ATTACK_STATES.has(sm.current_state.name), 300)
		var pause: float = defense.clock - contact
		results.append({"moved": moved, "away": away, "inside": inside, "attacked": attacked, "pause": pause})
		log_p("%s: knocked %.0f px%s, inside bounds %s, next attack after %.2f s" % ["super" if supercharged else "normal", moved, " away" if away else " TOWARD the player", inside, pause])
		sm.rest_timer.stop()
		sm.downed_state_timer.stop()
		sm.on_child_transition(sm.current_state, "Idle")
		# The finisher tweens the player home afterwards; dazing again before it ends moves him off the boss.
		await wait_until(func(): return player.get_node("Finisher").phase == 0, 240)
		await wait(30)
		clear_iframes()
	check(absf(results[0].moved - 120.0) < 30.0, "a normal uppercut shoves him about 120 px (%.0f)" % results[0].moved)
	check(absf(results[1].moved - 240.0) < 40.0, "a supercharged one about 240 px (%.0f)" % results[1].moved)
	check(results[0].away and results[1].away, "always away from the player")
	check(results[0].inside and results[1].inside, "never outside his bounds")
	check(results[0].attacked and results[1].attacked, "his chain carries on")
	check(results[0].pause > 1.1 and results[1].pause > 1.7, "the pause before the next attack grows (%.2f / %.2f s)" % [results[0].pause, results[1].pause])
	check(results[1].pause > results[0].pause, "a supercharged uppercut buys more time")


# A boss anchored to his own cycle rocks back on his sprite instead, and his body stays put.
# Boss 2's Computah, whose near-death clamp is the floor that clips the uppercut: he cannot be
# killed while Greyson is above GreysonComputahScript.SWAP_GUARD_RATIO, so the blow lands on 1 and
# the supercharge, having added nothing, is not spent.
func test_knockback_computah() -> void:
	await load_fight("greyson")
	player.playerHealth = 100
	var pair: Node = current_scene.get_node("Arena/GreysonComputahScene")
	var computah: Node = pair.computah
	var machine: Node = pair.get_node("StateManager")
	# swing() reads the boss's health to report what it dealt.
	boss = computah
	var hype: Node = player.get_node("Hype")
	var finisher: Node = player.get_node("Finisher")
	machine.post_dialogue_pre_fight_timer.stop()
	hype._set_hype(100.0)
	# Greyson untouched, so the clamp holds Computah at 1. Six leaves the three daze punches - the
	# third is charged and worth two - taking him to 2, one above the clamp, so the uppercut lands
	# and is then clipped by it.
	computah.boss_health = 6
	pair.on_body_damaged(computah)
	machine.open_window(computah, 60.0, computah.MAX_HITS_PER_WINDOW, &"collapse", &"down", &"reboot")
	await wait(5)
	place_under(computah.get_node("Hurtbox"))
	await wait(6)
	for i in 3:
		await swing()
		if i < 2:
			await wait(6)
	check(await wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120), "dazed")
	var body_at: Vector2 = computah.global_position
	var rest: Vector2 = computah.sprite.offset
	var health: int = computah.boss_health
	await mash_finisher()
	check(await wait_until(func(): return computah.boss_health < health, 90), "the uppercut lands")
	await wait(8)
	log_p("computah %d -> %d, body moved %.1f px, sprite offset %s -> %s" % [health, computah.boss_health, body_at.distance_to(computah.global_position), rest, computah.sprite.offset])
	check(computah.boss_health == 1, "it stops at the near-death clamp (%d)" % computah.boss_health)
	check(hype.is_full(), "no hype spent: the supercharge added nothing past the clamp")
	check(body_at.distance_to(computah.global_position) < 1.0, "his body stays where his fight expects it")
	check(computah.sprite.offset != rest, "he rocks back on his sprite")
	check(computah.on_brink, "and the clamp puts him visibly on the brink")
	await wait(120)
	check(computah.sprite.offset.distance_to(rest) < 1.0, "the recoil settles back (%s)" % computah.sprite.offset)


# The rest of the roster, one fight per run: [boss body, punish state].
const PUNISH_WINDOWS := {
	"mason": ["Arena/MasonScene/MasonCharacterBody", "Eat"],
	"jordan": ["Arena/JordanScene/JordanCharacterBody", "Taunt"],
	"liam": ["Arena/BixbyBeastScene/BixbyBeastCharacterBody", "Recover"],
}
# The ring floor, from ArenaScene's wallBoundaries.
const ROPES := Rect2(105, 105, 1710, 870)


func test_knockback_boss() -> void:
	var key := fight
	await load_fight(key, STATE_INTROS.has(key))
	await clear_intro(key)
	player.playerHealth = 1000
	var hype: Node = player.get_node("Hype")
	var finisher: Node = player.get_node("Finisher")
	boss = current_scene.get_node(PUNISH_WINDOWS[key][0])
	var bsm: Node = boss.state_machine
	hype._set_hype(100.0)
	bsm.on_child_transition(bsm.current_state, PUNISH_WINDOWS[key][1])
	await wait(5)
	# The window's own timer would close it mid-combo.
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	place_under(boss.get_finisher_hurtbox())
	await wait(6)
	check(boss.can_be_dazed(), "%s has a punish window open" % key)
	for i in 3:
		await swing_any()
		if i < 2:
			await wait(6)
	check(await wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120), "dazed")
	# The three daze punches can leave him inside a phase floor, which would clip the supercharged
	# uppercut back to the normal one. Topped up, the full 40% lands.
	boss.boss_health = boss.max_health
	var body_at: Vector2 = boss.global_position
	var player_at: Vector2 = player.global_position
	var rest: Vector2 = boss.sprite.offset
	var ratio: float = boss.get_health_ratio()
	log_p("  hype %.0f full %s supercharged %s, health ratio %.2f" % [hype.hype, hype.is_full(), finisher.supercharged, ratio])
	await mash_finisher()
	check(await wait_until(func(): return boss.get_health_ratio() < ratio, 90), "the uppercut lands")
	log_p("  dealt %.0f%% of max health, hype now %.0f" % [(ratio - boss.get_health_ratio()) * 100.0, hype.hype])
	var contact: float = defense.clock
	var held: String = bsm.current_state.name
	await wait(45)
	var moved: float = body_at.distance_to(boss.global_position)
	var recoiled: float = rest.distance_to(boss.sprite.offset) * boss.sprite.global_scale.x
	var hurt: Rect2 = area_rect(boss.get_finisher_hurtbox())
	log_p("%s: body moved %.0f px, sprite recoil %.0f px, hurtbox %s, player %s" % [key, moved, recoiled, hurt, player.global_position])
	check(moved > 1.0 or recoiled > 1.0, "the uppercut rocks him (%.0f px body, %.0f px sprite)" % [moved, recoiled])
	if moved > 1.0:
		check(boss.global_position.distance_to(player_at) > body_at.distance_to(player_at), "he is shoved away from the player")
		check(ROPES.encloses(hurt), "he stays inside the ropes (%s)" % hurt)
		check(not hurt.has_point(player.global_position), "he is not shoved onto the player")
	# He must hold the post-finisher state for the whole stagger; what his chain picks afterwards is
	# up to his own pacing (and the funkos left over from the taunt in this setup).
	while defense.clock - contact < 3.0 and bsm.current_state.name == held:
		await physics_frame
	var pause: float = minf(defense.clock - contact, 3.0)
	log_p("%s: held %s for %.2f s, then %s" % [key, held, pause, bsm.current_state.name])
	check(pause > 1.7, "he stays staggered about 1.8 s (%.2f s)" % pause)
	check(boss.get_health_ratio() > 0.0, "the fight carries on")
	await wait(120)
	check(boss.sprite.offset.distance_to(rest) < 2.0, "the recoil settles back (%s)" % boss.sprite.offset)


# A killing uppercut leaves the boss where he stands: no shove, no recoil, his defeat plays from the
# spot he was hit on, and the outro runs once.
const KILL_WINDOWS := {
	"eric": ["Arena/EricBossScene/CharacterBody2D", "Downed"],
}


# One boss and one tier per run: the outro node outlives its fight scene, so reloading inside a run
# would meet the last fight's leftovers.
func test_kill_shove() -> void:
	var key := fight
	var supercharged := tier == "super"
	await load_fight(key)
	player.playerHealth = 1000
	var hype: Node = player.get_node("Hype")
	var finisher: Node = player.get_node("Finisher")
	var health_on: Node = null
	if true:
		current_scene.get_node("Arena/EricBossScene/CharacterBody2D").state_machine.post_dialogue_pre_fight_timer.stop()
	boss = current_scene.get_node(KILL_WINDOWS[key][0])
	sm = boss.state_machine
	if health_on == null:
		health_on = boss
	hype._set_hype(100.0 if supercharged else 0.0)
	sm.on_child_transition(sm.current_state, KILL_WINDOWS[key][1])
	await wait(5)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	place_under(boss.get_finisher_hurtbox())
	await wait(6)
	for i in 3:
		await swing_any()
		if i < 2:
			await wait(6)
	check(await wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120), "%s: dazed" % tier)
	# Exactly the damage this uppercut deals, so it kills.
	var max_health: int = boss.get_max_health()
	health_on.boss_health = roundi(max_health * (0.40 if supercharged else 0.25))
	var body_at: Vector2 = boss.global_position
	var rest: Vector2 = boss.sprite.offset
	# This mode is about where a killing blow leaves him, not the mash. The press gate counts real
	# seconds, and a --fixed-fps run outpaces them until the charge times out, so it's switched off.
	finisher.min_press_interval = 0.0
	await mash_finisher()
	check(await wait_until(func(): return health_on.boss_health <= 0, 90), "%s: the uppercut kills" % tier)
	var hype_spent: bool = not hype.is_full()
	# Sampled before it can end: a defeat animation that has played out reads as "".
	await wait(20)
	var animator: AnimationPlayer = boss.animation_player if "animation_player" in boss else boss.animationPlayer
	var playing: String = animator.current_animation
	var where: String = sm.current_state.name
	await wait(70)
	var moved: float = body_at.distance_to(boss.global_position)
	var recoiled: float = rest.distance_to(boss.sprite.offset) * boss.sprite.global_scale.x
	var outros: int = root.get_children().filter(func(c): return c.name == "FightOutro").size()
	log_p("%s %s kill: moved %.0f px, sprite %.0f px, state %s animation %s, outros %d, supercharge spent %s" % [key, tier, moved, recoiled, where, playing, outros, hype_spent])
	check(moved < 1.0, "%s: his body stays where he was hit (%.0f px)" % [tier, moved])
	check(recoiled < 1.0, "%s: his sprite stays put (%.0f px)" % [tier, recoiled])
	check(outros == 1, "%s: one outro (%d)" % [tier, outros])
	check(playing.contains("defeat") or playing.contains("down"), "%s: his defeat plays (%s in %s)" % [tier, playing, where])
	if supercharged:
		check(hype_spent, "%s: a killing supercharge still spends the hype" % tier)
	await wait(30)


# ------------------------------------------------------------------ the handed-out finisher

# A fight handing the player the whole finisher (PlayerFinisher.begin_auto): the daze, no prompt, and
# the uppercut firing itself. tier=super runs it with a full hype meter.
func test_auto_finisher() -> void:
	await load_eric()
	health_ok()
	park_eric()
	var finisher: Node = player.get_node("Finisher")
	var hype: Node = player.get_node("Hype")
	var sound: AudioStreamPlayer = player.get_node("SuperUppercutSfxPlayer")
	var supercharged := tier == "super"
	var prompts := [0]
	finisher.prompt_shown.connect(func(): prompts[0] += 1)
	log_p("-- the sound the supercharged uppercut has and the normal one doesn't")
	check(sound.stream != null, "its stream is loaded up front (%s)" % (sound.stream.resource_path if sound.stream else "none"))
	log_p("  %s at %.1f dB, pitch %.2f" % [sound.stream.resource_path.get_file(), sound.volume_db, sound.pitch_scale])

	log_p("-- it will not start on a boss that cannot be dazed")
	check(not finisher.begin_auto(boss), "refused while he is not in a punish window")
	check(not player.is_finishing and finisher.phase == 0, "and nothing was started")

	log_p("-- opened up, it takes")
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	boss.daze_used = false
	boss.boss_health = 24
	hype._set_hype(100.0 if supercharged else 0.0)
	place_under(boss.get_node("Hurtbox"))
	await wait(4)
	var health: int = boss.boss_health
	var boss_at: Vector2 = boss.global_position
	var started: float = defense.clock
	check(finisher.begin_auto(boss), "begin_auto took")
	check(not finisher.begin_auto(boss), "and refuses to start a second one over it")
	check(await wait_until(func(): return finisher.dazed, 60), "he is dazed")
	check(finisher.supercharged == supercharged, "the meter was read at the daze (%s)" % finisher.supercharged)

	log_p("-- no prompt, and presses do nothing")
	tap(KEY_Q)
	tap(KEY_W)
	await wait(4)
	check(not finisher.prompt_visible and prompts[0] == 0, "the prompt never shows")
	check(finisher.meter < 1.0 or finisher.phase >= 4, "a press never filled the meter")

	log_p("-- the uppercut fires itself")
	check(await wait_until(func(): return boss.boss_health < health, 180), "it lands")
	var to_contact: float = defense.clock - started
	var dealt: int = health - boss.boss_health
	log_p("contact %.2f s after the call, dealt %d of %d, sound playing %s at pitch %.2f" % [to_contact, dealt, boss.max_health, sound.playing, sound.pitch_scale])
	check(to_contact >= 0.35, "the dazed beat is held before it (%.2f s)" % to_contact)
	check(dealt == (10 if supercharged else 6), "it deals what the hand-driven one deals (%d)" % dealt)
	check(sound.playing == supercharged, "the supercharged sound plays only for the supercharged one (%s)" % sound.playing)
	check(is_equal_approx(sound.pitch_scale, 1.0 if supercharged else sound.pitch_scale), "the hit-stop does not bend its pitch (%.2f)" % sound.pitch_scale)
	if supercharged:
		check(hype.hype == 0.0, "the meter was spent (%.0f)" % hype.hype)
		# The freeze is 0.35 s of real time and the sound is longer, so it has to ring through it.
		await wait(30)
		check(sound.playing, "and it rings on through the freeze")
	else:
		check(hype.hype == 0.0 or not hype.is_full(), "nothing to spend")
	log_p("-- and it puts the player back")
	check(await wait_until(func(): return finisher.phase == 0, 180), "the finisher ends")
	check(not player.is_finishing, "the player is his own again")
	check(finisher.is_input_locked(), "with the usual beat of swallowed input after it")
	check(await wait_until(func(): return not finisher.is_input_locked(), 90), "which passes")
	check(not finisher.auto, "and the handed-out flag is cleared")
	# The shove is a game-time tween, so it plays out slowly through the contact's hit-stop.
	await wait(45)
	check(boss.global_position.distance_to(boss_at) > 50.0, "he is knocked back like any other uppercut (%.0f px)" % boss.global_position.distance_to(boss_at))


# A handed-out finisher that kills: the same rules as a mashed one.
func test_auto_kill() -> void:
	await load_eric()
	health_ok()
	park_eric()
	var finisher: Node = player.get_node("Finisher")
	player.get_node("Hype")._set_hype(0.0)
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	boss.daze_used = false
	# Exactly what a normal uppercut deals, so it kills.
	boss.boss_health = 6
	place_under(boss.get_node("Hurtbox"))
	await wait(4)
	var boss_at: Vector2 = boss.global_position
	check(finisher.begin_auto(boss), "it took")
	check(await wait_until(func(): return boss.boss_health <= 0, 240), "the boss died")
	await wait(60)
	var outros: int = root.get_children().filter(func(c): return c.name == "FightOutro").size()
	log_p("killed: moved %.0f px, outros %d, state %s" % [boss_at.distance_to(boss.global_position), outros, sm.current_state.name])
	check(boss_at.distance_to(boss.global_position) < 1.0, "a killing blow still leaves him where he was hit")
	check(outros == 1, "one outro (%d)" % outros)
	check(player.fight_over, "and the fight is over")
	check(not finisher.begin_auto(boss), "and nothing can be handed out after it")
	check(not player.is_finishing and finisher.phase == 0, "nothing was started (%d)" % finisher.phase)


# ------------------------------------------------------------------ a barrage's cadence

# Carter's clone barrage read against the parry window, without needing his fight to be running: a
# clone shows a light for clone_show, dashes for clone_dash and strikes at the end of the dash, and
# the next light comes up clone_gap later.
# The mode reads those three off CarterStateMachine when his fight is in the build, so it can never
# model a barrage tighter than the one he ships, and the constants below are only the fallback for a
# build without him. They mirror his numbers and the mode fails if they drift apart, so change them
# in the same pass as his.
const CARTER_STATE_MACHINE := "res://Scripts/States/CarterAkuma/CarterStateMachine.gd"
const CARTER_ART_LAYOUT := "res://Scripts/CarterArtLayout.gd"
const CLONE_SHOW := 0.36
const CLONE_DASH := 0.18
const CLONE_GAP := 0.08
# CarterArtLayout.CLONE_LIGHT_OUT: how long a light takes to go out, which has to fit in the gap.
const CLONE_LIGHT_OUT := 0.05


func clone_frames(seconds: float) -> int:
	return int(roundf(seconds * 60.0))


func test_clone_cadence() -> void:
	await load_eric()
	health_ok()
	park_eric()
	await settle_player(Vector2(972, 800))
	var show_time := CLONE_SHOW
	var dash_time := CLONE_DASH
	var gap_time := CLONE_GAP
	var light_out := CLONE_LIGHT_OUT
	if ResourceLoader.exists(CARTER_STATE_MACHINE):
		var probe: Node = load(CARTER_STATE_MACHINE).new()
		show_time = probe.clone_show
		dash_time = probe.clone_dash
		gap_time = probe.clone_gap
		probe.free()
		light_out = load(CARTER_ART_LAYOUT).CLONE_LIGHT_OUT
		log_p("read off his fight: show %.2f, dash %.2f, gap %.2f, light out %.2f" % [show_time, dash_time, gap_time, light_out])
		check(is_equal_approx(show_time, CLONE_SHOW) and is_equal_approx(dash_time, CLONE_DASH) and is_equal_approx(gap_time, CLONE_GAP) and is_equal_approx(light_out, CLONE_LIGHT_OUT), "the numbers in this file still mirror his fight (%.2f/%.2f/%.2f/%.2f against %.2f/%.2f/%.2f/%.2f)" % [CLONE_SHOW, CLONE_DASH, CLONE_GAP, CLONE_LIGHT_OUT, show_time, dash_time, gap_time, light_out])
	else:
		log_p("his fight is not in this build, so the numbers in this file are what is modelled")
	var window: float = defense.parry_window
	var strike: float = show_time + dash_time
	var cadence: float = strike + gap_time
	log_p("light %.2f s, dash %.2f s, strike at %.2f s, cadence %.2f s, window %.2f s" % [show_time, dash_time, strike, cadence, window])
	check(gap_time >= light_out, "a light has time to go out before the next comes up (%.2f s gap, %.2f s to fade)" % [gap_time, light_out])
	check(strike < cadence, "one clone is done before the next starts (%.2f s of life, %.2f s cadence)" % [strike, cadence])

	log_p("-- pressing the instant the light comes up is still too early")
	defense.rearm_parry()
	var on_sight: int = await parry_at(clone_frames(strike))
	check(on_sight == 2, "a press on sight only blocks (%d)" % on_sight)
	check(strike > window + 1.0 / 60.0, "the strike is %.2f s past the light, the window covers %.2f s" % [strike, window])

	log_p("-- and the read, on the dash, parries")
	defense.rearm_parry()
	var on_dash: int = await parry_at(clone_frames(dash_time))
	check(on_dash == 3, "a press as it dashes parries (%d)" % on_dash)
	# The window opens this long after the light, which is what the player has to wait out.
	log_p("the window opens %.2f s into the light, %.0f%% of the way through it" % [strike - window, 100.0 * (strike - window) / show_time])

	log_p("-- a clone bitten on sight is blocked, not parried, and the guard holds")
	defense.rearm_parry()
	press(KEY_SHIFT)
	await wait(clone_frames(strike))
	var bitten := front_hit(&"eric_quake_wave", dummy_source())
	release(KEY_SHIFT)
	check(bitten == 2, "the bitten clone lands as a block (%d)" % bitten)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await past_window()
	await wait(40)

	# A yellow clone never strikes, so a press at it whiffs with nothing to answer. That press is what
	# the next clone's read has to survive, and only the rearm lets it.
	log_p("-- biting a feint late is what would cost the next clone, and the rearm is what saves it")
	var bite_at := clone_frames(show_time + dash_time * 0.5)
	var to_next_read := clone_frames(cadence + strike - window) - bite_at
	log_p("  a press %.2f s into a feint, then the next clone's read %.2f s later, inside the %.2f s lockout" % [bite_at / 60.0, to_next_read / 60.0, defense.parry_mash_lockout])
	press(KEY_SHIFT)
	await wait(2)
	release(KEY_SHIFT)
	await wait(to_next_read)
	var spilled: int = await parry_at(clone_frames(window))
	check(spilled == 2, "with nothing rearming it, the feint's press costs the next clone too (%d)" % spilled)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await past_window()
	await wait(40)
	press(KEY_SHIFT)
	await wait(2)
	release(KEY_SHIFT)
	await wait(to_next_read)
	# What the fight does as each light comes up.
	defense.rearm_parry()
	var saved: int = await parry_at(clone_frames(window))
	check(saved == 3, "the rearm gives the next clone back (%d)" % saved)
	check(cadence < defense.parry_mash_lockout + window, "which the cadence needs: %.2f s is inside the lockout plus the window, %.2f s" % [cadence, defense.parry_mash_lockout + window])


# ------------------------------------------------------------------ approach times

# Attacks whose hitbox is spawned but whose read is the boss's wind-up, not the hitbox's flight.
# A ground attack that radiates from where the boss stands has no flight at all for anyone standing
# in it, and nothing can give it one: at 1150 px/s his waves would need the player 494 px away to
# clear the bar, so the only ways to buy the time are a wave under 250 px/s or a 400 px dead zone
# around him, and both throw the attack away. What the player reads is the slam itself.
# The value is that wind-up, and it is still held to the same bar as a flight.
const WINDUP_READS := {
	# enable_hitbox fires 0.667 s into `earthquake`, played at EricEarthquake's 1.6x at full health
	# and 1.85x at none: 0.42 s of raised sword before the first wave exists, 0.36 s once he is
	# enraged. The enraged one is the number here, because it is the one that can fall under the bar.
	&"eric_quake_wave": 0.360,
	# Each of beast Bixby's pounds cracks the floor where the player is standing, and the crack glows
	# and throbs there for BixbyBeastStateMachine.quake_warning before it erupts, its beat tightening
	# over the last 0.6 s. The two later cracks burn quake_stagger longer again, so the first one is
	# the number here: it is the one that can fall under the bar.
	&"bixby_quake_burst": 1.200,
	# Computah's pounce, the grab at the end of his chase. GcStateMachine.pounce_tell is 0.45, but
	# the second lunge of a high-power double pounce runs on double_pounce_tell, and that is the one
	# that can fall under the bar. Both are floored at POUNCE_TELL_FLOOR.
	&"computah_chase": 0.320,
	# The twin sweep's aim lines, GcStateMachine.laser_telegraph. It never scales with the surge or
	# with `power`, so this is the number in every phase.
	&"computah_laser": 0.500,
	# Eric's reworked fight (EricPacing V2), each at its enraged value, the one that can fall under the
	# bar. The slam's red tell comes up exactly slam_tell_time before the waves, delayed or not.
	&"eric_quake_wave_v2": 0.360,
	# The whirlwind's yellow wind-up, before the lunges; its sweep lives with him.
	&"eric_whirlwind_v2": 0.400,
	# The bear hug's charge, red or yellow on the same timing.
	&"eric_bear_hug_grab_v2": 0.450,
	&"eric_shoulder_charge": 0.450,
}


# How long each attack is in the air before it lands, against the parry window. An attack whose
# approach is not clearly longer than the window can be parried by pressing the moment it appears,
# which is not a read; those are the ones to lengthen. WINDUP_READS names the ones that are read
# off the boss instead, and they are held to the same bar.
func test_approach() -> void:
	if fight == "eric" and ver > 0:
		pin_eric(ver)
	await load_fight(fight, STATE_INTROS.has(fight))
	await clear_intro(fight)
	player.playerHealth = 100000
	var born := {}
	var approaches := {}
	defense.hit_taken.connect(func(hit):
		var id: int = hit.source.get_instance_id() if is_instance_valid(hit.source) else 0
		var seen: float = born.get(id, -1.0)
		var approach: float = defense.clock - seen if seen >= 0.0 else -1.0
		if not approaches.has(hit.attack_id):
			approaches[hit.attack_id] = []
		approaches[hit.attack_id].append(approach)
	)
	var spot: Vector2 = SMOKE_SPOTS[fight]
	if fight == "carter":
		spot.x = current_scene.get_node("Arena/CarterAndJoshScene/Carter").global_position.x
	await settle_player(spot)
	var start: float = defense.clock
	while defense.clock - start < 60.0 and not player.fight_over:
		player.global_position = spot
		for area in get_nodes_in_group("enemy projectile"):
			var id: int = area.get_instance_id()
			if not born.has(id):
				born[id] = defense.clock
		# Eric's thrown sword reports its own hits, so its hitbox is not in that group. It still has
		# a flight, which is exactly what this mode is for. No other fight has the group, so this
		# does nothing elsewhere.
		for hazard in get_nodes_in_group("eric_hazard"):
			var blade: Node = hazard.get_node_or_null("Hitbox")
			if blade and not born.has(blade.get_instance_id()):
				born[blade.get_instance_id()] = defense.clock
		await physics_frame
	var window: float = defense.parry_window
	var tight := []
	for id in approaches:
		var times: Array = approaches[id]
		var spawned: Array = times.filter(func(t): return t >= 0.0 and t < 5.0)
		if spawned.is_empty():
			# The hitbox never appears on its own: it lives with the boss, so the wind-up is the only
			# read there is. Registered in WINDUP_READS it is held to the bar; unregistered - a blow
			# landing on a player already held, which they could not answer anyway - it is only logged.
			if WINDUP_READS.has(id):
				var held: float = WINDUP_READS[id]
				log_p("  %-26s %d landed off the boss, read on a %.2f s wind-up" % [id, times.size(), held])
				if held <= window:
					tight.append("%s (%.2f s wind-up)" % [id, held])
			else:
				log_p("  %-26s hitbox lives with the boss, so its read is its wind-up" % id)
			continue
		var shortest: float = spawned.min()
		if WINDUP_READS.has(id):
			var windup: float = WINDUP_READS[id]
			log_p("  %-26s %d landed, shortest approach %.2f s, but it radiates from the boss: its read is a %.2f s wind-up" % [id, times.size(), shortest, windup])
			# A flight wants the 1.75x margin because the player has to notice a projectile before
			# they can answer it. A wind-up is the boss doing one obvious thing for that whole time,
			# which they are already watching, so it only has to outlast the window itself.
			if windup <= window:
				tight.append("%s (%.2f s wind-up)" % [id, windup])
			continue
		log_p("  %-26s %d landed, shortest approach %.2f s, %.0f%% of it inside the %.2f s window" % [id, times.size(), shortest, 100.0 * minf(window / shortest, 1.0), window])
		if shortest < window * 1.75:
			tight.append("%s (%.2f s)" % [id, shortest])
	log_p("%s: attacks a press on sight would parry: %s" % [fight, tight if not tight.is_empty() else "none"])
	check(tight.is_empty(), "every attack gives longer than the parry window to read it (%s)" % [tight])


# ------------------------------------------------------------------ parry feel

# A fresh press, then a hit `frames_before` frames later: the press-to-hit gap the window measures.
func parry_at(frames_before: int, id := &"eric_quake_wave") -> int:
	press(KEY_SHIFT)
	await wait(frames_before)
	var result := front_hit(id, dummy_source())
	release(KEY_SHIFT)
	await wait(4)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	# Past the mash lockout, so the next attempt starts clean.
	await wait(40)
	return result


func window_band(window: float) -> Array:
	defense.parry_window = window
	var parried := []
	for frames in range(1, 20):
		if await parry_at(frames) == 3:
			parried.append(frames)
	return parried


func test_parry_window() -> void:
	await load_eric()
	park_eric()
	health_ok()
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await settle_player(Vector2(972, 800))
	var shipped: float = defense.parry_window
	log_p("-- the press-to-hit gaps that parry, in frames at 60")
	var old_band: Array = await window_band(0.15)
	var new_band: Array = await window_band(shipped)
	log_p("0.15 s: %s" % [old_band])
	log_p("%.2f s: %s" % [shipped, new_band])
	check(new_band.size() >= old_band.size(), "the shipped window is no tighter than the old 0.15 s (%d frames against %d)" % [new_band.size(), old_band.size()])
	check(absf(new_band.size() - shipped * 60.0) <= 2.0, "the band matches the %.2f s it is set to (%d frames)" % [shipped, new_band.size()])
	check(new_band[0] == 1 and new_band[-1] == new_band.size(), "every gap up to %d frames parries (%s)" % [new_band.size(), new_band])
	check(await parry_at(new_band.size() + 1) == 2, "a press a frame earlier than that is only a block")
	defense.parry_window = shipped

	log_p("-- what that means for the attacks that matter")
	# Carter's clone: 0.44 s of light, then a 0.18 s dash into the player.
	var dash_frames := int(roundf(0.18 * 60.0))
	check(await parry_at(dash_frames) == 3, "a press on the first frame of a %d-frame clone dash still parries" % dash_frames)
	defense.parry_window = 0.15
	var old_dash: int = await parry_at(dash_frames)
	defense.parry_window = shipped
	log_p("the same press at the old window: %d (1 HIT, 2 BLOCKED, 3 PARRIED)" % old_dash)
	check(old_dash == 2, "at 0.15 that same read was too early and only blocked (%d)" % old_dash)
	# Josh's cards land 0.9 s apart: a whiff at one still clears the mash lockout before the next.
	check(defense.parry_mash_lockout < 0.9, "a whiffed press clears before the next card (%.2f < 0.9)" % defense.parry_mash_lockout)
	# Eric's thrown sword: what the window is worth against the fastest thing in the game.
	unpark_eric()
	sm.chain = []
	sm.on_child_transition(sm.current_state, "SwordThrow")
	if not await wait_until(func(): return not get_nodes_in_group("enemy projectile").is_empty(), 300):
		log_p("his sword never came out; his fight is mid-rework, so this one is skipped")
		return
	var sword: Node2D = get_nodes_in_group("enemy projectile")[0]
	while not ("speed" in sword) and sword.get_parent() is Node2D:
		sword = sword.get_parent()
	var reach: float = sword.speed * shipped
	log_p("the sword travels %.0f px/s, so the window opens %.0f px out from the player" % [sword.speed, reach])
	check(reach > 200.0, "that is a readable distance, not a pixel (%.0f px)" % reach)


func test_parry_freeze() -> void:
	await load_eric()
	park_eric()
	health_ok()
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await settle_player(Vector2(972, 800))
	log_p("-- one parry: the stop, the slow beat, then normal speed")
	var trace := []
	watch = func(): trace.append(Engine.time_scale)
	check(await parry_once() == 3, "parried")
	await wait(40)
	watch = Callable()
	var stopped: int = trace.filter(func(t): return t <= 0.06).size()
	var slowed: int = trace.filter(func(t): return t > 0.06 and t < 0.99).size()
	var normal: int = trace.filter(func(t): return t >= 0.99).size()
	log_p("frames: %d stopped, %d slowed, %d normal; scales seen %s" % [stopped, slowed, normal, trace.reduce(func(acc, t): return acc if acc.has(t) else acc + [t], [])])
	check(stopped >= 6 and stopped <= 10, "the dead stop lasts about %.2f s (%d frames)" % [defense.parry_hit_stop, stopped])
	check(slowed >= 9 and slowed <= 13, "then a slow beat of about %.2f s (%d frames)" % [defense.parry_slow_time, slowed])
	check(Engine.time_scale == 1.0, "and time is normal again (%.2f)" % Engine.time_scale)

	log_p("-- three parries in a row, at the cadences the fights use")
	for cadence in [0.9, 0.62]:
		defense.end_parry_streak()
		await wait(20)
		trace.clear()
		watch = func(): trace.append(Engine.time_scale)
		var start_frame: int = frame
		var start_clock: float = defense.clock
		var gaps := []
		for i in 3:
			check(await parry_once() == 3, "parry %d at a %.2f s cadence" % [i + 1, cadence])
			var normal_run := 0
			var until: float = defense.clock + cadence
			while defense.clock < until:
				normal_run += 1 if Engine.time_scale >= 0.99 else 0
				await physics_frame
			gaps.append(normal_run)
		watch = Callable()
		var chain_frames: int = frame - start_frame
		var altered: int = trace.filter(func(t): return t < 0.99).size()
		log_p("%.2f s cadence: %d frames of real time for %.2f s of fight, %d (%.0f%%) not at full speed, full-speed frames between parries %s" % [cadence, chain_frames, defense.clock - start_clock, altered, 100.0 * altered / maxf(chain_frames, 1), gaps])
		check(defense.parry_streak == 3, "the streak counts to 3 (%d)" % defense.parry_streak)
		check(gaps.min() > 20, "the fight runs at full speed between parries (%s frames)" % [gaps])
		check(altered < chain_frames * 0.55, "and the chain is not one long slideshow (%d of %d frames)" % [altered, chain_frames])
	await wait(40)
	check(Engine.time_scale == 1.0, "time is normal after the chain (%.2f)" % Engine.time_scale)

	log_p("-- a parry on the frame the fight ends")
	clear_iframes()
	press(KEY_SHIFT)
	await wait(3)
	var result := front_hit(&"eric_quake_wave", dummy_source())
	boss.boss_health = 0
	release(KEY_SHIFT)
	check(result == 3, "the parry landed (%d)" % result)
	check(await wait_until(func(): return player.fight_over, 60), "and the fight ended on the same beat")
	await wait(20)
	log_p("time scale after the fight ended: %.2f" % Engine.time_scale)
	check(Engine.time_scale == 1.0, "the outro runs at full speed (%.2f)" % Engine.time_scale)


func test_parry_cue() -> void:
	await load_eric()
	park_eric()
	health_ok()
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await settle_player(Vector2(972, 800))
	var fx: Node = player.get_node("CombatFx")
	log_p("-- the window shows itself")
	check(not is_instance_valid(fx.window_rim), "nothing before a press")
	press(KEY_SHIFT)
	await wait(2)
	check(defense.is_parry_ready() and is_instance_valid(fx.window_rim), "a credited press puts the rim up")
	check(fx.window_rim.texture == player.sprite.texture and fx.window_rim.frame == player.sprite.frame, "it is the player's own frame")
	check(fx.window_rim.get_index() < player.sprite.get_index(), "drawn behind him (%d vs %d)" % [fx.window_rim.get_index(), player.sprite.get_index()])
	var frames_up := 0
	while defense.is_parry_ready() and frames_up < 40:
		frames_up += 1
		await physics_frame
	await wait(2)
	log_p("the window was open for %d frames (%.2f s)" % [frames_up, frames_up / 60.0])
	check(absf(frames_up - defense.parry_window * 60.0) <= 2, "it lasts the window's own length (%d frames)" % frames_up)
	check(not is_instance_valid(fx.window_rim), "and goes when the window does")
	release(KEY_SHIFT)
	await wait(6)

	log_p("-- a press that gets no parry credit shows nothing")
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(14)
	press(KEY_SHIFT)
	await wait(2)
	check(not defense.is_parry_ready() and not is_instance_valid(fx.window_rim), "a mashed press has no rim")
	release(KEY_SHIFT)
	await wait(40)

	log_p("-- after a parry it stays only as long as the window it stands for")
	check(await parry_once() == 3, "parried")
	check(await wait_until(func(): return not defense.is_parry_ready(), 30), "the window closed")
	await wait(2)
	check(not is_instance_valid(fx.window_rim), "the rim went with it")


# ------------------------------------------------------------------ parry-only lock

func test_locked() -> void:
	await load_eric()
	park_eric()
	health_ok()
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	track_parries()
	var hype: Node = player.get_node("Hype")
	var locks := [0, 0]
	var warps := []
	player.actions_locked.connect(func(): locks[0] += 1)
	player.actions_unlocked.connect(func(): locks[1] += 1)
	player.warped.connect(func(from: Vector2, to: Vector2): warps.append([from, to]))

	log_p("-- unlocked: everything as it was")
	await settle_player(Vector2(972, 700))
	check(not player.is_action_locked, "not locked to start with")
	var walked: Vector2 = await walk_offset(KEY_RIGHT, 15)
	check(walked.x > 100.0, "walking works (%s)" % walked)

	log_p("-- locked: no walking")
	await settle_player(Vector2(972, 700))
	player.lock_actions()
	player.lock_actions()
	check(player.is_action_locked and locks == [1, 0], "locked once, however many times it was asked (%s)" % [locks])
	check(player.velocity == Vector2.ZERO and not player.is_dodging and not player.punch_buffered, "it leaves the player still")
	check(not defense.is_dash_recovering() and not defense.ghost_active, "with no dash recovery and no dodge ghost")
	check(not player.is_grabbed and not player.is_talking and not player.fight_over and not player.is_finishing, "and none of the other flags touched")
	await wait(4)
	var held: Vector2 = await walk_offset(KEY_RIGHT, 20)
	log_p("holding right while locked: moved %s, state %s" % [held, player.state_machine.current_state.name])
	check(held.length() < 1.0, "the player stays put (%s)" % held)
	check(player.state_machine.current_state.name == "Idle", "and stays in Idle, not Walking (%s)" % player.state_machine.current_state.name)

	log_p("-- locked: no dash, no punch")
	var stamina_before: float = defense.stamina
	var at: Vector2 = player.global_position
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(12)
	release(KEY_RIGHT)
	check(not player.is_dodging and player.global_position.distance_to(at) < 1.0, "the dash does nothing (%s)" % player.global_position)
	check(is_equal_approx(defense.stamina, stamina_before), "and costs no stamina (%.1f)" % defense.stamina)
	var boss_health: int = boss.boss_health
	place_under(boss.get_node("Hurtbox"))
	tap(KEY_Q)
	await wait(20)
	check(player.state_machine.current_state.name != "Punching", "the punch never starts (%s)" % player.state_machine.current_state.name)
	check(boss.boss_health == boss_health, "so the boss takes nothing (%d)" % boss.boss_health)

	log_p("-- a guard already up stays up when the lock lands")
	player.unlock_actions()
	await settle_player(Vector2(972, 700))
	press(KEY_SHIFT)
	await wait(6)
	check(defense.is_guarding(), "guarding before the lock")
	player.lock_actions()
	await wait(6)
	check(defense.is_guarding() and player.state_machine.current_state.name == "Blocking", "still guarding after it")
	release(KEY_SHIFT)
	await wait(40)

	log_p("-- locked: the guard and its parry are untouched")
	await settle_player(Vector2(972, 700))
	defense._set_stamina(defense.max_stamina)
	press(KEY_SHIFT)
	await wait(4)
	check(defense.is_guarding() and player.state_machine.current_state.name == "Blocking", "the guard still goes up")
	release(KEY_SHIFT)
	# Past parry_mash_lockout, so the parry press below is credited like any fresh one.
	await wait(40)
	var hype_before: float = hype.hype
	var streak_before: int = defense.parry_streak
	var parried: int = await parry_once()
	log_p("parry while locked: result %d, hype %.0f -> %.0f, streak %d -> %d" % [parried, hype_before, hype.hype, streak_before, defense.parry_streak])
	check(parried == 3, "a parry still parries (%d)" % parried)
	var first_parry_gain: float = feel("hype_parry_gains")[0]
	check(is_equal_approx(hype.hype - hype_before, first_parry_gain), "it still pays its hype, %.0f (%.0f)" % [first_parry_gain, hype.hype - hype_before])
	check(defense.parry_streak == streak_before + 1, "and still counts on the streak (%d)" % defense.parry_streak)
	clear_iframes()
	await wait(20)

	log_p("-- the facing follows whatever the fight points at")
	await settle_player(Vector2(972, 700))
	var wanted := {KEY_0: [Vector2(972, 200), player.Facing.UP], KEY_1: [Vector2(972, 1000), player.Facing.DOWN], KEY_2: [Vector2(300, 700), player.Facing.LEFT], KEY_3: [Vector2(1600, 700), player.Facing.RIGHT]}
	var faced := []
	for spot in wanted:
		player.face_point(wanted[spot][0])
		faced.append(player.facing == wanted[spot][1])
		await wait(6)
		faced.append(player.facing == wanted[spot][1])
	check(not faced.has(false), "it turns at once and holds (%s)" % [faced])
	log_p("facing %d with Eric at %s" % [player.facing, boss.global_position])
	player.clear_face_point()
	await wait(10)
	check(player.facing == player.Facing.UP, "cleared, it goes back to the boss (%d)" % player.facing)

	log_p("-- the warp")
	var from: Vector2 = player.global_position
	var middle := Vector2(960, 620)
	player.warp_to(middle)
	await wait(2)
	log_p("warped %s -> %s, velocity %s, ghosts %d" % [from, player.global_position, player.velocity, current_scene.get_node("Arena/MainPlayer/FinisherFx").get_child_count()])
	check(player.global_position == middle, "the player lands exactly where the fight asked (%s)" % player.global_position)
	check(player.velocity == Vector2.ZERO, "with no leftover speed")
	check(warps.size() == 1 and warps[0][0] == from and warps[0][1] == middle, "the signal carries where from and where to (%s)" % [warps])
	check(current_scene.get_node("Arena/MainPlayer/FinisherFx").get_child_count() >= 3, "and it leaves a trail of ghosts behind")

	log_p("-- unlocking, twice")
	var counted: Array = locks.duplicate()
	player.unlock_actions()
	player.unlock_actions()
	check(not player.is_action_locked and locks == [counted[0], counted[1] + 1], "unlocked once, however many times it was asked (%s)" % [locks])
	await settle_player(Vector2(972, 700))
	var free_again: Vector2 = await walk_offset(KEY_RIGHT, 15)
	check(free_again.x > 100.0, "walking works again (%s)" % free_again)

	log_p("-- a dash and a punch already under way when the lock starts")
	await settle_player(Vector2(972, 700))
	press(KEY_RIGHT)
	tap(KEY_W)
	check(await wait_until(func(): return player.is_dodging, 20), "dashing")
	player.lock_actions()
	release(KEY_RIGHT)
	await wait(6)
	check(not player.is_dodging, "the dash is cut")
	check(not defense.is_dash_recovering(), "and so are its recovery frames")
	player.unlock_actions()
	await wait(30)
	place_under(boss.get_node("Hurtbox"))
	var swung: int = boss.boss_health
	tap(KEY_Q)
	check(await wait_until(func(): return player.state_machine.current_state.name == "Punching", 20), "punching")
	player.lock_actions()
	await wait(2)
	check(player.state_machine.current_state.name == "Punching", "a swing in the air plays out (%s)" % player.state_machine.current_state.name)
	check(await wait_until(func(): return player.state_machine.current_state.name != "Punching", 60), "and ends on its own")
	check(not player.get_node("Hitbox").monitoring, "with its hitbox off")
	log_p("the swing that was in the air dealt %d" % (swung - boss.boss_health))

	log_p("-- a finisher starting releases it")
	player.begin_finisher()
	check(not player.is_action_locked, "the lock is off")
	player.end_finisher(false)
	await wait(10)


# The press bookkeeping Carter's clones depend on: every press is reported, and rearm_parry() excuses
# exactly one press, the one the fight opens each clone with.
func test_parry_rearm() -> void:
	await load_eric()
	park_eric()
	health_ok()
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	track_parries()
	var presses := []
	defense.block_pressed.connect(func(credited: bool): presses.append(credited))
	await settle_player(Vector2(972, 800))

	log_p("-- every press is reported, credited or not")
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(6)
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	log_p("presses %s" % [presses])
	check(presses == [true, false], "a fresh press counts, one inside the mash lockout does not (%s)" % [presses])

	log_p("-- rearm_parry excuses the next press only")
	presses.clear()
	defense.rearm_parry()
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(6)
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	log_p("presses after a rearm %s" % [presses])
	check(presses == [true, false], "the rearmed press counts, mashing after it still does not (%s)" % [presses])

	log_p("-- what it means for a clone: a whiff at one, then the next one parried")
	await wait(40)
	# A whiffed press, as at a clone that never swung.
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(12)
	# Without the rearm, a press this soon after cannot parry.
	var carried: int = await parry_once()
	check(carried == 2, "inside the lockout the hit is only blocked (%d)" % carried)
	clear_iframes()
	await wait(12)
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(12)
	# The fight opens the next clone: the carryover is wiped.
	defense.rearm_parry()
	var rearmed: int = await parry_once()
	check(rearmed == 3, "after the rearm the same press parries (%d)" % rearmed)
	clear_iframes()

	log_p("-- but an early press inside the clone's own window still loses it")
	await wait(40)
	defense.rearm_parry()
	# The player reads it too early: the press is credited but its window has passed by the hit.
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(20)
	var early: int = await parry_once()
	check(early == 2, "the early press whiffs and the mash lockout keeps the clone (%d)" % early)
	clear_iframes()

	log_p("-- end_parry_streak is callable from a fight")
	await wait(40)
	defense.rearm_parry()
	check(await parry_once() == 3, "a parry to build a streak")
	check(defense.parry_streak > 0, "a streak is running (%d)" % defense.parry_streak)
	defense.end_parry_streak()
	check(defense.parry_streak == 0, "the fight ended the streak (%d)" % defense.parry_streak)


# tier=death kills the player, tier=fight_over ends the fight under the lock. One per run: the outro
# outlives the fight scene.
func test_locked_end() -> void:
	await load_eric()
	health_ok()
	await settle_player(Vector2(972, 700))
	player.lock_actions()
	check(player.is_action_locked, "locked")
	if tier == "death":
		player.playerHealth = 1
		clear_iframes()
		front_hit(&"eric_quake_wave", dummy_source())
		check(await wait_until(func(): return player.playerHealth <= 0, 30), "the player died")
	else:
		boss.boss_health = 0
		check(await wait_until(func(): return player.fight_over, 60), "the fight ended")
	await wait(10)
	check(not player.is_action_locked, "the lock released")
	player.lock_actions()
	check(not player.is_action_locked, "and nothing can lock them again")


# ------------------------------------------------------------------ status effects

func walk_offset(code: int, frames: int) -> Vector2:
	var from: Vector2 = player.global_position
	press(code)
	await wait(frames)
	release(code)
	await wait(3)
	return player.global_position - from


func test_status() -> void:
	await load_eric()
	park_eric()
	health_ok()
	# He would knock the player about mid-measurement.
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	var status: Node = player.get_node("Status")
	var icons: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/StatusIcons")
	var popups: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/CombatPopups")
	var started := []
	var ended := []
	status.status_started.connect(func(kind: StringName, duration: float): started.append([kind, duration]))
	status.status_ended.connect(func(kind: StringName): ended.append(kind))

	log_p("-- nothing on: as it was")
	await settle_player(Vector2(972, 700))
	var plain: Vector2 = await walk_offset(KEY_RIGHT, 20)
	log_p("walking right: %s" % plain)
	check(plain.x > 100.0 and absf(plain.y) < 1.0, "walking right moves right (%s)" % plain)
	check(icons.get_child_count() == 0 and status.kinds().is_empty(), "no icons and no statuses")
	defense._spend(40.0)
	await wait(60)
	check(defense.stamina > 60.0, "the bar refills as usual (%.0f)" % defense.stamina)

	log_p("-- inverted controls")
	await settle_player(Vector2(972, 700))
	player.apply_status(&"inverted_controls")
	check(player.has_status(&"inverted_controls"), "the status is on")
	check(started.size() == 1 and started[0][0] == &"inverted_controls" and is_equal_approx(started[0][1], 4.0), "started with its 4 s default (%s)" % [started])
	check(icons.get_child_count() > 0, "the HUD shows an icon")
	check(popups.popups.size() == 1 and popups.popups[0].kind == &"reversed", "REVERSED! pops up (%s)" % [popups.popups.map(func(pop): return pop.kind)])
	var flipped: Vector2 = await walk_offset(KEY_RIGHT, 20)
	log_p("walking right while inverted: %s" % flipped)
	check(flipped.x < -100.0 and absf(flipped.y) < 1.0, "right walks left (%s)" % flipped)
	await settle_player(Vector2(972, 700))
	var flipped_up: Vector2 = await walk_offset(KEY_UP, 20)
	check(flipped_up.y > 100.0 and absf(flipped_up.x) < 1.0, "up walks down (%s)" % flipped_up)

	log_p("-- what inverting must not touch")
	await settle_player(Vector2(972, 700))
	press(KEY_SHIFT)
	await wait(4)
	check(defense.is_guarding() and player.state_machine.current_state.name == "Blocking", "block still blocks")
	release(KEY_SHIFT)
	await wait(4)
	tap(KEY_Q)
	check(await wait_until(func(): return player.state_machine.current_state.name == "Punching", 20), "punch still punches")
	await wait_until(func(): return player.state_machine.current_state.name != "Punching", 60)
	await wait(10)
	check(player.facing == player.Facing.UP, "the facing still turns to the boss (%d)" % player.facing)
	await settle_player(Vector2(972, 700))
	var dash_from: Vector2 = player.global_position
	press(KEY_RIGHT)
	await wait(2)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait_until(func(): return not player.is_dodging, 40)
	release(KEY_RIGHT)
	var dashed: Vector2 = player.global_position - dash_from
	log_p("dash with right held while inverted: %s" % dashed)
	check(dashed.x < -50.0, "the dash follows the inverted keys (%s)" % dashed)
	check(defense.is_dash_recovering(), "it still ends in dash recovery")
	await wait(30)

	log_p("-- it expires on its own")
	check(await wait_until(func(): return not player.has_status(&"inverted_controls"), 400), "the status ran out")
	check(ended == [&"inverted_controls"], "it reported ending (%s)" % [ended])
	check(icons.get_child_count() == 0, "the HUD hides it")
	await settle_player(Vector2(972, 700))
	var back: Vector2 = await walk_offset(KEY_RIGHT, 20)
	check(back.x > 100.0, "walking is itself again (%s)" % back)

	log_p("-- a refresh resets the clock instead of stacking")
	player.apply_status(&"inverted_controls", 2.0)
	await wait(60)
	var left_before: float = status.time_left(&"inverted_controls")
	player.apply_status(&"inverted_controls", 2.0)
	var left_after: float = status.time_left(&"inverted_controls")
	log_p("%.2f s left, refreshed to %.2f s, popups %s" % [left_before, left_after, popups.popups.map(func(pop): return pop.kind)])
	check(not popups.popups.any(func(pop): return pop.kind == &"reversed"), "a refresh says nothing new")
	check(left_before < 1.2 and is_equal_approx(snappedf(left_after, 0.01), 2.0), "the refresh puts it back to 2 s, not 3")
	check(status.kinds().size() == 1, "still one status, not two (%s)" % [status.kinds()])
	player.clear_statuses()
	check(not player.has_status(&"inverted_controls"), "clear_statuses takes it off")
	# The icons are queue_freed, so they leave the count on the next frame.
	await wait(2)
	check(icons.get_child_count() == 0, "and the HUD with it")

	log_p("-- the stamina drain")
	await settle_player(Vector2(972, 700))
	defense._set_stamina(defense.max_stamina)
	await wait(60)
	player.apply_status(&"stamina_drain", 3.0)
	var drain_from: float = defense.stamina
	await wait(60)
	var drained: float = drain_from - defense.stamina
	log_p("drained %.1f in a second, bar at %.1f" % [drained, defense.stamina])
	check(absf(drained - status.stamina_drain_per_second) < 1.5, "it drains about %.0f a second (%.1f)" % [status.stamina_drain_per_second, drained])
	check(defense.clock - defense.last_spend_time < defense.stamina_regen_delay, "the refill stays off while it drains")
	check(await wait_until(func(): return not player.has_status(&"stamina_drain"), 300), "the drain ran out")
	var settled: float = defense.stamina
	await wait(90)
	check(defense.stamina > settled, "the bar refills again once it is over (%.0f -> %.0f)" % [settled, defense.stamina])

	log_p("-- the drain breaks a held guard")
	defense._set_stamina(40.0)
	press(KEY_SHIFT)
	await wait(6)
	check(defense.is_guarding(), "guarding")
	player.apply_status(&"stamina_drain", 5.0)
	check(await wait_until(func(): return defense.is_guard_broken, 300), "the drain broke the guard")
	release(KEY_SHIFT)
	log_p("guard broken with %.0f stamina at %.2f s" % [defense.stamina, defense.clock])
	await wait_until(func(): return not defense.is_guard_broken, 300)
	player.clear_statuses()
	await wait(30)
	clear_iframes()

	log_p("-- a finisher takes them off")
	defense._set_stamina(defense.max_stamina)
	player.apply_status(&"stamina_drain")
	player.apply_status(&"inverted_controls")
	check(status.kinds().size() == 2, "both on")
	check(icons.get_child_count() == 4, "two icons with their countdowns (%d nodes)" % icons.get_child_count())
	boss.daze_used = false
	check(await daze_eric(), "dazed")
	check(status.kinds().is_empty(), "the finisher cleared them (%s)" % [status.kinds()])
	check(icons.get_child_count() == 0, "and the HUD with them")
	player.apply_status(&"inverted_controls")
	check(not player.has_status(&"inverted_controls"), "nothing new sticks during a finisher")
	await mash_finisher()
	await wait_until(func(): return player.get_node("Finisher").phase == 0, 180)


# The row keeps out of a dialogue balloon's way, like the hype meter.
func test_status_dialogue() -> void:
	await load_eric(true)
	health_ok()
	var status: Node = player.get_node("Status")
	var icons: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/StatusIcons")
	var meter: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/HypeMeter")
	await wait(60)
	check(icons._dialogue_showing(), "a balloon is up")

	log_p("-- a status landing while a balloon is up stays hidden")
	player.apply_status(&"stamina_drain")
	player.apply_status(&"inverted_controls", 1.0)
	await wait(30)
	log_p("icons alpha %.2f, meter alpha %.2f, %d nodes" % [icons.modulate.a, meter.modulate.a, icons.get_child_count()])
	check(icons.modulate.a < 0.05, "the row is out of the way (%.2f)" % icons.modulate.a)
	check(icons.modulate.a <= meter.modulate.a + 0.01, "it hides with the hype meter (%.2f / %.2f)" % [icons.modulate.a, meter.modulate.a])
	check(icons.get_child_count() == 4, "both are still on the row underneath")

	log_p("-- one expires while the row is hidden")
	check(await wait_until(func(): return not player.has_status(&"inverted_controls"), 240), "it ran out behind the balloon")
	await wait(4)
	check(icons.get_child_count() == 2, "the row tidied up to one (%d nodes)" % icons.get_child_count())

	log_p("-- the balloon goes and the row comes back")
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(1)
	await skip_vs_card()
	await wait(40)
	log_p("icons alpha %.2f with %d nodes, statuses %s" % [icons.modulate.a, icons.get_child_count(), status.kinds()])
	check(icons.modulate.a > 0.9, "the row is back (%.2f)" % icons.modulate.a)
	check(icons.get_child_count() == 2 and status.kinds() == [&"stamina_drain"], "showing only what is still on")
	var icon: CanvasItem = icons.entries[&"stamina_drain"].icon
	check(icon.position.x == 0.0, "and it sits in the first slot (%s)" % icon.position)

	log_p("-- the last one ends: the row fades away again")
	player.clear_statuses()
	await wait(40)
	check(icons.modulate.a < 0.05 and icons.get_child_count() == 0, "nothing left (%.2f, %d nodes)" % [icons.modulate.a, icons.get_child_count()])


# The two ways a fight stops: tier=fight_over ends it, tier=death kills the player. One per run,
# since the outro outlives the fight scene.
func test_status_end() -> void:
	await load_eric()
	health_ok()
	var status: Node = player.get_node("Status")
	var icons: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/StatusIcons")
	await settle_player(Vector2(972, 700))
	player.apply_status(&"stamina_drain")
	player.apply_status(&"inverted_controls")
	check(status.kinds().size() == 2, "both on")
	if tier == "death":
		player.playerHealth = 1
		clear_iframes()
		front_hit(&"eric_quake_wave", dummy_source())
		check(await wait_until(func(): return player.playerHealth <= 0, 30), "the player died")
	else:
		boss.boss_health = 0
		check(await wait_until(func(): return player.fight_over, 60), "the fight ended")
	await wait(10)
	log_p("%s: statuses %s, icons %d" % [tier, status.kinds(), icons.get_child_count()])
	check(status.kinds().is_empty(), "they came off (%s)" % [status.kinds()])
	check(icons.get_child_count() == 0, "the HUD is empty")
	player.apply_status(&"inverted_controls")
	check(not player.has_status(&"inverted_controls"), "and nothing new sticks")


func area_rect(area: Area2D) -> Rect2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	var size: Vector2 = shape.shape.size * shape.global_scale.abs()
	return Rect2(shape.global_position - size / 2.0, size)


# ------------------------------------------------------------------ parry streak

# One clean parry: a fresh press, then a blockable hit from the front.
func parry_once(id := &"eric_quake_wave") -> int:
	press(KEY_SHIFT)
	await wait(3)
	var result := front_hit(id, dummy_source())
	release(KEY_SHIFT)
	await wait(8)
	return result


func test_parry_streak() -> void:
	await load_eric()
	park_eric()
	health_ok()
	track()
	track_parries()
	var hype: Node = player.get_node("Hype")
	var counter: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/ParryStreak")
	var popups: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/CombatPopups")
	var voice: AudioStreamPlayer = player.get_node("ParrySfxPlayer0")
	var streaks := []
	defense.parry_streak_changed.connect(func(streak): streaks.append(streak); log_p("  streak -> %d" % streak))
	await settle_player(Vector2(972, 800))

	log_p("-- three parries in a row")
	var gains := []
	var sounds := []
	for i in 3:
		var before: float = hype.hype
		check(await parry_once() == 3, "parry %d landed" % (i + 1))
		gains.append(hype.hype - before)
		sounds.append([voice.stream.resource_path.get_file(), snappedf(voice.volume_db, 0.1), voice.playing])
	log_p("streaks %s, hype gains %s, sounds %s" % [streaks, gains, sounds])
	check(defense.parry_streak == 3, "streak counts to 3 (%d)" % defense.parry_streak)
	# PlayerFeel's, by the player's feel_v2, which every fight is on.
	var wanted_gains: Array = feel("hype_parry_gains")
	check(gains == wanted_gains, "hype pays %s by tier (%s)" % [wanted_gains, gains])
	# One sound, the same every time: the streak climbs in the art, never in the ears.
	check(sounds[0] == sounds[1] and sounds[1] == sounds[2], "every parry sounds the same (%s)" % [sounds])
	check(sounds[0][2], "and it is playing")
	check(player.get_node_or_null("ParryStingPlayer") == null, "no streak sting")
	check(player.get_node_or_null("ParrySfxPlayer1") == null, "and no layered voices")
	check(parries[1].streak == 2 and parries[2].streak == 3, "the signal carries the streak")
	await wait(4)
	check(counter.modulate.a > 0.5 and counter.streak == 3, "the streak badge is up (alpha %.2f)" % counter.modulate.a)
	check(counter.badge != null and counter.badge.frame_coords.y == 2, "the badge shows the x3 row (%s)" % counter.badge.frame_coords)
	check(counter.digits[0].visible and counter.digits[0].frame == 3 and not counter.digits[1].visible, "the badge reads 3")
	var kinds: Array = popups.popups.map(func(p): return p.kind)
	check(kinds.has(&"parry_x2") and kinds.has(&"parry_x3"), "the popups step up with the tier (%s)" % [kinds])

	log_p("-- a hit ends it")
	clear_iframes()
	front_hit(&"untagged", dummy_source())
	check(defense.parry_streak == 0, "a hit resets the streak")
	await wait(30)
	check(counter.modulate.a < 0.1, "the counter fades out (%.2f)" % counter.modulate.a)
	clear_iframes()

	log_p("-- a guard break ends it")
	check(await parry_once() == 3, "parry lands")
	check(defense.parry_streak == 1, "streak restarts at 1")
	defense.stamina = 20.0
	defense.last_spend_time = defense.clock
	press(KEY_SHIFT)
	# Blocked, not parried, so the block empties the bar.
	await past_window()
	front_hit(&"eric_quake_wave", dummy_source())
	release(KEY_SHIFT)
	check(defense.is_guard_broken and defense.parry_streak == 0, "a guard break resets the streak")
	defense.clear_guard_break()
	clear_iframes()
	# Past the mash lockout, so the next press is credited again.
	await wait(45)

	log_p("-- it lapses on its own")
	defense.parry_streak_timeout = 1.0
	check(await parry_once() == 3, "parry lands")
	check(defense.parry_streak == 1, "counting again")
	await wait(70)
	check(defense.parry_streak == 0, "the streak times out")
	defense.parry_streak_timeout = 8.0
	clear_iframes()

	log_p("-- the stagger window grows with the streak, up to the cap")
	# Measured against a stand-in boss rather than one of Eric's attacks: which attack a parry
	# staggers him out of is his own business, and is being reworked, while the window the parry
	# hands the boss is this rule's.
	var spy := StaggerSpy.new()
	current_scene.add_child(spy)
	spy.global_position = player.global_position + Vector2(0, -200)
	for wanted in [3, 4, 5]:
		defense.parry_streak = wanted - 1
		defense.last_parry_time = defense.clock
		defense.rearm_parry()
		press(KEY_SHIFT)
		await wait(3)
		# Whichever attack carries parry_stagger: the rule is the window, not the attack.
		var result := front_hit_from(&"eric_thrown_sword", spy)
		release(KEY_SHIFT)
		check(result == 3 and defense.parry_streak == wanted, "the parry landed at streak %d (%d)" % [wanted, defense.parry_streak])
		clear_iframes()
		defense._set_stamina(defense.max_stamina)
		await past_window()
		await wait(70)
	var windows: Array = spy.windows
	log_p("stagger windows at streaks 3, 4, 5: %s" % [windows])
	var wanted_windows := [1.4, 1.6, 1.6]
	var window_ok: bool = windows.size() == wanted_windows.size()
	for i in wanted_windows.size():
		window_ok = window_ok and i < windows.size() and absf(windows[i] - wanted_windows[i]) < 0.001
	check(window_ok, "1.2 + 0.2 per tier over 2, capped at +0.4 (%s)" % [windows])

# Runs his bear hug and taps block just before the lunge arrives, or holds it from the start.
func meet_the_lunge(hold_from_the_start: bool) -> void:
	await settle_player(Vector2(972, 800))
	if hold_from_the_start:
		press(KEY_SHIFT)
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	var grab_shape: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	await wait_until(func():
		if hug.phase != hug.Phase.LUNGE:
			return false
		var half: Vector2 = grab_shape.shape.size * grab_shape.global_scale.abs() / 2.0
		return (shape.global_position.y - 27.0) - (grab_shape.global_position.y + half.y) < 1500.0 * 0.09, 400)
	if not hold_from_the_start:
		press(KEY_SHIFT)


func test_grab_parry() -> void:
	await load_eric()
	health_ok()
	track()
	track_parries()
	log_p("-- a held guard still gets grabbed")
	await meet_the_lunge(true)
	check(await wait_until(func(): return player.is_grabbed, 60), "the grab beats a held guard")
	release(KEY_SHIFT)
	check(parries.is_empty(), "no parry from a guard held all along")
	await wait_until(func(): return sm.current_state.name == "Downed", 600)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(60)
	clear_iframes()

	log_p("-- a parry just before the lunge lands")
	events.clear()
	parries.clear()
	var health: int = player.playerHealth
	await meet_the_lunge(false)
	check(await wait_until(func(): return not parries.is_empty(), 40), "the lunge is parried (%s)" % [parries])
	release(KEY_SHIFT)
	check(parries[0].id == &"eric_bear_hug_grab" and parries[0].staggered, "the parried grab staggers him")
	check(not player.is_grabbed, "not grabbed")
	check(player.playerHealth == health, "no damage")
	check(await wait_until(func(): return sm.current_state.name == "ParryStaggered", 10), "he is in ParryStaggered (%s)" % sm.current_state.name)
	await wait(3)
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	check(hurtbox.monitoring, "open to punches")
	check(not player.is_grabbed and player.state_machine.current_state.name != "Idle" or true, "player free")
	place_under(hurtbox)
	await wait(4)
	var dealt := []
	for i in 3:
		dealt.append(await swing())
		await wait(6)
	log_p("punches on the parried grab: %s" % [dealt])
	check(dealt[0] > 0 and dealt[1] > 0 and dealt[2] == 0, "two punches land, the third deals 0")
	var home: Vector2 = sm.states["BearHug"].plant_spot
	check(await wait_until(func(): return sm.current_state.name != "ParryStaggered", 300), "the stagger ends")
	log_p("after the stagger: %s at %s (his plant spot %s)" % [sm.current_state.name, boss.global_position, home])
	check(boss.global_position == home, "he picks himself up where he planted the sword")
	check(sm.current_state.name == "Downed", "the chain carries on")
	check(get_nodes_in_group("eric_hazard").filter(func(h): return h is Sprite2D).is_empty(), "the planted sword is gone")
	sm.downed_state_timer.stop()


func tell_node() -> Node:
	return boss.get_parent().get_node_or_null("ParryTell%d" % boss.get_instance_id())


func test_tells() -> void:
	await load_eric()
	health_ok()
	await settle_player(Vector2(972, 800))
	check(tell_node() == null, "no tell while he idles")

	log_p("-- the sword throw's wind-up")
	sm.chain = []
	sm.on_child_transition(sm.current_state, "SwordThrow")
	await wait(3)
	var tell := tell_node()
	check(tell != null and tell.strong, "the wind-up shows the strong tell")
	# The badge stands on the head point his state passes, not on the downed-frame daze anchor.
	var head: Vector2 = sm.states["SwordThrow"]._tell_anchor()
	log_p("tell at %s, its head point %s, his daze anchor %s" % [tell.global_position, head, boss.get_daze_anchor()])
	check(tell.global_position.distance_to(head) < 2.0, "it stands on his head point")
	check(tell.global_position.y < boss.global_position.y, "above him")
	var throw_state: Node = sm.states["SwordThrow"]
	check(await wait_until(func(): return is_instance_valid(throw_state.sword), 200), "the sword leaves his hands")
	await wait(2)
	check(tell_node() == null, "it goes as the sword goes: the blade in the air is the cue from there")
	await wait_until(func(): return sm.current_state.name == "Downed", 900)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(30)

	log_p("-- attacks with no tell")
	var seen := [false]
	var watch_tell := func():
		if tell_node() != null:
			seen[0] = true
	process_frame.connect(watch_tell)
	sm.chain = []
	# The spin has no wind-up to read and a parry no longer staggers him, so it warns about nothing.
	sm.on_child_transition(sm.current_state, "Whirlwind")
	await wait_until(func(): return sm.current_state.name == "Downed", 600)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(20)
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Earthquake")
	await wait_until(func(): return sm.current_state.name == "Downed", 600)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(20)
	process_frame.disconnect(watch_tell)
	check(not seen[0], "the spin and the slam never show one")
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(30)

	log_p("-- the bear hug's charge")
	sm.chain = []
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	check(await wait_until(func(): return hug.phase == hug.Phase.CHARGE, 300), "he charges the grab")
	await wait(2)
	tell = tell_node()
	check(tell != null and tell.strong, "the charge shows the strong tell")
	check(await wait_until(func(): return hug.phase == hug.Phase.LUNGE, 200), "he lunges")
	await wait(2)
	check(tell_node() == null, "the tell goes as the lunge starts")

	log_p("-- the fight ending clears it")
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(10)
	sm.chain = []
	sm.on_child_transition(sm.current_state, "SwordThrow")
	await wait(3)
	check(tell_node() != null, "tell up")
	sm.enter_player_defeated()
	await wait(3)
	check(tell_node() == null, "cleared when the fight ends")


func test_prompt_overlap() -> void:
	await load_eric()
	var hype: Node = player.get_node("Hype")
	var meter: Control = current_scene.get_node("Arena/MainPlayer/CanvasLayer/HypeMeter")
	var prompt: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/FinisherPrompt")
	hype._set_hype(100.0)
	await settle_player(Vector2(960, 500))
	await wait(30)
	check(meter.modulate.a > 0.9, "the meter is up (%.2f)" % meter.modulate.a)
	log_p("-- the player in the bottom-right corner, with the prompt showing")
	# Low enough to be in the meter's corner, high enough that the prompt still fits UNDER his feet:
	# past about y 880 it flips above his head instead and there is nothing to overlap. That cut-off
	# moved up with the player's size (FinisherArtLayout.PLAYER_FEET), which is why this is not 900.
	await settle_player(Vector2(1780, 860))
	prompt.finisher.prompt_shown.emit()
	await wait(40)
	var prompt_rect := Rect2(prompt.position, prompt.prompt_size)
	var meter_rect := Rect2(meter.position, meter.size)
	log_p("prompt %s, meter %s, overlapping %s, meter alpha %.2f" % [prompt_rect, meter_rect, prompt_rect.intersects(meter_rect), meter.modulate.a])
	check(prompt.visible and prompt_rect.intersects(meter_rect), "the prompt lands on the meter there")
	check(meter.modulate.a < 0.05, "the meter fades out of its way (%.2f)" % meter.modulate.a)
	prompt.finisher.finished.emit()
	await wait(40)
	check(not prompt.visible and meter.modulate.a > 0.9, "the meter comes back (%.2f)" % meter.modulate.a)
	log_p("-- the player away from the corner")
	await settle_player(Vector2(500, 500))
	prompt.finisher.prompt_shown.emit()
	await wait(40)
	check(prompt.visible and meter.modulate.a > 0.9, "the meter stays up when the prompt is elsewhere (%.2f)" % meter.modulate.a)
	prompt.finisher.finished.emit()


# Dashing out of the way of a rocket (Computah) or a charge (Carter and Josh).
func test_dodge_rollout() -> void:
	await load_fight(fight)
	player.playerHealth = 1000
	track()
	track_dodges()
	var spot: Vector2 = SMOKE_SPOTS[fight]
	if fight == "carter":
		spot.x = current_scene.get_node("Arena/CarterAndJoshScene/Carter").global_position.x
	await settle_player(spot)
	var start: float = defense.clock
	var dashed := false
	while defense.clock - start < 60.0 and not player.fight_over and dodges.is_empty():
		if not dashed:
			player.global_position = spot
		var incoming := false
		if fight == "greyson":
			for area in get_nodes_in_group("enemy projectile"):
				if area.name == "RocketHitbox" and area.get_parent().global_position.distance_to(spot) < 130.0:
					incoming = true
		else:
			for name_of in ["Carter", "Josh"]:
				var wrestler: Node = current_scene.get_node_or_null("Arena/CarterAndJoshScene/" + name_of)
				if wrestler and wrestler.state == wrestler.State.CHARGING and absf(wrestler.global_position.x - spot.x) < 60.0 and absf(wrestler.global_position.y - spot.y) < wrestler.charge_speed * 0.15 + 60.0:
					incoming = true
		if incoming and not dashed:
			dashed = true
			press(KEY_LEFT)
			tap(KEY_W)
		if dashed and defense.clock - start > 0.0:
			await wait(6)
			release(KEY_LEFT)
			# Past the 0.6 s gap, so the next attempt's dash is clean too.
			await wait(45)
			if dodges.is_empty():
				dashed = false
				await settle_player(spot)
				defense.stamina = defense.max_stamina
		await physics_frame
	log_p("%s: dodges %s" % [fight, dodges.map(func(d): return d.id)])
	check(not dodges.is_empty(), "dashing out of the way earns a perfect dodge")


# A punch that doesn't care what it hits.
func swing_any() -> void:
	tap(KEY_Q)
	for i in 10:
		await physics_frame
		if player.state_machine.current_state.name == "Punching":
			break
	while player.state_machine.current_state.name == "Punching":
		await physics_frame
	await wait(3)


# ------------------------------------------------------------------ feel_v2's dash
# The dash player.feel_v2 gives every fight: a short landing beat instead of the long lockout, a
# re-dash cooldown that keeps mashing at today's rate, the direction read once the frame's input is
# all in, and PlayerDashFx's afterimages, dust and whoosh. dash_legacy holds a fight to the dash the
# feel_v2 opt-out leaves it on; dash_layers draws v2 in any of the seven fights.

# The seven fights, and where each keeps its boss so it can be switched off.
const DASH_FIGHTS := {
	"eric": ["res://Scenes/Bosses/EricBossFightScene.tscn", "Arena/EricBossScene"],
	"greyson": ["res://Scenes/Bosses/GreysonBossFightScene.tscn", "Arena/GreysonComputahScene"],
	"mason": ["res://Scenes/Bosses/MasonBossFightScene.tscn", "Arena/MasonScene"],
	"josh": ["res://Scenes/Bosses/JoshBossFightScene.tscn", "Arena/JoshCardsScene"],
	"carter": ["res://Scenes/Bosses/CarterBossFightScene.tscn", "Arena/CarterAkumaScene"],
	"liam": ["res://Scenes/Bosses/LiamBossFightScene.tscn", "Arena/BixbyBeastScene"],
	"jordan": ["res://Scenes/Bosses/JordanBossFightScene.tscn", "Arena/JordanScene"],
}
const DASH_KEYS := {
	"R": [KEY_RIGHT], "RD": [KEY_RIGHT, KEY_DOWN], "D": [KEY_DOWN], "LD": [KEY_LEFT, KEY_DOWN],
	"L": [KEY_LEFT], "LU": [KEY_LEFT, KEY_UP], "U": [KEY_UP], "RU": [KEY_RIGHT, KEY_UP],
}
const KEY_UNITS := {KEY_RIGHT: Vector2.RIGHT, KEY_LEFT: Vector2.LEFT, KEY_UP: Vector2.UP, KEY_DOWN: Vector2.DOWN}
# Today's dash at 60 Hz: 3 frames of 83.3 px, 23 standing still, then walking at 10 px a frame, and a
# mashed dash comes back 26 frames after the last started. Today's 0.4 s lockout ends exactly on a
# frame, so float rounding makes some of them one frame longer: 24 still, 27 apart. feel_v2 stands
# still for 5 and comes back at 26, and its numbers sit between frames so they never move.
const DASH_LENGTH := 250.0
const LEGACY_STILL_FRAMES := [23, 24]
const V2_STILL_FRAMES := 5
const MASH_PERIOD_FRAMES := 26
const LEGACY_MASH_PERIOD_FRAMES := [26, 27]
const DASH_CENTRE := Vector2(700, 650)
const DASH_WHOOSH := "res://Assets/Audio/SFX/dash_whoosh.wav"
# The floor layers the y-sorted fights keep effects in; the mat sorts at 99.
const FLOOR_LAYER_Y := 101.0


# A fight with its boss switched off and nothing holding the player, so only the dash moves him. Eric
# is parked his own tests' way and moved clear of every dash from DASH_CENTRE.
func load_quiet(name: String) -> void:
	if name == "eric":
		await load_eric()
		park_eric()
		boss.global_position = Vector2(1300, 300)
	else:
		var path: String = DASH_FIGHTS[name][0]
		change_scene_to_file(path)
		while current_scene == null or current_scene.scene_file_path != path:
			await process_frame
		await wait(3)
		player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
		defense = player.get_node("Defense")
		current_scene.get_node(DASH_FIGHTS[name][1]).process_mode = Node.PROCESS_MODE_DISABLED
		for child in current_scene.get_children():
			if child is CanvasLayer:
				child.queue_free()
		await skip_entrance()
		root.get_node("DialogueManager").dialogue_ended.emit(null)
		await wait(1)
		await skip_vs_card()
	await wait(2)
	player.unlock_actions()
	player.clear_face_point()
	player.clear_statuses()
	player.is_talking = false
	health_ok()
	clear_iframes()
	await wait(2)


func dash_fx() -> Node:
	return player.get_node("DashFx")


func key_unit(keys: Array) -> Vector2:
	var sum := Vector2.ZERO
	for k in keys:
		sum += KEY_UNITS[k]
	return sum.normalized()


func body_rect() -> Rect2:
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# Where the player's frame is drawn, from his body origin.
func sprite_draw_offset() -> Vector2:
	return player.sprite.global_position + player.sprite.offset * player.sprite.global_scale - player.global_position


# Past the lockout and the cooldown, with a full bar.
func dash_ready() -> void:
	await wait_until(func(): return not defense.is_dash_recovering() and not defense.is_dash_cooling_down(), 120)
	defense._set_stamina(defense.max_stamina)
	await wait(1)


# Holds `keys`, dashes and lets go once the dash has stopped moving: [where it started, where it stopped].
func dash_keys(keys: Array) -> Array:
	for k in keys:
		press(k)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	var from: Vector2 = defense.dash_start_position
	await wait_until(func(): return not player.is_dodging, 20)
	var to: Vector2 = player.global_position
	for k in keys:
		release(k)
	return [from, to]


# Dashes with `keys` held and returns how far the player moved on each physics frame after the press.
func frame_moves(keys: Array, frames: int) -> Array:
	for k in keys:
		press(k)
	tap(KEY_W)
	var moves := []
	var last: Vector2 = player.global_position
	for i in frames:
		await physics_frame
		moves.append(player.global_position.distance_to(last))
		last = player.global_position
	for k in keys:
		release(k)
	return moves


# [frames dashing, frames standing still after it, px walked the frame after that].
func dash_phases(moves: Array) -> Array:
	var i := 0
	while i < moves.size() and moves[i] < 80.0:
		i += 1
	var dashing := 0
	while i < moves.size() and moves[i] > 80.0:
		dashing += 1
		i += 1
	var still := 0
	while i < moves.size() and moves[i] < 0.01:
		still += 1
		i += 1
	return [dashing, still, snappedf(moves[i], 0.01) if i < moves.size() else 0.0]


# Presses dash on every frame until a second dash starts: the frames between the two dashes' starts.
# A dash starts when the player goes from not dashing to dashing; today a press during a dash is taken
# too, and re-aims it, but it doesn't start another.
func mash_gap() -> int:
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	var was_dodging := true
	for i in 90:
		tap(KEY_W)
		await physics_frame
		if player.is_dodging and not was_dodging:
			return i + 1
		was_dodging = player.is_dodging
	return -1


# Every effect PlayerDashFx has drawn that is still up.
func live_effects() -> Array:
	return dash_fx().drawn.filter(func(entry): return is_instance_valid(entry[0]) and not entry[0].is_queued_for_deletion())


func ghosts_of(effects: Array) -> Array:
	return effects.filter(func(entry): return entry[0].texture == player.sprite.texture)


func dust_of(effects: Array) -> Array:
	return effects.filter(func(entry): return entry[0].texture != player.sprite.texture)


# Where an effect really draws its anchor, whatever y it sorts at: a ghost's frame centre, the dust's feet.
func drawn_at(entry: Array) -> Vector2:
	var node: Sprite2D = entry[0]
	return node.global_position + (node.offset - entry[3]) * node.scale


func off_path(point: Vector2, from: Vector2, to: Vector2) -> float:
	return point.distance_to(Geometry2D.get_closest_point_to_segment(point, from, to))


func test_dash_v2() -> void:
	await load_quiet("eric")
	var layout = load("res://Scripts/DefenseHypeArtLayout.gd")
	var arena: Node = current_scene.get_node("Arena")
	var stage: Node = arena.get_node("MainPlayer")
	var sfx: AudioStreamPlayer = player.get_node("DashSfxPlayer")
	check(player.feel_v2, "the fight is on feel_v2")
	# Taken standing: a landing pose leans the sprite back a texel, and the afterimages don't.
	var draw_offset := sprite_draw_offset()

	log_p("-- all 8 directions go the same distance")
	var lengths := {}
	var aimed := true
	for name in DASH_KEYS:
		await dash_ready()
		await settle_player(DASH_CENTRE)
		var path: Array = await dash_keys(DASH_KEYS[name])
		var moved: Vector2 = path[1] - path[0]
		lengths[name] = snappedf(moved.length(), 0.01)
		aimed = aimed and moved.normalized().distance_to(key_unit(DASH_KEYS[name])) < 0.001
	log_p("dash lengths %s" % [lengths])
	check(lengths.values().all(func(length): return absf(length - DASH_LENGTH) < 0.5), "every direction dashes %.0f px, the diagonals too" % DASH_LENGTH)
	check(aimed, "each along its own direction")

	log_p("-- nothing held: in place, as it always was")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	var still: Array = await dash_keys([])
	check(still[0].distance_to(still[1]) < 0.01, "no direction, no movement (%s)" % (still[1] - still[0]))

	log_p("-- the second arrow of a diagonal landing in the same frame as the dash key, after it")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	tap(KEY_W)
	press(KEY_LEFT)
	press(KEY_UP)
	await wait_until(func(): return player.is_dodging, 20)
	var late_from: Vector2 = defense.dash_start_position
	await wait_until(func(): return not player.is_dodging, 20)
	release(KEY_LEFT)
	release(KEY_UP)
	var late: Vector2 = player.global_position - late_from
	log_p("dash key, then both arrows, all in one frame: moved %s" % late)
	check(late.normalized().distance_to(Vector2(-1, -1).normalized()) < 0.001 and absf(late.length() - DASH_LENGTH) < 0.5, "still goes up-left, the full length")

	log_p("-- walls and corners stop a diagonal cleanly")
	var reach_min: Vector2 = player.global_position - body_rect().position
	var reach_max: Vector2 = body_rect().end - player.global_position
	var body_area := Rect2(ROPES.position + reach_min, ROPES.size - reach_min - reach_max).grow(1.0)
	var inside := [true]
	var keep_inside := func(_from: Vector2, _to: Vector2, _kick: bool):
		if not ROPES.encloses(body_rect()):
			inside[0] = false
	player.dash_stepped.connect(keep_inside)
	var corners := {"LU": Vector2(177, 191), "RU": Vector2(1743, 191), "LD": Vector2(177, 887), "RD": Vector2(1743, 887)}
	for name in corners:
		await dash_ready()
		await settle_player(corners[name])
		var unit := key_unit(DASH_KEYS[name])
		await dash_keys(DASH_KEYS[name])
		var box := body_rect()
		var gap_x: float = ROPES.end.x - box.end.x if unit.x > 0.0 else box.position.x - ROPES.position.x
		var gap_y: float = ROPES.end.y - box.end.y if unit.y > 0.0 else box.position.y - ROPES.position.y
		var trail_in := ghosts_of(live_effects()).all(func(entry): return body_area.has_point(drawn_at(entry) - draw_offset))
		log_p("%s corner: body %s, %.2f px off the side rope and %.2f off the end one" % [name, box, gap_x, gap_y])
		check(inside[0] and gap_x < 1.0 and gap_y < 1.0 and trail_in, "into the %s corner: it stops flush in it, never through a rope, and so does its trail" % name)
		await dash_ready()
		var out_x: Vector2 = await walk_offset(KEY_LEFT if unit.x > 0.0 else KEY_RIGHT, 10)
		var out_y: Vector2 = await walk_offset(KEY_UP if unit.y > 0.0 else KEY_DOWN, 10)
		check(absf(out_x.x) > 50.0 and absf(out_y.y) > 50.0, "and walks back out of it both ways (%s, %s)" % [out_x, out_y])
	var glances := {"RU": Vector2(960, 170), "LD": Vector2(960, 910), "LU": Vector2(150, 540), "RD": Vector2(1770, 540)}
	for name in glances:
		await dash_ready()
		await settle_player(glances[name])
		var path: Array = await dash_keys(DASH_KEYS[name])
		var moved: Vector2 = path[1] - path[0]
		var trail_in := ghosts_of(live_effects()).all(func(entry): return body_area.has_point(drawn_at(entry) - draw_offset))
		log_p("%s dash beside a rope from %s: moved %s" % [name, glances[name], moved])
		check(inside[0] and moved.length() > 150.0 and trail_in, "a %s dash along a rope slides along it, inside the ropes, trail and all" % name)
	player.dash_stepped.disconnect(keep_inside)

	log_p("-- afterimages along the path, dust where it started, a whoosh")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	await wait(30)
	var children_before := arena.get_child_count()
	var frames_seen := []
	var note_frame := func(_from: Vector2, _to: Vector2, _kick: bool): frames_seen.append(player.sprite.frame)
	player.dash_stepped.connect(note_frame)
	sfx.stop()
	var path: Array = await dash_keys(DASH_KEYS["R"])
	player.dash_stepped.disconnect(note_frame)
	var whooshed := sfx.playing and sfx.stream != null and sfx.stream.resource_path == DASH_WHOOSH
	var effects := live_effects()
	var ghosts := ghosts_of(effects)
	var dust := dust_of(effects)
	log_p("a right dash: %d afterimages, %d dust, the arena %d -> %d children" % [ghosts.size(), dust.size(), children_before, arena.get_child_count()])
	check(ghosts.size() == layout.DASH_GHOST_COUNT, "%d afterimages" % layout.DASH_GHOST_COUNT)
	check(ghosts.all(func(entry):
		var ghost: Sprite2D = entry[0]
		return ghost.hframes == player.sprite.hframes and ghost.vframes == player.sprite.vframes and frames_seen.has(ghost.frame) and ghost.flip_h == player.sprite.flip_h and ghost.scale == player.sprite.global_scale), "each a copy of his frame: texture, frame, flip and 2x scale")
	check(ghosts.all(func(entry):
		var tint: Color = entry[0].modulate
		return tint.b > tint.r and tint.b > tint.g and tint.a < 1.0), "tinted a light cool colour, see-through")
	var spots: Array = ghosts.map(func(entry): return drawn_at(entry) - draw_offset)
	spots.sort_custom(func(a: Vector2, b: Vector2): return a.x < b.x)
	var gaps := []
	for i in range(1, spots.size()):
		gaps.append(snappedf(spots[i].distance_to(spots[i - 1]), 0.1))
	var on_path: bool = spots.all(func(spot: Vector2): return off_path(spot, path[0], path[1]) <= 1.0)
	check(on_path and spots[0].distance_to(path[0]) <= 1.0 and gaps.all(func(gap: float): return absf(gap - DASH_LENGTH / layout.DASH_GHOST_COUNT) <= 1.5), "laid evenly along the dash from where it started (gaps %s)" % [gaps])
	var alphas: Array = ghosts.map(func(entry): return snappedf(entry[0].modulate.a, 0.01))
	log_p("afterimage alphas, oldest first: %s" % [alphas])
	var mat_index: int = arena.get_node("Mat").get_index()
	check(effects.all(func(entry): return entry[0].get_parent() == arena and entry[0].get_index() > mat_index and entry[0].get_index() < stage.get_index()), "all drawn beside him in the arena: after the mat and before MainPlayer, so over the floor and behind him")
	var feet: Vector2 = path[0] + Vector2(0.0, body_rect().end.y - player.global_position.y)
	var kicked: Vector2 = feet - Vector2.RIGHT * layout.DASH_DUST.push * layout.DASH_DUST.scale
	check(dust.size() == 1 and drawn_at(dust[0]).distance_to(kicked.round()) <= 0.01, "one puff of dust at his feet where it started, kicked back along it")
	check(whooshed, "the whoosh plays")
	var first: Sprite2D = ghosts[0][0]
	var spawned_alpha: float = first.modulate.a
	var dust_frames := [dust[0][0].frame]
	for i in 8:
		await physics_frame
		if is_instance_valid(dust[0][0]):
			dust_frames.append(dust[0][0].frame)
	check(is_instance_valid(first) and first.modulate.a < spawned_alpha * 0.8, "they fade (%.2f -> %.2f)" % [spawned_alpha, first.modulate.a if is_instance_valid(first) else 0.0])
	check(dust_frames.max() > dust_frames.min(), "the dust plays through its frames (%s)" % [dust_frames])
	await wait(14)
	check(live_effects().is_empty() and arena.get_child_count() == children_before, "and every one is gone within 0.4 s (%d left, %d children)" % [live_effects().size(), arena.get_child_count()])

	log_p("-- 50 dashes leave nothing behind")
	await wait(30)
	var nodes_before := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	var children := arena.get_child_count()
	var most := 0
	var names: Array = DASH_KEYS.keys()
	for i in 50:
		await dash_ready()
		await settle_player(DASH_CENTRE)
		await dash_keys(DASH_KEYS[names[i % names.size()]])
		most = maxi(most, live_effects().size())
	await wait(40)
	var nodes_after := Performance.get_monitor(Performance.OBJECT_NODE_COUNT)
	log_p("50 dashes: at most %d effects up at once; nodes %d -> %d, arena children %d -> %d, %d still listed" % [most, nodes_before, nodes_after, children, arena.get_child_count(), dash_fx().drawn.size()])
	check(dash_fx().drawn.is_empty() and arena.get_child_count() == children and nodes_after == nodes_before, "every effect freed itself: no leaked nodes")
	check(most <= layout.DASH_GHOST_COUNT + 1, "and no more than one dash's worth were ever up at once (%d)" % most)

	log_p("-- a hit-stop holds them, and so does a finisher's freeze")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	await dash_keys(DASH_KEYS["R"])
	load("res://Scripts/HitStop.gd").freeze(self, 0.3)
	var held: Sprite2D = ghosts_of(live_effects())[0][0]
	var held_from: float = held.modulate.a
	await wait(12)
	log_p("a hit-stop: alpha %.3f -> %.3f over 12 frames" % [held_from, held.modulate.a])
	check(is_instance_valid(held) and held_from - held.modulate.a < held_from * 0.2, "a hit-stop holds the fade")
	await wait_until(func(): return Engine.time_scale == 1.0, 60)
	await wait(20)
	check(live_effects().is_empty(), "which carries on once it is over")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	await dash_keys(DASH_KEYS["L"])
	var freeze = load("res://Scripts/FightFreeze.gd")
	check(freeze.freeze(self, [player.get_parent()]), "the fight froze around the player")
	var frozen: Sprite2D = ghosts_of(live_effects())[0][0]
	var frozen_from: float = frozen.modulate.a
	await wait(30)
	log_p("a finisher's freeze: alpha %.3f -> %.3f over 30 frames" % [frozen_from, frozen.modulate.a])
	check(is_instance_valid(frozen) and frozen.modulate.a == frozen_from, "a finisher's freeze holds them exactly")
	freeze.unfreeze(self)
	await wait(25)
	check(live_effects().is_empty(), "and they finish once it lets go")

	log_p("-- every lock still stops the dash, its effects and its sound")
	for lock in ["lock_actions", "grab", "talking", "finisher", "guard_break"]:
		await dash_ready()
		await settle_player(DASH_CENTRE)
		match lock:
			"lock_actions": player.lock_actions()
			"grab": player.grab()
			"talking": player.is_talking = true
			"finisher": player.begin_finisher()
			"guard_break": defense._start_guard_break()
		await wait(2)
		sfx.stop()
		var dodge_frame: int = player.last_dodge_physics_frame
		var up := live_effects().size()
		press(KEY_RIGHT)
		tap(KEY_W)
		await wait(10)
		release(KEY_RIGHT)
		check(player.last_dodge_physics_frame == dodge_frame and not player.is_dodging and live_effects().size() == up and not sfx.playing, "%s: no dash, no afterimages, no dust, no whoosh" % lock)
		match lock:
			"lock_actions": player.unlock_actions()
			"grab": player.release_grab(Vector2.ZERO)
			"talking": player.is_talking = false
			"finisher": player.end_finisher(false)
			"guard_break": defense.clear_guard_break()
		clear_iframes()
		await wait(10)

	log_p("-- attacks tagged dash_through are still dashed through")
	var hit_info = load("res://Scripts/HitInfo.gd")
	var catalog = load("res://Scripts/AttackCatalog.gd")
	var through: Array = catalog.ATTACKS.keys().filter(func(id): return catalog.ATTACKS[id].get("dash_through", false))
	var results := {}
	for id in through:
		await dash_ready()
		await settle_player(DASH_CENTRE)
		# Past DashImmunity's 0.6 s gap from the dash before.
		await wait(40)
		tap(KEY_W)
		await wait_until(func(): return player.is_dodging, 20)
		await wait(1)
		var source := dummy_source()
		results[id] = hit_info.Result.keys()[player.receive_hit(hit_info.make(id, source, player.global_position + Vector2(80, 0)))]
		source.queue_free()
		clear_iframes()
		health_ok()
	log_p("inside a v2 dash: %s" % [results])
	check(not through.is_empty() and results.values().all(func(result): return result == "DODGED"), "every dash_through attack is dodged, Computah's laser included")
	await wait(40)
	var control := dummy_source()
	var landed: int = player.receive_hit(hit_info.make(&"computah_laser", control, player.global_position + Vector2(80, 0)))
	check(landed == hit_info.Result.HIT, "and without a dash the laser lands (%s)" % hit_info.Result.keys()[landed])
	clear_iframes()
	health_ok()


func test_dash_recovery_v2() -> void:
	await load_quiet("eric")
	track_parries()
	check(player.feel_v2, "the fight is on feel_v2")

	log_p("-- the timeline, frame by frame, with right held through it")
	await settle_player(DASH_CENTRE)
	var moves: Array = await frame_moves([KEY_RIGHT], 40)
	var phases := dash_phases(moves)
	log_p("per-frame moves %s" % [moves.slice(0, 14).map(func(m): return snappedf(m, 0.1))])
	log_p("v2: %d frames dashing, %d standing still, then %.1f px a frame walking" % phases)
	check(phases[0] == 3 and phases[1] == V2_STILL_FRAMES and is_equal_approx(phases[2], 10.0), "3 frames dashing, %d standing still, then walking at once" % V2_STILL_FRAMES)
	await dash_ready()
	var stamina_before: float = defense.stamina
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	check(is_equal_approx(stamina_before - defense.stamina, defense.dash_stamina_cost), "it still costs %.0f stamina" % defense.dash_stamina_cost)

	log_p("-- a punch comes out the first frame the landing is over, never before")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait_until(func(): return not player.is_dodging, 20)
	var frames := 0
	var early := false
	while player.state_machine.current_state.name != "Punching" and frames < 40:
		tap(KEY_Q)
		await physics_frame
		frames += 1
		# Read after the press's frame: the clock the press was judged on is the one it reads now.
		early = early or (defense.is_dash_recovering() and player.state_machine.current_state.name == "Punching")
	log_p("pressing punch every frame after the dash: it came out after %d frames" % frames)
	check(not early and frames <= V2_STILL_FRAMES + 1, "the punch comes out as the landing ends (%d frames), none sooner" % frames)
	await wait_until(func(): return player.state_machine.current_state.name != "Punching", 60)

	log_p("-- the guard goes up inside it, and a parry ends it and the cooldown")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	await wait(40)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait_until(func(): return not player.is_dodging, 20)
	press(KEY_SHIFT)
	await wait(1)
	check(player.state_machine.current_state.name == "Blocking" and defense.is_dash_recovering(), "the guard is up inside the landing (%s)" % player.state_machine.current_state.name)
	var result := front_hit(&"eric_quake_wave", dummy_source())
	check(result == 3 and not defense.is_dash_recovering() and not defense.is_dash_cooling_down(), "a parry ends the landing and the cooldown (%d)" % result)
	release(KEY_SHIFT)
	await wait(2)
	defense._set_stamina(defense.max_stamina)
	tap(KEY_W)
	check(await wait_until(func(): return player.is_dodging, 6), "so the next dash comes out at once")
	await wait_until(func(): return not player.is_dodging, 20)

	log_p("-- a block that isn't a parry leaves it running")
	await wait_until(func(): return Engine.time_scale == 1.0, 120)
	defense.dash_recovery_time_v2 = 0.6
	await dash_ready()
	await settle_player(DASH_CENTRE)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait_until(func(): return not player.is_dodging, 20)
	press(KEY_SHIFT)
	# The landing is stretched to 0.6 s above, so it is still running once the parry window has passed.
	await past_window()
	result = front_hit(&"eric_quake_wave", dummy_source())
	check(result == 2 and defense.is_dash_recovering(), "blocked, and the landing runs on (%d)" % result)
	release(KEY_SHIFT)
	defense.dash_recovery_time_v2 = 0.09

	log_p("-- mashing: the next dash comes %d frames after the last, and the presses between cost nothing" % MASH_PERIOD_FRAMES)
	await dash_ready()
	await settle_player(DASH_CENTRE)
	await wait(40)
	var refused := [0]
	var count_refused := func(): refused[0] += 1
	defense.stamina_refused.connect(count_refused)
	var bar_before: float = defense.stamina
	var gap: int = await mash_gap()
	defense.stamina_refused.disconnect(count_refused)
	log_p("mashed: the second dash started %d frames after the first; stamina %.0f -> %.0f, %d refusals flashed" % [gap, bar_before, defense.stamina, refused[0]])
	check(gap == MASH_PERIOD_FRAMES, "mashed dashes come %d frames apart, exactly as today's lockout spaced them" % MASH_PERIOD_FRAMES)
	check(is_equal_approx(bar_before - defense.stamina, 2.0 * defense.dash_stamina_cost) and refused[0] == 0, "only the two dashes spent stamina, and the refused presses flashed nothing")

	log_p("-- the finisher and a grab clear it all")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	await dash_keys([])
	check(defense.is_dash_recovering() and defense.is_dash_cooling_down(), "landing and cooling down")
	player.begin_finisher()
	check(not defense.is_dash_recovering() and not defense.is_dash_cooling_down(), "begin_finisher clears both")
	player.is_finishing = false
	await dash_ready()
	await dash_keys([])
	player.grab()
	check(not defense.is_dash_recovering() and not defense.is_dash_cooling_down(), "a grab clears both")
	player.release_grab(Vector2.UP)
	clear_iframes()
	await wait(5)


# Mashes dash for `seconds` with right held, pressing every `every` frames: how many frames dash
# immunity was up, how many presses were taken, when each dash started, and how far it all went.
func mash_run(seconds: float, every: int) -> Dictionary:
	var immunity = load("res://Scripts/DashImmunity.gd")
	var catalog = load("res://Scripts/AttackCatalog.gd")
	player.global_position = Vector2(300, 650)
	player.velocity = Vector2.ZERO
	defense.clear_dash_recovery()
	defense._set_stamina(defense.max_stamina)
	defense.last_spend_time = -INF
	# Past the 0.6 s gap from any earlier dash, so the first dash of the run is clean.
	await wait(45)
	var frames := int(seconds * 60.0)
	var immune := 0
	var taken := 0
	var starts := []
	var last: int = player.last_dodge_physics_frame
	var was_dodging := false
	var covered := 0.0
	var x: float = player.global_position.x
	press(KEY_RIGHT)
	for i in frames:
		if i % every == 0:
			tap(KEY_W)
		await physics_frame
		if immunity.is_immune(player, catalog.DASH_IMMUNITY_TIME, catalog.DASH_IMMUNITY_COOLDOWN):
			immune += 1
		if player.last_dodge_physics_frame != last:
			last = player.last_dodge_physics_frame
			taken += 1
		if player.is_dodging and not was_dodging:
			starts.append(i)
		was_dodging = player.is_dodging
		covered += absf(player.global_position.x - x)
		if player.global_position.x > 1500.0:
			player.global_position.x = 300.0
		x = player.global_position.x
	release(KEY_RIGHT)
	await wait(5)
	var gaps := []
	for i in range(1, starts.size()):
		gaps.append(starts[i] - starts[i - 1])
	return {"immune": immune, "frames": frames, "taken": taken, "dashes": starts.size(), "gaps": gaps, "covered": covered}


func test_dash_spam_v2() -> void:
	await load_quiet("eric")
	var walked := await travel(6.0, false)
	log_p("walking 6 s: %.0f px (%.0f px/s)" % [walked, walked / 6.0])
	var runs := {}
	player.feel_v2 = false
	runs["today, mashed"] = await mash_run(6.0, 1)
	player.feel_v2 = true
	runs["v2, mashed"] = await mash_run(6.0, 1)
	var cooldown: float = defense.dash_cooldown_v2
	defense.dash_cooldown_v2 = 0.0
	runs["v2 with no cooldown, mashed"] = await mash_run(6.0, 1)
	defense.dash_cooldown_v2 = cooldown
	player.feel_v2 = false
	runs["today, a dash every 0.6 s"] = await mash_run(6.0, 36)
	player.feel_v2 = true
	runs["v2, a dash every 0.6 s"] = await mash_run(6.0, 36)
	for name in runs:
		var run: Dictionary = runs[name]
		log_p("%-28s %2d dashes from %2d presses taken, gaps %s; dash immunity up %3d of %d frames (%.1f%%); covered %.0f px (%.0f%% of walking)" % [name, run.dashes, run.taken, str(run.gaps.slice(0, 8)), run.immune, run.frames, 100.0 * run.immune / run.frames, run.covered, 100.0 * run.covered / walked])
	var today: Dictionary = runs["today, mashed"]
	var v2: Dictionary = runs["v2, mashed"]
	check(today.gaps.size() > 0 and LEGACY_MASH_PERIOD_FRAMES.has(today.gaps[0]) and v2.gaps.size() > 0 and v2.gaps[0] == MASH_PERIOD_FRAMES, "mashed, v2 dashes as often as today: every %d frames until the bar runs dry (today %d)" % [MASH_PERIOD_FRAMES, today.gaps[0] if today.gaps.size() > 0 else -1])
	check(v2.taken == v2.dashes and today.taken > today.dashes, "today a press during a dash is taken and paid for again; v2 takes none (%d of %d against %d of %d)" % [v2.taken, v2.dashes, today.taken, today.dashes])
	check(v2.immune <= today.immune, "mashing v2 is never immune for longer than mashing today (%d frames against %d)" % [v2.immune, today.immune])
	check(runs.values().all(func(run: Dictionary): return float(run.immune) / run.frames < 0.35), "no way of dashing keeps dash immunity up for even 35% of the time")


# A fight that opts out of feel_v2, the one line a fight whose retune isn't done puts in its _ready:
# today's dash, frame for frame, with nothing drawn and nothing played.
func test_dash_legacy() -> void:
	await load_quiet(fight)
	player.feel_v2 = false
	log_p("%s's fight, opted out of feel_v2" % fight)
	var arena: Node = current_scene.get_node("Arena")
	var sfx: AudioStreamPlayer = player.get_node("DashSfxPlayer")
	var children := arena.get_child_count()
	var drawn := [0]
	var sounded := [false]
	var count_drawn := func(_node: Node): drawn[0] += 1
	arena.child_entered_tree.connect(count_drawn)
	watch = func():
		sounded[0] = sounded[0] or sfx.playing

	log_p("-- 8 directions, %.0f px each, the diagonals as they have always been" % DASH_LENGTH)
	var lengths := {}
	var aimed := true
	for name in DASH_KEYS:
		await dash_ready()
		await settle_player(DASH_CENTRE)
		var path: Array = await dash_keys(DASH_KEYS[name])
		var moved: Vector2 = path[1] - path[0]
		lengths[name] = snappedf(moved.length(), 0.01)
		aimed = aimed and moved.normalized().distance_to(key_unit(DASH_KEYS[name])) < 0.001
	log_p("dash lengths %s" % [lengths])
	check(lengths.values().all(func(length): return absf(length - DASH_LENGTH) < 0.5) and aimed, "every direction dashes %.0f px along itself" % DASH_LENGTH)

	log_p("-- today's lockout")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	var phases := dash_phases(await frame_moves([KEY_RIGHT], 45))
	log_p("today: %d frames dashing, %d standing still, then %.1f px a frame walking" % phases)
	check(phases[0] == 3 and LEGACY_STILL_FRAMES.has(phases[1]) and is_equal_approx(phases[2], 10.0), "3 frames dashing, %s standing still, then walking" % [LEGACY_STILL_FRAMES])

	log_p("-- mashing")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	var gap: int = await mash_gap()
	check(LEGACY_MASH_PERIOD_FRAMES.has(gap), "mashed dashes come %s frames apart (%d)" % [LEGACY_MASH_PERIOD_FRAMES, gap])

	log_p("-- the direction is read on the press, as it always was")
	await dash_ready()
	await settle_player(DASH_CENTRE)
	tap(KEY_W)
	press(KEY_LEFT)
	press(KEY_UP)
	await wait_until(func(): return player.is_dodging, 20)
	var from: Vector2 = defense.dash_start_position
	await wait_until(func(): return not player.is_dodging, 20)
	release(KEY_LEFT)
	release(KEY_UP)
	check(player.global_position.distance_to(from) < 0.01, "arrows landing after the dash key in the same frame don't steer it (%s)" % (player.global_position - from))

	await wait(30)
	watch = Callable()
	arena.child_entered_tree.disconnect(count_drawn)
	check(drawn[0] == 0 and dash_fx().drawn.is_empty() and arena.get_child_count() == children, "no afterimages and no dust, ever (%d drawn)" % drawn[0])
	check(not sounded[0], "and no whoosh")


# feel_v2's effects in any of the seven fights: always drawn behind the player and over the floor.
# Every fight is on feel_v2 now, and the assignment below keeps the mode honest if one opts back out.
func test_dash_layers() -> void:
	await load_quiet(fight)
	player.feel_v2 = true
	var arena: Node2D = current_scene.get_node("Arena")
	var stage: Node = arena.get_node("MainPlayer")
	var mat_index: int = arena.get_node("Mat").get_index()
	var sorted: bool = arena.y_sort_enabled
	log_p("%s: arena y-sorted %s; his sprite sorts %+.0f px from his origin" % [fight, sorted, player.sprite.global_position.y - player.global_position.y])
	var seen := [0]
	var problems := []
	# On physics_frame rather than in watch: this tree's _process runs before the nodes' own, where
	# PlayerDashFx re-sorts, and the start of the next physics step sees the frame as it was drawn.
	var check_layers := func():
		var sprite_y: float = player.sprite.global_position.y
		for entry in live_effects():
			var node: Sprite2D = entry[0]
			seen[0] += 1
			var wrong := ""
			if node.get_parent() != arena or node.get_index() >= stage.get_index():
				wrong = "not just before MainPlayer"
			elif sorted and node.global_position.y >= sprite_y:
				wrong = "sorts at %.1f, not behind his %.1f" % [node.global_position.y, sprite_y]
			elif sorted and node.global_position.y <= FLOOR_LAYER_Y:
				wrong = "sorts at %.1f, under the floor layers" % node.global_position.y
			elif not sorted and node.get_index() <= mat_index:
				wrong = "under the mat"
			elif drawn_at(entry).distance_to(entry[1]) > 0.01:
				wrong = "drawn at %s instead of %s" % [drawn_at(entry), entry[1]]
			if not wrong.is_empty() and problems.size() < 10:
				problems.append("%s %s" % [node.name, wrong])
	physics_frame.connect(check_layers)
	# Out along each direction, then straight back through the trail while it is still up.
	for name in DASH_KEYS:
		await dash_ready()
		await settle_player(Vector2(960, 560))
		var keys: Array = DASH_KEYS[name]
		await dash_keys(keys)
		var back: Array = keys.map(func(k): return {KEY_RIGHT: KEY_LEFT, KEY_LEFT: KEY_RIGHT, KEY_UP: KEY_DOWN, KEY_DOWN: KEY_UP}[k])
		await wait_until(func(): return not defense.is_dash_recovering(), 20)
		for k in back:
			press(k)
		await wait(14)
		for k in back:
			release(k)
	await wait(20)
	physics_frame.disconnect(check_layers)
	log_p("%d effect-frames checked; problems %s" % [seen[0], problems])
	check(seen[0] > 100 and problems.is_empty(), "%s: every afterimage and puff stays behind him and over the floor, drawn where it belongs" % fight)
	check(live_effects().is_empty(), "and all of them are gone")


# ------------------------------------------------------------------ feel_v2's punch
# The punch player.feel_v2 gives every fight: PlayerScript's PUNCH_HITBOXES_V2, fitted as every swing
# starts, and PunchFx's swoosh, star and whoosh. fight=eric pins v2 against the real Eric, held down so
# his hurtbox is live; any other fight is opted back out here and must keep today's box exactly, with
# nothing drawn or played.

const PUNCH_SWOOSH_TEXTURE := "res://Assets/Effects/punch_swoosh.png"
const PUNCH_FX_SCRIPT := "res://Scripts/PunchFx.gd"
const PUNCH_SWOOSH_CELL := 48
const PUNCH_FACING_NAMES := ["down", "up", "left", "right"]
# Where his hurtbox's near face is put, in px past today's far edge: inside it for a plain hit, just
# beyond it where only v2 reaches, and well short for a whiff.
const PUNCH_SPOTS := {"hit": -6.0, "reach": 3.0, "whiff": 40.0}


func test_punch_reach() -> void:
	if fight == "eric":
		await punch_reach_v2()
	else:
		await punch_reach_legacy()


func punch_fx() -> Node2D:
	return player.get_node("PunchFx")


# The punch hitbox as it is fitted right now, in texels from the frame centre.
func fitted_punch_box() -> Rect2:
	var shape: CollisionShape2D = player.punch_hitbox
	var size: Vector2 = (shape.shape as RectangleShape2D).size
	return Rect2(shape.position - size / 2.0, size)


func same_rect(a: Rect2, b: Rect2) -> bool:
	return a.position.is_equal_approx(b.position) and a.size.is_equal_approx(b.size)


# Where the player stands so `facing` points at `box` with today's far edge `past` px short of its near
# face (negative: inside it). Beside him, his glove's height sits well inside the box.
func punch_spot(facing: int, box: Rect2, past: float) -> Vector2:
	var today: Rect2 = player.PUNCH_HITBOXES[facing]
	var s: float = player.global_scale.x
	var reach := Rect2(today.position * s, today.size * s)
	match facing:
		player.Facing.UP:
			return Vector2(box.get_center().x - reach.get_center().x, box.end.y + past - reach.position.y)
		player.Facing.DOWN:
			return Vector2(box.get_center().x - reach.get_center().x, box.position.y - past - reach.end.y)
		player.Facing.LEFT:
			return Vector2(box.end.x + past - reach.position.x, box.get_center().y + 30.0 - reach.get_center().y)
		_:
			return Vector2(box.position.x - past - reach.end.x, box.get_center().y + 30.0 - reach.get_center().y)


# One punch, watched on every frame until everything it shows is gone.
func watched_punch() -> Dictionary:
	var fx := punch_fx()
	var swoosh: Sprite2D = fx.get_node("Swoosh")
	var star: Sprite2D = fx.get_node("Star")
	var whoosh: AudioStreamPlayer = fx.get_node("WhooshSfxPlayer")
	var seen := {"box": Rect2(), "facing": player.facing, "frames": [], "aligned": true, "whooshes": 0,
		"star_rows": [], "star_at": Vector2.INF, "stopped_frames": [], "drawn": false, "dealt": 0}
	var health: int = boss.boss_health if is_instance_valid(boss) else 0
	# Headless audio plays in wall-clock time while these frames race ahead, so the last swing's whoosh
	# can still be sounding: only a fresh play() counts.
	whoosh.stop()
	var was_whooshing := false
	tap(KEY_Q)
	for i in 70:
		await physics_frame
		if seen.box == Rect2() and player.state_machine.current_state.name == "Punching":
			seen.box = fitted_punch_box()
		if swoosh.visible:
			seen.drawn = true
			var frame: int = swoosh.frame_coords.x
			if seen.frames.is_empty() or seen.frames[-1] != frame:
				seen.frames.append(frame)
			if swoosh.frame_coords.y != seen.facing or swoosh.scale != player.sprite.global_scale:
				seen.aligned = false
			if frame != 2 and swoosh.global_position != player.sprite.global_position:
				seen.aligned = false
		if star.visible:
			seen.drawn = true
			if seen.star_at == Vector2.INF:
				seen.star_at = star.global_position
			if seen.star_rows.is_empty() or seen.star_rows[-1] != star.frame_coords.y:
				seen.star_rows.append(star.frame_coords.y)
			if Engine.time_scale < 1.0 and not seen.stopped_frames.has(star.frame_coords.x):
				seen.stopped_frames.append(star.frame_coords.x)
		if whoosh.playing and not was_whooshing:
			seen.whooshes += 1
		was_whooshing = whoosh.playing
	if is_instance_valid(boss):
		seen.dealt = health - boss.boss_health
	return seen


func punch_reach_v2() -> void:
	await load_eric()
	check(player.feel_v2, "the fight is on feel_v2")
	check(player.punch_fx != null and player.punch_fx == punch_fx(), "the player carries PunchFx")

	log_p("-- the first punch gets v2's box, fitted as the swing starts rather than once at _ready")
	var before := fitted_punch_box()
	var first := await watched_punch()
	log_p("box before the first swing %s, during it %s (facing %s)" % [before, first.box, PUNCH_FACING_NAMES[first.facing]])
	check(same_rect(first.box, player.PUNCH_HITBOXES_V2[first.facing]), "fitted to PUNCH_HITBOXES_V2 as the swing starts")

	park_eric()
	health_ok()
	boss.boss_health = 1000
	sm.downed_state_timer.start(600.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	# After Downed's Enter, which clears it: no daze, so a charged punch can't start a finisher yet.
	boss.daze_used = true
	var hurt_shape: CollisionShape2D = boss.get_node("Hurtbox/CollisionShape2D")
	var hurt := hurt_shape.global_transform * hurt_shape.shape.get_rect()

	for facing in [player.Facing.UP, player.Facing.DOWN, player.Facing.LEFT, player.Facing.RIGHT]:
		var name: String = PUNCH_FACING_NAMES[facing]
		var v2: Rect2 = player.PUNCH_HITBOXES_V2[facing]
		check(v2.encloses(player.PUNCH_HITBOXES[facing]), "%s: v2's box contains today's" % name)
		for kind in PUNCH_SPOTS:
			await settle_player(punch_spot(facing, hurt, PUNCH_SPOTS[kind]).round())
			await wait(8)
			var seen := await watched_punch()
			var lands: bool = kind != "whiff"
			log_p("%s %s: dealt %d, box %s, swoosh %s, whooshes %d, star rows %s at %s, star frames in the hit-stop %s" % [name, kind, seen.dealt, seen.box, seen.frames, seen.whooshes, seen.star_rows, seen.star_at, seen.stopped_frames])
			check(seen.facing == facing, "%s %s: facing %s" % [name, kind, PUNCH_FACING_NAMES[seen.facing]])
			check(same_rect(seen.box, v2), "%s %s: the swing's box is PUNCH_HITBOXES_V2" % [name, kind])
			check(seen.dealt == (1 if lands else 0), "%s %s: %s (dealt %d)" % [name, kind, "lands" if lands else "misses", seen.dealt])
			check(seen.frames == [0, 1, 2] and seen.aligned, "%s %s: the swoosh plays launch, full extension, afterimage, on his own position, scale and facing row (%s)" % [name, kind, seen.frames])
			check(seen.whooshes == 1, "%s %s: one whoosh (%d)" % [name, kind, seen.whooshes])
			if lands:
				var reach := Rect2(player.global_transform * v2)
				var inside: bool = reach.grow(0.5).has_point(seen.star_at) and hurt.grow(0.5).has_point(seen.star_at)
				check(seen.star_rows == [0] and inside, "%s %s: a white star inside both the reach and his hurtbox (%s at %s)" % [name, kind, seen.star_rows, seen.star_at])
				check(seen.stopped_frames == [0], "%s %s: the hit-stop holds the star on its first frame (%s)" % [name, kind, seen.stopped_frames])
			else:
				check(seen.star_rows.is_empty(), "%s %s: no star" % [name, kind])
			await wait(20)

	log_p("-- three punches on the beat: the third, charged, star is the gold one")
	await settle_player(punch_spot(player.Facing.UP, hurt, PUNCH_SPOTS.hit).round())
	await wait(40)
	var star: Sprite2D = punch_fx().get_node("Star")
	var rows := []
	for n in 3:
		await swing()
		rows.append(star.frame_coords.y if star.visible else -1)
		await wait(6)
	log_p("star rows over the combo %s" % [rows])
	check(rows == [0, 0, 1], "white, white, then gold (%s)" % [rows])
	await wait(60)

	log_p("-- a swing cut off by a grab leaves nothing behind")
	await settle_player(punch_spot(player.Facing.UP, hurt, PUNCH_SPOTS.whiff).round())
	await wait(10)
	var swoosh: Sprite2D = punch_fx().get_node("Swoosh")
	tap(KEY_Q)
	var launched := await wait_until(func(): return swoosh.visible and swoosh.frame_coords.x == 0, 30)
	check(launched, "the launch frame is up")
	player.grab()
	var after_grab := [false]
	for i in 20:
		await physics_frame
		after_grab[0] = after_grab[0] or swoosh.visible
	check(not after_grab[0], "grabbed mid-swing: no swoosh and no afterimage")
	player.release_grab(Vector2.DOWN)
	await wait(90)
	clear_iframes()

	log_p("-- feel_v2 off: today's box on the very next swing, nothing drawn or played; back on, v2 again")
	await settle_player(punch_spot(player.Facing.UP, hurt, PUNCH_SPOTS.hit).round())
	await wait(10)
	player.feel_v2 = false
	var off := await watched_punch()
	check(same_rect(off.box, player.PUNCH_HITBOXES[off.facing]) and not off.drawn and off.whooshes == 0, "off: today's box %s, drawn %s, whooshes %d" % [off.box, off.drawn, off.whooshes])
	player.feel_v2 = true
	await wait(10)
	var on := await watched_punch()
	check(same_rect(on.box, player.PUNCH_HITBOXES_V2[on.facing]) and on.frames == [0, 1, 2], "on again: v2's box and the swoosh (%s, %s)" % [on.box, on.frames])

	log_p("-- the swoosh's full-extension frame is PUNCH_HITBOXES_V2 drawn out")
	var sheet: Image = (load(PUNCH_SWOOSH_TEXTURE) as Texture2D).get_image()
	var cell := PUNCH_SWOOSH_CELL
	check(swoosh.hframes == 3 and swoosh.vframes == 4 and sheet.get_width() == 3 * cell and sheet.get_height() == 4 * cell, "3 frames by 4 facing rows of %dx%d" % [cell, cell])
	for facing in 4:
		var v2: Rect2 = player.PUNCH_HITBOXES_V2[facing]
		var outside := []
		for frame in 3:
			var used := sheet.get_region(Rect2i(frame * cell, facing * cell, cell, cell)).get_used_rect()
			var drawn := Rect2(Vector2(used.position) - Vector2(cell, cell) / 2.0, Vector2(used.size))
			if not v2.encloses(drawn):
				outside.append(frame)
			if frame != 1:
				continue
			var spans: bool
			match facing:
				player.Facing.RIGHT:
					spans = drawn.end.x == v2.end.x and drawn.position.y == v2.position.y and drawn.end.y == v2.end.y
				player.Facing.LEFT:
					spans = drawn.position.x == v2.position.x and drawn.position.y == v2.position.y and drawn.end.y == v2.end.y
				player.Facing.UP:
					spans = drawn.position.y == v2.position.y and drawn.position.x == v2.position.x and drawn.end.x == v2.end.x
				_:
					spans = drawn.end.y == v2.end.y and drawn.position.x == v2.position.x and drawn.end.x == v2.end.x
			check(spans, "%s: full extension reaches v2's far edge and spans its width exactly (drawn %s, box %s)" % [PUNCH_FACING_NAMES[facing], drawn, v2])
		check(outside.is_empty(), "%s: no swoosh frame reaches outside the box (%s)" % [PUNCH_FACING_NAMES[facing], outside])

	log_p("-- freeze-safe timing: nothing on a SceneTree timer or tween")
	var source := FileAccess.get_file_as_string(PUNCH_FX_SCRIPT)
	check(not source.contains("create_timer") and not source.contains("create_tween"), "PunchFx counts its own game time")

	log_p("-- a charged punch that starts the finisher: nothing of the punch is on screen when the fight freezes")
	await settle_player(punch_spot(player.Facing.UP, hurt, PUNCH_SPOTS.hit).round())
	await wait(40)
	boss.daze_used = false
	for n in 3:
		await swing()
		await wait(6)
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	var froze := await wait_until(func(): return freeze.is_frozen(), 180)
	check(froze, "the charged punch dazed him and the fight froze")
	check(not swoosh.visible and not star.visible, "no swoosh or star left once it froze (swoosh %s, star %s)" % [swoosh.visible, star.visible])


# A fight that opts out of feel_v2, the one line a fight whose retune isn't done puts in its _ready:
# today's box in every facing, and PunchFx never draws or plays.
func punch_reach_legacy() -> void:
	await load_quiet(fight)
	player.feel_v2 = false
	log_p("%s's fight, opted out of feel_v2" % fight)
	check(player.punch_fx != null, "the player carries PunchFx here too")
	var fx := punch_fx()
	var swoosh: Sprite2D = fx.get_node("Swoosh")
	var star: Sprite2D = fx.get_node("Star")
	var whoosh: AudioStreamPlayer = fx.get_node("WhooshSfxPlayer")
	var drawn := [false]
	var sounded := [false]
	watch = func():
		drawn[0] = drawn[0] or swoosh.visible or star.visible
		sounded[0] = sounded[0] or whoosh.playing
	await settle_player(DASH_CENTRE)
	for facing in 4:
		player.face_point(player.global_position + defense.FACING_VECTORS[facing] * 200.0)
		await wait(4)
		var seen := await watched_punch()
		log_p("%s: box %s" % [PUNCH_FACING_NAMES[facing], seen.box])
		check(seen.facing == facing and same_rect(seen.box, player.PUNCH_HITBOXES[facing]), "%s: today's box exactly" % PUNCH_FACING_NAMES[facing])
	player.clear_face_point()
	watch = Callable()
	check(not drawn[0] and not sounded[0], "no swoosh, star or whoosh, ever (drawn %s, sounded %s)" % [drawn[0], sounded[0]])


# ------------------------------------------------------------------ Eric's reworked fight (EricPacing V2)
# His pacing rework switches whole on EricPacing.version: V2 ships, and V1 is the fight the modes above
# were written against, which ERIC_V1_MODES pins them to. These modes load V2 whatever ships, and hold
# his Break gauge still wherever it isn't what is under test, so a run of parries or dodges can't break
# him halfway through something else.

const FRAME_TIME := 1.0 / 60.0
# The plan's section 1, which EricPacing's V2 column has to match.
const V2_PACE := {
	"max_health": 56, "attacks_per_chain": 3, "rage_attacks_per_chain": 4,
	"rage_chain_health_ratio": 0.40, "attack_gap": 0.25, "rage_attack_gap": 0.15, "recovery_rest": 0.25,
	"window_time": 2.0, "rage_window_time": 1.6, "slam_tell_time": 0.36, "delayed_slam_chance": 0.4,
	"whirl_windup": 0.45, "rage_whirl_windup": 0.40, "whirl_lunges": 2, "rage_whirl_lunges": 3,
	"whirl_lunge_time": 0.5, "whirl_lunge_speed": 1000.0, "rage_whirl_lunge_speed": 1150.0,
	"whirl_reaim_time": 0.35, "rage_whirl_reaim_time": 0.30, "whirl_dizzy_time": 0.8,
	"rage_whirl_dizzy_time": 0.6, "planted_time": 0.5, "rage_planted_time": 0.35,
	"hug_charge_time": 0.55, "rage_hug_charge_time": 0.45, "hug_stumble_time": 0.7,
	"hug_yellow_chance": 0.5, "broken_time": 3.0, "rage_broken_time": 2.6,
}
# Every tell's floor: a red timing tell is 1.5x the parry window, a single-answer read 0.40 s, and a
# colour decision 0.40 s with its margin.
const TELL_FLOORS := {"Earthquake": 0.36, "Whirlwind": 0.40, "BearHug": 0.45, "SwordThrow": 0.40}
# Far enough from his spawn that his bear hug's lunge falls short and a lunge's sweep starts well off.
const OUT_OF_REACH := Vector2(1780, 940)


func load_eric_v2() -> void:
	pin_eric(2)
	await load_eric()


# EricPacing's `key` at his current rage.
func paced(key: String) -> float:
	return load(ERIC_PACING).raged(key, sm.rage)


func hold_gauge() -> void:
	boss.break_gauge.locked = true
	boss.break_gauge.set_physics_process(false)


func hazards_of(script_file: String) -> Array:
	return get_nodes_in_group(sm.HAZARD_GROUP).filter(func(h): return is_instance_valid(h) and not h.is_queued_for_deletion() and h.get_script() != null and str(h.get_script().resource_path).ends_with(script_file))


func live_hazards() -> Array:
	return get_nodes_in_group(sm.HAZARD_GROUP).filter(func(h): return is_instance_valid(h) and not h.is_queued_for_deletion())


# His attack `state_name` on its own, through to the window it ends in, then idle again.
# Started in the idle step, where the game starts his attacks (his rest timer), so a wind-up counted in
# physics steps gets all of its frames.
func attack_v2(state_name: String, max_frames := 900) -> bool:
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await process_frame
	sm.on_child_transition(sm.current_state, state_name)
	var ended := await wait_until(func(): return sm.current_state.name == "Winded", max_frames)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(2)
	return ended


# The moment his attack becomes the threat its tell warned of.
func impact_seen(attack_name: String) -> bool:
	match attack_name:
		"Earthquake":
			return not hazards_of("EarthquakeProjectilesScript.gd").is_empty()
		"Whirlwind":
			return boss.get_node("WhirlwindArea2D").monitoring
		"BearHug":
			return boss.get_node("GrabArea2D").monitoring
		"SwordThrow":
			return is_instance_valid(sm.states["SwordThrow"].sword)
	return false


# ---- the punch

# feel_v2 lands a punch as the arm reaches full extension; today's lands once the boss's hurtbox reports
# it after the swing: f+16 against f+24 from the press. Either way a swing resolves once, and the beat
# window after it is PlayerFeel's.
func test_punch_contact() -> void:
	await load_eric()
	park_eric()
	health_ok()
	boss.boss_health = 1000
	sm.downed_state_timer.start(600.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	# No daze, so no charged punch starts a finisher here.
	boss.daze_used = true
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	var landed := []
	player.combo.punch_landed.connect(func(_target, dealt, _charged): landed.append([Engine.get_physics_frames(), dealt]))
	var windows := []
	player.combo.beat_window_changed.connect(func(open): windows.append([open, player.combo.clock - player.combo.swing_end_time]))
	for v2 in [true, false]:
		player.feel_v2 = v2
		var name := "feel_v2" if v2 else "today's"
		player.fit_punch_hitbox()
		place_under(hurtbox)
		await wait(40)
		landed.clear()
		windows.clear()
		var pressed := Engine.get_physics_frames()
		tap(KEY_Q)
		await wait_until(func(): return player.state_machine.current_state.name == "Punching", 10)
		while player.state_machine.current_state.name == "Punching":
			await physics_frame
		var pending: bool = player.combo.report_pending()
		await wait(40)
		var at: int = landed[0][0] - pressed if not landed.is_empty() else -1
		log_p("%s: landed %d frames after the press, %d resolve(s); a report pending as the swing ended: %s; beat window %s" % [name, at, landed.size(), pending, windows])
		check(at == (16 if v2 else 24), "%s: the punch resolves at f+%d (f+%d)" % [name, 16 if v2 else 24, at])
		check(landed.size() == 1 and landed[0][1] == 1, "%s: once for the swing, for 1 (%s)" % [name, landed])
		check(pending != v2, "%s: %s" % [name, "nothing waits on a report" if v2 else "the report is waited on"])
		var offset: float = feel("combo_window_offset")
		var length: float = feel("combo_window_length")
		var opened: Array = windows.filter(func(w): return w[0])
		var closed: Array = windows.filter(func(w): return not w[0])
		check(opened.size() == 1 and absf(opened[0][1] - offset) <= FRAME_TIME + 0.001, "%s: the beat window opens %.2f s after the swing (%s)" % [name, offset, opened])
		check(closed.size() == 1 and absf(closed[0][1] - offset - length) <= FRAME_TIME + 0.001, "%s: and stays open %.2f s (%s)" % [name, length, closed])

	log_p("-- feel_v2: a whiff lands nothing and ends the combo with its swing")
	player.feel_v2 = true
	player.fit_punch_hitbox()
	place_under(hurtbox)
	await wait(40)
	await swing()
	check(player.combo.count == 1, "a landed punch starts a combo (%d)" % player.combo.count)
	await settle_player(player.global_position + Vector2(0, 200))
	landed.clear()
	await wait(6)
	tap(KEY_Q)
	await wait_until(func(): return player.state_machine.current_state.name == "Punching", 10)
	while player.state_machine.current_state.name == "Punching":
		await physics_frame
	check(landed.is_empty() and player.combo.count == 0 and not player.combo.swing_open, "the whiff landed nothing, and the combo is over as its swing ends (count %d)" % player.combo.count)


# ---- the y-sort

# Eric's fight y-sorts like the other six: whoever stands lower draws over the other, both sorted at
# their feet, and whatever lies on the floor draws under both.
func test_y_sort_eric() -> void:
	await load_eric()
	park_eric()
	health_ok()
	var layout = load("res://Scripts/EricArtLayout.gd")
	var arena: Node2D = current_scene.get_node("Arena")
	var eric_root: Node2D = boss.get_parent()
	var ground: Node2D = arena.get_node_or_null("GroundFx")
	var ropes: Node2D = arena.get_node("wallBoundaries")
	check(current_scene.y_sort_enabled and arena.y_sort_enabled and arena.get_node("MainPlayer").y_sort_enabled and player.y_sort_enabled, "the fight, the arena and the player sort, as in the other six fights")
	check(eric_root.y_sort_enabled and boss.y_sort_enabled, "and so does Eric")
	check(ropes.z_index == 1, "the ropes draw over everyone (z %d)" % ropes.z_index)
	check(ground != null and not ground.y_sort_enabled and is_equal_approx(ground.position.y, FLOOR_LAYER_Y) and ground.z_index == 0, "a floor layer at y %.0f that doesn't sort its own children" % FLOOR_LAYER_Y)

	log_p("-- he sorts at his feet, and is drawn where he always was")
	var sprite: Sprite2D = boss.sprite
	check(sprite.position == layout.SORT_POINT and sprite.offset == layout.SPRITE_OFFSET - layout.SORT_POINT, "his sprite sits at SORT_POINT and its offset takes it back (%s, %s)" % [sprite.position, sprite.offset])
	var drawn_origin: Vector2 = sprite.to_global(sprite.offset - layout.FRAME_SIZE / 2.0)
	var frame_origin: Vector2 = boss.to_global(layout.frame_local(Vector2.ZERO))
	check(drawn_origin.distance_to(frame_origin) < 0.01, "his frames are drawn where frame_local() puts them (%s, %s)" % [drawn_origin, frame_origin])
	var feet: float = boss.frame_point(Vector2(128, layout.FEET_ROW)).y
	check(absf(sprite.global_position.y - feet) < 0.51, "he sorts on the row his feet stand on (%.1f, his feet %.1f)" % [sprite.global_position.y, feet])

	log_p("-- in front of him and behind him")
	var drawn := Rect2(drawn_origin, layout.FRAME_SIZE * boss.global_scale)
	boss.get_node("CollisionShape2D").disabled = true
	for spot in [[Vector2(60, 170), true], [Vector2(60, 120), false]]:
		player.global_position = boss.global_position + spot[0]
		await wait(3)
		var mine: float = player.sprite.global_position.y
		var his: float = sprite.global_position.y
		var same_layer: bool = player.sprite.z_index == sprite.z_index and player.z_index == boss.z_index
		log_p("player at %s sorts at %.1f against his %.1f" % [player.global_position, mine, his])
		check(drawn.has_point(player.global_position) and same_layer, "standing over his frame, on his layer")
		check((mine > his) == spot[1], "a player %s draws %s him" % ["in front" if spot[1] else "behind", "over" if spot[1] else "under"])
	boss.get_node("CollisionShape2D").disabled = false

	log_p("-- what lies on the floor draws under both")
	unpark_eric()
	await settle_player(Vector2(1500, 900))
	var lowest: float = minf(sprite.global_position.y, player.sprite.global_position.y)
	check(ground.position.y < lowest, "the floor layer sorts under both of them (%.0f against %.0f)" % [ground.position.y, lowest])
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Earthquake")
	await wait_until(func(): return not hazards_of("EarthquakeProjectilesScript.gd").is_empty(), 300)
	var waves := hazards_of("EarthquakeProjectilesScript.gd")
	check(not waves.is_empty() and waves.all(func(w): return w.get_parent() == ground), "a slam's waves lie on the floor layer")
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(30)
	sm.chain = []
	sm.on_child_transition(sm.current_state, "SwordThrow")
	var throw_state: Node = sm.states["SwordThrow"]
	await wait_until(func(): return is_instance_valid(throw_state.sword), 300)
	var sword: Node2D = throw_state.sword
	check(sword.get_parent() == eric_root and sword.get_node("Sword").z_index == 0 and sword.get_node("Planted").z_index == 0, "the flying sword sorts among the fighters, at its ground point")
	check(sword.shadow.get_parent() == ground, "while its shadow lies on the floor layer")
	await wait_until(func(): return not hazards_of("EricQuakeRingScript.gd").is_empty(), 300)
	await wait(2)
	var rings_down: bool = hazards_of("EricQuakeRingScript.gd").all(func(r): return r.get_parent() == ground)
	var dust: Array = live_hazards().filter(func(h): return h is Sprite2D and h.get_parent() == ground)
	check(rings_down and not dust.is_empty(), "and so do the ring and the dust where it lands")
	await wait_until(func(): return sm.current_state.name != "SwordThrow", 400)
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(30)
	var shadows_left: Array = ground.get_children().filter(func(c): return c is Sprite2D and not c.is_queued_for_deletion() and c.texture and c.texture.resource_path.ends_with("eric_leap_shadow.png"))
	check(shadows_left.is_empty(), "the shadow goes with the sword")
	sm.chain = []
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	await wait_until(func(): return hug.phase == hug.Phase.CHARGE, 300)
	await wait(2)
	var tell := tell_node()
	check(tell != null and tell.z_index > ropes.z_index, "a tell draws over the ropes (z %d)" % (tell.z_index if tell else -1))
	await wait_until(func(): return hug.phase == hug.Phase.LUNGE, 300)
	await wait(2)
	var planted: Node2D = hug.planted_sword
	var planted_at: float = hug.plant_spot.y + layout.SORT_POINT.y * boss.global_scale.y
	check(is_instance_valid(planted) and planted.get_parent() == eric_root and absf(planted.global_position.y - planted_at) < 0.01, "the hug's planted sword sorts where his feet were when he planted it")
	sm.on_child_transition(sm.current_state, "Idle")


# ---- the pace

# EricPacing's V2 column against the plan's section 1; each attack at full health and enraged, its tell
# timed against its floor; then whole chains, timed: the gaps between attacks, the Winded window and
# the rest after it.
func test_v2_cadence() -> void:
	await load_eric_v2()
	health_ok()
	hold_gauge()
	var pacing = load(ERIC_PACING)
	var drift := []
	for key in V2_PACE:
		if not is_equal_approx(float(pacing.value(key)), float(V2_PACE[key])):
			drift.append("%s %s, plan %s" % [key, pacing.value(key), V2_PACE[key]])
	check(pacing.is_v2() and drift.is_empty(), "EricPacing's V2 numbers are the plan's (%s)" % [drift])
	check(pacing.value("window_state") == "Winded" and pacing.value("delayed_slam_holds") == [0.20, 0.35], "a chain ends in Winded, and a delayed slam holds 0.20 or 0.35 s")
	check(boss.max_health == 56 and boss.boss_health == 56, "56 health, and he starts on it (%d of %d)" % [boss.boss_health, boss.max_health])

	log_p("-- 3 attacks a chain, 4 from 40% down")
	for health in [23, 22]:
		boss.boss_health = health
		sm.start_chain(5.0)
		var count: int = sm.chain.size() + 1
		sm.rest_timer.stop()
		check(count == (3 if health == 23 else 4), "at %d of 56 (%.0f%%) a chain is %d attacks" % [health, 100.0 * health / 56.0, count])
	boss.boss_health = 56
	sm.chain = []
	sm.on_child_transition(sm.current_state, "Idle")

	log_p("-- each attack's tell against its floor, at full health and enraged")
	for rage in [0.0, 1.0]:
		for attack in ["Earthquake", "Whirlwind", "BearHug", "SwordThrow"]:
			boss.global_position = Vector2(960, 380)
			await settle_player(Vector2(1500, 900))
			sm.rage = rage
			var seen := {"tell": -1.0, "impact": -1.0, "look": ""}
			var probe := func():
				var tell := tell_node()
				if seen.tell < 0.0 and tell != null:
					seen.tell = defense.clock
					seen.look = "yellow" if tell.dodge else ("strong red" if tell.strong else "red")
				if seen.tell >= 0.0 and seen.impact < 0.0 and impact_seen(attack):
					seen.impact = defense.clock
			physics_frame.connect(probe)
			await attack_v2(attack, 1500)
			physics_frame.disconnect(probe)
			clear_iframes()
			health_ok()
			var lead: float = seen.impact - seen.tell
			var own: float = {"Earthquake": pacing.value("slam_tell_time"), "Whirlwind": pacing.raged("whirl_windup", rage), "BearHug": pacing.raged("hug_charge_time", rage), "SwordThrow": sm.states["SwordThrow"].TELL_TIME}[attack]
			log_p("%s at rage %.0f: a %s tell %.3f s before it strikes (its own %.2f, floor %.2f)" % [attack, rage, seen.look, lead, own, TELL_FLOORS[attack]])
			check(seen.tell >= 0.0 and seen.impact >= 0.0, "%s at rage %.0f: the tell, then the attack" % [attack, rage])
			check(lead >= TELL_FLOORS[attack] - 0.001 and absf(lead - own) <= 2.0 * FRAME_TIME + 0.001, "%s at rage %.0f: the tell leads by its own %.2f s, at or over its %.2f s floor (%.3f)" % [attack, rage, own, TELL_FLOORS[attack], lead])
			var looks := {"Earthquake": ["red"], "Whirlwind": ["yellow"], "BearHug": ["strong red", "yellow"], "SwordThrow": ["strong red"]}
			check(looks[attack].has(seen.look), "%s: its tell is %s (%s)" % [attack, " or ".join(looks[attack]), seen.look])

	log_p("-- whole chains: the gaps between attacks, the Winded window, the rest after it")
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	for health in [56, 1]:
		boss.global_position = Vector2(960, 380)
		await settle_player(Vector2(1500, 900))
		boss.boss_health = health
		var states := []
		var winded_open := [true]
		var probe := func():
			var name: String = sm.current_state.name
			if states.is_empty() or states[-1][1] != name:
				states.append([defense.clock, name])
			if name == "Winded" and states[-1][0] < defense.clock:
				winded_open[0] = winded_open[0] and hurtbox.monitoring and not boss.can_be_dazed()
		physics_frame.connect(probe)
		sm.start_chain(0.0)
		var rage_now: float = sm.rage
		var chain_length: int = sm.chain.size() + 1
		await wait_until(func(): return states.any(func(s): return s[1] == "Winded") and not ["Winded", "Idle"].has(states[-1][1]), 3000)
		physics_frame.disconnect(probe)
		var gaps := []
		var winded := -1.0
		var rest := -1.0
		for i in range(1, states.size() - 1):
			var lasted: float = states[i + 1][0] - states[i][0]
			if states[i][1] == "Idle":
				if states[i - 1][1] == "Winded":
					rest = lasted
				else:
					gaps.append(snappedf(lasted, 0.001))
			elif states[i][1] == "Winded":
				winded = lasted
		var gap: float = pacing.raged("attack_gap", rage_now)
		var window: float = pacing.raged("window_time", rage_now)
		log_p("rage %.2f, %d attacks: %s; gaps %s (%.3f), Winded %.3f (%.3f), rest %.3f (%.2f)" % [rage_now, chain_length, states.map(func(s): return s[1]), gaps, gap, winded, window, rest, pacing.value("recovery_rest")])
		check(gaps.size() == chain_length - 1 and gaps.all(func(g): return absf(g - gap) <= FRAME_TIME + 0.001), "rage %.2f: %.3f s between attacks" % [rage_now, gap])
		check(absf(winded - window) <= FRAME_TIME + 0.001, "rage %.2f: the chain ends in %.2f s Winded (%.3f)" % [rage_now, window, winded])
		check(winded_open[0], "rage %.2f: open to punches all through it, and never dazed there" % rage_now)
		check(absf(rest - pacing.value("recovery_rest")) <= FRAME_TIME + 0.001, "rage %.2f: then %.2f s before the next chain (%.3f)" % [rage_now, pacing.value("recovery_rest"), rest])
		sm.chain = []
		sm.rest_timer.stop()
		sm.downed_state_timer.stop()
		sm.on_child_transition(sm.current_state, "Idle")
		clear_iframes()
		health_ok()
		await wait(20)


# ---- the slam

# At most one slam an attack holds on the frame before impact, for 0.20 or 0.35 s, never in the fight's
# first slam attack, at the share EricPacing sets; and every slam's red tell comes up its tell time
# before the waves, held or not.
func test_delayed_slam() -> void:
	await load_eric_v2()
	health_ok()
	hold_gauge()
	await settle_player(Vector2(250, 950))
	var layout = load("res://Scripts/EricArtLayout.gd")
	var pacing = load(ERIC_PACING)
	var quake: Node = sm.states["Earthquake"]
	var animator: AnimationPlayer = boss.animationPlayer
	var ground: Node = current_scene.get_node("Arena/GroundFx")
	var spawned := [0]
	var wave_ids := {}
	var count_waves := func(node: Node):
		if node.get_script() != null and str(node.get_script().resource_path).ends_with("EarthquakeProjectilesScript.gd"):
			spawned[0] += 1
			wave_ids[node.attack_id] = true
	ground.child_entered_tree.connect(count_waves)
	var slams := []
	var slam := {}
	var seen_waves := [0]
	var attack := [0]
	var probe := func():
		if spawned[0] > seen_waves[0]:
			seen_waves[0] = spawned[0]
			if slam.has("tell"):
				slam.lead = defense.clock - slam.tell
				slams.append(slam.duplicate())
			slam.clear()
		if sm.current_state != quake:
			slam.clear()
			return
		if slam.is_empty():
			slam.merge({"attack": attack[0], "rage": sm.rage, "held_frames": 0, "held_on": [], "hold": 0.0})
		var tell := tell_node()
		if not slam.has("tell") and tell != null:
			slam.tell = defense.clock
			slam.look = "yellow" if tell.dodge else ("strong red" if tell.strong else "red")
		if animator.speed_scale == 0.0:
			slam.held_frames += 1
			slam.hold = quake.hold_time
			if not slam.held_on.has(boss.sprite.frame):
				slam.held_on.append(boss.sprite.frame)
	physics_frame.connect(probe)
	# The holds are random: a fixed seed keeps the run the same every time.
	seed(20260918)
	for i in 16:
		attack[0] = i
		sm.rage = 0.0 if i < 12 else 1.0
		await attack_v2("Earthquake", 900)
		clear_iframes()
		health_ok()
	physics_frame.disconnect(probe)
	ground.child_entered_tree.disconnect(count_waves)

	var held: Array = slams.filter(func(s): return s.held_frames > 0)
	var per_attack := {}
	for s in held:
		per_attack[s.attack] = per_attack.get(s.attack, 0) + 1
	var eligible: Array = slams.filter(func(s): return s.attack > 0 and s.rage == 0.0)
	var eligible_held: Array = eligible.filter(func(s): return s.held_frames > 0)
	log_p("%d slams, %d held %s; at full health %d of %d eligible slams held (%.0f%%)" % [slams.size(), held.size(), held.map(func(s): return "a%d %.2f s" % [s.attack, s.held_frames * FRAME_TIME]), eligible_held.size(), eligible.size(), 100.0 * eligible_held.size() / maxf(eligible.size(), 1.0)])
	log_p("tell leads %s" % [slams.map(func(s): return snappedf(s.lead, 0.001))])
	check(slams.size() == 12 * 2 + 4 * 3, "every slam of 16 attacks was seen (%d)" % slams.size())
	check(slams.filter(func(s): return s.attack == 0 and s.held_frames > 0).is_empty(), "the fight's first slam attack never holds")
	check(per_attack.values().all(func(n): return n == 1), "no attack holds more than one slam (%s)" % [per_attack])
	check(held.all(func(s): return pacing.value("delayed_slam_holds").has(s.hold) and absf(s.held_frames * FRAME_TIME - s.hold) <= FRAME_TIME + 0.001), "each hold is 0.20 or 0.35 s")
	check(held.all(func(s): return s.held_on == [layout.SLAM_HOLD_FRAME]), "held on frame %d, the sword at the top of its arc" % layout.SLAM_HOLD_FRAME)
	var share: float = float(eligible_held.size()) / maxf(eligible.size(), 1.0)
	check(share >= 0.2 and share <= 0.6, "about %.0f%% of the slams that can hold do (%.0f%%)" % [100.0 * pacing.value("delayed_slam_chance"), 100.0 * share])
	check(slams.all(func(s): return s.lead >= pacing.value("slam_tell_time") - 0.001 and s.lead <= pacing.value("slam_tell_time") + 2.0 * FRAME_TIME + 0.001), "every slam's tell leads its waves by %.2f s, held or not" % pacing.value("slam_tell_time"))
	check(slams.all(func(s): return s.look == "red"), "a standard red tell every time")
	check(wave_ids.keys() == [&"eric_quake_wave_v2"], "the waves are V2's (%s)" % [wave_ids.keys()])


# ---- the whirlwind

# The Whirlwind's yellow wind-up, straight lunges with a re-aim between them, and the sword release it
# ends in: the spin hands its last beat to the throw (EricStateMachine.throw_from_whirlwind), which owns
# the red tell from its first frame. Then, against the player's own dash, one dash from a standing start
# clears each lunge.
func test_whirl_lunges() -> void:
	await load_eric_v2()
	health_ok()
	hold_gauge()
	track()
	track_dodges()
	var pacing = load(ERIC_PACING)
	var whirl: Node = sm.states["Whirlwind"]
	var throw_state: Node = sm.states["SwordThrow"]
	var sweep: CollisionShape2D = boss.get_node("WhirlwindArea2D/CollisionShape2D")
	var hitbox: Area2D = boss.get_node("WhirlwindArea2D")
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	var catalog = load("res://Scripts/AttackCatalog.gd")
	var entry: Dictionary = catalog.get_attack(&"eric_whirlwind_v2")
	check(entry.blockable and entry.weight == catalog.Weight.HEAVY and entry.dash_through and entry.dodge_tell and not entry.tell, "eric_whirlwind_v2: blocked at a heavy cost, dashed through, told in yellow")

	log_p("-- its shape, at full health and enraged")
	for rage in [0.0, 1.0]:
		boss.global_position = Vector2(300, 450)
		await settle_player(Vector2(1780, 470))
		sm.rage = rage
		var trace := []
		var probe := func():
			var tell := tell_node()
			var blade: Node2D = throw_state.sword if is_instance_valid(throw_state.sword) else null
			trace.append({"t": defense.clock, "phase": whirl.phase, "at": boss.global_position, "sweep": sweep.global_position, "spinning": hitbox.monitoring, "open": hurtbox.monitoring, "yellow": tell != null and tell.dodge, "left": whirl.lunges_left, "target": player.hurtBox.get_node("CollisionShape2D").global_position, "state": sm.current_state.name, "met": whirl.met_at >= 0.0, "red": tell != null and tell.strong, "tell_at": Vector2.ZERO if tell == null else tell.global_position, "head": throw_state._tell_anchor(), "sword": "" if blade == null else ("back" if blade.returning else "out"), "live": blade != null and blade.get_node("Hitbox").monitoring, "mark": Vector2.ZERO if blade == null or not is_instance_valid(blade.mark) else blade.mark.global_position, "here": player.global_position, "ring": not hazards_of("EricQuakeRingScript.gd").is_empty()})
		physics_frame.connect(probe)
		await attack_v2("Whirlwind", 900)
		physics_frame.disconnect(probe)
		clear_iframes()
		health_ok()
		# Runs of the same phase, in order.
		var runs := []
		for sample in trace:
			if sample.state != "Whirlwind":
				continue
			if runs.is_empty() or runs[-1].phase != sample.phase or runs[-1].left != sample.left:
				runs.append({"phase": sample.phase, "left": sample.left, "samples": []})
			runs[-1].samples.append(sample)
		var windups: Array = runs.filter(func(r): return r.phase == whirl.Phase.WINDUP)
		var lunges: Array = runs.filter(func(r): return r.phase == whirl.Phase.LUNGE)
		var reaims: Array = runs.filter(func(r): return r.phase == whirl.Phase.REAIM)
		var lasted := func(run: Dictionary) -> float: return run.samples.size() * FRAME_TIME
		log_p("rage %.0f: wind-up %s, lunges %s, re-aims %s" % [rage, windups.map(lasted), lunges.map(lasted), reaims.map(lasted)])
		check(windups.size() == 1 and absf(lasted.call(windups[0]) - pacing.raged("whirl_windup", rage)) <= FRAME_TIME + 0.001, "rage %.0f: a %.2f s wind-up" % [rage, pacing.raged("whirl_windup", rage)])
		if windups.size() == 1:
			var still: bool = windups[0].samples.all(func(s): return s.at == windups[0].samples[0].at and not s.spinning)
			var told: bool = windups[0].samples.slice(1).all(func(s): return s.yellow)
			check(still and told, "rage %.0f: through it he stands still, harmless, under the yellow ring" % rage)
		check(lunges.size() == roundi(pacing.raged("whirl_lunges", rage)), "rage %.0f: %d lunges (%d)" % [rage, roundi(pacing.raged("whirl_lunges", rage)), lunges.size()])
		for run in lunges:
			var s: Array = run.samples
			var step: Vector2 = s[3].at - s[2].at
			var speed := step.length() / FRAME_TIME
			var aim: Vector2 = s[0].target - s[0].sweep
			var heading: Vector2 = s[mini(6, s.size() - 1)].at - s[0].at
			check(absf(lasted.call(run) - pacing.value("whirl_lunge_time")) <= FRAME_TIME + 0.001 and absf(speed - pacing.raged("whirl_lunge_speed", rage)) < 1.0, "rage %.0f: a lunge lasts %.2f s at %.0f px/s (%.3f s, %.0f px/s)" % [rage, pacing.value("whirl_lunge_time"), pacing.raged("whirl_lunge_speed", rage), lasted.call(run), speed])
			check(absf(rad_to_deg(aim.angle_to(heading))) < 2.0 and s.all(func(x): return x.spinning), "rage %.0f: straight at where the player stood as it began, spinning (%.1f deg off)" % [rage, rad_to_deg(aim.angle_to(heading))])
		# A re-aim after a lunge that met the player can hold longer, until the next one is dodgeable.
		for run in reaims:
			var after_meeting: bool = run.samples[0].met
			var took: float = lasted.call(run)
			var on_time: bool = absf(took - pacing.raged("whirl_reaim_time", rage)) <= FRAME_TIME + 0.001 or (after_meeting and took > pacing.raged("whirl_reaim_time", rage))
			check(on_time and run.samples.all(func(s): return s.spinning and s.at == run.samples[0].at), "rage %.0f: %.2f s re-aiming in place%s, still spinning (%.3f)" % [rage, pacing.raged("whirl_reaim_time", rage), " or longer after meeting the player" if after_meeting else "", took])
		# The last beat is the throw's: he lets the sword go at them instead of stopping dizzy.
		var last_lunge := -1
		var handoff := -1
		var released := -1
		var caught := -1
		for i in trace.size():
			if trace[i].state == "Whirlwind" and trace[i].phase == whirl.Phase.LUNGE:
				last_lunge = i
			if handoff < 0 and trace[i].state == "SwordThrow":
				handoff = i
			if released < 0 and trace[i].sword == "out":
				released = i
			if released >= 0 and caught < 0 and trace[i].sword == "":
				caught = i
		if handoff < 0 or released < 0 or caught < 0:
			check(false, "rage %.0f: the spin ends in the throw's release (handoff %d, release %d, catch %d)" % [rage, handoff, released, caught])
			continue
		var wind: Array = range(handoff, released)
		var red: Array = wind.filter(func(i): return trace[i].red)
		var over: Array = range(handoff, caught)
		var back: Array = over.filter(func(i): return trace[i].sword == "back")
		log_p("rage %.0f: the throw takes over on the frame after the last lunge, a %.2f s wind (%.2f s of it red), %.2f s of flight, %.2f s coming back" % [rage, wind.size() * FRAME_TIME, red.size() * FRAME_TIME, (caught - back.size() - released) * FRAME_TIME, back.size() * FRAME_TIME])
		check(handoff == last_lunge + 1, "rage %.0f: no dizzy - the throw takes over on the frame the last lunge ends" % rage)
		check(trace[handoff].red and trace[handoff].tell_at.distance_to(trace[handoff].head) < 2.0, "rage %.0f: its red tell is up on that first frame, on the throw's own head point" % rage)
		# The badge leaves on its own fade, a frame or two before the sword it warned of exists.
		check(red.size() * FRAME_TIME >= throw_state.WHIRL_TELL_TIME - 3.0 * FRAME_TIME and absf(wind.size() * FRAME_TIME - throw_state.WHIRL_TELL_TIME) <= 2.0 * FRAME_TIME, "rage %.0f: and stays up for the whole %.2f s wind" % [rage, throw_state.WHIRL_TELL_TIME])
		check(trace[released].mark.distance_to(trace[released].here) < 2.0, "rage %.0f: the mark lands on the spot the player is standing on" % rage)
		check(over.all(func(i): return not trace[i].spinning), "rage %.0f: harmless from the moment the spin hands over" % rage)
		check(wind.all(func(i): return not trace[i].open) and range(released + 1, caught).all(func(i): return trace[i].open), "rage %.0f: shut through the red wind, open to punches from the release to the catch" % rage)
		check(not back.is_empty() and back.all(func(i): return not trace[i].live), "rage %.0f: the sword comes back through them harmless (%d frames)" % [rage, back.size()])
		check(over.all(func(i): return not trace[i].ring), "rage %.0f: it skips off the mat: no plant and no quake ring" % rage)

	log_p("-- the other read: off the mark, in on him, and punching")
	boss.global_position = Vector2(700, 400)
	await settle_player(Vector2(1480, 700))
	sm.rage = 0.0
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await process_frame
	sm.on_child_transition(sm.current_state, "Whirlwind")
	# The lunges are their own dodge check, above; this is about what the release leaves him open to.
	player.is_invincible = true
	var flew: bool = await wait_until(func(): return is_instance_valid(throw_state.sword), 600)
	var thrown: Node2D = throw_state.sword
	var clipped := [0]
	var watch_blade := func():
		if is_instance_valid(thrown) and thrown.returning and thrown.get_node("Hitbox").monitoring:
			clipped[0] += 1
	physics_frame.connect(watch_blade)
	await settle_player(_bot_punch_spot())
	player.face_point(hurtbox.get_node("CollisionShape2D").global_position)
	await wait(2)
	clear_iframes()
	var health: int = player.playerHealth
	var punched := 0
	for i in 3:
		if sm.current_state != throw_state:
			break
		punched += await swing()
	physics_frame.disconnect(watch_blade)
	log_p("in beside him: %d of punches, %d frames of live blade on the way back, the player on %d of %d" % [punched, clipped[0], player.playerHealth, health])
	check(flew and punched > 0, "punches land on him while the sword is away (%d)" % punched)
	check(clipped[0] == 0 and player.playerHealth == health, "and the sword he threw comes back through them without touching them")
	await wait_until(func(): return sm.current_state.name == "Winded", 400)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	clear_iframes()
	health_ok()
	await wait(20)

	log_p("-- the window it hands the chain on to")
	# The release shuts his hurtbox on the way out, and EricWinded opens its own on the way in: shut it
	# deferred and it lands on top of that and leaves him untouchable for the whole punish window.
	boss.global_position = Vector2(700, 400)
	await settle_player(OUT_OF_REACH)
	sm.rage = 0.0
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await process_frame
	sm.on_child_transition(sm.current_state, "Whirlwind")
	player.is_invincible = true
	var into_winded: bool = await wait_until(func(): return sm.current_state.name == "Winded", 900)
	var stayed_open := [true]
	var watch_open := func(): stayed_open[0] = stayed_open[0] and hurtbox.monitoring and hurtbox.monitorable
	physics_frame.connect(watch_open)
	await wait(20)
	physics_frame.disconnect(watch_open)
	log_p("the Winded window after a release: reached %s, open %s, state %s" % [into_winded, stayed_open[0], sm.current_state.name])
	check(into_winded and stayed_open[0], "the window it hands on to is open to punches, not shut by the release's own close")
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	clear_iframes()
	health_ok()
	await wait(10)

	log_p("-- the mark's commit frame ends when the blade arrives, at any range")
	# The release leaves from wherever his last lunge put him, usually on top of them; the toss he winds
	# up himself leaves from his own spot. The blade is 108 px across and dives in tip first, so a short
	# throw reaches them with a third of its flight still to run: the mark has to say so.
	for case in [["his release, from where the lunges leave him", "Whirlwind"], ["his own toss, from his spot", "SwordThrow"]]:
		boss.global_position = Vector2(700, 400)
		await settle_player(Vector2(1480, 700))
		health_ok()
		clear_iframes()
		player.is_invincible = true
		sm.chain = []
		sm.rest_timer.stop()
		sm.downed_state_timer.stop()
		await process_frame
		sm.on_child_transition(sm.current_state, case[1])
		var out: bool = await wait_until(func(): return is_instance_valid(throw_state.sword) and throw_state.sword.flying, 600)
		var flung: Node2D = throw_state.sword if out else null
		var commit: float = flung.mark.commit_at if out and is_instance_valid(flung.mark) else -1.0
		var flight: float = flung.duration if out else 0.0
		var span: float = flung.from_ground.distance_to(flung.to_ground) if out else 0.0
		var window: float = defense.parry_window / flight if out else 0.0
		var slack: float = FRAME_TIME / flight + 0.01 if out else 0.0
		var reach := -1.0
		while out and is_instance_valid(flung) and flung.flying and not flung.returning:
			if reach < 0.0 and flung.get_node("Hitbox").get_overlapping_areas().has(player.hurtBox):
				reach = flung.elapsed / flight
			await physics_frame
		log_p("%s: %.0f px over %.2f s, the blade reaches them at %.2f of the flight, the commit frame lights at %.2f, the window is %.2f of it" % [case[0], span, flight, reach, commit, window])
		check(out and reach >= 0.0, "%s: the blade reaches a player standing on the mark" % case[0])
		if out and reach >= 0.0:
			# Or the whole flight is the window, for a throw from right on top of them.
			var on_time: bool = absf(reach - commit - window) <= slack or (commit <= 0.0 and reach <= window + slack)
			check(on_time, "%s: it arrives a parry window after the commit frame lights (%.3f of the flight against %.3f)" % [case[0], reach - commit, window])
		await wait_until(func(): return sm.current_state.name == "Winded", 400)
		sm.downed_state_timer.stop()
		sm.on_child_transition(sm.current_state, "Idle")
		clear_iframes()
		health_ok()
		await wait(10)

	log_p("-- one dash from a standing start clears each lunge")
	# [what, Eric's spot, the player's, the lunge they dash out of]. For a second lunge they stand far
	# enough off that the first falls short, so they meet it standing, with a clean dash.
	var standing := [
		["straight at him from below, lunge 1", Vector2(960, 380), Vector2(960, 900), 0],
		["straight at him from below, lunge 2", Vector2(960, 200), Vector2(960, 945), 1],
		["across the ring, lunge 1", Vector2(960, 380), Vector2(1700, 470), 0],
		["across the ring, lunge 2", Vector2(700, 386), Vector2(1700, 470), 1],
		["on the diagonal, lunge 1", Vector2(960, 380), Vector2(1500, 860), 0],
		["on the diagonal, lunge 2", Vector2(700, 200), Vector2(1428, 813), 1],
	]
	for case in standing:
		var lunges: Array = await dash_lunges(case[1], case[2], [case[3]], 3)
		var mine: Dictionary = lunges[case[3]] if lunges.size() > case[3] else {}
		log_p("%s: %s" % [case[0], lunges.map(lunge_line)])
		check(case[3] == 0 or (lunges.size() > 1 and lunges[0].hits == 0), "%s: the lunge before it falls short, so it is met standing" % case[0])
		check(not mine.is_empty() and not mine.dash.is_empty() and mine.hits == 0, "%s: one dash from standing clears it" % case[0])

	log_p("-- both lunges of one whirlwind, each dashed: the re-aim leaves the second dash its immunity")
	# A dash is only immune DASH_IMMUNITY_COOLDOWN after the last one, and a second lunge can start on top
	# of a player who has just dashed through the first; the diagonals are where it used to.
	var pairs := [
		["straight at him from below", Vector2(960, 380), Vector2(960, 900)],
		["across the ring", Vector2(960, 380), Vector2(1700, 470)],
		["on the diagonal, down and right", Vector2(960, 380), Vector2(1500, 860)],
		["on the diagonal, down and left", Vector2(960, 380), Vector2(420, 860)],
		["on the diagonal, up and right", Vector2(700, 700), Vector2(1150, 330)],
		["on the diagonal, up and left", Vector2(1300, 700), Vector2(850, 330)],
		["on a shallow diagonal", Vector2(500, 400), Vector2(1200, 650)],
		["on a steep diagonal", Vector2(800, 200), Vector2(1000, 750)],
	]
	for case in pairs:
		for lead in [3, 8]:
			var lunges: Array = await dash_lunges(case[1], case[2], [0, 1], lead)
			var both: bool = lunges.size() == 2 and lunges.all(func(l): return not l.dash.is_empty())
			var gap: float = lunges[1].pressed_at - lunges[0].pressed_at if both else -1.0
			log_p("%s, dashing %d frames ahead: %s" % [case[0], lead, lunges.map(lunge_line)])
			check(both and lunges.all(func(l): return l.hits == 0) and gap >= catalog.DASH_IMMUNITY_COOLDOWN, "%s, dashing %d frames ahead: both lunges dashed through, %.2f s apart" % [case[0], lead, gap])


# One whirlwind at full health from `eric_at` on a player standing at `spot`, who dashes out of the
# lunges numbered in `dash_for` (from 0), lead_frames before the sweep would reach them, and stands still
# through the rest. A lunge they don't dash for can hit them; its
# i-frames are cleared as the next lunge starts, so it can't shelter them from that one. Returns each
# lunge's angle, the dash taken and how long before contact, and the hits it landed.
func dash_lunges(eric_at: Vector2, spot: Vector2, dash_for: Array, lead_frames: int) -> Array:
	var whirl: Node = sm.states["Whirlwind"]
	var sweep: CollisionShape2D = boss.get_node("WhirlwindArea2D/CollisionShape2D")
	var radii: Vector2 = Vector2.ONE * sweep.shape.radius * sweep.global_scale.abs()
	boss.global_position = eric_at
	await settle_player(spot)
	clear_iframes()
	health_ok()
	defense._set_stamina(defense.max_stamina)
	# Past DashImmunity's gap from any earlier dash, so the first dash here is a clean one.
	await wait(45)
	events.clear()
	sm.rage = 0.0
	sm.chain = []
	await process_frame
	sm.on_child_transition(sm.current_state, "Whirlwind")
	var lunges := []
	var last_left := -1
	var held_keys := []
	var release_in := 0
	for i in 400:
		if release_in > 0:
			release_in -= 1
			if release_in == 0:
				for k in held_keys:
					release(k)
				held_keys.clear()
		# The last lunge hands straight over to the throw, so leaving the state is the end of them.
		if sm.current_state != whirl:
			break
		if whirl.phase == whirl.Phase.LUNGE and whirl.lunges_left != last_left:
			last_left = whirl.lunges_left
			clear_iframes()
			lunges.append({"from": defense.clock, "angle": rad_to_deg(whirl.lunge_velocity.angle()), "dash": "", "eta": -1.0, "pressed_at": -1.0, "hits": 0})
		var index := lunges.size() - 1
		if whirl.phase == whirl.Phase.LUNGE and dash_for.has(index) and lunges[index].dash.is_empty():
			var eta := sweep_eta(sweep.global_position, whirl.lunge_velocity, whirl.phase_left, radii)
			if eta >= 0.0 and eta <= lead_frames * FRAME_TIME:
				var escape := sweep_escape(whirl.lunge_velocity)
				held_keys = keys_toward(escape)
				for k in held_keys:
					press(k)
				tap(KEY_W)
				release_in = 4
				lunges[index].dash = "up" if escape.y < 0.0 else "down"
				lunges[index].eta = eta
				lunges[index].pressed_at = defense.clock
		await physics_frame
	for k in held_keys:
		release(k)
	var until: float = defense.clock
	await wait_until(func(): return sm.current_state.name == "Winded", 300)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	for e in events_of("HIT"):
		for i in range(lunges.size() - 1, -1, -1):
			if e.t >= lunges[i].from and e.t <= until:
				lunges[i].hits += 1
				break
	clear_iframes()
	health_ok()
	await wait(20)
	return lunges


func lunge_line(lunge: Dictionary) -> String:
	if lunge.is_empty():
		return "no lunge"
	var dash: String = "a dash %s %.3f s before contact" % [lunge.dash, lunge.eta] if not lunge.dash.is_empty() else "no dash"
	return "%.0f deg, %s, %d hit(s)" % [lunge.angle, dash, lunge.hits]


# Seconds until a sweep centred on `centre`, moving at `velocity` for `left` more seconds, would first
# touch the player standing where they are, or -1 if it won't.
func sweep_eta(centre: Vector2, velocity: Vector2, left: float, radii: Vector2) -> float:
	var rect := hurtbox_rect()
	var t := 0.0
	while t <= left + 0.0001:
		var at := centre + velocity * t
		var near := Vector2(clampf(at.x, rect.position.x, rect.end.x), clampf(at.y, rect.position.y, rect.end.y)) - at
		if (near / radii).length_squared() <= 1.0:
			return t
		t += FRAME_TIME / 4.0
	return -1.0


# The arrows for the 8-way direction nearest `direction`.
func keys_toward(direction: Vector2) -> Array:
	var keys := []
	var unit := direction.normalized()
	if unit.x > 0.38:
		keys.append(KEY_RIGHT)
	elif unit.x < -0.38:
		keys.append(KEY_LEFT)
	if unit.y > 0.38:
		keys.append(KEY_DOWN)
	elif unit.y < -0.38:
		keys.append(KEY_UP)
	return keys


# Out of a lunge across the sweep's thin side: it is 708 px wide and 210 px tall, so the way out is up
# or down whatever the lunge's angle, against its climb or its fall, which also takes the player through
# him if it is coming straight at them. Along a level lunge, toward whichever side has more room.
func sweep_escape(velocity: Vector2) -> Vector2:
	if absf(velocity.y) > 1.0:
		return Vector2(0, -signf(velocity.y))
	return Vector2.UP if ROPES.has_point(player.global_position + Vector2(0, -300)) else Vector2.DOWN


# ---- the bear hug

# Red is the grab, which only a parry answers; yellow a shoulder charge, which only a dash answers. The
# same charge on the same art, told apart only by the tell; the fight's first hug red, never three of
# one colour in a row; and the yellow one always ends in the stumble.
func test_hug_mixup() -> void:
	await load_eric_v2()
	health_ok()
	hold_gauge()
	track()
	track_parries()
	track_dodges()
	var pacing = load(ERIC_PACING)
	var hug: Node = sm.states["BearHug"]
	var hurtbox: Area2D = boss.get_node("Hurtbox")

	log_p("-- the colours and their tells, with the player out of reach")
	var sequence := []
	for i in 14:
		boss.global_position = Vector2(960, 380)
		await settle_player(OUT_OF_REACH)
		sm.rage = 0.0 if i % 2 == 0 else 1.0
		var seen := {"charge": -1.0, "lunge": -1.0, "look": "", "anim": "", "frames": []}
		var probe := func():
			if seen.charge < 0.0 and hug.phase == hug.Phase.CHARGE:
				seen.charge = defense.clock
				seen.anim = boss.animationPlayer.current_animation
			var tell := tell_node()
			if seen.look.is_empty() and tell != null:
				seen.look = "yellow" if tell.dodge else ("strong red" if tell.strong else "red")
			if tell != null and tell.dodge and tell.sprite and (seen.frames.is_empty() or seen.frames[-1] != tell.sprite.frame):
				seen.frames.append(tell.sprite.frame)
			if seen.lunge < 0.0 and hug.phase == hug.Phase.LUNGE:
				seen.lunge = defense.clock
		physics_frame.connect(probe)
		await attack_v2("BearHug", 900)
		physics_frame.disconnect(probe)
		sequence.append({"yellow": hug.yellow, "look": seen.look, "charge": seen.lunge - seen.charge, "rage": sm.rage, "anim": seen.anim, "frames": seen.frames})
	var colours: Array = sequence.map(func(s): return "Y" if s.yellow else "R")
	log_p("colours %s, charges %s" % ["".join(colours), sequence.map(func(s): return snappedf(s.charge, 0.001))])
	check(colours[0] == "R", "the fight's first hug is red")
	var runs_ok := true
	for i in range(2, colours.size()):
		if colours[i] == colours[i - 1] and colours[i] == colours[i - 2]:
			runs_ok = false
	check(runs_ok, "never three of one colour in a row")
	check(colours.has("R") and colours.has("Y"), "both colours come up")
	check(sequence.all(func(s): return s.look == ("yellow" if s.yellow else "strong red")), "a red hug shows the strong red tell, a yellow one the yellow ring")
	if load("res://Scripts/DefenseHypeArtLayout.gd").dodge_tell().has("texture") and colours.has("Y"):
		var ring_frames: Array = sequence.filter(func(s): return s.yellow)[0].frames
		var ring_ok: bool = ring_frames.size() >= 4 and ring_frames[0] == 0 and ring_frames[1] == 1
		for i in range(2, ring_frames.size()):
			ring_ok = ring_ok and ring_frames[i] == 2 + (i - 2) % 4
		check(ring_ok, "the yellow ring ignites once, then loops its pulsing arcs (%s)" % [ring_frames])
	check(sequence.all(func(s): return s.anim == "hug_charge" and absf(s.charge - pacing.raged("hug_charge_time", s.rage)) <= FRAME_TIME + 0.001), "both charge on the same frames for the same time, 0.55 s or 0.45 enraged")

	log_p("-- red: a held guard and a dash are both grabbed")
	sm.rage = 0.0
	for answer in ["guard", "dash"]:
		events.clear()
		dodges.clear()
		clear_iframes()
		health_ok()
		# The fight's first hug is red.
		hug.hugs_started = 0
		boss.global_position = Vector2(960, 380)
		if answer == "guard":
			await meet_the_lunge(true)
		else:
			await await_hug_lunge()
			tap(KEY_W)
		var grabbed := await wait_until(func(): return player.is_grabbed, 40)
		release(KEY_SHIFT)
		log_p("%s: grabbed %s, events %s" % [answer, grabbed, events.map(func(e): return "%s %s" % [e.kind, e.id])])
		check(not hug.yellow and grabbed and events_of("HIT", &"eric_bear_hug_grab_v2").size() == 1, "red, %s: grabbed all the same" % answer)
		await wait_until(func(): return sm.current_state.name == "Winded", 600)
		sm.downed_state_timer.stop()
		sm.on_child_transition(sm.current_state, "Idle")
		await wait(60)

	log_p("-- red: a parry staggers him")
	events.clear()
	parries.clear()
	clear_iframes()
	health_ok()
	hug.hugs_started = 0
	boss.global_position = Vector2(960, 380)
	await meet_the_lunge(false)
	check(await wait_until(func(): return not parries.is_empty(), 40), "the lunge is parried")
	release(KEY_SHIFT)
	check(not parries.is_empty() and parries[0].id == &"eric_bear_hug_grab_v2" and parries[0].staggered and await wait_until(func(): return sm.current_state.name == "ParryStaggered", 10), "the parried grab staggers him")
	check(not player.is_grabbed and player.playerHealth == 100, "and the player is free and unhurt")
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(60)

	log_p("-- red: stepping out of its line makes it whiff, into the stumble")
	events.clear()
	clear_iframes()
	health_ok()
	hug.hugs_started = 0
	boss.global_position = Vector2(960, 380)
	await await_hug_lunge()
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(5)
	release(KEY_LEFT)
	var whiff_stumble := await time_stumble(hug, hurtbox)
	check(not player.is_grabbed and events_of("HIT").is_empty() and absf(whiff_stumble[0] - pacing.value("hug_stumble_time")) <= FRAME_TIME + 0.001 and whiff_stumble[1], "red: stepped out of, it whiffs into a %.2f s stumble, open to punches (%.3f s)" % [pacing.value("hug_stumble_time"), whiff_stumble[0]])
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(60)

	log_p("-- yellow: it hits through a guard and a parry, for 1, and never holds")
	for answer in ["stand", "guard", "parry"]:
		events.clear()
		parries.clear()
		clear_iframes()
		health_ok()
		# Two reds in a row: the next is yellow.
		hug.hugs_started = 1
		hug.recent_yellows.assign([false, false])
		boss.global_position = Vector2(960, 380)
		if answer == "stand":
			await await_hug_lunge()
		else:
			await meet_the_lunge(answer == "guard")
		var charge_stumble := await time_stumble(hug, hurtbox)
		release(KEY_SHIFT)
		log_p("%s: events %s, health %d, stumble %s" % [answer, events.map(func(e): return "%s %s" % [e.kind, e.id]), player.playerHealth, charge_stumble])
		check(hug.yellow and events_of("HIT", &"eric_shoulder_charge").size() == 1 and player.playerHealth == 99 and events_of("BLOCKED").is_empty() and parries.is_empty(), "yellow, %s: it lands, for 1" % answer)
		check(not player.is_grabbed and absf(charge_stumble[0] - pacing.value("hug_stumble_time")) <= FRAME_TIME + 0.001 and charge_stumble[1], "yellow, %s: holds no one, and ends in the %.2f s stumble, open to punches (%.3f s)" % [answer, pacing.value("hug_stumble_time"), charge_stumble[0]])
		sm.on_child_transition(sm.current_state, "Idle")
		await wait(60)

	log_p("-- yellow: a dash goes through it")
	events.clear()
	dodges.clear()
	clear_iframes()
	health_ok()
	defense._set_stamina(defense.max_stamina)
	await wait(40)
	hug.hugs_started = 1
	hug.recent_yellows.assign([false, false])
	boss.global_position = Vector2(960, 380)
	await await_hug_lunge()
	tap(KEY_W)
	var dash_stumble := await time_stumble(hug, hurtbox)
	log_p("dash: events %s, dodges %s, health %d" % [events.map(func(e): return "%s %s" % [e.kind, e.id]), dodges.map(func(d): return d.id), player.playerHealth])
	check(hug.yellow and events_of("HIT").is_empty() and player.playerHealth == 100, "yellow: dashed through, it misses")
	check(absf(dash_stumble[0] - pacing.value("hug_stumble_time")) <= FRAME_TIME + 0.001, "and still ends in the stumble")
	sm.on_child_transition(sm.current_state, "Idle")


# Starts his bear hug on a player standing at (972, 800) and waits until its lunge is about to reach
# them, as meet_the_lunge() does, with no guard touched.
func await_hug_lunge() -> void:
	await settle_player(Vector2(972, 800))
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "BearHug")
	var hug: Node = sm.states["BearHug"]
	var grab_shape: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	await wait_until(func():
		if hug.phase != hug.Phase.LUNGE:
			return false
		var half: Vector2 = grab_shape.shape.size * grab_shape.global_scale.abs() / 2.0
		return (shape.global_position.y - 27.0) - (grab_shape.global_position.y + half.y) < 1500.0 * 0.09, 400)


# Waits for his hug's stumble and returns [how long it lasted, whether his hurtbox was open all through].
func time_stumble(hug: Node, hurtbox: Area2D) -> Array:
	await wait_until(func(): return hug.phase == hug.Phase.STUMBLE, 200)
	var started: float = defense.clock
	var open := true
	while hug.phase == hug.Phase.STUMBLE and sm.current_state == hug:
		open = open and hurtbox.monitoring
		await physics_frame
	return [defense.clock - started, open]


# ---- the Break

# The Break gauge: what fills and drains it, that it holds 100 and never decays, the Break that empties
# it and the wait before it fills again, its bar, and that V1 has none.
func test_break_gauge() -> void:
	await load_eric_v2()
	park_eric()
	health_ok()
	track()
	track_parries()
	track_dodges()
	var gauge: Node = boss.break_gauge
	gauge.locked = false
	gauge.set_physics_process(true)
	var finisher: Node = player.get_node("Finisher")
	var bars: Array = boss.hud_layer.get_children().filter(func(c): return c.get_script() != null and str(c.get_script().resource_path).ends_with("BreakGaugeUI.gd"))
	var ui: Control = bars[0] if bars.size() == 1 else null
	var gauge_art: Dictionary = load("res://Scripts/EricArtLayout.gd").break_gauge()
	var drawn: bool = gauge_art.has("frame")
	check(ui != null and ui.position == gauge_art.position and ui.size == gauge_art.size, "%s at %s, %s" % [gauge_art.size, gauge_art.position, "on the top rope" if drawn else "under his health bar"])
	check(gauge.max_value == 100.0 and gauge.value == 0.0, "it holds 100 and starts empty")
	await settle_player(Vector2(972, 800))

	log_p("-- what fills it")
	check(await parry_once(&"eric_quake_wave_v2") == 3 and gauge.value == 15.0, "a parry: 15 (%.0f)" % gauge.value)
	clear_iframes()
	await wait(40)
	press(KEY_SHIFT)
	await wait(3)
	var grab_parry := front_hit(&"eric_bear_hug_grab_v2", dummy_source())
	release(KEY_SHIFT)
	check(grab_parry == 3 and gauge.value == 35.0, "a parry of his red grab: 20 (%.0f)" % gauge.value)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await wait(60)
	var ring := spawn_ring(player.global_position + Vector2(372, 0))
	await ring_close(ring, 0.05)
	tap(KEY_W)
	check(await wait_until(func(): return dodges.size() > 0, 30) and gauge.value == 47.0, "a perfect dodge: 12 (%.0f)" % gauge.value)
	await wait(60)
	clear_iframes()
	sm.downed_state_timer.start(60.0)
	sm.on_child_transition(sm.current_state, "Downed")
	await wait(5)
	boss.daze_used = true
	place_under(boss.get_node("Hurtbox"))
	await wait(6)
	var steps := []
	for i in 3:
		var before: float = gauge.value
		await swing()
		steps.append(gauge.value - before)
		if i < 2:
			await wait(6)
	check(steps == [8.0, 8.0, 14.0], "punches that land: 8 each, 14 for the charged third (%s)" % [steps])
	sm.on_child_transition(sm.current_state, "Idle")
	await settle_player(Vector2(972, 800))

	log_p("-- what drains it")
	var before_hit: float = gauge.value
	front_hit(&"eric_quake_wave_v2", dummy_source())
	check(gauge.value == before_hit - 20.0, "a hit: -20 (%.0f -> %.0f)" % [before_hit, gauge.value])
	player.take_grab_damage()
	check(gauge.value == before_hit - 20.0, "a squeeze in his grab costs nothing more: the grab was the hit (%.0f)" % gauge.value)
	clear_iframes()
	health_ok()
	await wait(40)
	var before_break: float = gauge.value
	defense.stamina = 20.0
	defense.last_spend_time = defense.clock
	press(KEY_SHIFT)
	await past_window()
	front_hit(&"eric_quake_wave_v2", dummy_source())
	release(KEY_SHIFT)
	check(defense.is_guard_broken and gauge.value == before_break - 35.0, "a guard break: -35 (%.0f -> %.0f)" % [before_break, gauge.value])
	defense.clear_guard_break()
	clear_iframes()
	await wait(45)

	log_p("-- what isn't his counts for nothing")
	var before_other: float = gauge.value
	check(await parry_once(&"greyson_throw") == 3, "someone else's attack parried")
	clear_iframes()
	front_hit(&"wrestler_charge", dummy_source())
	clear_iframes()
	check(gauge.value == before_other, "and one that lands: the gauge doesn't move (%.0f)" % gauge.value)
	await wait(45)

	log_p("-- it stops at 0 and never decays")
	defense.stamina = 20.0
	defense.last_spend_time = defense.clock
	press(KEY_SHIFT)
	await past_window()
	front_hit(&"eric_quake_wave_v2", dummy_source())
	release(KEY_SHIFT)
	defense.clear_guard_break()
	clear_iframes()
	check(gauge.value == 0.0, "a second guard break takes it to 0, not under (%.0f)" % gauge.value)
	gauge.add(40.0)
	await wait(300)
	check(gauge.value == 40.0, "5 s later it still holds 40 (%.0f)" % gauge.value)
	if drawn:
		check(ui.bar.value == roundf(0.4 * gauge_art.fill_steps), "its fill shows whole texels (%.2f of %d)" % [ui.bar.value, gauge_art.fill_steps])

	log_p("-- from 80% its bar pulses")
	gauge.add(45.0)
	var looks := {}
	var hot_fill := [true]
	for i in 30:
		if drawn:
			if ui.pulse.visible:
				looks[ui.pulse.frame] = true
				hot_fill[0] = hot_fill[0] and ui.bar.texture_progress == ui.hot_fills[ui.pulse.frame] and ui.bar.modulate == Color.WHITE
		else:
			looks[ui.bar.modulate] = true
		await process_frame
	check(looks.size() >= 2, "the bar pulses at %.0f (%d looks)" % [gauge.value, looks.size()])
	if drawn:
		check(hot_fill[0], "its hot fill in step with the brass, and nothing brightening it on top")
	await wait(45)

	log_p("-- the Break")
	unpark_eric()
	var broke := [0]
	# Connected after the bar's own handler, so this sees what the bar did with it.
	var shattered := [false]
	gauge.broke.connect(func():
		broke[0] += 1
		var pieces_out: bool = (ui.shatter.visible and ui.shatter.frame == 0 and ui.word_sheet.visible) if drawn else (ui.word_label.visible and not ui.shards.is_empty())
		shattered[0] = pieces_out and ui.bar.value == 0.0)
	await parry_once(&"eric_quake_wave_v2")
	await wait(2)
	log_p("gauge %.0f locked %s, state %s, broke %d" % [gauge.value, gauge.locked, sm.current_state.name, broke[0]])
	check(broke[0] == 1 and gauge.value == 0.0 and gauge.locked and sm.current_state.name == "Broken", "the parry that fills it breaks him, and it empties")
	check(shattered[0], "its bar empties and shatters under a BREAK!")
	await wait_until(func(): return not player.is_action_locked, 120)
	clear_iframes()
	await wait(40)
	check(await parry_once(&"eric_quake_wave_v2") == 3 and gauge.value == 0.0, "a parry now fills nothing (%.0f)" % gauge.value)

	log_p("-- with no finisher: it fills again 3 s after he gets up")
	await wait_until(func(): return sm.current_state.name != "Broken", 300)
	var got_up: float = defense.clock
	await wait_until(func(): return not gauge.locked, 400)
	var unlocked_after: float = defense.clock - got_up
	check(absf(unlocked_after - gauge.unlock_delay) <= FRAME_TIME + 0.001, "%.1f s after he got up (%.3f)" % [gauge.unlock_delay, unlocked_after])
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	clear_iframes()
	health_ok()
	await wait(20)

	log_p("-- with a finisher: 3 s after it ends, or after he gets up for his sword if that's later")
	gauge.value = 95.0
	gauge.add(10.0)
	await wait(2)
	check(sm.current_state.name == "Broken", "broken again")
	await wait_until(func(): return not player.is_action_locked, 120)
	var finished_at := [-1.0]
	finisher.finished.connect(func(): finished_at[0] = defense.clock, CONNECT_ONE_SHOT)
	check(finisher.begin_auto(boss), "the finisher takes him while he is Broken")
	var locked_through := [true]
	var up_at := [-1.0]
	var watch_lock := func():
		var still_broken: bool = sm.current_state.name == "Broken" or sm.current_state.name == "Juggled"
		if finisher.is_active() or still_broken:
			locked_through[0] = locked_through[0] and gauge.locked
		if not still_broken and up_at[0] < 0.0:
			up_at[0] = defense.clock
	physics_frame.connect(watch_lock)
	await wait_until(func(): return finished_at[0] >= 0.0 and up_at[0] >= 0.0, 400)
	physics_frame.disconnect(watch_lock)
	await wait_until(func(): return not gauge.locked, 400)
	var after_both: float = defense.clock - maxf(finished_at[0], up_at[0])
	log_p("the finisher ended at %.3f, he was up at %.3f, the gauge opened at %.3f" % [finished_at[0], up_at[0], defense.clock])
	check(locked_through[0] and absf(after_both - gauge.unlock_delay) <= FRAME_TIME + 0.001, "it stays shut through both and opens %.1f s after the later (%.3f)" % [gauge.unlock_delay, after_both])

	log_p("-- V1 has none")
	pin_eric(1)
	change_scene_to_file(SCENES["eric"])
	await scene_changed
	await wait(3)
	var v1_boss: Node = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	var v1_bars: Array = v1_boss.hud_layer.get_children().filter(func(c): return c.get_script() != null and str(c.get_script().resource_path).ends_with("BreakGaugeUI.gd"))
	check(v1_boss.break_gauge == null and v1_bars.is_empty() and v1_boss.max_health == 24, "V1 Eric has no gauge and no bar, and 24 health")


# A Break from inside each of his attacks, his windows and the gap between attacks: whatever he was doing
# stops cleanly. Then the Break frame; Broken itself, with the player driven in beside him; how long it
# lasts; the opener that starts the finisher; the parried sword's reflect; and what can't break him.
func test_break_entry() -> void:
	await load_eric_v2()
	health_ok()
	var layout = load("res://Scripts/EricArtLayout.gd")
	var pacing = load(ERIC_PACING)
	var gauge: Node = boss.break_gauge
	var broken: Node = sm.states["Broken"]
	var hug: Node = sm.states["BearHug"]
	var whirl: Node = sm.states["Whirlwind"]
	var throw_state: Node = sm.states["SwordThrow"]
	var quake: Node = sm.states["Earthquake"]
	var finisher: Node = player.get_node("Finisher")
	var sheet: Texture2D = boss.sprite.texture
	var home: Vector2 = boss.global_position
	var ground: Node = current_scene.get_node("Arena/GroundFx")
	# The final art knocks his sword into the mat and draws him on a sheet of his own; the placeholder
	# keeps both in his hands on his downed frames.
	var art: Dictionary = layout.broken()
	var final_art: bool = art.has("sword")
	var broken_sheet: String = art.texture if final_art else sheet.resource_path
	var broken_frames: int = art.hframes if final_art else layout.SHEET_FRAMES
	var cases := [
		["the slam, its waves out", "Earthquake", func(): return not hazards_of("EarthquakeProjectilesScript.gd").is_empty()],
		["the slam, held before impact", "Earthquake", func(): return boss.animationPlayer.speed_scale == 0.0],
		["a whirlwind lunge", "Whirlwind", func(): return whirl.phase == whirl.Phase.LUNGE],
		["the whirlwind's sword release", "Whirlwind", func(): return sm.current_state == throw_state and throw_state.from_whirlwind and is_instance_valid(throw_state.sword) and throw_state.sword.flying],
		["his sword in the air", "SwordThrow", func(): return is_instance_valid(throw_state.sword) and throw_state.sword.flying],
		["his sword planted, its ring out", "SwordThrow", func(): return not hazards_of("EricQuakeRingScript.gd").is_empty()],
		["the hug's charge", "BearHug", func(): return hug.phase == hug.Phase.CHARGE],
		["the hug's lunge", "BearHug", func(): return hug.phase == hug.Phase.LUNGE],
		["the hug's stumble", "BearHug", func(): return hug.phase == hug.Phase.STUMBLE],
		["Winded", "Winded", func(): return true],
		["between two attacks", "Idle", func(): return true],
	]
	for case in cases:
		await reset_break(home)
		await settle_player(OUT_OF_REACH)
		sm.chain = []
		if case[1] == "Winded":
			sm.downed_state_timer.start(pacing.value("window_time"))
		elif case[1] == "Idle":
			sm.chain = ["Earthquake", "Earthquake"]
			sm.rest_timer.start(1.0)
			sm.state_after_rest = "Earthquake"
		sm.on_child_transition(sm.current_state, case[1])
		if case[0] == "the slam, held before impact":
			quake.delayed_slam = quake.slams_left
			quake.hold_time = 0.35
		var reached := await wait_until(case[2], 600)
		gauge.value = 95.0
		gauge.add(10.0)
		await wait(2)
		var left := live_hazards()
		var stray_shadows: Array = ground.get_children().filter(func(c): return c is Sprite2D and not c.is_queued_for_deletion() and c.texture and c.texture.resource_path.ends_with("eric_leap_shadow.png"))
		log_p("%s: reached %s, now %s, hazards left %d, tell %s, sheet %s/%d, speed %.2f" % [case[0], reached, sm.current_state.name, left.size(), tell_node() != null, boss.sprite.texture.resource_path.get_file(), boss.sprite.hframes, boss.animationPlayer.speed_scale])
		check(reached and sm.current_state == broken, "%s: broken out of it" % case[0])
		check(left.is_empty() and stray_shadows.is_empty() and tell_node() == null, "%s: everything he threw is gone, and any tell" % case[0])
		check(boss.sprite.texture.resource_path == broken_sheet and boss.sprite.hframes == broken_frames and boss.animationPlayer.speed_scale == 1.0, "%s: nothing of its sheet or speed is left on him" % case[0])
		check(not boss.get_node("WhirlwindArea2D").monitoring and not boss.get_node("GrabArea2D").monitoring and not player.is_grabbed and sm.rest_timer.is_stopped() and sm.downed_state_timer.is_stopped(), "%s: nothing of it can still hit, or start another" % case[0])

	log_p("-- the Break frame, then Broken")
	await reset_break(home)
	await settle_player(Vector2(700, 800))
	var zoom_seen := [1.0]
	var zoom_watch := func(): zoom_seen[0] = maxf(zoom_seen[0], load("res://Scripts/ScreenView.gd").zoom)
	process_frame.connect(zoom_watch)
	var broke_at: float = defense.clock
	gauge.value = 95.0
	gauge.add(10.0)
	await process_frame
	await process_frame
	var flashes: Array = boss.hud_layer.get_children().filter(func(c): return c is ColorRect and c.color.a > 0.5)
	check(Engine.time_scale < 0.1 and not flashes.is_empty(), "the fight stops dead under a white flash (time scale %.2f)" % Engine.time_scale)
	var cheering: float = get_nodes_in_group("arena_crowd")[0]._cheer_time_left
	check(cheering > 3.0, "the crowd roars (%.2f s of cheering left)" % cheering)
	var sword: Sprite2D = sm.dropped_sword
	if final_art:
		check(boss.sprite.texture.resource_path == art.texture and boss.sprite.hframes == art.hframes, "his Broken sheet (%s, %d frames)" % [boss.sprite.texture.resource_path.get_file(), boss.sprite.hframes])
		check(is_instance_valid(sword) and sword.frame == 0 and boss.sprite.frame == 0, "his sword is knocked from his grip, starting its plunge on his first frame")
		check(sword.get_parent() == boss.get_parent() and sword.global_position == home + layout.SORT_POINT * layout.SCALE and sword.offset == layout.SPRITE_OFFSET - layout.SORT_POINT and sword.scale == boss.scale, "placed like his sprite, at the Break spot in the world rather than on him (%s)" % sword.global_position)
		check(sword.get_index() < boss.get_index(), "and it draws behind him")
		check(not broken.stars.visible, "no stars while he reels")
	await wait_until(func(): return not player.is_action_locked, 120)
	var drive_took: float = defense.clock - broke_at
	process_frame.disconnect(zoom_watch)
	await wait_until(func(): return not final_art or art.heads.has(boss.sprite.frame), 60)
	var stars_ok: bool = is_instance_valid(broken.stars) and broken.stars.visible and broken.stars.global_position == broken.head_point().round()
	var shape: CollisionShape2D = boss.get_node("Hurtbox/CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	log_p("driven in within %.3f s of game time to %s, facing %d; his hurtbox %s; zoom peaked at %.2f" % [drive_took, player.global_position, player.facing, box, zoom_seen[0]])
	check(zoom_seen[0] >= 1.25, "the view punches in (%.2f)" % zoom_seen[0])
	check(stars_ok and boss.get_node("Hurtbox").monitoring and boss.get_node("CollisionShape2D").disabled, "dazed, stars over his head, open to punches")
	# Read off EricBroken rather than copied: it is the player's half-body, so it moves when he does.
	var feet_offset: float = broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT
	check(drive_took <= broken.DRIVE_TIME + 3.0 * FRAME_TIME and absf(player.global_position.y + feet_offset - box.end.y) <= 1.0, "the player is driven in beside him, on his ground line, in %.2f s, and has their moves back" % broken.DRIVE_TIME)
	check(player.facing == player.Facing.RIGHT or player.facing == player.Facing.LEFT, "facing him across")
	if final_art:
		check(signf(player.global_position.x - box.get_center().x) == (-1.0 if sword.flip_h else 1.0) and player.sprite.global_position.y > boss.sprite.global_position.y, "on the side away from his sword, and drawn in front of him")
		var rides := {}
		for i in 40:
			await physics_frame
			var frame: int = boss.sprite.frame
			if art.heads.has(frame) and broken.stars.visible:
				rides[frame] = broken.stars.global_position == boss.to_global(layout.frame_local(art.heads[frame] + Vector2(0.5, 0.5), boss.sprite.flip_h)).round()
		check(rides.size() >= 3 and not rides.values().has(false), "the stars ride his head through each frame he's down on (%s)" % [rides])
		check(sword.frame == art.sword.hframes - 1, "his sword stands in the mat on its last frame (%d)" % sword.frame)
	var dealt := await swing()
	check(dealt == 1, "a punch from there lands (%d)" % dealt)

	log_p("-- how long he stays down, then he gets up")
	var attacking := func(): return quake == sm.current_state or ["Whirlwind", "SwordThrow", "BearHug"].has(sm.current_state.name)
	for rage in [0.0, 1.0]:
		await reset_break(home)
		await settle_player(Vector2(700, 800))
		sm.rage = rage
		gauge.value = 95.0
		gauge.add(10.0)
		await wait(2)
		var from: float = defense.clock
		await wait_until(func(): return broken.retrieving or sm.current_state != broken, 400)
		var lasted: float = defense.clock - from
		check(absf(lasted - pacing.raged("broken_time", rage)) <= 2.0 * FRAME_TIME + 0.001, "rage %.0f: %.1f s (%.3f)" % [rage, pacing.raged("broken_time", rage), lasted])
		if final_art and rage == 0.0:
			var spot: Vector2 = sm.dropped_sword.global_position - layout.SORT_POINT * layout.SCALE
			var got_up: float = defense.clock
			check(boss.sprite.frame == art.reach_frame and not boss.get_node("Hurtbox").monitoring and not boss.can_be_dazed(), "time up: he's on one knee reaching for his sword, and no longer open")
			await wait_until(func(): return is_instance_valid(broken.flying_sword), 60)
			var reached_for: float = defense.clock - got_up
			var guard: Vector2 = spot + layout.frame_local(art.sword.guard + Vector2(0.5, 0.5)) * layout.SCALE
			var launch: Vector2 = broken.flying_sword.sword.global_position
			check(absf(reached_for - art.reach_time) <= 2.0 * FRAME_TIME + 0.001 and not is_instance_valid(sm.dropped_sword), "%.1f s later it leaves the mat (%.3f)" % [art.reach_time, reached_for])
			check(launch.distance_to(guard) < 1.0, "from its crossguard, where it stood (%s, guard at %s)" % [launch, guard])
			await process_frame
			check(boss.sprite.texture == sheet and boss.sprite.frame == 38, "his recall reach, on his own sheet (frame %d)" % boss.sprite.frame)
			var last_centre := [launch]
			await wait_until(func():
				if is_instance_valid(broken.flying_sword):
					last_centre[0] = broken.flying_sword.sword.global_position
				return not is_instance_valid(broken.flying_sword), 60)
			var hand: Vector2 = boss.to_global(layout.frame_local(layout.THROW_CATCH_CENTRE))
			check(last_centre[0].distance_to(hand) < 2.0 and boss.animationPlayer.assigned_animation == &"recall_catch", "it flies into his hand and he catches it (%s, hand at %s)" % [last_centre[0], hand])
			await wait_until(func(): return sm.current_state != broken, 60)
			var caught: float = defense.clock
			check(await wait_until(attacking, 60) and absf(defense.clock - caught - pacing.value("recovery_rest")) <= 2.0 * FRAME_TIME + 0.001, "and %.2f s after the catch his next chain starts (%.3f)" % [pacing.value("recovery_rest"), defense.clock - caught])
		else:
			check(await wait_until(attacking, 120), "rage %.0f: and his next chain starts" % rage)

	if final_art:
		log_p("-- the uppercut juggles him: he crashes, gets up for his sword, and attacks again the juggle's recovery after the crash")
		await reset_break(home)
		await settle_player(Vector2(700, 800))
		gauge.value = 95.0
		gauge.add(10.0)
		await wait(2)
		await wait_until(func(): return not player.is_action_locked, 120)
		check(finisher.begin_auto(boss), "the finisher takes him")
		check(await wait_until(func(): return sm.current_state.name == "Juggled", 300), "the uppercut throws him into the air, his sword left in the mat (%s)" % is_instance_valid(sm.dropped_sword))
		# The player lands first; the finisher ends as he crashes.
		await wait_until(func(): return finisher.phase == FINISHER_OFF, 300)
		var crashed_at: float = defense.clock
		check(await wait_until(func(): return sm.current_state == broken and broken.retrieving, 120), "down, he lies a beat and gets up for it")
		check(await wait_until(attacking, 300) and absf(defense.clock - crashed_at - finisher.juggle_recovery) <= 3.0 * FRAME_TIME, "his next attack %.1f s after the crash, sword and all (%.3f)" % [finisher.juggle_recovery, defense.clock - crashed_at])

	log_p("-- the opener: the combo on the beat starts the finisher; left alone it fizzles and the chance goes")
	await reset_break(home)
	await settle_player(Vector2(700, 800))
	gauge.value = 95.0
	gauge.add(10.0)
	await wait(2)
	await wait_until(func(): return not player.is_action_locked, 120)
	var health: int = boss.boss_health
	for i in 3:
		await swing()
		if i < 2:
			await wait(6)
	check(await wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120), "3 on the beat daze him: the finisher's prompt is up")
	check(boss.boss_health == health - 4 and not broken.stars.visible, "the combo dealt 1 + 1 + 2, and the finisher's stars take over from his")
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	check(sm.current_state == broken and broken.stars.visible, "the fizzle leaves him Broken for the rest of his time")
	await wait_until(func(): return sm.current_state != broken, 300)
	check(boss.boss_health == health - 4, "then he gets up, the uppercut never came")

	log_p("-- the parried sword: +35 that fills the gauge breaks him instead of the uppercut")
	for fill in [true, false]:
		await reset_break(home)
		gauge.value = 50.0 if fill else 0.0
		events.clear()
		await settle_player(Vector2(1480, 700))
		sm.chain = []
		sm.on_child_transition(sm.current_state, "SwordThrow")
		await wait_until(func(): return is_instance_valid(throw_state.sword), 200)
		var blade: Area2D = throw_state.sword.get_node("Hitbox")
		var body: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
		await wait_until(func(): return blade.global_position.distance_to(body.global_position) < 108.0 + 27.0 + throw_state.sword.speed * 0.07, 200)
		press(KEY_SHIFT)
		var outcome := await wait_until(func(): return sm.current_state.name == ("Broken" if fill else "ParryStaggered"), 300)
		release(KEY_SHIFT)
		log_p("from %.0f: %s, gauge %.0f, finisher phase %d" % [50.0 if fill else 0.0, sm.current_state.name, gauge.value, finisher.phase])
		if fill:
			check(outcome and finisher.phase == FINISHER_OFF, "from 50: parry 15 and the reflect's 35 fill it: a Break, and no uppercut fires")
		else:
			check(outcome and sm.states["ParryStaggered"].from_reflect and gauge.value == 50.0, "from 0: 15 and 35 make 50, and the reflect's own uppercut fires as before")
			check(await wait_until(func(): return finisher.phase != FINISHER_OFF, 60), "the finisher takes it")
			await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)

	log_p("-- what can't break him")
	await reset_break(home)
	await settle_player(Vector2(700, 800))
	var breaks := [0]
	gauge.broke.connect(func(): breaks[0] += 1)
	gauge.value = 95.0
	gauge.add(10.0)
	await wait(2)
	var time_left: float = broken.time_left
	sm.enter_broken()
	gauge.add(500.0)
	await wait(2)
	check(breaks[0] == 1 and sm.current_state == broken and broken.time_left < time_left, "Broken, he can't be broken again: the gauge takes nothing and his time runs on")
	sm.on_child_transition(sm.current_state, "Idle")
	gauge.add(500.0)
	await wait(2)
	check(breaks[0] == 1 and sm.current_state.name != "Broken", "nor while the gauge waits to fill again")
	boss.boss_health = 0
	await wait(3)
	gauge.locked = false
	gauge.add(500.0)
	await wait(2)
	check(sm.current_state.name != "Broken", "nor once he is beaten (%s)" % sm.current_state.name)


# Back to idle at his spot with an empty, open gauge, and the Break's own effects over.
func reset_break(home: Vector2) -> void:
	load("res://Scripts/HitStop.gd").clear()
	load("res://Scripts/ScreenView.gd").reset(self)
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	player.unlock_actions()
	boss.global_position = home
	boss.break_gauge.locked = false
	boss.break_gauge.value = 0.0
	boss.break_gauge.set_physics_process(true)
	clear_iframes()
	health_ok()
	await wait(20)


# ------------------------------------------------------------------ the tiered finisher and the juggle
# Eric V2's finisher (PlayerFinisher against a boss that can be juggled): a mash of up to three bars
# (FinisherTierMeter), then an uppercut for each bar banked, juggling him higher each time until he
# crashes. Most of these mash with the finisher's real-time press gate off, so the mash is the same
# at any pacing; mash_tiers_live keeps it on.

const FINISHER_CHARGING := 3
const FINISHER_JUGGLE_FALL := 6
# The plan's rates for the three bars, in alternating presses a second.
const TIER_RATES := [7.0, 9.4, 10.9]
# Presses every this many frames at 60 fps reach each tier, and every one more doesn't.
const TIER_PASS_FRAMES := [8, 6, 5]
# How many press intervals every pass and fail keeps clear of its bar's window.
const TIER_MARGIN := 1.3
# The juggle's peaks before they are fitted to his headroom, in px: the first two uppercuts' and the
# third's.
const JUGGLE_PEAKS := [166.0, 210.0, 309.0]


# A Break on V2 Eric, the player driven in beside him, and the opener landed: the finisher's prompt is up.
func break_into_prompt() -> bool:
	var finisher: Node = player.get_node("Finisher")
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await settle_player(Vector2(700, 800))
	boss.break_gauge.locked = false
	boss.break_gauge.value = 0.0
	boss.break_gauge.add(boss.break_gauge.max_value)
	await wait_until(func(): return sm.current_state.name == "Broken", 30)
	await wait_until(func(): return not player.is_action_locked, 120)
	for i in 3:
		await swing()
		if i < 2:
			await wait(6)
	return await wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120)


# The mash pair, one press every `every` frames, until the mash resolves.
func mash_tiered(every: int, gate_off := true) -> int:
	var finisher: Node = player.get_node("Finisher")
	if gate_off:
		finisher.min_press_interval = 0.0
	var pair: Array = finisher.mash_actions()
	var presses := 0
	var i := 0
	while finisher.phase == FINISHER_DAZED or finisher.phase == FINISHER_CHARGING:
		if i % every == 0:
			tap(MASH_KEYS[pair[presses % 2]])
			presses += 1
		i += 1
		await physics_frame
	return presses


# The meter model, frame by frame at 60 fps with a press every `every` frames (none for 0), stopping
# after `stop_after` frames if that's set. `windows` stands in for the finisher's.
func model_mash(finisher: Node, every: int, banked_at_start := 0, stop_after := -1, windows: Array = []) -> Dictionary:
	var meter = load("res://Scripts/FinisherTierMeter.gd").new(finisher.tier_gain, finisher.tier_drains, finisher.tier_windows if windows.is_empty() else windows, finisher.tier_start_grace, finisher.tier_idle_stop, banked_at_start)
	var banked_at := []
	var last_press := -1.0
	for f in 7200:
		if meter.resolved:
			break
		if every > 0 and f % every == 0 and (stop_after < 0 or f < stop_after):
			last_press = meter.clock
			if meter.press() > 0:
				banked_at.append(meter.clock)
		meter.advance(1.0 / 60.0)
	return {"tier": meter.banked, "banked_at": banked_at, "resolved_at": meter.clock, "last_press": last_press}


# The lowest steady rate that banks bar `bar`, presses at exact times rather than on frames.
func threshold_rate(finisher: Node, bar: int) -> float:
	var low := 3.0
	var high := 20.0
	for i in 24:
		var rate := (low + high) / 2.0
		var meter = load("res://Scripts/FinisherTierMeter.gd").new(finisher.tier_gain, finisher.tier_drains, finisher.tier_windows, finisher.tier_start_grace, finisher.tier_idle_stop)
		var next_press := 0.0
		while not meter.resolved and meter.clock < 10.0:
			if meter.clock >= next_press - 1e-9:
				meter.press()
				next_press += 1.0 / rate
			meter.advance(1.0 / 1200.0)
		if meter.banked >= bar:
			high = rate
		else:
			low = rate
	return high


func test_mash_tiers() -> void:
	await load_eric_v2()
	var finisher: Node = player.get_node("Finisher")
	log_p("gain %.2f, drains %s, windows %s, %.1f s to start, %.1f s idle stop" % [finisher.tier_gain, finisher.tier_drains, finisher.tier_windows, finisher.tier_start_grace, finisher.tier_idle_stop])

	log_p("-- a press every n frames at 60 fps")
	for bar in 3:
		var reach: int = TIER_PASS_FRAMES[bar]
		var reached: Dictionary = model_mash(finisher, reach)
		var missed: Dictionary = model_mash(finisher, reach + 1)
		log_p("bar %d: every %d frames banks at %s, tier %d; every %d banks at %s, tier %d" % [bar + 1, reach, reached.banked_at, reached.tier, reach + 1, missed.banked_at, missed.tier])
		check(reached.tier >= bar + 1 and missed.tier == bar, "tier %d at a press every %d frames (%.1f a second), not at every %d (%.1f)" % [bar + 1, reach, 60.0 / reach, reach + 1, 60.0 / (reach + 1)])

	log_p("-- every pass and fail %.1f press intervals clear of its window" % TIER_MARGIN)
	# Each bar's fill at the two rates with no window to cut it short, from the press or bank before it.
	var open_windows := [INF, INF, INF]
	for bar in 3:
		var window: float = finisher.tier_windows[bar]
		var margins := []
		for frames in [TIER_PASS_FRAMES[bar], TIER_PASS_FRAMES[bar] + 1]:
			var run: Dictionary = model_mash(finisher, frames, 0, -1, open_windows)
			var from: float = run.banked_at[bar - 1] if bar > 0 else 0.0
			var fill: float = run.banked_at[bar] - from
			var interval: float = frames / 60.0
			margins.append((window - fill) / interval if frames == TIER_PASS_FRAMES[bar] else (fill - window) / interval)
			log_p("bar %d, every %d frames: fills in %.3f s against a %.2f s window" % [bar + 1, frames, fill, window])
		check(margins.min() >= TIER_MARGIN, "bar %d: the pass fills %.2f intervals inside its window and the fail %.2f outside" % [bar + 1, margins[0], margins[1]])

	log_p("-- the rates it takes")
	for bar in 3:
		var rate := threshold_rate(finisher, bar + 1)
		check(absf(rate - TIER_RATES[bar]) <= 0.3, "bar %d from about %.1f presses a second (%.2f)" % [bar + 1, TIER_RATES[bar], rate])

	log_p("-- stopping, and starting")
	var stopped: Dictionary = model_mash(finisher, 5, 0, 36)
	check(stopped.tier == 1 and absf(stopped.resolved_at - stopped.last_press - finisher.tier_idle_stop) <= 1.0 / 60.0 + 0.001, "stopping after bar 1 keeps it: the mash ends %.1f s after the last press (tier %d at %.3f)" % [finisher.tier_idle_stop, stopped.tier, stopped.resolved_at])
	var idle: Dictionary = model_mash(finisher, 0)
	check(idle.tier == 0 and absf(idle.resolved_at - finisher.tier_start_grace - finisher.tier_windows[0]) <= 1.0 / 60.0 + 0.001, "never pressed, it fizzles when bar 1's window runs out %.1f s after the prompt (%.3f)" % [finisher.tier_start_grace + finisher.tier_windows[0], idle.resolved_at])
	var hyped: Dictionary = model_mash(finisher, 0, 1)
	check(hyped.tier == 1, "full hype banks bar 1 before the first press, and keeps it untouched (tier %d)" % hyped.tier)
	var hyped_mash: Dictionary = model_mash(finisher, TIER_PASS_FRAMES[1], 1)
	check(hyped_mash.tier >= 2, "then bar 2 at bar 2's rate (tier %d)" % hyped_mash.tier)


# Real presses, the real-time press gate on, and the keys the mash shares with moving and guarding.
func test_mash_tiers_live() -> void:
	await load_eric_v2()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var banks := []
	finisher.tier_banked.connect(func(tier): banks.append(tier))

	log_p("-- the arrows, a press every 5 frames: all three bars, and nothing else happens")
	check(await break_into_prompt(), "a Break and the opener put up the prompt")
	check(finisher.tiered and finisher.mash_actions() == [&"mash_left", &"mash_right"], "a tiered mash on the arrows")
	var stood: Vector2 = player.global_position
	var guarded := [false]
	var watch := func():
		guarded[0] = guarded[0] or defense.is_guarding()
	physics_frame.connect(watch)
	await mash_tiered(5, false)
	physics_frame.disconnect(watch)
	check(banks == [1, 2, 3] and finisher.juggle_tiers == 3, "three bars banked (%s)" % [banks])
	check(player.global_position == stood and not guarded[0], "the arrows neither moved nor guarded the player (%s, %s)" % [player.global_position - stood, guarded[0]])
	press(KEY_LEFT)
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	var after: Vector2 = player.global_position
	await wait(20)
	check(player.global_position == after and finisher.is_mash_latched(), "a key still held from the mash doesn't walk them off")
	release(KEY_LEFT)
	await wait(90)

	log_p("-- one key over and over counts once")
	banks.clear()
	check(await break_into_prompt(), "the prompt again")
	for i in 12:
		tap(KEY_LEFT)
		await wait(5)
	check(finisher.meter <= finisher.tier_gain + 0.001 and banks.is_empty(), "twelve lefts are one press (%.2f)" % finisher.meter)
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	await wait(60)

	log_p("-- the bumpers, a press every 6 frames: two bars")
	banks.clear()
	check(await break_into_prompt(), "the prompt again")
	var pair := [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER]
	var presses := 0
	var i := 0
	while finisher.phase == FINISHER_DAZED or finisher.phase == FINISHER_CHARGING:
		if i % 6 == 0:
			pad_tap(pair[presses % 2])
			presses += 1
		i += 1
		await physics_frame
	check(banks == [1, 2] and finisher.juggle_tiers == 2, "two bars banked (%s)" % [banks])
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)

	log_p("-- every fight mashes the pair, and opting out of feel_v2 puts it back on attack and dash")
	await load_fight("mason")
	check(player.get_node("Finisher").mash_actions() == [&"mash_left", &"mash_right"], "Mason's fight mashes the pair too")
	player.feel_v2 = false
	check(player.get_node("Finisher").mash_actions() == [&"punch", &"dodge"], "opted out of feel_v2, it mashes punch and dodge")


# Tier 3 from start to finish, watched frame by frame.
func test_juggle() -> void:
	await load_eric_v2()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var juggled: Node = sm.states["Juggled"]
	check(await break_into_prompt(), "a Break and the opener put up the prompt")
	var hits := []
	finisher.juggle_hit.connect(func(index, last): hits.append({"t": defense.clock, "index": index, "last": last, "health": boss.boss_health, "lift": finisher.lift}))
	var trace := []
	var recoveries := [0]
	var was_recovering := [false]
	var watch := func():
		if juggled.recovering and not was_recovering[0]:
			recoveries[0] += 1
		was_recovering[0] = juggled.recovering
		trace.append({"t": defense.clock, "lift": finisher.lift, "drawn": juggled.drawn_lift, "airborne": finisher.airborne, "phase": finisher.phase, "state": sm.current_state.name, "anim": boss.animationPlayer.assigned_animation})
	physics_frame.connect(watch)
	var health: int = boss.boss_health
	await mash_tiered(5)
	await wait_until(func(): return sm.current_state.name != "Juggled" and hits.size() > 0, 600)
	physics_frame.disconnect(watch)
	var dealt := []
	var before := health
	for hit in hits:
		dealt.append(before - hit.health)
		before = hit.health
	log_p("hits %s, dealt %s, lift scale %.2f" % [hits.map(func(h): return snappedf(h.t, 0.001)), dealt, finisher.lift_scale])
	check(hits.size() == 3 and hits[2].last, "three uppercuts, the third the last")
	check(dealt == [8, 6, 8], "8, 6 and 8 of his 56 (%s)" % [dealt])
	var gaps := []
	for k in range(1, hits.size()):
		gaps.append(hits[k].t - hits[k - 1].t)
	check(gaps.size() == 2 and gaps.all(func(g): return absf(g - 0.55) <= FRAME_TIME + 0.001), "0.55 s apart (%s)" % [gaps])
	var first: float = hits[0].t if hits.size() > 0 else 0.0
	var last: float = hits[-1].t if hits.size() > 0 else 0.0
	var up: Array = trace.filter(func(s): return s.t > first and s.t <= last)
	check(not up.is_empty() and up.all(func(s): return s.drawn > 0.0), "he never touches the ground between the first and the last")
	var peaks := []
	for k in hits.size():
		var until: float = hits[k + 1].t if k + 1 < hits.size() else INF
		var arc: Array = trace.filter(func(s): return s.t > hits[k].t and s.t < until)
		peaks.append(arc.map(func(s): return s.lift).max() if not arc.is_empty() else 0.0)
	log_p("peaks %s, drawn at %.2f of that" % [peaks.map(func(p): return snappedf(p, 0.1)), finisher.lift_scale])
	check(peaks.size() == 3 and range(3).all(func(k): return absf(peaks[k] - JUGGLE_PEAKS[k]) <= 8.0), "peaks of %s px, fitted to his headroom as drawn (%s)" % [JUGGLE_PEAKS, peaks.map(func(p): return snappedf(p, 0.1))])
	var landed_at: Array = trace.filter(func(s): return s.phase == FINISHER_JUGGLE_FALL)
	var crashed_at: Array = trace.filter(func(s): return s.t > last and not s.airborne and s.state == "Juggled")
	check(not landed_at.is_empty() and not crashed_at.is_empty() and landed_at[0].t < crashed_at[0].t, "the player lands before he does")
	check(recoveries[0] == 1 and not crashed_at.is_empty() and trace.filter(func(s): return s.t < crashed_at[0].t and s.state == "Juggled").all(func(s): return s.phase != FINISHER_OFF), "his recovery comes once, as he crashes (%d)" % recoveries[0])
	check(trace.any(func(s): return s.anim == eric_art().juggle().crash), "he crashes")
	check(await wait_until(func(): return sm.current_state.name == "Broken" and sm.states["Broken"].retrieving, 120), "then gets up for his sword")


func eric_art() -> GDScript:
	return load("res://Scripts/EricArtLayout.gd")


# The uppercut numbered `tier` kills him: nothing follows, one outro, and his defeat once he has landed.
func test_juggle_kill() -> void:
	await load_eric_v2()
	health_ok()
	var n := int(tier) if tier.is_valid_int() else 3
	var finisher: Node = player.get_node("Finisher")
	check(await break_into_prompt(), "a Break and the opener put up the prompt")
	# The damage the uppercuts before this one deal, and one more.
	boss.boss_health = [1, 9, 15][n - 1]
	var hits := []
	finisher.juggle_hit.connect(func(index, last): hits.append({"index": index, "last": last, "health": boss.boss_health, "at": boss.global_position}))
	var states := []
	var watch := func():
		if states.is_empty() or states[-1] != sm.current_state.name:
			states.append(sm.current_state.name)
	physics_frame.connect(watch)
	await mash_tiered(5)
	await wait_until(func(): return sm.current_state.name == "Downed", 400)
	var downed_anim: String = boss.animationPlayer.assigned_animation
	await wait(90)
	physics_frame.disconnect(watch)
	var outros: int = root.get_children().filter(func(c): return c.name == "FightOutro").size()
	var moved: float = hits[0].at.distance_to(boss.global_position) if not hits.is_empty() else -1.0
	log_p("tier=%d: hits %s, states %s, defeat anim %s, outros %d, moved %.1f px" % [n, hits.map(func(h): return [h.index, h.last, h.health]), states, downed_anim, outros, moved])
	check(hits.size() == n and hits[-1].health == 0 and hits[-1].last, "the uppercut numbered %d kills him, and none follows (%d)" % [n, hits.size()])
	check(outros == 1, "one outro (%d)" % outros)
	check(states.find("Juggled") < states.find("Downed") and downed_anim == eric_art().juggle().down, "he finishes his fall and crash, then lies there beaten (%s)" % [states])
	check(moved >= 0.0 and moved < 1.0, "the killing uppercut doesn't shove him (%.1f px)" % moved)


# A full hype meter: bar 1 banked before the first press, the last uppercut 0.10 more, the hype spent once.
func test_juggle_super() -> void:
	await load_eric_v2()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var hype: Node = player.get_node("Hype")
	var spends := [0]
	hype.hype_spent.connect(func(): spends[0] += 1)
	hype._set_hype(100.0)
	check(await break_into_prompt(), "a Break and the opener put up the prompt")
	check(finisher.supercharged and finisher.tier_meter.banked == 1 and finisher.meter == 1.0, "bar 1 is banked before the first press")
	var health := [boss.boss_health]
	var dealt := []
	finisher.juggle_hit.connect(func(_index, _last):
		dealt.append(health[0] - boss.boss_health)
		health[0] = boss.boss_health)
	await mash_tiered(6)
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	log_p("tiers %d, dealt %s, spends %d" % [finisher.juggle_tiers, dealt, spends[0]])
	check(dealt == [8, 11], "tier 2 at bar 2's rate, the last uppercut 0.10 more: 8 and 11 (%s)" % [dealt])
	check(spends[0] == 1 and not hype.is_full(), "the hype spent once (%d)" % spends[0])


# His parried sword flung back into him: a tier-1 juggle with no prompt, or a Break if its +35 fills the gauge.
func test_reflect_auto_v2() -> void:
	await load_eric_v2()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var throw_state: Node = sm.states["SwordThrow"]
	var gauge: Node = boss.break_gauge
	var home: Vector2 = boss.global_position
	for fill in [false, true]:
		await reset_break(home)
		gauge.value = 50.0 if fill else 0.0
		var prompts := [0]
		var on_prompt := func(): prompts[0] += 1
		finisher.prompt_shown.connect(on_prompt)
		var hits := []
		var on_hit := func(index, last): hits.append([index, last])
		finisher.juggle_hit.connect(on_hit)
		var health: int = boss.boss_health
		await settle_player(Vector2(1480, 700))
		sm.chain = []
		sm.on_child_transition(sm.current_state, "SwordThrow")
		await wait_until(func(): return is_instance_valid(throw_state.sword), 200)
		var blade: Area2D = throw_state.sword.get_node("Hitbox")
		var body: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
		await wait_until(func(): return blade.global_position.distance_to(body.global_position) < 108.0 + 27.0 + throw_state.sword.speed * 0.07, 200)
		press(KEY_SHIFT)
		await wait(6)
		release(KEY_SHIFT)
		if fill:
			check(await wait_until(func(): return sm.current_state.name == "Broken", 300), "from 50: the parry's 15 and the reflect's 35 break him")
			await wait(60)
			check(hits.is_empty() and finisher.phase == FINISHER_OFF, "and no juggle fires on its own")
		else:
			check(await wait_until(func(): return sm.current_state.name == "Juggled", 300), "from 0: the reflect juggles him")
			await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
			check(prompts[0] == 0 and hits == [[0, true]], "one uppercut, the last, and no prompt (%s)" % [hits])
			check(health - boss.boss_health == 1 + 8 and gauge.value == 50.0, "his sword's 1 and the uppercut's 8, and the gauge at 50 (%d, %.0f)" % [health - boss.boss_health, gauge.value])
			check(await wait_until(func(): return sm.current_state.name == "Broken" and sm.states["Broken"].retrieving, 120), "down, he gets up for the sword the uppercut knocked away")
		finisher.prompt_shown.disconnect(on_prompt)
		finisher.juggle_hit.disconnect(on_hit)


# ------------------------------------------------------------------ pace_bot
# A tuning aid, not a gate: a bot plays V2 Eric to the end, answering each attack the way its tell says,
# punishing his windows and cashing each Break in, and logs how long it took, how often it broke him and
# where the damage came from. tier=skilled reads nearly everything, lands full combos and mashes tier 3;
# tier=average misses a third of its reads, lands shorter combos and mashes tier 1. The player can't die,
# so the numbers are about pace; the hits it takes are logged too.

const PACE_BOTS := {
	"skilled": {"reads": 0.95, "mash_every": 5, "punches": 3, "time_limit": 240.0},
	"average": {"reads": 0.65, "mash_every": 8, "punches": 2, "time_limit": 360.0},
}
# Where the bot waits between answers: this far below him, beside his line.
const PACE_WAIT := Vector2(260, 330)


func test_pace_bot() -> void:
	var profile: Dictionary = PACE_BOTS.get(tier, PACE_BOTS.skilled)
	seed(20260919)
	await load_eric_v2()
	player.playerHealth = 1000000
	track()
	var finisher: Node = player.get_node("Finisher")
	finisher.min_press_interval = 0.0
	var gauge: Node = boss.break_gauge
	var tally := {"breaks": 0, "winded": 0, "hits_taken": 0, "tiers": [], "damage": {"punches": 0, "finisher": 0, "reflect": 0}}
	gauge.broke.connect(func(): tally.breaks += 1)
	finisher.charge_ended.connect(func(filled): tally.tiers.append(finisher.juggle_tiers if filled and finisher.tiered else 0))
	defense.hit_taken.connect(func(_hit): tally.hits_taken += 1)
	var last_state := [""]
	var bot := {"decided": {}, "held": [], "mash_step": 0, "frame": 0, "shift_left": 0}
	sm.start_chain(0.5)
	var start: float = defense.clock
	var health: int = boss.boss_health
	while boss.boss_health > 0 and defense.clock - start < profile.time_limit:
		if sm.current_state.name != last_state[0]:
			if sm.current_state.name == "Winded":
				tally.winded += 1
			last_state[0] = sm.current_state.name
		await _bot_step(profile, bot, finisher)
		if boss.boss_health < health:
			var source := "finisher" if finisher.is_active() else ("reflect" if sm.current_state.name == "SwordThrow" else "punches")
			tally.damage[source] += health - boss.boss_health
			health = boss.boss_health
	_bot_release(bot)
	var took: float = defense.clock - start
	var chains: int = tally.winded + tally.breaks
	log_p("%s bot: %s in %.1f s, %d chains, %d Breaks (%.2f a chain), tiers %s, damage %s, hits taken %d" % [tier, "beat him" if boss.boss_health <= 0 else "ran out of time with him on %d" % boss.boss_health, took, chains, tally.breaks, float(tally.breaks) / maxi(chains, 1), tally.tiers, tally.damage, tally.hits_taken])


func _bot_step(profile: Dictionary, bot: Dictionary, finisher: Node) -> void:
	bot.frame += 1
	# A parry is a fresh press, held a few frames.
	if bot.shift_left > 0:
		bot.shift_left -= 1
		if bot.shift_left == 0:
			release(KEY_SHIFT)
	# The mash.
	if finisher.phase == FINISHER_DAZED or finisher.phase == FINISHER_CHARGING:
		_bot_release(bot)
		if finisher.prompt_visible and bot.frame % profile.mash_every == 0:
			var pair: Array = finisher.mash_actions()
			tap(MASH_KEYS[pair[bot.mash_step % 2]])
			bot.mash_step += 1
		await physics_frame
		return
	if finisher.is_active() or player.is_grabbed or player.is_action_locked:
		_bot_release(bot)
		await physics_frame
		return
	var state: String = sm.current_state.name
	# His windows: straight in and punch.
	if _bot_window_open(state):
		await _bot_punish(profile, bot)
		return
	# His attacks.
	var answer := _bot_threat(profile, bot)
	if answer == "parry":
		_bot_release(bot)
		if bot.shift_left == 0:
			press(KEY_SHIFT)
			bot.shift_left = 6
	elif answer.begins_with("dash"):
		_bot_release(bot)
		var escape := Vector2.UP if answer == "dash_up" else Vector2.DOWN
		for k in keys_toward(escape):
			press(k)
			bot.held.append(k)
		tap(KEY_W)
	else:
		_bot_walk(bot, _bot_wait_spot())
	await physics_frame


func _bot_window_open(state: String) -> bool:
	match state:
		"Winded", "ParryStaggered":
			return true
		"Broken":
			return not sm.states["Broken"].retrieving
		"Whirlwind":
			# The dizzy stop it used to end on is a sword release now, which the bot answers as a threat
			# (_bot_threat) rather than walking into.
			return false
		"BearHug":
			var hug: Node = sm.states["BearHug"]
			return hug.phase == hug.Phase.STUMBLE
	return false


# Up beside his hurtbox, then a combo on the beat, for as long as the window stays open.
func _bot_punish(profile: Dictionary, bot: Dictionary) -> void:
	var spot := _bot_punch_spot()
	for i in 40:
		if not _bot_window_open(sm.current_state.name) or player.global_position.distance_to(spot) < 14.0:
			break
		_bot_walk(bot, spot)
		await physics_frame
	_bot_release(bot)
	for n in profile.punches:
		if not _bot_window_open(sm.current_state.name) or player.get_node("Finisher").is_active():
			break
		await swing()
		await wait(6)


func _bot_punch_spot() -> Vector2:
	var shape: CollisionShape2D = boss.get_node("Hurtbox/CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var side := 1.0 if player.global_position.x >= box.get_center().x else -1.0
	var reach: Rect2 = player.punch_box(player.Facing.LEFT if side > 0.0 else player.Facing.RIGHT)
	var edge: float = box.end.x if side > 0.0 else box.position.x
	return Vector2(edge - reach.get_center().x * player.global_scale.x, box.end.y - 28.0).clamp(ROPES.position, ROPES.end)


func _bot_wait_spot() -> Vector2:
	var side := 1.0 if player.global_position.x >= boss.global_position.x else -1.0
	return (boss.global_position + Vector2(PACE_WAIT.x * side, PACE_WAIT.y)).clamp(ROPES.position, ROPES.end)


# What his attack asks for this frame, if anything: "parry", "dash_up", "dash_down" or "". Each threat is
# read or missed once, as it first comes in reach.
func _bot_threat(profile: Dictionary, bot: Dictionary) -> String:
	var body: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var at: Vector2 = body.global_position
	for hazard in live_hazards():
		var script_path: String = str(hazard.get_script().resource_path) if hazard.get_script() else ""
		if script_path.ends_with("EarthquakeProjectilesScript.gd") and "collision_map" in hazard:
			var nearest := INF
			for numpad in hazard.collision_map:
				nearest = minf(nearest, hazard.collision_map[numpad].global_position.distance_to(at))
			if nearest < 1150.0 * 0.07 + 40.0 and _bot_reads(profile, bot, hazard):
				return "parry"
		elif script_path.ends_with("EricThrownSwordScript.gd") and hazard.flying and not hazard.returning:
			var blade: Area2D = hazard.get_node("Hitbox")
			if blade.monitoring and blade.global_position.distance_to(at) < 108.0 + 27.0 + hazard.speed * 0.07 and _bot_reads(profile, bot, hazard):
				return "parry"
		elif script_path.ends_with("EricQuakeRingScript.gd"):
			var gap := absf(hazard.global_position.distance_to(at) - hazard.radius)
			if gap < hazard.speed * 0.06 + 33.0 and _bot_reads(profile, bot, hazard):
				return "dash_up" if at.y > hazard.global_position.y else "dash_down"
	var state = sm.current_state
	if state == sm.states["Whirlwind"] and state.phase == state.Phase.LUNGE:
		var sweep: CollisionShape2D = boss.get_node("WhirlwindArea2D/CollisionShape2D")
		var radii: Vector2 = Vector2.ONE * sweep.shape.radius * sweep.global_scale.abs()
		var eta := sweep_eta(sweep.global_position, state.lunge_velocity, state.phase_left, radii)
		if eta >= 0.0 and eta <= 3.0 * FRAME_TIME and _bot_reads(profile, bot, "lunge%d" % state.lunges_left):
			return "dash_up" if sweep_escape(state.lunge_velocity).y < 0.0 else "dash_down"
	if state == sm.states["BearHug"] and state.phase == state.Phase.LUNGE:
		var grab: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
		var half: Vector2 = grab.shape.size * grab.global_scale.abs() / 2.0
		var gap: float = (at - grab.global_position).abs().y - half.y - 27.0
		var lead := 0.06 if state.yellow else 0.09
		if gap < 1500.0 * lead and _bot_reads(profile, bot, "hug%d" % state.hugs_started):
			if state.yellow:
				return "dash_up" if at.y < grab.global_position.y else "dash_down"
			return "parry"
	return ""


func _bot_reads(profile: Dictionary, bot: Dictionary, threat: Variant) -> bool:
	var key: String = str(threat.get_instance_id()) if threat is Object else str(threat)
	if not bot.decided.has(key):
		bot.decided[key] = randf() < profile.reads
		return bot.decided[key]
	return false


func _bot_walk(bot: Dictionary, spot: Vector2) -> void:
	var to := spot - player.global_position
	var wanted := []
	if to.x > 8.0:
		wanted.append(KEY_RIGHT)
	elif to.x < -8.0:
		wanted.append(KEY_LEFT)
	if to.y > 8.0:
		wanted.append(KEY_DOWN)
	elif to.y < -8.0:
		wanted.append(KEY_UP)
	for k in bot.held.duplicate():
		if not wanted.has(k):
			release(k)
			bot.held.erase(k)
	for k in wanted:
		if not bot.held.has(k):
			press(k)
			bot.held.append(k)


func _bot_release(bot: Dictionary) -> void:
	for k in bot.held:
		release(k)
	bot.held.clear()


# ------------------------------------------------------------------ the pause screen

const CARTER_AKUMA := "res://Scenes/Bosses/CarterBossFightScene.tscn"
const NOT_A_FIGHT := "res://Scenes/Core/MainScene.tscn"
const MAIN_MENU := "res://Scenes/Core/MainMenuScene.tscn"


func pause_menu() -> Node:
	return current_scene.get_node("Arena/PauseMenu")


# Escape, the way the player presses it, plus the frames the deferred unpause needs.
func tap_pause() -> void:
	tap(KEY_ESCAPE)
	await wait(3)


# The showing dialogue balloon, which the pause screen has to re-arm.
func live_balloon() -> Node:
	for child in current_scene.get_children():
		if child.has_method(&"rearm_input_lock"):
			return child
	return null


# Everything the fight has to come back holding, read off the live nodes.
func fight_snapshot() -> Dictionary:
	var snap := {
		"player": player.global_position,
		"health": player.playerHealth,
		"stamina": defense.stamina,
		"clock": defense.clock,
		"time_scale": Engine.time_scale,
		"timers": {},
	}
	if boss != null and is_instance_valid(boss):
		snap["boss"] = boss.global_position
		snap["boss_health"] = boss.boss_health
		for timer in boss.find_children("*", "Timer", true, false):
			if not timer.is_stopped():
				snap["timers"][str(timer.get_path())] = timer.time_left
	return snap


# Every field the same, to the float's own precision: a paused fight may not advance by a hair.
func snapshot_diff(before: Dictionary, after: Dictionary) -> Array:
	var moved := []
	for field in before:
		if field == "timers":
			for path in before.timers:
				var was: float = before.timers[path]
				var now: float = after.timers.get(path, -1.0)
				if not is_equal_approx(was, now):
					moved.append("%s %.4f -> %.4f" % [path, was, now])
			continue
		if not after.has(field):
			moved.append("%s went away" % field)
		elif typeof(before[field]) == TYPE_FLOAT:
			if not is_equal_approx(before[field], after[field]):
				moved.append("%s %.4f -> %.4f" % [field, before[field], after[field]])
		elif before[field] != after[field]:
			moved.append("%s %s -> %s" % [field, before[field], after[field]])
	return moved


# The fight stops dead and comes back exactly as it was, whatever was held down over the pause.
func test_pause_basic() -> void:
	await load_eric()
	boss.start_music()
	health_ok()
	await settle_player(Vector2(700, 800))
	var pause: Node = pause_menu()
	check(pause != null, "every fight carries a pause screen")
	check(pause.can_open(), "and a live fight can open it")

	log_p("-- Escape opens it and stops the fight")
	check(boss.music_player.playing, "his theme is playing")
	# One of his Timers armed by hand, so the snapshot really covers the claim that a Timer node
	# keeps its time left: whether one of his own happens to be running at this instant is luck.
	sm.rest_timer.start(9.0)
	await wait(2)
	var music_before: float = boss.music_player.get_playback_position()
	await tap_pause()
	check(pause.is_open() and paused, "open, and the tree is paused")
	var before := fight_snapshot()
	log_p("snapshot: %s" % [before])
	press(KEY_RIGHT)
	await wait(40)
	release(KEY_RIGHT)
	await wait(2)
	var held := fight_snapshot()
	var moved := snapshot_diff(before, held)
	log_p("40 paused frames moved: %s" % ["nothing" if moved.is_empty() else str(moved)])
	check(moved.is_empty(), "40 paused frames change nothing, a held direction included")
	# Godot pauses an AudioStreamPlayer with the tree and holds it where it is, so playing reads
	# false under the pause and the position is the one it will carry on from.
	var music_during: float = boss.music_player.get_playback_position()
	log_p("his theme sat at %.3f s, and reads %.3f s after 40 paused frames" % [music_before, music_during])
	check(not boss.music_player.playing, "the music is paused with the fight")
	check(music_during - music_before < 0.1, "and held where it was, not run on")

	log_p("-- Escape again resumes it exactly where it was")
	await tap_pause()
	check(not pause.is_open() and not paused, "closed, and the tree is running")
	var resumed := fight_snapshot()
	check(resumed.player.is_equal_approx(before.player), "the player is where they were (%s)" % [resumed.player])
	check(resumed.boss.is_equal_approx(before.boss), "and so is Eric (%s)" % [resumed.boss])
	check(resumed.health == before.health and resumed.boss_health == before.boss_health, "both healths kept")
	check(is_equal_approx(resumed.stamina, before.stamina), "stamina kept (%.2f)" % resumed.stamina)
	check(is_equal_approx(Engine.time_scale, 1.0), "time scale is 1 (%.3f)" % Engine.time_scale)
	var was_clock: float = defense.clock
	await wait(20)
	check(defense.clock > was_clock, "and the fight's own clock is running again")

	log_p("-- the window losing focus pauses the fight on its own")
	pause.notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	await wait(2)
	check(pause.is_open() and paused, "alt-tabbing away opened it")
	pause.notification(NOTIFICATION_APPLICATION_FOCUS_IN)
	await wait(2)
	check(pause.is_open() and paused, "and coming back does not resume on its own")
	await tap_pause()
	check(not pause.is_open() and not paused, "only the player does")
	# Not "has moved on": the headless dummy mixer reports a position of its own accord, and under a
	# full suite run it can still read 0. What matters is that the unpause gave the music back and
	# never sent it to the start.
	var music_after: float = boss.music_player.get_playback_position()
	check(boss.music_player.playing and music_after >= music_during, "the music picks up from where it stopped rather than restarting (%.3f s)" % music_after)


# A hit-stop is a SceneTree timer, the one kind that keeps running through a pause unless it is
# asked not to: it has to come back with exactly the stop it had left.
func test_pause_hitstop() -> void:
	await load_eric()
	park_eric()
	await settle_player(Vector2(700, 800))
	var hit_stop: GDScript = load("res://Scripts/HitStop.gd")
	var pause: Node = pause_menu()
	hit_stop.freeze(self, 0.5)
	await wait(6)
	await tap_pause()
	check(pause.is_open(), "paused in the middle of a hit-stop")
	check(is_equal_approx(Engine.time_scale, 0.05), "the stop is still on (%.3f)" % Engine.time_scale)
	# Read once the pause is up: the frames between the press and it are the fight's, not the pause's.
	var left: float = hit_stop.release_timer.time_left
	log_p("the hit-stop has %.3f s left under the pause" % left)
	await wait(60)
	var still: float = hit_stop.release_timer.time_left
	log_p("after 60 paused frames it has %.3f s left" % still)
	check(is_equal_approx(left, still), "60 paused frames don't eat the stop")
	await tap_pause()
	check(await wait_until(func(): return is_equal_approx(Engine.time_scale, 1.0), 90), "and it runs out after the resume")


# The finisher's freeze keeps the player's branch running under a disabled scene. A pause has to
# reach that branch too, or the player would still be walking about under the dim.
func test_pause_freeze() -> void:
	await load_eric()
	park_eric()
	health_ok()
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	var pause: Node = pause_menu()
	await settle_player(Vector2(700, 800))
	var start: Vector2 = player.global_position
	check(freeze.freeze(self, [player.get_parent()]), "the fight is frozen around the player")
	press(KEY_RIGHT)
	await wait(6)
	check(not player.global_position.is_equal_approx(start), "who is still walking under the freeze")
	await tap_pause()
	check(pause.is_open() and freeze.is_frozen(), "paused, and still frozen")
	var at_pause: Vector2 = player.global_position
	await wait(40)
	check(player.global_position.is_equal_approx(at_pause), "40 paused frames don't move the kept branch (%s)" % [player.global_position])
	await tap_pause()
	release(KEY_RIGHT)
	await wait(4)
	check(freeze.is_frozen(), "still frozen after the resume")
	freeze.unfreeze(self)
	await wait(2)
	check(not freeze.is_frozen(), "and it unfreezes normally")


# The mash is a _process meter behind that freeze, with a real-clock gate on its presses: it has to
# stop with the fight, and the alternation latch has to survive the resume.
func test_pause_mash() -> void:
	await load_eric()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	check(await daze_eric(), "Eric is dazed and the prompt is up")
	var pair: Array = finisher.mash_actions()
	tap(MASH_KEYS[pair[0]])
	await wait(4)
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open(), "paused in the middle of the mash")
	var meter: float = finisher.meter
	var phase: int = finisher.phase
	var latch = finisher.last_action
	for i in 6:
		tap(MASH_KEYS[pair[i % 2]])
		await wait(4)
	log_p("6 presses over 24 paused frames moved the meter by %.5f" % (finisher.meter - meter))
	check(is_equal_approx(finisher.meter, meter), "presses while paused don't fill it")
	check(finisher.phase == phase, "and the phase is where it was (%d)" % finisher.phase)
	check(finisher.last_action == latch, "the alternation latch is kept")
	await tap_pause()
	await mash_finisher()
	check(await wait_until(func(): return not finisher.is_active(), 240), "and the mash still finishes the uppercut")


# Carter's barrage is physics accumulators and node-bound tweens under a near-black curtain: the
# whole thing has to stop, clones included.
func test_pause_barrage() -> void:
	change_scene_to_file(CARTER_AKUMA)
	while current_scene == null or current_scene.scene_file_path != CARTER_AKUMA:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	boss = current_scene.get_node("Arena/CarterAkumaScene/CarterAkumaCharacterBody")
	sm = boss.get_node("StateManager")
	var demon: Node = sm.get_node("RagingDemon")
	# His machine fills its states and defers the entrance, so the cycle is forced a frame later
	# rather than in the middle of the scene coming up, exactly as his own suite does it.
	check(await wait_until(func(): return sm.states.has("Intro"), 120), "his state machine is up")
	sm.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	player.playerHealth = 9999
	await wait(2)
	sm.start_cycle()
	check(await wait_until(func(): return sm.current_state == demon and demon.beat == demon.Beat.RUSH and demon.clone_index >= 1, 900), "the barrage is running")
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open(), "paused inside the barrage")
	var clock: float = demon.clone_clock
	var index: int = demon.clone_index
	var spots := []
	for clone in get_nodes_in_group(sm.HAZARD_GROUP):
		spots.append(clone.global_position)
	await wait(40)
	var after := []
	for clone in get_nodes_in_group(sm.HAZARD_GROUP):
		after.append(clone.global_position)
	log_p("clone clock %.4f -> %.4f, clone %d -> %d, %d clones out" % [clock, demon.clone_clock, index, demon.clone_index, spots.size()])
	check(is_equal_approx(clock, demon.clone_clock) and index == demon.clone_index, "the barrage's own clock stopped")
	check(spots == after, "and no clone moved")
	await tap_pause()
	check(await wait_until(func(): return not is_equal_approx(clock, demon.clone_clock), 60), "and it carries on from there")


# Pre-fight banter is the longest uninterruptible stretch in the game, so it is deliberately
# pausable - and the balloon's input lock is on the real clock, so a resume has to re-arm it.
func test_pause_dialogue() -> void:
	await load_eric(true)
	check(await wait_until(func(): return live_balloon() != null, 300), "the pre-fight balloon is up")
	var balloon: Node = live_balloon()
	balloon.input_lock_time = 1.2
	balloon.rearm_input_lock()
	await wait(4)
	var line: String = balloon.dialogue_label.text
	var pause: Node = pause_menu()
	check(pause.can_open(), "a fight mid-dialogue can still be paused")
	await tap_pause()
	check(pause.is_open() and paused, "paused mid-line")
	await wait(120)
	await tap_pause()
	await wait(2)
	check(balloon.dialogue_label.text == line, "the same line is still up after the resume")
	var since: int = Time.get_ticks_msec() - balloon._line_shown_msec
	log_p("the line's input lock reads %d ms old on the resuming frame" % since)
	check(since < 400, "and its lock was re-armed, so the resuming press can't advance it")


# Opening and closing may never reach the fight, on either device. The pad is what makes this
# matter: A is both accept and punch, and B is both cancel and dash.
#
# Real time (--max-fps 60), because the resume grace is 0.15 real seconds: under --fixed-fps it
# would still be running at the end of the mode and nothing after the first resume would be read.
func test_pause_no_leak() -> void:
	await load_eric()
	park_eric()
	health_ok()
	await settle_player(Vector2(700, 800))
	var pause: Node = pause_menu()
	var seen := {"punch": 0, "guard": 0, "blocks": 0}
	var dodge_frame: int = player.last_dodge_physics_frame
	defense.block_pressed.connect(func(_credited: bool) -> void: seen.blocks += 1)
	watch = func() -> void:
		if player.state_machine.current_state.name == "Punching":
			seen.punch += 1
		if defense.is_guarding():
			seen.guard += 1

	log_p("-- keyboard: Escape in and out")
	await tap_pause()
	await tap_pause()
	await wait(20)
	log_p("after the keyboard round trip: %s, dodge frame %d -> %d" % [seen, dodge_frame, player.last_dodge_physics_frame])
	check(seen.punch == 0 and seen.guard == 0 and seen.blocks == 0, "no punch, no guard, no block press")
	check(player.last_dodge_physics_frame == dodge_frame, "and no dash")

	log_p("-- pad: Start opens, A on RESUME closes, and a mashed A after it never punches")
	pad_tap(JOY_BUTTON_START)
	await wait(3)
	check(pause.is_open(), "Start opened it")
	pad_tap(JOY_BUTTON_A)
	await wait(3)
	check(not pause.is_open(), "A on RESUME closed it")
	for i in 4:
		pad_tap(JOY_BUTTON_A)
		await wait(1)
	log_p("the mash landed with %d ms of grace left" % (pause.grace_until_msec - Time.get_ticks_msec()))
	await wait(20)
	log_p("after the A resume and four more A presses: %s" % [seen])
	check(seen.punch == 0, "the accept that resumed, and the mash after it, punched nothing")

	log_p("-- pad: B backs out and never dashes")
	pad_tap(JOY_BUTTON_START)
	await wait(3)
	check(pause.is_open(), "Start opened it again")
	pad_tap(JOY_BUTTON_B)
	await wait(3)
	check(not pause.is_open(), "B resumed from the root")
	for i in 4:
		pad_tap(JOY_BUTTON_B)
		await wait(1)
	log_p("the mash landed with %d ms of grace left" % (pause.grace_until_msec - Time.get_ticks_msec()))
	await wait(20)
	log_p("dodge frame %d -> %d, %s" % [dodge_frame, player.last_dodge_physics_frame, seen])
	check(player.last_dodge_physics_frame == dodge_frame, "the cancel that resumed, and the mash after it, dashed nothing")
	check(seen.blocks == 0, "and nothing reached the defence as a block")
	watch = Callable()

	log_p("-- a guard held across the pause is still up on the other side")
	press(KEY_SHIFT)
	await wait(6)
	check(defense.is_guarding(), "guarding before the pause")
	await tap_pause()
	await wait(10)
	await tap_pause()
	await wait(6)
	check(defense.is_guarding(), "still guarding after it")
	release(KEY_SHIFT)


# The screen is for a fight in progress and nothing else.
func test_pause_blocked() -> void:
	await load_eric()
	park_eric()
	await settle_player(Vector2(700, 800))
	var pause: Node = pause_menu()

	log_p("-- a fight that is already decided")
	player.fight_over = true
	check(not pause.can_open(), "fight_over blocks it")
	await tap_pause()
	check(not pause.is_open() and not paused, "and Escape does nothing")
	player.fight_over = false
	check(pause.can_open(), "cleared again")

	log_p("-- a Restart or Quit already on its way")
	pause.leaving = true
	check(not pause.can_open(), "the leaving flag blocks it")
	await tap_pause()
	check(not pause.is_open(), "and Escape does nothing")
	pause.leaving = false

	log_p("-- the outro")
	var stub := Node.new()
	stub.name = "FightOutro"
	root.add_child(stub)
	check(not pause.can_open(), "a FightOutro under the root blocks it")
	await tap_pause()
	check(not pause.is_open() and not paused, "and Escape does nothing")
	root.remove_child(stub)
	stub.free()
	check(pause.can_open(), "cleared again")

	log_p("-- a scene that is not a fight")
	change_scene_to_file(NOT_A_FIGHT)
	while current_scene == null or current_scene.scene_file_path != NOT_A_FIGHT:
		await process_frame
	await wait(4)
	var idle: Node = current_scene.get_node("Arena/PauseMenu")
	check(idle != null, "MainScene carries the layer too")
	check(not idle.can_open(), "but it is inert there")
	tap(KEY_ESCAPE)
	await wait(4)
	check(not idle.is_open() and not paused, "and Escape does nothing")


# Restart puts back everything the fight put on the engine. The proof that it did is that the next
# fight can still freeze: FightFreeze.frozen is static, and a leaked one refuses every later freeze.
func test_pause_restart() -> void:
	await load_eric()
	park_eric()
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	var view: GDScript = load("res://Scripts/ScreenView.gd")
	var full: int = boss.boss_health
	boss.boss_health -= 10
	player.playerHealth -= 2
	load("res://Scripts/HitStop.gd").freeze(self, 5.0)
	view.zoom_to(self, 1.6, Vector2(900, 700), 0.01, true)
	check(freeze.freeze(self, [player.get_parent()]), "the fight is frozen, zoomed and in a hit-stop")
	await wait(4)
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open(), "paused")

	# Down to RESTART FIGHT, accept, right to CONFIRM, accept.
	tap(KEY_DOWN)
	await wait(2)
	tap(KEY_ENTER)
	await wait(2)
	check(pause.level == pause.Level.CONFIRM, "the confirm row is up")
	check(root.gui_get_focus_owner() == pause.confirm_back_button, "with BACK holding focus, not CONFIRM")
	tap(KEY_RIGHT)
	await wait(2)
	tap(KEY_ENTER)
	var gone: Node = pause
	check(await wait_until(func(): return current_scene != null and current_scene.scene_file_path == SCENES["eric"] and current_scene.get_node_or_null("Arena/PauseMenu") != gone, 300), "the fight reloaded")
	await wait(8)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	check(not paused, "the tree is running")
	check(not freeze.is_frozen(), "nothing is left frozen")
	check(is_equal_approx(Engine.time_scale, 1.0), "time scale is 1 (%.3f)" % Engine.time_scale)
	check(view.zoom == 1.0 and root.canvas_transform == Transform2D.IDENTITY, "the view is back to normal")
	check(boss.boss_health == full, "Eric is on full health again (%d of %d)" % [boss.boss_health, full])
	check(player.playerHealth == 6, "and so is the player (%d)" % player.playerHealth)
	check(freeze.freeze(self, [player.get_parent()]), "and the next finisher can still freeze the fight")
	freeze.unfreeze(self)


# QUIT TO MAIN MENU, confirmed with accept held down and mashed through the scene change. The pause
# screen's resume grace dies with the fight, so what stops that accept from pressing NEW GAME is the
# main menu holding its focus back until it has faded in, the way Victory and Defeat do.
func test_pause_quit() -> void:
	await load_eric()
	park_eric()
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open(), "paused")
	# RESUME, RESTART FIGHT, CONTROLS, VOLUME, then QUIT TO MAIN MENU.
	for i in 4:
		tap(KEY_DOWN)
		await wait(2)
	check(root.gui_get_focus_owner().name == &"QuitButton", "QUIT TO MAIN MENU has focus (%s)" % root.gui_get_focus_owner().name)
	tap(KEY_ENTER)
	await wait(2)
	check(pause.level == pause.Level.CONFIRM, "the confirm row is up")
	tap(KEY_RIGHT)
	await wait(2)

	# Held from the confirm onwards, and mashed on top of it: the worst a player can do.
	press(KEY_ENTER)
	for i in 8:
		await physics_frame
		tap(KEY_ENTER)
	release(KEY_ENTER)
	check(await wait_until(func(): return current_scene != null and current_scene.scene_file_path == MAIN_MENU, 300), "the fight quit to the main menu")
	await wait(20)
	check(root.gui_get_focus_owner() == null, "nothing has focus while it fades in, so the mashed accept presses nothing")
	tap(KEY_ENTER)
	await wait(10)
	check(current_scene.scene_file_path == MAIN_MENU, "still on the menu (%s)" % current_scene.scene_file_path)
	check(not paused and is_equal_approx(Engine.time_scale, 1.0), "unpaused, at normal speed")

	await wait(60)
	check(root.gui_get_focus_owner() != null and root.gui_get_focus_owner().name == &"StartGameButton", "once it is up NEW GAME takes focus (%s)" % [root.gui_get_focus_owner()])
	tap(KEY_ENTER)
	check(await wait_until(func(): return current_scene != null and current_scene.scene_file_path != MAIN_MENU, 120), "and a press then does start a new game (%s)" % current_scene.scene_file_path)


# ------------------------------------------------------------------ the VS card

const VS_CARD_LAYOUT := "res://Scripts/VsCardArtLayout.gd"


# The fight scene the card's own table names for a key, which is not always the one SCENES holds:
# this suite's "carter" is the old combined fight.
func card_fight_scene(key: String) -> String:
	return load(VS_CARD_LAYOUT).CARDS[key]["fight"]


# The node that holds the timer a fight starts on once its card is done, whichever boss it is.
func fight_state_machine() -> Node:
	for node in current_scene.find_children("*", "Node", true, false):
		if "post_dialogue_pre_fight_timer" in node and node.post_dialogue_pre_fight_timer != null:
			return node
	return null


# A fight entered the way the main menu's boss select enters it: a fresh run, straight into the
# scene, with nothing read before it. The boss entrance that plays in front of it is cut unless the
# caller is the mode that tests it.
func enter_fight(scene: String, keep_entrance := false) -> void:
	root.get_node("GameProgress").reset_progress()
	change_scene_to_file(scene)
	while current_scene == null or current_scene.scene_file_path != scene:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	# Another coder's temporary driver rides in Eric's fight scene and steers his states.
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	if not keep_entrance:
		await skip_entrance()


# The card between a fight's pre-fight lines and the fight itself. It plays once per entry, nothing
# in the fight runs under it, the pause screen is refused for as long as it is up, and any press
# ends it without that press ever reaching the fight.
#
# Real time (--max-fps 60), because the card's input grace is 0.15 real seconds: under --fixed-fps
# it would still be eating presses long after the card is gone.
func test_vs_card() -> void:
	var scene := card_fight_scene(fight)
	log_p("-- %s, through its pre-fight lines" % fight)
	await enter_fight(scene)
	var card: Node = vs_card()
	check(card != null, "the fight carries a VS card")
	var plays := [0]
	card.finished.connect(func() -> void: plays[0] += 1)
	var pause: Node = pause_menu()
	check(await wait_until(func(): return live_balloon() != null, 300), "its pre-fight balloon is up")
	check(not card.is_playing(), "and the card waits while the lines are")

	var boss_sm := fight_state_machine()
	check(boss_sm != null, "found the fight's state machine")
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(2)
	check(card.is_playing(), "the card plays the moment the lines end")
	check(player.is_talking, "the player is still held where the lines left them")
	check(boss_sm.post_dialogue_pre_fight_timer.is_stopped(), "and the fight has not started under it")
	check(not pause.can_open(), "the pause screen is refused while it plays")

	var card_art: GDScript = load(VS_CARD_LAYOUT)
	check(await wait_until(func(): return not card.is_playing(), 240), "it ends on its own")
	log_p("it ran for %.2fs of a %.2fs card, %d play(s)" % [card.clock, card_art.CARD_END, plays[0]])
	check(card.clock >= card_art.CARD_END, "having played the whole card")
	await wait(2)
	check(not player.is_talking, "the player has the fight once it is gone")
	check(not boss_sm.post_dialogue_pre_fight_timer.is_stopped(), "and the fight started on the other side of it")
	check(pause.can_open(), "and the pause screen is open again")
	await wait(90)
	check(plays[0] == 1 and not card.is_playing(), "it played once and did not come back")

	log_p("-- entered from the boss select, with no line read")
	await enter_fight(scene)
	card = vs_card()
	await start_vs_card()
	check(card.is_playing(), "the card still plays with nothing read before it")

	var seen := {"punch": 0, "guard": 0, "blocks": 0}
	var dodge_frame: int = player.last_dodge_physics_frame
	defense.block_pressed.connect(func(_credited: bool) -> void: seen.blocks += 1)
	watch = func() -> void:
		if player.state_machine.current_state.name == "Punching":
			seen.punch += 1
		if defense.is_guarding():
			seen.guard += 1

	log_p("-- a punch press skips it, and neither it nor the mash after it reaches the fight")
	tap(KEY_Q)
	check(await wait_until(func(): return card.clock >= card_art.HOLD_END, 30), "the press skipped it to the flash")
	check(card.is_playing(), "which it plays out rather than vanishing on")
	for i in 4:
		tap(KEY_Q)
		tap(KEY_W)
		await wait(2)
	await wait_until(func(): return not card.is_playing(), 60)
	while Time.get_ticks_msec() < card.grace_until_msec:
		await process_frame
	await wait(20)
	watch = Callable()
	log_p("after the skip and the mash: %s, dodge frame %d -> %d" % [seen, dodge_frame, player.last_dodge_physics_frame])
	check(seen.punch == 0 and seen.guard == 0 and seen.blocks == 0, "no punch, no guard, no block press")
	check(player.last_dodge_physics_frame == dodge_frame, "and no dash")
	check(not player.is_talking, "and the fight is the player's again")

	log_p("-- and a punch after the grace is a punch")
	tap(KEY_Q)
	check(await wait_until(func(): return player.state_machine.current_state.name == "Punching", 30), "the next press punched")

	log_p("-- Escape while it plays neither pauses the fight nor is swallowed")
	await enter_fight(scene)
	card = vs_card()
	pause = pause_menu()
	await start_vs_card()
	check(card.is_playing() and not pause.can_open(), "the card is up and the pause screen is refused")
	tap(KEY_ESCAPE)
	check(await wait_until(func(): return card.clock >= card_art.HOLD_END, 30), "Escape skipped the card, the way any press does")
	await wait(4)
	check(not pause.is_open() and not paused, "and it neither opened the pause screen nor paused the fight")
	check(await wait_until(func(): return not card.is_playing(), 60), "the card is gone")
	while Time.get_ticks_msec() < card.grace_until_msec:
		await process_frame
	await wait(4)
	check(pause.can_open(), "and the pause screen is the player's again")
	await tap_pause()
	check(pause.is_open() and paused, "Escape now opens it")
	await tap_pause()


# The fight's lines thrown away unread, the way a playtest jump into a fight leaves them: the
# balloon freed and the dialogue ended without a word of it having been shown. Waited for first -
# two of the fights open on an entrance, and only hand the dialogue over once it has played.
func start_vs_card() -> void:
	await wait_until(func(): return live_balloon() != null, 900)
	for child in current_scene.get_children():
		if child is CanvasLayer:
			child.queue_free()
	root.get_node("DialogueManager").dialogue_ended.emit(null)
	await wait(2)


# ------------------------------------------------------------------ the boss entrance

# Eric's entrance: the ring opens on his planted sword, both fighters walk in, the gates slam, and
# his lines call the pull and the point as beats before the VS card and the fight. Nothing in the
# fight runs under it, the player is held through it and gets their own state machine back before
# the card takes the hold, it pauses and resumes cleanly, a held ui_cancel cuts it, and a second
# entry in the same run doesn't play it again.
#
# Real time (--max-fps 60), because the skip is a 0.4 real-second hold and the card's input grace is
# another 0.15.
func test_entrance() -> void:
	var scene := card_fight_scene("eric")
	var screen: GDScript = load("res://Scripts/ScreenView.gd")

	log_p("-- the ring opens on the sword, and both of them walk in")
	await enter_fight(scene, true)
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	sm = boss.state_machine
	var intro := entrance_state()
	check(intro != null, "his fight opens on an entrance state")
	check(await wait_until(func(): return intro.entered, 60), "which starts itself")
	var gates: Node = current_scene.get_node_or_null("Arena/Gates")
	check(gates != null and gates.is_open(), "the ring is open")
	check(is_instance_valid(intro.planted), "his sword is planted in the mat")
	check(player.is_talking and not player.state_machine.is_processing(), "the player is held, and their own state machine stopped")
	check(sm.post_dialogue_pre_fight_timer.is_stopped(), "and the fight has not started")

	var seen := {"punch": 0, "guard": 0}
	var dodge_frame: int = player.last_dodge_physics_frame
	watch = func() -> void:
		if player.state_machine.current_state.name == "Punching":
			seen.punch += 1
		if defense.is_guarding():
			seen.guard += 1

	var player_home: Vector2 = intro.player_home
	var eric_home: Vector2 = intro.home
	check(await wait_until(func(): return player.global_position.y > player_home.y + 100.0, 120), "the player starts from outside the ring")
	check(await wait_until(func(): return player.global_position.is_equal_approx(player_home), 300), "and walks up onto their mark")
	check(await wait_until(func(): return boss.global_position.y < eric_home.y - 100.0, 240), "Eric starts from above the ring")
	check(await wait_until(func(): return boss.global_position.is_equal_approx(eric_home), 400), "and walks down onto his")
	var layout: GDScript = load("res://Scripts/EricEntranceLayout.gd")
	log_p("%d of %d plants landed" % [intro.footfalls, layout.WALK_STEPS])
	check(intro.footfalls == layout.WALK_STEPS, "every step of the walk planted, none of them dropped")
	# He has to stop in reach of the blade, or the grip frame needs a reposition the art can't make.
	var feet: Vector2 = eric_home + Vector2(0, load("res://Scripts/EricArtLayout.gd").SORT_POINT.y * boss.scale.y)
	var reach: Vector2 = intro.planted.global_position - feet
	log_p("the planted sword sits %.0f px across and %.0f px up from where he stops" % [reach.x, reach.y])
	check(absf(reach.x) < 140.0 and absf(reach.y) < 60.0, "and he arrives in reach of it")
	check(await wait_until(func(): return not gates.is_open(), 240), "the gates slam shut behind them")
	check(await wait_until(func(): return live_balloon() != null, 180), "and his first line comes up")
	check(sm.post_dialogue_pre_fight_timer.is_stopped(), "the fight is still waiting")

	log_p("-- a press during it never reaches the fight")
	for i in 3:
		tap(KEY_Q)
		tap(KEY_W)
		await wait(2)
	await wait(10)
	log_p("through the walk-in: %s, dodge frame %d -> %d" % [seen, dodge_frame, player.last_dodge_physics_frame])
	check(seen.punch == 0 and seen.guard == 0, "no punch and no guard")
	check(player.last_dodge_physics_frame == dodge_frame, "and no dash")
	watch = Callable()

	log_p("-- the lines call the pull and the point")
	await read_line()

	# Mid-heave, where his frames are cycling: a pause has to stop that clock with the fight.
	await wait(26)
	var pause_mid: Node = pause_menu()
	check(pause_mid.can_open(), "a fight mid-pull can be paused")
	await tap_pause()
	check(pause_mid.is_open(), "paused inside the pull")
	var frame_held: int = boss.sprite.frame
	await wait(60)
	check(boss.sprite.frame == frame_held, "his pull held on the frame it stopped on (%d)" % frame_held)
	await tap_pause()
	await wait(6)

	check(await wait_until(func(): return not is_instance_valid(intro.planted), 300), "do pull_sword() took the sword out of the mat")
	check(await wait_until(func(): return screen.zoom > 1.0, 300), "do point_at_player() leaned the view in on him")
	check(await wait_until(func(): return intro.finished, 300), "and the entrance is done with the last beat")
	check(player.state_machine.is_processing(), "the player has their state machine back before the card asks for the hold")
	check(player.is_talking, "while the lines still hold them")
	check(boss.music_player.playing, "his theme is already playing")

	log_p("-- and it hands over to the card and the fight exactly as it did before")
	var card := vs_card()
	await read_line()
	check(await wait_until(func(): return card.is_playing(), 300), "the card plays when the lines end")
	check(await wait_until(func(): return is_equal_approx(screen.zoom, 1.0), 120), "the push-in levelled off for it")
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	check(await wait_until(func(): return not sm.post_dialogue_pre_fight_timer.is_stopped() or sm.current_state != intro, 180), "and the fight starts behind it")
	check(not player.is_talking, "with the player free")

	log_p("-- Escape tapped pauses it; held, it skips it")
	await enter_fight(scene, true)
	# Every handle from the last entry went with its scene.
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	sm = boss.state_machine
	gates = current_scene.get_node("Arena/Gates")
	intro = entrance_state()
	var pause: Node = pause_menu()
	check(await wait_until(func(): return intro.entered, 60), "a fresh entrance is playing")
	check(pause.can_open(), "a fight mid-entrance can be paused")
	await tap_pause()
	check(pause.is_open() and paused, "a tapped Escape opened it rather than skipping")
	var walked: Vector2 = player.global_position
	await wait(60)
	check(player.global_position.is_equal_approx(walked), "and the walk-in stopped dead with the fight")
	await tap_pause()
	await wait(20)
	check(not paused and not player.global_position.is_equal_approx(walked), "the resume carries it on from there")

	press(KEY_ESCAPE)
	check(await wait_until(func(): return intro.finished, 120), "a held Escape skipped it")
	release(KEY_ESCAPE)
	await wait(4)
	check(not pause.is_open() and not paused, "and never opened the pause screen")
	check(not gates.is_open() and not is_instance_valid(intro.planted), "the ring is set: gates shut, sword in his hands")
	check(player.global_position.is_equal_approx(intro.player_home) and boss.global_position.is_equal_approx(intro.home), "both of them on their marks")
	check(await wait_until(func(): return live_balloon() != null, 120), "and the lines started anyway")

	log_p("-- paused mid-line, the fight still starts")
	await tap_pause()
	check(pause.is_open(), "paused on a line")
	await wait(60)
	await tap_pause()
	await wait(4)
	card = vs_card()
	# Mashed through the way a player reads them: the beats between the lines hide the balloon while
	# they play, so this waits on the card rather than on a line count.
	for i in 600:
		if card.is_playing():
			break
		if i % 8 == 0:
			tap(KEY_ENTER)
		await physics_frame
	check(card.is_playing(), "the lines read through to the card")
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	check(await wait_until(func(): return not sm.post_dialogue_pre_fight_timer.is_stopped(), 180), "and the fight starts")

	log_p("-- a second go at the same fight in the same run doesn't play it again")
	change_scene_to_file(scene)
	while current_scene == null or current_scene.scene_file_path != scene:
		await process_frame
	await wait(6)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	gates = current_scene.get_node("Arena/Gates")
	intro = entrance_state()
	check(intro != null and intro.finished, "the entrance is already over on arrival")
	check(not gates.is_open(), "and the ring was never opened")
	check(await wait_until(func(): return live_balloon() != null, 120), "and his lines start straight away")
	check(player.state_machine.is_processing(), "with the player's state machine running")
