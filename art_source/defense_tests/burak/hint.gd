extends RefCounted

# burak_hint: his tutorial hints never hide the player (BurakBossScript.fade_hints_over_player, the playtest
# of 2026-10-04). They sit across the bottom of the ring, and the parry hint comes up with the fight's first
# shot while the player is still on the mark the entrance left them on, right under it. --fixed-fps 60:
#   under it     on their entrance mark, the parry hint is drawn over their hurtbox and goes see-through
#                (his bar's own hud_fade_alpha), from its first frame up to its last
#   clear of it  walked up the ring, it is whole again on the next frame; back under, see-through again
#   the others   the cutlass hint does the same over a player standing at the bottom of the ring
#   untouched    the show and hide fades still run on modulate, and the hint still goes when the pair ends

const BURAK_BODY := "Arena/BurakBossScene/BurakBossCharacterBody"
# Where his entrance leaves the player (BurakBossIntro's player_home).
const MARK := Vector2(959, 900)
const CLEAR := Vector2(959, 600)


static func run(t) -> void:
	await t.load_burak_attacks(["Shots"])
	var body: Node = t.boss
	var sm: Node = t.sm
	var faded: float = sm.hud_fade_alpha

	t.log_p("-- the parry hint, with the player on their entrance mark")
	await t.burak_reset(MARK)
	sm.on_child_transition(sm.current_state, "Shots")
	t.check(await t.wait_until(func(): return body.hints.has(&"parry"), 400), "the first shot puts the parry hint up")
	var label: Label = body.hints[&"parry"]
	await t.wait(1)
	t.check(label.get_global_rect().intersects(on_screen(t)), "drawn across the player's hurtbox on the screen (%s over %s)" % [label.get_global_rect(), on_screen(t)])
	t.check(is_equal_approx(label.self_modulate.a, faded), "see-through from its first frame (%.2f)" % label.self_modulate.a)
	await t.wait(20)
	t.check(is_equal_approx(label.modulate.a, 1.0) and is_equal_approx(label.self_modulate.a, faded), "its fade-in has run on modulate (%.2f), and it is still see-through over them (%.2f)" % [label.modulate.a, label.self_modulate.a])

	t.log_p("-- walked clear of it, and back")
	t.player.global_position = CLEAR
	await t.wait(2)
	t.check(not label.get_global_rect().intersects(on_screen(t)) and is_equal_approx(label.self_modulate.a, 1.0), "clear of it, whole again (%.2f)" % label.self_modulate.a)
	t.player.global_position = MARK
	await t.wait(2)
	t.check(is_equal_approx(label.self_modulate.a, faded), "back under it, see-through again (%.2f)" % label.self_modulate.a)
	t.check(await t.wait_until(func(): return not body.hints.has(&"parry"), 400), "and it still goes when the pair is over")

	t.log_p("-- the cutlass hint over a player at the bottom of the ring")
	sm.ATTACK_ORDER.assign(["Cutlass"])
	await t.burak_reset(Vector2(700, 930))
	body.hints_shown.erase(&"cutlass")
	sm.on_child_transition(sm.current_state, "Cutlass")
	t.check(await t.wait_until(func(): return body.hints.has(&"cutlass"), 400), "the swing's wind-up puts the cutlass hint up")
	var cutlass: Label = body.hints[&"cutlass"]
	await t.wait(1)
	var under: bool = cutlass.get_global_rect().intersects(on_screen(t))
	t.check(under and is_equal_approx(cutlass.self_modulate.a, faded), "over a player under it, see-through (%s, %.2f)" % [under, cutlass.self_modulate.a])
	t.player.global_position = CLEAR
	await t.wait(2)
	t.check(is_equal_approx(cutlass.self_modulate.a, 1.0), "and whole once they are clear (%.2f)" % cutlass.self_modulate.a)
	await t.wait_until(func(): return sm.current_state.name != "Cutlass", 600)


# The player's hurtbox where it is drawn on the screen, which the hints' layer is in.
static func on_screen(t) -> Rect2:
	var shape: CollisionShape2D = t.player.hurtBox.get_node("CollisionShape2D")
	return t.root.get_canvas_transform() * (shape.global_transform * shape.shape.get_rect())
