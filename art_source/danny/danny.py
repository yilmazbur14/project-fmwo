"""Danny full-body sprite, 64x64 per frame. Pure python (no PIL).

Pipeline: polygon/capsule silhouettes -> z-composite -> directional bevel
shading (light from upper-left) -> auto 1px black outline -> letter grid ->
hand-authored stamps (face, hands, chain, belly) -> PNG.
All colours are DawnBringer-32.
"""
import math, os, sys, collections
from pngio import write_png, upscale

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 64, 64
AX = 37.0   # continuous mirror axis in design coords (pixel x <-> 73 - x)
DX = 2      # global shift right applied at raster time (room for the pointing hand)

PAL = {
    'K': '#000000',
    # beanie
    'W': '#ffffff', 'C': '#cbdbfc', 'G': '#9badb7', 'g': '#847e87', 'q': '#696a6a',
    # skin (portrait base #eec39a + portrait neck shadow #d9a066)
    'S': '#eec39a', 's': '#d9a066', 'd': '#8f563b', 'D': '#663931',
    # shirt / shorts (portrait base #ac3232 + portrait highlight #d95763)
    'R': '#d95763', 'r': '#ac3232', 'M': '#45283c',
    # chain
    'Y': '#fbf236', 'y': '#df7126', 'o': '#8a6f30',
    # boots
    'B': '#595652', 'b': '#323c39', 'k': '#222034',
    # misc
    'E': '#ffffff', 'n': '#45283c',
}

LEVEL_LETTERS = {
    'skin':   ['S', 'S', 's', 'd'],
    'belly':  ['S', 'S', 's', 'd'],
    'shirt':  ['R', 'r', 'D', 'M'],
    'shorts': ['R', 'r', 'D', 'M'],
    'bw':     ['W', 'W', 'C', 'G'],   # beanie white stripe
    'bg':     ['G', 'G', 'g', 'q'],   # beanie grey stripe
    'boot':   ['B', 'b', 'k', 'k'],
}


def hexc(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def mirror(left):
    right = [(2 * AX - x, y) for (x, y) in reversed(left)]
    return left + right


def mx(pts):
    return [(2 * AX - x, y) for (x, y) in reversed(pts)]


def inside(px, py, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py):
            xint = xi + (py - yi) * (xj - xi) / (yj - yi)
            if px < xint:
                c = not c
        j = i
    return c


def seg_dist(px, py, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L2))
    return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))


def raster(shape):
    if isinstance(shape, list):
        shape = dict(polys=[shape])
    polys = shape.get('polys', [])
    caps = shape.get('caps', [])
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5 - DX, y + 0.5
            hit = any(inside(px, py, p) for p in polys)
            if not hit:
                hit = any(seg_dist(px, py, *c[:4]) <= c[4] for c in caps)
            m[y][x] = hit
    return m


# ------------------------------------------------------------------ SHAPES
REGIONS = []


def region(name, shape, z, group, mat, R=None, light=None, clip=None):
    REGIONS.append(dict(name=name, shape=shape, z=z, group=group, mat=mat, R=R,
                        light=light, clip=clip))


def hem_y(x):
    """shirt hem riding up over the gut: lower in the middle (design x)."""
    return 42.6 - 0.013 * (x + 0.5 - AX) ** 2


HEAD = mirror([
    (37.0, 1.0), (33.0, 1.0), (31.0, 2.0), (29.0, 3.2), (27.5, 4.8),
    (26.3, 6.8), (25.5, 9.0), (25.0, 11.5), (24.8, 15.0), (24.8, 20.0),
    (25.2, 22.5), (26.2, 24.6), (27.8, 26.4), (30.0, 27.8), (32.5, 28.8),
    (35.0, 29.2), (37.0, 29.3),
])

BODY = mirror([
    (37.0, 23.0), (31.0, 23.5), (27.0, 24.6), (24.0, 26.0), (21.6, 27.8),
    (20.2, 30.0), (19.8, 32.5), (20.4, 35.0), (21.0, 37.0), (20.8, 39.5),
    (21.0, 42.0), (22.2, 44.2), (24.4, 46.0), (28.0, 47.2), (32.5, 47.8),
    (37.0, 48.0),
])

SHORTS = [
    (24.5, 44.0), (49.5, 44.0), (50.4, 46.5), (50.8, 49.0), (50.8, 51.6),
    (40.2, 51.6), (38.8, 49.6), (37.0, 49.0), (35.2, 49.6), (33.8, 51.6),
    (23.2, 51.6), (23.2, 49.0), (23.6, 46.5),
]

LEG_L = [(26.4, 50.0), (34.0, 50.0), (33.8, 58.5), (26.8, 58.5)]
LEG_R = mx(LEG_L)

BOOT_L = [(26.0, 55.5), (34.4, 55.5), (34.9, 57.5), (35.2, 60.0), (35.3, 62.5),
          (34.8, 64.0), (23.0, 64.0), (22.2, 63.0), (22.4, 61.6), (23.6, 60.4),
          (25.6, 59.2)]
BOOT_R = mx(BOOT_L)

SLEEVE_R = [(47.5, 25.8), (51.8, 27.0), (54.8, 29.0), (56.4, 32.0), (56.8, 35.0),
            (56.2, 37.2), (50.6, 37.6), (49.2, 34.5), (48.2, 30.5)]
ARM_R = dict(caps=[(53.3, 36.5, 53.8, 43.0, 3.3), (53.8, 43.0, 54.0, 45.5, 3.2)])

SLEEVE_L = [(26.5, 25.8), (22.0, 27.0), (18.5, 28.2), (15.6, 29.4), (14.4, 31.0),
            (14.8, 36.2), (19.0, 37.0), (23.0, 36.8), (25.5, 34.0)]
ARM_L = dict(caps=[(17.0, 33.2, 12.0, 32.8, 2.8), (12.0, 32.8, 8.5, 29.8, 2.6)])

region('leg_l', LEG_L, 1, 'leg_l', 'skin', R=3)
region('leg_r', LEG_R, 1, 'leg_r', 'skin', R=3)
region('boot_l', BOOT_L, 2, 'boot_l', 'boot', R=4)
region('boot_r', BOOT_R, 2, 'boot_r', 'boot', R=4)
region('shorts', SHORTS, 3, 'shorts', 'shorts', R=5)
region('belly', BODY, 3.5, 'belly', 'belly', clip=lambda xd, y: y + 0.5 >= hem_y(xd))
region('body', BODY, 4, 'body', 'shirt', clip=lambda xd, y: y + 0.5 < hem_y(xd))
region('arm_r', ARM_R, 5, 'arm_r', 'skin')
region('sleeve_r', SLEEVE_R, 6, 'sleeve_r', 'shirt', R=4)
region('arm_l', ARM_L, 5, 'arm_l', 'skin')
region('sleeve_l', SLEEVE_L, 6, 'sleeve_l', 'shirt', R=4)
region('head', HEAD, 9, 'head', 'skin')


# ------------------------------------------------------------- COMPOSITE
def composite():
    idm = [[None] * W for _ in range(H)]
    for r in sorted(REGIONS, key=lambda r: r['z']):
        r['mask'] = raster(r['shape'])
        if r['clip']:
            for y in range(H):
                for x in range(W):
                    if r['mask'][y][x] and not r['clip'](x - DX, y):
                        r['mask'][y][x] = False
        for y in range(H):
            for x in range(W):
                if r['mask'][y][x]:
                    idm[y][x] = r
    return idm


def outline_pass(idm):
    out = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            a = idm[y][x]
            if a is None:
                continue
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ddx, y + ddy
                b = idm[ny][nx] if (0 <= nx < W and 0 <= ny < H) else None
                if b is None or (b['group'] != a['group'] and b['z'] < a['z']):
                    out[y][x] = True
                    break
    return out


def dist_map(mask):
    pts = [(x, y) for y in range(H) for x in range(W) if mask[y][x]]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    outside = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
               if not (0 <= x < W and 0 <= y < H and mask[y][x])]
    d = {}
    for (x, y) in pts:
        d[(x, y)] = math.sqrt(min((x - ox) ** 2 + (y - oy) ** 2 for ox, oy in outside))
    return d


U = (0.62, 0.78)   # direction toward shadow (light comes from upper-left)
UN = math.hypot(*U)
U = (U[0] / UN, U[1] / UN)

# per material: (t0, t1, t2, rim_amount, rim_radius)
BANDS = {
    'shirt':  (0.14, 0.80, 1.02, 0.45, 2.5),
    'shorts': (0.04, 0.60, 0.97, 0.35, 2.5),
    'skin':   (-9.0, 0.62, 0.90, 0.42, 2.5),
    'belly':  (-9.0, 0.60, 0.88, 0.50, 2.5),
    'boot':   (0.08, 0.40, 0.62, 0.40, 2.5),
    'beanie': (0.34, 0.62, 0.86, 0.30, 3.0),
}


def shade_region(r, idm):
    d = dist_map(r['mask'])
    pts = list(d.keys())
    proj = {p: p[0] * U[0] + p[1] * U[1] for p in pts}
    lo, hi = min(proj.values()), max(proj.values())
    span = max(hi - lo, 1e-6)
    mat = r['mat']
    t0, t1, t2, amt, Rr = BANDS[mat]
    lev = {}
    tval = {}
    for (x, y) in pts:
        p = (proj[(x, y)] - lo) / span
        gx = d.get((x + 1, y), 0.0) - d.get((x - 1, y), 0.0)
        gy = d.get((x, y + 1), 0.0) - d.get((x, y - 1), 0.0)
        gn = math.hypot(gx, gy)
        s = 0.0 if gn == 0 else -(gx * U[0] + gy * U[1]) / gn
        rim = max(0.0, 1.0 - (d[(x, y)] - 1.0) / Rr)
        t = p + amt * rim * s
        # cast shadow from any part in front of this one (toward the light)
        for step in (1, 2):
            cx = int(round(x - U[0] * step))
            cy = int(round(y - U[1] * step))
            if 0 <= cx < W and 0 <= cy < H:
                o = idm[cy][cx]
                if o is not None and o['z'] > r['z'] and o['group'] != r['group']:
                    t += 0.30 if step == 1 else 0.18
                    break
        tval[(x, y)] = t
        lev[(x, y)] = 0 if t < t0 else 1 if t < t1 else 2 if t < t2 else 3
    r['lev'] = lev
    r['t'] = tval


# beanie geometry (design coords, before DX)
def beanie_is(x, y):
    """True if head pixel (x,y in final pixel coords) belongs to the beanie."""
    xd = x - DX
    face_top = 12.0 + 0.045 * (xd + 0.5 - AX) ** 2
    if y < face_top:
        return True
    # side flaps come down beside the face (portrait)
    if (xd <= 28 or xd >= 45) and y <= 17:
        return True
    return False


def stripe_is_grey(x, y):
    xd = x - DX
    k = (xd - 36) if xd <= 36 else (xd - 37)  # centre pair 36,37 grey
    return (abs(k) % 3) == 0


def build_letters():
    idm = composite()
    for r in REGIONS:
        shade_region(r, idm)
    ol = outline_pass(idm)
    g = [[' '] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            r = idm[y][x]
            if r is None:
                continue
            if ol[y][x]:
                g[y][x] = 'K'
                continue
            lv = r['lev'][(x, y)]
            mat = r['mat']
            if r['name'] == 'head':
                if beanie_is(x, y):
                    t = r['t'][(x, y)]
                    b0, b1, b2 = BANDS['beanie'][:3]
                    lv = 0 if t < b0 else 1 if t < b1 else 2 if t < b2 else 3
                    mat = 'bg' if stripe_is_grey(x, y) else 'bw'
                else:
                    lv = 1  # face is hand-shaded by stamp
            g[y][x] = LEVEL_LETTERS[mat][lv]
    return g


# ------------------------------------------------------------------ STAMPS
def stamp(g, x0, y0, block):
    """block: multi-line string. ' ' or '.' keep, '_' clear, other = letter."""
    lines = block.strip('\n').split('\n')
    for j, line in enumerate(lines):
        for i, ch in enumerate(line):
            if ch in ' .':
                continue
            x, y = x0 + i, y0 + j
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = ' ' if ch == '_' else ch


def S(x0, y0, rows, width):
    for i, r in enumerate(rows):
        assert len(r) == width, 'stamp @(%d,%d) row %d len %d != %d: %r' % (
            x0, y0, i, len(r), width, r)
    return (x0, y0, '\n'.join(rows))


# ---- beanie: cuff fold line (portrait: black arc across the knit)
FOLD = S(27, 7, [
    "........KKKKKKKK........",
    ".....KKK........KKK.....",
    ".KKKK..............KKKK.",
], 24)

# ---- face: rows 12-27.  Portrait features: brows with raised inner ends,
#      thick 2px bar eyes, nose, lopsided pouty frown, wide jaw.
FACE = S(27, 12, [
    "........KKKKKKKK........",   # 12 face-top line under the cuff
    "....KKKKssssssssKKKK....",   # 13 cuff shadow on forehead
    "...KsSSSSSSSSSSSSSssK...",   # 14
    "...KSSSSSKSSSSKSSSssK...",   # 15 brow inner ends (raised)
    "...KSKKKKSSSSSSKKKKsK...",   # 16 brows
    ".KKKSSSSSSSSSSSSSSssKKK.",   # 17 flap bottoms
    ".SSSKKKKKKSSSSKKKKKKssd.",   # 18 eyes
    ".SSSsKKKKsSSSSsKKKKsssd.",   # 19 eyes (heavy lids: lower row narrower)
    ".SSSSssssSSSsSSssssSssd.",   # 20 bags under eyes, nose
    ".SSSSSSSSSSSsSSSSSSSssd.",   # 21 nose
    ".SSSSSSSSSdsdSSSSSSSssd.",   # 22 nose bottom
    ".KSSSSSSSSKKKKSSSSSssdK.",   # 23 mouth
    ".KSSSSSSSKSSSSKSSSSssdK.",   # 24 mouth corners
    "...SSSSSKSSSSSSSSsssd...",   # 25 left corner droops (lopsided)
    ".....SSSSSSssssssdd.....",   # 26 jaw underside
    ".......ssssssdddd.......",   # 27 chin underside
], 24)

# ---- V-neck + gold chain (portrait)
CHAIN = S(33, 29, [
    ".YssssssssY.",
    ".YSSSSSsssy.",
    "..YSSSSssy..",
    "...YSSssy...",
    "....YSsy....",
    ".....Yy.....",
], 12)

# ---- shirt volume: chest fold over the gut + portrait's #d95763 belly-bulge light
SHIRT_VOL = S(23, 28, [
    ".....RR......................",  # 28
    ".....RRR.....................",  # 29
    ".....RR......................",  # 30
    ".....R.......................",  # 31
    ".............................",  # 32
    ".............................",  # 33
    "......DDD...............DDD..",  # 34 fold under chest
    "...RRR...DDD.........DDD.....",  # 35
    "..RRRRR.....D.......D........",  # 36
    ".RRRRR.......................",  # 37
    ".RRR.........................",  # 38
], 29)

# ---- shirt hem riding up, exposed gut with navel (old sprite)
BELLY = S(23, 39, [
    "KKKK........................KKK",
    "KSSSKKKKrrrrrrrrDDDDMMMMKKKKsdK",
    "KSSSssssKKKKKrrrDDMKKKKKssssddK",
    "KSSSSSSSsssssKKKKKKsssssssssddK",
    ".KSSSSSSSSSSSsssssssssssssssddK",
    "..KSSSSSSSSSSSSDssssssssssssdKK",
    "...KKSSSSsssssssssssssdddddKK..",
    "...KrKKKKssssddddddddddKKKKMK..",
], 31)

# ---- pointing hand: fist with index finger extended toward the controls
HAND_L = S(0, 24, [
    ".KKKK........",   # 24 finger top
    "KSSSSKKKK....",   # 25 finger lit top / fist top outline
    "KsssSSSSSK_..",   # 26 finger underside / knuckles
    ".KKKSSSSSSK_.",   # 27 finger bottom outline
    "...KsSSSSSsKK",   # 28 wrist dips on top
    "...KsKSSSSsSS",   # 29 curled-finger crease
    "...KssSSSssSS",   # 30
    "...KsKsSSsdsS",   # 31 second crease
    "....KssssdKsS",   # 32 wrist notch underneath
    ".....KKKKK_KS",   # 33 fist bottom
], 13)

# ---- shorts: belly cast shadow, inner-leg shadow, left-edge highlight
SHORTS_ST = S(25, 47, [
    "KRrrrrDKKKKKKKKKKKKKKDDDDDMK",
    "KRrrrrrrDDDDDKKDDDDDrrrrDDDK",
    "KRrrrrrrrDDDK..KDDrrrrrrDDDK",
    "KRrrrrrrrDDK....KDrrrrrrDDDK",
], 28)

# ---- relaxed hanging hand (his left)
HAND_R = S(52, 44, [
    ".KSSsdK.",
    "KSSSssdK",
    "KSSsssdK",
    "KsSsKsdK",
    ".KssKddK",
    "..KK.KK.",
], 8)

# ---- soften the shadow crescent on the lower-right of the shirt
SHIRT_FIX = S(39, 38, [
    ".......DDDDDD",
    "...DDDDDDDDM.",
    "DDDDDDDM.....",
], 13)

STAMPS = [FOLD, FACE, CHAIN, SHIRT_VOL, BELLY, HAND_L, SHORTS_ST, HAND_R, SHIRT_FIX]

# ---- variant: shirt without the chest fold lines (keeps the belly light)
NO_FOLD = S(29, 34, [
    "rrr...............rrr",
    "...rrr.........rrr...",
    "......r.......r......",
], 21)

# ================================================================ FRAME 1
# talking: mouth open (dark interior), pointing finger tilts up a pixel
MOUTH_OPEN = S(35, 23, [
    "..KKKK.",
    ".KMMMMK",
    "K.KDDK.",
    "...KK..",
], 7)

# left-side fold removed, crease kept only on the shadow side of the chest
FOLD_RIGHT_ONLY = S(29, 34, [
    "rrr..................",
    "...rrr...............",
    "......r.......r......",
], 21)

# sparse dither where the shirt base meets the shadow crescent
SHIRT_DITHER = S(36, 35, [
    "............D...",   # 35
    "..........D.....",   # 36
    ".......D.D......",   # 37
    "......D.D.......",   # 38
    "..D.D...........",   # 39
    ".D..............",   # 40
], 16)

# ---- final cleanup of isolated pixels (orphan scan)
POLISH_PX = [
    (48, 6, 'g'), (48, 7, 'g'), (48, 8, 'g'), (48, 10, 'g'),       # beanie stripe shade
    (31, 14, 's'), (32, 14, 's'), (33, 14, 's'), (34, 14, 's'),    # cuff shadow arc
    (43, 14, 's'), (44, 14, 's'),
    (28, 27, 'R'), (25, 28, 'R'),                                  # shoulder light edge
    (43, 29, 'y'),                                                 # chain shadow strand
    (53, 36, 'D'),                                                 # sleeve underside
    (50, 39, 'D'), (46, 40, 'D'), (41, 41, 'D'),                   # hem accents
    (32, 48, 'D'),                                                 # shorts shadow
    (25, 62, 'k'),                                                 # boot toe
]


class _Px:
    pass


def apply_px(g, lst):
    for x, y, c in lst:
        g[y][x] = c


FRAME0_EXTRA = [FOLD_RIGHT_ONLY]

HAND_L_TALK = S(0, 23, [
    ".KK..........",
    "KSSKK........",
    "KssSSKKKK....",
    "_KKssSSSSK...",
    "___KSSSSSSK..",
], 13)

FRAME1_STAMPS = [MOUTH_OPEN, HAND_L_TALK]
FRAME0_EXTRA = []  # filled below once all stamps are defined

# ---- eye variants (for comparison)
EYES = {
    'A_bars': S(31, 18, [
        "KKKKKK....KKKKKK",
        "KKKKKK....KKKKKK",
    ], 16),
    'B_lid_pupil': S(31, 18, [
        "KKKKKK....KKKKKK",
        "sKKKKs....sKKKKs",
    ], 16),
    'C_lid_white': S(31, 18, [
        "KKKKKK....KKKKKK",
        "SWKKWS....SWKKWS",
    ], 16),
    'D_side_glance': S(31, 18, [
        "KKKKKK....KKKKKK",
        "KKKWWs....KKKWWs",
    ], 16),
}


def to_pix(g):
    pix = [[(0, 0, 0, 0)] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c != ' ':
                pix[y][x] = hexc(PAL[c])
    return pix


def save_views(g, stem):
    pix = to_pix(g)
    write_png(os.path.join(HERE, stem + '_1x.png'), W, H, pix)
    for s in (3, 8):
        w2, h2, p2 = upscale(W, H, pix, s, bg='checker')
        write_png(os.path.join(HERE, '%s_%dx.png' % (stem, s)), w2, h2, p2)


def dump(g, path=None):
    lines = ['    ' + ''.join(str((x // 10) % 10) for x in range(W)),
             '    ' + ''.join(str(x % 10) for x in range(W))]
    for y in range(H):
        lines.append('%3d ' % y + ''.join(g[y]))
    s = '\n'.join(lines)
    if path:
        open(path, 'w').write(s)
    return s


if __name__ == '__main__':
    g = build_letters()
    dump(g, os.path.join(HERE, 'stageB.txt'))
    for (x0, y0, block) in STAMPS:
        stamp(g, x0, y0, block)
    save_views(g, 'stageC')
    print(dump(g, os.path.join(HERE, 'stageC.txt')))
