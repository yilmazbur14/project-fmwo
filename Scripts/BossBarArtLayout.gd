extends RefCounted

# Every number the boss health HUD is drawn from: the bar block, the nameplate, the per-boss fill and
# the damage feedback's timing. USE_FINAL_BOSS_BAR picks between the drawn art and the placeholder,
# and both go through the same code in BossHealthBarUI, so turning the flag off brings the old look
# back. HUD art uses the _3x copies at scale 1 on whole screen px, like the stamina and break frames.
#
# The placeholder is not a rough stand-in: it is exactly the ProgressBar-and-Label block each boss
# script built inline before this component existed, down to the corner radius, so landing the
# component changed nothing on screen. Its geometry is written as offsets from BLOCK_ANCHOR, which
# means "anchor" means the same thing in both branches and a fight that moves its block moves the
# whole thing either way.

const USE_FINAL_BOSS_BAR := true

#GEOMETRY
# The block's top-left, centred on x=960: the bar's TOP RAIL, which every offset below is from. The
# drawn block is the taller of the two - its plate rides above the crest instead of lapping the rail,
# and a pair's plate is taller still - so it hangs 40 px lower than the flat one. At the flat block's
# y=60 a pair's plate top lands at -13 and clips off the top of the screen.
const PLACEHOLDER_ANCHOR := Vector2(720, 60)
const FINAL_ANCHOR := Vector2(720, 100)
const BLOCK_ANCHOR := FINAL_ANCHOR if USE_FINAL_BOSS_BAR else PLACEHOLDER_ANCHOR
# The drawn frame, and the window the fills are revealed in, from the frame's top-left.
const FRAME_SIZE := Vector2(480, 54)
const FILL_OFFSET := Vector2(12, 12)
const FILL_SIZE := Vector2(456, 36)
# Whole texels of fill, so it steps a texel at a time rather than sliding.
const FILL_TEXELS := 152
# Stacked pairs (Greyson & Computah, Liam & Bixby) put row 1 this far under row 0: the frame's 54 px
# and 29 of gap, which is more than the 21 the crest stands proud of its rails, so neither row's
# crest can reach into the other's fill window.
const ROW_PITCH := 83.0
# The nameplate rides above the crest rather than lapping the bar's rail. Both are centred on the
# bar, so lapping put the plate exactly where the crest's mask and horns rise and the crest ate the
# name. It laps the crest's topmost tips by 2 px instead, which reads as the horns rising to meet it:
# -(21 of overhang + the plate's height - 2).
const PLATE_SIZE := Vector2(288, 48)
const PLATE_OFFSET := Vector2(96, -67)
# A pair's name bakes as two stacked lines, which only the tall plate holds.
const PLATE_TALL_SIZE := Vector2(288, 78)
const PLATE_TALL_OFFSET := Vector2(96, -97)
# The emblem's slot at the plate's left, from the plate's top-left.
const PLATE_EMBLEM_OFFSET := Vector2(9, 9)
# The baked name is centred in this span across the plate and in the plate's full height, both
# snapped to the art's own 3 px texel grid, which is the placement the plate was baked with.
const PLATE_NAME_LEFT := 48.0
const PLATE_NAME_WIDTH := 228.0

#TIMING
# Real seconds and screen px. The fill snaps on the frame the hit lands - a hit that has to wait for
# an ease to read is a hit the player doesn't feel - and the chip trail behind it is what animates.
const CHIP_HOLD := 0.18
const CHIP_DRAIN := 0.30
const PUNISH_CHIP_HOLD := 0.28
const FLASH_TIME := 0.10
const SHAKE_TIME := 0.12
const SHAKE_PX := 5.0
const SHAKE_STEPS := 4
const PUNISH_SHAKE_MULT := 1.6
# Below this the low-health pulse and the hot rim come on.
const LOW_RATIO := 0.25
# A drain that isn't a hit: a phase handoff, or the row going out.
const DRAIN_TIME := 0.35
# What a finished row is left at.
const DEAD_FILL := Color(0.3, 0.32, 0.36, 1)
const DEAD_DIM := Color(0.6, 0.6, 0.6)

#THE BLOCK
# The chrome every bar shares. The placeholder's numbers are the StyleBoxFlat the boss scripts built;
# the final one's are the three frame sheets.
const PLACEHOLDER_BAR := {
	"bg_color": Color(0.08, 0.08, 0.08, 0.85),
	"corner_radius": 3,
	"border": 2,
	"border_color": Color(0, 0, 0),
	# The ProgressBar's own ease, in real seconds.
	"drain_time": 0.2,
	"ghost_width": 3.0,
	"ghost_color": Color(1, 1, 1, 0.85),
	# Eric's Break gauge sat under his old bar, at the top rope's band.
	"break_gauge_offset": Vector2(48, 33),
}
# `fill_offset` and `fill_texels` are the window inside the frame; the chip trail, the hot fill, the
# low pulse, the flash and the sweep are all that window's size and sit on it.
const FINAL_BAR := {
	"frame_back": "res://Assets/UI/boss_hp_frame_back_3x.png",
	"frame_over": "res://Assets/UI/boss_hp_frame_over_3x.png",
	"frame_over_low": "res://Assets/UI/boss_hp_frame_over_low_3x.png",
	"chip": "res://Assets/UI/boss_hp_chip_3x.png",
	"low": "res://Assets/UI/boss_hp_low_3x.png",
	"low_hframes": 2,
	"low_frame_time": 0.16,
	"flash": "res://Assets/UI/boss_hp_flash_3x.png",
	"flash_punish": "res://Assets/UI/boss_hp_flash_punish_3x.png",
	"flash_alpha": 0.85,
	"spark": "res://Assets/UI/boss_hp_spark_3x.png",
	"spark_hframes": 3,
	"spark_frame_time": 0.05,
	# The burst sits on the fill's leading edge, this far up from the window's top-left.
	"spark_pivot": Vector2(36, 30),
	"sweep": "res://Assets/UI/boss_hp_sweep_3x.png",
	"sweep_hframes": 3,
	"sweep_frame_time": 0.07,
	"ghost": "res://Assets/UI/boss_hp_ghost_3x.png",
	"ghost_width": 9.0,
	# A drain that isn't a hit: the drawn fill steps a texel at a time, so it takes longer than the
	# flat bar's slide did.
	"drain_time": DRAIN_TIME,
	# The winged crest, centred on the bar and standing proud of both rails - the one thing that stops
	# the block reading as a plain rectangle. It hugs the rails rather than crossing them, so only its
	# chin spike is ever over the fill, 3 texels of a 152 texel window.
	"crest": "res://Assets/UI/boss_hp_crest_3x.png",
	"crest_low": "res://Assets/UI/boss_hp_crest_low_3x.png",
	"crest_offset": Vector2(171, -21),
	"plate": "res://Assets/UI/boss_plate_3x.png",
	"plate_tall": "res://Assets/UI/boss_plate_tall_3x.png",
	"size": FRAME_SIZE,
	"fill_offset": FILL_OFFSET,
	"fill_texels": FILL_TEXELS,
	# Screen px per texel of fill, for putting the spark on the fill's leading edge.
	"fill_step": FILL_SIZE.x / FILL_TEXELS,
	# Eric's daze meter, 6 px under the block's bottom rail and in the bar's own language, so the two
	# read as one instrument. It is already 384 wide and already centred here, so only its y moves
	# between the two looks.
	"break_gauge_offset": Vector2(48, 60),
}

#PER BOSS
# One frame for everyone; the identity is the fill. `heat_ramp` is the placeholder ProgressBar's fill
# colour walked from cold to hot by set_heat() - the stops are exactly the colours each boss script
# switched between, so a caller passing 0.0 / 0.5 / 1.0 lands on them exactly. `low_color` replaces
# the cold stop under `low_ratio`, which is the only shape Computah's bar needed.
const BOSS_BARS := {
	# A gold Jolly Roger over crossed cutlasses for his emblem, and a crimson fill with a gold trim line
	# that heats to copper.
	&"burak": {
		"fill": "res://Assets/UI/boss_hp_fill_burak_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_burak_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_burak_3x.png",
		"heat_ramp": [Color("#B02436"), Color("#CF7540")],
	},
	&"eric": {
		"fill": "res://Assets/UI/boss_hp_fill_eric_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_eric_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_eric_3x.png",
		"heat_ramp": [Color(0.85, 0.16, 0.16, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	# Greyson, the second half of FIGHT 06: a double biceps for his emblem and his purple fill, the approved set
	# (2026-09-24). The ramp is the fill's own two purples, for the flat fallback.
	&"greyson": {
		"fill": "res://Assets/UI/boss_hp_fill_greyson_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_greyson_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_greyson_3x.png",
		"heat_ramp": [Color("#7C3BB4"), Color("#A5478F")],
	},
	&"computah": {
		"fill": "res://Assets/UI/boss_hp_fill_computah_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_computah_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_computah_3x.png",
		"heat_ramp": [Color(0.35, 0.72, 0.95, 1), Color(1.0, 0.78, 0.22, 1)],
		"low_color": Color(0.95, 0.5, 0.3, 1),
		"low_ratio": 0.34,
	},
	# A speaker for his emblem, and his shirt's lavender heating to raspberry, from his red roar eyes. The
	# ramp only drives the flat fallback now.
	&"matt": {
		"fill": "res://Assets/UI/boss_hp_fill_matt_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_matt_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_matt_3x.png",
		"heat_ramp": [Color(0.7, 0.71, 0.95, 1), Color(0.96, 0.84, 0.43, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	&"mason": {
		"fill": "res://Assets/UI/boss_hp_fill_mason_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_mason_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_mason_3x.png",
		"heat_ramp": [Color(0.55, 0.36, 0.2, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	&"josh": {
		"fill": "res://Assets/UI/boss_hp_fill_josh_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_josh_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_josh_3x.png",
		"heat_ramp": [Color(0.95, 0.75, 0.15, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	# Danny, boss 5. His set was built from vs_card/bosses.py's data before his fight existed.
	&"danny": {
		"fill": "res://Assets/UI/boss_hp_fill_danny_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_danny_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_danny_3x.png",
		"heat_ramp": [Color(0.4, 0.62, 0.35, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	&"carter": {
		"fill": "res://Assets/UI/boss_hp_fill_carter_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_carter_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_carter_3x.png",
		"heat_ramp": [Color(0.58, 0.22, 0.42, 1), Color(0.7, 0.2, 0.36, 1), Color(0.85, 0.2, 0.28, 1)],
	},
	&"liam": {
		"fill": "res://Assets/UI/boss_hp_fill_liam_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_liam_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_liam_3x.png",
		"heat_ramp": [Color(0.62, 0.12, 0.2, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	# The swallow swaps the row's identity to the beast mid-fight. Its placeholder colours are Liam's
	# own, because the old bar didn't change colour there and this pass isn't allowed to.
	&"bixby": {
		"fill": "res://Assets/UI/boss_hp_fill_bixby_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_bixby_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_bixby_3x.png",
		"heat_ramp": [Color(0.62, 0.12, 0.2, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	&"jordan": {
		"fill": "res://Assets/UI/boss_hp_fill_jordan_3x.png",
		"fill_hot": "res://Assets/UI/boss_hp_fill_hot_jordan_3x.png",
		"emblem": "res://Assets/UI/boss_hp_emblem_jordan_3x.png",
		"heat_ramp": [Color(0.8, 0.22, 0.55, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
	# The keyless row: the legacy CarterAndJoshScene, which the Carter/Josh split superseded. It gets
	# no drawn fill of its own, so it keeps the flat bar under either flag.
	&"": {
		"heat_ramp": [Color(0.75, 0.25, 0.65, 1), Color(0.95, 0.75, 0.1, 1), Color(1.0, 0.55, 0.0, 1)],
	},
}

# The baked nameplate lettering, keyed the way the plate is asked for: a boss, or a pair sharing one
# plate. &"" means there is no baked plate and the block falls back to a themed Label.
const PLATE_NAMES := {
	&"burak": "res://Assets/UI/boss_plate_name_burak_3x.png",
	&"eric": "res://Assets/UI/boss_plate_name_eric_3x.png",
	&"greyson_pair": "res://Assets/UI/boss_plate_name_greyson_pair_3x.png",
	&"greyson": "res://Assets/UI/boss_plate_name_greyson_3x.png",
	&"computah": "res://Assets/UI/boss_plate_name_computah_3x.png",
	&"matt": "res://Assets/UI/boss_plate_name_matt_3x.png",
	&"mason": "res://Assets/UI/boss_plate_name_mason_3x.png",
	&"josh": "res://Assets/UI/boss_plate_name_josh_3x.png",
	&"danny": "res://Assets/UI/boss_plate_name_danny_3x.png",
	&"carter": "res://Assets/UI/boss_plate_name_carter_3x.png",
	&"liam_pair": "res://Assets/UI/boss_plate_name_liam_pair_3x.png",
	# Liam alone, once Bixby has coughed him up (LiamScript).
	&"liam": "res://Assets/UI/boss_plate_name_liam_a_3x.png",
	&"jordan": "res://Assets/UI/boss_plate_name_jordan_3x.png",
}

# The plates whose baked lettering is two stacked lines. They carry the tall plate, and there is one
# of them for the whole block: the pair bake already says both names, so giving row 1 a plate of its
# own puts a COMPUTAH plate straight across Greyson's fill.
const PAIR_PLATES := [&"greyson_pair", &"liam_pair"]

#THE PLACEHOLDER BLOCKS
# One per plate key: the exact Label-and-ProgressBar block that fight drew before the component, in
# px from BLOCK_ANCHOR. `name_font_size` 0 means the theme's own size, which is what the single-bar
# bosses used. Only the pair blocks have a panel, a bracket or row labels.
const PLACEHOLDER_BLOCKS := {
	&"burak": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"eric": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"carter": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(100, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(100, 10, 380, 22)],
	},
	&"josh": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(100, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(100, 10, 380, 22)],
	},
	&"mason": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"jordan": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"computah": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"matt": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"greyson": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"danny": {
		"size": Vector2(380, 56),
		"name_offset": Vector2(50, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(50, 10, 380, 22)],
	},
	&"liam_pair": {
		"size": Vector2(460, 56),
		"name_offset": Vector2(-20, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(-20, 10, 460, 22)],
	},
	# Greyson & Computah: one framed panel, one name, two bars joined by a bracket down their left
	# edge, each bar labelled with its body's initial in that body's own colour.
	&"greyson_pair": {
		"size": Vector2(480, 104),
		"panel": Rect2(0, -32, 480, 104),
		"panel_bg": Color(0.05, 0.06, 0.09, 0.82),
		"panel_border": 3,
		"panel_border_color": Color(0, 0, 0),
		"panel_corner_radius": 4,
		"name_offset": Vector2(12, -28),
		"name_font_size": 30,
		"name_outline": 6,
		"bracket": Rect2(32, 10, 6, 50),
		"bracket_color": Color(0.62, 0.66, 0.78, 0.9),
		"row_labels": ["G", "C"],
		"row_label_offsets": [Vector2(16, 6), Vector2(16, 36)],
		"row_label_font_size": 20,
		"row_label_outline": 5,
		# The beat the neglected body's bar runs while the gap is open, through set_beat(). Only the
		# flat bars need it: the drawn ones say the same thing with their hot fill.
		"heat_pulse": {"time": 0.45, "alpha": 0.45},
		"rows": [Rect2(44, 10, 400, 20), Rect2(44, 40, 400, 20)],
	},
	# The legacy Carter & Josh coordinator.
	&"": {
		"size": Vector2(460, 56),
		"name_offset": Vector2(-20, -24),
		"name_font_size": 0,
		"name_outline": 6,
		"rows": [Rect2(-20, 10, 460, 22)],
	},
}


# A block with a row whose boss has no drawn fill keeps the flat chrome even with the flag on, so the
# block says which one it was built with rather than the flag answering for it.
static func bar(drawn := USE_FINAL_BOSS_BAR) -> Dictionary:
	return FINAL_BAR if drawn else PLACEHOLDER_BAR


# The boss whose fill this row carries. An unknown key falls back to the keyless entry, so a fight
# added before its art still gets a bar rather than an error.
static func boss_bar(key: StringName) -> Dictionary:
	return BOSS_BARS[key] if BOSS_BARS.has(key) else BOSS_BARS[&""]


# The placeholder chrome for a block, asked for by its plate key.
static func block(plate: StringName) -> Dictionary:
	return PLACEHOLDER_BLOCKS[plate] if PLACEHOLDER_BLOCKS.has(plate) else PLACEHOLDER_BLOCKS[&""]


# The baked lettering for a plate, or "" for the ones that keep the themed Label.
static func plate_name(plate: StringName) -> String:
	return PLATE_NAMES.get(plate, "")


# Whether this plate's lettering is a pair's two stacked lines, which needs the tall plate.
static func plate_is_pair(plate: StringName) -> bool:
	return PAIR_PLATES.has(plate)


# The fill's colour for a flat bar: the boss's ramp walked from cold to hot, with the cold stop
# swapped for the low one while the row is under its low ratio.
static func heat_color(key: StringName, heat: float, ratio: float) -> Color:
	var spec := boss_bar(key)
	var stops: Array = spec.heat_ramp.duplicate()
	if spec.has("low_color") and ratio <= spec.low_ratio:
		stops[0] = spec.low_color
	if stops.size() == 1:
		return stops[0]
	var walk := clampf(heat, 0.0, 1.0) * (stops.size() - 1)
	var step := floori(walk)
	if step >= stops.size() - 1:
		return stops[stops.size() - 1]
	return (stops[step] as Color).lerp(stops[step + 1], walk - step)
