extends Node2D

# A crack one of beast Bixby's pounds plants in the floor, where the player was standing when it landed.
# It splits open and throbs while it warns, then erupts and throws up a crest of broken ground that rolls
# the way he pounded it. The eruption and every tile of the crest hurt whoever is standing on them. Its
# timing all runs in _physics_process, so a freeze holds it.

const CombinedLayout := preload("res://Scripts/BixbyCombinedArtLayout.gd")
const HitInfo := preload("res://Scripts/HitInfo.gd")
const BURST_SCENE := preload("res://Scenes/Bosses/BixbyQuakeBurstScene.tscn")
const WAVE_SCENE := preload("res://Scenes/Bosses/BixbyQuakeWaveScene.tscn")

# How far out of the ropes a wave still hurts, so hugging a rope is no safer than the rest of the floor.
const WAVE_AREA := Rect2(105, 105, 1710, 870)

enum Phase { MARK, WAVE }

# Set by the attack before the crack enters the tree.
var warning_time := 1.2
var speed := 700.0
var direction := Vector2.DOWN

var phase := Phase.MARK
var clock := 0.0
# How many throbs into the fuse it is, which the beat tightening makes uneven.
var throbs := 0.0
# How long after the eruption starts the wave tears out of it.
var wave_delay := 0.0
var burst: Area2D
var burst_hurts := false
# The tiles of the wave's crest, and each one's place across it, which it keeps the whole way out.
var tiles: Array[Area2D] = []
var offsets: Array[Vector2] = []

@onready var crack: Sprite2D = $Crack
@onready var erupt_sfx: AudioStreamPlayer = $EruptSfx


func _ready() -> void:
	CombinedLayout.dress(crack, CombinedLayout.CRACK_SHEET, CombinedLayout.CRACK_FRAME_SIZE,
		CombinedLayout.CRACK_OFFSET)
	direction = direction.normalized()
	for frame in CombinedLayout.BURST_WAVE_FRAME:
		wave_delay += CombinedLayout.BURST_TIMES[frame]


func _physics_process(delta: float) -> void:
	clock += delta
	if phase == Phase.MARK:
		_warn(delta)
		if clock >= warning_time:
			_erupt()
	else:
		_advance()


# The crack splits open, then throbs until it goes off, its beat tightening over the last of the fuse.
func _warn(delta: float) -> void:
	var opening: float = CombinedLayout.CRACK_OPEN_TIMES[0] + CombinedLayout.CRACK_OPEN_TIMES[1]
	if clock < CombinedLayout.CRACK_OPEN_TIMES[0]:
		crack.frame = 0
		return
	if clock < opening:
		crack.frame = 1
		return
	var beat_time: float = CombinedLayout.CRACK_THROB_TIME
	if warning_time - clock < CombinedLayout.CRACK_RUSH_TIME:
		beat_time = CombinedLayout.CRACK_RUSH_THROB_TIME
	throbs += delta / beat_time
	var throb: Array = CombinedLayout.CRACK_THROB_FRAMES
	crack.frame = throb[int(throbs) % throb.size()]


func _erupt() -> void:
	phase = Phase.WAVE
	clock = 0.0
	crack.hide()
	erupt_sfx.play()
	burst = _hazard(BURST_SCENE, CombinedLayout.BURST_SHEET, CombinedLayout.BURST_FRAME_SIZE,
		CombinedLayout.BURST_OFFSET, CombinedLayout.BURST_HIT_SIZE)
	# Before it enters the tree, so the first frame's puff of dust can't hurt anyone.
	(burst.get_node("CollisionShape2D") as CollisionShape2D).disabled = true
	add_child(burst)
	_show_burst()


# The eruption plays out where the crack was, and the crest it throws up rolls on across the floor at a
# steady speed. A tile that has left the floor stops hurting, and once they all have, the crack is done.
func _advance() -> void:
	_show_burst()
	var rolled := clock - wave_delay
	if rolled < 0.0:
		return
	if tiles.is_empty():
		_break_ground()

	var travelled := direction * speed * rolled
	# Each tile a frame further on than the one beside it, so the crest runs along the whole ridge.
	var beat := int(rolled / CombinedLayout.WAVE_FRAME_TIME)
	var live := false
	for i in tiles.size():
		var tile := tiles[i]
		tile.position = (offsets[i] + travelled).round()
		var inside := WAVE_AREA.has_point(tile.global_position)
		live = live or inside
		if tile.visible != inside:
			tile.visible = inside
			# Deferred: this runs inside a physics flush.
			tile.get_node("CollisionShape2D").set_deferred("disabled", not inside)
		var sprite: Sprite2D = tile.get_node("Sprite2D")
		sprite.frame = (beat + i) % sprite.hframes

	if not live and burst == null:
		queue_free()


func _show_burst() -> void:
	if burst == null:
		return
	var frame := _burst_frame(clock)
	if frame < 0:
		burst.queue_free()
		burst = null
		return
	burst.get_node("Sprite2D").frame = frame
	var hurts := frame >= CombinedLayout.BURST_HIT_FIRST_FRAME and frame <= CombinedLayout.BURST_HIT_LAST_FRAME
	if hurts != burst_hurts:
		burst_hurts = hurts
		# Deferred: this runs inside a physics flush.
		burst.get_node("CollisionShape2D").set_deferred("disabled", not hurts)


# Which frame of the eruption is showing `at` seconds in, or -1 once it is over.
func _burst_frame(at: float) -> int:
	var total := 0.0
	for frame in CombinedLayout.BURST_TIMES.size():
		total += CombinedLayout.BURST_TIMES[frame]
		if at < total:
			return frame
	return -1


# The crest, laid across the way it travels with its tiles exactly a frame apart.
func _break_ground() -> void:
	var across := direction.orthogonal()
	for i in CombinedLayout.WAVE_TILES:
		var tile := _hazard(WAVE_SCENE, CombinedLayout.WAVE_SHEET, CombinedLayout.WAVE_FRAME_SIZE,
			CombinedLayout.WAVE_OFFSET, CombinedLayout.WAVE_HIT_SIZE)
		var offset := across * (i - (CombinedLayout.WAVE_TILES - 1) / 2.0) * CombinedLayout.WAVE_SPACING
		tile.position = offset.round()
		offsets.append(offset)
		tiles.append(tile)
		add_child(tile)


func _hazard(scene: PackedScene, sheet: Texture2D, frame_size: Vector2, offset: Vector2, hit_size: Vector2) -> Area2D:
	var hazard: Area2D = scene.instantiate()
	hazard.set_meta(HitInfo.META_ATTACK, &"bixby_quake_burst")
	CombinedLayout.dress(hazard.get_node("Sprite2D"), sheet, frame_size, offset)
	var shape: CollisionShape2D = hazard.get_node("CollisionShape2D")
	(shape.shape as RectangleShape2D).size = hit_size
	return hazard
