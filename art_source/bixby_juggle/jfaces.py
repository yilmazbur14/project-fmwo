"""Expressions the juggle adds to the rig, registered into rig_faces' tables on import the way
rig_faces2 registers its own (the rig's files are not edited).

  'wide'  the apex take: round glowing eyes blown open with pinprick pupils and the brows shot up.
          Built on the footprint of rig_faces2's dizzy eyes, so it sits on the same skull.

Middle head maps are in head-space rows shifted by `off`; side head maps are drawn against the head
at frame.SIDE_REF, shifted by (dx, dy), as in rig_faces2.
"""
import jcommon  # noqa: F401
import rig_faces as RF
import rig_faces2 as F2  # noqa: F401  (its variants are registered first)
from pal import amap

# MIDDLE HEAD, right eye, x 98..115 (the left is its mirror)
MID_EYE_WIDE = [
    # 98-102 103-107 108-112 113-115    y
    "..... ..uuu uu... ...",       # 21  the brow, shot up and arched
    "....u ukkkk kkuu. ...",       # 22
    "...uk kk... ..kk. ...",       # 23
    "...kk ..... ...k. ...",       # 24
    "..... ..... ..... ...",       # 25
    "..... kkkkk k.... ...",       # 26
    "...kk hhhhh hkk.. ...",       # 27
    "..khh iiiii ihhk. ...",       # 28
    "..kii iiiii iiik. ...",       # 29
    ".kiii iikki iiiik ...",       # 30  a pinprick pupil,
    ".kiii iikkW iiiik ...",       # 31  a glint beside it
    ".kiii iiiii iiiik ...",       # 32
    "..kji iiiii iijk. ...",       # 33
    "..kjj jiiii ijjk. ...",       # 34
    "...kk jjjjj jkk.. ...",       # 35
    ".....kkkkk k.... ...",        # 36
]
MID_WIDE_Y0 = 21


def _mid_wide(cv, dx, off):
    right = amap(MID_EYE_WIDE, 98 + dx, MID_WIDE_Y0 + off)
    cv.stamp({(191 + 2 * dx - x, y): k for (x, y), k in right.items()}, outline=False)
    cv.stamp(right, outline=False)


RF.MID_EYES['wide'] = _mid_wide

# SIDE HEAD (the right one; drawn against the head at frame.SIDE_REF)
SIDE_EYES_WIDE = {
    'far': ([
        # 143-147 148-152 153-154   y
        "..uuu ..... ..",      # 59
        ".ukkk u.... ..",      # 60
        ".k... k.... ..",      # 61
        "..... ..... ..",      # 62
        "..kkk kk... ..",      # 63
        ".khhh hhk.. ..",      # 64
        ".kiii iik.. ..",      # 65
        ".kiik Wik.. ..",      # 66
        ".kiii iik.. ..",      # 67
        "..kjj jjk.. ..",      # 68
        "...kk kk... ..",      # 69
    ], (143, 59)),
    'near': ([
        # 156-160 161-165 166-169   y
        "..... .uuuu u...",    # 59
        "..... ukkkk kuu.",    # 60
        "....u kk... .kk.",    # 61
        "....k ..... ..k.",    # 62
        "..... kkkkk k...",    # 63
        "....k hhhhh hk..",    # 64
        "...kh iiiii iik.",    # 65
        "...ki iikkW iik.",    # 66
        "...ki iikki iik.",    # 67
        "...kj iiiii ijk.",    # 68
        "....k jjjjj jk..",    # 69
        "..... kkkkk k...",    # 70
    ], (156, 59)),
}


def _side_wide(dx, dy):
    out = []
    for key in ('far', 'near'):
        rows, (x0, y0) = SIDE_EYES_WIDE[key]
        out.append(amap(rows, x0 + dx, y0 + dy))
    return out


RF.SIDE_EYES['wide'] = _side_wide
