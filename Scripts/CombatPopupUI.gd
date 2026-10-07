extends Node2D

# Word popups over the player's head: PARRY!, PERFECT!, GUARD BREAK!, HYPE!, TIRED! and the status effects.
# They're on the HUD layer, so the finisher's zoom doesn't scale them; DefenseHypeArtLayout's POPUPS
# section has their rules.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

@export var player: CharacterBody2D
@export var defense: Node
@export var hype: Node
@export var status: Node

# The word each status effect (PlayerStatus) announces itself with.
const STATUS_WORDS := {
	&"stamina_drain": &"drained",
	&"inverted_controls": &"reversed",
}

# {kind, node, size, stack: px above the first line, lift, clock, tween, room: the counter's height it stands
# over} for each popup still showing.
var popups: Array = []
# The status effects whose word has already been said.
var status_shown := {}


func _ready() -> void:
	defense.parried.connect(func(_hit: RefCounted, _point: Vector2, _staggered: bool, streak: int) -> void:
		# One word per tier; the exact count is on the streak badge.
		if streak >= 3:
			show_popup(&"parry_x3")
		elif streak == 2:
			show_popup(&"parry_x2")
		else:
			show_popup(&"parry")
	)
	defense.perfect_dodged.connect(func(_hit: RefCounted) -> void: show_popup(&"perfect"))
	defense.guard_broken.connect(show_popup.bind(&"guard_break"))
	defense.stamina_refused.connect(show_popup.bind(&"tired"))
	hype.hype_full_changed.connect(func(full: bool) -> void:
		if full:
			show_popup(&"hype")
	)
	# Only when the effect lands, not when a boss refreshes one that is already running.
	status.status_started.connect(func(kind: StringName, _duration: float) -> void:
		if status_shown.has(kind):
			return
		status_shown[kind] = true
		show_popup(STATUS_WORDS[kind])
	)
	status.status_ended.connect(func(kind: StringName) -> void: status_shown.erase(kind))


func _process(delta: float) -> void:
	for popup in popups:
		popup.clock += delta
		_animate(popup)
		_place(popup)


func show_popup(kind: StringName, count := 0) -> void:
	if kind in DefenseHypeArtLayout.POPUP_HOLDING:
		for other in popups:
			if other.kind == kind:
				_run(other)
				return
	var spec := DefenseHypeArtLayout.popup(kind)
	var popup := {"kind": kind, "count": count, "stack": 0.0, "lift": 0.0, "clock": 0.0}
	for other in popups:
		popup.stack = maxf(popup.stack, other.stack + other.size.y)
	if spec.has("texture"):
		var sprite := Sprite2D.new()
		sprite.texture = load(spec.texture)
		sprite.hframes = spec.hframes
		sprite.centered = false
		add_child(sprite)
		popup.node = sprite
		popup.size = Vector2(sprite.texture.get_width() / float(spec.hframes), sprite.texture.get_height())
	else:
		var label := Label.new()
		label.theme = load("res://Assets/UI/ui_theme.tres")
		label.text = spec.text % count if spec.text.contains("%d") else spec.text
		label.add_theme_font_size_override("font_size", spec.font_size)
		label.add_theme_constant_override("outline_size", spec.outline)
		label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		# In the tree first: a label only measures its text with its theme applied.
		add_child(label)
		popup.node = label
		popup.size = label.get_combined_minimum_size()
		label.size = popup.size
	popups.append(popup)
	_animate(popup)
	_place(popup)
	_run(popup)


# Its rise, from wherever it has got to, then its hold and its fade. A word held again rises on from where it is
# rather than dropping back to the start, so it never jumps. Real time, so a hit-stop doesn't hold the word up.
func _run(popup: Dictionary) -> void:
	if popup.has("tween"):
		popup.tween.kill()
	popup.node.modulate.a = 1.0
	var tween: Tween = popup.node.create_tween().set_ignore_time_scale(true)
	popup.tween = tween
	var rise_left: float = DefenseHypeArtLayout.POPUP_RISE_TIME * (1.0 - popup.lift / DefenseHypeArtLayout.POPUP_RISE)
	if rise_left > 0.0:
		tween.tween_method(func(lift: float) -> void: popup.lift = lift, popup.lift, DefenseHypeArtLayout.POPUP_RISE, rise_left).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_interval(DefenseHypeArtLayout.POPUP_HOLD_TIME)
	tween.tween_property(popup.node, "modulate:a", 0.0, DefenseHypeArtLayout.POPUP_FADE_TIME)
	tween.tween_callback(func() -> void:
		popups.erase(popup)
		popup.node.queue_free()
	)


func _animate(popup: Dictionary) -> void:
	var spec := DefenseHypeArtLayout.popup(popup.kind)
	var look := int(popup.clock / spec.frame_time) % 2
	if popup.node is Sprite2D:
		popup.node.frame = look
	else:
		popup.node.add_theme_color_override("font_color", spec.colors[look])


# Bottom-centre over the head, over the combo counter when it is up there too (ComboCounterUI). Top-centre
# under the feet where its rise would take it over POPUP_TOP_LIMIT or into the HUD at the top, and stood
# clear above any HUD at the bottom it would sink into (POPUP_KEEP_OUT).
func _place(popup: Dictionary) -> void:
	var tree := get_tree()
	var size: Vector2 = popup.size
	var counter := get_parent().get_node_or_null("ComboCounter")
	var room: float = counter.overhead_room() if counter != null and counter.has_method("overhead_room") else 0.0
	# Grown the moment the counter comes up under a word, never shrunk while the word is up: a held TIRED! dropping
	# back as the counter fades out would jump.
	room = maxf(popup.get("room", 0.0), room)
	popup.room = room
	var head := ScreenView.world_to_screen(tree, _head())
	var left: float = head.x - size.x / 2.0
	var bottom: float = head.y - DefenseHypeArtLayout.POPUP_GAP - popup.stack - room
	var risen := Rect2(left, bottom - size.y - DefenseHypeArtLayout.POPUP_RISE, size.x, size.y + DefenseHypeArtLayout.POPUP_RISE)
	var under := risen.position.y < DefenseHypeArtLayout.POPUP_TOP_LIMIT
	for keep_out in DefenseHypeArtLayout.POPUP_KEEP_OUT:
		var hud := keep_out.grow(DefenseHypeArtLayout.POPUP_HUD_CLEARANCE)
		if hud.get_center().y < head.y:
			under = under or hud.intersects(risen)
		elif hud.intersects(Rect2(left, bottom - size.y, size.x, size.y)):
			bottom = minf(bottom, hud.position.y)
	var top: float = bottom - size.y - popup.lift
	if under:
		var feet := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_FEET)
		top = feet.y + DefenseHypeArtLayout.POPUP_GAP + popup.stack + popup.lift + room
	var margin := Vector2.ONE * DefenseHypeArtLayout.POPUP_SCREEN_MARGIN
	var corner := Vector2(left, top)
	popup.node.position = corner.clamp(margin, get_viewport_rect().size - size - margin).round()


# The point the words stand over: the player's head, or, posed on a fight's sheet that marks the head on its
# cell (Greyson's brawl draws them twice the size, from behind), that texel where the sprite draws it.
func _head() -> Vector2:
	if player.is_posed() and player.pose_sheet.has("head"):
		var sprite: Sprite2D = player.sprite
		var cell := Vector2(sprite.texture.get_width() / float(sprite.hframes), sprite.texture.get_height() / float(sprite.vframes))
		return sprite.to_global(player.pose_sheet.head - cell / 2.0 + sprite.offset)
	return player.global_position + FinisherArtLayout.PLAYER_HEAD
