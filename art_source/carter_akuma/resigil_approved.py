"""Restamp the new emblem onto frame 2 of the APPROVED sheet.

The user signed off on changing the back view's mark, and nothing else in
carter_akuma.png.  So rather than regenerating the whole sheet, this rebuilds
frame 2 only, splices it in, and refuses to write unless frames 0 and 1 come
back byte-identical to what was already shipped.

    python resigil_approved.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from lib import W, H, Canvas
from pngio import read_png, write_png, crop, paste
import aura as AU
import poses as PO

OUT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))
SHEET = os.path.join(OUT, 'carter_akuma.png')


def frame2():
    """identical to build.py's frame2 - only poses.sigil() has changed"""
    cv = Canvas()
    bm = PO.back_body_mask()
    AU.paint(cv, AU.IDLE, AU.IDLE_SPARKS, bm)
    AU.haze(cv, bm, 5, 0, 1)
    PO.draw_back(cv)
    return cv


if __name__ == '__main__':
    w, h, old = read_png(SHEET)
    assert (w, h) == (W * 3, H), (w, h)
    new = [row[:] for row in old]
    paste_src = frame2().rgba()
    for y in range(H):
        for x in range(W):
            new[y][2 * W + x] = paste_src[y][x]

    for f in (0, 1):
        a = crop(old, f * W, 0, W, H)
        b = crop(new, f * W, 0, W, H)
        same = all(a[y][x] == b[y][x] for y in range(H) for x in range(W))
        print('frame %d untouched: %s' % (f, same))
        assert same, 'frame %d changed - refusing to write' % f

    changed = sum(1 for y in range(H) for x in range(W)
                  if old[y][2 * W + x] != new[y][2 * W + x])
    write_png(SHEET, w, h, new)
    print('frame 2 restamped with the new emblem (%d pixels changed)' % changed)
    print('wrote', SHEET)
