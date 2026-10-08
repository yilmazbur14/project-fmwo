extends Node

# The flow of Jordan's last phase (JordanGodScript): Open as the fight comes up where his finale left it, then Idle
# and a combination attack in turn for as long as it lasts - attack 1, attack 2, attack 1 again - and Defeated at his
# 20th uppercut. The attacks are JordanCombo states built here in code off JordanGodLayout.COMBOS, in its order; a
# path whose script isn't there yet, or won't load, is skipped, so the fight runs while they are being written.
# Defeated is terminal, and so is the player's loss: nothing late may start another attack. With the final beam on
# (JordanGodLayout.USE_FINAL_BEAM), his kill goes to FinalBeam instead, built here in code too: Defeated after it wins,
# Idle and the next attack after it fails.

const Layout := preload("res://Scripts/JordanGodLayout.gd")

@onready var god: Node2D = get_parent()

var states := {}
var current_state: State
# The attacks in turn, and which is next.
var combos: Array[State] = []
var next_combo := 0
var player_defeated := false
# The attacks entered, by name, in order: what a test of the rotation reads.
var rotation_log: Array[StringName] = []
var final_beam: State


# Once the god is built (his _ready): the scene's own states, then the attacks, then the fight opens on Open.
func start() -> void:
	for child in get_children():
		if child is State:
			_adopt(child)
	_build_combos()
	_build_final_beam()
	current_state = states["Open"]
	current_state.Enter.call_deferred()


func _adopt(state: State) -> void:
	states[state.name] = state
	if "god" in state:
		state.god = god
	if "state_machine" in state:
		state.state_machine = self


func _build_combos() -> void:
	for path in Layout.COMBOS:
		if not ResourceLoader.exists(path):
			continue
		var script = load(path)
		if not (script is GDScript) or not script.can_instantiate():
			push_warning("Jordan's last phase: %s won't load; its attack is skipped" % path)
			continue
		var combo = script.new()
		if not (combo is State):
			push_warning("Jordan's last phase: %s is not a State; its attack is skipped" % path)
			if combo is Node:
				combo.free()
			continue
		var base := path.get_file().get_basename()
		var node_name := base
		var n := 2
		while states.has(node_name):
			node_name = "%s_%d" % [base, n]
			n += 1
		combo.name = node_name
		add_child(combo)
		_adopt(combo)
		combos.append(combo)


# A guarded load, as the attacks': missing or broken, it warns and his kill plays his defeat.
func _build_final_beam() -> void:
	var path: String = Layout.FINAL_BEAM_STATE
	var script = load(path) if ResourceLoader.exists(path) else null
	if not (script is GDScript) or not script.can_instantiate():
		push_warning("Jordan's last phase: %s won't load; his kill plays his defeat" % path)
		return
	var state = script.new()
	if not (state is State):
		push_warning("Jordan's last phase: %s is not a State; his kill plays his defeat" % path)
		if state is Node:
			state.free()
		return
	state.name = "FinalBeam"
	add_child(state)
	_adopt(state)
	final_beam = state


func has_final_beam() -> bool:
	return final_beam != null


func _process(delta: float) -> void:
	if current_state:
		current_state.Update(delta)


func _physics_process(delta: float) -> void:
	if current_state:
		current_state.Physics_Update(delta)


# The state is current before its Enter() runs, so an attack that finishes inside its own Enter still goes back.
func on_child_transition(state, new_state_name) -> void:
	if state != current_state or current_state == states.get("Defeated") or player_defeated:
		return
	var new_state: State = states.get(new_state_name)
	if new_state == null:
		return
	current_state.Exit()
	current_state = new_state
	new_state.Enter()


# The next attack in turn, from Idle. False when there are none yet.
func start_next_attack() -> bool:
	if combos.is_empty():
		return false
	var combo: State = combos[next_combo % combos.size()]
	next_combo += 1
	rotation_log.append(StringName(combo.name))
	on_child_transition(current_state, combo.name)
	return true


# The attack under way, or null between attacks.
func current_combo() -> State:
	return current_state if combos.has(current_state) else null


# His 20th uppercut (JordanGodScript._on_defeated): whatever was under way is let go, and he is Defeated. Past the
# terminal guard, the one way into it.
func enter_defeated() -> void:
	var defeated_state: State = states["Defeated"]
	if current_state == defeated_state:
		return
	var was := current_state
	current_state = defeated_state
	if was:
		was.Exit()
	defeated_state.Enter()


# His kill with the final beam on (JordanGodScript._begin_final_beam): whatever was under way is let go, as for his
# defeat. Past the transition guard, the one way into it.
func enter_final_beam() -> void:
	if final_beam == null or current_state == final_beam:
		return
	var was := current_state
	current_state = final_beam
	if was:
		was.Exit()
	final_beam.Enter()


# The player lost: the attack under way lets go of them, and he hovers on in Idle, which starts nothing more.
func enter_player_defeated() -> void:
	player_defeated = true
	var idle: State = states["Idle"]
	if current_state == idle or current_state == states.get("Defeated"):
		return
	var was := current_state
	current_state = idle
	if was:
		was.Exit()
	idle.Enter()
