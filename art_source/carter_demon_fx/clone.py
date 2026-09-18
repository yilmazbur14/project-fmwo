"""demon_clone.png and demon_clone_ghost.png - the shadow that rushes you.

A clone is NOT Carter.  The first pass put a full-size 96x96 Carter on screen at
3x, 288px tall, four times the player's height, and it read as the man himself
standing in the dark rather than as a swarm closing in.  These are half that:
48x48 frames, 144px at 3x, about twice the player and half of Carter.  48 is the
largest size that still halves him on an integer 3x, and the silhouette survives
it because a shadow only ever has to carry a shape - the beard, the belt and the
juzu were never legible at speed anyway.  The one thing kept from the detail is
the pair of red eye slits, which is the whole of the clone's identity.

They MATERIALISE rather than appear, the way Akuma's Oboro throw does: the
silhouette gathers out of scattered pixels, firms up as it commits, and scatters
again as it passes.  That is authored here as frames, not left to a code alpha
ramp, because a flat opacity fade looks like a sprite being turned on.  What
makes it read as gathering is `scatter` - every pixel of the silhouette is
thrown outward from the body's centroid by an amount that falls to zero over the
four appear frames, so the shape converges on itself.  Dissipate runs the same
trick in reverse with a backward-and-upward bias, so the residue is left behind
by a clone that has already gone past.

Everything derives from the rush pose sheet.  While Assets/Characters/Carter/
carter_rush.png does not exist yet this falls back to carter_akuma.png frame 0
and says so loudly; once the real sheet lands, re-running build_fx.py picks it
up with no hand-fitting, and the ghost follows because it is a smear of the same
silhouette rather than a separately drawn figure.
"""
import math
import os

from fxlib import Mask, Cv, ell, ramp, sheet, bayer01, hexc, read_png, crop

SRC = 96                   # the pose sheet's frame size
S = 48                     # the clone's frame size -> 144px at 3x
GW = 96                    # the ghost's frame is wider, to have room for a
GX = 24                    # trail; the clone's box sits at x 24..71, i.e. both
                           # sprites are `centered` on the same point

VO = ramp('void')          # e2a2f4 b45ae0 7c2eb0 4e1878 2e0c4c 19062a
EM = ramp('ember')
GLOW = [hexc(c) for c in ('ffffff', 'ffd2d8', 'ff5a62',
                          'e0203c', '90102a', '54061a')]

CHARS = os.path.join('..', '..', 'Assets', 'Characters')
RUSH = os.path.join(CHARS, 'Carter', 'carter_rush.png')
STAND_IN = os.path.join(CHARS, 'Carter', 'carter_akuma.png')


class _R:
    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s

    def f(self):
        return self.next() / float(0x7FFFFFFF)

    def r(self, a, b):
        return a + (b - a) * self.f()


# ------------------------------------------------------------------- source

def load_pose():
    """4 frames of the rush, as (silhouette, eyes) masks at 48x48"""
    if os.path.isfile(RUSH):
        w, h, px = read_png(RUSH)
        n = max(1, w // SRC)
        frames = [crop(px, i * SRC, 0, SRC, SRC) for i in range(min(4, n))]
        real = True
    else:
        w, h, px = read_png(STAND_IN)
        frames = [crop(px, 0, 0, SRC, SRC)] * 4
        real = False
        print('  ! carter_rush.png not found - clones built from the '
              'carter_akuma.png frame 0 STAND-IN.  Re-run build_fx.py once the '
              'rush sheet lands and they regenerate from it.')
    while len(frames) < 4:
        frames.append(frames[-1])
    return [(_down2(_opaque(f)), _down2(_glow(f))) for f in frames], real


def _opaque(f):
    m = Mask(SRC, SRC)
    for y in range(SRC):
        for x in range(SRC):
            if f[y][x][3] > 0:
                m.g[y][x] = True
    return m


def _glow(f):
    """the red eye slits: glow-ramp pixels in the top of the body box"""
    ys = [y for y in range(SRC) for x in range(SRC) if f[y][x][3] > 0]
    if not ys:
        return Mask(SRC, SRC)
    y0, y1 = min(ys), max(ys)
    cut = y0 + (y1 - y0) * 0.45
    m = Mask(SRC, SRC)
    for y in range(SRC):
        if y > cut:
            continue
        for x in range(SRC):
            if f[y][x][3] > 0 and f[y][x][:3] in [g[:3] for g in GLOW]:
                m.g[y][x] = True
    return m


def _down2(m):
    """96 -> 48, by majority of each 2x2 block, so the silhouette neither
    fattens nor frays.

    The eyes go through the same majority rule.  Taking ANY set pixel instead -
    on the theory that two slits 8px wide would be lost - rounded them up to
    five texels each, which on a twelve-texel head read as goggles."""
    out = Mask(S, S)
    for y in range(S):
        for x in range(S):
            n = sum(1 for dy in (0, 1) for dx in (0, 1)
                    if m.g[y * 2 + dy][x * 2 + dx])
            out.g[y][x] = n >= 2
    return out


# ------------------------------------------------------------------ gather

def _centroid(m):
    pts = [(x, y) for y in range(m.h) for x in range(m.w) if m.g[y][x]]
    if not pts:
        return m.w / 2.0, m.h / 2.0
    return (sum(p[0] for p in pts) / float(len(pts)),
            sum(p[1] for p in pts) / float(len(pts)))


def scatter(m, amt, rng, bias=(0.0, 0.0)):
    """throw every pixel outward from the centroid by up to `amt`.

    This is what makes the appear read as a shape CONVERGING rather than as a
    sprite fading up: amt falls to zero across the four frames, so the cloud
    collapses into the silhouette."""
    if amt <= 0.01 and bias == (0.0, 0.0):
        return m
    cx, cy = _centroid(m)
    out = Mask(m.w, m.h)
    for y in range(m.h):
        for x in range(m.w):
            if not m.g[y][x]:
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            n = math.hypot(dx, dy) or 1.0
            k = rng.r(0.35, 1.0) * amt
            nx = int(round(x + dx / n * k + bias[0] * rng.r(0.4, 1.6)
                           + rng.r(-1.0, 1.0)))
            ny = int(round(y + dy / n * k * 0.75 + bias[1] * rng.r(0.4, 1.6)
                           + rng.r(-1.0, 1.0)))
            if 0 <= nx < m.w and 0 <= ny < m.h:
                out.g[ny][nx] = True
    return out


# ------------------------------------------------------------------- render

def shadow(body, eyes, alpha, cover, rim, eyeglow):
    """a flat, dark, translucent stand-in for a man"""
    def a(c):
        return (c[0], c[1], c[2], alpha)

    cv = Cv(S, S)
    b = body if cover >= 16 else body.dither(cover)
    # flat on purpose - a shadow-image has no modelling.  Only the deepest
    # middle goes a step darker, and all the readability comes from the rim.
    cv.paint(b, a(VO[4]))
    cv.paint(b.erode(4), a(VO[5]))
    if rim:
        # the rim is the only thing separating the figure from its own trail,
        # which is the same purple family - so it runs a full two steps hotter
        # than the body rather than one
        cv.paint(b - b.erode(1), a(VO[2]))
        # he is running into his own light: the front edge is the hottest
        cv.paint((b - b.shift(-1, 0)) & b, a(VO[1]))
    if eyeglow and eyes.count():
        e = eyes if cover >= 12 else eyes.dither(max(6, cover))
        cv.paint(e.ring(1).dither(9, off=1),
                 (EM[3][0], EM[3][1], EM[3][2], min(255, alpha + 30)))
        cv.paint(e, (EM[2][0], EM[2][1], EM[2][2], 255))
    return cv


# 12 frames: 0-3 appear, 4-7 rush, 8-11 dissipate.
# `scatter` also thins a shape on its own - displaced pixels collide and merge -
# so the coverage numbers here are higher than the density they actually
# produce.  Tuned by eye against the darkened stage, where the first pass's
# f0/f1 were invisible rather than faint.
APPEAR = [(6.0, 6, 100, False, False),
          (3.6, 10, 140, False, True),
          (1.8, 13, 172, True, True),
          (0.0, 16, 196, True, True)]
RUSHF = (0.0, 16, 212, True, True)
DISSIP = [(1.5, 13, 186, True, True),
          (3.6, 10, 150, False, True),
          (6.2, 6, 112, False, False),
          (9.5, 3, 72, False, False)]
DRIFT = (-2.0, -1.1)       # residue is left behind and rises


def clone_frames(poses):
    out = []
    for i, (amt, cov, al, rim, eye) in enumerate(APPEAR):
        b, e = poses[0]
        rng = _R(0xA11CE + i * 131)
        out.append(shadow(scatter(b, amt, rng), scatter(e, amt * 0.5, _R(i)),
                          al, cov, rim, eye))
    for i in range(4):
        b, e = poses[i]
        amt, cov, al, rim, eye = RUSHF
        out.append(shadow(b, e, al, cov, rim, eye))
    for i, (amt, cov, al, rim, eye) in enumerate(DISSIP):
        b, e = poses[3]
        rng = _R(0xD1E + i * 977)
        out.append(shadow(scatter(b, amt, rng, DRIFT),
                          scatter(e, amt * 0.6, _R(90 + i), DRIFT),
                          al, cov, rim, eye))
    return out


# -------------------------------------------------------------------- ghost

def _wide(m):
    """put the 48x48 silhouette into the ghost's 96x48 frame"""
    out = Mask(GW, S)
    for y in range(S):
        for x in range(S):
            if m.g[y][x]:
                out.g[y][x + GX] = True
    return out


def smear(m, n):
    out = m.copy()
    for k in range(1, n + 1):
        out = out | m.shift(-k, 0)
    return out


def _agefield(body, reach, power=1.0):
    """1.0 on the body, falling to 0.0 `reach` pixels behind it ALONG THE ROW,
    so the trail hugs the silhouette and each limb streams its own tail"""
    out = [[0.0] * GW for _ in range(S)]
    for y in range(S):
        age = None
        for x in range(GW - 1, -1, -1):
            if body.g[y][x]:
                age = 0
            elif age is not None:
                age += 1
            if age is None or age > reach:
                continue
            out[y][x] = (1.0 - age / float(reach)) ** power
    return out


def _dissolve(cv, fld, gain):
    hit = Mask(GW, S)
    for y in range(S):
        for x in range(GW):
            if cv.px[y][x] is not None and fld[y][x] * gain < bayer01(x, y):
                hit.g[y][x] = True
    cv.erase(hit)


def _streaks(rng, x_head, reach, n, thick_max):
    m = Mask(GW, S)
    for _ in range(n):
        y = int(rng.r(5, S - 4))
        x1 = int(rng.r(x_head - 10, x_head + 2))
        x0 = max(0, x1 - int(rng.r(reach * 0.45, reach)))
        t = int(rng.r(1, thick_max + 1))
        for yy in range(y, min(S, y + t)):
            for xx in range(max(0, x0), min(GW, x1)):
                m.g[yy][xx] = True
    return m


GHOST_A = 162              # the trail is translucent too


def ghost_frame(body48, stage):
    rng = _R(0xC0FFEE + stage * 977)
    cv = Cv(GW, S)

    def a(c):
        return (c[0], c[1], c[2], GHOST_A)

    dx = (-4, -8, -12, -16)[stage]
    reach = (10, 15, 20, 24)[stage]
    gain = (1.5, 1.25, 1.0, 0.72)[stage]
    body = _wide(body48).shift(dx, 0)
    bb = body.bbox()
    if bb is None:
        return cv
    x_head = bb[2]
    trail = smear(body, reach)

    fld = _agefield(body, reach, power=1.3)
    cv.steps(fld, [a(VO[5]), a(VO[4]), a(VO[4]), a(VO[3]), a(VO[3])],
             mask=trail, floor=1)
    _dissolve(cv, fld, gain)

    # speed lines go on AFTER the dissolve and reach further back than the
    # smear: eaten by the same age field they left the trail with nothing that
    # says "fast"
    st = _streaks(rng, x_head, int(reach * 1.6), (10, 13, 16, 14)[stage], 2)
    cv.paint(st.dither((12, 11, 9, 7)[stage], off=1), a(VO[3]))
    hot = _streaks(rng, x_head, int(reach * 0.9), (4, 5, 6, 4)[stage], 1)
    cv.paint(hot.dither((13, 12, 10, 8)[stage], off=2), a(VO[2]))

    if stage < 3:
        cv.paint((body - body.shift(-1, 0)).dither((16, 13, 9, 0)[stage]),
                 a(VO[1]))
    for _ in range((5, 7, 8, 6)[stage]):
        cv.set(int(rng.r(max(0, x_head - reach), x_head)),
               int(rng.r(5, S - 4)), a(VO[1]))

    # Never draw inside the clone's own footprint.  Both sprites are
    # translucent, so where they overlapped the purple composited twice and the
    # clone's silhouette dissolved into its own trail.  The ghost is the TAIL
    # and nothing else; the clone on top provides the figure.
    cv.erase(_wide(body48))
    return cv


def build(path_clone, path_ghost):
    poses, real = load_pose()
    sheet(clone_frames(poses), path_clone)
    sheet([ghost_frame(poses[i][0], i) for i in range(4)], path_ghost)
    return path_clone, path_ghost
