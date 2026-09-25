extends State

# ATTACK 1: THE POWDER KEGS, Captain Burak's lesson in punching, then in dashing. He lobs five kegs out
# across the whole ring, fast, each onto a marker that shows where it will come down marker_lead ahead of
# it. As the fifth lands he loads his pistol, one bullet a keg on the pips beside his head, while their
# fuses burn. Every keg still standing when the fifth bullet is in is armed, and he shoots them one at a
# time: each goes up over the whole ring for half a heart that nothing answers (BurakBossBlastScript). The
# answer was a punch on each keg before he is loaded (BurakBossBarrelScript). Break all five and he pulls
# the trigger on nothing - a dry click and a shrug - and his Taunt runs clean_run_bonus longer.
#
# THE BEATS, on one clock from the first marker, every dial locked off ramp_p() as it starts:
#   RETURN   home first, if he is away.
#   THROWS   keg k's marker at k c, the throw played in time with the cadence; the keg leaves his hand on
#            the throw's release frame and lands at k c + marker_lead.
#   LOAD     from the fifth landing: the fuses light and a bullet goes in every b, its pip flashing in the
#            load's last frame and showing loaded as the bullet is in.
#   VOLLEY   from the lock, when the fifth is in (D = marker_lead + 4 c + 5 b): the kegs left are armed and,
#            in landing order, each is aimed at for aim_time, shot, and goes up ball_time later; the next
#            aim starts next_after that. The chain stops the moment the player is down.
#   SETTLE   the unfired rounds fade as he lowers the gun; then the Laugh if the fight's first volley landed
#            all five, and the Taunt.
#   MISFIRE  in place of the rest, from the first step after the fifth landing with no keg left standing.
#
# THE SPREAD: five spots drawn fresh each volley off the fight's rng, anywhere in keg_area but never within
# home_clearance of HOME, never in `shade` (where a keg would stand over or in front of him), never where
# he would take the facing from a player punching it (faced_from_both_sides), never within
# player_clearance of the player's feet, and all at least the spread gap apart, wider as his health falls.
# Between them they cover the ring's left and right thirds and its top and bottom halves. He throws them in
# the order a player would take them: nearest first from the player's feet, then nearest to that.
# The first comes down within first_reach of the player, so walking or dashing they are beside it as it
# lands, and the race is the round after it: the four legs from the first keg to the fifth, walked to
# whichever side of each is nearer (round_length). The load is paced to that round. Each bullet takes the
# ramp's bullet plus a fifth of however long the round's walk runs past `tour` (less, if it falls short),
# so every layout leaves a player the same time to spare. The round is held to tour_slack either side of
# `tour`, so the pace barely moves between volleys.
#
# THE RAMP makes the dash the answer. A player's round of the kegs is mostly travel, so the ramp lengthens
# it as it shortens the clock: cadence, spread and tour go linearly from their full-health values (x) to
# their values at the cap (y), the bullet through bullet_mid halfway, and at the cap a human walking fails
# while dashing clears (burak_bots).
#
# RELEASE: the kegs fade, the ball and the pips go, and the hints come down, through release(), which
# Exit(), _exit_tree() and BurakBossStateMachine._stop_everything() call.
#
# FREEZE SAFETY: every wait is a Physics_Update accumulator or a node-bound tween.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const PlayerScript := preload("res://Scripts/PlayerScript.gd")
const Layout := preload("res://Scripts/BurakBossArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const KEG_SCENE := preload("res://Scenes/Bosses/BurakBossBarrelScene.tscn")
const BALL_SCENE := preload("res://Scenes/Bosses/BurakBossBallScene.tscn")
const BLAST_SCRIPT := preload("res://Scripts/BurakBossBlastScript.gd")

const PUNCH_HINT_KEY := &"barrels_punch"
const PUNCH_HINT := "PUNCH THE BARRELS BEFORE HE'S LOADED!"
const DASH_HINT_KEY := &"barrels_dash"
const DASH_HINT := "DASH (%s) BETWEEN BARRELS!"

# The spread's search: layouts tried before the rules give, draws for each keg in a layout, and how far the
# rules give each time no layout fits (so a volley always has its five): the gap narrows by GAP_RELAX, and
# first_reach and the tour's slack widen.
const LAYOUT_ATTEMPTS := 400
const SPOT_TRIES := 60
const GAP_RELAX := 0.9

@export var body : CharacterBody2D

#KNOBS (the ramp's pairs are x at full health, y at BurakBossStateMachine.CAP_RATIO or under)
@export var return_speed := 1000.0
@export var return_max := 0.9
@export var cadence := Vector2(0.55, 0.20)
# The least gap between any two kegs.
@export var spread := Vector2(350.0, 450.0)
# The round after the first keg, in walking px (round_length).
@export var tour := Vector2(1700.0, 1900.0)
@export var tour_slack := 150.0
# The bullet's ramp goes through bullet_mid at p 0.5, for a round of exactly `tour`. It is tuned for a human
# rather than a perfect bot (burak_bots): reacting in 0.22 s, one dash a hop clears every layout with 0.2 s
# or more to spare, a walker clears at full health, and at the cap a walker misses at least one keg.
@export var bullet := Vector2(0.71, 0.95)
@export var bullet_mid := 0.77
@export var kegs_per_attack := 5
@export var keg_hits := 1
# Floor points the kegs may come down on: inside the ropes with room to stand beside them, and low enough
# that a keg's top stays under the HUD.
@export var keg_area := Rect2(250, 380, 1420, 545)
@export var home_clearance := 200.0
# From HOME, the floor points that would stand a keg over him or in front of him: the FX artist's measured
# clearances, 171 px to his left and 114 px to his right, from above his hat to 156 px below his feet.
@export var shade := Rect2(-171, -180, 285, 336)
@export var player_clearance := 160.0
# Walking px from the player's feet to the nearest keg, at most.
@export var first_reach := 285.0
# Where a player stands to punch a keg: beside it, this far out past its hurtbox's half-width.
@export var stand_margin := 30.0
# The throw's release frame starts here at the art's own pace (windup .16 + heave .12); a faster cadence
# plays the throw faster. The keg lands marker_lead after its marker at every p, so the read never shortens.
@export var throw_release := 0.28
@export var marker_lead := 0.85
@export var arc_height := 180.0
@export var same_swing_guard := 0.2
@export var aim_time := 0.30
@export var ball_time := 0.18
@export var next_after := 0.25
@export var settle := 0.5
@export var misfire_aim := 0.4
@export var misfire_shrug := 0.5
@export var misfire_time := 1.2
@export var first_volley_mercy := true
@export var break_hype := 4.0
@export var clean_hype := 10.0
@export var clean_cheer := 2.0
@export var dash_hint_p := 0.6

@onready var state_machine = get_parent()

enum Beat { RETURN, THROWS, LOAD, VOLLEY, SETTLE, MISFIRE }
enum Shot { AIM, FLIGHT, GAP }

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
# The player is down: nothing more goes off, and the fight's end releases this.
var stopped := false
var beat := Beat.RETURN
var beat_clock := 0.0
# From the first marker.
var clock := 0.0
var first_barrels := false
var mercy := false

# The dials, locked as it starts: p, the cadence, the spread gap, the bullet paced to this volley's round,
# and the throw's length and release at that cadence.
var p := 0.0
var c := 0.0
var gap := 0.0
var b := 0.0
var throw_time := 0.0
var release_at := 0.0
# In throwing order.
var spots: Array[Vector2] = []
# His hurtbox as it stands at HOME, for faced_from_both_sides.
var home_hurtbox := Rect2()
var kegs: Array[Node2D] = []
# Where each keg left his hand.
var releases: Array[Vector2] = []
var landed := 0
var load_started := 0.0
var pips_loaded := 0
# The kegs the volley shoots, in landing order.
var armed: Array[Node2D] = []
var shot_index := 0
var shot_beat := Shot.AIM
var shot_clock := 0.0
var ball: Node2D
var misfire_step := 0

# For tests: the kegs still standing, the blasts that landed as HITs, and the fight_clock of the lock.
var kegs_left := 0
var blast_hits := 0
var locked_at := -1.0
# Also for tests, in fight_clock: each marker, each landing and the load's start; the lock's physics frame;
# each blast's result and the physics frame it went off on; and whether this one ended in the misfire.
var locked_frame := -1
var marker_times: Array[float] = []
var land_times: Array[float] = []
var load_started_at := -1.0
var volley_results: Array[int] = []
var blast_frames: Array[int] = []
var clean_run := false


func Enter() -> void:
	released = false
	stopped = false
	clock = 0.0
	first_barrels = state_machine.barrel_attacks_done == 0
	mercy = first_volley_mercy and first_barrels
	p = state_machine.ramp_p()
	c = lerpf(cadence.x, cadence.y, p)
	gap = lerpf(spread.x, spread.y, p)
	var art_throw := Layout.loop_length(Layout.anim(&"throw"))
	throw_time = minf(art_throw, c)
	release_at = throw_release * throw_time / art_throw
	var player: Node2D = state_machine.get_player()
	var feet := player.global_position + FinisherArtLayout.PLAYER_FEET
	spots = spread_spots(feet)
	b = bullet_at(p) + (round_length(spots, feet) - lerpf(tour.x, tour.y, p)) / (kegs_per_attack * player.SPEED)
	kegs.clear()
	releases.clear()
	landed = 0
	pips_loaded = 0
	armed.clear()
	shot_index = 0
	misfire_step = 0
	kegs_left = 0
	blast_hits = 0
	locked_at = -1.0
	locked_frame = -1
	marker_times.clear()
	land_times.clear()
	load_started_at = -1.0
	volley_results.clear()
	blast_frames.clear()
	clean_run = false
	body.velocity = Vector2.ZERO
	body.set_hurtbox_active(false)
	body.show_body()
	if body.global_position.distance_to(state_machine.HOME) < 1.0:
		_start_throws()
	else:
		_begin(Beat.RETURN)
		body.play_state_anim(&"run")


func Exit() -> void:
	release()


func _exit_tree() -> void:
	release()


# Idempotent: whichever way the attack ends, what is left of the kegs fades and everything else of it goes.
func release() -> void:
	if released:
		return
	released = true
	for keg in kegs:
		if is_instance_valid(keg):
			keg.fade_away()
	kegs.clear()
	armed.clear()
	if is_instance_valid(ball):
		ball.queue_free()
	ball = null
	if is_instance_valid(body):
		body.stop_sfx(&"fuse_hiss")
		body.hide_pips()
		_hide_hints()


func Physics_Update(delta: float) -> void:
	if released or stopped:
		return
	beat_clock += delta
	match beat:
		Beat.RETURN:
			_run_home(delta)
		Beat.THROWS:
			clock += delta
			_run_throws()
		Beat.LOAD:
			clock += delta
			_run_load()
		Beat.VOLLEY:
			_run_volley(delta)
		Beat.SETTLE:
			if beat_clock >= settle:
				_finish()
		Beat.MISFIRE:
			_run_misfire()


func _begin(next: Beat) -> void:
	beat = next
	beat_clock = 0.0


# The bullet time at `ramp`: bullet.x at full health, bullet_mid halfway, bullet.y at the cap, linear between.
func bullet_at(ramp: float) -> float:
	if ramp <= 0.5:
		return lerpf(bullet.x, bullet_mid, ramp * 2.0)
	return lerpf(bullet_mid, bullet.y, (ramp - 0.5) * 2.0)


#THE SPREAD

# This volley's five spots for a player whose feet are at `feet`, at the dials locked now, in throwing order.
func spread_spots(feet: Vector2) -> Array[Vector2]:
	var his_box: CollisionShape2D = body.hurtbox.get_node("CollisionShape2D")
	home_hurtbox = his_box.shape.get_rect()
	home_hurtbox.position += state_machine.HOME + his_box.position
	var at_gap := gap
	var reach := first_reach
	var slack := tour_slack
	var length := lerpf(tour.x, tour.y, p)
	while true:
		for attempt in LAYOUT_ATTEMPTS:
			var found := _draw_spots(feet, at_gap, reach)
			if found.is_empty() or not covers(found):
				continue
			var order := route(found, feet)
			if absf(round_length(order, feet) - length) <= slack:
				return order
		at_gap *= GAP_RELAX
		reach /= GAP_RELAX
		slack *= 2.0
	return []


# Five spots, the first drawn within `reach` of the feet, or none if one of them won't go in. Being within
# reach, the first is never further than the nearest of them, which is thrown first.
func _draw_spots(feet: Vector2, at_gap: float, reach: float) -> Array[Vector2]:
	var near := Rect2(feet - Vector2.ONE * reach, Vector2.ONE * reach * 2.0).intersection(keg_area)
	var found: Array[Vector2] = []
	while found.size() < kegs_per_attack:
		var box := near if found.is_empty() and near.has_area() else keg_area
		var placed := false
		for tries in SPOT_TRIES:
			var spot := Vector2(state_machine.rng.randf_range(box.position.x, box.end.x),
				state_machine.rng.randf_range(box.position.y, box.end.y)).round()
			if spot_allowed(spot, feet, found, at_gap):
				found.append(spot)
				placed = true
				break
		if not placed:
			return []
	return found


# Whether a keg may come down on `spot`, with `others` already down and `at_gap` between them.
func spot_allowed(spot: Vector2, feet: Vector2, others: Array[Vector2], at_gap: float) -> bool:
	var home: Vector2 = state_machine.HOME
	if spot.distance_to(home) < home_clearance or Rect2(shade.position + home, shade.size).has_point(spot):
		return false
	if spot.distance_to(feet) < player_clearance:
		return false
	for other in others:
		if spot.distance_to(other) < at_gap:
			return false
	return faced_from_both_sides(spot)


# A player punching the keg on `spot` from beside it, either side, is turned to it rather than to him: it is
# nearer them than his hurtbox by more than the facing's switch margin, and by stand_margin more for a player
# standing further out. Otherwise the punch goes to him, whose hurtbox is off for the attack.
func faced_from_both_sides(spot: Vector2) -> bool:
	var keg := Layout.keg_rect(Layout.KEG.hurtbox)
	keg.position += spot
	for side in [-1.0, 1.0]:
		var stand: Vector2 = spot + Vector2(side * beside(), 0.0) - FinisherArtLayout.PLAYER_FEET
		var to_keg := stand.distance_to(stand.clamp(keg.position, keg.end))
		var to_him := stand.distance_to(stand.clamp(home_hurtbox.position, home_hurtbox.end))
		if to_him - to_keg <= PlayerScript.TARGET_SWITCH_MARGIN + stand_margin:
			return false
	return true


# How far beside a keg's floor point a player stands to punch it.
func beside() -> float:
	return Layout.keg_rect(Layout.KEG.hurtbox).size.x / 2.0 + stand_margin


# The ring's left and right thirds and its top and bottom halves each have a keg.
func covers(found: Array[Vector2]) -> bool:
	var third := keg_area.size.x / 3.0
	var middle := keg_area.get_center().y
	return found.any(func(v): return v.x < keg_area.position.x + third) \
		and found.any(func(v): return v.x > keg_area.end.x - third) \
		and found.any(func(v): return v.y < middle) and found.any(func(v): return v.y > middle)


# `found` in the order a walking player takes them from `from`: the nearest first, then the nearest to that.
# Walking goes on both axes at once, so near is the larger of the two distances.
static func route(found: Array[Vector2], from: Vector2) -> Array[Vector2]:
	var left := found.duplicate()
	var out: Array[Vector2] = []
	var at := from
	while not left.is_empty():
		var next: Vector2 = left[0]
		for spot in left:
			if walk_distance(at, spot) < walk_distance(at, next):
				next = spot
		out.append(next)
		left.erase(next)
		at = next
	return out


static func walk_distance(from: Vector2, to: Vector2) -> float:
	var apart := (to - from).abs()
	return maxf(apart.x, apart.y)


# The round a player walks of `order` from `feet`, standing beside each keg on the side nearer where they
# come from: the four legs from the first keg to the fifth, in walking px.
func round_length(order: Array[Vector2], feet: Vector2) -> float:
	var out := Vector2(beside(), 0.0)
	var at := feet
	var length := 0.0
	for k in order.size():
		var stand := order[k] - out
		if walk_distance(at, order[k] + out) < walk_distance(at, stand):
			stand = order[k] + out
		if k > 0:
			length += walk_distance(at, stand)
		at = stand
	return length


#RETURN

func _run_home(delta: float) -> void:
	var home: Vector2 = state_machine.HOME
	body.face_toward(home)
	body.global_position = body.global_position.move_toward(home, return_speed * delta)
	if body.global_position == home or beat_clock >= return_max:
		body.global_position = home
		_start_throws()


#THROWS

func _start_throws() -> void:
	_begin(Beat.THROWS)
	clock = 0.0
	body.play_state_anim(&"idle")
	_run_throws()


func _run_throws() -> void:
	while kegs.size() < kegs_per_attack and clock >= kegs.size() * c:
		_throw(kegs.size())
	while releases.size() < kegs.size() and clock >= releases.size() * c + release_at:
		releases.append(body.release_point(&"throw"))
		body.play_sfx(&"throw")
	var flight := marker_lead - release_at
	for k in range(landed, releases.size()):
		kegs[k].carry(releases[k], clampf((clock - k * c - release_at) / flight, 0.0, 1.0), arc_height)
	while landed < releases.size() and clock >= landed * c + marker_lead:
		_land(landed)
		landed += 1
	if landed == kegs_per_attack:
		_start_load()


func _throw(k: int) -> void:
	var keg: Node2D = KEG_SCENE.instantiate()
	keg.boss = body
	keg.floor_layer = body.floor_layer
	keg.same_swing_guard = same_swing_guard
	keg.hits_to_break = keg_hits
	keg.broken.connect(_on_keg_broken)
	state_machine.add_hazard(keg, spots[k], body.barrel_layer)
	keg.show_marker()
	kegs.append(keg)
	marker_times.append(body.fight_clock)
	body.face_toward(spots[k])
	body.play_anim(&"throw", &"idle", throw_time)


func _land(k: int) -> void:
	kegs[k].land()
	kegs_left += 1
	land_times.append(body.fight_clock)
	if k == 0:
		# Each once a fight (show_hint).
		body.show_hint(PUNCH_HINT_KEY, PUNCH_HINT)
		if p >= dash_hint_p:
			body.show_hint(DASH_HINT_KEY, DASH_HINT % InputSettings.label_for(&"dodge"))


func _on_keg_broken(_keg: Node2D) -> void:
	kegs_left -= 1
	body.add_player_hype(break_hype)


#LOAD

func _start_load() -> void:
	_begin(Beat.LOAD)
	load_started = clock
	load_started_at = body.fight_clock
	for keg in kegs:
		if keg.is_breakable():
			keg.light_fuse()
	body.play_sfx(&"fuse_hiss")
	body.show_pips(kegs_per_attack)
	body.play_anim(&"load", &"", b)


func _run_load() -> void:
	if not _any_standing():
		_misfire()
		return
	var since := clock - load_started
	var flash: float = Layout.fx(&"pips").flash_time
	while pips_loaded < kegs_per_attack and since >= (pips_loaded + 1) * b - flash:
		body.load_pip(pips_loaded)
		body.play_sfx(&"load_click")
		pips_loaded += 1
	if since >= kegs_per_attack * b:
		_lock()


func _any_standing() -> bool:
	for keg in kegs:
		if keg.is_breakable():
			return true
	return false


# The fifth bullet is in. A punch that registered this step has already broken its keg: kegs report in
# the physics flush, before any state steps.
func _lock() -> void:
	locked_at = body.fight_clock
	locked_frame = Engine.get_physics_frames()
	for keg in kegs:
		if keg.is_breakable():
			keg.arm()
			armed.append(keg)
	_hide_hints()
	_begin(Beat.VOLLEY)
	shot_index = 0
	_aim()


#VOLLEY

func _run_volley(delta: float) -> void:
	shot_clock += delta
	match shot_beat:
		Shot.AIM:
			if shot_clock >= aim_time:
				_fire()
		Shot.FLIGHT:
			if shot_clock >= aim_time + ball_time:
				_detonate()
		Shot.GAP:
			if shot_clock >= aim_time + ball_time + next_after:
				shot_index += 1
				if shot_index < armed.size():
					_aim()
				else:
					_settle()


func _aim() -> void:
	shot_beat = Shot.AIM
	shot_clock = 0.0
	body.face_toward(armed[shot_index].global_position)
	body.play_anim(&"fire_aim")


func _fire() -> void:
	shot_beat = Shot.FLIGHT
	if _player_down():
		stopped = true
		return
	var target := _keg_centre(armed[shot_index])
	body.face_toward(target)
	body.play_anim(&"fire")
	var muzzle: Vector2 = body.muzzle_point(&"fire")
	_muzzle(muzzle, target - muzzle, false)
	body.play_sfx(&"gunshot")
	body.spend_pip()
	ball = BALL_SCENE.instantiate()
	ball.harmless = true
	ball.max_speed = INF
	ball.min_flight = ball_time
	ball.aim(muzzle, target)
	state_machine.add_hazard(ball, muzzle, body.projectile_layer)


func _detonate() -> void:
	shot_beat = Shot.GAP
	if is_instance_valid(ball):
		ball.queue_free()
	ball = null
	if _player_down():
		stopped = true
		return
	var blast: Node2D = BLAST_SCRIPT.new()
	# Never in the hazard group: its hit lands on the step it appears, and the suite's approach mode would
	# read that as an attack with no flight. It frees itself once it has played.
	body.projectile_layer.add_child(blast)
	var result: int = blast.go_off(armed[shot_index], state_machine.get_player(), body, shot_index == 0, mercy)
	volley_results.append(result)
	blast_frames.append(Engine.get_physics_frames())
	kegs_left -= 1
	if result == HitInfo.Result.HIT:
		blast_hits += 1


func _player_down() -> bool:
	var player: Node2D = state_machine.get_player()
	return player == null or player.playerHealth <= 0 or player.fight_over


func _keg_centre(keg: Node2D) -> Vector2:
	return keg.global_position + Layout.keg_rect(Layout.KEG.body).get_center()


#SETTLE

func _settle() -> void:
	_begin(Beat.SETTLE)
	body.stop_sfx(&"fuse_hiss")
	body.fade_pips()
	body.play_state_anim(&"idle")


# The Laugh is owed when the fight's first volley shot all five kegs and every one landed on a player
# who is still standing.
func _finish(bonus := 0.0) -> void:
	if first_barrels and not clean_run and blast_hits == kegs_per_attack and not _player_down() \
			and not state_machine.laugh_played:
		state_machine.laugh_owed = true
	state_machine.attack_done(self, bonus)


#MISFIRE

func _misfire() -> void:
	clean_run = true
	_begin(Beat.MISFIRE)
	misfire_step = 0
	body.stop_sfx(&"fuse_hiss")
	_hide_hints()
	body.face_toward(_spots_centre())
	body.play_anim(&"fire_aim")


func _run_misfire() -> void:
	if misfire_step == 0 and beat_clock >= misfire_aim:
		misfire_step = 1
		var muzzle: Vector2 = body.muzzle_point(&"fire_aim")
		_muzzle(muzzle, _spots_centre() - muzzle, true)
		body.play_sfx(&"misfire")
		body.show_talk(&"shrug", false)
	elif misfire_step == 1 and beat_clock >= misfire_aim + misfire_shrug:
		misfire_step = 2
		body.play_state_anim(&"idle")
		get_tree().call_group("arena_crowd", "cheer", clean_cheer)
		body.add_player_hype(clean_hype)
	elif misfire_step == 2 and beat_clock >= misfire_time:
		misfire_step = 3
		_finish(state_machine.clean_run_bonus)


func _spots_centre() -> Vector2:
	var sum := Vector2.ZERO
	for spot in spots:
		sum += spot
	return sum / spots.size()


#WHAT IS DRAWN

func _hide_hints() -> void:
	body.hide_hint(PUNCH_HINT_KEY)
	body.hide_hint(DASH_HINT_KEY)


# The pistol's flash and smoke off the muzzle, or only the smoke, at the nearest of its drawn headings.
# Flipped sideways only, never upside down: the smoke always rises.
func _muzzle(at: Vector2, heading: Vector2, smoke_only: bool) -> void:
	var spec: Dictionary = Layout.fx(&"muzzle")
	var pick: Array = Layout.art_frame(heading, spec.headings)
	var frames: Array = spec.smoke_frames if smoke_only else spec.flash_frames + spec.smoke_frames
	var first: int = pick[0] * spec.frames_per_heading
	var sprite := Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.scale = Vector2.ONE * Layout.SCALE
	sprite.flip_h = pick[1]
	sprite.frame = first + frames[0]
	state_machine.add_hazard(sprite, at, body.projectile_layer)
	var play := sprite.create_tween()
	for i in range(1, frames.size()):
		play.tween_interval(spec.frame_time)
		play.tween_callback(sprite.set_frame.bind(first + frames[i]))
	play.tween_interval(spec.frame_time)
	play.tween_callback(sprite.queue_free)
