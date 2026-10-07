extends RefCounted

# jordan_kegs (coder B): Jordan's attack 2, Captain Burak + Danny's kegs (JordanComboKegs, JordanKegsLayout), in the god
# fight, each tier on a fresh fight whose rotation holds only the kegs, started as soon as it opens. --max-fps 60: the
# payoff's mash is real time. Every time is on the attack's own clock (kegs_clock), which is game time. tier=
#   layout   staging option B under the fight's 2/3 view: the kegs, the stations and both puppets on the floor; the
#            stations outside Danny's seat and the centre in it; Danny at rest clear of Jordan's right hand; the counter
#            at UI scale over Burak's hat; the kegs, the puppets, the counter and the player at every station clear of
#            Jordan's mask and core and 12 px clear of the HUD (screen px); Danny hung over the centre under the core.
#   dash     the dash button alone does nothing, and neither does a diagonal (two arrows at once); an arrow alone is the
#            move: RIGHT reaches the east station in 0.08 s (five steps) facing it, and no stamina goes; from there only
#            LEFT moves, back to the centre, and held it moves once, not on to the west keg; a press inside a move or a
#            punch counts for nothing.
#   perfect  a bot that dashes out on each glow, punches it, and goes home once Danny is down: eight defuses, the eighth
#            keg into Burak, a walk to him, three presses and a three-bar mash: Jordan -3, and not a half-heart lost.
#   miss     a glow left alone blows GLOW_TIME on, to the frame: exactly one half-heart, its flash over the fight's whole
#            view; the count kept; the keg laid again, a move at it meanwhile doing nothing; never the same keg twice
#            running.
#   slam     standing in the centre with no glow lit: the shadow hangs 0.5 s and the landing takes exactly one
#            half-heart, the soles in his seat; a bot that leaves under the shadow takes none.
#   fuse     (the tuning of 2026-10-04) a right answer at a first-timer's pace - a 0.25 s reaction, the dash, a 0.10 s
#            settle and the punch - beats GLOW_TIME with FUSE_SLACK in hand; a fumble at a practised pace - out to the
#            wrong keg, a reaction there, back, a settle, over - is too slow, and the keg blows for its half-heart.
#   order    60 glows off the attack's own pick: never the same keg twice running, and all four used.
#   stall    staying at a keg after a defuse: the next glow comes 2.0 s after it, to the frame, on another keg.
#   pause    the pause screen under Danny's shadow and mid-glow holds the attack's clock, and the shadow's 0.5 s and the
#            glow's GLOW_TIME still land on game time; paused mid-move, the move still lands on its station.
#   death    at one half-heart a blast gives the Defeat screen, and the attack leaves nothing of its own behind.
#   normal   all of them in turn.

const FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const GOD := "Arena/JordanGodScene/God"
const KEGS_SCRIPT := "res://Scripts/States/JordanGod/JordanComboKegs.gd"
const Layout := preload("res://Scripts/JordanKegsLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const BurakArt := preload("res://Scripts/BurakBossArtLayout.gd")
const DannyArt := preload("res://Scripts/DannyBossArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BLAST_SCRIPT := preload("res://Scripts/BurakBossBlastScript.gd")
const SEED := 20260928
const FRAME := 1.0 / 60.0
const TIERS := ["layout", "dash", "perfect", "miss", "slam", "fuse", "order", "stall", "pause", "death"]
const WAY_KEYS := {&"up": KEY_UP, &"right": KEY_RIGHT, &"down": KEY_DOWN, &"left": KEY_LEFT}
# Staging option B's keep-clears (art_source/jordan_puppeteer/staging/staging.json): Jordan's mask and core in world px,
# and the HUD in screen px with the clearance round it.
const MASK := Rect2(912, 189, 96, 69)
const CORE := Rect2(936, 270, 48, 57)
const HUD_KEEP_OUT := [Rect2(720, 33, 480, 148), Rect2(10, 842, 406, 229), Rect2(1371, 946, 537, 126)]
const HUD_CLEARANCE := 12.0
# A bot's reaction to a glow, in frames: a practised player's, and a first-timer's (the playtest model's 0.20 and 0.25 s).
const REACTION := 12
const FIRST_REACTION := 15
# The model's settle between a dash landing and the next press, in frames, and what a first-timer's answer must still
# have of the fuse.
const SETTLE := 6
const FUSE_SLACK := 0.2
# The payoff's punches, this many frames apart: over the punch-out's 0.10 s floor.
const PUNCH_GAP := 9
const PAUSE_FRAMES := 45


# Every hit the player takes, on the attack's clock.
class Hits:
	var list: Array = []
	var combo: Node

	func _init(defense: Node, attack: Node) -> void:
		combo = attack
		defense.hit_taken.connect(_on_hit)

	func _on_hit(hit: RefCounted) -> void:
		list.append({id = hit.attack_id, at = combo.kegs_clock, damage = hit.damage})

	func of(id: StringName) -> Array:
		return list.filter(func(h: Dictionary) -> bool: return h.id == id)


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	for tier in tiers:
		t.log_p("-- jordan_kegs %s" % tier)
		match tier:
			"layout":
				await tier_layout(t)
			"dash":
				await tier_dash(t)
			"perfect":
				await tier_perfect(t)
			"miss":
				await tier_miss(t)
			"slam":
				await tier_slam(t)
			"fuse":
				await tier_fuse(t)
			"order":
				await tier_order(t)
			"stall":
				await tier_stall(t)
			"pause":
				await tier_pause(t)
			"death":
				await tier_death(t)
			_:
				t.check(false, "jordan_kegs has no tier %s" % tier)


#GETTING THERE

# A fresh god fight whose rotation is the kegs alone, the player at `health`, the attack started as the fight's Open
# hands over and its seed fixed before the first glow: back once the lay has played out and the loop runs, the player
# in the centre.
static func enter(t, health := 100) -> Node:
	var combos: Array[String] = [KEGS_SCRIPT]
	GodLayout.COMBOS = combos
	await t.open_scene(FIGHT)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(GOD)
	t.sm = t.boss.state_machine
	t.player.playerHealth = health
	var combo := combo_of(t)
	t.check(combo != null, "the rotation holds the kegs")
	await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 4)
	t.sm.start_next_attack()
	combo.rng.seed = SEED
	var looping: bool = await t.wait_until(func(): return combo.beat == combo.Beat.LOOP, 60 * 8)
	t.check(looping and t.sm.current_state == combo, "the kegs start, and the lay plays out into the loop")
	return combo


static func combo_of(t) -> Node:
	for node in t.current_scene.find_children("*", "Node", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == KEGS_SCRIPT:
			return node
	return null


static func soles(t) -> Vector2:
	return t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


#THE BOT

# One arrow tapped: the move that way.
static func move(t, way: StringName) -> void:
	t.tap(WAY_KEYS[way])
	await t.wait(1)


# To `goal` (a keg's station, or &"centre") the way the attack allows: out from the centre, or straight back.
static func move_to(t, combo: Node, goal: StringName) -> bool:
	var way: StringName = Layout.back_way(combo.where) if goal == &"centre" else Layout.WAYS[goal]
	await move(t, way)
	return await t.wait_until(func(): return combo.where == goal, 20)


static func airborne(combo: Node) -> bool:
	return combo.slam in [combo.Slam.YANK, combo.Slam.LEAP, combo.Slam.SHADOW, combo.Slam.DROP]


# Home once Danny is not about to come down on the centre.
static func home(t, combo: Node) -> void:
	await t.wait_until(func(): return not airborne(combo), 120)
	await move_to(t, combo, &"centre")


# The next glow, answered REACTION steps after it lights: out to it (by the centre, from a keg) and one punch. The keg.
static func answer(t, combo: Node) -> StringName:
	await t.wait_until(func(): return combo.glowing != &"" or combo.beat != combo.Beat.LOOP, 60 * 5)
	var keg: StringName = combo.glowing
	if keg == &"":
		return &""
	await t.wait(REACTION)
	if combo.where != &"centre":
		await move_to(t, combo, &"centre")
	await move_to(t, combo, keg)
	var before: int = combo.defused
	t.tap(KEY_Q)
	await t.wait_until(func(): return combo.defused > before, 20)
	return keg


# Walking at him, the way a player holds the keys, until the punches start.
static func walk_to_burak(t, combo: Node) -> void:
	var held: Array = []
	for i in 60 * 5:
		if combo.beat != combo.Beat.WALK:
			break
		var to: Vector2 = Layout.BURAK_FEET - soles(t)
		var want: Array = []
		if absf(to.x) > 8.0:
			want.append(KEY_RIGHT if to.x > 0.0 else KEY_LEFT)
		if absf(to.y) > 8.0:
			want.append(KEY_DOWN if to.y > 0.0 else KEY_UP)
		for code in held:
			if not want.has(code):
				t.release(code)
		for code in want:
			if not held.has(code):
				t.press(code)
		held = want
		await t.physics_frame
	for code in held:
		t.release(code)


# The three presses and a mash that banks every bar; the bars the payoff reported.
static func pay_off(t, combo: Node) -> int:
	for i in 3:
		t.tap(KEY_Q)
		await t.wait(PUNCH_GAP)
	await t.wait_until(func(): return t.player.finisher.is_active(), 60 * 2)
	await t.mash_tiered(t.TIER_PASS_FRAMES[2])
	await t.wait_until(func(): return combo.bars >= 0, 60 * 10)
	return combo.bars


#THE TIERS

static func tier_layout(t) -> void:
	var combo: Node = await enter(t)
	var floor_rect: Rect2 = GodLayout.FLOOR
	var origins: Rect2 = t.player.ring_origins
	t.check(Layout.in_slam_zone(Layout.CENTRE) and soles(t) == Layout.CENTRE, "the player in the centre, inside Danny's seat")
	for keg: StringName in Layout.KEGS:
		var station: Vector2 = Layout.STATIONS[keg]
		t.check(floor_rect.has_point(Layout.KEG_POINTS[keg]) and origins.has_point(Layout.body_point(station)),
			"the %s keg and its station on the floor" % keg)
		t.check(not Layout.in_slam_zone(station), "the %s station outside his seat" % keg)
		var laid: bool = combo.kegs.has(keg) and combo.kegs[keg].global_position == Layout.KEG_POINTS[keg]
		t.check(laid, "the %s keg laid on its spot" % keg)
		if laid:
			var keg_rect: Rect2 = drawn(combo.kegs[keg].body_sprite)
			t.check(clear_of_jordan(keg_rect) and clear_of_hud(keg_rect), "the %s keg clear of Jordan's mask and core, and of the HUD (screen %s)" % [keg, to_screen(keg_rect)])
		var body := Rect2(Layout.body_point(station) - Vector2(48, 48), Vector2(96, 96))
		t.check(clear_of_hud(body), "the player at the %s station clear of the HUD (screen %s)" % [keg, to_screen(body)])
	t.check(combo.burak.global_position == Layout.BURAK_FEET and combo.danny.global_position == Layout.DANNY_REST
		and floor_rect.has_point(Layout.BURAK_FEET) and floor_rect.has_point(Layout.DANNY_REST),
		"Burak and Danny stand on their spots on the floor")
	for puppet: Node2D in [combo.burak, combo.danny]:
		var frame: Rect2 = drawn(puppet.sprite)
		t.check(clear_of_jordan(frame) and clear_of_hud(frame) and floor_rect.encloses(Rect2(frame.position.x, frame.end.y - 1.0, frame.size.x, 1.0)),
			"%s at rest clear of Jordan's mask and core and of the HUD, his frame's width on the floor (screen %s)" % [puppet.boss, to_screen(frame)])
	var claws := -INF
	for i in 5:
		claws = maxf(claws, t.boss.fingertip(&"right", i).x)
	var danny_frame: Rect2 = drawn(combo.danny.sprite)
	t.log_p("Danny's frame at rest %s; Jordan's right claws to x %.1f" % [danny_frame, claws])
	t.check(danny_frame.position.x > claws, "Danny at rest clear of Jordan's right hand (from x %.0f; the claws to %.0f)" % [danny_frame.position.x, claws])

	var crown_y: float = combo.burak.get_daze_anchor().y + BurakArt.DAZE_GAP
	var row := Rect2()
	for pip: Sprite2D in combo.counter.pips:
		row = drawn(pip) if row.size == Vector2.ZERO else row.merge(drawn(pip))
	var on_screen := to_screen(row)
	t.log_p("the counter %s (screen %s); Burak's crown y %.0f" % [row, on_screen, crown_y])
	t.check(combo.counter.pips.size() == Layout.DEFUSES and is_equal_approx(on_screen.size.y, 72.0),
		"the counter's %d pips read at their own size on the screen (%.0f px tall)" % [combo.counter.pips.size(), on_screen.size.y])
	t.check(row.end.y <= crown_y and absf(row.get_center().x - Layout.BURAK_FEET.x) <= 1.0, "centred over Burak's hat, clear of it (to y %.0f)" % row.end.y)
	t.check(clear_of_jordan(row) and clear_of_hud(row), "and clear of Jordan's mask and core, and of the HUD")

	var tallest := 0.0
	for spec: Dictionary in [DannyArt.anim(&"air"), DannyArt.anim(&"slam_drop")]:
		tallest = maxf(tallest, drawn_height(spec))
	var hung_top: float = Layout.CENTRE.y - Layout.HOVER_HEIGHT - tallest
	t.check(hung_top >= CORE.end.y + 12.0, "Danny hung over the centre stays under Jordan's core (his top at y %.0f)" % hung_top)


# A sprite's frame in world px.
static func drawn(sprite: Sprite2D) -> Rect2:
	return sprite.get_global_transform() * sprite.get_rect()


static func clear_of_jordan(rect: Rect2) -> bool:
	return not rect.intersects(MASK) and not rect.intersects(CORE)


# Through the fight's base view, where the HUD sits over it.
static func to_screen(rect: Rect2) -> Rect2:
	var zoom: float = ScreenView.base_zoom
	return Rect2((rect.position - ScreenView.base_focus) * zoom + ScreenView.VIEW_SIZE / 2.0, rect.size * zoom)


static func clear_of_hud(rect: Rect2) -> bool:
	var on_screen := to_screen(rect)
	for keep_out: Rect2 in HUD_KEEP_OUT:
		if on_screen.intersects(keep_out.grow(HUD_CLEARANCE)):
			return false
	return true


# How far above his soles the tallest of `spec`'s frames is drawn, in px: his own sheet's pixels.
static func drawn_height(spec: Dictionary) -> float:
	var image: Image = load(spec.sheet).get_image()
	var size: Vector2 = spec.get("frame", DannyArt.FRAME_SIZE)
	var feet: Vector2 = spec.get("feet", DannyArt.ANCHOR)
	var top := INF
	for f in spec.frames:
		var used := image.get_region(Rect2i(int(f) * int(size.x), 0, int(size.x), int(size.y))).get_used_rect()
		top = minf(top, used.position.y)
	return (feet.y + 1.0 - top) * DannyArt.SCALE


static func tier_dash(t) -> void:
	var combo: Node = await enter(t)
	var stamina: float = t.defense.stamina
	var start: Vector2 = t.player.global_position
	t.tap(KEY_W)
	await t.wait(8)
	t.check(t.player.global_position == start and combo.where == &"centre", "the dash button alone does nothing")
	t.press(KEY_UP)
	t.press(KEY_RIGHT)
	await t.wait(8)
	t.release(KEY_UP)
	t.release(KEY_RIGHT)
	await t.wait(2)
	t.check(t.player.global_position == start and combo.where == &"centre", "nor does a diagonal, two arrows at once")

	var pressed_at: float = combo.kegs_clock
	await move(t, &"right")
	await t.wait_until(func(): return combo.where == &"e", 30)
	var took: float = combo.kegs_clock - pressed_at
	t.log_p("east reached %.3f s after the press, soles %s" % [took, soles(t)])
	t.check(took <= Layout.DASH_TIME + 2.0 * FRAME + 0.0001 and soles(t) == Layout.STATIONS[&"e"],
		"RIGHT alone reaches the east station in 0.08 s (%.3f)" % took)
	t.check(t.player.facing == t.player.Facing.RIGHT, "facing its keg")
	t.check(is_equal_approx(t.defense.stamina, stamina), "no stamina spent (%.1f)" % t.defense.stamina)

	for way: StringName in [&"up", &"right", &"down"]:
		await move(t, way)
		await t.wait(8)
		t.check(combo.where == &"e" and soles(t) == Layout.STATIONS[&"e"], "from the east keg, %s does nothing" % way)
	t.tap(KEY_Q)
	await t.wait(1)
	await move(t, &"left")
	await t.wait(10)
	t.check(combo.where == &"e", "a move pressed inside a punch counts for nothing")
	t.press(KEY_LEFT)
	await t.wait(30)
	t.release(KEY_LEFT)
	await t.wait(2)
	t.check(combo.where == &"centre" and soles(t) == Layout.CENTRE,
		"LEFT held goes back to the centre once, not on to the west keg (%s)" % soles(t))

	await t.wait_until(func(): return combo.kegs.has(&"n"), 60 * 2)
	await move(t, &"up")
	await move(t, &"down")
	await t.wait(10)
	t.check(combo.where == &"n", "a second press inside the move counts for nothing (%s)" % combo.where)
	t.check(is_equal_approx(t.defense.stamina, stamina), "and still no stamina spent (%.1f)" % t.defense.stamina)


static func tier_perfect(t) -> void:
	var combo: Node = await enter(t)
	var hits := Hits.new(t.defense, combo)
	var health: int = t.player.playerHealth
	var jordan: int = t.boss.boss_health
	var hype: float = t.player.hype.hype
	while combo.defused < Layout.DEFUSES and combo.beat == combo.Beat.LOOP:
		await answer(t, combo)
		if combo.defused < Layout.DEFUSES:
			await home(t, combo)
	t.log_p("defuses %s" % [combo.defuses.map(func(d): return [d.keg, snappedf(d.at, 0.001)])])
	t.log_p("glows %s; slams %d" % [combo.glows.map(func(g): return g.keg), combo.slams.size()])
	t.check(combo.defused == Layout.DEFUSES and combo.blasts.is_empty(), "eight defuses, no keg blown (%d, %d)" % [combo.defused, combo.blasts.size()])
	await t.wait_until(func(): return combo.beat == combo.Beat.WALK, 60 * 2)
	t.check(combo.beat == combo.Beat.WALK and combo.kegs.is_empty() and combo.burak.current_anim == &"broken"
		and (combo.slam == combo.Slam.LIMP or combo.limp_owed), "the eighth keg flies into Burak: dazed, the kegs gone, Danny let go")
	t.check(not t.player.is_action_locked, "and the player is let go")
	t.check(t.player.hype.hype >= hype + Layout.DEFUSES * Layout.HYPE_EACH + Layout.HYPE_CLEAN - 0.01,
		"hype for each defuse and the clean eight (%.1f -> %.1f)" % [hype, t.player.hype.hype])
	await walk_to_burak(t, combo)
	t.check(combo.beat == combo.Beat.PAYOFF, "a walk to him (%s)" % soles(t))
	var bars: int = await pay_off(t, combo)
	t.log_p("bars %d, Jordan %d -> %d" % [bars, jordan, t.boss.boss_health])
	t.check(bars == 3 and t.boss.boss_health == jordan - 3, "three presses and a three-bar mash: Jordan -3")
	t.check(hits.list.is_empty() and t.player.playerHealth == health, "not a half-heart lost (%s)" % [hits.list])
	await t.wait_until(func(): return t.sm.current_state != combo, 60 * 6)
	t.check(t.sm.current_state != combo and combo.beat == combo.Beat.OFF and combo.puppets.is_empty()
		and t.get_nodes_in_group(GodLayout.HAZARD_GROUP).is_empty() and t.player.z_index == 0,
		"then the wrap: the puppets recalled, nothing left, the player's z back, and Idle (%s)" % t.sm.current_state.name)


static func tier_miss(t) -> void:
	var combo: Node = await enter(t)
	var hits := Hits.new(t.defense, combo)
	await answer(t, combo)
	await home(t, combo)
	await t.wait_until(func(): return combo.glowing != &"", 60 * 3)
	var lit: StringName = combo.glowing
	var glow_at: float = combo.glow_started
	var away: StringName = Layout.KEGS[(Layout.KEGS.find(lit) + 2) % 4]
	await move_to(t, combo, away)
	var health: int = t.player.playerHealth
	await t.wait_until(func(): return not combo.blasts.is_empty(), 60 * 3)
	var flash := Rect2()
	for node in t.get_nodes_in_group(GodLayout.HAZARD_GROUP):
		if node.get_script() == BLAST_SCRIPT and is_instance_valid(node.screen):
			flash = drawn(node.screen)
	t.check(flash.is_equal_approx(ScreenView.base_rect()), "its flash covers the fight's whole view (%s)" % flash)
	var blast: Dictionary = combo.blasts[0] if not combo.blasts.is_empty() else {keg = &"", at = -1.0}
	t.log_p("the %s keg lit at %.3f, blew at %.3f: %s" % [lit, glow_at, blast.at, blast])
	t.check(blast.keg == lit and absf(blast.at - glow_at - Layout.GLOW_TIME) <= FRAME + 0.0001,
		"a glow left alone blows %.2f s on (%.3f)" % [Layout.GLOW_TIME, blast.at - glow_at])
	t.check(health - t.player.playerHealth == 1 and hits.of(&"burak_barrel_blast").size() == 1, "exactly one half-heart")
	t.check(combo.defused == 1, "the count is kept (%d)" % combo.defused)
	await move_to(t, combo, &"centre")
	await move(t, Layout.WAYS[lit])
	await t.wait(8)
	t.check(combo.where == &"centre" and not combo.kegs.has(lit), "a move at a keg being laid again does nothing")
	await t.wait_until(func(): return combo.kegs.has(lit), 60)
	t.check(combo.kegs.has(lit) and combo.kegs[lit].is_breakable(), "the keg is laid again")
	await t.wait_until(func(): return combo.glows.size() >= 3, 60 * 3)
	var order: Array = combo.glows.map(func(g): return g.keg)
	var repeats := 0
	for i in range(1, order.size()):
		if order[i] == order[i - 1]:
			repeats += 1
	t.check(order.size() >= 3 and order[2] != lit and repeats == 0, "the next glow is on another keg, and none twice running (%s)" % [order])


static func tier_slam(t) -> void:
	var combo: Node = await enter(t)
	# No glow this run: since GLOW_TIME came down to 0.85 (2026-10-04) a keg left alone blows before he lands, and its
	# i-frames would cover his landing.
	combo.quiet_gap = 60.0
	var hits := Hits.new(t.defense, combo)
	var health: int = t.player.playerHealth
	await t.wait_until(func(): return combo.slams.size() >= 1 and combo.slams[0].has("impact_at"), 60 * 3)
	var first: Dictionary = combo.slams[0]
	var hung: float = first.drop_at - first.shadow_at
	var slammed: Array = hits.of(Layout.SLAM_ID)
	t.log_p("staying: %s; hits %s" % [first, hits.list])
	t.check(absf(hung - Layout.SHADOW_TIME) <= FRAME + 0.0001, "the shadow hangs 0.5 s before he drops (%.3f)" % hung)
	t.check(first.inside and first.result == 1 and slammed.size() == 1 and slammed[0].damage == 1
		and absf(slammed[0].at - first.impact_at) <= 0.0001, "then the landing takes one half-heart, the soles in his seat")
	t.check(health - t.player.playerHealth == 1, "exactly one (%d)" % (health - t.player.playerHealth))

	combo = await enter(t)
	hits = Hits.new(t.defense, combo)
	await t.wait_until(func(): return combo.slam == combo.Slam.SHADOW, 60 * 3)
	await t.wait(6)
	await move_to(t, combo, combo.glowing)
	await t.wait_until(func(): return combo.slams[0].has("impact_at"), 60 * 2)
	t.log_p("leaving: %s" % [combo.slams[0]])
	t.check(not combo.slams[0].inside and hits.of(Layout.SLAM_ID).is_empty(), "a bot that leaves under the shadow takes none")


static func tier_fuse(t) -> void:
	var combo: Node = await enter(t)
	var hits := Hits.new(t.defense, combo)
	await t.wait_until(func(): return combo.glowing != &"", 60 * 3)
	var lit: StringName = combo.glowing
	var glow_at: float = combo.glow_started
	await t.wait(FIRST_REACTION)
	await move_to(t, combo, lit)
	await t.wait(SETTLE)
	var before: int = combo.defused
	t.tap(KEY_Q)
	await t.wait_until(func(): return combo.defused > before or not combo.blasts.is_empty(), 30)
	var spare: float = Layout.GLOW_TIME - (combo.defuses[-1].at - glow_at) if combo.defused > before else -1.0
	t.log_p("a first-timer's answer on the %s keg: %.3f s of the fuse in hand" % [lit, spare])
	t.check(combo.blasts.is_empty() and spare >= FUSE_SLACK,
		"a right answer at a first-timer's pace puts it out with %.2f s or more in hand (%.3f)" % [FUSE_SLACK, spare])

	await home(t, combo)
	await t.wait_until(func(): return combo.glowing != &"", 60 * 3)
	lit = combo.glowing
	var wrong: StringName = Layout.KEGS.filter(func(k: StringName) -> bool: return k != lit and combo.kegs.has(k))[0]
	var health: int = t.player.playerHealth
	await t.wait(REACTION)
	await move_to(t, combo, wrong)
	await t.wait(REACTION)
	await move_to(t, combo, &"centre")
	await t.wait(SETTLE)
	await move_to(t, combo, lit)
	await t.wait(SETTLE)
	t.tap(KEY_Q)
	await t.wait(12)
	var blew: Array = combo.blasts.filter(func(b: Dictionary) -> bool: return b.keg == lit)
	t.log_p("a fumble on the %s keg (out to %s first): blasts %s, defused %d" % [lit, wrong, combo.blasts, combo.defused])
	t.check(blew.size() == 1 and combo.defused == before + 1 and health - t.player.playerHealth == 1
		and hits.of(&"burak_barrel_blast").size() == 1, "a fumble - the wrong keg, back and over - is too slow: it blows, one half-heart")


static func tier_order(t) -> void:
	var combo: Node = await enter(t)
	await answer(t, combo)
	var used := {}
	var repeats := 0
	var last: StringName = combo.last_glow
	for i in 60:
		var pick: StringName = combo.pick_glow()
		if pick == last:
			repeats += 1
		used[pick] = true
		last = pick
		combo.last_glow = pick
	t.check(repeats == 0 and used.size() == 4, "60 glows: never the same keg twice running (%d), all four used (%s)" % [repeats, used.keys()])


static func tier_stall(t) -> void:
	var combo: Node = await enter(t)
	var keg: StringName = await answer(t, combo)
	var defused_at: float = combo.defuses[0].at
	await t.wait_until(func(): return combo.glows.size() >= 2, 60 * 4)
	var next: Dictionary = combo.glows[1]
	t.log_p("defused %s at %.3f and stayed; the next glow %s" % [keg, defused_at, next])
	t.check(combo.where == keg and absf(next.at - defused_at - Layout.STALL_TIME) <= FRAME + 0.0001,
		"staying at the keg, the next glow comes 2.0 s after the defuse (%.3f)" % (next.at - defused_at))
	t.check(next.keg != keg, "on another keg (%s)" % next.keg)


static func tier_pause(t) -> void:
	var combo: Node = await enter(t)
	await t.wait_until(func(): return combo.glowing != &"", 60 * 2)
	var lit: StringName = combo.glowing
	var glow_at: float = combo.glow_started
	await t.wait_until(func(): return combo.slam == combo.Slam.SHADOW, 60 * 2)
	await t.wait(10)
	await t.tap_pause()
	var paused: bool = t.paused
	var clock: float = combo.kegs_clock
	await t.wait(PAUSE_FRAMES)
	var after: float = combo.kegs_clock
	await t.tap_pause()
	t.check(paused and is_equal_approx(after, clock),
		"paused under the shadow and mid-glow, the attack's clock holds over %d frames (%.3f, %.3f)" % [PAUSE_FRAMES, clock, after])
	await t.wait_until(func(): return combo.slams[0].has("drop_at"), 60 * 2)
	var hung: float = combo.slams[0].drop_at - combo.slams[0].shadow_at
	t.check(absf(hung - Layout.SHADOW_TIME) <= FRAME + 0.0001, "the shadow still hangs 0.5 s of game time (%.3f)" % hung)
	await t.wait_until(func(): return not combo.blasts.is_empty(), 60 * 3)
	var blew: float = combo.blasts[0].at - glow_at if not combo.blasts.is_empty() else -1.0
	t.check(absf(blew - Layout.GLOW_TIME) <= FRAME + 0.0001, "and the %s keg still blows %.2f s of game time on (%.3f)" % [lit,
		Layout.GLOW_TIME, blew])

	await t.wait_until(func(): return not airborne(combo) and combo.where == &"centre", 60 * 3)
	var goal := &""
	for keg: StringName in Layout.KEGS:
		if combo.kegs.has(keg):
			goal = keg
			break
	var pressed_at: float = combo.kegs_clock
	t.tap(WAY_KEYS[Layout.WAYS[goal]])
	await t.wait(3)
	var mid: bool = combo.where == &""
	await t.tap_pause()
	await t.wait(PAUSE_FRAMES)
	await t.tap_pause()
	await t.wait_until(func(): return combo.where == goal, 30)
	var took: float = combo.kegs_clock - pressed_at
	t.check(mid and soles(t) == Layout.STATIONS[goal] and took <= Layout.DASH_TIME + 2.0 * FRAME + 0.0001,
		"paused mid-move, it still lands on the %s station in 0.08 s of game time (%.3f)" % [goal, took])


static func tier_death(t) -> void:
	var combo: Node = await enter(t, 1)
	await t.wait_until(func(): return combo.glowing != &"", 60 * 2)
	var away: StringName = Layout.KEGS[(Layout.KEGS.find(combo.glowing) + 2) % 4]
	await move_to(t, combo, away)
	await t.wait_until(func(): return t.player.playerHealth <= 0, 60 * 3)
	await t.wait(3)
	t.check(t.player.playerHealth == 0 and combo.blasts.size() == 1, "at one half-heart the blast takes the last")
	t.check(combo.beat == combo.Beat.OFF and not t.player.is_action_locked and not t.player.is_posed() and t.player.z_index == 0,
		"the attack lets go: no lock, no pose, the player's z back")
	t.check(t.get_nodes_in_group(GodLayout.HAZARD_GROUP).all(func(node: Node) -> bool: return node.is_queued_for_deletion())
		and combo.puppets.is_empty() and not is_instance_valid(combo.mark) and not is_instance_valid(combo.stars),
		"and nothing of its own is left: kegs, pips, the shadow, the stars, the puppets")
	var reached := false
	for i in 60 * 12:
		if t.current_scene != null and t.current_scene.scene_file_path == DEFEAT:
			reached = true
			break
		await t.process_frame
	t.check(reached, "then the Defeat screen")
