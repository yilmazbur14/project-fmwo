"""Fire, smoke and vapour, the house way, for Liam's attacks 3-4 (v3: "see and feel the elements").

FIRE follows Bixby's approved fire (bixby_fire_trail / bixby_inferno_edge / bixby_quake_burst): tongues with a
dark-maroon rim (zeta), then red-orange (delta), orange (gamma), yellow (beta), pale (alpha) and a white-hot
core, and sharp tips. What is new is that it LIVES AT ITS EDGES: the tips neck, tear off, and the torn piece
cools on the way up (a small outlined flame, then a red blob, then a dark ember) and goes out, sometimes as a
curl of smoke.

The engine is metaball particles. Each tongue emits blobs at its base on a fixed clock; a blob rises
(accelerating), sways, shrinks and cools with age, so the top of a tongue necks and tears off by itself.
Everything is a function of the loop time t in [0, 1), so every animation made from it loops seamlessly.

PUFFS (steam and smoke) are shaded clusters that dissolve from the edge inwards (hash-noise erosion that
moves with the puff), not a checkerboard.
"""
import math

import numpy as np

import le_rig as R
import le_a34 as A          # registers the fire / rock / steam / fog / tell keys in R.PAL

RIM = 'ζ'
BANDS = 'δγβαW'             # cool -> white-hot, inside the rim
# smoke is translucent (it drifts over what it passes): dense, mid, thin, wisp
SMOKE = {'ϑ': (86, 90, 102, 225), 'ϒ': (104, 110, 122, 185), 'ϖ': (132, 138, 150, 140), 'ϡ': (160, 166, 176, 100)}
R.PAL.update(SMOKE)
SMOKE_LIGHT = ('w', 'v', 'y')      # pale smoke puffs (Bixby's): light, mid, shade
SMOKE_DARK = ('ϒ', 'ϑ', 'ϑ', 'ϖ')   # a fire tornado's smoke (translucent)
SMOKE_THIN = ('ϖ', 'ϖ', 'ϡ', 'ϡ')
STEAM = ('λ', 'μ', 'ν', 'ξ')      # semi-transparent vapour, dense -> thin
TAU = 2 * math.pi


def blank(w, h):
    return R.blank(w, h)


def plot(L, x, y, ch):
    h, w = L.shape
    xi, yi = int(math.floor(x)), int(math.floor(y))
    if 0 <= xi < w and 0 <= yi < h:
        L[yi, xi] = ch
        return True
    return False


def hash01(x, y, seed=0):
    """A fixed per-texel random in [0, 1)."""
    v = np.sin(np.asarray(x) * 12.9898 + np.asarray(y) * 78.233 + seed * 37.719) * 43758.5453
    return v - np.floor(v)


def fill_holes(ins, max_size=14):
    """Fill the small enclosed gaps of a mask (bubbles where two flames meet and leave a pocket)."""
    h, w = ins.shape
    out = ins.copy()
    seen = ins.copy()
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0, x0]:
                continue
            stack = [(y0, x0)]
            seen[y0, x0] = True
            comp = []
            border = False
            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                if y == 0 or x == 0 or y == h - 1 or x == w - 1:
                    border = True
                for (yy, xx) in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < h and 0 <= xx < w and not seen[yy, xx]:
                        seen[yy, xx] = True
                        stack.append((yy, xx))
            if not border and len(comp) <= max_size:
                for (y, x) in comp:
                    out[y, x] = True
    return out


# ------------------------------------------------------------------ the metaball field
class Field:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.X, self.Y = R.centres(w, h)
        self.F = np.zeros((h, w))
        self.T = np.zeros((h, w))

    def blob(self, x, y, r, temp=1.0, stretch=1.3, mass=1.0, axis=(0.0, -1.0)):
        """A gaussian blob of radius r, stretched `stretch` times along `axis` (default: vertical)."""
        if r <= 0.05:
            return
        rl = r * stretch
        ext = 3 * max(r, rl)
        x0, x1 = int(max(0, math.floor(x - ext))), int(min(self.w, math.ceil(x + ext) + 1))
        y0, y1 = int(max(0, math.floor(y - ext))), int(min(self.h, math.ceil(y + ext) + 1))
        if x1 <= x0 or y1 <= y0:
            return
        X, Y = self.X[y0:y1, x0:x1] - x, self.Y[y0:y1, x0:x1] - y
        ax, ay = axis
        n = math.hypot(ax, ay) or 1.0
        ax, ay = ax / n, ay / n
        along = X * ax + Y * ay
        across = -X * ay + Y * ax
        g = mass * np.exp(-((along / rl) ** 2 + (across / r) ** 2))
        self.F[y0:y1, x0:x1] += g
        self.T[y0:y1, x0:x1] += g * temp

    def add(self, other_F, other_T):
        self.F += other_F
        self.T += other_T

    def inside(self, thr=0.5):
        return self.F > thr

    def render(self, L, thr=0.5, core=2.4, depth_w=0.6, temp_w=0.4, cuts=(0.2, 0.4, 0.62, 0.86),
               rim=RIM, bands=BANDS, mask=None, base_inside=None, base_heat=None, fill=True):
        """Band the field into the fire ramp inside a 1-px rim. Returns the inside mask. base_inside /
        base_heat add a body drawn another way (a funnel, a pool) that the tongues merge into."""
        ins = self.F > thr
        if base_inside is not None:
            ins = ins | base_inside
        if mask is not None:
            ins &= mask
        if not ins.any():
            return ins
        if fill:
            filled = fill_holes(ins)
            if base_inside is not None:
                base_inside = base_inside | (filled & ~ins)      # a filled pocket takes the body's heat
            ins = filled
        Tm = self.T / np.maximum(self.F, 1e-9)
        depth = np.clip((self.F - thr) / max(1e-6, core - thr), 0, 1)
        heat = depth_w * depth + temp_w * Tm
        if base_heat is not None:
            # the body keeps its own heat (tongues merging into it must not brighten it)
            heat = np.where(base_inside, base_heat, heat)
            Tm = np.where(base_inside, base_heat, Tm)
        idx = np.zeros(heat.shape, dtype=int)
        for c in cuts:
            idx += heat >= c
        chars = np.array(list(bands))[idx]
        L[ins] = chars[ins]
        if rim:
            p = np.pad(ins, 1, constant_values=False)
            edge = ins & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
            core_px = ins & ~edge
            # a rim texel with no interior texel round it belongs to a sliver (a tip, a torn piece): it
            # keeps a flame colour (red-orange while hot, dark red as it cools) instead of going maroon
            c = np.pad(core_px, 1, constant_values=False)
            near_core = np.zeros_like(ins)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    near_core |= c[1 + dy:1 + dy + ins.shape[0], 1 + dx:1 + dx + ins.shape[1]]
            sliver = edge & ~near_core
            L[edge & near_core] = rim
            L[sliver] = np.where(Tm[sliver] > 0.12, 'δ', 'ε')
        return ins


# ------------------------------------------------------------------ tongues
def _path(bx, by, up, curl, dist, side):
    """A point `dist` along a tongue that sets off along `up` and (with curl > 0) bends toward straight
    up over about `curl` texels - flames curl upward - plus a sideways offset. Returns (x, y, heading)."""
    ux, uy = up
    n = math.hypot(ux, uy) or 1.0
    ux, uy = ux / n, uy / n
    if curl <= 0:
        px, py = -uy, ux
        return bx + ux * dist + px * side, by + uy * dist + py * side, (ux, uy)
    x, y = bx, by
    steps = 6
    d = dist / steps
    dx, dy, m = ux, uy, 1.0
    for i in range(steps):
        f = min(1.0, ((i + 0.5) * d) / curl)
        dx, dy = ux * (1 - f), uy * (1 - f) - f
        m = math.hypot(dx, dy) or 1.0
        x += dx / m * d
        y += dy / m * d
    hx, hy = dx / m, dy / m
    return x - hy * side, y + hx * side, (hx, hy)


def tongue(fd, bx, by, t, H, r0, seed=0, rate=7, life=0.66, sway=1.0, lean=0.0, anchor=True, embers=None,
           ember_life=0.3, ember_every=2, up=(0.0, -1.0), accel=2.0, shrink=0.42, tip_stretch=1.4,
           cool=2.0, temp=1.0, curl=0.0):
    """One tongue on the base (bx, by). `up` is the direction it burns (default straight up); with
    curl > 0 it bends toward straight up over about `curl` texels. lean tilts it sideways per texel of
    height. Blobs spawn `rate` times a loop and live `life` loops, stretched along their heading. Every
    `ember_every`-th blob that dies carries on as an ember (appended to `embers` as (x, y, age 0..1))."""
    rnd = np.random.RandomState(1000 + int(seed * 97) % 100000)
    jit = rnd.rand(rate, 6)
    ux, uy = up
    for j in range(rate):
        s = (j + (jit[j, 0] - 0.5) * 0.35) / rate
        a = (t - s) % 1.0
        q = a / life
        k = 0.88 + 0.24 * jit[j, 1]
        if q <= 1.0:
            dist = H * (q ** accel) * k
            side = lean * dist + sway * math.sin(TAU * (0.8 * q + jit[j, 2])) * (0.3 + 1.4 * q)
            x, y, d = _path(bx, by, up, curl, dist, side)
            r = r0 * (1 - q) ** shrink * (0.85 + 0.3 * jit[j, 3])
            fd.blob(x, y, r, temp=temp * (1.0 - q) ** cool, stretch=1.25 + tip_stretch * q, axis=d)
        elif embers is not None and (j % ember_every == 0) and q <= 1.0 + ember_life / life:
            e = (a - life) / ember_life                 # 0..1 across the ember's life
            dist = H * k * (1.0 + 0.45 * e) + 1.0
            side = lean * dist + sway * math.sin(TAU * (0.8 + jit[j, 2]) + e * 3.0) * 1.8 + (jit[j, 4] - 0.5) * 3 * e
            x, y, d = _path(bx, by, up, curl, dist, side)
            embers.append((x, y - e * 3.0, e))
    if anchor:
        wob = 1.0 + 0.08 * math.sin(TAU * (2 * t + jit[0, 5]))
        fd.blob(bx + ux * r0 * 0.4, by + uy * r0 * 0.4, r0 * 1.05 * wob, temp=temp)
    return fd


def draw_embers(L, embers, smoke=True, smoke_ramp=SMOKE_LIGHT):
    """A torn tip's afterlife: a bright spark, cooling to red and dark, and (late) a grey wisp."""
    for (x, y, e) in embers:
        if e < 0.3:
            plot(L, x, y, 'α' if e < 0.12 else 'β')
            if e < 0.2:
                plot(L, x, y + 1, 'γ')
        elif e < 0.55:
            plot(L, x, y, 'γ' if e < 0.42 else 'δ')
        elif e < 0.75:
            plot(L, x, y, 'ε')
        elif smoke:
            c = smoke_ramp[1] if e < 0.88 else smoke_ramp[2]
            plot(L, x, y, c)
            plot(L, x + (1 if e > 0.82 else 0), y - 1, c)


def flames(w, h, specs, t, thr=0.5, render_kw=None, smoke=True, embers_on=True, extra=None):
    """A canvas with a set of tongues: specs = [dict(bx, by, H, r0, seed, ...)]. `extra(fd, t)` may add
    blobs (bodies, pools) before banding."""
    L = blank(w, h)
    fd = Field(w, h)
    emb = [] if embers_on else None
    for sp in specs:
        sp = dict(sp)
        bx, by, H, r0 = sp.pop('bx'), sp.pop('by'), sp.pop('H'), sp.pop('r0')
        tongue(fd, bx, by, t, H, r0, embers=emb, **sp)
    if extra is not None:
        extra(fd, t)
    fd.render(L, thr=thr, **(render_kw or {}))
    if emb:
        draw_embers(L, emb, smoke=smoke)
    return L


# ------------------------------------------------------------------ puffs (steam, smoke) that dissolve
def puff(L, cx, cy, r, ramp=STEAM, dissolve=0.0, seed=0, lobes=None, squash=0.85, light=(-0.6, -0.8, 0.9),
         shade_cuts=(0.72, 0.42), keep_core=True):
    """A shaded cloud of a few lobes at (cx, cy), radius r. ramp = (light, mid, shade[, thin]).
    dissolve 0..1 eats it from the edges in (texels near the rim go first), leaving torn scraps, and
    thins the colours toward the last ramp entry."""
    h, w = L.shape
    if r <= 0.4:
        return L
    if lobes is None:
        lobes = ((0.0, 0.0, 1.0), (-0.62, 0.28, 0.68), (0.6, 0.3, 0.72), (0.12, -0.5, 0.66))
    x0, x1 = int(max(0, cx - 2.2 * r - 2)), int(min(w, cx + 2.2 * r + 3))
    y0, y1 = int(max(0, cy - 2.2 * r - 2)), int(min(h, cy + 2.2 * r + 3))
    if x1 <= x0 or y1 <= y0:
        return L
    X, Y = R.centres(w, h)
    X, Y = X[y0:y1, x0:x1], Y[y0:y1, x0:x1]
    inside = np.zeros(X.shape, bool)
    depth = np.zeros(X.shape)
    shade = np.full(X.shape, -9.0)
    for (dx, dy, f) in lobes:
        rr = r * f
        ox, oy = cx + dx * r, cy + dy * r
        d2 = ((X - ox) / rr) ** 2 + ((Y - oy) / (rr * squash)) ** 2
        m = d2 <= 1
        inside |= m
        depth = np.maximum(depth, np.where(m, 1 - np.sqrt(np.minimum(d2, 1)), 0))
        v = R.lambert(R.sphere_normal(X, Y, ox, oy, rr, rr * squash), light=light)
        shade = np.where(m, np.maximum(shade, v), shade)
    if dissolve > 0:
        # coarse noise (2x2 texel cells), so a dissolving puff tears into scraps, not static
        n = hash01(np.floor((X - cx + 64) / 2.0), np.floor((Y - cy + 64) / 2.0), seed)
        # rim texels go first; by dissolve 1 even the core has holes and the whole thing is scraps
        eat = n < (dissolve * 1.25 - depth * (1.1 if keep_core else 0.6))
        inside &= ~eat
    lt, md, sh = ramp[0], ramp[1], ramp[2]
    thin = ramp[3] if len(ramp) > 3 else ramp[2]
    ch = np.where(shade > shade_cuts[0], lt, np.where(shade > shade_cuts[1], md, sh))
    if dissolve > 0.45:
        step = {lt: md, md: sh, sh: thin}
        ch = np.vectorize(lambda c: step.get(c, c))(ch)
    if dissolve > 0.8:
        ch = np.where(ch != '.', thin, ch)
    sub = L[y0:y1, x0:x1]
    sub[inside] = ch[inside]
    return L


def wisp_line(L, pts, ramp=STEAM, gap_every=0, seed=0, fade_from=0.6):
    """A thread of vapour through pts (list of (x, y)), thick-to-thin: early points use the dense colours,
    the tail the thin ones; gap_every > 0 breaks the tail into dashes."""
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        u = i / max(1, n - 1)
        if gap_every and u > fade_from and (i % gap_every) == 0:
            continue
        c = ramp[min(len(ramp) - 1, int(u * len(ramp)))]
        plot(L, x, y, c)
    return L
