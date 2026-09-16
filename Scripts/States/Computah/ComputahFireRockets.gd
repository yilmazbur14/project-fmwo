extends State

@export var animationPlayer : AnimationPlayer
@export var sprite : Sprite2D

func Enter():
	# Hold a "readying" pose (a previously-unused sprite frame) while
	# lobbing rockets, instead of the old copy-paste bug that played
	# the laughing animation during the attack.
	animationPlayer.stop()
	if sprite:
		sprite.frame = 19

func Exit():
	pass

func Update(_delta: float):
	pass

func Physics_Update(_delta: float):
	pass
