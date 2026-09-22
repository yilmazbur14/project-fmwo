extends RefCounted

# Every size, colour, beat and texture the VS intro card is drawn from, and the per-fight table that
# drives it. Each set of art has its own USE_FINAL_* flag; placeholder and final art go through the
# same code, so turning a flag off brings the placeholder back. Eric's set is final; the other six
# fights draw their half of the band and all of their writing in code until theirs lands.
#
# TWO SCALES, ON PURPOSE. The project is 1920x1080 with stretch/mode="canvas_items", so pixel art
# authored at 640x360 draws at ART_SCALE and lettering, which the artist bakes at screen resolution,
# draws at 1. Every position below is a literal top-left in that 1920x1080 frame, except the name
# and the WIN plate, which hang from a right edge so a longer name or rank still lands where Eric's
# does. Font sizes belong to the placeholder only, on ui_theme.tres' 11 px grid.

const ART_SCALE := 3.0

#THE BAND
# One Elite-Four-style banner across a darkened arena: two blocks meeting on a diagonal, the
# player's bust baked into the left one and the boss's into the right one.
const BAND_AT := Vector2(0, 366)
# Texels, before ART_SCALE: the size the two halves are authored at.
const BAND_SIZE := Vector2(640, 132)
# The seam's x on the band's top and bottom rows, in texels - the diagonal both halves are cut on.
# Only the placeholder needs them; the final halves arrive already cut.
const SPLIT_TOP := 350.0
const SPLIT_BOTTOM := 290.0
# How far off its home each half starts, in screen px: enough to clear the screen, no further.
const DRIVE_OFFSET := 1080.0

enum Side { LEFT, RIGHT }

#THE FRAME THE CODE DRAWS
# Letterbox over the arena, top and bottom, with a rule on each inner edge, and the live arena
# behind it darkened toward the menus' night blue.
# [the strip, the rule down its inner edge], both in the 1920x1080 frame.
const LETTERBOX_TOP := [Rect2(0, 0, 1920, 276), Rect2(0, 274, 1920, 2)]
const LETTERBOX_BOTTOM := [Rect2(0, 852, 1920, 228), Rect2(0, 852, 1920, 2)]
const LETTERBOX_COLOR := Color(0.08235294, 0.07450981, 0.12156863)
const LETTERBOX_RULE_COLOR := Color(0.24705882, 0.24705882, 0.45490196)
# #222034 over the arena: it keeps 22% of what is behind it, the darkening the mock-ups were judged
# on. It fades in with the halves and goes out under the white flash.
const DIM_COLOR := Color(0.13333334, 0.1254902, 0.20392157, 0.78)
const FLASH_COLOR := Color(1, 1, 1)

#THE BEAT SHEET
# Seconds from play(), the approved timing. Everything between two beats is interpolated, so the
# card is a pure function of its clock and skipping to the end is just moving the clock.
#   0.00 - 0.16  the halves drive in from opposite edges, easing out, busts riding them
#   0.16         they meet; the seam flashes white, held two frames, then fading
#   0.16 - 0.24  the VS falls from 1.6x onto 1.0 about its own centre
#   0.16 - 0.26  the card takes a knock, two frames per step
#   0.24         the burst pops on the landing frame and fades
#   0.24 - 0.38  the name and the WIN plate slide in from the right as they fade up; the fight
#                number and the epithet fade in
#   0.38 - 1.75  hold
#   1.75 - 1.95  white flash out into the fight
const DRIVE_IN := 0.16
const VS_LAND := 0.24
const WRITING_IN := 0.38
const HOLD_END := 1.75
const FLASH_PEAK := 1.83
const CARD_END := 1.95

const VS_FROM_SCALE := 1.6
# The knock, in screen px; (0, 0) is the settle. The card takes it, not the arena behind it: the dim
# and the letterbox cover the whole screen, and moving those would open a strip at the edge.
const SLAM_SHAKE := [Vector2(-21, 15), Vector2(18, -12), Vector2(-9, 6), Vector2(0, 0)]
const SLAM_SHAKE_FRAMES := 2
# Held at full alpha this long from the meeting, then faded out over the next stretch.
const SEAM_FLASH_HOLD := 0.033
const SEAM_FLASH_FADE := 0.08
const BURST_FADE := 0.12
# How far the name and the WIN plate come in from the right, in screen px.
const SLIDE_IN := 40.0

#WHERE EVERY PIECE SITS, IN THE 1920x1080 FRAME
const VS_AT := Vector2(866, 487)
const VS_SIZE := Vector2(224, 154)
# It falls onto its own centre, so that is what it is placed by.
const VS_CENTRE := VS_AT + VS_SIZE * 0.5
const FIGHT_AT := Vector2(54, 174)
const EPITHET_AT := Vector2(54, 900)
# Top-right, not top-left: the plates are trimmed to their ink, so each one's own width decides
# where it starts. Eric's 208 px name lands on (1577, 644) and his 206 px WIN on (1510, 924), the
# coordinates the set was drawn to.
const NAME_TOP_RIGHT := Vector2(1785, 644)
const WIN_TOP_RIGHT := Vector2(1716, 924)
const BADGE_AT := Vector2(1746, 888)

#THE FIGHTS, KEYED
# A new boss is a new entry here and the files its key names, and nothing else: play() takes the
# key, and everything the card draws comes out of this table or out of Assets/UI/VsCard.
#   fight      the fight scene the key belongs to, so a fight can look its own key up
#   number     what the card counts this fight as, and which fight_NN plate it draws. The playable
#              index - not an index into GameProgress.BOSSES, which still carries fights whose
#              scenes aren't built.
#   name       what the name plate says; the placeholder writes it while the plate is missing
#   epithet    the line under the band. Optional: a card with none lays out without it, and the
#              six that aren't Eric's are stand-ins until the user approves them.
#   rank       what a win promotes the player to, and which win_<rank> plate is drawn. It has to
#              read the same as this fight's rank in GameProgress.BOSSES, which is what the
#              Victory screen actually pays out. The last fight hands over an invite, not a rank,
#              so its rank is empty and it draws no WIN plate.
#   rank_icon  PLACEHOLDER ONLY: the frame of Assets/UI/Screens/rank_icons.png the stand-in badge
#              shows, which is this fight's slot on the Victory screen's ladder
#   ramp       PLACEHOLDER ONLY: five colours, darkest first, for the boss's half of the band while
#              it is drawn in code. The final halves carry their own ramp, baked in.
#   portrait   PLACEHOLDER ONLY: the 64x64 dialogue portrait the stand-in half busts the boss with
const CARDS := {
	"eric": {
		"fight": "res://Scenes/Bosses/EricBossFightScene.tscn",
		"number": 1,
		"name": "ERIC",
		"epithet": "THE WHITE KNIGHT",
		"rank": "@regular",
		"rank_icon": 2,
		"ramp": ["#525A74", "#7A86A0", "#A3B1C2", "#CDD7E2", "#EAF0F6"],
		"portrait": "res://Assets/Characters/Eric/portrait.png",
	},
	"computah": {
		"fight": "res://Scenes/Bosses/ComputahBossFightScene.tscn",
		"number": 2,
		"name": "COMPUTAH",
		"epithet": "",
		"rank": "@active",
		"rank_icon": 3,
		"ramp": ["#0B1620", "#12304A", "#1F5C8A", "#35A6D8", "#A9E4FF"],
		"portrait": "res://Assets/Characters/Computah/portrait.png",
	},
	"mason": {
		"fight": "res://Scenes/Bosses/MasonBossFightScene.tscn",
		"number": 3,
		"name": "MASON",
		"epithet": "",
		"rank": "@trusted",
		"rank_icon": 5,
		"ramp": ["#3A2418", "#74432A", "#B07A34", "#D9A066", "#F2C457"],
		"portrait": "res://Assets/Characters/Mason/portrait.png",
	},
	"josh": {
		"fight": "res://Scenes/Bosses/JoshBossFightScene.tscn",
		"number": 4,
		"name": "JOSH",
		"epithet": "",
		"rank": "@vip",
		"rank_icon": 6,
		"ramp": ["#2B1B3A", "#45283C", "#6B3F7A", "#9C5FB5", "#D6A9E8"],
		"portrait": "res://Assets/Characters/Josh/portrait.png",
	},
	"carter": {
		"fight": "res://Scenes/Bosses/CarterBossFightScene.tscn",
		"number": 5,
		"name": "CARTER",
		"epithet": "",
		"rank": "@moderator",
		"rank_icon": 8,
		"ramp": ["#140A0A", "#3C0C20", "#6E1F22", "#AC3232", "#D95763"],
		"portrait": "res://Assets/Characters/Carter/portrait.png",
	},
	"liam": {
		"fight": "res://Scenes/Bosses/LiamBossFightScene.tscn",
		"number": 6,
		"name": "LIAM & BIXBY",
		"epithet": "",
		"rank": "@admin",
		"rank_icon": 9,
		"ramp": ["#1A1016", "#4A1C08", "#7A3010", "#DF6C22", "#FFB45E"],
		"portrait": "res://Assets/Characters/Liam/portrait.png",
	},
	"jordan": {
		"fight": "res://Scenes/Bosses/JordanBossFightScene.tscn",
		"number": 7,
		"name": "JORDAN",
		"epithet": "",
		"rank": "",
		"rank_icon": 10,
		"ramp": ["#0B0A12", "#222034", "#3F3F74", "#5B6EE1", "#CBDBFC"],
		"portrait": "res://Assets/Characters/Jordan/portrait.png",
	},
}

# What a key with no entry of its own gets, so a fight that is renamed or not in the table yet still
# opens on a card rather than erroring.
const FALLBACK_CARD := {
	"fight": "",
	"number": 0,
	"name": "CHALLENGER",
	"epithet": "",
	"rank": "",
	"rank_icon": 0,
	"ramp": ["#15131F", "#222034", "#2E2C4A", "#3F3F74", "#3A5BA8"],
	"portrait": "",
}

#FINAL ART
const FINAL_DIR := "res://Assets/UI/VsCard/"
# The furniture every card shares: the left half with Burak baked into it, the VS glyph, the white
# wedge that flashes along the seam and the burst the VS lands in. bust_burak.png and bust_<key>.png
# ship alongside for reuse elsewhere; the halves already carry them, so the card never draws one.
const USE_FINAL_FRAME := true
const FRAME_ART := {
	"band_left": "band_left.png",
	"vs": "vs.png",
	"seam_flash": "seam_flash.png",
	"burst": "vs_burst.png",
}
# Flipped per fight as that fight's set lands. A set is the boss's half of the band, their name,
# their epithet, their badge, the fight_NN plate for their number and the win_<rank> plate for their
# rank; nothing under FINAL_DIR is loaded for a fight whose flag is off.
const USE_FINAL_CARDS := {
	"eric": true,
	"computah": false,
	"mason": false,
	"josh": false,
	"carter": false,
	"liam": false,
	"jordan": false,
}

#PLACEHOLDER
# The dialogue portraits are 64x64; at this scale they stand 96 texels tall in a 132 texel band, and
# their bottom centre lands on the same spot the drawn busts stand on.
const PLACEHOLDER_BUST_SCALE := 1.5
const PLACEHOLDER_BUST_AT := Vector2(462, 124)
# The player's half if the drawn one is ever switched off: his side stays dark, the way Platinum
# keeps the challenger's dark, and Burak has no dialogue portrait, so his bust is the front-facing
# idle off the sheet he fights on.
const PLACEHOLDER_PLAYER_RAMP := ["#15131F", "#222034", "#2E2C4A", "#3F3F74", "#3A5BA8"]
const PLACEHOLDER_PLAYER_BUST := {
	"texture": "res://Assets/Characters/MainPlayer/player_4dir_sheet.png",
	"region": Rect2(0, 0, 32, 32),
	"scale": 3.0,
	"at": Vector2(170, 124),
}
# The band's top and bottom rules, drawn full width over both halves: [inset from the edge, height,
# colour], in texels. They are up from the first frame, so the halves read as driving into a slot.
const PLACEHOLDER_RULES := [
	[0.0, 3.0, Color(0, 0, 0)],
	[3.0, 1.0, Color(0.2901961, 0.2901961, 0.50980395)],
]
# The seam: [texels along the band's top row from the split, width, colour]. Positive offsets ride
# the boss's block, so the placeholder half carries its own edge in and out with it.
const PLACEHOLDER_SEAM := [
	[0.0, 5.0, Color(0, 0, 0)],
	[4.0, 2.0, Color(0.76862746, 0.5411765, 0.17254902)],
	[6.0, 1.0, Color(0.9490196, 0.76862746, 0.34117648)],
	[22.0, 1.0, Color(0.91764706, 0.9411765, 0.9647059)],
]
# The stand-in badge: the Victory screen's own rank ring, with that rank's icon inside it.
const PLACEHOLDER_BADGE := {
	"slot": "res://Assets/UI/Screens/rank_slot.png",
	"icons": "res://Assets/UI/Screens/rank_icons.png",
	"frame_width": 40,
	# The ring's "current" frame: the slot this win lights up.
	"slot_frame": 2,
}
# Pixelify Sans is only crisp at multiples of its 11 px design size. The name is written at the size
# the drawn plate is baked at, so the two lay out the same. Written text hangs in a box this wide,
# which is what lets a line be right-aligned on its anchor without measuring it.
const NAME_FONT_SIZE := 99
const LINE_FONT_SIZE := 33
const VS_FONT_SIZE := 198
const LABEL_BOX_WIDTH := 900.0
const NAME_COLOR := Color(1, 1, 1)
const NAME_SHADOW_COLOR := Color(0.043137256, 0.039215688, 0.07058824)
const EPITHET_COLOR := Color(0.8039216, 0.84313726, 0.8862745)
const FIGHT_COLOR := Color(0.60784316, 0.6784314, 0.7176471)
const WIN_COLOR := Color(0.9490196, 0.76862746, 0.34117648)
# The burst the VS lands in while the drawn one is off: a spiked star and a ring, in screen px
# around the VS's centre. Every other spike is the short one.
const PLACEHOLDER_BURST := {
	"spikes": 20,
	"inner_radius": 60.0,
	"long_radius": 480.0,
	"short_radius": 350.0,
	"ring_radius": 168.0,
	"ring_width": 9.0,
	"color": Color(1, 1, 1),
}
# The white wedge along the seam, in texels either side of it.
const PLACEHOLDER_SEAM_FLASH_WIDTH := 7.0


# The table's entry for a fight, or the fallback for a key with none.
static func card(key: String) -> Dictionary:
	return CARDS.get(key, FALLBACK_CARD)


# The key a fight scene's own path belongs to, "" for a scene that is not in the table. This is how
# a card finds its data when it is handed a scene rather than a key.
static func key_for_scene(scene_path: String) -> String:
	for key in CARDS:
		if CARDS[key]["fight"] == scene_path:
			return key
	return ""


static func uses_final_card(key: String) -> bool:
	return USE_FINAL_CARDS.get(key, false)


# One of FRAME_ART's pieces, or null while the shared furniture is still drawn in code.
static func frame_art(piece: String) -> Texture2D:
	return load(FINAL_DIR + FRAME_ART[piece]) if USE_FINAL_FRAME else null


# The boss's own half of the band, or null while that fight is still on a placeholder.
static func band_right(key: String) -> Texture2D:
	return _final(key, "band_right_%s.png" % key)


static func name_plate(key: String) -> Texture2D:
	return _final(key, "name_%s.png" % key)


# Null for a fight with no epithet yet as well as for one still on a placeholder: a card lays out
# without one.
static func epithet_plate(key: String) -> Texture2D:
	if card(key)["epithet"] == "":
		return null
	return _final(key, "epithet_%s.png" % key)


static func fight_plate(key: String) -> Texture2D:
	return _final(key, "fight_%02d.png" % int(card(key)["number"]))


# The last fight hands over an invite rather than a rank, so it has no WIN plate and no badge.
static func win_plate(key: String) -> Texture2D:
	var rank: String = card(key)["rank"]
	if rank == "":
		return null
	return _final(key, "win_%s.png" % rank.trim_prefix("@"))


static func badge_plate(key: String) -> Texture2D:
	if card(key)["rank"] == "":
		return null
	return _final(key, "badge_%s.png" % key)


# The placeholder bust for a boss, or null for a fight with no portrait drawn yet.
static func placeholder_bust(key: String) -> Texture2D:
	var path: String = card(key).get("portrait", "")
	return load(path) if path != "" and ResourceLoader.exists(path) else null


static func placeholder_player_bust() -> Texture2D:
	return _atlas(PLACEHOLDER_PLAYER_BUST.texture, 0, int(PLACEHOLDER_PLAYER_BUST.region.size.x))


# The stand-in badge's ring and icon, each a frame off a strip the Victory screen already uses.
static func placeholder_badge(key: String) -> Array[Texture2D]:
	var width: int = PLACEHOLDER_BADGE.frame_width
	return [
		_atlas(PLACEHOLDER_BADGE.icons, int(card(key)["rank_icon"]), width),
		_atlas(PLACEHOLDER_BADGE.slot, PLACEHOLDER_BADGE.slot_frame, width),
	]


# One half of the band, in texels of the band's own frame: the block's four corners, cut on the seam.
static func half_points(side: int) -> PackedVector2Array:
	var w := BAND_SIZE.x
	var h := BAND_SIZE.y
	if side == Side.LEFT:
		return PackedVector2Array([Vector2(0, 0), Vector2(SPLIT_TOP, 0), Vector2(SPLIT_BOTTOM, h), Vector2(0, h)])
	return PackedVector2Array([Vector2(SPLIT_TOP, 0), Vector2(w, 0), Vector2(w, h), Vector2(SPLIT_BOTTOM, h)])


# A corner colour per half_points() vertex, so a flat polygon reads as the ramp's diagonal gradient.
static func half_colors(ramp: Array, side: int) -> PackedColorArray:
	var cols: Array[Color] = []
	for entry in ramp:
		cols.append(Color(entry))
	if side == Side.LEFT:
		return PackedColorArray([cols[1], cols[3], cols[2], cols[0]])
	return PackedColorArray([cols[3], cols[1], cols[0], cols[2]])


# A line parallel to the seam, `offset` texels along the band's top row from it: [top, bottom].
static func seam_line(offset: float) -> PackedVector2Array:
	return PackedVector2Array([Vector2(SPLIT_TOP + offset, 0), Vector2(SPLIT_BOTTOM + offset, BAND_SIZE.y)])


# The placeholder burst's star, in screen px around its own origin.
static func burst_points() -> PackedVector2Array:
	var spec: Dictionary = PLACEHOLDER_BURST
	var spikes: int = spec.spikes
	var points := PackedVector2Array()
	for i in spikes * 2:
		var angle := TAU * float(i) / float(spikes * 2)
		var radius: float = spec.inner_radius
		if i % 2 == 0:
			radius = spec.long_radius if i % 4 == 0 else spec.short_radius
		points.append(Vector2(cos(angle), sin(angle)) * radius)
	return points


static func _final(key: String, file: String) -> Texture2D:
	if not uses_final_card(key):
		return null
	return load(FINAL_DIR + file)


static func _atlas(path: String, frame: int, width: int) -> Texture2D:
	var atlas := AtlasTexture.new()
	atlas.atlas = load(path)
	atlas.region = Rect2(frame * width, 0, width, width)
	return atlas
