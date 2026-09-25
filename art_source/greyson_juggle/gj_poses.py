"""Greyson's juggle: twelve frames in Mason's order (the juggle contract), on the approved rig.

  0-1    HIT     the uppercut lands under his chin: the head snaps back, the eyes squeeze shut to
                 > <, the jaw drops, both arms fly up (the cannon with them), sweat flies off his
                 temple; then the lift, his boots leaving the mat.
  2-6    TUMBLE  2 is the apex hang: tipped back past level, limp, elbows folded, legs loose,
                 eyes blown wide; 3-6 are one full backward turn, a quarter a frame, spread out
                 like a starfish with the elbows loose, his head lagging the turn and his pupils
                 rolling round behind the glasses. The hang is also the loop's in-between (-30,
                 -75, -120), so the loop turns evenly through it.
  7-9    CRASH   flat on his back on the mat, squashed, teeth clenched; the bounce; the settle.
  10-11  DOWN    lying there KO'd: an X in each lens, tongue out, the chest rising and falling.

THE BARBELL IS DROPPED (the brief): no frame carries it. The cannon stays on his left forearm
throughout, as the approved fight sheets wear it.

He turns BACKWARDS (negative, anticlockwise angles). His sheets are drawn facing right (the plan's
`flips`), so an uppercut to the chin throws his head back to the left and his feet over to the
right, and he comes down on his back with his head to the left (Computah's and Carter's juggles
do the same).

Every pose is the approved parts re-hinged (gj_body.Fig): nothing is redrawn but the faces
(gj_faces) and the effects (gj_fx).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gj_rig as R    # noqa: E402
import gj_body as GB  # noqa: E402
import gj_faces as FC  # noqa: E402
import gj_fx as X     # noqa: E402

Fig = GB.Fig
FEET = R.FEET
LIE_X = 78            # the lying body's middle column: knocked back, clear of the player
SPIN_Y = 85           # the tumble's turning point, on the frame


PAD = 64


def render(F):
    head, face = FC.head(F.face)
    return GB.draw(F, head, face)


def extent(F):
    """His whole extent on the frame, measured on a padded canvas: nothing clipped."""
    head, face = FC.head(F.face)
    x0, y0, x1, y1 = GB.extent(GB.draw(F, head, face, pad=PAD))
    return (x0 - PAD, y0 - PAD, x1 - PAD, y1 - PAD)


def grounded(F, x_mid=None, lift=0):
    """F drawn with its lowest pixel `lift` rows over the feet row (and, given x_mid, its middle
    column there): the ground frames. Measured unclipped, and moved by whole pixels only, so a
    quarter turn stays a texel-for-texel copy."""
    x0, y0, x1, y1 = extent(F)
    dx = 0 if x_mid is None else int(round(x_mid - (x0 + x1) / 2.0))
    dy = FEET[1] - lift - y1
    F.at = (F.at[0] + dx, F.at[1] + dy)
    return render(F)


def head_at(cv, x, y):
    """A point of his head (his own space) in the frame."""
    return cv.tf['head'].fwd(x, y)


# ------------------------------------------------------------------------------------ frames

def _ground_puffs(cv, big=2.6, small=1.6):
    """Dust kicked up either side of his boots (their widest over the bottom rows)."""
    runs = [r for y in range(FEET[1] - 6, FEET[1] + 1) for r in X.soles(cv, y)]
    if not runs:
        return
    l, r = min(a for a, _ in runs), max(b for _, b in runs)
    X.puff(cv, (l - 5, FEET[1] - 3), big)
    X.puff(cv, (l - 11, FEET[1] - 2), small)
    X.puff(cv, (r + 5, FEET[1] - 3), big)
    X.puff(cv, (r + 11, FEET[1] - 2), small)


def hit():
    """The uppercut lands: the head snapped back, eyes squeezed shut, jaw dropped, both arms flung
    up and out, the boots still on the mat; sweat knocked off his temple, shock lines round his
    head, dust at his feet."""
    F = Fig(angle=-6, pivot=GB.SOLES, at=FEET, arm=(110, -20), gun=(110, -20), legs=(6, 6),
            head=-6, head_shift=(-1.0, -2.0), face='jolt', flare=1.0)
    cv = grounded(F)
    hx, hy = head_at(cv, 56, 40)
    X.ticks(cv, (hx, hy), 25, 28, (-160, -125, -55, -20))
    X.drop(cv, (int(hx) - 33, int(hy) - 16))
    X.drop(cv, (int(hx) - 25, int(hy) - 27))
    _ground_puffs(cv)
    return cv


def lift():
    """Off the mat: tipping back, the arms thrown up over him, the legs trailing; the dust he
    left behind below."""
    F = Fig(angle=-24, at=(94, 92), arm=(128, -12), gun=(122, -15), legs=(-4, 16),
            head=8, head_shift=(-1.0, -1.0), face='jolt', flare=1.0)
    cv = render(F)
    X.puff(cv, (79, 140), 3.0)
    X.puff(cv, (114, 140), 3.0)
    X.puff(cv, (71, 141.5), 1.6)
    X.puff(cv, (122, 141.5), 1.6)
    return cv


def hang():
    """The apex: tipped back past level, limp, the elbows folded, the legs loose, the eyes blown
    wide. It is also the loop's in-between (spin_d's -30 degrees, this -75, spin_a's -120), so it
    turns about the same point as the spin. The head lolls back on the neck to a quarter turn (a
    texel-for-texel copy of the face)."""
    F = Fig(angle=-75, at=(96, SPIN_Y), arm=(60, -45), gun=(50, -45), legs=(30, 0), head=-15,
            face='gasp', flare=0.8)
    return render(F)


# One backward turn, a quarter a frame. The head lags the turn by 30 degrees on the neck, which
# also lands every face on a quarter turn (a texel-for-texel copy of the approved grid).
SPIN = (-120.0, -210.0, -300.0, -390.0)
# (arm, gun, legs) per frame: spread like a starfish, the elbows loose, each limb flopping a
# little differently from frame to frame
SPIN_LIMBS = (((70, -20), (74, -12), (16, 12)), ((76, -24), (68, -8), (12, 16)),
              ((68, -16), (76, -14), (16, 14)), ((74, -22), (70, -10), (14, 16)))


def spin(i):
    arm, gun, legs = SPIN_LIMBS[i]
    F = Fig(angle=SPIN[i], at=(96, SPIN_Y), arm=arm, gun=gun, legs=legs, head=30.0,
            face='roll%d' % i, flare=1.0)
    cv = render(F)
    c = (96, SPIN_Y)
    # he turns anticlockwise: on the left he is moving down, on the right up; each arc's bright
    # lead is where he is going, its tail where he was
    wob = (0, 12, 4, 16)[i]
    X.swoosh(cv, c, 212 - wob, 152 - wob)
    X.swoosh(cv, c, 32 - wob, -28 - wob)
    return cv


def _mat_puffs(cv, r0=3.2, r1=2.2):
    x0, y0, x1, y1 = GB.extent(cv)
    for (x, r) in ((x0 - 5, r0), (x0 - 11, r1), (x1 + 5, r0), (x1 + 11, r1)):
        X.puff(cv, (x, FEET[1] - 3.5), r)


def crash():
    """Back first onto the mat, squashed flat, teeth clenched; dust out both ends."""
    F = Fig(angle=-90, at=(LIE_X, 100), squash=(1.08, 0.82), arm=(0, 0), gun=(20, 0),
            legs=(14, 10), face='crash', flare=1.5, gun_face=0.5)
    cv = grounded(F, LIE_X)
    _mat_puffs(cv)
    x0, y0, x1, y1 = GB.extent(cv)
    X.ticks(cv, ((x0 + x1) / 2.0, FEET[1]), 52, 55, (-168, -156, -24, -12))
    return cv


def bounce():
    """Up off the mat again, everything flung up, dazed."""
    F = Fig(angle=-80, at=(LIE_X, 96), arm=(-4, 30), gun=(58, -10), legs=(34, -14),
            head=-10, face='daze', flare=1.0)
    cv = grounded(F, LIE_X, lift=9)     # up off the mat
    x0, y0, x1, y1 = GB.extent(cv)
    X.puff(cv, (x0 + 6, FEET[1] - 2.5), 2.4)
    X.puff(cv, (x1 - 8, FEET[1] - 2.5), 2.4)
    return cv


LIE = dict(angle=-90, at=(LIE_X, 100), arm=(10, 0), gun=(30, 0), legs=(12, 8), face='ko',
           gun_face=0.5)


def settle():
    """Down: the limbs still coming to rest (the cannon arm dropping, the legs settling), the
    lights going out."""
    kw = dict(LIE, arm=(14, 4), gun=(42, -8), legs=(16, 11))
    return grounded(Fig(flare=1.0, **kw), LIE_X)


def down(breath):
    """Lying KO'd, breathing: the ribcage swells (the lats spread) and the arms ride out on it."""
    kw = dict(LIE)
    kw['arm'] = (LIE['arm'][0] + 3 * breath, 0)
    kw['gun'] = (LIE['gun'][0] + 3 * breath, 0)
    return grounded(Fig(flare=0.5 + 2.5 * breath, **kw), LIE_X)


# (name, builder, suggested hold in seconds)
FRAMES = [
    ('hit', hit, 0.06),
    ('lift', lift, 0.08),
    ('hang', hang, 0.16),
    ('spin_a', lambda: spin(0), 0.07),
    ('spin_b', lambda: spin(1), 0.07),
    ('spin_c', lambda: spin(2), 0.07),
    ('spin_d', lambda: spin(3), 0.07),
    ('crash', crash, 0.06),
    ('bounce', bounce, 0.08),
    ('settle', settle, 0.12),
    ('down_out', lambda: down(0.0), 0.4),
    ('down_in', lambda: down(1.0), 0.4),
]
TAGS = {'launch': (0, 1, False), 'tumble': (2, 6, True), 'crash': (7, 9, False),
        'down': (10, 11, True)}


def build(i):
    return FRAMES[i][1]()
