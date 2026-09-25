"""Matt's fight body set: shared base.

Builds on the intro rig (art_source/matt_intro, mi_*), which builds on the approved rig
(art_source/matt), both imported READ-ONLY with bytecode off. Modules here are named mf_* so none
can shadow the intro rig's mi_*, the approved rig's modules, or josh_redesign's lib.

Nothing here writes into Assets/. mf_export.py writes only with an explicit folder or --ship.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
INTRO = os.path.join(os.path.dirname(HERE), 'matt_intro')
if INTRO not in sys.path:
    sys.path.insert(0, INTRO)
sys.path.insert(0, HERE)

import mi_base as B      # noqa: E402,F401
import mi_arms as A      # noqa: E402,F401
import mi_faces as G     # noqa: E402,F401
import mi_fig as F       # noqa: E402,F401
import mi_hands as H     # noqa: E402,F401
import mi_legs as L      # noqa: E402,F401
import mi_poses as PZ    # noqa: E402,F401
import mi_hong as HG     # noqa: E402,F401

for _m in (B, A, G, F, H, L, PZ, HG):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(INTRO):
        raise ImportError('%s came from %s, not the intro rig' % (_m.__name__, _m.__file__))

SCRATCH = os.path.join(os.path.dirname(B.SCRATCH), 'matt_fight')


def part(rows, x, y):
    return B.amap(rows, x, y)
