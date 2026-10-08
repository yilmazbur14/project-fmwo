extends Node2D

# One of the figures Jordan throws down from the kaiju's head (JordanBreath, JordanStomp): it arcs from his hand to
# its landing spot and pops in there as an ordinary funko (FunkoFigureScript), stamped with its throw's id so the
# Break gauge pays one parry a throw, with the kaiju fight's shorter badge lead and its whole-heart blast (ATTACK_ID).
# A hazard from the moment it leaves his hand, so a Break or the end of the fight takes it out of the air too. Its
# flight runs on physics frames, so a freeze holds it.

const FUNKO_FIGURE_SCENE := preload("res://Scenes/Bosses/FunkoFigureScene.tscn")
const FunkoFigure := preload("res://Scripts/FunkoFigureScript.gd")

# Over the fighters while it flies.
const FLIGHT_Z := 2
const ATTACK_ID := &"jordan_kaiju_funko"

# Set by the thrower before it is added.
var from := Vector2.ZERO
var to := Vector2.ZERO
var fly_time := 0.45
var apex := 160.0
var throw_id := -1
var player: CharacterBody2D
var jordan: CharacterBody2D
var state_machine: Node

var clock := 0.0
var sprite: Sprite2D
# The figure it became, for a test.
var figure: Node


func _ready() -> void:
	z_index = FLIGHT_Z
	sprite = Sprite2D.new()
	sprite.texture = FunkoFigure.FIGURE_SHEETS.pick_random()
	sprite.hframes = FunkoFigure.SHEET_FRAMES
	sprite.frame = FunkoFigure.PUNCHED_FRAMES[0]
	sprite.scale = Vector2.ONE * FunkoFigure.ART_SCALE
	add_child(sprite)
	global_position = from


func _physics_process(delta: float) -> void:
	clock += delta
	var p := clampf(clock / fly_time, 0.0, 1.0)
	global_position = (from.lerp(to, p) - Vector2(0, 4.0 * apex * p * (1.0 - p))).round()
	sprite.rotation = TAU * p * signf(to.x - from.x)
	if p < 1.0:
		return
	figure = FUNKO_FIGURE_SCENE.instantiate()
	figure.player = player
	figure.jordan = jordan
	figure.throw_id = throw_id
	figure.tell_lead = FunkoFigure.TELL_LEAD
	figure.attack_id = ATTACK_ID
	state_machine.add_hazard(figure, to)
	queue_free()
