extends Node2D

# The red warning over a boss's head while an attack the player can parry winds up:
#     ParryTell.telegraph(boss, &"attack_id", seconds)   from the attack's telegraph
#     ParryTell.clear(boss)                              when its hitbox starts, or the wind-up is cut
# Which attacks advertise themselves is data: AttackCatalog's `tell`, with `parry_stagger` picking the
# strong look. It's purely a picture: it never touches hitboxes or timing. It lives beside the boss in
# the fight scene, so it freezes with a finisher and goes away with the fight.

const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

# Knobs: switch every tell off, or keep only the ones whose parry also staggers.
static var parry_tells_enabled := true
static var tells_only_for_stagger := false

var boss: Node2D
var strong := false
var clock := 0.0
var time_left := 0.0
var sprite: Sprite2D


static func telegraph(for_boss: Node2D, attack_id: StringName, duration: float) -> void:
	clear(for_boss)
	if not parry_tells_enabled or not is_instance_valid(for_boss) or for_boss.get_parent() == null:
		return
	var attack := AttackCatalog.get_attack(attack_id)
	if not attack.tell or (tells_only_for_stagger and not attack.parry_stagger):
		return
	var tell := new()
	tell.name = _tell_name(for_boss)
	tell.boss = for_boss
	tell.strong = attack.parry_stagger
	tell.time_left = duration
	# Beside the boss rather than under him: his art is scaled up, this isn't.
	for_boss.get_parent().add_child(tell)


static func clear(for_boss: Node2D) -> void:
	if not is_instance_valid(for_boss) or for_boss.get_parent() == null:
		return
	var showing := for_boss.get_parent().get_node_or_null(_tell_name(for_boss))
	if showing:
		showing.queue_free()


static func _tell_name(for_boss: Node2D) -> String:
	return "ParryTell%d" % for_boss.get_instance_id()


func _ready() -> void:
	z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	var spec := DefenseHypeArtLayout.parry_tell()
	if spec.has("standard"):
		sprite = Sprite2D.new()
		sprite.texture = load(spec.strong if strong else spec.standard)
		sprite.hframes = spec.hframes
		sprite.centered = false
		sprite.offset = -spec.pivot
		sprite.scale = Vector2.ONE * spec.scale
		add_child(sprite)
	else:
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
	_follow()


func _process(delta: float) -> void:
	if not is_instance_valid(boss):
		queue_free()
		return
	clock += delta
	time_left -= delta
	if time_left <= 0.0:
		queue_free()
		return
	var spec := DefenseHypeArtLayout.parry_tell()
	if sprite:
		sprite.frame = int(clock / spec.frame_time) % sprite.hframes
	else:
		var pulse: Array = spec.pulse
		scale = Vector2.ONE * lerpf(pulse[0], pulse[1], absf(sin(clock * PI / spec.pulse_time)))
	_follow()


# Over his head wherever he is: he moves while the whirlwind spins up.
func _follow() -> void:
	var anchor: Vector2 = boss.get_daze_anchor() if boss.has_method("get_daze_anchor") else boss.global_position
	global_position = (anchor + DefenseHypeArtLayout.PARRY_TELL_OFFSET).round()
