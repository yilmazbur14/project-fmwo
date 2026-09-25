"""Matt's Glass Row / Deafening Yell art: shared base.

Matt's frames build on the intro and fight rigs (art_source/matt_intro mi_*, art_source/matt_fight
mf_*), which build on the approved rig (art_source/matt), all imported READ-ONLY with bytecode off.
The player's poses (mg_player.py) are hand-drawn grids in the player's own seven colours.
Modules here are named mg_* so none can shadow another rig's modules.

Nothing here writes into Assets/. mg_export.py writes only with an explicit folder or --ship.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
INTRO = os.path.join(ART, 'matt_intro')
FIGHT = os.path.join(ART, 'matt_fight')
for _p in (FIGHT, INTRO):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, HERE)

import mi_base as B      # noqa: E402,F401
import mi_arms as A      # noqa: E402,F401
import mi_faces as G     # noqa: E402,F401
import mi_fig as F       # noqa: E402,F401
import mi_hands as H     # noqa: E402,F401
import mi_legs as L      # noqa: E402,F401
import mi_poses as PZ    # noqa: E402,F401
import mf_faces as FF    # noqa: E402,F401

for _m, _d in ((B, INTRO), (A, INTRO), (G, INTRO), (F, INTRO), (H, INTRO), (L, INTRO), (PZ, INTRO),
               (FF, FIGHT)):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(_d):
        raise ImportError('%s came from %s, not %s' % (_m.__name__, _m.__file__, _d))

SCRATCH = os.path.join(os.path.dirname(B.SCRATCH), 'matt_glass_art')
PLAYER_DIR = os.path.join(B.ROOT, 'Assets', 'Characters', 'MainPlayer')


def part(rows, x, y):
    return B.amap(rows, x, y)
