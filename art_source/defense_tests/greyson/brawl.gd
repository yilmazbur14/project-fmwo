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
#            (3 hits, the catalog's damage for each - the straight's a whole heart - and the meter back to 0); no answer
#            is a hit at the lead; the two hedges are hits; a press before the tell counts for nothing; every lead at
#            least LEAD_FLOOR and every parry inside the parry window
#   daze     daze_reads reads start the finisher on the brawl's sheet with no node added for the meter, and one fewer
#            doesn't; no presses fizzle and the boxing is back within 1.2 s; the mash's uppercuts come off his count
#   win      uppercuts_to_kill at the strongest mash there is - three bars, every read a slip, so the hype meter is
#            full at every daze (4 + 4) - still takes two dazes and MIN_BOXED_READS reads of boxing: the KO, one
#            player_won outro, Defeated on the KO's frame, the view level, the player on their own sheet at (960,566)
#   loss     one miss at a half-heart: one player_lost outro; release() twice is safe, the player unlocked, no brawl
#            FX left, the heaps kept
#   feint    (coder A) the feint's tell is what the straight's has and it lacks: no red badge, no parry sting, and his
#            cannon arm cocked on the straight sheet's uncharged frame rather than the charged wind-up. Let go, it
#            drops at the lead: no hit, no read, back into his guard. Guarded, it is bitten: no parry, the press's
#            whiff paid (PlayerDefense.parry_whiff_cost), his counter-jab feint_counter after the press for the
#            catalog's heart and a half and a read, and the straight after it still parried (its tell rearms the parry). Slipped,
#            nothing.
#   pace     the tiers: four, lead, gap and breath each shorter than the tier before, the lead never under
#            LEAD_FLOOR; no feint in the openers, none ending a combo, never two in a row; after feint_drought
#            punches without one, every tier's next pick has one; a fourth-cycle tell on the fourth tier's lead, and
#            the next one its gap after.
#   bots     (the user, 2026-09-27: "the punch out part should be longer, too easy right now, maybe faster as well
#            and add a feint to the parry attack") BOTS through the whole brawl from the cut-in, at full health, on
#            each of BOT_SEEDS, each answering its reaction time after a tell and mashing each daze like the win tier:
#            a skilled one that reads every punch and lets every feint go wins, at 0.26 s and at 0.33 s; one that
#            guards every straight-shaped wind-up, feints included, loses; one that never guards loses. Logged: the
#            outcome, the seconds from the first tell, the punches and feints, the bites, the hits, the damage, the
#            stamina left, the dazes and each one's uppercuts, the last tier, and the longest run of punches without
#            a feint once the openers are over.
#   framing  (the user, 2026-10-04: "after some time, the camera will zoom out") a whole brawl to the KO by a bot that
#            reads every punch, parrying the straights in a streak (the parry's punch-in, from the third, eased the view
#            back to 1, the whole arena), mashing its first daze too slowly to bank a bar (the fizzle's zoom back) and the
#            rest at two bars (the juggle's): the view never drawn further out than the brawl's framing from the cut-in
#            to the KO's hand-off, and level again there with ScreenView's floor gone
#   normal   every tier above, in turn

const SCENE := "res://Scenes/Bosses/GreysonTestFightScene.tscn"
const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const Layout := preload("res://Scripts/GreysonBrawlLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const FightFreeze := preload("res://Scripts/FightFreeze.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
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
# The house's floor for a read, which no tell may go under.
const LEAD_FLOOR := 0.36
# The bots: how each answers, and what it should come to.
const BOTS := {
	"skilled": {"straights": true, "feints": false, "reaction": 0.26, "want": "won"},
	"skilled_slower": {"straights": true, "feints": false, "reaction": 0.33, "want": "won"},
	"guards_every_windup": {"straights": true, "feints": true, "reaction": 0.26, "want": "lost"},
	"never_guards": {"straights": false, "feints": false, "reaction": 0.26, "want": "lost"},
}
const BOT_SEEDS := [20260927, 7, 11]
# The player's full health, half-hearts.
const BOT_HEALTH := 6
# [L, R] combos the daze and win tiers pin: eight dazes' worth at up to 16 reads each.
const PINNED_PAIRS := 64
# However strong the mash, the boxing before the KO: four of the brawl's old six-read dazes (tuning, 2026-10-04).
const MIN_BOXED_READS := 24
# The framing tier's mashes, a press every this many frames: 3 a second banks nothing, 8.57 banks two bars.
const FIZZLE_MASH_EVERY := 20
const MODEL_MASH_EVERY := 7
# Picks per tier, each way, for the pace tier's drought check.
const DROUGHT_DRAWS := 40
const TIERS := ["entry", "skip", "lock", "answers", "daze", "win", "loss", "feint", "pace", "bots", "framing"]


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
			"feint":
				await tier_feint(t)
			"pace":
				await tier_pace(t)
			"bots":
				await tier_bots(t)
			"framing":
				await tier_framing(t)
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


# Each punch of `kinds` answered right, ANSWER_AT after its tell: a feint by letting it go.
static func clean(kinds: Array) -> Array:
	return kinds.map(func(kind: StringName) -> Array:
		return [] if kind == &"F" else [[{&"L": &"left", &"R": &"right", &"S": &"guard"}[kind], ANSWER_AT]])


static func damage_of(id: StringName) -> int:
	return AttackCatalog.get_attack(id).damage


# `pairs` [L, R] combos to pin: enough for every daze the win tier can take at the brawl's daze_reads.
static func hooks(pairs: int) -> Array:
	var combos: Array = []
	for i in pairs:
		combos.append([&"L", &"R"])
	return combos


# The first `count` punches of pinned [L, R] combos from a combo's start: L, R, L, R...
static func alternating(count: int) -> Array:
	var kinds: Array = []
	for i in count:
		kinds.append(&"L" if i % 2 == 0 else &"R")
	return kinds


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
	var wrong_damage: int = damage_of(&"greyson_brawl_hook_l") + damage_of(&"greyson_brawl_hook_r") + damage_of(&"greyson_brawl_straight_unguarded")
	t.check(wrong.map(func(p): return p.result) == [&"hit", &"hit", &"hit"] and t.player.playerHealth == health - wrong_damage
		and brawl.reads == 0, "[L,R,S] answered wrong: 3 hits, %d damage (the straight the heavy one), the meter back to 0 (%d)" % [wrong_damage, brawl.reads])
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
	var short: Array = every.filter(func(p): return p.lead < LEAD_FLOOR - 0.0001)
	var late: Array = every.filter(func(p): return p.result == &"parried" and p.resolve - p.answer_at > t.defense.parry_window)
	t.check(short.is_empty() and late.is_empty(), "every lead at least %.2f s, every parry resolved inside the %.2f s window" % [LEAD_FLOOR, t.defense.parry_window])


#THE DAZE AND THE FINISHER

static func tier_daze(t) -> void:
	var L := &"L"
	var R := &"R"
	var brawl: Node = await to_boxing(t, hooks(PINNED_PAIRS))
	if brawl == null:
		return
	var n: int = brawl.daze_reads
	var finisher: Node = t.player.finisher
	var controls_before := count_controls(t)
	await box(t, brawl, clean(alternating(n - 1)), 60 * 40)
	var controls_short := count_controls(t)
	t.check(brawl.reads == n - 1 and controls_short == controls_before and brawl.phase == brawl.Phase.BOXING,
		"%d reads show nowhere: no node added (%d controls, then %d), still boxing" % [n - 1, controls_before, controls_short])
	await box(t, brawl, clean([alternating(n)[n - 1]]))
	var dazed: bool = await t.wait_until(func(): return finisher.is_active() and finisher.phase == t.FINISHER_DAZED, 120)
	var want_texture: String = finisher.texture_path()
	t.check(dazed and brawl.phase == brawl.Phase.FINISHER and brawl.dazes == 1 and brawl.reads == 0
		and finisher.sheet_override == Layout.uppercut_sheet() and t.player.sprite.texture.resource_path == want_texture,
		"read %d (daze_reads) dazes him: the finisher on the brawl's sheet (%s), the meter back to 0" % [n, want_texture.get_file()])
	# No presses: it fizzles, and the boxing comes back.
	await t.wait_until(func(): return not finisher.is_active(), 600)
	var over: float = t.boss.fight_clock
	var fizzled: bool = brawl.phase == brawl.Phase.RECOVER and brawl.cycle == 2
	await t.wait_until(func(): return brawl.phase == brawl.Phase.BOXING, 200)
	var back: float = t.boss.fight_clock - over
	t.check(fizzled and back <= 1.2 and uppercut_count(brawl) == brawl.uppercuts_to_kill and t.player.is_posed() and t.player.is_action_locked,
		"no presses fizzle; the player is locked and posed again, and the next tell comes %.2f s later" % back)
	await box(t, brawl, clean(alternating(n)), 60 * 40)
	await t.wait_until(func(): return finisher.is_active() and finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	await t.mash_tiered(5)
	await t.wait_until(func(): return not finisher.is_active(), 400)
	var landed: int = brawl.uppercuts_to_kill - brawl.uppercuts_left
	t.check(landed >= 1 and brawl.uppercuts_left > 0 and brawl.cycle == 3 and brawl.phase == brawl.Phase.RECOVER,
		"the mash's %d uppercuts come off his %d: %d left, cycle %d" % [landed, brawl.uppercuts_to_kill, brawl.uppercuts_left, brawl.cycle])


static func uppercut_count(brawl: Node) -> int:
	return brawl.uppercuts_left


static func count_controls(t) -> int:
	return t.current_scene.find_children("*", "Control", true, false).size()


#THE WIN

static func tier_win(t) -> void:
	var brawl: Node = await to_boxing(t, hooks(PINNED_PAIRS))
	if brawl == null:
		return
	var finisher: Node = t.player.finisher
	var outro_ids := {}
	var watch_outros := func():
		for c in t.root.get_children():
			if c.get_script() != null and str(c.get_script().resource_path).ends_with("FightOutro.gd"):
				outro_ids[c.get_instance_id()] = c
	t.physics_frame.connect(watch_outros)
	var dazes := 0
	while brawl.uppercuts_left > 0 and dazes < 8:
		await box(t, brawl, clean(alternating(brawl.daze_reads)), 60 * 40)
		await t.wait_until(func(): return finisher.is_active() and finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
		await t.mash_tiered(5)
		await t.wait_until(func(): return not finisher.is_active() or brawl.phase >= brawl.Phase.KO_SNAP, 400)
		dazes += 1
		t.log_p("daze %d: %d uppercuts left, phase %s" % [dazes, brawl.uppercuts_left, brawl.Phase.keys()[brawl.phase]])
	var beaten: bool = await t.wait_until(func(): return t.sm.current_state == t.sm.states["Defeated"], 400)
	var at_hand_off := {
		"zoom": ScreenView.zoom, "canvas": t.root.canvas_transform, "player": t.player.global_position,
		"posed": t.player.is_posed(), "locked": t.player.is_action_locked, "texture": t.player.sprite.texture.resource_path,
		"z": t.player.sprite.z_index, "his_rotation": t.boss.sprite.rotation, "his_frame": t.boss.sprite.frame,
		"his_texture": t.boss.sprite.texture.resource_path,
	}
	t.log_p("at the hand-off: %s" % [at_hand_off])
	t.check(beaten and brawl.uppercuts_left == 0 and t.boss.defeated and t.sm.states["Defeated"].lying and dazes >= 2
		and dazes * brawl.daze_reads >= MIN_BOXED_READS,
		"%d uppercuts over %d dazes (%d reads boxed, at least %d) knock him out: Defeated, lying"
		% [brawl.uppercuts_to_kill, dazes, dazes * brawl.daze_reads, MIN_BOXED_READS])
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


#THE FEINT

static func tier_feint(t) -> void:
	var L := &"L"
	var R := &"R"
	var S := &"S"
	var F := &"F"
	var brawl: Node = await to_boxing(t, [[F, L], [F, S], [F, R], [L, F, S]])
	if brawl == null:
		return
	# A sting started is a voice going from quiet to playing, or starting over.
	var sting: Array = t.boss.sfx_players.get(&"brawl_tell_parry", [])
	var heard := {}
	var tells := {"badge": false, "sting": false, "clips": {}, "frames": {}, "sheets": {}}
	var watch := func():
		var started := false
		for voice in sting:
			var at: float = voice.get_playback_position() if voice.playing else -1.0
			var before: float = heard.get(voice.get_instance_id(), -1.0)
			started = started or (at >= 0.0 and (before < 0.0 or at < before))
			heard[voice.get_instance_id()] = at
		if brawl.punch.is_empty() or brawl.punch.resolved or brawl.punch.kind != F:
			return
		tells.badge = tells.badge or t.live_tells().any(func(tell): return tell.name == "ParryTell%d" % t.boss.get_instance_id())
		tells.sting = tells.sting or started
		tells.clips[brawl.clip_name] = true
		tells.frames[t.boss.sprite.frame] = true
		tells.sheets[t.boss.sprite.texture.resource_path.get_file()] = true
	t.physics_frame.connect(watch)
	var parries := [0]
	var count := func(_hit, _point, _staggered, _streak): parries[0] += 1
	t.defense.parried.connect(count)
	var health: int = t.player.playerHealth

	# Let go, then the left hook after it.
	var held: Array = await box(t, brawl, [[], [[&"left", ANSWER_AT]]])
	var after_held := {"health": t.player.playerHealth, "reads": brawl.reads, "clip": brawl.clip_name}
	t.log_p("let go: %s; then %s" % [held, after_held])
	t.check(held[0].kind == F and held[0].result == &"held" and held[0].answer == &"" and held[0].damage == 0
		and absf(held[0].resolve - held[0].lead) <= FRAME + 0.0001,
		"a feint let go drops at the lead (%.3f of %.2f), no hit" % [held[0].resolve, held[0].lead])
	t.check(held[1].result == &"dodged" and after_held.health == health and after_held.reads == 1,
		"no read for it: the hook after it is the only read (%d)" % after_held.reads)

	# Guarded - bitten - then the real straight after it.
	var stamina_before: float = t.defense.stamina
	var bitten: Array = await box(t, brawl, [[[&"guard", ANSWER_AT]]])
	await t.wait(2)
	var stamina_after: float = t.defense.stamina
	var straight: Array = await box(t, brawl, [[[&"guard", ANSWER_AT]]])
	t.log_p("bitten: %s, stamina %.1f -> %.1f; then %s" % [bitten, stamina_before, stamina_after, straight])
	t.check(bitten[0].kind == F and bitten[0].result == &"countered" and bitten[0].damage == damage_of(&"greyson_brawl_counter")
		and absf(bitten[0].resolve - bitten[0].answer_at - brawl.feint_counter) <= FRAME + 0.0001,
		"a feint guarded is bitten: his counter-jab %.2f s after the press (%.3f) for its %d half-hearts (%d)"
		% [brawl.feint_counter, bitten[0].resolve - bitten[0].answer_at, damage_of(&"greyson_brawl_counter"), bitten[0].damage])
	t.check(is_equal_approx(stamina_before - stamina_after, t.defense.parry_whiff_cost),
		"and the press's whiff is paid: %.1f of the bar (PlayerDefense.parry_whiff_cost %.1f)"
		% [stamina_before - stamina_after, t.defense.parry_whiff_cost])
	t.check(parries[0] == 1 and straight[0].kind == S and straight[0].result == &"parried",
		"the press parried nothing, and the straight after it is still parried (parries %d, %s)" % [parries[0], straight[0].result])
	t.check(brawl.reads == 1, "the bite cost a read and the straight made it back (%d)" % brawl.reads)

	# Slipped: nothing.
	var health_before_slip: int = t.player.playerHealth
	var reads_before_slip: int = brawl.reads
	var slipped: Array = await box(t, brawl, [[[&"left", ANSWER_AT]], [[&"right", ANSWER_AT]]])
	t.log_p("slipped: %s" % [slipped])
	t.check(slipped[0].result == &"slipped" and slipped[0].damage == 0 and t.player.playerHealth == health_before_slip
		and brawl.reads == reads_before_slip + 1, "a feint slipped: nothing lands and nothing is read; the hook after it is")
	var clean_run: Array = await box(t, brawl, clean([L, F, S]))
	t.check(clean_run.map(func(p): return p.result) == [&"dodged", &"held", &"parried"], "[L,F,S] read right: slipped, let go, parried (%s)"
		% [clean_run.map(func(p): return p.result)])
	t.physics_frame.disconnect(watch)
	t.defense.parried.disconnect(count)
	var windup: Dictionary = Layout.clip(&"straight_windup")
	var feint: Dictionary = Layout.clip(&"feint_windup")
	t.log_p("the feint's tells: %s; the straight's wind-up is %s f%s, the feint's %s f%s" % [tells, windup.texture.get_file(), windup.frames, feint.texture.get_file(), feint.frames])
	t.check(not tells.badge and not tells.sting, "no red badge and no parry sting over any feint")
	t.check(tells.clips.keys() == [&"feint_windup"] and feint.frames != windup.frames and tells.frames.keys() == feint.frames,
		"its wind-up is the straight sheet's uncharged frame %s, not the charged %s" % [feint.frames, windup.frames])


#THE PACE

static func tier_pace(t) -> void:
	var brawl: Node = await into_brawl(t)
	if brawl == null:
		return
	var tiers: int = brawl.lead_times.size()
	var stepping: bool = tiers == 4 and brawl.gap_times.size() == tiers and brawl.neutral_times.size() == tiers \
		and brawl.PATTERNS.size() == tiers
	for k in range(1, tiers):
		stepping = stepping and brawl.lead_times[k] < brawl.lead_times[k - 1] and brawl.gap_times[k] < brawl.gap_times[k - 1] \
			and brawl.neutral_times[k] < brawl.neutral_times[k - 1]
	t.log_p("leads %s, gaps %s, breaths %s" % [brawl.lead_times, brawl.gap_times, brawl.neutral_times])
	t.check(stepping and brawl.lead_times.min() >= LEAD_FLOOR - 0.0001,
		"four tiers, each tell, gap and breath shorter than the last, no tell under %.2f s" % LEAD_FLOOR)
	var clean_openers: bool = brawl.OPENERS.all(func(c): return not c.has(&"F"))
	var shapes := true
	var shares := []
	for k in tiers:
		var punches := 0
		var feints := 0
		for combo in brawl.PATTERNS[k]:
			shapes = shapes and combo[-1] != &"F"
			for i in combo.size():
				punches += 1
				if combo[i] == &"F":
					feints += 1
					shapes = shapes and (i == 0 or combo[i - 1] != &"F")
		shares.append("%d%%" % roundi(100.0 * feints / punches))
	t.log_p("feints by tier %s" % [shares])
	t.check(clean_openers and shapes, "no feint in the openers, none ending a combo, never two in a row")
	var drawn := {"dry": 0, "free": 0, "free_feints": 0}
	for k in tiers:
		brawl.cycle = k + 1
		for n in DROUGHT_DRAWS:
			for dry in [true, false]:
				brawl.combos_thrown = brawl.OPENERS.size()
				brawl.last_combo = []
				brawl.last_kind = &"L"
				brawl.since_feint = brawl.feint_drought if dry else 0
				var feinted: bool = brawl._pick_combo().has(&"F")
				if dry:
					drawn.dry += 1 if feinted else 0
				else:
					drawn.free += 1
					drawn.free_feints += 1 if feinted else 0
	t.log_p("draws after %d punches without a feint: %d of %d feint; with one just thrown, %d of %d"
		% [brawl.feint_drought, drawn.dry, tiers * DROUGHT_DRAWS, drawn.free_feints, drawn.free])
	t.check(drawn.dry == tiers * DROUGHT_DRAWS and drawn.free_feints < drawn.free,
		"after %d punches without a feint, every tier's next combo has one" % brawl.feint_drought)
	brawl.since_feint = 0
	brawl.last_kind = &""
	# The fourth cycle's pace, live.
	brawl.cycle = tiers
	brawl.pinned_combos = [[&"L", &"R"]]
	await through_cut(t, brawl, 0.1)
	t.player.playerHealth = 100
	await t.wait_until(func(): return brawl.phase == brawl.Phase.BOXING, 120)
	var two: Array = await box(t, brawl, clean([&"L", &"R"]))
	var gap: float = two[1].told_at - (two[0].told_at + two[0].resolve) if two.size() == 2 else INF
	t.log_p("the fourth tier live: %s, the gap %.3f" % [two, gap])
	t.check(two.size() == 2 and two[0].tier == tiers and absf(two[0].lead - brawl.lead_times[-1]) <= 0.0001
		and absf(gap - brawl.gap_times[-1]) <= FRAME + 0.0001,
		"a fourth-cycle tell on %.2f s, the next %.2f s after it lands" % [brawl.lead_times[-1], brawl.gap_times[-1]])


#THE FRAMING

static func tier_framing(t) -> void:
	var brawl: Node = await into_brawl(t)
	if brawl == null:
		return
	await through_cut(t, brawl, 0.1)
	t.player.playerHealth = 100
	t.clear_iframes()
	var finisher: Node = t.player.finisher
	var seen := {"lowest": INF, "framed_frames": 0, "streak": 0, "fizzles": 0, "juggles": 0, "last_framed": &""}
	var on_parry := func(_hit, _point, _staggered, streak: int) -> void:
		seen.streak = maxi(seen.streak, streak)
	t.defense.parried.connect(on_parry)
	var watch := func() -> void:
		if not brawl.framed:
			return
		seen.framed_frames += 1
		seen.lowest = minf(seen.lowest, t.root.canvas_transform.get_scale().x)
		seen.last_framed = StringName(brawl.Phase.keys()[brawl.phase])
	t.physics_frame.connect(watch)
	var answered := {}
	var dazes := 0
	var juggling_seen := false
	for i in 60 * 300:
		if t.sm.current_state == t.sm.states["Defeated"] or brawl.phase == brawl.Phase.LOST:
			break
		if finisher.phase == t.FINISHER_FIZZLE and brawl.phase == brawl.Phase.FINISHER:
			seen.fizzles += 1 if seen.get("fizzling_daze", -1) != brawl.dazes else 0
			seen["fizzling_daze"] = brawl.dazes
		if finisher.juggling and not juggling_seen:
			juggling_seen = true
			seen.juggles += 1
		if not finisher.is_active():
			juggling_seen = false
		if finisher.is_active() and finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible:
			dazes += 1
			# The first too slowly to bank a bar, so it fizzles; the rest at the model's two bars, so they juggle.
			await t.mash_tiered(FIZZLE_MASH_EVERY if dazes == 1 else MODEL_MASH_EVERY)
			continue
		if brawl.phase == brawl.Phase.BOXING and not brawl.punch.is_empty() and not brawl.punch.resolved:
			var p: Dictionary = brawl.punch
			if not answered.has(p.told_at) and p.clock >= BOTS.skilled.reaction - 0.0001:
				answered[p.told_at] = true
				var key: int = bot_key(p.kind, BOTS.skilled)
				if key != 0:
					t.tap(key)
		await t.physics_frame
	await t.wait_until(func(): return t.sm.current_state == t.sm.states["Defeated"], 400)
	t.physics_frame.disconnect(watch)
	t.defense.parried.disconnect(on_parry)
	var scale_after: float = t.root.canvas_transform.get_scale().x
	t.log_p("framing: %d framed frames, the view drawn at %.3f at the least (the brawl's %.2f); the longest parry streak %d, %d fizzled dazes, %d juggles; framed until %s; after the hand-off %.3f, floor %s"
		% [seen.framed_frames, seen.lowest, Layout.ZOOM, seen.streak, seen.fizzles, seen.juggles, seen.last_framed, scale_after, ScreenView.base_is_floor])
	t.check(t.sm.current_state == t.sm.states["Defeated"] and seen.streak >= 3 and seen.fizzles >= 1 and seen.juggles >= 2,
		"a whole brawl to the KO through a parry streak of %d (the punch-in comes from the third), %d fizzled daze and %d juggles" % [seen.streak, seen.fizzles, seen.juggles])
	t.check(seen.framed_frames > 0 and seen.lowest >= Layout.ZOOM - 0.001 and seen.last_framed == &"KO_DOWN",
		"the view never drawn further out than the brawl's framing from the cut-in to the KO's hand-off (at least %.3f, framed until %s)" % [seen.lowest, seen.last_framed])
	t.check(is_equal_approx(scale_after, 1.0) and not ScreenView.base_is_floor and is_equal_approx(ScreenView.base_zoom, 1.0),
		"and level again at the hand-off, the floor gone (%.3f, floor %s)" % [scale_after, ScreenView.base_is_floor])


#THE BOTS

static func tier_bots(t) -> void:
	var outcomes := {}
	for bot in BOTS:
		outcomes[bot] = []
		for seed in BOT_SEEDS:
			var result: Dictionary = await play_bot(t, bot, BOTS[bot], seed)
			outcomes[bot].append(result.outcome)
			leave(t)
	for bot in BOTS:
		var want: String = BOTS[bot].want
		t.check(outcomes[bot].all(func(o): return o == want), "%s: %s on every seed (%s)" % [bot, want, outcomes[bot]])


# One whole brawl from the cut-in, `spec`'s bot answering every tell and mashing every daze. What came of it.
static func play_bot(t, bot: String, spec: Dictionary, seed: int) -> Dictionary:
	var brawl: Node = await into_brawl(t)
	if brawl == null:
		return {"outcome": "none"}
	await through_cut(t, brawl, 0.1)
	t.sm.rng.seed = seed
	t.player.playerHealth = BOT_HEALTH
	t.clear_iframes()
	var finisher: Node = t.player.finisher
	var answered := {}
	var uppercuts: Array = []
	var start := -1.0
	var last_tier := 1
	var outcome := "timeout"
	for i in 60 * 300:
		if t.sm.current_state == t.sm.states["Defeated"]:
			outcome = "won"
			break
		if brawl.phase == brawl.Phase.LOST or t.sm.current_state == t.sm.states["Victory"] or t.player.playerHealth <= 0:
			outcome = "lost"
			break
		if finisher.is_active() and finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible:
			var before: int = brawl.uppercuts_left
			await t.mash_tiered(5)
			await t.wait_until(func(): return not finisher.is_active() or brawl.phase >= brawl.Phase.KO_SNAP, 400)
			uppercuts.append(before - brawl.uppercuts_left)
			continue
		if brawl.phase == brawl.Phase.BOXING and not brawl.punch.is_empty() and not brawl.punch.resolved:
			var p: Dictionary = brawl.punch
			if start < 0.0:
				start = p.told_at
			last_tier = maxi(last_tier, p.tier)
			if not answered.has(p.told_at) and p.clock >= spec.reaction - 0.0001:
				answered[p.told_at] = true
				var key: int = bot_key(p.kind, spec)
				if key != 0:
					t.tap(key)
		await t.physics_frame
	var log: Array = brawl.punch_log
	var kinds := {}
	for p in log:
		kinds[p.kind] = kinds.get(p.kind, 0) + 1
	var bites: int = log.filter(func(p): return p.result == &"countered").size()
	var hits: int = log.filter(func(p): return p.result == &"hit").size()
	var damage := 0
	for p in log:
		damage += p.damage
	var lasted: float = t.boss.fight_clock - start if start >= 0.0 else 0.0
	var opened := 0
	for combo in brawl.OPENERS:
		opened += combo.size()
	var dry := 0
	var driest := 0
	for p in log.slice(opened):
		dry = 0 if p.kind == &"F" else dry + 1
		driest = maxi(driest, dry)
	t.log_p("%s, seed %d: %s after %.1f s of boxing; %d punches %s, %d bitten feints, %d hits, %d damage, health %d, stamina %.0f; dazes %d, uppercuts each %s, %d left; the last tier %d; at most %d punches running without a feint"
		% [bot, seed, outcome, lasted, log.size(), kinds, bites, hits, damage, t.player.playerHealth, t.defense.stamina, uppercuts.size(),
			uppercuts, brawl.uppercuts_left, last_tier, driest])
	return {"outcome": outcome, "lasted": lasted}


# The key `spec`'s bot presses for a punch of `kind`, or 0 for none.
static func bot_key(kind: StringName, spec: Dictionary) -> int:
	match kind:
		&"L":
			return KEY_LEFT
		&"R":
			return KEY_RIGHT
		&"S":
			return KEY_SHIFT if spec.straights else 0
		&"F":
			return KEY_SHIFT if spec.feints else 0
	return 0
