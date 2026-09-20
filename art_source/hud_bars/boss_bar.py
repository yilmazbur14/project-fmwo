"""Boss health bar art. Native px; export_all writes the _3x companions.

Frame geometry from the build plan: 160x18 frame, fill window at (4,4) 152x12,
seven interior notches at x = 4+19k. The frame splits into a BACK plate (brass
chrome + recessed well, under the fills) and an OVER plate (rim, top highlight,
studs and notches, with the window transparent so the notches read on top of the
fill). The low variant is the same OVER plate in hot tones.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from barlib import *

FW, FH = FRAME_W, FRAME_H
WX, WY, WW, WH = WIN_X, WIN_Y, WIN_W, WIN_H


def frame_back():
    im = canvas(FW, FH)
    brass_box(im, 0, 0, FW - 1, FH - 1)
    well_box(im, WX - 1, WY - 1, WX + WW, WY + WH)
    stud(im, 1, 1)
    stud(im, FW - 5, 1)
    stud(im, 1, FH - 5)
    stud(im, FW - 5, FH - 5)
    return im


def _frame_over(hot=False):
    """Rim + studs + notches only. The window stays transparent."""
    hi, lt, bo, dk = (HOT_HI, HOT_LT, HOT, HOT_DK) if hot else (BRASS_HI, BRASS_LT, BRASS, BRASS_DK)
    im = canvas(FW, FH)
    rect(im, 0, 0, FW - 1, 0, KEY)
    rect(im, 0, FH - 1, FW - 1, FH - 1, KEY)
    rect(im, 0, 0, 0, FH - 1, KEY)
    rect(im, FW - 1, 0, FW - 1, FH - 1, KEY)
    hline(im, 1, FW - 2, 1, hi)
    hline(im, 1, FW - 2, 2, lt)
    hline(im, 1, FW - 2, FH - 2, dk)
    rect(im, 1, 3, WX - 1, FH - 3, bo)
    rect(im, WX + WW, 3, FW - 2, FH - 3, bo)
    vline(im, WX - 1, WY - 1, WY + WH, KEY)
    vline(im, WX + WW, WY - 1, WY + WH, KEY)
    hline(im, WX - 1, WX + WW, WY - 1, KEY)
    hline(im, WX - 1, WX + WW, WY + WH, KEY)
    stud(im, 1, 1)
    stud(im, FW - 5, 1)
    stud(im, 1, FH - 5)
    stud(im, FW - 5, FH - 5)
    for x in NOTCH_XS:                       # seven interior ticks over the fill
        vline(im, x, WY, WY + WH - 1, KEY, 150)
        vline(im, x + 1, WY, WY + WH - 1, hi, 70)
    return im


def frame_over():
    return _frame_over(False)


def frame_over_low():
    im = _frame_over(True)
    hline(im, WX, WX + WW - 1, WY, HOT, 110)          # hot lip inside the well
    return im


def bar_ramp(ramp, mark=None):
    """Push a card ramp toward something that reads as a FILL.

    Two problems to solve at once. The ramps in bosses.py were authored as
    background blocks behind a bust, so some are deliberately desaturated -
    Eric's is pale steel-white, which as a bar fill reads as an EMPTY bar, the
    one thing a health fill must never do. But a blanket saturation slam is
    worse: it collapsed Eric, Josh, Jordan and Computah into four identical
    blues, because boosting a near-grey hue invents a colour the boss does not
    own.

    So: a gentle boost that preserves hue, and for a ramp that is genuinely
    neutral, take the hue from the boss's MARK colour instead. Eric's mark is
    his red cross, so his bar goes red - which is both readable and his."""
    import colorsys
    cols = [_rgb(c) for c in ramp]
    # Neutrality has to be measured as CHROMA, not HLS saturation: HLS reports
    # #EAF0F6 as 0.40 saturated because it is near white, so a saturation test
    # said Eric's steel ramp was colourful and left his bar blue.
    chroma = [(max(c) - min(c)) / 255.0 for c in cols]
    neutral = sum(chroma) / len(chroma) < 0.12
    hue = None
    if neutral and mark:
        mr, mg, mb = _rgb(mark)
        hue = colorsys.rgb_to_hls(mr / 255.0, mg / 255.0, mb / 255.0)[0]
    out = []
    n = len(ramp) - 1.0
    for i, (r, g, b) in enumerate(cols):
        h, l, sat = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        if hue is not None:
            h, sat = hue, 0.62
        else:
            sat = min(0.95, sat * 1.55 + 0.08)
        l = 0.18 + (i / n) * 0.62
        rr, gg, bb = colorsys.hls_to_rgb(h, l, sat)
        out.append("#%02X%02X%02X" % (int(rr * 255), int(gg * 255), int(bb * 255)))
    return out


def _rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def fill(ramp, mark=None):
    return ramp_fill(WW, WH, bar_ramp(ramp, mark))


def fill_hot(ramp, accent_hi, mark=None):
    im = ramp_fill(WW, WH, bar_ramp(ramp, mark))
    tint(im, accent_hi, 0.55)
    hline(im, 0, WW - 1, 1, accent_hi)
    return im


def chip():
    """Pale bone damage trail - has to read over every boss ramp."""
    im = canvas(WW, WH)
    rect(im, 0, 0, WW - 1, WH - 1, BONE_DK)
    rect(im, 0, 0, WW - 1, 1, BONE)
    rect(im, 0, WH - 2, WW - 1, WH - 1, "#9A8F80")
    for x in range(0, WW, 6):
        vline(im, x, 2, WH - 3, BONE, 90)
    return im


def low_pulse():
    """Two frames, a slow breath at <=25% - a rim treatment, not a strobe."""
    out = []
    for a in (70, 130):
        im = canvas(WW, WH)
        rect(im, 0, 0, WW - 1, WH - 1, HOT, a // 2)
        hline(im, 0, WW - 1, 0, HOT_LT, a)
        hline(im, 0, WW - 1, WH - 1, HOT_DK, a)
        out.append(im)
    return out


def flash():
    im = canvas(WW, WH)
    rect(im, 0, 0, WW - 1, WH - 1, "#FFFFFF")
    return im


def flash_punish():
    """Gold and cyan, matching the popup_parry / popup_perfect family."""
    im = canvas(WW, WH)
    rect(im, 0, 0, WW - 1, WH - 1, BRASS_HI)
    rect(im, 0, 0, WW - 1, 1, "#FFFFFF")
    rect(im, 0, WH - 3, WW - 1, WH - 1, CYAN)
    for x in range(0, WW, 8):
        vline(im, x, 0, WH - 1, CYAN_LT, 160)
    return im


def spark():
    """Three-frame burst at the fill's leading edge, punish hits only."""
    import math
    from PIL import ImageDraw as _D
    out = []
    cx, cy = SPARK_W // 2, SPARK_H // 2
    for i, (r, arms, col, core) in enumerate(((5, 4, "#FFFFFF", 3), (8, 8, BRASS_HI, 2), (10, 8, CYAN, 1))):
        im = canvas(SPARK_W, SPARK_H)
        d = _D.Draw(im)
        for k in range(arms):
            a = k * (math.pi * 2 / arms) + (0.4 if i else 0.0)
            d.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)],
                   fill=rgba(col, 255 - i * 60), width=2)
        rect(im, cx - core, cy - core, cx + core - 1, cy + core - 1, "#FFFFFF", 255 - i * 70)
        out.append(im)
    return out


def sweep():
    """Three-frame bright band for the phase-2 refill."""
    out = []
    for i, x0 in enumerate((-20, WW // 3, WW - 20)):
        im = canvas(WW, WH)
        for d in range(24):
            x = x0 + d
            if 0 <= x < WW:
                a = int(200 * (1 - abs(d - 12) / 12.0))
                vline(im, x, 0, WH - 1, "#FFFFFF", max(a, 0))
        out.append(im)
    return out


def ghost():
    """Greyson's opposite-body marker notch."""
    im = canvas(GHOST_W, WIN_H)
    rect(im, 0, 0, GHOST_W - 1, WIN_H - 1, KEY)
    vline(im, 1, 0, WIN_H - 1, "#FFFFFF")
    return im
