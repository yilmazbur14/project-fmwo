extends RefCounted

# Computah's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=computah). The keys and the optional statics are listed over
# GAUGE_FIGHTS_DIR there. His gauge is on his own tuned numbers rather than on N reads
# (ComputahScript.BREAK), and his juggle is a BossJuggled drawn from clips.

const SPEC := {
	"body": "Arena/ComputahScene/ComputahCharacterBody",
	# His fighting spot, under his health block, where every attack of his starts and ends.
	"home": Vector2(960, 560),
	# His only parryable attack is the pounce, and it is also the one worth grab_parry_gain: he has no
	# plain parry, and nothing of his is blockable, so there is no second, strong one to name.
	"light": &"computah_chase",
	"strong": &"",
	"foreign": &"josh_card_throw",
	"punish_state": "Punish",
	"broken_state": "Broken",
	# The beam alone since 2026-09-24 (ComputahStateMachine.live_attacks). The entry cases below still break him out
	# of the mine field and the overload, driven directly, so the dormant two stay covered.
	"cycle_states": ["Beam"],
	"defeated_state": "Defeated",
	"reads_to_break": 0,
	"art": "res://Scripts/ComputahArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
	# Nothing of his is blockable, so the guard break is Eric's old charge: it drains his gauge all the same.
	"guard_break_attack": &"wrestler_charge",
}

# Somewhere inside his runner bounds where the chase can close to pounce range: the harness parks the
# player out of reach, in a corner his feet may not follow them into.
const POUNCE_SPOT := Vector2(1400, 700)


# Past the grace a released hold leaves (trap_grace, catch_grace), so no case waits on the last one's.
# reset_gauged() has already stopped his clocks, which holds his cycle short of attacking.
static func reset(t) -> void:
	t.sm.last_release_time = -INF


# The moments his gauge can actually fill in: a window's punches, the overload's charge taking its
# punches, a perfect dodge through the beam as it fires, and a dodge or a parry of the pounce over a
# fresh field. He can't be punched, dodged or parried anywhere else. Plus one guard case: nothing fills
# the gauge while a pod holds the player, but enter_broken's release is what would keep them from being
# left sealed, so it is held to that.
static func entry_cases(t) -> Array:
	var sm = t.sm
	var beam: Node = sm.states["Beam"]
	var chase: Node = sm.states["Chase"]
	var overload: Node = sm.states["Overload"]
	return [
		["a vent, punched", func(): sm.on_child_transition(sm.current_state, "Punish"), func(): return sm.current_state.name == "Punish"],
		["the overload's charge, punched", func(): sm.on_child_transition(sm.current_state, "Overload"), func(): return sm.current_state == overload and overload.phase == overload.Phase.CHARGE],
		["the beam firing, dashed through", func(): sm.on_child_transition(sm.current_state, "Beam"), func(): return sm.current_state == beam and beam.phase == beam.Phase.FIRE],
		["the pounce over a fresh field", func(): t.player.global_position = POUNCE_SPOT; sm.on_child_transition(sm.current_state, "LayMines"), func(): return sm.current_state == chase and chase.phase == chase.Phase.LUNGE and not sm.live_mines().is_empty()],
		["a pod holding the player", func(): t.lay_mine_at(t.player.global_position), func(): return sm.current_state.name == "Trapped"],
	]


# Killed in the air, he lies on the juggle's own KO frames, and his defeat is never played over them.
# With Greyson following him (ComputahScript.greyson_follows), his defeat hands the ring to Greyson rather than
# ending the fight; this mode is about his own kill and its one outro.
static func before_kill(t) -> void:
	t.boss.greyson_follows = false


static func after_kill(t) -> void:
	var sheet: String = t.boss.sprite.texture.resource_path
	t.check(sheet.ends_with("computah_juggle.png") and t.boss.current_anim != &"defeat", "his own defeat never replaces the juggle's KO (%s, %s)" % [sheet.get_file(), t.boss.current_anim])
	t.check(not t.boss.hurtbox.monitoring, "and nothing about him is punchable any more")


static func extra(t) -> void:
	var sm = t.sm
	var boss = t.boss
	var broken: Node = sm.states["Broken"]
	var juggled: Node = sm.states["Juggled"]
	var layout: GDScript = load(SPEC.art)
	var bounds: Rect2 = sm.runner_bounds()
	var hazard_layer: Node = boss.get_parent().get_node("HazardLayer")

	t.log_p("-- a Break mid-chase, high on the mat, slides him down to his juggle floor first")
	var high := Vector2(1100, bounds.position.y)
	boss.global_position = high
	await t.settle_player(Vector2(700, 800))
	var floor_y: float = juggled.floor_y()
	await t.force_break()
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	# The drive and the slide run on the same clock, so the drive handing the player back is the slide's
	# end too, the Break's hit-stop included.
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 120)
	var shape: CollisionShape2D = boss.hurtbox_shape
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var stand_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y
	t.log_p("floor y %.1f: feet from %s to %s; the player driven to %s, %.1f px off his ground line" % [floor_y, high, boss.global_position, t.player.global_position, stand_off])
	t.check(broke and driven and boss.global_position == Vector2(high.x, roundf(floor_y)), "his feet slide straight down to his floor, y %.0f (%s)" % [roundf(floor_y), boss.global_position])
	t.check(absf(stand_off) <= 1.0, "and the player is driven in beside where he lands, on that ground line")
	var lift_scale: float = juggled.headroom() / t.player.finisher.planned_apex(3)
	t.check(lift_scale >= 0.49, "where a three-uppercut juggle is drawn at least half its height (%.3f)" % lift_scale)

	t.log_p("-- a punch doesn't stand him up, and the stars stay on his downed head")
	t.check(await t.wait_until(func(): return boss.current_anim == &"down", 60), "he lands in the floor loop")
	t.check(not sm.trap_allowed(), "no pod may close on the player while he is Broken")
	var dealt: int = await t.swing()
	t.check(dealt > 0 and boss.current_anim == &"down" and boss.sprite.frame in [3, 4], "a punch lands (%d) and he stays in the floor loop (%s, frame %d)" % [dealt, boss.current_anim, boss.sprite.frame])
	var head: Vector2 = boss.frame_point(layout.C_DOWN_HEAD) + Vector2(0, -layout.DAZE_GAP)
	t.check(broken.head_point().is_equal_approx(head) and boss.get_daze_anchor().is_equal_approx(head), "the stars and the finisher's daze both circle his downed head (%s)" % head)
	t.check(is_instance_valid(broken.stars) and broken.stars.global_position.distance_to(head) <= 1.0, "and Broken's own stars are there (%s)" % (broken.stars.global_position if is_instance_valid(broken.stars) else Vector2.ZERO))

	t.log_p("-- juggled: the leap shadow lies on his HazardLayer, and no pod may close")
	sm.enter_juggled()
	await t.wait(2)
	t.check(sm.current_state == juggled, "the first uppercut's hand-over puts him in Juggled")
	t.check(is_instance_valid(juggled.shadow) and juggled.shadow.get_parent() == hazard_layer, "his leap shadow is on HazardLayer (%s)" % (juggled.shadow.get_parent().name if is_instance_valid(juggled.shadow) else "none"))
	t.check(is_instance_valid(juggled.shadow) and not juggled.shadow.is_in_group(sm.HAZARD_GROUP), "and it is not one of his hazards")
	t.check(not sm.trap_allowed(), "no pod may close on the player while he is juggled")
	sm.on_child_transition(sm.current_state, "Idle")
	await t.wait(2)
	var own: String = boss.sprite.texture.resource_path
	t.check(not own.ends_with("computah_juggle.png") and boss.sprite.offset == layout.computah_offset(), "out of the juggle, his own sheet and offset are back (%s, %s)" % [own.get_file(), boss.sprite.offset])

	t.log_p("-- a pod breaking up can neither catch nor hurt anyone")
	await t.reset_gauged(SPEC.home)
	await t.settle_player(Vector2(1400, 800))
	var pod: Node2D = await t.armed_mine_at(Vector2(700, 800))
	t.check(pod.is_armed() and pod.is_in_group(sm.HAZARD_GROUP), "an armed pod is one of his hazards")
	sm.sweep_field()
	t.check(not pod.is_in_group(sm.HAZARD_GROUP) and pod.phase == pod.Phase.FADING, "expired, it leaves his hazards the moment it starts breaking up")
	var health: int = t.player.playerHealth
	await t.settle_player(pod.global_position)
	await t.wait(30)
	t.check(sm.current_state.name != "Trapped" and not t.player.is_action_locked and t.player.playerHealth == health, "standing in it while it breaks up, the player is neither caught nor hurt (%s)" % sm.current_state.name)
	t.check(await t.wait_until(func(): return not is_instance_valid(pod), 90), "and it frees itself once it has played out")

	t.log_p("-- the juggle's last shove keeps inside his bounds, and never toward the player")
	await t.reset_gauged(SPEC.home)
	boss.global_position = Vector2(bounds.position.x + 40.0, 560)
	await t.settle_player(Vector2(bounds.position.x + 300.0, 600))
	boss.juggle_knock_back(Vector2(-240, 0), 0.05)
	await t.wait(10)
	t.check(is_equal_approx(boss.global_position.x, bounds.position.x), "shoved at the ropes, he stops at his bounds (x %.0f)" % boss.global_position.x)
	boss.global_position = Vector2(1000, 560)
	await t.settle_player(Vector2(800, 560))
	boss.juggle_knock_back(Vector2(-240, 0), 0.05)
	await t.wait(10)
	t.check(boss.global_position == Vector2(1000, 560), "shoved toward the player, he isn't moved (%s)" % boss.global_position)
