"""Hand-authored maps for the middle head (frame-0 coordinates, head at identity).

MOUTH_R is the right half of the snarl, x 96..115 (its left half is the mirror); '.' keeps what the
procedural head drew there. TONGUE is drawn in place over the left side of the mouth and chin.
"""
from pal import amap

# x: 96 ... 115
MOUTH_R = [
    # r0-4  5-9   10-14 15-19          y
    "xxxxx xkkkk kyy.. .....",       # 54  lip lifted over the canine
    "xxxxx xkwxy kkk.. .....",       # 55
    "xxxxk kkwxy kxkkk kk...",       # 56
    "kkkkk xkwxy kxkxk qqk..",       # 57
    "wkxxk ykwxy kkqkq qqkk.",       # 58
    "xkyyk kkwxk qqqqq qqkk.",       # 59
    "ykkkq qkwyk qqqqq qqkk.",       # 60
    "kkkkk qkwyk qqqqq qqkk.",       # 61
    "kkkkk qkwyk qqqqq qksk.",       # 62
    "kkkkk qqkxk kqqqq qksk.",       # 63
    "kkkkk qqkxk xkqqq qksk.",       # 64
    "kkkkk qqkyk xkqqq qksk.",       # 65
    "kkkkk qqqkk wxkqq ksk..",       # 66
    "kkkkq qqqqk wxkqk ssk..",       # 67
    "qqqqq qqqqk wykks ssk..",       # 68
    "qqqqq qqqqk wykss ssk..",       # 69
    "qqqqq qqqqk wkwss ssk..",       # 70
    "qqqqq qqqqk kkxss sk...",       # 71
    "qxkxk xkkkk wwwss sk...",       # 72
    "xxkxk kkxxx xxxss sk...",       # 73
    "kkkkx xxxxx xxxss sk...",       # 74
    "wwwww wwwxx xxxss k....",       # 75
    "xxxxx xxxxx xxxss k....",       # 76
    "xxxxx xxxxx xxyss k....",       # 77
    "xxxxx xxxxx xxysk .....",       # 78
    "xxxxx xxxxx xyysk .....",       # 79
    "xxxxx xxxxx yyysk .....",       # 80
    "xxxxx xxxxy yysk. .....",       # 81
    "xxxxx xxxyy yysk. .....",       # 82
    "xxxxx xxyyy ysk.. .....",       # 83
    "xxxxx xyyyy zk... .....",       # 84
    "yyyyy zzzkk k.... .....",       # 85
    "zzzzz kkk.. ..... .....",       # 86
    "kkkkk ..... ..... .....",       # 87
]
MOUTH_Y0 = 54

# x: 80 ... 101
TONGUE = [
    # 80-84 85-89 90-94 95-99 100-101   y
    "..... ....k kkkkk k.... ..",      # 65
    "..... ...kp pNNNN Nk... ..",      # 66
    "..... ..kpp NNNNN nnk.. ..",      # 67
    "..... .kppN NNNnN nnk.. ..",      # 68
    "..... kppNN NNnNN nnk.. ..",      # 69
    "....k ppNNN NnNNN nk... ..",      # 70
    "....k pNNNN nNNNn nk... ..",      # 71
    "...kp pNNNN nNNNn k.... ..",      # 72
    "...kp NNNNn NNNnn k.... ..",      # 73
    "..kpp NNNnN NNNnk ..... ..",      # 74
    "..kpN NNNnN NNnnk ..... ..",      # 75
    "..kpN PNNnN NNnnk ..... ..",      # 76
    "..kpP PNNnN NNnnk ..... ..",      # 77
    "..kpN NNNnN NNnk. ..... ..",      # 78
    "..kpN NNnNN NNnk. ..... ..",      # 79
    "..kpN NNnNN Nnnk. ..... ..",      # 80
    "..kpN NNnNN Nnk.. ..... ..",      # 81
    "..kpP NNnNN Nnk.. ..... ..",      # 82
    "..kpN NNnNN nnk.. ..... ..",      # 83
    "..kpN NNnNN nk... ..... ..",      # 84
    "..kpN NnNNN nk... ..... ..",      # 85
    "...kp NnNNn nk... ..... ..",      # 86
    "...kp NnNNn k.... ..... ..",      # 87
    "...kp NnNnn k.... ..... ..",      # 88
    "....k pnNnk ..... ..... ..",      # 89
    "....k pNnnk ..... ..... ..",      # 90
    "..... knnk. ..... ..... ..",      # 91
    "..... .kk.. ..... ..... ..",      # 92
]
TONGUE_X0, TONGUE_Y0 = 80, 65


# The right eye, x 99..114 (the left is its mirror): lid shadow along the top, glowing mint, the
# pupil low on the inside so he glares down at the player, a glint on the outside.
EYE_R = [
    # 99-103 104-108 109-113 114   y
    "..... ..... ...hh k",     # 28
    "..... ..... .hhii k",     # 29
    "..... ....h hiWij k",     # 30
    "..... ..hhi iiijk .",     # 31
    "..... hhiii ijjk. .",     # 32
    "...hh kkiij jkk.. .",     # 33
    "..hii kkjjk k.... .",     # 34
    "..kjj jjkk. ..... .",     # 35
    "...kk kk... ..... .",     # 36
]
EYE_X0, EYE_Y0 = 99, 28


def eye_parts(dx=0, dy=0):
    right = amap(EYE_R, EYE_X0 + dx, EYE_Y0 + dy)
    left = {(191 + 2 * dx - x, y): k for (x, y), k in right.items()}
    return right, left


#FRAME 2: THE INHALE. The head is thrown back 3px (upper lip and teeth drawn 3 rows higher than frame
# 0) and the jaw dropped 10, so the maw opens on a fire building deep in the throat.

INHALE_UPPER_R = [
    # r0-4  5-9   10-14 15-19          y
    "xxxxx xkkkk kyy.. .....",       # 51  lip lifted over the canine
    "xxxxx xkwxy kkk.. .....",       # 52
    "xxxxk kkwxy kxkkk kk...",       # 53
    "kkkkk xkwxy kxkxk ..k..",       # 54
    "wkxxk ykwxy kk.k. ..kk.",       # 55
    "xkyyk kkwxk ..... ..kk.",       # 56
    "ykkk. .kwyk ..... ..kk.",       # 57
    "k.... .kwyk ..... ..kk.",       # 58
    "..... .kwyk ..... ..kk.",       # 59
    "..... ..kxk ..... .ksk.",       # 60
    "..... ..kxk ..... .ksk.",       # 61
    "..... ..kyk ..... .ksk.",       # 62
    "..... ...k. ..... .ksk.",       # 63
    "..... ..... ..... .ksk.",       # 64
    "..... ..... ..... .ksk.",       # 65
    "..... ..... ..... .ksk.",       # 66
    "..... ..... ..... .ksk.",       # 67
    "..... ..... ..... .ksk.",       # 68
]
INHALE_UPPER_Y0 = 51

INHALE_LOWER_R = [
    # r0-4  5-9   10-14 15-19          y
    "..... ..... ..... kssk.",       # 69
    "..... ..... ..... kssk.",       # 70
    "..... ..... .k... ksk..",       # 71
    "..... ..... kxk.. ksk..",       # 72
    "..... ..... kxk.k ssk..",       # 73
    "..... ..... kxk.k ssk..",       # 74
    "..... ....k wxkks ssk..",       # 75
    "..... ....k wxkks sk...",       # 76
    "..... ....k wykss sk...",       # 77
    "..... ....k wkwss sk...",       # 78
    "..... ..... kwwss sk...",       # 79
    "..... ..... kxxss sk...",       # 80
    ".xkxx kx.kk xxxss k....",       # 81
    "xxkxx kkkxx xxxss k....",       # 82
    "xxkxk kxxxx xxxss k....",       # 83
    "kkkkw wwwxx xxxss k....",       # 84
    "wwwww wwwxx xxxsk .....",       # 85
    "xxxxx xxxxx xxxsk .....",       # 86
    "xxxxx xxxxx xxysk .....",       # 87
    "xxxxx xxxxx xyk.. .....",       # 88
    "xxxxx xxxxx yyk.. .....",       # 89
    "xxxxx xxxxy yk... .....",       # 90
    "xxxxx xxxyy k.... .....",       # 91
    "xxxxx yyykk k.... .....",       # 92
    "yyzzz kkk.. ..... .....",       # 93
    "kkkkk ..... ..... .....",       # 94
]
INHALE_LOWER_Y0 = 69

# The lip edge of the dropped jaw, as the first column that is lip rather than mouth, per row.
INHALE_EDGE = {**{y: 17 for y in range(54, 60)}, **{y: 16 for y in range(60, 69)},
               **{y: 15 for y in range(69, 73)}, 73: 14, 74: 14, 75: 13, 76: 13, 77: 12, 78: 11,
               79: 10, 80: 10, 81: 8, 82: 6, 83: 4}
THROAT = (0, 67)            # the glow's centre, in half-columns from the axis and rows


def inhale_glow(dx=0, dy=0):
    """The maw's interior: dark at the lips, a fire building deep in the throat."""
    import math
    out = {}
    for y, e in INHALE_EDGE.items():
        for r in range(e):
            d = math.hypot(r + 0.5, (y - THROAT[1]) * 0.85)
            k = 'Y' if d < 3.0 else 'P' if d < 5.2 else 'p' if d < 7.2 else 'N' if d < 9.0 else \
                'n' if d < 11 else 'q' if d < 14 else 'k'
            if y <= 55 and k in 'nq':
                k = 'q'
            out[(96 + r + dx, y + dy)] = k
            out[(95 - r + dx, y + dy)] = k
    return out


def inhale_mouth(dx=0, dy=0):
    parts = []
    for rows, y0 in ((INHALE_UPPER_R, INHALE_UPPER_Y0), (INHALE_LOWER_R, INHALE_LOWER_Y0)):
        right = amap(rows, 96 + dx, y0 + dy)
        part = {(191 + 2 * dx - x, y): k for (x, y), k in right.items()}
        part.update(right)
        parts.append(part)
    return parts


def inhale_tongue(dx=0, dy=0):
    """Frame 0's tongue, lolling from lower in the dropped jaw."""
    return amap(TONGUE, TONGUE_X0 + dx, TONGUE_Y0 + 11 + dy)


def mouth_part(dx=0, dy=0):
    right = amap(MOUTH_R, 96 + dx, MOUTH_Y0 + dy)
    out = {(191 + 2 * dx - x, y): k for (x, y), k in right.items()}
    out.update(right)
    return out


def tongue_part(dx=0, dy=0):
    return amap(TONGUE, TONGUE_X0 + dx, TONGUE_Y0 + dy)
