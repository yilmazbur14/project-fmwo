"""A small muscle renderer. One body layer = one silhouette + one global form (its big volume) +
muscles on top that only TILT the form's normal, lit from the upper left.

Why: shading every muscle as its own outlined ellipsoid reads as a stack of balloons (the
"snowman" failure this project has rejected before). Here the global form decides where the layer
is lit (the torso as one barrel, a limb as one tube), each pixel is tilted only by the muscle it
belongs to, and every boundary between two muscles gets ONE clean separation line on the far side
of the muscle in front: black where a limb crosses the body, a dark tone of the skin for
muscle-on-muscle (the house rule, art_source/vs_card_v2/STYLE.md).

Two kinds of muscle:
  Bump    a superellipse dome (egg / teardrop / bowed shapes via taper and skew): legs, torso.
  Region  a traced polygon with a pillow profile, for shapes an ellipse can't give: the arms and
          the fists' finger segments.

Coordinates are pixel centres. Angles in degrees, 0 = +x, 90 = +y (down the screen).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gr_kit as K  # noqa: E402


class Bump:
    """A rounded muscle mass: a superellipse (exponent p; 2 = ellipse, higher = boxier) with a
    domed profile of height `amp` over a base level z0.

    cast: the separation line this muscle throws onto a muscle BEHIND it where they meet:
          'k' black, another key (e.g. '6') that fixed tone, 1 or 2 that many ramp steps darker,
          0 none.
    depth: front-to-back order for that decision (higher is in front); ties go to the light:
          the line lands on the pixel further from the upper left.
    taper: the half-width grows toward +u (the end the angle points at) by this fraction and
          shrinks toward -u, making an egg / teardrop.
    skew: the ends droop toward -v by this fraction of b, bowing the muscle like a peaked biceps."""

    def __init__(self, name, c, a, b, ang=0.0, amp=1.0, z0=0.0, p=2.0, prof=0.5, cast=1, depth=0,
                 taper=0.0, skew=0.0):
        self.name, self.c, self.a, self.b = name, c, a, b
        self.ang, self.amp, self.z0, self.p, self.prof = ang, amp, z0, p, prof
        self.cast, self.depth, self.taper, self.skew = cast, depth, taper, skew
        t = math.radians(ang)
        self.ct, self.st = math.cos(t), math.sin(t)

    def d(self, x, y):
        dx, dy = x - self.c[0], y - self.c[1]
        u = (dx * self.ct + dy * self.st) / self.a
        bw = self.b * max(0.25, 1.0 + self.taper * max(-1.0, min(1.0, u)))
        vv = (-dx * self.st + dy * self.ct) + self.skew * self.b * (u * u)
        v = vv / bw
        return (abs(u) ** self.p + abs(v) ** self.p) ** (1.0 / self.p)

    def h(self, x, y):
        d = self.d(x, y)
        if d >= 1.0:
            return None
        return self.z0 + self.amp * (1.0 - d * d) ** self.prof

    def grad(self, x, y, e=0.35):
        def hh(px, py):
            v = self.h(px, py)
            return self.z0 if v is None else v
        return ((hh(x + e, y) - hh(x - e, y)) / (2 * e), (hh(x, y + e) - hh(x, y - e)) / (2 * e))

    def mirrored(self):
        # mirroring flips the sense of v, so the skew changes sign; the taper runs along u and
        # keeps its sign
        return Bump(self.name + "'", (K.AX - self.c[0], self.c[1]), self.a, self.b, 180.0 - self.ang,
                    self.amp, self.z0, self.p, self.prof, self.cast, self.depth, self.taper,
                    -self.skew)


class Form:
    """A layer's big volume: an ellipsoid (cx, cy, rx, ry) or, with `axis`, a tube from p0 to p1
    of radius r. Returns the unit normal at a pixel."""

    def __init__(self, ellipsoid=None, axis=None, r=None, flat=1.0):
        self.ell, self.axis, self.r, self.flat = ellipsoid, axis, r, flat

    def normal(self, x, y):
        if self.axis is not None:
            (x0, y0), (x1, y1) = self.axis
            ax, ay = x1 - x0, y1 - y0
            al = math.hypot(ax, ay) or 1.0
            ax, ay = ax / al, ay / al
            nx, ny = -ay, ax
            s = ((x - x0) * nx + (y - y0) * ny) / self.r
            s = max(-0.97, min(0.97, s))
            z = math.sqrt(1.0 - s * s) * self.flat
            return (s * nx, s * ny, z)
        cx, cy, rx, ry = self.ell
        u, v = (x - cx) / rx, (y - cy) / ry
        r2 = u * u + v * v
        if r2 > 0.94:
            s = math.sqrt(0.94 / r2)
            u, v, r2 = u * s, v * s, 0.94
        return (u, v, math.sqrt(1.0 - r2) * self.flat)


class Layer:
    """pixels: the silhouette (a set). bumps: the muscles. Anything inside the silhouette but in
    no bump belongs to the floor (owner None) at height `floor`."""

    def __init__(self, pixels, form, bumps, floor=0.0, strength=1.0):
        self.pixels, self.form, self.bumps = set(pixels), form, bumps
        self.floor, self.strength = floor, strength

    def owners(self):
        """Each pixel's muscle: the highest bump there (hard max), None for the floor."""
        own = {}
        for (x, y) in self.pixels:
            best, ob = self.floor, None
            for b in self.bumps:
                v = b.h(x, y)
                if v is not None and v > best:
                    best, ob = v, b
            own[(x, y)] = ob
        return own

    def shade_owned(self, ramp='12345', cuts=(0.84, 0.60, 0.30, 0.02), floor_cast=0, lines=True):
        """-> (part, owners). Every pixel is lit by the global form tilted by ITS OWN muscle's
        slope (no blending across a boundary, so no speckle), then each boundary gets one clean
        separation line on the far side of the muscle in front."""
        own = self.owners()
        part = {}
        s = self.strength
        for (x, y) in self.pixels:
            n0 = self.form.normal(x, y)
            b = own[(x, y)]
            gx, gy = b.grad(x, y) if b is not None else (0.0, 0.0)
            n = (n0[0] - s * gx, n0[1] - s * gy, n0[2])
            part[(x, y)] = K.tone(K.lambert(n), ramp, cuts)
        if lines:
            separate(part, own, floor_cast)
        return part, own


def separate(part, own, floor_cast=0):
    """Draw one line on every boundary between two owners, on the pixel of the one BEHIND
    (lower depth; on a tie, the pixel further from the upper-left light), in the front one's
    `cast`. Where several lines claim a pixel the strongest wins."""
    marks = {}
    for (x, y), a in own.items():
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            q = (x + dx, y + dy)
            if q not in own:
                continue
            b = own[q]
            if b is a:
                continue
            da = a.depth if a is not None else -99
            db = b.depth if b is not None else -99
            if da > db:
                front, back_px = a, q
            elif db > da:
                front, back_px = b, (x, y)
            else:
                far = q if (dx + dy) > 0 else (x, y)
                front = a if far == q else b
                back_px = far
            cast = front.cast if front is not None else floor_cast
            if not cast:
                continue
            prev = marks.get(back_px)
            if prev is None or _strength(cast) > _strength(prev):
                marks[back_px] = cast
    for p, cast in marks.items():
        if isinstance(cast, str):
            part[p] = cast          # a fixed key: 'k' black, or a dark skin tone
        else:
            k = part[p]
            for _ in range(cast):
                k = K.DARKER[k]
            part[p] = k


def _strength(cast):
    """Which separation wins where two meet: black, then a fixed dark tone, then N steps."""
    if cast == 'k':
        return 100
    if isinstance(cast, str):
        return 50
    return cast


# ================================================================================ polygon regions

class Region:
    """A muscle drawn as a traced polygon (or any pixel set) with a PILLOW profile: flat on top,
    rounding off within `round_px` of its edge. The form lights the flat top; the rounded rim gives
    the lit edge on the upper left and the dark edge on the lower right, the way the approved
    sprites shade a muscle.

    cast / depth: as for Bump. Regions are layered by depth (later wins a tie), so a region partly
    covered by one in front keeps only its visible part. form: its own big volume, else the
    layer's."""

    def __init__(self, name, pixels, amp=1.0, round_px=2.5, cast=1, depth=0, form=None):
        self.name, self.pixels = name, set(pixels)
        self.amp, self.round_px, self.cast, self.depth = amp, round_px, cast, depth
        self.form = form


class RegionLayer:
    def __init__(self, form, regions, base=(), strength=1.0):
        self.form, self.regions, self.strength = form, regions, strength
        self.pixels = set(base)
        for r in regions:
            self.pixels |= r.pixels

    def owners(self):
        own = {p: None for p in self.pixels}
        for r in sorted(enumerate(self.regions), key=lambda ir: (ir[1].depth, ir[0])):
            for p in r[1].pixels:
                own[p] = r[1]
        return own

    @staticmethod
    def _heights(region, visible):
        """Pillow height over the region's VISIBLE pixels: distance to the nearest pixel outside
        them, eased."""
        R = int(math.ceil(region.round_px)) + 1
        hs = {}
        for (x, y) in visible:
            best = R + 1.0
            for dy in range(-R, R + 1):
                for dx in range(-R, R + 1):
                    if (x + dx, y + dy) not in visible:
                        d = math.hypot(dx, dy) - 0.5
                        if d < best:
                            best = d
            t = min(1.0, max(0.0, best) / region.round_px)
            hs[(x, y)] = region.amp * math.sqrt(max(0.0, 1.0 - (1.0 - t) ** 2))
        return hs

    def shade(self, ramp='12345', cuts=(0.84, 0.58, 0.30, 0.02), floor_cast=0, lines=True):
        own = self.owners()
        vis = {}
        for p, r in own.items():
            if r is not None:
                vis.setdefault(id(r), set()).add(p)
        h = {}
        for r in self.regions:
            if id(r) in vis:
                h.update(self._heights(r, vis[id(r)]))
        part = {}
        s = self.strength
        for (x, y) in self.pixels:
            r = own[(x, y)]
            if r is None:
                gx = gy = 0.0
            else:
                def hh(q):
                    return h[q] if own.get(q) is r else 0.0
                gx = (hh((x + 1, y)) - hh((x - 1, y))) / 2.0
                gy = (hh((x, y + 1)) - hh((x, y - 1))) / 2.0
            f = r.form if (r is not None and r.form is not None) else self.form
            n0 = f.normal(x, y)
            n = (n0[0] - s * gx, n0[1] - s * gy, n0[2])
            part[(x, y)] = K.tone(K.lambert(n), ramp, cuts)
        if lines:
            separate(part, own, floor_cast)
        return part, own
