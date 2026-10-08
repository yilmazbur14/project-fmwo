extends State

# Josh's summon, to the user's design of 2026-09-29: "Josh at the beginning of the fight will summon two portals above
# him to the right and to the left of him, he will then send a flurry of cards into the portals creating two big hands
# coming out of the portals made entirely of cards, the portals do not move with josh, they stay where the spawened
# the whole fight." Once a fight load, right after the VS card and before his first attack:
#   RAISE   0.00  he raises his hands (summon, then summon_hold), facing the player
#   OPEN    0.20  both portals open at JoshHandsLayout.PORTAL_POINTS, with a small shake
#   FLURRY  0.55  sixteen cards, eight a portal and a side at a time, card_gap apart, each flying card_flight from the
#                 hand on its side up an arc into its portal, which flares as it takes it
#   FORM    1.70  a hand forms out of each portal at its rest point and hovers there
#   IDLE    2.30  he drops his hands
#   END     2.50  the fight starts: his first attack (JoshCardsStateMachine.start_cycle)
# A retry in the same run plays the quick one (JoshHandsLayout.SUMMON_QUICK): the portals open and the hands form at
# 1.5x, no flurry, 0.60 s. The player is free all through it, and a held ESC skips it: its BossEntrance is begun with
# no player, for the hint and the hold only, as Captain Burak's laugh cut uses one.
#
# EVERY WAY OUT GOES THROUGH finish_summon(), which is idempotent and leaves the same end state however it came: the
# portals looping, the hands resting at their portals, no card in the air, him idle and facing the player where he
# stood, the hint retired. Exit() is it without starting the fight, so a harness that starts the fight over the top
# of it finds the portals and the hands in place. It never has a finish_entrance(), skip() or skip_to_fight(): the
# defence suite finds a fight's entrance by the first.
# FREEZE SAFETY: every beat runs off one Physics_Update clock, and the cards fly on it.

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshArtLayout := preload("res://Scripts/JoshArtLayout.gd")
const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

# As DannyBossSlams': summed steps land a hair short of a scheduled time.
const STEP_TOLERANCE := 0.0001

@export var body : CharacterBody2D

@onready var state_machine = get_parent()


# One card of the flurry, from his hand up an arc through `via` into its portal.
class Card:
	var node: Node2D
	var sprite: Sprite2D
	var side := &""
	var from := Vector2.ZERO
	var via := Vector2.ZERO
	var to := Vector2.ZERO
	var launched := 0.0


# Enter() has run, so there is a summon to end.
var entered := false
# It is over, one way or another. finish_summon() is the only thing that sets it.
var finished := true
# A retry in the same run: the short one.
var quick := false
var clock := 0.0
var cards: Array[Card] = []
# The skip and its hint, up for the whole of it.
var entrance: CanvasLayer
var launched := 0
var opened := false
var formed := false
var idled := false
# For a test: each card as it went into its portal ({side, at}), and the clock the summon ended on.
var arrivals: Array[Dictionary] = []
var ended_at := -1.0


func Enter() -> void:
	entered = true
	finished = false
	quick = BossEntrance.already_seen(Layout.SUMMON_SEEN_KEY)
	clock = 0.0
	launched = 0
	opened = false
	formed = false
	idled = false
	arrivals.clear()
	ended_at = -1.0
	body.fly_velocity = Vector2.ZERO
	body.height = 0.0
	body.place()
	body.hide_glider()
	body.set_air_draw(false)
	body.set_hurtbox_active(false)
	body.set_target_active(true)
	body.air.show()
	body.shadow.show()
	body.face_player()
	if not quick:
		body.play_anim(&"summon", &"summon_hold")
	state_machine.hands.build()
	entrance = BossEntrance.new()
	entrance.name = "SummonSkip"
	add_child(entrance)
	entrance.skipped.connect(skip_summon)
	entrance.begin()
	_run_due()


func Exit() -> void:
	finish_summon(false)


func _exit_tree() -> void:
	_free_cards()


func Physics_Update(delta: float) -> void:
	if finished:
		return
	clock += delta
	_run_due()
	if not finished:
		_step_cards()


func _beats() -> Dictionary:
	return Layout.SUMMON_QUICK if quick else Layout.SUMMON


func _due(at: float) -> bool:
	return clock >= at - STEP_TOLERANCE


# Every beat that is due, in order.
func _run_due() -> void:
	var beats := _beats()
	if not opened and _due(beats.open):
		opened = true
		state_machine.hands.open_portals(beats.open_speed)
		var shake: Dictionary = beats.open_shake
		ScreenView.shake(get_tree(), shake.strength, shake.steps, shake.step)
	if not quick:
		while launched < 2 * beats.cards and _due(beats.flurry + launched * beats.card_gap):
			_launch(launched, beats)
			launched += 1
	if not formed and _due(beats.form):
		formed = true
		state_machine.hands.form_hands(beats.form_speed)
	if not quick and not idled and _due(beats.idle):
		idled = true
		body.face_player()
		body.play_anim(&"idle")
	if _due(beats.end):
		finish_summon(true)


#THE FLURRY

# Card `index` leaves the hand drawn on its side, the sides taking turns, on the stage over the ropes: not on the
# SkyLayer, whose cards are his Wild Cards' volley.
func _launch(index: int, beats: Dictionary) -> void:
	var side: StringName = Layout.SIDES[index % Layout.SIDES.size()]
	var spec := JoshArtLayout.FINAL_THROWN_CARD
	var card := Card.new()
	card.side = side
	card.from = Layout.card_origin(side, body.ground_position, body.sprite.flip_h, body.sprite.frame)
	card.to = state_machine.hands.portal_point(side)
	card.via = (card.from + card.to) / 2.0 + Vector2(0.0, -beats.arc_rise)
	card.launched = beats.flurry + index * beats.card_gap
	card.node = Node2D.new()
	card.node.name = "SummonCard"
	card.node.z_index = beats.card_z
	card.sprite = Sprite2D.new()
	card.sprite.texture = load(spec.texture)
	card.sprite.hframes = spec.hframes
	card.sprite.scale = Vector2.ONE * spec.scale
	card.sprite.offset = spec.frame_size / 2.0 - spec.pivot
	card.node.add_child(card.sprite)
	state_machine.add_hazard(card.node, card.from, body.get_parent())
	cards.append(card)
	_place_card(card, beats)


func _step_cards() -> void:
	var beats := _beats()
	for card in cards.duplicate():
		if not is_instance_valid(card.node):
			cards.erase(card)
		elif _due(card.launched + beats.card_flight):
			_arrive(card)
		else:
			_place_card(card, beats)


# Along its arc, turned along it and spinning, shrinking over the last of its flight and fading at the very end.
func _place_card(card: Card, beats: Dictionary) -> void:
	var spec := JoshArtLayout.FINAL_THROWN_CARD
	var age := maxf(clock - card.launched, 0.0)
	var s := clampf(age / beats.card_flight, 0.0, 1.0)
	var u := 1.0 - s
	card.node.global_position = (card.from * u * u + card.via * 2.0 * u * s + card.to * s * s).round()
	card.node.rotation = ((card.via - card.from) * u + (card.to - card.via) * s).angle()
	card.sprite.frame = int(age / spec.frame_time) % int(spec.hframes)
	var shrink := clampf((s - 1.0 + beats.shrink_share) / beats.shrink_share, 0.0, 1.0)
	card.node.scale = Vector2.ONE * lerpf(1.0, beats.shrink_to, shrink)
	card.node.modulate.a = 1.0 - clampf((s - 1.0 + beats.fade_share) / beats.fade_share, 0.0, 1.0)


# Into its portal's pivot and gone, with the portal's flare and a quiet tick.
func _arrive(card: Card) -> void:
	cards.erase(card)
	card.node.global_position = card.to.round()
	arrivals.append({side = card.side, at = card.node.global_position})
	card.node.queue_free()
	var portal: Node2D = state_machine.hands.portal_of(card.side)
	if portal != null:
		portal.feed()
	state_machine.hands.play_sound(&"card_in")


func _free_cards() -> void:
	for card in cards:
		if is_instance_valid(card.node):
			card.node.queue_free()
	cards.clear()


#ENDING IT

# The one way it ends: its last beat, a held skip, or the fight going on over the top of it (Exit(), with
# `start_fight` false). Idempotent.
func finish_summon(start_fight := true) -> void:
	if finished or not entered:
		return
	finished = true
	ended_at = clock
	_free_cards()
	state_machine.hands.place_summoned()
	body.air.show()
	body.shadow.show()
	body.face_player()
	body.play_anim(&"idle")
	BossEntrance.mark_seen(Layout.SUMMON_SEEN_KEY)
	if is_instance_valid(entrance):
		entrance.end()
	entrance = null
	if start_fight:
		state_machine.start_cycle()


# What a held ui_cancel does: the arena settled, and the summon's end, all at once.
func skip_summon() -> void:
	if finished or not entered or state_machine.current_state != self:
		return
	BossEntrance.settle_arena(get_tree())
	finish_summon(true)
