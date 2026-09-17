"""The player (shirtless boxer, red headband, blue gloves + shorts) seen from behind,
arms raised to the crowd, backlit by the arena spotlights.
Designed shapes (not pillow shading): flat base per part, then light/shadow shapes clipped
to the part, then outlines. Output: role grid ascii + png. A hand-edit patch pass is applied
from player_patch.txt if present (same-size grid, '.' = keep).
python player.py out_prefix"""
import sys, os
from cv import *

PW, PH = 72, 120
AX = 71            # mirror: x' = 71 - x
HERE = os.path.dirname(os.path.abspath(__file__))

ROLE = {
    'k': K,
    'd': BROWN, 's': RUST, 'b': TAN, 'l': SKIN, 'r': WHITE, 'x': WHITE,
    'H': NAVY, 'h': INDIGO, 'j': BLURPLE,
    'R': RED, 'P': PINK, 'Q': PLUM,
    'I': INDIGO, 'B': BLURPLE, 'S': SKY, 'W': PALE,
    'N': NAVY, 'D': DASH, 'G': GREY,
}


def M(m):
    return {(AX - x, y) for (x, y) in m}


def Mp(pts):
    return [(AX + 1 - x, y) for (x, y) in pts]


def sym(poly_left):
    return poly_left + [(AX + 1 - x, y) for (x, y) in reversed(poly_left)]


def P(pts):
    return poly_mask(pts)


def both(pts):
    return P(pts) | P(Mp(pts))


def sh(pts, dx):
    return [(x + dx, y) for (x, y) in pts]


class Fig:
    def __init__(self):
        self.g = {}
        self.part = {}

    def base(self, name, mask, role):
        for p in mask:
            self.g[p] = role
            self.part[p] = name

    def paint(self, name, mask, role):
        for p in mask:
            if self.part.get(p) == name:
                self.g[p] = role

    def mask(self, name):
        return {p for p, n in self.part.items() if n == name}

    def rim(self, name, role, dirs):
        """edge pixels whose outside neighbour lies in one of dirs (x mirrored on the right half)."""
        m = self.mask(name)
        for (x, y) in m:
            for dx, dy in dirs:
                if x > 35:
                    dx = -dx
                if (x + dx, y + dy) not in m:
                    self.g[(x, y)] = role
                    break


def stroke(pts):
    m = set()
    for i in range(len(pts) - 1):
        m |= set(line_pts(*pts[i], *pts[i + 1]))
    return m


UP, DN, LF, RT = (0, -1), (0, 1), (-1, 0), (1, 0)
AS = -2   # arms shifted outward (left side coordinates)


def build():
    f = Fig()
    # ---------------- silhouettes (left side; mirrored) ----------------
    shoeL = [(19, 111), (32, 111), (33, 114), (33, 118), (17, 118), (17, 114)]
    calfL = [(21, 100), (32, 100), (33, 106), (32, 112), (22, 112), (20, 106)]
    shortsL = [(36, 80), (23, 80), (21, 88), (18, 101), (26, 103), (34, 102), (36, 95)]
    torsoL = [(36, 48), (30, 48), (22, 51), (16, 57), (16, 63), (19, 71), (22, 78), (24, 83), (36, 83)]
    upperL = [(6, 38), (12, 35), (18, 38), (24, 44), (29, 48), (31, 54), (27, 60), (20, 60), (13, 54), (8, 47)]
    upperL = [(x + (AS if y < 50 else AS // 2), y) for (x, y) in upperL]
    foreL = sh([(7, 20), (18, 20), (17, 28), (14, 38), (9, 43), (3, 42), (3, 33)], AS)
    gloveL = sh([(5, 5), (8, 1), (14, 0), (19, 2), (21, 6), (21, 12), (19, 17), (17, 19), (8, 19), (4, 15), (3, 10)], AS)
    cuffL = sh([(6, 16), (19, 16), (19, 22), (6, 22)], AS)
    neck = P(sym([(36, 43), (30, 43), (29, 51), (36, 52)]))
    headm = ellipse_mask(36, 35.5, 13, 13)
    spikes = (P([(26, 29), (27, 21), (32, 25)]) | P([(31, 25), (34, 17), (38, 23)]) |
              P([(37, 23), (42, 18), (43, 26)]) | P([(42, 27), (48, 23), (48, 32)]) |
              P([(24, 33), (22, 27), (28, 28)]))
    hair = headm | spikes

    f.base('shoe', P(shoeL) | P(Mp(shoeL)), 'N')
    f.base('calf', P(calfL) | P(Mp(calfL)), 'b')
    f.base('torso', P(sym(torsoL)), 'b')
    f.base('shorts', P(sym(shortsL)), 'B')
    f.base('upper', both(upperL), 'b')
    f.base('fore', both(foreL), 'b')
    f.base('neck', neck, 'b')
    f.base('hair', hair, 'H')
    f.base('cuff', both(cuffL), 'S')
    f.base('glove', both(gloveL), 'B')

    def two(name, pts, role, dx=0):
        pts = sh(pts, dx)
        f.paint(name, P(pts) | P(Mp(pts)), role)

    def two_s(name, pts, role, dx=0):
        m = stroke(sh(pts, dx))
        f.paint(name, m | M(m), role)

    # gloves
    two('glove', [(3, 13), (4, 5), (9, 1), (15, 0), (21, 4), (21, 10), (15, 8), (9, 9)], 'S', AS)
    two('glove', [(7, 4), (10, 2), (14, 2), (12, 4), (8, 6)], 'W', AS)
    two('glove', [(3, 13), (8, 17), (17, 17), (21, 12), (21, 19), (3, 19)], 'I', AS)
    two_s('glove', [(17, 6), (18, 10), (17, 14)], 'I', AS)
    f.rim('glove', 'W', [UP])
    two('cuff', [(5, 20), (20, 20), (20, 23), (5, 23)], 'B', AS)
    two_s('cuff', [(6, 18), (19, 18)], 'W', AS)

    # ---------- skin: axis-following tonal bands, computed on the left half then mirrored ----------
    def left_mask(name):
        return {(x, y) for (x, y) in f.mask(name) if x <= 35}

    def mirror_roles(name):
        for (x, y) in left_mask(name):
            q = (AX - x, y)
            if f.part.get(q) == name:
                f.g[q] = f.g[(x, y)]

    # forearms: rim on the outer edge, lit extensor band, shadow on the inner edge
    fm = left_mask('fore')
    rows_x = {}
    for (x, y) in fm:
        rows_x.setdefault(y, []).append(x)
    for y, xs in rows_x.items():
        x0, x1 = min(xs), max(xs)
        for x in xs:
            dl, dr = x - x0, x1 - x
            r = 'b'
            if dl == 0:
                r = 'l'
            elif 2 <= dl <= 6:
                r = 'l'
            if dr <= 2:
                r = 's'
            if dr == 0 and y < 30:
                r = 'd'
            if y == 23:
                r = 's' if dl > 0 else 'b'       # cuff cast shadow
            f.g[(x, y)] = r
    # upper arms: bands parallel to the arm axis (u = x - y)
    for (x, y) in left_mask('upper'):
        if f.part.get((x, y)) != 'upper':
            continue
        u = x - y
        r = 'b'
        if u >= -24:
            r = 'l'
        elif u >= -27:
            r = 'b'
        elif u >= -31:
            r = 'l' if 42 <= y <= 55 else 'b'     # triceps bulge
        elif u >= -35:
            r = 'b'
        else:
            r = 's'
        if u <= -39:
            r = 'd' if y >= 49 else 's'
        f.g[(x, y)] = r
    # rim + deltoid spec along the top edge (facing the lights)
    um = left_mask('upper')
    for (x, y) in um:
        if f.part.get((x + 1, y)) not in ('upper', 'fore', 'torso') or f.part.get((x, y - 1)) not in ('upper', 'fore', 'torso'):
            if x - y >= -24:
                f.g[(x, y)] = 'r' if 44 <= y <= 49 else 'l'
    # elbow crease at the inner angle
    for (x, y) in [(12, 37), (11, 38), (10, 39), (9, 40)]:
        q = (x + AS, y)
        if f.part.get(q) in ('fore', 'upper'):
            f.g[q] = 'd'
    for (x, y) in [(13, 37), (12, 38), (11, 39), (10, 40)]:
        q = (x + AS, y)
        if f.part.get(q) in ('fore', 'upper'):
            f.g[q] = 's'

    # back: traps, scapulae, spine groove, lats (tonal shapes, tiny deep accents)
    def T(pts, role):
        for p in P(pts):
            if f.part.get(p) == 'torso' and p[0] <= 35:
                f.g[p] = role
    T([(36, 47), (29, 48), (24, 51), (29, 54), (33, 60), (36, 66)], 'l')        # upper + mid traps
    T([(31, 49), (36, 48), (36, 52), (33, 52)], 'r')                            # trap spec near the neck
    T([(22, 56), (27, 54), (32, 58), (33, 63), (29, 67), (23, 66), (20, 61)], 'l')  # scapula
    T([(20, 64), (23, 67), (29, 68), (34, 63), (35, 66), (30, 71), (22, 70), (19, 67)], 's')  # below scapula
    T([(24, 69), (29, 69), (27, 70)], 'd')
    T([(15, 55), (19, 55), (22, 59), (19, 64), (16, 64)], 's')                  # armpit / teres
    T([(16, 57), (18, 57), (19, 61), (17, 62)], 'd')
    T([(34, 58), (36, 58), (36, 80), (34, 80)], 's')                            # spine groove
    T([(35, 68), (36, 68), (36, 80), (35, 80)], 'd')
    T([(29, 71), (33, 70), (33, 79), (29, 79)], 'l')                            # erectors
    T([(17, 66), (20, 66), (24, 78), (22, 80), (19, 72)], 's')                  # lat edge
    T([(21, 76), (26, 76), (29, 80), (22, 80)], 's')                            # waist
    for (x, y) in left_mask('torso'):
        if f.part.get((x - 1, y)) is None and 58 <= y <= 72:
            f.g[(x, y)] = 'l'                                                   # backlit rim on the lat
    T([(22, 79), (36, 79), (36, 80), (22, 80)], 'd')                            # shadow under the waistband

    mirror_roles('fore')
    mirror_roles('upper')
    mirror_roles('torso')

    # neck
    two('neck', [(31, 49), (41, 49), (41, 52), (31, 52)], 's')
    two('neck', [(33, 44), (36, 44), (36, 48), (33, 48)], 'l')

    # hair strands + rim
    hs = lambda pts: f.paint('hair', stroke(pts), 'h')
    hs([(28, 23), (29, 30)]); hs([(34, 19), (33, 29)]); hs([(41, 20), (39, 29)]); hs([(46, 25), (43, 31)])
    hs([(25, 30), (27, 33)]); hs([(26, 40), (28, 45)]); hs([(46, 40), (44, 45)]); hs([(31, 40), (32, 44)])
    hs([(40, 40), (39, 44)])
    f.rim('hair', 'j', [UP, LF])
    # brightest glints on the spike tips and upper crown
    hm = f.mask('hair')
    for (x, y) in hm:
        if (x, y - 1) not in hm and (x - 1, y) not in hm and (x + 1, y) not in hm:
            f.g[(x, y)] = 'S'
    for (x, y) in [(27, 22), (34, 18), (42, 19), (47, 24), (22, 28), (25, 26), (45, 26)]:
        if (x, y) in hm:
            f.g[(x, y)] = 'S'
    nape = P([(28, 46), (32, 48), (36, 46), (40, 48), (44, 46), (44, 51), (28, 51)])
    for p in nape:
        if f.part.get(p) == 'hair':
            f.part[p] = 'neck'
            f.g[p] = 'b'

    # headband
    band = {(x, y) for (x, y) in headm if 33 <= y <= 37}
    for (x, y) in band:
        f.g[(x, y)] = 'R' if 34 <= y <= 36 else ('P' if y == 33 else 'Q')
        f.part[(x, y)] = 'band'

    # ribbon tails (polygons) streaming to the right
    tailA = P([(38, 34), (41, 34), (45, 37), (50, 39), (56, 38), (54, 41), (56, 44), (49, 43), (44, 41), (39, 38)])
    tailB = P([(36, 36), (39, 36), (41, 41), (44, 46), (49, 50), (46, 51), (47, 54), (42, 51), (38, 45), (36, 40)])
    for (tm, name) in ((tailB, 'tailB'), (tailA, 'tailA')):
        for p in tm:
            f.g[p] = 'R'
            f.part[p] = name
        for (x, y) in tm:
            if (x, y - 1) not in tm:
                f.g[(x, y)] = 'P'
            elif (x, y + 1) not in tm:
                f.g[(x, y)] = 'Q'
    KNOT = [
        ".kkkk.",
        "kRPPRk",
        "kRPRQk",
        "kQRRQk",
        ".kkkk.",
    ]
    for j, row in enumerate(KNOT):
        for i, ch in enumerate(row):
            if ch != '.':
                f.g[(33 + i, 32 + j)] = ch
                f.part[(33 + i, 32 + j)] = 'knot'

    # shorts
    f.paint('shorts', P(sym([(36, 80), (23, 80), (22, 85), (36, 85)])), 'S')
    f.paint('shorts', P(sym([(36, 80), (23, 80), (23, 81), (36, 81)])), 'W')
    f.paint('shorts', P(sym([(36, 85), (22, 85), (22, 86), (36, 86)])), 'I')
    two('shorts', [(22, 88), (25, 88), (23, 102), (19, 101)], 'I')
    two_s('shorts', [(35, 93), (33, 102)], 'I')
    two('shorts', [(27, 89), (31, 88), (30, 99), (27, 99)], 'S')
    f.rim('shorts', 'S', [LF])

    # calves
    two('calf', [(23, 102), (28, 101), (30, 106), (27, 110), (23, 108)], 'l')
    two_s('calf', [(31, 101), (31, 111)], 'd')
    f.rim('calf', 'l', [LF])

    # shoes
    two('shoe', [(17, 116), (33, 116), (33, 118), (17, 118)], 'G')
    two_s('shoe', [(20, 112), (25, 112)], 'D')
    two_s('shoe', [(26, 113), (31, 113)], 'D')

    # ---------------- outlines ----------------
    MAT = {'calf': 'skin', 'torso': 'skin', 'upper': 'skin', 'fore': 'skin', 'neck': 'skin',
           'shoe': 'shoe', 'shorts': 'blue', 'hair': 'hair', 'band': 'band', 'knot': 'band',
           'tailA': 'tA', 'tailB': 'tB', 'cuff': 'cuff', 'glove': 'glove'}
    Z = {'shoe': 0, 'calf': 1, 'torso': 2, 'shorts': 3, 'upper': 4, 'fore': 5, 'neck': 6,
         'hair': 8, 'band': 9, 'knot': 12, 'tailB': 10, 'tailA': 11, 'cuff': 9, 'glove': 10}
    union = set(f.g)
    for p in outer_ring(union, N4):
        f.g[p] = 'k'
    lines = set()
    for (x, y), name in list(f.part.items()):
        for dx, dy in N4:
            on = f.part.get((x + dx, y + dy))
            if on and MAT[on] != MAT[name] and Z[on] > Z[name] and not (name == 'hair' and on == 'band'):
                lines.add((x, y))
    for p in lines:
        f.g[p] = 'k'
    return f.g


def to_rows(g):
    return [''.join(g.get((x, y), '.') for x in range(PW)) for y in range(PH)]


def apply_patch(rows, path):
    if not os.path.exists(path):
        return rows
    pr = open(path).read().split('\n')
    out = []
    for y, r in enumerate(rows):
        p = pr[y] if y < len(pr) else ''
        out.append(''.join((p[x] if x < len(p) and p[x] not in '.' else r[x]) if not (x < len(p) and p[x] == '_') else '.'
                           for x in range(len(r))))
    return out


def render(rows):
    cv = Canvas(PW, PH)
    cv.grid(rows, ROLE, 0, 0)
    return cv


def final_rows():
    return apply_patch(to_rows(build()), os.path.join(HERE, 'player_patch.txt'))


if __name__ == '__main__':
    pre = sys.argv[1]
    rows = final_rows()
    open(pre + '.txt', 'w').write('\n'.join(rows) + '\n')
    render(rows).save(pre + '.png')
    print('ok')
