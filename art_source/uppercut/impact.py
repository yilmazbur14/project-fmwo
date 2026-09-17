"""uppercut_impact: 6 frames of 96x96, contact centre (48, 48). DB32 only, alpha 0/255.
Bold jagged starburst with an upward bias (uppercut hits from below), shock ring, radial rays,
debris shards and sparkles."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import Canvas, strip, save_zoom, FX
from paths import work

S = 96
CX, CY = 48, 48
W_, P_, C_, L_, R_, I_, K_, Y_, T_ = FX['W'], FX['P'], FX['C'], FX['L'], FX['R'], FX['I'], FX['K'], FX['Y'], FX['T']
PAL = {'K': K_, 'W': W_, 'P': P_, 'C': C_, 'L': L_, 'R': R_, 'Y': Y_, 'T': T_, 'I': I_}


def polar_poly_radius(verts, theta_deg):
    """verts: list of (angle_deg, radius) sorted by angle (closed). Returns boundary radius at theta."""
    th = theta_deg % 360
    vs = sorted(((a % 360, r) for a, r in verts))
    vs.append((vs[0][0] + 360, vs[0][1]))
    if th < vs[0][0]:
        th += 360
    for (a0, r0), (a1, r1) in zip(vs, vs[1:]):
        if a0 <= th <= a1:
            x0, y0 = r0 * math.cos(math.radians(a0)), r0 * math.sin(math.radians(a0))
            x1, y1 = r1 * math.cos(math.radians(a1)), r1 * math.sin(math.radians(a1))
            dx, dy = math.cos(math.radians(th)), math.sin(math.radians(th))
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                return max(r0, r1)
            return (x0 * ey - y0 * ex) / den
    return vs[0][1]


def burst_verts(spikes, inner, rot=0.0):
    """spikes: list of (angle, length); inner vertices halfway between neighbours"""
    sp = sorted(((a + rot) % 360, l) for a, l in spikes)
    verts = []
    for k, (a, l) in enumerate(sp):
        verts.append((a, l))
        a_next = sp[(k + 1) % len(sp)][0]
        if a_next <= a:
            a_next += 360
        verts.append(((a + a_next) / 2.0, inner))
    return verts


def fill_polar(c, verts, bands, outline=K_, cx=CX, cy=CY, only_empty=False):
    rmax = max(r for _, r in verts) + 2
    inside = set()
    for y in range(int(cy - rmax), int(cy + rmax) + 1):
        for x in range(int(cx - rmax), int(cx + rmax) + 1):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            rb = polar_poly_radius(verts, math.degrees(math.atan2(dy, dx)))
            if r <= rb:
                s = r / rb if rb > 0 else 0.0
                col = bands[-1][1]
                for smax, bc in bands:
                    if s <= smax:
                        col = bc
                        break
                if not (only_empty and c.get(x, y) is not None):
                    c.set(x, y, col)
                inside.add((x, y))
    if outline:
        for (x, y) in list(inside):
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + ddx, y + ddy)
                if p not in inside and c.inb(*p):
                    c.set(p[0], p[1], outline)
    return inside


def wedge(c, ang, r0, r1, half_w0, half_w1, cols, outline=K_):
    """a tapered ray (quad) from radius r0 (width 2*half_w0) to r1 (tip width 2*half_w1).
    cols: colours across the length from inner to outer"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    inside = set()
    xs = [CX + ux * r0 + vx * half_w0, CX + ux * r0 - vx * half_w0, CX + ux * r1 + vx * half_w1,
          CX + ux * r1 - vx * half_w1]
    ys = [CY + uy * r0 + vy * half_w0, CY + uy * r0 - vy * half_w0, CY + uy * r1 + vy * half_w1,
          CY + uy * r1 - vy * half_w1]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px, py = x - CX, y - CY
            along = px * ux + py * uy
            across = px * vx + py * vy
            if r0 <= along <= r1:
                t = (along - r0) / (r1 - r0)
                hw = half_w0 + (half_w1 - half_w0) * t
                if abs(across) <= hw:
                    c.set(x, y, cols[min(len(cols) - 1, int(t * len(cols)))])
                    inside.add((x, y))
    if outline:
        for (x, y) in list(inside):
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + ddx, y + ddy)
                if p not in inside and c.get(*p) is None:
                    c.set(p[0], p[1], outline)
    return inside


def ring(c, r, cols, gaps=(), only_empty=False):
    th = len(cols)
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - CX, y - CY)
            k = int(math.floor(d - r))
            if 0 <= k < th:
                a = math.degrees(math.atan2(y - CY, x - CX)) % 360
                if any((a0 <= a <= a1) if a0 <= a1 else (a >= a0 or a <= a1) for a0, a1 in gaps):
                    continue
                if only_empty and c.get(x, y) is not None:
                    continue
                c.set(x, y, cols[k])


def sparkle(c, x, y, size, core=W_, tip=P_):
    c.set(x, y, core)
    for k in range(1, size + 1):
        col = core if k < size else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.set(x + dx, y + dy, col)


SHARDS = {
    'big': ["..K..", ".KWK.", "KWWPK", "KPCCK", ".KCK.", "..K.."],
    'wide': [".KK..", "KWPKK", "KPCCK", ".KKK."],
    'gold': ["..K..", ".KYK.", "KYWTK", ".KTK.", "..K.."],
    'mid': [".K.", "KWK", "KCK", ".K."],
    'dot': ["KK", "KK"],
}


def stamp(c, rows, x, y, recolor=None):
    h, w = len(rows), len(rows[0])
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            col = PAL[ch]
            if recolor and ch in recolor:
                col = recolor[ch]
            c.set(x - w // 2 + i, y - h // 2 + j, col)


# debris: (angle, speed px/frame, kind); mostly flung upward
DEBRIS = [(-98, 10.5, 'big'), (-68, 9.0, 'gold'), (-128, 8.5, 'wide'), (-40, 8.0, 'mid'), (-150, 7.5, 'gold'),
          (-10, 7.5, 'mid'), (192, 7.5, 'mid'), (-82, 12.5, 'mid'), (-114, 12.0, 'gold'), (25, 6.0, 'mid'),
          (155, 6.0, 'wide')]


def debris_pos(ang, v, t):
    a = math.radians(ang)
    return (int(round(CX + v * t * math.cos(a))),
            int(round(CY + v * t * math.sin(a) + 1.1 * t * t)))


BIG = [(-90, 46), (-62, 30), (-38, 38), (-12, 28), (14, 36), (40, 24), (68, 30), (90, 26), (112, 30),
       (140, 24), (166, 36), (192, 28), (218, 38), (242, 30)]


def frame(i):
    c = Canvas(S, S)
    if i == 0:
        # contact flash: fat 4-point cross burst + hot core
        verts = burst_verts([(-90, 30), (0, 22), (90, 18), (180, 22), (-45, 13), (45, 11), (135, 11), (225, 13)], 9)
        fill_polar(c, verts, [(0.55, W_), (0.8, P_), (1.0, C_)])
        for ang in (-70, -110, -30, -150, 20, 160):
            wedge(c, ang, 20, 30, 1.2, 0.3, [W_, P_, C_], outline=None)
    elif i == 1:
        # peak: huge jagged starburst, rays, shards
        for ang, r0, r1 in [(-78, 34, 46), (-102, 34, 46), (-50, 34, 44), (-130, 34, 44), (-25, 34, 42),
                            (-155, 34, 42), (2, 34, 44), (178, 34, 44), (28, 30, 38), (152, 30, 38),
                            (55, 28, 36), (125, 28, 36)]:
            wedge(c, ang, r0, r1, 1.6, 0.4, [W_, P_, C_, L_], outline=None)
        verts = burst_verts(BIG, 15)
        fill_polar(c, verts, [(0.42, W_), (0.66, W_), (0.8, P_), (0.92, C_), (1.0, L_)])
        # hot core glint
        sparkle(c, CX, CY - 2, 6, W_, W_)
        for (ang, v, kind) in DEBRIS[:6]:
            x, y = debris_pos(ang, v, 2.2)
            stamp(c, SHARDS[kind], x, y)
    elif i == 2:
        # burst breaks up: thick shock ring, detached rays outside it, small hot core
        for ang, ln in BIG:
            wedge(c, ang, 31, 31 + ln * 0.36, 2.2, 0.4, [P_, C_, L_], outline=None)
        ring(c, 23, [W_, W_, P_, C_], gaps=[(262, 278), (30, 42), (138, 150)])
        verts = burst_verts([(a, l * 0.40) for a, l in BIG], 7)
        fill_polar(c, verts, [(0.5, W_), (0.8, P_), (1.0, C_)])
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 3.1)
            stamp(c, SHARDS[kind], x, y)
        for (x, y) in [(12, 18), (84, 14), (88, 72), (8, 76)]:
            sparkle(c, x, y, 2)
    elif i == 3:
        ring(c, 33, [P_, C_, L_], gaps=[(255, 285), (15, 35), (145, 165), (82, 98)])
        for ang, ln in BIG[::2]:
            wedge(c, ang, 40, 40 + ln * 0.16, 1.2, 0.3, [C_, L_], outline=None)
        sparkle(c, CX, CY - 1, 5, W_, P_)
        sparkle(c, CX, CY - 1, 2, W_, W_)
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 3.9)
            if kind == 'gold':
                stamp(c, [".Y.", "YWT", ".T."], x, y)
            else:
                stamp(c, [".P.", "PWC", ".C."], x, y)
        for (x, y) in [(10, 14), (86, 10), (90, 84), (6, 86), (62, 6), (30, 92)]:
            sparkle(c, x, y, 2, P_, C_)
    elif i == 4:
        ring(c, 41, [C_, L_], gaps=[(240, 300), (5, 55), (125, 175), (70, 110)])
        sparkle(c, CX, CY - 1, 3, P_, C_)
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 4.6)
            if kind == 'gold':
                c.set(x, y, Y_)
                c.set(x + 1, y, T_)
            else:
                c.set(x, y, P_)
                c.set(x + 1, y, C_)
        for (x, y) in [(18, 26), (80, 30), (74, 84), (22, 82)]:
            sparkle(c, x, y, 1, P_, C_)
    else:
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 5.2)
            c.set(x, y, T_ if kind == 'gold' else L_)
        for (x, y) in [(8, 34), (88, 40), (58, 92), (36, 2), (70, 16)]:
            sparkle(c, x, y, 1, C_, L_)
        c.set(CX, CY - 1, P_)
    return c


def build():
    return [frame(i) for i in range(6)]


if __name__ == '__main__':
    frames = build()
    s = strip(frames)
    s.save(work('impact_strip.png'))
    save_zoom(s, work('impact_3x.png'), 3, bg=(136, 180, 99), grid=(96, 96))
    print('ok')
