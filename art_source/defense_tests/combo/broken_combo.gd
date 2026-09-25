extends RefCounted

# broken_combo fight=<fight>: a broken combo in a boss's opening (the user's playtest, 2026-09-24). Each
# opening takes the damage of a clean chain of its cap's punches (PunchAllowance): 4 for the usual cap of
# 3, and a window with a `hit_cap` of its own scales the same way. --fixed-fps 60.
#   broken    one punch, one press too slow so the combo drops, then every press on the beat: the combo
#             starts again at 1, every punch lands while the opening has any of its allowance left, the
#             POW is cut down to what is left, and nothing takes more than the allowance.
#   spent     presses too slow one after another, so every punch lands for 1: exactly the allowance lands,
#             then the next punch is refused, with PlayerCombo.punch_refused, the dull deflect's spark where
#             the fist met him and its thud.
#   closed    a punch at him in his Idle, his hurtbox switched off, is refused the same way (PlayerPunching).
#   opening   his hurtbox switched off under the fist and back on the frame after the arm is out, as an
#             opening that starts right then does: the punch lands, and nothing is refused.
#   counter   after a landed punch the combo counter is up over the player's head, centred on it and whole
#             on the screen.
# Eric's one cap is his parry stagger's (EricScript.PARRY_STAGGER_HIT_CAP), so his fight runs there.

const PunchAllowance := preload("res://Scripts/PunchAllowance.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

const ERIC_BODY := "Arena/EricBossScene/CharacterBody2D"


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

	t.log_p("-- broken: one punch, one too slow, then on the beat")
	await open(t, key)
	var allowance: int = PunchAllowance.clean_chain(cap(t))
	t.log_p("the opening's cap is %d punches, so it takes %d" % [cap(t), allowance])
	var runs := []
	var finisher: Node = t.player.get_node("Finisher")
	for i in 8:
		if finisher.is_active():
			break
		runs.append(await punch(t, "fresh" if i == 0 else ("late" if i == 1 else "beat")))
		if i == 0:
			await check_counter(t)
	var dealt: Array = runs.map(func(r): return r.dealt)
	var total: int = dealt.reduce(func(a, b): return a + b, 0)
	t.log_p("punches %s, counts %s, %d in all, finisher %s, refused %d" % [dealt, runs.map(func(r): return r.count), total, finisher.is_active(), refused.size()])
	t.check(runs.size() >= 2 and runs[0].dealt == 1 and runs[1].dealt == 1 and runs[1].count == 1, "the combo starts again at 1 after the one too slow")
	var spent := 0
	var landed_while_left := true
	for r in runs:
		if spent < allowance and r.dealt <= 0:
			landed_while_left = false
		spent += r.dealt
	t.check(landed_while_left, "every punch lands while the opening has any of it left (%s)" % [dealt])
	t.check(total <= allowance, "and nothing takes more than it: %d of %d" % [total, allowance])
	if total == allowance or finisher.is_active():
		t.check(finisher.is_active() or refused.size() > 0, "it ends on the POW's daze, or on a refusal the player sees")
	await settle(t)

	t.log_p("-- spent: every punch too slow, then one more")
	refused.clear()
	await open(t, key)
	var took := 0
	var landed := 0
	for i in allowance + 1:
		var r: Dictionary = await punch(t, "fresh" if i == 0 else "late")
		took += r.dealt
		if r.dealt > 0:
			landed += 1
		if i == allowance:
			t.check(r.dealt == 0 and refused.size() == 1, "the punch after the allowance is refused (%d dealt, %d refusals)" % [r.dealt, refused.size()])
			check_deflect(t, r)
	t.check(took == allowance and landed == allowance, "exactly the allowance lands, a punch at a time (%d of %d in %d punches)" % [took, allowance, landed])
	await settle(t)

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
	var r: Dictionary = await punch(t, "fresh")
	t.check(not hurtbox.monitorable and r.dealt == 0 and refused.size() == 1, "his hurtbox off, the punch is refused (%d dealt, %d refusals)" % [r.dealt, refused.size()])
	if refused.size() == 1:
		t.check(refused[0] - r.extended_at <= t.player.combo.REPORT_FRAMES and refused[0] < r.ended_at,
			"as it meets him, with the arm still out: %d frames after it came out, %d before the swing ended" % [refused[0] - r.extended_at, r.ended_at - refused[0]])
	check_deflect(t, r)


# The opening under test, fresh: its state entered anew, which zeroes his count of punches landed; his
# own timers stopped so it stays open; his hurtbox on, since some windows open a beat into their state
# (Greyson's Pose turns to the crowd first); his Break gauge held; the player under his hurtbox.
static func open(t, key: String) -> void:
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


# One punch: "fresh" at once, "late" once the last one's combo has dropped, "beat" inside its window;
# `at_extension` is called at the start of the first physics frame the arm is out. Returns what the combo
# says it dealt (off PlayerCombo.punch_landed, since a nap's regen moves his health under it), the
# combo's count after it, and the deflect's pieces if it drew one.
static func punch(t, when: String, at_extension := Callable()) -> Dictionary:
	var combo: Node = t.player.combo
	if when == "late":
		await t.wait_until(func(): return combo.count == 0 and not combo.window_open, 120)
		await t.wait(4)
	elif when == "beat":
		await t.wait_until(func(): return combo.window_open or combo.count == 0, 120)
	var fx: Node = t.player.get_parent().get_node("FinisherFx")
	var fx_before: Array = fx.get_children()
	var landed := [0]
	var on_landed := func(_target, dealt: int, _charged: bool): landed[0] += dealt
	combo.punch_landed.connect(on_landed)
	t.tap(KEY_Q)
	for i in 10:
		await t.physics_frame
		if t.player.state_machine.current_state.name == "Punching":
			break
	var sparks := []
	var swing: Node = t.player.get_node("StateMachine/Punching")
	var extended_at := -1
	while t.player.state_machine.current_state.name == "Punching":
		if extended_at < 0 and swing.extended:
			extended_at = Engine.get_physics_frames()
			if at_extension.is_valid():
				at_extension.call()
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
	return {"dealt": landed[0], "count": combo.count, "sparks": sparks, "sfx_stream": str(sfx.stream.resource_path) if sfx.stream else "", "sfx_pitch": sfx.pitch_scale,
		"extended_at": extended_at, "ended_at": ended_at}


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
	var counter: Control = t.player.get_parent().get_node("CanvasLayer/ComboCounter")
	await t.wait(1)
	var head: Vector2 = ScreenView.world_to_screen(t, t.player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var rect := Rect2(counter.position, counter.size)
	var screen: Rect2 = counter.get_viewport_rect()
	t.log_p("counter '%s' at %s, head on screen %s" % [counter.text, rect, head])
	t.check(counter.visible and counter.modulate.a > 0.9 and counter.text == "1 HIT", "the counter is up: 1 HIT")
	t.check(rect.end.y <= head.y - DefenseHypeArtLayout.POPUP_GAP + 1.0 or rect.position.y >= head.y, "over the head (or under the feet, near the top)")
	t.check(absf(rect.get_center().x - head.x) <= 1.0 or rect.position.x <= DefenseHypeArtLayout.POPUP_SCREEN_MARGIN + 0.5 or rect.end.x >= screen.end.x - DefenseHypeArtLayout.POPUP_SCREEN_MARGIN - 0.5, "centred on it, unless the screen's edge holds it in")
	t.check(screen.encloses(rect) and rect.position == rect.position.round(), "whole on the screen, on whole pixels")


# The opening wound down: the finisher over, the boss back in his window's state, the player free.
static func settle(t) -> void:
	var finisher: Node = t.player.get_node("Finisher")
	await t.wait_until(func(): return not finisher.is_active(), 900)
	await t.wait(20)
	t.clear_iframes()
	t.player.playerHealth = 1000
