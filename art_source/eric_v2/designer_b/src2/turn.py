"""Turned body views of the Eric redesign (96-space), rendered from simple 3D primitives with the same
ramps, light, thresholds and outline rules as parts.py. Small details are wrapped from the approved front layers.

yaw 0 = front, 90 = profile facing screen-right, 180 = back; side=-1 mirrors (facing screen-left).
Body-local: X = front x - 48, Y = height (screen y at depth 0), Z = toward camera in the front view.
screen x = 48 + side*(X cos + Z sin);  d = -X sin + Z cos (toward camera);  screen y = Y + KAPPA*d
(KAPPA reproduces the slight top-down tilt baked into the approved belt / fauld curvature)."""
import math
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT, TH_CLOTH, hexc, RAMPS

KAPPA = 0.27
N = 96


def interp(table, y):
    if y <= table[0][0]:
        return table[0][1]
    for (y0, v0), (y1, v1) in zip(table, table[1:]):
        if y0 <= y <= y1:
            return v0 + (v1 - v0) * (y - y0) / (y1 - y0)
    return table[-1][1]


def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


class Samples:
    """z-buffered splat of surface samples for one part"""

    def __init__(self):
        self.buf = {}

    def add(self, x, y, d, n, tex=None, tone=0):
        px, py = int(math.floor(x)), int(math.floor(y))
        if not (0 <= px < N and 0 <= py < N):
            return
        cur = self.buf.get((px, py))
        if cur is None or d > cur[0]:
            self.buf[(px, py)] = (d, n, tex, tone)

    def mask(self):
        m = [[False] * N for _ in range(N)]
        for (x, y) in self.buf:
            m[y][x] = True
        return m


class View:
    def __init__(self, yaw, side=1):
        self.yaw = yaw
        self.side = side
        self.c = math.cos(math.radians(yaw))
        self.s = math.sin(math.radians(yaw))

    def proj(self, X, Y, Z, kappa=None):
        d = -X * self.s + Z * self.c
        k = KAPPA if kappa is None else kappa
        return 48 + self.side * (X * self.c + Z * self.s), Y + k * d, d

    def nproj(self, n):
        nX, nY, nZ = n
        return (self.side * (nX * self.c + nZ * self.s), nY, -nX * self.s + nZ * self.c)


# ------------------------------------------------------------------ rendering a sampled part
def render_part(cv, smp, ramp, th, bias=0, outline=True, tex_layer=None, tex_filter=None, cleanup=True,
                back_bias=0):
    buf = smp.buf
    rp = [hexc(c) for c in RAMPS[ramp]]
    idx = {}
    for (x, y), (d, n, tex, tone) in buf.items():
        if n[2] < 0:            # inside of a sheet seen from behind: flip toward camera, darker
            n = (-n[0], -n[1], -n[2])
            tone = tone + back_bias
        I = lib.intensity(n)
        k = len(th)
        for i, t in enumerate(th):
            if I >= t:
                k = i
                break
        idx[(x, y)] = max(0, min(len(rp) - 1, k + bias + tone))
    if cleanup:
        for _ in range(2):
            chg = []
            for (x, y), v in idx.items():
                nb = [idx[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in idx]
                if len(nb) >= 3 and v not in nb:
                    chg.append(((x, y), max(set(nb), key=nb.count)))
            for q, v in chg:
                idx[q] = v
    for (x, y), v in idx.items():
        cv.px[y][x] = rp[v]
    m = smp.mask()
    if tex_layer is not None:
        for (x, y), (d, n, tex, tone) in buf.items():
            if tex is None:
                continue
            tx, ty = int(math.floor(tex[0])), int(math.floor(tex[1]))
            if 0 <= tx < N and 0 <= ty < N:
                p = tex_layer[ty][tx]
                if p is not None and (tex_filter is None or tex_filter(p, tx, ty)):
                    cv.px[y][x] = p
    if outline:
        for (x, y) in buf:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in buf:
                    cv.px[y][x] = BLACK
                    break
    return m


# ------------------------------------------------------------------ primitives
TORSO_W = [(33, 9), (34, 9), (37, 17), (42, 22), (49, 25.5), (56, 27), (61.5, 26.7), (65.8, 24.8), (69.2, 20.7),
           (71.4, 14), (72.4, 7), (72.7, 0.5)]
ZF, ZB = 0.82, 0.72


def torso_samples(V, step=0.22):
    smp = Samples()
    y = 33.0
    while y <= 72.7:
        w = interp(TORSO_W, y)
        dw = (interp(TORSO_W, y + 0.5) - interp(TORSO_W, y - 0.5))
        nt = max(24, int(2 * math.pi * w / step))
        for i in range(nt):
            t = 2 * math.pi * i / nt
            ct, st = math.cos(t), math.sin(t)
            z = w * (ZF if st > 0 else ZB)
            X, Z = w * ct, z * st
            n = norm((z * ct, -dw * max(w, 1) * 0.9, w * st))
            # silhouette rows in the front art are at depth 0; front-surface texture sits lower by KAPPA*Z
            Yb = y
            x, ys, d = V.proj(X, Yb, Z)
            tex = (48 + X, y + KAPPA * Z) if st > 0 else None
            smp.add(x, ys, d, V.nproj(n), tex)
        y += step
    return smp


def ellipsoid_samples(V, cx, cy, cz, rx, ry, rz, roll=0.0, step=0.35, tex=True, front_only_tex=True, kappa=None,
                      rim_axis=None):
    smp = Samples()
    rr = math.radians(roll)
    cr, sr = math.cos(rr), math.sin(rr)
    nu = max(16, int(math.pi * max(rx, ry) / step))
    nv = max(24, int(2 * math.pi * max(rx, rz) / step))
    for i in range(nu + 1):
        u = math.pi * i / nu - math.pi / 2          # latitude
        for j in range(nv):
            v = 2 * math.pi * j / nv
            ex, ey, ez = rx * math.cos(u) * math.cos(v), ry * math.sin(u), rz * math.cos(u) * math.sin(v)
            # roll in the X-Y plane
            X = cx + ex * cr - ey * sr
            Y = cy + ex * sr + ey * cr
            Z = cz + ez
            nx, ny, nz = ex / (rx * rx), ey / (ry * ry), ez / (rz * rz)
            n = norm((nx * cr - ny * sr, nx * sr + ny * cr, nz))
            x, ys, d = V.proj(X, Y, Z, kappa)
            kk = KAPPA if kappa is None else kappa
            t = (48 + X, Y + kk * Z) if (tex and (Z - cz) > 0) else None
            tone = 0
            if rim_axis is not None:
                ux, uy, uz = ex / rx, ey / ry, ez / rz
                cth = ux * rim_axis[0] + uy * rim_axis[1] + uz * rim_axis[2]
                if cth > 0 and uy > 0.12:
                    sth = math.sqrt(max(0.0, 1 - cth * cth))
                    if 0.70 <= sth < 0.80:
                        tone = 1
                    elif 0.80 <= sth < 0.92:
                        tone = -1
            smp.add(x, ys, d, V.nproj(n), t, tone)
    return smp


CAPE_W = [(39, 17), (45, 31), (56, 36.5), (68, 39.5), (80, 41.5), (90, 43), (97, 43.5)]


def cape_zc(y):
    tb = interp(TORSO_W, min(y, 60)) * ZB + 3
    if y > 60:
        tb = tb + (y - 60) * 0.35
    return tb


def cape_hem(t, teeth=9):
    # zigzag hem between ~90 and ~95.5
    f = (t / math.pi) * teeth
    frac = f - math.floor(f)
    tri = abs(frac - 0.5) * 2
    k = int(math.floor(f))
    amp = 5.0 if k % 2 == 0 else 3.5
    return 90.3 + amp * (1 - tri)


def cape_samples(V, step=0.3, t0=-0.12, t1=math.pi + 0.12):
    smp = Samples()
    y = 38.5
    while y <= 96:
        wc = interp(CAPE_W, y)
        zc = cape_zc(y)
        nt = max(20, int((t1 - t0) * wc / step))
        for i in range(nt + 1):
            t = t0 + (t1 - t0) * i / nt
            if y > cape_hem(t):
                continue
            ct, st = math.cos(t), math.sin(t)
            X, Z = wc * ct, -zc * st
            n = norm((zc * ct, -0.25, -wc * st))
            x, ys, d = V.proj(X, y, Z)
            # fold lines at fixed parameters
            tone = 0
            for tf in (0.28, 0.62, 1.25, 1.9, 2.52, 2.86):
                if abs(t - tf) * wc < 0.55 and y > 58:
                    tone = 2
            smp.add(x, ys, d, V.nproj(n), None, tone)
        y += step
    return smp


def ring_band_samples(V, R, Rz, y_front_top, y_front_bot, y_side_top, y_side_bot, tex=True, step=0.3):
    """belt-like band. Front-view shape: at the centre spans y_front_top..bot, at the sides y_side_top..bot."""
    smp = Samples()
    nt = int(2 * math.pi * R / step)
    for i in range(nt):
        t = 2 * math.pi * i / nt
        ct, st = math.cos(t), math.sin(t)
        X, Z = R * ct, Rz * st
        # body-local band limits: remove the KAPPA tilt of the front art
        ytop = y_side_top + (y_front_top - y_side_top) * max(0.0, st) ** 1.5 - KAPPA * max(0.0, Z) * 0
        ybot = y_side_bot + (y_front_bot - y_side_bot) * max(0.0, st) ** 1.5
        if st < 0:
            ytop, ybot = y_side_top, y_side_bot
        # convert to body-local height (front art height = local + KAPPA*Z)
        ytop_l, ybot_l = ytop - KAPPA * Z, ybot - KAPPA * Z
        yy = ytop_l
        while yy <= ybot_l:
            n = norm((Rz * ct, 0.0, R * st))
            x, ys, d = V.proj(X, yy, Z)
            tx = (48 + X, yy + KAPPA * Z) if (tex and st > 0) else None
            smp.add(x, ys, d, V.nproj(n), tx)
            yy += step
    return smp


def plate_from_layer(V, layer, R=27.0, Rz=25.0, flat_z=None, step=0.34):
    """re-project the opaque pixels of an approved front layer that lie on a hip ring (tassets, straps, flap)"""
    smp = Samples()
    ys = [y for y in range(N) for x in range(N) if layer[y][x] is not None]
    xs = [x for y in range(N) for x in range(N) if layer[y][x] is not None]
    if not ys:
        return smp
    y = min(ys)
    while y <= max(ys) + 1:
        x = min(xs)
        while x <= max(xs) + 1:
            ix, iy = int(math.floor(x)), int(math.floor(y))
            if 0 <= ix < N and 0 <= iy < N and layer[iy][ix] is not None:
                X = x - 48
                if flat_z is not None:
                    Z = flat_z
                    n = (0.0, 0.0, 1.0)
                else:
                    Z = Rz * math.sqrt(max(0.0, 1 - (X / R) ** 2))
                    n = norm((X / (R * R), 0.0, Z / (Rz * Rz)))
                Yl = y - KAPPA * Z
                px, py, d = V.proj(X, Yl, Z)
                smp.add(px, py, d, V.nproj(n), (x, y))
            x += step
        y += step
    return smp



def tasset_wrap_samples(V, layer, R=26.0, Rz=18.0, step=0.34, wrap=78.0):
    """tassets hang on the hip ring: front-view |X| 0..25 wraps from the front (t=90) toward the side
    (t = 90 +- wrap) so that turned views see a real plate over the thigh."""
    smp = Samples()
    ys = [y for y in range(N) for x in range(N) if layer[y][x] is not None]
    xs = [x for y in range(N) for x in range(N) if layer[y][x] is not None]
    if not ys:
        return smp
    y = min(ys)
    while y <= max(ys) + 1:
        x = min(xs)
        while x <= max(xs) + 1:
            ix, iy = int(math.floor(x)), int(math.floor(y))
            if 0 <= ix < N and 0 <= iy < N and layer[iy][ix] is not None:
                Xf = x - 48
                t = math.radians(90.0 - wrap * max(-1.0, min(1.0, Xf / 25.0)))
                X, Z = R * math.cos(t), Rz * math.sin(t)
                n = norm((math.cos(t) / R, -0.02, math.sin(t) / Rz))
                Yl = y - KAPPA * 9.0
                px, py, d = V.proj(X, Yl, Z)
                smp.add(px, py, d, V.nproj(n), (x, y))
            x += step
        y += step
    return smp
