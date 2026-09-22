extends RefCounted

# The input plumbing every alternating mash in the game shares: which pair of actions it runs on,
# which events it has to swallow while it runs, whether a key is still held, and the rule that decides
# whether a press counts.
# Two nodes call it - PlayerFinisher's charge mash and PlayerGrabEscape's escape mash - and they must
# agree: they run on the same keys, and those keys are also movement and the guard, so a mash that
# swallowed a different set from the other would leak presses into walking or into the block.

# In a feel_v2 fight the mash runs on keys movement and the guard share, so while it runs they are
# kept from everything else.
const V2_SWALLOWS: Array[StringName] = [&"mash_left", &"mash_right", &"move_up", &"move_down", &"move_left", &"move_right", &"block"]


# The pair a mash alternates between. A fight on the player's feel_v2 mashes on its own keys, the
# arrows or the bumpers, clear of attack and dash; every other fight mashes attack and dash.
static func actions(player: Node) -> Array[StringName]:
	if player.feel_v2:
		return [&"mash_left", &"mash_right"]
	return [&"punch", &"dodge"]


# Which of the pair this event is a fresh press of, or empty.
static func pressed_action(player: Node, event: InputEvent) -> StringName:
	for candidate in actions(player):
		if event.is_action_pressed(candidate):
			return candidate
	return &""


static func swallows(event: InputEvent) -> bool:
	return V2_SWALLOWS.any(func(swallowed: StringName) -> bool: return event.is_action(swallowed))


static func keys_held(player: Node) -> bool:
	return actions(player).any(func(action: StringName) -> bool: return Input.is_action_pressed(action))


# Whether this press counts toward the meter: the other key of the pair, and far enough after the last
# one that counted. `min_interval` is REAL seconds - both keys pressed together arrive in the same
# input flush however long the frame took, and must count once.
static func counts(action: StringName, last_action: StringName, now_usec: int, last_usec: int, min_interval: float) -> bool:
	return action != last_action and now_usec - last_usec >= roundi(min_interval * 1000000.0)
