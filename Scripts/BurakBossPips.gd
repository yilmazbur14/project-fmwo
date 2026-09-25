extends Node2D

# Captain Burak's bullet timer: a row of pips beside his head on the gun side, one a bullet he loads.
# Each is empty, flashes as its bullet goes in, then shows loaded, then spent as he fires it
# (BurakBossArtLayout.FX.pips). Fixed in the world at HOME + PIPS_OFFSET, on his projectile layer, and
# never in the hazard group: the attacks put it up and take it down (BurakBossScript's pips calls), and
# each attack's release() hides it.

const Layout := preload("res://Scripts/BurakBossArtLayout.gd")

var pips: Array[Sprite2D] = []
# How many have been fired, which is also the next to go.
var spent := 0


# `count` empty pips, replacing whatever row was up.
func show_pips(count: int) -> void:
	hide_pips()
	var spec: Dictionary = Layout.fx(&"pips")
	var texture: Texture2D = load(spec.texture)
	for i in count:
		var pip := Sprite2D.new()
		pip.texture = texture
		pip.hframes = spec.hframes
		pip.frame = spec.empty
		pip.offset = spec.offset
		pip.scale = Vector2.ONE * Layout.SCALE
		pip.position = Vector2(i * spec.spacing * Layout.SCALE, 0.0)
		add_child(pip)
		pips.append(pip)


# Pip `index` flashes as its bullet goes in, then shows loaded.
func load_pip(index: int) -> void:
	if index < 0 or index >= pips.size():
		return
	var spec: Dictionary = Layout.fx(&"pips")
	var pip := pips[index]
	pip.frame = spec.flash
	var settle := pip.create_tween()
	settle.tween_interval(spec.flash_time)
	settle.tween_callback(_settle.bind(pip))


# The next unfired pip, in the order they loaded.
func spend_pip() -> void:
	if spent >= pips.size():
		return
	pips[spent].frame = Layout.fx(&"pips").spent
	spent += 1


# After a volley: the rounds he never fired fade out as he lowers the gun.
func fade_pips() -> void:
	for i in range(spent, pips.size()):
		var fade := pips[i].create_tween()
		fade.tween_property(pips[i], "modulate:a", 0.0, Layout.PIPS_FADE)


func hide_pips() -> void:
	for pip in pips:
		pip.queue_free()
	pips.clear()
	spent = 0


# Only a pip still flashing: one already spent keeps its frame.
func _settle(pip: Sprite2D) -> void:
	var spec: Dictionary = Layout.fx(&"pips")
	if pip.frame == spec.flash:
		pip.frame = spec.loaded
