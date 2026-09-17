"""Body parts for beast Bixby. Geometry is driven by a pose dict so hover/flap/fire poses share code.
Point coords are continuous; the sprite's symmetry axis is x = 96 (between pixel columns 95 and 96)."""
import math
import lib
from lib import *
from pal import PALC, RAMPC, BLACK

AXM = 191          # mask mirror: x' = 191 - x


def MX(x):
    return 192 - x


def mpts(pts):
    return [(192 - x, y) for x, y in pts]


def sym_poly(half):
    """half: left-side points from top-centre to bottom-centre (x <= 96)"""
    return poly(half + [(192 - x, y) for x, y in reversed(half[1:-1])])


def qbez(a, c, b, n=8):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
                    (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]))
    return out


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + dx * t), p[1] - (ay + dy * t)), t


def side_fn(side):
    if side > 0:
        return (lambda pts: list(pts)), (lambda m: m), (lambda x: x)
    return mpts, (lambda m: mirror(m, AXM)), MX


def offset(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]

# ======================================================================= wings


def wing(cv, P, side):
    f, g, fx = side_fn(side)
    root, elbow, wrist, thumb = f([P['w_root'], P['w_elbow'], P['w_wrist'], P['w_thumb']])
    tips = f(P['w_tips'])
    attach = f([P['w_attach']])[0]
    depth = P.get('w_scallop', 0.40)
    pts = [wrist, tips[0]]
    chain = tips + [attach]
    scallops = []
    for i, (a, b) in enumerate(zip(chain, chain[1:])):
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        d = depth * (0.8 if i == len(chain) - 2 else 1.0)
        c = (mid[0] + (wrist[0] - mid[0]) * d, mid[1] + (wrist[1] - mid[1]) * d)
        arc = qbez(a, c, b, 12)
        scallops.append(arc)
        pts += arc[1:]
    pts += [root, elbow]
    mem = poly(pts)
    bones_arm = [(root, elbow, 3.6, 3.0), (elbow, wrist, 3.0, 2.4)]
    bones_fing = [(wrist, t, 2.0, 1.0) for t in tips]
    rp = RAMPC['wing']
    dedge = chamfer(mem)
    L = max(math.hypot(t[0] - wrist[0], t[1] - wrist[1]) for t in tips)
    for (x, y) in mem:
        p = (x + 0.5, y + 0.5)
        r = math.hypot(p[0] - wrist[0], p[1] - wrist[1]) / L
        # base: darker near the arm, lighter (thinner, translucent) toward the trailing edge
        idx = 3 if r < 0.62 else 2
        # angular position inside each panel: shadow on the side just below each finger (light from top-left)
        for (a, b, r0, r1) in bones_fing + bones_arm:
            d, t = seg_dist(p, a, b)
            cr = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            below = (cr > 0) if side > 0 else (cr < 0)
            if below and d < 3.2 + 2.5 * t:
                idx = max(idx, 4 if d < 1.8 + 1.8 * t else 3)
        dd = dedge[(x, y)]
        if dd <= 1.5:
            idx = 1
        cv.put(x, y, rp[idx])
    # glow speckles at the thinnest part of each scallop
    for arc in scallops[:-1]:
        mx, my = arc[len(arc) // 2]
        for k in (-3, -2, -1, 0, 1, 2, 3):
            ax_, ay_ = arc[max(0, min(len(arc) - 1, len(arc) // 2 + k))]
            q = (int(ax_), int(ay_))
            # step one pixel inward toward the wrist
            vx, vy = wrist[0] - ax_, wrist[1] - ay_
            n = math.hypot(vx, vy) or 1
            qi = (int(ax_ + vx / n * 1.6), int(ay_ + vy / n * 1.6))
            if qi in mem and abs(k) <= 1:
                cv.put(qi[0], qi[1], PALC['P'])
    cv.outline(mem)
    for (a, b, r0, r1) in bones_arm + bones_fing:
        m = capsule(a, b, r0, r1)
        cv.part(m, 'dark', ('cyl', a, b, max(r0, r1) + 0.5), TH_B)
    # wrist knuckle + thumb claw
    kn = ell(wrist[0], wrist[1], 3.4, 3.4)
    cv.part(kn, 'dark', ('sphere', wrist[0] - 0.5, wrist[1] - 0.5, 3.6, 3.6), TH_B)
    mid = ((wrist[0] + thumb[0]) / 2 + 2.2 * side, (wrist[1] + thumb[1]) / 2 + 0.5)
    m = tube([wrist, mid, thumb], [2.4, 1.7, 0.5])
    cv.part(m, 'dark', ('dist', 2.0), TH_GLOSS)
    # fingertip claws poking past the membrane
    for t in tips:
        v = (t[0] - wrist[0], t[1] - wrist[1])
        n = math.hypot(*v)
        e = (t[0] + v[0] / n * 3.5, t[1] + v[1] / n * 3.5)
        m = capsule(t, e, 1.4, 0.4)
        cv.part(m, 'dark', ('dist', 1.2), TH_GLOSS)
    return mem

# ======================================================================= tail


def tail(cv, P):
    path = P['tail_path']
    m = tube(path, P['tail_r'])
    cv.part(m, 'dark', ('dist', 3.2), TH_B)
    tx, ty = P['tail_tip']
    tip = poly([(tx, ty + 2), (tx - 6, ty - 3), (tx - 8, ty - 9), (tx - 5, ty - 15), (tx - 2, ty - 20), (tx, ty - 27),
                (tx + 2, ty - 20), (tx + 5, ty - 15), (tx + 8, ty - 9), (tx + 6, ty - 3)])
    cv.part(tip, 'lava', ('sphere', tx - 1.5, ty - 12, 7, 12), [0.95, 0.80, 0.55, 0.30, 0.05, -0.3], bias=1)
    return m | tip

# ======================================================================= legs


def hind_leg(cv, P, side):
    f, g, fx = side_fn(side)
    hip, knee, ank, paw = f([P['h_hip'], P['h_knee'], P['h_ankle'], P['h_paw']])
    thigh = ell(hip[0], hip[1], 9.5, 11, 20 * side)
    shin = capsule(knee, ank, 5.8, 4.6)
    pw = ell(paw[0], paw[1], 6.5, 4.6)
    cv.part(shin | pw, 'fur', ('dist', 3.0), TH_B, bias=0)
    cv.part(thigh, 'dark', ('sphere', hip[0] - 2, hip[1] - 3, 11, 13), TH_B)
    for i, dx in enumerate((-4, 0, 4)):
        c = (paw[0] + dx, paw[1] + 3.5)
        e = (c[0] + dx * 0.25, c[1] + 4)
        cm = capsule(c, e, 1.5, 0.45)
        cv.part(cm, 'dark', ('dist', 1.4), TH_GLOSS)


def front_leg(cv, P, side):
    f, g, fx = side_fn(side)
    sh, el, wr, pw = f([P['f_sh'], P['f_el'], P['f_wr'], P['f_paw']])
    upper = capsule(sh, el, 10.5, 8)
    fore = capsule(el, wr, 7.8, 6.6)
    paw = ell(pw[0], pw[1], 9.5, 6.5)
    cv.part(fore | paw, 'fur', ('cyl', el, wr, 8), TH_B, bias=0)
    cv.part(upper, 'dark', ('cyl', sh, el, 11), TH_B)
    # claws: 4, hooked downward
    for dx in (-6, -2, 2, 6):
        c = (pw[0] + dx, pw[1] + 4.5)
        e = (c[0] + dx * 0.22, c[1] + 5.5)
        cm = tube([c, (c[0] + dx * 0.15, c[1] + 3), e], [2.0, 1.4, 0.4])
        cv.part(cm, 'dark', ('dist', 1.6), TH_GLOSS)

# ======================================================================= torso


def torso(cv, P):
    dy = P.get('body_dy', 0)
    half = offset([(96, 79), (84, 80), (73, 84), (63, 91), (59, 100), (61, 110), (67, 119), (75, 126), (85, 132), (96, 134)], 0, dy)
    m = sym_poly(half)
    cv.part(m, 'dark', ('dist', 8.0), TH_B)
    belly_half = offset([(96, 81), (85, 82), (77, 89), (75, 100), (78, 113), (85, 125), (96, 131)], 0, dy)
    bm = sym_poly(belly_half) & m
    cv.part(bm, 'fur', ('sphere', 94, 98 + dy, 24, 34), TH_B, bias=0, outline=False)
    return m, bm

# ======================================================================= necks & collars


def side_neck(cv, P, side):
    f, g, fx = side_fn(side)
    a, b = f([P['sn_base'], P['sn_top']])
    m = capsule(a, b, 10.5, 9.5)
    cv.part(m, 'fur', ('cyl', a, b, 11), TH_B)
    return m


# ======================================================================= spiked collars
def spike(cv, base, direction, length, width):
    """iron cone spike from base point along direction"""
    dx, dy = direction
    n = math.hypot(dx, dy) or 1
    dx, dy = dx / n, dy / n
    tip = (base[0] + dx * length, base[1] + dy * length)
    m = capsule(base, tip, width, 0.35)
    cv.part(m, 'iron', ('cyl', base, tip, width + 0.6), [0.9, 0.5, 0.1])
    return m


def middle_collar(cv, P):
    cx = 96
    top = P.get('mc_top', 73)
    h = P.get('mc_h', 9)
    sag = P.get('mc_sag', 3.5)
    halfw = P.get('mc_halfw', 20)
    upper = [(cx - halfw + i * (2 * halfw) / 16, top + sag * (1 - ((i - 8) / 8) ** 2)) for i in range(17)]
    lower = [(x, y + h) for x, y in upper]
    band = poly(upper + list(reversed(lower)))
    # spikes under the band (drawn first so the band overlaps their bases)
    sp = []
    for i, fx in enumerate((-0.82, -0.42, 0.0, 0.42, 0.82)):
        x = cx + fx * halfw
        t = (fx + 1) / 2 * 16
        y = top + sag * (1 - ((t - 8) / 8) ** 2) + h - 1
        d = (fx * 0.9, 1.0)
        sp.append(spike(cv, (x, y), d, 6.5 if i == 2 else 5.5, 2.6))
    cv.part(band, 'collar', ('sphere', cx - 6, top - 2, 28, 16, 0.2), TH_B4)
    # studs
    for fx in (-0.62, -0.21, 0.21, 0.62):
        x = cx + fx * halfw
        t = (fx + 1) / 2 * 16
        y = top + sag * (1 - ((t - 8) / 8) ** 2) + h / 2
        st = ell(x, y, 1.6, 1.6)
        cv.part(st, 'iron', ('sphere', x - 0.5, y - 0.5, 1.8, 1.8), [0.9, 0.5, 0.1], outline=False)
        cv.put(int(x) - 1 if x % 1 < 0.5 else int(x), int(y) - 1, PALC['x'])
    return band


def side_collar(cv, P, side):
    f, g, fx = side_fn(side)
    a, b = f(P['sc_axis'])          # collar band axis (across the neck)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    band = capsule(a, b, P.get('sc_w', 4.2), P.get('sc_w', 4.2))
    # outward normal (away from the neck base, toward the head)
    nx, ny = -math.sin(ang), math.cos(ang)
    hx, hy = f([P['sn_top']])[0]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if (hx - mx) * nx + (hy - my) * ny > 0:
        nx, ny = -nx, -ny
    for t in (0.18, 0.5, 0.82):
        px = a[0] + (b[0] - a[0]) * t + nx * 3.2
        py = a[1] + (b[1] - a[1]) * t + ny * 3.2
        spike(cv, (px, py), (nx + (t - 0.5) * 0.8 * math.cos(ang), ny + (t - 0.5) * 0.8 * math.sin(ang)), 5.0, 2.3)
    cv.part(band, 'collar', ('cyl', a, b, 5), TH_B4)
    for t in (0.33, 0.67):
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t
        cv.put(int(x), int(y), PALC['X'])
        cv.put(int(x) - 1, int(y) - 1, PALC['x'])
    return band
