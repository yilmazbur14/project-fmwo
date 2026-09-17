"""Polished limbs, tail and wings for beast Bixby."""
import math
import lib
from lib import *
from pal import PALC, RAMPC, BLACK
from parts import side_fn, mpts, qbez, seg_dist
from body import crack, line_px


def claw(cv, base, direction, length, width, curl=0.35):
    dx, dy = direction
    n = math.hypot(dx, dy) or 1
    dx, dy = dx / n, dy / n
    px, py = -dy, dx
    mid = (base[0] + dx * length * 0.55 + px * curl * length * 0.25, base[1] + dy * length * 0.55 + py * curl * length * 0.25)
    tip = (base[0] + dx * length + px * curl * length * 0.1, base[1] + dy * length + py * curl * length * 0.1)
    m = tube([base, mid, tip], [width, width * 0.62, 0.3])
    cv.part(m, 'dark', ('dist', width), TH_GLOSS)
    return m


def paw(cv, c, n_toes, spread, toe_r, pad_rx, pad_ry, claw_len, claw_w, side=1):
    """rounded paw with toe bumps along the bottom and a claw per toe"""
    toes = []
    for i in range(n_toes):
        t = (i - (n_toes - 1) / 2) / max(1, (n_toes - 1) / 2)
        tx = c[0] + t * spread
        ty = c[1] + pad_ry * 0.55 - abs(t) * 1.2
        toes.append((tx, ty, t))
    for tx, ty, t in toes:
        claw(cv, (tx + t * 0.6, ty + toe_r * 0.6), (t * 0.35, 1.0), claw_len, claw_w, curl=-0.4 * t)
    m = ell(c[0], c[1], pad_rx, pad_ry)
    for tx, ty, t in toes:
        m |= ell(tx, ty, toe_r, toe_r * 0.95)
    cv.part(m, 'fur', ('sphere', c[0] - 3, c[1] - 4, pad_rx + 4, pad_ry + 5, 0.05), TH_B)
    inner = erode(m, 1)
    # toe separations: short dark lines between adjacent toes, rising from the bottom edge
    for (ax, ay, _), (bx, by, _) in zip(toes, toes[1:]):
        x = int(round((ax + bx) / 2 - 0.5))
        ybot = max(y for (xx, y) in m if xx == x) if any(xx == x for (xx, _) in m) else int(c[1] + pad_ry)
        for y in range(ybot - 3, ybot + 1):
            if (x, y) in inner:
                cv.put(x, y, PALC['u'] if y < ybot - 1 else BLACK)
    return m


def front_leg(cv, P, side):
    f, g, fx = side_fn(side)
    sh, el, wr, pw = f([P['f_sh'], P['f_el'], P['f_wr'], P['f_paw']])
    upper = capsule(sh, el, 10, 8.5)
    fore = tube([el, ((el[0] + wr[0]) / 2, (el[1] + wr[1]) / 2), wr], [8.4, 7.4, 6.0])
    pm = paw(cv, pw, 4, 6.6, 3.1, 9.2, 6.2, 6.0, 2.2, side)
    cv.part(fore, 'fur', ('cyl', (el[0] - 2, el[1]), (wr[0] - 2, wr[1]), 9, 0.1), TH_B)
    # re-outline the paw top so the wrist sits on it cleanly
    cv.part(upper, 'dark', ('cyl', (sh[0] - 2, sh[1] - 2), (el[0] - 2, el[1] - 2), 11, 0.05), TH_B)
    iu = erode(upper, 1)
    for t in (0.42, 0.78):
        cxp = sh[0] + (el[0] - sh[0]) * t
        cyp = sh[1] + (el[1] - sh[1]) * t
        ang = math.atan2(el[1] - sh[1], el[0] - sh[0]) + math.pi / 2
        a = (cxp - math.cos(ang) * 9, cyp - math.sin(ang) * 9 - 1)
        b = (cxp + math.cos(ang) * 9, cyp + math.sin(ang) * 9 - 1)
        mid = ((a[0] + b[0]) / 2 + (el[0] - sh[0]) * 0.08, (a[1] + b[1]) / 2 + 2)
        crack(cv, [a, mid, b], iu, glow=(t < 0.6))
    # fur cuff: white forearm fur rises over the plate in zig-zag tufts
    ang = math.atan2(wr[1] - el[1], wr[0] - el[0])
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = -uy, ux
    zz = []
    n_teeth = 4
    halfw = 8.6
    for k in range(n_teeth * 2 + 1):
        t = -halfw + (2 * halfw) * k / (n_teeth * 2)
        back = 4.5 if k % 2 == 1 else 0.0
        zz.append((el[0] + px_ * t - ux * back + ux * 1.5, el[1] + py_ * t - uy * back + uy * 1.5))
    lower = [(el[0] + px_ * halfw + ux * 6, el[1] + py_ * halfw + uy * 6), (el[0] - px_ * halfw + ux * 6, el[1] - py_ * halfw + uy * 6)]
    cm = poly(zz + lower) & dilate(upper | fore, 1)
    cv.part(cm, 'fur', ('sphere', el[0] - 4, el[1] - 3, 11, 8, 0.1), TH_B)
    # blend into the forearm: remove outline where cuff meets forearm interior
    fin = erode(fore, 1)
    for q in edge(cm):
        x, y = q
        below = (int(round(x + ux)), int(round(y + uy)))
        if q in fin and below in fin and below not in edge(cm):
            cv.put(x, y, PALC['v'])
    return upper | fore | pm | cm


def hind_leg(cv, P, side):
    f, g, fx = side_fn(side)
    hip, knee, ank, pwc = f([P['h_hip'], P['h_knee'], P['h_ankle'], P['h_paw']])
    pm = paw(cv, pwc, 3, 4.2, 2.6, 6.8, 4.6, 4.6, 1.8, side)
    shin = tube([knee, ((knee[0] + ank[0]) / 2, (knee[1] + ank[1]) / 2), ank], [6.2, 5.4, 4.6])
    cv.part(shin, 'fur', ('cyl', (knee[0] - 1, knee[1]), (ank[0] - 1, ank[1]), 7, 0.1), TH_B)
    thigh = ell(hip[0], hip[1], 10, 11.5, 18 * side)
    cv.part(thigh, 'tan', ('sphere', hip[0] - 3, hip[1] - 4, 12, 14, 0.05), TH_B)
    crack(cv, [(hip[0] - 7, hip[1] + 4), (hip[0], hip[1] + 7), (hip[0] + 7, hip[1] + 5)], erode(thigh, 1), glow=False)


# ------------------------------------------------------------------ tail
TAIL_TIP = """
.........k.........
........kOk........
........kLk........
.......kOLOk.......
.......kOLOk.......
......kOLWLOk......
......kOLWLOk......
.....kOOLWLOOk.....
....koOLWWWLOok....
...kFoOLWWWLOoFk...
..kFooOLWWWLOooFk..
.kFooOOLLWLLOOooFk.
kFFooOOLLLLLOOooFFk
kFoooOOOLLLOOOoooFk
kFFoooOOOLOOOoooFFk
.kFFooooOOOooooFFk.
..kFFFoookoooFFFk..
...kkkFFkQkFFkkk...
......kkkQkkk......
........kQk........
"""


def tail(cv, P):
    path = P['tail_path']
    radii = P['tail_r']
    m = tube(path, radii)
    # dorsal spikes along the outer (convex) side
    sp = catmull(path, 8)
    L = len(sp)
    spikes = set()
    for i in range(6, L - 10, 7):
        (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n        # left normal of travel direction
        # outer side = away from the curve centre (roughly toward the bottom/left of the sprite)
        cxm, cym = 40, 128
        if (sp[i][0] + nx - cxm) ** 2 + (sp[i][1] + ny - cym) ** 2 < (sp[i][0] - nx - cxm) ** 2 + (sp[i][1] - ny - cym) ** 2:
            nx, ny = -nx, -ny
        r = radii[0] + (radii[-1] - radii[0]) * i / L
        base = (sp[i][0] + nx * (r - 1.0), sp[i][1] + ny * (r - 1.0))
        tip = (base[0] + nx * 4.2 - dx / n * 2.0, base[1] + ny * 4.2 - dy / n * 2.0)
        spikes |= poly([(base[0] - dx / n * 2.2, base[1] - dy / n * 2.2), tip, (base[0] + dx / n * 2.2, base[1] + dy / n * 2.2)])
    cv.part(spikes, 'dark', ('dist', 1.5), TH_GLOSS)
    cv.part(m, 'dark', ('dist', 3.6, 0.05), TH_B)
    inner = erode(m, 1)
    # segment lines across the tail every few px
    for i in range(10, L - 4, 9):
        (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n
        r = radii[0] + (radii[-1] - radii[0]) * i / L + 1
        a = (sp[i][0] - nx * r - dx / n * 0.8, sp[i][1] - ny * r - dy / n * 0.8)
        b = (sp[i][0] + nx * r + dx / n * 0.8, sp[i][1] + ny * r + dy / n * 0.8)
        pts = line_px([a, sp[i], b])
        for k, q in enumerate(pts):
            if q in inner:
                cv.put(q[0], q[1], PALC['Z'] if (i // 9) % 2 else PALC['r'])
        if (i // 9) % 2 == 0:
            for q in pts[len(pts) // 3: 2 * len(pts) // 3]:
                if q in inner:
                    cv.put(q[0], q[1], PALC['F'])
    tx, ty = P['tail_tip']
    rows = TAIL_TIP.strip('\n').split('\n')
    w = len(rows[0])
    for dy_, row in enumerate(rows):
        for dx_, ch in enumerate(row):
            if ch == '.':
                continue
            cv.put(int(tx - w // 2 + dx_), int(ty - len(rows) + 1 + dy_), PALC[ch])
    return m


# ------------------------------------------------------------------ wings
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
        d = depth * (0.75 if i == len(chain) - 2 else 1.0)
        c = (mid[0] + (wrist[0] - mid[0]) * d, mid[1] + (wrist[1] - mid[1]) * d)
        arc = qbez(a, c, b, 14)
        scallops.append(arc)
        pts += arc[1:]
    pts += [root, elbow]
    mem = poly(pts)
    rp = RAMPC['wing']
    dedge = chamfer(mem)
    fingers = [(wrist, t) for t in tips]
    arm = [(root, elbow), (elbow, wrist)]
    Lmax = max(math.hypot(t[0] - wrist[0], t[1] - wrist[1]) for t in tips)
    # angle of each finger around the wrist, to find each pixel's panel
    def ang(p):
        return math.atan2(p[1] - wrist[1], (p[0] - wrist[0]) * side)
    fa = [ang(t) for t in tips]
    for (x, y) in mem:
        p = (x + 0.5, y + 0.5)
        r = math.hypot(p[0] - wrist[0], p[1] - wrist[1]) / Lmax
        a = ang(p)
        # panel position: 0 just below the upper finger, 1 just above the lower finger
        idx = 2
        u = None
        for k in range(len(fa) - 1):
            if fa[k] <= a <= fa[k + 1]:
                u = (a - fa[k]) / (fa[k + 1] - fa[k])
        if u is not None:
            if u < 0.10:
                idx = 4
            elif u < 0.22:
                idx = 3
            elif 0.34 < u < 0.66 and r > 0.42:
                idx = 1 if (r > 0.72 and 0.42 < u < 0.58) else 2
            if r < 0.22:
                idx = max(idx, 3)
        else:
            if a > fa[-1]:
                idx = 3 if r > 0.45 else 4
            else:
                idx = 2
        dd = dedge[(x, y)]
        if dd <= 1.6 and r > 0.3:
            idx = 1 if idx >= 2 else 0
        cv.put(x, y, rp[idx])
    # glow on the thinnest part of each scallop
    for arc in scallops:
        n = len(arc)
        for k in range(n // 2 - 2, n // 2 + 3):
            ax_, ay_ = arc[k]
            vx, vy = wrist[0] - ax_, wrist[1] - ay_
            nn = math.hypot(vx, vy) or 1
            for dstep, col in ((1.5, 'P'), (2.6, 'Q')):
                q = (int(ax_ + vx / nn * dstep), int(ay_ + vy / nn * dstep))
                if q in mem and dedge.get(q, 9) <= 2.2:
                    cv.put(q[0], q[1], PALC[col])
    cv.outline(mem)
    # veins: faint dark line down the middle of each panel
    for k in range(len(tips) - 1):
        a = (tips[k][0] + tips[k + 1][0]) / 2, (tips[k][1] + tips[k + 1][1]) / 2
        e = (wrist[0] + (a[0] - wrist[0]) * 0.62, wrist[1] + (a[1] - wrist[1]) * 0.62)
        for q in line_px([(wrist[0] + (a[0] - wrist[0]) * 0.18, wrist[1] + (a[1] - wrist[1]) * 0.18), e]):
            if q in erode(mem, 2):
                cv.put(q[0], q[1], PALC['T'])
    # bones
    for (a, b), r0, r1 in ((arm[0], 3.8, 3.0), (arm[1], 3.0, 2.3)):
        m = capsule(a, b, r0, r1)
        cv.part(m, 'dark', ('cyl', (a[0] - 1, a[1] - 1), (b[0] - 1, b[1] - 1), max(r0, r1) + 0.6), TH_B)
    for (a, b) in fingers:
        m = capsule(a, b, 1.9, 1.0)
        cv.part(m, 'dark', ('cyl', (a[0] - 0.6, a[1] - 0.6), (b[0] - 0.6, b[1] - 0.6), 2.4), TH_B)
    ek = ell(elbow[0], elbow[1], 3.8, 3.8)
    cv.part(ek, 'dark', ('sphere', elbow[0] - 1, elbow[1] - 1, 4, 4), TH_B)
    kn = ell(wrist[0], wrist[1], 3.6, 3.6)
    cv.part(kn, 'dark', ('sphere', wrist[0] - 1, wrist[1] - 1, 3.8, 3.8), TH_B)
    mid = ((wrist[0] + thumb[0]) / 2 + 2.4 * side, (wrist[1] + thumb[1]) / 2 + 0.5)
    m = tube([wrist, mid, thumb], [2.6, 1.8, 0.4])
    cv.part(m, 'dark', ('dist', 2.2), TH_GLOSS)
    for t in tips:
        v = (t[0] - wrist[0], t[1] - wrist[1])
        n = math.hypot(*v)
        e = (t[0] + v[0] / n * 4.0, t[1] + v[1] / n * 4.0)
        m = capsule(t, e, 1.5, 0.35)
        cv.part(m, 'dark', ('dist', 1.3), TH_GLOSS)
    return mem
