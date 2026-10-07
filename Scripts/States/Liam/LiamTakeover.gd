extends State

# Liam's takeover (plan section 2): beast Bixby is beaten and has coughed Liam up, and Liam takes the fight over.
# LiamTakeover.dialogue carries his lines and calls the beats between them, waiting on each; its natural end hands over
# to the fight (finish_cut, then begin_fight).
#
# The KO first: the finisher that beat Bixby plays out, and a juggle kill's crash and defeat, then a beat with the crowd
# cheering. Then the cut: a BossEntrance for the hold on the player where they stand and the skip hint, with
# GreysonTakeover's skip - every wait is a node-bound tween in `waits`, so a pause holds the cut where it is, and a held
# skip closes the balloon and runs the waits out. It never has a finish_entrance(): the defence suite finds a fight's
# entrance by that method.
#
# THE BEATS: the swap onto his own sprite and a sprite of the dog on the frame the beast's defeat left them, him getting
# up and wiping off the slime while the dog hops out of the ring (liam_gets_up); his anime laugh (anime_laugh); the
# staff tugged out of his mouth and planted (staff_from_mouth); the staff slammed and the pillar erupting under him
# (earth_pillar); the ride to the top of the ring as his bar sweeps in and his theme starts (ride_to_the_top). Between
# them his lines, each with its talk gesture while it types (the `liam` tag), and his shut pose after.
#
# EVERY WAY OUT LANDS ON ONE END STATE (_settle), and finish_cut() is the only way out: the lines' end, the hold, the
# test scene's start_active, and the fight ending over the top of it (LiamStateMachine._end_fight). Liam on his parked
# pillar at PERCH, STAND_HEIGHT up, on perch_idle facing down the screen; the pillar solid, shielded and the only boss
# target; his HUD full at pillar_hud_fade_alpha and Bixby's gone; the beast hidden and the dog gone; the player free
# where they stood, put just below the pillar's footprint if they are in it; his theme started once; the view level and
# the crowd at rest; no balloon; nothing of the takeover's own left and nothing in his hazard group. A retry plays it
# all again.

const BossEntrance := preload("res://Scripts/BossEntrance.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const PLAYER_PATH := "Arena/MainPlayer/CharacterBody2D"
# The name his lines go under.
const SPEAKER := "Liam"
# His talk gestures, by his lines' `liam` tags. The laugh is its own loop, with no shut pose.
const GESTURES := {"thanks": &"talk_thanks", "explain": &"talk_explain", "elements": &"talk_elements",
	"smug": &"talk_smug", "staff": &"talk_staff", "laugh": &"laugh"}

#THE KO
const KO_BEAT := 0.8

#THE BEATS (seconds)
const GET_UP_TIME := 0.9
# He and the dog sit as the beast's frame 9 left them for this long before he gets up and the dog hops, so the swap
# onto their own sprites is seen.
const SWAP_HOLD := 0.15
const LAUGH_TIME := 1.6
const STAFF_TIME := 1.6
# The staff comes free on the pull's fourth frame: the two tugs thump before it.
const TUG_TIMES := [0.3, 0.6]
const PILLAR_TIME := 1.0
# slam_rise's impact: raise and overhead first. The pillar erupts from there, over the rest of the beat.
const SLAM_IMPACT := 0.25
const SLAM_SHAKE := 10.0
const SLAM_SHAKE_STEPS := 6
const SLAM_SHAKE_STEP_TIME := 0.03
# The slam at the top of the ride lands this far into its pose, and the row rises from it.
const ROW_SLAM_IMPACT := 0.2
const HUD_SWEEP_TIME := 0.5
const BIXBY_HUD_FADE := 0.4
# The dog, over the ropes and the ringside crowd as he hops out.
const HOP_Z := 10

var body: CharacterBody2D
var state_machine: Node

# The hold on the player and the skip hint, up from the cut to the end.
var cut: CanvasLayer
# Enter() has run, so there is a takeover to end.
var entered := false
# The takeover is over, one way or another. finish_cut() is the only thing that sets it.
var finished := false
# Waiting for the KO to play out before the cut starts.
var waiting_ko := false
var waits: Array[Tween] = []
# A beat owns his frames until the next line comes up.
var beat_running := false
var last_line: RefCounted
# The dog hopping out of the ring, from the swap until he is off the screen.
var dog: Sprite2D
# Beats seen through to their end, for a test: name -> game seconds it took.
var beat_times := {}


func Enter() -> void:
	# Deferred, so the fight may already have been ended over the top of this state (Exit).
	if finished:
		return
	entered = true
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	if body.start_active:
		finish_cut.call_deferred()
		return
	var bixby = body.bixby
	if is_instance_valid(bixby):
		body.global_position = Layout.liam_handover(bixby.air.global_position)
	body.air.visible = false
	body.set_target_active(true)
	waiting_ko = true


func Exit() -> void:
	finish_cut(false)


func Update(_delta: float) -> void:
	if finished:
		return
	_read_lines()


func Physics_Update(_delta: float) -> void:
	if waiting_ko and _ko_over():
		waiting_ko = false
		_after_ko()


#THE KO

# The finisher that beat Bixby has played out, and a juggle kill has crashed and gone into his defeat.
func _ko_over() -> bool:
	var player := _player()
	if player != null and player.finisher.is_active():
		return false
	var bixby = body.bixby
	return not (is_instance_valid(bixby) and bixby.is_juggled())


func _after_ko() -> void:
	await _beat(KO_BEAT)
	if finished:
		return
	cut = BossEntrance.new()
	cut.name = "TakeoverCut"
	add_child(cut)
	cut.skipped.connect(skip_cut)
	cut.begin(_player())
	state_machine.crowd(&"hush")
	state_machine.show_takeover_dialogue(self)


#THE BEATS THE DIALOGUE CALLS

# His sprite and the dog's swap in for the beast's defeat frame on the same frame; he gets up and wipes off the slime
# while the dog hops out of the ring and off the screen.
func liam_gets_up() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	var bixby = body.bixby
	var beast_feet: Vector2 = bixby.air.global_position if is_instance_valid(bixby) else body.global_position
	body.global_position = Layout.liam_handover(beast_feet)
	body.height = 0.0
	body.place()
	body.set_facing(false)
	body.play_anim(&"slimed_sit")
	body.air.visible = true
	_show_dog(beast_feet)
	if is_instance_valid(bixby):
		bixby.air.visible = false
		bixby.shadow.visible = false
	await _beat(SWAP_HOLD)
	if not _cut_is_live():
		return
	_hop_dog()
	body.play_anim(&"get_up", &"wipe")
	await _beat(GET_UP_TIME - SWAP_HOLD)
	if not _cut_is_live():
		return
	body.play_anim(&"talk_thanks_shut")
	beat_running = false
	beat_times[&"liam_gets_up"] = body.fight_clock - started


# Doubled over laughing at the player.
func anime_laugh() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	body.play_anim(&"laugh")
	body.play_sfx(&"laugh")
	state_machine.crowd(&"cheer", LAUGH_TIME)
	await _beat(LAUGH_TIME)
	if not _cut_is_live():
		return
	beat_running = false
	beat_times[&"anime_laugh"] = body.fight_clock - started


# He reaches into his mouth, tugs twice, pulls the staff out and plants it.
func staff_from_mouth() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	body.stop_sfx(&"laugh")
	body.play_anim(&"staff_pull")
	var tugs := create_tween()
	for i in TUG_TIMES.size():
		tugs.tween_interval(TUG_TIMES[i] - (TUG_TIMES[i - 1] if i > 0 else 0.0))
		tugs.tween_callback(body.play_sfx.bind(&"staff_pull"))
	await _beat(STAFF_TIME)
	if not _cut_is_live():
		return
	body.play_anim(&"talk_staff_shut")
	beat_running = false
	beat_times[&"staff_from_mouth"] = body.fight_clock - started


# The staff slammed down, and the pillar erupts under him and lifts him STAND_HEIGHT.
func earth_pillar() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	body.play_anim(&"slam_rise")
	await _beat(SLAM_IMPACT)
	if not _cut_is_live():
		return
	body.play_sfx(&"slam")
	ScreenView.shake(get_tree(), SLAM_SHAKE, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP_TIME)
	body.set_target_active(false)
	body.shadow.visible = false
	var rise_time := PILLAR_TIME - SLAM_IMPACT
	body.pillar.rise(body.global_position, rise_time)
	var lift := create_tween()
	lift.tween_method(_follow_pillar, 0.0, 1.0, rise_time)
	await _wait(lift)
	if not _cut_is_live():
		return
	body.stand_on_pillar()
	beat_running = false
	beat_times[&"earth_pillar"] = body.fight_clock - started


# The pillar grinds up to PERCH with him on it; Bixby's bar goes as his sweeps in full and fades out of his way, and his
# theme starts.
func ride_to_the_top() -> void:
	if not _cut_is_live():
		return
	beat_running = true
	var started: float = body.fight_clock
	var from: Vector2 = body.pillar.global_position
	var ride_time: float = state_machine.ride_time_for(from)
	body.play_anim(&"ride")
	_retire_bixby_hud(BIXBY_HUD_FADE)
	body.show_hud(HUD_SWEEP_TIME)
	body.start_music()
	var ride := create_tween()
	ride.tween_method(_step_ride.bind(from), 0.0, 1.0, ride_time)
	var sweep := create_tween()
	sweep.tween_interval(HUD_SWEEP_TIME)
	sweep.tween_callback(body.set_hud_alpha.bind(state_machine.pillar_hud_fade_alpha))
	await _wait(ride)
	if not _cut_is_live():
		return
	if sweep.is_valid() and sweep.is_running():
		await _wait(sweep)
		if not _cut_is_live():
			return
	body.pillar.park()
	# At the top he slams his staff and the row ripples up out of the floor either side of him, all inside this beat.
	body.play_anim(&"slam")
	await _beat(ROW_SLAM_IMPACT)
	if not _cut_is_live():
		return
	body.play_sfx(&"slam")
	ScreenView.shake(get_tree(), SLAM_SHAKE, SLAM_SHAKE_STEPS, SLAM_SHAKE_STEP_TIME)
	body.row.rise(state_machine.row_rise_time, state_machine.row_ripple)
	await _beat(state_machine.row_rise_time)
	if not _cut_is_live():
		return
	body.play_anim(&"perch_idle")
	body.perch()
	beat_running = false
	beat_times[&"ride_to_the_top"] = body.fight_clock - started


#HIS LINES

func _read_lines() -> void:
	# Untyped: the balloon frees itself when the lines end, and a freed object can't be held in a typed variable long
	# enough to ask is_instance_valid about it.
	var balloon = state_machine.takeover_balloon
	if not is_instance_valid(balloon) or not balloon.is_inside_tree():
		return
	var line: RefCounted = balloon.dialogue_line
	if line == null:
		return
	if line != last_line:
		last_line = line
		body.talking = false
	if beat_running or not body.air.visible or line.character != SPEAKER or not line.has_tag("liam"):
		return
	var gesture: StringName = GESTURES.get(line.get_tag_value("liam"), &"")
	if gesture == &"":
		return
	if gesture == &"laugh":
		if body.current_anim != &"laugh":
			body.play_anim(&"laugh")
		return
	body.show_talk(gesture, balloon.dialogue_label.is_typing)


#THE DOG

# Normal Bixby as the beast's frame 9 drew him, on the frame the beast's sprite goes.
func _show_dog(beast_feet: Vector2) -> void:
	_free_dog()
	dog = Sprite2D.new()
	dog.name = "HopBixby"
	var at: Vector2 = Layout.bixby_handover(beast_feet)
	var cut_out := Layout.defeat_region(Layout.DEFEAT_BIXBY_REGION, Layout.DEFEAT_BIXBY_FEET + Vector2(0, 1))
	dog.texture = load(Layout.BixbyBeastArtLayout.DEFEAT_SHEET)
	dog.region_enabled = true
	dog.region_rect = cut_out.rect
	dog.centered = false
	dog.offset = cut_out.offset
	dog.scale = Vector2.ONE * Layout.SCALE
	body.get_parent().add_child(dog)
	dog.global_position = at.round()


# Up off the mat as bixby.png and out over the nearer rope, off the screen, on a code arc.
func _hop_dog() -> void:
	if dog == null:
		return
	var from: Vector2 = dog.global_position
	var width: float = get_viewport().get_visible_rect().size.x
	var hop: Dictionary = Layout.BIXBY_HOP
	var toward := -1.0 if from.x < width / 2.0 else 1.0
	var to := Vector2(-hop.off_screen if toward < 0.0 else width + hop.off_screen, from.y)
	dog.texture = load(Layout.BIXBY_SPRITE)
	dog.region_enabled = false
	dog.centered = true
	dog.offset = Vector2(0, -32)
	dog.flip_h = toward < 0.0
	dog.z_index = HOP_Z
	var arc := create_tween()
	arc.tween_method(_step_hop.bind(from, to, hop.arc), 0.0, 1.0, hop.time)
	arc.tween_callback(_free_dog)
	waits.append(arc)
	arc.finished.connect(func() -> void: waits.erase(arc))


func _step_hop(weight: float, from: Vector2, to: Vector2, rise: float) -> void:
	if not is_instance_valid(dog):
		return
	dog.global_position = (from.lerp(to, weight) + Vector2(0, -4.0 * rise * weight * (1.0 - weight))).round()


func _free_dog() -> void:
	if is_instance_valid(dog):
		dog.queue_free()
	dog = null


#ENDING IT

# The one way the takeover ends. Idempotent. `route` is false when the fight ended under it, which then goes wherever
# the fight's end sends it rather than into the fight.
func finish_cut(route := true) -> void:
	if finished or not entered:
		return
	finished = true
	waiting_ko = false
	beat_running = false
	BossEntrance.close_balloon(state_machine.takeover_balloon)
	BossEntrance.run_out(waits)
	state_machine.end_takeover_dialogue()
	_settle()
	if is_instance_valid(cut):
		cut.end()
	cut = null
	var player := _player()
	if player != null:
		player.is_talking = false
	BossEntrance.settle_arena(get_tree())
	if route:
		state_machine.begin_fight()


# What a held ui_cancel does: whatever is left of the lines and the beats, all at once, landing where their own end
# lands.
func skip_cut() -> void:
	if finished or not entered:
		return
	finish_cut()


# The end state every way out lands on. Idempotent.
func _settle() -> void:
	_free_dog()
	body.stop_sfx(&"laugh")
	var bixby = body.bixby
	if is_instance_valid(bixby):
		bixby.air.visible = false
		bixby.shadow.visible = false
		_retire_bixby_hud(0.0)
	var pillar: Node2D = body.pillar
	pillar.rise(state_machine.PERCH, 0.0)
	pillar.park()
	pillar.set_shielded(true)
	body.row.stand_up_now()
	body.talking = false
	body.air.visible = true
	body.set_facing(false)
	body.play_anim(&"perch_idle")
	body.stand_on_pillar()
	body.show_hud(0.0)
	body.health_bar.refill_row(0, body.boss_health, 0.0)
	body.perch()
	body.set_hud_alpha(state_machine.pillar_hud_fade_alpha, 0.0)
	body.start_music()


# Bixby's bar and gauge gone over `time` (0 at once), from his side: nothing of Bixby's own is called.
func _retire_bixby_hud(time: float) -> void:
	var bixby = body.bixby
	if not is_instance_valid(bixby) or bixby.hud_layer == null or not bixby.hud_layer.visible:
		return
	var parts: Array = [bixby.health_bar, bixby.gauge_bar].filter(func(part): return is_instance_valid(part))
	if time <= 0.0 or parts.is_empty():
		bixby.hud_layer.hide()
		return
	var fade: Tween = bixby.hud_layer.create_tween().set_parallel()
	for part in parts:
		fade.tween_property(part, "modulate:a", 0.0, time)
	fade.chain().tween_callback(bixby.hud_layer.hide)


# Every beat asks this before it touches him, so one that outlived the takeover leaves the fight alone.
func _cut_is_live() -> bool:
	return not finished and is_instance_valid(body) and state_machine.current_state == self


#PIECES

# Waits `seconds` on this node's own clock. A cut-short takeover lets it run out rather than killing it, and the
# caller's own check is what bails.
func _beat(seconds: float) -> void:
	var tween := create_tween()
	tween.tween_interval(seconds)
	await _wait(tween)


func _wait(tween: Tween) -> void:
	waits.append(tween)
	await tween.finished
	waits.erase(tween)


func _follow_pillar(_weight: float) -> void:
	if not finished:
		body.stand_on_pillar()


func _step_ride(weight: float, from: Vector2) -> void:
	if finished:
		return
	body.pillar.global_position = from.lerp(state_machine.PERCH, weight).round()
	body.stand_on_pillar()


func _player() -> Node:
	var scene := get_tree().current_scene
	return scene.get_node_or_null(PLAYER_PATH) if scene else null
