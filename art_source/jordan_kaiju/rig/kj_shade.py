"""Volume shading for the kaiju: parts modelled as unions of ellipsoids and tapered capsules, each
pixel lit by the analytic normal of the primitives over it (soft-blended where they meet), from the
upper left like the cast, then quantised onto a colour ramp. No pillow shading: the light follows
the actual forms.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LIGHT = (-0.52, -0.66, 0.54)
_ln = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _ln for c in LIGHT)
HALF = (LIGHT[0], LIGHT[1], LIGHT[2] + 1.0)
_hn = math.sqrt(sum(c * c for c in HALF))
HALF = tuple(c / _hn for c in HALF)

HIDE = ['#', '%', '&', '@', '+', '=']
BELLY = ['C', 'E', 'F', 'H']
BONE = ['4', '5', '6', '7']
GLOW = ['8', 'I', 'J', 'K', 'X']
RAMPS = {'hide': HIDE, 'belly': BELLY, 'bone': BONE, 'glow': GLOW}

# lambert thresholds per ramp (len(ramp) - 1 cut points)
CUTS = {
    'hide': [0.04, 0.3, 0.54, 0.74, 1.5],
    'belly': [0.2, 0.48, 0.74],
    'bone': [0.15, 0.45, 0.75],
    'glow': [0.2, 0.45, 0.7, 0.9],
}

DARKER = {}
LIGHTER = {}
for _r in (HIDE, BELLY, BONE, GLOW):
    for i, k in enumerate(_r):
        DARKER[k] = _r[max(0, i - 1)]
        LIGHTER[k] = _r[min(len(_r) - 1, i + 1)]
DARKER['~'] = '='
LIGHTER['='] = '='


class Ell:
    """An ellipsoid seen from the front; `ang` (degrees, clockwise) turns it in the picture plane, and
    its normals turn with it, so the light stays where it is."""
    def __init__(self, cx, cy, rx, ry, z=0.0, gloss=False, ang=0.0):
        self.cx, self.cy, self.rx, self.ry, self.z, self.gloss = cx, cy, rx, ry, z, gloss
        self.ang = ang
        self._c = math.cos(math.radians(ang))
        self._s = math.sin(math.radians(ang))

    def bounds(self):
        if self.ang:
            r = max(self.rx, self.ry)
            return (int(self.cx - r) - 1, int(self.cy - r) - 1, int(self.cx + r) + 2, int(self.cy + r) + 2)
        return (int(self.cx - self.rx) - 1, int(self.cy - self.ry) - 1,
                int(self.cx + self.rx) + 2, int(self.cy + self.ry) + 2)

    def sample(self, x, y):
        if self.ang:
            ux, uy = x - self.cx, y - self.cy
            lx = ux * self._c + uy * self._s
            ly = -ux * self._s + uy * self._c
            dx, dy = lx / self.rx, ly / self.ry
        else:
            dx, dy = (x - self.cx) / self.rx, (y - self.cy) / self.ry
        d2 = dx * dx + dy * dy
        if d2 > 1.0:
            return None
        nz = math.sqrt(1.0 - d2)
        r = min(self.rx, self.ry)
        if self.ang:
            wx = dx * self._c - dy * self._s
            wy = dx * self._s + dy * self._c
            return (wx, wy, nz), nz * r + self.z
        return (dx, dy, nz), nz * r + self.z


class Cap:
    def __init__(self, p0, p1, r0, r1, z=0.0, gloss=False):
        self.p0, self.p1, self.r0, self.r1, self.z, self.gloss = p0, p1, r0, r1, z, gloss

    def bounds(self):
        r = max(self.r0, self.r1)
        xs = (self.p0[0], self.p1[0])
        ys = (self.p0[1], self.p1[1])
        return int(min(xs) - r) - 1, int(min(ys) - r) - 1, int(max(xs) + r) + 2, int(max(ys) + r) + 2

    def sample(self, x, y):
        (x0, y0), (x1, y1) = self.p0, self.p1
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, ((x - x0) * vx + (y - y0) * vy) / L2))
        cx, cy = x0 + vx * t, y0 + vy * t
        r = self.r0 + (self.r1 - self.r0) * t
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d > r:
            return None
        nz = math.sqrt(max(0.0, 1.0 - (d / r) ** 2))
        return (dx / r, dy / r, nz), nz * r + self.z


def part_pixels(prims):
    out = set()
    for p in prims:
        x0, y0, x1, y1 = p.bounds()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if p.sample(x, y) is not None:
                    out.add((x, y))
    return out


def shade(prims, ramp='hide', soft=1.6, bias=0.0, gloss_cut=0.93, flatten=1.0, bounce=0.0):
    """{pixel: key} for the union of `prims`, lit from LIGHT. `flatten` < 1 squashes the normals'
    z (a flatter, more graphic read); `bias` shifts the whole part lighter (+) or darker (-)."""
    keys = RAMPS[ramp]
    cuts = CUTS[ramp]
    out = {}
    info = {}
    for (x, y) in part_pixels(prims):
        hits = []
        for p in prims:
            s = p.sample(x, y)
            if s is not None:
                hits.append((s[1], s[0], p))
        hmax = max(h for h, _, _ in hits)
        nx = ny = nz = 0.0
        gl = False
        for h, n, p in hits:
            w = math.exp((h - hmax) / soft)
            nx += n[0] * w
            ny += n[1] * w
            nz += n[2] * w * flatten
            if p.gloss and h == hmax:
                gl = True
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        n = (nx / ln, ny / ln, nz / ln)
        lam = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2] + bias
        if bounce and n[1] > 0.55:
            lam += bounce * (n[1] - 0.55) / 0.45          # light bounced up off the mat
        idx = sum(1 for c in cuts if lam >= c)
        k = keys[idx]
        spec = n[0] * HALF[0] + n[1] * HALF[1] + n[2] * HALF[2]
        if gl and ramp == 'hide' and spec >= gloss_cut:
            k = '~'
        out[(x, y)] = k
        info[(x, y)] = (lam, n, hmax)
    return out, info


def shade_clip(prims, clip, ramp='hide', fallback=None, strict=False, **kw):
    """Shade the pixels of `clip` (a pixel set: a traced silhouette) with the normals of `prims`;
    pixels no primitive covers take `fallback`'s normal (a big soft primitive round the whole part)."""
    allp = list(prims) + ([fallback] if fallback else [])
    part, info = shade(allp, ramp, **kw)
    out = {q: k for q, k in part.items() if q in clip}
    inf = {q: v for q, v in info.items() if q in clip}
    missing = [q for q in clip if q not in out]
    if missing and strict:
        raise ValueError('%d clip pixels have no normal (first %s)' % (len(missing), missing[:3]))
    for q in missing:                      # (only under a squashed turn) borrow the nearest shaded pixel
        best = None
        for r in range(1, 6):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    n = (q[0] + dx, q[1] + dy)
                    if n in out and n not in missing:
                        best = n
                        break
                if best:
                    break
            if best:
                break
        out[q] = out[best] if best else keys_default(ramp)
        inf[q] = inf[best] if best else (0.5, (0.0, 0.0, 1.0), 0.0)
    return out, inf


def keys_default(ramp):
    return RAMPS[ramp][len(RAMPS[ramp]) // 2]


def rim_light(part, depth=1, keys=('#', '%', '&', '@', '+')):
    """The crisp lit rim of pixel art: the part's pixels on its upper-left edge (open to the up-left)
    step one tone up the ramp."""
    hits = []
    for (x, y), k in part.items():
        if k not in keys:
            continue
        if any((x - d, y) not in part or (x, y - d) not in part for d in range(1, depth + 1)):
            if (x - 1, y) not in part and (x, y - 1) not in part:
                hits.append(((x, y), 2))
            else:
                hits.append(((x, y), 1))
    for q, n in hits:
        k = part[q]
        for _ in range(n):
            k = LIGHTER.get(k, k)
        part[q] = k
