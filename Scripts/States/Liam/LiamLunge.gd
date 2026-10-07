extends State

# Attack 4 (addendum 3 C): the steam lunge. On its own clock, phase by phase:
#   VANISH   (vanish_time) he goes to steam as his pillar sinks under him to a stump (stump_risen), still shielded: the
#            steam thickens to steam_max, the last of the ice thaws, the water drains, and he fades out over its last
#            FADE_TIME and is gone
#   WAIT     a random while in lunge_wait_range (rng, seeded by lunge_seed; -1 random)
#   TELL     his feet, unseen, lunge_distance to one side of the player and 0 or lunge_rise off their feet, inside
#            LUNGE_AREA: the red parry badge where his head will be and its sting, the player turned to face it
#   LUNGE    from lunge_lead - lunge_show he is there, lunging, homing so his staff tip meets the player's hurtbox centre
#            exactly lunge_lead after the badge, a wake behind him; there liam_lunge lands at the player's own centre:
#            PARRIED knocks him down where he is into his pillarless window (LiamStateMachine.lunge_parried), DODGED or
#            IGNORED carries him past (WHIFF: whiff_overshoot on, a puff, gone, then the next WAIT, or RETURN after
#            lunge_count lunges), and HIT is the IMPALE
#   IMPALE   (its clock from the hit) the player held up on his staff tip, sealed and posed and over the row
#            (IMPALE_Z): his call to Bixby at impale_call_at, Bixby's fire on them from sky_fire_at, burn_ticks of
#            liam_impale_burn burn_interval apart that land through i-frames, the fire stopping and the flames going to
#            embers; at water_blast_at his water blast, whose jet puts them out and washes the player down to
#            WATER_BLAST_SPOT (with blast_hangs_player they hang where the impale left them while he aims it); on
#            landing, RETURN
#   RETURN   teleported out (if he's there to be seen), the steam cleared over steam_clear_time, teleported in on his
#            stump at PERCH and the stump raised back to full under him; then the next attack
# The hold is Computah's catch: one idempotent release(), called from Exit() (through interrupt()), _exit_tree() and the
# water blast. A player left sealed can never move again, so every way out runs through it. Every beat is a
# Physics_Update clock, so a pause and a finisher's freeze hold all of it.

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Layout := preload("res://Scripts/LiamArtLayout.gd")
const LiamElementFx := preload("res://Scripts/LiamElementFx.gd")

const LUNGE_ID := &"liam_lunge"
const BURN_ID := &"liam_impale_burn"
# The player's feet off their centre.
const FEET := Vector2(0, 42)
# He fades out over the vanish's last FADE_TIME.
const FADE_TIME := 0.4
# A whiff carries him past over its first WHIFF_SLIDE and fades him out over its last WHIFF_FADE.
const WHIFF_SLIDE := 0.15
const WHIFF_FADE := 0.15
# Bixby answers the call this long before his fire comes down; the fire stops this long before the water blast, its
# tail falling onto the player over FIRE_TAIL.
const ANSWER_LEAD := 0.15
const FIRE_STOP_LEAD := 0.2
const FIRE_TAIL := 0.2
# The steam's clear bubble while the player hangs on his staff, so both of them read.
const IMPALE_BUBBLE := 340.0
const BUBBLE_TIME := 0.3
# The wake leaves his back this high over his feet.
const WAKE_HEIGHT := 60.0
# What sixty steps of 1/60 fall short of a second by: a beat due on a frame lands on that frame.
const EPSILON := 0.0001

enum Phase { VANISH, WAIT, TELL, WHIFF, IMPALE, RETURN }
enum Back { OUT, IN, RAISE }

var body: CharacterBody2D
var state_machine: Node
var running := false
var phase := Phase.VANISH
var clock := 0.0
var rng := RandomNumberGenerator.new()
var wait_for := 0.0
var lunges := 0
var appeared := false
var origin := Vector2.ZERO
var contact := Vector2.ZERO
var whiff_to := Vector2.ZERO
var back := Back.OUT
# The hold: starts spent, so a release() from a path that never held anyone does nothing.
var released := true
var old_stage_z := 0
var hold_offset := Vector2.ZERO
var hold_point := Vector2.ZERO
var ticks := 0
var called := false
var answered := false
var fire_on := false
var fire_stopped := false
var blasting := false
var jet_fired := false
var washed := false
var sky_fire: Node2D
var flames: Node2D
# For a test: the attack's own clock, every wait drawn, each badge [clock, origin], each lunge's result, each burn's
# clock on the impale's, and the clock the player landed on.
var total_clock := 0.0
var waits: Array[float] = []
var tells: Array = []
var results: Array[int] = []
var tick_times: Array[float] = []


func Enter() -> void:
	var sm: Node = state_machine
	running = true
	total_clock = 0.0
	lunges = 0
	waits.clear()
	tells.clear()
	results.clear()
	tick_times.clear()
	if sm.lunge_seed >= 0:
		rng.seed = sm.lunge_seed
	else:
		rng.randomize()
	_start(Phase.VANISH)


func Exit() -> void:
	interrupt()


func _exit_tree() -> void:
	release()


# Stopped where it is: the badge down, the player let go, him seen again. Idempotent, and nothing of his is touched
# unless it was running (stop_everything asks every state).
func interrupt() -> void:
	release()
	if not running:
		return
	running = false
	ParryTell.clear(body)
	var player: Node2D = state_machine.get_player()
	if player != null:
		player.clear_face_point()
	body.air.visible = true
	body.air.modulate.a = 1.0


# Idempotent: the player unsealed, unposed, facing freed and back at their own z, the fire on them gone, the steam's
# bubble back to its size.
func release() -> void:
	if released:
		return
	released = true
	if is_instance_valid(sky_fire):
		sky_fire.queue_free()
	sky_fire = null
	if is_instance_valid(flames):
		flames.queue_free()
	flames = null
	if not is_instance_valid(state_machine):
		return
	var player: Node2D = state_machine.get_player()
	if player != null:
		player.set_scripted_pose(false)
		player.unlock_actions()
		player.clear_face_point()
	state_machine.set_player_stage_z(old_stage_z)
	if is_instance_valid(body) and is_instance_valid(body.steam):
		body.steam.set_bubble(Layout.STEAM_BUBBLE, BUBBLE_TIME)


# A wait drawn off the attack's generator.
func next_wait() -> float:
	return rng.randf_range(state_machine.lunge_wait_range.x, state_machine.lunge_wait_range.y)


func Physics_Update(delta: float) -> void:
	if not running:
		return
	clock += delta
	total_clock += delta
	var sm: Node = state_machine
	match phase:
		Phase.VANISH:
			body.stand_on_pillar()
			var fade_from: float = sm.vanish_time - FADE_TIME
			if clock >= fade_from:
				body.air.modulate.a = clampf(1.0 - (clock - fade_from) / FADE_TIME, 0.0, 1.0)
			if clock >= sm.vanish_time:
				_hide()
				_start(Phase.WAIT)
		Phase.WAIT:
			if clock >= wait_for:
				_start(Phase.TELL)
		Phase.TELL:
			if not appeared and clock >= sm.lunge_lead - sm.lunge_show:
				_appear()
			if appeared:
				_home(delta)
			if clock >= sm.lunge_lead - EPSILON:
				_resolve()
		Phase.WHIFF:
			var slide := clampf(clock / WHIFF_SLIDE, 0.0, 1.0)
			body.global_position = contact.lerp(whiff_to, 1.0 - pow(1.0 - slide, 2.0)).round()
			body.place()
			var fade_from: float = sm.whiff_time - WHIFF_FADE
			if clock - delta < fade_from and clock >= fade_from:
				LiamElementFx.puff(body.fx_layer, body.global_position)
			if clock >= fade_from:
				body.air.modulate.a = clampf(1.0 - (clock - fade_from) / WHIFF_FADE, 0.0, 1.0)
			if clock >= sm.whiff_time:
				_hide()
				_start(Phase.RETURN if lunges >= sm.lunge_count else Phase.WAIT)
		Phase.IMPALE:
			_step_impale()
		Phase.RETURN:
			_step_return()


func _start(next: Phase) -> void:
	phase = next
	clock = 0.0
	var sm: Node = state_machine
	match next:
		Phase.VANISH:
			body.pillar.set_shielded(true)
			body.leave_perch()
			body.play_anim(&"vanish")
			body.play_sfx(&"vanish")
			LiamElementFx.puff(body.fx_layer, body.feet_position())
			body.steam.set_density(sm.steam_max, sm.vanish_time)
			if body.flood.is_iced():
				body.flood.thaw(0.3)
				sm.set_player_ice(false)
			if body.flood.coverage > 0.0:
				body.flood.drain(sm.vanish_time)
			body.pillar.set_risen_to(sm.stump_risen, sm.vanish_time)
		Phase.WAIT:
			wait_for = next_wait()
			waits.append(wait_for)
		Phase.TELL:
			_tell()
		Phase.WHIFF:
			var player: Node2D = sm.get_player()
			if player != null:
				player.clear_face_point()
			body.play_anim(&"lunge_whiff")
			var along := (contact - origin).normalized() if contact.distance_to(origin) > 0.5 else Vector2(-1.0 if body.facing_left else 1.0, 0.0)
			var area: Rect2 = sm.LUNGE_AREA
			whiff_to = (contact + along * sm.whiff_overshoot).clamp(area.position, area.end)
		Phase.IMPALE:
			_impale()
		Phase.RETURN:
			body.steam.set_density(0.0, sm.steam_clear_time)
			if body.air.visible:
				back = Back.OUT
				body.set_target_active(false)
				body.play_anim(&"teleport")
				body.play_sfx(&"teleport_out")
				LiamElementFx.puff(body.fx_layer, body.feet_position())
			else:
				_arrive()


#THE LUNGE

# Where he'll come from, and the badge over where his head will be.
func _tell() -> void:
	var sm: Node = state_machine
	appeared = false
	var player: Node2D = sm.get_player()
	var centre: Vector2 = player.global_position if player != null else sm.FRONT_SPOT
	var side := -1.0 if rng.randf() < 0.5 else 1.0
	var dy: float = [-sm.lunge_rise, 0.0, sm.lunge_rise][rng.randi_range(0, 2)]
	var area: Rect2 = sm.LUNGE_AREA
	var x: float = centre.x + side * sm.lunge_distance
	if x < area.position.x or x > area.end.x:
		x = centre.x - side * sm.lunge_distance
	origin = Vector2(x, clampf(centre.y + FEET.y + dy, area.position.y, area.end.y)).round()
	body.global_position = origin
	body.height = 0.0
	body.place()
	body.set_facing(centre.x < origin.x)
	if player != null:
		player.face_point(origin)
	var badge := origin + Vector2(0, Layout.HEAD_TOP.y - Layout.DAZE_GAP)
	ParryTell.telegraph(body, LUNGE_ID, sm.lunge_lead, func() -> Vector2: return badge)
	body.play_sfx(&"lunge_tell")
	tells.append([total_clock, origin])


func _appear() -> void:
	appeared = true
	body.air.visible = true
	body.air.modulate.a = 1.0
	body.shadow.visible = true
	body.play_anim(&"lunge")
	body.play_sfx(&"lunge")
	var toward: Vector2 = state_machine.player_hurtbox_centre()
	LiamElementFx.wake(body.fx_layer, body.global_position + Vector2(0, -WAKE_HEIGHT), toward)


# Whatever time is left covers whatever ground is left, so his staff tip lands on the player on the beat.
func _home(delta: float) -> void:
	var left: float = state_machine.lunge_lead - clock
	var target := _lunge_feet()
	var weight := 1.0 if left <= 0.0 else minf(delta / (left + delta), 1.0)
	body.global_position = body.global_position.lerp(target, weight)
	body.place()


# His feet with his lunge's last frame's staff tip on the player's hurtbox centre.
func _lunge_feet() -> Vector2:
	var frames: Array = Layout.clip(&"lunge").frames
	var tip := Layout.point(&"staff_tip", &"lunge", frames[frames.size() - 1])
	if body.facing_left:
		tip.x = -tip.x
	return state_machine.player_hurtbox_centre() - tip


func _resolve() -> void:
	var sm: Node = state_machine
	body.global_position = _lunge_feet()
	body.place()
	contact = body.global_position
	ParryTell.clear(body)
	lunges += 1
	var player: Node2D = sm.get_player()
	var result := HitInfo.Result.IGNORED
	if player != null:
		result = player.receive_hit(HitInfo.make(LUNGE_ID, body, sm.player_hurtbox_centre(), body))
	results.append(result)
	match result:
		HitInfo.Result.PARRIED:
			_parried()
		HitInfo.Result.HIT:
			_start(Phase.IMPALE)
		_:
			_start(Phase.WHIFF)


# Knocked down where he stands, off his pillar: his window (a Break owed makes it Broken).
func _parried() -> void:
	var sm: Node = state_machine
	running = false
	var player: Node2D = sm.get_player()
	if player != null:
		player.clear_face_point()
	var bounds: Rect2 = sm.stand_rect()
	body.stand_on_floor(body.global_position.clamp(bounds.position, bounds.end))
	var away := Vector2.UP
	if player != null and body.global_position.distance_to(player.global_position) > 0.5:
		away = (body.global_position - player.global_position).normalized()
	body.knock_back(away * sm.parry_recoil, 0.2)
	body.steam.set_density(0.0, sm.parry_steam_clear)
	sm.lunge_parried(self)


func _hide() -> void:
	body.air.visible = false
	body.air.modulate.a = 1.0
	body.shadow.visible = false


#THE IMPALE

func _impale() -> void:
	var sm: Node = state_machine
	released = false
	ticks = 0
	called = false
	answered = false
	fire_on = false
	fire_stopped = false
	blasting = false
	jet_fired = false
	washed = false
	var player: Node2D = sm.get_player()
	if player != null:
		player.lock_actions_sealed()
		player.set_scripted_pose(true)
		hold_offset = sm.player_hurtbox_centre() - player.global_position
	old_stage_z = sm.player_stage_z()
	sm.set_player_stage_z(sm.IMPALE_Z)
	body.play_anim(&"impale", &"impale_call")
	body.play_sfx(&"impale")
	body.steam.set_bubble(IMPALE_BUBBLE, BUBBLE_TIME)
	_hold()


func _step_impale() -> void:
	var sm: Node = state_machine
	var player: Node2D = sm.get_player()
	if not released:
		# Anything that took the player out from under the hold frees them here: a player left sealed never moves again.
		if player == null or player.fight_over or player.is_finishing:
			release()
		else:
			_hold()
	if not called and clock >= sm.impale_call_at - EPSILON:
		called = true
		body.play_sfx(&"call")
	if not answered and clock >= sm.sky_fire_at - ANSWER_LEAD - EPSILON:
		answered = true
		body.play_sfx(&"bixby_answer")
	if not fire_on and not released and clock >= sm.sky_fire_at - EPSILON:
		fire_on = true
		body.play_sfx(&"sky_fire")
		sky_fire = LiamElementFx.sky_fire(body.fx_layer, player)
		flames = LiamElementFx.flames(body.fx_layer, player)
	while not released and ticks < sm.burn_ticks and clock >= sm.sky_fire_at + ticks * sm.burn_interval - EPSILON:
		ticks += 1
		tick_times.append(clock)
		player.take_grab_damage(BURN_ID)
		if released or player.playerHealth <= 0:
			return
	if fire_on and not fire_stopped and clock >= sm.water_blast_at - FIRE_STOP_LEAD - EPSILON:
		fire_stopped = true
		if is_instance_valid(sky_fire):
			sky_fire.stop(FIRE_TAIL)
		sky_fire = null
		if is_instance_valid(flames):
			flames.to_embers()
	if not blasting and clock >= sm.water_blast_at - EPSILON:
		blasting = true
		body.play_anim(&"water_blast")
	var release_at: float = sm.water_blast_at + _release_time()
	if blasting and not jet_fired and clock >= release_at - EPSILON:
		jet_fired = true
		body.play_sfx(&"water_jet")
		if player != null:
			LiamElementFx.water_jet(body.fx_layer, body.pose_point(&"staff_tip", &"water_blast", Layout.BLAST_RELEASE_FRAME), player, sm.jet_time)
	if jet_fired and not washed and clock >= release_at + sm.jet_time - EPSILON:
		washed = true
		body.play_sfx(&"hiss")
		if is_instance_valid(flames):
			flames.extinguish()
		flames = null
		release()
		if not sm.launch_player(sm.WATER_BLAST_SPOT, &"water"):
			_start(Phase.RETURN)
		return
	if washed and not sm.is_launching():
		_start(Phase.RETURN)


# The player where his staff tip holds them (their hurtbox's centre on it), inside HOLD_AREA; through the water blast,
# with blast_hangs_player, where the impale left them.
func _hold() -> void:
	var sm: Node = state_machine
	var player: Node2D = sm.get_player()
	if player == null:
		return
	if not (blasting and sm.blast_hangs_player):
		var area: Rect2 = sm.HOLD_AREA
		hold_point = (body.pose_point(&"staff_tip") - hold_offset).clamp(area.position, area.end).round()
	player.global_position = hold_point
	player.velocity = Vector2.ZERO


# How far into the water blast the jet leaves his staff: its release frame's start, or on the stand-in the plan's.
func _release_time() -> float:
	if Layout.uses_final(&"water_blast"):
		return Layout.frame_start(&"water_blast", Layout.BLAST_RELEASE_FRAME)
	return Layout.BLAST_RELEASE_TIME


#BACK UP

func _step_return() -> void:
	var sm: Node = state_machine
	match back:
		Back.OUT:
			if clock >= sm.teleport_time:
				_arrive()
		Back.IN:
			body.stand_on_pillar()
			if clock >= sm.teleport_time:
				back = Back.RAISE
				clock = 0.0
				body.play_anim(&"ride")
				body.pillar.set_risen_to(1.0, sm.rise_time)
		Back.RAISE:
			body.stand_on_pillar()
			if clock >= sm.rise_time:
				running = false
				body.play_anim(&"perch_idle")
				body.perch()
				sm.attack_finished(self)


# On his stump at PERCH, out of the steam.
func _arrive() -> void:
	back = Back.IN
	clock = 0.0
	body.air.visible = true
	body.air.modulate.a = 1.0
	body.shadow.visible = false
	body.set_target_active(false)
	body.stand_on_pillar()
	body.set_facing(false)
	body.play_anim(&"teleport_in")
	body.play_sfx(&"teleport_in")
	LiamElementFx.puff(body.fx_layer, body.feet_position(), true)
