extends Node

# The finisher. A charged combo punch that lands in a boss's punish window dazes the boss and stops
# the fight around the player. Alternating punch and dodge fills a meter while the camera closes in,
# and a full meter fires a rising uppercut that takes a chunk of the boss's health and ends the window.
# A fight can also hand the whole thing out at once with begin_auto(), for a read the player has
# already earned: the same daze, no prompt, and the uppercut fires itself.
# A boss takes part by implementing:
#     can_be_dazed() -> bool             alive, in its punish window, not dazed in it yet, and the
#                                        finisher could still deal damage past any phase floor
#     enter_daze()                       at the freeze
#     exit_daze(finisher_landed: bool)   once, whenever the daze ends
#     end_recovery(stagger_time: float) -> bool
#                                        leave the window now, idle stagger_time, then attack again;
#                                        false when that doesn't apply (dead, changing phase)
#     take_finisher(amount: int) -> int  past the hit cap, but not past a phase floor
#     get_max_health() -> int
#     get_daze_anchor() -> Vector2       where the stars circle, about 34 px above the head
#     get_finisher_hurtbox() -> Area2D   with its shape in a child named CollisionShape2D
# besides the `sprite` and get_health_ratio() every boss has.
# Against a boss that can also be juggled, in a fight on the player's feel_v2, the mash is tiered
# instead: three bars (FinisherTierMeter), then an uppercut for each bar banked, each one throwing him
# higher, until he crashes. Such a boss also implements:
#     can_be_juggled() -> bool           asked as the daze starts
#     begin_juggle()                     at the first uppercut's contact, as the fight unfreezes
#     juggle_lift(px: float)             his height over his ground line, on his sprite alone
#     juggle_pose(pose: StringName, crater := false)
#                                        &"launch" at each contact, &"crash" as he lands
#     juggle_headroom() -> float         the most he can be lifted and still be seen whole
#     take_juggle_hit(amount: int, pitch: float) -> int
#                                        take_finisher, with his hit sound at `pitch`
#     get_juggle_point() -> Vector2      his middle in the air, which the camera follows
# and his end_recovery() then comes as he crashes rather than at contact.

signal prompt_shown
signal meter_changed(meter: float, next_action: StringName)
signal charge_ended(filled: bool)
signal finished
signal tier_banked(tier: int)
signal juggle_hit(index: int, last: bool)

const FightFreeze := preload("res://Scripts/FightFreeze.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const HitStop := preload("res://Scripts/HitStop.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const FinisherTierMeter := preload("res://Scripts/FinisherTierMeter.gd")
const MashInput := preload("res://Scripts/MashInput.gd")

# JUGGLE_FALL: the juggle's last uppercut has landed and the boss is still falling. CHARGE: a mash a
# fight runs on its own account (begin_scripted_charge), with no boss and no uppercut behind it.
enum Phase { OFF, SETTLE, DAZED, CHARGING, UPPERCUT, FIZZLE, JUGGLE_FALL, CHARGE }

# Seconds are game time unless noted.
# Time for the charged punch's hit-stop, flash and shake to play out before the fight stops.
@export var daze_settle_time := 0.2
# From the freeze until the prompt shows and presses count.
@export var prompt_delay := 0.1
@export var charge_time_limit := 3.0
# At r alternating presses a second the meter fills in about 1 / (r * gain - drain) seconds: 2 s at 7
# presses a second, 2.95 s at 5.5, never below 2.3. Mashing one key only counts its first press.
@export var meter_gain_per_press := 0.107
@export var meter_drain_per_second := 0.25
# Real seconds: Q and W pressed together arrive in the same input flush however long the frame took,
# and count once.
@export var min_press_interval := 0.03
@export var zoom := 1.5
@export var zoom_in_time := 0.25
@export var zoom_out_time := 0.3
# The zoom centres on the player, pulled this far toward the daze anchor.
@export var focus_boss_weight := 0.35
# Of the boss's max health, at least 1.
@export var finisher_damage_ratio := 0.25
# The same, for an uppercut supercharged by a full hype meter (PlayerHype). Every dial on the
# supercharged contact is bigger than the normal one: that gap is the point.
@export var supercharged_damage_ratio := 0.40
@export var super_impact_hit_stop := 0.35
@export var super_impact_shake := 34.0
@export var super_impact_shake_steps := 10
# Multiplies the view at contact, snapped to, held, then eased back out. Real seconds: the punch
# plays out during the hit-stop.
@export var super_impact_zoom := 1.25
@export var super_impact_zoom_in_time := 0.03
@export var super_impact_zoom_hold := 0.12
@export var super_impact_zoom_out_time := 0.45
@export var super_impact_flash := Color(2.6, 2.2, 0.9)
@export var super_impact_cheer := 4.0
# On the player as the uppercut launches.
@export var super_launch_flash := Color(2.0, 1.6, 0.6)
# How far the uppercut shoves the boss away from the player, and how long the shove takes.
@export var uppercut_knockback := 120.0
@export var super_uppercut_knockback := 240.0
@export var uppercut_knockback_time := 0.3
# px the boss's hurtbox grows by for the reach check.
@export var uppercut_reach := 48.0
@export var impact_hit_stop := 0.15
@export var impact_shake := 16.0
@export var impact_cheer := 2.0
# Stacks on the boss's own hit flash, which tweens modulate.
@export var impact_flash := Color(2.2, 1.9, 1.3)
@export var impact_flash_time := 0.35
# A boss the finisher lands on idles this long, hopping, then attacks again: long enough for the
# player to back off and read what comes next.
@export var stagger_time := 1.2
@export var super_stagger_time := 1.8
@export var stagger_hop_texels := 10
@export var fizzle_time := 0.25
# After the finisher, punch and dodge presses are swallowed for this long, so leftover mashing can't
# throw a punch or spend the next dash's immunity.
@export var post_input_lock := 0.2
# After a feel_v2 mash, whose keys (the arrows, the bumpers) movement and the guard share: while any is
# still held, up to this long, movement reads nothing and a held guard stays down (PlayerScript), so
# the key the player was last hammering doesn't walk them off or raise their guard.
@export var mash_release_latch := 1.0

# The tiered mash (FinisherTierMeter). At about 7.0, 9.4 and 10.9 alternating presses a second each bar
# fills inside its window: presses every 8, 6 and 5 frames reach tiers 1, 2 and 3, and every 9, 7 and 6
# don't, each at least 1.3 press intervals clear of its window either way (mash_tiers). Windows 2 and 3
# are under the plan's 1.2 and 1.05 s because the drain can't take the meter back under a bar that has
# just banked, so the next bar fills a press sooner than the plan's maths had it.
@export var tier_gain := 0.20
@export var tier_drains: Array[float] = [0.75, 1.0, 1.2]
@export var tier_windows: Array[float] = [1.30, 1.06, 0.92]
@export var tier_start_grace := 1.0
@export var tier_idle_stop := 0.5
# The charge builds with m_s: the banked bars, or the meter smoothed over meter_smoothing if higher.
@export var meter_smoothing := 0.12
@export var charge_zoom := 1.40
@export var charge_zoom_per_bar := 0.12
# A px rattle, reissued every rumble_step real seconds.
@export var charge_rumble := 1.5
@export var charge_rumble_per_bar := 3.0
@export var rumble_step := 0.05
# As each bar banks: a kick over bank_kick_steps, and the crowd.
@export var bank_kicks: Array[float] = [8.0, 12.0, 16.0]
@export var bank_kick_steps := 6
@export var bank_cheers: Array[float] = [1.0, 1.5, 2.5]
# The juggle: each uppercut a share of max health, at least 1, the last one supercharge_bonus more with
# a full hype meter at the daze.
@export var juggle_shares: Array[float] = [0.15, 0.10, 0.15]
@export var supercharge_bonus := 0.10
# Into the land frame before the next uppercut launches, so they connect 0.55 s apart.
@export var relaunch_delay := 0.08
# The boss's flight, px/s up and px/s/s down: for an uppercut more follow, by uppercut, and for the last
# one, by uppercut. Each hit before the last catches him about 100 px up.
@export var juggle_gravity := 2900.0
@export var juggle_launches: Array[float] = [980.0, 800.0]
@export var juggle_last_launches: Array[float] = [900.0, 900.0, 1100.0]
@export var juggle_hit_stops: Array[float] = [0.10, 0.10, 0.35]
# From the first contact the view eases to juggle_zoom, between the player and the boss in the air, and
# follows them; after the crash it eases back out.
@export var juggle_zoom := 1.45
@export var juggle_zoom_in_time := 0.25
@export var juggle_zoom_out_time := 0.45
@export var crash_shake := 18.0
@export var special_crash_shake := 34.0
@export var crash_shake_steps := 8
# How long the boss takes to get up and attack again after he crashes, longer after the third uppercut
# or a supercharged one.
@export var juggle_recovery := 1.5
@export var long_juggle_recovery := 2.0

# What a scripted charge takes when its caller doesn't say (begin_scripted_charge).
const SCRIPTED_PRESS_GAIN := 0.12
const SCRIPTED_FLOOR_TIME := 6.0
# The prompt's FULL! flash and its fade (FinisherPromptUI.FULL_HOLD + FADE_TIME), which a scripted
# charge waits out before it ends, exactly as the uppercut a mashed finisher fires does.
const SCRIPTED_FULL_HOLD := 0.5

# Straight above or below the boss's middle, the player keeps the side they were facing.
const SIDE_DEAD_ZONE := 8.0
const IMPACT_SHAKE_STEPS := 6
const IMPACT_SHAKE_STEP_TIME := 0.03
# The stagger hop: up, down, then a small bounce, stagger_time in all.
const HOP_UP_TIME := 0.18
const HOP_DOWN_TIME := 0.22
const HOP_BOUNCE_TEXELS := 2
const HOP_BOUNCE_TIME := 0.1
# Summed frame deltas land a hair short of a step's start, which would hold a 3-frame step a frame long.
const STEP_TOLERANCE := 0.001
# The ground layer's y: one px below the top edge of the arena floor, where the fights keep their own
# floor layers, so a y-sorted fight sorts it over the mat and under every character.
const GROUND_FX_Y := 101.0

@onready var player: CharacterBody2D = get_parent()
@onready var fx_layer: Node2D = player.get_parent().get_node("FinisherFx")
@onready var super_sfx_player: AudioStreamPlayer = player.get_node("SuperUppercutSfxPlayer")

var phase := Phase.OFF
var boss: Node
var phase_time := 0.0
# From the freeze, through the prompt and the charge.
var daze_time := 0.0
var dazed := false
var prompt_visible := false
var meter := 0.0
var last_action := &""
var last_press_usec := 0
var zoomed := false
var charge_clock := 0.0
var charge_step := 0
var uppercut_step := 0
var flipped := false
var stars: Sprite2D
var stars_clock := 0.0
var input_lock_left := 0.0
# Set by begin_auto(): the charge is already made, so the dazed beat runs on its own clock and no
# press is ever counted.
var auto := false
var auto_hold := 0.0
# Decided when the daze starts: nothing can hit the player during the finisher, so the hype it needs
# can't drain in between. PlayerFinishing reads it for the recoloured sheet.
var supercharged := false
# Whether this finisher asked for a mash: only then is a key held at its end left over from mashing.
var mashed := false
var latch_left := 0.0
# The tiered mash and the juggle it pays out.
var tiered := false
var tier_meter: RefCounted
var smoothed_meter := 0.0
# m_s, what the charge builds with.
var charge_level := 0.0
var charge_time := 0.0
var charge_zoom_from := 1.0
var charge_focus_from := Vector2.ZERO
var rumble_left := 0.0
var kick_left := 0.0
var juggle_tiers := 0
var juggle_index := 0
# Whether another uppercut can follow: a whiff or a kill stops the juggle.
var juggle_goes_on := false
var juggling := false
# The third uppercut, Knight Breaker.
var special := false
# Whether the last contact was Knight Breaker's or a supercharged one.
var last_hit_big := false
# The boss's height over his ground line in px, before lift_scale, and the arc he's on.
var lift := 0.0
var lift_scale := 1.0
var arc_from := 0.0
var arc_speed := 0.0
var arc_time := 0.0
var airborne := false
var camera_time := 0.0
var camera_zoom_from := 1.0
var camera_focus_from := Vector2.ZERO
# Knight Breaker's zoom punch, on top of the juggle's zoom.
var punch_zoom := 1.0
var punch_tween: Tween
var charge_loop: AudioStreamPlayer
var bar_sounds: Array[AudioStreamPlayer] = []
var knight_breaker_sound: AudioStreamPlayer
# The scripted charge: its caller's dials, and the FULL! flash it ends on.
var scripted_gain := SCRIPTED_PRESS_GAIN
var scripted_floor := SCRIPTED_FLOOR_TIME
var scripted_filled := false
var scripted_hold_left := 0.0
# Which word FinisherPromptUI shows. &"mash" everywhere else; the caller sets it.
var prompt_key := &"mash"


func _ready() -> void:
	player.get_node("Combo").charged_hit_landed.connect(_on_charged_hit_landed)
	# Loaded up front: the local sound is an MP3, and the first supercharged uppercut of a fight must
	# not wait on a decoder to warm up.
	var impact := FinisherArtLayout.super_impact_sfx()
	super_sfx_player.stream = load(impact.stream)
	super_sfx_player.pitch_scale = impact.pitch
	super_sfx_player.volume_db = impact.volume_db
	charge_loop = _add_sound(FinisherArtLayout.CHARGE_LOOP_SFX)
	for path in FinisherArtLayout.BAR_SFX:
		bar_sounds.append(_add_sound(path))
	knight_breaker_sound = _add_sound(FinisherArtLayout.KNIGHT_BREAKER_SFX)


# Under this node, in the player's branch, so they play on through the freeze.
func _add_sound(path: String) -> AudioStreamPlayer:
	var sound := AudioStreamPlayer.new()
	sound.stream = load(path)
	add_child(sound)
	return sound


func is_active() -> bool:
	return phase != Phase.OFF


func is_input_locked() -> bool:
	return input_lock_left > 0.0


# The pair the mash alternates between, and the rest of its input plumbing, shared with the grab
# escape's mash (MashInput).
func mash_actions() -> Array[StringName]:
	return MashInput.actions(player)


func is_mash_latched() -> bool:
	return latch_left > 0.0


func charge_time_left() -> float:
	if phase != Phase.DAZED and phase != Phase.CHARGING:
		return 0.0
	return maxf(prompt_delay + charge_time_limit - daze_time, 0.0)


# The freeze and the zoom are static, so they'd outlive the fight scene.
func _exit_tree() -> void:
	if phase != Phase.OFF:
		FightFreeze.unfreeze(get_tree())
		ScreenView.reset(get_tree())


func _input(event: InputEvent) -> void:
	var action := MashInput.pressed_action(player, event)
	var attack_or_dash := event.is_action_pressed("punch") or event.is_action_pressed("dodge")
	if phase == Phase.OFF:
		if not (attack_or_dash and is_input_locked()):
			return
	elif action.is_empty() and not attack_or_dash and not (player.feel_v2 and _v2_swallows(event)):
		return
	# Before the event is marked handled: the autoload's device tracker sits below this node in the
	# propagation order and would never see the presses that drive the mash.
	InputSettings.note_device(event)
	get_viewport().set_input_as_handled()
	if not action.is_empty() and ((phase == Phase.DAZED and prompt_visible) or phase == Phase.CHARGING or phase == Phase.CHARGE):
		_press(action)


func _v2_swallows(event: InputEvent) -> bool:
	return MashInput.swallows(event)


func _mash_keys_held() -> bool:
	return MashInput.keys_held(player)


# The hit is reported inside a physics flush, where collision can't be taken out of physics.
func _on_charged_hit_landed(target: Node) -> void:
	_try_begin.call_deferred(target)


func _try_begin(target: Node) -> void:
	if phase != Phase.OFF or not is_instance_valid(target) or not target.has_method("can_be_dazed"):
		return
	if player.fight_over or player.playerHealth <= 0 or player.is_grabbed or player.is_talking:
		return
	if not target.can_be_dazed():
		return
	boss = target
	dazed = false
	player.begin_finisher()
	player.combo.reset()
	_set_phase(Phase.SETTLE)


# A fight hands the player the finisher outright, for something they have already earned: the boss is
# dazed, the prompt never shows and the uppercut fires on its own after `hold` seconds of the dazed
# pose, which is the beat that makes it read as "he is reeling, and then you hit him". Everything
# else is the hand-driven path: the same entry guards, the freeze, the supercharge decision, the
# contact, the knockback, the kill rule and the outro. Returns whether it started.
func begin_auto(target: Node, hold := 0.35) -> bool:
	if phase != Phase.OFF:
		return false
	auto = true
	auto_hold = maxf(hold, 0.0)
	_try_begin(target)
	if phase == Phase.OFF:
		auto = false
		return false
	return true


# A fight runs the mash on its own account: the same keys, the same prompt, the same camera, and
# NOTHING else. No boss, no daze, no FightFreeze, no player pose, no uppercut, no damage, no hype.
# The caller owns all of that. Returns false if a finisher is already running.
# Two beats, as in a mashed finisher: charge_ended(true) is the meter filling, and `finished` about
# SCRIPTED_FULL_HOLD later is the prompt's FULL! flash having played out, the mash keys stopping being
# swallowed and the player being theirs again. A caller who hands them back does it on `finished`.
#   config, all optional:
#     "press_gain"  meter per alternating press             default 0.12
#     "floor_time"  seconds to fill with no presses at all  default 6.0
#     "zoom"        the view's zoom                         default charge_zoom
#     "focus"       a Vector2 the view centres on, or Vector2.INF for the player
func begin_scripted_charge(config := {}) -> bool:
	if phase != Phase.OFF:
		return false
	scripted_gain = config.get("press_gain", SCRIPTED_PRESS_GAIN)
	scripted_floor = maxf(config.get("floor_time", SCRIPTED_FLOOR_TIME), 0.001)
	scripted_filled = false
	scripted_hold_left = 0.0
	meter = 0.0
	last_action = &""
	last_press_usec = 0
	# What arms the release latch at the end: this beat is mashed, whoever asked for it.
	mashed = true
	prompt_visible = true
	zoomed = true
	_set_phase(Phase.CHARGE)
	var focus: Vector2 = config.get("focus", Vector2.INF)
	ScreenView.zoom_to(get_tree(), config.get("zoom", charge_zoom), player.global_position if focus == Vector2.INF else focus, zoom_in_time)
	prompt_shown.emit()
	return true


# The caller takes it back, however far it got: the prompt goes and the view comes back out.
func cancel_scripted_charge() -> void:
	if phase != Phase.CHARGE:
		return
	if not scripted_filled:
		_end_scripted_charge(false)
	_finish()


func is_charging() -> bool:
	return phase == Phase.CHARGE


# The meter is full. The prompt's FULL! flash and fade play out before the charge ends, as they do
# over the uppercut a mashed finisher fires.
func _fill_scripted_charge() -> void:
	scripted_filled = true
	scripted_hold_left = SCRIPTED_FULL_HOLD
	_end_scripted_charge(true)


func _end_scripted_charge(filled: bool) -> void:
	charge_ended.emit(filled)
	if zoomed:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)
	# From here leftover hammering can't throw a punch or walk the player off, exactly as after a
	# mashed finisher.
	_lock_input()


func _process(delta: float) -> void:
	if phase == Phase.OFF:
		input_lock_left = maxf(input_lock_left - delta, 0.0)
		# Letting go of every mash key ends it early: from then on a press is meant.
		if latch_left > 0.0:
			latch_left = maxf(latch_left - delta, 0.0) if _mash_keys_held() else 0.0
		return
	phase_time += delta
	# A scripted charge has no boss to lose, so only the fight ending takes it away.
	if phase == Phase.CHARGE:
		if player.fight_over:
			cancel_scripted_charge()
			return
	# The uppercut always plays out to its landing, and a juggled boss to his, even past a kill.
	elif phase != Phase.UPPERCUT and phase != Phase.JUGGLE_FALL and (player.fight_over or not _boss_valid()):
		_abort()
		return
	match phase:
		Phase.SETTLE:
			if phase_time >= daze_settle_time and player.state_machine.current_state.name != "Punching" and not player.combo.report_pending():
				_begin_daze()
		Phase.DAZED:
			daze_time += delta
			if auto:
				# No prompt, no presses and no time limit: the beat is the boss reeling, and then the
				# uppercut, which the charging phase fires on the next frame from a full meter.
				if daze_time >= auto_hold:
					meter = 1.0
					_start_charging()
			elif not prompt_visible and daze_time >= prompt_delay:
				prompt_visible = true
				mashed = true
				if tiered:
					charge_loop.pitch_scale = 1.0 + FinisherArtLayout.CHARGE_LOOP_PITCH_PER_BAR * charge_level
					charge_loop.play()
				prompt_shown.emit()
			elif tiered and prompt_visible:
				tier_meter.advance(delta)
				if tier_meter.resolved:
					_resolve_mash()
			elif daze_time >= prompt_delay + charge_time_limit:
				_start_fizzle()
		Phase.CHARGING:
			if tiered:
				_charge_tiered(delta)
			# Before the drain, so the press that filled the meter counts.
			elif meter >= 1.0:
				_start_uppercut()
			else:
				daze_time += delta
				meter = maxf(meter - meter_drain_per_second * delta, 0.0)
				_animate_charge(delta)
				if daze_time >= prompt_delay + charge_time_limit:
					_start_fizzle()
		Phase.UPPERCUT:
			# The boss's arc first, so a contact this frame launches him from where he is now.
			_fly_boss(delta)
			if phase == Phase.UPPERCUT:
				_advance_uppercut()
		Phase.JUGGLE_FALL:
			_fly_boss(delta)
		Phase.FIZZLE:
			if phase_time >= fizzle_time:
				_end_fizzle()
		Phase.CHARGE:
			if scripted_filled:
				scripted_hold_left -= delta
				if scripted_hold_left <= 0.0:
					_finish()
			else:
				# No drain, and the meter rises on its own: with nobody pressing anything it still fills
				# inside floor_time, which is what makes the beat unfailable.
				meter = minf(meter + delta / scripted_floor, 1.0)
				if meter >= 1.0:
					_fill_scripted_charge()
	if juggling and phase != Phase.OFF:
		_follow_juggle(delta)
	if phase == Phase.OFF:
		return
	_animate_stars(delta)
	# Every frame, so a shake written straight to the canvas by another script can't linger.
	ScreenView.apply(get_tree())


func _set_phase(new_phase: Phase) -> void:
	phase = new_phase
	phase_time = 0.0


func _begin_daze() -> void:
	# The window can close during the beat.
	if not boss.can_be_dazed():
		player.end_finisher(false)
		_finish()
		return
	boss.enter_daze()
	dazed = true
	supercharged = player.hype.is_full()
	tiered = player.feel_v2 and boss.has_method("can_be_juggled") and boss.can_be_juggled()
	if tiered:
		# A full hype meter banks bar 1 before the first press.
		tier_meter = FinisherTierMeter.new(tier_gain, tier_drains, tier_windows, tier_start_grace, tier_idle_stop, 1 if supercharged else 0)
		smoothed_meter = tier_meter.meter
		charge_level = tier_meter.meter
	FightFreeze.freeze(get_tree(), [player.get_parent()])
	player.enter_finisher_pose()
	flipped = _boss_on_left()
	_show_pose(_sheet().ready)
	_spawn_stars(boss.get_daze_anchor())
	get_tree().call_group("arena_crowd", "cheer", 1.0)
	daze_time = 0.0
	prompt_visible = false
	meter = tier_meter.meter if tiered else 0.0
	last_action = &""
	last_press_usec = 0
	_set_phase(Phase.DAZED)
	if auto:
		# The view closes in over the held beat instead of over a mash, so the uppercut lands on a
		# camera that has already arrived.
		zoomed = true
		ScreenView.zoom_to(get_tree(), zoom, player.global_position.lerp(boss.get_daze_anchor(), focus_boss_weight), zoom_in_time)


func _press(action: StringName) -> void:
	var now := Time.get_ticks_usec()
	if not MashInput.counts(action, last_action, now, last_press_usec, min_press_interval):
		return
	last_action = action
	last_press_usec = now
	if phase == Phase.CHARGE:
		meter = minf(meter + scripted_gain, 1.0)
	elif tiered:
		var banked: int = tier_meter.press()
		meter = tier_meter.meter
		if banked > 0:
			_on_bar_banked(banked)
	else:
		meter = minf(meter + meter_gain_per_press, 1.0)
	var pair := mash_actions()
	meter_changed.emit(meter, pair[1] if action == pair[0] else pair[0])
	get_tree().call_group("arena_crowd", "cheer", 0.4)
	if phase == Phase.DAZED:
		_start_charging()


func _start_charging() -> void:
	_set_phase(Phase.CHARGING)
	charge_clock = 0.0
	charge_step = 0
	_show_pose(_sheet().charge[0])
	zoomed = true
	if tiered and not auto:
		# The charge drives the view itself from here (_escalate), easing in from where it is.
		if ScreenView.zoom_tween:
			ScreenView.zoom_tween.kill()
		charge_zoom_from = ScreenView.zoom
		charge_focus_from = ScreenView.focus
		charge_time = 0.0
		return
	ScreenView.zoom_to(get_tree(), zoom, player.global_position.lerp(boss.get_daze_anchor(), focus_boss_weight), zoom_in_time)


func _charge_tiered(delta: float) -> void:
	if auto:
		juggle_tiers = 1
		_start_uppercut()
		return
	tier_meter.advance(delta)
	meter = tier_meter.meter
	if tier_meter.resolved:
		_resolve_mash()
		return
	_escalate(delta)
	_animate_charge(delta)


# What the mash banked: an uppercut for each bar, or today's fizzle for none.
func _resolve_mash() -> void:
	charge_loop.stop()
	juggle_tiers = tier_meter.banked
	if juggle_tiers == 0:
		_start_fizzle()
		return
	_start_uppercut()


# The view closes in and rattles harder as the charge builds. The prompt is on the HUD, so neither
# touches it.
func _escalate(delta: float) -> void:
	smoothed_meter = lerpf(smoothed_meter, meter, 1.0 - exp(-delta / meter_smoothing))
	charge_level = maxf(float(tier_meter.banked), smoothed_meter)
	charge_time += delta
	var ease_in := 1.0 - pow(1.0 - clampf(charge_time / zoom_in_time, 0.0, 1.0), 2.0)
	var focus := player.global_position.lerp(boss.get_daze_anchor(), focus_boss_weight)
	ScreenView.zoom = lerpf(charge_zoom_from, charge_zoom + charge_zoom_per_bar * charge_level, ease_in)
	ScreenView.focus = charge_focus_from.lerp(focus, ease_in)
	var real_delta := delta / maxf(Engine.time_scale, 0.001)
	kick_left -= real_delta
	rumble_left -= real_delta
	if kick_left <= 0.0 and rumble_left <= 0.0:
		ScreenView.shake(get_tree(), charge_rumble + charge_rumble_per_bar * charge_level, 1, rumble_step, Vector2.ZERO, true)
		rumble_left = rumble_step
	charge_loop.pitch_scale = 1.0 + FinisherArtLayout.CHARGE_LOOP_PITCH_PER_BAR * charge_level


func _on_bar_banked(tier: int) -> void:
	ScreenView.shake(get_tree(), bank_kicks[tier - 1], bank_kick_steps, IMPACT_SHAKE_STEP_TIME, Vector2.ZERO, true)
	kick_left = bank_kick_steps * IMPACT_SHAKE_STEP_TIME
	get_tree().call_group("arena_crowd", "cheer", bank_cheers[tier - 1])
	bar_sounds[tier - 1].play()
	tier_banked.emit(tier)


func _animate_charge(delta: float) -> void:
	var frame_times: Array = _sheet().charge_frame_time
	charge_clock += delta
	var frame_time := lerpf(frame_times[0], frame_times[1], charge_level / 3.0 if tiered else meter)
	if charge_clock < frame_time:
		return
	charge_clock -= frame_time
	charge_step = (charge_step + 1) % _sheet().charge.size()
	_show_pose(_sheet().charge[charge_step])


func _start_uppercut() -> void:
	charge_ended.emit(true)
	if supercharged:
		_flash(player.sprite, super_launch_flash)
	if tiered:
		juggle_index = 0
		juggle_goes_on = true
		special = false
		lift = 0.0
	_set_phase(Phase.UPPERCUT)
	uppercut_step = -1
	_advance_uppercut()


func _advance_uppercut() -> void:
	var steps: Array = _sheet().uppercut
	var starts := FinisherArtLayout.uppercut_step_starts()
	while uppercut_step + 1 < steps.size() and phase_time + STEP_TOLERANCE >= starts[uppercut_step + 1]:
		if special and FinisherArtLayout.KNIGHT_BREAKER_GHOST.steps.has(uppercut_step + 1):
			_drop_ghost()
		uppercut_step += 1
		_show_pose(steps[uppercut_step])
		if uppercut_step == _sheet().contact_step:
			if tiered:
				_juggle_contact()
			else:
				_contact()
	if tiered and juggle_goes_on and juggle_index + 1 < juggle_tiers and phase_time + STEP_TOLERANCE >= starts[steps.size() - 1] + relaunch_delay:
		_relaunch()
	elif phase_time + STEP_TOLERANCE >= starts[-1]:
		if tiered and airborne:
			_set_phase(Phase.JUGGLE_FALL)
		else:
			_land()


# The next uppercut, from the land frame.
func _relaunch() -> void:
	juggle_index += 1
	special = juggle_index == 2
	_set_phase(Phase.UPPERCUT)
	uppercut_step = -1
	_advance_uppercut()


# The fight starts again at contact, before any damage, so a killing blow goes through the boss's own
# defeat and FightOutro as a punch would, and the outro never meets a frozen scene.
func _contact() -> void:
	var landed := _boss_valid() and _in_reach()
	var box := _hurtbox_rect() if landed else Rect2()
	var super_applied := false
	FightFreeze.unfreeze(get_tree())
	_clear_stars()
	if landed:
		var max_health: int = boss.get_max_health()
		var normal := maxi(1, roundi(max_health * finisher_damage_ratio))
		var dealt: int = boss.take_finisher(maxi(1, roundi(max_health * supercharged_damage_ratio)) if supercharged else normal)
		# A phase floor or a nearly dead boss can clip it: hype is only spent for damage it added.
		super_applied = supercharged and dealt > normal
		if super_applied:
			player.hype.spend()
		boss.exit_daze(true)
		var stagger: float = super_stagger_time if super_applied else stagger_time
		# A killing blow leaves him where he stands: his defeat and the outro play from that spot.
		if boss.get_health_ratio() > 0.0:
			var rocked := _knock_back(super_uppercut_knockback if super_applied else uppercut_knockback, stagger)
			# A boss rocking back on his sprite is already reeling; a hop on the same offset would fight it.
			if boss.end_recovery(stagger) and not rocked:
				_hop(boss.sprite)
		_spawn_impact(box, super_applied)
		if super_applied:
			# On the contact frame with the freeze, the shake and the burst, so the hit is one event.
			# Audio runs on its own clock, so the hit-stop neither chops it nor bends its pitch.
			super_sfx_player.play()
			_super_contact_extras(box)
		HitStop.freeze(get_tree(), super_impact_hit_stop if super_applied else impact_hit_stop)
		ScreenView.shake(get_tree(), super_impact_shake if super_applied else impact_shake, super_impact_shake_steps if super_applied else IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP_TIME)
		_flash(boss.sprite, super_impact_flash if super_applied else impact_flash)
		get_tree().call_group("arena_crowd", "cheer", super_impact_cheer if super_applied else impact_cheer)
	elif _boss_valid():
		# A whiff: the punish window carries on with the time it had left.
		boss.exit_daze(false)
	if super_applied:
		# The punch owns the view from here: it snaps in, holds, then eases out over the freeze.
		_super_zoom_punch()
	else:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)


# One uppercut of the juggle: its share of his health, and a launch higher than the one before. The first
# unfreezes the fight and hands him to his juggled state; the last knocks him back unless it killed him.
# A kill or a whiff means none follow.
func _juggle_contact() -> void:
	var landed := _boss_valid() and _in_reach()
	var box := _hurtbox_rect() if landed else Rect2()
	if juggle_index == 0:
		FightFreeze.unfreeze(get_tree())
		_clear_stars()
		if not landed:
			juggle_goes_on = false
			if _boss_valid():
				boss.exit_daze(false)
			ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)
			return
		boss.exit_daze(true)
		boss.begin_juggle()
		lift_scale = clampf(boss.juggle_headroom() / _planned_apex(), 0.0, 1.0)
		juggling = true
		camera_time = 0.0
		camera_zoom_from = ScreenView.zoom
		camera_focus_from = ScreenView.focus
		if ScreenView.zoom_tween:
			ScreenView.zoom_tween.kill()
	elif not landed:
		juggle_goes_on = false
		return
	var last := juggle_index == juggle_tiers - 1
	var share: float = juggle_shares[juggle_index]
	var max_health: int = boss.get_max_health()
	var normal := maxi(1, roundi(max_health * share))
	var amount := maxi(1, roundi(max_health * (share + supercharge_bonus))) if last and supercharged else normal
	var dealt: int = boss.take_juggle_hit(amount, FinisherArtLayout.JUGGLE_HIT_PITCHES[juggle_index])
	# A nearly dead boss can clip it: hype is only spent for damage it added.
	var super_applied := last and supercharged and dealt > normal
	if super_applied:
		player.hype.spend()
	var killed: bool = boss.get_health_ratio() <= 0.0
	if killed:
		last = true
		juggle_goes_on = false
	arc_from = lift
	arc_speed = juggle_last_launches[juggle_index] if last else juggle_launches[juggle_index]
	arc_time = 0.0
	airborne = true
	boss.juggle_pose(&"launch")
	last_hit_big = special or super_applied
	# A killing blow leaves him where it caught him: his defeat and the outro play from under it.
	if last and not killed:
		_knock_back(super_uppercut_knockback if last_hit_big else uppercut_knockback, 0.0, true)
	_spawn_impact(box, last_hit_big)
	if last_hit_big:
		_super_contact_extras(box)
		_juggle_zoom_punch()
	if special:
		knight_breaker_sound.play()
	if super_applied:
		super_sfx_player.play()
	HitStop.freeze(get_tree(), super_impact_hit_stop if super_applied else juggle_hit_stops[juggle_index])
	ScreenView.shake(get_tree(), super_impact_shake if last_hit_big else impact_shake, super_impact_shake_steps if last_hit_big else IMPACT_SHAKE_STEPS, IMPACT_SHAKE_STEP_TIME)
	_flash(boss.sprite, super_impact_flash if last_hit_big else impact_flash)
	get_tree().call_group("arena_crowd", "cheer", super_impact_cheer if last_hit_big else impact_cheer)
	juggle_hit.emit(juggle_index, last)


# The highest the juggle ahead would throw him, each uppercut catching him where the one before left him.
func _planned_apex() -> float:
	var starts := FinisherArtLayout.uppercut_step_starts()
	var between: float = starts[_sheet().uppercut.size() - 1] + relaunch_delay
	var apex := 0.0
	var from := 0.0
	for i in juggle_tiers:
		var speed: float = juggle_last_launches[i] if i == juggle_tiers - 1 else juggle_launches[i]
		apex = maxf(apex, from + speed * speed / (2.0 * juggle_gravity))
		from += speed * between - 0.5 * juggle_gravity * between * between
	return apex


# His arc, in game time like the uppercuts, so the two stay in step through every hit-stop.
func _fly_boss(delta: float) -> void:
	if not airborne or not _boss_valid():
		return
	arc_time += delta
	lift = arc_from + arc_speed * arc_time - 0.5 * juggle_gravity * arc_time * arc_time
	if lift > 0.0:
		boss.juggle_lift(lift * lift_scale)
		return
	lift = 0.0
	airborne = false
	boss.juggle_lift(0.0)
	_crash()


# He hits the mat: his crash, a shake, and, alive, the recovery that ends in his next attack. The view
# eases back out, and the player, who has landed first, is theirs again.
func _crash() -> void:
	var crater := special and last_hit_big
	boss.juggle_pose(&"crash", crater)
	ScreenView.shake(get_tree(), special_crash_shake if crater else crash_shake, crash_shake_steps, IMPACT_SHAKE_STEP_TIME)
	if boss.get_health_ratio() > 0.0:
		boss.end_recovery(long_juggle_recovery if last_hit_big else juggle_recovery)
	juggling = false
	if punch_tween:
		punch_tween.kill()
	punch_zoom = 1.0
	ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, juggle_zoom_out_time)
	if phase == Phase.JUGGLE_FALL:
		_land()


# Between the player and the boss in the air, easing in from the mash's view, and on top of it
# Knight Breaker's zoom punch.
func _follow_juggle(delta: float) -> void:
	camera_time += delta
	var ease_in := 1.0 - pow(1.0 - clampf(camera_time / juggle_zoom_in_time, 0.0, 1.0), 2.0)
	var middle: Vector2 = player.global_position.lerp(boss.get_juggle_point(), 0.5) if _boss_valid() else ScreenView.focus
	ScreenView.zoom = lerpf(camera_zoom_from, juggle_zoom, ease_in) * punch_zoom
	ScreenView.focus = camera_focus_from.lerp(middle, ease_in)


# Snapped in, held and eased back in real time, so it plays out through the hit-stop.
func _juggle_zoom_punch() -> void:
	if punch_tween:
		punch_tween.kill()
	punch_tween = create_tween().set_ignore_time_scale(true)
	punch_tween.tween_property(self, "punch_zoom", super_impact_zoom, super_impact_zoom_in_time)
	punch_tween.tween_interval(super_impact_zoom_hold)
	punch_tween.tween_property(self, "punch_zoom", 1.0, super_impact_zoom_out_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


# Knight Breaker's afterimage: the pose just shown, left behind in gold as the next one replaces it.
func _drop_ghost() -> void:
	var source: Sprite2D = player.sprite
	var spec := FinisherArtLayout.KNIGHT_BREAKER_GHOST
	var ghost := Sprite2D.new()
	ghost.texture = source.texture
	ghost.hframes = source.hframes
	ghost.vframes = source.vframes
	ghost.frame = source.frame
	ghost.flip_h = source.flip_h
	ghost.centered = source.centered
	ghost.offset = source.offset
	ghost.scale = source.global_scale
	ghost.modulate = spec.tint
	fx_layer.add_child(ghost)
	ghost.global_position = source.global_position
	var fade := ghost.create_tween()
	fade.tween_property(ghost, "modulate:a", 0.0, spec.fade_time)
	fade.tween_callback(ghost.queue_free)


# The shove away from the player. A boss who can take it moves for real, clamped to his own ground;
# the rest rock back on their sprite and settle through the stagger, so nothing anchored to their
# position moves with them. Returns true when the sprite is what moved. A `level` shove keeps his
# ground line: a juggle's, whose heights are fitted to where he stands.
func _knock_back(distance: float, settle_time: float, level := false) -> bool:
	if distance <= 0.0 or not _boss_valid():
		return false
	var push := (_hurtbox_rect().get_center() - player.global_position).normalized()
	if level:
		push = Vector2(-1.0 if flipped else 1.0, 0.0)
	if push == Vector2.ZERO:
		push = Vector2.UP
	if boss.has_method("knock_back"):
		boss.knock_back(push * distance, uppercut_knockback_time)
		return false
	var sprite: Sprite2D = boss.sprite
	var rest := sprite.offset
	# The offset is in the sheet's texels, so the px shove is divided by what the sprite is drawn at.
	var slide: Vector2 = rest + push * distance / sprite.global_scale
	var recoil := sprite.create_tween()
	recoil.tween_property(sprite, "offset", slide, uppercut_knockback_time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	recoil.tween_property(sprite, "offset", rest, maxf(settle_time - uppercut_knockback_time, 0.1)).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	return true


# The supercharged extras: a shock ring rolling out along the floor and speed lines across the
# screen. Both ignore hit-stop, so they play out during the longer freeze.
func _super_contact_extras(box: Rect2) -> void:
	var point := box.get_center() if box.has_area() else player.global_position
	# The ring rolls out along the floor, so it starts at the boss's feet rather than his chest.
	_spawn_shock_ring(Vector2(point.x, box.end.y) if box.has_area() else point)
	_spawn_speedlines(point)


# Snapped in on the contact frame and eased back out, in real time so it reads through the hit-stop.
func _super_zoom_punch() -> void:
	ScreenView.zoom_to(get_tree(), ScreenView.zoom * super_impact_zoom, ScreenView.focus, super_impact_zoom_in_time, true)
	var settle := get_tree().create_timer(super_impact_zoom_in_time + super_impact_zoom_hold, false, false, true)
	# A method rather than a closure: the timer outlives a scene change, the connection doesn't.
	settle.timeout.connect(_ease_out_super_zoom)


func _ease_out_super_zoom() -> void:
	if not player.fight_over:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, super_impact_zoom_out_time, true)


func _spawn_shock_ring(point: Vector2) -> void:
	var spec := FinisherArtLayout.super_shock_ring()
	if spec.has("texture"):
		var sheet := _make_sheet(spec, spec.scale)
		_ground_layer().add_child(sheet)
		sheet.global_position = point.round()
		_play_sheet(sheet, spec)
		return
	var ring := Line2D.new()
	ring.width = spec.width
	ring.default_color = spec.color
	ring.closed = true
	var points := PackedVector2Array()
	for i in spec.points:
		points.append(Vector2.from_angle(TAU * i / spec.points))
	ring.points = points
	ring.scale = Vector2.ONE * spec.radius
	fx_layer.add_child(ring)
	ring.global_position = point
	var grow := ring.create_tween().set_parallel().set_ignore_time_scale(true)
	grow.tween_property(ring, "scale", Vector2.ONE * spec.to_radius, spec.time).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	grow.tween_property(ring, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(ring.queue_free)


func _spawn_speedlines(point: Vector2) -> void:
	var spec := FinisherArtLayout.super_speedlines()
	if spec.has("texture"):
		var screen_point: Vector2 = get_viewport().get_canvas_transform() * point
		var middle := get_viewport().get_visible_rect().size / 2.0
		var lines_scale: float = spec.off_centre_scale if screen_point.distance_to(middle) > spec.off_centre else spec.scale
		var sheet := _make_sheet(spec, lines_scale)
		var hud: CanvasLayer = player.get_parent().get_node("CanvasLayer")
		hud.add_child(sheet)
		# First on the HUD layer: over the arena, under every readout.
		hud.move_child(sheet, 0)
		sheet.position = screen_point.round()
		_play_sheet(sheet, spec)
		return
	var lines := Node2D.new()
	fx_layer.add_child(lines)
	lines.global_position = point
	for i in spec.rays:
		var ray := Polygon2D.new()
		var out := Vector2.from_angle(TAU * i / spec.rays)
		var side: Vector2 = out.orthogonal() * spec.width / 2.0
		ray.polygon = PackedVector2Array([out * spec.inner_radius + side, out * spec.length, out * spec.inner_radius - side])
		ray.color = spec.color
		lines.add_child(ray)
	var fade := lines.create_tween().set_ignore_time_scale(true)
	fade.tween_property(lines, "modulate:a", 0.0, spec.time)
	fade.tween_callback(lines.queue_free)


func _make_sheet(spec: Dictionary, sheet_scale: float) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(spec.texture)
	sheet.hframes = spec.hframes
	sheet.centered = false
	sheet.offset = -spec.pivot
	sheet.scale = Vector2.ONE * sheet_scale
	return sheet


func _play_sheet(sheet: Sprite2D, spec: Dictionary) -> void:
	var frames := sheet.create_tween().set_ignore_time_scale(true)
	for i in spec.frame_times.size():
		frames.tween_callback(sheet.set_frame.bind(i))
		frames.tween_interval(spec.frame_times[i])
	frames.tween_callback(sheet.queue_free)


# A layer in the arena drawn before the player and the boss, for effects that belong on the floor.
func _ground_layer() -> Node2D:
	var stage: Node2D = player.get_parent()
	var arena: Node = stage.get_parent()
	var layer: Node2D = arena.get_node_or_null("GroundFx")
	if layer == null:
		layer = Node2D.new()
		layer.name = "GroundFx"
		layer.position.y = GROUND_FX_Y
		arena.add_child(layer)
		arena.move_child(layer, stage.get_index())
	return layer


func _land() -> void:
	player.end_finisher(true)
	_lock_input()
	_finish()


func _start_fizzle() -> void:
	charge_loop.stop()
	charge_ended.emit(false)
	_show_pose(_sheet().ready)
	if zoomed:
		ScreenView.zoom_to(get_tree(), 1.0, ScreenView.focus, zoom_out_time)
	_set_phase(Phase.FIZZLE)


func _end_fizzle() -> void:
	FightFreeze.unfreeze(get_tree())
	_clear_stars()
	boss.exit_daze(false)
	player.end_finisher(true)
	_lock_input()
	_finish()


func _abort() -> void:
	charge_loop.stop()
	FightFreeze.unfreeze(get_tree())
	ScreenView.reset(get_tree())
	_clear_stars()
	if dazed and _boss_valid():
		boss.exit_daze(false)
	player.end_finisher(false)
	_finish()


func _finish() -> void:
	if mashed and player.feel_v2 and _mash_keys_held():
		latch_left = mash_release_latch
	mashed = false
	phase = Phase.OFF
	boss = null
	auto = false
	dazed = false
	supercharged = false
	prompt_visible = false
	zoomed = false
	tiered = false
	juggling = false
	airborne = false
	special = false
	scripted_filled = false
	charge_loop.stop()
	finished.emit()


func _lock_input() -> void:
	input_lock_left = post_input_lock


func _boss_valid() -> bool:
	return is_instance_valid(boss) and boss.is_inside_tree() and not boss.is_queued_for_deletion()


func _sheet() -> Dictionary:
	return FinisherArtLayout.player_sheet()


func _show_pose(pose: Array) -> void:
	player.state_machine.states["Finishing"].show_frame(pose[0], pose[1], flipped)


func _hurtbox_rect() -> Rect2:
	var shape: CollisionShape2D = boss.get_finisher_hurtbox().get_node("CollisionShape2D")
	return shape.global_transform * shape.shape.get_rect()


func _boss_on_left() -> bool:
	var dx := _hurtbox_rect().get_center().x - player.global_position.x
	if absf(dx) < SIDE_DEAD_ZONE:
		return player.facing == player.Facing.LEFT
	return dx < 0.0


func _fist_point(step: int) -> Vector2:
	return player.global_position + FinisherArtLayout.mirrored(_sheet().fists[step], flipped)


func _in_reach() -> bool:
	var reach := _hurtbox_rect().grow(uppercut_reach)
	if reach.has_point(player.global_position):
		return true
	for step in _sheet().reach_steps:
		if reach.has_point(_fist_point(step)):
			return true
	return false


func _spawn_stars(anchor: Vector2) -> void:
	var spec := FinisherArtLayout.stars()
	stars = Sprite2D.new()
	stars.texture = load(spec.texture)
	stars.hframes = spec.hframes
	stars.centered = false
	stars.offset = -spec.pivot
	stars.scale = Vector2.ONE * spec.scale
	fx_layer.add_child(stars)
	stars.global_position = anchor.round()
	stars_clock = 0.0


func _animate_stars(delta: float) -> void:
	if not is_instance_valid(stars):
		return
	stars_clock += delta
	stars.frame = int(stars_clock / FinisherArtLayout.stars().frame_time) % stars.hframes


func _clear_stars() -> void:
	if is_instance_valid(stars):
		stars.queue_free()
	stars = null


func _spawn_impact(box: Rect2, super_burst: bool) -> void:
	var point := _fist_point(_sheet().contact_step) + FinisherArtLayout.mirrored(FinisherArtLayout.IMPACT_OFFSET, flipped)
	point = point.clamp(box.position, box.end).round()
	var spec := FinisherArtLayout.super_impact() if super_burst else FinisherArtLayout.impact()
	if spec.has("texture"):
		var burst := Sprite2D.new()
		burst.texture = load(spec.texture)
		burst.hframes = spec.hframes
		burst.centered = false
		burst.offset = -spec.pivot
		burst.scale = Vector2.ONE * spec.scale
		# The placeholder supercharged burst is the normal one, tinted.
		burst.self_modulate = spec.get("tint", Color.WHITE)
		fx_layer.add_child(burst)
		burst.global_position = point
		var frames := burst.create_tween()
		for i in spec.frame_times.size():
			frames.tween_callback(burst.set_frame.bind(i))
			frames.tween_interval(spec.frame_times[i])
		frames.tween_callback(burst.queue_free)
		return
	var spark := Polygon2D.new()
	var polygon := PackedVector2Array()
	var corners: int = spec.points * 2
	for i in corners:
		var radius: float = spec.outer_radius if i % 2 == 0 else spec.inner_radius
		polygon.append(Vector2.from_angle(TAU * i / corners - PI / 2.0) * radius)
	spark.polygon = polygon
	spark.color = spec.color * spec.get("tint", Color.WHITE)
	spark.scale = Vector2.ONE * spec.from_scale
	fx_layer.add_child(spark)
	spark.global_position = point
	var grow := spark.create_tween().set_parallel()
	grow.tween_property(spark, "scale", Vector2.ONE * spec.to_scale, spec.time)
	grow.tween_property(spark, "modulate:a", 0.0, spec.time)
	grow.chain().tween_callback(spark.queue_free)


func _flash(sprite: CanvasItem, color: Color) -> void:
	sprite.self_modulate = color
	get_tree().create_tween().tween_property(sprite, "self_modulate", Color(1, 1, 1), impact_flash_time)


# The offset rather than the position: hit shakes, frame_point() and y-sorting all use the position.
func _hop(sprite: Sprite2D) -> void:
	var base_y := sprite.offset.y
	var lift := func(texels: float) -> void:
		sprite.offset.y = base_y - roundi(texels)
	var hop := sprite.create_tween()
	hop.tween_method(lift, 0.0, float(stagger_hop_texels), HOP_UP_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	hop.tween_method(lift, float(stagger_hop_texels), 0.0, HOP_DOWN_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	hop.tween_method(lift, 0.0, float(HOP_BOUNCE_TEXELS), HOP_BOUNCE_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	hop.tween_method(lift, float(HOP_BOUNCE_TEXELS), 0.0, HOP_BOUNCE_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
