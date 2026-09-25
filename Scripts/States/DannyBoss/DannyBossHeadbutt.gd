extends State

# His Sumo Headbutt (plan section 6), E. Honda's torpedo at a player his worms have rooted in Idle, the Spit
# or his nap (DannyBossStateMachine.on_player_rooted). Parry-only: a guard held through it doesn't stop it
# (AttackCatalog), and the root has taken the dash away.
#   REACT    react_time: the root clamps and he notices it; out of his nap he pops awake.
#   SLIDE    suriashi back to the launch spot, facing the player: launch_offset px beside them on the side
#            he is on, or the far side if WALK_RECT leaves that run under min_run. slide_time, or longer at
#            slide_max_speed. The spot is as low as his flying head has to be to meet the player's hurtbox,
#            since the torpedo is drawn far thicker than the player is tall - but never below WALK_RECT, nor
#            so high that his wind-up's badge leaves the screen.
#   WINDUP   windup_time crouched under the red badge, which stays up to the impact. The parry is rearmed.
#   FLIGHT   the launch frame, then the torpedo loop with its trail behind him, flight_time flat, his head
#            flying straight at the near edge of the player's hurtbox level with its middle (higher up that
#            edge at the bottom rope, to keep him on screen) - on a diagonal where the spot had to be
#            clamped - and the hit as it gets there.
#   RECOIL   he flips back flip_back px on a flip_arc arc over flip_time. Parried: bonked, the root bursts,
#            and he lands dizzy in Staggered for the stagger the parry handed him. Otherwise the root lets
#            go - a hit knocks the player on along his flight - and he lands into Idle.
# From the launch until he lands he draws BEHIND the player (_place), so the contact reads as contact, and
# he is back on his own y-sort once he is down. However it went, no puddle roots for ROOT_GRACE after
# (start_root_grace). Its parry's read is the gauge's own (DannyBossScript.BREAK_EARNS): nothing here
# credits it.

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/DannyBossArtLayout.gd")

const HEADBUTT_ID := &"danny_headbutt"
const HINT_KEY := &"headbutt"
const HINT_TEXT := "STUCK! TAP %s AS HE HITS TO PARRY!"
const SHAKE_STEPS := 3
const SHAKE_STEP_TIME := 0.03
# The impact clears the badge, and lands on a whole physics step, which can be one past windup_time +
# flight_time: the badge's own clock must not run out that step first.
const BADGE_SLACK := 0.05

@export var body : CharacterBody2D

#KNOBS (seconds and px)
@export var react_time := 0.15
@export var launch_offset := 560.0
@export var min_run := 360.0
@export var slide_time := 0.40
@export var slide_max_speed := 1800.0
# One pass of his step loop: 0.06 s a frame.
@export var slide_loop_time := 0.24
# The strong badge's height over its tip (DefenseHypeArtLayout's parry tell), kept on screen over the wind-up.
@export var badge_room := 108.0
@export var windup_time := 0.55
@export var flight_time := 0.22
@export var launch_shake := 4.0
@export var flip_back := 180.0
@export var flip_arc := 120.0
@export var flip_time := 0.45
@export var bonk_hit_stop := 0.08
@export var knock_back := 160.0
@export var knock_back_time := 0.20

@onready var state_machine = get_parent()

enum Beat { REACT, SLIDE, WINDUP, FLIGHT, RECOIL }

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var beat := Beat.REACT
var beat_clock := 0.0
var slide_from := Vector2.ZERO
var slide_length := 0.0
var launch_spot := Vector2.ZERO
# Where his head makes contact (_impact_point).
var impact_point := Vector2.ZERO
var flight_from := Vector2.ZERO
var flight_to := Vector2.ZERO
var recoil_from := Vector2.ZERO
var recoil_to := Vector2.ZERO
# From the launch until he lands: where his feet are drawn, and how far his node sits above them (_place).
var feet := Vector2.ZERO
var sink := 0.0
var trail: Sprite2D
var trail_rest := Vector2.ZERO
# -1 until the impact, then its HitInfo.Result.
var result := -1
# The stagger PlayerDefense hands a parried flight (parry_stagger), or below 0.
var stagger_time := -1.0
# For tests: the state the root cut short, and the fight_clock at the wind-up, the launch and the impact.
var from_state := ""
var windup_at := -1.0
var launch_at := -1.0
var impact_at := -1.0


func Enter() -> void:
	released = false
	result = -1
	stagger_time = -1.0
	sink = 0.0
	windup_at = -1.0
	launch_at = -1.0
	impact_at = -1.0
	# Still the state the root cut short: this one only becomes current once Enter returns.
	from_state = String(state_machine.current_state.name) if state_machine.current_state else ""
	beat = Beat.REACT
	beat_clock = 0.0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	_face_player()
	body.set_body_box(&"idle")
	if from_state == "Sleep":
		body.play_anim(&"wake")
		body.play_sfx(&"wake")


func Physics_Update(delta: float) -> void:
	if released:
		return
	beat_clock += delta
	match beat:
		Beat.REACT:
			if beat_clock >= react_time:
				_slide()
		Beat.SLIDE:
			_step_slide()
		Beat.WINDUP:
			if beat_clock >= windup_time:
				_launch()
		Beat.FLIGHT:
			_step_flight()
		Beat.RECOIL:
			_step_recoil()


func Exit() -> void:
	release()


# Idempotent, however it ended: a headbutt cut short before its impact still lets the player go and starts
# the grace, and one cut short in the air is put back down on his own feet and y-sort.
func release() -> void:
	if released:
		return
	released = true
	if not is_instance_valid(body):
		return
	ParryTell.clear(body)
	_clear_trail()
	if sink != 0.0:
		_unsink()
	body.set_lift(0.0)
	body.restore_hud()
	body.hide_hint(HINT_KEY)
	state_machine.release_root()
	if result < 0:
		state_machine.start_root_grace()


# Leaving with his whole scene: the badge, the trail and the HUD are going with it, and the root lets the
# player go on its own way out.
func _exit_tree() -> void:
	released = true


#THE PARRY (DannyBossScript relays PlayerDefense's calls here)

# Only the flight: the impact asks while it is still flying.
func can_parry_stagger(_hit: RefCounted) -> bool:
	return not released and beat == Beat.FLIGHT


# Deferred by PlayerDefense, so it lands once the parried impact has already turned him into his flip back.
func parry_stagger(duration: float) -> void:
	if released or result != HitInfo.Result.PARRIED:
		return
	stagger_time = duration


#THE BEATS

func _slide() -> void:
	beat = Beat.SLIDE
	beat_clock = 0.0
	slide_from = body.global_position
	launch_spot = _launch_spot()
	slide_length = maxf(slide_time, slide_from.distance_to(launch_spot) / slide_max_speed)
	body.play_anim(&"step", &"", slide_loop_time)


func _step_slide() -> void:
	var weight := minf(beat_clock / slide_length, 1.0)
	body.global_position = slide_from.lerp(launch_spot, weight).round()
	_face_player()
	if weight >= 1.0:
		_wind_up()


func _wind_up() -> void:
	beat = Beat.WINDUP
	beat_clock = 0.0
	windup_at = body.fight_clock
	_face_player()
	body.play_anim(&"headbutt_windup")
	ParryTell.telegraph(body, HEADBUTT_ID, windup_time + flight_time + BADGE_SLACK, body.tell_anchor)
	# ALWAYS, at the start of every tell: a press that whiffed earlier must never make this one unanswerable.
	state_machine.rearm_parry()
	body.play_sfx(&"headbutt_charge")
	body.update_hud_fade(&"headbutt_windup")
	body.show_hint(HINT_KEY, HINT_TEXT % InputSettings.label_for(&"block"))


func _launch() -> void:
	beat = Beat.FLIGHT
	beat_clock = 0.0
	launch_at = body.fight_clock
	flight_from = body.global_position
	impact_point = _impact_point(body.sprite.flip_h)
	flight_to = impact_point - _head_local(body.sprite.flip_h)
	body.play_anim(&"headbutt_launch", &"headbutt_fly")
	body.play_sfx(&"headbutt_launch")
	ScreenView.shake(get_tree(), launch_shake, SHAKE_STEPS, SHAKE_STEP_TIME)
	_show_trail()
	_place(flight_from)


func _step_flight() -> void:
	var weight := minf(beat_clock / flight_time, 1.0)
	_place(flight_from.lerp(flight_to, weight))
	if is_instance_valid(trail):
		var frame_time: float = Layout.fx(&"headbutt_trail").frame_time
		trail.frame = int(beat_clock / frame_time) % trail.hframes
	if weight >= 1.0:
		_impact()


func _impact() -> void:
	impact_at = body.fight_clock
	ParryTell.clear(body)
	_clear_trail()
	var player: Node2D = state_machine.get_player()
	result = HitInfo.Result.IGNORED
	if player:
		result = player.receive_hit(HitInfo.make(HEADBUTT_ID, self, state_machine.player_hurtbox_centre(), body))
	# A hit that ended the fight has handed it on already.
	if released:
		return
	state_machine.start_root_grace()
	body.restore_hud()
	body.hide_hint(HINT_KEY)
	if result == HitInfo.Result.PARRIED:
		body.play_anim(&"headbutt_bonk", &"headbutt_recoil")
		body.play_sfx(&"headbutt_bonk")
		body.play_sfx(&"root_burst")
		HitStop.freeze(get_tree(), bonk_hit_stop)
		state_machine.release_root()
	else:
		body.play_anim(&"headbutt_recoil")
		state_machine.release_root()
		if result == HitInfo.Result.HIT:
			body.play_sfx(&"headbutt_hit")
			_knock_back(player)
	_flip_back()


func _flip_back() -> void:
	beat = Beat.RECOIL
	beat_clock = 0.0
	var back := 1.0 if body.sprite.flip_h else -1.0
	var walk: Rect2 = state_machine.WALK_RECT
	recoil_from = feet
	recoil_to = (feet + Vector2(back * flip_back, 0.0)).clamp(walk.position, walk.end)


func _step_recoil() -> void:
	var weight := minf(beat_clock / flip_time, 1.0)
	_place(recoil_from.lerp(recoil_to, weight), 4.0 * flip_arc * weight * (1.0 - weight))
	if weight < 1.0:
		return
	_unsink()
	if result == HitInfo.Result.PARRIED:
		state_machine.states["Staggered"].window = maxf(stagger_time, 0.0)
		state_machine.on_child_transition(self, "Staggered")
	else:
		state_machine.attack_done(self)


#WHERE HE GOES

# launch_offset px beside the player on the side he's on, or the far side if WALK_RECT leaves that run under
# min_run; as low as his flying head must be to meet the player's hurtbox, within what keeps his wind-up in
# the ring and its badge on screen.
func _launch_spot() -> Vector2:
	var target: Vector2 = state_machine.player_hurtbox_centre()
	var side := -1.0 if body.global_position.x < target.x else 1.0
	var x := _run_up_x(target.x, side)
	if absf(x - target.x) < min_run:
		side = -side
		x = _run_up_x(target.x, side)
	var level := target.y - _head_local(side > 0.0).y
	return Vector2(x, clampf(level, _highest_launch(), state_machine.WALK_RECT.end.y)).round()


func _run_up_x(from_x: float, side: float) -> float:
	var walk: Rect2 = state_machine.WALK_RECT
	return clampf(from_x + side * launch_offset, walk.position.x, walk.end.x)


# The highest his feet may stand for the wind-up: the badge over its crown just inside the screen's top.
func _highest_launch() -> float:
	var crown: Vector2 = Layout.texel_local(Layout.crown(&"headbutt_windup"), &"headbutt_windup")
	return maxf(state_machine.WALK_RECT.position.y, badge_room + Layout.TELL_GAP - crown.y)


# The front of his head in flight, from his feet, flying left when flipped.
func _head_local(flipped: bool) -> Vector2:
	return Layout.texel_local(Layout.head(&"headbutt_fly"), &"headbutt_fly", flipped)


# On the player's near edge, level with its middle - but never so low that his feet leave the screen, since the
# launch and bonk frames reach down to them. Against the bottom rope his head meets them higher up; at the
# lowest the ring lets them stand, just over the top of their hurtbox.
func _impact_point(flipped: bool) -> Vector2:
	var box := _player_box()
	var lowest := ScreenView.VIEW_SIZE.y + _head_local(flipped).y
	return Vector2(box.end.x if flipped else box.position.x, minf(box.get_center().y, lowest))


func _player_box() -> Rect2:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return Rect2(state_machine.HOME, Vector2.ZERO)
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


# Along his flight, the player's hurtbox kept inside the ropes.
func _knock_back(player: Node2D) -> void:
	var box := _player_box()
	var ropes: Rect2 = state_machine.ROPES
	var along := -1.0 if body.sprite.flip_h else 1.0
	var to_x := clampf(box.get_center().x + along * knock_back, ropes.position.x + box.size.x / 2.0, ropes.end.x - box.size.x / 2.0)
	state_machine.drive_player_to(player.global_position + Vector2(to_x - box.get_center().x, 0.0), knock_back_time)


func _face_player() -> void:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return
	body.face_toward(player.global_position)
	state_machine.face_player_at(body.global_position)


#DRAWN BEHIND THE PLAYER

# His feet drawn at `at` and `arc` px up, with his node - what the fight's y-sort orders him by - no lower
# than just over the player's sprite, and his lift putting his drawing back down where it belongs. His
# points all take the lift off, so his head, crown and badge stay where they are drawn.
func _place(at: Vector2, arc := 0.0) -> void:
	feet = at.round()
	var node := Vector2(feet.x, minf(feet.y, _sort_line()))
	sink = feet.y - node.y
	body.global_position = node
	body.set_lift(roundf(arc) - sink)
	if is_instance_valid(trail):
		trail.position = trail_rest + Vector2(0.0, sink)


# Down on his own feet and his own y-sort.
func _unsink() -> void:
	body.global_position = feet
	sink = 0.0
	body.set_lift(0.0)


# A pixel over the player's sprite's origin, which is where the y-sort puts them.
func _sort_line() -> float:
	var player: Node2D = state_machine.get_player()
	if player == null:
		return INF
	return floorf(player.to_global(player.sprite_base_position).y) - 1.0


#THE TRAIL

# Behind his body, its pivot on the back of his flight box level with its middle, flipped with him.
func _show_trail() -> void:
	_clear_trail()
	var spec: Dictionary = Layout.fx(&"headbutt_trail")
	var box := Layout.body_rect(&"headbutt")
	trail = Sprite2D.new()
	trail.texture = load(spec.texture)
	trail.hframes = spec.hframes
	trail.scale = Vector2.ONE * Layout.SCALE
	trail.flip_h = body.sprite.flip_h
	trail.offset = Layout.flipped_offset(spec.offset, trail.flip_h)
	trail_rest = Vector2(-box.position.x if trail.flip_h else box.position.x, box.get_center().y)
	trail.position = trail_rest
	body.add_child(trail)
	body.move_child(trail, body.sprite.get_index())


func _clear_trail() -> void:
	if is_instance_valid(trail):
		trail.queue_free()
	trail = null
