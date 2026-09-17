extends State

@export var animation_player : AnimationPlayer
@export var summon_sfx_player : AudioStreamPlayer
@export var body : CharacterBody2D

const FUNKO_FIGURE_SCENE := preload("res://Scenes/Bosses/FunkoFigureScene.tscn")
const FunkoFigure := preload("res://Scripts/FunkoFigureScript.gd")

@onready var state_machine = get_parent()

var elapsed := 0.0


func Enter() -> void:
	body.explosion_hits_this_cycle = 0
	animation_player.play("summon")
	summon_sfx_player.play()
	elapsed = 0.0


func Physics_Update(delta: float) -> void:
	elapsed += delta
	if elapsed < state_machine.SUMMON_WINDUP:
		return
	_summon()
	state_machine.on_child_transition(self, "Taunt")


# Spaced evenly around him from a random start. A spot past the ropes moves inside them.
func _summon() -> void:
	var counts: Array = state_machine.SUMMON_COUNTS
	var count: int = counts[state_machine.summons % counts.size()]
	state_machine.summons += 1
	state_machine.last_summon_time = body.fight_clock

	var player = state_machine.get_player()
	var start_angle := randf() * TAU
	for i in count:
		var ring_offset: Vector2 = Vector2.from_angle(start_angle + TAU * i / count) * state_machine.SUMMON_RING
		var figure := FUNKO_FIGURE_SCENE.instantiate()
		figure.player = player
		figure.jordan = body
		state_machine.add_hazard(figure, FunkoFigure.inside_ropes(body.global_position + ring_offset))
