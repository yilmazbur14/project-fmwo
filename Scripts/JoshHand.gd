extends Node2D

# One of Josh's two card hands in his own fight (JoshHandsRig builds the pair): a persistent actor, never a hazard and
# never hittable. Whoever moves it places it one of three ways; it knows nothing of the fight:
#   REST    at its portal, on the backdrop's y-sort point (JoshHandsLayout.HAND_REST_SORT_Y), drawn at its rest point
#   AIR     over the floor point it would come down on, `height` px up, drawn over the ropes (HAND_AIR_Z), its box kept
#           on screen: its lift clamped at the back rope and leaned in off a side rope (JoshHandsLayout.max_lift, lean)
#   GROUND  flat on its floor point, y-sorted there with everyone, so a player standing in front is drawn in front
# Its Draw child is the pivot, mirrored for the left hand, and everything drawn is on whole px. Its clips step on its
# own physics clock, so a pause or a freeze holds them.
#
# The drawn one (once all six clips are in and imported, JoshHandsLayout.final_hand), with each clip's additive glow
# layer over it in step where that is in; or until then the placeholder: a glove of cards whose clips are transforms
# of it, with the fan of cards for form and shatter.
#
# THE X-RAY: in the air and on the floor, a mask of the hand's own shape over it holds a copy of the player's sprite,
# so wherever the hand covers the player they show through it at XRAY_ALPHA; everywhere else the hand is solid.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")

const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"

enum Mode { HIDDEN, REST, AIR, GROUND }

var side := &"right"
var mode := Mode.HIDDEN
var floor_at := Vector2.ZERO
var height := 0.0
var clip := &""
# Set while JoshCardsHandSlam drives it: the rig leaves it alone.
var driven := false
# Dissolved into its portal at his Break (JoshHandsRig.retract), until it forms again.
var retracted := false
var drawn := false
var art: Node2D
var sprite: Sprite2D
var glow_sprite: Sprite2D
var look: Node2D
var fan: Sprite2D
# The x-ray's mask (a copy of the hand's shape, clipping its children to it) and the copy of the player in it.
var xray_mask: CanvasItem
var xray_ghost: Sprite2D
var player_sprite: Sprite2D
# How far it is leaned in off a side rope, px, and how much of that lean it takes, as last placed.
var lean_px := 0.0
var leaning := 1.0
# A finger gun (JoshGunHands): its box is the gun's, and until the gun art is in (gun_drawn) its clips stand in off
# the hand's own, turned a quarter to point into the ring (gun_turn, degrees) and kicking back as they fire (recoil,
# px).
var gun := false
var gun_drawn := false
var gun_turn := 0.0
var recoil := 0.0
# Seconds into the clip, never wrapped: a stand-in times its own frames off it.
var elapsed := 0.0
# The clip playing: its speed, whether backwards, what follows it, and how far into it in the clip's own seconds.
var speed := 1.0
var reverse := false
var then := &""
var into := 0.0
var done := false
var frame_index := 0


static func make(hand_side: StringName) -> Node2D:
	var hand = new()
	hand.side = hand_side
	hand.name = "JoshHand_%s" % hand_side
	return hand


func _ready() -> void:
	art = Node2D.new()
	art.name = "Draw"
	art.scale = Vector2(-1.0 if side == &"left" else 1.0, 1.0)
	add_child(art)
	drawn = Layout.final_hand()
	gun_drawn = drawn and Layout.final_gun()
	if drawn:
		_build_drawn()
	else:
		_build_placeholder()
	hide_hand()


#WHERE IT IS

func place_rest(point: Vector2) -> void:
	mode = Mode.REST
	floor_at = point
	height = 0.0
	lean_px = 0.0
	visible = true
	z_index = 0
	global_position = Vector2(roundf(point.x), Layout.HAND_REST_SORT_Y)
	art.position = Vector2(0.0, roundf(point.y) - Layout.HAND_REST_SORT_Y)
	_show_xray(false)


# `lift` px over `at`, as far as its box stays on screen: `height` is what it got. `lean_weight` is how much of the
# lean off a side rope it takes, which a drop fades out so it lands on its floor point.
func place_air(at: Vector2, lift: float, lean_weight := 1.0) -> void:
	mode = Mode.AIR
	floor_at = at
	height = minf(lift, Layout.max_lift(at.y))
	leaning = lean_weight
	lean_px = Layout.lean_in(_box(), at.x) * leaning
	visible = true
	z_index = Layout.HAND_AIR_Z
	global_position = at.round()
	art.position = Vector2(roundf(lean_px + _kick()), -roundf(height))
	_show_xray(true)


func place_ground(at: Vector2) -> void:
	mode = Mode.GROUND
	floor_at = at
	height = 0.0
	lean_px = 0.0
	visible = true
	z_index = 0
	global_position = at.round()
	art.position = Vector2.ZERO
	_show_xray(true)


func hide_hand() -> void:
	mode = Mode.HIDDEN
	visible = false
	_show_xray(false)


# The pivot as drawn.
func drawn_point() -> Vector2:
	return art.global_position


# What an air frame covers, round the pivot as drawn: the gun's box, as a gun (_box).
func drawn_rect() -> Rect2:
	var box := _box()
	return Rect2(drawn_point() + box.position, box.size)


# On as it leaves for its post, off as it lands home: the stand-ins' turn and kick with it.
func set_gun(on: bool) -> void:
	gun = on
	if clip != &"":
		_show()


# The muzzle on its Draw node, px: where the flash and the charge are put, so they follow its kick.
func muzzle_local() -> Vector2:
	return (Layout.GUN_MUZZLE - Layout.HAND.pivot) * Layout.SCALE


# The stand-in fire's kick, out of the ring: to the right for the right hand, which points left.
func _kick() -> float:
	return recoil if side == &"right" else -recoil


# The box its frames stay inside, round the pivot: the air box, or as a gun playing a gun clip the gun's - while
# gun_form plays, forwards or backwards, the box of the frame it is on. The hover that ends its flight home is a hand
# again.
func _box() -> Rect2:
	if not gun or not Layout.GUN_CLIPS.has(clip):
		return Layout.air_box(side)
	if clip == &"gun_form":
		return Layout.gun_form_box(side, _form_frame())
	return Layout.gun_box(side)


# gun_form's own frame now, whatever sheet stands in for it.
func _form_frame() -> int:
	var times: Array = Layout.GUN_CLIPS[&"gun_form"].times
	var index := times.size() - 1
	var end := 0.0
	for i in times.size():
		end += float(times[i])
		if into < end:
			index = i
			break
	return times.size() - 1 - index if reverse else index


# The clip whose frames are drawn: a gun clip's own once the gun art is in, and what stands in for it until then.
func _sheet_clip(clip_name: StringName) -> StringName:
	if Layout.GUN_CLIPS.has(clip_name) and not gun_drawn:
		return Layout.GUN_CLIPS[clip_name].stand_in
	return clip_name


# The stand-ins' quarter turn and kick: turning over gun_form (back again played backwards), turned through the other
# gun clips, and kicking back at the start of gun_fire. The gun art draws its own.
func _pose_gun() -> void:
	gun_turn = 0.0
	recoil = 0.0
	if not gun or gun_drawn or not Layout.GUN_CLIPS.has(clip):
		return
	var p := clampf(into / Layout.clip_time(clip), 0.0, 1.0)
	if reverse:
		p = 1.0 - p
	gun_turn = Layout.GUN_TURN * (p if clip == &"gun_form" else 1.0)
	if clip == &"gun_fire":
		recoil = Layout.GUN_RECOIL * (1.0 - p)


#ITS CLIPS

# `clip_name` from its first frame at `at_speed`, backwards if asked, and `next` once it ends if it doesn't loop. The
# seconds it takes: one round of a loop.
func play(clip_name: StringName, at_speed := 1.0, backwards := false, next := &"") -> float:
	clip = clip_name
	speed = at_speed
	reverse = backwards
	then = next
	into = 0.0
	elapsed = 0.0
	done = false
	if drawn:
		var sheet := _sheet_clip(clip_name)
		var frames: int = Layout.clip_spec(sheet).times.size()
		sprite.frame = 0
		sprite.texture = load(Layout.hand_sheet(sheet))
		sprite.hframes = frames
		xray_mask.frame = 0
		xray_mask.texture = sprite.texture
		xray_mask.hframes = frames
		var glow_sheet := Layout.hand_glow_sheet(sheet)
		glow_sprite.visible = ResourceLoader.exists(glow_sheet)
		if glow_sprite.visible:
			glow_sprite.frame = 0
			glow_sprite.texture = load(glow_sheet)
			glow_sprite.hframes = frames
	_show()
	return Layout.clip_time(clip_name) / speed


# A clip, or an optional one or its stand-in (JoshHandsLayout.motion), played to last `seconds`.
func play_motion(motion_name: StringName, seconds: float, next := &"") -> float:
	var plays: Dictionary = Layout.motion(motion_name, drawn)
	play(plays.clip, Layout.clip_time(plays.clip) / maxf(seconds, 0.001), plays.reverse, next)
	return seconds


func clip_done() -> bool:
	return done


# Seconds left of a clip that ends; 0 for a loop, or one that has.
func clip_left() -> float:
	if clip == &"" or done or Layout.clip_spec(clip).loop:
		return 0.0
	return maxf(Layout.clip_time(clip) - into, 0.0) / speed


func _physics_process(delta: float) -> void:
	if clip == &"" or done:
		return
	var total := Layout.clip_time(clip)
	into += delta * speed
	elapsed += delta * speed
	if into >= total:
		if Layout.clip_spec(clip).loop:
			into = fposmod(into, total)
		else:
			into = total
			done = true
	_show()
	if done and then != &"":
		play(then)


func _show() -> void:
	var sheet := _sheet_clip(clip)
	var times: Array = Layout.clip_spec(sheet).times
	var index := times.size() - 1
	var end := 0.0
	var at := _sheet_time(sheet)
	for i in times.size():
		end += float(times[i])
		if at < end:
			index = i
			break
	frame_index = times.size() - 1 - index if reverse else index
	_pose_gun()
	if drawn:
		sprite.frame = frame_index
		xray_mask.frame = frame_index
		if glow_sprite.visible:
			glow_sprite.frame = frame_index
		for part: Node2D in [sprite, glow_sprite, xray_mask]:
			part.rotation = deg_to_rad(gun_turn)
	else:
		_pose_placeholder()
	# Its clip can step onto a frame of another box after it was placed this step (gun_form's), so the lean follows.
	if mode == Mode.AIR:
		lean_px = Layout.lean_in(_box(), floor_at.x) * leaning
		art.position.x = roundf(lean_px + _kick())


# How far into `sheet`'s own frames it is: the clip's time, or for a stand-in its own looped or held time.
func _sheet_time(sheet: StringName) -> float:
	if sheet == clip:
		return into
	var total := Layout.clip_time(sheet)
	return fposmod(elapsed, total) if Layout.clip_spec(sheet).loop else minf(elapsed, total)


#THE X-RAY

func _show_xray(on: bool) -> void:
	xray_mask.visible = on


# The player's sprite as it is drawn this frame, copied into the mask: only where the hand's own pixels are does it
# show, over the hand.
func _process(_delta: float) -> void:
	if not visible or not xray_mask.visible:
		return
	var source := _player_sprite()
	xray_ghost.visible = source != null and source.is_visible_in_tree()
	if not xray_ghost.visible:
		return
	if xray_ghost.texture != source.texture or xray_ghost.hframes != source.hframes or xray_ghost.vframes != source.vframes:
		xray_ghost.frame = 0
		xray_ghost.texture = source.texture
		xray_ghost.hframes = source.hframes
		xray_ghost.vframes = source.vframes
	xray_ghost.frame = source.frame
	xray_ghost.flip_h = source.flip_h
	xray_ghost.flip_v = source.flip_v
	xray_ghost.offset = source.offset
	xray_ghost.centered = source.centered
	xray_ghost.global_transform = source.global_transform
	var tint := source.modulate
	xray_ghost.modulate = Color(tint.r, tint.g, tint.b, tint.a * Layout.XRAY_ALPHA)


func _player_sprite() -> Sprite2D:
	if not is_instance_valid(player_sprite):
		var scene := get_tree().current_scene
		var player: Node = scene.get_node_or_null(PLAYER_PATH) if scene else null
		player_sprite = player.sprite if player != null and "sprite" in player else null
	return player_sprite


func _add_xray(mask: CanvasItem) -> void:
	xray_mask = mask
	xray_mask.name = "XrayMask"
	xray_mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	xray_mask.visible = false
	xray_ghost = Sprite2D.new()
	xray_ghost.name = "XrayGhost"
	xray_mask.add_child(xray_ghost)


#WHAT IS DRAWN

func _build_drawn() -> void:
	var spec: Dictionary = Layout.HAND
	sprite = Sprite2D.new()
	sprite.name = "Hand"
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.offset = spec.frame / 2.0 - spec.pivot
	art.add_child(sprite)
	glow_sprite = Sprite2D.new()
	glow_sprite.name = "Glow"
	glow_sprite.scale = sprite.scale
	glow_sprite.offset = sprite.offset
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow_sprite.material = added
	glow_sprite.visible = false
	art.add_child(glow_sprite)
	var mask := Sprite2D.new()
	mask.scale = sprite.scale
	mask.offset = sprite.offset
	art.add_child(mask)
	_add_xray(mask)


func _build_placeholder() -> void:
	var colours: Dictionary = Layout.PLACEHOLDER
	var spec: Dictionary = Layout.PLACEHOLDER_LOOK
	look = Node2D.new()
	look.name = "Look"
	art.add_child(look)
	var outline := PackedVector2Array()
	for texel in Layout.PLACEHOLDER_HAND:
		outline.append(texel * Layout.SCALE)
	var glove := Polygon2D.new()
	glove.name = "Glove"
	glove.polygon = outline
	glove.color = colours.card
	look.add_child(glove)
	var rim := Line2D.new()
	rim.name = "Rim"
	rim.points = outline
	rim.closed = true
	rim.width = spec.rim_width * Layout.SCALE
	rim.default_color = colours.edge
	look.add_child(rim)
	var r: float = spec.pip_radius * Layout.SCALE
	for texel in Layout.PLACEHOLDER_PIPS:
		var pip := Polygon2D.new()
		pip.polygon = PackedVector2Array([Vector2(0, -r), Vector2(r, 0), Vector2(0, r), Vector2(-r, 0)])
		pip.position = texel * Layout.SCALE
		pip.color = colours.pip
		look.add_child(pip)
	var mask := Polygon2D.new()
	mask.polygon = outline
	look.add_child(mask)
	_add_xray(mask)
	var burst: Dictionary = JoshArtLayout.FINAL_CARD_BURST
	fan = Sprite2D.new()
	fan.name = "Fan"
	fan.texture = load(burst.texture)
	fan.hframes = burst.hframes
	fan.scale = Vector2.ONE * burst.scale
	fan.offset = burst.frame_size / 2.0 - burst.pivot
	fan.visible = false
	art.add_child(fan)


# The clips as transforms of the glove, about its pivot: form grows it in out of the fan of cards, hover bobs it,
# windup swells it, drop squashes it as it falls and impact lies it flat; shatter is the fan alone. A gun clip is its
# stand-in's, turned (_pose_gun).
func _pose_placeholder() -> void:
	var spec: Dictionary = Layout.PLACEHOLDER_LOOK
	var shown := _sheet_clip(clip)
	var total := Layout.clip_time(shown)
	var p := clampf(_sheet_time(shown) / total, 0.0, 1.0) if total > 0.0 else 1.0
	if reverse:
		p = 1.0 - p
	var squash := Vector2.ONE
	var bob := 0.0
	var alpha := 1.0
	look.rotation = deg_to_rad(gun_turn)
	match shown:
		&"form":
			squash = Vector2.ONE * lerpf(spec.form_from, 1.0, p)
			alpha = p
		&"hover":
			bob = roundf(spec.bob * (0.5 + 0.5 * sin(TAU * p)))
		&"windup":
			squash = Vector2.ONE * lerpf(1.0, spec.windup_scale, p)
		&"drop":
			squash = Vector2.ONE.lerp(spec.drop_squash, p)
		&"impact":
			squash = spec.impact_squash
	look.visible = clip != &"shatter"
	look.scale = squash
	look.position = Vector2(0.0, -bob)
	look.modulate.a = alpha
	fan.visible = (clip == &"form" or clip == &"shatter") and not done
	if fan.visible:
		fan.frame = mini(int(p * fan.hframes), fan.hframes - 1)
