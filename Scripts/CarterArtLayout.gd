extends RefCounted

# Every number that depends on how Carter, his clones and his darkness are drawn, so a redraw only
# needs this file. Points and boxes are in texels on one of his frames, origin top-left.
# Each asset has its own USE_FINAL_* flag: placeholder and final art go through the same code, so the
# fight is playable before a sheet lands and turning a flag off brings the placeholder back.
# This is the Akuma Carter, boss 5. The wrestler Carter that Mason calls in is a different character
# with his own script and art (Scripts/CarterScript.gd); nothing here belongs to him.

const SCALE := 3.0

#CARTER (horizontal strips of 96x96 frames, feet on row 95, x = 47.5 the symmetry axis)
const FRAME_SIZE := Vector2(96, 96)
const ANCHOR := Vector2(48, 95)
# The approved sheet: frame 0 standing, frame 1 arms crossed (his signature), frame 2 his back.
# Every placeholder pose below is one of those three.
const AKUMA_SHEET := "res://Assets/Characters/Carter/carter_akuma.png"

# What the player can punch while he is down recovering: the mass of carter_spent, the pose he holds
# through the punish window. He kneels, so the box sits well below the standing one. The polished
# redraw spans x 19-72 from row 36 or 37 down, so it was widened to take in his head and his right
# hand.
const RECOVER_BODY_BOX := Rect2(18, 37, 55, 58)
# Where the finisher's daze stars circle, in px from the floor point he stands on: a little over the
# badge anchor of that same kneeling pose, which sits at texel (48, 31).
const DAZE_ANCHOR := Vector2(0, -226)

#THE HUD
# Where his health bar block and the player's own HUD are drawn, measured off the live fight: the
# defence suite's carter_hud mode walks the real HUD and fails if these stop covering it. Nothing the
# player has to read - a clone's light, a badge - may sit under one of them, or off the view (VIEW_RECT).
const HUD_KEEP_OUT: Array[Rect2] = [
	# His name plate, bar, crest and Break gauge.
	Rect2(720, 33, 480, 148),
	# The player's combo count, hearts and stamina, bottom left.
	Rect2(10, 842, 406, 229),
	# The player's parry streak and hype meter, bottom right.
	Rect2(1371, 946, 537, 126),
]
# How far clear of them, and of the edge of the view, what is read has to stay.
const HUD_CLEARANCE := 12.0
# A ParryTell badge, red or yellow, around the anchor its bottom tip stands on: a 32x24 frame at 3x.
const TELL_BADGE := Rect2(-48, -72, 96, 72)

#ANIMATIONS
# name: sheet, frames in order, seconds on each (the last value repeats) and whether it loops.
# Optional: turn, the degrees the sprite is rotated (the defeat placeholder is his standing pose
# keeled over). The final sheets are 96x96 strips drawn facing right with the feet on row 95.
const USE_FINAL_ANIMS := {
	&"idle": true,
	&"intro": true,
	&"eye_flash": true,
	&"summon": true,
	&"rush": true,
	&"rush_pass": true,
	&"vanish": true,
	&"reappear": true,
	&"recover": true,
	&"hit": true,
	&"defeat": true,
	&"victory": true,
	&"victory_hold": true,
	&"ko_vanish": true,
	&"ko_reappear": true,
	&"look_back_ready": true,
	&"look_back": true,
	&"look_back_hold": true,
	&"lights_out": false,
	&"messatsu_charge": true,
	&"messatsu_fire": true,
}

const PLACEHOLDER_ANIMS := {
	&"idle": {sheet = AKUMA_SHEET, frames = [1], times = [1.0], loop = true},
	&"intro": {sheet = AKUMA_SHEET, frames = [1], times = [1.2], loop = false},
	# The eyes go: he drops the crossed arms and squares up.
	&"eye_flash": {sheet = AKUMA_SHEET, frames = [1, 0], times = [0.18, 0.37], loop = false},
	&"summon": {sheet = AKUMA_SHEET, frames = [0], times = [0.35], loop = false},
	# He is squared up while the tell is over his head, then his back is to the player once the
	# strike has gone through them.
	&"rush": {sheet = AKUMA_SHEET, frames = [0], times = [0.21], loop = false},
	&"rush_pass": {sheet = AKUMA_SHEET, frames = [2], times = [0.165], loop = false},
	&"vanish": {sheet = AKUMA_SHEET, frames = [2], times = [0.45], loop = false},
	&"reappear": {sheet = AKUMA_SHEET, frames = [2, 1], times = [0.18, 0.32], loop = false},
	&"recover": {sheet = AKUMA_SHEET, frames = [0], times = [1.0], loop = true},
	&"hit": {sheet = AKUMA_SHEET, frames = [0], times = [0.22], loop = false},
	&"defeat": {sheet = AKUMA_SHEET, frames = [0], times = [1.0], loop = false, turn = 90.0},
	# He turns his back on them. The hand-over from victory to victory_hold IS the ignition, so the
	# placeholder turn is one frame long and the back view is where the mark takes.
	&"victory": {sheet = AKUMA_SHEET, frames = [0], times = [0.37], loop = false},
	&"victory_hold": {sheet = AKUMA_SHEET, frames = [2], times = [1.0], loop = true},
	&"ko_vanish": {sheet = AKUMA_SHEET, frames = [2], times = [0.28], loop = false},
	&"ko_reappear": {sheet = AKUMA_SHEET, frames = [2], times = [0.30], loop = false},
	# His back view, still burning, for when the look-back sheet is turned off.
	&"look_back_ready": {sheet = "res://Assets/Characters/Carter/carter_victory.png",
		frames = [4, 5, 6], times = [0.11, 0.13, 0.13], loop = true},
	&"look_back": {sheet = "res://Assets/Characters/Carter/carter_victory.png",
		frames = [4, 5, 6], times = [0.11, 0.13, 0.13], loop = false},
	&"look_back_hold": {sheet = "res://Assets/Characters/Carter/carter_victory.png",
		frames = [4, 5, 6], times = [0.11, 0.13, 0.13], loop = true},
	# The Messatsu's stand-ins, off sheets that already exist: the lights die on the eye flash run
	# through, he charges holding its hard downward glare, and he fires on the rush's committed frame.
	# The charge and the fire have their own sheets now. carter_lights_out was never drawn, so the eye
	# flash is still what plays, lit, before the lights go.
	&"lights_out": {sheet = "res://Assets/Characters/Carter/carter_eye_flash.png",
		frames = [0, 1, 2, 3], times = [0.10, 0.08, 0.08, 0.14], loop = false},
	&"messatsu_charge": {sheet = "res://Assets/Characters/Carter/carter_eye_flash.png",
		frames = [3], times = [0.12], loop = true},
	&"messatsu_fire": {sheet = "res://Assets/Characters/Carter/carter_rush.png",
		frames = [3], times = [0.10], loop = false},
}

const FINAL_ANIMS := {
	# The standing pose, not the arms-crossed one: frame 0 is byte-identical to the entrance's last
	# frame, so the entrance cuts to it with no blend. Changing one means changing both.
	&"idle": {sheet = "res://Assets/Characters/Carter/carter_idle.png",
		frames = [0, 1, 2, 3], times = [0.18], loop = true},
	&"intro": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
		times = [0.10, 0.10, 0.10, 0.12, 0.14, 0.09, 0.07, 0.07, 0.16, 0.11, 0.11, 0.11, 0.13, 0.20,
			0.30, 0.14, 0.60], loop = false},
	# Frame 3 is the control-loss frame, held for its full 260 ms: the beat ends on it and the yank
	# carries it straight on.
	&"eye_flash": {sheet = "res://Assets/Characters/Carter/carter_eye_flash.png",
		frames = [0, 1, 2, 3], times = [0.12, 0.09, 0.09, 0.26], loop = false},
	# No summon sheet was ever drawn. The yank holds eye_flash's control-loss frame, which is already
	# a hard downward glare with the jaw open: it reads as him doing this to you.
	&"summon": {sheet = "res://Assets/Characters/Carter/carter_eye_flash.png",
		frames = [3], times = [0.4], loop = false},
	# The Beam Rush's strike, in two halves. Both sheets are drawn travelling RIGHT, so a strike from
	# the player's right mirrors them; their timings are the ones build_combat.py quotes.
	# `rush` is 0.21 s of a 0.36 s read, so it holds its last frame - him committed, about to go -
	# for the rest of the window, which is exactly what the player is reading.
	&"rush": {sheet = "res://Assets/Characters/Carter/carter_rush.png",
		frames = [0, 1, 2, 3], times = [0.05, 0.045, 0.06, 0.055], loop = false},
	&"rush_pass": {sheet = "res://Assets/Characters/Carter/carter_rush_pass.png",
		frames = [0, 1, 2], times = [0.045, 0.05, 0.07], loop = false},
	# No vanish sheet either. The entrance draws him materialising out of his aura, so its first five
	# frames run backwards are him dissolving back into it, retimed to the length of the blackout.
	&"vanish": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [4, 3, 2, 1, 0], times = [0.11, 0.10, 0.08, 0.08, 0.08], loop = false},
	# And the same five forwards for him reforming, retimed to the length of the lights coming up.
	&"reappear": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [0, 1, 2, 3, 4], times = [0.09, 0.09, 0.10, 0.10, 0.10], loop = false},
	# The same two again, run fast, for the KO's teleport to the middle of the ring. They are their
	# own entries rather than the Demon's beats played short, because a dissolve cut off part-way
	# through looks like a dropped frame. Together they are 0.58 s, which with the 0.37 s turn after
	# them puts the bell 0.95 s after the player goes down.
	&"ko_vanish": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [4, 3, 2, 1, 0], times = [0.07, 0.06, 0.05, 0.05, 0.05], loop = false},
	&"ko_reappear": {sheet = "res://Assets/Characters/Carter/carter_intro.png",
		frames = [0, 1, 2, 3, 4], times = [0.05, 0.05, 0.06, 0.06, 0.08], loop = false},
	# The punish window's pose: hunched and blowing, the one the player punches.
	&"recover": {sheet = "res://Assets/Characters/Carter/carter_spent.png",
		frames = [0, 1, 2, 3], times = [0.2, 0.17, 0.17, 0.2], loop = true},
	&"hit": {sheet = "res://Assets/Characters/Carter/carter_hit.png",
		frames = [0, 1], times = [0.07, 0.09], loop = false},
	# Never advances past frame 5.
	&"defeat": {sheet = "res://Assets/Characters/Carter/carter_defeat.png",
		frames = [0, 1, 2, 3, 4, 5], times = [0.11, 0.11, 0.10, 0.13, 0.18, 0.7], loop = false},
	# Front, pivot, edge-on, then settled with the mark nearly out. These four sum to the generator's
	# IGNITE_MS of 370 ms, which is what puts the bell on frame 4 and not a frame either side.
	&"victory": {sheet = "res://Assets/Characters/Carter/carter_victory.png",
		frames = [0, 1, 2, 3], times = [0.09, 0.07, 0.07, 0.14], loop = false},
	# Frame 4 is the ignition and it is a SNAP, not a ramp: the jump from 3 to 4 is the moment, and
	# smoothing it would steal the sound's cue. Then it burns on a loop under the defeat screen.
	&"victory_hold": {sheet = "res://Assets/Characters/Carter/carter_victory.png",
		frames = [4, 5, 6], times = [0.11, 0.13, 0.13], loop = true},
	# His back stays to the player; only his head comes round, neck cranked, over his RIGHT shoulder,
	# face to screen-right so the earring stays on our side. Never flip_h it: that moves the earring.
	# His feet and his emblem sit exactly where carter_akuma frame 2 has them, so the mark overlay's
	# offset holds on every frame.
	# The burn frames paint the emblem white-hot with bloom and this sheet paints it crisp, so the swap
	# to this sheet happens as the light starts coming up - frame 0, held through KO_LOOK_DELAY - where
	# the lighting change hides it, rather than popping at the start of the turn.
	&"look_back_ready": {sheet = "res://Assets/Characters/Carter/carter_look_back.png",
		frames = [0], times = [1.0], loop = true},
	# 330 ms, and his head arrives on the first frame of the hold. CarterVictory.pose_length() reads
	# this length, so his outro line lands the moment it does.
	&"look_back": {sheet = "res://Assets/Characters/Carter/carter_look_back.png",
		frames = [0, 1, 2], times = [0.12, 0.11, 0.10], loop = false},
	&"look_back_hold": {sheet = "res://Assets/Characters/Carter/carter_look_back.png",
		frames = [3, 4, 5], times = [0.2], loop = true},
	# The Gou Hadou stance, palms cupped at his hip. It plays unseen through the dark and is what the
	# lights come up on: every frame keeps the palm cup on MESSATSU_MUZZLE and his eye slits under
	# MESSATSU_EYES, which is what the ball and the glow in the dark sit on.
	&"messatsu_charge": {sheet = "res://Assets/Characters/Carter/carter_messatsu_charge.png",
		frames = [0, 1, 2, 3], times = [0.12], loop = true},
	# The thrust, the recoil, then the bracing hold, which stays up for the rest of the string. The
	# recoil slides him back inside the frame to keep his palms on MESSATSU_MUZZLE (MESSATSU_RECOIL).
	&"messatsu_fire": {sheet = "res://Assets/Characters/Carter/carter_messatsu_fire.png",
		frames = [0, 1, 2], times = [0.05, 0.05, 0.1], loop = false},
}

# The clones are half his height by the user's own call, so Demon/demon_clone.png is his lunge
# redrawn at 48x48 with its own gather and scatter frames; the full-size carter_rush pair above is
# the Beam Rush, where the one doing the rushing is him.

#HIS AURA
# Drawn UNDER him on its own node, a sibling of his sprite rather than a child: boss.sprite has to
# stay the body sprite, which PlayerFinisher._flash and PlayerCombo._charged_feedback both write to.
const USE_FINAL_AURA := true
const FINAL_AURA := {
	"texture": "res://Assets/Characters/Carter/carter_aura.png",
	"hframes": 6,
	"frame_size": Vector2(96, 96),
	"frame_time": 0.11,
	"scale": 3.0,
}
const AURA_ALPHA := 0.75

#THE MARK ON HIS BACK
# Additive, hidden until the eyes go. Its frame size and its offset inside his 96x96 frame are
# printed by art_source/carter_akuma/build_intro.py; they are copied here rather than guessed.
const USE_FINAL_MARK_GLOW := true
const FINAL_MARK_GLOW := {
	"texture": "res://Assets/Characters/Carter/carter_mark_glow.png",
	"hframes": 6,
	"frame_size": Vector2(64, 54),
	# The glow's top-left texel, on his 96x96 frame. The emblem shrank with him but its bloom box
	# grew, so this moved even though the frame didn't.
	"offset": Vector2(16, 32),
	"frame_time": 0.09,
	"scale": 3.0,
	# The brightest frame of the cycle, by a factor of seven over the dimmest: 747 lit texels against
	# 247 (the 天 mark, 2026-09-23). The KO starts the cycle here so the ignition IS the peak, on the same frame as the bell,
	# instead of snapping on at its faintest and brightening a third of a second later.
	"peak_frame": 3,
	# Once his body is lit, only these. The peaks (3 and 4) spread a dithered wash over his whole upper
	# back, which is exactly right burning alone in the dark and exactly wrong once the point is to
	# show the body under it.
	"lit_frames": [0, 1, 2, 5],
}

#THE GROUND RING HIS ENTRANCE LANDS ON
const USE_FINAL_INTRO_FLASH := true
const FINAL_INTRO_FLASH := {
	"texture": "res://Assets/Characters/Carter/carter_intro_flash.png",
	"frame_size": Vector2(120, 44),
	# Its centre sits on his floor point.
	"pivot": Vector2(60, 22),
	"scale": 3.0,
	"time": 0.45,
}
# The step of `intro` the ring and the mark's glare land on: the stomp, before the pose settles.
const INTRO_FLASH_STEP := 8

#THE DARKNESS
# World-space Node2Ds, NEVER a CanvasLayer: a CanvasLayer would black out the HUD, his health bar
# and the dialogue balloon along with the arena.
# THE LAYERING IS THE EFFECT AND IT INVERTS IF IT IS WRONG. The darkness sits above the floor and the
# crowd but BELOW the fighters, which is what makes the player and the clones read as lit rather than
# as tinted. The player's own stage (MainPlayer) is z 0, so the sequence lifts it to PLAYER_Z while
# it runs and puts it back after: that one write is the only thing this fight does to a node it
# doesn't own, and CarterRagingDemon.release() is what undoes it.
const DARK_Z := 5
const POOL_Z := 6
const PLAYER_Z := 10
const CLONE_Z := 10
# Relative to a clone: its trail one below it, its light well above it.
const CLONE_GHOST_Z := -1
const CLONE_LIGHT_Z := 10
# Relative to the clone layer: the hit and the parry break over everything, the bloom over those.
const BURST_Z := 15
const FINISH_Z := 20

const DARKEN_TIME := 0.35
const CLEAR_TIME := 0.40
const POOL_OPEN_TIME := 0.25
# The pool blooms open from this much of its size.
const POOL_OPEN_FROM := 0.3
# A parry lifts the dark by this much of its alpha for this long, so the hit landing reads through it.
const CURTAIN_PARRY_LIFT := 0.09
const CURTAIN_PARRY_TIME := 0.08

# Drawn at exactly 3x from its top-left corner. Its alpha is already dithered per band - 150 over the
# crowd, 236 over the floor - so nothing may modulate it beyond the ramp in and out.
const USE_FINAL_DARKNESS := true
const FINAL_DARKNESS := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_darkness.png",
	"size": Vector2(640, 360),
	"scale": 3.0,
	# What it settles to over the floor and the sides, which is what the border quads below match.
	"edge_alpha": 0.926,
}
const PLACEHOLDER_DARKNESS := {
	"color": Color(0, 0, 0, 0.86),
}
# The sheet is exactly the view, so a screen shake - a parry's, say - would show an undarkened strip
# at one edge. Black quads fill the border it can be shaken into; only ever a few px of them is on
# screen.
const DARK_BORDER := Rect2(-400, -400, 2720, 1880)
const VIEW_RECT := Rect2(0, 0, 1920, 1080)

# ONE node under the fighters, drawn as light. The pool and the cone also ship split in two, but the
# combined sheet already contains both: never draw the combined one AND the cone, or the shaft is
# laid down twice.
const USE_FINAL_SPOTLIGHT := true
const PLACEHOLDER_SPOTLIGHT := {
	"radii": Vector2(330, 210),
	"points": 28,
	"color": Color(1, 0.95, 0.8, 0.22),
}
const FINAL_SPOTLIGHT := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_spotlight.png",
	# The texel that goes on the player's feet.
	"anchor": Vector2(80, 186),
	"scale": 3.0,
}

#THE CLONES
# MUCH SMALLER THAN CARTER - about half his height and twice the player's - and they materialise out
# of the dark and dissolve back into it rather than appearing and vanishing, the way Akuma's Oboro
# throw does. They have their own frame size and their own feet anchor, not his, and they are drawn
# at a whole 3x: the size comes from the art, never from a fractional scale on a bigger sheet.
# The art is authored dark and translucent, so nothing here tints it - that would double up.
const CLONE_FRAME_SIZE := Vector2(48, 48)
const CLONE_ANCHOR := Vector2(24, 47)
const CLONE_SCALE := 3.0

const USE_FINAL_CLONE := true
# Constant, never ramped: the fade is authored into the frames (100/140/172/196 gathering, 212
# rushing, 186/150/112/72 scattering) and an alpha tween on top of that turns it to mush. This is
# only here to take the whole set down a notch if they read too strongly.
const CLONE_ALPHA := 1.0
# A wraith outline in texels around the feet anchor, for when the sheet is turned off.
const PLACEHOLDER_CLONE := {
	"color": Color(0.14, 0.05, 0.19, 0.82),
	"rim_color": Color(0.66, 0.22, 0.54, 0.9),
	"rim_width": 3.0,
	"shape": [
		Vector2(0, -47), Vector2(5, -43), Vector2(6, -37), Vector2(13, -32), Vector2(12, -21),
		Vector2(16, -9), Vector2(7, -3), Vector2(3, 0), Vector2(-3, 0), Vector2(-7, -3),
		Vector2(-16, -9), Vector2(-12, -21), Vector2(-13, -32), Vector2(-6, -37), Vector2(-5, -43),
	],
}
# Three phases off one 12-frame strip: it gathers out of nothing, holds full strength while it
# commits and travels, then scatters away behind. The gather is 200 ms, which fits inside the FRONT
# of the 0.36 s read window: the clone is fully resolved while the player is still deciding, which is
# the whole reason the window is that long. Never let it creep toward clone_show.
const FINAL_CLONE := {
	"sheet": "res://Assets/Characters/Carter/Demon/demon_clone.png",
	"appear": [0, 1, 2, 3],
	"appear_times": [0.05, 0.05, 0.05, 0.05],
	"rush": [4, 5, 6, 7],
	"rush_time": 0.045,
	"dissipate": [8, 9, 10, 11],
	"dissipate_times": [0.05, 0.05, 0.05, 0.05],
}
# Only the placeholder uses these: the sheet's own frames carry both fades.
const CLONE_FADE_IN := 0.2
const CLONE_PASS_TIME := 0.2

# The trail behind it: four ages of one streak, not four poses. It is 48 texels wider than the clone
# so the tail has room, and it erases the clone's own footprint - it is purely the tail, and the
# clone on top of it provides the figure. Both share clone_sheet_offset(), which is what lines the
# two frames up with no further maths.
const USE_FINAL_CLONE_GHOST := true
const FINAL_CLONE_GHOST := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_clone_ghost.png",
	"hframes": 4,
	"frame_size": Vector2(96, 48),
	"frame_time": 0.055,
	"scale": 3.0,
}

#THE LIGHT OVER A CLONE
# Red means parry it; the fake's mark means don't press, because a parry is punished. The two are timed
# identically, so the only thing separating them is what they look like: red is the same
# diamond-and-exclamation as the game's existing parry tell, the fake a bold pale steel X of its own
# (FINAL_FEINT_TELL), with the yellow ring - the game's dodge tell - standing in until its sheet is
# imported. They differ in silhouette, colour and outline, so the read survives colourblindness. A
# redraw has to keep all of that, not just the hue.
# THE HOLD FRAME IS HELD STEADY FOR THE WHOLE REACTION WINDOW. It must never pulse or loop: a tell
# that flickers gets re-read instead of acted on.
# It sits this far over the clone's head, so its height follows the clone's frame rather than being
# written down: the clones shrank once already. Its own drawn size does NOT follow - it is a tell and
# has to stay big enough to read.
const CLONE_LIGHT_GAP := 34.0
# How far the light reaches above its anchor, which is half its own drawn height. A clone is never
# spawned high enough for this to leave the top of the view: a colour that can't be seen isn't a read.
# The punish clone's light is bigger, so this allows for that one.
const CLONE_LIGHT_REACH := 48.0
# A clone that has gone past takes its light with it this fast. It has to be out before the next
# clone's light comes up, and at a 0.62 s cadence against a 0.54 s clone there are only 0.08 s
# between the two - so this is 0.05, leaving a couple of frames of margin. Two lights up at once and
# the player can't tell which one a press is answering.
const CLONE_LIGHT_OUT := 0.05

# THE CLONE AFTER A FEINT THE PLAYER BIT ON. It cannot be parried or blocked, and the player has to
# be able to see that coming or they will read it as their parry having failed. Until it has frames
# of its own it is the same shape run hot and white, with a light a third bigger that BEATS instead
# of holding steady - the one tell in this fight allowed to move, because it is not a decision, it is
# a sentence already passed.
const PUNISH_CLONE := {
	"tint": Color(2.2, 0.8, 0.85),
	"light_tint": Color(2.4, 1.0, 1.0),
	"light_scale": 1.35,
	"beat": [0.82, 1.18],
	"beat_time": 0.07,
}
const USE_FINAL_CLONE_LIGHT := true
const PLACEHOLDER_CLONE_LIGHT := {
	"red": {"shape": "diamond", "radius": 46.0, "color": Color(1.0, 0.16, 0.2)},
	"yellow": {"shape": "ring", "radius": 46.0, "width": 11.0, "points": 20, "color": Color(1.0, 0.85, 0.15)},
}
const FINAL_CLONE_LIGHT := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_light.png",
	"hframes": 8,
	"frame_size": Vector2(24, 24),
	# The texture's centre, which sits on CLONE_LIGHT_ANCHOR.
	"pivot": Vector2(12, 12),
	"scale": 3.0,
	"red": {"ignite": 0, "peak": 1, "hold": 2, "fade": 3},
	"yellow": {"ignite": 4, "peak": 5, "hold": 6, "fade": 7},
	"ignite_time": 0.05,
	"peak_time": 0.04,
	"fade_time": 0.08,
}
# The fake's own mark, on the lights' own contract and FINAL_CLONE_LIGHT's timings, never tinted. It is
# loaded at run time and only once the editor has imported it (feint_tell), so a checkout without its
# import still runs, on the yellow ring.
const USE_FINAL_FEINT_TELL := true
const FINAL_FEINT_TELL := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_feint.png",
	"hframes": 4,
	"frame_size": Vector2(24, 24),
	"pivot": Vector2(12, 12),
	"scale": 3.0,
	"steps": {"ignite": 0, "peak": 1, "hold": 2, "fade": 3},
}

#WHAT A CLONE LEAVES BEHIND
# Both are drawn as light, on the contact point, which is the player's own hurtbox centre.
# The break is the parry's reward, so it is spawned on the frame the parry resolves, not the one
# after; its first frame is already the full burst.
const USE_FINAL_CLONE_SHATTER := true
const PLACEHOLDER_CLONE_SHATTER := {
	"points": 7,
	"inner_ratio": 0.42,
	"radius": 70.0,
	"color": Color(1.0, 0.94, 0.78),
	"from_scale": 0.4,
	"to_scale": 1.3,
	"time": 0.22,
}
const FINAL_CLONE_SHATTER := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_parry_break.png",
	"hframes": 6,
	"frame_times": [0.04, 0.04, 0.033, 0.033, 0.033, 0.066],
	"frame_size": Vector2(96, 96),
	"pivot": Vector2(48, 48),
	"scale": 3.0,
	"additive": true,
}

# A clone that wasn't stopped: it landed, and this is the hit.
const USE_FINAL_CLONE_HIT := true
const PLACEHOLDER_CLONE_HIT := {
	"radii": Vector2(52, 34),
	"points": 18,
	"color": Color(0.5, 0.3, 0.52, 0.7),
	"from_scale": 0.6,
	"to_scale": 1.25,
	"time": 0.26,
}
const FINAL_CLONE_HIT := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_strike.png",
	"hframes": 6,
	"frame_times": [0.033, 0.033, 0.033, 0.033, 0.033, 0.05],
	"frame_size": Vector2(96, 96),
	"pivot": Vector2(48, 48),
	"scale": 3.0,
	"additive": true,
}

#THE LIGHTS COMING UP
# A 672 px bloom in the middle of the ring, not a screen white-out: what actually blows the screen
# out is the flash rect, stepped alongside it one alpha per frame.
const USE_FINAL_FINISH := true
const FINAL_FINISH := {
	"texture": "res://Assets/Characters/Carter/Demon/demon_finish.png",
	"hframes": 5,
	"frame_times": [0.05, 0.05, 0.083, 0.066, 0.1],
	"frame_size": Vector2(224, 224),
	"pivot": Vector2(112, 112),
	"scale": 3.0,
	"at": Vector2(960, 540),
	"flash": [0.15, 0.45, 0.8, 0.3, 0.06],
}

#THE BEAM RUSH
# His second attack (CarterBeamRush): four clones across the top of the ring charge beams, lock them
# onto the player and fire them, volley after volley, while he waits for his moment to teleport in and
# strike. Their beams are drawn with the Messatsu's sheets and sizes below, all but its surges.
# Their x comes from the inside of the ropes (CarterStateMachine.ROPES) and nowhere else: evenly
# spaced, a fifth of the ring apart.
const BEAM_COUNT := 4
const BEAM_X := [451.0, 790.0, 1128.0, 1467.0]
# Where the four stand, high in the ring: far enough down that a whole 288 px figure is on screen.
const BEAM_CLONE_Y := 300.0
# Relative to the clone layer: each figure over its own aim line, and the ball over the figure's palms.
const BEAM_CLONE_Z := 2
const BEAM_BALL_Z := 3
# They hold his own messatsu_charge and messatsu_fire frames. THEY ARE NOT THE BARRAGE'S CLONES AND
# MUST NEVER BE MISTAKEN FOR THEM: full size, not the 48x48 halflings, and dark and violet, the barrage
# wraith's own colour, so they read as apparitions rather than as four more Carters.
const BEAM_CLONE_TINT := Color(0.42, 0.26, 0.56, 0.88)


#THE MESSATSU
# His third attack (CarterMessatsu): the lights go out, he reappears across the ring charging a beam
# locked onto the player, and he fires it as they come back on - one hit as it lands and one per surge
# after it, six in all, every one of them its own parry.
# THE WIDTH IS THE DODGE. To be clear of the first hit the player's hurtbox has to be 180 + h px off
# the beam's axis, where h = 18|sin| + 40.5|cos| of its angle: 198 to 224 px. In the 0.10 s the head
# takes to arrive, walking covers at most 85 px, a dash started before the fire at most 167 px after
# the aim latches, and a dash whose three frames all fall inside those six frames always clears (231 px
# against 224 at the worst angle, 22.5 degrees). So there is a dodge, about four frames long, and it
# has to be timed before the beam is seen. Above about 373 px it is literally impossible at some
# angles. TO TUNE THE DODGE, CHANGE messatsu_travel, NOT THE WIDTH.
const MESSATSU_HIT_WIDTH := 360.0
# 136 texels at SCALE, of which 120 hurt: 24 px of glow down each side that is light and not damage.
const MESSATSU_DRAW_WIDTH := 408.0
# From his palms to past the far corner of the view, wherever in the ring he fires from.
const MESSATSU_LENGTH := 2240.0
# Closer than this to his palms the aim holds its last angle instead of spinning on the spot.
const MESSATSU_MIN_AIM := 40.0
# The band starts this far BEHIND his palms, so standing on top of him is not a safe spot.
const MESSATSU_BACK := 60.0
# He only turns round during the charge, and only once the player is this far past his centre line,
# so walking across in front of him can't flicker him.
const MESSATSU_FACE_HYSTERESIS := 60.0
const MESSATSU_DARKEN := 0.10
# The flash rect popped over the lights coming back on.
const MESSATSU_FLASH_PEAK := 0.22
const MESSATSU_FLASH_TIME := 0.12
# The Demon's duck: the same room going dark.
const MESSATSU_DUCK_DB := -10.0
const MESSATSU_DUCK_TIME := 0.2
const MESSATSU_MUSIC_BACK := 0.25
const MESSATSU_CHEER := 1.0
# Measured off carter_messatsu_charge and _fire, on frames facing right, and mirrored with him.
# The badge's point is in px from his feet, as the Beam Rush's is: over the centre line of his head,
# which sits right of his feet in the charge pose (x 61, crown on row 29, the aura's tongues up to about
# -261 px).
const MESSATSU_TELL_ANCHOR := Vector2(39, -300)
# The palm cup's gap on all four charge frames and the heels of his palms on fire frames 1 and 2. The
# thrust, fire frame 0, has its palms out at (84, 61), inside the flare.
const MESSATSU_MUZZLE := Vector2(54, 64)
# The corner between his two eye slits, x 52-57 and 64-69 on rows 44-45 of all four charge frames, and
# the gap between them. The glow in the dark is laid on those slits to the texel: at lights-on it hands
# over to them.
const MESSATSU_EYES := Vector2(61, 45)
const MESSATSU_EYE_GAP := 6.0
# The same for the last frame of the lights going out, carter_eye_flash frame 3 until carter_lights_out
# is drawn, where the glow starts: his eyes are flared white across x 34-44 and 51-62 of row 36, with
# pink and red rims above and below and streaks out to the frame's edge. That is about twice as wide as
# the glow's slits, so its halves sit centred on them, their hottest row on the white.
const MESSATSU_LIGHTS_OUT_EYES := Vector2(48, 36)
const MESSATSU_LIGHTS_OUT_EYE_GAP := 12.0
# When he turns in the charge, his eyes slide across in this long, the way a head turns, instead of
# hopping the 78 px from one side of his feet to the other.
const MESSATSU_EYES_TURN := 0.1
# The dark's two middle beats are his eyes': they fade out where he stood, then back in where he has
# gone. Nothing else of him shows until the lights come back.
const MESSATSU_EYES_OUT := 0.28
const MESSATSU_EYES_IN := 0.30
# The fire frames slide him back as he recoils, so his palms stay on MESSATSU_MUZZLE: on the held last
# frame the mass of him is this many texels further back than on carter_spent (x 38 against 49). He is
# handed over to the spent pose moved back by it, rather than popping forward.
const MESSATSU_RECOIL := 11.0
const MESSATSU_FIRE_SHAKE := 12.0
const MESSATSU_FIRE_SHAKE_STEPS := 6
const MESSATSU_FIRE_SHAKE_STEP_TIME := 0.03
const MESSATSU_HIT_SHAKE := 3.0
const MESSATSU_HIT_SHAKE_STEPS := 2
const MESSATSU_HIT_SHAKE_STEP_TIME := 0.03
# Where his feet may land: inside the ropes, and low enough that the badge 300 px over them stays on
# screen. Only where that badge is clear of the HUD, too (CarterMessatsu._tell_clear_at).
const MESSATSU_SPOT_AREA := Rect2(233, 430, 1452, 470)

# The ball gathering in his palms, the eyes that are all that shows of him in the dark, the aim line
# and the lock on the player, the beam, the flare at his palms, its head and the surges that carry hits
# 2 to 6. Each has its sheet below and a flag that brings its placeholder back; the aim line has no
# sheet and is drawn in code.
# THE AIM LINE AND THE LOCK ARE VIOLET, NEVER RED OR YELLOW. Those two colours are this fight's answer
# key, and the only red anywhere in this attack is the badge and the surges' rim.
const USE_FINAL_MESSATSU_BALL := true
const USE_FINAL_MESSATSU_EYES := true
const USE_FINAL_MESSATSU_LOCK := true
const USE_FINAL_MESSATSU_BEAM := true
const USE_FINAL_MESSATSU_FLARE := true
const USE_FINAL_MESSATSU_HEAD := true
const USE_FINAL_MESSATSU_PULSE := true
# Drawn as light, and scaled up from `from_scale` to full over the charge.
const PLACEHOLDER_MESSATSU_BALL := {
	"radius": 42.0,
	"points": 24,
	"color": Color(0.82, 0.55, 1.0),
	"from_scale": 0.3,
}
# Two slits, centred on MESSATSU_EYES and `spacing` px apart.
const PLACEHOLDER_MESSATSU_EYES := {
	"size": Vector2(14, 4),
	"spacing": 20.0,
	"color": Color(1.0, 0.12, 0.12),
}
# Dim and flickering in the dark, solid once the lights are back.
const PLACEHOLDER_MESSATSU_LINE := {
	"width": 6.0,
	"color": Color(0.72, 0.4, 1.0, 0.55),
	"flicker_alpha": 0.3,
	"flicker_time": 0.05,
	"lit_color": Color(0.9, 0.7, 1.0, 0.9),
}
# Contracting on the player over the charge.
const PLACEHOLDER_MESSATSU_RING := {
	"from": 72.0,
	"to": 40.0,
	"width": 4.0,
	"points": 28,
	"color": Color(0.72, 0.4, 1.0, 0.85),
}
# MESSATSU_DRAW_WIDTH across with a hot core down the middle, both drawn as light.
const PLACEHOLDER_MESSATSU_BEAM := {
	"color": Color(0.55, 0.25, 0.9, 0.45),
	"core_color": Color(1.0, 0.92, 1.0, 0.75),
	"core_width": 136.0,
}
const PLACEHOLDER_MESSATSU_FLARE := {
	"radii": Vector2(150, 204),
	"points": 24,
	"color": Color(0.9, 0.7, 1.0, 0.6),
}
const PLACEHOLDER_MESSATSU_HEAD := {
	"radii": Vector2(36, 204),
	"points": 20,
	"color": Color(1.0, 0.92, 1.0, 0.75),
}
const PLACEHOLDER_MESSATSU_PULSE := {
	"size": Vector2(48, 408),
	"color": Color(1.0, 0.35, 0.4, 0.8),
	"core_size": Vector2(20, 136),
	"core_color": Color(1.0, 1.0, 1.0, 0.9),
}
# The sheets, all drawn at SCALE, with `pivot` the texel that sits on the node's origin.
# THE BALL, THE EYES AND THE LOCK ARE LIGHT; THE BEAM, THE FLARE, THE HEAD AND THE SURGES ARE PAINT.
# The first three only ever show in the dark, where light lands as drawn. The other four show over the
# lit green mat, and violet is green's complement: added to it as light it washes to grey and buries
# the parry burst, which read at 4-23% through the core as light against 77-84% as paint.
const FINAL_MESSATSU_BALL := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_ball.png",
	"hframes": 6,
	"frame_size": Vector2(32, 32),
	"pivot": Vector2(16, 16),
	"scale": 3.0,
	"additive": true,
	"frame_time": 0.06,
	"from_scale": 0.3,
}
# The pivot is the point between the slits, and it mirrors with him: the glint is on one eye. Its slits
# are `gap` texels apart where his are MESSATSU_EYE_GAP, so it is split at column `split` and each half
# laid on its own eye.
const FINAL_MESSATSU_EYES := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_eyes.png",
	"hframes": 2,
	"frame_size": Vector2(16, 8),
	"pivot": Vector2(8, 4),
	"split": 8,
	"gap": 2.0,
	"scale": 3.0,
	"additive": true,
	"frame_times": [0.36, 0.06],
}
# Its frames are the lock's progress over the charge, not a loop, and it is drawn at the size it ends
# at: the squeeze down from `from_scale` is on top of them.
const FINAL_MESSATSU_LOCK := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_lock.png",
	"hframes": 6,
	"frame_size": Vector2(32, 32),
	"pivot": Vector2(16, 16),
	"scale": 3.0,
	"additive": true,
	"from_scale": 1.8,
}
# MESSATSU_DRAW_WIDTH across: rows 8 to 127 are the hurting band, with its edge rows the brightest,
# and 8 rows of glow either side. Each frame tiles along the beam on its own and frame k+1 is frame k
# moved 8 texels down it. Region repeat tiles a whole texture, so the frames are cut apart and
# swapped, not stepped.
const FINAL_MESSATSU_BEAM := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_beam.png",
	"hframes": 4,
	"frame_size": Vector2(32, 136),
	"pivot": Vector2(0, 68),
	"scale": 3.0,
	"additive": false,
	"frame_time": 0.05,
}
# The beam's body starts this far past his palms, under the flare's full-width stretch, so its flat end
# never shows. Its texture's columns count from his palms, so its flow carries straight on out of the
# flare's.
const MESSATSU_BEAM_START := 96.0
# The beam's tapered start, out of his palms and pointing down it. It is on the beam's clock: frame k
# of it is frame k of the beam.
const FINAL_MESSATSU_FLARE := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_flare.png",
	"hframes": 4,
	"frame_size": Vector2(64, 144),
	"pivot": Vector2(6, 72),
	"scale": 3.0,
	"additive": false,
	"frame_time": 0.05,
}
# On the beam's front end while it crosses: all three frames show in the 0.10 s it takes.
const FINAL_MESSATSU_HEAD := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_head.png",
	"hframes": 3,
	"frame_size": Vector2(24, 144),
	"pivot": Vector2(5, 72),
	"scale": 3.0,
	"additive": false,
	"frame_time": 0.034,
}
const FINAL_MESSATSU_PULSE := {
	"texture": "res://Assets/Characters/Carter/Messatsu/messatsu_pulse.png",
	"hframes": 3,
	"frame_size": Vector2(20, 136),
	"pivot": Vector2(10, 68),
	"scale": 3.0,
	"additive": false,
	"frame_time": 0.05,
}

# Each take is used the moment its own file exists; until then the fallback stands in for it.
const MESSATSU_SFX := {
	&"charge": {"final": "res://Assets/Audio/SFX/carter_messatsu_charge.wav",
		"fallback": "res://Assets/Audio/SFX/laser_charge.ogg"},
	&"lights_on": {"final": "res://Assets/Audio/SFX/carter_lights_on.wav",
		"fallback": "res://Assets/Audio/SFX/carter_dark.wav"},
	&"fire": {"final": "res://Assets/Audio/SFX/carter_messatsu_fire.wav",
		"fallback": "res://Assets/Audio/SFX/rocket_launch.ogg"},
	&"pulse_1": {"final": "res://Assets/Audio/SFX/carter_messatsu_pulse_1.wav",
		"fallback": "res://Assets/Audio/SFX/carter_rush_1.wav"},
	&"pulse_2": {"final": "res://Assets/Audio/SFX/carter_messatsu_pulse_2.wav",
		"fallback": "res://Assets/Audio/SFX/carter_rush_2.wav"},
	&"pulse_3": {"final": "res://Assets/Audio/SFX/carter_messatsu_pulse_3.wav",
		"fallback": "res://Assets/Audio/SFX/carter_rush_3.wav"},
}
# His rushes standing in for the surges are pitched down under the beam.
const MESSATSU_PULSE_FALLBACK_PITCH := 0.85


static func messatsu_sfx(key: StringName) -> String:
	var sound: Dictionary = MESSATSU_SFX[key]
	if ResourceLoader.exists(sound.final):
		return sound.final
	return sound.fallback


static func messatsu_ball() -> Dictionary:
	return FINAL_MESSATSU_BALL if USE_FINAL_MESSATSU_BALL else PLACEHOLDER_MESSATSU_BALL


static func messatsu_eyes() -> Dictionary:
	return FINAL_MESSATSU_EYES if USE_FINAL_MESSATSU_EYES else PLACEHOLDER_MESSATSU_EYES


static func messatsu_lock() -> Dictionary:
	return FINAL_MESSATSU_LOCK if USE_FINAL_MESSATSU_LOCK else PLACEHOLDER_MESSATSU_RING


static func messatsu_beam() -> Dictionary:
	return FINAL_MESSATSU_BEAM if USE_FINAL_MESSATSU_BEAM else PLACEHOLDER_MESSATSU_BEAM


static func messatsu_flare() -> Dictionary:
	return FINAL_MESSATSU_FLARE if USE_FINAL_MESSATSU_FLARE else PLACEHOLDER_MESSATSU_FLARE


static func messatsu_head() -> Dictionary:
	return FINAL_MESSATSU_HEAD if USE_FINAL_MESSATSU_HEAD else PLACEHOLDER_MESSATSU_HEAD


static func messatsu_pulse() -> Dictionary:
	return FINAL_MESSATSU_PULSE if USE_FINAL_MESSATSU_PULSE else PLACEHOLDER_MESSATSU_PULSE


#HIS BREAK GAUGE (BreakGaugeUI, BossBreakGauge)
# His fight-long Break gauge, hung under his health bar and filled by every parry of all three attacks.
# The art is the game's shared Break gauge chrome in Assets/UI, the same pieces Eric's gauge draws with
# - it is one instrument, not a per-boss redraw - so a redraw of those files is a redraw of both gauges.
# `position` is only a fallback: CarterAkumaScript places it from health_bar.break_gauge_anchor(),
# which is the same point.
# From this share of full it pulses, and this many real seconds for the fill to catch up. At 12.5 a
# parry, 0.8 puts the pulse on the seventh read in a row: one more breaks him.
const USE_FINAL_BREAK_GAUGE := true
const PLACEHOLDER_BREAK_GAUGE := {
	"position": Vector2(770, 96),
	"size": Vector2(380, 10),
	"pulse_from": 0.8,
	"fill_time": 0.15,
	"fill_color": Color(1.0, 0.34, 0.3),
	"pulse_modulate": Color(1.8, 1.8, 1.8),
	"pulse_time": 0.12,
	"locked_modulate": Color(0.5, 0.5, 0.5),
	"shards": 12,
	"shard_size": Vector2(18, 10),
	"shard_speed": Vector2(220, 520),
	"shatter_time": 0.45,
	"word": "BREAK!",
	"word_size": Vector2(380, 60),
	"font_size": 44,
	"outline": 8,
	"word_colors": [Color(1.0, 0.36, 0.3), Color(1, 1, 1)],
	"word_frame_time": 0.08,
	"word_time": 1.0,
	"word_rise": 24.0,
}
const FINAL_BREAK_GAUGE := {
	"position": Vector2(768, 160),
	"size": Vector2(384, 21),
	"pulse_from": 0.8,
	"fill_time": 0.15,
	"frame": "res://Assets/UI/break_gauge_frame_3x.png",
	"fill": "res://Assets/UI/break_gauge_fill_3x.png",
	"fill_offset": Vector2(21, 6),
	"fill_steps": 114,
	"pulse": "res://Assets/UI/break_gauge_pulse_3x.png",
	"pulse_hframes": 4,
	"pulse_offset": Vector2(-18, 0),
	"pulse_frame_times": [0.10, 0.09, 0.11, 0.09],
	"fill_hot": "res://Assets/UI/break_gauge_fill_hot_3x.png",
	"locked_modulate": Color(0.5, 0.5, 0.5),
	"shatter": "res://Assets/UI/break_gauge_shatter_3x.png",
	"shatter_hframes": 6,
	"shatter_offset": Vector2(-24, -36),
	"shatter_frame_times": [0.05, 0.05, 0.06, 0.06, 0.07, 0.07],
	"word_texture": "res://Assets/UI/break_text_3x.png",
	"word_hframes": 2,
	"word_offset": Vector2(84, 27),
	"word_frame_time": 0.08,
	"word_time": 1.0,
	"word_rise": 0.0,
}


static func break_gauge() -> Dictionary:
	return FINAL_BREAK_GAUGE if USE_FINAL_BREAK_GAUGE else PLACEHOLDER_BREAK_GAUGE


# The shared Break sting (BossBroken's), played as his gauge breaks, whenever in an attack that lands.
const BREAK_STING_SFX := {"stream": "res://Assets/Audio/SFX/break_sting.wav", "pitch": 1.0, "volume_db": 0.0}


#HIS JUGGLE (BossJuggled)
# The tiered finisher after a Break: carter_juggle.png, twelve 192x144 frames drawn facing right at 3x.
# Its frame is bigger than his and its origin is not his feet, so it carries its own offset, feet and
# top row, and the juggle owns the sprite's texture, frames and offset for as long as it runs. Top row 48
# is the highest any frame draws (tumble frame 5); the lying frames rest on row 143, the launch frames
# stand a texel higher on 142. The paths are strings, loaded when the juggle runs.
const USE_FINAL_JUGGLE := true
const FINAL_JUGGLE := {
	"texture": "res://Assets/Characters/Carter/carter_juggle.png",
	"hframes": 12,
	"frame_size": Vector2(192, 144),
	"offset": Vector2(0, -71),
	"feet": Vector2(96, 143),
	"tumble_centre": Vector2(96, 94),
	"top_row": 48,
	"clips": {
		&"launch": {"frames": [0, 1], "times": [0.06, 0.08], "loop": false},
		&"tumble": {"frames": [2, 3, 4, 5, 6], "times": [0.16, 0.07, 0.07, 0.07, 0.07], "loop": true},
		&"crash": {"frames": [7, 8, 9], "times": [0.06, 0.08, 0.12], "loop": false},
		&"down": {"frames": [10, 11], "times": [0.4, 0.4], "loop": true},
	},
	"shadow": {
		"texture": "res://Assets/Characters/Carter/carter_leap_shadow.png",
		"hframes": 3, "scale": 3.0, "alpha": 0.35, "step": 100.0, "offset": Vector2.ZERO,
	},
	"lying_time": 0.3,
	"outro_delay": 1.8,
	"crash_sfx": {"stream": "res://Assets/Audio/SFX/hit_impact.ogg", "pitch": 0.7, "volume_db": 0.0},
}


static func juggle() -> Dictionary:
	return FINAL_JUGGLE


#HIS VICTORY POSE
# The mirror of his entrance. He arrives with his back turned and the mark flaring, and he sends the
# player off the same way: back turned, emblem burning between his shoulders, not even watching.
# THE SOUND LANDS ON THE FRAME THE MARK TAKES, not one either side - that is the whole point of the
# beat. That frame is the first of `victory_hold`, so the ignition is simply where `victory` hands
# over, and CarterVictory reads it off the animation's own timing. Retiming the sheet retimes the
# sound with it, with nothing here to keep in step by hand.
# The mark takes hold: the room jolts and the music gets out of the way of the bell. There is no
# screen flash any more - against a fully black arena a white wash reads as a glitch, and the user
# asked for the emblem to be the only thing showing.
const VICTORY_SHAKE := 12.0
const VICTORY_SHAKE_STEPS := 5
const VICTORY_SHAKE_STEP_TIME := 0.035
# The track fades out under the bell rather than ducking and coming back - this is the end of the
# fight, and his lines land in the quiet after the ring.
const VICTORY_MUSIC_FADE := 1.4
const VICTORY_CHEER := 3.0

# He doesn't walk to the middle, he is simply there: the Demon's own vanish and reappear, so it reads
# as his technique rather than as the fight repositioning him.
# Then the arena goes ALL the way down - no spotlight, no dithered bands, just black. It is its own
# quad rather than the darkness sheet turned up, because that sheet's alpha is baked per band and
# tops out at 0.93, and "nearly black" with the crowd faintly showing is not what was asked for.
# The blackout finishes exactly on the ignition, so the world darkens around him while he turns and
# the mark lights the instant he is gone into it.
const KO_BLACKOUT_TIME := 0.5
# Relative to DarkStage, so the blackout ends up over every fighter, hazard and burst in the world.
const KO_BLACK_Z := 30
# Where he is drawn for the KO's teleport: over the barrage's darkness (DARK_Z) and its pool (POOL_Z)
# so it reads in the dark, and under the blackout so the blackout still takes him.
const KO_TELEPORT_Z := 8
# Absolute, and above that: the emblem has to be the one lit thing left on screen.
const KO_MARK_Z := 40
# At its usual size the emblem is 192x162 px alone in a 1920x1080 frame, which reads as a speck. For
# this beat and no other it is drawn twice that, scaled about its own centre so it doesn't drift off
# his back.
const KO_MARK_SCALE := 2.0

# THEN THE LIGHT COMES BACK ON HIM. The emblem burns alone for KO_HOLD_TIME - the moment the user
# picked out as the one to keep - and then the Demon's own spotlight comes up on him and he looks
# back over his shoulder at them, back still turned.
const KO_HOLD_TIME := 2.0
const KO_LIGHT_TIME := 0.6
# A breath after he is lit before his head comes round, so the body registers before the look does.
const KO_LOOK_DELAY := 0.25
# The draw order once he is lit, all over the blackout: the light on the black, him on the light, the
# emblem on him. The arena stays gone - the light is drawn on the blackout, not cut out of it, so the
# pool lands on black rather than bringing the mat back.
const KO_LIGHT_Z := 36
const KO_BODY_Z := 38
# Twice its size was right alone in the dark and is wrong on a lit body - it would be bigger than his
# torso - so once he is lit it settles back to its own size on his back. It is drawn additively over
# the emblem the sheet already paints there, so it comes down in strength too or the two stack into a
# white smear.
const KO_LIT_MARK_ALPHA := 0.7

#HIS MUSIC
# The user's own track, kept out of the repo for the same reason as the KO bell below. A fresh clone
# gets the placeholder theme and still has music to fight to.
# THE LEVEL IS MEASURED, NOT GUESSED (art_source/carter_fight/measure_theme.gd plays each one through
# a capture bus): the track peaks at -1.1 dBFS and its busiest stretch runs -9.6 dBFS RMS, which is
# 4.8 dB hotter than the placeholder it replaces. At -12 dB it sits about 2 dB under where the
# placeholder sat, and that is where it has to be - this fight is a reaction test played over
# constant sound, and the clone rushes (-25.7 RMS) and the parry break have to stay on top of it.
# IT IS A TRACK, NOT A LOOP, AND IT OPENS ON FOUR SECONDS OF DIGITAL SILENCE. Measured: 0 s, 2 s and
# 3 s are all -100 dBFS, a lead-in starts around 4 s and it is at full level by 5 s. Played from the
# top, the fight would begin with four seconds of nothing, so it starts - and loops back to - the
# lead-in instead. Both numbers are the same one on purpose.
# The tail fades out from about 260 s into silence by 263 s, so the loop seam is a fade into a
# lead-in rather than a stutter. The file is 4:26 and a fight lasts 35-90 s, so that seam is almost
# never reached anyway. Nothing here compensates for the MP3's encoder delay or padding: Godot 4.6
# strips both itself (it reports the file as 266.043 s, which is its raw 266.088 s less exactly the
# 576 + 1601 samples the Lavc header declares), so the 3.9 s above is 3.9 s of music time.
const MUSIC_LOCAL := {
	"stream": "res://Assets/Audio/SFX/local/carter_theme_local.mp3",
	"volume_db": -12.0,
	"start": 3.9,
	"loop_offset": 3.9,
}
# "The Mark Burns", written for this fight - see art_source/music/carter_theme.rb. One 16-bar cycle
# cut to the beat, so it needs no lead-in and no loop offset: the seam is the bar line. This is what
# a fresh clone hears, and it is ours, unlike the local reference track above.
const MUSIC_FALLBACK := {
	"stream": "res://Assets/Audio/Music/carter_theme.wav",
	"volume_db": -7.0,
	"start": 0.0,
	"loop_offset": 0.0,
}


# His own track when it is there, ours when it isn't.
static func theme() -> Dictionary:
	if ResourceLoader.exists(MUSIC_LOCAL.stream):
		return MUSIC_LOCAL
	return MUSIC_FALLBACK


#THE KO
# The user's own sound, kept out of the repo: Assets/Audio/SFX/local/ is gitignored, because those
# rights aren't ours to redistribute and the repo is public. A fresh clone won't have it and still
# has to have a cue, so the synthesised bell stands in.
# Both are levelled to land around -3 dBFS, so swapping one for the other doesn't move the mix: the
# local file is a mastered sample near full scale, the bell peaks at -6.
# LET IT RING. The bell is 1.43 s and the user's file is longer; nothing may cut it short. The only
# thing that touches it is FightOutro's fade at the end of the outro, which is a fade, not a stop.
const KO_DING_LOCAL := "res://Assets/Audio/SFX/local/carter_ko_local.mp3"
const KO_DING_FALLBACK := "res://Assets/Audio/SFX/carter_ko_ding.wav"
const KO_DING_LOCAL_DB := -3.0
const KO_DING_FALLBACK_DB := 3.0


# The stream is the user's own when it is there, the synthesised bell when it isn't.
static func ko_ding() -> Dictionary:
	if ResourceLoader.exists(KO_DING_LOCAL):
		return {"stream": KO_DING_LOCAL, "volume_db": KO_DING_LOCAL_DB}
	return {"stream": KO_DING_FALLBACK, "volume_db": KO_DING_FALLBACK_DB}


#THE YANK
# The ghosts of the player dragged to the middle, and the dust where they land. PlayerCombatFx draws
# its own trail for warp_to(), but this yank is a drive rather than a blink, so it leaves its own.
const YANK_GHOSTS := 3
const YANK_GHOST_TINT := Color(0.72, 0.5, 1.0, 0.55)
const YANK_GHOST_FADE := 0.22
const YANK_DUST := {
	"radii": Vector2(120, 42),
	"points": 20,
	"color": Color(0.86, 0.8, 0.92, 0.5),
	"from_scale": 0.35,
	"to_scale": 1.3,
	"time": 0.3,
}

#THE FEINT PUNISH
# Its own word over his health bar rather than a PlayerDefense popup: the popup set is the defence
# coder's, and a word only this fight says doesn't belong in it.
const WORD_CENTRE := Vector2(960, 300)
const WORD_TIME := 0.9
const WORD_FONT_SIZE := 92
const WORD_COLOR := Color(1.0, 0.36, 0.3)
const WORD_OUTLINE := 10
const WORD_FROM_SCALE := 0.7
const WORD_TO_SCALE := 1.0
const WORD_GROW_TIME := 0.16
# The red pulse that runs the screen edge with it.
const EDGE_PULSE := {
	"color": Color(1.0, 0.15, 0.15, 0.55),
	"thickness": 90.0,
	"time": 0.35,
}


static func anim(anim_name: StringName) -> Dictionary:
	if USE_FINAL_ANIMS.get(anim_name, false):
		return FINAL_ANIMS[anim_name]
	return PLACEHOLDER_ANIMS[anim_name]


# Seconds from the start of an animation to the start of its frame at `step`.
static func time_to_step(anim_name: StringName, step: int) -> float:
	var times: Array = anim(anim_name).times
	var total := 0.0
	for i in step:
		total += times[mini(i, times.size() - 1)]
	return total


# Sprite offset, in texels, that puts ANCHOR on the sprite's origin.
static func sheet_offset(frame_size: Vector2) -> Vector2:
	return frame_size / 2.0 - ANCHOR


# Screen-px offset from his feet of a point on his frames. Mirroring flips the texel column, so a
# point measured on a pose follows that pose when it faces the other way.
static func local(point: Vector2, flipped := false) -> Vector2:
	var column: float = (FRAME_SIZE.x - 1.0 - point.x) if flipped else point.x
	return (Vector2(column, point.y) - ANCHOR) * SCALE


static func local_rect(rect: Rect2) -> Rect2:
	return Rect2(local(rect.position), rect.size * SCALE)


# Sprite offset, in texels, for an effect sheet drawn at `offset` inside his 96x96 frame.
static func inset_offset(frame_size: Vector2, offset: Vector2) -> Vector2:
	return frame_size / 2.0 - (ANCHOR - offset)


# Where the emblem is actually drawn, in px from his feet. Scaling it for the KO has to happen about
# this point or it slides off his back.
static func mark_centre() -> Vector2:
	return local(FINAL_MARK_GLOW.offset + FINAL_MARK_GLOW.frame_size / 2.0)


# Sprite offset, in texels, that puts CLONE_ANCHOR on a clone's origin.
static func clone_sheet_offset() -> Vector2:
	return CLONE_FRAME_SIZE / 2.0 - CLONE_ANCHOR


# Over the clone's head, which is the top row of its own frame.
static func clone_light_anchor() -> Vector2:
	return Vector2(0, -CLONE_ANCHOR.y * CLONE_SCALE - CLONE_LIGHT_GAP)


# The placeholder wraith, in px around its feet.
static func clone_shape() -> PackedVector2Array:
	var shape := PackedVector2Array()
	for point in PLACEHOLDER_CLONE.shape:
		shape.append(point * CLONE_SCALE)
	return shape


static func clone_light() -> Dictionary:
	return FINAL_CLONE_LIGHT if USE_FINAL_CLONE_LIGHT else PLACEHOLDER_CLONE_LIGHT


# The fake's mark once its sheet has been imported; an empty spec until then, for the yellow ring.
static func feint_tell() -> Dictionary:
	if USE_FINAL_FEINT_TELL and ResourceLoader.exists(FINAL_FEINT_TELL.texture):
		return FINAL_FEINT_TELL
	return {}


# A clone and the light over its head, around its feet: the light at the punish clone's size, the
# bigger of the two.
static func clone_drawn_rect() -> Rect2:
	var body := Rect2(-CLONE_ANCHOR * CLONE_SCALE, CLONE_FRAME_SIZE * CLONE_SCALE)
	var reach := Vector2.ONE * CLONE_LIGHT_REACH
	return body.merge(Rect2(clone_light_anchor() - reach, reach * 2.0))


# Whether something drawn at `rect` is wholly in view and clear of every HUD block.
static func clear_of_hud(rect: Rect2) -> bool:
	if not VIEW_RECT.grow(-HUD_CLEARANCE).encloses(rect):
		return false
	for keep_out in HUD_KEEP_OUT:
		if keep_out.grow(HUD_CLEARANCE).intersects(rect):
			return false
	return true


# The first of `anchors` whose badge would be clear of the HUD; the first of them if none would be.
static func clear_tell_anchor(anchors: Array) -> Vector2:
	for anchor: Vector2 in anchors:
		if clear_of_hud(Rect2(anchor + TELL_BADGE.position, TELL_BADGE.size)):
			return anchor
	return anchors[0]


static func clone_shatter() -> Dictionary:
	return FINAL_CLONE_SHATTER if USE_FINAL_CLONE_SHATTER else PLACEHOLDER_CLONE_SHATTER


static func clone_hit() -> Dictionary:
	return FINAL_CLONE_HIT if USE_FINAL_CLONE_HIT else PLACEHOLDER_CLONE_HIT


static func spotlight() -> Dictionary:
	return FINAL_SPOTLIGHT if USE_FINAL_SPOTLIGHT else PLACEHOLDER_SPOTLIGHT


# A filled ellipse, points on its rim, centred on the origin.
static func ellipse(radii: Vector2, points: int) -> PackedVector2Array:
	var rim := PackedVector2Array()
	for i in points:
		var angle := TAU * i / points
		rim.append(Vector2(cos(angle) * radii.x, sin(angle) * radii.y))
	return rim


# A star, for the placeholder bursts: `points` spikes out to `radius`, the dips at `inner_ratio` of it.
static func star(points: int, radius: float, inner_ratio: float) -> PackedVector2Array:
	var shape := PackedVector2Array()
	for i in points * 2:
		var angle := TAU * i / (points * 2) - PI / 2.0
		var reach := radius if i % 2 == 0 else radius * inner_ratio
		shape.append(Vector2(cos(angle), sin(angle)) * reach)
	return shape


# The four corners of a rect, for the darkness and its border.
static func rect_polygon(rect: Rect2) -> PackedVector2Array:
	return PackedVector2Array([
		rect.position, Vector2(rect.end.x, rect.position.y), rect.end,
		Vector2(rect.position.x, rect.end.y),
	])


# The border the view can be shaken into: DARK_BORDER with the view cut out of it.
static func border_rects() -> Array[Rect2]:
	var whole := DARK_BORDER
	var hole := VIEW_RECT
	return [
		Rect2(whole.position, Vector2(whole.size.x, hole.position.y - whole.position.y)),
		Rect2(Vector2(whole.position.x, hole.end.y), Vector2(whole.size.x, whole.end.y - hole.end.y)),
		Rect2(Vector2(whole.position.x, hole.position.y), Vector2(hole.position.x - whole.position.x, hole.size.y)),
		Rect2(Vector2(hole.end.x, hole.position.y), Vector2(whole.end.x - hole.end.x, hole.size.y)),
	]


# The mark's glow, the spotlight and every burst in the sequence are drawn as light, not as paint:
# flat bright shapes that have to add to what is under them rather than cover it.
static func additive() -> CanvasItemMaterial:
	var material := CanvasItemMaterial.new()
	material.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return material


# The placeholder red light: a solid diamond standing on its bottom point, which is the pivot.
static func diamond(radius: float) -> PackedVector2Array:
	return PackedVector2Array([
		Vector2(0, -radius * 2.0), Vector2(radius, -radius), Vector2(0, 0), Vector2(-radius, -radius),
	])
