extends RefCounted

# jordan_kaiju (the kaiju coder, 2026-10-04): Jordan's phase 1 on the kaiju (scratchpad jordan_kaiju/PLAN.md), with
# JordanKaijuLayout.USE_KAIJU switched on for this run whatever the game ships with. tier=
#   layout     its walls walked and dashed into from 8 directions, never entered; every walkable spot in the head's
#              aim and the beam's reach; at home its crown, the rider, its head and its plates clear of the boss bar's
#              fade rect and every HUD piece, the bar never faded for it; no walkable spot drawn over by it beyond 12 px.
#   intro      a watched entrance on the plan's beats, ending grown at home with its walls up and him riding, the player
#              held every frame until his lines; a held ESC at the box, the grow, the climb, the lines and the card's
#              build-up each ending exactly there; a retry starts him riding, with no grow.
#   breath     standing still anywhere (the corners, every rope, under the bar): the beam reaches them every time; an
#              outrunner is never hit and ends past where it stops; a dash through it is a perfect dodge; a walker is
#              swept against their motion; its burn line hurts a walk into it, a dash across is safe and pays nothing;
#              under half health two passes the other way 1.2 s apart; no figure's blast within half a second before a
#              contact or 0.3 s after it over seeds and both phases; the yellow ring clear of the HUD.
#   stomp      it lands on a player standing anywhere and on a circling one; a learned parry knocks him off, onto the
#              mat; a first-exposure press at the badge plus a 250 ms reaction parries it 85% of 20 seeds; stepping out
#              sends its ring, and a tail comes only after a dodge; a parry puts the burn lines out and leaves nothing
#              live; a Break in the air waits for the landing, which crash-lands him off it into Broken; under half
#              health a second stomp a second or more after the first.
#   punish     from every spot: knocked off onto open floor, no fire, the player a short walk away; three punches and the
#              POW land and the POW dazes him; the mash's uppercut lands for the plain finisher's share; then he climbs
#              back on and it hops home. Left alone, his knock-off lasts its 4.0 s.
#   recoil     the opening after its breath (the user, 2026-10-04: more openings): its head down 0.3 s after the breath's
#              last pass, open for 3.0 s with its back wall stood back to x 590 and his hurtbox on, then shut, the wall
#              home and Idle; a player standing still far off deals nothing; from four spots (the far corner too) a player walks to him on the
#              floor and lands three punches and the POW for 4, and the POW dazes him (the user, 2026-10-06: "yes give the
#              kaiju breath opening the uppercut too"); the mash's uppercut lands for the plain finisher's share and shuts
#              the opening, its head stays down until the finisher is over, then comes up with him on it, his recoil off
#              the uppercut settled, and the player is slid clear of the wall as it comes back; the breath's line of fire
#              burns on through it; under half health one opening after both passes; a
#              Break in it throws him off into Broken with the wall home and the player clear; his KO in it ends it the
#              same way.
#   occlusion  stomps landed with the player put behind its body: the x-ray ghost is drawn over them.
#   defeat     KO punched on the mat, KO by a juggle, KO riding it (a blast): it shrinks back into the toy, its walls go,
#              nothing of his is left live, he lies on the defeat's last frame (or the juggle's), and the walk-out comes.
#   lazy       standing still, circling, the four corners, under the bar and walking about never pressing a thing:
#              each loses at least 4 half-hearts a minute or deals him nothing.
#   art        its drawn sheets wired as their contracts have them (art_source/jordan_kaiju/contract_wave1.json, _wave2,
#              _rider): every animation on its own sheet; at home the seat and the mouth on the approved points, him on
#              his ride sheet with its SEAT on the seat; on the charge stance its head turned frame by frame with its aim,
#              the mouth and the seat riding it, its plates lit row by row; its bow's seat frame by frame; the Phase B
#              roar's plates over it; the tail's arc frame by frame round its feet; a stomp landing its stomping foot on
#              its mark. Needs the sheets: imported by the editor, or read off their PNGs with art=raw.
#   model      (reports only, never fails) the experienced-player bot (playtest_1004/BRIEF.md) over seeds 1-8, first
#              and learned: per-attack hits, time to kill, half-hearts a minute, clear rate, attempts to a first clear.
#   answers    the model's Bot on the two hits it kept taking in the 2026-10-07 playtest: a pair of figures 0.30 s apart,
#              both parried by presses due on the fight's clock through the first parry's freeze; the breath's line of
#              fire between it and his lowered head with the bar under a dash: it waits for the bar, dashes square across
#              unburnt and lands a punch in the opening.
#   normal     every tier but art and model.
# Its own runs leave the switch on in this process only. art=raw (after `--`) reads the kaiju's sheets off their PNGs for
# the run (JordanKaijuLayout.test_textures), so every tier can play the drawn art before the editor has imported it.

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")
const ArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Breath := preload("res://Scripts/States/Jordan/JordanBreath.gd")
const Stomp := preload("res://Scripts/States/Jordan/JordanStomp.gd")
const Finisher := preload("res://Scripts/PlayerFinisher.gd")
const FunkoFigure := preload("res://Scripts/FunkoFigureScript.gd")
const FunkoThrow := preload("res://Scripts/JordanFunkoThrow.gd")
const BurnLine := preload("res://Scripts/JordanBurnLine.gd")
const Beam := preload("res://Scripts/JordanKaijuBeam.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const FIGHT := "res://Scenes/Bosses/JordanBossFightScene.tscn"
const BODY := "Arena/JordanScene/JordanCharacterBody"
const TIERS := ["layout", "intro", "breath", "stomp", "punish", "occlusion", "defeat", "lazy", "recoil", "answers"]
const Sheets := preload("res://Scripts/JordanKaijuSheets.gd")
const SEED := 20261004
const FRAME := 1.0 / 60.0
# The player's soles under their body's centre.
const FEET_OFFSET := 42.0
# The ropes' collision edges, which the player's body stays inside.
const ROPES := Rect2(105, 105, 1710, 870)
const PLAYER_BOX := Vector2(36, 81)
const ESCAPE_HOLD := 40
# A guard press this far ahead of a landing, inside the parry window.
const PARRY_LEAD := 4.0 / 60.0
# Standing spots (soles): the corners of the open ring, every rope, under the boss bar, against both walls, the middle.
const STAND_SPOTS: Array[Vector2] = [Vector2(692, 192), Vector2(1300, 192), Vector2(1788, 192), Vector2(960, 192),
	Vector2(1788, 560), Vector2(1788, 945), Vector2(1300, 945), Vector2(612, 945), Vector2(612, 700),
	Vector2(692, 420), Vector2(1200, 560)]


static func run(t) -> void:
	Layout.USE_KAIJU = true
	if OS.get_cmdline_user_args().has("art=raw"):
		read_raw_sheets(t)
	var tiers: Array = TIERS if t.tier == "normal" else [t.tier]
	for tier in tiers:
		t.log_p("-- jordan_kaiju %s" % tier)
		match tier:
			"layout":
				await tier_layout(t)
			"intro":
				await tier_intro(t)
			"breath":
				await tier_breath(t)
			"stomp":
				await tier_stomp(t)
			"punish":
				await tier_punish(t)
			"recoil":
				await tier_recoil(t)
			"occlusion":
				await tier_occlusion(t)
			"defeat":
				await tier_defeat(t)
			"lazy":
				await tier_lazy(t)
			"art":
				await tier_art(t)
			"model":
				await load("res://art_source/defense_tests/jordan/kaiju_model.gd").run(t)
			"answers":
				await tier_answers(t)
			_:
				t.check(false, "jordan_kaiju has no tier %s" % tier)


# Every sheet of the contract's, read off its PNG for this run.
static func read_raw_sheets(t) -> void:
	var read := 0
	for sheet_name in Sheets.SHEETS:
		var path: String = Layout.SHEET_DIR + Sheets.SHEETS[sheet_name].file
		var image := Image.load_from_file(ProjectSettings.globalize_path(path))
		if image != null:
			Layout.test_textures[path] = ImageTexture.create_from_image(image)
			read += 1
	t.log_p("  art=raw: %d of %d sheets read off their PNGs" % [read, Sheets.SHEETS.size()])


#GETTING THERE

# His fight on the kaiju past its entrance, lines and card, his turns parked in Idle and the player with health to
# spare.
static func enter(t, seed_value := SEED) -> void:
	seed(seed_value)
	await t.load_fight("jordan")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.sm.rng.seed = seed_value
	t.player.playerHealth = 1000
	await t.wait_until(func(): return t.sm.fighting, 600)
	park(t)
	await t.wait(2)


# A fresh instance of his fight, his entrance left to play.
static func fresh_scene(t) -> void:
	var old: int = t.current_scene.get_instance_id() if t.current_scene != null else 0
	t.change_scene_to_file(FIGHT)
	await t.wait_until(func(): return t.current_scene != null and t.current_scene.get_instance_id() != old, 600)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine


static func park(t) -> void:
	if t.sm.current_state != t.sm.states["Idle"]:
		t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.sm.states["Idle"].rested = -INF


# Back as a turn starts: riding it at home, nothing of his live, the player whole and out of i-frames.
static func home_again(t) -> void:
	for hazard in t.get_nodes_in_group("jordan_hazard"):
		hazard.queue_free()
	park(t)
	var kaiju: Node2D = t.sm.kaiju
	kaiju.place(Layout.HOME)
	kaiju.set_lift(0.0)
	kaiju.light_spines(0)
	kaiju.set_charge(0.0)
	kaiju.play_anim(&"idle")
	t.sm.set_mounted(true)
	t.boss.play_anim(&"ride_idle")
	t.sm.phase_b = false
	t.sm.finisher_stagger_timer.stop()
	t.player.unlock_actions()
	t.player.playerHealth = 1000
	t.clear_iframes()
	await t.wait(3)


static func soles(t) -> Vector2:
	return t.sm.player_feet()


static func at_feet(t, feet: Vector2) -> void:
	await t.settle_player(feet - Vector2(0, FEET_OFFSET))


static func strip_funkos(t) -> void:
	for node in t.get_nodes_in_group("jordan_hazard"):
		var script: Script = node.get_script()
		if script == FunkoThrow or script == FunkoFigure:
			node.queue_free()


# One turn from Idle, `each` called every physics step with it, its figures taken away as they come if `bare`, until
# it hands back to Idle (parked again) or something else takes over.
static func play_turn(t, state_name: String, bare: bool, each := Callable(), max_frames := 60 * 16) -> Node:
	var state: Node = t.sm.states[state_name]
	t.sm.on_child_transition(t.sm.current_state, state_name)
	for f in max_frames:
		if bare:
			strip_funkos(t)
		if each.is_valid():
			each.call(state)
		await t.physics_frame
		if t.sm.current_state != state:
			break
	if t.sm.current_state == t.sm.states["Idle"]:
		park(t)
	return state


# What the player has been hit by, and the perfect dodges they made, from now on.
class Log:
	var hits: Array = []
	var dodges: Array = []
	var parries: Array = []

	func _init(t) -> void:
		t.defense.hit_taken.connect(func(hit): hits.append({"id": hit.attack_id, "damage": hit.damage}))
		t.defense.perfect_dodged.connect(func(hit): dodges.append(hit.attack_id))
		t.defense.parried.connect(func(hit, _point, _staggered, _streak): parries.append(hit.attack_id))

	func of(list: Array, id: StringName) -> int:
		return list.filter(func(entry): return (entry.id if entry is Dictionary else entry) == id).size()

	func clear() -> void:
		hits.clear()
		dodges.clear()
		parries.clear()


# The arrows held for a direction, eight ways, and changes to them pressed and let go.
class Keys:
	var t
	var held: Array = []

	func _init(tester) -> void:
		t = tester

	func toward(direction: Vector2) -> void:
		var want: Array = []
		if direction.length() > 0.001:
			var d := direction.normalized()
			if d.x > 0.38:
				want.append(KEY_RIGHT)
			elif d.x < -0.38:
				want.append(KEY_LEFT)
			if d.y > 0.38:
				want.append(KEY_DOWN)
			elif d.y < -0.38:
				want.append(KEY_UP)
		for code in held:
			if not want.has(code):
				t.release(code)
		for code in want:
			if not held.has(code):
				t.press(code)
		held = want

	func stop() -> void:
		toward(Vector2.ZERO)


#LAYOUT

const WALL_TRIES := [
	[Vector2(760, 300), [KEY_LEFT]], [Vector2(760, 300), [KEY_LEFT, KEY_UP]], [Vector2(760, 420), [KEY_LEFT, KEY_DOWN]],
	[Vector2(680, 720), [KEY_LEFT]], [Vector2(680, 720), [KEY_LEFT, KEY_UP]], [Vector2(680, 820), [KEY_LEFT, KEY_DOWN]],
	[Vector2(630, 660), [KEY_UP]], [Vector2(720, 640), [KEY_UP, KEY_LEFT]],
]


static func tier_layout(t) -> void:
	await enter(t)
	var kaiju: Node2D = t.sm.kaiju
	t.check(kaiju.is_home() and kaiju.walls_up() and t.boss.mounted and kaiju.visible,
		"the kaiju at home with its walls up, him riding it")
	var deepest := 0.0
	var started_clear := true
	for entry in WALL_TRIES:
		await t.dash_ready()
		await t.settle_player(entry[0])
		started_clear = started_clear and wall_depth(t) <= 0.0
		for code in entry[1]:
			t.press(code)
		var most := 0.0
		for f in 50:
			await t.physics_frame
			most = maxf(most, wall_depth(t))
		t.tap(KEY_W)
		for f in 25:
			await t.physics_frame
			most = maxf(most, wall_depth(t))
		for code in entry[1]:
			t.release(code)
		t.log_p("  from %s holding %s: ended at %s, deepest %.2f px" % [entry[0], entry[1], t.player.global_position, most])
		deepest = maxf(deepest, most)
	t.check(started_clear and deepest <= 0.5, "walked and dashed into its walls from 8 directions, never into them (deepest %.2f px)" % deepest)

	var walkable := walkable_soles()
	var out_of_reach: Array = []
	for feet in walkable:
		var angle := aim_at(kaiju, feet)
		var mouth: Vector2 = kaiju.mouth_point()
		var degrees := rad_to_deg(angle)
		if degrees < Layout.BEAM_AIM_MIN - 0.01 or degrees > Layout.BEAM_AIM_MAX + 0.01 or mouth.distance_to(feet) > Layout.reach_to_ropes(mouth, angle) + 1.0:
			out_of_reach.append(feet)
	kaiju.aim_head(0.0)
	t.check(out_of_reach.is_empty(), "every one of %d walkable spots is in its aim and its beam's reach (out: %s)" % [walkable.size(), out_of_reach.slice(0, 6)])

	await t.wait(30)
	var hud: Array = t.carter_hud_rects()
	var pieces := home_pieces(kaiju)
	for piece_name in pieces:
		var rect: Rect2 = pieces[piece_name]
		var clash := hud.filter(func(h: Rect2) -> bool: return h.intersects(rect))
		t.check(not rect.intersects(Layout.HUD_FADE_RECT) and clash.is_empty(), "at home its %s %s is clear of the bar's fade rect and the HUD (%s)" % [piece_name, rect, clash])
	t.check(is_equal_approx(t.boss.hud_alpha, 1.0) and is_equal_approx(t.boss.health_bar.modulate.a, 1.0), "and the bar never fades for it at home")

	var covered: Array = []
	for feet in walkable:
		if feet.y >= Layout.HOME.y:
			continue
		var inner := Rect2(feet + Vector2(-PLAYER_BOX.x / 2.0 + 12.0, -PLAYER_BOX.y + 12.0), PLAYER_BOX - Vector2(24, 24))
		for q in [inner.position, inner.end, Vector2(inner.position.x, inner.end.y), Vector2(inner.end.x, inner.position.y), inner.get_center()]:
			if kaiju.covers(q):
				covered.append(feet)
				break
	t.check(covered.is_empty(), "no walkable spot is drawn over by it beyond 12 px (%s)" % [covered.slice(0, 6)])


# How far the player's body is into a wall, px: 0 outside them all.
static func wall_depth(t) -> float:
	var shape: CollisionShape2D = t.player.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var depth := 0.0
	for wall in Layout.WALLS:
		var overlap := wall.intersection(box)
		if overlap.has_area():
			depth = maxf(depth, minf(overlap.size.x, overlap.size.y))
	return depth


# Soles on a 40 px grid wherever the player's body fits: inside the ropes and out of the walls.
static func walkable_soles() -> Array[Vector2]:
	var out: Array[Vector2] = []
	for x in range(131, 1790, 40):
		for y in range(190, 950, 40):
			var feet := Vector2(x, y)
			var box := Rect2(feet - Vector2(PLAYER_BOX.x / 2.0, PLAYER_BOX.y), PLAYER_BOX)
			if ROPES.encloses(box) and not Layout.box_in_walls(box):
				out.append(feet)
	return out


# The head turned at `point` (its mouth moves as it turns), and the beam's angle from the mouth to it.
static func aim_at(kaiju: Node2D, point: Vector2) -> float:
	var angle: float = (point - kaiju.mouth_point()).angle()
	for i in 3:
		kaiju.aim_head(rad_to_deg(angle))
		angle = (point - kaiju.mouth_point()).angle()
	return angle


# On screen at home: its crown, him riding it, its head and its plates.
static func home_pieces(kaiju: Node2D) -> Dictionary:
	var art: Node2D = kaiju.art
	var plates := Rect2(art.to_global(Layout.PLATE_ROWS[0][0]), Vector2.ZERO)
	for row in Layout.PLATE_ROWS:
		var size: float = row[2]
		plates = plates.expand(art.to_global(row[0] + (row[1] as Vector2).normalized() * size)).expand(art.to_global(row[0] - Vector2(size, size) * 0.5))
	return {
		"crown": Rect2(kaiju.crown_point() - Vector2(4, 4), Vector2(8, 8)),
		"rider": Rect2(art.to_global(Layout.RIDER_CROWN + Vector2(-80, 0)), Vector2.ZERO).expand(art.to_global(Layout.SEAT + Vector2(-60, 60))).expand(art.to_global(Layout.RIDER_HAND + Vector2(40, -40))),
		"head": Rect2(art.to_global(Vector2(150, -488)), Vector2.ZERO).expand(art.to_global(Vector2(310, -330))),
		"plates": plates,
	}


#INTRO

const INTRO_BEATS := {&"box_open": 0.40, &"toss": 1.00, &"toy_flight": 1.08, &"grow": 2.00, &"roar": 3.20, &"climb": 4.00, &"cheer": 4.60}
const INTRO_SLACK := 0.06


static func tier_intro(t) -> void:
	var progress: Node = t.root.get_node("GameProgress")
	progress.entrances_seen.erase(FIGHT)
	await fresh_scene(t)
	var intro: Node = t.sm.states["Intro"]
	var seen := {"lines": false, "unheld": 0, "grew": false}
	var watch := func():
		if not is_instance_valid(t.sm) or not is_instance_valid(t.player):
			return
		if t.live_balloon() != null:
			seen.lines = true
		if not seen.lines and not t.player.is_talking:
			seen.unheld += 1
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return intro.entered, 60)
	var entered_at: float = t.boss.fight_clock
	await t.wait_until(func(): return intro.finished, 60 * 8)
	var late: Array = []
	for beat in INTRO_BEATS:
		var at: float = intro.beat_times.get(beat, INF) - entered_at
		if absf(at - INTRO_BEATS[beat]) > INTRO_SLACK:
			late.append("%s %.2f" % [beat, at])
	t.check(late.is_empty() and intro.beat_times.size() == INTRO_BEATS.size(), "a watched entrance on the plan's beats (%s)" % [late])
	await t.wait(2)
	var problems := end_state(t)
	t.check(problems.is_empty(), "it ends grown at home with its walls up and him riding it (%s)" % [problems])
	t.check(await t.wait_until(func(): return t.live_balloon() != null, 60 * 2), "then his lines")
	for i in 8:
		if t.live_balloon() == null:
			break
		await t.read_line()
		await t.wait(4)
	await t.wait_until(func(): return t.vs_card() != null and t.vs_card().is_playing(), 120)
	await t.skip_vs_card()
	t.check(await t.wait_until(func(): return t.sm.fighting, 60 * 4), "then the card and the fight")
	t.physics_frame.disconnect(watch)
	t.check(seen.unheld == 0, "the player held every frame until his lines (%d frames free)" % seen.unheld)

	for point in ["box", "grow", "climb", "lines", "card"]:
		progress.entrances_seen.erase(FIGHT)
		await fresh_scene(t)
		var cut_intro: Node = t.sm.states["Intro"]
		match point:
			"box":
				await t.wait_until(func(): return cut_intro.beat_times.has(&"box_open"), 60 * 3)
			"grow":
				await t.wait_until(func(): return cut_intro.beat_times.has(&"grow"), 60 * 4)
				await t.wait(20)
			"climb":
				await t.wait_until(func(): return cut_intro.beat_times.has(&"climb"), 60 * 6)
				await t.wait(15)
			"lines":
				await t.wait_until(func(): return t.live_balloon() != null, 60 * 8)
			"card":
				await t.wait_until(func(): return t.live_balloon() != null, 60 * 8)
				for i in 8:
					if t.live_balloon() == null:
						break
					await t.read_line()
					await t.wait(4)
				await t.wait_until(func(): return t.vs_card() != null and t.vs_card().is_playing(), 120)
				await t.wait(10)
		t.press(KEY_ESCAPE)
		await t.wait(ESCAPE_HOLD)
		t.release(KEY_ESCAPE)
		await t.wait(4)
		var left := end_state(t)
		t.check(left.is_empty() and t.live_balloon() == null and progress.entrances_seen.has(FIGHT) and not t.paused,
			"a held ESC at the %s lands where a watched entrance does (%s, balloon %s)" % [point, left, t.live_balloon()])
		await t.skip_vs_card()
		t.check(await t.wait_until(func(): return t.sm.fighting, 60 * 4), "and the fight starts from there")

	await fresh_scene(t)
	var anims := {}
	var mounted_from := [-1]
	for f in 60 * 3:
		if is_instance_valid(t.sm.kaiju):
			anims[t.sm.kaiju.current_anim] = true
			if mounted_from[0] < 0 and t.boss.mounted:
				mounted_from[0] = f
		await t.physics_frame
	t.check(mounted_from[0] >= 0 and mounted_from[0] <= 3 and not anims.has(&"grow") and not anims.has(&"toy"),
		"a retry starts him riding it at once (frame %d), with no grow (%s)" % [mounted_from[0], anims.keys()])
	t.check(end_state(t).is_empty(), "the same end state")


# What a finished entrance must leave, as a list of what isn't so.
static func end_state(t) -> Array:
	var problems: Array = []
	var kaiju: Node2D = t.sm.kaiju
	if not is_instance_valid(kaiju):
		return ["no kaiju"]
	if not kaiju.visible or not kaiju.is_home() or kaiju.lift != 0.0:
		problems.append("kaiju at %s lift %.0f visible %s" % [kaiju.feet_point(), kaiju.lift, kaiju.visible])
	if kaiju.current_anim != &"idle":
		problems.append("kaiju on %s" % kaiju.current_anim)
	if not kaiju.walls_up():
		problems.append("walls down")
	if not t.boss.mounted or t.boss.current_anim != &"ride_idle":
		problems.append("jordan mounted %s on %s" % [t.boss.mounted, t.boss.current_anim])
	if t.boss.sprite.visible:
		problems.append("his own sprite showing")
	if not is_equal_approx(ScreenView.zoom, 1.0):
		problems.append("view zoom %.2f" % ScreenView.zoom)
	if not t.get_nodes_in_group("jordan_hazard").is_empty():
		problems.append("hazards live")
	return problems


#BREATH

static func tier_breath(t) -> void:
	await enter(t)
	var seen_hits := Log.new(t)
	var hud: Array = t.carter_hud_rects()
	var missed: Array = []
	var badge_clash: Array = []
	for feet in STAND_SPOTS:
		await home_again(t)
		await at_feet(t, feet)
		seen_hits.clear()
		var badge_check := func(state: Node) -> void:
			if state.beat != Breath.Beat.LOCK:
				return
			for tell in t.live_tells():
				var sprite: Node2D = tell.get("sprite")
				if sprite == null:
					continue
				var rect: Rect2 = sprite.get_global_transform() * sprite.get_rect()
				if rect.position.y < 0.0 or hud.any(func(h: Rect2) -> bool: return h.intersects(rect)):
					badge_clash.append([feet, rect])
		var state: Node = await play_turn(t, "Breath", true, badge_check)
		if seen_hits.of(seen_hits.hits, &"jordan_kaiju_breath") != 1:
			missed.append([feet, state.plans.map(func(p): return [snappedf(rad_to_deg(p.start), 0.1), snappedf(rad_to_deg(p.end), 0.1)])])
	t.check(missed.is_empty(), "standing still on %d spots, the beam hits every one of them once (missed %s)" % [STAND_SPOTS.size(), missed])
	t.check(badge_clash.is_empty(), "its yellow ring whole on screen and clear of the HUD (%s)" % [badge_clash])

	var outran: Array = []
	for feet in [Vector2(1200, 560), Vector2(1000, 320), Vector2(1500, 800), Vector2(950, 820), Vector2(1400, 300)]:
		await home_again(t)
		await at_feet(t, feet)
		seen_hits.clear()
		var keys := Keys.new(t)
		var bot := {"go": -1.0}
		var run := func(state: Node) -> void:
			if state.plans.is_empty() or state.beat == Breath.Beat.DONE:
				keys.stop()
				return
			var plan: Dictionary = state.plans[0]
			if bot.go < 0.0:
				bot.go = state.clock + 0.20
			if state.clock < bot.go:
				return
			var a: float = (soles(t) - plan.origin).angle()
			keys.toward(Vector2.from_angle(a).rotated(PI / 2.0) * float(plan.dir))
		var state: Node = await play_turn(t, "Breath", true, run)
		keys.stop()
		var plan: Dictionary = state.plans[0]
		var past: float = (wrapf((soles(t) - plan.origin).angle() - plan.end, -PI, PI)) * plan.dir
		outran.append([feet, seen_hits.of(seen_hits.hits, &"jordan_kaiju_breath"), snappedf(rad_to_deg(past), 0.1)])
	t.log_p("  outrun [start, beam hits, degrees past its end]: %s" % [outran])
	t.check(outran.all(func(o): return o[1] == 0 and o[2] > 0.0), "an outrunner from a standing start is never hit and ends past where it stops")

	var dashed: Array = []
	for feet in [Vector2(1200, 560), Vector2(1000, 320), Vector2(1500, 800)]:
		await home_again(t)
		await at_feet(t, feet)
		await t.dash_ready()
		seen_hits.clear()
		var keys := Keys.new(t)
		var bot := {"done": false, "release_at": -1.0}
		var dash := func(state: Node) -> void:
			if state.plans.is_empty() or state.beat != Breath.Beat.FIRE:
				return
			var plan: Dictionary = state.plans[0]
			# Its band's near edge reaches the feet this long before its middle does.
			var edge: float = (Beam.HALF_WIDTH + Beam.FOOT_RADIUS) / float(plan.v_eff)
			if not bot.done and state.clock >= plan.contact - edge - 2.0 * FRAME:
				bot.done = true
				var a: float = (soles(t) - plan.origin).angle()
				keys.toward(-Vector2.from_angle(a).rotated(PI / 2.0) * float(plan.dir))
				t.tap(KEY_W)
				bot.release_at = state.clock + 0.1
			elif bot.done and bot.release_at > 0.0 and state.clock >= bot.release_at:
				keys.stop()
		await play_turn(t, "Breath", true, dash)
		keys.stop()
		dashed.append([feet, seen_hits.of(seen_hits.hits, &"jordan_kaiju_breath"), seen_hits.of(seen_hits.dodges, &"jordan_kaiju_breath")])
	t.log_p("  dash [start, beam hits, perfect dodges]: %s" % [dashed])
	t.check(dashed.all(func(d): return d[1] == 0 and d[2] == 1), "a dash through it at contact is a perfect dodge, never a hit")

	await home_again(t)
	await at_feet(t, Vector2(1300, 300))
	var walker := Keys.new(t)
	var loop := func(_state: Node) -> void:
		var y: float = soles(t).y
		if y >= 900.0:
			walker.toward(Vector2.UP)
		elif y <= 300.0 or walker.held.is_empty():
			walker.toward(Vector2.DOWN)
	var looped: Node = await play_turn(t, "Breath", true, loop)
	walker.stop()
	var lp: Dictionary = looped.plans[0]
	t.log_p("  walker: tangential %.0f px/s, sweep %+.0f" % [lp.tangential, lp.dir])
	t.check(lp.moving and is_equal_approx(lp.dir, -signf(lp.tangential)), "a walker crossing its aim is swept against their motion")

	await home_again(t)
	await at_feet(t, Vector2(1200, 560))
	var laid: Node = await play_turn(t, "Breath", true)
	var burn: Node2D = laid.burns[0] if not laid.burns.is_empty() else null
	t.check(is_instance_valid(burn) and burn.is_burning(), "it leaves a line of fire where it stopped")
	if is_instance_valid(burn):
		var on: Vector2 = burn.from.lerp(burn.to, 0.55)
		var across: Vector2 = (burn.to - burn.from).orthogonal().normalized()
		t.clear_iframes()
		await at_feet(t, on + across * 90.0)
		seen_hits.clear()
		var walk := Keys.new(t)
		walk.toward(-across)
		await t.wait_until(func(): return seen_hits.of(seen_hits.hits, &"jordan_burn_line") > 0, 40)
		walk.stop()
		t.check(seen_hits.of(seen_hits.hits, &"jordan_burn_line") == 1, "walking into the line burns")
		t.clear_iframes()
		await t.dash_ready()
		await at_feet(t, on + across * 90.0)
		seen_hits.clear()
		var dash_keys := Keys.new(t)
		dash_keys.toward(-across)
		t.tap(KEY_W)
		await t.wait(12)
		dash_keys.stop()
		await t.wait(10)
		var crossed: float = (soles(t) - on).dot(across)
		t.check(crossed < -30.0 and seen_hits.of(seen_hits.hits, &"jordan_burn_line") == 0 and seen_hits.of(seen_hits.dodges, &"jordan_burn_line") == 0,
			"a dash across it is safe and pays no perfect dodge (ended %.0f px across)" % crossed)

	await home_again(t)
	t.sm.phase_b = true
	await at_feet(t, Vector2(1300, 600))
	var twice: Node = await play_turn(t, "Breath", true)
	var gap: float = twice.plans[1].contact - twice.plans[0].contact if twice.plans.size() == 2 else 0.0
	t.check(twice.plans.size() == 2 and twice.plans[0].dir == -twice.plans[1].dir and twice.burns.size() == 2 and gap >= 1.2,
		"under half health it sweeps back the other way, %.2f s after, and lays a second line" % gap)

	var noisy: Array = []
	var turns := 0
	for s in range(1, 7):
		for phase in [false, true]:
			await home_again(t)
			t.sm.phase_b = phase
			t.sm.rng.seed = s
			seed(s)
			await at_feet(t, STAND_SPOTS[(s * 3) % STAND_SPOTS.size()])
			var blasts: Array = []
			var seen := {}
			var record := func(state: Node) -> void:
				for fig in t.hazards_of("FunkoFigureScript.gd"):
					if fig.phase == fig.Phase.EXPLODING and not seen.has(fig.get_instance_id()):
						seen[fig.get_instance_id()] = true
						blasts.append(state.clock + FunkoFigure._first_hit_time())
				t.player.playerHealth = 1000
			var state: Node = await play_turn(t, "Breath", false, record)
			turns += 1
			for plan in state.plans:
				for b in blasts:
					if b >= plan.contact - 0.5 and b <= plan.contact + 0.3:
						noisy.append([s, phase, snappedf(b, 0.01), snappedf(plan.contact, 0.01)])
			t.log_p("  seed %d phase_b %s: blasts %s, contacts %s" % [s, phase, blasts.map(func(b): return snappedf(b, 0.01)), state.plans.map(func(p): return snappedf(p.contact, 0.01))])
	t.check(noisy.is_empty(), "the quiet rule over %d turns: no blast within 0.5 s before a contact or 0.3 s after (%s)" % [turns, noisy])


#STOMP

static func tier_stomp(t) -> void:
	await enter(t)
	t.hold_break_gauge(t.boss)
	var seen_hits := Log.new(t)
	var stood: Array = []
	for feet in STAND_SPOTS:
		await home_again(t)
		await at_feet(t, feet)
		var state: Node = await play_turn(t, "Stomp", true)
		if state.results.is_empty() or not state.results[0].feet_inside:
			stood.append([feet, state.results])
	t.check(stood.is_empty(), "standing still on %d spots it comes down on them every time (missed %s)" % [STAND_SPOTS.size(), stood])

	await home_again(t)
	await at_feet(t, Vector2(1200 + 260, 560))
	var circler := Keys.new(t)
	var circle := func(_state: Node) -> void:
		var r: Vector2 = soles(t) - Vector2(1200, 560)
		circler.toward(r.rotated(PI / 2.0).normalized() - r.normalized() * (r.length() - 260.0) / 260.0)
	var circled: Node = await play_turn(t, "Stomp", true, circle)
	circler.stop()
	t.check(not circled.results.is_empty() and circled.results[0].feet_inside, "and on a player circling the ring")

	await home_again(t)
	await at_feet(t, Vector2(1300, 600))
	seen_hits.clear()
	var learned: Node = await play_turn(t, "Stomp", true, parry_at_landing(t, 0.0))
	var landed: Vector2 = learned.knocked_to
	t.check(not learned.results.is_empty() and learned.results[0].result == HitInfo.Result.PARRIED, "a learned parry at the landing parries it")
	t.check(t.sm.current_state.name == "Dismounted" and not t.boss.mounted and t.sm.kaiju.current_anim == &"kneel"
		and t.boss.to_global(ArtLayout.FLOOR_POINT).distance_to(landed) < 1.0,
		"it stumbles onto one knee and he tumbles off onto the mat at %s: Dismounted (%s)" % [landed, t.sm.current_state.name])

	var parried := 0
	var presses: Array = []
	for s in 20:
		await home_again(t)
		await at_feet(t, Vector2(1100 + 30 * (s % 5), 500 + 40 * (s % 4)))
		var react := maxf(0.15, 0.25 + 0.05 * REACTION_QUANTILES[s])
		presses.append(snappedf(react, 0.001))
		var state: Node = await play_turn(t, "Stomp", true, parry_after_tell(t, react))
		if not state.results.is_empty() and state.results[0].result == HitInfo.Result.PARRIED:
			parried += 1
	t.log_p("  first-exposure presses after the badge %s" % [presses])
	t.check(parried >= 17, "a first-exposure press at the badge plus a 250 +/- 50 ms reaction parries %d of 20" % parried)

	for case in ["step", "hit", "parry"]:
		await home_again(t)
		await at_feet(t, Vector2(1300, 600))
		t.sm.states["Stomp"].tail_chance = 1.0
		var each := Callable()
		var keys := Keys.new(t)
		if case == "step":
			each = func(state: Node) -> void:
				if state.beat == Stomp.Beat.LATCH and state.clock - state.beat_at >= 0.05:
					keys.toward(Vector2.RIGHT)
				elif state.beat > Stomp.Beat.DROP:
					keys.stop()
		elif case == "parry":
			each = parry_at_landing(t, 0.0)
		var state: Node = await play_turn(t, "Stomp", true, each)
		keys.stop()
		t.sm.states["Stomp"].tail_chance = 0.35
		var result: int = state.results[0].result if not state.results.is_empty() else -1
		t.log_p("  %s: result %s, rings %d, tails %d" % [case, result, state.rings.size(), state.tails.size()])
		match case:
			"step":
				t.check(result == HitInfo.Result.IGNORED and state.rings.size() == 1 and state.tails.size() == 1,
					"stepping out of it sends its ring, and then (at chance 1) the tail")
			"hit":
				t.check(result == HitInfo.Result.HIT and state.rings.is_empty() and state.tails.is_empty(), "a hit sends no ring and never the tail")
			"parry":
				t.check(result == HitInfo.Result.PARRIED and state.rings.is_empty() and state.tails.is_empty(), "a parry sends neither")

	await home_again(t)
	await at_feet(t, Vector2(1300, 600))
	await play_turn(t, "Breath", true)
	t.check(not t.sm.live_burns().is_empty(), "with a line of fire burning")
	var into: Node = await play_turn(t, "Stomp", true, parry_at_landing(t, 0.0))
	await t.wait(2)
	# The landing's own hit node and its cracks on the mat aside, which hurt nobody.
	var live: Array = t.get_nodes_in_group("jordan_hazard").filter(func(h): return is_instance_valid(h) and not h.is_queued_for_deletion() and h.get_script() != load("res://Scripts/JordanStompHit.gd") and h.name != "StompImpact" and not (h.get_script() == BurnLine and not h.is_burning()))
	t.check(into.results[0].result == HitInfo.Result.PARRIED and t.sm.live_burns().is_empty() and live.is_empty(),
		"a parry puts every line out and leaves nothing live (%s)" % [live])

	await home_again(t)
	await at_feet(t, Vector2(1300, 600))
	seen_hits.clear()
	var gauge: Node = t.boss.break_gauge
	var broke := {"done": false}
	var break_in_air := func(state: Node) -> void:
		if not broke.done and state.beat == Stomp.Beat.TRACK:
			broke.done = true
			gauge.locked = false
			gauge.set_physics_process(true)
			gauge.value = 0.0
			gauge.add(gauge.max_value)
	var crashed: Node = await play_turn(t, "Stomp", true, break_in_air)
	await t.wait_until(func(): return t.sm.current_state.name == "Broken", 30)
	await t.wait_until(func(): return t.sm.states["Broken"].slide_left <= 0.0, 240)
	var his_soles: Vector2 = t.boss.to_global(ArtLayout.FLOOR_POINT)
	t.check(crashed.crashed and not crashed.results.is_empty() and crashed.results[-1].get("crash", false) and seen_hits.of(seen_hits.hits, &"jordan_kaiju_stomp") == 0,
		"a Break in the air waits for the landing, which hurts nobody")
	t.check(t.sm.current_state.name == "Broken" and not t.boss.mounted and t.sm.kaiju.current_anim in [&"collapse", &"down"]
		and Layout.SOLES_BOUNDS.has_point(his_soles) and not Layout.box_in_walls(t.sm._body_box_at(his_soles)),
		"it crash-lands and collapses, and he is thrown off onto open floor into Broken (%s at %s)" % [t.sm.current_state.name, his_soles])
	t.hold_break_gauge(t.boss)

	await home_again(t)
	t.sm.phase_b = true
	await at_feet(t, Vector2(1300, 600))
	var double: Node = await play_turn(t, "Stomp", true)
	var spacing: float = double.impact_times[1] - double.impact_times[0] if double.impact_times.size() == 2 else 0.0
	t.check(double.impact_times.size() == 2 and spacing >= 1.0, "under half health a second stomp follows, %.2f s after the first" % spacing)


# The 20 quantiles of a standard normal, (i + 0.5) / 20: the model's first-exposure reaction, 250 +/- 50 ms, taken as its
# distribution rather than sampled, so the rate it gives is the rate a player gets.
const REACTION_QUANTILES := [-1.960, -1.440, -1.150, -0.935, -0.755, -0.598, -0.454, -0.319, -0.189, -0.063,
	0.063, 0.189, 0.319, 0.454, 0.598, 0.755, 0.935, 1.150, 1.440, 1.960]


# A guard press PARRY_LEAD before the landing (plus `late`).
static func parry_at_landing(t, late: float) -> Callable:
	var bot := {"pressed": false, "release": -1.0}
	return func(state: Node) -> void:
		if not bot.pressed and state.beat == Stomp.Beat.DROP and state.clock - state.beat_at >= state.drop_time - PARRY_LEAD + late:
			bot.pressed = true
			bot.release = state.clock + 0.1
			t.press(KEY_SHIFT)
		elif bot.pressed and bot.release > 0.0 and state.clock >= bot.release:
			bot.release = -1.0
			t.release(KEY_SHIFT)


# A guard press `react` seconds after the badge goes up.
static func parry_after_tell(t, react: float) -> Callable:
	var bot := {"pressed": false, "release": -1.0}
	return func(state: Node) -> void:
		if not bot.pressed and state.beat >= Stomp.Beat.LATCH and not state.latch_times.is_empty() and state.clock >= state.latch_times[0] + react:
			bot.pressed = true
			bot.release = state.clock + 0.1
			t.press(KEY_SHIFT)
		elif bot.pressed and bot.release > 0.0 and state.clock >= bot.release:
			bot.release = -1.0
			t.release(KEY_SHIFT)


#PUNISH

const PUNISH_SPOTS: Array[Vector2] = [Vector2(1300, 600), Vector2(692, 300), Vector2(1788, 560), Vector2(960, 192),
	Vector2(1200, 945), Vector2(612, 760), Vector2(1788, 945), Vector2(1000, 320)]


static func tier_punish(t) -> void:
	await enter(t)
	t.hold_break_gauge(t.boss)
	var pows := [0]
	t.player.combo.charged_hit_landed.connect(func(_target): pows[0] += 1)
	var finisher: Node = t.player.get_node("Finisher")
	# Its key bounce is real seconds, which a fixed-fps run outpaces.
	finisher.min_press_interval = 0.0
	for feet in PUNISH_SPOTS:
		t.boss.boss_health = t.boss.max_health
		await home_again(t)
		await at_feet(t, feet)
		var state: Node = await play_turn(t, "Stomp", true, parry_at_landing(t, 0.0))
		var spot: Vector2 = state.knocked_to
		var open: bool = t.sm.current_state.name == "Dismounted"
		var box: Rect2 = t.sm._body_box_at(spot)
		var clear: bool = Layout.SOLES_BOUNDS.has_point(spot) and ROPES.encloses(box) and not Layout.box_in_walls(box) and t.sm.live_burns().is_empty()
		var from: Vector2 = t.player.global_position
		t.place_under(t.boss.get_finisher_hurtbox())
		var walk: float = from.distance_to(t.player.global_position) / 600.0
		var health: int = t.boss.boss_health
		pows[0] = 0
		for i in 3:
			await t.swing_any()
		var dealt: int = health - t.boss.boss_health
		# PlayerFinisher's Phase: 2 is dazed, the mash's.
		var dazed: bool = await t.wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120)
		var share: float = finisher.finisher_damage_ratio * (Finisher.SUPERCHARGE_MULTIPLIER if finisher.supercharged else 1.0)
		var due: int = maxi(1, roundi(t.boss.max_health * share))
		health = t.boss.boss_health
		await t.mash_finisher()
		await t.wait_until(func(): return t.boss.boss_health < health, 90)
		var upper: int = health - t.boss.boss_health
		t.log_p("  %s: knocked to %s, walk %.2f s, dealt %d, POW %d, dazed %s, uppercut %d of %d" % [feet, spot, walk, dealt, pows[0], dazed, upper, due])
		t.check(open and clear and walk <= 0.9, "from %s he lands on open floor with no fire, %.2f s away" % [feet, walk])
		t.check(dealt == 4 and pows[0] == 1 and dazed, "three punches and the POW land (%d), and the POW dazes him" % dealt)
		t.check(upper == due, "the mash's uppercut lands for the plain finisher's %d (%d)" % [due, upper])
		var back: bool = await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 8)
		t.check(back and t.boss.mounted and t.sm.kaiju.is_home() and t.sm.kaiju.lift == 0.0, "then he climbs back on and it hops home")
	t.boss.boss_health = t.boss.max_health
	await home_again(t)
	await at_feet(t, PUNISH_SPOTS[0])
	await play_turn(t, "Stomp", true, parry_at_landing(t, 0.0))
	var lasted: float = t.sm.states["Dismounted"].elapsed - t.boss.fight_clock
	await t.wait_until(func(): return t.sm.current_state.name != "Dismounted", 60 * 6)
	lasted += t.boss.fight_clock
	t.check(t.sm.current_state.name == "Remount" and absf(lasted - t.sm.states["Dismounted"].window) <= 2.0 * FRAME,
		"left alone, his knock-off lasts its %.1f s (%.2f), then he gets up" % [t.sm.states["Dismounted"].window, lasted])
	var home: bool = await t.wait_until(func(): return t.sm.current_state.name == "Idle", 60 * 8)
	t.check(home and t.boss.mounted and t.sm.kaiju.is_home(), "and climbs back on")


#RECOIL

const RECOIL_STARTS: Array[Vector2] = [Vector2(1300, 600), Vector2(1700, 250), Vector2(1000, 900), Vector2(800, 330)]


static func tier_recoil(t) -> void:
	await enter(t)
	t.hold_break_gauge(t.boss)
	var kaiju: Node2D = t.sm.kaiju
	var recoil: Node = t.sm.states["Recoil"]
	var player_box := func() -> Rect2:
		var shape: CollisionShape2D = t.player.get_node("CollisionShape2D")
		return shape.global_transform * shape.shape.get_rect()

	t.log_p("-- standing still far off: the opening comes and goes, and deals nothing")
	await home_again(t)
	await at_feet(t, Vector2(1500, 800))
	await play_turn(t, "Breath", true)
	t.check(t.sm.current_state == recoil, "the breath's last pass hands over to the recoil (%s)" % t.sm.current_state.name)
	var seen := {"open_at": -1.0, "shut_at": -1.0, "wall": [], "hurt": false, "bow": false}
	var health: int = t.boss.boss_health
	var entered_at: float = t.boss.fight_clock
	for f in 60 * 5:
		if t.sm.current_state != recoil:
			break
		seen.bow = seen.bow or kaiju.current_anim == &"bow"
		if recoil.open and seen.open_at < 0.0:
			seen.open_at = t.boss.fight_clock - entered_at
		if not recoil.open and seen.open_at >= 0.0 and seen.shut_at < 0.0:
			seen.shut_at = t.boss.fight_clock - entered_at
		if recoil.open:
			seen.wall.append(kaiju.wall_rect(0).end.x)
			seen.hurt = seen.hurt or t.boss.hurtbox.monitorable
		await t.physics_frame
	var window: float = seen.shut_at - seen.open_at
	t.log_p("  head down at %.2f s, shut at %.2f s (%.2f s open), back wall while open %s" % [seen.open_at, seen.shut_at, window, seen.wall.slice(0, 1)])
	t.check(seen.bow and absf(seen.open_at - recoil.lower_time) <= 2.0 * FRAME and absf(window - recoil.window) <= 2.0 * FRAME,
		"its head comes down %.1f s after the breath and stays down %.1f s" % [recoil.lower_time, recoil.window])
	t.check(not seen.wall.is_empty() and seen.wall.all(func(x): return is_equal_approx(x, Layout.RECOIL_WALL_X)) and seen.hurt,
		"open, its back wall stands back to x %.0f and his hurtbox is on" % Layout.RECOIL_WALL_X)
	var mouth: Vector2 = kaiju.breath_origin()
	var too_near: Array = []
	for aim in range(-80, 100, 10):
		var burn := BurnLine.new()
		burn.origin = mouth
		burn.angle = deg_to_rad(aim)
		burn.life = 0.0
		t.sm.add_floor_hazard(burn, Vector2.ZERO)
		var feet := Vector2(650, 520)
		if burn.distance_to_point(feet) <= BurnLine.HALF_WIDTH + Beam.FOOT_RADIUS:
			too_near.append(aim)
		burn.queue_free()
	t.check(too_near.is_empty(), "no line of fire, whatever its aim, reaches the floor in front of the lowered head (%s)" % [too_near])
	t.check(t.sm.current_state.name == "Idle" and kaiju.wall_rect(0) == Layout.WALLS[0] and not t.boss.hurtbox.monitorable and t.boss.mounted,
		"then the wall is home, his hurtbox off, and his turns go on")
	t.check(t.boss.boss_health == health, "a player standing still far off deals him nothing")

	t.log_p("-- walked to from the floor: three punches and the POW, the uppercut, then slid clear of the wall")
	# Its key bounce is real seconds, which a fixed-fps run outpaces.
	t.player.get_node("Finisher").min_press_interval = 0.0
	var pows := [0]
	t.player.combo.charged_hit_landed.connect(func(_target): pows[0] += 1)
	var finisher: Node = t.player.get_node("Finisher")
	for start in RECOIL_STARTS:
		# Four uppercuts and their punches would kill him.
		t.boss.boss_health = t.boss.max_health
		await home_again(t)
		await at_feet(t, Vector2(1500, 800))
		await play_turn(t, "Breath", true)
		await t.wait_until(func(): return recoil.open, 60)
		await at_feet(t, start)
		var keys := Keys.new(t)
		var box: Rect2 = t.boss.hurtbox_rect()
		var reach: Rect2 = t.player.punch_box(t.player.Facing.LEFT)
		var spot := Vector2(box.end.x - reach.get_center().x * t.player.global_scale.x, box.end.y - FEET_OFFSET + 3.0)
		var walked := 0.0
		for f in 60 * 3:
			var to: Vector2 = spot - t.player.global_position
			# The walk's 10 px steps can't land on a spot between them.
			if to.length() <= 12.0:
				break
			keys.toward(to)
			await t.physics_frame
			walked += FRAME
		keys.stop()
		await t.wait(2)
		var arrived: bool = t.player.global_position.distance_to(spot) <= 16.0
		var in_wall: bool = Layout.box_in_walls(player_box.call()) and kaiju.wall_rect(0).intersects(player_box.call())
		health = t.boss.boss_health
		pows[0] = 0
		for i in 3:
			await t.swing_any()
		var dealt: int = health - t.boss.boss_health
		# PlayerFinisher's Phase: 2 is dazed, the mash's.
		var dazed: bool = await t.wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120)
		t.log_p("  from %s: at %s in %.2f s, dealt %d, POW %d, dazed %s" % [start, t.player.global_position, walked, dealt, pows[0], dazed])
		t.check(arrived and not in_wall and walked <= recoil.window - 1.0, "from %s the player walks to him on the open floor in %.2f s" % [start, walked])
		t.check(dealt == 4 and pows[0] == 1 and dazed, "three punches and the POW land on him on its head (%d), and the POW dazes him" % dealt)
		var share: float = finisher.finisher_damage_ratio * (Finisher.SUPERCHARGE_MULTIPLIER if finisher.supercharged else 1.0)
		var due: int = maxi(1, roundi(t.boss.max_health * share))
		health = t.boss.boss_health
		await t.mash_finisher()
		await t.wait_until(func(): return t.boss.boss_health < health, 90)
		var upper: int = health - t.boss.boss_health
		var shut_at_contact: bool = not recoil.open
		await t.wait_until(func(): return finisher.phase == 0, 300)
		var down_through: bool = t.sm.current_state == recoil and recoil.beat == recoil.Beat.OPEN and recoil.slid == null
		t.log_p("  the uppercut %d of %d, the opening shut at contact %s, the head still down as the finisher ends %s" % [upper, due, shut_at_contact, down_through])
		t.check(upper == due and shut_at_contact and down_through,
			"the mash's uppercut lands for the plain finisher's %d (%d) and shuts the opening, its head down until the finisher is over" % [due, upper])
		await t.wait_until(func(): return t.sm.current_state != recoil, 60 * 4)
		await t.wait(2)
		var clear: bool = not Layout.WALLS[0].intersects(player_box.call())
		t.check(clear and recoil.slid_out and not t.player.is_action_locked and kaiju.wall_rect(0) == Layout.WALLS[0] and t.boss.mounted,
			"as its head comes up with him on it the player is slid clear of the wall coming back (%s)" % t.player.global_position)
		await t.wait_until(func(): return t.sm.finisher_stagger_timer.is_stopped(), 60 * 3)
		await t.wait(30)
		t.check(t.boss.sprite.offset.distance_to(ArtLayout.SPRITE_OFFSET) < 1.0,
			"and his recoil off the uppercut has settled back onto his seat (%s)" % t.boss.sprite.offset)

	t.log_p("-- the breath's line of fire burns on through it")
	await home_again(t)
	await at_feet(t, Vector2(1300, 600))
	var seen_hits := Log.new(t)
	await play_turn(t, "Breath", true)
	await t.wait_until(func(): return recoil.open, 60)
	var burns: Array = t.sm.live_burns()
	var burning: bool = not burns.is_empty()
	if burning:
		var burn: Node2D = burns[0]
		t.clear_iframes()
		await at_feet(t, burn.from.lerp(burn.to, 0.6))
		await t.wait(3)
	t.check(burning and seen_hits.of(seen_hits.hits, &"jordan_burn_line") >= 1, "a line of fire is still alight in the opening, and burns")

	t.log_p("-- under half health one opening, after both passes")
	await home_again(t)
	t.sm.phase_b = true
	await at_feet(t, Vector2(1300, 600))
	var breath: Node = await play_turn(t, "Breath", true)
	t.check(t.sm.current_state == recoil and breath.plans.size() == 2, "the recoil comes after the second pass (%d passes)" % breath.plans.size())

	t.log_p("-- a Break in it: thrown off, the wall home, the player clear")
	await home_again(t)
	await at_feet(t, Vector2(1500, 800))
	await play_turn(t, "Breath", true)
	await t.wait_until(func(): return recoil.open, 60)
	await at_feet(t, Vector2(640, 400))
	var gauge: Node = t.boss.break_gauge
	gauge.locked = false
	gauge.set_physics_process(true)
	gauge.value = 0.0
	gauge.add(gauge.max_value)
	await t.wait_until(func(): return t.sm.current_state.name == "Broken", 30)
	await t.wait(3)
	var stood_box: Rect2 = t.boss.hurtbox_rect()
	t.check(t.sm.current_state.name == "Broken" and not t.boss.mounted and kaiju.wall_rect(0) == Layout.WALLS[0] and stood_box.size == Vector2(120, 270),
		"a Break in it throws him off into Broken, its wall home and his hurtbox his standing one (%s)" % stood_box)
	await t.wait_until(func(): return not t.player.is_action_locked, 120)
	t.check(not Layout.box_in_walls(player_box.call()), "and the player clear of its walls (%s)" % t.player.global_position)
	t.hold_break_gauge(t.boss)

	t.log_p("-- his KO in it")
	await enter(t)
	t.hold_break_gauge(t.boss)
	kaiju = t.sm.kaiju
	recoil = t.sm.states["Recoil"]
	await at_feet(t, Vector2(1500, 800))
	await play_turn(t, "Breath", true)
	await t.wait_until(func(): return recoil.open, 60)
	t.boss.boss_health = 1
	var box_ko: Rect2 = t.boss.hurtbox_rect()
	var reach_ko: Rect2 = t.player.punch_box(t.player.Facing.LEFT)
	await t.settle_player(Vector2(box_ko.end.x - reach_ko.get_center().x * t.player.global_scale.x, box_ko.end.y - FEET_OFFSET + 3.0))
	t.player.face_point(box_ko.get_center())
	await t.swing_any()
	var died: bool = await t.wait_until(func(): return t.boss.defeated, 60)
	await t.wait(3)
	var live: Array = t.get_nodes_in_group("jordan_hazard").filter(func(h): return is_instance_valid(h) and not h.is_queued_for_deletion())
	t.check(died and t.sm.current_state.name == "Defeated" and not kaiju.walls_up() and live.is_empty() and not t.boss.mounted,
		"a punch on its head that KOs him ends it: bucked off, its walls gone, nothing of his live (%s)" % [live])
	await t.wait_until(func(): return t.sm.current_state.name == "WalkOut", 60 * 8)
	load("res://Scripts/JordanGodLayout.gd").release_prefetch()


#OCCLUSION

static func tier_occlusion(t) -> void:
	await enter(t)
	t.hold_break_gauge(t.boss)
	for feet in [Vector2(1200, 560), Vector2(950, 820), Vector2(1550, 420)]:
		await home_again(t)
		await at_feet(t, feet)
		t.sm.states["Stomp"].settle_time = 3.0
		t.sm.states["Stomp"].tail_chance = 0.0
		var seen := {"covered": false, "ghost": false, "frames": 0}
		var hide := func(state: Node) -> void:
			if state.beat != Stomp.Beat.SETTLE:
				return
			var kaiju: Node2D = t.sm.kaiju
			if seen.frames == 0:
				t.player.global_position = kaiju.feet_point() + Vector2(-70, -80) - Vector2(0, FEET_OFFSET)
			seen.frames += 1
			if seen.frames < 5:
				return
			var sprite: Sprite2D = t.player.sprite
			var behind: bool = soles(t).y < kaiju.feet_point().y and kaiju.covers(sprite.global_position)
			seen.covered = seen.covered or behind
			var ghost: Sprite2D = kaiju.ghosts[1] if kaiju.sheet_drawn else kaiju.ghosts[0]
			if behind and ghost.is_visible_in_tree() and ghost.global_position.is_equal_approx(sprite.global_position) and ghost.frame == sprite.frame and is_equal_approx(ghost.modulate.a, sprite.modulate.a * 0.8):
				seen.ghost = true
		await play_turn(t, "Stomp", true, hide)
		t.sm.states["Stomp"].settle_time = 0.5
		t.sm.states["Stomp"].tail_chance = 0.35
		t.check(seen.covered and seen.ghost, "landed at %s with the player put behind its body, the x-ray ghost is drawn over them" % feet)


#DEFEAT

# The juggle first: each KO hands the fight to his walk-out, and the next fight is loaded over it, which the game never
# does (the walk-out leads into his finale's room).
static func tier_defeat(t) -> void:
	for how in ["juggled", "punched", "riding"]:
		await enter(t)
		t.hold_break_gauge(t.boss)
		var kaiju: Node2D = t.sm.kaiju
		var anims := {}
		# His pose on the last frame before the walk-out takes over: [sheet, frame, juggle clip].
		var pose := ["", -1, &""]
		var watch := func():
			if is_instance_valid(kaiju):
				anims[kaiju.current_anim] = true
			if is_instance_valid(t.sm) and t.sm.current_state != null and t.sm.current_state.name != "WalkOut":
				pose[0] = t.boss.sprite.texture.resource_path.get_file()
				pose[1] = t.boss.sprite.frame
				pose[2] = t.sm.states["Juggled"].clip_name
		t.physics_frame.connect(watch)
		match how:
			"punched":
				t.sm.on_child_transition(t.sm.current_state, "Dismounted")
				await t.wait(5)
				t.boss.boss_health = 1
				t.place_under(t.boss.get_finisher_hurtbox())
				await t.swing_any()
			"juggled":
				var gauge: Node = t.boss.break_gauge
				gauge.locked = false
				gauge.set_physics_process(true)
				gauge.value = 0.0
				gauge.add(gauge.max_value)
				await t.wait_until(func(): return t.sm.current_state.name == "Broken", 30)
				await t.wait_until(func(): return not t.player.is_action_locked, 120)
				var finisher: Node = t.player.get_node("Finisher")
				for i in 3:
					await t.swing_any()
					if i < 2:
						await t.wait(6)
				await t.wait_until(func(): return finisher.prompt_visible, 120)
				t.boss.boss_health = 1
				# Its key bounce is real seconds, which a fixed-fps run outpaces.
				finisher.min_press_interval = 0.0
				await t.mash_finisher()
			"riding":
				t.boss.boss_health = 1
				t.boss.explosion_hits_this_cycle = 0
				t.boss.take_explosion_hit(1)
		var died: bool = await t.wait_until(func(): return t.boss.defeated, 60 * 6)
		await t.wait_until(func(): return t.sm.current_state.name in ["Defeated", "WalkOut"], 60 * 6)
		var walls_down: bool = not kaiju.walls_up()
		var live: Array = t.get_nodes_in_group("jordan_hazard").filter(func(h): return is_instance_valid(h) and not h.is_queued_for_deletion())
		var walked: bool = await t.wait_until(func(): return t.sm.current_state.name == "WalkOut", 60 * 8)
		# The walk-out starts loading his last phase on threads: joined before the next fight loads over it.
		load("res://Scripts/JordanGodLayout.gd").release_prefetch()
		var soles_at: Vector2 = t.boss.to_global(ArtLayout.FLOOR_POINT)
		t.physics_frame.disconnect(watch)
		var frame_ok: bool
		if how == "juggled":
			frame_ok = pose[2] == &"down"
		else:
			# His butt-land sheet's last frame is the defeat's, pixel for pixel.
			frame_ok = pose[0] in ["jordan_defeat.png", "jordan_butt_land.png"] and pose[1] == 5
		t.log_p("  %s: kaiju anims %s, his last pose %s, his soles %s, state %s" % [how, anims.keys(), pose, soles_at, t.sm.current_state.name])
		t.check(died and anims.has(&"shrink") and not kaiju.visible, "KO %s: it shrinks back into the toy and hops into his box" % how)
		t.check(walls_down and live.is_empty() and not t.boss.mounted, "its walls go and nothing of his is left live (%s)" % [live])
		t.check(frame_ok and (how != "riding" or soles_at.distance_to(Layout.DEFEAT_LANDING) < 1.0),
			"he lies on %s" % ("the juggle's down loop" if how == "juggled" else "the defeat's last frame"))
		t.check(walked, "and the walk-out comes")


#THE MODEL'S ANSWERS

# Two figures going off this far apart, the second inside the first parry's freeze and slow motion.
const PAIR_GAP := 0.30
# The second half's line of fire, the one the model met in the playtest (seed 1): its last pass's mouth and aim, the line
# running from (701, 626) down to the bottom rope between the player's feet and the floor in front of the lowered head.
const RECOIL_BURN_ORIGIN := Vector2(574, 546)
const RECOIL_BURN_ANGLE := 32.0
const RECOIL_BURN_FEET := Vector2(1000, 900)


# The 2026-10-07 playtest's two hits the model kept taking, played by its own Bot (kaiju_model.gd), learned: a pair of
# figures going off PAIR_GAP apart, its presses due on the fight's clock, both parried; then the breath's line of fire
# lying between it and his lowered head with the bar under a dash, and it waits for the dash's third of the bar instead
# of walking through the fire, dashes square across it unburnt and lands a punch in the opening (what the wait costs it
# of the opening is the price of the low bar).
static func tier_answers(t) -> void:
	var model: GDScript = load("res://art_source/defense_tests/jordan/kaiju_model.gd")
	await enter(t)
	t.hold_break_gauge(t.boss)
	await home_again(t)
	t.log_p("-- two figures going off %.2f s apart" % PAIR_GAP)
	await at_feet(t, model.STATION)
	var seen := Log.new(t)
	var bot = model.Bot.new(t, 1, true)
	bot.late_share = 0.0
	var figures: Array = []
	for i in 2:
		var figure: Node = FunkoThrow.FUNKO_FIGURE_SCENE.instantiate()
		figure.player = t.player
		figure.jordan = t.boss
		figure.tell_lead = FunkoFigure.TELL_LEAD
		figure.attack_id = FunkoThrow.ATTACK_ID
		t.sm.add_hazard(figure, t.player.global_position + Vector2(60.0 if i == 0 else -60.0, 0.0))
		figure.fuse = 1.2 + PAIR_GAP * i
		figures.append(figure)
	for f in 60 * 3:
		bot.step()
		await t.physics_frame
		if figures.all(func(figure) -> bool: return not is_instance_valid(figure)) and not t.player.is_invincible:
			break
	bot.keys.stop()
	t.release(KEY_SHIFT)
	t.log_p("  parried %s, hit by %s, presses %s" % [seen.parries, seen.hits, bot.press_log])
	t.check(seen.of(seen.parries, FunkoThrow.ATTACK_ID) == 2 and seen.hits.is_empty(),
		"both blasts parried, the second through the first parry's freeze and slow motion")

	t.log_p("-- the breath's line of fire between the player and his lowered head, the bar under a dash")
	await home_again(t)
	var recoil: Node = t.sm.states["Recoil"]
	await at_feet(t, Vector2(1500, 800))
	await play_turn(t, "Breath", true)
	await t.wait_until(func(): return recoil.open, 60)
	for old in t.sm.live_burns():
		old.queue_free()
	var burn := BurnLine.new()
	burn.player = t.player
	burn.boss = t.boss
	burn.origin = RECOIL_BURN_ORIGIN
	burn.angle = deg_to_rad(RECOIL_BURN_ANGLE)
	burn.life = 9.0
	t.sm.add_floor_hazard(burn, Vector2.ZERO)
	await at_feet(t, RECOIL_BURN_FEET)
	t.clear_iframes()
	t.defense.drain_stamina(t.defense.stamina - 20.0)
	seen.clear()
	var health: int = t.boss.boss_health
	bot = model.Bot.new(t, 2, true)
	# Steps it stood still short of him, its keys let go and the bar under a dash.
	var waited := 0
	for f in 60 * 4:
		if not recoil.open and not t.player.get_node("Finisher").is_active():
			break
		bot.step()
		await t.physics_frame
		if f > 3 and not bot.punishing and bot.keys.held.is_empty() and t.defense.stamina < t.defense.max_stamina * model.DASH_COST:
			waited += 1
	bot.keys.stop()
	var dealt: int = health - t.boss.boss_health
	t.log_p("  burns %d, waited for the bar %.2f s, dealt %d, the player at %s" % [seen.of(seen.hits, BurnLine.BURN_ID),
		waited * FRAME, dealt, soles(t)])
	t.check(seen.of(seen.hits, BurnLine.BURN_ID) == 0 and waited >= 12 and dealt >= 1,
		"it waits for the bar, dashes across unburnt and lands a punch on him in the opening (%d)" % dealt)


#LAZY

const LAZY_SECONDS := 60.0


static func tier_lazy(t) -> void:
	for bot in ["still", "circle", "corners", "under_bar", "walker"]:
		await enter(t, SEED + bot.length())
		t.sm.states["Idle"].rested = 0.0
		var seen_hits := Log.new(t)
		var keys := Keys.new(t)
		var rng := RandomNumberGenerator.new()
		rng.seed = SEED
		var start_health: int = t.boss.boss_health
		var goal := {"at": Vector2(1200, 560), "next": 0.0}
		var corners: Array[Vector2] = [Vector2(692, 192), Vector2(1788, 192), Vector2(1788, 945), Vector2(612, 945)]
		match bot:
			"still":
				await at_feet(t, Vector2(1200, 560))
			"under_bar":
				await at_feet(t, Vector2(960, 192))
			"corners":
				await at_feet(t, corners[0])
		var clock := 0.0
		while clock < LAZY_SECONDS and not t.boss.defeated:
			t.player.playerHealth = 1000
			match bot:
				"circle":
					var r: Vector2 = soles(t) - Vector2(1200, 560)
					keys.toward(r.rotated(PI / 2.0).normalized() - r.normalized() * (r.length() - 260.0) / 260.0)
				"corners":
					var corner: Vector2 = corners[int(clock / (LAZY_SECONDS / 4.0)) % 4]
					var to: Vector2 = corner - soles(t)
					keys.toward(to if to.length() > 12.0 else Vector2.ZERO)
				"walker":
					if clock >= goal.next or soles(t).distance_to(goal.at) < 20.0:
						goal.at = Vector2(rng.randf_range(640, 1780), rng.randf_range(200, 940))
						goal.next = clock + 1.5
					keys.toward(goal.at - soles(t))
			await t.physics_frame
			clock += FRAME
		keys.stop()
		var lost := 0
		for hit in seen_hits.hits:
			lost += hit.damage
		var per_minute := lost / clock * 60.0
		var dealt: int = start_health - t.boss.boss_health
		t.log_p("  %s: %d half-hearts in %.0f s (%.1f a minute), dealt him %d" % [bot, lost, clock, per_minute, dealt])
		t.check(per_minute >= 4.0 or dealt <= 1, "%s loses at least 4 half-hearts a minute or deals him nothing (%.1f, %d)" % [bot, per_minute, dealt])


#ART

const WAVE_ONE: Array[StringName] = [&"idle", &"charge", &"rear", &"leap", &"drop", &"stomp", &"stumble", &"kneel", &"stand",
	&"land", &"grow", &"shrink", &"toy"]
const WAVE_TWO: Array[StringName] = [&"roar", &"bow", &"hit", &"tail_windup", &"tail_spin", &"collapse", &"down"]
const RIDER_ANIMS: Array[StringName] = [&"ride_idle", &"ride_throw", &"ride_brace", &"ride_taunt", &"topple",
	&"dismount_daze", &"climb", &"box_open", &"toss", &"butt_land"]
const TailSweep := preload("res://Scripts/JordanTailSweep.gd")


static func tier_art(t) -> void:
	var missing := (WAVE_ONE + WAVE_TWO).filter(func(anim_name): return not Layout.anim(anim_name).get("sheet", "").ends_with("kaiju_%s.png" % anim_name))
	if not missing.is_empty():
		t.check(false, "the kaiju's sheets are in (imported, or art=raw): missing %s" % [missing])
		return
	var rider_missing := RIDER_ANIMS.filter(func(anim_name): return ArtLayout.anchors(anim_name).is_empty())
	t.check(rider_missing.is_empty(), "every animation of the kaiju's on its own sheet, and every one of his ride and mat sheets in (%s)" % [rider_missing])
	await enter(t)
	var kaiju: Node2D = t.sm.kaiju
	kaiju.play_anim(&"idle")
	await t.wait(1)
	var seat: Vector2 = kaiju.seat_point()
	var mouth: Vector2 = kaiju.mouth_point()
	# The contract's screen anchors are its texels' centres, a texel's corner and its middle 1.5 px apart at 3x.
	t.check(kaiju.body_sprite.visible and kaiju.body_sprite.frame == 0 and seat.distance_to(Vector2(454, 342)) <= 2.0 and mouth.distance_to(Vector2(637, 429)) <= 2.0,
		"at home on the idle's first frame the seat is on (454, 342) and the mouth on (637, 429) (%s, %s)" % [seat, mouth])
	var rect: Rect2 = kaiju.drawn_rect()
	t.check(rect.position.distance_to(Vector2(36, 182)) <= 1.0 and rect.size == Vector2(672, 696), "its frame's top-left on (36, 182) at home (%s)" % rect)
	var his_seat: Vector2 = t.boss.global_position + ArtLayout.frame_local(t.boss.anchor(&"seat"))
	t.check(str(t.boss.current_anim).begins_with("ride_") and his_seat.distance_to(seat) <= 1.0 and kaiju.rider.visible and not kaiju.rider_sheet.visible
		and kaiju.rider.global_position.distance_to(t.boss.sprite.global_position) <= 1.0,
		"and him drawn on his ride sheet with its SEAT on the seat (%s; %s, %s, rider %s on %s, stand-in %s)" % [his_seat, t.boss.current_anim,
			kaiju.rider.visible, kaiju.rider.global_position, t.boss.sprite.global_position, kaiju.rider_sheet.visible])

	kaiju.play_anim(&"bow")
	var bowed: Array = []
	var bow: Dictionary = Sheets.SHEETS[&"bow"]
	for i in bow.anchors.size():
		kaiju.anim_step = i
		kaiju.body_sprite.frame = i
		var want: Vector2 = Layout.HOME + ((bow.anchors[i].rider_seat as Vector2) - (bow.pivot as Vector2)) * Layout.SCALE
		if kaiju.seat_point().distance_to(want) > 1.0:
			bowed.append([i, kaiju.seat_point(), want])
	t.check(bowed.is_empty(), "its bow lowers his seat frame by frame (%s)" % [bowed])
	kaiju.play_anim(&"roar")
	kaiju.light_spines(8)
	t.check(kaiju.spines_sprite.visible and kaiju.spines_sprite.frame == kaiju.body_sprite.frame and str(kaiju.spines_sprite.texture.resource_path).get_file() in ["kaiju_roar_spines.png", ""],
		"the Phase B roar has every plate lit over it, frame for frame")
	kaiju.light_spines(0)
	kaiju.play_anim(&"idle")
	var sweep := TailSweep.new()
	sweep.player = null
	t.sm.add_floor_hazard(sweep, Layout.HOME)
	var arcs: Array = []
	for k in 16:
		sweep.hand = deg_to_rad(k * 22.5)
		var frame := posmod(roundi(rad_to_deg(sweep.hand) / 22.5), 16)
		if frame != k or sweep.material == null:
			arcs.append(k)
	sweep.queue_free()
	t.check(arcs.is_empty() and TailSweep.drawn_clockwise(), "its tail's arc frame k at k x 22.5 degrees round its feet, additive, turning clockwise (%s)" % [arcs])

	kaiju.play_anim(&"charge")
	await t.wait(1)
	var turned: Array = []
	var head: Dictionary = Sheets.SHEETS[&"head_aim"]
	for i in head.anchors.size():
		var a: Dictionary = head.anchors[i]
		kaiju.aim_head(a.aim)
		await t.wait(1)
		var want_mouth: Vector2 = Layout.HOME + ((Vector2(131, 74) - Vector2(98, 206)) + (a.mouth - a.neck)) * Layout.SCALE
		var level: Dictionary = head.anchors[3]
		var want_seat: Vector2 = Layout.HOME + ((Vector2(139, 53) - Vector2(98, 206)) + (a.seat_on_head - level.seat_on_head)) * Layout.SCALE
		if kaiju.head_sprite.frame != i or kaiju.mouth_point().distance_to(want_mouth) > 1.0 or kaiju.seat_point().distance_to(want_seat) > 1.0:
			turned.append([a.aim, kaiju.head_sprite.frame, kaiju.mouth_point(), want_mouth, kaiju.seat_point(), want_seat])
	t.check(kaiju.head_sprite.visible and turned.is_empty(), "on its charge stance its head turns frame by frame with its aim, the mouth and his seat riding it (%s)" % [turned])
	var lit: Array = []
	for rows in 9:
		kaiju.light_spines(rows)
		if not kaiju.spines_sprite.visible or kaiju.spines_sprite.frame != rows:
			lit.append(rows)
	t.check(lit.is_empty() and not kaiju.plate_glow.visible, "and its plates light from its own sheet, row by row (%s)" % [lit])
	kaiju.set_charge(1.0, true)
	t.check(kaiju.head_sprite.texture.resource_path.ends_with("kaiju_head_fire.png") or Layout.test_textures.get(Layout.SHEET_DIR + "kaiju_head_fire.png") == kaiju.head_sprite.texture,
		"its jaws open as it fires")
	kaiju.set_charge(0.0)
	kaiju.light_spines(0)
	kaiju.aim_head(0.0)

	await home_again(t)
	await at_feet(t, Vector2(1300, 600))
	var landed := {"foot": Vector2.INF, "mark": Vector2.INF, "frame": -1}
	var watch_foot := func(state: Node) -> void:
		if landed.frame < 0 and not state.impact_times.is_empty():
			landed.foot = kaiju.art.to_global(kaiju._anchor(&"foot_impact", Vector2.ZERO))
			landed.mark = state.target
			landed.frame = kaiju.body_sprite.frame
	await play_turn(t, "Stomp", true, watch_foot)
	t.check(kaiju.current_anim != &"" and landed.foot.distance_to(landed.mark) <= 1.0,
		"a stomp lands its stomping foot on its mark (%s on %s)" % [landed.foot, landed.mark])
