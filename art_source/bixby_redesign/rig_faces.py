"""Expressions for the rig's heads: which hand-drawn maps go on for a given mouth / eyes.

Middle head (row offset `off` = the head's offset from head space, as midmaps expects):
  mouths: 'snarl' (approved frame 0), 'inhale' (approved frame 2: jaw dropped, fire in the throat)
  eyes:   'open' (approved)
Side head (maps drawn against the head at frame.SIDE_REF, offset mdx/mdy):
  mouths: 'snarl', 'roar' (approved)
  eyes:   'open'
More variants are added in rig_faces2.py and registered in the tables below.
"""
import midmaps
import sidemaps
from pal import amap

MID_MOUTHS = {}
MID_EYES = {}
SIDE_MOUTHS = {}
SIDE_EYES = {}


def _mid_snarl(cv, dx, off, tongue):
    cv.stamp(midmaps.mouth_part(dx, off), outline=False)
    if tongue is None:
        cv.stamp(midmaps.tongue_part(dx, off), outline=False)
    elif tongue:
        cv.stamp(tongue(dx, off), outline=False)


def _mid_inhale(cv, dx, off, tongue):
    m = off + 3             # the inhale maps were drawn with the head 3 rows above frame 0's
    cv.stamp(midmaps.inhale_glow(dx, m), outline=False)
    for p in midmaps.inhale_mouth(dx, m):
        cv.stamp(p, outline=False)
    if tongue is None:
        cv.stamp(midmaps.inhale_tongue(dx, m), outline=False)
    elif tongue:
        cv.stamp(tongue(dx, m), outline=False)


def _mid_open_eyes(cv, dx, off):
    for e in midmaps.eye_parts(dx, off):
        cv.stamp(e, outline=False)


MID_MOUTHS.update(snarl=_mid_snarl, inhale=_mid_inhale)
MID_EYES.update(open=_mid_open_eyes)


def mid_mouth(cv, mouth, dx, off, tongue=None):
    MID_MOUTHS[mouth](cv, dx, off, tongue)


def mid_eyes(cv, eyes, dx, off):
    MID_EYES[eyes](cv, dx, off)


def _side_mouth(roar):
    def f(dx, dy):
        rows = sidemaps.ROAR if roar else sidemaps.MOUTH
        return amap(rows, sidemaps.MOUTH_XY[0] + dx, sidemaps.MOUTH_XY[1] + dy)
    return f


def _side_tongue(roar):
    def f(dx, dy):
        tdy = sidemaps.ROAR_TONGUE_DY if roar else 0
        return amap(sidemaps.TONGUE, sidemaps.TONGUE_XY[0] + dx, sidemaps.TONGUE_XY[1] + tdy + dy)
    return f


def _side_open_eyes(dx, dy):
    return [amap(sidemaps.FAR_EYE, sidemaps.FAR_EYE_XY[0] + dx, sidemaps.FAR_EYE_XY[1] + dy),
            amap(sidemaps.NEAR_EYE, sidemaps.NEAR_EYE_XY[0] + dx, sidemaps.NEAR_EYE_XY[1] + dy)]


SIDE_MOUTHS.update(snarl=(_side_mouth(False), _side_tongue(False)),
                   roar=(_side_mouth(True), _side_tongue(True)))
SIDE_EYES.update(open=_side_open_eyes)


def side_face(cv, mouth, eyes, dx, dy, tongue=None):
    """Back to front, as sidemaps.parts: mouth, tongue, far eye, near eye."""
    m, t = SIDE_MOUTHS[mouth]
    cv.stamp(m(dx, dy), outline=False)
    if tongue is None:
        cv.stamp(t(dx, dy), outline=False)
    elif tongue:
        cv.stamp(tongue(dx, dy), outline=False)
    for e in SIDE_EYES[eyes](dx, dy):
        cv.stamp(e, outline=False)
