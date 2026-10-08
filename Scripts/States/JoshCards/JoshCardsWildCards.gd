extends State

# Josh's first attack, Wild Cards - Twisted Fate's Q - to the user's design of 2026-09-28: "Josh
# teleports to random spots in the arena spawning clones and once hes spawned 5 clones relatively spaced
# out across the arena, josh will teleport off the screen and all clones will fire a twisted fate Q
# (wild cards) at the same time directly in front of them. These attacks are not parriable."
#   HOP     every wild_hop_time he gates to a new spot in a flurry of cards and stands there in his
#           throw's wind-up, and a clone of him is left on it, its three lanes laid on the floor toward
#           where the player is at that moment and locked there. He is drawn over it until he leaves.
#   WARN    from the fifth clone, wild_warning, drawn out if the player needs longer to walk clear
#           (below): wild_exit_beat in he gates off the screen, the lanes come up to full with the
#           yellow badge over every clone, and flash as the cards leave.
#   VOLLEY  all fifteen cards on one frame, wild_card_speed, straight down their lanes and through
#           everything until they leave the floor. Each lane stays drawn ahead of its card until the card
#           is gone. The clones scatter in a burst of cards wild_clone_linger after they throw.
#   RETURN  wild_return_beat after the last card, he gates back in away from the player, winded: his
#           Recover, the punish window.
# The cards can't be blocked or parried (josh_wild_card): the answer is to be out of every lane when they
# come, and a dash through a card is a PERFECT DODGE that gives the dash back.
#
# THE LANES ARE THE HIT AREA, TO THE PIXEL. A lane (lane_box) is every square a card covers on its way
# down it (card_box), from the throwing hand to where it leaves the floor, and a card is tested at both
# ends of its run. One oriented box draws the lanes, tests the cards against the player and finds the way
# out (box_corners, box_hits, _blocked_span), so what is drawn and what hurts can't drift apart, as
# BixbyCombinedArtLayout.beam_band keeps the spin's warning and its sweep one shape.
#
# THERE IS ALWAYS A WAY OUT ON FOOT when the warning starts, which is the moment the fifth clone locks.
# Its spot is chosen so that, with all fifteen lanes down, a place where the player's hurtbox, with
# ESCAPE_ROOM round it, touches none of them is inside the warning's walk, less wild_escape_reaction to
# see it (escape_time_from): the first spot that leaves one. If none does - the player has walked into the middle of the first four fans - the
# warning is drawn out to the walk to the nearest one, up to wild_warning_cap. Dashing through a lane is
# the other answer.
#
# ONE HIT AT A TIME. Every card is its own hit source, and a hit's i-frames cover whatever else of the
# volley reaches the player inside them; one that reaches them after they end lands too. A card never
# stops: one that hits flies on, and one dashed through was never touched. However many a dash goes
# through, a volley pays his Break gauge one read (pay_read).
#
# IT IS ONE STATE ON PURPOSE: the clones, their lanes, the cards and the badges are taken and given back
# as a unit through release(), which his Break (JoshCardsStateMachine.enter_broken) and the end of the
# fight go through too, and which always leaves him back in view where he last stood.
# FREEZE SAFETY: every wait is a Physics_Update accumulator and every flurry a node-bound tween.
#
# THE GUN HANDS (JoshGunHands, the addendum of 2026-09-29) are a layer inside it while the state machine's
# wild_guns is on: made here, begun as it enters, stepped first thing every step and let go first thing in
# release(). The fifth hop - the one that locks the last clone and works out the way out - waits until
# the layer's beams are gone (lets_last_hop), so the way out is worked out on the lanes alone.

const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const BossBroken := preload("res://Scripts/BossBroken.gd")
const JoshGunHands := preload("res://Scripts/JoshGunHands.gd")

const CARD_ID := &"josh_wild_card"
# The clones' spots are planned at the top of the attack from a pool of PLAN_POOL random spots that fit -
# inside the ropes with the throwing hand, clear of the HUD with the badge over them, far enough from the
# player - drawn in at most SPOT_TRIES: the best spread of PLAN_TRIES, each from a random first spot and
# then the one in the pool farthest from those before it. Random, but across the whole floor: a random
# pick among spots far enough apart left the first clones in the middle and no room for the last. The
# player walking up to a planned spot takes the plan out of order - the next planned spot they are clear
# of comes first - and only with none left does the one of SPOT_CHOICES fresh fits farthest from the rest
# take its place. The last may be swapped too, for one that leaves the player a way out; that is checked
# on the first ESCAPE_CANDIDATES.
const SPOT_TRIES := 400
const PLAN_POOL := 80
const SPOT_CHOICES := 24
const PLAN_TRIES := 10
const ESCAPE_CANDIDATES := 6
# The way-out search's rows, in px: finer than any gap a hurtbox fits through.
const ESCAPE_ROW_STEP := 4.0
# A way out has this much room all round the hurtbox: somewhere to stand, not a sliver only a pixel-perfect
# stop would fit.
const ESCAPE_ROOM := 6.0
# How far clear of a lane a hurtbox is put when the search steps past it: touching is a hit.
const ESCAPE_CLEARANCE := 1.0
# How far in from the side ropes a clone's feet stand, past the reach of its throwing hand, so its cards
# always leave over the floor; and up from the bottom rope.
const SPOT_HAND_MARGIN := 24.0
const SPOT_BOTTOM_MARGIN := 40.0
# The player's hurtbox around their body position, for when there is no player to measure.
const HURT_FALLBACK := Rect2(-18.0, -39.0, 36.0, 81.0)
# As CarterMessatsu's: summed 1/60 s steps fall a hair short of a round number.
const CLOCK_SLACK := 0.0001

@export var body : CharacterBody2D

@onready var state_machine = get_parent()

enum Beat { HOP, WARN, VOLLEY, RETURN }


# A clone he left, the three lanes it laid, where it stood and what it aimed at.
class Clone:
	var figure: Sprite2D
	var shadow: Sprite2D
	var feet := Vector2.ZERO
	var flip := false
	var aimed_at := Vector2.ZERO
	var lanes: Array[Lane] = []


# One lane: from `origin`, the clone's hand, along `dir` for `length` px, to where a card leaves the floor.
# `passed` is how far down it its card has gone.
class Lane:
	var origin := Vector2.ZERO
	var dir := Vector2.RIGHT
	var length := 0.0
	var passed := 0.0
	var band: Polygon2D
	var rim: Line2D


class Card:
	var node: Node2D
	var sprite: Sprite2D
	var lane: Lane
	var travelled := 0.0
	var since := 0.0
	# It hit the player, or reached the spot a dash left: neither happens twice.
	var landed := false
	var grazed := false


var beat := Beat.HOP
var beat_clock := 0.0
# What every sheet steps off.
var fx_clock := 0.0
# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var clones: Array[Clone] = []
var cards: Array[Card] = []
var warn_time := 0.0
# How long the player, standing where they were as the last clone locked, needed to walk clear: what the
# warning was held to.
var escape_time := 0.0
var fired_at := 0.0
# He has gated off the screen.
var gone := false
var scattered := false
var read_paid := false
# Where the clones are to stand, in order.
var plan: Array[Vector2] = []
# For a test or a still that has to know: the spots in order, and where he comes back; empty and INF pick.
var forced_spots: Array[Vector2] = []
var forced_return := Vector2.INF
var guns: Node


func _ready() -> void:
	guns = JoshGunHands.new()
	guns.name = "GunHands"
	guns.body = body
	guns.state_machine = state_machine
	add_child(guns)


func Enter() -> void:
	released = false
	beat = Beat.HOP
	beat_clock = 0.0
	fx_clock = 0.0
	clones.clear()
	cards.clear()
	gone = false
	scattered = false
	read_paid = false
	warn_time = state_machine.wild_warning
	escape_time = 0.0
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.hide_glider()
	body.set_air_draw(false)
	plan.clear()
	if forced_spots.is_empty():
		plan = plan_spots(_standing())
	if state_machine.wild_guns:
		guns.begin()
	_hop()


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent, and called from Exit(), _exit_tree() and, through the state machine, his Break and the end
# of the fight: everything of the attack goes, and he is back in view where he last stood - gated off
# the screen, on his last spot.
func release() -> void:
	if released:
		return
	released = true
	guns.release()
	for clone in clones:
		_free_clone(clone)
		for lane in clone.lanes:
			_free_lane(lane)
	for card in cards:
		if is_instance_valid(card.node):
			card.node.queue_free()
	cards.clear()
	if is_instance_valid(body):
		_show_him()


func Physics_Update(delta: float) -> void:
	guns.step(delta)
	beat_clock += delta
	fx_clock += delta
	_step_cards(delta)
	_step_clones()
	_step_lanes()
	match beat:
		Beat.HOP:
			if _due(beat_clock, state_machine.wild_hop_time) and (clones.size() < state_machine.wild_clones - 1 or guns.lets_last_hop()):
				_hop()
		Beat.WARN:
			if not gone and _due(beat_clock, state_machine.wild_exit_beat):
				_gate_off()
			if _due(beat_clock, warn_time):
				_fire()
		Beat.VOLLEY:
			if not scattered and _due(beat_clock, state_machine.wild_clone_linger):
				_scatter()
			if scattered and cards.is_empty():
				beat = Beat.RETURN
				beat_clock = 0.0
		Beat.RETURN:
			if _due(beat_clock, state_machine.wild_return_beat):
				_come_back()


func _due(clock: float, at: float) -> bool:
	return clock >= at - CLOCK_SLACK


# One read a volley at most, however many of its cards a dash goes through (JoshCardsScript.BREAK_EARNS).
# Anything that isn't one of this volley's cards is a read of its own.
func pay_read(hit: RefCounted) -> bool:
	if not cards.any(func(card: Card) -> bool: return card.node == hit.source):
		return true
	if read_paid:
		return false
	read_paid = true
	return true


#THE HOPS

# He leaves where he stands in a flurry of cards and comes in on the next spot in another, and a clone is
# left there laying its lanes on the player where they are now. The fifth starts the warning.
func _hop() -> void:
	beat_clock = 0.0
	var last: bool = clones.size() >= state_machine.wild_clones - 1
	var standing := _standing()
	var aim := _player_centre()
	var pick := _pick_spot(last, standing, aim)
	if body.air.visible:
		_flurry(body.ground_position)
	var clone := _make_clone(pick.feet, aim)
	clones.append(clone)
	body.ground_position = pick.feet
	body.place()
	body.flying_left = clone.flip
	body.play_anim(&"wild_hold")
	_flurry(pick.feet)
	body.shuffle_sfx_player.play()
	if not last:
		return
	escape_time = pick.escape
	warn_time = pick.warning
	beat = Beat.WARN
	for each in clones:
		ParryTell.telegraph(each.figure, CARD_ID, warn_time, _badge_anchor.bind(each))
	body.reveal_sfx_player.play()


# Where the next clone stands, and for the last one how long the player needs to walk clear of all
# fifteen lanes and the warning that gives them: {feet, escape, warning}. Random, spread out as far as
# the floor allows, inside the ropes, clear of the HUD and never on top of the player.
func _pick_spot(last: bool, standing: Vector2, aim: Vector2) -> Dictionary:
	var candidates := _spot_candidates(standing, last)
	var warning: float = state_machine.wild_warning
	var picked := {"feet": candidates[0], "escape": 0.0, "warning": warning}
	if not last:
		return picked
	var reaction: float = state_machine.wild_escape_reaction
	var cap: float = state_machine.wild_warning_cap
	var so_far := lane_boxes()
	var best := INF
	for i in mini(candidates.size(), ESCAPE_CANDIDATES):
		var feet: Vector2 = candidates[i]
		var boxes: Array[Dictionary] = []
		boxes.append_array(so_far)
		for lane in _lanes_from(_hand(feet, aim), aim):
			boxes.append(lane_box(lane.origin, lane.dir, lane.length, state_machine.wild_card_size))
		var escape := escape_time_from(boxes, standing, cap - reaction)
		if escape <= warning - reaction + CLOCK_SLACK:
			return {"feet": feet, "escape": escape, "warning": warning}
		if escape < best:
			best = escape
			picked.feet = feet
	# Nothing leaves a way out in the warning's time: the one nearest to it, and the warning drawn out.
	picked.escape = best
	picked.warning = clampf(best + reaction, warning, cap) if best < INF else cap
	return picked


# Where the next clone may stand: the next planned spot the player hasn't walked up to, then - for the last,
# or with none left - the fits farthest from every other clone, down or planned.
func _spot_candidates(standing: Vector2, last: bool) -> Array[Vector2]:
	var index := clones.size()
	var spots: Array[Vector2] = []
	if index < forced_spots.size():
		spots.append(forced_spots[index])
		return spots
	for k in range(index, plan.size()):
		if plan[k].distance_to(standing) >= state_machine.wild_player_clearance:
			var next := plan[k]
			plan[k] = plan[index]
			plan[index] = next
			spots.append(next)
			break
	if not spots.is_empty() and not last:
		return spots
	var others: Array[Vector2] = []
	for clone in clones:
		others.append(clone.feet)
	others.append_array(plan.slice(index + 1))
	spots.append_array(_fits_by_spread(others, standing))
	if spots.is_empty():
		spots.append(_spot_area().get_center().round())
	return spots


# The five spots for the clones, from the player standing at `standing`: the best spread of PLAN_TRIES.
func plan_spots(standing: Vector2) -> Array[Vector2]:
	var pool := _fits(standing, PLAN_POOL)
	var best: Array[Vector2] = []
	var best_spread := -1.0
	if pool.is_empty():
		return best
	for trial in PLAN_TRIES:
		var spots: Array[Vector2] = [pool.pick_random()]
		while spots.size() < state_machine.wild_clones:
			var pick: Vector2 = pool[0]
			var farthest := -1.0
			for feet in pool:
				var nearest := _nearest(feet, spots)
				if nearest > farthest:
					farthest = nearest
					pick = feet
			spots.append(pick)
		var spread := spread_of(spots)
		if spread > best_spread:
			best = spots
			best_spread = spread
	return best


# SPOT_CHOICES random spots that fit, the farthest from `others` first.
func _fits_by_spread(others: Array[Vector2], standing: Vector2) -> Array[Vector2]:
	var fits := _fits(standing, SPOT_CHOICES)
	fits.sort_custom(func(a: Vector2, b: Vector2) -> bool: return _nearest(a, others) > _nearest(b, others))
	return fits


# Up to `count` random spots that fit.
func _fits(standing: Vector2, count: int) -> Array[Vector2]:
	var area := _spot_area()
	var fits: Array[Vector2] = []
	for i in SPOT_TRIES:
		if fits.size() >= count:
			break
		var feet := Vector2(randf_range(area.position.x, area.end.x), randf_range(area.position.y, area.end.y)).round()
		if not JoshArtLayout.clear_of_hud(JoshArtLayout.standing_rect(feet)):
			continue
		if feet.distance_to(standing) < state_machine.wild_player_clearance:
			continue
		fits.append(feet)
	return fits


static func _nearest(feet: Vector2, others: Array[Vector2]) -> float:
	var nearest := INF
	for other in others:
		nearest = minf(nearest, feet.distance_to(other))
	return nearest


# The least distance between any two of `spots`.
static func spread_of(spots: Array[Vector2]) -> float:
	var spread := INF
	for a in spots.size():
		for b in range(a + 1, spots.size()):
			spread = minf(spread, spots[a].distance_to(spots[b]))
	return spread


func _spot_area() -> Rect2:
	var reach := absf(JoshArtLayout.local(JoshArtLayout.HAND_THROW).x) + SPOT_HAND_MARGIN
	return state_machine.ROPES.grow_individual(-reach, 0.0, -reach, -SPOT_BOTTOM_MARGIN)


# Out of sight, and out of the player's aim: nothing to face or punch where he stood.
func _gate_off() -> void:
	gone = true
	_flurry(body.ground_position)
	body.shuffle_sfx_player.play()
	body.air.hide()
	body.shadow.hide()
	body.set_target_active(false)


func _show_him() -> void:
	gone = false
	body.air.show()
	body.shadow.show()
	body.set_target_active(true)


#THE CLONES

# In his throw's wind-up, a cool see-through ghost of him on a faint copy of his shadow.
func _make_clone(feet: Vector2, aim: Vector2) -> Clone:
	var clone := Clone.new()
	clone.feet = feet
	clone.flip = aim.x < feet.x
	clone.aimed_at = aim
	var shadow_spec := JoshArtLayout.FINAL_SHADOW
	clone.shadow = Sprite2D.new()
	clone.shadow.texture = load(shadow_spec.texture)
	clone.shadow.hframes = shadow_spec.hframes
	clone.shadow.scale = Vector2.ONE * shadow_spec.scale
	clone.shadow.offset = shadow_spec.frame_size / 2.0 - shadow_spec.pivot
	clone.shadow.modulate.a = JoshArtLayout.WILD_CLONE_SHADOW_ALPHA
	state_machine.add_hazard(clone.shadow, feet + shadow_spec.offset, body.shadow.get_parent())
	var hold := JoshArtLayout.anim(&"wild_hold")
	var sheet: Texture2D = load(hold.sheet)
	clone.figure = Sprite2D.new()
	clone.figure.texture = sheet
	clone.figure.hframes = roundi(sheet.get_width() / JoshArtLayout.FRAME_SIZE.x)
	clone.figure.offset = JoshArtLayout.sheet_offset(JoshArtLayout.FRAME_SIZE)
	clone.figure.scale = Vector2.ONE * JoshArtLayout.SCALE
	clone.figure.frame = hold.frames[0]
	clone.figure.flip_h = clone.flip
	clone.figure.modulate = JoshArtLayout.WILD_CLONE_TINT
	var stage: Node2D = body.get_parent()
	state_machine.add_hazard(clone.figure, feet, stage)
	# First among equals in the y-sort, so while he stands on his own clone's spot he is drawn over it.
	stage.move_child(clone.figure, 0)
	for lane in _lanes_from(_hand(feet, aim), aim):
		_draw_lane(lane)
		clone.lanes.append(lane)
	return clone


# Waiting, they hold the wind-up; throwing, they run through the release and the follow-through and hold it.
func _step_clones() -> void:
	if beat != Beat.VOLLEY or scattered:
		return
	var throw_anim := JoshArtLayout.anim(&"throw")
	var steps := JoshArtLayout.WILD_RELEASE_STEPS
	var into := fx_clock - fired_at
	var step: int = steps[steps.size() - 1]
	for s in steps:
		into -= throw_anim.times[mini(s, throw_anim.times.size() - 1)]
		if into < 0.0:
			step = s
			break
	for clone in clones:
		if is_instance_valid(clone.figure):
			clone.figure.frame = throw_anim.frames[step]


func _scatter() -> void:
	scattered = true
	for clone in clones:
		if is_instance_valid(clone.figure):
			_flurry(clone.feet)
		_free_clone(clone)


func _free_clone(clone: Clone) -> void:
	if is_instance_valid(clone.figure):
		ParryTell.clear(clone.figure)
		clone.figure.queue_free()
	if is_instance_valid(clone.shadow):
		clone.shadow.queue_free()


func _badge_anchor(clone: Clone) -> Vector2:
	return clone.feet + JoshArtLayout.mirrored(JoshArtLayout.TELL_ANCHOR, clone.flip)


# Where a clone standing at `feet` and facing `aim` lets go of its cards: the throw's release hand-off.
func _hand(feet: Vector2, aim: Vector2) -> Vector2:
	return feet + JoshArtLayout.local(JoshArtLayout.HAND_THROW, aim.x < feet.x)


#THE LANES

# Three, wild_spread_degrees apart, the middle one straight at `aim`, each from the hand to where a card
# leaves the floor.
func _lanes_from(hand: Vector2, aim: Vector2) -> Array[Lane]:
	var to := aim - hand
	var base := to.angle() if to.length() > 1.0 else 0.0
	var spread := deg_to_rad(state_machine.wild_spread_degrees)
	var lanes: Array[Lane] = []
	for i in [-1, 0, 1]:
		var lane := Lane.new()
		lane.origin = hand
		lane.dir = Vector2.from_angle(base + i * spread)
		lane.length = room_to_edge(hand, lane.dir, state_machine.ROPES)
		lanes.append(lane)
	return lanes


# Every lane down now, as boxes.
func lane_boxes() -> Array[Dictionary]:
	var boxes: Array[Dictionary] = []
	for clone in clones:
		for lane in clone.lanes:
			boxes.append(lane_box(lane.origin, lane.dir, lane.length, state_machine.wild_card_size))
	return boxes


# What is still ahead of a lane's card, and so still hurts: all of it until the volley.
func live_box(lane: Lane) -> Dictionary:
	return lane_box(lane.origin + lane.dir * lane.passed, lane.dir, lane.length - lane.passed, state_machine.wild_card_size)


func _draw_lane(lane: Lane) -> void:
	lane.band = Polygon2D.new()
	lane.rim = Line2D.new()
	lane.rim.closed = true
	lane.rim.width = JoshArtLayout.WILD_LANE_RIM_WIDTH
	for node in [lane.band, lane.rim]:
		state_machine.add_hazard(node, Vector2.ZERO, body.floor_layer)
	_shape_lane(lane)
	_colour_lane(lane, JoshArtLayout.WILD_LANE_COLOR, JoshArtLayout.WILD_LANE_DIM_ALPHA)


func _shape_lane(lane: Lane) -> void:
	var corners := box_corners(live_box(lane))
	if is_instance_valid(lane.band):
		lane.band.polygon = corners
	if is_instance_valid(lane.rim):
		lane.rim.points = corners


# Faint while the clones go down, up to full through the warning and a flash as the cards leave; then
# each one shrinks ahead of its card until the card is gone.
func _step_lanes() -> void:
	var color := JoshArtLayout.WILD_LANE_COLOR
	var alpha := JoshArtLayout.WILD_LANE_DIM_ALPHA
	var flying := beat == Beat.VOLLEY or beat == Beat.RETURN
	if beat == Beat.WARN:
		var ramp := maxf(warn_time - JoshArtLayout.WILD_LANE_FLASH_TIME, CLOCK_SLACK)
		alpha = lerpf(JoshArtLayout.WILD_LANE_DIM_ALPHA, JoshArtLayout.WILD_LANE_FULL_ALPHA, clampf(beat_clock / ramp, 0.0, 1.0))
		if beat_clock >= ramp - CLOCK_SLACK:
			color = JoshArtLayout.WILD_LANE_FLASH_COLOR
			alpha = JoshArtLayout.WILD_LANE_FLASH_ALPHA
	elif flying:
		alpha = JoshArtLayout.WILD_LANE_FULL_ALPHA
	for clone in clones:
		for lane in clone.lanes:
			if flying:
				_shape_lane(lane)
			_colour_lane(lane, color, alpha)


func _colour_lane(lane: Lane, color: Color, alpha: float) -> void:
	if is_instance_valid(lane.band):
		lane.band.color = Color(color, alpha)
	if is_instance_valid(lane.rim):
		lane.rim.default_color = Color(color, minf(alpha * JoshArtLayout.WILD_LANE_RIM_ALPHA, 1.0))


func _free_lane(lane: Lane) -> void:
	for node in [lane.band, lane.rim]:
		if is_instance_valid(node):
			node.queue_free()


#THE VOLLEY

# All fifteen on one frame, one down each lane, each tested where it leaves the hand.
func _fire() -> void:
	if not gone:
		_gate_off()
	beat = Beat.VOLLEY
	beat_clock = 0.0
	fired_at = fx_clock
	read_paid = false
	for clone in clones:
		ParryTell.clear(clone.figure)
		for lane in clone.lanes:
			cards.append(_make_card(lane))
	# The clones let go on the frame the cards leave, not the one after.
	_step_clones()
	body.throw_sfx_player.play()
	for card in cards.duplicate():
		_contact(card)


func _make_card(lane: Lane) -> Card:
	var card := Card.new()
	card.lane = lane
	card.since = fx_clock
	card.node = Node2D.new()
	card.node.rotation = lane.dir.angle()
	var spec := JoshArtLayout.FINAL_THROWN_CARD
	card.sprite = Sprite2D.new()
	card.sprite.texture = load(spec.texture)
	card.sprite.hframes = spec.hframes
	card.sprite.scale = Vector2.ONE * spec.scale
	# The pivot is the card body's centre, which is what the square that hurts sits on; the trail follows.
	card.sprite.offset = spec.frame_size / 2.0 - spec.pivot
	card.node.add_child(card.sprite)
	state_machine.add_hazard(card.node, lane.origin, body.sky_layer)
	return card


# Each card runs its lane to the end - tested on the frame it gets there - and goes the frame after.
func _step_cards(delta: float) -> void:
	if cards.is_empty():
		return
	var spec := JoshArtLayout.FINAL_THROWN_CARD
	for card in cards.duplicate():
		if card.travelled >= card.lane.length or not is_instance_valid(card.node):
			cards.erase(card)
			_free_lane(card.lane)
			if is_instance_valid(card.node):
				card.node.queue_free()
			continue
		card.travelled = minf(card.travelled + state_machine.wild_card_speed * delta, card.lane.length)
		card.lane.passed = card.travelled
		card.node.global_position = (card.lane.origin + card.lane.dir * card.travelled).round()
		card.sprite.frame = int((fx_clock - card.since) / spec.frame_time) % int(spec.hframes)
		_contact(card)


# The card's square against the player's hurtbox: a hit, or - through a dash's immunity - a dodge the
# player's defence pays for. Clear of them, the square reaching the spot a dash left is a perfect dodge.
# No boss on the hit: nothing about a card staggers him.
func _contact(card: Card) -> void:
	if card.landed:
		return
	var player := _player()
	if player == null or player.playerHealth <= 0:
		return
	var box := card_box(card.lane.origin, card.lane.dir, card.travelled, state_machine.wild_card_size)
	if box_hits(box, _hurt_rect(player)):
		if player.receive_hit(HitInfo.make(CARD_ID, card.node, box.centre)) == HitInfo.Result.HIT:
			card.landed = true
		return
	if card.grazed or player.dodge_ghost_position() == Vector2.INF:
		return
	if box_hits(box, _rect_of(player.dodge_ghost.get_node("CollisionShape2D"))):
		card.grazed = true
		player.receive_near_miss(HitInfo.make(CARD_ID, card.node, box.centre))


#HIS WAY BACK IN

func _come_back() -> void:
	var feet := _return_spot()
	body.ground_position = feet
	body.place()
	_show_him()
	body.face_player()
	_flurry(feet)
	body.shuffle_sfx_player.play()
	state_machine.end_attack(self)


# Away from the player but a walk they can make inside his window: wild_return_range from them, on floor
# he stands on in view and clear of the HUD. The farthest spot tried, if none is in range.
func _return_spot() -> Vector2:
	if forced_return != Vector2.INF:
		return forced_return
	var from := _standing()
	var ground: Rect2 = body.ground_bounds(0.0)
	# Whole px strictly inside the ground: rounding must not carry a spot onto its far edges, which aren't in it.
	var lowest := ground.position.ceil()
	var highest := ground.end.ceil() - Vector2.ONE
	var span: Vector2 = state_machine.wild_return_range
	var farthest := ground.get_center().round()
	for i in SPOT_TRIES:
		var feet := Vector2(randf_range(ground.position.x, ground.end.x), randf_range(ground.position.y, ground.end.y)).round().clamp(lowest, highest)
		if not JoshArtLayout.clear_of_hud(JoshArtLayout.standing_rect(feet)):
			continue
		var away := feet.distance_to(from)
		if away >= span.x and away <= span.y:
			return feet
		if away > farthest.distance_to(from):
			farthest = feet
	return farthest


#THE WAY OUT

# How long the player standing at `from` needs to walk to where their hurtbox, with ESCAPE_ROOM round it,
# touches none of `boxes`, no longer than `limit`: INF if nowhere that near is clear. The two axes walk
# separately, so a walk of t seconds reaches a square around them; row by row across it, the nearest clear
# point is found exactly from the stretch of each row every box blocks.
func escape_time_from(boxes: Array[Dictionary], from: Vector2, limit: float) -> float:
	var speed := _walk_speed()
	var area: Rect2 = BossBroken.PLAYER_AREA
	var start := from.clamp(area.position, area.end)
	var hurt := _hurt_offset().grow(ESCAPE_ROOM)
	var reach := speed * limit
	var best := INF
	var dy := 0.0
	while dy <= reach and dy < best:
		for y in ([start.y] if dy == 0.0 else [start.y - dy, start.y + dy]):
			if y < area.position.y or y > area.end.y:
				continue
			var spans: Array[Vector2] = []
			for box in boxes:
				var span := _blocked_span(box, y, hurt)
				if span.x <= span.y:
					spans.append(span)
			best = minf(best, maxf(dy, _nearest_clear(spans, start.x, area)))
		dy += ESCAPE_ROW_STEP
	return best / speed if best <= reach else INF


# How far along a row from `x` the nearest body position is whose hurtbox touches none of `spans`, on the
# floor: INF if the row is shut both ways.
static func _nearest_clear(spans: Array[Vector2], x: float, area: Rect2) -> float:
	var best := INF
	for way in [-1.0, 1.0]:
		var at := x
		var moved := true
		while moved:
			moved = false
			for span in spans:
				if at >= span.x and at <= span.y:
					at = span.x - ESCAPE_CLEARANCE if way < 0.0 else span.y + ESCAPE_CLEARANCE
					moved = true
		if at >= area.position.x and at <= area.end.x:
			best = minf(best, absf(at - x))
	return best


# The body positions along row `y` whose hurtbox (`hurt`, around the body position) touches `box`, as the
# x-span (x, y) they run over: each of box_hits' four tests solved for x. Empty, x > y, if none do.
static func _blocked_span(box: Dictionary, y: float, hurt: Rect2) -> Vector2:
	var u: Vector2 = box.dir
	var n := u.orthogonal()
	var h: Vector2 = box.half
	var r := hurt.size / 2.0
	var centre: Vector2 = box.centre - hurt.get_center()
	var dy := y - centre.y
	if absf(dy) > r.y + h.x * absf(u.y) + h.y * absf(n.y):
		return Vector2(INF, -INF)
	var reach_x := r.x + h.x * absf(u.x) + h.y * absf(n.x)
	var span := Vector2(centre.x - reach_x, centre.x + reach_x)
	for axis in [[u, h.x + r.x * absf(u.x) + r.y * absf(u.y)], [n, h.y + r.x * absf(n.x) + r.y * absf(n.y)]]:
		var along: Vector2 = axis[0]
		var limit: float = axis[1]
		var fixed := dy * along.y
		if absf(along.x) < 1e-6:
			if absf(fixed) > limit:
				return Vector2(INF, -INF)
			continue
		var a := (-limit - fixed) / along.x
		var b := (limit - fixed) / along.x
		span = Vector2(maxf(span.x, centre.x + minf(a, b)), minf(span.y, centre.x + maxf(a, b)))
	return span


func _walk_speed() -> float:
	var player := _player()
	return float(player.SPEED) if player else 600.0


# The player's hurtbox, relative to where their body stands.
func _hurt_offset() -> Rect2:
	var player := _player()
	if player == null:
		return HURT_FALLBACK
	var rect := _hurt_rect(player)
	return Rect2(rect.position - player.global_position, rect.size)


#THE SHAPES
# An oriented box is {centre, dir, half}: `half` is how far it reaches along `dir` and across it.

# A lane's band: every square a card covers on its way down it, from the hand to where it leaves the
# floor. What the lane draws, and what the way out keeps clear of.
static func lane_box(origin: Vector2, dir: Vector2, length: float, size: float) -> Dictionary:
	return {"centre": origin + dir * (length / 2.0), "dir": dir, "half": Vector2(length / 2.0 + size / 2.0, size / 2.0)}


# A card's square, `travelled` px down its lane: what hurts.
static func card_box(origin: Vector2, dir: Vector2, travelled: float, size: float) -> Dictionary:
	return {"centre": origin + dir * travelled, "dir": dir, "half": Vector2.ONE * size / 2.0}


static func box_corners(box: Dictionary) -> PackedVector2Array:
	var u: Vector2 = box.dir
	var n := u.orthogonal()
	var h: Vector2 = box.half
	var c: Vector2 = box.centre
	return PackedVector2Array([c - u * h.x - n * h.y, c + u * h.x - n * h.y, c + u * h.x + n * h.y, c - u * h.x + n * h.y])


# Whether an oriented box touches an axis-aligned rect: separated along none of the four axes.
static func box_hits(box: Dictionary, rect: Rect2) -> bool:
	var u: Vector2 = box.dir
	var n := u.orthogonal()
	var h: Vector2 = box.half
	var d: Vector2 = rect.get_center() - box.centre
	var r := rect.size / 2.0
	if absf(d.x) > r.x + h.x * absf(u.x) + h.y * absf(n.x):
		return false
	if absf(d.y) > r.y + h.x * absf(u.y) + h.y * absf(n.y):
		return false
	if absf(d.dot(u)) > h.x + r.x * absf(u.x) + r.y * absf(u.y):
		return false
	return absf(d.dot(n)) <= h.y + r.x * absf(n.x) + r.y * absf(n.y)


# How far along `dir` from `from`, inside `rect`, its edge is.
static func room_to_edge(from: Vector2, dir: Vector2, rect: Rect2) -> float:
	var room := INF
	if absf(dir.x) > 1e-6:
		room = minf(room, ((rect.end.x if dir.x > 0.0 else rect.position.x) - from.x) / dir.x)
	if absf(dir.y) > 1e-6:
		room = minf(room, ((rect.end.y if dir.y > 0.0 else rect.position.y) - from.y) / dir.y)
	return maxf(room, 0.0)


#WHAT IS DRAWN

# His gate out and in and a clone scattering: the fan of cards, once, stood on the floor point.
func _flurry(feet: Vector2) -> void:
	var spec := JoshArtLayout.FINAL_CARD_BURST
	var fan := Sprite2D.new()
	fan.texture = load(spec.texture)
	fan.hframes = spec.hframes
	fan.scale = Vector2.ONE * spec.scale
	fan.offset = spec.frame_size / 2.0 - spec.pivot
	state_machine.add_hazard(fan, feet, body.get_parent())
	var times: Array = spec.frame_times
	var play := fan.create_tween()
	for i in range(1, spec.hframes):
		play.tween_interval(times[i - 1])
		play.tween_callback(fan.set_frame.bind(i))
	play.tween_interval(times[times.size() - 1])
	play.tween_callback(fan.queue_free)


#WHERE THINGS ARE

func _player() -> Node2D:
	var player: Node2D = state_machine.get_player()
	return player if is_instance_valid(player) else null


func _standing() -> Vector2:
	var player := _player()
	return player.global_position if player else state_machine.ROPES.get_center()


func _player_centre() -> Vector2:
	var player := _player()
	if player == null:
		return state_machine.ROPES.get_center()
	return _hurt_rect(player).get_center()


func _hurt_rect(player: Node2D) -> Rect2:
	return _rect_of(player.hurtBox.get_node("CollisionShape2D"))


func _rect_of(shape: CollisionShape2D) -> Rect2:
	return shape.global_transform * shape.shape.get_rect()
