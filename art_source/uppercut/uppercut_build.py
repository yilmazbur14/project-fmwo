"""Builds player_uppercut frames (48x64 each, 10 frames) = body poses (player palette) + energy FX (DB32).
Frame order: 0-2 charge loop, 3 launch, 4-6 rise, 7 apex, 8 fall, 9 land."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import *
import uppercut_poses as PO
from paths import work

FW, FH = 48, 64
GROUND = 60           # feet bottom row when grounded
Wc, Pc, Cc, Lc, Rc, Ic, Yc, Gc = FX['W'], FX['P'], FX['C'], FX['L'], FX['R'], FX['I'], FX['Y'], FX['G']

# (pose, lift R)
SEQ = [('CROUCH', 0), ('CROUCH_B', 0), ('CROUCH_C', 0), ('LAUNCH', 0), ('RISE1', 8), ('RISE2', 15),
       ('RISE3', 21), ('APEX', 22), ('FALL', 10), ('LAND', 0)]


PUFF = [
    ".PPP.",
    "PPPPG",
    "GPPGG",
    ".GGG.",
]
PUFF_S = [
    ".PP.",
    "PPPG",
    ".GG.",
]


class Layers:
    def __init__(self):
        self.back = Canvas(FW, FH)
        self.front = Canvas(FW, FH)


def put(c, x, y, col, body=None, only_empty=False):
    if only_empty and body is not None and body.get(x, y) is not None:
        return
    c.set(x, y, col)


def stamp_rows(c, rows, x0, y0, body=None, only_empty=False):
    """rows of chars in FX palette, '.' transparent"""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in '. ':
                continue
            put(c, x0 + i, y0 + j, PAL[ch], body, only_empty)


def rim(c, body, pts_set, col):
    """1px rim on empty pixels around a set of body pixels"""
    for (x, y) in pts_set:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + dx, y + dy
            if (X, Y) in pts_set:
                continue
            if body.get(X, Y) is None:
                c.set(X, Y, col)


def glove_pixels(body, x0, y0, x1, y1):
    out = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = body.get(x, y)
            if v in (PLAYER['a'], PLAYER['f'], PLAYER['g']):
                out.add((x, y))
    return out


def star4(c, x, y, arm, cols, body=None, only_empty=False):
    """cols: colours from centre outward, len >= arm+1"""
    put(c, x, y, cols[0], body, only_empty)
    for k in range(1, arm + 1):
        col = cols[min(k, len(cols) - 1)]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            put(c, x + dx, y + dy, col, body, only_empty)


def column(back, axis_x, y_top, y_bot, widths, cols):
    """energy column behind the body. widths(t)->half width (float), cols(t, edge)->colour"""
    n = max(1, y_bot - y_top)
    for y in range(y_top, y_bot + 1):
        t = (y - y_top) / n
        hw = widths(t)
        if hw <= 0:
            continue
        xa = int(math.floor(axis_x - hw + 0.5))
        xb = int(math.floor(axis_x + hw - 0.5))
        for x in range(xa, xb + 1):
            edge = (x == xa or x == xb)
            col = cols(t, edge, y)
            if col:
                back.set(x, y, col)


def strand(front, back, axis_x, y_top, y_bot, radius, turns, phase, colour, front_ok=None, body=None):
    """helix strand, 8-connected, front/back split by depth. Front pixels that would cover a body
    pixel outside front_ok(x, y) are demoted to the back layer (hidden behind the body)."""
    prev = None
    n = max(1, y_bot - y_top)
    for y in range(y_top, y_bot + 1):
        t = (y - y_top) / n
        th = phase + t * turns * 2 * math.pi
        r = radius(t)
        ax = axis_x(t) if callable(axis_x) else axis_x
        x = int(round(ax + r * math.sin(th)))
        depth = math.cos(th)
        col = colour(t, depth, y)
        if col is None:
            prev = None
            continue
        def plot(xx):
            tgt = front if depth > -0.2 else back
            if tgt is front and body is not None and body.get(xx, y) is not None and front_ok is not None \
                    and not front_ok(xx, y):
                tgt = back
            tgt.set(xx, y, col)
        plot(x)
        if prev is not None and abs(x - prev) > 1:
            step = 1 if x > prev else -1
            for xx in range(prev + step, x, step):
                plot(xx)
        prev = x


# ------------------------------------------------------------------ per-frame FX
def fx_charge(k, body, L):
    """k = 0,1,2 brightness; rear glove at (19..21, 50..52), centre ~(20, 51)"""
    g = glove_pixels(body, 17, 48, 23, 53)
    ring1 = set()
    for (x, y) in g:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            if body.get(x + dx, y + dy) is None:
                ring1.add((x + dx, y + dy))
    ring2 = set()
    for (x, y) in ring1:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if p not in ring1 and p not in g and body.get(*p) is None:
                ring2.add(p)
    # converging streaks: 2px dashes aimed at the fist
    far = [((11, 44), (12, 45)), ((9, 51), (10, 51)), ((12, 58), (13, 57)), ((17, 41), (17, 42))]
    mid = [((14, 46), (15, 47)), ((12, 51), (13, 51)), ((15, 56), (16, 55)), ((18, 44), (18, 45))]
    far2 = [((8, 47), (9, 47)), ((10, 55), (11, 55)), ((14, 42), (15, 43))]
    near = [((16, 48), (17, 49)), ((15, 51), (16, 51)), ((17, 54), (17, 55))]
    if k == 0:
        for (x, y) in ring1:
            if x <= 19 or y >= 53:
                put(L.back, x, y, Rc, body, True)
        for a, b in far:
            put(L.front, a[0], a[1], Rc, body, True)
            put(L.front, b[0], b[1], Lc, body, True)
    elif k == 1:
        for (x, y) in ring1:
            put(L.back, x, y, Lc, body, True)
        for (x, y) in ring2:
            if x <= 17:
                put(L.back, x, y, Rc, body, True)
        for (x, y) in g:
            if body.get(x, y) == PLAYER['g']:
                L.front.set(x, y, Pc)
        for a, b in mid:
            put(L.front, a[0], a[1], Lc, body, True)
            put(L.front, b[0], b[1], Cc, body, True)
        for a, b in far2:
            put(L.front, a[0], a[1], Rc, body, True)
            put(L.front, b[0], b[1], Lc, body, True)
    else:
        for (x, y) in ring2:
            put(L.back, x, y, Lc, body, True)
        for (x, y) in ring1:
            put(L.back, x, y, Pc if (x <= 19 and y <= 51) else Cc, body, True)
        for (x, y) in g:
            v = body.get(x, y)
            L.front.set(x, y, Wc if v == PLAYER['g'] else (Pc if v == PLAYER['a'] else Cc))
        star4(L.front, 18, 50, 4, [Wc, Wc, Pc, Cc, Lc], body, True)
        for a, b in near:
            put(L.front, a[0], a[1], Cc, body, True)
            put(L.front, b[0], b[1], Pc, body, True)
        for (x, y) in [(13, 47), (12, 53), (21, 55)]:
            put(L.front, x, y, Wc, body, True)


def fx_launch(body, L):
    g = glove_pixels(body, 28, 30, 35, 36)
    rim(L.back, body, g, Pc)
    # swing smear: crescent from the hip-front up to the fist, just ahead of the body
    smear = {
        33: [(35, 'P')],
        34: [(34, 'PW')],
        35: [(34, 'PWP')],
        36: [(34, 'CPPC')],
        37: [(34, 'CPCL')],
        38: [(34, 'CCCL')],
        39: [(33, 'LCCL')],
        40: [(33, 'LCLR')],
        41: [(32, 'LCLR')],
        42: [(32, 'LLR')],
        43: [(31, 'LLR')],
        44: [(30, 'RLR')],
        45: [(30, 'RR')],
        46: [(29, 'R')],
    }
    for y, segs in smear.items():
        for x, run in segs:
            for i, ch in enumerate(run):
                put(L.front, x + i, y, PAL[ch], body, True)
    star4(L.front, 35, 31, 2, [Wc, Pc, Cc], body, True)
    # take-off burst at the rear toe (toe at 13..15, 59..60)
    stamp_rows(L.back, [
        "..PP..",
        ".PPPP.",
        "PPPPGG",
        ".GGGG.",
    ], 6, 57, body, True)
    stamp_rows(L.back, PUFF_S, 16, 58, body, True)
    for (x, y, ch) in [(5, 55, 'G'), (11, 55, 'P'), (20, 56, 'G'), (22, 58, 'P'), (2, 60, 'P'), (3, 60, 'P'),
                       (21, 60, 'P'), (22, 60, 'P'), (23, 60, 'G')]:
        put(L.back, x, y, PAL[ch], body, True)


def path_x(ctrl, y):
    """cosine-interpolated x along a list of (y, x) control points sorted by y"""
    if y <= ctrl[0][0]:
        return ctrl[0][1]
    for (y0, x0), (y1, x1) in zip(ctrl, ctrl[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / float(y1 - y0)
            t = (1 - math.cos(t * math.pi)) / 2
            return x0 + (x1 - x0) * t
    return ctrl[-1][1]


# fist trail control points per rise frame (frame coords): the fist's earlier positions this move
RISE_PATHS = [
    [(20, 29.5), (30, 30.6), (41, 31.5), (52, 29.0), (60, 25.5)],
    [(13, 27.0), (29, 29.5), (48, 31.5), (56, 30.0), (60, 28.0)],
    [(7, 26.0), (21, 27.0), (35, 29.5), (54, 31.5), (60, 30.5)],
]
RISE_ARM_ROWS = [(19, 25), (12, 18), (6, 12)]   # rows where strands may cross the glove/forearm


def fx_rise(i, body, L, R):
    """i = 0,1,2 for RISE1..3: tapered energy column along the fist's path + two unequal spiral strands"""
    ctrl = RISE_PATHS[i]
    top = ctrl[0][0]
    glove_box = [(26, 19, 33, 25), (24, 12, 30, 17), (23, 6, 29, 11)][i]
    g = glove_pixels(body, *glove_box)
    rim(L.back, body, g, Pc)
    a0, a1 = RISE_ARM_ROWS[i]

    def front_ok(x, y):
        return a0 <= y <= a1

    n = GROUND - top
    for y in range(top, GROUND):
        t = (y - top) / float(n)
        ax = path_x(ctrl, y)
        hw = 2.0 - 1.4 * t
        if i == 2 and t > 0.8 and y % 2 == 0:
            continue                      # oldest part of the trail breaks up
        xa = int(math.floor(ax - hw + 0.5))
        xb = int(math.floor(ax + hw - 0.5))
        for x in range(xa, xb + 1):
            edge = (x == xa or x == xb)
            if edge:
                col = Cc if t < 0.2 else (Lc if t < 0.6 else Rc)
            else:
                col = Wc if t < 0.08 else (Pc if t < 0.25 else (Cc if t < 0.62 else Lc))
            L.back.set(x, y, col)

    phases = [0.4, 2.5, 4.6]
    specs = [  # (radius at top, radius mid, turns, bright)
        (3.4, 4.2, 2.3, True),
        (2.6, 3.2, 2.3, False),
    ]
    for s, (r_top, r_mid, turns, bright) in enumerate(specs):
        def radius(t, r_top=r_top, r_mid=r_mid):
            if t < 0.35:
                return r_top + (r_mid - r_top) * t / 0.35
            return r_mid * (1 - (t - 0.35) / 0.65) + 0.8 * ((t - 0.35) / 0.65)

        def colour(t, depth, y, bright=bright):
            if y >= GROUND or t > (0.92 if bright else 0.75):
                return None
            if bright:
                ramp = [Wc, Pc, Cc, Lc] if depth > 0.3 else [Pc, Cc, Lc, Rc]
            else:
                ramp = [Pc, Cc, Lc, Rc] if depth > 0.3 else [Cc, Lc, Rc, Rc]
            return ramp[min(3, int(t * 4))]

        strand(L.front, L.back, lambda t: path_x(ctrl, top + t * n), top, GROUND - 1, radius, turns,
               phases[i] + s * math.pi * 0.85, colour, front_ok=front_ok, body=body)
    fist = [(30, 21), (27, 14), (26, 8)][i]
    star4(L.front, fist[0] + 1, fist[1] - 3, 3 if i < 2 else 2, [Wc, Wc, Pc, Cc], body, True)


def fx_apex(body, L):
    g = glove_pixels(body, 23, 4, 29, 10)
    cx, cy = 26, 7            # glove centre at R=22
    # big 8-point flash BEHIND the glove so the fist silhouette stays readable
    star4(L.back, cx, cy, 6, [Wc, Wc, Wc, Pc, Pc, Cc, Lc])
    for k in (1, 2, 3, 4):
        col = [Wc, Wc, Pc, Cc][k - 1]
        for dx, dy in ((k, k), (-k, k), (k, -k), (-k, -k)):
            L.back.set(cx + dx, cy + dy, col)
    rim(L.back, body, g, Wc)
    # glove edge catches the light
    for (x, y) in g:
        if body.get(x, y) == PLAYER['g']:
            L.front.set(x, y, Pc)
    # dissolving sparkles along the old trail
    for (x, y, ch) in [(21, 14, 'P'), (31, 15, 'C'), (20, 22, 'L'), (32, 23, 'P'), (30, 31, 'L'),
                       (21, 38, 'R'), (28, 42, 'L'), (25, 49, 'R'), (33, 10, 'W'), (18, 9, 'C'), (35, 5, 'P')]:
        put(L.front, x, y, PAL[ch], body, True)
    for y in range(38, 54, 2):
        put(L.back, 26 + (1 if y % 4 == 0 else 0), y, Lc if y < 46 else Rc, body, True)


def fx_fall(body, L):
    for (x, y, ch) in [(28, 19, 'P'), (20, 21, 'C'), (33, 27, 'L'), (13, 30, 'L'), (31, 36, 'R'),
                       (16, 42, 'R'), (26, 16, 'C')]:
        put(L.front, x, y, PAL[ch], body, True)


def fx_land(body, L):
    stamp_rows(L.back, PUFF, 9, 57, body, True)
    stamp_rows(L.back, PUFF_S, 6, 58, body, True)
    stamp_rows(L.back, PUFF, 34, 57, body, True)
    stamp_rows(L.back, PUFF_S, 38, 58, body, True)
    for (x, y, ch) in [(7, 55, 'G'), (41, 55, 'G'), (13, 54, 'P'), (36, 54, 'P')]:
        put(L.back, x, y, PAL[ch], body, True)


def build_frames():
    frames, bodies = [], []
    for idx, (name, R) in enumerate(SEQ):
        body = PO.body_canvas(name, R)
        L = Layers()
        if idx <= 2:
            fx_charge(idx, body, L)
        elif idx == 3:
            fx_launch(body, L)
        elif idx <= 6:
            fx_rise(idx - 4, body, L, R)
        elif idx == 7:
            fx_apex(body, L)
        elif idx == 8:
            fx_fall(body, L)
        else:
            fx_land(body, L)
        out = Canvas(FW, FH)
        out.blit(L.back, 0, 0)
        out.blit(body, 0, 0)
        out.blit(L.front, 0, 0)
        frames.append(out)
        bodies.append((L.back, body, L.front))
    return frames, bodies


# frame timing (ms), tags and lift per frame, for the export + report
DURATIONS_MS = [80, 80, 80, 50, 60, 60, 60, 140, 100, 160]
TAGS = [('charge_loop', 1, 3), ('launch', 4, 4), ('rise', 5, 7), ('apex', 8, 8), ('land', 9, 10)]


if __name__ == '__main__':
    frames, bodies = build_frames()
    s = strip(frames)
    s.save(work('uc_strip.png'))
    save_zoom(s, work('uc_strip_5x.png'), 5, bg=(136, 180, 99), grid=(48, 64))
    save_zoom(s, work('uc_strip_2x.png'), 2, bg=(136, 180, 99), grid=(48, 64))
    print('ok', s.w, s.h)
