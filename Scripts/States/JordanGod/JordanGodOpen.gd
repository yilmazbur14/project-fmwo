extends State

# Jordan's last phase opening where his finale cut away: the god hovering on his point and the player on the void's mark
# facing UP, drawn exactly as the finale left them, at the finale's own view. Then the view pulls back, easing out, to
# the fight's wider one (JordanGodLayout's VIEW_ZOOM and VIEW_FOCUS, over PULL_BACK), his fight's theme (Neo Tokyo,
# JordanGodLayout.music()) starts on the fight's first frame and his HUD fades in. The player is held (is_talking, which PlayerScript's _ready sets and
# every other fight's pre-fight lines clear) until OPEN_TIME is up; then they are theirs, and he goes to Idle.

const Layout := preload("res://Scripts/JordanGodLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")

var god: Node2D
var state_machine: Node
var clock := 0.0
var updates := 0
var pulling := false


func Enter() -> void:
	clock = 0.0
	updates = 0
	pulling = false
	god.play(&"hover")
	god.music.play()
	god.set_hud(true, Layout.HUD_FADE_IN)
	ScreenView.set_base(get_tree(), Layout.VIEW_ZOOM, Layout.VIEW_FOCUS)


# The fight comes up on a long frame (its loading), and a tween's first step would take all of it: a jump where the cut
# should be invisible. So the pull-back starts on the frame after the one it came up on.
func Update(_delta: float) -> void:
	updates += 1
	if updates == 2:
		_pull_back()


func Physics_Update(delta: float) -> void:
	clock += delta
	if clock < Layout.OPEN_TIME:
		return
	var player: CharacterBody2D = god.player()
	if player != null:
		player.is_talking = false
	state_machine.on_child_transition(self, "Idle")


func Exit() -> void:
	_pull_back()


# On the finale's own centre, which ScreenView keeps inside the fight's view: so it is a plain pull-back about the top
# edge's middle, nothing drifting on the way out.
func _pull_back() -> void:
	if pulling:
		return
	pulling = true
	ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, Layout.PULL_BACK)
