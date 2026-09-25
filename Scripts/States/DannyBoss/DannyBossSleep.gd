extends State

# His nap after every Sumo Smash string, and the window to punish him in (plan section 5). He sits where the
# string left him for sleep_time on his SleepTimer and heals: after the settle, regen_share of his max health
# a second in whole-HP ticks, each one a green "+N" over his crown and a chime, the bar filling without a
# sound. Every punch that lands flinches him and holds the regen for hit_pause; hit_cap of them at most, and a
# charged third dazes him for the single-bar finisher, whose uppercut ends the nap
# (DannyBossScript.end_recovery). Time up, he wakes and goes back to Idle. Enter() needs nothing from the
# state before it, so a bare transition into it opens a working window.

@export var body : CharacterBody2D
@export var sleep_timer : Timer

@export var sleep_time := 5.0
# He only sits for this long before the regen starts.
@export var settle := 0.5
# A share of his max health a second.
@export var regen_share := 0.05
@export var hit_pause := 0.6
# This window's cap (DannyBossScript.window_hit_cap).
@export var hit_cap := 6
# His theme this far under its own level while he sleeps.
@export var music_duck_db := -4.0
@export var music_duck_time := 0.3

# Shown on the first nap of the fight.
const HINT_KEY := &"sleep"
const HINT_TEXT := "HE'S HEALING! HIT HIM FAST!"

@onready var state_machine = get_parent()

# Starts spent, so a release() from a path that never entered this state does nothing.
var released := true
var settle_left := 0.0
var pause_left := 0.0
var regen_clock := 0.0
# Seconds since Enter, the HP healed, and when each tick landed and what it healed, for a test.
var clock := 0.0
var healed := 0
var tick_times: Array[float] = []
var tick_amounts: Array[int] = []


func Enter() -> void:
	released = false
	body.velocity = Vector2.ZERO
	body.show_body()
	body.hits_this_window = 0
	body.daze_used = false
	body.play_state_anim(&"sleep")
	body.set_body_box(&"sleep")
	body.set_hurtbox_active(true)
	body.show_zzz(true)
	body.play_sfx(&"snore")
	body.duck_music(music_duck_db, music_duck_time)
	body.show_hint(HINT_KEY, HINT_TEXT)
	settle_left = settle
	pause_left = 0.0
	regen_clock = 0.0
	clock = 0.0
	healed = 0
	tick_times.clear()
	tick_amounts.clear()
	sleep_timer.paused = false
	sleep_timer.start(sleep_time)


func Physics_Update(delta: float) -> void:
	if released:
		return
	clock += delta
	# The two run down together: a punch in the settle holds the regen from the punch, not from the settle's end.
	var held := settle_left > 0.0 or pause_left > 0.0
	settle_left = maxf(settle_left - delta, 0.0)
	pause_left = maxf(pause_left - delta, 0.0)
	if not held:
		regen_clock += delta
		var tick_time := tick_seconds()
		while regen_clock >= tick_time:
			regen_clock -= tick_time
			_tick()
	body.show_regen(is_regenerating())


# Seconds between two ticks of one HP: 1 / (regen_share * max health).
func tick_seconds() -> float:
	return 1.0 / (regen_share * float(body.max_health))


# The regen is running: settled, not held by a punch, and short of his max.
func is_regenerating() -> bool:
	return not released and settle_left <= 0.0 and pause_left <= 0.0 and body.boss_health < body.max_health


func _tick() -> void:
	var amount: int = body.heal(1)
	if amount <= 0:
		return
	healed += amount
	tick_times.append(clock)
	tick_amounts.append(amount)
	body.pop_regen_label(amount)
	body.play_sfx(&"regen_tick")


# A punch landed: he snorts and flinches in his sleep, and the regen holds.
func flinch() -> void:
	pause_left = hit_pause
	body.play_anim(&"sleep_hit", &"sleep")
	body.play_sfx(&"sleep_hit")


func Exit() -> void:
	release()


func release() -> void:
	if released:
		return
	released = true
	sleep_timer.stop()
	if not is_instance_valid(body):
		return
	body.set_hurtbox_active(false)
	body.set_body_box(&"idle")
	body.show_zzz(false)
	body.show_regen(false)
	body.stop_sfx(&"snore")
	body.duck_music(0.0, music_duck_time)
	body.hide_hint(HINT_KEY)


func _exit_tree() -> void:
	release()


func _on_sleep_timer_timeout() -> void:
	if state_machine.current_state != self:
		return
	body.play_anim(&"wake", &"idle")
	body.play_sfx(&"wake")
	state_machine.on_child_transition(self, "Idle")
