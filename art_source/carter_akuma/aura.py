"""Satsui no Hado aura: dark energy wisps that take the place of Akuma's
flame hair, plus a faint violet haze clinging to the silhouette."""
import math
from lib import (W, H, union, inter, sub, mirror, empty, grow, ring, dither,
                 poly, ell, PALC, BLACK, TH_HARD, TH_HARD2, bayer)


def _bez(pts, t):
    """de Casteljau on an arbitrary-degree bezier"""
    p = list(pts)
    while len(p) > 1:
        p = [((1 - t) * p[i][0] + t * p[i + 1][0],
              (1 - t) * p[i][1] + t * p[i + 1][1]) for i in range(len(p) - 1)]
    return p[0]


def tendril(ctrl, w0, w1, n=22):
    """curling energy tendril along a bezier spine, tapering w0 -> w1."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        cx, cy = _bez(ctrl, t)
        ax, ay = _bez(ctrl, min(1.0, t + 0.02))
        bx, by = _bez(ctrl, max(0.0, t - 0.02))
        dx, dy = ax - bx, ay - by
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        w = (w0 + (w1 - w0) * (t ** 0.75)) / 2.0
        left.append((cx + px * w, cy + py * w))
        right.append((cx - px * w, cy - py * w))
    return poly(left + list(reversed(right)))


def spark(x, y, r=1.0):
    return ell(x, y, r, r)


# each entry: (control points bottom->top, base width, tip width)
IDLE = [
    ([(38.5, 18.0), (34.0, 12.0), (35.5, 6.0), (30.0, 2.0)], 9.2, 1.2),
    ([(43.0, 14.0), (41.0, 8.5), (43.5, 4.0), (39.0, 0.5)], 7.9, 1.2),
    ([(47.8, 12.0), (48.5, 6.0), (46.0, 2.5), (49.5, 0.0)], 8.9, 1.2),
    ([(52.5, 13.0), (54.5, 8.0), (52.0, 3.5), (56.5, 1.0)], 7.9, 1.2),
    ([(57.0, 17.0), (61.5, 11.0), (59.0, 5.5), (65.0, 3.0)], 8.6, 1.2),
    ([(34.5, 22.0), (29.0, 17.0), (30.5, 11.5), (25.0, 8.5)], 6.6, 1.1),
    ([(61.0, 22.5), (66.5, 17.5), (65.0, 12.0), (70.5, 9.5)], 6.6, 1.1),
    ([(23.0, 44.0), (18.0, 39.0), (19.5, 34.0), (14.0, 30.0)], 7.6, 1.1),
    ([(72.5, 44.0), (77.5, 39.0), (76.0, 34.0), (81.5, 30.0)], 7.6, 1.1),
]

FLARE = [
    ([(37.0, 18.0), (30.0, 12.0), (32.5, 5.0), (24.0, 0.5)], 12.2, 1.3),
    ([(42.0, 14.0), (38.5, 8.0), (41.5, 3.0), (35.0, 0.0)], 10.2, 1.3),
    ([(47.8, 11.5), (49.0, 5.0), (45.5, 1.5), (50.5, -1.0)], 11.5, 1.3),
    ([(53.5, 12.5), (57.0, 6.5), (53.5, 2.0), (60.0, 0.0)], 10.2, 1.3),
    ([(58.5, 17.0), (65.0, 10.0), (62.0, 3.5), (70.5, 0.5)], 11.2, 1.3),
    ([(33.0, 23.0), (24.0, 17.0), (26.5, 9.5), (18.0, 5.0)], 8.9, 1.2),
    ([(62.5, 23.0), (71.5, 17.0), (69.0, 9.5), (77.5, 5.0)], 8.9, 1.2),
    ([(21.5, 45.0), (13.0, 39.0), (15.0, 31.0), (6.5, 25.0)], 10.2, 1.2),
    ([(74.0, 45.0), (82.5, 39.0), (80.5, 31.0), (89.0, 25.0)], 10.2, 1.2),
    ([(24.5, 59.0), (16.5, 54.0), (18.0, 47.0), (10.5, 43.0)], 8.2, 1.2),
    ([(71.0, 59.0), (79.0, 54.0), (77.5, 47.0), (85.0, 43.0)], 8.2, 1.2),
    ([(30.5, 83.0), (23.0, 80.0), (24.5, 74.5), (17.5, 71.0)], 7.3, 1.1),
    ([(65.0, 83.0), (72.5, 80.0), (71.0, 74.5), (78.0, 71.0)], 7.3, 1.1),
]

IDLE_SPARKS = [(30.5, 9.5), (65.5, 12.5), (19.5, 26.5), (76.5, 24.5),
               (44.5, 3.5), (52.5, 5.5)]
FLARE_SPARKS = [(26.5, 13.5), (69.5, 11.5), (14.5, 22.5), (81.5, 20.5),
                (33.5, 3.5), (62.5, 4.5), (6.5, 42.5), (89.5, 40.5),
                (16.5, 60.5), (79.5, 58.5), (44.5, 1.5), (51.5, 2.5)]


def build(specs, sparks, body_mask, crown=None):
    """returns (core_mask, mid_mask, edge_mask) for the wisps, body removed."""
    whole = empty()
    if crown is not None:
        whole = union(whole, crown)
    for ctrl, w0, w1 in specs:
        whole = union(whole, tendril(ctrl, w0, w1))
    for sx, sy in sparks:
        whole = union(whole, spark(sx, sy, 1.2))
    from lib import erode
    core = erode(whole, 2)
    mid = sub(erode(whole, 1), core)
    edge = sub(whole, erode(whole, 1))
    body = grow(body_mask, 1)
    return sub(core, body), sub(mid, body), sub(edge, body)


def paint(cv, specs, sparks, body_mask, hot=True):
    from lib import erode
    whole = empty()
    for ctrl, w0, w1 in specs:
        whole = union(whole, tendril(ctrl, w0, w1))
    for sx, sy in sparks:
        whole = union(whole, spark(sx, sy, 1.4))
    whole = sub(whole, grow(body_mask, 1))
    layers = [('S', 1), ('R', 2), ('Y' if hot else 'S', 3), ('y' if hot else 'R', 4)]
    cv.paint(whole, PALC['T'])
    for ch, n in layers:
        cv.paint(erode(whole, n), PALC[ch])
    # hot at the source, cool at the tips
    if hot:
        near = inter(whole, grow(body_mask, 7))
        warm = {PALC['T']: PALC['Z'], PALC['S']: PALC['z'],
                PALC['R']: PALC['Y'], PALC['Y']: PALC['y'],
                PALC['y']: PALC['X']}
        for y in range(H):
            for x in range(W):
                if near[y][x] and cv.px[y][x] in warm:
                    cv.px[y][x] = warm[cv.px[y][x]]
    cv.outline(whole, PALC['U'])
    return whole


def haze(cv, body_mask, inner=8, outer=4, off=0):
    """violet dissolve hugging the silhouette - opaque, alpha stays 0/255."""
    r1 = sub(grow(body_mask, 2), body_mask)
    r2 = sub(grow(body_mask, 4), grow(body_mask, 2))
    for rgn, lvl, ch in ((r1, inner, 'T'), (r2, outer, 'U')):
        d = bayer(rgn, lvl, off)
        for y in range(H):
            for x in range(W):
                if d[y][x] and cv.px[y][x] is None:
                    cv.px[y][x] = PALC[ch]


def eye_spill(cv):
    """a little red bleed under the sockets, so the glow feels lit"""
    for x, y in [(38, 31), (40, 31), (42, 31), (44, 31),
                 (51, 31), (53, 31), (55, 31), (57, 31)]:
        if cv.px[y][x] is not None and cv.px[y][x] != BLACK:
            cv.px[y][x] = PALC['w']
