extends RefCounted

# matt_badge (playtest 2026-10-04): every badge he puts up is whole on the screen. --fixed-fps 60.
#   yell    a yell forced on the first punch of a window at HOME and at the Glass Row's station: the yellow
#           badge's drawn rect inside the view, its tip on his crown's spot where that leaves room (HOME) and
#           pushed down onto his crest where it doesn't (the station, where the spot is 53 px from the top and
#           the 72 px badge stood with its top quarter out of the view), never more than the badge's height
#           down onto him.
#   cycle   a real Ezreal set below a third of his health, the player standing on the smoke spot: every red
#           badge it puts up, read on every frame - each Mystic cast's and each Trueshot station's - is whole
#           inside the view.
#   echo    (E9) a phase-two Echo Roars at HOME: every red and yellow badge and every X (one forced a string: none in
#           the live game since 2026-10-06), read on every frame, is whole inside the view and clear of the boss bar
#           (MattStateMachine.HUD_FADE_RECT).

const VIEW := Rect2(0, 0, 1920, 1080)
const RECOVER_SCRIPT := "res://Scripts/States/Matt/MattRecover.gd"


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.player.playerHealth = 1000
	await yell(t)
	await cycle(t)
	await echo(t)


# His live badge, if one is up and not on its way out.
static func live_badge(t) -> Node:
	for child in t.boss.get_parent().get_children():
		var named := str(child.name)
		if named.begins_with("ParryTell") and not named.ends_with("Spent"):
			return child
	return null


static func badge_rect(badge: Node) -> Rect2:
	var sprite: Sprite2D = badge.sprite
	if sprite == null:
		return Rect2(badge.global_position, Vector2.ZERO)
	return sprite.get_global_transform() * sprite.get_rect()


static func yell(t) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var recover: Node = sm.states["Recover"]
	var room: float = load(RECOVER_SCRIPT).badge_floor()
	for spot in [sm.HOME, sm.GLASS_ROW.station]:
		for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
			hazard.queue_free()
		sm.recover_spot = spot
		# Off in the live game (yell_counter_enabled): its badge is held to the screen for when it is on.
		sm.yell_counter_enabled = true
		sm.yell_chance = 1.0
		sm.windows_opened = sm.yell_from_window
		sm.on_child_transition(sm.current_state, "Recover")
		recover.yell_on_hit = 1
		await t.wait(2)
		recover.on_punch_landed(1)
		var up: bool = await t.wait_until(func(): return recover.yell == recover.Yell.TELL and live_badge(t) != null, 10)
		await t.wait(6)
		var badge: Node = live_badge(t)
		var crown: Vector2 = boss.tell_anchor(&"yell_tell")
		var rect := badge_rect(badge) if badge else Rect2()
		var tip: Vector2 = badge.global_position if badge else Vector2.INF
		var want := Vector2(crown.x, maxf(crown.y, room))
		t.log_p("window at %s: crown's spot %s, badge tip %s, drawn %s" % [spot, crown, tip, rect])
		t.check(up and badge != null and badge.dodge and VIEW.encloses(rect),
			"the yell's yellow badge in the window at %s is whole on the screen (%s)" % [spot, rect])
		t.check(tip == want and tip.y - crown.y <= room,
			"its tip on his crown's spot, or pushed down just far enough to fit (%s, crown's spot %s)" % [tip, crown])
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
		await t.wait(20)
	sm.yell_chance = 0.0
	sm.yell_counter_enabled = false
	sm.recover_spot = sm.HOME


static func cycle(t) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	await t.settle_player(t.SMOKE_SPOTS["matt"])
	boss.boss_health = int(boss.max_health * 0.3)
	sm.start_cycle()
	var seen := 0
	var outside := []
	for f in 1200:
		t.player.global_position = t.SMOKE_SPOTS["matt"]
		t.player.velocity = Vector2.ZERO
		t.player.playerHealth = 1000
		var badge: Node = live_badge(t)
		if badge and badge.sprite:
			seen += 1
			var rect := badge_rect(badge)
			if not VIEW.encloses(rect):
				outside.append("%s in %s" % [rect, sm.current_state.name])
		await t.physics_frame
		if sm.current_state.name == "Recover":
			break
	t.log_p("a real Ezreal set: a badge up on %d frames, outside the view on %d: %s" % [seen, outside.size(), outside.slice(0, 4)])
	t.check(seen > 0 and outside.is_empty(), "every red badge of the Ezreal set is whole inside the view (%d frames up, %d out)" % [seen, outside.size()])


static func echo(t) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(2)
	await t.settle_player(t.SMOKE_SPOTS["matt"])
	sm.plan_echo(true)
	# No X in the live game since 2026-10-06 (MattStateMachine.echo_feints_phase_two); one forced a string, so the X
	# kept behind the knob still has its place checked.
	sm.cycle_echo_feints.assign([1, 0, 2, 1])
	var state: Node = sm.states["EchoRoars"]
	sm.on_child_transition(sm.current_state, "EchoRoars")
	var view := Rect2(0, 0, 1920, 1080)
	var hud: Rect2 = sm.HUD_FADE_RECT
	var seen := 0
	var marks := 0
	var bad := []
	for f in 1500:
		t.player.global_position = t.SMOKE_SPOTS["matt"]
		t.player.playerHealth = 1000
		var badge: Node = live_badge(t)
		var rects := []
		if badge and badge.sprite:
			seen += 1
			rects.append(badge_rect(badge))
		if is_instance_valid(state.mark) and state.mark.get_child_count() > 0:
			marks += 1
			var sheet: Sprite2D = state.mark.get_child(0)
			rects.append(sheet.get_global_transform() * sheet.get_rect())
		for rect in rects:
			if not view.encloses(rect) or rect.intersects(hud):
				bad.append("%s" % rect)
		await t.physics_frame
		if sm.current_state != state:
			break
	t.log_p("a phase-two Echo Roars: a badge up on %d frames and an X on %d; outside the view or over the bar %d: %s" % [seen, marks, bad.size(), bad.slice(0, 4)])
	t.check(seen > 0 and marks > 0 and bad.is_empty(), "every badge and X of the Echo Roars is whole in the view and clear of the boss bar (%d, %d frames)" % [seen, marks])
