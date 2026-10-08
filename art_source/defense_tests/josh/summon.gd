extends RefCounted

# josh_summon (the user, 2026-09-29): Josh's summon (JoshCardsSummon), which opens his fight behind the VS card and
# brings in his card-gate portals and his card hands (JoshHandsRig). Real time (--max-fps 60): the ESC hold is counted
# in real seconds, and so is the VS card's input grace.
#   watched  entered from the boss select, the lines read and the card let run: the Summon starts on the pre-fight
#            timer; the portals stand at PORTAL_POINTS from their first frame and go open, then loop; sixteen cards,
#            eight a portal, each ending within a px of its portal's pivot; the hands form at their rest points and
#            hover there; it ends at SUMMON.end, to a frame, into the Hand Slam; the player is never held and walks
#            during it; nothing of it is left in the hazard group, and its hint is retired.
#   tap      a tapped ESC mid-summon pauses rather than skipping: its clock, its cards and the portals hold for 60
#            frames, and the resume carries it on.
#   hold     ESC held from 0.8 s skips it within the 0.4 s hold and two frames, to the end state a watched one leaves,
#            field by field; the pause never opens, and the first attack starts once.
#   retry    a second go in the same run plays the quick one - no flurry, over by 0.6 s and a frame - to the same end
#            state.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")

const SCENE := "res://Scenes/Bosses/JoshBossFightScene.tscn"
const BODY := "Arena/JoshCardsScene/JoshCardsCharacterBody"
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const FRAME := 1.0 / 60.0
const SLACK := 0.0001
# Where the hold and the tap come in, into the flurry.
const HOLD_AT := 0.8
const TAP_AT := 0.9
# BossEntrance.SKIP_HOLD.
const SKIP_HOLD := 0.4
# The walk tried in the middle of it: straight up, so the player stays level with him and he faces the same way.
const WALK_AT := 1.2
const WALK_FRAMES := 10


static func run(t) -> void:
	var watched: Dictionary = await _watched(t)
	await _tapped(t)
	await _held(t, watched)
	await _retry(t, watched)


#GETTING THERE

# The fight entered from the boss select (a fresh run) or again in the same run, its lines read and the card let
# run out on its own, until the summon is up. `record` gets the state he is in as the pre-fight timer fires.
static func _to_summon(t, fresh: bool, record := {}) -> Node:
	if fresh:
		await t.enter_fight(SCENE)
	else:
		t.change_scene_to_file(SCENE)
		while t.current_scene == null or t.current_scene.scene_file_path != SCENE:
			await t.process_frame
		await t.wait(3)
		t.player = t.current_scene.get_node(PLAYER_PATH)
		t.defense = t.player.get_node("Defense")
		await t.skip_entrance()
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	var summon: Node = t.sm.states["Summon"]
	# After the fight's own handler, which the scene connected first.
	t.sm.post_dialogue_pre_fight_timer.timeout.connect(func(): record["after_timer"] = str(t.sm.current_state.name), CONNECT_ONE_SHOT)
	for i in 3000:
		var card: Node = t.vs_card()
		if t.sm.current_state == summon or (card != null and card.is_playing()):
			break
		if i % 8 == 0:
			t.tap(KEY_ENTER)
		await t.physics_frame
	await t.wait_until(func(): return t.sm.current_state == summon, 900)
	return summon


#WHAT IT LEAVES

# The end state, read on the first step after it: what a watched summon leaves and a skip must leave too.
static func _end_state(t, summon: Node) -> Dictionary:
	var rig: Node = t.sm.hands
	var out := {"state": str(t.sm.current_state.name), "finished": summon.finished, "cards": summon.cards.size(),
		"flurry_nodes": _flurry_nodes(t).size(), "hint_retired": summon.entrance == null, "built": rig.built,
		"josh": [t.boss.ground_position, t.boss.sprite.flip_h, t.boss.air.visible, t.boss.shadow.visible, t.boss.current_anim],
		"cycles": t.sm.cycles_started}
	for side in Layout.SIDES:
		var portal: Node2D = rig.portal_of(side)
		var hand: Node2D = rig.hand_of(side)
		out[side] = {"portal": portal.pivot_point() if portal else Vector2.INF, "sequence": portal.sequence if portal else &"",
			"portal_shown": portal.visible if portal else false, "mode": hand.mode if hand else -1,
			"hand_at": hand.drawn_point() if hand else Vector2.INF, "hand_shown": hand.visible if hand else false,
			"sort_y": hand.global_position.y if hand else -1.0, "z": hand.z_index if hand else -1, "clip": hand.clip if hand else &""}
	return out


static func _flurry_nodes(t) -> Array:
	return t.live_hazards().filter(func(h): return str(h.name).begins_with("SummonCard"))


static func _differences(got: Dictionary, want: Dictionary) -> Array:
	var diffs := []
	for key in want:
		if str(got.get(key)) != str(want[key]):
			diffs.append([key, got.get(key), want[key]])
	return diffs


# Resting at their portals and hovering, both of them.
static func _resting(t) -> bool:
	var rig: Node = t.sm.hands
	for side in Layout.SIDES:
		var hand: Node2D = rig.hand_of(side)
		if hand == null or hand.mode != JoshHand.Mode.REST or not hand.visible or hand.clip != &"hover":
			return false
		if hand.drawn_point().distance_to(Layout.rest_point(side)) > 0.5:
			return false
	return true


#WATCHED

static func _watched(t) -> Dictionary:
	t.log_p("-- watched, from the boss select, the lines read and the card let run")
	var record := {}
	var summon: Node = await _to_summon(t, true, record)
	var rig: Node = t.sm.hands
	var seen := {"states": ["Intro"], "talking": false, "pivots_off": [], "sequences": {&"left": [], &"right": []},
		"formed": {}, "before_end": false, "end": {}, "hazards_at_end": -1, "music": t.boss.music_player.playing}
	var watch := func():
		var state := str(t.sm.current_state.name)
		if seen.states[-1] != state:
			seen.states.append(state)
			if seen.states.size() >= 2 and seen.states[-2] == "Summon" and seen.end.is_empty():
				seen.end = _end_state(t, summon)
				seen.hazards_at_end = t.live_hazards().size()
		if t.sm.current_state != summon:
			return
		if t.player.is_talking:
			seen.talking = true
		for side in Layout.SIDES:
			var portal: Node2D = rig.portal_of(side)
			if portal != null:
				if portal.pivot_point().distance_to(Layout.PORTAL_POINTS[side]) > 0.5:
					seen.pivots_off.append([side, portal.pivot_point()])
				var sequences: Array = seen.sequences[side]
				if portal.visible and (sequences.is_empty() or sequences[-1] != portal.sequence):
					sequences.append(portal.sequence)
			var hand: Node2D = rig.hand_of(side)
			if hand != null and hand.clip == &"form" and not seen.formed.has(side):
				seen.formed[side] = {"mode": hand.mode, "at": hand.drawn_point()}
		if summon.clock >= Layout.SUMMON.end - FRAME - SLACK and not summon.finished:
			seen.before_end = _resting(t)
	t.physics_frame.connect(watch)
	# The walk, in the middle of it.
	await t.wait_until(func(): return summon.clock >= WALK_AT, 300)
	var from: Vector2 = t.player.global_position
	t.press(KEY_UP)
	await t.wait(WALK_FRAMES)
	t.release(KEY_UP)
	var walked: float = from.y - t.player.global_position.y
	await t.wait_until(func(): return t.sm.current_state != summon, 300)
	await t.wait(2)
	t.physics_frame.disconnect(watch)

	var arrivals: Array = summon.arrivals
	var off_pivot: Array = arrivals.filter(func(a): return a.at.distance_to(Layout.PORTAL_POINTS[a.side]) > 1.0)
	var per_side: Dictionary = {}
	for a in arrivals:
		per_side[a.side] = per_side.get(a.side, 0) + 1
	t.log_p("states %s; ended at %.3f s; sequences %s; arrivals %d %s; formed %s; walked %.0f px; hint %s" % [seen.states, summon.ended_at, seen.sequences, arrivals.size(), per_side, seen.formed, walked, summon.entrance])
	var intro_at: int = seen.states.find("Summon")
	t.check(record.get("after_timer") == "Summon" and intro_at == 1 and seen.music, "the Summon starts on the pre-fight timer, straight after his intro, with his theme (%s, %s)" % [record, seen.states])
	t.check(seen.pivots_off.is_empty(), "the portals stand at PORTAL_POINTS from their first frame (%s)" % [seen.pivots_off])
	t.check(Layout.SIDES.all(func(side): return seen.sequences[side].slice(0, 2) == [&"open", &"loop"] and seen.sequences[side].all(func(s): return s in [&"open", &"loop", &"feed"])), "each opens, then loops (%s)" % [seen.sequences])
	t.check(arrivals.size() == 2 * Layout.SUMMON.cards and per_side.get(&"left", 0) == Layout.SUMMON.cards and per_side.get(&"right", 0) == Layout.SUMMON.cards, "sixteen cards, eight into each portal (%s)" % [per_side])
	t.check(off_pivot.is_empty(), "each ends within a px of its portal's pivot (%s)" % [off_pivot])
	t.check(Layout.SIDES.all(func(side): return seen.formed.has(side) and seen.formed[side].mode == JoshHand.Mode.REST and seen.formed[side].at.distance_to(Layout.rest_point(side)) <= 0.5), "the hands form at their rest points (%s)" % [seen.formed])
	t.check(seen.before_end, "and hover there, resting, as it ends")
	t.check(absf(summon.ended_at - Layout.SUMMON.end) <= FRAME + SLACK, "it ends at %.2f s, to a frame (%.3f)" % [Layout.SUMMON.end, summon.ended_at])
	t.check(intro_at >= 0 and seen.states.size() > intro_at + 1 and seen.states[intro_at + 1] == "HandSlam", "into the Hand Slam (%s)" % [seen.states])
	t.check(not seen.talking and walked > 50.0, "the player is never held, and a held arrow walks them (%.0f px)" % walked)
	t.check(seen.hazards_at_end == 0, "nothing of it is left in the hazard group (%d)" % seen.hazards_at_end)
	t.check(seen.end.get("hint_retired", false) and t.current_scene.find_children("SummonSkip", "", true, false).all(func(n): return n.retired), "its hint is retired")
	return seen.end


#A TAP

static func _tapped(t) -> void:
	t.log_p("-- ESC tapped mid-summon")
	var summon: Node = await _to_summon(t, true)
	var rig: Node = t.sm.hands
	var pause: Node = t.pause_menu()
	await t.wait_until(func(): return summon.clock >= TAP_AT, 300)
	await t.tap_pause()
	var opened: bool = pause.is_open() and t.paused
	var held := {"clock": summon.clock, "launched": summon.launched, "cards": summon.cards.map(func(c): return c.node.global_position),
		"portals": Layout.SIDES.map(func(side): return [rig.portal_of(side).step, rig.portal_of(side).clock])}
	await t.wait(60)
	var after := {"clock": summon.clock, "launched": summon.launched, "cards": summon.cards.map(func(c): return c.node.global_position),
		"portals": Layout.SIDES.map(func(side): return [rig.portal_of(side).step, rig.portal_of(side).clock])}
	t.log_p("paused at %s; 60 frames later %s" % [held, after])
	t.check(opened and t.sm.current_state == summon and not summon.finished, "a tapped ESC opens the pause screen and skips nothing")
	t.check(str(held) == str(after), "its clock, its cards and the portals hold for 60 frames")
	await t.tap_pause()
	await t.wait(20)
	t.check(not t.paused and summon.clock > held.clock and t.sm.current_state == summon, "the resume carries it on (%.3f -> %.3f)" % [held.clock, summon.clock])


#A HOLD

static func _held(t, watched: Dictionary) -> void:
	t.log_p("-- ESC held from %.1f s" % HOLD_AT)
	var summon: Node = await _to_summon(t, true)
	var pause: Node = t.pause_menu()
	var hand_slam: Node = t.sm.states["HandSlam"]
	var seen := {"paused": false, "end": {}, "slams": 0, "last": t.sm.current_state}
	var watch := func():
		if pause.is_open() or t.paused:
			seen.paused = true
		if t.sm.current_state != seen.last:
			if t.sm.current_state == hand_slam:
				seen.slams += 1
			if seen.last == summon and seen.end.is_empty():
				seen.end = _end_state(t, summon)
			seen.last = t.sm.current_state
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return summon.clock >= HOLD_AT, 300)
	var pressed_at: float = summon.clock
	t.press(KEY_ESCAPE)
	await t.wait_until(func(): return summon.finished, 120)
	t.release(KEY_ESCAPE)
	await t.wait(60)
	t.physics_frame.disconnect(watch)
	var took: float = summon.ended_at - pressed_at
	var diffs := _differences(seen.end, watched)
	t.log_p("held at %.3f s, skipped at %.3f s (%.3f s); end state %s; differences from a watched one %s" % [pressed_at, summon.ended_at, took, seen.end, diffs])
	t.check(summon.finished and took >= SKIP_HOLD - FRAME - SLACK and took <= SKIP_HOLD + 2.0 * FRAME + SLACK, "it skips within the %.1f s hold and two frames (%.3f)" % [SKIP_HOLD, took])
	t.check(not seen.end.is_empty() and diffs.is_empty(), "to the end state a watched one leaves, field by field (%s)" % [diffs])
	t.check(not seen.paused, "the pause screen never opens")
	t.check(seen.slams == 1 and t.sm.cycles_started == 1, "and the first attack starts once (%d, cycles %d)" % [seen.slams, t.sm.cycles_started])


#A RETRY

static func _retry(t, watched: Dictionary) -> void:
	t.log_p("-- a second go in the same run")
	var summon: Node = await _to_summon(t, false)
	var seen := {"end": {}}
	var watch := func():
		if t.sm.current_state != summon and seen.end.is_empty():
			seen.end = _end_state(t, summon)
	t.physics_frame.connect(watch)
	await t.wait_until(func(): return not seen.end.is_empty(), 120)
	t.physics_frame.disconnect(watch)
	var diffs := _differences(seen.end, watched)
	t.log_p("quick %s, cards launched %d, arrivals %d, ended at %.3f s; differences from a watched one %s" % [summon.quick, summon.launched, summon.arrivals.size(), summon.ended_at, diffs])
	t.check(summon.quick and summon.launched == 0 and summon.arrivals.is_empty(), "the quick one plays, with no flurry")
	t.check(summon.ended_at >= 0.0 and summon.ended_at <= Layout.SUMMON_QUICK.end + FRAME + SLACK, "over by %.1f s and a frame (%.3f)" % [Layout.SUMMON_QUICK.end, summon.ended_at])
	t.check(diffs.is_empty(), "to the same end state (%s)" % [diffs])
