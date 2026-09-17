extends RefCounted

# Stops a fight in place around the player. The fight scene is disabled, which stops every boss,
# Timer, AnimationPlayer, node-bound tween and hazard under it and takes their collision out of
# physics; the kept branches are set to always process, so they carry on. A Timer keeps its time
# left, so a boss's punish window resumes where it stopped. SceneTree timers and tweens aren't
# stopped. Not SceneTree.paused: that would also stop the player's physics and FightOutro's lines.

const CROWD_GROUP := "arena_crowd"

static var frozen := false
static var frozen_scene: Node
static var scene_mode := Node.PROCESS_MODE_INHERIT
# [node, its own process mode] for every kept branch.
static var kept: Array = []


# Keeps `keep` running, along with the crowd and every sound player in the scene, so the music and
# the sounds already playing don't cut out. Returns false if there was nothing to freeze.
static func freeze(tree: SceneTree, keep: Array) -> bool:
	var scene := tree.current_scene
	if frozen or scene == null:
		return false
	var candidates: Array = keep + tree.get_nodes_in_group(CROWD_GROUP) + scene.find_children("*", "AudioStreamPlayer", true, false)
	for node in candidates:
		if kept.any(func(pair: Array) -> bool: return pair[0] == node):
			continue
		if candidates.any(func(other: Node) -> bool: return other.is_ancestor_of(node)):
			continue
		kept.append([node, node.process_mode])
	# Kept branches first: a mode change only passes down to children that inherit theirs, so the
	# disable never reaches them and the player never leaves the physics world.
	for pair in kept:
		pair[0].process_mode = Node.PROCESS_MODE_ALWAYS
	frozen_scene = scene
	scene_mode = scene.process_mode
	scene.process_mode = Node.PROCESS_MODE_DISABLED
	frozen = true
	return true


# Safe to call when nothing is frozen.
static func unfreeze(_tree: SceneTree) -> void:
	if not frozen:
		return
	# The scene first, for the same reason the kept branches went first.
	if is_instance_valid(frozen_scene):
		frozen_scene.process_mode = scene_mode
	for pair in kept:
		if is_instance_valid(pair[0]):
			pair[0].process_mode = pair[1]
	kept.clear()
	frozen_scene = null
	frozen = false


static func is_frozen() -> bool:
	return frozen
