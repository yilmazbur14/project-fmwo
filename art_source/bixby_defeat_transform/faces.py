"""Expressions and glow levels for the beast's heads (new work; the redesign's maps are only read).

cool_ears      the burning drop-ear tips at full, dying or cold
glow_eye       the mint eyes lit, dimmed or unlit
dark_maw       the dropped jaw's mouth with no fire in the throat (the K.O. gape)
mid_eyes       hand-drawn middle-head eyes: 'shut' (squeezed in pain), 'dizzy' (spirals)
side_eyes      the same for the RIGHT side head (mirror for the left)

Map coordinates follow the redesign's maps: the middle head's right eye box starts at
midmaps.EYE_X0/EYE_Y0 (x 99, y 28 before the head's row offset), the side head's eye boxes at
sidemaps.FAR_EYE_XY / NEAR_EYE_XY (before its (mdx, mdy)).
"""
import math

import common as C  # noqa: F401
from pal import amap
import heads
import midmaps
import sidemaps

#EARS: the ragged bottoms of the long drop ears burn (heads.ear: u, then v, then P toward the points)

EAR_LEVELS = {
    1: {},
    0.5: {'P': 'v', 'v': 'u', 'u': 's'},            # dying: one step cooler
    0: {'P': 'q', 'v': 'r', 'u': 's'},              # cold: the tips out, charred dark
}


def ear_fire(xf):
    """{pixel: key} of the burning ear-tip pixels of the head at xf (both ears)."""
    out = {}
    for side in (1, -1):
        e = heads.ear(xf, side)
        hy = heads.head_y(xf, e, -4)
        for p, k in e.items():
            if hy[p] >= 67 and k in 'uvP':
                out[p] = k
    return out


def cool_ears(px, xf, level=1):
    if level == 1:
        return
    m = EAR_LEVELS[level]
    for p, k in ear_fire(xf).items():
        if px.get(p) == k and k in m:
            px[p] = m[k]


#EYES: lit (approved), dim, unlit

EYE_LEVELS = {
    1: {},
    0.5: {'j': 'i', 'W': 'j', 'i': 'h'},
    0: {'j': 'h', 'W': 'h', 'i': 'h', 'h': 'a'},
}


def glow_eye(part, level=1):
    if level == 1:
        return part
    m = EYE_LEVELS[level]
    return {p: m.get(k, k) for p, k in part.items()}


#MAW

def dark_maw(dx=0, dy=0):
    """The dropped jaw's mouth (midmaps.INHALE_EDGE) with a dark throat: no fire."""
    out = {}
    for y, e in midmaps.INHALE_EDGE.items():
        for r in range(e):
            d = math.hypot(r + 0.5, (y - midmaps.THROAT[1]) * 0.85)
            k = 'k' if d < 3.6 else 'q' if d < 13 else 'k'
            out[(96 + r + dx, y + dy)] = k
            out[(95 - r + dx, y + dy)] = k
    return out


#MIDDLE HEAD EYES (right eye authored over x 99..114 of the approved eye box; the left is mirrored)

MID_EYES = {
    # squeezed shut in pain: the brow crushed down onto a '<' crease, the lid between in shadow
    'shut': [
        # 99-103 104-108 109-113 114        y (+ the head's row offset)
        "..... ..... ...kk .",     # 28
        "..... ..... kkks. .",     # 29
        "..... ...kk kss.. .",     # 30
        "..... kkkss s.... .",     # 31
        "...kk kss.. ..... .",     # 32
        "....s kkkk. ..... .",     # 33
        "..... ...kk kk... .",     # 34
        "..... ..... ..kkk .",     # 35
        "..... ..... ..... .",     # 36
    ],
    # knocked silly: a glowing mint disc with a black spiral, lids gone slack
    'dizzy': [
        # 99-103 104-108 109-113 114
        "..... kkkkk k.... .",     # 28
        "....k kiiii ikk.. .",     # 29
        "...ki ikkkk iiik. .",     # 30
        "...ki kiiii kijk. .",     # 31
        "..kik ikkki kijik .",     # 32
        "..kik ikjii kiik. .",     # 33
        "..kji kiikk iik.. .",     # 34
        "...kj jkiii ikk.. .",     # 35
        "....k kjjjj kk... .",     # 36
        "..... kkkkk ..... .",     # 37
    ],
}


def mid_eyes(name, dx=0, off=0):
    right = amap(MID_EYES[name], midmaps.EYE_X0 + dx, midmaps.EYE_Y0 + off)
    left = {(191 + 2 * dx - x, y): k for (x, y), k in right.items()}
    return [right, left]


#SIDE HEAD EYES (right side head: far eye tucked against the blaze, near eye the big one)

def _shut_from(rows):
    """A closed eye from an open one: the mint becomes a lid in shadow, the lowest mint pixel of each
    column becomes the lash line."""
    grid = [list(r.replace(' ', '')) for r in rows]
    for c in range(max(len(r) for r in grid)):
        mint = [r for r in range(len(grid)) if c < len(grid[r]) and grid[r][c] in 'hijW']
        for r in mint:
            grid[r][c] = 's'
        if mint:
            grid[max(mint)][c] = 'k'
    return [''.join(r) for r in grid]


SIDE_EYES = {
    'shut_hand': (
        [   # far eye, x 143..154
            "..... ..... ..",      # 61
            "..... ..... ..",      # 62
            "..... ..... ..",      # 63
            ".kk.. ..... ..",      # 64
            "..kkk ..... ..",      # 65
            "....k kk... ..",      # 66
            "..kkk ..... ..",      # 67
            ".k... ..... ..",      # 68
            "..... ..... ..",      # 69
            "..... ..... ..",      # 70
        ],
        [   # near eye, x 156..169
            "..... ..... ....",    # 62
            "..... ..... ..k.",    # 63
            "..... ...kk k...",    # 64
            "..... .kk.. ..k.",    # 65
            "...kk k.... kk..",    # 66
            ".kk.. ..kkk ....",    # 67
            "kkkkk kk... ....",    # 68
            "..... ..... ....",    # 69
            "..... ..... ....",    # 70
            "..... ..... ....",    # 71
        ]),
    'dizzy': (
        [   # far eye, x 143..154
            "..... ..... ..",      # 61
            "..... ..... ..",      # 62
            "..kkk k.... ..",      # 63
            ".kiii ik... ..",      # 64
            "kikkk kik.. ..",      # 65
            "kiki. kik.. ..",      # 66
            "kikik kik.. ..",      # 67
            ".kjjj ik... ..",      # 68
            "..kkk k.... ..",      # 69
            "..... ..... ..",      # 70
        ],
        [   # near eye, x 156..169
            "..... ..... ....",    # 62
            "..... kkkkk ....",    # 63
            "....k iiiii k...",    # 64
            "...ki kkkkk ik..",    # 65
            "...ki kiiii kik.",    # 66
            "..kik ikkki kik.",    # 67
            "..kik ikjik iik.",    # 68
            "..kjk iiiik kik.",    # 69
            "...kj kkkkk jk..",    # 70
            "....k jjjjj k...",    # 71
            ".... .kkkkk ....",    # 72
        ]),
}


SIDE_EYES['shut'] = (_shut_from(sidemaps.FAR_EYE), _shut_from(sidemaps.NEAR_EYE))


def side_eyes(name, mdx=0, mdy=0):
    far, near = SIDE_EYES[name]
    return [amap(far, sidemaps.FAR_EYE_XY[0] + mdx, sidemaps.FAR_EYE_XY[1] + mdy),
            amap(near, sidemaps.NEAR_EYE_XY[0] + mdx, sidemaps.NEAR_EYE_XY[1] + mdy)]
