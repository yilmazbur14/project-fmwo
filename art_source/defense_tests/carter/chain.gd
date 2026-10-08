extends RefCounted

# carter_chain (tuning 2026-10-05): his attacks are one combo (CarterStateMachine.chain_attacks). --fixed-fps 60.
# The barrage's feints first: dealt from clone_count and cycle_yellows 2000 times a count, the yellows asked for
# (no more than half the clones after the first), clone 1 never one, and no two adjacent - shuffling and retrying
# used to leave two adjacent in 55% of the six-feint rounds (CarterRagingDemon._build_pattern).
# The barrages after the first: pale_x_clone_count clones with PALE_X_ROUND of them pale X (tuning 2026-10-06).
# Then a real combo with the chain on: a barrage with its first three reds parried hands straight on to the Beam
# Rush as the lights come up - no window, its bank cashed, the player free and back under the ropes, the dark
# gone, nothing of the barrage left out; the Beam Rush sat through hands straight on to the second Beam Rush and
# that to the Messatsu, with nothing of the four left; and the Messatsu ends in his window, which isn't a Break's
# and still dazes him for the plain finisher. With the chain off, a barrage hands over to its own window.
# And every window long enough to walk in on (the user, 2026-10-06: every opening long enough to walk in and land
# three punches, and three punches always the uppercut): a Messatsu sat through from across the ring earns the
# shortest window the string can, and it is still at least CarterStateMachine.walk_in_time from where the player
# stands, and walking in from there - no dash - lands three punches and the daze before it shuts.

const SPEC := "res://art_source/defense_tests/gauge_fights/carter_akuma.gd"


static func run(t) -> void:
	await pattern(t)
	await combo(t)
	await unchained(t)
	await far_window(t)


static func pattern(t) -> void:
	await t.load_carter_akuma()
	var sm: Node = t.sm
	var demon: Node = sm.get_node("RagingDemon")
	var count_was: int = sm.clone_count
	for count in [15, sm.clone_count, sm.pale_x_clone_count]:
		sm.clone_count = count
		for asked in range(0, count / 2 + 2):
			sm.cycle_yellows = asked
			var bad := {"count": 0, "first": 0, "adjacent": 0}
			var want: int = mini(asked, count / 2)
			for i in 2000:
				demon._build_pattern()
				var picked: Array = range(count).filter(func(k): return demon.feints[k])
				if picked.size() != want or demon.reds_total != count - want:
					bad.count += 1
				if demon.feints[0]:
					bad.first += 1
				if demon._adjacent(picked):
					bad.adjacent += 1
			t.check(bad.count == 0 and bad.first == 0 and bad.adjacent == 0, "%d clones, %d feints asked: always %d dealt, never the first clone, never two adjacent (%s)" % [count, asked, want, bad])
	sm.clone_count = count_was
	sm.cycles_started = 1
	sm.cycle_yellows = sm.yellow_count()
	demon._build_pattern()
	t.check(demon.feints.size() == sm.clone_count and demon.feints.count(true) == 0, "the first barrage: %d clones, all red" % demon.feints.size())
	sm.cycles_started = 4
	sm.cycle_yellows = sm.yellow_count()
	demon._build_pattern()
	t.check(demon.feints.size() == sm.pale_x_clone_count and demon.feints.count(true) == sm.PALE_X_ROUND, "every later one: %d clones, %d of them pale X" % [demon.feints.size(), demon.feints.count(true)])
	sm.cycles_started = 0


static func combo(t) -> void:
	var rush: Node = await t.load_carter_akuma()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var player: Node = t.player
	var demon: Node = sm.get_node("RagingDemon")
	var mess: Node = sm.get_node("Messatsu")
	var spec: GDScript = load(SPEC)
	player.playerHealth = 1000
	sm.chain_attacks = true
	t.log_p("-- a barrage that didn't break him hands straight on to the Beam Rush")
	sm.cycles_started = 0
	sm.start_cycle()
	var parried := 0
	for k in 3:
		if await spec._parry_clone(t, demon, k):
			parried += 1
	var health: int = boss.boss_health
	var seen := {"recover": false, "rush_at": -1}
	var watch := func() -> void:
		if sm.is_recovering():
			seen.recover = true
		if sm.current_state == rush and seen.rush_at < 0:
			seen.rush_at = Engine.get_physics_frames()
	t.physics_frame.connect(watch)
	var handed: bool = await t.wait_until(func(): return sm.current_state == rush, 1500)
	await t.wait(1)
	var bank: int = demon.reds_parried / sm.bank_per_parries
	t.log_p("%d reds parried, %d banked; health %d -> %d; in %s" % [demon.reds_parried, bank, health, boss.boss_health, sm.current_state.name])
	t.check(handed and not seen.recover, "the Beam Rush starts with no window between")
	t.check(demon.reds_parried == 3 and health - boss.boss_health == bank, "what the barrage's parries banked is cashed as it hands on (%d)" % (health - boss.boss_health))
	t.check(not player.is_action_locked and player.get_parent().z_index == 0, "the player is free and back under the ropes")
	t.check(demon.released and demon.clone == null, "and nothing of the barrage is left out")
	t.check(await t.wait_until(func(): return not boss.dark_stage.visible, 120), "the dark lifts")

	t.log_p("-- the Beam Rush sat through hands straight on to the second, and that to the Messatsu")
	seen.recover = false
	var cycle: int = sm.cycles_started
	var again: bool = await t.wait_until(func(): return sm.current_state == rush and sm.cycles_started == cycle + 1, 1200)
	t.check(again and not seen.recover, "the second Beam Rush starts with no window between")
	var to_mess: bool = await t.wait_until(func(): return sm.current_state == mess, 1200)
	t.check(to_mess and not seen.recover, "the Messatsu starts with no window between")
	t.check(rush.released and rush.casters.is_empty(), "with nothing of the four left")

	t.log_p("-- and the Messatsu ends in his window")
	var windowed: bool = await t.wait_until(func(): return sm.is_recovering() and boss.hurtbox.monitoring, 1200)
	t.physics_frame.disconnect(watch)
	t.check(windowed and not sm.current_state.from_break, "his window opens after it, not a Break's")
	t.check(boss.can_be_dazed() and not boss.can_be_juggled(), "and it dazes him for the plain finisher")
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()


static func unchained(t) -> void:
	await t.load_carter_akuma()
	var sm: Node = t.sm
	var demon: Node = sm.get_node("RagingDemon")
	t.player.playerHealth = 1000
	sm.chain_attacks = false
	sm.cycles_started = 0
	sm.start_cycle()
	var windowed: bool = await t.wait_until(func(): return sm.current_state != demon, 1500)
	t.check(windowed and sm.is_recovering() and not sm.current_state.from_break, "with the chain off, a barrage hands over to its own window (%s)" % sm.current_state.name)
	sm.recover_timer.stop()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()


static func far_window(t) -> void:
	await _far_window(t, Vector2(250, 700), Vector2(1650, 700))
	await _far_window(t, Vector2(1700, 450), Vector2(260, 880))


static func _far_window(t, stand: Vector2, spot: Vector2) -> void:
	await t.load_carter_akuma()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var player: Node = t.player
	var m: Node = sm.get_node("Messatsu")
	player.playerHealth = 1000
	await t.settle_player(stand)
	if not await t.start_messatsu(m, spot):
		t.check(false, "a Messatsu from across the ring starts")
		return
	if not await t.wait_until(func(): return sm.is_recovering() and boss.hurtbox.monitoring, 1200):
		t.check(false, "and ends in his window")
		return
	var distance: float = player.global_position.distance_to(boss.global_position)
	var earned: float = sm.recover_window(m.parried, sm.messatsu_hits - m.parried)
	var floor_time: float = sm.walk_in_time(distance)
	var window: float = sm.recover_timer.wait_time
	t.log_p("sat through from %.0f px: the string earned %.2f s, walking in takes %.2f s, the window is %.2f s" % [distance, earned, floor_time, window])
	t.check(earned < floor_time and absf(window - floor_time) <= 0.02, "a blown string's window is stretched to the walk in (%.2f s)" % window)
	var finisher: Node = player.get_node("Finisher")
	var held := {}
	# The reaction the floor allows for, then the walk.
	await t.wait(roundi(sm.WALK_IN_REACTION * 60.0))
	var dazed := false
	for frame in 600:
		if finisher.phase != t.FINISHER_OFF:
			dazed = finisher.phase == t.FINISHER_DAZED or finisher.phase == t.FINISHER_SETTLE
			break
		if not sm.is_recovering():
			break
		var shape: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
		var box: Rect2 = shape.global_transform * shape.shape.get_rect()
		var reach: Rect2 = player.global_transform * player.punch_box(player.facing)
		var want := Vector2.ZERO
		if box.grow(-6.0).intersects(reach):
			if player.state_machine.current_state.name != "Punching":
				t.tap(KEY_Q)
		else:
			var right: Rect2 = player.punch_box(player.Facing.RIGHT)
			want = Vector2(box.position.x - right.end.x + 24.0, box.get_center().y - right.get_center().y) - player.global_position
		_steer(t, held, want)
		await t.physics_frame
	_steer(t, held, Vector2.ZERO)
	t.check(dazed, "walking in from there, three punches land and daze him before it shuts")
	await t.wait_until(func(): return finisher.phase == t.FINISHER_OFF, 900)


static func _steer(t, held: Dictionary, dir: Vector2) -> void:
	var want := {}
	if dir.length() > 4.0:
		var n := dir.normalized()
		if n.x > 0.38:
			want[KEY_RIGHT] = true
		elif n.x < -0.38:
			want[KEY_LEFT] = true
		if n.y > 0.38:
			want[KEY_DOWN] = true
		elif n.y < -0.38:
			want[KEY_UP] = true
	for k in [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN]:
		if want.has(k) and not held.has(k):
			t.press(k)
			held[k] = true
		elif not want.has(k) and held.has(k):
			t.release(k)
			held.erase(k)
