"""Stage 3: body layer with form-following 4-tone shading (Mason-style diagonal bands).
Writes parts/body_auto.txt (64x64). Hand edits happen in parts/body.txt afterwards."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import *
from palette import PAL

LIGHT = (-0.7, -1.0)  # direction pointing TOWARD the light (upper-left, mostly top)

RAMPS = {
    'white': ['W', 'w', 'v', 'u'],
    'black': ['B', 'k', 'j', 'j'],
    'tan':   ['1', '2', '3', '4'],
}


def march(mask, x, y, dx, dy, limit=64):
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    px, py = x + 0.5, y + 0.5
    for i in range(1, limit):
        qx, qy = px + dx * i, py + dy * i
        if (int(math.floor(qx)), int(math.floor(qy))) not in mask:
            return i
    return limit


def tone_map(mask, cuts=(0.22, 0.5, 0.78), light=LIGHT):
    out = {}
    for (x, y) in mask:
        a = march(mask, x, y, light[0], light[1])
        b = march(mask, x, y, -light[0], -light[1])
        t = a / float(a + b)
        k = 0
        while k < 3 and t >= cuts[k]:
            k += 1
        out[(x, y)] = k
    return out


def outline_of(mask):
    edge = set()
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in mask:
                edge.add((x, y))
                break
    return edge


def paint_form(g, form, pattern_fn, cuts=(0.22, 0.5, 0.78), light=LIGHT, outline=True):
    tones = tone_map(form, cuts, light)
    edge = outline_of(form) if outline else set()
    for (x, y) in form:
        if not (0 <= x < 64 and 0 <= y < 64):
            continue
        if (x, y) in edge:
            g[y][x] = 'K'
        else:
            g[y][x] = RAMPS[pattern_fn(x, y)][tones[(x, y)]]


def tail_mask_and_param(path, widths):
    m = mask_tube(path, widths)
    total = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
                for i in range(len(path) - 1))
    samples = []
    acc = 0
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        for s in range(60):
            t = s / 60
            samples.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, (acc + L * t) / total))
        acc += L
    param = {}
    for (x, y) in m:
        best = min(samples, key=lambda s: (s[0] - x - 0.5) ** 2 + (s[1] - y - 0.5) ** 2)
        param[(x, y)] = best[2]
    return m, param


# ------------------------------------------------------------------ shapes
TAIL_PATH = [(7.5, 44), (3.4, 38), (2.2, 31), (2.4, 24), (4.0, 17.5), (7.4, 13), (11.5, 10.6), (15.0, 10.8)]
TAIL_W = (3.5, 1.9)
TAIL_SPLIT = 0.46

# single traced contour: torso + near hind leg + near front leg
BODY = [(9.0, 36.6), (6.0, 37.2), (4.0, 38.6), (2.6, 40.6), (2.0, 43.0), (2.2, 46.0), (2.8, 49.0),
        (3.6, 52.0), (4.4, 54.5), (4.6, 56.6), (4.2, 58.4), (3.6, 60.2), (3.0, 62.0), (3.2, 64.0),
        (14.8, 64.0), (14.8, 62.2), (13.6, 61.0), (12.2, 60.4), (11.8, 58.0), (12.0, 55.8),
        (13.2, 53.6), (15.0, 51.8), (16.6, 50.2), (19.5, 49.8), (23.0, 49.4), (26.0, 50.0),
        (26.4, 52.0), (26.0, 55.0), (26.2, 58.0), (25.6, 60.2), (24.4, 62.0), (24.4, 64.0),
        (36.6, 64.0), (36.6, 62.2), (35.4, 61.0), (34.4, 59.4), (34.6, 56.0), (35.0, 52.6),
        (36.2, 51.6), (38.6, 51.4), (41.0, 50.8), (45.0, 50.0), (48.6, 48.6), (51.4, 46.4),
        (53.4, 43.4), (54.2, 40.4), (53.8, 37.6), (52.2, 35.2), (49.0, 33.6), (44.0, 33.0),
        (34.0, 33.6), (24.0, 34.6), (15.0, 35.6)]
# form masks used only for shading (subsets of BODY)
TORSO = [(0, 30), (58, 30), (58, 50.6), (41, 50.8), (36, 51.8), (26, 50), (16.6, 50.2), (0, 52)]
NEAR_HIND = [(0, 43), (16, 44), (17.5, 50), (13, 54), (12, 58), (15, 62), (15, 64), (0, 64)]
NEAR_FRONT = [(25.5, 46), (35.5, 46), (35, 53), (34.4, 59), (37, 62), (37, 64), (24, 64), (26, 58)]
FAR_HIND = [(15.0, 49.0), (21.0, 49.0), (21.8, 51.5), (21.4, 54.0), (20.0, 56.2), (20.0, 58.2),
            (21.0, 59.6), (22.4, 60.6), (22.4, 62.4), (14.0, 62.4), (14.4, 60.6), (15.4, 58.4),
            (15.0, 55.4), (14.4, 52.0)]
FAR_FRONT = [(38.0, 49.0), (46.0, 48.0), (46.4, 52.0), (46.0, 55.0), (46.2, 58.0), (47.2, 59.8),
             (48.4, 60.8), (48.4, 62.4), (37.4, 62.4), (37.6, 60.6), (38.6, 59.2), (38.8, 56.0),
             (38.4, 52.4)]
NECK_C = [(25.4, 20), (37.6, 20), (38.4, 26), (39.0, 31), (40.4, 35), (23.6, 35), (25.0, 31), (24.8, 26)]
NECK_L = [(10.0, 30.0), (20.5, 29.5), (22.5, 33.0), (23.5, 36.5), (12.5, 37.0), (11.0, 34.0)]
NECK_R = [(42.5, 29.5), (53.0, 30.0), (52.0, 34.0), (50.5, 37.0), (39.5, 36.5), (40.5, 33.0)]

SADDLE = [(0, 0), (64, 0), (64, 44), (52, 45), (46, 47.5), (40.5, 46), (24, 47.2), (20, 47.8),
          (14, 48.2), (8, 48.6), (0, 49.5)]
BIB = [(25.5, 30), (38.5, 30), (40, 38), (40.5, 44), (39, 50), (36.5, 53), (27, 53), (25.5, 48), (24.5, 40)]
STRIPE = [(13.5, 30), (18.5, 30), (18.2, 38), (17.6, 48.5), (12.6, 48.8), (13.0, 38)]
TAN_HIP = [(0, 47.6), (8, 46.8), (12.6, 46.4), (12.6, 50.2), (8, 50.4), (0, 51.2)]


def build():
    g = blank()
    saddle = mask_poly(SADDLE)
    stripe = mask_poly(STRIPE)
    tan = mask_poly(TAN_HIP)

    bib = mask_poly(BIB)

    def coat(x, y):
        if (x, y) in bib:
            return 'white'
        if (x, y) in stripe and (x, y) in saddle:
            return 'white'
        if (x, y) in tan:
            return 'tan'
        if (x, y) in saddle:
            return 'black'
        return 'white'

    # tail (back)
    tm, tp = tail_mask_and_param(TAIL_PATH, TAIL_W)
    paint_form(g, tm, lambda x, y: 'black' if tp[(x, y)] < TAIL_SPLIT else 'white',
               cuts=(0.25, 0.55, 0.8), light=(-1.0, -0.4))
    # far legs
    paint_form(g, mask_poly(FAR_HIND), lambda x, y: 'white', cuts=(0.1, 0.3, 0.62), light=(-1, -0.3))
    paint_form(g, mask_poly(FAR_FRONT), lambda x, y: 'white', cuts=(0.1, 0.3, 0.62), light=(-1, -0.3))
    body = mask_poly(BODY)
    torso = mask_poly(TORSO) & body
    nh = mask_poly(NEAR_HIND) & body
    nf = mask_poly(NEAR_FRONT) & body
    nl, nr, nc = mask_poly(NECK_L), mask_poly(NECK_R), mask_poly(NECK_C)
    union = body | nl | nr | nc
    edge = outline_of(union)
    layers = [
        (torso, coat, (0.2, 0.48, 0.78), LIGHT),
        (nh, coat, (0.25, 0.5, 0.8), (-1.0, -0.5)),
        (nf, lambda x, y: 'white', (0.25, 0.5, 0.8), (-1.0, -0.5)),
        (nl, lambda x, y: 'white', (0.3, 0.6, 0.85), (-1.0, -0.3)),
        (nr, lambda x, y: 'white', (0.3, 0.6, 0.85), (-1.0, -0.3)),
        (nc, lambda x, y: 'white', (0.3, 0.6, 0.85), (-1.0, -0.3)),
    ]
    for form, pat, cuts, light in layers:
        tones = tone_map(form, cuts, light)
        for (x, y) in form:
            if 0 <= x < 64 and 0 <= y < 64:
                g[y][x] = RAMPS[pat(x, y)][tones[(x, y)]]
    for (x, y) in body:
        if 0 <= x < 64 and 0 <= y < 64 and g[y][x] == '.':
            g[y][x] = 'k'
    for (x, y) in edge:
        if 0 <= x < 64 and 0 <= y < 64:
            g[y][x] = 'K'
    return g


if __name__ == '__main__':
    g = build()
    save_rows(os.path.join(HERE, 'parts', 'body_auto.txt'), g)
    print('ok')
