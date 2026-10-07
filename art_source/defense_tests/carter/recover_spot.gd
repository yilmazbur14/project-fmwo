extends RefCounted

# carter_recover_spot (playtest 2026-10-04): where a Raging Demon that didn't break him kneels him for his punish
# window (CarterRagingDemon._recover_spot), out along the compass point its last clone came from. --fixed-fps 60.
# For each of the seven points, a barrage with nothing pressed and its last clone dealt from there: his kneeling
# hurtbox and the finisher's daze stars over it (on his get_daze_anchor(), at the stars' own size) clear of the HUD
# (CarterArtLayout.clear_of_hud) - from the two points 37 degrees up he used to kneel at y 336, his head under his
# health bar block and the stars behind it - and the spot still out on that point's side of the middle. Then, from
# one of those two, three punches and the daze: the stars as really drawn, clear of the HUD; and with his
# break_only_finisher switch on (off by the user's call, 2026-10-05) the same window can't be dazed. And a barrage that
# breaks him still kneels him level with the player, where three punches daze him for the tiered finisher, with the
# stars as really drawn clear of the HUD.
# Then the Messatsu's spot (CarterMessatsu._pick_spot), which his window kneels him on a recoil off: picked 20 times
# from each of 260 player spots, every one with his badge and his kneeling hurtbox, a recoil either way, clear of the
# HUD and messatsu_min_range from the player - the spot area's bottom-left corner is under the player's hearts and
# stamina, where about one in 25 used to kneel him - and three real Messatsus fired at a player up in the top right,
# which deals him to the bottom left, each kneeling him with his hurtbox clear of the HUD.

const RagingDemon := preload("res://Scripts/States/CarterAkuma/CarterRagingDemon.gd")
const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")


static func run(t) -> void:
	for direction: Vector2 in RagingDemon.COMPASS:
		await one(t, direction, direction.y < -0.1 and direction.x > 0.0)
	await broken(t)
	await messatsu_spots(t)


# The finisher's stars, drawn on `anchor`, as a rect.
static func stars_rect(anchor: Vector2) -> Rect2:
	var spec := FinisherArtLayout.stars()
	var sheet: Texture2D = load(spec.texture)
	var size: Vector2 = Vector2(sheet.get_width() / float(spec.hframes), sheet.get_height()) * spec.scale
	return Rect2(anchor - spec.pivot * spec.scale, size)


static func one(t, last: Vector2, daze: bool) -> void:
	await t.load_carter_akuma()
	var sm: Node = t.sm
	# The window a barrage earns opens only with his combo off (chain_attacks): it is the barrage's own
	# ending this holds, and a Break's, which opens either way.
	sm.chain_attacks = false
	var boss: Node = t.boss
	var player: Node = t.player
	var demon: Node = sm.get_node("RagingDemon")
	player.playerHealth = 99
	sm.start_cycle()
	await t.wait_until(func(): return demon.beat == demon.Beat.YANK, 120)
	var last_index: int = demon.directions.size() - 1
	demon.directions[last_index] = last
	if demon.directions[last_index - 1] == last:
		demon.directions[last_index - 1] = -last
	if not await t.wait_until(func(): return sm.is_recovering() and boss.hurtbox.monitoring, 1500):
		t.check(false, "from %s the barrage hands over to his punish window" % last)
		return
	var spot: Vector2 = boss.global_position
	var shape: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var stars := stars_rect(boss.get_daze_anchor())
	var out: Vector2 = spot - sm.ARENA_CENTRE
	t.log_p("last clone from %s: he kneels at %s, hurtbox %s, stars %s" % [last, spot, box, stars])
	t.check(not sm.current_state.from_break, "from %s the window is not a Break's" % last)
	t.check(CarterArtLayout.clear_of_hud(box), "from %s his kneeling hurtbox is clear of the HUD" % last)
	t.check(CarterArtLayout.clear_of_hud(stars), "from %s the daze stars over him are clear of the HUD" % last)
	t.check(out.length() >= 0.75 * sm.recover_offset, "from %s he is still well out from the middle (%.0f px)" % [last, out.length()])
	t.check(out.dot(last) > 0.0 and (absf(last.x) < 0.1 or signf(out.x) == signf(last.x)), "from %s and on that point's side of it (%s)" % [last, out])
	if not daze:
		return
	var finisher: Node = player.get_node("Finisher")
	boss.break_only_finisher = true
	var break_only: bool = boss.can_be_dazed()
	boss.break_only_finisher = false
	t.check(not break_only and boss.can_be_dazed(), "from %s a window he earned can be dazed, and with break_only_finisher on it can't" % last)
	await punch_three(t, box)
	if not await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and is_instance_valid(finisher.stars), 120):
		t.check(false, "from %s three punches daze him" % last)
		return
	var drawn: Sprite2D = finisher.stars
	var drawn_rect := Rect2(drawn.global_position + drawn.offset * drawn.global_scale, drawn.get_rect().size * drawn.global_scale)
	t.log_p("the stars as drawn: %s" % [drawn_rect])
	t.check(not finisher.tiered, "from %s three punches daze him for the plain finisher" % last)
	t.check(CarterArtLayout.clear_of_hud(drawn_rect), "from %s the stars as the daze draws them are clear of the HUD" % last)


# Beside his hurtbox `box`, facing it, and three punches.
static func punch_three(t, box: Rect2) -> void:
	var player: Node = t.player
	var right: Rect2 = player.punch_box(player.Facing.RIGHT)
	player.global_position = Vector2(box.position.x - right.end.x + 24.0, box.get_center().y - right.get_center().y).round()
	player.velocity = Vector2.ZERO
	await t.wait(2)
	for i in 3:
		await t.swing_any()


static func broken(t) -> void:
	await t.load_carter_akuma()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var demon: Node = sm.get_node("RagingDemon")
	t.player.playerHealth = 99
	sm.start_cycle()
	await t.wait_until(func(): return demon.beat == demon.Beat.RUSH and demon.clone_index >= 2, 600)
	demon.last_direction = Vector2(0.8, -0.6)
	boss.break_gauge.add(boss.break_gauge.max_value)
	await t.wait_until(func(): return sm.is_recovering() and boss.hurtbox.monitoring, 120)
	t.log_p("broken: he kneels at %s" % [boss.global_position])
	t.check(sm.current_state.from_break and is_equal_approx(boss.global_position.y, sm.ARENA_CENTRE.y), "a Break still kneels him level with the player (%s)" % [boss.global_position])
	var shape: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
	var finisher: Node = t.player.get_node("Finisher")
	await punch_three(t, shape.global_transform * shape.shape.get_rect())
	if not await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and is_instance_valid(finisher.stars), 120):
		t.check(false, "in his Break's window three punches daze him")
		return
	var drawn: Sprite2D = finisher.stars
	var drawn_rect := Rect2(drawn.global_position + drawn.offset * drawn.global_scale, drawn.get_rect().size * drawn.global_scale)
	t.log_p("the stars as drawn: %s" % [drawn_rect])
	t.check(finisher.tiered, "in his Break's window three punches daze him, for the tiered finisher")
	t.check(CarterArtLayout.clear_of_hud(drawn_rect), "and the stars as the daze draws them are clear of the HUD")


static func messatsu_spots(t) -> void:
	await t.load_carter_akuma()
	var sm: Node = t.sm
	var boss: Node = t.boss
	var player: Node = t.player
	var mess: Node = sm.get_node("Messatsu")
	var recoil: float = CarterArtLayout.MESSATSU_RECOIL * CarterArtLayout.SCALE
	var kneel := CarterArtLayout.local_rect(CarterArtLayout.RECOVER_BODY_BOX).grow_individual(recoil, 0.0, recoil, 0.0)
	seed(20261004)
	var picks := 0
	var under := 0
	var near := 0
	var badge := 0
	for px in range(180, 1760, 80):
		for py in range(170, 940, 60):
			player.global_position = Vector2(px, py)
			for k in 20:
				var spot: Vector2 = mess._pick_spot()
				picks += 1
				if not CarterArtLayout.clear_of_hud(Rect2(spot + kneel.position, kneel.size)):
					under += 1
				if spot.distance_to(player.global_position) < sm.messatsu_min_range:
					near += 1
				if not mess._tell_clear_at(spot):
					badge += 1
	t.log_p("%d Messatsu spots picked: %d kneel him under the HUD, %d inside the range, %d with the badge under it" % [picks, under, near, badge])
	t.check(under == 0, "no Messatsu spot kneels him, a recoil either way, under the HUD (%d of %d)" % [under, picks])
	t.check(near == 0 and badge == 0, "and every one is still out of range of the player with its badge clear (%d, %d)" % [near, badge])
	player.playerHealth = 99
	for i in 3:
		seed(700 + i)
		await t.settle_player(Vector2(1560, 300))
		sm.cycles_started = sm.ATTACK_ROTATION.find("Messatsu")
		sm.start_cycle()
		if not await t.wait_until(func(): return sm.current_state == mess, 120):
			t.check(false, "Messatsu %d starts" % i)
			return
		if not await t.wait_until(func(): return sm.is_recovering() and boss.hurtbox.monitoring, 900):
			t.check(false, "Messatsu %d hands over to his window" % i)
			return
		var shape: CollisionShape2D = boss.hurtbox.get_node("CollisionShape2D")
		var box: Rect2 = shape.global_transform * shape.shape.get_rect()
		t.log_p("Messatsu %d: he kneels at %s, hurtbox %s" % [i, boss.global_position, box])
		t.check(CarterArtLayout.clear_of_hud(box), "Messatsu %d kneels him with his hurtbox clear of the HUD" % i)
		sm.recover_timer.stop()
		sm.on_child_transition(sm.current_state, "Idle")
		sm.beat_timer.stop()
		await t.wait(2)
