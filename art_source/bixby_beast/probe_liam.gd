extends SceneTree

# How the Liam & Bixby fight was measured against the V2 player, kept so the numbers can be checked
# again. Not part of the defence suite: it reports, it doesn't pass or fail.
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/bixby_beast/probe_liam.gd -- bot=<name>
# bot=punch    punch-only kill run, no finisher and no guard: proves the punish windows pay out
# bot=full     punch, finisher and a guard re-pressed every mash lockout, to the end of the fight.
#              Needs --max-fps 60: the finisher's mash gates presses on real seconds
# bot=ceiling  the same with every press credited, so every parryable hit is parried: the hype ceiling
# bot=window   how many frames before the hurtbox opens a punch can be thrown and still land
# bot=dodge    whether each of his three can still be got out of, and how tight the dash is
# bot=tells    every ParryTell he raises: colour, when, where and for how long
# bot=census   his loop, state by state, with what it lands on a player who does nothing
# bot=shot     windowed, saves a frame of each tell. Needs --resolution 1920x1080 --position 100,100

const SCENE := "res://Scenes/Bosses/LiamBossFightScene.tscn"
const BOSS_PATH := "Arena/BixbyBeastScene/BixbyBeastCharacterBody"

var bot := "punch"
var clock := 0.0
var frame := 0
var player: CharacterBody2D
var defense: Node
var combo: Node
var hype: Node
var finisher: Node
var boss: Node
var bsm: Node


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("bot="):
			bot = arg.substr(4)
	_main.call_deferred()


func _process(delta: float) -> bool:
	clock += delta
	frame += 1
	return false


func p(msg: String) -> void:
	print("P [%.3f f%d] %s" % [clock, frame, msg])


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


func load_liam() -> void:
	change_scene_to_file(SCENE)
	while current_scene == null or current_scene.scene_file_path != SCENE:
		await process_frame
	await wait(3)
	player = current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	defense = player.get_node("Defense")
	combo = player.get_node("Combo")
	hype = player.get_node("Hype")
	finisher = player.get_node("Finisher")
	boss = current_scene.get_node(BOSS_PATH)
	bsm = boss.state_machine
	for i in 3000:
		if bsm.current_state.name != "Intro":
			break
		if i % 15 == 0:
			tap(KEY_ENTER)
		await physics_frame
	var card: Node = current_scene.get_node_or_null("Arena/VsCard")
	if card and card.is_playing():
		card.skip()
		await wait_until(func(): return not card.is_playing(), 120)
	if card:
		card.grace_until_msec = 0
	await wait(2)
	p("intro done in %s, boss %d HP, feel_v2 %s" % [bsm.current_state.name, boss.boss_health, player.feel_v2])


func place_under(area: Area2D) -> void:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	var half: Vector2 = shape.shape.size * shape.global_scale.abs() / 2.0
	var hb: CollisionShape2D = player.get_node("Hitbox/CollisionShape2D")
	var reach: Vector2 = hb.global_position - player.global_position
	player.global_position = Vector2(shape.global_position.x - reach.x, shape.global_position.y + half.y - reach.y - 4.0)


# One swing, from the press to the punch state ending.
func swing() -> void:
	tap(KEY_Q)
	for i in 10:
		await physics_frame
		if player.state_machine.current_state.name == "Punching":
			break
	while player.state_machine.current_state.name == "Punching":
		await physics_frame


# Mashes the finisher prompt. min_press_interval is real seconds, so the gap is spun out in real time.
func mash() -> void:
	var pair: Array = finisher.mash_actions()
	var keys := {&"punch": KEY_Q, &"dodge": KEY_W, &"mash_left": KEY_LEFT, &"mash_right": KEY_RIGHT}
	var step := 0
	var spent := 0
	while (finisher.phase == 2 or finisher.phase == 3) and spent < 600:
		tap(keys[pair[step % 2]])
		step += 1
		var since := Time.get_ticks_usec()
		while Time.get_ticks_usec() - since < 35000 and (finisher.phase == 2 or finisher.phase == 3):
			spent += 1
			await physics_frame


var hits: Array = []
var parries: Array = []
var dodges: Array = []
var blocked: Array = []


func track() -> void:
	defense.hit_taken.connect(func(hit): hits.append({"id": hit.attack_id, "t": clock}))
	defense.parried.connect(func(hit, _c, _s, streak): parries.append({"id": hit.attack_id, "t": clock, "streak": streak}))
	defense.perfect_dodged.connect(func(hit): dodges.append({"id": hit.attack_id, "t": clock}))
	defense.blocked.connect(func(hit, _c): blocked.append({"id": hit.attack_id, "t": clock}))


func summary(label: String, started: float) -> void:
	var ids := {}
	for h in hits:
		ids[h.id] = ids.get(h.id, 0) + 1
	var bids := {}
	for b in blocked:
		bids[b.id] = bids.get(b.id, 0) + 1
	var pids := {}
	for b in parries:
		pids[b.id] = pids.get(b.id, 0) + 1
	p("%s: %.1f s, boss %d/%d HP, player %d HP, hype %.0f (full %s)" % [
		label, clock - started, boss.boss_health, boss.max_health, player.playerHealth, hype.hype, hype.is_full()])
	p("  hits %s, blocked %s, parried %s (%d), dodged %d" % [ids, bids, pids, parries.size(), dodges.size()])
	if parries.is_empty():
		return
	# The parry tiers the hype cut is paid at: [25,30,35] became [15,20,25], which is -40% on the
	# first parry of a chain but only -28.6% on the third and up.
	var tiers := [0, 0, 0]
	for e in parries:
		tiers[clampi(e.streak - 1, 0, 2)] += 1
	var was: float = tiers[0] * 25.0 + tiers[1] * 30.0 + tiers[2] * 35.0
	var now: float = tiers[0] * 15.0 + tiers[1] * 20.0 + tiers[2] * 25.0
	p("  parry tiers [1st, 2nd, 3rd+] %s: V1 would pay %.0f, V2 pays %.0f, a %.1f%% cut" % [
		tiers, was, now, 100.0 * (was - now) / was])


# ------------------------------------------------------------------ bots

func _main() -> void:
	await load_liam()
	match bot:
		"punch":
			await bot_punch()
		"full":
			await bot_full()
		"window":
			await bot_window()
		"census":
			await bot_census()
		"ceiling":
			await bot_ceiling()
		"tells":
			await bot_tells()
		"shot":
			await bot_shot()
		"dodge":
			await bot_dodge()
	quit(0)


# Can each of his three still be got out of, and is any of them free now the dash is quicker?
func bot_dodge() -> void:
	player.playerHealth = 100000
	track()
	p("-- the sonic beams, a dash every 39 frames (past DASH_IMMUNITY_COOLDOWN), started at every phase")
	var dodged_at := []
	for offset in [0, 5, 10, 15, 20, 25, 30, 35]:
		await wait_until(func(): return bsm.current_state.name == "Combined" and bsm.current_state.phase == 3, 3000)
		hits.clear()
		dodges.clear()
		var since := []
		var watching := true
		var tap_frames := []
		defense.hit_taken.connect(func(_h): if watching: since.append(frame - (tap_frames[-1] if not tap_frames.is_empty() else 0)))
		await wait(offset)
		var dashes := 0
		while bsm.current_state.name == "Combined" and bsm.current_state.phase <= 5:
			defense.stamina = defense.max_stamina
			tap(KEY_W)
			tap_frames.append(frame)
			dashes += 1
			await wait(39)
		watching = false
		p("  offset %2d: %d dashes, %d perfect dodges, %d hits (frames since the last dash %s)" % [
			offset, dashes, dodges.size(), hits.size(), since])
		if not dodges.is_empty():
			dodged_at.append(offset)
		await wait_until(func(): return bsm.current_state.name != "Combined", 1200)
	p("  a dash beat the beams at these offsets: %s" % [dodged_at])

	p("-- the same scream standing still, for the comparison")
	for run in 2:
		await wait_until(func(): return bsm.current_state.name == "Combined" and bsm.current_state.phase == 3, 3000)
		hits.clear()
		dodges.clear()
		var swept := clock
		while bsm.current_state.name == "Combined" and bsm.current_state.phase <= 5:
			await physics_frame
		p("  scream %d over %.2f s: %d hits standing in it" % [run + 1, clock - swept, hits.size()])
		await wait_until(func(): return bsm.current_state.name != "Combined", 1200)

	p("-- the fire stream, walking out from under him as the wind-up starts (it follows at breath_drift_speed)")
	for run in 3:
		await wait_until(func(): return bsm.current_state.name == "FireBreath" and bsm.current_state.phase == 1, 3000)
		hits.clear()
		var away := KEY_RIGHT if boss.global_position.x <= player.global_position.x else KEY_LEFT
		press(away)
		while bsm.current_state.name == "FireBreath":
			await physics_frame
		release(away)
		p("  breath %d: %d hits, walked %.0f px clear" % [run + 1, hits.size(), absf(player.global_position.x - boss.ground_position.x)])
		await wait(30)

	p("-- the ground waves, walking clear of the crack line once the pounds are done")
	for run in 3:
		await wait_until(func(): return bsm.current_state.name == "Combined" and bsm.current_state.phase == 3, 3000)
		hits.clear()
		var cracks := get_nodes_in_group(bsm.HAZARD_GROUP)
		var away := KEY_RIGHT if boss.global_position.x <= player.global_position.x else KEY_LEFT
		press(away)
		await wait(60)
		release(away)
		await wait_until(func(): return bsm.current_state.name != "Combined", 1200)
		p("  pounds %d: %d cracks lit, %d hits after walking clear" % [run + 1, cracks.size(), hits.size()])


# Windowed: saves a crop around each tell the first time it comes up, to look at the anchoring.
#   Godot.exe --path . --resolution 1920x1080 --position 100,100 --fixed-fps 60 --script ... -- bot=shot out=<dir>
func bot_shot() -> void:
	var out_dir := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("out="):
			out_dir = arg.substr(4)
	DirAccess.make_dir_recursive_absolute(out_dir)
	player.playerHealth = 100000
	var taken := {}
	var started := clock
	while clock - started < 90.0 and taken.size() < 3:
		player.global_position = Vector2(760, 700)
		for node in current_scene.find_children("ParryTell*", "Node2D", true, false):
			if node.name.ends_with("Spent"):
				continue
			var kind := "yellow_sonic" if node.dodge else ("red_crack" if node.boss != boss else "red_fire")
			if taken.has(kind):
				continue
			taken[kind] = true
			await wait(6)
			await process_frame
			var shot := root.get_texture().get_image()
			shot.save_png("%s/%s.png" % [out_dir, kind])
			p("  saved %s at %s" % [kind, node.global_position.round()])
		await physics_frame
	p("shots: %s" % [taken.keys()])


# Every ParryTell that comes up in two cycles of his loop: colour, when, where and for how long.
func bot_tells() -> void:
	player.playerHealth = 100000
	track()
	var live := {}
	var started := clock
	while clock - started < 90.0:
		player.global_position = Vector2(760, 700)
		var now := {}
		for node in current_scene.find_children("ParryTell*", "Node2D", true, false):
			if node.name.ends_with("Spent"):
				continue
			now[node.get_instance_id()] = node
			if not live.has(node.get_instance_id()):
				var colour := "YELLOW dodge" if node.dodge else ("RED strong" if node.strong else "RED")
				var owner_name: String = node.boss.name if is_instance_valid(node.boss) else "?"
				live[node.get_instance_id()] = {
					"t": clock, "colour": colour, "on": owner_name,
					"at": node.global_position, "state": _state_tag(), "said": node.time_left}
		for id in live.keys():
			if now.has(id):
				continue
			var e: Dictionary = live[id]
			p("  %-12s on %-22s %5.2f s (booked %.2f) from %s, at %s -> %s" % [
				e.colour, e.on, clock - e.t, e.said, e.state, e.at.round(), _state_tag()])
			live.erase(id)
		await physics_frame
	p("tells still up at the end: %d" % live.size())
	summary("tells", started)


func _state_tag() -> String:
	var cur = bsm.current_state
	var phase := -1
	if "phase" in cur:
		phase = cur.phase
	return "%s/%d" % [cur.name, phase]


# The most hype the fight can pay: every parryable hit parried, every punish window punched out.
func bot_ceiling() -> void:
	player.playerHealth = 100000
	track()
	var peak := [0.0]
	hype.hype_changed.connect(func(v, _m): peak[0] = maxf(peak[0], v))
	# Every press credited, so the parry window is open the whole fight: the ceiling, not a read.
	defense.parry_mash_lockout = 0.0
	var started := clock
	var windows := 0
	press(KEY_SHIFT)
	while boss.boss_health > 0 and clock - started < 300.0:
		defense.stamina = defense.max_stamina
		release(KEY_SHIFT)
		press(KEY_SHIFT)
		if not bsm.is_recovering():
			await physics_frame
			continue
		windows += 1
		var at_start: int = boss.boss_health
		var hype_at_start: float = hype.hype
		release(KEY_SHIFT)
		var swings := 0
		while bsm.is_recovering() and boss.boss_health > 0 and swings < 3 and not player.is_finishing:
			place_under(boss.hurtbox)
			await wait(2)
			await swing()
			swings += 1
			await wait_until(func(): return combo.window_open or not bsm.is_recovering(), 40)
		p("  window %d: %d HP -> %d, hype %.0f -> %.0f" % [windows, at_start, boss.boss_health, hype_at_start, hype.hype])
		press(KEY_SHIFT)
		await wait_until(func(): return not bsm.is_recovering(), 900)
	var end_hype: float = hype.hype
	release(KEY_SHIFT)
	var streaks := parries.map(func(e): return e.streak)
	summary("ceiling", started)
	p("  %d punish windows, hype at the kill %.0f, peak %.0f, parry streaks %s" % [windows, end_hype, peak[0], streaks])


# No guard, no finisher: three punches a window until he dies. Proves the punish window pays.
func bot_punch() -> void:
	player.playerHealth = 1000
	track()
	var started := clock
	var windows := 0
	var punches := 0
	var landed := 0
	while boss.boss_health > 0 and clock - started < 300.0:
		if not bsm.is_recovering():
			await physics_frame
			continue
		windows += 1
		var window_state: String = bsm.current_state.name
		var at_start: int = boss.boss_health
		var swings := 0
		var window_opened := clock
		while bsm.is_recovering() and boss.boss_health > 0 and swings < 3:
			place_under(boss.hurtbox)
			await wait(2)
			var before: int = boss.boss_health
			var was_open: bool = combo.window_open
			var pressed := clock
			await swing()
			swings += 1
			punches += 1
			if boss.boss_health < before:
				landed += 1
			p("    punch %d at +%.2f s: pressed on beat %s, dealt %d, combo %d, hurtbox %s" % [
				swings, pressed - window_opened, was_open, before - boss.boss_health, combo.count, boss.hurtbox.monitorable])
			# On the beat: the window opens a beat after the swing ends.
			await wait_until(func(): return combo.window_open or not bsm.is_recovering(), 40)
		var during := hits.filter(func(h): return h.t >= window_opened).map(func(h): return "%s at +%.2f" % [h.id, h.t - window_opened])
		p("  window %d (%s): %d HP -> %d over %.2f s, combo %d, hype %.0f, hits during it %s" % [windows, window_state, at_start, boss.boss_health, clock - window_opened, combo.count, hype.hype, during])
		# Out of the way, and wait for the window to close so the next one is counted once.
		await wait_until(func(): return not bsm.is_recovering(), 900)
	summary("punch-only", started)
	p("  %d punish windows, %d punches, %d landed" % [windows, punches, landed])
	p("  killed: %s" % [boss.boss_health <= 0])


# The fight as played: guard up, re-pressed so the parry window is open as much as the rules allow,
# three punches and a finisher every window.
func bot_full() -> void:
	track()
	var started := clock
	var windows := 0
	var uppercuts := 0
	var last_press := -10.0
	press(KEY_SHIFT)
	while boss.boss_health > 0 and not player.fight_over and clock - started < 300.0:
		# A fresh press every mash lockout, so the parry window is open 0.24 of every 0.5 s.
		if clock - last_press >= 0.5 and defense.is_guarding() and not player.is_finishing:
			release(KEY_SHIFT)
			await physics_frame
			press(KEY_SHIFT)
			last_press = clock
		defense.stamina = defense.max_stamina
		if not bsm.is_recovering():
			await physics_frame
			continue
		windows += 1
		var at_start: int = boss.boss_health
		var hype_at_start: float = hype.hype
		release(KEY_SHIFT)
		var swings := 0
		while bsm.is_recovering() and boss.boss_health > 0 and swings < 3 and not player.is_finishing:
			place_under(boss.hurtbox)
			await wait(2)
			await swing()
			swings += 1
			await wait_until(func(): return combo.window_open or not bsm.is_recovering() or player.is_finishing, 40)
		if await wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120):
			var before: int = boss.boss_health
			p("  window %d: dazed, hype %.0f, supercharged %s" % [windows, hype.hype, finisher.supercharged])
			await mash()
			await wait_until(func(): return boss.boss_health < before or finisher.phase == 0, 300)
			uppercuts += 1
		await wait_until(func(): return finisher.phase == 0, 300)
		p("  window %d: %d HP -> %d, hype %.0f -> %.0f" % [windows, at_start, boss.boss_health, hype_at_start, hype.hype])
		press(KEY_SHIFT)
		last_press = clock
		await wait_until(func(): return not bsm.is_recovering(), 900)
	var end_hype: float = hype.hype
	release(KEY_SHIFT)
	summary("full", started)
	p("  %d punish windows, %d uppercuts, hype at the kill %.0f" % [windows, uppercuts, end_hype])


# How early a punch can be thrown before the window opens and still land, which is what moved when
# the punch started resolving at arm extension.
func bot_window() -> void:
	player.playerHealth = 1000
	p("-- a punch thrown N frames before Recover opens; V2 resolves at extension")
	p("  last lead that lands, V2: %d frames" % await last_lead_that_lands())
	p("-- and the same with the legacy resolve, for the comparison")
	player.feel_v2 = false
	p("  last lead that lands, V1: %d frames" % await last_lead_that_lands())
	player.feel_v2 = true


# Walks the lead out a frame at a time and reports the last one that still connects.
func last_lead_that_lands() -> int:
	var best := -1
	for lead in range(0, 32):
		var ok := await try_lead(lead)
		p("    %2d frames early: %s" % [lead, "LANDS" if ok else "whiffs"])
		if ok:
			best = lead
		elif best >= 0:
			break
	return best


# Puts him in Land's last beat, waits until `lead` frames before Recover, punches, reports whether
# it dealt damage.
func try_lead(lead: int) -> bool:
	# Straight into the landing, from hover height.
	await wait_until(func(): return bsm.current_state.name == "Hover" or bsm.current_state.name == "Recover", 1200)
	if bsm.current_state.name == "Recover":
		await wait_until(func(): return bsm.current_state.name != "Recover", 600)
		await wait_until(func(): return bsm.current_state.name == "Hover", 1200)
	bsm.on_child_transition(bsm.current_state, "Land")
	# The landing's own frames decide when Recover opens; punch `lead` frames before it does.
	var land: Node = bsm.states["Land"]
	var opened := false
	var swung := false
	var before: int = boss.boss_health
	boss.hits_this_window = 0
	for i in 900:
		if bsm.current_state.name == "Recover":
			opened = true
			break
		# Frames left of the landing: TOUCHDOWN holds until the anim is done.
		if not swung and land.phase == 2 and _land_frames_left() <= lead:
			swung = true
			tap(KEY_Q)
		place_under(boss.hurtbox)
		await physics_frame
	if not swung:
		tap(KEY_Q)
	await wait(30)
	var dealt: int = before - boss.boss_health
	boss.boss_health = boss.max_health
	boss.hits_this_window = 0
	combo.reset()
	return dealt > 0


# Physics frames left of the landing animation before Recover.
func _land_frames_left() -> int:
	var left := 0.0
	var i: int = boss.anim_step
	left += boss.anim.times[mini(i, boss.anim.times.size() - 1)] - boss.anim_clock
	i += 1
	while i < boss.anim.frames.size():
		left += boss.anim.times[mini(i, boss.anim.times.size() - 1)]
		i += 1
	return int(round(left * 60.0))


# What he throws, and how long each attack's wind-up runs, with the player parked out of reach.
func bot_census() -> void:
	player.playerHealth = 100000
	track()
	var started := clock
	var seen := {}
	var last_state := ""
	var last_at := clock
	var marks := []
	while clock - started < 120.0:
		player.global_position = Vector2(960, 640)
		var name: String = bsm.current_state.name
		var phase := -1
		var cur = bsm.current_state
		if "phase" in cur:
			phase = cur.phase
		var tag := "%s/%d" % [name, phase]
		if tag != last_state:
			if last_state != "":
				marks.append("%s %.2fs" % [last_state, clock - last_at])
				seen[last_state] = seen.get(last_state, 0) + 1
			last_state = tag
			last_at = clock
		await physics_frame
	p("state timeline: %s" % [", ".join(marks)])
	p("state counts: %s" % [seen])
	summary("census", started)
