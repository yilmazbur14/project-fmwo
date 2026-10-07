extends Node2D

# One spike of Jordan's attack 3 (JordanComboPortals): a portal Josh opens on the floor, Eric's greatsword shot up out
# of it and sucked back in, and the portal closing. The node stands on the Stage on its floor point, where its blade
# y-sorts; its portal (JordanPortal) lies on the Floor under it. Its own timeline, stepped by the attack a physics step
# at a time (step()): TELL, the portal alone for SPIKE_TELL; RISE and HOLD, live - the blade up, and a player whose soles
# box is on the opening's ellipse is hit for half a heart; SUCK, the blade going back down, harmless; CLOSE. It reports
# its own hits (never in the enemy projectile group) and never touches a held player.

const Layout := preload("res://Scripts/JordanPortalsLayout.gd")
const Spikes := preload("res://Scripts/JordanPortalSpikes.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

enum Stage { TELL, RISE, HOLD, SUCK, CLOSE, DONE }

var portal: Node2D
# The stand-in blade its attack cut once for all its spikes (cut_stand_in), until the drawn one is in.
var stand_in_blade: Texture2D
var player: CharacterBody2D
var aimed := false
# How far its blade and its smear come up, in texels: short of any keep-clear over it (JordanPortalSpikes).
var rows := Layout.BLADE_ROWS
var smear_rows := int(Layout.SMEAR.anchor.y)
var stage := Stage.TELL
var age := 0.0
# Its blade came up (a spike called off in its tell never does).
var rose := false
# The first answer its live window got from the player (a HitInfo.Result), or -1.
var struck := -1
var blade: Sprite2D
var point_x := Layout.SPIKE_BLADE_POINT_X
var smear: Sprite2D


func _ready() -> void:
	if Layout.final_smear():
		smear = Sprite2D.new()
		smear.name = "Smear"
		smear.texture = load(Layout.SPIKE_SMEAR)
		smear.centered = false
		smear.region_enabled = true
		smear.scale = Vector2.ONE * Layout.SCALE
		smear.visible = false
		add_child(smear)
	blade = Sprite2D.new()
	blade.name = "Blade"
	blade.centered = false
	blade.region_enabled = true
	blade.scale = Vector2.ONE * Layout.SCALE
	blade.visible = false
	if Layout.final_blade():
		blade.texture = load(Layout.SPIKE_BLADE)
	else:
		blade.texture = stand_in_blade if stand_in_blade != null else cut_stand_in()
		point_x = Layout.BLADE_STAND_IN.point_x
	add_child(blade)


func step(delta: float) -> void:
	if stage == Stage.DONE:
		return
	age += delta
	var up := Layout.SPIKE_TELL + Layout.SPIKE_RISE
	var down := up + Layout.SPIKE_HOLD
	var sucked := down + Layout.SPIKE_SUCK
	if stage == Stage.TELL and _reached(Layout.SPIKE_TELL):
		stage = Stage.RISE
		rose = true
		portal.burst()
	if stage == Stage.RISE and _reached(up):
		stage = Stage.HOLD
	if stage == Stage.HOLD and _reached(down):
		stage = Stage.SUCK
		portal.suck()
	if stage == Stage.SUCK and _reached(sucked):
		stage = Stage.CLOSE
		portal.close()
	if stage == Stage.CLOSE and _reached(sucked + Layout.SPIKE_CLOSE):
		stage = Stage.DONE
	_show_blade()
	if live():
		_strike()


func live() -> bool:
	return stage == Stage.RISE or stage == Stage.HOLD


# Called off in its tell, its blade never up: its portal closes and it is gone.
func retract() -> void:
	if stage != Stage.TELL:
		return
	stage = Stage.CLOSE
	age = Layout.SPIKE_TELL + Layout.SPIKE_RISE + Layout.SPIKE_HOLD + Layout.SPIKE_SUCK
	portal.close()


func covers(soles: Vector2) -> bool:
	return Spikes.covers(global_position, soles)


# A float clock summed a step at a time lands a hair short of a beat's end.
func _reached(at: float) -> bool:
	return age >= at - 0.0001


# The blade's top `rows` rows over the floor line, the rest under it; the smear behind it as it comes up, holds, goes.
func _show_blade() -> void:
	var up := Layout.SPIKE_TELL + Layout.SPIKE_RISE
	var reach := 0.0
	var smear_frame := -1
	match stage:
		Stage.RISE:
			reach = maxf(1.0, rows * _ease_out((age - Layout.SPIKE_TELL) / Layout.SPIKE_RISE))
			smear_frame = 0
		Stage.HOLD:
			reach = rows
			smear_frame = 1
		Stage.SUCK:
			reach = rows * (1.0 - clampf((age - up - Layout.SPIKE_HOLD) / Layout.SPIKE_SUCK, 0.0, 1.0))
			smear_frame = 2
	var shown := mini(roundi(reach), rows)
	blade.visible = shown > 0
	if shown > 0:
		blade.region_rect = Rect2(0, 0, blade.texture.get_width(), shown)
		blade.offset = Vector2(-point_x, -shown)
	if smear == null:
		return
	var anchor: Vector2 = Layout.SMEAR.anchor
	var tall := mini(int(anchor.y), smear_rows)
	smear.visible = smear_frame >= 0 and tall > 0
	if smear.visible:
		var size: Vector2 = Layout.SMEAR.size
		smear.region_rect = Rect2(smear_frame * size.x, anchor.y - tall, size.x, tall)
		smear.offset = Vector2(-anchor.x, -tall)


func _strike() -> void:
	if not is_instance_valid(player) or player.is_grabbed:
		return
	if not covers(player.global_position + Vector2(0, Layout.SOLES_OVER_ORIGIN)):
		return
	var result: int = player.receive_hit(HitInfo.make(Layout.HIT_ID, self, global_position))
	if struck < 0 and result != HitInfo.Result.IGNORED:
		struck = result


# eric_thrown_sword_v2 frame 6 cropped to the blade, with its spin trail - the only pure white on it - taken out.
static func cut_stand_in() -> Texture2D:
	var sheet: Texture2D = load(Layout.BLADE_STAND_IN.sheet)
	var image := sheet.get_image()
	if image.is_compressed():
		image.decompress()
	var cut := image.get_region(Layout.BLADE_STAND_IN.region)
	for y in cut.get_height():
		for x in cut.get_width():
			if cut.get_pixel(x, y) == Color.WHITE:
				cut.set_pixel(x, y, Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(cut)


static func _ease_out(x: float) -> float:
	var left := 1.0 - clampf(x, 0.0, 1.0)
	return 1.0 - left * left
