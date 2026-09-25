extends "res://Scripts/DannyBossPuddleScript.gd"

# The puddle one of Danny's landings leaves where it came down (DannyBossSlams): coder B's puddle, spawned with its
# splat rather than a glob, registered like any other so the next Spit's gulp dries it, with two differences.
# Its splat plays out over `arm_grace` - the worms wriggling up - and it only arms after it, so a player who
# parried on the spot has that long to step off. And feet still on it as it arms are taken: a glob's puddle
# spares feet it came down under, but this one is laid under the player on purpose, and sparing them would let
# them parry the whole string standing still (the user's playtest, 2026-09-24).

# Set before it enters the tree.
var arm_grace := 0.40


func _ready() -> void:
	splat_spec = splat_spec.duplicate()
	splat_spec.frame_time = arm_grace / splat_spec.hframes
	super._ready()


func _arm() -> void:
	super._arm()
	spared = false
