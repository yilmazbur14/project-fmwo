extends RefCounted

# What the liam/ modes share: Liam's test scene (SCENES["liam_elements"], LiamTestFightScene: the takeover's end state,
# Liam on his pillar at the top of the ring) with his rotation held, and the pieces of it they reach for.
# tier=placeholder holds his final art off (LiamArtLayout's USE_FINAL_* switches), so a run can cover the stand-ins once
# the approved sheets are in.

const FIGHT := "liam_elements"
const BODY := "Arena/LiamScene/LiamCharacterBody"
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const Patterns := preload("res://Scripts/LiamTremorPatterns.gd")
const LiamWave := preload("res://Scripts/LiamWave.gd")
const KEYS := [KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_SHIFT, KEY_W, KEY_Q]


# His test scene at the takeover's end state, his first attack held off.
static func enter(t) -> void:
	if t.tier == "placeholder":
		hold_placeholders()
	await t.load_fight(FIGHT)
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	hold(t)
	# His test scene hands straight on to attack 1 through his wind's reset: nothing of it may be left, not even the
	# water a cut-short first wave spends.
	await clear(t)
	t.boss.flood.drain(0.0)
	t.player.playerHealth = 1000
	t.log_p("art in: pillar %s, waves %s, flood %s, ice %s, ridges %s, gust %s, poses %s, juggle %s, row %s, tornados %s, steam %s, lunge %s" % [Layout.final_pillar(),
		Layout.final_wave(), Layout.final_flood(), Layout.final_ice(), Layout.final_tremor(), Layout.final_gust(),
		Layout.uses_final(&"perch_idle"), Layout.juggle() == Layout.FINAL_JUGGLE, Layout.final_row(), Layout.final_tornado(),
		Layout.final_steam(Layout.STEAM_TILE_SHEET), Layout.uses_final(&"lunge")])


static func hold_placeholders() -> void:
	Layout.USE_FINAL_POSES = false
	Layout.USE_FINAL_PILLAR = false
	Layout.USE_FINAL_WAVE = false
	Layout.USE_FINAL_GUST = false
	Layout.USE_FINAL_FLOOD = false
	Layout.USE_FINAL_TREMOR = false
	Layout.USE_FINAL_BREATH = false
	Layout.USE_FINAL_SHADOW = false
	Layout.USE_FINAL_JUGGLE = false
	Layout.USE_FINAL_ROW = false
	Layout.USE_FINAL_DOWNDRAFT = false
	Layout.USE_FINAL_FIRESTORM = false
	Layout.USE_FINAL_STEAM = false
	Layout.USE_FINAL_LUNGE = false


# On his pillar in Idle, nothing of his running and no attack coming, and nobody left in the air on his wind.
static func hold(t) -> void:
	t.sm.states["Idle"].beat_left = -1.0
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.sm.cancel_launch()


static func start(t, state_name: String) -> void:
	t.sm.on_child_transition(t.sm.current_state, state_name)


static func keys_up(t) -> void:
	for code in KEYS:
		t.release(code)


# The player at `at`, still, on a full bar, out of every lock and every cooldown of their last move.
static func fresh(t, at: Vector2, settle := 45) -> void:
	keys_up(t)
	await t.wait(settle)
	t.player.unlock_actions()
	t.player.set_ice(false)
	t.player.global_position = at
	t.player.velocity = Vector2.ZERO
	t.defense._set_stamina(t.defense.max_stamina)
	t.clear_iframes()
	t.player.playerHealth = 1000
	await t.wait(2)


static func player_box(t) -> Rect2:
	var shape: CollisionShape2D = t.player.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


static func hurtbox_top(t) -> float:
	return t.area_rect(t.player.hurtBox).position.y


# A wave of his own, outside his Tsunami: its front at `front`, on `side`, rolling from now.
static func spawn_wave(t, side: StringName, front: float) -> Node2D:
	var wave = LiamWave.new()
	wave.side = side
	wave.front_y = front
	wave.height = t.sm.wave_height
	wave.speed = t.sm.wave_speed
	wave.carry_time = t.sm.wave_carry
	wave.rope_top = t.sm.ROPES.position.y
	wave.rope_bottom = t.sm.ROPES.end.y
	wave.player = t.player
	wave.host = t.sm
	wave.flood = t.boss.flood
	wave.fx_layer = t.boss.fx_layer
	t.sm.add_hazard(wave, t.boss.wave_layer)
	return wave


# Everything of his on the mat and in the air gone, and nothing coming.
static func clear(t) -> void:
	hold(t)
	for hazard in t.get_nodes_in_group(t.sm.HAZARD_GROUP):
		hazard.queue_free()
	t.sm.carry_left = 0.0
	await t.wait(2)


# A punch at the pillar from where the player stands: whether the pillar took it.
static func punch_pillar(t) -> bool:
	var before: int = t.sm.pillar_hits
	await t.swing()
	return t.sm.pillar_hits > before


static func state(t) -> String:
	return String(t.sm.current_state.name)
