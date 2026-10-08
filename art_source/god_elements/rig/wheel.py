"""The ELEMENT WHEEL: a 192x192 disc that hangs behind Liam's Avatar-State puppet (its centre - the texel
CORNER (96, 96) - on his float pivot). Four segments, Liam's own element colours, one bold keylined icon each:
    top-left WATER (a drop)   top-right EARTH (a stone with a sprout)
    bottom-left AIR (a swirl) bottom-right FIRE (a flame)
clockwise water -> earth -> fire -> air (the show's own order); opposites face each other across the hub.
The spokes run along the axes, so his cross-shaped body (spread arms, head, legs) hides the spokes and the
four icons sit in the four clear corners. The rim and spokes are the puppets' iron and bone with Jordan's
rune-blue notches: his machine, Liam's elements.

States (frames of element_wheel.png):
  0 rest     every segment at its own tone
  1-4 lit    one segment stopped-on (water, earth, fire, air): lifted a tone, an inner glow line, its icon
             haloed, its quarter of the rim's runes and an outer glow lit; the other three dimmed
  5 spin     the disc mid-spin, smeared into arcs of its own colours with speed lines (motion blur)
  6-7 double two segments lit (fire + air, water + earth), the other two dimmed
"""
import math
from ge_common import *
import le_rig as R
import elements_pal as E

S = 192
CX = CY = 96.0
R_OUT, R_RIM, R_HUB = 90.5, 80.5, 18.5
SPOKE = 2.5
ICON_R = 55.0

# one char per colour across the whole wheel
PALETTE = {
    '#': (0, 0, 0, 255), 'W': E.WATER['W'],
    # iron, bone and runes (the puppet palette, take B)
    'P': PUP['P1'], 'I': PUP['I2'], 'J': PUP['I3'], 'B': PUP['B1'], 'A': PUP['A5'], 'g': PUP['G1'], 'h': PUP['G2'],
    'H': HOT,
    # water
    '0': E.WATER['d'], '1': E.WATER['e'], '2': E.WATER['b'], '3': E.WATER['B'], '4': E.WATER['L'], '5': E.WATER['l'],
    # fire
    'a': E.FIRE['d'], 'b': E.FIRE['e'], 'c': E.FIRE['r'], 'd': E.FIRE['o'], 'e': E.FIRE['y'], 'f': E.FIRE['c'],
    # earth
    'k': E.EARTH['d'], 'l': E.EARTH['n'], 'm': E.EARTH['J'], 'n': E.EARTH['j'], 'o': E.EARTH['i'],
    'p': E.EARTH['D'], 'q': E.EARTH['G'], 'r': E.EARTH['g'],
    # air
    's': E.AIR['d'], 't': E.AIR['t'], 'u': E.AIR['v'], 'v': E.AIR['s'], 'w': E.AIR['p'],
}
SEG = ['water', 'earth', 'fire', 'air']           # quadrant order: TL, TR, BR, BL (clockwise from top-left)
# per element: the field's tones (shadow, base, light, bright) and the icon ramp dark -> light
FIELD = {'water': '0123', 'earth': 'pqrr', 'fire': 'bcde', 'air': 'stvw'}
LIFT = {  # one tone up (the stopped-on segment)
    'water': {'0': '1', '1': '2', '2': '3', '3': '4', '4': '5', '5': 'W'},
    'earth': {'p': 'q', 'q': 'r', 'k': 'l', 'l': 'm', 'm': 'n', 'n': 'o', 'o': 'f'},
    'fire': {'a': 'b', 'b': 'c', 'c': 'd', 'd': 'e', 'e': 'f', 'f': 'W'},
    'air': {'s': 't', 't': 'v', 'u': 'v', 'v': 'w', 'w': 'W'},
}
DROP = {  # one or two tones down (the segments it did not stop on)
    'water': {'1': '0', '2': '1', '3': '2', '4': '2', '5': '3', 'W': '4'},
    'earth': {'q': 'p', 'r': 'q', 'l': 'k', 'm': 'l', 'n': 'm', 'o': 'n'},
    'fire': {'b': 'a', 'c': 'b', 'd': 'c', 'e': 'd', 'f': 'd', 'W': 'e'},
    'air': {'t': 's', 'u': 's', 'v': 't', 'w': 'u', 'W': 'v'},
}
BRIGHT = {'water': '5', 'earth': 'r', 'fire': 'f', 'air': 'W'}     # the glow line on a lit segment
HALO = {'water': '4', 'earth': 'r', 'fire': 'e', 'air': 'w'}       # the glow round a lit icon / outside the rim

YY, XX = np.mgrid[0:S, 0:S]
X = XX + 0.5 - CX
Y = YY + 0.5 - CY
RR = np.hypot(X, Y)
TH = np.arctan2(Y, X)
LIGHT = np.array(R.LIGHT) / np.linalg.norm(R.LIGHT)


def quad_of(x, y):
    return np.where(y < 0, np.where(x < 0, 0, 1), np.where(x >= 0, 2, 3))


QUAD = quad_of(X, Y)
ICON_AT = {}
for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
    ICON_AT[SEG[i]] = (CX + sx * ICON_R / math.sqrt(2), CY + sy * ICON_R / math.sqrt(2))


# ------------------------------------------------------------------ regions and keylines
def regions():
    reg = np.zeros((S, S), int)                    # 0 air
    disc = RR <= R_OUT
    reg[disc] = 1                                   # rim
    field = disc & (RR <= R_RIM)
    reg[field] = 10 + QUAD[field]                   # segments 10..13
    spoke = field & ((np.abs(X) <= SPOKE) | (np.abs(Y) <= SPOKE))
    reg[spoke] = 3
    reg[RR <= R_HUB] = 2
    return reg


def keylines(reg):
    """A one-texel black line on every boundary, on the higher-numbered side (air is 0, so the outer edge
    is on the disc)."""
    k = np.zeros((S, S), bool)
    P_ = np.pad(reg, 1, constant_values=0)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = P_[1 + dy:S + 1 + dy, 1 + dx:S + 1 + dx]
        k |= (nb != reg) & (reg > nb)
    return k & (reg > 0)


# ------------------------------------------------------------------ the parts
def rim(cv, reg):
    m = reg == 1
    mid = (R_OUT + R_RIM) / 2
    half = (R_OUT - R_RIM) / 2 + 0.6
    t = np.clip((RR - mid) / half, -0.99, 0.99)
    nx, ny = np.cos(TH) * t, np.sin(TH) * t
    nz = np.sqrt(1 - t * t)
    v = np.maximum(0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])
    ch = R.quant(v, 'PIJB', [0.30, 0.62, 0.93])
    cv[m] = ch[m]
    # the rune notches: 7 a quarter, between the studs
    for q in range(4):
        for k in range(7):
            a = math.radians(q * 90 + 11.25 * (k + 1) + (0 if k < 3 else 0))
            if k == 3:
                continue                            # the quarter's middle carries a bigger glyph below
            for rr in np.arange(mid - 2.0, mid + 2.01, 0.25):
                x, y = CX + rr * math.cos(a) - 0.5, CY + rr * math.sin(a) - 0.5
                xi, yi = int(round(x)), int(round(y))
                if m[yi, xi]:
                    cv[yi, xi] = 'g' if abs(rr - mid) < 1.1 else 'h'
        # the quarter's glyph: a rune diamond at 45 degrees into each quarter
        a = math.radians(q * 90 + 45)
        gx, gy = CX + mid * math.cos(a), CY + mid * math.sin(a)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = abs(dx) + abs(dy)
                x, y = int(math.floor(gx + dx)), int(math.floor(gy + dy))
                if m[y, x] and d <= 3:
                    cv[y, x] = '#' if d == 3 else ('g' if d <= 1 else 'h')
    # the bone studs where the spokes meet the rim
    for a in (0, 90, 180, 270):
        sx = CX + mid * math.cos(math.radians(a))
        sy = CY + mid * math.sin(math.radians(a))
        st = np.hypot(XX + 0.5 - sx, YY + 0.5 - sy)
        sm = st <= 3.2
        nx2, ny2 = (XX + 0.5 - sx) / 3.2, (YY + 0.5 - sy) / 3.2
        nz2 = np.sqrt(np.clip(1 - nx2 ** 2 - ny2 ** 2, 0, 1))
        v2 = nx2 * LIGHT[0] + ny2 * LIGHT[1] + nz2 * LIGHT[2]
        cv[sm] = R.quant(v2, 'IAB', [0.35, 0.75])[sm]
        ring = sm & (st > 2.3)
        cv[ring] = '#'


def spokes(cv, reg):
    m = reg == 3
    lit = ((np.abs(X) <= SPOKE) & (X < -0.5)) | ((np.abs(Y) <= SPOKE) & (Y < -0.5))
    dark = ((np.abs(X) <= SPOKE) & (X > 0.5)) | ((np.abs(Y) <= SPOKE) & (Y > 0.5))
    ch = np.where(lit, 'J', np.where(dark, 'P', 'I'))
    cv[m] = ch[m]


def hub(cv, reg):
    m = reg == 2
    t = np.clip(RR / (R_HUB + 0.5), 0, 0.99)
    nz = np.sqrt(1 - t * t)
    v = np.maximum(0, np.cos(TH) * t * LIGHT[0] + np.sin(TH) * t * LIGHT[1] + nz * LIGHT[2])
    cv[m] = R.quant(v, 'PIJ', [0.35, 0.7])[m]
    ring = m & (np.abs(RR - 11.5) < 0.6)
    cv[ring] = 'h'
    ring2 = m & (np.abs(RR - 11.5) < 0.6) & (np.cos(TH * 4) > 0.6)
    cv[ring2] = 'g'


def field(cv, reg):
    for q, el in enumerate(SEG):
        m = reg == 10 + q
        tones = FIELD[el]
        d_edge = np.minimum.reduce([R_RIM - RR, RR - R_HUB, np.abs(X) - SPOKE, np.abs(Y) - SPOKE])
        ch = np.full((S, S), tones[1])
        ch = np.where(d_edge < 3.0, tones[0], ch)
        # the lit band along the rim's inner edge, on the side facing the light
        facing = -(np.cos(TH) * LIGHT[0] + np.sin(TH) * LIGHT[1])     # the inner wall faces inward
        ch = np.where((R_RIM - RR < 5.0) & (R_RIM - RR >= 3.0) & (facing < -0.2), tones[2], ch)
        texture(ch, el, m, tones, d_edge)
        cv[m] = ch[m]


def texture(ch, el, m, tones, d_edge):
    """A sparse pattern of the element in the field's own tones (never at the edges)."""
    inner = m & (d_edge >= 3.0)
    if el == 'water':
        wave = ((YY + np.round(2.2 * np.sin(XX / 5.0))).astype(int) % 9 == 0)
        ch[inner & wave] = tones[2]
        crest = ((YY + np.round(2.2 * np.sin(XX / 5.0))).astype(int) % 9 == 8)
        ch[inner & crest & (np.sin(XX / 5.0) < -0.6)] = tones[0]
    elif el == 'fire':
        # rising heat: wavering vertical streaks, brighter where they lick upward
        w = (XX + np.round(2.0 * np.sin(YY / 4.5))).astype(int)
        ch[inner & (w % 10 == 0)] = tones[2]
        ch[inner & (w % 10 == 0) & (np.sin(YY / 4.5) > 0.7)] = tones[3]
        ch[inner & (w % 10 == 5) & (np.sin(YY / 4.5 + 2.0) > 0.85)] = tones[0]
    elif el == 'earth':
        rnd = np.random.RandomState(4)
        for _ in range(9):                         # cracks
            a = rnd.uniform(-math.pi / 2, 0)
            r0 = rnd.uniform(26, 70)
            x, y = CX + r0 * math.cos(a), CY + r0 * math.sin(a)
            for k in range(rnd.randint(5, 11)):
                xi, yi = int(x), int(y)
                if inner[yi, xi]:
                    ch[yi, xi] = tones[0]
                x += rnd.choice([-1, 0, 1])
                y += rnd.choice([0, 1])
        for _ in range(26):                        # pebbles and moss
            a = rnd.uniform(-math.pi / 2, 0)
            r0 = rnd.uniform(24, 78)
            xi, yi = int(CX + r0 * math.cos(a)), int(CY + r0 * math.sin(a))
            if inner[yi, xi]:
                ch[yi, xi] = tones[2]
    elif el == 'air':
        s = ((XX - YY + np.round(3 * np.sin((XX + YY) / 9.0))).astype(int) % 11 == 0)
        ch[inner & s] = tones[2]
        s2 = ((XX - YY + np.round(3 * np.sin((XX + YY) / 9.0))).astype(int) % 11 == 1)
        ch[inner & s2 & (np.sin((XX + YY) / 9.0) > 0.5)] = tones[3]


# ------------------------------------------------------------------ icons (drawn in an IB x IB box, then placed)
# Each is authored on a 40-unit grid and drawn at K texels a unit (K = IB / 40), so every shape is traced at
# its final size (no rescaled pixels).
IB = 54
K = IB / 40.0


def _k(pts):
    return [(x * K, y * K) for x, y in pts]


def _dots(cv, pts, c, keep='.#'):
    for (x, y) in pts:
        xi, yi = int(math.floor(x * K + 0.5)), int(math.floor(y * K + 0.5))
        if 0 <= xi < IB and 0 <= yi < IB and cv[yi, xi] not in keep:
            cv[yi, xi] = c


def _stroke(cv, pts, r, c, inside=None):
    m = R.polyline_mask(_k(pts), r, IB, IB)
    if inside is not None:
        m &= inside
    cv[m & (cv != '#') & (cv != '.')] = c


def icon_fire():
    cv = R.blank(IB, IB)
    outer = [(19, 38.5), (12, 37.5), (7, 34.5), (4, 29), (3, 24), (4, 19), (6, 15), (8, 10.5), (9.5, 16), (11, 19),
             (12, 14), (14, 9), (17, 4), (19.5, 0), (20.5, 6), (22, 10), (24, 7), (26.5, 2.5), (27.5, 9), (28, 14),
             (30, 11.5), (32.5, 17), (34.5, 22), (34.5, 28), (32.5, 33), (27.5, 37), (23, 38.5)]
    mid = [(19, 37), (14, 36), (11, 33), (9, 29), (9, 25), (11, 21), (13, 24), (15, 19.5), (17, 14), (19.5, 8.5),
           (21, 15), (23, 19), (25.5, 16.5), (27.5, 22), (28, 27), (27, 32), (24, 36)]
    core = [(19, 37), (16, 36), (14, 33), (14, 29), (16, 25), (18, 20), (19.5, 16.5), (21, 22), (23, 26), (24, 30),
            (23, 34), (21, 36)]
    m_o, m_m, m_c = (R.poly_mask(_k(p), IB, IB) for p in (outer, mid, core))
    Xi, Yi = R.centres(IB, IB)
    Xu, Yu = Xi / K, Yi / K
    ch = np.where(Xu > 25 + (Yu - 20) * 0.2, 'd', 'e')
    ch = np.where((Yu > 33.5) & (Xu > 21), 'd', ch)
    R.paint_part(cv, m_o, ch)
    ch = np.where(Xu > 22 + (Yu - 20) * 0.15, 'f', 'W')
    ol = R.outline_pixels(m_m, prune=False)
    cv[m_m & ~ol] = ch[m_m & ~ol]
    cv[m_m & ol] = 'f'
    cc = np.where(Yu > 33.5, 'f', 'W')
    olc = R.outline_pixels(m_c, prune=False)
    cv[m_c] = cc[m_c]
    cv[m_c & olc & (Yu < 33)] = 'W'
    _stroke(cv, [(9, 25), (8.5, 22), (9.5, 19)], 0.7, 'f', inside=m_o & ~m_m)
    _stroke(cv, [(15, 15), (16.5, 11), (18.5, 6)], 0.6, 'f', inside=m_o & ~m_m)
    return cv


def icon_water():
    cv = R.blank(IB, IB)
    Xi, Yi = R.centres(IB, IB)
    body = R.ellipse_mask(20 * K, 26 * K, 12.5 * K, 12.0 * K, IB, IB)
    tip = R.poly_mask(_k([(20, 0.5), (26, 11), (31.5, 19), (8.5, 19), (14, 11)]), IB, IB)
    m = body | tip
    nx, ny, nz = R.sphere_normal(Xi, Yi, 19.0 * K, 24.0 * K, 14.0 * K, 15.0 * K)
    v = R.lambert((nx, ny, nz), wrap=0.25)
    R.paint_part(cv, m, R.quant(v, '1234', [0.22, 0.48, 0.8]))
    # the glint: a white crescent up the left flank, a bright point under it
    _stroke(cv, [(12.6, 25), (12.4, 22), (13.4, 19), (15, 16.5), (16.6, 14)], 0.75, 'W', inside=m)
    _stroke(cv, [(15.5, 22.5), (16.2, 21)], 0.8, '5', inside=m)
    # a wave curling through the drop (the show's water): crest line and its foam
    _stroke(cv, [(10, 31), (13, 29.5), (16, 29.5), (19, 31.5), (22, 32.5), (25, 31), (27.5, 28.5), (29.5, 28)], 0.75, '2',
            inside=m)
    _stroke(cv, [(14, 30.5), (16.5, 30.6)], 0.55, '5', inside=m)
    _stroke(cv, [(25.5, 30.0), (27.5, 29.0)], 0.55, '5', inside=m)
    return cv


def icon_earth():
    cv = R.blank(IB, IB)
    Xi, Yi = R.centres(IB, IB)
    rock = [(5, 36), (3, 29), (5, 21), (10, 16), (16, 13), (24, 12), (31, 15), (35, 22), (37, 30), (35, 36), (26, 38.5),
            (14, 38.5)]
    m = R.poly_mask(_k(rock), IB, IB)
    top = R.poly_mask(_k([(5, 21), (10, 16), (16, 13), (24, 12), (31, 15), (29, 20), (20, 22), (11, 23)]), IB, IB)
    right = R.poly_mask(_k([(29, 20), (31, 15), (35, 22), (37, 30), (35, 36), (26, 38.5), (27, 29)]), IB, IB)
    Yu = Yi / K
    ch = np.full((IB, IB), 'n')
    ch = np.where(right, 'l', ch)
    ch = np.where(top, 'o', ch)
    ch = np.where(Yu > 34.5, np.where(right, 'k', 'm'), ch)
    R.paint_part(cv, m, ch)
    for (a, b) in (((11, 23), (20, 22)), ((20, 22), (29, 20)), ((27, 29), (29, 20)), ((27, 29), (26, 37.5)),
                   ((13, 26.5), (17, 30.5)), ((17, 30.5), (16, 35)), ((31, 25), (33, 30)), ((6.5, 28), (9, 31))):
        R.line(cv, int(round(a[0] * K)), int(round(a[1] * K)), int(round(b[0] * K)), int(round(b[1] * K)), 'k')
    # a lit edge along the top facet's front
    _stroke(cv, [(12, 22.2), (19.5, 21.2), (28, 19.3)], 0.45, 'f', inside=top)
    # the sprout: a stem and two leaves on the crown
    leaf_l = R.poly_mask(_k([(19.5, 9.5), (15, 6), (10.5, 6), (12.5, 9.5), (17, 10.5)]), IB, IB)
    leaf_r = R.poly_mask(_k([(20.5, 8), (24, 2.5), (29.5, 1.5), (28.5, 6), (23, 9)]), IB, IB)
    stem = R.polyline_mask(_k([(20, 12.5), (20, 8)]), 1.4, IB, IB)
    R.paint_part(cv, stem, 'q')
    R.paint_part(cv, leaf_l, np.where(Yu < 7.2, 'r', 'q'))
    R.paint_part(cv, leaf_r, np.where(Xi / K < 25.5, 'r', 'q'))
    return cv


def icon_air():
    """A spiral of wind, one and a half turns, its outer end streaming off as a gust, two gust lines under it."""
    cv = R.blank(IB, IB)
    pts = []
    for i in range(200):
        t = i / 199
        a = 1.55 * 2 * math.pi * t + 3.4
        r = 1.2 + 12.5 * t
        pts.append((19 + r * math.cos(a), 19 + r * math.sin(a)))
    end = pts[-1]
    tail = [(end[0] + k * 1.3, end[1] + k * 0.02) for k in range(1, 12)]
    Xi, Yi = R.centres(IB, IB)
    v = (-(Xi / K - 19) * 0.55 - (Yi / K - 19) * 0.75) / 15.0
    ch = R.quant(v, 'uvwW', [-0.45, -0.05, 0.35])
    for line, r in (([(3, 36), (12, 36.2), (19, 35)], 1.45), ([(22, 37.5), (29, 37.6), (34, 36)], 1.3),
                    (pts + tail, 1.7)):
        R.paint_part(cv, R.polyline_mask(_k(line), r * K, IB, IB), ch)
    return cv


ICONS = {'fire': icon_fire, 'water': icon_water, 'earth': icon_earth, 'air': icon_air}


def place_icon(cv, ic, el, glow=None):
    cx, cy = ICON_AT[el]
    x0, y0 = int(round(cx - IB / 2)), int(round(cy - IB / 2))
    m = ic != '.'
    if glow:
        # a two-texel halo round the icon's keyline, in its lit segment
        P_ = np.pad(m, 2)
        dil1 = np.zeros_like(m)
        dil2 = np.zeros_like(m)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                sh = P_[2 + dy:2 + dy + IB, 2 + dx:2 + dx + IB]
                if abs(dx) + abs(dy) <= 1:
                    dil1 |= sh
                if abs(dx) + abs(dy) <= 3:
                    dil2 |= sh
        for (mm, c) in ((dil2 & ~m, glow[1]), (dil1 & ~m, glow[0])):
            ys, xs = np.nonzero(mm)
            for y, x in zip(ys, xs):
                X_, Y_ = x0 + x, y0 + y
                if cv[Y_, X_] not in '#' and REG[Y_, X_] >= 10:
                    if c == glow[1] and (X_ + Y_) % 2:
                        continue
                    cv[Y_, X_] = c
    for y, x in zip(*np.nonzero(m)):
        cv[y0 + y, x0 + x] = ic[y, x]


REG = regions()
KEY = keylines(REG)


def base():
    cv = np.full((S, S), '.', dtype='<U1')
    rim(cv, REG)
    spokes(cv, REG)
    hub(cv, REG)
    field(cv, REG)
    cv[KEY] = '#'
    return cv


def frame(lit=(), spin=False):
    cv = base()
    seg_of = {el: (REG == 10 + q) for q, el in enumerate(SEG)}
    if lit:
        for q, el in enumerate(SEG):
            m = seg_of[el] & (cv != '#')
            table = LIFT[el] if el in lit else DROP[el]
            cv[m] = np.vectorize(lambda c: table.get(c, c))(cv[m])
        for el in lit:
            # the glow line one texel inside the segment's keyline
            m = seg_of[el]
            P_ = np.pad(KEY, 1)
            nearkey = (P_[:-2, 1:-1] | P_[2:, 1:-1] | P_[1:-1, :-2] | P_[1:-1, 2:]) & ~KEY
            cv[m & nearkey] = BRIGHT[el]
    for el in SEG:
        ic = ICONS[el]()
        if lit and el not in lit:
            ic = np.vectorize(lambda c: DROP[el].get(c, c) if c not in '.#' else c)(ic)
        place_icon(cv, ic, el, glow=(HALO[el], BRIGHT[el]) if el in lit else None)
    if lit:
        # the lit quarter's rim: its runes burn hot, and a glow rings the disc outside it
        for q, el in enumerate(SEG):
            if el not in lit:
                continue
            qm = (QUAD == q) & (REG == 1)
            lift = {'g': 'H', 'h': 'g', 'P': 'I', 'I': 'J', 'J': 'B'}
            cv[qm] = np.vectorize(lambda c: lift.get(c, c))(cv[qm])
            # the glow outside the rim: solid against it, then a dithered fringe, fading at the quarter's ends
            ang = np.degrees(np.abs(((TH - math.radians(-135 + 90 * q)) + math.pi) % (2 * math.pi) - math.pi))
            for (r0, r1, c, dith) in ((R_OUT, R_OUT + 1.3, HALO[el], 0), (R_OUT + 1.3, R_OUT + 2.6, BRIGHT[el], 0),
                                      (R_OUT + 2.6, R_OUT + 4.2, HALO[el], 1)):
                band = (RR > r0) & (RR <= r1) & (QUAD == q) & (ang < (44 if not dith else 38))
                if dith:
                    band &= (XX + YY) % 2 == 0
                cv[band & (cv == '.')] = c
    if spin:
        cv = spin_blur(cv)
    return cv


def to_rgba(cv):
    out = np.zeros((S, S, 4), np.uint8)
    for k, c in PALETTE.items():
        out[cv == k] = c
    return out


def spin_blur(cv):
    """The disc at speed (clockwise): inside the rim the four segments sweep back into a swirl of their own
    base tones; each spoke leaves a dark smear, each icon a streak of its colours, and white speed arcs run
    round it. The rim, the studs and the hub stay sharp (they are the frame it spins in)."""
    out = cv.copy()
    inside = (RR <= R_RIM) & (RR > R_HUB)
    swirl = TH + 0.010 * np.clip(RR - R_HUB, 0, None) ** 1.2         # how far back each radius has swept
    q = quad_of(np.cos(swirl), np.sin(swirl))
    for i, el in enumerate(SEG):
        tones = FIELD[el]
        m = inside & (q == i)
        frac = ((swirl % (math.pi / 2)) / (math.pi / 2))   # 0..1 across the quarter, leading edge last
        ch = np.where(frac > 0.72, tones[2], np.where(frac < 0.12, tones[0], tones[1]))
        out[m] = ch[m]
    # the spokes' smears: a dark arc trailing each spoke's sweep
    edge = np.abs(((swirl + math.pi / 4) % (math.pi / 2)) - math.pi / 4)
    smear = inside & (np.abs(((swirl) % (math.pi / 2))) < 0.05)
    out[smear] = '#'
    # the icons' streaks: at the icon ring, each element trails its colours over 70 degrees
    stripe = {'water': '34W', 'earth': 'mor', 'fire': 'efW', 'air': 'wWv'}
    for i, el in enumerate(SEG):
        a0 = math.radians(-135 + 90 * i)
        for k, (dr, c) in enumerate(((-9, stripe[el][0]), (-4, stripe[el][1]), (0, stripe[el][2]), (4, stripe[el][1]),
                                     (8, stripe[el][0]))):
            span = 70 - abs(dr) * 3
            for t in range(int(span * 3)):
                a = a0 - math.radians(t / 3.0)
                r = ICON_R + dr
                for rr in (r, r + 0.6):
                    x, y = int(math.floor(CX + rr * math.cos(a))), int(math.floor(CY + rr * math.sin(a)))
                    if inside[y, x]:
                        out[y, x] = c
    # white speed arcs
    for r0, a0, span, c in ((27, 20, 70, 'W'), (39, 160, 80, 'w'), (67, 260, 70, 'W'), (73, 60, 50, 'w'),
                            (33, 210, 50, 'w'), (75, 120, 55, 'W'), (24, 300, 45, 'w')):
        for k in range(int(span * 2)):
            a = math.radians(a0 + k * 0.5)
            x, y = int(math.floor(CX + r0 * math.cos(a))), int(math.floor(CY + r0 * math.sin(a)))
            if inside[y, x]:
                out[y, x] = c
    out[KEY & inside] = out[KEY & inside]
    return out


STATES = [('rest', {}), ('lit_water', {'lit': ('water',)}), ('lit_earth', {'lit': ('earth',)}),
          ('lit_fire', {'lit': ('fire',)}), ('lit_air', {'lit': ('air',)}), ('spin', {'spin': True}),
          ('lit_fire_air', {'lit': ('fire', 'air')}), ('lit_water_earth', {'lit': ('water', 'earth')})]


def build():
    return [to_rgba(frame(**kw)) for _n, kw in STATES]


if __name__ == '__main__':
    frames = build()
    im = Image.fromarray(strip(frames), 'RGBA')
    im.save(os.path.join(LOOK, 'wheel_draft.png'))
    up(Image.fromarray(strip(frames[:4]), 'RGBA'), 2, bg=(14, 10, 24, 255)).save(os.path.join(LOOK, 'wheel_draft_a_2x.png'))
    up(Image.fromarray(strip(frames[4:]), 'RGBA'), 2, bg=(14, 10, 24, 255)).save(os.path.join(LOOK, 'wheel_draft_b_2x.png'))
    up(Image.fromarray(frames[0], 'RGBA'), 4, bg=(14, 10, 24, 255)).save(os.path.join(LOOK, 'wheel_rest_4x.png'))
    s = stats(frames[0])
    print('rest: black %.1f%% colours %d semi %d' % (100 * s['black'], s['colours'], s['semi']))
