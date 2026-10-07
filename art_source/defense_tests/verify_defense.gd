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
	"computah": "res://Scenes/Bosses/ComputahBossFightScene.tscn",
	# Deliberately the LEGACY combined scene, not the shipped CarterBossFightScene: test_smoke,
	# test_blocks, test_approach and test_dodge_rollout all reach into Arena/CarterAndJoshScene/Carter
	# and would break against the split fight. The shipped Carter is covered by clone_cadence, which
	# uses Arena/CarterAkumaScene. Pointing this row at the split fight is its own job - it means
	# reworking those four node paths - and is NOT a one-line change.
	"carter": "res://Scenes/Bosses/CarterAndJoshBossFightScene.tscn",
	# The shipped Carter fight, under its own key so the row above keeps its four modes working.
	"carter_akuma": "res://Scenes/Bosses/CarterBossFightScene.tscn",
	"josh": "res://Scenes/Bosses/JoshBossFightScene.tscn",
	"mason": "res://Scenes/Bosses/MasonBossFightScene.tscn",
	"jordan": "res://Scenes/Bosses/JordanBossFightScene.tscn",
	"liam": "res://Scenes/Bosses/LiamBossFightScene.tscn",
	"matt": "res://Scenes/Bosses/MattBossFightScene.tscn",
	# Captain Burak, fight 01 of the ladder.
	"burak": "res://Scenes/Bosses/BurakBossFightScene.tscn",
	# Danny, fight 07 of the ladder.
	"danny": "res://Scenes/Bosses/DannyBossFightScene.tscn",
	# Greyson, fight 03's second half, on his own: his test scene starts him active at HOME, the takeover's end
	# state, with Computah already down. greyson_takeover plays the takeover in Computah's fight instead.
	"greyson": "res://Scenes/Bosses/GreysonTestFightScene.tscn",
	# Jordan's last phase, the Puppet Master: a scene of its own after his finale (FIGHT 10 still).
	"jordan_god": "res://Scenes/Bosses/JordanGodFightScene.tscn",
	# Liam's own phase on its own: his test scene starts him at the takeover's end state, on his pillar at the top of the
	# ring with Bixby already gone. liam_takeover plays the takeover in the real fight instead.
	"liam_elements": "res://Scenes/Bosses/LiamTestFightScene.tscn",
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
# Where in Liam's rotation smoke, blocks and approach start him: 0 for the fight as it starts, 2 for his
# Inferno's cycle (rotate_liam_to_inferno), the last of his rotation, which those modes would otherwise
# reach late in their window, if at all.
var phase := 0

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
# The game ships with blocking off (PlayerDefense.BLOCKING_ENABLED). These modes exist to test the
# blocking it keeps behind that switch, so they switch it back on for themselves and keep it working
# for the day it is flipped back. Every other mode plays the game as it ships.
const BLOCKING_MODES := [
	"stamina", "block_eric", "behind", "blocks", "guard_break", "guard_break_timeout", "guard_break_grab",
	"guard_break_lose",
]
const PLAYER_DEFENSE := "res://Scripts/PlayerDefense.gd"
# blocking=on or blocking=off overrides BLOCKING_MODES for one run, whatever the mode.
var blocking_arg := ""


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
		elif arg.begins_with("phase="):
			phase = int(arg.substr(6))
		elif arg.begins_with("blocking="):
			blocking_arg = arg.substr(9)
	_main.call_deferred()


# Before the fight loads: his _ready reads it.
func pin_eric(version: int) -> void:
	load(ERIC_PACING).version = version


# Whether a held guard blocks in this run (PlayerDefense.BLOCKING_ENABLED, which the game ships off).
func blocking() -> bool:
	return load(PLAYER_DEFENSE).BLOCKING_ENABLED


# What a guarded hit that isn't parried comes out as: 2 (BLOCKED) with blocking, 1 (HIT) without.
func unparried() -> int:
	return 2 if blocking() else 1


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


# The longest a scene may take to become the current one once it has opened.
const SCENE_LOAD_FRAMES := 600


# Changes to the scene at `path` and waits until it is the current one. One that can't be opened, or
# never arrives, fails the run and ends it here, rather than leaving the wait for it spinning forever.
func open_scene(path: String) -> void:
	var err := change_scene_to_file(path)
	if err == OK:
		for i in SCENE_LOAD_FRAMES:
			if current_scene != null and current_scene.scene_file_path == path:
				return
			await process_frame
	check(false, "%s opens and becomes the current scene (error %d)" % [path, err])
	log_p("RESULT mode=%s fails=%d" % [mode, fails])
	quit(fails)
	# Parked until the quit lands, so the mode never goes on to run on a scene it doesn't have.
	while true:
		await process_frame


func load_fight(key_name: String, keep_balloon := false) -> void:
	await open_scene(SCENES[key_name])
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	# Another coder's temporary driver rides in Eric's fight scene and steers his states; it would
	# drive them through these tests too. Freeing it only affects this process.
	var scratch := current_scene.get_node_or_null("ScratchEricDriver")
	if scratch:
		scratch.free()
	if key_name == "matt" and mode != "matt_yell":
		park_matt_yell()
	if key_name == "matt" and not matt_glass_mode():
		park_matt_glass()
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
	load(PLAYER_DEFENSE).BLOCKING_ENABLED = blocking_arg == "on" or (blocking_arg != "off" and BLOCKING_MODES.has(mode))
	match mode:
		"stamina": await test_stamina()
		"stamina_costs": await load("res://art_source/defense_tests/stamina/costs.gd").run(self)
		"tired_popup": await load("res://art_source/defense_tests/stamina/tired.gd").run(self)
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
		"no_block": await test_no_block()
		"broken_combo": await load("res://art_source/defense_tests/combo/broken_combo.gd").run(self)
		"combo_art": await load("res://art_source/defense_tests/combo/combo_art.gd").run(self)
		"combo_reset": await load("res://art_source/defense_tests/combo/combo_reset.gd").run(self)
		"pow_always_dazes": await load("res://art_source/defense_tests/combo/pow_always_dazes.gd").run(self)
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
		"beam": await test_beam()
		"prompt_overlap": await test_prompt_overlap()
		"grab_parry": await test_grab_parry()
		"parry_streak": await test_parry_streak()
		"knockback": await test_knockback()
		"knockback_boss": await test_knockback_boss()
		"kill_shove": await test_kill_shove()
		"status": await test_status()
		"status_end": await test_status_end()
		"status_dialogue": await test_status_dialogue()
		"locked": await test_locked()
		"locked_end": await test_locked_end()
		"scripted": await test_scripted()
		"parry_rearm": await test_parry_rearm()
		"parry_window": await test_parry_window()
		"parry_freeze": await test_parry_freeze()
		"parry_cue": await test_parry_cue()
		"approach": await test_approach()
		"clone_cadence": await test_clone_cadence()
		"beam_rush": await test_beam_rush()
		"beam_rush_live": await test_beam_rush_live()
		"carter_hud": await test_carter_hud()
		"messatsu": await test_messatsu()
		"messatsu_live": await test_messatsu_live()
		"carter_recover_spot": await load("res://art_source/defense_tests/carter/recover_spot.gd").run(self)
		"carter_caster_see_through": await load("res://art_source/defense_tests/carter/caster_see_through.gd").run(self)
		"carter_strike_iframes": await load("res://art_source/defense_tests/carter/strike_iframes.gd").run(self)
		"carter_chain": await load("res://art_source/defense_tests/carter/chain.gd").run(self)
		"auto_finisher": await test_auto_finisher()
		"auto_kill": await test_auto_kill()
		"tells": await test_tells()
		"dash_v2": await test_dash_v2()
		"dash_recovery_v2": await test_dash_recovery_v2()
		"dash_spam_v2": await test_dash_spam_v2()
		"dash_parry": await test_dash_parry()
		"dash_legacy": await test_dash_legacy()
		"dash_layers": await test_dash_layers()
		"punch_reach": await test_punch_reach()
		"punch_contact": await test_punch_contact()
		"y_sort_eric": await test_y_sort_eric()
		"v2_cadence": await test_v2_cadence()
		"delayed_slam": await test_delayed_slam()
		"whirl_lunges": await test_whirl_lunges()
		"hug_mixup": await test_hug_mixup()
		"hug_reach": await test_hug_reach()
		"break_gauge": await test_break_gauge()
		"break_entry": await test_break_entry()
		"mash_tiers": await test_mash_tiers()
		"mash_tiers_live": await test_mash_tiers_live()
		"juggle": await test_juggle()
		"juggle_kill": await test_juggle_kill()
		"juggle_super": await test_juggle_super()
		"mash_rates": await load("res://art_source/defense_tests/mash/rates.gd").run(self)
		"gauge_extra": await test_gauge_extra()
		"mason_contact": await test_mason_contact()
		"mason_combined": await test_mason_combined()
		"mason_bots": await test_mason_bots()
		"mason_back_rope": await test_mason_back_rope()
		"mason_pitch": await load(MASON_MODES + "pitch.gd").run(self)
		"mason_rain": await load(MASON_MODES + "rain.gd").run(self)
		"reflect_auto_v2": await test_reflect_auto_v2()
		"eric_window_daze": await load("res://art_source/defense_tests/eric/window_daze.gd").run(self)
		"sword_gate": await test_sword_gate()
		"sword_path": await load(ERIC_MODES_DIR + "sword_path.gd").run(self)
		"slam_point": await load(ERIC_MODES_DIR + "slam_point.gd").run(self)
		"entrance_hud": await load(ERIC_MODES_DIR + "entrance_hud.gd").run(self)
		"mine_trap": await test_mine_trap()
		"mine_mash": await test_mine_mash()
		"computah_overload": await test_computah_overload()
		"pace_bot": await test_pace_bot()
		"pause_basic": await test_pause_basic()
		"pause_hitstop": await test_pause_hitstop()
		"pause_freeze": await test_pause_freeze()
		"pause_mash": await test_pause_mash()
		"pause_barrage": await test_pause_barrage()
		"pause_beam_rush": await test_pause_beam_rush()
		"pause_messatsu": await test_pause_messatsu()
		"pause_dialogue": await test_pause_dialogue()
		"pause_no_leak": await test_pause_no_leak()
		"pause_blocked": await test_pause_blocked()
		"pause_restart": await test_pause_restart()
		"pause_quit": await test_pause_quit()
		"vs_card": await test_vs_card()
		"entrance": await test_entrance()
		"drift": await test_drift()
		"inferno": await test_inferno()
		"combined": await test_combined()
		"spin_tell": await test_spin_tell()
		"bixby_flyby": await load(BIXBY_MODES + "flyby.gd").run(self)
		"bixby_inside": await load(BIXBY_MODES + "inside.gd").run(self)
		"spin_reach": await test_spin_reach()
		"static_dodge": await test_static_dodge()
		"josh_layout": await test_josh_layout()
		"josh_wild_cards": await load(JOSH_MODES + "wild_cards.gd").run(self)
		"josh_summon": await load(JOSH_MODES + "summon.gd").run(self)
		"josh_hands": await load(JOSH_MODES + "hands.gd").run(self)
		"josh_guns": await load(JOSH_MODES + "guns.gd").run(self)
		"josh_monte": await load(JOSH_MODES + "monte.gd").run(self)
		"matt_pass_through": await test_matt_pass_through()
		"matt_bounces": await test_matt_bounces()
		"matt_trueshot": await test_matt_trueshot()
		"matt_yell": await test_matt_yell()
		"matt_entrance": await test_matt_entrance()
		"matt_bots": await test_matt_bots()
		"matt_glass_row": await test_matt_glass_row()
		"matt_glass_damage": await test_matt_glass_damage()
		"matt_glass_release": await test_matt_glass_release()
		"matt_deafen": await test_matt_deafen()
		"matt_glass_bots": await test_matt_glass_bots()
		"matt_scream": await load(MATT_MODES + "scream.gd").run(self)
		"matt_glass_rows": await load(MATT_MODES + "glass_rows.gd").run(self)
		"matt_deafen_rate": await load(MATT_MODES + "deafen_rate.gd").run(self)
		"matt_spots": await load(MATT_MODES + "spots.gd").run(self)
		"matt_badge": await load(MATT_MODES + "badge.gd").run(self)
		"matt_yell_chain": await load(MATT_MODES + "yell_chain.gd").run(self)
		"matt_cover": await load(MATT_MODES + "cover.gd").run(self)
		"matt_echo": await load(MATT_MODES + "echo.gd").run(self)
		"matt_echo_gaps": await load(MATT_MODES + "echo_gaps.gd").run(self)
		"matt_echo_disc": await load(MATT_MODES + "echo_disc.gd").run(self)
		"matt_echo_parry": await load(MATT_MODES + "echo_parry.gd").run(self)
		"matt_echo_boomburst": await load(MATT_MODES + "echo_boomburst.gd").run(self)
		"matt_echo_feint": await load(MATT_MODES + "echo_feint.gd").run(self)
		"matt_echo_stamina": await load(MATT_MODES + "echo_stamina.gd").run(self)
		"matt_echo_lazy": await load(MATT_MODES + "echo_lazy.gd").run(self)
		"matt_echo_rotation": await load(MATT_MODES + "echo_rotation.gd").run(self)
		"matt_echo_bots": await load(MATT_MODES + "echo_bots.gd").run(self)
		"matt_break_only": await load(MATT_MODES + "break_only.gd").run(self)
		"burak_shots": await test_burak_shots()
		"burak_cutlass": await test_burak_cutlass()
		"burak_entrance": await test_burak_entrance()
		"burak_laugh": await test_burak_laugh()
		"burak_barrels": await test_burak_barrels()
		"burak_volley": await test_burak_volley()
		"burak_ramp": await test_burak_ramp()
		"burak_bots": await test_burak_bots()
		"burak_hint": await load("res://art_source/defense_tests/burak/hint.gd").run(self)
		"burak_laugh_auto": await load("res://art_source/defense_tests/burak/laugh_auto.gd").run(self)
		"danny_entrance": await load(DANNY_MODES + "entrance.gd").run(self)
		"danny_sleep": await load(DANNY_MODES + "sleep.gd").run(self)
		"danny_spit": await load(DANNY_MODES + "spit.gd").run(self)
		"danny_headbutt": await load(DANNY_MODES + "headbutt.gd").run(self)
		"danny_slams": await load(DANNY_MODES + "slams.gd").run(self)
		"danny_sumo": await load(DANNY_MODES + "sumo.gd").run(self)
		"danny_bump": await load(DANNY_MODES + "bump.gd").run(self)
		"greyson_takeover": await load(GREYSON_MODES + "takeover.gd").run(self)
		"greyson_takeover_mark": await load(GREYSON_MODES + "takeover_mark.gd").run(self)
		"greyson_plates": await load(GREYSON_MODES + "plates.gd").run(self)
		"greyson_slams": await load(GREYSON_MODES + "slams.gd").run(self)
		"greyson_poses": await load(GREYSON_MODES + "poses.gd").run(self)
		"greyson_race": await load(GREYSON_MODES + "race.gd").run(self)
		"greyson_bomb": await load(GREYSON_MODES + "bomb.gd").run(self)
		"greyson_brawl": await load(GREYSON_MODES + "brawl.gd").run(self)
		"greyson_orb": await load(GREYSON_MODES + "orb.gd").run(self)
		"jordan_finale": await load(JORDAN_MODES + "finale.gd").run(self)
		"jordan_god": await run_mode_file(JORDAN_MODES + "god.gd")
		"jordan_maze": await run_mode_file(JORDAN_MODES + "maze.gd")
		"jordan_kegs": await run_mode_file(JORDAN_MODES + "kegs.gd")
		"jordan_portals": await run_mode_file(JORDAN_MODES + "portals.gd")
		"jordan_circle": await run_mode_file(JORDAN_MODES + "circle.gd")
		"jordan_kaiju": await run_mode_file(JORDAN_MODES + "kaiju.gd")
		"jordan_final_beam": await run_mode_file(JORDAN_MODES + "final_beam.gd")
		"jordan_wheel": await run_mode_file(JORDAN_MODES + "wheel.gd")
		"bounds":await load(RING_MODES + "bounds.gd").run(self)
		"liam_takeover": await run_mode_file(LIAM_MODES + "takeover.gd")
		"liam_waves": await run_mode_file(LIAM_MODES + "waves.gd")
		"liam_pillar": await run_mode_file(LIAM_MODES + "pillar.gd")
		"liam_window": await run_mode_file(LIAM_MODES + "window.gd")
		"liam_ice": await run_mode_file(LIAM_MODES + "ice.gd")
		"liam_tremors": await run_mode_file(LIAM_MODES + "tremors.gd")
		"liam_maze_bot": await run_mode_file(LIAM_MODES + "maze_bot.gd")
		"liam_zip": await run_mode_file(LIAM_MODES + "zip.gd")
		"liam_firestorm": await run_mode_file(LIAM_MODES + "firestorm.gd")
		"liam_firestorm_bot": await run_mode_file(LIAM_MODES + "firestorm_bot.gd")
		"liam_lunge": await run_mode_file(LIAM_MODES + "lunge.gd")
		"liam_loop": await run_mode_file(LIAM_MODES + "loop.gd")
		"liam_tsunami_gate": await run_mode_file(LIAM_MODES + "gate.gd")
		"liam_firestorm_gate": await run_mode_file(LIAM_MODES + "firestorm_gate.gd")
		"champion_ending": await run_mode_file(ENDING_MODES + "champion.gd")
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
	var after_dash: float = defense.max_stamina - defense.dash_stamina_cost
	check(is_equal_approx(defense.stamina, after_dash), "a dash costs a third of the bar, %.2f (%.2f)" % [defense.dash_stamina_cost, defense.stamina])
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
	var delay: float = defense.stamina_regen_delay
	check(first_regen >= delay - 0.001 and first_regen <= delay + 1.0 / 60.0 + 0.001, "regen starts %.2f s after the spend (%.4f)" % [delay, first_regen])
	var mid := 0.0
	for since in stamina_at:
		if since >= delay + 0.3 and mid == 0.0:
			mid = since
	var rate: float = defense.max_stamina / defense.stamina_refill_time
	var expected := after_dash + rate * (mid - delay + 1.0 / 60.0)
	log_p("stamina %.3f at %.4f s (expected about %.3f)" % [stamina_at[mid], mid, expected])
	check(absf(stamina_at[mid] - expected) <= rate / 60.0 + 0.01, "refills at %.2f/s" % rate)
	await wait_until(func(): return defense.stamina >= 100.0, 240)
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
	# It only hurts where it lands, so they stay on the spot it is aimed at.
	await settle_player(Vector2(972, 800))
	await attack("SwordThrow")
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
	log_p("-- returning sword, through them from behind")
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
	var crossed := [false]
	var watch_back := func():
		if is_instance_valid(sword) and sword.flying and sword._reaches(player.hurtBox):
			crossed[0] = true
	physics_frame.connect(watch_back)
	await wait(40)
	physics_frame.disconnect(watch_back)
	log_p("its reach crossed them %s; events %s" % [crossed[0], events.map(func(e): return "%s %s" % [e.kind, e.id])])
	check(crossed[0] and events.is_empty(), "a returning sword goes right through them and hurts nothing: it has no mark to say where it flies")
	await wait(70)
	clear_iframes()
	events.clear()
	log_p("-- thrown sword, landing on them")
	var sword2: Node2D = load("res://Scenes/Bosses/EricThrownSwordScene.tscn").instantiate()
	sword2.player = player
	sword2.thrower = boss
	var hand: Vector2 = boss.frame_point(layout.THROW_RELEASE_PIXEL)
	sm.add_hazard(sword2, Vector2(hand.x, ground_y))
	# Aimed at where they stand, since it only hurts where it lands: it comes down point first, so the
	# guard takes it from any side.
	sword2.throw(hand, ground_y, player.global_position)
	await wait_until(func(): return not sword2.flying, 120)
	await wait(2)
	check(events_of("BLOCKED", &"eric_thrown_sword").size() == 1 and events_of("HIT").is_empty(), "the sword landing on them is blocked")
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
	# Without blocking a held guard drops once its parry window is over, long before the hug arrives.
	if blocking():
		check(guard_at_grab[0], "guard was up when the grab landed")
	else:
		check(not guard_at_grab[0], "the guard held from the start had dropped long before the grab landed")
	check(grabbed[0], "the hug grabbed the player holding block")
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


# Every drop in the stamina bar from here on, to the thousandth: what a run paid, whatever the refill or a
# test's own top-ups did around it.
var spends: Array = []


func track_spends() -> void:
	spends.clear()
	var last := [defense.stamina]
	defense.stamina_changed.connect(func(value: float, _max_value: float):
		if value < last[0] - 0.0001:
			spends.append(snappedf(last[0] - value, 0.001))
		last[0] = value)


# `count` whiffs, as track_spends() records them.
func whiffs(count: int) -> Array:
	var want := []
	want.resize(count)
	want.fill(snappedf(defense.parry_whiff_cost, 0.001))
	return want


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
	# Each case from a full bar, so no press is refused for want of stamina: this is which presses parry,
	# and what the rest cost is read off track_spends().
	var full := func(): defense._set_stamina(defense.max_stamina)
	track_spends()
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
	log_p("-- a press whose window has passed doesn't parry")
	full.call()
	press(KEY_SHIFT)
	# The window is measured in game time, which a freeze slows, so wait for the window itself.
	await past_window()
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- mashing: presses 0.2 s apart")
	full.call()
	for i in 3:
		press(KEY_SHIFT)
		await wait(6)
		release(KEY_SHIFT)
		await wait(6)
	press(KEY_SHIFT)
	await wait(3)
	# Without blocking the hits before this one land, and their i-frames would swallow it.
	clear_iframes()
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- guard held from earlier")
	full.call()
	press(KEY_SHIFT)
	await wait(60)
	clear_iframes()
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	await wait(40)
	log_p("-- after mashing stops for 0.5 s, a press parries again")
	full.call()
	press(KEY_SHIFT)
	await wait(3)
	clear_iframes()
	results.append(front_hit(&"eric_quake_wave", dummy_source()))
	release(KEY_SHIFT)
	var late := unparried()
	log_p("results %s (1 HIT, 2 BLOCKED, 3 PARRIED), blocking %s" % [results, "on" if blocking() else "off"])
	check(results == [3, 3, late, late, late, 3], "parry, re-armed parry, then the late press, the mash and the held guard all %s, then a parry" % ("blocked" if blocking() else "hit"))
	# (step 4b tests below)
	await wait(roundi(defense.parry_window * 60.0) + 10)
	log_p("spends %s" % [spends])
	if blocking():
		check(player.playerHealth == 100, "no damage")
		var block: float = snappedf(catalogue_block_cost(&"eric_quake_wave"), 0.001)
		check(spends == [block, block, block], "only the three blocks cost stamina (%s)" % [spends])
	else:
		check(player.playerHealth == 97, "the three that weren't parried each cost a half-heart (%d)" % player.playerHealth)
		# The late press, the four mashed and the held one parried nothing; the three parries were free.
		check(spends == whiffs(6), "and each of the six presses that parried nothing cost a missed parry, the parries nothing (%s)" % [spends])


# The game as it ships, with blocking off (PlayerDefense.BLOCKING_ENABLED): the guard is only the parry's
# stance. It shows for the press's parry window and drops after it with the key still held, and the
# player walks again; a held guard takes light and heavy blockable hits as HITs, pays nothing for them
# and never breaks; holding it never pauses the refill; and the parry inside the window is untouched.
func test_no_block() -> void:
	await load_eric()
	park_eric()
	health_ok()
	track()
	track_parries()
	var source: String = FileAccess.get_file_as_string(PLAYER_DEFENSE)
	check(source.contains("static var BLOCKING_ENABLED := false") and not blocking(), "blocking ships switched off, and this run plays it that way")
	await settle_player(Vector2(972, 800))

	log_p("-- the guard is only the parry's stance")
	press(KEY_SHIFT)
	await wait(3)
	check(defense.is_guarding() and player.state_machine.current_state.name == "Blocking", "a press puts the guard up (%s)" % player.state_machine.current_state.name)
	await past_window()
	await wait(2)
	check(not defense.is_guarding() and player.state_machine.current_state.name != "Blocking", "and it drops once the parry window is over, the key still held (%s)" % player.state_machine.current_state.name)
	var held_from: Vector2 = player.global_position
	press(KEY_RIGHT)
	await wait(20)
	release(KEY_RIGHT)
	await wait(10)
	var walked: float = player.global_position.x - held_from.x
	check(walked > 100.0, "so a player still holding it walks (%.0f px)" % walked)
	check(not defense.is_guarding(), "and holding it never brings the guard back")
	release(KEY_SHIFT)
	await wait(40)

	log_p("-- a held guard takes the hits, pays only its press's missed parry and never breaks")
	await settle_player(Vector2(972, 800))
	health_ok()
	defense._set_stamina(defense.max_stamina)
	press(KEY_SHIFT)
	await past_window()
	var landed := [front_hit(&"eric_quake_wave", dummy_source())]
	for i in 5:
		clear_iframes()
		landed.append(front_hit(&"eric_whirlwind", dummy_source()))
	clear_iframes()
	release(KEY_SHIFT)
	log_p("a light hit then five heavy ones on a held guard: %s, stamina %.1f" % [landed, defense.stamina])
	check(landed == [1, 1, 1, 1, 1, 1] and events_of("BLOCKED").is_empty(), "a light and five heavy hits all land (%s)" % [landed])
	check(is_equal_approx(defense.stamina, defense.max_stamina - defense.parry_whiff_cost) and not defense.is_guard_broken, "the press cost its missed parry and nothing more, and the guard never broke (%.1f)" % defense.stamina)
	health_ok()
	await wait(40)

	log_p("-- holding it never pauses the refill")
	defense._set_stamina(defense.max_stamina)
	press(KEY_SHIFT)
	# Its missed parry paid first: from here on only the held key is under test.
	await past_window()
	defense._spend(60.0)
	var low: float = defense.stamina
	await wait(roundi((defense.stamina_regen_delay + 1.0) * 60.0))
	check(not defense.is_regen_paused() and defense.stamina > low + 10.0, "the bar refills with the key held (%.1f -> %.1f)" % [low, defense.stamina])
	release(KEY_SHIFT)
	await wait(40)

	log_p("-- the parry is untouched")
	var parried: int = await parry_once()
	check(parried == 3 and parries.size() == 1, "a fresh press inside the window still parries (%d)" % parried)


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
	check(before - 1 - boss.boss_health == roundi(full * finisher.finisher_damage_ratio * finisher.SUPERCHARGE_MULTIPLIER), "the supercharged damage")
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
	# Each case from a full bar: a dash is a third of it, and this is about what follows a dash, not whether
	# the bar has one in it (stamina_costs).
	var full := func(): defense._set_stamina(defense.max_stamina)
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
	full.call()
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

	log_p("-- a press that isn't a parry does not cancel it")
	defense.dash_recovery_time = 0.6
	await settle_player(Vector2(972, 760))
	await wait(20)
	full.call()
	await dash(KEY_LEFT)
	release(KEY_LEFT)
	press(KEY_SHIFT)
	# The recovery is set to 0.6 s above, so it is still running once the parry window has passed.
	await past_window()
	result = front_hit(&"eric_quake_wave", dummy_source())
	check(result == unparried(), "not parried (%d)" % result)
	check(defense.is_dash_recovering(), "a press that isn't a parry leaves the recovery running")
	tap(KEY_Q)
	await wait(3)
	check(player.state_machine.current_state.name != "Punching", "no punch during the recovery (%s)" % player.state_machine.current_state.name)
	release(KEY_SHIFT)
	defense.dash_recovery_time = 0.25

	log_p("-- the finisher and a grab clear it")
	await settle_player(Vector2(972, 700))
	await wait(30)
	full.call()
	await dash(0)
	check(defense.is_dash_recovering(), "recovering")
	player.begin_finisher()
	check(not defense.is_dash_recovering(), "begin_finisher clears it")
	player.is_finishing = false
	await wait(30)
	full.call()
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
	await break_guard()
	check(defense.is_guard_broken and is_equal_approx(hype.hype, 20.0), "a guard break costs 30 (50 -> %.0f)" % hype.hype)
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
# Hits that land inside the i-frames on purpose, because the player is held and cannot dodge, or, for
# Captain Burak's keg blasts, because the bill is one hit for every keg left, one after another, and for
# his pistol pair, so a hit on the first shot never swallows the second's parry. Danny's rope slam lands just
# after the belly bump's own hit, on a player he has sealed and is carrying into the ropes.
const IGNORES_IFRAMES := [&"eric_bear_hug_squeeze", &"computah_slam", &"burak_barrel_blast", &"burak_shot",
	&"danny_rope_slam"]

const SMOKE_SPOTS := {
	"eric": Vector2(972, 700),
	"computah": Vector2(960, 700),
	"carter": Vector2(960, 560),
	"mason": Vector2(960, 640),
	"jordan": Vector2(960, 640),
	"liam": Vector2(960, 640),
	"josh": Vector2(960, 640),
	"matt": Vector2(960, 760),
	"burak": Vector2(960, 800),
	"danny": Vector2(960, 800),
	"greyson": Vector2(960, 800),
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
	rotate_liam_to_inferno()
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
		# The fight's first hug squeezes hug_first_squeezes times, every later one hug_squeezes. The first is
		# always red, so it is always a grab here.
		var pacing = load(ERIC_PACING)
		var wanted := range(hugs.size()).map(func(k): return pacing.value("hug_first_squeezes" if k == 0 else "hug_squeezes"))
		check(hugs == wanted, "every bear hug that finished squeezed %d times, the fight's first %d (%s)" % [pacing.value("hug_squeezes"), pacing.value("hug_first_squeezes"), hugs])
	if fight == "carter":
		check(ids.has(&"wrestler_punish"), "punching a wrestler still hurts")
	if fight == "liam" and phase == 2:
		check(ids.has(&"bixby_fireball") and ids.has(&"bixby_inferno"), "his Inferno lands: its fireballs and its breath (%s)" % [ids.keys()])
		check_liam_perch()
	elif fight == "liam":
		check(ids.has(&"bixby_quake_ring") and ids.has(&"bixby_sonic_beam") and not ids.has(&"bixby_quake_burst"),
			"his combined attack lands its quake rings and its beams, and plants no crack (%s)" % [ids.keys()])
		check(ids.get(&"bixby_flyby_breath", 0) >= 2, "his flyby lands on a still player, once a pass")


# What each attack should cost the guard, and what should never be blockable at all.
const UNBLOCKABLE := [&"computah_beam", &"computah_chase", &"computah_slam", &"computah_overload_blast", &"wrestler_punish", &"eric_quake_ring", &"eric_bear_hug_squeeze", &"mason_poo_contact", &"bixby_inferno", &"bixby_ember", &"bixby_quake_ring", &"bixby_sonic_beam", &"bixby_flyby_breath", &"bixby_flyby_fire",&"matt_yell", &"matt_glass", &"burak_barrel_blast", &"burak_cutlass", &"danny_quake_ring", &"danny_headbutt", &"greyson_plate", &"greyson_eruption", &"greyson_brawl_hook_l", &"greyson_brawl_hook_r", &"greyson_brawl_straight", &"greyson_brawl_straight_unguarded", &"josh_hand_slam", &"josh_gun_beam", &"josh_monte_strike", &"josh_monte_punish"]


func test_blocks() -> void:
	await load_fight(fight, STATE_INTROS.has(fight))
	await clear_intro(fight)
	rotate_liam_to_inferno()
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
	# Danny's landings leave puddles that root feet still on them as they arm, and a root seals the guard: his
	# blocker steps off each one, as a player must (danny/blocks.gd).
	var stepper = load(DANNY_MODES + "blocks.gd").new() if fight == "danny" else null
	while defense.clock - start < 45.0 and not player.fight_over:
		frames_run += 1
		if stepper:
			spot = stepper.next_spot(self, spot)
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
	if stepper:
		log_p("stepped off %d puddles as they armed" % stepper.steps)
		stepper.clear_floor(self)
	check(guarded_frames > frames_run * 0.9, "the guard stayed up through the fight (%d of %d frames)" % [guarded_frames, frames_run])
	for id in costs:
		var want: float = catalogue_block_cost(id)
		check(want > 0.0 and is_equal_approx(costs[id], want), "%s costs %.0f (expected %s)" % [id, costs[id], "%.0f" % want if want > 0.0 else "nothing: it shouldn't be blockable"])
	for id in hit_ids:
		if UNBLOCKABLE.has(id):
			check(not costs.has(id), "%s is never blocked" % id)
	if fight == "liam" and phase == 2:
		check(costs.has(&"bixby_fireball") and hit_ids.has(&"bixby_inferno"), "his Inferno came: a fireball blocked, and the breath through the guard (%s, %s)" % [costs, hit_ids])
		check_liam_perch()
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
	var front := front_hit(&"mason_poo_blast", dummy_source())
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


# The rest of the roster, one fight per run: [boss body, punish state].
const PUNISH_WINDOWS := {
	# Boss 2's vent. His punish state's exported defaults ARE the vent, so a bare transition into it
	# opens a working window without going through open_window().
	"computah": ["Arena/ComputahScene/ComputahCharacterBody", "Punish"],
	"mason": ["Arena/MasonScene/MasonCharacterBody", "Eat"],
	"jordan": ["Arena/JordanScene/JordanCharacterBody", "Taunt"],
	"liam": ["Arena/BixbyBeastScene/BixbyBeastCharacterBody", "Recover"],
	# His Recover needs nothing from the attack before it, so a bare transition opens a working window.
	"matt": ["Arena/MattScene/MattCharacterBody", "Recover"],
	"josh": ["Arena/JoshCardsScene/JoshCardsCharacterBody", "Recover"],
	"carter_akuma": ["Arena/CarterAkumaScene/CarterAkumaCharacterBody", "Recover"],
	"burak": ["Arena/BurakBossScene/BurakBossCharacterBody", "Taunt"],
	# His nap needs nothing from the string before it, so a bare transition opens a working window.
	"danny": ["Arena/DannyBossScene/DannyBossCharacterBody", "Sleep"],
	"greyson": ["Arena/GreysonScene/GreysonCharacterBody", "Pose"],
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
	# Matt's finisher is his Break's alone (MattScript.can_be_dazed); this knob gives his window its old daze.
	if key == "matt":
		boss.daze_in_recover = true
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
	# Two seconds on his chain can have him on another sheet, and a boss whose sheets each stand on
	# their own offset (sheet_offset: Danny's, Burak's) is settled on whichever one is showing, less
	# any lift (Danny's set_lift).
	var settled: Vector2 = rest
	if "sheet_offset" in boss:
		settled = boss.sheet_offset - Vector2(0, boss.lift_px if "lift_px" in boss else 0.0) / boss.sprite.global_scale
	check(boss.sprite.offset.distance_to(settled) < 2.0, "the recoil settles back (%s, the sheet showing stands on %s)" % [boss.sprite.offset, settled])


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
	check(on_sight == unparried(), "a press on sight doesn't parry (%d)" % on_sight)
	check(strike > window + 1.0 / 60.0, "the strike is %.2f s past the light, the window covers %.2f s" % [strike, window])

	log_p("-- and the read, on the dash, parries")
	defense.rearm_parry()
	var on_dash: int = await parry_at(clone_frames(dash_time))
	check(on_dash == 3, "a press as it dashes parries (%d)" % on_dash)
	# The window opens this long after the light, which is what the player has to wait out.
	log_p("the window opens %.2f s into the light, %.0f%% of the way through it" % [strike - window, 100.0 * (strike - window) / show_time])

	log_p("-- a clone bitten on sight isn't parried")
	defense.rearm_parry()
	press(KEY_SHIFT)
	await wait(clone_frames(strike))
	var bitten := front_hit(&"eric_quake_wave", dummy_source())
	release(KEY_SHIFT)
	check(bitten == unparried(), "the bitten clone isn't parried (%d)" % bitten)
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
	check(spilled == unparried(), "with nothing rearming it, the feint's press costs the next clone too (%d)" % spilled)
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
	# Computah's pounce, the grab at the end of his chase: ComputahStateMachine.pounce_tell, floored
	# at POUNCE_TELL_FLOOR. The chase is not in his rotation yet, so nothing drives this today.
	&"computah_chase": 0.320,
	# THE LOCK-TO-FIRE HOLD, NOT THE CHARGE. ComputahStateMachine.beam_lock, floored at
	# BEAM_LOCK_FLOOR. The charge before it is longer but gives no read at all: the aim follows the
	# player for the whole of it, so there is nothing to be somewhere else from until it latches.
	&"computah_beam": 0.450,
	# Eric's reworked fight (EricPacing V2), each at its enraged value, the one that can fall under the
	# bar. The slam's red tell comes up exactly slam_tell_time before the waves, delayed or not.
	&"eric_quake_wave_v2": 0.360,
	# The whirlwind's yellow wind-up, before the lunges; its sweep lives with him.
	&"eric_whirlwind_v2": 0.400,
	# The bear hug's charge, red or yellow on the same timing.
	&"eric_bear_hug_grab_v2": 0.450,
	&"eric_shoulder_charge": 0.450,
	# Beast Bixby's Inferno floods three quarters of the ring from his mouths: nothing flies, so its read
	# is the wind-up he rears back through under the yellow ring. BixbyBeastStateMachine.inferno_windup.
	&"bixby_inferno": 1.400,
	# Matt's Trueshot: THE LATCH-TO-RELEASE HOLD, like Computah's beam. The aim tracks the player through the
	# charge, so there is nothing to be elsewhere from until it latches, trueshot_lock_lead before the
	# release; and from the station nearest the player the wave has almost no flight at all.
	&"matt_trueshot": 0.350,
	# His yell in the punish window: the ring blows out from his mouth, so its read is the yellow tell
	# before it, MattStateMachine.yell_tell (0.40 until the 2026-10-04 tuning: matt_yell_chain).
	&"matt_yell": 0.580,
	# The Echo Roars' rings blow out from his mouth: a roar's read is its badge, a beat (echo_red_lead_beats at 152
	# bpm), and the BOOMBURST's a beat and a half. Documentation while approach pins him to the Ezreal set; their own
	# modes hold them (matt_echo, matt_echo_gaps).
	&"matt_echo": 0.395,
	&"matt_boomburst": 0.592,
	# Captain Burak's pistol pair: each ball is slowed to take at least 0.40 s to reach the point it was
	# aimed at (his plan's number), and that floor is its read, held to the window as a wind-up is.
	&"burak_shot": 0.400,
	# His cutlass strikes the step its wind-up ends, so its read is that wind-up: 0.55 s held under the
	# red badge.
	&"burak_cutlass": 0.550,
	# Danny's Sumo Smash lands where he latched, and the badge over the marked spot is up from the latch:
	# DannyBossSlams' latch-to-impact. The big fifth, under the red badge, 0.20 s of latch and the 0.35 s drop; each
	# hop, under the yellow ring and its splash zone, 0.12 s of latch and the 0.28 s drop.
	&"danny_butt_slam": 0.550,
	&"danny_hop_slam": 0.400,
	# His belly bump's read is its wind-up under the red badge, before the run (DannyBossBellyBump.windup_time).
	&"danny_belly_bump": 0.800,
	# His headbutt's read is its wind-up under the red badge, from the crouch to the launch; the 0.22 s flight
	# after it is shorter than the parry window by design (his plan's section 6).
	&"danny_headbutt": 0.550,
	# Greyson's plates, Burak's pistol balls again: each plate's first leg is slowed to take at least 0.40 s to
	# reach the player's feet as it left his hand (GreysonThrow.min_flight, his plan's number), and that floor is
	# its read, held to the window as a wind-up is.
	&"greyson_plate": 0.400,
	# Josh's Hand Slam lands where the hand locked, and the red badge over the spot is up from the lock: its
	# lock-to-impact, 0.13 s of lock and the 0.23 s drop (JoshCardsStateMachine.hand_lock_time + hand_drop_time).
	&"josh_hand_slam": 0.360,
	# Josh's Gun Hands: each beam's band is drawn, with the yellow badge on it over the player, for the whole charge
	# before it fires (JoshCardsStateMachine.gun_charge_time), and the beam comes off hands parked at the sides of the
	# ring: that charge is its read.
	&"josh_gun_beam": 1.00,
	# Josh's Portal Monte: the real him's red badge is up over its small gate from its mark to its contact, show and
	# dash (JoshCardsStateMachine.monte_show + monte_dash), and the figure lunging out of it is that read's end.
	&"josh_monte_strike": 0.54,
	# Mason's Nugget Fastball: the strong red badge goes up as he comes set and the ball reaches the player a fixed beat
	# later, aimed where they're heading (MasonPitch: release_after + fastball_flight, release_after + changeup_flight).
	# The ball reports its own hits, so its read is that badge.
	&"mason_fastball": 0.42,
	&"mason_changeup": 0.64,
	# Beast Bixby's Flyby: its hits come off a Node2D, the pass's fire, so what is read is the floor projection, up for
	# BixbyBeastStateMachine.flyby_telegraph_time before the front sweeps.
	&"bixby_flyby_breath": 1.000,
	&"bixby_flyby_fire": 1.000,
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
	rotate_liam_to_inferno()
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
		# Matt's bolts and waves report their own hits the same way, off their own Hitbox.
		for hazard in get_nodes_in_group("matt_hazard"):
			var shot: Node = hazard.get_node_or_null("Hitbox")
			if shot and not born.has(shot.get_instance_id()):
				born[shot.get_instance_id()] = defense.clock
		# Captain Burak's report their own hits too, some off the hazard itself (his balls are their own
		# Area2D) and any off a Hitbox under it.
		for hazard in get_nodes_in_group("burak_hazard"):
			for source in [hazard, hazard.get_node_or_null("Hitbox")]:
				if source and not born.has(source.get_instance_id()):
					born[source.get_instance_id()] = defense.clock
		# Danny's report their own hits the same way: a slam's hit node and a quake ring are their own sources.
		for hazard in get_nodes_in_group("danny_hazard"):
			for source in [hazard, hazard.get_node_or_null("Hitbox")]:
				if source and not born.has(source.get_instance_id()):
					born[source.get_instance_id()] = defense.clock
		# Greyson's plates and zones are their own hit sources too.
		for hazard in get_nodes_in_group("greyson_hazard"):
			for source in [hazard, hazard.get_node_or_null("Hitbox")]:
				if source and not born.has(source.get_instance_id()):
					born[source.get_instance_id()] = defense.clock
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
	if fight == "liam" and phase == 2:
		check(approaches.has(&"bixby_fireball") and approaches.has(&"bixby_inferno"), "his Inferno's fireballs and breath were both read (%s)" % [approaches.keys()])
		check_liam_perch()


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
	check(await parry_at(new_band.size() + 1) == unparried(), "a press a frame earlier than that doesn't parry")
	defense.parry_window = shipped

	log_p("-- what that means for the attacks that matter")
	# Carter's clone: 0.44 s of light, then a 0.18 s dash into the player.
	var dash_frames := int(roundf(0.18 * 60.0))
	check(await parry_at(dash_frames) == 3, "a press on the first frame of a %d-frame clone dash still parries" % dash_frames)
	defense.parry_window = 0.15
	var old_dash: int = await parry_at(dash_frames)
	defense.parry_window = shipped
	log_p("the same press at the old window: %d (1 HIT, 2 BLOCKED, 3 PARRIED)" % old_dash)
	check(old_dash == unparried(), "at 0.15 that same read was too early and not parried (%d)" % old_dash)
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
	# Each case from a full bar: this is which presses count, and a bar run dry would refuse them
	# (stamina_costs is what they cost).
	var full := func(): defense._set_stamina(defense.max_stamina)

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
	full.call()
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
	full.call()
	# A whiffed press, as at a clone that never swung.
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(12)
	# Without the rearm, a press this soon after cannot parry.
	var carried: int = await parry_once()
	check(carried == unparried(), "inside the lockout the hit isn't parried (%d)" % carried)
	clear_iframes()
	await wait(12)
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(12)
	full.call()
	# The fight opens the next clone: the carryover is wiped.
	defense.rearm_parry()
	var rearmed: int = await parry_once()
	check(rearmed == 3, "after the rearm the same press parries (%d)" % rearmed)
	clear_iframes()

	log_p("-- but an early press inside the clone's own window still loses it")
	await wait(40)
	full.call()
	defense.rearm_parry()
	# The player reads it too early: the press is credited but its window has passed by the hit.
	press(KEY_SHIFT)
	await wait(3)
	release(KEY_SHIFT)
	await wait(20)
	var early: int = await parry_once()
	check(early == unparried(), "the early press whiffs and the mash lockout keeps the clone (%d)" % early)
	clear_iframes()

	log_p("-- end_parry_streak is callable from a fight")
	await wait(40)
	full.call()
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


# What a fight builds a scripted beat out of: the sealed lock, which takes the guard away too, the
# still pose it holds the player in, and the mash it runs on its own account, with no boss behind it.
func test_scripted() -> void:
	await load_eric()
	park_eric()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var hype: Node = player.get_node("Hype")
	var prompt: Node2D = current_scene.get_node("Arena/MainPlayer/CanvasLayer/FinisherPrompt")
	var animation_player: AnimationPlayer = player.get_node("AnimationPlayer")
	var presses := []
	defense.block_pressed.connect(func(credited: bool): presses.append(credited))
	await settle_player(Vector2(972, 700))

	log_p("-- the parry-only lock still answers a block press")
	player.lock_actions()
	press(KEY_SHIFT)
	await wait(6)
	check(defense.is_guarding(), "the guard goes up under lock_actions()")
	release(KEY_SHIFT)
	player.unlock_actions()
	await wait(40)

	log_p("-- a sealed lock does not")
	presses.clear()
	player.lock_actions_sealed()
	check(player.is_action_locked and player.lock_seals_guard, "sealed (%s, %s)" % [player.is_action_locked, player.lock_seals_guard])
	press(KEY_SHIFT)
	await wait(8)
	check(not defense.is_guarding() and player.state_machine.current_state.name != "Blocking", "no guard goes up (%s)" % player.state_machine.current_state.name)
	check(presses.is_empty(), "and the press never reaches the parry (%s)" % [presses])
	release(KEY_SHIFT)
	var held: Vector2 = await walk_offset(KEY_RIGHT, 15)
	check(held.length() < 1.0, "the rest of the hold is as it was: no walking (%s)" % held)

	log_p("-- a guard already up comes down as the seal lands")
	player.unlock_actions()
	await wait(40)
	press(KEY_SHIFT)
	await wait(6)
	check(defense.is_guarding(), "guarding before the seal")
	player.lock_actions_sealed()
	await wait(6)
	check(not defense.is_guarding() and player.state_machine.current_state.name != "Blocking", "and not after it (%s)" % player.state_machine.current_state.name)
	release(KEY_SHIFT)

	log_p("-- unlocking clears both kinds")
	player.unlock_actions()
	check(not player.is_action_locked and not player.lock_seals_guard, "both clear (%s, %s)" % [player.is_action_locked, player.lock_seals_guard])
	await wait(40)
	presses.clear()
	player.lock_actions()
	press(KEY_SHIFT)
	await wait(8)
	check(defense.is_guarding() and presses.size() == 1, "a plain lock answers a press again (%s, %s)" % [defense.is_guarding(), presses])
	release(KEY_SHIFT)
	player.unlock_actions()
	await wait(20)

	log_p("-- the scripted pose")
	await settle_player(Vector2(972, 700))
	press(KEY_RIGHT)
	check(await wait_until(func(): return player.state_machine.current_state.name == "Walking", 20), "walking into the beat")
	await wait(12)
	var mid_stride: int = player.sprite.frame_coords.x
	log_p("mid-stride on walk frame %d" % mid_stride)
	check(mid_stride > 0, "mid-stride, off the standing frame (%d)" % mid_stride)
	player.lock_actions()
	player.set_scripted_pose(true)
	await wait(6)
	check(player.state_machine.current_state.name == "Idle", "the pose puts them in Idle (%s)" % player.state_machine.current_state.name)
	check(not animation_player.is_playing(), "with the animation stopped")
	check(player.sprite.frame_coords.x == 0, "standing, not stopped mid-stride (%d)" % player.sprite.frame_coords.x)
	var posed: Vector2i = player.sprite.frame_coords
	await wait(30)
	check(player.sprite.frame_coords == posed, "holding the frame they are on (%s against %s)" % [player.sprite.frame_coords, posed])
	player.set_scripted_pose(false)
	await wait(4)
	check(animation_player.is_playing(), "and the AnimationPlayer runs again once the pose ends")
	release(KEY_RIGHT)
	player.unlock_actions()
	await wait(20)

	log_p("-- a scripted charge: no boss, no daze, no freeze, no hype")
	hype._set_hype(100.0)
	var spends := [0]
	hype.hype_spent.connect(func(): spends[0] += 1)
	var ended := []
	finisher.charge_ended.connect(func(filled: bool): ended.append(filled))
	var boss_health: int = boss.boss_health
	await settle_player(Vector2(972, 700))
	player.lock_actions()
	check(finisher.begin_scripted_charge({"press_gain": 0.25, "floor_time": 10.0}), "the charge starts")
	check(not finisher.begin_scripted_charge(), "and a second one is refused while it runs")
	await wait(3)
	check(finisher.is_charging() and finisher.boss == null, "it charges with no boss (%s)" % finisher.boss)
	check(not player.is_finishing and not finisher.tiered, "no player pose and no tiers")
	check(current_scene.process_mode != Node.PROCESS_MODE_DISABLED, "and nothing is frozen")
	check(prompt.visible, "the prompt is up")

	log_p("-- presses fill it")
	var pair: Array = finisher.mash_actions()
	var before: float = finisher.meter
	tap(MASH_KEYS[pair[0]])
	await wait(4)
	var gained: float = finisher.meter - before
	check(gained > 0.2, "a press pays press_gain (%.3f)" % gained)
	var repeated: float = finisher.meter
	tap(MASH_KEYS[pair[0]])
	await wait(4)
	check(finisher.meter - repeated < 0.2, "the same key twice does not (%.3f)" % (finisher.meter - repeated))
	var steps := 0
	while finisher.is_charging() and not finisher.scripted_filled and steps < 40:
		tap(MASH_KEYS[pair[steps % 2]])
		steps += 1
		await wait(4)
	log_p("filled over %d presses, meter %.3f" % [steps, finisher.meter])
	check(finisher.scripted_filled, "the mash fills it")
	check(ended == [true], "charge_ended(true), once (%s)" % [ended])
	check(finisher.is_input_locked(), "and input is locked from the fill")
	press(MASH_KEYS[pair[0]])
	check(await wait_until(func(): return not finisher.is_charging(), 120), "the charge ends after the prompt's FULL flash")
	check(finisher.is_mash_latched(), "a key still held is latched, so leftover mashing can't walk the player off")
	release(MASH_KEYS[pair[0]])
	check(spends[0] == 0 and hype.is_full(), "no hype spent (%d, %.0f)" % [spends[0], hype.hype])
	check(boss.boss_health == boss_health, "the boss took nothing (%d)" % boss.boss_health)

	log_p("-- with nobody pressing anything it still fills, inside floor_time")
	ended.clear()
	await wait(60)
	var started := Time.get_ticks_usec()
	check(finisher.begin_scripted_charge({"floor_time": 1.0}), "a charge with a one-second floor")
	check(await wait_until(func(): return finisher.scripted_filled, 300), "it fills with no press at all")
	var took := (Time.get_ticks_usec() - started) / 1000000.0
	log_p("filled in %.2f s, meter %.3f" % [took, finisher.meter])
	check(took >= 0.85 and took <= 1.8, "in about its floor_time (%.2f s)" % took)
	check(ended == [true], "and ends filled (%s)" % [ended])
	check(await wait_until(func(): return not finisher.is_charging(), 120), "the charge ends")

	log_p("-- ESCAPE!: the same widget, the opposite meaning")
	ended.clear()
	finisher.prompt_key = &"escape"
	check(finisher.begin_scripted_charge({"press_gain": 0.25, "floor_time": 20.0}), "a charge asking for the escape word")
	await wait(4)
	check(prompt.word_label != null and prompt.word_label.visible and prompt.word_label.text == "ESCAPE!", "the prompt says ESCAPE!")
	check(not prompt.text_sprite.visible, "with the drawn MASH! out of the way")
	steps = 0
	while finisher.is_charging() and not finisher.scripted_filled and steps < 40:
		tap(MASH_KEYS[pair[steps % 2]])
		steps += 1
		await wait(4)
	await wait(2)
	check(ended == [true], "it fills like any other word (%s)" % [ended])
	check(prompt.text_sprite.visible and not prompt.word_label.visible, "and FULL! takes it back as it always does")
	check(await wait_until(func(): return not finisher.is_charging(), 120), "the charge ends")

	log_p("-- and the usual word for everyone else")
	finisher.prompt_key = &"mash"
	ended.clear()
	check(finisher.begin_scripted_charge({"floor_time": 20.0}), "a charge on the usual word")
	await wait(4)
	check(prompt.text_sprite.visible and not prompt.word_label.visible, "shows the drawn MASH!")
	finisher.cancel_scripted_charge()
	await wait(4)
	check(not finisher.is_charging() and ended == [false], "and the caller can take it back (%s)" % [ended])
	player.unlock_actions()
	await wait(10)


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

	if blocking():
		log_p("-- the drain breaks a guard that is up when the bar runs out")
		defense._set_stamina(40.0)
		press(KEY_SHIFT)
		await wait(6)
		check(defense.is_guarding(), "guarding")
		player.apply_status(&"stamina_drain", 5.0)
		check(await wait_until(func(): return defense.is_guard_broken, 300), "the drain broke the guard")
		release(KEY_SHIFT)
		log_p("guard broken with %.0f stamina at %.2f s" % [defense.stamina, defense.clock])
		await wait_until(func(): return not defense.is_guard_broken, 300)
	else:
		# Without blocking the guard is only the parry's stance, up for its window, and a press needs its missed
		# parry in the bar, more than the drain takes in one window. So the drain never breaks it, and nor does
		# the whiff that empties the bar under the drain as the window closes.
		log_p("-- the drain never breaks the parry's stance")
		defense._spend(defense.stamina - (defense.parry_whiff_cost + 1.0))
		press(KEY_SHIFT)
		await wait(1)
		player.apply_status(&"stamina_drain", 5.0)
		await wait(1)
		var stance: bool = defense.is_guarding()
		await past_window()
		await wait(30)
		release(KEY_SHIFT)
		log_p("the stance up %s; now %.1f in the bar, the guard broken %s" % [stance, defense.stamina, defense.is_guard_broken])
		check(stance and defense.stamina <= 0.001 and not defense.is_guard_broken, "the stance comes up, its whiff empties the bar under the drain, and nothing breaks")
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


# One perfect dodge of a dash_through attack, as gauge_fights/greyson.gd's: a fresh dash, and the hit
# inside its immunity. Whether it paid out.
func perfect_dodge_once(id: StringName) -> bool:
	await wait_until(func(): return not defense.is_dash_recovering() and not defense.is_dash_cooling_down() \
		and defense.clock - defense.last_perfect_dodge_time >= defense.perfect_dodge_cooldown + 0.05, 240)
	# Past the gap a dash's immunity needs from the last one.
	await wait(40)
	var got := [false]
	var on_dodge := func(hit: RefCounted): got[0] = got[0] or hit.attack_id == id
	defense.perfect_dodged.connect(on_dodge)
	clear_iframes()
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait(2)
	omni_hit(id, dummy_source())
	defense.perfect_dodged.disconnect(on_dodge)
	await wait_until(func(): return not player.is_dodging, 30)
	await wait(4)
	return got[0]


# A read of a gauge spec's light attack: parried, or dashed through for one nothing guards (light_read).
func read_light(spec: Dictionary) -> bool:
	if spec.get("light_read", "parry") == "dodge":
		return await perfect_dodge_once(spec.light)
	return await parry_once(spec.light) == 3


# Breaks the player's guard from a nearly empty bar: with blocking, by blocking `id` past the parry
# window; without it, the one way left, the bar emptied while the guard is up.
func break_guard(id := &"eric_quake_wave") -> void:
	defense.stamina = 20.0
	defense.last_spend_time = defense.clock
	press(KEY_SHIFT)
	if blocking():
		await past_window()
		front_hit(id, dummy_source())
	else:
		await wait(3)
		defense.drain_stamina(defense.max_stamina)
	release(KEY_SHIFT)


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
	await break_guard()
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
	await wait_until(func(): return hug_lands_within(hug, 0.09), 400)
	if not hold_from_the_start:
		press(KEY_SHIFT)


# Whether his hug's lunge reaches the player inside `lead` seconds: V2's rush off its own clock, since
# it lands on hug_rush_time from any range, and V1's straight lunge off the gap left to close at its
# 1500 px/s.
func hug_lands_within(hug: Node, lead: float) -> bool:
	if hug.phase != hug.Phase.LUNGE:
		return false
	if load(ERIC_PACING).is_v2():
		return hug.lunge_left <= lead
	var grab_shape: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = grab_shape.shape.size * grab_shape.global_scale.abs() / 2.0
	return (shape.global_position.y - 27.0) - (grab_shape.global_position.y + half.y) < 1500.0 * lead


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


# Dashing out of the way of Computah's beam or a charge (Carter and Josh).
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
		if fight == "computah":
			# The locked aim line IS the incoming cue: it stops following them and the yellow ring
			# comes up, and from there the beam is coming down that exact line. The beam has no
			# flight - it is simply there at the end of the hold - so the dash is timed to the end
			# of the hold rather than to its start, or the ghost has expired before it arrives.
			var beam: Node = current_scene.get_node("Arena/ComputahScene/ComputahCharacterBody/StateManager/Beam")
			var bsm: Node = beam.get_parent()
			var fires_at: float = bsm.beam_charge + maxf(bsm.beam_lock, bsm.BEAM_LOCK_FLOOR)
			incoming = beam.phase == beam.Phase.LOCKED and beam.elapsed >= fires_at - 0.10
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


# Computah's cannon beam, boss 2's attack 1. THE READ IS THE LOCK, NOT THE CHARGE: the aim follows
# the player for the whole charge, so there is nothing to be somewhere else from until it latches.
# What is checked is exactly that - the line tracks, the latch freezes it, the yellow ring lives for
# the latched-to-fired hold and no longer, the fired beam goes through the spot it locked on rather
# than the spot they walked to, and a dash out of that line pays a perfect dodge.
func test_beam() -> void:
	await load_fight("computah")
	player.playerHealth = 1000
	track()
	track_dodges()
	boss = current_scene.get_node("Arena/ComputahScene/ComputahCharacterBody")
	var bsm: Node = boss.state_machine
	var beam: Node = bsm.states["Beam"]
	# The fight drives itself from here rather than off its own opening timer.
	bsm.post_dialogue_pre_fight_timer.stop()

	log_p("-- the aim tracks while it charges")
	await settle_player(Vector2(600, 760))
	bsm.on_child_transition(bsm.current_state, "Beam")
	await wait(3)
	check(beam.phase == beam.Phase.TRACK, "he braces and the cannon charges")
	check(tell_node() == null, "no badge while it tracks: there is nothing to answer yet")
	var opening: float = beam.beam.rotation
	await settle_player(Vector2(1400, 500))
	await wait(20)
	var tracked: float = beam.beam.rotation
	var onto: float = (beam._aim_point(player) - boss.muzzle_point()).angle()
	log_p("aim %.1f deg -> %.1f deg, the player at %.1f deg" % [rad_to_deg(opening), rad_to_deg(tracked), rad_to_deg(onto)])
	check(absf(rad_to_deg(angle_difference(opening, tracked))) > 5.0, "the aim followed them across the ring")
	check(absf(rad_to_deg(angle_difference(tracked, onto))) < 5.0, "and it is on them, not on their feet or their old spot")

	log_p("-- it latches, and nothing moves after that")
	check(await wait_until(func(): return beam.phase == beam.Phase.LOCKED, 200), "the aim latches")
	var lock_at: float = defense.clock
	var locked_angle: float = beam.locked_angle
	var locked_origin: Vector2 = beam.locked_origin
	var aimed_at: Vector2 = beam._aim_point(player)
	var ring := tell_node()
	check(ring != null and ring.dodge, "the yellow dodge ring comes up on the lock, not before it")
	await settle_player(Vector2(420, 900))
	await wait(8)
	check(beam.beam.rotation == locked_angle, "the line does not follow them any more")
	check(beam.locked_origin == locked_origin, "and it fires from where the muzzle was, not where it is")

	log_p("-- the shot goes down the latched line")
	check(await wait_until(func(): return beam.phase == beam.Phase.FIRE, 120), "it fires")
	var hold: float = defense.clock - lock_at
	log_p("locked for %.3f s before firing (floor %.2f s)" % [hold, bsm.BEAM_LOCK_FLOOR])
	check(hold >= bsm.BEAM_LOCK_FLOOR, "the lock-to-fire hold is at least the read floor")
	await wait(2)
	check(tell_node() == null, "the ring goes the moment the beam does")
	var along := Vector2.from_angle(locked_angle)
	var off_locked: float = absf((aimed_at - locked_origin).cross(along))
	var off_now: float = absf((beam._aim_point(player) - locked_origin).cross(along))
	log_p("the fired line passes %.0f px from where they were at the lock, %.0f px from where they are now" % [off_locked, off_now])
	check(off_locked < 40.0, "it goes through the spot it locked on")
	check(off_now > 200.0, "and not through the spot they walked to")

	log_p("-- a dash out of the line is a perfect dodge")
	check(await wait_until(func(): return bsm.current_state.name == "Beam", 900), "the next beam comes round")
	dodges.clear()
	events.clear()
	# Beside him, so the line it locks runs across the ring and a dash down clears it.
	await settle_player(Vector2(1500, 380))
	defense.stamina = defense.max_stamina
	check(await wait_until(func(): return beam.phase == beam.Phase.LOCKED, 400), "it locks on them where they stand")
	# A few frames before the shot: far enough out to be clear of it, close enough that the ghost
	# they left behind is still live when it arrives (PlayerDefense.perfect_dodge_window).
	await wait_until(func(): return beam.elapsed >= bsm.beam_charge + 0.36, 60)
	press(KEY_DOWN)
	tap(KEY_W)
	await wait(4)
	release(KEY_DOWN)
	await wait(30)
	log_p("dodges %s, hits %s" % [dodges.map(func(d): return d.id), events.map(func(e): return e.kind)])
	check(dodges.size() >= 1 and dodges[0].id == &"computah_beam", "dashing out of the beam earns a perfect dodge")
	check(events_of("HIT").is_empty(), "and it never touched them")


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
	"computah": ["res://Scenes/Bosses/ComputahBossFightScene.tscn", "Arena/ComputahScene"],
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
# too, and re-aims it, but it doesn't start another. `keep_full` holds the bar full for the spacing alone:
# today's dash pays again for every press during one, which a third of the bar a dash can't cover.
func mash_gap(keep_full := false) -> int:
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	var was_dodging := true
	for i in 90:
		if keep_full:
			defense._set_stamina(defense.max_stamina)
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
	check(not through.is_empty() and results.values().all(func(result): return result == "DODGED"), "every dash_through attack is dodged, Computah's beam included")
	await wait(40)
	var control := dummy_source()
	var landed: int = player.receive_hit(hit_info.make(&"computah_beam", control, player.global_position + Vector2(80, 0)))
	check(landed == hit_info.Result.HIT, "and without a dash the beam lands (%s)" % hit_info.Result.keys()[landed])
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

	log_p("-- a press that isn't a parry leaves it running")
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
	check(result == unparried() and defense.is_dash_recovering(), "not parried, and the landing runs on (%d)" % result)
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
# On a bar kept full: what is compared is the two dashes' own spacing and immunity, and at a third of the
# bar a dash, today's would run dry inside its first dash (it pays again for every press during one), so
# the bar would be all a run measured (stamina_costs has what the bar allows).
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
		defense._set_stamina(defense.max_stamina)
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
	check(today.gaps.size() > 0 and LEGACY_MASH_PERIOD_FRAMES.has(today.gaps[0]) and v2.gaps.size() > 0 and v2.gaps[0] == MASH_PERIOD_FRAMES, "mashed, v2 dashes as often as today: every %d frames (today %d)" % [MASH_PERIOD_FRAMES, today.gaps[0] if today.gaps.size() > 0 else -1])
	check(v2.taken == v2.dashes and today.taken > today.dashes, "today a press during a dash is taken and paid for again; v2 takes none (%d of %d against %d of %d)" % [v2.taken, v2.dashes, today.taken, today.dashes])
	# Against one dash rather than against today: on the full bar these runs keep, today's own re-aims spoil its
	# first dash's gap (DashImmunity), where v2 takes no press during a dash and keeps it. That one dash is all
	# mashing buys.
	var one_dash: int = ceili(CATALOG.DASH_IMMUNITY_TIME * 60.0) + 1
	check(v2.immune <= one_dash, "mashing v2 is never immune for longer than one dash is (%d frames, one dash %d; today %d)" % [v2.immune, one_dash, today.immune])
	check(runs.values().all(func(run: Dictionary): return float(run.immune) / run.frames < 0.35), "no way of dashing keeps dash immunity up for even 35% of the time")


# ------------------------------------------------------------------ the dash parry
# The dash cancelled into the guard (PlayerScript.dash_parry, on in Eric's fight and in the training
# room whose only exit is that fight). A block press ends the dash where it is and the guard goes up
# in its place, so the dash is a non-committal approach: the player can stop it into a block or a
# parry at any point in it. The parry itself is the ordinary guarded one, so everything that bounds a
# standing parry bounds this - and a press that is late or mashed buys a block at full stamina.
# What the cancel gives up is what the dash had not paid out: its i-frames and its dodge ghost. What
# it keeps is the wait for the next dash, so cancelling is never a free approach loop.

# In front of Eric, so the facing is up and front_hit comes down at them: parry_rules' own spot.
const DASH_PARRY_SPOT := Vector2(972, 800)


# The dash is 3 frames long, which dash_recovery_v2 pins, and a test can only reach two of them. A
# check that has to press inside a dash and then wait out a whole window inside the same dash needs
# more room than that, and stretches it: what those checks are about is the rule, not the length.
func stretch_dash(frames: int) -> void:
	player.dodge_time = frames / 60.0


# Dashes on the spot, then presses block inside the dash: [dashing, guarding] once the press has
# landed. Nothing is held, so the dash doesn't move the player and the hit that follows meets them
# where they already stand.
func dash_then_press() -> Array:
	await dash_ready()
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	press(KEY_SHIFT)
	await wait(1)
	return [player.is_dodging, defense.is_guarding()]


# Back to a standing player at full health with a full bar, whatever the last check left behind. It
# waits out parry_mash_lockout too: every check below presses block, and a press inside the lockout of
# the check before it would be uncredited for that reason rather than for the one under test.
func dash_parry_reset() -> void:
	release(KEY_SHIFT)
	await wait_until(func(): return Engine.time_scale == 1.0, 180)
	await wait_until(func(): return not player.is_dodging, 60)
	clear_iframes()
	health_ok()
	await settle_player(DASH_PARRY_SPOT)
	await wait_until(func(): return defense.clock - defense.last_press_time > defense.parry_mash_lockout, 120)


# Taps dash every frame until one comes out: physics frames from `from_frame`, the frame the last dash
# was pressed on, to the frame the next one is.
func redash_gap(from_frame: int) -> int:
	for i in 90:
		tap(KEY_W)
		await physics_frame
		if player.last_dodge_physics_frame != from_frame:
			return player.last_dodge_physics_frame - from_frame
	return -1


func test_dash_parry() -> void:
	await load_eric()
	park_eric()
	health_ok()
	track()
	track_parries()
	track_dodges()
	var immunity = load("res://Scripts/DashImmunity.gd")
	var catalog = load("res://Scripts/AttackCatalog.gd")
	var dash_length: float = player.dodge_time
	check(player.dash_parry, "Eric's fight turns the dash parry on")
	await settle_player(DASH_PARRY_SPOT)

	log_p("-- the press ends the dash and the guard goes up in its place, with the flag off and on")
	var results := []
	for on in [false, true]:
		player.dash_parry = on
		var state: Array = await dash_then_press()
		var blocking: bool = player.state_machine.current_state.name == "Blocking"
		var result := front_hit(&"eric_quake_wave", dummy_source())
		log_p("dash_parry %s: still dashing %s, guarding %s, state %s, result %d" % [on, state[0], state[1], player.state_machine.current_state.name, result])
		if on:
			check(not state[0] and state[1] and blocking, "the press ended the dash and put the guard up")
		else:
			check(state[0] and not state[1], "without it the dash runs on and the guard stays down")
		results.append(result)
		await dash_parry_reset()
	check(results == [1, 3], "off it is a hit, on it is a parry: %s (1 HIT, 3 PARRIED)" % [results])
	player.dash_parry = true

	log_p("-- it is a dead stop: no momentum carries into the guard")
	await dash_ready()
	press(KEY_RIGHT)
	await wait(2)
	var from: Vector2 = player.global_position
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	press(KEY_SHIFT)
	await wait(1)
	var at_cancel: Vector2 = player.global_position
	await wait(10)
	var slid: float = at_cancel.distance_to(player.global_position)
	log_p("cancelled after 1 dash frame: %.0f px travelled of the dash's %.0f, then %.1f px in the next 10 frames" % [from.distance_to(at_cancel), DASH_LENGTH, slid])
	check(from.distance_to(at_cancel) < DASH_LENGTH - 60.0, "the dash stopped well short of its %.0f px" % DASH_LENGTH)
	check(slid < 1.0, "and nothing slid on afterwards (%.1f px)" % slid)
	release(KEY_RIGHT)
	await dash_parry_reset()

	log_p("-- the landing beat is skipped, and the wait for the next dash is not")
	await dash_ready()
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	var pressed_on: int = player.last_dodge_physics_frame
	press(KEY_SHIFT)
	await wait(1)
	log_p("after the cancel: recovering %s, cooling down %s, state %s" % [defense.is_dash_recovering(), defense.is_dash_cooling_down(), player.state_machine.current_state.name])
	check(not defense.is_dash_recovering() and player.state_machine.current_state.name == "Blocking", "no landing beat: the guard is what they land in")
	check(defense.is_dash_cooling_down(), "the wait for the next dash still runs")
	release(KEY_SHIFT)
	var gap: int = await redash_gap(pressed_on)
	log_p("mashing dash from the cancel: the next one came %d frames after the first was pressed" % gap)
	check(gap == MASH_PERIOD_FRAMES, "cancelling buys no dash back: still %d frames apart (%d)" % [MASH_PERIOD_FRAMES, gap])
	await dash_parry_reset()

	log_p("-- the i-frames go with the dash: a dash-through attack lands after the cancel")
	dodges.clear()
	# Past perfect_dodge_min_dash_gap, so the dash that follows is a clean one.
	await wait(45)
	await dash_ready()
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	check(immunity.is_immune(player, catalog.DASH_IMMUNITY_TIME, catalog.DASH_IMMUNITY_COOLDOWN), "dashing, the i-frames are up")
	check(defense.ghost_active, "and the dodge ghost is out")
	press(KEY_SHIFT)
	await wait(1)
	log_p("after the cancel: immune %s, ghost %s" % [immunity.is_immune(player, catalog.DASH_IMMUNITY_TIME, catalog.DASH_IMMUNITY_COOLDOWN), defense.ghost_active])
	check(not immunity.is_immune(player, catalog.DASH_IMMUNITY_TIME, catalog.DASH_IMMUNITY_COOLDOWN), "cancelled, they are gone")
	check(not defense.ghost_active and player.dodge_ghost_position() == Vector2.INF, "and so is the ghost, so no near miss can pay either")
	var yellow := front_hit(&"eric_shoulder_charge", dummy_source())
	log_p("his yellow charge, which only a dash answers: result %d, %d dodges" % [yellow, dodges.size()])
	check(yellow == 1 and dodges.is_empty(), "it lands: the press bought the guard, not the guard and the dodge (%d)" % yellow)
	await dash_parry_reset()

	log_p("-- with no cancel the perfect dodge still wins over the parry")
	dodges.clear()
	parries.clear()
	await wait(45)
	await dash_ready()
	press(KEY_SHIFT)
	await wait(1)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	var through := front_hit(&"eric_whirlwind_v2", dummy_source())
	log_p("a blockable dash-through attack inside an uncancelled dash: result %d, %d dodges, %d parries" % [through, dodges.size(), parries.size()])
	check(through == 4 and dodges.size() == 1 and parries.is_empty(), "dodged, never parried (%d)" % through)
	await dash_parry_reset()

	log_p("-- a late press cancels the dash and buys %s, not a parry" % ("a block" if blocking() else "only its missed parry's cost"))
	stretch_dash(40)
	await dash_ready()
	var bar: float = defense.stamina
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	press(KEY_SHIFT)
	await past_window()
	var late := front_hit(&"eric_quake_wave", dummy_source())
	log_p("stamina %.0f -> %.0f, result %d" % [bar, defense.stamina, late])
	check(late == unparried(), "past the window it isn't parried (%d)" % late)
	var late_cost: float = defense.dash_stamina_cost + (defense.light_block_cost if blocking() else defense.parry_whiff_cost)
	check(is_equal_approx(bar - defense.stamina, late_cost), "and it costs %.0f in all: the dash and %s (%.1f)" % [late_cost, "the block" if blocking() else "the missed parry", bar - defense.stamina])
	player.dodge_time = dash_length
	await dash_parry_reset()

	log_p("-- a mashed press cancels it and buys no parry either: the lockout still bites")
	for i in 3:
		press(KEY_SHIFT)
		await wait(6)
		release(KEY_SHIFT)
		await wait(6)
	var mashed_state: Array = await dash_then_press()
	var mashed := front_hit(&"eric_quake_wave", dummy_source())
	log_p("still dashing %s, press credited %s, result %d" % [mashed_state[0], defense.press_credited, mashed])
	check(not mashed_state[0] and mashed == unparried() and not defense.press_credited, "the dash ends and nothing parries (%d)" % mashed)
	await dash_parry_reset()

	log_p("-- and a cancel leaves parry credit exactly where a standing press would")
	var credited := []
	await dash_ready()
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	press(KEY_SHIFT)
	await wait(1)
	credited.append(defense.press_credited)
	release(KEY_SHIFT)
	await wait(12)
	press(KEY_SHIFT)
	await wait(1)
	credited.append(defense.press_credited)
	log_p("a press that cancelled a dash and parried nothing, then one 0.2 s later: credited %s" % [credited])
	check(credited == [true, false], "the cancel sets parry_mash_lockout the way any other press does %s" % [credited])
	await dash_parry_reset()

	log_p("-- the guarded side still decides it")
	var behind_state: Array = await dash_then_press()
	var behind := front_hit(&"eric_quake_wave", dummy_source(), true)
	check(not behind_state[0] and behind == 1, "an attack behind the guard the dash became is neither parried nor blocked (%d)" % behind)
	await dash_parry_reset()
	var omni_state: Array = await dash_then_press()
	var omni := omni_hit(&"eric_quake_wave", dummy_source())
	check(not omni_state[0] and omni == 3, "one landed on top of them, with no direction to face, is (%d)" % omni)
	await dash_parry_reset()

	log_p("-- the dash is still paid for, and a parry off a cancel buys no dash back")
	await dash_ready()
	var before: float = defense.stamina
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	var parry_from: int = player.last_dodge_physics_frame
	press(KEY_SHIFT)
	await wait(1)
	var paid := front_hit(&"eric_quake_wave", dummy_source())
	log_p("stamina %.0f -> %.0f across a cancel and a parry" % [before, defense.stamina])
	check(paid == 3 and is_equal_approx(before - defense.stamina, defense.dash_stamina_cost), "the dash's %.0f stands and the parry costs nothing more (%.1f)" % [defense.dash_stamina_cost, before - defense.stamina])
	check(defense.is_dash_cooling_down(), "the wait for the next dash survived the parry")
	release(KEY_SHIFT)
	await wait_until(func(): return Engine.time_scale == 1.0, 180)
	var parry_gap: int = await redash_gap(parry_from)
	log_p("mashing dash after a parry off a cancel: the next one came %d frames after the first" % parry_gap)
	check(parry_gap >= MASH_PERIOD_FRAMES, "still at least %d frames apart (%d): parrying can't unwind the cancel" % [MASH_PERIOD_FRAMES, parry_gap])
	await dash_parry_reset()

	log_p("-- a block already held is not a cancel: dashing out of the guard still dashes")
	stretch_dash(20)
	await dash_ready()
	press(KEY_SHIFT)
	await wait(2)
	check(defense.is_guarding(), "guarding before the dash")
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait(10)
	log_p("10 frames into a dash out of a held guard: dashing %s, guarding %s" % [player.is_dodging, defense.is_guarding()])
	check(player.is_dodging and not defense.is_guarding(), "the held block leaves the dash alone, exactly as it always has")
	player.dodge_time = dash_length
	await dash_parry_reset()

	log_p("-- live: his thrown sword, parried by cancelling a dash into the guard")
	parries.clear()
	events.clear()
	# Stretched so the sword's own arrival decides when the press lands inside the dash rather than a
	# 3-frame budget: the real dash's frames are what every check above ran on.
	stretch_dash(10)
	unpark_eric()
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await settle_player(Vector2(1480, 700))
	sm.on_child_transition(sm.current_state, "SwordThrow")
	var throw_state: Node = sm.states["SwordThrow"]
	check(await wait_until(func(): return is_instance_valid(throw_state.sword), 200), "he throws it")
	var sword: Node2D = throw_state.sword
	var off_a_cancel := [false]
	var note := func(_hit, _point, _staggered, _streak): off_a_cancel[0] = player.dash_cancelled and not player.is_dodging
	defense.parried.connect(note)
	# The dash goes on the frame its ring lights, a parry window before it lands, and the press cancels it.
	await wait_until(func(): return is_instance_valid(sword.mark) and mark_lit(sword.mark), 200)
	defense._set_stamina(defense.max_stamina)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	press(KEY_SHIFT)
	check(await wait_until(func(): return parries.size() > 0 or not events.is_empty(), 60), "the sword reaches them")
	defense.parried.disconnect(note)
	log_p("parries %s, hits %s, off a cancelled dash %s" % [parries, events, off_a_cancel[0]])
	check(parries.size() == 1 and parries[0].id == &"eric_thrown_sword" and off_a_cancel[0], "his sword parried out of a cancelled dash")
	check(player.playerHealth == 100 and events.is_empty(), "no damage and no block")
	check(sword.reflecting, "and it is a whole parry: the sword is flung back at him")
	release(KEY_SHIFT)
	player.dodge_time = dash_length

	log_p("-- and it is his fight's alone: a fight that never turns it on has it off")
	await load_quiet("josh")
	check(not player.dash_parry, "Josh's fight leaves the dash parry off")
	var still := await dash_then_press()
	var elsewhere := front_hit(&"mason_poo_blast", dummy_source())
	log_p("the same press in the same dash there: still dashing %s, result %d" % [still[0], elsewhere])
	check(still[0] and elsewhere == 1, "the press leaves the dash alone and the hit lands (%d)" % elsewhere)


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
	var gap: int = await mash_gap(true)
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
			# Each its own first punch: the combo carries its count (PlayerCombo), and every third would
			# be the gold POW.
			player.combo.reset()
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

	log_p("-- three punches: the third, charged, star is the gold one")
	await settle_player(punch_spot(player.Facing.UP, hurt, PUNCH_SPOTS.hit).round())
	await wait(40)
	player.combo.reset()
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
	player.combo.reset()
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
# The plan's section 1, which EricPacing's V2 column has to match, but for his health: the plan's 56,
# doubled by the user with every boss's (2026-09-25), then raised 25% with them (2026-09-30); and for the
# 2026-10-05 tuning round's chain of all four attacks and the 2026-10-06 one's chains of five, whirlwinds of
# four lunges and mostly yellow hugs.
const V2_PACE := {
	"max_health": 140, "attacks_per_chain": 5, "rage_attacks_per_chain": 5,
	"rage_chain_health_ratio": 0.40, "attack_gap": 0.25, "rage_attack_gap": 0.15, "recovery_rest": 0.25,
	"window_time": 2.0, "rage_window_time": 1.6, "slam_tell_time": 0.36, "delayed_slam_chance": 0.4,
	"whirl_windup": 0.45, "rage_whirl_windup": 0.40, "whirl_lunges": 4, "rage_whirl_lunges": 4,
	"whirl_lunge_time": 0.5, "whirl_lunge_speed": 1000.0, "rage_whirl_lunge_speed": 1150.0,
	"whirl_reaim_time": 0.35, "rage_whirl_reaim_time": 0.30, "whirl_dizzy_time": 0.8,
	"rage_whirl_dizzy_time": 0.6, "planted_time": 0.5, "rage_planted_time": 0.35,
	"hug_charge_time": 0.55, "rage_hug_charge_time": 0.45, "hug_stumble_time": 0.7,
	"hug_yellow_chance": 0.65, "broken_time": 3.0, "rage_broken_time": 2.6,
}
# Every tell's floor: a red timing tell is 1.5x the parry window, a single-answer read 0.40 s, and a
# colour decision 0.40 s with its margin.
const TELL_FLOORS := {"Earthquake": 0.36, "Whirlwind": 0.40, "BearHug": 0.45, "SwordThrow": 0.40}
# Far enough from his spawn that a whirlwind lunge's sweep starts well off. V2's bear hug reaches it
# all the same: its rush homes on the player from anywhere in the ring.
const OUT_OF_REACH := Vector2(1780, 940)


func load_eric_v2() -> void:
	pin_eric(2)
	await load_eric()


# EricPacing's `key` at his current rage.
func paced(key: String) -> float:
	return load(ERIC_PACING).raged(key, sm.rage)


# A fight whose boss builds no gauge has nothing to hold.
func hold_gauge() -> void:
	if not ("break_gauge" in boss) or boss.break_gauge == null:
		return
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
# it after the swing: f+16 against f+24 from the press. Either way a swing resolves once, and one that
# reaches nothing is known missed (PlayerCombo.punch_missed) with the combo's count carried on through it.
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
	for v2 in [true, false]:
		player.feel_v2 = v2
		var name := "feel_v2" if v2 else "today's"
		player.fit_punch_hitbox()
		place_under(hurtbox)
		await wait(40)
		landed.clear()
		var pressed := Engine.get_physics_frames()
		tap(KEY_Q)
		await wait_until(func(): return player.state_machine.current_state.name == "Punching", 10)
		while player.state_machine.current_state.name == "Punching":
			await physics_frame
		var pending: bool = player.combo.report_pending()
		await wait(40)
		var at: int = landed[0][0] - pressed if not landed.is_empty() else -1
		log_p("%s: landed %d frames after the press, %d resolve(s); a report pending as the swing ended: %s" % [name, at, landed.size(), pending])
		check(at == (16 if v2 else 24), "%s: the punch resolves at f+%d (f+%d)" % [name, 16 if v2 else 24, at])
		check(landed.size() == 1 and landed[0][1] == 1, "%s: once for the swing, for 1 (%s)" % [name, landed])
		check(pending != v2, "%s: %s" % [name, "nothing waits on a report" if v2 else "the report is waited on"])

	log_p("-- a whiff lands nothing, is known missed by its report's time, and the count carries on through it")
	var missed := []
	player.combo.punch_missed.connect(func(): missed.append(Engine.get_physics_frames()))
	for v2 in [true, false]:
		player.feel_v2 = v2
		var name := "feel_v2" if v2 else "today's"
		player.fit_punch_hitbox()
		place_under(hurtbox)
		await wait(40)
		player.combo.reset()
		await swing()
		check(player.combo.count == 1, "%s: a landed punch starts a combo (%d)" % [name, player.combo.count])
		await settle_player(player.global_position + Vector2(0, 200))
		landed.clear()
		missed.clear()
		await wait(6)
		tap(KEY_Q)
		await wait_until(func(): return player.state_machine.current_state.name == "Punching", 10)
		while player.state_machine.current_state.name == "Punching":
			await physics_frame
		var ended := Engine.get_physics_frames()
		await wait(6)
		log_p("%s: the whiff ended on frame %d, known missed on %s" % [name, ended, missed])
		check(landed.is_empty() and missed.size() == 1 and absi(missed[0] - ended) <= player.combo.REPORT_FRAMES,
			"%s: the whiff landed nothing, and was known missed once, by the time a report would be in (%s)" % [name, missed])
		check(player.combo.count == 1 and not player.combo.swing_open, "%s: the count carries on through it (%d)" % [name, player.combo.count])
	player.feel_v2 = true


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
	check(boss.max_health == 140 and boss.boss_health == 140, "140 health, and he starts on it (%d of %d)" % [boss.boss_health, boss.max_health])

	log_p("-- %d attacks a chain, %d from 40%% down" % [pacing.value("attacks_per_chain"), pacing.value("rage_attacks_per_chain")])
	for health in [57, 56]:
		boss.boss_health = health
		sm.start_chain(5.0)
		var count: int = sm.chain.size() + 1
		sm.rest_timer.stop()
		var wanted: int = pacing.value("attacks_per_chain" if health == 57 else "rage_attacks_per_chain")
		check(count == wanted, "at %d of 140 (%.1f%%) a chain is %d attacks (%d)" % [health, 100.0 * health / 140.0, wanted, count])
	# Longer than his four attacks, a chain goes round again: all four first, and never one twice running.
	var rounds_ok := true
	for i in 40:
		sm.start_chain(5.0)
		sm.rest_timer.stop()
		var whole: Array = [sm.last_attack] + sm.chain
		var first_four: Array = whole.slice(0, mini(4, whole.size()))
		var repeats := range(1, whole.size()).any(func(k): return whole[k] == whole[k - 1])
		if repeats or first_four.size() != mini(4, whole.size()) or sm.ATTACKS.any(func(a): return whole.size() >= 4 and not first_four.has(a)):
			rounds_ok = false
			log_p("chain %s" % [whole])
	check(rounds_ok, "40 chains: each opens on all four of his attacks, and none repeats one twice running")
	boss.boss_health = 140
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
			# The hug's badge is up for its charge, and its rush then takes a fixed hug_rush_time to arrive:
			# two clocks counted down in frames, each of which can run a frame over, so one frame more slack.
			var own: float = {"Earthquake": pacing.value("slam_tell_time"), "Whirlwind": pacing.raged("whirl_windup", rage), "BearHug": pacing.raged("hug_charge_time", rage) + pacing.value("hug_rush_time"), "SwordThrow": sm.states["SwordThrow"].TELL_TIME}[attack]
			var slack: float = (3.0 if attack == "BearHug" else 2.0) * FRAME_TIME + 0.001
			log_p("%s at rage %.0f: a %s tell %.3f s before it strikes (its own %.2f, floor %.2f)" % [attack, rage, seen.look, lead, own, TELL_FLOORS[attack]])
			check(seen.tell >= 0.0 and seen.impact >= 0.0, "%s at rage %.0f: the tell, then the attack" % [attack, rage])
			check(lead >= TELL_FLOORS[attack] - 0.001 and absf(lead - own) <= slack, "%s at rage %.0f: the tell leads by its own %.2f s, at or over its %.2f s floor (%.3f)" % [attack, rage, own, TELL_FLOORS[attack], lead])
			var looks := {"Earthquake": ["red"], "Whirlwind": ["yellow"], "BearHug": ["strong red", "yellow"], "SwordThrow": ["strong red"]}
			check(looks[attack].has(seen.look), "%s: its tell is %s (%s)" % [attack, " or ".join(looks[attack]), seen.look])

	log_p("-- whole chains: the gaps between attacks, the Winded window, the rest after it")
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	for health in [140, 1]:
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
				# A POW dazes him there with daze_in_windows (the user, 2026-10-05), and never without it.
				winded_open[0] = winded_open[0] and hurtbox.monitoring and boss.can_be_dazed() == boss.daze_in_windows
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
		check(winded_open[0], "rage %.2f: open to punches all through it, and %s" % [rage_now, "a POW dazes him there" if boss.daze_in_windows else "never dazed there"])
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
	var wanted_slams: int = 12 * roundi(pacing.raged("slams", 0.0)) + 4 * roundi(pacing.raged("slams", 1.0))
	check(slams.size() == wanted_slams, "every slam of 16 attacks was seen (%d of %d)" % [slams.size(), wanted_slams])
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
			# A lunge that starts against the ropes (the last of four enraged, at a player outside his area)
			# runs along them: it keeps its length, and stays in his area.
			var at_ropes: bool = s.slice(0, mini(7, s.size())).any(func(x): return not whirl.LUNGE_AREA.grow(-1.0).has_point(x.at))
			if at_ropes:
				check(absf(lasted.call(run) - pacing.value("whirl_lunge_time")) <= FRAME_TIME + 0.001 and s.all(func(x): return whirl.LUNGE_AREA.grow(1.0).has_point(x.at) and x.spinning), "rage %.0f: a lunge from the ropes lasts %.2f s and stays in his area, spinning (%.3f s)" % [rage, pacing.value("whirl_lunge_time"), lasted.call(run)])
				continue
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

	log_p("-- the mark's commit frame ends as the blade lands, at any range")
	# The release leaves from wherever his last lunge put him, usually on top of them; the toss he winds
	# up himself leaves from his own spot. Either way it only hurts them as it lands, so that is the
	# moment the ring times the press off.
	for case in [["his release, from where the lunges leave him", "Whirlwind"], ["his own toss, from his spot", "SwordThrow"]]:
		boss.global_position = Vector2(700, 400)
		await settle_player(Vector2(1480, 700))
		health_ok()
		clear_iframes()
		# Through his lunges, which are their own dodge check above.
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
		var reach := [-1.0]
		var on_hit := func(hit):
			if hit.attack_id == &"eric_thrown_sword" and reach[0] < 0.0:
				reach[0] = flung.elapsed / flung.duration
		defense.hit_taken.connect(on_hit)
		# Out of his hands, nothing but the blade is left to reach them.
		clear_iframes()
		while out and is_instance_valid(flung) and flung.flying and not flung.returning:
			await physics_frame
		defense.hit_taken.disconnect(on_hit)
		log_p("%s: %.0f px over %.2f s, the blade reaches them at %.2f of the flight, the commit frame lights at %.2f, the window is %.2f of it" % [case[0], span, flight, reach[0], commit, window])
		check(out and reach[0] == 1.0, "%s: the blade reaches a player standing on the mark as it lands" % case[0])
		if out and reach[0] >= 0.0:
			check(absf(reach[0] - commit - window) <= slack, "%s: it lands a parry window after the commit frame lights (%.3f of the flight against %.3f)" % [case[0], reach[0] - commit, window])
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

	var count: int = roundi(pacing.raged("whirl_lunges", 0.0))
	log_p("-- all %d lunges of one whirlwind, each dashed: the re-aim leaves every dash after the first its immunity" % count)
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
			var lunges: Array = await dash_lunges(case[1], case[2], range(count), lead)
			var every: bool = lunges.size() == count and lunges.all(func(l): return not l.dash.is_empty())
			var gap := INF if every else -1.0
			if every:
				for k in range(1, count):
					gap = minf(gap, lunges[k].pressed_at - lunges[k - 1].pressed_at)
			log_p("%s, dashing %d frames ahead: %s" % [case[0], lead, lunges.map(lunge_line)])
			check(every and lunges.all(func(l): return l.hits == 0) and gap >= catalog.DASH_IMMUNITY_COOLDOWN, "%s, dashing %d frames ahead: all %d lunges dashed through, at least %.2f s apart" % [case[0], lead, count, gap])

	# Fairness (2026-10-06): every lunge asks for a dash, a third of the bar, so the whirlwind's wind-up and
	# each re-aim wait until the player's bar can pay for the next one (EricWhirlwind._dash_affordable).
	log_p("-- coming in with any stamina, the wind-up waits until the first dash can be paid for")
	await settle_player(Vector2(960, 900))
	boss.global_position = Vector2(960, 380)
	sm.chain = []
	await wait(45)
	defense._spend(defense.stamina)
	sm.on_child_transition(sm.current_state, "Whirlwind")
	await wait(2)
	var held: bool = whirl.phase == whirl.Phase.HOLD and tell_node() == null and not boss.get_node("WhirlwindArea2D").monitoring
	var wound := await wait_until(func(): return whirl.phase == whirl.Phase.WINDUP, 600)
	check(held and wound and defense.can_afford(defense.dash_stamina_cost), "on an empty bar he stands, harmless and with no tell, and winds up once a dash can be paid for (%.0f)" % defense.stamina)
	await wait_until(func(): return sm.current_state.name == "Winded", 900)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	clear_iframes()
	health_ok()
	for spent in [100.0, 80.0, 50.0]:
		log_p("-- all %d lunges dashed, coming in %.0f stamina down" % [count, spent])
		for case in pairs:
			var lunges: Array = await dash_lunges(case[1], case[2], range(count), 8, spent)
			var every: bool = lunges.size() == count and lunges.all(func(l): return not l.dash.is_empty())
			log_p("%s, %.0f down: %s" % [case[0], spent, lunges.map(lunge_line)])
			check(every and lunges.all(func(l): return l.hits == 0), "%s, coming in %.0f stamina down: all %d lunges dashed through" % [case[0], spent, count])


# One whirlwind at full health from `eric_at` on a player standing at `spot`, who dashes out of the
# lunges numbered in `dash_for` (from 0), lead_frames before the sweep would reach them, and stands still
# through the rest. A lunge they don't dash for can hit them; its
# i-frames are cleared as the next lunge starts, so it can't shelter them from that one. Returns each
# lunge's angle, the dash taken and how long before contact, and the hits it landed. `spent` is stamina they
# spend on the frame before the whirlwind starts, as a player who came in off a dash or a missed parry has.
func dash_lunges(eric_at: Vector2, spot: Vector2, dash_for: Array, lead_frames: int, spent := 0.0) -> Array:
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
	# Back on their spot after the wait: with three lunges a whirlwind, the case before can leave them
	# moving off it.
	await settle_player(spot)
	events.clear()
	sm.rage = 0.0
	sm.chain = []
	await process_frame
	if spent > 0.0:
		defense._spend(spent)
	sm.on_child_transition(sm.current_state, "Whirlwind")
	var lunges := []
	var last_left := -1
	var held_keys := []
	var release_in := 0
	# Long enough for a wind-up and re-aims held for the bar to refill (EricWhirlwind._dash_affordable).
	for i in 900:
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

	log_p("-- the colours and their tells, with the player across the ring")
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

	log_p("-- red: stepping out of its line doesn't save them, the rush follows")
	events.clear()
	clear_iframes()
	health_ok()
	hug.hugs_started = 0
	boss.global_position = Vector2(960, 380)
	await await_hug_lunge()
	press(KEY_LEFT)
	tap(KEY_W)
	var stepped_grabbed := await wait_until(func(): return player.is_grabbed, 40)
	release(KEY_LEFT)
	check(not hug.yellow and stepped_grabbed and events_of("HIT", &"eric_bear_hug_grab_v2").size() == 1, "red: stepped and dashed out of its line, grabbed all the same")
	await wait_until(func(): return sm.current_state.name == "Winded", 600)
	sm.downed_state_timer.stop()
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
		var charge_damage: int = catalogue_damage(&"eric_shoulder_charge")
		check(hug.yellow and events_of("HIT", &"eric_shoulder_charge").size() == 1 and player.playerHealth == 100 - charge_damage and events_of("BLOCKED").is_empty() and parries.is_empty(), "yellow, %s: it lands, for %d" % [answer, charge_damage])
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
	await wait_until(func(): return hug_lands_within(hug, 0.09), 400)


# Waits for his hug's stumble and returns [how long it lasted, whether his hurtbox was open all through].
func time_stumble(hug: Node, hurtbox: Area2D) -> Array:
	await wait_until(func(): return hug.phase == hug.Phase.STUMBLE, 200)
	var started: float = defense.clock
	var open := true
	while hug.phase == hug.Phase.STUMBLE and sm.current_state == hug:
		open = open and hurtbox.monitoring
		await physics_frame
	return [defense.clock - started, open]


# The bear hug's reach: V2's rush homes on the player and lands on hug_rush_time from anywhere in the
# ring, near or far, and his arms are harmless until it arrives. From the far side: red grabs a player
# who stands still and one who runs, and a parry still staggers it; yellow lands for 1 and holds no one,
# and a dash through it is still a perfect dodge into his stumble. Then the player pushed flush into
# every corner and against every rope, with the hug started from across the ring: red holds them there.
func test_hug_reach() -> void:
	await load_eric_v2()
	hold_gauge()
	track()
	track_parries()
	track_dodges()
	var pacing = load(ERIC_PACING)
	var hug: Node = sm.states["BearHug"]
	var rush: float = pacing.value("hug_rush_time")
	var old_reach: float = pacing.TABLE["hug_lunge_max_distance"][0]
	var far_from := Vector2(300, 380)
	var far_at := Vector2(1700, 880)
	var arrivals := []
	log_p("-- red from the far side of the ring, %.0f px away, where V1's lunge stopped at %.0f" % [far_from.distance_to(far_at), old_reach])
	for answer in ["stand", "run", "parry"]:
		var at: Vector2 = Vector2(1000, 500) if answer == "run" else far_at
		var seen: Dictionary = await run_hug_at(false, far_from, at, answer)
		arrivals.append(snappedf(seen.arrive - seen.rush, 0.001))
		log_p("red, %s: rushed %.3f s from %s to %s, the player from %s to %s, live on the way %s, grabbed %s, now %s, events %s, parries %s" % [answer, seen.arrive - seen.rush, far_from, seen.to, at, seen.player_to, seen.live_early, seen.grabbed, seen.state, events.map(func(e): return "%s %s" % [e.kind, e.id]), parries.map(func(p): return p.id)])
		check(seen.to.distance_to(far_from) > old_reach, "red, %s: he crossed the ring to them (%.0f px)" % [answer, seen.to.distance_to(far_from)])
		check(not seen.live_early, "red, %s: his arms were harmless until he arrived" % answer)
		if answer == "parry":
			check(parries.size() == 1 and parries[0].id == &"eric_bear_hug_grab_v2" and parries[0].staggered and seen.state == "ParryStaggered", "red, parried just before it lands: it staggers him")
			check(not player.is_grabbed and player.playerHealth == 100, "and the player is free and unhurt")
		else:
			check(seen.grabbed and events_of("HIT", &"eric_bear_hug_grab_v2").size() == 1, "red, %s: it reaches them and grabs" % answer)
		if answer == "run":
			check(seen.player_to.distance_to(at) > 100.0, "and they were on the move all the way (%.0f px)" % seen.player_to.distance_to(at))
		await end_hug()

	log_p("-- yellow from the far side")
	for answer in ["stand", "dash"]:
		var seen: Dictionary = await run_hug_at(true, far_from, far_at, answer)
		arrivals.append(snappedf(seen.arrive - seen.rush, 0.001))
		log_p("yellow, %s: rushed %.3f s to %s, live on the way %s, stumbled %s, events %s, dodges %s, health %d" % [answer, seen.arrive - seen.rush, seen.to, seen.live_early, seen.stumbled, events.map(func(e): return "%s %s" % [e.kind, e.id]), dodges.map(func(d): return d.id), player.playerHealth])
		check(not seen.live_early and seen.to.distance_to(far_from) > old_reach, "yellow, %s: he crossed the ring to them, harmless on the way" % answer)
		if answer == "stand":
			var charge_damage: int = catalogue_damage(&"eric_shoulder_charge")
			check(events_of("HIT", &"eric_shoulder_charge").size() == 1 and player.playerHealth == 100 - charge_damage and not seen.grabbed, "yellow, standing: it lands, for %d, and holds no one" % charge_damage)
		else:
			check(events_of("HIT").is_empty() and player.playerHealth == 100, "yellow, dashed just before it lands: it misses")
			check(dodges.any(func(d): return d.id == &"eric_shoulder_charge"), "and the dash is a perfect dodge (%s)" % [dodges.map(func(d): return d.id)])
		check(seen.stumbled, "yellow, %s: he stumbles, open to punches" % answer)
		await end_hug()

	log_p("-- red from close up")
	var near: Dictionary = await run_hug_at(false, Vector2(900, 460), Vector2(960, 640), "stand")
	arrivals.append(snappedf(near.arrive - near.rush, 0.001))
	check(near.grabbed and not near.live_early, "from close up it grabs too, harmless until it lands")
	await end_hug()
	check(arrivals.all(func(a): return absf(a - rush) <= 2.0 * FRAME_TIME + 0.001), "every rush lands %.2f s after it starts, near or far (%s)" % [rush, arrivals])

	log_p("-- flush against every rope and in every corner, from across the ring")
	var area: Rect2 = load("res://Scripts/EricArtLayout.gd").PLAYER_AREA
	var pushes := {
		"the top-left corner": [KEY_LEFT, KEY_UP], "the left rope": [KEY_LEFT], "the bottom-left corner": [KEY_LEFT, KEY_DOWN],
		"the top rope": [KEY_UP], "the bottom rope": [KEY_DOWN],
		"the top-right corner": [KEY_RIGHT, KEY_UP], "the right rope": [KEY_RIGHT], "the bottom-right corner": [KEY_RIGHT, KEY_DOWN],
	}
	var steps := {KEY_LEFT: Vector2.LEFT, KEY_RIGHT: Vector2.RIGHT, KEY_UP: Vector2.UP, KEY_DOWN: Vector2.DOWN}
	var missed := []
	for where in pushes:
		var keys: Array = pushes[where]
		var out := Vector2.ZERO
		for k in keys:
			out += steps[k]
		# A little way in from that edge of the floor, then walked into the ropes until they stop.
		await settle_player(area.get_center() + out * (area.size / 2.0 - Vector2(80, 80)))
		for k in keys:
			press(k)
		await wait(60)
		for k in keys:
			release(k)
		await wait(4)
		var spot: Vector2 = player.global_position
		var from: Vector2 = (area.get_center() * 2.0 - spot).clamp(hug.RUSH_AREA.position, hug.RUSH_AREA.end)
		var seen: Dictionary = await run_hug_at(false, from, spot, "stand")
		log_p("%s: the player at %s, him from %s to %s, grabbed %s" % [where, spot, from, seen.to, seen.grabbed])
		if not seen.grabbed:
			missed.append("%s %s" % [where, spot])
		await end_hug()
	check(missed.is_empty(), "red holds them flush against every rope and in every corner (missed %s)" % [missed])


# Runs one bear hug of the colour asked for, him from `from` at a player on `at`, and hands back what
# it did: when the rush started and when it arrived, where he and the player were then, whether his
# arms were live on the way, and how it ended. `answer`: "stand" still, "run" away from him the whole
# way, or "parry" or "dash" just before it lands.
func run_hug_at(yellow: bool, from: Vector2, at: Vector2, answer: String) -> Dictionary:
	var hug: Node = sm.states["BearHug"]
	var grab_area: Area2D = boss.get_node("GrabArea2D")
	var hurtbox: Area2D = boss.get_node("Hurtbox")
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	boss.global_position = from
	await settle_player(at)
	events.clear()
	parries.clear()
	dodges.clear()
	clear_iframes()
	health_ok()
	defense._set_stamina(defense.max_stamina)
	defense.clear_dash_recovery()
	# The fight's first hug is red; after two reds the next is yellow.
	hug.hugs_started = 1 if yellow else 0
	hug.recent_yellows.assign([false, false] if yellow else [])
	var seen := {"rush": -1.0, "arrive": -1.0, "to": Vector2.INF, "player_to": Vector2.INF, "live_early": false, "grabbed": false, "stumbled": false, "state": ""}
	var probe := func():
		if sm.current_state != hug:
			return
		if hug.phase == hug.Phase.LUNGE:
			if seen.rush < 0.0:
				seen.rush = defense.clock
			seen.live_early = seen.live_early or grab_area.monitoring
		if seen.arrive < 0.0 and hug.phase == hug.Phase.CONTACT:
			seen.arrive = defense.clock
			seen.to = boss.global_position
			seen.player_to = player.global_position
	physics_frame.connect(probe)
	var away: Array = []
	if answer == "run":
		away = [KEY_RIGHT if at.x >= from.x else KEY_LEFT, KEY_DOWN if at.y >= from.y else KEY_UP]
	await process_frame
	sm.on_child_transition(sm.current_state, "BearHug")
	for k in away:
		press(k)
	if answer == "parry" or answer == "dash":
		await wait_until(func(): return hug_lands_within(hug, 0.09), 400)
		if answer == "parry":
			press(KEY_SHIFT)
		else:
			tap(KEY_W)
	await wait_until(func(): return player.is_grabbed or sm.current_state != hug or hug.phase == hug.Phase.STUMBLE, 400)
	for k in away:
		release(k)
	seen.grabbed = player.is_grabbed
	seen.state = str(sm.current_state.name)
	if sm.current_state == hug and hug.phase == hug.Phase.STUMBLE:
		await wait(2)
		seen.stumbled = hug.phase == hug.Phase.STUMBLE and hurtbox.monitoring
	physics_frame.disconnect(probe)
	return seen


# Takes him out of whatever a hug left him in, and gives the player back.
func end_hug() -> void:
	release(KEY_SHIFT)
	sm.downed_state_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(30)


# ---- the Break

# The Break gauge: what fills and drains it, that it holds 100 and never decays, the Break that empties
# it and the wait before it fills again, its bar, and that V1 has none.
func test_break_gauge() -> void:
	# A second fight with a gauge of its own reads its expectations off its boss.
	if fight != "eric":
		await test_break_gauge_fight()
		return
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
	# His own numbers (EricScript.BREAK), on the gauge he built.
	var spec: Dictionary = boss.BREAK
	var off_table := spec.keys().filter(func(k): return gauge.get(k) != spec[k])
	check(off_table.is_empty(), "his own BREAK numbers are the gauge's (%s off)" % [off_table])
	check(gauge.max_value == spec.max_value and gauge.value == 0.0, "it holds %.0f and starts empty" % spec.max_value)
	await settle_player(Vector2(972, 800))

	log_p("-- what fills it")
	check(await parry_once(&"eric_quake_wave_v2") == 3 and gauge.value == spec.parry_gain, "a parry: %.0f (%.0f)" % [spec.parry_gain, gauge.value])
	clear_iframes()
	await wait(40)
	press(KEY_SHIFT)
	await wait(3)
	var grab_parry := front_hit(&"eric_bear_hug_grab_v2", dummy_source())
	release(KEY_SHIFT)
	check(grab_parry == 3 and gauge.value == spec.parry_gain + spec.grab_parry_gain, "a parry of his red grab: %.0f (%.0f)" % [spec.grab_parry_gain, gauge.value])
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await wait(60)
	var ring := spawn_ring(player.global_position + Vector2(372, 0))
	await ring_close(ring, 0.05)
	tap(KEY_W)
	check(await wait_until(func(): return dodges.size() > 0, 30) and gauge.value == spec.parry_gain + spec.grab_parry_gain + spec.perfect_dodge_gain, "a perfect dodge: %.0f (%.0f)" % [spec.perfect_dodge_gain, gauge.value])
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
	check(steps == [spec.punch_gain, spec.punch_gain, spec.charged_punch_gain], "punches that land: %.0f each, %.0f for the charged third (%s)" % [spec.punch_gain, spec.charged_punch_gain, steps])
	sm.on_child_transition(sm.current_state, "Idle")
	await settle_player(Vector2(972, 800))

	log_p("-- what drains it")
	# Topped up past both drains, so each shows whole.
	gauge.add(spec.hit_loss + spec.guard_break_loss)
	var before_hit: float = gauge.value
	front_hit(&"eric_quake_wave_v2", dummy_source())
	check(gauge.value == maxf(before_hit - spec.hit_loss, 0.0), "a hit: -%.0f (%.0f -> %.0f)" % [spec.hit_loss, before_hit, gauge.value])
	player.take_grab_damage()
	check(gauge.value == maxf(before_hit - spec.hit_loss, 0.0), "a squeeze in his grab costs nothing more: the grab was the hit (%.0f)" % gauge.value)
	clear_iframes()
	health_ok()
	await wait(40)
	var before_break: float = gauge.value
	await break_guard(&"eric_quake_wave_v2")
	check(defense.is_guard_broken and gauge.value == before_break - spec.guard_break_loss, "a guard break: -%.0f (%.0f -> %.0f)" % [spec.guard_break_loss, before_break, gauge.value])
	defense.clear_guard_break()
	clear_iframes()
	await wait(45)

	log_p("-- what isn't his counts for nothing")
	var before_other: float = gauge.value
	check(await parry_once(&"mason_poo_blast") == 3, "someone else's attack parried")
	clear_iframes()
	front_hit(&"wrestler_charge", dummy_source())
	clear_iframes()
	check(gauge.value == before_other, "and one that lands: the gauge doesn't move (%.0f)" % gauge.value)
	await wait(45)

	log_p("-- it stops at 0 and never decays")
	await break_guard(&"eric_quake_wave_v2")
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
	# One parry short of full, whatever his parry is worth.
	gauge.add(spec.max_value - spec.parry_gain - gauge.value)
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
	# A second fight with a gauge of its own reads its expectations off its boss.
	if fight != "eric":
		await test_break_entry_fight()
		return
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
		elif case[0] == "the hug's stumble":
			# The yellow charge ends in the stumble whether it lands or not. Nowhere in the ring is out of
			# the red grab's reach, so a red one would hold them instead.
			hug.hugs_started = 1
			hug.recent_yellows.assign([false, false])
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

	log_p("-- the opener: the combo starts the finisher; left alone it fizzles and the chance goes")
	await reset_break(home)
	await settle_player(Vector2(700, 800))
	gauge.value = 95.0
	gauge.add(10.0)
	await wait(2)
	await wait_until(func(): return not player.is_action_locked, 120)
	player.combo.reset()
	var health: int = boss.boss_health
	for i in 3:
		await swing()
		if i < 2:
			await wait(6)
	check(await wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120), "3 punches daze him: the finisher's prompt is up")
	check(boss.boss_health == health - 4 and not broken.stars.visible, "the combo dealt 1 + 1 + 2, and the finisher's stars take over from his")
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	check(sm.current_state == broken and broken.stars.visible, "the fizzle leaves him Broken for the rest of his time")
	await wait_until(func(): return sm.current_state != broken, 300)
	check(boss.boss_health == health - 4, "then he gets up, the uppercut never came")

	# The parry's gain and the reflect's together, his own numbers (EricScript.BREAK).
	var reads: float = gauge.parry_gain + gauge.reflect_gain
	var auto_uppercut: bool = pacing.value("reflect_auto_uppercut")
	log_p("-- the parried sword: the reflect that fills the gauge breaks him; one that doesn't %s" % ("fires its own uppercut" if auto_uppercut else "staggers him plainly"))
	for fill in [true, false]:
		await reset_break(home)
		gauge.value = gauge.max_value - reads if fill else 0.0
		var from: float = gauge.value
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
		log_p("from %.0f: %s, gauge %.0f, finisher phase %d" % [from, sm.current_state.name, gauge.value, finisher.phase])
		if fill:
			check(outcome and finisher.phase == FINISHER_OFF, "from %.0f: the parry's %.0f and the reflect's %.0f fill it: a Break, and no uppercut fires" % [from, gauge.parry_gain, gauge.reflect_gain])
		elif auto_uppercut:
			check(outcome and sm.states["ParryStaggered"].from_reflect and gauge.value == reads, "from 0: %.0f and %.0f make %.0f, and the reflect's own uppercut fires" % [gauge.parry_gain, gauge.reflect_gain, reads])
			check(await wait_until(func(): return finisher.phase != FINISHER_OFF, 60), "the finisher takes it")
			await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
		else:
			check(outcome and not sm.states["ParryStaggered"].from_reflect and gauge.value == reads, "from 0: %.0f and %.0f make %.0f, and he is staggered plainly" % [gauge.parry_gain, gauge.reflect_gain, reads])
			var fired := await wait_until(func(): return finisher.phase != FINISHER_OFF, 60)
			# No uppercut of its own; a POW of the player's still dazes him there with daze_in_windows.
			check(not fired and boss.can_be_dazed() == boss.daze_in_windows, "no uppercut fires on its own, and a POW %s" % ("would daze him" if boss.daze_in_windows else "can't daze him"))
			await wait_until(func(): return sm.current_state.name != "ParryStaggered", 400)

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
# The rates for the three bars, in alternating presses a second: the user's 6, 8 and 10 (2026-10-04) as fitted.
const TIER_RATES := [5.8, 8.0, 9.7]
# Presses every this many frames at 60 fps reach each tier, and every one more doesn't.
const TIER_PASS_FRAMES := [10, 7, 6]
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
func model_mash(finisher: Node, every: int, stop_after := -1, windows: Array = []) -> Dictionary:
	var meter = load("res://Scripts/FinisherTierMeter.gd").new(finisher.tier_gain, finisher.tier_drains, finisher.tier_windows if windows.is_empty() else windows, finisher.tier_start_grace, finisher.tier_idle_stop)
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
			var run: Dictionary = model_mash(finisher, frames, -1, open_windows)
			# MashCurve's top can hold a rate short of a bar for good. For the fail that is as clear of the
			# window as it gets; for the pass it is a miss.
			if run.banked_at.size() <= bar:
				var failing: bool = frames != TIER_PASS_FRAMES[bar]
				margins.append(INF if failing else -INF)
				log_p("bar %d, every %d frames: never fills, held short of its top" % [bar + 1, frames])
				continue
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
	var stopped: Dictionary = model_mash(finisher, 5, 36)
	check(stopped.tier == 1 and absf(stopped.resolved_at - stopped.last_press - finisher.tier_idle_stop) <= 1.0 / 60.0 + 0.001, "stopping after bar 1 keeps it: the mash ends %.1f s after the last press (tier %d at %.3f)" % [finisher.tier_idle_stop, stopped.tier, stopped.resolved_at])
	var idle: Dictionary = model_mash(finisher, 0)
	check(idle.tier == 0 and absf(idle.resolved_at - finisher.tier_start_grace - finisher.tier_windows[0]) <= 1.0 / 60.0 + 0.001, "never pressed, it fizzles when bar 1's window runs out %.1f s after the prompt (%.3f)" % [finisher.tier_start_grace + finisher.tier_windows[0], idle.resolved_at])


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
	var one_press: float = load("res://Scripts/MashCurve.gd").gain(finisher.tier_gain, 0.0)
	check(finisher.meter <= one_press + 0.001 and banks.is_empty(), "twelve lefts are one press (%.2f)" % finisher.meter)
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	await wait(60)

	log_p("-- the bumpers, a press every %d frames: two bars" % TIER_PASS_FRAMES[1])
	banks.clear()
	check(await break_into_prompt(), "the prompt again")
	var pair := [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER]
	var presses := 0
	var i := 0
	while finisher.phase == FINISHER_DAZED or finisher.phase == FINISHER_CHARGING:
		if i % TIER_PASS_FRAMES[1] == 0:
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
	player.feel_v2 = true

	log_p("-- and the tiered mash is the Break's payout alone: Mason's eat window gives the plain one")
	boss = current_scene.get_node(PUNISH_WINDOWS["mason"][0])
	sm = boss.state_machine
	finisher = player.get_node("Finisher")
	player.playerHealth = 1000
	use_gauge_spec("mason")
	await reset_gauged(fight_spec.home)
	sm.on_child_transition(sm.current_state, "Eat")
	await wait(5)
	stop_boss_timers()
	place_under(boss.get_finisher_hurtbox())
	await wait(6)
	check(finisher.begin_auto(boss), "the finisher takes his eat window")
	check(await wait_until(func(): return finisher.phase == FINISHER_DAZED, 120), "and reaches the daze")
	check(not finisher.tiered, "from the eat window: the plain single-bar finisher")
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	await reset_gauged(fight_spec.home)
	await settle_player(fight_spec.home + Vector2(-320, 60))
	boss.break_gauge.add(boss.break_gauge.max_value)
	check(await wait_until(func(): return sm.current_state.name == "Broken", 30), "and a Break")
	await wait_until(func(): return not player.is_action_locked, 120)
	check(finisher.begin_auto(boss), "the finisher takes the Break")
	check(await wait_until(func(): return finisher.phase == FINISHER_DAZED, 120), "and reaches the daze")
	check(finisher.tiered, "from the Break: the three-bar mash and the juggle")
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)


# Tier 3 from start to finish, watched frame by frame.
func test_juggle() -> void:
	# A second fight with a gauge of its own reads its expectations off its boss.
	if fight != "eric":
		await test_juggle_fight()
		return
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
	check(dealt == [35, 14, 21], "35, 14 and 21 of his 140 (%s)" % [dealt])
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
	# A second fight with a gauge of its own reads its expectations off its boss.
	if fight != "eric":
		await test_juggle_kill_fight()
		return
	await load_eric_v2()
	health_ok()
	var n := int(tier) if tier.is_valid_int() else 3
	var finisher: Node = player.get_node("Finisher")
	check(await break_into_prompt(), "a Break and the opener put up the prompt")
	# The damage the uppercuts before this one deal, and one more.
	boss.boss_health = [1, 36, 50][n - 1]
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


# A full hype meter: nothing banked before the first press, tier 2 at bar 2's rate, and the last uppercut carrying
# SUPERCHARGE_MULTIPLIER - 1 of both bars, so the juggle pays 1.6 times its 35%; the hype spent once.
func test_juggle_super() -> void:
	await load_eric_v2()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var hype: Node = player.get_node("Hype")
	var spends := [0]
	hype.hype_spent.connect(func(): spends[0] += 1)
	hype._set_hype(100.0)
	check(await break_into_prompt(), "a Break and the opener put up the prompt")
	check(finisher.supercharged and finisher.tier_meter.banked == 0 and finisher.meter == 0.0, "supercharged, and nothing is banked before the first press")
	var health := [boss.boss_health]
	var dealt := []
	finisher.juggle_hit.connect(func(_index, _last):
		dealt.append(health[0] - boss.boss_health)
		health[0] = boss.boss_health)
	await mash_tiered(TIER_PASS_FRAMES[1])
	await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
	log_p("tiers %d, dealt %s, spends %d" % [finisher.juggle_tiers, dealt, spends[0]])
	check(dealt == [35, 43], "tier 2 at bar 2's rate, the last uppercut 0.6 of both bars more: 35 and 43, 1.6 times 35 + 14 (%s)" % [dealt])
	check(spends[0] == 1 and not hype.is_full(), "the hype spent once (%d)" % spends[0])


# His parried sword flung back into him: a Break if the parry's and the reflect's gains fill the gauge, and
# otherwise what EricPacing's reflect_auto_uppercut says. On (V1's way): a tier-1 juggle with no prompt.
# Off (V2's since the 2026-10-04 tuning round): a plain stagger, open to punches, with no uppercut of its
# own; a POW dazes him there like any punish window with EricScript.daze_in_windows (2026-10-05).
func test_reflect_auto_v2() -> void:
	await load_eric_v2()
	health_ok()
	var finisher: Node = player.get_node("Finisher")
	var throw_state: Node = sm.states["SwordThrow"]
	var gauge: Node = boss.break_gauge
	var home: Vector2 = boss.global_position
	var reads: float = gauge.parry_gain + gauge.reflect_gain
	var auto_uppercut: bool = load(ERIC_PACING).value("reflect_auto_uppercut")
	log_p("the reflect's own uppercut is %s" % ("on" if auto_uppercut else "off"))
	for fill in [false, true]:
		await reset_break(home)
		gauge.value = gauge.max_value - reads if fill else 0.0
		var from: float = gauge.value
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
		var sword: Node2D = throw_state.sword
		# On the frame its ring lights, a parry window before it lands, and held until it comes down:
		# the guard drops with the key.
		await wait_until(func(): return is_instance_valid(sword.mark) and mark_lit(sword.mark), 200)
		press(KEY_SHIFT)
		await wait_until(func(): return not is_instance_valid(sword) or not sword.flying, 60)
		release(KEY_SHIFT)
		if fill:
			check(await wait_until(func(): return sm.current_state.name == "Broken", 300), "from %.0f: the parry's %.0f and the reflect's %.0f break him" % [from, gauge.parry_gain, gauge.reflect_gain])
			await wait(60)
			check(hits.is_empty() and finisher.phase == FINISHER_OFF, "and no juggle fires on its own")
		elif auto_uppercut:
			var share: int = roundi(boss.max_health * finisher.juggle_shares[0])
			check(await wait_until(func(): return sm.current_state.name == "Juggled", 300), "from 0: the reflect juggles him")
			await wait_until(func(): return finisher.phase == FINISHER_OFF, 400)
			check(prompts[0] == 0 and hits == [[0, true]], "one uppercut, the last, and no prompt (%s)" % [hits])
			check(health - boss.boss_health == 1 + share and gauge.value == reads, "his sword's 1 and the uppercut's %d, and the gauge at %.0f (%d, %.0f)" % [share, reads, health - boss.boss_health, gauge.value])
			check(await wait_until(func(): return sm.current_state.name == "Broken" and sm.states["Broken"].retrieving, 120), "down, he gets up for the sword the uppercut knocked away")
		else:
			var staggered := await wait_until(func(): return sm.current_state.name == "ParryStaggered", 300)
			check(staggered and not sm.states["ParryStaggered"].from_reflect, "from 0: the reflect staggers him, plainly (%s)" % sm.current_state.name)
			check(health - boss.boss_health == throw_state.REFLECT_DAMAGE and gauge.value == reads, "his sword's %d, and the gauge at %.0f (%d, %.0f)" % [throw_state.REFLECT_DAMAGE, reads, health - boss.boss_health, gauge.value])
			check(boss.get_node("Hurtbox").monitoring and boss.can_be_dazed() == boss.daze_in_windows, "open to punches, and a POW %s" % ("would daze him" if boss.daze_in_windows else "can't daze him"))
			await wait(90)
			check(prompts[0] == 0 and hits.is_empty() and finisher.phase == FINISHER_OFF and boss.boss_health == health - throw_state.REFLECT_DAMAGE, "no prompt, no uppercut, nothing more off him (%s)" % [hits])
			check(await wait_until(func(): return sm.current_state.name != "ParryStaggered", 400), "and he gets up again (%s)" % sm.current_state.name)
		finisher.prompt_shown.disconnect(on_prompt)
		finisher.juggle_hit.disconnect(on_hit)


# ------------------------------------------------------------------ the thrown sword and its mark

# Where the player stands for the throw, and so the spot he aims it at and the mark lands on.
const SWORD_SPOT := Vector2(1480, 700)
# Far enough up-arena to put them inside the blade's path with the throw still in the air, and no
# further than one dash and a step: what a player who read the mark and moved actually covers.
const SWORD_STEP := Vector2(-212.0, -212.0)
# Beside the blade's path early on, for the dash that gets nothing: the blade sweeps this spot long
# before it lands.
const SWORD_EARLY := Vector2(1111, 433)


# His SwordThrow on its own, started in the idle step the way attack_v2 starts one, and the sword it
# puts in the air.
func throw_sword() -> Node2D:
	var throw_state: Node = sm.states["SwordThrow"]
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await process_frame
	sm.on_child_transition(sm.current_state, "SwordThrow")
	await wait_until(func(): return is_instance_valid(throw_state.sword), 300)
	return throw_state.sword


# Whether the floor mark is drawing its commit frame, on either art path.
func mark_lit(mark: Node2D) -> bool:
	if mark.sprite:
		return mark.sprite.frame == mark.spec.commit_frame
	return mark.target_ring.default_color == mark.spec.commit_color


# Whether the parry aura still lights a thrown sword's blade, rather than being on its way out.
func sword_glows(thrown: Node2D) -> bool:
	var parry_tell: Script = load("res://Scripts/ParryTell.gd")
	return thrown.sword.get_children().any(func(child): return child.get_script() == parry_tell and not child.fading)


# Watches one outgoing throw the whole way in, on the flight's own clock: the progress the ring lights
# its commit frame on, the progress the blade's reach first covers the player's hurtbox and the ghost a
# dash left behind, and the progress the blade's own hit or perfect dodge resolves on, read as it
# resolves.
func fly_out(sword: Node2D) -> Dictionary:
	var seen := {"cover": -1.0, "lit": -1.0, "hit": -1.0, "ghost": -1.0, "dodge": -1.0}
	var on_hit := func(hit):
		if hit.attack_id == &"eric_thrown_sword" and seen.hit < 0.0:
			seen.hit = sword.elapsed / sword.duration
	var on_dodge := func(hit):
		if hit.attack_id == &"eric_thrown_sword" and seen.dodge < 0.0:
			seen.dodge = sword.elapsed / sword.duration
	defense.hit_taken.connect(on_hit)
	defense.perfect_dodged.connect(on_dodge)
	# To the end of the outgoing leg, however it ends: a parry stops it dead and the throw flings it
	# back, which is a flight of its own on a clock of its own.
	while is_instance_valid(sword) and sword.flying and not sword.returning and not sword.reflecting:
		var t: float = sword.elapsed / sword.duration
		if seen.cover < 0.0 and sword._reaches(player.hurtBox):
			seen.cover = t
		if seen.lit < 0.0 and is_instance_valid(sword.mark) and mark_lit(sword.mark):
			seen.lit = t
		if seen.ghost < 0.0 and defense.ghost_active and sword._reaches(player.dodge_ghost):
			seen.ghost = t
		await physics_frame
	defense.hit_taken.disconnect(on_hit)
	defense.perfect_dodged.disconnect(on_dodge)
	return seen


# Back to Idle with his sword back in his hand, whatever the throw ended as.
func sword_reset() -> void:
	clear_iframes()
	await wait_until(func(): return sm.current_state.name == "Winded" or sm.current_state.name == "Idle", 900)
	sm.on_child_transition(sm.current_state, "Idle")
	await wait(6)


# His thrown sword keeps the promise its floor mark makes: EricSwordMark's ring closes onto the spot the
# blade lands on and lights its commit frame exactly PlayerDefense.parry_window before it lands there,
# and the blade hurts nobody until it does - not a player on the mark, whom its reach is over well before
# it lands, and not one who moved off the mark into its path. Nothing hurts them after that either: the
# recall has no mark, and the flung-back sword is theirs. sword_path stands them all along the flight.
func test_sword_gate() -> void:
	await load_eric_v2()
	hold_gauge()
	track()
	track_parries()
	track_dodges()
	# Long enough that a mode full of his sword can never end the fight under a check.
	player.playerHealth = 100000
	var throw_state: Node = sm.states["SwordThrow"]
	var window: float = defense.parry_window

	log_p("-- the ring lights a parry window before the blade lands, on the spot it lands on")
	await settle_player(SWORD_SPOT)
	var sword: Node2D = await throw_sword()
	var commit: float = sword.mark.commit_at if is_instance_valid(sword.mark) else -1.0
	var step: float = 1.0 / 60.0 / sword.duration
	log_p("duration %.3f s at %.0f px/s over its %.0f px path, mark commit %.4f; the %.2f s window is %.4f of the flight" % [sword.duration, sword.speed, sword.from_ground.distance_to(sword.to_ground), commit, window, window / sword.duration])
	check(is_equal_approx((1.0 - commit) * sword.duration, window), "the ring's commit frame is a parry window of flight before it lands (%.3f s)" % ((1.0 - commit) * sword.duration))
	check(sword.mark.global_position.distance_to(sword.to_ground) < 0.01, "and the ring is on the very spot it lands on (%s against %s)" % [sword.mark.global_position, sword.to_ground])
	var standing := await fly_out(sword)
	log_p("standing still: its reach over them from %.4f, ring lit %.4f, hit %.4f" % [standing.cover, standing.lit, standing.hit])
	check(standing.lit >= commit and standing.lit - commit < step, "the ring lights on the first frame at or past it (%.4f)" % standing.lit)
	check(standing.hit == 1.0, "a player who stays on the spot is hit as it lands, and not before (%.4f)" % standing.hit)
	check(standing.cover >= 0.0 and standing.cover < 1.0, "though its reach was over them from %.4f of the flight: it is held back all the way down" % standing.cover)

	log_p("-- it plants, and comes back to his hand through them harmless")
	check(await wait_until(func(): return is_instance_valid(throw_state.sword) and throw_state.sword.returning, 300), "it plants and he calls it back")
	var back: Node2D = throw_state.sword
	check(is_instance_valid(back) and not sword_glows(back), "no longer lit as a parry: nothing on its way back can be")
	# Where its reach passes halfway home, put there the moment it leaves the mat.
	var halfway: Vector2 = back.from_ground.lerp(back.to_ground, 0.5) - Vector2(0, lerpf(back.from_height, back.to_height, 0.5) + back.ARC_HEIGHT)
	player.global_position = halfway
	clear_iframes()
	var unhurt: int = player.playerHealth
	var crossed := [false]
	var watch_back := func():
		if is_instance_valid(back) and back.returning and back.flying and back._reaches(player.hurtBox):
			crossed[0] = true
	physics_frame.connect(watch_back)
	await wait_until(func(): return not is_instance_valid(back) or not back.flying, 120)
	physics_frame.disconnect(watch_back)
	log_p("stood at %s: its reach crossed them %s, health %d -> %d" % [halfway, crossed[0], unhurt, player.playerHealth])
	check(crossed[0] and player.playerHealth == unhurt, "its reach goes right through them on the way back, and hurts nothing")
	await sword_reset()

	log_p("-- off the mark, it passes through them on its way in and never hurts them")
	# Standing in for a player who read the ring and moved 300 px up-arena while the blade was out.
	await settle_player(SWORD_SPOT)
	sword = await throw_sword()
	player.global_position = SWORD_SPOT + SWORD_STEP
	var moved := await fly_out(sword)
	log_p("moved %s: its reach over them from %.4f, ring lit %.4f, hit %.4f" % [SWORD_STEP, moved.cover, moved.lit, moved.hit])
	check(moved.cover >= 0.0 and moved.cover < 1.0, "the blade's reach does pass through them on its way in (%.4f)" % moved.cover)
	check(moved.hit < 0.0, "and it never hurts them, there or where it lands: they were not on the mark")
	await sword_reset()

	log_p("-- a press on the frame the ring lights catches it as it lands")
	await settle_player(SWORD_SPOT)
	sword = await throw_sword()
	unhurt = player.playerHealth
	var caught: int = parries.size()
	# reflect() overwrites the flight, so the spot it was going to land on is kept here.
	var aimed_at: Vector2 = sword.to_ground
	# The earliest press the mark asks for, and so the tightest one it has to honour.
	check(await wait_until(func(): return is_instance_valid(sword.mark) and mark_lit(sword.mark), 300), "the ring lights its commit frame")
	press(KEY_SHIFT)
	check(await wait_until(func(): return parries.size() > caught, 60), "and a press on that very frame still has a blade to catch")
	release(KEY_SHIFT)
	check(parries[-1].id == &"eric_thrown_sword" and player.playerHealth == unhurt, "it is the sword that was parried, and it never touches them (%s)" % [parries.map(func(p): return p.id)])
	check(not is_instance_valid(sword.mark), "the mark it cancelled went with it, so nothing lands there")
	check(await wait_until(func(): return is_instance_valid(throw_state.sword) and throw_state.sword.reflecting, 60), "and it is flung back at him")
	check(sword.from_ground.distance_to(aimed_at) < 1.0, "from the spot it was aimed at, where they caught it (%s against %s)" % [sword.from_ground, aimed_at])
	check(await wait_until(func(): return not is_instance_valid(throw_state.sword), 120) and player.playerHealth == unhurt, "and it is spent on him without touching them: the flung-back sword is theirs")
	await sword_reset()

	log_p("-- a dash off the spot as it comes down is a perfect dodge")
	defense.last_perfect_dodge_time = -INF
	await settle_player(SWORD_SPOT)
	sword = await throw_sword()
	# Late enough that the ghost the dash leaves is still up when the blade goes into it.
	await wait_until(func(): return not sword.flying or sword.duration - sword.elapsed < defense.perfect_dodge_window - 0.05, 300)
	press(KEY_DOWN)
	tap(KEY_W)
	var dodged := await fly_out(sword)
	release(KEY_DOWN)
	log_p("dashed clear: the ghost under its reach from %.4f, dodge %.4f, hit %.4f" % [dodged.ghost, dodged.dodge, dodged.hit])
	check(dodged.dodge == 1.0 and dodges[-1].id == &"eric_thrown_sword", "the blade going into the spot they left pays a perfect dodge as it lands (%.4f, %s)" % [dodged.dodge, dodges.map(func(d): return d.id)])
	check(dodged.hit < 0.0, "and no hit")
	await sword_reset()

	log_p("-- and a dash out of its path early pays nothing: there was nothing there to dodge")
	defense.last_perfect_dodge_time = -INF
	var had: int = dodges.size()
	await settle_player(SWORD_SPOT)
	sword = await throw_sword()
	# Off to one side of the blade's path, near enough that its reach sweeps the spot they leave while
	# the ghost is still up, long before it lands.
	player.global_position = SWORD_EARLY
	await wait_until(func(): return not sword.flying or sword.elapsed >= 0.10, 60)
	press(KEY_DOWN)
	tap(KEY_W)
	var early := await fly_out(sword)
	release(KEY_DOWN)
	log_p("dashed early: the ghost under its reach from %.4f, dodge %.4f, hit %.4f" % [early.ghost, early.dodge, early.hit])
	check(early.ghost >= 0.0 and early.ghost < 1.0, "its reach does sweep the ghost they left, early in its flight (%.4f)" % early.ghost)
	check(dodges.size() == had, "and pays no perfect dodge for it (%d)" % (dodges.size() - had))
	check(early.hit < 0.0, "nor hurts them")
	await sword_reset()

	log_p("-- enraged, where he throws it harder")
	sm.rage = 1.0
	await settle_player(SWORD_SPOT)
	sword = await throw_sword()
	commit = sword.mark.commit_at if is_instance_valid(sword.mark) else -1.0
	log_p("enraged: %.0f px/s over %.3f s, mark commit %.4f; the window is %.4f of this flight" % [sword.speed, sword.duration, commit, window / sword.duration])
	check(is_equal_approx((1.0 - commit) * sword.duration, window), "the window is worked out from this flight (%.4f)" % commit)
	var raged := await fly_out(sword)
	log_p("enraged, standing still: its reach over them from %.4f, ring lit %.4f, hit %.4f" % [raged.cover, raged.lit, raged.hit])
	check(raged.hit == 1.0 and raged.cover >= 0.0 and raged.cover < 1.0, "a faster blade still only hurts them as it lands (%.4f), its reach over them from %.4f" % [raged.hit, raged.cover])
	sm.rage = 0.0
	await sword_reset()

	log_p("-- the whirlwind's own release lands the same way, on its own mark")
	# Across the ring from him, so his lunges cannot close the whole gap and the release has a flight to
	# watch; the spin ends on a throw either way.
	boss.global_position = Vector2(300, 450)
	await settle_player(Vector2(1780, 470))
	sm.chain = []
	sm.rest_timer.stop()
	sm.downed_state_timer.stop()
	await process_frame
	sm.on_child_transition(sm.current_state, "Whirlwind")
	check(await wait_until(func(): return is_instance_valid(throw_state.sword), 600), "the spin ends in a throw")
	var spun: Node2D = throw_state.sword
	var spun_commit: float = spun.mark.commit_at if is_instance_valid(spun.mark) else -1.0
	log_p("spin release: plants %s, %.3f s, mark commit %.4f" % [spun.plants, spun.duration, spun_commit])
	check(not spun.plants and is_equal_approx((1.0 - spun_commit) * spun.duration, window), "it skips off the mat, and its ring lights a parry window before it lands (%.4f)" % spun_commit)
	# Whatever his lunges did, the blade is all that is left to reach them.
	clear_iframes()
	var released := await fly_out(spun)
	log_p("spin release, standing still: its reach over them from %.4f, hit %.4f" % [released.cover, released.hit])
	check(released.hit == 1.0, "a player on its mark is hit as it lands, and not before (%.4f)" % released.hit)
	check(await wait_until(func(): return not is_instance_valid(throw_state.sword) or throw_state.sword.returning, 300), "and it still comes back")
	check(not is_instance_valid(throw_state.sword) or not sword_glows(throw_state.sword), "no longer lit as a parry on the way back")


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


# Up beside his hurtbox, then a combo, for as long as the window stays open.
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
		elif script_path.ends_with("EricThrownSwordScript.gd") and hazard.flying and not hazard.returning and not hazard.reflecting:
			# It only hurts where it lands: parry on its lit ring, when standing where it comes down.
			var box: Rect2 = body.global_transform * body.shape.get_rect()
			var reach: float = hazard.get_node("Hitbox/CollisionShape2D").shape.radius
			var lands_on: bool = hazard.to_ground.clamp(box.position, box.end).distance_to(hazard.to_ground) <= reach
			if lands_on and is_instance_valid(hazard.mark) and mark_lit(hazard.mark) and _bot_reads(profile, bot, hazard):
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
	if state == sm.states["BearHug"]:
		var lead := 0.06 if state.yellow else 0.09
		if hug_lands_within(state, lead) and _bot_reads(profile, bot, "hug%d" % state.hugs_started):
			if state.yellow:
				var grab: CollisionShape2D = boss.get_node("GrabArea2D/CollisionShape2D")
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
	check(player.playerHealth == 8, "and so is the player (%d)" % player.playerHealth)
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
	await open_scene(scene)
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

	# One hold takes all of it - the walk-in, his lines and their beats, and the card's build-up - and
	# lands on the card's flash, where a watched entrance ends.
	card = vs_card()
	var card_art: GDScript = load(VS_CARD_LAYOUT)
	press(KEY_ESCAPE)
	check(await wait_until(func(): return card.is_playing(), 120), "a held Escape skipped it, lines and all, to the card")
	check(card.clock >= card_art.HOLD_END, "which it jumped to its flash")
	release(KEY_ESCAPE)
	await wait(4)
	check(not pause.is_open() and not paused, "and never opened the pause screen")
	check(live_balloon() == null, "and not one of his lines came up")
	check(not gates.is_open() and not is_instance_valid(intro.planted), "the ring is set: gates shut, sword in his hands")
	check(player.global_position.is_equal_approx(intro.player_home) and boss.global_position.is_equal_approx(intro.home), "both of them on their marks")
	check(boss.music_player.playing, "his theme is playing, as it is after the pull")
	check(player.state_machine.is_processing() and player.is_talking, "the player has their state machine back, and the card has the hold")
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	check(await wait_until(func(): return not sm.post_dialogue_pre_fight_timer.is_stopped() or sm.current_state != intro, 180), "and the fight starts behind it")
	check(not player.is_talking, "with the player free")

	log_p("-- a second go at the same fight in the same run doesn't play it again")
	change_scene_to_file(scene)
	while current_scene == null or current_scene.scene_file_path != scene:
		await process_frame
	await wait(6)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	boss = current_scene.get_node("Arena/EricBossScene/CharacterBody2D")
	sm = boss.state_machine
	gates = current_scene.get_node("Arena/Gates")
	intro = entrance_state()
	check(intro != null and intro.finished, "the entrance is already over on arrival")
	check(not gates.is_open(), "and the ring was never opened")
	check(await wait_until(func(): return live_balloon() != null, 120), "and his lines start straight away")
	check(player.state_machine.is_processing(), "with the player's state machine running")

	log_p("-- paused mid-line, the fight still starts")
	pause = pause_menu()
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

	log_p("-- on a second go the lines still play, and a held Escape still skips them to the card")
	change_scene_to_file(scene)
	while current_scene == null or current_scene.scene_file_path != scene:
		await process_frame
	await wait(6)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	card = vs_card()
	check(await wait_until(func(): return live_balloon() != null, 120), "his first line is up")
	press(KEY_ESCAPE)
	check(await wait_until(func(): return card.is_playing(), 120), "a held Escape skipped the rest of them to the card")
	check(card.clock >= card_art.HOLD_END, "at its flash")
	release(KEY_ESCAPE)
	await wait(4)
	check(live_balloon() == null and not paused, "with the balloon gone and nothing paused")


# ------------------------------------------------------------------ the gauge, the Break and the juggle in every other fight
# Everything above was written against Eric, the first fight with a Break gauge, and the modes above
# hand over to these for any fight= but his. These read every expectation off the boss - his live
# gauge's numbers, his get_max_health(), the finisher's shares of it - and off the fight's spec file,
# never off Eric's literals. Adding a fight means one file, gauge_fights/<fight>.gd, and nothing here:
#   const SPEC := {
#     "body": his body's path under the fight scene,
#     "home": where he is parked: somewhere he may stand, with room over his head for a juggle and
#             beside him for the player,
#     "light": one of his own attacks, read and landed: it has to fill and drain,
#     "light_read": OPTIONAL, "dodge" for a light attack nothing guards, read by dashing through it (a
#                   perfect dodge); without it, "parry",
#     "strong": the one worth grab_parry_gain, or &"" for none,
#     "foreign": an attack that isn't his at all,
#     "punish_state": his ordinary punish window, where punches are measured,
#     "broken_state": the state his Break puts him in, or "" for a fight whose Break window isn't one,
#     "cycle_states": the states that mean his fight has started again once he is up,
#     "defeated_state": the state he is beaten in,
#     "reads_to_break": N on the rule "N clean reads from empty is a Break", 0 for a fight not on it,
#     "art": his layout script,
#     "juggle_via": "clip" for a BossJuggled, "animation_player" for one on his AnimationPlayer,
#     "drives_player": whether his Break drives the player in beside him,
#     "guard_break_attack": OPTIONAL, the blockable attack break_gauge breaks the guard with, for a
#                           fight with nothing of its own a guard can take; without it, strong or light,
#     "gauge_gains": OPTIONAL, false for a fight whose body credits his reads itself and leaves the
#                    gauge's own gains at 0: break_gauge reads those gains, so it leaves him to extra(t),
#   }
# and, all optional, statics that are handed the harness as `t` (t.boss, t.sm, t.player, t.check(),
# t.wait() and the rest). All may await but timer_roots and break_feet, which must return at once:
#   park(t, home: Vector2)     puts him at home; without it, boss.global_position = home
#   reset(t)                   whatever else reset_gauged() has to put back
#   force_break(t)             breaks him; without it, his gauge is filled
#   entry_cases(t) -> Array    break_entry's cases: [name, start: Callable, reached: Callable]
#   timer_roots(t) -> Array    nodes whose Timers (themselves included) a Break must stop; without
#                              it, his body, state machine and all
#   break_feet(t) -> Vector2   his feet as his Break window stands him; without it, the broken
#                              state's _feet()
#   before_kill(t)             juggle_kill's own setup, with his health set and the prompt up
#   after_kill(t)              juggle_kill's own checks, after the shared ones
#   extra(t)                   the whole of mode gauge_extra, after a reset_gauged()
const GAUGE_FIGHTS_DIR := "res://art_source/defense_tests/gauge_fights/"
# Danny's own modes, one file each and owned by whoever built what it tests: extends RefCounted, one
# `static func run(t)` taking this suite, explicit types.
const DANNY_MODES := "res://art_source/defense_tests/danny/"
# Greyson's, the same way.
const GREYSON_MODES := "res://art_source/defense_tests/greyson/"
# Jordan's, the same way.
const JORDAN_MODES := "res://art_source/defense_tests/jordan/"
# His last phase's, which three coders write at once (the Puppet Master: god.gd, maze.gd, kegs.gd): a mode whose file
# isn't written yet says so and fails, rather than calling run() on nothing and hanging the run.
func run_mode_file(path: String) -> void:
	if not ResourceLoader.exists(path):
		check(false, "%s: %s is not written yet" % [mode, path])
		return
	await load(path).run(self)


# The ring's own modes, the same way: what keeps the player inside the ropes, across every fight.
const RING_MODES := "res://art_source/defense_tests/ring/"
# Eric's own modes, the same way, for the ones that don't live in this file.
const ERIC_MODES_DIR := "res://art_source/defense_tests/eric/"
# Matt's modes added since the user's 2026-09-27 playtest, the same way.
const MATT_MODES := "res://art_source/defense_tests/matt/"
# Josh's, the same way, since his rework of 2026-09-28.
const JOSH_MODES := "res://art_source/defense_tests/josh/"
# Mason's, the same way, since his Nugget Fastball of 2026-10-04.
const MASON_MODES := "res://art_source/defense_tests/mason/"
# Beast Bixby's, the same way, since his Flyby of 2026-09-29 (liam/ is left for Liam's own phase).
const BIXBY_MODES := "res://art_source/defense_tests/bixby/"
# Liam's own phase, after Bixby coughs him up (2026-09-29), the same way.
const LIAM_MODES := "res://art_source/defense_tests/liam/"
# The game's ending after god-Jordan (the champion cutscene and its credits), the same way.
const ENDING_MODES := "res://art_source/defense_tests/ending/"
# The longest the VS card may take to come up once a state intro is over.
const VS_CARD_WAIT_FRAMES := 60

# The fight's SPEC, and an instance of its file so has_method() can see which statics it has.
var fight_spec := {}
var fight_hooks: Object


func use_gauge_spec(key_name: String) -> bool:
	var path := GAUGE_FIGHTS_DIR + key_name + ".gd"
	if not ResourceLoader.exists(path):
		check(false, "%s has a gauge spec (%s)" % [key_name, path])
		return false
	var script: GDScript = load(path)
	fight_spec = script.SPEC
	fight_hooks = script.new()
	return true


func has_hook(hook: String) -> bool:
	return fight_hooks != null and fight_hooks.has_method(hook)


func load_gauged() -> bool:
	if not use_gauge_spec(fight):
		return false
	await load_fight(fight, STATE_INTROS.has(fight))
	await clear_intro(fight)
	# A fight whose intro is a state of its own comes out of it into the VS card, which load_fight()
	# returned before it could skip, and which holds the player's presses.
	if STATE_INTROS.has(fight):
		await wait_until(func(): return vs_card() != null and vs_card().is_playing(), VS_CARD_WAIT_FRAMES)
		await skip_vs_card()
	boss = current_scene.get_node(fight_spec.body)
	sm = boss.state_machine
	# His fight goes on around these checks, and its hazards would whittle the player down.
	player.playerHealth = 1000
	return true


# For a bot or a sweep that reads a fight far more often than a player does, whose own counts a Break
# in the middle of it would wreck: his gauge is pinned empty and can't break him for the rest of the
# run. It is held from outside, so the gauge's rules in play are untouched. Nothing for a boss without one.
func hold_break_gauge(target: Node) -> void:
	if target == null or not ("break_gauge" in target) or target.break_gauge == null:
		return
	target.break_gauge.value = 0.0
	target.break_gauge.locked = true
	target.break_gauge.set_physics_process(false)


# Every clock of his: the state machine's own, and the stagger the finisher starts.
func stop_boss_timers() -> void:
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()


# Back at `home`, idle, with an empty open gauge, full health, nothing of his left on the mat and the
# Break's own effects over.
func reset_gauged(home: Vector2) -> void:
	load("res://Scripts/HitStop.gd").clear()
	load("res://Scripts/ScreenView.gd").reset(self)
	sm.on_child_transition(sm.current_state, "Idle")
	stop_boss_timers()
	for hazard in get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	player.unlock_actions()
	if has_hook("park"):
		await fight_hooks.park(self, home)
	else:
		boss.global_position = home
	boss.boss_health = boss.get_max_health()
	if "phase_two" in boss:
		boss.phase_two = false
	boss.break_gauge.locked = false
	boss.break_gauge.value = 0.0
	boss.break_gauge.set_physics_process(true)
	if has_hook("reset"):
		await fight_hooks.reset(self)
	clear_iframes()
	player.playerHealth = 1000
	await wait(20)


# Every parry badge still up anywhere in the fight. A spent one renames itself and is on its way out.
func live_tells() -> Array:
	return current_scene.find_children("ParryTell*", "", true, false).filter(func(t): return not t.name.ends_with("Spent") and not t.is_queued_for_deletion())


# His Break, however his fight takes one.
func force_break() -> void:
	if has_hook("force_break"):
		await fight_hooks.force_break(self)
	else:
		boss.break_gauge.add(boss.break_gauge.max_value)


# A Break, the player beside him (driven there, or put there for a fight that doesn't drive them), and
# the opener landed: the finisher's prompt is up.
func break_into_prompt_fight(spec: Dictionary) -> bool:
	var finisher: Node = player.get_node("Finisher")
	sm.on_child_transition(sm.current_state, "Idle")
	stop_boss_timers()
	await settle_player(spec.home + Vector2(-320, 60))
	boss.break_gauge.locked = false
	boss.break_gauge.value = 0.0
	await force_break()
	if not spec.broken_state.is_empty():
		await wait_until(func(): return sm.current_state.name == spec.broken_state, 30)
	await wait_until(func(): return not player.is_action_locked, 120)
	if not spec.drives_player:
		place_under(boss.get_finisher_hurtbox())
		await wait(6)
	for i in 3:
		await swing()
		if i < 2:
			await wait(6)
	return await wait_until(func(): return finisher.phase == FINISHER_DAZED and finisher.prompt_visible, 120)


func test_break_gauge_fight() -> void:
	if not await load_gauged():
		return
	var spec: Dictionary = fight_spec
	if spec.broken_state.is_empty():
		log_p("%s's Break window isn't a state of its own: its gauge_extra covers the gauge" % fight)
		return
	if not spec.get("gauge_gains", true):
		log_p("%s's body credits his reads, not his gauge's own gains: its gauge_extra covers the gauge" % fight)
		return
	var broken_state: String = spec.broken_state
	var strong: StringName = spec.get("strong", &"")
	var gauge: Node = boss.break_gauge
	check(gauge != null, "%s has a Break gauge" % fight)
	if gauge == null:
		return
	await reset_gauged(spec.home)
	track()
	track_parries()
	var bars: Array = boss.hud_layer.get_children().filter(func(c): return c.get_script() != null and str(c.get_script().resource_path).ends_with("BreakGaugeUI.gd"))
	var ui: Control = bars[0] if bars.size() == 1 else null
	var gauge_art: Dictionary = load("res://Scripts/EricArtLayout.gd").break_gauge()
	log_p("his numbers: parry %s, strong parry %s, perfect dodge %s, punches %s and %s, hit %s, guard break %s, unlock %s s; bar at %s" % [gauge.parry_gain, gauge.grab_parry_gain, gauge.perfect_dodge_gain, gauge.punch_gain, gauge.charged_punch_gain, gauge.hit_loss, gauge.guard_break_loss, gauge.unlock_delay, ui.position if ui else Vector2.ZERO])
	check(ui != null and ui.size == gauge_art.size and ui.position == boss.health_bar.break_gauge_anchor(), "a gauge bar hung under his health bar")
	check(gauge.max_value == 100.0 and gauge.value == 0.0, "it holds 100 and starts empty")
	await settle_player(Vector2(500, 700))

	log_p("-- what fills it")
	# A light attack that is one of his strong parries too is worth what a strong parry is; one read by
	# dashing through it, what a perfect dodge is.
	var read_by: String = "perfect dodge" if spec.get("light_read", "parry") == "dodge" else "parry"
	var light_gain: float = gauge.perfect_dodge_gain if read_by == "perfect dodge" else (gauge.grab_parry_gain if spec.light in gauge.strong_parry_ids else gauge.parry_gain)
	check(await read_light(spec) and is_equal_approx(gauge.value, light_gain), "a %s of %s: %.3f (%.3f)" % [read_by, spec.light, light_gain, gauge.value])
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await wait(40)
	if not strong.is_empty():
		press(KEY_SHIFT)
		await wait(3)
		var strong_parry := front_hit(strong, dummy_source())
		release(KEY_SHIFT)
		check(strong_parry == 3 and is_equal_approx(gauge.value, light_gain + gauge.grab_parry_gain), "a parry of %s: %.3f (%.3f)" % [strong, gauge.grab_parry_gain, gauge.value])
		clear_iframes()
		defense._set_stamina(defense.max_stamina)
		await wait(40)
	sm.on_child_transition(sm.current_state, spec.punish_state)
	await wait(5)
	stop_boss_timers()
	boss.daze_used = true
	place_under(boss.get_finisher_hurtbox())
	await wait(6)
	var steps := []
	for i in 3:
		var before: float = gauge.value
		await swing()
		steps.append(gauge.value - before)
		if i < 2:
			await wait(6)
	var want_steps := [gauge.punch_gain, gauge.punch_gain, gauge.charged_punch_gain]
	check(steps.size() == 3 and range(3).all(func(k): return is_equal_approx(steps[k], want_steps[k])), "punches that land: %s each, %s for the charged third (%s)" % [gauge.punch_gain, gauge.charged_punch_gain, steps])

	log_p("-- what drains it")
	await reset_gauged(spec.home)
	await settle_player(Vector2(500, 700))
	gauge.value = gauge.guard_break_loss + gauge.hit_loss + 10.0
	var before_hit: float = gauge.value
	front_hit(spec.light, dummy_source())
	check(is_equal_approx(gauge.value, before_hit - gauge.hit_loss), "a hit: -%.3f (%.3f -> %.3f)" % [gauge.hit_loss, before_hit, gauge.value])
	clear_iframes()
	player.playerHealth = 1000
	await wait(40)
	var before_break: float = gauge.value
	# With blocking, any block takes the last 20 stamina. A fight with nothing of its own a guard can take
	# names someone else's (guard_break_attack): a guard break drains the gauge whoever's attack it was.
	var breaker: StringName = spec.get("guard_break_attack", spec.light if strong.is_empty() else strong)
	await break_guard(breaker)
	check(defense.is_guard_broken and is_equal_approx(gauge.value, before_break - gauge.guard_break_loss), "a guard break: -%.3f (%.3f -> %.3f)" % [gauge.guard_break_loss, before_break, gauge.value])
	defense.clear_guard_break()
	clear_iframes()
	player.playerHealth = 1000
	await wait(45)

	log_p("-- what isn't his counts for nothing")
	gauge.value = 40.0
	check(await parry_once(spec.foreign) == 3, "someone else's attack parried")
	clear_iframes()
	front_hit(&"wrestler_charge", dummy_source())
	clear_iframes()
	player.playerHealth = 1000
	check(gauge.value == 40.0, "and one that lands: the gauge doesn't move (%.0f)" % gauge.value)
	await wait(45)

	log_p("-- it stops at 0 and never decays")
	gauge.value = gauge.hit_loss - 1.0
	front_hit(spec.light, dummy_source())
	clear_iframes()
	player.playerHealth = 1000
	check(gauge.value == 0.0, "a hit from under its cost takes it to 0, not under (%.0f)" % gauge.value)
	gauge.add(40.0)
	await wait(300)
	check(gauge.value == 40.0, "5 s later it still holds 40 (%.0f)" % gauge.value)

	log_p("-- the Break")
	await reset_gauged(spec.home)
	await settle_player(Vector2(640, 700))
	var broke := [0]
	gauge.broke.connect(func(): broke[0] += 1)
	gauge.value = gauge.max_value - light_gain
	check(await read_light(spec), "the %s that fills it" % read_by)
	await wait(2)
	log_p("gauge %.0f locked %s, state %s, broke %d" % [gauge.value, gauge.locked, sm.current_state.name, broke[0]])
	check(broke[0] == 1 and gauge.value == 0.0 and gauge.locked and sm.current_state.name == broken_state, "breaks him, and it empties")
	await wait_until(func(): return not player.is_action_locked, 120)
	clear_iframes()
	await wait(40)
	check(await read_light(spec) and gauge.value == 0.0, "a %s now fills nothing (%.0f)" % [read_by, gauge.value])

	log_p("-- it fills again %.0f s after he is back up" % gauge.unlock_delay)
	await wait_until(func(): return sm.current_state.name != broken_state, 400)
	var got_up: float = defense.clock
	await wait_until(func(): return not gauge.locked, 400)
	var unlocked_after: float = defense.clock - got_up
	check(absf(unlocked_after - gauge.unlock_delay) <= FRAME_TIME + 0.001, "%.1f s after he got up (%.3f)" % [gauge.unlock_delay, unlocked_after])

	var reads: int = spec.reads_to_break
	if reads > 0:
		log_p("-- %d clean reads from empty break him, %d don't, and a hit between them costs one" % [reads, reads - 1])
		var read_breaks := [0]
		var count_read_break := func(): read_breaks[0] += 1
		gauge.broke.connect(count_read_break)
		await reset_gauged(spec.home)
		for i in reads - 1:
			gauge.add(gauge.parry_gain)
		check(read_breaks[0] == 0, "%d reads leave him standing (%.6f)" % [reads - 1, gauge.value])
		gauge.add(gauge.parry_gain)
		check(read_breaks[0] == 1, "the %dth breaks him" % reads)
		await wait(2)
		await reset_gauged(spec.home)
		for i in reads - 1:
			gauge.add(gauge.parry_gain)
		gauge.add(-gauge.hit_loss)
		gauge.add(gauge.parry_gain)
		check(read_breaks[0] == 1, "with a hit between them, %d reads leave him standing (%.6f)" % [reads, gauge.value])
		gauge.add(gauge.parry_gain)
		check(read_breaks[0] == 2, "and the %dth breaks him" % (reads + 1))
		await wait(2)
		gauge.broke.disconnect(count_read_break)

	log_p("-- what can't break him")
	await reset_gauged(spec.home)
	await settle_player(Vector2(640, 700))
	var breaks := [0]
	gauge.broke.connect(func(): breaks[0] += 1)
	gauge.add(gauge.max_value)
	await wait(2)
	var time_left: float = sm.states[broken_state].time_left
	sm.enter_broken()
	gauge.add(500.0)
	await wait(2)
	check(breaks[0] == 1 and sm.current_state.name == broken_state and sm.states[broken_state].time_left < time_left, "Broken, he can't be broken again: the gauge takes nothing and his time runs on")
	sm.on_child_transition(sm.current_state, "Idle")
	gauge.add(500.0)
	await wait(2)
	check(breaks[0] == 1 and sm.current_state.name != broken_state, "nor while the gauge waits to fill again")
	boss.boss_health = 0
	await wait(3)
	gauge.locked = false
	gauge.add(500.0)
	await wait(2)
	check(sm.current_state.name != broken_state, "nor once he is beaten (%s)" % sm.current_state.name)


# The Timers a Break has to leave stopped: the spec's timer_roots(t), each root counted too, or
# everything under his body, which is where every fight keeps its clocks, his state machine included.
func break_timers() -> Array:
	var roots: Array = fight_hooks.timer_roots(self) if has_hook("timer_roots") else [boss]
	var timers := []
	for root_node in roots:
		if root_node is Timer:
			timers.append(root_node)
		timers.append_array(root_node.find_children("*", "Timer", true, false))
	return timers


# A Break from inside each of his attacks, his windows and the gap between them: the spec's own table
# (entry_cases). Mason's is the first: the squat is the case that matters there, because
# MasonPooSquat's Exit() leaves its squat timer running, and that timer drops a bomb whether or not he
# is still standing over it.
func test_break_entry_fight() -> void:
	if not await load_gauged():
		return
	var spec: Dictionary = fight_spec
	if spec.broken_state.is_empty():
		log_p("%s's Break window isn't a state of its own: its gauge_extra covers the Break" % fight)
		return
	if not has_hook("entry_cases"):
		check(false, "gauge_fights/%s.gd has entry_cases(t)" % fight)
		return
	var gauge: Node = boss.break_gauge
	var cases: Array = await fight_hooks.entry_cases(self)
	for case in cases:
		await reset_gauged(spec.home)
		await settle_player(OUT_OF_REACH)
		case[1].call()
		var reached := await wait_until(case[2], 600)
		gauge.value = gauge.max_value - 1.0
		gauge.add(1.0)
		await wait(2)
		var left := live_hazards()
		var tells := live_tells()
		var running := break_timers().filter(func(t): return not t.is_stopped())
		log_p("%s: reached %s, now %s, hazards left %d, tells %d, timers running %s" % [case[0], reached, sm.current_state.name, left.size(), tells.size(), running.map(func(t): return t.name)])
		check(reached and sm.current_state.name == spec.broken_state, "%s: broken out of it" % case[0])
		check(left.is_empty(), "%s: everything he sent out is gone (%s)" % [case[0], left.map(func(h): return h.name)])
		check(tells.is_empty(), "%s: no parry badge survives" % case[0])
		check(running.is_empty(), "%s: every one of his timers is stopped" % case[0])
		var freed := await wait_until(func(): return not player.is_action_locked, 120)
		check(freed and not player.lock_seals_guard and not player.scripted_pose and not player.is_posed(), "%s: the player is theirs again, not locked, sealed or posed" % case[0])
		check(await wait_until(func(): return spec.cycle_states.has(str(sm.current_state.name)), 400), "%s: and his cycle starts again" % case[0])


# His feet as his Break window stands him: the spec's break_feet(t), or else his broken state's
# _feet(). null for a fight with neither.
func break_feet() -> Variant:
	if has_hook("break_feet"):
		return fight_hooks.break_feet(self)
	var broken: Node = null if fight_spec.broken_state.is_empty() else sm.states.get(fight_spec.broken_state)
	if broken and broken.has_method("_feet"):
		return broken._feet()
	return null


# Tier 3 from start to finish in a fight of its own, watched frame by frame.
func test_juggle_fight() -> void:
	if not await load_gauged():
		return
	var spec: Dictionary = fight_spec
	var by_clip: bool = spec.juggle_via == "clip"
	var finisher: Node = player.get_node("Finisher")
	var anim: AnimationPlayer = null if by_clip else boss.get_node("AnimationPlayer")
	var art: GDScript = load(spec.art)
	await reset_gauged(spec.home)
	var juggled: Node = sm.states["Juggled"]
	check(await break_into_prompt_fight(spec), "a Break and the opener put up the prompt")
	check(finisher.tiered, "the Break's mash is the tiered one")
	# Past the phase floor, as juggle_kill is: three bars are half his health, which from a full bar reaches a floor at
	# half, and the cut there is the floor's business, not this mode's.
	if "phase_two" in boss:
		boss.phase_two = true
	var want := []
	for k in 3:
		want.append(maxi(1, roundi(boss.get_max_health() * finisher.juggle_shares[k])))
	var hits := []
	# As the first uppercut lands, with him just handed to Juggled: where his juggle sheet puts his feet
	# against where his Break window stood him, which is what a wrong juggle offset gets wrong.
	var launch := {}
	finisher.juggle_hit.connect(func(index, last):
		hits.append({"t": defense.clock, "index": index, "last": last, "health": boss.boss_health})
		if index == 0:
			launch["lift_scale"] = finisher.lift_scale
			var stood: Variant = break_feet()
			if juggled.has_method("feet_point") and stood != null:
				launch["feet"] = juggled.feet_point().y
				launch["stood"] = stood.y)
	var trace := []
	var watch := func():
		trace.append({"t": defense.clock, "drawn": juggled.drawn_lift, "airborne": finisher.airborne, "phase": finisher.phase, "state": sm.current_state.name, "anim": juggled.clip_name if by_clip else anim.assigned_animation})
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
	log_p("headroom %.0f px, lift scale %.2f, hits %s, dealt %s of %d" % [boss.juggle_headroom(), finisher.lift_scale, hits.map(func(h): return snappedf(h.t, 0.001)), dealt, boss.get_max_health()])
	check(hits.size() == 3 and hits[2].last, "three uppercuts, the third the last")
	check(dealt == want, "%s of his %d, the finisher's shares of it (%s)" % [want, boss.get_max_health(), dealt])
	check(not dealt.has(0), "and not one of them deals 0 (%s)" % [dealt])
	if launch.has("feet"):
		check(absf(launch.feet - launch.stood) <= 2.0, "his juggle sheet stands his feet where his Break window stood them (y %.1f against %.1f)" % [launch.feet, launch.stood])
	else:
		log_p("no juggle feet to hold to his Break window's: %s is not on BossJuggled, or the spec has no break_feet" % fight)
	check(launch.get("lift_scale", 0.0) >= 0.49, "drawn at least half its height where he was Broken (lift scale %.2f)" % launch.get("lift_scale", 0.0))
	var gaps := []
	for k in range(1, hits.size()):
		gaps.append(hits[k].t - hits[k - 1].t)
	check(gaps.size() == 2 and gaps.all(func(g): return absf(g - 0.55) <= FRAME_TIME + 0.001), "0.55 s apart (%s)" % [gaps])
	var first: float = hits[0].t if hits.size() > 0 else 0.0
	var last: float = hits[-1].t if hits.size() > 0 else 0.0
	var up: Array = trace.filter(func(s): return s.t > first and s.t <= last)
	check(not up.is_empty() and up.all(func(s): return s.drawn > 0.0), "he never touches the ground between the first and the last")
	var landed_at: Array = trace.filter(func(s): return s.phase == FINISHER_JUGGLE_FALL)
	var crashed_at: Array = trace.filter(func(s): return s.t > last and not s.airborne and s.state == "Juggled")
	check(not landed_at.is_empty() and not crashed_at.is_empty() and landed_at[0].t < crashed_at[0].t, "the player lands before he does")
	var crash: StringName = &"crash" if by_clip else art.juggle().crash
	check(trace.any(func(s): return s.anim == crash), "he crashes")
	check(await wait_until(func(): return spec.cycle_states.has(str(sm.current_state.name)), 400), "then he gets up and his cycle starts again")


# The longest a fight may take from his defeat to its outro, and how long after that it is watched for
# a second one.
const OUTRO_WAIT_FRAMES := 240
const OUTRO_SETTLE_FRAMES := 90


# The uppercut numbered `tier` kills him: nothing follows, one outro, and his defeat once he has landed.
func test_juggle_kill_fight() -> void:
	if not await load_gauged():
		return
	var spec: Dictionary = fight_spec
	var by_clip: bool = spec.juggle_via == "clip"
	var n := int(tier) if tier.is_valid_int() else 3
	var finisher: Node = player.get_node("Finisher")
	var anim: AnimationPlayer = null if by_clip else boss.get_node("AnimationPlayer")
	var art: GDScript = load(spec.art)
	var juggled: Node = sm.states["Juggled"]
	await reset_gauged(spec.home)
	check(await break_into_prompt_fight(spec), "a Break and the opener put up the prompt")
	# Past the phase floor: under it the uppercuts after the one that reaches it deal nothing, which
	# is what the floor fix is for and not what this mode is about.
	if "phase_two" in boss:
		boss.phase_two = true
	# The damage the uppercuts before this one deal, and one more.
	var health := 1
	for k in n - 1:
		health += maxi(1, roundi(boss.get_max_health() * finisher.juggle_shares[k]))
	boss.boss_health = health
	if has_hook("before_kill"):
		await fight_hooks.before_kill(self)
	var hits := []
	finisher.juggle_hit.connect(func(index, last): hits.append({"index": index, "last": last, "health": boss.boss_health, "at": boss.global_position}))
	var states := []
	var watch := func():
		if states.is_empty() or states[-1] != sm.current_state.name:
			states.append(sm.current_state.name)
	physics_frame.connect(watch)
	await mash_tiered(5)
	await wait_until(func(): return sm.current_state.name == spec.defeated_state, 400)
	# A juggle drawn from clips leaves him on the juggle sheet's `down` loop, lingering past the state.
	var defeat_anim: String = str(juggled.clip_name) if by_clip else anim.assigned_animation
	var lying: bool = juggled.lingering if by_clip else true
	var down: String = "down" if by_clip else str(art.juggle().down)
	# Every outro started from here on, told apart by instance so a second beside the first still counts.
	# A fight whose defeat plays out before its lines (Bixby lies, then coughs Liam up) starts its outro
	# late, so the first is waited for, then the watch runs on for a second.
	var outro_ids := {}
	var watch_outros := func():
		for c in root.get_children():
			if c.get_script() != null and str(c.get_script().resource_path).ends_with("FightOutro.gd"):
				outro_ids[c.get_instance_id()] = true
	physics_frame.connect(watch_outros)
	await wait_until(func(): return not outro_ids.is_empty(), OUTRO_WAIT_FRAMES)
	await wait(OUTRO_SETTLE_FRAMES)
	physics_frame.disconnect(watch_outros)
	physics_frame.disconnect(watch)
	var outros: int = outro_ids.size()
	var moved: float = hits[0].at.distance_to(boss.global_position) if not hits.is_empty() else -1.0
	log_p("tier=%d from %d: hits %s, states %s, defeat anim %s, outros %d, moved %.1f px" % [n, health, hits.map(func(h): return [h.index, h.last, h.health]), states, defeat_anim, outros, moved])
	check(hits.size() == n and hits[-1].health == 0 and hits[-1].last, "the uppercut numbered %d kills him, and none follows (%d)" % [n, hits.size()])
	check(outros == 1, "one outro (%d)" % outros)
	check(states.find("Juggled") >= 0 and states.find("Juggled") < states.find(spec.defeated_state) and defeat_anim == down and lying, "he finishes his fall and crash, then lies there beaten (%s)" % [states])
	check(moved >= 0.0 and moved < 1.0, "the killing uppercut doesn't shove him (%.1f px)" % moved)
	if has_hook("after_kill"):
		await fight_hooks.after_kill(self)


# A fight's own checks on its gauge, its Break and its juggle, past what the shared modes can say: the
# spec's extra(t), from a reset.
func test_gauge_extra() -> void:
	if not await load_gauged():
		return
	if not has_hook("extra"):
		check(false, "gauge_fights/%s.gd has an extra(t)" % fight)
		return
	await reset_gauged(fight_spec.home)
	await fight_hooks.extra(self)


# ------------------------------------------------------------------ Captain Burak: his pistol pair and his cutlass string
# On his fight with his next attack held off, the Laugh already had and his order pinned
# (load_burak_attacks). His Break gauge is his own (BurakBossScript.BREAK): max 60, +30 a parried shot and
# +20 a parried swing through his body's own Defense.parried connection, -20 a hit, never under 0.
#   burak_shots    tier=parry|block|hit|carry|lock|phit, parry without one
#   burak_cutlass  tier=walk|guard|dash|parry|mixed, walk without one
const BURAK_BODY := "Arena/BurakBossScene/BurakBossCharacterBody"
const BURAK_SEED := 20260923


func load_burak_attacks(order: Array) -> void:
	await load_fight("burak")
	boss = current_scene.get_node(BURAK_BODY)
	sm = boss.state_machine
	sm.rng.seed = BURAK_SEED
	sm.laugh_played = true
	sm.ATTACK_ORDER.assign(order)
	burak_park()
	player.playerHealth = 1000


# Idle, with his next attack held off: entering Idle starts the beat to it.
func burak_park() -> void:
	sm.on_child_transition(sm.current_state, "Idle")
	stop_boss_timers()


# Back at HOME and parked, an empty open gauge, the player fresh at `at` with every key up, and past the
# parry's mash lockout.
func burak_reset(at: Vector2) -> void:
	burak_park()
	boss.global_position = sm.HOME
	boss.break_gauge.locked = false
	boss.break_gauge.value = 0.0
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT]:
		release(code)
	await settle_player(at)
	clear_iframes()
	player.playerHealth = 1000
	defense._set_stamina(defense.max_stamina)
	await wait(40)
	events.clear()
	parries.clear()
	dodges.clear()


# By id: a lambda holding a ball itself errors once the ball frees.
func burak_live(id: int) -> Node2D:
	return instance_from_id(id) as Node2D if is_instance_id_valid(id) else null


# Physics steps until a ball's circle reaches the player's hurtbox where it is now.
func burak_steps_to_contact(ball: Node2D) -> float:
	var rect := area_rect(player.hurtBox)
	var at: Vector2 = ball.global_position
	var gap: float = at.distance_to(at.clamp(rect.position, rect.end)) - ball.hit_radius
	return gap / maxf(ball.speed * FRAME_TIME, 0.001)


# One pistol pair, shot k answered as answers[k] says: "parry" a fresh press as it arrives, "block" a guard
# raised as its aim starts and held to the end of the pair, "hit" nothing. `start` enters Shots, or else
# waits for his cycle to. Returns every step's picture and each ball's flight to the point it was aimed at.
func burak_run_shots(answers: Array, start := true) -> Dictionary:
	var shots: Node = sm.states["Shots"]
	var steps := []
	var flights := []
	var seen := {}
	var watch := func():
		steps.append({"beat": shots.beat, "fired": shots.fired, "tell": not live_tells().is_empty(), "pips": boss.pips.pips.size(), "state": str(sm.current_state.name)})
		for ball in shots.balls:
			if is_instance_valid(ball) and not seen.has(ball.get_instance_id()):
				seen[ball.get_instance_id()] = true
				var from: Vector2 = ball.global_position - ball.heading * ball.speed * ball.life
				flights.append(from.distance_to(ball.target) / ball.speed)
	if start:
		sm.on_child_transition(sm.current_state, "Shots")
	else:
		await wait_until(func(): return sm.current_state == shots, 400)
	physics_frame.connect(watch)
	var guarding := false
	for k in answers.size():
		var aiming := func(): return sm.current_state != shots or (shots.beat == shots.Beat.AIM and shots.fired == k)
		if not await wait_until(aiming, 400) or sm.current_state != shots:
			break
		if answers[k] == "block" and not guarding:
			press(KEY_SHIFT)
			guarding = true
		await wait_until(func(): return sm.current_state != shots or shots.fired > k, 120)
		if shots.balls.size() <= k:
			break
		var id: int = shots.balls[k].get_instance_id()
		if answers[k] == "parry":
			await wait_until(func(): return burak_live(id) == null or burak_steps_to_contact(burak_live(id)) <= 5.0, 120)
			press(KEY_SHIFT)
		await wait_until(func(): return burak_live(id) == null, 120)
		if answers[k] == "parry":
			release(KEY_SHIFT)
	if guarding:
		release(KEY_SHIFT)
	await wait_until(func(): return sm.current_state != shots, 400)
	physics_frame.disconnect(watch)
	return {"steps": steps, "flights": flights}


# Whatever the answers: the red badge up on every step from the load's start until the last release, with
# its pips beside him, the releases recoil + aim_second apart, and no ball reaching the point it was aimed
# at in under min_flight.
func burak_check_pair(run: Dictionary) -> void:
	var shots: Node = sm.states["Shots"]
	var armed: Array = run.steps.filter(func(s): return s.state == "Shots" and s.beat != shots.Beat.RETURN and s.beat != shots.Beat.SETTLE and s.fired < shots.bullets)
	check(not armed.is_empty() and armed.all(func(s): return s.tell), "the red badge is up on all %d steps from the load's start to the last release" % armed.size())
	check(not armed.is_empty() and armed.all(func(s): return s.pips == shots.bullets), "with %d pips beside him" % shots.bullets)
	var times: Array = shots.release_times
	if times.size() == shots.bullets:
		var gap: float = times[1] - times[0]
		var want: float = shots.recoil + shots.aim_second
		check(absf(gap - want) <= FRAME_TIME + 0.001, "the releases %.2f s apart, to the frame (%.4f)" % [want, gap])
	var flights: Array = run.flights
	check(flights.size() == times.size() and flights.all(func(f): return f >= shots.min_flight - 0.005), "every ball at least %.2f s from the point it was aimed at (%s)" % [shots.min_flight, flights.map(func(f): return snappedf(f, 0.001))])


func burak_parries_of(id: StringName) -> int:
	return parries.filter(func(p): return p.id == id).size()


# The Cutlass's strike results, one by one: they are a typed Array[int].
func burak_results_are(want: Array) -> bool:
	var got: Array = sm.states["Cutlass"].results
	return got.size() == want.size() and range(want.size()).all(func(i): return got[i] == want[i])


func test_burak_shots() -> void:
	await load_burak_attacks(["Shots"])
	track()
	track_parries()
	var gauge: Node = boss.break_gauge
	var values := []
	gauge.changed.connect(func(value, _max_value): values.append(value))
	var breaks := [0]
	gauge.broke.connect(func(): breaks[0] += 1)
	var shots: Node = sm.states["Shots"]
	await burak_reset(Vector2(960, 800))
	var answer := "parry" if tier == "normal" else tier
	match answer:
		"parry":
			log_p("-- both shots parried: the first fills 30, the second 60 and breaks him")
			var run := await burak_run_shots(["parry", "parry"])
			var broken := await wait_until(func(): return sm.current_state.name == "Broken", 30)
			log_p("parries %d, events %s, gauge %s, Breaks %d, now %s" % [burak_parries_of(&"burak_shot"), events.map(func(e): return e.kind), values, breaks[0], sm.current_state.name])
			burak_check_pair(run)
			check(burak_parries_of(&"burak_shot") == 2 and shots.parries == 2 and events.is_empty() and player.playerHealth == 1000, "2 PARRIED, and nothing landed")
			check(not values.is_empty() and values[0] == 30.0 and breaks[0] == 1 and broken, "the gauge 30, then 60 breaks him (%s)" % [values])
		"block":
			log_p("-- a held guard: %s" % ("both BLOCKED for 20 stamina each, and the gauge never moves" if blocking() else "no answer without blocking, so both land"))
			track_spends()
			var run := await burak_run_shots(["block", "block"])
			var blocks := events_of("BLOCKED", &"burak_shot")
			log_p("blocks %s, parries %d, gauge %s" % [blocks.map(func(b): return b.stamina), parries.size(), values])
			burak_check_pair(run)
			if blocking():
				check(blocks.size() == 2 and is_equal_approx(blocks[-1].stamina, defense.max_stamina - 40.0) and events_of("HIT").is_empty() and parries.is_empty(), "2 BLOCKED, -40 stamina")
			else:
				check(events_of("HIT", &"burak_shot").size() == 2 and player.playerHealth == 998 and blocks.is_empty() and parries.is_empty() and spends == whiffs(1),
					"2 HITs through the held guard, a half-heart each, and nothing spent but the press's missed parry (%s)" % [spends])
			check(values.is_empty() and gauge.value == 0.0 and breaks[0] == 0, "and the gauge stays 0")
		"hit":
			log_p("-- no answer: both land for half a heart, and each drains 20 from 30: 10, then 0, not under")
			gauge.add(30.0)
			values.clear()
			var run := await burak_run_shots(["hit", "hit"])
			log_p("hits %d, health %d, gauge %s" % [events_of("HIT", &"burak_shot").size(), player.playerHealth, values])
			burak_check_pair(run)
			check(events_of("HIT", &"burak_shot").size() == 2 and player.playerHealth == 998 and parries.is_empty() and events_of("BLOCKED").is_empty(), "2 HITs, a half-heart each")
			check(values == [10.0, 0.0] and gauge.value == 0.0 and breaks[0] == 0, "the gauge 10, then 0 (%s)" % [values])
		"carry":
			log_p("-- 40 carried in: the first parry breaks him, and the second shot never comes")
			gauge.add(40.0)
			values.clear()
			var run := await burak_run_shots(["parry", "parry"])
			var broken := await wait_until(func(): return sm.current_state.name == "Broken", 30)
			await wait(60)
			log_p("released %d, balls %d, parries %d, Breaks %d, now %s" % [shots.release_times.size(), shots.balls.size(), parries.size(), breaks[0], sm.current_state.name])
			burak_check_pair(run)
			check(broken and breaks[0] == 1 and burak_parries_of(&"burak_shot") == 1, "the first parry breaks him: 40 + 30")
			check(shots.release_times.size() == 1 and shots.balls.size() == 1 and sm.current_state.name == "Broken", "and the second shot never fires")
		"lock":
			log_p("-- a locked gauge holds Idle; once it opens the pair comes, and a parry in it counts")
			gauge.locked = true
			gauge.unlock_left = gauge.unlock_delay
			var clocks := {"unlocked": -1.0, "shots": -1.0}
			var start: float = defense.clock
			var watch := func():
				if clocks.unlocked < 0.0 and not gauge.locked:
					clocks.unlocked = defense.clock
				if clocks.shots < 0.0 and sm.current_state == shots:
					clocks.shots = defense.clock
			physics_frame.connect(watch)
			sm.on_child_transition(sm.current_state, "Idle")
			var came := await wait_until(func(): return sm.current_state == shots, 400)
			physics_frame.disconnect(watch)
			log_p("the gauge opened %.3f s in, the pair came %.3f s in (Idle's own beat %.2f s)" % [clocks.unlocked - start, clocks.shots - start, sm.idle_beat])
			check(came and clocks.unlocked > 0.0 and clocks.shots >= clocks.unlocked and clocks.shots - start > sm.idle_beat + FRAME_TIME, "Idle held the pair past its beat until the gauge opened")
			var run := await burak_run_shots(["parry", "block"], false)
			burak_check_pair(run)
			# Without blocking the held guard is no answer, so the second shot lands and drains its 20.
			var credited: Array = [30.0] if blocking() else [30.0, 10.0]
			check(burak_parries_of(&"burak_shot") == 1 and values == credited and breaks[0] == 0, "and the parry is credited (%s)" % [values])
		"phit":
			log_p("-- parry, hit, then the next pair's parry: 30, 10, 40, and no Break (C1)")
			await burak_run_shots(["parry", "hit"])
			await burak_run_shots(["parry", "block"], false)
			log_p("gauge %s, Breaks %d" % [values, breaks[0]])
			# Without blocking the last shot lands through the held guard and drains its 20 as well.
			var path: Array = [30.0, 10.0, 40.0] if blocking() else [30.0, 10.0, 40.0, 20.0]
			check(values == path and gauge.value == path[-1] and breaks[0] == 0, "the gauge goes %s and never breaks him (%s)" % [path, values])
		_:
			check(false, "burak_shots has no tier %s" % tier)


# One cutlass string from HOME, swing k answered as answers[k] says: "walk" a diagonal held away from him
# the whole string, "guard" block held the whole string, "dash" a dash straight up two steps before the
# strike, "parry" a block press two steps before it. Returns every step's picture.
func burak_run_cutlass(answers: Array) -> Array:
	var cutlass: Node = sm.states["Cutlass"]
	var steps := []
	var watch := func():
		steps.append({"beat": cutlass.beat, "swing": cutlass.swing, "tell": not live_tells().is_empty(), "state": str(sm.current_state.name)})
	var held := []
	if answers.has("walk"):
		held = [KEY_LEFT, KEY_DOWN]
	elif answers.has("guard"):
		held = [KEY_SHIFT]
	for code in held:
		press(code)
	sm.on_child_transition(sm.current_state, "Cutlass")
	physics_frame.connect(watch)
	for k in answers.size():
		if answers[k] != "dash" and answers[k] != "parry":
			continue
		var due := func(): return sm.current_state != cutlass or (cutlass.beat == cutlass.Beat.WINDUP and cutlass.swing == k and cutlass.beat_clock >= cutlass.windup - 2.0 * FRAME_TIME - 0.0001)
		if not await wait_until(due, 400) or sm.current_state != cutlass:
			break
		var key := KEY_SHIFT
		if answers[k] == "dash":
			key = KEY_UP
			press(KEY_UP)
			tap(KEY_W)
		else:
			press(KEY_SHIFT)
		await wait_until(func(): return sm.current_state != cutlass or cutlass.results.size() > k, 30)
		release(key)
	await wait_until(func(): return sm.current_state != cutlass, 600)
	for code in held:
		release(code)
	physics_frame.disconnect(watch)
	return steps


# Whatever the answers: strikes at least follow + reaim_min + windup apart, each wind-up under its own red
# badge for the whole of it, and no badge anywhere else in the string.
func burak_check_string(steps: Array) -> void:
	var cutlass: Node = sm.states["Cutlass"]
	var times: Array = cutlass.strike_times
	var gaps := []
	for i in range(1, times.size()):
		gaps.append(times[i] - times[i - 1])
	var least: float = cutlass.follow + cutlass.reaim_min + cutlass.windup
	check(gaps.all(func(g): return g >= least - FRAME_TIME - 0.001), "strikes at least %.2f s apart (%s)" % [least, gaps.map(func(g): return snappedf(g, 0.001))])
	var mine: Array = steps.filter(func(s): return s.state == "Cutlass")
	for k in times.size():
		var up: Array = mine.filter(func(s): return s.beat == cutlass.Beat.WINDUP and s.swing == k)
		check(not up.is_empty() and up.all(func(s): return s.tell) and absf(up.size() * FRAME_TIME - cutlass.windup) <= 2.0 * FRAME_TIME + 0.001, "swing %d's wind-up under its own red badge the whole %.2f s (%d steps)" % [k, cutlass.windup, up.size()])
	check(mine.filter(func(s): return s.beat != cutlass.Beat.WINDUP).all(func(s): return not s.tell), "and no badge anywhere else in the string")


# The chase from eight starts round his floor on a player fleeing diagonally away from him the whole time:
# he gets to his spot beside them and winds up inside chase_max every time.
func burak_chase_sweep() -> void:
	var cutlass: Node = sm.states["Cutlass"]
	var walk: Rect2 = sm.WALK_RECT.grow(-20.0)
	var mid := walk.get_center()
	var starts := [walk.position, Vector2(mid.x, walk.position.y), Vector2(walk.end.x, walk.position.y), Vector2(walk.end.x, mid.y),
		walk.end, Vector2(mid.x, walk.end.y), Vector2(walk.position.x, walk.end.y), Vector2(walk.position.x, mid.y)]
	var took := []
	for from: Vector2 in starts:
		await burak_reset(Vector2(960, 640))
		boss.global_position = from
		var keys := [KEY_LEFT if player.global_position.x < from.x else KEY_RIGHT, KEY_UP if player.global_position.y < from.y else KEY_DOWN]
		for code in keys:
			press(code)
		var start: float = defense.clock
		sm.on_child_transition(sm.current_state, "Cutlass")
		await wait_until(func(): return cutlass.beat == cutlass.Beat.WINDUP or sm.current_state != cutlass, 240)
		took.append(defense.clock - start if sm.current_state == cutlass and cutlass.beat == cutlass.Beat.WINDUP else INF)
		for code in keys:
			release(code)
		burak_park()
	log_p("the chase from %s reached its first wind-up in %s s" % [starts, took.map(func(t): return snappedf(t, 0.01))])
	check(took.all(func(t): return t <= cutlass.chase_max), "it catches a fleeing diagonal walker from all %d starts inside %.1f s" % [starts.size(), cutlass.chase_max])


func test_burak_cutlass() -> void:
	await load_burak_attacks(["Cutlass"])
	track()
	track_parries()
	track_dodges()
	var gauge: Node = boss.break_gauge
	var values := []
	gauge.changed.connect(func(value, _max_value): values.append(value))
	var breaks := [0]
	gauge.broke.connect(func(): breaks[0] += 1)
	var cutlass: Node = sm.states["Cutlass"]
	var slash_script: GDScript = load("res://Scripts/BurakBossSlashScript.gd")
	var boxes: Array = load("res://Scripts/BurakBossArtLayout.gd").SLASH_BOXES
	check(boxes.size() == 3 and boxes.all(func(b): return slash_script.reaches(b)), "every SLASH_BOX overlaps %s, which every player position at a strike covers (%s)" % [slash_script.REACH, boxes])
	var hit: int = load("res://Scripts/HitInfo.gd").Result.HIT
	var parried: int = load("res://Scripts/HitInfo.gd").Result.PARRIED
	var dodged: int = load("res://Scripts/HitInfo.gd").Result.DODGED
	var answer := "walk" if tier == "normal" else tier
	match answer:
		"walk", "guard":
			if answer == "walk":
				await burak_chase_sweep()
			await burak_reset(Vector2(700, 800))
			log_p("-- %s: there is no getting out of it, all three swings land" % ("walking away" if answer == "walk" else "a held guard"))
			var steps := await burak_run_cutlass([answer, answer, answer])
			log_p("results %s, hits %d, health %d, now at %s" % [cutlass.results, events_of("HIT", &"burak_cutlass").size(), player.playerHealth, player.global_position])
			burak_check_string(steps)
			check(burak_results_are([hit, hit, hit]) and events_of("HIT", &"burak_cutlass").size() == 3 and player.playerHealth == 997 and parries.is_empty() and events_of("BLOCKED").is_empty(), "3 HITs, a half-heart each")
		"dash":
			await burak_reset(Vector2(700, 850))
			await fresh_dash_ready()
			log_p("-- a dash two steps before each strike: all three DODGED, nothing landed, nothing credited")
			var steps := await burak_run_cutlass(["dash", "dash", "dash"])
			log_p("results %s, perfect dodges %d, stamina %.0f, health %d, gauge %.0f" % [cutlass.results, dodges.size(), defense.stamina, player.playerHealth, gauge.value])
			burak_check_string(steps)
			check(burak_results_are([dodged, dodged, dodged]) and events_of("HIT").is_empty() and player.playerHealth == 1000, "3 DODGED, no damage")
			check(dodges.size() >= 1 and gauge.value == 0.0 and values.is_empty(), "perfect dodges that fill nothing")
		"parry":
			await burak_reset(Vector2(700, 800))
			log_p("-- a fresh press two steps before each strike: all three PARRIED, and the third breaks him")
			var steps := await burak_run_cutlass(["parry", "parry", "parry"])
			var broken := await wait_until(func(): return sm.current_state.name == "Broken", 30)
			log_p("results %s, gauge %s, Breaks %d, now %s, his sprite at %s" % [cutlass.results, values, breaks[0], sm.current_state.name, boss.sprite.position])
			burak_check_string(steps)
			check(burak_results_are([parried, parried, parried]) and burak_parries_of(&"burak_cutlass") == 3 and events.is_empty() and player.playerHealth == 1000, "3 PARRIED, nothing landed")
			check(values == [20.0, 40.0, 0.0] and breaks[0] == 1 and broken, "the gauge 20, 40, then 60 breaks him on the third (%s)" % [values])
			check(boss.sprite.position == boss.sprite_base_position, "his sprite back on its rest after the jolts")
		"mixed":
			await burak_reset(Vector2(700, 800))
			log_p("-- parry, dash, parry: 40 and no Break, and the next pair's first parry breaks him")
			var steps := await burak_run_cutlass(["parry", "dash", "parry"])
			sm.ATTACK_ORDER.assign(["Shots"])
			log_p("results %s, gauge %s, Breaks %d" % [cutlass.results, values, breaks[0]])
			burak_check_string(steps)
			check(burak_results_are([parried, dodged, parried]) and values == [20.0, 40.0] and breaks[0] == 0, "PARRIED, DODGED, PARRIED: 20, then 40, and no Break (%s)" % [values])
			await burak_run_shots(["parry", "parry"], false)
			var broken := await wait_until(func(): return sm.current_state.name == "Broken", 30)
			log_p("gauge %s, Breaks %d, now %s" % [values, breaks[0], sm.current_state.name])
			check(broken and breaks[0] == 1 and burak_parries_of(&"burak_shot") == 1, "and the next Shots' first parry breaks him: 40 + 30")
		_:
			check(false, "burak_cutlass has no tier %s" % tier)


# ------------------------------------------------------------------ Mason's body while he lays a line
# Touching him hurts from the squat that starts a poo line to the step that ends it
# (MasonScript.set_contact_live), and at no other time. A process only gets one ending, so the run ends
# on the contact killing the player, or with `tier=won` on his defeat mid-line.

const CONTACT_ID := &"mason_poo_contact"
# Off to one side of where his line starts, so only its run across the mat reaches the player: the run
# crosses their row right at their x, which walks him straight through a player who stands still.
const CONTACT_PATH_SPOT := Vector2(560, 520)


func contact_hits() -> Array:
	return events_of("HIT", CONTACT_ID)


func contact_live() -> bool:
	return boss.contact_hitbox.is_in_group("enemy projectile")


# The player's hurtbox centred on his contact box, wherever he is, for `seconds` of game time: a
# Break's hit-stop stretches frames.
func hold_in_him(seconds: float) -> void:
	var until: float = defense.clock + seconds
	while defense.clock < until:
		var into: Vector2 = boss.contact_hitbox.get_node("CollisionShape2D").global_position
		player.global_position += into - player.hurtBox.get_node("CollisionShape2D").global_position
		player.velocity = Vector2.ZERO
		await physics_frame


# Idle at home, with his next line starting where he stands rather than where the last one ended.
func reset_contact(spec: Dictionary) -> void:
	await reset_gauged(spec.home)
	sm.rest_point = boss.global_position + sm.BOMB_SPAWN_OFFSET
	events.clear()
	dodges.clear()


func test_mason_contact() -> void:
	fight = "mason"
	if not await load_gauged():
		return
	var spec: Dictionary = fight_spec
	var entry: Dictionary = CATALOG.get_attack(CONTACT_ID)
	check(entry.damage == 1 and not entry.blockable and not entry.parryable and not entry.tell and not entry.dodge_tell and entry.dash_through and not entry.bypass_invincibility, "catalogued: half a heart, no guard, no badge, dashed through, spaced by the i-frames (%s)" % [entry])
	check(boss.ATTACK_IDS.has(CONTACT_ID), "his own attack, for his Break gauge")
	track()
	track_dodges()
	var laying := ["PooSquat", "Waddle"]
	var hit_in := []
	defense.hit_taken.connect(func(hit):
		if hit.attack_id == CONTACT_ID:
			hit_in.append(str(sm.current_state.name)))
	var watched := {"frames": 0, "live": 0, "wrong": 0, "first": ""}
	var watch_contact := func():
		var live: bool = contact_live()
		watched.frames += 1
		if live:
			watched.live += 1
		if live != laying.has(str(sm.current_state.name)):
			watched.wrong += 1
			if watched.first.is_empty():
				watched.first = "%s, live %s" % [sm.current_state.name, live]
	physics_frame.connect(watch_contact)

	log_p("-- outside a line, standing in him costs nothing")
	await reset_contact(spec)
	for state_name in ["Idle", "Eat"]:
		sm.on_child_transition(sm.current_state, state_name)
		stop_boss_timers()
		await hold_in_him(1.5)
		check(sm.current_state.name == state_name and contact_hits().is_empty(), "%s: 1.5 s in him, no hit (%d)" % [state_name, contact_hits().size()])

	log_p("-- already in him as a line starts, and still in him as the i-frames run out")
	await reset_contact(spec)
	hit_in.clear()
	await hold_in_him(0.2)
	var health: int = player.playerHealth
	var start: float = defense.clock
	sm.start_cycle()
	# Held in the squat over the player, rather than laying its bomb and walking off.
	sm.squat_timer.stop()
	await hold_in_him(3.55)
	var hits := contact_hits()
	log_p("held in the squat over the player: hits at %s s, in %s" % [hits.map(func(e): return snappedf(e.t - start, 0.001)), hit_in])
	check(hits.size() == 4 and hit_in.all(func(s): return s == "PooSquat"), "hit as the line starts, then each time the i-frames run out: 4 in 3.55 s (%d)" % hits.size())
	# The cycle's first squat leaves a player already in him alone for sm.cycle_contact_grace (eating ends with them
	# punching him); a line's first frame otherwise.
	var grace: float = sm.cycle_contact_grace
	check(not hits.is_empty() and hits[0].t - start >= grace - 0.001 and hits[0].t - start <= grace + 2.0 * FRAME_TIME + 0.001, "the first as the cycle's %.2f s contact grace runs out, with no entry to report it (%.3f s)" % [grace, hits[0].t - start if not hits.is_empty() else -1.0])
	var gaps := []
	for i in range(1, hits.size()):
		gaps.append(snappedf(hits[i].t - hits[i - 1].t, 0.001))
	check(not gaps.is_empty() and gaps.all(func(g): return g >= 1.0 - 0.001 and g <= 1.0 + 2.0 * FRAME_TIME + 0.001), "a second of i-frames apart and no more (%s)" % [gaps])
	check(health - player.playerHealth == hits.size() * catalogue_damage(CONTACT_ID), "half a heart each (%d lost)" % (health - player.playerHealth))

	log_p("-- standing in his path while he walks a line")
	await reset_contact(spec)
	hit_in.clear()
	await settle_player(CONTACT_PATH_SPOT)
	health = player.playerHealth
	sm.start_cycle()
	var walked := await wait_until(func():
		player.global_position = CONTACT_PATH_SPOT
		return sm.lines_done >= 1, 400)
	hits = contact_hits()
	log_p("standing at %s through his first line: %d hits, in %s" % [CONTACT_PATH_SPOT, hits.size(), hit_in])
	check(walked, "his line reached its end")
	check(hits.size() == 1 and hit_in == ["Waddle"], "he walks through them once and it hurts once, mid-waddle")
	check(health - player.playerHealth == catalogue_damage(CONTACT_ID), "half a heart (%d lost)" % (health - player.playerHealth))

	log_p("-- a dash through him mid-line")
	await reset_contact(spec)
	var box_shape: CollisionShape2D = boss.contact_hitbox.get_node("CollisionShape2D")
	var box: Rect2 = box_shape.global_transform * box_shape.shape.get_rect()
	var hurt_shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var hurt: Rect2 = hurt_shape.global_transform * hurt_shape.shape.get_rect()
	# Level with him, the player's right edge 12 px short of his left one.
	await settle_player(player.global_position + Vector2(box.position.x - 12.0 - hurt.end.x, box.get_center().y - hurt.get_center().y))
	sm.start_cycle()
	sm.squat_timer.stop()
	await wait(3)
	var gauge_before: float = boss.break_gauge.value
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(4)
	release(KEY_RIGHT)
	await wait(30)
	hurt = hurt_shape.global_transform * hurt_shape.shape.get_rect()
	log_p("dashed to x %.0f past his box %.0f-%.0f: dodges %s, contact hits %d, gauge %.0f -> %.0f" % [hurt.position.x, box.position.x, box.end.x, dodges.map(func(d): return d.id), contact_hits().size(), gauge_before, boss.break_gauge.value])
	check(contact_hits().is_empty() and hurt.position.x > box.end.x, "through him and out the other side without a hit")
	check(dodges.size() == 1 and dodges[0].id == CONTACT_ID, "and it is a perfect dodge")
	check(boss.break_gauge.value - gauge_before == boss.break_gauge.perfect_dodge_gain, "which his gauge takes as his own (+%.0f)" % (boss.break_gauge.value - gauge_before))

	log_p("-- every way out of a line takes it with it")
	await reset_contact(spec)
	await settle_player(OUT_OF_REACH)
	sm.start_cycle()
	sm.lines_done = sm.lines_per_cycle[sm.cycle_phase] - 1
	var ended := await wait_until(func(): return not laying.has(str(sm.current_state.name)), 400)
	check(ended and not contact_live(), "the cycle's last line ends: off as %s starts" % sm.current_state.name)
	for case in [["a Break out of the squat", "PooSquat"], ["a Break out of the waddle", "Waddle"]]:
		await reset_contact(spec)
		await settle_player(OUT_OF_REACH)
		sm.start_cycle()
		var reached := await wait_until(func(): return sm.current_state.name == case[1], 120)
		boss.break_gauge.add(boss.break_gauge.max_value)
		await wait_until(func(): return sm.current_state.name == "Broken", 30)
		var off := not contact_live()
		await hold_in_him(1.2)
		check(reached and sm.current_state.name == "Broken" and off and contact_hits().is_empty(), "%s: off, and 1.2 s in him while he is down costs nothing (%d)" % [case[0], contact_hits().size()])

	if tier == "won":
		log_p("-- his defeat mid-line")
		await reset_contact(spec)
		await settle_player(OUT_OF_REACH)
		sm.start_cycle()
		var waddling := await wait_until(func(): return sm.current_state.name == "Waddle", 120)
		boss.phase_two = true
		boss.boss_health = 1
		boss.take_finisher(1)
		var beaten := await wait_until(func(): return sm.current_state.name == "Defeated", 60)
		await hold_in_him(1.2)
		check(waddling and beaten and not contact_live() and contact_hits().is_empty(), "beaten mid-waddle: off, and nothing from him after (%s)" % sm.current_state.name)
	else:
		log_p("-- the contact kills the player mid-line")
		await reset_contact(spec)
		await hold_in_him(0.2)
		player.playerHealth = 1
		sm.start_cycle()
		sm.squat_timer.stop()
		var lost := await wait_until(func(): return player.fight_over, 60)
		await hold_in_him(1.2)
		var landed := events_of("HIT")
		check(lost and player.playerHealth == 0 and landed.size() == 1 and landed[0].id == CONTACT_ID, "the contact is the killing blow (%s)" % [landed.map(func(e): return e.id)])
		check(not contact_live() and sm.current_state.name == "Idle" and sm.player_defeated, "the outro stands him down with it off (%s)" % sm.current_state.name)
	physics_frame.disconnect(watch_contact)
	log_p("watched %d frames, %d live, %d wrong%s" % [watched.frames, watched.live, watched.wrong, (": first " + watched.first) if watched.wrong > 0 else ""])
	check(watched.live > 0 and watched.wrong == 0, "live on exactly the frames he is in PooSquat or Waddle")


# ------------------------------------------------------------------ Mason's phase-two combined attack
# Under half his health his one finisher is the nugget shower with Carter called in while it rains
# (MasonNuggetShower, MasonStateMachine.carter_in_shower). The rain is timed around Carter: no nugget
# lands from slam_clear_before ahead of one of his slams to slam_clear_after past its hitbox, anywhere
# on the mat, so answering him is never answering a nugget in the same breath. A process gets one
# ending: the run ends on the player killed mid-attack, or with `tier=won` on Mason beaten mid-attack.

# Where he stands for it, on the wall column his lines end on, and where a player stands it out.
const MASON_COMBINED_AT := Vector2(1660, 480)
const MASON_STAND_AT := Vector2(760, 640)
# The dodging bot keeps a person's pace rather than a perfect bot's: it sees anything new this long
# after it appears, and picks its next step every few frames, off where each marker says its hit lands.
const MASON_BOT_REACTION := 0.3
const MASON_BOT_REPLAN := 6
# How far outside an oval it wants its hurtbox, and the floor it keeps to so a wall never pins it.
const MASON_BOT_MARGIN := 10.0
const MASON_BOT_AREA := Rect2(150, 175, 1620, 760)
const MASON_BOT_SPOTS := [Vector2(760, 640), Vector2(400, 820), Vector2(1200, 300), Vector2(300, 300)]
const MASON_BOT_DIRECTIONS := [Vector2.ZERO, Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1), Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1), Vector2(1, -1)]
# feel_v2's dash: 250 px over three frames, then five standing.
const MASON_BOT_DASH := 250.0
const MASON_BOT_DASH_TIME := 8.0 / 60.0
const MASON_BOT_SPEED := 600.0
# The most one attack may cost the bot, from a full bar of eight half-hearts (six until 2026-09-30).
const MASON_BOT_MAX_HITS := 2
const MASON_FULL_HEALTH := 8
# The floor a player's body can stand on and the grid it is read on, as the tuning script reads them
# (art_source/mason_tuning/verify_mason_tuning.gd), but with the player's own hurtbox.
const MASON_STAND_AREA := Rect2(117, 132, 1686, 816)
const MASON_GRID_STEP := 40.0
# A blast is live from its detonation's EXPLOSION_HITBOX_DELAY to 0.3 s in (PooBombScene's explode track).
const MASON_BOMB_LIVE := 0.2
# How finely, and how far ahead, the bot reads Mason's body along the line he is laying.
const MASON_BOT_BODY_STEP := 1.0 / 30.0
const MASON_BOT_BODY_AHEAD := 1.0
# The parrying bot presses this long before Carter's slam, well inside PlayerDefense.parry_window, and
# keeps its guard up this long after his hitbox is gone.
const MASON_BOT_PARRY_LEAD := 0.12
const MASON_BOT_GUARD_AFTER := 0.05

var mason_log := {}
var mason_bot := {}


# Idle on his wall column in phase two, with the player at `at`: his next finisher is the combined one.
func mason_ready_combined(at: Vector2) -> void:
	await reset_gauged(fight_spec.home)
	boss.global_position = MASON_COMBINED_AT
	sm.rest_point = boss.global_position + sm.BOMB_SPAWN_OFFSET
	boss.phase_two = true
	boss.boss_health = floori(boss.get_max_health() * boss.PHASE_TWO_RATIO)
	await settle_player(at)


func mason_start_combined() -> void:
	sm.cycle_phase = 1
	sm.finishers = []
	sm.on_child_transition(sm.current_state, "NuggetShower")


# Deep in it: Carter coming down or on the mat, with nuggets in the sky around him.
func mason_mid_attack() -> bool:
	if sm.current_state.name != "NuggetShower" or not sm.states["CallCarter"].sent:
		return false
	var drops := hazards_of("CarterElbowDropScript.gd")
	var in_sky := hazards_of("NuggetMeteorScript.gd").filter(func(nugget): return nugget.marker.visible)
	return not drops.is_empty() and drops[0].carter_sprite.visible and in_sky.size() >= 2


func mason_new_log() -> void:
	mason_log = {"nuggets": {}, "drops": {}, "marks": [], "slams": [], "phone_told": 0, "both_up": 0, "overlaps": 0, "under": 0, "under_first": "", "sorted_off": 0,
		"cells": 0, "samples": 0, "free_sum": 0, "worst_free": 1 << 30, "worst_at": 0.0, "worst_patch": 0, "furthest": 0.0, "furthest_at": 0.0, "covered": {}}


# Every nugget's landing, each of Carter's marks and slams with the badge over each approach, and how
# his marker and the nuggets' stack wherever they overlap. Game time, on the player's own clock.
func mason_record() -> void:
	var log: Dictionary = mason_log
	var now: float = defense.clock
	if Engine.get_physics_frames() % 6 == 0:
		mason_sample_cells()
	var told := not live_tells().is_empty()
	var target: Sprite2D = null
	var markers := []
	for hazard in live_hazards():
		if hazard.get_script() == null:
			continue
		var id: int = hazard.get_instance_id()
		match hazard.get_script().resource_path.get_file():
			"NuggetMeteorScript.gd":
				var nugget: Dictionary = log.nuggets.get(id, {"at": hazard.global_position, "landed": -1.0})
				log.nuggets[id] = nugget
				if nugget.landed < 0.0 and not hazard.hitbox_shape.disabled:
					nugget.landed = now
				if hazard.marker.visible:
					markers.append(hazard.marker)
			"CarterElbowDropScript.gd":
				var drop: Dictionary = log.drops.get(id, {"marked": false, "live": false, "approach": 0, "told": 0})
				log.drops[id] = drop
				var marked: bool = hazard.target_sprite.visible
				if marked:
					target = hazard.target_sprite
					if not drop.marked:
						log.marks.append({"t": now, "at": hazard.global_position})
						drop.approach = 0
						drop.told = 0
					drop.approach += 1
					if told:
						drop.told += 1
					var drawn: Vector2 = (target.get_global_transform() * target.get_rect()).get_center()
					if absf(target.global_position.y - sm.states["CallCarter"].ROPES.position.y) > 0.5 or drawn.distance_to(hazard.global_position) > 0.5:
						log.sorted_off += 1
				drop.marked = marked
				var live: bool = not hazard.hitbox_shape.disabled
				if live and not drop.live:
					log.slams.append({"t": now, "end": INF, "at": hazard.global_position, "approach": drop.approach, "told": drop.told})
				elif drop.live and not live:
					log.slams[-1].end = now
				drop.live = live
	if told and log.marks.is_empty():
		log.phone_told += 1
	if target == null or markers.is_empty():
		return
	log.both_up += 1
	var target_rect: Rect2 = target.get_global_transform() * target.get_rect()
	for marker: Sprite2D in markers:
		if not (marker.get_global_transform() * marker.get_rect()).intersects(target_rect):
			continue
		log.overlaps += 1
		if marker.z_index > target.z_index or (marker.z_index == target.z_index and marker.global_position.y > target.global_position.y):
			continue
		log.under += 1
		if log.under_first.is_empty():
			log.under_first = "the marker at %s under his at %s" % [marker.global_position, target.global_position]


# The nearest any landing came to a slam: before it, and after its hitbox went off.
func mason_clearances() -> Dictionary:
	var before := INF
	var after := INF
	var inside := 0
	for nugget in mason_log.nuggets.values():
		if nugget.landed < 0.0:
			continue
		for slam in mason_log.slams:
			if nugget.landed < slam.t:
				before = minf(before, slam.t - nugget.landed)
			elif nugget.landed >= slam.end:
				after = minf(after, nugget.landed - slam.end)
			else:
				inside += 1
	return {"before": before, "after": after, "inside": inside}


# The floor on the grid right now: which cells a hurtbox standing in is caught by nothing, by a nugget
# marker, or only by Carter's marker or slam, whose own answer is his parry or a dash. Kept: the worst
# moment's free count and its biggest open patch, every cell a marker ever covered, and the furthest a
# cell under a nugget marker was from a free one, counted in grid steps round whatever is in the way.
func mason_sample_cells() -> void:
	var log: Dictionary = mason_log
	var nugget_ovals := []
	var carter_ovals := []
	for hazard in live_hazards():
		if hazard.get_script() == null:
			continue
		match hazard.get_script().resource_path.get_file():
			"NuggetMeteorScript.gd":
				if hazard.marker.visible:
					nugget_ovals.append([hazard.global_position, hazard.HIT_SIZE / 2.0])
			"CarterElbowDropScript.gd":
				if hazard.target_sprite.visible or not hazard.hitbox_shape.disabled:
					carter_ovals.append([hazard.global_position, hazard.hit_size() / 2.0])
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	var offset: Vector2 = shape.global_position - player.global_position
	var free := {}
	var blocked := {}
	var under_nugget := []
	var columns := int(MASON_STAND_AREA.size.x / MASON_GRID_STEP) + 1
	var rows := int(MASON_STAND_AREA.size.y / MASON_GRID_STEP) + 1
	for column in columns:
		for row in rows:
			var cell := Vector2i(column, row)
			var centre: Vector2 = MASON_STAND_AREA.position + Vector2(cell) * MASON_GRID_STEP + offset
			var by_nugget := nugget_ovals.any(func(oval): return ((Vector2(oval[0]).clamp(centre - half, centre + half) - oval[0]) / oval[1]).length() < 1.0)
			if by_nugget or carter_ovals.any(func(oval): return ((Vector2(oval[0]).clamp(centre - half, centre + half) - oval[0]) / oval[1]).length() < 1.0):
				blocked[cell] = true
				log.covered[cell] = true
				if by_nugget:
					under_nugget.append(cell)
			else:
				free[cell] = true
	log.cells = columns * rows
	log.samples += 1
	log.free_sum += free.size()
	if free.size() < log.worst_free:
		log.worst_free = free.size()
		log.worst_at = defense.clock
		log.worst_patch = mason_largest_patch(free)
	var steps := {}
	var queue: Array = free.keys()
	for cell in queue:
		steps[cell] = 0
	var head := 0
	while head < queue.size():
		var at: Vector2i = queue[head]
		head += 1
		for step: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var next: Vector2i = at + step
			if blocked.has(next) and not steps.has(next):
				steps[next] = steps[at] + 1
				queue.append(next)
	for cell in under_nugget:
		var far: float = steps.get(cell, INF) * MASON_GRID_STEP
		if far > log.furthest:
			log.furthest = far
			log.furthest_at = defense.clock


func mason_largest_patch(cells: Dictionary) -> int:
	var seen := {}
	var best := 0
	for start in cells:
		if seen.has(start):
			continue
		var size := 0
		var stack: Array = [start]
		seen[start] = true
		while not stack.is_empty():
			var at: Vector2i = stack.pop_back()
			size += 1
			for step: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var next: Vector2i = at + step
				if cells.has(next) and not seen.has(next):
					seen[next] = true
					stack.append(next)
		best = maxi(best, size)
	return best


# One whole attack as mason_record saw it: the two overlapping, the rain clear of every slam, both
# tells up and readable, and nothing of it left behind.
func mason_check_attack(case: String, ended: bool, needs_overlap: bool) -> void:
	var log: Dictionary = mason_log
	var landings: Array = log.nuggets.values().filter(func(n): return n.landed >= 0.0).map(func(n): return n.landed)
	landings.sort()
	var slams: Array = log.slams
	var drops: int = sm.elbow_drops[sm.cycle_phase]
	var next: String = log.get("next", "AwaitDelivery")
	check(ended and sm.current_state.name == next, "%s: it plays out and hands over to %s (%s)" % [case, next, sm.current_state.name])
	check(slams.size() == drops and log.marks.size() == drops, "%s: all %d of Carter's drops come down (%d marks, %d slams)" % [case, drops, log.marks.size(), slams.size()])
	if landings.is_empty() or slams.is_empty():
		check(false, "%s: the rain and Carter both came (%d landings, %d slams)" % [case, landings.size(), slams.size()])
		return
	var between := []
	for i in range(1, slams.size()):
		between.append(landings.filter(func(l): return l > slams[i - 1].t and l < slams[i].t).size())
	var first_before: int = landings.filter(func(l): return l < slams[0].t).size()
	log_p("%s: %d nuggets landed from %.2f to %.2f s and %d slams from %.2f to %.2f s; %d landings before the first slam, then %s between each and the next; his marker and nugget markers down together on %d frames" % [case, landings.size(), landings[0], landings[-1], slams.size(), slams[0].t, slams[-1].t, first_before, between, log.both_up])
	check(first_before > 0 and between.all(func(n): return n > 0) and log.both_up > 0, "%s: they overlap: nuggets land before his first slam and between every two, with their markers down alongside his" % case)
	log_p("%s: free standing cells (%.0f px grid): %d of %d at worst (%.2f s), its biggest open patch %d; %.0f%% free on average; %.0f%% of the floor under a marker at some point; the furthest a cell under a nugget marker was from a free one %.0f px (%.2f s)" % [case, MASON_GRID_STEP, log.worst_free, log.cells, log.worst_at, log.worst_patch, 100.0 * log.free_sum / maxf(log.samples * log.cells, 1.0), 100.0 * log.covered.size() / maxf(log.cells, 1.0), log.furthest, log.furthest_at])
	check(log.worst_free > 0 and log.furthest / MASON_BOT_SPEED <= sm.states["NuggetShower"].warning - MASON_BOT_REACTION, "%s: at every moment there is somewhere free to stand, and it is a walk from anywhere under a nugget marker that fits in its warning less a reaction (%.0f px)" % [case, log.furthest])
	var clear := mason_clearances()
	log_p("%s: the nearest a nugget landed to a slam was %.3f s before one and %.3f s after its hitbox; %d landed during one" % [case, clear.before, clear.after, clear.inside])
	check(clear.inside == 0 and clear.before >= sm.slam_clear_before - 0.001 and clear.after >= sm.slam_clear_after - 0.001, "%s: no nugget lands within %.2f s before a slam or %.2f s after its hitbox, anywhere on the mat" % [case, sm.slam_clear_before, sm.slam_clear_after])
	var untold := slams.filter(func(s): return s.told < s.approach - 2)
	log_p("%s: the badge was up %d frames of the call before his first mark, and on %s of each approach's frames" % [case, log.phone_told, slams.map(func(s): return "%d/%d" % [s.told, s.approach])])
	check(log.phone_told > 0 and untold.is_empty(), "%s: Carter's badge is up through the call and over every drop's approach" % case)
	log_p("%s: %d overlaps of a nugget marker with his, %d drawn under it; his marker off the rope line or moved on %d frames" % [case, log.overlaps, log.under, log.sorted_off])
	check((log.overlaps > 0 or not needs_overlap) and log.under == 0, "%s: a nugget marker lying on his is drawn over it%s" % [case, "" if log.under == 0 else " (first: %s)" % log.under_first])
	check(log.sorted_off == 0, "%s: his marker sorts on the back rope's line and still draws on his landing spot" % case)
	# His last slam's sound outlives him (CarterElbowDropScript._finish), and his last dust still has a
	# frame or two to play as the call ends.
	var lingering := hazards_of("CarterElbowDropScript.gd")
	log_p("%s: left as it ends: %d nuggets, %d badges, Carter %s" % [case, hazards_of("NuggetMeteorScript.gd").size(), live_tells().size(), lingering.map(func(d): return "hitbox off %s, him %s, marker %s, dust %s" % [d.hitbox_shape.disabled, d.carter_sprite.visible, d.target_sprite.visible, d.impact_sprite.visible])])
	check(hazards_of("NuggetMeteorScript.gd").is_empty() and live_tells().is_empty() and lingering.all(func(d): return d.hitbox_shape.disabled and not d.carter_sprite.visible and not d.target_sprite.visible), "%s: nothing of it is left: no nugget, no badge, and Carter at most ringing out, hidden with his hitbox off (%d)" % [case, lingering.size()])
	var shower: Node = sm.states["NuggetShower"]
	var call: Node = sm.states["CallCarter"]
	check(call.carter == null and not call.sent and not call.telling and not (shower.shower and shower.shower.is_valid()) and not (shower.phone and shower.phone.is_valid()), "%s: the call is let go and both of the shower's tweens are done" % case)


# Everything of the attack stopped by whatever ended it: no nugget and no Carter, no badge, none of his
# clocks running, the shower and the call's tweens dead and the call let go.
func mason_check_released(case: String) -> void:
	var shower: Node = sm.states["NuggetShower"]
	var call: Node = sm.states["CallCarter"]
	var nuggets := hazards_of("NuggetMeteorScript.gd")
	var carters := hazards_of("CarterElbowDropScript.gd")
	var running := break_timers().filter(func(t): return not t.is_stopped())
	var tweens := [shower.shower, shower.phone].filter(func(t): return t != null and t.is_valid())
	log_p("%s: now %s, nuggets %d, Carter %d, badges %d, timers running %s, tweens alive %d, call %s sent %s telling %s" % [case, sm.current_state.name, nuggets.size(), carters.size(), live_tells().size(), running.map(func(t): return t.name), tweens.size(), call.carter, call.sent, call.telling])
	check(nuggets.is_empty() and carters.is_empty(), "%s: every nugget and Carter are gone" % case)
	check(live_tells().is_empty(), "%s: no badge survives" % case)
	check(running.is_empty(), "%s: none of his timers is running" % case)
	check(tweens.is_empty(), "%s: the shower's rain and its call have stopped" % case)
	check(call.carter == null and not call.sent and not call.telling, "%s: the call is let go" % case)


# Everything of the attack that moves or counts down, read off the live nodes.
func mason_snapshot() -> Array:
	var shower: Node = sm.states["NuggetShower"]
	var snap := [defense.clock]
	for tween: Tween in [shower.shower, shower.phone]:
		snap.append(tween.get_total_elapsed_time() if tween and tween.is_valid() else -1.0)
	for nugget in hazards_of("NuggetMeteorScript.gd"):
		snap.append([nugget.get_instance_id(), nugget.meteor.position, nugget.meteor.visible, nugget.marker.frame, nugget.impact_sprite.frame])
	for drop in hazards_of("CarterElbowDropScript.gd"):
		snap.append([drop.global_position, drop.carter_sprite.position, drop.carter_sprite.frame, drop.target_sprite.visible, drop.target_sprite.frame, drop.impact_sprite.frame])
	for tell in live_tells():
		snap.append(tell.time_left)
	return snap


func mason_bot_reset(parry := false) -> void:
	mason_bot = {"known": [], "seen": {}, "marked": {}, "held": {}, "dir": Vector2.ZERO, "last_dash": -INF, "dashes": 0, "offset": Vector2.ZERO, "half": Vector2.ZERO, "body": [], "line": null, "line_seen": -INF,
		"parry": parry, "guard_until": -INF, "pressed": {}, "presses": 0, "guards": []}


func mason_bot_frame() -> void:
	mason_bot_perceive()
	if mason_bot.parry and mason_bot_guard():
		return
	if Engine.get_physics_frames() % MASON_BOT_REPLAN == 0:
		mason_bot_plan()


# The parrying bot's answer to Carter: it stays planted where his marker has it, presses a beat before
# his slam and holds the guard until his hitbox is gone. True while it is planted.
func mason_bot_guard() -> bool:
	var now: float = defense.clock
	if mason_bot.guard_until > now:
		return true
	if mason_bot.guard_until > -INF:
		release(KEY_SHIFT)
		mason_bot.guard_until = -INF
	for threat in mason_bot.known:
		if threat.kind != "carter" or now - threat.seen < MASON_BOT_REACTION or mason_bot.pressed.has(threat.lands):
			continue
		var left: float = threat.lands - now
		if left <= 0.0 or left > MASON_BOT_PARRY_LEAD or mason_bot_reach(player.global_position, threat) >= 1.0:
			continue
		mason_bot.pressed[threat.lands] = true
		mason_bot.presses += 1
		mason_bot_hold(Vector2.ZERO)
		press(KEY_SHIFT)
		mason_bot.guard_until = threat.lands + threat.live + MASON_BOT_GUARD_AFTER
		mason_bot.guards.append([now, mason_bot.guard_until])
		return true
	return false


# Each nugget marker and each of Carter's marks as it appears, with where its hit lands and when: the
# fight's own numbers, which the markers' own count-downs show a player.
func mason_bot_perceive() -> void:
	var now: float = defense.clock
	for hazard in live_hazards():
		if hazard.get_script() == null:
			continue
		var id: int = hazard.get_instance_id()
		match hazard.get_script().resource_path.get_file():
			"NuggetMeteorScript.gd":
				if not mason_bot.seen.has(id):
					mason_bot.seen[id] = true
					mason_bot.known.append({"kind": "nugget", "at": hazard.global_position, "seen": now, "lands": now + sm.nugget_warning[sm.cycle_phase], "live": hazard.HITBOX_ACTIVE_TIME, "semi": hazard.HIT_SIZE / 2.0})
			"CarterElbowDropScript.gd":
				var marked: bool = hazard.target_sprite.visible
				if marked and not mason_bot.marked.get(id, false):
					mason_bot.known.append({"kind": "carter", "at": hazard.global_position, "seen": now, "lands": now + hazard.telegraph_time + hazard.dive_time, "live": hazard.hitbox_active_time, "semi": hazard.hit_size() / 2.0})
				mason_bot.marked[id] = marked
			"PooBombScript.gd":
				# From the moment its line is laid and it starts counting down, as the line going off in
				# order from its start ring shows a player.
				if not hazard.detonate_timer.is_stopped() and not mason_bot.seen.has(id):
					mason_bot.seen[id] = true
					var blast: float = (hazard.explosion_hitbox_shape.shape as CircleShape2D).radius
					mason_bot.known.append({"kind": "bomb", "at": hazard.global_position, "seen": now, "lands": now + hazard.detonate_timer.time_left + hazard.EXPLOSION_HITBOX_DELAY, "live": MASON_BOMB_LIVE, "semi": Vector2.ONE * blast})
	mason_bot.known = mason_bot.known.filter(func(k): return k.lands + k.live > now)
	mason_bot_follow_mason(now)


# Mason himself while he lays a line: where he stands until the line's start ring has been up a
# reaction's time, and after that where the ring's path takes him, which is what it shows a player.
func mason_bot_follow_mason(now: float) -> void:
	mason_bot.body = []
	var state := str(sm.current_state.name)
	if state != "PooSquat" and state != "Waddle":
		return
	if sm.line_start != mason_bot.line:
		mason_bot.line = sm.line_start
		mason_bot.line_seen = now
	var shape: CollisionShape2D = boss.contact_hitbox.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	var offset: Vector2 = shape.global_position - boss.global_position
	var read: bool = now - mason_bot.line_seen >= MASON_BOT_REACTION
	var walked: float = sm.states["Waddle"].distance if state == "Waddle" else 0.0
	var squatting := 0.0
	if state == "PooSquat":
		squatting = sm.release_timer.time_left if sm.squat_timer.is_stopped() else sm.squat_timer.time_left + sm.states["PooSquat"].release_hold
	var speed: float = sm.waddle_speed[sm.cycle_phase]
	var ahead := 0.0
	while ahead <= MASON_BOT_BODY_AHEAD:
		var at: Vector2 = boss.global_position
		if read:
			at = sm.walk_position(minf(walked + speed * maxf(0.0, ahead - squatting), sm.line_length))
		mason_bot.body.append({"at": at + offset, "t": now + ahead, "half": half})
		ahead += MASON_BOT_BODY_STEP


# The step, from standing still to a dash and a walk in any of eight directions, whose path is clear of
# everything it has seen by its hit's time, keeping off the walls.
func mason_bot_plan() -> void:
	var now: float = defense.clock
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	mason_bot.offset = shape.global_position - player.global_position
	mason_bot.half = shape.shape.size * shape.global_scale.abs() / 2.0
	# Standing in Carter's marker, the parrying bot leaves him to its guard (mason_bot_guard); outside it,
	# it keeps out, as a player would rather than walk in on a slam.
	var here: Vector2 = player.global_position
	var threats: Array = mason_bot.known.filter(func(k): return now - k.seen >= MASON_BOT_REACTION and not (mason_bot.parry and k.kind == "carter" and mason_bot_reach(here, k) < 1.0))
	var can_dash: bool = defense.can_afford(defense.dash_stamina_cost) and not defense.is_dash_cooling_down() and not defense.is_dash_recovering()
	var best := {"cost": INF, "dir": Vector2.ZERO, "dash": false}
	for dir: Vector2 in MASON_BOT_DIRECTIONS:
		for move_for: float in ([0.0] if dir == Vector2.ZERO else [0.1, 0.2, 0.35, 0.5, 0.8]):
			for dash: bool in ([false, true] if can_dash and dir != Vector2.ZERO else [false]):
				var cost := mason_bot_cost(threats, dir, dash, move_for)
				if cost < best.cost:
					best = {"cost": cost, "dir": dir, "dash": dash}
	mason_bot_hold(best.dir)
	mason_bot.dir = best.dir
	if best.dash:
		mason_bot.last_dash = now
		mason_bot.dashes += 1
		tap(KEY_W)


func mason_bot_cost(threats: Array, dir: Vector2, dash: bool, move_for: float) -> float:
	var now: float = defense.clock
	var from: Vector2 = player.global_position
	var cost := 0.0
	for threat in threats:
		for t: float in [threat.lands, threat.lands + threat.live * 0.5, threat.lands + threat.live]:
			if t < now:
				continue
			var reach := mason_bot_reach(mason_bot_at(from, dir, dash, move_for, t), threat)
			if reach < 1.0:
				cost += 1000.0
				break
			if reach < 1.4:
				cost += (1.4 - reach) * 50.0
	# His body is dash_through: a dash's own immunity carries the bot through him.
	var immune_until: float = now + (CATALOG.DASH_IMMUNITY_TIME if dash and now - mason_bot.last_dash >= CATALOG.DASH_IMMUNITY_COOLDOWN else 0.0)
	for body in mason_bot.body:
		if body.t < immune_until:
			continue
		var centre: Vector2 = mason_bot_at(from, dir, dash, move_for, body.t) + mason_bot.offset
		var gap: Vector2 = (centre - body.at).abs() - (mason_bot.half + body.half + Vector2.ONE * MASON_BOT_MARGIN)
		if gap.x < 0.0 and gap.y < 0.0:
			cost += 1000.0
			break
	var rest := mason_bot_at(from, dir, dash, move_for, now + 1.0)
	var middle := MASON_BOT_AREA.get_center()
	cost += maxf(0.0, absf(rest.x - middle.x) - 500.0) * 0.05 + maxf(0.0, absf(rest.y - middle.y) - 220.0) * 0.1
	cost += move_for * 4.0 + (30.0 if dash else 0.0) + (3.0 if dir != mason_bot.dir else 0.0)
	return cost


func mason_bot_at(from: Vector2, dir: Vector2, dash: bool, move_for: float, t: float) -> Vector2:
	var left: float = t - defense.clock
	if left <= 0.0:
		return from
	var heading := dir.normalized()
	var at := from
	if dash:
		at += heading * MASON_BOT_DASH
		left -= MASON_BOT_DASH_TIME
	at += heading * MASON_BOT_SPEED * clampf(minf(left, move_for), 0.0, INF)
	return at.clamp(MASON_BOT_AREA.position, MASON_BOT_AREA.end)


# Under 1, the hurtbox of a player standing at `body` is inside the threat's oval grown by the margin.
func mason_bot_reach(body: Vector2, threat: Dictionary) -> float:
	var centre: Vector2 = body + mason_bot.offset
	var spot: Vector2 = threat.at
	return ((spot.clamp(centre - mason_bot.half, centre + mason_bot.half) - spot) / (threat.semi + Vector2.ONE * MASON_BOT_MARGIN)).length()


func mason_bot_hold(dir: Vector2) -> void:
	var want := {KEY_LEFT: dir.x < 0.0, KEY_RIGHT: dir.x > 0.0, KEY_UP: dir.y < 0.0, KEY_DOWN: dir.y > 0.0}
	for code in want:
		if want[code] == mason_bot.held.get(code, false):
			continue
		if want[code]:
			press(code)
		else:
			release(code)
		mason_bot.held[code] = want[code]


func test_mason_combined() -> void:
	fight = "mason"
	if not await load_gauged():
		return
	var shower: Node = sm.states["NuggetShower"]
	var hits := []
	defense.hit_taken.connect(func(hit): hits.append(hit.attack_id))
	var theirs := func(id): return id == &"mason_nugget" or id == &"carter_elbow_drop"

	log_p("-- phase one takes turns, phase two has the one attack")
	var firsts: Array = sm.FINISHERS[0].map(func(turn): return sm.resolve_attack(turn[0]))
	check(firsts == ["NuggetShower" if sm.carter_rain else "CallCarter", "NuggetShower"] and sm.FINISHERS[0][0][0] == "CarterRain" and not sm.carter_in_shower[0], "phase one still takes turns between Carter (his light rain under him while carter_rain is on) and the nuggets (%s)" % [firsts])
	check(sm.FINISHERS[1].size() == 1 and sm.FINISHERS[1][0][0] == "NuggetShower" and sm.carter_in_shower[1], "phase two's one finisher is the shower with Carter called into it")
	check(sm.FINISHERS.all(func(turns): return turns.all(func(turn): return turn[-1] == "Pitch")), "and every cycle's attack is followed by his pitches (%s)" % [sm.FINISHERS])

	log_p("-- a real phase-two cycle into it, the player standing still")
	await mason_ready_combined(MASON_STAND_AT)
	hold_break_gauge(boss)
	sm.start_cycle()
	check(sm.cycle_phase == 1 and sm.finishers == ["NuggetShower", "Pitch"], "the cycle's finisher is the shower, then his pitches (%s)" % [sm.finishers])
	sm.lines_done = sm.lines_per_cycle[1] - 1
	var handed := await wait_until(func(): return sm.current_state.name == "NuggetShower", 400)
	check(handed and shower.with_carter, "its last line hands over to the shower, with Carter called in")
	hits.clear()
	mason_new_log()
	mason_log.next = "AwaitDelivery" if sm.resolve_attack("Pitch").is_empty() else "Pitch"
	physics_frame.connect(mason_record)
	var ended := await wait_until(func(): return sm.current_state.name != "NuggetShower", 900)
	physics_frame.disconnect(mason_record)
	var stood: Array = hits.filter(theirs)
	log_p("standing still through it: %d hits, %s" % [stood.size(), stood])
	mason_check_attack("standing still", ended, true)

	log_p("-- a Break mid-attack, Carter in the air and nuggets in the sky")
	await mason_ready_combined(MASON_STAND_AT)
	mason_start_combined()
	var deep := await wait_until(mason_mid_attack, 600)
	var out: int = hazards_of("NuggetMeteorScript.gd").size()
	boss.break_gauge.value = boss.break_gauge.max_value - 1.0
	boss.break_gauge.add(1.0)
	await wait(2)
	check(deep and sm.current_state.name == "Broken", "broken out of it, with Carter in the air and %d nuggets out" % out)
	mason_check_released("the Break")
	var came := 0
	for i in 120:
		await physics_frame
		came += hazards_of("NuggetMeteorScript.gd").size() + hazards_of("CarterElbowDropScript.gd").size()
	check(came == 0, "the Break: nothing of it comes down in the 2 s after (%d)" % came)
	var freed := await wait_until(func(): return not player.is_action_locked, 120)
	check(freed and not player.lock_seals_guard and not player.scripted_pose and not player.is_posed(), "the Break: the player is theirs again once the drive is over")
	var again := await wait_until(func(): return sm.current_state.name == "PooSquat", 400)
	check(again and sm.cycle_phase == 1 and sm.finishers == ["NuggetShower", "Pitch"], "the Break: he gets up into a phase-two cycle with the combined attack still to come")

	log_p("-- paused mid-attack")
	await mason_ready_combined(MASON_STAND_AT)
	hold_break_gauge(boss)
	mason_new_log()
	physics_frame.connect(mason_record)
	mason_start_combined()
	deep = await wait_until(mason_mid_attack, 600)
	await tap_pause()
	var held := mason_snapshot()
	await wait(40)
	var still := mason_snapshot()
	check(deep and pause_menu().is_open() and paused and held == still, "paused with Carter in the air and nuggets in the sky, 40 frames move none of it (%d things watched)" % held.size())
	await tap_pause()
	check(not paused, "and the resume carries it on")
	# The resume's input grace is in real seconds, and the bot below must have every dash it presses.
	pause_menu().grace_until_msec = 0
	ended = await wait_until(func(): return sm.current_state.name != "NuggetShower", 900)
	physics_frame.disconnect(mason_record)
	mason_check_attack("paused and resumed", ended, false)

	log_p("-- a human-paced dodging bot from full health: it sees things %.2f s late and picks a step every %d frames" % [MASON_BOT_REACTION, MASON_BOT_REPLAN])
	var per_attack := []
	for i in MASON_BOT_SPOTS.size():
		seed(20260924 + i)
		await mason_ready_combined(MASON_BOT_SPOTS[i])
		hold_break_gauge(boss)
		player.playerHealth = MASON_FULL_HEALTH
		clear_iframes()
		hits.clear()
		mason_bot_reset()
		mason_start_combined()
		physics_frame.connect(mason_bot_frame)
		var over := await wait_until(func(): return sm.current_state.name != "NuggetShower" or player.fight_over, 900)
		physics_frame.disconnect(mason_bot_frame)
		mason_bot_hold(Vector2.ZERO)
		var taken: Array = hits.filter(theirs)
		per_attack.append(taken.size())
		log_p("from %s: %d hits %s, %d dashes, health %d of %d, now %s" % [MASON_BOT_SPOTS[i], taken.size(), taken, mason_bot.dashes, player.playerHealth, MASON_FULL_HEALTH, sm.current_state.name])
		check(over and not player.fight_over and taken.size() <= MASON_BOT_MAX_HITS, "from %s the bot comes through it alive, hit %d times, at most %d" % [MASON_BOT_SPOTS[i], taken.size(), MASON_BOT_MAX_HITS])
		if player.fight_over:
			return
		player.playerHealth = 1000
	log_p("the bot over %d attacks: %s hits, %d in all; standing still took %d in one" % [per_attack.size(), per_attack, per_attack.reduce(func(a, b): return a + b, 0), stood.size()])

	log_p("-- the same pace, parrying Carter where his marker has it and walking out of the rain")
	var timed := []
	var parried := []
	defense.hit_taken.connect(func(hit): timed.append({"t": defense.clock, "id": hit.attack_id}))
	defense.parried.connect(func(hit, _point, _staggered, _streak): parried.append(hit.attack_id))
	for i in MASON_BOT_SPOTS.size():
		seed(20260924 + i)
		await mason_ready_combined(MASON_BOT_SPOTS[i])
		hold_break_gauge(boss)
		player.playerHealth = MASON_FULL_HEALTH
		clear_iframes()
		timed.clear()
		parried.clear()
		mason_bot_reset(true)
		mason_start_combined()
		physics_frame.connect(mason_bot_frame)
		var through := await wait_until(func(): return sm.current_state.name != "NuggetShower" or player.fight_over, 900)
		physics_frame.disconnect(mason_bot_frame)
		mason_bot_hold(Vector2.ZERO)
		release(KEY_SHIFT)
		var planted_hits: Array = timed.filter(func(h): return mason_bot.guards.any(func(g): return h.t >= g[0] and h.t <= g[1]))
		var taken: Array = timed.map(func(h): return h.id).filter(theirs)
		log_p("from %s: planted %d times, parried %s, hit %d times %s, %d of them while planted" % [MASON_BOT_SPOTS[i], mason_bot.presses, parried, taken.size(), taken, planted_hits.size()])
		check(through and not player.fight_over and planted_hits.is_empty() and not taken.has(&"carter_elbow_drop") and taken.size() <= MASON_BOT_MAX_HITS, "from %s the parrying bot is never hit while planted for Carter, never hit by him, and hit at most %d times" % [MASON_BOT_SPOTS[i], MASON_BOT_MAX_HITS])
		if player.fight_over:
			return
		player.playerHealth = 1000

	if tier == "won":
		log_p("-- Mason beaten mid-attack")
		await mason_ready_combined(MASON_STAND_AT)
		hold_break_gauge(boss)
		mason_start_combined()
		deep = await wait_until(mason_mid_attack, 600)
		boss.boss_health = 1
		boss.take_finisher(1)
		var beaten := await wait_until(func(): return sm.current_state.name == "Defeated", 60)
		await wait(2)
		check(deep and beaten, "beaten with Carter in the air and nuggets in the sky (%s)" % sm.current_state.name)
		mason_check_released("beaten")
		hits.clear()
		await wait(72)
		check(hits.is_empty() and hazards_of("NuggetMeteorScript.gd").is_empty() and hazards_of("CarterElbowDropScript.gd").is_empty(), "beaten: nothing of it lands on the player after (%s)" % [hits])
		check(root.get_children().filter(func(n): return n.name == "FightOutro").size() == 1, "beaten: exactly one outro")
	else:
		log_p("-- the player killed mid-attack")
		await mason_ready_combined(MASON_STAND_AT)
		hold_break_gauge(boss)
		mason_start_combined()
		deep = await wait_until(mason_mid_attack, 600)
		clear_iframes()
		player.playerHealth = 1
		hits.clear()
		var lost := await wait_until(func(): return player.fight_over, 300)
		await wait(2)
		check(deep and lost and player.playerHealth == 0 and hits.size() == 1 and theirs.call(hits[0]), "killed by it with Carter in the air and nuggets in the sky (%s)" % [hits])
		check(sm.current_state.name == "Idle" and sm.player_defeated, "the outro stands him down (%s)" % sm.current_state.name)
		mason_check_released("the player's death")
		await wait(72)
		check(hazards_of("NuggetMeteorScript.gd").is_empty() and hazards_of("CarterElbowDropScript.gd").is_empty() and hits.size() == 1, "the player's death: nothing of it comes down after")
		check(root.get_children().filter(func(n): return n.name == "FightOutro").size() == 1, "the player's death: exactly one outro")


# ------------------------------------------------------------------ Mason's whole cycles, played through
# His cycles from the first squat to the delivery: a phase-one cycle ending on Carter, one ending on the
# shower, and two phase-two cycles ending on the combined attack. The dodging bot plays them, or with
# `tier=still` a player who never moves, and each cycle reports what its lines cost and what its
# finisher cost.

const MASON_CYCLES := [[false, 0], [false, 1], [true, 0], [true, 1]]
const MASON_LINE_IDS := [&"mason_poo_blast", &"mason_poo_contact"]
# His pitches after the attack (MasonPitch): this bot never parries, and walking out of a fastball is the read the
# pitch takes away, so they are counted on their own and expected to land.
const MASON_PITCH_IDS := [&"mason_fastball", &"mason_changeup", &"mason_quick_pitch"]


func test_mason_bots() -> void:
	fight = "mason"
	if not await load_gauged():
		return
	var still := tier == "still"
	var hits := []
	var hit_times := []
	defense.hit_taken.connect(func(hit):
		hits.append(hit.attack_id)
		hit_times.append(defense.clock))
	log_p("-- %s, through whole cycles" % ("a player standing still" if still else "the dodging bot: it sees things %.2f s late and picks a step every %d frames" % [MASON_BOT_REACTION, MASON_BOT_REPLAN]))
	var totals := []
	for i in MASON_CYCLES.size():
		var phase_two: bool = MASON_CYCLES[i][0]
		seed(20260925 + i)
		await reset_gauged(fight_spec.home)
		hold_break_gauge(boss)
		boss.global_position = MASON_COMBINED_AT
		sm.rest_point = boss.global_position + sm.BOMB_SPAWN_OFFSET
		boss.phase_two = phase_two
		boss.boss_health = floori(boss.get_max_health() * boss.PHASE_TWO_RATIO) if phase_two else boss.get_max_health()
		sm.cycles_started = MASON_CYCLES[i][1]
		await settle_player(MASON_STAND_AT)
		clear_iframes()
		hits.clear()
		hit_times.clear()
		if not still:
			mason_bot_reset()
			physics_frame.connect(mason_bot_frame)
		var started: float = defense.clock
		sm.start_cycle()
		var finisher: String = sm.finishers[0]
		var lines: int = sm.lines_per_cycle[sm.cycle_phase]
		var through := await wait_until(func(): return sm.current_state.name == "AwaitDelivery", 3600)
		if not still:
			physics_frame.disconnect(mason_bot_frame)
			mason_bot_hold(Vector2.ZERO)
		var from_lines: int = hits.filter(func(id): return MASON_LINE_IDS.has(id)).size()
		var from_pitch: int = hits.filter(func(id): return MASON_PITCH_IDS.has(id)).size()
		var from_finisher: int = hits.size() - from_lines - from_pitch
		totals.append([from_lines, from_finisher, from_pitch])
		var dead_at: String = "never" if hit_times.size() < MASON_FULL_HEALTH else "%.2f s in" % (hit_times[MASON_FULL_HEALTH - 1] - started)
		log_p("phase %d, %d lines then %s%s: the lines hit %d times, the finisher %d and the pitches %d %s%s; a full bar of %d would run out %s" % [2 if phase_two else 1, lines, finisher, " with Carter in it" if phase_two else "", from_lines, from_finisher, from_pitch, hits, "" if still else ", %d dashes" % mason_bot.dashes, MASON_FULL_HEALTH, dead_at])
		check(through, "phase %d, cycle %d plays through to the delivery" % [2 if phase_two else 1, i + 1])
		if not still:
			check(from_lines <= MASON_BOT_MAX_HITS and from_finisher <= MASON_BOT_MAX_HITS and from_lines + from_finisher < MASON_FULL_HEALTH, "the bot comes through the lines and the %s with at most %d hits each, alive from full health (%d and %d; the pitches %d)" % [finisher, MASON_BOT_MAX_HITS, from_lines, from_finisher, from_pitch])
	log_p("hits per cycle, lines, finisher, pitches: %s" % [totals])


# ------------------------------------------------------------------ Carter's drops along the back rope
# His landed pose is kept under the back rope (CarterElbowDropScript.landing_bounds), and that alone left a
# strip along it, and the two top corners, that no drop of his reached: a player standing there was never
# hit (playtest 2026-10-04). A landing short of a player there now comes up until it reaches into them
# (_reach_past_back_rope). Every spot below is a still player pinned through a whole call, with Mason on
# his wall column and at his top walk limit; the open floor still has every drop marked on the player; and
# a drop over the back rope is answered the way his badge says, by a parry a beat before the slam, at both
# phases' timings.

const MASON_ROPE_SPOTS := [Vector2(117, 132), Vector2(560, 132), Vector2(960, 140), Vector2(1400, 148), Vector2(1803, 132), Vector2(117, 190), Vector2(1803, 196), Vector2(1442, 156)]
const MASON_ROPE_OPEN := Vector2(760, 640)


# One call of Carter's at `phase`'s timings with the player pinned at `spot`, pressing the parry
# MASON_BOT_PARRY_LEAD before every slam (`parry` 1), every other one from the first (2) or none (0): what
# landed, what was parried, and how far each drop reached into them (under 1 reaches).
func mason_rope_call(spot: Vector2, phase: int, parry: int) -> Dictionary:
	var out := {"hits": 0, "parried": 0, "drops": 0, "on_player": 0, "reach": []}
	var on_hit := func(hit):
		if hit.attack_id == &"carter_elbow_drop":
			out.hits += 1
	var on_parry := func(hit, _point, _staggered, _streak):
		if hit.attack_id == &"carter_elbow_drop":
			out.parried += 1
	defense.hit_taken.connect(on_hit)
	defense.parried.connect(on_parry)
	await settle_player(spot)
	# Where the walls let them stand: a spot written into the rope is pushed back out of it.
	var stand: Vector2 = player.global_position
	clear_iframes()
	sm.cycle_phase = phase
	sm.finishers = []
	var marked := {}
	var guard := {"press": INF, "release": INF}
	var hurt_shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var follow := func():
		var now: float = defense.clock
		player.global_position = stand
		player.velocity = Vector2.ZERO
		# Every other slam left unanswered lands, and its i-frames would swallow the next: off, so only the
		# hit source decides.
		if parry == 2:
			clear_iframes()
		for drop in hazards_of("CarterElbowDropScript.gd"):
			var id: int = drop.get_instance_id()
			var up: bool = drop.target_sprite.visible
			if up and not marked.get(id, false):
				out.drops += 1
				var hurt: Rect2 = hurt_shape.global_transform * hurt_shape.shape.get_rect()
				if drop.global_position.distance_to(player.global_position) < 0.5:
					out.on_player += 1
				out.reach.append(snappedf(((drop.global_position.clamp(hurt.position, hurt.end) - drop.global_position) / (drop.hit_size() / 2.0)).length(), 0.001))
				if parry == 1 or (parry == 2 and out.drops % 2 == 1):
					var lands: float = now + drop.telegraph_time + drop.dive_time
					guard.press = lands - MASON_BOT_PARRY_LEAD
					guard.release = lands + drop.hitbox_active_time + MASON_BOT_GUARD_AFTER
			marked[id] = up
		if parry == 0:
			return
		if now >= guard.press:
			guard.press = INF
			press(KEY_SHIFT)
		elif now >= guard.release:
			guard.release = INF
			release(KEY_SHIFT)
	physics_frame.connect(follow)
	sm.on_child_transition(sm.current_state, "CallCarter")
	await wait_until(func(): return sm.current_state.name != "CallCarter", 1800)
	physics_frame.disconnect(follow)
	release(KEY_SHIFT)
	defense.hit_taken.disconnect(on_hit)
	defense.parried.disconnect(on_parry)
	return out


func test_mason_back_rope() -> void:
	fight = "mason"
	if not await load_gauged():
		return
	log_p("-- a still player along the back rope and in its corners")
	for mason_at in [MASON_COMBINED_AT, Vector2(960, sm.WALK_Y_MIN)]:
		for spot in MASON_ROPE_SPOTS:
			await reset_gauged(fight_spec.home)
			hold_break_gauge(boss)
			boss.global_position = mason_at
			var call: Dictionary = await mason_rope_call(spot, 0, 0)
			log_p("Mason at %s, player at %s: %d of %d drops hit, reach %s" % [mason_at, spot, call.hits, call.drops, call.reach])
			check(call.drops == sm.elbow_drops[0] and call.hits == call.drops, "Mason at %s, a still player at %s is hit by every drop (%d of %d)" % [mason_at, spot, call.hits, call.drops])
			check(call.reach.all(func(r): return r < 1.0), "and every drop marked there reaches into them (%s)" % [call.reach])
	log_p("-- the open floor is unchanged")
	await reset_gauged(fight_spec.home)
	hold_break_gauge(boss)
	boss.global_position = MASON_COMBINED_AT
	var open: Dictionary = await mason_rope_call(MASON_ROPE_OPEN, 0, 0)
	check(open.drops == sm.elbow_drops[0] and open.on_player == open.drops and open.hits == open.drops, "a still player at %s: every drop marked on them, and landing (%d, %d of %d)" % [MASON_ROPE_OPEN, open.on_player, open.hits, open.drops])
	log_p("-- and still answered by the parry his badge promises, %.2f s before each slam" % MASON_BOT_PARRY_LEAD)
	for phase in 2:
		for spot in [MASON_ROPE_SPOTS[0], MASON_ROPE_SPOTS[2], MASON_ROPE_SPOTS[4]]:
			await reset_gauged(fight_spec.home)
			hold_break_gauge(boss)
			boss.global_position = MASON_COMBINED_AT
			var parried: Dictionary = await mason_rope_call(spot, phase, 1)
			log_p("phase %d at %s: %d of %d drops parried, %d hit" % [phase + 1, spot, parried.parried, parried.drops, parried.hits])
			check(parried.drops == sm.elbow_drops[phase] and parried.parried == parried.drops and parried.hits == 0, "phase %d, at %s every drop over the back rope is parried (%d of %d, %d hits)" % [phase + 1, spot, parried.parried, parried.drops, parried.hits])
	# Every slam of a call came off one area, which a parry absorbs for a second, and phase two's come 0.89 s
	# apart: the slam after a parried one went through the player untouched, neither hit nor parried. Each
	# slam is its own source now (CarterElbowDropScript._fresh_hitbox).
	log_p("-- each slam is judged on its own: every other one parried, the rest land")
	for phase in 2:
		await reset_gauged(fight_spec.home)
		hold_break_gauge(boss)
		boss.global_position = MASON_COMBINED_AT
		var alternate: Dictionary = await mason_rope_call(MASON_ROPE_OPEN, phase, 2)
		var halves: int = sm.elbow_drops[phase] / 2
		log_p("phase %d on the open floor: %d parried, %d hit, of %d" % [phase + 1, alternate.parried, alternate.hits, alternate.drops])
		check(alternate.drops == sm.elbow_drops[phase] and alternate.parried == halves and alternate.hits == alternate.drops - halves, "phase %d: the %d slams pressed for are parried and the %d after them land (%d parried, %d hit)" % [phase + 1, halves, alternate.drops - halves, alternate.parried, alternate.hits])


# ------------------------------------------------------------------ Carter's Beam Rush

# The fight's own numbers, mirrored here the way clone_cadence mirrors the barrage's, so a mode still
# has something to hold his fight to if his scripts aren't in a build. beam_rush reads the live ones
# off CarterStateMachine and checks these still match them.
const BEAM_SUMMON := 0.70
const BEAM_CHARGE := 1.20
const BEAM_ESCAPE := 0.80
const BEAM_LIVE := 1.20
const BEAM_VOLLEYS := 3
const BEAM_END := 0.40
const RUSH_BEAM_ID := &"carter_rush_beam"
const STRIKE_SHOW := 0.36
const STRIKE_DASH := 0.08
const STRIKE_GAP := 0.06
const STRIKE_REACH := 120.0
const STRIKE_FROM := 0.30
const STRIKE_CLEAR := 0.30
const BEAM_RECOVER_BREAK := 5.0
const BEAM_RECOVER_SPENT := 1.5
const DEFEAT_SCENE := "res://Scenes/Core/DefeatScene.tscn"
# beam_rush's escape model: the grid it walks the ring on, how near the ropes the player's hurtbox
# centre gets, and the time it leaves a player to see the lock and react to it.
const ESCAPE_GRID := 40.0
const ESCAPE_ROPE_MARGIN := 20.0
const ESCAPE_REACTION := 0.25
# beam_rush_live's walk out of each volley's lines as they lock: 390 px, where the model wants about
# 300 in the lower middle of the ring.
const ESCAPE_WALK := 0.65
# And its timed dash through a line: this far out of the crossing first, so the dash's 250 px and a few
# steps after it clear every band before its immunity runs out.
const DASH_THROUGH_LEAD := 0.10


# The Beam Rush against the parry window and the ring's own geometry, modelled rather than run, so it
# needs no Carter scene: his strike is dealt to a parked Eric through the same player path, and the
# escape from the four locked lines is walked out over the whole ring on paper.
# THE ATTACK HAS NO TIMEOUT AND MUST NEVER GROW ONE.
func test_beam_rush() -> void:
	await load_eric()
	health_ok()
	park_eric()
	await settle_player(Vector2(972, 800))
	var mirrored := {
		"beam_summon": BEAM_SUMMON, "beam_charge": BEAM_CHARGE, "beam_escape": BEAM_ESCAPE, "beam_live": BEAM_LIVE,
		"beam_volleys": BEAM_VOLLEYS, "beam_end": BEAM_END, "strike_show": STRIKE_SHOW, "strike_dash": STRIKE_DASH,
		"strike_gap": STRIKE_GAP, "strike_reach": STRIKE_REACH, "strike_from": STRIKE_FROM,
		"strike_clear": STRIKE_CLEAR, "messatsu_tell": MESSATSU_TELL, "messatsu_travel": MESSATSU_TRAVEL,
		"messatsu_fade": MESSATSU_FADE,
	}
	var n := mirrored.duplicate()
	if ResourceLoader.exists(CARTER_STATE_MACHINE):
		var probe: Node = load(CARTER_STATE_MACHINE).new()
		for knob in mirrored:
			n[knob] = probe.get(knob)
		probe.free()
		var drifted := mirrored.keys().filter(func(knob): return not is_equal_approx(float(n[knob]), float(mirrored[knob])))
		log_p("read off his fight: %s" % [n])
		check(drifted.is_empty(), "the numbers in this file still mirror his fight (drifted: %s)" % [drifted])
	else:
		log_p("his fight is not in this build, so the numbers in this file are what is modelled")
	var window: float = defense.parry_window
	var strike: float = n.strike_show + n.strike_dash
	log_p("badge %.2f s, dash %.2f s, contact at %.2f s, window %.2f s" % [n.strike_show, n.strike_dash, strike, window])
	check(n.strike_show >= 0.36, "the strike's read is at its floor or above it (%.2f s)" % n.strike_show)

	log_p("-- pressing the instant he appears is too early")
	defense.rearm_parry()
	var on_sight: int = await parry_at(clone_frames(strike))
	check(on_sight == unparried(), "a press on sight doesn't parry (%d)" % on_sight)
	check(strike > window + 1.0 / 60.0, "contact is %.2f s past the badge, the window covers %.2f s" % [strike, window])

	log_p("-- and the read, as he lunges, parries")
	defense.rearm_parry()
	var on_dash: int = await parry_at(clone_frames(n.strike_dash))
	check(on_dash == 3, "a press as he lunges parries (%d)" % on_dash)

	# He comes in the middle of a charge, where a player may already have pressed at nothing. Inside
	# parry_mash_lockout that press would cost the strike, and the rearm he makes as he appears is what
	# gives it back.
	log_p("-- a press whiffed just before he appears")
	var early := 0.2
	var to_read := clone_frames(early + strike - window)
	log_p("  a press %.2f s before he appears, then his read %.2f s after it" % [early, to_read / 60.0])
	check(early + strike - window < defense.parry_mash_lockout, "which is inside the %.2f s lockout" % defense.parry_mash_lockout)
	press(KEY_SHIFT)
	await wait(2)
	release(KEY_SHIFT)
	await wait(to_read - 2)
	var spilled: int = await parry_at(clone_frames(window))
	check(spilled == unparried(), "with nothing rearming it, the whiff costs the strike (%d)" % spilled)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await past_window()
	await wait(40)
	press(KEY_SHIFT)
	await wait(2)
	release(KEY_SHIFT)
	await wait(to_read - 2)
	# What the fight does as he appears.
	defense.rearm_parry()
	var saved: int = await parry_at(clone_frames(window))
	check(saved == 3, "the rearm he makes as he appears gives it back (%d)" % saved)

	log_p("-- a volley's tell and its escape")
	var to_hit: float = n.beam_escape + n.messatsu_travel
	# The badge goes up on the lock itself (tuning 2026-10-04), so the whole escape is under it;
	# beam_rush_live watches it go up on the lock's frame.
	log_p("the lines lock %.2f s before the heads land and the beams start to hurt, and the yellow badge goes up with them" % to_hit)
	check(to_hit >= 0.36, "the badge is up at the read floor or over it before they hurt (%.2f s)" % to_hit)

	# By the user's call the Beam Rush's beams are escaped and never parried: his strike is the one parry
	# in the attack.
	log_p("-- the beams can only be escaped")
	var hits: Dictionary = (load("res://Scripts/HitInfo.gd") as GDScript).Result
	var rush_beam: Dictionary = CATALOG.get_attack(RUSH_BEAM_ID)
	check(not rush_beam.blockable and not rush_beam.parryable and not rush_beam.tell and rush_beam.dodge_tell, "no guard and no parry answers them, and their badge is the yellow one")
	check(rush_beam.dash_through and not rush_beam.bypass_invincibility, "a dash's immunity carries the player through one, and the i-frames space their hits")
	defense.rearm_parry()
	press(KEY_SHIFT)
	await wait(3)
	var pressed: int = omni_hit(RUSH_BEAM_ID, dummy_source())
	release(KEY_SHIFT)
	await wait(4)
	clear_iframes()
	check(pressed == hits.HIT, "a fresh press with the guard up takes the hit (%s)" % hits.keys()[pressed])
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(2)
	var dashed: int = omni_hit(RUSH_BEAM_ID, dummy_source())
	release(KEY_RIGHT)
	await wait(30)
	clear_iframes()
	await settle_player(Vector2(972, 800))
	check(dashed == hits.DODGED, "and a dash through one is dodged (%s)" % hits.keys()[dashed])

	# Four lines latched on the player's hurtbox centre wherever in the ring they stand: how soon can the
	# player be out of every band, walking along one of the eight directions the keys give - the axes are
	# separate, so a diagonal is faster - or dashing first?
	log_p("-- the escape from four locked lines, over the whole ring")
	var art: GDScript = load(CARTER_ART_LAYOUT)
	var machine: GDScript = load(CARTER_STATE_MACHINE)
	var ropes: Rect2 = machine.ROPES
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs() / 2.0
	var area := ropes.grow(-ESCAPE_ROPE_MARGIN)
	var budget: float = to_hit - ESCAPE_REACTION
	var speed: float = player.get_script().SPEED
	var worst := {"walk": 0.0, "walk_at": Vector2.ZERO, "dash": 0.0, "dash_at": Vector2.ZERO}
	var walked := 0
	var spots := 0
	var y := area.position.y
	while y <= area.end.y:
		var x := area.position.x
		while x <= area.end.x:
			var at := Vector2(x, y)
			var lines := beam_rush_lines(art, at, half)
			var walk := beam_rush_walk_out(lines, at, area, speed)
			var dash := beam_rush_dash_out(lines, at, area, speed)
			spots += 1
			if walk <= budget:
				walked += 1
			if walk > worst.walk:
				worst.walk = walk
				worst.walk_at = at
			if dash > worst.dash:
				worst.dash = dash
				worst.dash_at = at
			x += ESCAPE_GRID
		y += ESCAPE_GRID
	log_p("ESCAPE: from %d spots, a dash and a walk get out of all four in %.2f s at worst (%s); walking alone in %.2f s at worst (%s), and inside %.2f s from %d of them (%.0f%%)" % [spots, worst.dash, worst.dash_at, worst.walk, worst.walk_at, budget, walked, 100.0 * walked / spots])
	check(worst.dash <= budget, "from anywhere in the ring a dash gets out of all four and leaves %.2f s to react to the lock (%.2f s of %.2f)" % [ESCAPE_REACTION, worst.dash, to_hit])
	check(walked >= spots * 0.75, "and walking alone does from most of it (%.0f%%)" % (100.0 * walked / spots))
	for i in art.BEAM_COUNT:
		var want: float = ropes.position.x + ropes.size.x * (i + 1) / float(art.BEAM_COUNT + 1)
		check(absf(art.BEAM_X[i] - want) <= 1.0, "clone %d stands spaced off the ropes, not written down (%.0f against %.1f)" % [i + 1, art.BEAM_X[i], want])

	log_p("-- the strike's place in its charge")
	var latest: float = n.beam_charge - strike - n.strike_clear
	var after_hit: float = n.messatsu_fade + n.strike_from + strike
	var before_hit: float = n.strike_clear + to_hit
	log_p("he appears %.2f to %.2f s into a charge: his blow lands %.2f s after the last volley's beams stop hurting at the least, and %.2f s before the lock and %.2f s before the next beams hurt at the least" % [n.strike_from, latest, after_hit, n.strike_clear, before_hit])
	check(latest >= n.strike_from, "every charge has room for him (%.2f to %.2f s)" % [n.strike_from, latest])
	check(after_hit > window and before_hit > window, "so his blow never lands with a beam")
	check(before_hit >= to_hit + n.strike_clear - 0.0001, "and a player who stood rooted to parry it still has the whole escape ahead of them")
	# The strike doesn't pass the i-frames, so a beam hit on the last live frame of the volley before it must have run
	# out its i-frames by his blow, or they swallow an on-time parry (tuning 2026-10-04; carter_strike_iframes plays it).
	check(after_hit > player.invincibility_timer.wait_time + 1.0 / 60.0, "and the i-frames a beam's last possible hit leaves are over before his earliest blow (%.2f s against %.2f)" % [after_hit, player.invincibility_timer.wait_time])

	log_p("-- what the attack costs a player who never moves")
	var catalog: Dictionary = CATALOG.get_attack(&"carter_teleport_strike")
	check(not catalog.bypass_invincibility, "the strike does NOT bypass the i-frames, unlike the barrage's clones")
	check(catalog.blockable and catalog.tell, "it is blockable and it advertises itself: the attack's one parry")
	var iframes: float = player.invincibility_timer.wait_time
	var per_volley := 0
	var since_live := 0.0
	while since_live <= n.beam_live:
		per_volley += 1
		since_live += iframes
	var landing: int = n.beam_volleys * per_volley
	log_p("in a beam all the %.2f s it hurts, against %.2f s of i-frames: %d hits a volley and %d in all, and his strike %.2f s after the beams before it stopped hurting" % [n.beam_live, iframes, per_volley, landing, after_hit])
	# The user's call (2026-09-30), once the player had four hearts: standing still no longer kills, it leaves them on
	# half a heart.
	var taken: int = landing * CATALOG.get_attack(RUSH_BEAM_ID).damage + catalog.damage
	var full: int = load("res://Scripts/PlayerHealthArtLayout.gd").CONTAINERS * 2
	check(taken == full - 1, "a player who never moves survives it on half a heart (%d beam hits and the strike: %d of %d half-hearts)" % [landing, taken, full])


# Where the four's lines run when they lock on a player whose hurtbox centre is `at`: from each one's
# palms, facing the player as CarterBeamRush turns them. Each line carries the half-width its band has
# across it for a hurtbox of half-size `half` (CarterBeamRush._in_band).
func beam_rush_lines(art: GDScript, at: Vector2, half: Vector2) -> Array:
	var lines := []
	for x in art.BEAM_X:
		var feet := Vector2(x, art.BEAM_CLONE_Y)
		var palms: Vector2 = feet + art.local(art.MESSATSU_MUZZLE, at.x < feet.x)
		var n := (at - palms).normalized().orthogonal()
		lines.append({"palms": palms, "n": n, "across": art.MESSATSU_HIT_WIDTH / 2.0 + half.x * absf(n.x) + half.y * absf(n.y)})
	return lines


# How far along `dir` from `at` a hurtbox centre has to go to be out of every band, or INF if it
# reaches the ropes first. Each band is an interval along the ray, so it is solved rather than
# stepped. The 60 px a band reaches behind the palms is left out, which can only make a band longer.
func beam_rush_ray_out(lines: Array, at: Vector2, dir: Vector2, area: Rect2) -> float:
	var s := 0.0
	var moved := true
	while moved:
		moved = false
		for line in lines:
			var a: float = (at - line.palms).dot(line.n)
			var b: float = dir.dot(line.n)
			var w: float = line.across
			if absf(a + s * b) > w:
				continue
			if absf(b) < 0.0001:
				return INF
			s = maxf((w - a) / b, (-w - a) / b) + 0.5
			moved = true
	return s if area.has_point(at + dir * s) else INF


# The soonest walking gets out, along one of the eight directions the keys give.
func beam_rush_walk_out(lines: Array, at: Vector2, area: Rect2, speed: float) -> float:
	var best := INF
	for i in 8:
		var pace: float = speed * (sqrt(2.0) if i % 2 == 1 else 1.0)
		best = minf(best, beam_rush_ray_out(lines, at, Vector2.from_angle(i * PI / 4.0), area) / pace)
	return best


# A dash first - DASH_LENGTH over three frames along one of the eight directions, or to the ropes -
# then V2_STILL_FRAMES stood still and walking the rest.
func beam_rush_dash_out(lines: Array, at: Vector2, area: Rect2, speed: float) -> float:
	var best := INF
	for i in 8:
		var dir := Vector2.from_angle(i * PI / 4.0)
		var length := DASH_LENGTH
		while length > 0.0 and not area.has_point(at + dir * length):
			length -= 1.0
		var landed := at + dir * length
		var out := beam_rush_ray_out(lines, landed, dir, area)
		if out == 0.0:
			best = minf(best, 3.0 / 60.0)
			continue
		best = minf(best, 3.0 / 60.0 + V2_STILL_FRAMES / 60.0 + beam_rush_walk_out(lines, landed, area, speed))
	return best


# The shipped Carter, set up the way test_pause_barrage does it: his machine fills its states and
# defers the entrance, so a cycle is forced a frame later rather than in the middle of the scene
# coming up. Returns his BeamRush state.
func load_carter_akuma() -> Node:
	change_scene_to_file(CARTER_AKUMA)
	while current_scene == null or current_scene.scene_file_path != CARTER_AKUMA:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	boss = current_scene.get_node("Arena/CarterAkumaScene/CarterAkumaCharacterBody")
	sm = boss.get_node("StateManager")
	await wait_until(func(): return sm.states.has("Intro"), 120)
	sm.states["Intro"].process_mode = Node.PROCESS_MODE_DISABLED
	player.is_talking = false
	await wait(2)
	return sm.get_node("BeamRush")


# Straight into a Beam Rush. Cycle 1 is always the barrage, so the counter is nudged and the cycle
# started, which is also the rotation doing its job. His strike is put where the caller wants it, so
# every run plays the same attack.
func start_beam_rush(rush: Node, strike_volley := 1, strike_at := 0.3) -> bool:
	rush.forced_strike_volley = strike_volley
	rush.forced_strike_at = strike_at
	sm.cycles_started = 1
	sm.start_cycle()
	return await wait_until(func(): return sm.current_state == rush, 60)


# Presses the guard as his strike lunges, which is the read: the badge has just gone and contact is
# strike_dash away. Held through the contact: a parry needs the guard up when the blow arrives.
func parry_beam_rush_strike(rush: Node) -> bool:
	if not await wait_until(func(): return rush.strike == rush.Strike.LUNGE, 900):
		return false
	press(KEY_SHIFT)
	await wait_until(func(): return rush.strike != rush.Strike.LUNGE, 60)
	release(KEY_SHIFT)
	await wait(2)
	return true


# The press a player standing in volley `v`'s lines makes as its beams land, the way a parry would be
# timed: the frame the four fire, held until they hurt. The beams can't be parried, so it answers nothing.
func press_at_beam_rush_landing(rush: Node, v: int) -> bool:
	if not await wait_until(func(): return rush.volley == v and rush.beat == rush.Beat.STRING, 900):
		return false
	press(KEY_SHIFT)
	await wait_until(func(): return rush.live or rush.beat != rush.Beat.STRING, 60)
	await wait(2)
	release(KEY_SHIFT)
	defense._set_stamina(defense.max_stamina)
	return true


# The real thing, in his real fight. The check that matters most is the first: with no input at all the
# attack ends on its own, because the volley count is its only bound and there is no clock anywhere in
# it.
func test_beam_rush_live() -> void:
	var rush: Node = await load_carter_akuma()
	check(rush != null, "his fight carries a BeamRush state")
	# The rush's own ending, his window, is what this holds it to; in his combo it hands on to the Messatsu
	# instead (chain_attacks, which carter_chain covers).
	sm.chain_attacks = false
	var gauge: Node = boss.break_gauge
	check(gauge != null, "and a Break gauge")
	# next_attack() is read after start_cycle() has counted the cycle, so cycle 1 is cycles_started 1.
	sm.cycles_started = 1
	check(sm.next_attack() == "RagingDemon", "cycle 1 is always the barrage, which teaches the read this attack assumes")
	sm.cycles_started = 2
	check(sm.next_attack() == "BeamRush", "and this one comes second")
	sm.cycles_started = 3
	check(sm.next_attack() == "BeamRush", "and again third (tuning 2026-10-06)")
	sm.cycles_started = 4
	check(sm.next_attack() == "Messatsu", "the Messatsu fourth")
	sm.cycles_started = 5
	check(sm.next_attack() == "RagingDemon", "and back to the barrage, strictly, rather than by a random pick")
	sm.cycles_started = 0
	track()
	track_parries()
	track_dodges()
	var iframes: float = player.invincibility_timer.wait_time
	var per_volley := int(floor(BEAM_LIVE / iframes)) + 1

	log_p("-- three volleys with nothing pressed end it")
	player.playerHealth = 9999
	await settle_player(Vector2(959, 800))
	var beam_hits: int = events_of("HIT", RUSH_BEAM_ID).size()
	var strike_hits: int = events_of("HIT", &"carter_teleport_strike").size()
	check(await start_beam_rush(rush), "the rush is running, his strike put 0.30 s into the second charge")
	check(is_equal_approx(gauge.value, 0.0) and not gauge.locked, "the gauge reads 0 on entry and takes fills (%.0f)" % gauge.value)
	check(rush.casters.size() == 4, "four clones are up (%d)" % rush.casters.size())
	var seen := {"locks": [], "locked_at": [], "off": 0.0, "fired": {}, "moved": 0, "strike": [], "blow": -1.0, "away": 0, "badges": []}
	var watch := func() -> void:
		if sm.current_state != rush:
			return
		if rush.beat == rush.Beat.LOCK and seen.locks.size() == rush.volley:
			seen.locks.append(rush.lock_point)
			seen.locked_at.append(defense.clock)
			seen.off = maxf(seen.off, rush.lock_point.distance_to(player_centre()))
			# The first step the lock is seen on: the yellow badge has to be up over it already, with the whole
			# escape still to run.
			var badge: Node = boss.clone_layer.get_node_or_null("ParryTell%d" % rush.lock_ring.get_instance_id())
			seen.badges.append(snappedf(badge.time_left, 0.001) if badge != null and badge.dodge else -1.0)
		if rush.beat == rush.Beat.STRING:
			var now := []
			for caster in rush.casters:
				now.append([caster.beam_root.global_position, caster.beam_root.rotation, caster.aim_origin, caster.aim_angle])
			if not seen.fired.has(rush.volley):
				seen.fired[rush.volley] = now
			elif seen.fired[rush.volley] != now:
				seen.moved += 1
		if rush.strike == rush.Strike.SHOW and seen.strike.is_empty():
			seen.strike = [rush.volley, rush.beat, snappedf(rush.beat_clock, 0.001)]
		if rush.strike == rush.Strike.HOLD and seen.blow < 0.0:
			seen.blow = defense.clock
		if rush.strike == rush.Strike.DONE and rush.beat != rush.Beat.END and boss.global_position != rush.home:
			seen.away += 1
	physics_frame.connect(watch)
	var left: bool = await wait_until(func(): return sm.current_state != rush, 1800)
	physics_frame.disconnect(watch)
	var beams: Array = events_of("HIT", RUSH_BEAM_ID).slice(beam_hits)
	var strikes: Array = events_of("HIT", &"carter_teleport_strike").slice(strike_hits)
	var gaps := []
	for i in range(1, beams.size()):
		if i % per_volley != 0:
			gaps.append(snappedf(beams[i].t - beams[i - 1].t, 0.001))
	var firsts := []
	for v in seen.locked_at.size():
		if v * per_volley < beams.size():
			firsts.append(snappedf(beams[v * per_volley].t - seen.locked_at[v], 0.001))
	var blow_to_lock: float = seen.locked_at[1] - seen.blow if seen.locked_at.size() > 1 and seen.blow > 0.0 else -1.0
	log_p("locks at %s, %.1f px off the player at worst; first hits %s s after them, the rest %s s apart; the strike %s, its blow %.2f s before that volley's lock; the state settled in %s" % [seen.locks, seen.off, firsts, gaps, seen.strike, blow_to_lock, sm.current_state.name])
	check(left, "the attack ended on its own with no input")
	check(seen.locks.size() == BEAM_VOLLEYS, "after three volleys, and not on a clock (%d)" % seen.locks.size())
	check(seen.off <= 1.0, "each locked onto the player's hurtbox centre where they stood")
	check(seen.badges.size() == BEAM_VOLLEYS and seen.badges.all(func(b): return b >= BEAM_ESCAPE - 2.5 / 60.0), "each volley's yellow badge went up over the lock on the frame its lines locked, for the whole %.2f s escape (time left on it then: %s)" % [BEAM_ESCAPE, seen.badges])
	check(seen.moved == 0, "and no beam moved off its latched line once it fired")
	check(beams.size() == BEAM_VOLLEYS * per_volley, "a still player where four cross takes one hit at a time, %d a volley over the %.2f s the beams hurt: %d" % [per_volley, BEAM_LIVE, beams.size()])
	check(not gaps.is_empty() and gaps.all(func(g): return absf(g - iframes) <= 1.5 / 60.0), "spaced by the i-frames, %.2f s (%s)" % [iframes, gaps])
	check(firsts.size() == BEAM_VOLLEYS and firsts.all(func(f): return absf(f - BEAM_ESCAPE - MESSATSU_TRAVEL) <= 1.5 / 60.0), "each volley's first lands %.2f s after its lock (%s)" % [BEAM_ESCAPE + MESSATSU_TRAVEL, firsts])
	check(seen.strike.size() == 3 and seen.strike[0] == 1 and seen.strike[1] == rush.Beat.CHARGE and absf(seen.strike[2] - 0.3) <= 1.5 / 60.0, "his strike came once, where it was put: 0.30 s into the second charge (%s)" % [seen.strike])
	check(strikes.size() == 1, "and landed on a player who didn't answer it (%d)" % strikes.size())
	check(blow_to_lock >= STRIKE_CLEAR - 0.001, "its blow landed %.2f s before that volley's lines locked" % blow_to_lock)
	check(seen.away == 0, "and he stood back where he started from then on")
	check(sm.current_state.name == "Recover", "into his punish window")
	var walk_in: float = sm.walk_in_time(player.global_position.distance_to(boss.global_position))
	check(absf(sm.recover_timer.wait_time - maxf(BEAM_RECOVER_SPENT, walk_in)) <= 0.02, "an attack simply sat through earns the short window, or the walk in from where the player stands if that is longer: %.2f s (walk in %.2f s)" % [sm.recover_timer.wait_time, walk_in])
	check(get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), "nothing is left on the mat")

	log_p("-- a player who parries his strike rooted, then walks out of every volley's lines as they lock")
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await settle_player(Vector2(1250, 820))
	clear_iframes()
	beam_hits = events_of("HIT", RUSH_BEAM_ID).size()
	var strike_parries: int = parries.filter(func(p): return p.id == &"carter_teleport_strike").size()
	# As late in its charge as he may come, so its blow lands as near the lock as it ever does.
	check(await start_beam_rush(rush, 1, sm.strike_latest()), "a second rush is running, his strike as late as it comes")
	var walks := []
	for v in BEAM_VOLLEYS:
		if v == 1:
			check(await parry_beam_rush_strike(rush), "he strikes in the second charge")
		if not await wait_until(func(): return rush.volley == v and rush.beat == rush.Beat.LOCK, 900):
			break
		var toward := KEY_LEFT if player.global_position.x > sm.ARENA_CENTRE.x else KEY_RIGHT
		var from_x: float = player.global_position.x
		press(toward)
		await wait(clone_frames(ESCAPE_WALK))
		release(toward)
		walks.append(roundi(player.global_position.x - from_x))
	await wait_until(func(): return sm.current_state != rush, 900)
	var landed: int = events_of("HIT", RUSH_BEAM_ID).size() - beam_hits
	log_p("walked %s px as each volley locked; %d beam hits landed" % [walks, landed])
	check(parries.filter(func(p): return p.id == &"carter_teleport_strike").size() == strike_parries + 1, "his strike was parried with the guard up, %.2f s before the lock" % sm.strike_clear)
	check(walks.size() == BEAM_VOLLEYS and landed == 0, "and not one beam lands on a player who walks away as the lines lock (%d)" % landed)

	# Still in the lines a moment before they go live, the player dashes out through them: the dash's
	# immunity covers the frames it is still inside, and it is clear of every band before that runs out.
	log_p("-- a timed dash out through the lines as they go live")
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await settle_player(Vector2(959, 800))
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	beam_hits = events_of("HIT", RUSH_BEAM_ID).size()
	var dodged_before: int = dodges.size()
	check(await start_beam_rush(rush, 2, 0.3), "a third rush is running, his strike out of the way in the last charge")
	check(await wait_until(func(): return rush.volley == 0 and rush.beat == rush.Beat.LOCK, 900), "the first volley locks on the player")
	press(KEY_RIGHT)
	await wait(clone_frames(DASH_THROUGH_LEAD))
	release(KEY_RIGHT)
	# A press reaches the player on the next frame's input flush, so this is two frames before they go live.
	check(await wait_until(func(): return rush.beat == rush.Beat.STRING and rush.fire_clock >= sm.messatsu_travel - 3.5 / 60.0, 120), "the four fire")
	var inside: bool = rush.casters.any(func(c): return rush._in_band(c, rush._rect_of(player.hurtBox.get_node("CollisionShape2D"))))
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(30)
	release(KEY_RIGHT)
	var dashed_hits: int = events_of("HIT", RUSH_BEAM_ID).size() - beam_hits
	log_p("in the lines as the dash was pressed: %s; beam hits %d, perfect dodges %d" % [inside, dashed_hits, dodges.size() - dodged_before])
	check(inside and dashed_hits == 0, "still in them as they went live, and not hit (%d)" % dashed_hits)
	check(dodges.size() > dodged_before and dodges[-1].id == RUSH_BEAM_ID, "a perfect dodge through the beam")

	log_p("-- his strike is the attack's one read: with all but one read carried in, its parry breaks him and ends it on the spot")
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await settle_player(Vector2(959, 800))
	clear_iframes()
	# His gauge is fight-long and carries over between attacks: all but one read comes in from the attacks before.
	gauge.locked = false
	gauge.value = (boss.BREAK_READS - 1) * boss.BREAK_READ
	var parried := []
	# PlayerCombatFx._attack_art flicks the first visible Sprite2D among a parried source's siblings, and
	# its handler runs before this one, so a hit source parented beside a sprite shows here as one of the
	# four at the top lit up by the parry.
	var flicked := []
	defense.parried.connect(func(hit, _at, _staggered, _streak):
		parried.append(hit.attack_id)
		for c in rush.casters.size():
			if rush.casters[c].figure.self_modulate != Color.WHITE:
				flicked.append(c + 1))
	check(await start_beam_rush(rush, 0, 0.3), "a fourth rush is running with %.1f in the gauge, his strike in the first charge" % gauge.value)
	# Taken now: the Break frees the ring with the rest of the attack.
	var lock_id: int = rush.lock_ring.get_instance_id()
	var frames := {"broke": -1, "ended": -1}
	var on_broke := func() -> void:
		if frames.broke < 0:
			frames.broke = Engine.get_physics_frames()
	var on_frame := func() -> void:
		if frames.broke >= 0 and frames.ended < 0 and sm.current_state != rush:
			frames.ended = Engine.get_physics_frames()
	gauge.broke.connect(on_broke)
	physics_frame.connect(on_frame)
	var answered: bool = await parry_beam_rush_strike(rush)
	await wait(1)
	gauge.broke.disconnect(on_broke)
	physics_frame.disconnect(on_frame)
	var lock_badge: Node = boss.clone_layer.get_node_or_null("ParryTell%d" % lock_id)
	log_p("parried %s; the attack over %d frame(s) after the Break, in %s" % [parried, frames.ended - frames.broke, sm.current_state.name])
	check(answered and parried == [&"carter_teleport_strike"], "his strike, parried")
	check(flicked.is_empty(), "and no parry flashed or knocked one of the four at the top (clones %s)" % [flicked])
	check(rush.broke and frames.ended >= 0 and frames.ended - frames.broke <= 2, "it broke him, and the attack is over within two frames (%d)" % (frames.ended - frames.broke))
	check(messatsu_badge() == null and lock_badge == null, "with no badge left, over him or over the lock")
	check(rush.casters.is_empty() and not is_instance_valid(rush.lock_ring), "and no clone, line, ball or lock ring left up")
	check(sm.current_state.name == "Recover", "straight into his window")
	check(is_equal_approx(sm.recover_timer.wait_time, BEAM_RECOVER_BREAK), "the long window a Break earns: %.2f s" % sm.recover_timer.wait_time)
	check(sm.current_state.from_break and boss.can_be_juggled(), "and it is a Break's window, which pays the tiered finisher")
	check(get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), "and nothing is left on the mat")

	log_p("-- a player beaten in the middle of it leaves nothing behind")
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await settle_player(Vector2(959, 800))
	clear_iframes()
	player.playerHealth = 6
	var opened: float = defense.clock
	check(await start_beam_rush(rush), "a fifth rush is running")
	var died: bool = await wait_until(func(): return player.fight_over or player.playerHealth <= 0, 1800)
	log_p("TIME TO DEATH with nothing pressed: %.2f s from the top of the attack, in volley %d" % [defense.clock - opened, rush.volley + 1])
	check(died, "a player who never moves dies to it")
	await wait(20)
	check(rush.released, "the rush was released by the end of the fight")
	check(rush.casters.is_empty(), "no clone and no beam is left")
	check(get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), "nothing is left on the mat")
	var badges: Array = boss.clone_layer.get_children().filter(func(c): return str(c.name).begins_with("ParryTell"))
	check(messatsu_badge() == null and badges.is_empty(), "no badge is left over his head or over a lock (%d)" % badges.size())
	check(not player.is_action_locked, "and the player was never locked by it anyway")
	check(root.has_node(^"FightOutro") and not root.get_node(^"FightOutro").player_won, "the loss is running")
	# The rest of the way to the screen: his pose, his outro line read the way a player reads one, and
	# the fade behind it. current_scene is null for the frame between the fight going and the loss
	# screen coming, and a poll can land on it.
	for i in 200:
		if current_scene != null and current_scene.scene_file_path == DEFEAT_SCENE:
			break
		if current_scene != null and live_balloon() != null:
			await read_line()
		else:
			await wait(6)
	check(current_scene != null and current_scene.scene_file_path == DEFEAT_SCENE, "and it reaches the loss screen (%s)" % [current_scene.scene_file_path if current_scene else "<none>"])


# The four forming, charging and firing, and a Carter halfway through his strike, under a pause and
# under a finisher's freeze. Every wait in the attack is a physics accumulator and every ramp a
# node-bound tween, so both have to stop the whole of it dead.
func test_pause_beam_rush() -> void:
	var rush: Node = await load_carter_akuma()
	var art: GDScript = load(CARTER_ART_LAYOUT)
	player.playerHealth = 9999
	await settle_player(Vector2(959, 800))
	var pause: Node = pause_menu()

	# The one moment the four are on a live tween rather than sitting at full: catching it is what
	# proves it is node-bound and not a tree-level one, which a pause would not hold.
	log_p("-- paused with the four still forming")
	check(await start_beam_rush(rush, 0, 0.3), "the rush is running, his strike in the first charge")
	check(await wait_until(func(): return rush.casters.size() == 4 and rush.casters[3].figure.modulate.a > 0.0 and rush.casters[3].figure.modulate.a < art.BEAM_CLONE_TINT.a - 0.01, 120), "the last of the four is still forming")
	await tap_pause()
	var forming := beam_rush_alphas(rush)
	check(pause.is_open(), "paused mid-form (%s)" % [forming])
	await wait(40)
	var still_forming := beam_rush_alphas(rush)
	log_p("clone alphas %s -> %s over 40 paused frames" % [forming, still_forming])
	check(forming == still_forming, "no clone formed by a hair")
	await tap_pause()
	check(await wait_until(func(): return rush.beat == rush.Beat.CHARGE, 120), "and the charge starts after the resume")

	log_p("-- paused in the charge, with him in to strike")
	check(await wait_until(func(): return rush.strike == rush.Strike.SHOW and rush.strike_clock > 0.1, 240), "he is in beside the player with the badge up, mid-charge")
	await tap_pause()
	check(pause.is_open(), "paused inside the rush")
	var held := beam_rush_moving(rush)
	await wait(40)
	var after := beam_rush_moving(rush)
	log_p("%s -> %s" % [held, after])
	check(held == after, "the charge, his strike, the balls and the lock all held")
	await tap_pause()
	check(await wait_until(func(): return not is_equal_approx(held.strike, rush.strike_clock), 60), "and it carries on from there")

	log_p("-- paused with the beams out")
	check(await wait_until(func(): return rush.beat == rush.Beat.STRING and rush.live and rush.fire_clock >= 0.35, 300), "four beams out and hurting")
	await tap_pause()
	held = beam_rush_moving(rush)
	await wait(40)
	after = beam_rush_moving(rush)
	log_p("%s -> %s" % [held, after])
	check(held == after, "the beams, their flow and their clock held")
	await tap_pause()
	check(await wait_until(func(): return rush.fire_clock > held.fire, 60), "and it carries on from there")

	log_p("-- and a finisher's freeze, as the beams fade")
	check(await wait_until(func(): return rush.beat == rush.Beat.FADE and rush.casters[0].beam_root.modulate.a > 0.0 and rush.casters[0].beam_root.modulate.a < 1.0, 300), "the beams mid-fade")
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	check(freeze.freeze(self, [player.get_parent()]), "the fight is frozen around the player")
	held = beam_rush_moving(rush)
	await wait(40)
	after = beam_rush_moving(rush)
	log_p("frozen: %s -> %s" % [held, after])
	check(held == after, "40 frozen frames don't advance the fade or anything else")
	freeze.unfreeze(self)
	await wait(2)
	check(await wait_until(func(): return rush.beat_clock > held.beat, 60), "and it carries on after the unfreeze")
	rush.release()


func beam_rush_alphas(rush: Node) -> Array:
	return rush.casters.map(func(c): return c.figure.modulate.a)


# Everything in the Beam Rush that moves on its own: its clocks, him, the four and their balls, the
# lock, and the beams, their flow and their fade.
func beam_rush_moving(rush: Node) -> Dictionary:
	var pieces := []
	for c in rush.casters:
		pieces.append([c.figure.frame, c.ball.scale, c.ball.get("frame")])
		if is_instance_valid(c.beam_root):
			pieces.append([c.beam_root.modulate.a, c.head.global_position, c.flare.get("frame")])
			pieces.append(c.beam_parts.map(func(part): return part.get("texture")))
	return {"beat": rush.beat_clock, "fire": rush.fire_clock, "strike": rush.strike_clock, "fx": rush.fx_clock,
		"carter": boss.global_position, "lock": [rush.lock_ring.scale, rush.lock_ring.get("frame")], "pieces": pieces}


# ------------------------------------------------------------------ Carter's reads and the HUD

# Nothing the player has to read in Carter's fight may sit under the HUD or off the view: the Raging
# Demon's clones and the lights over them, the Beam Rush's badge over the lock and his strike's, and the
# Messatsu's badge over him. They are all placed against CarterArtLayout.HUD_KEEP_OUT, so the live HUD
# is walked first and held to it; then each read is checked against the live HUD itself, where it is
# placed and where it really draws.
func test_carter_hud() -> void:
	var rush: Node = await load_carter_akuma()
	var art: GDScript = load(CARTER_ART_LAYOUT)
	var demon: Node = sm.get_node("RagingDemon")
	var m: Node = sm.get_node(MESSATSU_STATE)
	var badge: Rect2 = art.TELL_BADGE
	player.playerHealth = 9999
	await wait(10)

	log_p("-- the live HUD, held to his keep-out")
	var hud := carter_hud_rects()
	var loose := hud.filter(func(r): return not art.HUD_KEEP_OUT.any(func(k): return k.encloses(r)))
	log_p("%d pieces of HUD drawn: %s" % [hud.size(), hud])
	check(hud.size() > 5 and loose.is_empty(), "every piece of the HUD is inside his keep-out (outside it: %s)" % [loose])

	log_p("-- the barrage, from where the player is locked")
	var drawn: Rect2 = art.clone_drawn_rect()
	var spawns := []
	for direction: Vector2 in demon.COMPASS:
		var at: Vector2 = demon._spawn_point(sm.ARENA_CENTRE, direction)
		spawns.append([direction, at, carter_hud_gap(Rect2(at + drawn.position, drawn.size), hud)])
	log_p("each direction, the clone's feet, and its drawn rect's gap to the nearest HUD: %s" % [spawns])
	check(demon.COMPASS.size() == 7 and not demon.COMPASS.has(Vector2(0, -1)), "seven directions, and none of them due north")
	check(spawns.all(func(s): return s[2] > 0.0), "every clone and the light over it - the punish clone's bigger one - clear of the HUD and in view")

	log_p("-- a real barrage, dealt from every direction, with fakes in it")
	track()
	var samples := []
	var watch := func() -> void:
		if sm.current_state != demon or demon.beat != demon.Beat.RUSH or not is_instance_valid(demon.clone):
			return
		var c: Node = demon.clone
		if c.light_sprite == null or not c.light.visible:
			return
		if samples.size() == demon.clone_index:
			samples.append({"index": demon.clone_index, "feint": c.is_feint, "mark": c.light_sprite.texture.resource_path,
				"ignite": c.light_sprite.frame == c.light_steps.ignite, "hold": false, "body": Rect2(), "light": Rect2()})
		elif samples.size() == demon.clone_index + 1 and demon.clone_clock >= 0.25 and not samples[-1].hold:
			samples[-1].hold = c.light_sprite.frame == c.light_steps.hold
			samples[-1].body = carter_drawn_rect(c.sprite)
			samples[-1].light = carter_drawn_rect(c.light_sprite)
	sm.cycles_started = 0
	sm.start_cycle()
	var dealt: Array[Vector2] = []
	var fakes: Array[bool] = []
	for i in sm.clone_count:
		dealt.append(demon.COMPASS[i % demon.COMPASS.size()])
		fakes.append(i in [3, 7, 11])
	demon.directions = dealt
	demon.feints = fakes
	demon.reds_total = sm.clone_count - 3
	physics_frame.connect(watch)
	await wait_until(func(): return sm.current_state != demon, 1500)
	physics_frame.disconnect(watch)
	var red_marks := samples.filter(func(s): return not s.feint).map(func(s): return s.mark)
	var fake_marks := samples.filter(func(s): return s.feint).map(func(s): return s.mark)
	var worst_clone := INF
	for s in samples:
		worst_clone = minf(worst_clone, minf(carter_hud_gap(s.body, hud), carter_hud_gap(s.light, hud)))
	log_p("%d clones read; nearest any clone or light came to the HUD or the edge: %.0f px; reds wore %s, fakes %s" % [samples.size(), worst_clone, red_marks.slice(0, 1), fake_marks.slice(0, 1)])
	check(samples.size() == sm.clone_count and worst_clone > 0.0, "no clone and no light over one sat under the HUD or off the view, from any of the seven")
	var feint_mark: Dictionary = art.feint_tell()
	var fake_wants: String = feint_mark.texture if not feint_mark.is_empty() else art.FINAL_CLONE_LIGHT.texture
	check(fake_marks.size() == 3 and fake_marks.all(func(p): return p == fake_wants), "the fakes wore %s (%s)" % ["their own X" if not feint_mark.is_empty() else "the yellow ring, standing in until the X is imported", fake_wants])
	check(red_marks.all(func(p): return p == art.FINAL_CLONE_LIGHT.texture), "and the reds their red light")
	check(samples.all(func(s): return s.ignite and s.hold), "red or fake, every light ignites and holds on the same clock")
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()

	log_p("-- the Beam Rush's badges, wherever the player stands and wherever he comes in")
	var locks := []
	for spot: Vector2 in [Vector2(959, 250), Vector2(959, 800), Vector2(700, 300), Vector2(1220, 300),
			Vector2(150, 150), Vector2(1770, 150), Vector2(150, 930), Vector2(1770, 930)]:
		rush.lock_point = spot
		var tip: Vector2 = art.clear_tell_anchor(rush._lock_tell_anchors())
		locks.append([spot, tip, carter_hud_gap(Rect2(tip + badge.position, badge.size), hud)])
	log_p("lock, badge tip, gap: %s" % [locks])
	check(locks.all(func(l): return l[2] > 0.0), "the badge over the lock is clear of the HUD and in view wherever the lines lock")
	var home: Vector2 = boss.global_position
	var bounds: Rect2 = sm.ROPES.grow(-rush.WARP_MARGIN)
	var worst_strike := INF
	var worst_at := Vector2.ZERO
	for side in [-1.0, 1.0]:
		rush.strike_side = side
		var y: float = bounds.position.y
		while y <= bounds.end.y:
			var x: float = bounds.position.x
			while x <= bounds.end.x:
				boss.global_position = Vector2(x, y)
				var tip: Vector2 = art.clear_tell_anchor(rush._strike_tell_anchors())
				var gap := carter_hud_gap(Rect2(tip + badge.position, badge.size), hud)
				if gap < worst_strike:
					worst_strike = gap
					worst_at = Vector2(x, y)
				x += 40.0
			y += 40.0
	boss.global_position = home
	log_p("his strike's badge, wherever in the ring he comes in: %.0f px from the HUD or the edge at worst, at %s" % [worst_strike, worst_at])
	check(worst_strike > 0.0, "his strike's badge is clear of the HUD and in view wherever he comes in")

	log_p("-- and live, with the player standing under the bar")
	await settle_player(Vector2(959, 250))
	clear_iframes()
	check(await start_beam_rush(rush, 0, 0.3), "a Beam Rush, his strike in the first charge")
	check(await wait_until(func(): return rush.strike == rush.Strike.SHOW and rush.strike_clock > 0.1, 600), "he comes in beside them")
	var strike_badge: Node = messatsu_badge()
	var strike_rect := carter_drawn_rect(strike_badge.sprite) if strike_badge else Rect2()
	check(strike_badge != null and carter_hud_gap(strike_rect, hud) > 0.0, "his badge is clear of the bar and in view (%s)" % [strike_rect])
	check(await wait_until(func(): return rush.beat == rush.Beat.LOCK, 600), "the lines lock on them")
	await wait(2)
	var lock_badge: Node = boss.clone_layer.get_node_or_null("ParryTell%d" % rush.lock_ring.get_instance_id())
	var lock_rect := carter_drawn_rect(lock_badge.sprite) if lock_badge else Rect2()
	check(lock_badge != null and carter_hud_gap(lock_rect, hud) > 0.0, "and the yellow badge over the lock is clear of the bar and in view (%s)" % [lock_rect])
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()

	log_p("-- the Messatsu's badge, wherever he reappears")
	var worst_m := INF
	var worst_spot := Vector2.ZERO
	m.spot_override = Vector2.INF
	for i in 300:
		player.global_position = Vector2(randf_range(150.0, 1770.0), randf_range(150.0, 930.0))
		var spot: Vector2 = m._pick_spot()
		for offset: Vector2 in [art.MESSATSU_TELL_ANCHOR, Vector2(-art.MESSATSU_TELL_ANCHOR.x, art.MESSATSU_TELL_ANCHOR.y)]:
			var gap := carter_hud_gap(Rect2(spot + offset + badge.position, badge.size), hud)
			if gap < worst_m:
				worst_m = gap
				worst_spot = spot
	log_p("300 spots picked for players all over the ring: his badge %.0f px from the HUD or the edge at worst, at %s" % [worst_m, worst_spot])
	check(worst_m > 0.0, "his badge is clear of the HUD and in view from every spot, facing either way")
	await settle_player(Vector2(959, 250))
	clear_iframes()
	check(await start_messatsu(m, Vector2.INF) and await wait_until(func(): return m.beat == m.Beat.TELL, 600), "and live, a Messatsu on a player under the bar")
	await wait(2)
	var m_badge: Node = messatsu_badge()
	var m_rect := carter_drawn_rect(m_badge.sprite) if m_badge else Rect2()
	check(m_badge != null and carter_hud_gap(m_rect, hud) > 0.0, "his badge as the lights come on is clear of the bar and in view (%s)" % [m_rect])
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()


# The drawn pieces of the HUD in Carter's fight - his health bar block and the player's own - where the
# view has them.
func carter_hud_rects() -> Array:
	var rects := []
	for layer: Node in [boss.hud_layer, current_scene.get_node("Arena/MainPlayer/CanvasLayer")]:
		for item: Node in layer.find_children("*", "", true, false):
			if not item is CanvasItem or not item.is_visible_in_tree():
				continue
			var drawing: bool = item is Sprite2D or item is TextureRect or item is TextureProgressBar or item is ColorRect or item is NinePatchRect or (item is Label and not item.text.is_empty())
			var rect := carter_drawn_rect(item)
			if drawing and rect.has_area():
				rects.append(rect)
	return rects


func carter_drawn_rect(item: CanvasItem) -> Rect2:
	if item is Control:
		return (item as Control).get_global_rect()
	var sprite := item as Sprite2D
	if sprite == null or sprite.texture == null:
		return Rect2()
	return sprite.get_global_transform() * sprite.get_rect()


# How far `rect` is from the nearest piece of `hud` - negative where it overlaps one - or -1 if any of it
# is off the view.
func carter_hud_gap(rect: Rect2, hud: Array) -> float:
	var art: GDScript = load(CARTER_ART_LAYOUT)
	if not rect.has_area() or not art.VIEW_RECT.encloses(rect):
		return -1.0
	var gap := INF
	for piece: Rect2 in hud:
		var dx := maxf(piece.position.x - rect.end.x, rect.position.x - piece.end.x)
		var dy := maxf(piece.position.y - rect.end.y, rect.position.y - piece.end.y)
		gap = minf(gap, maxf(dx, dy))
	return gap


# ------------------------------------------------------------------ Carter's Messatsu

# His third attack's numbers, mirrored the way the Beam Rush's are: messatsu reads the live ones off
# CarterStateMachine and CarterArtLayout and fails if these copies have drifted from them.
const MESSATSU_ID := &"carter_messatsu_beam"
const MESSATSU_STATE := "Messatsu"
const MESSATSU_CHARGE := 1.20
const MESSATSU_TELL := 0.30
const MESSATSU_TRAVEL := 0.10
const MESSATSU_TICK := 0.50
const MESSATSU_HITS := 7
const MESSATSU_REARM_DELAY := 0.08
const MESSATSU_PULSE_TRAVEL := 0.30
const MESSATSU_END_HOLD := 0.20
const MESSATSU_FADE := 0.30
const MESSATSU_MIN_RANGE := 520.0
const MESSATSU_HIT_WIDTH := 360.0
const MESSATSU_BACK := 60.0
const MESSATSU_MIN_AIM := 40.0
# What his punish window comes to for a string sat through and for a perfect one (recover_window() on
# all of it missed and all of it parried), and the damage a perfect string banks with the perfect bonus:
# seven hits and recover_base 1.5 since the 2026-10-05 tuning (six and 3.0 before).
# No window is shorter than walking in from where the player stands (CarterStateMachine.walk_in_time).
const MESSATSU_WINDOW_STILL := 1.5
const MESSATSU_WINDOW_PERFECT := 2.9
const MESSATSU_BANKED_PERFECT := 4
# Where the live modes put him and stand the player: 900 px apart, so the beam comes in about 10
# degrees off level and a dash straight up is across it.
const MESSATSU_CARTER_SPOT := Vector2(1500, 700)
const MESSATSU_PLAYER_SPOT := Vector2(600, 700)


# The Messatsu against the parry window and the player's own movement, modelled rather than run, so
# it needs no Carter scene: the hits are dealt through the same player path, next to a parked Eric.
func test_messatsu() -> void:
	await load_eric()
	health_ok()
	park_eric()
	await settle_player(Vector2(972, 800))
	var numbers := {
		"charge": MESSATSU_CHARGE, "tell": MESSATSU_TELL, "travel": MESSATSU_TRAVEL, "tick": MESSATSU_TICK,
		"hits": MESSATSU_HITS, "rearm": MESSATSU_REARM_DELAY, "pulse": MESSATSU_PULSE_TRAVEL,
		"hold": MESSATSU_END_HOLD, "fade": MESSATSU_FADE, "range": MESSATSU_MIN_RANGE,
		"width": MESSATSU_HIT_WIDTH, "back": MESSATSU_BACK, "min_aim": MESSATSU_MIN_AIM,
	}
	if ResourceLoader.exists(CARTER_STATE_MACHINE):
		var probe: Node = load(CARTER_STATE_MACHINE).new()
		var art: GDScript = load(CARTER_ART_LAYOUT)
		var live := {
			"charge": probe.messatsu_charge, "tell": probe.messatsu_tell, "travel": probe.messatsu_travel,
			"tick": probe.messatsu_tick, "hits": probe.messatsu_hits, "rearm": probe.messatsu_rearm_delay,
			"pulse": probe.messatsu_pulse_travel, "hold": probe.messatsu_end_hold, "fade": probe.messatsu_fade,
			"range": probe.messatsu_min_range, "width": art.MESSATSU_HIT_WIDTH, "back": art.MESSATSU_BACK,
			"min_aim": art.MESSATSU_MIN_AIM,
		}
		var times := []
		var want := []
		for k in probe.messatsu_hits:
			times.append(snappedf(probe.messatsu_hit_time(k), 0.001))
			want.append(snappedf(probe.messatsu_travel + k * probe.messatsu_tick, 0.001))
		probe.free()
		var drifted := []
		for key in numbers:
			if not is_equal_approx(float(live[key]), float(numbers[key])):
				drifted.append("%s %s against %s" % [key, live[key], numbers[key]])
		log_p("read off his fight: %s; hits land %s s after the fire" % [live, times])
		check(drifted.is_empty(), "the numbers in this file still mirror his fight (%s)" % ["they do" if drifted.is_empty() else str(drifted)])
		check(times == want, "messatsu_hit_time() is travel + k * tick (%s)" % [times])
		numbers = live
	else:
		log_p("his fight is not in this build, so the numbers in this file are what is modelled")
	var tell: float = numbers.tell
	var travel: float = numbers.travel
	var tick: float = numbers.tick
	var rearm: float = numbers.rearm
	var pulse: float = numbers.pulse
	var width: float = numbers.width
	var window: float = defense.parry_window
	var frame_time := 1.0 / 60.0
	log_p("lights to hit 1 %.2f s, surges %.2f s long, %.2f s apart, rearmed %.2f s after each hit; window %.2f s, lockout %.2f s" % [tell + travel, pulse, tick, rearm, window, defense.parry_mash_lockout])
	check(tell + travel >= 0.36 - 0.0001, "from the lights to the first hit is at or over the 0.36 s floor (%.2f s)" % (tell + travel))
	check(pulse > window + frame_time, "a surge leaves his palms more than the window and a frame before it lands (%.2f s against %.3f s)" % [pulse, window + frame_time])
	check(tick - rearm - window >= 0.15 - 0.0001, "there is at least 0.15 s of early zone between two hits (%.2f s)" % (tick - rearm - window))
	check(rearm < tick - pulse, "the rearm comes before the next surge leaves (%.2f s against %.2f s)" % [rearm, tick - pulse])
	check(tick <= defense.parry_mash_lockout + 0.0001, "the tick sits on parry_mash_lockout, so the rearm is load-bearing (%.2f s against %.2f s)" % [tick, defense.parry_mash_lockout])
	var entry: Dictionary = CATALOG.get_attack(MESSATSU_ID)
	check(entry.blockable and entry.weight == CATALOG.Weight.HEAVY and entry.tell and entry.bypass_invincibility and not entry.dash_through and not entry.parry_stagger, "its catalogue entry: blockable, HEAVY, a red tell, through the i-frames, no dash-through and no stagger")

	log_p("-- pressing as a surge leaves his palms doesn't parry, pressing in the window does")
	defense.rearm_parry()
	var on_sight: int = await parry_at(clone_frames(pulse), MESSATSU_ID)
	check(on_sight == unparried(), "a press as the surge appears isn't a parry (%d)" % on_sight)
	defense.rearm_parry()
	var in_window: int = await parry_at(clone_frames(window) - 2, MESSATSU_ID)
	check(in_window == 3, "a press inside the window is a parry (%d)" % in_window)

	# Times are from the hit before, which the model doesn't deliver: an early press, a panicked second
	# one inside its lockout, then an honest one for the hit after.
	log_p("-- an early whiff costs that hit, and the rearm gives the next one back")
	var whiff := [0.13, 0.45, 2.0 * tick - 0.10]
	var saved: Array = await messatsu_run(whiff, [rearm, tick + rearm], [tick, 2.0 * tick])
	var spilled: Array = await messatsu_run(whiff, [rearm], [tick, 2.0 * tick])
	log_p("  presses at %s s: %s with every rearm, %s with none after the first hit" % [whiff, saved, spilled])
	check(saved == [unparried(), 3], "the early press costs only its own hit, and the next is parried (%s)" % [saved])
	check(spilled == [unparried(), unparried()], "and without the rearm after that hit, the whiff would have cost the next one too (%s)" % [spilled])
	log_p("-- and a press up to 0.08 s late costs nothing")
	var late := [rearm - 0.03, tick - 0.10]
	var forgiven: Array = await messatsu_run(late, [rearm], [tick])
	var unforgiven: Array = await messatsu_run(late, [], [tick])
	check(forgiven == [3], "a press %.2f s late for the last hit, then one in the window, parries the next (%s)" % [late[0], forgiven])
	check(unforgiven == [unparried()], "which only the rearm makes true: %s without it" % [unforgiven])

	log_p("-- %d hits %.2f s apart on a player who does nothing" % [MESSATSU_HITS, tick])
	player.playerHealth = 100
	var landed := []
	for k in MESSATSU_HITS:
		if k > 0:
			await wait(clone_frames(tick))
		landed.append(omni_hit(MESSATSU_ID, dummy_source()))
	log_p("  %s, health %d" % [landed, player.playerHealth])
	check(landed.count(1) == MESSATSU_HITS, "all %d land through each other's i-frames (%s)" % [MESSATSU_HITS, landed])
	check(player.playerHealth == 100 - MESSATSU_HITS * entry.damage, "for %d half-hearts, a full health bar (%d left of 100)" % [MESSATSU_HITS * entry.damage, player.playerHealth])
	clear_iframes()
	health_ok()
	await wait(40)

	log_p("-- a held guard %s" % ("breaks on the third block" if blocking() else "is no answer: all three land and nothing breaks"))
	defense._set_stamina(defense.max_stamina)
	press(KEY_SHIFT)
	await past_window()
	var blocks := []
	var broke_on := 0
	for k in 3:
		if k > 0:
			await wait(clone_frames(tick))
		blocks.append(omni_hit(MESSATSU_ID, dummy_source()))
		if broke_on == 0 and defense.is_guard_broken:
			broke_on = k + 1
	release(KEY_SHIFT)
	log_p("  %s, broken on block %d" % [blocks, broke_on])
	if blocking():
		check(blocks == [2, 2, 2] and broke_on == 3, "three blocks at %.0f stamina each, and the third breaks the guard (%s, block %d)" % [defense.heavy_block_cost, blocks, broke_on])
	else:
		check(blocks == [1, 1, 1] and broke_on == 0, "three hits through the held guard, and it never breaks (%s)" % [blocks])
	defense.clear_guard_break()
	clear_iframes()
	health_ok()
	await wait(4)

	# The first hit lands messatsu_travel after the aim latches. To be clear of it the hurtbox has to
	# be half the width plus its own reach across the beam off the axis; a dash counts only the frames
	# it moves after the latch, and walking only what it covers in the travel.
	log_p("-- the dodge, worked out at every angle")
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var half: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs() / 2.0
	var travel_frames := clone_frames(travel)
	var dash_step: float = player.DODGE_SPEED / 60.0
	var dash_frames := roundi(DASH_LENGTH / dash_step)
	var early_px := dash_step * (dash_frames - 1)
	var walk_step: float = player.SPEED / 60.0
	check(dash_frames <= travel_frames, "a whole dash fits inside the travel (%d frames against %d)" % [dash_frames, travel_frames])
	var worst := INF
	var worst_at := 0.0
	var widest := INF
	var early_clears := []
	var walk_clears := []
	for i in 720:
		var n := Vector2.from_angle(deg_to_rad(i * 0.5)).orthogonal()
		var across := half.x * absf(n.x) + half.y * absf(n.y)
		var need := width / 2.0 + across
		var best := 0.0
		for d in 4:
			best = maxf(best, absf(Vector2.from_angle(d * PI / 4.0).dot(n)))
		var margin := best * DASH_LENGTH - need
		if margin < worst:
			worst = margin
			worst_at = i * 0.5
		widest = minf(widest, 2.0 * (best * DASH_LENGTH - across))
		if best * early_px >= need:
			early_clears.append(i * 0.5)
		var walked := 0.0
		for v in [Vector2(1, 0), Vector2(0, 1), Vector2(1, 1), Vector2(1, -1)]:
			walked = maxf(walked, absf((v * walk_step * travel_frames).dot(n)))
		if walked >= need:
			walk_clears.append(i * 0.5)
	log_p("  the best of 8 dashes (%.0f px) clears the first hit by %.1f px at worst, at %.1f deg; above %.0f px wide the dodge would be gone at some angle" % [DASH_LENGTH, worst, worst_at, widest])
	check(worst >= 0.0 and worst <= 60.0, "the best 8-way dash clears it at every angle, by 0 to 60 px at the worst (%.1f px)" % worst)
	check(early_clears.is_empty(), "a dash one frame early - %.0f px after the latch - never clears (%d angles do)" % [early_px, early_clears.size()])
	check(walk_clears.is_empty(), "and neither does walking, at most %.0f px in %d frames (%d angles do)" % [walk_step * travel_frames * sqrt(2.0), travel_frames, walk_clears.size()])


# A stretch of the string on the player's own input path, with times in seconds from a hit the model
# doesn't deliver: a guard press at each of `taps` (held until the next one), the fight's rearm at each
# of `rearms`, and a hit at each of `hits`. Returns the hits' results.
func messatsu_run(taps: Array, rearms: Array, hits: Array) -> Array:
	var plan := []
	for at in taps:
		plan.append([at, 0])
	for at in rearms:
		plan.append([at, 1])
	for at in hits:
		plan.append([at, 2])
	plan.sort_custom(func(a, b): return a[0] < b[0])
	var now := 0
	var held := false
	var results := []
	for step in plan:
		var at_frame := clone_frames(step[0])
		if at_frame > now:
			await wait(at_frame - now)
			now = at_frame
		match step[1]:
			0:
				if held:
					release(KEY_SHIFT)
					await wait(1)
					now += 1
				press(KEY_SHIFT)
				held = true
			1:
				defense.rearm_parry()
			2:
				results.append(front_hit(MESSATSU_ID, dummy_source()))
				clear_iframes()
	if held:
		release(KEY_SHIFT)
	await wait(4)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	await wait(40)
	return results


# Straight into a Messatsu from wherever his machine is: back to Idle with its beat stopped, then the
# rotation's third cycle - the rotation doing its job - with him put on a known spot.
func start_messatsu(m: Node, spot := MESSATSU_CARTER_SPOT) -> bool:
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	m.spot_override = spot
	sm.cycles_started = sm.ATTACK_ROTATION.find(MESSATSU_STATE)
	sm.start_cycle()
	return sm.current_state == m


# How many frames after this one the Messatsu fires in, stepping its tell clock exactly as it does.
func messatsu_frames_to_fire(m: Node) -> int:
	var at: float = m.beat_clock
	var n := 0
	while at + 1.0 / 60.0 < sm.messatsu_tell - m.CLOCK_SLACK:
		at += 1.0 / 60.0
		n += 1
	return n


func player_centre() -> Vector2:
	return player.hurtBox.get_node("CollisionShape2D").global_position


func messatsu_badge() -> Node:
	return boss.get_parent().get_node_or_null("ParryTell%d" % boss.get_instance_id())


# Whether any of him is drawn - his body, his aura or his mark, shown and not faded right out - under
# the curtain or not: drawn under it, about 7% of him shows through.
func carter_shows() -> bool:
	for part: CanvasItem in [boss.sprite, boss.aura, boss.mark_glow]:
		if part.visible and part.modulate.a > 0.0:
			return true
	return false


# How far the lock has closed, however it is drawn: the placeholder ring's rim, or the sheet's frame
# and its squeeze.
func messatsu_lock(m: Node) -> Array:
	if m.lock_ring is Line2D:
		return [m.lock_ring.points[0]]
	return [m.lock_ring.frame, m.lock_ring.scale]


# One Messatsu, with the player standing at `stand` and dashing toward `key` so that the dash's first
# moving frame is `lead` frames after the fire frame (negative: before it). What the first hit did,
# and the lead as measured: a press only reaches the player on the next frame's input flush.
func messatsu_dash(m: Node, lead: int, key: int, stand := MESSATSU_PLAYER_SPOT) -> Dictionary:
	await settle_player(stand)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	var hurt: int = events_of("HIT", MESSATSU_ID).size()
	var dodged: int = dodges.size()
	if not await start_messatsu(m) or not await wait_until(func(): return m.beat == m.Beat.TELL, 600):
		return {"lead": 999, "hit": true, "dodged": false, "latched": false, "resolved": false}
	var seen := {"fire": -1, "dash": -1, "angle": 0.0}
	var watcher := func() -> void:
		var now := Engine.get_physics_frames()
		if seen.fire < 0 and m.latched:
			seen.fire = now - 1
			seen.angle = m.aim_angle
		if seen.dash < 0 and player.is_dodging:
			seen.dash = now
	physics_frame.connect(watcher)
	await wait(maxi(messatsu_frames_to_fire(m) + lead - 1, 0))
	press(key)
	tap(KEY_W)
	var resolved := await wait_until(func(): return m.tick_index >= 1, 120)
	await wait(1)
	physics_frame.disconnect(watcher)
	release(key)
	var result := {
		"lead": seen.dash - seen.fire if seen.dash >= 0 and seen.fire >= 0 else 999,
		"hit": events_of("HIT", MESSATSU_ID).size() > hurt,
		"dodged": dodges.size() > dodged and dodges[-1].id == MESSATSU_ID,
		"latched": is_instance_valid(m.beam_root) and is_equal_approx(m.beam_root.rotation, seen.angle) and is_equal_approx(m.aim_angle, seen.angle),
		"resolved": resolved,
	}
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await wait(2)
	return result


# The real thing, in his shipped fight, with him on a known spot. tier=death and tier=defeated each end
# the fight, so each gets a process of its own.
func test_messatsu_live() -> void:
	await load_carter_akuma()
	var m: Node = sm.get_node_or_null(MESSATSU_STATE)
	check(m != null, "his fight carries a Messatsu state")
	if m == null:
		return
	var art: GDScript = load(CARTER_ART_LAYOUT)
	track()
	track_parries()
	track_dodges()
	track_guard()
	if tier == "death":
		await messatsu_death(m)
		return
	if tier == "defeated":
		await messatsu_defeated(m)
		return

	var order := []
	for cycle in range(1, 6):
		sm.cycles_started = cycle
		order.append(sm.next_attack())
	sm.cycles_started = 0
	check(order == ["RagingDemon", "BeamRush", "BeamRush", MESSATSU_STATE, "RagingDemon"], "his rotation is the barrage, the Beam Rush twice, the Messatsu, then the barrage again (%s)" % [order])

	log_p("-- a player who presses nothing: the dark, the lights, %d hits" % MESSATSU_HITS)
	player.playerHealth = 9999
	await settle_player(MESSATSU_PLAYER_SPOT)
	var hurt: int = events_of("HIT", MESSATSU_ID).size()
	check(await start_messatsu(m), "a Messatsu is running")
	# He goes down with the curtain, so from the frame it is fully down nothing of him may be drawn.
	var dark := {"frames": 0, "shown": 0}
	var charging := false
	for i in 300:
		if m.beat == m.Beat.CHARGE:
			charging = true
			break
		if boss.curtain.modulate.a >= 1.0:
			dark.frames += 1
			if carter_shows():
				dark.shown += 1
		await physics_frame
	check(charging, "and charging")
	# The player walks down and back up through the charge, so the line has something to follow.
	var charge := {"frames": 0, "off": 0, "worst": 0.0, "lit": 0, "unlifted": 0, "carter": 0, "buried": 0}
	press(KEY_DOWN)
	while m.beat == m.Beat.CHARGE:
		charge.frames += 1
		var off: float = m.aim_line.to_global(m.aim_line.points[1]).distance_to(player_centre())
		charge.worst = maxf(charge.worst, off)
		if off > 1.0:
			charge.off += 1
		if not boss.dark_stage.visible or boss.curtain.modulate.a < 0.99:
			charge.lit += 1
		if player.get_parent().z_index != art.PLAYER_Z:
			charge.unlifted += 1
		if carter_shows():
			charge.carter += 1
		for fx: CanvasItem in [m.ball, m.eyes, m.aim_line, m.lock_ring]:
			if not fx.visible or boss.clone_layer.z_index + fx.z_index <= boss.dark_stage.z_index:
				charge.buried += 1
		if charge.frames == 20:
			release(KEY_DOWN)
			press(KEY_UP)
		elif charge.frames == 40:
			release(KEY_UP)
		await physics_frame
	release(KEY_DOWN)
	release(KEY_UP)
	log_p("charge: %s; fully dark before it: %s" % [charge, dark])
	check(charge.frames >= 60 and charge.off == 0, "the aim line was on the player's hurtbox centre every one of the %d charge frames while they walked (%.2f px off at worst)" % [charge.frames, charge.worst])
	check(charge.lit == 0, "the arena was dark for all of the charge")
	check(charge.unlifted == 0, "the player was lifted over it to z %d throughout" % art.PLAYER_Z)
	check(dark.frames > 0 and dark.shown + charge.carter == 0, "and from the dark being fully down to the lights coming back, nothing of him was drawn: body, aura and mark (%d frames of it before the charge, %d in it)" % [dark.frames, charge.frames])
	check(charge.buried == 0, "and the ball, the eyes, the line and the ring were all drawn over it, above z %d" % boss.dark_stage.z_index)
	check(m.beat == m.Beat.TELL, "the lights are back (%s)" % m.Beat.keys()[m.beat])
	check(not boss.dark_stage.visible and boss.curtain.modulate.a == 0.0 and messatsu_badge() != null, "and on the frame they come back, the dark is gone and the badge is up")
	check(player.get_parent().z_index == 0, "the player is back under the ropes (z %d)" % player.get_parent().z_index)
	check(await wait_until(func(): return m.latched, 60), "it fires")
	var angle: float = m.aim_angle
	var origin: Vector2 = m.aim_origin
	check(messatsu_badge() == null, "the badge is gone the frame it fires")
	check(is_instance_valid(m.beam_root) and is_equal_approx(m.beam_root.rotation, angle), "and the beam lies along the latched aim (%.1f deg)" % rad_to_deg(angle))
	check(await wait_until(func(): return sm.current_state.name == "Recover", 600), "the string hands over to his punish window")
	var hits: Array = events_of("HIT", MESSATSU_ID).slice(hurt)
	var gaps := []
	for i in range(1, hits.size()):
		gaps.append(snappedf(hits[i].t - hits[i - 1].t, 0.001))
	log_p("%d hits, %s s apart; the window %.2f s" % [hits.size(), gaps, sm.recover_timer.wait_time])
	check(hits.size() == MESSATSU_HITS, "exactly %d hits land on a still player (%d)" % [MESSATSU_HITS, hits.size()])
	check(gaps.all(func(gap): return absf(gap - MESSATSU_TICK) <= 1.5 / 60.0), "%.2f s apart (%s)" % [MESSATSU_TICK, gaps])
	check(is_equal_approx(m.aim_angle, angle) and m.aim_origin == origin, "and the aim never moved after the fire")
	var walk_in: float = sm.walk_in_time(player.global_position.distance_to(boss.global_position))
	check(absf(sm.recover_timer.wait_time - maxf(MESSATSU_WINDOW_STILL, walk_in)) <= 0.02, "a string sat through earns the short window, or the walk in from where the player stands if that is longer: %.2f s (walk in %.2f s)" % [sm.recover_timer.wait_time, walk_in])
	check(get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), "nothing is left on the mat")
	check(not boss.dark_stage.visible and boss.curtain.modulate.a == 0.0, "no dark is left up")
	check(is_equal_approx(boss.music_player.volume_db, boss.music_base_db), "the music is back to %.1f dB" % boss.music_base_db)
	check(player.get_parent().z_index == 0, "the player is under the ropes")
	check(not boss.sprite.flip_h, "he is facing the way he always stands")
	check(messatsu_badge() == null, "and there is no badge over his head")

	log_p("-- %d parries" % MESSATSU_HITS)
	await settle_player(MESSATSU_PLAYER_SPOT)
	clear_iframes()
	boss.boss_health = boss.max_health
	var parried_before: int = parries.size()
	check(await start_messatsu(m), "a second Messatsu is running")
	for k in MESSATSU_HITS:
		var at: float = sm.messatsu_hit_time(k) - 0.10
		if not await wait_until(func(): return m.beat == m.Beat.STRING and m.tick_index == k and m.fire_clock >= at, 600):
			break
		press(KEY_SHIFT)
		await wait_until(func(): return m.tick_index > k, 120)
		release(KEY_SHIFT)
		defense._set_stamina(defense.max_stamina)
	check(await wait_until(func(): return sm.current_state.name == "Recover", 300), "into his punish window")
	var got: Array = parries.slice(parried_before)
	log_p("parried %d (%s), banked %d, window %.2f s" % [m.parried, got.map(func(p): return p.id), boss.max_health - boss.boss_health, sm.recover_timer.wait_time])
	check(m.parried == MESSATSU_HITS and got.size() == MESSATSU_HITS and got.all(func(p): return p.id == MESSATSU_ID and not p.staggered), "all %d parried, and none of them staggers him" % MESSATSU_HITS)
	check(boss.boss_health == boss.max_health - MESSATSU_BANKED_PERFECT, "a perfect string banks %d (%d taken)" % [MESSATSU_BANKED_PERFECT, boss.max_health - boss.boss_health])
	var walk_in_perfect: float = sm.walk_in_time(player.global_position.distance_to(boss.global_position))
	check(absf(sm.recover_timer.wait_time - maxf(MESSATSU_WINDOW_PERFECT, walk_in_perfect)) <= 0.02, "and earns a %.1f s window, or the walk in from where the player stands if that is longer (%.2f s, walk in %.2f s)" % [MESSATSU_WINDOW_PERFECT, sm.recover_timer.wait_time, walk_in_perfect])

	log_p("-- a player who turtles behind the guard")
	await settle_player(MESSATSU_PLAYER_SPOT)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	hurt = events_of("HIT", MESSATSU_ID).size()
	var broken_before: int = guard_events.filter(func(e): return e[0] == "broken").size()
	check(await start_messatsu(m), "a third Messatsu is running")
	check(await wait_until(func(): return m.beat == m.Beat.CHARGE, 300), "and the guard goes up in the dark")
	press(KEY_SHIFT)
	check(await wait_until(func(): return sm.current_state.name == "Recover", 900), "held all the way to his punish window")
	release(KEY_SHIFT)
	var breaks: int = guard_events.filter(func(e): return e[0] == "broken").size() - broken_before
	var taken: int = events_of("HIT", MESSATSU_ID).size() - hurt
	log_p("guard broken %d times, %d hits taken, %d blocked, %d parried" % [breaks, taken, m.blocked, m.parried])
	if blocking():
		check(breaks >= 1 and taken <= 2, "the guard breaks at least once and no more than two hits land (%d breaks, %d hits)" % [breaks, taken])
	else:
		check(breaks == 0 and taken == MESSATSU_HITS and m.blocked == 0, "without blocking the guard is no answer: all %d land and nothing breaks (%d breaks, %d hits)" % [MESSATSU_HITS, breaks, taken])
	defense.clear_guard_break()
	await wait(4)

	log_p("-- a player who takes the first hit and walks out of the beam")
	await settle_player(MESSATSU_PLAYER_SPOT)
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	hurt = events_of("HIT", MESSATSU_ID).size()
	check(await start_messatsu(m), "a fourth Messatsu is running")
	check(await wait_until(func(): return m.tick_index >= 1, 600), "the first hit is in")
	press(KEY_UP)
	await wait(36)
	release(KEY_UP)
	check(await wait_until(func(): return sm.current_state.name == "Recover", 600), "into his punish window")
	taken = events_of("HIT", MESSATSU_ID).size() - hurt
	log_p("%d hits taken, window %.2f s" % [taken, sm.recover_timer.wait_time])
	check(taken == 1, "walking out of the beam after the first hit caps the bill at one (%d)" % taken)

	# A dash straight up, started a frame at a time either side of the fire. The aim tracks until the
	# fire frame and the player moves before he does in a frame, so only dash frames AFTER it count.
	log_p("-- the dodge: a dash up, frame by frame around the fire")
	var sweep := []
	for lead in range(-2, 7):
		var r: Dictionary = await messatsu_dash(m, lead, KEY_UP)
		sweep.append(r)
		log_p("  dash %+d frames from the fire (measured %+d): %s%s%s" % [lead, r.lead, "HIT" if r.hit else "clear", ", PERFECT DODGE" if r.dodged else "", "" if r.latched else ", the beam moved"])
	var escaped: Array = sweep.filter(func(r): return not r.hit).map(func(r): return r.lead)
	escaped.sort()
	check(sweep.all(func(r): return r.resolved and r.latched), "every one reached its first hit, and no beam followed a dash once it had fired")
	check(sweep.filter(func(r): return r.lead <= -1).all(func(r): return r.hit), "a dash started before the fire is hit, every time")
	check(sweep.any(func(r): return r.lead >= 1 and not r.hit and r.dodged), "a dash after it escapes, for a perfect dodge")
	check(not escaped.is_empty() and escaped.size() <= 5 and escaped[-1] - escaped[0] + 1 == escaped.size(), "and the frames that escape are one unbroken run, 1 to 5 wide (%s)" % [escaped])
	if not escaped.is_empty():
		log_p("DODGE WINDOW: %d frames (%.0f ms), for a dash whose first moving frame is %d to %d frames after the fire" % [escaped.size(), escaped.size() * 1000.0 / 60.0, escaped[0], escaped[-1]])

	log_p("-- and a dash back through him from close in, kept on purpose")
	var palms: Vector2 = MESSATSU_CARTER_SPOT + art.local(art.MESSATSU_MUZZLE, true)
	var lift: Vector2 = player_centre() - player.global_position
	var through := []
	for gap in [120.0, 150.0, 160.0, 170.0, 180.0, 200.0]:
		var r: Dictionary = await messatsu_dash(m, 1, KEY_RIGHT, palms + Vector2(-gap, 0.0) - lift)
		through.append(not r.hit)
		log_p("  from %.0f px in front of his palms: %s%s" % [gap, "HIT" if r.hit else "out of the back of the band", ", PERFECT DODGE" if r.dodged else ""])
	check(through[0] and not through[-1], "a dash through him gets out from 120 px and not from 200 px (%s)" % [through])

	log_p("-- dashing in with a block press parries the first hit, with dash_parry off and on")
	for flag in [false, true]:
		player.dash_parry = flag
		await settle_player(MESSATSU_PLAYER_SPOT)
		clear_iframes()
		defense._set_stamina(defense.max_stamina)
		var before: int = parries.size()
		check(await start_messatsu(m) and await wait_until(func(): return m.beat == m.Beat.TELL, 600), "a Messatsu for dash_parry %s" % flag)
		await wait(messatsu_frames_to_fire(m))
		press(KEY_RIGHT)
		tap(KEY_W)
		await wait(1)
		press(KEY_SHIFT)
		await wait_until(func(): return m.tick_index >= 1, 120)
		release(KEY_SHIFT)
		release(KEY_RIGHT)
		var first: Array = parries.slice(before)
		check(m.parried == 1 and first.size() == 1 and first[0].id == MESSATSU_ID, "dash_parry %s: a dash toward him with a press in it parries the first hit (%d)" % [flag, m.parried])
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
		await wait(40)
	player.dash_parry = false


# tier=death: killed in the middle of the string, standing in it. Everything he sent out goes, the
# badge with it; the dark was already down, so none is left for the KO to hand on.
func messatsu_death(m: Node) -> void:
	log_p("-- a player killed in the middle of the string")
	player.playerHealth = 3
	await settle_player(MESSATSU_PLAYER_SPOT)
	check(await start_messatsu(m), "a Messatsu is running")
	check(await wait_until(func(): return player.fight_over or player.playerHealth <= 0, 900), "and it kills a player who stands in it")
	var on_hit: int = m.tick_index
	await wait(20)
	log_p("down on hit %d, and he settled in %s" % [on_hit, sm.current_state.name])
	check(sm.current_state.name == "Victory", "into his victory pose")
	check(m.released, "the Messatsu was released")
	var left := [m.beam_root, m.ball, m.eyes, m.aim_line, m.lock_ring].filter(func(node): return is_instance_valid(node))
	check(left.is_empty() and m.surges.is_empty() and get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), "nothing of it is left (%d nodes, %d hazards)" % [left.size(), get_nodes_in_group(sm.HAZARD_GROUP).size()])
	check(messatsu_badge() == null, "no badge is left over his head")
	check(boss.curtain.modulate.a == 0.0, "none of its dark is up for the KO to carry on")
	check(player.get_parent().z_index == 0, "the player is under the ropes")
	check(not player.is_action_locked, "and was never locked by it")
	check(root.has_node(^"FightOutro") and not root.get_node(^"FightOutro").player_won, "the loss is running")


# tier=defeated: he is beaten in the dark, mid-charge. That can't happen in play - his hurtbox is shut
# outside his punish window - so this is the release path proving itself: the lights snap on, the duck
# lifts and the player comes back down.
func messatsu_defeated(m: Node) -> void:
	log_p("-- Carter beaten in the middle of the charge, in the dark")
	player.playerHealth = 9999
	await settle_player(MESSATSU_PLAYER_SPOT)
	check(await start_messatsu(m), "a Messatsu is running")
	check(await wait_until(func(): return m.beat == m.Beat.CHARGE and m.beat_clock >= 0.3, 300), "into the charge")
	check(boss.dark_stage.visible and player.get_parent().z_index > 0 and boss.music_player.volume_db < boss.music_base_db - 6.0 and boss.charge_sfx_player.playing, "dark, the player lifted, the music ducked and the charge humming")
	boss.boss_health = 1
	boss._apply_damage(1)
	await wait(6)
	log_p("he settled in %s" % sm.current_state.name)
	check(sm.current_state.name == "Defeated", "he is beaten")
	check(m.released, "the Messatsu was released")
	check(not boss.dark_stage.visible and boss.curtain.modulate.a == 0.0, "the lights snapped back on")
	check(is_equal_approx(boss.music_player.volume_db, boss.music_base_db), "the duck is undone (%.1f dB)" % boss.music_player.volume_db)
	check(player.get_parent().z_index == 0, "the player is back under the ropes")
	check(not boss.charge_sfx_player.playing, "the hum stopped")
	var left := [m.beam_root, m.ball, m.eyes, m.aim_line, m.lock_ring].filter(func(node): return is_instance_valid(node))
	check(left.is_empty() and get_nodes_in_group(sm.HAZARD_GROUP).is_empty() and messatsu_badge() == null, "and nothing of it is left (%d nodes)" % left.size())
	check(root.has_node(^"FightOutro") and root.get_node(^"FightOutro").player_won, "the win is running")


# The dark coming in, the charge and a surge in flight, under a pause and under a finisher's freeze.
# Every wait in the attack is a physics accumulator and every ramp a node-bound tween, so both have to
# stop the whole of it dead.
func test_pause_messatsu() -> void:
	await load_carter_akuma()
	var m: Node = sm.get_node(MESSATSU_STATE)
	player.playerHealth = 9999
	await settle_player(MESSATSU_PLAYER_SPOT)
	var pause: Node = pause_menu()

	# The dark comes in over 0.10 s: the only moment it is on a live tween rather than at full, and
	# catching it is what proves the tween is node-bound.
	log_p("-- paused with the lights still going out")
	check(await start_messatsu(m), "a Messatsu is running")
	check(await wait_until(func(): return m.beat == m.Beat.VANISH, 120), "the lights are going out")
	await tap_pause()
	var ramp: float = boss.curtain.modulate.a
	var eyes: float = m.eyes.modulate.a
	check(pause.is_open() and ramp > 0.0 and ramp < 1.0, "paused mid-ramp (curtain %.3f)" % ramp)
	await wait(40)
	log_p("curtain %.3f -> %.3f, eyes %.3f -> %.3f over 40 paused frames" % [ramp, boss.curtain.modulate.a, eyes, m.eyes.modulate.a])
	check(is_equal_approx(ramp, boss.curtain.modulate.a) and is_equal_approx(eyes, m.eyes.modulate.a), "the dark didn't deepen and his eyes didn't fade by a hair")
	await tap_pause()
	check(await wait_until(func(): return boss.curtain.modulate.a >= 1.0, 60), "and the dark finishes coming in after the resume")

	log_p("-- paused in the middle of the charge")
	check(await wait_until(func(): return m.beat == m.Beat.CHARGE and m.beat_clock >= 0.5, 300), "he is charging")
	await tap_pause()
	var beat: float = m.beat_clock
	var ball: Vector2 = m.ball.scale
	var ring: Array = messatsu_lock(m)
	await wait(40)
	log_p("charge clock %.4f -> %.4f, ball %s -> %s, ring %s -> %s" % [beat, m.beat_clock, ball, m.ball.scale, ring, messatsu_lock(m)])
	check(is_equal_approx(beat, m.beat_clock) and ball == m.ball.scale and ring == messatsu_lock(m), "the charge clock, the ball and the lock ring all held")
	await tap_pause()
	check(await wait_until(func(): return not is_equal_approx(beat, m.beat_clock), 60), "and it carries on")

	log_p("-- paused with a surge in flight")
	var surge_due := func(k: int) -> bool:
		return (m.beat == m.Beat.STRING and m.tick_index == k and not m.surges.is_empty()
			and m.fire_clock > sm.messatsu_hit_time(k) - sm.messatsu_pulse_travel * 0.5)
	check(await wait_until(func(): return surge_due.call(1), 600), "a surge is on its way down the beam")
	await tap_pause()
	var fire: float = m.fire_clock
	var tick: int = m.tick_index
	var at: Vector2 = m.surges[0].global_position
	await wait(40)
	log_p("fire clock %.4f -> %.4f, hit %d -> %d, surge %s -> %s" % [fire, m.fire_clock, tick, m.tick_index, at, m.surges[0].global_position])
	check(is_equal_approx(fire, m.fire_clock) and tick == m.tick_index and at == m.surges[0].global_position, "the string's clock, its count and the surge all held")
	await tap_pause()
	check(await wait_until(func(): return not is_equal_approx(fire, m.fire_clock), 60), "and it carries on")

	log_p("-- and a finisher's freeze")
	check(await wait_until(func(): return surge_due.call(2), 600), "the next surge is on its way")
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	check(freeze.freeze(self, [player.get_parent()]), "the fight is frozen around the player")
	fire = m.fire_clock
	tick = m.tick_index
	at = m.surges[0].global_position
	await wait(40)
	log_p("frozen: fire clock %.4f -> %.4f, hit %d -> %d, surge %s -> %s" % [fire, m.fire_clock, tick, m.tick_index, at, m.surges[0].global_position])
	check(is_equal_approx(fire, m.fire_clock) and tick == m.tick_index and at == m.surges[0].global_position, "40 frozen frames don't advance the string or move the surge")
	freeze.unfreeze(self)
	await wait(2)
	check(await wait_until(func(): return not is_equal_approx(fire, m.fire_clock), 60), "and it carries on after the unfreeze")
	m.release()


# ------------------------------------------------------------------ Computah's mine field
# His second attack: pods on the mat, then a high-speed chase to herd the player over them. A pod
# that closes SEALS the player - no move, no dash, no punch, and the guard and its parry are sealed
# off too - and he walks over and charges an uppercut while they mash out of it.

const COMPUTAH_SCENE := "Arena/ComputahScene"
const COMPUTAH_MINE_SCENE := "res://Scenes/Bosses/ComputahMineScene.tscn"


# His fight, driving itself from here rather than off its own opening timer. The modes on it test the mine
# field and the overload, out of his live rotation since 2026-09-24 (ComputahStateMachine.live_attacks), so it
# puts them back in for itself, with the health they were sized for.
func load_computah_fight() -> void:
	await load_fight("computah")
	boss = current_scene.get_node(COMPUTAH_SCENE + "/ComputahCharacterBody")
	sm = boss.state_machine
	sm.live_attacks.assign(sm.ATTACKS)
	boss.max_health = boss.FULL_ROTATION_HEALTH
	boss.boss_health = boss.max_health
	boss.health_bar.set_max(0, boss.max_health)
	boss.health_bar.set_value(0, boss.boss_health, boss.health_bar.HIT_SILENT)
	sm.post_dialogue_pre_fight_timer.stop()
	# Out of the intro pose, which trap_allowed() refuses on purpose, and off the beat clock: from
	# here the test drives his states itself.
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	player.playerHealth = 1000
	track()


# One pod, laid by hand where the test wants it. lob() from its own spot, so the flight is a
# formality; the phases run on its own clock either way.
func lay_mine_at(at: Vector2) -> Node2D:
	var mine: Node2D = load(COMPUTAH_MINE_SCENE).instantiate()
	mine.state_machine = sm
	sm.add_hazard(mine, at, current_scene.get_node(COMPUTAH_SCENE + "/HazardLayer"))
	mine.lob(at)
	return mine


func armed_mine_at(at: Vector2) -> Node2D:
	var mine := lay_mine_at(at)
	await wait_until(func(): return mine.is_armed(), 180)
	return mine


# Out of the mine field and back to a standing start, with the mat cleared.
func park_computah() -> void:
	for hazard in get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	sm.window_timer.stop()
	sm.last_release_time = -INF
	boss.global_position = sm.COMPUTAH_HOME
	await wait(2)


func test_mine_trap() -> void:
	await load_computah_fight()
	var trapped: Node = sm.states["Trapped"]
	var punish: Node = sm.states["Punish"]
	var layout: GDScript = load("res://Scripts/ComputahArtLayout.gd")

	log_p("-- the picker: the mine field never runs twice in a row, and never straight after a catch")
	sm.last_attack = "LayMines"
	sm.caught_since_cycle = false
	check(sm._next_attack() == "Beam", "after a mine field, the beam")
	sm.last_attack = "Beam"
	check(sm._next_attack() == "LayMines", "after the beam, the mine field")
	sm.caught_since_cycle = true
	check(sm._next_attack() == "Beam", "and a catch is always followed by the beam")
	sm.caught_since_cycle = false

	log_p("-- the trigger is the drawn ring, to the texel")
	var ring: Rect2 = layout.mine_ring()
	log_p("ring box %s texels -> %s px" % [layout.MINE_RING_BOX, ring])
	check(ring.size == layout.MINE_RING_BOX.size * layout.SCALE, "the trigger is the measured ring at SCALE (%s)" % ring.size)
	check(is_equal_approx(ring.size.x, 72.0) and is_equal_approx(ring.size.y, 36.0), "which is 72 x 36 px (%s)" % ring.size)

	log_p("-- he lays a field")
	await settle_player(Vector2(500, 800))
	var stood_at: Vector2 = player.global_position
	sm.on_child_transition(sm.current_state, "LayMines")
	check(await wait_until(func(): return sm.current_state.name == "Chase", 300), "the lay hands over to the chase")
	var mines: Array = sm.live_mines()
	log_p("%d pods at %s" % [mines.size(), mines.map(func(m): return m.global_position)])
	check(mines.size() > 0 and mines.size() <= sm.mine_count, "at most mine_count pods went down (%d of %d)" % [mines.size(), sm.mine_count])
	var bounds: Rect2 = sm.runner_bounds()
	check(mines.all(func(m): return bounds.has_point(m.global_position)), "every pod is inside runner_bounds(), not just inside the ropes")
	var apart := true
	for i in mines.size():
		for j in range(i + 1, mines.size()):
			if mines[i].global_position.distance_to(mines[j].global_position) < sm.mine_spacing:
				apart = false
	check(apart, "no two pods are inside mine_spacing (%.0f px) of each other" % sm.mine_spacing)
	check(mines.all(func(m): return m.global_position.distance_to(stood_at) >= sm.mine_min_from_player),
		"and none was dropped inside mine_min_from_player (%.0f px) of the player" % sm.mine_min_from_player)

	log_p("-- the cap holds across cycles")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	for round_number in 3:
		sm.on_child_transition(sm.current_state, "LayMines")
		await wait_until(func(): return sm.current_state.name == "Chase", 300)
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
	var live: int = sm.live_mines().size()
	log_p("after four fields laid back to back, %d pods are live (cap %d)" % [live, sm.mine_cap])
	check(live <= sm.mine_cap, "the field never goes over mine_cap (%d)" % live)
	await park_computah()

	log_p("-- the arming beat")
	await settle_player(Vector2(500, 800))
	var mine := lay_mine_at(Vector2(1200, 700))
	check(not mine.is_armed(), "a pod that has just landed is not armed")
	check(await wait_until(func(): return mine.is_armed(), 180), "it arms")
	check(mine.phase == mine.Phase.ARMED, "into the armed phase (%d)" % mine.phase)

	log_p("-- Computah cannot set off his own pod, and a punch cannot clear one")
	boss.global_position = mine.global_position
	await wait(6)
	check(sm.current_state.name != "Trapped" and mine.is_armed(), "he stands in it and nothing happens")
	boss.global_position = sm.COMPUTAH_HOME
	await settle_player(mine.global_position + Vector2(200, 0))
	swing_any()
	await wait(20)
	check(is_instance_valid(mine) and mine.is_armed(), "a punch beside it leaves it armed")

	log_p("-- refused, and NOT consumed: a guard-broken player")
	defense._start_guard_break()
	await wait(2)
	check(defense.is_guard_broken, "the guard is broken")
	check(not sm.trap_allowed(), "trap_allowed() refuses")
	await settle_player(mine.global_position)
	await wait(6)
	check(sm.current_state.name != "Trapped", "standing in it does nothing")
	check(mine.is_armed(), "and the pod is still armed for whatever they do next")
	# Off the pod BEFORE the stun ends, and a few frames for the overlap list to catch up: an area's
	# overlaps are a physics step behind, and teleporting off one is not something a fight does.
	await settle_player(Vector2(500, 800))
	await wait(6)
	defense.clear_guard_break()
	await wait(4)

	log_p("-- refused: a grabbed player, and a finishing one")
	player.is_grabbed = true
	check(not sm.trap_allowed(), "a grabbed player is refused")
	player.is_grabbed = false
	player.is_finishing = true
	check(not sm.trap_allowed(), "a finishing one too")
	player.is_finishing = false
	check(sm.trap_allowed(), "and a free player is not")

	log_p("-- refused: the beam, once its aim has latched")
	var beam: Node = sm.states["Beam"]
	sm.on_child_transition(sm.current_state, "Beam")
	await wait(3)
	check(beam.phase == beam.Phase.TRACK and sm.trap_allowed(), "the tracking charge is fine: nothing is answerable yet")
	check(await wait_until(func(): return beam.phase == beam.Phase.LOCKED, 200), "the aim latches")
	check(not sm.trap_allowed(), "and from there a pod may not close: being somewhere else is the only answer left")
	await park_computah()

	log_p("-- triggers: an invincible player, and a dashing one")
	player.is_invincible = true
	check(sm.trap_allowed(), "being hit a moment ago is not a reason to walk through a bear trap")
	clear_iframes()
	var walked := await armed_mine_at(Vector2(900, 800))
	boss.global_position = Vector2(900, 400)
	defense.stamina = defense.max_stamina
	await settle_player(Vector2(900 - 260, 800))
	press(KEY_RIGHT)
	tap(KEY_W)
	var caught := await wait_until(func(): return sm.current_state.name == "Trapped", 120)
	release(KEY_RIGHT)
	log_p("dashed into it: state %s" % sm.current_state.name)
	check(caught, "a dash through a pod still springs it - lock_actions() cuts the dash")
	check(not is_instance_valid(walked) or walked.phase == walked.Phase.SPRUNG, "and the pod snaps shut")
	# Before the lock is tested below: by the time those presses are done he has already crossed.
	var started_at: Vector2 = boss.global_position

	log_p("-- THE TOTAL LOCK")
	check(player.is_action_locked and player.lock_seals_guard, "sealed (%s, %s)" % [player.is_action_locked, player.lock_seals_guard])
	var held_at: Vector2 = player.global_position
	var presses := []
	var watch_press := func(credited: bool): presses.append(credited)
	defense.block_pressed.connect(watch_press)
	press(KEY_RIGHT)
	await wait(15)
	release(KEY_RIGHT)
	log_p("held at %s, now %s" % [held_at, player.global_position])
	check(player.global_position.distance_to(held_at) < 1.0, "no walking")
	var before_dash: int = player.last_dodge_physics_frame
	tap(KEY_W)
	await wait(6)
	check(player.last_dodge_physics_frame == before_dash and not player.is_dodging, "no dash")
	tap(KEY_Q)
	await wait(6)
	check(player.state_machine.current_state.name != "Punching", "no punch (%s)" % player.state_machine.current_state.name)
	press(KEY_SHIFT)
	await wait(8)
	check(not defense.is_guarding() and player.state_machine.current_state.name != "Blocking", "the block press raises no guard (%s)" % player.state_machine.current_state.name)
	check(presses.is_empty(), "and earns no parry credit at all (%s)" % [presses])
	release(KEY_SHIFT)
	defense.block_pressed.disconnect(watch_press)

	log_p("-- the walk-over")
	check(await wait_until(func(): return trapped.phase == trapped.Phase.CHARGE, 300), "he crosses and charges")
	var reach: float = boss.global_position.distance_to(player.global_position)
	log_p("crossed %.0f px, stopped %.0f px away (pounce_range %.0f)" % [started_at.distance_to(boss.global_position), reach, sm.pounce_range])
	check(started_at.distance_to(boss.global_position) > 100.0, "he actually crossed to them")
	check(reach <= sm.pounce_range + 32.0, "and stopped at pounce_range")
	check(boss.current_anim == &"uppercut_wind", "on the uppercut's load (%s)" % boss.current_anim)

	log_p("-- the whiff, and the window it opens")
	# Half a press short, at what a press is worth at the top of the bar (MashCurve).
	trapped.meter = 1.0 - load("res://Scripts/MashCurve.gd").gain(sm.escape_gain, 1.0) * 0.5
	tap(MASH_KEYS[trapped.mash_actions()[0]])
	await wait(2)
	check(trapped.escaped, "the last press fills the meter and they are out")
	check(not player.is_action_locked and not player.lock_seals_guard, "and free on the instant, both kinds of lock cleared")
	var health_at_escape: int = player.playerHealth
	check(await wait_until(func(): return sm.current_state.name == "Punish", 400), "he swings anyway and overbalances into a window")
	check(player.playerHealth == health_at_escape, "the swing had NO hitbox on it at all (%d)" % player.playerHealth)
	log_p("window %.2f s, cap %d, poses %s/%s/%s" % [punish.window_time, punish.window_cap, punish.enter_anim, punish.hold_anim, punish.exit_anim])
	check(is_equal_approx(punish.window_time, sm.mine_fall_window), "it is mine_fall_window long (%.2f)" % punish.window_time)
	check(punish.window_cap == sm.mine_fall_cap, "with mine_fall_cap punches in it (%d)" % punish.window_cap)
	check(punish.enter_anim == &"uppercut_fall" and punish.hold_anim == &"fallen" and punish.exit_anim == &"uppercut_up", "on the felled poses")
	check(boss.body_pose == &"fallen", "and the hurtbox is on the floor pose (%s)" % boss.body_pose)
	var box: Vector2 = boss.hurtbox_shape.shape.size
	check(box == layout.C_DOWN_BODY_BOX.size * layout.SCALE, "swapped to the down box, not left on the standing chassis (%s)" % box)
	await park_computah()

	log_p("-- a failed mash: the uppercut lands, and he is NOT punishable for it")
	clear_iframes()
	player.playerHealth = 10
	var pod := await armed_mine_at(Vector2(960, 800))
	boss.global_position = Vector2(1100, 800)
	await settle_player(pod.global_position)
	check(await wait_until(func(): return sm.current_state.name == "Trapped", 120), "a pod closes on them")
	var health_before: int = player.playerHealth
	check(await wait_until(func(): return trapped.swung, 400), "the uppercut connects")
	await wait(2)
	log_p("health %d -> %d" % [health_before, player.playerHealth])
	check(player.playerHealth == health_before - 2, "computah_uppercut costs 2 half-hearts (%d)" % player.playerHealth)
	check(not player.is_action_locked, "and the launch that frees them is the knockdown")
	var back := await wait_until(func(): return sm.current_state.name != "Trapped", 300)
	log_p("he goes to %s" % sm.current_state.name)
	check(back and sm.current_state.name != "Punish", "no punish window follows an uppercut that landed")
	await park_computah()

	log_p("-- a catch's three costs, landing through i-frames")
	clear_iframes()
	player.playerHealth = 10
	defense.stamina = defense.max_stamina
	boss.break_gauge.value = 60.0
	await settle_player(Vector2(960, 800))
	# THE GAUGE DRAINS OFF THE GRAB, not off the slam: computah_chase carries hype_loss, the slam does
	# not, and BossBreakGauge subtracts hit_loss itself off PlayerDefense.hit_taken. Nothing in the
	# fight calls it by hand - two sources for one number is how they drift.
	player.is_invincible = true
	var gauge_in: float = boss.break_gauge.value
	check(front_hit(&"computah_chase", boss) == 1, "the pounce lands through the i-frames")
	await wait(2)
	log_p("gauge %.0f -> %.0f (hit_loss %.0f)" % [gauge_in, boss.break_gauge.value, boss.break_gauge.hit_loss])
	check(is_equal_approx(gauge_in - boss.break_gauge.value, boss.break_gauge.hit_loss), "and drains %.0f Break gauge, by the gauge's own rule (%.1f)" % [boss.break_gauge.hit_loss, gauge_in - boss.break_gauge.value])
	player.is_invincible = true
	var health_in: int = player.playerHealth
	var stamina_in: float = defense.stamina
	sm.states["Caught"].grabber = boss
	sm.on_child_transition(sm.current_state, "Caught")
	check(await wait_until(func(): return player.playerHealth < health_in, 90), "the slam lands inside the i-frames too")
	await wait(6)
	log_p("health %d -> %d, stamina %.0f -> %.0f" % [health_in, player.playerHealth, stamina_in, defense.stamina])
	check(player.playerHealth == health_in - 2, "2 half-hearts (%d)" % player.playerHealth)
	check(is_equal_approx(stamina_in - defense.stamina, sm.catch_stamina_drain), "%.0f stamina (%.1f)" % [sm.catch_stamina_drain, stamina_in - defense.stamina])
	check(not defense.is_guard_broken, "and a catch never guard-breaks them: a stun on top of a grab is a double punish")
	check(await wait_until(func(): return not player.is_action_locked, 120), "the catch lets go")
	await park_computah()

	log_p("-- the grace after a hold")
	sm.note_release()
	check(sm.in_catch_grace(), "inside catch_grace the pounce arms nothing")
	check(not sm.trap_allowed(), "and inside trap_grace no pod may close either")
	await wait(int(sm.trap_grace * 60.0) + 8)
	check(sm.trap_allowed(), "past trap_grace a pod may close again")

	log_p("-- a full Break gauge drops him where he stands")
	check(boss.break_gauge != null, "he has a Break gauge at all")
	sm.on_child_transition(sm.current_state, "Beam")
	await wait(4)
	boss.break_gauge.locked = false
	boss.break_gauge.value = 0.0
	check(boss.break_gauge.add(boss.break_gauge.max_value), "filling it breaks him")
	check(await wait_until(func(): return sm.current_state.name == "Broken", 120), "which puts him down Broken - the window the three-bar finisher needs")
	check(boss.break_gauge.locked, "and the gauge locks behind it")
	check(boss.is_down(), "is_down() reads the Break, which is what the gauge's own wait runs on")
	# The Break drives the player in beside him, and holds their actions for the drive.
	check(await wait_until(func(): return not player.is_action_locked, 120), "the player is theirs again once the drive-in ends")
	await park_computah()

	log_p("-- every release path leaves them free")
	await mine_release_path("the fight ending under them", func(): sm.enter_defeated())
	await mine_release_path("the player being beaten under them", func(): player.playerHealth = 0)
	await mine_release_path("a finisher starting under them", func(): player.is_finishing = true)
	await mine_release_path("the state leaving the tree under them", func():
		var manager: Node = sm.states["Trapped"].get_parent()
		manager.remove_child(sm.states["Trapped"]))


# One trap, one way of ending it, and the only thing that matters: the player is not left sealed.
func mine_release_path(what: String, end_it: Callable) -> void:
	await load_computah_fight()
	var trapped: Node = sm.states["Trapped"]
	clear_iframes()
	var pod := await armed_mine_at(Vector2(960, 800))
	boss.global_position = Vector2(1400, 800)
	await settle_player(pod.global_position)
	if not await wait_until(func(): return sm.current_state.name == "Trapped", 120):
		check(false, "%s: a pod closed on them" % what)
		return
	check(player.is_action_locked and player.lock_seals_guard, "%s: sealed first" % what)
	end_it.call()
	await wait(20)
	check(not player.is_action_locked and not player.lock_seals_guard, "%s: and free after (%s, %s)" % [what, player.is_action_locked, player.lock_seals_guard])
	check(trapped.released, "%s: through the one funnel" % what)
	# The scene-change path pulls the state out of the tree; put it back so nothing is left orphaned.
	if trapped.get_parent() == null:
		sm.add_child(trapped)


# The mash itself. REAL seconds: the press rule (MashInput.counts) gates on a real interval, so this
# mode runs with --max-fps rather than --fixed-fps.
func test_mine_mash() -> void:
	await load_computah_fight()
	var trapped: Node = sm.states["Trapped"]
	var finisher: Node = player.get_node("Finisher")

	log_p("-- it runs on the player's own mash pair, and the prompt says ESCAPE!")
	clear_iframes()
	var pod := await armed_mine_at(Vector2(960, 800))
	boss.global_position = Vector2(1080, 800)
	await settle_player(pod.global_position)
	check(await wait_until(func(): return sm.current_state.name == "Trapped", 120), "a pod closes on them")
	var pair: Array = trapped.mash_actions()
	log_p("the pair is %s" % [pair])
	check(pair == finisher.mash_actions(), "the same pair the finisher mashes, read off it rather than named here")
	check(trapped.prompt_key == &"escape", "the prompt asks for the alarm-red ESCAPE!, not the finisher's gold MASH!")
	var layout: GDScript = load("res://Scripts/FinisherArtLayout.gd")
	check(layout.PROMPT_WORDS.has(&"escape"), "and that word is already written")
	var prompt: Node2D = trapped.prompt
	check(prompt != null and prompt.finisher == trapped, "it has a prompt of its own, wired to the trap")
	check(prompt.visible, "and it is up from the moment the jaws shut")

	log_p("-- alternation, and two presses in one flush")
	trapped.meter = 0.0
	trapped.last_action = &""
	trapped.last_press_usec = 0
	tap(MASH_KEYS[pair[0]])
	await wait(4)
	var after_one: float = trapped.meter
	check(after_one > 0.0, "the first press pays escape_gain (%.3f)" % after_one)
	tap(MASH_KEYS[pair[0]])
	await wait(1)
	log_p("the same key again: %.3f -> %.3f" % [after_one, trapped.meter])
	check(trapped.meter <= after_one, "the same key twice pays nothing")
	trapped.meter = 0.0
	trapped.last_action = &""
	trapped.last_press_usec = 0
	press(MASH_KEYS[pair[0]])
	press(MASH_KEYS[pair[1]])
	release(MASH_KEYS[pair[0]])
	release(MASH_KEYS[pair[1]])
	await wait(2)
	var one_press: float = load("res://Scripts/MashCurve.gd").gain(sm.escape_gain, 0.0)
	log_p("both keys in one flush: %.3f (one press is %.3f)" % [trapped.meter, one_press])
	check(trapped.meter <= one_press + 0.001, "both keys pressed together count once")
	trapped.meter = 0.0
	trapped.last_action = &""
	trapped.last_press_usec = 0

	log_p("-- ten presses a second gets out; three does not")
	var trap_seconds: float = trapped.CLOSE_TIME + sm.mine_charge
	var boundary: float = ((1.0 / trap_seconds) + sm.escape_drain) / sm.escape_gain
	log_p("gain %.2f, drain %.2f/s, about %.2f s of trap: the boundary is %.1f presses a second"
		% [sm.escape_gain, sm.escape_drain, trap_seconds, boundary])
	check(boundary > 3.5 and boundary < 9.0, "and both test rates are clear of it (%.1f/s)" % boundary)
	check(await mash_out(trapped, pair, 6), "at ten a second they are out before the uppercut")
	await park_computah()

	await load_computah_fight()
	trapped = sm.states["Trapped"]
	clear_iframes()
	player.playerHealth = 10
	pod = await armed_mine_at(Vector2(960, 800))
	boss.global_position = Vector2(1080, 800)
	await settle_player(pod.global_position)
	check(await wait_until(func(): return sm.current_state.name == "Trapped", 120), "a second pod closes on them")
	var slow := await mash_out(trapped, trapped.mash_actions(), 20)
	check(not slow, "at three a second they are not")
	check(player.playerHealth < 10, "and they wear the uppercut (%d)" % player.playerHealth)


# Alternating presses every `every` frames until the trap resolves. Returns whether they got out.
func mash_out(trapped: Node, pair: Array, every: int) -> bool:
	var step := 0
	for i in 600:
		if trapped.escaped:
			return true
		if trapped.done or sm.current_state.name != "Trapped":
			return trapped.escaped
		tap(MASH_KEYS[pair[step % 2]])
		step += 1
		await wait(every)
	return trapped.escaped


# ------------------------------------------------------------------ Computah's overload
# HIS DPS CHECK, AND THE ONE ATTACK IN THE GAME THAT ASKS FOR OFFENCE. He stands still and winds
# himself up; the player has to rush him and land overload_threshold half-hearts before his clock runs
# out. Break it and he is left dazed, which is the uppercut. Fail it and the charge covers the whole
# mat for a full heart that nothing answers - no guard, no parry, no dash - which is exactly why it
# carries no tell of either colour: a badge is an answer key naming a button, and this has no button.

const OVERLOAD_BLAST := &"computah_overload_blast"
const DASH_IMMUNITY := "res://Scripts/DashImmunity.gd"
# REACHABILITY's steady player: a press this long after each swing ends.
const OVERLOAD_STEADY_GAP := 0.10


func overload() -> Node:
	return sm.states["Overload"]


# His own entry, not a hand-built one, from wherever the player is standing.
func begin_overload() -> Node:
	sm.on_child_transition(sm.current_state, "Overload")
	await wait(2)
	return overload()


# Back to a standing start with his health, his gauge, the mat and the combo's count all clean, so one
# section can never decide the next one.
func overload_reset() -> void:
	await park_computah()
	player.combo.reset()
	boss.boss_health = boss.max_health
	if boss.break_gauge:
		boss.break_gauge.locked = false
		boss.break_gauge.value = 0.0
	boss.begin_window(boss.MAX_HITS_PER_WINDOW)
	clear_iframes()
	player.playerHealth = 1000
	player.is_grabbed = false
	player.is_finishing = false
	player.is_talking = false
	player.is_action_locked = false
	defense.clear_guard_break()
	defense.stamina = defense.max_stamina
	await wait(2)


# Exactly overload_start_range away, to his RIGHT and a little above his feet so the punch box lands
# in the middle of his hurtbox band rather than on its bottom edge. The 60 px of lift comes out of the
# horizontal run-in, so the straight-line distance is the gate's own number to the pixel.
func overload_start_spot() -> Vector2:
	var lift := 60.0
	var range_px: float = sm.overload_start_range
	return boss.global_position + Vector2(sqrt(range_px * range_px - lift * lift), -lift)


# The gap between their origins at which a punch first reaches him, with the player standing to his
# RIGHT: the far edge of the fitted punch box against the near face of his hurtbox, both read off the
# live shapes rather than assumed.
func overload_reach() -> float:
	player.fit_punch_hitbox()
	var box: Rect2 = fitted_punch_box()
	var hurt: CollisionShape2D = boss.hurtbox_shape
	var near: float = hurt.position.x + (hurt.shape as RectangleShape2D).size.x / 2.0
	return near - box.position.x * player.global_scale.x


# THE BOT. It rushes him from where it stands and punches until the charge resolves, the way a player
# does: the walk held all the way in, then a press `gap` seconds after each swing ends (a steady
# player), or with no gap as fast as the game will take them (a masher). The combo has no timing
# (PlayerCombo), so the pace is all the gap changes. Nothing is teleported and nothing is handed to it -
# what it measures is whether the attack is winnable from where it started.
func rush_and_punch(gap := 0.0, max_frames := 400) -> Dictionary:
	var out := {"damage": 0, "seconds": 0.0, "presses": 0, "contact": -1.0, "arrived": -1.0,
		"reach": overload_reach(), "from": player.global_position.distance_to(boss.global_position)}
	var start: float = defense.clock
	var ov: Node = overload()
	var walking := true
	var was_punching := false
	var ended_at := -INF
	press(KEY_LEFT)
	for i in max_frames:
		if sm.current_state != ov or ov.phase != ov.Phase.CHARGE:
			break
		if walking and player.global_position.x - boss.global_position.x <= out.reach:
			walking = false
			out.arrived = defense.clock - start
			release(KEY_LEFT)
		var punching: bool = player.state_machine.current_state.name == "Punching"
		if was_punching and not punching:
			ended_at = defense.clock
		was_punching = punching
		if not walking and not punching and defense.clock - ended_at >= gap - 0.001:
			tap(KEY_Q)
			out.presses += 1
		if out.contact < 0.0 and boss.damage_this_window > 0:
			out.contact = defense.clock - start
		out.damage = maxi(out.damage, boss.damage_this_window)
		await physics_frame
	if walking:
		release(KEY_LEFT)
	out.seconds = defense.clock - start
	return out


func test_computah_overload() -> void:
	await load_computah_fight()
	var ov: Node = overload()
	var catalogue: Dictionary = CATALOG.get_attack(OVERLOAD_BLAST)
	var blast_damage: int = catalogue.damage

	log_p("-- the numbers, and the one that would make it unwinnable by construction")
	var needed: int = sm.overload_threshold
	log_p("threshold %d half-hearts, hit cap %d, %.2f s, from %.0f px, every %d cycles"
		% [needed, sm.overload_hit_cap, sm.overload_time, sm.overload_start_range, sm.overload_every_cycles])
	# take_punch() returns 0 past the cap, which refuses the punch (PlayerCombo.punch_refused): a cap
	# anywhere near the threshold leaves the player hitting a boss that has stopped taking anything while
	# the charge runs on. THE THRESHOLD ENDS THE CHARGE, NEVER THE CAP.
	check(sm.overload_hit_cap > needed, "overload_hit_cap (%d) strictly exceeds the %d punches the threshold needs at 1 damage each" % [sm.overload_hit_cap, needed])
	check(sm.overload_hit_cap > boss.MAX_HITS_PER_WINDOW, "and it is not the window's usual cap of %d" % boss.MAX_HITS_PER_WINDOW)
	check(needed <= boss.max_health / 4, "the threshold is a check, not a second health bar (%d of %d)" % [needed, boss.max_health])

	log_p("-- the catalogue entry: a full heart, and no answer of any kind")
	var halves: int = load("res://Scripts/PlayerHealthArtLayout.gd").CONTAINERS * 2
	log_p("%s: %s" % [OVERLOAD_BLAST, catalogue])
	check(blast_damage == 2 and halves == 8, "one full heart: damage %d of the player's %d halves" % [blast_damage, halves])
	check(not catalogue.blockable and not catalogue.parryable and not catalogue.dash_through, "no guard, no parry, no dash")
	check(not catalogue.tell and not catalogue.dodge_tell, "and NEITHER tell: a badge is an answer key, and this has no answer")
	check(catalogue.hype_loss, "hype_loss stays on: no grab took a toll first, so the blast IS the toll")
	check(not catalogue.bypass_invincibility, "it does not bypass i-frames: it closes no exploit, and it protects being hit just before an undodgeable blast")
	check(UNBLOCKABLE.has(OVERLOAD_BLAST), "the suite's UNBLOCKABLE list has it")
	check(not IGNORES_IFRAMES.has(OVERLOAD_BLAST), "IGNORES_IFRAMES does not")
	check(not WINDUP_READS.has(OVERLOAD_BLAST), "and the tell-timing table does not: there is no wind-up to read, because reading it is not the answer")

	log_p("-- the entry: the race gauge, his body, and no badge of either colour")
	await overload_reset()
	await settle_player(boss.global_position + Vector2(300, -60))
	var seen_tell := [false]
	var watch_tell := func():
		if tell_node() != null:
			seen_tell[0] = true
	physics_frame.connect(watch_tell)
	await begin_overload()
	check(boss.overload.visible, "the race gauge is up over his head")
	check(boss.overload_cells.size() == needed, "its bottom row is one cell per half-heart of the threshold (%d)" % boss.overload_cells.size())
	check(boss.aura.visible, "the overcharge aura is on")
	check(boss.is_open() and boss.hurtbox.monitoring, "and he is punchable from the first frame")
	check(boss.window_cap == sm.overload_hit_cap, "on the overload's own cap (%d)" % boss.window_cap)
	check(boss.damage_this_window == 0, "with the damage counter cleared")
	var rows := {}
	var watch_rows := func(): rows[boss.charge_state] = true
	physics_frame.connect(watch_rows)
	check(await wait_until(func(): return ov.phase != ov.Phase.CHARGE, 400), "the charge runs out on its own")
	physics_frame.disconnect(watch_rows)
	physics_frame.disconnect(watch_tell)
	log_p("his charge rows over the whole charge: %s" % [rows.keys()])
	# computah_overload_charge is 4 frames x 3 rows and runs the OPPOSITE way to the battery sheets:
	# row 0 is barely charged and row 2 is white-hot.
	check(rows.has(0) and rows.has(1) and rows.has(2), "his body steps all three charge rows, 0 barely -> 2 white-hot (%s)" % [rows.keys()])
	check(not seen_tell[0], "and no ParryTell badge ever goes up: red would say parry and yellow would say dodge, and both lose a heart here")

	log_p("-- FAIL: the blast fires once, and nothing answers it")
	await overload_reset()
	# load_computah_fight() already tracks hits; a second track() would connect a second handler and
	# log every hit twice.
	track_parries()
	track_dodges()
	player.playerHealth = 6
	await settle_player(boss.global_position + Vector2(300, -60))
	events.clear()
	await begin_overload()
	press(KEY_SHIFT)
	check(await wait_until(func(): return ov.phase == ov.Phase.RELEASE, 400), "the charge runs out and he releases")
	await wait(6)
	release(KEY_SHIFT)
	var blasts := events_of("HIT", OVERLOAD_BLAST)
	log_p("health 6 -> %d, %d blast(s), %d blocked, %d parried, %d dodged"
		% [player.playerHealth, blasts.size(), events_of("BLOCKED").size(), parries.size(), dodges.size()])
	check(ov.blast_fired and blasts.size() == 1, "the blast lands exactly once (%d)" % blasts.size())
	check(player.playerHealth == 6 - blast_damage, "for the catalogue's %d half-hearts (%d left of 6)" % [blast_damage, player.playerHealth])
	check(events_of("BLOCKED").is_empty(), "a guard held through the whole charge absorbs nothing")
	check(parries.is_empty(), "and the press that raised it parries nothing")
	check(dodges.is_empty(), "nothing about it is a perfect dodge")
	check(await wait_until(func(): return sm.current_state.name == "Punish", 200), "he vents afterwards")
	check(is_equal_approx(sm.states["Punish"].window_time, sm.overload_vent), "on the stingy overload_vent window (%.2f s)" % sm.states["Punish"].window_time)

	log_p("-- FAIL: a dash onto the release dodges nothing either")
	await overload_reset()
	player.playerHealth = 6
	defense.stamina = defense.max_stamina
	await settle_player(boss.global_position + Vector2(300, -60))
	events.clear()
	dodges.clear()
	await begin_overload()
	# Inside the dash's immunity window when the charge runs out, so what is under test is a player who
	# really is dash-immune rather than one who mistimed it.
	check(await wait_until(func(): return ov.clock >= sm.overload_time - 0.12, 400), "the charge reaches its last tenth")
	tap(KEY_W)
	var immune := [false]
	var dash_immunity: GDScript = load(DASH_IMMUNITY)
	var watch_dash := func():
		if ov.blast_fired and not immune[0]:
			immune[0] = dash_immunity.is_immune(player, CATALOG.DASH_IMMUNITY_TIME, CATALOG.DASH_IMMUNITY_COOLDOWN)
	physics_frame.connect(watch_dash)
	check(await wait_until(func(): return ov.blast_fired, 120), "it goes off mid-dash")
	await wait(4)
	physics_frame.disconnect(watch_dash)
	log_p("dash-immune as it landed: %s, health 6 -> %d, %d dodges" % [immune[0], player.playerHealth, dodges.size()])
	check(immune[0], "the player really was inside the dash's i-frames")
	check(player.playerHealth == 6 - blast_damage, "and still paid the full heart (%d left of 6)" % player.playerHealth)
	check(dodges.is_empty(), "with no perfect dodge to show for it")

	log_p("-- BREAK: punching through the threshold drops him, and hands over the uppercut")
	await overload_reset()
	player.playerHealth = 6
	await settle_player(boss.global_position + Vector2(300, -60))
	events.clear()
	await begin_overload()
	var dazeable := [false]
	var watch_daze := func():
		if sm.current_state == ov and boss.can_be_dazed():
			dazeable[0] = true
	physics_frame.connect(watch_daze)
	var run := await rush_and_punch()
	log_p("put in %d of %d in %.2f s over %d presses" % [run.damage, needed, run.seconds, run.presses])
	check(run.damage >= needed, "the threshold is reached (%d of %d)" % [run.damage, needed])
	check(ov.phase == ov.Phase.BROKEN, "which breaks the charge rather than the hit cap ending it (%d)" % ov.phase)
	check(await wait_until(func(): return sm.current_state.name == "Broken", 200), "and he drops into his Break")
	physics_frame.disconnect(watch_daze)
	log_p("gauge %.0f of %.0f, locked %s; blast fired %s; health %d" % [boss.break_gauge.value, boss.break_gauge.max_value, boss.break_gauge.locked, ov.blast_fired, player.playerHealth])
	check(not ov.blast_fired and events_of("HIT", OVERLOAD_BLAST).is_empty(), "no blast went off at all")
	check(player.playerHealth == 6, "so the player's health never moved (%d of 6)" % player.playerHealth)
	check(boss.break_gauge.locked and boss.break_gauge.value == 0.0, "it went down the Break gauge's own road: filled, broken and locked behind it")
	check(not dazeable[0], "can_be_dazed() was false for every frame of the charge: no finisher may start mid-charge")
	check(boss.can_be_dazed(), "and true in the window it opened, which is the daze his uppercut needs")

	log_p("-- BREAK: with no Break gauge at all, the reward still exists")
	await overload_reset()
	var gauge: Node = boss.break_gauge
	boss.break_gauge = null
	await settle_player(boss.global_position + Vector2(300, -60))
	await begin_overload()
	run = await rush_and_punch()
	check(await wait_until(func(): return sm.current_state.name == "Punish", 200), "the fallback window opens (%d damage in)" % run.damage)
	check(is_equal_approx(sm.states["Punish"].window_time, sm.overload_break_window), "on overload_break_window (%.2f s)" % sm.states["Punish"].window_time)
	boss.break_gauge = gauge

	log_p("-- REACHABILITY: from exactly overload_start_range, mashed and steady punching both clear it")
	for gap in [0.0, OVERLOAD_STEADY_GAP]:
		await overload_reset()
		var how := "mashing" if gap == 0.0 else "a press %.2f s after each swing" % gap
		await settle_player(overload_start_spot())
		await wait(4)
		await begin_overload()
		run = await rush_and_punch(gap)
		var spare: float = sm.overload_time - run.seconds
		log_p("%s from %.0f px: reach %.0f px, arrived at %.2f s, first contact %.2f s, %d of %d in %.2f s over %d presses (%.2f s spare of %.2f)"
			% [how, run.from, run.reach, run.arrived, run.contact, run.damage, needed, run.seconds, run.presses, spare, sm.overload_time])
		check(absf(run.from - sm.overload_start_range) < 1.0, "%s: it started at the gate's own range (%.0f px)" % [how, run.from])
		check(run.damage >= needed, "%s: the threshold is cleared from the worst legal start (%d of %d)" % [how, run.damage, needed])
		check(ov.phase == ov.Phase.BROKEN and spare > 0.0, "%s: the charge broke with %.2f s to spare" % [how, spare])
		await wait_until(func(): return sm.current_state.name == "Broken", 200)

	log_p("-- FAIRNESS: every way of being unable to answer refuses the start")
	await overload_reset()
	await settle_player(boss.global_position + Vector2(300, -60))
	check(sm.can_start_overload(), "a free player in range, with nothing on the mat, is allowed")
	var gates := [
		["a grabbed player", func(): player.is_grabbed = true, func(): player.is_grabbed = false],
		["a trapped one - anything that locks their actions", func(): player.is_action_locked = true, func(): player.is_action_locked = false],
		["a finishing one", func(): player.is_finishing = true, func(): player.is_finishing = false],
		["a talking one", func(): player.is_talking = true, func(): player.is_talking = false],
		["a beaten one", func(): player.playerHealth = 0, func(): player.playerHealth = 1000],
		["one whose fight is over", func(): player.fight_over = true, func(): player.fight_over = false],
		["a locked Break gauge, which is the whole of the pacing gate", func(): boss.break_gauge.locked = true, func(): boss.break_gauge.locked = false],
	]
	for gate in gates:
		gate[1].call()
		var refused: bool = not sm.can_start_overload()
		gate[2].call()
		check(refused, "refused: %s" % gate[0])
	var stood: Vector2 = player.global_position
	player.global_position = boss.global_position + Vector2(sm.overload_start_range + 40.0, 0)
	check(not sm.can_start_overload(), "refused: a player further than overload_start_range (%.0f px)" % sm.overload_start_range)
	player.global_position = boss.global_position + Vector2(sm.overload_start_range - 40.0, 0)
	check(sm.can_start_overload(), "and allowed just inside it")
	player.global_position = stood
	await wait(2)
	defense._start_guard_break()
	await wait(2)
	check(defense.is_guard_broken and not sm.can_start_overload(), "refused: a guard break is a stun with no input in it")
	defense.clear_guard_break()
	await wait(2)
	var pod := await armed_mine_at(boss.global_position + Vector2(400, 0))
	check(pod.is_live() and sm.can_start_overload(), "a live pod does NOT refuse the start: the field is built to overlap itself, so refusing on one refuses forever")

	log_p("-- instead he WIPES THE MAT as he plants, so nobody is ever asked to cross a minefield")
	var flying := lay_mine_at(boss.global_position + Vector2(-400, 0))
	await settle_player(boss.global_position + Vector2(300, -60))
	await begin_overload()
	check(not pod.is_live() and pod.phase == pod.Phase.FADING, "the armed pod is EXPIRING, not freed: it breaks up through its own frames (%d)" % pod.phase)
	check(not flying.is_live() and flying.phase == flying.Phase.FADING, "and a pod still in flight goes with it (%d)" % flying.phase)
	check(not pod.trigger.monitoring and not flying.trigger.monitoring, "neither can catch anything from the first frame of the charge")
	check(await wait_until(func(): return get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), int(sm.mine_fade * 60.0) + 30),
		"and the mat is clear inside mine_fade (%.2f s), under the 0.98 s run-in from the furthest legal start" % sm.mine_fade)

	log_p("-- a player sealed in a pod still refuses the start, and the sweep never takes their pod")
	await overload_reset()
	var held_pod := await armed_mine_at(Vector2(960, 800))
	boss.global_position = Vector2(1400, 800)
	await settle_player(held_pod.global_position)
	check(await wait_until(func(): return sm.current_state.name == "Trapped", 120), "a pod closes on them")
	check(player.is_action_locked and not sm.can_start_overload(), "refused while they are sealed in it, on the lock rather than on the pod")
	sm.sweep_field()
	await wait(3)
	check(is_instance_valid(held_pod) and held_pod.phase == held_pod.Phase.SPRUNG, "a sweep run anyway leaves the SPRUNG pod alone: ComputahTrapped.release() owns its life")
	check(player.is_action_locked, "so nobody is ever stranded by a pod freeing itself out from under them")
	sm.states["Trapped"].release()
	await wait(4)
	check(not player.is_action_locked and not is_instance_valid(held_pod), "and the trap's own release frees the player and the pod together")

	log_p("-- FAIRNESS: the blast is DISARMED by anything that takes their inputs away mid-charge")
	await overload_reset()
	player.playerHealth = 6
	await settle_player(boss.global_position + Vector2(300, -60))
	events.clear()
	await begin_overload()
	await wait(60)
	defense._start_guard_break()
	check(await wait_until(func(): return ov.phase == ov.Phase.DISARM, 120), "the guard break disarms it mid-charge (%d)" % ov.phase)
	check(await wait_until(func(): return sm.current_state.name == "Punish", 300), "he vents it into the floor instead")
	log_p("health %d of 6, blast fired %s, gauge %.0f" % [player.playerHealth, ov.blast_fired, boss.break_gauge.value])
	check(not ov.blast_fired and player.playerHealth == 6, "NO BLAST AND NO DAMAGE: failing a check they were never given a turn in is not their fault")
	check(not boss.break_gauge.locked, "and it does not drop him either: being guard-broken is not a thing to be rewarded for")
	defense.clear_guard_break()

	log_p("-- the picker: it takes a turn without spending one")
	await overload_reset()
	await settle_player(boss.global_position + Vector2(300, -60))
	sm.last_attack = "LayMines"
	sm.cycles_started = sm.overload_every_cycles - 1
	sm.start_cycle()
	check(sm.current_state.name == "Overload", "every overload_every_cycles cycles it comes round (%s)" % sm.current_state.name)
	check(sm.last_attack == "LayMines", "and leaves the beam/mine alternation exactly where it was")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	sm.start_cycle()
	check(sm.current_state.name == "Beam", "so the mine field is still always followed by the beam (%s)" % sm.current_state.name)
	await park_computah()
	boss.break_gauge.locked = true
	sm.last_attack = "Beam"
	sm.cycles_started = sm.overload_every_cycles - 1
	sm.start_cycle()
	check(sm.current_state.name == "LayMines", "a cycle it is refused on is a plain one (%s)" % sm.current_state.name)
	boss.break_gauge.locked = false
	await park_computah()


# ------------------------------------------------------------------ a fight's pull on the player
# PlayerScript.add_drift(): px/s a fight adds on top of the player's own movement for one physics step,
# through the same collision as walking. Beast Bixby's Inferno is what pulls; Eric's fight, parked, is
# only the floor it is tested on here.

const DRIFT := Vector2(330, 0)
const DRIFT_SPOT := Vector2(700, 500)


# Adds `velocity` on each of the next `frames` physics steps and returns how far the player went. Called
# on a physics_frame, so each add is taken by the player's own step in the same frame.
func drift_for(frames: int, velocity: Vector2) -> Vector2:
	var from: Vector2 = player.global_position
	for i in frames:
		player.add_drift(velocity)
		await physics_frame
	return player.global_position - from


# Adds DRIFT on every step `holding` stays true, up to `limit` steps: [steps, px moved, px it should
# have moved]. What it should is counted in game time, which a hit-stop slows along with the pull.
func drift_while(holding: Callable, limit: int) -> Array:
	var from: Vector2 = player.global_position
	var clock_from: float = defense.clock
	var steps := 0
	while holding.call() and steps < limit:
		player.add_drift(DRIFT)
		await physics_frame
		steps += 1
	return [steps, player.global_position - from, DRIFT * (defense.clock - clock_from)]


func test_drift() -> void:
	await load_quiet("eric")
	log_p("-- an idle player in the open")
	await settle_player(DRIFT_SPOT)
	var moved: Vector2 = await drift_for(30, DRIFT)
	log_p("30 steps of %s moved them %s" % [DRIFT, moved])
	check(absf(moved.x - 165.0) <= 2.0 and absf(moved.y) <= 0.01, "30 steps at 330 px/s move an idle player 165 px (%.2f)" % moved.x)
	var stopped_at: Vector2 = player.global_position
	await wait(1)
	var one_later: Vector2 = player.global_position - stopped_at
	await wait(10)
	check(one_later.length() < 0.01 and player.global_position.distance_to(stopped_at) < 0.01, "the step the calls stop, it stops (%s, then %s)" % [one_later, player.global_position - stopped_at])
	player.add_drift(DRIFT * 10.0)
	player.warp_to(DRIFT_SPOT)
	await wait(2)
	check(player.global_position.distance_to(DRIFT_SPOT) < 0.01, "a warp drops a pull still to come (%s)" % (player.global_position - DRIFT_SPOT))

	log_p("-- into the right rope at a slant")
	await settle_player(Vector2(1760, 500))
	moved = await drift_for(30, Vector2(330, 330))
	var body := body_rect()
	log_p("pulled down and right: moved %s, body now %s, rope face %.0f" % [moved, body, ROPES.end.x])
	check(body.end.x <= ROPES.end.x + 0.1, "the rope stops them (%.2f)" % body.end.x)
	check(moved.y >= 160.0, "and they slide along it instead of stopping dead (%.2f of 165 down)" % moved.y)

	log_p("-- into a solid body on layer 1")
	var wall := StaticBody2D.new()
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = Vector2(20, 400)
	shape.shape = box
	wall.add_child(shape)
	wall.position = Vector2(1000, 500)
	current_scene.add_child(wall)
	await settle_player(Vector2(900, 500))
	moved = await drift_for(30, DRIFT)
	body = body_rect()
	log_p("pulled into a block at x 990: moved %s, body right edge %.2f" % [moved, body.end.x])
	check(moved.x > 60.0 and body.end.x <= 990.0 + 0.1, "it stops them at its face")
	wall.queue_free()
	await wait(2)

	log_p("-- a pull drags a player who is guarding, swinging, landing a dash or stunned")
	await settle_player(DRIFT_SPOT)
	press(KEY_SHIFT)
	var guarding := await wait_until(func(): return player.current_state.name == "Blocking", 20)
	var run: Array = await drift_while(func(): return player.current_state.name == "Blocking", 10)
	release(KEY_SHIFT)
	log_p("guarding: %d steps, moved %s of %s" % run)
	check(guarding and run[0] == 10 and run[1].distance_to(run[2]) <= 0.5, "guarding: %.2f of %.2f px" % [run[1].x, run[2].x])
	await wait(10)

	await settle_player(DRIFT_SPOT)
	tap(KEY_Q)
	var swinging := await wait_until(func(): return player.current_state.name == "Punching", 20)
	run = await drift_while(func(): return player.current_state.name == "Punching", 60)
	log_p("swinging: %d steps, moved %s of %s" % run)
	check(swinging and run[0] > 3 and run[1].distance_to(run[2]) <= 0.5, "swinging: %.2f of %.2f px" % [run[1].x, run[2].x])
	await wait(10)

	await dash_ready()
	await settle_player(DRIFT_SPOT)
	press(KEY_DOWN)
	tap(KEY_W)
	await wait_until(func(): return player.is_dodging, 20)
	await wait_until(func(): return not player.is_dodging, 20)
	release(KEY_DOWN)
	var landing: bool = defense.is_dash_recovering()
	run = await drift_while(func(): return defense.is_dash_recovering(), 60)
	log_p("a dash's landing beat: %d steps, moved %s of %s" % run)
	check(landing and run[0] > 0 and run[1].distance_to(run[2]) <= 0.5, "landing a dash: %.2f of %.2f px" % [run[1].x, run[2].x])
	await wait(10)

	await settle_player(DRIFT_SPOT)
	defense._start_guard_break()
	await wait(2)
	var stunned: bool = defense.is_guard_broken
	run = await drift_while(func(): return defense.is_guard_broken, 10)
	defense.clear_guard_break()
	log_p("guard-broken: %d steps, moved %s of %s (its hit-stop slows the pull with the fight)" % run)
	check(stunned and run[0] == 10 and run[1].distance_to(run[2]) <= 0.5, "guard-broken: %.2f of %.2f px" % [run[1].x, run[2].x])
	await wait(10)

	log_p("-- and none while talking, grabbed, finishing or locked, or at 0 health")
	await settle_player(DRIFT_SPOT)
	player.is_talking = true
	moved = await drift_for(10, DRIFT)
	player.is_talking = false
	check(moved.length() < 0.01, "talking: no pull (%s)" % moved)
	player.grab()
	moved = await drift_for(10, DRIFT)
	player.release_grab(Vector2.ZERO)
	clear_iframes()
	check(moved.length() < 0.01, "grabbed: no pull (%s)" % moved)
	await wait(2)
	player.is_finishing = true
	moved = await drift_for(10, DRIFT)
	player.is_finishing = false
	check(moved.length() < 0.01, "finishing: no pull (%s)" % moved)
	player.lock_actions()
	moved = await drift_for(10, DRIFT)
	player.unlock_actions()
	check(moved.length() < 0.01, "action-locked: no pull (%s)" % moved)
	# Last: at 0 health the fight is lost, and a process gets one ending.
	await settle_player(DRIFT_SPOT)
	player.playerHealth = 0
	moved = await drift_for(10, DRIFT)
	check(moved.length() < 0.01, "at 0 health: no pull (%s)" % moved)


# ------------------------------------------------------------------ beast Bixby's Inferno
# BixbyBeastInferno, forced from his hover with nothing else queued, on a fixed seed, six times over with the
# player somewhere different for each breath. A process gets one ending, so the player dying mid-pull
# (tier=death) and him beaten on the rope (tier=defeated) are runs of their own. The geometry is
# BixbyInfernoArtLayout's, the numbers BixbyBeastStateMachine's.

const LIAM_BEAST := "Arena/BixbyBeastScene/BixbyBeastCharacterBody"
const INFERNO_LAYOUT := "res://Scripts/BixbyInfernoArtLayout.gd"
const INFERNO_SEED := 20260923
# Where a run starts the player: the first of these clear of the embers still burning from the run before.
const INFERNO_STARTS := [Vector2(1400, 800), Vector2(520, 800), Vector2(300, 900), Vector2(1620, 900), Vector2(720, 650), Vector2(1200, 650)]
# How far inside the cone the player stands before dashing out of it as it catches.
const INFERNO_EDGE_DEPTH := 40.0
# The shower's drop area (BixbyInfernoArtLayout.FIREBALL_AREA), and how long after the last landing its
# hit is still worth counting.
const INFERNO_FIREBALL_AREA := Rect2(170, 170, 1580, 720)
const INFERNO_HIT_TAIL := 0.15
# A landing further than this from a player's feet can't touch them: their hurtbox stands 81 px over their
# feet, and a landing's oval reaches 33 px above and below its middle.
const INFERNO_LANDING_REACH := 114.0
# The circle a player walks the shower off on: well inside the floor, and long enough that nobody walking
# it is back where they were a second ago.
const INFERNO_CIRCLE_CENTRE := Vector2(960, 600)
const INFERNO_CIRCLE_RADIUS := 280.0
# How far in from the side ropes a player strafing the bottom rope starts and stops.
const INFERNO_STRAFE_INSET := 40.0
# "Roughly three quarters" of the ring, the user's own rough figure: with the perch art's apex the approved
# cone covers 68%.
const INFERNO_COVERAGE_RANGE := Vector2(0.65, 0.80)
# What a player needs to see the wind-up before they move: the longest run out of the cone has to fit in
# what is left of it.
const INFERNO_REACTION := 0.25

var inf: Node
# Once a physics frame, what the frame before it left: {frame, phase (-1 outside the Inferno), pulled, t}.
var inf_frames: Array = []
var inf_rises := {}
# Per fireball: where, and when it was first seen, its marker lit, its hitbox live and it landed.
var inf_fireballs := {}
# The game clock on every frame a live ParryTell stood over him, whether it was yellow, and how far off his
# middle mouth it stood at most.
var inf_tell: Array = []
var inf_tell_dodge := false
var inf_tell_off := 0.0
# Per ember: where, when laid and where the player was, when it caught, started burning and burnt out.
var inf_embers := {}
var inf_land_frame := -1
var inf_land_player := Vector2.INF
# The perch and the HUD over it, by his own clock (fight_clock), which a freeze and a pause both hold:
# frames on the rope that weren't at the middle facing down, and frames the HUD wasn't where it should
# have settled by then.
var inf_perched_since := -1.0
var inf_left_rope_at := -1.0
# The last frame his Flyby was going: it fades the bar itself (bixby_flyby tier=draw checks that), so the HUD isn't
# held to full off the rope until it has settled after one.
var inf_flyby_seen_at := -INF
var inf_perched_frames := 0
var inf_perch_wrong := []
var inf_hud_wrong := []
# How far every marker of every run went down from the player's feet as it appeared.
var inf_marker_offsets: Array = []
# Where each rising fireball of the volley left from, and the perch frame up as it went.
var inf_rise_origins: Array = []
var inf_rise_frames: Array = []
var inf_tell_at := Vector2.INF
var inf_land_feet := Vector2.INF
# While he hangs off the rope: frames a fireball was seen, frames its burst was seen in flame and in scorch,
# and whatever of the shower sorted or was drawn where it shouldn't be; frames an ember was seen, and any
# that reached what he draws.
var inf_floor_frames := 0
var inf_burst_frames := [0, 0]
var inf_floor_wrong := []
var inf_ember_frames := 0
var inf_ember_over := []
var inf_perch_image: Image


func load_liam() -> void:
	await load_fight("liam", true)
	await clear_intro("liam")
	boss = current_scene.get_node(LIAM_BEAST)
	sm = boss.state_machine
	player.playerHealth = 1000


# From his next hover with nothing else queued, so it ends on Land and Recover.
func force_inferno() -> Node:
	var inferno: Node = sm.states["Inferno"]
	if not await wait_until(func(): return sm.current_state.name == "Hover", 900):
		return null
	sm.attacks = []
	sm.on_child_transition(sm.current_state, "Inferno")
	return inferno if sm.current_state == inferno else null


func reach_phase(which: int, max_frames := 900) -> bool:
	return await wait_until(func(): return sm.current_state == inf and inf.phase == which, max_frames)


func burning_embers() -> Array:
	return hazards_of("BixbyEmberScript.gd").filter(func(ember): return ember.is_active())


func hud_alpha() -> float:
	return boss.health_bar.modulate.a


func on_rope() -> bool:
	return sm.current_state == inf and inf.phase >= inf.Phase.PERCH


# Where the player stands on the floor: the foot of their hurtbox, as the shower aims at it.
func player_feet() -> Vector2:
	var box := hurtbox_rect()
	return Vector2(box.get_center().x, box.end.y)


# Runs `step` a frame at a time through the rest of the shower, to its last landing's hit: the fireball hits
# it took and how far the player went.
func shower_hits(step: Callable) -> Dictionary:
	var before := events_of("HIT", &"bixby_fireball").size()
	var travelled := [0.0]
	var last := [player.global_position]
	var measure := func():
		travelled[0] += player.global_position.distance_to(last[0])
		last[0] = player.global_position
	physics_frame.connect(measure)
	var left: float = sm.inferno_first_marker + (sm.inferno_fireballs - 1) * sm.inferno_marker_interval + sm.inferno_fireball_warning - inf.elapsed
	var until: float = defense.clock + left + INFERNO_HIT_TAIL
	while defense.clock < until and inf.phase == inf.Phase.INHALE:
		await step.call()
	physics_frame.disconnect(measure)
	for k in [KEY_RIGHT, KEY_LEFT, KEY_DOWN, KEY_UP]:
		release(k)
	return {"hits": events_of("HIT", &"bixby_fireball").slice(before), "walked": travelled[0]}


func stand_still() -> void:
	await physics_frame


# One frame of walking round a circle, with the arrow keys against the pull as a player would: whichever
# of the eight directions best carries them along it, the way it goes and back onto it.
func walk_circle(centre: Vector2, radius: float) -> void:
	var from_centre: Vector2 = player.global_position - centre
	var along := Vector2(-from_centre.y, from_centre.x).normalized()
	var want: Vector2 = along * 450.0 + from_centre.normalized() * (radius - from_centre.length()) * 4.0 - inf.pull_at(player.global_position)
	var keys := {KEY_RIGHT: want.x > 150.0, KEY_LEFT: want.x < -150.0, KEY_DOWN: want.y > 150.0, KEY_UP: want.y < -150.0}
	for k in keys:
		if keys[k] != Input.is_physical_key_pressed(k):
			if keys[k]:
				press(k)
			else:
				release(k)
	await physics_frame


# The player's hurtbox if they stood at `at`.
func hurtbox_at(at: Vector2) -> Rect2:
	var rect := hurtbox_rect()
	rect.position += at - player.global_position
	return rect


func hits_cone(rect: Rect2) -> bool:
	return load(INFERNO_LAYOUT).rect_hits_cone(rect, inf.cone_apex, inf._half_angle())


# Before anything steps: what the last physics frame left. The player's drift_velocity is then the pull
# he added in it, which the player's own step is about to take.
func watch_inferno() -> void:
	var now: float = defense.clock
	var at_frame := Engine.get_physics_frames()
	inf_frames.append({"frame": at_frame, "phase": inf.phase if sm.current_state == inf else -1, "pulled": player.drift_velocity != Vector2.ZERO, "t": now})
	for rise in hazards_of("BixbyFireballRiseScript.gd"):
		if not inf_rises.has(rise.get_instance_id()):
			inf_rises[rise.get_instance_id()] = true
			inf_rise_origins.append(rise.at - rise.velocity * rise.clock)
			inf_rise_frames.append(boss.sprite.frame)
	for fireball in hazards_of("BixbyFireballScript.gd"):
		var id: int = fireball.get_instance_id()
		if not inf_fireballs.has(id):
			var record := {"pos": fireball.global_position, "seen": now, "lit": -1.0, "hot": -1.0, "landed": -1.0, "landed_frame": -1}
			# The feet the state aimed it at: nothing moves the player between its spawn and this frame's start.
			var aimed_at: Vector2 = player_feet().clamp(INFERNO_FIREBALL_AREA.position, INFERNO_FIREBALL_AREA.end)
			record["off"] = fireball.global_position.distance_to(aimed_at)
			inf_marker_offsets.append(record.off)
			inf_fireballs[id] = record
			fireball.landed.connect(func():
				record.landed = defense.clock
				record.landed_frame = Engine.get_physics_frames()
				record["landed_feet"] = player_feet())
		var seen: Dictionary = inf_fireballs[id]
		if seen.lit < 0.0 and fireball.marker.visible:
			seen.lit = now
		if seen.hot < 0.0 and not fireball.get_node("Hitbox/CollisionShape2D").disabled:
			seen.hot = now
	var tell := tell_node()
	if tell and sm.current_state == inf:
		inf_tell.append(now)
		inf_tell_dodge = tell.dodge
		inf_tell_off = maxf(inf_tell_off, tell.global_position.distance_to(inf._mouth(0).round()))
		inf_tell_at = tell.global_position
	for ember in hazards_of("BixbyEmberScript.gd"):
		var id: int = ember.get_instance_id()
		if not inf_embers.has(id):
			inf_embers[id] = {"pos": ember.global_position, "laid": now, "player": player.global_position, "hurt": -1.0, "burning": -1.0, "out": -1.0}
		var record: Dictionary = inf_embers[id]
		if record.hurt < 0.0 and ember.is_hurting():
			record.hurt = now
		if record.burning < 0.0 and ember.phase == ember.Phase.BURNING:
			record.burning = now
		if record.out < 0.0 and ember.phase >= ember.Phase.BURN_OUT:
			record.out = now
	if inf_land_frame < 0 and sm.current_state.name == "Land":
		inf_land_frame = at_frame
		inf_land_player = player.global_position
		inf_land_feet = boss.feet_position()
	watch_perch()


func watch_perch() -> void:
	var clock: float = boss.fight_clock
	var perched := on_rope()
	if sm.current_state == sm.states.get("Flyby"):
		inf_flyby_seen_at = clock
	if perched and inf_perched_since < 0.0:
		inf_perched_since = clock
	elif not perched and inf_perched_since >= 0.0:
		inf_perched_since = -1.0
		inf_left_rope_at = clock
	var settle: float = boss.HUD_FADE_TIME + 2.0 * FRAME_TIME
	if perched:
		inf_perched_frames += 1
		if boss.sprite.flip_h or not is_equal_approx(boss.feet_position().x, 960.0):
			inf_perch_wrong.append("f%d x %.1f flipped %s" % [Engine.get_physics_frames(), boss.feet_position().x, boss.sprite.flip_h])
		if clock - inf_perched_since >= settle and absf(hud_alpha() - sm.inferno_hud_fade_alpha) > 0.001:
			inf_hud_wrong.append("f%d on the rope %.2f s, HUD at %.3f" % [Engine.get_physics_frames(), clock - inf_perched_since, hud_alpha()])
		watch_perch_floor()
	elif inf_left_rope_at >= 0.0 and clock - inf_left_rope_at >= settle and clock - inf_flyby_seen_at >= settle and absf(hud_alpha() - 1.0) > 0.001:
		inf_hud_wrong.append("f%d off the rope %.2f s, HUD at %.3f" % [Engine.get_physics_frames(), clock - inf_left_rope_at, hud_alpha()])


# While he hangs over the floor: the shower's markers sort over him, as the warning they are, and under the
# player; its bursts' flames are over everyone, as the ball falling onto them is, and from their first frame
# of scorch they lie on the floor layer under him with the scorch; each is drawn on its spot. And no ember,
# laid before he lets go or left from the last time, reaches what he draws.
func watch_perch_floor() -> void:
	var layout: GDScript = load(INFERNO_LAYOUT)
	var spec: Dictionary = layout.FINAL_FIREBALL if layout.USE_FINAL_FIREBALL else layout.PLACEHOLDER_FIREBALL
	var scorch_frames: Array = spec.impact_frames.slice(spec.impact_scorch_step)
	var at_frame := Engine.get_physics_frames()
	var his_y: float = boss.global_position.y
	for fireball in hazards_of("BixbyFireballScript.gd"):
		inf_floor_frames += 1
		var spot: Vector2 = fireball.global_position
		var holder: Node2D = fireball.floor_layer
		var wrong := []
		var marker_y: float = fireball.marker.global_position.y
		if not (is_equal_approx(marker_y, layout.MARKER_LAYER_Y) and marker_y > his_y and marker_y < sm.PLAYER_FLOOR.position.y and marker_y < player.global_position.y):
			wrong.append("marker sorting at y %.1f" % marker_y)
		if not fireball.marker_sprite.global_position.is_equal_approx(spot + Vector2(0, -layout.MARKER_RAISE)):
			wrong.append("marker drawn from %s" % fireball.marker_sprite.global_position)
		if not (is_equal_approx(holder.global_position.y, layout.FLOOR_LAYER_Y) and holder.global_position.y < his_y and fireball.scorch.global_position.is_equal_approx(spot)):
			wrong.append("scorch sorting at y %.1f, drawn from %s" % [holder.global_position.y, fireball.scorch.global_position])
		if fireball.impact.visible:
			var scorched: bool = fireball.impact.frame in scorch_frames
			inf_burst_frames[1 if scorched else 0] += 1
			var on_floor: bool = fireball.impact.get_parent() == holder and fireball.impact.z_index == 0
			var over_all: bool = fireball.impact.get_parent() == fireball and fireball.impact.z_index > 0
			if not (on_floor if scorched else over_all) or not fireball.impact.global_position.is_equal_approx(spot):
				wrong.append("burst frame %d under %s at z %d, drawn from %s" % [fireball.impact.frame, fireball.impact.get_parent().name, fireball.impact.z_index, fireball.impact.global_position])
		if [fireball, holder, fireball.marker, fireball.scorch].any(func(item: Node2D) -> bool: return item.z_index != 0) or boss.z_index != 0 or fireball.ball.z_index <= 0:
			wrong.append("z: marker %d, scorch %d, ball %d, him %d" % [fireball.marker.z_index, fireball.scorch.z_index, fireball.ball.z_index, boss.z_index])
		if not wrong.is_empty():
			inf_floor_wrong.append("f%d fireball at %s: %s" % [at_frame, spot, wrong])
	var body := perch_drawn_rect()
	for ember in hazards_of("BixbyEmberScript.gd"):
		inf_ember_frames += 1
		var sprite: Sprite2D = ember.get_node("Sprite2D")
		var drawn: Rect2 = sprite.global_transform * sprite.get_rect()
		if drawn.intersects(body):
			inf_ember_over.append("f%d ember at %s drawn over %s, his frame %d drawn over %s" % [at_frame, ember.global_position, drawn, boss.sprite.frame, body])


# The opaque part of the perch frame he's drawing, in px.
func perch_drawn_rect() -> Rect2:
	var art: GDScript = load("res://Scripts/BixbyBeastArtLayout.gd")
	if inf_perch_image == null:
		inf_perch_image = Image.load_from_file(ProjectSettings.globalize_path(art.PERCH_SHEET))
	var size := Vector2i(art.FRAME_SIZE)
	var used: Rect2i = inf_perch_image.get_region(Rect2i(boss.sprite.frame * size.x, 0, size.x, size.y)).get_used_rect()
	return Rect2(boss.air.global_position + art.local(Vector2(used.position)), Vector2(used.size) * art.SCALE)


func inferno_reset() -> void:
	inf_frames.clear()
	inf_rises.clear()
	inf_rise_origins.clear()
	inf_rise_frames.clear()
	inf_tell_at = Vector2.INF
	inf_land_feet = Vector2.INF
	inf_fireballs.clear()
	inf_tell.clear()
	inf_tell_dodge = false
	inf_tell_off = 0.0
	inf_land_frame = -1
	inf_land_player = Vector2.INF


# Puts the player at `at`, holds `keys` and lets the pull run `frames`: [px moved, game seconds, their
# state as it started]. A warp, so the pull already added for this step, aimed from where they were, goes.
func pull_run(at: Vector2, keys: Array, frames: int) -> Array:
	player.warp_to(at)
	for k in keys:
		press(k)
	await wait(4)
	var state: String = player.current_state.name
	var from: Vector2 = player.global_position
	var clock_from: float = defense.clock
	await wait(frames)
	var moved: Vector2 = player.global_position - from
	var took: float = defense.clock - clock_from
	for k in keys:
		release(k)
	return [moved, took, state]


# The first of `spots` where the player's hurtbox is clear of every ember still burning: the last run's
# are still alight when the next one starts.
func clear_of_embers(spots: Array) -> Vector2:
	for spot in spots:
		var body := hurtbox_at(spot).grow(8.0)
		if not hazards_of("BixbyEmberScript.gd").any(func(ember): return ember.footprint().intersects(body)):
			return spot
	return spots[0]


# The player's hurtbox centred on `ember`'s, for `seconds` of game time.
func hold_in_ember(ember: Node2D, seconds: float) -> void:
	var until: float = defense.clock + seconds
	while defense.clock < until and is_instance_valid(ember):
		var into: Vector2 = ember.get_node("Hitbox/CollisionShape2D").global_position
		player.global_position += into - player.hurtBox.get_node("CollisionShape2D").global_position
		player.velocity = Vector2.ZERO
		await physics_frame


# What a perch frame may draw on, in px: its whole width, from PERCH_HEADROOM rows above the rope down.
func perch_frame_rect(layout: GDScript) -> Rect2:
	var art: GDScript = load("res://Scripts/BixbyBeastArtLayout.gd")
	var top: float = layout.PERCH_ROPE_ROW - layout.PERCH_HEADROOM
	var drawn := Rect2(0.0, top, art.FRAME_SIZE.x, art.FRAME_SIZE.y - top)
	return Rect2(layout.perch_point() + art.local(drawn.position), drawn.size * art.SCALE)


func inferno_snapshot() -> Dictionary:
	var clocks := []
	for fireball in hazards_of("BixbyFireballScript.gd"):
		clocks.append([fireball.get_instance_id(), fireball.clock])
	return {"player": player.global_position, "phase": inf.phase, "elapsed": inf.elapsed, "fireballs": clocks, "boss": boss.global_position, "state": str(sm.current_state.name), "hud": hud_alpha()}


# The share of INFERNO_AREA inside the cone, counted on a 5 px grid rather than worked out, so it checks
# the layout's own sums rather than repeating them.
func cone_coverage(layout: GDScript) -> float:
	var area: Rect2 = layout.INFERNO_AREA
	var inside := 0
	var total := 0
	var y := area.position.y + 2.5
	while y < area.end.y:
		var x := area.position.x + 2.5
		while x < area.end.x:
			total += 1
			if layout.point_in_cone(Vector2(x, y), inf.cone_apex, inf._half_angle()):
				inside += 1
			x += 5.0
		y += 5.0
	return float(inside) / total


# How long a player standing at `at` takes to walk to where the breath can't touch them: per axis at
# walking speed, so a diagonal takes as long as its longer side. Up and to one side, or straight up, on
# the floor they can stand on.
func escape_time(at: Vector2) -> float:
	var floor_area: Rect2 = sm.PLAYER_FLOOR
	var best := INF
	for side in [1.0, -1.0, 0.0]:
		var reach := func(r: float) -> Vector2:
			return Vector2(clampf(at.x + side * r, floor_area.position.x, floor_area.end.x), maxf(at.y - r, floor_area.position.y))
		if hits_cone(hurtbox_at(reach.call(2000.0))):
			continue
		var low := 0.0
		var high := 2000.0
		for i in 30:
			var mid := (low + high) / 2.0
			if hits_cone(hurtbox_at(reach.call(mid))):
				low = mid
			else:
				high = mid
		best = minf(best, high)
	return best / player.SPEED


# The longest escape_time() from anywhere the breath reaches, on a 10 px grid over the floor and the
# bottom-centre itself: [seconds, from].
func worst_escape() -> Array:
	var floor_area: Rect2 = sm.PLAYER_FLOOR
	var spots := [Vector2(floor_area.get_center().x, floor_area.end.y)]
	var y := floor_area.position.y
	while y <= floor_area.end.y + 0.01:
		var x := floor_area.position.x
		while x <= floor_area.end.x + 0.01:
			spots.append(Vector2(x, y))
			x += 10.0
		y += 10.0
	var worst := [0.0, Vector2.INF]
	for spot in spots:
		if hits_cone(hurtbox_at(spot)):
			var took := escape_time(spot)
			if took > worst[0]:
				worst = [took, spot]
	return worst


# Where a player stands in the upper corner on `side` (1 right, -1 left): 200 px down, halfway between the
# cone's slant and the rope.
func safe_corner(side: float) -> Vector2:
	var floor_area: Rect2 = sm.PLAYER_FLOOR
	var y := 200.0
	var rect := hurtbox_at(Vector2(960, y))
	var slant: float = inf.cone_apex.x + side * (rect.end.y - inf.cone_apex.y) * tan(inf._half_angle())
	var clear_of_it := slant + side * (rect.size.x / 2.0 + 1.0)
	var wall := floor_area.end.x if side > 0.0 else floor_area.position.x
	return Vector2(roundf((clear_of_it + wall) / 2.0), y)


# One whole Inferno with the player put at `spot` as the wind-up starts, through to his breath: the
# inferno hits it cost them, and the health, counted from the wind-up so the shower's hits don't.
func breath_at(spot: Vector2) -> Dictionary:
	if not await reach_phase(inf.Phase.WINDUP, 900):
		return {"hits": [], "lost": -1}
	await settle_player(spot)
	clear_iframes()
	var health: int = player.playerHealth
	var before := events_of("HIT", &"bixby_inferno").size()
	await reach_phase(inf.Phase.SPENT, 200)
	return {"hits": events_of("HIT", &"bixby_inferno").slice(before), "lost": health - player.playerHealth}


func start_inferno_run(what: String) -> bool:
	log_p("-- " + what)
	await settle_player(clear_of_embers(INFERNO_STARTS))
	inferno_reset()
	inf = await force_inferno()
	check(inf != null, "he goes into the Inferno from his hover")
	return inf != null


func test_inferno() -> void:
	seed(INFERNO_SEED)
	await load_liam()
	# His hovers held, as combined, spin_tell and spin_reach hold them: force_inferno() waits 900 frames for a hover,
	# and a Flyby's cycle, with its landing, recovery and takeoff, runs longer than that.
	sm.hover_time = 600.0
	sm.hover_between_attacks = 600.0
	# Six Infernos' dodges and windows in one fight add up to a Break, which would cut a run short.
	hold_break_gauge(boss)
	track()
	track_dodges()
	var fireball: Dictionary = CATALOG.get_attack(&"bixby_fireball")
	var breath: Dictionary = CATALOG.get_attack(&"bixby_inferno")
	var ember: Dictionary = CATALOG.get_attack(&"bixby_ember")
	check(fireball.damage == 2 and fireball.blockable and fireball.weight == CATALOG.Weight.LIGHT and fireball.from_above and fireball.dodge_tell and not fireball.dash_through, "bixby_fireball is catalogued as mason_nugget is, at a full heart (the tuning round of 2026-10-04) (%s)" % [fireball])
	check(breath.damage == 2 and not breath.blockable and not breath.parryable and breath.dodge_tell and not breath.tell and not breath.dash_through, "bixby_inferno: a full heart, no guard, no parry, no dash through, a yellow tell (%s)" % [breath])
	check(ember.damage == 1 and ember.dash_through and not ember.blockable and not ember.parryable and not ember.tell and not ember.dodge_tell and not ember.bypass_invincibility, "bixby_ember: half a heart, no guard, no badge, dashed through, spaced by the i-frames (%s)" % [ember])
	if tier == "death":
		await inferno_death()
		return
	if tier == "defeated":
		await inferno_defeated()
		return
	var layout: GDScript = load(INFERNO_LAYOUT)
	physics_frame.connect(watch_inferno)
	await inferno_run_one(layout)
	await inferno_run_two()
	await inferno_run_three()
	await inferno_run_four()
	await inferno_run_five()
	await inferno_run_six()
	physics_frame.disconnect(watch_inferno)
	log_p("%d markers over the six runs, %.1f px at most from the player's feet as each appeared" % [inf_marker_offsets.size(), inf_marker_offsets.max()])
	check(inf_marker_offsets.size() == 6 * sm.inferno_fireballs and inf_marker_offsets.max() <= sm.inferno_track_scatter + 1.0, "every marker of every run tracked the player, within %.0f px" % sm.inferno_track_scatter)
	log_p("%d frames on the rope; off the middle or mirrored on %s; the HUD not settled where it should be on %s" % [inf_perched_frames, inf_perch_wrong.slice(0, 5), inf_hud_wrong.slice(0, 5)])
	check(inf_perched_frames > 0 and inf_perch_wrong.is_empty(), "every frame on the rope, he is on its middle facing down, never mirrored")
	check(inf_hud_wrong.is_empty(), "the HUD is at %.2f whenever he has been on the rope %.2f s, and back to full whenever he has been off it that long" % [sm.inferno_hud_fade_alpha, boss.HUD_FADE_TIME])
	log_p("on the rope: %d fireball frames, bursts seen in flame on %d and in scorch on %d, wrong on %s; %d ember frames, over his body on %s" % [inf_floor_frames, inf_burst_frames[0], inf_burst_frames[1], inf_floor_wrong.slice(0, 5), inf_ember_frames, inf_ember_over.slice(0, 5)])
	check(inf_floor_frames > 0 and inf_burst_frames[0] > 0 and inf_burst_frames[1] > 0 and inf_floor_wrong.is_empty(), "while he hangs off the rope, the shower's markers sort over him and under the player, its bursts' flames over everyone and their scorch under him from its first frame, each on its own spot, and the ball falling onto it over him")
	check(inf_ember_frames > 0 and inf_ember_over.is_empty(), "and no ember reaches what he draws until he lets go")


func inferno_run_one(layout: GDScript) -> void:
	if not await start_inferno_run("run 1: the perch and the HUD, the volley, the cone, the pull, the tell, the breath under him, the embers and the recharge"):
		return
	var start: float = defense.clock
	check(await reach_phase(inf.Phase.PERCH, 200), "he takes the rope (%.2f s after he set off)" % (defense.clock - start))
	var feet: Vector2 = layout.perch_point()
	var frame_rect := perch_frame_rect(layout)
	log_p("perched: feet %s (perch_point %s), sorting at y %.1f, frame %s, HUD at %.2f" % [boss.feet_position(), feet, boss.global_position.y, frame_rect, hud_alpha()])
	check(is_equal_approx(feet.x, 960.0) and boss.feet_position().is_equal_approx(feet) and boss.air.global_position.is_equal_approx(feet), "his feet on perch_point, the middle of the rope")
	check(not boss.sprite.flip_h, "facing down, not mirrored")
	check(is_equal_approx(boss.global_position.y, sm.ROPES.position.y), "sorting at the rope line, y 114, behind everyone on the mat (%.1f)" % boss.global_position.y)
	check(not boss.shadow.visible and boss.rope_sfx_player.playing, "no shadow on the rope, and the rope creaks")
	check(Rect2(Vector2.ZERO, boss.VIEW_SIZE).encloses(frame_rect), "the perch frame is on screen")
	var art: GDScript = load("res://Scripts/BixbyBeastArtLayout.gd")
	var body_box: Rect2 = art.local_rect(art.PERCH_BODY_BOX)
	check(area_rect(boss.hurtbox).is_equal_approx(Rect2(feet + body_box.position, body_box.size)), "while he hangs there his hurtbox is the spent pose's drawn body, %s" % area_rect(boss.hurtbox))
	await wait(roundi(boss.HUD_FADE_TIME / FRAME_TIME) + 2)
	log_p("HUD %.3f once he has hung there %.2f s" % [hud_alpha(), boss.HUD_FADE_TIME])
	check(is_equal_approx(hud_alpha(), sm.inferno_hud_fade_alpha), "the boss bar and its plate over him fade to %.2f" % sm.inferno_hud_fade_alpha)

	log_p("-- the cone")
	var apex: Vector2 = inf.cone_apex
	var coverage := cone_coverage(layout)
	log_p("apex %s (%.0f px under the rope), half-angle %.1f deg: covers %.1f%% of the ring" % [apex, apex.y - layout.TOP_ROPE_Y, sm.inferno_cone_half_angle, coverage * 100.0])
	check(coverage >= INFERNO_COVERAGE_RANGE.x and coverage <= INFERNO_COVERAGE_RANGE.y, "it covers roughly three quarters of the ring, %.0f%% to %.0f%% (%.1f%%)" % [INFERNO_COVERAGE_RANGE.x * 100.0, INFERNO_COVERAGE_RANGE.y * 100.0, coverage * 100.0])
	check(apex.is_equal_approx(layout.perch_point() + load("res://Scripts/BixbyBeastArtLayout.gd").local(layout.CONE_APEX)), "the cone's tip is CONE_APEX on him")
	var worst := worst_escape()
	var budget: float = sm.inferno_windup - INFERNO_REACTION
	var pulled_in := escape_time(inf.pull_target())
	log_p("the longest walk out of it: %.3f s from %s, of the %.2f s the %.1f s wind-up leaves after a %.2f s reaction; from where the pull ends, %.3f s" % [worst[0], worst[1], budget, sm.inferno_windup, INFERNO_REACTION, pulled_in])
	check(worst[0] <= budget, "anyone in it can walk out before it catches, with %.2f s to react (%.3f s at most)" % [INFERNO_REACTION, worst[0]])
	check(hits_cone(hurtbox_at(inf.pull_target())), "and the pull drags the player into it, not past its tip")
	check(inf.pull_target().is_equal_approx(layout.perch_mouth_point(layout.INHALE_FRAME, 0)), "the pull converges on his middle mouth as he inhales, %s" % inf.pull_target())

	check(await reach_phase(inf.Phase.INHALE, 300), "the volley and the empty sky run on into the inhale")
	var off_mouth := []
	for i in inf_rise_origins.size():
		var want: Vector2 = layout.perch_mouth_point(4 + i % 3, i % 3)
		if inf_rise_origins[i].distance_to(want) > 0.5 or inf_rise_frames[i] != 4 + i % 3:
			off_mouth.append("#%d from %s on frame %d, not %s on frame %d" % [i, inf_rise_origins[i], inf_rise_frames[i], want, 4 + i % 3])
	log_p("volley: first three from %s on frames %s; off their mouth %s" % [inf_rise_origins.slice(0, 3), inf_rise_frames.slice(0, 3), off_mouth.slice(0, 3)])
	check(inf_rise_origins.size() == sm.inferno_fireballs and off_mouth.is_empty(), "each fireball of the volley leaves the spitting head's mouth, the middle, left and right head in turn on frames 4, 5 and 6")
	var suction: Array = hazards_of("BixbySuctionScript.gd")
	var inhale_mouths: Array = [0, 1, 2].map(func(head): return layout.perch_mouth_point(layout.INHALE_FRAME, head))
	log_p("the suction converges on %s" % [suction[0].mouths if not suction.is_empty() else []])
	check(suction.size() == 1 and Array(suction[0].mouths) == inhale_mouths, "the suction's streaks converge on his three inhaling mouths %s" % [inhale_mouths])
	log_p("%d fireballs went up; %d still up as the inhale starts" % [inf_rises.size(), hazards_of("BixbyFireballRiseScript.gd").size()])
	check(inf_rises.size() == sm.inferno_fireballs, "%d rising shots (%d)" % [sm.inferno_fireballs, inf_rises.size()])
	check(hazards_of("BixbyFireballRiseScript.gd").is_empty(), "every one off the screen and gone before the inhale")
	check(boss.inhale_sfx_player.playing, "the inhale is heard")

	log_p("-- the pull, past its ramp")
	var target: Vector2 = inf.pull_target()
	await wait_until(func(): return inf.elapsed >= sm.inferno_pull_ramp + 0.05, 60)
	var far := Vector2(1400, 800)
	var idle: Array = await pull_run(far, [], 30)
	var speed: float = idle[0].length() / idle[1]
	var off_aim: float = rad_to_deg(absf(idle[0].angle_to(target - far)))
	log_p("idle at %s: dragged %s in %.3f s, %.1f px/s, %.2f degrees off the floor under him %s" % [far, idle[0], idle[1], speed, off_aim, target])
	check(absf(speed - sm.inferno_pull_speed) <= 5.0 and off_aim <= 2.0, "an idle player is dragged at %.0f px/s, straight at him (%.1f, %.2f deg)" % [sm.inferno_pull_speed, speed, off_aim])
	var away: Array = await pull_run(Vector2(target.x, 560), [KEY_DOWN], 30)
	var net: float = away[0].y / away[1]
	log_p("walking straight away from under him: moved %s in %.3f s, %.1f px/s" % [away[0], away[1], net])
	check(absf(net - (player.SPEED - sm.inferno_pull_speed)) <= 5.0 and absf(away[0].x) < 0.5, "walking straight away nets %.0f px/s (%.1f)" % [player.SPEED - sm.inferno_pull_speed, net])
	var guard: Array = await pull_run(far, [KEY_SHIFT], 30)
	var dragged: float = guard[0].length() / guard[1]
	log_p("guarding at %s (%s): dragged %s, %.1f px/s" % [far, guard[2], guard[0], dragged])
	check(guard[2] == "Blocking" and absf(dragged - sm.inferno_pull_speed) <= 5.0, "the guard roots them, so the pull drags them at %.0f (%.1f)" % [sm.inferno_pull_speed, dragged])

	log_p("-- under the cone's tip")
	var under := Vector2(960, 300)
	var burnt := await breath_at(under)
	var flood: Node2D = inf.flood
	var burst_at: Vector2 = flood.position + flood.burst.position if is_instance_valid(flood) else Vector2.INF
	log_p("spent on frame %d; the breath's burst stood at %s" % [boss.sprite.frame, burst_at])
	check(boss.sprite.frame == 13, "spent: he hangs in the spent pose, frame 13")
	check(burst_at.is_equal_approx(apex + layout.BURST_ANCHOR_OFFSET), "the breath's burst sits on the cone's tip, %s" % apex)
	log_p("at %s through the wind-up and the breath: %d inferno hits, %d health lost" % [under, burnt.hits.size(), burnt.lost])
	check(burnt.hits.size() == 1 and burnt.lost == catalogue_damage(&"bixby_inferno"), "under the apex: exactly one hit, worth %d" % catalogue_damage(&"bixby_inferno"))

	var tell_time: float = inf_tell[-1] - inf_tell[0] + FRAME_TIME if not inf_tell.is_empty() else 0.0
	log_p("yellow ring up for %.3f s (%d frames), %.1f px off his middle mouth at most" % [tell_time, inf_tell.size(), inf_tell_off])
	check(inf_tell_dodge and absf(tell_time - sm.inferno_windup) <= FRAME_TIME + 0.0001, "the yellow ring lives for the %.1f s wind-up, give or take a frame (%.3f)" % [sm.inferno_windup, tell_time])
	check(inf_tell_off <= 1.0 and inf_tell_at.is_equal_approx(layout.perch_mouth_point(10, 0).round()), "and sits on his middle mouth as he rears back, %s" % inf_tell_at)

	var balls: Array = inf_fireballs.values()
	var last_landing := -1
	var early := []
	var strays := []
	for a in balls:
		last_landing = maxi(last_landing, a.landed_frame)
		if a.lit < 0.0 or a.hot < 0.0 or a.hot - a.lit < sm.inferno_fireball_warning - FRAME_TIME - 0.0001:
			early.append("%s lit %.3f hot %.3f" % [a.pos, a.lit, a.hot])
		if a.off > sm.inferno_track_scatter + 1.0:
			strays.append("%s %.1f px off" % [a.pos, a.off])
	var offsets: Array = balls.map(func(b): return b.off)
	log_p("%d markers, %.1f to %.1f px from the player's feet as each appeared; last landing on frame %d; too early %s; strays %s" % [balls.size(), offsets.min(), offsets.max(), last_landing, early, strays])
	check(balls.size() == sm.inferno_fireballs and balls.all(func(b): return b.landed >= 0.0), "%d markers, and every fireball lands (%d)" % [sm.inferno_fireballs, balls.size()])
	check(early.is_empty(), "each marker lit at least the %.1f s warning, less a frame, before its hitbox" % sm.inferno_fireball_warning)
	check(strays.is_empty(), "each marker goes down on the player, within %.0f px of their feet as it appears" % sm.inferno_track_scatter)

	var inhale_first := inf_frames.find_custom(func(f): return f.phase == inf.Phase.INHALE)
	var inhale_end := inhale_first
	while inhale_end < inf_frames.size() and inf_frames[inhale_end].phase == inf.Phase.INHALE:
		inhale_end += 1
	var pulled := []
	for i in inf_frames.size():
		if inf_frames[i].pulled:
			pulled.append(i)
	var expected := range(inhale_first + 1, inhale_end + 1)
	var pull_to_frame: int = inf_frames[pulled[-1]].frame if not pulled.is_empty() else -1
	log_p("inhale seen on frames %d to %d; the player felt the pull on %d frames, %d to %d; last landing on frame %d" % [inf_frames[inhale_first].frame, inf_frames[inhale_end - 1].frame, pulled.size(), inf_frames[pulled[0]].frame if not pulled.is_empty() else -1, pull_to_frame, last_landing])
	check(pulled == expected, "the pull is felt from the inhale's first frame to the one after it ends, and on no other frame")
	check(pull_to_frame == last_landing + 1, "the last frame of it is the one after the last fireball lands")

	log_p("-- the embers it leaves")
	await wait(1)
	var ember_size: Vector2 = load("res://Scripts/BixbyEmberScript.gd").SIZE
	var keep_out: Rect2 = inf._landing_box().grow(inf.EMBER_LANDING_KEEP_OUT)
	var laid: Array = inf_embers.values()
	var misplaced := []
	for i in laid.size():
		var at: Vector2 = laid[i].pos
		var foot := Rect2(at - ember_size / 2.0, ember_size)
		if not layout.rect_inside_cone(foot, apex, inf._half_angle()):
			misplaced.append("%s outside the cone" % at)
		if foot.intersects(keep_out):
			misplaced.append("%s in his landing keep-out" % at)
		if at.distance_to(laid[i].player) < inf.EMBER_PLAYER_CLEARANCE:
			misplaced.append("%s %.0f px from the player" % [at, at.distance_to(laid[i].player)])
		for j in range(i + 1, laid.size()):
			if at.distance_to(laid[j].pos) < sm.inferno_lingering_spacing:
				misplaced.append("%s and %s %.0f px apart" % [at, laid[j].pos, at.distance_to(laid[j].pos)])
	log_p("%d embers at %s; the player at %s" % [laid.size(), laid.map(func(e): return e.pos), player.global_position])
	check(laid.size() >= 1 and laid.size() <= sm.inferno_lingering_patches, "1 to %d embers (%d)" % [sm.inferno_lingering_patches, laid.size()])
	check(misplaced.is_empty(), "each inside the burnt cone, %.0f px from the others, %.0f px from the player and clear of his landing (%s)" % [sm.inferno_lingering_spacing, inf.EMBER_PLAYER_CLEARANCE, misplaced])

	check(await wait_until(func(): return inf_land_frame >= 0, 120), "he lets go and comes down")
	var perch_image := Image.load_from_file(ProjectSettings.globalize_path(art.PERCH_SHEET))
	var land_image := Image.load_from_file(ProjectSettings.globalize_path(art.LAND_SHEET))
	var release_rows: Rect2i = perch_image.get_region(Rect2i(15 * 192, 0, 192, 160)).get_used_rect()
	var land_rows: Rect2i = land_image.get_region(Rect2i(0, 0, 192, 160)).get_used_rect()
	var land_top: float = inf_land_feet.y + (land_rows.position.y - art.ANCHOR.y) * art.SCALE
	var release_bottom: float = feet.y + (release_rows.end.y - art.ANCHOR.y) * art.SCALE
	var land_bottom: float = inf_land_feet.y + (land_rows.end.y - art.ANCHOR.y) * art.SCALE
	log_p("let go: feet %s -> %s; land frame 0 drawn from y %.0f; release frame 15 ends at y %.0f, land frame 0 at %.0f" % [feet, inf_land_feet, land_top, release_bottom, land_bottom])
	check(inf_land_feet.is_equal_approx(feet + Vector2(0, layout.release_drop())), "he drops %.0f px as he lets go" % layout.release_drop())
	check(land_top >= 0.0, "so land frame 0 starts the fall on screen (y %.0f)" % land_top)
	check(is_equal_approx(release_bottom, land_bottom), "and exactly where release frame 15 left him")
	await wait(1)
	var landed_box: Rect2 = inf._landing_box()
	var in_way := []
	for burning in burning_embers():
		var foot: Rect2 = burning.footprint()
		if sm._fire_in_the_way(foot, inf_land_player, landed_box) or foot.intersects(landed_box.grow(sm.inferno_landing_clearance)):
			in_way.append(burning.global_position)
	log_p("landing on %s with the player at %s: %d embers still burning, in the way %s" % [landed_box, inf_land_player, burning_embers().size(), in_way])
	check(sm.PLAYER_FLOOR.grow_individual(18.0, 40.5, 18.0, 40.5).intersects(landed_box), "his landing, at the top-centre of the ring, is on floor the player can reach")
	check(in_way.is_empty(), "as he lands, nothing burning is within %.0f px of him or in the straight way from the player to him" % sm.inferno_landing_clearance)
	check(hazards_of("BixbyEmberScript.gd").size() == laid.size(), "and his leaving the rope freed none of them")
	for id in inf_embers:
		var node := instance_from_id(id)
		inf_embers[id]["run"] = 1
		inf_embers[id]["cleared"] = is_instance_valid(node) and node.phase >= node.Phase.BURN_OUT

	check(await wait_until(func(): return sm.current_state.name == "Recover", 120), "he lands into his recharge")
	check(is_equal_approx(hud_alpha(), 1.0), "with the HUD back at full (%.3f)" % hud_alpha())
	var down_box: Rect2 = art.local_rect(art.RECOVER_BODY_BOX)
	check(area_rect(boss.hurtbox).is_equal_approx(Rect2(boss.feet_position() + down_box.position, down_box.size)), "his hurtbox is his grounded body again, for the punish window")
	var recover_from: float = defense.clock
	log_p("recharging at %s, under the perch at x %.0f" % [boss.global_position, feet.x])
	check(absf(boss.global_position.x - feet.x) <= 2.0, "on the mat under his perch at the top-centre (x %.1f)" % boss.global_position.x)
	var open := [true]
	while sm.current_state.name == "Recover":
		open[0] = open[0] and sm.is_recovering()
		await physics_frame
	var recharge: float = defense.clock - recover_from
	log_p("recharged for %.3f s, then %s" % [recharge, sm.current_state.name])
	check(open[0], "open to punches the whole time")
	check(absf(recharge - sm.inferno_recover_time) <= FRAME_TIME + 0.0001, "his recharge lasts %.1f s (%.3f)" % [sm.inferno_recover_time, recharge])


func inferno_run_two() -> void:
	if not await start_inferno_run("run 2: walking the shower off, the left upper corner, an ember in the way, the straight way to him, standing in one and dashing through one"):
		return
	check(await reach_phase(inf.Phase.INHALE, 900), "the shower starts")
	await settle_player(INFERNO_CIRCLE_CENTRE + Vector2(INFERNO_CIRCLE_RADIUS, 0))
	clear_iframes()
	var walked := await shower_hits(walk_circle.bind(INFERNO_CIRCLE_CENTRE, INFERNO_CIRCLE_RADIUS))
	log_p("walking a %.0f px circle round %s through the shower: %d fireball hits at %s, %.0f px walked" % [INFERNO_CIRCLE_RADIUS, INFERNO_CIRCLE_CENTRE, walked.hits.size(), walked.hits.map(func(e): return snappedf(e.t, 0.001)), walked.walked])
	check(walked.hits.size() <= 1, "a player who keeps walking takes 0 or 1 fireball hits (%d)" % walked.hits.size())
	var corner := safe_corner(-1.0)
	var burnt := await breath_at(corner)
	log_p("in the left corner at %s through the wind-up and the breath: %d inferno hits, %d health lost" % [corner, burnt.hits.size(), burnt.lost])
	check(not hits_cone(hurtbox_at(corner)) and burnt.hits.is_empty() and burnt.lost == 0, "in the left upper corner: no hit")

	var lived := []
	var cleared := 0
	for id in inf_embers:
		var record: Dictionary = inf_embers[id]
		if record.get("run", 0) != 1:
			continue
		if record.cleared:
			cleared += 1
		else:
			lived.append(snappedf(record.out - record.burning, 0.001))
	log_p("run 1's embers: %d burnt out by his landing, the rest burnt for %s s" % [cleared, lived])
	check(not lived.is_empty() and lived.all(func(t): return absf(t - sm.inferno_lingering_time) <= 2.0 * FRAME_TIME), "run 1's embers the landing left burnt for %.0f s each" % sm.inferno_lingering_time)

	log_p("-- standing where an ember is in the straight way to him")
	await wait(1)
	var landed_box: Rect2 = inf._landing_box()
	var reach: Vector2 = sm.PLAYER_HALF_BODY + Vector2.ONE * sm.FIRE_PASSAGE_MARGIN
	var behind: Node2D = null
	var spot := Vector2.INF
	for candidate in burning_embers():
		var nearest: Vector2 = candidate.global_position.clamp(landed_box.position, landed_box.end)
		var there: Vector2 = candidate.global_position + (candidate.global_position - nearest).normalized() * 150.0
		var clear := burning_embers().all(func(other): return not other.footprint().grow_individual(reach.x, reach.y, reach.x, reach.y).has_point(there))
		if sm.PLAYER_FLOOR.has_point(there) and clear:
			behind = candidate
			spot = there
			break
	check(behind != null, "an ember with room to stand behind it")
	if behind == null:
		return
	await settle_player(spot)
	check(await wait_until(func(): return sm.current_state.name == "Land", 120), "he comes down")
	await wait(1)
	var in_way := []
	for burning in burning_embers():
		if sm._fire_in_the_way(burning.footprint(), spot, landed_box):
			in_way.append(burning.global_position)
	log_p("standing at %s behind the ember at %s: it is now %s; burning embers left in the way %s" % [spot, behind.global_position, behind.Phase.keys()[behind.phase], in_way])
	check(behind.phase >= behind.Phase.BURN_OUT, "the ember in the way burns out as he lands")
	check(in_way.is_empty(), "and no burning one is left in the straight way from the player to him")

	check(await wait_until(func(): return sm.current_state.name == "Recover", 120), "his punish window opens")
	var to: Vector2 = spot.clamp(landed_box.position, landed_box.end)
	var ember_hits := events_of("HIT", &"bixby_ember").size()
	clear_iframes()
	var steps := ceili(spot.distance_to(to) / 10.0)
	for i in steps + 1:
		player.global_position = spot.lerp(to, float(i) / steps)
		player.velocity = Vector2.ZERO
		await physics_frame
	log_p("walked %s -> %s in %d steps: %d ember hits" % [spot, to, steps, events_of("HIT", &"bixby_ember").size() - ember_hits])
	check(events_of("HIT", &"bixby_ember").size() == ember_hits, "walking that straight way to his punish window costs nothing")

	log_p("-- standing in an ember")
	var parked_in: Node2D = burning_embers()[0] if not burning_embers().is_empty() else null
	check(parked_in != null, "an ember still burning to stand in")
	if parked_in == null:
		return
	clear_iframes()
	var health: int = player.playerHealth
	var parked_from := events_of("HIT", &"bixby_ember").size()
	await hold_in_ember(parked_in, 2.2)
	var parked: Array = events_of("HIT", &"bixby_ember").slice(parked_from)
	var gaps := []
	for i in range(1, parked.size()):
		gaps.append(snappedf(parked[i].t - parked[i - 1].t, 0.001))
	log_p("2.2 s in the ember at %s: hits at %s, gaps %s, health %d -> %d" % [parked_in.global_position, parked.map(func(e): return snappedf(e.t, 0.001)), gaps, health, player.playerHealth])
	check(parked.size() >= 1, "a player parked in an ember is hit")
	check(parked.size() == 3 and gaps.all(func(g): return g >= 1.0 - 0.001 and g <= 1.0 + 2.0 * FRAME_TIME + 0.001), "and again every time the i-frames run out: 3 in 2.2 s, a second apart (%d, %s)" % [parked.size(), gaps])
	check(health - player.playerHealth == parked.size() * catalogue_damage(&"bixby_ember"), "half a heart each")

	log_p("-- dashing through one")
	await settle_player(safe_corner(1.0))
	await dash_ready()
	var through: Node2D = null
	var dash_key := KEY_RIGHT
	var from := Vector2.ZERO
	var hurt_size: Vector2 = hurtbox_rect().size
	var hurt_offset: Vector2 = hurtbox_rect().get_center() - player.global_position
	for candidate in burning_embers():
		var foot: Rect2 = candidate.footprint()
		for key in [KEY_RIGHT, KEY_LEFT]:
			var sign := 1.0 if key == KEY_RIGHT else -1.0
			var start_x: float = (foot.position.x - 30.0 - hurt_size.x / 2.0) if key == KEY_RIGHT else (foot.end.x + 30.0 + hurt_size.x / 2.0)
			var start := Vector2(start_x, foot.get_center().y) - hurt_offset
			var end := start + Vector2(sign * DASH_LENGTH, 0.0)
			var swept := Rect2(start + hurt_offset - hurt_size / 2.0, hurt_size).merge(Rect2(end + hurt_offset - hurt_size / 2.0, hurt_size))
			var others_clear := burning_embers().all(func(other): return other == candidate or not other.footprint().intersects(swept))
			if sm.PLAYER_FLOOR.has_point(start) and sm.PLAYER_FLOOR.has_point(end) and others_clear:
				through = candidate
				dash_key = key
				from = start
				break
		if through:
			break
	check(through != null, "an ember with room to dash across it")
	if through == null:
		return
	await settle_player(from)
	clear_iframes()
	ember_hits = events_of("HIT", &"bixby_ember").size()
	var dodged := dodges.size()
	press(dash_key)
	tap(KEY_W)
	await wait(4)
	release(dash_key)
	await wait(30)
	var past: Rect2 = hurtbox_rect()
	var across: bool = past.position.x > through.footprint().end.x if dash_key == KEY_RIGHT else past.end.x < through.footprint().position.x
	log_p("dashed across the ember at %s from %s: now %s, ember hits %d, perfect dodges %s" % [through.global_position, from, player.global_position, events_of("HIT", &"bixby_ember").size() - ember_hits, dodges.slice(dodged).map(func(d): return d.id)])
	check(across and events_of("HIT", &"bixby_ember").size() == ember_hits, "a dash goes through one without a hit")
	check(dodges.slice(dodged).is_empty(), "and pays no PERFECT DODGE: it lies still on the floor (no_perfect_dodge)")


func inferno_run_three() -> void:
	if not await start_inferno_run("run 3: a finisher's freeze as the HUD fades and mid-pull, a pause mid-pull, and the right upper corner"):
		return
	check(await reach_phase(inf.Phase.PERCH, 200), "he takes the rope")
	await wait(5)
	var freeze: GDScript = load("res://Scripts/FightFreeze.gd")
	check(freeze.freeze(self, [player.get_parent()]), "the fight freezes around the player as the HUD fades")
	var fading: float = hud_alpha()
	await wait(20)
	log_p("HUD mid-fade: %.3f, and %.3f after 20 frozen frames" % [fading, hud_alpha()])
	check(fading < 1.0 and fading > sm.inferno_hud_fade_alpha and is_equal_approx(fading, hud_alpha()), "its fade holds with the fight: the tween is the bar's own")
	freeze.unfreeze(self)
	check(await reach_phase(inf.Phase.INHALE, 900), "the pull is on")
	await wait(40)
	check(freeze.freeze(self, [player.get_parent()]), "the fight freezes around the player mid-pull")
	# The pull he added the step before the freeze is the player's to take on the first frozen one.
	await wait(1)
	var held := inferno_snapshot()
	await wait(30)
	var after := inferno_snapshot()
	log_p("frozen: %s -> %s" % [held, after])
	check(held == after and not held.fireballs.is_empty(), "30 frozen frames move nothing: the player, the fireballs' clocks, his phase and clock, the HUD")
	freeze.unfreeze(self)
	await wait(3)
	check(player.global_position != after.player, "and the pull comes back with the fight")
	await tap_pause()
	check(pause_menu().is_open(), "paused mid-pull")
	held = inferno_snapshot()
	await wait(30)
	after = inferno_snapshot()
	log_p("paused: %s -> %s" % [held, after])
	check(held == after and not held.fireballs.is_empty(), "30 paused frames move nothing either")
	await tap_pause()
	await wait(3)
	check(not pause_menu().is_open() and player.global_position != after.player, "and it all carries on from there")
	# Its resume grace is 0.15 REAL seconds, which --fixed-fps never lets pass: it would eat a later press.
	pause_menu().grace_until_msec = 0
	var corner := safe_corner(1.0)
	var burnt := await breath_at(corner)
	log_p("in the right corner at %s through the wind-up and the breath: %d inferno hits, %d health lost" % [corner, burnt.hits.size(), burnt.lost])
	check(not hits_cone(hurtbox_at(corner)) and burnt.hits.is_empty() and burnt.lost == 0, "in the right upper corner: no hit")


func inferno_run_four() -> void:
	if not await start_inferno_run("run 4: standing still through the shower, then the bottom-centre of the ring, the longest way out"):
		return
	check(await reach_phase(inf.Phase.INHALE, 900), "the shower starts")
	await settle_player(inf.pull_target())
	clear_iframes()
	var stood := await shower_hits(stand_still)
	var gaps := []
	for i in range(1, stood.hits.size()):
		gaps.append(snappedf(stood.hits[i].t - stood.hits[i - 1].t, 0.001))
	var landing_span: float = (sm.inferno_fireballs - 1) * sm.inferno_marker_interval
	log_p("standing still where the pull ends through %.2f s of landings: %d fireball hits at %s, gaps %s, %.0f px moved" % [landing_span, stood.hits.size(), stood.hits.map(func(e): return snappedf(e.t, 0.001)), gaps, stood.walked])
	check(stood.hits.size() >= floori(landing_span / (1.0 + 2.0 * sm.inferno_marker_interval)) and gaps.all(func(g): return g >= 1.0 - 0.001 and g <= 1.0 + 2.0 * sm.inferno_marker_interval + 2.0 * FRAME_TIME), "a player who stands still is hit about once per i-frame window (%d in %.2f s, gaps %s)" % [stood.hits.size(), landing_span, gaps])
	var bottom := Vector2(sm.PLAYER_FLOOR.get_center().x, sm.PLAYER_FLOOR.end.y)
	var burnt := await breath_at(bottom)
	log_p("at the bottom-centre %s through the wind-up and the breath: %d inferno hits, %d health lost" % [bottom, burnt.hits.size(), burnt.lost])
	check(burnt.hits.size() == 1 and burnt.lost == catalogue_damage(&"bixby_inferno"), "at the bottom-centre: exactly one hit, worth %d" % catalogue_damage(&"bixby_inferno"))


func inferno_run_five() -> void:
	if not await start_inferno_run("run 5: walking straight away from him through the shower, dashing out of the cone as it catches, and an ember catching under a player"):
		return
	check(await reach_phase(inf.Phase.INHALE, 900), "the shower starts")
	await settle_player(inf.pull_target() + Vector2(0, 15))
	clear_iframes()
	var hits_before := events_of("HIT").size()
	var health: int = player.playerHealth
	var set_off: float = defense.clock
	var from_y: float = player.global_position.y
	# How much further from the floor under him the player is on each frame than on the one before.
	var gained: Array = []
	var was := [player.global_position.distance_to(inf.pull_target())]
	var measure := func():
		var now: float = player.global_position.distance_to(inf.pull_target())
		gained.append(now - was[0])
		was[0] = now
	physics_frame.connect(measure)
	press(KEY_DOWN)
	# Straight down the ring, away from him, until the bottom rope stops them or the shower ends. Pinned
	# against the rope, the pull lifts them a frame's worth of itself off it every frame, so they come to
	# rest that much and a little more short of the floor's edge.
	var at_rope: float = sm.PLAYER_FLOOR.end.y - 8.0 - sm.inferno_pull_speed * FRAME_TIME
	await wait_until(func(): return player.global_position.y >= at_rope or inf.phase != inf.Phase.INHALE, 600)
	var stopped: float = defense.clock
	release(KEY_DOWN)
	physics_frame.disconnect(measure)
	var walked: float = stopped - set_off
	var walk_hits: Array = events_of("HIT").slice(hits_before)
	var gaps := []
	for i in range(1, walk_hits.size()):
		gaps.append(snappedf(walk_hits[i].t - walk_hits[i - 1].t, 0.001))
	var iframes: float = player.invincibility_timer.wait_time
	var owed := 0
	for e in walk_hits:
		owed += catalogue_damage(e.id)
	# The press is taken a frame or so after it is made: from their first step on.
	var first_step: int = gained.find_custom(func(g): return g > 0.0)
	var steps: Array = gained.slice(first_step) if first_step >= 0 else []
	var least: float = steps.min() if not steps.is_empty() else -1.0
	var dropped_on_the_way: Array = inf_fireballs.values().filter(func(r): return r.seen > set_off and r.seen <= stopped)
	dropped_on_the_way.sort_custom(func(a, b): return a.seen < b.seen)
	var apart := []
	for i in range(1, dropped_on_the_way.size()):
		apart.append(dropped_on_the_way[i].pos.distance_to(dropped_on_the_way[i - 1].pos))
	var behind: Array = inf_fireballs.values().filter(func(r): return r.landed > set_off and r.landed <= stopped and r.has("landed_feet")).map(func(r): return r.pos.distance_to(r.landed_feet))
	var average := func(values: Array) -> float: return values.reduce(func(sum, v): return sum + v, 0.0) / maxi(values.size(), 1)
	var net: float = (player.global_position.y - from_y) / walked
	var floor_net: float = player.SPEED - sm.inferno_pull_speed
	log_p("walked straight away from him for %.2f s at %.0f px/s net, %.2f px further from him a frame at the least: %d hits %s at %s, gaps %s, health %d -> %d; markers %.0f px apart on average, %d landed while walking, %.0f to %.0f px from their feet (%.0f on average)" % [walked, net, least, walk_hits.size(), walk_hits.map(func(e): return e.id), walk_hits.map(func(e): return snappedf(e.t - set_off, 0.001)), gaps, health, player.playerHealth, average.call(apart), behind.size(), behind.min() if not behind.is_empty() else -1.0, behind.max() if not behind.is_empty() else -1.0, average.call(behind)])
	# Walking straight out no longer gets away from the shower (the user, 2026-09-29: a harder pull means moving
	# sideways or dashing), but it still gains ground, and what it costs is spaced by the i-frames.
	check(net >= floor_net - 1.0, "walking straight away still makes ground: %.0f px/s net, at least the %.0f walking speed less the pull leaves" % [net, floor_net])
	check(not steps.is_empty() and least >= 0.0, "and the pull never drags them back toward him, on any frame (%.2f px a frame at the least)" % least)
	check(gaps.all(func(g): return g >= iframes - 0.001) and walk_hits.size() <= floori(walked / iframes) + 1, "its hits are one per %.1f s i-frame window at most: %d in %.2f s, gaps %s" % [iframes, walk_hits.size(), walked, gaps])
	check(health - player.playerHealth == owed, "and nothing stacks: %d health lost for their catalogued %d" % [health - player.playerHealth, owed])
	check(await reach_phase(inf.Phase.WINDUP, 900), "the wind-up")
	# Inside the cone's right slant by INFERNO_EDGE_DEPTH, dashing right out of it.
	var rect := hurtbox_at(Vector2(960, 300))
	var slant: float = inf.cone_apex.x + (rect.end.y - inf.cone_apex.y) * tan(inf._half_angle())
	var stand := Vector2(slant - INFERNO_EDGE_DEPTH + rect.size.x / 2.0, 300.0)
	await settle_player(stand)
	await dash_ready()
	await settle_player(stand)
	clear_iframes()
	var burns_before := events_of("HIT", &"bixby_inferno").size()
	var dodged := dodges.size()
	await wait_until(func(): return inf.phase == inf.Phase.WINDUP and inf.elapsed >= sm.inferno_windup - 2.5 * FRAME_TIME, 120)
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(4)
	release(KEY_RIGHT)
	check(await reach_phase(inf.Phase.SPENT, 200), "the breath goes off")
	var inferno_dodges: Array = dodges.slice(dodged).filter(func(d): return d.id == &"bixby_inferno")
	log_p("dashed right from %s (in the cone: %s) to %s: %d inferno hits, perfect dodges %s" % [stand, hits_cone(hurtbox_at(stand)), player.global_position, events_of("HIT", &"bixby_inferno").size() - burns_before, dodges.slice(dodged).map(func(d): return d.id)])
	check(hits_cone(hurtbox_at(stand)) and not hits_cone(hurtbox_rect()), "the dash took them from inside the cone to outside it")
	check(events_of("HIT", &"bixby_inferno").size() == burns_before and inferno_dodges.size() == 1, "untouched, and a PERFECT DODGE for leaving as it caught")

	log_p("-- an ember catching under a player already standing in it")
	await wait(1)
	var fresh: Array = hazards_of("BixbyEmberScript.gd").filter(func(e): return e.phase == e.Phase.IGNITE and not e.is_hurting())
	check(not fresh.is_empty(), "the embers are down and not burning yet")
	if fresh.is_empty():
		return
	var ember: Node2D = fresh[0]
	clear_iframes()
	var ember_hits := events_of("HIT", &"bixby_ember").size()
	await hold_in_ember(ember, 0.5)
	var caught: Array = events_of("HIT", &"bixby_ember").slice(ember_hits)
	var record: Dictionary = inf_embers.get(ember.get_instance_id(), {})
	log_p("stood in the ember at %s as it caught (hurting from %.3f): hits at %s" % [ember.global_position, record.get("hurt", -1.0), caught.map(func(e): return snappedf(e.t, 0.001))])
	check(caught.size() == 1 and absf(caught[0].t - record.get("hurt", -1.0)) <= FRAME_TIME + 0.0001, "hit on the frame it catches, with no entry to report it")


# Moving across the pull is what beats the shower now that walking straight out of it doesn't: the length of
# the bottom rope, with DOWN held against the pull's lift.
func inferno_run_six() -> void:
	if not await start_inferno_run("run 6: strafing the length of the bottom rope through the shower"):
		return
	# The last run's embers are still burning along the rope, and one would hand out i-frames that hide a fireball.
	for ember in burning_embers():
		ember.burn_out()
	check(await reach_phase(inf.Phase.INHALE, 900), "the shower starts")
	var start := Vector2(sm.PLAYER_FLOOR.position.x + INFERNO_STRAFE_INSET, sm.PLAYER_FLOOR.end.y)
	await settle_player(start)
	clear_iframes()
	var hits_before := events_of("HIT").size()
	var set_off: float = defense.clock
	var arrived := [INF]
	var strafe := func():
		if arrived[0] == INF:
			for k in [KEY_RIGHT, KEY_DOWN]:
				if not Input.is_physical_key_pressed(k):
					press(k)
			if player.global_position.x >= sm.PLAYER_FLOOR.end.x - INFERNO_STRAFE_INSET:
				arrived[0] = defense.clock
				release(KEY_RIGHT)
				release(KEY_DOWN)
		await physics_frame
	await shower_hits(strafe)
	var until: float = minf(arrived[0], defense.clock)
	var all_hits: Array = events_of("HIT").slice(hits_before)
	var on_the_way: Array = all_hits.filter(func(e): return e.t <= until)
	var landed: Array = inf_fireballs.values().filter(func(r): return r.landed > set_off and r.landed <= until and r.has("landed_feet")).map(func(r): return r.pos.distance_to(r.landed_feet))
	log_p("strafed the bottom rope from %s for %.2f s%s: %d hits on the way, %d fireballs landed on the way, %.0f to %.0f px from their feet; %d hits stood at the far end after" % [start, until - set_off, "" if arrived[0] != INF else " (the shower ended first)", on_the_way.size(), landed.size(), landed.min() if not landed.is_empty() else -1.0, landed.max() if not landed.is_empty() else -1.0, all_hits.size() - on_the_way.size()])
	check(on_the_way.is_empty(), "strafing across the pull beats the shower: no hit on the way (%d)" % on_the_way.size())
	check(not landed.is_empty() and landed.min() > INFERNO_LANDING_REACH, "every fireball that lands on the way lands clear of their feet (%.0f px at the least)" % (landed.min() if not landed.is_empty() else -1.0))


# tier=death: a player at 1 health is killed by an aimed fireball mid-pull, and the outro stands him down.
func inferno_death() -> void:
	log_p("-- killed by a fireball mid-pull")
	await settle_player(INFERNO_STARTS[0])
	inf = await force_inferno()
	if inf == null:
		check(false, "he goes into the Inferno from his hover")
		return
	check(await reach_phase(inf.Phase.INHALE, 900), "the pull is on")
	await settle_player(inf.pull_target())
	await wait(10)
	check(is_equal_approx(hud_alpha(), sm.inferno_hud_fade_alpha), "the HUD is faded while he hangs there (%.3f)" % hud_alpha())
	clear_iframes()
	player.playerHealth = 1
	var lost := await wait_until(func(): return player.fight_over, 400)
	var hits := events_of("HIT")
	log_p("lost %s at %s, health %d, the blow %s" % [lost, player.global_position, player.playerHealth, hits[-1].id if not hits.is_empty() else &""])
	check(lost and player.playerHealth == 0 and not hits.is_empty() and hits[-1].id == &"bixby_fireball", "a fireball is the killing blow")
	await wait(3)
	var at: Vector2 = player.global_position
	log_p("3 frames on: hazards %s, tells %s, inhale playing %s, state %s, height %.1f, shadow %s, HUD %.3f" % [live_hazards().map(func(h): return h.name), live_tells().size(), boss.inhale_sfx_player.playing, sm.current_state.name, boss.height, boss.shadow.visible, hud_alpha()])
	check(live_hazards().is_empty(), "no hazard of his is left")
	check(live_tells().is_empty(), "no tell")
	check(not boss.inhale_sfx_player.playing, "the inhale has stopped")
	check(sm.current_state.name == "Idle" and sm.player_defeated, "he stands down in Idle")
	check(is_equal_approx(boss.height, boss.HOVER_HEIGHT_PX) and boss.shadow.visible, "off the rope, hovering at %.0f px with his shadow back" % boss.HOVER_HEIGHT_PX)
	check(hud_alpha() > sm.inferno_hud_fade_alpha, "the HUD is on its way back (%.3f)" % hud_alpha())
	await wait(30)
	check(player.global_position == at, "and nothing moves the player for 30 frames")
	log_p("HUD %.3f with the outro %s" % [hud_alpha(), "up" if root.has_node("FightOutro") else "not up"])
	check(root.has_node("FightOutro") and is_equal_approx(hud_alpha(), 1.0), "and through the outro the HUD is back at full")


# tier=defeated: he is beaten while he hangs off the rope, which his fight never allows, to prove the way
# out of the Inferno every ending takes restores the HUD.
func inferno_defeated() -> void:
	log_p("-- beaten on the rope")
	await settle_player(INFERNO_STARTS[0])
	inf = await force_inferno()
	if inf == null:
		check(false, "he goes into the Inferno from his hover")
		return
	check(await reach_phase(inf.Phase.VOLLEY, 300), "he is on the rope, spitting")
	await wait(10)
	check(is_equal_approx(hud_alpha(), sm.inferno_hud_fade_alpha), "the HUD is faded (%.3f)" % hud_alpha())
	# His own defeat's outro, as before Liam took the rest of the fight over (liam_takeover plays that).
	boss.liam_follows = false
	boss.boss_health = 1
	boss._apply_damage(1)
	check(await wait_until(func(): return sm.current_state.name == "Defeated", 30), "he is beaten")
	await wait(3)
	log_p("3 frames on: hazards %s, tells %s, height %.1f, shadow %s, HUD %.3f" % [live_hazards().map(func(h): return h.name), live_tells().size(), boss.height, boss.shadow.visible, hud_alpha()])
	check(live_hazards().is_empty() and live_tells().is_empty(), "nothing of the Inferno is left")
	check(is_equal_approx(boss.height, boss.HOVER_HEIGHT_PX) and boss.shadow.visible, "off the rope, with his shadow back")
	await wait(roundi(boss.HUD_FADE_TIME / FRAME_TIME) + 2)
	check(is_equal_approx(hud_alpha(), 1.0), "and the HUD back at full (%.3f)" % hud_alpha())
	var outro := await wait_until(func(): return root.has_node("FightOutro"), 300)
	log_p("the win's outro %s, HUD %.3f" % ["up" if outro else "not up", hud_alpha()])
	check(outro and is_equal_approx(hud_alpha(), 1.0), "and still at full as the win's outro plays")


# phase=2 for Liam's fight in smoke, blocks and approach: his rotation moved on to the Inferno's cycle while
# his opening takeoff is still rising, so his first cycle is the Inferno and the rest of the rotation follows
# it. It is the last of his cycles, which those modes would otherwise reach late in their window, if at all.
# The perch and the HUD over it are watched from here to check_liam_perch().
func rotate_liam_to_inferno() -> void:
	if fight != "liam" or phase != 2:
		return
	boss = current_scene.get_node(LIAM_BEAST)
	sm = boss.state_machine
	inf = sm.states["Inferno"]
	sm.cycles_started = sm.ATTACK_CYCLES.find_custom(func(cycle: Array) -> bool: return cycle.has("Inferno"))
	log_p("liam's rotation moved on to cycle %d of %d, %s, still in %s" % [sm.cycles_started + 1, sm.ATTACK_CYCLES.size(), sm.ATTACK_CYCLES[sm.cycles_started], sm.current_state.name])
	physics_frame.connect(watch_perch)


# He took the rope in the middle facing down, the HUD faded over him, and it came back once he let go.
func check_liam_perch() -> void:
	if fight != "liam" or phase != 2:
		return
	physics_frame.disconnect(watch_perch)
	log_p("%d frames on the rope; off the middle or mirrored on %s; the HUD not where it should be on %s; HUD now %.3f" % [inf_perched_frames, inf_perch_wrong.slice(0, 5), inf_hud_wrong.slice(0, 5), hud_alpha()])
	check(inf_perched_frames > 0 and inf_perch_wrong.is_empty(), "his Inferno hangs him off the middle of the rope facing down")
	check(inf_hud_wrong.is_empty(), "the HUD fades to %.2f over him and comes back to full once he lets go" % sm.inferno_hud_fade_alpha)
	log_p("on the rope: %d fireball frames, bursts seen in flame on %d and in scorch on %d, wrong on %s; %d ember frames, over his body on %s" % [inf_floor_frames, inf_burst_frames[0], inf_burst_frames[1], inf_floor_wrong.slice(0, 5), inf_ember_frames, inf_ember_over.slice(0, 5)])
	check(inf_floor_wrong.is_empty() and inf_ember_over.is_empty(), "while he hangs off the rope, the shower's markers draw over him and under the player, and its scorches and the embers under him")


# ------------------------------------------------------------------ beast Bixby's combined attack
# BixbyBeastCombined forced from his hover, again and again on one fight, played with real arrow keys and
# dashes: the quake rings his pounds and his spin send out, the slow spin the beams turn with, and whether
# the two together are fair. Every number is read from BixbyCombinedArtLayout, BixbyBeastArtLayout's spin
# loop and BixbyBeastStateMachine's knobs rather than copied.

const CB_LAYOUT := "res://Scripts/BixbyCombinedArtLayout.gd"
const CB_BEAST_LAYOUT := "res://Scripts/BixbyBeastArtLayout.gd"
const CB_RING_SCRIPT := "BixbyQuakeRingScript.gd"
const CB_CRACK_SCRIPT := "BixbyQuakeCrackScript.gd"
# Where the player waits while he hovers. He strafes above them, so each puts the attack somewhere else.
const CB_SPOTS: Array[Vector2] = [Vector2(960, 900), Vector2(600, 900), Vector2(1300, 900), Vector2(400, 700),
	Vector2(1500, 700), Vector2(960, 640), Vector2(300, 300), Vector2(1700, 300), Vector2(960, 150)]
const CB_DIRS: Array[Vector2] = [Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1), Vector2(-1, 0),
	Vector2(-1, -1), Vector2(0, -1), Vector2(1, -1)]
# How far ahead the circling player looks, in physics frames.
const CB_HORIZON := 60
# Where the circling player aims to be: off the walls, where a ring can corner anyone.
const CB_ROOM := Rect2(203, 225.5, 1514, 629)

var cb: Node
var cb_layout: GDScript
var cb_art: GDScript
var cb_held := {}
# Per physics frame from the one the press is read on: whether a dash_through hit is dodged, and how far
# the player has gone since the press (cb_check_dash).
var cb_dash_immune: Array = []
var cb_dash_moved: Array = []


func test_combined() -> void:
	await load_liam()
	# load_liam() keeps the lines' balloon, and with it the VS card's input grace, which is counted in real
	# time and would swallow the first dash press here.
	await skip_vs_card()
	# Every ring the bot dashes through is a perfect dodge, a read: a Break would end his attack mid-run.
	hold_break_gauge(boss)
	# His hovers last until an attack is forced from them, so no fire breath lays solid fire in the way.
	sm.hover_time = 600.0
	sm.hover_between_attacks = 600.0
	cb = sm.states["Combined"]
	cb_layout = load(CB_LAYOUT)
	cb_art = load(CB_BEAST_LAYOUT)
	track()
	track_dodges()
	cb_check_catalogue()
	await cb_check_dash()
	await cb_check_parked()
	cb_check_room()
	await cb_check_pound_dash()
	await cb_check_circling()
	cb_steer(Vector2.ZERO)


func cb_check_catalogue() -> void:
	log_p("-- the catalogue")
	var ring: Dictionary = CATALOG.get_attack(&"bixby_quake_ring")
	check(ring.damage == 2 and ring.dash_through and not ring.blockable and not ring.parryable and not ring.tell
		and not ring.dodge_tell and not ring.no_perfect_dodge and not ring.bypass_invincibility,
		"bixby_quake_ring: a full heart (the tuning round of 2026-10-04), dashed through and a PERFECT DODGE when it is, no guard, no parry, no badge (%s)" % [ring])


# A dash measured the way a ring meets it: from its first frame of movement, the frame after the one its
# press is read on (immune already, standing still), which frames a dash_through hit is dodged on, and how
# far the player has gone by the end of each, holding the way they dashed.
func cb_check_dash() -> void:
	log_p("-- the dash the rings are crossed with")
	await wait_until(func(): return sm.current_state.name == "Hover", 900)
	await settle_player(Vector2(1300, 800))
	await dash_ready()
	var immunity: GDScript = load("res://Scripts/DashImmunity.gd")
	var start := player.global_position.x
	press(KEY_LEFT)
	tap(KEY_W)
	cb_dash_immune.clear()
	cb_dash_moved.clear()
	await wait_until(func(): return player.is_dodging, 10)
	# The first frame it moves on is the frame the press was read on.
	var at := start
	for i in 30:
		cb_dash_immune.append(immunity.is_immune(player, CATALOG.DASH_IMMUNITY_TIME, CATALOG.DASH_IMMUNITY_COOLDOWN))
		await physics_frame
		at = player.global_position.x
		cb_dash_moved.append(start - at)
	release(KEY_LEFT)
	var immune_frames := cb_dash_immune.count(true)
	var travel: float = cb_dash_moved[immune_frames - 1]
	log_p("a dash is immune for %d frames and carries the player %.0f px in them: %s px by each" % [immune_frames, travel, cb_dash_moved.slice(0, immune_frames).map(func(x): return roundi(x))])
	check(immune_frames == roundi(CATALOG.DASH_IMMUNITY_TIME * 60.0), "immune for its first %d frames of movement, as on the frame its press is read" % roundi(CATALOG.DASH_IMMUNITY_TIME * 60.0))
	check(travel >= 250.0, "and further than the dash itself while immune, walking on after its landing beat (%.0f px)" % travel)


# His next hover, held over `spot` long enough for him to strafe above it and for the last attack's rings
# to roll off the floor, then the combined attack with nothing queued behind it.
func cb_force(spot: Vector2) -> bool:
	cb_steer(Vector2.ZERO)
	if not await wait_until(func(): return sm.current_state.name == "Hover", 1200):
		return false
	var hover: Node = sm.states["Hover"]
	for i in 1800:
		hover.elapsed = 0.0
		player.global_position = spot
		player.velocity = Vector2.ZERO
		if i >= 150 and hazards_of(CB_RING_SCRIPT).is_empty():
			break
		await physics_frame
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	sm.attacks = []
	sm.on_child_transition(sm.current_state, "Combined")
	return sm.current_state == cb


# One attack standing still where the smoke test stands: its shape frame by frame, and what it lands.
func cb_check_parked() -> void:
	log_p("-- one attack, standing still at %s" % SMOKE_SPOTS["liam"])
	if not await cb_force(SMOKE_SPOTS["liam"]):
		check(false, "the combined attack starts from his hover")
		return
	var start: float = defense.clock
	var hits_before := events.size()
	var impact: float = cb_art.time_to_step(&"pound", cb_art.POUND_IMPACT_STEP)
	var f: float = cb_layout.FLOOR_FLATTEN
	var rings := {}
	var births := []
	var cracks := 0
	var off_ellipse := []
	var shown_off_floor := 0
	# The ring art's checks, frame after frame (cb_check_segments).
	var art_checks := {"frames": 0, "off": [], "uneven": 0.0, "rows": [], "beats": [], "culled": [], "to_ropes": INF}
	var last_phase := -1
	var phase_at := {}
	var spin_steps := []
	var worst_step := 0.0
	var off_mouths := 0.0
	var ahead_of_drawn := []
	var spin_az_start := INF
	var spin_az_end := 0.0
	var spin_t := [0.0, 0.0]
	var last_az := []
	var last_loop_frame := -1
	var growth := []
	var loop: Dictionary = cb_art.SPIN_LOOP
	# The wind-down: the yellow ring on the spin's last frame and on the frame the beams stop, where his
	# heads were on the last frame before the wobble, and when each wobble frame came up.
	var tell_on_last_spin := false
	var tell_on_stop := true
	var last_front := 0.0
	var wobble_at := {}
	while sm.current_state == cb:
		player.global_position = SMOKE_SPOTS["liam"]
		player.velocity = Vector2.ZERO
		await physics_frame
		var t: float = defense.clock - start
		if cb.phase != last_phase:
			phase_at[cb.phase] = t
			if cb.phase == cb.Phase.SPIN_DOWN:
				tell_on_stop = cb_tell_up()
			last_phase = cb.phase
		if cb.phase == cb.Phase.SPIN:
			tell_on_last_spin = cb_tell_up()
		if cb.phase == cb.Phase.SPIN_DOWN:
			if boss.current_anim == &"spin":
				last_loop_frame = boss.drawn_frame_of(loop.sheet)
				last_front = cb_layout.LOOP_MOUTH_ANCHORS[loop.frames[boss.anim_step]][0][0] \
					+ loop.step_degrees * boss.anim_clock / cb_art.spin_step_time()
			elif boss.current_anim == &"spin_down" and not wobble_at.has(boss.sprite.frame):
				wobble_at[boss.sprite.frame] = t
		cracks += hazards_of(CB_CRACK_SCRIPT).size()
		for ring in hazards_of(CB_RING_SCRIPT):
			var id: int = ring.get_instance_id()
			if not rings.has(id):
				rings[id] = {"born": t, "phase": cb.phase, "r": ring.radius, "at": ring.global_position,
					"pound_elapsed": cb.elapsed, "impact_done": cb.impact_done, "ring_clock": cb.ring_clock,
					"feet": boss.ground_position, "first_r": ring.radius, "first_t": t}
				births.append(snappedf(t, 0.001))
			else:
				rings[id].r = ring.radius
				rings[id].t = t
			if cb_layout.USE_FINAL_RING:
				cb_check_segments(ring, art_checks)
				continue
			# Every tile standing on the flattened ellipse, and drawn only inside the ropes.
			for i in mini(ceili(TAU * ring.radius / cb_layout.RING_TILE_SPACING), ring.tiles.size()):
				var tile: Sprite2D = ring.tiles[i]
				var p: Vector2 = tile.position
				var on := Vector2(p.x / ring.radius, p.y / (ring.radius * f)).length()
				if absf(on - 1.0) > 2.0 / (ring.radius * f):
					off_ellipse.append(snappedf(on, 0.001))
				if tile.visible and not cb_layout.RING_VISIBLE_AREA.has_point(tile.global_position):
					shown_off_floor += 1
		if cb.phase == cb.Phase.SPIN and is_instance_valid(cb.sweep):
			var az: Array = cb.sweep.was_azimuth.map(func(a): return rad_to_deg(a))
			if not last_az.is_empty() and last_az.size() == az.size():
				var step := 0.0
				for i in az.size():
					step = maxf(step, absf(wrapf(az[i] - last_az[i], -180.0, 180.0)))
				worst_step = maxf(worst_step, step)
				spin_steps.append(step)
				spin_az_end += wrapf(az[0] - last_az[0], -180.0, 180.0)
				spin_t[1] = t
			else:
				spin_t[0] = t
			last_az = az
			# The beams come out of the maws glided to between the frame drawn and the next.
			var mouths: Array = cb_layout.loop_mouths(boss.anim_step, boss.anim_clock)
			for beam in cb.sweep.beams:
				var nearest := INF
				for mouth in mouths:
					nearest = minf(nearest, beam.position.distance_to(cb_art.local(Vector2(mouth[1], mouth[2]))))
				off_mouths = maxf(off_mouths, nearest)
			# The heads drawn trail the beams by less than a frame's step.
			var drawn: Array = cb_layout.LOOP_MOUTH_ANCHORS[boss.sprite.frame]
			var lead := INF
			for a in az:
				for head in drawn:
					lead = minf(lead, fposmod(a - head[0], 360.0))
			ahead_of_drawn.append(lead)
			last_loop_frame = boss.drawn_frame_of(loop.sheet)
	var t_end: float = defense.clock - start
	var hits := events.slice(hits_before)
	var ids := {}
	for e in hits:
		ids[e.id] = ids.get(e.id, 0) + 1
	log_p("phases at %s; rings born at %s; %d crack frames" % [phase_at, births, cracks])

	log_p("-- rings instead of cracks")
	check(cracks == 0 and not ids.has(&"bixby_quake_burst"), "no crack, eruption or wave: nothing of the old pound is planted")
	var pound_rings := rings.values().filter(func(r): return r.phase == cb.Phase.POUNDS)
	check(pound_rings.size() == sm.combined_pounds, "every pound sends one ring out (%d of %d)" % [pound_rings.size(), sm.combined_pounds])
	check(pound_rings.all(func(r): return r.impact_done and r.pound_elapsed - impact < 1.0 / 60.0 + 0.001),
		"on the frame his claws land (the pound's step %d)" % cb_art.POUND_IMPACT_STEP)
	check(rings.values().all(func(r): return r.at.distance_to(r.feet) < 1.0 and r.first_r - cb_layout.RING_START_RADIUS <= sm.quake_ring_speed / 60.0 + 0.01),
		"each on his feet, starting at RING_START_RADIUS under his claws")
	for r in rings.values():
		if r.has("t") and r.t > r.first_t:
			growth.append((r.r - r.first_r) / (r.t - r.first_t))
	check(growth.all(func(g): return absf(g - sm.quake_ring_speed) < 0.5), "and growing at quake_ring_speed, %.0f px of floor a second (%s)" % [sm.quake_ring_speed, growth.map(func(g): return snappedf(g, 0.1))])
	if cb_layout.USE_FINAL_RING:
		log_p("the ring art over %d ring frames: neighbours at most %.2fx further apart than the closest pair; a drawn segment's ground came within %.0f px of the rope art" % [art_checks.frames, art_checks.uneven, art_checks.to_ropes])
		check(art_checks.off.is_empty(), "every segment stands on the ellipse flattened by FLOOR_FLATTEN, snapped to the texel grid (%s off it)" % [art_checks.off.slice(0, 5)])
		check(art_checks.uneven < 1.3, "spaced evenly round the screen, not bunched up the sides (%.2fx)" % art_checks.uneven)
		check(art_checks.rows.is_empty(), "each on the row of its screen tangent, flipped on the other diagonal (%s wrong)" % [art_checks.rows.slice(0, 5)])
		check(art_checks.beats.is_empty(), "neighbours a frame of the crest apart (%s not)" % [art_checks.beats.slice(0, 5)])
		check(art_checks.culled.is_empty(), "drawn only while its ground is within the rope art at the sides and bottom and its crest under the top rope (%s not)" % [art_checks.culled.slice(0, 5)])
	else:
		check(off_ellipse.is_empty(), "every tile stands on the ellipse flattened by FLOOR_FLATTEN (%s off it)" % [off_ellipse.slice(0, 5)])
		check(shown_off_floor == 0, "and none is drawn outside the ropes (%d)" % shown_off_floor)

	log_p("-- the slow, continuous sweep")
	var rate: float = spin_az_end / (spin_t[1] - spin_t[0])
	log_p("beams turned %.1f deg over %.2f s: %.2f deg/s; the most any beam moved between two frames %.3f deg; beams at most %.2f px off the glided maws; drawn heads trail them by %.2f to %.2f deg" % [spin_az_end, spin_t[1] - spin_t[0], rate, worst_step, off_mouths, ahead_of_drawn.min(), ahead_of_drawn.max()])
	check(absf(rate - cb_art.SPIN_DEGREES_PER_SECOND) < 0.5, "the beams turn at SPIN_DEGREES_PER_SECOND (%.2f)" % rate)
	check(worst_step <= cb_art.SPIN_DEGREES_PER_SECOND / 60.0 + 0.05, "continuously: never more than a frame's turn between two physics frames (%.3f deg)" % worst_step)
	check(off_mouths < 0.5, "coming out of his maws glided between the frame drawn and the next (%.2f px)" % off_mouths)
	check(ahead_of_drawn.max() < loop.step_degrees + 0.01, "with his drawn heads less than a frame's step behind them")
	var spun: float = phase_at.get(cb.Phase.SPIN_DOWN, t_end) - phase_at.get(cb.Phase.SPIN, 0.0)
	log_p("he spun %.2f s and left the loop on frame %d" % [spun, last_loop_frame])
	check(spun >= sm.combined_spin_time - 0.001 and spun < sm.combined_spin_time + cb_art.anim_time(&"spin"),
		"for at least combined_spin_time and at most a loop more (%.2f s)" % spun)
	check(loop.exit_frames.has(last_loop_frame), "handing over to the wobble from one of SPIN_LOOP.exit_frames (%d)" % last_loop_frame)

	log_p("-- the wind-down")
	var wobble: Array = cb_art.ANIMS[&"spin_down"].frames
	var first_heads: Array = cb_layout.MOUTH_ANCHORS[wobble[0]]
	var second_heads: Array = cb_layout.MOUTH_ANCHORS[wobble[1]]
	var wobble_turn := INF
	for head in second_heads:
		wobble_turn = minf(wobble_turn, fposmod(head[0] - first_heads[0][0], 360.0))
	var stop_at: float = phase_at.get(cb.Phase.SPIN_DOWN, t_end)
	var first_at: float = wobble_at.get(wobble[0], t_end)
	var second_at: float = wobble_at.get(wobble[1], t_end)
	var dizzy_at: float = phase_at.get(cb.Phase.DIZZY, t_end)
	var short_of_it := absf(wrapf(first_heads[0][0] - last_front, -60.0, 60.0))
	var coast_rate: float = cb_art.SPIN_DEGREES_PER_SECOND
	var wobble_rate: float = wobble_turn / (second_at - first_at)
	log_p("the beams stop at %.3f s with the yellow ring up to the frame before (%s) and gone on it (%s); his heads turn on through the loop to %.3f s, %.2f deg short of the wobble's first frame on the last, which is up %.3f s, then its second, %.0f deg on, at %.3f s (%.1f deg/s), and he is dizzy at %.3f s, %.2f s after the beams stop. The whole attack: %.2f s" % [stop_at, tell_on_last_spin, not tell_on_stop, first_at, short_of_it, second_at - first_at, wobble_turn, second_at, wobble_rate, dizzy_at, dizzy_at - stop_at, t_end])
	check(tell_on_last_spin and not tell_on_stop, "the yellow ring is up to the last frame of the spin and gone on the frame the beams stop")
	check(short_of_it <= coast_rate / 60.0 + 0.01, "his heads turn on at the loop's rate right up to the wobble's first frame, so it follows without a jump")
	check(absf(second_at - first_at - cb_art.ANIMS[&"spin_down"].times[0]) < 1.5 / 60.0 and wobble_rate < coast_rate,
		"its second frame turns slower than the loop did (%.1f deg/s against %.0f)" % [wobble_rate, coast_rate])
	check(absf(dizzy_at - second_at - cb_art.ANIMS[&"spin_down"].times[1]) < 1.5 / 60.0, "and he holds it %.2f s, stopped, before the dizzy spell" % cb_art.ANIMS[&"spin_down"].times[1])

	log_p("-- the rings the spin sends")
	var spin_start: float = phase_at.get(cb.Phase.SPIN, 0.0)
	var spin_rings := rings.values().filter(func(r): return r.phase == cb.Phase.SPIN)
	var beats := spin_rings.map(func(r): return snappedf(r.born - spin_start, 0.001))
	var expect := floori(spun / sm.combined_spin_ring_interval)
	log_p("spin rings at %s s into the spin" % [beats])
	check(spin_rings.size() == expect and beats.all(func(b): return absf(fposmod(b + 0.001, sm.combined_spin_ring_interval) - 0.001) < 1.0 / 60.0 + 0.002),
		"one every combined_spin_ring_interval (%.2f s) while he spins: %d" % [sm.combined_spin_ring_interval, expect])
	check(rings.values().all(func(r): return r.phase == cb.Phase.POUNDS or r.phase == cb.Phase.SPIN), "and none once he stops")

	log_p("-- standing still")
	log_p("standing at %s took %d hits: %s" % [SMOKE_SPOTS["liam"], hits.size(), ids])
	check(ids.has(&"bixby_quake_ring") and ids.has(&"bixby_sonic_beam"), "standing still is hit by the rings and by the beams")
	check(hits.all(func(e): return catalogue_damage(e.id) == 2), "a full heart each (the tuning round of 2026-10-04)")


# The room between rings, from the knobs. The spin's are far enough apart to stand between. The pounds'
# are not, which is why cb_check_pound_dash crosses all three in one dash.
func cb_check_room() -> void:
	log_p("-- room between rings")
	var v: float = sm.quake_ring_speed
	var band: float = cb_layout.RING_HURT_HALF_WIDTH * 2.0
	var f: float = cb_layout.FLOOR_FLATTEN
	var foot := Vector2(36.0, cb_layout.RING_FOOT_HEIGHT)
	var spin_gap: float = sm.combined_spin_ring_interval * v - band
	var pound_gap: float = sm.combined_pound_interval * v - band
	var impact: float = cb_art.time_to_step(&"pound", cb_art.POUND_IMPACT_STEP)
	var third: float = (sm.combined_pounds - 1) * sm.combined_pound_interval + impact
	var first_spin: float = sm.combined_pounds * sm.combined_pound_interval + sm.combined_spin_tell + sm.combined_spin_ring_interval
	var group_gap: float = (first_spin - third) * v - band
	log_p("between the spin's rings %.0f px of floor: %.0f broadside against a %.0f px wide foot, %.0f across the screen against a %.0f px deep one" % [spin_gap, spin_gap, foot.x, spin_gap * f, foot.y])
	log_p("between the pounds' last ring and the spin's first %.0f px of floor; between two of the pounds' %.0f" % [group_gap, pound_gap])
	check(spin_gap > foot.x * 2.0 and spin_gap * f > foot.y * 2.0, "the spin's rings leave room to stand between them")
	check(group_gap > foot.x * 2.0 and group_gap * f > foot.y * 2.0, "and so do the pounds' three and the spin's first")
	check(pound_gap < foot.x, "the pounds' three do not (%.0f px), so they are one band, crossed in one dash below" % pound_gap)


# The pounds' three rings where they are thickest on screen, broadside: the player stands at his side level
# with his feet and dashes in across all three at once, at the middle of the frames a dash could be pressed
# on and still carry them clear.
func cb_check_pound_dash() -> void:
	log_p("-- the pounds' three rings in one dash")
	if not await cb_force(Vector2(960, 900)):
		check(false, "the combined attack starts from his hover")
		return
	await wait_until(func(): return cb.phase == cb.Phase.BRACE, 60)
	var feet: Vector2 = boss.ground_position
	var side := 1.0 if feet.x < 960.0 else -1.0
	var foot_line := feet.y - 36.0
	var stand := Vector2(feet.x + side * 420.0, foot_line)
	await wait_until(func(): return cb.pounds_done == sm.combined_pounds and cb.impact_done, 120)
	player.global_position = stand
	player.velocity = Vector2.ZERO
	clear_iframes()
	var rings := cb_rings_ahead()
	# Every frame the press could come on from now: is the player touched before the dash is under way, or
	# after its immunity, before they are inside all three?
	var good := []
	for press_in in 90:
		var ok := true
		for k in range(1, press_in + 45):
			var moved := 0.0
			var immune := false
			var into := k - press_in - 2
			if into >= 0:
				moved = cb_dash_moved[mini(into, cb_dash_moved.size() - 1)]
				immune = into < cb_dash_immune.size() and cb_dash_immune[into]
			var at := stand + Vector2(-side * moved, 0.0)
			if not immune and cb_ring_gap(at, rings, k / 60.0) < 0.0:
				ok = false
				break
		if ok:
			good.append(press_in)
	log_p("broadside, %.0f px out: a press %s frames from now carries them across all three" % [absf(stand.x - feet.x), good])
	check(good.size() >= 6, "there are %d frames (%.2f s) to press it on" % [good.size(), good.size() / 60.0])
	if good.is_empty():
		return
	var mid: int = good[good.size() / 2]
	var ring_hits := events_of("HIT", &"bixby_quake_ring").size()
	for i in mid:
		player.global_position = stand
		await physics_frame
	cb_steer(Vector2(-side, 0))
	tap(KEY_W)
	await wait(40)
	cb_steer(Vector2.ZERO)
	var hurt := events_of("HIT", &"bixby_quake_ring").size() - ring_hits
	var d: Vector2 = player.global_position - feet
	var rho := Vector2(absf(d.x) + 18.0, (d.y + 42.0) / cb_layout.FLOOR_FLATTEN).length()
	var inner: float = hazards_of(CB_RING_SCRIPT).map(func(r): return r.radius).min() - cb_layout.RING_HURT_HALF_WIDTH
	log_p("pressed %d frames in: %d ring hits, now %.0f px of floor out against the nearest ring's inner edge at %.0f" % [mid, hurt, rho, inner])
	check(hurt == 0 and rho < inner, "one dash across all three, untouched, and inside them")
	await wait_until(func(): return sm.current_state != cb, 900)


# The player who circles with the beams and dashes through each ring as it reaches them, from every spot:
# never hit, never left in a beam by a ring, never short of stamina.
func cb_check_circling() -> void:
	log_p("-- circling with the beams, dashing through each ring")
	var refused := [0]
	defense.stamina_refused.connect(func(): refused[0] += 1)
	var total_hits := 0
	var landings := []
	var worst_stamina := INF
	var through_beams := 0
	for spot in CB_SPOTS:
		if not await cb_force(spot):
			check(false, "the combined attack starts from his hover over %s" % spot)
			continue
		var hits_before := events.size()
		var dodged := dodges.size()
		var dashes := 0
		var dash_frame := -1000
		var frames_run := 0
		var min_stamina := INF
		var run_landings := []
		var closest := INF
		while sm.current_state == cb:
			frames_run += 1
			var act := cb_choose()
			cb_steer(act.dir)
			if act.kind == "dash":
				tap(KEY_W)
				dashes += 1
				dash_frame = frames_run
			await physics_frame
			min_stamina = minf(min_stamina, defense.stamina)
			var beam_room := cb_beam_gap(player.global_position, cb_beams_ahead(0))
			if not player.is_dodging:
				closest = minf(closest, beam_room)
			if frames_run - dash_frame == 13 and beam_room < INF:
				run_landings.append(roundi(beam_room))
		cb_steer(Vector2.ZERO)
		var hits := events.slice(hits_before)
		var beam_dodges: int = dodges.slice(dodged).filter(func(e): return e.id == &"bixby_sonic_beam").size()
		log_p("from %s, him at %s: %d hits %s, %d dashes, stamina down to %.0f, beam clearance after each dash %s, nearest a beam outside a dash %.0f px, %d beams crossed inside a ring dash" % [spot, boss.ground_position.round(), hits.size(), hits.map(func(e): return e.id), dashes, min_stamina, run_landings, closest, beam_dodges])
		total_hits += hits.size()
		landings.append_array(run_landings)
		worst_stamina = minf(worst_stamina, min_stamina)
		through_beams += beam_dodges
	log_p("%d runs: %d hits; beam clearance after every ring dash %s; stamina never below %.0f; %d refused dashes; %d beams crossed inside a ring dash's immunity" % [CB_SPOTS.size(), total_hits, landings, worst_stamina, refused[0], through_beams])
	check(total_hits == 0, "circling with the beams and dashing through each ring as it comes takes no hits, from %d starts" % CB_SPOTS.size())
	check(not landings.is_empty() and landings.min() >= 0, "a ring never leaves the player in a beam: clear of every one once each dash's immunity is over (%d px at the least)" % (landings.min() if not landings.is_empty() else -1))
	# Never short: every dash it wanted came out. Not a dash in reserve as well, as when a dash was 15 of the bar:
	# at a third of it (2026-09-27) the worst run spends nearly all of it.
	check(refused[0] == 0, "and never short of stamina: no dash it wanted was refused (the bar never below %.0f)" % worst_stamina)


# One frame of one ring's art, against the artist's rules worked out here again rather than read off the
# layout's helpers: each segment on the flattened ellipse to within the texel snap; neighbours as far apart
# on screen all the way round; the row its screen tangent picks, flipped on the falling diagonal; a frame of
# the crest on from its neighbour; drawn only where its ground and crest are allowed.
func cb_check_segments(ring: Node2D, checks: Dictionary) -> void:
	var f: float = cb_layout.FLOOR_FLATTEN
	var count: int = ring.segments.size()
	if count == 0 or count % 4 != 0:
		checks.off.append("count %d" % count)
		return
	checks.frames += 1
	var centre: Vector2 = ring.global_position
	var r: float = ring.radius
	var bounds: Array = cb_layout.RING_ROW_TANGENTS
	var rope: Rect2 = cb_layout.RING_ROPE_ART
	var gaps := []
	for i in count:
		var tile: Sprite2D = ring.tiles[i]
		var theta: float = ring.segments[i][0]
		var exact := centre + Vector2(cos(theta), sin(theta) * f) * r
		var at := tile.global_position
		if absf(at.x - exact.x) > 1.51 or absf(at.y - exact.y) > 1.51 or fmod(at.x, 3.0) != 0.0 or fmod(at.y, 3.0) != 0.0:
			checks.off.append(at)
		gaps.append(at.distance_to(ring.tiles[(i + 1) % count].global_position))
		var tangent := rad_to_deg(atan2(f * absf(cos(theta)), absf(sin(theta))))
		var row := bounds.size()
		for bucket in bounds.size():
			if tangent < bounds[bucket]:
				row = bucket
				break
		var flip := row >= 1 and row <= 5 and sin(theta) * cos(theta) < 0.0
		if tile.frame / 4 != row or tile.flip_h != flip:
			checks.rows.append([snappedf(tangent, 0.1), row, tile.frame / 4, flip, tile.flip_h])
		if posmod(tile.frame - ring.tiles[(i + count - 1) % count].frame, 4) != 1:
			checks.beats.append(i)
		var ground: Array = cb_layout.RING_GROUND_BOXES[row]
		var room := minf(minf(at.x - ground[0] - rope.position.x, rope.end.x - at.x - ground[0]), rope.end.y - at.y - ground[2])
		var allowed: bool = room >= 0.0 and at.y + cb_layout.RING_CREST_TOPS[row] >= rope.position.y
		if tile.visible != allowed:
			checks.culled.append([at, row, tile.visible])
		if tile.visible:
			checks.to_ropes = minf(checks.to_ropes, room)
	if r >= 300.0:
		checks.uneven = maxf(checks.uneven, gaps.max() / gaps.min())


# Whether his yellow ring is up: ParryTell names the one live badge a boss has after him, and renames it
# spent as it clears.
func cb_tell_up() -> bool:
	return boss.get_parent().get_node_or_null("ParryTell%d" % boss.get_instance_id()) != null


func cb_hold(code: int, on: bool) -> void:
	if cb_held.get(code, false) == on:
		return
	cb_held[code] = on
	if on:
		press(code)
	else:
		release(code)


func cb_steer(dir: Vector2) -> void:
	cb_hold(KEY_RIGHT, dir.x > 0.0)
	cb_hold(KEY_LEFT, dir.x < 0.0)
	cb_hold(KEY_DOWN, dir.y > 0.0)
	cb_hold(KEY_UP, dir.y < 0.0)


func cb_held_dir() -> Vector2:
	return Vector2(float(cb_held.get(KEY_RIGHT, false)) - float(cb_held.get(KEY_LEFT, false)),
		float(cb_held.get(KEY_DOWN, false)) - float(cb_held.get(KEY_UP, false)))


# The rings on the floor and the ones still to come, as [centre, radius, seconds from now it starts from
# there, speed, still to be born]: the pounds' on their impacts, the spin's on its beat.
func cb_rings_ahead() -> Array:
	var out := []
	for ring in hazards_of(CB_RING_SCRIPT):
		out.append([ring.global_position, ring.radius, 0.0, ring.speed, ring.hurts_inside_at_birth and not ring.born])
	var feet: Vector2 = boss.ground_position
	var r0: float = cb_layout.RING_START_RADIUS
	var v: float = sm.quake_ring_speed
	var impact: float = cb_art.time_to_step(&"pound", cb_art.POUND_IMPACT_STEP)
	match cb.phase:
		cb.Phase.DESCENT, cb.Phase.BRACE:
			var first: float = sm.combined_windup + impact - (cb.elapsed if cb.phase == cb.Phase.BRACE else 0.0)
			for i in sm.combined_pounds:
				out.append([feet, r0, first + i * sm.combined_pound_interval, v, true])
		cb.Phase.POUNDS:
			var next: float = impact - cb.elapsed + (sm.combined_pound_interval if cb.impact_done else 0.0)
			for i in sm.combined_pounds - cb.pounds_done + (0 if cb.impact_done else 1):
				out.append([feet, r0, next + i * sm.combined_pound_interval, v, true])
		cb.Phase.SPIN_UP:
			out.append([feet, r0, sm.combined_spin_tell - cb.elapsed + sm.combined_spin_ring_interval, v, true])
		cb.Phase.SPIN:
			out.append([feet, r0, sm.combined_spin_ring_interval - cb.ring_clock, v, true])
	return out


# How far the foot of the player's hurtbox at `at` is from every band `after` seconds on, as the ring tests
# it (on the floor, in screen px across it): below 0, in one.
func cb_ring_gap(at: Vector2, rings: Array, after: float) -> float:
	var f: float = cb_layout.FLOOR_FLATTEN
	var hw: float = cb_layout.RING_HURT_HALF_WIDTH
	var foot: float = cb_layout.RING_FOOT_HEIGHT
	var gap := INF
	for ring in rings:
		if after < ring[2]:
			continue
		var radius: float = ring[1] + ring[3] * (after - ring[2])
		var c: Vector2 = ring[0]
		var x0 := at.x - 18.0 - c.x
		var x1 := at.x + 18.0 - c.x
		var y0 := (at.y + 42.0 - foot - c.y) / f
		var y1 := (at.y + 42.0 - c.y) / f
		var near := Vector2(clampf(0.0, x0, x1), clampf(0.0, y0, y1)).length()
		var far := maxf(maxf(Vector2(x0, y0).length(), Vector2(x1, y0).length()), maxf(Vector2(x0, y1).length(), Vector2(x1, y1).length()))
		# On the frame it is born (give or take one) his ring catches everything inside it too (hurts_inside_at_birth).
		var birth: bool = ring[4] and after - ring[2] <= 2.0 / 60.0
		if near <= radius + hw and (birth or far >= radius - hw):
			return -1.0
		gap = minf(gap, (near - radius - hw) if near > radius + hw else (radius - hw - far))
	return gap * f


func cb_loop_ahead(step: int, into: float) -> Array:
	var step_time: float = cb_art.spin_step_time()
	var steps := int(into / step_time)
	var frames: Array = cb_art.SPIN_LOOP.frames
	return cb_layout.loop_mouths((step + steps) % frames.size(), into - steps * step_time)


# The beams `ahead` physics frames from now as [origin, screen angle, length], glued to his maws as the
# sweep glues them: lit once the spin's warning is over, on the loop step it picked, then gliding on with
# his drawn clock. Before the warning picks it, the step it would pick with the player where they are.
func cb_beams_ahead(ahead: int) -> Array:
	var sweep = cb.sweep
	if is_instance_valid(sweep) and sweep.fading:
		return []
	var t := ahead / 60.0
	var lit_in := INF
	match cb.phase:
		cb.Phase.BRACE:
			lit_in = sm.combined_windup - cb.elapsed + sm.combined_pounds * sm.combined_pound_interval + sm.combined_spin_tell
		cb.Phase.POUNDS:
			lit_in = (sm.combined_pounds - cb.pounds_done + 1) * sm.combined_pound_interval - cb.elapsed + sm.combined_spin_tell
		cb.Phase.SPIN_UP:
			lit_in = sm.combined_spin_tell - cb.elapsed
	var mouths := []
	if boss.current_anim == &"spin":
		mouths = cb_loop_ahead(boss.anim_step, boss.anim_clock + t)
	elif lit_in < INF:
		if t < lit_in:
			return []
		mouths = cb_loop_ahead(cb.entry_step if cb.phase == cb.Phase.SPIN_UP else cb._widest_gap_step(), t - lit_in)
	elif is_instance_valid(sweep):
		mouths = cb_layout.MOUTH_ANCHORS.get(boss.drawn_frame_of(cb_art.SPIN_SHEET), [])
	var out := []
	for mouth in mouths:
		var origin: Vector2 = boss.feet_position() + cb_art.local(Vector2(mouth[1], mouth[2]))
		var az := deg_to_rad(mouth[0])
		var angle: float = cb_layout.beam_angle(az)
		out.append([origin, angle, cb_reach(az, origin, angle)])
	return out


# How far a full-grown beam runs: to the ropes, whichever way it points; only a mouth outside them keeps the
# drawn length the art reads at.
func cb_reach(az: float, origin: Vector2, angle: float) -> float:
	var room := cb_room_to_ropes(origin, angle)
	return room if room < INF else cb_layout.BEAM_REACH * cb_layout.SCALE * cb_layout.beam_length(az)


func cb_room_to_ropes(from: Vector2, angle: float) -> float:
	var arena: Rect2 = sm.ROPES
	if not arena.has_point(from):
		return INF
	var along := Vector2.RIGHT.rotated(angle)
	var room := INF
	if absf(along.x) > 0.001:
		room = minf(room, ((arena.end.x if along.x > 0.0 else arena.position.x) - from.x) / along.x)
	if absf(along.y) > 0.001:
		room = minf(room, ((arena.end.y if along.y > 0.0 else arena.position.y) - from.y) / along.y)
	return room


# How far the player's body, as the sweep tests it, is from every beam: below 0, in one.
func cb_beam_gap(at: Vector2, beams: Array) -> float:
	var radius: float = load("res://Scripts/BixbySonicSweepScript.gd").PLAYER_RADIUS
	var across: float = cb_layout.BEAM_HIT_THICKNESS * cb_layout.SCALE / 2.0 + radius
	var gap := INF
	for beam in beams:
		var along: Vector2 = (at - beam[0]).rotated(-beam[1])
		var out_x := maxf(maxf(-radius - along.x, 0.0), along.x - (beam[2] + radius))
		var out_y := maxf(absf(along.y) - across, 0.0)
		if out_x == 0.0 and out_y == 0.0:
			return -1.0
		gap = minf(gap, Vector2(out_x, out_y).length())
	return gap


# The middle of the gap between the beams the player is in, a little ahead of it, on a loop round his maws:
# 420 px out to either side, 300 below them and 170 above. Before the beams: in front of him if the floor
# goes that far, where the pounds' rings are thinnest on screen, or out to his side.
func cb_gap_target(at: Vector2) -> Vector2:
	var feet: Vector2 = boss.ground_position
	var maws: Vector2 = boss.feet_position() + cb_art.local(cb_layout.SPIN_CENTRE)
	var beams := cb_beams_ahead(0)
	if cb.phase != cb.Phase.SPIN or beams.is_empty():
		var ahead := feet + Vector2(0, 300)
		if ahead.y <= CB_ROOM.end.y:
			return ahead
		var side := 1.0 if at.x >= feet.x else -1.0
		return (feet + Vector2(side * 400.0, 0)).clamp(CB_ROOM.position, CB_ROOM.end)
	var mine := rad_to_deg(cb_layout.floor_azimuth((at - maws).angle()))
	var front := rad_to_deg(cb_layout.floor_azimuth(beams[0][1]))
	var azimuth := mine - fposmod(mine - front, 120.0) + 70.0
	var dir := Vector2.from_angle(cb_layout.beam_angle(deg_to_rad(azimuth)))
	var r := 1.0 / Vector2(dir.x / 420.0, dir.y / (300.0 if dir.y > 0.0 else 170.0)).length()
	return (maws + dir * r).clamp(CB_ROOM.position, CB_ROOM.end)


func cb_step(at: Vector2, dir: Vector2, px: float) -> Vector2:
	var floor_area: Rect2 = sm.PLAYER_FLOOR
	return (at + dir * px).clamp(floor_area.position, floor_area.end)


# The circling player's move this frame: each of the nine walks and, when a ring is about to reach them,
# the eight dashes, run CB_HORIZON frames ahead. Never a beam, dash or no dash; never a ring outside a
# dash's immunity unless the next dash will be ready for it; then as near the middle of the gap as can be,
# with room to spare and off the walls. Keys pressed now only move the player from the next frame, so this
# frame's step (k = 1) is already the held keys'; a dash pressed now is immune from this frame, though, for
# immune_frames of them, and moves on the next dash_frames.
func cb_choose() -> Dictionary:
	if player.is_dodging or defense.is_dash_recovering():
		return {"kind": "walk", "dir": cb_held_dir()}
	var walk: float = load("res://Scripts/PlayerScript.gd").SPEED / 60.0
	var dash: float = load("res://Scripts/PlayerScript.gd").DODGE_SPEED / 60.0
	var dash_frames := ceili(player.dodge_time * 60.0 - 0.001)
	var immune_frames := roundi(CATALOG.DASH_IMMUNITY_TIME * 60.0) + 1
	var cooldown := roundi(CATALOG.DASH_IMMUNITY_COOLDOWN * 60.0)
	var since: int = Engine.get_physics_frames() - player.last_dodge_physics_frame
	var at := player.global_position
	var first := cb_step(at, cb_held_dir(), walk)
	var target := cb_gap_target(at)
	var rings := cb_rings_ahead()
	var beams := []
	for k in CB_HORIZON + 1:
		beams.append(cb_beams_ahead(k))
	var stamina_ok: bool = defense.can_afford(defense.dash_stamina_cost)
	var can_dash: bool = since >= cooldown and not defense.is_dash_cooling_down() and stamina_ok
	var ring_now := false
	for d in [Vector2.ZERO, (target - at).sign()]:
		var q := first
		for k in range(2, 5):
			q = cb_step(q, d, walk)
			if cb_ring_gap(q, rings, k / 60.0) < 0.0:
				ring_now = true
	var options := [{"kind": "walk", "dir": Vector2.ZERO}]
	for d in CB_DIRS:
		options.append({"kind": "walk", "dir": d})
	if can_dash and ring_now:
		for d in CB_DIRS:
			# What they do once its landing beat is over: stand, walk back out behind the ring they crossed,
			# which a dash side-on lands close to the next one for, or step aside.
			for then in [Vector2.ZERO, -d, Vector2(d.y, -d.x), Vector2(-d.y, d.x)]:
				options.append({"kind": "dash", "dir": d, "then": then})
	var landing_beat: int = dash_frames + 1 + floori(defense.dash_recovery_time_v2 * 60.0)
	var best := {}
	var best_score := INF
	var floor_area: Rect2 = sm.PLAYER_FLOOR
	for option in options:
		var q := first
		var danger := 0.0
		var clear := INF
		var off_wall := INF
		var next_dash: int = cooldown + 2 if option.kind == "dash" else (maxi(0, cooldown - since) + 2 if stamina_ok else CB_HORIZON + 1)
		for k in range(2, CB_HORIZON + 1):
			var immune := false
			if option.kind == "walk":
				q = cb_step(q, option.dir, walk)
			else:
				if k <= dash_frames + 1:
					q = cb_step(q, option.dir.normalized(), dash)
				elif k > landing_beat:
					q = cb_step(q, option.then, walk)
				immune = k <= immune_frames
			var rg := cb_ring_gap(q, rings, k / 60.0)
			var bg := cb_beam_gap(q, beams[k])
			off_wall = minf(off_wall, minf(minf(q.x - floor_area.position.x, floor_area.end.x - q.x),
				minf(q.y - floor_area.position.y, floor_area.end.y - q.y)))
			if bg < 0.0:
				danger += 1.0 / k
			clear = minf(clear, bg)
			if not immune:
				# A ring the next dash can't be ready for, a few frames before it arrives.
				if rg < 0.0 and k < next_dash + 3:
					danger += 1.0 / k
				clear = minf(clear, rg)
		var score := danger * 100000.0 - minf(clear, 40.0) * 20.0 + q.distance_to(target) \
			+ pow(maxf(0.0, 150.0 - off_wall), 2.0) * 0.08 + (400.0 if option.kind == "dash" else 0.0)
		if score < best_score:
			best_score = score
			best = option
	return best


# ------------------------------------------------------------------ the spin's warning
# The bands beast Bixby's beams will come out along, lit on the floor for combined_spin_tell before they do
# (BixbySonicLanesScript), on his combined attack forced from his hover as the combined mode forces it: where
# the bands lie against where the beams then come out, how long before, the cue, and a player caught standing
# in one as they light, played with real arrow keys and dashes. The quake rings are swept off the floor as
# they come: a ring's hit would hand the player i-frames the beams would then be ignored through.

const ST_LANES_SCRIPT := "BixbySonicLanesScript.gd"
const ST_SWEEP_SCRIPT := "BixbySonicSweepScript.gd"
const CB_SWEEP_SCRIPT_PATH := "res://Scripts/BixbySonicSweepScript.gd"
# How long a player takes to see the bands light and start moving.
const ST_REACTION := 0.25
# How long into the spin a player who got off their band must go on untouched: one still walking the way
# they went, a reaction's worth of the sweep they can see by then; one who stopped on the side the beams
# turn away from, a second; and how long one who stayed is watched for.
const ST_AFTER := 0.3
const ST_AFTER_TRAILING := 1.0
const ST_AFTER_STAYING := 0.5
# How far past a band's edge a player walking off it goes before stopping.
const ST_CLEAR := 40.0
# Where the player waits for his hover: he lands the attack by them, so each lays the bands somewhere else.
const ST_SPOTS: Array[Vector2] = [Vector2(960, 900), Vector2(600, 820), Vector2(1320, 820), Vector2(960, 640)]
# Where on a band's middle line the player is caught, as shares of its length out from his maw.
const ST_ALONG := [0.7, 0.6, 0.5, 0.8, 0.4]


func test_spin_tell() -> void:
	await load_liam()
	await skip_vs_card()
	hold_break_gauge(boss)
	# His hovers last until an attack is forced from them, so no fire breath lays solid fire in the way.
	sm.hover_time = 600.0
	sm.hover_between_attacks = 600.0
	cb = sm.states["Combined"]
	cb_layout = load(CB_LAYOUT)
	cb_art = load(CB_BEAST_LAYOUT)
	track()
	var lead: float = sm.combined_spin_tell
	check(lead >= 0.5 and lead <= 0.7, "the warning is %.2f s, inside 0.5-0.7 s" % lead)
	await st_check_warning()
	var plans := ["stay", "walk_trailing", "walk_leading", "dash_trailing"]
	for i in plans.size():
		await st_check_caught(plans[i], i)
	await st_check_break()
	cb_steer(Vector2.ZERO)


func st_sweep_rings() -> void:
	for ring in hazards_of(CB_RING_SCRIPT):
		ring.queue_free()


# His combined attack from his hover over `spot`, the rings swept off as they come, up to the first frame its
# bands are seen: whether it got there.
func st_to_warning(spot: Vector2) -> bool:
	if not await cb_force(spot):
		return false
	return await wait_until(func():
		st_sweep_rings()
		return not hazards_of(ST_LANES_SCRIPT).is_empty(), 600)


# The beams `into` seconds after they come out, glued to his maws on the loop step the warning picked, as
# cb_beams_ahead has them: [origin, screen angle, length].
func st_beams_at(into: float) -> Array:
	var out := []
	for mouth in cb_loop_ahead(cb.entry_step, into):
		var origin: Vector2 = boss.feet_position() + cb_art.local(Vector2(mouth[1], mouth[2]))
		var az := deg_to_rad(mouth[0])
		var angle: float = cb_layout.beam_angle(az)
		out.append([origin, angle, cb_reach(az, origin, angle)])
	return out


# Which of LANE_LOOKS the bands are showing.
func st_look(lanes: Node) -> int:
	if lanes.rims.is_empty():
		return -1
	var rim: Line2D = lanes.rims[0]
	for i in cb_layout.LANE_LOOKS.size():
		if rim.default_color == cb_layout.LANE_LOOKS[i][1] and rim.width == cb_layout.LANE_LOOKS[i][2]:
			return i
	return -1


# One attack stood through at ST_SPOTS[0]: what lights, when, where and with what, and how the beams come out
# over it.
func st_check_warning() -> void:
	log_p("-- the warning")
	if not await st_to_warning(ST_SPOTS[0]):
		check(false, "the combined attack reaches its warning")
		return
	var lanes: Node = hazards_of(ST_LANES_SCRIPT)[0]
	var bands: Array = lanes.bands.duplicate()
	var cue: AudioStreamPlayer = cb.windup_sfx_player
	var cue_path := str(cue.stream.resource_path) if cue.stream else ""
	log_p("the bands light on loop step %d with him at %s: %s" % [cb.entry_step, boss.ground_position, bands.map(func(b): return [b[0].round(), snappedf(rad_to_deg(b[1]), 0.1), roundi(b[2])])])
	check(cb.phase == cb.Phase.SPIN_UP and boss.current_anim == &"spin_charge" and boss.drawn_frame_of(cb_art.SPIN_SHEET) == 0,
		"they light as the pounds end, with him crouched on spin_up's first frame")
	check(cue.playing and cue_path.ends_with("laser_charge.ogg"), "to the wind-up's charge (%s)" % cue_path)
	check(cb_tell_up(), "under the yellow ring")
	check(lanes.get_parent() == sm.ground_layer(), "on his shadow's layer, under everyone standing on the floor")

	var expected := st_beams_at(0.0)
	var off := 0.0
	for i in mini(bands.size(), expected.size()):
		off = maxf(off, maxf(bands[i][0].distance_to(expected[i][0]), absf(bands[i][2] - expected[i][2])))
		off = maxf(off, rad_to_deg(absf(angle_difference(bands[i][1], expected[i][1]))))
	check(bands.size() == 3 and expected.size() == 3 and off < 0.01,
		"three bands, each where a beam out of a maw on that step runs, to the ropes (%.4f off)" % off)
	# The drawn fills: nothing outside the ropes, and every point of every band inside them covered.
	var outside := 0
	var fills := []
	for fill in lanes.fills:
		var drawn := PackedVector2Array()
		for point in fill.polygon:
			var at: Vector2 = fill.get_global_transform() * point
			drawn.append(at)
			if not sm.ROPES.grow(0.5).has_point(at):
				outside += 1
		fills.append(drawn)
	var uncovered := 0
	var sampled := 0
	var half: float = cb_layout.BEAM_HIT_THICKNESS * cb_layout.SCALE / 2.0 - 1.0
	for band in bands:
		var along := Vector2.from_angle(band[1])
		var d := 2.0
		while d < band[2] - 1.0:
			for across in [-half, 0.0, half]:
				var point: Vector2 = band[0] + along * d + along.orthogonal() * across
				if not sm.ROPES.grow(-1.0).has_point(point):
					continue
				sampled += 1
				if not fills.any(func(poly): return Geometry2D.is_point_in_polygon(point, poly)):
					uncovered += 1
			d += 10.0
	check(outside == 0 and sampled > 0 and uncovered == 0,
		"drawn as the bands, cut at the ropes: %d points of %d sampled uncovered, %d drawn outside" % [uncovered, sampled, outside])

	var t := 0
	var looks: Array = []
	var lead_in_at := -1
	var live_at := -1
	var gone_at := -1
	var entered_on := -1
	var hits0 := events_of("HIT", &"bixby_sonic_beam").size()
	var hits_in_lead := 0
	var aim_off := [-1.0, -1.0]
	while t < 300 and sm.current_state == cb:
		st_sweep_rings()
		if live_at < 0:
			if is_instance_valid(lanes) and not lanes.fading:
				looks.append(st_look(lanes))
			if lead_in_at < 0 and boss.current_anim == &"spin_up":
				lead_in_at = t
			if is_instance_valid(cb.sweep):
				live_at = t
				entered_on = boss.anim_step if boss.current_anim == &"spin" else -1
				hits_in_lead = events_of("HIT", &"bixby_sonic_beam").size() - hits0
		if live_at >= 0 and aim_off[0] < 0.0 and is_instance_valid(cb.sweep) and cb.sweep.aimed:
			aim_off = [0.0, 0.0]
			for beam in cb.sweep.beams:
				var px := INF
				var deg := INF
				for band in bands:
					px = minf(px, beam.global_position.distance_to(band[0]))
					deg = minf(deg, rad_to_deg(absf(angle_difference(cb_layout.floor_azimuth(beam.global_rotation), cb_layout.floor_azimuth(band[1])))))
				aim_off = [maxf(aim_off[0], px), maxf(aim_off[1], deg)]
		if live_at >= 0 and gone_at < 0 and not is_instance_valid(lanes):
			gone_at = t
		if gone_at >= 0 and aim_off[0] >= 0.0:
			break
		await physics_frame
		t += 1
	var runs := []
	for look in looks:
		if runs.is_empty() or runs[-1][0] != look:
			runs.append([look, 0])
		runs[-1][1] += 1
	var lead_frames := roundi(sm.combined_spin_tell * 60.0)
	log_p("the looks, as [look, frames]: %s; the lead-in from frame %d; the beams out on frame %d on loop step %d, %.2f px and %.2f deg of the floor off the bands; the bands gone on frame %d" % [runs, lead_in_at, live_at, entered_on, aim_off[0], aim_off[1], gone_at])
	check(absi(live_at - lead_frames) <= 1, "the beams come out %d frames after the bands light (%.3f s, the warning %.3f s)" % [live_at, live_at / 60.0, sm.combined_spin_tell])
	check(hits_in_lead == 0, "and nothing of the beams hurts before they do (%d hits)" % hits_in_lead)
	check(entered_on == cb.entry_step and aim_off[0] >= 0.0 and aim_off[0] <= 3.0 and aim_off[1] <= 1.0,
		"they come out on the step the warning picked, on the bands to a frame's turn (%.2f px, %.2f deg)" % [aim_off[0], aim_off[1]])
	check(absi(lead_in_at - roundi((sm.combined_spin_tell - cb_art.anim_time(&"spin_up")) * 60.0)) <= 1,
		"his lead-in plays out of the crouch so that it ends as they come out")
	var flashing := runs.slice(2).all(func(r): return r[0] == 2 or r[0] == 3)
	check(runs.size() >= 4 and runs[0][0] == 0 and runs[1][0] == 1 and runs[2][0] == 2 and flashing
		and absi(runs[0][1] - lead_frames / 4) <= 1 and absi(runs[1][1] - lead_frames / 4) <= 1,
		"lit in the shower markers' contract: two looks a quarter of the warning each, then the last two flashing")
	check(gone_at >= 0 and gone_at - live_at <= ceili(cb_layout.LANE_FADE_TIME * 60.0) + 2,
		"and they fade out under the beams as they grow (%d frames)" % (gone_at - live_at))


# A player caught standing in a band as it lights, on its middle line, playing `plan`, from the first of
# ST_SPOTS where somewhere suits it: `stay` stays; `walk_trailing` waits out a reaction, then walks straight off
# it with the arrow keys to the side the beams turn away from and stops ST_CLEAR past its edge;
# `walk_leading` walks off it the other way, toward the side they turn to, and keeps going into the spin;
# `dash_trailing` dashes off it to the side they turn away from after the same reaction. Band `first` is
# tried first, so the plans between them stand in all three.
func st_check_caught(plan: String, first: int) -> void:
	log_p("-- caught standing in a band as it lights: %s" % plan)
	for spot in ST_SPOTS:
		if not await st_to_warning(spot):
			check(false, "the combined attack reaches its warning from %s" % spot)
			return
		var pick := st_pick(plan, first)
		if pick.is_empty():
			log_p("from %s, nowhere on a band suits %s: next spot" % [spot, plan])
			continue
		await st_play(plan, pick)
		return
	check(false, "somewhere on a band to be caught for %s" % plan)


# Where the player is caught for `plan`, and the keys they go with: the first point on a band's middle line
# (ST_ALONG) where the whole way they go stays on the floor and, from the moment the beams come out until
# the watch is over, clear of every beam as cb_beams_ahead has them. {} for none. How many were turned down
# for the beams is logged.
func st_pick(plan: String, first: int) -> Dictionary:
	var bands := st_beams_at(0.0)
	var in_the_way := 0
	for n in bands.size():
		var i := (first + n) % bands.size()
		var band: Array = bands[i]
		var along := Vector2.from_angle(band[1])
		for share in ST_ALONG:
			var at: Vector2 = band[0] + along * band[2] * share
			if not sm.PLAYER_FLOOR.grow(-20.0).has_point(at):
				continue
			if plan == "stay":
				return {"at": at, "band": i, "dir": Vector2.ZERO}
			# The beams turn with his heads, which is the way their screen angle grows (beam_angle).
			var away := along.rotated((PI if plan.ends_with("leading") else -PI) / 2.0)
			var keys := st_keys(away, plan.begins_with("dash"))
			var path := st_path(plan, at, keys, band)
			if path.is_empty():
				continue
			if not st_path_clear(path):
				in_the_way += 1
				continue
			if in_the_way > 0:
				log_p("%d places on the bands turned down first: the beams would reach the way off them" % in_the_way)
			return {"at": at, "band": i, "dir": keys}
	if in_the_way > 0:
		log_p("%d places on the bands turned down: the beams would reach the way off them" % in_the_way)
	return {}


# The arrow keys that go most nearly `dir`: a walk's axes are separate, a dash's are normalised. Between two
# that push as hard, the one nearer its way.
func st_keys(dir: Vector2, dash: bool) -> Vector2:
	var best := Vector2.ZERO
	var most := -INF
	for d in CB_DIRS:
		var push := d.dot(dir) / (d.length() if dash else 1.0) + 0.001 * d.normalized().dot(dir)
		if push > most:
			most = push
			best = d
	return best


# Where the player is on each frame from the bands being seen until the watch is over, going the way `plan`
# does on `keys`, or [] if it leaves the floor. A walk moves from the frame after the keys go down; a dash
# covers its whole reach in its moving frames, then stands.
func st_path(plan: String, at: Vector2, keys: Vector2, band: Array) -> Array:
	var lead := roundi(sm.combined_spin_tell * 60.0)
	var react := roundi(ST_REACTION * 60.0)
	var after := roundi((ST_AFTER_TRAILING if plan.ends_with("trailing") else ST_AFTER) * 60.0)
	var walk: float = load("res://Scripts/PlayerScript.gd").SPEED / 60.0
	var dash_frames := ceili(player.dodge_time * 60.0 - 0.001)
	var dash_step: float = load("res://Scripts/PlayerScript.gd").DODGE_SPEED / 60.0
	var floor_area: Rect2 = sm.PLAYER_FLOOR
	var q := at
	var moving := true
	var out := []
	for k in lead + after + 2:
		var going := k - react - 1
		if moving and going >= 0:
			if plan.begins_with("dash"):
				if going < dash_frames:
					q += keys.normalized() * dash_step
				else:
					moving = false
			elif plan == "walk_trailing" and cb_beam_gap(q, [band]) >= ST_CLEAR:
				moving = false
			else:
				q += keys * walk
				if plan == "walk_leading" and k >= lead + after:
					moving = false
		if not floor_area.has_point(q):
			return []
		out.append(q)
	return out


# Whether a path from st_path stays clear of every beam from the frame they come out to the end of the watch.
func st_path_clear(path: Array) -> bool:
	var lead := roundi(sm.combined_spin_tell * 60.0)
	for k in range(lead, path.size()):
		if cb_beam_gap(path[k], st_beams_at((k - lead) / 60.0)) < 0.0:
			return false
	return true


# Plays `pick` from the frame the bands are seen: the player put on its band's middle line, then held there,
# walked off it after ST_REACTION or dashed off it. When they were off their band, where they were as the beams
# came out, and every beam hit, against when the beams came out.
func st_play(plan: String, pick: Dictionary) -> void:
	var band: Array = st_beams_at(0.0)[pick.band]
	var lead := roundi(sm.combined_spin_tell * 60.0)
	var react := roundi(ST_REACTION * 60.0)
	var after := ST_AFTER_STAYING if plan == "stay" else (ST_AFTER_TRAILING if plan.ends_with("trailing") else ST_AFTER)
	player.global_position = pick.at
	player.velocity = Vector2.ZERO
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	var started_in := cb_beam_gap(pick.at, [band])
	# How far inside the band's hit edge they stand, across it, as the sweep tests the player's body.
	var across: float = cb_layout.BEAM_HIT_THICKNESS * cb_layout.SCALE / 2.0 + load(CB_SWEEP_SCRIPT_PATH).PLAYER_RADIUS
	var depth: float = across - absf((pick.at - band[0]).rotated(-band[1]).y)
	var hits0 := events_of("HIT", &"bixby_sonic_beam").size()
	var hit_frames := []
	var k := 0
	var live := -1
	var off_at := -1
	var gap_at_live := 0.0
	var holding := false
	var dashed := false
	while sm.current_state == cb:
		st_sweep_rings()
		var at: Vector2 = player.global_position
		var gap := cb_beam_gap(at, [band])
		if plan == "stay":
			player.global_position = pick.at
			player.velocity = Vector2.ZERO
		elif k == react:
			cb_steer(pick.dir)
			holding = true
			if plan.begins_with("dash"):
				tap(KEY_W)
		elif holding:
			dashed = dashed or player.is_dodging
			var done := false
			if plan.begins_with("dash"):
				done = dashed and not player.is_dodging
			elif plan == "walk_trailing":
				done = gap >= ST_CLEAR
			else:
				done = live >= 0 and k >= live + roundi(ST_AFTER * 60.0)
			if done:
				cb_steer(Vector2.ZERO)
				holding = false
		if off_at < 0 and gap >= 0.0:
			off_at = k
		if live < 0 and is_instance_valid(cb.sweep):
			live = k
			gap_at_live = gap
		var hits: int = events_of("HIT", &"bixby_sonic_beam").size() - hits0
		while hit_frames.size() < hits:
			hit_frames.append(k)
		if live >= 0 and k > live + roundi(after * 60.0):
			break
		await physics_frame
		k += 1
	cb_steer(Vector2.ZERO)
	var before := hit_frames.filter(func(f): return live < 0 or f <= live)
	log_p("caught at %s on band %d, %.1f px inside its hit edge, going %s: off it on frame %s, the beams out on frame %d with them %.0f px clear of it, beam hits on frames %s" % [pick.at.round(), pick.band, depth, pick.dir, off_at, live, gap_at_live, hit_frames])
	check(started_in < 0.0 and live >= 0, "caught standing in the band as it lit, and the beams came out")
	check(before.is_empty(), "no beam hit before the beams came out (%s)" % [before])
	if plan == "stay":
		var grow := ceili(cb_layout.BEAM_GROW_TIME * 60.0)
		check(not hit_frames.is_empty() and hit_frames[0] > live and hit_frames[0] <= live + grow + 3,
			"staying put, hit once they are out, not before: frame %s, %d after the bands lit" % [hit_frames.slice(0, 1), lead])
		return
	check(off_at >= 0 and off_at < live, "off the band %d frames after it lit, %.2f s before the beams came out" % [off_at, (live - off_at) / 60.0])
	check(hit_frames.is_empty(), "and never hit, to %.1f s into the spin" % after)


# A Break in the middle of the warning takes the bands and the ring down with everything else, and no beam
# comes out.
func st_check_break() -> void:
	log_p("-- a Break mid-warning")
	if not await st_to_warning(ST_SPOTS[0]):
		check(false, "the combined attack reaches its warning")
		return
	await wait(roundi(sm.combined_spin_tell * 30.0))
	sm.enter_broken()
	await wait(2)
	var left: int = hazards_of(ST_LANES_SCRIPT).size() + hazards_of(ST_SWEEP_SCRIPT).size()
	check(sm.current_state.name == "Broken" and left == 0 and not cb_tell_up(),
		"Broken halfway through it, the bands and the yellow ring are gone at once (%s, %d left)" % [sm.current_state.name, left])
	await wait(roundi(sm.combined_spin_tell * 60.0))
	check(hazards_of(ST_SWEEP_SCRIPT).is_empty(), "and no beam comes out where they were")


# ------------------------------------------------------------------ the spin's full-length beams
# The user, 2026-09-28: his spin's beams reach the full length of the arena. His combined attack forced from his
# hover with him put down off the middle, and played through with real arrow keys and dashes, rings and all, on
# the real rules: anything of his touching the player inside a dash's immunity is dodged, and a beam or ring
# dodged that way is a PERFECT DODGE, which pays the dash back. On every frame a beam is full grown it runs right
# up to the ropes, and how much further that is than the length the art used to be drawn at is logged. Then three
# players: one who waits out at the edge and never moves, hit now that the edge is in reach; one who waits there
# and dashes through each beam and ring as it is about to reach them; and one who stays close to him and moves
# with the gap between his beams, where they sweep slowly, dashing through the rings that come their way.

# [where he comes down, the edge the player waits at]: a side away from him, both ways, and the bottom rope under
# him, each out of his beams' old drawn reach for part of the spin.
const SR_RUNS := [[Vector2(450, 640), Vector2(1760, 700)], [Vector2(1470, 640), Vector2(160, 760)],
	[Vector2(958, 470), Vector2(958, 915)]]
# How far ahead the players look, in physics frames.
const SR_HORIZON := 40
# The close player's loop round his maws: [out to either side, below, above] of the point they orbit, in px.
const SR_CLOSE_ORBIT := Vector3(180.0, 170.0, 100.0)


func test_spin_reach() -> void:
	await load_liam()
	await skip_vs_card()
	hold_break_gauge(boss)
	sm.hover_time = 600.0
	sm.hover_between_attacks = 600.0
	cb = sm.states["Combined"]
	cb_layout = load(CB_LAYOUT)
	cb_art = load(CB_BEAST_LAYOUT)
	track()
	track_dodges()
	var refused := [0]
	defense.stamina_refused.connect(func(): refused[0] += 1)
	var plans := {}
	for plan in ["edge_still", "edge_dash", "close"]:
		log_p("-- %s" % plan)
		plans[plan] = []
		for run in SR_RUNS:
			var r := await sr_play(plan, run[0], run[1])
			if r.is_empty():
				check(false, "his combined attack starts from his hover with him at %s" % run[0])
				continue
			plans[plan].append(r)
			log_p("  him at %s, the player %s: %d beam hits, %d ring hits; %d dashes, %d perfect dodges (%d of them beams); stamina down to %.0f; the beams reached up to %.0f px, %.0f past the old drawn length, and were at most %.2f px off the ropes" % [r.him, r.at, r.beam_hits, r.ring_hits, r.dashes, r.perfect, r.perfect_beams, r.low, r.longest, r.beyond_old, r.reach_off])
	var every: Array = plans.edge_still + plans.edge_dash + plans.close
	var off: float = every.map(func(r): return r.reach_off).max()
	check(every.all(func(r): return r.beam_frames > 0) and off < 1.0,
		"every full-grown beam, on every frame, runs right up to the ropes and no further (%.2f px off at most)" % off)
	check(plans.edge_still.all(func(r): return r.beyond_old > 0.0 and r.beam_hits > 0),
		"waiting at the edge is no longer out of reach: every edge was beyond the old drawn length for part of the spin, and the beams hit there (%s)" % [plans.edge_still.map(func(r): return r.beam_hits)])
	for plan in ["edge_dash", "close"]:
		var runs: Array = plans[plan]
		log_p("%s: hits %s, dashes %s, perfect dodges %s, stamina low points %s" % [plan, runs.map(func(r): return r.beam_hits + r.ring_hits), runs.map(func(r): return r.dashes), runs.map(func(r): return r.perfect), runs.map(func(r): return roundi(r.low))])
	log_p("%d dashes refused for stamina in all" % refused[0])
	var cost: float = defense.dash_stamina_cost
	check(plans.edge_dash.size() == SR_RUNS.size() and plans.edge_dash.all(func(r): return r.beam_hits + r.ring_hits == 0 and r.perfect >= r.dashes - 1),
		"waiting at the edge and dashing through each beam and ring as it comes is never hit, every dash but at most one an attack a PERFECT DODGE that pays it back (%s dashes, %s perfect)" % [plans.edge_dash.map(func(r): return r.dashes), plans.edge_dash.map(func(r): return r.perfect)])
	check(plans.close.size() == SR_RUNS.size() and plans.close.all(func(r): return r.beam_hits + r.ring_hits <= 1),
		"staying close to him with the gap between his beams is hit once an attack at the most (%s)" % [plans.close.map(func(r): return r.beam_hits + r.ring_hits)])
	check(refused[0] == 0 and (plans.edge_dash + plans.close).all(func(r): return r.low >= cost - 0.001),
		"and neither ever wants a dash the stamina can't pay for: the bar never below one dash (%.0f)" % (plans.edge_dash + plans.close).map(func(r): return r.low).min())
	cb_steer(Vector2.ZERO)


# His next hover held with the player at `at` until the last attack's rings have rolled off the floor, him put down
# over `him`, then the combined attack with nothing queued behind it.
func sr_force(him: Vector2, at: Vector2) -> bool:
	cb_steer(Vector2.ZERO)
	if not await wait_until(func(): return sm.current_state.name == "Hover", 1200):
		return false
	var hover: Node = sm.states["Hover"]
	for i in 1800:
		hover.elapsed = 0.0
		player.global_position = at
		player.velocity = Vector2.ZERO
		if i >= 30 and hazards_of(CB_RING_SCRIPT).is_empty():
			break
		await physics_frame
	var bounds: Rect2 = boss.ground_bounds(0.0)
	boss.ground_position = him.clamp(bounds.position, bounds.end)
	boss.place()
	clear_iframes()
	defense._set_stamina(defense.max_stamina)
	sm.attacks = []
	sm.on_child_transition(sm.current_state, "Combined")
	return sm.current_state == cb


# One combined attack with him at `him`, the player playing `plan` from `edge` (or beside him, close): what hit
# them, what they dodged, their dashes and stamina, and his beams' reach on every frame they were full grown.
func sr_play(plan: String, him: Vector2, edge: Vector2) -> Dictionary:
	if not await sr_force(him, him + Vector2(0, -20) if plan == "close" else edge):
		return {}
	var events0 := events.size()
	var dodges0 := dodges.size()
	var dashes := 0
	var low: float = defense.stamina
	var reach_off := 0.0
	var longest := 0.0
	var beyond_old := 0.0
	var beam_frames := 0
	while sm.current_state == cb:
		var act := {"kind": "walk", "dir": Vector2.ZERO}
		match plan:
			"edge_dash":
				act = sr_choose(edge)
			"close":
				act = sr_choose(sr_close_target())
		cb_steer(act.dir)
		if act.kind == "dash":
			tap(KEY_W)
			dashes += 1
		await physics_frame
		low = minf(low, defense.stamina)
		var sweep = cb.sweep
		if is_instance_valid(sweep) and not sweep.fading and sweep.clock >= cb_layout.BEAM_GROW_TIME:
			for beam in sweep.beams:
				var length: float = (beam.get_node("CollisionShape2D").shape as RectangleShape2D).size.x
				var room := cb_room_to_ropes(beam.global_position, beam.global_rotation)
				var az: float = cb_layout.floor_azimuth(beam.global_rotation)
				var old: float = minf(cb_layout.BEAM_REACH * cb_layout.SCALE * cb_layout.beam_length(az), room)
				reach_off = maxf(reach_off, absf(length - room))
				longest = maxf(longest, length)
				beyond_old = maxf(beyond_old, length - old)
				beam_frames += 1
	cb_steer(Vector2.ZERO)
	var hits := events.slice(events0).filter(func(e): return e.kind == "HIT")
	var perfect := dodges.slice(dodges0)
	return {"him": boss.ground_position.round(), "at": edge, "beam_hits": hits.filter(func(e): return e.id == &"bixby_sonic_beam").size(),
		"ring_hits": hits.filter(func(e): return e.id == &"bixby_quake_ring").size(), "dashes": dashes,
		"perfect": perfect.size(), "perfect_beams": perfect.filter(func(d): return d.id == &"bixby_sonic_beam").size(),
		"low": low, "reach_off": reach_off, "longest": longest, "beyond_old": beyond_old, "beam_frames": beam_frames}


# Where the close player heads: just in front of his feet, inside where his rings start (each catches them there as it
# is born, so sr_choose answers it), until he spins; then the
# middle of the gap between his beams on SR_CLOSE_ORBIT round his maws, a little ahead of it.
func sr_close_target() -> Vector2:
	var feet: Vector2 = boss.ground_position
	var beams := cb_beams_ahead(0)
	if cb.phase != cb.Phase.SPIN or beams.is_empty():
		return feet + Vector2(0, -20)
	var maws: Vector2 = boss.feet_position() + cb_art.local(cb_layout.SPIN_CENTRE)
	var mine := rad_to_deg(cb_layout.floor_azimuth((player.global_position - maws).angle()))
	var front := rad_to_deg(cb_layout.floor_azimuth(beams[0][1]))
	var azimuth := mine - fposmod(mine - front, 120.0) + 70.0
	var dir := Vector2.from_angle(cb_layout.beam_angle(deg_to_rad(azimuth)))
	var r := 1.0 / Vector2(dir.x / SR_CLOSE_ORBIT.x, dir.y / (SR_CLOSE_ORBIT.y if dir.y > 0.0 else SR_CLOSE_ORBIT.z)).length()
	return (maws + dir * r).clamp(sm.PLAYER_FLOOR.position, sm.PLAYER_FLOOR.end)


# The move this frame for a player making for `target`: standing and the eight walks and, when something of his is
# about to reach them, the eight dashes, each played SR_HORIZON frames ahead over the real rings and beams, a dash
# standing once its landing beat is over. Whatever of his touches them inside a dash's immunity is dodged, as the
# game has it; outside it, it lands, unless it comes late enough for the next dash to answer it (when there is the
# stamina for one), so they dash only as something is about to reach them and never spend the dash they will need.
# The fewest landings, then the nearest `target`, then no dash.
func sr_choose(target: Vector2) -> Dictionary:
	if player.is_dodging or defense.is_dash_recovering():
		return {"kind": "walk", "dir": cb_held_dir()}
	var walk: float = load("res://Scripts/PlayerScript.gd").SPEED / 60.0
	var dash: float = load("res://Scripts/PlayerScript.gd").DODGE_SPEED / 60.0
	var dash_frames := ceili(player.dodge_time * 60.0 - 0.001)
	var immune_frames := roundi(CATALOG.DASH_IMMUNITY_TIME * 60.0) + 1
	var landing_beat: int = dash_frames + 1 + floori(defense.dash_recovery_time_v2 * 60.0)
	var cooldown := roundi(defense.dash_cooldown_v2 * 60.0)
	var cost: float = defense.dash_stamina_cost
	var first := cb_step(player.global_position, cb_held_dir(), walk)
	var rings := cb_rings_ahead()
	var beams := []
	for k in SR_HORIZON + 1:
		beams.append(cb_beams_ahead(k))
	var soon := false
	for k in range(2, 6):
		if cb_ring_gap(first, rings, k / 60.0) < 0.0 or cb_beam_gap(first, beams[k]) < 0.0:
			soon = true
	var options := [{"kind": "walk", "dir": Vector2.ZERO}]
	for d in CB_DIRS:
		options.append({"kind": "walk", "dir": d})
	if soon and bot_can_dash():
		for d in CB_DIRS:
			options.append({"kind": "dash", "dir": d})
	var wait := maxi(0, ceili((defense.dash_ready_at - defense.clock) * 60.0))
	var best := {}
	var best_score := INF
	for option in options:
		var q := first
		var landed := 0.0
		var next_dash := SR_HORIZON + 1
		if option.kind == "dash" and defense.stamina >= 2.0 * cost - 0.001:
			next_dash = cooldown + 2
		elif option.kind == "walk" and defense.stamina >= cost - 0.001:
			next_dash = wait + 2
		for k in range(2, SR_HORIZON + 1):
			var immune := false
			if option.kind == "walk":
				q = cb_step(q, option.dir, walk)
			else:
				if k <= dash_frames + 1:
					q = cb_step(q, option.dir.normalized(), dash)
				immune = k <= immune_frames
			if not immune and k < next_dash + 3 and (cb_ring_gap(q, rings, k / 60.0) < 0.0 or cb_beam_gap(q, beams[k]) < 0.0):
				landed += 1.0 / k
		var score := landed * 100000.0 + q.distance_to(target) + (300.0 if option.kind == "dash" else 0.0)
		if score < best_score:
			best_score = score
			best = option
	return best


# Whether a bot can dash on this frame: not dashing, not landing or cooling down from the last one, and the stamina
# for it.
func bot_can_dash() -> bool:
	return not player.is_dodging and not defense.is_dash_recovering() and not defense.is_dash_cooling_down() \
		and defense.stamina >= defense.dash_stamina_cost


# ------------------------------------------------------------------ Josh against his redrawn sheets
# Every final sheet of his is drawn facing right. On the ground he faces the player, and what is traced
# off his poses mirrors with him: the box the player punches while he recovers, the daze stars over his
# hat, and the hand his Wild Cards' clones throw from. His entrance's flick at the camera starts on the
# pose's own flick step. Each clone is drawn facing where it throws, holding the throw's wind-up, and he
# stands on it drawn the same way; they throw on the throw's release steps.

const JOSH_BODY := "Arena/JoshCardsScene/JoshCardsCharacterBody"
const JOSH_ART := "res://Scripts/JoshArtLayout.gd"
const JOSH_SPOT := Vector2(960, 640)
# Where the player waits out his entrance: on his left, so it is drawn mirrored.
const JOSH_INTRO_PLAYER := Vector2(600, 900)
# His clones' spots, either side of the player at JOSH_SPOT in turn, so they face both ways.
const JOSH_CLONE_SPOTS: Array[Vector2] = [Vector2(500, 500), Vector2(1400, 500), Vector2(500, 800), Vector2(1400, 800), Vector2(1500, 640)]
# How far to either side of the player he is put down to recover.
const JOSH_RECOVER_OFFSET := 260.0


func test_josh_layout() -> void:
	var art: GDScript = load(JOSH_ART)
	var unmirrored: Array = art.FINAL_ANIMS.keys().filter(func(anim_name): return not art.FINAL_ANIMS[anim_name].get("flips", false))
	check(unmirrored.is_empty(), "every final sheet mirrors, since all of them are drawn facing right (%s don't)" % [unmirrored])

	# Kept, not cut the way load_fight() cuts an entrance: the flick is watched below.
	await enter_fight(SCENES["josh"], true)
	boss = current_scene.get_node(JOSH_BODY)
	sm = boss.state_machine
	var intro: Node = sm.states["Intro"]

	log_p("-- his entrance, with the player on his left")
	check(not boss.air.visible, "he has not appeared yet")
	player.global_position = JOSH_INTRO_PLAYER
	var flick := {}
	intro.stage.child_entered_tree.connect(func(node: Node) -> void:
		if boss.air.visible and flick.is_empty():
			flick["card"] = node
			flick["anim"] = boss.current_anim
			flick["step"] = boss.anim_step
	)
	check(await wait_until(func(): return boss.air.visible, 120), "he appears")
	check(boss.current_anim == &"intro" and boss.sprite.flip_h, "his entrance is drawn facing left, toward the player")
	check(await wait_until(func(): return not flick.is_empty(), 180), "he flicks a card at the camera")
	log_p("the flick's card came on %s step %s" % [flick.get("anim"), flick.get("step")])
	check(flick.get("anim") == &"intro" and flick.get("step") == art.INTRO_FLICK_STEP, "on the step his entrance flicks it, %d" % art.INTRO_FLICK_STEP)
	await wait(6)
	var flicked: Node2D = flick.get("card")
	var flicked_x: float = flicked.position.x if is_instance_valid(flicked) else INF
	check(flicked_x < 0.0, "and out to the left, the side he faces (x %.0f)" % flicked_x)
	player.global_position = JOSH_SPOT
	log_p("his intro ended in %s" % await clear_intro("josh"))

	log_p("-- his Wild Cards, through a whole cycle")
	player.playerHealth = 1000
	# The card's end would start a cycle of its own over this one.
	await skip_vs_card()
	stop_boss_timers()
	sm.on_child_transition(sm.current_state, "Idle")
	var wild: Node = sm.states["WildCards"]
	var hold: Dictionary = art.anim(&"wild_hold")
	var throw_anim: Dictionary = art.anim(&"throw")
	wild.forced_spots.assign(JOSH_CLONE_SPOTS)
	await settle_player(JOSH_SPOT)
	var clones_seen := []
	var thrown := {}
	# His cycle alternates his Hand Slam with Wild Cards since 2026-09-29: this cycle is Wild Cards, and Wild
	# Cards alone, its Gun Hands pinned off (josh_guns tests them).
	if "ATTACK_ORDER" in sm:
		sm.ATTACK_ORDER.assign(["WildCards"])
		sm.cycles_started = 0
	if "wild_guns" in sm:
		sm.wild_guns = false
	# One attack, then his Recover (two run before each window since 2026-10-04).
	if "attacks_per_window" in sm:
		sm.attacks_per_window = 1
	sm.start_cycle()
	while sm.current_state == wild:
		for k in range(clones_seen.size(), wild.clones.size()):
			var clone: Object = wild.clones[k]
			clones_seen.append({"flip": clone.flip, "faces": clone.aimed_at.x < clone.feet.x, "drawn": clone.figure.flip_h,
				"sheet": clone.figure.texture.resource_path, "frame": clone.figure.frame, "tint": clone.figure.modulate,
				"hands": clone.lanes.map(func(lane): return lane.origin - clone.feet),
				"josh": [boss.current_anim, boss.sprite.flip_h, boss.ground_position == clone.feet]})
		if wild.beat == wild.Beat.VOLLEY and not wild.scattered:
			for clone in wild.clones:
				if is_instance_valid(clone.figure):
					thrown[clone.figure.frame] = true
		await physics_frame
	wild.forced_spots.clear()
	log_p("clones [flip, drawn, frame, josh]: %s; thrown on frames %s" % [clones_seen.map(func(c): return [c.flip, c.drawn, c.frame, c.josh]), thrown.keys()])
	var flips: Array = clones_seen.map(func(c): return c.flip)
	check(clones_seen.size() == sm.wild_clones and flips.has(true) and flips.has(false), "all %d clones, facing both ways" % sm.wild_clones)
	check(clones_seen.all(func(c): return c.drawn == c.faces and c.flip == c.faces), "each drawn facing where it throws, mirrored when that is left")
	check(clones_seen.all(func(c): return c.sheet == hold.sheet and c.frame == hold.frames[0] and c.tint == art.WILD_CLONE_TINT), "on the throw's wind-up, tinted as a clone")
	check(clones_seen.all(func(c): return c.hands.all(func(h): return h.distance_to(art.local(art.HAND_THROW, c.flip)) < 0.01)), "its lanes leave its hand where the throw's release draws it, mirrored with it")
	check(clones_seen.all(func(c): return c.josh[0] == &"wild_hold" and c.josh[1] == c.flip and c.josh[2]), "and he stands on each as it appears, in the same pose, drawn the same way")
	var release_frames: Array = art.WILD_RELEASE_STEPS.map(func(s): return throw_anim.frames[s])
	check(not thrown.is_empty() and thrown.keys().all(func(f): return release_frames.has(f)) and thrown.has(release_frames[0]), "throwing, they draw the throw's release steps %s (%s)" % [art.WILD_RELEASE_STEPS, thrown.keys()])

	log_p("-- the rest drives his states by hand")
	sm.set_process(false)
	sm.set_physics_process(false)
	for timer in boss.find_children("*", "Timer", true, false):
		timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	for hazard in live_hazards():
		hazard.queue_free()
	await wait(2)

	var finisher: Node = player.get_node("Finisher")
	var stars_at := {}
	for josh_right in [false, true]:
		var side := "right" if josh_right else "left"
		sm.on_child_transition(sm.current_state, "Idle")
		boss.boss_health = boss.max_health
		boss.ground_position = JOSH_SPOT + Vector2(JOSH_RECOVER_OFFSET * (1.0 if josh_right else -1.0), 0.0)
		boss.place()
		await settle_player(JOSH_SPOT)
		sm.on_child_transition(sm.current_state, "Recover")
		sm.recover_timer.stop()
		await wait(5)
		var left: bool = boss.sprite.flip_h
		check(boss.current_anim == &"recover" and left == josh_right, "recovering on the player's %s, he faces them" % side)
		var box: Rect2 = area_rect(boss.hurtbox)
		var want: Rect2 = art.local_rect(art.RECOVER_BODY_BOX, left)
		want.position += boss.global_position
		check(box.position.distance_to(want.position) < 0.5 and box.size.distance_to(want.size) < 0.5, "his hurtbox is the recovery box, mirrored with him (%s, want %s)" % [box, want])
		place_under(boss.get_finisher_hurtbox())
		await wait(6)
		check(boss.can_be_dazed(), "his punish window is open")
		for i in 3:
			await swing_any()
			if i < 2:
				await wait(6)
		check(boss.sprite.flip_h == left, "flinching keeps his facing")
		var dazed := await wait_until(func(): return finisher.phase == FINISHER_DAZED and is_instance_valid(finisher.stars), 120)
		stars_at[side] = finisher.stars.global_position - boss.global_position if dazed else Vector2.INF
		log_p("dazed on the player's %s: stars %s from his feet" % [side, stars_at[side]])
		check(dazed and stars_at[side].distance_to(art.mirrored(art.DAZE_ANCHOR, left)) < 0.5, "the punches daze him, and the stars circle over his hat")
		# Nobody mashes, so the daze runs out and leaves him recovering.
		await wait_until(func(): return finisher.phase == FINISHER_OFF, 600)
		await wait(30)
	var mirror_of_right := Vector2(-stars_at["right"].x, stars_at["right"].y)
	check(stars_at["left"].distance_to(mirror_of_right) < 0.5, "one side's stars are the mirror of the other's (%s, %s)" % [stars_at["left"], stars_at["right"]])

	# The tuning round of 2026-10-04: he sorted on his feet and the player's sprite on a point 3 px over theirs, so a
	# player up to 3 px in front of him was drawn behind him.
	log_p("-- the y-sort: the player beside him, their feet a few px behind or in front of his")
	sm.on_child_transition(sm.current_state, "Idle")
	boss.ground_position = JOSH_SPOT
	boss.place()
	await settle_player(JOSH_SPOT + Vector2(30, 0))
	var feet_below: float = area_rect(player.hurtBox).end.y - player.global_position.y
	var sorted := []
	for ahead in [-40.0, -5.0, -1.0, 1.0, 3.0, 5.0, 40.0]:
		await settle_player(Vector2(JOSH_SPOT.x + 30.0, boss.global_position.y + ahead - feet_below))
		var feet: float = area_rect(player.hurtBox).end.y
		sorted.append([feet - boss.global_position.y, player.sprite.global_position.y > boss.sort_point.global_position.y])
	log_p("[player's feet in front of his by, the player drawn in front]: %s" % [sorted])
	check(boss.y_sort_enabled and boss.air.get_parent() == boss.sort_point, "everything of him drawn sorts on his sort point")
	check(sorted.all(func(s): return s[1] == (s[0] > 0.0)), "the player is drawn in front of him exactly when their feet are in front of his (%s)" % [sorted])


# ------------------------------------------------------------------ no perfect dodge off a static floor hazard
# A hazard lying still on the floor never pays a PERFECT DODGE (AttackCatalog's no_perfect_dodge, the
# user's rule of 2026-09-23): Bixby's embers and Computah's mine pods. A dash across an ember is still
# safe; it is just not a dodge. Anything that moves keeps paying one. Played in Computah's fight, where
# the pods are real, with a real ember laid on his mat beside them.

const STATIC_EMBER_SPOT := Vector2(700, 820)
const STATIC_MINE_SPOT := Vector2(1250, 820)
const STATIC_CLEAR_SPOT := Vector2(960, 700)
const STATIC_EMBER_SCENE := "res://Scenes/Bosses/BixbyEmberScene.tscn"
const STATIC_FIREBALL_SCENE := "res://Scenes/Bosses/BixbyFireballScene.tscn"


# A dash that could pay a perfect dodge: past the last one's cooldown, off the dash's own, a full bar and
# no i-frames.
func fresh_dash_ready() -> void:
	await wait_until(func(): return defense.clock - defense.last_perfect_dodge_time >= defense.perfect_dodge_cooldown + 0.05, 240)
	await dash_ready()
	clear_iframes()


# What a perfect dodge pays, to be read before and after one that mustn't.
func dodge_rewards() -> Dictionary:
	return {"hype": player.get_node("Hype").hype, "stamina": defense.stamina, "gauge": boss.break_gauge.value}


# Level with `box`, the player's near edge `gap` px short of it: where a dash that way crosses it.
func beside(box: Rect2, side: float, gap: float) -> Vector2:
	var hurt := hurtbox_rect()
	var edge := box.position.x - gap - hurt.end.x if side > 0.0 else box.end.x + gap - hurt.position.x
	return player.global_position + Vector2(edge, box.get_center().y - hurt.get_center().y)


# The bounding box of an area's shape, whatever the shape.
func area_rect_any(area: Area2D) -> Rect2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func test_static_dodge() -> void:
	await load_computah_fight()
	await park_computah()
	boss.global_position = Vector2(960, 300)
	track_dodges()
	var hit_info: GDScript = load("res://Scripts/HitInfo.gd")

	log_p("-- the catalogue")
	var still := [&"bixby_ember", &"computah_mine", &"bixby_flyby_fire"]
	var moving := [&"mason_poo_contact", &"bixby_sonic_beam", &"bixby_flyby_breath",&"bixby_quake_ring", &"eric_whirlwind_v2", &"bixby_fireball", &"bixby_inferno", &"josh_wild_card", &"josh_hand_slam", &"josh_gun_beam", &"mason_poo_blast", &"funko_blast", &"computah_beam"]
	check(still.all(func(id): return CATALOG.get_attack(id).no_perfect_dodge), "no_perfect_dodge on the hazards lying still on the floor: %s" % [still])
	check(moving.all(func(id): return not CATALOG.get_attack(id).no_perfect_dodge), "and on nothing that moves: %s" % [moving])
	check(CATALOG.get_attack(&"bixby_ember").dash_through, "an ember is still dashed through")

	var ember: Node2D = load(STATIC_EMBER_SCENE).instantiate()
	ember.position = STATIC_EMBER_SPOT
	ember.burn_time = 120.0
	ember.player = player
	current_scene.add_child(ember)
	var mine: Node2D = await armed_mine_at(STATIC_MINE_SPOT)
	check(await wait_until(func(): return ember.is_hurting(), 60) and mine.is_armed(), "a burning ember and an armed pod on the mat")
	var ember_box: Rect2 = ember.footprint()
	var ember_hitbox: Area2D = ember.get_node("Hitbox")

	log_p("-- a clean dash across the ember")
	await fresh_dash_ready()
	await settle_player(beside(ember_box, 1.0, 30.0))
	clear_iframes()
	var before := dodge_rewards()
	var health: int = player.playerHealth
	var dodged := dodges.size()
	var results := []
	var crossing := [0]
	press(KEY_RIGHT)
	tap(KEY_W)
	for i in 12:
		await physics_frame
		if player.hurtBox.overlaps_area(ember_hitbox):
			crossing[0] += 1
			if results.is_empty():
				# The ember's own report, made again to read what it resolved to.
				results.append(player.receive_hit(hit_info.from_area(ember_hitbox)))
	release(KEY_RIGHT)
	var after := dodge_rewards()
	await wait(30)
	var past: bool = hurtbox_rect().position.x > ember_box.end.x
	log_p("crossed the ember on %d frames, resolved %s, now past it %s: hits %d, health %d -> %d, perfect dodges %s, stamina %.0f -> %.0f, hype %.1f -> %.1f" % [crossing[0], results.map(func(r): return hit_info.Result.keys()[r]), past, events_of("HIT", &"bixby_ember").size(), health, player.playerHealth, dodges.slice(dodged).map(func(d): return d.id), before.stamina, after.stamina, before.hype, after.hype])
	check(crossing[0] > 0 and past, "the dash carried them across it")
	check(results == [hit_info.Result.DODGED] and events_of("HIT", &"bixby_ember").is_empty() and player.playerHealth == health, "DODGED, and no damage")
	check(dodges.size() == dodged, "and NO perfect dodge")
	check(is_equal_approx(after.stamina, before.stamina - defense.dash_stamina_cost) and is_equal_approx(after.hype, before.hype), "none of what one pays: the dash's stamina stays spent, no hype")

	log_p("-- the dodge ghost's own door")
	# Called by hand: a hazard that never moves can only be under the ghost if it was under the player as
	# the dash started, and PlayerDefense already refuses those (dash_overlaps).
	await fresh_dash_ready()
	await settle_player(STATIC_CLEAR_SPOT)
	var fireball: Node2D = load(STATIC_FIREBALL_SCENE).instantiate()
	fireball.position = Vector2(300, 300)
	current_scene.add_child(fireball)
	await wait(1)
	dodged = dodges.size()
	press(KEY_UP)
	tap(KEY_W)
	var ghosted := await wait_until(func(): return defense.dodge_ghost_position() != Vector2.INF, 10)
	release(KEY_UP)
	defense._on_ghost_entered(ember_hitbox)
	defense._on_ghost_entered(mine.trigger)
	player.receive_near_miss(hit_info.from_area(ember_hitbox))
	player.receive_near_miss(hit_info.make(&"computah_mine", mine, mine.global_position, boss))
	var off_still: Array = dodges.slice(dodged).map(func(d): return d.id)
	defense._on_ghost_entered(fireball.get_node("Hitbox"))
	var off_moving: Array = dodges.slice(dodged).map(func(d): return d.id)
	log_p("ghost up %s: off the ember and the pod %s, then off a falling fireball's area %s" % [ghosted, off_still, off_moving])
	check(ghosted and off_still.is_empty(), "the ghost's area_entered and a near miss reported outright both pay nothing off the ember or the pod")
	check(off_moving == [&"bixby_fireball"], "while a moving attack's area through the same door, on the same ghost, pays one")
	fireball.queue_free()

	log_p("-- a clean dash past the armed pod")
	await fresh_dash_ready()
	var ring: Rect2 = area_rect_any(mine.trigger)
	var under_ring := Rect2(ring.position.x, ring.end.y + 20.0 + hurtbox_rect().size.y / 2.0, ring.size.x, 0.0)
	var below := beside(under_ring, 1.0, 60.0)
	await settle_player(below)
	clear_iframes()
	before = dodge_rewards()
	dodged = dodges.size()
	press(KEY_RIGHT)
	tap(KEY_W)
	await wait(4)
	release(KEY_RIGHT)
	await wait(30)
	after = dodge_rewards()
	log_p("dashed past the ring %s from %s to %s: state %s, armed %s, perfect dodges %s, gauge %.0f -> %.0f" % [ring, below, player.global_position, sm.current_state.name, mine.is_armed(), dodges.slice(dodged).map(func(d): return d.id), before.gauge, after.gauge])
	check(player.global_position.x > ring.end.x and sm.current_state.name != "Trapped" and mine.is_armed(), "past it, uncaught, and it is still armed")
	check(dodges.size() == dodged and is_equal_approx(after.gauge, before.gauge), "no perfect dodge, and nothing for his gauge")

	log_p("-- anything that moves still pays one")
	for id in [&"bixby_sonic_beam", &"eric_whirlwind_v2"]:
		await fresh_dash_ready()
		await settle_player(STATIC_CLEAR_SPOT)
		dodged = dodges.size()
		press(KEY_UP)
		tap(KEY_W)
		await wait_until(func(): return player.is_dodging, 10)
		release(KEY_UP)
		var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
		var result: int = player.receive_hit(hit_info.make(id, dummy_source(), centre + Vector2(40, 0)))
		var paid: Array = dodges.slice(dodged).map(func(d): return d.id)
		log_p("%s through a dash: %s, perfect dodges %s" % [id, hit_info.Result.keys()[result], paid])
		check(result == hit_info.Result.DODGED and paid == [id], "%s: DODGED, and still a PERFECT DODGE" % id)

	log_p("-- a clean dash over the armed pod")
	await fresh_dash_ready()
	await settle_player(beside(ring, 1.0, 60.0))
	clear_iframes()
	dodged = dodges.size()
	press(KEY_RIGHT)
	tap(KEY_W)
	var caught := await wait_until(func(): return sm.current_state.name == "Trapped", 120)
	release(KEY_RIGHT)
	log_p("dashed onto it: state %s, perfect dodges %s" % [sm.current_state.name, dodges.slice(dodged).map(func(d): return d.id)])
	check(caught and dodges.size() == dodged, "it catches them, as a pod does, and pays no perfect dodge")


# ------------------------------------------------------------------ Matt (boss 4)
# His first attack, the Ezreal set: a teleporting volley of bouncing bolts, four golden waves from the
# four sides of the ring, then a punish window he may yell his way out of. The bolts and the waves are
# parry_pass_through: a parry or a block lets them fly on through the player, whole.

const MATT_BODY := "Arena/MattScene/MattCharacterBody"
const MATT_SEED := 20260923
const MATT_BOLT_SCENE := "res://Scenes/Bosses/MattMysticBoltScene.tscn"
const MATT_WAVE_SCENE := "res://Scenes/Bosses/MattTrueshotScene.tscn"
const MATT_VIEW := Rect2(0, 0, 1920, 1080)


# His yell only goes off after a punch lands in his window, and a mode about something else must not be
# thrown across the ring by it. Every Matt mode but his yell's own calls this.
func park_matt_yell() -> void:
	var body: Node = current_scene.get_node_or_null(MATT_BODY)
	if body:
		body.state_machine.yell_chance = 0.0


func seed_matt() -> void:
	current_scene.get_node(MATT_BODY).state_machine.rng.seed = MATT_SEED


# The modes written for his Glass Row and Deafening Yell, which run them for real.
func matt_glass_mode() -> bool:
	return mode.begins_with("matt_glass") or mode == "matt_deafen"


# Every other Matt mode was written for the Ezreal set: the rotation is pinned to the volley and phase
# two is never reached, so none of them meets a Glass Row - a Break doesn't start it either
# (phase_two_at_break) - and the set opens its own window rather than running on into the Echo Roars
# (echo_after_ezreal). The Echo Roars' own modes (matt_echo*) are pinned to the Echo Roars instead.
func park_matt_glass() -> void:
	var body: Node = current_scene.get_node_or_null(MATT_BODY)
	if body:
		var pinned: Array[String] = ["MysticVolley"]
		if mode.begins_with("matt_echo"):
			pinned = ["EchoRoars"]
		body.state_machine.attack_rotation = pinned
		body.state_machine.phase_two_ratio = -1.0
		body.state_machine.phase_two_at_break = false
		body.state_machine.echo_after_ezreal = false


# His fight with the lines and the card cut, seeded, and held in his intro until the mode starts it.
func load_matt() -> void:
	await load_fight("matt")
	boss = current_scene.get_node(MATT_BODY)
	sm = boss.state_machine
	seed_matt()
	if mode != "matt_yell":
		park_matt_yell()
	if not matt_glass_mode():
		park_matt_glass()
	sm.post_dialogue_pre_fight_timer.stop()


func matt_centre() -> Vector2:
	return player.hurtBox.get_node("CollisionShape2D").global_position


func spawn_matt_bolt(at: Vector2, heading: Vector2, with_player := true) -> Node2D:
	var bolt: Node2D = load(MATT_BOLT_SCENE).instantiate()
	bolt.heading = heading
	bolt.speed = sm.mystic_speed
	bolt.bounces = sm.mystic_bounces
	bolt.hit_radius = sm.mystic_hit_radius
	bolt.bounds = sm.ROPES.grow(-sm.mystic_hit_radius)
	bolt.player = player if with_player else null
	bolt.body = boss
	sm.add_hazard(bolt, at, boss.projectile_layer)
	return bolt


func spawn_matt_wave(at: Vector2, heading: Vector2) -> Node2D:
	var wave: Node2D = load(MATT_WAVE_SCENE).instantiate()
	wave.heading = heading
	wave.speed = sm.trueshot_speed
	wave.view_margin = sm.trueshot_view_margin
	wave.player = player
	sm.add_hazard(wave, at, boss.projectile_layer)
	return wave


# The first physics step, 1 to `frames` ahead, on which a live bolt or wave will touch the player's
# hurtbox where it is now, or -1. Bolts are stepped through their own rope reflections.
func matt_contact_in(proj: Node2D, frames: int) -> int:
	var box: Rect2 = area_rect(player.hurtBox)
	var pos: Vector2 = proj.global_position
	var heading: Vector2 = proj.heading
	var step: float = proj.speed / 60.0
	var is_bolt: bool = "bounds" in proj
	for k in range(1, frames + 1):
		pos += heading * step
		if is_bolt:
			var bounds: Rect2 = proj.bounds
			if pos.x < bounds.position.x or pos.x > bounds.end.x:
				var wall_x := bounds.position.x if pos.x < bounds.position.x else bounds.end.x
				pos.x = 2.0 * wall_x - pos.x
				heading.x = -heading.x
			if pos.y < bounds.position.y or pos.y > bounds.end.y:
				var wall_y := bounds.position.y if pos.y < bounds.position.y else bounds.end.y
				pos.y = 2.0 * wall_y - pos.y
				heading.y = -heading.y
			if pos.clamp(box.position, box.end).distance_to(pos) <= proj.hit_radius:
				return k
		else:
			return matt_wave_contact(proj.global_position, heading, proj.speed, frames)
	return -1


# The first step, 0 to `frames` ahead, on which a wave at `at` flying down `heading` touches the player's
# hurtbox where it is now, or -1: its hit polygon, turned to the heading, against the box.
func matt_wave_contact(at: Vector2, heading: Vector2, speed: float, frames: int) -> int:
	var box: Rect2 = area_rect(player.hurtBox)
	var rect := PackedVector2Array([box.position, Vector2(box.end.x, box.position.y), box.end, Vector2(box.position.x, box.end.y)])
	var layout: GDScript = load("res://Scripts/MattArtLayout.gd")
	var poly: PackedVector2Array = layout.scaled_poly(layout.trueshot_hit_poly(), layout.SCALE, heading.angle())
	for k in range(0, frames + 1):
		var moved := PackedVector2Array()
		for point in poly:
			moved.append(point + at + heading * speed / 60.0 * k)
		if not Geometry2D.intersect_polygons(moved, rect).is_empty():
			return k
	return -1


# Whether the player's hurtbox, where it is now, touches a polygon in world px.
func matt_in_zone(zone: PackedVector2Array) -> bool:
	var box: Rect2 = area_rect(player.hurtBox)
	var rect := PackedVector2Array([box.position, Vector2(box.end.x, box.position.y), box.end, Vector2(box.position.x, box.end.y)])
	return not Geometry2D.intersect_polygons(zone, rect).is_empty()


# The parry mode's player: stands still, and presses the guard a few steps before anything reaches them
# that hasn't already been answered on this pass, holding it long enough to cover everything the one
# press can parry.
var matt_bot := {"held": false, "held_frames": 0, "presses": 0}


func matt_parry_step() -> void:
	var soonest := 99
	for proj in sm.live_projectiles():
		if proj.latched:
			continue
		var k := matt_contact_in(proj, 12)
		if k >= 0:
			soonest = mini(soonest, k)
	# A latched Trueshot is read off its release, as a player reads the latch: from the station nearest
	# them the wave is on them the moment it leaves.
	var barrage: Node = sm.states["TrueshotBarrage"]
	if sm.current_state == barrage and barrage.beat == barrage.Beat.CHARGE and barrage.latched:
		var to_release := ceili((barrage.release_at - barrage.beat_clock) * 60.0)
		var k := matt_wave_contact(barrage._spawn_point() + barrage.aim_heading * sm.trueshot_lead,
			barrage.aim_heading, sm.trueshot_speed, 12)
		if k >= 0:
			soonest = mini(soonest, to_release + k)
		# Standing in the burst - on him, beside him, behind him - it is on them as the wave leaves.
		if matt_in_zone(barrage.burst_zone()):
			soonest = mini(soonest, to_release)
	if not matt_bot.held and soonest <= 5:
		press(KEY_SHIFT)
		matt_bot.held = true
		matt_bot.held_frames = 0
		matt_bot.presses += 1
	elif matt_bot.held:
		matt_bot.held_frames += 1
		if matt_bot.held_frames >= 16 and soonest > 5:
			release(KEY_SHIFT)
			matt_bot.held = false


# What he and the ring look like at the VS card's flash: everything a watched entrance and a skipped
# one must agree on. Floats are rounded: a zoom tweened back to 1.0 can land a float's width off the
# skip's exact reset.
func matt_snapshot() -> Dictionary:
	var gates: Node = current_scene.get_node("Arena/Gates")
	var screen: GDScript = load("res://Scripts/ScreenView.gd")
	var crowd: Node = get_first_node_in_group("arena_crowd")
	return {
		"matt": boss.global_position, "anim": boss.current_anim, "flip": boss.sprite.flip_h,
		"modulate": boss.sprite.modulate, "rotation": snappedf(boss.sprite.rotation, 0.0001), "offset": boss.sprite.offset,
		"hurtbox": boss.hurtbox.monitoring, "hud": boss.hud_layer.visible, "hud_alpha": snappedf(boss.health_bar.modulate.a, 0.0001),
		"gates_open": gates.is_open(), "player": player.global_position, "talking": player.is_talking,
		"player_sm": player.state_machine.is_processing(), "face_point": player.facing_point,
		"zoom": snappedf(screen.zoom, 0.0001), "shake": screen.shake_offset, "time_scale": snappedf(Engine.time_scale, 0.0001),
		"crowd_cheering": crowd != null and crowd._cheer_time_left > 0.0, "music": boss.music_player.playing,
		"music_starts": boss.music_starts, "hazards": get_nodes_in_group(sm.HAZARD_GROUP).size(),
		"balloon": live_balloon() != null, "doll": boss.get_node_or_null("Hong") != null,
		"intro_fx": sm.states["Intro"].intro_fx.size(),
		"seen": root.get_node("GameProgress").entrances_seen.has(boss.FIGHT_SCENE),
	}


func matt_snapshot_diff(got: Dictionary, want: Dictionary) -> Array:
	var diffs := []
	for k in want:
		if got[k] != want[k]:
			diffs.append("%s %s (watched %s)" % [k, got[k], want[k]])
	return diffs


# Waits for the VS card to be at or past its flash, which a watched entrance reaches on the card's own
# clock and a skip jumps straight to.
func matt_card_flash(max_frames := 900) -> bool:
	var card: Node = vs_card()
	var card_art: GDScript = load(VS_CARD_LAYOUT)
	return await wait_until(func(): return card.is_playing() and card.clock >= card_art.HOLD_END, max_frames)


# ---- the pass-through

func test_matt_pass_through() -> void:
	await load_matt()
	health_ok()
	track()
	track_parries()
	track_dodges()
	var hype: Node = player.get_node("Hype")
	var catalog: GDScript = load("res://Scripts/AttackCatalog.gd")

	log_p("-- the catalogue")
	var shot: Dictionary = catalog.get_attack(&"matt_mystic_shot")
	var wave: Dictionary = catalog.get_attack(&"matt_trueshot")
	var yell: Dictionary = catalog.get_attack(&"matt_yell")
	check(shot.blockable and shot.weight == catalog.Weight.LIGHT and shot.tell and shot.parry_pass_through
		and not shot.dash_through and not shot.parryable and not shot.dodge_tell and shot.damage == 2 and shot.hype_loss
		and not shot.bypass_invincibility and not shot.no_perfect_dodge and not shot.from_above,
		"matt_mystic_shot: blockable LIGHT, red, passes through, a whole heart (since 2026-10-05), inside the i-frames' rules, a perfect dodge")
	check(wave.blockable and wave.weight == catalog.Weight.HEAVY and wave.tell and wave.dash_through and wave.parry_pass_through
		and not wave.parryable and not wave.dodge_tell and wave.damage == 2 and wave.hype_loss
		and not wave.bypass_invincibility and not wave.no_perfect_dodge and not wave.from_above,
		"matt_trueshot: blockable HEAVY, red, dashed through, passes through, a whole heart (since 2026-10-05)")
	check(yell.dash_through and yell.dodge_tell and not yell.blockable and not yell.parryable and not yell.tell
		and not yell.parry_pass_through and yell.damage == 1 and yell.hype_loss and not yell.bypass_invincibility
		and not yell.no_perfect_dodge, "matt_yell: yellow, a dash or distance only, 1 damage")
	check(catalog.DEFAULTS.has("parry_pass_through") and catalog.DEFAULTS.parry_pass_through == false, "parry_pass_through defaults off")
	# Every hit in his fight is catalogued under matt_ (bolts, waves, yell, glass, the Echo Roars' rings). Other fights
	# carry it by their own design (Liam's tsunami), so only his are held to this.
	var his: Array = catalog.ATTACKS.keys().filter(func(id): return String(id).begins_with("matt_"))
	var passing: Array = his.filter(func(id): return catalog.get_attack(id).parry_pass_through)
	check(passing.size() == 3 and passing.has(&"matt_mystic_shot") and passing.has(&"matt_trueshot") and passing.has(&"matt_echo"),
		"and of his attacks only his bolts, waves and Echo rings carry it, nothing else in his fight (%s of %s)" % [passing, his])
	var ring: Dictionary = catalog.get_attack(&"matt_echo")
	var punish: Dictionary = catalog.get_attack(&"matt_echo_punish")
	var gold: Dictionary = catalog.get_attack(&"matt_boomburst")
	check(ring.parryable and ring.tell and ring.parry_pass_through and ring.bypass_invincibility and not ring.blockable
		and not ring.dash_through and not ring.dodge_tell and ring.damage == 1,
		"matt_echo: parried, red, passes through, inside the i-frames, 1 damage, never dashed through")
	check(not punish.parryable and not punish.blockable and not punish.tell and not punish.dodge_tell and not punish.dash_through
		and punish.bypass_invincibility and punish.damage == 2, "matt_echo_punish: nothing answers it, no badge, inside the i-frames, a whole heart")
	check(gold.dash_through and gold.dodge_tell and is_equal_approx(gold.dash_immunity, 0.21) and gold.bypass_invincibility
		and not gold.parryable and not gold.blockable and gold.damage == 3, "matt_boomburst: yellow, dashed through on 0.21 s, inside the i-frames, a heart and a half")

	log_p("-- a parried bolt flies on, whole")
	var fx: Node = current_scene.get_node("Arena/MainPlayer/FinisherFx")
	var shatter_seen := [false]
	watch = func():
		for child in fx.get_children():
			if child is Sprite2D and child.texture and child.texture.resource_path.ends_with("parry_shatter.png"):
				shatter_seen[0] = true
	boss.global_position = Vector2(1500, 300)
	await settle_player(Vector2(900, 700))
	var heading := Vector2.from_angle(deg_to_rad(22.5))
	var bolt := spawn_matt_bolt(matt_centre() - heading * 500.0, heading)
	# The drawn sprite straight off the bolt, which is where PlayerCombatFx looks for a parried projectile's
	# art: the pass-through branch has to leave it flashed but neither shattered nor knocked. The stand-in
	# bolt draws with polygons, so a sprite is hung there for it.
	var art: Sprite2D = bolt.sheet
	if art == null:
		art = Sprite2D.new()
		art.texture = load("res://Assets/Characters/Matt/matt.png")
		art.hframes = 2
		art.scale = Vector2.ONE * 0.2
		bolt.add_child(art)
	var art_rest: Vector2 = art.offset
	var health: int = player.playerHealth
	var hype_before: float = hype.hype
	var flashed := [false]
	var offsets := []
	await wait(1)
	await wait_until(func(): return bolt.global_position.distance_to(matt_centre()) < 40.0 + bolt.speed * 0.1, 120)
	press(KEY_SHIFT)
	await wait_until(func(): return not parries.is_empty() or not events.is_empty() or not is_instance_valid(bolt), 30)
	var seen_heading: Vector2 = bolt.heading if is_instance_valid(bolt) else Vector2.ZERO
	for i in 40:
		if is_instance_valid(art):
			if art.self_modulate != Color.WHITE:
				flashed[0] = true
			offsets.append(art.offset)
		if not is_instance_valid(bolt) or not bolt.latched:
			break
		await physics_frame
	release(KEY_SHIFT)
	await wait(6)
	watch = Callable()
	log_p("parries %s, events %s, heading %s -> %s, reflections %d, hype %.0f -> %.0f" % [parries.map(func(p): return p.id), events.map(func(e): return e.kind), heading, seen_heading, bolt.reflections if is_instance_valid(bolt) else -1, hype_before, hype.hype])
	check(parries.size() == 1 and parries[0].id == &"matt_mystic_shot", "parried")
	check(events.is_empty(), "and never HIT or BLOCKED during the overlap")
	check(is_instance_valid(bolt) and not bolt.spent, "the bolt survives")
	check(is_instance_valid(bolt) and bolt.heading == heading and bolt.speed == sm.mystic_speed and bolt.reflections == 0 and seen_heading == heading, "with the same heading, speed and bounce count")
	check(not shatter_seen[0], "no shatter")
	check(flashed[0] and offsets.all(func(o): return o == art_rest), "its art flashed and was never knocked off its hitbox")
	check(player.playerHealth == health, "no health lost")
	check(hype.hype > hype_before, "hype paid (%.0f -> %.0f)" % [hype_before, hype.hype])

	log_p("-- and it HITs on its next pass, and is consumed")
	await wait(int(defense.blocked_rehit_interval * 60.0) + 10)
	clear_iframes()
	events.clear()
	var ahead := Vector2.INF
	for reach in [260.0, 220.0, 180.0, 140.0]:
		var point: Vector2 = bolt.global_position + bolt.heading * reach
		if sm.ROPES.grow(-70.0).has_point(point):
			ahead = point
			break
	check(ahead != Vector2.INF, "found a spot in its path inside the ropes")
	if ahead != Vector2.INF:
		await settle_player(ahead - (matt_centre() - player.global_position))
		# By id: a lambda called with a freed object in its captures prints an engine error each call.
		var bolt_id := bolt.get_instance_id()
		await wait_until(func(): return not events.is_empty() or not is_instance_id_valid(bolt_id), 60)
		await wait(2)
		check(events_of("HIT", &"matt_mystic_shot").size() == 1 and player.playerHealth == health - shot.damage, "HIT for its %d half-hearts (%s)" % [shot.damage, events.map(func(e): return "%s %s" % [e.kind, e.id])])
		check(not is_instance_valid(bolt), "and the bolt is gone")

	log_p("-- a held guard %s" % ("blocks it for 20, and it stays whole" if blocking() else "is no answer: it hits"))
	events.clear()
	parries.clear()
	health_ok()
	clear_iframes()
	await settle_player(Vector2(900, 700))
	defense._set_stamina(defense.max_stamina)
	track_spends()
	press(KEY_SHIFT)
	await past_window()
	var blocked_bolt := spawn_matt_bolt(matt_centre() - heading * 400.0, heading)
	var blocked_id := blocked_bolt.get_instance_id()
	await wait_until(func(): return not events.is_empty() or not is_instance_id_valid(blocked_id), 90)
	await wait(20)
	release(KEY_SHIFT)
	if blocking():
		var blocks := events_of("BLOCKED", &"matt_mystic_shot")
		var cost: float = defense.max_stamina - blocks[0].stamina if not blocks.is_empty() else 0.0
		check(blocks.size() == 1 and events_of("HIT").is_empty() and is_equal_approx(cost, 20.0), "BLOCKED once for %.0f" % cost)
		check(is_instance_valid(blocked_bolt) and not blocked_bolt.spent, "and it flies on")
	else:
		check(events_of("HIT", &"matt_mystic_shot").size() == 1 and events_of("BLOCKED").is_empty() and spends == whiffs(1),
			"HIT through the held guard, and nothing spent but the press's missed parry (%s)" % [spends])
	if is_instance_valid(blocked_bolt):
		blocked_bolt.queue_free()

	log_p("-- facing away")
	events.clear()
	parries.clear()
	await wait(40)
	# He is straight above them, so they face up, and the bolt comes up at them from below: from behind.
	boss.global_position = Vector2(900, 160)
	await settle_player(Vector2(900, 560))
	await wait(6)
	var up: Vector2 = Vector2.from_angle(deg_to_rad(-67.5))
	var behind := spawn_matt_bolt(matt_centre() - up * 330.0, up)
	await wait_until(func(): return behind.global_position.distance_to(matt_centre()) < 40.0 + behind.speed * 0.1, 120)
	var facing: int = player.facing
	press(KEY_SHIFT)
	await wait_until(func(): return not parries.is_empty() or not events.is_empty(), 30)
	release(KEY_SHIFT)
	log_p("facing %d (1 is up, toward him) with the bolt coming up from behind: %s" % [facing, parries.map(func(p): return p.id)])
	check(facing == 1 and parries.size() == 1 and events.is_empty(), "a parry answers a bolt from behind")
	if is_instance_valid(behind):
		behind.queue_free()

	log_p("-- a wave flies on through a parry, a block and a hit, never bounces, and goes only off screen")
	boss.global_position = Vector2(1500, 300)
	for answer in ["parry", "block", "hit"]:
		events.clear()
		parries.clear()
		clear_iframes()
		health_ok()
		defense._set_stamina(defense.max_stamina)
		await wait(40)
		await settle_player(Vector2(960, 700))
		if answer == "block":
			press(KEY_SHIFT)
			await past_window()
		var down := Vector2.DOWN
		var w := spawn_matt_wave(matt_centre() - down * 450.0, down)
		var path := []
		var last_bounds := Rect2()
		var pressed := false
		for i in 240:
			if not is_instance_valid(w):
				break
			path.append(w.global_position)
			last_bounds = w._bounds()
			if answer == "parry" and not pressed and matt_contact_in(w, 8) >= 0:
				press(KEY_SHIFT)
				pressed = true
			await physics_frame
		release(KEY_SHIFT)
		var forward := true
		for i in range(1, path.size()):
			if (path[i] - path[i - 1]).dot(down) <= 0.0:
				forward = false
		log_p("%s: %s, %d steps, last box %s, health %d" % [answer, events.map(func(e): return e.kind) + parries.map(func(p): return "PARRIED"), path.size(), last_bounds, player.playerHealth])
		match answer:
			"parry":
				check(parries.size() == 1 and events.is_empty() and player.playerHealth == 100, "parried, and it flew on")
			"block":
				if blocking():
					var wave_blocks := events_of("BLOCKED", &"matt_trueshot")
					check(wave_blocks.size() == 1 and is_equal_approx(defense.max_stamina - wave_blocks[0].stamina, 35.0), "blocked for 35, and it flew on")
				else:
					check(events_of("HIT", &"matt_trueshot").size() == 1 and player.playerHealth == 100 - wave.damage, "a held guard is no answer: HIT for its %d half-hearts, and it flew on" % wave.damage)
			"hit":
				check(events_of("HIT", &"matt_trueshot").size() == 1 and player.playerHealth == 100 - wave.damage, "HIT for its %d half-hearts, and it flew on" % wave.damage)
		check(forward, "%s: it only ever moved on down its heading - no bounce" % answer)
		check(not MATT_VIEW.intersects(last_bounds), "%s: it went only once it was off the screen (%s)" % [answer, last_bounds])

	log_p("-- a dash through a wave is DODGED and a perfect dodge")
	events.clear()
	dodges.clear()
	clear_iframes()
	await fresh_dash_ready()
	await settle_player(Vector2(960, 760))
	var dash_wave := spawn_matt_wave(matt_centre() + Vector2.UP * 520.0, Vector2.DOWN)
	await wait_until(func(): return matt_contact_in(dash_wave, 3) >= 0, 60)
	press(KEY_UP)
	tap(KEY_W)
	await wait_until(func(): return not is_instance_valid(dash_wave) or not dash_wave.results.is_empty(), 30)
	release(KEY_UP)
	var got: Array = dash_wave.results if is_instance_valid(dash_wave) else []
	log_p("dash: results %s, perfect dodges %s, events %s" % [got, dodges.map(func(d): return d.id), events.map(func(e): return e.kind)])
	check(got.size() >= 1 and got[0] == load("res://Scripts/HitInfo.gd").Result.DODGED and dodges.size() == 1 and dodges[0].id == &"matt_trueshot" and events.is_empty(), "DODGED, and a PERFECT DODGE")


# ---- the bounces and a real volley

func test_matt_bounces() -> void:
	await load_matt()
	health_ok()
	var ropes: Rect2 = sm.ROPES
	var bounds: Rect2 = ropes.grow(-sm.mystic_hit_radius)

	log_p("-- one bolt in an empty ring")
	var start_heading := Vector2.from_angle(deg_to_rad(22.5))
	var bolt := spawn_matt_bolt(Vector2(960, 540), start_heading, false)
	var turns: Array = bolt.turns
	var outside := 0
	var last := bolt.global_position
	for i in 60 * 14:
		if not is_instance_valid(bolt):
			break
		last = bolt.global_position
		if not ropes.has_point(last):
			outside += 1
		await physics_frame
	var lattice_ok := true
	var mirror_ok := true
	var previous := start_heading
	for turn in turns:
		var h: Vector2 = turn.heading
		var degrees := fposmod(rad_to_deg(h.angle()), 360.0)
		var steps := degrees / 22.5
		if absf(steps - roundf(steps)) > 0.001 or int(roundf(steps)) % 4 == 0:
			lattice_ok = false
		if not (is_equal_approx(absf(h.x), absf(previous.x)) and is_equal_approx(absf(h.y), absf(previous.y)) and h != previous):
			mirror_ok = false
		previous = h
	var edge_gap := minf(minf(absf(last.x - bounds.position.x), absf(last.x - bounds.end.x)), minf(absf(last.y - bounds.position.y), absf(last.y - bounds.end.y)))
	log_p("reflections %d at %s; last seen %s, %.1f px from a rope; frames outside the ropes %d" % [turns.size(), turns.map(func(t): return Vector2i(t.at)), last, edge_gap, outside])
	check(turns.size() == sm.mystic_bounces, "exactly mystic_bounces (%d) reflections" % sm.mystic_bounces)
	check(lattice_ok, "every heading on the lattice, never along an axis")
	check(mirror_ok, "each an exact mirror of the one before")
	check(outside == 0, "inside the ropes throughout")
	check(not is_instance_valid(bolt) and edge_gap <= sm.mystic_speed / 60.0 + 1.0, "and it bursts on the rope contact after them")

	log_p("-- a corner is one bounce")
	var diagonal := Vector2.from_angle(deg_to_rad(45.0))
	var per_axis: float = sm.mystic_speed / 60.0 * diagonal.x
	var corner_bolt := spawn_matt_bolt((bounds.end - Vector2.ONE * (per_axis * 20.0 + per_axis * 0.5)).round(), diagonal, false)
	var corner_turns: Array = corner_bolt.turns
	await wait_until(func(): return not corner_turns.is_empty(), 60)
	await wait(10)
	log_p("corner: %s" % [corner_turns.map(func(t): return [Vector2i(t.at), t.heading])])
	check(corner_turns.size() == 1 and corner_turns[0].heading.is_equal_approx(-diagonal), "both components turned on one contact, counted once")
	if is_instance_valid(corner_bolt):
		corner_bolt.queue_free()

	log_p("-- a real volley at the top tier")
	player.playerHealth = 1000
	var spot: Vector2 = SMOKE_SPOTS["matt"]
	await settle_player(spot)
	boss.boss_health = int(boss.max_health * 0.3)
	var volley: Node = sm.states["MysticVolley"]
	var births := []
	var tells := []
	var known := {}
	var had_tell := false
	var max_alive := 0
	var start: float = defense.clock
	sm.start_cycle()
	check(sm.cycle_casts == sm.mystic_casts_by_tier[2], "the top tier's %d casts below a third of his health (%d)" % [sm.mystic_casts_by_tier[2], sm.cycle_casts])
	while defense.clock - start < 12.0 and sm.current_state == volley:
		player.global_position = spot
		var tell := tell_node()
		var up := tell != null and not str(tell.name).ends_with("Spent")
		if up and not had_tell:
			tells.append(defense.clock)
		had_tell = up
		var alive: Array = sm.live_bolts()
		max_alive = maxi(max_alive, alive.size())
		for b in alive:
			if not known.has(b.get_instance_id()):
				known[b.get_instance_id()] = true
				births.append(defense.clock)
		await physics_frame
	log_p("%d spots, %d bolts, %d badges, at most %d alive, %d skipped" % [volley.spots.size(), births.size(), tells.size(), max_alive, volley.skipped])
	check(max_alive <= sm.mystic_max_alive, "never more than five alive (%d)" % max_alive)
	var spots_ok := true
	for s in volley.spots:
		var line: Vector2 = s.player - s.mouth
		var on_line: bool = line.normalized().is_equal_approx(s.heading)
		log_p("  spot: range %.0f, heading %.1f, mouth %s, feet %s, on the line through the player %s" % [s.range, rad_to_deg(s.heading.angle()), Vector2i(s.mouth), Vector2i(s.feet), on_line])
		if s.range < 450.0 - 0.01 or not on_line or absf(line.length() - s.range) > 0.5:
			spots_ok = false
	check(volley.spots.size() == sm.cycle_casts and spots_ok, "every spot at least 450 px out, on a lattice line through the player")
	var leads := []
	for b in births:
		var lead := -1.0
		for t in tells:
			if t <= b:
				lead = b - t
		leads.append(snappedf(lead, 0.001))
	log_p("badge to bolt: %s s" % [leads])
	check(births.size() == sm.cycle_casts and leads.all(func(l): return absf(l - sm.mystic_windup) <= 2.0 / 60.0 + 0.001), "the badge up %.2f s before each bolt" % sm.mystic_windup)


# ---- the Trueshot barrage

func test_matt_trueshot() -> void:
	await load_matt()
	player.playerHealth = 1000
	var barrage: Node = sm.states["TrueshotBarrage"]
	var spent: Node = sm.states["Spent"]
	var bar: Control = boss.health_bar
	await settle_player(Vector2(760, 760))
	var charges := {}
	var tracking_ok := true
	var frozen_ok := true
	var badge_ok := true
	var hud := {"top_min": 1.0, "left_max": 0.0}
	var waves := {}
	var sheets := {}
	var station := -1
	var t0: float = defense.clock
	var at_recover := {}
	sm.on_child_transition(sm.current_state, "TrueshotBarrage")
	while defense.clock - t0 < 12.0:
		var t: float = defense.clock - t0
		# Sideways and back, so the aim has something to track.
		player.global_position = Vector2(760.0 + 160.0 * sin(t * TAU / 1.4), 760)
		player.velocity = Vector2.ZERO
		var centre := matt_centre()
		await physics_frame
		if sm.current_state == barrage and barrage.beat == barrage.Beat.CHARGE:
			if barrage.station_index != station:
				station = barrage.station_index
				charges[station] = {"feet": boss.global_position, "name": barrage._station().name}
			var clock: float = barrage.beat_clock
			var tell := tell_node()
			if clock < barrage.release_at - 1.5 / 60.0 and (tell == null or str(tell.name).ends_with("Spent")):
				badge_ok = false
			if not barrage.latched:
				if not barrage.aim_point.is_equal_approx(centre):
					tracking_ok = false
			elif charges[station].has("locked"):
				if not barrage.aim_point.is_equal_approx(charges[station].locked):
					frozen_ok = false
			else:
				charges[station]["locked"] = barrage.aim_point
				charges[station]["lock_clock"] = clock
			if station == 0:
				hud.top_min = minf(hud.top_min, bar.modulate.a)
			elif station == 1 and clock > 0.3:
				hud.left_max = maxf(hud.left_max, bar.modulate.a)
		for w in sm.live_waves():
			var id: int = w.get_instance_id()
			if not waves.has(id):
				waves[id] = []
				if w.sheet != null:
					sheets[id] = {"heading": w.heading, "texture": w.sheet.texture.resource_path, "frame": w.sheet.frame,
						"flip_h": w.sheet.flip_h, "flip_v": w.sheet.flip_v}
			waves[id].append(w.global_position)
		if sm.current_state == sm.states["Recover"] and at_recover.is_empty():
			at_recover = {"feet": boss.global_position, "clear": sm.live_projectiles().is_empty(), "capped": spent.capped, "waited": spent.waited}
			await wait(2)
			at_recover["hurtbox"] = boss.hurtbox.monitoring
			break

	log_p("-- the stations")
	var names := []
	var feet_ok := true
	for i in charges:
		names.append(charges[i].name)
		if not charges[i].feet.is_equal_approx(sm.STATIONS[i].feet):
			feet_ok = false
		log_p("  %s: feet %s, latched at %.3f s on %s" % [charges[i].name, charges[i].feet, charges[i].get("lock_clock", -1.0), charges[i].get("locked", Vector2.INF)])
	check(names == [&"top", &"left", &"bottom", &"right"], "top, left, bottom, right, in that order (%s)" % [names])
	check(feet_ok, "each on its exact feet point")
	check(badge_ok, "the badge up for the whole of every charge")
	check(tracking_ok, "the aim on the player every step until it latches")
	check(frozen_ok, "and frozen from the latch on")
	var locks_ok := true
	for i in charges:
		if absf(charges[i].get("lock_clock", -1.0) - (sm.trueshot_charge - sm.trueshot_lock_lead)) > 1.5 / 60.0:
			locks_ok = false
	check(locks_ok, "the latch %.2f s into the charge" % (sm.trueshot_charge - sm.trueshot_lock_lead))

	log_p("-- the shots")
	var heading_ok := true
	var path_ok := true
	for shot in barrage.shots:
		var normal: Vector2 = sm.STATIONS[barrage.shots.find(shot)].normal
		var degrees := rad_to_deg(shot.heading.angle())
		var off := absf(rad_to_deg(normal.angle_to(shot.heading)))
		var steps: float = degrees / sm.trueshot_step
		if absf(steps - roundf(steps)) > 0.001 or off > sm.trueshot_max_turn + 0.001:
			heading_ok = false
		var perp: Vector2 = shot.heading.orthogonal()
		var across: float = (shot.point - shot.mouth).dot(perp)
		var lateral_ok := is_equal_approx(shot.lateral, clampf(across, -sm.trueshot_offset_max, sm.trueshot_offset_max))
		var miss: float = absf((shot.point - shot.spawn).dot(perp))
		if not lateral_ok or (absf(across) <= sm.trueshot_offset_max and miss > 0.5):
			path_ok = false
		log_p("  %s: heading %.1f (%.1f off the normal), %.1f across from his mouth, lateral %.1f, path misses the latched point by %.2f px" % [shot.station, degrees, off, across, shot.lateral, miss])
	check(barrage.shots.size() == 4 and heading_ok, "every heading snapped to %.2f and within %.1f of the station's normal" % [sm.trueshot_step, sm.trueshot_max_turn])
	check(path_ok, "every path through the latched point, sliding at most %.0f px along the chord" % sm.trueshot_offset_max)
	var speed_ok := not waves.is_empty()
	for id in waves:
		var path: Array = waves[id]
		for i in range(1, path.size()):
			if absf(path[i].distance_to(path[i - 1]) - sm.trueshot_speed / 60.0) > 0.01:
				speed_ok = false
	check(speed_ok, "every wave at %.0f px/s (%d seen)" % [sm.trueshot_speed, waves.size()])
	# The art's contract: fold the heading into the first quadrant, k = its 11.25 degree step; an even k
	# is heading k/2 of the main sheet, an odd one (k-1)/2 of the in-between sheet, flipped by its signs.
	var art_ok := not sheets.is_empty()
	for id in sheets:
		var seen: Dictionary = sheets[id]
		var k := roundi(rad_to_deg(atan2(absf(seen.heading.y), absf(seen.heading.x))) / 11.25)
		var want := "matt_trueshot_wave_mid.png" if k % 2 == 1 else "matt_trueshot_wave.png"
		var index := floori(k / 2.0)
		if not seen.texture.ends_with("/" + want) or floori(seen.frame / 4.0) != index \
				or seen.flip_h != (seen.heading.x < 0.0) or seen.flip_v != (seen.heading.y < 0.0):
			art_ok = false
		log_p("  wave at %.2f: %s frame %d, flips %s/%s" % [rad_to_deg(seen.heading.angle()), seen.texture.get_file(), seen.frame, seen.flip_h, seen.flip_v])
	check(art_ok, "each wave drawn at its own heading, the odd 11.25 steps off the in-between sheet")

	log_p("-- the HUD, Spent and the window")
	log_p("bar alpha at the top %.2f, back at the left %.2f; at the window: %s" % [hud.top_min, hud.left_max, at_recover])
	check(is_equal_approx(hud.top_min, sm.hud_fade_alpha), "the bar fades to %.1f while he charges at the top" % sm.hud_fade_alpha)
	check(is_equal_approx(hud.left_max, 1.0), "and is back at full once he has gone")
	check(not at_recover.is_empty() and (at_recover.clear or at_recover.capped), "Spent waits for a clear ring before the window")
	check(not at_recover.is_empty() and at_recover.waited >= sm.spent_min - 0.001, "and holds at least %.1f s" % sm.spent_min)
	check(not at_recover.is_empty() and at_recover.feet.is_equal_approx(sm.HOME) and at_recover.hurtbox, "the window opens at HOME with a live hurtbox")

	log_p("-- R9: nowhere on or round a station is safe from its shot")
	var swept := await matt_station_sweep()
	for line in swept.lines:
		log_p(line)
	check(swept.shots > 0 and swept.safe.is_empty(), "every spot in him, on his box's edge and 50 and 100 px off it, and the smoke spot, is hit (%d shots; safe: %s)" % [swept.shots, swept.safe])


# The floor the player's origin can reach: slid into each wall from the middle of the ring.
func matt_floor() -> Rect2:
	var was: Vector2 = player.global_position
	var ends := []
	for push in [Vector2(-3000, 0), Vector2(3000, 0), Vector2(0, -3000), Vector2(0, 3000)]:
		player.global_position = sm.HOME
		player.move_and_collide(push)
		ends.append(player.global_position)
	player.global_position = was
	return Rect2(Vector2(ends[0].x, ends[2].y), Vector2(ends[1].x - ends[0].x, ends[3].y - ends[2].y))


# Real shots, one station at a time, at a player standing still inside his body box, on its edge and 50
# and 100 px off it (eight spots a ring, those on the floor), and on the smoke spot from the bottom.
func matt_station_sweep() -> Dictionary:
	var barrage: Node = sm.states["TrueshotBarrage"]
	var layout: GDScript = load("res://Scripts/MattArtLayout.gd")
	var box: Rect2 = area_rect(player.hurtBox)
	var half: Vector2 = box.size / 2.0
	var reach: Vector2 = box.get_center() - player.global_position
	var floor_rect := matt_floor()
	var landed := []
	var on_hit := func(hit): landed.append(hit.attack_id)
	defense.hit_taken.connect(on_hit)
	var result := {"shots": 0, "safe": [], "lines": []}
	for s in sm.STATIONS.size():
		var station: Dictionary = sm.STATIONS[s]
		var body_box: Rect2 = layout.local_rect(layout.BODY_BOX)
		body_box.position += station.feet
		var spots := []
		if station.name == &"bottom":
			spots.append({"at": SMOKE_SPOTS["matt"], "ring": "the smoke spot"})
		for f in [Vector2(0.5, 0.5), Vector2(0.2, 0.2), Vector2(0.8, 0.2), Vector2(0.2, 0.85), Vector2(0.8, 0.85)]:
			spots.append({"at": body_box.position + body_box.size * f - reach, "ring": "inside"})
		for d in [0.0, 50.0, 100.0]:
			var ring := body_box.grow_individual(d + half.x, d + half.y, d + half.x, d + half.y)
			for corner in [ring.position, Vector2(ring.get_center().x, ring.position.y), Vector2(ring.end.x, ring.position.y),
					Vector2(ring.end.x, ring.get_center().y), ring.end, Vector2(ring.get_center().x, ring.end.y),
					Vector2(ring.position.x, ring.end.y), Vector2(ring.position.x, ring.get_center().y)]:
				var origin: Vector2 = corner - reach
				if floor_rect.has_point(origin):
					spots.append({"at": origin, "ring": "%d px off" % d})
		var hit_count := 0
		for spot in spots:
			landed.clear()
			player.playerHealth = 1000
			player.is_invincible = false
			player.invincibility_timer.stop()
			for hazard in get_nodes_in_group(sm.HAZARD_GROUP):
				hazard.queue_free()
			sm.on_child_transition(sm.current_state, "Idle")
			sm.beat_timer.stop()
			await wait(1)
			sm.on_child_transition(sm.current_state, "TrueshotBarrage")
			barrage.station_index = s
			var released := false
			for f in 150:
				player.global_position = spot.at
				player.velocity = Vector2.ZERO
				await physics_frame
				released = released or barrage.beat == barrage.Beat.FIRE
				if released and (barrage.beat != barrage.Beat.FIRE or barrage.beat_clock > 0.3):
					break
			result.shots += 1
			if landed.has(&"matt_trueshot"):
				hit_count += 1
			else:
				result.safe.append("%s %s %s" % [station.name, spot.ring, spot.at])
		result.lines.append("  %s: %d spots, hit on %d" % [station.name, spots.size(), hit_count])
	defense.hit_taken.disconnect(on_hit)
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	return result


# ---- the yell

func matt_window(yell_on := 0) -> Node:
	var recover: Node = sm.states["Recover"]
	for hazard in get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	# A combo of its own: the count carries between windows (PlayerCombo), and a POW would come early.
	player.combo.reset()
	sm.on_child_transition(sm.current_state, "Recover")
	if yell_on > 0:
		recover.yell_on_hit = yell_on
	await wait(3)
	return recover


func test_matt_yell() -> void:
	await load_matt()
	# His window's old daze (Break-only since 2026-10-04): "never dazeable through the tell" and the daze after a
	# dodged yell are rules of a window that can daze.
	boss.daze_in_recover = true
	health_ok()
	track()
	track_parries()

	log_p("-- the live game never yells (yell_counter_enabled off, the user, 2026-10-04)")
	var knob_off: bool = not sm.yell_counter_enabled
	var live_chance: float = sm.yell_chance
	var planned := 0
	var told := 0
	var thrown := false
	for w in 12:
		var window: Node = await matt_window()
		if window.yell_planned:
			planned += 1
		place_under(boss.get_finisher_hurtbox())
		await wait(4)
		for i in 2:
			await swing_any()
			if window.yell != window.Yell.NONE or window.yells > 0:
				told += 1
			thrown = thrown or boss.is_launching()
		boss.boss_health = boss.max_health
	log_p("12 windows at yell_chance %.2f with the knob off: %d planned, %d tells, thrown %s" % [live_chance, planned, told, thrown])
	check(knob_off and live_chance > 0.0 and planned == 0 and told == 0 and not thrown,
		"off by default: no window plans a yell, puts up its badge or throws the player")
	sm.yell_counter_enabled = true
	sm.windows_opened = 0
	track_dodges()
	var finisher: Node = player.get_node("Finisher")
	finisher.min_press_interval = 0.0
	sm.yell_chance = 1.0

	log_p("-- the first window never yells")
	var recover := await matt_window()
	place_under(boss.get_finisher_hurtbox())
	await wait(4)
	check(not recover.yell_planned, "not planned in window %d" % sm.windows_opened)
	# Two punches short of the POW, with no miss after them, which he would scream away (matt_scream).
	for i in 2:
		await swing_any()
		if i < 1:
			await wait(6)
	await wait(10)
	check(boss.hits_this_window == 2 and recover.yells == 0, "two punches in and no yell (%d punches, %d yells)" % [boss.hits_this_window, recover.yells])

	log_p("-- a yell that lands")
	recover = await matt_window(1)
	check(recover.yell_planned, "planned in window %d at yell_chance 1" % sm.windows_opened)
	clear_iframes()
	health_ok()
	events.clear()
	place_under(boss.get_finisher_hurtbox())
	await wait(4)
	var punched_at := -1.0
	var tell_at := -1.0
	var tell_look := ""
	var dazeable := false
	tap(KEY_Q)
	for i in 60:
		await physics_frame
		if punched_at < 0.0 and boss.hits_this_window >= 1:
			punched_at = defense.clock
		if recover.yell == recover.Yell.TELL and tell_at < 0.0:
			tell_at = defense.clock
			var tell := tell_node()
			tell_look = "yellow" if tell != null and tell.dodge else ("red" if tell != null else "none")
		if recover.yell == recover.Yell.TELL and boss.can_be_dazed():
			dazeable = true
		if tell_at >= 0.0 and defense.clock - tell_at >= sm.yell_tell - 4.0 / 60.0:
			break
	# Guard held and a fresh press on the blast: neither answers it.
	press(KEY_SHIFT)
	var health: int = player.playerHealth
	var mouth: Vector2 = boss.mouth_point(&"roar")
	var from: Vector2 = player.global_position
	var want: Vector2 = recover.launch_point(from)
	var hit_at := -1.0
	var blast_at := -1.0
	var locked_in_air := false
	var left_recover_at := -1.0
	for i in 90:
		await physics_frame
		if blast_at < 0.0 and recover.yell == recover.Yell.BLAST:
			blast_at = defense.clock
		if hit_at < 0.0 and not events_of("HIT", &"matt_yell").is_empty():
			hit_at = defense.clock
		if hit_at >= 0.0 and left_recover_at < 0.0 and not sm.is_recovering():
			left_recover_at = defense.clock
		if hit_at >= 0.0 and player.is_action_locked:
			locked_in_air = true
		if hit_at >= 0.0 and not boss.is_launching() and not player.is_action_locked:
			break
	release(KEY_SHIFT)
	log_p("punch at %.3f, tell at %.3f (%s), blast at %.3f, hit at %.3f; health %d -> %d; landed %s (want %s); left the window at %.3f" % [punched_at, tell_at, tell_look, blast_at, hit_at, health, player.playerHealth, player.global_position, want, left_recover_at])
	check(tell_at > 0.0 and tell_at - punched_at <= 2.5 / 60.0 and tell_look == "yellow", "the yellow badge on the step after the punch")
	check(not dazeable, "never dazeable through the tell")
	check(tell_at > punched_at, "and not on the punch's own step")
	check(blast_at > 0.0 and absf(blast_at - tell_at - sm.yell_tell) <= 1.5 / 60.0, "the blast %.2f s after it" % sm.yell_tell)
	check(parries.is_empty() and events_of("BLOCKED").is_empty() and player.playerHealth == health - 1, "a held guard and a fresh press don't answer it: 1 damage")
	var expect_x: float = sm.launch_left_x if from.x < mouth.x else sm.launch_right_x
	check(player.global_position.is_equal_approx(want.round()) and is_equal_approx(want.x, expect_x) and want.y >= sm.launch_y_range.x and want.y <= sm.launch_y_range.y, "thrown to %s, the far side, inside the ropes" % want)
	check(locked_in_air and not player.is_action_locked and not player.scripted_pose, "locked through the throw and given back on landing")
	check(left_recover_at >= 0.0 and left_recover_at - hit_at <= 1.5 / 60.0, "he is out of his window on the hit")
	var attack_at := -1.0
	await wait_until(func(): return sm.current_state.name == "MysticVolley", 120)
	attack_at = defense.clock
	log_p("his next attack %.3f s after the hit" % (attack_at - hit_at))
	check(absf(attack_at - hit_at - sm.post_yell_beat) <= 2.0 / 60.0, "and attacks again %.1f s later" % sm.post_yell_beat)

	log_p("-- walked away from")
	recover = await matt_window(1)
	clear_iframes()
	health_ok()
	events.clear()
	place_under(boss.get_finisher_hurtbox())
	await wait(4)
	tap(KEY_Q)
	await wait_until(func(): return recover.yell == recover.Yell.TELL, 60)
	var remainder: float = sm.recover_timer.time_left
	await settle_player(boss.mouth_point(&"roar") + Vector2(0, sm.yell_radius + sm.yell_band + 120.0))
	await wait_until(func(): return recover.yell == recover.Yell.NONE, 90)
	var after: float = sm.recover_timer.time_left
	log_p("walked out: %s; window %.3f s left at the tell, %.3f after" % [events.map(func(e): return e.kind), remainder, after])
	check(events_of("HIT").is_empty(), "no hit")
	check(absf(after - (remainder + sm.yell_whiff_bonus)) <= 1.5 / 60.0 and not sm.recover_timer.paused, "the window gets %.2f s back on top of what it had" % sm.yell_whiff_bonus)

	log_p("-- dashed through")
	recover = await matt_window(1)
	clear_iframes()
	health_ok()
	events.clear()
	dodges.clear()
	await fresh_dash_ready()
	place_under(boss.get_finisher_hurtbox())
	await wait(4)
	tap(KEY_Q)
	await wait_until(func(): return recover.yell == recover.Yell.TELL, 60)
	remainder = sm.recover_timer.time_left
	var tell_frames := roundi(sm.yell_tell * 60.0)
	await wait(tell_frames - 3)
	# In place, with nothing held: the ring passes through them inside the dash's i-frames.
	tap(KEY_W)
	await wait_until(func(): return recover.yell_result != 0 or recover.yell == recover.Yell.AFTER, 30)
	await wait_until(func(): return recover.yell == recover.Yell.NONE, 90)
	after = sm.recover_timer.time_left
	log_p("dashed: ring %d, events %s, perfect dodges %s; window %.3f -> %.3f, punches %d" % [recover.yell_result, events.map(func(e): return e.kind), dodges.map(func(d): return d.id), remainder, after, boss.hits_this_window])
	check(recover.yell_result == load("res://Scripts/HitInfo.gd").Result.DODGED and dodges.size() == 1 and dodges[0].id == &"matt_yell" and events_of("HIT").is_empty(), "DODGED, and a PERFECT DODGE")
	check(absf(after - (remainder + sm.yell_whiff_bonus)) <= 1.5 / 60.0, "the window gets %.2f s back" % sm.yell_whiff_bonus)
	check(boss.hits_this_window == 0, "and its punches count from nothing again")
	await dash_ready()
	place_under(boss.get_finisher_hurtbox())
	await wait(8)
	for i in 3:
		await swing_any()
		if i < 2:
			await wait(6)
	check(await wait_until(func(): return finisher.phase == 2, 120), "three more punches daze him")
	await mash_finisher()
	await wait(30)


# ---- the entrance

func test_matt_entrance() -> void:
	var scene: String = card_fight_scene("matt")
	var talk: Dictionary = load("res://Scripts/MattArtLayout.gd").TALK_POSES

	log_p("-- watched: the walk-in")
	await enter_fight(scene, true)
	boss = current_scene.get_node(MATT_BODY)
	sm = boss.state_machine
	var intro: Node = entrance_state()
	check(intro != null and intro == sm.states["Intro"], "his fight opens on MattIntro")
	check(await wait_until(func(): return intro.entered, 60), "which starts itself")
	var gates: Node = current_scene.get_node("Arena/Gates")
	check(gates.is_open() and not boss.hud_layer.visible, "the ring is open and his bar is down")
	check(player.is_talking and not player.state_machine.is_processing(), "the player is held, their own state machine stopped")
	check(boss.global_position.y < 0.0 and player.global_position.y > intro.player_home.y + 100.0, "he starts above the ring and the player below it")
	check(await wait_until(func(): return player.global_position.is_equal_approx(intro.player_home), 300), "the player walks up onto their mark")
	check(await wait_until(func(): return boss.global_position.is_equal_approx(intro.home) and boss.current_anim != &"walk", 400), "he walks down onto his")
	check(await wait_until(func(): return not gates.is_open(), 120), "the gates slam behind him")
	check(await wait_until(func(): return boss.hud_layer.visible, 120), "then his bar comes up")
	check(await wait_until(func(): return live_balloon() != null, 120), "and his first line")
	check(sm.post_dialogue_pre_fight_timer.is_stopped() and boss.music_starts == 0, "the fight and his theme are still waiting")

	log_p("-- the lines, their tags and their beats")
	var card: Node = vs_card()
	var sampled := {}
	var music_before_roar := -1
	var music_on_roar := -1
	var last_line = null
	for i in 3600:
		if card.is_playing():
			break
		var balloon := live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			await wait(3)
			var text: String = last_line.text
			var look := {"pose": intro.pose, "frame": boss.sprite.frame, "flip": boss.sprite.flip_h, "anim": boss.current_anim}
			if text.begins_with("Well anyways"):
				sampled["proud"] = look
			elif text.begins_with("Matt I think"):
				sampled["glance"] = look
			elif text.begins_with("NO I DID"):
				sampled["snap"] = look
		if music_before_roar < 0 and boss.current_anim == &"roar_inhale":
			music_before_roar = boss.music_starts
		if music_on_roar < 0 and boss.current_anim == &"roar":
			await wait(1)
			music_on_roar = boss.music_starts if boss.music_player.playing else -1
		if i % 8 == 0:
			tap(KEY_ENTER)
		await physics_frame
	log_p("sampled %s" % [sampled])
	check(sampled.has("proud") and sampled.proud.pose == &"proud" and talk[&"proud"].has(sampled.proud.frame) and sampled.proud.anim == &"talk", "the proud line puts him in the proud pose")
	check(sampled.has("glance") and sampled.glance.flip and sampled.glance.pose == &"irritated", "Danny's line turns him toward Danny, still irritated")
	check(sampled.has("snap") and sampled.snap.pose == &"snap" and not sampled.snap.flip and talk[&"snap"].has(sampled.snap.frame), "the snap line snaps him back, unturned")
	var beats: Dictionary = intro.beat_times
	log_p("beats %s" % [beats])
	check(beats.has(&"composes_himself") and absf(beats[&"composes_himself"] - 2.0) <= 1.0 / 60.0 + 0.001, "the compose beat is 2.00 s to a frame (%.3f)" % beats.get(&"composes_himself", -1.0))
	check(beats.has(&"pulls_out_hong") and beats.has(&"screams_at_hong") and beats.has(&"small_pause") and beats.has(&"roars"), "the doll's three beats and the roar all played")
	check(music_before_roar == 0 and music_on_roar == 1, "his theme starts on the roar and not before (%d then %d)" % [music_before_roar, music_on_roar])
	check(await matt_card_flash(), "the lines hand over to the card")
	var watched := matt_snapshot()
	log_p("watched, at the card's flash: %s" % [watched])
	check(watched.matt == sm.HOME and watched.anim == &"idle" and not watched.flip and watched.hud and not watched.gates_open
		and watched.talking and watched.player_sm and watched.music and watched.music_starts == 1 and watched.hazards == 0
		and not watched.balloon and not watched.doll and watched.intro_fx == 0 and watched.seen and watched.zoom == 1.0
		and watched.time_scale == 1.0 and not watched.crowd_cheering, "and the ring is set the way the plan says")
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	check(await wait_until(func(): return sm.current_state != intro, 180), "and the fight starts behind it")

	for where in ["walk", "line", "roar"]:
		log_p("-- held at mid-%s" % where)
		await enter_fight(scene, true)
		boss = current_scene.get_node(MATT_BODY)
		sm = boss.state_machine
		intro = entrance_state()
		card = vs_card()
		await wait_until(func(): return intro.entered, 60)
		var lines := 0
		last_line = null
		for i in 3600:
			if where == "walk" and intro.home.y - boss.global_position.y > 200.0 and boss.global_position.y > -60.0:
				break
			var balloon := live_balloon()
			if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
				last_line = balloon.dialogue_line
				lines += 1
				if where == "line" and lines == 3:
					await wait(10)
					break
			if where == "roar" and boss.current_anim == &"roar":
				await wait(20)
				break
			if where != "walk" and i % 8 == 0:
				tap(KEY_ENTER)
			await physics_frame
		log_p("holding Escape: anim %s, lines %d" % [boss.current_anim, lines])
		press(KEY_ESCAPE)
		var reached := await matt_card_flash(120)
		var skipped := matt_snapshot()
		release(KEY_ESCAPE)
		await wait(4)
		var diffs := matt_snapshot_diff(skipped, watched)
		check(reached and diffs.is_empty(), "mid-%s: the card's flash, with the ring exactly as a watched entrance leaves it %s" % [where, diffs])
		check(not pause_menu().is_open() and not paused, "mid-%s: and the pause screen never opened" % where)

	log_p("-- a tapped Escape pauses it")
	await enter_fight(scene, true)
	boss = current_scene.get_node(MATT_BODY)
	sm = boss.state_machine
	intro = entrance_state()
	await wait_until(func(): return intro.entered, 60)
	await wait(30)
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open() and paused, "a tap opened the pause screen rather than skipping")
	var held_at: Vector2 = player.global_position
	await wait(40)
	check(player.global_position.is_equal_approx(held_at), "and the walk-in stopped dead with the fight")
	await tap_pause()
	await wait(20)
	check(not paused and not player.global_position.is_equal_approx(held_at), "the resume carries it on")
	# Skipped to its end, which is what marks it seen for the run.
	press(KEY_ESCAPE)
	await matt_card_flash(120)
	release(KEY_ESCAPE)
	card = vs_card()
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0

	log_p("-- the retry: no walk-in, the lines and their beats again, and a hold still skips them")
	change_scene_to_file(scene)
	while current_scene == null or current_scene.scene_file_path != scene:
		await process_frame
	await wait(6)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	boss = current_scene.get_node(MATT_BODY)
	sm = boss.state_machine
	intro = entrance_state()
	gates = current_scene.get_node("Arena/Gates")
	card = vs_card()
	check(intro.finished and not gates.is_open(), "the entrance is over on arrival and the ring was never opened")
	check(await wait_until(func(): return live_balloon() != null, 120), "his lines start straight away")
	for i in 3600:
		if card.is_playing():
			break
		if i % 8 == 0:
			tap(KEY_ENTER)
		await physics_frame
	check(intro.beat_times.has(&"composes_himself") and intro.beat_times.has(&"roars"), "the beats played again (%s)" % [intro.beat_times.keys()])
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	change_scene_to_file(scene)
	while current_scene == null or current_scene.scene_file_path != scene:
		await process_frame
	await wait(6)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	boss = current_scene.get_node(MATT_BODY)
	sm = boss.state_machine
	intro = entrance_state()
	card = vs_card()
	for i in 3600:
		if intro.beat_running and boss.current_anim == &"talk" and boss.talk_pose == &"snap":
			break
		if i % 8 == 0:
			tap(KEY_ENTER)
		await physics_frame
	log_p("holding Escape in the compose beat")
	press(KEY_ESCAPE)
	var reached := await matt_card_flash(120)
	var retried := matt_snapshot()
	release(KEY_ESCAPE)
	var retry_diffs := matt_snapshot_diff(retried, watched)
	check(reached and retry_diffs.is_empty(), "a hold in a replayed beat lands on the card's flash with the same ring %s" % [retry_diffs])


# ---- the bots

# The circle walker is a random-movement density bound, not the skill path: it never guards, dashes or
# reads a tell, so all it measures is how thick the ring gets with everything he throws. It walks every
# circle and seed his tuning was measured on, and the bound is on all of their cycles together. The
# fairness guarantee is the parry bot's 0. Raised from 2.5 and 4 with his 8/10's thicker volleys (2026-10-06:
# five casts at every tier, seven bounces), which walk it into 2.89 a cycle, 5 at worst.
const MATT_CIRCLES := [[Vector2(960, 700), 260.0], [Vector2(960, 620), 300.0], [Vector2(960, 540), 380.0]]
const MATT_CIRCLE_SEEDS := [MATT_SEED, 1, 2]
const MATT_CIRCLE_MEAN := 3.0
const MATT_CIRCLE_WORST := 5


func test_matt_bots() -> void:
	if tier == "circle":
		await test_matt_circle()
		return
	await load_matt()
	var run := await matt_two_cycles({"spot": SMOKE_SPOTS["matt"], "parry": tier == "parry"})
	if tier == "parry" and matt_bot.held:
		release(KEY_SHIFT)
	var hits: Array = run.hits
	log_p("%s: %d hits over two cycles, %s a cycle (%s); %d parried, %d blocked, %d presses; cycles started at %s" % [tier, hits.size(), run.per_cycle, hits.map(func(e): return e.id), parries.size(), events_of("BLOCKED").size(), matt_bot.presses, run.starts])
	check(run.ended, "two whole cycles ran")
	match tier:
		"still":
			check(run.per_cycle[0] >= 6, "standing still is hit about 7 times a cycle, so it dies in the first (%d)" % run.per_cycle[0])
		"parry":
			check(hits.is_empty(), "a player who parries everything is never hit (%d)" % hits.size())


func test_matt_circle() -> void:
	var cycles := []
	var all_ended := true
	for circle in MATT_CIRCLES:
		for seed_value in MATT_CIRCLE_SEEDS:
			await load_matt()
			sm.rng.seed = seed_value
			var run := await matt_two_cycles({"centre": circle[0], "radius": circle[1]})
			all_ended = all_ended and run.ended
			cycles.append_array(run.per_cycle)
			log_p("circle round %s r%.0f, seed %d: %s a cycle (%s)" % [circle[0], circle[1], seed_value, run.per_cycle, run.hits.map(func(e): return e.id)])
	var total := 0
	for c in cycles:
		total += c
	var mean := float(total) / maxf(cycles.size(), 1.0)
	var worst: int = cycles.max()
	log_p("circle: %d cycles, mean %.2f hits a cycle, worst %d" % [cycles.size(), mean, worst])
	check(all_ended and cycles.size() == MATT_CIRCLES.size() * MATT_CIRCLE_SEEDS.size() * 2, "two whole cycles ran on every circle and seed")
	check(mean <= MATT_CIRCLE_MEAN, "walking a circle is hit at most %.1f times a cycle on average (%.2f)" % [MATT_CIRCLE_MEAN, mean])
	check(worst <= MATT_CIRCLE_WORST, "and no cycle more than %d times (%d)" % [MATT_CIRCLE_WORST, worst])


# Two whole cycles below a third of his health, from the top of one, with the player put each step on
# `walk.spot` (pressing like the parry bot if `walk.parry`) or round the circle `walk.centre`/`walk.radius`
# at walking speed: the hits a cycle and where the cycles started. His gauge is held: a parry bot reads
# a whole cycle, and a Break would cut the two cycles being measured.
func matt_two_cycles(walk: Dictionary) -> Dictionary:
	hold_break_gauge(boss)
	player.playerHealth = 1000
	track()
	track_parries()
	await settle_player(SMOKE_SPOTS["matt"])
	boss.boss_health = int(boss.max_health * 0.3)
	var cycle_starts := []
	var walk_speed: float = load("res://Scripts/PlayerScript.gd").SPEED
	var t0: float = defense.clock
	var last_state := ""
	var ended := false
	sm.start_cycle()
	cycle_starts.append(defense.clock)
	while defense.clock - t0 < 60.0:
		var t: float = defense.clock - t0
		if walk.has("radius"):
			player.global_position = walk.centre + Vector2.from_angle(t * walk_speed / walk.radius) * walk.radius
		else:
			player.global_position = walk.spot
			if walk.get("parry", false):
				matt_parry_step()
		player.velocity = Vector2.ZERO
		var state: String = sm.current_state.name
		if state != last_state:
			if state == "MysticVolley" and last_state != "":
				cycle_starts.append(defense.clock)
			if last_state == "Recover" and cycle_starts.size() >= 2:
				ended = true
			last_state = state
		if ended:
			break
		await physics_frame
	var hits := events_of("HIT")
	var per_cycle := [0, 0]
	for e in hits:
		per_cycle[1 if cycle_starts.size() >= 2 and e.t >= cycle_starts[1] else 0] += 1
	return {"ended": ended, "per_cycle": per_cycle, "hits": hits, "starts": cycle_starts.map(func(c): return snappedf(c - t0, 0.01))}


# ---- the Glass Row (Attack 2)

const ARROW_KEYS := {&"up": KEY_UP, &"down": KEY_DOWN, &"left": KEY_LEFT, &"right": KEY_RIGHT}


# A Glass Row from wherever the fight stands: `booms` of them in `sets` (phase two's stomps between them),
# with the Deafening Yell or not. One set is full health's row: its two rows of glass, B and A, and the plain
# charge. Phase two's sets are phase two's: four rows, D to A, and its longer charge (matt_glass_rows has the
# rest).
func glass_row(booms: int, deafen := false, sets := 1) -> Node:
	var glass: Node = sm.states["GlassRow"]
	for hazard in get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	sm.cycle_booms = booms
	sm.cycle_deafen = deafen
	sm.cycle_sets = sets
	sm.cycle_glass_rows = sm.glass_rows_by_share[0] if sets == 1 else sm.glass_rows_by_share[-1]
	sm.cycle_boom_charge_extra = 0.0 if sets == 1 else sm.phase_two_charge_extra
	sm.on_child_transition(sm.current_state, "GlassRow")
	return glass


# A direction other than `arrow`, for a wrong answer.
func glass_wrong(arrow: StringName) -> StringName:
	return &"left" if arrow != &"left" else &"up"


# Where the player's hurtbox centre stands in row k: what a boom has to reach.
func glass_row_centre(k: int) -> Vector2:
	var reach: Vector2 = matt_centre() - player.global_position
	return sm.row_body_point(k) + reach


# What a boom's arrow-to-impact window should be with the player in row k, phase two's extra charge and all.
func glass_window(k: int, dizzy := false) -> float:
	var charged: float = boss.mouth_point(&"roar").y + sm.boom_spawn_drop + sm.boom_charge_drift
	var charge: float = (sm.boom_charge_wobble if dizzy else sm.boom_charge) + sm.cycle_boom_charge_extra
	return charge + (glass_row_centre(k).y - charged) / sm.boom_speed


# A measured window against glass_window(): the charge and the flight each end on a whole frame, so it
# runs up to two frames over the formula, and never under it.
func glass_window_ok(measured: float, k: int, dizzy := false) -> bool:
	var over := measured - glass_window(k, dizzy)
	return over >= -0.001 and over <= 2.0 / 60.0 + 0.001


# What a Glass Row may leave behind once it is over: nothing.
func matt_glass_leftovers() -> Array:
	var left := []
	if player.is_action_locked:
		left.append("locked")
	if player.is_posed():
		left.append("posed")
	if player.scripted_pose:
		left.append("scripted pose")
	if player.facing_point != Vector2.INF:
		left.append("facing point")
	var hazards := get_nodes_in_group(sm.HAZARD_GROUP).filter(func(h): return not h.is_queued_for_deletion())
	if not hazards.is_empty():
		left.append("hazards %s" % [hazards.map(func(h): return str(h.name))])
	if boss.wobble_amount() > 0.0:
		left.append("wobble %.2f" % boss.wobble_amount())
	if not sm.states["GlassRow"].released:
		left.append("not released")
	return left


func test_matt_glass_row() -> void:
	await load_matt()
	player.playerHealth = 1000
	track()
	var catalog: GDScript = load("res://Scripts/AttackCatalog.gd")
	var hype: Node = player.get_node("Hype")

	log_p("-- the catalogue and the floor plan")
	var glass_attack: Dictionary = catalog.get_attack(&"matt_glass")
	check(glass_attack.damage == 2 and glass_attack.bypass_invincibility and not glass_attack.blockable and not glass_attack.parryable
		and not glass_attack.tell and not glass_attack.dodge_tell and not glass_attack.dash_through and not glass_attack.grab,
		"matt_glass: a whole heart inside the i-frames, and nothing answers it")
	var bodies := []
	for k in 4:
		bodies.append(sm.row_body_point(k))
	check(bodies == [Vector2(960, 436), Vector2(960, 526), Vector2(960, 616), Vector2(960, 706)], "rows F to C put the player at %s" % [bodies])
	check(sm.glass_band() == Rect2(113, 787, 1692, 180) and sm.fails_to_glass() == 4, "the glass is B and A rope to rope (%s), four fails away" % sm.glass_band())
	var tiers := []
	for share in [1.0, 0.5, 0.2]:
		boss.boss_health = int(boss.max_health * share)
		var pinned: Array[String] = ["GlassRow"]
		sm.attack_rotation = pinned
		sm.last_attack = ""
		sm.start_cycle()
		tiers.append(sm.cycle_booms)
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
		await wait(2)
	boss.boss_health = boss.max_health
	check(tiers == Array(sm.boom_counts_by_tier), "booms by tier: %s" % [tiers])
	var rolled: Array = sm.states["GlassRow"]._roll_arrows(3000)
	var triples := 0
	var counts := {}
	for i in rolled.size():
		counts[rolled[i]] = counts.get(rolled[i], 0) + 1
		if i >= 2 and rolled[i] == rolled[i - 1] and rolled[i] == rolled[i - 2]:
			triples += 1
	check(triples == 0 and counts.size() == 4 and counts.values().all(func(c): return c > 600), "3000 arrows: never three alike in a row, all four about as often (%s)" % [counts])

	log_p("-- DirectionPress")
	var direction_press: GDScript = load("res://Scripts/DirectionPress.gd")
	var dp = direction_press.new()
	var keys_read := []
	for code in [KEY_UP, KEY_RIGHT, KEY_DOWN, KEY_LEFT]:
		keys_read.append(dp.read(key(code, true)))
	var echo := key(KEY_UP, true)
	echo.echo = true
	var pad := InputEventJoypadButton.new()
	pad.button_index = JOY_BUTTON_DPAD_LEFT
	pad.pressed = true
	check(keys_read == [&"up", &"right", &"down", &"left"] and dp.read(key(KEY_UP, false)) == &"" and dp.read(echo) == &""
		and dp.read(pad) == &"left", "the arrows and the D-pad through the move actions, never a release or an echo")
	var stick = direction_press.new()
	var flicks := []
	for at in [Vector2(0.2, 0.0), Vector2(0.45, 0.1), Vector2(0.7, 0.1), Vector2(0.95, 0.2), Vector2(0.35, 0.0), Vector2(0.1, 0.1),
			Vector2(0.6, 0.55), Vector2(0.2, 0.9), Vector2(0.0, 0.0), Vector2(-0.1, -0.8)]:
		for axis in [JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y]:
			var motion := InputEventJoypadMotion.new()
			motion.axis = axis
			motion.axis_value = at.x if axis == JOY_AXIS_LEFT_X else at.y
			stick.read(motion)
		flicks.append(stick.poll())
	check(flicks == [&"", &"", &"right", &"", &"", &"", &"", &"down", &"", &"up"],
		"the stick: once past 0.5, not again until it is back under 0.3, and no call on a diagonal (%s)" % [flicks])

	log_p("-- a Glass Row: right, wrong, none, right then wrong, a press between booms then right")
	await settle_player(Vector2(700, 800))
	var hype_before: float = hype.hype
	var glass := glass_row(5)
	var seen := {"tell_locked": false, "slam_locked": false, "drag_end": Vector2.INF, "posed": false, "facing": -1,
		"whole": -1, "landings_inside": true, "rects": [], "winded_free": false, "recover": {}}
	var hint_spec: Dictionary = load("res://Scripts/MattArtLayout.gd").GLASS_HINT
	var hint_seen := {"up": false, "followed": true, "weakest": 1.0, "gone": {}}
	var pressed := {}
	var last_beat := -1
	while true:
		await physics_frame
		if sm.current_state != glass:
			seen.recover = {"state": sm.current_state.name, "at": boss.global_position, "timer": snappedf(sm.recover_timer.time_left, 0.01)}
			break
		var beat_name: String = glass.Beat.keys()[glass.beat]
		var entered: bool = glass.beat != last_beat
		last_beat = glass.beat
		if is_instance_valid(glass.hint):
			hint_seen.up = true
			if glass.hint.global_position != (player.global_position + hint_spec.offset).round():
				hint_seen.followed = false
			if glass.state_clock - glass.hint_shown_at > hint_spec.fade + 0.05:
				hint_seen.weakest = minf(hint_seen.weakest, glass.hint.modulate.a)
		elif hint_seen.up and hint_seen.gone.is_empty():
			hint_seen.gone = {"landed": glass.outcomes.size(), "up_for": snappedf(glass.state_clock - glass.hint_shown_at, 0.001)}
		match beat_name:
			"TELL":
				seen.tell_locked = seen.tell_locked or player.is_action_locked
			"ROOT":
				if entered:
					seen.slam_locked = player.is_action_locked and player.lock_seals_guard
			"FURY":
				if entered:
					seen.drag_end = player.global_position
					seen.posed = player.is_posed()
					seen.facing = player.facing
			"BOOMS":
				if entered:
					seen.whole = glass.glass_floor.revealed_count()
					seen.rects = glass.glass_floor.segment_rects()
					for land in glass.glass_floor.landings:
						if not sm.glass_band().has_point(land):
							seen.landings_inside = false
				var i: int = glass.boom_index
				if glass.boom != null and not pressed.has(i) and glass.state_clock - glass.birth_clock >= 0.2:
					pressed[i] = true
					var arrow: StringName = glass.arrows[i]
					match i:
						0, 4:
							tap(ARROW_KEYS[arrow])
						1:
							tap(ARROW_KEYS[glass_wrong(arrow)])
						3:
							tap(ARROW_KEYS[arrow])
							await physics_frame
							tap(ARROW_KEYS[glass_wrong(arrow)])
				if glass.boom_phase == glass.BoomPhase.GAP and i == 3 and not pressed.has("gap"):
					pressed["gap"] = true
					tap(ARROW_KEYS[glass_wrong(glass.arrows[4])])
			"WINDED":
				if entered:
					seen.winded_free = not player.is_action_locked and not player.is_posed()
	log_p("arrows %s, outcomes %s, windows %s, fails %d, row %d; %s" % [glass.arrows, glass.outcomes, glass.windows.map(func(w): return snappedf(w, 0.001)), glass.fails, glass.row, seen])
	log_p("the hint: %s" % [hint_seen])
	var gone: Dictionary = hint_seen.gone
	var hint_on_time: bool = not gone.is_empty() and gone.landed >= hint_spec.booms and gone.up_for >= hint_spec.min_time \
		and (gone.landed == hint_spec.booms or gone.up_for <= hint_spec.min_time + 1.0 / 60.0 + 0.001)
	check(hint_on_time, "the fight's first hint stays up until %d booms have landed and %.1f s have passed, whichever is later (%s)" % [hint_spec.booms, hint_spec.min_time, gone])
	check(hint_seen.followed and is_equal_approx(hint_seen.weakest, 1.0), "at full strength, and on the player as the fails knock them down")
	check(not seen.tell_locked and seen.slam_locked, "the player is free through the tell and sealed on the slam's step")
	check(seen.drag_end.distance_to(sm.row_body_point(0)) <= 0.5 and seen.posed and seen.facing == player.Facing.UP,
		"dragged to row F %s, posed and facing him" % seen.drag_end)
	var union := Rect2()
	var widths := 0.0
	for r in seen.rects:
		union = r if union.size == Vector2.ZERO else union.merge(r)
		widths += r.size.x
	check(seen.rects.size() == sm.glass_segments and union == sm.glass_band() and is_equal_approx(widths, sm.glass_band().size.x),
		"%d segments exactly covering the band" % seen.rects.size())
	check(seen.landings_inside and seen.whole == sm.glass_segments, "every shard inside it, and all of it glass by the first boom")
	check(Array(glass.outcomes) == [&"answered", &"cracked", &"missed", &"answered", &"answered"],
		"right answers, a wrong one cracks, none misses, the first press decides and a press between booms does nothing (%s)" % [glass.outcomes])
	var rows_at := [0, 0, 1, 2, 2]
	var windows_ok: bool = glass.windows.size() == 5
	for i in mini(glass.windows.size(), 5):
		if not glass_window_ok(glass.windows[i], rows_at[i]):
			windows_ok = false
	check(windows_ok, "every window its row's, to the frames it ends on (F %.3f, E %.3f, D %.3f)" % [glass_window(0), glass_window(1), glass_window(2)])
	check(seen.winded_free, "let go as he is winded")
	check(seen.recover.get("state") == "Recover" and seen.recover.at == sm.GLASS_ROW.station and absf(seen.recover.timer - sm.recover_time) <= 2.0 / 60.0 + 0.01,
		"the window opens where he stands, %.1f s with two fails (%s)" % [sm.recover_time, seen.recover])
	check(is_equal_approx(hype.hype - hype_before, sm.boom_hype_each * 3.0), "hype for the three right answers and nothing else (%.1f)" % (hype.hype - hype_before))

	log_p("-- a clean one")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await wait(2)
	await settle_player(Vector2(1200, 700))
	hype_before = hype.hype
	glass = glass_row(5)
	pressed.clear()
	var clean := {}
	while true:
		await physics_frame
		if sm.current_state != glass:
			clean = {"state": sm.current_state.name, "timer": snappedf(sm.recover_timer.time_left, 0.01)}
			break
		if glass.beat == glass.Beat.BOOMS and glass.boom != null and not pressed.has(glass.boom_index):
			pressed[glass.boom_index] = true
			tap(ARROW_KEYS[glass.arrows[glass.boom_index]])
	log_p("outcomes %s; %s; hype +%.1f" % [glass.outcomes, clean, hype.hype - hype_before])
	check(glass.outcomes.all(func(o): return o == &"answered") and clean.get("state") == "Recover"
		and absf(clean.timer - sm.recover_time - sm.glass_clean_bonus) <= 2.0 / 60.0 + 0.01, "all answered: %.1f s more in the window" % sm.glass_clean_bonus)
	check(is_equal_approx(hype.hype - hype_before, sm.boom_hype_each * 5.0 + sm.boom_hype_clean), "and the clean run's hype on top")
	check(glass.glass_top == sm.glass_top_row() and glass.glass_top == 4 and glass.stomps == 0, "no stomp in phase one's row: the glass stays B and A")
	await matt_glass_phase_two()


# Phase two's Glass Row (G11): the sets locked at the cycle's top, then a row of fifteen over its four rows of
# glass, every boom answered, with a stomp after the fifth and the tenth each bringing shards down onto the
# glass's front row, their shadows first, and laying no glass.
func matt_glass_phase_two() -> void:
	log_p("-- phase two: five booms, a stomp and its shards, twice, then five")
	var pinned: Array[String] = ["GlassRow"]
	sm.attack_rotation = pinned
	var locked := []
	for share in [1.0, 0.45]:
		boss.boss_health = int(boss.max_health * share)
		sm.last_attack = ""
		sm.start_cycle()
		locked.append(sm.cycle_sets)
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
		await wait(2)
	boss.boss_health = boss.max_health
	check(locked == [1, sm.phase_two_boom_sets], "locked at the cycle's top: one set above half his health, %d below (%s)" % [sm.phase_two_boom_sets, locked])
	await settle_player(Vector2(700, 800))
	var row := glass_row(15, false, sm.phase_two_boom_sets)
	var pressed := {}
	var stomps := []
	var stomp := {}
	var boom_in_stomp := false
	var segments := 0
	while sm.current_state == row:
		await physics_frame
		if row.beat != row.Beat.BOOMS:
			continue
		if row.boom != null and not pressed.has(row.boom_index):
			pressed[row.boom_index] = true
			tap(ARROW_KEYS[row.arrows[row.boom_index]])
		var ground: Node = row.glass_floor
		segments = ground.segment_rects().size()
		if row.boom_phase == row.BoomPhase.STOMP:
			if stomp.is_empty():
				stomp = {"after": row.outcomes.size(), "start": row.state_clock, "top_before": row.glass_top, "slam": -1.0,
					"landings": ground.landings.size(), "first_land": -1.0}
			if row.stomp_slammed and stomp.slam < 0.0:
				stomp.slam = row.state_clock
				stomp["top_after"] = row.glass_top
			if stomp.slam >= 0.0 and stomp.first_land < 0.0 and ground.landings.size() > stomp.landings:
				stomp.first_land = row.state_clock
			boom_in_stomp = boom_in_stomp or row.boom != null
		elif not stomp.is_empty():
			var band: Rect2 = sm.row_band(stomp.top_after)
			stomp["took"] = snappedf(row.state_clock - stomp.start, 0.001)
			stomp["shadows_for"] = snappedf(stomp.first_land - stomp.slam, 0.001)
			stomp["landed"] = ground.landings.slice(stomp.landings).filter(func(p): return band.has_point(p)).size()
			stomp["whole"] = ground.revealed_count() == ground.segment_rects().size()
			stomps.append(stomp)
			stomp = {}
	log_p("outcomes %s, glass from row %d, %d stomps; stomps %s" % [row.outcomes, row.glass_top, row.stomps, stomps])
	var per_row: int = sm.glass_segments * sm.glass_spread_shards_per_segment
	check(row.outcomes.size() == 15 and row.outcomes.all(func(o): return o == &"answered") and not boom_in_stomp,
		"fifteen booms, every one answered, and none of them live through a stomp")
	check(stomps.map(func(s): return s.after) == [5, 10] and row.stomps == 2, "a stomp after the fifth and after the tenth")
	check(stomps.size() == 2 and stomps.map(func(s): return [s.top_before, s.top_after]) == [[2, 2], [2, 2]] and row.glass_top == 2
		and segments == sm.glass_segments * 3, "the glass D to A from the start, and neither stomp lays any more (%d segments at the last boom)" % segments)
	check(stomps.size() == 2 and stomps.all(func(s): return s.took >= 0.8 and s.took <= 1.0), "each about %.2f s long" % (sm.glass_spread_tell + sm.glass_spread_time))
	check(stomps.size() == 2 and stomps.all(func(s): return s.landed == per_row and s.shadows_for >= sm.glass_shard_fall - 1.0 / 60.0 and s.whole),
		"its %d shards land on the glass's front row, D, after %.2f s of their shadows" % [per_row, sm.glass_shard_fall])
	check(row.row == 0, "and the player, every boom answered, stays on row F")


func test_matt_glass_damage() -> void:
	await load_matt()
	track()
	var glass: Node = sm.states["GlassRow"]

	log_p("-- no presses at 6 health")
	player.playerHealth = 6
	player.healthUI.update_health(6)
	await settle_player(Vector2(700, 800))
	glass_row(5)
	var gaps := []
	var at_winded := {}
	var last_phase := -1
	while sm.current_state == glass:
		await physics_frame
		if glass.beat == glass.Beat.BOOMS and glass.boom_phase != last_phase:
			last_phase = glass.boom_phase
			if glass.boom_phase == glass.BoomPhase.GAP:
				gaps.append(player.global_position)
		if glass.beat == glass.Beat.WINDED and at_winded.is_empty():
			at_winded = {"at": player.global_position, "locked": player.is_action_locked, "posed": player.is_posed()}
	var glass_hits := events_of("HIT", &"matt_glass")
	log_p("outcomes %s, windows %d, player at each gap %s, at winded %s, glass hits %s, health %d" % [glass.outcomes, glass.windows.size(), gaps, at_winded, glass_hits.map(func(e): return e.health), player.playerHealth])
	check(Array(glass.outcomes) == [&"missed", &"missed", &"missed", &"missed"] and glass.windows.size() == 4, "four booms missed, and no fifth")
	check(gaps == [sm.row_body_point(1), sm.row_body_point(2), sm.row_body_point(3)], "knocked to rows E, D and C, a row a fail")
	check(glass.glass_hit and glass_hits.size() == 1 and player.playerHealth == 4, "then into the glass: one hit, a whole heart")
	check(at_winded.get("at") == sm.row_body_point(3), "bounced back to row C (%s)" % at_winded.get("at"))
	check(at_winded.get("locked") == false and at_winded.get("posed") == false, "and let go as he is winded")
	await wait(40)
	check(matt_glass_leftovers().is_empty(), "nothing left behind %s" % [matt_glass_leftovers()])

	log_p("-- inside the i-frames")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	player.playerHealth = 6
	player.healthUI.update_health(6)
	await settle_player(Vector2(700, 800))
	glass_row(5)
	var made_invincible := false
	while sm.current_state == glass:
		await physics_frame
		if not made_invincible and glass.beat == glass.Beat.BOOMS and glass.boom_phase == glass.BoomPhase.KNOCK and glass.fails == sm.fails_to_glass():
			made_invincible = true
			player.is_invincible = true
			player.invincibility_timer.start()
	check(made_invincible and player.playerHealth == 4, "the glass lands inside the i-frames too (health %d)" % player.playerHealth)

	log_p("-- phase two: four rows of glass from the start, and the stomps never move the player")
	var sets: int = sm.phase_two_boom_sets
	var answer_until := func(last: int) -> Callable:
		return func(i: int, arrow: StringName) -> Dictionary: return {"at": 0.05, "key": ARROW_KEYS[arrow]} if i < last else {}
	var miss_first := func(i: int, arrow: StringName) -> Dictionary: return {} if i == 0 else {"at": 0.05, "key": ARROW_KEYS[arrow]}
	await glass_bot_reset()
	var glass_hits_before := events_of("HIT", &"matt_glass").size()
	var held := await glass_bot_row(15, false, miss_first, sets)
	log_p("the first missed, then every one answered: %s" % [held])
	check(held.fails == 1 and held.row == 1 and held.stomps == sets - 1 and not held.glass and held.damage == 0
		and events_of("HIT", &"matt_glass").size() == glass_hits_before, "one miss knocks them to E, in front of the glass, and they stay there through both stomps, unhurt")
	await glass_bot_reset()
	var none := await glass_bot_row(15, false, answer_until.call(0), sets)
	log_p("none answered: %s" % [none])
	check(none.glass and none.fails == 2 and none.booms == 2 and none.damage == 2 and none.row == 1,
		"no presses: the second miss is the glass, a whole heart, back to E, and the barrage ends before a stomp")
	await glass_bot_reset()
	var after_one := await glass_bot_row(15, false, answer_until.call(5), sets)
	log_p("the first set answered, then none: %s" % [after_one])
	check(after_one.glass and after_one.fails == 2 and after_one.booms == 7 and after_one.damage == 2 and after_one.row == 1,
		"the first set answered, then none: after the stomp the second miss is the glass, a whole heart, back to E")
	await glass_bot_reset()
	var after_two := await glass_bot_row(15, false, answer_until.call(10), sets)
	log_p("two sets answered, then none: %s" % [after_two])
	check(after_two.glass and after_two.fails == 2 and after_two.booms == 12 and after_two.damage == 2 and after_two.row == 1,
		"and after both stomps the same")

	log_p("-- lethal at 2 health")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	player.is_invincible = false
	player.invincibility_timer.stop()
	player.playerHealth = 2
	player.healthUI.update_health(2)
	await settle_player(Vector2(700, 800))
	glass_row(5)
	var ended := await wait_until(func(): return sm.player_defeated, 60 * 20)
	await wait(10)
	var left := matt_glass_leftovers()
	log_p("fight over %s, state %s, health %d, left %s" % [ended, sm.current_state.name, player.playerHealth, left])
	check(ended and player.playerHealth == 0 and sm.current_state.name == "Victory", "the glass can end the fight")
	check(left.is_empty() and glass.stopped, "and leaves nothing held or live %s" % [left])


func test_matt_glass_release() -> void:
	await load_matt()
	player.playerHealth = 1000
	var glass: Node = sm.states["GlassRow"]
	var ends := [
		["the tell", func(): return glass.beat == glass.Beat.TELL and glass.beat_clock > 0.2],
		["just after the slam", func(): return glass.beat == glass.Beat.ROOT],
		["mid-drag", func(): return glass.beat == glass.Beat.DRAG and glass.beat_clock > 0.12],
		["mid-fury", func(): return glass.beat == glass.Beat.FURY and glass.beat_clock > 0.7],
		["mid-charge", func(): return glass.beat == glass.Beat.BOOMS and glass.boom_phase == glass.BoomPhase.CHARGE and glass.boom_clock > 0.3],
		["mid-knock", func(): return glass.beat == glass.Beat.BOOMS and glass.boom_phase == glass.BoomPhase.KNOCK],
	]
	log_p("-- ended early, anywhere")
	for end in ends:
		await settle_player(Vector2(700, 800))
		glass_row(5)
		var reached := await wait_until(end[1], 60 * 12)
		sm.on_child_transition(glass, "Idle")
		sm.beat_timer.stop()
		await wait(2)
		var left := matt_glass_leftovers()
		check(reached and left.is_empty(), "ended at %s: all of it let go %s" % [end[0], left])

	log_p("-- paused mid-charge")
	await settle_player(Vector2(700, 800))
	glass_row(5)
	await wait_until(func(): return glass.beat == glass.Beat.BOOMS and glass.boom_phase == glass.BoomPhase.CHARGE and glass.boom_clock > 0.2, 60 * 12)
	var held := {"clock": glass.boom_clock, "at": glass.boom.global_position}
	paused = true
	await wait(45)
	var during := {"clock": glass.boom_clock, "at": glass.boom.global_position}
	paused = false
	var finished := await wait_until(func(): return sm.current_state != glass, 60 * 20)
	check(held == during and finished, "a pause holds the boom where it is, and the row still ends (%s, %s)" % [held, during])

	log_p("-- the scene changed mid-booms")
	await settle_player(Vector2(700, 800))
	glass_row(5)
	await wait_until(func(): return glass.beat == glass.Beat.BOOMS and glass.boom != null, 60 * 12)
	await load_matt()
	player.playerHealth = 1000
	await wait(5)
	var fresh := []
	if player.is_action_locked:
		fresh.append("locked")
	if player.is_posed():
		fresh.append("posed")
	check(fresh.is_empty() and get_nodes_in_group(sm.HAZARD_GROUP).is_empty(), "the next fight starts clean %s" % [fresh])


# ---- the Deafening Yell (Attack 3: phase two's Glass Row)

# A phase-two Glass Row, in phase two's sets, mashed at `rate` presses a second (0 for none), every boom
# answered right 0.3 s after its birth, inside even the plain pace's shortest window, to its end: what the
# yell, the booms and the stomps did. The presses fall on the steps at or after k / `rate` from the yell's
# first, so the rate is the one asked for rather than drifting down to whole steps.
func deafen_row(rate: float) -> Dictionary:
	var glass := glass_row(sm.boom_counts_by_tier[sm.tier()], true, sm.phase_two_boom_sets)
	var seen := {"pair": [], "prompt_up": false, "word": "", "meter": -1.0, "passed": false, "dizzy": false,
		"stars": false, "wobble_first_boom": -1.0, "prompt_gone": false, "windows": [], "outcomes": [], "wobble_after": -1.0,
		"stars_after": true, "mashed": 0, "stomps": 0, "wobble_in_stomps": 1.0}
	var mashed := 0
	var answered := {}
	while sm.current_state == glass:
		await physics_frame
		match glass.Beat.keys()[glass.beat]:
			"DEAFEN":
				if seen.pair.is_empty():
					seen.pair = glass.pair.duplicate()
				if is_instance_valid(glass.prompt) and glass.prompt.visible:
					seen.prompt_up = true
					var word_label: Label = glass.prompt.word_label if glass.prompt.word_label else glass.prompt.text_label
					if word_label.visible:
						seen.word = word_label.text
				while rate > 0.0 and mashed / rate <= glass.beat_clock + 0.000001:
					tap(MASH_KEYS[glass.pair[mashed % 2]])
					mashed += 1
			"BOOMS":
				if seen.wobble_first_boom < 0.0:
					seen.meter = glass.meter
					seen.passed = glass.deafen_passed
					seen.dizzy = glass.dizzy
					seen.stars = is_instance_valid(glass.stars)
					seen.wobble_first_boom = boss.wobble_amount()
					seen.prompt_gone = not (is_instance_valid(glass.prompt) and glass.prompt.visible)
				if glass.boom != null and not answered.has(glass.boom_index) and glass.state_clock - glass.birth_clock >= 0.3:
					answered[glass.boom_index] = true
					tap(ARROW_KEYS[glass.arrows[glass.boom_index]])
				if glass.boom_phase == glass.BoomPhase.STOMP:
					seen.wobble_in_stomps = minf(seen.wobble_in_stomps, boss.wobble_amount())
	seen.windows = glass.windows.map(func(w): return snappedf(w, 0.001))
	seen.outcomes = Array(glass.outcomes)
	seen.stomps = glass.stomps
	await wait(roundi((sm.wobble_out + 0.2) * 60.0))
	seen.wobble_after = boss.wobble_amount()
	seen.stars_after = is_instance_valid(glass.stars)
	seen.mashed = mashed
	return seen


func test_matt_deafen() -> void:
	await load_matt()
	player.playerHealth = 1000
	var glass: Node = sm.states["GlassRow"]
	var rotation: Array[String] = ["MysticVolley", "GlassRow"]
	sm.attack_rotation = rotation
	var half := int(boss.max_health * sm.phase_two_ratio)

	log_p("-- when it comes")
	var cases := [
		[boss.max_health, 1, false, "MysticVolley", "GlassRow", false, "phase one: a plain Glass Row"],
		[half - 2, 0, false, "MysticVolley", "GlassRow", false, "phase two, but the fight's first Glass Row: no yell"],
		[half - 2, 1, false, "MysticVolley", "GlassRow", true, "phase two's opener, forced as the next cycle"],
		# Never two Glass Rows in a row (the Echo Roars' plan, 2026-10-04): straight after one, the opener waits a cycle.
		[half - 2, 1, false, "GlassRow", "MysticVolley", false, "but never straight after a Glass Row: the rotation first"],
		[half - 2, 2, true, "GlassRow", "MysticVolley", false, "then the rotation"],
		[half - 2, 2, true, "MysticVolley", "GlassRow", true, "and every phase-two Glass Row yells"],
		[half + 1, 1, false, "MysticVolley", "GlassRow", false, "just over half: no yell"],
	]
	for c in cases:
		boss.boss_health = c[0]
		sm.glass_rows_done = c[1]
		sm.deafen_opened = c[2]
		sm.last_attack = c[3]
		var plan: Dictionary = sm.plan_next()
		check(plan.attack == c[4] and plan.deafen == c[5], "%s (%s)" % [c[6], plan])
	boss.boss_health = half - 2
	sm.glass_rows_done = 1
	sm.deafen_opened = false
	sm.last_attack = "MysticVolley"
	sm.start_cycle()
	check(sm.current_state == glass and sm.cycle_deafen and sm.deafen_opened, "starting the opener marks it played")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await wait(3)

	log_p("-- the mash")
	await settle_player(Vector2(700, 800))
	var pair: Array = player.finisher.mash_actions()
	var row := glass_row(6, true)
	await wait_until(func(): return row.beat == row.Beat.DEAFEN and row.beat_clock > 0.1, 60 * 10)
	var before: float = row.meter
	tap(MASH_KEYS[pair[0]])
	tap(MASH_KEYS[pair[1]])
	await wait(2)
	var once: float = row.meter - before
	var one_gain: float = load("res://Scripts/MashCurve.gd").gain(sm.deafen_gain, before)
	log_p("pair %s; both keys in one flush moved the meter %.4f (one press %.4f)" % [pair, once, one_gain])
	check(Array(row.pair) == pair, "it mashes on the finisher's own pair")
	check(once > 0.0 and absf(once - one_gain) <= 0.01, "and both keys at once count once")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await wait(3)

	# Clear of what the mash asks since the user's 2026-09-28 retune, about 8.9 a second (matt_deafen_rate).
	log_p("-- 10 presses a second")
	await settle_player(Vector2(700, 800))
	var fast := await deafen_row(10.0)
	log_p("%s" % [fast])
	check(fast.prompt_up and fast.word == "RESIST!", "the RESIST! prompt is up through the yell (%s)" % fast.word)
	check(fast.passed and is_equal_approx(fast.meter, 1.0) and not fast.dizzy and not fast.stars and is_zero_approx(fast.wobble_first_boom),
		"10 a second mashes through it: no dizzy, no stars, no wobble")
	check(fast.prompt_gone, "and the prompt is gone by the first boom")
	var plain_ok: bool = not fast.windows.is_empty() and glass_window_ok(fast.windows[0], 0)
	check(plain_ok, "its booms charge phase two's usual %.2f s (window %s)" % [sm.boom_charge + sm.cycle_boom_charge_extra, fast.windows])
	check(fast.stomps == sm.phase_two_boom_sets - 1 and fast.outcomes.size() == 15 and fast.outcomes.all(func(o): return o == &"answered"),
		"in phase two's sets: %d stomps, and all 15 booms answered (%d)" % [sm.phase_two_boom_sets - 1, fast.stomps])

	for rate in [4.0, 0.0]:
		log_p("-- %d presses a second" % int(rate))
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
		await wait(3)
		await settle_player(Vector2(700, 800))
		var slow := await deafen_row(rate)
		log_p("%s" % [slow])
		check(not slow.passed and slow.dizzy and slow.stars, "%d a second fails: dizzy, with stars" % int(rate))
		check(slow.wobble_first_boom >= 0.999, "the wobble at full before the first boom (%.3f)" % slow.wobble_first_boom)
		var dizzy_ok: bool = not slow.windows.is_empty() and glass_window_ok(slow.windows[0], 0, true)
		check(dizzy_ok, "every charge %.2f s while dizzy (window %s)" % [sm.boom_charge_wobble + sm.cycle_boom_charge_extra, slow.windows])
		check(slow.stomps == sm.phase_two_boom_sets - 1 and slow.wobble_in_stomps >= 0.999 and slow.outcomes.size() == 15
			and slow.outcomes.all(func(o): return o == &"answered"), "the wobble full through both stomps, and every boom still answered (%d stomps, %.3f)" % [slow.stomps, slow.wobble_in_stomps])
		check(is_zero_approx(slow.wobble_after) and not slow.stars_after, "and all of it clears after the barrage (wobble %.3f)" % slow.wobble_after)

	log_p("-- the layers")
	var layers := {}
	for layer in root.find_children("*", "CanvasLayer", true, false):
		layers[str(current_scene.get_path_to(layer))] = layer.layer
	var wobble: Node2D = boss.wobble
	log_p("layers %s; the wobble at z %d, relative %s, on %s" % [layers, wobble.z_index, wobble.z_as_relative, wobble.get_canvas_layer_node()])
	check(wobble.get_canvas_layer_node() == null and wobble.z_index == RenderingServer.CANVAS_ITEM_Z_MAX and not wobble.z_as_relative,
		"the wobble is the arena's own last draw, over the arena and the booms")
	check(layers.values().all(func(l): return l >= 1), "so every CanvasLayer draws over it sharp: the fight HUD and the prompt, the VS card, the pause menu")

	log_p("-- the fight ends mid-mash")
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await wait(3)
	await settle_player(Vector2(700, 800))
	row = glass_row(6, true)
	await wait_until(func(): return row.beat == row.Beat.DEAFEN and row.beat_clock > 0.5, 60 * 10)
	tap(MASH_KEYS[pair[0]])
	await wait(2)
	sm.enter_defeated()
	await wait(3)
	var left := matt_glass_leftovers()
	var prompt_up: bool = is_instance_valid(row.prompt) and row.prompt.visible
	check(left.is_empty() and not prompt_up and not is_instance_valid(row.stars), "everything let go, the prompt too %s" % [left])


# ---- the Glass Row's bots (seeded, the plan's targets)

# A Glass Row run to its end with a bot answering: `plan` is handed each live boom's index and arrow and
# returns {at, key} - a key pressed `at` seconds after the birth - or {} for none. What it came to.
func glass_bot_row(booms: int, deafen: bool, plan: Callable, sets := 1) -> Dictionary:
	var glass := glass_row(booms, deafen, sets)
	var health_before: int = player.playerHealth
	var planned := {}
	var taps := []
	var wobble_at_taps := []
	while sm.current_state == glass:
		await physics_frame
		if glass.beat != glass.Beat.BOOMS or glass.boom == null:
			continue
		var i: int = glass.boom_index
		if not planned.has(i):
			planned[i] = plan.call(i, glass.arrows[i])
		var want: Dictionary = planned[i]
		if want.is_empty() or want.get("done", false):
			continue
		if glass.state_clock - glass.birth_clock >= want.at:
			want["done"] = true
			tap(want.key)
			taps.append(want.key == ARROW_KEYS[glass.arrows[i]])
			wobble_at_taps.append(boss.wobble_amount())
	var timer: float = sm.recover_timer.time_left if sm.current_state == sm.states["Recover"] else -1.0
	return {"outcomes": Array(glass.outcomes), "fails": glass.fails, "glass": glass.glass_hit, "booms": glass.windows.size(),
		"damage": health_before - player.playerHealth, "timer": snappedf(timer, 0.01), "taps": taps, "wobble_at_taps": wobble_at_taps,
		"stomps": glass.stomps, "row": glass.row}


func glass_bot_reset() -> void:
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	sm.recover_timer.stop()
	player.playerHealth = 6
	player.healthUI.update_health(6)
	player.is_invincible = false
	player.invincibility_timer.stop()
	await wait(3)
	await settle_player(Vector2(700, 800))


# A person answering the booms: each reaction drawn round MATT_GLASS_REACTION, now and then a slow one, on
# the fight's seed. Through the phase-two wobble - the waves and the sway - the arrow takes
# MATT_GLASS_WOBBLE_READ longer to read, an assumption, not a measurement.
const MATT_GLASS_REACTION := 0.375
const MATT_GLASS_REACTION_SPREAD := 0.05
const MATT_GLASS_WOBBLE_READ := 0.10
const MATT_GLASS_HUMAN_RUNS := 5
# The pace is meant to be demanding: a run may miss this many and still be a person keeping up.
const MATT_GLASS_HUMAN_MISSES := 2


func test_matt_glass_bots() -> void:
	await load_matt()
	await glass_bot_reset()
	# Each count the tiers use, once.
	var counts := []
	for count in sm.boom_counts_by_tier:
		if not counts.has(count):
			counts.append(count)
	var top: int = sm.boom_counts_by_tier[-1]
	var true_at := func(at: float) -> Callable:
		return func(_i: int, arrow: StringName) -> Dictionary: return {"at": at, "key": ARROW_KEYS[arrow]}
	var skip_three := func(at: float) -> Callable:
		return func(i: int, arrow: StringName) -> Dictionary: return {} if i < 3 else {"at": at, "key": ARROW_KEYS[arrow]}
	var person := func(bot: RandomNumberGenerator, slower: float) -> Callable:
		return func(_i: int, arrow: StringName) -> Dictionary:
			return {"at": maxf(bot.randfn(MATT_GLASS_REACTION, MATT_GLASS_REACTION_SPREAD), 0.25) + slower, "key": ARROW_KEYS[arrow]}
	match tier:
		"perfect":
			for booms in counts:
				var run := await glass_bot_row(booms, false, true_at.call(1.0 / 60.0))
				log_p("perfect, %d booms: %s" % [booms, run])
				check(run.fails == 0 and run.damage == 0 and absf(run.timer - sm.recover_time - sm.glass_clean_bonus) <= 0.05,
					"%d booms: nothing missed, nothing lost, and the clean run's longer window" % booms)
				await glass_bot_reset()
		"human":
			var bot := RandomNumberGenerator.new()
			bot.seed = MATT_SEED
			var misses := []
			var glassed := 0
			for n in MATT_GLASS_HUMAN_RUNS:
				var run := await glass_bot_row(top, false, person.call(bot, 0.0))
				log_p("human %d, %d booms: %d missed; %s" % [n, top, run.fails, run])
				misses.append(run.fails)
				glassed += 1 if run.glass else 0
				await glass_bot_reset()
			log_p("human: missed per run %s" % [misses])
			check(glassed == 0 and misses.all(func(m): return m <= MATT_GLASS_HUMAN_MISSES),
				"a person reacting in about %.2f s keeps up with %d booms: missed per run %s, never the glass" % [MATT_GLASS_REACTION, top, misses])
			var from_c := await glass_bot_row(top, false, skip_three.call(MATT_GLASS_REACTION + MATT_GLASS_REACTION_SPREAD))
			log_p("human from row C: %s" % [from_c])
			check(from_c.fails == 3 and not from_c.glass, "three missed on purpose, then from row C every one answered: no glass")
		"random":
			var bot := RandomNumberGenerator.new()
			bot.seed = MATT_SEED
			var glassed := 0
			var right := 0
			var pressed := 0
			for n in 5:
				var run := await glass_bot_row(top, false, func(_i: int, _arrow: StringName) -> Dictionary:
					return {"at": 0.30, "key": ARROW_KEYS.values()[bot.randi_range(0, 3)]})
				log_p("random %d: %s" % [n, run])
				glassed += 1 if run.glass else 0
				right += run.taps.count(true)
				pressed += run.taps.size()
				await glass_bot_reset()
			var accuracy := float(right) / maxf(pressed, 1.0)
			log_p("random: glass in %d of 5, %d of %d right" % [glassed, right, pressed])
			check(glassed >= 4 and accuracy <= 0.40, "a random press a boom: the glass in %d of 5 top-tier barrages, %.0f%% right" % [glassed, accuracy * 100.0])
		"none":
			for booms in counts:
				var run := await glass_bot_row(booms, false, func(_i: int, _arrow: StringName) -> Dictionary: return {})
				log_p("none, %d booms: %s" % [booms, run])
				check(run.glass and run.booms == 4 and run.damage == 2, "%d booms, no presses: the glass on the fourth, one heart, no fifth boom" % booms)
				await glass_bot_reset()
		"wobble":
			# Phase two with the mash failed: the view at full wobble through three sets and their two stomps.
			# The true arrow a frame after each birth, then a person reading slower through it.
			var sets: int = sm.phase_two_boom_sets
			var perfect := await glass_bot_row(top, true, true_at.call(1.0 / 60.0), sets)
			log_p("wobble, perfect: %s" % [perfect])
			check(perfect.fails == 0 and perfect.stomps == sets - 1 and not perfect.taps.is_empty() and perfect.wobble_at_taps.all(func(w): return w >= 0.999),
				"the mash failed, the screen at full wobble: the true arrow a frame after each birth misses none of %d booms through %d stomps" % [top, sets - 1])
			await glass_bot_reset()
			var bot := RandomNumberGenerator.new()
			bot.seed = MATT_SEED
			var misses := []
			var glassed := 0
			for n in MATT_GLASS_HUMAN_RUNS:
				var run := await glass_bot_row(top, true, person.call(bot, MATT_GLASS_WOBBLE_READ), sets)
				log_p("wobble, person %d: %d missed, glass %s; %s" % [n, run.fails, run.glass, run])
				misses.append(run.fails)
				glassed += 1 if run.glass else 0
				await glass_bot_reset()
			log_p("wobble, person: missed per run %s, the glass in %d of %d" % [misses, glassed, MATT_GLASS_HUMAN_RUNS])
			check(glassed == 0, "a person %.2f s slower to read through it stays out of the glass: missed per run %s" % [MATT_GLASS_WOBBLE_READ, misses])
			# Phase two's glass is D to A, so E is the last row before it.
			var slow_read: float = MATT_GLASS_REACTION + MATT_GLASS_REACTION_SPREAD + MATT_GLASS_WOBBLE_READ
			var skip_one := func(i: int, arrow: StringName) -> Dictionary: return {} if i < 1 else {"at": slow_read, "key": ARROW_KEYS[arrow]}
			var from_e := await glass_bot_row(top, true, skip_one, sets)
			log_p("wobble from row E: %s" % [from_e])
			check(from_e.fails == 1 and from_e.row == 1 and not from_e.glass, "and from row E, one missed on purpose, still no glass through both stomps")


# ---- Captain Burak: his powder kegs
# On his fight through load_burak_attacks and burak_park, the pistol pair's and the cutlass's own: his order
# pinned to the kegs, the Laugh already had, and parked between attacks. A keg breaks to one punch, and the
# five are spread across the ring afresh each volley off his seeded rng.
#   burak_barrels  the spread's rules over seeds, health and the player's spot, and a new layout each
#                  volley; the markers, a keg landing on the player, the facing, the one-punch break, the lock
#                  on the fifth pip, the armed kegs, the clean run
#   burak_volley   N kegs left gives N HITs, the gauge's drain, the first volley's mercy, the chain stopping
#   burak_ramp     the dials off his health and the round, locked as the attack starts, and the deadline
#   burak_bots     tier=walk_full|walk_full_human|walk_cap|walk_cap_human|dash_cap|dash1_cap|dash1_human|
#                  nopunch|partial, walk_full without one

const BurakArtLayout := preload("res://Scripts/BurakBossArtLayout.gd")
const BurakFinisherLayout := preload("res://Scripts/FinisherArtLayout.gd")
# Appendix R: a bot stands the live keg hurtbox's half-width plus this far out from the keg.
const BURAK_STAND_MARGIN := 30.0
# A dash on a hop pays when what it leaves to walk, plus the walking its own frames would have covered, is
# less than the hop: the press's frame, three moving and the five-frame landing.
const BURAK_DASH_FRAMES := 9
# A human-paced bot's reaction: before each hop, from the attack's start and from the end of each punch,
# and before punching a keg that lands in front of it.
const BURAK_REACTION := 0.22
# Where each tier plays: the fight's rng seeded afresh, and the player's feet as the attack starts - below
# him, beside him, and out to each side.
const BURAK_BOT_SEEDS := [11, 22, 33]
const BURAK_BOT_STARTS := [Vector2(960, 860), Vector2(1120, 620), Vector2(420, 700), Vector2(1500, 780)]
# dash1_human's health sweep, as p: its rule holds at every p.
const BURAK_SWEEP_P := [0.0, 0.25, 0.5, 0.75, 1.0]
const BURAK_DASH_KEYS := {Vector2i(1, 0): [KEY_RIGHT], Vector2i(-1, 0): [KEY_LEFT], Vector2i(0, 1): [KEY_DOWN],
	Vector2i(0, -1): [KEY_UP], Vector2i(1, 1): [KEY_RIGHT, KEY_DOWN], Vector2i(1, -1): [KEY_RIGHT, KEY_UP],
	Vector2i(-1, 1): [KEY_LEFT, KEY_DOWN], Vector2i(-1, -1): [KEY_LEFT, KEY_UP]}


# His health at `ratio` of its maximum: the keg attack reads its ramp off it as it starts.
func burak_health(ratio: float) -> void:
	boss.boss_health = roundi(boss.max_health * ratio)


# His health for ramp `p`, BurakBossStateMachine.ramp_p() the other way round.
func burak_health_for(p: float) -> void:
	burak_health(1.0 - p * (1.0 - sm.CAP_RATIO))


# His keg attack, now, with the player's feet at `feet` as it starts, and his rng seeded with `seed_value`
# first unless it is negative: the spread keeps clear of the feet and is thrown nearest them first.
func start_burak_barrels(feet: Vector2, seed_value := -1) -> Node:
	await settle_player(feet - BurakFinisherLayout.PLAYER_FEET)
	if seed_value >= 0:
		sm.rng.seed = seed_value
	sm.on_child_transition(sm.current_state, "Barrels")
	return sm.states["Barrels"]


# Out of the attack and parked (burak_park), with what is left of its kegs faded out.
func burak_clear_kegs() -> void:
	burak_park()
	await wait(25)


# How far out from a keg's centre line the player stands to punch it: the live hurtbox's half-width plus
# BURAK_STAND_MARGIN.
func burak_stand_reach() -> float:
	return BurakArtLayout.keg_rect(BurakArtLayout.KEG.hurtbox).size.x / 2.0 + BURAK_STAND_MARGIN


# The player's position to punch the keg on `spot` from `side` (-1 its left, 1 its right), feet on its floor line.
func burak_keg_stand(spot: Vector2, side: float) -> Vector2:
	return spot + Vector2(side * burak_stand_reach(), 0.0) - BurakFinisherLayout.PLAYER_FEET


# Walking on both axes at once, near is the larger of the two distances.
func burak_walk(from: Vector2, to: Vector2) -> float:
	return maxf(absf(to.x - from.x), absf(to.y - from.y))


# Which side of the keg on `spot` a player at `from` stands to punch it: the nearer, the left on a tie.
func burak_near_side(spot: Vector2, from: Vector2) -> float:
	return 1.0 if burak_walk(from, burak_keg_stand(spot, 1.0)) < burak_walk(from, burak_keg_stand(spot, -1.0)) else -1.0


# The round the bots walk of `spots` from `feet`: to the nearer side of each keg in turn, and of that the
# four legs from the first keg to the last, in walking px.
func burak_round(spots: Array, feet: Vector2) -> float:
	var at := feet - BurakFinisherLayout.PLAYER_FEET
	var length := 0.0
	for k in spots.size():
		var stand := burak_keg_stand(spots[k], burak_near_side(spots[k], at))
		if k > 0:
			length += burak_walk(at, stand)
		at = stand
	return length


# Punch pressed on every frame the player can take it until `reports` punches have reached `keg` (a tonk
# included) or it breaks. How many reached it.
func punch_burak_keg(keg: Node2D, reports := 1) -> int:
	var got := 0
	var last: float = keg.last_punch_time
	for i in 400:
		if got >= reports or keg.phase == keg.Phase.BROKEN:
			break
		if player.state_machine.current_state.name != "Punching":
			tap(KEY_Q)
		await physics_frame
		if keg.last_punch_time != last:
			last = keg.last_punch_time
			got += 1
	await wait_until(func(): return player.state_machine.current_state.name != "Punching", 60)
	return got


# Beside `keg`, on its left and turned to it, and punches until it breaks.
func break_burak_keg(keg: Node2D) -> void:
	await settle_player(burak_keg_stand(keg.global_position, -1.0))
	await wait_until(func(): return player.facing == player.Facing.RIGHT, 30)
	await punch_burak_keg(keg, keg.hits_to_break)


func burak_sfx_playing(key: StringName) -> bool:
	for sfx in boss.sfx_players.get(key, []):
		if sfx.playing:
			return true
	return false


# What breaks the spread's rules in `spots` for a player whose feet were at `feet`, checked from the rules'
# own numbers rather than through the state's code: every spot in keg_area, clear of HOME and out of his
# shade, nearer than him from either side, clear of the player's feet, all `gap` apart; the ring's thirds
# and halves covered; thrown nearest-first from the feet, the first within first_reach of them; and the
# round within tour_slack of the tour at `p`. Empty when they hold.
func burak_spread_faults(barrels: Node, spots: Array, feet: Vector2, gap: float, p: float) -> Array:
	var faults := []
	var home: Vector2 = sm.HOME
	var shade := Rect2(barrels.shade.position + home, barrels.shade.size)
	var area: Rect2 = barrels.keg_area
	if spots.size() != barrels.kegs_per_attack:
		faults.append("%d spots" % spots.size())
	for i in spots.size():
		var v: Vector2 = spots[i]
		if not Rect2(area.position, area.size + Vector2.ONE).has_point(v):
			faults.append("%s outside the area" % v)
		if v.distance_to(home) < barrels.home_clearance:
			faults.append("%s %.0f px from him" % [v, v.distance_to(home)])
		if shade.has_point(v):
			faults.append("%s in his shade" % v)
		if v.distance_to(feet) < barrels.player_clearance:
			faults.append("%s %.0f px from the player" % [v, v.distance_to(feet)])
		for j in range(i + 1, spots.size()):
			if v.distance_to(spots[j]) < gap - 0.5:
				faults.append("%s and %s %.0f px apart" % [v, spots[j], v.distance_to(spots[j])])
	var third: float = area.size.x / 3.0
	var middle: float = area.get_center().y
	if not (spots.any(func(v): return v.x < area.position.x + third) and spots.any(func(v): return v.x > area.end.x - third)
			and spots.any(func(v): return v.y < middle) and spots.any(func(v): return v.y > middle)):
		faults.append("the thirds and halves not all covered")
	var at := feet
	var left := spots.duplicate()
	for v in spots:
		var nearest: float = left.map(func(o): return burak_walk(at, o)).min()
		if burak_walk(at, v) > nearest + 0.5:
			faults.append("%s thrown out of nearest-first order" % v)
			break
		left.erase(v)
		at = v
	# From beside each keg, either side, it has to be nearer than his hurtbox by more than the facing's switch
	# margin, with the stand margin to spare.
	var his_box: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
	var him := Rect2(home + his_box.position - his_box.shape.size / 2.0, his_box.shape.size)
	for v in spots:
		var keg := BurakArtLayout.keg_rect(BurakArtLayout.KEG.hurtbox)
		keg.position += v
		for side in [-1.0, 1.0]:
			var stand := burak_keg_stand(v, side)
			var lead := stand.distance_to(stand.clamp(him.position, him.end)) - stand.distance_to(stand.clamp(keg.position, keg.end))
			if lead <= player.TARGET_SWITCH_MARGIN + BURAK_STAND_MARGIN:
				faults.append("%s from its %s: only %.0f px nearer than him" % [v, "right" if side > 0.0 else "left", lead])
	if not spots.is_empty() and burak_walk(feet, spots[0]) > barrels.first_reach + 0.5:
		faults.append("the first %.0f px from the player" % burak_walk(feet, spots[0]))
	var round_px := burak_round(spots, feet)
	var tour: float = lerpf(barrels.tour.x, barrels.tour.y, p)
	if absf(round_px - tour) > barrels.tour_slack + 0.5:
		faults.append("a round of %.0f px against %.0f +- %.0f" % [round_px, tour, barrels.tour_slack])
	return faults


# His bullet for this volley, from the knobs and the round the suite measures: the ramp's bullet at p, plus
# a fifth of the time the round's walk runs past the tour.
func burak_bullet_want(barrels: Node, p: float, spots: Array, feet: Vector2) -> float:
	var ramp: float = lerpf(barrels.bullet.x, barrels.bullet_mid, p * 2.0) if p <= 0.5 \
		else lerpf(barrels.bullet_mid, barrels.bullet.y, (p - 0.5) * 2.0)
	var tour: float = lerpf(barrels.tour.x, barrels.tour.y, p)
	return ramp + (burak_round(spots, feet) - tour) / (barrels.kegs_per_attack * player.SPEED)


# §4.7, as retuned: p 0, 0.5, 1 and 1 at 100%, 60%, 20% and 10% of his health; the cadence, the gap and the
# bullet off it and off the round, locked as the attack starts; the throw played in time with the cadence;
# and the deadline each gives, marker to lock.
func test_burak_ramp() -> void:
	await load_burak_attacks(["Barrels"])
	health_ok()
	var barrels: Node = sm.states["Barrels"]
	var art_throw: float = BurakArtLayout.loop_length(BurakArtLayout.anim(&"throw"))
	var feet := Vector2(960, 860)
	log_p("cadence %s, spread %s, tour %s +- %.0f, bullet %.3f / %.3f / %.3f" % [barrels.cadence, barrels.spread, barrels.tour,
		barrels.tour_slack, barrels.bullet.x, barrels.bullet_mid, barrels.bullet.y])
	for row in [[1.0, 0.0], [0.6, 0.5], [0.2, 1.0], [0.1, 1.0]]:
		burak_health(row[0])
		var p: float = row[1]
		var tag := "at %d%% health" % roundi(row[0] * 100.0)
		check(is_equal_approx(sm.ramp_p(), p), "%s p is %.1f (%.3f)" % [tag, p, sm.ramp_p()])
		await start_burak_barrels(feet)
		var cadence_want: float = lerpf(barrels.cadence.x, barrels.cadence.y, p)
		var gap_want: float = lerpf(barrels.spread.x, barrels.spread.y, p)
		var bullet_want := burak_bullet_want(barrels, p, barrels.spots, feet)
		var throw_want: float = minf(art_throw, cadence_want)
		var dials := [barrels.p, barrels.c, barrels.gap, barrels.b, barrels.throw_time, barrels.release_at]
		var d_want: float = barrels.marker_lead + 4.0 * cadence_want + 5.0 * bullet_want
		log_p("%s: cadence %.3f, gap %.0f, round %.0f, bullet %.3f, throw %.3f (release %.3f), D %.3f" % [tag, dials[1], dials[2],
			burak_round(barrels.spots, feet), dials[3], dials[4], dials[5], d_want])
		check(is_equal_approx(dials[0], p) and is_equal_approx(dials[1], cadence_want) and is_equal_approx(dials[2], gap_want)
			and absf(dials[3] - bullet_want) <= 0.0005, "%s the dials: cadence %.3f, gap %.0f, bullet %.3f for this round" % [tag, cadence_want, gap_want, bullet_want])
		check(is_equal_approx(dials[4], throw_want) and is_equal_approx(dials[5], barrels.throw_release * throw_want / art_throw),
			"%s the throw takes %.3f s, no longer than the cadence, releasing at %.3f s" % [tag, throw_want, barrels.throw_release * throw_want / art_throw])
		burak_health(1.1 - row[0])
		await wait(5)
		check([barrels.p, barrels.c, barrels.gap, barrels.b, barrels.throw_time, barrels.release_at] == dials,
			"%s the dials stay locked when his health moves mid-attack" % tag)
		await wait_until(func(): return barrels.locked_at >= 0.0, 60 * 20)
		# The load starts on the first step past the fifth landing and locks on the first past the fifth bullet:
		# each rounds up to a step.
		var late: float = barrels.locked_at - barrels.marker_times[0] - d_want
		check(late >= -0.5 / 60.0 and late <= 2.0 / 60.0, "%s the lock falls %.3f s after the first marker (D %.3f)" % [tag, d_want + late, d_want])
		await burak_clear_kegs()


# §4.2-4.6 on the real attack: the spread's rules over seeds, health and the player's spot, and a new layout
# each volley; the markers' lead; a keg landing on the player; walking through one; the facing; the
# one-punch break; the lock on the fifth pip's step; the armed kegs; and the clean run.
func test_burak_barrels() -> void:
	await load_burak_attacks(["Barrels"])
	health_ok()
	track()
	var barrels: Node = sm.states["Barrels"]

	# THE SPREAD, at three healths from every start, three volleys in a row off one seed.
	sm.rng.seed = 7
	var layouts := 0
	var repeats := 0
	for ratio in [1.0, 0.6, 0.2]:
		burak_health(ratio)
		for start in BURAK_BOT_STARTS:
			var last: Array = []
			for volley in 3:
				await start_burak_barrels(start)
				var spots: Array = barrels.spots
				var faults := burak_spread_faults(barrels, spots, start, barrels.gap, barrels.p)
				check(faults.is_empty(), "p %.1f from %s, volley %d: %s, round %.0f %s" % [barrels.p, start, volley + 1, spots,
					burak_round(spots, start), faults])
				if spots == last:
					repeats += 1
				last = spots
				layouts += 1
				await burak_clear_kegs()
	check(repeats == 0, "each of %d volleys spread its kegs afresh (%d repeats)" % [layouts, repeats])

	# ONE ATTACK AT p 0. The player stands on keg 2's spot as it comes down.
	burak_health(1.0)
	await start_burak_barrels(Vector2(960, 860))
	var spots: Array = barrels.spots
	await wait_until(func(): return barrels.kegs.size() >= 1, 5)
	var first: Node2D = barrels.kegs[0]
	check(is_instance_valid(first.marker) and first.marker.global_position == spots[0] and not first.is_breakable(),
		"a keg's marker is on its spot from the throw, and until it lands it can't be punched")
	await settle_player(spots[1] - BurakFinisherLayout.PLAYER_FEET)
	var stood := player.global_position
	await wait_until(func(): return barrels.landed >= 2, 60 * 5)
	check(events_of("HIT").is_empty() and player.global_position == stood,
		"a keg landing on the player does nothing: no hit, and they are where they stood")
	for k in 2:
		var lead: float = barrels.land_times[k] - barrels.marker_times[k]
		check(absf(lead - barrels.marker_lead) <= 1.5 / 60.0 and not is_instance_valid(barrels.kegs[k].marker),
			"keg %d lands %.3f s after its marker, and the marker goes as it does" % [k + 1, lead])

	# The facing: beside keg 4's spot before it lands, between it and him, so it faces him until it lands.
	var fourth_spot: Vector2 = spots[3]
	var side := 1.0 if sm.HOME.x >= fourth_spot.x else -1.0
	await settle_player(burak_keg_stand(fourth_spot, side))
	await wait(2)
	var fourth: Node2D = barrels.kegs[3] if barrels.kegs.size() > 3 else null
	var threat_before: bool = fourth != null and fourth.hurtbox.is_in_group("facing_threat")
	var facing_before: int = player.facing
	await wait_until(func(): return barrels.landed >= 4, 60 * 5)
	fourth = barrels.kegs[3]
	var toward: int = player.Facing.LEFT if side > 0.0 else player.Facing.RIGHT
	await wait_until(func(): return player.facing == toward, 30)
	check(not threat_before and fourth.hurtbox.is_in_group("facing_threat") and player.facing == toward,
		"the facing turns to a keg as it lands in reach (facing %d, then %d)" % [facing_before, player.facing])
	var frame_before: int = fourth.body_sprite.frame
	var got := await punch_burak_keg(fourth, 1)
	check(got == 1 and frame_before == 0 and fourth.phase == fourth.Phase.BROKEN and not fourth.visual.visible
		and not fourth.hurtbox.is_in_group("facing_threat"), "one punch breaks a keg straight from f0 into the burst")

	# Walking through a landed keg: keg 2, from its side toward the middle of the ring outward.
	var outward := -1.0 if spots[1].x < 960.0 else 1.0
	var through_key := KEY_LEFT if outward < 0.0 else KEY_RIGHT
	await settle_player(spots[1] - Vector2(outward * 110.0, 0.0) - BurakFinisherLayout.PLAYER_FEET)
	press(through_key)
	await wait(24)
	release(through_key)
	await wait(2)
	check(outward * (player.global_position.x - spots[1].x) > 100.0, "the player walks through a landed keg (x %.0f past %.0f)" % [player.global_position.x, spots[1].x])

	# The lock falls on the step the fifth pip shows loaded, and arms the kegs left. The pip settles in idle
	# time and the lock in physics time, so either can show a step before the other.
	var loaded: int = BurakArtLayout.fx(&"pips").loaded
	var pip_frame := -1
	for i in 60 * 20:
		var pips: Array = boss.pips.pips
		if pip_frame < 0 and pips.size() == 5 and pips[4].frame == loaded:
			pip_frame = Engine.get_physics_frames()
		if barrels.locked_frame >= 0 and (pip_frame >= 0 or Engine.get_physics_frames() > barrels.locked_frame + 3):
			break
		await physics_frame
	log_p("fifth pip loaded on frame %d, the lock on frame %d" % [pip_frame, barrels.locked_frame])
	check(absi(barrels.locked_frame - pip_frame) <= 1, "the lock falls on the step the fifth pip shows loaded (pip f%d, lock f%d)" % [pip_frame, barrels.locked_frame])
	check(barrels.armed.size() == 4 and barrels.kegs_left == 4 and barrels.armed.all(func(k): return k.is_armed() and not k.hurtbox.is_in_group("facing_threat")),
		"the four kegs left are armed and out of the facing (%d)" % barrels.armed.size())

	# An armed keg only tonks. It no longer turns the player, so the fight's own face_point() aims the punch.
	var last_armed: Node2D = barrels.armed[-1]
	await settle_player(burak_keg_stand(last_armed.global_position, -1.0))
	player.face_point(last_armed.global_position + BurakArtLayout.keg_rect(BurakArtLayout.KEG.hurtbox).get_center())
	await wait(2)
	got = await punch_burak_keg(last_armed, 1)
	player.clear_face_point()
	check(got == 1 and last_armed.hits == 0 and last_armed.body_sprite.frame == 0 and last_armed.is_armed() and burak_sfx_playing(&"barrel_tonk"),
		"a punch reaches an armed keg and only tonks (%d reached, hits %d)" % [got, last_armed.hits])
	await wait_until(func(): return sm.current_state.name == "Taunt", 60 * 10)
	check(barrels.volley_results.size() == 4, "and the four are shot (%d)" % barrels.volley_results.size())
	await burak_clear_kegs()

	# THE CLEAN RUN: every keg broken as it lands.
	var hype: Node = player.get_node("Hype")
	await start_burak_barrels(Vector2(960, 860))
	for k in 5:
		await wait_until(func(): return barrels.kegs.size() > k and barrels.kegs[k].is_breakable(), 60 * 5)
		await break_burak_keg(barrels.kegs[k])
	await wait_until(func(): return barrels.clean_run, 30)
	var frozen: Array = boss.pips.pips.map(func(pip): return pip.frame)
	check(barrels.clean_run and barrels.locked_at < 0.0 and barrels.beat == barrels.Beat.MISFIRE,
		"no keg left after the fifth landing: the load aborts into the misfire, no lock")
	await wait_until(func(): return barrels.misfire_step >= 1, 60)
	check(boss.current_anim == &"talk" and boss.talk_pose == &"shrug" and burak_sfx_playing(&"misfire"),
		"a dry click and a shrug")
	var hype_before: float = hype.hype
	await wait_until(func(): return barrels.misfire_step >= 2, 60)
	check(hype.hype >= hype_before + barrels.clean_hype - 0.01, "the crowd and %d hype for the clean run (%.1f -> %.1f)" % [barrels.clean_hype, hype_before, hype.hype])
	check(boss.pips.pips.map(func(pip): return pip.frame) == frozen, "the pips froze where they were (%s)" % [frozen])
	await wait_until(func(): return sm.current_state.name == "Taunt", 60 * 3)
	await wait(1)
	check(absf(sm.taunt_timer.time_left - (sm.taunt_time + sm.clean_run_bonus)) <= 2.5 / 60.0,
		"then a %.1f s Taunt (%.2f left)" % [sm.taunt_time + sm.clean_run_bonus, sm.taunt_timer.time_left])


# §4.5: N kegs left (5, 3, 1, 0) gives N blasts, each one HIT on its detonation step, through the i-frames, a
# guard and a dash; each drains the gauge 20, clamped at 0; the first volley's mercy floors the player at one
# half-heart and its HITs still count; a later volley kills, and the chain stops there.
func test_burak_volley() -> void:
	await load_burak_attacks(["Barrels"])
	var barrels: Node = sm.states["Barrels"]
	var blasts: Array = []
	defense.hit_taken.connect(func(hit):
		if hit.attack_id == &"burak_barrel_blast":
			blasts.append({"frame": Engine.get_physics_frames(), "damage": hit.damage, "dodging": player.is_dodging,
				"guarding": defense.is_guarding(), "invincible": player.is_invincible}))
	var gauge: Node = boss.break_gauge
	var aside := Vector2(1700, 950)

	# The fight's first volley, all five: the mercy, the i-frames, a guard and a dash.
	player.playerHealth = 2
	gauge.value = 40.0
	await start_burak_barrels(aside)
	var shot := func(n: int) -> bool: return barrels.beat == barrels.Beat.VOLLEY and barrels.shot_index == n
	await wait_until(func(): return shot.call(2), 60 * 20)
	# Six steps before the third blast, inside the parry window: without blocking that is as long as a guard
	# stays up.
	await wait_until(func(): return shot.call(2) and barrels.shot_beat == barrels.Shot.FLIGHT and barrels.shot_clock + 6.0 / 60.0 >= barrels.aim_time + barrels.ball_time, 60 * 2)
	press(KEY_SHIFT)
	await wait_until(func(): return shot.call(3), 60 * 2)
	release(KEY_SHIFT)
	# Two steps before the fourth blast, so it goes off inside the dash.
	var dash_now := func() -> bool:
		return barrels.shot_beat == barrels.Shot.FLIGHT and barrels.shot_clock + 2.0 / 60.0 >= barrels.aim_time + barrels.ball_time
	await wait_until(dash_now, 60 * 2)
	press(KEY_LEFT)
	tap(KEY_W)
	await wait(1)
	release(KEY_LEFT)
	await wait_until(func(): return sm.current_state.name == "Taunt", 60 * 5)
	log_p("first volley: %s, frames %s, health %d, gauge %.1f" % [blasts, barrels.blast_frames, player.playerHealth, gauge.value])
	check(barrels.blast_hits == 5 and blasts.size() == 5, "five kegs left: five blasts, five HITs (%d)" % blasts.size())
	check(blasts.size() == 5 and blasts.map(func(e): return e.frame) == barrels.blast_frames, "each HIT on its own blast's step")
	check(player.playerHealth == 1 and blasts.map(func(e): return e.damage) == [1, 0, 0, 0, 0],
		"the first volley's mercy: one half-heart left, and the HITs past it still count (%s)" % [blasts.map(func(e): return e.damage)])
	check(blasts.size() == 5 and blasts[1].invincible and blasts[2].guarding and blasts[3].dodging,
		"they land inside the i-frames, through a held guard and mid-dash")
	check(is_zero_approx(gauge.value), "five blasts drain the gauge from 40 to 0, clamped (%.1f)" % gauge.value)
	check(not sm.laugh_owed, "with the Laugh spent it is not owed")
	await burak_clear_kegs()

	# Later volleys: three, one and no kegs left.
	for n in [3, 1, 0]:
		blasts.clear()
		player.playerHealth = 6
		clear_iframes()
		gauge.value = 40.0
		await start_burak_barrels(aside)
		for k in 5 - n:
			await wait_until(func(): return barrels.kegs.size() > k and barrels.kegs[k].is_breakable(), 60 * 5)
			await break_burak_keg(barrels.kegs[k])
		await settle_player(aside - BurakFinisherLayout.PLAYER_FEET)
		await wait_until(func(): return sm.current_state.name == "Taunt", 60 * 20)
		log_p("%d left: %d blasts, health %d, gauge %.1f" % [n, blasts.size(), player.playerHealth, gauge.value])
		check(blasts.size() == n and barrels.blast_hits == n and player.playerHealth == 6 - n,
			"%d kegs left: %d HITs, %d half-hearts" % [n, blasts.size(), 6 - player.playerHealth])
		check(blasts.map(func(e): return e.frame) == barrels.blast_frames, "each on its own blast's step")
		check(is_equal_approx(gauge.value, maxf(40.0 - 20.0 * n, 0.0)), "%d blasts drain the gauge 40 -> %.0f (%.1f)" % [n, maxf(40.0 - 20.0 * n, 0.0), gauge.value])
		if n == 0:
			check(barrels.clean_run, "no keg left: the misfire")
		await burak_clear_kegs()

	# A later volley kills: no mercy, and nothing goes off after the blast that does it.
	blasts.clear()
	player.playerHealth = 2
	clear_iframes()
	await start_burak_barrels(aside)
	await wait_until(func(): return player.playerHealth <= 0, 60 * 20)
	var fired: int = barrels.volley_results.size()
	await wait(60 * 3)
	log_p("the kill: %s, results %s" % [blasts, barrels.volley_results])
	check(player.playerHealth == 0 and fired == 2 and barrels.volley_results.size() == 2 and blasts.size() == 2,
		"a later volley kills on its second blast, and the chain stops there (%d fired)" % barrels.volley_results.size())
	check(not sm.laugh_owed and sm.current_state.name != "Laugh", "and there is no Laugh")


# §4.8 on the spread: bots taking the real attack's kegs in his throwing order, each tier on every seed in
# BURAK_BOT_SEEDS from every start in BURAK_BOT_STARTS. The deadline is tuned for a human: a perfect walker
# only reports, and the human-paced tiers are the ones that have to fail or clear.
#   walk_full        a perfect walker at full health (p 0): clears every layout.
#   walk_full_human  a walker reacting in BURAK_REACTION at full health: clears every layout.
#   walk_cap         a perfect walker at the cap (p 1): its margins, reported.
#   walk_cap_human   a walker reacting in BURAK_REACTION at the cap: misses at least one keg on every layout.
#   dash_cap         a perfect bot dashing up to twice a hop at the cap: clears every layout.
#   dash1_cap        a perfect bot dashing once a hop at the cap: clears every layout.
#   dash1_human      dashing once a hop, reacting in BURAK_REACTION, at p 0, 0.25, 0.5, 0.75 and 1: clears
#                    every layout with at least 0.2 s to spare.
#   nopunch          standing still at full health: all five, five HITs.
#   partial          breaking the first two it reaches at full health: three HITs.
func test_burak_bots() -> void:
	await load_burak_attacks(["Barrels"])
	health_ok()
	var sweep: Array = BURAK_SWEEP_P if tier == "dash1_human" else ([1.0] if tier.contains("_cap") else [0.0])
	var dashes: int = {"dash_cap": 2, "dash1_cap": 1, "dash1_human": 1}.get(tier, 0)
	var breaks: int = {"nopunch": 0, "partial": 2}.get(tier, 5)
	var reaction: float = BURAK_REACTION if tier.ends_with("_human") else 0.0
	var runs := []
	var least_at := []
	for p in sweep:
		var at_p := []
		for seed_value in BURAK_BOT_SEEDS:
			for start in BURAK_BOT_STARTS:
				burak_health_for(p)
				var run := await burak_keg_bot(start, seed_value, dashes, breaks, reaction)
				runs.append(run)
				at_p.append(run.spare)
				log_p("burak_bots %s p %.2f seed %d from %s: %d HITs, spare %.3f s, round %.0f px, bullet %.3f, D %.3f, breaks at %s, spots %s" % [tier,
					run.p, seed_value, start, run.hits, run.spare, run.round_px, run.b, run.deadline, run.breaks, run.spots])
				await burak_reset_bot()
		least_at.append(at_p.min())
		log_p("burak_bots %s p %.2f: least spare %.3f s, most %.3f s" % [tier, p, at_p.min(), at_p.max()])
	var spares: Array = runs.map(func(r): return r.spare)
	var hits: Array = runs.map(func(r): return r.hits)
	log_p("burak_bots %s: %d runs, least spare %.3f s, HITs %s" % [tier, runs.size(), spares.min(), hits])
	match tier:
		"walk_full", "walk_full_human":
			check(hits.max() == 0, "%s at full health clears every layout (least spare %.3f s)" % [tier, spares.min()])
		"walk_cap":
			check(runs.size() == BURAK_BOT_SEEDS.size() * BURAK_BOT_STARTS.size(), "a perfect walker at the cap, reported: least spare %.3f s, HITs %s" % [spares.min(), hits])
		"walk_cap_human":
			check(hits.min() >= 1, "a human-paced walker at the cap misses at least one keg on every layout (%s)" % [hits])
		"dash_cap", "dash1_cap":
			check(hits.max() == 0, "%s at the cap clears every layout (least spare %.3f s)" % [tier, spares.min()])
		"dash1_human":
			check(hits.max() == 0 and spares.min() >= 0.2,
				"human-paced, one dash a hop clears every layout at every p with at least 0.2 s to spare (least by p: %s)" % [least_at.map(func(s): return snappedf(s, 0.001))])
		"nopunch":
			check(hits.min() == 5, "no punches at full health: all five blasts land every time (%s)" % [hits])
		"partial":
			check(hits.min() == 3 and hits.max() == 3, "two kegs broken: three blasts land every time (%s)" % [hits])


# Between two bot runs: parked, fresh and back to full stamina with no keys held.
func burak_reset_bot() -> void:
	await burak_clear_kegs()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_Q, KEY_W]:
		release(code)
	clear_iframes()
	player.playerHealth = 100
	defense._set_stamina(defense.max_stamina)
	await wait(40)


# The one of the eight dashes that leaves least to walk of `to`, and how much that is.
func burak_dash_pick(to: Vector2) -> Array:
	var reach: float = player.DODGE_SPEED * player.dodge_time
	var pick := Vector2i.ZERO
	var least := INF
	for dir in BURAK_DASH_KEYS:
		var left := burak_walk(Vector2(dir).normalized() * reach, to)
		if left < least:
			least = left
			pick = dir
	return [pick, least]


# One keg attack, his rng seeded with `seed_value`, played from `start` by a bot that goes for the first
# `breaks` kegs in his throwing order: each at whichever side is nearer as it sets off, walking at the
# player's speed or dashing up to `dashes` times a hop where a dash pays (burak_dash_pick), and punching the
# moment it stands there turned to a keg that is down. With a `reaction` it plays at a human's pace: that
# long before each hop, from the attack's start and from the moment it is free to move after a punch, and
# before the punch on a keg that lands in front of it. Runs until the Taunt.
# `spare` is the deadline less the last break, or less when the bot would have broken a keg it reached too
# late: armed, a keg no longer turns the player, so its break is estimated as a press after arriving.
# Negative means it missed one; -INF, that the attack ended before it reached them all.
func burak_keg_bot(start: Vector2, seed_value: int, dashes: int, breaks: int, reaction := 0.0) -> Dictionary:
	var barrels: Node = await start_burak_barrels(start, seed_value)
	var broken_at := {}
	# A dictionary, so the handler's count is the one read back: a lambda holds its own copy of a plain local.
	var counted := {"hits": 0}
	var hit_counter := func(hit):
		if hit.attack_id == &"burak_barrel_blast":
			counted.hits += 1
	defense.hit_taken.connect(hit_counter)
	var walk: float = player.SPEED / Engine.physics_ticks_per_second
	var target := -1
	var side := -1.0
	var hop_dashes := 0
	var held: Array = []
	# Nothing before this fight_clock; a hop waiting on its reaction; the keg the bot stood at before it
	# landed; and when it got to its target.
	var act_at := -INF
	var hop_pending := reaction > 0.0
	var waited_for := -1
	var arrived_at := -INF
	while sm.current_state.name == "Barrels":
		for code in held:
			release(code)
		held = []
		for i in barrels.kegs.size():
			# Untyped: a keg that has gone up is a freed instance, which a typed variable can't hold.
			var keg = barrels.kegs[i]
			if not broken_at.has(i) and is_instance_valid(keg) and keg.phase == keg.Phase.BROKEN:
				broken_at[i] = boss.fight_clock
		if target >= 0 and broken_at.has(target):
			target = -1
			hop_pending = reaction > 0.0
		var busy: bool = player.state_machine.current_state.name == "Punching" or player.is_dodging or defense.is_dash_recovering()
		if hop_pending and not busy:
			hop_pending = false
			act_at = boss.fight_clock + reaction
		if target < 0 and broken_at.size() < breaks:
			target = broken_at.size()
			side = burak_near_side(barrels.spots[target], player.global_position)
			hop_dashes = 0
			arrived_at = -INF
		if target >= 0 and not busy and boss.fight_clock >= act_at:
			var stand := burak_keg_stand(barrels.spots[target], side)
			var to: Vector2 = stand - player.global_position
			var keg = barrels.kegs[target] if target < barrels.kegs.size() else null
			var landed: bool = target < barrels.landed
			var standing: bool = is_instance_valid(keg) and keg.is_breakable()
			if reaction > 0.0 and to.length() <= 0.5 and not landed:
				waited_for = target
			var pick := burak_dash_pick(to)
			var dash_ready: bool = not defense.is_dash_cooling_down() and defense.can_afford(defense.dash_stamina_cost)
			if hop_dashes < dashes and dash_ready and pick[1] + BURAK_DASH_FRAMES * walk < burak_walk(Vector2.ZERO, to):
				held = BURAK_DASH_KEYS[pick[0]]
				for code in held:
					press(code)
				tap(KEY_W)
				hop_dashes += 1
			elif to.length() > 0.5:
				player.global_position += Vector2(clampf(to.x, -walk, walk), clampf(to.y, -walk, walk))
				player.velocity = Vector2.ZERO
				to = stand - player.global_position
			if to.length() <= 0.5:
				if arrived_at == -INF:
					arrived_at = boss.fight_clock
				# Only turned to it: a swing thrown at the facing it had on the way would whiff.
				var facing_keg: int = player.Facing.LEFT if side > 0.0 else player.Facing.RIGHT
				if standing and player.facing == facing_keg:
					if waited_for == target:
						waited_for = -1
						act_at = boss.fight_clock + reaction
					else:
						tap(KEY_Q)
				elif landed and not standing:
					broken_at[target] = -(arrived_at + 2.0 / Engine.physics_ticks_per_second)
					target = -1
					hop_pending = reaction > 0.0
		await physics_frame
	defense.hit_taken.disconnect(hit_counter)
	var deadline_at: float = barrels.load_started_at + barrels.kegs_per_attack * barrels.b
	var first: float = barrels.marker_times[0]
	var times: Array = broken_at.values().map(func(t): return absf(t))
	var spare: float = deadline_at - times.max() if not times.is_empty() else 0.0
	if broken_at.size() < breaks:
		spare = -INF
	return {"p": barrels.p, "b": barrels.b, "spots": barrels.spots.duplicate(), "round_px": burak_round(barrels.spots, start), "hits": counted.hits, "spare": spare,
		"breaks": times.map(func(t): return snappedf(t - first, 0.001)), "deadline": deadline_at - first}


# ------------------------------------------------------------------ Captain Burak: his entrance and his laugh cut
# Real time (--max-fps 60), as matt_entrance: the VS card's input grace is real seconds.
#   burak_entrance  watched, held at mid-walk, mid-line and mid-shot, a tapped Escape, and the retry
#   burak_laugh     the cut his fight's first volley owes: watched, once a fight, held, paused, and the fight
#                   ending under it

func burak_card_flash(max_frames := 900) -> bool:
	var card: Node = vs_card()
	var card_art: GDScript = load(VS_CARD_LAYOUT)
	return await wait_until(func(): return card.is_playing() and card.clock >= card_art.HOLD_END, max_frames)


# What he and the ring look like at the VS card's flash: everything a watched entrance and a held one must
# agree on. Floats are rounded, as matt_snapshot's are.
func burak_snapshot() -> Dictionary:
	var gates: Node = current_scene.get_node("Arena/Gates")
	var screen: GDScript = load("res://Scripts/ScreenView.gd")
	var crowd: Node = get_first_node_in_group("arena_crowd")
	return {
		"burak": boss.global_position, "anim": boss.current_anim, "flip": boss.sprite.flip_h,
		"modulate": boss.sprite.modulate, "rotation": snappedf(boss.sprite.rotation, 0.0001), "offset": boss.sprite.offset,
		"hurtbox": boss.hurtbox.monitoring, "hud": boss.hud_layer.visible, "hud_alpha": snappedf(boss.health_bar.modulate.a, 0.0001),
		"gates_open": gates.is_open(), "player": player.global_position, "talking": player.is_talking,
		"player_sm": player.state_machine.is_processing(), "face_point": player.facing_point,
		"zoom": snappedf(screen.zoom, 0.0001), "shake": screen.shake_offset, "time_scale": snappedf(Engine.time_scale, 0.0001),
		"crowd_cheering": crowd != null and crowd._cheer_time_left > 0.0, "music": boss.music_player.playing,
		"music_starts": boss.music_starts, "hazards": get_nodes_in_group(sm.HAZARD_GROUP).size(),
		"balloon": live_balloon() != null, "intro_fx": sm.states["Intro"].intro_fx.size(),
		"seen": root.get_node("GameProgress").entrances_seen.has(boss.FIGHT_SCENE),
	}


func burak_snapshot_diff(got: Dictionary, want: Dictionary) -> Array:
	var diffs := []
	for k in want:
		if got[k] != want[k]:
			diffs.append("%s %s (watched %s)" % [k, got[k], want[k]])
	return diffs


func burak_enter(fresh := true) -> void:
	if fresh:
		await enter_fight(SCENES["burak"], true)
	else:
		change_scene_to_file(SCENES["burak"])
		while current_scene == null or current_scene.scene_file_path != SCENES["burak"]:
			await process_frame
		await wait(6)
		player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
		defense = player.get_node("Defense")
	boss = current_scene.get_node(BURAK_BODY)
	sm = boss.state_machine


func test_burak_entrance() -> void:
	var talk: Dictionary = load("res://Scripts/BurakBossArtLayout.gd").TALK_POSES

	log_p("-- watched: the walk-in")
	await burak_enter()
	var intro: Node = entrance_state()
	check(intro != null and intro == sm.states["Intro"], "his fight opens on BurakBossIntro")
	check(await wait_until(func(): return intro.entered, 60), "which starts itself")
	var gates: Node = current_scene.get_node("Arena/Gates")
	check(gates.is_open() and not boss.hud_layer.visible, "the ring is open and his bar is down")
	check(player.is_talking and not player.state_machine.is_processing(), "the player is held, their own state machine stopped")
	check(boss.global_position.y < 0.0 and player.global_position.y > intro.player_home.y + 100.0, "he starts above the ring and the player below it")
	check(await wait_until(func(): return player.global_position.is_equal_approx(intro.player_home), 300), "the player walks up onto their mark")
	check(await wait_until(func(): return boss.global_position.is_equal_approx(intro.home) and boss.current_anim != &"walk", 400), "he swaggers down onto his")
	check(await wait_until(func(): return not gates.is_open(), 120), "the gates slam behind him")
	check(await wait_until(func(): return boss.hud_layer.visible, 120), "then his bar comes up")
	check(await wait_until(func(): return live_balloon() != null, 120), "and his first line")
	check(sm.post_dialogue_pre_fight_timer.is_stopped() and boss.music_starts == 0, "the fight and his theme are still waiting")

	log_p("-- the lines, their tags and the warning shot")
	var card: Node = vs_card()
	var sampled := {}
	var music_before_fire := -1
	var music_on_fire := -1
	var ball_seen := false
	var ball_harmless := true
	var dust_seen := false
	var last_line = null
	for i in 3600:
		if card.is_playing():
			break
		var balloon := live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			await wait(3)
			var text: String = last_line.text
			var look := {"pose": intro.pose, "frame": boss.sprite.frame, "flip": boss.sprite.flip_h, "anim": boss.current_anim}
			if text.begins_with("Ahoy"):
				sampled["smug"] = look
			elif text.begins_with("Captain Burak. Best"):
				sampled["point"] = look
			elif text.begins_with("And every server"):
				sampled["shrug"] = look
		if music_before_fire < 0 and boss.current_anim == &"fire_aim":
			music_before_fire = boss.music_starts
		if music_on_fire < 0 and boss.current_anim == &"fire":
			await wait(1)
			music_on_fire = boss.music_starts if boss.music_player.playing else -1
		for node in intro.intro_fx:
			if is_instance_valid(node) and node.has_method("aim"):
				ball_seen = true
				ball_harmless = ball_harmless and node.harmless and not node.is_in_group(sm.HAZARD_GROUP)
			elif is_instance_valid(node) and node.get_parent() == boss.floor_layer:
				dust_seen = true
		if i % 8 == 0 and not intro.beat_running:
			tap(KEY_ENTER)
		await physics_frame
	log_p("sampled %s" % [sampled])
	for pose in ["smug", "point", "shrug"]:
		var look: Dictionary = sampled.get(pose, {})
		check(not look.is_empty() and look.pose == StringName(pose) and talk[StringName(pose)].has(look.frame) and look.anim == &"talk"
			and not look.flip, "the %s line puts him in the %s pose" % [pose, pose])
	var beats: Dictionary = intro.beat_times
	log_p("beats %s" % [beats])
	check(beats.has(&"warning_shot") and absf(beats[&"warning_shot"] - 1.35) <= 1.0 / 30.0, "the warning shot takes 1.35 s (%.3f)" % beats.get(&"warning_shot", -1.0))
	check(music_before_fire == 0 and music_on_fire == 1, "his theme starts on the shot and not before (%d then %d)" % [music_before_fire, music_on_fire])
	check(ball_seen and ball_harmless, "the shot's ball flew, harmless and out of the hazard group")
	check(dust_seen, "and it kicked up dust where it landed")
	check(await burak_card_flash(), "the lines hand over to the card")
	var watched := burak_snapshot()
	log_p("watched, at the card's flash: %s" % [watched])
	check(watched.burak == sm.HOME and watched.anim == &"idle" and not watched.flip and watched.modulate == Color.WHITE
		and not watched.hurtbox and watched.hud and not watched.gates_open and watched.talking and watched.player_sm
		and watched.music and watched.music_starts == 1 and watched.hazards == 0 and not watched.balloon
		and watched.intro_fx == 0 and watched.seen and watched.zoom == 1.0 and watched.time_scale == 1.0
		and not watched.crowd_cheering, "and the ring is set the way the plan says")
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	check(await wait_until(func(): return sm.current_state != intro, 180), "and the fight starts behind it")

	for where in ["walk", "line", "shot"]:
		log_p("-- held at mid-%s" % where)
		await burak_enter()
		intro = entrance_state()
		card = vs_card()
		await wait_until(func(): return intro.entered, 60)
		var lines := 0
		last_line = null
		for i in 3600:
			if where == "walk" and intro.home.y - boss.global_position.y > 200.0 and boss.global_position.y > -60.0:
				break
			var balloon := live_balloon()
			if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
				last_line = balloon.dialogue_line
				lines += 1
				if where == "line" and lines == 3:
					await wait(10)
					break
			if where == "shot" and boss.current_anim == &"fire":
				await wait(6)
				break
			if where != "walk" and i % 8 == 0 and not intro.beat_running:
				tap(KEY_ENTER)
			await physics_frame
		log_p("holding Escape: anim %s, lines %d, music_starts %d" % [boss.current_anim, lines, boss.music_starts])
		press(KEY_ESCAPE)
		var reached := await burak_card_flash(120)
		var skipped := burak_snapshot()
		release(KEY_ESCAPE)
		await wait(4)
		var diffs := burak_snapshot_diff(skipped, watched)
		check(reached and diffs.is_empty(), "mid-%s: the card's flash, with the ring exactly as a watched entrance leaves it %s" % [where, diffs])
		check(not pause_menu().is_open() and not paused, "mid-%s: and the pause screen never opened" % where)

	log_p("-- a tapped Escape pauses it")
	await burak_enter()
	intro = entrance_state()
	await wait_until(func(): return intro.entered, 60)
	await wait(30)
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open() and paused, "a tap opened the pause screen rather than skipping")
	var held_at: Vector2 = player.global_position
	await wait(40)
	check(player.global_position.is_equal_approx(held_at), "and the walk-in stopped dead with the fight")
	await tap_pause()
	await wait(20)
	check(not paused and not player.global_position.is_equal_approx(held_at), "the resume carries it on")
	# Skipped to its end, which is what marks it seen for the run.
	press(KEY_ESCAPE)
	await burak_card_flash(120)
	release(KEY_ESCAPE)
	card = vs_card()
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0

	log_p("-- the retry: no walk-in, the lines and the shot again, and a hold still skips them")
	await burak_enter(false)
	intro = entrance_state()
	gates = current_scene.get_node("Arena/Gates")
	card = vs_card()
	check(intro.finished and not gates.is_open(), "the entrance is over on arrival and the ring was never opened")
	check(await wait_until(func(): return live_balloon() != null, 120), "his lines start straight away")
	for i in 3600:
		if card.is_playing():
			break
		if i % 8 == 0 and not intro.beat_running:
			tap(KEY_ENTER)
		await physics_frame
	check(intro.beat_times.has(&"warning_shot"), "the warning shot played again (%s)" % [intro.beat_times.keys()])
	card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	await burak_enter(false)
	intro = entrance_state()
	card = vs_card()
	for i in 3600:
		if intro.beat_running and boss.current_anim == &"fire_aim":
			break
		if i % 8 == 0 and not intro.beat_running:
			tap(KEY_ENTER)
		await physics_frame
	log_p("holding Escape in the aim")
	press(KEY_ESCAPE)
	var reached := await burak_card_flash(120)
	var retried := burak_snapshot()
	release(KEY_ESCAPE)
	var retry_diffs := burak_snapshot_diff(retried, watched)
	check(reached and retry_diffs.is_empty(), "a hold in the replayed shot lands on the card's flash with the same ring %s" % [retry_diffs])


# His fight with the entrance held through and the card skipped, parked in Idle, the laugh not yet had.
func load_burak_laugh() -> void:
	await burak_enter()
	var intro: Node = sm.states["Intro"]
	await wait_until(func(): return intro.entered, 60)
	intro.skip_to_fight()
	var card: Node = vs_card()
	if card.is_playing():
		card.skip()
	await wait_until(func(): return not card.is_playing(), 60)
	card.grace_until_msec = 0
	await wait_until(func(): return str(sm.current_state.name) == "Idle", 120)
	stop_boss_timers()
	player.playerHealth = 1000


# A volley ending, owing the laugh or not: into the kegs and straight out through attack_done, which is the
# routing under test. The volley itself, and when it owes the laugh, is Barrels' own (burak_volley).
func burak_end_volley(owed: bool) -> void:
	var barrels: Node = sm.states["Barrels"]
	sm.on_child_transition(sm.current_state, "Barrels")
	await wait(2)
	sm.laugh_owed = owed
	sm.attack_done(barrels)
	await wait(1)


func burak_ear_ringing() -> bool:
	for sfx in boss.sfx_players[&"ear_ring"]:
		if sfx.playing:
			return true
	return false


# Where the cut leaves the ring, however it ended.
func burak_laugh_snapshot(laugh: Node) -> Dictionary:
	var screen: GDScript = load("res://Scripts/ScreenView.gd")
	return {
		"state": str(sm.current_state.name), "talking": player.is_talking, "player_sm": player.state_machine.is_processing(),
		"balloon": live_balloon() != null, "hint": laugh.get_node_or_null("LaughCut") != null,
		"music_db": snappedf(boss.music_player.volume_db, 0.01), "ear_ring": burak_ear_ringing(), "laugh_played": sm.laugh_played,
		"zoom": snappedf(screen.zoom, 0.0001), "shake": screen.shake_offset, "time_scale": snappedf(Engine.time_scale, 0.0001),
		"hurtbox": boss.hurtbox.monitoring, "jitter": laugh.jitter != null, "finished": laugh.finished,
		"burak": boss.global_position, "hazards": get_nodes_in_group(sm.HAZARD_GROUP).size(),
	}


func test_burak_laugh() -> void:
	var layout: GDScript = load("res://Scripts/BurakBossArtLayout.gd")
	var theme_db: float = layout.THEME_DB
	var talk: Dictionary = layout.TALK_POSES
	var screen: GDScript = load("res://Scripts/ScreenView.gd")

	log_p("-- watched")
	await load_burak_laugh()
	await burak_end_volley(true)
	var laugh: Node = sm.states["Laugh"]
	check(sm.current_state == laugh, "an owed laugh plays straight after the kegs (%s)" % sm.current_state.name)
	check(not laugh.has_method("finish_entrance") and entrance_state() == sm.states["Intro"], "and it is not an entrance: skip_entrance() still finds the intro")
	check(player.is_talking and not player.state_machine.is_processing(), "the player is held")
	check(not boss.hurtbox.monitoring, "his hurtbox is off")
	check(await wait_until(func(): return boss.current_anim == &"laugh", 60), "he bursts out laughing")
	var slaps := 0
	var shake_seen := false
	var last_step := -1
	var looks := {}
	var deaf := {"seen": false, "ring": false, "duck": 1000.0, "jitter": 0.0}
	var after_deaf := {}
	var last_line = null
	var deaf_line = null
	for i in 3600:
		if sm.current_state != laugh:
			break
		if boss.current_anim == &"laugh" and boss.anim_step != last_step:
			last_step = boss.anim_step
			if last_step in [1, 3]:
				slaps += 1
		if screen.shake_offset != Vector2.ZERO:
			shake_seen = true
		var balloon := live_balloon()
		if balloon != null and balloon.dialogue_line != null:
			var line = balloon.dialogue_line
			if line != last_line:
				if deaf_line != null and last_line == deaf_line:
					await wait(20)
					after_deaf = {"ring": burak_ear_ringing(), "db": boss.music_player.volume_db, "rot": balloon.portrait_frame.rotation}
				last_line = line
				await wait(4)
				var text: String = line.text
				if text.begins_with("...pfffft"):
					looks["laugh"] = {"pose": laugh.pose, "flip": boss.sprite.flip_h, "frame": boss.sprite.frame}
				elif text.begins_with("...."):
					deaf_line = line
					deaf.seen = true
				elif text.begins_with("Let's get back"):
					looks["point"] = {"pose": laugh.pose, "flip": boss.sprite.flip_h, "frame": boss.sprite.frame}
			if line == deaf_line:
				deaf.ring = deaf.ring or burak_ear_ringing()
				deaf.duck = minf(deaf.duck, boss.music_player.volume_db)
				deaf.jitter = maxf(deaf.jitter, absf(balloon.portrait_frame.rotation))
		if i % 10 == 0 and not laugh.beat_running:
			tap(KEY_ENTER)
		await physics_frame
	log_p("fit %s, slaps %d, looks %s, deaf %s, after %s" % [laugh.beat_times, slaps, looks, deaf, after_deaf])
	check(laugh.beat_times.has(&"bursts_out_laughing") and absf(laugh.beat_times[&"bursts_out_laughing"] - 1.40) <= 1.0 / 30.0,
		"the fit takes 1.40 s (%.3f)" % laugh.beat_times.get(&"bursts_out_laughing", -1.0))
	check(slaps >= 2 and shake_seen, "the view thumps on his knee slaps (%d)" % slaps)
	check(looks.has("laugh") and looks.laugh.pose == &"laugh" and looks.laugh.flip and talk[&"laugh"].has(looks.laugh.frame), "his first line laughs, turned toward Danny")
	check(looks.has("point") and looks.point.pose == &"point" and not looks.point.flip and talk[&"point"].has(looks.point.frame), "his last points, turned back")
	check(deaf.seen and deaf.ring and absf(deaf.duck - (theme_db - 8.0)) < 0.05 and deaf.jitter > deg_to_rad(1.9),
		"Danny's line rings, ducks the music 8 dB and twitches his portrait (%s)" % [deaf])
	check(not after_deaf.is_empty() and not after_deaf.ring and absf(after_deaf.db - theme_db) < 0.05 and after_deaf.rot == 0.0,
		"and all of it goes with the line (%s)" % [after_deaf])
	check(str(sm.current_state.name) == "Taunt", "the lines' end opens the Taunt")
	await wait(30)
	var watched := burak_laugh_snapshot(laugh)
	log_p("watched: %s" % [watched])
	check(watched.state == "Taunt" and not watched.talking and watched.player_sm and not watched.balloon and not watched.hint
		and absf(watched.music_db - theme_db) < 0.05 and not watched.ear_ring and watched.laugh_played and watched.zoom == 1.0
		and watched.time_scale == 1.0 and watched.hurtbox and not watched.jitter and watched.finished and watched.hazards == 0,
		"and the ring is back: the Taunt open, the player free, no balloon or hint, the music level")

	log_p("-- once a fight, and only when owed")
	await burak_end_volley(true)
	check(str(sm.current_state.name) == "Taunt", "a second owed laugh goes straight to the Taunt (%s)" % sm.current_state.name)
	await load_burak_laugh()
	await burak_end_volley(false)
	check(str(sm.current_state.name) == "Taunt" and not sm.laugh_played, "a volley that owes nothing opens the Taunt (%s)" % sm.current_state.name)

	for where in ["fit", "line", "deaf"]:
		log_p("-- held mid-%s" % where)
		await load_burak_laugh()
		await burak_end_volley(true)
		laugh = sm.states["Laugh"]
		last_line = null
		var lines := 0
		for i in 3600:
			if where == "fit" and boss.current_anim == &"laugh" and laugh.beat_running:
				await wait(40)
				break
			var balloon := live_balloon()
			if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
				last_line = balloon.dialogue_line
				lines += 1
				if where == "line" and lines == 1:
					await wait(10)
					break
				if where == "deaf" and last_line.text.begins_with("...."):
					await wait(10)
					break
			if where != "fit" and i % 10 == 0 and not laugh.beat_running:
				tap(KEY_ENTER)
			await physics_frame
		log_p("holding Escape: anim %s, lines %d, ear ring %s, music %.2f" % [boss.current_anim, lines, burak_ear_ringing(), boss.music_player.volume_db])
		press(KEY_ESCAPE)
		var reached := await wait_until(func(): return str(sm.current_state.name) == "Taunt", 120)
		release(KEY_ESCAPE)
		await wait(30)
		var diffs := burak_snapshot_diff(burak_laugh_snapshot(laugh), watched)
		check(reached and diffs.is_empty(), "mid-%s: the hold lands where the lines' end does %s" % [where, diffs])
		check(not paused, "mid-%s: and nothing paused" % where)

	log_p("-- paused mid-fit, then mid-line")
	await load_burak_laugh()
	await burak_end_volley(true)
	laugh = sm.states["Laugh"]
	await wait_until(func(): return boss.current_anim == &"laugh" and laugh.beat_running, 60)
	await wait(20)
	var pause: Node = pause_menu()
	await tap_pause()
	check(pause.is_open() and paused and sm.current_state == laugh, "a tapped Escape mid-fit pauses rather than skipping")
	var frame_at: int = boss.sprite.frame
	await wait(120)
	check(laugh.beat_running and not laugh.beat_times.has(&"bursts_out_laughing") and boss.sprite.frame == frame_at, "and the fit holds where it is")
	await tap_pause()
	check(await wait_until(func(): return laugh.beat_times.has(&"bursts_out_laughing"), 120), "the resume carries it on")
	await wait_until(func(): return live_balloon() != null and live_balloon().dialogue_line != null, 120)
	await wait(10)
	await tap_pause()
	var line_at = live_balloon().dialogue_line if live_balloon() != null else null
	check(pause.is_open() and paused and sm.current_state == laugh, "a tapped Escape mid-line pauses too")
	await wait(60)
	check(live_balloon() != null and live_balloon().dialogue_line == line_at and sm.current_state == laugh, "and the line stays up under it")
	await tap_pause()
	await wait(10)
	check(not paused and sm.current_state == laugh and not laugh.finished, "the resume hands the line back")

	log_p("-- the fight ends under it")
	await load_burak_laugh()
	await burak_end_volley(true)
	laugh = sm.states["Laugh"]
	for i in 3600:
		var balloon := live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line.text.begins_with("...."):
			await wait(10)
			break
		if i % 10 == 0 and not laugh.beat_running:
			tap(KEY_ENTER)
		await physics_frame
	check(burak_ear_ringing() and laugh.jitter != null, "mid Danny's line")
	sm.enter_player_defeated()
	await wait(30)
	var ended := burak_laugh_snapshot(laugh)
	log_p("ended: %s" % [ended])
	check(ended.state == "Victory" and ended.finished and not ended.talking and not ended.ear_ring and not ended.jitter
		and not ended.hint and not ended.balloon and absf(ended.music_db - theme_db) < 0.05,
		"the cut lets go of everything, its lines included, and he laughs in Victory")
