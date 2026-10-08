extends State

# Matt's Attack 3, the Echo Roars (the user's pick, 2026-10-04): he plants himself at HOME and roars on the beat of his
# theme. Every roar is a ring of sound over the whole ring (MattEchoRingScript), with its echo a beat behind it:
# parry, then parry. Three roars make a string, and gold BOOMBURSTs end it (MattStateMachine.echo_boombursts, two
# since 2026-10-06): dash through each, or it costs a heart and a half. Phase one plays echo_strings strings and phase two echo_strings_phase_two (MattStateMachine.cycle_echo_strings),
# and with a feint knob on (MattStateMachine.echo_feints_phase_one/two, both off since 2026-10-06) one roar a string is
# a silent fake under Carter's pale X (cycle_echo_feints): a press on it arms the echo behind it as a punish nothing
# answers. Then Recover at HOME, with its usual yell and scream rules.
# Built in code by MattStateMachine, beside his Broken and Juggled.
#
# One instance, his hurtbox off throughout:
#   OUT, IN  he squeezes out where he is and reforms at HOME, unflipped.
#   LANDING  while the player is still flying from a yell's throw, he waits for them to land.
#   STRINGS  one beat grid, from the lead-in, on game time. String s's first roar is on beat
#            echo_first_lead_beats + s * echo_string_beats, and from it, in beats:
#              -2  the first roar's badge (red, or the X), and the inhale     0  roar A (a ghost under an X)
#               1  echo A (a punish behind a bitten X), and B's badge         2  roar B
#               3  echo B, and C's badge                                       4  roar C
#               5  echo C                                                      6.5  the BOOMBURST's yellow badge, wind-up
#               8  the BOOMBURST                                               9.5  the second's badge and wind-up
#              11  the second BOOMBURST, each one echo_boomburst_spacing_beats after the one before, and the next
#                  string's first roar on echo_string_beats (14)
#            Every ring is spawned with its radius where its exact beat would have put it, so frame rounding never
#            squeezes two together.
#   OUTRO    a beat after the last BOOMBURST: spent, for at least echo_gasp and until none of his rings is alive;
#            echo_outro_cap frees any still out. Then Recover.
# The rules it keeps, E1-E9, are in MattStateMachine's header.
#
# FREEZE SAFETY: every wait is a Physics_Update accumulator and every effect node-bound.

# Every ring as it is born and as it touches the player, for the tests and the bots.
signal ring_born(ring: Node2D)
signal ring_touched(ring: Node2D, result: int)

const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const MattArtLayout := preload("res://Scripts/MattArtLayout.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const RING := preload("res://Scripts/MattEchoRingScript.gd")
const UI_THEME := preload("res://Assets/UI/ui_theme.tres")

const ECHO_ID := &"matt_echo"
const BOOMBURST_ID := &"matt_boomburst"
const HINT_WIDTH := 1200.0
# Events on one beat, in this order: a ring before the badge for the next one.
const EVENT_ORDER := {&"roar": 0, &"echo": 0, &"boomburst": 0, &"badge": 1, &"windup": 1, &"outro": 2}

var body: CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { OUT, IN, LANDING, STRINGS, OUTRO }

var beat := Beat.OUT
var beat_clock := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# The grid's clock, from the lead-in, and its schedule: [time, what, string, slot] in order.
var clock := 0.0
var events: Array = []
var next_event := 0
var strings := 0
var feints: Array[int] = []
var string_index := 0
var centre := Vector2.ZERO
# This instance's rings in the order they were born.
var rings: Array[Node2D] = []
# Every X: {string, slot, prev (the ring born last as its badge went up) and its touch, ring (the ghost) and its touch,
# echo, bitten}. The touches are kept here: a ring is freed once it has faded, long before a far player's window ends.
var xs: Array[Dictionary] = []
var mark: Node2D
var mark_clock := 0.0
var hint: Node2D
var hint_until := INF
var listening := false
var flooring := false
# On the player's defense clock.
var rearm_at: Array[float] = []
var badge_anim := &"echo_inhale"
# For tests: births [what, exact grid time, grid clock it was spawned on], badges [what, grid time, lead], and counts.
var births: Array = []
var badges: Array = []
var rings_born := 0
var bites := 0
var punishes_landed := 0
var reds_parried := 0
var reds_hit := 0
var boomburst_dodged := 0
var boomburst_hit := 0
var words := 0


func Enter() -> void:
	released = false
	beat = Beat.OUT
	beat_clock = 0.0
	clock = 0.0
	events.clear()
	next_event = 0
	string_index = 0
	strings = state_machine.cycle_echo_strings
	feints = state_machine.cycle_echo_feints.duplicate()
	rings.clear()
	xs.clear()
	rearm_at.clear()
	births.clear()
	badges.clear()
	rings_born = 0
	bites = 0
	punishes_landed = 0
	reds_parried = 0
	reds_hit = 0
	boomburst_dodged = 0
	boomburst_hit = 0
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.teleport_out()


func Exit() -> void:
	release()


# Idempotent: every ring, the badge, the X, the hint, the word, the press listener and the stamina floor go whichever
# way the instance ended.
func release() -> void:
	if released:
		return
	released = true
	if listening:
		state_machine.disconnect_block_presses(_on_block_pressed)
		listening = false
	_end_floor()
	for ring in rings:
		if is_instance_valid(ring):
			ring.queue_free()
	rings.clear()
	_drop_mark()
	if is_instance_valid(hint):
		hint.queue_free()
	hint = null
	if is_instance_valid(body):
		ParryTell.clear(body)
		body.restore_hud()
		body.stop_sfx(&"boomburst")


func Physics_Update(delta: float) -> void:
	beat_clock += delta
	match beat:
		Beat.OUT:
			if beat_clock >= state_machine.teleport_out:
				beat = Beat.IN
				beat_clock = 0.0
				body.teleport_in(state_machine.HOME, false)
				body.update_hud_fade(&"echo_inhale")
		Beat.IN:
			if beat_clock >= state_machine.teleport_in:
				if body.is_launching():
					beat = Beat.LANDING
					beat_clock = 0.0
				else:
					_begin_strings()
		Beat.LANDING:
			if not body.is_launching():
				_begin_strings()
		Beat.STRINGS:
			clock += delta
			state_machine.hold_stamina_floor(state_machine.echo_stamina_floor)
			_step_rearms()
			while next_event < events.size() and events[next_event][0] <= clock + 0.000001:
				var event: Array = events[next_event]
				next_event += 1
				_fire(event, clock - event[0])
			_step_mark(delta)
			_keep_hint()
		Beat.OUTRO:
			clock += delta
			state_machine.hold_stamina_floor(state_machine.echo_stamina_floor)
			_step_rearms()
			_keep_hint()
			var alive := rings.any(func(ring): return is_instance_valid(ring) and ring.is_live())
			if beat_clock >= state_machine.echo_outro_cap or (beat_clock >= state_machine.echo_gasp and not alive):
				for ring in rings:
					if is_instance_valid(ring):
						ring.queue_free()
				_end_floor()
				state_machine.on_child_transition(self, "Recover")


#THE GRID

func _begin_strings() -> void:
	beat = Beat.STRINGS
	beat_clock = 0.0
	clock = 0.0
	centre = body.mouth_point(&"roar")
	# E8: nothing else of his is alive under the rings. Spent and the Glass Row's release() see to it.
	var others: Array[Node] = state_machine.live_bolts() + state_machine.live_waves()
	if not others.is_empty():
		push_warning("Matt: %d bolts or waves still alive as the Echo Roars began; freed" % others.size())
		for other in others:
			other.queue_free()
	# The press listener only ever bites an X.
	if feints.any(func(slot): return slot >= 0):
		listening = state_machine.connect_block_presses(_on_block_pressed)
	flooring = true
	state_machine.watch_stamina(_on_stamina_changed)
	state_machine.hold_stamina_floor(state_machine.echo_stamina_floor)
	_schedule()


# E5: from the lead-in to the end of the OUTRO the bar is held at echo_stamina_floor, so a parry press or the
# BOOMBURST's dash is never refused - each step, and again on any change that takes it under.
func _on_stamina_changed(value: float, _max_value: float) -> void:
	if flooring and value < state_machine.echo_stamina_floor - 0.0001:
		state_machine.hold_stamina_floor(state_machine.echo_stamina_floor)


func _end_floor() -> void:
	if flooring:
		flooring = false
		state_machine.unwatch_stamina(_on_stamina_changed)


func _schedule() -> void:
	events.clear()
	var sm = state_machine
	var b: float = sm.echo_beat()
	for s in strings:
		var first: float = (sm.echo_first_lead_beats + s * sm.echo_string_beats) * b
		for slot in 3:
			var roar_at: float = first + 2.0 * slot * b
			var lead: float = (sm.echo_first_lead_beats if slot == 0 else sm.echo_red_lead_beats) * b
			events.append([roar_at - lead, &"badge", s, slot])
			events.append([roar_at, &"roar", s, slot])
			events.append([roar_at + b, &"echo", s, slot])
		for i in sm.echo_boombursts:
			var boom_at: float = first + (sm.echo_boomburst_beat + i * sm.echo_boomburst_spacing_beats) * b
			events.append([boom_at - sm.echo_yellow_lead_beats * b, &"windup", s, -1])
			events.append([boom_at, &"boomburst", s, -1])
	var last_boom: float = (sm.echo_first_lead_beats + (strings - 1) * sm.echo_string_beats + sm.echo_boomburst_beat
		+ (sm.echo_boombursts - 1) * sm.echo_boomburst_spacing_beats) * b
	events.append([last_boom + b, &"outro", strings - 1, -1])
	events.sort_custom(func(a, c): return a[0] < c[0] - 0.000001 or (absf(a[0] - c[0]) <= 0.000001 and EVENT_ORDER[a[1]] < EVENT_ORDER[c[1]]))


func _fire(event: Array, over: float) -> void:
	var s: int = event[2]
	var slot: int = event[3]
	string_index = s
	var b: float = state_machine.echo_beat()
	match event[1]:
		&"badge":
			var lead: float = (state_machine.echo_first_lead_beats if slot == 0 else state_machine.echo_red_lead_beats) * b
			_pose(&"echo_inhale")
			body.play_sfx(&"echo_inhale")
			if _is_x(s, slot):
				ParryTell.clear(body)
				var prev: Node2D = rings.back() if not rings.is_empty() else null
				xs.append({"string": s, "slot": slot, "prev": prev, "prev_touch": prev.touched_at if prev else -1.0,
					"ring": null, "touch": -1.0, "echo": null, "bitten": false})
				_raise_mark()
				badges.append([&"x", event[0], lead])
			else:
				ParryTell.telegraph(body, ECHO_ID, lead - over, _tell_anchor)
				badges.append([&"red", event[0], lead])
		&"roar":
			if _is_x(s, slot):
				_clear_mark()
				_pose(&"echo_psych")
				var x := _x_of(s, slot)
				var ghost := _spawn(RING.Kind.GHOST, over, &"ghost", event[0])
				x.ring = ghost
				x.touch = ghost.touched_at
			else:
				ParryTell.clear(body)
				_pose(&"roar")
				body.play_sfx(&"echo_roar")
				_spawn(RING.Kind.RED, over, &"red", event[0])
		&"echo":
			var x := _x_of(s, slot)
			var bitten: bool = not x.is_empty() and x.bitten
			var ring := _spawn(RING.Kind.PUNISH if bitten else RING.Kind.ECHO, over, &"punish" if bitten else &"echo", event[0])
			if not x.is_empty():
				x.echo = ring
			if not bitten:
				body.play_sfx(&"echo_echo")
		&"windup":
			var lead: float = state_machine.echo_yellow_lead_beats * b
			_pose(&"boomburst_windup")
			body.play_sfx(&"echo_inhale", 0.8)
			ParryTell.telegraph(body, BOOMBURST_ID, lead - over, _tell_anchor)
			badges.append([&"yellow", event[0], lead])
			if not state_machine.echo_hint_shown:
				state_machine.echo_hint_shown = true
				_show_hint()
		&"boomburst":
			ParryTell.clear(body)
			_pose(&"boomburst_blast")
			body.play_sfx(&"boomburst")
			var ring := _spawn(RING.Kind.BOOMBURST, over, &"boomburst", event[0])
			if is_instance_valid(hint) and hint_until == INF:
				hint.set_meta(&"boomburst", ring)
		&"outro":
			beat = Beat.OUTRO
			beat_clock = over
			body.play_state_anim(&"spent")


func _is_x(s: int, slot: int) -> bool:
	return s < feints.size() and feints[s] == slot


func _x_of(s: int, slot: int) -> Dictionary:
	for x in xs:
		if x.string == s and x.slot == slot:
			return x
	return {}


func _spawn(kind: int, over: float, what: StringName, at: float) -> Node2D:
	var sm = state_machine
	var ring: Node2D = RING.new()
	ring.kind = kind
	ring.player = sm.get_player()
	ring.speed = sm.echo_ring_speed
	ring.start_radius = sm.echo_ring_start_radius
	ring.end_radius = sm.echo_ring_end_radius
	ring.band = sm.echo_band
	ring.birth_disc_time = sm.echo_birth_disc_time
	ring.overshoot = over
	ring.touched.connect(_on_ring_touched)
	rings.append(ring)
	rings_born += 1
	births.append([what, at, clock])
	sm.add_hazard(ring, centre, body.projectile_layer)
	ring_born.emit(ring)
	return ring


func _pose(anim_name: StringName) -> void:
	body.play_anim(anim_name)
	body.update_hud_fade(anim_name)
	if anim_name in [&"echo_inhale", &"boomburst_windup"]:
		badge_anim = anim_name


func _tell_anchor() -> Vector2:
	return body.tell_anchor(badge_anim)


#THE ANSWERS

# A ring's one touch. A real one re-arms the parry echo_rearm_delay later, so a whiffed or late press never locks out
# the next ring (E4); a ghost's leaves the lockout alone.
func _on_ring_touched(ring: Node2D, result: int) -> void:
	if released:
		return
	ring_touched.emit(ring, result)
	match ring.kind:
		RING.Kind.RED, RING.Kind.ECHO:
			if result == HitInfo.Result.PARRIED:
				reds_parried += 1
			elif result == HitInfo.Result.HIT:
				reds_hit += 1
		RING.Kind.PUNISH:
			if result == HitInfo.Result.HIT:
				punishes_landed += 1
				body.play_sfx(&"echo_punish")
		RING.Kind.BOOMBURST:
			if result == HitInfo.Result.DODGED:
				boomburst_dodged += 1
			elif result == HitInfo.Result.HIT:
				boomburst_hit += 1
			if is_instance_valid(hint) and hint.get_meta(&"boomburst", null) == ring:
				hint_until = _defense_clock() + MattArtLayout.ECHO_HINT.hold_after
	for x in xs:
		if x.prev == ring:
			x.prev_touch = ring.touched_at
		if x.ring == ring:
			x.touch = ring.touched_at
	if ring.kind != RING.Kind.GHOST:
		rearm_at.append(_defense_clock() + state_machine.echo_rearm_delay)


func _step_rearms() -> void:
	var now := _defense_clock()
	while not rearm_at.is_empty() and rearm_at[0] <= now + 0.000001:
		rearm_at.pop_front()
		state_machine.rearm_parry()


# A press while an X is the next thing coming: from echo_bite_grace past the touch of the ring before it to
# echo_bite_grace past its own. Before that it is a late press for that ring; after, a press for its echo.
func _on_block_pressed(_credited := false) -> void:
	if released or not (beat == Beat.STRINGS or beat == Beat.OUTRO):
		return
	var now := _defense_clock()
	var grace: float = state_machine.echo_bite_grace
	for x in xs:
		if x.bitten:
			continue
		if x.prev_touch < 0.0 or now <= x.prev_touch + grace:
			continue
		if x.touch >= 0.0 and now > x.touch + grace:
			continue
		_bite(x)
		return


# His laugh and the word, the streak gone, and the echo behind it a punish: nothing answers it, and its hit costs the
# read back through the gauge's own hit_loss.
func _bite(x: Dictionary) -> void:
	x.bitten = true
	bites += 1
	var echo: Node2D = x.echo
	if echo != null and is_instance_valid(echo):
		echo.set_kind(RING.Kind.PUNISH)
	state_machine.end_parry_streak()
	body.play_sfx(&"echo_psych")
	_show_word()


func _defense_clock() -> float:
	var player: Node = state_machine.get_player()
	var defense = player.get("defense") if player else null
	return defense.clock if defense else clock


#THE X

func _raise_mark() -> void:
	_drop_mark()
	var spec := MattArtLayout.FEINT_MARK
	mark = Node2D.new()
	mark.name = "EchoMark"
	mark.z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.scale = Vector2.ONE * spec.scale
	sheet.offset = spec.frame_size / 2.0 - spec.pivot
	sheet.frame = spec.steps.ignite
	mark.add_child(sheet)
	mark_clock = 0.0
	state_machine.add_hazard(mark, _mark_point(), body.get_parent())


# The X's tip where a badge's would stand.
func _mark_point() -> Vector2:
	var spec := MattArtLayout.FEINT_MARK
	return _tell_anchor() - Vector2(0.0, spec.frame_size.y * spec.scale / 2.0)


# Ignite, peak, then a hold that never pulses.
func _step_mark(delta: float) -> void:
	if not is_instance_valid(mark) or mark.get_child_count() == 0 or mark.has_meta(&"fading"):
		return
	var spec := MattArtLayout.FEINT_MARK
	mark_clock += delta
	var step: int = spec.steps.hold
	if mark_clock < spec.ignite_time:
		step = spec.steps.ignite
	elif mark_clock < spec.ignite_time + spec.peak_time:
		step = spec.steps.peak
	(mark.get_child(0) as Sprite2D).frame = step
	mark.global_position = _mark_point().round()


# At the ghost's birth: its fade frame, gone in FEINT_MARK.out.
func _clear_mark() -> void:
	if not is_instance_valid(mark):
		mark = null
		return
	var spec := MattArtLayout.FEINT_MARK
	(mark.get_child(0) as Sprite2D).frame = spec.steps.fade
	mark.set_meta(&"fading", true)
	var out := mark.create_tween()
	out.tween_property(mark, "modulate:a", 0.0, spec.out)
	out.tween_callback(mark.queue_free)
	mark = null


func _drop_mark() -> void:
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null


#THE WORD AND THE HINT

# PSYCH! beside him, alternating sides from bite to bite, clear of the badge (PSYCH_WORD.badge_rect).
func _show_word() -> void:
	var spec := MattArtLayout.PSYCH_WORD
	var offset: Vector2 = spec.offset
	if words % 2 == 1:
		offset.x = -offset.x
	words += 1
	var holder := Node2D.new()
	holder.name = "PsychWord"
	holder.z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	var label := Label.new()
	label.theme = UI_THEME
	label.text = spec.text
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.add_theme_constant_override("outline_size", spec.outline)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.size = spec.box
	label.position = -spec.box / 2.0
	label.pivot_offset = spec.box / 2.0
	label.scale = Vector2.ONE * spec.from_scale
	holder.add_child(label)
	state_machine.add_hazard(holder, state_machine.HOME + offset, body.projectile_layer)
	var show := label.create_tween()
	show.tween_property(label, "scale", Vector2.ONE * spec.to_scale, spec.grow_time).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	show.tween_interval(spec.time - spec.grow_time)
	show.tween_property(label, "modulate:a", 0.0, 0.3)
	show.tween_callback(holder.queue_free)


# Where the word for the next bite stands, in world px: for a test.
func word_box(bite: int) -> Rect2:
	var spec := MattArtLayout.PSYCH_WORD
	var offset: Vector2 = spec.offset
	if bite % 2 == 1:
		offset.x = -offset.x
	return Rect2(state_machine.HOME + offset - spec.box / 2.0, spec.box)


func _show_hint() -> void:
	var spec := MattArtLayout.ECHO_HINT
	hint_until = INF
	hint = Node2D.new()
	hint.name = "EchoHint"
	var label := Label.new()
	label.theme = UI_THEME
	label.text = spec.text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", spec.font_size)
	label.add_theme_constant_override("outline_size", spec.outline)
	label.add_theme_color_override("font_color", spec.color)
	label.add_theme_color_override("font_outline_color", spec.outline_color)
	label.size = Vector2(HINT_WIDTH, spec.font_size * 2)
	label.position = Vector2(-HINT_WIDTH / 2.0, 0)
	hint.add_child(label)
	hint.modulate.a = 0.0
	state_machine.add_hazard(hint, _hint_point(), body.projectile_layer)
	var fade := hint.create_tween()
	fade.tween_property(hint, "modulate:a", 1.0, spec.fade)


func _hint_point() -> Vector2:
	var player: Node2D = state_machine.get_player()
	var at: Vector2 = player.global_position if player else state_machine.HOME
	return at + MattArtLayout.ECHO_HINT.offset


# On the player until hold_after past the BOOMBURST's touch.
func _keep_hint() -> void:
	if not is_instance_valid(hint):
		return
	hint.global_position = _hint_point().round()
	if _defense_clock() < hint_until:
		return
	var gone := hint
	hint = null
	var fade := gone.create_tween()
	fade.tween_property(gone, "modulate:a", 0.0, MattArtLayout.ECHO_HINT.fade)
	fade.tween_callback(gone.queue_free)
