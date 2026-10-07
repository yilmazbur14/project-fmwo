extends RefCounted

# greyson_takeover_mark (tuning 2026-10-04, the user's default (f)): the takeover walks the player onto their mark
# under his HOME (GreysonTakeover.PLAYER_MARK), so his first throw never opens on them point blank. The playtest found
# it left them where they had finished Computah, beside his hand, and his first plate touched them as it left it.
# In Computah's real fight with greyson_follows on, the player beside his HOME as Computah goes down. tier=
#   watched  (the default) every line read: they walk onto the mark on the walk's rows as he walks in, done before he
#            is home, and stand on it facing him; clear of him through the tear and the hurl, where his z is over
#            theirs; the end state holds them on it, free; and his first plate, thrown at them standing there, has a
#            real first leg and touches them no sooner than min_flight after it leaves his hand.
#   held     a hold on the shout (before the walk), mid-walk, and mid-tear: each lands them on the mark, free, and his
#            first plate the same.
#   restart  the GREYSON row and a restart in his half (GameProgress.start_at_greyson): the takeover from Computah
#            already down, the player where the scene put them; read through, it lands them on the mark, and his first
#            plate the same.

const Takeover := preload("res://art_source/defense_tests/greyson/takeover.gd")
const FIGHT := "res://Scenes/Bosses/ComputahBossFightScene.tscn"
const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const COMPUTAH_BODY := "Arena/ComputahScene/ComputahCharacterBody"
const FRAME_TIME := 1.0 / 60.0
# Where a punish on Computah leaves the player: beside his HOME, where a plate off Greyson's hand touches them as it
# leaves it.
const BESIDE_HOME := Vector2(1075, 585)
const HOLD_POINTS := ["shout", "walk", "tear"]
const HOLD_FRAMES := 90
# A first leg this long or longer is a flight to read, not a plate that leaves his hand on them.
const REAL_FLIGHT := 250.0
const ON_MARK := 0.5


static func run(t) -> void:
	match "watched" if t.tier == "normal" else t.tier:
		"watched":
			await watched(t)
		"held":
			for point in HOLD_POINTS:
				await held(t, point)
		"restart":
			await restart(t)
		_:
			t.check(false, "greyson_takeover_mark has no tier %s" % t.tier)


static func watched(t) -> void:
	t.log_p("-- watched through")
	var parts: Array = await into_takeover(t, BESIDE_HOME)
	if parts.is_empty():
		return
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var mark: Vector2 = takeover.PLAYER_MARK
	var start: Vector2 = t.player.global_position
	var seen := {"walk_anims": {}, "moved_at": -1.0, "on_mark_at": -1.0, "home_at": -1.0, "off_mark": 0.0,
		"facing_on_mark": -1, "tear_checked": 0, "overlaps": [], "closest": INF}
	var watch := func() -> void:
		if takeover.finished:
			return
		var player: Node2D = t.player
		var at: Vector2 = player.global_position
		var anim: StringName = player.get_node("AnimationPlayer").current_animation
		if seen.moved_at < 0.0 and at.distance_to(start) > 1.0:
			seen.moved_at = body.fight_clock
		if seen.moved_at >= 0.0 and seen.on_mark_at < 0.0:
			seen.walk_anims[anim] = true
		if seen.on_mark_at < 0.0 and at.distance_to(mark) <= ON_MARK:
			seen.on_mark_at = body.fight_clock
			seen.facing_on_mark = -2
		if seen.on_mark_at >= 0.0:
			seen.off_mark = maxf(seen.off_mark, at.distance_to(mark))
		if seen.home_at < 0.0 and body.global_position == body.state_machine.HOME and takeover.beat_times.has(&"greyson_enters"):
			seen.home_at = body.fight_clock
		if seen.facing_on_mark == -2 and takeover.beat_times.has(&"greyson_enters"):
			seen.facing_on_mark = player.facing
		if body.sprite.z_index > 0:
			seen.tear_checked += 1
			var his := drawn(body.sprite)
			var theirs := drawn(player.sprite)
			seen.closest = minf(seen.closest, gap(his, theirs))
			if his.intersects(theirs):
				seen.overlaps.append([body.current_anim, his, theirs])
	t.physics_frame.connect(watch)
	await Takeover.read_until(t, func() -> bool: return takeover.finished, 60 * 70)
	t.physics_frame.disconnect(watch)
	t.log_p("start %s, walk from %.2f s to %.2f s, him home at %.2f s, anims %s, off the mark by %.2f px after, facing %d; tear and hurl frames %d, the closest his frame came to theirs %.1f px"
		% [start, seen.moved_at, seen.on_mark_at, seen.home_at, seen.walk_anims.keys(), seen.off_mark, seen.facing_on_mark, seen.tear_checked, seen.closest])
	t.check(start.distance_to(mark) > 200.0, "the player starts beside his HOME, well off the mark (%.0f px off)" % start.distance_to(mark))
	t.check(seen.moved_at >= 0.0 and seen.on_mark_at > seen.moved_at and seen.walk_anims.has(&"walking"),
		"they walk onto the mark on the walk's rows (%s)" % [seen.walk_anims.keys()])
	t.check(seen.on_mark_at >= 0.0 and seen.home_at >= 0.0 and seen.on_mark_at <= seen.home_at,
		"as he walks in: on it by the time he is home (%.2f s, him %.2f s)" % [seen.on_mark_at, seen.home_at])
	t.check(seen.off_mark <= ON_MARK, "and they stay on it through the rest of the takeover (%.2f px)" % seen.off_mark)
	t.check(seen.facing_on_mark == t.player.Facing.UP, "facing up at him on it (facing %d)" % seen.facing_on_mark)
	t.check(seen.tear_checked > 0 and seen.overlaps.is_empty(),
		"clear of him through the tear and the hurl, where his z is over theirs (%d frames, overlaps %s)" % [seen.tear_checked, seen.overlaps.slice(0, 3)])
	await check_end(t, body, takeover, "watched")


static func held(t, point: String) -> void:
	t.log_p("-- held on %s" % point)
	var parts: Array = await into_takeover(t, BESIDE_HOME)
	if parts.is_empty():
		return
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var mark: Vector2 = takeover.PLAYER_MARK
	var start: Vector2 = t.player.global_position
	var reached := func() -> bool: return at_point(t, point, body, start, mark)
	await Takeover.read_until(t, func() -> bool: return takeover.finished or reached.call(), 60 * 40)
	t.check(reached.call() and not takeover.finished, "reached %s (player at %s, him on %s)" % [point, t.player.global_position, body.current_anim])
	t.press(KEY_ESCAPE)
	var skipped: bool = await t.wait_until(func(): return takeover.finished, HOLD_FRAMES)
	t.release(KEY_ESCAPE)
	t.check(skipped, "the hold skips it")
	await check_end(t, body, takeover, "held on %s" % point)


# The GREYSON row's way in, which the pause screen's restart in his half takes too: no fight of Computah's, him already
# down, and the takeover from its first line, the player where the scene put them.
static func restart(t) -> void:
	t.log_p("-- the GREYSON row / a restart in his half")
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	t.root.get_node("GameProgress").start_at_greyson = true
	await t.open_scene(FIGHT)
	await t.wait(3)
	t.player = t.current_scene.get_node("Arena/MainPlayer/CharacterBody2D")
	t.defense = t.player.get_node("Defense")
	var body: Node = null
	for i in 120:
		body = t.current_scene.get_node_or_null(BODY)
		if body != null:
			break
		await t.wait(1)
	t.check(body != null, "his half opens on Greyson's takeover")
	if body == null:
		return
	var takeover: Node = body.state_machine.states["Takeover"]
	var start: Vector2 = t.player.global_position
	var cut_up: bool = await t.wait_until(func(): return takeover.cut != null, 120)
	t.check(cut_up, "the KO beat, then the cut")
	await Takeover.read_until(t, func() -> bool: return takeover.finished, 60 * 70)
	t.log_p("the player started at %s, %.1f px off the mark" % [start, start.distance_to(takeover.PLAYER_MARK)])
	await check_end(t, body, takeover, "restart")


# Computah's fight on and Computah beaten with the player at `at`: [Computah, Greyson, the takeover] once its cut is up.
static func into_takeover(t, at: Vector2) -> Array:
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	await t.load_fight("computah")
	var computah: Node = t.current_scene.get_node(COMPUTAH_BODY)
	computah.greyson_follows = true
	computah.greyson_scene = load(computah.GREYSON_SCENE)
	await t.wait(10)
	t.player.global_position = at
	t.player.velocity = Vector2.ZERO
	await t.wait(2)
	computah._apply_damage(computah.boss_health)
	await t.wait(3)
	var body: Node = t.current_scene.get_node_or_null(BODY)
	var handed: bool = body != null and computah.defeated
	t.check(handed, "Computah beaten with the player at %s: Greyson in" % at)
	if not handed:
		return []
	var takeover: Node = body.state_machine.states["Takeover"]
	var cut_up: bool = await t.wait_until(func(): return takeover.cut != null, 120)
	t.check(cut_up, "the KO beat, then the cut")
	if not cut_up:
		return []
	return [computah, body, takeover]


static func at_point(t, point: String, body: Node, start: Vector2, mark: Vector2) -> bool:
	var at: Vector2 = t.player.global_position
	match point:
		"shout":
			var balloon: Node = t.live_balloon()
			return balloon != null and balloon.dialogue_line != null and balloon.dialogue_line.text == "COMPUTAH NOOO" \
				and at.distance_to(start) <= 1.0
		"walk":
			return at.distance_to(start) > 40.0 and at.distance_to(mark) > 40.0
		"tear":
			return body.current_anim == &"tear_strain"
	return false


# The takeover over, by whichever way: the player on the mark, free, and his first plate thrown at them standing there
# flies a real first leg and touches them no sooner than min_flight after it leaves his hand.
static func check_end(t, body: Node, takeover: Node, label: String) -> void:
	var sm: Node = body.state_machine
	var mark: Vector2 = takeover.PLAYER_MARK
	await Takeover.settle(t, body)
	var at: Vector2 = t.player.global_position
	t.check(at.distance_to(mark) <= ON_MARK and not t.player.is_talking and not t.player.is_action_locked,
		"%s: the player on the mark %s, free (at %s, talking %s, locked %s)" % [label, mark, at, t.player.is_talking, t.player.is_action_locked])
	var throw: Node = sm.states["Throw"]
	var touch := {}
	var on_hit := func(hit) -> void:
		if hit.attack_id != &"greyson_plate" or touch.has("after") or throw.plates.is_empty():
			return
		if is_instance_valid(hit.source) and hit.source == throw.plates[0]:
			touch["after"] = body.fight_clock - throw.release_clocks[0]
	t.defense.hit_taken.connect(on_hit)
	t.player.playerHealth = 1000
	var thrown: bool = await t.wait_until(func(): return throw.thrown >= 1, 60 * 3)
	await t.wait_until(func(): return touch.has("after"), 60 * 2)
	t.defense.hit_taken.disconnect(on_hit)
	if not thrown:
		t.check(false, "%s: his first throw comes (on %s)" % [label, sm.current_state.name])
		return
	var leg: float = throw.first_legs[0]
	var after: float = touch.get("after", -1.0)
	t.log_p("%s: plate 1 from %s at %s, first leg %.1f px, point blank %s, touched them %.3f s after it left his hand"
		% [label, throw.release_points[0], throw.aimed_at[0], leg, throw.point_blank[0], after])
	t.check(not throw.point_blank[0] and leg >= REAL_FLIGHT, "%s: his first plate flies a real first leg (%.0f px, at least %.0f)" % [label, leg, REAL_FLIGHT])
	t.check(after >= throw.min_flight - FRAME_TIME - 0.001,
		"%s: and touches them no sooner than %.2f s after it leaves his hand (%.3f s)" % [label, throw.min_flight, after])


# A sprite's frame as drawn, mirrored or not: the box its flipped twin covers too, so a flip can't hide an overlap.
static func drawn(sprite: Sprite2D) -> Rect2:
	var box: Rect2 = sprite.get_global_transform() * sprite.get_rect()
	var pivot: float = sprite.global_position.x
	var twin := Rect2(2.0 * pivot - box.end.x, box.position.y, box.size.x, box.size.y)
	return box.merge(twin)


static func gap(a: Rect2, b: Rect2) -> float:
	var dx: float = maxf(maxf(a.position.x - b.end.x, b.position.x - a.end.x), 0.0)
	var dy: float = maxf(maxf(a.position.y - b.end.y, b.position.y - a.end.y), 0.0)
	return Vector2(dx, dy).length()
