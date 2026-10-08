extends Node2D

# Liam's earth pillar (his elements phase): he stands on it STAND_HEIGHT px over its floor line, and the player topples
# him by punching it. LiamScript builds it and puts it just before his body in his scene, so it is drawn behind him on
# the y-sort tie. Its node sits on its floor line; `risen` (0 to 1) is how much of the column is up, which is how high
# he stands on it.
#
# It owns its solid footprint (a StaticBody2D on layer 1, only while parked) and its hurtbox, in boss_target while it
# stands: the player's punches find it by walking up from that hurtbox (PlayerPunching._boss_of), and take_punch() asks
# its host whether each one counts (LiamStateMachine.take_pillar_hit): 1 for a hit it takes, 0 - the dull deflect - when
# it is shielded or its host refuses. It has no can_be_dazed(), so a POW on it never starts the finisher.
# Everything it times is node-bound, so a pause and a finisher's freeze hold it.

const Layout := preload("res://Scripts/LiamArtLayout.gd")
const HitStop := preload("res://Scripts/HitStop.gd")

const PHANTOM_HIT_WINDOW := 0.5
# How far below the footprint a player standing in it is put as it parks.
const NUDGE_GAP := 2.0
# open_with_burst: the shield blown out to this scale as it fades, over this long.
const BURST_SCALE := 1.8
const BURST_TIME := 0.35

# Set before it enters the tree: who is asked about each punch, and the floor its shadow and dust lie on.
var host: Node
var floor_layer: Node2D

# The drawn column: the charged punch's flash lights it (PlayerCombo._charged_feedback writes self_modulate).
var sprite: CanvasItem
var body: StaticBody2D
var body_shape: CollisionShape2D
var hurtbox: Area2D
var risen := 0.0
var standing := false
var parked := false
var shielded := true
var hits := 0
var fight_clock := 0.0
var last_contact_hit_time := -INF

var column: Node2D
var shield: Node2D
var shadow: Node2D
var base_position := Vector2.ZERO
var rise_tween: Tween
var shake_tween: Tween
# The stand-in's pieces.
var mask: Polygon2D
var runes: Array[Polygon2D] = []
var cracks: Array[Line2D] = []
# The final sheets' sprites.
var sheet: Sprite2D
var shield_sheet: Sprite2D
var shield_clock := 0.0
var hit_sound: AudioStreamPlayer
var rise_sound: AudioStreamPlayer
var crumble_sound: AudioStreamPlayer
var open_sound: AudioStreamPlayer
# For a test: how many times open_with_burst has burst the shield.
var bursts := 0


func _ready() -> void:
	_build_body()
	_build_hurtbox()
	_build_art()
	_build_sounds()
	_show_risen()
	visible = false


func _physics_process(delta: float) -> void:
	fight_clock += delta


func _process(delta: float) -> void:
	if shield.visible:
		shield_clock += delta
		if shield_sheet != null:
			shield_sheet.frame = int(shield_clock / Layout.PILLAR_SHIELD_FRAME_TIME) % shield_sheet.hframes
		else:
			shield.modulate.a = 0.75 + 0.25 * sin(shield_clock * TAU * 1.5)
	if is_instance_valid(shadow):
		shadow.global_position = global_position.round()


#WHERE HE STANDS

# px over the floor line his feet are on, as far as it has risen.
func top_height() -> float:
	return Layout.STAND_HEIGHT * risen


# The solid footprint and the hurtbox, in world px.
func footprint() -> Rect2:
	return Rect2(global_position + Layout.PILLAR_FOOTPRINT.position, Layout.PILLAR_FOOTPRINT.size)


func hurtbox_rect() -> Rect2:
	return Rect2(global_position + Layout.PILLAR_HURTBOX.position, Layout.PILLAR_HURTBOX.size)


#ITS LIFE

# Out of the floor at `floor_point` over `time`, shielded and not yet solid. Awaitable.
func rise(floor_point: Vector2, time: float) -> void:
	_kill_rise()
	reset()
	global_position = floor_point.round()
	visible = true
	shadow.visible = true
	standing = true
	_set_target(true)
	if time <= 0.0:
		risen = 1.0
		_show_risen()
		return
	rise_sound.play()
	_puff()
	rise_tween = create_tween()
	rise_tween.tween_method(_set_risen, 0.0, 1.0, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	await rise_tween.finished


# Fully up at once, where it stands.
func stand_up_now() -> void:
	_kill_rise()
	risen = 1.0
	_show_risen()


# Down or up to `value` of its height over `time`, still standing where it is (attack 4 sinks it to a stump and raises
# it again). Awaitable.
func set_risen_to(value: float, time: float) -> void:
	_kill_rise()
	if time <= 0.0:
		_set_risen(value)
		return
	rise_tween = create_tween()
	rise_tween.tween_method(_set_risen, risen, value, time)
	await rise_tween.finished


# Settled at its spot for the fight: solid from here, and a player standing where its footprint lands is put just below
# it, never pushed through it.
func park() -> void:
	parked = true
	_nudge_player()
	body_shape.set_deferred("disabled", false)


# Moving again (a ride), so nothing solid is dragged into the player.
func unpark() -> void:
	parked = false
	body_shape.set_deferred("disabled", true)


# Into the floor over `time` and gone: nothing solid or punchable from the first frame. Awaitable.
func crumble(time: float) -> void:
	if not standing:
		return
	_kill_rise()
	unpark()
	standing = false
	_set_target(false)
	set_shielded(false)
	crumble_sound.play()
	_puff()
	if sheet != null:
		var frames: Array = Layout.PILLAR_CRUMBLE_FRAMES
		rise_tween = create_tween()
		for frame in frames:
			rise_tween.tween_callback(sheet.set_frame.bind(frame))
			rise_tween.tween_interval(time / frames.size())
	else:
		rise_tween = create_tween()
		rise_tween.tween_method(_set_risen, risen, 0.0, time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	await rise_tween.finished
	gone()


# Nothing of it left: hidden, not solid, not a target.
func gone() -> void:
	_kill_rise()
	unpark()
	standing = false
	_set_target(false)
	set_shielded(false)
	visible = false
	shadow.visible = false
	risen = 0.0
	_show_risen()


# A new pillar's look: no hits, shielded.
func reset() -> void:
	hits = 0
	_show_hits()
	set_shielded(true)


func set_shielded(on: bool) -> void:
	shielded = on
	shield.visible = on and standing
	shield_clock = 0.0


# An attack's gate letting go mid-attack (the Tsunami's first crash, the Firestorm's release): the shield's spiral
# blown outward as it fades, with a fizzle, so the moment it can be hit is seen and heard. Only a shield that is up
# bursts.
func open_with_burst() -> void:
	if shielded and standing and shield.get_child_count() > 0:
		var centre: Vector2 = shield.get_child(0).position
		if shield_sheet != null:
			centre += shield_sheet.offset * shield_sheet.scale
		var pivot := Node2D.new()
		pivot.name = "ShieldBurst"
		pivot.position = centre
		add_child(pivot)
		var spiral: Node2D = shield.duplicate()
		spiral.visible = true
		spiral.position = -centre
		pivot.add_child(spiral)
		var blow := pivot.create_tween().set_parallel()
		blow.tween_property(pivot, "scale", Vector2.ONE * BURST_SCALE, BURST_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		blow.tween_property(pivot, "modulate:a", 0.0, BURST_TIME)
		blow.chain().tween_callback(pivot.queue_free)
		open_sound.play()
		bursts += 1
	set_shielded(false)


# `count` of its six runes gone dark and as many cracks, one a hit.
func show_hits(count: int) -> void:
	hits = count
	_show_hits()


#THE PLAYER'S PUNCHES

func _on_hurtbox_entered(area: Area2D) -> void:
	if not area.is_in_group("player attack"):
		return
	# The phantom-hit filter every boss has: a punch that connects as its hitbox switches on is reported again when
	# PlayerPunching switches the hitbox off.
	if not area.monitorable and fight_clock - last_contact_hit_time < PHANTOM_HIT_WINDOW:
		return
	if area.get_parent().combo.resolve_punch(self) > 0 and area.monitorable:
		last_contact_hit_time = fight_clock


# 1 for a hit it takes, 0 while it is shielded or down.
func take_punch(_amount: int) -> int:
	if not standing or not parked or shielded or host == null:
		return 0
	if not host.take_pillar_hit():
		return 0
	_hit_feedback()
	return 1


#BUILDING IT

func _build_body() -> void:
	body = StaticBody2D.new()
	body.name = "Footprint"
	body.collision_layer = 1
	body.collision_mask = 0
	body_shape = CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Layout.PILLAR_FOOTPRINT.size
	body_shape.shape = rect
	body_shape.position = Layout.PILLAR_FOOTPRINT.get_center()
	body_shape.disabled = true
	body.add_child(body_shape)
	add_child(body)


func _build_hurtbox() -> void:
	hurtbox = Area2D.new()
	hurtbox.name = "Hurtbox"
	var shape := CollisionShape2D.new()
	shape.name = "CollisionShape2D"
	var rect := RectangleShape2D.new()
	rect.size = Layout.PILLAR_HURTBOX.size
	shape.shape = rect
	shape.position = Layout.PILLAR_HURTBOX.get_center()
	hurtbox.add_child(shape)
	hurtbox.monitoring = false
	hurtbox.monitorable = false
	hurtbox.area_entered.connect(_on_hurtbox_entered)
	add_child(hurtbox)


func _set_target(on: bool) -> void:
	hurtbox.set_deferred("monitoring", on)
	hurtbox.set_deferred("monitorable", on)
	if on and not hurtbox.is_in_group("boss_target"):
		hurtbox.add_to_group("boss_target")
	elif not on and hurtbox.is_in_group("boss_target"):
		hurtbox.remove_from_group("boss_target")


func _build_art() -> void:
	column = Node2D.new()
	column.name = "Column"
	add_child(column)
	sprite = column
	shield = Node2D.new()
	shield.name = "Shield"
	add_child(shield)
	shadow = Node2D.new()
	shadow.name = "PillarShadow"
	var shade := Polygon2D.new()
	shade.polygon = Layout.ellipse(Vector2(84, 20))
	shade.color = Layout.PLACEHOLDER_PILLAR.shadow
	shadow.add_child(shade)
	if floor_layer != null:
		floor_layer.add_child(shadow)
	else:
		add_child(shadow)
	shadow.visible = false
	if Layout.final_pillar():
		_build_final()
	else:
		_build_placeholder()


func _build_final() -> void:
	sheet = _sheet_sprite(Layout.PILLAR_SHEET)
	column.add_child(sheet)
	if Layout.final_pillar_shield():
		shield_sheet = _sheet_sprite(Layout.PILLAR_SHIELD_SHEET)
		shield.add_child(shield_sheet)
	else:
		_build_placeholder_shield()


func _sheet_sprite(path: String) -> Sprite2D:
	var sheet_sprite := Sprite2D.new()
	var texture: Texture2D = load(path)
	sheet_sprite.texture = texture
	sheet_sprite.hframes = roundi(texture.get_width() / Layout.PILLAR_FRAME.x)
	sheet_sprite.scale = Vector2.ONE * Layout.SCALE
	sheet_sprite.offset = Layout.PILLAR_FRAME / 2.0 - Layout.PILLAR_PIVOT
	return sheet_sprite


# The column and its slab under a mask that ends on the floor line, so as it rises it comes up out of the floor.
func _build_placeholder() -> void:
	var look: Dictionary = Layout.PLACEHOLDER_PILLAR
	var s := Layout.SCALE
	mask = Polygon2D.new()
	mask.polygon = Layout.rect_polygon(Rect2(-40 * s, -80 * s, 80 * s, 80 * s))
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	column.add_child(mask)
	var half: float = look.width / 2.0 * s
	var face := Polygon2D.new()
	face.polygon = Layout.rect_polygon(Rect2(-half, -46 * s, half * 2.0, 46 * s))
	face.color = look.stone
	mask.add_child(face)
	var shade := Polygon2D.new()
	shade.polygon = Layout.rect_polygon(Rect2(half - 6 * s, -46 * s, 6 * s, 46 * s))
	shade.color = look.stone_dark
	mask.add_child(shade)
	var outline := Line2D.new()
	outline.points = Layout.rect_polygon(Rect2(-half, -46 * s, half * 2.0, 46 * s))
	outline.closed = true
	outline.width = s
	outline.default_color = look.edge
	mask.add_child(outline)
	var cap_half: float = look.cap_width / 2.0 * s
	var cap := Polygon2D.new()
	cap.polygon = Layout.rect_polygon(Rect2(-cap_half, -58 * s, cap_half * 2.0, look.cap_height * s))
	cap.color = look.cap
	mask.add_child(cap)
	var cap_outline := Line2D.new()
	cap_outline.points = cap.polygon
	cap_outline.closed = true
	cap_outline.width = s
	cap_outline.default_color = look.edge
	mask.add_child(cap_outline)
	for point: Vector2 in Layout.PLACEHOLDER_RUNES:
		var rune := Polygon2D.new()
		rune.polygon = PackedVector2Array([Vector2(0, -2), Vector2(2, 0), Vector2(0, 2), Vector2(-2, 0)])
		rune.scale = Vector2.ONE * s
		rune.position = point * s
		mask.add_child(rune)
		runes.append(rune)
	for points: Array in Layout.PLACEHOLDER_CRACKS:
		var crack := Line2D.new()
		for point: Vector2 in points:
			crack.add_point(point * s)
		crack.width = s
		crack.default_color = look.crack
		mask.add_child(crack)
		cracks.append(crack)
	_build_placeholder_shield()


func _build_placeholder_shield() -> void:
	var look: Dictionary = Layout.PLACEHOLDER_PILLAR
	var ring := Polygon2D.new()
	ring.polygon = Layout.ellipse(Vector2(84, 110), 32)
	ring.position = Vector2(0, -84)
	ring.color = look.shield
	shield.add_child(ring)
	var edge := Line2D.new()
	edge.points = ring.polygon
	edge.closed = true
	edge.width = 4.0
	edge.default_color = look.shield_edge
	edge.position = ring.position
	shield.add_child(edge)
	shield.visible = false


func _build_sounds() -> void:
	hit_sound = _sound(&"pillar_hit")
	rise_sound = _sound(&"pillar_rise")
	crumble_sound = _sound(&"crumble")
	open_sound = _sound(&"fizzle")


func _sound(key: StringName) -> AudioStreamPlayer:
	var spec: Dictionary = Layout.SFX[key]
	var player := AudioStreamPlayer.new()
	player.stream = load(spec.stream)
	player.pitch_scale = spec.pitch
	player.volume_db = spec.volume_db
	add_child(player)
	return player


#DRAWING IT

func _set_risen(value: float) -> void:
	risen = value
	_show_risen()


func _show_risen() -> void:
	if sheet != null:
		if standing:
			var frames: Array = Layout.PILLAR_RISE_FRAMES
			var step := clampi(int(risen * frames.size()), 0, frames.size() - 1)
			sheet.frame = frames[step] if risen < 1.0 else Layout.PILLAR_STAND_FIRST + mini(hits, 5)
		return
	if mask != null:
		# The drawing slides up through the floor line as it rises: its top at the standing surface when fully up.
		column.position.y = roundf((1.0 - risen) * 58.0 * Layout.SCALE)
		mask.position.y = -column.position.y


func _show_hits() -> void:
	if sheet != null:
		_show_risen()
		return
	var look: Dictionary = Layout.PLACEHOLDER_PILLAR
	for i in runes.size():
		runes[i].color = look.rune_dark if i < hits else look.rune
	for i in cracks.size():
		cracks[i].visible = i < hits


func _hit_feedback() -> void:
	hit_sound.play()
	column.modulate = Color(2.2, 2.2, 2.2)
	var flash := column.create_tween()
	flash.tween_property(column, "modulate", Color.WHITE, 0.15)
	if shake_tween and shake_tween.is_valid():
		shake_tween.kill()
	shake_tween = column.create_tween()
	var rest: Vector2 = Vector2(0, column.position.y)
	for i in 4:
		var offset := Vector2(randf_range(-4, 4), 0).round()
		shake_tween.tween_callback(func() -> void: column.position = rest + offset)
		shake_tween.tween_interval(0.025)
	shake_tween.tween_callback(func() -> void: column.position = rest)
	HitStop.freeze(get_tree(), 0.05)


# Dust at the base: its sheet once it ships, puffs until then.
func _puff() -> void:
	if Layout.final_pillar_dust():
		var dust := _sheet_sprite(Layout.PILLAR_DUST_SHEET)
		add_child(dust)
		var play := dust.create_tween()
		for i in dust.hframes:
			play.tween_callback(dust.set_frame.bind(i))
			play.tween_interval(Layout.PILLAR_DUST_FRAME_TIME)
		play.tween_callback(dust.queue_free)
		return
	for side: float in [-1.0, 1.0]:
		var puff := Polygon2D.new()
		puff.polygon = Layout.ellipse(Vector2(30, 14))
		puff.color = Layout.PLACEHOLDER_PILLAR.dust
		puff.position = Vector2(side * 50.0, -6.0)
		add_child(puff)
		var drift := puff.create_tween().set_parallel()
		drift.tween_property(puff, "position", Vector2(side * 110.0, -24.0), 0.4)
		drift.tween_property(puff, "modulate:a", 0.0, 0.4)
		drift.chain().tween_callback(puff.queue_free)


func _nudge_player() -> void:
	var scene := get_tree().current_scene
	var player: Node2D = scene.get_node_or_null("Arena/MainPlayer/CharacterBody2D") if scene else null
	if player == null:
		return
	var shape: CollisionShape2D = player.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var foot := footprint()
	if not box.intersects(foot):
		return
	player.global_position.y += foot.end.y + NUDGE_GAP - box.position.y


func _kill_rise() -> void:
	if rise_tween and rise_tween.is_valid():
		rise_tween.kill()
	rise_tween = null
