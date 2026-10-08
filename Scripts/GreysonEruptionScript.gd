extends Node2D

# One of the zones Greyson's barbell slam plants on the floor under the player (plan section 3.3), beast
# Bixby's crack made big. Its mark opens, then throbs a stage at a time: stage 1 while it waits its turn -
# when is the state machine's to say (schedule_next_eruption) - stage 2 once scheduled, and stage 3, the
# rush, over the last ring_lead under the yellow ring. Several can be pending at once, and their stages tell
# them apart. Then it ERUPTS: the burst plays once over the whole zone, and hurts on its hurt frames.
# fizzle() clears it without erupting. Its rumble is its own, ramped up the fuse (fuse_progress), heard only while
# it is one of the zones going off soonest (GreysonStateMachine.rumbles), and stops as it goes off.
#
# THE ERUPTION HURTS ONCE, and only if the player's FEET are inside it: the bottom middle of their hurtbox,
# the point every floor hazard in this game tests. A dash through it as it goes is DODGED, a perfect dodge;
# the dodge ghost left inside it by a dash out is a near miss, a perfect dodge too. Never parried or
# blocked: nothing about it reads a press. It is its own hit source, and its origin is the player's own
# hurtbox centre.

signal erupted
# The player's answer, the once it was asked.
signal answered(result: int)

const HitInfo := preload("res://Scripts/HitInfo.gd")
const ParryTell := preload("res://Scripts/ParryTell.gd")
const Layout := preload("res://Scripts/GreysonArtLayout.gd")

const ERUPTION_ID := &"greyson_eruption"
# The rumble from waiting to going off: its level under its own and its pitch against its own.
const RUMBLE_DB := Vector2(-12.0, 0.0)
const RUMBLE_PITCH := Vector2(0.9, 1.15)
# The yellow ring stands this far over the zone's centre, clear of a player's head there: zone 1 is centred on the
# player's feet, and a ring standing on them (ParryTell's z, over the fighters) covered them to the chest just as they
# had to move. RING_TOP keeps the ring's 72 px frame inside the ropes for a zone planted up by the top one.
const RING_LIFT := 100.0
const RING_TOP := 72.0

enum Phase { PENDING, SCHEDULED, ERUPTING, FIZZLING }

# Set before it enters the tree.
var player: Node2D
var body: Node2D

var zone: Dictionary = Layout.fx(&"zone")
var mark_spec: Dictionary = Layout.fx(&"erupt_mark")
var burst_spec: Dictionary = Layout.fx(&"erupt_burst")
var radii: Vector2 = zone.radii
var phase := Phase.PENDING
var clock := 0.0
var phase_clock := 0.0
var fuse := 0.0
var fuse_left := 0.0
var stage := 1
var answered_once := false
var mark: Sprite2D
var burst: Sprite2D
var rumble: AudioStreamPlayer
# For tests: seconds from schedule() to the ring and to the eruption, and the answer it got.
var ring_after := -1.0
var erupt_after := -1.0
var result := -1


func _ready() -> void:
	mark = _sheet(mark_spec, _mask(zone.mark_clip))
	var burst_mask := _mask(zone.burst_clip)
	# The mask, not the burst: a mask only cuts what draws on its own z.
	burst_mask.z_index = body.fx_layer.z_index if is_instance_valid(body) else 0
	burst = _sheet(burst_spec, burst_mask)
	burst.hide()
	_show_mark()
	if is_instance_valid(body):
		rumble = body.sfx_player_for(&"eruption_rumble", self)
		_ramp_rumble()
		rumble.play()


# Goes off `seconds` from now, the rush and the ring coming ring_lead before. Once.
func schedule(seconds: float) -> void:
	if phase != Phase.PENDING:
		return
	phase = Phase.SCHEDULED
	phase_clock = 0.0
	fuse = maxf(seconds, 0.0)
	fuse_left = fuse
	stage = 2
	if fuse_left <= zone.ring_lead:
		_rush()


# Cleared without erupting, whatever it was waiting for.
func fizzle() -> void:
	if phase != Phase.PENDING and phase != Phase.SCHEDULED:
		return
	ParryTell.clear(self)
	_stop_rumble()
	phase = Phase.FIZZLING
	phase_clock = 0.0


func is_pending() -> bool:
	return phase == Phase.PENDING or phase == Phase.SCHEDULED


# 0 while it waits its turn, then up to 1 across its fuse once it is scheduled.
func fuse_progress() -> float:
	if phase == Phase.PENDING:
		return 0.0
	if phase != Phase.SCHEDULED or fuse <= 0.0:
		return 1.0
	return clampf(1.0 - fuse_left / fuse, 0.0, 1.0)


func contains_feet(point: Vector2) -> bool:
	var d := point - global_position
	return (d.x * d.x) / (radii.x * radii.x) + (d.y * d.y) / (radii.y * radii.y) <= 1.0


func _physics_process(delta: float) -> void:
	clock += delta
	phase_clock += delta
	match phase:
		Phase.PENDING:
			_show_mark()
			_ramp_rumble()
		Phase.SCHEDULED:
			fuse_left -= delta
			if stage < 3 and fuse_left <= zone.ring_lead:
				_rush()
			_show_mark()
			_ramp_rumble()
			if fuse_left <= 0.0:
				_erupt()
		Phase.ERUPTING:
			var frame := int(phase_clock / burst_spec.frame_time)
			if frame >= burst.hframes:
				queue_free()
				return
			burst.frame = frame
			_resolve(frame)
		Phase.FIZZLING:
			# The mark's, not the zone's: the zone's would fade the mask as well, and the mark twice over.
			mark.modulate.a = 1.0 - minf(phase_clock / zone.fizzle_time, 1.0)
			if phase_clock >= zone.fizzle_time:
				queue_free()


func _rush() -> void:
	stage = 3
	ring_after = phase_clock
	ParryTell.telegraph(self, ERUPTION_ID, fuse_left + zone.ring_slack, ring_anchor)


# Never past the top rope, nor up into his HUD block over the middle of the ring (which is drawn over it): a zone
# planted that high has its ring held just under them instead.
func ring_anchor() -> Vector2:
	var at := global_position - Vector2(0.0, RING_LIFT)
	var top: float = zone.mark_clip.position.y
	if is_instance_valid(body):
		var hud: Rect2 = body.state_machine.HUD_FADE_RECT
		if at.x >= hud.position.x and at.x <= hud.end.x:
			top = maxf(top, hud.end.y)
	at.y = maxf(at.y, top + RING_TOP)
	return at


func _erupt() -> void:
	erupt_after = phase_clock
	ParryTell.clear(self)
	_stop_rumble()
	phase = Phase.ERUPTING
	phase_clock = 0.0
	mark.hide()
	burst.show()
	burst.frame = 0
	if is_instance_valid(body):
		body.play_sfx(&"eruption_blast")
	erupted.emit()
	_resolve(0)


# Once, on the first hurt frame the feet are inside, whatever the answer but the i-frames' IGNORED, which asks
# again on the next step. The ghost alone inside is a near miss, which PlayerDefense pays once.
func _resolve(frame: int) -> void:
	if answered_once or not is_instance_valid(player) or not (frame in burst_spec.hurt_frames):
		return
	if contains_feet(_feet_of(player.hurtBox)):
		var got: int = player.receive_hit(_hit())
		if got != HitInfo.Result.IGNORED:
			answered_once = true
			result = got
			answered.emit(got)
		return
	if player.dodge_ghost_position() != Vector2.INF and contains_feet(_feet_of(player.dodge_ghost)):
		player.receive_near_miss(_hit())


func _hit() -> RefCounted:
	var centre: Vector2 = player.hurtBox.get_node("CollisionShape2D").global_position
	return HitInfo.make(ERUPTION_ID, self, centre, body)


# The bottom middle of an area's box: the player's feet, or where they were when the dash began.
static func _feet_of(area: Area2D) -> Vector2:
	var shape: CollisionShape2D = area.get_node("CollisionShape2D")
	var box: Rect2 = shape.global_transform * shape.shape.get_rect()
	return Vector2(box.get_center().x, box.end.y)


func _ramp_rumble() -> void:
	if not is_instance_valid(rumble):
		return
	# Only the zones going off soonest rumble (GreysonStateMachine.rumbles). The rest keep their place in the loop,
	# paused, until they are among them.
	var quiet: bool = is_instance_valid(body) and body.state_machine.has_method("rumbles") and not body.state_machine.rumbles(self)
	if rumble.stream_paused != quiet:
		rumble.stream_paused = quiet
	var p := fuse_progress()
	rumble.volume_db = rumble.get_meta(&"base_db") + lerpf(RUMBLE_DB.x, RUMBLE_DB.y, p)
	rumble.pitch_scale = rumble.get_meta(&"base_pitch") * lerpf(RUMBLE_PITCH.x, RUMBLE_PITCH.y, p)


func _stop_rumble() -> void:
	if is_instance_valid(rumble):
		rumble.stop()


#WHAT IS DRAWN

func _sheet(spec: Dictionary, under: Node2D) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(spec.texture)
	sprite.hframes = spec.hframes
	sprite.offset = spec.offset
	sprite.scale = Vector2.ONE * Layout.SCALE
	under.add_child(sprite)
	return sprite


# Draws nothing itself, and cuts whatever is put under it to `area` (global px). A zone never moves once planted.
func _mask(area: Rect2) -> Polygon2D:
	var mask := Polygon2D.new()
	var from := to_local(area.position)
	var to := to_local(area.end)
	mask.polygon = PackedVector2Array([from, Vector2(to.x, from.y), to, Vector2(from.x, to.y)])
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	add_child(mask)
	return mask


# Planted, then the current stage's pair.
func _show_mark() -> void:
	var planted: Array = mark_spec.planted
	var planted_time: float = mark_spec.planted_time
	var opened := planted.size() * planted_time
	if clock < opened:
		mark.frame = planted[int(clock / planted_time)]
		return
	var pair: Array = mark_spec.stages[stage - 1]
	var beat: float = mark_spec.stage_times[stage - 1]
	mark.frame = pair[int((clock - opened) / beat) % pair.size()]
