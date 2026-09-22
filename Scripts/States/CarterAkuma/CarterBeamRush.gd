extends State

# Carter's second attack, the Beam Rush, beats 0 to 3 in a single state:
#   SUMMON  0.70 s  four clones gather across the top of the ring, one to a lane divider.
#   CHARGE  0.45 s  each one brings its curtain of light up. This is the whole warning the curtains
#                   give and the only chance to step out of a lane, so nothing hurts until it ends.
#   RUSH   ~6.00 s  twelve strikes, 0.50 s apart. Each one: he materialises beside the player with a
#                   red badge over his head, holds it for the 0.36 s read, then covers the gap and
#                   hits. A parry - and only a parry - feeds his Break gauge, and the full gauge is
#                   the only thing that ends this early. The curtains stand still through all of it.
#   END     0.40 s  the curtains go out, the four dissolve, and he is left standing there spent.
#
# IF THE PLAYER NEVER PARRIES THEY DIE, AND THAT IS THE DESIGN RATHER THAN A GAP IN IT. There is no
# timeout, no passive fill and no other escape hatch, because every one of them would undercut it: he
# always arrives beside them and always tracks them, so a controller put down is about seven seconds
# from the loss screen. The exit is a count of strikes, not a clock - see CarterStateMachine, which
# has the arithmetic for why.
#
# THE PLAYER IS NOT LOCKED HERE, unlike the barrage. The Raging Demon is the locked, parry-only
# attack; if this one locked too the pair would read as one attack with different scenery, and the
# curtains could never touch anyone. Free movement is what makes the curtains exist at all, and it is
# what gives the strike a real second answer: a sidestep. Sidestepping feeds the gauge nothing,
# though, so the player who only ever walks eats all twelve strikes and earns the short window.
#
# IT IS ONE STATE ON PURPOSE, for the reason RagingDemon is one: the curtains, the four clones, the
# per-strike hit sources and the badge over his head have to be taken and given back as a unit, and a
# single release() funnel is the only way every failure path - a win, a loss, a finisher, a scene
# change - is provably safe. Do not split it into beats.
#
# FREEZE SAFETY: every wait here is a Physics_Update accumulator and every ramp a node-bound tween,
# both of which a finisher's FightFreeze stops with the rest of the fight. Nothing here may use
# get_tree().create_timer() or a tree-level create_tween(): a hit-stop has to hold four live curtains
# and a Carter halfway through a teleport, and the window this hands over to is one a finisher starts
# in. Neither of those is theoretical.

const CarterArtLayout := preload("res://Scripts/CarterArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")

const STRIKE_ID := &"carter_teleport_strike"
const BEAM_ID := &"carter_beam"

# How far inside the ropes he may materialise.
const WARP_MARGIN := 90.0
# He pulls up this far short of the point he latched onto, so the blow lands beside the player rather
# than with him standing inside them.
const LUNGE_STANDOFF := 96.0
# The badge sits here over his feet. NOT get_daze_anchor(), which is tuned for the kneeling recovery
# pose and would put it in the middle of his chest while he is standing.
const TELL_ANCHOR := Vector2(0, -300)
# The four gather one after another rather than all at once, so the ring fills from one side.
const CLONE_FORM_TIME := 0.22
const CLONE_FORM_STAGGER := 0.08
const CLONE_GO_TIME := 0.18

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { SUMMON, CHARGE, RUSH, END }

var beat := Beat.SUMMON
var beat_clock := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# Whether the gauge filled, which is what decides the length of the window this hands over to.
var broke := false

var clones: Array[Node2D] = []
var clone_clock := 0.0
var beams: Array[Node2D] = []
var beam_clock := 0.0
# The curtains only hurt once they are fully up. Until then they are the tell for themselves.
var beams_live := false

var strike_index := -1
var strike_clock := 0.0
var strike_shown := false
var strike_landed := false
# Where he came in, and the point the strike was latched to when the badge came down.
var strike_from := Vector2.ZERO
var strike_point := Vector2.ZERO
# Which side of the player he is on: +1 their right, -1 their left. It flips every strike.
var strike_side := 1.0
# One bare marker per strike, kept until the attack ends.
var sources: Array[Node2D] = []


func Enter() -> void:
	released = false
	broke = false
	beat = Beat.SUMMON
	beat_clock = 0.0
	clone_clock = 0.0
	beam_clock = 0.0
	beams_live = false
	strike_index = -1
	strike_clock = 0.0
	strike_shown = false
	strike_landed = false
	strike_side = 1.0 if randi() % 2 == 0 else -1.0

	body.velocity = Vector2.ZERO
	body.show_body(true)
	# His emblem stays out for this one: its offset is measured on the frame where his back is turned,
	# and every pose here faces the player.
	body.show_mark_glow(false)
	body.play_anim(&"summon")
	body.flash_sfx_player.play()
	_reset_gauge()
	body.show_break_gauge(true)
	_build_clones()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent, and called from Exit(), _exit_tree() and CarterStateMachine._end_fight(). A terminal
# path that skips Exit() would otherwise leave four curtains standing and a red badge over a boss who
# has already lost the fight.
func release() -> void:
	if released:
		return
	released = true
	beams_live = false
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.show_body(true)
		body.show_mark_glow(false)
		body.sprite.flip_h = false
		body.show_break_gauge(false)
	_free_all(beams)
	_free_all(clones)
	_free_all(sources)


func Physics_Update(delta: float) -> void:
	_step_clones(delta)
	_step_beams(delta)
	if beams_live:
		_beam_contact()
	beat_clock += delta
	match beat:
		Beat.SUMMON:
			if beat_clock >= state_machine.beam_summon:
				_begin_charge()
		Beat.CHARGE:
			if beat_clock >= state_machine.beam_charge:
				_begin_rush()
		Beat.RUSH:
			_advance_rush(delta)
		Beat.END:
			if beat_clock >= state_machine.beam_end:
				_hand_over()


#THE GAUGE
# It is a PER-ATTACK meter, not a fight-long one: every rush starts from empty and every rush takes
# fills again, so the Break the last one ended on must not still be holding it shut.

func _reset_gauge() -> void:
	var gauge: Node = body.break_gauge
	if gauge == null:
		return
	gauge.value = 0.0
	gauge.locked = false
	gauge.changed.emit(0.0, gauge.max_value)


# His Break, deferred here from CarterAkumaScript._on_break through the state machine. The gauge
# fills inside a physics flush, where states cannot switch.
func on_broke() -> void:
	if released or beat != Beat.RUSH:
		return
	broke = true
	_begin_end()


#THE FOUR AT THE TOP
# Scenery, and only scenery: no light over the head, no hurtbox, no strike, nothing to punch, and
# nothing the player is ever asked to read. This fight already teaches one clone vocabulary - red
# parry, yellow feint - and a second, contradictory one would poison the first. They are full size
# rather than the barrage's 48x48 halflings for exactly that reason: at a glance they cannot be
# mistaken for the things that rush you.

func _build_clones() -> void:
	var art := CarterArtLayout.beam_clone()
	var sheet: Texture2D = load(art.sheet)
	for i in CarterArtLayout.BEAM_COUNT:
		var clone := Sprite2D.new()
		clone.texture = sheet
		clone.hframes = roundi(sheet.get_width() / CarterArtLayout.FRAME_SIZE.x)
		clone.offset = CarterArtLayout.sheet_offset(CarterArtLayout.FRAME_SIZE)
		clone.scale = Vector2.ONE * CarterArtLayout.SCALE
		clone.frame = art.frames[0]
		clone.z_index = CarterArtLayout.BEAM_CLONE_Z
		# The final sheet will be authored in its own colour; only the stand-in is tinted.
		if not CarterArtLayout.USE_FINAL_BEAM_CLONE:
			clone.modulate = CarterArtLayout.BEAM_CLONE_TINT
		var rest: float = clone.modulate.a
		clone.modulate.a = 0.0
		state_machine.add_hazard(clone, Vector2(CarterArtLayout.BEAM_X[i], CarterArtLayout.BEAM_CLONE_Y), body.clone_layer)
		clones.append(clone)
		var form := clone.create_tween()
		form.tween_interval(i * CLONE_FORM_STAGGER)
		form.tween_property(clone, "modulate:a", rest, CLONE_FORM_TIME)


# One clock for all four: they hold the same pose, so there is nothing to stagger once they are up.
func _step_clones(delta: float) -> void:
	var art := CarterArtLayout.beam_clone()
	var frames: Array = art.frames
	if clones.is_empty() or frames.size() < 2:
		return
	clone_clock += delta
	var step := _looped_step(art.times, frames.size(), clone_clock)
	for clone in clones:
		if is_instance_valid(clone):
			clone.frame = frames[step]


# Which of `count` frames `clock` has reached, `times` repeating its last value the way every
# animation in CarterArtLayout does.
func _looped_step(times: Array, count: int, clock: float) -> int:
	var loop := 0.0
	for i in count:
		loop += times[mini(i, times.size() - 1)]
	var into := fposmod(clock, maxf(loop, 0.0001))
	var end := 0.0
	for i in count:
		end += times[mini(i, times.size() - 1)]
		if into < end:
			return i
	return count - 1


#THE FOUR CURTAINS
# STATIC, VERTICAL AND UNCHANGING FOR THE WHOLE ATTACK. They do not sweep and they do not pulse:
# PlayerDefense.block_move_speed_ratio is 0.0, so a player holding the guard for the parry is ROOTED,
# and a moving curtain would ask the player who committed to the read to dodge something they
# physically cannot move away from. They are lanes to stand in, never a dodge.
# There is no Area2D and no "enemy projectile" group, exactly as CarterCloneScript documents for the
# clones: contact is a rect the sequence owns, tested per physics step. Each curtain is its own node
# and so its own hit source.

func _build_beams() -> void:
	var spec := CarterArtLayout.beam()
	var height: float = CarterArtLayout.BEAM_BOTTOM_Y - CarterArtLayout.BEAM_TOP_Y
	for i in CarterArtLayout.BEAM_COUNT:
		var curtain := Node2D.new()
		curtain.z_index = CarterArtLayout.BEAM_Z
		curtain.modulate.a = 0.0
		_draw_curtain(curtain, spec, height)
		state_machine.add_hazard(curtain, Vector2(CarterArtLayout.BEAM_X[i], CarterArtLayout.BEAM_TOP_Y), body.clone_layer)
		beams.append(curtain)
		var light := curtain.create_tween()
		light.tween_property(curtain, "modulate:a", 1.0, state_machine.beam_charge)


# Drawn from the curtain's own top-centre downward, as light.
func _draw_curtain(curtain: Node2D, spec: Dictionary, height: float) -> void:
	if spec.has("texture"):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.centered = false
		sheet.offset = Vector2(-spec.frame_size.x / 2.0, 0)
		sheet.scale = Vector2.ONE * spec.scale
		sheet.material = CarterArtLayout.additive()
		curtain.add_child(sheet)
		return
	for part in [
		[CarterArtLayout.BEAM_DRAW_WIDTH, spec.color],
		[spec.core_width, spec.core_color],
	]:
		var width: float = part[0]
		var quad := Polygon2D.new()
		quad.polygon = CarterArtLayout.rect_polygon(Rect2(-width / 2.0, 0.0, width, height))
		quad.color = part[1]
		quad.material = CarterArtLayout.additive()
		curtain.add_child(quad)


# The drawn curtain's own loop. The placeholder is two flat quads with nothing to step.
func _step_beams(delta: float) -> void:
	var spec := CarterArtLayout.beam()
	if beams.is_empty() or not spec.has("texture"):
		return
	beam_clock += delta
	var frame: int = int(beam_clock / float(spec.frame_time)) % int(spec.hframes)
	for curtain in beams:
		if is_instance_valid(curtain):
			(curtain.get_child(0) as Sprite2D).frame = frame


# An axis-aligned test against the player's own hurtbox, per curtain, per physics step. Skipped
# outright while they are flashing: carter_beam does not bypass the i-frames, so reporting into them
# would only be noise.
func _beam_contact() -> void:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player) or player.is_invincible:
		return
	var box := _player_box(player)
	for i in beams.size():
		var curtain: Node2D = beams[i]
		if not is_instance_valid(curtain):
			continue
		var hurts := CarterArtLayout.beam_rect(CarterArtLayout.BEAM_X[i], CarterArtLayout.BEAM_HIT_WIDTH)
		if not hurts.intersects(box):
			continue
		player.receive_hit(HitInfo.make(BEAM_ID, curtain, box.get_center(), body))
		return


func _fade_curtains() -> void:
	for curtain in beams:
		if not is_instance_valid(curtain):
			continue
		var out := curtain.create_tween()
		out.tween_property(curtain, "modulate:a", 0.0, state_machine.beam_end)
	for clone in clones:
		if not is_instance_valid(clone):
			continue
		var gone := clone.create_tween()
		gone.tween_property(clone, "modulate:a", 0.0, CLONE_GO_TIME)


#THE BEATS

func _begin_charge() -> void:
	beat = Beat.CHARGE
	beat_clock = 0.0
	_build_beams()
	body.dark_sfx_player.play()


func _begin_rush() -> void:
	beat = Beat.RUSH
	beat_clock = 0.0
	# Only now. The charge is the curtains' entire warning, and 0.45 s against 600 px/s of walking is
	# 270 px - enough to leave any lane from the middle of it - so a player standing where one comes
	# up is never hit by its arrival.
	beams_live = true
	strike_index = -1
	_next_strike()


func _advance_rush(delta: float) -> void:
	strike_clock += delta
	if not strike_shown and strike_clock >= state_machine.strike_show:
		strike_shown = true
		_launch_strike()
	if strike_shown and not strike_landed:
		_drive_lunge()
		if strike_clock >= state_machine.strike_show + state_machine.strike_dash:
			strike_landed = true
			_contact()
	if strike_clock < state_machine.strike_period():
		return
	if strike_index + 1 >= state_machine.strike_cap:
		_begin_end()
	else:
		_next_strike()


func _begin_end() -> void:
	beat = Beat.END
	beat_clock = 0.0
	beams_live = false
	ParryTell.clear(body)
	_fade_curtains()
	body.sprite.flip_h = false
	body.play_anim(&"idle")
	body.finish_sfx_player.play()


func _hand_over() -> void:
	var recover: State = state_machine.states.get("Recover")
	if recover:
		# Nothing is banked here: what a rush read well earns is the long window, and prepare() zeroes
		# the barrage's own tally so its banked damage cannot be cashed in a second time.
		recover.prepare(0, 0, 0, 0,
			state_machine.recover_break if broke else state_machine.recover_spent)
	state_machine.on_child_transition(self, "Recover")


#ONE STRIKE

func _next_strike() -> void:
	strike_index += 1
	strike_clock = 0.0
	strike_shown = false
	strike_landed = false
	# The side flips every time, so he is never twice running on the same shoulder.
	strike_side = -strike_side

	var player: Node2D = state_machine.get_player()
	var at: Vector2 = player.global_position if is_instance_valid(player) else state_machine.ARENA_CENTRE
	body.global_position = _warp_spot(at)
	strike_from = body.global_position
	body.play_anim(&"rush")
	_face_player()
	body.play_rush(strike_index)
	# The badge comes up on the frame he does, and the parry is re-armed on that same frame, all
	# twelve, every rush. At a 0.50 s period - exactly PlayerDefense.parry_mash_lockout - this is what
	# keeps a press that whiffed on strike N from making strike N+1 unparryable. It is load-bearing,
	# not a safety net.
	ParryTell.telegraph(body, STRIKE_ID, state_machine.strike_show, _tell_anchor)
	state_machine.rearm_parry()


# Beside the player, on the opposite side from last time, jittered off their line and always inside
# the ropes.
func _warp_spot(at: Vector2) -> Vector2:
	var bounds: Rect2 = state_machine.ROPES.grow(-WARP_MARGIN)
	var reach := randf_range(state_machine.strike_range.x, state_machine.strike_range.y)
	var y: float = at.y + randf_range(-state_machine.strike_y_jitter, state_machine.strike_y_jitter)
	var spot := Vector2(at.x + strike_side * reach, y).clamp(bounds.position, bounds.end)
	# Against the ropes the clamp can drop him in their lap, so the SIDE gives way rather than the
	# distance: he is meant to arrive a read away, never already on top of them.
	if absf(spot.x - at.x) < state_machine.strike_range.x:
		strike_side = -strike_side
		spot = Vector2(at.x + strike_side * reach, y).clamp(bounds.position, bounds.end)
	return spot.round()


# Both rush sheets are drawn travelling right, so the strike from the player's right mirrors them.
func _face_player() -> void:
	body.sprite.flip_h = strike_side > 0.0


# The badge comes down and the lunge starts. The destination is LATCHED here, on the player's hurtbox
# centre this frame, and nothing moves it afterwards - the same rule ComputahBeam._lock() works by.
# What the player does with the 0.08 s after this is the whole of their second answer.
func _launch_strike() -> void:
	ParryTell.clear(body)
	strike_point = _player_centre()
	body.play_anim(&"rush_pass")
	_face_player()


func _drive_lunge() -> void:
	var weight := clampf((strike_clock - state_machine.strike_show) / maxf(state_machine.strike_dash, 0.0001), 0.0, 1.0)
	var toward := strike_point + Vector2(strike_side * LUNGE_STANDOFF, 0.0)
	body.global_position = strike_from.lerp(toward, weight).round()


# The contact instant. The player is free to move here, so a strike can WHIFF: if they are no longer
# inside the box around the point it latched onto, nothing lands and nothing feeds the gauge. That is
# the second answer, and it is why walking out of strikes does not end the attack.
# The hit's origin is the player's own hurtbox centre, inside PlayerDefense.block_omni_radius, so any
# facing answers it: this is a timing check, not an aiming one.
func _contact() -> void:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player):
		return
	var centre := _player_centre()
	var reach: float = state_machine.strike_reach
	if absf(centre.x - strike_point.x) > reach or absf(centre.y - strike_point.y) > reach:
		return
	var result: int = player.receive_hit(HitInfo.make(STRIKE_ID, _strike_source(centre), centre, body))
	if result == HitInfo.Result.PARRIED:
		body.break_sfx_player.play()
	elif result != HitInfo.Result.IGNORED:
		body.strike_sfx_player.play()


# A bare marker per strike, kept until the attack ends. PlayerDefense holds absorbed_until per SOURCE
# for blocked_rehit_interval (1.0 s) and the strikes come 0.50 s apart, so one shared source would
# make every strike after a blocked one free - the exact trap CarterCloneScript's header warns about.
func _strike_source(at: Vector2) -> Node2D:
	var marker := Node2D.new()
	body.clone_layer.add_child(marker)
	marker.global_position = at.round()
	sources.append(marker)
	return marker


func _player_centre() -> Vector2:
	var player: Node2D = state_machine.get_player()
	if not is_instance_valid(player):
		return body.global_position
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position


func _player_box(player: Node2D) -> Rect2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var size: Vector2 = (shape.shape as RectangleShape2D).size * shape.global_scale
	return Rect2(shape.global_position - size / 2.0, size)


func _tell_anchor() -> Vector2:
	return body.global_position + TELL_ANCHOR


func _free_all(nodes: Array[Node2D]) -> void:
	for node in nodes:
		if is_instance_valid(node):
			node.queue_free()
	nodes.clear()
