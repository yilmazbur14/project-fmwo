extends RefCounted

# Every speaker's dialogue talk blip, keyed by their name in lowercase. The sounds are synthesized by
# art_source/audio_voices/make_voices.py, which can also render a preview of every voice from this table.
#   streams     The voice's variants. Each blip picks one at random, never the same one twice running.
#   pitch_min   Each blip's pitch_scale is picked at random between these two.
#   pitch_max
#   melody      pitch_scale multipliers the blips step through in turn, from the first on every new line.
#   every       Blip on every Nth letter. Spaces and punctuation stay silent and don't count.
#   volume_db   How loud the voice plays. Every sound was made equally loud, so 0 means the same for everyone.

# However fast the text types, blips are at least this far apart, so they never run together into a buzz.
const MIN_BLIP_GAP_MS := 45

# The voice for lines without a speaker name.
const NAMELESS_VOICE := "burak"
# The voice for speakers missing from VOICES.
const NEUTRAL_VOICE := "neutral"

const VOICES := {
	# The main character: clean, friendly and neutral, the gentlest voice of all.
	"burak": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_burak_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_burak_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_burak_3.wav"),
		],
		"pitch_min": 0.95,
		"pitch_max": 1.05,
		"melody": [1.0],
		"every": 4,
		"volume_db": 0.0,
	},
	# Deep, warm and a little gritty, and heavier, so a touch slower.
	"eric": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_eric_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_eric_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_eric_3.wav"),
		],
		"pitch_min": 0.96,
		"pitch_max": 1.04,
		"melody": [1.0],
		"every": 5,
		"volume_db": 1.5,
	},
	# Robotic beeps on a fixed set of pitches, so no random pitch. Variant 5 is a two-tone chirp.
	"computah": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_computah_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_computah_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_computah_3.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_computah_4.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_computah_5.wav"),
		],
		"pitch_min": 1.0,
		"pitch_max": 1.0,
		"melody": [1.0],
		"every": 3,
		"volume_db": -2.5,
	},
	# Deadpan and unimpressed: nearly monotone and unhurried.
	"carter": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_carter_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_carter_2.wav"),
		],
		"pitch_min": 0.985,
		"pitch_max": 1.015,
		"melody": [1.0],
		"every": 6,
		"volume_db": 1.0,
	},
	# A flashy show-off: bright, bouncy and quick, with the widest pitch swing.
	"josh": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_josh_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_josh_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_josh_3.wav"),
		],
		"pitch_min": 0.88,
		"pitch_max": 1.12,
		"melody": [1.0],
		"every": 2,
		"volume_db": -2.5,
	},
	# Smug and sing-song: hops between a note and the minor third below it, like a playground "nyah-nyah".
	"liam": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_liam_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_liam_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_liam_3.wav"),
		],
		"pitch_min": 0.98,
		"pitch_max": 1.02,
		"melody": [1.0, 0.841],
		"every": 6,
		"volume_db": 1.0,
	},
	# The final boss, slightly scary: low, breathy and echoing, and slow and deliberate.
	"jordan": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_jordan_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_jordan_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_jordan_3.wav"),
		],
		"pitch_min": 0.97,
		"pitch_max": 1.03,
		"melody": [1.0],
		"every": 8,
		"volume_db": 1.5,
	},
	# A goofy guy in a chicken suit: a bouncy "bawk" with a playful pitch swing.
	"mason": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_mason_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_mason_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_mason_3.wav"),
		],
		"pitch_min": 0.9,
		"pitch_max": 1.1,
		"melody": [1.0],
		"every": 3,
		"volume_db": -2.0,
	},
	# The pilot and gamer: short and a little nasal.
	"greyson": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_greyson_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_greyson_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_greyson_3.wav"),
		],
		"pitch_min": 0.95,
		"pitch_max": 1.05,
		"melody": [1.0],
		"every": 3,
		"volume_db": -1.0,
	},
	# The intro guide: a warm, mid-range "bop".
	"danny": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_danny_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_danny_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_danny_3.wav"),
		],
		"pitch_min": 0.95,
		"pitch_max": 1.05,
		"melody": [1.0],
		"every": 4,
		"volume_db": -1.0,
	},
	# The dog: short "arf"s.
	"bixby": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_bixby_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_bixby_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_bixby_3.wav"),
		],
		"pitch_min": 0.92,
		"pitch_max": 1.08,
		"melody": [1.0],
		"every": 4,
		"volume_db": 0.0,
	},
	# Nathan (Dialogue Manager's example speaker) and anyone else not listed above: plain and level.
	"neutral": {
		"streams": [
			preload("res://Assets/Audio/SFX/Voices/voice_neutral_1.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_neutral_2.wav"),
			preload("res://Assets/Audio/SFX/Voices/voice_neutral_3.wav"),
		],
		"pitch_min": 0.96,
		"pitch_max": 1.04,
		"melody": [1.0],
		"every": 4,
		"volume_db": -1.0,
	},
}


static func for_character(character: String) -> Dictionary:
	if character.is_empty():
		return VOICES[NAMELESS_VOICE]
	return VOICES.get(character.to_lower(), VOICES[NEUTRAL_VOICE])
