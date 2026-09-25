"""Expression variants for the flight set, registered into rig_faces' tables on import.

Middle head maps are in head-space rows (the head at identity, as midmaps), shifted by `off`.
Side head maps are in sidemaps' frame (the head at frame.SIDE_REF), shifted by (dx, dy).
Each eye map carries its own brow: the rig builds the head without the procedural brows for them.
"""
import math

import midmaps
import rig_faces as RF
import sidemaps
from pal import amap

#MIDDLE HEAD EYES (right eye, x 98..115; the left is its mirror)

# spent: a heavy lid over a thin, dim slit, the brow sagging at the outside
MID_EYE_TIRED = [
    # 98-102 103-107 108-112 113-115    y
    "..... ..... ..... ...",       # 24
    ".kk.. ..... ..... ...",       # 25
    ".ukkk ..... ..... ...",       # 26
    "..uuk kkk.. ..... ...",       # 27
    "....u uukkk k.... ...",       # 28
    "..... ..uuu kkkk. ...",       # 29
    "..... ..... uuukk ...",       # 30
    "..kkk kkkkk kkkkk ...",       # 31
    "..khk kiijj ihhhk ...",       # 32  (a last glint of the glow in the slit)
    "...kk kkkkk kkkk. ...",       # 33
]
# squeezed shut in pain: the brow knitted up at the inside, the eye a pinched '<'
MID_EYE_SHUT = [
    "..kk. ..... ..... ...",       # 24
    "..ukk kk... ..... ...",       # 25
    "...uu ukkkk ..... ...",       # 26
    "..... .uuuk kk... ...",       # 27
    "..... ...uu ..k.. ...",       # 28
    "..... ..... ..kkk ...",       # 29
    "..... ....k kkr.. ...",       # 30
    "..... .kkkr ..... ...",       # 31
    "...kk kr... ..... ...",       # 32
    "..... .kkkr ..... ...",       # 33
    "..... ....k kkr.. ...",       # 34
    "..... ..... ..kkk ...",       # 35
]
# dazed: a swirl in place of the glare
MID_EYE_DIZZY = [
    "..... ..... ..... ...",       # 26
    "....k kkkkk ..... ...",       # 27
    "...ki iiiii k.... ...",       # 28
    "..kii kkkii ik... ...",       # 29
    "..kik jjkki ik... ...",       # 30
    "..kik jkjki ik... ...",       # 31
    "..kik kkjki ik... ...",       # 32
    "..kii kjjki ik... ...",       # 33
    "...ki ikkii k.... ...",       # 34
    "....k kkkkk ..... ...",       # 35
]
MID_EYE_Y0 = {'tired': 24, 'shut': 24, 'dizzy': 26}
MID_EYE_MAPS = {'tired': MID_EYE_TIRED, 'shut': MID_EYE_SHUT, 'dizzy': MID_EYE_DIZZY}


def _mid_eye_variant(name):
    def f(cv, dx, off):
        right = amap(MID_EYE_MAPS[name], 98 + dx, MID_EYE_Y0[name] + off)
        cv.stamp({(191 + 2 * dx - x, y): k for (x, y), k in right.items()}, outline=False)
        cv.stamp(right, outline=False)
    return f


for _n in MID_EYE_MAPS:
    RF.MID_EYES[_n] = _mid_eye_variant(_n)


#MIDDLE HEAD TONGUE, LONG (panting): frame 0's tongue with the hanging part drawn out 8 rows further

def _longer(rows, start, n, times=1):
    return rows[:start] + rows[start:start + n] * (times + 1) + rows[start + n:]


MID_TONGUE_LONG = _longer(midmaps.TONGUE, 14, 4, 2)      # rows 79-82 repeated: +8 rows


def mid_tongue_long(dx, off):
    return amap(MID_TONGUE_LONG, midmaps.TONGUE_X0 + dx, midmaps.TONGUE_Y0 + off)


#MIDDLE HEAD YELP: the dropped jaw of the inhale with a dark throat, no fire

def _mid_yelp(cv, dx, off, tongue):
    m = off + 3
    out = {}
    for y, e in midmaps.INHALE_EDGE.items():
        for r in range(e):
            d = math.hypot(r + 0.5, (y - midmaps.THROAT[1]) * 0.85)
            k = 'k' if d < 7 else 'q'
            out[(96 + r + dx, y + m)] = k
            out[(95 - r + dx, y + m)] = k
    cv.stamp(out, outline=False)
    for p in midmaps.inhale_mouth(dx, m):
        cv.stamp(p, outline=False)
    if tongue is None:
        cv.stamp(midmaps.inhale_tongue(dx, m), outline=False)
    elif tongue:
        cv.stamp(tongue(dx, m), outline=False)


RF.MID_MOUTHS['yelp'] = _mid_yelp


#SIDE HEAD EYES (the right side head; drawn against the head at frame.SIDE_REF)

SIDE_EYES_TIRED = {
    'far': ([
        # 143-147 148-152 153-154   y
        ".kk.. ..... ..",      # 62
        ".ukkk ..... ..",      # 63
        "..uuk kk... ..",      # 64
        "..... uukk. ..",      # 65
        "..kkk kkkkk ..",      # 66
        "..khi jihkk ..",      # 67
        "...kk kkkk. ..",      # 68
    ], (143, 62)),
    'near': ([
        # 156-160 161-165 166-169   y
        "..... ...kk ....",    # 63
        "..... .kkku ....",    # 64
        "...kk kkuu. ....",    # 65
        ".kkuu u.... ....",    # 66
        "..... ..... ....",    # 67
        ".kkkk kkkkk kk..",    # 68
        ".khkk iijii hk..",    # 69
        "..kkk kkkkk k...",    # 70
    ], (156, 63)),
}
SIDE_EYES_SHUT = {
    'far': ([
        ".kk.. ..... ..",      # 62
        ".ukkk k.... ..",      # 63
        "..... ..k.. ..",      # 64
        "..... kkk.. ..",      # 65
        "...kk k.... ..",      # 66
        ".kk.. ..... ..",      # 67
        "...kk k.... ..",      # 68
        "..... kkk.. ..",      # 69
    ], (143, 62)),
    'near': ([
        "..... ...kk k...",    # 63
        "..... kkkuu ....",    # 64
        "..... ..... ....",    # 65
        "..kkk ..... ....",    # 66
        "..... kkk.. ....",    # 67
        "..... ...kk k...",    # 68
        "..... kkk.. ....",    # 69
        "..kkk ..... ....",    # 70
    ], (156, 63)),
}
SIDE_EYES_DIZZY = {
    'far': ([
        "..kkk kk... ..",      # 63
        ".kiii iik.. ..",      # 64
        ".kikk kik.. ..",      # 65
        ".kikj kik.. ..",      # 66
        ".kiik kik.. ..",      # 67
        "..kii iik.. ..",      # 68
        "...kk kk... ..",      # 69
    ], (143, 63)),
    'near': ([
        "..... kkkkk ....",    # 63
        "....k iiiii k...",    # 64
        "....k ikkki k...",    # 65
        "....k ikjki k...",    # 66
        "....k ikkji k...",    # 67
        "....k iiiii k...",    # 68
        "..... kkkkk ....",    # 69
    ], (156, 63)),
}


def _side_eye_variant(table):
    def f(dx, dy):
        out = []
        for key in ('far', 'near'):
            rows, (x0, y0) = table[key]
            out.append(amap(rows, x0 + dx, y0 + dy))
        return out
    return f


RF.SIDE_EYES['tired'] = _side_eye_variant(SIDE_EYES_TIRED)
RF.SIDE_EYES['shut'] = _side_eye_variant(SIDE_EYES_SHUT)
RF.SIDE_EYES['dizzy'] = _side_eye_variant(SIDE_EYES_DIZZY)


#SIDE HEAD TONGUE, LONG

SIDE_TONGUE_LONG = _longer(sidemaps.TONGUE, 8, 3, 2)      # +6 rows


def side_tongue_long(roar=False):
    def f(dx, dy):
        tdy = sidemaps.ROAR_TONGUE_DY if roar else 0
        return amap(SIDE_TONGUE_LONG, sidemaps.TONGUE_XY[0] + dx, sidemaps.TONGUE_XY[1] + tdy + dy)
    return f
