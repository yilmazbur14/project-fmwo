extends RefCounted

# matt_echo_boomburst (the BOOMBURST, a whole heart that a dash goes through). --fixed-fps 60, lone rings at his roar
# mouth at HOME, the dash pressed in place.
#   dodged    a dash whose immunity covers its first touch: DODGED, a perfect dodge, one read on the gauge and the
#             dash's stamina back
#   window    the dash's start swept a step at a time round the touch: the starts that go through it span at least
#             MIN_SPAN, on top of him (it touches as it is born) and in the far corner
#   hit       no dash: its damage (a heart and a half since 2026-10-05); a parry press instead: the same
#   i-frames  a red ring that hits two steps before it doesn't shield the player: the BOOMBURST lands too

const Lib := preload("res://art_source/defense_tests/matt/echo_lib.gd")
const MIN_SPAN := 0.18
const FAR := Vector2(123, 933)


static func run(t) -> void:
	await t.load_matt()
	t.hold_break_gauge(t.boss)
	t.track()
	t.track_dodges()
	var sm: Node = t.sm
	var boss: Node = t.boss
	await Lib.reset(t)
	boss.global_position = sm.HOME
	var mouth: Vector2 = boss.mouth_point(&"roar")
	var on_top: Vector2 = mouth - (t.hurtbox_rect().get_center() - t.player.global_position)

	t.log_p("-- dashed through")
	var gauge: Node = boss.break_gauge
	await t.fresh_dash_ready()
	t.player.global_position = Vector2(960, 760)
	gauge.locked = false
	gauge.value = 0.0
	t.dodges.clear()
	var ring := Lib.spawn(t, Lib.BOOMBURST)
	await t.wait_until(func(): return Lib.contact_in(t, ring) <= 0.06, 60)
	var stamina_before: float = t.defense.stamina
	t.tap(KEY_W)
	await t.wait_until(func(): return ring.answered, 60)
	await t.wait(20)
	var paid: float = gauge.value
	t.log_p("dash 0.06 s before its touch: result %d, perfect dodges %s, gauge %.3f (a read %.3f), stamina %.1f -> %.1f" % [ring.result, t.dodges.map(func(d): return d.id), paid, gauge.perfect_dodge_gain, stamina_before, t.defense.stamina])
	t.check(ring.result == Lib.HitInfo.Result.DODGED and t.dodges.size() == 1 and t.dodges[0].id == &"matt_boomburst" and is_equal_approx(paid, gauge.perfect_dodge_gain),
		"a dash whose immunity covers the first touch goes through it: DODGED, a perfect dodge and one read")
	t.check(t.defense.stamina >= stamina_before - 0.01, "and the dash's stamina comes back")
	gauge.locked = true
	gauge.value = 0.0

	t.log_p("-- the window")
	for spot in [on_top, FAR]:
		var through := []
		for k in range(-3, 22):
			await Lib.reset(t)
			await t.dash_ready()
			await t.wait(40)
			t.player.global_position = spot
			# Steps from the spawn to the touch, then the press k steps before the touch.
			var contact := 0
			if spot != on_top:
				var probe_ring := Lib.spawn(t, Lib.BOOMBURST)
				probe_ring.player = null
				contact = ceili(Lib.contact_in(t, probe_ring) * 60.0)
				probe_ring.queue_free()
			var r: Node2D
			if k > contact:
				t.tap(KEY_W)
				await t.wait(k - contact)
				r = Lib.spawn(t, Lib.BOOMBURST)
			else:
				r = Lib.spawn(t, Lib.BOOMBURST)
				await t.wait(contact - k)
				t.tap(KEY_W)
			await t.wait_until(func():
				t.player.global_position = spot
				return r.answered, 90)
			if r.result == Lib.HitInfo.Result.DODGED:
				through.append(k)
		var span: float = (through.max() - through.min() + 1) / 60.0 if not through.is_empty() else 0.0
		t.log_p("at %s: presses %s steps before the touch go through (%.3f s)" % [spot.round(), through, span])
		t.check(span >= MIN_SPAN, "at %s the dash starts that go through the BOOMBURST span %.3f s, at least %.2f" % [spot.round(), span, MIN_SPAN])

	t.log_p("-- not dodged")
	await Lib.reset(t)
	t.player.global_position = Vector2(960, 760)
	var health: int = t.player.playerHealth
	var plain := Lib.spawn(t, Lib.BOOMBURST)
	await t.wait_until(func(): return plain.answered, 60)
	var lost_plain: int = health - t.player.playerHealth
	var plain_result: int = plain.result
	await Lib.reset(t)
	await t.wait(70)
	t.player.global_position = Vector2(960, 760)
	health = t.player.playerHealth
	var guarded := Lib.spawn(t, Lib.BOOMBURST)
	await t.wait_until(func(): return Lib.contact_in(t, guarded) <= 0.10, 60)
	t.tap(KEY_SHIFT)
	await t.wait_until(func(): return guarded.answered, 60)
	var lost_guarded: int = health - t.player.playerHealth
	t.log_p("no dash: -%d (result %d); a parry press: -%d (result %d)" % [lost_plain, plain_result, lost_guarded, guarded.result])
	var gold_damage: int = load("res://Scripts/AttackCatalog.gd").get_attack(&"matt_boomburst").damage
	t.check(lost_plain == gold_damage and plain_result == Lib.HitInfo.Result.HIT, "no dash: its %d half-hearts" % gold_damage)
	t.check(lost_guarded == gold_damage and guarded.result == Lib.HitInfo.Result.HIT, "a parry press does nothing: its %d half-hearts" % gold_damage)

	t.log_p("-- a red just before it")
	await Lib.reset(t)
	await t.wait(70)
	t.player.global_position = Vector2(960, 760)
	health = t.player.playerHealth
	var red := Lib.spawn(t, Lib.RED)
	await t.wait(2)
	var gold := Lib.spawn(t, Lib.BOOMBURST)
	await t.wait_until(func(): return gold.answered, 60)
	t.log_p("red %d at %.3f, BOOMBURST %d at %.3f; lost %d" % [red.result, red.touched_at, gold.result, gold.touched_at, health - t.player.playerHealth])
	var both: int = 1 + load("res://Scripts/AttackCatalog.gd").get_attack(&"matt_boomburst").damage
	t.check(red.result == Lib.HitInfo.Result.HIT and gold.result == Lib.HitInfo.Result.HIT and health - t.player.playerHealth == both,
		"a red ring hitting first buys no i-frames against the BOOMBURST: %d half-hearts in all" % both)
	await Lib.reset(t)
