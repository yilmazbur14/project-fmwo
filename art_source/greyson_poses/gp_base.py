"""Greyson's POSE sheets (pose A / B / C, the spoiled pose, the spirit bomb): the shared base.

Builds on two rigs this folder does NOT own, imported READ-ONLY:
  art_source/greyson_redesign (gr_*)  the approved design of record (2026-09-24)
  art_source/greyson_fight   (gf_*)  the fight rig: the cannon gauntlet, the back views, the
                                      approved fight frames (greyson_fight_approval.png)
Nothing here edits either. On import it proves (1) the design rig still draws the approved
sprite (gf_base does that) and (2) the fight rig still draws the four approved fight frames this
job holds on (pose A, B, C and the spirit raise), pixel for pixel, and refuses to run if not, so a
change in someone else's rig can never slip into these sheets unnoticed.

Every module here is named gp_*, so none can shadow (or be shadowed by) a gr_* or gf_* module.
Coordinates are the rigs': 112x112 frames, feet on row 111, column 56 the axis (x' = 112 - x),
light from the upper left. Nothing in this module writes files.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
FIGHT = os.path.join(ART, 'greyson_fight')
if FIGHT not in sys.path:
    sys.path.insert(0, FIGHT)

import gf_base as B      # noqa: E402  (proves the approved design rig on import)
import gf_fig            # noqa: E402
import gf_arms           # noqa: E402
import gf_back           # noqa: E402
import gf_cannon         # noqa: E402
import gf_faces          # noqa: E402
import gf_hands          # noqa: E402

# gf_base reorders sys.path; keep this folder first (its names never clash: gp_*)
while HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)

for _m in (B, gf_fig, gf_arms, gf_back, gf_cannon, gf_faces, gf_hands):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(FIGHT):
        raise ImportError('%s came from %s, not the fight rig %s' % (_m.__name__, _m.__file__, FIGHT))

K = B.K
gr_arms, gr_hands, gr_face, gr_fig, gr_boots = B.gr_arms, B.gr_hands, B.gr_face, B.gr_fig, B.gr_boots
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

W = H = 112
AX = K.AX
FEET_ROW = 111
APPROVAL_PNG = os.path.join(B.ASSETS_GREYSON, 'greyson_fight_approval.png')
APPROVED = {'pose_a': 1, 'pose_b': 2, 'pose_c': 3, 'spirit': 4}   # frame index in the approval strip
SHIP_DIR = B.ASSETS_GREYSON
SCRATCH = os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\greyson_poses')


def approved_frame(name):
    i = APPROVED[name]
    return Image.open(APPROVAL_PNG).convert('RGBA').crop((112 * i, 0, 112 * i + 112, 112))


def check_fight_rig():
    """The fight rig must still draw the approved fight frames exactly."""
    for name in APPROVED:
        d = pixel_diff(gf_fig.build(name).image(), approved_frame(name))
        if d:
            raise SystemExit('the fight rig no longer draws the approved %s frame: %s' % (name, d))


check_fight_rig()


def image(px):
    return B.image(px)


def audit(px, fx=()):
    return B.audit(px, fx)
