"""Juggle-sheet machinery shared by Josh's and Danny's juggle rigs (art_source/danny_juggle imports it).

Nothing here draws a character. A pose is built from the character's APPROVED rig, part by part, into
a Fig: a key map (one palette key per pixel, the rig's own keys) that also remembers which part owns
each pixel and each part's whole silhouette. Then:

  relight()   turns the key light back to the frame's upper left for a figure that is about to be
              rotated. Rotating a sprite rotates its shading with it; the cast is lit from the upper
              left. Each part keeps its own volume (its silhouette inflated, the same trick
              sumo_lib.intensity uses), only the SURFACE NORMAL is turned by the rotation, and the
              light stays put. The change in light is added to each pixel's tone as a continuous value
              (slope measured off the approved frame, per ramp family), and the tones are then dealt
              back out per family in the pose's OWN proportions, highlight to deep. So the ramp shares
              of a relit frame are exactly those of the same pose unrotated -- the trap the contract
              names (a relight that refit the light and went from 14% to 31% deep shadow) cannot happen.
  rot90()     exact quarter turns, lossless: the approved pixels, turned.
  rotsprite() any other angle (RotSprite: Scale2x three times, nearest sample back), with the face's
              features lifted off first and put back crisp (turned by the nearest quarter turn).

Angles are screen degrees, clockwise positive (y points down).
"""
import math

import numpy as np

LIGHT = np.array([-0.45, -0.58, 0.68])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# ------------------------------------------------------------------ THE FIGURE
class Fig:
    """A pose being assembled in the character's own upright frame, on a canvas `w` x `h` whose
    origin is shifted by `off` (so rig coordinates stay what they are in the approved rig, and limbs
    thrown past the rig's own frame are not clipped)."""

    def __init__(self, w, h, off=(0, 0)):
        self.w, self.h, self.off = w, h, off
        self.px, self.lab = {}, {}
        self.masks = {}          # label -> the part's whole silhouette (keyline included)
        self.flat = set()        # labels that are flat props: never relit (cards, effects)

    def inside(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, label='body', flat=False):
        """The rig's Canvas.stamp: a 1px keyline round the part over whatever is under it, then the
        part. Records the owner of every pixel it writes and the part's silhouette."""
        ox, oy = self.off
        part = {(x + ox, y + oy): k for (x, y), k in part.items()}
        body = set(part)
        mask = self.masks.setdefault(label, set())
        if flat:
            self.flat.add(label)
        if outline:
            for (x, y) in body:
                for dx, dy in N4:
                    q = (x + dx, y + dy)
                    if q not in body and self.inside(q):
                        self.px[q] = 'k'
                        self.lab[q] = label
                        mask.add(q)
        for q, k in part.items():
            if self.inside(q):
                self.px[q] = k
                self.lab[q] = label
                mask.add(q)

    def put(self, part, label='fx', only_empty=False):
        """Pixels with no keyline of their own (glows, smears, dust), as a flat prop."""
        ox, oy = self.off
        self.flat.add(label)
        for (x, y), k in part.items():
            q = (x + ox, y + oy)
            if self.inside(q) and (not only_empty or q not in self.px):
                self.px[q] = k
                self.lab[q] = label
                self.masks.setdefault(label, set()).add(q)

    def local(self, p):
        return (p[0] + self.off[0], p[1] + self.off[1])


# ------------------------------------------------------------------ NORMALS
def _blur(a, sigma):
    r = max(1, int(3 * sigma + 1))
    xs = np.arange(-r, r + 1, dtype=float)
    k = np.exp(-(xs ** 2) / (2 * sigma * sigma))
    k /= k.sum()
    a = np.pad(a, r)
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 0, a)
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 1, a)
    return a[r:-r, r:-r]


def normals(mask, sigma=None, bulge=0.8):
    """The surface normal of a part's inflated silhouette at each of its pixels: its mask blurred
    into a height field (sumo_lib.intensity's volume), then the slope."""
    mask = set(mask)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    x0, y0 = min(xs), min(ys)
    if sigma is None:
        sigma = max(1.6, 0.35 * math.sqrt(len(mask) / math.pi))
    pad = int(3 * sigma) + 3
    w = max(xs) - x0 + 1 + 2 * pad
    h = max(ys) - y0 + 1 + 2 * pad
    m = np.zeros((h, w))
    for (x, y) in mask:
        m[y - y0 + pad, x - x0 + pad] = 1.0
    hf = _blur(m, sigma)
    gy, gx = np.gradient(hf)
    s = 6.0 * sigma * bulge
    out = {}
    for (x, y) in mask:
        i, j = y - y0 + pad, x - x0 + pad
        n = np.array([-gx[i, j] * s, -gy[i, j] * s, 1.0])
        out[(x, y)] = n / np.linalg.norm(n)
    return out


def fig_normals(fig, sigmas=None):
    """Normals for every relightable pixel of a figure, each from its OWNER part's whole silhouette."""
    sigmas = sigmas or {}
    out = {}
    for label, mask in fig.masks.items():
        if label in fig.flat or not mask:
            continue
        nn = normals(mask, sigma=sigmas.get(label))
        for q in mask:
            if fig.lab.get(q) == label and q in nn:
                out[q] = nn[q]
    return out


def rotn(n, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([n[0] * c - n[1] * s, n[0] * s + n[1] * c, n[2]])


# ------------------------------------------------------------------ THE RELIGHT
def key_families(families):
    """{family: 'keys dark->light'} -> {key: (family, index)}."""
    out = {}
    for fam, keys in families.items():
        for i, k in enumerate(keys):
            out[k] = (fam, i)
    return out


def fit_slopes(px, nrm, families):
    """Tone steps per unit of light, per family, measured off an approved frame: the least-squares
    slope of each pixel's ramp index against its normal's dot with the key light."""
    k2f = key_families(families)
    out = {}
    for fam in families:
        X, Y = [], []
        for q, k in px.items():
            if q in nrm and k in k2f and k2f[k][0] == fam:
                X.append(float(nrm[q] @ LIGHT))
                Y.append(k2f[k][1])
        if len(X) < 12:
            out[fam] = 0.0
            continue
        X, Y = np.array(X), np.array(Y, dtype=float)
        A = np.vstack([X, np.ones_like(X)]).T
        (slope, _), *_ = np.linalg.lstsq(A, Y, rcond=None)
        out[fam] = max(0.0, float(slope))
    return out


def relight(fig, deg, families, slopes, gain=1.0, nrm=None, skip=()):
    """The figure's key map with the light turned back to the upper left for a figure about to be
    rotated by `deg`. Rank-preserving per family (see the module note). Pixels of flat labels and
    keys outside the families are left exactly as they are."""
    if not deg:
        return dict(fig.px)
    nrm = nrm if nrm is not None else fig_normals(fig)
    k2f = key_families(families)
    out = dict(fig.px)
    groups = {}
    for q, k in fig.px.items():
        if q not in nrm or k not in k2f or fig.lab.get(q) in skip:
            continue
        fam, i = k2f[k]
        n0 = nrm[q]
        d = float(rotn(n0, deg) @ LIGHT - n0 @ LIGHT)
        groups.setdefault(fam, []).append((i + slopes.get(fam, 0.0) * gain * d, i, q))
    for fam, items in groups.items():
        counts = [0] * len(families[fam])
        for _, i, _ in items:
            counts[i] += 1
        items.sort(key=lambda t: (t[0], t[1], t[2][1], t[2][0]))
        pos = 0
        for tone, c in enumerate(counts):
            for _, _, q in items[pos:pos + c]:
                out[q] = families[fam][tone]
            pos += c
    return out


# ------------------------------------------------------------------ ROTATION
def rot90(px, turns, pivot, to):
    """Exact quarter turns (clockwise positive) about an integer pivot, the pivot placed at `to`."""
    out = {}
    cx, cy = pivot
    tx, ty = to
    t = turns % 4
    for (x, y), k in px.items():
        u, v = x - cx, y - cy
        for _ in range(t):
            u, v = -v, u
        out[(tx + u, ty + v)] = k
    return out


def rot_pt(p, deg, pivot, to=None):
    """Where a point goes under the same rotation (continuous)."""
    to = to or pivot
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (to[0] + x * math.cos(a) - y * math.sin(a), to[1] + x * math.sin(a) + y * math.cos(a))


def _scale2x(grid):
    h, w = len(grid), len(grid[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            p = grid[y][x]
            a = grid[y - 1][x] if y > 0 else p
            b = grid[y][x + 1] if x < w - 1 else p
            c = grid[y][x - 1] if x > 0 else p
            d = grid[y + 1][x] if y < h - 1 else p
            e0 = e1 = e2 = e3 = p
            if c == a and c != d and a != b:
                e0 = a
            if a == b and a != c and b != d:
                e1 = b
            if d == c and d != b and c != a:
                e2 = c
            if b == d and b != a and d != c:
                e3 = d
            out[2 * y][2 * x] = e0
            out[2 * y][2 * x + 1] = e1
            out[2 * y + 1][2 * x] = e2
            out[2 * y + 1][2 * x + 1] = e3
    return out


def rotsprite(px, deg, pivot, to=None):
    """RotSprite (the approved rig's ground_kit.rotate, generalised to place the pivot at `to`):
    Scale2x three times, each output pixel sampled back from the 8x image. No re-keyline here."""
    to = to or pivot
    if not px:
        return {}
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    x0, y0 = min(xs) - 2, min(ys) - 2
    x1, y1 = max(xs) + 2, max(ys) + 2
    w, h = x1 - x0 + 1, y1 - y0 + 1
    grid = [[px.get((x0 + x, y0 + y), '.') for x in range(w)] for y in range(h)]
    big = grid
    for _ in range(3):
        big = _scale2x(big)
    S = 8
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    corners = [(x0 - 1, y0 - 1), (x1 + 1, y0 - 1), (x0 - 1, y1 + 1), (x1 + 1, y1 + 1)]
    rc = [rot_pt(c, deg, pivot, to) for c in corners]
    ox0, ox1 = int(math.floor(min(c[0] for c in rc))), int(math.ceil(max(c[0] for c in rc)))
    oy0, oy1 = int(math.floor(min(c[1] for c in rc))), int(math.ceil(max(c[1] for c in rc)))
    out = {}
    for oy in range(oy0, oy1 + 1):
        for ox in range(ox0, ox1 + 1):
            dx, dy = ox - to[0], oy - to[1]
            sx = pivot[0] + dx * ca + dy * sa
            sy = pivot[1] - dx * sa + dy * ca
            bx = int(math.floor((sx - x0 + 0.5) * S))
            by = int(math.floor((sy - y0 + 0.5) * S))
            if 0 <= bx < w * S and 0 <= by < h * S:
                k = big[by][bx]
                if k != '.':
                    out[(ox, oy)] = k
    return out


def affine(px, M, pivot, to):
    """RotSprite with any 2x2 matrix M (a turn, a squash, both): Scale2x three times, then every
    output pixel samples the 8x image through the inverse of M. dst = M . (src - pivot) + to."""
    if not px:
        return {}
    a, b, c, d = M
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    x0, y0 = min(xs) - 2, min(ys) - 2
    x1, y1 = max(xs) + 2, max(ys) + 2
    w, h = x1 - x0 + 1, y1 - y0 + 1
    grid = [[px.get((x0 + x, y0 + y), '.') for x in range(w)] for y in range(h)]
    big = grid
    for _ in range(3):
        big = _scale2x(big)
    S = 8
    cx = [a * (u - pivot[0]) + b * (v - pivot[1]) + to[0] for u in (x0 - 1, x1 + 1) for v in (y0 - 1, y1 + 1)]
    cy = [c * (u - pivot[0]) + d * (v - pivot[1]) + to[1] for u in (x0 - 1, x1 + 1) for v in (y0 - 1, y1 + 1)]
    out = {}
    for oy in range(int(math.floor(min(cy))), int(math.ceil(max(cy))) + 1):
        for ox in range(int(math.floor(min(cx))), int(math.ceil(max(cx))) + 1):
            dx, dy = ox - to[0], oy - to[1]
            sx = pivot[0] + ia * dx + ib * dy
            sy = pivot[1] + ic * dx + id_ * dy
            bx = int(math.floor((sx - x0 + 0.5) * S))
            by = int(math.floor((sy - y0 + 0.5) * S))
            if 0 <= bx < w * S and 0 <= by < h * S:
                k = big[by][bx]
                if k != '.':
                    out[(ox, oy)] = k
    return out


def affine_pt(p, M, pivot, to):
    a, b, c, d = M
    u, v = p[0] - pivot[0], p[1] - pivot[1]
    return (a * u + b * v + to[0], c * u + d * v + to[1])


def turn_squash(deg, sx=1.0, sy=1.0):
    """The matrix for a turn of deg (screen, clockwise positive) followed by a squash in the frame
    (sx across, sy down): how a body flattens against the mat whatever way it is lying."""
    t = math.radians(deg)
    ct, st = math.cos(t), math.sin(t)
    return (sx * ct, -sx * st, sy * st, sy * ct)


def affine_with_features(px, M, pivot, to, features, turns=0):
    """affine() keeping small features crisp: lifted off, the rest transformed, then put back at
    their transformed centres, themselves only turned by `turns` quarter turns (never squashed)."""
    base = dict(px)
    lifted = []
    for feat, fill in features:
        if not feat:
            continue
        for q in feat:
            base[q] = fill
        cx = sum(q[0] for q in feat) / len(feat)
        cy = sum(q[1] for q in feat) / len(feat)
        lifted.append((feat, cx, cy))
    out = affine(base, M, pivot, to)
    for feat, cx, cy in lifted:
        rel = turn_patch({(q[0] - cx, q[1] - cy): k for q, k in feat.items()}, turns)
        nx, ny = affine_pt((cx, cy), M, pivot, to)
        for (u, v), k in rel.items():
            q = (int(math.floor(nx + u + 0.5)), int(math.floor(ny + v + 0.5)))
            if q in out:
                out[q] = k
    return out


def turn_patch(patch, turns):
    """A feature patch {(dx, dy): key} about its own centre, by quarter turns."""
    out = {}
    for (x, y), k in patch.items():
        u, v = x, y
        for _ in range(turns % 4):
            u, v = -v, u
        out[(u, v)] = k
    return out


def rotate_with_features(px, deg, pivot, to, features):
    """Rotate a key map by any angle with RotSprite, keeping small features crisp. `features` is a
    list of (pixels {q: key}, fill key): each feature is lifted off (its pixels take the fill key),
    the rest is rotated, and the feature goes back on at its rotated centre, itself turned by the
    nearest quarter turn."""
    base = dict(px)
    lifted = []
    for feat, fill in features:
        if not feat:
            continue
        for q in feat:
            base[q] = fill
        cx = sum(q[0] for q in feat) / len(feat)
        cy = sum(q[1] for q in feat) / len(feat)
        lifted.append((feat, cx, cy))
    out = rotsprite(base, deg, pivot, to)
    turns = int(round(deg / 90.0))
    for feat, cx, cy in lifted:
        rel = {(q[0] - cx, q[1] - cy): k for q, k in feat.items()}
        rel = turn_patch(rel, turns)
        nx, ny = rot_pt((cx, cy), deg, pivot, to)
        for (u, v), k in rel.items():
            q = (int(math.floor(nx + u + 0.5)), int(math.floor(ny + v + 0.5)))
            if q in out:
                out[q] = k
    return out


# ------------------------------------------------------------------ CLEAN-UP
def rekeyline(px, key='k'):
    """After a RotSprite turn: keyline pixels that no longer touch the inside go, and every fill
    pixel left on the silhouette edge gets a keyline outside it (ground_kit.rekeyline)."""
    body = {q for q, k in px.items() if k != key}
    out = {q: k for q, k in px.items() if k != key}
    for q, k in px.items():
        if k == key:
            x, y = q
            touches = any((x + dx, y + dy) in body for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            outside = any((x + dx, y + dy) not in px for dx, dy in N4)
            if touches or not outside:
                out[q] = key
    for (x, y) in list(body):
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in out:
                out[q] = key
    return out


def seal(px, fill_keys, key='k'):
    """Keyline any body pixel left touching transparency."""
    add = []
    for (x, y), k in px.items():
        if k not in fill_keys:
            continue
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in px:
                add.append(q)
    for q in add:
        px[q] = key
    return px


def pinholes(px):
    """Transparent pixels with all four neighbours drawn."""
    out = []
    seen = set()
    for (x, y) in px:
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q in px or q in seen:
                continue
            seen.add(q)
            if all((q[0] + ex, q[1] + ey) in px for ex, ey in N4):
                out.append(q)
    return out


def orphans(px, keys=None):
    """Drawn pixels with no drawn 8-neighbour (a lone speck)."""
    out = []
    for (x, y), k in px.items():
        if keys is not None and k not in keys:
            continue
        if not any((x + dx, y + dy) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            out.append((x, y))
    return out


def gaps(px, fill_keys):
    """Fill pixels touching transparency: a missing keyline."""
    return [(x, y) for (x, y), k in px.items() if k in fill_keys
            and any((x + dx, y + dy) not in px for dx, dy in N4)]


def blobs(px):
    """8-connected islands, largest first."""
    seen, out = set(), []
    for p in px:
        if p in seen:
            continue
        stack, blob = [p], []
        seen.add(p)
        while stack:
            q = stack.pop()
            blob.append(q)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    r = (q[0] + dx, q[1] + dy)
                    if r in px and r not in seen:
                        seen.add(r)
                        stack.append(r)
        out.append(blob)
    return sorted(out, key=len, reverse=True)


def bbox(pts):
    pts = list(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def shift(px, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in px.items()}


def clip(px, w, h):
    return {q: k for q, k in px.items() if 0 <= q[0] < w and 0 <= q[1] < h}


# ------------------------------------------------------------------ SMALL EFFECTS (palette keys passed in)
def line_px(x0, y0, x1, y1):
    out = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return out


def arc_px(cx, cy, r, a0, a1, ry=None):
    """The pixels of an elliptical arc from angle a0 to a1 (screen degrees, 0 = right, 90 = down)."""
    ry = r if ry is None else ry
    pts = []
    steps = max(8, int(abs(a1 - a0) * 1.6))
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((int(round(cx + r * math.cos(a))), int(round(cy + ry * math.sin(a)))))
    out = []
    for p, q in zip(pts, pts[1:]):
        for s in line_px(p[0], p[1], q[0], q[1]):
            if not out or out[-1] != s:
                out.append(s)
    return out
