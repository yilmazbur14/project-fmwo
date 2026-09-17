"""Liam pose kit: cut regions out of the approved liam.png (head, torso, arms, legs) so new poses reuse his exact
head/face/torso pixels and only the limbs are redrawn."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *

LIAM_PNG = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Liam/liam.png'
BIX_PNG = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/bixby.png'


def load_liam():
    return from_png(LIAM_PNG)


def flood(cv, seed, passable):
    """4-connected flood fill over pixels where passable(colour) is True"""
    out = set()
    stack = [seed]
    while stack:
        x, y = stack.pop()
        if (x, y) in out:
            continue
        c = cv.get(x, y)
        if c is None or not passable(c):
            continue
        out.add((x, y))
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return out


def not_black(c):
    return c != BLACK


def region(cv, seeds):
    m = set()
    for s in seeds:
        m |= flood(cv, s, not_black)
    return m


def cut(cv, fill):
    """erase a filled region and the outline pixels that only belonged to it (keeps outlines shared with the rest)"""
    rest = {(x, y) for y in range(cv.h) for x in range(cv.w) if cv.px[y][x] not in (None, BLACK)} - fill
    outl = set()
    for (x, y) in fill:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if cv.get(*q) == BLACK:
                    outl.add(q)
    for (x, y) in outl:
        shared = any((x + dx, y + dy) in rest for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if not shared:
            cv.put(x, y, None)
    for p in fill:
        cv.put(*p, None)


# seeds inside liam.png regions (verified with preview_regions)
SEED_LARM = [(8, 35), (7, 44), (6, 50)]           # screen-left sleeve, wristband, fist
SEED_RARM = [(52, 32), (54, 43), (48, 45)]        # screen-right sleeve, wristband, hand on hip
SEED_LEGS = [(20, 50), (40, 50), (10, 59), (44, 59)]   # pants legs + shoes


if __name__ == '__main__':
    import view
    cv = load_liam()
    show = cv.copy()
    for seeds, col in ((SEED_LARM, (255, 0, 255, 255)), (SEED_RARM, (0, 255, 255, 255)), (SEED_LEGS, (255, 255, 0, 255))):
        for p in region(cv, seeds):
            show.put(*p, col)
    print(view.zoom(show, 8, 'liam_regions_8x.png'))
