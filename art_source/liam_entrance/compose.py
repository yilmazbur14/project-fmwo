"""Assemble the throne procession from its sprites (the same layering the scene should use).
All offsets are relative to the palanquin frame's top-left."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
import throne
import liam_seated
import carriers
from liamkit import BIX_PNG

# carrier frame top-left offsets (palanquin coords); carriers grip rows 11-14 of their frame
REAR_Y = throne.REAR_POLE[0] - 11
FRONT_Y = throne.FRONT_POLE[0] - 11
CARRIER_POS = {
    'c3': (-4, REAR_Y),     # rear-left, lanky (pole end in his right fist)
    'c4': (168, REAR_Y),    # rear-right, round beanie
    'c1': (30, FRONT_Y),    # front-left, hoodie + headset
    'c2': (118, FRONT_Y),   # front-right, cat-ear hoodie
}
LIAM_POS = (throne.SEAT[0] - liam_seated.ANCHOR[0], throne.SEAT[1] - liam_seated.ANCHOR[1])
BIXBY_POS = (throne.BIXBY[0] - 32, throne.BIXBY[1] - 63)


def procession(cv, ox, oy, with_liam=True, with_bixby=True, carrier_frames=None, bob=0):
    """carrier_frames: dict name -> Canvas (defaults to the straining poses). bob: palanquin rise in px (walk)."""
    f0, f1 = throne.build()
    cs = carrier_frames or dict(zip(['c1', 'c2', 'c3', 'c4'], carriers.build_all()))
    py = oy - bob
    cv.blit(f1, ox, py)
    for name in ('c3', 'c4'):
        x, y = CARRIER_POS[name]
        cv.blit(cs[name], ox + x, oy + y)
    cv.blit(f0, ox, py)
    if with_bixby:
        cv.blit(from_png(BIX_PNG), ox + BIXBY_POS[0], py + BIXBY_POS[1])
    if with_liam:
        cv.blit(liam_seated.build(), ox + LIAM_POS[0], py + LIAM_POS[1])
    for name in ('c1', 'c2'):
        x, y = CARRIER_POS[name]
        cv.blit(cs[name], ox + x, oy + y)
    return cv


if __name__ == '__main__':
    import view
    cv = Canvas(230, 150)
    procession(cv, 20, 4)
    print(view.zoom(cv, 4, 'procession_4x.png', bg=view.FLOOR))
