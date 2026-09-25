extends State

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")

@export var body : CharacterBody2D
@export var recover_timer : Timer
@export var recover_sfx_player : AudioStreamPlayer

@onready var state_machine = get_parent()

# Handed over by the attack that ended, through prepare(), and read once here.
var reds_parried := 0
var reds_missed := 0
var feints_parried := 0
var reds_total := 0
# The window in seconds when the attack decides it itself, or negative to earn it from the tally
# above. The Beam Rush sets it: what it earned is a Break, not a count of parried reds.
var window_override := -1.0
# Whether this window cashes a Break. It has no state of its own: it is this one, at least his
# BREAK.broken_time long, and it pays the tiered finisher (CarterAkumaScript.can_be_juggled).
var from_break := false

# A Break cashed too high in the ring for a full juggle to be drawn over him first takes him away and
# brings him back lower: the clock on that, and where he comes back.
var dropping := false
var drop_clock := 0.0
var drop_back := false
var drop_to := Vector2.ZERO


# EVERY attack hands over through here, and never by writing the fields directly. The tally below is
# plain state that survives the state being left, so an attack that set only some of it would cash in
# the previous attack's banked damage on top of its own.
func prepare(parried: int, missed: int, feints: int, total: int, window := -1.0, broke := false) -> void:
	reds_parried = parried
	reds_missed = missed
	feints_parried = feints
	reds_total = total
	window_override = window
	from_break = broke


# The punish window: the only place punches reach him. How long it lasts is what the round earned -
# a parry's real reward is this, not the chip damage below.
# Gating his hurtbox to this state survives feel_v2's punch, which resolves at arm extension rather
# than on his report: a swing keeps retrying every frame until it ends, so a punch pressed up to 21
# frames (0.35 s) before the window opens still lands, against V1's 22. One frame of a 22-frame
# swing is the whole cost of the change.
func Enter() -> void:
	body.hits_this_window = 0
	body.daze_used = false
	body.velocity = Vector2.ZERO
	body.show_body(true)
	body.play_anim(&"recover")
	# Before the hurtbox opens. Parries are banked and cashed here rather than applied as they land,
	# because a hit resolving mid-sequence would fire flinch() or the whole defeat sequence with the
	# player still locked and the arena still dark. is_recovering() is false until Enter() returns,
	# so this shows his hit flash without the recoil frame fighting the recovery pose.
	var banked := banked_damage()
	if banked > 0:
		body._apply_damage(banked)
	dropping = false
	drop_to = _drop_spot() if from_break else body.global_position
	if drop_to != body.global_position:
		_begin_drop()
		return
	_open()


func Exit() -> void:
	dropping = false
	body.set_hurtbox_active(false)


# His vanish, then his reappear on the spot, then the window - the whole of it, from when he is back.
func Physics_Update(delta: float) -> void:
	if not dropping:
		return
	drop_clock += delta
	var gone := _anim_length(&"ko_vanish")
	if not drop_back and drop_clock >= gone:
		drop_back = true
		body.global_position = drop_to
		body.play_anim(&"ko_reappear", &"recover")
	elif drop_back and drop_clock >= gone + _anim_length(&"ko_reappear"):
		dropping = false
		_open()


# Punches can reach him from here, and the window starts.
func _open() -> void:
	body.set_hurtbox_active(true)
	recover_sfx_player.play()
	var window: float = window_override if window_override > 0.0 else state_machine.recover_window(reds_parried, reds_missed)
	if from_break:
		window = maxf(window, body.BREAK.broken_time)
	recover_timer.start(window)


# A Break window needs his feet on or under the line a full juggle can be thrown from (the Juggled
# state's floor_y()). Above it - a Beam Rush broken beside a player up by the top rope, a Messatsu fired
# from the top of its area - he comes back on that line: in his own column if that leaves the player a
# clear gap, else that gap across from them, and inside the ropes.
func _drop_spot() -> Vector2:
	var line := ceilf(state_machine.states["Juggled"].floor_y())
	var here: Vector2 = body.global_position
	if here.y >= line:
		return here
	var bounds: Rect2 = state_machine.ROPES.grow(-state_machine.BREAK_ROPE_MARGIN)
	var spot := Vector2(here.x, line).clamp(bounds.position, bounds.end)
	var player: Node2D = state_machine.get_player()
	if player:
		var gap: float = state_machine.BREAK_PLAYER_GAP
		var px := player.global_position.x
		if absf(spot.x - px) < gap:
			var side := 1.0 if spot.x >= px else -1.0
			spot.x = px + side * gap
			if spot.x < bounds.position.x or spot.x > bounds.end.x:
				spot.x = px - side * gap
	return spot.clamp(bounds.position, bounds.end).round()


# His own teleport, the KO's quick pair, and his warp's sound; nothing can reach him until he is back.
func _begin_drop() -> void:
	dropping = true
	drop_clock = 0.0
	drop_back = false
	body.play_anim(&"ko_vanish")
	body.yank_sfx_player.play()


func _anim_length(anim_name: StringName) -> float:
	return CarterArtLayout.time_to_step(anim_name, CarterArtLayout.anim(anim_name).frames.size())


# One half-heart per bank_per_parries reds stopped, and a bonus on top for a barrage with every red
# stopped and no feint bitten on. Fifteen clones is roughly ten seconds of standing still, so a
# barrage read well is worth several times what the old five-clone one was.
func banked_damage() -> int:
	var banked := reds_parried / maxi(state_machine.bank_per_parries, 1)
	if reds_total > 0 and reds_parried >= reds_total and feints_parried == 0:
		banked += state_machine.bank_perfect_bonus
	return banked


func flinch() -> void:
	body.play_anim(&"hit", &"recover")


func _on_recover_timer_timeout() -> void:
	state_machine.on_child_transition(self, "Idle")
