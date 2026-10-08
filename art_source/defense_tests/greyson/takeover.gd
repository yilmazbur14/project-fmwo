extends RefCounted

# greyson_takeover (coder A): Greyson's takeover (GreysonTakeover) in Computah's real fight with greyson_follows
# on - Computah beaten, and Greyson storming in, tearing his cannon arm off, throwing him out of the ring and taking
# the fight over.
#   watched  every line read the way a player reads it, the upset one typed out to its end: the user's four lines
#            verbatim, the shout on the first and no blips under it; the upset line's three gestures and the smug
#            two; his node on Computah's floor point plus (156,-1) for the tear; the torn arm at its handoff, then its
#            grip on his fist; Computah hauled, torn and armless; the hurl (below); the roar's FX; every beat, the
#            roar's 1.8 s; the end state; and his first cycle.
#   hurl     from the other tear side, Computah by the right rope: Greyson on his left, and Computah thrown left.
#   held     a hold mid-walk, mid-line (the upset one, typing), mid-tear, mid-step, mid-grab, mid-heave, mid-flight,
#            on the crash and mid-roar each lands on that end state.
# The hurl, on its own sheets once they are imported (the stand-ins before): a step that puts his grab fist over
# Computah's collar, his feet on their line; the grab, the heave, the release and the recovery on their rows;
# Computah hidden from the heave, and in his place the thrown copy: its grip on his fist and behind him through the
# heave and the release, then in front, its cells' middles riding one arc over his head and over the far rope - the
# rope on the side away from where Computah lay - past the screen's edge, the spin cells in turn; the crash as he
# leaves the screen, and the crowd's cheer; about 1.5 s.
# The end state (PLAN section 6): Greyson at HOME, whole, on his own z, wearing the cannon, idle, the only boss,
# targetable with his hurtbox off; his bar full, his gauge and meter empty, his theme started once; the gates shut;
# the player free on their mark under HOME (greyson_takeover_mark has the walk there); no balloon, nothing of the
# takeover's own left and nothing in the hazard group; Computah gone from
# the ring - hidden, out of the fight and untargetable, his bar gone.

const ComputahLayout := preload("res://Scripts/ComputahArtLayout.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")
const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const COMPUTAH_BODY := "Arena/ComputahScene/ComputahCharacterBody"
const LINES := [
	"COMPUTAH NOOO",
	"That was my gym partner. I hit my first 225 on bench with this little guy. That was a long time ago. Now you've really messed up.",
	"What Computah didn't know was that this cannon is fueled by the crowd's energy... but I know how to get them going.",
	"Pal, you won't like what comes next.",
]
const HOLDS := ["walk", "line", "tear", "step", "grab", "heave", "flight", "crash", "roar"]
# Where Computah goes down for the other tear side: close enough to the right rope that Greyson tears from his left.
const BY_THE_RIGHT_ROPE := Vector2(1650, 600)
# Well past the 0.4 s hold.
const HOLD_FRAMES := 90
# A line is tapped every this many frames it is up, never on the frame it comes up: a tap that lands before its
# typing starts would move straight on past it.
const TAP_EVERY := 8


static func run(t) -> void:
	t.log_p("the hurl on its own sheets: %s" % Layout.uses_final_hurl())
	await watched(t)
	await hurl_right(t)
	for point in HOLDS:
		# The stand-ins take no step.
		if point == "step" and not Layout.uses_final_hurl():
			continue
		await held(t, point)


static func watched(t) -> void:
	t.log_p("-- watched through")
	var parts: Array = await into_takeover(t)
	if parts.is_empty():
		return
	var computah: Node = parts[0]
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var torn_frame: int = ComputahLayout.ARM_PROP.frames[&"torn"]
	var lift_frame: int = ComputahLayout.ARM_PROP.frames[&"lift"]
	var lines: Array[String] = []
	var anims_by_line := {}
	var shout_heard := false
	var blips_on_first := false
	var tear_offset := Vector2.INF
	var torn_offset := Vector2.INF
	var lift_gap := Vector2.INF
	var computah_anims := {}
	var roar_fx_seen := false
	var screen_fx_seen := false
	var hurl := new_hurl_watch()
	var last_line: Object = null
	var line_age := 0
	for i in 60 * 70:
		if takeover.finished:
			break
		var balloon: Node = t.live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			lines.append(balloon.dialogue_line.text)
			line_age = 0
		var index := lines.size() - 1
		if index >= 0:
			if not anims_by_line.has(index):
				anims_by_line[index] = {}
			anims_by_line[index][body.current_anim] = true
		if index == 0 and balloon != null:
			shout_heard = shout_heard or playing(body.sfx_players[&"shout"])
			blips_on_first = blips_on_first or playing(balloon.blip_players)
		if tear_offset == Vector2.INF and body.current_anim == &"tear_grip":
			tear_offset = body.global_position - computah.global_position
		var prop = takeover.prop
		if is_instance_valid(prop):
			if torn_offset == Vector2.INF and prop.frame == torn_frame:
				torn_offset = prop.global_position - computah.global_position
			if lift_gap == Vector2.INF and prop.frame == lift_frame:
				lift_gap = prop.global_position - body.hand_point()
		if takeover.hurl_beat == &"":
			computah_anims[computah.current_anim] = true
		watch_hurl(t, hurl, body, computah, takeover)
		roar_fx_seen = roar_fx_seen or is_instance_valid(takeover.roar_fx)
		for node in takeover.fx:
			screen_fx_seen = screen_fx_seen or (is_instance_valid(node) and not node.centered)
		# The upset line types out to its own end, and the pose its end leaves him in is seen before a tap moves on.
		var upset_up: bool = index == 1 and balloon != null \
			and (balloon.dialogue_label.is_typing or not anims_by_line[1].has(&"talk_fury_shut"))
		if balloon != null and not upset_up and line_age % TAP_EVERY == TAP_EVERY - 1:
			t.tap(KEY_ENTER)
		line_age += 1
		await t.physics_frame
	t.log_p("lines %d, beats %s" % [lines.size(), takeover.beat_times])
	t.check(lines == LINES, "the user's four lines, verbatim, tags stripped")
	t.check(shout_heard and not blips_on_first, "the shout on the first line (%s), and no blips under it (%s)" % [shout_heard, blips_on_first])
	var upset: Dictionary = anims_by_line.get(1, {})
	t.check(upset.has(&"talk_grief") and upset.has(&"talk_fond") and upset.has(&"talk_fury") and upset.has(&"talk_fury_shut"),
		"the upset line's three beats as it types, shut on fury at its end (%s)" % [upset.keys()])
	t.check(anims_by_line.get(2, {}).has(&"talk_cannon_show") and anims_by_line.get(3, {}).has(&"talk_cannon_stance"),
		"the smug show, then the smug stance (%s / %s)" % [anims_by_line.get(2, {}).keys(), anims_by_line.get(3, {}).keys()])
	t.check(tear_offset.is_equal_approx(Vector2(156, -1)), "his node on Computah's floor point plus (156,-1) for the tear (%s)" % tear_offset)
	t.check(torn_offset.is_equal_approx(Vector2(44, -73)), "the torn arm at its handoff, (43.8,-73.2) from Computah's floor point (%s)" % torn_offset)
	t.check(absf(lift_gap.x) <= 0.5 and absf(lift_gap.y - 9.0) <= 0.5, "held up, its grip on his fist to the whole pixel (%s from the fist)" % lift_gap)
	t.check(computah_anims.has(&"wrench_haul") and computah_anims.has(&"wrench_tear") and computah_anims.has(&"armless"),
		"Computah hauled, torn and armless (%s)" % [computah_anims.keys()])
	check_hurl(t, hurl, takeover, 1.0)
	t.check(roar_fx_seen and screen_fx_seen, "the roar's FX on his mouth and over the screen")
	t.check(takeover.beat_times.size() == 4 and absf(takeover.beat_times.get(&"roar", 0.0) - 1.8) < 0.05,
		"every beat, the roar's 1.8 s (%s)" % [takeover.beat_times.keys()])
	await settle(t, body)
	var diffs := end_state_diffs(t, computah, body)
	t.check(diffs.is_empty(), "the end state (%s)" % ", ".join(diffs))
	var sm: Node = body.state_machine
	var cycling: bool = await t.wait_until(func(): return String(sm.current_state.name) == "Throw", 60 * 3)
	t.check(cycling, "and his first cycle starts (%s)" % sm.current_state.name)


# The other tear side: Computah down by the right rope, Greyson on his left, and the throw to the left, over his head
# and the whole ring. Held to skip once the crash has played.
static func hurl_right(t) -> void:
	t.log_p("-- the hurl from the other side")
	var parts: Array = await into_takeover(t, BY_THE_RIGHT_ROPE)
	if parts.is_empty():
		return
	var computah: Node = parts[0]
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var hurl := new_hurl_watch()
	var line_age := 0
	var last_line: Object = null
	for i in 60 * 40:
		if takeover.finished or takeover.hurl_beat == &"done":
			break
		var balloon: Node = t.live_balloon()
		if balloon != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			line_age = 0
		watch_hurl(t, hurl, body, computah, takeover)
		if balloon != null and line_age % TAP_EVERY == TAP_EVERY - 1:
			t.tap(KEY_ENTER)
		line_age += 1
		await t.physics_frame
	t.check(takeover.side == -1.0, "by the right rope, he tears from Computah's left (side %d)" % takeover.side)
	check_hurl(t, hurl, takeover, -1.0)
	t.press(KEY_ESCAPE)
	var skipped: bool = await t.wait_until(func(): return takeover.finished, HOLD_FRAMES)
	t.release(KEY_ESCAPE)
	await settle(t, body)
	var diffs := end_state_diffs(t, computah, body)
	t.check(skipped and diffs.is_empty(), "held after the crash: the end state (%s)" % ", ".join(diffs))


static func held(t, point: String) -> void:
	t.log_p("-- held mid-%s" % point)
	var parts: Array = await into_takeover(t)
	if parts.is_empty():
		return
	var computah: Node = parts[0]
	var body: Node = parts[1]
	var takeover: Node = parts[2]
	var reached := func() -> bool: return at_point(t, point, body, takeover)
	await read_until(t, func() -> bool: return takeover.finished or reached.call(), 60 * 40)
	t.check(reached.call() and not takeover.finished, "reached mid-%s (on %s)" % [point, body.current_anim])
	t.press(KEY_ESCAPE)
	var skipped: bool = await t.wait_until(func(): return takeover.finished, HOLD_FRAMES)
	t.release(KEY_ESCAPE)
	t.check(skipped, "the hold skips it")
	await settle(t, body)
	var diffs := end_state_diffs(t, computah, body)
	t.check(diffs.is_empty(), "the end state (%s)" % ", ".join(diffs))


# Computah's fight on and Computah beaten, where `at` puts him if it is given: [Computah, Greyson, the takeover]
# once its cut is up, or nothing.
static func into_takeover(t, at := Vector2.INF) -> Array:
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	await t.load_fight("computah")
	var computah: Node = t.current_scene.get_node(COMPUTAH_BODY)
	computah.greyson_follows = true
	computah.greyson_scene = load(computah.GREYSON_SCENE)
	await t.wait(10)
	if at != Vector2.INF:
		computah.global_position = at
	computah._apply_damage(computah.boss_health)
	await t.wait(3)
	var body: Node = t.current_scene.get_node_or_null(BODY)
	var handed: bool = body != null and computah.defeated and not t.root.has_node("FightOutro")
	t.check(handed, "Computah beaten: Greyson in, and no outro")
	if not handed:
		return []
	var takeover: Node = body.state_machine.states["Takeover"]
	var cut_up: bool = await t.wait_until(func(): return takeover.cut != null, 120)
	t.check(cut_up, "the KO beat, then the cut")
	if not cut_up:
		return []
	return [computah, body, takeover]


# Whether the takeover is at `point`: the walk in, the upset line typing, the tear's strain, each beat of the hurl,
# the roar.
static func at_point(t, point: String, body: Node, takeover: Node) -> bool:
	match point:
		"walk":
			return body.current_anim == &"walk" and body.global_position.y < body.state_machine.HOME.y - 100.0
		"line":
			var balloon: Node = t.live_balloon()
			return balloon != null and balloon.dialogue_line != null and balloon.dialogue_line.text.begins_with("That was") \
				and balloon.dialogue_label.is_typing
		"tear":
			return body.current_anim == &"tear_strain"
		"step", "grab", "heave", "crash":
			return takeover.hurl_beat == StringName(point)
		"flight":
			# Past the release, in front of him and on its way.
			return takeover.hurl_beat == &"flight" and is_instance_valid(takeover.hurled) \
				and takeover.hurled.z_index == takeover.HURL_Z
		"roar":
			return body.current_anim == &"roar"
	return false


# Reads whatever lines come up, the way a player does, until `done` says so.
static func read_until(t, done: Callable, max_frames: int) -> void:
	var last_line: Object = null
	var line_age := 0
	for i in max_frames:
		if done.call():
			return
		var balloon: Node = t.live_balloon()
		if balloon != null and balloon.dialogue_line != null and balloon.dialogue_line != last_line:
			last_line = balloon.dialogue_line
			line_age = 0
		if balloon != null and line_age % TAP_EVERY == TAP_EVERY - 1:
			t.tap(KEY_ENTER)
		line_age += 1
		await t.physics_frame


#THE HURL, WATCHED

static func new_hurl_watch() -> Dictionary:
	return {"anims": {}, "final": Layout.uses_final_hurl(), "hidden_from_heave": true, "heaved": false, "grab_gap": Vector2.INF,
		"grip_gaps": [], "behind": true, "released": false, "cells": [], "off_arc": 0.0, "turns_square": true, "turned": false,
		"xs": [], "last_x": NAN, "crash_heard": false, "cheered": false}


# One step of the hurl: Greyson's rows through it, his fist on Computah's collar on the grab, Computah hidden from the
# heave, the copy's grip on the fist and its place behind him until the release is over, each cell's middle on the
# flight's arc, and the crash and the cheer.
static func watch_hurl(t, hurl: Dictionary, body: Node, computah: Node, takeover: Node) -> void:
	var beat: StringName = takeover.hurl_beat
	if beat in [&"step", &"grab", &"heave", &"flight"]:
		if not hurl.anims.has(beat):
			hurl.anims[beat] = {}
		hurl.anims[beat][body.current_anim] = true
	if hurl.final and beat == &"grab" and hurl.grab_gap == Vector2.INF:
		hurl.grab_gap = body.hand_point() - computah.frame_point(ComputahLayout.C_ARMLESS_COLLAR)
	if beat in [&"heave", &"flight", &"crash", &"done"]:
		hurl.heaved = true
		hurl.hidden_from_heave = hurl.hidden_from_heave and not computah.visible
	var copy = takeover.hurled
	if not is_instance_valid(copy):
		if beat == &"crash":
			hurl.crash_heard = hurl.crash_heard or playing(body.sfx_players[&"hurl_crash"])
			for member in t.get_nodes_in_group("arena_crowd"):
				hurl.cheered = hurl.cheered or member._cheer_time_left > 0.0
		return
	var tumble: Dictionary = ComputahLayout.ARMLESS_TUMBLE
	var releasing: bool = beat == &"flight" and body.current_anim == Layout.hurl_anim(&"hurl_release")
	var held_cell: bool = hurl.final and copy.frame == tumble.held
	if beat == &"heave" or (releasing and held_cell):
		var grip: Vector2 = copy.global_position + (cell_local(tumble.grip, copy.flip_h) if hurl.final else Vector2.ZERO)
		hurl.grip_gaps.append((grip - body.hand_point()).length())
	if beat == &"heave" or releasing:
		hurl.behind = hurl.behind and copy.z_index < body.sprite.z_index
	if beat == &"flight" and not releasing:
		hurl.released = true
	if beat != &"flight" or held_cell:
		return
	var middle: Vector2 = copy.global_position + (cell_local(tumble.middles[copy.frame], copy.flip_h) if hurl.final else Vector2.ZERO)
	hurl.xs.append(middle.x)
	hurl.last_x = middle.x
	hurl.cells.append(copy.frame)
	var from: Vector2 = takeover.hurl_arc[0]
	var to: Vector2 = takeover.hurl_arc[1]
	var along: float = (middle.x - from.x) / (to.x - from.x)
	var on_arc: float = lerpf(from.y, to.y, along) - 4.0 * takeover.HURL_ARC * along * (1.0 - along)
	hurl.off_arc = maxf(hurl.off_arc, absf(middle.y - on_arc))
	var quarters: float = copy.rotation / (PI / 2.0)
	hurl.turns_square = hurl.turns_square and absf(quarters - roundf(quarters)) < 0.001
	hurl.turned = hurl.turned or absf(copy.rotation) > 0.0


static func check_hurl(t, hurl: Dictionary, takeover: Node, toward: float) -> void:
	var names: Array = [&"hurl_grab", &"hurl_heave", &"hurl_release", &"hurl_recover"]
	var want: Array = names.map(func(a): return Layout.hurl_anim(a))
	var flown: Dictionary = hurl.anims.get(&"flight", {})
	var got: Array = [hurl.anims.get(&"grab", {}).keys(), hurl.anims.get(&"heave", {}).keys(), flown.keys()]
	var rows: bool = got[0] == [want[0]] and got[1] == [want[1]] and flown.has(want[2]) and flown.has(want[3])
	if hurl.final:
		rows = rows and hurl.anims.get(&"step", {}).has(&"walk_cannon")
	t.check(rows, "%sthe grab, the heave, the release and the recovery on their rows (%s)" % ["the step, then " if hurl.final else "", [got]])
	t.check(hurl.heaved and hurl.hidden_from_heave, "Computah hidden from the heave on, the thrown copy in his place")
	if hurl.final:
		# The feet share a line, so the fist closes on the collar from where the anchors put it: two texels over it,
		# and the tear's pixel.
		t.check(absf(hurl.grab_gap.x) <= 1.5 and hurl.grab_gap.y <= 0.0 and hurl.grab_gap.y >= -8.0,
			"the step puts the grab fist over his collar, the feet on their line (%s px off)" % hurl.grab_gap)
		var gaps: Array = hurl.grip_gaps
		t.check(not gaps.is_empty() and gaps.max() <= 1.5, "the tumble's grip on his fist through the heave and on the release's first tick (%s px)" % [gaps.max() if not gaps.is_empty() else INF])
		var cells: Array = hurl.cells
		var spin: Array = ComputahLayout.ARMLESS_TUMBLE.spin
		var in_turn := not cells.is_empty()
		for k in cells.size():
			in_turn = in_turn and spin.has(cells[k])
		t.check(in_turn and cells.has(spin[0]) and cells.has(spin[-1]), "the spin cells in the flight, all four (%s)" % [cells])
		t.check(hurl.off_arc <= 2.0, "each cell's middle on the one arc, so the spin stays steady (at most %.1f px off)" % hurl.off_arc)
	else:
		t.check(hurl.turned and hurl.turns_square, "the stand-in tumbling in quarter turns")
	t.check(hurl.behind and hurl.released, "behind him through the heave and the release, then in front")
	var rope: float = takeover.state_machine.ROPES.position.x if toward < 0.0 else takeover.state_machine.ROPES.end.x
	var width: float = takeover.get_viewport().get_visible_rect().size.x
	var xs: Array = hurl.xs
	var one_way := true
	for k in range(1, xs.size()):
		one_way = one_way and (xs[k] - xs[k - 1]) * toward >= -0.5
	var past_rope: bool = not xs.is_empty() and (xs.min() < rope if toward < 0.0 else xs.max() > rope)
	var half: float = ComputahLayout.ARMLESS_TUMBLE.frame_size.x / 2.0 * ComputahLayout.SCALE
	var gone: bool = hurl.last_x < half * 0.5 if toward < 0.0 else hurl.last_x > width - half * 0.5
	t.check(takeover.hurl_toward == toward and one_way and past_rope and gone,
		"thrown %s over his head: over the rope at x %.0f and off the screen as the flight ends (last seen at x %.0f)" % ["left" if toward < 0.0 else "right", rope, hurl.last_x])
	t.check(hurl.crash_heard and hurl.cheered, "the crash as he leaves the screen (%s), and the crowd's cheer (%s)" % [hurl.crash_heard, hurl.cheered])
	var longest: float = 1.75 if hurl.final else 1.6
	t.check(takeover.hurl_time >= 1.3 and takeover.hurl_time <= longest, "about 1.5 s from the %s to the crash's end (%.2f s)" % ["step" if hurl.final else "grab", takeover.hurl_time])


# A texel on a tumble cell from the cell's middle, in px, mirrored with the sprite, as the takeover places it.
static func cell_local(point: Vector2, flipped: bool) -> Vector2:
	var size: Vector2 = ComputahLayout.ARMLESS_TUMBLE.frame_size
	if flipped:
		point.x = size.x - 1.0 - point.x
	return (point - size / 2.0) * ComputahLayout.SCALE


# Long enough after the takeover's end for its leftovers to go, and short of his first breath's end (first_beat), when
# he starts throwing.
static func settle(t, body: Node) -> void:
	await t.wait(clampi(floori(body.state_machine.first_beat * 60.0) - 4, 1, 30))


# Everything the end state isn't, in words: empty when it is exactly the end state.
static func end_state_diffs(t, computah: Node, body: Node) -> Array[String]:
	var sm: Node = body.state_machine
	var diffs: Array[String] = []
	if body.global_position != sm.HOME:
		diffs.append("at %s" % body.global_position)
	if not body.sprite.visible or body.sprite.z_index != 0 or not body.has_cannon or body.current_anim != &"idle":
		diffs.append("visible %s, z %d, cannon %s, on %s" % [body.sprite.visible, body.sprite.z_index, body.has_cannon, body.current_anim])
	var bosses: Array = t.get_nodes_in_group("fight_boss")
	if bosses.size() != 1 or bosses[0] != body:
		diffs.append("the boss group is %s" % [bosses])
	if not body.hurtbox.is_in_group("boss_target") or body.hurtbox.monitoring:
		diffs.append("targetable %s, hurtbox on %s" % [body.hurtbox.is_in_group("boss_target"), body.hurtbox.monitoring])
	if body.health_bar == null or not is_equal_approx(body.health_bar.rows[0].value, body.max_health):
		diffs.append("his bar not full")
	var gauge: float = body.break_gauge.value if body.break_gauge != null else 0.0
	if gauge != 0.0 or body.hype != 0.0:
		diffs.append("gauge %.1f, meter %.1f" % [gauge, body.hype])
	if body.music_starts != 1 or not body.music_player.playing:
		diffs.append("his theme started %d times, playing %s" % [body.music_starts, body.music_player.playing])
	var gates: Node = sm.gates()
	if gates == null or not gates.visible or gates.is_open():
		diffs.append("the gates not shut")
	if t.player.is_talking or t.player.is_action_locked:
		diffs.append("the player held")
	var mark: Vector2 = sm.states["Takeover"].PLAYER_MARK
	if t.player.global_position.distance_to(mark) > 0.5:
		diffs.append("the player at %s, not on their mark %s" % [t.player.global_position, mark])
	if t.live_balloon() != null:
		diffs.append("a balloon up")
	var takeover: Node = sm.states["Takeover"]
	if is_instance_valid(takeover.prop) or is_instance_valid(takeover.hurled) or not takeover.fx.is_empty() or is_instance_valid(takeover.roar_fx):
		diffs.append("the takeover's own left")
	if not t.get_nodes_in_group(sm.HAZARD_GROUP).is_empty():
		diffs.append("hazards left")
	if computah.visible or computah.is_in_group("fight_boss") or computah.hurtbox.is_in_group("boss_target") or computah.hud_layer.visible:
		diffs.append("Computah still in the ring %s, a boss %s, his bar up %s" % [computah.visible, computah.is_in_group("fight_boss"), computah.hud_layer.visible])
	return diffs


static func playing(players: Array) -> bool:
	for player in players:
		if is_instance_valid(player) and player.playing:
			return true
	return false
