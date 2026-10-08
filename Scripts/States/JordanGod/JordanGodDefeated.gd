extends State

# Jordan beaten, his 20th uppercut: terminal, as every boss's defeat is. FightOutro hands him the won outro
# (JordanGodScript.take_won_outro, begin()), and this plays it out once the KO is over - the finisher that killed him
# landed and a puppet it juggled down - and the outro's own line delay has passed: every string snaps, the puppets
# crumple and dissolve, he dissolves, a beat, and the outro fades to the champion ending - or TO BE CONTINUED with it
# switched off (_leave, FightOutro.leave_to). Every wait a node-bound tween, so nothing of it outlives the scene.
#
# THE TESTS READ: beat - &"" until it plays, then &"snap", &"crumple", &"dissolve", &"god" and &"leaving"; or, after a
# final beam won the fight (JordanGodScript.beam_won), which has played all of that out already, &"beam" and &"leaving".

const Layout := preload("res://Scripts/JordanGodLayout.gd")
const ChampionEndingLayout := preload("res://Scripts/ChampionEndingLayout.gd")

var god: Node2D
var state_machine: Node
var outro: Node
var waiting_ko := false
var ko_left := 0.0
var beat := &""


func Enter() -> void:
	god.play(&"hit", &"hover")


func begin(fight_outro: Node, line_delay: float) -> void:
	if outro != null:
		return
	outro = fight_outro
	ko_left = line_delay
	waiting_ko = true


func Physics_Update(delta: float) -> void:
	if not waiting_ko or not _ko_over():
		return
	ko_left -= delta
	if ko_left <= 0.0:
		waiting_ko = false
		_play_out()


func _ko_over() -> bool:
	var player: CharacterBody2D = god.player()
	if player != null and player.finisher.is_active():
		return false
	return not god.defeat_puppets.any(func(puppet) -> bool: return is_instance_valid(puppet) and puppet.is_juggled())


func _play_out() -> void:
	if god.beam_won:
		beat = &"beam"
		# A frame on the beat, so a test watching it frame by frame sees the beam's way out taken.
		await _wait(0.0)
		_leave()
		return
	var spec: Dictionary = Layout.DEFEAT
	var strings: Node2D = god.layer(&"strings")
	var puppets: Array = god.defeat_puppets.filter(func(puppet) -> bool: return is_instance_valid(puppet))
	beat = &"snap"
	god.play(&"hit", &"hover")
	if not puppets.is_empty():
		god.play_sound(&"snap")
	for puppet in puppets:
		strings.snap(puppet)
		puppet.crumple()
	await _wait(spec.snap)
	beat = &"crumple"
	await _wait(spec.crumple)
	beat = &"dissolve"
	for puppet in puppets:
		if is_instance_valid(puppet):
			puppet.dissolve(spec.puppet_dissolve)
	if not puppets.is_empty():
		god.play_sound(&"dissolve")
		await _wait(spec.puppet_dissolve)
	for puppet in puppets:
		if is_instance_valid(puppet):
			puppet.queue_free()
	god.defeat_puppets.clear()
	beat = &"god"
	god.dissolve(spec.god_dissolve)
	await _wait(spec.god_dissolve + spec.hold)
	_leave()


# The fight's one way out once he is beaten: the outro's fade to wherever the game goes after him.
func _leave() -> void:
	beat = &"leaving"
	if is_instance_valid(outro):
		outro.leave_to(ChampionEndingLayout.after_jordan_god())


func _wait(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await tween.finished
