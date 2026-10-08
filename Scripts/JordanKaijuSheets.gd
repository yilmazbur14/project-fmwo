extends RefCounted

# The kaiju's drawn sheets as the artist's contracts give them (art_source/jordan_kaiju/contract_wave1.json and
# contract_wave2.json, approved 2026-10-04), written from them by the kaiju coder's scratch generator rather than by
# hand, so the fight reads the numbers the art was audited against. Per sheet: its file under
# JordanKaijuLayout.SHEET_DIR, frame size and pivot in texels, frames, times (HOLD for the contract's null) and loop;
# per frame the anchors the fight places things by, texels on the frame. Head frames carry their AIM_DEG, the tail's
# arc its ANGLE_DEG and the PIVOT_FEET that goes on its feet.

const HOLD := 3600.0

const SHEETS := {
	&"idle": {
		file = "kaiju_idle.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 6, times = [0.16, 0.16, 0.16, 0.16, 0.16, 0.16], loop = true,
		anchors = [
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), mouth = Vector2(200, 82), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 43)},
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), mouth = Vector2(200, 82), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 43)},
			{rider_seat = Vector2(139, 54), neck = Vector2(131, 75), mouth = Vector2(200, 83), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 44)},
			{rider_seat = Vector2(139, 54), neck = Vector2(131, 75), mouth = Vector2(200, 83), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 44)},
			{rider_seat = Vector2(139, 54), neck = Vector2(131, 75), mouth = Vector2(200, 83), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 44)},
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), mouth = Vector2(200, 82), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 43)},
		],
	},
	&"charge": {
		file = "kaiju_charge.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 2, times = [0.2, 0.2], loop = true,
		anchors = [
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(116, 45)},
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(116, 45)},
		],
	},
	&"head_aim": {
		file = "kaiju_head_aim.png", frame = Vector2(112, 143), pivot = Vector2(35, 66), count = 8, times = [], loop = false,
		anchors = [
			{neck = Vector2(35, 66), mouth = Vector2(75, 12), seat_on_head = Vector2(20, 49), aim = -60.0},
			{neck = Vector2(35, 66), mouth = Vector2(91, 29), seat_on_head = Vector2(27, 45), aim = -40.0},
			{neck = Vector2(35, 66), mouth = Vector2(100, 50), seat_on_head = Vector2(35, 44), aim = -20.0},
			{neck = Vector2(35, 66), mouth = Vector2(102, 73), seat_on_head = Vector2(42, 45), aim = 0.0},
			{neck = Vector2(35, 66), mouth = Vector2(95, 96), seat_on_head = Vector2(49, 49), aim = 20.0},
			{neck = Vector2(35, 66), mouth = Vector2(81, 115), seat_on_head = Vector2(54, 55), aim = 40.0},
			{neck = Vector2(35, 66), mouth = Vector2(56, 130), seat_on_head = Vector2(57, 64), aim = 65.0},
			{neck = Vector2(35, 66), mouth = Vector2(28, 133), seat_on_head = Vector2(56, 73), aim = 90.0},
		],
	},
	&"head_fire": {
		file = "kaiju_head_fire.png", frame = Vector2(112, 143), pivot = Vector2(35, 66), count = 8, times = [], loop = false,
		anchors = [
			{neck = Vector2(35, 66), mouth = Vector2(80, 16), seat_on_head = Vector2(20, 49), aim = -60.0},
			{neck = Vector2(35, 66), mouth = Vector2(94, 35), seat_on_head = Vector2(27, 45), aim = -40.0},
			{neck = Vector2(35, 66), mouth = Vector2(101, 57), seat_on_head = Vector2(35, 44), aim = -20.0},
			{neck = Vector2(35, 66), mouth = Vector2(101, 80), seat_on_head = Vector2(42, 45), aim = 0.0},
			{neck = Vector2(35, 66), mouth = Vector2(92, 102), seat_on_head = Vector2(49, 49), aim = 20.0},
			{neck = Vector2(35, 66), mouth = Vector2(76, 119), seat_on_head = Vector2(54, 55), aim = 40.0},
			{neck = Vector2(35, 66), mouth = Vector2(50, 131), seat_on_head = Vector2(57, 64), aim = 65.0},
			{neck = Vector2(35, 66), mouth = Vector2(21, 132), seat_on_head = Vector2(56, 73), aim = 90.0},
		],
	},
	&"spines": {
		file = "kaiju_spines.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 9, times = [], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
	&"rear": {
		file = "kaiju_rear.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 4, times = [0.12, 0.12, 0.13, 0.13], loop = false,
		anchors = [
			{rider_seat = Vector2(112, 45), neck = Vector2(116, 67), mouth = Vector2(180, 39), foot_impact = Vector2(138, 201), hip = Vector2(101, 147), crown = Vector2(132, 21)},
			{rider_seat = Vector2(95, 44), neck = Vector2(106, 63), mouth = Vector2(158, 18), foot_impact = Vector2(138, 198), hip = Vector2(101, 145), crown = Vector2(136, 5)},
			{rider_seat = Vector2(159, 72), neck = Vector2(145, 90), mouth = Vector2(207, 121), foot_impact = Vector2(139, 206), hip = Vector2(101, 156), crown = Vector2(123, 56)},
			{rider_seat = Vector2(172, 91), neck = Vector2(154, 104), mouth = Vector2(206, 150), foot_impact = Vector2(139, 206), hip = Vector2(101, 162), crown = Vector2(105, 62)},
		],
	},
	&"leap": {
		file = "kaiju_leap.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 3, times = [0.1, 0.1, 0.1], loop = false,
		anchors = [
			{rider_seat = Vector2(117, 35), neck = Vector2(118, 57), mouth = Vector2(185, 39), foot_impact = Vector2(135, 191), hip = Vector2(101, 137), crown = Vector2(141, 14)},
			{rider_seat = Vector2(113, 31), neck = Vector2(115, 53), mouth = Vector2(182, 34), foot_impact = Vector2(126, 183), hip = Vector2(101, 133), crown = Vector2(136, 10)},
			{rider_seat = Vector2(151, 41), neck = Vector2(139, 61), mouth = Vector2(205, 83), foot_impact = Vector2(140, 178), hip = Vector2(101, 131), crown = Vector2(127, 29)},
		],
	},
	&"drop": {
		file = "kaiju_drop.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 2, times = [0.11, 0.11], loop = false,
		anchors = [
			{rider_seat = Vector2(120, 35), neck = Vector2(114, 57), mouth = Vector2(183, 61), foot_impact = Vector2(170, 159), hip = Vector2(101, 137), crown = Vector2(138, 24)},
			{rider_seat = Vector2(163, 57), neck = Vector2(146, 71), mouth = Vector2(201, 114), foot_impact = Vector2(125, 196), hip = Vector2(101, 137), crown = Vector2(125, 38)},
		],
	},
	&"stomp": {
		file = "kaiju_stomp.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 3, times = [0.05, 0.1, 3600.0], loop = false,
		anchors = [
			{rider_seat = Vector2(167, 84), neck = Vector2(150, 98), mouth = Vector2(204, 141), foot_impact = Vector2(139, 206), hip = Vector2(101, 160), crown = Vector2(98, 61)},
			{rider_seat = Vector2(153, 65), neck = Vector2(140, 83), mouth = Vector2(205, 108), foot_impact = Vector2(139, 206), hip = Vector2(101, 153), crown = Vector2(129, 51)},
			{rider_seat = Vector2(144, 57), neck = Vector2(134, 77), mouth = Vector2(201, 93), foot_impact = Vector2(139, 206), hip = Vector2(101, 150), crown = Vector2(120, 46)},
		],
	},
	&"stumble": {
		file = "kaiju_stumble.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 5, times = [0.07, 0.08, 0.1, 0.1, 3600.0], loop = false,
		anchors = [
			{rider_seat = Vector2(89, 47), neck = Vector2(101, 65), mouth = Vector2(149, 16), foot_impact = Vector2(139, 192), hip = Vector2(98, 147), crown = Vector2(128, 4)},
			{rider_seat = Vector2(88, 46), neck = Vector2(97, 66), mouth = Vector2(153, 25), foot_impact = Vector2(126, 198), hip = Vector2(95, 148), crown = Vector2(130, 11)},
			{rider_seat = Vector2(168, 88), neck = Vector2(150, 101), mouth = Vector2(201, 148), foot_impact = Vector2(139, 206), hip = Vector2(101, 163), crown = Vector2(98, 64)},
			{rider_seat = Vector2(176, 105), neck = Vector2(155, 113), mouth = Vector2(192, 172), foot_impact = Vector2(139, 206), hip = Vector2(101, 169), crown = Vector2(108, 69)},
			{rider_seat = Vector2(172, 97), neck = Vector2(152, 107), mouth = Vector2(197, 160), foot_impact = Vector2(139, 206), hip = Vector2(101, 167), crown = Vector2(102, 68)},
		],
	},
	&"kneel": {
		file = "kaiju_kneel.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 2, times = [0.3, 0.3], loop = true,
		anchors = [
			{rider_seat = Vector2(172, 97), neck = Vector2(152, 107), mouth = Vector2(197, 160), foot_impact = Vector2(139, 206), hip = Vector2(101, 167), crown = Vector2(102, 68)},
			{rider_seat = Vector2(171, 97), neck = Vector2(151, 106), mouth = Vector2(192, 162), foot_impact = Vector2(139, 206), hip = Vector2(101, 167), crown = Vector2(100, 68)},
		],
	},
	&"stand": {
		file = "kaiju_stand.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 3, times = [0.12, 0.12, 0.12], loop = false,
		anchors = [
			{rider_seat = Vector2(158, 76), neck = Vector2(144, 93), mouth = Vector2(205, 125), foot_impact = Vector2(139, 206), hip = Vector2(101, 160), crown = Vector2(122, 60)},
			{rider_seat = Vector2(146, 62), neck = Vector2(137, 82), mouth = Vector2(204, 97), foot_impact = Vector2(139, 206), hip = Vector2(101, 154), crown = Vector2(123, 51)},
			{rider_seat = Vector2(137, 54), neck = Vector2(131, 75), mouth = Vector2(201, 78), foot_impact = Vector2(139, 206), hip = Vector2(101, 150), crown = Vector2(156, 42)},
		],
	},
	&"land": {
		file = "kaiju_land.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 3, times = [0.06, 0.1, 0.14], loop = false,
		anchors = [
			{rider_seat = Vector2(125, 44), neck = Vector2(123, 67), mouth = Vector2(191, 58), foot_impact = Vector2(138, 200), hip = Vector2(101, 145), crown = Vector2(151, 27)},
			{rider_seat = Vector2(168, 87), neck = Vector2(151, 101), mouth = Vector2(205, 144), foot_impact = Vector2(139, 206), hip = Vector2(101, 162), crown = Vector2(99, 63)},
			{rider_seat = Vector2(148, 62), neck = Vector2(137, 81), mouth = Vector2(205, 99), foot_impact = Vector2(139, 206), hip = Vector2(101, 153), crown = Vector2(125, 50)},
		],
	},
	&"grow": {
		file = "kaiju_grow.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 10, times = [0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12], loop = false,
		anchors = [
			{rider_seat = Vector2(103, 188), neck = Vector2(102, 190), mouth = Vector2(110, 191), foot_impact = Vector2(103, 206), hip = Vector2(98, 199), crown = Vector2(101, 186)},
			{rider_seat = Vector2(105, 178), neck = Vector2(104, 182), mouth = Vector2(116, 184), foot_impact = Vector2(105, 206), hip = Vector2(99, 196), crown = Vector2(108, 176)},
			{rider_seat = Vector2(109, 166), neck = Vector2(107, 172), mouth = Vector2(125, 174), foot_impact = Vector2(109, 206), hip = Vector2(99, 191), crown = Vector2(112, 163)},
			{rider_seat = Vector2(113, 151), neck = Vector2(110, 158), mouth = Vector2(135, 161), foot_impact = Vector2(113, 206), hip = Vector2(99, 186), crown = Vector2(118, 147)},
			{rider_seat = Vector2(117, 133), neck = Vector2(114, 143), mouth = Vector2(147, 147), foot_impact = Vector2(117, 206), hip = Vector2(99, 179), crown = Vector2(107, 128)},
			{rider_seat = Vector2(122, 114), neck = Vector2(118, 127), mouth = Vector2(159, 132), foot_impact = Vector2(122, 206), hip = Vector2(100, 172), crown = Vector2(131, 108)},
			{rider_seat = Vector2(127, 96), neck = Vector2(122, 111), mouth = Vector2(172, 117), foot_impact = Vector2(127, 206), hip = Vector2(100, 165), crown = Vector2(137, 89)},
			{rider_seat = Vector2(132, 78), neck = Vector2(126, 95), mouth = Vector2(184, 102), foot_impact = Vector2(132, 206), hip = Vector2(100, 158), crown = Vector2(146, 69)},
			{rider_seat = Vector2(136, 62), neck = Vector2(129, 82), mouth = Vector2(194, 90), foot_impact = Vector2(136, 206), hip = Vector2(101, 153), crown = Vector2(151, 53)},
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), mouth = Vector2(200, 82), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 43)},
		],
	},
	&"shrink": {
		file = "kaiju_shrink.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 8, times = [0.11, 0.11, 0.11, 0.11, 0.11, 0.11, 0.11, 0.11], loop = false,
		anchors = [
			{rider_seat = Vector2(139, 53), neck = Vector2(131, 74), mouth = Vector2(200, 82), foot_impact = Vector2(139, 206), hip = Vector2(101, 149), crown = Vector2(156, 43)},
			{rider_seat = Vector2(132, 78), neck = Vector2(126, 95), mouth = Vector2(184, 102), foot_impact = Vector2(132, 206), hip = Vector2(100, 158), crown = Vector2(146, 69)},
			{rider_seat = Vector2(122, 114), neck = Vector2(118, 127), mouth = Vector2(159, 132), foot_impact = Vector2(122, 206), hip = Vector2(100, 172), crown = Vector2(131, 108)},
			{rider_seat = Vector2(114, 145), neck = Vector2(111, 153), mouth = Vector2(139, 156), foot_impact = Vector2(114, 206), hip = Vector2(99, 183), crown = Vector2(105, 141)},
			{rider_seat = Vector2(108, 169), neck = Vector2(106, 174), mouth = Vector2(123, 176), foot_impact = Vector2(108, 206), hip = Vector2(99, 192), crown = Vector2(103, 167)},
			{rider_seat = Vector2(104, 183), neck = Vector2(103, 186), mouth = Vector2(113, 187), foot_impact = Vector2(104, 206), hip = Vector2(98, 198), crown = Vector2(101, 181)},
			{rider_seat = Vector2(103, 188), neck = Vector2(102, 190), mouth = Vector2(110, 191), foot_impact = Vector2(103, 206), hip = Vector2(98, 199), crown = Vector2(101, 186)},
			{rider_seat = Vector2(103, 188), neck = Vector2(102, 190), mouth = Vector2(110, 191), foot_impact = Vector2(103, 206), hip = Vector2(98, 199), crown = Vector2(101, 186)},
		],
	},
	&"toy": {
		file = "kaiju_toy.png", frame = Vector2(32, 32), pivot = Vector2(12, 27), count = 4, times = [0.1, 0.1, 0.1, 0.1], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
		],
	},
	&"shadow": {
		file = "kaiju_shadow.png", frame = Vector2(168, 32), pivot = Vector2(84, 14), count = 1, times = [], loop = false,
		anchors = [
			{},
		],
	},
	&"stomp_mark": {
		file = "kaiju_stomp_mark.png", frame = Vector2(112, 80), pivot = Vector2(56, 40), count = 6, times = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
	&"stomp_impact": {
		file = "kaiju_stomp_impact.png", frame = Vector2(160, 96), pivot = Vector2(80, 48), count = 6, times = [0.05, 0.06, 0.07, 0.08, 0.1, 3600.0], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
	&"beam_body": {
		file = "kaiju_beam_body.png", frame = Vector2(32, 32), pivot = Vector2(0, 16), count = 4, times = [0.05, 0.05, 0.05, 0.05], loop = true,
		anchors = [
			{},
			{},
			{},
			{},
		],
	},
	&"beam_mouth": {
		file = "kaiju_beam_mouth.png", frame = Vector2(48, 48), pivot = Vector2(24, 24), count = 4, times = [0.05, 0.05, 0.05, 0.05], loop = true,
		anchors = [
			{},
			{},
			{},
			{},
		],
	},
	&"beam_end": {
		file = "kaiju_beam_end.png", frame = Vector2(48, 48), pivot = Vector2(28, 24), count = 4, times = [0.05, 0.05, 0.05, 0.05], loop = true,
		anchors = [
			{},
			{},
			{},
			{},
		],
	},
	&"mouth_charge": {
		file = "kaiju_mouth_charge.png", frame = Vector2(32, 32), pivot = Vector2(16, 16), count = 6, times = [0.08, 0.08, 0.08, 0.08, 0.08, 0.08], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
	&"burn_flame": {
		file = "kaiju_burn_flame.png", frame = Vector2(16, 24), pivot = Vector2(8, 23), count = 6, times = [0.08, 0.08, 0.08, 0.08, 0.08, 0.08], loop = true,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
	&"burn_out": {
		file = "kaiju_burn_out.png", frame = Vector2(16, 24), pivot = Vector2(8, 23), count = 4, times = [0.1, 0.1, 0.1, 0.1], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
		],
	},
	&"roar": {
		file = "kaiju_roar.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 6, times = [0.1, 0.1, 0.15, 0.15, 0.15, 0.15], loop = false,
		anchors = [
			{rider_seat = Vector2(157, 67), neck = Vector2(142, 83), mouth = Vector2(202, 118), foot_impact = Vector2(139, 206), hip = Vector2(101, 152), crown = Vector2(131, 51)},
			{rider_seat = Vector2(105, 45), neck = Vector2(112, 66), mouth = Vector2(171, 29), foot_impact = Vector2(138, 201), hip = Vector2(101, 147), crown = Vector2(150, 13)},
			{rider_seat = Vector2(92, 46), neck = Vector2(104, 64), mouth = Vector2(152, 13), foot_impact = Vector2(138, 199), hip = Vector2(101, 146), crown = Vector2(130, 2)},
			{rider_seat = Vector2(91, 47), neck = Vector2(105, 64), mouth = Vector2(150, 11), foot_impact = Vector2(138, 199), hip = Vector2(102, 146), crown = Vector2(127, 1)},
			{rider_seat = Vector2(92, 46), neck = Vector2(104, 64), mouth = Vector2(153, 15), foot_impact = Vector2(138, 199), hip = Vector2(100, 146), crown = Vector2(130, 3)},
			{rider_seat = Vector2(91, 46), neck = Vector2(104, 64), mouth = Vector2(151, 12), foot_impact = Vector2(138, 199), hip = Vector2(101, 146), crown = Vector2(128, 2)},
		],
	},
	&"roar_spines": {
		file = "kaiju_roar_spines.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 6, times = [0.1, 0.1, 0.15, 0.15, 0.15, 0.15], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
	&"bow": {
		file = "kaiju_bow.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 4, times = [0.1, 0.1, 0.1, 0.1], loop = false,
		anchors = [
			{rider_seat = Vector2(152, 63), neck = Vector2(138, 80), mouth = Vector2(201, 110), foot_impact = Vector2(139, 206), hip = Vector2(101, 152), crown = Vector2(126, 49)},
			{rider_seat = Vector2(164, 76), neck = Vector2(145, 88), mouth = Vector2(195, 136), foot_impact = Vector2(139, 206), hip = Vector2(101, 154), crown = Vector2(107, 54)},
			{rider_seat = Vector2(173, 91), neck = Vector2(152, 96), mouth = Vector2(181, 159), foot_impact = Vector2(139, 206), hip = Vector2(101, 156), crown = Vector2(102, 56)},
			{rider_seat = Vector2(174, 94), neck = Vector2(152, 98), mouth = Vector2(179, 162), foot_impact = Vector2(139, 206), hip = Vector2(101, 156), crown = Vector2(103, 56)},
		],
	},
	&"hit": {
		file = "kaiju_hit.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 2, times = [0.08, 0.14], loop = false,
		anchors = [
			{rider_seat = Vector2(116, 44), neck = Vector2(118, 66), mouth = Vector2(184, 43), foot_impact = Vector2(138, 201), hip = Vector2(101, 146), crown = Vector2(137, 22)},
			{rider_seat = Vector2(150, 61), neck = Vector2(138, 80), mouth = Vector2(203, 104), foot_impact = Vector2(139, 206), hip = Vector2(101, 151), crown = Vector2(126, 48)},
		],
	},
	&"tail_windup": {
		file = "kaiju_tail_windup.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 3, times = [0.13, 0.13, 0.13], loop = false,
		anchors = [
			{rider_seat = Vector2(142, 58), neck = Vector2(134, 79), mouth = Vector2(202, 90), foot_impact = Vector2(139, 206), hip = Vector2(101, 153), crown = Vector2(119, 48)},
			{rider_seat = Vector2(153, 67), neck = Vector2(141, 86), mouth = Vector2(206, 109), foot_impact = Vector2(139, 206), hip = Vector2(101, 155), crown = Vector2(129, 53)},
			{rider_seat = Vector2(159, 74), neck = Vector2(145, 91), mouth = Vector2(207, 123), foot_impact = Vector2(139, 206), hip = Vector2(101, 157), crown = Vector2(107, 58)},
		],
	},
	&"tail_spin": {
		file = "kaiju_tail_spin.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 8, times = [0.0875, 0.0875, 0.0875, 0.0875, 0.0875, 0.0875, 0.0875, 0.0875], loop = false,
		anchors = [
			{rider_seat = Vector2(156, 67), neck = Vector2(142, 85), mouth = Vector2(205, 114), foot_impact = Vector2(139, 206), hip = Vector2(101, 153), crown = Vector2(132, 52)},
			{rider_seat = Vector2(137, 72), neck = Vector2(127, 88), mouth = Vector2(164, 124), foot_impact = Vector2(123, 206), hip = Vector2(100, 153), crown = Vector2(104, 54)},
			{rider_seat = Vector2(59, 72), neck = Vector2(69, 88), mouth = Vector2(32, 124), foot_impact = Vector2(73, 206), hip = Vector2(96, 153), crown = Vector2(73, 54)},
			{rider_seat = Vector2(40, 67), neck = Vector2(54, 85), mouth = Vector2(-9, 114), foot_impact = Vector2(57, 206), hip = Vector2(95, 153), crown = Vector2(63, 52)},
			{rider_seat = Vector2(59, 72), neck = Vector2(69, 88), mouth = Vector2(32, 124), foot_impact = Vector2(73, 206), hip = Vector2(96, 153), crown = Vector2(73, 54)},
			{rider_seat = Vector2(137, 72), neck = Vector2(127, 88), mouth = Vector2(164, 124), foot_impact = Vector2(123, 206), hip = Vector2(100, 153), crown = Vector2(104, 54)},
			{rider_seat = Vector2(153, 65), neck = Vector2(141, 84), mouth = Vector2(205, 109), foot_impact = Vector2(139, 206), hip = Vector2(101, 153), crown = Vector2(117, 52)},
			{rider_seat = Vector2(148, 62), neck = Vector2(137, 81), mouth = Vector2(204, 99), foot_impact = Vector2(139, 206), hip = Vector2(101, 153), crown = Vector2(125, 50)},
		],
	},
	&"tail_arc": {
		file = "kaiju_tail_arc.png", frame = Vector2(176, 80), pivot = Vector2(0, 0), count = 16, times = [], loop = false,
		anchors = [
			{pivot_feet = Vector2(-15, 66), angle = 0.0},
			{pivot_feet = Vector2(-16, 40), angle = 22.5},
			{pivot_feet = Vector2(-12, 14), angle = 45.0},
			{pivot_feet = Vector2(3, 1), angle = 67.5},
			{pivot_feet = Vector2(32, -5), angle = 90.0},
			{pivot_feet = Vector2(89, -6), angle = 112.5},
			{pivot_feet = Vector2(149, -4), angle = 135.0},
			{pivot_feet = Vector2(176, 2), angle = 157.5},
			{pivot_feet = Vector2(191, 15), angle = 180.0},
			{pivot_feet = Vector2(193, 41), angle = 202.5},
			{pivot_feet = Vector2(188, 67), angle = 225.0},
			{pivot_feet = Vector2(173, 79), angle = 247.5},
			{pivot_feet = Vector2(146, 86), angle = 270.0},
			{pivot_feet = Vector2(87, 86), angle = 292.5},
			{pivot_feet = Vector2(27, 85), angle = 315.0},
			{pivot_feet = Vector2(0, 78), angle = 337.5},
		],
	},
	&"collapse": {
		file = "kaiju_collapse.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 4, times = [0.08, 0.1, 0.12, 3600.0], loop = false,
		anchors = [
			{rider_seat = Vector2(161, 77), neck = Vector2(145, 93), mouth = Vector2(203, 130), foot_impact = Vector2(139, 206), hip = Vector2(101, 159), crown = Vector2(123, 59)},
			{rider_seat = Vector2(89, 68), neck = Vector2(99, 87), mouth = Vector2(153, 43), foot_impact = Vector2(158, 207), hip = Vector2(101, 169), crown = Vector2(130, 30)},
			{rider_seat = Vector2(115, 72), neck = Vector2(111, 93), mouth = Vector2(180, 92), foot_impact = Vector2(173, 208), hip = Vector2(101, 174), crown = Vector2(142, 57)},
			{rider_seat = Vector2(136, 77), neck = Vector2(124, 96), mouth = Vector2(188, 121), foot_impact = Vector2(173, 208), hip = Vector2(101, 173), crown = Vector2(106, 68)},
		],
	},
	&"down": {
		file = "kaiju_down.png", frame = Vector2(224, 232), pivot = Vector2(98, 206), count = 2, times = [0.3, 0.3], loop = true,
		anchors = [
			{rider_seat = Vector2(136, 77), neck = Vector2(124, 96), mouth = Vector2(188, 121), foot_impact = Vector2(173, 208), hip = Vector2(101, 173), crown = Vector2(106, 68)},
			{rider_seat = Vector2(140, 80), neck = Vector2(125, 97), mouth = Vector2(186, 130), foot_impact = Vector2(173, 208), hip = Vector2(101, 173), crown = Vector2(109, 68)},
		],
	},
	&"puff": {
		file = "kaiju_puff.png", frame = Vector2(96, 96), pivot = Vector2(48, 48), count = 6, times = [0.06, 0.06, 0.06, 0.06, 0.06, 0.06], loop = false,
		anchors = [
			{},
			{},
			{},
			{},
			{},
			{},
		],
	},
}
