extends RefCounted

# Jordan's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=jordan). The keys and the optional statics are listed over
# GAUGE_FIGHTS_DIR there. He is the reference fight on BossBroken and BossJuggled.
# His phase 1 is the kaiju's while JordanKaijuLayout.USE_KAIJU is on (read as this spec loads): its knock-off his punish
# window, its two turns his cycle, its own reads to a Break (JordanKaijuLayout.BREAK_READS) and its stomp the strong
# parry. With it off, the funko summon's.

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")
const ArtLayout := preload("res://Scripts/JordanArtLayout.gd")
const Breath := preload("res://Scripts/States/Jordan/JordanBreath.gd")
const Stomp := preload("res://Scripts/States/Jordan/JordanStomp.gd")
const FunkoThrow := preload("res://Scripts/JordanFunkoThrow.gd")

const CLASSIC := {
	"body": "Arena/JordanScene/JordanCharacterBody",
	# His spot, the user's call. His soles are on y 506 there, already lower than his juggle floor.
	"home": Vector2(960, 410),
	"light": &"funko_blast",
	"strong": &"",
	"foreign": &"eric_quake_wave_v2",
	"punish_state": "Taunt",
	"broken_state": "Broken",
	"cycle_states": ["SummonFunkos"],
	"defeated_state": "Defeated",
	"reads_to_break": 6,
	"art": "res://Scripts/JordanArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}
const KAIJU := {
	"body": "Arena/JordanScene/JordanCharacterBody",
	# Where the player is put about him: he rides the kaiju at its home (park), and his Break throws him off to
	# Layout.BREAK_THROW_OFF, so this only places the player, clear of its walls.
	"home": Vector2(1100, 410),
	"light": FunkoThrow.ATTACK_ID,
	"strong": &"jordan_kaiju_stomp",
	"foreign": &"eric_quake_wave_v2",
	"punish_state": "Dismounted",
	"broken_state": "Broken",
	"cycle_states": ["Breath", "Stomp"],
	"defeated_state": "Defeated",
	"reads_to_break": Layout.BREAK_READS,
	"art": "res://Scripts/JordanArtLayout.gd",
	"juggle_via": "clip",
	"drives_player": true,
}
static var SPEC: Dictionary = KAIJU if Layout.USE_KAIJU else CLASSIC


# On the kaiju he is parked riding it at its home; off it, on his spot.
static func park(t, home: Vector2) -> void:
	if not t.sm.kaiju_mode:
		t.boss.global_position = home
		return
	var kaiju: Node2D = t.sm.kaiju
	kaiju.place(Layout.HOME)
	kaiju.set_lift(0.0)
	kaiju.light_spines(0)
	kaiju.set_charge(0.0)
	kaiju.play_anim(&"idle")
	t.sm.set_mounted(true)
	t.boss.play_anim(&"ride_idle")
	t.sm.phase_b = false


# His states only run while `fighting` is set, which his post-dialogue timer does and
# reset_gauged()'s stop_boss_timers() keeps from happening. His Idle is held short of summoning, so
# nothing he sends out lands between the checks, until a Break or a juggle sends him back into it and
# starts his cycle again, as it does in play.
static func reset(t) -> void:
	t.sm.fighting = true
	t.sm.stagger_left = 0.0
	t.sm.states["Idle"].rested = -INF
	t.boss.explosion_hits_this_cycle = 0
	t.boss.paid_throws.clear()


static func entry_cases(t) -> Array:
	var sm = t.sm
	if sm.kaiju_mode:
		return kaiju_entry_cases(t)
	return [
		["between two summons", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["his summon's wind-up", func(): sm.on_child_transition(sm.current_state, "SummonFunkos"), func(): return sm.current_state.name == "SummonFunkos" and sm.current_state.elapsed >= 0.3],
		["his figures giving chase", func(): sm.on_child_transition(sm.current_state, "SummonFunkos"), func():
			var figures: Array = t.hazards_of("FunkoFigureScript.gd")
			return figures.size() >= 2 and figures.all(func(f): return f.phase == f.Phase.CHASING)],
		["the taunt", func(): sm.on_child_transition(sm.current_state, "Taunt"), func(): return sm.current_state.name == "Taunt"],
	]


# On the kaiju, a Break out of each of its turns and the gaps between them, on the ground: one in the air waits for the
# landing (jordan_kaiju tier=stomp).
static func kaiju_entry_cases(t) -> Array:
	var sm = t.sm
	return [
		["between two turns", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["the breath's charge", func(): sm.on_child_transition(sm.current_state, "Breath"), func(): return sm.current_state.name == "Breath" and sm.current_state.beat == Breath.Beat.CHARGE],
		["his figures giving chase", func(): sm.on_child_transition(sm.current_state, "Breath"), func():
			var figures: Array = t.hazards_of("FunkoFigureScript.gd")
			return figures.size() >= 2 and figures.all(func(f): return f.phase == f.Phase.CHASING)],
		["its beam sweeping", func(): sm.on_child_transition(sm.current_state, "Breath"), func(): return sm.current_state.name == "Breath" and sm.current_state.beat == Breath.Beat.FIRE],
		["the stomp's rear", func(): sm.on_child_transition(sm.current_state, "Stomp"), func(): return sm.current_state.name == "Stomp" and sm.current_state.beat == Stomp.Beat.REAR],
		["knocked off", func(): sm.on_child_transition(sm.current_state, "Dismounted"), func(): return sm.current_state.name == "Dismounted"],
		["on its lowered head after its breath", func(): sm.on_child_transition(sm.current_state, "Recoil"), func(): return sm.current_state.name == "Recoil" and sm.current_state.open],
	]


static func extra(t) -> void:
	if t.sm.kaiju_mode:
		await kaiju_extra(t)
		return
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var broken = sm.states["Broken"]
	var juggled = sm.states["Juggled"]

	t.log_p("-- standing high, a Break slides him down to his juggle floor first (BossBroken)")
	boss.global_position = Vector2(960, 200)
	await t.settle_player(Vector2(600, 700))
	var floor_y: float = juggled.floor_y()
	gauge.add(gauge.max_value)
	var broke: bool = await t.wait_until(func(): return sm.current_state == broken, 30)
	var driven: bool = await t.wait_until(func(): return not t.player.is_action_locked, 120)
	var feet: Vector2 = broken._feet()
	var box: Rect2 = boss.hurtbox_rect()
	var stand_off: float = t.player.global_position.y + broken.PLAYER_FEET_OFFSET - broken.PLAYER_IN_FRONT - box.end.y
	t.log_p("floor y %.1f: soles from y 296 to %s; the player driven to %s, %.1f px off his ground line" % [floor_y, feet, t.player.global_position, stand_off])
	t.check(broke and driven and feet == Vector2(960, roundf(floor_y)), "his soles slide from y 296 down to his floor, y %.0f (%s)" % [roundf(floor_y), feet])
	t.check(absf(stand_off) <= 1.0, "and the player is driven in beside where he lands, on that ground line")
	var lift_scale: float = juggled.headroom() / t.player.finisher.planned_apex(3)
	t.check(lift_scale >= 0.49, "where a three-uppercut juggle is drawn at least half its height (%.2f)" % lift_scale)

	t.log_p("-- a Break out of his summon's wind-up puts him down at once, and no figure comes of it")
	await t.reset_gauged(t.fight_spec.home)
	sm.on_child_transition(sm.current_state, "SummonFunkos")
	await t.wait(18)
	gauge.add(gauge.max_value)
	await t.wait_until(func(): return sm.current_state == broken, 30)
	await t.wait(2)
	var sprite: Sprite2D = boss.sprite
	t.log_p("anim %s, sheet %s frame %d, stars at %s, daze anchor %s" % [boss.current_anim, sprite.texture.resource_path.get_file(), sprite.frame, broken.stars.global_position, boss.get_daze_anchor()])
	t.check(boss.current_anim == &"broken" and sprite.texture.resource_path.ends_with("jordan_defeat.png") and sprite.frame == 4, "kneeling on defeat frame 4, not finishing the wind-up first")
	t.check(broken.stars.global_position == broken.head_point().round() and boss.get_daze_anchor() == broken.head_point(), "his stars and the finisher's daze anchor over the kneel's crown")
	await t.wait(60)
	t.check(t.hazards_of("FunkoFigureScript.gd").is_empty(), "and the summon he was winding up never comes")

	t.log_p("-- a figure punched back into him is two reads")
	await t.reset_gauged(t.fight_spec.home)
	var breaks := [0]
	var count_break := func(): breaks[0] += 1
	gauge.broke.connect(count_break)
	boss.take_explosion_hit(1)
	t.check(is_equal_approx(gauge.value, 2.0 * gauge.parry_gain), "its blast: %.3f, two reads of %.3f" % [gauge.value, gauge.parry_gain])
	await t.reset_gauged(t.fight_spec.home)
	for i in 4:
		gauge.add(gauge.parry_gain)
	boss.take_explosion_hit(1)
	t.check(breaks[0] == 1, "four reads and one redirect break him")
	await t.wait(2)
	gauge.broke.disconnect(count_break)
	t.check(sm.current_state == broken and boss.sprite.rotation == 0.0, "down at once, with the blast's lean cut (rotation %.2f)" % boss.sprite.rotation)


# A blast's source the way his thrown figures are: it carries its throw's id.
class Thrown:
	extends Node2D
	var throw_id := -1


static func kaiju_extra(t) -> void:
	var boss = t.boss
	var sm = t.sm
	var gauge = boss.break_gauge
	var kaiju: Node2D = sm.kaiju

	t.log_p("-- a figure punched into the kaiju's legs is two reads and a point off his bar, and it flinches for him")
	t.check(boss.redirect_rect() == Layout.LEG_BOX, "riding it at home, its legs are what a punched figure hits (%s)" % boss.redirect_rect())
	boss.take_explosion_hit(1)
	t.check(is_equal_approx(gauge.value, 2.0 * gauge.parry_gain) and boss.boss_health == boss.get_max_health() - 1 and kaiju.art.modulate.r > 1.0,
		"its blast: %.3f, two reads of %.3f, and the kaiju flashes" % [gauge.value, gauge.parry_gain])
	kaiju.set_lift(200.0)
	t.check(not boss.redirect_rect().has_area(), "in the air nothing of it can be hit")
	kaiju.set_lift(0.0)

	t.log_p("-- a throw's figures pay one read between them, however many are parried")
	await t.reset_gauged(t.fight_spec.home)
	await t.settle_player(Vector2(1200, 640))
	var sources: Array = []
	for id in [7, 7, 8]:
		var source := Thrown.new()
		source.throw_id = id
		t.current_scene.add_child(source)
		sources.append(source)
	var steps: Array = []
	for source in sources:
		var before: float = gauge.value
		t.press(KEY_SHIFT)
		await t.wait(3)
		var result: int = t.front_hit(FunkoThrow.ATTACK_ID, source)
		t.release(KEY_SHIFT)
		steps.append([result, snappedf(gauge.value - before, 0.001)])
		t.clear_iframes()
		t.defense._set_stamina(t.defense.max_stamina)
		await t.wait(40)
	for source in sources:
		source.queue_free()
	t.check(steps[0] == [3, snappedf(gauge.parry_gain, 0.001)] and steps[1] == [3, 0.0] and steps[2] == [3, snappedf(gauge.parry_gain, 0.001)],
		"one throw's two parries pay one read, the next throw's another ([result, gain]: %s)" % [steps])

	t.log_p("-- a Break while he rides it: it collapses and he is thrown off onto open floor, the player beside him")
	await t.reset_gauged(t.fight_spec.home)
	await t.settle_player(Vector2(1200, 640))
	var broken = sm.states["Broken"]
	gauge.add(gauge.max_value)
	await t.wait_until(func(): return sm.current_state == broken, 30)
	await t.wait_until(func(): return broken.slide_left <= 0.0 and not t.player.is_action_locked, 240)
	var soles: Vector2 = boss.to_global(ArtLayout.FLOOR_POINT)
	t.check(soles == Layout.BREAK_THROW_OFF and not boss.mounted and boss.sprite.visible and boss.current_anim == &"broken"
		and kaiju.current_anim in [&"collapse", &"down"], "thrown off to %s, kneeling, the kaiju collapsed (%s, %s, %s)" % [Layout.BREAK_THROW_OFF, soles, boss.current_anim, kaiju.current_anim])
	t.check(broken.stars.global_position == broken.head_point().round() and t.player.global_position.distance_to(soles) < 260.0,
		"his stars over his head, the player driven in beside him (%s)" % t.player.global_position)

	t.log_p("-- knocked off, his punches pay their reads, the POW dazes him and the mash's uppercut lands")
	await t.reset_gauged(t.fight_spec.home)
	sm.on_child_transition(sm.current_state, "Dismounted")
	await t.wait(5)
	t.stop_boss_timers()
	t.place_under(boss.get_finisher_hurtbox())
	await t.wait(6)
	var health: int = boss.boss_health
	for i in 3:
		await t.swing()
		if i < 2:
			await t.wait(6)
	var finisher: Node = t.player.get_node("Finisher")
	# PlayerFinisher's Phase: 2 is dazed, the mash's.
	var dazed: bool = await t.wait_until(func(): return finisher.phase == 2 and finisher.prompt_visible, 120)
	t.check(boss.boss_health == health - 4 and is_equal_approx(gauge.value, gauge.parry_gain) and dazed,
		"three punches and the POW: 4 off his bar, one read (%.3f), and the POW dazes him" % gauge.value)
	health = boss.boss_health
	# Its key bounce is real seconds, which a fixed-fps run outpaces.
	finisher.min_press_interval = 0.0
	await t.mash_finisher()
	t.check(await t.wait_until(func(): return boss.boss_health < health, 90), "and the mash's uppercut lands (%d left)" % boss.boss_health)
