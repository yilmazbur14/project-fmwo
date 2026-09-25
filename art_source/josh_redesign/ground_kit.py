"""Parts and tools for Josh's ground animation sheets, on top of josh3 (read-only) and rig.

Every re-posed piece uses the approved sprite's conventions: pure-black keylines cut by stamping,
light from the upper left, the lit near side on the cream ramp 0/9/8 and the far side on 9/8/7.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import josh3                                                       # noqa: E402
import lib                                                         # noqa: E402
import rig                                                         # noqa: E402
from josh3 import capsule                                          # noqa: E402
from lib import Canvas, amap, ellipse, fill, line, paint, poly, rect, rim, stroke  # noqa: E402,F401


#THE SKIRT, WITH ITS ROW TABLE AS A PARAMETER (josh3.skirt, generalised: same colours, same rules)

def skirt_px(rows, trouser_row=None):
    """rows: (y, left outer keyline, left front keyline, right front keyline, right outer keyline,
    lining width). The last row is the hem; the hem keyline goes under it."""
    px = {}
    hem_y = rows[-1][0]
    for (y, lo, lf, rf, ro, lw) in rows:
        hem = (y == hem_y)
        fold_a = int(round(33 - (y - 57) * 2.0 / 13.0)) + (lo - josh3_lo(y))
        fold_b = (35 if y < 66 else 34)
        px[(lo, y)] = 'k'
        for x in range(lo + 1, lf):
            k = '9'
            if x == lo + 1:
                k = '0'
            if x == fold_a:
                k = '8'
            if x == fold_a + 1 and y >= 63:
                k = '7'
            if x == fold_b and y >= 61:
                k = '8'
            if y <= 57 and x <= lo + 4:
                k = '8'
            if hem:
                k = '7' if x in (fold_a, fold_a + 1) else '8'
            if x == lf - 1:
                k = 'o'
            px[(x, y)] = k
        px[(lf, y)] = 'k'
        px[(rf, y)] = 'k'
        x = rf + 1
        px[(x, y)] = 'G'
        lining = 'R' if lw == 1 else ('RV' if lw == 2 else ('RRV' if lw == 3 else 'RRRV'))
        for i, k in enumerate(lining):
            px[(x + 1 + i, y)] = 'V' if hem else k
        for xx in range(x + 1 + lw, ro):
            k = '8'
            if xx == ro - 1:
                k = '7'
            if y >= 62 and xx == ro - 3:
                k = '7'
            if hem:
                k = '7' if xx < ro - 1 else '6'
            px[(xx, y)] = k
        px[(ro, y)] = 'k'
        if y >= 59:
            for xx in range(lf + 1, rf):
                if y <= 60:
                    k = 'n' if xx == 42 else ('s' if xx == lf + 1 else 'N')
                elif xx == 42:
                    k = 'k'
                elif y >= 66 and xx == 43:
                    k = 'v'
                elif xx < 42:
                    k = 's' if xx == lf + 1 else ('n' if xx == 41 else 'N')
                    if y in (62, 63) and xx == lf + 2:
                        k = 'S'
                else:
                    first = 44 if y >= 66 else 43
                    k = 's' if xx == first else ('n' if xx == rf - 1 else 'N')
                    if y in (63, 64) and xx == first + 1:
                        k = 'S'
                px[(xx, y)] = k
    y, lo, lf, rf, ro, lw = rows[-1]
    for x in range(lo, lf + 1):
        px[(x, hem_y + 1)] = 'k'
    for x in range(rf, ro + 1):
        px[(x, hem_y + 1)] = 'k'
    for x, k in zip(range(37, 49), 'sNNnkvsNNNnk'):
        px[(x, hem_y + 1)] = k
    return px


_LO = {r[0]: r[1] for r in josh3.SKIRT_ROWS}


def josh3_lo(y):
    return _LO.get(y, 25)


def sway_rows(dx_by_row, lining_by_row=None):
    """The approved skirt with its outer keylines nudged per row: {y: (dlo, dro)}. The edges stay
    monotonic (a coat panel never tucks back in on its way down), so a sway never notches."""
    out = []
    prev_lo = prev_ro = None
    for (y, lo, lf, rf, ro, lw) in josh3.SKIRT_ROWS:
        dlo, dro = dx_by_row.get(y, (0, 0))
        lo, ro = lo + dlo, ro + dro
        if prev_lo is not None:
            lo = min(lo, prev_lo)
            ro = max(ro, prev_ro)
        prev_lo, prev_ro = lo, ro
        if lining_by_row and y in lining_by_row:
            lw = lining_by_row[y]
        out.append((y, lo, lf, rf, ro, lw))
    return out


def torso_px(rows=None, far_boot=(0, 0), near_boot=(0, 0)):
    """rig.torso_px, with the skirt built from `rows` (the approved table when None) and the boots
    optionally stepped by (dx, dy)."""
    cv = Canvas()
    for c in josh3.collar():
        cv.stamp(c)
    cv.stamp(josh3.coat_back())
    for leg in josh3.legs():
        cv.stamp(leg)
    fb = amap(josh3.BOOT_FAR, 43 + far_boot[0], 72 + far_boot[1])
    nb = amap(josh3.BOOT_NEAR, 34 + near_boot[0], 72 + near_boot[1])
    if far_boot != (0, 0) or near_boot != (0, 0):
        for q in [q for q in cv.px if q[1] >= 72]:
            del cv.px[q]
    cv.stamp(fb, outline=False)
    cv.stamp(nb, outline=False)
    for c in josh3.coat_panels():
        cv.stamp(c)
    cv.stamp(josh3.vest())
    lib.patch(cv.px, josh3.CHEST)
    sk = josh3.skirt() if rows is None else skirt_px(rows)
    for q in [q for q in cv.px if 56 <= q[1] <= 71 and 24 <= q[0] <= 58]:
        del cv.px[q]
    cv.px.update(sk)
    lib.patch(cv.px, josh3.VEST_HEM)
    return dict(cv.px)


#ARMS

NEAR_RAMP = ('9', '0', '8')      # base, lit, shade: the near arm faces the light
FAR_RAMP = ('8', '9', '7')


def segment(p0, p1, r0, r1, ramp, lit_dirs=None):
    base, lit, shade = ramp
    part = fill(capsule(p0, p1, r0, r1), base)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    if lit_dirs is None:
        lit_dirs = [(-1, 0)] if abs(dy) >= abs(dx) else [(0, -1)]
    for d in lit_dirs:
        rim(part, lit, d[0], d[1], only=base)
    for d in lit_dirs:
        rim(part, shade, -d[0], -d[1], only=base)
    return part


def cuff(fore, wrist, elbow, r, key='o', at=1.3, width=0.6):
    ux, uy = elbow[0] - wrist[0], elbow[1] - wrist[1]
    ln = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ln, uy / ln
    a = (wrist[0] + ux * (at - width / 2), wrist[1] + uy * (at - width / 2))
    b = (wrist[0] + ux * (at + width / 2), wrist[1] + uy * (at + width / 2))
    paint(fore, capsule(a, b, r, r), key)


def arm(shoulder, elbow, wrist, near, r=(2.4, 2.1, 1.9), lit_up=None, lit_fore=None, cuff_at=1.3,
        cuff_r=None):
    """Upper arm and forearm as two keylined layers, shaded like the approved arms."""
    ramp = NEAR_RAMP if near else FAR_RAMP
    up = segment(shoulder, elbow, r[0], r[1], ramp, lit_up)
    fo = segment(elbow, wrist, r[1], r[2], ramp, lit_fore)
    if cuff_at is not None:
        cuff(fo, wrist, elbow, cuff_r or r[2], at=cuff_at)
    return [(up, True), (fo, True)]


#HANDS (crimson fingerless gloves, skin fingertips; each map carries its own keyline)

def hand(rows, x0, y0):
    return amap(rows, x0, y0)


#SMALL THINGS

def sparkle(px, x, y, big=True, only_empty=True):
    pts = {(x, y): 'W'}
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pts[(x + dx, y + dy)] = 'Y'
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            pts[(x + dx, y + dy)] = 'O'
    for q, k in pts.items():
        if not only_empty or q not in px:
            px[q] = k


def glint(px, x, y):
    """A two-pixel catch light."""
    px[(x, y)] = 'W'


def glow_ring(px, body, inner='O', outer='r', only_empty=True):
    """The approved gold card's glow: a ring of `inner` round the keyline and `outer` round that."""
    body = set(body)
    ring1 = {}
    for (x, y) in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in body:
                    ring1[q] = inner
    ring2 = {}
    for (x, y) in list(ring1) + list(body):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and q not in ring1:
                ring2[q] = outer
    for q, k in ring2.items():
        if not only_empty or q not in px:
            px[q] = k
    for q, k in ring1.items():
        if not only_empty or q not in px:
            px[q] = k


def put(px, part, only_empty=False):
    for q, k in part.items():
        if not only_empty or q not in px:
            px[q] = k


def clip(px, w=80, h=80):
    return {q: k for q, k in px.items() if 0 <= q[0] < w and 0 <= q[1] < h}


#THE FAN

def fan_spread(dx=-1, dy=-1, split=18):
    """The approved fan with the two back cards (everything left of the ace's keyline at x=split)
    splayed by (dx, dy); the ace, pinned under the thumb, stays. The column the move uncovers takes
    the pixel beside it, so the back cards' edges stay unbroken."""
    fan = lib.amap(josh3.FAN, 6, 34)
    back = {q: k for q, k in fan.items() if q[0] < split}
    front = {q: k for q, k in fan.items() if q[0] >= split}
    moved = {(x + dx, y + dy): k for (x, y), k in back.items()}
    # close the seam against the ace: the back cards' own column next to it, carried across
    for (x, y), k in back.items():
        if x == split - 1:
            q = (x, y + dy)
            if q not in moved:
                moved[q] = k
    # and the rows the move lifted off the bottom
    if dy < 0:
        for (x, y), k in back.items():
            if y == max(yy for (xx, yy) in back if xx == x):
                q = (x + dx, y)
                if q not in moved:
                    moved[q] = k
    out = dict(moved)
    out.update(front)
    return out


#THE APPROVED ARMS, WITH THEIR JOINTS MOVABLE (identical to josh3 at zero offsets)

def near_arm_std(shoulder=(32, 43), elbow=(27, 50), wrist=(21.5, 46.5)):
    up = fill(capsule(shoulder, elbow, 2.4, 2.1), '9')
    rim(up, '0', -1, 0)
    rim(up, '8', 1, 0)
    fo = fill(capsule(elbow, wrist, 2.0, 1.9), '9')
    rim(fo, '0', 0, -1)
    rim(fo, '8', 0, 1)
    ox, oy = wrist[0] - 21.5, wrist[1] - 46.5
    paint(fo, capsule((22.6 + ox, 47.2 + oy), (23.2 + ox, 47.6 + oy), 1.9, 1.9), 'o')
    return [(up, True), (fo, True)]


def far_arm_std(dx=0, dy=0, hand_dx=0, hand_dy=0):
    """josh3.far_arm (fist on the hip), moved; the fist can lag the shoulder."""
    upper = fill(capsule((51 + dx, 43 + dy), (56 + dx, 50 + dy), 2.4, 2.1), '8')
    rim(upper, '9', 0, -1)
    rim(upper, '7', 1, 0)
    wx, wy = 51 + dx + hand_dx, 55 + dy + hand_dy
    fore = fill(capsule((56 + dx, 50 + dy), (wx, wy), 2.1, 1.9), '8')
    rim(fore, '9', 0, -1)
    rim(fore, '7', 0, 1)
    paint(fore, capsule((wx + 1.5, wy - 1.2), (wx + 0.5, wy - 0.2), 1.6, 1.6), 'o')
    hand = amap([
        ".kkk. .",
        "kRTRk .",
        "kRRRV k",
        "kVRRV k",
        ".kVVk .",
    ], 46 + dx + hand_dx, 53 + dy + hand_dy)
    return [(upper, True), (fore, True), (hand, False)]


#FACES: patches on a copy of the approved HEAD, in the approved head's own coordinates
# (y, x0, keys); '_' keeps, '.' erases. Every face keeps his mouth shut: at most a glint of teeth.

FACES = {
    'smirk': [],
    'wink': josh3.WINK,
    # Spans run x = 36-40 | 41-45 | 46-50 (the nose is the 'ded' in the middle group).
    # Approved rows, for reference:
    #   22 jcccc ccccc cccjl    23 deeed ddddd hhhjj    24 hhhhk dedch cccjj
    #   25 dkkkk dedck kkcji    26 d0lk0 dedcl k0cjj    27 dcccd dedbc ccbji
    #   31 icjjj jjjji kciih    32 iiiik kkk00 kiih.    33 iiiii ppbii iiih.
    # narrowed on the target: brows pulled down to the nose, onto the lids
    'focus': [
        (23, 36, "deeed ddddd chhjj"),
        (24, 36, "hhhdd dedhh hccjj"),
        (25, 36, "dkkhh dedck kkcji"),
    ],
    # smug, eyes shut: lids down to a line
    'shut': [
        (25, 36, "ddddd dedcc cccji"),
        (26, 36, "dkkkk dedck kkcjj"),
    ],
    # squeezed shut >  < , teeth clenched, corners pulled down
    'wince': [
        (23, 36, "dhhhe ddddd hhhjj"),
        (24, 36, "dkddd dedcc ckcjj"),
        (25, 36, "ddkkd dedck kccji"),
        (26, 36, "dkddd dedcc ckcjj"),
        (31, 36, "icjjj jjjji jciih"),
        (32, 36, "iiiik 0000k iiih."),
        (33, 36, "iiiki ppbik iiih."),
    ],
    # out of breath: brows up in the middle, heavy lids over unfocused eyes, a tired flat mouth
    'winded': [
        (22, 36, "jcccc cccch hccjl"),
        (23, 36, "dehhh ddddd chhjj"),
        (24, 36, "hhddd dedcc cccjj"),
        (25, 36, "dkkkk dedck kkcji"),
        (26, 36, "ddlkd dedcl kccjj"),
        (27, 36, "dcbbd dedbb bcbji"),
        (31, 36, "icjjj jjjji jciih"),
        (32, 36, "iiiik kk00k kiih."),
    ],
    # knocked silly: brows up, eyes wide, tiny pupils
    'shock': [
        (22, 36, "jhhhh ccccc hhhjl"),
        (23, 36, "deeed ddddd cccjj"),
        (24, 36, "dkkkk dedck kkkjj"),
        (25, 36, "d000k dedc0 00kji"),
        (26, 36, "d0k0k dedc0 k0cjj"),
        (27, 36, "dkkkd dedbk kkbji"),
        (31, 36, "icjjj jjjji jciih"),
        (32, 36, "iiiik k00kk iiih."),
    ],
    # down and out: eyes shut and drooping at the outer corners, mouth flat
    'ko': [
        (24, 36, "hhhhk dedch cccjj"),
        (25, 36, "ddddd dedcc cccji"),
        (26, 36, "kkkkd dedck kkkkj"),
        (27, 36, "kcccd dedbc ccbjk"),
        (31, 36, "icjjj jjjji jciih"),
        (32, 36, "iiiik kkkkk kiih."),
    ],
}


def head(face='smirk', dx=0, dy=0, extra=None):
    """The approved HEAD with an expression patched in, moved by (dx, dy)."""
    px = dict(josh3.head())
    lib.patch(px, FACES[face])
    if extra:
        lib.patch(px, extra)
    return rig.mv(px, dx, dy)


#HAIR UNDER THE HAT: the crown of his head, for when the hat leaves it. Swept back, lit from the left.
HAIR_TOP = [
    (15, 35, "kkkkk kkkkk kkk"),
    (16, 33, "kkijj jjjii iiiik k"),
    (17, 32, "kiljj lljjj iiiii ik"),
    (18, 31, "kmljj ljjji jiiii iihk"),
    (19, 31, "mmljl jjiij iiiji iiihk"),
    (20, 31, "lmmlj jjiii jiiii iiijih"),
]


def hatless(px, dx=0, dy=0):
    """Round off the top of the head where the hat was."""
    for q in [q for q in px if q[1] <= 20 + dy and 29 + dx <= q[0] <= 54 + dx]:
        pass
    lib.patch(px, [(y + dy, x + dx, keys) for (y, x, keys) in HAIR_TOP])


#THE HAT: the approved layers, lifted, tilted (a column shear that reads as a rotation on a wide flat
# brim) or both.

def hat_flat():
    """The approved hat as one part (crown, tucked card, band and brim stamped in order)."""
    cv = Canvas(100, 60)
    for part, outline in rig.hat_layers():
        cv.stamp(part, outline=outline)
    return dict(cv.px)


def hat(dx=0, dy=0, tilt=0, deg=None, pivot=(41, 14)):
    """The hat, moved; tilt > 0 tips the front (right) brim up by about 6 degrees a step, or give
    deg directly (positive turns clockwise). A tilted hat is rotated with RotSprite as one part."""
    if deg is None:
        deg = -6.0 * tilt
    if not deg:
        return rig.mvl(rig.hat_layers(), dx, dy)
    turned = rotate(hat_flat(), deg, pivot)
    # the spade badge re-stamped upright on its turned centre, so it stays crisp
    crown = amap(josh3.CROWN, 32, 5)
    badge = {q: k for q, k in crown.items() if 41 <= q[0] <= 47 and 7 <= q[1] <= 13 and k in 'ok'}
    a = math.radians(deg)
    cx, cy = 44 - pivot[0], 10 - pivot[1]
    nx = pivot[0] + cx * math.cos(a) - cy * math.sin(a)
    ny = pivot[1] + cx * math.sin(a) + cy * math.cos(a)
    ox, oy = int(round(nx - 44)), int(round(ny - 10))
    for (x, y), k in badge.items():
        turned[(x + ox, y + oy)] = k
    return [(rig.mv(turned, dx, dy), False)]


#ROTATION (RotSprite: Scale2x three times, rotate the 8x image by nearest neighbour, sample back)

def _scale2x(grid):
    h, w = len(grid), len(grid[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            p = grid[y][x]
            a = grid[y - 1][x] if y > 0 else p
            b = grid[y][x + 1] if x < w - 1 else p
            c = grid[y][x - 1] if x > 0 else p
            d = grid[y + 1][x] if y < h - 1 else p
            e0 = e1 = e2 = e3 = p
            if c == a and c != d and a != b:
                e0 = a
            if a == b and a != c and b != d:
                e1 = b
            if d == c and d != b and c != a:
                e2 = c
            if b == d and b != a and d != c:
                e3 = d
            out[2 * y][2 * x] = e0
            out[2 * y][2 * x + 1] = e1
            out[2 * y + 1][2 * x] = e2
            out[2 * y + 1][2 * x + 1] = e3
    return out


def rotate(part, deg, pivot, rekey=True):
    """Rotate a part (clockwise for positive deg, in screen space) about pivot (x, y)."""
    if not part:
        return {}
    xs = [q[0] for q in part]
    ys = [q[1] for q in part]
    x0, y0 = min(xs) - 2, min(ys) - 2
    x1, y1 = max(xs) + 2, max(ys) + 2
    w, h = x1 - x0 + 1, y1 - y0 + 1
    grid = [[part.get((x0 + x, y0 + y), '.') for x in range(w)] for y in range(h)]
    big = grid
    for _ in range(3):
        big = _scale2x(big)
    S = 8
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    px, py = pivot
    # output bounds: rotate the corners
    corners = [(x0 - 1, y0 - 1), (x1 + 1, y0 - 1), (x0 - 1, y1 + 1), (x1 + 1, y1 + 1)]
    rc = [(px + (cx - px) * ca - (cy - py) * sa, py + (cx - px) * sa + (cy - py) * ca) for cx, cy in corners]
    ox0, ox1 = int(math.floor(min(c[0] for c in rc))), int(math.ceil(max(c[0] for c in rc)))
    oy0, oy1 = int(math.floor(min(c[1] for c in rc))), int(math.ceil(max(c[1] for c in rc)))
    out = {}
    for oy in range(oy0, oy1 + 1):
        for ox in range(ox0, ox1 + 1):
            # sample the centre of the output pixel, rotated back into the source
            dx, dy = ox - px, oy - py
            sx = px + dx * ca + dy * sa
            sy = py - dx * sa + dy * ca
            bx = int(math.floor((sx - x0 + 0.5) * S))
            by = int(math.floor((sy - y0 + 0.5) * S))
            if 0 <= bx < w * S and 0 <= by < h * S:
                k = big[by][bx]
                if k != '.':
                    out[(ox, oy)] = k
    if rekey:
        out = rekeyline(out)
    return out


def rekeyline(part):
    """After a rotation: drop keyline pixels that no longer touch the inside, and close gaps in the
    outer keyline so it is one pixel and unbroken."""
    body = {q for q, k in part.items() if k != 'k'}
    out = {q: k for q, k in part.items() if k != 'k'}
    for q, k in part.items():
        if k == 'k':
            x, y = q
            touches_body = any((x + dx, y + dy) in body for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            outside = any((x + dx, y + dy) not in part for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            # a stray on the outside goes; solid black inside the shape (a badge, a pip) stays
            if touches_body or not outside:
                out[q] = 'k'
    # any fill pixel on the silhouette's edge gets a keyline outside it
    for (x, y) in list(body):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in out:
                out[q] = 'k'
    return out


#CARDS IN HAND

def small_card(bx, by, angle, w=6, h=8, pip='diamond', face='0', border='9'):
    """A small playing card standing on its bottom-centre point, keylined, with a red pip."""
    pips = {'diamond': ['.R.', 'RRR', '.R.'], 'heart': ['R.R', 'RRR', '.R.'],
            'spade': ['.k.', 'kkk', 'k.k'], None: []}
    return josh3.card(bx, by, angle, w=w, h=h, pip=pips[pip], face=face, border=border)


def keyline(part):
    """A part plus its 1px keyline, as one part (for stamping with outline=False over others)."""
    out = {}
    body = set(part)
    for (x, y) in body:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body:
                out[q] = 'k'
    out.update(part)
    return out


class Lean:
    """A lean of everything above the waist: rows above y0 slide sideways one pixel per `per` rows
    (sign -1 back / left, +1 forward / right). pt() moves a joint with the body."""

    def __init__(self, sign=0, per=8, y0=56):
        self.sign, self.per, self.y0 = sign, per, y0

    def dx(self, y):
        if not self.sign or y >= self.y0:
            return 0
        return self.sign * ((self.y0 - y + self.per - 1) // self.per)

    def torso(self, px):
        return rig.hshear(px, self.y0, self.per, self.sign) if self.sign else px

    def pt(self, x, y):
        return (x + self.dx(int(round(y))), y)


def smear_arc(px, pts, widths, keys=('Y', 'O', 'o'), only_empty=False):
    """An anime smear along a polyline: a band that is `widths[i]` thick at pts[i], cored with the
    first key and edged with the later ones. No keyline, like the approved card glow."""
    import math as _m
    band = {}
    for (x0, y0), (x1, y1), w0, w1 in zip(pts, pts[1:], widths, widths[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        for t in range(n + 1):
            f = t / n
            x = x0 + (x1 - x0) * f
            y = y0 + (y1 - y0) * f
            w = w0 + (w1 - w0) * f
            r = max(0.0, w / 2.0)
            for yy in range(int(_m.floor(y - r - 1)), int(_m.ceil(y + r + 1)) + 1):
                for xx in range(int(_m.floor(x - r - 1)), int(_m.ceil(x + r + 1)) + 1):
                    d = _m.hypot(xx - x, yy - y)
                    if d <= r + 0.35:
                        lvl = 0 if d <= r * 0.35 else (1 if d <= r * 0.75 else 2)
                        cur = band.get((xx, yy))
                        if cur is None or lvl < cur:
                            band[(xx, yy)] = lvl
    for q, lvl in band.items():
        if not only_empty or q not in px:
            px[q] = keys[min(lvl, len(keys) - 1)]


def crescent(px, outer, inner, keys=('G', 'o', 'O', 'Y'), only_empty=False, lead_last=True):
    """A smear crescent between two polylines (outer and inner edge, same direction, start to
    finish). It brightens toward the finish, where the moving thing is now: the tail in keys[0],
    the head in keys[-1] with its outer edge a step darker."""
    import math as _m
    shape = poly(list(outer) + list(reversed(inner)))
    # progress along the arc for each pixel: nearest point on the mid line
    mid = [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b in zip(outer, inner)]
    seg_len = [_m.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(mid, mid[1:])]
    total = sum(seg_len) or 1.0
    for (x, y) in shape:
        best, prog = None, 0.0
        acc = 0.0
        for (a, b), L in zip(zip(mid, mid[1:]), seg_len):
            vx, vy = b[0] - a[0], b[1] - a[1]
            t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - a[0]) * vx + (y - a[1]) * vy) / (L * L)))
            d = _m.hypot(a[0] + vx * t - x, a[1] + vy * t - y)
            if best is None or d < best:
                best, prog = d, (acc + t * L) / total
            acc += L
        lvl = min(len(keys) - 1, int(prog * len(keys)))
        if not only_empty or (x, y) not in px:
            px[(x, y)] = keys[lvl]
    # the outer rim of the head a step down, so the band has an edge
    for (x, y) in shape:
        for dx, dy in ((1, 0), (0, -1), (1, -1)):
            if (x + dx, y + dy) not in shape and px.get((x, y)) == keys[-1]:
                px[(x, y)] = keys[-2]
                break


def card_chain(points, w=5, h=7, pips=None, lean=0.0):
    """A spring of cards: one small keylined card per point, each turned along the chain's line,
    back to front in order. Returns layers."""
    import math as _m
    out = []
    n = len(points)
    for i, (x, y) in enumerate(points):
        a = points[min(i + 1, n - 1)]
        b = points[max(i - 1, 0)]
        ang = _m.degrees(_m.atan2(a[1] - b[1], a[0] - b[0]))
        # the card's long side across the chain: its up points along the normal
        deg = ang + lean
        pip = pips[i % len(pips)] if pips else None
        c = small_card(x, y + h / 2.0, deg, w=w, h=h, pip=pip)
        out.append((keyline(c), False))
    return out


#A CARD FOR ROTATING: upright, 8 x 11 with its keyline, standing on its bottom-centre (x + 3.5, y + 10)

def _face(pip, corner):
    top = ["kkkkkkkk", "k999999k", "k9%s0009k" % corner, "k900009k"]
    mid = ["k90%s9k" % pip[0], "k90%s9k" % pip[1], "k90%s9k" % pip[2]]
    bot = ["k900009k", "k9000%s9k" % corner, "k999999k", "kkkkkkkk"]
    return top + mid + bot


CARD_FACES = {
    'heart': _face(["R0R", "RRR", "0R0"], 'R'),
    'diamond': _face(["0R0", "RRR", "0R0"], 'R'),
    'spade': _face(["0k0", "kkk", "k0k"], 'k'),
    'club': _face(["0k0", "kkk", "0k0"], 'k'),
}


def _face9(pip, corner):
    return (["kkkkkkkkk", "k9999999k", "k9%s00009k" % corner, "k9000009k"]
            + ["k90%s09k" % r for r in pip]
            + ["k9000009k", "k9000009k", "k90000%s9k" % corner, "k9999999k", "kkkkkkkkk"])


CARD_FACES9 = {
    'heart': _face9(["R0R", "RRR", "0R0"], 'R'),
    'diamond': _face9(["0R0", "RRR", "0R0"], 'R'),
    'spade': _face9(["0k0", "kkk", "k0k"], 'k'),
    'club': _face9(["0k0", "kkk", "0k0"], 'k'),
}


def card_up(kind, bx, by, big=False):
    """An upright card whose bottom-centre sits at (bx, by)."""
    rows = (CARD_FACES9 if big else CARD_FACES)[kind]
    w = len(rows[0])
    return amap(rows, int(round(bx - (w - 1) / 2.0)), by - len(rows) + 1)


def big_fan(pivot, angles, kinds, hold=2, big=True):
    """Cards pivoting on one point, back to front, each turned by its angle (0 upright, positive
    leaning right) with RotSprite. `hold` rows of each card sit below the pivot, in the hand."""
    out = []
    px, py = pivot
    for ang, kind in zip(angles, kinds):
        c = card_up(kind, px, py + hold, big=big)
        out.append((rotate(c, ang, (px, py)), False))
    return out


def gold_card_turned(deg, dx=0, dy=0, glow=True, ring=True):
    """josh3's gold card, turned by deg about its centre, with its spade re-stamped upright so it
    stays crisp. Returns layers: glow (optional) then the card."""
    rows = josh3.GOLD_CARD
    card = amap(rows, 55, 22)
    spade = {q: 'k' for q, k in card.items() if k == 'k' and 57 <= q[0] <= 63 and 24 <= q[1] <= 30}
    blank = dict(card)
    for q in spade:
        blank[q] = 'O'
    turned = rotate(blank, deg, (60, 27)) if deg else blank
    # re-centre the spade on the turned card's centre (it is turned about that centre, so it stays)
    for q, k in spade.items():
        turned[q] = k
    out = []
    if glow:
        g = {}
        glow_ring(g, turned, inner='O', outer='r' if ring else 'O')
        out.append((rig.mv(g, dx, dy), False))
    out.append((rig.mv(turned, dx, dy), False))
    return out


#BENT LEGS UNDER THE DUSTER: a parametric lower body for crouches, kneels and hunches.
# Everything is shaded by the approved rules: the near (left) coat panel lit, gold-trimmed on its
# front edge; the far panel in shade with its crimson lining showing; trousers lit on the left.

def trouser(p0, p1, r0, r1, near=True, knee=None):
    part = fill(capsule(p0, p1, r0, r1), 'N')
    rim(part, 's', -1, 0)
    rim(part, 'n', 1, 0)
    if near:
        rim(part, 'S', 0, -1, only='N')
    if knee:
        kx, ky = knee
        for q in [(kx, ky), (kx + 1, ky), (kx, ky + 1)]:
            if q in part:
                part[q] = 'S' if q != (kx, ky) else 't'
    return part


def boot(near, x, y, cut=0):
    """An approved boot, its top `cut` rows sunk out of sight (hidden under the coat)."""
    rows = josh3.BOOT_NEAR if near else josh3.BOOT_FAR
    return amap(rows[cut:], x, y + cut)


def lower_body(W, hem, left, right, knees, ankles, boots_at, lining=3, back=True, hips=((39, 0), (45, 0)),
               boot_cut=(0, 0), fold_left=None, fold_right=None):
    """Layers for the coat skirt, legs and boots below the waist row W.

    left / right: the coat panels as polygons (lists of points), outer edge first then front edge,
    running from the waist down to the hem and back up.
    knees, ankles: ((near x, y), (far x, y)).
    boots_at: ((near x0, y0), (far x0, y0)) for the boot maps.
    """
    L = []
    if back:
        # the inside of the coat hanging behind the legs: lining, darkest up under him
        if isinstance(back, list):
            inside = fill(poly(back), 'v')
        else:
            inside = fill(poly([(37, W + 3), (47, W + 3), (50, hem), (34, hem)]), 'v')
        # the hem of the lining catches a little light
        rim(inside, 'V', 0, 1)
        L.append((inside, True))
    (nk, fk), (na, fa) = knees, ankles
    (nh, fh) = ((hips[0][0], W + 1 + hips[0][1]), (hips[1][0], W + 1 + hips[1][1]))
    # far leg first, then the near one over it
    L.append((trouser(fk, fa, 2.4, 2.1, near=False), True))
    L.append((trouser(fh, fk, 2.7, 2.4, near=False, knee=(fk[0] - 1, fk[1] - 2)), True))
    L.append((boot(False, *boots_at[1], cut=boot_cut[1]), False))
    L.append((trouser(nk, na, 2.4, 2.1, near=True), True))
    L.append((trouser(nh, nk, 2.7, 2.4, near=True, knee=(nk[0] - 1, nk[1] - 2)), True))
    L.append((boot(True, *boots_at[0], cut=boot_cut[0]), False))
    # the far panel: shade, gold trim on its front edge, lining where it swings back
    rp = fill(poly(right), '8')
    rim(rp, '7', 1, 0)
    rim(rp, 'R', -1, 0, depth=lining)
    rim(rp, 'V', -1, 0, depth=1, only='R')
    rim(rp, 'G', -1, 0, depth=1)
    rim(rp, '6', 0, 1, only='87')
    if fold_right:
        stroke(rp, fold_right, '7', only='8')
    L.append((rp, True))
    # the near panel: lit edge, folds, gold trim on the front edge
    lp = fill(poly(left), '9')
    rim(lp, '0', -1, 0)
    rim(lp, 'o', 1, 0)
    rim(lp, '8', 0, 1, only='90')
    if fold_left:
        stroke(lp, fold_left, '8', only='9')
    L.append((lp, True))
    return L


def upper_torso(px, W=56):
    """The rows of a torso layer above the waist row W (collar, lapels, waistcoat, coat tops)."""
    return {q: k for q, k in px.items() if q[1] < W}


#A TILTED HEAD: the features are lifted off, the bare head is turned with RotSprite, and the
# features go back on upright at their turned positions, so eyes and mouth stay one-pixel crisp.

FEATURE_KEYS = set('kh0lpWb')
FEATURE_BOXES = [
    # (x0, y0, x1, y1, what the lifted pixels become)
    (36, 22, 40, 27, 'd'),        # near brow and eye
    (44, 22, 48, 27, 'c'),        # far brow and eye
    (38, 31, 47, 33, 'i'),        # mouth
]


def rot_pt(p, deg, pivot):
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))


def head_rot(face, deg, pivot=(42, 38), hatless_top=False):
    hp = dict(josh3.head())
    lib.patch(hp, FACES[face])
    if hatless_top:
        hatless(hp)
    base = dict(hp)
    feats = []
    for (x0, y0, x1, y1, fillk) in FEATURE_BOXES:
        fp = {}
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                k = hp.get((x, y))
                if k is not None and k in FEATURE_KEYS and not (fillk == 'i' and k == 'b'):
                    fp[(x, y)] = k
                    base[(x, y)] = fillk
        feats.append((((x0 + x1) / 2.0, (y0 + y1) / 2.0), fp))
    out = rotate(base, deg, pivot, rekey=False)
    for (cx, cy), fp in feats:
        nx, ny = rot_pt((cx, cy), deg, pivot)
        ox, oy = int(round(nx - cx)), int(round(ny - cy))
        for (x, y), k in fp.items():
            q = (x + ox, y + oy)
            if q in out:
                out[q] = k
    # the turned head's own keyline comes from stamping it with outline=True
    return {q: k for q, k in out.items() if k != 'k' or any(
        (q[0] + dx, q[1] + dy) in out and out[(q[0] + dx, q[1] + dy)] != 'k'
        for dx in (-1, 0, 1) for dy in (-1, 0, 1))}


def burst(px, cx, cy, r=6, only_empty=False):
    """An impact flash: a white core and eight rays in yellow and gold, no keyline."""
    pts = {}
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if abs(dx) + abs(dy) <= 1:
                pts[(cx + dx, cy + dy)] = 'W'
    for (ux, uy, n) in ((1, 0, r), (-1, 0, r), (0, 1, r - 1), (0, -1, r - 1),
                        (1, 1, r - 3), (-1, 1, r - 3), (1, -1, r - 3), (-1, -1, r - 3)):
        for t in range(2, n + 1):
            k = 'W' if t <= 2 else ('Y' if t <= n - 2 else 'O')
            pts[(cx + ux * t, cy + uy * t)] = k
    for q, k in pts.items():
        if not only_empty or q not in px:
            px[q] = k


def loose_card(kind, cx, cy, deg):
    """A single small card spinning free."""
    c = card_up(kind, cx, cy + 5)
    return rotate(c, deg, (cx, cy))


HAT_CENTRE = (41, 13)


def hat_at(centre, deg=0.0):
    """The hat turned about its own centre and placed with that centre on `centre`."""
    layers = hat(0, 0, deg=deg, pivot=HAT_CENTRE) if deg else rig.hat_layers()
    dx = int(round(centre[0] - HAT_CENTRE[0]))
    dy = int(round(centre[1] - HAT_CENTRE[1]))
    return rig.mvl(layers, dx, dy)


def bbox(layers):
    xs, ys = [], []
    for p, _ in layers:
        for (x, y) in p:
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


SEAL_KEYS = set('abcdehijlmwxyzZVRTnNsStp56789' + '0')


def seal(px, w=80, h=80):
    """Keyline any body pixel left touching transparency (a re-posed part whose edge came out from
    under another). Run on the composed body, before effects, which are meant to glow unkeylined.
    The approved sprite's one open pixel, the dark coat inside between his boots, is left as it is."""
    add = []
    for (x, y), k in px.items():
        if k not in SEAL_KEYS:
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in px and 0 <= q[0] < w and 0 <= q[1] < h:
                add.append(q)
    for q in add:
        px[q] = 'k'
    return px


GLOW_KEYS = set('rOYW')


def fill_pinholes(px):
    """Close one-pixel holes (transparent, drawn on all four sides) that a re-posed part left
    between keylines. The approved sprite's own slits between the popped collar and his neck are
    kept wherever they turn up: collar crimson and neck or beard both within two pixels."""
    add = {}
    for (x, y) in list(px):
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q in px or q in add:
                continue
            qx, qy = q
            n4 = [(qx + 1, qy), (qx - 1, qy), (qx, qy + 1), (qx, qy - 1)]
            if not all(n in px for n in n4):
                continue
            near = [px.get((qx + dx, qy + dy)) for dx in range(-2, 3) for dy in range(-2, 3)]
            if any(k in ('R', 'V') for k in near) and any(k in ('a', 'b', 'i', 'h', 'j') for k in near):
                continue
            glow = [px[n] for n in n4 if px[n] in GLOW_KEYS]
            add[q] = 'O' if glow else 'k'
    px.update(add)
    return px


# Card directions on clean slopes (right vector W, up vector H), for cards set by hand like the
# approved fan's: straight edges, no rotation blur.
SLOPES = {
    'l90': ((0, -8), (-11, 0)),
    'l21': ((4, -8), (-10, -5)),
    'l11': ((6, -6), (-8, -8)),
    'l12': ((8, -4), (-5, -10)),
    'up': ((8, 0), (0, -11)),
    'r12': ((8, 4), (5, -10)),
    'r11': ((6, 6), (8, -8)),
}
PIPS3 = {'diamond': josh3.MARK_DIAMOND, 'spade': josh3.MARK_SPADE, 'heart': josh3.PIP_HEART,
         'club': ['.k.', 'kkk', '.k.']}


def clean_card(pivot, slope, kind):
    """A card whose bottom edge is centred on `pivot`, set on a clean slope, keylined."""
    (wx, wy), (hx, hy) = SLOPES[slope]
    px, py = pivot
    bl = (px - wx / 2.0, py - wy / 2.0)
    br = (bl[0] + wx, bl[1] + wy)
    tr = (br[0] + hx, br[1] + hy)
    tl = (bl[0] + hx, bl[1] + hy)
    corners = [(int(round(x)), int(round(y))) for x, y in (bl, br, tr, tl)]
    return keyline(josh3.card_poly(corners, PIPS3[kind], face='0', border='9'))


def clean_fan(pivot, slopes, kinds):
    return [(clean_card(pivot, s, k), False) for s, k in zip(slopes, kinds)]
