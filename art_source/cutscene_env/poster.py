"""poster_closeup.png (640x360): the MEMBERS WANTED poster on the lit brick wall.

Same poster and neighbouring flyers as street_buildings.png, seen ~7x closer.
Dialogue box covers x 54..586, y 272..356 -> everything that must be read sits above y 262.
"""
import math
from lib import Canvas, bayer, hsh, vnoise, ellipse_mask, boundary, poly_mask, text_width
from fonts import F57, F35
import bold
from type import bitmap, epx, nearest, pixels, paint_text, size

W, H = 640, 360
PX0, PY0, PX1, PY1 = 178, 8, 461, 338
CX = (PX0 + PX1) // 2          # 319

BRICK = ['K', 'N', 'M', 'B', 'w', 'd']
MORTAR = ['K', 'K', 'N', 'N', 'M', 'B']

LAYERS = {}    # name -> Canvas, for the layered .aseprite
OPTS = {'lettering': True}


def light(x, y):
    """0..~2.8 light level: sconce above the poster, falling off to the sides and the bottom."""
    dx = (x - 320.0) / 430.0
    dy = (y + 40.0) / 420.0
    f = max(0.0, 1.0 - dx * dx - dy * dy)
    return 0.55 + 2.35 * f


def level(x, y, bias=0.0):
    L = light(x, y) * 0.8 + bias
    base = int(math.floor(L))
    if bayer(x, y) < (L - base):
        base += 1
    return base


def wall(c):
    """Big bricks, each shaded as a unit from the light at its centre (no per-pixel dither noise)."""
    bw, bh, mort = 56, 26, 4
    for y in range(H):
        row = (y + 9) // bh
        ry = (y + 9) % bh
        off = bw // 2 if row % 2 else 0
        for x in range(W):
            rx = (x + off + 13) % bw
            bi = (x + off + 13) // bw
            # brick centre in screen space
            bcx = bi * bw - off - 13 + (bw - mort) / 2.0
            bcy = row * bh - 9 + (bh - mort) / 2.0
            Lb = light(bcx, bcy) * 0.8
            v = hsh(bi, row, 5)
            lvl = int(math.floor(Lb + (v - 0.5) * 0.6))
            if ry >= bh - mort or rx >= bw - mort:
                Lm = int(math.floor(light(x, y) * 0.8 + 0.2))
                k = MORTAR[max(0, min(5, Lm + 1))]
                if ry == bh - 1 and rx < bw - mort and Lm >= 2:
                    k = MORTAR[max(0, min(5, Lm + 2))]
                c.p[y][x] = k
                continue
            t = lvl + 1
            if ry == 0 or rx == 0:
                t += 1
            elif ry == bh - mort - 1 or rx == bw - mort - 1:
                t -= 1
            h = hsh(x, y, 9)
            if h < 0.010:
                t -= 1
            elif h > 0.996:
                t += 1
            # soft weathering blotch on a few bricks
            if v > 0.86 and ((x - bcx) ** 2 / 90.0 + (y - bcy) ** 2 / 20.0) < 1.0 and bayer(x, y) < 0.5:
                t -= 1
            c.p[y][x] = BRICK[max(0, min(5, t))]
    for (bxx, byy) in ((96, 60), (530, 205), (40, 300), (600, 40)):
        for i in range(5):
            for j in range(5 - i):
                k = c.get(bxx + i, byy + j)
                if k in BRICK and BRICK.index(k) > 0:
                    c.set(bxx + i, byy + j, BRICK[BRICK.index(k) - 1])


def dim(c, x, y, steps=1):
    k = c.get(x, y)
    ramp = ['K', 'N', 'M', 'B', 'w', 'd', 's']
    alt = {'P': 'g', 'g': 'F', 'F': 'D', 'D': 'E', 'E': '6', '6': 'N', 'W': 'P', 'd': 'w', 's': 'd', '8': 'V',
           'V': 'I', 'I': 'N', 'U': 'I', 'A': '5', '5': 'N', '9': '4', '4': '6', 'R': 'M', 'r': 'R', '7': 'I', 'c': '7', 'u': 'U'}
    for _ in range(steps):
        if k in ramp and ramp.index(k) > 0:
            k = ramp[ramp.index(k) - 1]
        elif k in alt:
            k = alt[k]
    c.set(x, y, k)


def ragged(x0, y0, x1, y1, seed, torn=None, tear_depth=40):
    m = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            e = 0
            if x - x0 < 3 or x1 - x < 3 or y - y0 < 3 or y1 - y < 3:
                if hsh(x // 2, y // 2, seed) < 0.35:
                    continue
            if torn:
                u = (x - x0) if 'l' in torn else (x1 - x)
                v = (y - y0) if 't' in torn else (y1 - y)
                n = int(10 * vnoise((u - v) / 7.0, seed))
                if u + v < tear_depth + n:
                    continue
            m.add((x, y))
    return m


def paper(c, m, base, shade, seed):
    edge = boundary(m)
    for (x, y) in m:
        L = light(x, y)
        k = base
        if L < 1.45 or (L < 1.55 and bayer(x, y) < (1.55 - L) / 0.1):
            k = shade
        c.set(x, y, k)
    for (x, y) in edge:
        c.set(x, y, 'K' if hsh(x, y, seed) < 0.7 else shade)


def scrap_lines(c, m, edge, x0, x1, ys, col, thick, seed, gap=0.12):
    for i, yy in enumerate(ys):
        ln = int((x1 - x0) * (0.45 + 0.45 * hsh(i, 1, seed)))
        for x in range(x0, x0 + ln):
            if hsh(x // 4, yy, seed + 1) < gap:
                continue
            for t in range(thick):
                if (x, yy + t) in m and (x, yy + t) not in edge:
                    c.set(x, yy + t, col)


def neighbours(c):
    """The flyers around the poster (same ones as in the street layer), cropped and sitting in shadow."""
    # upper right: faded gold lined flyer
    m = ragged(506, -30, 700, 74, 3, torn='bl', tear_depth=36)
    e = boundary(m)
    paper(c, m, 'A', '5', 3)
    for (x, y) in m:
        pass
    scrap_lines(c, m, e, 530, 640, range(4, 66, 12), 'N', 3, 4)
    # right: pale blue lined flyer, in the dark
    m = ragged(528, 96, 700, 390, 7, torn='tl', tear_depth=44)
    e = boundary(m)
    paper(c, m, 'g', 'F', 7)
    for (x, y) in m:
        pass
    scrap_lines(c, m, e, 552, 640, range(118, 122), 'I', 1, 8, gap=0.0)
    scrap_lines(c, m, e, 552, 640, range(140, 340, 15), 'I', 3, 9)
    # left: grey LOST flyer with its cat doodle, mostly out of frame
    m = ragged(-120, 18, 116, 250, 11, torn='tr', tear_depth=40)
    e = boundary(m)
    paper(c, m, 'F', 'D', 11)
    for (x, y) in m:
        pass
    lost = pixels(nearest(bitmap('LOST', F35), 6), -52, 34)
    c.mask({p for p in lost if p in m and p not in e}, 'N')
    catp = [".X.......X.", ".XX.....XX.", ".XXXXXXXXX.", "XXXXXXXXXXX", "XX.XXXXX.XX", "XXXXXXXXXXX", "XXXX.X.XXXX",
            ".XXXXXXXXX.", "..XXXXXXX.."]
    for j, r in enumerate(catp):
        for i, ch in enumerate(r):
            if ch == 'X':
                for yy in range(4):
                    for xx in range(4):
                        p = (14 + i * 4 + xx, 88 + j * 4 + yy)
                        if p in m and p not in e:
                            c.set(p[0], p[1], 'N')
    scrap_lines(c, m, e, 8, 100, range(132, 236, 18), 'E', 3, 12)
    # lower left: cream tear-off-tab flyer (under the dialogue box)
    m = ragged(-30, 268, 150, 400, 17)
    e = boundary(m)
    paper(c, m, 'w', 'B', 17)
    scrap_lines(c, m, e, 0, 140, (282,), 'M', 4, 18)
    for i, tx in enumerate(range(-4, 150, 22)):
        if i in (2, 5):
            for y in range(300, H):
                for x in range(tx + 2, tx + 20):
                    if (x, y) in m:
                        c.p[y][x] = None
        for y in range(296, H):
            if (tx, y) in m and y % 4 < 2:
                c.set(tx, y, 'B')
    # lower right: tan tabs flyer peeking out under the poster
    m = ragged(470, 300, 600, 420, 23)
    e = boundary(m)
    paper(c, m, 'B', 'M', 23)
    for tx in range(478, 600, 20):
        for y in range(318, H):
            if (tx, y) in m and y % 4 < 2:
                c.set(tx, y, 'N')
    # scraps of older posters still glued to the brick
    for (sx, sy, sw, sh, col, sd) in ((134, 96, 26, 14, 'E', 31), (140, 196, 18, 26, 'B', 32), (486, 150, 20, 16, 'D', 33),
                                      (474, 236, 24, 12, 'E', 34), (150, 10, 14, 20, 'B', 35)):
        m = ragged(sx, sy, sx + sw, sy + sh, sd)
        e = boundary(m)
        for (x, y) in m:
            c.set(x, y, col if (x, y) not in e else 'N')
        for (x, y) in m:
            if hsh(x, y, sd) < 0.2 and (x, y) not in e:
                dim(c, x, y, 1)


def refill_holes(c, brick_layer):
    for y in range(H):
        for x in range(W):
            if c.p[y][x] is None:
                c.p[y][x] = brick_layer.p[y][x]


def poster_shadow(c):
    for y in range(PY0 + 5, PY1 + 7):
        for x in range(PX0 + 5, PX1 + 6):
            if not (PX0 <= x <= PX1 and PY0 <= y <= PY1):
                dim(c, x, y, 2)


GLOVE = [
    ".....#####......",
    "....#WcccC#.....",
    "....#cccCC#.....",
    "....#######.....",
    "....#hrrrd#.....",
    "...#hrrrrrd#....",
    "..#hhrrrrrd##...",
    "..#hrrrrrrd#t#..",
    ".#hrrrrrrrd#tt#.",
    ".#hrrrrrrrr#ttd#",
    "#hhsrrrrrrrr#td#",
    "#hssrrrrrrrrr#d#",
    "#hhrrrrrrrrrrr##",
    "#hrrrrrrrrrrrrd#",
    "#rrrrrrrrrrrrrd#",
    "#rrrrrrrrrrrrdd#",
    "#drrrrrrrrrrrdd#",
    ".#drrrrrrrrrdd#.",
    ".#ddrrrrrrrddd#.",
    "..#dddddddddd#..",
    "...##dddddd##...",
    ".....######.....",
]
GLOVE_MAP = {'#': 'K', 'W': 'W', 'c': 'P', 'C': 'g', 'h': 'r', 'r': 'R', 's': 's', 'd': 'M', 't': 'R'}

MASCOT15 = [
    "..UUU.....UUU..",
    ".UUUUUUUUUUUUU.",
    "UUUUUUUUUUUUUUU",
    "UUUUUUUUUUUUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUUUUUUUUUUUU",
    "UUUUUUUUUUUUUUU",
    ".UUUUUUUUUUUUU.",
    "..UUUU...UUUU..",
]


def centered(bw):
    return CX - bw // 2 + (0 if bw % 2 else 1)


def poster(c):
    x0, y0, x1, y1 = PX0, PY0, PX1, PY1
    # ---- paper
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = 'W'
            if y > 256 or (y > 250 and bayer(x, y) < (y - 250) / 7.0):
                k = 'P'
            c.p[y][x] = k
    c.rect(x1 - 2, y0 + 1, x1 - 1, y1 - 1, 'P')
    # fold crease (the poster was folded in half)
    cy = 170
    c.hline(x0 + 1, x1 - 1, cy, 'P')
    for x in range(x0 + 1, x1):
        if bayer(x, cy + 1) < 0.5:
            c.set(x, cy + 1, 'P')
    # ---- header band (rounded, like a message card)
    hb = (x0 + 6, y0 + 6, x1 - 6, y0 + 94)
    band = bold.rrect(hb[0], hb[1], hb[2], hb[3], 5, 5, 5, 5)
    c.mask(band, 'U')
    for (x, y) in band:
        if y <= hb[1] + 1:
            c.set(x, y, 'u')
        elif y >= hb[3] - 2:
            c.set(x, y, 'I')
    for (x, y) in band:
        if (x - hb[0]) + (y - hb[1]) < 4 and (x, y) in band:
            pass
    # @everyone mention pill
    at = bitmap('@everyone', F57)
    aw, ah = size(at)
    pw = aw + 12
    px = centered(pw)
    py = hb[1] + 8
    pill = bold.rrect(px, py, px + pw - 1, py + 14, 4, 4, 4, 4)
    c.mask(pill, 'I')
    c.mask({(x, y) for (x, y) in pill if y == py}, 'N')
    if OPTS['lettering']:
        paint_text(c, pixels(at, px + 6, py + 3), 'P')
    # MEMBERS / WANTED
    for (wd, yy) in (('MEMBERS', hb[1] + 31), ('WANTED', hb[1] + 60)):
        ww = bold.word_width(wd)
        pts = bold.word(wd, centered(ww), yy)
        if OPTS['lettering']:
            paint_text(c, pts, 'W', outline='N', shadow='I', shadow_off=(0, 3))
        # top-lit edge on the letters
        for (x, y) in pts:
            if (x, y - 1) not in pts and (x, y + 1) in pts:
                pass
    # typing-indicator dots in the band corner
    for i in range(3):
        c.rect(hb[2] - 22 + i * 6, hb[1] + 12, hb[2] - 20 + i * 6, hb[1] + 14, 'u' if i != 1 else 'P')
    # ---- mascot badge
    bcx, bcy, br = CX + 0.5, 134.5, 27.5
    disc = ellipse_mask(bcx, bcy, br, br)
    ring_in = ellipse_mask(bcx, bcy, br - 4, br - 4)
    c.mask(disc, 'I')
    c.mask(ring_in, 'P')
    for (x, y) in ring_in:
        d = ((x + 0.5 - bcx) ** 2 + (y + 0.5 - bcy) ** 2) ** 0.5
        if d > br - 8 and (x - bcx) + (y - bcy) > 8:
            c.set(x, y, 'g')
    c.mask(boundary(disc), 'K')
    for (x, y) in disc - ring_in:
        if (x - bcx) + (y - bcy) < -30 and (x, y) not in boundary(disc):
            c.set(x, y, 'U')
    mb = epx([[ch != '.' for ch in r] for r in MASCOT15])
    eyes = epx([[ch == 'W' for ch in r] for r in MASCOT15])
    mw, mh = size(mb)
    mx, my = int(bcx - mw / 2.0), int(bcy - mh / 2.0) + 1
    body = pixels(mb, mx, my)
    eye = pixels(eyes, mx, my)
    for (x, y) in body:
        k = 'U'
        if y >= my + mh - 5:
            k = 'I'
        elif y <= my + 2 or (x <= mx + 3 and y <= my + 8):
            k = 'u'
        c.set(x, y, k)
    c.mask(boundary(body), 'N')
    for (x, y) in eye:
        c.set(x, y, 'W')
    for (x, y) in eye:
        if (x, y + 1) not in eye:
            c.set(x, y, 'P')
    # online dot
    dcx, dcy = bcx + 19, bcy + 19
    c.mask(ellipse_mask(dcx, dcy, 6.5, 6.5), 'W')
    c.mask(ellipse_mask(dcx, dcy, 5, 5), 'K')
    c.mask(ellipse_mask(dcx, dcy, 4, 4), '2')
    c.set(int(dcx) - 2, int(dcy) - 2, '1')
    c.set(int(dcx) - 1, int(dcy) - 2, '1')
    c.set(int(dcx) - 2, int(dcy) - 1, '1')
    # sparkles
    for (sx, sy, s) in ((CX - 52, 118, 3), (CX + 48, 112, 2), (CX - 40, 150, 2)):
        c.hline(sx - s, sx + s, sy, 'u')
        c.vline(sx, sy - s, sy + s, 'u')
        c.set(sx, sy, 'U')
    # ---- TRYOUTS AT
    tb = nearest(bitmap('TRYOUTS AT', F57, spacing=2), 2)
    tw, th = size(tb)
    tp = pixels(tb, centered(tw + 1), 173)
    tp |= {(x + 1, y) for (x, y) in tp}           # 3px verticals: a heavier sub-head
    if OPTS['lettering']:
        paint_text(c, tp, 'N')
    # ---- ARENA #1 with gloves
    ww = bold.word_width('ARENA #1')
    ax = centered(ww)
    pts = bold.word('ARENA #1', ax, 193)
    if OPTS['lettering']:
        paint_text(c, pts, 'R', outline='K', shadow='M', shadow_off=(0, 3), outline8=False)
        for (x, y) in pts:
            if (x, y - 1) not in pts:
                c.set(x, y, 'r')
    gl = [[GLOVE_MAP.get(ch) if ch != '.' else None for ch in r] for r in GLOVE]
    gh, gw = len(gl), len(gl[0])
    # rotate so the cuff is on the outside and the fist punches toward the text (thumb on top)
    rot = [[gl[x][gw - 1 - y] for x in range(gh)] for y in range(gw)]      # ccw: cuff -> left
    rot = [r[::-1] for r in rot[::-1]]                                     # thumb up, fist right
    rot = [r[::-1] for r in rot]
    rh, rw = len(rot), len(rot[0])
    gy = 193 + (20 - rh) // 2
    for j, r in enumerate(rot):
        for i, k in enumerate(r):
            if k:
                c.set(ax - rw - 6 + i, gy + j, k)
                c.set(ax + ww + 5 + (rw - 1 - i), gy + j, k)
    # ---- Earn your invite
    eb = epx(bitmap('Earn your invite', F57))
    ew, eh = size(eb)
    if OPTS['lettering']:
        paint_text(c, pixels(eb, centered(ew), 228), 'I')
    # ---- cut line + tear-off tabs (sits under the dialogue box: kept quiet)
    ty = 258
    for x in range(x0 + 4, x1 - 3):
        if (x // 4) % 2 == 0:
            c.set(x, ty, 'g')
    sc = ["XX...X", "X.X.X.", ".XX.X.", "..XX..", ".XX.X.", "X.X.X.", "XX...X"]
    c.stamp(sc, x0 + 8, ty - 3, {'X': 'F'})
    ntab = 10
    tw_ = (x1 - x0 - 1) // ntab
    torn = {3, 7}
    tab_text = [list(r) for r in bitmap('#tryouts', F57)]
    for i in range(ntab):
        tx0 = x0 + 1 + i * tw_
        tx1 = tx0 + tw_ - 1
        if i in torn:
            continue
        if i > 0:
            for y in range(ty + 2, y1):
                if y % 3 != 0:
                    c.set(tx0, y, 'g')
        # rotated channel name (reads bottom-to-top)
        for j, r in enumerate(tab_text):
            for k_, v in enumerate(r):
                if v and OPTS['lettering']:
                    c.set(tx0 + 9 + j, y1 - 12 - k_, 'g')
    c.box(x0, y0, x1, y1, 'K')
    for i in sorted(torn):
        tx0 = x0 + 1 + i * tw_
        tx1 = tx0 + tw_ - 1
        # ragged tear line, wall shows below
        for x in range(tx0, tx1 + 1):
            top = ty + 6 + int(5 * vnoise(x / 3.0, i))
            for y in range(top, y1 + 1):
                c.p[y][x] = None
            c.set(x, top - 1, 'g')
            c.set(x, top - 2, 'P')
    # bottom-right corner curl
    for i in range(16):
        for j in range(16 - i):
            x, y = x1 - i, y1 - j
            c.p[y][x] = None
    for i in range(17):
        c.set(x1 - 16 + i, y1 - i, 'K')
    for i in range(1, 15):
        for j in range(1, 15 - i + 1):
            x, y = x1 - 16 + j, y1 - i - j + 1
            if (x - (x1 - 16)) + (y1 - y) <= 16:
                pass
    curl = poly_mask([(x1 - 15.5, y1 - 0.5), (x1 + 0.5, y1 - 16.5), (x1 - 12, y1 - 16.5)])
    c.mask(curl, 'g')
    c.mask(boundary(curl), 'K')
    # tape
    for (tx, tyy, ang) in ((x0 - 8, y0 - 2, 1), (x1 - 22, y0 - 3, -1)):
        tp = poly_mask([(tx, tyy + 6 + 4 * ang), (tx + 30, tyy + 6 - 4 * ang), (tx + 31, tyy + 16 - 4 * ang),
                        (tx + 1, tyy + 16 + 4 * ang)])
        for (x, y) in tp:
            k = c.get(x, y)
            c.set(x, y, 'P' if k in ('W', 'P', None) or (x, y) in boundary(tp) else 'g')
        c.mask({p for p in boundary(tp) if hsh(p[0], p[1], 3) < 0.5}, 'g')
    # raindrop spots on the paper
    for (dx, dy) in ((12, 108), (266, 150), (14, 236)):
        x, y = x0 + dx, y0 + dy
        if c.get(x, y) in ('W', 'P'):
            c.set(x, y, 'P')
            c.set(x, y + 1, 'g')


def drips(c):
    for (x, y0, ln) in ((PX0 - 14, 150, 90), (PX1 + 20, 60, 120), (PX1 + 26, 250, 70), (120, 262, 60), (600, 10, 80)):
        for y in range(y0, min(H, y0 + ln)):
            k = c.get(x, y)
            if k in ('B', 'w', 'd', 'M'):
                dim(c, x, y, 1)
        c.set(x, min(H - 1, y0 + ln), 'P')


def build():
    base = Canvas(W, H)
    wall(base)
    drips(base)
    LAYERS['wall'] = base
    c = Canvas(W, H)
    c.blit(base, 0, 0)
    neighbours(c)
    refill_holes(c, base)
    poster_shadow(c)
    LAYERS['flyers'] = c
    p = Canvas(W, H)
    p.blit(c, 0, 0)
    poster(p)
    refill_holes(p, c)
    return p


if __name__ == '__main__':
    c = build()
    c.save('out/poster_closeup.png')
    c.save('view/poster_2x.png', 2)
