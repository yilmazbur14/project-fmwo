extends Node2D

# The worms of one of Danny's puddles holding the player's feet (plan section 3.3), drawn over them. It takes
# the player's movement, dash and punches with lock_actions(), and NOT the sealed kind: the guard and its
# parry stay live, because the parry is the answer to what he does with a rooted player (his Headbutt). The
# player is turned to face him.
# The fight decides how long it lasts. His state machine is told of it (on_player_rooted, by the puddle
# that sprang it), and lets it go with release(), or with hold(t) to have it let go by itself t from now.
# release() is idempotent, and a root that leaves the tree without one lets go of the player on its way out.

# The player has been let go, once, however it ended.
signal let_go

const HitStop := preload("res://Scripts/HitStop.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

const CLAMP_HIT_STOP := 0.05

# Set before it enters the tree.
var player: Node2D
var body: Node2D

var released := false
# Seconds until it lets go by itself, or below 0 for never.
var hold_left := -1.0
var clock := 0.0
# f0-3 loop while they hold, f4-7 play once as they let go; its pivot is the floor under the player's feet.
var spec: Dictionary = Layout.fx(&"root")
var sheet: Sprite2D


# Where the worms take hold under `who`: from their sprite's rest, so a hit shake doesn't drag the worms.
static func pivot_of(who: Node2D) -> Vector2:
	var sprite: Sprite2D = who.sprite
	var below: float = Layout.fx(&"root").feet_below_centre
	return who.to_global(who.sprite_base_position) + sprite.offset * sprite.global_scale + Vector2(0, below)


func _ready() -> void:
	sheet = Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.scale = Vector2.ONE * Layout.SCALE
	sheet.offset = spec.offset
	sheet.frame = spec.hold_frames[0]
	add_child(sheet)
	global_position = pivot_of(player)
	player.lock_actions()
	player.face_point(body.global_position)
	body.play_sfx(&"root_clamp")
	HitStop.freeze(get_tree(), CLAMP_HIT_STOP)


func _physics_process(delta: float) -> void:
	if released:
		return
	clock += delta
	var frames: Array = spec.hold_frames
	var hold_time: float = spec.hold_time
	sheet.frame = frames[int(clock / hold_time) % frames.size()]
	# On their feet wherever the fight puts them while they're held.
	if is_instance_valid(player):
		global_position = pivot_of(player)
	if hold_left >= 0.0:
		hold_left -= delta
		if hold_left <= 0.0:
			release()


# Lets go by itself `seconds` from now; a second call starts the wait again.
func hold(seconds: float) -> void:
	if released:
		return
	hold_left = maxf(seconds, 0.0)


func release() -> void:
	if released:
		return
	released = true
	hold_left = -1.0
	if is_instance_valid(player):
		player.unlock_actions()
	let_go.emit()
	var frames: Array = spec.release_frames
	var release_time: float = spec.release_time
	sheet.frame = frames[0]
	var play := create_tween()
	for i in range(1, frames.size()):
		play.tween_interval(release_time)
		play.tween_callback(sheet.set_frame.bind(frames[i]))
	play.tween_interval(release_time)
	play.tween_callback(queue_free)


# Freed with the fight's hazards or with his whole scene, never released: the player is let go on the way
# out, without the release frames, which have no tree left to play in.
func _exit_tree() -> void:
	if released:
		return
	released = true
	if is_instance_valid(player) and player.is_inside_tree():
		player.unlock_actions()
	let_go.emit()
