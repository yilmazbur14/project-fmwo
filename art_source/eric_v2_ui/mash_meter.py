"""The tiered finisher's mash meter: today's 72x16 brass meter (qte_meter_frame, reused pixel for pixel)
with its channel split into three windows, so it keeps the prompt's footprint between the two keys.

  qte_meter3_frame   72x16        the approved frame; two brass struts split the channel into three
                                  16-texel windows at x 7, 28 and 49
  qte_meter3_fill    58x6         drawn at (7, 5) like today's fill. Each window holds a third of today's
                                  heat ramp: bar 1 blue, bar 2 cyan to white, bar 3 white to gold, so a
                                  full meter still reads as the old one. The strut columns are clear.
  qte_meter3_banked  3 rows x 4   72x16 overlays, one row per bar: a banked bar keeps its colour with a
                                  white top edge, a glint sweeps across it (frames 0-2, then a rest), and
                                  the strut after it lights up. Drawn at (0, 0), looped.
  qte_meter3_flash   3 rows x 4   96x40 bursts, one row per bar, played once as that bar banks. Drawn at
                                  (-12, -12). Each tier throws a bigger burst.
  qte_meter3_full    2 x 72x16    today's qte_meter_full for this meter: the whole meter flashing as bar 3
                                  banks and the mash resolves (white-hot on lit brass, gold on plain brass)
"""
import math
import sys
sys.dont_write_bytecode = True
from ev2_common import *
import qte_ui as UI

MW, MH = 72, 16
FILL_X, FILL_Y, FILL_W, FILL_H = 7, 5, 58, 6
WIN_W, STRUT_W = 16, 5
WINDOWS = [7, 28, 49]                        # first column of each window, in the frame
STRUTS = [23, 44]                            # first column of each strut, in the frame

# each bar's (highlight, base, shade) bands, two per window, from today's heat ramp
BANDS = [
    [('b', 'B', 'I'), ('C', 'b', 'B')],      # bar 1: blue, "decently hard"
    [('P', 'C', 'b'), ('W', 'P', 'C')],      # bar 2: cyan into white, "hard"
    [('W', 'Y', 'T'), ('W', 'Y', 'O')],      # bar 3: gold, "intense", Knight Breaker's colour
]
# a banked bar keeps its colour, so the three bars stay three different tiers, but its top edge burns
# white and a glint runs across it
BANKED = [
    [('W', 'B', 'I'), ('W', 'b', 'B')],
    [('W', 'C', 'b'), ('W', 'P', 'C')],
    [('W', 'Y', 'T'), ('W', 'Y', 'O')],
]


def strut(c, x0, pal=None):
    """a brass post between two windows, cast into the rails above and below it"""
    P = dict(C)
    if pal:
        P.update(pal)
    for y in range(4, 12):
        for i, ch in enumerate('KYTDK'):
            c.p[y][x0 + i] = P[ch]
    # joined to the rails: the post's brass runs through their inner outline rows
    for i, (top, bottom) in enumerate([('K', 'K'), ('Y', 'T'), ('T', 'T'), ('D', 'D'), ('K', 'K')]):
        c.p[4][x0 + i] = P[top] if i in (1, 2, 3) else P['K']
        c.p[11][x0 + i] = P[bottom] if i in (1, 2, 3) else P['K']
    # a rivet in the middle of the post
    c.p[7][x0 + 2] = P['W']
    c.p[8][x0 + 2] = P['p']


def window_inset(c, x0):
    """a window's inset look, as today's channel: shadow on the top and left, reflected light below and
    on the right, navy between"""
    for y in range(5, 11):
        for x in range(x0, x0 + WIN_W):
            if y == 5:
                col = 'K'
            elif y == 10:
                col = 'I'
            elif x == x0:
                col = 'K'
            elif x == x0 + WIN_W - 1:
                col = 'I'
            else:
                col = 'n'
            c.p[y][x] = C[col]


def frame_canvas(lit_struts=()):
    c = UI.meter_frame()
    for x0 in WINDOWS:
        window_inset(c, x0)
    for i, x0 in enumerate(STRUTS):
        strut(c, x0, LIT_BRASS if i in lit_struts else None)
    return c


LIT_BRASS = {'Y': C['W'], 'T': C['Y'], 'D': C['T'], 'p': C['D'], 'S': C['W'], 'o': C['D']}


def window_fill(bar, bands, w=WIN_W, h=FILL_H):
    """one window's fill: two bands with a 2-column checker dither between them"""
    c = Canvas(w, h)
    edge = w // 2
    for x in range(w):
        band = 0 if x < edge else 1
        nb = 1 if x in (edge - 2, edge - 1) else band
        for y in range(h):
            b = nb if (nb != band and (x + y) % 2 == 0) else band
            hi, base, sh = bands[bar][b]
            c.p[y][x] = C[hi if y == 0 else (sh if y == h - 1 else base)]
    return c


def meter_fill():
    c = Canvas(FILL_W, FILL_H)
    for bar, x0 in enumerate(WINDOWS):
        c.blit(window_fill(bar, BANDS), x0 - FILL_X, 0)
    return c


BANKED_MS = [60, 60, 60, 240]
GLINT_X = [4, 10, 16, None]        # a diagonal glint sweeps across the window, then rests


def banked_frames(bar):
    out = []
    x0 = WINDOWS[bar]
    for f, gx in enumerate(GLINT_X):
        c = Canvas(MW, MH)
        w = window_fill(bar, BANKED)
        if gx is not None:
            for y in range(FILL_H):
                for x in range(gx - y, gx - y + 2):
                    if 0 <= x < WIN_W:
                        w.p[y][x] = C['W']
        c.blit(w, x0, FILL_Y)
        # the post after the bar lights up (brightest while the glint passes); bar 3 lights the right
        # end cap's inner edge instead
        bright = gx is not None
        if bar < 2:
            s = Canvas(MW, MH)
            strut(s, STRUTS[bar], LIT_BRASS if bright else {'Y': C['W'], 'T': C['Y']})
            for y in range(4, 12):
                for x in range(STRUTS[bar] + 1, STRUTS[bar] + 4):
                    c.p[y][x] = s.p[y][x]
        else:
            for y in range(6, 10):
                c.p[y][66] = C['W']
                c.p[y][67] = C['Y'] if bright else C['S']
        out.append(c)
    return out


FL_PAD_X, FL_PAD_Y = 12, 12
FW_, FH_ = MW + 2 * FL_PAD_X, MH + 2 * FL_PAD_Y
FLASH_MS = [40, 50, 60, 70]


def flash_frames(bar):
    """a burst from the window as it banks: white-out, rays through the rails, sparks. Bigger per tier."""
    out = []
    x0 = WINDOWS[bar] + FL_PAD_X
    cx = x0 + WIN_W / 2.0 - 0.5
    top, bottom = FL_PAD_Y, FL_PAD_Y + MH - 1
    reach = [6, 8, 11][bar]
    rays = [(-4, 'up'), (4, 'up'), (0, 'up'), (-4, 'down'), (4, 'down'), (0, 'down')]
    if bar >= 1:
        rays += [(-7, 'up'), (7, 'up'), (-7, 'down'), (7, 'down')]
    for f in range(4):
        c = Canvas(FW_, FH_)
        if f == 0:
            for y in range(FL_PAD_Y + FILL_Y - 1, FL_PAD_Y + FILL_Y + FILL_H + 1):
                for x in range(x0 - 1, x0 + WIN_W + 1):
                    put(c, x, y, 'W')
            halo(c, C['Y'])
        elif f == 1:
            for y in range(FL_PAD_Y + FILL_Y, FL_PAD_Y + FILL_Y + FILL_H):
                for x in range(x0, x0 + WIN_W):
                    put(c, x, y, 'W' if y == FL_PAD_Y + FILL_Y else 'Y')
        # rays: grow on 0-1, detach and thin on 2-3
        seg = {0: (1, reach // 2), 1: (1, reach), 2: (reach // 2, reach + 2), 3: (reach, reach + 3)}[f]
        for dx, way in rays:
            long_ray = dx == 0
            r0, r1 = seg
            if not long_ray:
                r0, r1 = max(1, r0 - 1), max(1, r1 - 3)
            for r in range(r0, r1 + 1):
                y = top - r if way == 'up' else bottom + r
                x = cx + dx + (dx / 4.0) * (r / 3.0)
                col = 'W' if r - r0 < 2 and f < 2 else ('Y' if f < 3 else 'T')
                put(c, int(round(x)), y, col)
        if f >= 1:
            for (dx, dy, s) in [(-11, -3, 1), (12, -2, 1), (-10, 4, 0), (11, 5, 0)][: 2 + bar]:
                sx = int(round(cx + dx * (1 + 0.25 * f)))
                sy = (top + dy) if dy < 0 else (bottom + dy)
                sy += (-f if dy < 0 else f)
                if 0 <= sx < FW_ and 0 <= sy < FH_:
                    sparkle(c, sx, sy, s if f < 3 else 0, 'W', 'Y')
        out.append(c)
    return out


def full_frames():
    """today's qte_meter_full for the three-window meter: the whole meter flashing once bar 3 banks,
    frame 0 white-hot on lit brass, frame 1 gold on plain brass"""
    out = []
    for lit in (True, False):
        c = UI.meter_frame(lit=lit)
        for i, x0 in enumerate(STRUTS):
            strut(c, x0, LIT_BRASS if lit else None)
        ramp = [('W', 'W', 'P')] * 2 if lit else [('W', 'Y', 'T')] * 2
        for bar, x0 in enumerate(WINDOWS):
            c.blit(window_fill(0, [ramp]), x0, FILL_Y)
        if lit:
            for (x, y) in [(12, 7), (33, 6), (55, 8)]:
                c.set(x, y, C['Y'])
        out.append(c)
    return out


def build():
    return {
        'qte_meter3_frame': [frame_canvas()],
        'qte_meter3_fill': [meter_fill()],
        'qte_meter3_banked': [banked_frames(b) for b in range(3)],
        'qte_meter3_flash': [flash_frames(b) for b in range(3)],
        'qte_meter3_full': full_frames(),
    }


def composite(meter, banked=(), glint_frame=0, flash=None):
    """meter in bars (0..3): banked bars show their overlay, the current bar fills from its left"""
    A = build()
    c = A['qte_meter3_frame'][0].copy()
    fill = A['qte_meter3_fill'][0]
    for bar, x0 in enumerate(WINDOWS):
        part = min(max(meter - bar, 0.0), 1.0)
        n = int(round(WIN_W * part))
        if n:
            c.blit(crop(fill, x0 - FILL_X, 0, n, FILL_H), x0, FILL_Y)
    for bar in banked:
        c.blit(A['qte_meter3_banked'][bar][glint_frame], 0, 0)
    if flash is not None:
        bar, f = flash
        big = Canvas(FW_, FH_)
        big.blit(c, FL_PAD_X, FL_PAD_Y)
        big.blit(A['qte_meter3_flash'][bar][f], 0, 0)
        return big
    return c


if __name__ == '__main__':
    A = build()
    for name, v in A.items():
        rows = v if isinstance(v[0], list) else [v]
        for r in rows:
            for f in r:
                check_db32(f, name)
        print(name, len(rows), 'x', len(rows[0]), rows[0][0].w, rows[0][0].h)
