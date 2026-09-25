extends RefCounted

# greyson_brawl (coder D): Greyson's final brawl (GreysonFinalBrawl, PLAN_BRAWL.md section 10) in his test scene,
# entered the way start_in_brawl enters it (skip_to_brawl) unless a tier says otherwise. --fixed-fps 60, the default
# keyboard bindings: the arrows slip, Shift guards. tier=
#   entry    a punch kill and a pose-finisher kill: each reaches the brawl, waits out the finisher that killed him,
#            hides his HUD and plays one cut; with his juggle on, a tiered kill too, which lands in the brawl still on
#            the juggle's lying loop, is taken over at the KO hold and gets up in the cut
#   skip     a watched cut, him teleporting home and the player walking onto the mark, against holds mid-walk,
#            mid-slam and at the toss: all land on the same cut-in
#   lock     move, dash and punch for a second leave the player where they stand; a guard press is credited
#   answers  [L,R,S] answered right (3 reads, no damage, the straight parried through the posed guard) and wrong
#            (3 hits, 3 damage, the meter back to 0); no answer is a hit at the lead; the two hedges are hits; a press
#            before the tell counts for nothing; every lead at least 0.40 and every parry inside the parry window
#   daze     6 reads start the finisher on the brawl's sheet with no node added for the meter; no presses fizzle and
#            the boxing is back within 1.2 s; a 3-bar mash leaves one uppercut
#   win      four uppercuts over two dazes: the KO, one player_won outro, Defeated on the KO's frame, the view
#            level, the player on their own sheet at (960,566)
#   loss     one miss at a half-heart: one player_lost outro; release() twice is safe, the player unlocked, no brawl
#            FX left, the heaps kept
#   normal   every tier above, in turn

const SCENE := "res://Scenes/Bosses/GreysonTestFightScene.tscn"
const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const Layout := preload("res://Scripts/GreysonBrawlLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const FightFreeze := preload("res://Scripts/FightFreeze.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const SEED := 20260924
const FRAME := 1.0 / 60.0
# Frames Escape is held for a skip: past BossEntrance.SKIP_HOLD.
const ESCAPE_HOLD := 32
const KEYS := {&"left": KEY_LEFT, &"right": KEY_RIGHT, &"guard": KEY_SHIFT}
# Where the player starts, well off the mark, and where he is put so he has to teleport home.
const START := Vector2(560, 820)
const AWAY := Vector2(420, 760)
# The seconds after a tell a clean answer comes.
const ANSWER_AT := 0.25
const TIERS := ["entry", "skip", "lock", "answers", "daze", "win", "loss"]


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	for tier in tiers:
		t.log_p("-- greyson_brawl %s" % tier)
		match tier:
			"entry":
				await tier_entry(t)
			"skip":
				await tier_skip(t)
			"lock":
				await tier_lock(t)
			"answers":
				await tier_answers(t)
			"daze":
				await tier_daze(t)
			"win":
				await tier_win(t)
			"loss":
				await tier_loss(t)
			_:
				t.check(false, "greyson_brawl has no tier %s" % tier)
		leave(t)


#GETTING THERE

# His test scene, in Idle with his attacks held off, a seeded fight, the player at `feet` with every key up.
static func open(t, feet := START) -> void:
	leave(t)
	await t.open_scene(SCENE)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.check(await t.wait_until(func(): return String(t.sm.current_state.name) == "Idle", 120), "his test scene comes up in Idle")
	t.sm.rng.seed = SEED
	t.stop_boss_timers()
	for code in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_ESCAPE, KEY_Q, KEY_W]:
		t.release(code)
	t.player.is_talking = false
	t.player.playerHealth = 100
	t.player.get_node("Hype")._set_hype(0.0)
	t.clear_iframes()
	t.player.global_position = feet
	t.player.velocity = Vector2.ZERO
	t.set_meta(&"brawl_player_z", t.player.sprite.z_index)
	await t.wait(2)


# Into the brawl the way start_in_brawl goes there, him at `his_feet` if it is given. The brawl, or null.
static func into_brawl(t, his_feet := Vector2.INF, feet := START) -> Node:
	await open(t, feet)
	if his_feet != Vector2.INF:
		t.boss.global_position = his_feet
	var brawl: Node = t.sm.states["FinalBrawl"]
	t.boss.skip_to_brawl()
	var entered: bool = await t.wait_until(func(): return t.sm.current_state == brawl, 30)
	t.check(entered, "his bar emptied, he goes into the brawl (%s)" % t.sm.current_state.name)
	return brawl if entered else null


# The cut from its start to the cut-in, Escape held from `skip_at` seconds into it, or watched through. Whether it
# reached the square-up.
static func through_cut(t, brawl: Node, skip_at := -1.0) -> bool:
	await t.wait_until(func(): return brawl.phase == brawl.Phase.CUT, 120)
	var held := -1
	for i in 900:
		if brawl.phase != brawl.Phase.CUT:
			break
		if skip_at >= 0.0 and held < 0 and brawl.phase_clock >= skip_at:
			t.press(KEY_ESCAPE)
			held = 0
		if held >= 0:
			held += 1
			if held == ESCAPE_HOLD:
				t.release(KEY_ESCAPE)
		await t.physics_frame
	if held >= 0 and held < ESCAPE_HOLD:
		t.release(KEY_ESCAPE)
	return brawl.phase == brawl.Phase.SQUARE_UP


# Into the brawl, the cut held past at once, the combos pinned, and on to its first tell.
static func to_boxing(t, combos: Array, health := 100) -> Node:
	var brawl: Node = await into_brawl(t)
	if brawl == null:
		return null
	brawl.pinned_combos = combos.duplicate(true)
	if not await through_cut(t, brawl, 0.1):
		t.check(false, "the held cut reaches the square-up (%s)" % brawl.Phase.keys()[brawl.phase])
		return null
	t.player.playerHealth = health
	t.clear_iframes()
	await t.wait_until(func(): return brawl.phase == brawl.Phase.BOXING, 120)
	return brawl


# Answers the next punches, a plan each: [answer, seconds after its tell] pressed in turn, one a frame ([] answers
# nothing). Their punch_log entries, once the last has resolved.
static func box(t, brawl: Node, plans: Array, max_frames := 1500) -> Array:
	var first: int = brawl.punch_log.size()
	var told := {}
	var pressed := {}
	for i in max_frames:
		if brawl.punch_log.size() >= first + plans.size():
			break
		if brawl.phase == brawl.Phase.BOXING and not brawl.punch.is_empty() and not brawl.punch.resolved:
			var at: float = brawl.punch.told_at
			if not told.has(at):
				told[at] = told.size()
			var index: int = told[at]
			if index < plans.size():
				var plan: Array = plans[index]
				for k in plan.size():
					var id := "%d:%d" % [index, k]
					if not pressed.has(id) and brawl.punch.clock >= plan[k][1] - 0.0001:
						pressed[id] = true
						t.tap(KEYS[plan[k][0]])
						break
		await t.physics_frame
	return brawl.punch_log.slice(first, first + plans.size())


# Each punch of `kinds` answered right, ANSWER_AT after its tell.
static func clean(kinds: Array) -> Array:
	return kinds.map(func(kind: StringName) -> Array: return [[{&"L": &"left", &"R": &"right", &"S": &"guard"}[kind], ANSWER_AT]])


# Out of whatever the last run left: its outro, a hit-stop, a freeze and the view.
static func leave(t) -> void:
	for code in [KEY_LEFT, KEY_RIGHT, KEY_SHIFT, KEY_ESCAPE, KEY_Q, KEY_W]:
		t.release(code)
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	t.paused = false
	HitStop.clear()
	FightFreeze.unfreeze(t)
	ScreenView.reset(t)


#ENTRY

static func tier_entry(t) -> void:
	for how in ["punch", "finisher"]:
		await open(t, Vector2(960, 600))
		var brawl: Node = t.sm.states["FinalBrawl"]
		t.sm.on_child_transition(t.sm.current_state, "Pose")
		await t.wait(2)
		t.stop_boss_timers()
		t.boss.boss_health = 1
		var finisher: Node = t.player.finisher
		var busy_in_ko_wait := [0, 0]
		var watch := func():
			if t.sm.current_state == brawl and brawl.phase == brawl.Phase.KO_WAIT:
				busy_in_ko_wait[0 if finisher.is_active() else 1] += 1
		t.physics_frame.connect(watch)
		if how == "punch":
			t.check(t.boss.take_punch(1) == 1, "a punch at 1 HP in his pose lands")
		else:
			t.check(finisher.begin_auto(t.boss), "the pose window's finisher starts at 1 HP")
		var entered: bool = await t.wait_until(func(): return t.sm.current_state == brawl, 240)
		var was_active: bool = finisher.is_active()
		var to_cut: bool = await t.wait_until(func(): return brawl.phase >= brawl.Phase.CUT, 400)
		t.physics_frame.disconnect(watch)
		t.check(entered and to_cut, "the %s kill reaches the brawl and its cut (%s)" % [how, brawl.Phase.keys()[brawl.phase]])
		if how == "finisher":
			t.check(was_active and busy_in_ko_wait[0] > 0 and not finisher.is_active(),
				"the brawl waits in KO_WAIT while the finisher that killed him plays out (%d frames busy, %d after)" % busy_in_ko_wait)
		t.check(is_zero_approx(t.boss.health_bar.modulate.a) and is_zero_approx(t.boss.gauge_bar.modulate.a),
			"his bar and gauge are gone by the cut (%.2f, %.2f)" % [t.boss.health_bar.modulate.a, t.boss.gauge_bar.modulate.a])
		await through_cut(t, brawl)
		await t.wait_until(func(): return brawl.phase == brawl.Phase.BOXING, 120)
		t.check(brawl.cuts == 1 and brawl.entered_count == 1, "one brawl, one cut (%d, %d)" % [brawl.entered_count, brawl.cuts])
		leave(t)
	if not t.boss.JUGGLE_ENABLED:
		t.log_p("no tiered kill: his juggle is off (GreysonScript.JUGGLE_ENABLED)")
		return
	await entry_juggle(t)


# Broken at 1 HP and juggled to 0 by the tiered finisher: he finishes his fall and his crash and lands in the brawl
# still on the juggle's own lying loop; the KO hold lets that go for his defeat's last frame; he gets up in the cut,
# and there is one cut.
static func entry_juggle(t) -> void:
	await open(t, Vector2(960, 600))
	var brawl: Node = t.sm.states["FinalBrawl"]
	var juggled: Node = t.sm.states["Juggled"]
	var finisher: Node = t.player.finisher
	t.sm.enter_broken()
	await t.wait(2)
	t.stop_boss_timers()
	t.boss.boss_health = 1
	t.check(t.sm.current_state.name == "Broken" and finisher.begin(t.boss), "Broken at 1 HP, the finisher starts")
	await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	await t.mash_tiered(5)
	var states := []
	var watch := func():
		if states.is_empty() or states[-1] != String(t.sm.current_state.name):
			states.append(String(t.sm.current_state.name))
	t.physics_frame.connect(watch)
	var entered: bool = await t.wait_until(func(): return t.sm.current_state == brawl, 400)
	var landed := {"phase": brawl.Phase.keys()[brawl.phase], "lingering": juggled.lingering, "active": finisher.is_active()}
	await t.wait_until(func(): return brawl.phase >= brawl.Phase.KO_HOLD, 60)
	var lying := {"texture": t.boss.sprite.texture.resource_path, "frame": t.boss.sprite.frame, "clip": brawl.clip_name,
		"lingering": juggled.lingering}
	await through_cut(t, brawl)
	t.physics_frame.disconnect(watch)
	t.log_p("juggled into the brawl: states %s, landed %s, at the KO hold %s, setup %.3f" % [states, landed, lying, brawl.setup_time])
	var defeat_sheet: String = load("res://Scripts/GreysonArtLayout.gd").anim(&"defeat").sheet
	t.check(entered and brawl.from_juggle and states.find("Juggled") < states.find("FinalBrawl") and not landed.active
		and landed.phase == "KO_WAIT" and landed.lingering,
		"a juggle kill finishes its fall and crash, then lands in the brawl after the finisher, still on the juggle's loop (%s)" % [states])
	t.check(lying.texture == defeat_sheet and lying.frame == 4 and lying.clip == &"lying" and not lying.lingering,
		"at the KO hold the brawl takes him over: his defeat's last frame, the juggle's loop let go")
	await t.wait_until(func(): return brawl.phase == brawl.Phase.BOXING, 120)
	t.check(brawl.setup_time >= brawl.rise_time and brawl.cuts == 1 and is_zero_approx(t.boss.health_bar.modulate.a),
		"he gets up in the cut (S %.2f), one cut, his bar gone" % brawl.setup_time)


#THE CUT AND ITS SKIP

static func tier_skip(t) -> void:
	var brawl: Node = await into_brawl(t, AWAY)
	if brawl == null:
		return
	var beats := {"teleported": false}
	var watch := func():
		if t.boss.current_anim == &"teleport_in":
			beats.teleported = true
	t.physics_frame.connect(watch)
	var reached: bool = await through_cut(t, brawl)
	t.physics_frame.disconnect(watch)
	var times: Dictionary = brawl.beat_times
	var walk := clampf(START.distance_to(Layout.PLAYER_MARK) / brawl.walk_speed, brawl.walk_min, brawl.walk_max)
	var setup := maxf(walk, brawl.teleport_time)
	t.log_p("watched: setup %.3f (walk %.3f), beats %s" % [brawl.setup_time, walk, times])
	t.check(reached and beats.teleported, "the watched cut reaches the square-up, him teleporting home on the way")
	t.check(absf(times.get(&"setup", -1.0) - setup) <= 2.0 * FRAME and absf(times.get(&"cut", -1.0) - brawl.cut_at) <= 2.0 * FRAME,
		"S is the longer of the walk and his teleport (%.3f, want %.3f), and the cut-in comes %.2f s after it (%.3f)"
		% [times.get(&"setup", -1.0), setup, brawl.cut_at, times.get(&"cut", -1.0)])
	var watched: Dictionary = await square_up_end(t, brawl)
	t.log_p("watched, at the square-up's end: %s" % [watched])
	t.check(watched.his_feet == t.sm.HOME and watched.his_visible and not watched.hurtbox and watched.his_clip == &"guard"
		and not watched.his_flip and watched.his_rotation == 0.0,
		"him: home, in his guard, never flipped, hurtbox off")
	t.check(watched.bar == 0.0 and watched.gauge == 0.0 and watched.meter == 0.0, "his bar, gauge and hype meter hidden")
	t.check(watched.heaps == brawl.rubble.slots.size() and watched.heaps > 0 and watched.falling == 0 and watched.in_clearing == 0
		and watched.over_him == 0, "every heap of the fill settled (%d), nothing falling, the clearing empty, nothing over him" % watched.heaps)
	t.check(watched.player == Layout.PLAYER_MARK and watched.locked and not watched.sealed and watched.posed
		and watched.facing_point == Layout.FACE_AT and not watched.talking and watched.player_z == Layout.PLAYER_Z
		and watched.player_texture == Layout.player_sheet().texture,
		"the player: on the mark, locked (unsealed), in the 2x guard, facing him, z %d" % Layout.PLAYER_Z)
	t.check(watched.zoom == Layout.ZOOM and watched.focus == Layout.FOCUS and watched.shake == Vector2.ZERO
		and watched.time_scale == 1.0, "the view at zoom %.1f on %s, still" % [Layout.ZOOM, Layout.FOCUS])
	t.check(not watched.cut and watched.hazards == 0 and watched.music_db == 0.0 and watched.cuts == 1,
		"the cut over, nothing in greyson_hazard, the music at its level")
	# Mid-walk, mid-slam (between slams 2 and 3) and at the toss, each from the cut's start.
	for skip_at in [0.3, setup + 1.0, setup + brawl.toss_at + 0.1]:
		brawl = await into_brawl(t, AWAY)
		if brawl == null:
			return
		var held: bool = await through_cut(t, brawl, skip_at)
		var skipped: Dictionary = await square_up_end(t, brawl)
		var diffs := diff(skipped, watched)
		t.check(held and diffs.is_empty(), "a hold %.2f s into the cut lands on the same cut-in %s" % [skip_at, diffs])


# Everything a watched cut and a held one must agree on, taken just before the first tell.
static func square_up_end(t, brawl: Node) -> Dictionary:
	await t.wait_until(func(): return brawl.phase != brawl.Phase.SQUARE_UP or brawl.phase_clock >= brawl.square_up - 0.1, 120)
	var boss: Node = t.boss
	var player: Node = t.player
	var sprite: Sprite2D = boss.sprite
	var heaps: Array = brawl.rubble.heaps.values()
	var in_clearing := 0
	var over_him := 0
	for i in brawl.rubble.slots.size():
		var slot: Dictionary = brawl.rubble.slots[i]
		if Layout.CLEARING.has_point(slot.base):
			in_clearing += 1
		if Layout.heap_rect(slot.base, slot.frame).intersects(Layout.KEEP_CLEAR):
			over_him += 1
	var heap_sum := Vector2.ZERO
	for heap in heaps:
		heap_sum += heap.global_position
	var barbell: Node2D = brawl.rubble.barbell
	return {
		"his_feet": boss.global_position, "his_texture": sprite.texture.resource_path, "his_frame": sprite.frame,
		"his_offset": sprite.offset, "his_shift": sprite.position, "his_rotation": snappedf(sprite.rotation, 0.001),
		"his_flip": sprite.flip_h, "his_visible": sprite.visible, "his_clip": brawl.clip_name,
		"hurtbox": boss.hurtbox.monitoring,
		"bar": snappedf(boss.health_bar.modulate.a, 0.01), "gauge": snappedf(boss.gauge_bar.modulate.a, 0.01),
		"meter": snappedf(boss.hype_meter.modulate.a, 0.01),
		"heaps": heaps.size(), "heap_sum": heap_sum, "falling": brawl.rubble.falling_count(),
		"in_clearing": in_clearing, "over_him": over_him,
		"barbell": barbell.global_position if is_instance_valid(barbell) else Vector2.INF,
		"barbell_turn": snappedf(barbell.rotation, 0.001) if is_instance_valid(barbell) else INF,
		"player": player.global_position, "locked": player.is_action_locked, "sealed": player.lock_seals_guard,
		"posed": player.is_posed(), "facing_point": player.facing_point, "talking": player.is_talking,
		"player_z": player.sprite.z_index, "player_texture": player.sprite.texture.resource_path,
		"player_sm": player.state_machine.is_physics_processing(),
		"zoom": snappedf(ScreenView.zoom, 0.0001), "focus": ScreenView.focus, "shake": ScreenView.shake_offset,
		"time_scale": snappedf(Engine.time_scale, 0.01), "cut": is_instance_valid(brawl.cut),
		"hazards": t.get_nodes_in_group(t.sm.HAZARD_GROUP).filter(func(h): return not h.is_queued_for_deletion()).size(),
		"music_db": snappedf(boss.music_player.volume_db - boss.music_base_db, 0.1), "cuts": brawl.cuts,
		"phase": brawl.Phase.keys()[brawl.phase],
	}


static func diff(got: Dictionary, want: Dictionary) -> Array:
	var diffs := []
	for k in want:
		if got.get(k) != want[k]:
			diffs.append("%s %s (watched %s)" % [k, got.get(k), want[k]])
	return diffs


#THE LOCK

static func tier_lock(t) -> void:
	var brawl: Node = await into_brawl(t)
	if brawl == null:
		return
	brawl.square_up = 2.5
	await through_cut(t, brawl, 0.1)
	await t.wait(2)
	var credited := [0, 0]
	var count := func(was_credited: bool): credited[0 if was_credited else 1] += 1
	t.defense.block_pressed.connect(count)
	var mark: Vector2 = t.player.global_position
	t.press(KEY_RIGHT)
	for i in 60:
		if i % 12 == 0:
			t.tap(KEY_W)
		if i % 12 == 6:
			t.tap(KEY_Q)
		await t.physics_frame
	t.release(KEY_RIGHT)
	await t.wait(2)
	var still: bool = t.player.global_position == mark
	var state := String(t.player.state_machine.current_state.name)
	t.tap(KEY_SHIFT)
	await t.wait(2)
	t.defense.block_pressed.disconnect(count)
	t.check(still and state == "Posed" and brawl.phase == brawl.Phase.SQUARE_UP,
		"a second of move, dash and punch leaves the player on their mark, posed (%s, %s)" % [t.player.global_position, state])
	t.check(credited[0] == 1 and credited[1] == 0 and t.defense.is_parry_ready(), "a guard press is credited and opens the parry window (%s)" % [credited])


#THE ANSWERS

static func tier_answers(t) -> void:
	var L := &"L"
	var R := &"R"
	var S := &"S"
	var brawl: Node = await to_boxing(t, [[L, R, S], [L, R, S], [L], [R], [S], [R]])
	if brawl == null:
		return
	var parries := [0]
	var count := func(_hit, _point, _staggered, _streak): parries[0] += 1
	t.defense.parried.connect(count)
	var health: int = t.player.playerHealth
	var right: Array = await box(t, brawl, clean([L, R, S]))
	t.log_p("right: %s" % [right])
	t.check(right.map(func(p): return p.result) == [&"dodged", &"dodged", &"parried"] and brawl.reads == 3
		and t.player.playerHealth == health and parries[0] == 1,
		"[L,R,S] answered right: slipped, slipped, parried through the posed guard; 3 reads, no damage")
	var wrong: Array = await box(t, brawl, [[[&"right", ANSWER_AT]], [[&"left", ANSWER_AT]], [[&"left", ANSWER_AT]]])
	t.log_p("wrong: %s" % [wrong])
	t.check(wrong.map(func(p): return p.result) == [&"hit", &"hit", &"hit"] and t.player.playerHealth == health - 3
		and brawl.reads == 0, "[L,R,S] answered wrong: 3 hits, 3 damage, the meter back to 0 (%d)" % brawl.reads)
	var none: Array = await box(t, brawl, [[]])
	t.check(none[0].result == &"hit" and none[0].answer == &"" and absf(none[0].resolve - none[0].lead) <= FRAME + 0.0001,
		"no answer: a hit exactly at the lead (%.4f of %.2f)" % [none[0].resolve, none[0].lead])
	var hedge_hook: Array = await box(t, brawl, [[[&"left", 0.10], [&"right", 0.12]]])
	var hedge_straight: Array = await box(t, brawl, [[[&"right", 0.10], [&"guard", 0.12]]])
	t.log_p("hedges: %s, %s" % [hedge_hook, hedge_straight])
	t.check(hedge_hook[0].result == &"hit" and hedge_hook[0].answer == &"left", "LEFT then RIGHT on a right hook is a hit")
	t.check(hedge_straight[0].result == &"hit" and hedge_straight[0].answer == &"right" and parries[0] == 1,
		"RIGHT then the guard on the straight is a hit, and no parry")
	# The right answer to the next punch, pressed in the neutral before its tell.
	await t.wait_until(func(): return brawl.punch.is_empty() or brawl.punch.resolved, 120)
	await t.wait(6)
	t.tap(KEY_RIGHT)
	var early: Array = await box(t, brawl, [[]])
	t.check(early[0].kind == R and early[0].result == &"hit" and early[0].answer == &"",
		"RIGHT pressed before the right hook's tell counts for nothing: it lands")
	t.defense.parried.disconnect(count)
	var every: Array = brawl.punch_log
	var short: Array = every.filter(func(p): return p.lead < 0.40 - 0.0001)
	var late: Array = every.filter(func(p): return p.result == &"parried" and p.resolve - p.answer_at > t.defense.parry_window)
	t.check(short.is_empty() and late.is_empty(), "every lead at least 0.40 s, every parry resolved inside the %.2f s window" % t.defense.parry_window)


#THE DAZE AND THE FINISHER

static func tier_daze(t) -> void:
	var L := &"L"
	var R := &"R"
	var brawl: Node = await to_boxing(t, [[L, R], [L, R], [L, R], [L, R], [L, R], [L, R], [L, R]])
	if brawl == null:
		return
	var finisher: Node = t.player.finisher
	var controls_before := count_controls(t)
	await box(t, brawl, clean([L, R, L, R, L]))
	var controls_at_five := count_controls(t)
	t.check(brawl.reads == 5 and controls_at_five == controls_before and brawl.phase == brawl.Phase.BOXING,
		"five reads show nowhere: no node added (%d controls, then %d), still boxing" % [controls_before, controls_at_five])
	await box(t, brawl, clean([R]))
	var dazed: bool = await t.wait_until(func(): return finisher.is_active() and finisher.phase == t.FINISHER_DAZED, 120)
	var want_texture: String = finisher.texture_path()
	t.check(dazed and brawl.phase == brawl.Phase.FINISHER and brawl.dazes == 1 and brawl.reads == 0
		and finisher.sheet_override == Layout.uppercut_sheet() and t.player.sprite.texture.resource_path == want_texture,
		"the sixth read dazes him: the finisher on the brawl's sheet (%s), the meter back to 0" % want_texture.get_file())
	# No presses: it fizzles, and the boxing comes back.
	await t.wait_until(func(): return not finisher.is_active(), 600)
	var over: float = t.boss.fight_clock
	var fizzled: bool = brawl.phase == brawl.Phase.RECOVER and brawl.cycle == 2
	await t.wait_until(func(): return brawl.phase == brawl.Phase.BOXING, 200)
	var back: float = t.boss.fight_clock - over
	t.check(fizzled and back <= 1.2 and uppercut_count(brawl) == 4 and t.player.is_posed() and t.player.is_action_locked,
		"no presses fizzle; the player is locked and posed again, and the next tell comes %.2f s later" % back)
	await box(t, brawl, clean([L, R, L, R, L, R]), 2400)
	await t.wait_until(func(): return finisher.is_active() and finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	await t.mash_tiered(5)
	await t.wait_until(func(): return not finisher.is_active(), 400)
	t.check(brawl.uppercuts_left == 1 and brawl.cycle == 3 and brawl.phase == brawl.Phase.RECOVER,
		"a 3-bar mash lands three uppercuts: one left (%d), cycle %d" % [brawl.uppercuts_left, brawl.cycle])


static func uppercut_count(brawl: Node) -> int:
	return brawl.uppercuts_left


static func count_controls(t) -> int:
	return t.current_scene.find_children("*", "Control", true, false).size()


#THE WIN

static func tier_win(t) -> void:
	var L := &"L"
	var R := &"R"
	var brawl: Node = await to_boxing(t, [[L, R], [L, R], [L, R], [L, R], [L, R], [L, R], [L, R]])
	if brawl == null:
		return
	var finisher: Node = t.player.finisher
	var outro_ids := {}
	var watch_outros := func():
		for c in t.root.get_children():
			if c.get_script() != null and str(c.get_script().resource_path).ends_with("FightOutro.gd"):
				outro_ids[c.get_instance_id()] = c
	t.physics_frame.connect(watch_outros)
	for daze in 2:
		await box(t, brawl, clean([L, R, L, R, L, R]), 2400)
		await t.wait_until(func(): return finisher.is_active() and finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
		await t.mash_tiered(5)
		await t.wait_until(func(): return not finisher.is_active() or brawl.phase >= brawl.Phase.KO_SNAP, 400)
		t.log_p("daze %d: %d uppercuts left, phase %s" % [daze + 1, brawl.uppercuts_left, brawl.Phase.keys()[brawl.phase]])
	var beaten: bool = await t.wait_until(func(): return t.sm.current_state == t.sm.states["Defeated"], 400)
	var at_hand_off := {
		"zoom": ScreenView.zoom, "canvas": t.root.canvas_transform, "player": t.player.global_position,
		"posed": t.player.is_posed(), "locked": t.player.is_action_locked, "texture": t.player.sprite.texture.resource_path,
		"z": t.player.sprite.z_index, "his_rotation": t.boss.sprite.rotation, "his_frame": t.boss.sprite.frame,
		"his_texture": t.boss.sprite.texture.resource_path,
	}
	t.log_p("at the hand-off: %s" % [at_hand_off])
	t.check(beaten and brawl.uppercuts_left == 0 and t.boss.defeated and t.sm.states["Defeated"].lying,
		"four uppercuts over two dazes knock him out: Defeated, lying")
	t.check(at_hand_off.zoom == 1.0 and at_hand_off.canvas == Transform2D.IDENTITY, "the view is level at the hand-off")
	t.check(at_hand_off.player == Layout.PLAYER_HANDOFF and not at_hand_off.posed and not at_hand_off.locked
		and at_hand_off.texture != Layout.player_sheet().texture and at_hand_off.z == t.get_meta(&"brawl_player_z"),
		"the player on their own sheet at %s, unlocked, their z back" % [Layout.PLAYER_HANDOFF])
	var ko_frame: bool
	if Layout.uses_final_sheet(&"ko"):
		ko_frame = at_hand_off.his_texture == Layout.SHEETS[&"ko"] and at_hand_off.his_frame == 4
	else:
		ko_frame = absf(at_hand_off.his_rotation - deg_to_rad(-80.0)) < 0.01
	await t.wait(t.OUTRO_WAIT_FRAMES)
	t.physics_frame.disconnect(watch_outros)
	var kept: bool = t.boss.sprite.rotation == at_hand_off.his_rotation and t.boss.sprite.frame == at_hand_off.his_frame \
		and t.boss.sprite.texture.resource_path == at_hand_off.his_texture
	t.check(ko_frame and kept, "Defeated keeps the KO's last frame through the outro")
	var outros: Array = outro_ids.values().filter(func(o): return is_instance_valid(o))
	t.check(outro_ids.size() == 1 and outros.size() == 1 and outros[0].player_won, "one outro, the player's win (%d)" % outro_ids.size())


#THE LOSS

static func tier_loss(t) -> void:
	var brawl: Node = await to_boxing(t, [[&"L"]], 1)
	if brawl == null:
		return
	var outro_ids := {}
	var watch_outros := func():
		for c in t.root.get_children():
			if c.get_script() != null and str(c.get_script().resource_path).ends_with("FightOutro.gd"):
				outro_ids[c.get_instance_id()] = c
	t.physics_frame.connect(watch_outros)
	var miss: Array = await box(t, brawl, [[]])
	# The first frame after the lethal hit, by which FightOutro has already taken the fight to Victory.
	var after_hit := {"state": String(t.sm.current_state.name), "zoom": ScreenView.zoom, "player": t.player.global_position,
		"locked": t.player.is_action_locked, "posed": t.player.is_posed(), "z": t.player.sprite.z_index}
	t.log_p("the miss: %s; the next frame: %s" % [miss, after_hit])
	t.check(miss[0].result == &"hit" and t.player.playerHealth == 0 and after_hit.zoom == 1.0
		and after_hit.player == Layout.PLAYER_HANDOFF and not after_hit.locked and not after_hit.posed
		and after_hit.z == t.get_meta(&"brawl_player_z"),
		"the last half-heart gone: the view level, the player unlocked on their own sheet in front of his boots")
	var victory: bool = await t.wait_until(func(): return t.sm.current_state == t.sm.states["Victory"], 400)
	await t.wait(t.OUTRO_WAIT_FRAMES)
	t.physics_frame.disconnect(watch_outros)
	var outros: Array = outro_ids.values().filter(func(o): return is_instance_valid(o))
	t.check(victory and outros.size() == 1 and not outros[0].player_won, "one outro, the player's loss, him in Victory (%d)" % outro_ids.size())
	brawl.release()
	brawl.release()
	await t.wait(2)
	var fx_left: Array = t.boss.fx_layer.find_children("*", "", true, false).filter(func(n): return not n.is_queued_for_deletion())
	var heaps: Array = brawl.rubble.heaps.values().filter(func(h): return is_instance_valid(h))
	t.check(not t.player.is_action_locked and fx_left.is_empty() and brawl.rubble.falling_count() == 0
		and heaps.size() == brawl.rubble.slots.size() and heaps.size() > 0,
		"release() twice is safe: the player unlocked, no brawl FX left (%d), the %d heaps kept" % [fx_left.size(), heaps.size()])
