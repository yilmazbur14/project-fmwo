extends State

# Captain Burak's opener, the pistol pair (plan section 3). Back at HOME if he isn't there, he loads two
# bullets under a red badge, then fires them 1.10 s apart, each at the player's hurtbox centre as it stood
# latch_lead before the shot:
#   RETURN  burak_run to HOME at return_speed, return_max at most.
#   LOAD    one loop of burak_load a bullet; each loop's last frame loads a pip.
#   AIM     the aim frame, turned to the player every step until the aim latches.
#   RECOIL  the shot and its recoil, then the next AIM, or SETTLE after the last.
#   SETTLE  idle until no ball of his is left, settle_max at most.
# It teaches the parry. A parried ball fills half his Break gauge, a blocked one pays nothing, and one that
# lands costs half a heart and drains the gauge. His body's own Defense.parried connection credits the
# gauge; nothing here does. Each ball is its own BurakBossBallScript, and so its own hit source, and lands
# inside the i-frames: a hit from the first never swallows the second, or its parry.
# Every wait is a Physics_Update accumulator; the badge, the pips, the balls and the flashes are node-bound.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")
const BALL_SCENE := preload("res://Scenes/Bosses/BurakBossBallScene.tscn")

const SHOT_ID := &"burak_shot"

@export var body : CharacterBody2D

#KNOBS (seconds and px)
@export var return_speed := 1000.0
@export var return_max := 0.9
@export var bullets := 2
# One loop of burak_load, one bullet.
@export var bullet_time := 0.55
@export var aim_first := 0.40
@export var recoil := 0.30
@export var aim_second := 0.80
# The aim stops following the player this long before the shot.
@export var latch_lead := 0.12
@export var ball_speed := 750.0
# The least time a ball takes to reach the point it was aimed at.
@export var min_flight := 0.40
@export var hit_radius := 12.0
@export var settle_max := 1.5

@onready var state_machine = get_parent()

enum Beat { RETURN, LOAD, AIM, RECOIL, SETTLE }

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var beat := Beat.RETURN
var beat_clock := 0.0
var loaded := 0
var fired := 0
var latched := false
var aim_point := Vector2.ZERO
# Every ball this pair fired: the settle waits them out, and a test reads them.
var balls: Array = []
# For tests: the parries this Shots took, and the fight_clock of each release.
var parries := 0
var release_times: Array[float] = []


func Enter() -> void:
	released = false
	parries = 0
	release_times.clear()
	balls.clear()
	loaded = 0
	fired = 0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	if body.global_position.distance_to(state_machine.HOME) < 1.0:
		body.global_position = state_machine.HOME
		_load()
		return
	beat = Beat.RETURN
	beat_clock = 0.0
	body.face_toward(state_machine.HOME)
	body.play_anim(&"run")


func Exit() -> void:
	release()


# Leaving with his whole scene: the badge and the HUD it would tidy have left the tree already, and a
# tween can't start on them there.
func _exit_tree() -> void:
	released = true


# Idempotent: the badge, the pips and the hint go whichever way the pair ended. Balls still in flight
# belong to the hazard group, which a Break or the end of the fight clears.
func release() -> void:
	if released:
		return
	released = true
	if not is_instance_valid(body):
		return
	ParryTell.clear(body)
	body.hide_pips()
	body.hide_hint(&"parry")


func Physics_Update(delta: float) -> void:
	if released:
		return
	beat_clock += delta
	match beat:
		Beat.RETURN:
			_step_return(delta)
		Beat.LOAD:
			_step_load()
		Beat.AIM:
			_step_aim()
		Beat.RECOIL:
			if beat_clock >= recoil:
				beat_clock -= recoil
				if fired < bullets:
					_aim()
				else:
					_settle()
		Beat.SETTLE:
			if balls.all(func(ball): return not is_instance_valid(ball)) or beat_clock >= settle_max:
				state_machine.attack_done(self)


func _step_return(delta: float) -> void:
	var home: Vector2 = state_machine.HOME
	body.global_position = body.global_position.move_toward(home, return_speed * delta)
	if body.global_position == home or beat_clock >= return_max:
		body.global_position = home
		_load()


# The badge goes up with the pips and stays up through the last release.
func _load() -> void:
	beat = Beat.LOAD
	beat_clock = 0.0
	body.face_toward(state_machine.player_hurtbox_centre())
	body.play_anim(&"load", &"", bullet_time)
	body.show_pips(bullets)
	ParryTell.telegraph(body, SHOT_ID, _badge_time(), body.tell_anchor)


func _step_load() -> void:
	while loaded < bullets and beat_clock >= loaded * bullet_time + _pip_lead():
		body.load_pip(loaded)
		body.play_sfx(&"load_click")
		loaded += 1
	var load_time := bullets * bullet_time
	if beat_clock >= load_time:
		beat_clock -= load_time
		_aim()


func _aim() -> void:
	beat = Beat.AIM
	latched = false
	body.play_anim(&"fire_aim")


func _step_aim() -> void:
	var hold := aim_first if fired == 0 else aim_second
	if not latched:
		aim_point = state_machine.player_hurtbox_centre()
		latched = beat_clock >= hold - latch_lead
		body.face_toward(aim_point)
	if beat_clock >= hold:
		beat_clock -= hold
		_fire()


func _fire() -> void:
	beat = Beat.RECOIL
	body.play_anim(&"fire")
	var muzzle: Vector2 = body.muzzle_point(&"fire")
	_flash(muzzle)
	body.play_sfx(&"gunshot")
	body.spend_pip()
	var ball: Node2D = BALL_SCENE.instantiate()
	ball.max_speed = ball_speed
	ball.min_flight = min_flight
	ball.hit_radius = hit_radius
	ball.ropes = state_machine.ROPES
	ball.player = state_machine.get_player()
	ball.body = body
	ball.aim(muzzle, aim_point)
	ball.answered.connect(_on_ball_answered)
	state_machine.add_hazard(ball, muzzle, body.projectile_layer)
	balls.append(ball)
	release_times.append(body.fight_clock)
	fired += 1
	if fired == 1:
		body.show_hint(&"parry", "TAP %s AS THE SHOT HITS TO PARRY!" % InputSettings.label_for(&"block"))
	if fired == bullets:
		ParryTell.clear(body)


func _settle() -> void:
	beat = Beat.SETTLE
	beat_clock = 0.0
	body.play_state_anim(&"idle")


func _on_ball_answered(result: int) -> void:
	if result == HitInfo.Result.PARRIED:
		parries += 1


# The muzzle's flash and smoke on the drawn heading nearest the shot's. The smoke always rises, so it
# only ever flips left, and a shot aimed upward takes the level heading.
func _flash(at: Vector2) -> void:
	var spec := Layout.fx(&"muzzle")
	var line := aim_point - at
	var pick: Array = Layout.art_frame(Vector2(line.x, maxf(line.y, 0.0)), spec.headings)
	var flash := Sprite2D.new()
	flash.texture = load(spec.texture)
	flash.hframes = spec.hframes
	flash.scale = Vector2.ONE * Layout.SCALE
	flash.flip_h = pick[1]
	flash.offset = Layout.flipped_offset(spec.offset, pick[1], false)
	var first: int = pick[0] * spec.frames_per_heading
	flash.frame = first
	state_machine.add_hazard(flash, at, body.projectile_layer)
	var frame_time: float = spec.frame_time
	var play := flash.create_tween()
	for i in range(1, spec.frames_per_heading):
		play.tween_interval(frame_time)
		play.tween_callback(flash.set_frame.bind(first + i))
	play.tween_interval(frame_time)
	play.tween_callback(flash.queue_free)


# From the load's start to the last release.
func _badge_time() -> float:
	return bullets * bullet_time + aim_first + (bullets - 1) * (recoil + aim_second)


# How far into a bullet's loop of burak_load its last frame, the click that loads the pip, starts.
func _pip_lead() -> float:
	var times: Array = Layout.timed(Layout.anim(&"load"), bullet_time).times
	var lead := 0.0
	for i in times.size() - 1:
		lead += times[i]
	return lead
