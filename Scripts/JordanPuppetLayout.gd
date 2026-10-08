extends RefCounted

# Every number about the bosses Jordan raises as marionettes in his last phase (JordanPuppet): which of their own art
# layouts each one plays from, their frames and feet, which way their sheets face, where their strings hook on, what a
# punch can reach, the rift each rises through, and the recolour they wear. Texel points are on each boss's MAIN frame
# (the idle's), origin top-left; every sheet of theirs stands the soles on the puppet's origin, so a hook there is fixed
# to the body whatever sheet is showing.
#
# THE TWINS (take B, approved by the user 2026-09-28): each puppet is drawn off its boss's own sheets, recoloured into
# red-and-black undead twins with the same size, grid, anchors and silhouette, at PUPPET_DIR/<key>/<the source's file
# name> (Danny's are his sumo's). Each sheet swaps in once its file is in and imported (twin_path); until then, and for
# any twin still missing, the live sheet plays under the placeholder recolour, puppet_tint.gdshader.
#
# THE HOOKS: `back` is where the strings hang from, between the shoulder blades (the user's attach point). The twins
# bring a measured one per sheet frame in the generated Scripts/JordanPuppetHooks.gd (BACK: key -> sheet name -> a
# texel or null per frame), loaded guarded since it may not be in yet; where it has none, the fixed texel below, and on
# a juggle frame the juggle table's tumble_centre. The rest are for combos to come, stand-ins until measured. `_l` and
# `_r` are screen-left and -right on the unflipped sheet.
#
# KEYS: &"greyson", &"matt", &"burak" (Captain Burak; &"captain_burak", as the finale's cameos name him, is taken for
# him too) and &"danny"; and &"eric", &"mason", &"josh" and &"carter" (concepts approved by the user 2026-09-28:
# "approve the concept art, defaults are fine"), summonable, with no attack of theirs built yet.
#
# Eric's and Mason's fights animate them on their scenes' AnimationPlayers, so their layouts have no anim() and their
# juggles are clip names: their rows carry their own `anims` and a `juggle` in BossJuggled's shape, transcribed from
# EricScene and MasonScene. None of the four's layouts has crown(), DAZE_GAP, SFX or fx(): the puppet falls back on
# its head hook, DAZE_GAP below, no sounds of his own and no effect sheets.

const SCALE := 3.0

const TINT_SHADER := "res://Assets/Shaders/puppet_tint.gdshader"
# Luminance onto black, deep red, red and bone; whatever is darker than `keyline` stays black, so every keyline does.
const TINT := {deep = Color("#5A0E14"), red = Color("#B3202A"), bone = Color("#E8D8C8"), keyline = 0.1}

const PUPPET_DIR := "res://Assets/Characters/Jordan/Puppets/"
const USE_FINAL_PUPPET := {&"greyson": true, &"matt": true, &"burak": true, &"danny": true, &"eric": true, &"mason": true,
	&"josh": true, &"carter": true, &"liam": true, &"bixby": true}
const ALIASES := {&"captain_burak": &"burak"}
const HOOKS_SCRIPT := "res://Scripts/JordanPuppetHooks.gd"

# A punch in the punch-out: a flash, a jolt away from the player, and the hit every boss takes (hit_impact).
const FLINCH := {flash = Color(3, 3, 3), flash_time = 0.15, jolt = 3.0, jolt_time = 0.06}
# How far over his crown the finisher's daze stars circle, for a boss whose layout has no DAZE_GAP: the others' own.
const DAZE_GAP := 34.0
const HIT_SOUND := {stream = "res://Assets/Audio/SFX/hit_impact.ogg", volume_db = 0.0, pitch = 1.0}

# Each boss: his art layout (its anim(), crown(), SFX, fx() and juggle() are what the puppet plays), his main frame and
# the texel his soles stand on, how his sheets flip (&"spec": his rows say, as Greyson's poses never flip; &"all":
# drawn facing right, every sheet mirrors when he faces left), the animations the puppet stands, hangs and crumples
# in (the hang is his hit frame held until a limp drawing lands), what a punch can reach (his layout's body box), his
# hooks, and his rift's size (JordanGodLayout.RIFTS). Optional: `anims` and `juggle`, his own where his layout has
# none (above), and `top`, the highest row his standing and hanging frames draw where it is over his body box, which
# his rise starts from (rise_px), so nothing of him shows over the floor before it.
const PUPPETS := {
	&"greyson": {
		layout = "res://Scripts/GreysonArtLayout.gd", frame = Vector2(112, 112), feet = Vector2(56, 111), flip = &"spec",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(34, 26, 44, 86), rift = &"standard",
		hooks = {&"back": Vector2(56, 56), &"head": Vector2(56, 30), &"wrist_l": Vector2(24, 64),
			&"wrist_r": Vector2(88, 64), &"knee_l": Vector2(46, 92), &"knee_r": Vector2(66, 92)},
	},
	&"matt": {
		layout = "res://Scripts/MattArtLayout.gd", frame = Vector2(96, 96), feet = Vector2(48, 95), flip = &"all",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(17, 25, 63, 71), rift = &"standard",
		hooks = {&"back": Vector2(48, 46), &"head": Vector2(48, 12), &"wrist_l": Vector2(20, 60),
			&"wrist_r": Vector2(76, 60), &"knee_l": Vector2(40, 80), &"knee_r": Vector2(56, 80)},
	},
	&"burak": {
		layout = "res://Scripts/BurakBossArtLayout.gd", frame = Vector2(96, 96), feet = Vector2(48, 95), flip = &"all",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(30, 14, 36, 82), rift = &"standard",
		hooks = {&"back": Vector2(48, 49), &"head": Vector2(48, 14), &"wrist_l": Vector2(28, 58),
			&"wrist_r": Vector2(68, 58), &"knee_l": Vector2(42, 80), &"knee_r": Vector2(54, 80)},
	},
	&"danny": {
		layout = "res://Scripts/DannyBossArtLayout.gd", frame = Vector2(176, 144), feet = Vector2(88, 143), flip = &"all",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(40, 2, 96, 142), rift = &"wide",
		hooks = {&"back": Vector2(88, 71), &"head": Vector2(88, 12), &"wrist_l": Vector2(40, 90),
			&"wrist_r": Vector2(136, 90), &"knee_l": Vector2(68, 124), &"knee_r": Vector2(108, 124)},
	},
	# The approved puppet is the finale's idle, eric_entrance frame 3, with no sword: so is everything he plays here.
	# His hit is his juggle sheet's (his fight has no other), and he folds as his Break drops him to one knee, the
	# sword already gone. His fight never mirrors him. Hooks: the concept pass's approved ones, on that idle frame.
	&"eric": {
		layout = "res://Scripts/EricArtLayout.gd", frame = Vector2(256, 192), feet = Vector2(128, 191), flip = &"spec",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(102, 120, 58, 72), top = 98.0,
		rift = &"standard",
		hooks = {&"back": Vector2(131, 160), &"head": Vector2(131, 122), &"wrist_l": Vector2(98, 177),
			&"wrist_r": Vector2(163, 176), &"knee_l": Vector2(114, 185), &"knee_r": Vector2(148, 185)},
		anims = {
			&"idle": {sheet = "res://Assets/Characters/Eric/eric_entrance.png", frames = [3], times = [1.0], loop = true},
			&"hit": {sheet = "res://Assets/Characters/Eric/eric_juggle.png", frames = [0, 1], times = [0.05, 0.07],
				loop = false},
			&"defeat": {sheet = "res://Assets/Characters/Eric/eric_broken.png", frames = [2, 3, 4, 5],
				times = [0.07, 0.1, 0.1, 0.16], loop = false},
			# Attack 3's (JordanComboPortals), off his bear hug and EricScene's hug clips. The plunge is the sword's retrieve
			# backwards into his grip on it planted (13 and 0 draw it); `charge` is the drawn sword-less charge, a twin only,
			# played only once it is in (JordanPortalsLayout.charge_anim); `empty` his empty wait, its stand-in.
			&"plunge": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [14, 13, 0],
				times = [0.18, 0.10, 0.35], loop = false},
			&"plant": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [0], times = [1.0], loop = true},
			&"charge": {sheet = "res://Assets/Characters/Jordan/Puppets/eric/eric_portal_charge.png", frames = [0, 1],
				times = [0.08], loop = true},
			&"rush": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [3, 4], times = [0.07, 0.10],
				loop = false},
			&"whiff": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [5], times = [0.14], loop = false},
			&"stumble": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [6], times = [0.2], loop = false},
			&"grab": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [7], times = [0.28], loop = false},
			&"squeeze": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [8, 9, 10],
				times = [0.10, 0.20, 0.12], loop = false},
			&"toss": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [11], times = [0.20], loop = false},
			&"toss_end": {sheet = "res://Assets/Characters/Eric/eric_bearhug_v2.png", frames = [12], times = [0.30],
				loop = false},
			&"winded": {sheet = "res://Assets/Characters/Eric/eric_winded.png", frames = [0, 1, 2, 3], times = [0.15],
				loop = true},
			&"empty": {sheet = "res://Assets/Characters/Eric/eric_sheet_v2.png", frames = [36, 37], times = [0.12], loop = true},
		},
		# EricArtLayout's FINAL_JUGGLE and JUGGLE_*, and EricScene's juggle_*_final clips.
		juggle = {
			"texture": "res://Assets/Characters/Eric/eric_juggle.png", "hframes": 10, "frame_size": Vector2(256, 192),
			"offset": Vector2(0, -96), "feet": Vector2(128, 191), "tumble_centre": Vector2(128, 146), "top_row": 76,
			"clips": {
				&"launch": {"frames": [0, 1], "times": [0.05, 0.07], "loop": false},
				&"tumble": {"frames": [2, 3, 4, 5], "times": [0.11, 0.11, 0.11, 0.11], "loop": true},
				&"crash": {"frames": [6, 7, 8, 9], "times": [0.08, 0.1, 0.1, 0.02], "loop": false},
				&"down": {"frames": [9], "times": [0.1], "loop": true},
			},
			"shadow": {"texture": "res://Assets/Characters/Eric/eric_leap_shadow.png", "hframes": 3, "scale": 3.0,
				"alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO},
			"lying_time": 0.3, "outro_delay": 1.8,
			"crash_sfx": {"stream": "res://Assets/Audio/SFX/eric_crash_thud.wav", "pitch": 1.0, "volume_db": 0.0},
		},
	},
	# His fight never mirrors him. His body box is his fight's hurtbox; hooks the concept pass's approved ones.
	&"mason": {
		layout = "res://Scripts/MasonArtLayout.gd", frame = Vector2(64, 64), feet = Vector2(32, 63), flip = &"spec",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(10, 7, 44, 57), top = 1.0,
		rift = &"standard",
		hooks = {&"back": Vector2(32, 40), &"head": Vector2(32, 5), &"wrist_l": Vector2(7, 44),
			&"wrist_r": Vector2(56, 44), &"knee_l": Vector2(24, 55), &"knee_r": Vector2(39, 55)},
		anims = {
			&"idle": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [0, 1], times = [0.4], loop = true},
			&"hit": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [12], times = [0.2], loop = false},
			&"defeat": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [13, 14], times = [0.35],
				loop = false},
			# Jordan's circle (JordanComboCircle): his poo squat held up in the air, and slumped once he is let down.
			&"squat": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [6, 7], times = [0.2], loop = true},
			&"broken": {sheet = "res://Assets/Characters/Mason/mason_sheet.png", frames = [13, 14], times = [0.35], loop = true},
		},
		# MasonArtLayout's FINAL_JUGGLE, JUGGLE_* and CRASH_THUD_SFX, and MasonScene's juggle_*_final clips.
		juggle = {
			"texture": "res://Assets/Characters/Mason/mason_juggle.png", "hframes": 12, "frame_size": Vector2(128, 96),
			"offset": Vector2(0, -48), "feet": Vector2(64, 95), "tumble_centre": Vector2(64, 52), "top_row": 9,
			"clips": {
				&"launch": {"frames": [0, 1], "times": [0.06, 0.07], "loop": false},
				&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.2, 0.08, 0.05, 0.05, 0.07], "loop": true},
				&"crash": {"frames": [7, 8, 9], "times": [0.05, 0.09, 0.12], "loop": false},
				&"down": {"frames": [10, 11], "times": [0.55, 0.55], "loop": true},
			},
			"shadow": {"texture": "res://Assets/Characters/Mason/mason_leap_shadow.png", "hframes": 3, "scale": 3.0,
				"alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO},
			"lying_time": 0.3, "outro_delay": 1.8,
			"crash_sfx": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0},
		},
	},
	# His rows mirror as his fight mirrors them, toward the way he faces (every one of his is drawn facing right and
	# flips). His body box is his hat's brim to brim and its crown to his soles; hooks the concept pass's approved ones.
	&"josh": {
		layout = "res://Scripts/JoshArtLayout.gd", frame = Vector2(80, 80), feet = Vector2(40, 79), flip = &"spec",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(19, 5, 44, 75), top = 1.0,
		rift = &"standard",
		hooks = {&"back": Vector2(42, 45), &"head": Vector2(48, 10), &"wrist_l": Vector2(22, 46),
			&"wrist_r": Vector2(50, 51), &"knee_l": Vector2(38, 64), &"knee_r": Vector2(46, 64)},
		# Attack 3's (JordanComboPortals): the whole throw as he casts the sword's portal (frame 1 its release), and its
		# release alone as he flicks each wave of spike portals open. His wild_hold and recover are his layout's own.
		anims = {
			&"cast": {sheet = "res://Assets/Characters/Josh/josh_throw.png", frames = [0, 1, 2, 3],
				times = [0.25, 0.07, 0.11, 0.13], loop = false, flips = true},
			&"flick": {sheet = "res://Assets/Characters/Josh/josh_throw.png", frames = [1, 2], times = [0.07, 0.11],
				loop = false, flips = true},
		},
	},
	# Drawn facing right; his fight turns every sheet to face the player. His body box is his standing mass, his
	# crown to his soles and wrap to wrap, under the aura spikes his idle draws; hooks the concept pass's approved ones.
	&"carter": {
		layout = "res://Scripts/CarterArtLayout.gd", frame = Vector2(96, 96), feet = Vector2(48, 95), flip = &"all",
		idle = &"idle", limp = &"hit", crumple = &"defeat", body_box = Rect2(18, 24, 60, 72), top = 3.0,
		rift = &"standard",
		hooks = {&"back": Vector2(48, 58), &"head": Vector2(48, 27), &"wrist_l": Vector2(20, 72),
			&"wrist_r": Vector2(75, 72), &"knee_l": Vector2(39, 79), &"knee_r": Vector2(57, 79)},
	},
	# Jordan's Elemental Wheel (JordanComboWheel), on his Elements rig (96x96, liam.png at (16, 32), feet on row 95). His
	# layout has no anim(), so every pose is listed here, its frames those of the live strip (his `all` poses count theirs
	# off it, and jordan_wheel's layout tier holds the two equal). Hooks on the live sheet, the approval pass's measured
	# ones (taken on his float, 12 rows higher) moved down to it.
	&"liam": {
		layout = "res://Scripts/LiamArtLayout.gd", frame = Vector2(96, 96), feet = Vector2(48, 95), flip = &"spec",
		idle = &"channel", limp = &"wobble", crumple = &"defeat", body_box = Rect2(32, 36, 32, 60), top = 20.0,
		rift = &"standard",
		hooks = {&"back": Vector2(47, 68), &"head": Vector2(48, 40), &"wrist_l": Vector2(15, 75),
			&"wrist_r": Vector2(77, 75), &"knee_l": Vector2(37, 88), &"knee_r": Vector2(57, 89)},
		anims = {
			&"channel": {sheet = "res://Assets/Characters/Liam/Elements/liam_channel.png", frames = [0, 1, 2, 3, 4, 5],
				times = [0.12], loop = true},
			&"blow": {sheet = "res://Assets/Characters/Liam/Elements/liam_blow.png", frames = [0, 1, 2, 3, 4, 5],
				times = [0.15, 0.2, 0.12, 0.16, 0.14, 0.13], loop = false},
			&"ignite": {sheet = "res://Assets/Characters/Liam/Elements/liam_ignite.png", frames = [0, 1, 2, 3, 4],
				times = [0.06], loop = false},
			&"cast_left": {sheet = "res://Assets/Characters/Liam/Elements/liam_cast_left.png", frames = [0, 1, 2],
				times = [0.15], loop = false},
			&"cast_right": {sheet = "res://Assets/Characters/Liam/Elements/liam_cast_right.png", frames = [0, 1, 2],
				times = [0.15], loop = false},
			&"slam_rise": {sheet = "res://Assets/Characters/Liam/Elements/liam_slam_rise.png", frames = [0, 1, 2],
				times = [0.15, 0.1, 0.75], loop = false},
			&"wobble": {sheet = "res://Assets/Characters/Liam/Elements/liam_wobble.png", frames = [0, 1, 2, 3],
				times = [0.12], loop = true},
			&"fall": {sheet = "res://Assets/Characters/Liam/Elements/liam_fall.png", frames = [0, 1, 2, 3],
				times = [0.15], loop = false},
			&"downed": {sheet = "res://Assets/Characters/Liam/Elements/liam_downed.png", frames = [0, 1, 2],
				times = [0.3], loop = true},
			&"defeat": {sheet = "res://Assets/Characters/Liam/Elements/liam_defeat.png", frames = [0, 1, 2, 3, 4],
				times = [0.12, 0.12, 0.14, 0.2, 1.0], loop = false},
			# Held on its first frame while the State flares in or bursts out over it (JordanWheelLayout.AVATAR_ON_SHEET).
			&"channel_hold": {sheet = "res://Assets/Characters/Liam/Elements/liam_channel.png", frames = [0], times = [1.0],
				loop = true},
		},
	},
	# Jordan's Elemental Wheel: beast Bixby on his own 192x160 grid. His layout has no anim(), so his rows are his ANIMS'
	# own, listed; `bite` and `swim` are drawn for this attack alone (twins only), each played only once it is in, with
	# its stand-in beside it. His body box is his recovery's (RECOVER_BODY_BOX), his head his DAZE_ANCHOR, his back the
	# art pass's measured hook on his hover.
	&"bixby": {
		layout = "res://Scripts/BixbyBeastArtLayout.gd", frame = Vector2(192, 160), feet = Vector2(96, 151), flip = &"spec",
		idle = &"hover", limp = &"hit", crumple = &"recover", body_box = Rect2(3, 56, 186, 99), top = 2.0, rift = &"wide",
		hooks = {&"back": Vector2(95, 71), &"head": Vector2(96, 56), &"wrist_l": Vector2(74, 130),
			&"wrist_r": Vector2(135, 130), &"knee_l": Vector2(30, 126), &"knee_r": Vector2(147, 133)},
		anims = {
			&"hover": {sheet = "res://Assets/Characters/Bixby/bixby_beast.png", frames = [0, 1, 2, 3], times = [0.12],
				loop = true},
			&"fly": {sheet = "res://Assets/Characters/Bixby/bixby_beast_fly.png", frames = [0, 1, 2],
				times = [0.09, 0.07, 0.08], loop = true, flips = true},
			&"land": {sheet = "res://Assets/Characters/Bixby/bixby_beast_land.png", frames = [0, 1, 2],
				times = [0.2, 0.14, 0.35], loop = false},
			&"recover": {sheet = "res://Assets/Characters/Bixby/bixby_beast_recover.png", frames = [0, 1, 2, 3],
				times = [0.18, 0.14, 0.18, 0.16], loop = true},
			&"hit": {sheet = "res://Assets/Characters/Bixby/bixby_beast_hit.png", frames = [0, 1], times = [0.08, 0.14],
				loop = false},
			&"brace": {sheet = "res://Assets/Characters/Bixby/bixby_pound.png", frames = [0, 1], times = [0.09, 0.12],
				loop = false},
			&"pound": {sheet = "res://Assets/Characters/Bixby/bixby_pound.png", frames = [2, 3, 4, 5],
				times = [0.07, 0.08, 0.08, 0.12], loop = false},
			&"perch": {sheet = "res://Assets/Characters/Bixby/bixby_perch.png", frames = [2, 3], times = [0.25], loop = true},
			&"inhale": {sheet = "res://Assets/Characters/Bixby/bixby_perch.png", frames = [7, 8, 9], times = [0.13],
				loop = true},
			&"flyby_glide": {sheet = "res://Assets/Characters/Bixby/bixby_beast_flyby.png", frames = [0, 1, 2, 3],
				times = [0.06], loop = true, flips = true},
			&"flyby_breath": {sheet = "res://Assets/Characters/Bixby/bixby_beast_flyby.png", frames = [4, 5, 6, 7],
				times = [0.06], loop = true, flips = true},
			# Rear, lunge, the snap on BITE_TELL (0.40 s), the recoil.
			&"bite": {sheet = "res://Assets/Characters/Jordan/Puppets/bixby/bixby_bite.png", frames = [0, 1, 2, 3, 4],
				times = [0.15, 0.10, 0.15, 0.06, 0.20], loop = false},
			&"bite_stand_in": {sheet = "res://Assets/Characters/Bixby/bixby_perch.png", frames = [11, 11, 12],
				times = [0.15, 0.25, 0.2], loop = false},
			&"swim": {sheet = "res://Assets/Characters/Jordan/Puppets/bixby/bixby_swim.png", frames = [0, 1, 2, 3],
				times = [0.08], loop = true},
			&"swim_stand_in": {sheet = "res://Assets/Characters/Bixby/bixby_beast.png", frames = [0, 1, 2, 3],
				times = [0.08], loop = true},
		},
	},
}
# The stand-in rift under a puppet is this wide against his body box.
const RIFT_WIDTH_RATIO := 1.2
# Sheets with his back to the camera (the hooks table's note): the strings tie on over the body there, on the ring the
# twins draw on his back, rather than running in behind it. Until the hooks table lists them frame by frame (OVER).
const BACK_VIEWS: Array[String] = ["greyson_pose_a", "greyson_pose_c"]


static func key(boss: StringName) -> StringName:
	return ALIASES.get(boss, boss)


static func spec(boss: StringName) -> Dictionary:
	return PUPPETS[key(boss)]


static func layout(boss: StringName) -> GDScript:
	return load(spec(boss).layout)


# One of his animations by name: his row's own where it has one, his layout's otherwise.
static func anim(boss: StringName, anim_name: StringName) -> Dictionary:
	var anims: Dictionary = spec(boss).get("anims", {})
	if anims.has(anim_name):
		return anims[anim_name]
	return layout(boss).anim(anim_name)


# His juggle in BossJuggled's shape: his row's own where his layout's is his AnimationPlayer's clip names.
static func juggle(boss: StringName) -> Dictionary:
	var s := spec(boss)
	return s.juggle if s.has("juggle") else layout(boss).juggle()


static func daze_gap(boss: StringName) -> float:
	return layout(boss).get_script_constant_map().get("DAZE_GAP", DAZE_GAP)


# His layout's sounds, or none.
static func sfx(boss: StringName) -> Dictionary:
	return layout(boss).get_script_constant_map().get("SFX", {})


# His twin of `live_path`, once it is in and imported; "" until then.
static func twin_path(boss: StringName, live_path: String) -> String:
	var k := key(boss)
	var twin := PUPPET_DIR + String(k) + "/" + live_path.get_file()
	if USE_FINAL_PUPPET.get(k, false) and ResourceLoader.exists(twin):
		return twin
	return ""


# The generated back hooks, if they are in: a guarded load, since they may not be.
static func hooks_table() -> GDScript:
	if not ResourceLoader.exists(HOOKS_SCRIPT):
		return null
	var table = load(HOOKS_SCRIPT)
	return table if table is GDScript and table.can_instantiate() else null


# The measured back hook on frame `frame` of the sheet `sheet_name` (its file name with no extension), or null.
static func measured_back(table: GDScript, boss: StringName, sheet_name: String, frame: int) -> Variant:
	if table == null:
		return null
	var back: Dictionary = table.get_script_constant_map().get("BACK", {})
	var sheets: Dictionary = back.get(key(boss), back.get(String(key(boss)), {}))
	var frames: Array = sheets.get(StringName(sheet_name), sheets.get(sheet_name, []))
	if frame < 0 or frame >= frames.size():
		return null
	return frames[frame]


# A row of his layout's animations: its own frame and feet, or his main ones.
static func frame_of(boss: StringName, row: Dictionary) -> Vector2:
	return row.get("frame", spec(boss).frame)


static func feet_of(boss: StringName, row: Dictionary) -> Vector2:
	return row.get("feet", spec(boss).feet)


# What stands a sheet's soles on the puppet's origin.
static func sheet_offset(boss: StringName, row: Dictionary) -> Vector2:
	var frame := frame_of(boss, row)
	var feet := feet_of(boss, row)
	return Vector2(frame.x / 2.0 - feet.x, frame.y / 2.0 - feet.y - 1.0)


# Whether a row is drawn mirrored with him facing left.
static func flipped(boss: StringName, row: Dictionary, face_left: bool) -> bool:
	if spec(boss).flip == &"spec":
		return row.get("flips", false) and face_left != row.get("drawn_left", false)
	return face_left


# How far under the floor line he starts his rise: his whole body, the top of the box (or of what he draws, `top`) to
# the soles.
static func rise_px(boss: StringName) -> float:
	var s := spec(boss)
	return (s.feet.y + 1.0 - minf(s.body_box.position.y, s.get("top", s.body_box.position.y))) * SCALE


# Whether the strings tie on over him on `frame` of the sheet `sheet_name` (its file name with no extension): his back
# is to the camera. The hooks table's OVER lists every such frame by sheet once it has one; until then, BACK_VIEWS'
# whole sheets do.
static func strings_over(table: GDScript, sheet_name: String, frame: int) -> bool:
	var over = table.get_script_constant_map().get("OVER") if table != null else null
	if not (over is Dictionary):
		return BACK_VIEWS.has(sheet_name)
	var frames = over.get(sheet_name, over.get(StringName(sheet_name), over.get(sheet_name + ".png", null)))
	return frames is Array and frames.has(frame)


static func rift_radius(boss: StringName) -> float:
	return spec(boss).body_box.size.x * SCALE * RIFT_WIDTH_RATIO / 2.0
