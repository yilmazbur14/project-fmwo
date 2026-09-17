"""SUPERCHARGED finisher art (DB32 for effects; the player's body stays in its own colours, untouched).
  uppercut_impact_super : 7 frames of 96x96, contact centre (48, 48) - same contract as uppercut_impact.png.
                          Gold + magenta hype energy: bigger burst reaching the frame edge, double shock ring,
                          crowd-roar sound arcs, gold/magenta debris and confetti.
  player_uppercut_super : 10 frames of 48x64, identical to player_uppercut.png except the energy pixels, which
                          are recoloured cyan/blue -> white/gold/magenta. Dust puffs and the body are unchanged.
"""
import sys
sys.dont_write_bytecode = True
import math, os
from dh_common import *

S = 96
CX, CY = 48, 48


# ------------------------------------------------------------------ geometry helpers (as in uppercut impact.py)
def polar_poly_radius(verts, theta_deg):
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
    sp = sorted(((a + rot) % 360, l) for a, l in spikes)
    verts = []
    for k, (a, l) in enumerate(sp):
        verts.append((a, l))
        a_next = sp[(k + 1) % len(sp)][0]
        if a_next <= a:
            a_next += 360
        verts.append(((a + a_next) / 2.0, inner))
    return verts


def fill_polar(c, verts, bands, outline='K'):
    rmax = max(r for _, r in verts) + 2
    inside = set()
    for y in range(int(CY - rmax), int(CY + rmax) + 1):
        for x in range(int(CX - rmax), int(CX + rmax) + 1):
            dx, dy = x - CX, y - CY
            r = math.hypot(dx, dy)
            rb = polar_poly_radius(verts, math.degrees(math.atan2(dy, dx)))
            if r <= rb:
                s = r / rb if rb > 0 else 0.0
                col = bands[-1][1]
                for smax, bc in bands:
                    if s <= smax:
                        col = bc
                        break
                c.set(x, y, C[col])
                inside.add((x, y))
    if outline:
        for (x, y) in list(inside):
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + ddx, y + ddy)
                if p not in inside and c.inb(*p):
                    c.set(p[0], p[1], C[outline])
    return inside


def wedge(c, ang, r0, r1, half_w0, half_w1, cols, cx=CX, cy=CY):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    R = max(r0, r1) + half_w0 + 2
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            px, py = x - cx, y - cy
            along = px * ux + py * uy
            across = px * vx + py * vy
            if r0 <= along <= r1:
                t = (along - r0) / (r1 - r0)
                hw = half_w0 + (half_w1 - half_w0) * t
                if abs(across) <= hw:
                    c.set(x, y, C[cols[min(len(cols) - 1, int(t * len(cols)))]])


def ring(c, r, cols, gaps=(), arc=None):
    th = len(cols)
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - CX, y - CY)
            k = int(math.floor(d - r))
            if 0 <= k < th:
                a = math.degrees(math.atan2(y - CY, x - CX)) % 360
                if any((a0 <= a <= a1) if a0 <= a1 else (a >= a0 or a <= a1) for a0, a1 in gaps):
                    continue
                if arc and not ((arc[0] <= a <= arc[1]) if arc[0] <= arc[1] else (a >= arc[0] or a <= arc[1])):
                    continue
                c.set(x, y, C[cols[k]])


def sparkle(c, x, y, size, core='W', tip='Y'):
    c.set(x, y, C[core])
    for k in range(1, size + 1):
        col = core if k < size else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.set(x + dx, y + dy, C[col])


def stamp_c(c, rows, x, y):
    h, w = len(rows), len(rows[0])
    stamp(c, rows, x - w // 2, y - h // 2)


SHARDS = {
    'gold_big': ["..K..", ".KWK.", "KYWYK", "KOYOK", ".KOK.", "..K.."],
    'mag_big': ["..K..", ".KSK.", "KmWmK", "KVmVK", ".KVK.", "..K.."],
    'gold': ["..K..", ".KYK.", "KYWOK", ".KOK.", "..K.."],
    'mag': [".K.", "KmK", "KVK", ".K."],
    'star': ["..K..", ".KYK.", "KYWYK", ".KYK.", "K.K.K"],
}

# (angle, speed px/frame, kind) - flung mostly upward like the approved impact, but more of them
DEBRIS = [(-98, 11.0, 'gold_big'), (-70, 9.5, 'mag_big'), (-126, 9.0, 'gold'), (-42, 8.5, 'mag'),
          (-152, 8.0, 'gold'), (-12, 8.0, 'mag'), (192, 8.0, 'mag'), (-84, 13.0, 'star'), (-112, 12.5, 'gold'),
          (24, 6.5, 'gold'), (156, 6.5, 'mag_big'), (-58, 12.0, 'star'), (-138, 11.5, 'mag')]


def debris_pos(ang, v, t):
    a = math.radians(ang)
    return (int(round(CX + v * t * math.cos(a))), int(round(CY + v * t * math.sin(a) + 1.1 * t * t)))


# confetti: (start x, start y, drift x per frame, colour, orientation)
CONFETTI = [(14, 20, 1, 'Y', 'h'), (80, 16, -1, 'm', 'v'), (26, 10, 0, 'W', 'v'), (70, 8, 1, 'Y', 'h'),
            (8, 40, 1, 'm', 'h'), (88, 36, -1, 'Y', 'v'), (40, 4, -1, 'm', 'h'), (58, 12, 1, 'W', 'h'),
            (20, 66, 1, 'Y', 'v'), (76, 60, -1, 'm', 'h')]


def confetti(c, f):
    for (x0, y0, dx, col, o) in CONFETTI:
        t = f - 2
        x, y = x0 + dx * t, y0 + 4 * t
        flip = (t + x0) % 2 == 0
        o2 = o if flip else ('v' if o == 'h' else 'h')
        c.set(x, y, C[col])
        if o2 == 'h':
            c.set(x + 1, y, C[col])
        else:
            c.set(x, y + 1, C[col])


def roar_arcs(c, radii, cols, span=(200, 340)):
    """crowd-roar sound arcs: short concentric arc segments above the burst, and mirrored below"""
    for r, col in zip(radii, cols):
        ring(c, r, [col], arc=span)


BIG = [(-90, 50), (-64, 34), (-40, 44), (-14, 32), (12, 42), (38, 28), (64, 36), (90, 30), (116, 36),
       (142, 28), (166, 42), (192, 32), (218, 44), (244, 34)]


def impact_frame(i):
    c = Canvas(S, S)
    if i == 0:
        # contact flash: fat 4-point cross with diagonal nubs, rays already flying
        for ang in (-72, -108, -36, -144, 18, 162, 54, 126):
            wedge(c, ang, 22, 36, 1.6, 0.3, ['W', 'Y', 'O'])
        verts = burst_verts([(-90, 40), (0, 30), (90, 24), (180, 30), (-45, 17), (45, 14), (135, 14), (225, 17)], 11)
        fill_polar(c, verts, [(0.5, 'W'), (0.75, 'Y'), (1.0, 'O')])
    elif i == 1:
        # peak: huge jagged starburst to the frame edge, magenta rim, rays and shards
        for ang, r0, r1 in [(-78, 38, 47), (-102, 38, 47), (-52, 36, 46), (-128, 36, 46), (-26, 36, 45),
                            (-154, 36, 45), (2, 36, 46), (178, 36, 46), (28, 32, 42), (152, 32, 42),
                            (54, 30, 40), (126, 30, 40), (78, 28, 36), (102, 28, 36)]:
            wedge(c, ang, r0, r1, 2.0, 0.4, ['W', 'Y', 'm', 'm'])
        verts = burst_verts(BIG, 17)
        fill_polar(c, verts, [(0.42, 'W'), (0.6, 'Y'), (0.72, 'O'), (0.9, 'm'), (1.0, 'V')])
        sparkle(c, CX, CY - 2, 7, 'W', 'W')
        for (ang, v, kind) in DEBRIS[:7]:
            x, y = debris_pos(ang, v, 2.2)
            stamp_c(c, SHARDS[kind], x, y)
    elif i == 2:
        # burst breaks up: gold inner shock ring + magenta outer ring, detached rays, hot core, debris
        for ang, ln in BIG:
            wedge(c, ang, 36, 36 + ln * 0.3, 2.4, 0.4, ['Y', 'm', 'V'])
        ring(c, 33, ['m', 'm', 'V'], gaps=[(262, 278), (22, 34), (146, 158)])
        ring(c, 22, ['W', 'W', 'Y', 'O'], gaps=[(84, 96), (200, 212), (330, 342)])
        verts = burst_verts([(a, l * 0.36) for a, l in BIG], 8)
        fill_polar(c, verts, [(0.5, 'W'), (0.8, 'Y'), (1.0, 'O')])
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 3.1)
            stamp_c(c, SHARDS[kind], x, y)
        for (x, y) in [(10, 14), (86, 12), (90, 70), (6, 74)]:
            sparkle(c, x, y, 2, 'W', 'Y')
        confetti(c, 2)
    elif i == 3:
        # rings expand; roar arcs bloom above and below; debris flies
        ring(c, 40, ['m', 'V'], gaps=[(250, 290), (10, 30), (150, 170), (84, 96)])
        ring(c, 30, ['Y', 'O'], gaps=[(40, 60), (120, 140), (220, 240), (300, 320)])
        roar_arcs(c, [14, 19], ['Y', 'm'], span=(215, 325))
        roar_arcs(c, [14, 19], ['Y', 'm'], span=(35, 145))
        sparkle(c, CX, CY - 1, 5, 'W', 'Y')
        sparkle(c, CX, CY - 1, 2, 'W', 'W')
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 3.9)
            if kind in ('gold_big', 'gold', 'star'):
                stamp_c(c, [".Y.", "YWO", ".O."], x, y)
            else:
                stamp_c(c, [".m.", "mSV", ".V."], x, y)
        for (x, y) in [(8, 12), (88, 8), (92, 86), (4, 88), (64, 4), (28, 92)]:
            sparkle(c, x, y, 2, 'W', 'm')
        confetti(c, 3)
    elif i == 4:
        ring(c, 45, ['m'], gaps=[(236, 304), (0, 58), (122, 180), (66, 114)])
        roar_arcs(c, [20, 26], ['Y', 'm'], span=(222, 318))
        roar_arcs(c, [20, 26], ['Y', 'm'], span=(42, 138))
        sparkle(c, CX, CY - 1, 3, 'Y', 'O')
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 4.6)
            gold = kind in ('gold_big', 'gold', 'star')
            c.set(x, y, C['Y' if gold else 'm'])
            c.set(x + 1, y, C['O' if gold else 'V'])
        for (x, y) in [(16, 24), (82, 28), (76, 86), (20, 84)]:
            sparkle(c, x, y, 1, 'W', 'Y')
        confetti(c, 4)
    elif i == 5:
        roar_arcs(c, [30], ['m'], span=(232, 308))
        roar_arcs(c, [30], ['m'], span=(52, 128))
        for (ang, v, kind) in DEBRIS:
            x, y = debris_pos(ang, v, 5.2)
            c.set(x, y, C['O' if kind in ('gold_big', 'gold', 'star') else 'V'])
        for (x, y) in [(6, 32), (90, 38), (56, 92), (34, 2), (72, 14)]:
            sparkle(c, x, y, 1, 'Y', 'm')
        c.set(CX, CY - 1, C['Y'])
        confetti(c, 5)
    else:
        for (x, y) in [(12, 50), (84, 54), (46, 6), (60, 90)]:
            sparkle(c, x, y, 1, 'm', 'V')
        confetti(c, 6)
    return c


def impact_super():
    return [impact_frame(i) for i in range(7)]


IMPACT_DURATIONS_MS = [40, 60, 60, 70, 80, 90, 100]


# ------------------------------------------------------------------ player_uppercut_super (recolour)
UPC_DIR = PROJ + 'art_source/uppercut'
ENERGY_MAP = {'ffffff': 'ffffff',   # white core stays white-hot
              'cbdbfc': C['Y'],     # pale blue -> gold
              '5fcde4': C['Y'],     # cyan -> gold
              '639bff': C['O'],     # light blue -> orange
              '5b6ee1': C['m']}     # royal blue -> magenta


def uppercut_layers():
    """(back, body, front) layers from the approved uppercut build, verified against the project PNG"""
    os.environ.setdefault('UPPERCUT_WORK', WORK.rstrip('/') + '/upc_tmp')
    sys.dont_write_bytecode = True
    if UPC_DIR not in sys.path:
        sys.path.insert(0, UPC_DIR)
    import uppercut_build as UB
    frames, layers = UB.build_frames()
    proj = from_png(PROJ + 'Assets/Characters/MainPlayer/player_uppercut.png')
    assert strip(frames).p == proj.p, 'uppercut build no longer matches player_uppercut.png'
    return layers, UB.DURATIONS_MS, UB.TAGS


def is_dust(frame_index, layer, y):
    # take-off (frame 3) and landing (frame 9) dust puffs sit on the ground rows in the back layer
    return layer == 'back' and frame_index in (3, 9) and y >= 54


def uppercut_super():
    layers, durations, tags = uppercut_layers()
    out_frames, out_layers = [], []
    for i, (back, body, front) in enumerate(layers):
        nb, nf = back.copy(), front.copy()
        for name, src, dst in (('back', back, nb), ('front', front, nf)):
            for y in range(src.h):
                for x in range(src.w):
                    v = src.p[y][x]
                    if v and not is_dust(i, name, y):
                        dst.p[y][x] = ENERGY_MAP[v]
        comp = Canvas(48, 64)
        comp.blit(nb, 0, 0)
        comp.blit(body, 0, 0)
        comp.blit(nf, 0, 0)
        out_frames.append(comp)
        out_layers.append((nb, body, nf))
    return out_frames, out_layers, durations, tags


if __name__ == '__main__':
    imp = impact_super()
    s = strip(imp)
    print('impact non-DB32', s.colours() - DB32)
    save_zoom(s, work('impact_super_3x.png'), 3, bg=(40, 40, 56), grid=(96, 96))
    save_zoom(s, work('impact_super_3x_green.png'), 3, bg=(136, 180, 99), grid=(96, 96))
    ref = from_png(PROJ + 'Assets/Effects/uppercut_impact.png')
    save_zoom(ref, work('impact_ref_3x.png'), 3, bg=(40, 40, 56), grid=(96, 96))
    frames, lays, d, t = uppercut_super()
    us = strip(frames)
    save_zoom(us, work('uppercut_super_4x.png'), 4, bg=(70, 70, 90), grid=(48, 64))
    orig = from_png(PROJ + 'Assets/Characters/MainPlayer/player_uppercut.png')
    changed = sum(1 for y in range(us.h) for x in range(us.w) if us.p[y][x] != orig.p[y][x])
    body_changed = sum(1 for y in range(us.h) for x in range(us.w)
                       if orig.p[y][x] in PLAYER_SET and us.p[y][x] != orig.p[y][x])
    print('uppercut recolour: changed px', changed, 'player-palette px changed', body_changed)
