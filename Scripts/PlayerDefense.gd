extends Node

# The player's defence. One stamina bar pays for dashing and blocking, and refills after a short
# pause. Every attack reaches the player through player.receive_hit(), which asks resolve_hit() for
# the outcome: ignored, dodged by a dash, absorbed by the guard, or a hit.
# Blocking: the guard covers the sides around the auto-aimed facing (sky attacks from any facing).
# A blocked source is absorbed for blocked_rehit_interval, so a continuous attack costs stamina once
# a second.
# Parry: a guarded hit within parry_window of a fresh block press is negated for free. A press
# within parry_mash_lockout of an earlier press that didn't parry gets no parry credit, so mashing
# block can't parry; a parry re-arms the next press at once. A `parryable` attack, like Eric's grab,
# can only be answered this way: a held guard doesn't stop it.
# Parries in a row build a streak, which pays more hype, louder feedback and a longer stagger window.
# A hit, a guard break or parry_streak_timeout without a parry ends it.
# Guard break: the block that empties the bar is still absorbed, then the player is stunned and every
# hit lands; the first one ends the stun, so it isn't punished twice. Only blocks break the guard.
# Perfect dodge: either a dash-through attack touches the player during dash immunity, or another
# attack reaches the spot the dash started from, inside perfect_dodge_window, without reaching the
# player. The second case uses the DodgeGhost, a copy of the hurtbox left where the dash started.
# NEW ATTACK CODE must compare overlaps against player.hurtBox and ignore the ghost, then report a
# ghost-only overlap with player.receive_near_miss(); the ghost is monitorable on the player's layer,
# so every attack area that watches the player can see it.
# Dash recovery: a dash ends in recovery frames where the player can't move, punch or dash, so dash
# spam is slower than walking. The guard may still go up, and a parry during them ends them at once.
# Status drain: a status effect (PlayerStatus) can empty the bar over time through drain_stamina(),
# which keeps the refill off and breaks the guard of a player who holds block through it.
# Stamina keeps refilling through a finisher's freeze, since the player's branch keeps processing.

signal stamina_changed(stamina: float, max_stamina: float)
# A dash was pressed without the stamina for it.
signal stamina_refused
signal blocked(hit: RefCounted, contact_point: Vector2)
# `streak` counts this parry: 1 for the first, then up while they keep landing.
signal parried(hit: RefCounted, contact_point: Vector2, staggered: bool, streak: int)
signal parry_streak_changed(streak: int)
# Every block press, with whether it was credited toward a parry: a fight watching for a parry that
# has nothing to parry (Carter's feints) reads this.
signal block_pressed(credited: bool)
signal guard_broken
signal guard_recovered
signal perfect_dodged(hit: RefCounted)
signal hit_taken(hit: RefCounted)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")
const DashImmunity := preload("res://Scripts/DashImmunity.gd")
const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")

# Prints each resolved hit: attack id, result, then health, stamina and hype after it.
static var LOG_HITS := false

@export var max_stamina := 100.0
@export var stamina_regen_per_second := 35.0
# Seconds of game time after any spend before the bar starts refilling.
@export var stamina_regen_delay := 0.6
# The refill rate while the guard is up; 0 pauses it without draining.
@export var block_hold_regen_multiplier := 0.0
# A dash is refused below this.
@export var dash_stamina_cost := 15.0
@export var light_block_cost := 20.0
@export var heavy_block_cost := 35.0
# Either side of the facing.
@export var block_half_angle_degrees := 60.0
# A hit from this close to the hurtbox centre has no direction to face, so any facing blocks it.
@export var block_omni_radius := 20.0
# Of the walking speed while guarding; 0 roots the player.
@export var block_move_speed_ratio := 0.0
# The i-frames' cadence.
@export var blocked_rehit_interval := 1.0
# Light blocks have none.
@export var heavy_block_hit_stop := 0.03
@export var guard_break_time := 1.5
# Of max_stamina, given back when the stun ends.
@export var guard_break_refill_ratio := 0.5
@export var guard_break_ends_on_hit := true
@export var guard_break_hit_stop := 0.12
@export var guard_break_shake := 10.0
# The read: how long after a credited press a guarded hit is parried instead of blocked. 12 frames
# at 60: long enough to be a reaction rather than a guess, short enough that pressing early still
# misses. PlayerCombatFx shows the window while it is open, so a miss teaches the timing.
@export var parry_window := 0.2
@export var parry_mash_lockout := 0.5
# The dead stop on a parry, then a beat of slow motion at parry_slow_scale before normal speed.
@export var parry_hit_stop := 0.13
@export var parry_slow_time := 0.18
@export var parry_slow_scale := 0.3
# How long a parried boss that can be staggered stays open to punches.
@export var parry_stagger_time := 1.2
# Seconds without a parry before the streak lapses.
@export var parry_streak_timeout := 8.0
# Added to the stagger window per streak tier above 2, up to the cap.
@export var parry_stagger_streak_bonus := 0.2
@export var parry_stagger_streak_bonus_max := 0.4
# How long after a dash an attack reaching its starting spot still counts.
@export var perfect_dodge_window := 0.2
# A dash any sooner after the one before it can't earn a dodge, the DashImmunity rule.
@export var perfect_dodge_min_dash_gap := 0.6
@export var perfect_dodge_cooldown := 1.5
# One reward per attack instance.
@export var perfect_dodge_source_lockout := 3.0
# An attack that touched the player this recently isn't a near miss.
@export var perfect_dodge_contact_grace := 1.0
# The lockout after a dash, long enough that mashing dash covers less ground than walking. Only a
# parry cuts it short.
@export var dash_recovery_time := 0.4

# In PlayerScript's Facing order: DOWN, UP, LEFT, RIGHT.
const FACING_VECTORS := [Vector2.DOWN, Vector2.UP, Vector2.LEFT, Vector2.RIGHT]
# Source records past this many get their stale entries pruned.
const MAX_SOURCES := 32

@onready var player: CharacterBody2D = get_parent()

# Game time, so hit-stop slows every window with the fight.
var clock := 0.0
var stamina := 0.0
var last_spend_time := -INF
var guard_up := false
var is_guard_broken := false
var last_press_time := -INF
var press_credited := false
var last_press_parried := false
var parry_streak := 0
var last_parry_time := -INF
# Instance id of whatever is hitting -> {contact, absorbed_until, lockout_until}, in game time.
var sources := {}
var guard_break_timer: Timer

var ghost: Area2D
var ghost_active := false
var dash_start_time := -INF
var dash_start_position := Vector2.INF
var dash_clean := false
var dash_started_invincible := false
var dash_refundable := false
var hit_during_window := false
# Instance ids of the areas already touching the player when the dash started.
var dash_overlaps := {}
var last_perfect_dodge_time := -INF
var dash_recovery_until := -INF


func _ready() -> void:
	stamina = max_stamina
	guard_break_timer = Timer.new()
	guard_break_timer.one_shot = true
	guard_break_timer.timeout.connect(_end_guard_break)
	add_child(guard_break_timer)
	ghost = player.get_parent().get_node("DodgeGhost")
	ghost.area_entered.connect(_on_ghost_entered)


func _physics_process(delta: float) -> void:
	clock += delta
	_regen(delta)
	if parry_streak > 0 and clock - last_parry_time > parry_streak_timeout:
		end_parry_streak()
	if ghost_active and clock - dash_start_time > perfect_dodge_window:
		clear_dodge_ghost()


# The order matters: with no guard up and no dash, a hit lands exactly as it did before any of this.
func resolve_hit(hit: RefCounted) -> int:
	# At 0 health the loss is only reported at the end of the frame, and nothing may hurt them before that.
	if player.fight_over or player.playerHealth <= 0 or player.is_finishing:
		return HitInfo.Result.IGNORED
	var record := _record(hit.source)
	record.contact = clock
	if player.is_invincible and not hit.bypass_invincibility:
		return HitInfo.Result.IGNORED
	if hit.dash_through and DashImmunity.is_immune(player, AttackCatalog.DASH_IMMUNITY_TIME, AttackCatalog.DASH_IMMUNITY_COOLDOWN):
		_try_award_perfect_dodge(hit)
		return HitInfo.Result.DODGED
	if hit.grab:
		# A held guard never stops a grab; only a parry does.
		if _can_parry(hit):
			return _parry(hit, record)
		if player.is_grabbed:
			return HitInfo.Result.IGNORED
		return _take_hit(hit)
	if clock < record.absorbed_until:
		return HitInfo.Result.IGNORED
	if _can_parry(hit):
		return _parry(hit, record)
	if hit.blockable and is_guarding() and _from_guarded_side(hit):
		return _block(hit, record)
	return _take_hit(hit)


# This frame the attack touches the ghost but not the player.
func resolve_near_miss(hit: RefCounted) -> void:
	if not ghost_active:
		return
	if player.fight_over or player.is_finishing or player.is_grabbed or is_guard_broken:
		return
	if dash_overlaps.has(hit.source.get_instance_id()):
		return
	var record := _record(hit.source)
	if clock - record.contact <= perfect_dodge_contact_grace:
		return
	if hit.source is Area2D and player.hurtBox.overlaps_area(hit.source):
		return
	_try_award_perfect_dodge(hit)


func log_hit(hit: RefCounted, result: int) -> void:
	if not LOG_HITS or result == HitInfo.Result.IGNORED:
		return
	var hype := player.get_node_or_null("Hype")
	print("HIT %s -> %s | health %d stamina %.1f hype %s" % [hit.attack_id, HitInfo.Result.keys()[result], player.playerHealth, stamina, str(hype.hype) if hype else "-"])


func try_spend_dash() -> bool:
	if stamina < dash_stamina_cost:
		stamina_refused.emit()
		return false
	_spend(dash_stamina_cost)
	return true


func refund(amount: float) -> void:
	_set_stamina(minf(stamina + amount, max_stamina))


# A status effect emptying the bar (PlayerStatus). It counts as a spend, so the refill stays off
# while it lasts, and emptying the bar breaks a held guard the way a block that empties it does.
func drain_stamina(amount: float) -> void:
	if amount <= 0.0 or is_guard_broken or player.fight_over or player.is_finishing:
		return
	_spend(amount)
	if stamina <= 0.0 and is_guarding():
		_start_guard_break()


func is_regen_paused() -> bool:
	return guard_up and block_hold_regen_multiplier <= 0.0 and stamina < max_stamina


func is_guarding() -> bool:
	return guard_up and not is_guard_broken


func can_raise_guard() -> bool:
	if player.fight_over or player.is_finishing or player.is_grabbed or player.is_talking or is_guard_broken:
		return false
	return player.state_machine.current_state.name != "Punching"


func on_guard_raised() -> void:
	guard_up = true


func on_guard_lowered() -> void:
	guard_up = false


func on_block_pressed() -> void:
	press_credited = last_press_parried or clock - last_press_time >= parry_mash_lockout
	last_press_time = clock
	last_press_parried = false
	block_pressed.emit(press_credited)


# The next press counts toward a parry however recently the last one was made. A fight calls it as
# each attack it wants read becomes readable (Carter's clones), so a whiff at the last one can't
# carry over. Only that next press is excused: it still sets the mash lockout, so pressing again
# inside the same window still whiffs.
func rearm_parry() -> void:
	last_press_time = -INF


func clear_guard_break() -> void:
	_end_guard_break()


func on_fight_over() -> void:
	end_parry_streak()
	clear_guard_break()
	clear_dodge_ghost()
	clear_dash_recovery()


# Called as a dash starts, once its frames are recorded.
func on_dash_started() -> void:
	var ticks := Engine.physics_ticks_per_second
	var previous_frame: int = player.previous_dodge_physics_frame
	dash_clean = previous_frame < 0 or player.last_dodge_physics_frame - previous_frame >= roundi(perfect_dodge_min_dash_gap * ticks)
	dash_started_invincible = player.is_invincible
	dash_start_time = clock
	dash_start_position = player.global_position
	dash_refundable = true
	hit_during_window = false
	dash_overlaps.clear()
	for area in player.hurtBox.get_overlapping_areas():
		dash_overlaps[area.get_instance_id()] = true
	var shape: CollisionShape2D = player.hurtBox.get_node("CollisionShape2D")
	ghost.global_position = shape.global_position
	var ghost_shape: CollisionShape2D = ghost.get_node("CollisionShape2D")
	ghost_shape.shape.size = shape.shape.size * shape.global_scale.abs() / ghost.global_scale.abs()
	ghost_active = true
	ghost.set_deferred("monitoring", true)
	ghost.set_deferred("monitorable", true)


# Called as a dash's frames run out.
func on_dash_ended() -> void:
	dash_recovery_until = clock + dash_recovery_time


func is_dash_recovering() -> bool:
	return clock < dash_recovery_until


func clear_dash_recovery() -> void:
	dash_recovery_until = -INF


func clear_dodge_ghost() -> void:
	ghost_active = false
	ghost.set_deferred("monitoring", false)
	ghost.set_deferred("monitorable", false)


# The player's position when the dash started, or Vector2.INF when the window is over.
func dodge_ghost_position() -> Vector2:
	return dash_start_position if ghost_active else Vector2.INF


func _block(hit: RefCounted, record: Dictionary) -> int:
	record.absorbed_until = clock + blocked_rehit_interval
	_spend(heavy_block_cost if hit.weight == AttackCatalog.Weight.HEAVY else light_block_cost)
	blocked.emit(hit, _contact_point(hit))
	if stamina <= 0.0:
		_start_guard_break()
	return HitInfo.Result.BLOCKED


func _can_parry(hit: RefCounted) -> bool:
	if not hit.blockable and not hit.parryable:
		return false
	return is_guarding() and _from_guarded_side(hit) and _parry_ready()


func _parry_ready() -> bool:
	return press_credited and clock - last_press_time <= parry_window


# Whether a guarded hit right now would be parried: PlayerCombatFx shows the window with it.
func is_parry_ready() -> bool:
	return _parry_ready()


# A boss whose attack a parry can stagger implements can_parry_stagger(hit) -> bool and
# parry_stagger(duration).
func _parry(hit: RefCounted, record: Dictionary) -> int:
	record.absorbed_until = clock + blocked_rehit_interval
	last_press_parried = true
	# The reward for reading the attack: a parry cancels a dash's recovery frames.
	clear_dash_recovery()
	parry_streak += 1
	last_parry_time = clock
	parry_streak_changed.emit(parry_streak)
	var staggered: bool = hit.parry_stagger and is_instance_valid(hit.boss) and hit.boss.has_method("can_parry_stagger") and hit.boss.can_parry_stagger(hit)
	if staggered:
		# Parries resolve inside physics flushes and the boss's own physics step, where it can't switch state.
		hit.boss.parry_stagger.call_deferred(parry_stagger_time + _streak_stagger_bonus())
	parried.emit(hit, _contact_point(hit), staggered, parry_streak)
	return HitInfo.Result.PARRIED


func _streak_stagger_bonus() -> float:
	return clampf((parry_streak - 2) * parry_stagger_streak_bonus, 0.0, parry_stagger_streak_bonus_max)


func end_parry_streak() -> void:
	if parry_streak == 0:
		return
	parry_streak = 0
	parry_streak_changed.emit(0)


func _on_ghost_entered(area: Area2D) -> void:
	if area.is_in_group("enemy projectile"):
		resolve_near_miss(HitInfo.from_area(area))


# Shared by both ways to earn one: a dash-through attack touching the player during dash immunity,
# and an attack reaching the ghost.
func _try_award_perfect_dodge(hit: RefCounted) -> void:
	if not dash_clean or dash_started_invincible or hit_during_window:
		return
	if clock - last_perfect_dodge_time < perfect_dodge_cooldown:
		return
	var record := _record(hit.source)
	if clock < record.lockout_until:
		return
	record.lockout_until = clock + perfect_dodge_source_lockout
	last_perfect_dodge_time = clock
	if dash_refundable:
		dash_refundable = false
		refund(dash_stamina_cost)
	perfect_dodged.emit(hit)


func _take_hit(hit: RefCounted) -> int:
	hit_during_window = true
	end_parry_streak()
	hit_taken.emit(hit)
	if is_guard_broken and guard_break_ends_on_hit:
		_end_guard_break.call_deferred()
	return HitInfo.Result.HIT


func _start_guard_break() -> void:
	is_guard_broken = true
	clear_dash_recovery()
	end_parry_streak()
	_set_stamina(0.0)
	guard_break_timer.start(guard_break_time)
	player.combo.reset()
	player.punch_buffered = false
	# Blocks resolve inside physics flushes, where the stun's state can't switch safely.
	_enter_guard_broken_state.call_deferred()
	guard_broken.emit()


func _enter_guard_broken_state() -> void:
	if is_guard_broken:
		player.state_machine.on_child_transition(player.state_machine.current_state, "GuardBroken")


func _end_guard_break() -> void:
	if not is_guard_broken:
		return
	is_guard_broken = false
	guard_break_timer.stop()
	_set_stamina(max_stamina * guard_break_refill_ratio)
	var state_machine: Node = player.state_machine
	if state_machine.current_state.name == "GuardBroken":
		state_machine.on_child_transition(state_machine.current_state, "Idle")
	guard_recovered.emit()


func _from_guarded_side(hit: RefCounted) -> bool:
	if hit.from_above:
		return true
	var to_origin: Vector2 = hit.origin - _hurtbox_centre()
	if to_origin.length() <= block_omni_radius:
		return true
	var facing: Vector2 = FACING_VECTORS[player.facing]
	return absf(facing.angle_to(to_origin)) <= deg_to_rad(block_half_angle_degrees)


# Where the guard meets the attack: the hurtbox centre pushed toward it, or up for a sky attack.
func _contact_point(hit: RefCounted) -> Vector2:
	var centre := _hurtbox_centre()
	var toward: Vector2 = Vector2.UP if hit.from_above else hit.origin - centre
	if toward.length() <= block_omni_radius:
		toward = FACING_VECTORS[player.facing]
	return (centre + toward.normalized() * DefenseHypeArtLayout.CONTACT_PUSH).round()


func _hurtbox_centre() -> Vector2:
	return player.hurtBox.get_node("CollisionShape2D").global_position


func _record(source: Object) -> Dictionary:
	var id := source.get_instance_id()
	if not sources.has(id):
		if sources.size() >= MAX_SOURCES:
			_prune_sources()
		sources[id] = {"contact": -INF, "absorbed_until": -INF, "lockout_until": -INF}
	return sources[id]


func _prune_sources() -> void:
	for id in sources.keys():
		var record: Dictionary = sources[id]
		var spent: bool = record.absorbed_until <= clock and record.lockout_until <= clock
		if not is_instance_id_valid(id) or (spent and clock - record.contact > maxf(blocked_rehit_interval, perfect_dodge_contact_grace)):
			sources.erase(id)


func _regen(delta: float) -> void:
	if stamina >= max_stamina or is_guard_broken or clock - last_spend_time < stamina_regen_delay:
		return
	var rate := stamina_regen_per_second * (block_hold_regen_multiplier if guard_up else 1.0)
	if rate > 0.0:
		_set_stamina(minf(stamina + rate * delta, max_stamina))


func _spend(amount: float) -> void:
	last_spend_time = clock
	_set_stamina(maxf(stamina - amount, 0.0))


func _set_stamina(value: float) -> void:
	if value == stamina:
		return
	stamina = value
	stamina_changed.emit(stamina, max_stamina)
