extends RefCounted

# bixby_inside (the playtest of 2026-10-04): beast Bixby's quake rings are born under his claws, so a ring of his
# catches a player standing between them on the frame it is born (BixbyQuakeRingScript.hurts_inside_at_birth, which
# his send_quake_ring sets). Before, his feet were a spot none of his rings ever reached: a player parked on them through
# his combined attack took its beams and nothing else. --fixed-fps 60, his hovers held and his gauge held.
#   Rings sent from his state machine onto a still player at RING_AT: feet in the middle of the ring as it is born are
#   hit on its first frame; feet just outside its band as it is born are hit only once the band gets to them; a dash out
#   pressed just before its birth is no hit and one PERFECT DODGE; and a ring made the way Liam's fire rings are (the
#   flag off) still leaves a player inside it alone. Then the real combined attack with the player's feet put on his as
#   he touches down and left there: his rings land on them now, the first on the frame of his first pound.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const RingScript := preload("res://Scripts/BixbyQuakeRingScript.gd")

const RING_AT := Vector2(960, 700)
const RING_ID := &"bixby_quake_ring"
# The foot of the player's hurtbox off their centre.
const FEET := Vector2(0, 42)
const KEYS := [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_W]


static func run(t) -> void:
	await t.load_liam()
	await t.skip_vs_card()
	t.hold_break_gauge(t.boss)
	t.sm.hover_time = 600.0
	t.sm.hover_between_attacks = 600.0
	t.cb = t.sm.states["Combined"]
	t.track()
	t.track_dodges()
	if not await t.wait_until(func(): return str(t.sm.current_state.name) == "Hover", 1200):
		t.check(false, "he hovers")
		return
	await _born_inside(t)
	await _born_outside(t)
	await _dashed_out(t)
	await _flag_off(t)
	await _real_attack(t)


static func _fresh(t, feet: Vector2) -> void:
	for code in KEYS:
		t.release(code)
	for ring in t.hazards_of("BixbyQuakeRingScript.gd"):
		ring.queue_free()
	t.sm.states["Hover"].elapsed = 0.0
	await t.settle_player(feet - FEET)
	await t.dash_ready()
	t.clear_iframes()
	t.player.playerHealth = 1000


# Frames from now until the first hit of `id` after `before` events, up to `frames`; -1 for none.
static func _first_hit(t, before: int, id: StringName, frames: int) -> int:
	for i in frames:
		if t.events.slice(before).any(func(e): return e.kind == "HIT" and e.id == id):
			return i
		t.sm.states["Hover"].elapsed = 0.0
		await t.physics_frame
	return -1


static func _born_inside(t) -> void:
	t.log_p("-- feet in the middle of a ring as it is born")
	await _fresh(t, RING_AT)
	var before: int = t.events.size()
	t.sm.send_quake_ring(RING_AT)
	var at := await _first_hit(t, before, RING_ID, 30)
	t.log_p("hit %d frames after it was sent" % at)
	t.check(at >= 0 and at <= 2, "a player standing between his claws is hit on the ring's first frame (%d)" % at)


static func _born_outside(t) -> void:
	t.log_p("-- feet just outside the band as it is born")
	var outer := CombinedLayout.RING_START_RADIUS + CombinedLayout.RING_HURT_HALF_WIDTH
	var off := outer + 30.0 + 18.0
	await _fresh(t, RING_AT + Vector2(off, 0))
	var before: int = t.events.size()
	t.sm.send_quake_ring(RING_AT)
	var at := await _first_hit(t, before, RING_ID, 60)
	var due := ceili((off - 18.0 - outer) / t.sm.quake_ring_speed * 60.0)
	t.log_p("%.0f px out: hit %d frames after it was sent, the band due there in about %d" % [off, at, due])
	t.check(at > 2 and absi(at - due) <= 2, "nothing is hit outside the band as it is born, only once the band gets there (%d, due %d)" % [at, due])


static func _dashed_out(t) -> void:
	t.log_p("-- a dash out pressed just before it is born")
	await _fresh(t, RING_AT)
	var before: int = t.events.size()
	var dodged_before: int = t.dodges.size()
	var health: int = t.player.playerHealth
	t.press(KEY_RIGHT)
	t.tap(KEY_W)
	await t.wait_until(func(): return t.player.is_dodging, 10)
	t.sm.send_quake_ring(RING_AT)
	await t.wait(40)
	t.release(KEY_RIGHT)
	var hits: Array = t.events.slice(before).filter(func(e): return e.kind == "HIT")
	var reads: Array = t.dodges.slice(dodged_before).filter(func(d): return d.id == RING_ID)
	t.log_p("hits %s, perfect dodges %d, health %d -> %d" % [hits.map(func(e): return e.id), reads.size(), health, t.player.playerHealth])
	t.check(hits.is_empty() and t.player.playerHealth == health, "dashing out of it as it is born is no hit")
	t.check(reads.size() == 1, "and one PERFECT DODGE (%d)" % reads.size())


static func _flag_off(t) -> void:
	t.log_p("-- a ring made the way Liam's fire rings are")
	await _fresh(t, RING_AT)
	var before: int = t.events.size()
	var ring: Node2D = RingScript.new()
	ring.speed = t.sm.quake_ring_speed
	ring.player = t.player
	t.current_scene.add_child(ring)
	ring.global_position = RING_AT
	var at := await _first_hit(t, before, RING_ID, 20)
	ring.queue_free()
	t.check(not ring.hurts_inside_at_birth and at == -1, "is off by default, and leaves a player inside it alone (%d)" % at)


static func _real_attack(t) -> void:
	t.log_p("-- his combined attack with the player's feet on his")
	if not await t.cb_force(Vector2(960, 760)):
		t.check(false, "the combined attack starts from his hover")
		return
	var cb: Node = t.cb
	await t.wait_until(func(): return cb.phase != cb.Phase.DESCENT, 120)
	var feet: Vector2 = t.boss.ground_position
	await t.settle_player(feet - FEET)
	t.clear_iframes()
	var before: int = t.events.size()
	var first_impact := -1.0
	while t.sm.current_state == cb:
		if first_impact < 0.0 and cb.impact_done:
			first_impact = t.defense.clock
		await t.physics_frame
	var rings: Array = t.events.slice(before).filter(func(e): return e.kind == "HIT" and e.id == RING_ID)
	var ids := {}
	for e in t.events.slice(before):
		ids[e.id] = ids.get(e.id, 0) + 1
	var first := INF if rings.is_empty() else float(rings[0].t)
	t.log_p("his feet at %s, the player's on them: hits %s, the first ring hit %.3f s after his first pound" % [feet, ids, first - first_impact])
	t.check(rings.size() >= 2, "his rings land on a player parked on his feet (%d)" % rings.size())
	t.check(absf(first - first_impact) <= 2.0 / 60.0 + 0.0001, "the first on the frame of his first pound")
