"""Armoured body for beast Bixby: torso with plated flanks + scaled underbelly, shoulders, legs, necks."""
import math
import lib
from lib import *
from pal import PALC, RAMPC, BLACK
from parts import side_fn, sym_poly, offset, mpts


def line_px(path):
    pts = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            q = (int(math.floor(x0 + (x1 - x0) * t)), int(math.floor(y0 + (y1 - y0) * t)))
            if not pts or pts[-1] != q:
                pts.append(q)
    return pts


def crack(cv, path, clip, glow=True):
    """1px lava crack along a polyline, only on non-outline pixels inside clip"""
    pts = line_px(path)
    L = len(pts)
    for i, q in enumerate(pts):
        if q not in clip:
            continue
        c = cv.get(*q)
        if c is None or c == BLACK:
            continue
        t = i / max(1, L - 1)
        if 0.3 < t < 0.7 and glow:
            col = PALC['O'] if i % 3 == 0 else PALC['o']
        elif 0.12 < t < 0.88:
            col = PALC['F']
        else:
            col = PALC['r']
        cv.put(q[0], q[1], col)
    return pts


def torso(cv, P):
    dy = P.get('body_dy', 0)
    O = lambda pts: offset(pts, 0, dy)
    half = O([(96, 76), (86, 77), (76, 80), (67, 86), (60, 94), (58, 104), (61, 114), (68, 122), (76, 130), (85, 136), (96, 139)])
    body = sym_poly(half)
    cv.part(body, 'dark', ('dist', 9.0), TH_B)
    inner = erode(body, 1)
    for side in (1, -1):
        f, g, fx = side_fn(side)
        rows = [
            O([(61, 100), (70, 96), (79, 100), (78, 112), (66, 114), (60, 108)]),
            O([(63, 114), (72, 111), (81, 114), (82, 126), (72, 128), (66, 121)]),
            O([(71, 127), (79, 125), (86, 128), (88, 136), (80, 136), (74, 132)]),
        ]
        for pts in rows:
            m = poly(f(pts)) & inner
            cxm = sum(p[0] for p in pts) / len(pts) - 3
            cym = sum(p[1] for p in pts) / len(pts) - 4
            c = f([(cxm, cym)])[0]
            cv.part(m, 'dark', ('sphere', c[0], c[1], 10, 9, 0.1), TH_B, outline=False)
            lower = f(pts[3:] + pts[:1])
            crack(cv, lower, inner)
    belly = sym_poly(O([(96, 80), (85, 81), (77, 88), (75, 100), (78, 113), (84, 125), (90, 133), (96, 136)])) & body
    cv.part(belly, 'fur', ('sphere', 92, 96 + dy, 26, 40, 0.15), TH_B, outline=True)
    ys = [100, 107, 114, 121, 128, 134]
    eb = edge(belly)
    for i, y0 in enumerate(ys):
        y1 = ys[i + 1] if i + 1 < len(ys) else 139
        seg = poly(O([(60, y0 + 1.5), (96, y0 - 0.5), (132, y0 + 1.5), (132, y1 + 1.5), (96, y1 - 0.5), (60, y1 + 1.5)])) & belly
        seg -= eb
        if not seg:
            continue
        mid = y0 + (y1 - y0) / 2 + dy - 1
        cv.part(seg, 'fur', ('cyl', (60, mid), (132, mid), (y1 - y0) / 1.3, 0.1), TH_B, outline=False)
        for x in range(60, 133):
            yy = int(round(y0 - 0.5 + 2.0 * ((x + 0.5 - 96) / 36) ** 2)) + dy
            if (x, yy) in belly and (x, yy) not in eb:
                cv.put(x, yy, PALC['u'])
    # white fur chest ruff (beagle chest) spilling over the first belly plates in tufts
    tufts = O([(73, 84), (72, 94), (76, 101), (79, 98), (83, 106), (87, 101), (91.5, 109), (96, 104)])
    ruff = sym_poly(O([(96, 79)]) + O([(84, 79.5), (76, 81)]) + tufts)
    cv.part(ruff, 'fur', ('sphere', 86, 82 + dy, 24, 22, 0.3), TH_B)
    ir = erode(ruff, 1)
    for (x0, y0, x1, y1) in ((80, 88, 83, 92), (86, 93, 88, 98), (84, 84, 86, 87)):
        for side in (1, -1):
            for q in line_px([(x0, y0 + dy), (x1, y1 + dy)]):
                qq = q if side > 0 else (191 - q[0], q[1])
                if qq in ir:
                    cv.put(qq[0], qq[1], PALC['v'])
    return body, belly


def shoulder(cv, P, side):
    f, g, fx = side_fn(side)
    dy = P.get('body_dy', 0)
    c = f([P.get('sh_c', (66, 95))])[0]
    c = (c[0], c[1] + dy)
    m = ell(c[0], c[1], 13, 12, -25 * side)
    cv.part(m, 'dark', ('sphere', c[0] - 4, c[1] - 5, 15, 14, 0.05), TH_B)
    inner = erode(m, 1)
    crack(cv, [(c[0] - 10 * side, c[1] + 5), (c[0] - 4 * side, c[1] + 9), (c[0] + 4 * side, c[1] + 10), (c[0] + 10 * side, c[1] + 6)], inner)
    crack(cv, [(c[0] - 9 * side, c[1] - 3), (c[0] - 2 * side, c[1] + 1), (c[0] + 6 * side, c[1] + 1), (c[0] + 11 * side, c[1] - 3)], inner, glow=False)
    return m


def front_leg(cv, P, side):
    f, g, fx = side_fn(side)
    sh, el, wr, pw = f([P['f_sh'], P['f_el'], P['f_wr'], P['f_paw']])
    upper = capsule(sh, el, 10, 8.5)
    fore = capsule(el, wr, 8.2, 7.0)
    paw = ell(pw[0], pw[1], 10, 6.8)
    for dxx in (-7, -2.5, 2.5, 7):
        c = (pw[0] + dxx, pw[1] + 4)
        e = (c[0] + dxx * 0.18, c[1] + 6.5)
        mid = (c[0] + dxx * 0.2 - 0.6 * (1 if dxx < 0 else -1), c[1] + 3.5)
        cm = tube([c, mid, e], [2.3, 1.6, 0.4])
        cv.part(cm, 'dark', ('dist', 1.8), TH_GLOSS)
    cv.part(fore | paw, 'fur', ('cyl', (el[0] - 2, el[1]), (wr[0] - 2, wr[1]), 9, 0.1), TH_B)
    ip = erode(paw, 1)
    for dxx in (-4.5, 0, 4.5):
        x = int(pw[0] + dxx)
        for yy in range(int(pw[1] + 1), int(pw[1] + 6)):
            if (x, yy) in ip:
                cv.put(x, yy, PALC['u'])
    cv.part(upper, 'dark', ('cyl', (sh[0] - 2, sh[1] - 2), (el[0] - 2, el[1] - 2), 11, 0.05), TH_B)
    iu = erode(upper, 1)
    for t in (0.45, 0.8):
        cxp = sh[0] + (el[0] - sh[0]) * t
        cyp = sh[1] + (el[1] - sh[1]) * t
        ang = math.atan2(el[1] - sh[1], el[0] - sh[0]) + math.pi / 2
        a = (cxp - math.cos(ang) * 9, cyp - math.sin(ang) * 9 - 1)
        b = (cxp + math.cos(ang) * 9, cyp + math.sin(ang) * 9 - 1)
        mid = ((a[0] + b[0]) / 2 + (el[0] - sh[0]) * 0.08, (a[1] + b[1]) / 2 + 2)
        crack(cv, [a, mid, b], iu, glow=(t < 0.6))
    ang = math.atan2(wr[1] - el[1], wr[0] - el[0])
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = -uy, ux
    for k in (-5, -2, 1, 4):
        base = (el[0] + px_ * k + ux * 3, el[1] + py_ * k + uy * 3)
        tip = (base[0] - ux * 4 + px_ * 0.8, base[1] - uy * 4 + py_ * 0.8)
        tm = capsule(base, tip, 1.8, 0.5) & dilate(upper, 1)
        cv.part(tm, 'fur', ('dist', 1.5), TH_B, outline=False)
    return upper | fore | paw


def side_neck(cv, P, side):
    """furry side neck rising from the shoulder; base ends in fur tufts over the shoulder plate"""
    f, g, fx = side_fn(side)
    a, b = f([P['sn_base'], P['sn_top']])
    ax, ay = b[0] - a[0], b[1] - a[1]
    L = math.hypot(ax, ay)
    ux, uy = ax / L, ay / L            # base -> top
    px_, py_ = -uy, ux
    R0, R1 = 9.5, 8.5
    m = capsule(a, b, R0, R1)
    # cut the round base: keep pixels beyond a line 3px up the axis, then add tuft teeth below that line
    cut_c = (a[0] + ux * 3, a[1] + uy * 3)
    keep = {q for q in m if ((q[0] + 0.5 - cut_c[0]) * ux + (q[1] + 0.5 - cut_c[1]) * uy) > 0}
    teeth = []
    n = 4
    for k in range(n * 2 + 1):
        t = -R0 + 2 * R0 * k / (n * 2)
        back = 5.0 if k % 2 == 1 else 0.0
        teeth.append((cut_c[0] + px_ * t - ux * back, cut_c[1] + py_ * t - uy * back))
    tuft = poly(teeth + [(cut_c[0] + px_ * R0 + ux * 2, cut_c[1] + py_ * R0 + uy * 2), (cut_c[0] - px_ * R0 + ux * 2, cut_c[1] - py_ * R0 + uy * 2)])
    nm = keep | tuft
    cv.part(nm, 'fur', ('cyl', (a[0] - 2, a[1] - 2), (b[0] - 2, b[1] - 2), 11, 0.1), TH_B)
    nx, ny = px_, py_
    if ny > 0:
        nx, ny = -nx, -ny
    back = poly([(a[0] + nx * 11, a[1] + ny * 11), (b[0] + nx * 9, b[1] + ny * 9), (b[0] + nx * 3, b[1] + ny * 3), (a[0] + nx * 4, a[1] + ny * 4)])
    cv.recolor(back & erode(nm, 1), 'tan', ('cyl', a, b, 10), TH_B)
    return nm


def hind_leg(cv, P, side):
    f, g, fx = side_fn(side)
    hip, knee, ank, paw = f([P['h_hip'], P['h_knee'], P['h_ankle'], P['h_paw']])
    for dxx in (-4, 0, 4):
        c = (paw[0] + dxx, paw[1] + 3)
        e = (c[0] + dxx * 0.25, c[1] + 5)
        cm = capsule(c, e, 1.7, 0.45)
        cv.part(cm, 'dark', ('dist', 1.4), TH_GLOSS)
    shin = capsule(knee, ank, 6, 4.8)
    pw = ell(paw[0], paw[1], 7, 4.8)
    cv.part(shin | pw, 'fur', ('cyl', (knee[0] - 1, knee[1]), (ank[0] - 1, ank[1]), 7, 0.1), TH_B)
    thigh = ell(hip[0], hip[1], 10, 11.5, 18 * side)
    cv.part(thigh, 'tan', ('sphere', hip[0] - 3, hip[1] - 4, 12, 14, 0.05), TH_B)
    crack(cv, [(hip[0] - 7, hip[1] + 4), (hip[0], hip[1] + 7), (hip[0] + 7, hip[1] + 5)], erode(thigh, 1), glow=False)
