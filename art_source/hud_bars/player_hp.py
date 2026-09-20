"""Player health containers: the tray and the three heart states, plus their FX.

The tray is exactly as wide as stamina_bar_frame (88 native) and carries the same
brass-and-navy chrome, so the heart row, the stamina bar and the break gauge read
as one left column rather than three unrelated widgets.

Hearts are 18x16 native on the 3x grid - the 32x32 placeholders were the only HUD
element off it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from barlib import *

HW, HH = HEART_W, HEART_H
RED_HI, RED_LT, RED, RED_DK, RED_BK = "#FF7A8A", "#D95763", "#AC3232", "#6E1F22", "#3C0C20"


def tray(warn=0):
    """warn 0 = normal, 1/2 = the two red rim pulse frames."""
    im = canvas(TRAY_W, TRAY_H)
    brass_box(im, 0, 0, TRAY_W - 1, TRAY_H - 1)
    well_box(im, 3, 3, TRAY_W - 4, TRAY_H - 4)
    for x in HEART_SLOTS:                       # a seated recess per container
        rect(im, x - 2, 4, x + HW + 1, TRAY_H - 5, KEY, 90)
    stud(im, 1, 1)
    stud(im, TRAY_W - 5, 1)
    stud(im, 1, TRAY_H - 5)
    stud(im, TRAY_W - 5, TRAY_H - 5)
    if warn:
        a = 120 if warn == 1 else 210
        for x0, y0, x1, y1 in ((0, 0, TRAY_W - 1, 0), (0, TRAY_H - 1, TRAY_W - 1, TRAY_H - 1),
                               (0, 0, 0, TRAY_H - 1), (TRAY_W - 1, 0, TRAY_W - 1, TRAY_H - 1)):
            rect(im, x0, y0, x1, y1, RED_LT, a)
        hline(im, 1, TRAY_W - 2, 1, RED, a - 40)
    return im


def _heart_shape():
    """The classic two-lobe heart, as a list of (x0,x1) spans per row."""
    return [(4, 13), (2, 15), (1, 16), (1, 16), (1, 16), (1, 16), (2, 15), (2, 15),
            (3, 14), (4, 13), (5, 12), (6, 11), (7, 10), (8, 9)]


def _heart_base(fill_to=1.0, empty=False):
    im = canvas(HW, HH)
    spans = _heart_shape()
    top = 1
    # keyline first, then the body inside it
    for i, (a, b) in enumerate(spans):
        y = top + i
        rect(im, a - 1, y, b + 1, y, KEY)
    for i, (a, b) in enumerate(spans):
        y = top + i
        if empty:
            rect(im, a, y, b, y, WELL)
            continue
        cut = a + (b - a + 1) * fill_to
        if a <= cut - 1:
            rect(im, a, y, int(cut) - 1, y, RED)
        if cut <= b:
            rect(im, int(cut), y, b, y, WELL)
    if not empty:
        # top-lit lobes, dark underside, one glint - same language as the plates
        for i, (a, b) in enumerate(spans[:4]):
            y = top + i
            if a + (b - a + 1) * fill_to > a:
                rect(im, a, y, min(b, int(a + (b - a + 1) * fill_to) - 1), y, RED_LT)
        for i, (a, b) in enumerate(spans[-4:]):
            y = top + len(spans) - 4 + i
            if a + (b - a + 1) * fill_to > a:
                rect(im, a, y, min(b, int(a + (b - a + 1) * fill_to) - 1), y, RED_DK)
        if fill_to > 0.35:
            rect(im, 4, 3, 5, 4, RED_HI)
            rect(im, 4, 2, 4, 2, "#FFFFFF")
    else:
        hline(im, 2, 15, top + 1, "#1A1828")
        hline(im, 3, 14, top + len(spans) - 2, WELL_RIM)
    return im


def heart_full():
    return _heart_base(1.0)


def heart_half():
    im = _heart_base(0.5)
    vline(im, 8, 1, HH - 2, KEY, 170)
    return im


def heart_empty():
    return _heart_base(empty=True)


def heart_break():
    """Four frames, oversized so the shatter spills past the container."""
    out = []
    ox, oy = (BREAK_W - HW) // 2, (BREAK_H - HH) // 2
    for f in range(4):
        im = canvas(BREAK_W, BREAK_H)
        if f == 0:
            im.alpha_composite(_heart_base(1.0), (ox, oy))
            rect(im, ox + 8, oy, ox + 9, oy + HH - 1, "#FFFFFF")
        else:
            k = f
            for i, (dx, dy) in enumerate(((-5, -3), (5, -4), (-6, 3), (6, 4), (0, -6), (-2, 6))):
                sx = ox + 8 + dx * k
                sy = oy + 7 + dy * k
                s = max(1, 4 - k)
                col = RED_LT if i % 2 == 0 else RED
                rect(im, sx - s, sy - s, sx + s, sy + s, KEY)
                rect(im, sx - s + 1, sy - s + 1, sx + s - 1, sy + s - 1, col, 255 - (k - 1) * 70)
        out.append(im)
    return out


def heart_gain():
    """Three-frame restore pop."""
    out = []
    for f, (grow, a) in enumerate(((3, 140), (1, 220), (0, 255))):
        im = canvas(HW, HH)
        im.alpha_composite(_heart_base(1.0), (0, 0))
        if grow:
            for r in range(grow):
                rect(im, 1 - r, 1 - r, HW - 2 + r, HH - 2 + r, "#FFFFFF", max(0, a - r * 60))
            im.alpha_composite(_heart_base(1.0), (0, 0))
        out.append(im)
    return out


def _heart_beat(fill_to):
    """The lit frame of the beat at this fill: the top of whatever is filled, brightened.

    The wash stops at the fill line, so a half heart beats as a half. At 0.5 that line
    is x 8, which is exactly where heart_half puts its split."""
    im = _heart_base(fill_to)
    for i, (a, b) in enumerate(_heart_shape()[:5]):
        cut = int(a + (b - a + 1) * fill_to)
        if cut > a:
            rect(im, a, 1 + i, min(b, cut - 1), 1 + i, RED_HI)
    rect(im, 4, 3, 6, 5, "#FFFFFF")
    return im


def heart_low():
    """Heartbeat on the last container: a rest frame and a lit one per state, whole then half.

    Four frames rather than two because the beat is drawn over the container, so a whole
    heart's beat on a container down to its last half would paint a full one over it - the
    player one hit from death would read a full container."""
    half = _heart_base(0.5)
    vline(half, 8, 1, HH - 2, KEY, 170)
    half_lit = _heart_beat(0.5)
    vline(half_lit, 8, 1, HH - 2, KEY, 170)
    return [_heart_base(1.0), _heart_beat(1.0), half, half_lit]
