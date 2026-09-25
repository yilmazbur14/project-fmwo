extends Node2D

# One keg going up in Captain Burak's volley (BurakBossBarrels): the fireball on the keg's floor point, the
# flash and smoke over the whole ring, and the hit, all on the step it goes off. Nothing answers it and it
# carries no tell: the answer was the punches that broke the kegs in time. It lands through the guard, the
# dash and the i-frames (AttackCatalog's burak_barrel_blast), so the bill is one hit per keg left.
# Every blast is its own node and its hit's source, the rule for every hit in this fight.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")

const ATTACK_ID := &"burak_barrel_blast"

const SHAKE := 18.0
const SHAKE_STEPS := 8
const SHAKE_STEP_TIME := 0.03
const HIT_STOP := 0.04
const CHEER := 0.6

var fireball: Sprite2D
var screen: Sprite2D


# Goes off on `keg` on this step and returns what the hit did (HitInfo.Result). The node must already be in
# the tree, on the fight's projectile layer.
# `flash`: only a volley's first blast whites out the screen. Four or five full-screen flashes back to back
# are harsh, so every later one starts its overlay on the smoke; each still shakes and stops the fight.
# `mercy`: the fight's first volley can't take the last half-heart. The hit still lands and still counts.
func go_off(keg: Node2D, player: Node2D, boss: Node2D, flash: bool, mercy: bool) -> int:
	global_position = keg.global_position
	keg.blow()
	_play_fireball()
	_play_screen(flash)
	ScreenView.shake(get_tree(), SHAKE, SHAKE_STEPS, SHAKE_STEP_TIME)
	HitStop.freeze(get_tree(), HIT_STOP)
	boss.play_sfx(&"blast")
	get_tree().call_group("arena_crowd", "cheer", CHEER)
	var hit := HitInfo.make(ATTACK_ID, self, hurtbox_centre(player), boss)
	if mercy:
		hit.damage = mini(hit.damage, player.playerHealth - 1)
	return player.receive_hit(hit)


# The hit's origin. The blast fills the ring, so there is no side for a facing to be measured against.
static func hurtbox_centre(player: Node2D) -> Vector2:
	var shape: Node2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


func _play_fireball() -> void:
	var spec: Dictionary = Layout.fx(&"blast")
	fireball = _sheet(spec)
	fireball.offset = spec.offset
	add_child(fireball)
	# The longer of the two, so the node goes with it.
	var play := create_tween()
	for f in range(1, spec.hframes):
		play.tween_interval(spec.frame_time)
		play.tween_callback(fireball.set_frame.bind(f))
	play.tween_interval(spec.frame_time)
	play.tween_callback(queue_free)


func _play_screen(flash: bool) -> void:
	var spec: Dictionary = Layout.fx(&"blast_screen")
	var first: int = 0 if flash else spec.smoke_first
	screen = _sheet(spec)
	screen.centered = false
	screen.z_index = spec.z_index
	screen.frame = first
	add_child(screen)
	screen.global_position = Vector2.ZERO
	var play := create_tween()
	for f in range(first + 1, spec.hframes):
		play.tween_interval(spec.frame_time)
		play.tween_callback(screen.set_frame.bind(f))
	play.tween_interval(spec.frame_time)
	play.tween_callback(screen.queue_free)


static func _sheet(spec: Dictionary) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.scale = Vector2.ONE * Layout.SCALE
	return sprite
