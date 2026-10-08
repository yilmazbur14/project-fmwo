extends Node

# The arena crowd's voice (the 2026-10-07 playtest: every walk-in and pre-fight line, about 9 minutes of a first run,
# played in silence). A low murmur loops under every fight from its first frame, under the walk-in and the lines; once
# the fight's music is playing it drops to a bed under it, and it comes back up whenever the music stops with the fight
# still on (Greyson's and Liam's takeovers, Danny's false victory). Each cheer() the crowd gets lifts it with the
# cheering loop for the cheer's seconds; hush() cuts that short.
#
# It is heard only in a fight (a boss in FightOutro.BOSS_GROUP: not the champion ending, which builds the arena for a
# crowd of its own), with the crowd on screen (not the Puppet Master's void, which hides it), and only until the fight is
# decided: from the KO or the loss it fades out, so Jordan's walk-out and his room have none. On the Master bus, under
# the volume slider. ArenaCrowdScript builds one an arena, on the first of its two crowds.

const FightOutro := preload("res://Scripts/FightOutro.gd")

#THE LEVELS ARE MEASURED
# Decoded through Godot's own playback and measured offline: RMS of the mono fold-down, in dBFS, over a whole loop for
# these two and over 90 s of each fight's theme at its own volume_db. At 0 dB the murmur loop is -25.7 and the cheering
# loop -19.6. The themes play at -26.0 (Josh) to -16.5 (Jordan), most near -22; a talk blip is about -19 while it
# sounds. The fights as played, sound effects and all, average -17.6 to -12.5 (the playtest's measure).
const MURMUR := "res://Assets/Audio/SFX/champion_murmur_loop.wav"
const CHEERING := "res://Assets/Audio/SFX/champion_crowd_loop.wav"
const MURMUR_RMS := -25.7
const CHEERING_RMS := -19.6
# Where the murmur sits, in dBFS as heard: under the walk-in and the lines, and under the music, 10 dB under the
# quietest theme.
const UNDER_LINES := -28.0
const UNDER_MUSIC := -36.0
# The cheering loop over the murmur's level while the crowd cheers: the two together about 4 dB up.
const CHEER_OVER := 2.0
# Fading in decibels sounds even all the way down; by this level the sound can't be heard.
const SILENT := -60.0

#THE FADES, in seconds
const FADE_IN := 1.0
const DUCK := 1.0
const RISE := 2.0
const FADE_OUT := 1.0
const CHEER_IN := 0.3
const CHEER_OUT := 1.2

var murmur: AudioStreamPlayer
var cheering: AudioStreamPlayer
var cheer_time_left := 0.0
# By player: its level as heard (dBFS), the level it is heading for, and how fast it moves there, in dB a second.
var levels := {}


func _ready() -> void:
	murmur = _build("MurmurPlayer", MURMUR)
	cheering = _build("CheeringPlayer", CHEERING)


# Overlapping cheers extend rather than restart, as the crowd's own do.
func cheer(duration: float) -> void:
	cheer_time_left = maxf(cheer_time_left, duration)


func hush() -> void:
	cheer_time_left = 0.0


# Where the murmur is heading, in dBFS as heard: UNDER_LINES, UNDER_MUSIC, or SILENT where it isn't heard.
func bed_level() -> float:
	if not _heard():
		return SILENT
	return UNDER_MUSIC if _music_playing() else UNDER_LINES


func _process(delta: float) -> void:
	# Real seconds: a hit-stop slows the fight, not the room around it.
	var real_delta := delta / maxf(Engine.time_scale, 0.001)
	cheer_time_left = maxf(cheer_time_left - real_delta, 0.0)
	var bed := bed_level()
	_steer(murmur, MURMUR_RMS, bed, FADE_IN, FADE_OUT, real_delta)
	var lift := bed + CHEER_OVER if bed > SILENT and cheer_time_left > 0.0 else SILENT
	_steer(cheering, CHEERING_RMS, lift, CHEER_IN, CHEER_OUT, real_delta)


func _heard() -> bool:
	var crowd := get_parent() as CanvasItem
	if crowd == null or not crowd.is_visible_in_tree():
		return false
	var tree := get_tree()
	var outro := tree.root.get_node_or_null(^"FightOutro")
	if outro != null and outro.fight_scene == tree.current_scene:
		return false
	return tree.get_first_node_in_group(FightOutro.BOSS_GROUP) != null


# Every boss keeps his theme on music_player.
func _music_playing() -> bool:
	for boss in get_tree().get_nodes_in_group(FightOutro.BOSS_GROUP):
		var music = boss.get("music_player")
		if music is AudioStreamPlayer and music.playing:
			return true
	return false


# Moves `player` toward `target` (dBFS as heard), starting it as it rises out of SILENT and stopping it there.
func _steer(player: AudioStreamPlayer, rms: float, target: float, fade_in: float, fade_out: float, delta: float) -> void:
	var at: Dictionary = levels[player]
	if target != at.target:
		var time := fade_out if target <= SILENT else (fade_in if at.now <= SILENT else (DUCK if target < at.now else RISE))
		at.rate = absf(target - at.now) / time
		at.target = target
	at.now = move_toward(at.now, target, at.rate * delta)
	if at.now <= SILENT:
		if player.playing:
			player.stop()
		return
	player.volume_db = at.now - rms
	# Only on the way up: FightOutro's fade stops every sound still playing, and that one stays stopped.
	if not player.playing and target > SILENT:
		# From anywhere in the loop, so no two fights open on the same second of it.
		player.play(randf() * player.stream.get_length())


# The two loops carry their own loop points (art_source/audio_champion/make_champion_sfx.py), so they loop as imported.
func _build(player_name: String, path: String) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.name = player_name
	player.stream = load(path)
	add_child(player)
	levels[player] = {now = SILENT, target = SILENT, rate = 0.0}
	return player
