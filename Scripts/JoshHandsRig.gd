extends Node

# Josh's two card-gate portals and the two card hands that come out of them, in his own fight (the user, 2026-09-29).
# His Summon (JoshCardsSummon) builds and opens them once a fight load and they are there from then on: the portals
# never move, and the hands rest at them except while his Hand Slam (JoshCardsHandSlam) drives them. At his Break the
# hands dissolve into the portals and his next cycle (JoshCardsStateMachine.start_cycle) forms them again; beaten, he
# takes them with him - the hands shatter and the portals close - and nothing forms again.
#
# THEY ARE NEVER HAZARDS: nothing here joins the fight's hazard group, which every Break, the end of the fight and the
# suite's resets free, and nothing here can be hit. They live on the fight's stage beside him, portals first, and this
# node only steers them: it draws nothing of its own.
# FREEZE SAFETY: no Timers, no tree timers and no tweens. Its motions - a hand flying home, dissolving, shattering -
# step on its own physics clock, so a pause or a finisher's freeze holds them, and only for a hand the attack isn't
# driving (JoshHand.driven).

const Layout := preload("res://Scripts/JoshHandsLayout.gd")
const JoshPortal := preload("res://Scripts/JoshPortal.gd")
const JoshHand := preload("res://Scripts/JoshHand.gd")

# Both set before it is added.
var body: CharacterBody2D
var state_machine: Node

var portals := {}
var hands := {}
var built := false
var collapsed := false
# A hand's motion in progress, by side: {kind, and for a flight home: from, lift, time, age}.
var motions := {}
var sound_players := {}


# Idempotent. Once he is beaten nothing is built again.
func build() -> void:
	if built or collapsed:
		return
	built = true
	var stage: Node = body.get_parent()
	for side in Layout.SIDES:
		var portal: Node2D = JoshPortal.make(side)
		stage.add_child(portal)
		portals[side] = portal
	for side in Layout.SIDES:
		var hand: Node2D = JoshHand.make(side)
		stage.add_child(hand)
		hands[side] = hand


# Both open at `speed`. The seconds that takes.
func open_portals(speed := 1.0) -> float:
	var seconds := 0.0
	for side in Layout.SIDES:
		var portal := portal_of(side)
		if portal != null:
			seconds = maxf(seconds, portal.open(speed))
	play_sound(&"portal_open")
	return seconds


# Both form at their rest points at `speed`, then hover there. The seconds that takes.
func form_hands(speed := 1.0) -> float:
	var seconds := 0.0
	for side in Layout.SIDES:
		var hand := hand_of(side)
		if hand == null:
			continue
		motions.erase(side)
		hand.retracted = false
		hand.place_rest(rest_point(side))
		seconds = maxf(seconds, hand.play(&"form", speed, false, &"hover"))
	play_sound(&"hand_form")
	return seconds


# Where a summon leaves them, however it ended: the portals looping, the hands resting at their portals.
func place_summoned() -> void:
	build()
	if collapsed:
		return
	for side in Layout.SIDES:
		var portal := portal_of(side)
		if portal != null:
			portal.loop_now()
		var hand := hand_of(side)
		if hand == null:
			continue
		motions.erase(side)
		hand.driven = false
		hand.retracted = false
		hand.place_rest(rest_point(side))
		if hand.clip != &"hover":
			hand.play(&"hover")


# How long until both hands rest at their portals, formed: what the Hand Slam waits before it starts.
func time_to_ready() -> float:
	var left := 0.0
	for side in Layout.SIDES:
		var hand := hand_of(side)
		if hand == null:
			continue
		var motion: Dictionary = motions.get(side, {})
		if motion.get("kind") == &"home":
			left = maxf(left, motion.time - motion.age)
		elif hand.mode == JoshHand.Mode.REST and hand.clip != &"hover":
			left = maxf(left, hand.clip_left())
	return left


# Every hand gone into its portal forms again at its rest point: his next cycle. Wild Cards doesn't wait for it; the
# Hand Slam does (time_to_ready).
func ensure_formed() -> void:
	if collapsed or not built:
		return
	for side in Layout.SIDES:
		var hand := hand_of(side)
		if hand == null or hand.driven:
			continue
		if hand.mode == JoshHand.Mode.HIDDEN or motions.get(side, {}).get("kind") == &"retract":
			motions.erase(side)
			hand.retracted = false
			hand.place_rest(rest_point(side))
			hand.play(&"form", 1.0, false, &"hover")
			play_sound(&"hand_form")


# A hand still out from an earlier string, in the air or on the floor, put back at its portal at once.
func snap_home() -> void:
	if collapsed:
		return
	for side in Layout.SIDES:
		var hand := hand_of(side)
		if hand == null:
			continue
		if hand.mode == JoshHand.Mode.AIR or hand.mode == JoshHand.Mode.GROUND or motions.get(side, {}).get("kind") == &"home":
			motions.erase(side)
			hand.driven = false
			hand.place_rest(rest_point(side))
			hand.play(&"hover")


# The hand flies back to its portal over `seconds`, harmless, and hovers there. One on the floor peels up off it as it
# goes; one that is gone re-forms at its portal instead.
func send_home(side: StringName, seconds: float) -> void:
	var hand := hand_of(side)
	if hand == null or collapsed:
		return
	hand.driven = false
	if hand.mode == JoshHand.Mode.HIDDEN:
		reform_home(side)
		return
	if hand.mode == JoshHand.Mode.REST:
		return
	if hand.mode == JoshHand.Mode.GROUND:
		hand.play_motion(&"lift", state_machine.hand_rise_time, &"hover")
	elif hand.clip != &"hover":
		hand.play(&"hover")
	motions[side] = {kind = &"home", from = hand.floor_at, lift = hand.height, time = maxf(seconds, 0.001), age = 0.0}


func reform_home(side: StringName) -> void:
	var hand := hand_of(side)
	if hand == null or collapsed:
		return
	hand.driven = false
	motions.erase(side)
	hand.retracted = false
	hand.place_rest(rest_point(side))
	hand.play_motion(&"reform", state_machine.hand_reform_time, &"hover")
	play_sound(&"hand_form")


# His Break: each hand dissolves into its portal from wherever it is, and stays gone until ensure_formed(). The
# portals stay open.
func retract() -> void:
	if collapsed or not built:
		return
	for side in Layout.SIDES:
		var hand := hand_of(side)
		if hand == null:
			continue
		hand.driven = false
		motions.erase(side)
		if hand.mode == JoshHand.Mode.HIDDEN:
			hand.retracted = true
			continue
		hand.play_motion(&"retract", Layout.RETRACT_TIME)
		motions[side] = {kind = &"retract"}


# He is beaten: each hand shatters where it is and is gone, both portals close and go, and nothing forms again.
func collapse() -> void:
	if collapsed:
		return
	collapsed = true
	var shattered := false
	for side in Layout.SIDES:
		var hand := hand_of(side)
		if hand == null:
			continue
		hand.driven = false
		motions.erase(side)
		if hand.mode == JoshHand.Mode.HIDDEN:
			hands.erase(side)
			hand.queue_free()
			continue
		hand.play(&"shatter")
		motions[side] = {kind = &"collapse"}
		shattered = true
	if shattered:
		play_sound(&"hand_shatter")
	var closed := false
	for side in Layout.SIDES:
		var portal := portal_of(side)
		if portal != null:
			portal.close()
			closed = true
	if closed:
		play_sound(&"portal_close")


func _physics_process(delta: float) -> void:
	for side in motions.keys():
		var hand := hand_of(side)
		if hand == null:
			motions.erase(side)
			continue
		if hand.driven:
			continue
		var motion: Dictionary = motions[side]
		match motion.kind:
			&"home":
				_fly_home(hand, motion, delta)
			&"retract":
				if hand.clip_done():
					motions.erase(side)
					hand.hide_hand()
					hand.retracted = true
			&"collapse":
				if hand.clip_done():
					motions.erase(side)
					hands.erase(side)
					hand.queue_free()


# Home in the air is the rest point from hover height, so the flight lands on the rest point without a jump.
func _fly_home(hand: Node2D, motion: Dictionary, delta: float) -> void:
	motion.age = minf(motion.age + delta, motion.time)
	var s := smoothstep(0.0, 1.0, motion.age / motion.time)
	var hover: float = state_machine.hand_hover_height
	var home := rest_point(hand.side) + Vector2(0.0, hover)
	hand.place_air(motion.from.lerp(home, s), lerpf(motion.lift, hover, s))
	if motion.age >= motion.time:
		motions.erase(hand.side)
		hand.place_rest(rest_point(hand.side))


func portal_point(side: StringName) -> Vector2:
	return Layout.PORTAL_POINTS[side]


func rest_point(side: StringName) -> Vector2:
	return Layout.rest_point(side)


func hand_of(side: StringName) -> Node2D:
	var hand = hands.get(side)
	return hand if is_instance_valid(hand) and not hand.is_queued_for_deletion() else null


func portal_of(side: StringName) -> Node2D:
	var portal = portals.get(side)
	return portal if is_instance_valid(portal) and not portal.is_queued_for_deletion() else null


# Its own players, made the first time each sound is asked for; each only if its file is in.
func play_sound(key: StringName) -> void:
	var spec: Dictionary = Layout.SOUNDS.get(key, {})
	if spec.is_empty() or not ResourceLoader.exists(spec.stream):
		return
	if not sound_players.has(key):
		var stream: AudioStream = load(spec.stream)
		var voices: Array[AudioStreamPlayer] = []
		for i in spec.voices:
			var sfx := AudioStreamPlayer.new()
			sfx.name = "%sSfx%d" % [String(key).to_pascal_case(), i]
			sfx.stream = stream
			sfx.pitch_scale = spec.pitch
			sfx.volume_db = spec.volume_db
			add_child(sfx)
			voices.append(sfx)
		sound_players[key] = voices
	var voices: Array = sound_players[key]
	for sfx: AudioStreamPlayer in voices:
		if not sfx.playing:
			sfx.play()
			return
	voices[0].play()
