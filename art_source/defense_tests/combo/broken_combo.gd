extends RefCounted

# broken_combo fight=<fight>: the combo with no timing in a boss's opening (the user, 2026-09-30: "lets remove the
# timed 3 hit combo all together and just have it so the user has to hit the boss 3 times for the uppercut mash to
# appear"). Every punch that lands counts one and the third is the POW; the POW, the finisher, a punch landed on
# another target, Matt's scream and PlayerCombo.COMBO_RESET_TIME without a punch landing (the user, 2026-10-04)
# start the count again. The mode keeps the name it had while combos broke; combo_reset has the reset's own cases.
# --fixed-fps 60.
#   carries   one punch, then a whiff out of his reach, a press SLOW_FRAMES on and a refusal (his hurtbox switched
#             off under the fist): the count is still 1 through the whiff (PlayerCombo.punch_missed), it has started
#             again by the slow press, past COMBO_RESET_TIME, the counter's 1 HIT faded with it, the slow punch lands
#             as a first, 1 HIT, and the count is still 1 through the refusal.
#   carried   two punches, then a new opening inside COMBO_RESET_TIME, the count still 2, and a press mashed
#             mid-swing: the opening's first punch to land is the POW - charged, its damage whole, 3 POW! - the
#             count starts again, and the finisher's mash opens if he can be dazed right then, and not if he can't.
#   spent     each opening takes the damage of a clean chain of its cap's punches (PunchAllowance): 4 for the
#             usual cap of 3, and a window with a `hit_cap` of its own scales the same way. From a fresh count, with
#             no daze to give, the chain lands punch for punch, POW and all, then the next punch is refused with
#             PlayerCombo.punch_refused, the dull deflect's spark where the fist met him and its thud, and the count
#             kept through it.
#   switch    a punch landing on another target (a stand-in with a hurtbox of its own) starts the count again at
#             1, and so does the next one back on him.
#   opening   his hurtbox switched off under the fist and back on the frame after the arm is out, as an opening
#             that starts right then does: the punch lands, and nothing is refused.
#   closed    a punch at him in his Idle, his hurtbox switched off, is refused the same way (PlayerPunching), and
#             the count kept through it: the refusal never starts it again, though COMBO_RESET_TIME may run out
#             under the swing.
#   counter   after a landed punch the combo counter is up over the player's head, centred on it and whole on the
#             screen.
# Eric's one cap is his parry stagger's (EricScript.PARRY_STAGGER_HIT_CAP), so his fight runs there, where he
# can't be dazed. Matt screams at a whiff or a refusal once a punch short of the POW has landed in his window
# (SCREAMS): his carries has no whiff or refusal in it, and a screamed case has one punch and a whiff take the
# count and the opening away. matt_scream has the rest.

const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const ERIC_BODY := "Arena/EricBossScene/CharacterBody2D"
# Fights whose boss screams at a miss after a punch short of the POW, and ends his opening with it: no whiff or
# refusal is left to count on in one of their openings. None today: Matt's (the user's 2026-09-27 playtest) is off
# in the live game since 2026-10-05 (MattStateMachine.scream_on_miss), and matt_scream holds it with the knob on.
const SCREAMS := []
# A slow press: 1.5 s after the last swing, past PlayerCombo.COMBO_RESET_TIME and the counter's fade with it.
const SLOW_FRAMES := 90
# The mashed press's frame of the swing, the arm still on its way out.
const MASH_AFTER := 4
# How far from the spot under his hurtbox a whiff stands: well out of the fist's reach.
const WHIFF_STEP := 200.0
# The stand-in's hurtbox, and how far to the side of his it stands.
const STAND_IN_SIZE := Vector2(60, 60)
const STAND_IN_OFFSET := 350.0


# A second target for the switch: a body the fist reaches through a hurtbox of its own in the boss target group,
# which takes every punch whole and notes what it was asked to take.
class StandIn extends Node2D:
	var sprite := Sprite2D.new()
	var hurtbox := Area2D.new()
	var asked: Array = []

	func _init(size: Vector2) -> void:
		add_child(sprite)
		hurtbox.name = "Hurtbox"
		var shape := CollisionShape2D.new()
		shape.name = "CollisionShape2D"
		var rect := RectangleShape2D.new()
		rect.size = size
		shape.shape = rect
		hurtbox.add_child(shape)
		add_child(hurtbox)

	func take_punch(amount: int) -> int:
		asked.append(amount)
		return amount


static func run(t) -> void:
	var key: String = t.fight
	if key != "eric" and not t.PUNISH_WINDOWS.has(key):
		t.check(false, "broken_combo knows no opening for fight=%s" % key)
		return
	await t.load_fight(key, t.STATE_INTROS.has(key))
	await t.clear_intro(key)
	# A fight whose intro is a state of its own comes out of it into the VS card, which holds the player's
	# presses (load_gauged's rule).
	if t.STATE_INTROS.has(key):
		await t.wait_until(func(): return t.vs_card() != null and t.vs_card().is_playing(), t.VS_CARD_WAIT_FRAMES)
		await t.skip_vs_card()
	t.player.playerHealth = 1000
	t.boss = t.current_scene.get_node(ERIC_BODY if key == "eric" else t.PUNISH_WINDOWS[key][0])
	t.sm = t.boss.state_machine
	# The physics frame of each refusal.
	var refused := []
	t.player.combo.punch_refused.connect(func(_target): refused.append(Engine.get_physics_frames()))

	await carries(t, key, refused)
	await carried(t, key)
	if SCREAMS.has(key):
		await screamed(t, key)
	await spent(t, key, refused)
	await switch(t, key)

	t.log_p("-- opening: his hurtbox back on the frame after the arm is out")
	refused.clear()
	await open(t, key)
	var hurtbox: Area2D = t.boss.get_finisher_hurtbox()
	hurtbox.set_deferred("monitoring", false)
	hurtbox.set_deferred("monitorable", false)
	await t.wait(3)
	var off_at_contact := [false]
	var switch_on := func():
		off_at_contact[0] = not hurtbox.monitorable
		hurtbox.set_deferred("monitoring", true)
		hurtbox.set_deferred("monitorable", true)
	var late: Dictionary = await punch(t, "fresh", switch_on)
	t.check(off_at_contact[0] and late.dealt > 0 and refused.is_empty(),
		"off as the arm came out, it lands, and nothing is refused (%s, %d dealt, %d refusals)" % [off_at_contact[0], late.dealt, refused.size()])
	await settle(t)

	t.log_p("-- closed: a punch at him in his Idle")
	refused.clear()
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	await t.wait(4)
	for timer in t.boss.find_children("*", "Timer", true, false):
		timer.stop()
	t.place_under(hurtbox)
	await t.wait(6)
	# The opening's punch landed about a second ago, so its count may run out under this swing: only that may
	# start it again, never the refusal.
	var combo: Node = t.player.combo
	var resets := []
	var on_changed := func(count: int, _charged: bool):
		if count == 0:
			resets.append(combo.since_landed)
	combo.combo_changed.connect(on_changed)
	var r: Dictionary = await punch(t, "fresh")
	combo.combo_changed.disconnect(on_changed)
	t.check(not hurtbox.monitorable and r.dealt == 0 and refused.size() == 1, "his hurtbox off, the punch is refused (%d dealt, %d refusals)" % [r.dealt, refused.size()])
	if refused.size() == 1:
		t.check(refused[0] - r.extended_at <= t.player.combo.REPORT_FRAMES and refused[0] < r.ended_at,
			"as it meets him, with the arm still out: %d frames after it came out, %d before the swing ended" % [refused[0] - r.extended_at, r.ended_at - refused[0]])
	var ran_out: bool = r.count == 0 and resets.size() == 1 and resets[0] >= combo.COMBO_RESET_TIME - 0.0001
	t.check(r.count == r.count_before or ran_out, "and the count kept through it, or run out under it %.3f s after the last punch landed (%d, %d)" % [resets[0] if resets.size() > 0 else -1.0, r.count_before, r.count])
	check_deflect(t, r)


# One punch, then a whiff, a slow press and a refusal. The whiff and the refusal don't start the count again; the
# slow press, past PlayerCombo.COMBO_RESET_TIME, finds it started again. Matt screams at the whiff and the refusal
# (SCREAMS), so his is the punch and the slow press alone.
static func carries(t, key: String, refused: Array) -> void:
	var screams := SCREAMS.has(key)
	t.log_p("-- carries: one punch, then %sa slow press%s" % ["" if screams else "a whiff and ", "" if screams else " and a refusal"])
	refused.clear()
	await open(t, key)
	var spot: Vector2 = t.player.global_position
	var combo: Node = t.player.combo
	var missed := [0]
	var on_missed := func(): missed[0] += 1
	combo.punch_missed.connect(on_missed)
	var first: Dictionary = await punch(t, "fresh")
	await check_counter(t)
	var steps := [first]
	if not screams:
		await t.settle_player(whiff_spot(t, spot))
		await t.wait(6)
		var whiff: Dictionary = await punch(t, "fresh")
		steps.append(whiff)
		await t.settle_player(spot)
		await t.wait(6)
		t.check(whiff.dealt == 0 and missed[0] == 1 and refused.is_empty() and whiff.count == 1,
			"the whiff lands nothing and is known missed, and the count is still 1 (%d dealt, %d missed, %d refused, count %d)" % [whiff.dealt, missed[0], refused.size(), whiff.count])
	var slow: Dictionary = await punch(t, "slow")
	steps.append(slow)
	if not screams:
		var hurtbox: Area2D = t.boss.get_finisher_hurtbox()
		hurtbox.set_deferred("monitoring", false)
		hurtbox.set_deferred("monitorable", false)
		await t.wait(3)
		var refusal: Dictionary = await punch(t, "fresh")
		steps.append(refusal)
		hurtbox.set_deferred("monitoring", true)
		hurtbox.set_deferred("monitorable", true)
		await t.wait(3)
		t.check(refusal.dealt == 0 and refused.size() == 1 and refusal.count == 1,
			"the refusal deals nothing, and the count is still 1 (%d dealt, %d refused, count %d)" % [refusal.dealt, refused.size(), refusal.count])
	combo.punch_missed.disconnect(on_missed)
	t.log_p("dealt %s, counts %s, the counter's alpha as each press went in %s" % [steps.map(func(s): return s.dealt), steps.map(func(s): return s.count),
		steps.map(func(s): return snappedf(s.counter_before, 0.01))])
	t.check(first.dealt == 1 and first.count == 1, "the first lands, the count 1 (%d, %d)" % [first.dealt, first.count])
	t.check(slow.count_before == 0 and is_zero_approx(slow.counter_before), "%d frames on, past COMBO_RESET_TIME, the count has started again and the counter faded with it (%d, alpha %.2f)" % [SLOW_FRAMES, slow.count_before, slow.counter_before])
	t.check(slow.dealt == 1 and not slow.charged and slow.count == 1 and slow.counter == "1 HIT", "the slow punch lands as a first: 1 HIT (%d dealt, count %d, '%s')" % [slow.dealt, slow.count, slow.counter])
	await settle(t)


# Two punches, then a new opening inside COMBO_RESET_TIME with the count still 2: the first punch to land in it is
# the POW.
static func carried(t, key: String) -> void:
	t.log_p("-- carried: two punches, a new opening, the count still 2, and a press mashed mid-swing")
	var finisher: Node = t.player.get_node("Finisher")
	var combo: Node = t.player.combo
	await open(t, key)
	var landed := []
	var on_landed := func(_target, _dealt, _charged): landed.append(combo.clock)
	combo.punch_landed.connect(on_landed)
	await punch(t, "fresh")
	await punch(t, "fresh")
	await open(t, key, true)
	var before: int = combo.count
	var dazeable: bool = t.boss.can_be_dazed()
	var pow: Dictionary = await punch(t, "mash")
	combo.punch_landed.disconnect(on_landed)
	var gap: float = landed[-1] - landed[-2] if landed.size() >= 3 else -1.0
	var mashed := false
	if dazeable:
		mashed = await t.wait_until(func(): return finisher.phase == t.FINISHER_DAZED and finisher.prompt_visible, 120)
	t.log_p("count %d carried in, %s; the punch dealt %d, charged %s, counter '%s', count after %d, %.3f s after the last; the finisher %s" % [before,
		"he can be dazed" if dazeable else "he can't be dazed", pow.dealt, pow.charged, pow.counter, pow.count, gap, "mashing" if mashed else ("running" if finisher.is_active() else "off")])
	t.check(before == 2 and gap > 0.0 and gap < combo.COMBO_RESET_TIME, "the count carried in is 2, the POW landing %.3f s after the last punch (%d)" % [gap, before])
	t.check(pow.charged and pow.dealt == t.player.combo.charged_damage and pow.counter == "3 POW!", "the opening's first punch is the POW: charged, %d, 3 POW! (%s, %d, '%s')" % [t.player.combo.charged_damage, pow.charged, pow.dealt, pow.counter])
	t.check(pow.count == 0, "and the count starts again (%d)" % pow.count)
	if dazeable:
		t.check(mashed, "he could be dazed, and the finisher's mash opens")
	else:
		t.check(not finisher.is_active(), "he couldn't be dazed, and no finisher starts")
	await settle(t)


# A boss who screams at a miss after a punch short of the POW (SCREAMS): one punch, then a whiff, and the count
# and the opening go with the scream.
static func screamed(t, key: String) -> void:
	t.log_p("-- screamed: one punch, then a whiff")
	await open(t, key)
	var spot: Vector2 = t.player.global_position
	var first: Dictionary = await punch(t, "fresh")
	await t.settle_player(whiff_spot(t, spot))
	await t.wait(3)
	var whiff: Dictionary = await punch(t, "fresh")
	await t.wait(2)
	t.check(first.dealt == 1 and whiff.dealt == 0 and t.player.combo.count == 0 and not t.sm.is_recovering(),
		"the first lands, and after the whiff the count and the opening are gone (%d, %d, count %d, recovering %s)" % [first.dealt, whiff.dealt, t.player.combo.count, t.sm.is_recovering()])
	await settle(t)


# From a fresh count, with no daze to give, the opening's allowance punch for punch, then one more.
static func spent(t, key: String, refused: Array) -> void:
	t.log_p("-- spent: punches until the opening's allowance is spent, then one more")
	refused.clear()
	await open(t, key)
	# After the window's Enter, which clears it: the POW deals its damage and the opening runs on.
	t.boss.daze_used = true
	var hits: int = cap(t)
	var allowance: int = PunchAllowance.clean_chain(hits)
	t.log_p("the opening's cap is %d punches, so it takes %d" % [hits, allowance])
	var runs := []
	for i in hits:
		runs.append(await punch(t, "fresh"))
	var dealt: Array = runs.map(func(r): return r.dealt)
	var chain: Array = range(hits).map(func(i): return PunchAllowance.clean_chain(i + 1) - PunchAllowance.clean_chain(i))
	var took: int = dealt.reduce(func(a, b): return a + b, 0)
	t.log_p("punches %s against the chain's %s, charged %s, %d in all, refused %d" % [dealt, chain, runs.map(func(r): return r.charged), took, refused.size()])
	t.check(dealt == chain and runs.all(func(r): return r.charged == (r.dealt == PunchAllowance.CHARGED_DAMAGE)), "the chain lands punch for punch, the POWs where it has them (%s)" % [dealt])
	t.check(took == allowance and refused.is_empty(), "exactly the allowance, %d, and nothing refused on the way" % allowance)
	var r: Dictionary = await punch(t, "fresh")
	t.check(r.dealt == 0 and refused.size() == 1, "the punch after the allowance is refused (%d dealt, %d refusals)" % [r.dealt, refused.size()])
	t.check(r.count == r.count_before, "and the count kept through it (%d, %d)" % [r.count_before, r.count])
	check_deflect(t, r)
	await settle(t)


# A punch landing on another target starts the count again, and so does the next one back on him.
static func switch(t, key: String) -> void:
	t.log_p("-- switch: a punch on another target, and back")
	await open(t, key)
	var spot: Vector2 = t.player.global_position
	var centre: Vector2 = t.boss.get_finisher_hurtbox().get_node("CollisionShape2D").global_position
	var floor: Rect2 = t.player.ring_origins
	var stand_in := StandIn.new(STAND_IN_SIZE)
	stand_in.name = "ComboStandIn"
	t.current_scene.add_child(stand_in)
	stand_in.global_position = centre + Vector2(STAND_IN_OFFSET if centre.x < floor.get_center().x else -STAND_IN_OFFSET, 0.0)
	stand_in.hurtbox.add_to_group(t.player.BOSS_TARGET_GROUP)
	var on_him: Dictionary = await punch(t, "fresh")
	t.place_under(stand_in.hurtbox)
	await t.wait(6)
	var first: Dictionary = await punch(t, "fresh")
	var second: Dictionary = await punch(t, "fresh")
	await t.settle_player(spot)
	await t.wait(6)
	var back: Dictionary = await punch(t, "fresh")
	stand_in.queue_free()
	t.log_p("on him %s, on the stand-in %s (asked %s), back on him %s" % [[on_him.dealt, on_him.count], [[first.dealt, first.count], [second.dealt, second.count]], stand_in.asked,
		[back.dealt, back.count, back.charged]])
	t.check(on_him.dealt == 1 and on_him.count == 1, "his punch lands, the count 1")
	t.check(first.count == 1 and not first.charged and stand_in.asked.slice(0, 1) == [1], "the stand-in's first starts it again: 1, not 2 (%d)" % first.count)
	t.check(second.count == 2 and not second.charged and stand_in.asked == [1, 1], "its second makes 2 (%d, asked %s)" % [second.count, stand_in.asked])
	t.check(back.dealt == 1 and back.count == 1 and not back.charged, "and back on him it starts again: 1, not the POW (%d, charged %s)" % [back.count, back.charged])
	await settle(t)


# The opening under test: his state entered anew, which zeroes his count of punches landed; his own timers stopped
# so it stays open; his hurtbox on, since some windows open a beat into their state (Greyson's Pose turns to the
# crowd first); his Break gauge held; the player under his hurtbox. The combo's count starts again unless
# `keep_count`.
static func open(t, key: String, keep_count := false) -> void:
	t.boss.boss_health = t.boss.get_max_health()
	if key == "eric":
		t.sm.parry_stagger(60.0, t.boss.global_position)
	else:
		t.sm.on_child_transition(t.sm.current_state, t.PUNISH_WINDOWS[key][1])
	await t.wait(5)
	for timer in t.boss.find_children("*", "Timer", true, false):
		timer.stop()
	var hurtbox: Area2D = t.boss.get_finisher_hurtbox()
	t.check(await t.wait_until(func(): return hurtbox.monitorable, 120), "his window is open, his hurtbox on")
	t.hold_gauge()
	if not keep_count:
		t.player.combo.reset()
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)


# The cap on the opening the boss is in, in punches of a clean chain.
static func cap(t) -> int:
	if "PARRY_STAGGER_HIT_CAP" in t.boss:
		return t.boss.PARRY_STAGGER_HIT_CAP
	if "window_cap" in t.boss:
		return t.boss.window_cap
	if t.boss.has_method("window_hit_cap"):
		return t.boss.window_hit_cap()
	return t.boss.MAX_HITS_PER_WINDOW


# Where a swing reaches nothing: WHIFF_STEP under the spot below his hurtbox, or beside it where that is off the
# ring's floor.
static func whiff_spot(t, spot: Vector2) -> Vector2:
	var floor: Rect2 = t.player.ring_origins
	var down := spot + Vector2(0.0, WHIFF_STEP)
	if floor.has_point(down):
		return down
	return spot + Vector2(WHIFF_STEP if spot.x < floor.get_center().x else -WHIFF_STEP, 0.0)


# One punch: "fresh" at once, "slow" SLOW_FRAMES on, "mash" with a second press MASH_AFTER frames into the swing;
# `at_extension` is called at the start of the first physics frame the arm is out. Returns what the combo says it
# dealt (off PlayerCombo.punch_landed, since a nap's regen moves his health under it), whether it was charged, the
# combo's count before and after it, the counter's alpha as the press went in and its text on the hit, and the
# deflect's pieces if it drew one.
static func punch(t, when: String, at_extension := Callable()) -> Dictionary:
	var combo: Node = t.player.combo
	if when == "slow":
		await t.wait(SLOW_FRAMES)
	var counter: Label = counter_of(t)
	var fx: Node = t.player.get_parent().get_node("FinisherFx")
	var fx_before: Array = fx.get_children()
	var seen := {"dealt": 0, "charged": false, "count_before": combo.count, "counter_before": counter.modulate.a, "counter": ""}
	var on_landed := func(_target, dealt: int, charged: bool):
		seen.dealt += dealt
		seen.charged = seen.charged or charged
		# The counter heard it first: it connected as the player loaded.
		seen.counter = counter.text
	combo.punch_landed.connect(on_landed)
	t.tap(KEY_Q)
	for i in 10:
		await t.physics_frame
		if t.player.state_machine.current_state.name == "Punching":
			break
	var sparks := []
	var swing: Node = t.player.get_node("StateMachine/Punching")
	var extended_at := -1
	var step := 0
	while t.player.state_machine.current_state.name == "Punching":
		if extended_at < 0 and swing.extended:
			extended_at = Engine.get_physics_frames()
			if at_extension.is_valid():
				at_extension.call()
		if when == "mash" and step == MASH_AFTER:
			t.tap(KEY_Q)
		step += 1
		for child in fx.get_children():
			if not fx_before.has(child) and not sparks.has(child):
				sparks.append(child)
		await t.physics_frame
	var ended_at := Engine.get_physics_frames()
	await t.wait(3)
	for child in fx.get_children():
		if not fx_before.has(child) and not sparks.has(child):
			sparks.append(child)
	combo.punch_landed.disconnect(on_landed)
	var sfx: AudioStreamPlayer = t.player.get_node("BlockSfxPlayer")
	seen.merge({"count": combo.count, "sparks": sparks, "sfx_stream": str(sfx.stream.resource_path) if sfx.stream else "", "sfx_pitch": sfx.pitch_scale,
		"extended_at": extended_at, "ended_at": ended_at})
	return seen


static func counter_of(t) -> Label:
	return t.player.get_parent().get_node("CanvasLayer/ComboCounter")


static func check_deflect(t, r: Dictionary) -> void:
	var spec: Dictionary = DefenseHypeArtLayout.deflect_spark()
	var drawn: Array = r.sparks.filter(func(s): return s is Sprite2D and s.texture != null and s.texture.resource_path == spec.get("texture", "") and is_equal_approx(s.scale.x, spec.get("scale", 0.0)))
	var sound: Dictionary = DefenseHypeArtLayout.DEFLECT_SFX
	t.check(not drawn.is_empty() or (not spec.has("texture") and not r.sparks.is_empty()), "the dull deflect's spark (%d new FX)" % r.sparks.size())
	if not drawn.is_empty():
		var contact: Vector2 = t.player.punch_fx.contact_point(t.boss).round()
		t.check(drawn[0].global_position.distance_to(contact) <= 2.0, "where the fist met him, a landed punch's star spot (%s, contact %s)" % [drawn[0].global_position, contact])
	t.check(r.sfx_stream == sound.stream and is_equal_approx(r.sfx_pitch, sound.pitch), "and its thud (%s at %.2f)" % [r.sfx_stream.get_file(), r.sfx_pitch])


# The combo counter after a landed punch: up, over the player's head (or under the feet near the top of
# the screen), centred on it, and whole on the screen.
static func check_counter(t) -> void:
	var counter: Label = counter_of(t)
	await t.wait(1)
	var head: Vector2 = ScreenView.world_to_screen(t, t.player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var rect := Rect2(counter.position, counter.size)
	var screen: Rect2 = counter.get_viewport_rect()
	t.log_p("counter '%s' at %s, head on screen %s" % [counter.text, rect, head])
	t.check(counter.visible and counter.modulate.a > 0.9 and counter.text == "1 HIT", "the counter is up: 1 HIT")
	t.check(rect.end.y <= head.y - DefenseHypeArtLayout.POPUP_GAP + 1.0 or rect.position.y >= head.y, "over the head (or under the feet, near the top)")
	t.check(absf(rect.get_center().x - head.x) <= 1.0 or rect.position.x <= DefenseHypeArtLayout.POPUP_SCREEN_MARGIN + 0.5 or rect.end.x >= screen.end.x - DefenseHypeArtLayout.POPUP_SCREEN_MARGIN - 0.5, "centred on it, unless the screen's edge holds it in")
	t.check(screen.encloses(rect) and rect.position == rect.position.round(), "whole on the screen, on whole pixels")


# The opening wound down: the finisher over, whatever answered the last punch over (Matt's scream shoves the
# player for a whiff), the player free.
static func settle(t) -> void:
	var finisher: Node = t.player.get_node("Finisher")
	await t.wait_until(func(): return not finisher.is_active(), 900)
	await t.wait(1)
	await t.wait_until(func(): return not t.player.is_action_locked, 120)
	await t.wait(20)
	t.clear_iframes()
	t.player.playerHealth = 1000
