extends RefCounted

# Hits 2 and 3 of the combo drawn apart from hit 1 (the user's ask, 2026-09-25): hit 2 thrown with the
# other hand, hit 3 - the charged punch - a blow to the stomach. Only the drawing differs: each plays hit
# 1's "punch" cadence with its hitbox, damage and enable_hitbox frame (PlayerPunching).

# On since the user approved the art as drawn (2026-09-25). Off, or on with SHEET not imported yet,
# every punch is hit 1's "punch" on the player's own sheet. A static var rather than a const so the
# defence suite can pin it for the one mode that tests it (combo_art).
static var COMBO_ANIMS_ENABLED := true

# The artist's contract: 8 columns by player_4dir_sheet.png's 4 facing rows of 32x32 cells, the body
# placed in the cell as on that sheet. Each hit takes 4 columns on hit 1's 4 beats, full extension on
# the 4th.
const SHEET := "res://Assets/Characters/MainPlayer/player_combo_sheet.png"
const HFRAMES := 8
const VFRAMES := 4
const OTHER_HAND := "punch_2"
const BODY_BLOW := "punch_3"
const FIRST_COLUMNS := {OTHER_HAND: 0, BODY_BLOW: 4}

# The fist on each hit's full-extension frame (column 3, column 7), per facing (PlayerScript.Facing
# order), in texels from the cell's centre (16, 16), from the artist's report (2026-09-25). Along the
# punch it is the fist-tip pixel's outer edge that way: x + 1 - 16 facing right, x - 16 facing left,
# y - 16 facing up, y + 1 - 16 facing down, the rule PunchFx.GLOVE_FRONTS is measured by. PunchFx never
# puts a landed punch's star nearer the player than that, and puts it on the fist across the punch: these
# fists are drawn off hit 1's hitbox, which they keep (up, hits 2 and 3 are at cell x 18-20, the hitbox
# over x 10-14), so the star can't take the hitbox's middle as hit 1's does.
const GLOVE_FRONTS := {
	OTHER_HAND: [Vector2(-0.5, 11.0), Vector2(3.0, -16.0), Vector2(-11.0, -5.0), Vector2(11.0, -5.0)],
	BODY_BLOW: [Vector2(0.0, 13.0), Vector2(3.5, -14.0), Vector2(-12.0, -0.5), Vector2(12.0, -0.5)],
}
