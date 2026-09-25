"""The ground of a quake-ring segment: a straight stretch of the hurt band, broken into heaved chunks along a
hellfire crack, modelled on the floor and ray-marched the way the arena draws the floor.

Coordinates: t runs along the band (floor texels), v across it (floor texels, + toward the camera, or to the
right up the sides), z is height in screen texels. A floor point lands on screen at (x, 0.36 y - z) where
(x, y) = t * u + v * n: floor y is squashed by FLOOR_FLATTEN, height is not. The band is BAND (12) texels of
floor either side of the crack, the hurt band's 36 px.

The band is broken into chunks: a Voronoi pattern of seeds on each side of the crack, periodic along the band
with the row's period. Each chunk is a tilted block. The chunks along the crack are heaved: behind it they
are thrust up so their broken faces show, lit by the magma; in front they drop into it (or bridge it) so the
magma shows past them; up the sides, where neither is behind the other, both rise.

Seams: the whole ring is modelled, not just the segment. A segment draws its own stretch of the crack and
the chunks that reach into its stretch (clipped a little past the overlap); everything else stops the rays
exactly as on the continuous ring but stays clear, for the neighbour to fill. So two segments of a row laid
at the row's period composite into exactly the continuous ring, whichever is drawn on top, and the sampling
divides the period so that holds to the texel (tiletest.py).
"""
import math
import random

import numpy as np

K = 0.36
BAND = 12.0          # hurt band half-width, floor texels
MAGMA_Z = -0.9       # the magma's surface, screen texels below the floor
CRACK_W = 1.7        # the crack's half-width at a seam, floor texels
RES = 0.1            # heightfield grid, floor texels

# Materials
CLEAR, EARTH, CHUNK, MAGMA, UNOWNED = 0, 1, 2, 3, 4


class Ground:
    def __init__(self, index, period, seeds, stretch, overlap=3.5, allow=2.5, seed=0):
        """period: the row's screen period (dx, dy); seeds: chunks per side per period; stretch: how much
        longer than wide chunks are along the band; overlap: how far past each end of its period (screen
        texels) a segment draws the crack; allow: how much further its chunks may reach before they're cut."""
        dx, dy = period
        self.index = index
        fx, fy = dx, dy / K
        self.lt = math.hypot(fx, fy)
        self.ls = math.hypot(dx, dy)
        self.u = (fx / self.lt, fy / self.lt)
        self.n = (-self.u[1], self.u[0])
        self.alpha = math.atan2(-fy, fx)
        self.ca = math.cos(self.alpha)
        self.to_floor = self.lt / self.ls
        self.m_t = overlap * self.to_floor
        self.still_t = self.m_t + 0.5 * self.to_floor     # the magma holds still this close to a seam
        self.stretch = stretch
        self.allow = allow * self.to_floor
        # sampling that divides the period exactly, so a period along the band renders the same texels: the
        # heightfield grid divides the period's length, the ray's depth step divides its floor-depth offset
        self.res = self.lt / round(self.lt / RES)
        self.fy_period = abs(dy) / K
        self.step = self.fy_period / round(self.fy_period / 0.025) if dy else 0.025
        # screen texels across the band per floor texel of v (0.36 broadside, 1 up the sides)
        self.sv = K / math.sqrt((K * math.sin(self.alpha)) ** 2 + math.cos(self.alpha) ** 2)
        self.rnd = random.Random(7000 + 97 * index + seed)
        self._crack_fns()
        self._seeds(seeds)
        self._build()

    # ------------------------------------------------------------------ layout

    def _periodic(self, terms):
        waves = [(amp, k, self.rnd.uniform(0, 2 * math.pi)) for amp, k in terms]
        lt = self.lt

        def f(t):
            s = np.zeros_like(t, dtype=float)
            for amp, k, ph in waves:
                s = s + amp * np.sin(2 * math.pi * k * t / lt + ph)
            return s
        return f

    def window(self, t):
        tm = np.mod(t + self.lt / 2, self.lt)
        d = np.minimum(tm, self.lt - tm) / (0.22 * self.lt)
        return np.clip(d, 0.0, 1.0)

    def _crack_fns(self):
        # the crack meanders and breathes, but is straight and standard at the seams (window 0 there)
        # sized on screen, so the zigzag reads the same broadside (where floor v is squashed) as up the sides
        zig = 1.25 / self.sv
        self.meander = self._periodic([(0.55 * zig, 1), (0.3 * zig, 2), (0.22 * zig, 3), (0.14 * zig, 5)])
        self.breathe = self._periodic([(0.45, 2), (0.35, 3), (0.25, 5)])
        rag = min(2.2, 0.55 / self.sv)
        self.rag = self._periodic([(0.45 * rag, 2), (0.35 * rag, 3), (0.3 * rag, 5), (0.2 * rag, 7)])
        # how hot the magma runs along the crack: hot spots and cooler stretches, even at the seams, and
        # each stretch pulsing on its own phase through the four-frame loop
        self.hot = self._periodic([(0.5, 1), (0.4, 2), (0.3, 3)])
        self.pulse_phase = self._periodic([(1.0, 1), (0.7, 2), (0.5, 3)])
        # where a chunk reaching past the overlap is cut, wiggling across the band like a crack
        self.seam_rnd = [(self.rnd.uniform(0.15, 0.35), self.rnd.uniform(0, 6.3)) for _ in range(2)]

    def _seeds(self, per_side):
        """Voronoi seeds (t, d, kind) per side; d is distance from the crack line. The first ranks sit on
        the crack's edge (lip chunks), the rest fill out to the band's edge."""
        rnd = self.rnd
        lt = self.lt
        self.seeds = {}
        for side in (-1, 1):
            pts = []
            lips = max(2, per_side // 2)
            for j in range(lips):
                t = -lt / 2 + lt * (j + 0.5) / lips + rnd.uniform(-0.15, 0.15) * lt / lips
                pts.append([t, CRACK_W + rnd.uniform(1.6, 2.6), 'lip'])
            rest = per_side - lips
            for j in range(rest):
                t = -lt / 2 + lt * (j + rnd.uniform(0.15, 0.85)) / rest
                pts.append([t, rnd.uniform(5.5, 11.0), 'field'])
            self.seeds[side] = pts
        # a height plane per seed: z = z0 + gd * (d - d0) + gt * (t - t0)
        self.planes = {}
        for side in (-1, 1):
            planes = []
            for k, (t0, d0, kind) in enumerate(self.seeds[side]):
                if kind == 'lip':
                    tall = k % 2 == 0
                    behind = rnd.uniform(1.8, 2.6) if tall else rnd.uniform(0.7, 1.3)   # thrust up
                    front = rnd.uniform(-0.9, 1.3)                                       # dropped in, or bridging it
                    sym = rnd.uniform(1.6, 2.4) if tall else rnd.uniform(0.8, 1.4)      # up the sides
                    h = (behind if side < 0 else front)
                    h = sym + (h - sym) * self.ca
                    gd = -h / 6.5 if h > 0 else -h / 8.0
                    z0 = h + gd * (d0 - CRACK_W)
                    gt = rnd.uniform(-0.15, 0.15)
                else:
                    z0 = rnd.uniform(0.4, 1.9)
                    gd = rnd.uniform(-0.18, 0.12)
                    gt = rnd.uniform(-0.2, 0.2)
                planes.append((z0, gd, gt))
            self.planes[side] = planes

    # ------------------------------------------------------------------ heightfield

    def _build(self):
        lt, m = self.lt, self.m_t
        # the band modelled as far along as any ray of the canvas can reach, so rays near a segment's ends meet
        # the neighbours' ground (as occluders) exactly as on the continuous ring
        span = (lt / 2 + m) * abs(self.u[1]) + (BAND + 2) * abs(self.n[1]) + 16
        reach = 40 * abs(self.u[0]) + span * abs(self.u[1]) + 2.0
        pad = max(12.0, reach - lt / 2 - m)
        self.t0 = -lt / 2 - m - pad
        self.v0 = -BAND - 2.0
        nt = int(math.ceil((lt + 2 * m + 2 * pad) / self.res)) + 1
        nv = int(math.ceil((2 * BAND + 4.0) / RES)) + 1
        t = self.t0 + np.arange(nt) * self.res
        v = self.v0 + np.arange(nv) * RES
        T, V = np.meshgrid(t, v, indexing='ij')           # (nt, nv)
        w = self.window(T)
        cv = self.meander(T) * w
        cw = CRACK_W + self.breathe(T) * w
        dv = V - cv
        d = np.abs(dv)
        side = np.where(dv < 0, -1, 1)
        edge = BAND + (self.rag(T) - 0.3) * w
        self.T = T
        in_band = d <= edge
        in_crack = in_band & (d < cw)

        z = np.zeros(T.shape)
        cid = np.full(T.shape, -1)
        gapw = np.full(T.shape, 99.0)
        owned = np.zeros(T.shape, dtype=bool)
        for s in (-1, 1):
            pts = self.seeds[s]
            best = np.full(T.shape, 1e9)
            second = np.full(T.shape, 1e9)
            bid = np.full(T.shape, -1)
            bwrap = np.zeros(T.shape)
            # seeds of this period and its neighbours (the pattern repeats every lt)
            for j, (st, sd, kind) in enumerate(pts):
                for wrap in (-2 * lt, -lt, 0.0, lt, 2 * lt):
                    ddist = np.sqrt(((T - st - wrap) / self.stretch) ** 2 + (d - sd) ** 2)
                    closer = ddist < best
                    second = np.where(closer, best, np.minimum(second, ddist))
                    best = np.where(closer, ddist, best)
                    bid = np.where(closer, j, bid)
                    bwrap = np.where(closer, wrap + st, bwrap)
            sel = side == s
            zs = np.zeros(T.shape)
            for j, (z0, gd, gt) in enumerate(self.planes[s]):
                st, sd, kind = pts[j]
                zs = np.where(bid == j, z0 + gd * (d - sd) + gt * (T - bwrap), zs)
            z = np.where(sel, zs, z)
            cid = np.where(sel, bid + (0 if s < 0 else 100), cid)
            gapw = np.where(sel, second - best, gapw)
            # whole chunks: every chunk (this copy of its seed) that reaches into the period, or within the
            # allowance of it, so a segment's own stretch of the band is always complete
            key = bid * 100000 + np.rint(bwrap * 100).astype(int)
            touch = sel & in_band & (np.abs(T) <= lt / 2 + self.allow)
            own = np.isin(key, np.unique(key[touch]))
            owned = np.where(sel, own, owned)
        # The whole band is modelled, a segment's neighbours' ground included, so every ray stops where it
        # would on the continuous ring; what the segment doesn't draw itself (chunks it doesn't own, the
        # crack past its reach) stops the ray but stays clear, for the neighbour to fill. Two segments laid
        # at the period therefore composite into exactly the continuous ring, whichever is drawn on top.
        own_crack = in_crack & (np.abs(T) <= lt / 2 + m)
        # and no further than the overlap: a chunk reaching past it reaches into the neighbour's stretch too,
        # so the neighbour draws the rest of it; the cut wiggles across the band like a crack
        wig = sum(a * np.sin(0.55 * (k + 1) * d + ph) for k, (a, ph) in enumerate(self.seam_rnd)) * 2.5
        owned = owned & (np.abs(T) + wig * np.sign(T) <= lt / 2 + m + self.allow)
        in_chunks = in_band & ~in_crack
        in_gap = in_chunks & (gapw < 0.85)
        z = np.where(in_chunks, z, 0.0)
        z = np.where(in_gap, np.minimum(z, 0.0) - 0.5, z)
        z = np.where(in_crack, MAGMA_Z, z)
        mat = np.where(in_chunks, CHUNK, CLEAR)
        mat = np.where(in_gap, EARTH, mat)
        mat = np.where(in_crack, MAGMA, mat)
        self.UNDER = mat.copy()                           # what an UNOWNED texel is underneath
        mat = np.where((in_chunks & ~owned) | (in_crack & ~own_crack), UNOWNED, mat)
        self.Z, self.MAT, self.CID = z, mat, cid
        self.D, self.CW, self.SIDE = d, cw, side
        self.nt, self.nv = nt, nv

    def heat(self, t, frame=None):
        """The magma's heat along the crack: 0.1 (cool) .. 1 (white-hot), 0.55 at the seams. With a frame, the
        magma surface's pulse on that frame; it lives only in this segment's own stretch of the crack, further
        than the overlap from either seam, which is magma no neighbour draws. Without one (the lit faces
        either side of the crack), it holds still."""
        w = self.window(t)
        pulse = 0.0
        if frame is not None:
            live = np.clip((self.lt / 2 - self.still_t - np.abs(t)) / (0.12 * self.lt), 0.0, 1.0)
            pulse = 0.45 * np.sin(2 * math.pi * frame / 4.0 + 2.2 * self.pulse_phase(t)) * live
        return 0.55 + 0.45 * np.clip(self.hot(t) / 0.7 + pulse, -1, 1) * w

    def lookup(self, t, v):
        it = np.clip(np.rint((t - self.t0) / self.res).astype(int), 0, self.nt - 1)
        iv = np.clip(np.rint((v - self.v0) / RES).astype(int), 0, self.nv - 1)
        outside = (t < self.t0) | (t > self.t0 + (self.nt - 1) * self.res) | (v < self.v0) | (v > self.v0 + (self.nv - 1) * RES)
        z = np.where(outside, 0.0, self.Z[it, iv])
        mat = np.where(outside, CLEAR, self.MAT[it, iv])
        return z, mat, it, iv

    # ------------------------------------------------------------------ projection and marching

    def to_screen(self, t, v, z=0.0):
        fx = t * self.u[0] + v * self.n[0]
        fy = t * self.u[1] + v * self.n[1]
        return fx, K * fy - z

    def march(self, cw_, ch_, px, py):
        """For each texel of a cw_ x ch_ canvas with the pivot at texel corner (px, py): what its ray
        meets first. Returns dict of arrays: mat, wall, z, y (floor depth), it, iv (grid cell)."""
        X, Y = np.meshgrid(np.arange(cw_) + 0.5 - px, np.arange(ch_) + 0.5 - py)
        span = (self.lt / 2 + self.m_t) * abs(self.u[1]) + (BAND + 2) * abs(self.n[1]) + 16
        done = np.zeros(X.shape, dtype=bool)
        out = {'mat': np.zeros(X.shape, dtype=int), 'wall': np.zeros(X.shape, dtype=bool),
               'z': np.zeros(X.shape), 'y': np.zeros(X.shape),
               'it': np.zeros(X.shape, dtype=int), 'iv': np.zeros(X.shape, dtype=int)}
        k = int(math.ceil(span / self.step))
        for y in self.step * np.arange(k, -k - 1, -1):
            t = X * self.u[0] + y * self.u[1]
            v = X * self.n[0] + y * self.n[1]
            zr = K * y - Y
            gz, mat, it, iv = self.lookup(t, v)
            new = (zr <= gz) & ~done
            if not new.any():
                continue
            out['mat'] = np.where(new, mat, out['mat'])
            out['wall'] = np.where(new, gz - zr > 0.12, out['wall'])
            out['z'] = np.where(new, np.minimum(zr, gz), out['z'])
            out['y'] = np.where(new, y, out['y'])
            out['it'] = np.where(new, it, out['it'])
            out['iv'] = np.where(new, iv, out['iv'])
            done |= new
        return out
