"""Jordan's Peach tee, as the rig draws it now: the interface this folder's first approval pass left
behind, kept for the modules that read it.

History (the user, 2026-09-28):
  - "less baggy and more fitted to his skinny frame": the FITTED tee (this folder's pass: a 19px close
    column, short sleeves), approved "everywhere" and folded into the v2 rig the same day;
  - "i want jordan even skinnier and his shirt even more fitted": the SKINNY build (skinny/: a 15px
    chest tapering to a 13px waist, the Peach print's two side outline columns cropped, arms and jeans
    about a pixel thinner, tighter and shorter sleeves), approved as "approve the skinnier one" and
    folded into art_source/jordan_v2/jv2_body.py the same day.
The fitted and sack versions of this module are in git history.

Everything here is now the rig's OWN part or number, re-exported: nothing is patched. apply() and
restore() change nothing and fitted() is an empty context, kept so their callers still run:
  - the standing finale's base (jordan_finale_standing/jfs_base.py) calls apply() and builds its
    sleeves with near_sleeve / far_sleeve and the shoulder numbers below;
  - the seated finale's check_fit_matches() (jordan_finale_chars/jfc_front.py) compares its own copy
    of the tee's numbers with NEAR_X, FAR_X, HEM_Y, torso_outline(), the sleeve roots, collar ends and
    shoulder lines, and DANDRUFF.

Coordinates are the rig's BUILD coordinates, as in jv2_body (a frame is x - 1).
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
V2_DIR = os.path.join(ART, 'jordan_v2')
if V2_DIR not in sys.path:
    sys.path.append(V2_DIR)

import jv2_base as B  # noqa: E402  (read-only)
import jv2_body as V  # noqa: E402  (read-only)

if os.path.normcase(os.path.dirname(os.path.abspath(V.__file__))) != os.path.normcase(os.path.abspath(V2_DIR)):
    raise ImportError('jv2_body came from %s, not %s' % (V.__file__, V2_DIR))

T = B.rig_torso                          # the approved rig: the Peach print (its map untouched)
PRINT_AT, BAND_Y = V.PRINT_AT, V.BAND_Y
PRINT_X0, PRINT_X1 = V.PRINT_X0, V.PRINT_X1
PRINT_Y0, PRINT_Y1 = PRINT_AT[1], PRINT_AT[1] + 14


#THE TEE'S BODY (the rig's)

NEAR_X, FAR_X = V.NEAR_X, V.FAR_X                     # the chest's side seams: 41.6, 56.4
WAIST_NEAR, WAIST_FAR = V.WAIST_NEAR, V.WAIST_FAR     # the waist's, under the print: 42.6, 55.4
HEM_Y = V.HEM_Y                                       # 69.3


def torso_outline(frame=0):
    """The rig's tee outline (jv2_body.torso_outline), standing: the hem on HEM_Y."""
    return V.torso_outline(HEM_Y)


shirt = V.shirt


#SLEEVES (the rig's)

sleeve_outline = V.sleeve_outline
sleeve = V.sleeve
NEAR_ROOT, NEAR_COLLAR = V.NEAR_ROOT, V.NEAR_COLLAR
FAR_ROOT, FAR_COLLAR = V.FAR_ROOT, V.FAR_COLLAR
NEAR_SHOULDER, FAR_SHOULDER = V.NEAR_SHOULDER, V.FAR_SHOULDER


def near_sleeve(root=NEAR_ROOT, elbow=(32.4, 57.2), collar=NEAR_COLLAR, shoulder=NEAR_SHOULDER, **kw):
    """The rig's short sleeve on any near upper arm, the collar end and shoulder line given."""
    pts, hem = V.sleeve_outline(root, elbow, collar, shoulder, +1, **kw)
    return V.sleeve(pts, hem)


def far_sleeve(root=FAR_ROOT, elbow=(62.8, 56.6), collar=FAR_COLLAR, shoulder=FAR_SHOULDER, **kw):
    """The rig's short sleeve on any far upper arm, behind the tee, in shade."""
    kw.setdefault('length', 4.6)
    pts, hem = V.sleeve_outline(root, elbow, collar, shoulder, -1, **kw)
    return V.sleeve(pts, hem, lit=False)


near_arm_hip = V.near_arm_hip
far_arm_box = V.far_arm_box
far_arm_box_low = V.far_arm_box_low
raised_sleeve = V.raised_sleeve
raised_arm = V.raised_arm
DANDRUFF = dict(V.DANDRUFF)


#NO PATCHING ANY MORE

def apply():
    """Nothing to do: the rig draws this tee itself."""


def restore():
    """Nothing to do."""


class fitted:
    """An empty context, kept for the fitted pass's scripts (jfit_frames.py)."""
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
