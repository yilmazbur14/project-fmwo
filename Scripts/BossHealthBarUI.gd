extends Control

# The boss health block: one bar per body, a nameplate, and the feedback a hit earns. Every fight
# builds it with BossHealthBarUI.create() and then only ever talks to it through set_value() and its
# friends, so there is one boss HUD in the game rather than one per boss script.
#
# It runs on real seconds throughout - node-bound tweens that ignore the time scale, and a _process
# clock divided by it - so a drain plays out through a hit-stop instead of crawling. The component
# lives under the boss, which is the branch FightFreeze disables, so a finisher correctly stalls the
# bar mid-drain and it lands the damage on the unfreeze.
#
# BossBarArtLayout owns every number. With USE_FINAL_BOSS_BAR off - and for a block with a row whose
# boss has no drawn fill, whatever the flag says - the placeholder branch draws the exact
# ProgressBar-and-Label block each boss script used to build inline: same rects, same corner radius,
# same colour ladder, same 0.2 s ease. Both branches can be reached in the same build, so a block
# holds the chrome it was built with instead of asking the flag again.

const BossBarArtLayout := preload("res://Scripts/BossBarArtLayout.gd")
const HudPlayerFade := preload("res://Scripts/HudPlayerFade.gd")
const THEME := "res://Assets/UI/ui_theme.tres"

# What kind of hit a set_value() is reporting. HIT_SILENT is a correction rather than damage - a
# phase floor being applied, or the bar being put back in step - and plays nothing.
const HIT_NORMAL := 0
const HIT_PUNISH := 1
const HIT_SILENT := 2

# Emitted when a row's drain actually reaches empty, so a fight can sequence off the visual rather
# than off a guessed delay.
signal row_emptied(row: int)

# Set by create() before the component is added.
var block_anchor := BossBarArtLayout.BLOCK_ANCHOR
var plate_key: StringName = &""
var label_text := ""
var row_specs: Array = []

var rows: Array[Dictionary] = []
var clock := 0.0
# The chrome this block was built with, not whatever the flag says now.
var chrome: Dictionary = BossBarArtLayout.PLACEHOLDER_BAR


static func create(config: Dictionary) -> Control:
	var ui := new()
	ui.block_anchor = config.get("anchor", BossBarArtLayout.BLOCK_ANCHOR)
	ui.plate_key = config.get("plate", &"")
	ui.label_text = config.get("text", "")
	ui.row_specs = config.get("rows", [])
	return ui


func _ready() -> void:
	position = block_anchor
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var drawn := BossBarArtLayout.USE_FINAL_BOSS_BAR and _all_rows_drawn()
	chrome = BossBarArtLayout.bar(drawn)
	if drawn:
		_build_final()
	else:
		_build_placeholder()
	HudPlayerFade.wrap(self)


# A row whose boss has no drawn fill - the legacy Carter & Josh pair the split superseded - keeps the
# flat bar whatever the flag says.
func _all_rows_drawn() -> bool:
	for spec in row_specs:
		if not BossBarArtLayout.boss_bar(spec.get("key", &"")).has("fill"):
			return false
	return true


# Loops only: a frame where the time scale changed shifts their phase and nothing more.
func _process(delta: float) -> void:
	clock += delta / maxf(Engine.time_scale, 0.001)
	for row in rows:
		if row.has("beat"):
			_step_beat(row)
		if row.has("low"):
			_step_low(row)


#THE FIGHT'S SIDE

# The hit lands on the bar the frame it lands on the boss: the drawn fill snaps and the chip trail
# behind it is what animates. `flags` says what kind of hit it was, for the feedback the art plays.
func set_value(row: int, value: float, flags: int = HIT_NORMAL) -> void:
	if not _has(row):
		return
	var spec := rows[row]
	var lost: float = spec.value - clampf(value, 0.0, spec.max)
	spec.value = clampf(value, 0.0, spec.max)
	_refresh_fill(row)
	if spec.has("bar"):
		_drain(row, chrome.drain_time)
		return
	_snap_fill(row)
	if flags & HIT_SILENT != 0 or lost <= 0.0:
		_kill_drain(spec)
		spec.chip.value = spec.fill.value
		_on_drained(row)
		return
	_play_chip(row, flags)
	_play_hit(row, lost, flags)


func set_max(row: int, max_value: float) -> void:
	if not _has(row):
		return
	var spec := rows[row]
	spec.max = maxf(max_value, 1.0)
	spec.value = clampf(spec.value, 0.0, spec.max)
	if spec.has("bar"):
		spec.bar.max_value = spec.max
		spec.bar.value = spec.value
	else:
		_snap_fill(row)
		spec.chip.value = spec.fill.value
	_refresh_fill(row)


# The other body's ratio, marked across this row: the gap between the fill's edge and the marker is
# the imbalance a two-body fight is about.
func set_ghost(row: int, ratio: float, shown: bool) -> void:
	if not _has(row):
		return
	var spec := rows[row]
	# Same latch as _refresh_fill: a finished row's marker stays gone, whatever the fight asks for.
	if spec.finished:
		spec.ghost.hide()
		return
	var width: float = spec.ghost_width
	spec.ghost.position.x = spec.ghost_left + clampf(ratio * spec.ghost_span - width / 2.0,
		0.0, spec.ghost_span - width)
	spec.ghost.visible = shown


# A row changing whose bar it is mid-fight: Bixby swallowing Liam.
func set_accent(row: int, key: StringName) -> void:
	if not _has(row):
		return
	var spec := rows[row]
	spec.key = key
	var boss := BossBarArtLayout.boss_bar(key)
	if spec.has("fill") and boss.has("fill"):
		spec.fill.texture_progress = load(boss.fill)
		spec.hot.texture_progress = load(boss.fill_hot)
		if spec.has("emblem") and boss.has("emblem"):
			spec.emblem.texture = load(boss.emblem)
	_refresh_fill(row)


# How far this row is blended toward its hot fill: a rage chain, a surge, a phase two's power.
func set_heat(row: int, amount: float) -> void:
	if not _has(row):
		return
	rows[row].heat = clampf(amount, 0.0, 1.0)
	_refresh_fill(row)


# How hard the row beats while it is the one being neglected. Separate from the heat, because a bar
# can be hot without being the one the player is being warned about.
func set_beat(row: int, amount: float) -> void:
	if not _has(row) or not rows[row].has("beat"):
		return
	var spec := rows[row]
	spec.beat_amount = clampf(amount, 0.0, 1.0)
	if spec.beat_amount <= 0.0:
		spec.node.modulate.a = 1.0


# This body is out: drain what is left, then leave the row dead. It deliberately does not latch - a
# later set_value or set_heat on the row is honoured, which is what the two-body fight already did.
func finish_row(row: int) -> void:
	if not _has(row):
		return
	var spec := rows[row]
	spec.value = 0.0
	if spec.has("fill"):
		_snap_fill(row)
	_drain(row, chrome.drain_time)
	if spec.has("fill_style"):
		spec.fill_style.bg_color = BossBarArtLayout.DEAD_FILL
	spec.node.modulate = BossBarArtLayout.DEAD_DIM
	# Latch last, so the drain and the grey above still run, and only later refreshes are refused.
	spec.finished = true
	spec.ghost.hide()


# A new phase filling the row back up, with the sweep over it once the art is in.
func refill_row(row: int, to: float, time: float) -> void:
	if not _has(row):
		return
	var spec := rows[row]
	# A new phase brings the row back to life, so the latch lifts before anything repaints it.
	spec.finished = false
	spec.value = clampf(to, 0.0, spec.max)
	spec.node.modulate = Color.WHITE
	_drain(row, time)
	_refresh_fill(row)
	if spec.has("sweep"):
		_play_sheet(spec.sweep, chrome.sweep_frame_time)


# Where Eric's Break gauge hangs off this block.
func break_gauge_anchor() -> Vector2:
	return block_anchor + chrome.break_gauge_offset


#DRAWING

func _has(row: int) -> bool:
	return row >= 0 and row < rows.size()


func _refresh_fill(row: int) -> void:
	var spec := rows[row]
	# A spent row stays spent. The fights keep refreshing every row after one of them is finished -
	# Greyson's pair refreshes both bodies on any change - and without this the dead bar gets its
	# live colour painted back over the grey.
	if spec.finished:
		return
	var ratio: float = spec.value / spec.max
	if spec.has("fill_style"):
		spec.fill_style.bg_color = BossBarArtLayout.heat_color(spec.key, spec.heat, ratio)
		return
	spec.hot.modulate.a = spec.heat
	var low: bool = ratio <= BossBarArtLayout.LOW_RATIO
	spec.low.visible = low
	spec.over.visible = not low
	spec.over_low.visible = low
	spec.crest.visible = not low
	spec.crest_low.visible = low


# Whole texels of the art's own window, so the drawn fill steps a texel at a time rather than
# sliding a fraction of one.
func _texels(row: int) -> float:
	var spec := rows[row]
	return roundf(spec.value / spec.max * chrome.fill_texels)


func _snap_fill(row: int) -> void:
	var spec := rows[row]
	spec.fill.value = _texels(row)
	spec.hot.value = spec.fill.value


func _kill_drain(spec: Dictionary) -> void:
	if spec.drain:
		spec.drain.kill()
		spec.drain = null


# Everything on the row moving together: the ease a phase handoff or a row going out runs on.
func _drain(row: int, time: float) -> void:
	var spec := rows[row]
	_kill_drain(spec)
	if spec.has("bar"):
		spec.drain = spec.bar.create_tween().set_ignore_time_scale(true)
		spec.drain.tween_property(spec.bar, "value", spec.value, time)
	else:
		var to := _texels(row)
		spec.drain = spec.chip.create_tween().set_ignore_time_scale(true).set_parallel(true)
		for part in ["chip", "fill", "hot"]:
			spec.drain.tween_property(spec[part], "value", to, time)
		spec.drain.chain()
	spec.drain.tween_callback(_on_drained.bind(row))


# The pale trail the fill left behind: it holds, so the size of the hit reads, then runs out.
func _play_chip(row: int, flags: int) -> void:
	var spec := rows[row]
	_kill_drain(spec)
	var hold: float = BossBarArtLayout.PUNISH_CHIP_HOLD if flags & HIT_PUNISH != 0 else BossBarArtLayout.CHIP_HOLD
	spec.drain = spec.chip.create_tween().set_ignore_time_scale(true)
	spec.drain.tween_interval(hold)
	spec.drain.tween_property(spec.chip, "value", spec.fill.value,
		BossBarArtLayout.CHIP_DRAIN).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	spec.drain.tween_callback(_on_drained.bind(row))
	if flags & HIT_PUNISH != 0:
		spec.spark.position = (spec.fill_edge - chrome.spark_pivot
			+ Vector2(spec.fill.value * chrome.fill_step, 0.0))
		_play_sheet(spec.spark, chrome.spark_frame_time)


func _play_hit(row: int, damage: float, flags: int) -> void:
	var spec := rows[row]
	var punish: bool = flags & HIT_PUNISH != 0
	spec.flash.texture = load(chrome.flash_punish if punish else chrome.flash)
	spec.flash.modulate.a = chrome.flash_alpha
	spec.flash.show()
	if spec.flash_tween:
		spec.flash_tween.kill()
	spec.flash_tween = spec.flash.create_tween().set_ignore_time_scale(true)
	spec.flash_tween.tween_property(spec.flash, "modulate:a", 0.0, BossBarArtLayout.FLASH_TIME)
	spec.flash_tween.tween_callback(spec.flash.hide)

	var strength := BossBarArtLayout.SHAKE_PX * clampf(damage / spec.max, 0.0, 1.0)
	_shake(row, strength * BossBarArtLayout.PUNISH_SHAKE_MULT if punish else strength)


func _shake(row: int, strength: float) -> void:
	var spec := rows[row]
	if spec.shake_tween:
		spec.shake_tween.kill()
	var holder: Control = spec.node
	var home: Vector2 = spec.rect.position
	var steps := BossBarArtLayout.SHAKE_STEPS
	spec.shake_tween = holder.create_tween().set_ignore_time_scale(true)
	for i in steps:
		var offset := Vector2(randf_range(-strength, strength), randf_range(-strength, strength)).round()
		spec.shake_tween.tween_callback(func() -> void: holder.position = home + offset)
		spec.shake_tween.tween_interval(BossBarArtLayout.SHAKE_TIME / steps)
	spec.shake_tween.tween_callback(func() -> void: holder.position = home)


func _on_drained(row: int) -> void:
	if rows[row].value <= 0.0:
		row_emptied.emit(row)


func _play_sheet(sheet: Sprite2D, frame_time: float) -> void:
	sheet.frame = 0
	sheet.show()
	var play := sheet.create_tween().set_ignore_time_scale(true)
	for i in range(1, sheet.hframes):
		play.tween_interval(frame_time)
		play.tween_callback(sheet.set_frame.bind(i))
	play.tween_interval(frame_time)
	play.tween_callback(sheet.hide)


func _step_beat(row: Dictionary) -> void:
	if row.beat_amount <= 0.0:
		return
	# Typed explicitly: the period comes out of an untyped Dictionary, so inferring from it leaves
	# the parser resolving a Variant and it can refuse depending on the order scripts are read.
	var period: float = row.beat.time
	var alpha: float = row.beat.alpha
	var beat: float = absf(sin(clock * PI / period))
	row.node.modulate.a = lerpf(1.0, 1.0 - alpha * row.beat_amount, beat)


func _step_low(row: Dictionary) -> void:
	if not row.low.visible:
		return
	row.low.frame = int(clock / chrome.low_frame_time) % chrome.low_hframes


#BUILDING

# The block each boss script drew before this component existed, rebuilt here once: a name, an
# optional panel and bracket for a pair, and a flat ProgressBar per row.
func _build_placeholder() -> void:
	var art := chrome
	var block := BossBarArtLayout.block(plate_key)
	size = block.size

	if block.has("panel"):
		var panel := Panel.new()
		panel.position = block.panel.position
		panel.size = block.panel.size
		panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var frame := StyleBoxFlat.new()
		frame.bg_color = block.panel_bg
		frame.set_corner_radius_all(block.panel_corner_radius)
		frame.set_border_width_all(block.panel_border)
		frame.border_color = block.panel_border_color
		panel.add_theme_stylebox_override("panel", frame)
		add_child(panel)

	add_child(_label(label_text, block.name_offset, block.name_font_size, block.name_outline, Color(1, 1, 1)))

	if block.has("bracket"):
		var bracket := ColorRect.new()
		bracket.color = block.bracket_color
		bracket.position = block.bracket.position
		bracket.size = block.bracket.size
		bracket.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(bracket)

	for i in row_specs.size():
		var rect: Rect2 = block.rows[i]
		var key: StringName = row_specs[i].get("key", &"")
		if block.has("row_labels"):
			add_child(_label(block.row_labels[i], block.row_label_offsets[i],
				block.row_label_font_size, block.row_label_outline,
				BossBarArtLayout.boss_bar(key).heat_ramp[0]))

		var holder := Control.new()
		holder.position = rect.position
		holder.size = rect.size
		holder.mouse_filter = Control.MOUSE_FILTER_IGNORE

		var bar := ProgressBar.new()
		bar.min_value = 0
		bar.max_value = row_specs[i].get("max", 1)
		bar.value = row_specs[i].get("value", bar.max_value)
		bar.show_percentage = false
		bar.size = rect.size
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var background := StyleBoxFlat.new()
		background.bg_color = art.bg_color
		background.set_corner_radius_all(art.corner_radius)
		background.set_border_width_all(art.border)
		background.border_color = art.border_color
		bar.add_theme_stylebox_override("background", background)
		var fill_style := StyleBoxFlat.new()
		fill_style.set_corner_radius_all(art.corner_radius)
		bar.add_theme_stylebox_override("fill", fill_style)
		holder.add_child(bar)

		# On the bar rather than beside it, so it is drawn over the fill it is measuring against.
		var ghost := ColorRect.new()
		ghost.color = art.ghost_color
		ghost.size = Vector2(art.ghost_width, rect.size.y)
		ghost.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ghost.hide()
		bar.add_child(ghost)

		add_child(holder)
		var row := {
			"key": key,
			"max": float(bar.max_value),
			"value": float(bar.value),
			"heat": 0.0,
			# Latched once the row is spent, so nothing repaints a dead bar or brings its ghost tick back.
			"finished": false,
			"rect": rect,
			"node": holder,
			"bar": bar,
			"fill_style": fill_style,
			"ghost": ghost,
			"ghost_width": art.ghost_width,
			"ghost_left": 0.0,
			"ghost_span": rect.size.x,
			"drain": null,
			"shake_tween": null,
		}
		if block.has("heat_pulse"):
			row["beat"] = block.heat_pulse
			row["beat_amount"] = 0.0
		rows.append(row)
		_refresh_fill(i)


# The drawn block: one frame under the fills, one over them carrying the notches, and the per-boss
# fill between. Everything the feedback plays sits on the fill's own window.
func _build_final() -> void:
	var art := chrome
	size = Vector2(art.size.x, art.size.y + BossBarArtLayout.ROW_PITCH * (row_specs.size() - 1))

	for i in row_specs.size():
		var rect := Rect2(Vector2(0, BossBarArtLayout.ROW_PITCH * i), art.size)
		var key: StringName = row_specs[i].get("key", &"")
		var boss := BossBarArtLayout.boss_bar(key)

		var holder := Control.new()
		holder.position = rect.position
		holder.size = rect.size
		holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(_sheet(art.frame_back, 1, Vector2.ZERO))

		var chip := _texel_bar(art.chip, art.fill_offset, art.fill_texels)
		var fill := _texel_bar(boss.fill, art.fill_offset, art.fill_texels)
		var hot := _texel_bar(boss.fill_hot, art.fill_offset, art.fill_texels)
		hot.modulate.a = 0.0
		for part in [chip, fill, hot]:
			holder.add_child(part)

		var low := _sheet(art.low, art.low_hframes, art.fill_offset)
		var flash := _sheet(art.flash, 1, art.fill_offset)
		var over := _sheet(art.frame_over, 1, Vector2.ZERO)
		var over_low := _sheet(art.frame_over_low, 1, Vector2.ZERO)
		# Over the chrome, so the crest breaks both rails the way it is drawn; under the feedback, which
		# is the only thing allowed to play on top of it.
		var crest := _sheet(art.crest, 1, art.crest_offset)
		var crest_low := _sheet(art.crest_low, 1, art.crest_offset)
		var sweep := _sheet(art.sweep, art.sweep_hframes, art.fill_offset)
		var spark := _sheet(art.spark, art.spark_hframes, art.fill_offset)
		var ghost := _sheet(art.ghost, 1, art.fill_offset)
		for part in [low, flash, over, over_low, crest, crest_low, sweep, spark, ghost]:
			holder.add_child(part)
		for part in [flash, sweep, spark, ghost]:
			part.hide()

		add_child(holder)
		var row := {
			"key": key,
			"max": maxf(float(row_specs[i].get("max", 1)), 1.0),
			"value": float(row_specs[i].get("value", row_specs[i].get("max", 1))),
			"heat": 0.0,
			# Latched once the row is spent, so nothing repaints a dead bar or brings its ghost tick back.
			"finished": false,
			"rect": rect,
			"node": holder,
			"chip": chip,
			"fill": fill,
			"hot": hot,
			"low": low,
			"flash": flash,
			"over": over,
			"over_low": over_low,
			"crest": crest,
			"crest_low": crest_low,
			"sweep": sweep,
			"spark": spark,
			"ghost": ghost,
			"ghost_width": art.ghost_width,
			"ghost_left": art.fill_offset.x,
			"ghost_span": BossBarArtLayout.FILL_SIZE.x,
			"fill_edge": art.fill_offset,
			"drain": null,
			"flash_tween": null,
			"shake_tween": null,
		}
		rows.append(row)
		_snap_fill(i)
		chip.value = fill.value
		_refresh_fill(i)

	_build_plate()


# ONE plate for the block, however many rows it carries: a pair's bake already says both names, and
# giving row 1 a plate of its own puts a COMPUTAH plate straight across Greyson's fill. It rides above
# the crest. Its lettering is baked with the VS card's, so the HUD and the card say the boss's name in
# exactly the same hand; a plate with no baked name keeps the Label.
func _build_plate() -> void:
	var pair := BossBarArtLayout.plate_is_pair(plate_key)
	var at: Vector2 = BossBarArtLayout.PLATE_TALL_OFFSET if pair else BossBarArtLayout.PLATE_OFFSET
	var plate_size: Vector2 = BossBarArtLayout.PLATE_TALL_SIZE if pair else BossBarArtLayout.PLATE_SIZE
	add_child(_sheet(chrome.plate_tall if pair else chrome.plate, 1, at))
	var key: StringName = rows[0].key if not rows.is_empty() else &""
	var boss := BossBarArtLayout.boss_bar(key)
	if boss.has("emblem"):
		var emblem := _sheet(boss.emblem, 1, at + BossBarArtLayout.PLATE_EMBLEM_OFFSET)
		add_child(emblem)
		if not rows.is_empty():
			rows[0]["emblem"] = emblem
	var baked := BossBarArtLayout.plate_name(plate_key)
	if baked == "":
		var block := BossBarArtLayout.block(plate_key)
		add_child(_label(label_text, block.name_offset, block.name_font_size,
			block.name_outline, Color(1, 1, 1)))
		return
	var lettering := load(baked) as Texture2D
	var name_sheet := Sprite2D.new()
	name_sheet.texture = lettering
	name_sheet.centered = false
	name_sheet.position = at + Vector2(BossBarArtLayout.PLATE_NAME_LEFT, 0.0) + _texel_centre(
		Vector2(BossBarArtLayout.PLATE_NAME_WIDTH, plate_size.y) - lettering.get_size())
	add_child(name_sheet)


# Half of a gap, floored onto the art's own 3 px texel grid. The baked lettering has to land on the
# same grid as the plate under it, or its pixels sit a third of a texel off the plate's.
func _texel_centre(gap: Vector2) -> Vector2:
	return (gap / 6.0).floor() * 3.0


func _label(text: String, at: Vector2, font_size: int, outline: int, tint: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.position = at
	label.theme = load(THEME)
	if font_size > 0:
		label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", tint)
	label.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	label.add_theme_constant_override("outline_size", outline)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _sheet(path: String, hframes: int, at: Vector2) -> Sprite2D:
	var sheet := Sprite2D.new()
	sheet.texture = load(path)
	sheet.hframes = hframes
	sheet.centered = false
	sheet.position = at
	return sheet


func _texel_bar(path: String, at: Vector2, texels: int) -> TextureProgressBar:
	var bar := TextureProgressBar.new()
	bar.texture_progress = load(path)
	bar.texture_progress_offset = at
	bar.fill_mode = TextureProgressBar.FILL_LEFT_TO_RIGHT
	bar.min_value = 0.0
	bar.max_value = texels
	bar.step = 1.0
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return bar
