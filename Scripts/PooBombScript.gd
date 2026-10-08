extends Node2D

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const MasonImpactThrottle := preload("res://Scripts/MasonImpactThrottle.gd")

# The red badge stands on the bomb rather than over Mason: the blast is what the player parries, and
# it goes off wherever the line left it, often halfway across the mat from him.
# Two things narrow it down from "every bomb", and both are about a line being a dozen of these at
# once rather than one attack with one wind-up:
# - it comes up a read before the blast, not for the whole fuse. PlayerDefense.parry_window is 0.24 s
#   and 1.5x it is the floor Eric's slam tell sits on.
# - only a blast whose radius already covers the player wears one. A line is area denial: the answer
#   is to be somewhere else, and the ring on the line's start spot is what says where. The parry is
#   the out for the one blast that has the player in it, so that is the one the badge times. Telling
#   every armed bomb put up to 7 badges at once (15-17 bombs sit on the mat at the peak), and on the
#   leg of a line that runs straight down the screen each badge covered the bomb 100 px above it.
const TELL_LEAD := 0.36
# Where the badge's tip stands: just over the turd, which is drawn 48 px either side of the origin
# the blast is centred on.
const TELL_ANCHOR_OFFSET := Vector2(0, -56)
# Where the "explode" animation's method track switches the hitbox on, so the badge is still up as
# the blast becomes real.
const EXPLOSION_HITBOX_DELAY := 0.1

@export var animation_player: AnimationPlayer
@export var detonate_timer: Timer
@export var explode_sfx: AudioStreamPlayer
@export var explosion_hitbox_shape: CollisionShape2D
@export var bomb_sprite: Sprite2D

# Set by Mason as the bomb is dropped; without one the bomb never tells, which is what the headless
# checks that run no player see.
var player: Node2D


func _ready() -> void:
	explosion_hitbox_shape.get_parent().set_meta(HitInfo.META_ATTACK, &"mason_poo_blast")
	detonate_timer.timeout.connect(_detonate)
	animation_player.animation_finished.connect(_on_animation_player_animation_finished)
	animation_player.play("armed")


func arm(detonate_delay: float) -> void:
	# Mason's next line can walk back across this one while it counts down, and depth
	# sorting would hide a lit bomb behind him, so lit bombs draw above the characters.
	bomb_sprite.z_index = 1
	_tell_before(detonate_delay)
	# Timer.start(0) silently falls back to the timer's old wait_time instead of
	# firing immediately, so a zero delay has to bypass the timer entirely.
	if detonate_delay <= 0.0:
		_detonate.call_deferred()
		return
	detonate_timer.start(detonate_delay)


# The wait is a tween bound to the bomb, so freeing it mid-fuse takes the badge's cue with it.
func _tell_before(detonate_delay: float) -> void:
	var lead := minf(maxf(detonate_delay, 0.0), TELL_LEAD)
	if detonate_delay <= TELL_LEAD:
		_show_tell(lead)
		return
	var wait := create_tween()
	wait.tween_interval(detonate_delay - TELL_LEAD)
	wait.tween_callback(_show_tell.bind(lead))


func _show_tell(lead: float) -> void:
	if not _blast_reaches_player():
		return
	ParryTell.telegraph(self, &"mason_poo_blast", lead + EXPLOSION_HITBOX_DELAY, _tell_anchor)


# Where the player stands as the read begins. They can still walk out of it, and a badge left over a
# blast they have cleared costs them nothing; walking in after it is the same silence as today.
func _blast_reaches_player() -> bool:
	if not is_instance_valid(player):
		return false
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	var radius: float = (explosion_hitbox_shape.shape as CircleShape2D).radius
	return global_position.distance_to(global_position.clamp(box.position, box.end)) < radius


func _tell_anchor() -> Vector2:
	return global_position + TELL_ANCHOR_OFFSET


func _detonate() -> void:
	if MasonImpactThrottle.allow():
		explode_sfx.play()
	animation_player.play("explode")


# Called by the "explode" animation's method track.
func _enable_hitbox() -> void:
	# The blast is the threat now: the warning has done its job.
	ParryTell.clear(self)
	explosion_hitbox_shape.set_deferred("disabled", false)


# Called by the "explode" animation's method track.
func _disable_hitbox() -> void:
	explosion_hitbox_shape.set_deferred("disabled", true)


func _on_animation_player_animation_finished(anim_name: StringName) -> void:
	if anim_name == &"explode":
		queue_free()
