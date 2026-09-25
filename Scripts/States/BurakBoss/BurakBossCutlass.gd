extends State

# Captain Burak's cutlass string (plan section 5): he runs the player down and swings three times, and only
# a parry or a timed dash answers a swing. A held guard is hit (burak_cutlass is parryable, not blockable),
# and walking away never works: he tracks at chase_speed, faster than any walk, to a spot standoff px beside
# the player's feet.
#   CHASE   burak_run to that spot, chase_max at most; a chase that never gets there ends in a huff.
#   WINDUP  swing k's wind-up held under a red badge, still tracking.
#   STRIKE  the step the wind-up ends: the strike frame, and the swing asks the player's defence once.
#   FOLLOW  the strike frame for strike_show, then the follow-through, rooted.
#   REAIM   burak_run back to the spot, reaim_min to reaim_max, before the next wind-up.
#   SPENT   idle, then the next attack.
# Strike to strike is at least follow + reaim_min + windup, 1.10 s, past the 1.0 s i-frames. A parried swing
# fills a third of his Break gauge, so three in a row always Break him. His body's own Defense.parried
# connection credits the gauge; nothing here does. Every wait is a Physics_Update accumulator; the jolt and
# the trail are node-bound tweens.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")
const SLASH_SCRIPT := preload("res://Scripts/BurakBossSlashScript.gd")

const CUTLASS_ID := &"burak_cutlass"

@export var body : CharacterBody2D

#KNOBS (seconds and px)
@export var chase_speed := 1400.0
@export var chase_max := 2.5
# Close enough to the spot to swing from.
@export var arrive := 24.0
# How far beside the player's feet he swings from.
@export var standoff := 100.0
# How far past the player he has to go before he takes the other side.
@export var side_hysteresis := 24.0
@export var windup := 0.55
@export var follow := 0.30
@export var reaim_min := 0.25
@export var reaim_max := 0.85
@export var spent := 0.35
# A chase that never got there: he shrugs this long, then the next attack.
@export var huff := 0.6
# The strike frame's own time on the sheet, the artist's for all three swings; the follow-through after it.
@export var strike_show := 0.08
# A parried swing knocks his sprite back this far and home again over this long.
@export var jolt := 6.0
@export var jolt_time := 0.1
# The whoosh, a pitch a swing.
@export var slash_pitches: Array[float] = [1.0, 1.12, 0.9]

@onready var state_machine = get_parent()

enum Beat { CHASE, HUFF, WINDUP, FOLLOW, REAIM, SPENT }

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var beat := Beat.CHASE
var beat_clock := 0.0
# The swing coming or landing: 0 side, 1 backhand, 2 overhead.
var swing := 0
# The side of the player he swings from: 1 their right, -1 their left.
var side := 1.0
# A bare node on his projectile layer that holds the swings, so nothing beside a swing is a sprite: a
# parry's flash and shatter land on the first sprite by the hit's source (BurakBossSlashScript).
var holder: Node2D
var trail: Sprite2D
var jolt_tween: Tween
# For tests: the fight_clock of each strike, and each strike's HitInfo.Result.
var strike_times: Array[float] = []
var results: Array[int] = []


func Enter() -> void:
	released = false
	strike_times.clear()
	results.clear()
	swing = 0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	if not is_instance_valid(holder):
		holder = Node2D.new()
		holder.name = "SlashHolder"
		body.projectile_layer.add_child(holder)
	var player: Node2D = state_machine.get_player()
	side = -1.0 if player and body.global_position.x < _player_feet(player).x else 1.0
	beat = Beat.CHASE
	beat_clock = 0.0
	body.play_anim(&"run")


func Exit() -> void:
	release()


# Leaving with his whole scene: the badge and the HUD it would tidy have left the tree already, and a
# tween can't start on them there.
func _exit_tree() -> void:
	released = true


# Idempotent: the badge, the HUD's fade, the hint, the trail and the jolt go whichever way the string ended.
func release() -> void:
	if released:
		return
	released = true
	if not is_instance_valid(body):
		return
	ParryTell.clear(body)
	body.restore_hud()
	body.hide_hint(&"cutlass")
	_drop_trail()
	if jolt_tween:
		jolt_tween.kill()
	body.sprite.position = body.sprite_base_position


func Physics_Update(delta: float) -> void:
	if released:
		return
	beat_clock += delta
	match beat:
		Beat.CHASE:
			if _track(delta):
				_wind_up()
			elif beat_clock >= chase_max:
				_huff()
		Beat.HUFF:
			if beat_clock >= huff:
				state_machine.attack_done(self)
		Beat.WINDUP:
			_track(delta)
			if beat_clock >= windup:
				beat_clock -= windup
				_strike()
		Beat.FOLLOW:
			var pose := Layout.slash_anim(swing, &"follow")
			if beat_clock >= strike_show and body.current_anim != pose:
				body.play_anim(pose)
			if beat_clock >= follow:
				beat_clock -= follow
				swing += 1
				if swing < Layout.SLASH_BOXES.size():
					_reaim()
				else:
					_spend()
		Beat.REAIM:
			var there := _track(delta)
			if beat_clock >= reaim_min and (there or beat_clock >= reaim_max):
				_wind_up()
		Beat.SPENT:
			if beat_clock >= spent:
				state_machine.attack_done(self)


# Straight at the spot beside the player's feet, facing them. True once he is there.
func _track(delta: float) -> bool:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return false
	var spot := _side_point(player)
	body.global_position = body.global_position.move_toward(spot, chase_speed * delta)
	body.face_toward(player.global_position)
	return body.global_position.distance_to(spot) <= arrive


# standoff px beside the player's feet on the side he is on, which he keeps until he is side_hysteresis
# past them: the other side where this one is off his floor, and his floor's edge where both are.
func _side_point(player: Node2D) -> Vector2:
	var feet := _player_feet(player)
	var dx := body.global_position.x - feet.x
	if side > 0.0 and dx < -side_hysteresis:
		side = -1.0
	elif side < 0.0 and dx > side_hysteresis:
		side = 1.0
	var walk: Rect2 = state_machine.WALK_RECT
	var spot := feet + Vector2(side * standoff, 0.0)
	if not walk.has_point(spot):
		var other := feet - Vector2(side * standoff, 0.0)
		if walk.has_point(other):
			side = -side
			spot = other
	return spot.clamp(walk.position, walk.end)


# The bottom middle of the player's hurtbox: their feet, on the ground line he stands on.
func _player_feet(player: Node2D) -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)


func _wind_up() -> void:
	beat = Beat.WINDUP
	beat_clock = 0.0
	var pose := Layout.slash_anim(swing, &"windup")
	body.play_anim(pose)
	ParryTell.telegraph(body, CUTLASS_ID, windup, body.tell_anchor)
	body.update_hud_fade(pose)
	body.show_hint(&"cutlass", "YOU CAN'T OUTRUN HIM! DASH (%s) THROUGH THE SWING OR TAP %s TO PARRY" % [InputSettings.label_for(&"dodge"), InputSettings.label_for(&"block")])


func _strike() -> void:
	beat = Beat.FOLLOW
	ParryTell.clear(body)
	body.play_anim(Layout.slash_anim(swing, &"strike"))
	body.play_sfx(&"slash", slash_pitches[swing])
	_play_trail()
	var slash: Node2D = SLASH_SCRIPT.new()
	slash.name = "Slash%d" % swing
	slash.player = state_machine.get_player()
	slash.body = body
	slash.box = Layout.SLASH_BOXES[swing]
	slash.flip = body.sprite.flip_h
	slash.answered.connect(_on_answered)
	state_machine.add_hazard(slash, body.global_position, holder)
	strike_times.append(body.fight_clock)
	results.append(slash.strike())


func _reaim() -> void:
	beat = Beat.REAIM
	body.play_anim(&"run")


func _spend() -> void:
	beat = Beat.SPENT
	body.play_state_anim(&"idle")


# The chase never got there: a shrug, then the next attack.
func _huff() -> void:
	beat = Beat.HUFF
	beat_clock = 0.0
	body.show_talk(&"shrug", false)


func _on_answered(result: int) -> void:
	if result != HitInfo.Result.PARRIED:
		return
	body.play_sfx(&"clang")
	_jolt()


# His sprite knocked back off the parry, away from the player, and home again. His feet stay put.
func _jolt() -> void:
	if jolt_tween:
		jolt_tween.kill()
	var sprite: Sprite2D = body.sprite
	var back := Vector2(jolt if sprite.flip_h else -jolt, 0.0)
	jolt_tween = sprite.create_tween()
	jolt_tween.tween_property(sprite, "position", body.sprite_base_position + back, jolt_time / 2.0)
	jolt_tween.tween_property(sprite, "position", body.sprite_base_position, jolt_time / 2.0)


# Swing k's arc over him, on his node and flipped with him, from the strike frame: its first two frames
# span the strike, the third the follow-through's start.
func _play_trail() -> void:
	_drop_trail()
	var spec := Layout.fx(&"slash_trail")
	trail = Sprite2D.new()
	trail.texture = load(spec.texture)
	trail.hframes = spec.hframes
	trail.scale = Vector2.ONE * Layout.SCALE
	trail.flip_h = body.sprite.flip_h
	trail.offset = Layout.flipped_offset(spec.offset, trail.flip_h, false)
	trail.position = body.sprite_base_position
	var first: int = swing * spec.frames_per_swing
	trail.frame = first
	body.add_child(trail)
	var frame_time: float = spec.frame_time
	var play := trail.create_tween()
	for i in range(1, spec.frames_per_swing):
		play.tween_interval(frame_time)
		play.tween_callback(trail.set_frame.bind(first + i))
	play.tween_interval(frame_time)
	play.tween_callback(trail.queue_free)


func _drop_trail() -> void:
	if is_instance_valid(trail):
		trail.queue_free()
	trail = null
