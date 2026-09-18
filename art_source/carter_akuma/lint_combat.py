"""Checks on Carter's combat sheets.  Run after build_combat.py.

    python lint_combat.py

Verifies, per frame:
  * every opaque pixel is an exact colour from lib.PAL (no accidental blends -
    mixc snaps, so anything off-palette means a bug, not a gradient)
  * alpha is strictly 0 or 255
  * nothing touches the left/right/top edge of its own frame cell, so flipping
    and scaling cannot clip him
  * the lowest opaque row per frame, so the feet anchor can be read off
  * frame 0 of the idle is byte-identical to frame 0 of the approved sheet
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from lib import PALC, GI_STEPS, RAMPS, hexc
from pngio import read_png, crop

A = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))
W = H = 96
# gi_fade blends navy toward violet in four quantised steps; those colours are
# not in PAL but they are all over the approved sheet, so they are legal here.
PAL_SET = set(PALC.values()) | set(c for step in GI_STEPS for c in step)
# aura and speed lines are allowed to run off the edge of the cell; skin, cloth
# and rope are not, because a clipped limb is visible and a clipped wisp is not.
BODY_SET = set(hexc(c) for r in ('skin', 'skinr', 'hair', 'gi', 'rope', 'belt',
                                 'bead', 'steel') for c in RAMPS[r])
BODY_SET |= set(c for step in GI_STEPS for c in step)

SHEETS = ['carter_idle.png', 'carter_eye_flash.png', 'carter_rush.png',
          'carter_rush_pass.png', 'carter_spent.png', 'carter_hit.png',
          'carter_defeat.png', 'carter_victory.png']


def check(name):
    w, h, px = read_png(os.path.join(A, name))
    assert h == H, (name, h)
    n = w // W
    assert w == n * W, (name, w)
    bad_pal, bad_a, edge = 0, 0, []
    rows = []
    for i in range(n):
        f = crop(px, i * W, 0, W, H)
        lo, hi, top, bot = W, -1, H, -1
        for y in range(H):
            for x in range(W):
                p = f[y][x]
                if p[3] == 0:
                    continue
                if p[3] != 255:
                    bad_a += 1
                if tuple(p) not in PAL_SET:
                    bad_pal += 1
                lo, hi = min(lo, x), max(hi, x)
                top, bot = min(top, y), max(bot, y)
        clipped = [(x, y) for y in range(H) for x in (0, W - 1)
                   if f[y][x][3] and tuple(f[y][x]) in BODY_SET]
        clipped += [(x, 0) for x in range(W)
                    if f[0][x][3] and tuple(f[0][x]) in BODY_SET]
        if clipped:
            edge.append((i, lo, hi, top))
        rows.append((i, lo, hi, top, bot))
    print('%-24s %d frames' % (name, n))
    for i, lo, hi, top, bot in rows:
        print('   f%d  x %2d..%-2d  y %2d..%-2d  bottom row %d' %
              (i, lo, hi, top, bot, bot))
    if bad_pal:
        print('   !! %d off-palette pixels' % bad_pal)
    if bad_a:
        print('   !! %d partial-alpha pixels' % bad_a)
    for i, lo, hi, top in edge:
        print('   !! f%d has BODY pixels on a frame edge (x %d..%d, top %d)' %
              (i, lo, hi, top))
    return bad_pal + bad_a + len(edge)


def check_handover():
    _, _, appr = read_png(os.path.join(A, 'carter_akuma.png'))
    _, _, idle = read_png(os.path.join(A, 'carter_idle.png'))
    a = crop(appr, 0, 0, W, H)
    b = crop(idle, 0, 0, W, H)
    diff = sum(1 for y in range(H) for x in range(W) if a[y][x] != b[y][x])
    print('idle f0 vs approved f0: %d differing pixels' % diff)
    return diff


if __name__ == '__main__':
    bad = 0
    for s in SHEETS:
        bad += check(s)
    bad += check_handover()
    print('FAILURES:', bad)
    sys.exit(1 if bad else 0)
