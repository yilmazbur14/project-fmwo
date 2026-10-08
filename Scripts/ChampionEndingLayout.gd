extends RefCounted

# Every number the champion ending plays on (ChampionEndingScript, ChampionCredits): where it goes, its song and the beat
# sheet on that song's own clock, the staging in the ring, the sounds, the art behind its USE_FINAL_* flags, and the
# credits. No preloads, so anything - god.gd's defeat included - can preload this without pulling the ending in.
#
# THE BEAT SHEET IS IN SONG SECONDS. The ending runs on the song's own clock (ChampionEndingScript.music_time), so every
# time below is where the song is as heard, not frames since the scene loaded. They were read off the user's track by
# decoding it: a near-silent breath at 7.40, a slam at 7.78, and the beat doubling on a 1.2 s bar grid from 7.80 - so
# 9.00, 11.40, 15.00 and 17.40 are bar lines, and the big beats sit on them.
#
# THE STAGING is the approved art's (art_source/champion_ending/contract.json, 2026-10-06; the user picked take A, the
# Glove Cup). The trophy waits on its stand in the middle of the ring, over the centre crest. The player comes in
# through the top gate, the one the walk-out left by, walks down toward the camera facing it all the way, and stops at
# MARK, just north of the stand, which hides him from the waist down until the lift. Every lift sheet is 40x64-texel
# cells with the player's own 32x32 cell at (4, 21) in each, drawn the contract's way: a Sprite2D on MARK, centred, at
# SCALE, offset CELL_OFFSET - which puts cell texel CELL_CENTRE on MARK. Points on the art below are cell texels.

const SCALE := 3.0

#WHERE IT GOES
# After god-Jordan's defeat the game ends here rather than on TO BE CONTINUED. A static var so the defence suite can turn
# it off for a run (jordan_god). ON since the build (2026-10-06, "wire new work promptly").
static var USE_CHAMPION_ENDING := true
const ENDING_SCENE := "res://Scenes/Core/ChampionEndingScene.tscn"
const CARD_SCENE := "res://Scenes/Core/ToBeContinuedScene.tscn"
const MENU_SCENE := "res://Scenes/Core/MainMenuScene.tscn"
const ARENA_SCENE := "res://Scenes/Core/ArenaScene.tscn"
# The arena's own nodes the ending has no use for, freed before it enters the tree: with no PauseMenu, a short ESC tap
# does nothing.
const ARENA_DROPS: Array[String] = ["MainPlayer", "VsCard", "PauseMenu"]

#THE SONG
# "Universal Collapse" by DM DOKURO, the user's own MP3, kept in Assets/Audio/SFX/local/, which is gitignored: those
# rights aren't ours and the repo is public. A fresh clone doesn't have it, and then our own "Main Character Energy"
# plays instead (it loops by its import), on a scene clock started with it.
# THE LEVEL IS MEASURED (decoded offline, K-weighted per BS.1770, ungated, mono fold-down): the song's body from the drop
# on is -9.4 LUFS and its intro -14.1, mastered hot (peaks +2 dBFS). God-Jordan's fight, which this follows, plays Neo
# Tokyo at -12 dB, where it sits at -19.0. At -9 dB this one's body sits at -18.4, level with it and a touch over, and
# the drop lands about 5 dB over the intro under it.
# MUSIC_LOCAL_LENGTH is the file it was measured on: a different track dropped in at this path keeps the beat sheet's
# times, which were read off this one.
static var MUSIC_LOCAL := "res://Assets/Audio/SFX/local/champion_theme_local.mp3"
const MUSIC_LOCAL_DB := -9.0
const MUSIC_LOCAL_LENGTH := 256.55
const MUSIC_FALLBACK := "res://Assets/Audio/Music/burak_theme.wav"
const MUSIC_FALLBACK_DB := -4.0
# The music under the announcement, and back to full on the name.
const MUSIC_DUCK_DB := -4.0
const MUSIC_DUCK_TIME := 0.4
const MUSIC_BACK_TIME := 0.15
const SILENT_DB := -60.0

#THE BEATS (song seconds)
# The lift's peak, the user's "9/10 s" where the beat doubles: the art's DROP frame (lift) first shows on it. One knob:
# everything before it clamps to fit, so a DROP_TIME of 7.78 (the slam) brings the grab and the arrival forward.
static var DROP_TIME := 9.00
# The grab on the slam, after the take-in and the reach in the breath before it.
const GRIP_TIME := 7.78
const HUSH_AT := 7.40
const ARRIVE_AT := 6.90
# The lift's frames, the art's (contract.json, champion_frames), and how long each holds: arrive, the reach and the
# grab in, then the gather pair looping until the drop - it soaks up whatever time is left, at least MIN_GATHER of it -
# lift on the drop, settle, and the hold loop.
const LIFT_FRAMES: Array[StringName] = [&"arrive", &"take_in", &"reach", &"grab", &"gather_a", &"gather_b", &"lift",
	&"settle", &"hold_1", &"hold_2", &"hold_3", &"hold_4"]
const ARRIVE_HOLD := 0.30
const TAKE_IN_TIME := 0.40
const REACH_TIME := 0.15
const GRAB_TIME := 0.25
const GATHER_STEP := 0.10
const MIN_GATHER := 0.20
const LIFT_HOLD := 0.10
const SETTLE_HOLD := 0.10
const HOLD_STEP := 0.20
const FADE_IN := 2.0
const EARLIEST_WALK := 2.2
const GATE_LEAD := 0.5
const WALK_PACE := 180.0
# The player's own walk (row 0, columns 0-4), at its own pace (StoryPlayer.WALK_FRAME_TIME), as the contract asks.
const WALK_FRAME_TIME := 1.0 / 6.0
const SETTLE_AT := 11.40
const ANNOUNCE_AT := 11.60
const ANNOUNCE_SPEED := 0.6
# Where the name would be: the biggest roar of the scene. The balloon holds NAME_HOLD through it and closes.
const NAME_AT := 15.00
const NAME_HOLD := 1.2
const FADE_AT := 17.40
const FADE_TIME := 6.0
# A held ESC in the cutscene: to black this fast (or what's left of a fade already under way), and on to the credits.
const SKIP_FADE := 0.6
# The appear cheer, once the player's soles cross APPEAR_Y.
const APPEAR_CHEER := 2.0
# A sparkle on the cup this often through the hold.
const SPARKLE_EVERY := 1.2


static func grip_time() -> float:
	return minf(GRIP_TIME, DROP_TIME - MIN_GATHER - GRAB_TIME)


static func reach_time() -> float:
	return grip_time() - REACH_TIME


static func take_in_time() -> float:
	return reach_time() - TAKE_IN_TIME


# The song's breath, never after the grab, so the gather's rising murmur always follows the hush.
static func hush_time() -> float:
	return minf(HUSH_AT, grip_time())


# On the mark showing the arrive frame for at least ARRIVE_HOLD.
static func arrive_time() -> float:
	return minf(ARRIVE_AT, take_in_time() - ARRIVE_HOLD)


# The walk is scheduled to arrive at arrive_time(): it starts `distance` / WALK_PACE before, but never before
# EARLIEST_WALK, and a walk that would have to then goes a little faster instead.
static func walk_start(distance: float) -> float:
	return maxf(arrive_time() - distance / WALK_PACE, EARLIEST_WALK)


static func walk_pace(distance: float) -> float:
	return distance / maxf(arrive_time() - walk_start(distance), 0.001)


# The lift's frame at song time `t` (LIFT_FRAMES), or &"" before the arrival.
static func lift_frame_at(t: float) -> StringName:
	if t < arrive_time():
		return &""
	if t < take_in_time():
		return &"arrive"
	if t < reach_time():
		return &"take_in"
	if t < grip_time():
		return &"reach"
	if t < grip_time() + GRAB_TIME:
		return &"grab"
	if t < DROP_TIME:
		return &"gather_a" if int((t - grip_time() - GRAB_TIME) / GATHER_STEP) % 2 == 0 else &"gather_b"
	if t < DROP_TIME + LIFT_HOLD:
		return &"lift"
	if t < DROP_TIME + LIFT_HOLD + SETTLE_HOLD:
		return &"settle"
	return LIFT_FRAMES[8 + int((t - DROP_TIME - LIFT_HOLD - SETTLE_HOLD) / HOLD_STEP) % 4]


static func own_track() -> bool:
	return ResourceLoader.exists(MUSIC_LOCAL)


static func after_jordan_god() -> String:
	if USE_CHAMPION_ENDING and ResourceLoader.exists(ENDING_SCENE):
		return ENDING_SCENE
	return CARD_SCENE


#THE STAGING (screen px)
# Where the contract's sheets go (its mark, which puts the stand on the centre crest), and so where the player stops:
# their soles, StoryPlayer's origin, are cell texel CELL_SOLES - the player cell's (16, 29) - which is LIFT_MARK.
const MARK := Vector2(960, 495)
const CELL := Vector2(40, 64)
const CELL_OFFSET := Vector2(0, -5)
const CELL_CENTRE := Vector2(20, 37)
const CELL_SOLES := Vector2(20, 50)
const LIFT_MARK := MARK + (CELL_SOLES - CELL_CENTRE) * SCALE
const ENTRY_POINT := Vector2(960, -30)
# A test's own start spot (INF for ENTRY_POINT). It must be behind the stand: y under LIFT_MARK.y.
static var entry_override := Vector2.INF
const APPEAR_Y := 0.0
# The middle of the player and the cup overhead, for the camera.
const FOCUS := Vector2(960, 470)
# The camera: pushed in from the arrival to the drop, punched in on the drop and on the name, and eased out on the fade.
const PUSH_ZOOM := 1.3
const DROP_ZOOM := 1.45
const DROP_PUNCH := 0.08
const DROP_SETTLE := 1.0
const NAME_ZOOM := 1.38
const NAME_PUNCH := 0.08
const NAME_SETTLE := 0.8
const FADE_ZOOM := 1.1
# Shakes: [px, steps, seconds a step].
const GRIP_SHAKE := [4.0, 3, 0.04]
const DROP_SHAKE := [10.0, 6, 0.04]
const NAME_SHAKE := [8.0, 6, 0.04]
# The arena dimmed under the actors until the drop, over whatever a shake can pull into view.
const DIM_ALPHA := 0.55
const DIM_BORDER := Rect2(-1920, -1080, 5760, 3240)
const DIM_LIFT := 0.15
# The stand-in's white flash on the drop.
const FLASH_ALPHA := 0.55
const FLASH_TIME := 0.35
# Draw order in the world: the dim, the lights, the art's spot sweep, its lift flash (under the player, so the cup stays
# readable), the actors, and the fx over everything. Inside the actors, the stand and the cup over the player - who is
# north of them - and the cup under the player once it is overhead.
const DIM_Z := 5
const LIGHTS_Z := 6
const SPOT_SWEEP_Z := 7
const LIFT_FLASH_Z := 8
const ACTORS_Z := 10
const FX_Z := 20
const WALKER_Z := 0
const STAND_Z := 1
const TROPHY_OVER_Z := 2
const TROPHY_UNDER_Z := -1
# Canvas layers (the dialogue balloon is 100, BossEntrance's hint 90).
const CONFETTI_LAYER := 70
const FLASH_LAYER := 80
const FADE_LAYER := 120
const CREDITS_LAYER := 124
const CREDITS_SKIP_LAYER := 125


# A cell texel's top-left corner on screen, the contract's sheets drawn on MARK.
static func at_cell(texel: Vector2) -> Vector2:
	return MARK + (texel - CELL_CENTRE) * SCALE


#THE LIGHTS
# Carter's Demon spotlight, drawn as light, its anchor texel on whoever it lights: one on the stand from the start, and
# a follow-spot under the player's soles through the walk, gone on the arrival. Both go out on the drop.
const SPOTLIGHT := {texture = "res://Assets/Characters/Carter/Demon/demon_spotlight.png", anchor = Vector2(80, 186)}
const PLACEHOLDER_SPOTLIGHT := {radii = Vector2(330, 210), points = 28, color = Color(1, 0.95, 0.8, 0.22)}
const FOLLOW_FADE := 0.5
const SPOTS_OUT := 0.15
# The light was drawn for Carter's near-black stage; under this lighter dim it is let down, or it blows out the player.
const SPOT_ALPHA := 0.6

#THE ANNOUNCER
# Unseen: the normal dialogue balloon, no portrait, a voice of its own (DialogueVoices "???"). The input lock is longer
# than the line, so no press can advance or skip it.
const ANNOUNCER_NAME := "???"
const ANNOUNCER_LINE := "And announcing your new discord champion of this server...."
const ANNOUNCER_INPUT_LOCK := 60.0

#THE SOUNDS
# Each sound's own file once it is in and imported (art_source/audio_champion/make_champion_sfx.py makes them), at
# volume_db; until then its stand-in layers, each at its own level, pitch and offset. A level set on a sound later (the
# hush, the gather, the name) is a final level: a stand-in layer keeps its own trim against it. The files are made to
# play exactly as loud as their stand-ins at these levels; the roar and the pop sit higher than their stand-ins' so
# their files stay under -1 dBFS (the master bus's limiter catches the sum). The script keeps the same numbers.
const SFX_DIR := "res://Assets/Audio/SFX/"
const CROWD_CHEER := SFX_DIR + "crowd_cheer.wav"
const SOUNDS := {
	&"murmur": {final = SFX_DIR + "champion_murmur_loop.wav", volume_db = -16.0, loop = true,
		stand_in = [{stream = CROWD_CHEER, volume_db = -22.0, pitch = 0.7, at = 0.0}]},
	&"appear": {final = CROWD_CHEER, volume_db = -8.0, loop = false, stand_in = []},
	&"roar": {final = SFX_DIR + "champion_roar.wav", volume_db = 3.0, loop = false,
		stand_in = [{stream = CROWD_CHEER, volume_db = 1.0, pitch = 0.94, at = 0.0},
			{stream = CROWD_CHEER, volume_db = 1.0, pitch = 1.0, at = 0.15},
			{stream = CROWD_CHEER, volume_db = 1.0, pitch = 1.07, at = 0.3}]},
	&"cheer_loop": {final = SFX_DIR + "champion_crowd_loop.wav", volume_db = -8.0, loop = true,
		stand_in = [{stream = CROWD_CHEER, volume_db = -8.0, pitch = 1.0, at = 0.0}]},
	&"pop": {final = SFX_DIR + "champion_confetti_pop.wav", volume_db = -9.0, loop = false,
		stand_in = [{stream = SFX_DIR + "burak_blast.wav", volume_db = -12.0, pitch = 1.6, at = 0.0}]},
}
# The murmur through the beats (final levels): hushed in the breath, climbing through the gather, gone into the roar.
const MURMUR_HUSH_DB := -26.0
const MURMUR_HUSH_TIME := 0.3
const MURMUR_STRAIN_DB := -14.0
const MURMUR_OUT := 0.3
# The cheer loop dropped to the murmur's level for the announcement, and up for the name, where the roar is louder too.
const CHEER_SETTLE_TIME := 0.4
const NAME_CHEER_DB := -6.0
const NAME_ROAR_BOOST := 3.0

#THE STAND-IN CONFETTI AND THE CROWD'S CAMERAS
# Until the art's fx are on: two cannons from below the frame, angled in, firing 1x2-texel bits; a pop of bits off the
# cup's top; and the Victory screen's full-screen shower fading in over it all. The cameras flashing in the crowd bands
# while the crowd is up are code on both paths: the band over the ring, and the ringside's edges.
const CANNONS := [Vector2(300, 1000), Vector2(1620, 1000)]
const CANNON := {amount = 90, lifetime = 3.2, explosiveness = 0.92, lean = 18.0, spread = 12.0,
	velocity = Vector2(1250, 1650), gravity = 700.0, damping = Vector2(160, 220), spin = 540.0, bit = Vector2(1, 2)}
const TROPHY_POP := {amount = 26, lifetime = 0.9, velocity = Vector2(160, 320), spread = 70.0, gravity = 520.0,
	bit = Vector2(1, 1)}
const CONFETTI_COLORS: Array[Color] = [Color("fbf236"), Color("ac3232"), Color("2464bd"), Color("3883c9"),
	Color("eeeae0"), Color("99e550"), Color("d95763")]
const POP_COLORS: Array[Color] = [Color("fff4a3"), Color("fbd23c"), Color("ffffff")]
const SHOWER := {sheet = "res://Assets/UI/Screens/victory_confetti.png", frames = 4, frame_time = 0.12, fade = 0.4}
const CROWD_BANDS: Array[Rect2] = [Rect2(0, 6, 1920, 102), Rect2(0, 1053, 1920, 27), Rect2(0, 120, 27, 933),
	Rect2(1890, 120, 30, 933)]
const FLASH_POPS := {per_second = 7.0, size = 2.0, life = 0.12, color = Color(1, 1, 1, 0.95)}

#THE ART (contract.json; approved 2026-10-06, "approve all, glove cup, reveal is fine")
# Final art goes up only once the user has approved it and its flag is on, and it still plays its stand-in until its
# file is in and the editor has imported it (the final_* functions below), decided once as the scene is built. Static
# vars, so the defence suite can play either path (champion_ending's art and stand_in tiers). ON since the user's
# approval, 2026-10-06, all but the burst below.
static var USE_FINAL_CHAMPION := true
static var USE_FINAL_FX := true
static var USE_FINAL_CROWD_ROAR := true
static var USE_FINAL_CREDITS_ART := true
# The confetti burst on a flag of its own: first shipped as one 17920 px row, past the 16384 px a GPU texture can be, it
# couldn't load. Re-cut as a 7x4 grid (2026-10-06), it does; off, the stand-in cannons and pop fire in its place.
static var USE_FINAL_BURST := true

# The cup waiting on its stand through the walk-in, an 11-frame shine loop on the frame clock, over the player; and on
# the arrival, the lift itself: 12 frames, stand, player, cup, his grip and the effects baked in that order, frame 0
# pixel-identical to the player's idle beside the waiting cup, so the swap doesn't show. Its frames are LIFT_FRAMES, on
# the song's clock.
const CHAMPION := {lift = "res://Assets/Characters/MainPlayer/player_trophy_lift.png",
	stand_idle = "res://Assets/Environment/Champion/champion_trophy_stand_idle.png",
	stand_idle_times = [0.6, 0.05, 0.05, 0.05, 0.05, 0.05, 0.35, 0.06, 0.08, 0.06, 0.45]}
# The cup, take A (17x16): where its bottom centre is on each lift frame (on the stand's seat through gather_a, a texel
# up on gather_b, overhead from the drop, swaying through the hold), whether it is still on the stand (drawn over the
# player) or overhead (under him, so his grip draws over its base), its anchor - its bottom centre on its own image -
# and the texel its highlight sparkles off.
const TROPHY_BOTTOM := {&"arrive": Vector2(19, 55), &"take_in": Vector2(19, 55), &"reach": Vector2(19, 55),
	&"grab": Vector2(19, 55), &"gather_a": Vector2(19, 55), &"gather_b": Vector2(19, 54), &"lift": Vector2(19, 22),
	&"settle": Vector2(19, 23), &"hold_1": Vector2(18, 22), &"hold_2": Vector2(19, 24), &"hold_3": Vector2(20, 22),
	&"hold_4": Vector2(19, 24)}
const TROPHY_REST := Vector2(19, 55)
const TROPHY_ON_STAND := [&"arrive", &"take_in", &"reach", &"grab", &"gather_a", &"gather_b"]
const TROPHY := {size = Vector2(17, 16), anchor = Vector2(8, 15), sparkle = Vector2(4, 2)}
# The stand's floor contact, its bottom centre.
const STAND_FLOOR := Vector2(19, 63)
# The art's full-screen effects (640x360 texels, at the world's origin, at SCALE), all from the drop on the song's clock:
# the lift flash under the player; the confetti burst from the ring's corners and off the cup, once, and again on the
# name; the rain from `from` after the drop, looping; and the spot sweep, its first `intro` frames once, then the rest
# looping at `loop_step`. `columns` is frames a row, where a sheet is a grid.
const FX := {
	&"lift_flash": {sheet = "res://Assets/Environment/Champion/champion_lift_flash.png", frames = 3, step = 0.05,
		z = LIFT_FLASH_Z},
	&"confetti_burst": {sheet = "res://Assets/Environment/Champion/champion_confetti_burst.png", frames = 28,
		columns = 7, step = 0.05, z = FX_Z},
	&"confetti_rain": {sheet = "res://Assets/Environment/Champion/champion_confetti_rain.png", frames = 4, step = 0.12,
		z = FX_Z, from = 1.0},
	&"spot_sweep": {sheet = "res://Assets/Environment/Champion/champion_spot_sweep.png", frames = 10, step = 0.06,
		z = SPOT_SWEEP_Z, intro = 8, loop_step = 0.15},
}
# The crowd's roar: both crowd sheets with four roar frames after the seven they had (0-6 untouched), swapped in on this
# scene's own arena, the roar looping while the crowd is up.
const CROWD_ROAR := {"res://Assets/Environment/crowd_v3.png": "res://Assets/Environment/crowd_v3_roar.png",
	"res://Assets/Environment/arena_ringside_crowd.png": "res://Assets/Environment/arena_ringside_crowd_roar.png"}
const ROAR_HFRAMES := 11
const ROAR_FRAMES := [7, 8, 9, 10]
const ROAR_STEP := 0.10
# The THANK YOU card's still: the champion from behind, the cup raised, full screen behind the words.
const CREDITS_ART := "res://Assets/UI/Screens/credits_champion.png"

# Until the lift is in: the player keeps the 4-direction sheet's DOWN idle, sinking and jittering by
# PLACEHOLDER_LIFT_SHIFT texels as the art's frames bow and heave, and the stand-in cup goes where the art's does
# (TROPHY_BOTTOM). The stand-ins are drawn in code as coloured rects in texels [x, y, w, h, colour] with a pure-black
# keyline put round them, each on a canvas the art's size and anchored where its is: the cup a two-handled loving cup
# with a blue glove on its bowl on a navy plinth, the stand a navy drum with a gold lip and foot and a red velvet top.
const PLACEHOLDER_LIFT_SHIFT := {&"reach": Vector2(0, 1), &"grab": Vector2(0, 2), &"gather_a": Vector2(0, 2),
	&"gather_b": Vector2(1, 2), &"hold_2": Vector2(0, 1), &"hold_4": Vector2(0, 1)}
const PLACEHOLDER_TROPHY := [
	[3, 11, 11, 4, Color("222034")], [3, 11, 11, 1, Color("3f3f74")], [6, 12, 5, 2, Color("e6a21e")],
	[5, 10, 7, 1, Color("e6a21e")], [7, 9, 3, 1, Color("b8681b")],
	[2, 2, 13, 2, Color("e6a21e")], [3, 4, 11, 2, Color("e6a21e")], [4, 6, 9, 1, Color("b8681b")],
	[5, 7, 7, 1, Color("b8681b")], [6, 8, 5, 1, Color("7a3e17")],
	[2, 1, 13, 1, Color("fbd23c")], [4, 1, 9, 1, Color("7a3e17")],
	[1, 2, 1, 4, Color("fbd23c")], [15, 2, 1, 4, Color("b8681b")],
	[6, 3, 4, 3, Color("2464bd")], [7, 3, 2, 1, Color("3883c9")], [9, 5, 1, 1, Color("162fbb")],
	[5, 3, 1, 2, Color("cbdbfc")], [4, 2, 1, 2, Color("ffffff")],
]
const PLACEHOLDER_STAND := {size = Vector2(23, 13), anchor = Vector2(11, 12), rects = [
	[2, 1, 19, 4, Color("ac3232")], [3, 1, 8, 1, Color("d95763")], [12, 4, 8, 1, Color("6e1e2a")],
	[1, 5, 21, 1, Color("fbd23c")], [1, 6, 21, 5, Color("2c2a42")], [1, 6, 4, 5, Color("3f3f74")],
	[15, 6, 7, 5, Color("222034")], [1, 11, 21, 1, Color("e6a21e")], [5, 8, 1, 1, Color("e6a21e")],
	[11, 8, 1, 1, Color("e6a21e")], [17, 8, 1, 1, Color("b8681b")],
]}
const KEYLINE := Color.BLACK
# The sparkle off the cup, in texels: a dot, then a cross, then a dot again, added.
const SPARKLE := {steps = [1, 3, 1], step = 0.08, color = Color(1.0, 0.98, 0.85)}


static func final_champion() -> bool:
	return USE_FINAL_CHAMPION and ResourceLoader.exists(CHAMPION.lift) and ResourceLoader.exists(CHAMPION.stand_idle)


# The lift flash, the rain and the spot sweep.
static func final_fx() -> bool:
	return USE_FINAL_FX and [&"lift_flash", &"confetti_rain", &"spot_sweep"].all(func(fx_name: StringName) -> bool:
		return ResourceLoader.exists(FX[fx_name].sheet))


static func final_burst() -> bool:
	return USE_FINAL_FX and USE_FINAL_BURST and ResourceLoader.exists(FX[&"confetti_burst"].sheet)


static func final_crowd_roar() -> bool:
	return USE_FINAL_CROWD_ROAR and CROWD_ROAR.values().all(func(path: String) -> bool: return ResourceLoader.exists(path))


static func final_credits_art() -> bool:
	return USE_FINAL_CREDITS_ART and ResourceLoader.exists(CREDITS_ART)


#THE CREDITS
# The title holds, then the roll runs at CREDITS_SPEED until it is gone; THANK YOU FOR PLAYING fades in and holds, a
# press after CREDITS_PRESS_AFTER cutting the hold short; then the text and the music fade out and the menu loads. A
# held ESC skips to the menu, armed once ui_cancel has been let go and CREDITS_SKIP_AFTER has passed.
const CREDITS_TITLE_FADE := 1.0
const CREDITS_TITLE_HOLD := 2.0
const CREDITS_SPEED := 90.0
const CREDITS_THANKS_FADE := 1.0
const CREDITS_THANKS_HOLD := 5.0
const CREDITS_PRESS_AFTER := 1.0
const CREDITS_FADE_OUT := 3.0
const CREDITS_SKIP_AFTER := 1.0
# Kinds of line: size, colour and theme type. Pixelify Sans is only crisp at multiples of its 11 px design size.
const CREDITS_STYLES := {
	&"title": {size = 99, color = Color("eeeae0"), type = &"TitleLabel"},
	&"role": {size = 33, color = Color("fbf236"), type = &""},
	&"name": {size = 44, color = Color("eeeae0"), type = &""},
	&"section": {size = 55, color = Color("fbf236"), type = &"CardTitle"},
	&"small": {size = 22, color = Color("9badb7"), type = &""},
	&"thanks": {size = 99, color = Color("eeeae0"), type = &"TitleLabel"},
}
# The gap under each kind of line before the next one in its block, px; BLOCK_GAP more between two role blocks, and
# SECTION_GAP more before a section title or the small print. Together they make a roll of about a minute.
const CREDITS_GAP_AFTER := {&"title": 30, &"role": 6, &"name": 10, &"section": 24, &"small": 8, &"thanks": 0}
const CREDITS_BLOCK_GAP := 30
const CREDITS_SECTION_GAP := 110
# Over the still, THANK YOU sits in the dark sky above the champion, outlined so it reads on the glow.
const CREDITS_THANKS_OVER_ART_Y := 66
const CREDITS_THANKS_OUTLINE := 18
const CREDITS_NAME := "Burak Yilmaz"
const CREDITS_GAME := "ENTER THE DISCORD"
const CREDITS_BY := "A GAME BY"
const CREDITS_ROLES: Array[String] = ["DIRECTED BY", "GAME DESIGN", "STORY & DIALOGUE", "BOSS DESIGN",
	"CHARACTER DESIGN", "ART DIRECTION", "PIXEL ART & ANIMATION", "PROGRAMMING", "COMBAT DESIGN", "ARENA DESIGN",
	"CUTSCENES", "USER INTERFACE", "SOUND DESIGN", "CHARACTER VOICES", "ORIGINAL MUSIC", "PRODUCER",
	"EXECUTIVE PRODUCER", "CHIEF HYPE OFFICER"]
# The cast never names the player, to keep the gag.
const CREDITS_CAST_TITLE := "THE SERVER"
const CREDITS_CAST_NOTE := "the challengers, in ladder order"
const CREDITS_CAST: Array[String] = ["CAPTAIN BURAK", "MASON", "JOSH", "ERIC", "DANNY", "COMPUTAH", "GREYSON",
	"LIAM & BIXBY", "CARTER", "MATT", "JORDAN"]
const CREDITS_NEWCOMER_NOTE := "and introducing"
const CREDITS_NEWCOMER := "THE NEWCOMER"
# Third-party music: an entry shows only once its title and artist are filled in and its file is there - and the
# ending's own song only when it actually played. Titles and artists for the other local tracks are the user's to give.
const CREDITS_MUSIC_TITLE := "MUSIC"
const CREDITS_MUSIC := [
	{title = "Universal Collapse", artist = "DM DOKURO", file = "res://Assets/Audio/SFX/local/champion_theme_local.mp3",
		ending_song = true},
	{title = "Neo Tokyo", artist = "", file = "res://Assets/Audio/SFX/local/jordan_theme_local.mp3"},
	{title = "", artist = "", file = "res://Assets/Audio/SFX/local/carter_theme_local.mp3"},
	{title = "", artist = "", file = "res://Assets/Audio/SFX/local/mason_theme_local.mp3"},
]
const CREDITS_TOOLS_TITLE := "BUILT WITH"
const CREDITS_TOOLS: Array[String] = ["Godot Engine", "Dialogue Manager by Nathan Hoad"]
const CREDITS_THANKS_TITLE := "SPECIAL THANKS"
const CREDITS_THANKS: Array[String] = ["The real server, for being good sports"]
const CREDITS_SMALL_PRINT: Array[String] = ["Discord is a trademark of Discord Inc.",
	"This is a fan-made game. It is not affiliated with, endorsed by or sponsored by Discord Inc.",
	"© 2026 Burak Yilmaz"]
const CREDITS_THANK_YOU := "THANK YOU FOR PLAYING"
