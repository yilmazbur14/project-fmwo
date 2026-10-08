extends State

# The Nugget Fastball (the user's pick, 2026-10-04; scratchpad plan mason_fastball/PLAN.md): once a cycle, after his
# attack, Mason pitches nuggets at the player. Seconds are [phase 1, phase 2]; t = 0 is the SET, when the mark goes up.
#   READY        ready_time, once a set: he calls his shot, facing the player.
#   a slot each, in the set's order:
#   FASTBALL     windup_time (STRETCH then KICK), then the SET under the strong red badge; the ball leaves his hand
#                release_after later and reaches the player fastball_flight after that: contact at +0.42.
#   CHANGEUP     change_windup_time rocking (its own tell, before any badge), the same badge at the SET and the same
#                release, then a changeup_flight lob: contact at +0.64. Pressed at a fastball's timing it whiffs.
#   HESITATION   the fastball's wind-up to the frame, then Carter's pale X instead of the badge for feint_show; he
#                pump-fakes where a fastball would leave his hand. Left alone: a hitch_time hitch, then the red badge
#                and a real fastball. A press while the X is up (a bite) costs feint_stamina inside the press, ends
#                both streaks, puts up FEINT! and lights his hand: quick_delay later a quick pitch nothing answers.
#   RECOVER      recover_time after each contact, or long enough for a home run's return and his bonk.
# The ball is aimed where the player is heading as it leaves his hand (their velocity capped at aim_lead_cap, times
# its flight), so walking away doesn't take them out of it; it can only hurt around its contact (live_lead,
# live_tail), and its origin is the player's own hurtbox centre, so any facing parries it. A parried ball is a HOME
# RUN: batted back into his head for home_run_chip, and knockdown_streak in a row knock him into his Break.
# Every wait runs off one clock (pause and hit-stop hold it), and everything it puts up goes through one idempotent
# release(), which Exit(), _exit_tree() and MasonStateMachine._stop_everything() call.

const MasonArtLayout := preload("res://Scripts/MasonArtLayout.gd")
const MasonPitchBall := preload("res://Scripts/MasonPitchBall.gd")
const MasonBroken := preload("res://Scripts/States/Mason/MasonBroken.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

enum Beat { READY, WINDUP, SET, FLIGHT, RECOVER, PUMP, HITCH, BITTEN, DONE }

const FASTBALL := &"fastball"
const CHANGEUP := &"changeup"
const HESITATION := &"hesitation"
const QUICK := &"quick"
# Summed steps land a hair short of a scheduled time, which would start its beat a step late.
const STEP_TOLERANCE := 0.0001
# The red badge is cleared at its contact; given this much longer, it never runs out a step early.
const BADGE_SLACK := 0.1
# The share of a fastball's wind-up spent in STRETCH before KICK.
const STRETCH_SHARE := 0.45

@export var body : CharacterBody2D

#KNOBS, [phase 1, phase 2] where they differ
@export var ready_time: Array[float] = [0.60, 0.50]
@export var windup_time: Array[float] = [0.55, 0.45]
@export var change_windup_time: Array[float] = [0.80, 0.70]
@export var change_rock_time := 0.20
@export var release_after := 0.30
@export var fastball_flight := 0.12
@export var changeup_flight := 0.34
@export var changeup_arc := 70.0
@export var recover_time: Array[float] = [0.35, 0.30]
@export var release_frame_time := 0.06
@export var live_lead := 0.06
@export var live_tail := 0.14
@export var return_time := 0.16
@export var bonk_time := 0.45
@export var feint_show := 0.50
@export var pump_hold_after := 0.40
@export var hitch_time: Array[float] = [0.15, 0.12]
@export var quick_delay := 0.10
@export var quick_flight := 0.12
@export var feint_stamina := 40.0
@export var home_run_chip := 2
@export var knockdown_streak := 3
@export var aim_lead_cap := 600.0
# Each phase's sets, one picked at random a set: slot 1 is never a hesitation, and no two are next to each other.
@export var set_orders: Array = [
	[[FASTBALL, CHANGEUP, HESITATION], [FASTBALL, HESITATION, CHANGEUP]],
	[[FASTBALL, HESITATION, CHANGEUP, HESITATION], [CHANGEUP, HESITATION, FASTBALL, HESITATION]],
]
# The fight's first set has no fakes: the X first shows in a later cycle.
@export var teach_set: Array = [FASTBALL, FASTBALL, CHANGEUP]

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var listening := false
var clock := 0.0
var phase := 0
# [seconds on this clock, Callable], in order.
var queue: Array = []
var beat := Beat.READY
# The set, and the slot being thrown: its kind (the hesitation's red after the hitch keeps HESITATION), when its
# wind-up started, its badge or X went up and its contact is due, and until when its X is up.
var slots: Array = []
var slot_index := -1
var kind := &""
var kind_at := -INF
var badge_at := -INF
var contact_at := -INF
var x_at := -INF
var x_until := -INF
var slot_end_at := -INF
var flipped := false
var tell_tip := Vector2.ZERO
var bitten := false
# Home runs in a row this set; and whether the last one is the knockdown, which keeps its HOME RUN! up.
var streak := 0
var knocked_down := false
var ball: Node2D
var mark: Node2D
var mark_clock := 0.0
var glow: Polygon2D
var glow_clock := 0.0
var words: Array[Node] = []
var player: Node2D
var saved := {}
var sfx := {}
# For tests and bots: every pitch as it resolved ({slot, kind, result, at, badge_at, contact_at}), and a forced set.
var results: Array[Dictionary] = []
var forced_slots: Array = []


func _ready() -> void:
	for key in MasonArtLayout.PITCH_SFX:
		var spec: Dictionary = MasonArtLayout.PITCH_SFX[key]
		var player_sfx := AudioStreamPlayer.new()
		player_sfx.stream = load(spec.stream)
		player_sfx.pitch_scale = spec.pitch
		player_sfx.volume_db = spec.volume_db
		add_child(player_sfx)
		sfx[key] = player_sfx


func Enter() -> void:
	released = false
	clock = 0.0
	queue.clear()
	phase = state_machine.cycle_phase
	player = state_machine.get_player()
	slots = deal_slots()
	state_machine.pitch_sets_started += 1
	slot_index = -1
	kind = &""
	badge_at = -INF
	contact_at = -INF
	x_at = -INF
	x_until = -INF
	streak = 0
	knocked_down = false
	bitten = false
	results.clear()
	words.clear()
	var defense := _defense()
	listening = defense != null
	if listening and not defense.block_pressed.is_connected(_on_block_pressed):
		defense.block_pressed.connect(_on_block_pressed)
	var sprite: Sprite2D = body.sprite
	saved = {"texture": sprite.texture, "hframes": sprite.hframes, "flip_h": sprite.flip_h, "frame": sprite.frame, "modulate": sprite.modulate}
	body.animation_player.stop()
	var art := MasonArtLayout.pitch()
	if art.has("texture"):
		sprite.frame = 0
		sprite.hframes = art.hframes
		sprite.texture = load(art.texture)
	beat = Beat.READY
	_face_player()
	_show(&"ready")
	_at(ready_time[phase], _start_slot)


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	_run_due()
	if released:
		return
	_step(delta)


# Idempotent. Everything of it goes - the ball on its way out, the badge, the X, the glow and its words - unless the
# scene is being torn down, and he is back on his own sheet. A ball already batted back is the player's and flies on
# into his head. The knockdown's HOME RUN! stays up over his Break.
func release() -> void:
	if released:
		return
	released = true
	queue.clear()
	if listening:
		var defense := _defense()
		if defense != null and defense.block_pressed.is_connected(_on_block_pressed):
			defense.block_pressed.disconnect(_on_block_pressed)
	listening = false
	if is_instance_valid(ball) and not ball.returning:
		ball.queue_free()
	ball = null
	_clear_mark()
	_clear_glow()
	for word in words:
		if is_instance_valid(word) and not (knocked_down and word.has_meta(&"home_run")):
			word.queue_free()
	words.clear()
	if not is_instance_valid(body) or not body.is_inside_tree():
		return
	ParryTell.clear(body)
	var sprite: Sprite2D = body.sprite
	if not saved.is_empty():
		sprite.texture = saved.texture
		sprite.hframes = saved.hframes
		sprite.flip_h = saved.flip_h
		sprite.frame = saved.frame
		sprite.modulate = saved.modulate


# This set's slots: a forced set (a test's), the fight's first set (no fakes), or one of the phase's orders.
func deal_slots() -> Array:
	if not forced_slots.is_empty():
		return forced_slots.duplicate()
	if phase == 0 and state_machine.pitch_sets_started == 0:
		return teach_set.duplicate()
	var orders: Array = set_orders[phase]
	return orders[randi() % orders.size()].duplicate()


#THE SCHEDULE

func _at(time: float, action: Callable) -> void:
	var i := queue.size()
	while i > 0 and queue[i - 1][0] > time:
		i -= 1
	queue.insert(i, [time, action])


func _run_due() -> void:
	while not released and not queue.is_empty() and clock >= queue[0][0] - STEP_TOLERANCE:
		var entry: Array = queue.pop_front()
		entry[1].call()


func _start_slot() -> void:
	slot_index += 1
	if slot_index >= slots.size():
		_finish()
		return
	kind = slots[slot_index]
	kind_at = clock
	bitten = false
	beat = Beat.WINDUP
	_face_player()
	sfx[&"windup"].play()
	var now := clock
	if kind == CHANGEUP:
		var rocks := ceili(change_windup_time[phase] / change_rock_time)
		for i in rocks:
			_at(now + i * change_rock_time, _show.bind(&"change_a" if i % 2 == 0 else &"change_b"))
		_at(now + change_windup_time[phase], _set_red.bind(CHANGEUP))
		return
	_show(&"stretch")
	_at(now + windup_time[phase] * STRETCH_SHARE, _show.bind(&"kick"))
	_at(now + windup_time[phase], _set_red.bind(FASTBALL) if kind == FASTBALL else _set_fake)


func _end_slot() -> void:
	if clock < slot_end_at - STEP_TOLERANCE:
		_at(slot_end_at, _end_slot)
		return
	_start_slot()


func _finish() -> void:
	beat = Beat.DONE
	state_machine.next_attack(self)


#THE MARKS

# The SET under the red badge: a fastball or the hesitation's real one after its hitch (`pitch` FASTBALL), or a
# changeup.
func _set_red(pitch: StringName) -> void:
	beat = Beat.SET
	_show(&"change_set" if pitch == CHANGEUP else &"set")
	_clear_pulse()
	var flight: float = changeup_flight if pitch == CHANGEUP else fastball_flight
	badge_at = clock
	contact_at = clock + release_after + flight
	tell_tip = _tell_point()
	ParryTell.telegraph(body, &"mason_changeup" if pitch == CHANGEUP else &"mason_fastball", contact_at - clock + BADGE_SLACK, _tell_anchor)
	_rearm()
	_at(clock + release_after, _release.bind(pitch, flight))
	_at(contact_at, _contact)
	slot_end_at = contact_at + recover_time[phase]
	_at(slot_end_at, _end_slot)


# A hesitation's SET: the pale X where the badge would be, and a pump where the ball would leave his hand.
func _set_fake() -> void:
	beat = Beat.SET
	_show(&"set")
	x_at = clock
	x_until = clock + feint_show
	tell_tip = _tell_point()
	mark = _feint_mark(tell_tip)
	mark_clock = 0.0
	_rearm()
	_at(clock + release_after, _pump.bind(&"pump"))
	_at(clock + pump_hold_after, _pump.bind(&"pump_hold"))
	_at(x_until, _hitch)


func _pump(pose: StringName) -> void:
	beat = Beat.PUMP
	_show(pose)


# Left alone, the X goes and he comes set again: then the red badge and the real one.
func _hitch() -> void:
	beat = Beat.HITCH
	_clear_mark()
	results.append({slot = slot_index, kind = &"fake", result = &"ignored", at = clock, badge_at = x_at, contact_at = x_until})
	_show(&"set")
	_at(clock + hitch_time[phase], _set_red.bind(FASTBALL))


func _rearm() -> void:
	var defense := _defense()
	if defense != null:
		defense.rearm_parry()


#THE BALL

func _release(pitch: StringName, flight: float) -> void:
	beat = Beat.FLIGHT
	_clear_glow()
	_show(&"change_release" if pitch == CHANGEUP else &"release")
	if pitch != CHANGEUP:
		_at(clock + release_frame_time, _show.bind(&"follow"))
	sfx[&"changeup" if pitch == CHANGEUP else &"release"].play()
	if not is_instance_valid(player):
		return
	var thrown: Node2D = MasonPitchBall.new()
	thrown.name = "MasonPitchBall"
	thrown.kind = pitch
	thrown.player = player
	thrown.body = body
	thrown.answered.connect(_on_ball_answered.bind(thrown))
	get_tree().current_scene.add_child(thrown)
	var from: Vector2 = _anchor_point("release_hand")
	thrown.launch(from, aim_point(flight), flight, live_lead, live_tail, MasonArtLayout.BALL_RADIUS, changeup_arc if pitch == CHANGEUP else 0.0)
	# It left his hand on the step this was due, which may be a hair past the schedule: the ball's clock carries the
	# difference, so its contact keeps to contact_at.
	thrown.clock = maxf(clock - (contact_at - flight), 0.0)
	ball = thrown


# Where the player will be `flight` from now, by their velocity capped at aim_lead_cap, on the floor they can stand
# on, at their hurtbox's centre.
func aim_point(flight: float) -> Vector2:
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	var offset: Vector2 = shape.global_position - player.global_position
	var area: Rect2 = MasonBroken.PLAYER_AREA
	var ahead: Vector2 = player.global_position + player.velocity.limit_length(aim_lead_cap) * flight
	return ahead.clamp(area.position, area.end) + offset


func _contact() -> void:
	ParryTell.clear(body)
	if beat == Beat.FLIGHT:
		beat = Beat.RECOVER


func _on_ball_answered(result: int, thrown: Node2D) -> void:
	var was: StringName = thrown.kind
	results.append({slot = slot_index, kind = was, result = result, at = clock, badge_at = badge_at, contact_at = contact_at})
	if released and not thrown.returning and result != HitInfo.Result.PARRIED:
		return
	if result == HitInfo.Result.PARRIED and was != QUICK:
		streak += 1
		thrown.bat_back(_anchor_point("head_hit"), return_time)
		thrown.arrived.connect(_on_ball_arrived.bind(streak))
		slot_end_at = maxf(slot_end_at, clock + return_time + bonk_time)
		return
	if was != QUICK:
		streak = 0


# A HOME RUN: the chip, the word with the streak under it, the bonk on his head, and his bonk frames if he is still
# pitching. The knockdown_streak-th in a row fills his Break gauge: his Break takes over from there.
func _on_ball_arrived(in_a_row: int) -> void:
	if not is_instance_valid(body) or body.defeated or state_machine.player_defeated:
		return
	var head: Vector2 = _anchor_point("head_hit")
	if body.take_home_run(home_run_chip) <= 0:
		sfx[&"bonk"].play()
	_bonk_fx(head)
	_home_run_word(head, in_a_row)
	var pitching: bool = not released and state_machine.current_state == self
	if in_a_row >= knockdown_streak and body.break_gauge != null:
		knocked_down = true
		if body.break_gauge.add(body.break_gauge.max_value):
			return
		knocked_down = false
	if pitching:
		var art := MasonArtLayout.pitch()
		var times: Array = art.bonk_times
		var at := clock
		for i in art.bonk.size():
			_at(at, _show_frame.bind(art.bonk[i]))
			at += times[i]


#A BITE

# Any press while the X is up: the colour read wrong. It costs feint_stamina inside the press (it replaces the press's
# whiff), both streaks, and the quick pitch is the bill.
func _on_block_pressed(_credited := false) -> void:
	if released or bitten or clock < x_at or clock >= x_until or kind != HESITATION:
		return
	bitten = true
	beat = Beat.BITTEN
	queue.clear()
	x_until = clock
	results.append({slot = slot_index, kind = &"fake", result = &"bitten", at = clock, badge_at = x_at, contact_at = clock})
	var defense := _defense()
	if defense != null:
		defense.drain_stamina(feint_stamina)
		defense.end_parry_streak()
	streak = 0
	_clear_mark()
	_show(&"set")
	glow = _hand_glow()
	glow_clock = 0.0
	var head: Vector2 = _anchor_point("head_hit")
	_track_word(body.show_word("FEINT!", _word_centre(head, MasonArtLayout.WORD.box)))
	contact_at = clock + quick_delay + quick_flight
	_at(clock + quick_delay, _release.bind(QUICK, quick_flight))
	_at(contact_at, _contact)
	slot_end_at = contact_at + recover_time[phase]
	_at(slot_end_at, _end_slot)


#WHAT IS DRAWN

func _show(pose: StringName) -> void:
	var frames: Dictionary = MasonArtLayout.pitch().frames
	_show_frame(frames[pose])
	if pose == &"change_a" or pose == &"change_b":
		_pulse(pose == &"change_a")


func _show_frame(frame: int) -> void:
	if released:
		return
	body.sprite.frame = frame
	body.sprite.flip_h = flipped


# The placeholder's changeup tell: its frames face the viewer, so the rock is a light-blue beat on him.
func _pulse(up: bool) -> void:
	var look: Variant = MasonArtLayout.pitch().get("changeup_pulse")
	if look == null:
		return
	body.sprite.modulate = look.color if up else Color.WHITE


func _clear_pulse() -> void:
	if MasonArtLayout.pitch().has("changeup_pulse"):
		body.sprite.modulate = Color.WHITE


# Toward the player at READY and at each wind-up's start; held from the SET to the end of the slot. Drawn throwing
# toward screen-left, so a player on his right mirrors him.
func _face_player() -> void:
	if is_instance_valid(player):
		flipped = player.global_position.x > body.global_position.x
	body.sprite.flip_h = flipped


func _anchor_point(anchor: String) -> Vector2:
	var texel: Variant = MasonArtLayout.pitch_anchor(anchor, body.sprite.frame)
	if texel == null:
		return body.get_daze_anchor()
	return body.pitch_point(texel, flipped)


# The badge's and the X's bottom tip: the art's TELL anchor, or over his head; its top kept inside the view.
func _tell_point() -> Vector2:
	var texel: Variant = MasonArtLayout.pitch_anchor("tell", body.sprite.frame)
	var tip: Vector2 = body.get_daze_anchor() if texel == null else body.pitch_point(texel, flipped)
	var view: Rect2 = MasonArtLayout.VIEW_RECT
	var half: float = MasonArtLayout.TELL_BADGE_HEIGHT * 2.0 / 3.0
	tip.x = clampf(tip.x, view.position.x + MasonArtLayout.TELL_TOP_MARGIN + half, view.end.x - MasonArtLayout.TELL_TOP_MARGIN - half)
	tip.y = maxf(tip.y, view.position.y + MasonArtLayout.TELL_TOP_MARGIN + MasonArtLayout.TELL_BADGE_HEIGHT)
	return tip.round()


func _tell_anchor() -> Vector2:
	return tell_tip


# Carter's pale X on the tip, or the yellow ring standing in until it is there.
func _feint_mark(tip: Vector2) -> Node2D:
	var holder := Node2D.new()
	holder.name = "MasonPitchMark"
	holder.z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	var spec := MasonArtLayout.feint_mark()
	if not spec.is_empty():
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * spec.scale
		sheet.offset = spec.frame_size / 2.0 - spec.pivot
		sheet.frame = spec.steps.ignite
		sheet.add_to_group(&"hud_fade_under")
		holder.add_child(sheet)
		holder.position = tip - Vector2(0.0, spec.frame_size.y * spec.scale / 2.0)
	else:
		var look: Dictionary = MasonArtLayout.FEINT_RING
		var ring := Line2D.new()
		var points := PackedVector2Array()
		for i in look.points:
			points.append(Vector2.from_angle(TAU * i / look.points) * look.radius)
		ring.points = points
		ring.closed = true
		ring.width = look.width
		ring.default_color = look.color
		holder.add_child(ring)
		holder.position = tip - Vector2(0.0, look.radius + look.width / 2.0)
	body.get_parent().add_child(holder)
	return holder


func _clear_mark() -> void:
	if not is_instance_valid(mark):
		mark = null
		return
	var spec := MasonArtLayout.feint_mark()
	if not spec.is_empty() and mark.get_child_count() > 0:
		(mark.get_child(0) as Sprite2D).frame = spec.steps.fade
	var out := mark.create_tween()
	out.tween_property(mark, "modulate:a", 0.0, MasonArtLayout.MARK_OUT)
	out.tween_callback(mark.queue_free)
	mark = null


# His hand burning white, beating, from the bite until the quick pitch leaves it.
func _hand_glow() -> Polygon2D:
	var look: Dictionary = MasonArtLayout.QUICK_GLOW
	var light := Polygon2D.new()
	light.name = "MasonPitchGlow"
	var points := PackedVector2Array()
	for i in look.points:
		points.append(Vector2.from_angle(TAU * i / look.points) * look.glow_radius)
	light.polygon = points
	light.color = look.glow
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	light.material = added
	light.z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	body.get_parent().add_child(light)
	light.global_position = _anchor_point("hand").round()
	return light


func _clear_glow() -> void:
	if is_instance_valid(glow):
		glow.queue_free()
	glow = null


func _step(delta: float) -> void:
	if is_instance_valid(mark):
		mark_clock += delta
		var spec := MasonArtLayout.feint_mark()
		if not spec.is_empty() and mark.get_child_count() > 0:
			var step: int = spec.steps.hold
			if mark_clock < spec.ignite_time:
				step = spec.steps.ignite
			elif mark_clock < spec.ignite_time + spec.peak_time:
				step = spec.steps.peak
			(mark.get_child(0) as Sprite2D).frame = step
	if is_instance_valid(glow):
		glow_clock += delta
		var look: Dictionary = MasonArtLayout.QUICK_GLOW
		var swing := 0.5 + 0.5 * sin(TAU * glow_clock / (look.beat_time * 2.0))
		glow.scale = Vector2.ONE * lerpf(look.beat[0], look.beat[1], swing)


#THE WORDS

# Beside his head on the ring-centre side, clear of him and the badge's column, in view and clear of the HUD.
func _word_centre(head: Vector2, box: Vector2) -> Vector2:
	var inward := -1.0 if body.global_position.x > MasonArtLayout.VIEW_RECT.get_center().x else 1.0
	return MasonArtLayout.clear_of_hud(Vector2(body.global_position.x + inward * (MasonArtLayout.WORD_BESIDE + box.x / 2.0), head.y), box)


func _track_word(word: Node) -> void:
	if word != null:
		words.append(word)


func _home_run_word(head: Vector2, in_a_row: int) -> void:
	var art := MasonArtLayout.home_run()
	var box: Vector2 = art.frame_size * art.scale if art.has("texture") else art.box
	var pips := MasonArtLayout.home_run_pips()
	var pip_room: float = (pips.radius * 2.0 if not pips.has("texture") else 12.0 * pips.scale) + 8.0
	var whole := box + Vector2(0.0, pip_room)
	var centre := _word_centre(head, whole)
	var holder := Control.new()
	holder.name = "HomeRun"
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.size = whole
	holder.position = centre - whole / 2.0
	holder.pivot_offset = whole / 2.0
	holder.set_meta(&"home_run", true)
	holder.add_to_group(&"hud_fade_under")
	if art.has("texture"):
		var sheet := Sprite2D.new()
		sheet.texture = load(art.texture)
		sheet.hframes = art.hframes
		sheet.scale = Vector2.ONE * art.scale
		sheet.centered = false
		sheet.offset = Vector2(-art.frame_size.x / 2.0, -art.frame_size.y)
		sheet.position = Vector2(box.x / 2.0, box.y)
		holder.add_child(sheet)
		var play := sheet.create_tween()
		for i in range(1, art.hframes):
			play.tween_interval(art.frame_times[i - 1])
			play.tween_callback(sheet.set_frame.bind(i))
	else:
		var label := Label.new()
		label.text = art.text
		label.theme = load("res://Assets/UI/ui_theme.tres")
		label.add_theme_font_size_override("font_size", art.font_size)
		label.add_theme_color_override("font_color", art.color)
		label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
		label.add_theme_constant_override("outline_size", art.outline)
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.size = box
		holder.add_child(label)
	_add_pips(holder, Vector2(box.x / 2.0, box.y + pip_room / 2.0), in_a_row, pips)
	body.hud_layer.add_child(holder)
	holder.scale = Vector2.ONE * MasonArtLayout.WORD.from_scale
	var show := holder.create_tween()
	show.tween_property(holder, "scale", Vector2.ONE, MasonArtLayout.WORD.grow_time).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	show.tween_interval(MasonArtLayout.HOME_RUN_TIME - MasonArtLayout.WORD.grow_time)
	show.tween_property(holder, "modulate:a", 0.0, 0.3)
	show.tween_callback(holder.queue_free)
	_track_word(holder)


# knockdown_streak baseballs in a row under the word, the streak's filled.
func _add_pips(holder: Control, middle: Vector2, filled: int, pips: Dictionary) -> void:
	var count := knockdown_streak
	if pips.has("texture"):
		var step: float = 12.0 * pips.scale + 6.0
		for i in count:
			var pip := Sprite2D.new()
			pip.texture = load(pips.texture)
			pip.hframes = pips.hframes
			pip.scale = Vector2.ONE * pips.scale
			pip.frame = 1 if i < filled else 0
			pip.position = middle + Vector2((i - (count - 1) / 2.0) * step, 0.0)
			holder.add_child(pip)
		return
	for i in count:
		var pip := Polygon2D.new()
		var points := PackedVector2Array()
		for k in 16:
			points.append(Vector2.from_angle(TAU * k / 16.0) * pips.radius)
		pip.polygon = points
		pip.color = pips.filled if i < filled else pips.empty
		pip.position = middle + Vector2((i - (count - 1) / 2.0) * pips.gap, 0.0)
		var rim := Line2D.new()
		rim.points = points
		rim.closed = true
		rim.width = 3.0
		rim.default_color = pips.rim
		pip.add_child(rim)
		holder.add_child(pip)


# Crumbs, a flash star and two cartoon stars on his forehead, then gone.
func _bonk_fx(at: Vector2) -> void:
	var art := MasonArtLayout.bonk()
	if art.has("texture"):
		var sheet := Sprite2D.new()
		sheet.texture = load(art.texture)
		sheet.hframes = art.hframes
		sheet.scale = Vector2.ONE * art.scale
		sheet.z_index = MasonPitchBall.Z_INDEX
		body.get_parent().add_child(sheet)
		sheet.global_position = at.round()
		var play := sheet.create_tween()
		for i in range(1, art.hframes):
			play.tween_interval(art.frame_time)
			play.tween_callback(sheet.set_frame.bind(i))
		play.tween_interval(art.frame_time)
		play.tween_callback(sheet.queue_free)
		return
	var star := Polygon2D.new()
	star.name = "MasonPitchBonk"
	var points := PackedVector2Array()
	for i in art.points * 2:
		points.append(Vector2.from_angle(PI * i / art.points) * (art.outer if i % 2 == 0 else art.inner))
	star.polygon = points
	star.color = art.color
	star.z_index = MasonPitchBall.Z_INDEX
	body.get_parent().add_child(star)
	star.global_position = at.round()
	var pop := star.create_tween()
	pop.tween_property(star, "scale", Vector2.ONE * 1.4, art.time)
	pop.parallel().tween_property(star, "modulate:a", 0.0, art.time)
	pop.tween_callback(star.queue_free)


func _defense() -> Node:
	if not is_instance_valid(player):
		player = state_machine.get_player()
	return player.get("defense") if is_instance_valid(player) else null
