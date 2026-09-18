extends Node2D

# The red warning over a boss's head while an attack the player can parry winds up:
#     ParryTell.telegraph(boss, &"attack_id", seconds, anchor)   from the attack's telegraph
#     ParryTell.clear(boss)                                      when its hitbox starts, or it's cut
# `anchor` is an optional Callable returning the world point the badge stands on, since a boss's daze
# anchor is tuned for his downed frames; without one it falls back to that anchor.
# Which attacks advertise themselves is data: AttackCatalog's `tell`, with `parry_stagger` picking the
# strong look. It's purely a picture: it never touches hitboxes or timing. It lives beside the boss in
# the fight scene, so it freezes with a finisher and goes away with the fight.
# ParryTell.glow() puts the matching aura behind a parryable projectile in flight; nothing calls it
# yet, since only Eric's sword toss and grab tell.

const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

# Knobs: switch every tell off, or keep only the ones whose parry also staggers.
static var parry_tells_enabled := true
static var tells_only_for_stagger := false

var boss: Node2D
var anchor := Callable()
var strong := false
var glowing := false
var clock := 0.0
var time_left := 0.0
var fading := false
var sprite: Sprite2D
var frame_times: Array = []


static func telegraph(for_boss: Node2D, attack_id: StringName, duration: float, at := Callable()) -> void:
	clear(for_boss)
	if not _tells(attack_id) or not is_instance_valid(for_boss) or for_boss.get_parent() == null:
		return
	var tell := new()
	tell.name = _tell_name(for_boss)
	tell.boss = for_boss
	tell.anchor = at
	tell.strong = AttackCatalog.get_attack(attack_id).parry_stagger
	tell.time_left = duration
	# Beside the boss rather than under him: his art is scaled up, this isn't.
	for_boss.get_parent().add_child(tell)


static func clear(for_boss: Node2D) -> void:
	if not is_instance_valid(for_boss) or for_boss.get_parent() == null:
		return
	var showing := for_boss.get_parent().get_node_or_null(_tell_name(for_boss))
	if showing:
		showing.fade_out()


# The aura for a projectile the player can parry, drawn behind its own art and gone with it.
static func glow(projectile: Node2D, attack_id: StringName) -> void:
	if not _tells(attack_id) or not is_instance_valid(projectile):
		return
	var aura := new()
	aura.glowing = true
	aura.time_left = INF
	projectile.add_child(aura)
	projectile.move_child(aura, 0)


static func _tells(attack_id: StringName) -> bool:
	if not parry_tells_enabled:
		return false
	var attack := AttackCatalog.get_attack(attack_id)
	return attack.tell and (attack.parry_stagger or not tells_only_for_stagger)


static func _tell_name(for_boss: Node2D) -> String:
	return "ParryTell%d" % for_boss.get_instance_id()


func _ready() -> void:
	if glowing:
		_build_sprite(DefenseHypeArtLayout.PARRY_GLOW, DefenseHypeArtLayout.PARRY_GLOW.scale)
		frame_times = [DefenseHypeArtLayout.PARRY_GLOW.frame_time]
		return
	z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	var spec := DefenseHypeArtLayout.parry_tell()
	if spec.has("scale"):
		var badge: Dictionary = spec.strong if strong else spec.standard
		_build_sprite(badge, spec.scale)
		frame_times = badge.frame_times
	else:
		_build_chevron(spec)
	_follow()


func _process(delta: float) -> void:
	if glowing:
		clock += delta
		sprite.frame = int(clock / frame_times[0]) % sprite.hframes
		return
	if not is_instance_valid(boss):
		queue_free()
		return
	clock += delta
	time_left -= delta
	if time_left <= 0.0:
		fade_out()
		return
	if sprite:
		sprite.frame = _frame_at(clock)
	else:
		var spec := DefenseHypeArtLayout.parry_tell()
		var pulse: Array = spec.pulse
		scale = Vector2.ONE * lerpf(pulse[0], pulse[1], absf(sin(clock * PI / spec.pulse_time)))
	_follow()


# Leaves at once as far as the next tell is concerned, then fades over a frame or two.
func fade_out() -> void:
	if fading:
		return
	fading = true
	name += "Spent"
	set_process(false)
	var fade := create_tween()
	fade.tween_property(self, "modulate:a", 0.0, DefenseHypeArtLayout.PARRY_TELL_FADE_OUT)
	fade.tween_callback(queue_free)


func _build_sprite(spec: Dictionary, at_scale: float) -> void:
	sprite = Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.centered = false
	sprite.offset = -spec.pivot
	sprite.scale = Vector2.ONE * at_scale
	add_child(sprite)


func _build_chevron(spec: Dictionary) -> void:
	var chevron := Polygon2D.new()
	var half: float = spec.size.x / 2.0
	var height: float = spec.size.y
	var thickness: float = height * spec.thickness
	chevron.polygon = PackedVector2Array([
		Vector2(-half, -height), Vector2(0, 0), Vector2(half, -height),
		Vector2(half, -height - thickness), Vector2(0, -thickness), Vector2(-half, -height - thickness),
	])
	chevron.color = spec.strong_color if strong else spec.color
	add_child(chevron)


# Loops, and starts on frame 0: the biggest, brightest one.
func _frame_at(time: float) -> int:
	var loop := 0.0
	for frame_time in frame_times:
		loop += frame_time
	var into := fposmod(time, loop)
	var end := 0.0
	for i in frame_times.size():
		end += frame_times[i]
		if into < end:
			return i
	return frame_times.size() - 1


# Over his head wherever he is: he moves while the whirlwind spins up.
func _follow() -> void:
	if anchor.is_valid():
		global_position = Vector2(anchor.call()).round()
		return
	var head: Vector2 = boss.get_daze_anchor() if boss.has_method("get_daze_anchor") else boss.global_position
	global_position = (head + DefenseHypeArtLayout.PARRY_TELL_OFFSET).round()
