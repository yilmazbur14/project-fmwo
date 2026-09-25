"""The Satsui no Hado aura: dark energy flames that take the place of Akuma's flame hair, rising from
behind the skull and off the shoulders, hot red at the root and violet toward the tips.

Kept from the approved sheet: the same idea and palette - tongues round the head and a pair off the
shoulders, violet-edged, red-hot near him, no black keyline (it is energy, not an object).
Changed:
  * the tongues are spaced so there is air between them above the skull; the approved centre five
    fused into a boxy crown with a notch in it;
  * the ordered-dither haze that clung to his whole outline read as dirt at 3x and fuzzed the
    silhouette; it is replaced by a few embers drifting up.
"""
import math
from lib import poly, ellipse, erode, grow

# (bezier control points root -> tip, root width, tip width)
IDLE = [
    ([(40.0, 27.5), (36.5, 23.0), (38.0, 18.5), (33.0, 14.0)], 7.2, 1.0),     # 0 left
    ([(47.5, 25.5), (49.0, 20.5), (46.0, 16.0), (48.5, 10.0)], 7.8, 1.0),     # 1 centre, tallest
    ([(55.0, 27.5), (58.5, 23.0), (57.0, 18.5), (62.0, 14.0)], 7.2, 1.0),     # 2 right
    ([(36.5, 32.5), (31.5, 29.0), (32.5, 25.0), (27.5, 21.5)], 5.8, 1.0),     # 3 left temple
    ([(58.5, 32.5), (63.5, 29.0), (62.5, 25.0), (67.5, 21.5)], 5.8, 1.0),     # 4 right temple
    ([(24.0, 56.0), (18.5, 51.5), (20.5, 47.0), (15.5, 43.0)], 6.2, 1.0),     # 5 left shoulder
    ([(71.0, 56.0), (76.5, 51.5), (74.5, 47.0), (79.5, 43.0)], 6.2, 1.0),     # 6 right shoulder
]

# embers drifting up off him: a point with a fading tail under it (x, y, hot) - dark, few
IDLE_EMBERS = [(31, 9, True), (66, 11, False)]


# the signature pose: the same tongues flaring bigger, plus pairs off the elbows and the legs
FLARE = [
    ([(40.0, 27.5), (35.5, 21.5), (37.5, 15.5), (30.5, 9.5)], 8.8, 1.0),     # 0 left
    ([(47.5, 25.5), (49.5, 18.5), (45.5, 12.5), (48.5, 4.5)], 9.6, 1.0),     # 1 centre
    ([(55.0, 27.5), (59.5, 21.5), (57.5, 15.5), (64.5, 9.5)], 8.8, 1.0),     # 2 right
    ([(36.5, 32.5), (30.0, 28.5), (31.5, 23.5), (23.5, 18.5)], 7.0, 1.0),    # 3 left temple
    ([(58.5, 32.5), (65.0, 28.5), (63.5, 23.5), (71.5, 18.5)], 7.0, 1.0),    # 4 right temple
    ([(24.0, 56.0), (17.0, 50.5), (19.5, 44.5), (11.5, 38.0)], 8.0, 1.0),    # 5 left shoulder
    ([(71.0, 56.0), (78.0, 50.5), (75.5, 44.5), (83.5, 38.0)], 8.0, 1.0),    # 6 right shoulder
    ([(23.5, 67.0), (16.5, 63.5), (18.5, 58.5), (11.5, 54.5)], 6.2, 1.0),    # 7 left elbow
    ([(71.5, 67.0), (78.5, 63.5), (76.5, 58.5), (83.5, 54.5)], 6.2, 1.0),    # 8 right elbow
    ([(31.0, 84.0), (25.0, 81.0), (26.5, 76.5), (20.5, 73.0)], 5.4, 1.0),    # 9 left leg
    ([(64.0, 84.0), (70.0, 81.0), (68.5, 76.5), (74.5, 73.0)], 5.4, 1.0),    # 10 right leg
]
FLARE_ORDER = [9, 10, 7, 8, 5, 6, 3, 4, 0, 2, 1]
FLARE_EMBERS = [(27, 5, True), (68, 5, False), (9, 34, False)]


def _bez(pts, t):
    p = list(pts)
    while len(p) > 1:
        p = [((1 - t) * p[i][0] + t * p[i + 1][0], (1 - t) * p[i][1] + t * p[i + 1][1])
             for i in range(len(p) - 1)]
    return p[0]


def tendril(ctrl, w0, w1, n=24):
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        cx, cy = _bez(ctrl, t)
        ax, ay = _bez(ctrl, min(1.0, t + 0.02))
        bx, by = _bez(ctrl, max(0.0, t - 0.02))
        dx, dy = ax - bx, ay - by
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        w = (w0 + (w1 - w0) * (t ** 1.35)) / 2.0      # stays full, then draws to a point: a flame, not a thorn
        left.append((cx + px * w, cy + py * w))
        right.append((cx - px * w, cy - py * w))
    return poly(left + list(reversed(right)))


def flames(specs, body, order=None, heat=0.0):
    """Returns a part dict. body: the set of pixels the figure covers (flames go behind it).

    Each tongue is layered and edged on its own and stamped over the ones behind it, so where two
    overlap the front one keeps its dark edge - they stay separate flames instead of fusing into one
    mass (which is what turned the approved centre five into a crown).
    heat (0..1, optional): how hot the aura burns - the hot zone reaches further out of him and the
    cores go orange-white. 0 is the resting aura every approved frame uses."""
    near = grow(body, 8 + int(round(8 * heat)))
    cool = ['U', 'T', 'S', 'R', 'R']
    hot = ['U', 'z', 'z', 'Y', 'y']          # the approved sheet's own reds: no #440618 anywhere
    if heat >= 0.5:
        hot = ['U', 'z', 'Y', 'y', 'X']
    if heat >= 0.9:
        hot = ['U', 'Y', 'y', 'X', 'x']
    part = {}
    idx = list(range(len(specs))) if order is None else order
    for i in idx:
        ctrl, w0, w1 = specs[i]
        whole = tendril(ctrl, w0, w1) - body
        rings = [whole] + [erode(whole, d) for d in range(1, 5)]
        for depth in range(5):
            cur = rings[depth] - (rings[depth + 1] if depth + 1 < len(rings) else set())
            for q in cur:
                part[q] = hot[depth] if q in near else cool[depth]
        for q in rings[-1]:
            part[q] = hot[4] if q in near else 'R'
    return part


# back to front: temples and shoulders, the outer pair, the inner pair, the centre tongue in front
IDLE_ORDER = [5, 6, 3, 4, 0, 2, 1]


def embers(spec):
    part = {}
    for x, y, hotp in spec:
        c, t1 = ('Y', 'z') if hotp else ('R', 'T')
        part[(x, y)] = c
        part[(x, y + 1)] = t1
    return part
