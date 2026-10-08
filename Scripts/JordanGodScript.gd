extends Node2D

# Demon-god Jordan in his last phase, the Puppet Master (JordanGodFightScene), right where his finale left him: he never
# fights himself. He hovers on his point, behind everything, and raises the bosses he erased as marionettes on strings
# from his hands to run combination attacks with them (JordanCombo, one state each, taken in turn by his state machine).
# He is never a physics body, never something the player faces or punches: every uppercut on a puppet runs up its
# strings into him (take_uppercut), and that is the only way he is hurt. JordanGodLayout has every number.
#
# THE FROZEN CONTRACT (the build plan's section 2), what the attacks are written against: max_health, boss_health,
# defeated, get_health_ratio(), get_max_health(), take_uppercut(), fingertip(), play(), set_hud(), layer(),
# on_player_defeated(), take_won_outro() and outro_line_delay(). The rest is his own.
#
# HOW HE IS DRAWN: his body and aura as the finale drew them (JordanFinaleLayout.GOD), his rune circle turning in the
# void behind him, and the arena dressed as that void around him (VoidArena). His puppeteer animations are the drawn
# set once it is in (JordanGodLayout.final_puppeteer), each with its aura strip and its fingertip table; until then
# they play off his hover and talk sheets, the strings hanging off the claws at the tops of his wings.
#
# HIS BAR stays at the top centre, over him, and goes see-through while his drawn body is behind it (_step_see_through).
#
# HIS DEFEAT, the 20th uppercut: the attack he died in hands him its puppets (JordanCombo.adopt_puppets) and is
# released, and FightOutro hands him the won outro (take_won_outro), which his Defeated state plays out: the strings
# snap, the puppets crumple and dissolve, he dissolves, and it fades to TO BE CONTINUED.

const FightOutro := preload("res://Scripts/FightOutro.gd")
const BossHealthBarUI := preload("res://Scripts/BossHealthBarUI.gd")
const Disintegrate := preload("res://Scripts/Disintegrate.gd")
const FinaleLayout := preload("res://Scripts/JordanFinaleLayout.gd")
const Layout := preload("res://Scripts/JordanGodLayout.gd")
const VoidArena := preload("res://Scripts/VoidArena.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
# What he says when he beats the player, under player_lost, in his demon portrait as in the finale (his win plays his
# defeat instead, take_won_outro).
const OUTRO_DIALOGUE := "res://Dialogue/JordanFinale.dialogue"

@onready var state_machine: Node = $StateManager
@onready var music: AudioStreamPlayer = $Music
@onready var sounds_holder: Node = $Sounds

var max_health: int = Layout.UPPERCUTS_TO_BEAT
var boss_health: int = Layout.UPPERCUTS_TO_BEAT
var defeated := false
var health_bar: Control
var hud_layer: CanvasLayer
var hud_tween: Tween
# The bar's wrapper, whose alpha is the see-through over him alone (_step_see_through), apart from the bar's own
# (set_hud) and its rows' (the beat, the dead dim), which it multiplies with.
var hud_see_through: Control
var see_through_tween: Tween
var see_through_on := false
# The block as drawn on screen, plate and row, taken as it is built.
var hud_block := Rect2()
# Each sheet's frames' drawn pixels (their used rects, in texels of the frame), taken the first time it shows.
var used_rects := {}
var body: Sprite2D
var aura: Sprite2D
var darkness: Polygon2D
var layers := {}
var sounds := {}
var sheets := {}
# Whether his drawn puppeteer set plays, and its fingertip table: taken once as he is built, so an import landing mid-
# fight can't mix it with its stand-ins.
var final_puppeteer := false
var tips_table: GDScript
var god_drawn := false
var current_anim := &""
var anim := {}
var anim_step := 0
var anim_clock := 0.0
var anim_next := &""
var anim_done := false
# The loop a hit or a one-shot hands back to.
var base_anim := &"hover"
var shake_tween: Tween
var flash_tween: Tween
var dissolve_tween: Tween
# The puppets his defeat plays out: the ones the attack he died in had up (JordanCombo.adopt_puppets).
var defeat_puppets: Array = []
# The final beam (JordanGodLayout.USE_FINAL_BEAM): `beaten` from his kill until it is decided, `revived` once a failed
# beam has brought him back, `beam_won` once it has won the fight.
var beaten := false
var revived := false
var beam_won := false


func _ready() -> void:
	add_to_group(FightOutro.BOSS_GROUP)
	global_position = Layout.GOD_POINT
	for layer_name in Layout.LAYERS:
		layers[layer_name] = get_parent().get_node(Layout.LAYERS[layer_name])
	var arena := get_parent().get_parent()
	VoidArena.dress(arena)
	VoidArena.build_void(layers[&"void"])
	var start: CharacterBody2D = arena.get_node_or_null(VoidArena.PLAYER)
	if start != null:
		start.global_position = Layout.PLAYER_START
	god_drawn = FinaleLayout.final_god()
	final_puppeteer = god_drawn and Layout.final_puppeteer()
	tips_table = Layout.tips_table() if final_puppeteer else null
	_build_body()
	_build_runes()
	_build_darkness()
	_build_sounds()
	_build_hud()
	var track := Layout.music()
	music.stream = track.stream
	music.volume_db = track.volume_db
	play(&"hover")
	state_machine.start()
	Layout.release_prefetch()


# His fight's wider view goes with it: whatever comes next is drawn on the arena's own.
func _exit_tree() -> void:
	ScreenView.clear_base(get_tree())


#THE CONTRACT

func get_health_ratio() -> float:
	return float(boss_health) / float(max_health)


func get_max_health() -> int:
	return max_health


# The only way he is hurt: `count` off him at once (the puppet's juggle asks for 1 an uppercut), the damage running up
# `from_puppet`'s strings as a bead (JordanStrings.pulse) and reaching him PULSE_TIME later, where his bar drops and he
# flinches. What it took, for the finisher; at 0 he is beaten. `from_puppet` may be null (a test's hook), and then it
# reaches him at once.
func take_uppercut(from_puppet: Node2D, count := 1, pitch := 1.0) -> int:
	if defeated or beaten or boss_health <= 0 or count <= 0:
		return 0
	var dealt := mini(count, boss_health)
	if revived and Layout.REVIVE_ONE_UPPERCUT:
		dealt = boss_health
	boss_health -= dealt
	var pulse: Tween = null
	if is_instance_valid(from_puppet):
		pulse = layer(&"strings").pulse(from_puppet)
	var reach := create_tween()
	if pulse != null:
		play_sound(&"pulse")
		reach.tween_interval(Layout.PULSE_TIME)
	reach.tween_callback(_feel_uppercut.bind(pitch))
	if boss_health <= 0:
		_on_defeated.call_deferred()
	return dealt


func _feel_uppercut(pitch: float) -> void:
	_refresh_health_bar()
	play_sound(&"hit", pitch)
	play(&"hit", base_anim)


# World px of `hand`'s (&"left" or &"right", the screen's) fingertip `index` on this frame: the drawn set's table, in
# its digit order, or the stand-in's wing claws.
func fingertip(hand: StringName, index: int) -> Vector2:
	var tips: Array = _tips_now(hand)
	var texel: Vector2 = tips[clampi(index, 0, tips.size() - 1)]
	if not final_puppeteer:
		var hands: Array = anim.get("hands", [])
		if anim_step < hands.size():
			texel += hands[anim_step].get(hand, Vector2.ZERO)
	return global_position + body.position + (texel + Vector2(0.5, 0.5) - Layout.ANCHOR) * Layout.GOD_SCALE


# His animations: &"hover", &"control", &"summon" (&"summon_left", &"summon_right"), &"yank_left", &"yank_right",
# &"hit". A one-shot holds its last frame when it ends, unless `next` (or its own `next`) follows.
func play(anim_name: StringName, next := &"") -> void:
	var spec: Dictionary = Layout.god_anim(anim_name, final_puppeteer)
	var same_loop: bool = spec.loop and anim.get("loop", false) and spec.sheet == anim.get("sheet", "") \
		and spec.frames == anim.get("frames", [])
	current_anim = anim_name
	anim = spec
	anim_next = next if next != &"" else spec.get("next", &"")
	anim_done = false
	if spec.loop:
		base_anim = anim_name
	if not same_loop:
		anim_step = 0
		anim_clock = 0.0
	if anim_name == &"hit" and not final_puppeteer:
		_placeholder_flinch()
	if not god_drawn:
		return
	var sheet := _sheet(spec.sheet)
	if body.texture != sheet:
		body.frame = 0
		body.texture = sheet
		body.hframes = maxi(roundi(sheet.get_width() / Layout.FRAME.x), 1)
	if aura != null and spec.has("aura"):
		var aura_sheet := _sheet(spec.aura)
		if aura.texture != aura_sheet:
			aura.frame = 0
			aura.texture = aura_sheet
			aura.hframes = maxi(roundi(aura_sheet.get_width() / FinaleLayout.GOD[&"aura"].frame.x), 1)
	_show_frame()


# His boss HUD in or out over `seconds` (at once for 0): the attacks take it down while they play. The bar's own alpha;
# the see-through over him is its wrapper's.
func set_hud(on: bool, seconds := 0.3) -> void:
	if health_bar == null:
		return
	if hud_tween != null and hud_tween.is_valid():
		hud_tween.kill()
	var to := 1.0 if on else 0.0
	if seconds <= 0.0:
		health_bar.modulate.a = to
		return
	hud_tween = create_tween()
	hud_tween.tween_property(health_bar, "modulate:a", to, seconds)


# JordanGodScene's layers: &"void", &"floor", &"strings", &"stage", &"dark", &"fx".
func layer(layer_name: StringName) -> Node2D:
	return layers.get(layer_name)


# FightOutro's lost outro: the attack under way stops and lets the player go, and he hovers on.
func on_player_defeated() -> void:
	state_machine.enter_player_defeated()
	_clear_hazards()


func take_won_outro(outro: Node, line_delay: float) -> void:
	state_machine.states["Defeated"].begin(outro, line_delay)


# A puppet killed him in the air: the outro waits for it to land first, as a juggled boss's does.
func outro_line_delay(player_won: bool) -> float:
	if not player_won:
		return 0.0
	for puppet in defeat_puppets:
		if is_instance_valid(puppet) and puppet.is_juggled():
			return puppet.juggle_art().outro_delay
	return 0.0


#HIS OWN

# A boss in the fight group that can be dazed is what makes PlayerHype count the fight as one with something to spend
# hype on (PlayerHype.is_inert): he never can be, but his puppets can, so he answers the question.
func can_be_dazed() -> bool:
	return false


func player() -> CharacterBody2D:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(FightOutro.PLAYER_PATH) if scene else null


func play_sound(sound_name: StringName, pitch := 1.0) -> void:
	var sound: AudioStreamPlayer = sounds.get(sound_name)
	if sound == null:
		return
	sound.pitch_scale = Layout.SOUNDS[sound_name].pitch * pitch
	sound.play()


# The fingertips a puppet's two strings come from: the drawn table's pair for it, or the layout's.
func string_pair(boss: StringName) -> Array:
	var pairs: Dictionary = _table_constant("PAIRS", {})
	var pair = pairs.get(boss, pairs.get(String(boss), null))
	if pair is Array and not pair.is_empty():
		return pair
	return Layout.STRING_PAIRS.get(boss, [0, 1])


# How taut `hand`'s strings are on this frame: the drawn table's, where it has one, or `fallback`.
func hand_tension(hand: StringName, fallback: float) -> float:
	if not final_puppeteer or not anim.has("tips"):
		return fallback
	var rows = _table_row("TENSION", anim.tips)
	if rows is Array and anim_step < rows.size() and rows[anim_step] is Dictionary:
		var value = rows[anim_step].get(hand, rows[anim_step].get(String(hand), null))
		if value is float or value is int:
			return float(value)
	return fallback


func is_hovering() -> bool:
	return base_anim == &"hover" and current_anim == &"hover"


# His dissolve at the end of his defeat: Disintegrate on his body, his aura and his runes fading with it. Its tween.
func dissolve(seconds: float) -> Tween:
	play_sound(&"dissolve")
	if aura != null:
		aura.create_tween().tween_property(aura, "modulate:a", 0.0, seconds * 0.5)
	for rune in layers[&"void"].get_children():
		if rune.name == &"Runes":
			rune.create_tween().tween_property(rune, "modulate:a", 0.0, seconds)
	dissolve_tween = Disintegrate.start(self, body, seconds)
	return dissolve_tween


#HIS FRAMES

func _process(delta: float) -> void:
	_step_see_through()
	if anim.is_empty() or anim_done:
		return
	anim_clock += delta
	while anim_clock >= _frame_time():
		anim_clock -= _frame_time()
		if anim_step < anim.frames.size() - 1:
			anim_step += 1
		elif anim.loop:
			anim_step = 0
		else:
			anim_done = true
			if anim_next != &"":
				_chain(anim_next, _resume_frame())
			return
		_show_frame()


# The next animation, from frame `resume`: the drawn yanks ride his hover's poses 0-3, so control picks up on its 4.
func _chain(next: StringName, resume: int) -> void:
	play(next)
	if resume > 0 and resume < anim.frames.size():
		anim_step = resume
		anim_clock = 0.0
		_show_frame()


func _resume_frame() -> int:
	if not final_puppeteer or not anim.has("tips"):
		return 0
	var resume = _table_row("NEXT_FRAME", anim.tips)
	return int(resume) if resume is int else 0


func _frame_time() -> float:
	var times: Array = anim.times
	return maxf(float(times[mini(anim_step, times.size() - 1)]), 0.001)


func _show_frame() -> void:
	if not god_drawn:
		return
	body.frame = mini(int(anim.frames[anim_step]), body.hframes - 1)
	if aura != null:
		# The stand-in's talk sheet has no aura of its own: its frames are drawn in hover frame 0's pose.
		aura.frame = mini(int(anim.frames[anim_step]) if anim.has("aura") else 0, aura.hframes - 1)


func _tips_now(hand: StringName) -> Array:
	if final_puppeteer and anim.has("tips"):
		var rows = _table_row("TIPS", anim.tips)
		if rows is Array and anim_step < rows.size() and rows[anim_step] is Dictionary:
			var tips = rows[anim_step].get(hand, rows[anim_step].get(String(hand), null))
			if tips is Array and not tips.is_empty():
				return tips
	var frame := 0
	if anim.get("sheet", "") == Layout.HOVER_SHEET:
		frame = int(anim.frames[anim_step])
	return Layout.PLACEHOLDER_FINGERTIPS[clampi(frame, 0, Layout.PLACEHOLDER_FINGERTIPS.size() - 1)][hand]


# A row of the generated table (JordanGodTips): `table_name`'s entry for `key`, whichever way its keys are written.
func _table_row(table_name: String, key: StringName) -> Variant:
	var table: Dictionary = _table_constant(table_name, {})
	return table.get(key, table.get(String(key), null))


func _table_constant(table_name: String, fallback: Variant) -> Variant:
	if tips_table == null:
		return fallback
	return tips_table.get_script_constant_map().get(table_name, fallback)


func _sheet(path: String) -> Texture2D:
	if not sheets.has(path):
		sheets[path] = load(path)
	return sheets[path]


# The stand-in's flinch, which has no hit drawn: a white flash and a shake of his body.
func _placeholder_flinch() -> void:
	if body == null:
		return
	var spec: Dictionary = Layout.HIT
	if flash_tween != null and flash_tween.is_valid():
		flash_tween.kill()
	body.modulate = spec.flash
	flash_tween = create_tween()
	flash_tween.tween_property(body, "modulate", Color.WHITE, spec.flash_time)
	if shake_tween != null and shake_tween.is_valid():
		shake_tween.kill()
	shake_tween = create_tween()
	var shake: float = spec.shake * Layout.GOD_SCALE / FinaleLayout.SCALE
	for i in spec.steps:
		shake_tween.tween_property(body, "position", Vector2(randf_range(-shake, shake), randf_range(-shake, shake)).round(),
			spec.step_time)
	shake_tween.tween_property(body, "position", Vector2.ZERO, spec.step_time)


#HIS DEFEAT

# His 20th uppercut: the attack he died in hands over its puppets for his defeat to play out (a juggle still in the air
# lands lying), and is released with everything else it put out; then the fight is won.
func _on_defeated() -> void:
	if defeated or beaten:
		return
	if Layout.USE_FINAL_BEAM and state_machine.has_final_beam():
		_begin_final_beam()
		return
	defeated = true
	var combo: Node = state_machine.current_combo()
	if combo != null:
		defeat_puppets = combo.adopt_puppets()
	for puppet in defeat_puppets:
		puppet.stay_down()
		puppet.set_punchable(false)
	state_machine.enter_defeated()
	_clear_hazards()
	FightOutro.finish_fight(get_tree(), true)


# His kill with the final beam on: the attack hands over its puppets as for his defeat, and the beam decides it.
func _begin_final_beam() -> void:
	beaten = true
	revived = false
	var combo: Node = state_machine.current_combo()
	if combo != null:
		defeat_puppets = combo.adopt_puppets()
	for puppet in defeat_puppets:
		puppet.stay_down()
		puppet.set_punchable(false)
	state_machine.enter_final_beam()
	_clear_hazards()


# Five bars: he is gone, and only now is the fight decided - FightOutro stops the player, so not a frame before.
func finish_beam_won() -> void:
	if defeated:
		return
	beam_won = true
	defeated = true
	state_machine.enter_defeated()
	FightOutro.finish_fight(get_tree(), true)


# A failed beam: back with `health` of his bar, refilled over `refill_time`, and his HUD back.
func revive(health: int, refill_time: float) -> void:
	beaten = false
	revived = true
	boss_health = health
	if health_bar != null:
		health_bar.refill_row(0, health, refill_time)
		var ratio := get_health_ratio()
		health_bar.set_heat(0, 1.0 if ratio <= 0.34 else (0.5 if ratio <= 0.6 else 0.0))
	set_hud(true, Layout.HUD_FADE)


func _clear_hazards() -> void:
	for hazard in get_tree().get_nodes_in_group(Layout.HAZARD_GROUP):
		hazard.queue_free()


func _refresh_health_bar() -> void:
	if health_bar == null:
		return
	health_bar.set_value(0, boss_health)
	var ratio := get_health_ratio()
	health_bar.set_heat(0, 1.0 if ratio <= 0.34 else (0.5 if ratio <= 0.6 else 0.0))


#BUILDING HIM

# As the finale placed him: each strip's anchor texel's top-left corner on his point, at GOD_SCALE, the aura added over
# him.
func _build_body() -> void:
	if not god_drawn:
		var spec: Dictionary = FinaleLayout.PLACEHOLDER_GOD
		body = Sprite2D.new()
		body.name = "Body"
		body.texture = load(spec.spec.sheet)
		body.hframes = maxi(roundi(body.texture.get_width() / spec.spec.frame.x), 1)
		body.frame = spec.spec.frames[0]
		body.offset = Vector2(0, -spec.spec.frame.y / 2.0)
		body.scale = Vector2.ONE * Layout.GOD_SCALE * spec.scale
		body.modulate = spec.tint
		add_child(body)
		return
	body = _strip(Layout.HOVER_SHEET, Layout.FRAME, Layout.ANCHOR)
	body.name = "Body"
	add_child(body)
	var aura_spec: Dictionary = FinaleLayout.GOD[&"aura"]
	if ResourceLoader.exists(aura_spec.sheet):
		aura = _strip(aura_spec.sheet, aura_spec.frame, aura_spec.anchor)
		aura.name = "Aura"
		var added := CanvasItemMaterial.new()
		added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		aura.material = added
		add_child(aura)


func _strip(path: String, frame: Vector2, anchor: Vector2) -> Sprite2D:
	var strip := Sprite2D.new()
	strip.texture = _sheet(path)
	strip.hframes = maxi(roundi(strip.texture.get_width() / frame.x), 1)
	strip.centered = false
	strip.offset = -anchor
	strip.scale = Vector2.ONE * Layout.GOD_SCALE
	return strip


# His rune circle on his chest core, turning, in the void behind him: in from the first frame, since the finale left
# it up. The finale's offset to his core is at 3 px a texel; it goes with him at GOD_SCALE.
func _build_runes() -> void:
	var void_layer: Node2D = layers[&"void"]
	var core: Vector2 = global_position + FinaleLayout.RUNES_OFFSET * Layout.GOD_SCALE / FinaleLayout.SCALE
	if ResourceLoader.exists(FinaleLayout.GOD_RUNES):
		var runes := Sprite2D.new()
		runes.name = "Runes"
		runes.texture = load(FinaleLayout.GOD_RUNES)
		runes.hframes = FinaleLayout.RUNES_FRAMES
		runes.scale = Vector2.ONE * Layout.GOD_SCALE
		runes.position = void_layer.to_local(core)
		void_layer.add_child(runes)
		var turn := runes.create_tween().set_loops()
		for i in FinaleLayout.RUNES_FRAMES:
			turn.tween_callback(runes.set_frame.bind(i))
			turn.tween_interval(FinaleLayout.RUNES_FRAME_TIME)
		return
	var spec: Dictionary = FinaleLayout.PLACEHOLDER_GOD
	var ring := Line2D.new()
	ring.name = "Runes"
	var points := PackedVector2Array()
	for i in 48:
		points.append(Vector2.from_angle(TAU * i / 48) * spec.ring_radius * Layout.GOD_SCALE / FinaleLayout.SCALE)
	ring.points = points
	ring.width = Layout.GOD_SCALE * 3.0
	ring.default_color = spec.ring
	ring.closed = true
	ring.position = void_layer.to_local(core)
	void_layer.add_child(ring)
	ring.create_tween().set_loops().tween_property(ring, "rotation", TAU, 8.0).from(0.0)


# Attack 1's darkness (JordanCombo.darken): pitch black on the Dark layer, reaching well past the view.
func _build_darkness() -> void:
	var border: Rect2 = Layout.DARK_BORDER
	darkness = Polygon2D.new()
	darkness.name = "Darkness"
	darkness.polygon = PackedVector2Array([border.position, Vector2(border.end.x, border.position.y), border.end,
		Vector2(border.position.x, border.end.y)])
	darkness.color = Layout.DARK_COLOR
	darkness.modulate.a = 0.0
	darkness.visible = false
	layers[&"dark"].add_child(darkness)


func _build_sounds() -> void:
	for sound_name in Layout.SOUNDS:
		var spec: Dictionary = Layout.SOUNDS[sound_name]
		var sound := AudioStreamPlayer.new()
		sound.name = String(sound_name)
		sound.stream = load(spec.stream)
		sound.volume_db = spec.volume_db
		sound.pitch_scale = spec.pitch
		sounds_holder.add_child(sound)
		sounds[sound_name] = sound


# One row, Jordan's, and no Break gauge: he takes one an uppercut. It fades in as the fight opens (JordanGodOpen), in
# its see-through wrapper.
func _build_hud() -> void:
	hud_layer = CanvasLayer.new()
	hud_layer.name = "Hud"
	add_child(hud_layer)
	hud_see_through = Control.new()
	hud_see_through.name = "SeeThrough"
	hud_see_through.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud_layer.add_child(hud_see_through)
	health_bar = BossHealthBarUI.create({
		"rows": [{"key": Layout.HUD_KEY, "max": max_health, "value": boss_health}],
		"plate": Layout.HUD_PLATE,
		"text": Layout.HUD_TEXT,
	})
	hud_see_through.add_child(health_bar)
	health_bar.modulate.a = 0.0
	hud_block = _drawn_rect(health_bar)


# Every piece of `item` showing, on screen: its sheets' frames and its controls' rects.
func _drawn_rect(item: CanvasItem) -> Rect2:
	var drawn := Rect2()
	var parts: Array = item.find_children("*", "CanvasItem", true, false)
	parts.push_front(item)
	for part in parts:
		var rect := Rect2()
		if not part.is_visible_in_tree():
			continue
		if part is Sprite2D and part.texture != null:
			rect = part.get_global_transform() * part.get_rect()
		elif part is Control:
			rect = part.get_global_rect()
		if rect.has_area():
			drawn = rect if not drawn.has_area() else drawn.merge(rect)
	return drawn


#SEE-THROUGH

# The block eases to see-through while his drawn body overlaps it on screen, and back once he is clear (JordanGodLayout's
# HUD_SEE_THROUGH_ALPHA and HUD_SEE_THROUGH_FADE), on real seconds like the bar.
func _step_see_through() -> void:
	if hud_see_through == null:
		return
	var behind := _body_on_screen().intersects(hud_block)
	if behind == see_through_on:
		return
	see_through_on = behind
	if see_through_tween != null and see_through_tween.is_valid():
		see_through_tween.kill()
	var to := Layout.HUD_SEE_THROUGH_ALPHA if behind else 1.0
	# With none of the block showing (the fight's first frame, an attack's HUD down) there is nothing to ease.
	if health_bar.modulate.a <= 0.0:
		hud_see_through.modulate.a = to
		return
	see_through_tween = hud_see_through.create_tween().set_ignore_time_scale(true)
	see_through_tween.tween_property(hud_see_through, "modulate:a", to, Layout.HUD_SEE_THROUGH_FADE)


# His body's drawn pixels on screen this frame: the used rect of the frame showing, through where and how big he is
# drawn (GOD_POINT, GOD_SCALE, his flinch) and this frame's view. His aura and his runes aren't in it.
func _body_on_screen() -> Rect2:
	if body == null or body.texture == null or not body.is_visible_in_tree():
		return Rect2()
	var frames: Array = _used_rects(body.texture, body.hframes, body.vframes)
	var used: Rect2 = frames[clampi(body.frame, 0, frames.size() - 1)]
	if not used.has_area():
		return Rect2()
	return body.get_global_transform_with_canvas() * Rect2(body.get_rect().position + used.position, used.size)


func _used_rects(texture: Texture2D, hframes: int, vframes: int) -> Array:
	if used_rects.has(texture):
		return used_rects[texture]
	var frame := Vector2i(texture.get_width() / hframes, texture.get_height() / vframes)
	var image := texture.get_image()
	var readable := image != null and not image.is_empty()
	if readable and image.is_compressed():
		image.decompress()
	var rects: Array[Rect2] = []
	for i in hframes * vframes:
		var at := Vector2i(i % hframes, i / hframes) * frame
		# A sheet whose pixels can't be read counts its whole frame as drawn.
		rects.append(Rect2(image.get_region(Rect2i(at, frame)).get_used_rect()) if readable else Rect2(Vector2.ZERO, frame))
	used_rects[texture] = rects
	return rects
