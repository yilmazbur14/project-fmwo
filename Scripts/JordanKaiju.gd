extends Node2D

# The giant vinyl kaiju Jordan rides through phase 1 (JordanKaijuLayout, the 2026-10-04 redesign). JordanStateMachine
# builds it at Arena/JordanScene/Kaiju when the switch is on: under his scene, so anything that switches his scene off
# switches its walls off too. It is never a hazard and never hittable, and it knows nothing of the fight: his states
# place it, lift it, aim its head, light its plates and pose it.
#
# Its node sits on its feet, its y-sort point, and only its art lifts (set_lift), as Danny's does. Each animation is
# drawn the best way the layout has it (JordanKaijuLayout.anim): its own sheet, with every point the fight reads (its
# seat, mouth, crown, hip, stomping foot) off that frame's contract anchors; or a stand-in posed in code. On the breath's
# charge stance its head is a layer of its own, turned by aim at its NECK, and its plates light over both.
#
# HIM ON ITS HEAD: while he rides it his own body sits his ride sheet's SEAT on its seat with his sprite hidden, and it
# draws him there, a copy of his sprite (before his ride sheets, the approved rider stand-in). His own sprite would
# y-sort at the seat, behind its body.
#
# THE X-RAY (JoshHand's): a mask of its own shape over it holds a copy of the player's sprite, and of his once he is off
# it, so wherever it covers them they show through at XRAY_ALPHA. Its walls keep the player out from behind it at home; away from home it
# is not solid, and this is what keeps them seen.

const Layout := preload("res://Scripts/JordanKaijuLayout.gd")
const JordanArtLayout := preload("res://Scripts/JordanArtLayout.gd")

const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
const XRAY_ALPHA := 0.8
const FLINCH_FLASH := Color(2.4, 2.4, 2.4)
const FLINCH_TIME := 0.15
const FLINCH_SHAKE := 6.0
const KEYLINE_WIDTH := 3.0
const SHADOW_RADII := Vector2(190, 50)
const SHADOW_ALPHA := 0.35
# The mouth's light is in front of everything it lights.
const FLARE_Z := 2
const FLASH_PERIOD := 0.12
const PLATE_GLOW_ALPHA := 0.55
const BEAM_MOUTH_FRAME_TIME := 0.05

# Set by the state machine before it is added.
var jordan: CharacterBody2D
var floor_layer: Node2D

var art: Node2D
var body_sprite: Sprite2D
var head_sprite: Sprite2D
var spines_sprite: Sprite2D
var plate_glow: Node2D
var rider_sheet: Sprite2D
var mask_draw: Node2D
var mask_sprite: Sprite2D
var ghosts: Array[Sprite2D] = []
# Him on the mat behind it the same way (his knock-off can land him by its kneel): his own sprite copied into the mask.
var jordan_ghosts: Array[Sprite2D] = []
var rider: Sprite2D
var flare: Node2D
var flare_sprite: Sprite2D
var shadow: Node2D
var shadow_sprite: Sprite2D
var walls: StaticBody2D

var current_anim := &""
var anim: Dictionary = {}
var anim_clock := 0.0
var anim_step := 0
var anim_next := &""
var anim_done := false
# A sheet is showing rather than the code-drawn kaiju, and whether its motion is the code's.
var sheet_drawn := false
var posed := true
# The head layer's sheet while it shows, {} otherwise.
var head_spec: Dictionary = {}

var lift := 0.0
# The head's aim in degrees, as asked: a drawn head snaps to its nearest frame.
var aim := 0.0
# 0 none, 1 to 7 rows lit from the tail to the neck, 8 all of them flashing.
var spines_lit := 0
var spines_clock := 0.0
# The mouth's light, 0 to 1, and whether the beam is pouring out of it.
var charge := 0.0
var firing := false
var fire_clock := 0.0
var shake_x := 0.0
# Its size over what its animation draws: the toy in his hands is smaller (JordanKaijuLayout.TOY_HELD_SCALE).
var art_scale := 1.0
var shadow_on := true
var flinch_tween: Tween
var player_sprite: Sprite2D
# A sheet's pixels, for what it covers: texture -> Image.
var images := {}

# The code-drawn kaiju's shapes, in px from its feet: [polygon, colour] drawn in order, the head's apart, and the plates
# as [polygon, row].
var parts: Array = []
var head_parts: Array = []
var plates: Array = []


func _init() -> void:
	_build_shapes()


func _ready() -> void:
	art = Node2D.new()
	art.name = "Art"
	add_child(art)
	art.draw.connect(_draw_art)
	body_sprite = _layer_sprite("Body")
	head_sprite = _layer_sprite("Head")
	spines_sprite = _layer_sprite("Spines")
	plate_glow = Node2D.new()
	plate_glow.name = "PlateGlow"
	plate_glow.material = _additive()
	art.add_child(plate_glow)
	plate_glow.draw.connect(_draw_plate_glow)
	mask_draw = Node2D.new()
	mask_draw.name = "XrayMask"
	mask_draw.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	art.add_child(mask_draw)
	mask_draw.draw.connect(_draw_mask)
	mask_sprite = _layer_sprite("XraySheetMask")
	mask_sprite.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	for mask: Node2D in [mask_draw, mask_sprite]:
		var ghost := Sprite2D.new()
		ghost.name = "XrayGhost"
		ghost.visible = false
		mask.add_child(ghost)
		ghosts.append(ghost)
		var his := Sprite2D.new()
		his.name = "XrayJordan"
		his.visible = false
		mask.add_child(his)
		jordan_ghosts.append(his)
	rider_sheet = _layer_sprite("RiderSheet")
	rider = Sprite2D.new()
	rider.name = "Rider"
	rider.visible = false
	add_child(rider)
	flare = Node2D.new()
	flare.name = "MouthFlare"
	flare.z_index = FLARE_Z
	add_child(flare)
	flare.draw.connect(_draw_flare)
	flare_sprite = Sprite2D.new()
	flare_sprite.name = "MouthFx"
	flare_sprite.scale = Vector2.ONE * Layout.SCALE
	flare_sprite.visible = false
	flare.add_child(flare_sprite)
	shadow = Node2D.new()
	shadow.name = "KaijuShadow"
	shadow.draw.connect(_draw_shadow)
	if floor_layer:
		floor_layer.add_child(shadow)
	var shadow_spec := Layout.fx(&"shadow")
	if not shadow_spec.is_empty():
		shadow_sprite = Sprite2D.new()
		shadow_sprite.texture = Layout.texture(shadow_spec.sheet)
		shadow_sprite.offset = shadow_spec.offset
		shadow_sprite.modulate.a = SHADOW_ALPHA
		shadow.add_child(shadow_sprite)
	_build_walls()
	play_anim(&"idle")


func _exit_tree() -> void:
	if is_instance_valid(shadow):
		shadow.queue_free()


func _layer_sprite(sprite_name: String) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.name = sprite_name
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.visible = false
	art.add_child(sprite)
	return sprite


static func _additive() -> CanvasItemMaterial:
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return additive


#WHERE IT IS

func place(feet: Vector2) -> void:
	global_position = feet.round()
	_follow()


# Lifted `px` off its feet, its art alone: its node and y-sort stay on the ground under it.
func set_lift(px: float) -> void:
	lift = px
	_apply_pose()


func aim_head(degrees: float) -> void:
	var was := drawn_aim()
	aim = clampf(degrees, Layout.BEAM_AIM_MIN, Layout.BEAM_AIM_MAX)
	if drawn_aim() != was:
		_show_layers()
		_redraw()


func light_spines(rows: int) -> void:
	if rows == spines_lit:
		return
	spines_lit = rows
	spines_clock = 0.0
	_show_layers()
	_redraw()


func set_charge(amount: float, pouring := false) -> void:
	charge = clampf(amount, 0.0, 1.0)
	if pouring != firing:
		firing = pouring
		fire_clock = 0.0
		_show_layers()
	flare.queue_redraw()


# The head as it is drawn: its nearest frame, or the roar's and the bow's own.
func drawn_aim() -> float:
	if current_anim == &"roar":
		return -40.0
	if current_anim in [&"bow", &"kneel", &"stand"] and not sheet_drawn:
		return 40.0
	return Layout.AIM_FRAMES[Layout.aim_frame(aim)]


# Whether the head turns as it aims: the code-drawn one does, and a drawn head layer; a sheet without one keeps its
# mouth where it is drawn.
func head_turns() -> bool:
	return not sheet_drawn or head_sprite.visible


func is_home() -> bool:
	return global_position.distance_to(Layout.HOME) < 1.0


func feet_point() -> Vector2:
	return global_position


func mouth_point() -> Vector2:
	if head_sprite.visible:
		var on_head: Dictionary = head_spec.anchors[head_sprite.frame]
		return art.to_global(head_sprite.position + (on_head.mouth - head_spec.pivot) * Layout.SCALE)
	if not sheet_drawn:
		return art.to_global(Layout.NECK + Vector2.from_angle(deg_to_rad(drawn_aim())) * Layout.MOUTH_REACH)
	return art.to_global(_anchor(&"mouth", Layout.MOUTH_OPEN if current_anim == &"charge" else Layout.MOUTH))


# Where the breath leaves its mouth for an aim, gliding with the aim rather than jumping from head frame to head frame:
# on the drawn head's arc about its NECK (the contract's mouths sit on it), on the code-drawn head's, or the drawn
# mouth itself on a sheet with no head of its own.
func breath_origin() -> Vector2:
	if head_sprite.visible:
		var level: Dictionary = head_spec.anchors[Layout.aim_frame(0.0)]
		var reach: Vector2 = ((level.mouth as Vector2) - (head_spec.pivot as Vector2)) * Layout.SCALE
		return art.to_global(head_sprite.position + reach.rotated(deg_to_rad(aim)))
	if not sheet_drawn:
		return art.to_global(Layout.NECK + Vector2.from_angle(deg_to_rad(aim)) * Layout.MOUTH_REACH)
	return mouth_point()


func seat_point() -> Vector2:
	return art.to_global(_seat_local())


func crown_point() -> Vector2:
	return art.to_global(_anchor(&"crown", Layout.CROWN))


# His crown while he rides it, as drawn.
func rider_crown_point() -> Vector2:
	if rider_sheet.visible:
		return art.to_global(_seat_local() + Layout.RIDER_CROWN - Layout.SEAT)
	return jordan.crown_point()


# The puff its grow, its shrink and the toy go with: its sheet on `point`, over the fighters, gone once played.
func puff_at(point: Vector2) -> void:
	var spec := Layout.fx(&"puff")
	if spec.is_empty() or get_parent() == null:
		return
	var puff := Sprite2D.new()
	puff.name = "KaijuPuff"
	puff.texture = Layout.texture(spec.sheet)
	puff.hframes = spec.count
	puff.offset = spec.offset
	puff.scale = Vector2.ONE * Layout.SCALE
	puff.z_index = FLARE_Z
	get_parent().add_child(puff)
	puff.global_position = point.round()
	var play := puff.create_tween()
	for i in range(1, spec.count):
		play.tween_interval(spec.times[i - 1])
		play.tween_callback(puff.set_frame.bind(i))
	play.tween_interval(spec.times[spec.count - 1])
	play.tween_callback(puff.queue_free)


func hip_point() -> Vector2:
	return art.to_global(_anchor(&"hip", Layout.HIP))


# The box in his raised hand as he rides: where his throws leave from. His ride sheets' release frame has his open palm.
func hand_point() -> Vector2:
	var hands := JordanArtLayout.anchors(&"ride_throw")
	if not rider_sheet.visible and is_instance_valid(jordan) and not hands.is_empty() and hands[2].has(&"hand"):
		return seat_point() + JordanArtLayout.frame_local(hands[2].hand) - JordanArtLayout.frame_local(hands[2].seat)
	return art.to_global(_seat_local() + Layout.RIDER_HAND - Layout.SEAT)


# From its feet to where its stomping foot comes down, across the ground: the stomp keeps that over its mark (the foot
# moves from frame to frame).
func foot_offset() -> Vector2:
	return Vector2(_anchor(&"foot_impact", Layout.FOOT_IMPACT).x, 0.0)


# Where a punched figure going off hurts him while he rides it: the front of its legs, wherever it stands.
func redirect_rect() -> Rect2:
	var box := Layout.LEG_BOX
	box.position += global_position - Layout.HOME
	return box


# Everything drawn of it, on screen.
func drawn_rect() -> Rect2:
	if sheet_drawn:
		return body_sprite.get_global_transform() * body_sprite.get_rect()
	var rect := Rect2()
	var first := true
	for polygon in silhouette():
		for point in polygon:
			if first:
				rect = Rect2(point, Vector2.ZERO)
				first = false
			else:
				rect = rect.expand(point)
	return rect


# The code-drawn kaiju's outline on screen, in pieces.
func silhouette() -> Array[PackedVector2Array]:
	var out: Array[PackedVector2Array] = []
	var to_screen := art.get_global_transform()
	for part in parts:
		out.append(to_screen * (part[0] as PackedVector2Array))
	for plate in plates:
		out.append(to_screen * (plate[0] as PackedVector2Array))
	var head := to_screen * Transform2D(deg_to_rad(drawn_aim()), Layout.NECK)
	for part in head_parts:
		out.append(head * (part[0] as PackedVector2Array))
	return out


# Whether a screen point is drawn over by it: its sheet's own pixels, or the code-drawn outline.
func covers(point: Vector2) -> bool:
	if sheet_drawn:
		return _sprite_covers(body_sprite, point) or (head_sprite.visible and _sprite_covers(head_sprite, point))
	for polygon in silhouette():
		if Geometry2D.is_point_in_polygon(point, polygon):
			return true
	return false


func _sprite_covers(sprite: Sprite2D, point: Vector2) -> bool:
	var image: Image = images.get(sprite.texture)
	if image == null:
		image = sprite.texture.get_image()
		images[sprite.texture] = image
	if image == null:
		return false
	var size := Vector2(image.get_width() / float(sprite.hframes), image.get_height())
	var texel := sprite.to_local(point) - sprite.offset + size / 2.0
	if texel.x < 0.0 or texel.y < 0.0 or texel.x >= size.x or texel.y >= size.y:
		return false
	return image.get_pixel(int(texel.x) + sprite.frame * int(size.x), int(texel.y)).a > 0.5


# A point on the frame showing, in px from its feet: off the frame's contract anchors, else `fallback`.
func _anchor(key: StringName, fallback: Vector2) -> Vector2:
	if sheet_drawn and anim.has("anchors") and not anim.anchors.is_empty():
		var frame_anchors: Dictionary = anim.anchors[mini(anim_step, anim.anchors.size() - 1)]
		if frame_anchors.has(key):
			return ((frame_anchors[key] as Vector2) - (anim.pivot as Vector2)) * Layout.SCALE
	return fallback


# The seat on the frame showing; on the charge stance it rides the head as it turns.
func _seat_local() -> Vector2:
	var seat := _anchor(&"rider_seat", Layout.SEAT)
	if head_sprite.visible:
		var now: Dictionary = head_spec.anchors[head_sprite.frame]
		var level: Dictionary = head_spec.anchors[Layout.aim_frame(0.0)]
		seat += ((now.seat_on_head as Vector2) - (level.seat_on_head as Vector2)) * Layout.SCALE
	return seat


#WHAT IT DOES

# `backwards` plays a sheet's frames last to first: the bow back up once he is on.
func play_anim(anim_name: StringName, next_anim: StringName = &"", backwards := false) -> void:
	current_anim = anim_name
	anim = Layout.anim(anim_name)
	if backwards and anim.has("frames") and not anim.get("posed", false):
		anim = anim.duplicate()
		for key in ["frames", "times", "anchors"]:
			var reversed: Array = (anim[key] as Array).duplicate()
			reversed.reverse()
			anim[key] = reversed
	anim_next = next_anim
	anim_clock = 0.0
	anim_step = 0
	anim_done = false
	sheet_drawn = anim.has("sheet")
	posed = anim.get("posed", false)
	body_sprite.visible = sheet_drawn
	if sheet_drawn:
		var sheet: Texture2D = Layout.texture(anim.sheet)
		for sprite: Sprite2D in [body_sprite, mask_sprite]:
			sprite.frame = 0
			sprite.texture = sheet
			sprite.hframes = roundi(sheet.get_width() / (anim.frame as Vector2).x)
			sprite.offset = anim.offset
			sprite.frame = anim.frames[0]
	_show_layers()
	_apply_pose()
	_redraw()


# A blast from a figure punched into its legs: a flash and a shudder, and whatever it is doing carries on. Standing idle
# it kicks its foot up (its hit sheet) and goes back to its idle; on a beat of an attack the beat goes on.
func flinch() -> void:
	if current_anim == &"idle":
		play_anim(&"hit", &"idle")
	if flinch_tween:
		flinch_tween.kill()
	art.modulate = FLINCH_FLASH
	flinch_tween = create_tween()
	flinch_tween.tween_property(art, "modulate", Color.WHITE, FLINCH_TIME)
	var shake := create_tween()
	for i in 4:
		shake.tween_property(self, "shake_x", FLINCH_SHAKE * (1.0 if i % 2 == 0 else -1.0), 0.025)
	shake.tween_property(self, "shake_x", 0.0, 0.025)


func set_walls(on: bool) -> void:
	for shape in walls.get_children():
		(shape as CollisionShape2D).set_deferred("disabled", not on)


# Its back wall stood back to `edge_x` (JordanRecoil's opening), or home again.
func open_back_wall(edge_x: float) -> void:
	_shape_wall(0, Rect2(Layout.WALLS[0].position, Vector2(edge_x - Layout.WALLS[0].position.x, Layout.WALLS[0].size.y)))


func close_back_wall() -> void:
	_shape_wall(0, Layout.WALLS[0])


func wall_rect(index: int) -> Rect2:
	var shape: CollisionShape2D = walls.get_child(index)
	var size: Vector2 = (shape.shape as RectangleShape2D).size
	return Rect2(shape.position - size / 2.0, size)


func _shape_wall(index: int, rect: Rect2) -> void:
	var shape: CollisionShape2D = walls.get_child(index)
	(shape.shape as RectangleShape2D).size = rect.size
	shape.position = rect.get_center()


func walls_up() -> bool:
	for shape in walls.get_children():
		if (shape as CollisionShape2D).disabled:
			return false
	return true


# The boss bar fades while its crown, or his, is under it.
func update_hud_fade() -> void:
	if not is_instance_valid(jordan):
		return
	var points: Array[Vector2] = [crown_point()]
	if jordan.mounted:
		points.append(rider_crown_point())
	elif jordan.sprite.visible:
		points.append(jordan.crown_point())
	jordan.update_hud_fade(points)


#STEPPING

func _process(delta: float) -> void:
	_step_anim(delta)
	if spines_lit == 8:
		spines_clock += delta
		if int(spines_clock / FLASH_PERIOD) != int((spines_clock - delta) / FLASH_PERIOD):
			_redraw()
	if firing:
		fire_clock += delta
	_apply_pose()
	_follow()
	_copy_player()
	_step_flare()


func _physics_process(_delta: float) -> void:
	_follow()
	update_hud_fade()


func _step_anim(delta: float) -> void:
	if anim.is_empty() or anim_done:
		return
	anim_clock += delta
	if posed:
		if not anim.loop and anim_clock >= anim.time:
			_end_anim()
		return
	var times: Array = anim.times
	while anim_clock >= times[mini(anim_step, times.size() - 1)]:
		anim_clock -= times[mini(anim_step, times.size() - 1)]
		if anim_step < anim.frames.size() - 1:
			anim_step += 1
		elif anim.loop:
			anim_step = 0
		else:
			_end_anim()
			return
		body_sprite.frame = anim.frames[anim_step]
		mask_sprite.frame = body_sprite.frame
		if spines_sprite.visible and current_anim == &"roar":
			spines_sprite.frame = body_sprite.frame
		# A last frame the contract holds (stumble's, which is the kneel's first) hands over as it is reached.
		if anim_next != &"" and not anim.loop and anim_step == anim.frames.size() - 1 and times[mini(anim_step, times.size() - 1)] >= Layout.Sheets.HOLD:
			_end_anim()
			return


func _end_anim() -> void:
	anim_done = true
	if anim_next != &"":
		play_anim(anim_next)


# His body on its seat while he rides, and him drawn there.
func _follow() -> void:
	var riding: bool = is_instance_valid(jordan) and jordan.mounted
	# His own ride sheets once they are in; the approved stand-in before them.
	var standin := Layout.rider_standin() if JordanArtLayout.anchors(&"ride_idle").is_empty() else ""
	rider_sheet.visible = riding and standin != ""
	rider.visible = riding and standin == ""
	if not riding:
		return
	jordan.global_position = (seat_point() - jordan.seat_local()).round()
	if rider_sheet.visible:
		if rider_sheet.texture == null:
			rider_sheet.texture = Layout.texture(standin)
			rider_sheet.hframes = Layout.STANDIN.count
			rider_sheet.offset = (Layout.STANDIN.frame as Vector2) / 2.0 - (Layout.STANDIN.pivot as Vector2)
		rider_sheet.frame = Layout.STANDIN_CHARGE if current_anim == &"charge" else Layout.STANDIN_IDLE
		rider_sheet.position = _seat_local() - Layout.SEAT
		rider_sheet.modulate = jordan.sprite.modulate
		return
	var source: Sprite2D = jordan.sprite
	if rider.texture != source.texture or rider.hframes != source.hframes:
		rider.frame = 0
		rider.texture = source.texture
		rider.hframes = source.hframes
		rider.vframes = source.vframes
	rider.frame = source.frame
	rider.offset = source.offset
	rider.flip_h = source.flip_h
	rider.modulate = source.modulate
	rider.self_modulate = source.self_modulate
	rider.global_transform = source.global_transform


func _copy_player() -> void:
	var player := _player_sprite()
	var him: Sprite2D = jordan.sprite if is_instance_valid(jordan) and not jordan.mounted else null
	for i in ghosts.size():
		_copy_ghost(ghosts[i], player)
		_copy_ghost(jordan_ghosts[i], him)


func _copy_ghost(ghost: Sprite2D, source: Sprite2D) -> void:
	var live: bool = source != null and source.is_visible_in_tree() and ghost.get_parent().visible
	ghost.visible = live
	if not live:
		return
	if ghost.texture != source.texture or ghost.hframes != source.hframes or ghost.vframes != source.vframes:
		ghost.frame = 0
		ghost.texture = source.texture
		ghost.hframes = source.hframes
		ghost.vframes = source.vframes
	ghost.frame = source.frame
	ghost.flip_h = source.flip_h
	ghost.offset = source.offset
	ghost.centered = source.centered
	ghost.global_transform = source.global_transform
	var tint := source.modulate
	ghost.modulate = Color(tint.r, tint.g, tint.b, tint.a * XRAY_ALPHA)


func _player_sprite() -> Sprite2D:
	if not is_instance_valid(player_sprite):
		var scene := get_tree().current_scene
		var player: Node = scene.get_node_or_null(PLAYER_PATH) if scene else null
		player_sprite = player.sprite if player != null and "sprite" in player else null
	return player_sprite


# The layers over the charge stance, its own sheets only: its head at its NECK on the frame its aim is nearest, the
# breath's jaws once it fires, and its plates lit over both.
func _show_layers() -> void:
	mask_draw.visible = not sheet_drawn
	mask_sprite.visible = sheet_drawn
	var charging := sheet_drawn and not posed and current_anim == &"charge"
	head_spec = Layout.sheet(&"head_fire" if firing else &"head_aim", Layout.USE_FINAL_HEAD) if charging else {}
	head_sprite.visible = not head_spec.is_empty()
	if head_sprite.visible:
		var head: Texture2D = Layout.texture(head_spec.sheet)
		if head_sprite.texture != head:
			head_sprite.frame = 0
			head_sprite.texture = head
			head_sprite.hframes = head_spec.count
			head_sprite.offset = head_spec.offset
		head_sprite.position = _anchor(&"neck", Layout.NECK)
		head_sprite.frame = Layout.aim_frame(aim)
	var spines := Layout.sheet(&"spines", Layout.USE_FINAL_SPINES) if charging else {}
	var roaring := sheet_drawn and not posed and current_anim == &"roar" and spines_lit == 8
	if roaring:
		spines = Layout.sheet(&"roar_spines", Layout.USE_FINAL_ROAR_SPINES)
	spines_sprite.visible = not spines.is_empty()
	if spines_sprite.visible:
		var plates_sheet: Texture2D = Layout.texture(spines.sheet)
		if spines_sprite.texture != plates_sheet:
			spines_sprite.frame = 0
			spines_sprite.texture = plates_sheet
			spines_sprite.hframes = spines.count
			spines_sprite.offset = spines.offset
		spines_sprite.frame = body_sprite.frame if roaring else clampi(spines_lit, 0, spines.count - 1)
	plate_glow.visible = sheet_drawn and not spines_sprite.visible and current_anim in [&"charge", &"roar"]


# The pose for the animation showing where its motion is the code's, and its lift, on the art.
func _apply_pose() -> void:
	var pose := _pose(current_anim, anim_clock) if posed else [Vector2.ONE, 0.0]
	art.scale = (pose[0] as Vector2) * art_scale
	art.rotation = pose[1]
	art.position = Vector2(roundf(shake_x), -roundf(lift))
	if head_sprite.visible:
		head_sprite.position = _anchor(&"neck", Layout.NECK)
	# Up in the air its stomp's mark is its shadow.
	shadow.visible = visible and shadow_on and lift <= 0.0
	if shadow.is_inside_tree():
		shadow.global_position = global_position.round()
		if shadow_sprite != null:
			shadow_sprite.scale = Vector2.ONE * Layout.SCALE * _body_size()
		else:
			shadow.queue_redraw()


# How big it is drawn, for its shadow: the grow's and the shrink's sheets bake their sizes in, and the toy is the first.
func _body_size() -> float:
	if posed:
		return absf(art.scale.y)
	match current_anim:
		&"grow":
			return Layout.GROW_STEPS[mini(anim_step, Layout.GROW_STEPS.size() - 1)]
		&"shrink":
			return Layout.SHRINK_STEPS[mini(anim_step, Layout.SHRINK_STEPS.size() - 1)]
		&"toy":
			return Layout.GROW_STEPS[0]
	return 1.0


# [scale, rotation] for a posed animation `t` seconds in.
func _pose(anim_name: StringName, t: float) -> Array:
	var length: float = anim.get("time", 1.0)
	var p := clampf(t / maxf(length, 0.001), 0.0, 1.0)
	var eased := 1.0 - (1.0 - p) * (1.0 - p)
	match anim_name:
		&"idle":
			return [Vector2(1.0, 1.0 + 0.012 * sin(TAU * t / 0.96)), 0.0]
		&"charge":
			return [Vector2(1.01, 1.0 - 0.012 * absf(sin(TAU * t / 0.4))), 0.0]
		&"rear":
			return [Vector2(1.0 + 0.06 * eased, 1.0 - 0.1 * eased), -0.08 * eased]
		&"leap":
			return [Vector2(0.92, 1.1), 0.0]
		&"drop":
			return [Vector2(0.94, 1.08), 0.04]
		&"stomp", &"land":
			return [Vector2(1.14, 0.84).lerp(Vector2.ONE, p), 0.0]
		&"stumble":
			return [Vector2(1.0, 1.0 - 0.16 * eased), 0.2 * eased]
		&"kneel":
			return [Vector2(1.02, 0.84 + 0.01 * sin(TAU * t / 0.6)), 0.2]
		&"stand":
			return [Vector2(1.02 - 0.02 * p, 0.84 + 0.16 * p), 0.2 * (1.0 - p)]
		&"grow":
			var steps: Array = Layout.GROW_STEPS
			return [Vector2.ONE * float(steps[mini(int(t / 0.12), steps.size() - 1)]), 0.0]
		&"shrink":
			var steps: Array = Layout.SHRINK_STEPS
			return [Vector2.ONE * float(steps[mini(int(t / 0.11), steps.size() - 1)]), 0.0]
		&"toy":
			return [Vector2.ONE * Layout.TOY_SCALE, 0.0]
		&"roar":
			return [Vector2(1.02, 1.04 + 0.015 * sin(t * 40.0)), -0.05]
		&"bow":
			return [Vector2(1.0, 1.0 - 0.06 * eased), 0.1 * eased]
		&"hit":
			return [Vector2(1.04, 0.96).lerp(Vector2.ONE, p), 0.0]
		&"tail_windup":
			return [Vector2(0.97, 1.0), -0.1 * eased]
		&"tail_spin":
			return [Vector2(cos(TAU * p), 1.0), 0.0]
		&"collapse":
			return [Vector2(1.0 + 0.05 * eased, 1.0 - 0.25 * eased), -0.32 * eased]
		&"down":
			return [Vector2(1.05, 0.75 + 0.01 * sin(TAU * t / 0.6)), -0.32]
	return [Vector2.ONE, 0.0]


func _redraw() -> void:
	art.queue_redraw()
	mask_draw.queue_redraw()
	plate_glow.queue_redraw()
	flare.queue_redraw()


# Its drawn mouth light while it gathers, its drawn breath at the mouth while it pours, or the code's circles.
func _step_flare() -> void:
	var spec := {}
	var frame := 0
	if firing:
		spec = Layout.fx(&"beam_mouth")
		if not spec.is_empty():
			frame = int(fire_clock / BEAM_MOUTH_FRAME_TIME) % spec.count
	elif charge > 0.0:
		spec = Layout.fx(&"mouth_charge")
		if not spec.is_empty():
			frame = mini(int(charge * spec.count), spec.count - 1)
	flare_sprite.visible = not spec.is_empty()
	if flare_sprite.visible:
		var sheet: Texture2D = Layout.texture(spec.sheet)
		if flare_sprite.texture != sheet:
			flare_sprite.frame = 0
			flare_sprite.texture = sheet
			flare_sprite.hframes = spec.count
			flare_sprite.offset = spec.offset
			flare_sprite.material = _additive() if not firing else null
		flare_sprite.frame = frame
		flare_sprite.global_position = (breath_origin() if firing else mouth_point()).round()
	if firing or charge > 0.0:
		flare.queue_redraw()


#THE CODE-DRAWN KAIJU

func _draw_art() -> void:
	if sheet_drawn:
		return
	for plate in plates:
		art.draw_colored_polygon(plate[0], _plate_colour(plate[1]))
		_keyline(plate[0])
	for part in parts:
		art.draw_colored_polygon(part[0], part[1])
		_keyline(part[0])
	art.draw_set_transform(Layout.NECK, deg_to_rad(drawn_aim()))
	for part in head_parts:
		art.draw_colored_polygon(part[0], part[1])
		_keyline(part[0])
	var eye := Vector2(60, -80)
	art.draw_circle(eye, 8.0, Layout.EYE)
	art.draw_circle(eye + Vector2(2, 0), 3.0, Layout.KEYLINE)
	if charge > 0.0:
		art.draw_line(Vector2(20, 2), Vector2(Layout.MOUTH_REACH, 2), Layout.BEAM_EDGE.lerp(Layout.BEAM_CORE, charge), 6.0)
	art.draw_set_transform(Vector2.ZERO, 0.0)


func _draw_mask() -> void:
	if sheet_drawn:
		return
	for plate in plates:
		mask_draw.draw_colored_polygon(plate[0], Color.WHITE)
	for part in parts:
		mask_draw.draw_colored_polygon(part[0], Color.WHITE)
	mask_draw.draw_set_transform(Layout.NECK, deg_to_rad(drawn_aim()))
	for part in head_parts:
		mask_draw.draw_colored_polygon(part[0], Color.WHITE)
	mask_draw.draw_set_transform(Vector2.ZERO, 0.0)


# Over a sheet with no plate layer of its own: each lit row glows on its plates.
func _draw_plate_glow() -> void:
	if spines_lit <= 0:
		return
	for r in Layout.PLATE_ROWS.size():
		var row: Array = Layout.PLATE_ROWS[r]
		var lit := spines_lit == 8 or r + 1 <= spines_lit
		if not lit:
			continue
		var colour := _plate_colour(r + 1)
		var at: Vector2 = row[0] + (row[1] as Vector2).normalized() * float(row[2]) * 0.4
		plate_glow.draw_circle(at, float(row[2]) * 0.8, Color(colour, PLATE_GLOW_ALPHA * 0.5))
		plate_glow.draw_circle(at, float(row[2]) * 0.45, Color(colour, PLATE_GLOW_ALPHA))


func _keyline(polygon: PackedVector2Array) -> void:
	var closed := polygon.duplicate()
	closed.append(polygon[0])
	art.draw_polyline(closed, Layout.KEYLINE, KEYLINE_WIDTH)


func _plate_colour(row: int) -> Color:
	if spines_lit == 8:
		return Layout.PLATE_FLASH if int(spines_clock / FLASH_PERIOD) % 2 == 0 else Layout.PLATE_LIT
	return Layout.PLATE_LIT if row <= spines_lit else Layout.PLATE


func _draw_flare() -> void:
	if flare_sprite.visible or (charge <= 0.0 and not firing):
		return
	var at := flare.to_local(breath_origin() if firing else mouth_point())
	var radius := 8.0 + 26.0 * charge
	if firing:
		radius = 40.0 + 6.0 * sin(fire_clock * 33.0)
	flare.draw_circle(at, radius * 1.5, Color(Layout.BEAM_EDGE, 0.35))
	flare.draw_circle(at, radius, Color(Layout.BEAM_CORE, 0.9))


func _draw_shadow() -> void:
	if shadow_sprite != null:
		return
	var shrink := 1.0 - clampf(lift / 900.0, 0.0, 0.6)
	var radii := SHADOW_RADII * shrink * _body_size()
	if radii.x < 1.0:
		return
	var points := PackedVector2Array()
	for i in 24:
		var a := TAU * i / 24.0
		points.append(Vector2(cos(a) * radii.x, sin(a) * radii.y))
	shadow.draw_colored_polygon(points, Color(0, 0, 0, SHADOW_ALPHA))


# The approved sprite's outline in pieces, drawn back to front, then the head about NECK aimed level; the plates on
# PLATE_ROWS, three to a row, drawn behind the body.
func _build_shapes() -> void:
	parts = [
		[_poly([Vector2(-120, -32), Vector2(10, -32), Vector2(15, -2), Vector2(-125, -2)]), Layout.HIDE_DARK],
		[_poly([Vector2(-150, -170), Vector2(-232, -60), Vector2(-205, 30), Vector2(-120, 62), Vector2(20, 58), Vector2(20, 36), Vector2(-110, 30), Vector2(-165, -10), Vector2(-90, -120)]), Layout.HIDE],
		[_ellipse(Vector2(-70, -130), Vector2(125, 110), 0.0), Layout.HIDE_DARK],
		[_ellipse(Vector2(-10, -260), Vector2(170, 200), -0.25), Layout.HIDE],
		[_ellipse(Vector2(110, -200), Vector2(55, 140), -0.2), Layout.BELLY],
		[_poly([Vector2(40, -400), Vector2(150, -470), Vector2(215, -445), Vector2(205, -330), Vector2(120, -300)]), Layout.HIDE],
		[_ellipse(Vector2(110, -140), Vector2(80, 80), 0.0), Layout.HIDE],
		[_poly([Vector2(70, -140), Vector2(160, -140), Vector2(165, -30), Vector2(70, -30)]), Layout.HIDE],
		[_poly([Vector2(60, -32), Vector2(222, -32), Vector2(225, -2), Vector2(55, -2)]), Layout.HIDE],
		[_poly([Vector2(120, -340), Vector2(240, -345), Vector2(270, -325), Vector2(255, -300), Vector2(130, -290)]), Layout.HIDE],
	]
	head_parts = [
		[_poly([Vector2(-45, -80), Vector2(20, -117), Vector2(80, -105), Vector2(112, -55), Vector2(114, -4), Vector2(60, 0), Vector2(-20, 8), Vector2(-50, -10)]), Layout.HIDE],
		[_poly([Vector2(-10, 6), Vector2(110, 4), Vector2(100, 32), Vector2(30, 45), Vector2(-10, 35)]), Layout.HIDE_DARK],
	]
	plates = []
	for r in Layout.PLATE_ROWS.size():
		var row: Array = Layout.PLATE_ROWS[r]
		var at: Vector2 = row[0]
		var out: Vector2 = (row[1] as Vector2).normalized()
		var size: float = row[2]
		var along := out.orthogonal()
		for column in [-1, 0, 1]:
			var s: float = size * (1.0 if column == 0 else 0.7)
			var base: Vector2 = at + along * column * size * 0.55
			plates.append([_poly([base - along * s * 0.4, base + out * s, base + along * s * 0.4]), r + 1])


static func _poly(points: Array) -> PackedVector2Array:
	return PackedVector2Array(points)


static func _ellipse(centre: Vector2, radii: Vector2, turn: float) -> PackedVector2Array:
	var points := PackedVector2Array()
	for i in 28:
		var a := TAU * i / 28.0
		points.append(centre + Vector2(cos(a) * radii.x, sin(a) * radii.y).rotated(turn))
	return points


func _build_walls() -> void:
	walls = StaticBody2D.new()
	walls.name = "HomeWalls"
	walls.top_level = true
	walls.collision_layer = 1
	walls.collision_mask = 0
	add_child(walls)
	walls.global_position = Vector2.ZERO
	for wall in Layout.WALLS:
		var shape := CollisionShape2D.new()
		var rect := RectangleShape2D.new()
		rect.size = wall.size
		shape.shape = rect
		shape.position = wall.get_center()
		shape.disabled = true
		walls.add_child(shape)
