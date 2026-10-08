extends RefCounted

# jordan_portals (coder C): Jordan's attack 3, Josh + Eric's portals (JordanComboPortals, JordanPortalsLayout,
# JordanPortalSpikes), in the god fight, each tier on a fresh fight whose rotation holds only the portals, started as
# soon as it opens, its rng seeded. --max-fps 60: the payoff's mash is real time. Every time is on the attack's own
# clock (portals_clock, game time) unless it says phase. tier=
# Every tier's start checks the player: warped to the nearest spot clear of the puppets, the sword portal and Eric's
# first arrival (START_CLEAR), facing up, and let go as the summon starts - or, standing clear, left where they were.
#   layout  the staging: Josh and Eric on their marks and the floor, Eric unflipped, the sword portal strictly between
#           them; the prop's blade base and the winded sword's (measured off their own pixels) on the portal (+-1 texel);
#           Josh, Eric, the recovery spot, the prop and the portal clear of Jordan's mask and core and of the HUD; the
#           layout's invariants; then 500 sampled hops, feint exits and spike waves each inside every placement rule;
#           the start from the kegs' end and from the spawn mark, and 300 sampled spots, clear of every zone and of
#           Josh's and Eric's drawn bodies.
#   spikes  a bot that stands still and parries every grab: hit only by jordan_portal_spike, for 1, with its soles in a
#           live ellipse; every blade 0.40 s after its portal, to the frame; never more than 5 up; no aimed live window
#           inside any contact's margin; every grab parried, feints included, a rush every 1.17 to 1.75 s of the phase
#           (4 to 6 in 7 s, 7 to 12 in 13), and after each
#           parry Eric up 420 px or more off the player with the badge up as he rises. Then a bot that steps out of
#           what opens under it (15-frame reaction, along a free way) and parries: not a spike and not a squeeze.
#   grabs   a bot that never parries: three squeezes a catch and nothing else of Eric's, let go with i-frames, never a
#           spike while held and no blade rising near a hold; paused mid-charge and mid-hold, the charge still 0.50 s and
#           the squeezes 0.42 s apart.
#   feint   a forced feint (rush 1): it lands 0.80 s after its rush starts (+-1 frame), the exit showing 0.35 s before
#           he comes out, and a reader parries it; a forced feint on rush 3 bitten on the promised timing is still
#           parried with a second press (the rearm); 40 rolls, never the first rush and never twice running; and with
#           FEINT_MODE charge, a forced re-route during the charge under the badge, landing 0.30 s after it clears.
#   end     the phase ended under a charge (called off: no rush, the badge gone, home), under a rush (it lands, then
#           home), under a hold (three squeezes, the toss, then home); nothing opens after it and every spike plays
#           out; Eric winded on the sword portal and Josh recovering; walking into Josh's reach (Eric's in another run)
#           takes him: three presses and a three-bar mash, Jordan -3; the recall and a clean release.
#   death   at one half-heart a spike gives the Defeat screen, and the attack leaves nothing of its own behind.
#   edges   the dead zones the playtest of 2026-10-04 found: standing still against any wall or in a corner, or where a
#           spike's telegraph would sit under the HUD or his mask and core, no aimed spike ever opened. Now a player
#           standing still on each of those spots (warped out of a no-stand zone first) has aimed spikes opened under
#           their soles, and a bot that steps out of them from there takes none; walked and dashed at every no-stand
#           zone, the soles never get into one; caught under the top one, Eric's toss lands them outside it, free to walk.
#           And rule c with the parry stance: a guard pressed on a grab's contact and held through its window never
#           leaves the player rooted on an aimed blade (AIM_CLEAR's after-margin).
#   normal  all of them in turn.

const FIGHT := "res://Scenes/Bosses/JordanGodFightScene.tscn"
const DEFEAT := "res://Scenes/Core/DefeatScene.tscn"
const GOD := "Arena/JordanGodScene/God"
const SCENE := "Arena/JordanGodScene"
const PORTALS_SCRIPT := "res://Scripts/States/JordanGod/JordanComboPortals.gd"
const PORTAL_SCRIPT := preload("res://Scripts/JordanPortal.gd")
const SPIKE_SCRIPT := preload("res://Scripts/JordanPortalSpike.gd")
const Layout := preload("res://Scripts/JordanPortalsLayout.gd")
const Spikes := preload("res://Scripts/JordanPortalSpikes.gd")
const GodLayout := preload("res://Scripts/JordanGodLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const SEED := 20260928
const FRAME := 1.0 / 60.0
const TIERS := ["layout", "spikes", "grabs", "feint", "end", "death", "edges"]
# HitInfo.Result.
const IGNORED := 0
const HIT := 1
const PARRIED := 3
# The keep-clears, the kegs test's: Jordan's mask and core in world px, the HUD in screen px with its clearance.
const MASK := Rect2(912, 189, 96, 69)
const CORE := Rect2(936, 270, 48, 57)
const HUD_KEEP_OUT := [Rect2(720, 33, 480, 148), Rect2(10, 842, 406, 229), Rect2(1371, 946, 537, 126)]
const HUD_CLEARANCE := 12.0
const PUNCH_GAP := 9
const PAUSE_FRAMES := 45
# The seconds a parried rush takes, hop to stumble, at the quickest and the slowest (a feint's).
const RUSH_CYCLE := Vector2(1.17, 1.75)
const SAMPLES := 500
# Where attack 2 leaves the player (at Burak's feet) and where the fight puts them (its spawn mark), as soles.
const KEGS_END := Vector2(360, 954)
const SPAWN_SOLES := Vector2(620, 803)
# In the open, clear of every START_CLEAR zone.
const OPEN_SOLES := Vector2(1350, 1250)
# The player's drawn box off their soles, world px (24 x 52 on the screen at 2/3).
const PLAYER_BOX := Rect2(-18, -78, 36, 78)
const DIAGONAL := 0.70710678
const WAYS := [Vector2(1, 0), Vector2(DIAGONAL, DIAGONAL), Vector2(0, 1), Vector2(-DIAGONAL, DIAGONAL), Vector2(-1, 0),
	Vector2(-DIAGONAL, -DIAGONAL), Vector2(0, -1), Vector2(DIAGONAL, -DIAGONAL)]


# Every hit the player takes, on the attack's clock, with whether they were held and whether a live spike was under
# their soles as it landed.
class Hits:
	var list: Array = []
	var combo: Node
	var player: Node

	func _init(body: Node, attack: Node) -> void:
		combo = attack
		player = body
		body.get_node("Defense").hit_taken.connect(_on_hit)

	func _on_hit(hit: RefCounted) -> void:
		var soles: Vector2 = player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)
		var under := false
		for spike in combo.live_spikes:
			if is_instance_valid(spike) and spike.live() and spike.covers(soles):
				under = true
		list.append({id = hit.attack_id, at = combo.portals_clock, damage = hit.damage, held = player.is_grabbed, under = under})

	func of(id: StringName) -> Array:
		return list.filter(func(h: Dictionary) -> bool: return h.id == id)


# A player: parries every grab on its contact (a biter also presses on a feint's promised contact first), and a
# stepper walks out of any spike under it REACTION frames after it notices, along a way clear of every other.
class Bot:
	var t
	var combo: Node
	var parries := true
	var biter := false
	var steps := false
	var lead := 6
	var hold := 8
	var reaction := 15
	# Out the way that leaves what is under it soonest (a player's choice), rather than the roomiest.
	var quickest := false
	var held_block := 0
	var pressed_for := -1
	var bit_for := -1
	var frame := 0
	var noticed := {}
	var keys: Array = []
	var walk_until := -1
	var live_max := 0

	func _init(suite, attack: Node) -> void:
		t = suite
		combo = attack

	func tick() -> void:
		frame += 1
		live_max = maxi(live_max, combo.live_spikes.size())
		_parry()
		if steps:
			_step()

	func stop() -> void:
		if held_block > 0:
			t.release(KEY_SHIFT)
		held_block = 0
		for code in keys:
			t.release(code)
		keys.clear()

	func _parry() -> void:
		if held_block > 0:
			held_block -= 1
			if held_block == 0:
				t.release(KEY_SHIFT)
			return
		var index: int = combo.rushes.size() - 1
		if not parries or index < 0:
			return
		var rush: Dictionary = combo.rushes[index]
		var clock: float = combo.portals_clock
		if biter and rush.feint and bit_for != index and clock >= rush.at + Layout.RUSH_TIME - 2.0 * FRAME:
			bit_for = index
			_press()
			return
		var due: float = combo.rush_contact_at()
		if due > 0.0 and pressed_for != index and clock >= due - lead * FRAME:
			pressed_for = index
			_press()

	func _press() -> void:
		t.press(KEY_SHIFT)
		held_block = hold

	func _step() -> void:
		var soles: Vector2 = t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)
		var under: Array = []
		for spike in combo.live_spikes:
			if is_instance_valid(spike) and spike.stage <= SPIKE_SCRIPT.Stage.HOLD and spike.covers(soles):
				under.append(spike)
				if not noticed.has(spike):
					noticed[spike] = frame
		if not keys.is_empty():
			if under.is_empty() and frame >= walk_until:
				for code in keys:
					t.release(code)
				keys.clear()
			return
		for spike in under:
			if frame - int(noticed[spike]) >= reaction:
				_walk(_free_way(soles, under))
				return

	# The way out that stays clearest of every other spike for AIM_ESCAPE, on the floor.
	func _free_way(soles: Vector2, under: Array) -> Vector2:
		var best := Vector2.ZERO
		var best_room := -INF
		var best_out := INF
		var origins: Rect2 = t.player.ring_origins
		var walled := Layout.no_stand_zones()
		for way in WAYS:
			var room := INF
			var clear := true
			var out := INF
			for k in range(1, 23):
				var at: Vector2 = soles + way * minf(k * 6.0, Layout.AIM_ESCAPE)
				if not origins.grow(0.5).has_point(at - Vector2(0, Layout.SOLES_OVER_ORIGIN)):
					clear = false
				if walled.any(func(zone: Rect2) -> bool: return zone.has_point(at)):
					clear = false
				if out == INF and not under.any(func(spike) -> bool: return is_instance_valid(spike) and spike.covers(at)):
					out = k * 6.0
				for spike in combo.live_spikes:
					if not is_instance_valid(spike) or under.has(spike) or spike.stage > SPIKE_SCRIPT.Stage.HOLD:
						continue
					room = minf(room, at.distance_to(spike.global_position))
					if spike.covers(at):
						clear = false
			if not clear:
				continue
			if quickest and (out < best_out or (out == best_out and room > best_room)):
				best = way
				best_out = out
				best_room = room
			elif not quickest and room > best_room:
				best = way
				best_room = room
		return best

	func _walk(way: Vector2) -> void:
		if way == Vector2.ZERO:
			return
		if way.x > 0.3:
			keys.append(KEY_RIGHT)
		elif way.x < -0.3:
			keys.append(KEY_LEFT)
		if way.y > 0.3:
			keys.append(KEY_DOWN)
		elif way.y < -0.3:
			keys.append(KEY_UP)
		for code in keys:
			t.press(code)
		walk_until = frame + 4


static func run(t) -> void:
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	var combos: Array[String] = GodLayout.COMBOS.duplicate()
	for tier in tiers:
		t.log_p("-- jordan_portals %s" % tier)
		match tier:
			"layout":
				await tier_layout(t)
			"spikes":
				await tier_spikes(t)
			"grabs":
				await tier_grabs(t)
			"feint":
				await tier_feint(t)
			"end":
				await tier_end(t)
			"death":
				await tier_death(t)
			"edges":
				await tier_edges(t)
			_:
				t.check(false, "jordan_portals has no tier %s" % tier)
	GodLayout.COMBOS = combos


#GETTING THERE

# A fresh god fight whose rotation is the portals alone, the player at `health`, the attack started as the fight's Open
# hands over, its seed fixed and `pinned` rushes feinting: back once the summon is over and the opening under way.
static func enter(t, health := 100, pinned: Array[int] = [], at_soles := Vector2.INF) -> Node:
	var combos: Array[String] = [PORTALS_SCRIPT]
	GodLayout.COMBOS = combos
	await t.open_scene(FIGHT)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(GOD)
	t.sm = t.boss.state_machine
	t.player.playerHealth = health
	var combo := combo_of(t)
	t.check(combo != null, "the rotation holds the portals")
	await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 4)
	if at_soles.is_finite():
		t.player.global_position = at_soles - Vector2(0, Layout.SOLES_OVER_ORIGIN)
		t.player.velocity = Vector2.ZERO
		await t.wait(1)
	var standing := soles(t)
	t.sm.start_next_attack()
	combo.rng.seed = SEED
	combo.pinned_feint = pinned
	var opened: bool = await t.wait_until(func(): return combo.beat == combo.Beat.OPENING, 60 * 4)
	t.check(opened and t.sm.current_state == combo, "the portals start: Josh and Eric summoned, the opening under way")
	var free: bool = not t.player.is_action_locked and not t.player.is_posed()
	if Spikes.start_clear(standing):
		t.check(combo.start_warp.is_empty() and soles(t) == standing and free, "standing clear at %s, left where they were and free" % standing)
	else:
		t.check(not combo.start_warp.is_empty() and soles(t) == combo.start_warp.to and Spikes.start_clear(soles(t))
			and t.player.facing == t.player.Facing.UP and free,
			"standing at %s, warped clear to %s facing up, and free again" % [standing, soles(t)])
	return combo


static func combo_of(t) -> Node:
	for node in t.current_scene.find_children("*", "Node", true, false):
		var script: Script = node.get_script()
		if script != null and script.resource_path == PORTALS_SCRIPT:
			return node
	return null


static func soles(t) -> Vector2:
	return t.player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)


# The bot plays until `until` holds (or `frames` run out); whether it did.
static func play(t, bot: Bot, until: Callable, frames := 60 * 20) -> bool:
	for i in frames:
		if until.call():
			return true
		bot.tick()
		await t.physics_frame
	return until.call()


static func phase_over(combo: Node) -> bool:
	return combo.beat == combo.Beat.WALK or combo.beat == combo.Beat.PAYOFF or combo.beat == combo.Beat.OFF


#THE KEEP-CLEARS

static func to_screen(rect: Rect2) -> Rect2:
	var zoom: float = GodLayout.VIEW_ZOOM
	return Rect2((rect.position - GodLayout.VIEW_FOCUS) * zoom + ScreenView.VIEW_SIZE / 2.0, rect.size * zoom)


static func clear_of_keep_outs(rect: Rect2) -> bool:
	if rect.intersects(MASK) or rect.intersects(CORE):
		return false
	var on_screen := to_screen(rect)
	for block: Rect2 in HUD_KEEP_OUT:
		if on_screen.intersects(block.grow(HUD_CLEARANCE)):
			return false
	return true


static func drawn(sprite: Sprite2D) -> Rect2:
	return sprite.get_global_transform() * sprite.get_rect()


# Where a planted sword meets its dirt on a frame of `image` at `frame_x`: its blade's middle (between its outlines on
# BLADE_ROW, low enough that no hand is over it) and the dirt's first row (its dark top outline, dirt under it), as an
# edge point in texels.
const BLADE_ROW := 182
static func sword_base(image: Image, frame_x: int, seed_x: int) -> Vector2:
	var left := seed_x
	while left > 0 and not dark(image.get_pixel(frame_x + left, BLADE_ROW)):
		left -= 1
	var right := seed_x
	while right < 255 and not dark(image.get_pixel(frame_x + right, BLADE_ROW)):
		right += 1
	var middle := (left + right + 1) / 2.0
	var column := frame_x + floori(middle)
	var row := BLADE_ROW + 1
	while row < 190 and not (dark(image.get_pixel(column, row)) and brown(image.get_pixel(column, row + 1))):
		row += 1
	return Vector2(middle, row)


static func dark(pixel: Color) -> bool:
	return pixel.a > 0.0 and pixel.r < 0.05 and pixel.g < 0.05 and pixel.b < 0.05


static func brown(pixel: Color) -> bool:
	return pixel.a > 0.0 and pixel.r > pixel.b + 0.06


#THE TIERS

static func tier_layout(t) -> void:
	var combo: Node = await enter(t)
	await t.wait_until(func(): return combo.sword_planted, 60 * 3)
	await t.wait(2)
	var floor_rect: Rect2 = GodLayout.FLOOR
	t.check(combo.josh.global_position == Layout.JOSH_FEET and combo.eric.global_position == Layout.ERIC_FEET,
		"Josh on %s and Eric on %s" % [Layout.JOSH_FEET, Layout.ERIC_FEET])
	t.check([Layout.JOSH_FEET, Layout.ERIC_FEET, Layout.ERIC_RECOVERY, Layout.SWORD_PORTAL, Layout.STAGE_CENTRE].all(
		func(point: Vector2) -> bool: return floor_rect.has_point(point)), "their marks, the recovery, the portal and the centre on the floor")
	t.check(not combo.eric.face_left and not combo.eric.sprite.flip_h, "Eric unflipped")
	t.check(Layout.JOSH_FEET.x < Layout.SWORD_PORTAL.x and Layout.SWORD_PORTAL.x < Layout.ERIC_FEET.x,
		"the sword portal strictly between them (x %.0f < %.0f < %.0f)" % [Layout.JOSH_FEET.x, Layout.SWORD_PORTAL.x, Layout.ERIC_FEET.x])

	var prop_image: Image = load(Layout.PLANTED_SWORD).get_image()
	var prop_base := sword_base(prop_image, 0, 63)
	var prop_world: Vector2 = Layout.ERIC_FEET + (prop_base - Layout.FEET_ANCHOR) * Layout.SCALE
	t.log_p("the prop's blade base %s texels, world %s; the portal %s" % [prop_base, prop_world, Layout.SWORD_PORTAL])
	t.check(prop_world.distance_to(Layout.SWORD_PORTAL) <= Layout.SCALE, "the prop's blade base on the sword portal (+-1 texel)")
	var prop_rect := drawn(combo.prop)
	t.check(absf(prop_rect.end.y - Layout.SWORD_PORTAL.y) <= 0.5, "the prop drawn down to the floor line and no further (%.1f)" % prop_rect.end.y)
	var winded: Image = load("res://Assets/Characters/Eric/eric_winded.png").get_image()
	var winded_base := sword_base(winded, 0, 88)
	var winded_world: Vector2 = Layout.ERIC_RECOVERY + (winded_base - Layout.FEET_ANCHOR) * Layout.SCALE
	t.log_p("the winded sword's base %s texels, world %s at the recovery %s" % [winded_base, winded_world, Layout.ERIC_RECOVERY])
	t.check(winded_world.distance_to(Layout.SWORD_PORTAL) <= Layout.SCALE, "the recovery puts the winded sword on the portal (+-1 texel)")

	var eric_rect := drawn(combo.eric.sprite)
	var josh_rect := drawn(combo.josh.sprite)
	for item: Array in [["Josh", josh_rect], ["Eric", eric_rect], ["the prop", prop_rect],
			["Eric at his recovery", Rect2(eric_rect.position + Layout.ERIC_RECOVERY - Layout.ERIC_FEET, eric_rect.size)],
			["the sword portal", Rect2(Layout.SWORD_PORTAL - Layout.PORTALS[&"sword"].anchor * 3.0, Layout.PORTALS[&"sword"].frame * 3.0)]]:
		t.check(clear_of_keep_outs(item[1]), "%s clear of Jordan's mask and core and of the HUD (screen %s)" % [item[0], to_screen(item[1])])
	t.check(Layout.invariants().is_empty(), "the layout's invariants hold %s" % [Layout.invariants()])

	start_rules(t)
	await sample_rules(t)


# Where the player starts: the layout's kept-clear bodies hold what the sheets draw; from the kegs' end and the spawn
# mark, and 300 spots over the floor, the start spot is clear of every zone, on the floor, never up behind where they
# stood, with the player's drawn box off Eric's body, the sword and his arrival, and Eric's whole grab round them off
# Josh's body; a spot already clear is kept.
static func start_rules(t) -> void:
	var origins: Rect2 = t.player.ring_origins
	var bodies := puppet_bodies()
	t.log_p("drawn bodies: Josh %s, Eric %s" % bodies)
	t.check(Layout.JOSH_BODY.encloses(bodies[0]) and Layout.ERIC_BODY.encloses(bodies[1]),
		"the start keeps clear of all that Josh and Eric draw on their marks (%s, %s)" % [Layout.JOSH_BODY, Layout.ERIC_BODY])
	for from: Vector2 in [KEGS_END, SPAWN_SOLES]:
		var to := Spikes.start_spot(from, origins)
		t.check(to != from and to.y >= from.y and start_fault(to, origins, bodies) == "",
			"from %s the start is %s: beside or in front, clear (%s)" % [from, to, start_fault(to, origins, bodies)])
	var rng := RandomNumberGenerator.new()
	rng.seed = SEED
	var bad := 0
	var kept := 0
	for i in 300:
		var from := (origins.position + Vector2(0, Layout.SOLES_OVER_ORIGIN) + Vector2(rng.randf(), rng.randf()) * origins.size).round()
		var to := Spikes.start_spot(from, origins)
		if Spikes.start_clear(from):
			kept += 1
			if to != from:
				bad += 1
		elif to.y < from.y or start_fault(to, origins, bodies) != "":
			bad += 1
			t.log_p("from %s to %s: %s" % [from, to, start_fault(to, origins, bodies)])
	t.check(bad == 0, "300 sampled starts clear and on the floor, off both puppets' bodies, the clear ones kept (%d kept, %d bad)" % [kept, bad])


static func start_fault(at: Vector2, origins: Rect2, bodies: Array) -> String:
	if not Spikes.start_clear(at):
		return "in a zone"
	if not origins.grow(0.5).has_point(at - Vector2(0, Layout.SOLES_OVER_ORIGIN)):
		return "off the floor"
	var box := Rect2(at + PLAYER_BOX.position, PLAYER_BOX.size)
	var arrival := Rect2(Layout.STAGE_CENTRE + Layout.ERIC_DRAWN.position, Layout.ERIC_DRAWN.size)
	for body: Rect2 in [bodies[1], Layout.SWORD_BODY, arrival]:
		if box.intersects(body):
			return "the player over %s" % body
	if Rect2(at + Layout.GRAB_REACH.position, Layout.GRAB_REACH.size).intersects(bodies[0]):
		return "a grab there would land on Josh"
	return ""


# Josh's and Eric's drawn bodies on their marks, world px, off their own sheets: Josh's idle, throw and recovery; Eric's
# idle, empty wait, and the plant and plunge right of the sword (the sword itself stands in the portal's zone).
static func puppet_bodies() -> Array:
	var josh := Rect2()
	for sheet: String in ["josh_idle", "josh_throw", "josh_recovery"]:
		for f in 4:
			josh = merge(josh, used("res://Assets/Characters/Josh/%s.png" % sheet, Vector2i(80, 80), f, 0))
	var eric := used("res://Assets/Characters/Eric/eric_entrance.png", Vector2i(256, 192), 3, 0)
	for f in [36, 37]:
		eric = merge(eric, used("res://Assets/Characters/Eric/eric_sheet_v2.png", Vector2i(256, 192), f, 0))
	for f in [0, 13]:
		eric = merge(eric, used("res://Assets/Characters/Eric/eric_bearhug_v2.png", Vector2i(256, 192), f, 92))
	return [Rect2(Layout.JOSH_FEET + (josh.position - Vector2(40, 80)) * 3.0, josh.size * 3.0),
		Rect2(Layout.ERIC_FEET + (eric.position - Layout.FEET_ANCHOR) * 3.0, eric.size * 3.0)]


# The drawn pixels of frame `f` of a strip of `size` frames, from column `from_col` on, in texels of the frame.
static func used(path: String, size: Vector2i, f: int, from_col: int) -> Rect2:
	var image: Image = load(path).get_image()
	var rect := Rect2(image.get_region(Rect2i(f * size.x + from_col, 0, size.x - from_col, size.y)).get_used_rect())
	rect.position.x += from_col
	return rect


static func merge(a: Rect2, b: Rect2) -> Rect2:
	return b if not a.has_area() else a.merge(b)


# SAMPLES hops, feint exits and spike waves off a seeded rng, each checked against the rules as the plan writes them.
static func sample_rules(t) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = SEED
	var origins: Rect2 = t.player.ring_origins
	var zone := Rect2(Layout.HOP_BAND.grow(150.0))
	var hop_bad := 0
	var exit_bad := 0
	var exits_none := 0
	var wave_bad := 0
	var aimed := 0
	var messages: Array = []
	for i in SAMPLES:
		var at_soles := zone.position + Vector2(rng.randf(), rng.randf()) * zone.size
		at_soles = at_soles.clamp(origins.position + Vector2(0, 42), origins.end + Vector2(0, 42)).round()
		var spikes := random_spikes(rng, at_soles, rng.randi_range(0, 4))
		var hop := Spikes.hop_spot(rng, at_soles, spikes)
		var hop_fault := hop_faults(hop, at_soles, spikes)
		if hop_fault != "":
			hop_bad += 1
			if messages.size() < 6:
				messages.append("hop %s for soles %s: %s" % [hop, at_soles, hop_fault])
		var eric := Layout.HOP_BAND.position + Vector2(rng.randf(), rng.randf()) * Layout.HOP_BAND.size
		var exit := Spikes.feint_exit(rng, at_soles, eric)
		if not exit.is_finite():
			exits_none += 1
		else:
			var exit_fault := exit_faults(exit, at_soles, eric)
			if exit_fault != "":
				exit_bad += 1
				if messages.size() < 6:
					messages.append("exit %s for soles %s from %s: %s" % [exit, at_soles, eric, exit_fault])
		var pattern: StringName = Layout.PATTERNS[i % 2]
		var aim_ok := rng.randf() < 0.8
		var held := at_soles if rng.randf() < 0.1 else Vector2.INF
		var room := rng.randi_range(1, 3)
		var wave := Spikes.wave(rng, pattern, at_soles, spikes, [Layout.SWORD_PORTAL], room, aim_ok, held, origins)
		var wave_fault := wave_faults(wave, pattern, at_soles, spikes, room, aim_ok, held, origins)
		aimed += wave.filter(func(spot: Dictionary) -> bool: return spot.aimed).size()
		if wave_fault != "":
			wave_bad += 1
			if messages.size() < 6:
				messages.append("wave %s (%s) for soles %s: %s" % [wave, pattern, at_soles, wave_fault])
	for message in messages:
		t.log_p(message)
	t.log_p("%d samples: %d aimed spikes, %d with no feint exit" % [SAMPLES, aimed, exits_none])
	t.check(hop_bad == 0, "%d sampled hops keep every rule (%d don't)" % [SAMPLES, hop_bad])
	t.check(exit_bad == 0, "every sampled feint exit keeps every rule (%d don't)" % exit_bad)
	t.check(wave_bad == 0 and aimed > 0, "%d sampled spike waves keep every rule (%d don't)" % [SAMPLES, wave_bad])


static func random_spikes(rng: RandomNumberGenerator, at_soles: Vector2, count: int) -> Array:
	var out: Array = []
	for attempt in 40:
		if out.size() >= count:
			break
		var at := (at_soles + Vector2.from_angle(rng.randf() * TAU) * rng.randf_range(160.0, 500.0)).round()
		if out.all(func(other: Vector2) -> bool: return other.distance_to(at) >= Layout.PORTAL_SPACING):
			out.append(at)
	return out


static func hop_faults(hop: Vector2, at_soles: Vector2, spikes: Array) -> String:
	if not Rect2(Layout.HOP_BAND).grow(0.5).has_point(hop):
		return "out of the band"
	var away := hop.distance_to(at_soles)
	if away < Layout.HOP_RANGE.x or away > Layout.HOP_RANGE.y:
		return "%.0f px off the player" % away
	if hop.distance_to(Layout.JOSH_FEET) < Layout.HOP_CLEAR or hop.distance_to(Layout.SWORD_PORTAL) < Layout.HOP_CLEAR:
		return "too near Josh or the sword portal"
	for spike: Vector2 in spikes:
		if hop.distance_to(spike) < Layout.HOP_SPIKE_CLEAR:
			return "%.0f px off a spike" % hop.distance_to(spike)
	for rect in Layout.eric_rects(hop):
		if not clear_of_keep_outs(rect):
			return "him or his badge under a keep-clear"
	return ""


static func exit_faults(exit: Vector2, at_soles: Vector2, eric: Vector2) -> String:
	if not Rect2(Layout.HOP_BAND).grow(0.5).has_point(exit):
		return "out of the band"
	var away := exit.distance_to(at_soles)
	if away < Layout.EXIT_RANGE.x or away > Layout.EXIT_RANGE.y:
		return "%.0f px off the player" % away
	var turn := rad_to_deg(absf((exit - at_soles).angle_to(eric - at_soles)))
	if turn < Layout.EXIT_TURN:
		return "only %.0f degrees off his approach" % turn
	for rect in Layout.eric_rects(exit):
		if not clear_of_keep_outs(rect):
			return "him or his badge under a keep-clear"
	return ""


static func wave_faults(wave: Array, pattern: StringName, at_soles: Vector2, spikes: Array, room: int, aim_ok: bool,
		held: Vector2, origins: Rect2) -> String:
	if wave.size() > room:
		return "more than the room (%d)" % room
	var taken: Array = spikes + [Layout.SWORD_PORTAL]
	var hurting: Array = spikes.duplicate()
	var sides := {}
	for spot: Dictionary in wave:
		var at: Vector2 = spot.at
		if not GodLayout.FLOOR.encloses(Rect2(at - Layout.SPIKE_OPENING, Layout.SPIKE_OPENING * 2.0)):
			return "off the floor"
		var spec: Dictionary = Layout.PORTALS[&"spike"]
		if not clear_of_keep_outs(Rect2(at - spec.anchor * 3.0, spec.frame * 3.0)):
			return "its telegraph under a keep-clear"
		for other: Vector2 in taken:
			if at.distance_to(other) < Layout.PORTAL_SPACING:
				return "%.0f px from another portal" % at.distance_to(other)
		if held.is_finite() and at.distance_to(held) < Layout.HELD_CLEAR:
			return "within %.0f of the held player" % Layout.HELD_CLEAR
		if spot.aimed:
			if at != Spikes.aim_point(at_soles) or not Spikes.covers(at, at_soles) or not aim_ok or held.is_finite() 					or pattern != &"aimed":
				return "an aimed spike where it may not be"
			if escapes(at_soles, hurting.filter(func(p: Vector2) -> bool: return p != at), origins) < Layout.AIM_FREE_WAYS:
				return "an aimed spike with fewer than %d ways out" % Layout.AIM_FREE_WAYS
		else:
			var away := at.distance_to(at_soles)
			var reach: Vector2 = Layout.PINCER_RANGE if pattern == &"pincer" else Layout.FLANK_RANGE
			if away < reach.x - 1.0 or away > reach.y + 1.0 or away < Layout.FLANK_MIN - 0.5:
				return "a flank %.0f px off" % away
			var tilt := rad_to_deg(absf(atan2(at.y - at_soles.y, absf(at.x - at_soles.x))))
			if tilt > Layout.FLANK_TILT + 0.5:
				return "a flank %.0f degrees off level" % tilt
			sides[signf(at.x - at_soles.x)] = sides.get(signf(at.x - at_soles.x), 0) + 1
		taken.append(at)
		hurting.append(at)
	if pattern == &"pincer" and wave.size() == 2 and sides.size() != 2:
		return "a pincer with both flanks on one side"
	return ""


# The ways out of `at_soles`, checked here rather than trusted: its soles box off every ellipse, and on the floor, every
# ESCAPE_STEP out to AIM_ESCAPE.
static func escapes(at_soles: Vector2, others: Array, origins: Rect2) -> int:
	var count := 0
	for way: Vector2 in WAYS:
		var clear := true
		for k in range(1, ceili(Layout.AIM_ESCAPE / Layout.ESCAPE_STEP) + 1):
			var at := at_soles + way * minf(k * Layout.ESCAPE_STEP, Layout.AIM_ESCAPE)
			if not origins.grow(0.5).has_point(at - Vector2(0, Layout.SOLES_OVER_ORIGIN)):
				clear = false
			for other: Vector2 in others:
				var box := Rect2(at + Layout.SOLES_BOX.position, Layout.SOLES_BOX.size)
				var near := other.clamp(box.position, box.end)
				if ((near - other) / Layout.SPIKE_OPENING).length_squared() <= 1.0:
					clear = false
		if clear:
			count += 1
	return count


static func tier_spikes(t) -> void:
	var combo: Node = await enter(t)
	var hits := Hits.new(t.player, combo)
	var bot := Bot.new(t, combo)
	var played: bool = await play(t, bot, func(): return phase_over(combo), 60 * 20)
	bot.stop()
	t.check(played, "the phase plays out to the recovery (%s)" % combo.Beat.keys()[combo.beat])
	t.log_p("rushes %s" % [combo.rushes.map(func(r): return [snappedf(r.start, 0.01), r.feint, r.result])])
	t.log_p("spikes %d (%d aimed); hits %s" % [combo.spikes.size(), combo.spikes.filter(func(s): return s.aimed).size(),
		hits.list.map(func(h): return [h.id, snappedf(h.at, 0.01), h.under])])
	var others: Array = hits.list.filter(func(h: Dictionary) -> bool: return h.id != Layout.HIT_ID)
	var stray: Array = hits.of(Layout.HIT_ID).filter(func(h: Dictionary) -> bool: return h.damage != 1 or not h.under)
	t.check(others.is_empty() and stray.is_empty(),
		"standing, hit only by jordan_portal_spike, for 1, with the soles in a live ellipse (%d spike hits; others %s)" % [hits.list.size(), others])
	var late: Array = combo.spikes.filter(func(s: Dictionary) -> bool:
		return s.erupted >= 0.0 and (s.erupted - s.opened < Layout.SPIKE_TELL - 0.0001 or s.erupted - s.opened > Layout.SPIKE_TELL + FRAME + 0.0001))
	t.check(combo.spikes.size() > 10 and late.is_empty(), "every blade 0.40 s after its portal, to the frame (%d off)" % late.size())
	t.check(bot.live_max <= Layout.MAX_LIVE, "never more than %d up at once (%d)" % [Layout.MAX_LIVE, bot.live_max])
	var inside := aimed_in_margins(combo)
	t.check(inside.is_empty(), "no aimed live window inside any contact's margin %s" % [inside])
	# A spike's hit leaves a second of i-frames, which a grab meets first (IGNORED), before any parry.
	var met: Array = combo.rushes.filter(func(r: Dictionary) -> bool: return r.result == PARRIED or r.result == IGNORED)
	var span := rush_span()
	t.check(met.size() == combo.rushes.size() and combo.rushes.size() >= span.x and combo.rushes.size() <= span.y,
		"every grab parried or met inside a spike's i-frames: %d of %d rushes, %d to %d in the %.1f s" % [met.size(),
		combo.rushes.size(), span.x, span.y, Layout.PHASE_TIME])
	var emerged: Array = combo.hops.filter(func(h: Dictionary) -> bool: return h.charges and not h.reroute and h.rose_at >= 0.0)
	var short: Array = emerged.slice(1).filter(func(h: Dictionary) -> bool: return h.to.distance_to(h.player) < Layout.HOP_RANGE.x - 0.5 or not h.badge)
	t.log_p("hops up at %s" % [emerged.map(func(h): return [h.to, snappedf(h.to.distance_to(h.player), 1.0), h.badge])])
	t.check(emerged.size() >= 2 and short.is_empty(), "after each parry he comes up 420 px or more off the player, the badge up as he rises %s" % [short])

	combo = await enter(t)
	hits = Hits.new(t.player, combo)
	bot = Bot.new(t, combo)
	bot.steps = true
	# The recovery pays its hype in the step it turns to the walk.
	var changes: Array = []
	var last := {value = t.player.hype.hype}
	t.player.hype.hype_changed.connect(func(value: float, most: float) -> void:
		changes.append({gain = value - last.value, capped = value >= most - 0.01, walk = combo.beat == combo.Beat.WALK})
		last.value = value)
	played = await play(t, bot, func(): return phase_over(combo), 60 * 20)
	bot.stop()
	var paid: Array = changes.filter(func(c: Dictionary) -> bool: return c.walk)
	# A long phase's parries can fill the meter before the recovery, and a full meter has nothing left to take.
	var full_already: bool = paid.is_empty() and last.value >= t.player.hype.max_hype - 0.01
	t.check(combo.hits == 0 and (full_already or (paid.size() == 1
			and (absf(paid[0].gain - Layout.HYPE_CLEAN) <= 0.01 or paid[0].capped))),
		"a phase with no hit taken pays %.0f hype as they recover, unless the meter is full already %s (full %s)" % [
			Layout.HYPE_CLEAN, paid, full_already])
	var aimed: int = combo.spikes.filter(func(s): return s.aimed).size()
	t.log_p("stepping: spikes %d (%d aimed), hits %s, rushes %s" % [combo.spikes.size(), aimed, hits.list,
		combo.rushes.map(func(r): return r.result)])
	t.check(played and aimed > 0 and hits.list.is_empty(),
		"a bot that steps out of what opens under it and parries takes not a spike and not a squeeze (%d aimed at it)" % aimed)
	var parried: Array = combo.rushes.filter(func(r: Dictionary) -> bool: return r.result == PARRIED)
	t.check(parried.size() == combo.rushes.size() and combo.rushes.size() >= span.x and combo.rushes.size() <= span.y,
		"and parries every grab, feints too: %d of %d rushes, %d to %d in the %.1f s" % [parried.size(), combo.rushes.size(),
		span.x, span.y, Layout.PHASE_TIME])


# How many rushes a phase holds, parried: one every RUSH_CYCLE.x to RUSH_CYCLE.y seconds (4 to 6 in the 7 s it was).
static func rush_span() -> Vector2i:
	return Vector2i(floori(Layout.PHASE_TIME / RUSH_CYCLE.y), ceili(Layout.PHASE_TIME / RUSH_CYCLE.x))


# Every aimed spike whose live window meets a logged contact's margin (AIM_CLEAR before and after).
static func aimed_in_margins(combo: Node) -> Array:
	var out: Array = []
	for spike: Dictionary in combo.spikes:
		if not spike.aimed:
			continue
		for rush: Dictionary in combo.rushes:
			var contact: float = rush.contact_at
			if contact >= 0.0 and spike.live_from <= contact + Layout.AIM_CLEAR.y and spike.live_to >= contact - Layout.AIM_CLEAR.x:
				out.append([spike.opened, contact])
	return out


static func tier_grabs(t) -> void:
	var none: Array[int] = []
	var combo: Node = await enter(t, 100, none, KEGS_END)
	var hits := Hits.new(t.player, combo)
	var caught := 0
	var squeezed := true
	var let_go := true
	var paused_charge := false
	var paused_hold := false
	for i in 60 * 20:
		if phase_over(combo):
			break
		if not paused_charge and combo.move == combo.Move.CHARGE and combo.rushes.size() >= 1:
			paused_charge = true
			var charged_at: float = combo.hops[-1].rose_at
			await pause_here(t, combo, "mid-charge")
			var rushed: bool = await t.wait_until(func(): return combo.move == combo.Move.RUSH, 60)
			var took: float = combo.rushes[-1].at - charged_at
			t.check(rushed and absf(took - Layout.CHARGE_TIME) <= FRAME + 0.0001,
				"paused mid-charge, the rush still comes 0.50 s of game time after the charge started (%.3f)" % took)
		if combo.move == combo.Move.GRAB:
			caught += 1
			var before: int = hits.of(Layout.SQUEEZE_ID).size()
			if not paused_hold:
				await t.wait_until(func(): return combo.move == combo.Move.SQUEEZE, 60)
				paused_hold = true
				await pause_here(t, combo, "mid-hold")
			await t.wait_until(func(): return combo.move == combo.Move.TOSS_END, 60 * 3)
			var these: Array = hits.of(Layout.SQUEEZE_ID).slice(before)
			var apart := true
			for k in range(1, these.size()):
				apart = apart and absf(these[k].at - these[k - 1].at - Layout.SQUEEZE_TIME) <= FRAME + 0.0001
			squeezed = squeezed and these.size() == Layout.SQUEEZES and these.all(func(h): return h.damage == 1 and h.held) and apart
			let_go = let_go and not t.player.is_grabbed and t.player.is_invincible and t.player.sprite.visible
			t.log_p("catch %d: squeezes %s" % [caught, these.map(func(h): return snappedf(h.at, 0.001))])
		await t.physics_frame
	var squeezes: Array = hits.of(Layout.SQUEEZE_ID)
	var stray: Array = hits.list.filter(func(h: Dictionary) -> bool:
		return h.id != Layout.HIT_ID and h.id != Layout.SQUEEZE_ID and not (h.id == Layout.GRAB_ID and h.damage == 0))
	var held_spikes: Array = hits.of(Layout.HIT_ID).filter(func(h: Dictionary) -> bool: return h.held)
	t.log_p("no parry: %d catches, hits %s" % [caught, hits.list.map(func(h): return [h.id, snappedf(h.at, 0.01), h.held])])
	t.check(caught >= 1 and squeezed and squeezes.size() == caught * Layout.SQUEEZES and stray.is_empty(),
		"never parried, three half-hearts of squeeze a catch and nothing else of Eric's, 0.42 s apart through a pause (%d catches)" % caught)
	t.check(let_go, "each time let go with i-frames, drawn again")
	t.check(held_spikes.is_empty(), "no spike ever touches the held player")
	var through: Array = []
	for rush: Dictionary in combo.rushes:
		if rush.held_from < 0.0:
			continue
		var until: float = rush.held_to if rush.held_to >= 0.0 else INF
		for spike: Dictionary in combo.spikes:
			# Spikes step before him: one erupting in the catch's own step was already up as it landed.
			if spike.erupted > rush.held_from + 0.0001 and spike.erupted <= until and spike.at.distance_to(rush.held_at) < Layout.HELD_CLEAR:
				through.append([spike.at, snappedf(spike.opened, 0.001), snappedf(spike.erupted, 0.001), snappedf(spike.retracted, 0.001)])
		t.log_p("hold %d at %s from %.3f to %.3f" % [rush.index, rush.held_at, rush.held_from, until])
	var retracted: int = combo.spikes.filter(func(s: Dictionary) -> bool: return s.retracted >= 0.0).size()
	t.check(through.is_empty(), "no blade rises within %.0f px of a hold after it lands (%d called off in their tell) %s" % [Layout.HELD_CLEAR, retracted, through])


static func pause_here(t, combo: Node, where: String) -> void:
	await t.tap_pause()
	var paused: bool = t.paused
	var clock: float = combo.portals_clock
	await t.wait(PAUSE_FRAMES)
	var after: float = combo.portals_clock
	await t.tap_pause()
	t.check(paused and is_equal_approx(after, clock), "paused %s, the attack's clock holds over %d frames (%.3f, %.3f)" % [where, PAUSE_FRAMES, clock, after])


static func tier_feint(t) -> void:
	var pins: Array[int] = [1, 3]
	var combo: Node = await enter(t, 100, pins, OPEN_SOLES)
	# It steps out of the spikes, so no spike's i-frames meet a grab before its parry.
	var bot := Bot.new(t, combo)
	bot.steps = true
	var played: bool = await play(t, bot, func(): return combo.rushes.size() >= 2 and combo.rushes[1].result >= 0, 60 * 12)
	var forced: Dictionary = combo.rushes[1] if combo.rushes.size() >= 2 else {}
	var feint: Dictionary = combo.feints[0] if not combo.feints.is_empty() else {}
	t.log_p("rush 1 %s; feint %s" % [forced, feint])
	t.check(played and forced.feint and absf(forced.contact_at - forced.at - Layout.FEINT_TOTAL) <= FRAME + 0.0001,
		"the forced feint lands 0.80 s after its rush starts (%.3f)" % (forced.get("contact_at", -1.0) - forced.get("at", 0.0)))
	t.check(not feint.is_empty() and feint.burst_at - feint.exit_at >= Layout.EXIT_TELL - 0.0001,
		"its exit shows %.3f s before he comes out" % (feint.get("burst_at", 0.0) - feint.get("exit_at", 0.0)))
	t.check(forced.get("result", -1) == PARRIED, "and a reader parries it")
	var crowded := exit_crowding(combo, feint)
	t.check(not feint.is_empty() and crowded.is_empty(),
		"no spike rises or opens within %.0f px of the exit while it shows %s" % [Layout.HOP_SPIKE_CLEAR, crowded])
	bot.biter = true
	played = await play(t, bot, func(): return combo.rushes.size() >= 4 and combo.rushes[3].result >= 0, 60 * 12)
	bot.stop()
	var bitten: Dictionary = combo.rushes[3] if combo.rushes.size() >= 4 else {}
	t.log_p("rush 3 %s" % [bitten])
	t.check(played and bitten.feint and absf(bitten.rearmed_at - bitten.at - Layout.REARM_AT) <= FRAME + 0.0001,
		"a feint on rush 3, rearmed at its promised contact (%.3f)" % (bitten.get("rearmed_at", -1.0) - bitten.get("at", 0.0)))
	t.check(bitten.get("result", -1) == PARRIED, "bitten on the promised timing, the real grab is still parried with a second press")

	Layout.FEINT_MODE = &"charge"
	var pin: Array[int] = [1]
	combo = await enter(t, 100, pin)
	bot = Bot.new(t, combo)
	bot.steps = true
	played = await play(t, bot, func(): return combo.rushes.size() >= 2 and combo.rushes[1].result >= 0, 60 * 12)
	bot.stop()
	Layout.FEINT_MODE = &"lunge"
	var rerouted: Dictionary = combo.rushes[1] if combo.rushes.size() >= 2 else {}
	var reroutes: Array = combo.hops.filter(func(h: Dictionary) -> bool: return h.reroute)
	t.log_p("charge mode: rush 1 %s; reroutes %s" % [rerouted, reroutes])
	t.check(played and rerouted.feint and reroutes.size() == 1 and reroutes[0].badge and reroutes[0].to == rerouted.exit,
		"FEINT_MODE charge: re-routed during the charge to an exit near the player, the badge on him all the way")
	t.check(absf(rerouted.get("contact_at", -1.0) - rerouted.get("at", 0.0) - Layout.RUSH_TIME) <= FRAME + 0.0001
		and rerouted.get("result", -1) == PARRIED, "the badge never clears early: it lands 0.30 s after it clears, and is parried")

	var rng := RandomNumberGenerator.new()
	rng.seed = SEED
	var rolls := 0
	var feints := 0
	var broken := 0
	while rolls < 40:
		var last := false
		var count := 0
		for index in 5:
			var feinted := Spikes.feint_roll(rng, index, last, count)
			rolls += 1
			if feinted and (index == 0 or last or count >= Layout.FEINTS_MAX):
				broken += 1
			if feinted:
				feints += 1
				count += 1
			last = feinted
	t.check(broken == 0 and feints > 0, "%d rolls: %d feints, never the first rush, never twice running, never over %d a phase" % [rolls, feints, Layout.FEINTS_MAX])


# Spikes round a feint's exit that rise or open while it shows (from its opening to his burst out): the ones still in
# their tell there are called off as it opens and none new opens there, so none should; a blade already up plays out.
static func exit_crowding(combo: Node, feint: Dictionary) -> Array:
	var out: Array = []
	if feint.is_empty():
		return out
	var from: float = feint.exit_at + 0.0001
	for spike: Dictionary in combo.spikes:
		if spike.at.distance_to(feint.exit) >= Layout.HOP_SPIKE_CLEAR:
			continue
		var rose_then: bool = spike.erupted > from and spike.erupted <= feint.burst_at
		var opened_then: bool = spike.opened > from and spike.opened <= feint.burst_at
		if rose_then or opened_then:
			out.append([spike.at, snappedf(spike.opened, 0.001), snappedf(spike.erupted, 0.001)])
	return out


static func tier_end(t) -> void:
	await end_under(t, "CHARGE", false, &"josh")
	await end_under(t, "RUSH", false, &"eric")
	await end_under(t, "GRAB", true, &"")


# The phase made to end as he is in `move` (its clock put on PHASE_TIME there); then, unless `take` is empty, the walk
# into that one's reach and the payoff, the wrap and a clean release.
static func end_under(t, move_name: String, hold: bool, take: StringName) -> void:
	var combo: Node = await enter(t)
	var hits := Hits.new(t.player, combo)
	var bot := Bot.new(t, combo)
	bot.parries = not hold
	var move: int = combo.Move[move_name]
	var ready := func() -> bool:
		if combo.move != move:
			return false
		match move_name:
			"CHARGE":
				return combo.rushes.size() >= 1 and combo.charge_left > 0.1
			"RUSH":
				return combo.rushes.size() >= 2 and combo.rush_clock < 0.05
		return combo.move_clock < 0.1
	var at_move: bool = await play(t, bot, ready, 60 * 12)
	var rushes_then: int = combo.rushes.size()
	combo.phase_clock = Layout.PHASE_TIME
	bot.tick()
	await t.physics_frame
	var ended: Dictionary = combo.ending
	t.log_p("ended under %s: %s" % [move_name, ended])
	t.check(at_move and ended.get("move", "") == move_name, "the phase ends with him in %s" % move_name)
	match move_name:
		"CHARGE":
			t.check(ended.cancelled and not combo.charging and not combo._badge_up() and combo.hops[-1].to == Layout.ERIC_RECOVERY,
				"the charge is called off at once: the badge gone and home")
		"RUSH":
			await play(t, bot, func(): return combo.rushes[-1].contact_at >= 0.0, 60)
			t.check(combo.rushes[-1].contact_at >= 0.0 and combo.rushes[-1].result == PARRIED, "the rush in flight resolves (%s)" % combo.rushes[-1])
		"GRAB":
			var before: int = hits.of(Layout.SQUEEZE_ID).size()
			await play(t, bot, func(): return combo.move == combo.Move.TOSS_END, 60 * 3)
			t.check(hits.of(Layout.SQUEEZE_ID).size() - before == Layout.SQUEEZES and not t.player.is_grabbed,
				"the hold plays out through its toss (%d squeezes after the end)" % (hits.of(Layout.SQUEEZE_ID).size() - before))
	var recovered: bool = await play(t, bot, func(): return combo.move == combo.Move.HOME or combo.beat == combo.Beat.WALK, 60 * 6)
	# Out of both reaches, as a player who had been walking about would be, so the recovery waits for the walk.
	if not t.player.is_grabbed:
		t.player.global_position = Vector2(960, 1300)
	recovered = recovered and await play(t, bot, func(): return combo.beat == combo.Beat.WALK, 60 * 6)
	bot.stop()
	t.check(combo.rushes.size() <= rushes_then + (1 if move_name == "RUSH" else 0), "no rush after the end (%d, %d)" % [rushes_then, combo.rushes.size()])
	var after: Array = combo.spikes.filter(func(s: Dictionary) -> bool: return s.opened > ended.clock + 0.0001)
	t.check(recovered and after.is_empty() and combo.live_spikes.is_empty(),
		"nothing opens after the end and every spike plays out before the recovery (%d after)" % after.size())
	t.check(combo.eric.global_position == Layout.ERIC_RECOVERY and combo.eric.current_anim == &"winded"
		and combo.josh.current_anim == &"recover" and not combo.prop.visible,
		"Eric winded on the sword portal, the prop hidden under his own sword, Josh recovering")
	if take == &"":
		return
	var puppet: Node2D = combo.puppets[take]
	var jordan: int = t.boss.boss_health
	await walk_into(t, combo, puppet)
	t.check(combo.beat == combo.Beat.PAYOFF and combo.target == puppet and not combo.puppets[&"eric" if take == &"josh" else &"josh"].punchable,
		"walking into %s's reach takes %s; the other stays out of it" % [take, take])
	for i in 3:
		t.tap(KEY_Q)
		await t.wait(PUNCH_GAP)
	await t.wait_until(func(): return t.player.finisher.is_active(), 60 * 2)
	await t.mash_tiered(t.TIER_PASS_FRAMES[2])
	await t.wait_until(func(): return combo.bars >= 0, 60 * 10)
	t.check(combo.bars == 3 and t.boss.boss_health == jordan - 3, "three presses and a three-bar mash on %s: Jordan -3 (%d, %d -> %d)" % [take, combo.bars, jordan, t.boss.boss_health])
	await t.wait_until(func(): return t.sm.current_state != combo, 60 * 6)
	await t.wait(3)
	var left: Array = leftovers(t)
	t.check(t.sm.current_state != combo and combo.puppets.is_empty() and left.is_empty(),
		"the recall, then a clean release: no portals, blades, prop, badges or stars %s" % [left])
	t.check(not t.player.is_action_locked and t.player.sprite.visible and not t.player.is_grabbed, "the player unlocked and drawn")


# Walks the player the way a player holds the keys to just in front of `puppet`, until the punches start.
static func walk_into(t, combo: Node, puppet: Node2D) -> void:
	var goal: Vector2 = puppet.global_position + Vector2(0, 30)
	var held: Array = []
	for i in 60 * 6:
		if combo.beat != combo.Beat.WALK:
			break
		var to: Vector2 = goal - soles(t)
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


# Whatever of the attack is still standing.
static func leftovers(t) -> Array:
	var out: Array = []
	var scene: Node = t.current_scene.get_node_or_null(SCENE)
	if scene == null:
		return out
	for node in scene.find_children("*", "Node", true, false):
		if node.is_queued_for_deletion():
			continue
		var script: Script = node.get_script()
		if script == PORTAL_SCRIPT or script == SPIKE_SCRIPT or node.name == &"PlantedSword" or node.name == &"DazeStars" \
				or String(node.name).begins_with("ParryTell") or String(node.name).begins_with("PortalFront"):
			out.append(node.name)
	return out


static func tier_death(t) -> void:
	var combo: Node = await enter(t, 1)
	var hits := Hits.new(t.player, combo)
	await t.wait_until(func(): return t.player.playerHealth <= 0, 60 * 12)
	await t.wait(3)
	t.log_p("hits %s" % [hits.list])
	t.check(t.player.playerHealth == 0 and not hits.list.is_empty() and hits.list[-1].id == Layout.HIT_ID,
		"at one half-heart a spike takes the last")
	t.check(combo.beat == combo.Beat.OFF and combo.live_spikes.is_empty() and leftovers(t).is_empty()
		and not t.player.is_grabbed and t.player.sprite.visible, "the attack lets go and leaves nothing of its own %s" % [leftovers(t)])
	var reached := false
	for i in 60 * 12:
		if t.current_scene != null and t.current_scene.scene_file_path == DEFEAT:
			reached = true
			break
		await t.process_frame
	t.check(reached, "then the Defeat screen")


#THE DEAD ZONES (playtest 2026-10-04)

# Soles on each wall, in each corner, and in the no-stand zones under the HUD's blocks and his mask: all of them were
# spots no aimed spike reached.
const EDGE_SPOTS := [Vector2(-340, 800), Vector2(2260, 800), Vector2(-340, 180), Vector2(2260, 180), Vector2(960, 1500),
	Vector2(-340, 1480), Vector2(2260, 1480), Vector2(100, 1300), Vector2(960, 200)]
# Walked at each no-stand zone from outside it, holding these keys, then dashed at it twice.
const ZONE_PUSHES := [[Vector2(400, 1350), [KEY_LEFT, KEY_DOWN]], [Vector2(1300, 1450), [KEY_RIGHT]],
	[Vector2(960, 600), [KEY_UP]], [Vector2(300, 260), [KEY_RIGHT]], [Vector2(1700, 260), [KEY_LEFT]],
	[Vector2(-300, 1100), [KEY_DOWN]], [Vector2(2200, 1200), [KEY_DOWN]]]


static func tier_edges(t) -> void:
	var none: Array[int] = []
	for at: Vector2 in EDGE_SPOTS:
		var combo: Node = await enter(t, 100, none, at)
		var stood := soles(t)
		var zoned := Layout.no_stand_zones().any(func(zone: Rect2) -> bool: return zone.has_point(stood))
		var bot := Bot.new(t, combo)
		await play(t, bot, func(): return phase_over(combo), 60 * 20)
		bot.stop()
		var aimed: Array = combo.spikes.filter(func(s: Dictionary) -> bool: return s.aimed and Spikes.covers(s.at, stood))
		t.check(not zoned and aimed.size() >= 2,
			"standing still at %s (from %s): aimed spikes open under the soles (%d of %d)" % [stood, at, aimed.size(), combo.spikes.size()])
		combo = await enter(t, 100, none, at)
		var hits := Hits.new(t.player, combo)
		bot = Bot.new(t, combo)
		bot.steps = true
		bot.quickest = true
		# A practised player: a 0.2 s reaction, and a tap of the guard rather than a hold. Rule c lets a grab land 0.29 s
		# into a spike's tell, and a guard held through it roots them there.
		bot.reaction = 12
		bot.hold = 4
		await play(t, bot, func(): return phase_over(combo), 60 * 20)
		bot.stop()
		var spiked: Array = hits.of(Layout.HIT_ID)
		var aimed_here: int = combo.spikes.filter(func(s: Dictionary) -> bool: return s.aimed).size()
		t.check(spiked.is_empty() and aimed_here > 0,
			"from %s, stepping out of them takes no spike (%d aimed; hits %s)" % [at, aimed_here, hits.list])
	for push: Array in ZONE_PUSHES:
		var combo: Node = await enter(t, 100, none, OPEN_SOLES)
		t.player.global_position = push[0] - Vector2(0, Layout.SOLES_OVER_ORIGIN)
		await t.wait(2)
		var deepest := 0.0
		for code in push[1]:
			t.press(code)
		for f in 70:
			await t.physics_frame
			deepest = maxf(deepest, zone_depth(soles(t)))
		for dash in 2:
			t.tap(KEY_W)
			for f in 40:
				await t.physics_frame
				deepest = maxf(deepest, zone_depth(soles(t)))
		for code in push[1]:
			t.release(code)
		t.check(deepest <= 0.0, "walked and dashed from %s at a no-stand zone: the soles never in one (%s, %.2f px deep)" % [
			push[0], soles(t), deepest])
	# Rule c with the parry stance in it: a guard pressed at the last moment and held holds the player for the whole
	# parry window, and still no aimed blade rises under them before they can step off it.
	for run in 3:
		var combo: Node = await enter(t, 100, none, OPEN_SOLES)
		combo.rng.seed = SEED + 1 + run
		var hits := Hits.new(t.player, combo)
		var bot := Bot.new(t, combo)
		bot.steps = true
		bot.quickest = true
		bot.reaction = 12
		# Three steps before the contact, the latest press that still lands in time (it reaches the player a step on).
		bot.lead = 3
		bot.hold = 20
		await play(t, bot, func(): return phase_over(combo), 60 * 20)
		bot.stop()
		var parried: Array = combo.rushes.filter(func(r: Dictionary) -> bool: return r.result == PARRIED)
		t.check(hits.of(Layout.HIT_ID).is_empty() and parried.size() == combo.rushes.size(),
			"run %d: parrying at the last moment and holding the guard, every grab parried (%d of %d) and no blade under them %s" % [
				run, parried.size(), combo.rushes.size(), hits.list])
	# Eric's toss puts the player 250 px over his feet: caught just under the top zone, they come down outside it, and
	# walk away.
	for at: Vector2 in [Vector2(960, 420), Vector2(700, 380), Vector2(1300, 400)]:
		var combo: Node = await enter(t, 100, none, OPEN_SOLES)
		t.player.global_position = at - Vector2(0, Layout.SOLES_OVER_ORIGIN)
		var bot := Bot.new(t, combo)
		bot.parries = false
		var tossed: bool = await play(t, bot, func(): return not combo.rushes.is_empty() and combo.rushes[0].held_to >= 0.0,
			60 * 12)
		bot.stop()
		await t.wait(2)
		var landed := soles(t)
		var depth := zone_depth(landed)
		await t.wait(40)
		var rested := soles(t)
		t.press(KEY_DOWN)
		await t.wait(20)
		t.release(KEY_DOWN)
		var walked := soles(t).y - rested.y
		t.check(tossed and depth <= 0.0 and walked > 100.0,
			"caught at %s and tossed: down at %s, outside every no-stand zone (%.1f px deep), and walking away (%.0f px)" % [
				at, landed, depth, walked])


# How deep inside a no-stand zone `at` is, px; 0 outside every one.
static func zone_depth(at: Vector2) -> float:
	var deepest := 0.0
	for zone: Rect2 in Layout.no_stand_zones():
		if zone.has_point(at):
			deepest = maxf(deepest, minf(minf(at.x - zone.position.x, zone.end.x - at.x), minf(at.y - zone.position.y, zone.end.y - at.y)))
	return deepest
