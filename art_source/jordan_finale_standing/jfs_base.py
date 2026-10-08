"""Jordan's four standing finale sheets (approval pass, 2026-09-28): shared base.

  jordan_getup      4 frames: up off his knees from the defeat's last frame, furious
  jordan_walk_away  6 frames: the angry stomp out of the arena, seen from behind
  jordan_rage       2 frames: the furious talk pair (shut, open)
  jordan_zap        5 frames: wind-up, thrust, hold, recover (the zap at Liam), and arms up (the rest)

Drawn in his FITTED Peach tee (the user, 2026-09-28: "yes, draw them with the fitted shirt") and redrawn
the same day in the SKINNY build ("approve the skinnier one", art_source/jordan_fit/skinny). The v2 rig
(art_source/jordan_v2/jv2_body.py) draws that build itself now; this base still calls
art_source/jordan_fit/jfit_body.apply(), which changes nothing any more, and builds its sleeves with
jfit_body's helpers, which are the rig's. The rigs are imported READ-ONLY; bytecode writing is off so
no __pycache__ lands in their folders. Every module here is named jfs_*, so none can shadow theirs.

Frames are his fight sheets' contract: 96x96, soles on row 95, the anchor (48, 95), scale 3, facing
screen-right like every sheet of his (the code mirrors him with `flips`). Parts are placed in the rigs'
BUILD coordinates; a finished frame is x - 1 (the rig's ANCHOR_SHIFT). Colours are v2's approved 40
keys through v2's palette (the pallor skin). Nothing in this module writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
FIT = os.path.join(ART, 'jordan_fit')
ANIMS = os.path.join(ART, 'jordan_anims')
for _p in (FIT, ANIMS):
    if _p not in sys.path:
        sys.path.append(_p)

import jfit_body as JF  # noqa: E402  the fitted tee (patches jv2_body in memory)
JF.apply()
import janim_base as AB  # noqa: E402  (read-only)
import janim_heads as HD  # noqa: E402  (read-only)
import janim_box as BX  # noqa: E402  (read-only)
import janim_defeat as AD  # noqa: E402  (read-only)
import janim_summon as AS  # noqa: E402  (read-only)
import janim_hit as AH  # noqa: E402  (read-only)
from imgdiff import pixel_diff  # noqa: E402,F401
from PIL import Image  # noqa: E402


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == os.path.normcase(os.path.abspath(folder))


for _m, _d in ((JF, FIT), (AB, ANIMS), (HD, ANIMS), (BX, ANIMS), (AD, ANIMS), (AS, ANIMS), (AH, ANIMS)):
    if not _same_dir(_m, _d):
        raise ImportError('%s was imported from %s, expected %s: a module-name clash' % (_m.__name__, _m.__file__, _d))

V = JF.V                     # jv2_body, patched: the thin body in the FITTED tee
V2B = JF.B                   # jv2_base: palette, audit
J = AB.jordan                # the approved redesign rig: sneakers, fist, box, pop, star
from lib import (Canvas, amap, ellipse, fill, line, paint, poly, rect, rim, stroke)  # noqa: E402,F401
from kit import capsule  # noqa: E402,F401

PAL = V2B.PAL
W = H = 96
ANCHOR = (48, 95)
ANCHOR_SHIFT = AB.ANCHOR_SHIFT
ALLOWED = AB.ALLOWED
FX_KEYS = set('WQYPOq09')          # effect pixels (sparks, steam, dust) float free of any keyline


def rows_of(rows):
    return [r.replace(' ', '') for r in rows]


def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def mirror(part, axis2):
    """Mirror a part about x = axis2 / 2 (so axis2 = 2 * the axis)."""
    return {(axis2 - x, y): k for (x, y), k in part.items()}


def stamp_all(cv, parts):
    for part, ol in parts:
        cv.stamp(part, outline=ol)


def finish(cv_or_px):
    return AB.finish(cv_or_px)


def to_image(px):
    return AB.to_image(px)


def stats(im):
    return AB.stats(im)


def audit(px, fx=()):
    return AB.audit(px, fx)


def bbox(px):
    return AB.bbox(px)


def close_gaps(part):
    return AB.close_gaps(part)


def fill_holes(px):
    for q in audit(px)['holes']:
        px[q] = 'k'
    return px


def unit(dx, dy):
    ln = math.hypot(dx, dy) or 1.0
    return dx / ln, dy / ln


#ARMS

def arm(segments, knobs=(), far=False):
    """A stick arm (jv2_body.limb): the near one lit, the far one a step darker, in his shadow."""
    if far:
        return V.limb(segments, knobs, base='c', lit='d', shade='b')
    return V.limb(segments, knobs)


def _moved(pts, dx, dy):
    return [(x + dx, y + dy) for (x, y) in pts]


def near_sleeve(root, elbow, **kw):
    """The fitted short sleeve round the top of the near upper arm (jfit_body.near_sleeve), for any
    arm that hangs or reaches out and down from the near shoulder. The collar end and the shoulder
    line move with the shoulder (root - v2's root), so a sleeve on a body moved by (dx, dy) comes
    out moved by (dx, dy)."""
    dx, dy = root[0] - JF.NEAR_ROOT[0], root[1] - JF.NEAR_ROOT[1]
    return JF.near_sleeve(root=root, elbow=elbow, collar=_moved([JF.NEAR_COLLAR], dx, dy)[0],
                          shoulder=_moved(JF.NEAR_SHOULDER, dx, dy), **kw)


def far_sleeve(root, elbow, **kw):
    dx, dy = root[0] - JF.FAR_ROOT[0], root[1] - JF.FAR_ROOT[1]
    return JF.far_sleeve(root=root, elbow=elbow, collar=_moved([JF.FAR_COLLAR], dx, dy)[0],
                         shoulder=_moved(JF.FAR_SHOULDER, dx, dy), **kw)


NEAR_ROOT = JF.NEAR_ROOT       # (40.6, 49.2)
FAR_ROOT = JF.FAR_ROOT         # (57.8, 48.5)


#HANDS (build-space maps; '.' transparent, the map carries its own keyline)

FIST_HANG = AS.FIST_HANG       # a fist clenched hanging at his side, knuckles down, lit on top (near)
BAND = AS.BAND                 # v2's pink wristband, loose on the thin wrist
FIST_UP = AS.FIST_UP           # the raised fist, palm out
HAND_OPEN = AH.HAND_OPEN       # a hand flung open, fingers splayed

# the far fist hanging, knuckles down, in his shadow (FIST_HANG a step down its ramp, lit edge right)
FIST_HANG_FAR = [
    ".kkkkk.",
    "kcddcck",
    "kccccbk",
    "kbcccbk",
    "kabcbak",
    "kakakak",
    ".kkkkk.",
]


def fixrow(rows):
    rows = rows_of(rows)
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows]


#EFFECTS (the finale's own vocabulary, snapshotted from art_source/jordan_finale_chars/jfc_front.py
# so the room reads as one piece: Matt's approved anger mark, the steam puffs)

ANGER = [
    "..kk.kk..",
    ".kTRkRRk.",
    "kTRk.kRVk",
    "kRk...kVk",
    ".k.....k.",
    "kRk...kVk",
    "kRRk.kRVk",
    ".kRRkRVk.",
    "..kk.kk..",
]
STEAM = [
    "..W0..",
    ".W00W.",
    "W0099W",
    ".999W.",
    "..99..",
]
STEAM_S = [
    ".W0.",
    "W009",
    ".99.",
]


def overlay(cv, rows, x0, y0, fx=None, only_empty=False):
    """Lay a map straight onto the canvas (no outline): '.' keeps what is under it. With `fx` the
    pixels are recorded as effects; only_empty keeps the figure in front of the effect."""
    for q, k in amap(rows_of(rows), x0, y0).items():
        if only_empty and q in cv.px:
            continue
        cv.px[q] = k
        if fx is not None:
            fx.add(q)


#HEADS

def head(rows, dx, dy, hair='v2', row21=None):
    """A face (rows 22 down, janim_heads' head space: x 37.., y 10..) under v2's greasy hair (or the
    flopped quiff), moved by (dx, dy): janim_heads.head's method, on any face rows."""
    face = {q: k for q, k in amap(rows, HD.X0, HD.Y0).items() if q[1] >= 22}
    part = dict(face)
    part.update(HD._flopped_hair() if hair == 'flopped' else HD.V2H.hair())
    part.update(row21 or {})
    return shift(part, dx, dy)


def tilt(part, deg, pivot):
    t = AB.tilt2(part, deg, pivot, 'xy')
    close_gaps(t)
    return t
