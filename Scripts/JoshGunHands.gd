extends Node

# Josh's Gun Hands, to the user's design of 2026-09-29: "...when josh is doing his 3 card clone attack, have the hands
# move up and down vertically across the side of the arena and then stop for a second after 1.5 seconds of going up and
# down from both sides of the arena and preparing to shoot a laser beam, the hands should be in the shape of a gun ...
# and so this should keep the player moving when dealing with the 3 cards." A layer inside Wild Cards, on the hands
# JoshHandsRig owns: JoshCardsWildCards makes it, begins it as it enters, steps it and lets it go through its own
# release(). Seconds from Wild Cards' Enter, later by `lead` while the hands still form (the state machine's gun_*):
#   OUT     0.00  both leave their portals for their posts at the sides, folding into finger guns (gun_form)
#   SWEEP   0.40  up and down their row ranges, opposite ways, for 1.50 s (gun_idle)
#   CHARGE  1.90  they stop: the far hand glides onto the player's row and the near one onto a row gun_row_offset off,
#                 toward the side with more floor (choose_rows); each band shows exactly where it will hurt, and the
#                 yellow badge stands on the aimed band over the player (gun_charge)
#   FIRE    2.90  both fire on one frame (gun_fire): each beam hurts for gun_beam_live, half a heart
#   FADE    3.25  the beams fade, harmless, and the hands fly home unfolding (gun_form backwards)
#   BACK    3.45  the beams are gone
#   DONE    3.75  home, resting at their portals, handed back to the rig
# THE LAST CLONE WAITS FOR IT: Wild Cards holds its fifth hop until gun_clear_gap after the beams are gone
# (lets_last_hop). So when the last clone locks and its warning is worked out, nothing of this layer is left, and from
# then on the only hazards are the lanes the existing way-out guarantee is worked out from. The answers: step out of
# the band (71 px mid-floor; 132 px, 0.22 s, at worst, by the bottom rope where the aimed row is clamped; against a 1.0 s
# charge), or dash through the beam, which is a PERFECT DODGE; a player who stands still takes one hit a layer.
# RELEASE: release() is idempotent: the beams and their telegraphs go, the badge on the aiming hand is cleared (his
# Break only clears his own), the bars come back, and each hand is a hand again, sent home on the rig's clock. It
# starts no tween at a scene's teardown, when the bars have already left the tree. With the rig not built or
# wild_guns off the layer never starts, and the fifth hop is never held.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")
const GunBeam := preload("res://Scripts/JoshGunBeam.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

enum Phase { OUT, SWEEP, CHARGE, FIRE, FADE, BACK, DONE }

const BEAM_ID := &"josh_gun_beam"
# As DannyBossSlams': summed steps land a hair short of a scheduled time.
const STEP_TOLERANCE := 0.0001
# The badge is cleared as the beams fire; given this much longer, it never runs out a step early on summed steps.
const BADGE_SLACK := 0.1
# The flight out rises this far at its middle, px.
const OUT_ARC := 40.0
const FIRE_SHAKE_STEPS := 4
const FIRE_SHAKE_STEP := 0.03
# What results[] holds for a near miss through the dash's ghost, besides HitInfo.Result's.
const NEAR_MISS := -1

# Set before it is added.
var body: CharacterBody2D
var state_machine: Node

var active := false
var released := true
var lead := 0.0
var clock := 0.0
var phase := Phase.DONE
# [seconds from Enter, Phase], in order.
var schedule: Array = []
var next_entry := 0
var phase_start := 0.0
# When the flight home began, which runs on through the beams' going.
var back_start := 0.0
# Each hand's muzzle row as it stopped, and which of them aims at the player.
var rows := {}
var aimer := &""
# The badge's tip: on the aimed band's top edge, over where the player stood as the hands stopped.
var aim_point := Vector2.INF
var beams: Array = []
var fired_at := -1.0
var freed_at := -1.0
# For a test: each time a live band reached the player or, on its first frame, the dash's ghost ({side, result, at};
# NEAR_MISS for the ghost), and rows to pin ({aimer, rows}), empty to choose.
var results: Array[Dictionary] = []
var forced_rows := {}
var hands := {}
var player: Node2D
# Where each hand's flight started, and each muzzle's row as the charge began.
var flight_from := {}
var row_from := {}
# The muzzle flash and the charge effect on each hand's Draw node: {node, since}.
var flashes := {}
var charges := {}
var near_checked := false


# Wild Cards is entering: the layer starts if the guns are on and the hands are there to be guns.
func begin() -> void:
	active = false
	released = true
	results.clear()
	beams.clear()
	rows.clear()
	flight_from.clear()
	row_from.clear()
	flashes.clear()
	charges.clear()
	aimer = &""
	aim_point = Vector2.INF
	fired_at = -1.0
	freed_at = -1.0
	near_checked = false
	var rig: Node = state_machine.hands
	if not state_machine.wild_guns or rig == null or not rig.built or rig.collapsed:
		return
	hands.clear()
	var out_there := false
	for side in Layout.SIDES:
		var hand: Node2D = rig.hand_of(side)
		if hand == null:
			return
		hands[side] = hand
		out_there = out_there or hand.mode == JoshHand.Mode.AIR or hand.mode == JoshHand.Mode.GROUND
	if out_there:
		rig.snap_home()
	rig.ensure_formed()
	lead = rig.time_to_ready()
	player = state_machine.get_player()
	for side in hands:
		hands[side].driven = true
	clock = 0.0
	next_entry = 0
	phase = Phase.OUT
	phase_start = lead
	schedule = _schedule()
	active = true
	released = false
	_run_due()


func step(delta: float) -> void:
	if not active:
		return
	clock += delta
	_run_due()
	if not active:
		return
	_place_hands()
	_step_beams(delta)
	_step_fx()
	_contact()
	_fade_hud()


# Whether Wild Cards may make its fifth hop: with no layer running, or gun_clear_gap after its beams are gone.
func lets_last_hop() -> bool:
	return not active or (freed_at >= 0.0 and clock >= freed_at + state_machine.gun_clear_gap - STEP_TOLERANCE)


func release() -> void:
	if released:
		return
	released = true
	active = false
	_free_beams()
	_free_fx()
	if not is_instance_valid(body) or body.health_bar == null or not body.health_bar.is_inside_tree():
		return
	var aiming = hands.get(aimer)
	if is_instance_valid(aiming):
		ParryTell.clear(aiming)
	body.restore_hud()
	var rig: Node = state_machine.hands
	for side in hands:
		var hand: Node2D = hands[side]
		if not is_instance_valid(hand):
			continue
		hand.set_gun(false)
		hand.driven = false
		rig.send_home(side, state_machine.gun_back_time)


#THE SCHEDULE

func _schedule() -> Array:
	var sm = state_machine
	var at := lead
	var entries := [[at, Phase.OUT]]
	at += sm.gun_out_time
	entries.append([at, Phase.SWEEP])
	at += sm.gun_sweep_time
	entries.append([at, Phase.CHARGE])
	at += sm.gun_charge_time
	entries.append([at, Phase.FIRE])
	at += sm.gun_beam_live
	entries.append([at, Phase.FADE])
	entries.append([at + sm.gun_beam_fade, Phase.BACK])
	entries.append([at + sm.gun_back_time, Phase.DONE])
	return entries


func _run_due() -> void:
	while active and next_entry < schedule.size() and clock >= schedule[next_entry][0] - STEP_TOLERANCE:
		var entry: Array = schedule[next_entry]
		next_entry += 1
		_begin(entry[1], entry[0])


func _begin(new_phase: int, at: float) -> void:
	phase = new_phase
	phase_start = at
	var sm = state_machine
	match new_phase:
		Phase.OUT:
			for side in hands:
				var hand: Node2D = hands[side]
				flight_from[side] = hand.drawn_point()
				hand.set_gun(true)
				hand.play(&"gun_form")
				hand.place_air(flight_from[side], 0.0)
			sm.hands.play_sound(&"gun_form")
		Phase.SWEEP:
			for side in hands:
				hands[side].play(&"gun_idle")
		Phase.CHARGE:
			_stop()
		Phase.FIRE:
			_fire()
		Phase.FADE:
			back_start = at
			for beam in beams:
				if is_instance_valid(beam):
					beam.fade(sm.gun_beam_fade)
			for side in hands:
				flight_from[side] = hands[side].floor_at
				hands[side].play(&"gun_form", 1.0, true, &"hover")
			sm.hands.play_sound(&"gun_form")
		Phase.BACK:
			_free_beams()
			freed_at = clock
		Phase.DONE:
			_home()


#THE HANDS

func _place_hands() -> void:
	var sm = state_machine
	var t := clock - phase_start
	for side in hands:
		var hand: Node2D = hands[side]
		if not is_instance_valid(hand):
			continue
		var at := Vector2.INF
		match phase:
			Phase.OUT:
				if flight_from.has(side):
					var p := clampf(t / sm.gun_out_time, 0.0, 1.0)
					var start: Vector2 = flight_from[side]
					at = start.lerp(Layout.gun_pivot(side, _mid_row(side)), smoothstep(0.0, 1.0, p)) + Vector2(0.0, -OUT_ARC * sin(PI * p))
			Phase.SWEEP:
				at = Layout.gun_pivot(side, _sweep_row(side, t))
			Phase.CHARGE:
				var glide := smoothstep(0.0, 1.0, clampf(t / sm.gun_glide_time, 0.0, 1.0))
				at = Layout.gun_pivot(side, lerpf(row_from[side], rows[side], glide))
			Phase.FIRE:
				at = Layout.gun_pivot(side, rows[side])
			Phase.FADE, Phase.BACK:
				var p := clampf((clock - back_start) / sm.gun_back_time, 0.0, 1.0)
				var start: Vector2 = flight_from[side]
				at = start.lerp(Layout.rest_point(side), smoothstep(0.0, 1.0, p))
		if at != Vector2.INF:
			hand.place_air(at, 0.0)


func _mid_row(side: StringName) -> float:
	var span := Layout.gun_row_range(side)
	return (span.x + span.y) / 2.0


# Up and down the whole range from its middle, the left starting down the screen and the right up it, so they always
# go opposite ways.
func _sweep_row(side: StringName, t: float) -> float:
	var span := Layout.gun_row_range(side)
	var phase_offset := 0.0 if side == &"left" else PI
	return (span.x + span.y) / 2.0 + (span.y - span.x) / 2.0 * sin(TAU * t / state_machine.gun_sweep_period + phase_offset)


# Home: hands again, resting at their portals, the rig's again.
func _home() -> void:
	for side in hands:
		var hand: Node2D = hands[side]
		if not is_instance_valid(hand):
			continue
		hand.set_gun(false)
		hand.place_rest(Layout.rest_point(side))
		if hand.clip != &"hover":
			hand.play(&"hover")
		hand.driven = false
	active = false
	released = true
	if is_instance_valid(body):
		body.restore_hud()


#THE STOP AND THE SHOT

func _stop() -> void:
	var sm = state_machine
	var centre := _player_centre()
	var pick: Dictionary = forced_rows if not forced_rows.is_empty() else choose_rows(centre, sm.gun_row_offset)
	aimer = pick.aimer
	rows = pick.rows.duplicate()
	var aimed := Layout.gun_band(aimer, rows[aimer])
	aim_point = Vector2(clampf(centre.x, aimed.position.x, aimed.end.x), aimed.position.y).round()
	for side in hands:
		var hand: Node2D = hands[side]
		row_from[side] = hand.floor_at.y + Layout.gun_muzzle(side).y
		hand.play(&"gun_charge")
		var beam: Node2D = GunBeam.make(side, rows[side], Vector2(Layout.gun_posts()[side], rows[side]))
		beam.fight = sm
		beam.floor_layer = body.floor_layer
		sm.add_hazard(beam, beam.origin, body.sky_layer)
		beams.append(beam)
		_add_charge(side)
	ParryTell.telegraph(hands[aimer], BEAM_ID, sm.gun_charge_time + BADGE_SLACK, _badge_point)
	sm.hands.play_sound(&"gun_charge")


func _badge_point() -> Vector2:
	return aim_point


func _fire() -> void:
	var sm = state_machine
	ParryTell.clear(hands[aimer])
	fired_at = clock
	near_checked = false
	for side in hands:
		hands[side].play(&"gun_fire")
		_free_charge(side)
		_add_flash(side)
	for beam in beams:
		if is_instance_valid(beam):
			beam.fire()
	ScreenView.shake(get_tree(), sm.gun_fire_shake, FIRE_SHAKE_STEPS, FIRE_SHAKE_STEP)
	sm.hands.play_sound(&"gun_fire")


func _step_beams(delta: float) -> void:
	var sm = state_machine
	for beam in beams:
		if not is_instance_valid(beam):
			continue
		if phase == Phase.CHARGE:
			var into := clock - phase_start
			beam.step_tell(into / sm.gun_charge_time, into >= sm.gun_charge_time - Layout.GUN_TELL.flash_time - STEP_TOLERANCE)
		beam.step(delta)


# The first live band holding the player's hurtbox reaches them, and the i-frames space any more (Carter's beams'
# rule); on the first live frame, a band holding only the spot a dash just left is a near miss.
func _contact() -> void:
	if not is_instance_valid(player) or player.playerHealth <= 0:
		return
	var live := beams.filter(func(beam) -> bool: return is_instance_valid(beam) and beam.live)
	if live.is_empty():
		return
	var box := _rect_of(player.hurtBox.get_node("CollisionShape2D"))
	var touched := false
	for beam in live:
		if beam.band().intersects(box):
			touched = true
			if not player.is_invincible:
				var result: int = player.receive_hit(HitInfo.make(BEAM_ID, beam, box.get_center(), body))
				results.append({"side": beam.side, "result": result, "at": clock})
			break
	if near_checked:
		return
	near_checked = true
	if touched or player.dodge_ghost_position() == Vector2.INF:
		return
	var ghost := _rect_of(player.dodge_ghost.get_node("CollisionShape2D"))
	for beam in live:
		if beam.band().intersects(ghost):
			player.receive_near_miss(HitInfo.make(BEAM_ID, beam, ghost.get_center(), body))
			results.append({"side": beam.side, "result": NEAR_MISS, "at": clock})
			return


func _free_beams() -> void:
	for beam in beams:
		if is_instance_valid(beam):
			beam.queue_free()
	beams.clear()


# The bars fade while a band crosses them.
func _fade_hud() -> void:
	var over: Array[Rect2] = []
	for beam in beams:
		if is_instance_valid(beam):
			over.append(beam.band())
	body.update_hud_fade(over)


#THE FLASH AND THE CHARGE, on each hand's Draw node at its muzzle

func _add_charge(side: StringName) -> void:
	var hand: Node2D = hands[side]
	var spec: Dictionary = Layout.GUN_CHARGE_FX
	var fx: Node2D
	if ResourceLoader.exists(spec.texture):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.frames
		sheet.offset = spec.frame / 2.0 - spec.pivot
		fx = sheet
	else:
		var look: Dictionary = Layout.PLACEHOLDER_CHARGE
		var circle := Polygon2D.new()
		circle.polygon = _circle(look.radius, 20)
		circle.color = look.color
		var added := CanvasItemMaterial.new()
		added.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		circle.material = added
		fx = circle
	fx.name = "GunCharge"
	fx.position = hand.muzzle_local()
	hand.art.add_child(fx)
	charges[side] = {"node": fx, "since": clock}


func _add_flash(side: StringName) -> void:
	var hand: Node2D = hands[side]
	var spec: Dictionary = Layout.GUN_FLASH
	var fx: Node2D
	if ResourceLoader.exists(spec.texture):
		var sheet := Sprite2D.new()
		sheet.texture = load(spec.texture)
		sheet.hframes = spec.frame_times.size()
		sheet.scale = Vector2.ONE * Layout.SCALE
		sheet.offset = spec.frame / 2.0 - spec.pivot
		fx = sheet
	else:
		var look: Dictionary = Layout.PLACEHOLDER_FLASH
		var star := Polygon2D.new()
		var points := PackedVector2Array()
		for i in 2 * int(look.points):
			var radius: float = look.outer if i % 2 == 0 else look.inner
			points.append(Vector2.from_angle(PI * i / look.points) * radius)
		star.polygon = points
		star.color = look.color
		fx = star
	fx.name = "GunFlash"
	fx.position = hand.muzzle_local()
	hand.art.add_child(fx)
	flashes[side] = {"node": fx, "since": clock}


# The charge grows through its whole-number scales over the charge and loops (or pulses); the flash plays once and
# goes.
func _step_fx() -> void:
	var sm = state_machine
	for side in charges.keys():
		var fx = charges[side].node
		if not is_instance_valid(fx):
			charges.erase(side)
			continue
		var t: float = clock - charges[side].since
		var grown := float(Layout.charge_scale(t / sm.gun_charge_time + STEP_TOLERANCE))
		if fx is Sprite2D:
			var spec: Dictionary = Layout.GUN_CHARGE_FX
			fx.scale = Vector2.ONE * grown
			fx.frame = int(t / spec.frame_time) % int(spec.frames)
		else:
			var look: Dictionary = Layout.PLACEHOLDER_CHARGE
			fx.scale = Vector2.ONE * grown / Layout.SCALE
			fx.modulate.a = lerpf(look.low, 1.0, 0.5 + 0.5 * sin(TAU * t / look.pulse_time))
	for side in flashes.keys():
		var fx = flashes[side].node
		var times: Array = Layout.GUN_FLASH.frame_times
		var t: float = clock - flashes[side].since
		var total := 0.0
		var index := -1
		for i in times.size():
			total += float(times[i])
			if index < 0 and t < total:
				index = i
		if not is_instance_valid(fx) or index < 0:
			if is_instance_valid(fx):
				fx.queue_free()
			flashes.erase(side)
			continue
		if fx is Sprite2D:
			fx.frame = index
		else:
			fx.modulate.a = 1.0 - t / total


func _free_charge(side: StringName) -> void:
	var entry: Dictionary = charges.get(side, {})
	if is_instance_valid(entry.get("node")):
		entry.node.queue_free()
	charges.erase(side)


func _free_fx() -> void:
	for side in charges.keys():
		_free_charge(side)
	for side in flashes.keys():
		if is_instance_valid(flashes[side].node):
			flashes[side].node.queue_free()
	flashes.clear()


#THE ROWS

# Where the two stop, from the player's hurtbox centre `centre`: {aimer, rows: {side: row}}. The far hand - across the
# ring's middle from the player, so its beam crosses the whole ring - aims at their row, clamped to its range; below
# the left hand's reach the right one aims instead. The near hand cuts off a row `offset` away toward the side with more
# floor, clamped to its own range, or the other way if that leaves no room between the bands. On whole px, so a beam
# drawn on its row is its band to the pixel.
static func choose_rows(centre: Vector2, offset: float) -> Dictionary:
	var aim_side: StringName = &"right" if centre.x < Layout.GUN_RING_MID_X else &"left"
	if aim_side == &"left" and centre.y > Layout.gun_left_reach():
		aim_side = &"right"
	var other := Layout.other_side(aim_side)
	var aim_span := Layout.gun_row_range(aim_side)
	var cut_span := Layout.gun_row_range(other)
	var aimed := roundf(clampf(centre.y, aim_span.x, aim_span.y))
	var floor_span: Vector2 = Layout.GUN_FLOOR
	var way := -1.0 if aimed - floor_span.x > floor_span.y - aimed else 1.0
	var cut := roundf(clampf(aimed + way * offset, cut_span.x, cut_span.y))
	if absf(cut - aimed) < Layout.gun_row_gap():
		cut = roundf(clampf(aimed - way * offset, cut_span.x, cut_span.y))
	return {aimer = aim_side, rows = {aim_side: aimed, other: cut}}


#WHERE THINGS ARE

func _player_centre() -> Vector2:
	if not is_instance_valid(player):
		return state_machine.ROPES.get_center()
	return _rect_of(player.hurtBox.get_node("CollisionShape2D")).get_center()


func _rect_of(shape: CollisionShape2D) -> Rect2:
	return shape.global_transform * shape.shape.get_rect()


static func _circle(radius: float, points: int) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in points:
		out.append(Vector2.from_angle(TAU * i / points) * radius)
	return out
