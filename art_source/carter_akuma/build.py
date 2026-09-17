"""Build Carter's Satsui no Hado sheet and write it into Assets/Characters/Carter.

    python build.py            # regenerate the PNGs
Frames: 0 = idle, 1 = arms-crossed signature pose, 2 = back view.
96x96, hframes=3, feet plane on row 95 (the bottom edge of the frame).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from lib import W, H, Canvas
from pngio import write_png, blank, paste
import render as R, parts as P, aura as AU, poses as PO

OUT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))


def frame0():
    cv = Canvas(); bm = P.body_mask()
    AU.paint(cv, AU.IDLE, AU.IDLE_SPARKS, bm)
    AU.haze(cv, bm, 5, 0, 0)
    R.body(cv); return cv


def frame1():
    cv = Canvas(); bm = PO.x_body_mask()
    AU.paint(cv, AU.FLARE, AU.FLARE_SPARKS, bm)
    AU.haze(cv, bm, 9, 4, 2)
    PO.draw_cross(cv); return cv


def frame2():
    cv = Canvas(); bm = PO.back_body_mask()
    AU.paint(cv, AU.IDLE, AU.IDLE_SPARKS, bm)
    AU.haze(cv, bm, 5, 0, 1)
    PO.draw_back(cv); return cv


if __name__ == '__main__':
    fs = [frame0(), frame1(), frame2()]
    sheet = blank(W * 3, H)
    for i, cv in enumerate(fs):
        paste(sheet, cv.rgba(), i * W, 0)
    write_png(os.path.join(OUT, 'carter_akuma.png'), W * 3, H, sheet)
    write_png(os.path.join(OUT, 'carter_akuma_pose.png'), W, H, fs[1].rgba())
    print('wrote carter_akuma.png (288x96) and carter_akuma_pose.png (96x96) to', OUT)
