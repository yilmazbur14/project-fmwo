"""Re-posing the APPROVED arm to new joints, for the takeover sheets.

The approved idle arm (gr_arms.IDLE) is traced as muscle polygons: the delt cap, the upper arm (the
triceps), the biceps, the forearm and its brachioradialis bulge. repose() carries those very
polygons (and their forms) to a new shoulder, elbow and wrist: each is moved by its bone's
similarity transform (the idle bone onto the new bone: turn, stretch, shift), the upper-arm
regions by the upper bone and the forearm regions by the lower bone, the delt turning half as far
as the upper arm (it caps the shoulder, which turns less than the arm). The result is shaded by
gf_fig.arm_layer exactly as the approved arms are, so a re-posed arm keeps the approved shapes,
widths and lines instead of being redrawn. Left-side coordinates (screen left); gf_fig.arm_layer
mirrors them for the right arm and keeps the light upper left.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
from gr_muscle import Form  # noqa: E402

gr_arms, K = B.gr_arms, B.K

# The approved idle arm's joints (gf_fig / gr_fig.Pose('idle'))
S0, E0, W0 = (30.0, 56.0), (21.0, 71.0), (25.0, 82.0)
UPPER = ('upper', 'biceps')
LOWER = ('forearm', 'brach')


def _sim(a0, b0, a1, b1, turn=1.0):
    """The similarity taking segment a0-b0 onto a1-b1 (only `turn` of the rotation; the length
    is matched along the new bone)."""
    ang0 = math.atan2(b0[1] - a0[1], b0[0] - a0[0])
    ang1 = math.atan2(b1[1] - a1[1], b1[0] - a1[0])
    rot = (ang1 - ang0) * turn
    s = math.hypot(b1[0] - a1[0], b1[1] - a1[1]) / (math.hypot(b0[0] - a0[0], b0[1] - a0[1]) or 1)
    c, si = math.cos(rot) * s, math.sin(rot) * s

    def f(p):
        dx, dy = p[0] - a0[0], p[1] - a0[1]
        return (a1[0] + dx * c - dy * si, a1[1] + dx * si + dy * c)
    return f


def _form(form, f):
    if form.axis is not None:
        (x0, y0), (x1, y1) = form.axis
        return Form(axis=[f((x0, y0)), f((x1, y1))], r=form.r, flat=form.flat)
    cx, cy, rx, ry = form.ell
    nx, ny = f((cx, cy))
    return Form(ellipsoid=(nx, ny, rx, ry), flat=form.flat)


def repose(shoulder, elbow, wrist, delt_turn=0.5):
    """-> (polys, forms) of the approved idle arm carried to the given joints."""
    fu = _sim(S0, E0, shoulder, elbow)
    fd = _sim(S0, E0, shoulder, elbow, turn=delt_turn)
    fl = _sim(E0, W0, elbow, wrist)
    polys, forms = {}, {}
    for name, pts in gr_arms.IDLE.items():
        f = fd if name == 'delt' else (fu if name in UPPER else fl)
        polys[name] = [f(p) for p in pts]
        forms[name] = _form(gr_arms.IDLE_FORMS[name], f)
    return polys, forms


def arm(shoulder, elbow, wrist, side, spec=None, delt_turn=0.5):
    """The re-posed arm, shaded (despeckled) for `side` (0 screen left, 1 its mirror)."""
    polys, forms = repose(shoulder, elbow, wrist, delt_turn)
    part = gf_fig.arm_layer(polys, forms, spec or gr_arms.SPEC, side)
    return K.despeckle(part)


def _check():
    """Re-posing to the idle joints must give back the approved idle arm exactly."""
    for side in (0, 1):
        a = K.despeckle(gr_arms.arm('idle', side))
        b = arm(S0, E0, W0, side)
        if a != b:
            raise SystemExit('gf_limb.repose no longer reproduces the approved idle arm')


_check()
