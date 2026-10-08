extends RefCounted

# Jordan's ride and mat sheets for phase 1 on the kaiju, per frame, as the artist's contract gives them
# (art_source/jordan_kaiju/contract_rider.json, approved 2026-10-04), written from it by the kaiju coder's scratch
# generator. Texels on his 96x96 frame: each a texel's top-left corner (the kaiju contract's convention), but SOLES,
# which is the bottom edge of the soles row, where his other sheets' soles stand (JordanArtLayout.FLOOR_POINT).
# body_box is his hurtbox on that frame, (x, y, w, h).

const SHEETS := {
	&"ride_idle": [
		{seat = Vector2(44, 75), crown = Vector2(57, 14), body_box = Rect2(25, 14, 37, 81)},
		{seat = Vector2(44, 75), crown = Vector2(57, 15), body_box = Rect2(25, 15, 37, 80)},
		{seat = Vector2(44, 75), crown = Vector2(57, 15), body_box = Rect2(25, 15, 37, 80)},
		{seat = Vector2(44, 75), crown = Vector2(57, 14), body_box = Rect2(25, 14, 37, 81)},
	],
	&"ride_throw": [
		{seat = Vector2(44, 75), crown = Vector2(60, 16), body_box = Rect2(36, 16, 26, 79)},
		{seat = Vector2(44, 75), crown = Vector2(53, 13), body_box = Rect2(21, 13, 39, 82)},
		{seat = Vector2(44, 75), hand = Vector2(66, 58), crown = Vector2(62, 18), body_box = Rect2(37, 18, 32, 77)},
		{seat = Vector2(44, 75), crown = Vector2(58, 15), body_box = Rect2(32, 15, 31, 80)},
	],
	&"ride_brace": [
		{seat = Vector2(44, 75), crown = Vector2(39, 18), body_box = Rect2(25, 18, 39, 76)},
		{seat = Vector2(44, 75), crown = Vector2(34, 17), body_box = Rect2(25, 17, 39, 78)},
	],
	&"topple": [
		{seat = Vector2(48, 70), pivot = Vector2(48, 64), crown = Vector2(38, 7), body_box = Rect2(24, 7, 46, 77)},
		{pivot = Vector2(51, 68), crown = Vector2(32, 13), body_box = Rect2(18, 7, 61, 65)},
		{pivot = Vector2(51, 68), crown = Vector2(29, 20), body_box = Rect2(2, 2, 66, 72)},
		{pivot = Vector2(51, 71), crown = Vector2(35, 18), body_box = Rect2(13, 11, 63, 65)},
		{pivot = Vector2(51, 76), crown = Vector2(37, 19), body_box = Rect2(22, 19, 59, 61)},
		{soles = Vector2(48, 96), pivot = Vector2(48, 91), crown = Vector2(49, 39), body_box = Rect2(28, 39, 49, 57)},
	],
	&"dismount_daze": [
		{soles = Vector2(48, 96), crown = Vector2(49, 37), stars = Vector2(49, 30), body_box = Rect2(28, 37, 49, 59)},
		{soles = Vector2(48, 96), crown = Vector2(50, 39), stars = Vector2(50, 31), body_box = Rect2(28, 39, 49, 57)},
		{soles = Vector2(48, 96), crown = Vector2(49, 39), stars = Vector2(51, 31), body_box = Rect2(28, 39, 49, 57)},
		{soles = Vector2(48, 96), crown = Vector2(49, 38), stars = Vector2(50, 30), body_box = Rect2(28, 38, 49, 58)},
	],
	&"climb": [
		{soles = Vector2(48, 96), pivot = Vector2(50, 66), crown = Vector2(69, 22), body_box = Rect2(31, 22, 41, 74)},
		{pivot = Vector2(49, 56), crown = Vector2(57, 1), body_box = Rect2(30, 1, 38, 93)},
		{pivot = Vector2(51, 48), crown = Vector2(35, 37), body_box = Rect2(22, 22, 64, 45)},
		{pivot = Vector2(51, 48), crown = Vector2(48, 42), body_box = Rect2(25, 13, 45, 64)},
		{seat = Vector2(48, 70), pivot = Vector2(49, 58), crown = Vector2(43, 13), body_box = Rect2(37, 13, 34, 74)},
		{seat = Vector2(48, 70), pivot = Vector2(49, 58), crown = Vector2(62, 10), body_box = Rect2(30, 10, 37, 79)},
	],
	&"ride_taunt": [
		{seat = Vector2(44, 75), crown = Vector2(51, 11), body_box = Rect2(25, 11, 40, 84)},
		{seat = Vector2(44, 75), crown = Vector2(51, 12), body_box = Rect2(25, 12, 40, 82)},
		{seat = Vector2(44, 75), crown = Vector2(51, 11), body_box = Rect2(25, 11, 40, 84)},
		{seat = Vector2(44, 75), crown = Vector2(51, 12), body_box = Rect2(25, 12, 40, 82)},
	],
	&"box_open": [
		{soles = Vector2(48, 96), crown = Vector2(61, 9), body_box = Rect2(29, 9, 48, 87)},
		{soles = Vector2(48, 96), crown = Vector2(64, 10), body_box = Rect2(36, 10, 30, 86)},
		{soles = Vector2(48, 96), crown = Vector2(61, 9), body_box = Rect2(29, 9, 37, 87)},
		{soles = Vector2(48, 96), crown = Vector2(64, 11), body_box = Rect2(36, 11, 30, 85)},
		{soles = Vector2(48, 96), toy = Vector2(36, 29), crown = Vector2(59, 8), body_box = Rect2(29, 8, 37, 88)},
		{soles = Vector2(48, 96), toy = Vector2(30, 16), crown = Vector2(60, 8), body_box = Rect2(26, 8, 40, 88)},
	],
	&"toss": [
		{soles = Vector2(48, 96), toy = Vector2(56, 45), crown = Vector2(64, 10), body_box = Rect2(36, 10, 30, 86)},
		{soles = Vector2(48, 96), hand = Vector2(16, 40), crown = Vector2(57, 8), body_box = Rect2(15, 8, 51, 88)},
		{soles = Vector2(48, 96), crown = Vector2(59, 9), body_box = Rect2(16, 9, 50, 87)},
	],
	&"butt_land": [
		{pivot = Vector2(49, 66), crown = Vector2(42, 12), body_box = Rect2(17, 12, 60, 58)},
		{pivot = Vector2(49, 70), crown = Vector2(41, 17), body_box = Rect2(16, 17, 59, 57)},
		{soles = Vector2(48, 96), crown = Vector2(50, 38), body_box = Rect2(28, 38, 49, 58)},
		{soles = Vector2(48, 96), crown = Vector2(47, 28), body_box = Rect2(26, 28, 41, 68)},
		{soles = Vector2(48, 96), crown = Vector2(55, 34), body_box = Rect2(26, 34, 46, 62)},
		{soles = Vector2(48, 96), crown = Vector2(55, 35), body_box = Rect2(26, 35, 46, 61)},
	],
}
