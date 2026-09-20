extends Control

# The player's health containers: three hearts, six halves. PlayerScript calls update_health() every
# time the number changes, and nothing else talks to this.
#
# PlayerHealthArtLayout owns every number, and both looks run through the same code here, so turning
# USE_FINAL_PLAYER_HP off brings the old row back. The row is built in code rather than laid out in
# the scene because the drawn tray places its hearts freely and a container would fight it; the row
# node carries the player_health_hud group, which is how the dialogue box knows to move off it.
#
# It lives under MainPlayer, which is the branch FightFreeze keeps running, so its feedback plays out
# through a finisher. Its tweens ignore the time scale and its clock is divided by it, so a hit-stop
# doesn't stretch a heart breaking.

const PlayerHealthArtLayout := preload("res://Scripts/PlayerHealthArtLayout.gd")

## While a node in this group is visible, the dialogue box moves to its right (Scripts/balloon.gd).
const HUD_GROUP: StringName = &"player_health_hud"

var row: Control
var containers: Array[TextureRect] = []
# Drawn art only: the tray behind the hearts, its warning rim, and a sheet per container.
var tray: Sprite2D
var tray_warn: Sprite2D
var breaks: Array[Sprite2D] = []
var gains: Array[Sprite2D] = []
var lows: Array[Sprite2D] = []
var tray_tween: Tween
var tray_shake: Tween

var health := PlayerHealthArtLayout.CONTAINERS * 2
var clock := 0.0
# First frame of the beat's run on the sheet: the whole-heart pair or the half's.
var low_run := 0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	_refresh()


# Loops only, so a frame where the time scale changed shifts their phase and nothing more.
func _process(delta: float) -> void:
	if lows.is_empty():
		return
	clock += delta / maxf(Engine.time_scale, 0.001)
	_step_loops()


# Also called the moment the health changes, not only on the next frame: the run the beat is on moves
# with it, and a frame of a whole heart left over a container that just dropped to its last half is
# the one thing this sheet has four frames to avoid.
func _step_loops() -> void:
	var spec := PlayerHealthArtLayout.hearts()
	var beat: int = int(clock / PlayerHealthArtLayout.LOW_FRAME_TIME) % int(spec.low_beat_frames)
	for low in lows:
		low.frame = low_run + beat
	tray_warn.frame = int(clock / PlayerHealthArtLayout.WARN_FRAME_TIME) % int(spec.tray_warn_hframes)


# Half-hearts, 0 to 6. The containers fill left to right: whole ones first, then the odd half.
func update_health(current_health: int) -> void:
	var before := health
	health = clampi(current_health, 0, PlayerHealthArtLayout.CONTAINERS * 2)
	_refresh()
	if breaks.is_empty() or health == before:
		return
	for i in containers.size():
		if _halves(i, before) > 0 and _halves(i, health) == 0:
			_play(breaks[i], PlayerHealthArtLayout.BREAK_FRAME_TIME)
		elif _halves(i, before) == 0 and _halves(i, health) > 0:
			_play(gains[i], PlayerHealthArtLayout.GAIN_FRAME_TIME)
	if health < before:
		_flash_tray(PlayerHealthArtLayout.TRAY_FLASH)
		_shake_tray()
	else:
		_flash_tray(PlayerHealthArtLayout.TRAY_GAIN_FLASH)


func _halves(container: int, total: int) -> int:
	return clampi(total - container * 2, 0, 2)


func _refresh() -> void:
	var spec := PlayerHealthArtLayout.hearts()
	for i in containers.size():
		var halves := _halves(i, health)
		containers[i].texture = load(spec.full if halves == 2 else (spec.half if halves == 1 else spec.empty))
	if lows.is_empty():
		return
	# The last container still holding anything beats while it is the only thing left, on the run of
	# frames drawn for what it is holding.
	var warn := health <= PlayerHealthArtLayout.WARN_AT and health > 0
	var last := maxi(floori((health - 1) / 2.0), 0)
	low_run = 0 if _halves(last, health) == 2 else int(spec.low_half_frame)
	for i in lows.size():
		lows[i].visible = warn and i == last
	tray_warn.visible = warn
	_step_loops()


func _play(sheet: Sprite2D, frame_time: float) -> void:
	sheet.frame = 0
	sheet.show()
	var play := sheet.create_tween().set_ignore_time_scale(true)
	for i in range(1, sheet.hframes):
		play.tween_interval(frame_time)
		play.tween_callback(sheet.set_frame.bind(i))
	play.tween_interval(frame_time)
	play.tween_callback(sheet.hide)


func _flash_tray(tint: Color) -> void:
	if tray_tween:
		tray_tween.kill()
	tray.modulate = tint
	tray_tween = tray.create_tween().set_ignore_time_scale(true)
	tray_tween.tween_property(tray, "modulate", Color.WHITE, PlayerHealthArtLayout.TRAY_FLASH_TIME)


func _shake_tray() -> void:
	if tray_shake:
		tray_shake.kill()
	var home := Vector2.ZERO
	var strength := PlayerHealthArtLayout.TRAY_SHAKE_PX
	var steps := PlayerHealthArtLayout.TRAY_SHAKE_STEPS
	tray_shake = row.create_tween().set_ignore_time_scale(true)
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		tray_shake.tween_callback(func() -> void: row.position = home + offset)
		tray_shake.tween_interval(PlayerHealthArtLayout.TRAY_SHAKE_TIME / steps)
	tray_shake.tween_callback(func() -> void: row.position = home)


func _build() -> void:
	var spec := PlayerHealthArtLayout.hearts()
	var frame := Control.new()
	frame.position = spec.position
	frame.size = spec.size
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_to_group(HUD_GROUP)
	add_child(frame)

	# The shake moves the whole row, so the tray and its hearts stay together inside the frame the
	# dialogue box measures itself against.
	row = Control.new()
	row.size = spec.size
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(row)

	if spec.has("tray"):
		tray = _sheet(spec.tray, 1, Vector2.ZERO)
		tray_warn = _sheet(spec.tray_warn, spec.tray_warn_hframes, Vector2.ZERO)
		tray_warn.hide()
		row.add_child(tray)
		row.add_child(tray_warn)

	for i in PlayerHealthArtLayout.CONTAINERS:
		var at: Vector2 = spec.heart_offsets[i]
		var heart := TextureRect.new()
		heart.position = at
		heart.size = spec.heart_size
		# Free-standing rather than in a container, so the texture never forces the rect's size.
		heart.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		heart.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(heart)
		containers.append(heart)

		if not spec.has("break"):
			continue
		var low := _sheet(spec.low, spec.low_hframes, at)
		low.hide()
		var gain := _sheet(spec.gain, spec.gain_hframes, at)
		gain.hide()
		# Oversized on purpose, so the shatter spills past the container it came out of.
		var shatter := _sheet(spec["break"], spec.break_hframes, at + spec.break_offset)
		shatter.hide()
		for sheet in [low, gain, shatter]:
			row.add_child(sheet)
		lows.append(low)
		gains.append(gain)
		breaks.append(shatter)


func _sheet(path: String, hframes: int, at: Vector2) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(path)
	sheet.hframes = hframes
	sheet.centered = false
	sheet.position = at
	return sheet
