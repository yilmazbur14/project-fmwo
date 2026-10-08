extends RefCounted

# What the matt_echo* modes share: starting an Echo Roars instance, a lone ring, where a ring will touch the player,
# and a press timed to it. Rings are MattEchoRingScript; their kinds are its Kind enum.

const RING := preload("res://Scripts/MattEchoRingScript.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const RED := 0
const ECHO := 1
const GHOST := 2
const PUNISH := 3
const BOOMBURST := 4
# A phase-one instance with no X, for the modes whose rings are counted or timed one by one, whatever
# MattStateMachine.echo_feints_phase_one says (off since 2026-10-06, on from 2026-10-05).
const NO_X := [-1, -1, -1]


# Nothing of his left out, the player whole and rested, then an instance from his first step: phase two's if `two`,
# with these Xs if given (one slot a string, -1 for none). Returns the state.
static func start(t, two: bool, feints: Array = []) -> Node:
	var sm: Node = t.sm
	await reset(t)
	sm.plan_echo(two)
	if not feints.is_empty():
		sm.cycle_echo_feints.assign(feints)
	sm.on_child_transition(sm.current_state, "EchoRoars")
	return sm.states["EchoRoars"]


static func reset(t) -> void:
	var sm: Node = t.sm
	for hazard in t.get_nodes_in_group(sm.HAZARD_GROUP):
		hazard.queue_free()
	sm.on_child_transition(sm.current_state, "Idle")
	sm.beat_timer.stop()
	await t.wait(2)
	t.player.playerHealth = 100000
	t.clear_iframes()
	t.defense._set_stamina(t.defense.max_stamina)
	t.defense.rearm_parry()
	t.boss.boss_health = t.boss.max_health


# A lone ring of `kind` born now at his roar mouth (he stands where he is), with the fight's numbers.
static func spawn(t, kind: int) -> Node2D:
	var sm: Node = t.sm
	var ring: Node2D = RING.new()
	ring.kind = kind
	ring.player = t.player
	ring.speed = sm.echo_ring_speed
	ring.start_radius = sm.echo_ring_start_radius
	ring.end_radius = sm.echo_ring_end_radius
	ring.band = sm.echo_band
	ring.birth_disc_time = sm.echo_birth_disc_time
	sm.add_hazard(ring, t.boss.mouth_point(&"roar"), t.boss.projectile_layer)
	return ring


# Seconds until `ring`'s band reaches the player's hurtbox where it is now, from its own radius and speed; 0 if it
# touches already, -1 once it has answered.
static func contact_in(t, ring: Node2D) -> float:
	if ring.answered:
		return -1.0
	var rect: Rect2 = t.hurtbox_rect()
	var nearest: float = ring.centre.clamp(rect.position, rect.end).distance_to(ring.centre)
	return maxf((nearest - ring.band - ring.radius) / ring.speed, 0.0)


# Steps until every ring of `echo` is answered or gone, or `frames`: `on_step` is called each step before it.
static func run_until_done(t, echo: Node, frames: int, on_step: Callable = Callable()) -> void:
	var sm: Node = t.sm
	for f in frames:
		if on_step.is_valid():
			on_step.call()
		await t.physics_frame
		if sm.current_state != echo:
			return


# Every touch of `echo`'s rings from here on, as they come: [kind, result, touched_at, ring].
static func watch_touches(echo: Node, into: Array) -> Callable:
	var on_touch := func(ring: Node2D, result: int): into.append([ring.kind, result, ring.touched_at, ring])
	echo.ring_touched.connect(on_touch)
	return on_touch
