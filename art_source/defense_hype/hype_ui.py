"""Crowd HYPE meter (brass kit), bottom-right of the HUD. All textures share one 123x42 canvas origin.
  hype_meter_frame : 123x42 fixed-size frame: megaphone medallion + brass tube (same tube profile as the
                     stamina bar). Transparent headroom above the tube holds the HYPE label and FULL flames.
  hype_meter_fill  : 88x5 heat gradient blurple -> purple -> magenta -> orange -> gold, revealed left to right,
                     drawn at (28, 26) in the frame
  hype_meter_full  : 4 frames of 123x42, whole-meter overlay while full (drawn over frame + fill)
  hype_label       : 2 frames of 52x20 "HYPE" (0 normal, 1 lit), drawn at (26, 6), on top of everything
"""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *
import lettering as LT

W_, H_ = 123, 42
BAR_TOP = 21                       # tube outline row
BAR_X0 = 14                        # tube starts under the medallion
X_RING = W_ - 7                    # 116
TUBE_Y = BAR_TOP + 5               # 26
FILL_X, FILL_Y, FILL_W, FILL_H = 28, TUBE_Y, 88, 5
MED_CX, MED_CY, MED_R = 14.0, 28.0, 13.6
LABEL_XY = (26, 6)
LABEL_W, LABEL_H = 52, 20

PLATE = ["KKKKKK", "KYYYSK", "KYWYDK", "KYRpDK", "KSDDoK", "KKKKKK"]

# white megaphone with a magenta band, gold bell rim and a dark mouth, pointing at the bar
MEGAPHONE = [
    "..........KKKK..",
    "........KKWYYYK.",
    "......KKWmKKKTYK",
    "....KKWWmKpppKTK",
    "..KKWWPPmKpppKTK",
    "KKWWPPPPVKpppKTK",
    "KSKPPPPsVKpppKDK",
    "KTKsPPssVKpppKDK",
    "KKKKssssVKpppKDK",
    "..KDKKssVKKpKDK.",
    "..KDK.KKKKDDDK..",
    "..KKK....KKKK...",
]
MEGA_XY = (6, 22)                  # top-left of the megaphone grid in the canvas


def medallion(c, P, lit=False):
    cx, cy, R = MED_CX, MED_CY, MED_R
    for y in range(H_):
        for x in range(W_):
            d = math.hypot(x - cx, y - cy)
            if d > R:
                continue
            ang = math.degrees(math.atan2(y - cy, x - cx))
            li = math.cos(math.radians(ang + 135))               # +1 toward the top-left
            if d > R - 1.0:
                col = 'K'
            elif d > R - 2.0:
                col = 'Y' if li > 0.3 else ('T' if li > -0.45 else 'D')
            elif d > R - 3.0:
                col = 'S' if li > 0.6 else ('T' if li > -0.15 else ('D' if li > -0.75 else 'o'))
            elif d > R - 4.0:
                col = 'K'
            else:
                col = 'n'
                if d > R - 5.0 and li < -0.35:
                    col = 'I'                                    # reflected light on the lower-right rim
            c.p[y][x] = P[col]


def frame_canvas(pal_over=None, mega_over=None):
    P = dict(C)
    if pal_over:
        P.update(pal_over)
    c = Canvas(W_, H_)
    mid = ['K', 'Y', 'T', 'D', 'K', 'n', 'n', 'n', 'n', 'I', 'K', 'T', 'D', 'o', 'K']
    for x in range(BAR_X0, W_):
        for j, ch in enumerate(mid):
            c.p[BAR_TOP + j][x] = P[ch]
    for j in range(5, 10):
        c.p[BAR_TOP + j][X_RING - 1] = P['I']
    for j in range(15):
        c.p[BAR_TOP + j][X_RING] = P['K'] if 4 <= j <= 10 else P[mid[j]]
    for j in range(6, 9):
        for i, ch in enumerate('STTDoK'):
            c.p[BAR_TOP + j][X_RING + 1 + i] = P[ch]
    for (x0, y0) in [(W_ - 6, BAR_TOP), (W_ - 6, BAR_TOP + 9)]:
        for j, row in enumerate(PLATE):
            for i, ch in enumerate(row):
                c.p[y0 + j][x0 + i] = P[ch]
    c.p[BAR_TOP][W_ - 1] = None
    c.p[BAR_TOP + 14][W_ - 1] = None
    medallion(c, P)
    MP = dict(C)
    if mega_over:
        MP.update(mega_over)
    stamp(c, MEGAPHONE, MEGA_XY[0], MEGA_XY[1], MP)
    return c


def fill_canvas(ramps, edges, w=FILL_W, h=FILL_H):
    c = Canvas(w, h)
    for x in range(w):
        band = sum(1 for e in edges if x >= e)
        nb = band + 1 if (band < len(edges) and x in (edges[band] - 2, edges[band] - 1)) else band
        for y in range(h):
            b = nb if (nb != band and (x + y) % 2 == 0) else band
            hi, base, sh = ramps[b]
            c.p[y][x] = C[hi if y == 0 else (sh if y == h - 1 else base)]
    return c


HEAT = [('b', 'B', 'I'),      # blurple
        ('m', 'V', 'p'),      # purple
        ('S', 'm', 'V'),      # magenta
        ('Y', 'O', 'E'),      # orange
        ('W', 'Y', 'O')]      # gold
HEAT_EDGES = [18, 36, 54, 71]


def hype_fill():
    return fill_canvas(HEAT, HEAT_EDGES)


def label_frames():
    return [LT.word_canvas('HYPE', 'hype', False, LABEL_W, LABEL_H),
            LT.word_canvas('HYPE', 'hype', True, LABEL_W, LABEL_H)]


# ------------------------------------------------------------------ FULL overlay
LIT = {'Y': C['W'], 'S': C['W'], 'T': C['Y'], 'D': C['T'], 'o': C['D'], 'I': C['m'], 'n': C['p']}

FLAMES = {   # '.' empty; W core, Y, O, m, V edge
    'tall': [
        "...V...",
        "...mV..",
        "..Vm...",
        "..mOV..",
        ".VmOmV.",
        ".mOYOm.",
        "VmOYOmV",
        "mOYWYOm",
        "mOYWYOm",
        ".OYWYO.",
        "..YWY..",
    ],
    'wide': [
        "....V....",
        "...Vm.V..",
        "...mOVm..",
        "..VmOmOV.",
        ".VmOYOmm.",
        ".mOYWYOmV",
        "VmOYWWYOm",
        "mOYWWWYOm",
        ".OYWWWYO.",
    ],
    'mid': [
        "..V..",
        ".Vm..",
        ".mOV.",
        "VmOmV",
        "mOYOm",
        "mYWYm",
        ".YWY.",
    ],
    'small': [
        ".V.",
        "VmV",
        "mOm",
        "OYO",
        ".W.",
    ],
}
FPAL = {'W': C['W'], 'Y': C['Y'], 'O': C['O'], 'm': C['m'], 'V': C['V']}

# flame slots along the tube's top edge (x centre); kinds cycle per frame so the fire flickers.
# Slots under the label are mostly hidden by it (the label draws on top).
FLAME_SLOTS = [32, 42, 52, 62, 72, 82, 90, 98, 106, 113]
FLAME_CYCLE = ['tall', 'small', 'wide', 'mid']


def sparkle(c, x, y, size, core, tip):
    c.set(x, y, core)
    for k in range(1, size + 1):
        col = core if k < size else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.set(x + dx, y + dy, col)


def hot_fill(frame):
    """gold/white-hot fill with a diagonal shine sweeping left to right and magenta embers"""
    c = fill_canvas([('W', 'Y', 'O')], [])
    sx = [6, 30, 54, 78][frame]
    for y in range(FILL_H):
        for x in range(FILL_W):
            d = x - (sx - y)
            if 0 <= d < 3:
                c.p[y][x] = C['W']
            elif d == 3 and y > 0:
                c.p[y][x] = C['S']
    for (x, y) in [(14 + 23 * frame % 70, 2), (44 + 17 * frame % 40, 3), (70 - 11 * frame % 50, 1)]:
        if 0 <= x < FILL_W and c.p[y][x] != C['W']:
            c.p[y][x] = C['m']
    return c


def halo(c, base, col):
    """1 px glow ring on empty pixels around the meter silhouette"""
    solid = {(x, y) for y in range(base.h) for x in range(base.w) if base.p[y][x]}
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in solid and base.inb(*q) and c.get(*q) is None:
                c.set(q[0], q[1], col)


def full_frame(f):
    lit = f % 2 == 0
    c = frame_canvas(LIT if lit else None, {'m': C['e'], 'Y': C['W'], 'T': C['Y']} if lit else None)
    c.blit(hot_fill(f), FILL_X, FILL_Y)
    halo(c, frame_canvas(), C['m'] if lit else C['V'])
    # flames licking up from the tube's top rim (drawn over it)
    for i, x in enumerate(FLAME_SLOTS):
        kind = FLAME_CYCLE[(i + f) % len(FLAME_CYCLE)]
        g = FLAMES[kind]
        gh, gw = len(g), len(g[0])
        stamp(c, g, x - gw // 2, BAR_TOP + 3 - gh, FPAL)
    # shout lines off the medallion's top-left (manga emphasis), long on lit frames
    L = 4 if lit else 3
    for ang in (-160, -128, -96):
        a = math.radians(ang)
        r0 = MED_R + (2 if lit else 3)
        for k in range(L):
            x = int(round(MED_CX + (r0 + k) * math.cos(a)))
            y = int(round(MED_CY + (r0 + k) * math.sin(a)))
            c.set(x, y, C['W'] if k < 2 else C['Y'])
    # sparkles
    spots = [[(121, 11, 2), (70, 39, 1), (3, 9, 1)],
             [(116, 4, 1), (44, 39, 2), (24, 11, 1)],
             [(120, 15, 1), (96, 40, 1), (6, 5, 2)],
             [(110, 2, 2), (60, 40, 1), (26, 14, 1)]][f]
    for (x, y, s) in spots:
        sparkle(c, x, y, s, C['W'], C['Y'] if s > 1 else C['W'])
    return c


def full_frames():
    return [full_frame(f) for f in range(4)]


def build():
    return {
        'hype_meter_frame': [frame_canvas()],
        'hype_meter_fill': [hype_fill()],
        'hype_meter_full': full_frames(),
        'hype_label': label_frames(),
    }


def composite(frac=0.7, label_frame=0, full=None):
    A = build()
    c = A['hype_meter_frame'][0].copy()
    n = int(round(FILL_W * frac))
    if n:
        c.blit(crop(A['hype_meter_fill'][0], 0, 0, n, FILL_H), FILL_X, FILL_Y)
    if full is not None:
        c.blit(A['hype_meter_full'][full], 0, 0)
    c.blit(A['hype_label'][label_frame], LABEL_XY[0], LABEL_XY[1])
    return c


if __name__ == '__main__':
    A = build()
    for name, frames in A.items():
        s = strip(frames)
        save_zoom(s, work('%s_8x.png' % name), 8, bg=(70, 70, 90), grid=(frames[0].w, frames[0].h))
        print(name, s.w, s.h, 'non-DB32', s.colours() - DB32)
    comps = [composite(0.0), composite(0.7), composite(1.0)] + [composite(1.0, 1, f) for f in range(4)]
    stack = Canvas(W_, H_ * len(comps))
    for i, c in enumerate(comps):
        stack.blit(c, 0, i * H_)
    save_zoom(stack, work('hype_states_6x.png'), 6, bg=(70, 70, 90))
    save_zoom(crop(stack, 0, 0, W_, H_ * 2), work('hype_top_10x.png'), 10, bg=(70, 70, 90))
