extends Node2D

# Word popups over the player's head: PARRY!, PERFECT!, GUARD BREAK! and HYPE!. They're on the HUD
# layer, so the finisher's zoom doesn't scale them; DefenseHypeArtLayout's POPUPS section has their
# rules.

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

@export var player: CharacterBody2D
@export var defense: Node
@export var hype: Node

# {kind, node, size, stack: px above the first line, lift, clock} for each popup still showing.
var popups: Array = []


func _ready() -> void:
	defense.parried.connect(func(_hit: RefCounted, _point: Vector2, _staggered: bool) -> void: show_popup(&"parry"))
	defense.perfect_dodged.connect(func(_hit: RefCounted) -> void: show_popup(&"perfect"))
	defense.guard_broken.connect(show_popup.bind(&"guard_break"))
	hype.hype_full_changed.connect(func(full: bool) -> void:
		if full:
			show_popup(&"hype")
	)


func _process(delta: float) -> void:
	for popup in popups:
		popup.clock += delta
		_animate(popup)
		_place(popup)


func show_popup(kind: StringName) -> void:
	var spec := DefenseHypeArtLayout.popup(kind)
	var popup := {"kind": kind, "stack": 0.0, "lift": 0.0, "clock": 0.0}
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
		label.text = spec.text
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
	# Real time, so a hit-stop doesn't hold the word up.
	var tween: Tween = popup.node.create_tween().set_ignore_time_scale(true)
	tween.tween_method(func(lift: float) -> void: popup.lift = lift, 0.0, DefenseHypeArtLayout.POPUP_RISE, DefenseHypeArtLayout.POPUP_RISE_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
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


# Bottom-centre over the head, or top-centre under the feet near the top of the screen.
func _place(popup: Dictionary) -> void:
	var tree := get_tree()
	var size: Vector2 = popup.size
	var head := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var bottom: float = head.y - DefenseHypeArtLayout.POPUP_GAP - popup.stack
	var top: float = bottom - size.y - popup.lift
	if bottom - size.y - DefenseHypeArtLayout.POPUP_RISE < DefenseHypeArtLayout.POPUP_TOP_LIMIT:
		var feet := ScreenView.world_to_screen(tree, player.global_position + FinisherArtLayout.PLAYER_FEET)
		top = feet.y + DefenseHypeArtLayout.POPUP_GAP + popup.stack + popup.lift
	var margin := Vector2.ONE * DefenseHypeArtLayout.POPUP_SCREEN_MARGIN
	var corner := Vector2(head.x - size.x / 2.0, top)
	popup.node.position = corner.clamp(margin, get_viewport_rect().size - size - margin).round()
