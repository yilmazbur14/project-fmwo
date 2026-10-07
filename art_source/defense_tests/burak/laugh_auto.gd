extends RefCounted

# burak_laugh_auto: his laugh cut moves on by itself when the player leaves it alone (the user, 2026-10-04),
# so a player who stands still through the kegs can't hold the fight on it for good. --fixed-fps 60:
#   only his     his pre-fight lines, left alone, still wait for accept
#   accept       a press on a whole line still moves it on at once
#   left alone   no press at all: every line moves on BurakBossLaugh.AUTO_ADVANCE_TIME after it came up and
#                no sooner than AUTO_ADVANCE_READ after its last letter, and the cut ends into the Taunt
#   paused       a paused tree holds the line where it is
#   finished     the fight carries on and finishes a still player on their last half-heart
# The player's defeat comes last: its outro would carry on into anything after it.

const LAUGH_SCRIPT := "res://Scripts/States/BurakBoss/BurakBossLaugh.gd"
const FRAME := 1.0 / 60.0
const PAUSED_FRAMES := 400


static func run(t) -> void:
	var laugh_script: GDScript = load(LAUGH_SCRIPT)
	var auto_time: float = laugh_script.AUTO_ADVANCE_TIME
	var read_time: float = laugh_script.AUTO_ADVANCE_READ

	t.log_p("-- only his laugh: the pre-fight lines still wait")
	await t.burak_enter()
	var pre_whole: bool = await t.wait_until(func():
		var b: Node = t.live_balloon()
		return b != null and b.dialogue_line != null and b.is_waiting_for_input, 1200)
	var pre: Node = t.live_balloon()
	var pre_line = pre.dialogue_line if pre != null else null
	await t.wait(roundi((auto_time + read_time + 2.0) * 60.0))
	t.check(pre_whole and t.live_balloon() == pre and pre.dialogue_line == pre_line and pre.is_waiting_for_input, "left alone %.1f s, his first pre-fight line is still up, waiting" % (auto_time + read_time + 2.0))

	t.log_p("-- accept still moves a line on at once")
	await t.load_burak_laugh()
	await t.burak_end_volley(true)
	var laugh: Node = t.sm.states["Laugh"]
	var first_whole: bool = await t.wait_until(func():
		var b: Node = t.live_balloon()
		return b != null and b.dialogue_line != null and b.is_waiting_for_input, 600)
	var pressed: Node = t.live_balloon()
	var pressed_on = pressed.dialogue_line if pressed != null else null
	var moved := false
	for i in 60:
		t.tap(KEY_ENTER)
		await t.wait(2)
		if t.live_balloon() != pressed or pressed.dialogue_line != pressed_on:
			moved = true
			break
	t.check(first_whole and moved and laugh.auto_advances == 0, "a press on the whole first line moves it on, not the clock (moved %s, auto %d)" % [moved, laugh.auto_advances])

	t.log_p("-- left alone")
	await t.load_burak_laugh()
	await t.burak_end_volley(true)
	laugh = t.sm.states["Laugh"]
	t.check(t.sm.current_state == laugh and t.player.is_talking, "an owed laugh holds the player")
	var lines := []
	var paused_held := [false, false]
	var line = null
	for i in 3600:
		if t.sm.current_state != laugh:
			break
		var balloon: Node = t.live_balloon()
		var now: float = t.boss.fight_clock
		var shown = balloon.dialogue_line if balloon != null else null
		if shown != line:
			if not lines.is_empty():
				lines[-1].gone = now
			line = shown
			if line != null:
				lines.append({"text": line.text.left(16), "up": now, "typed": -1.0, "gone": -1.0})
		if line != null and lines[-1].typed < 0.0 and balloon.is_waiting_for_input:
			lines[-1].typed = now
		# On Danny's line, once it is whole: the tree paused for a while holds it where it is.
		if line != null and not paused_held[0] and line.text.begins_with("....") and lines[-1].typed >= 0.0:
			paused_held[0] = true
			var clock_before: float = laugh.line_clock
			t.paused = true
			await t.wait(PAUSED_FRAMES)
			paused_held[1] = t.live_balloon() == balloon and balloon.dialogue_line == line and laugh.line_clock == clock_before
			t.paused = false
		await t.physics_frame
	if not lines.is_empty() and lines[-1].gone < 0.0:
		lines[-1].gone = t.boss.fight_clock
	t.log_p("lines %s, auto advances %d" % [lines, laugh.auto_advances])
	t.check(str(t.sm.current_state.name) == "Taunt" and not t.player.is_talking, "with no press at all, the cut ends into the Taunt and the player is free (%s)" % t.sm.current_state.name)
	t.check(lines.size() == 3 and laugh.auto_advances == 3, "all three lines moved on by themselves (%d lines, %d)" % [lines.size(), laugh.auto_advances])
	var timing_ok := lines.all(func(l):
		var due: float = maxf(l.up + auto_time, l.typed + read_time)
		return l.typed >= 0.0 and l.gone >= due - FRAME - 0.001 and l.gone <= due + 3.0 * FRAME)
	t.check(timing_ok, "each %.1f s after it came up, and at least %.1f s after its last letter" % [auto_time, read_time])
	t.check(paused_held[0] and paused_held[1], "a paused tree holds the line where it is (%s)" % [paused_held])

	t.log_p("-- and the fight finishes a still player")
	t.player.playerHealth = 1
	var died: bool = await t.wait_until(func(): return t.player.fight_over or t.player.playerHealth <= 0, 3600)
	t.check(died, "standing still on their last half-heart, they are finished (%s, health %d)" % [t.sm.current_state.name, t.player.playerHealth])
