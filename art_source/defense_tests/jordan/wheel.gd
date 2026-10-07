extends RefCounted

# jordan_wheel: Jordan's attack 5, Liam + Bixby's Elemental Wheel (JordanComboWheel, JordanWheelLayout, JordanElementWheel),
# in the god fight, each tier on a fresh fight whose rotation holds only the wheel (the switch's own rotation in
# `switch`), started as soon as it opens. --max-fps 60: the payoff's mash is real time. Times are on the attack's own
# clock (wheel_clock), which is game time. The model player: reactions 0.25 +- 0.05 s new, 0.20 +- 0.04 learned, a 25 px
# margin, 600 px/s on foot; every bot acts on an accumulating clock. tier=
#   layout   invariants() empty; the puppet rows' frame counts equal the live strips'; the staging (Liam's float pivot on
#            the hub, Bixby on his rest) on the floor, in view and clear of Jordan's mask and core and 12 px of the HUD;
#            the wheel on the Floor layer under the strings; the strings on their hands; the see-through.
#   wheel    F1: every spin of the actor, from every quarter to every element, lands on its element's quarter (the
#            second pointer on its clockwise neighbour), its last quarter turn no quicker than LAST_SEGMENT_MIN, a tick a
#            quarter; 200 dealt runs cover all four elements and never repeat a double; in a live run the spins land on
#            the deck, quicker each time, and the icon is up STOP_HOLD before anything can hurt.
#   fire     F2, F3: the model over a 120 px grid of starts, both entries, 20 seeds: into the column with 0 hits; live,
#            the walk bot into the column takes nothing, standing still takes exactly 1 hit, a dash back through the
#            front 1 hit.
#   water    F4: the window measured and logged; the model's dash clears >= 95% learned, >= 70% new; live, the dash bot
#            takes nothing and parries the shark's snap after the wave (its badge BREACH_RISE after the wave is off the
#            floor, its contact BITE_TELL after that), standing still and walking to the bottom wall take 1 wave hit each,
#            and standing still the snap lands too.
#   earth    F6: the arrival table at every grid point (the required dashes >= RING_SPACING apart); live, the dash bot takes
#            nothing, standing still takes 3 rings; a ring born on the player hurts only after SLAM_TELL of shadow.
#   air      F7, F8: the walk-away model never swallowed; live, walking away escapes, a guard held still drifts, the
#            reaction parry lands on both bites (model >= 95% new, ~85% learned), the second badge SECOND_BITE_GAP after
#            the first lands; a first bite taken still leaves the second readable and parried once the i-frames are over;
#            a press at 0.45 is hit for 3; a swallow is one chomp of 3 then the spit, and no bite.
#   doubles  F9, F10, F11: all four doubles pinned, the model bot clean; one badge at most; stamina never under the
#            floor and an empty bar still answers; at CLEAR no drift, no ice, the rings past, the wind off; the player
#            never on ice; the undertow's wave off the floor before its jaws start, and its two bites; the landslide's
#            wave, then the snap, then the aftershock.
#   lazy     F5, F12, F14: idle on the grid is hit by every result; nobody starts covered; idle at spawn, the corners
#            and the dash spammer lose their half-hearts.
#   payoff   the crash: spots, poses, punchable with stars; a walk to Liam (and in another run to Bixby), three presses and
#            a three-bar mash: Jordan -3; the hype per result and the clean bonus; then recall and Idle.
#   cleanup  cut at every beat by the player's death, his defeat, a scene change and a finish: nothing left behind.
#   switch   off: COMBOS is today's four and the god fight builds them; on: five, the wheel last, prefetched.
#   rating   the model bot through whole wheels (learned, first, second), logged for the MC.
#   normal   all but rating, in turn.

const SELF := "res://art_source/defense_tests/jordan/wheel.gd"
const FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const MENU := "res://Scenes/Core/MainMenuScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const GOD := "Arena/JordanGodScene/God"
const STRINGS := "Arena/JordanGodScene/Strings"
const STAGE := "Arena/JordanGodScene/Stage"
const FLOOR_LAYER := "Arena/JordanGodScene/Floor"
const WHEEL_SCRIPT := "res://Scripts/States/JordanGod/JordanComboWheel.gd"
const Layout := preload("res://Scripts/JordanWheelLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const PuppetLayout := preload("res://Scripts/JordanPuppetLayout.gd")
const LiamArtLayout := preload("res://Scripts/LiamArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const WheelActor := preload("res://Scripts/JordanElementWheel.gd")
const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const FRAME := 1.0 / 60.0
const TIERS := ["layout", "wheel", "switch", "fire", "water", "earth", "air", "doubles", "lazy", "payoff", "cleanup"]
const FIRE: int = Layout.Element.FIRE
const AIR: int = Layout.Element.AIR
const WATER: int = Layout.Element.WATER
const EARTH: int = Layout.Element.EARTH
const HIT := 1
const PARRIED := 3
const DODGED := 4
const VIEW_MARGIN := 12.0
const PUNCH_GAP := 9
const TODAY: Array[String] = [
	"res://Scripts/States/JordanGod/JordanComboMaze.gd",
	"res://Scripts/States/JordanGod/JordanComboKegs.gd",
	"res://Scripts/States/JordanGod/JordanComboPortals.gd",
	"res://Scripts/States/JordanGod/JordanComboCircle.gd",
]


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	var combos: Array[String] = GodLayout.COMBOS.duplicate()
	var switch_was: bool = GodLayout.USE_ELEMENT_WHEEL
	var me: GDScript = load(SELF)
	var methods: Array = me.get_script_method_list().map(func(m: Dictionary) -> String: return m.name)
	for tier in tiers:
		t.log_p("-- jordan_wheel %s" % tier)
		if not methods.has("tier_" + tier):
			t.check(false, "jordan_wheel has no tier %s" % tier)
			continue
		await me.call("tier_" + tier, t)
	GodLayout.COMBOS = combos
	GodLayout.USE_ELEMENT_WHEEL = switch_was


#GETTING THERE

# A fresh god fight whose rotation is the wheel alone, the player at `health`, the wheel started as Open hands over,
# its deck pinned to `deck` when one is given: back once it is under way (its Avatar State).
static func enter(t, health := 100, deck: Array = []) -> Node:
	var combos: Array[String] = [WHEEL_SCRIPT]
	GodLayout.COMBOS = combos
	t.root.get_node("GameProgress").reset_progress()
	await t.open_scene(FIGHT)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(GOD)
	t.sm = t.boss.state_machine
	t.player.playerHealth = health
	var combo := combo_of(t)
	t.check(combo != null, "the rotation holds the wheel")
	combo.pinned_deck = deck
	await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 4)
	t.sm.start_next_attack()
	var there: bool = await t.wait_until(func(): return combo.beat != combo.Beat.OFF, 60 * 8)
	t.check(there and t.sm.current_state == combo, "the wheel starts")
	return combo


static func combo_of(t) -> Node:
	for node in t.current_scene.find_children("*", "Node", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == WHEEL_SCRIPT:
			return node
	return null


static func soles(t) -> Vector2:
	return t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


static func hurt_box(t) -> Rect2:
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# Until the combo is on `beat` (with `k` its spin, -1 any), or `frames` run out.
static func until_beat(t, combo: Node, beat: int, k := -1, frames := 60 * 30) -> bool:
	return await t.wait_until(func(): return combo.beat == beat and (k < 0 or combo.spin_k == k), frames)


# Until result `k` has started.
static func until_result(t, combo: Node, k: int) -> bool:
	return await t.wait_until(func(): return combo.result_log.size() > k, 60 * 30)


# The player put somewhere, still.
static func place(t, soles_at: Vector2) -> void:
	t.player.global_position = soles_at - Vector2(0, Layout.SOLES_OVER_ORIGIN)
	t.player.velocity = Vector2.ZERO
	await t.wait(2)


# Every frame, the player can't be hurt (i-frames): a run with no hit, for the payoff's hype and to reach a beat.
class Shield:
	var t
	var on := true

	func _init(suite) -> void:
		t = suite
		t.physics_frame.connect(_keep)

	func _keep() -> void:
		if on and is_instance_valid(t.player):
			t.player.is_invincible = true

	func stop() -> void:
		on = false
		if t.physics_frame.is_connected(_keep):
			t.physics_frame.disconnect(_keep)
		if is_instance_valid(t.player):
			t.player.is_invincible = false


# The arrow keys held, as a player holds them.
class Pad:
	var t
	var held: Array = []

	func _init(suite) -> void:
		t = suite

	func steer(to: Vector2, dead := 8.0) -> void:
		var want: Array = []
		if absf(to.x) > dead:
			want.append(KEY_RIGHT if to.x > 0.0 else KEY_LEFT)
		if absf(to.y) > dead:
			want.append(KEY_DOWN if to.y > 0.0 else KEY_UP)
		hold(want)

	func hold(want: Array) -> void:
		for code in held:
			if not want.has(code):
				t.release(code)
		for code in want:
			if not held.has(code):
				t.press(code)
		held = want

	func stop() -> void:
		hold([])


# Walking the player's origin to `point`, until there or `frames` run out.
static func walk_to(t, point: Vector2, frames := 60 * 6) -> void:
	var pad := Pad.new(t)
	for i in frames:
		var to: Vector2 = point - t.player.global_position
		if to.length() <= 8.0:
			break
		pad.steer(to)
		await t.physics_frame
	pad.stop()


static func walk_path(t, points: Array) -> void:
	for point: Vector2 in points:
		await walk_to(t, point)


# Origins that walk into the uppercut's reach of one of the pair and never the other's: under Liam, up to him from
# below; to Bixby along the top of him and down into him.
static func to_liam(t) -> Array:
	var under := Layout.LIAM_DOWN + Vector2(0, 30 - Layout.SOLES_OVER_ORIGIN)
	return [Vector2(t.player.global_position.x, under.y + 150.0), Vector2(under.x, under.y + 150.0), under]


static func to_bixby(t) -> Array:
	var into := Layout.BIXBY_DOWN + Vector2(0, 30 - Layout.SOLES_OVER_ORIGIN)
	return [Vector2(t.player.global_position.x, 640.0), Vector2(into.x, 640.0), into]


#KEEP-CLEARS

static func clear_of_jordan(rect: Rect2) -> bool:
	return not rect.intersects(Layout.MASK) and not rect.intersects(Layout.CORE)


static func to_screen(rect: Rect2) -> Rect2:
	var zoom: float = ScreenView.base_zoom
	return Rect2((rect.position - ScreenView.base_focus) * zoom + ScreenView.VIEW_SIZE / 2.0, rect.size * zoom)


static func clear_of_hud(rect: Rect2) -> bool:
	var on_screen := to_screen(rect)
	for keep_out: Rect2 in Layout.HUD_KEEP_OUT:
		if on_screen.intersects(keep_out.grow(Layout.HUD_CLEARANCE)):
			return false
	return true


static func in_view(rect: Rect2) -> bool:
	return ScreenView.base_rect().grow(-VIEW_MARGIN / ScreenView.base_zoom).encloses(rect)


# A sprite's drawn pixels (the used rect of its frame), in world px.
static func drawn_used(sprite: Sprite2D) -> Rect2:
	var image: Image = sprite.texture.get_image()
	var size := Vector2i(sprite.texture.get_size() / Vector2(sprite.hframes, sprite.vframes))
	var cell := Vector2i(sprite.frame % sprite.hframes, sprite.frame / sprite.hframes) * size
	var used := Rect2(image.get_region(Rect2i(cell, size)).get_used_rect())
	var frame_rect := sprite.get_rect()
	var local := Rect2(frame_rect.position + used.position, used.size)
	if sprite.flip_h:
		local.position.x = frame_rect.end.x - used.end.x
	return sprite.get_global_transform() * local


#THE TIERS

static func tier_layout(t) -> void:
	t.check(Layout.invariants().is_empty(), "JordanWheelLayout.invariants() is empty (%s)" % [Layout.invariants()])
	for boss: StringName in [&"liam", &"bixby"]:
		var spec: Dictionary = PuppetLayout.spec(boss)
		var off := []
		for anim_name: StringName in spec.anims:
			var row: Dictionary = spec.anims[anim_name]
			if not ResourceLoader.exists(row.sheet):
				continue
			var count := LiamArtLayout.strip_count(row.sheet, spec.frame)
			var frames: Array = row.frames
			var whole: bool = boss == &"liam" and LiamArtLayout.ANIMS.get(anim_name, {}).get("all", false)
			if (whole and frames.size() != count) or int(frames.max()) >= count:
				off.append([anim_name, frames.size(), count])
		t.check(off.is_empty(), "%s: every row's frames inside its live strip%s (%s)" % [boss,
			", his `all` poses as many as it holds" if boss == &"liam" else "", off])
	var combo: Node = await enter(t)
	var spinning: bool = await until_beat(t, combo, combo.Beat.SPIN, 0, 60 * 10)
	t.check(spinning, "the Avatar State is over and spin 1 begins")
	var liam: Node2D = combo.liam
	var bixby: Node2D = combo.bixby
	var bob: float = sin(TAU * Layout.LIAM_BOB_HZ * combo.wheel_clock) * Layout.LIAM_BOB
	var pivot: Vector2 = combo._liam_pivot() + Vector2(0, bob)
	t.log_p("Liam on %s, his float pivot at %s (bob %.1f); Bixby on %s, lifted %.0f; the wheel on %s" % [liam.global_position,
		pivot, bob, bixby.global_position, combo.bixby_lift, combo.wheel.global_position])
	t.check(liam.global_position == Layout.LIAM_FEET and pivot.distance_to(Layout.WHEEL_HUB) <= 1.0,
		"Liam on LIAM_FEET, his float pivot on the hub (%s)" % pivot)
	t.check(bixby.global_position == Layout.BIXBY_REST and is_equal_approx(combo.bixby_lift, Layout.BIXBY_LIFT),
		"Bixby on his rest, lifted %.0f" % Layout.BIXBY_LIFT)
	var floor_layer: Node2D = t.current_scene.get_node(FLOOR_LAYER)
	var strings: Node2D = t.current_scene.get_node(STRINGS)
	var wheel: Node2D = combo.wheel
	var wheel_z: int = floor_layer.z_index + wheel.z_index
	t.check(wheel.get_parent() == floor_layer and wheel.global_position == Layout.WHEEL_HUB and wheel_z <= strings.z_index
		and floor_layer.get_index() < strings.get_index(),
		"the wheel on the hub, on the Floor layer, under the strings (z %d, the strings' %d)" % [wheel_z, strings.z_index])
	t.check(strings.line_count() == 4 and strings.is_attached(liam) and strings.is_attached(bixby),
		"two strings each, Liam on the left hand's and Bixby on the right's (%d)" % strings.line_count())
	t.check(t.boss.string_pair(&"liam") == [0, 1] and t.boss.string_pair(&"bixby") == [2, 3],
		"Liam on the inner pair, Bixby on the outer (%s, %s)" % [t.boss.string_pair(&"liam"), t.boss.string_pair(&"bixby")])
	var radius := Layout.WHEEL_RADIUS * Layout.WHEEL_SCALE
	var pieces := {
		"the wheel": Rect2(Layout.WHEEL_HUB - Vector2.ONE * (radius + 12.0), Vector2.ONE * (radius + 12.0) * 2.0),
		"Liam lifted": drawn_used(liam.sprite),
		"Bixby at rest": drawn_used(bixby.sprite),
		"the icon": Rect2(Layout.icon_point(Layout.WHEEL_HUB) - Vector2(80, 40), Vector2(160, 80)),
	}
	for piece: String in pieces:
		var rect: Rect2 = pieces[piece]
		t.check(clear_of_jordan(rect) and clear_of_hud(rect) and in_view(rect),
			"%s in view, clear of Jordan's mask and core and 12 px of the HUD (world %s, screen %s)" % [piece, rect, to_screen(rect)])
	# Behind Bixby while spin 1 turns: he eases see-through within SEE_THROUGH_FADE, and back once they leave.
	var shield := Shield.new(t)
	var behind := Vector2(Layout.BIXBY_REST.x, Layout.BIXBY_REST.y - Layout.BIXBY_LIFT - 150.0)
	await place(t, behind)
	await t.wait(ceili(Layout.SEE_THROUGH_FADE / FRAME) + 3)
	var faded: float = bixby.modulate.a
	await place(t, Vector2(400, 1400))
	await t.wait(ceili(Layout.SEE_THROUGH_FADE / FRAME) + 3)
	t.check(faded <= Layout.SEE_THROUGH + 0.01 and is_equal_approx(bixby.modulate.a, 1.0),
		"Bixby see-through over the player (%.2f), solid again once they leave (%.2f)" % [faded, bixby.modulate.a])
	shield.stop()
	await until_beat(t, combo, combo.Beat.STOP, 0)
	var icons: Node2D = combo.wheel.icons
	var icon_ok: bool = is_instance_valid(icons) and clear_of_hud(Rect2(icons.global_position - Vector2(80, 40), Vector2(160, 80)))
	t.check(icon_ok, "the icon pops over his head, clear of the HUD (%s)" % (icons.global_position if is_instance_valid(icons) else Vector2.INF))


static func tier_wheel(t) -> void:
	# The actor, stepped a physics frame at a time, from every quarter to every element, each spin.
	await t.open_scene(FIGHT)
	await t.wait(2)
	var actor: Node2D = WheelActor.new()
	t.current_scene.get_node(FLOOR_LAYER).add_child(actor)
	actor.global_position = Layout.WHEEL_HUB
	var wrong := []
	var slow := []
	var ticks_off := []
	var surges := []
	var worst_last := INF
	for k in 3:
		for quarter in 4:
			for target: int in Layout.CLOCKWISE:
				actor.rotation_deg = quarter * 90.0
				var counted := {"ticks": 0}
				var on_tick := func(): counted.ticks += 1
				actor.ticked.connect(on_tick)
				var plan: Dictionary = actor.begin_spin(k, target)
				var last_quarter_at := -1.0
				var clock := 0.0
				var peak := 0.0
				var surged := false
				while actor.spinning:
					actor.advance(FRAME)
					clock += FRAME
					if clock > plan.up + plan.hold + FRAME:
						surged = surged or actor.omega > peak + 0.0001
					peak = actor.omega if clock > plan.up + plan.hold else maxf(peak, actor.omega)
					if last_quarter_at < 0.0 and Layout.spin_rotation(plan, clock) >= plan.to - 90.0:
						last_quarter_at = clock
				actor.ticked.disconnect(on_tick)
				var last := clock - last_quarter_at
				worst_last = minf(worst_last, last)
				if actor.position_now() != Layout.stop_position(target) or actor.element_under() != target \
						or actor.element_under(true) != Layout.NEXT_CLOCKWISE[target]:
					wrong.append([k, quarter, Layout.NAMES[target], actor.position_now()])
				if last < Layout.LAST_SEGMENT_MIN - FRAME:
					slow.append([k, quarter, Layout.NAMES[target], snappedf(last, 0.001)])
				if counted.ticks != Layout.ticks_at(plan.to) - Layout.ticks_at(plan.from):
					ticks_off.append([k, quarter, counted.ticks])
				if surged:
					surges.append([k, quarter])
	actor.queue_free()
	t.log_p("48 actor spins: the quickest last quarter turn %.3f s" % worst_last)
	t.check(wrong.is_empty(), "every spin stops on its element's quarter, under the pointer, its clockwise neighbour under the second (%s)" % [wrong])
	t.check(slow.is_empty(), "every last quarter turn takes %.2f s or more, +-1 frame (%s)" % [Layout.LAST_SEGMENT_MIN, slow])
	t.check(ticks_off.is_empty(), "a tick each time a peg passes the pointer (%s)" % [ticks_off])
	t.check(surges.is_empty(), "the spin-down only ever slows (%s)" % [surges])
	t.check(Layout.SPIN_TIME[0] > Layout.SPIN_TIME[1] and Layout.SPIN_TIME[1] > Layout.SPIN_TIME[2],
		"each spin quicker than the last (%s)" % [Layout.SPIN_TIME])
	# The deck.
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261006
	var last_double := -1
	var repeats := 0
	var incomplete := 0
	var seen := {}
	for run_index in 200:
		var dealt: Array = Layout.deal(rng, last_double)
		if dealt[2] == last_double:
			repeats += 1
		last_double = dealt[2]
		seen[dealt[2]] = seen.get(dealt[2], 0) + 1
		var covered := {dealt[0]: true, dealt[1]: true}
		for element: int in Layout.DOUBLES[dealt[2]]:
			covered[element] = true
		if covered.size() != 4:
			incomplete += 1
	t.log_p("200 dealt runs, the doubles dealt %s" % [seen])
	t.check(repeats == 0 and incomplete == 0 and seen.size() == 4,
		"200 dealt runs: all four elements each, a double never twice running, every double dealt (%d, %d)" % [repeats, incomplete])
	var neighbours := Layout.DOUBLES.all(func(pair: Array) -> bool: return Layout.NEXT_CLOCKWISE[pair[0]] == pair[1])
	t.check(neighbours, "every double is a primary and its clockwise neighbour")
	# A live run, its deck dealt.
	var combo: Node = await enter(t)
	var shield := Shield.new(t)
	await until_beat(t, combo, combo.Beat.CRASH, -1, 60 * 45)
	shield.stop()
	var spins: Array = combo.spin_log
	var landed := spins.size() == 3
	var durations := []
	for i in spins.size():
		var spin: Dictionary = spins[i]
		durations.append(snappedf(spin.stop_at - spin.at, 0.001))
		var elements: Array = combo.spins[i]
		landed = landed and spin.position == Layout.stop_position(elements[0]) and spin.under == elements[0]
		if elements.size() > 1:
			landed = landed and spin.under_second == elements[1]
	t.log_p("live spins %s" % [spins.map(func(s: Dictionary) -> Array: return [Layout.NAMES[s.target], s.position, snappedf(s.omega, 0.01), snappedf(s.last90, 0.001), s.ticks])])
	t.check(landed, "a live run's three spins land on the deck (%s)" % [combo.spins])
	var timed := durations.size() == 3
	for i in durations.size():
		timed = timed and absf(durations[i] - Layout.SPIN_TIME[i]) <= FRAME + 0.0001
	t.check(timed and durations[0] > durations[1] and durations[1] > durations[2],
		"each spin its SPIN_TIME (+-1 frame), quicker each time (%s)" % [durations])
	var reads: bool = combo.stop_log.size() == 3
	var holds := []
	for i in combo.stop_log.size():
		var stop: Dictionary = combo.stop_log[i]
		holds.append(snappedf(stop.live_at - stop.badge_at, 0.001))
		reads = reads and stop.live_at - stop.badge_at >= Layout.STOP_HOLD[i] - FRAME
	t.check(reads, "the icon is up STOP_HOLD before the result's first hazard is live (%s)" % [holds])


static func tier_switch(t) -> void:
	var was: bool = GodLayout.USE_ELEMENT_WHEEL
	GodLayout.USE_ELEMENT_WHEEL = false
	var off: Array[String] = GodLayout.rotation()
	t.check(off == TODAY and GodLayout.BASE_COMBOS == TODAY, "off: the rotation is today's four (%s)" % [off])
	GodLayout.COMBOS = off
	await t.open_scene(FIGHT)
	await t.wait(3)
	var names: Array = t.current_scene.get_node(GOD).state_machine.combos.map(func(c: Node) -> String: return String(c.name))
	t.check(names == ["JordanComboMaze", "JordanComboKegs", "JordanComboPortals", "JordanComboCircle"],
		"off: the god fight builds today's four, in order (%s)" % [names])
	GodLayout.USE_ELEMENT_WHEEL = true
	var on: Array[String] = GodLayout.rotation()
	t.check(on.size() == 5 and on.slice(0, 4) == TODAY and on[4] == GodLayout.WHEEL_COMBO,
		"on: five, the wheel last (%s)" % [on])
	GodLayout.COMBOS = on
	GodLayout.prefetch()
	var fetched: bool = GodLayout.prefetch_paths.has(GodLayout.WHEEL_COMBO) or GodLayout.prefetched.has(GodLayout.WHEEL_COMBO)
	GodLayout.release_prefetch()
	t.check(fetched, "on: prefetch() takes the wheel too")
	await t.open_scene(FIGHT)
	await t.wait(3)
	names = t.current_scene.get_node(GOD).state_machine.combos.map(func(c: Node) -> String: return String(c.name))
	t.check(names.size() == 5 and names[4] == "JordanComboWheel", "on: the god fight builds five, the wheel last (%s)" % [names])
	GodLayout.USE_ELEMENT_WHEEL = was
	GodLayout.COMBOS = GodLayout.rotation()
	t.check(GodLayout.USE_ELEMENT_WHEEL == was, "the switch put back as it was found (%s)" % was)


# The crash, the walk to `which` and the payoff; the hype paid on the way. Shielded, so every result is clean.
static func pay_off(t, which: StringName, deck: Array) -> Dictionary:
	var combo: Node = await enter(t, 100, deck)
	var shield := Shield.new(t)
	var hype0: float = t.player.hype.hype
	var crashing: bool = await until_beat(t, combo, combo.Beat.CRASH, -1, 60 * 45)
	var hype_crash: float = t.player.hype.hype
	var walking: bool = await until_beat(t, combo, combo.Beat.WALK, -1, 60 * 4)
	shield.stop()
	var liam: Node2D = combo.liam
	var bixby: Node2D = combo.bixby
	await t.wait(45)
	var out := {combo = combo, crashing = crashing, walking = walking, hype0 = hype0, hype_crash = hype_crash,
		liam_at = liam.global_position, liam_lift = combo.liam_lift, liam_anim = liam.current_anim,
		bixby_at = bixby.global_position, bixby_lift = combo.bixby_lift, bixby_anim = bixby.current_anim,
		punchable = liam.punchable and bixby.punchable, stars = combo.stars.size(), floored = combo.flooring,
		hud = t.boss.health_bar.modulate.a, jordan = t.boss.boss_health}
	await walk_path(t, to_liam(t) if which == &"liam" else to_bixby(t))
	await t.wait_until(func(): return combo.beat == combo.Beat.PAYOFF, 60 * 2)
	out.target = combo.target.boss if is_instance_valid(combo.target) else &""
	out.other_punchable = (bixby if which == &"liam" else liam).punchable
	var top := {"y": INF, "headroom": INF, "puppet": combo.target}
	var watch := func():
		var puppet = top.puppet
		if is_instance_valid(puppet) and puppet.is_juggled():
			top.y = minf(top.y, (puppet.sprite.get_global_transform() * puppet.sprite.get_rect()).position.y)
			top.headroom = minf(top.headroom, puppet.juggle_headroom())
	t.physics_frame.connect(watch)
	for i in 3:
		t.tap(KEY_Q)
		await t.wait(PUNCH_GAP)
	await t.wait_until(func(): return t.player.finisher.is_active(), 60 * 2)
	await t.mash_tiered(t.TIER_PASS_FRAMES[2])
	await t.wait_until(func(): return combo.bars >= 0, 60 * 10)
	out.bars = combo.bars
	out.jordan_after = t.boss.boss_health
	await t.wait_until(func(): return t.sm.current_state != combo, 60 * 8)
	t.physics_frame.disconnect(watch)
	out.apex = top.y
	out.headroom = top.headroom
	await t.wait(3)
	out.idle = t.sm.current_state.name == "Idle"
	out.after = {puppets = combo.puppets.size(), hazards = t.get_nodes_in_group(GodLayout.HAZARD_GROUP).filter(
		func(n: Node) -> bool: return not n.is_queued_for_deletion()).size(), locked = t.player.is_action_locked}
	return out


static func tier_payoff(t) -> void:
	for which: StringName in [&"liam", &"bixby"]:
		var run: Dictionary = await pay_off(t, which, [WATER, EARTH, 0] if which == &"liam" else [FIRE, AIR, 2])
		t.log_p("%s: %s" % [which, run])
		var paid: float = run.hype_crash - run.hype0
		var owed := Layout.HYPE_RESULT * 3 + Layout.HYPE_CLEAN
		t.check(run.crashing and absf(paid - owed) <= 0.01,
			"a clean run pays HYPE_RESULT a result and HYPE_CLEAN (%.1f of %.1f)" % [paid, owed])
		t.check(run.walking and run.liam_at == Layout.LIAM_DOWN and is_equal_approx(run.liam_lift, 0.0) and run.liam_anim == &"downed",
			"the crash: Liam down on LIAM_DOWN, downed (%s, %.1f, %s)" % [run.liam_at, run.liam_lift, run.liam_anim])
		t.check(run.bixby_at == Layout.BIXBY_DOWN and is_equal_approx(run.bixby_lift, 0.0) and run.bixby_anim == &"recover",
			"the crash: Bixby down on BIXBY_DOWN, recovering (%s, %.1f, %s)" % [run.bixby_at, run.bixby_lift, run.bixby_anim])
		t.check(run.punchable and run.stars == 2 and not run.floored and is_equal_approx(run.hud, 1.0),
			"both punchable with stars, the stamina floor off, the HUD up")
		t.check(run.target == which and not run.other_punchable, "a walk to %s: he is the one (%s)" % [which, run.target])
		t.check(run.bars == 3 and run.jordan_after == run.jordan - 3,
			"three presses and a three-bar mash on %s: Jordan -3 (%d bars, %d -> %d)" % [which, run.bars, run.jordan, run.jordan_after])
		t.log_p("%s's juggle: its frame's top at world y %.0f (screen %.0f), its headroom %.0f px" % [which, run.apex, (run.apex + 6.0) / 1.5, run.headroom])
		t.check(run.idle and run.after.puppets == 0 and run.after.hazards == 0 and not run.after.locked,
			"then the recall and Idle, nothing left (%s)" % [run.after])


# What a cut must leave: nothing of the attack's own, the player free and whole.
static func left_behind(t, combo: Node) -> Dictionary:
	var stage: Node = t.current_scene.get_node_or_null(STAGE)
	var tells: Array = []
	for node in (stage.get_children() if stage else []):
		if String(node.name).begins_with("ParryTell") and not node.is_queued_for_deletion():
			tells.append(node)
	var defense: Node = t.defense
	return {
		released = combo.released,
		hazards = t.get_nodes_in_group(GodLayout.HAZARD_GROUP).filter(func(n: Node) -> bool: return not n.is_queued_for_deletion()).size(),
		tells = tells.size(), drift = t.player.drift_velocity, ice = t.player.on_ice, grabbed = t.player.is_grabbed,
		visible = t.player.sprite.visible, locked = t.player.is_action_locked,
		watching = defense.stamina_changed.is_connected(combo._on_stamina_changed),
		hits_watched = defense.hit_taken.is_connected(combo._on_hit_taken),
	}


static func clean(gone: Dictionary) -> bool:
	return gone.released and gone.hazards == 0 and gone.tells == 0 and gone.drift == Vector2.ZERO and not gone.ice \
		and not gone.grabbed and gone.visible and not gone.locked and not gone.watching and not gone.hits_watched


static func tier_cleanup(t) -> void:
	# [what it is cut at, how]: every beat, by each of the four ways.
	var cuts := [
		[&"spin0", "finish"], [&"result0", "death"], [&"spin1", "defeat"], [&"result1", "scene"],
		[&"spin2", "death"], [&"result2", "finish"], [&"crash", "defeat"], [&"walk", "finish"], [&"payoff", "death"],
	]
	for cut: Array in cuts:
		await cut_at(t, cut[0], cut[1], [AIR, WATER, 3])
	# Mid-swallow, mid-bite, mid-second bite, mid-snap after the wave, and the undertow mid-wave and mid-pull.
	await cut_at(t, &"swallow", "finish", [AIR, WATER, 3])
	await cut_at(t, &"bite", "defeat", [AIR, WATER, 3])
	await cut_at(t, &"bite2", "scene", [AIR, WATER, 3])
	await cut_at(t, &"breach", "finish", [WATER, EARTH, 0])
	await cut_at(t, &"undertow", "death", [FIRE, EARTH, 1])
	await cut_at(t, &"jaws", "defeat", [FIRE, EARTH, 1])
	# His kill mid-wheel with his final beam on: the wheel hands over to it.
	await cut_at(t, &"result0", "beam", [FIRE, EARTH, 1])
	await cut_at(t, &"swallow", "beam", [AIR, WATER, 3])


# One run cut at `point` by `how`, and checked.
static func cut_at(t, point: StringName, how: String, deck: Array) -> void:
	var combo: Node = await enter(t, 100, deck)
	var shield := Shield.new(t)
	var reached := false
	match point:
		&"spin0", &"spin1", &"spin2":
			reached = await until_beat(t, combo, combo.Beat.SPIN, int(String(point).right(1)))
			await t.wait(20)
		&"result0", &"result1", &"result2":
			reached = await until_beat(t, combo, combo.Beat.RESULT, int(String(point).right(1)))
			await t.wait(70)
		&"crash":
			reached = await until_beat(t, combo, combo.Beat.CRASH, -1, 60 * 45)
			await t.wait(20)
		&"walk":
			reached = await until_beat(t, combo, combo.Beat.WALK, -1, 60 * 45)
		&"swallow":
			shield.stop()
			combo.pinned_maw = 1
			await until_beat(t, combo, combo.Beat.STOP, 0)
			await place(t, Layout.MAWS[1] + Vector2(-Layout.AIR_START_MIN - 40.0, 0))
			reached = await t.wait_until(func(): return not combo.air_log.is_empty() and combo.air_log[-1].swallowed, 60 * 8)
			await t.wait(12)
			reached = reached and t.player.is_grabbed
		&"bite":
			combo.pinned_maw = 0
			reached = await t.wait_until(func(): return not combo.air_log.is_empty() and combo.air_log[-1].bite_at >= 0.0, 60 * 10)
			await t.wait(8)
		&"bite2":
			combo.pinned_maw = 0
			reached = await t.wait_until(func(): return not combo.air_log.is_empty() and combo.air_log[-1].bites.size() == 2, 60 * 10)
			await t.wait(8)
			reached = reached and combo.air_log[-1].bites[1].contact_at < 0.0
		&"breach":
			reached = await t.wait_until(func(): return not combo.water_log.is_empty() and not combo.water_log[-1].bite.is_empty(), 60 * 10)
			await t.wait(8)
			reached = reached and combo.water_log[-1].bite.contact_at < 0.0
		&"undertow":
			reached = await t.wait_until(func(): return combo.result_log.size() == 3 and combo.result.has("water") and combo.result.water.rolled, 60 * 40)
			await t.wait(20)
			reached = reached and not combo.result.water.cleared
		&"jaws":
			reached = await t.wait_until(func(): return combo.result.has("air") and combo.result.air.undertow and combo.result.air.pulling, 60 * 40)
			await t.wait(20)
		&"payoff":
			reached = await until_beat(t, combo, combo.Beat.WALK, -1, 60 * 45)
			shield.stop()
			await walk_path(t, to_liam(t))
			for i in 3:
				t.tap(KEY_Q)
				await t.wait(PUNCH_GAP)
			reached = reached and await t.wait_until(func(): return t.player.finisher.is_active(), 60 * 2)
			await t.wait(20)
	shield.stop()
	t.check(reached, "%s: reached" % point)
	var strings: Node = t.current_scene.get_node(STRINGS)
	match how:
		"death":
			t.player.playerHealth = 0
			await t.wait_until(func(): return t.root.has_node("FightOutro"), 30)
			await t.wait(3)
			var gone := left_behind(t, combo)
			t.log_p("%s cut by the player's death: %s" % [point, gone])
			t.check(clean(gone) and combo.puppets.is_empty() and strings.line_count() == 0,
				"%s, the player's death: nothing left, no puppets or strings" % point)
			await t.wait_until(func(): return t.current_scene != null and t.current_scene.scene_file_path == DEFEAT, 60 * 10)
		"defeat", "beam":
			# His defeat as it was ("defeat", the final beam pinned off) or into his final beam ("beam", pinned on), the
			# switch put back as it was found once the kill has been decided.
			var beam_was: bool = GodLayout.USE_FINAL_BEAM
			GodLayout.USE_FINAL_BEAM = how == "beam"
			var mine: Array = t.get_nodes_in_group(GodLayout.HAZARD_GROUP).filter(func(n: Node) -> bool: return not n.is_queued_for_deletion())
			var puppet: Node = combo.puppets.get(&"liam")
			t.boss.boss_health = 1
			t.boss.take_uppercut(puppet)
			var decided: bool = await t.wait_until(func(): return t.boss.defeated or t.boss.get("beaten") == true, 30)
			GodLayout.USE_FINAL_BEAM = beam_was
			await t.wait(3)
			var gone := left_behind(t, combo)
			var left := 0
			for node in mine:
				if is_instance_valid(node) and not node.is_queued_for_deletion():
					left += 1
			var kept: Array = t.boss.defeat_puppets.filter(func(p) -> bool: return is_instance_valid(p))
			var whole := true
			for kept_puppet: Node2D in kept:
				whole = whole and kept_puppet.modulate == Color.WHITE and kept_puppet.sprite.position == kept_puppet.sprite_base_position
			if how == "beam":
				t.log_p("%s cut by his kill into his final beam: beaten %s, %s, %d of the wheel's %d hazards left, %d kept" % [point,
					t.boss.get("beaten"), gone, left, mine.size(), kept.size()])
				# The beam holds the player: its lock is its own.
				gone.locked = false
				t.check(decided and t.boss.get("beaten") == true and not t.boss.defeated and clean(gone) and left == 0 and whole,
					"%s, his kill with the final beam on: the wheel hands over, nothing of it left, the puppets whole" % point)
			else:
				t.log_p("%s cut by his defeat: %s, %d of the wheel's %d hazards left, %d kept for it" % [point, gone, left, mine.size(),
					kept.size()])
				t.check(decided and t.boss.defeated and clean(gone) and left == 0 and whole,
					"%s, his defeat (final beam off): nothing left, the puppets handed over whole" % point)
		"scene":
			var at_exit := {"released": false}
			combo.tree_exited.connect(func(): at_exit.released = combo.released)
			await t.open_scene(MENU)
			await t.wait(3)
			t.check(at_exit.released, "%s, a scene change: released as it went" % point)
		"finish":
			t.sm.on_child_transition(combo, "Idle")
			await t.wait(3)
			var gone := left_behind(t, combo)
			t.log_p("%s cut by a finish: %s" % [point, gone])
			t.check(clean(gone) and combo.puppets.is_empty() and strings.line_count() == 0,
				"%s, a finish: nothing left, no puppets or strings" % point)
			combo.release()
			t.check(clean(left_behind(t, combo)), "%s: release() again changes nothing" % point)
			# The next one starts clean.
			t.sm.start_next_attack()
			var again: bool = await until_beat(t, combo, combo.Beat.SPIN, 0, 60 * 10)
			t.check(again and combo.spin_log.size() == 1 and combo.result_log.is_empty() and combo.hits == 0,
				"%s: the next run starts clean" % point)


#THE MODEL BOT

# The model player through a whole wheel, a physics step at a time (tick): every answer on a reaction (a new player's or
# a learned one's) or with a timing error off the window's middle (40 ms learned, 50 ms new), acting on its own clock.
# The fire: a walk into the column; the water (and the undertow's first part): a dash straight up through the wave; the
# earth (and the landslide's aftershock): a dash straight in at each ring; the air: a walk away from the maw; every bite,
# the jaws' two and the shark's snap after the wave: a parry a reaction after its badge. On a `first` run the first
# meeting of each answer fails at the plan's first-time rates (fire 0.35, water 0.4, a ring 0.25, the swallow 0.2, the
# bite 0.2): that answer isn't given. `empty` drains the stamina bar before every dash; `perfect` answers on the new
# player's mean reaction with no timing error (the answer each result is built on).
class Bot:
	const FIRST_FAILS := {&"fire": 0.35, &"water": 0.4, &"ring": 0.25, &"swallow": 0.2, &"bite": 0.2}
	var t
	var combo: Node
	var rng: RandomNumberGenerator
	var learned := false
	var first := false
	var empty := false
	var perfect := false
	var pad
	var seen := {}
	var k := -1
	var plan := {}
	var dashed := {}
	# Each bite met, by its badge's clock: {press (seconds after the badge), fail, pressed}.
	var bitten := {}
	var releases: Array = []
	var dashes: Array[Dictionary] = []
	var frame := 0

	func _init(suite, attack: Node, seed_value: int, is_learned: bool, is_first := false) -> void:
		t = suite
		combo = attack
		rng = RandomNumberGenerator.new()
		rng.seed = seed_value
		learned = is_learned
		first = is_first
		pad = Pad.new(suite)

	func react() -> float:
		if perfect:
			return Layout.REACTION
		return maxf(0.12, rng.randfn(0.20, 0.04) if learned else rng.randfn(0.25, 0.05))

	func error() -> float:
		return 0.0 if perfect else rng.randfn(0.0, 0.04 if learned else 0.05)

	# The first meeting of `kind` on a first run fails at its rate.
	func fails(kind: StringName) -> bool:
		var meetings: int = seen.get(kind, 0)
		seen[kind] = meetings + 1
		return first and meetings == 0 and rng.randf() < FIRST_FAILS[kind]

	func stop() -> void:
		pad.stop()
		for entry: Array in releases:
			t.release(entry[0])
		releases.clear()

	func dash(key: int) -> void:
		if empty:
			t.defense.drain_stamina(t.defense.max_stamina)
		dashes.append({at = combo.wheel_clock, stamina = t.defense.stamina, key = key})
		t.press(key)
		t.tap(KEY_W)
		releases.append([key, frame + 4])

	func tick() -> void:
		frame += 1
		for entry: Array in releases.duplicate():
			if frame >= entry[1]:
				t.release(entry[0])
				releases.erase(entry)
		if combo.beat != combo.Beat.RESULT or combo.result_log.is_empty():
			pad.stop()
			return
		var now: int = combo.result_log.size() - 1
		if now != k:
			k = now
			_plan()
		_bites()
		var into: float = combo.wheel_clock - float(combo.result_log[k].at)
		# The undertow's wave comes before its jaws.
		if combo.result.has("water") and not combo.result.water.cleared:
			_water(into)
			return
		match int(plan.primary):
			FIRE:
				_fire(into)
			WATER:
				_water(into)
			EARTH:
				_rings()
			AIR:
				_air(into)

	func _plan() -> void:
		var elements: Array = combo.result_log[k].elements
		plan = {primary = elements[0], secondary = elements[1] if elements.size() > 1 else -1, react = react(), err = error(),
			fail = false, wave_fail = false, water_dashed = false}
		match int(plan.primary):
			FIRE:
				plan.fail = fails(&"fire")
			WATER:
				plan.wave_fail = fails(&"water")
			AIR:
				if int(plan.secondary) == WATER:
					plan.wave_fail = fails(&"water")
				plan.fail = fails(&"swallow")

	# A parry a reaction after each badge goes up, unless it is a first meeting that fails.
	func _bites() -> void:
		for bite: Dictionary in combo.bite_log:
			var key: float = bite.clock
			if not bitten.has(key):
				bitten[key] = {press = react(), fail = fails(&"bite"), pressed = false}
			var mine: Dictionary = bitten[key]
			if mine.pressed or mine.fail or float(bite.contact_clock) >= 0.0:
				continue
			if combo.wheel_clock >= key + float(mine.press):
				mine.pressed = true
				t.tap(KEY_SHIFT)

	func _fire(into: float) -> void:
		var fire: Dictionary = combo.fire_log[-1]
		if plan.fail or into < plan.react:
			pad.stop()
			return
		var x: float = t.player.global_position.x
		var span: Vector2 = fire.span
		pad.steer(Vector2(clampf(x, span.x + 40.0, span.y - 40.0) - x, 0.0), 4.0)

	func _water(_into: float) -> void:
		var water: Dictionary = combo.water_log[-1]
		pad.stop()
		if not water.cleared:
			if plan.wave_fail or plan.water_dashed or not is_instance_valid(water.wave) or not water.wave.rolling:
				return
			var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
			var top: float = (shape.global_transform * shape.shape.get_rect()).position.y
			var reach := Layout.WAVE_IMMUNITY * Layout.WAVE_SPEED - (Layout.WAVE_H + Layout.PLAYER_HURT_HEIGHT - Layout.DASH_DISTANCE)
			if water.wave.front_y >= top - reach / 2.0 + float(plan.err) * Layout.WAVE_SPEED:
				plan.water_dashed = true
				dash(KEY_UP)
			return
		_rings()

	# Straight in at each ring born this result, as its band comes within the window's middle (off by the timing error).
	func _rings() -> void:
		pad.stop()
		var middle := (Layout.DASH_DISTANCE + Layout.RING_SPEED * Layout.DASH_IMMUNITY) / 2.0
		var soles_at: Vector2 = t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)
		# A slam's shadow on them: out of its ring's birth, a reaction after it shows.
		var slams: Array = []
		if combo.result.has("earth"):
			slams = combo.result.earth.slams
		elif combo.result.has("water"):
			slams = combo.result.water.slams
		var into: float = combo.wheel_clock - float(combo.result_log[k].at)
		for slam: Dictionary in slams:
			if slam.phase < 2 or slam.phase >= 4 or into < float(slam.tell_at) + float(plan.react):
				continue
			if Layout.ring_distance(slam.spot, soles_at) < CombinedLayout.RING_START_RADIUS + Layout.RING_HALF_WIDTH + 60.0:
				pad.steer(soles_at - Vector2(slam.spot))
				return
		for entry: Dictionary in combo.ring_log:
			if not is_instance_valid(entry.node) or dashed.has(entry.born) or entry.born < float(combo.result_log[k].at):
				continue
			var ring: Node2D = entry.node
			if not dashed.has(-entry.born):
				dashed[-entry.born] = {err = error(), fail = fails(&"ring")}
			var mine: Dictionary = dashed[-entry.born]
			var between: float = Layout.ring_distance(ring.global_position, soles_at) - ring.radius
			if between > middle + float(mine.err) * Layout.RING_SPEED or between < -Layout.RING_HALF_WIDTH:
				continue
			dashed[entry.born] = true
			if mine.fail:
				continue
			var off: Vector2 = ring.global_position - soles_at
			dash((KEY_RIGHT if off.x > 0.0 else KEY_LEFT) if absf(off.x) >= absf(off.y) / 0.36 else (KEY_DOWN if off.y > 0.0 else KEY_UP))
			return

	# Away from the maw a reaction after the pull starts, until the first badge; the bites are _bites()'.
	func _air(into: float) -> void:
		if not combo.result.has("air"):
			pad.stop()
			return
		var air: Dictionary = combo.result.air
		if air.bite_at < 0.0:
			if plan.fail or into - float(air.at) < Layout.PULL_START + float(plan.react):
				pad.stop()
				return
			var soles_at: Vector2 = t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)
			pad.steer(soles_at - Vector2(air.maw))
			return
		pad.stop()


# The bot through a whole wheel, to its walk (or the player's death); [hits by id with damage, seconds, dashes].
static func play_wheel(t, combo: Node, bot: Bot) -> void:
	while combo.beat != combo.Beat.WALK and combo.beat != combo.Beat.OFF and t.player.playerHealth > 0:
		bot.tick()
		await t.physics_frame
	bot.stop()


#DOUBLES

# The deck that ends on double `d`: its two singles first.
static func deck_for(d: int) -> Array:
	var singles: Array = Layout.CLOCKWISE.filter(func(e: int) -> bool: return not Layout.DOUBLES[d].has(e))
	return [singles[0], singles[1], d]


# The state as the double's result clears: {at, ice, drift, wind, pulling, rings_past}.
static func watch_clear(t, combo: Node, out: Dictionary) -> void:
	if not out.is_empty() or combo.beat != combo.Beat.CLEAR or combo.result_log.size() < 3:
		return
	var rings_past := true
	for entry: Dictionary in combo.ring_log:
		rings_past = rings_past and combo._ring_past(entry.node)
	out.merge({at = combo.wheel_clock, ice = t.player.on_ice, wind = combo.wind_streaks.size(),
		pulling = is_instance_valid(combo.suction), rings_past = rings_past, holding = combo.holding})


static func tier_doubles(t) -> void:
	# F6 (the landslide): from the wave's last required dash at any standing point to its aftershock's ring, DASH_GAP_MIN
	# or more (1.0 s in the plan, lowered with the retune for the user's "far too easy", 2026-10-06).
	var least := INF
	for start: Vector2 in grid():
		var wave_at: float = Layout.WAVE_TELL + (start.y - Layout.PLAYER_HURT_HEIGHT - Layout.FLOOR.position.y) / Layout.WAVE_SPEED
		var clear_at: float = Layout.WAVE_TELL + (Layout.FLOOR.size.y + Layout.WAVE_H) / Layout.WAVE_SPEED
		var spot := Layout.aftershock_for(start)
		var ring_at: float = clear_at + Layout.aftershock_after_clear() + maxf(Layout.ring_distance(spot, start) - CombinedLayout.RING_START_RADIUS, 0.0) / Layout.RING_SPEED
		least = minf(least, ring_at - wave_at)
	t.log_p("the landslide: the least gap from the wave to its aftershock's ring at a standing point %.3f s" % least)
	t.check(least >= Layout.DASH_GAP_MIN - 0.0001, "F6: the wave and the aftershock's ring %.2f s or more apart wherever the player stands (%.3f)" % [
		Layout.DASH_GAP_MIN, least])
	for d in Layout.DOUBLES.size():
		for empty: bool in ([false, true] if d == 2 else [false]):
			var combo: Node = await enter(t, 100, deck_for(d))
			var bot := Bot.new(t, combo, 30 + d, true)
			bot.perfect = true
			bot.empty = empty
			var at_clear := {}
			var iced := {"ever": false}
			var watch := func():
				watch_clear(t, combo, at_clear)
				iced.ever = iced.ever or t.player.on_ice
			t.physics_frame.connect(watch)
			await play_wheel(t, combo, bot)
			t.physics_frame.disconnect(watch)
			t.check(not iced.ever, "no slick: the player is never on ice")
			if d == 1:
				var water: Dictionary = combo.water_log[-1]
				var air: Dictionary = combo.air_log[-1]
				var kinds: Array = air.bites.map(func(b: Dictionary) -> StringName: return b.kind)
				t.log_p("the undertow: the wave rolled at %.3f and was off the floor at %.3f; the jaws from %.3f, their badges at %s" % [
					Layout.WAVE_TELL, water.cleared_at, air.at, air.bites.map(func(b: Dictionary) -> float: return snappedf(b.at, 0.001))])
				t.check(water.rolled and air.undertow and absf(float(air.at) - float(water.cleared_at)) <= FRAME + 0.0001
					and float(air.bites[0].at) > float(water.cleared_at) and kinds == [&"jaws", &"jaws2"] and water.bite.is_empty(),
					"the undertow: the wave, then the jaws once it is off the floor, their two bites and no snap after the wave")
			if d == 2:
				var water: Dictionary = combo.water_log[-1]
				var bite: Dictionary = water.bite
				var slam_at: float = water.slams[0].slam_at if not water.slams.is_empty() else -1.0
				t.log_p("the landslide: the wave off the floor at %.3f, the snap's badge at %.3f and its contact at %.3f, the aftershock's slam at %.3f" % [
					water.cleared_at, bite.at, bite.contact_at, slam_at])
				t.check(absf(float(bite.at) - float(water.cleared_at) - Layout.BREACH_RISE) <= FRAME + 0.0001
					and absf(float(bite.contact_at) - float(bite.at) - Layout.BITE_TELL) <= FRAME + 0.0001
					and slam_at >= float(bite.contact_at) + Layout.RECOIL_TIME + Layout.AFTERSHOCK_DELAY - FRAME,
					"the landslide: the wave, then the snap BREACH_RISE after it is off the floor, then the aftershock once he has recoiled")
			var names: Array = Layout.DOUBLES[d].map(func(e: int) -> StringName: return Layout.NAMES[e])
			var floored: bool = bot.dashes.all(func(dash: Dictionary) -> bool: return dash.stamina >= Layout.STAMINA_FLOOR - 0.01)
			t.log_p("%s%s: hits %s; badges at most %d; dashes %s; at the double's clear %s" % [names, " (the bar emptied before every dash)" if empty else "",
				combo.hit_log, combo.max_badges, bot.dashes.map(func(dash: Dictionary) -> float: return snappedf(dash.stamina, 0.1)), at_clear])
			t.check(combo.hit_log.is_empty(), "%s%s: the bot answering each result clean takes nothing" % [names, ", every dash begun on an emptied bar" if empty else ""])
			t.check(combo.max_badges <= 1, "F9: one red or yellow badge at most in any frame (%d)" % combo.max_badges)
			t.check(floored, "F10: every dash made on STAMINA_FLOOR or more")
			t.check(not at_clear.is_empty() and not at_clear.ice and at_clear.wind == 0 and not at_clear.pulling and at_clear.rings_past
				and not at_clear.holding, "F11: at the double's clear no ice, no wind, no pull, its rings past")


#LAZY

# A run with the player doing nothing but `act` each step from `where`: [half-hearts lost, hits by result index].
static func lazy_run(t, where: Vector2, act := Callable(), deck: Array = [WATER, EARTH, 0]) -> Array:
	var combo: Node = await enter(t, 100, deck)
	await until_beat(t, combo, combo.Beat.STOP, 0)
	await place(t, where)
	var health: int = t.player.playerHealth
	while combo.beat != combo.Beat.WALK and combo.beat != combo.Beat.OFF and t.player.playerHealth > 0:
		if act.is_valid():
			act.call(combo)
		await t.physics_frame
	var by_result := []
	for result: Dictionary in combo.result_log:
		by_result.append(result.hits)
	return [health - t.player.playerHealth, by_result]


static func tier_lazy(t) -> void:
	# F12: nobody starts covered.
	await enter(t, 100, [WATER, EARTH, 0])
	var start := Layout.LIAM_FEET + Vector2(0, 20)
	var spot := Layout.start_spot(start, t.player.ring_origins)
	t.check(not Layout.start_clear(start) and Layout.start_clear(spot) and spot.distance_to(start) <= 260.0,
		"F12: a player standing on Liam's mark is blinked to the nearest clear spot (%s)" % spot)
	var least := INF
	for at: Vector2 in grid():
		least = minf(least, Layout.aftershock_for(at).distance_to(at))
	t.check(least >= Layout.AFTERSHOCK_MIN, "F12: the aftershock lands AFTERSHOCK_MIN or more off the player (%.0f)" % least)
	# F5: standing at spawn, every result reaches them, on each of the four decks; F14: on the four together, most of a
	# health bar a run. A whole one before the retune (the user's "far too easy", 2026-10-06): its rings, now closer
	# together than the i-frames, can reach someone standing still inside those of the one before, so one of three is free.
	var spawn := GodLayout.PLAYER_START + Vector2(0, Layout.SOLES_OVER_ORIGIN)
	var losses := []
	for d in Layout.DOUBLES.size():
		var idle: Array = await lazy_run(t, spawn, Callable(), deck_for(d))
		losses.append(idle[0])
		t.log_p("idle at spawn %s, deck %s: lost %d half-hearts, hits by result %s" % [spawn, deck_for(d), idle[0], idle[1]])
		t.check(idle[1].size() == 3 and idle[1].all(func(n: int) -> bool: return n >= 1), "F5: standing still, every result reaches them")
	var mean: float = losses.reduce(func(a: int, b: int) -> int: return a + b, 0) / float(losses.size())
	t.check(mean >= 7.0, "F14: idle at spawn loses most of a health bar a run, 7 half-hearts or more on average over the four decks (%.2f; %s)" % [
		mean, losses])
	# F14: the corners, under Liam and on the wheel's hub each lose 5 or more.
	var floor_rect: Rect2 = Layout.FLOOR
	var campers := {
		"top left": floor_rect.position + Vector2(30, 60), "top right": Vector2(floor_rect.end.x - 30, floor_rect.position.y + 60),
		"bottom left": Vector2(floor_rect.position.x + 30, floor_rect.end.y - 10), "bottom right": floor_rect.end - Vector2(30, 10),
		"under Liam": Layout.LIAM_FEET + Vector2(0, 60), "on the hub": Layout.WHEEL_HUB,
	}
	for name: String in campers:
		var run: Array = await lazy_run(t, campers[name])
		t.log_p("camping %s %s: lost %d, hits by result %s" % [name, campers[name], run[0], run[1]])
		t.check(run[0] >= 5, "F14: camping %s loses 5 half-hearts or more (%d)" % [name, run[0]])
	# F14: a dash every 0.6 s, a random way, on its own clock.
	var rng := RandomNumberGenerator.new()
	rng.seed = 14
	var spam := {next = rng.randf() * 0.6, keys = []}
	var dasher := func(c: Node) -> void:
		for key: int in spam.keys:
			t.release(key)
		spam.keys = []
		if c.wheel_clock >= spam.next:
			spam.next += 0.6
			var key: int = [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN][rng.randi_range(0, 3)]
			t.press(key)
			t.tap(KEY_W)
			spam.keys = [key]
	var spammed: Array = await lazy_run(t, Vector2(700, 1100), dasher)
	t.log_p("the dash spammer: lost %d, hits by result %s" % [spammed[0], spammed[1]])
	t.check(spammed[0] >= 1, "F14: a dash every 0.6 s loses at least the learned bot's ~1 half-heart a run (%d)" % spammed[0])


#RATING

const RATING_RUNS := {"learned": 12, "first": 8, "second": 8}
const MASH_RATE := 8.5


# The payoff as the model plays it: a reaction, a walk to the nearer of the pair, the three presses, and the tiered
# mash at MASH_RATE presses a second (15% jitter) on its own clock. The bars it banked.
static func model_payoff(t, combo: Node, rng: RandomNumberGenerator) -> int:
	await t.wait(maxi(1, roundi(reaction(rng, true) * 60.0)))
	var liam_far: float = t.player.global_position.distance_to(Layout.LIAM_DOWN)
	var bixby_far: float = t.player.global_position.distance_to(Layout.BIXBY_DOWN)
	await walk_path(t, to_liam(t) if liam_far <= bixby_far else to_bixby(t))
	if combo.beat != combo.Beat.PAYOFF:
		return 0
	await t.wait(maxi(1, roundi(reaction(rng, true) * 60.0)))
	for i in GodLayout.PUNCH_OUT_PRESSES:
		t.tap(KEY_Q)
		await t.wait(maxi(7, roundi(rng.randfn(0.13, 0.02) * 60.0)))
	var finisher: Node = t.player.get_node("Finisher")
	await t.wait_until(func(): return finisher.prompt_visible or not finisher.is_active(), 60 * 3)
	await t.wait(maxi(1, roundi(reaction(rng, true) * 60.0)))
	finisher.min_press_interval = 0.0
	var pair: Array = finisher.mash_actions()
	var presses := 0
	var next_at := 0.0
	var clock := 0.0
	while finisher.phase == t.FINISHER_DAZED or finisher.phase == t.FINISHER_CHARGING:
		if clock >= next_at:
			t.tap(t.MASH_KEYS[pair[presses % 2]])
			presses += 1
			next_at += maxf(0.05, (1.0 / MASH_RATE) * (1.0 + rng.randfn(0.0, 0.15)))
		await t.physics_frame
		clock += FRAME
	await t.wait_until(func(): return combo.bars >= 0, 60 * 10)
	return maxi(combo.bars, 0)


static func tier_rating(t) -> void:
	for profile: String in RATING_RUNS:
		var rows: Array = []
		var deck_rng := RandomNumberGenerator.new()
		deck_rng.seed = 7
		var last_double := -1
		for run_index in RATING_RUNS[profile]:
			var deck: Array = Layout.deal(deck_rng, last_double)
			last_double = deck[2]
			var combo: Node = await enter(t, 100, deck)
			var entered: int = t.frame
			var bot := Bot.new(t, combo, 100 * run_index + profile.length(), profile == "learned", profile == "first")
			var health: int = t.player.playerHealth
			await play_wheel(t, combo, bot)
			var lost: int = health - t.player.playerHealth
			var bars: int = await model_payoff(t, combo, bot.rng)
			await t.wait_until(func(): return t.sm.current_state != combo, 60 * 10)
			var by_id := {}
			for hit: Dictionary in combo.hit_log:
				by_id[hit.id] = by_id.get(hit.id, 0) + hit.damage
			var results := {}
			for result: Dictionary in combo.result_log:
				var key := "+".join(result.elements.map(func(e: int) -> String: return String(Layout.NAMES[e])))
				results[key] = result.hits
			var row := {lost = lost, secs = snappedf((t.frame - entered) / 60.0, 0.01), bars = bars, ids = by_id, results = results,
				deck = deck}
			rows.append(row)
			t.log_p("RATING %s run %d: %s" % [profile, run_index, row])
		var lost_total := 0.0
		var secs_total := 0.0
		var by_id := {}
		for row: Dictionary in rows:
			lost_total += row.lost
			secs_total += row.secs
			for id: StringName in row.ids:
				by_id[id] = by_id.get(id, 0) + row.ids[id]
		for id: StringName in by_id:
			by_id[id] = snappedf(by_id[id] / float(rows.size()), 0.01)
		t.log_p("RATING SUMMARY %s: %d runs, %.2f half-hearts a run, %.1f s a run, by id a run %s" % [profile, rows.size(),
			lost_total / rows.size(), secs_total / rows.size(), by_id])
		t.check(rows.size() == RATING_RUNS[profile], "rating: %d %s runs played" % [rows.size(), profile])


#THE MODEL

# A reaction off the model: a new player's or a learned one's, never under 0.12 s.
static func reaction(rng: RandomNumberGenerator, learned: bool) -> float:
	return maxf(0.12, rng.randfn(0.20, 0.04) if learned else rng.randfn(0.25, 0.05))


# The 120 px grid of soles over the floor, a body's half width and the walls' margin in from its edges.
static func grid() -> Array[Vector2]:
	var out: Array[Vector2] = []
	var y := Layout.FLOOR.position.y + 60.0
	while y < Layout.FLOOR.end.y - 30.0:
		var x := Layout.FLOOR.position.x + 60.0
		while x < Layout.FLOOR.end.x - 30.0:
			out.append(Vector2(x, y))
			x += 120.0
		y += 120.0
	return out


# The walk-away model against the pull: the soles from `start`, walking straight away from the maw once a reaction
# after the pull starts, clamped to the floor. The closest it comes, in maw radii.
static func walk_away(start: Vector2, maw: Vector2, react: float) -> float:
	var at := start
	var nearest := INF
	var clock := 0.0
	while clock < Layout.PULL_START + Layout.PULL_TIME:
		var away := (at - maw).normalized()
		var velocity := away * Layout.PLAYER_WALK if clock >= Layout.PULL_START + react else Vector2.ZERO
		at += (velocity - away * Layout.pull_at(clock)) * FRAME
		at = at.clamp(Layout.FLOOR.position + Vector2(18, 39), Layout.FLOOR.end - Vector2(18, 0))
		nearest = minf(nearest, ((at - maw) / Layout.R_MAW).length())
		clock += FRAME
	return nearest


#AIR

static func tier_air(t) -> void:
	# F7: the walk-away model from every grid start, either maw where it may be picked.
	var swallowed := []
	var closest := INF
	var starts := 0
	for start: Vector2 in grid():
		for maw: Vector2 in Layout.MAWS:
			if start.distance_to(maw) < Layout.AIR_START_MIN:
				continue
			starts += 1
			var nearest := walk_away(start, maw, Layout.REACTION)
			closest = minf(closest, nearest)
			if nearest <= 1.0:
				swallowed.append([start, maw])
	t.log_p("the walk-away model from %d starts: its closest approach %.2f maw radii" % [starts, closest])
	t.check(swallowed.is_empty(), "walking away from every grid start is never swallowed (%s)" % [swallowed.slice(0, 5)])
	var picked_far := true
	for start: Vector2 in grid():
		picked_far = picked_far and start.distance_to(Layout.MAWS[Layout.maw_for(start)]) >= Layout.AIR_START_MIN
	t.check(picked_far, "the maw picked is always AIR_START_MIN or more from the start")
	# F8: the reaction parry, off the model.
	var rng := RandomNumberGenerator.new()
	rng.seed = 8
	var rates := {}
	for learned: bool in [false, true]:
		var parried := 0
		for i in 4000:
			var press := reaction(rng, learned)
			if press >= Layout.BITE_TELL - Layout.PARRY_WINDOW and press <= Layout.BITE_TELL:
				parried += 1
		rates[learned] = parried / 4000.0
	t.log_p("the bite parried on a reaction: new %.1f%%, learned %.1f%%" % [rates[false] * 100.0, rates[true] * 100.0])
	t.check(rates[false] >= 0.95, "a new player's reaction parries the bite 95%% of the time or more (%.1f%%)" % (rates[false] * 100.0))
	t.check(rates[true] >= 0.78 and rates[true] <= 0.92, "a learned player's about 85%% (%.1f%%)" % (rates[true] * 100.0))
	# Live: walking away, then a parry on a reaction.
	var combo: Node = await air_first(t, 0)
	var air: Dictionary = combo.air_log[-1]
	var at: float = combo.result.at
	var hits0: int = combo.hits
	await walk_from_maw(t, combo, air, at)
	var press_at: float = air.bite_at + 0.25
	await t.wait_until(func(): return combo.wheel_clock - at >= press_at - 0.0001, 60)
	t.tap(KEY_SHIFT)
	await t.wait_until(func(): return air.contact_at >= 0.0, 60)
	var after_bite: float = combo.wheel_clock
	t.log_p("walked away from the maw at %s: closest %.2f maw radii, pull up to %.0f px/s; bite at %.3f, contact at %.3f (%.3f after), %s" % [
		air.maw, air.nearest, air.drift_max, air.bite_at, air.contact_at, air.contact_at - air.bite_at, air.bite_result])
	t.check(not air.swallowed and air.drift_max > 0.0, "walking away from the pull, never swallowed")
	t.check(absf(air.contact_at - air.bite_at - Layout.BITE_TELL) <= FRAME + 0.0001,
		"the bite lands BITE_TELL after its badge, +-1 frame (%.3f)" % (air.contact_at - air.bite_at))
	t.check(air.bite_result == PARRIED and combo.hits == hits0, "a press 0.25 s after the badge parries it, from any facing: nothing lost")
	# Then the second bite, parried the same way.
	await t.wait_until(func(): return air.bites.size() == 2, 60 * 2)
	var second: Dictionary = air.bites[-1]
	await t.wait_until(func(): return combo.wheel_clock - at >= float(second.at) + 0.25 - 0.0001, 60)
	t.tap(KEY_SHIFT)
	await t.wait_until(func(): return second.contact_at >= 0.0, 60)
	after_bite = combo.wheel_clock
	t.log_p("the second bite: its badge %.3f after the first landed, its contact %.3f after its badge, %s" % [second.at - air.contact_at,
		second.contact_at - second.at, second.result])
	t.check(absf(second.at - air.contact_at - Layout.SECOND_BITE_GAP) <= FRAME + 0.0001
		and absf(second.contact_at - second.at - Layout.BITE_TELL) <= FRAME + 0.0001,
		"the second badge SECOND_BITE_GAP after the first bite lands and its contact BITE_TELL after it, +-1 frame")
	t.check(second.result == PARRIED and combo.hits == hits0 and combo.max_badges <= 1,
		"a press 0.25 s after the second badge parries it too, one badge at a time: nothing lost")
	await t.wait_until(func(): return combo.beat != combo.Beat.RESULT, 60 * 2)
	t.check(combo.result_log[0].clear_at - after_bite <= Layout.CLEAR_AFTER + FRAME * 2,
		"and it clears CLEAR_AFTER after the second (%.3f)" % (combo.result_log[0].clear_at - after_bite))
	# Live: the first bite taken. The second still comes, its badge up while the hit's i-frames run and its contact after
	# them, and a press 0.25 s after its badge parries it: the hit costs only its own 3.
	combo = await air_first(t, 0)
	air = combo.air_log[-1]
	at = combo.result.at
	var before_hit: int = t.player.playerHealth
	await walk_from_maw(t, combo, air, at)
	await t.wait_until(func(): return air.bites.size() == 2, 60 * 3)
	var flickering: bool = t.player.is_invincible
	second = air.bites[-1]
	await t.wait_until(func(): return combo.wheel_clock - at >= float(second.at) + 0.25 - 0.0001, 60)
	t.tap(KEY_SHIFT)
	await t.wait_until(func(): return second.contact_at >= 0.0, 60)
	t.log_p("the first bite taken (%s): the second's badge up %s the i-frames, its contact %.3f after the first's; %s, lost %d" % [
		air.bite_result, "inside" if flickering else "after", second.contact_at - air.contact_at, second.result,
		before_hit - t.player.playerHealth])
	t.check(air.bite_result == HIT and flickering and second.contact_at - air.contact_at > Layout.IFRAMES
		and second.result == PARRIED and before_hit - t.player.playerHealth == 3,
		"a first bite taken: the second's badge shows through the i-frames, it lands after them and is parried")
	# Live: a guard held still, AIR_START_MIN out - it still drifts, and is swallowed: one chomp of 3, the spit, no bite.
	combo = await air_first(t, 1, Layout.MAWS[1] + Vector2(-Layout.AIR_START_MIN - 40.0, 0))
	air = combo.air_log[-1]
	at = combo.result.at
	var start_at: Vector2 = soles(t)
	var health: int = t.player.playerHealth
	t.press(KEY_SHIFT)
	await t.wait_until(func(): return combo.wheel_clock - at >= Layout.PULL_START + Layout.PULL_RAMP + 0.3, 120)
	var drifted: float = soles(t).distance_to(start_at)
	await t.wait_until(func(): return air.swallowed or combo.beat != combo.Beat.RESULT, 60 * 4)
	t.release(KEY_SHIFT)
	await t.wait_until(func(): return air.spat or combo.beat != combo.Beat.RESULT, 60 * 2)
	var spat_at: Vector2 = soles(t)
	await t.wait(6)
	var lost: int = health - t.player.playerHealth
	var chomps: int = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.CHOMP_ID).size()
	t.log_p("guard held from %s: drifted %.0f px by 0.3 s into the full pull; swallowed at %.3f, spat at %s, lost %d" % [
		start_at, drifted, air.swallow_at, spat_at, lost])
	t.check(drifted > 60.0, "a guard held still drifts toward the maw (%.0f px)" % drifted)
	t.check(air.swallowed and air.spat and lost == 3 and chomps == 1,
		"standing in the pull ends in the jaws: exactly one chomp of 3 half-hearts (%d)" % lost)
	t.check(not Layout.in_maw(spat_at, air.maw) and t.player.sprite.visible and not t.player.is_grabbed,
		"then spat out clear of the maw, seen and free")
	await t.wait_until(func(): return combo.beat != combo.Beat.RESULT, 60 * 2)
	t.check(air.bite_at < 0.0 and air.bites.is_empty(), "and no bite after a swallow, not even the second")
	# Live: a press 0.45 s after the badge is too late: the bite's 3.
	combo = await air_first(t, 0)
	air = combo.air_log[-1]
	at = combo.result.at
	health = t.player.playerHealth
	await walk_from_maw(t, combo, air, at)
	var late_at: float = air.bite_at + 0.45
	await t.wait_until(func(): return combo.wheel_clock - at >= late_at - 0.0001, 60)
	t.tap(KEY_SHIFT)
	await t.wait(3)
	t.log_p("a press at 0.45: %s, lost %d" % [air.bite_result, health - t.player.playerHealth])
	t.check(air.bite_result == HIT and health - t.player.playerHealth == 3, "a press 0.45 s after the badge is too late: hit for 3")


# A fight whose first result is the air's, its maw pinned, the player waiting where either maw may be picked.
static func air_first(t, maw: int, where := Vector2(960, 1360)) -> Node:
	var combo: Node = await enter(t, 100, [AIR, WATER, 3])
	combo.pinned_maw = maw
	await until_beat(t, combo, combo.Beat.STOP, 0)
	await place(t, where)
	await until_beat(t, combo, combo.Beat.RESULT, 0)
	return combo


# Away from the maw, a reaction after the pull starts, until the badge.
static func walk_from_maw(t, combo: Node, air: Dictionary, at: float) -> void:
	var pad := Pad.new(t)
	while air.bite_at < 0.0 and combo.beat == combo.Beat.RESULT:
		if combo.wheel_clock - at >= Layout.PULL_START + Layout.REACTION:
			pad.steer(soles(t) - Vector2(air.maw))
		await t.physics_frame
	pad.stop()


#WATER

# The standing dash through the wave, frame by frame: the hurtbox's top at `top`, the dash straight up `tau` after the
# roll, its immunity DashImmunity's (frames up to round(WAVE_IMMUNITY * 60) after it). Whether the band reached them
# outside it.
static func wave_model(top: float, tau: float) -> bool:
	var dash_frame := roundi(tau * 60.0)
	var immune_frames := roundi(Layout.WAVE_IMMUNITY * 60.0)
	var frame := 0
	while true:
		var front: float = Layout.FLOOR.position.y + Layout.WAVE_SPEED * frame * FRAME
		if front - Layout.WAVE_H > Layout.FLOOR.end.y:
			return false
		var lifted := 0.0
		if frame >= dash_frame:
			lifted = Layout.DASH_DISTANCE * minf(float(frame - dash_frame + 1) / 3.0, 1.0)
		var box_top := top - lifted
		var immune := frame >= dash_frame and frame - dash_frame <= immune_frames
		if front > box_top and front - Layout.WAVE_H < box_top + Layout.PLAYER_HURT_HEIGHT and not immune:
			return true
		frame += 1
	return false


# The middle of the window, after the roll: the front 93 px short of the hurtbox's top.
static func ideal_dash(top: float) -> float:
	var touch: float = (top - Layout.FLOOR.position.y) / Layout.WAVE_SPEED
	var reach := Layout.WAVE_IMMUNITY * Layout.WAVE_SPEED - (Layout.WAVE_H + Layout.PLAYER_HURT_HEIGHT - Layout.DASH_DISTANCE)
	return touch - reach / Layout.WAVE_SPEED / 2.0


static func tier_water(t) -> void:
	# F4: the window, standing, and the model's dash through it.
	t.log_p("the wave's dash window, standing, no walk credit, %.0f px margin: %.4f s" % [Layout.MARGIN, Layout.wave_window()])
	t.check(Layout.wave_window() >= Layout.WAVE_WINDOW_MIN, "F4: %.4f s, at least %.2f" % [Layout.wave_window(), Layout.WAVE_WINDOW_MIN])
	var rng := RandomNumberGenerator.new()
	rng.seed = 4
	var tops := [300.0, 600.0, 900.0, 1200.0, 1420.0]
	var open := []
	for top: float in tops:
		var first := INF
		var last := -INF
		var tau := ideal_dash(top) - 0.3
		while tau < ideal_dash(top) + 0.3:
			if not wave_model(top, tau):
				first = minf(first, tau)
				last = maxf(last, tau)
			tau += FRAME
		open.append(snappedf(last - first + FRAME, 0.001))
	t.log_p("the window measured frame by frame at hurtbox tops %s: %s s" % [tops, open])
	t.check(open.all(func(w: float) -> bool: return w >= Layout.WAVE_WINDOW_MIN), "every standing height has a window of %.2f s or more" % Layout.WAVE_WINDOW_MIN)
	var clears := {}
	for learned: bool in [true, false]:
		var clean := 0
		for i in 200:
			var top: float = tops[i % tops.size()]
			var off := rng.randfn(0.0, 0.04) if learned else rng.randfn(0.0, 0.05)
			if not wave_model(top, ideal_dash(top) + off):
				clean += 1
		clears[learned] = clean / 200.0
	t.log_p("the model's dash, 200 seeds: learned (ideal +- 40 ms) %.1f%% clean, new (+- 50 ms on a 250 ms reaction) %.1f%%" % [
		clears[true] * 100.0, clears[false] * 100.0])
	t.check(clears[true] >= 0.95, "learned: 95%% or more clean (%.1f%%)" % (clears[true] * 100.0))
	t.check(clears[false] >= 0.70, "new: 70%% or more clean (%.1f%%)" % (clears[false] * 100.0))
	# Live: the dash bot, standing, dashes straight up on the window's middle.
	for top: float in [600.0, 1100.0]:
		var combo: Node = await water_first(t, Vector2(700, top + Layout.PLAYER_HURT_HEIGHT))
		var water: Dictionary = combo.water_log[-1]
		var box_top: float = hurt_box(t).position.y
		var reach := Layout.WAVE_IMMUNITY * Layout.WAVE_SPEED - (Layout.WAVE_H + Layout.PLAYER_HURT_HEIGHT - Layout.DASH_DISTANCE)
		await t.wait_until(func(): return water.wave.rolling and water.wave.front_y >= box_top - reach / 2.0, 60 * 4)
		t.press(KEY_UP)
		t.tap(KEY_W)
		await t.wait(4)
		t.release(KEY_UP)
		await t.wait_until(func(): return water.cleared, 60 * 4)
		var waves: Array = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.WAVE_ID)
		t.log_p("standing at hurtbox top %.0f, dashed at the front %.0f px short: results %s" % [box_top, reach / 2.0, water.results])
		t.check(waves.is_empty() and water.results.has(DODGED), "standing, a dash up through the wave on its window: dodged, nothing lost")
		# Then the shark's snap from where it collapsed, parried a reaction after its badge.
		await t.wait_until(func(): return not water.bite.is_empty(), 60 * 2)
		var bite: Dictionary = water.bite
		var at: float = combo.result.at
		await t.wait_until(func(): return combo.wheel_clock - at >= float(bite.at) + 0.25 - 0.0001, 60)
		t.tap(KEY_SHIFT)
		await t.wait_until(func(): return bite.contact_at >= 0.0, 60)
		var after_bite: float = combo.wheel_clock
		await t.wait_until(func(): return combo.beat != combo.Beat.RESULT, 60 * 2)
		t.log_p("the snap after the wave: its badge %.3f after the wave was off the floor, at %s; its contact %.3f after the badge, %s; cleared %.3f after" % [
			bite.at - water.cleared_at, (Vector2(bite.rear_from) * 10.0).round() / 10.0, bite.contact_at - bite.at, bite.result,
			combo.result_log[0].clear_at - after_bite])
		t.check(absf(bite.at - water.cleared_at - Layout.BREACH_RISE) <= FRAME + 0.0001 and absf(bite.contact_at - bite.at - Layout.BITE_TELL) <= FRAME + 0.0001
			and Vector2(bite.rear_from).y == Layout.FLOOR.end.y, "the snap's badge BREACH_RISE after the wave is off the floor, from its bottom edge; the contact BITE_TELL after it")
		t.check(bite.result == PARRIED and combo.hit_log.is_empty() and combo.max_badges <= 1
			and combo.result_log[0].clear_at - after_bite <= Layout.CLEAR_AFTER + FRAME * 2,
			"a press 0.25 s after the snap's badge parries it, one badge at a time: nothing lost, and the result clears CLEAR_AFTER later")
	# Live: standing still, and walking away down to the bottom wall: hit once each.
	for walk: bool in [false, true]:
		var combo: Node = await water_first(t, Vector2(700, 700))
		var water: Dictionary = combo.water_log[-1]
		if walk:
			await t.wait_until(func(): return water.rolled, 60 * 2)
			t.press(KEY_DOWN)
		await t.wait_until(func(): return water.cleared, 60 * 4)
		t.release(KEY_DOWN)
		var waves: Array = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.WAVE_ID)
		t.log_p("%s: hits %s" % ["walked down to the wall" if walk else "stood still", waves])
		t.check(waves.size() == 1 and waves[0].damage == 2, "%s: the wave hits once, for a heart" % ("walking away to the bottom wall" if walk else "standing still"))
		if not walk:
			await t.wait_until(func(): return combo.beat != combo.Beat.RESULT, 60 * 2)
			var snaps: Array = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.BREACH_ID)
			t.check(snaps.size() == 1 and snaps[0].damage == 3, "standing still, the snap after the wave lands too, for 3 (%s)" % [snaps])


#FIRE

# The walk into the column, frame by frame: a reaction after the projection, then straight along the floor at the walk
# (against the crosswind on the firestorm) until the body is a margin inside the column; the curtain and the burning band
# across the floor but the column. Whether the fire reached them.
static func fire_model(start_x: float, cx: float, double: bool, react: float) -> bool:
	var span := Layout.column_span(cx, double)
	var direction := Layout.entry_for(cx)
	var entry := Layout.entry_x(direction)
	var x := start_x
	var target := clampf(x, span.x + Layout.PLAYER_HALF_WIDTH + Layout.MARGIN, span.y - Layout.PLAYER_HALF_WIDTH - Layout.MARGIN)
	var speed := Layout.PLAYER_WALK - (Layout.WIND if double else 0.0)
	var clock := 0.0
	var sweep_end := Layout.T_PROJ + Layout.FLOOR.size.x / Layout.FRONT_SPEED
	while clock < sweep_end + Layout.BURN:
		if clock >= react:
			x = move_toward(x, target, speed * FRAME)
		var mouth := entry + direction * Layout.FRONT_SPEED * (clock - Layout.T_PROJ)
		if clock >= Layout.T_PROJ:
			var tail := entry + direction * Layout.FRONT_SPEED * (clock - Layout.T_PROJ - Layout.BURN)
			var lit := Vector2(minf(tail, mouth), maxf(tail, mouth))
			var body := Vector2(x - Layout.PLAYER_HALF_WIDTH, x + Layout.PLAYER_HALF_WIDTH)
			for piece: Vector2 in [Vector2(Layout.FLOOR.position.x, span.x), Vector2(span.y, Layout.FLOOR.end.x)]:
				var hot := Vector2(maxf(lit.x, piece.x), minf(lit.y, piece.y))
				if hot.x < hot.y and body.x < hot.y and body.y > hot.x:
					return true
		clock += FRAME
	return false


static func tier_fire(t) -> void:
	# F2: the model's walk into the column from every grid start, 20 seeds, single and firestorm.
	t.log_p("F2 spare, the worst placement: single %.3f s, firestorm %.3f s (CROSS_SPARE %.2f)" % [Layout.worst_fire_spare(false),
		Layout.worst_fire_spare(true), Layout.CROSS_SPARE])
	t.check(Layout.worst_fire_spare(false) >= Layout.CROSS_SPARE and Layout.worst_fire_spare(true) >= Layout.CROSS_SPARE,
		"F2: the walk into the column beats the front with CROSS_SPARE to spare at the worst placement")
	var rng := RandomNumberGenerator.new()
	rng.seed = 2
	var burnt := []
	var runs := 0
	var entries := {}
	var under := 0
	for double: bool in [false, true]:
		for start: Vector2 in grid():
			for seed_index in 20:
				var cx := Layout.column_for(rng, start.x, double)
				var span := Layout.column_span(cx, double)
				entries[Layout.entry_for(cx)] = true
				if start.x + Layout.PLAYER_HALF_WIDTH > span.x and start.x - Layout.PLAYER_HALF_WIDTH < span.y:
					under += 1
				runs += 1
				if fire_model(start.x, cx, double, reaction(rng, false)):
					burnt.append([start.x, snappedf(cx, 1.0), double])
	t.log_p("the walk bot over %d runs (both entries %s): burnt %d %s" % [runs, entries.keys(), burnt.size(), burnt.slice(0, 5)])
	t.check(burnt.is_empty() and entries.size() == 2, "a new player's reaction, then a walk into the column: never burnt, from either entry")
	t.check(under == 0, "F3: the column is never laid under the player (%d)" % under)
	# Live: the walk bot into the column, standing still, and a dash back through the front.
	for how: String in ["walk", "stand", "dash back"]:
		var combo: Node = await enter(t, 100, [FIRE, WATER, 3])
		await until_beat(t, combo, combo.Beat.STOP, 0)
		await place(t, Vector2(700, 1300))
		await until_beat(t, combo, combo.Beat.RESULT, 0)
		var fire: Dictionary = combo.fire_log[-1]
		var at: float = combo.result.at
		var span: Vector2 = fire.span
		var pad := Pad.new(t)
		var dashed := false
		while combo.beat == combo.Beat.RESULT:
			var x: float = t.player.global_position.x
			if how == "walk" and combo.wheel_clock - at >= Layout.REACTION:
				var target := clampf(x, span.x + 40.0, span.y - 40.0)
				pad.steer(Vector2(target - x, 0.0), 4.0)
			if how == "dash back" and not dashed and is_instance_valid(fire.node):
				var mouth: float = fire.node.mouth_x()
				if combo.wheel_clock - at >= Layout.T_PROJ and absf(mouth - x) <= 140.0:
					dashed = true
					var key: int = KEY_LEFT if fire.direction > 0.0 else KEY_RIGHT
					t.press(key)
					t.tap(KEY_W)
					await t.wait(4)
					t.release(key)
			await t.physics_frame
		pad.stop()
		var burns: Array = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.BREATH_ID or h.id == Layout.FIRE_ID)
		t.log_p("%s: the column %s from %.0f, entered from %s; reports %s; hits %s" % [how, span, 700.0,
			"the left" if fire.direction > 0.0 else "the right", fire.reports, burns])
		match how:
			"walk":
				t.check(burns.is_empty(), "walking into the gap: never burnt")
			"stand":
				t.check(burns.size() == 1 and burns[0].damage == 2, "standing still: burnt exactly once, a heart")
			"dash back":
				t.check(dashed and burns.size() == 1 and burns[0].id == Layout.FIRE_ID,
					"a dash back through the front lands in the burning floor: burnt once")


#EARTH

# When each ring's band reaches `point` standing there: its birth if it is born on them, else as its middle gets there.
static func arrivals(spots: Array[Vector2], times: Array[float], point: Vector2) -> Array[float]:
	var out: Array[float] = []
	for k in spots.size():
		var travel := maxf(Layout.ring_distance(spots[k], point) - CombinedLayout.RING_START_RADIUS, 0.0)
		out.append(times[k] + travel / Layout.RING_SPEED)
	return out


static func least_gap(arrive: Array[float]) -> float:
	var least := INF
	for k in range(1, arrive.size()):
		least = minf(least, arrive[k] - arrive[k - 1])
	return least


# The ring's band against a dash straight in at it along one axis, frame by frame (1D, floor px): the feet's near edge
# `gap` outside the band's outer edge as the dash starts. Whether it caught them outside the immunity.
static func ring_model(gap: float) -> bool:
	var feet := Layout.RING_HALF_WIDTH + gap + Layout.PLAYER_HALF_WIDTH
	var radius := 0.0
	var immune_frames := roundi(Layout.DASH_IMMUNITY * 60.0)
	for frame in 120:
		var moved := Layout.DASH_DISTANCE * minf(float(frame + 1) / 3.0, 1.0)
		var near := feet - moved - Layout.PLAYER_HALF_WIDTH
		var far := feet - moved + Layout.PLAYER_HALF_WIDTH
		if radius + Layout.RING_HALF_WIDTH > near and radius - Layout.RING_HALF_WIDTH < far and frame > immune_frames:
			return true
		radius += Layout.RING_SPEED * FRAME
	return false


static func tier_earth(t) -> void:
	# F6: the table of arrivals, every grid start standing, and everywhere else from a sample of starts.
	var least := INF
	var least_at := Vector2.ZERO
	var nearest_pillar := INF
	var starts := grid()
	for start: Vector2 in starts:
		var spots := Layout.pillars_for(start)
		var times := Layout.slam_times(spots)
		for spot: Vector2 in spots:
			nearest_pillar = minf(nearest_pillar, spot.distance_to(start))
		var gap := least_gap(arrivals(spots, times, start))
		if gap < least:
			least = gap
			least_at = start
	var anywhere := INF
	for i in range(0, starts.size(), 7):
		var spots := Layout.pillars_for(starts[i])
		var times := Layout.slam_times(spots)
		for point: Vector2 in starts:
			anywhere = minf(anywhere, least_gap(arrivals(spots, times, point)))
	t.log_p("rings at %d grid starts, standing: the least gap between two %.3f s (at %s); anywhere on the floor %.3f s; the nearest pillar to a start %.0f px" % [
		starts.size(), least, least_at, anywhere, nearest_pillar])
	t.check(least >= Layout.RING_SPACING - 0.0001 and anywhere >= Layout.RING_SPACING - 0.0001,
		"F6: every two required dashes %.2f s or more apart, wherever the player stands (%.3f, %.3f)" % [Layout.RING_SPACING, least, anywhere])
	t.check(nearest_pillar >= Layout.PILLAR_CLEAR, "F12: no pillar rises within PILLAR_CLEAR of the player (%.0f)" % nearest_pillar)
	t.log_p("a ring's dash window sideways: %.3f s (Layout.ring_window)" % Layout.ring_window())
	var open := 0.0
	var gap := 0.0
	while gap < 600.0:
		if not ring_model(gap):
			open += 1.0
		gap += 1.0
	t.log_p("the 1D model: a dash straight in clears the ring started from %.0f px of gaps (%.3f s of the ring's travel)" % [open, open / Layout.RING_SPEED])
	t.check(Layout.ring_window() >= Layout.RING_WINDOW_MIN and open / Layout.RING_SPEED >= Layout.RING_WINDOW_MIN,
		"a ring's window is %.2f s or more" % Layout.RING_WINDOW_MIN)
	# Live: the dash bot straight in through each ring as its band comes within the window's middle.
	var standing := Vector2(960, 1300)
	var combo: Node = await earth_first(t, standing)
	var earth: Dictionary = combo.earth_log[-1]
	var dashed := {}
	var hits0: int = combo.hit_log.size()
	var middle := (Layout.DASH_DISTANCE + Layout.RING_SPEED * Layout.DASH_IMMUNITY) / 2.0
	while combo.beat == combo.Beat.RESULT and combo.result_log.size() == 1:
		for entry: Dictionary in combo.ring_log:
			if not is_instance_valid(entry.node) or dashed.has(entry.born):
				continue
			var ring: Node2D = entry.node
			var off: Vector2 = Vector2(ring.global_position) - soles(t)
			var between: float = Layout.ring_distance(ring.global_position, soles(t)) - ring.radius
			if between > middle or between < 0.0:
				continue
			dashed[entry.born] = combo.wheel_clock
			var key: int = (KEY_RIGHT if off.x > 0.0 else KEY_LEFT) if absf(off.x) >= absf(off.y) / 0.36 else (KEY_DOWN if off.y > 0.0 else KEY_UP)
			t.press(key)
			t.tap(KEY_W)
			await t.wait(4)
			t.release(key)
		await t.physics_frame
	var rings: Array = combo.hit_log.slice(hits0).filter(func(h: Dictionary) -> bool: return h.id == Layout.RING_ID)
	t.log_p("pillars %s, slams at %s; the bot dashed %d rings; ring hits %s" % [earth.spots, earth.times, dashed.size(), rings])
	t.check(dashed.size() == 3 and rings.is_empty(), "the dash bot, straight in at each ring: three dashes, no ring hit")
	# Live: standing still, every ring lands (here they come over a second apart): three, half a heart each.
	combo = await earth_first(t, standing)
	earth = combo.earth_log[-1]
	var gaps := least_gap(arrivals(earth.spots, earth.times, standing))
	await t.wait_until(func(): return combo.result_log.size() > 1 or combo.beat != combo.Beat.RESULT, 60 * 8)
	rings = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.RING_ID)
	t.log_p("standing at %s (rings %.2f s apart at least): %s" % [standing, gaps, rings])
	t.check(rings.size() == 3 and rings.all(func(h: Dictionary) -> bool: return h.damage == 1), "standing still: three rings, half a heart each")
	# Live: beside a pillar as it is smashed, the ring born on them lands at once, after its shadow's whole tell.
	combo = await earth_first(t, standing)
	earth = combo.earth_log[-1]
	var first: Dictionary = earth.slams[0]
	await place(t, Vector2(first.spot) + Vector2(0, 60))
	await t.wait_until(func(): return first.phase >= 4, 60 * 3)
	await t.wait(2)
	var born: float = first.born_at + combo.result_log[0].at
	rings = combo.hit_log.filter(func(h: Dictionary) -> bool: return h.id == Layout.RING_ID)
	var told: float = first.slam_at - first.tell_at
	t.log_p("beside pillar 1 at %s: its ring born at %.3f, hits %s; its shadow up %.2f s before" % [first.spot, born, rings, told])
	t.check(rings.size() == 1 and absf(rings[0].at - born) <= FRAME + 0.0001 and told >= Layout.SLAM_TELL - 0.0001,
		"a ring born on the player hits as it is born, only after SLAM_TELL of shadow")


static func earth_first(t, where: Vector2) -> Node:
	var combo: Node = await enter(t, 100, [EARTH, FIRE, 1])
	await until_beat(t, combo, combo.Beat.STOP, 0)
	await place(t, where)
	await until_beat(t, combo, combo.Beat.RESULT, 0)
	return combo


# A fight whose first result is the water's, the player standing on `where` (soles) as it starts.
static func water_first(t, where: Vector2) -> Node:
	var combo: Node = await enter(t, 100, [WATER, EARTH, 0])
	await until_beat(t, combo, combo.Beat.STOP, 0)
	await place(t, where)
	await until_beat(t, combo, combo.Beat.RESULT, 0)
	return combo
