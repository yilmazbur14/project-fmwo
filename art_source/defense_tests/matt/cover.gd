extends RefCounted

# matt_cover (tuning 2026-10-04, the 2026-10-04 playtest's occlusion): the arena draws by y, so a player whose
# sprite stands higher up the screen than his feet draws under him, and from the Trueshot's bottom station his
# 288 px back hid a player still on their mark (about (959, 901)) for the whole 1.4 s of the shot. Now he goes
# see-through over them (MattArtLayout.STATION_SEE_THROUGH, MattTrueshotBarrage._step_see_through). --fixed-fps 60.
# Real shots, one station at a time, the player standing still:
#   covered   on their mark at the bottom station, and inside each station's sprite higher up the screen than his
#             feet: see-through on every step of the charge and the release, the shot still landing on them (the
#             wave or the burst, R9), and solid again once he has reformed on the next station or gone to Spent
#   in front  just lower on the screen than his feet at the top, left and right stations, the player's sprite
#             overlapping his: they draw over him, so he stays solid
#   clear     well away from every station: solid
#   cut short a barrage ended by a bare transition mid-charge, see-through, leaves him solid

const LAYOUT := "res://Scripts/MattArtLayout.gd"
const AWAY := Vector2(600, 760)
# Up into his sprite from his feet, and down in front of them.
const INSIDE := 80.0
const IN_FRONT := 20.0


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.player.playerHealth = 100000
	var sm: Node = t.sm
	var see: float = load(LAYOUT).STATION_SEE_THROUGH
	var mark: Vector2 = t.player.global_position
	t.log_p("the player's mark %s; see-through alpha %.2f" % [mark, see])
	for s in sm.STATIONS.size():
		var station: Dictionary = sm.STATIONS[s]
		var feet: Vector2 = station.feet
		var inside: Vector2 = feet - Vector2(0, INSIDE)
		var spots := [{"at": inside, "what": "inside", "covered": true}]
		if station.name == &"bottom":
			spots.append({"at": mark, "what": "the mark", "covered": true})
		else:
			spots.append({"at": feet + Vector2(0, IN_FRONT), "what": "in front", "covered": false})
		spots.append({"at": AWAY, "what": "away", "covered": false})
		for spot in spots:
			var got: Dictionary = await shoot(t, s, spot.at)
			t.log_p("%s station, the player %s %s: %s" % [station.name, spot.what, spot.at, got])
			if spot.covered:
				t.check(got.under and got.overlap and is_equal_approx(got.alpha_min, see) and is_equal_approx(got.alpha_max, see) and got.hit and got.solid_after,
					"%s station, the player %s: see-through through the charge and the release (%.2f to %.2f), still shot, solid once he has moved on" % [
					station.name, spot.what, got.alpha_min, got.alpha_max])
			elif spot.what == "in front":
				t.check(not got.under and got.overlap and is_equal_approx(got.alpha_min, 1.0),
					"%s station, the player in front of him, overlapping: drawn over him, so he stays solid (%.2f)" % [station.name, got.alpha_min])
			else:
				t.check(not got.overlap and is_equal_approx(got.alpha_min, 1.0), "%s station, the player away: solid (%.2f)" % [station.name, got.alpha_min])
	await cut_short(t, see)


# One station's real shot at a player held at `at`: his alpha over its charge and release, whether the player's
# sprite drew under him and overlapped his, whether the shot landed, and whether he was solid once he had
# reformed on the next station (or gone to Spent).
static func shoot(t, s: int, at: Vector2) -> Dictionary:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var barrage: Node = sm.states["TrueshotBarrage"]
	var landed := []
	var on_hit := func(hit): landed.append(hit.attack_id)
	t.defense.hit_taken.connect(on_hit)
	await reset(t)
	sm.on_child_transition(sm.current_state, "TrueshotBarrage")
	barrage.station_index = s
	var low := INF
	var high := -INF
	var under := false
	var overlap := false
	var solid_after := false
	for f in 240:
		t.player.global_position = at
		t.player.velocity = Vector2.ZERO
		t.clear_iframes()
		await t.physics_frame
		var here: bool = sm.current_state == barrage and barrage.station_index == s
		if here and barrage.beat in [barrage.Beat.CHARGE, barrage.Beat.FIRE]:
			var alpha: float = boss.sprite.self_modulate.a
			low = minf(low, alpha)
			high = maxf(high, alpha)
			var seen: Rect2 = t.player.sprite.get_global_transform() * t.player.sprite.get_rect()
			var drawn: Rect2 = boss.sprite.get_global_transform() * boss.sprite.get_rect()
			under = t.player.sprite.global_position.y < boss.global_position.y
			overlap = drawn.intersects(seen)
		var moved_on: bool = sm.current_state != barrage or (barrage.station_index > s and barrage.beat != barrage.Beat.OUT \
			and barrage.beat_clock >= load(LAYOUT).STATION_SEE_THROUGH_TIME + 1.0 / 60.0)
		if moved_on:
			solid_after = is_equal_approx(boss.sprite.self_modulate.a, 1.0) or barrage.covers_player()
			break
	t.defense.hit_taken.disconnect(on_hit)
	return {"alpha_min": low, "alpha_max": high, "under": under, "overlap": overlap,
		"hit": landed.has(&"matt_trueshot"), "solid_after": solid_after}


static func reset(t) -> void:
	var sm: Node = t.sm
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(2)


# Mid-charge at the bottom station over the player on their mark, then a bare transition: solid on the next step.
static func cut_short(t, see: float) -> void:
	var sm: Node = t.sm
	var boss: Node = t.boss
	var barrage: Node = sm.states["TrueshotBarrage"]
	var mark: Vector2 = sm.STATIONS[2].feet - Vector2(0, 54)
	await reset(t)
	sm.on_child_transition(sm.current_state, "TrueshotBarrage")
	barrage.station_index = 2
	var charging: bool = await t.wait_until(func():
		t.player.global_position = mark
		return barrage.beat == barrage.Beat.CHARGE and barrage.beat_clock > 0.3, 120)
	var before: float = boss.sprite.self_modulate.a
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.physics_frame
	var after: float = boss.sprite.self_modulate.a
	t.log_p("cut short mid-charge: %.2f -> %.2f" % [before, after])
	t.check(charging and is_equal_approx(before, see) and is_equal_approx(after, 1.0), "a barrage cut short mid-charge leaves him solid (%.2f -> %.2f)" % [before, after])
	await reset(t)
