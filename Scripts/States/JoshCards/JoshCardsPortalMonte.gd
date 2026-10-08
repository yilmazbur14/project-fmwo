extends State

# Josh's third attack, Portal Monte, to the user's design of 2026-09-29: "Portal Monte: he dives into a portal and
# bursts out of one of three small portals around you. The red one is real, so parry it. The yellow ones are fakes, so
# don't, same as Carter's clones." Its four open questions are on their defaults, each a knob on the state machine
# (monte_lock_player, monte_parry_ends, monte_hands_deal, monte_feint_punishes). Seconds from Enter:
#   DIVE     0.50  the player is locked on its first frame (a dash in flight is cut); he dives up into the big gate
#                  nearer him, which feeds, shrinking and fading into it
#   DEAL     0.25  a round's three spots round the player (JoshMonteLayout.place), in a random order: the resting hands
#                  flex and flick a card to each, from the nearer hand (from its big gate if the hand is gone)
#   OPEN     0.30  a small gate (JoshPortal, kind small) opens where each card lands, all three alike
#   and three bursts, monte_cadence apart:
#   SHOW     0.36  its gate's mark comes up - the red parry badge over the real him, Carter's pale X over a fake, a white
#                  glow beating and no badge over a punish - the parry is re-armed, and the player turned to face it
#   DASH     0.18  the figure bursts out (JoshMonteFigure) and lunges at the player
#   CONTACT        the real him: the hit, parried or landing; a fake bursts into cards; a punish lands. The mark clears
#                  and the gate closes. The real him parried ends it there (monte_parry_ends): the other gates fizzle,
#                  the player is free that frame, and he staggers out onto the floor where he struck, knocked back
#                  toward his gate, his Recover opening monte_parry_recover_bonus longer after monte_stagger_time
#   ...up to monte_rounds rounds (0.50, 2.91, 5.32, 7.73, 10.14), each dealt turned off the last
#   EMERGE   0.50  with no parry: the player is free, and he drops back out of his gate onto the floor under it, with a
#                  burst of cards and a thud; then his Recover
# THE READ is Carter's: each mark up monte_show and only one at a time; a fake's figure is the real one's to the
# frame until the contact. Biting a fake - a press while its mark is up - costs monte_feint_stamina (in the press's own
# signal, so it prices that press's whiff) and the streak, puts up "FEINT!", and makes the next burst a punish, even
# the real one and across a round; biting the attack's very last burst takes a read off his gauge instead.
# IT IS ONE STATE ON PURPOSE (Carter's rule): the lock, the marks, the small gates, the figures and his being gone are
# taken and given back through one idempotent release(), which Exit(), _exit_tree() and his Break go through - a player
# left locked would never move again. At a scene's teardown it touches nothing of the fight. Every wait runs off one
# clock against a schedule worked out as it enters (DannyBossSlams' pattern), so a pause or a freeze holds it.

const Monte := preload("res://Scripts/JoshMonteLayout.gd")
const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const JoshPortal := preload("res://Scripts/JoshPortal.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")
const Figure := preload("res://Scripts/JoshMonteFigure.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

enum Beat { DIVE, DEAL, OPEN, SHOW, DASH, CONTACT, EMERGE, STAGGER, DONE }

const STRIKE_ID := &"josh_monte_strike"
const BURSTS := 3
# Summed steps land a hair short of a scheduled time, which would start its beat a step late.
const STEP_TOLERANCE := 0.0001
# The red badge is cleared at its contact; given this much longer, it never runs out a step early.
const BADGE_SLACK := 0.1
# How long a parried him is knocked back over.
const KNOCK_TIME := 0.25

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var finished := false
var listening := false
var locked := false
var clock := 0.0
# [seconds from Enter, Beat, round, burst], in order.
var schedule: Array = []
var next_entry := 0
var beat := Beat.DIVE
var beat_start := 0.0
var round := -1
var burst_index := -1
# Which of each round's bursts is the real him.
var pattern: Array[int] = []
# The round's three small gates' floor points in the order they burst, the gates, and where JoshMonteLayout.place put
# them ({spots, turn, how}); every round's, for a test.
var spots: Array[Vector2] = []
var gates: Array[Node2D] = []
var placement := {}
var placements: Array[Dictionary] = []
var figure: Node2D
# The live burst: a fake, a punish, bitten.
var is_feint := false
var is_punish := false
var punish_next := false
var bitten := false
# The live burst's mark, when it isn't the red badge (a fake's X or ring, a punish's glow), and its clock.
var mark: Node2D
var mark_clock := 0.0
# A round's cards in flight: {node, from, to}.
var deal_cards: Array[Dictionary] = []
var player: Node2D
var pre_dive_spot := Vector2.ZERO
var dive_from := Vector2.ZERO
var dive_side := &"left"
# His middle, px from his feet, on the dive (facing his gate) and on the emerge's first frame: what the gate's opening
# is aimed at, and what he shrinks and grows about. How high the emerge starts him, and whether he has landed from it.
var dive_centre := Vector2.ZERO
var emerge_centre := Vector2.ZERO
var emerge_height := 0.0
var landed := false
var staggering := false
var stagger_spot := Vector2.INF
# For a test: the tallies, every burst as it resolved ({round, burst, kind: red, fake or punish, result, at}), when
# the player was locked and let go and when each mark came up and each burst struck, on this state's clock. A forced
# pattern pins the real him's burst a round; a forced rotation the placement's first turn (JoshMonteLayout.place), and
# with it the bursts in the order placed.
var reds_parried := 0
var reds_hit := 0
var feints_bitten := 0
var punishes_landed := 0
var results: Array[Dictionary] = []
var lock_times: Array[float] = []
var mark_times: Array[float] = []
var contact_times: Array[float] = []
var forced_pattern: Array[int] = []
var forced_rotation := -1


func Enter() -> void:
	released = false
	finished = false
	clock = 0.0
	next_entry = 0
	beat = Beat.DIVE
	beat_start = 0.0
	round = -1
	burst_index = -1
	spots.clear()
	gates.clear()
	placement = {}
	placements.clear()
	figure = null
	mark = null
	deal_cards.clear()
	is_feint = false
	is_punish = false
	punish_next = false
	bitten = false
	staggering = false
	stagger_spot = Vector2.INF
	reds_parried = 0
	reds_hit = 0
	feints_bitten = 0
	punishes_landed = 0
	results.clear()
	lock_times.clear()
	mark_times.clear()
	contact_times.clear()
	var sm = state_machine
	pattern = deal_pattern(sm.monte_rounds)
	for r in mini(forced_pattern.size(), pattern.size()):
		pattern[r] = forced_pattern[r]
	player = sm.get_player()
	listening = sm.connect_block_presses(_on_block_pressed)
	locked = false
	if sm.monte_lock_player:
		sm.lock_player()
		locked = true
		lock_times.append(clock)
	var rig: Node = sm.hands
	if not rig.built:
		rig.build()
		rig.place_summoned()
	body.fly_velocity = Vector2.ZERO
	body.hide_glider()
	body.set_hurtbox_active(false)
	body.set_target_active(true)
	body.height = 0.0
	body.place()
	pre_dive_spot = body.ground_position
	dive_from = body.ground_position
	var left: float = absf(Layout.PORTAL_POINTS[&"left"].x - dive_from.x)
	var right: float = absf(Layout.PORTAL_POINTS[&"right"].x - dive_from.x)
	dive_side = &"left" if left <= right else &"right"
	body.flying_left = Layout.PORTAL_POINTS[dive_side].x < dive_from.x
	dive_centre = Monte.dive_centre(body.flying_left)
	landed = false
	body.set_air_draw(true)
	body.play_anim(&"dive")
	var portal: Node2D = rig.portal_of(dive_side)
	if portal != null:
		portal.feed()
	rig.play_sound(&"monte_dive")
	schedule = _schedule()
	_run_due()


func Physics_Update(delta: float) -> void:
	if released:
		return
	# Polled here and only here, and only when PlayerDefense has no block_pressed signal to give (Carter's).
	if not listening and _mark_up() and Input.is_action_just_pressed("block"):
		_on_block_pressed(false)
	clock += delta
	_run_due()
	if released:
		return
	_step(delta)


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent. Everything of it goes - the cards, the small gates and their badges, the figure, the mark - and unless
# the scene is being torn down, the player is let go and he is in view: where his stagger took him, on the floor
# under his gate if he was coming back out, or back where he dove from.
func release() -> void:
	if released:
		return
	released = true
	if listening and is_instance_valid(state_machine):
		state_machine.disconnect_block_presses(_on_block_pressed)
	listening = false
	_free_cards()
	for gate in gates:
		if is_instance_valid(gate):
			ParryTell.clear(gate)
			gate.queue_free()
	gates.clear()
	if is_instance_valid(figure):
		figure.queue_free()
	figure = null
	if is_instance_valid(mark):
		mark.queue_free()
	mark = null
	if not is_instance_valid(body) or body.health_bar == null or not body.health_bar.is_inside_tree():
		return
	_free_player()
	if finished:
		return
	if staggering:
		if body.knock_tween:
			body.knock_tween.kill()
		_show_him(stagger_spot)
	elif beat == Beat.EMERGE:
		_show_him(_emerge_floor())
	else:
		_show_him(pre_dive_spot)


# Which of each of `rounds` rounds' bursts is the real him: any of the three, alike. That is the monte.
static func deal_pattern(rounds: int) -> Array[int]:
	var out: Array[int] = []
	for r in rounds:
		out.append(randi() % BURSTS)
	return out


#THE SCHEDULE

func _schedule() -> Array:
	var sm = state_machine
	var entries := [[0.0, Beat.DIVE, -1, -1]]
	var at: float = sm.monte_dive_time
	for r in sm.monte_rounds:
		entries.append([at, Beat.DEAL, r, -1])
		entries.append([at + sm.monte_deal_time, Beat.OPEN, r, -1])
		var first: float = at + sm.monte_deal_time + sm.monte_open_time
		for k in BURSTS:
			var show: float = first + k * sm.monte_cadence()
			entries.append([show, Beat.SHOW, r, k])
			entries.append([show + sm.monte_show, Beat.DASH, r, k])
			entries.append([show + sm.monte_show + sm.monte_dash, Beat.CONTACT, r, k])
		at = first + BURSTS * sm.monte_cadence()
	entries.append([at, Beat.EMERGE, sm.monte_rounds - 1, -1])
	entries.append([at + sm.monte_emerge_time, Beat.DONE, sm.monte_rounds - 1, -1])
	return entries


# Every beat that is due, in order. A parry swaps the rest of the schedule for the stagger's.
func _run_due() -> void:
	while not released and next_entry < schedule.size() and clock >= schedule[next_entry][0] - STEP_TOLERANCE:
		var entry: Array = schedule[next_entry]
		next_entry += 1
		_begin(entry[1], entry[2], entry[3], entry[0])


func _begin(new_beat: int, number: int, burst: int, at: float) -> void:
	beat = new_beat
	beat_start = at
	match new_beat:
		Beat.DEAL:
			_deal(number)
		Beat.OPEN:
			_open()
		Beat.SHOW:
			_mark_burst(burst)
		Beat.DASH:
			_dash()
		Beat.CONTACT:
			_contact()
		Beat.EMERGE:
			_emerge()
		Beat.DONE:
			_finish()


func _step(delta: float) -> void:
	var sm = state_machine
	match beat:
		Beat.DIVE:
			var s := smoothstep(0.0, 1.0, clampf(clock / sm.monte_dive_time, 0.0, 1.0))
			body.ground_position = dive_from.lerp(_dive_floor(), s)
			body.height = (Monte.DIVE_UNDER + dive_centre.y) * s
			body.place()
			_shrink(clampf((clock - sm.monte_dive_time + Monte.DIVE_SHRINK_TIME) / Monte.DIVE_SHRINK_TIME, 0.0, 1.0), dive_centre)
		Beat.DEAL:
			_fly_cards()
		Beat.SHOW, Beat.DASH:
			_step_mark(delta)
		Beat.EMERGE:
			if landed:
				return
			var into := clock - beat_start
			var landing := Monte.emerge_landing(sm.monte_emerge_time)
			var p := clampf(into / landing, 0.0, 1.0)
			body.height = emerge_height * (1.0 - p * p)
			body.place()
			_shrink(1.0 - clampf(into / Monte.DIVE_SHRINK_TIME, 0.0, 1.0), emerge_centre)
			if into >= landing - STEP_TOLERANCE:
				_land()


#THE DEAL

func _deal(number: int) -> void:
	var sm = state_machine
	round = number
	burst_index = -1
	if number == 0:
		_hide_him()
	placement = Monte.place(_standing(), placement, sm.monte_radius, sm.monte_min_radius, sm.ROPES, forced_rotation)
	placements.append(placement)
	spots.assign(placement.spots)
	if forced_rotation < 0:
		spots.shuffle()
	if sm.monte_hands_deal:
		_flick_cards()


# A card from the hand nearer each spot to where its gate opens; each hand that deals flexes once.
func _flick_cards() -> void:
	var rig: Node = state_machine.hands
	var flexed := {}
	for spot in spots:
		var side := _nearer_side(spot)
		var hand: Node2D = rig.hand_of(side)
		var from: Vector2 = Layout.PORTAL_POINTS[side]
		if hand != null and hand.visible and hand.mode == JoshHand.Mode.REST:
			from = hand.drawn_point()
			if not flexed.has(side) and hand.clip == &"hover" and not hand.driven:
				hand.play(&"windup", 1.0, false, &"hover")
			flexed[side] = true
		deal_cards.append({node = _card(from), from = from, to = spot - Vector2(0.0, Monte.small_drop())})
	rig.play_sound(&"monte_deal")


func _card(at: Vector2) -> Sprite2D:
	var spec: Dictionary = JoshArtLayout.FINAL_THROWN_CARD
	var card := Sprite2D.new()
	card.name = "MonteDealCard"
	card.texture = load(spec.texture)
	card.hframes = spec.hframes
	card.scale = Vector2.ONE * spec.scale
	card.offset = spec.frame_size / 2.0 - spec.pivot
	state_machine.add_hazard(card, at, body.sky_layer)
	return card


func _fly_cards() -> void:
	var spec: Dictionary = JoshArtLayout.FINAL_THROWN_CARD
	var into := clock - beat_start
	var p := clampf(into / state_machine.monte_deal_time, 0.0, 1.0)
	for card in deal_cards:
		if not is_instance_valid(card.node):
			continue
		var from: Vector2 = card.from
		var to: Vector2 = card.to
		card.node.global_position = (from.lerp(to, p) + Vector2(0.0, -Monte.DEAL_ARC * sin(PI * p))).round()
		card.node.frame = int(into / spec.frame_time) % int(spec.hframes)
		card.node.flip_h = to.x < from.x


func _free_cards() -> void:
	for card in deal_cards:
		if is_instance_valid(card.node):
			card.node.queue_free()
	deal_cards.clear()


# Each card opens into a small gate where it lands.
func _open() -> void:
	var sm = state_machine
	_free_cards()
	gates.clear()
	var open_time := 0.0
	for time: float in Monte.SMALL_PORTAL_SEQUENCES[&"open"]:
		open_time += time
	for spot in spots:
		var gate: Node2D = JoshPortal.make(&"right", &"small")
		sm.add_hazard(gate, spot, body.get_parent())
		gate.open(open_time / maxf(sm.monte_open_time, 0.001))
		gates.append(gate)


#THE BURSTS

func _mark_burst(burst: int) -> void:
	var sm = state_machine
	burst_index = burst
	is_punish = punish_next
	punish_next = false
	is_feint = pattern[round] != burst and not is_punish
	bitten = false
	mark_clock = 0.0
	mark_times.append(clock)
	var gate := _gate(burst)
	if gate != null:
		if is_punish:
			mark = _punish_mark(gate)
		elif is_feint:
			mark = _feint_mark(gate)
		else:
			ParryTell.telegraph(gate, STRIKE_ID, sm.monte_show + sm.monte_dash + BADGE_SLACK, _tip.bind(spots[burst]))
	# On the frame the mark comes up, every burst: a whiff at the last one can't lock this one out.
	sm.rearm_parry()
	if locked:
		sm.face_player_at(spots[burst] - Vector2(0.0, Monte.small_drop()))


func _dash() -> void:
	var sm = state_machine
	var gate := _gate(burst_index)
	if gate != null:
		gate.burst()
	var rush: Node2D = Figure.new()
	rush.name = "MonteFigure"
	rush.is_feint = is_feint
	rush.is_punish = is_punish
	rush.from_point = spots[burst_index]
	# Its feet end short of the player by where its cut lands, so the cut lands on their hurtbox centre.
	var hurt := _player_centre()
	rush.facing_left = hurt.x < rush.from_point.x
	rush.to_point = hurt - Monte.contact_offset(rush.facing_left)
	rush.player = player
	rush.body = body
	rush.homing = not locked
	# Its node sorts FIGURE_SORT_BUMP in front of its gate's floor point until its feet are lower (JoshMonteFigure._place),
	# so it is drawn over the gate it bursts out of.
	sm.add_hazard(rush, rush.from_point + Vector2(0.0, Monte.FIGURE_SORT_BUMP), body.get_parent())
	rush.launch(sm.monte_dash)
	figure = rush
	sm.hands.play_sound(&"monte_burst")


# The contact instant: the mark clears, the gate closes, and the figure strikes.
func _contact() -> void:
	contact_times.append(clock)
	var gate := _gate(burst_index)
	_clear_mark(gate)
	if gate != null:
		gate.close()
	var at: Vector2 = figure.to_point.round() if is_instance_valid(figure) else _player_centre()
	var result: int = figure.strike() if is_instance_valid(figure) else HitInfo.Result.IGNORED
	figure = null
	var kind := &"punish" if is_punish else (&"fake" if is_feint else &"red")
	results.append({round = round, burst = burst_index, kind = kind, result = result, at = clock})
	if is_feint:
		return
	if is_punish:
		if result == HitInfo.Result.HIT:
			punishes_landed += 1
		return
	match result:
		HitInfo.Result.PARRIED:
			reds_parried += 1
			if state_machine.monte_parry_ends:
				_parried(at)
			else:
				_burst_cards(at)
		HitInfo.Result.HIT:
			reds_hit += 1


# The real him, parried: the rest of the round fizzles, the player is free, and he is out on the floor where he
# struck, knocked back toward his gate.
func _parried(at: Vector2) -> void:
	var sm = state_machine
	staggering = true
	for k in range(burst_index + 1, gates.size()):
		var gate := _gate(k)
		if gate != null:
			gate.close()
	_free_player()
	var ground: Rect2 = body.ground_bounds(0.0)
	var spot := at.clamp(ground.position, ground.end)
	var away := spots[burst_index] - spot
	var push: Vector2 = away.normalized() * sm.monte_knock if away.length() > 0.5 else Vector2.ZERO
	stagger_spot = (spot + push).clamp(ground.position, ground.end)
	_show_him(spot)
	body.face_player()
	body.play_anim(&"hit", &"recover")
	body.knock_back(push, KNOCK_TIME)
	beat = Beat.STAGGER
	schedule = [[beat_start + sm.monte_stagger_time, Beat.DONE, round, -1]]
	next_entry = 0


# A press while a fake's mark is up (Carter's): the colour read wrong. It costs stamina and the streak, never health,
# and the next burst is the bill - a punish nothing answers - or, after the attack's last burst, a read off his gauge.
func _on_block_pressed(_credited := false) -> void:
	if released or not _mark_up() or not is_feint or bitten:
		return
	var sm = state_machine
	bitten = true
	feints_bitten += 1
	if sm.monte_feint_punishes:
		if round == sm.monte_rounds - 1 and burst_index == BURSTS - 1:
			if body.break_gauge:
				body.break_gauge.add(-body.break_gauge.hit_loss)
		else:
			punish_next = true
	sm.drain_stamina(sm.monte_feint_stamina)
	sm.end_parry_streak()
	body.show_word("FEINT!", Monte.word_centre(spots, burst_index))
	sm.hands.play_sound(&"monte_feint")


func _mark_up() -> bool:
	return beat == Beat.SHOW or beat == Beat.DASH


#THE MARKS

func _tip(spot: Vector2) -> Vector2:
	return Monte.mark_tip(spot)


# A fake's pale X over its gate, or the yellow ring standing in until the X is imported.
func _feint_mark(gate: Node2D) -> Node2D:
	var holder := Node2D.new()
	holder.name = "MonteMark"
	holder.z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	var tip := Monte.mark_tip(Vector2.ZERO)
	var spec := Monte.feint_mark()
	if not spec.is_empty():
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.hframes
		sheet.scale = Vector2.ONE * spec.scale
		sheet.offset = spec.frame_size / 2.0 - spec.pivot
		sheet.frame = spec.steps.ignite
		holder.add_child(sheet)
		holder.position = tip - Vector2(0.0, spec.frame_size.y * spec.scale / 2.0)
	else:
		var look: Dictionary = Monte.FEINT_RING
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
	gate.add_child(holder)
	return holder


# A punish: its gate burns white, beating, and wears no badge.
func _punish_mark(gate: Node2D) -> Node2D:
	var look: Dictionary = Monte.PUNISH
	var glow := Polygon2D.new()
	glow.name = "MonteMark"
	var points := PackedVector2Array()
	for i in look.points:
		points.append(Vector2.from_angle(TAU * i / look.points) * look.glow_radius)
	glow.polygon = points
	glow.color = look.glow
	var added := CanvasItemMaterial.new()
	added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow.material = added
	glow.z_index = DefenseHypeArtLayout.PARRY_TELL_Z_INDEX
	glow.position = Vector2(0.0, -Monte.small_drop())
	gate.add_child(glow)
	return glow


# The X steps through ignite and peak to its hold and stays there; the punish's glow beats.
func _step_mark(delta: float) -> void:
	if not is_instance_valid(mark):
		return
	mark_clock += delta
	if is_punish:
		var look: Dictionary = Monte.PUNISH
		var swing := 0.5 + 0.5 * sin(TAU * mark_clock / (look.beat_time * 2.0))
		mark.scale = Vector2.ONE * lerpf(look.beat[0], look.beat[1], swing)
		return
	var spec := Monte.feint_mark()
	if spec.is_empty() or mark.get_child_count() == 0:
		return
	var step: int = spec.steps.hold
	if mark_clock < spec.ignite_time:
		step = spec.steps.ignite
	elif mark_clock < spec.ignite_time + spec.peak_time:
		step = spec.steps.peak
	(mark.get_child(0) as Sprite2D).frame = step


# At its contact: the badge goes, and the X or the glow is gone in MARK_OUT.
func _clear_mark(gate: Node2D) -> void:
	if gate != null:
		ParryTell.clear(gate)
	if not is_instance_valid(mark):
		mark = null
		return
	var spec := Monte.feint_mark()
	if is_feint and not spec.is_empty() and mark.get_child_count() > 0:
		(mark.get_child(0) as Sprite2D).frame = spec.steps.fade
	var out := mark.create_tween()
	out.tween_property(mark, "modulate:a", 0.0, Monte.MARK_OUT)
	out.tween_callback(mark.queue_free)
	mark = null


#HIM

func _hide_him() -> void:
	body.air.hide()
	body.shadow.hide()
	body.set_target_active(false)
	_shrink(0.0)


func _show_him(spot: Vector2) -> void:
	_shrink(0.0)
	body.ground_position = spot
	body.height = 0.0
	body.place()
	body.set_air_draw(false)
	body.air.show()
	body.shadow.show()
	body.set_target_active(true)


# How far into his gate he has gone: shrunk to DIVE_SHRINK and faded out at 1, about his middle (`centre`, px from his
# feet), so it stays on the gate's opening; placed first, since place() puts him back on his feet.
func _shrink(amount: float, centre := Vector2.ZERO) -> void:
	var size := lerpf(1.0, Monte.DIVE_SHRINK, amount)
	body.air.scale = Vector2.ONE * size
	body.air.modulate.a = 1.0 - amount
	body.air.position += centre * (1.0 - size)


# With no parry: the player is free, and he comes back out of his gate, his middle on its opening, and drops to the
# floor under it.
func _emerge() -> void:
	_free_player()
	landed = false
	var lift := Monte.emerge_start_lift()
	emerge_centre = Vector2(0.0, -lift)
	emerge_height = maxf(Monte.DIVE_UNDER - lift, 0.0)
	_show_him(_emerge_floor())
	body.height = emerge_height
	body.place()
	body.set_air_draw(true)
	_shrink(1.0, emerge_centre)
	body.face_player()
	body.play_anim(&"emerge")
	var portal: Node2D = state_machine.hands.portal_of(dive_side)
	if portal != null:
		portal.feed()


# On the floor under his gate, with a thud: the drawn emerge scatters its own cards round his boots, the stand-in gets
# the fan of cards.
func _land() -> void:
	landed = true
	body.height = 0.0
	body.place()
	body.set_air_draw(false)
	if not Monte.final_emerge():
		_burst_cards(body.ground_position)
	body.land_sfx_player.play()
	body.shuffle_sfx_player.play()


# His Recover: landed from his gate, or out of his stagger with the parry's bonus. A parried real him opens it at once;
# otherwise he may go straight on into his next attack (JoshCardsStateMachine.end_attack).
func _finish() -> void:
	finished = true
	if not staggering and not landed:
		_land()
	var recover = state_machine.states.get("Recover")
	if recover != null and staggering:
		recover.bonus_time = state_machine.monte_parry_recover_bonus
	state_machine.end_attack(self, reds_parried > 0)


# The fan of cards, once, on a floor point (JoshCardsWildCards._flurry's pattern).
func _burst_cards(at: Vector2) -> void:
	var spec := JoshArtLayout.FINAL_CARD_BURST
	var fan := Sprite2D.new()
	fan.name = "MonteCardBurst"
	fan.texture = load(spec.texture)
	fan.hframes = spec.hframes
	fan.scale = Vector2.ONE * spec.scale
	fan.offset = spec.frame_size / 2.0 - spec.pivot
	state_machine.add_hazard(fan, at, body.get_parent())
	var times: Array = spec.frame_times
	var play := fan.create_tween()
	for i in range(1, spec.hframes):
		play.tween_interval(times[i - 1])
		play.tween_callback(fan.set_frame.bind(i))
	play.tween_interval(times[times.size() - 1])
	play.tween_callback(fan.queue_free)


#THE PLAYER

# Let go, and no longer turned to face anything.
func _free_player() -> void:
	if locked:
		locked = false
		state_machine.unlock_player()
		lock_times.append(clock)
	state_machine.clear_player_facing()


#WHERE THINGS ARE

func _gate(burst: int) -> Node2D:
	if burst < 0 or burst >= gates.size() or not is_instance_valid(gates[burst]):
		return null
	return gates[burst]


# The floor under his gate's opening that his dive ends over, with his middle on the opening.
func _dive_floor() -> Vector2:
	return Layout.PORTAL_POINTS[dive_side] + Vector2(-dive_centre.x, Monte.DIVE_UNDER)


# The floor under his gate's opening, where he lands coming back out.
func _emerge_floor() -> Vector2:
	return Layout.PORTAL_POINTS[dive_side] + Vector2(0.0, Monte.DIVE_UNDER)


func _nearer_side(spot: Vector2) -> StringName:
	var left := spot.distance_to(Layout.rest_point(&"left"))
	var right := spot.distance_to(Layout.rest_point(&"right"))
	return &"left" if left <= right else &"right"


func _standing() -> Vector2:
	return player.global_position if is_instance_valid(player) else state_machine.ROPES.get_center()


func _player_centre() -> Vector2:
	if not is_instance_valid(player):
		return _standing()
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	return shape.global_position
