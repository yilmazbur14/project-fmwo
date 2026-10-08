extends Control

# A HUD block that fades while something the player has to see is under it: the player's drawn body, a tell's badge
# or KNIGHT BREAKER! (UNDER_GROUP). Nobody may be hidden behind the boss bar at the top of the ring or behind the
# hearts, stamina and hype in the bottom corners (the 2026-10-04 playtest: a player near the top rope's middle vanished
# under the boss bar, which only faded where a fight faded it for his own badge). A boss's own body is left to his
# fight, which fades the bar for his crown where he stands under it: faded for his whole body, a big boss at home
# under the bar would hide his bar all fight. The block's pieces are moved into this node (wrap), so its alpha
# multiplies with the block's own modulate - which the fights tween for their badges, and the HUD scripts use for their
# own flashes and fades - instead of fighting them for it.

# The alpha and the time the fights already fade the boss bar with for a boss's badge.
const PLAYER_UNDER_ALPHA := 0.3
const FADE_TIME := 0.25
# Where FightOutro finds the fight's player.
const FIGHT_PLAYER_SPRITE := ^"Arena/MainPlayer/CharacterBody2D/Sprite2D"
# What else the HUD fades for: a tell's badge (its `sprite`), KNIGHT BREAKER! (a Sprite2D or a Label itself).
const UNDER_GROUP := &"hud_fade_under"

# Returns the player's Sprite2D, or null. Unset, the fight's player.
var sprite_of := Callable()
var pieces: Array[Node] = []


# Moves every child `host` has now into a new one of these, and returns it.
static func wrap(host: Control, player_sprite := Callable()) -> Control:
	var fade := new()
	fade.name = "PlayerFade"
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.sprite_of = player_sprite
	var children := host.get_children()
	host.add_child(fade)
	for child in children:
		child.reparent(fade, false)
	return fade


# Stepped off the tree's frame rather than _process: the boss's HUD lives under him, the branch a finisher's freeze
# stops, and KNIGHT BREAKER! goes up during the freeze. Its pieces keep the branch's process mode, so the bar's own
# drains still stall with the fight.
func _ready() -> void:
	get_tree().process_frame.connect(_step)


# Real seconds, so a hit-stop doesn't hold the bar over the player.
func _step() -> void:
	if not is_inside_tree():
		return
	var delta := get_process_delta_time()
	if pieces.is_empty():
		pieces = find_children("*", "CanvasItem", true, false)
	var wanted := PLAYER_UNDER_ALPHA if _covering() else 1.0
	var step := (1.0 - PLAYER_UNDER_ALPHA) * delta / maxf(Engine.time_scale, 0.001) / FADE_TIME
	modulate.a = move_toward(modulate.a, wanted, step)


func _covering() -> bool:
	var under: Array[Rect2] = []
	var player := _sprite()
	if player != null and player.is_visible_in_tree():
		under.append(_screen_rect(player))
	for node in get_tree().get_nodes_in_group(UNDER_GROUP):
		var drawn = node if node is Sprite2D or node is Control else node.get("sprite")
		if (drawn is Sprite2D or drawn is Control) and drawn.is_visible_in_tree():
			under.append(_screen_rect(drawn))
	if under.is_empty():
		return false
	for piece in pieces:
		if not is_instance_valid(piece) or not piece.is_visible_in_tree():
			continue
		var rect := _screen_rect(piece)
		if not rect.has_area():
			continue
		for body in under:
			if rect.intersects(body):
				return true
	return false


func _sprite() -> Sprite2D:
	if sprite_of.is_valid():
		return sprite_of.call() as Sprite2D
	var scene := get_tree().current_scene
	return scene.get_node_or_null(FIGHT_PLAYER_SPRITE) as Sprite2D if scene != null else null


func _screen_rect(piece: Node) -> Rect2:
	if piece is Control:
		return piece.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, piece.size)
	if piece is Sprite2D:
		return piece.get_global_transform_with_canvas() * piece.get_rect()
	return Rect2()
