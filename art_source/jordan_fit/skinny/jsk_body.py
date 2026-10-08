"""Jordan SKINNIER, in an even tighter tee: APPROVAL PASS (the user, 2026-09-28, after seeing the
fitted tee everywhere: "i want jordan even skinnier and his shirt even more fitted").

APPROVED the same day ("approve the skinnier one", the 15px proposal below) and FOLDED INTO THE RIGS:
art_source/jordan_v2/jv2_body.py draws these parts itself now, so apply() refuses to run (it would
thin him twice). This module and its previews are the approval record.

Nothing here edits a rig. The rigs are imported READ-ONLY with bytecode writing off; apply() swaps
the skinny parts into the imported module OBJECTS, in memory, for the life of one process:
  jv2_body (V)          the fight rig's body. Every builder that draws through it (v2's two frames,
                        the fight sheets' janim_*, the standing finale's jfs_*) draws the skinny build;
  torso.PRINT           the approved rig's Peach print, its two side outline columns cropped off;
  jfit_body (JF)        if given: the standing finale's base applies it over V, so its tee and sleeves
                        are patched the same way;
  jfc_base / jfc_front  if given: the seated finale's own tee outline, sleeves, limbs and legs.
restore() puts every part back.

WHAT CHANGES (build coordinates; a frame is x - 1). The proposal is VARIANT 'cropped':
  - chest: 15px (x 42-56, the fitted tee's was 19, x 40-58). The Peach print is the widest thing on
    him, so its two side OUTLINE columns come off: her hair runs to one pixel of the tee's red at
    each side, inside the tee's keyline. The print keeps its size, place, face, crown and dress;
  - waist: the tee tapers in under the print to 13px (x 43-55) and the pink hem hugs his hips there;
    the jeans' seat comes in to match (x 43-55, was 41-57);
  - arms: every stick-arm segment ARM_THIN thinner in radius (about a pixel off its width), the bony
    elbow knobs KNOB_THIN thinner, so the elbows still bulge. No joint moves: shoulders, elbows and
    hands stay exactly where they were, so every hand point and prop placement is unchanged;
  - legs: thinner jeans (row spans below): 4px thighs (were 5), 5px knees still knocking together
    (were 6), 4px shins (were 5-6), the stacks narrower at the top and spreading onto the sneakers at
    their base exactly as the fitted ones do;
  - sleeves: tighter round the thinner arms (half-width SLEEVE_HALF, was 2.5) and shorter (SLEEVE_LEN
    of their length); the fist-pump's cuff narrowed round the thinner raised arm;
  - one keyline pixel added beside the far hand's wrist (FAR_HAND_BOX), where the thinner forearm and
    tighter far sleeve would leave a pinhole.
VARIANT 'whole' (JSK_VARIANT=whole) keeps the print whole: a 17px chest (x 41-57) with a pixel of red
outside the print's own outline, a 15px waist (x 42-56); the rest as above.

Kept: his height, head, face, hair, beard, neck, hands, sneakers, the loose collar and its trim, the
drip, smudge and dandruff, the colours (the approved 40 keys), the pure-black keyline, the 96x96
frame, the anchor (48, 95) and the soles on row 95.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(os.path.dirname(HERE))
V2_DIR = os.path.join(ART, 'jordan_v2')
if V2_DIR not in sys.path:
    sys.path.append(V2_DIR)

import jv2_base as B  # noqa: E402  (read-only)
import jv2_body as V  # noqa: E402  (read-only; apply() patches the module object in memory only)
from jv2_base import fill, poly, span, stroke  # noqa: E402

if os.path.normcase(os.path.dirname(os.path.abspath(V.__file__))) != os.path.normcase(os.path.abspath(V2_DIR)):
    raise ImportError('jv2_body came from %s, not %s' % (V.__file__, V2_DIR))


#THE NUMBERS

ARM_THIN = float(os.environ.get('JSK_ARM_THIN', '0.5'))    # off every arm segment's radius
KNOB_THIN = 0.35               # off every elbow knob's radius
MIN_R, MIN_KNOB = 0.75, 1.2
SLEEVE_HALF = 2.0              # the sleeve's half-width round the arm (the fitted tee's: 2.5)
SLEEVE_LEN = 0.85              # of the fitted sleeve's length down the arm

# VARIANT 'cropped' (the proposal): the chest 15px (x 42-56), the print's side outline columns cropped
#   off so her hair runs to a pixel of red inside the keyline; the waist 13px (x 43-55).
# VARIANT 'whole': the chest one pixel of red outside the whole 15px print (x 41-57), the waist 42-56.
VARIANT = os.environ.get('JSK_VARIANT', 'cropped')
if VARIANT == 'cropped':
    NEAR_X, FAR_X = 41.6, 56.4
    WAIST_NEAR, WAIST_FAR = 42.6, 55.4
else:
    NEAR_X, FAR_X = 40.6, 57.4     # the chest's side seams: pixel centres 41..57 (fitted: 40..58)
    WAIST_NEAR, WAIST_FAR = 41.6, 56.4     # the waist's: 42..56, the print's own width
CROP_PRINT = VARIANT == 'cropped'
HEM_Y = V.HEM_Y                # 69.3, unchanged
HEM_Y_SEATED = 67.4            # jfc_front's seated hem, unchanged


def thin(r):
    return max(MIN_R, r - ARM_THIN)


def thin_knob(r):
    return max(MIN_KNOB, r - KNOB_THIN)


#THE TEE

def torso_outline(hem_y=HEM_Y):
    """The skinny tee: v2's narrow sloped shoulders (the collar and neck untouched), the sides close
    down his chest a pixel outside the print, tapering in under it to his narrow waist, the level hem
    on his hips with its one rumple."""
    n, f, wn, wf = NEAR_X, FAR_X, WAIST_NEAR, WAIST_FAR
    return [(44.4, 43.4), (55.6, 43.4), (57.2, 44.4), (58.0, 46.4),                   # far shoulder
            (f + 0.1, 50.0), (f, 56.0), (f, 60.4), (wf, 62.6), (wf, hem_y - 0.3),      # far side
            (54.0, hem_y), (52.6, hem_y + 0.9), (51.4, hem_y + 0.9), (49.8, hem_y), (46.0, hem_y - 0.1),
            (wn + 1.2, hem_y + 0.1), (wn, hem_y - 0.4),                                 # near corner
            (wn, 62.6), (n, 60.4), (n, 56.0), (n - 0.1, 50.0),                          # near side
            (41.2, 46.4), (42.4, 44.6)]                                                 # near shoulder


def shirt(frame=0):
    """jv2_body.shirt, line for line, on the skinny outline (its folds guarded, since the narrower waist
    leaves some of v2's fold pixels outside the tee)."""
    from jv2_base import amap
    part = fill(poly(torso_outline(HEM_Y)), 'R')
    for x, yc in V.COLLAR.items():
        for y in range(40, yc):
            part.pop((x, y), None)
    red = {'lit': 'T', 'base': 'R', 'shade': 'V', 'deep': 'v'}
    pink = {'lit': 'Q', 'base': 'P', 'shade': 'q', 'deep': 'q'}
    for (x, y) in list(part):
        lo, hi = span(part, y)
        t = (x - lo) / max(1, hi - lo)
        ramp = pink if y >= V.BAND_Y else red
        k = ramp['base']
        if t <= 0.06:
            k = ramp['lit']
        elif t >= 0.95:
            k = ramp['deep']
        elif t >= 0.76:
            k = ramp['shade']
        elif y < V.BAND_Y and 0.1 <= t <= 0.24 and 46 <= y <= 52:
            k = ramp['lit']
        part[(x, y)] = k
    for x, yc in V.COLLAR.items():
        if (x, yc) in part:
            part[(x, yc)] = '1'
    for (x, y) in list(part):
        if y == V.BAND_Y and (x < V.PRINT_X0 or x > V.PRINT_X1):
            part[(x, y)] = 'k'
    rows = B.rows_of(V.T.PRINT)                        # (cropped by apply() in the 'cropped' variant)
    for q, k in amap(rows, *V.PRINT_AT).items():
        if q in part:
            part[q] = k

    def fold(pts, key='q', only='PQ'):
        for q in pts:
            if q in part and part[q] in only:
                part[q] = key
    if frame == 0:
        fold(((42, 64), (43, 64), (44, 64), (45, 65), (46, 65)))
        fold(((42, 63), (43, 63), (45, 64)), 'Q', 'P')
        fold(((42, 66), (43, 66), (44, 67), (45, 67)))
        fold(((44, 66),), 'Q', 'P')
    else:
        fold(((43, 66), (44, 66), (45, 67), (46, 67)))
        fold(((44, 65), (45, 66)), 'Q', 'P')
    fold(((52, 68), (51, 67)))
    for q in ((55, 46), (56, 46), (56, 47)):
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'b'
    for q in ((54, 66), (55, 66), (55, 67)):
        if q in part:
            part[q] = 'c'
    return part


def cropped_print(rows):
    """The approved Peach print with its two side outline columns left off ('.' = the tee shows)."""
    out = []
    for r in B.rows_of(rows):
        assert len(r) == 15, r
        out.append('.' + r[1:14] + '.')
    return out


#SLEEVES AND ARMS

def thin_limb(orig):
    """A limb builder with every segment and knob thinned; the joints stay where they are."""
    def limb(segments, knobs=(), *a, **kw):
        segs = [(p0, p1, thin(r0), thin(r1)) for (p0, p1, r0, r1) in segments]
        kn = [(cx, cy, thin_knob(r)) for (cx, cy, r) in knobs]
        return orig(segs, kn, *a, **kw)
    limb.skinny = True
    limb.orig = orig
    return limb


def tight_sleeve_outline(orig):
    """A sleeve_outline with the sleeve tighter round the arm and shorter down it."""
    def sleeve_outline(root, elbow, collar, shoulder, outward, length=5.2, half=2.5):
        return orig(root, elbow, collar, shoulder, outward, length=length * SLEEVE_LEN,
                    half=SLEEVE_HALF + (half - 2.5))
    sleeve_outline.skinny = True
    sleeve_outline.orig = orig
    return sleeve_outline


# the fist-pump's cuff, ridden up round the top of the raised arm: a pixel of cloth either side of the
# thinner arm (the fitted tee's is jv2_body.RAISED_CUFF)
RAISED_CUFF = [(36.4, 43.2), (41.8, 43.2), (43.0, 44.2), (43.6, 45.8), (42.6, 48.0), (40.9, 50.0),
               (39.9, 50.0), (37.9, 47.8), (36.5, 45.4)]


# v2's hand round the box's base (jv2_body.FAR_HAND_BOX) with one keyline pixel added at the left of the
# wrist: the thinner forearm and tighter far sleeve leave a pinhole there (build (62, 49))
FAR_HAND_BOX = list(V.FAR_HAND_BOX)
assert FAR_HAND_BOX[5] == "..kbk."
FAR_HAND_BOX[5] = ".kkbk."


#JEANS

# The skinny jeans as row spans (build x, inclusive; the stamp's keyline goes round them), so every
# width is exact. v2's fitted legs were 5px thighs, 6px knees and 5-6px shins; these are a pixel
# thinner all the way down, the bony knees still knocking together (their keylines touch, rows 76-78),
# a narrow thigh gap under the crotch as before, the stacks at the ankles narrower at the top and
# spreading onto the sneakers at their base exactly as v2's do (the shoes' top edges need that cover).
_W0, _W1 = int(round(WAIST_NEAR + 0.4)), int(round(WAIST_FAR - 0.4))
HIP_ROWS = {y: (_W0, _W1) for y in range(64, 71)}       # under the tee: the seat, the waist's width
HIP_ROWS[71] = (43, 55)                                  # the crotch: the seat's last row
NEAR_ROWS = {71: (43, 46), 72: (43, 46), 73: (43, 46), 74: (43, 46), 75: (44, 47), 76: (44, 47),
             77: (44, 48), 78: (44, 47), 79: (44, 47), 80: (43, 46), 81: (43, 46), 82: (42, 45),
             83: (42, 45), 84: (40, 45), 85: (40, 45), 86: (40, 45), 87: (39, 46), 88: (39, 46)}
FAR_ROWS = {71: (52, 55), 72: (52, 55), 73: (52, 55), 74: (51, 54), 75: (51, 54), 76: (50, 54),
            77: (50, 54), 78: (50, 54), 79: (51, 54), 80: (51, 54), 81: (52, 55), 82: (52, 55),
            83: (53, 56), 84: (53, 57), 85: (53, 57), 86: (53, 57), 87: (53, 58), 88: (53, 58)}


def _rows(rows):
    return {(x, y) for y, (a, b) in rows.items() for x in range(a, b + 1)}


def legs():
    """v2's jeans (jv2_body.legs) on the thinner legs: the same shading and details, re-placed."""
    near, far, hips = _rows(NEAR_ROWS), _rows(FAR_ROWS), _rows(HIP_ROWS)
    jeans = fill(near | far | hips, 'N')
    for (x, y) in list(jeans):
        if (x, y) in near and y >= 72:
            lo, hi = span(near, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x == hi else 'N'))
        elif (x, y) in far and y >= 72:
            lo, hi = span(far, y)
            k = 's' if x == lo + 1 else ('n' if x in (lo, hi) else 'N')
        else:
            lo, hi = span(jeans, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x >= hi - 1 else 'N'))
        jeans[(x, y)] = k
    stroke(jeans, [(49, 66), (49, 71)], 'n')                          # the fly, under the hem
    for q in ((46, 76), (46, 77), (47, 77)):                           # the kneecaps poke through
        if jeans.get(q) in ('N', 'n'):
            jeans[q] = 's'
    for q in ((51, 76), (51, 77), (50, 77)):
        if jeans.get(q) in ('N', 'n'):
            jeans[q] = 's'
    for q in ((45, 80), (45, 81)):                                     # the fold behind each knee
        if jeans.get(q) == 'N':
            jeans[q] = 'n'
    for q in ((53, 80), (53, 81)):
        if jeans.get(q) == 'N':
            jeans[q] = 'n'
    stroke(jeans, [(44, 73), (45, 74)], 'n', only='N')                # slack drags down the thighs
    stroke(jeans, [(53, 72), (53, 73)], 'n', only='N')
    stroke(jeans, [(40, 85), (42, 86), (45, 85)], 'n', only='NsS')    # the stacks at the ankles
    stroke(jeans, [(40, 87), (43, 87), (45, 86)], 's', only='N')
    stroke(jeans, [(53, 85), (55, 86), (57, 85)], 'n', only='Ns')
    stroke(jeans, [(54, 87), (57, 87)], 's', only='N')
    return jeans


#PATCHING (in memory only)

_SAVED = {}


def _save(mod, name):
    _SAVED.setdefault((id(mod), name), (mod, name, getattr(mod, name)))


def _set(mod, name, value):
    _save(mod, name)
    setattr(mod, name, value)


def apply(jf=None, seated=None):
    """Swap the skinny build in. jf: the loaded jfit_body module (the standing finale's base applies
    it over V). seated: (jfc_base, jfc_front) for the seated finale."""
    if getattr(V.limb, 'skinny', False):
        raise RuntimeError('already applied')
    if hasattr(V, 'ARM_THIN'):
        raise RuntimeError('the v2 rig already draws the skinny build (folded into jv2_body.py on '
                           '2026-09-28 after approval): applying this patch would thin him twice')
    _set(V, 'limb', thin_limb(V.limb))
    _set(V, 'sleeve_outline', tight_sleeve_outline(V.sleeve_outline))
    if CROP_PRINT:
        _set(V.T, 'PRINT', cropped_print(V.T.PRINT))
    _set(V, 'TORSO', torso_outline(HEM_Y))
    _set(V, 'shirt', shirt)
    _set(V, 'NEAR_X', NEAR_X)
    _set(V, 'FAR_X', FAR_X)
    _set(V, 'RAISED_CUFF', RAISED_CUFF)
    _set(V, 'legs', legs)
    _set(V, 'raised_sleeve', raised_sleeve)
    _set(V, 'FAR_HAND_BOX', FAR_HAND_BOX)
    if jf is not None:
        _set(jf, 'torso_outline', lambda frame=0: torso_outline(HEM_Y))
        _set(jf, 'sleeve_outline', tight_sleeve_outline(jf.sleeve_outline))
        _set(jf, 'NEAR_X', NEAR_X)
        _set(jf, 'FAR_X', FAR_X)
        _set(jf, 'raised_sleeve', raised_sleeve)      # jfit's has the fitted cuff written in
    if seated is not None:
        cb, cf = seated
        _set(cb, 'limb', thin_limb(cb.limb))
        _set(cf, 'sleeve_outline', tight_sleeve_outline(cf.sleeve_outline))
        _set(cf, 'TORSO_SEATED', torso_outline(HEM_Y_SEATED))
        _set(cf, 'FIT_NEAR_X', NEAR_X)
        _set(cf, 'FIT_FAR_X', FAR_X)
        _set(cf, 'legs', seated_legs(cb, cf))


def raised_sleeve(arm):
    """jv2_body.raised_sleeve's rendering on the skinny RAISED_CUFF: red, lit left, dark underneath,
    the tension fold from the armpit, the trim round the opening."""
    from jv2_base import rim
    part = fill(poly(RAISED_CUFF), 'R')
    rim(part, 'T', -1, 0)
    rim(part, 'V', 1, 0)
    rim(part, 'v', 0, 1, only='RV')
    stroke(part, [(40, 47), (41, 49)], 'V', only='RT')
    top = min(y for (x, y) in part)
    for (x, y) in list(part):
        if y == top:
            part[(x, y)] = '1'
    return part


def restore():
    for (mod, name, value) in reversed(list(_SAVED.values())):
        setattr(mod, name, value)
    _SAVED.clear()


class skinny:
    """with skinny(): ... builds with the skinny build; the parts come back after."""
    def __init__(self, jf=None, seated=None):
        self.jf, self.seated = jf, seated

    def __enter__(self):
        apply(self.jf, self.seated)
        return self

    def __exit__(self, *a):
        restore()
        return False


#THE SEATED FINALE (jfc_front's legs, thinner)

def seated_legs(cb, cf):
    """jfc_front.legs on thinner legs: the same joints, the jeans' radii down by about a pixel of width,
    the knees still bony, the slack hems still bunched at the ankles."""
    def legs():
        cv = cb.Canvas(96, 96)
        far_thigh = cf.jeans_limb([((49.5, 61.5), (39.5, 67.8), 2.4, 2.0)], knobs=((38.8, 68.2, 2.0),))
        far_shin = cf.jeans_limb([((38.6, 69.5), (37.6, 84.5), 1.6, 1.5), ((37.6, 84.5), (37.4, 87.0), 2.2, 2.5)])
        near_thigh = cf.jeans_limb([((55.5, 63.6), (45.4, 70.6), 2.7, 2.2)], knobs=((44.6, 71.0, 2.1),))
        near_shin = cf.jeans_limb([((44.4, 72.4), (43.6, 87.5), 1.7, 1.6), ((43.6, 87.5), (43.4, 90.0), 2.3, 2.6)])
        cv.stamp(far_shin)
        cv.stamp(far_thigh)
        cv.stamp(near_shin)
        cv.stamp(near_thigh)
        px = cv.px
        for q in ((39, 67), (40, 67), (45, 70), (46, 70)):
            if px.get(q) in ('N', 'n'):
                px[q] = 's'
        for pts in (((36, 84), (38, 85), (39, 84)), ((42, 87), (44, 88), (45, 87))):
            for a, b in zip(pts, pts[1:]):
                for q in cb.line(a[0], a[1], b[0], b[1]):
                    if px.get(q) == 'N':
                        px[q] = 'n'
        return px
    legs.skinny = True
    return legs
