"""Greyson's brawl, the FINISHING half (PLAN_BRAWL.md section 7): dazed, uppercut, recover, KO,
toss, and the barbell prop. The shared base.

Builds on the brawl approval pass's rig (art_source/greyson_brawl, gb_*), which builds on the
pose rig (greyson_poses, gp_*), the fight rig (greyson_fight, gf_*) and the design of record
(greyson_redesign, gr_*). All of them are imported READ-ONLY; nothing here edits them. On import
this proves the brawl rig still draws the three frames the user APPROVED (the guard, the cannon
hook and the dazed slump, saved in greyson_brawl/approved/) pixel for pixel, and refuses to run if
not, so a change in the other artist's live rig can never slip into these sheets unnoticed.

Every module here is named gz_*, so none can shadow (or be shadowed by) any other rig's modules.
Coordinates: 112x112 cells, feet on row 111, column 56 the axis, light from the upper left. He
faces the player and is NEVER flipped: his right fist on screen left, the gauntlet on screen right.
Nothing in this module writes files.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
BRAWL = os.path.join(ART, 'greyson_brawl')
if BRAWL not in sys.path:
    sys.path.insert(0, BRAWL)

import gb_base as GB    # noqa: E402  (proves the pose, fight and design rigs on import)
import gb_body as BD    # noqa: E402
import gb_fig as F      # noqa: E402
import gb_arms as A     # noqa: E402
import gb_faces         # noqa: E402
import gb_sheets as GS  # noqa: E402  (its guard_cannon: the approved guard's left arm)

while HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)

for _m in (GB, BD, F, A, gb_faces, GS):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(BRAWL):
        raise ImportError('%s came from %s, not the brawl rig %s' % (_m.__name__, _m.__file__, BRAWL))

K, G, P = GB.K, GB.G, GB.P
gr_arms, gr_hands, gr_face, gr_fig = G.gr_arms, G.gr_hands, G.gr_face, G.gr_fig
gf_arms, gf_cannon = G.gf_arms, G.gf_cannon
import gf_barbell       # noqa: E402  (the fight rig's barbell: already on the path via gp_base)
import gf_faces         # noqa: E402
import gp_faces         # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image   # noqa: E402

W = H = 112
FEET = (56, 111)
APPROVED_DIR = os.path.join(BRAWL, 'approved')
APPROVED = {
    'greyson_brawl_guard_f0': (F.guard, {}),
    'greyson_brawl_hook_l_strike': (F.hook_l_strike, {}),
    'greyson_brawl_dazed_f0': (F.dazed, {}),
}
SCRATCH = os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\greyson_brawl_art\finish')


def approved_png(name):
    return Image.open(os.path.join(APPROVED_DIR, name + '.png')).convert('RGBA')


def check_brawl_rig():
    for name, (fn, kw) in APPROVED.items():
        cv, _ = fn(**kw)
        d = pixel_diff(cv.image(), approved_png(name))
        if d:
            raise SystemExit('the brawl rig no longer draws the approved %s: %s' % (name, d))


check_brawl_rig()

moved, mp, rnd = BD.moved, P.mp, F.rnd
Canvas = K.Canvas


def image(px):
    return G.image(px)


def audit(px, fx=()):
    return G.audit(px, fx)
