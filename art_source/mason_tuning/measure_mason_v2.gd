extends SceneTree

# What Mason's fight is worth against the V2 player (PlayerFeel/feel_v2): how many cycles it takes,
# what each eat window is worth, and how much hype a run banks. No window needed:
#   Godot.exe --headless --fixed-fps 60 --script res://art_source/mason_tuning/measure_mason_v2.gd -- run=<name>
# Runs: plain (punch every eat window on the beat, never guard), parry (the same, plus a guard press
# timed onto every elbow drop and nugget that reaches the player), sloppy (punches off the beat, so no
# charged third and no finisher), ceiling (parry, with the bombs and nuggets deleted so the elbow
# drops alone say what the parry economy is worth), super (plain, with the meter filled for free just
# before each daze, to see what a supercharged uppercut is worth here), gate (how long before the eat
# window opens a punch can be thrown and still land), dodge (dash out of whatever is about to land,
# rather than guard). `finisher=0` skips the mash, `v1` puts the player back on the old feel for an
# A/B.
# One run needs a real window rather than --headless, and writes its frames to out=<dir>:
#   Godot.exe --fixed-fps 60 --resolution 960x540 --position 100,100 \
#     --script res://art_source/mason_tuning/measure_mason_v2.gd -- run=shot out=<dir>

const FIGHT := "res://Scenes/Bosses/MasonBossFightScene.tscn"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const BOSS_PATH := "Arena/MasonScene/MasonCharacterBody"

const KEY_PUNCH := KEY_Q
const MASH_KEYS := {&"punch": KEY_Q, &"dodge": KEY_W, &"mash_left": KEY_LEFT, &"mash_right": KEY_RIGHT}

# Where the bot stands to punch: under Mason's hurtbox, inside the v2 up-punch box.
const PUNCH_OFFSET := Vector2(0, 135)
# Where it waits out the rest of the cycle: a corner, so only the aimed attacks come to it.
const PARK := Vector2(300, 860)

# The guard goes up this long before a hit lands, inside PlayerDefense.parry_window (0.24), and stays
# up this long after it.
const PARRY_LEAD := 0.12
const GUARD_HOLD := 0.30
# PlayerDefense.parry_mash_lockout: a press any sooner than this gets no parry credit.
const PRESS_GAP := 0.55

# PooBombScript: the explode animation switches the hitbox on 0.1 s in.
const BOMB_HIT_AFTER_DETONATE := 0.1
const BOMB_RADIUS := 60.0
# CarterElbowDropScript.DIVE_START_POSITION.length(), for reading how far through a dive it is.
const DIVE_START := Vector2(420, -1000)

var run := "plain"
var do_finisher := true
var feel_v1 := false
var out_dir := "."
var limit := 300.0

var scene: Node
var player: Node
var boss: Node
var sm: Node
var defense: Node
var hype: Node
var combo: Node
var finisher: Node

var clock := 0.0
var started := false
var done := false

# Per eat window: when it opened, the punches that landed, the damage, and the hype either side.
var windows: Array = []
var window_open := false
var window_hits := 0
var window_damage := 0
var boss_health_at_open := 0
var hype_at_open := 0.0
var window_opened := 0.0
var punch_times: Array = []

var hype_peak := 0.0
var hype_at_daze: Array[float] = []
var supercharged_dazes := 0
var finisher_damage: Array[int] = []
var parries: Array = []
var hits_taken: Array = []
var dazes := 0
var hype_spends := 0
# The Break gauge: each Break with the cycle it landed on, and every uppercut a juggle dealt.
var breaks: Array = []
var juggle_hits: Array = []
var peak_tells := 0
var peak_tells_at := 0.0
var tell_frames := 0
var tell_frames_any := 0
var cycles_seen := 0
var last_state := ""

const DODGE_LEAD := 0.22

var dash_key := 0
var dash_holding := 0.0
var dashes := 0
var guard_down_at := -1.0
var last_press := -INF
var seen: Dictionary = {}


func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("run="):
			run = arg.substr(4)
		elif arg.begins_with("finisher="):
			do_finisher = arg.substr(9) != "0"
		elif arg.begins_with("seconds="):
			limit = float(arg.substr(8))
		elif arg == "v1":
			feel_v1 = true
		elif arg.begins_with("out="):
			out_dir = arg.substr(4)
	scene = load(FIGHT).instantiate()
	root.add_child(scene)
	current_scene = scene
	player = scene.get_node(PLAYER_PATH)
	boss = scene.get_node(BOSS_PATH)
	sm = boss.get_node("StateManager")
	defense = player.get_node("Defense")
	hype = player.get_node("Hype")
	combo = player.get_node("Combo")
	finisher = player.get_node("Finisher")
	_main.call_deferred()


func _process(delta: float) -> bool:
	if started and not done:
		clock += delta
	return false


func wait(n: int) -> void:
	for i in n:
		await physics_frame


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


func _main() -> void:
	await wait(4)
	player.is_talking = false
	player.playerHealth = 1000
	if feel_v1:
		player.feel_v2 = false
	finisher.min_press_interval = 0.0
	defense.parried.connect(func(hit, _point, _staggered, streak):
		parries.append({"t": clock, "id": hit.attack_id, "streak": streak, "hype": hype.hype}))
	defense.hit_taken.connect(func(hit): hits_taken.append({"t": clock, "id": hit.attack_id}))
	hype.hype_spent.connect(func(): hype_spends += 1)
	if boss.break_gauge:
		boss.break_gauge.broke.connect(func(): breaks.append({"t": clock, "cycle": sm.cycles_started}))
	finisher.juggle_hit.connect(func(index, _last): juggle_hits.append({"index": index, "dealt": health_at_juggle[0] - boss.boss_health}))
	finisher.juggle_hit.connect(func(_index, _last): health_at_juggle[0] = boss.boss_health)
	combo.punch_landed.connect(func(_target, dealt, _charged):
		window_hits += 1
		window_damage += dealt
		punch_times.append(clock - window_opened))
	started = true
	if run == "shot":
		await _shoot_tells()
		quit(0)
		return
	if run == "gate":
		await _test_gate()
		quit(0)
		return
	sm.start_cycle()
	while not done and clock < limit:
		await physics_frame
		_tick(1.0 / 60.0)
		if boss.defeated:
			done = true
	_report()
	quit(0)


# A punch thrown before the eat window opens. feel_v2 resolves it at full extension and then retries
# every frame until the swing ends, so a window that opens inside that stretch still takes the hit;
# one that opens after it leaves the swing to whiff and PlayerCombo.end_swing() to break the combo.
func _test_gate() -> void:
	print("== mason %s, punching before the eat window opens" % ["v1 feel" if feel_v1 else "v2"])
	for lead in range(16, 26):
		boss.boss_health = boss.max_health
		boss.hits_this_window = 0
		combo.reset()
		sm.on_child_transition(sm.current_state, "Idle")
		await wait(8)
		player.global_position = boss.global_position + PUNCH_OFFSET
		player.velocity = Vector2.ZERO
		await wait(2)
		var before: int = boss.boss_health
		tap(KEY_PUNCH)
		for i in lead:
			await physics_frame
			player.global_position = boss.global_position + PUNCH_OFFSET
		sm.on_child_transition(sm.current_state, "Eat")
		for i in 40:
			await physics_frame
			player.global_position = boss.global_position + PUNCH_OFFSET
		var landed: bool = boss.boss_health < before
		print("  window opens %d frames (%.2f s) after the press: %s" % [
			lead, lead / 60.0, "lands" if landed else "whiffs, combo %d" % combo.count])
		sm.eat_timer.stop()


# A window is needed for this one. Stands the player in the middle of a line and saves the frame a
# badge is up on the blast that has them in it.
func _shoot_tells() -> void:
	player.is_invincible = true
	for node in scene.get_children():
		if "Balloon" in node.name:
			node.queue_free()
	sm.start_cycle()
	var shots := 0
	for i in 3000:
		await physics_frame
		player.global_position = Vector2(960, 640)
		player.velocity = Vector2.ZERO
		var showing := false
		for child in scene.get_children():
			if child.name.begins_with("ParryTell") and not child.name.ends_with("Spent"):
				showing = true
		if not showing:
			continue
		var path := "%s/mason_poo_tell_%d.png" % [out_dir, shots]
		RenderingServer.frame_post_draw.connect(func() -> void:
			root.get_texture().get_image().save_png(path), CONNECT_ONE_SHOT)
		shots += 1
		print("  shot %s" % path)
		if shots >= 4:
			return
		await wait(45)


func _tick(delta: float) -> void:
	hype_peak = maxf(hype_peak, hype.hype)
	var tells := 0
	for child in scene.get_children():
		if child.name.begins_with("ParryTell") and not child.name.ends_with("Spent"):
			tells += 1
	if tells > peak_tells:
		peak_tells = tells
		peak_tells_at = clock
	tell_frames += tells
	if tells > 0:
		tell_frames_any += 1
	if run == "ceiling":
		for hazard in get_nodes_in_group("mason_hazard"):
			if hazard.name.begins_with("PooBomb") or hazard.name.begins_with("NuggetMeteor"):
				hazard.queue_free()
	if run == "super" and sm.current_state.name == "Eat" and finisher.phase == 0:
		hype._set_hype(hype.max_hype)
	var state: String = sm.current_state.name
	if state != last_state:
		if state == "PooSquat" and last_state != "Waddle":
			cycles_seen += 1
		last_state = state
	_track_window(state)
	_track_finisher()
	# The finisher leaves the player where the charged punch landed: nothing moves them through it.
	if finisher.phase != 0:
		if finisher.phase == 2 or finisher.phase == 3:
			_mash()
		return
	if state == "Eat" or state == "Broken":
		_punch()
		return
	if run != "dodge":
		player.global_position = PARK
		player.velocity = Vector2.ZERO
	if run == "parry" or run == "ceiling":
		_guard()
	elif run == "dodge":
		_dodge(delta)


func _track_window(state: String) -> void:
	var open := state == "Eat"
	if open and not window_open:
		window_open = true
		window_hits = 0
		window_damage = 0
		window_opened = clock
		punch_times.clear()
		boss_health_at_open = boss.boss_health
		hype_at_open = hype.hype
	elif not open and window_open:
		window_open = false
		windows.append({
			"health": boss_health_at_open,
			"hits": window_hits,
			"damage": window_damage,
			"hype_in": hype_at_open,
			"hype_out": hype.hype,
			"at": punch_times.duplicate(),
			"length": clock - window_opened,
		})


# On the beat: the next press goes in the frame the combo window opens, which is the whole point of
# the 0.25 s window. `sloppy` presses as fast as it can instead, which the window never credits.
func _punch() -> void:
	player.global_position = boss.global_position + PUNCH_OFFSET
	player.velocity = Vector2.ZERO
	_lower_guard()
	if player.state_machine.current_state.name == "Punching":
		return
	if run == "sloppy":
		tap(KEY_PUNCH)
		return
	if combo.count == 0 or combo.window_open:
		tap(KEY_PUNCH)


var mash_step := 0
var last_phase := 0
var health_at_daze := 0
# Boxed so the juggle_hit handlers above can share it.
var health_at_juggle := [0]


func _track_finisher() -> void:
	if finisher.phase == last_phase:
		return
	print("    [%.2f] finisher phase %d -> %d, mason %d, hype %.0f, meter %.2f" % [
		clock, last_phase, finisher.phase, boss.boss_health, hype.hype, finisher.meter])
	if last_phase == 0 and finisher.phase != 0:
		dazes += 1
		mash_step = 0
		health_at_daze = boss.boss_health
		health_at_juggle[0] = boss.boss_health
		hype_at_daze.append(hype.hype)
	if finisher.phase == 2 and finisher.supercharged:
		supercharged_dazes += 1
	if finisher.phase == 0 and last_phase != 0:
		finisher_damage.append(health_at_daze - boss.boss_health)
	last_phase = finisher.phase


func _mash() -> void:
	if not do_finisher:
		return
	mash_step += 1
	if mash_step % 4 != 0:
		return
	var pair: Array = finisher.mash_actions()
	tap(MASH_KEYS[pair[(mash_step / 4) % 2]])


func _lower_guard() -> void:
	if guard_down_at >= 0.0:
		release(KEY_SHIFT)
		guard_down_at = -1.0


# Dashes out of anything about to land on the player, to say what the reworked dash is worth here.
# Arrow held from a frame before the dash key so InputSettings.move_vector() has it at kick-off, and
# through the dash, which is where PlayerScript reads the direction.
func _dodge(delta: float) -> void:
	if dash_holding > 0.0:
		dash_holding -= delta
		if dash_holding <= 0.0:
			release(dash_key)
			dash_key = 0
		return
	var soonest := INF
	var from := Vector2.ZERO
	for hazard in get_nodes_in_group("mason_hazard"):
		var left := _time_to_hit(hazard)
		if left >= 0.0 and left < soonest:
			soonest = left
			from = hazard.global_position
	if soonest > DODGE_LEAD:
		return
	var away: Vector2 = player.global_position - from
	# Along the arena's long axis unless the threat is squarely beside the player, and never into a wall.
	var toward := KEY_RIGHT if away.x >= 0.0 else KEY_LEFT
	if player.global_position.x < 400.0:
		toward = KEY_RIGHT
	elif player.global_position.x > 1520.0:
		toward = KEY_LEFT
	dash_key = toward
	press(dash_key)
	dashes += 1
	dash_holding = 0.25
	_dash_soon.call_deferred()


func _dash_soon() -> void:
	tap(KEY_W)


# One guard press per threat, timed so the hit lands inside the parry window.
func _guard() -> void:
	if guard_down_at >= 0.0:
		if clock >= guard_down_at:
			release(KEY_SHIFT)
			guard_down_at = -1.0
		return
	if clock - last_press < PRESS_GAP:
		return
	var soonest := INF
	for hazard in get_nodes_in_group("mason_hazard"):
		var left := _time_to_hit(hazard)
		if left >= 0.0:
			soonest = minf(soonest, left)
	if soonest <= PARRY_LEAD:
		press(KEY_SHIFT)
		last_press = clock
		guard_down_at = clock + GUARD_HOLD


# Seconds until this hazard's hitbox covers the player, or -1 if it never will.
func _time_to_hit(hazard: Node) -> float:
	var id := hazard.get_instance_id()
	if hazard.name.begins_with("CarterElbowDrop"):
		if not hazard.carter_sprite.visible or hazard.carter_sprite.position == Vector2.ZERO:
			return -1.0
		if not _oval_covers(hazard.global_position, hazard.hit_size()):
			return -1.0
		# The dive eases in quadratically from DIVE_START_POSITION to zero.
		var progress := sqrt(clampf(1.0 - hazard.carter_sprite.position.length() / DIVE_START.length(), 0.0, 1.0))
		return hazard.dive_time * (1.0 - progress)
	if hazard.name.begins_with("NuggetMeteor"):
		if not seen.has(id):
			seen[id] = clock + sm.nugget_warning[sm.cycle_phase]
		if not _oval_covers(hazard.global_position, hazard.HIT_SIZE):
			return -1.0
		return seen[id] - clock
	if hazard.name.begins_with("PooBomb"):
		if not _oval_covers(hazard.global_position, Vector2.ONE * BOMB_RADIUS * 2.0):
			return -1.0
		if hazard.detonate_timer.time_left > 0.0:
			return hazard.detonate_timer.time_left + BOMB_HIT_AFTER_DETONATE
		if hazard.animation_player.assigned_animation == "explode":
			return BOMB_HIT_AFTER_DETONATE - hazard.animation_player.current_animation_position
		return -1.0
	return -1.0


func _oval_covers(centre: Vector2, size: Vector2) -> bool:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return ((centre.clamp(box.position, box.end) - centre) / (size / 2.0)).length() < 1.0


func _report() -> void:
	print("== mason %s, run=%s finisher=%s" % ["v1 feel" if feel_v1 else "v2", run, do_finisher])
	print("  fight ended at %.1f s, mason %d/%d, defeated %s, cycles started %d" % [
		clock, boss.boss_health, boss.max_health, boss.defeated, sm.cycles_started])
	for i in windows.size():
		var w: Dictionary = windows[i]
		print("  eat window %d: mason %d, %d punches for %d at %s of %.2f s, hype %.0f -> %.0f" % [
			i + 1, w.health, w.hits, w.damage,
			w.at.map(func(t): return "%.2f" % t), w.length, w.hype_in, w.hype_out])
	print("  dazes %d, hype at each %s, supercharged %d, hype spent %d, uppercut dealt %s" % [
		dazes, hype_at_daze, supercharged_dazes, hype_spends, finisher_damage])
	if boss.break_gauge:
		print("  break gauge ended at %.0f of %.0f, locked %s" % [
			boss.break_gauge.value, boss.break_gauge.max_value, boss.break_gauge.locked])
	print("  breaks %d on cycles %s, %.2f cycles a break" % [
		breaks.size(), breaks.map(func(b): return b.cycle),
		float(sm.cycles_started) / maxf(breaks.size(), 1.0)])
	print("  juggle uppercuts %s, any dealing 0: %s" % [
		juggle_hits.map(func(h): return h.dealt), juggle_hits.any(func(h): return h.dealt == 0)])
	var tiers := {}
	var paid := 0.0
	var was := 0.0
	for p in parries:
		var tier: int = mini(p.streak, 3)
		tiers[tier] = tiers.get(tier, 0) + 1
		paid += maxf(p.hype - was, 0.0)
		was = p.hype
	print("  parries %d %s" % [parries.size(), parries.map(func(p): return "%s streak %d -> hype %.0f" % [p.id, p.streak, p.hype])])
	print("  parry tiers (1/2/3+) %s, paid %.0f hype in all" % [tiers, paid])
	var by_id := {}
	for h in hits_taken:
		by_id[h.id] = by_id.get(h.id, 0) + 1
	print("  hits taken %d %s, dashes %d" % [hits_taken.size(), by_id, dashes])
	print("  parry tells: at most %d at once (%.1f s), %.1f on average while any is up, up on %.0f%% of frames" % [
		peak_tells, peak_tells_at,
		float(tell_frames) / maxi(tell_frames_any, 1), 100.0 * tell_frames_any / maxf(clock * 60.0, 1.0)])
	print("  hype: peak %.0f, end %.0f, full ever %s" % [hype_peak, hype.hype, hype_peak >= hype.max_hype])
