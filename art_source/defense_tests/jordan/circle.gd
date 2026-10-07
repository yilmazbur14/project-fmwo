extends RefCounted

# jordan_circle (coder D): Jordan's attack 4, Carter + Mason's circle (JordanComboCircle, JordanCircleLayout), in the god
# fight, each tier on a fresh fight whose rotation holds only the circle, started as soon as it opens. --max-fps 60: the
# payoff's mash is real time. Every time is on the attack's own clock (circle_clock), which is game time. tier=
#   layout  staging option B under the fight's 2/3 view: the clones' feet on their ellipse (±1 px), each facing into
#           the circle; the clones in every pose, Carter, and Mason at rest, landed, and lifted over the run line's outer
#           top, on the floor, VIEW_MARGIN inside the view, clear of Jordan's mask and core and 12 px clear of the HUD
#           (screen px), and Carter and Mason's rest clear of every clone; the circle's size on screen logged; the wall
#           up. With playtest_invincible on: each of 8 directions held from the centre, then dashes into the wall - the
#           soles never more than 6 px outside SOLES_RADII; the player one z over the clones all through the sweep.
#   bot     the feasibility proof: a bot that chases a carrot on the run line 25 round degrees ahead of it, never past a
#           90 degree lead on the sweep as it stood 12 frames ago, steering 8-way on 24 of every 30 frames and stepping
#           out to the run line's zigzag either side of it, away from the bombs within 110 px. The fires: FIRES of them,
#           the first from the clone nearest the player, then clockwise, a lap (FIRES / CLONES), a cadence apart (±1 frame),
#           each landing 0.10 s after it fired; no beam hit and at most one bomb, the smallest margin of the player's
#           lead over the chasing band logged, and a clean run's hype each lap's, a part lap its share. The end: clones,
#           wall and bombs gone; Mason down beside Carter; both left open; the HUD back; the player free and at their own
#           z. Then a walk to Carter, three presses and a three-bar mash: Jordan -3, and a clean wrap into Idle.
#   idle    standing at the centre: the first band hits on its landing frame (±1) for a heart, then one every 1.0 s
#           (±2 frames) through the i-frames, a pause of 45 frames between the first two holding circle_clock; the
#           third is the Defeat, and the attack leaves nothing of its own behind.
#   poo     the bot, early in the loop, walks into the next bomb: exactly half a heart of jordan_circle_poo, and it
#           pops. Once the i-frames are out it dashes across two more: DODGED, and nothing lost. Mason then drops
#           nothing until he is at least 40 degrees ahead of the player again, within 1.0 s.
#   normal  all of them in turn.

const FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const GOD := "Arena/JordanGodScene/God"
const STRINGS := "Arena/JordanGodScene/Strings"
const CIRCLE_SCRIPT := "res://Scripts/States/JordanGod/JordanComboCircle.gd"
const Layout := preload("res://Scripts/JordanCircleLayout.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const PuppetLayout := preload("res://Scripts/JordanPuppetLayout.gd")
const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const POO_SCRIPT := preload("res://Scripts/JordanCirclePoo.gd")
const FRAME := 1.0 / 60.0
const TIERS := ["layout", "bot", "idle", "poo"]
# Staging option B's keep-clears: Jordan's mask and core in world px, the HUD in screen px with the clearance round it,
# and the view's own edge, which everything keeps VIEW_MARGIN screen px inside.
const MASK := Rect2(912, 189, 96, 69)
const CORE := Rect2(936, 270, 48, 57)
const HUD_KEEP_OUT := [Rect2(720, 33, 480, 148), Rect2(10, 842, 406, 229), Rect2(1371, 946, 537, 126)]
const HUD_CLEARANCE := 12.0
const VIEW_MARGIN := 12.0
const HIT := 1
const DODGED := 4
# The bot: its reaction in frames, the frames of every DUTY.y it moves on, its carrot and its cap (round degrees), and
# the bombs.
const REACTION := 12
const DUTY := Vector2i(24, 30)
const CARROT := 25.0
const LEAD_CAP := 90.0
const STEP_OUT := Vector2(Layout.RUN_RADIUS - Layout.ZIG, Layout.RUN_RADIUS + Layout.ZIG)
const BOMB_NEAR := 110.0
const DEAD_ZONE := 8.0
# 8 directions held from the centre, each HOLD_PAST frames past the step it reaches the wall on (hold_frames), so all of
# it fits inside the loop; and the dashes into the wall, from well inside it: the soles' offset as a share of
# SOLES_RADII, and which way.
const WAYS := [Vector2(1, 0), Vector2(1, 1), Vector2(0, 1), Vector2(-1, 1), Vector2(-1, 0), Vector2(-1, -1), Vector2(0, -1),
	Vector2(1, -1)]
const HOLD_PAST := 8
const DASHES := [[Vector2(0, 0.8), Vector2(0, 1)], [Vector2(0.45, 0.5), Vector2(1, 1)], [Vector2(-0.85, 0), Vector2(-1, 0)],
	[Vector2(0, -0.8), Vector2(0, -1)]]
const WALL_SLACK := 6.0
# The walk to Carter keeps clear of Mason's reach: out to the left of where the circle stood, then up to Carter.
const TO_CARTER := [Vector2(-250, 900), Vector2(-250, 480)]
const PUNCH_GAP := 9
const PAUSE_FRAMES := 45
# The poo tier: its dashes go sideways across outer bombs along the circle's bottom, where the run heads left, a
# sideways dash can't hop a bomb's oval (an up or down one can: the oval is only 48 px tall) and it carries the player
# furthest round, and only once the lead is back under DASH_LEAD. An outer bomb keeps the dash out of the middle, where
# the bands are widest.
const BOTTOM := Vector2(50, 130)
# It walks into a bomb once this many clones have fired and Mason's first bombs are down: early, with the lap
# still ahead of it for the dashes.
const POO_AFTER := 2
const DASH_FROM := 100.0
const DASH_LEAD := 80.0
# How close to the dash's start, each way: a walk moves 10 px a step, so a tighter stop only rocks either side of it.
# Level with the bomb to within ALIGN.y, a sideways dash crosses its oval.
const ALIGN := Vector2(12, 6)
# The dash held this many steps, and Mason watched for this many from it.
const DASH_FRAMES := 12
const WATCH_FRAMES := 72
# The fires `layout` and `poo` run the sweep for (extend_loop): the lap and a half the attack fired until 2026-10-04.
const TEST_FIRES := 36


# Every hit the player takes, on the attack's clock.
class Hits:
	var list: Array = []
	var combo: Node
	var body: Node2D

	func _init(defense: Node, attack: Node) -> void:
		combo = attack
		body = defense.get_parent()
		defense.hit_taken.connect(_on_hit)

	# With where the player stood: the round angle and floor radius of their soles.
	func _on_hit(hit: RefCounted) -> void:
		var at := body.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)
		list.append({id = hit.attack_id, at = combo.circle_clock, damage = hit.damage,
			where = Vector2(snappedf(Layout.round_angle(at), 0.1), snappedf(Layout.floor_radius(at), 0.1))})

	func of(id: StringName) -> Array:
		return list.filter(func(h: Dictionary) -> bool: return h.id == id)


# The arrow keys held, as a player holds them.
class Pad:
	var t
	var held: Array = []

	func _init(suite) -> void:
		t = suite

	func steer(to: Vector2, dead := DEAD_ZONE) -> void:
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


# The bot's run of the loop, and what it measured.
class Run:
	var frame := 0
	var min_margin := INF
	var min_front := INF
	var margin_at := 0.0
	var steps := 0


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	for tier in tiers:
		t.log_p("-- jordan_circle %s" % tier)
		match tier:
			"layout":
				await tier_layout(t)
			"bot":
				await tier_bot(t)
			"idle":
				await tier_idle(t)
			"poo":
				await tier_poo(t)
			_:
				t.check(false, "jordan_circle has no tier %s" % tier)


#GETTING THERE

# A fresh god fight whose rotation is the circle alone, the player at `health`, the attack started as the fight's Open
# hands over: back once it reaches `until` (the circle closed on the player, by default).
static func enter(t, health := 100, until := &"loop") -> Node:
	var combos: Array[String] = [CIRCLE_SCRIPT]
	GodLayout.COMBOS = combos
	await t.open_scene(FIGHT)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(GOD)
	t.sm = t.boss.state_machine
	t.player.playerHealth = health
	var combo := combo_of(t)
	t.check(combo != null, "the rotation holds the circle")
	await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 4)
	t.sm.start_next_attack()
	var beat: int = combo.Beat.FORM if until == &"form" else combo.Beat.LOOP
	var there: bool = await t.wait_until(func(): return combo.beat == beat, 60 * 8)
	t.check(there and t.sm.current_state == combo, "the circle starts, and reaches its %s" % until)
	return combo


static func combo_of(t) -> Node:
	for node in t.current_scene.find_children("*", "Node", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == CIRCLE_SCRIPT:
			return node
	return null


static func soles(t) -> Vector2:
	return t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


# Steps from the centre to the wall walking `way` 8-way at the player's 600 px/s a side, and HOLD_PAST more.
static func hold_frames(way: Vector2) -> int:
	var per_step := way * 600.0 * FRAME
	return ceili(1.0 / (per_step / Layout.SOLES_RADII).length()) + HOLD_PAST


# How far outside SOLES_RADII the soles are, in px along their ray from the centre; 0 inside.
static func outside(point: Vector2) -> float:
	var off := point - Layout.CENTRE
	var scaled := (off / Layout.SOLES_RADII).length()
	if scaled <= 1.0:
		return 0.0
	return off.length() * (1.0 - 1.0 / scaled)


#THE BOT

# One physics step of the bot: its carrot on the run line, capped on the sweep it last saw, stepped out round a bomb,
# or onto `into` (a bomb it means to walk into) when there is one. The carrot is measured off the chasing half rather
# than the bot's own angle, which means nothing near the middle, where it starts. Before the first beam it walks back
# to its cap if it is past it; after, it waits there instead.
static func bot_step(t, combo: Node, pad: Pad, run: Run, into: Node2D = null) -> void:
	var at := soles(t)
	var theta := Layout.round_angle(at)
	var seen: float = combo.sweep_at(combo.circle_clock - REACTION * FRAME)
	var lead := fposmod(theta - seen, 180.0)
	var ahead := minf(lead + CARROT, LEAD_CAP)
	if combo.first_fired:
		ahead = maxf(ahead, lead)
	var carrot := theta - lead + ahead
	var radius := Layout.RUN_RADIUS
	if is_instance_valid(into):
		radius = Layout.floor_radius(into.global_position)
	else:
		radius = step_out(combo, at)
	if run.frame % DUTY.y < DUTY.x:
		pad.steer(Layout.round_point(carrot, radius) - at)
	else:
		pad.stop()
	run.frame += 1


# Away from every bomb within BOMB_NEAR: inside the line from the outer ones, outside it from the inner ones, and on
# the line between them when there are both. Up the circle's sides the bombs lie only about 100 px apart, in and out
# by turns, so stepping away from one alone walks onto the next.
static func step_out(combo: Node, at: Vector2) -> float:
	var inner := false
	var outer := false
	for bomb: Node2D in combo.turds:
		if not is_instance_valid(bomb) or bomb.popped or at.distance_to(bomb.global_position) > BOMB_NEAR:
			continue
		if Layout.floor_radius(bomb.global_position) > Layout.RUN_RADIUS:
			outer = true
		else:
			inner = true
	if outer == inner:
		return Layout.RUN_RADIUS
	return STEP_OUT.x if outer else STEP_OUT.y


# The player's lead over the live band's chasing half, in round degrees, and how far round that half could still go
# before its band touched their hurtbox: the margin is the one less the other. The same for the leading half ahead.
static func measure(t, combo: Node, run: Run) -> void:
	var live: Dictionary = {}
	for shot: Dictionary in combo.beams:
		if shot.live:
			live = shot
	if live.is_empty():
		return
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale.abs()
	var c: Vector2 = shape.global_position - Layout.BEAM_CENTRE
	var theta := Layout.round_of(floor_deg(c))
	var axis := Layout.round_of(floor_deg(Vector2.from_angle(combo.clones[live.clone].angle)))
	var lead := fposmod(theta - axis, 180.0)
	var margin := lead - band_delta(c, size, theta, -1.0)
	var front := 180.0 - lead - band_delta(c, size, theta, 1.0)
	run.steps += 1
	if margin < run.min_margin:
		run.min_margin = margin
		run.margin_at = combo.circle_clock
	run.min_front = minf(run.min_front, front)


static func floor_deg(v: Vector2) -> float:
	return rad_to_deg(atan2(v.y / Layout.FLOOR_RATIO, v.x))


# How far round from round angle `theta`, `way` -1 behind or +1 ahead, a band through BEAM_CENTRE first leaves a hurtbox
# of `size` centred `c` from it: CarterBeamRush's band test, turned a quarter degree at a time.
static func band_delta(c: Vector2, size: Vector2, theta: float, way: float) -> float:
	var half := size / 2.0
	var turn := 0.0
	while turn < 180.0:
		var a := deg_to_rad(Layout.floor_of(theta + way * turn))
		var n := Vector2(cos(a), Layout.FLOOR_RATIO * sin(a)).normalized().orthogonal()
		var across := CarterArtLayout.MESSATSU_HIT_WIDTH / 2.0 + half.x * absf(n.x) + half.y * absf(n.y)
		if absf(c.dot(n)) > across:
			return turn
		turn += 0.25
	return 180.0


# The bot through the whole loop, measuring as it goes.
static func run_loop(t, combo: Node) -> Run:
	var pad := Pad.new(t)
	var run := Run.new()
	while combo.beat == combo.Beat.LOOP and t.player.playerHealth > 0:
		bot_step(t, combo, pad, run)
		await t.physics_frame
		measure(t, combo, run)
	pad.stop()
	return run


# Walking the player's origin through `points` in turn, until the attack is past its walk.
static func walk(t, combo: Node, points: Array) -> void:
	var pad := Pad.new(t)
	for point: Vector2 in points:
		for i in 60 * 6:
			if combo.beat != combo.Beat.WALK:
				break
			var to: Vector2 = point - t.player.global_position
			if to.length() <= DEAD_ZONE:
				break
			pad.steer(to)
			await t.physics_frame
	pad.stop()


# The three presses and a mash that banks every bar; the bars the payoff reported.
static func pay_off(t, combo: Node) -> int:
	for i in 3:
		t.tap(KEY_Q)
		await t.wait(PUNCH_GAP)
	await t.wait_until(func(): return t.player.finisher.is_active(), 60 * 2)
	await t.mash_tiered(t.TIER_PASS_FRAMES[2])
	await t.wait_until(func(): return combo.bars >= 0, 60 * 10)
	return combo.bars


#KEEP-CLEARS

# A sprite's frame in world px.
static func drawn(sprite: Sprite2D) -> Rect2:
	return sprite.get_global_transform() * sprite.get_rect()


static func clear_of_jordan(rect: Rect2) -> bool:
	return not rect.intersects(MASK) and not rect.intersects(CORE)


static func to_screen(rect: Rect2) -> Rect2:
	var zoom: float = ScreenView.base_zoom
	return Rect2((rect.position - ScreenView.base_focus) * zoom + ScreenView.VIEW_SIZE / 2.0, rect.size * zoom)


static func clear_of_hud(rect: Rect2) -> bool:
	var on_screen := to_screen(rect)
	for keep_out: Rect2 in HUD_KEEP_OUT:
		if on_screen.intersects(keep_out.grow(HUD_CLEARANCE)):
			return false
	return true


static func on_floor(rect: Rect2) -> bool:
	return GodLayout.FLOOR.encloses(Rect2(rect.position.x, rect.end.y - 1.0, rect.size.x, 1.0))


# VIEW_MARGIN screen px inside the fight's whole view.
static func in_view(rect: Rect2) -> bool:
	return ScreenView.base_rect().grow(-VIEW_MARGIN / ScreenView.base_zoom).encloses(rect)


# Every pose a clone takes, his charge and his fire off the sheets the attack draws him from: their drawn pixels round
# his feet, in world px, facing left or right.
static func clone_pixels(face_left: bool) -> Rect2:
	var used := Rect2()
	for anim_name: StringName in [&"messatsu_charge", &"messatsu_fire"]:
		var anim: Dictionary = CarterArtLayout.anim(anim_name)
		var twin := PuppetLayout.twin_path(&"carter", anim.sheet)
		var image: Image = load(twin if twin != "" else anim.sheet).get_image()
		var size := Vector2i(CarterArtLayout.FRAME_SIZE)
		for f: int in anim.frames:
			var rect := Rect2(image.get_region(Rect2i(f * size.x, 0, size.x, size.y)).get_used_rect())
			used = rect if used.size == Vector2.ZERO else used.merge(rect)
	var left := used.position.x - CarterArtLayout.ANCHOR.x
	var right := used.end.x - CarterArtLayout.ANCHOR.x
	if face_left:
		var was := left
		left = -right
		right = -was
	return Rect2(Vector2(left, used.position.y - CarterArtLayout.ANCHOR.y) * CarterArtLayout.SCALE,
		Vector2(right - left, used.size.y) * CarterArtLayout.SCALE)


# Mason drawn on his sheet's `frames` with his soles on `feet`: the used pixels of those frames, in world px.
static func mason_drawn(t, feet: Vector2, frames: Array) -> Rect2:
	var row: Dictionary = PuppetLayout.anim(&"mason", &"idle")
	var twin := PuppetLayout.twin_path(&"mason", row.sheet)
	var image: Image = load(twin if twin != "" else row.sheet).get_image()
	var spec: Dictionary = PuppetLayout.spec(&"mason")
	var frame: Vector2 = spec.frame
	var used := Rect2()
	for f: int in frames:
		var rect := Rect2(image.get_region(Rect2i(f * int(frame.x), 0, int(frame.x), int(frame.y))).get_used_rect())
		used = rect if used.size == Vector2.ZERO else used.merge(rect)
	# His soles are the bottom edge of his feet texel's row.
	var soles: Vector2 = spec.feet + Vector2(0.0, 1.0)
	return Rect2(feet + (used.position - soles) * PuppetLayout.SCALE, used.size * PuppetLayout.SCALE)


#THE TIERS

static func tier_layout(t) -> void:
	var combo: Node = await enter(t, 100, &"form")
	var mason: Node2D = combo.puppets.get(&"mason")
	var carter: Node2D = combo.puppets.get(&"carter")
	var rest: Rect2 = drawn(mason.sprite)
	t.check(mason.global_position == Layout.MASON_REST and carter.global_position == Layout.CARTER_FEET,
		"Carter and Mason stand on their spots (%s, %s)" % [carter.global_position, mason.global_position])
	var pieces := {
		"Carter": drawn(carter.sprite),
		"Mason at rest": rest,
		"Mason landed": mason_drawn(t, Layout.MASON_LANDING, [13, 14]),
	}
	var over_top := Layout.floor_point(270.0, Layout.RUN_RADIUS + Layout.ZIG)
	var lifted := mason_drawn(t, over_top - Vector2(0, Layout.MASON_LIFT), [6, 7])
	t.log_p("Mason lifted over the run line's outer top: floor point %s, drawn %s" % [over_top, lifted])
	t.check(clear_of_jordan(lifted) and clear_of_hud(lifted) and GodLayout.FLOOR.has_point(over_top),
		"Mason lifted over the run line's top: his floor point on the floor, clear of Jordan and the HUD (top y %.0f)" % lifted.position.y)
	for piece: String in pieces:
		var rect: Rect2 = pieces[piece]
		t.check(clear_of_jordan(rect) and clear_of_hud(rect) and on_floor(rect) and in_view(rect),
			"%s on the floor and in view, clear of Jordan's mask and core and of the HUD (world %s, screen %s)" % [piece, rect, to_screen(rect)])

	var looping: bool = await t.wait_until(func(): return combo.beat == combo.Beat.LOOP, 60 * 3)
	t.check(looping, "the circle closes")
	var off_ellipse := []
	var outward := []
	var unclear := []
	var crowded := []
	var ring := Rect2()
	for i in Layout.CLONES:
		var figure: Sprite2D = combo.clones[i].figure
		var a := deg_to_rad(Layout.clone_angle(i))
		var exact := Layout.CENTRE + Vector2(Layout.CLONE_RADII.x * cos(a), Layout.CLONE_RADII.y * sin(a))
		if figure.global_position.distance_to(exact) > 1.0 or figure.global_position != Layout.clone_feet(i):
			off_ellipse.append(i)
		if figure.flip_h != (figure.global_position.x > Layout.CENTRE.x):
			outward.append(i)
		var pixels := clone_pixels(figure.flip_h)
		var rect := Rect2(figure.global_position + pixels.position, pixels.size)
		ring = rect if ring.size == Vector2.ZERO else ring.merge(rect)
		if not (clear_of_jordan(rect) and clear_of_hud(rect) and on_floor(rect) and in_view(rect)):
			unclear.append([i, rect, to_screen(rect)])
		for piece: String in ["Carter", "Mason at rest"]:
			if rect.intersects(pieces[piece]):
				crowded.append([piece, i])
	var screen := to_screen(ring)
	t.log_p("the circle's clones, every pose, drawn over world %s, screen %s: %.1f%% of the screen wide, %.1f%% tall" % [ring,
		screen, screen.size.x / ScreenView.VIEW_SIZE.x * 100.0, screen.size.y / ScreenView.VIEW_SIZE.y * 100.0])
	t.check(off_ellipse.is_empty(), "the %d clones' feet on their ellipse, ±1 px (off: %s)" % [Layout.CLONES, off_ellipse])
	t.check(outward.is_empty(), "each clone facing into the circle (not: %s)" % [outward])
	t.check(unclear.is_empty(), "each clone, in every pose, on the floor and in view, clear of Jordan's mask and core and of the HUD (not: %s)" % [unclear])
	t.check(crowded.is_empty(), "Carter and Mason at rest stand clear of every clone (not: %s)" % [crowded])
	var wall: Node = combo.wall
	t.check(is_instance_valid(wall) and wall is StaticBody2D and wall.collision_layer == 1 and wall.is_in_group(GodLayout.HAZARD_GROUP),
		"the wall is up, on the walls' layer, in the hazard group")

	extend_loop(combo)
	var progress: Node = t.root.get_node("GameProgress")
	var was_invincible: bool = progress.playtest_invincible
	progress.playtest_invincible = true
	var worst := {"out": 0.0, "at": Vector2.ZERO, "reach": 0.0}
	var z_ok := {"ok": true}
	var watch := func():
		var out := outside(soles(t))
		worst.reach = maxf(worst.reach, ((soles(t) - Layout.CENTRE) / Layout.SOLES_RADII).length())
		if out > worst.out:
			worst.out = out
			worst.at = soles(t)
		if combo.beat == combo.Beat.LOOP and t.player.z_index != 1:
			z_ok.ok = false
	t.process_frame.connect(watch)
	var pad := Pad.new(t)
	for way: Vector2 in WAYS:
		t.player.global_position = Layout.body_point(Layout.CENTRE)
		pad.steer(way * 100.0)
		await t.wait(hold_frames(way))
		pad.stop()
		await t.wait(2)
	# Each from well inside, so the dash reaches the wall at full speed.
	var dashed := 0
	for dash: Array in DASHES:
		await t.wait_until(func(): return t.defense.can_afford(t.defense.dash_stamina_cost) and not t.defense.is_dash_cooling_down(), 60 * 2)
		t.player.global_position = Layout.body_point(Layout.CENTRE + dash[0] * Layout.SOLES_RADII)
		pad.steer(dash[1] * 100.0)
		await t.wait(2)
		var before: int = t.player.last_dodge_physics_frame
		t.tap(KEY_W)
		await t.wait(30)
		if t.player.last_dodge_physics_frame != before:
			dashed += 1
		pad.stop()
		await t.wait(12)
	t.process_frame.disconnect(watch)
	t.check(combo.beat == combo.Beat.LOOP, "the circle still closed round the player when the holds and dashes are done")
	t.check(dashed == DASHES.size(), "every dash into the wall went (%d of %d)" % [dashed, DASHES.size()])
	progress.playtest_invincible = was_invincible
	t.log_p("the soles' furthest outside SOLES_RADII: %.2f px at %s; furthest out, %.3f of the ellipse" % [worst.out, worst.at,
		worst.reach])
	t.check(worst.reach >= 0.97, "and they did reach the wall (%.3f of SOLES_RADII)" % worst.reach)
	t.check(worst.out <= WALL_SLACK, "8 directions held from the centre and 4 dashes into the wall: the soles never more than 6 px outside SOLES_RADII (%.2f)" % worst.out)
	t.check(z_ok.ok and combo.beat == combo.Beat.LOOP, "the player one z over the clones all through the sweep")


static func tier_bot(t) -> void:
	var combo: Node = await enter(t)
	var hits := Hits.new(t.defense, combo)
	var jordan: int = t.boss.boss_health
	var hype: float = t.player.hype.hype
	var first: int = Layout.first_clone(Layout.CENTRE, Vector2.UP)
	var run: Run = await run_loop(t, combo)
	var fires: Array = combo.fires
	var order_ok := fires.size() == Layout.FIRES
	var counts := {}
	var worst_gap := 0.0
	var worst_land := 0.0
	for k in fires.size():
		var fire: Dictionary = fires[k]
		order_ok = order_ok and fire.clone == (first + k) % Layout.CLONES
		counts[fire.clone] = counts.get(fire.clone, 0) + 1
		worst_land = maxf(worst_land, absf(fire.landed - fire.at - Layout.TRAVEL))
		if k > 0:
			worst_gap = maxf(worst_gap, absf(fire.at - fires[k - 1].at - Layout.cadence(k - 1)))
	t.log_p("fires %d, the first from clone %d (the nearest: %d); worst gap off %.4f s, worst landing off %.4f s" % [
		fires.size(), fires[0].clone if not fires.is_empty() else -1, first, worst_gap, worst_land])
	t.check(order_ok, "%d fires, the first from the clone nearest the player, then clockwise" % Layout.FIRES)
	# Past a whole lap, the clones from the first round to where the sweep stops fire once more than the rest.
	var twice := Layout.FIRES % Layout.CLONES
	var shares := []
	for k in Layout.CLONES:
		var clone: int = (first + k) % Layout.CLONES
		shares.append(counts.get(clone, 0) == Layout.FIRES / Layout.CLONES + (1 if k < twice else 0))
	t.check(counts.size() == Layout.CLONES and shares.all(func(ok: bool) -> bool: return ok),
		"every clone fires, the first %d of them once more (%s)" % [twice, [counts.values()]])
	t.check(worst_gap <= FRAME + 0.0001, "a cadence (%.3f s) apart, ±1 frame (worst off by %.4f)" % [Layout.cadence(0), worst_gap])
	t.check(worst_land <= FRAME + 0.0001, "each lands 0.10 s after it fires (worst off by %.4f)" % worst_land)
	var beamed: Array = hits.of(Layout.BEAM_ID)
	var pooed: Array = hits.of(Layout.POO_ID)
	t.log_p("THE BOT: smallest lead over the chasing band's edge (lambda - delta) %.2f deg at %.2f s; smallest margin ahead %.2f deg; over %d live steps" % [
		run.min_margin, run.margin_at, run.min_front, run.steps])
	t.log_p("hits %s; drops %d; hype %.1f -> %.1f" % [hits.list, combo.drops.size(), hype, t.player.hype.hype])
	var clean_hype: float = Layout.HYPE_LAP * Layout.FIRES / float(Layout.CLONES) + Layout.HYPE_CLEAN
	t.check(not hits.list.is_empty() or absf(t.player.hype.hype - hype - clean_hype) <= 0.01,
		"a clean run pays each lap's hype, a part lap its share, and the clean loop's (%.1f)" % (t.player.hype.hype - hype))
	t.log_p("the first fires at %s; the first drops (at, Mason's lead on the player) %s" % [
		fires.slice(0, 5).map(func(f: Dictionary) -> float: return snappedf(f.at, 0.001)),
		combo.drops.slice(0, 5).map(func(d: Dictionary) -> Array: return [snappedf(d.at, 0.001), snappedf(wrapf(d.angle - d.player, -180.0, 180.0), 0.1)])])
	# On the first fire he is exactly 40 degrees ahead of a bot at its cap, the least he drops at, so it may be his next
	# peak, ZIG_STEP on at the sweep's pace.
	var next_peak: float = fires[0].at + Layout.ZIG_STEP / (360.0 / Layout.LAP_TIME) if not fires.is_empty() else 0.0
	t.check(not combo.drops.is_empty() and combo.drops[0].at <= next_peak + FRAME + 0.0001,
		"Mason drops his first bomb as the first clone fires, or at his next peak (%.3f)" % (combo.drops[0].at if not combo.drops.is_empty() else -1.0))
	for report: Dictionary in combo.poo_hits:
		if report.result == HIT:
			var drop: Dictionary = combo.drops[int(String(report.bomb).trim_prefix("CirclePoo"))]
			t.log_p("the bomb stepped in lay at round angle %.1f, radius %.1f" % [Layout.round_angle(drop.point),
				Layout.floor_radius(drop.point)])
	t.check(beamed.is_empty() and combo.beam_hits.is_empty(), "no beam hit in %d fires (%d)" % [Layout.FIRES, beamed.size()])
	t.check(pooed.size() <= 1, "at most one bomb hit (%d)" % pooed.size())
	t.check(run.min_margin > 0.0, "the lead always clear of the chasing band (smallest %.2f deg)" % run.min_margin)

	var walking: bool = await t.wait_until(func(): return combo.beat == combo.Beat.WALK, 60 * 3)
	await t.wait(ceili(GodLayout.HUD_FADE / FRAME) + 2)
	var mason: Node2D = combo.mason
	var carter: Node2D = combo.carter
	var figures_gone: bool = combo.clones.all(func(clone) -> bool: return not is_instance_valid(clone.figure))
	var in_group: Array = t.get_nodes_in_group(GodLayout.HAZARD_GROUP)
	var walls: Array = in_group.filter(func(node: Node) -> bool: return node is StaticBody2D)
	var bombs: Array = in_group.filter(func(node: Node) -> bool: return node.get_script() == POO_SCRIPT)
	t.check(walking and figures_gone and walls.is_empty() and bombs.is_empty() and combo.turds.is_empty(),
		"the end: the clones, the wall and the bombs gone (%s, %d, %d)" % [figures_gone, walls.size(), bombs.size()])
	t.check(mason.global_position == Layout.MASON_LANDING and mason.sprite.position == mason.sprite_base_position and mason.z_index == 0,
		"Mason down beside Carter at %s (%s)" % [Layout.MASON_LANDING, mason.global_position])
	t.check(carter.current_anim == &"recover" and mason.current_anim == &"broken" and carter.punchable and mason.punchable,
		"both left open: Carter spent, Mason slumped (%s, %s)" % [carter.current_anim, mason.current_anim])
	t.check(is_equal_approx(t.boss.health_bar.modulate.a, 1.0), "the HUD back (%.2f)" % t.boss.health_bar.modulate.a)
	t.check(not t.player.is_action_locked and t.player.z_index == 0, "the player free, at their own z")

	await walk(t, combo, TO_CARTER)
	t.check(combo.beat == combo.Beat.PAYOFF and combo.target == carter and not mason.punchable,
		"a walk to Carter: he is the one (%s)" % [combo.target.boss if is_instance_valid(combo.target) else &""])
	var bars: int = await pay_off(t, combo)
	t.log_p("bars %d, Jordan %d -> %d" % [bars, jordan, t.boss.boss_health])
	t.check(bars == 3 and t.boss.boss_health == jordan - 3, "three presses and a three-bar mash on Carter: Jordan -3")
	await t.wait_until(func(): return t.sm.current_state != combo, 60 * 6)
	await t.wait(3)
	t.check(t.sm.current_state.name == "Idle" and combo.beat == combo.Beat.OFF and combo.puppets.is_empty()
		and t.get_nodes_in_group(GodLayout.HAZARD_GROUP).is_empty() and t.player.z_index == 0 and not t.player.is_action_locked,
		"then the wrap: the pair recalled, nothing left, the player free at their own z, and Idle (%s)" % t.sm.current_state.name)


static func tier_idle(t) -> void:
	var combo: Node = await enter(t, 6)
	var hits := Hits.new(t.defense, combo)
	var first_hit: bool = await t.wait_until(func(): return hits.list.size() >= 1, 60 * 4)
	var landed: float = combo.fires[0].landed if not combo.fires.is_empty() else -1.0
	var one: Dictionary = hits.list[0] if first_hit else {id = &"", at = -1.0, damage = 0}
	t.log_p("the first band landed at %.3f; hit %s" % [landed, one])
	t.check(one.id == Layout.BEAM_ID and one.damage == 2 and absf(one.at - landed) <= FRAME + 0.0001,
		"standing at the centre, the first band hits on its landing frame for a heart (%.3f, %.3f)" % [one.at, landed])
	await t.wait(10)
	await t.tap_pause()
	var paused: bool = t.paused
	var held_at: float = combo.circle_clock
	await t.wait(PAUSE_FRAMES)
	var after: float = combo.circle_clock
	await t.tap_pause()
	t.check(paused and is_equal_approx(held_at, after), "paused between the first two hits, circle_clock holds over %d frames (%.3f, %.3f)" % [PAUSE_FRAMES, held_at, after])
	await t.wait_until(func(): return t.player.playerHealth <= 0 or hits.list.size() >= 3, 60 * 4)
	var gaps := []
	for i in range(1, hits.list.size()):
		gaps.append(snappedf(hits.list[i].at - hits.list[i - 1].at, 0.001))
	t.log_p("hits %s; gaps %s" % [hits.list, gaps])
	t.check(hits.list.size() == 3 and gaps.all(func(gap: float) -> bool: return absf(gap - 1.0) <= 2.0 * FRAME + 0.0001),
		"then one every 1.0 s through the i-frames, ±2 frames (%s)" % [gaps])
	t.check(t.player.playerHealth == 0, "the third is the last heart")
	await t.wait(3)
	var strings: Node = t.current_scene.get_node(STRINGS)
	t.check(combo.beat == combo.Beat.OFF and not t.player.is_action_locked and not t.player.is_posed() and t.player.z_index == 0,
		"the attack lets go: no lock, no pose, the player's z back")
	t.check(t.get_nodes_in_group(GodLayout.HAZARD_GROUP).all(func(node: Node) -> bool: return node.is_queued_for_deletion())
		and combo.puppets.is_empty() and not is_instance_valid(combo.wall) and strings.line_count() == 0,
		"and nothing of its own is left: the wall, the clones, the beams, the bombs, Mason, the strings")
	var reached := false
	for i in 60 * 12:
		if t.current_scene != null and t.current_scene.scene_file_path == DEFEAT:
			reached = true
			break
		await t.process_frame
	t.check(reached, "then the Defeat screen")


static func tier_poo(t) -> void:
	var combo: Node = await enter(t)
	extend_loop(combo)
	var hits := Hits.new(t.defense, combo)
	var pad := Pad.new(t)
	var run := Run.new()
	while combo.fires.size() < POO_AFTER and combo.beat == combo.Beat.LOOP:
		bot_step(t, combo, pad, run)
		await t.physics_frame

	# Into the next bomb ahead, at the bot's own pace.
	var into: Node2D = null
	var lap_one: int = hits.list.size()
	var healthy: int = t.player.playerHealth
	for i in 60 * 4:
		if not is_instance_valid(into) or into.popped:
			into = next_bomb(combo, soles(t), Vector2(5, 60))
		bot_step(t, combo, pad, run, into)
		await t.physics_frame
		if hits.list.size() > lap_one:
			break
	var health: int = t.player.playerHealth
	var stepped: Array = hits.list.slice(lap_one)
	var squashed: Array = combo.poo_hits.filter(func(r: Dictionary) -> bool: return r.result == HIT)
	var bomb_hit: Node2D = null
	if not squashed.is_empty():
		for bomb: Node2D in combo.turds:
			if is_instance_valid(bomb) and bomb.name == squashed[-1].bomb:
				bomb_hit = bomb
	t.log_p("hits before %s; walking into %s: %s" % [hits.list.slice(0, lap_one), squashed.map(func(r: Dictionary) -> StringName: return r.bomb), stepped])
	t.check(stepped.size() == 1 and stepped[0].id == Layout.POO_ID and stepped[0].damage == 1 and healthy - health == 1,
		"walked into the next bomb: exactly half a heart of jordan_circle_poo")
	t.check(bomb_hit != null and bomb_hit.popped, "and it pops")
	lap_one = hits.list.size()

	# Across two more in the lower half, once the i-frames are out, each dash at least the immunity's cooldown after the
	# last. After each, Mason is watched for WATCH_FRAMES: a dash that takes the player past his 40 degrees has him
	# drop nothing until he is that far ahead of them again.
	var dodged := []
	var dash_at := -INF
	for n in 2:
		var bomb: Node2D = null
		var dashed := false
		while combo.beat == combo.Beat.LOOP:
			if t.player.is_invincible or combo.circle_clock - dash_at < 0.7:
				bot_step(t, combo, pad, run)
				await t.physics_frame
				continue
			if not is_instance_valid(bomb) or not bomb.live:
				bomb = next_bomb(combo, soles(t), Vector2(15, 70), BOTTOM, true)
			if bomb == null:
				bot_step(t, combo, pad, run)
				await t.physics_frame
				continue
			# Round the lower half the run heads right to left.
			var way := -1.0 if Layout.floor_angle(bomb.global_position) > 0.0 else 1.0
			var start: Vector2 = bomb.global_position - Vector2(way * DASH_FROM, 0)
			var to := start - soles(t)
			if absf(to.x) <= ALIGN.x and absf(to.y) <= ALIGN.y and beam_lead(t, combo) <= DASH_LEAD:
				pad.hold([KEY_RIGHT if way > 0.0 else KEY_LEFT])
				await t.physics_frame
				t.tap(KEY_W)
				dash_at = combo.circle_clock
				var dash := {bomb = bomb.name, at = dash_at, drops = combo.drops.size(), aheads = [], hurt = hits.list.size()}
				var reports: int = combo.poo_hits.size()
				for f in WATCH_FRAMES:
					if f == DASH_FRAMES:
						pad.stop()
						dash.hurt = hits.list.size() - dash.hurt
					elif f > DASH_FRAMES:
						bot_step(t, combo, pad, run)
					await t.physics_frame
					dash.aheads.append({at = combo.circle_clock, ahead = mason_ahead(t, combo)})
				var mine: Array = combo.poo_hits.slice(reports).filter(func(r: Dictionary) -> bool: return r.bomb == bomb.name)
				dash.results = mine.map(func(r: Dictionary) -> int: return r.result)
				dodged.append(dash)
				dashed = true
				break
			if combo.lead_of(start) <= LEAD_CAP:
				pad.steer(to, ALIGN.y)
			else:
				bot_step(t, combo, pad, run)
			await t.physics_frame
		if not dashed:
			break
	pad.stop()
	t.log_p("dashed across %s; hits since the step-in %s" % [dodged.map(func(d: Dictionary) -> Array: return [d.bomb, d.results, d.hurt]),
		hits.list.slice(lap_one)])
	t.check(dodged.size() == 2 and dodged.all(all_dodged), "dashed across two more: DODGED")
	t.check(dodged.all(func(d: Dictionary) -> bool: return d.hurt == 0), "and nothing lost to either dash")

	var dipped := 0
	var late := []
	var dropped_behind := []
	for dash: Dictionary in dodged:
		var behind_at := -1.0
		var ahead_at := -1.0
		for sample: Dictionary in dash.aheads:
			if behind_at < 0.0 and sample.ahead < Layout.DROP_AHEAD:
				behind_at = sample.at
			elif behind_at >= 0.0 and sample.ahead >= Layout.DROP_AHEAD:
				ahead_at = sample.at
				break
		var since: Array = combo.drops.slice(dash.drops).filter(func(d: Dictionary) -> bool: return d.at <= dash.aheads[-1].at)
		t.log_p("the dash at %.3f put the player past his 40 degrees at %.3f, and he was that far ahead again at %.3f; his lead on the player at each drop since %s" % [
			dash.at, behind_at, ahead_at, since.map(func(d: Dictionary) -> float: return snappedf(wrapf(d.angle - d.player, -180.0, 180.0), 0.1))])
		if behind_at < 0.0:
			continue
		dipped += 1
		if ahead_at < 0.0 or ahead_at - dash.at > 1.0:
			late.append(dash.bomb)
		for drop: Dictionary in since:
			if drop.at < ahead_at or ahead_at < 0.0 or wrapf(drop.angle - drop.player, -180.0, 180.0) < Layout.DROP_AHEAD:
				dropped_behind.append(drop.at)
	t.check(dipped >= 1, "a dash took the player past Mason's 40 degrees (%d of %d)" % [dipped, dodged.size()])
	t.check(late.is_empty(), "and he was 40 degrees ahead of them again within 1.0 s of it (late: %s)" % [late])
	t.check(dropped_behind.is_empty(), "dropping nothing until he was (%s)" % [dropped_behind])


# The holds and dashes of `layout` and the second pass along the bottom that `poo` dashes on need TEST_FIRES of sweep,
# and since the tuning of 2026-10-04 the attack fires one lap: the schedule, built as the circle closed, runs on past
# FIRES here exactly as JordanComboCircle._build_schedule lays it.
static func extend_loop(combo: Node) -> void:
	var fire_at: float = combo.schedule[-1].fire_at
	for k in range(combo.schedule.size(), TEST_FIRES):
		fire_at += Layout.cadence(k - 1)
		var off_at := fire_at + Layout.TRAVEL + Layout.cadence(k)
		combo.schedule.append({clone = (combo.k0 + k) % Layout.CLONES, charge_at = fire_at - Layout.charge_time(k),
			fire_at = fire_at, land_at = fire_at + Layout.TRAVEL, off_at = off_at, gone_at = off_at + Layout.FADE})


static func well_inside(soles_point: Vector2) -> bool:
	return ((soles_point - Layout.CENTRE) / Layout.SOLES_RADII).length() <= 0.97


# The soles' lead over the band last fired, round degrees: the smooth sweep runs up to a clone's step ahead of it.
static func beam_lead(t, combo: Node) -> float:
	if combo.fires.is_empty():
		return 0.0
	return fposmod(Layout.round_angle(soles(t)) - Layout.clone_round(combo.fires[-1].clone), 180.0)


static func mason_ahead(t, combo: Node) -> float:
	return wrapf(combo.mason_angle - Layout.round_angle(soles(t)), -180.0, 180.0)


static func all_dodged(dash: Dictionary) -> bool:
	return not dash.results.is_empty() and dash.results.all(func(r: int) -> bool: return r == DODGED)


# The nearest bomb lying live ahead of the soles, `ahead` round degrees on from them (min, max), inside `stretch` (floor
# degrees) when one is given; with `dashable`, only an outer one whose dash starts, DASH_FROM to its right, inside the
# wall. The inner ones lie at the edge of the lane a level band leaves at the circle's bottom.
static func next_bomb(combo: Node, at: Vector2, ahead: Vector2, stretch := Vector2(-INF, INF), dashable := false) -> Node2D:
	var theta := Layout.round_angle(at)
	var best: Node2D = null
	var best_ahead := INF
	for bomb: Node2D in combo.turds:
		if not is_instance_valid(bomb) or bomb.popped or bomb.fade_at >= 0.0:
			continue
		var round_from := fposmod(Layout.round_angle(bomb.global_position) - theta, 360.0)
		var where := fposmod(Layout.floor_angle(bomb.global_position), 360.0)
		if round_from < ahead.x or round_from > ahead.y or where < stretch.x or where > stretch.y:
			continue
		if dashable and not (Layout.floor_radius(bomb.global_position) > Layout.RUN_RADIUS
				and well_inside(bomb.global_position + Vector2(DASH_FROM, 0))):
			continue
		if round_from < best_ahead:
			best = bomb
			best_ahead = round_from
	return best
