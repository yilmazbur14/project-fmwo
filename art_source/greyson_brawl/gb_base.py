"""Greyson's BRAWL set (the Punch-Out final phase): the shared base.

Builds on the approved design rig (art_source/greyson_redesign, gr_*) and the fight rig
(art_source/greyson_fight, gf_*), both READ-ONLY and both proven on import (via
art_source/greyson_poses/gp_base, which this folder's modules reuse along with gp_fig's joint
tools: the pose artist's own folder, also read-only from here).

Every module here is named gb_*. Coordinates: 112x112 cells, feet on row 111, column 56 the axis
(x' = 112 - x), light from the upper left. Nothing in this module writes files.

The staging (PLAN_BRAWL.md): a LIGHT CROUCH, crown 78 and chin 52 texels above the soles, fist and
gauntlet up at cheek height; never flipped (the gauntlet stays on screen right). The plan measures
the chin two rows under the jaw's keyline (the approved standing chin is 59 above the soles), and
so do the anchors here.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
POSES = os.path.join(ART, 'greyson_poses')
if POSES not in sys.path:
    sys.path.insert(0, POSES)

import gp_base as G   # noqa: E402  (proves both rigs on import)
import gp_fig as P    # noqa: E402

while HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)

for _m in (G, P):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(POSES):
        raise ImportError('%s came from %s, not %s' % (_m.__name__, _m.__file__, POSES))

K = G.K
W = H = 112
FEET = (56, 111)
SCRATCH = os.path.join(os.path.dirname(G.SCRATCH), 'greyson_brawl_art')
SHIP_DIR = G.SHIP_DIR

# PLAN_BRAWL.md section 4, in his cell's texels
TARGET = {
    'guard_crown': (56, 33), 'guard_chin': (56, 59),
    'guard_fist': (42, 61), 'guard_gauntlet': (70, 63),
    'hook_l': {'windup': (90, 59), 'strike': (56, 73), 'follow': (34, 69), 'whiff': (26, 67)},
    'hook_r': {'windup': (22, 59), 'strike': (56, 73), 'follow': (78, 69), 'whiff': (86, 67)},
    'straight': {'windup': (64, 67), 'strike': (55, 63), 'landed': (56, 71)},
    'dazed_crown': (56, 39), 'dazed_chin': (56, 65),
    'daze_anchor': (56, 28),
}
# the approved head: the mane's top keyline and the jaw's keyline rows at rest
CROWN_ROW, JAW_ROW = 26, 50
CHIN_BELOW_JAW = 2
