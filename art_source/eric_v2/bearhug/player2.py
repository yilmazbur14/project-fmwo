"""The player boxer at ~2x true scale (~32 px tall on Eric's 128 grid), built from shaded parts so poses are cheap.
Seen from behind (face pressed into Eric's chest): dark hair, tan skin, blue gloves + shorts, dark shoes.
Local coords: x right, y down, origin = centre of the waistband. Pose = dict of joint positions (local).
"""
import math
import lib
from lib import hexc, BLACK, TH_SOFT, _DARKER, _LIGHTER

lib.RAMPS.update({
    'ptan': ['ffdcae', 'efb582', 'd79864', 'ac714f', '87553c', '6a3f2e'],
    'pblue': ['b0dcff', '5fabec', '2f78d0', '1f58a8', '173e80', '112c5e'],
    'phair': ['7a7486', '5a5466', '3a3544', '26232b', '17151b', '0f0e12'],
    'pshoe': ['6a6874', '4a4854', '33313b', '221f28', '141218', '0c0b0f'],
})
# register the ramps for darker/lighter lookups
for rn in ('ptan', 'pblue', 'phair', 'pshoe'):
    cs = [hexc(c) for c in lib.RAMPS[rn]]
    for i, c in enumerate(cs):
        _DARKER.setdefault(c, cs[min(i + 1, len(cs) - 1)])
        _LIGHTER.setdefault(c, cs[max(i - 1, 0)])

TH_P = [9.0, 0.86, 0.6, 0.3, 0.05]

BASE = dict(
    head=(0.0, -15.5), head_r=(4.9, 5.1), head_ang=0.0,
    neck=(0.0, -10.5),
    sh_l=(-6.0, -9.0), sh_r=(6.0, -9.0),
    el_l=(-8.5, -3.0), el_r=(8.5, -3.0),
    gl_l=(-9.0, 3.0), gl_r=(9.0, 3.0),
    hip_l=(-3.2, 5.0), hip_r=(3.2, 5.0),
    kn_l=(-3.8, 10.0), kn_r=(3.8, 10.0),
    ft_l=(-4.2, 14.5), ft_r=(4.2, 14.5),
    torso_w=(7.2, 5.6), torso_top=-10.0,
    shorts_h=6.0,
)


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


HUGGED = pose(el_l=(-11.0, -13.0), el_r=(11.0, -14.5), gl_l=(-13.5, -20.0), gl_r=(12.5, -22.0),
              kn_l=(-8.5, 9.0), ft_l=(-14.0, 10.5), kn_r=(7.0, 10.5), ft_r=(9.5, 15.5))
SQUASH = pose(head=(0.0, -12.0), head_r=(5.0, 3.9), neck=(0.0, -8.5), torso_top=-7.5, torso_w=(8.4, 6.6),
              sh_l=(-7.0, -6.5), sh_r=(7.0, -6.5), el_l=(-12.5, -12.0), el_r=(12.5, -12.5),
              gl_l=(-16.5, -18.0), gl_r=(16.0, -19.0), shorts_h=5.0,
              hip_l=(-3.8, 4.0), hip_r=(3.8, 4.0), kn_l=(-9.0, 7.5), kn_r=(9.0, 7.5), ft_l=(-13.5, 8.5), ft_r=(13.5, 8.5))
DAZED = pose(head=(1.8, -14.2), head_ang=18.0, el_l=(-8.5, -2.5), el_r=(8.8, -2.0), gl_l=(-8.8, 3.5), gl_r=(9.5, 4.0),
             kn_l=(-3.4, 10.5), kn_r=(3.6, 10.5), ft_l=(-3.2, 15.5), ft_r=(4.0, 15.5))
LOOSE = pose(el_l=(-11.0, -6.0), el_r=(11.0, -6.5), gl_l=(-13.5, -1.0), gl_r=(13.5, -2.0),
             kn_l=(-4.5, 10.5), kn_r=(4.5, 10.0), ft_l=(-5.5, 15.0), ft_r=(5.0, 14.5))
FLYING = pose(el_l=(-11.5, -12.0), el_r=(11.0, -13.5), gl_l=(-14.0, -17.5), gl_r=(13.0, -19.5),
              kn_l=(-7.5, 9.0), ft_l=(-11.5, 11.5), kn_r=(6.5, 9.5), ft_r=(10.0, 12.5))


class T:
    """local -> frame transform: rotate by ang (deg), scale, translate to origin o"""

    def __init__(self, o, ang=0.0, s=1.0):
        self.o, self.s = o, s
        a = math.radians(ang)
        self.ca, self.sa = math.cos(a), math.sin(a)
        self.ang = ang

    def __call__(self, p):
        x, y = p[0] * self.s, p[1] * self.s
        return (self.o[0] + x * self.ca - y * self.sa, self.o[1] + x * self.sa + y * self.ca)


def capsule(p0, p1, r0, r1=None):
    r1 = r0 if r1 is None else r1
    W, H = lib.W, lib.H
    m = [[False] * W for _ in range(H)]
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1e-6
    R = max(r0, r1)
    for y in range(max(0, int(min(y0, y1) - R - 2)), min(H, int(max(y0, y1) + R + 3))):
        for x in range(max(0, int(min(x0, x1) - R - 2)), min(W, int(max(x0, x1) + R + 3))):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
            cx, cy = x0 + dx * t, y0 + dy * t
            r = r0 + (r1 - r0) * t
            if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                m[y][x] = True
    return m


def draw(fr, P, origin, ang=0.0, s=1.0):
    """draw the boxer into a rig.Frame; returns bbox (x0, y0, x1, y1) of the pixels drawn"""
    cv = fr.canvas() if hasattr(fr, 'canvas') else fr.as_canvas()
    W, H = lib.W, lib.H
    before = [[p is not None for p in row] for row in fr.px]
    snap = [row[:] for row in fr.px]
    t = T(origin, ang, s)
    k = s
    touched = lib.empty()

    def part(mask, ramp, model, th=TH_P):
        cv.part(mask, ramp, model, th=th)
        for y in range(H):
            for x in range(W):
                if mask[y][x]:
                    touched[y][x] = True

    def limb(a, b, r0, r1, ramp):
        A, B = t(P[a] if isinstance(a, str) else a), t(P[b] if isinstance(b, str) else b)
        m = capsule(A, B, r0 * k, r1 * k)
        part(m, ramp, ('cyl', A, B, max(r0, r1) * k + 0.6))
        # outline the capsule separately so overlapping limbs keep their own edge
        return m

    # ---- legs (behind the shorts)
    for side in ('l', 'r'):
        limb('hip_' + side, 'kn_' + side, 2.9, 2.5, 'ptan')
        limb('kn_' + side, 'ft_' + side, 2.5, 2.1, 'ptan')
        f = t(P['ft_' + side])
        kn = t(P['kn_' + side])
        # shoe: an ellipse pointing along the shin
        ang_shin = math.degrees(math.atan2(f[1] - kn[1], f[0] - kn[0]))
        sm = lib.ell(f[0], f[1] + 0.6 * k, 2.8 * k, 3.4 * k, ang_shin - 90)
        part(sm, 'pshoe', ('sphere', f[0] - 1, f[1] - 0.5, 3.2 * k, 3.4 * k))
    # ---- arms (behind the torso)
    for side in ('l', 'r'):
        limb('sh_' + side, 'el_' + side, 2.8, 2.5, 'ptan')
        limb('el_' + side, 'gl_' + side, 2.5, 2.2, 'ptan')
    # ---- torso (bare back): trapezoid with rounded shoulders
    tw_top, tw_bot = P['torso_w']
    top = P['torso_top']
    pts = [(-tw_top + 1.2, top), (tw_top - 1.2, top), (tw_top, top + 1.6), (tw_bot + 0.6, -1.5), (tw_bot, 0.8),
           (-tw_bot, 0.8), (-tw_bot - 0.6, -1.5), (-tw_top, top + 1.6)]
    tm = lib.poly([t(p) for p in pts])
    c = t((0, (top + 0) / 2))
    part(tm, 'ptan', ('sphere', c[0] - 1.5 * k, c[1] - 2.5 * k, (tw_top + 2) * k, (-top / 2 + 3) * k, 0.2))
    # spine groove + shoulder-blade shadows
    for yy in range(int(top + 3), 0):
        q = t((0.0, yy + 0.5))
        x, y = int(math.floor(q[0])), int(math.floor(q[1]))
        if 0 <= x < W and 0 <= y < H and tm[y][x] and fr.px[y][x] not in (None, BLACK):
            fr.px[y][x] = _DARKER.get(fr.px[y][x], fr.px[y][x])
    for sx in (-1, 1):
        for (u, v) in ((2.6, top + 3.0), (3.6, top + 3.6), (4.4, top + 4.6)):
            q = t((sx * u, v))
            x, y = int(math.floor(q[0])), int(math.floor(q[1]))
            if 0 <= x < W and 0 <= y < H and tm[y][x] and fr.px[y][x] not in (None, BLACK):
                fr.px[y][x] = _DARKER.get(fr.px[y][x], fr.px[y][x])
    # ---- shorts
    sh = P['shorts_h']
    spts = [(-tw_bot - 0.6, -0.4), (tw_bot + 0.6, -0.4), (tw_bot + 1.6, sh), (1.0, sh), (0.0, sh - 1.8),
            (-1.0, sh), (-tw_bot - 1.6, sh)]
    smask = lib.poly([t(p) for p in spts])
    c = t((0, sh / 2))
    part(smask, 'pblue', ('sphere', c[0] - 2 * k, c[1] - 2 * k, (tw_bot + 4) * k, (sh + 3) * k, 0.2))
    # waistband highlight
    for u in range(int(-tw_bot), int(tw_bot) + 1):
        q = t((u + 0.5, 0.9))
        x, y = int(math.floor(q[0])), int(math.floor(q[1]))
        if 0 <= x < W and 0 <= y < H and smask[y][x] and fr.px[y][x] not in (None, BLACK):
            fr.px[y][x] = _LIGHTER.get(fr.px[y][x], fr.px[y][x])
    # ---- gloves (over the forearm ends)
    for side in ('l', 'r'):
        g = t(P['gl_' + side])
        el = t(P['el_' + side])
        a = math.degrees(math.atan2(g[1] - el[1], g[0] - el[0]))
        gm = lib.ell(g[0], g[1], 3.5 * k, 3.9 * k, a - 90)
        part(gm, 'pblue', ('sphere', g[0] - 1.2 * k, g[1] - 1.4 * k, 3.6 * k, 3.8 * k, 0.1))
    # ---- neck, ears, head (back of the head: all hair)
    n0, n1 = t(P['neck']), t((P['neck'][0], P['torso_top'] + 1.5))
    nm = capsule(n0, n1, 2.4 * k)
    part(nm, 'ptan', ('cyl', n0, n1, 2.6 * k))
    hc = P['head']
    hr = P['head_r']
    ha = P['head_ang']
    for sx in (-1, 1):
        # ear sits on the side of the skull, rotated with the head
        ea = math.radians(ha)
        ex, ey = sx * (hr[0] - 0.2), 0.6
        e = t((hc[0] + ex * math.cos(ea) - ey * math.sin(ea), hc[1] + ex * math.sin(ea) + ey * math.cos(ea)))
        em = lib.ell(e[0], e[1], 1.8 * k, 2.3 * k, t.ang + ha)
        part(em, 'ptan', ('sphere', e[0] - 0.5, e[1] - 0.8, 2.0 * k, 2.4 * k))
    h = t(hc)
    hm = lib.ell(h[0], h[1], hr[0] * k, hr[1] * k, t.ang + ha)
    part(hm, 'phair', ('sphere', h[0] - 1.6 * k, h[1] - 2.2 * k, (hr[0] + 1.2) * k, (hr[1] + 1.2) * k, 0.15))
    # a few lighter strands on the lit side of the hair
    for (u, v) in ((-1.5, -2.8), (-0.5, -3.3), (-2.4, -1.8), (0.6, -2.9)):
        a = math.radians(ha)
        q = t((hc[0] + u * math.cos(a) - v * math.sin(a), hc[1] + u * math.sin(a) + v * math.cos(a)))
        x, y = int(math.floor(q[0])), int(math.floor(q[1]))
        if 0 <= x < W and 0 <= y < H and hm[y][x] and fr.px[y][x] not in (None, BLACK):
            fr.px[y][x] = _LIGHTER.get(fr.px[y][x], fr.px[y][x])
    xs = [x for y in range(H) for x in range(W) if touched[y][x] or (fr.px[y][x] is not None and not before[y][x])]
    ys = [y for y in range(H) for x in range(W) if touched[y][x] or (fr.px[y][x] is not None and not before[y][x])]
    return (min(xs), min(ys), max(xs), max(ys))
