"""street_buildings.png (1280x360): storefront row, sidewalk, curb, road. Transparent above rooftops."""
import math
import random
from lib import Canvas, bayer, hsh, vnoise, ellipse_mask, poly_mask, boundary, text_width
from fonts import F57, F35

W, H = 1280, 360
WALL = 238          # last facade row
SW0, SW1 = 239, 281 # sidewalk rows
FEET = 262          # suggested feet line for Burak
CURB = 282
ROAD = 290

PROT = set()          # pixels excluded from the night grade (emissive: signs, lit glass)


def protect_rect(x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            PROT.add((x, y))


WARM = {'N': 'M', 'M': 'B', 'B': 'w', 'w': 'd', 'd': 's', 's': 'W', '6': 'E', 'E': 'D', 'D': 'F',
        'F': 'g', 'g': 'P', 'I': 'V', '4': '9', '7': 'g', 'A': 'd', 'R': 'r', 'V': '8'}
COOL = {'N': 'I', 'M': 'V', 'B': 'M', '6': '7', 'E': 'D', 'D': 'g', 'F': 'g', 'g': 'P', 'I': '7', '7': 'c'}
DARK = {'P': 'g', 'g': 'F', 'F': 'D', 'D': 'E', 'E': '6', '6': 'N', 'w': 'B', 'B': 'M', 'M': 'N',
        'I': 'N', '7': 'I', 'd': 'w', 's': 'd', 'W': 'P', 'V': 'I', '4': '5', '9': '4', 'A': '5', 'U': 'I',
        'r': 'R', 'R': 'M', '8': 'V', 'c': '7'}


def radial(c, cx, cy, rx, ry, mapping, strength=1.0, x0=0, x1=W - 1, y0=0, y1=H - 1, protect=('K',)):
    for y in range(max(y0, int(cy - ry)), min(y1, int(cy + ry)) + 1):
        for x in range(max(x0, int(cx - rx)), min(x1, int(cx + rx)) + 1):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            d = dx * dx + dy * dy
            if d >= 1.0:
                continue
            t = (1.0 - d) * strength
            k = c.p[y][x]
            if k is None or k in protect:
                continue
            if bayer(x, y) < t and k in mapping:
                c.p[y][x] = mapping[k]


# ------------------------------------------------------------------ materials
def bricks(c, x0, y0, x1, y1, brick, mortar, hi=None, lo=None, seed=0, bw=8, bh=4):
    for y in range(y0, y1 + 1):
        row = (y - y0) // bh
        ry = (y - y0) % bh
        off = (bw // 2) if row % 2 else 0
        for x in range(x0, x1 + 1):
            rx = (x - x0 + off) % bw
            if ry == bh - 1 or rx == bw - 1:
                c.set(x, y, mortar)
                continue
            bi = (x - x0 + off) // bw
            v = hsh(bi, row, seed)
            k = brick
            if lo and v < 0.18:
                k = lo
            if hi and ry == 0 and rx == 0 and v > 0.55:
                k = hi
            c.set(x, y, k)


def stucco(c, x0, y0, x1, y1, base, spk_hi, spk_lo, seed=0):
    c.rect(x0, y0, x1, y1, base)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            h = hsh(x, y, seed)
            if h < 0.018:
                c.set(x, y, spk_lo)
            elif h > 0.988:
                c.set(x, y, spk_hi)


def panels(c, x0, y0, x1, y1, base, shade, hi, pw=24):
    c.rect(x0, y0, x1, y1, base)
    for x in range(x0, x1 + 1):
        if (x - x0) % pw == 0:
            c.vline(x, y0, y1, shade)
        elif (x - x0) % pw == 1:
            c.vline(x, y0, y1, hi)


def stain(c, x0, x1, y0, length, seed=0):
    """Rain streak stains running down from a ledge."""
    for x in range(x0, x1 + 1):
        if hsh(x, 3, seed) < 0.55:
            continue
        L = int(length * (0.3 + 0.7 * hsh(x, 9, seed)))
        for y in range(y0, y0 + L):
            t = 1.0 - (y - y0) / max(1, L)
            if bayer(x, y) < t * 0.6:
                k = c.get(x, y)
                if k in DARK and k != 'K':
                    c.set(x, y, DARK[k])


def cornice(c, x0, x1, y, style=0):
    """y = top row. 9 rows tall."""
    c.hline(x0 - 2, x1 + 2, y, 'K')
    c.rect(x0 - 2, y + 1, x1 + 2, y + 2, 'D')
    c.hline(x0 - 2, x1 + 2, y + 3, 'E')
    c.hline(x0 - 2, x1 + 2, y + 4, 'K')
    c.vline(x0 - 2, y, y + 4, 'K')
    c.vline(x1 + 2, y, y + 4, 'K')
    c.rect(x0, y + 5, x1, y + 7, '6')
    for x in range(x0 + 1, x1, 4):
        c.rect(x, y + 5, x + 1, y + 6, 'E')
        c.set(x + 1, y + 7, 'K')
    c.hline(x0, x1, y + 8, 'K')


def window(c, x0, y0, x1, y1, style='dark', seed=0, lintel=True, sill=True):
    if lintel:
        c.rect(x0 - 2, y0 - 4, x1 + 2, y0 - 1, 'E')
        c.hline(x0 - 2, x1 + 2, y0 - 4, 'D')
        c.box(x0 - 2, y0 - 4, x1 + 2, y0 - 1, 'K')
    c.box(x0, y0, x1, y1, 'K')
    gx0, gy0, gx1, gy1 = x0 + 1, y0 + 1, x1 - 1, y1 - 1
    mid = (x0 + x1) // 2
    if style == 'dark':
        c.rect(gx0, gy0, gx1, gy1, 'N')
        # sky reflection diagonal
        for i in range(0, gy1 - gy0 + 1):
            for w_ in range(3):
                if (i + w_) % 2 == 0:
                    c.set(gx0 + 2 + i // 2 + w_, gy0 + i, 'I')
                    PROT.add((gx0 + 2 + i // 2 + w_, gy0 + i))
    elif style == 'warm':
        c.rect(gx0, gy0, gx1, gy1, 'B')
        radial(c, mid + 0.5, gy0 + (gy1 - gy0) * 0.35, (gx1 - gx0) * 0.7, (gy1 - gy0) * 0.6,
               {'B': 'w', 'w': 'd'}, 1.4, gx0, gx1, gy0, gy1)
        # curtains
        for y in range(gy0, gy1 + 1):
            cw = 3 + (y - gy0) // 6
            for x in range(gx0, gx0 + cw):
                c.set(x, y, 'R' if (x + y // 3) % 3 else 'M')
            for x in range(gx1 - cw + 1, gx1 + 1):
                c.set(x, y, 'R' if (x + y // 3) % 3 else 'M')
    elif style == 'tv':
        c.rect(gx0, gy0, gx1, gy1, 'N')
        radial(c, gx0 + (gx1 - gx0) * 0.6, gy1 - 4, (gx1 - gx0) * 0.8, (gy1 - gy0) * 0.8,
               {'N': 'I', 'I': '7'}, 1.2, gx0, gx1, gy0, gy1)
    elif style == 'blind':
        c.rect(gx0, gy0, gx1, gy1, 'N')
        by = gy0 + (gy1 - gy0) * 3 // 5
        for y in range(gy0, by + 1):
            c.hline(gx0, gx1, y, 'F' if (y - gy0) % 3 != 2 else 'E')
        c.hline(gx0, gx1, by + 1, 'K')
        c.set(mid, by + 2, 'D')
    elif style == 'cool':
        c.rect(gx0, gy0, gx1, gy1, 'I')
        radial(c, mid + 0.5, gy0 + 3, (gx1 - gx0) * 0.8, (gy1 - gy0) * 0.9, {'I': '7', '7': 'g'}, 1.2,
               gx0, gx1, gy0, gy1)
    if style in ('warm', 'tv', 'cool'):
        protect_rect(gx0, gy0, gx1, gy1)
    # mullion
    if gx1 - gx0 > 12:
        c.vline(mid, gy0, gy1, 'K')
        c.hline(gx0, gx1, gy0 + (gy1 - gy0) // 2, 'K')
    if sill:
        c.rect(x0 - 2, y1 + 1, x1 + 2, y1 + 3, 'E')
        c.hline(x0 - 2, x1 + 2, y1 + 1, 'D')
        c.box(x0 - 2, y1 + 1, x1 + 2, y1 + 3, 'K')


def awning(c, x0, x1, y0, y1, a, b, stripe=8):
    for x in range(x0, x1 + 1):
        k = a if ((x - x0) // stripe) % 2 == 0 else b
        c.vline(x, y0, y1, k)
    # top shade + scallop valance
    c.hline(x0, x1, y0 + 1, DARK.get(a, a))
    for x in range(x0, x1 + 1):
        k = a if ((x - x0) // stripe) % 2 == 0 else b
        ph = (x - x0) % stripe
        depth = 3 if 1 <= ph <= stripe - 2 else (2 if ph in (0, stripe - 1) else 3)
        depth = [1, 2, 3, 3, 3, 3, 2, 1][ph * 8 // stripe]
        for y in range(y1 + 1, y1 + 1 + depth):
            c.set(x, y, k)
        c.set(x, y1 + 1 + depth, 'K')
        c.set(x, y1 + depth, DARK.get(k, k)) if depth > 1 else None
    c.hline(x0 - 1, x1 + 1, y0, 'K')
    c.vline(x0 - 1, y0, y1 + 2, 'K')
    c.vline(x1 + 1, y0, y1 + 2, 'K')
    # awning drips
    for x in range(x0 + 3, x1, 13):
        if hsh(x, y1, 4) < 0.5:
            c.set(x, y1 + 6, 'g')


def door(c, x0, y0, x1, y1, glass='N', frame='6', glow=None):
    c.rect(x0, y0, x1, y1, frame)
    c.box(x0, y0, x1, y1, 'K')
    c.rect(x0 + 3, y0 + 3, x1 - 3, y0 + (y1 - y0) * 3 // 5, glass)
    c.box(x0 + 2, y0 + 2, x1 - 2, y0 + (y1 - y0) * 3 // 5 + 1, 'K')
    py = y0 + (y1 - y0) * 3 // 5 + 5
    c.box(x0 + 3, py, x1 - 3, y1 - 4, DARK.get(frame, 'N'))
    c.vline(x1 - 4, y0 + (y1 - y0) // 2 + 2, y0 + (y1 - y0) // 2 + 6, 'D')


# ------------------------------------------------------------------ ground
def ground(c):
    # sidewalk (drawn one step light; the night grade takes it to warm grey, lit pools stay light)
    for y in range(SW0, SW1 + 1):
        for x in range(W):
            k = 'D'
            h = hsh(x, y, 21)
            if h < 0.02:
                k = 'E'
            elif h > 0.992:
                k = 'F'
            c.p[y][x] = k
    # wall contact shadow
    for x in range(W):
        c.set(x, SW0, '6')
        c.set(x, SW0 + 1, 'E')
        if bayer(x, SW0 + 2) < 0.5:
            c.set(x, SW0 + 2, 'E')
    # slab seams (oblique)
    for sx in range(-40, W + 60, 44):
        for y in range(SW0 + 3, SW1 + 1):
            x = sx - (y - SW0) // 4
            c.set(x, y, 'E')
            if bayer(x + 1, y) < 0.35:
                c.set(x + 1, y, 'F')
    # crack lines
    rnd = random.Random(3)
    for _ in range(9):
        x, y = rnd.randint(0, W), rnd.randint(SW0 + 6, SW1 - 4)
        for i in range(rnd.randint(6, 14)):
            c.set(x, y, 'E')
            x += 1
            y += rnd.choice((-1, 0, 0, 1))
            y = max(SW0 + 3, min(SW1 - 1, y))
    # curb
    c.hline(0, W - 1, CURB, 'F')
    c.hline(0, W - 1, CURB + 1, 'D')
    c.rect(0, CURB + 2, W - 1, CURB + 6, '6')
    for x in range(W):
        if bayer(x, CURB + 2) < 0.5:
            c.set(x, CURB + 2, 'E')
        if x % 64 == 0:
            c.vline(x, CURB, CURB + 6, 'N')
    c.hline(0, W - 1, CURB + 7, 'K')
    # road
    for y in range(ROAD, H):
        for x in range(W):
            h = hsh(x, y, 33)
            k = '6'
            if h < 0.03:
                k = 'N'
            elif h > 0.992:
                k = 'E'
            c.p[y][x] = k
    for y in range(ROAD, ROAD + 3):
        for x in range(W):
            if bayer(x, y) < 0.6 - 0.2 * (y - ROAD):
                c.set(x, y, 'N')
    # faded lane dashes
    for x0 in range(20, W, 96):
        for x in range(x0, x0 + 40):
            for y in (338, 339):
                if hsh(x, y, 8) > 0.25:
                    c.set(x, y, 'D' if hsh(x, y, 9) > 0.3 else 'E')
    # storm drain grates in the curb
    for gx in (118, 690, 1178):
        c.rect(gx, CURB + 2, gx + 14, CURB + 6, 'K')
        for x in range(gx + 2, gx + 13, 3):
            c.vline(x, CURB + 3, CURB + 5, 'E')


def puddle(c, cx, cy, rx, ry, glint=None, seed=0):
    m = ellipse_mask(cx, cy, rx, ry)
    # irregular outline: nibble the rim with noise, add a lobe
    m |= ellipse_mask(cx + rx * 0.45, cy + ry * 0.35, rx * 0.5, ry * 0.8)
    m = {p for p in m if not (hsh(p[0], p[1], seed) < 0.35 and len([q for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)) if q not in m]) > 0)}
    edge = boundary(m)
    for (x, y) in m:
        # reflects the dark sky: navy, with an indigo band
        k = 'N'
        if abs(y - (cy - ry * 0.2)) < 1.0 and bayer(x, y) < 0.6:
            k = 'I'
        c.set(x, y, k)
    for (x, y) in edge:
        c.set(x, y, '6' if y < cy else 'E')
    if glint:
        for (x, y) in m:
            if (x, y) in edge:
                continue
            u = abs(x + 0.5 - cx)
            if u < 1.5:
                c.set(x, y, glint)
            elif u < 5 and bayer(x, y) < 0.5 * (1 - u / 5.0) + 0.1:
                c.set(x, y, glint)


def reflection(c, cx, width, color, y0=ROAD + 2, y1=H - 1, seed=0, dens=0.7):
    """Broken vertical light streak on wet asphalt."""
    for y in range(y0, y1 + 1):
        t = 1.0 - (y - y0) / (y1 - y0 + 1)
        wob = int(round(2 * (vnoise(y / 5.0, seed) - 0.5)))
        half = width * (0.4 + 0.6 * t)
        for x in range(int(cx - half) + wob, int(cx + half) + wob + 1):
            if (y // 3) % 3 == 2 and hsh(x, y, seed) < 0.6:
                continue
            core = abs(x - wob - cx) <= half * 0.4
            if bayer(x, y) < (dens * t + 0.15) * (1.0 if core else 0.45):
                c.set(x, y, color)


# ------------------------------------------------------------------ buildings
def building_A(c):
    x0, x1 = 0, 196
    top = 79
    bricks(c, x0, top, x1, WALL, 'B', 'M', hi='w', lo='M', seed=1)
    cornice(c, x0, x1, top - 9)
    # chimney
    c.rect(28, top - 26, 42, top - 10, 'B')
    bricks(c, 29, top - 25, 41, top - 10, 'B', 'M', seed=5)
    c.box(27, top - 26, 43, top - 10, 'K')
    c.rect(26, top - 29, 44, top - 26, 'E')
    c.box(26, top - 29, 44, top - 26, 'K')
    # rooftop antenna
    c.vline(150, top - 34, top - 10, 'K')
    for i, y in enumerate((top - 30, top - 24, top - 18)):
        c.hline(150 - 8 + i * 2, 150 + 8 - i * 2, y, 'K')
    # upper windows
    for (wx, st) in ((22, 'dark'), (86, 'warm'), (150, 'blind')):
        window(c, wx, top + 12, wx + 24, top + 44, st)
    stain(c, 20, 176, top + 48, 18, seed=2)
    # sign board
    sy0, sy1 = 132, 150
    c.rect(10, sy0, 186, sy1, '4')
    c.hline(11, 185, sy0 + 1, '9')
    c.hline(11, 185, sy1 - 1, '5')
    c.box(10, sy0, 186, sy1, 'K')
    txt = '#GENERAL STORE'
    tw = text_width(txt, F57)
    tx = 10 + (177 - tw) // 2
    c.text(tx, sy0 + 6, txt, F57, 's', shadow=('5', 1, 1))
    # peeling / faded letters
    for (x, y) in [(tx + 13, sy0 + 7), (tx + 14, sy0 + 8), (tx + 37, sy0 + 10), (tx + 38, sy0 + 11),
                   (tx + 58, sy0 + 6), (tx + 59, sy0 + 6), (tx + 60, sy0 + 7)]:
        c.set(x, y, '9')
    c.recolor(tx + 24, sy0 + 5, tx + 30, sy0 + 13, {'s': 'd'})
    # shutters
    for (a, b) in ((12, 126), (136, 184)):
        c.rect(a - 1, 153, b + 1, 157, 'E')
        c.hline(a - 1, b + 1, 154, 'D')
        c.box(a - 1, 153, b + 1, 157, 'K')
        for y in range(158, WALL + 1):
            k = ['D', 'D', 'E', '6'][(y - 158) % 4]
            c.hline(a, b, y, k)
        c.vline(a - 1, 158, WALL, 'K')
        c.vline(b + 1, 158, WALL, 'K')
        c.rect(a, 231, b, WALL, 'E')
        c.hline(a, b, 231, 'K')
        c.hline(a, b, WALL, 'K')
        hx = (a + b) // 2
        c.rect(hx - 3, 233, hx + 3, 235, 'K')
        c.set(hx, 234, 'D')
        # grime at the bottom
        for y in range(214, 231):
            for x in range(a, b + 1):
                if bayer(x, y) < (y - 214) / 40.0 and c.get(x, y) == 'D':
                    c.set(x, y, 'E')
    # graffiti on the big shutter: "afk" tag in blurple, pink underline swoosh
    tag = [
        "..........XX...XX......",
        ".........XX....XX......",
        "..XXXX..XXXXX..XX..XX..",
        ".XX..XX..XX....XX.XX...",
        ".XX..XX..XX....XXXX....",
        ".XX..XX..XX....XX.XX...",
        "..XXX.XX.XX....XX..XX..",
    ]
    gx, gy = 30, 178
    for j, r in enumerate(tag):
        for i, ch in enumerate(r):
            if ch == 'X':
                c.set(gx + i * 2, gy + j * 2, 'U')
                c.set(gx + i * 2 + 1, gy + j * 2, 'U')
                c.set(gx + i * 2, gy + j * 2 + 1, 'I')
                c.set(gx + i * 2 + 1, gy + j * 2 + 1, 'U')
    for i in range(52):
        x = 28 + i
        y = 196 + int(round(2.5 * math.sin(i / 8.0))) + i // 20
        c.set(x, y, 'r')
        c.set(x, y + 1, 'R')
    # CLOSED paper sign taped on the door shutter
    px0, py0 = 146, 184
    c.rect(px0, py0, px0 + 28, py0 + 11, 'g')
    c.rect(px0 + 1, py0 + 1, px0 + 27, py0 + 10, 'P')
    c.box(px0, py0, px0 + 28, py0 + 11, 'K')
    c.text(px0 + 3, py0 + 3, 'CLOSED', F35, 'R', spacing=1)
    c.rect(px0 - 1, py0 - 1, px0 + 3, py0 + 1, 'g')
    c.rect(px0 + 25, py0 - 1, px0 + 29, py0 + 1, 'g')
    # downpipe
    c.rect(189, top - 6, 192, WALL, 'D')
    c.vline(190, top - 6, WALL, 'F')
    c.vline(192, top - 6, WALL, 'E')
    c.vline(188, top - 6, WALL, 'K')
    c.vline(193, top - 6, WALL, 'K')
    for y in range(top + 10, WALL, 36):
        c.rect(187, y, 194, y + 1, 'K')
    c.vline(x1, top - 9, WALL, 'K')


def building_B(c):
    x0, x1 = 197, 372
    top = 31
    stucco(c, x0, top, x1, WALL, 'E', 'D', '6', seed=4)
    cornice(c, x0, x1, top - 9)
    # water tower on the roof
    wx = 236
    for (lx, rx_) in ((wx + 4, wx + 8), (wx + 28, wx + 24)):
        c.line(lx, top - 9, rx_, top - 20, 'K')
    c.vline(wx + 16, top - 20, top - 9, 'K')
    c.hline(wx + 5, wx + 27, top - 14, 'K')
    c.rect(wx + 2, top - 44, wx + 30, top - 21, 'B')
    for x in range(wx + 3, wx + 30, 4):
        c.vline(x, top - 43, top - 22, 'M')
    c.vline(wx + 4, top - 43, top - 22, 'w')
    c.box(wx + 2, top - 44, wx + 30, top - 21, 'K')
    c.hline(wx + 2, wx + 30, top - 36, 'K')
    c.hline(wx + 2, wx + 30, top - 28, 'K')
    for (a, b, y) in ((wx + 3, wx + 29, top - 45), (wx + 6, wx + 26, top - 46), (wx + 10, wx + 22, top - 47), (wx + 14, wx + 18, top - 48)):
        c.hline(a, b, y, 'M')
        c.set(a - 1, y, 'K')
        c.set(b + 1, y, 'K')
    c.hline(wx + 14, wx + 18, top - 49, 'K')
    # string courses
    for sy in (88, 146):
        c.rect(x0, sy, x1, sy + 3, 'D')
        c.hline(x0, x1, sy, 'F')
        c.hline(x0, x1, sy + 3, 'K')
        stain(c, x0, x1, sy + 4, 14, seed=sy)
    # upper windows
    styles = [['dark', 'warm', 'dark', 'dark'], ['tv', 'dark', 'blind', 'dark']]
    for fi, wy in enumerate((44, 102)):
        for wi, wxx in enumerate((210, 250, 290, 330)):
            window(c, wxx, wy, wxx + 22, wy + 32, styles[fi][wi], lintel=True)
    # AC unit hanging out of a window
    ax, ay = 247, 58
    c.rect(ax, ay, ax + 28, ay + 16, 'D')
    for y in range(ay + 3, ay + 14, 2):
        c.hline(ax + 3, ax + 17, y, 'E')
    c.rect(ax + 20, ay + 3, ax + 25, ay + 13, 'F')
    c.box(ax, ay, ax + 28, ay + 16, 'K')
    c.hline(ax + 1, ax + 27, ay + 1, 'g')
    stain(c, ax + 2, ax + 26, ay + 17, 20, seed=77)
    # awning
    awning(c, 204, 344, 152, 163, 'R', 'M', stripe=10)
    protect_rect(203, 152, 345, 170)
    # storefront window (warm noodle bar)
    fx0, fy0, fx1, fy1 = 206, 174, 300, 228
    c.rect(fx0, fy0, fx1, fy1, 'M')
    radial(c, 253, 188, 60, 30, {'M': 'B', 'B': 'w', 'w': 'd'}, 1.6, fx0 + 1, fx1 - 1, fy0 + 1, fy1 - 1)
    # paper lanterns
    for lx in (222, 253, 284):
        c.vline(lx, fy0 + 1, fy0 + 4, 'K')
        c.ellipse(lx + 0.5, fy0 + 9.5, 4, 5, 'R')
        c.ellipse(lx - 0.5, fy0 + 8.5, 2, 3, 'r')
        c.set(lx, fy0 + 14, 'K')
    # counter + stools + a hunched late-night customer silhouette
    c.rect(fx0 + 1, 206, fx1 - 1, 209, 'B')
    c.hline(fx0 + 1, fx1 - 1, 206, 'w')
    c.rect(fx0 + 1, 210, fx1 - 1, fy1 - 1, 'N')
    for sx in (218, 240, 262, 284):
        c.rect(sx - 3, 214, sx + 3, 215, 'K')
        c.vline(sx, 216, fy1 - 1, 'K')
    cu = ["...XXX...", "..XXXXX..", "..XXXXX..", "...XXX...", ".XXXXXXX.", "XXXXXXXXX", "XXXXXXXXX", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX."]
    c.stamp(cu, 236, 197, {'X': 'N'})
    c.rect(fx0, fy0, fx1, fy0, 'K')
    c.box(fx0, fy0, fx1, fy1, 'K')
    c.vline(253, fy0, fy1, 'K')
    # glass sheen + condensation
    for i in range(18):
        c.set(fx0 + 6 + i // 2, fy0 + 22 - i, 'P') if i % 3 else None
    for dx in (212, 231, 270, 293):
        for y in range(fy0 + 20, fy0 + 20 + int(10 + 20 * hsh(dx, 1, 5))):
            if bayer(dx, y) < 0.5:
                k = c.get(dx, y)
                c.set(dx, y, WARM.get(k, k) if k not in ('K',) else k)
    protect_rect(fx0 + 1, fy0 + 1, fx1 - 1, fy1 - 1)
    c.rect(fx0, fy1 + 1, fx1, WALL, 'B')
    c.hline(fx0, fx1, fy1 + 2, 'w')
    c.box(fx0, fy1 + 1, fx1, WALL, 'K')
    # door
    door(c, 310, 172, 340, WALL, glass='w', frame='B')
    radial(c, 325, 180, 12, 14, {'w': 'd'}, 1.0, 313, 337, 175, 196)
    protect_rect(313, 175, 337, 204)
    # blade sign "NOODLES" (neon, two letters dead)
    bx0, bx1, by0 = 352, 368, 38
    word = 'NOODLES'
    by1 = by0 + 6 + len(word) * 9
    c.rect(bx0, by0, bx1, by1, 'N')
    c.box(bx0, by0, bx1, by1, 'K')
    c.hline(bx0 + 1, bx1 - 1, by0 + 1, 'I')
    for yy in (by0 + 6, by1 - 6):
        c.rect(bx1 + 1, yy, bx1 + 4, yy + 1, 'K')
    dead = {1, 2}
    for i, ch in enumerate(word):
        gx = bx0 + 3 + (11 - len(F57[ch][0])) // 2
        gy = by0 + 4 + i * 9
        col = 'M' if i in dead else 'r'
        if i not in dead:
            # glow halo
            for j, r in enumerate(F57[ch]):
                for k_, px in enumerate(r):
                    if px == 'X':
                        for (ox, oy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            if c.get(gx + k_ + ox, gy + j + oy) == 'N':
                                c.set(gx + k_ + ox, gy + j + oy, 'V')
        c.text(gx, gy, ch, F57, col)
    protect_rect(bx0, by0, bx1, by1)
    # neon glow spill on the wall
    radial(c, 360, 80, 22, 50, {'E': 'V', 'D': '8', 'F': '8'}, 0.55, 345, 372, 30, 145)
    c.vline(x1, top - 9, WALL, 'K')


def building_C(c):
    """Vacant lot: chain-link fence, the far skyline shows through."""
    x0, x1 = 373, 452
    fy0 = 186
    # overhead wires across the gap
    for (ya, yb, sag) in ((52, 48, 12), (60, 58, 9)):
        for x in range(x0, x1 + 1):
            t = (x - x0) / (x1 - x0)
            y = ya + (yb - ya) * t + sag * 4 * t * (1 - t)
            c.set(x, int(round(y)), 'K')
    # weeds behind the fence line
    rnd = random.Random(9)
    for x in range(x0, x1 + 1):
        if rnd.random() < 0.55:
            hgt = rnd.randint(2, 9)
            c.vline(x, WALL - hgt, WALL, '4' if rnd.random() < 0.6 else '5')
    c.rect(x0, WALL - 1, x1, WALL, '5')
    # mesh
    for y in range(fy0 + 3, WALL - 1):
        for x in range(x0, x1 + 1):
            if (x + y) % 6 == 0:
                c.set(x, y, 'F')
            elif (x - y) % 6 == 0:
                c.set(x, y, 'E')
    c.hline(x0, x1, fy0 + 1, 'D')
    c.hline(x0, x1, fy0 + 2, 'K')
    c.hline(x0, x1, fy0, 'K')
    c.hline(x0, x1, WALL - 3, 'K')
    # barbed wire
    for x in range(x0, x1 + 1):
        ph = (x - x0) % 7
        for y in ({0: (-2, -6), 1: (-1, -7), 2: (-7,), 3: (-7,), 4: (-6, -1), 5: (-7, -2), 6: (-4,)}[ph]):
            c.set(x, fy0 + y, 'E' if y < -3 else 'D')
    for px in (x0 + 1, 412, x1 - 2):
        c.rect(px - 1, fy0 - 9, px + 1, WALL, 'D')
        c.vline(px - 1, fy0 - 9, WALL, 'F')
        c.box(px - 2, fy0 - 10, px + 2, WALL, 'K')
    # KEEP OUT sign on the fence
    kx, ky = 398, 200
    c.rect(kx, ky, kx + 34, ky + 10, 'R')
    c.hline(kx + 1, kx + 33, ky + 1, 'r')
    c.box(kx, ky, kx + 34, ky + 10, 'K')
    c.text(kx + 3, ky + 3, 'KEEP OUT', F35, 'P', spacing=1)
    stain(c, kx + 1, kx + 33, ky + 11, 6, seed=3)


def fire_escape(c, xa, xb, levels):
    for i, py in enumerate(levels):
        c.rect(xa, py, xb, py + 1, 'K')
        c.hline(xa, xb, py - 13, 'K')
        c.hline(xa, xb, py - 7, 'K')
        for x in range(xa, xb + 1, 5):
            c.vline(x, py - 13, py, 'K')
        c.vline(xb, py - 13, py, 'K')
        for x in range(xa + 2, xb, 9):
            c.set(x, py + 2, 'K')
        # stairs to the level above
        if i + 1 < len(levels):
            up = levels[i + 1]
            sx0, sx1 = xb - 8, xb - 58
            for k_ in range(0, py - up):
                x = int(round(sx0 - (sx0 - sx1) * k_ / (py - up)))
                c.set(x, py - k_, 'K')
                c.set(x + 5, py - k_, 'K')
                if k_ % 4 == 0:
                    c.hline(x, x + 5, py - k_, 'K')
    # drop ladder from the lowest platform
    lp = levels[0]
    c.vline(xb - 10, lp + 2, lp + 30, 'K')
    c.vline(xb - 4, lp + 2, lp + 30, 'K')
    for y in range(lp + 5, lp + 30, 4):
        c.hline(xb - 10, xb - 4, y, 'K')


def building_D(c):
    x0, x1 = 453, 700
    bricks(c, x0, 0, x1, WALL, 'M', 'N', hi='B', lo='N', seed=7)
    # string courses
    for sy in (26, 84, 142):
        c.rect(x0, sy, x1, sy + 3, 'E')
        c.hline(x0, x1, sy, 'D')
        c.hline(x0, x1, sy + 3, 'K')
    # windows
    rows = [(-12, ['dark', 'dark', 'cool', 'dark', 'dark']),
            (44, ['warm', 'dark', 'dark', 'blind', 'dark']),
            (102, ['dark', 'blind', 'dark', 'dark', 'tv'])]
    for (wy, sts) in rows:
        for (wx, st) in zip((470, 518, 566, 614, 662), sts):
            window(c, wx, wy, wx + 20, wy + 32, st)
    fire_escape(c, 462, 606, [138, 80, 22])
    # laundromat sign box
    c.rect(460, 150, 640, 166, 'I')
    c.hline(461, 639, 151, '7')
    c.box(460, 150, 640, 166, 'K')
    txt = 'LAUNDRY'
    tw = text_width(txt, F57)
    c.text(460 + (181 - tw) // 2, 155, txt, F57, 'c', shadow=('N', 1, 1))
    protect_rect(461, 151, 639, 165)
    radial(c, 550, 158, 110, 22, {'M': 'V', 'N': 'I', 'B': 'V'}, 0.5, 453, 700, 140, 149)
    # laundromat window
    lx0, ly0, lx1, ly1 = 464, 172, 598, 230
    c.rect(lx0, ly0, lx1, ly1, '7')
    radial(c, 531, ly0 + 4, 90, 40, {'7': 'g', 'g': 'P'}, 0.8, lx0 + 1, lx1 - 1, ly0 + 1, ly1 - 1)
    # tubes (one dead)
    for (t0, t1, k_) in ((472, 520, 'W'), (540, 588, 'E')):
        c.hline(t0, t1, ly0 + 3, k_)
        c.hline(t0, t1, ly0 + 2, 'K')
    # washers
    for i, wx in enumerate(range(468, 594, 32)):
        c.rect(wx, 196, wx + 26, ly1, 'g')
        c.hline(wx + 1, wx + 25, 197, 'P')
        c.rect(wx + 1, 199, wx + 25, 201, 'D')
        c.set(wx + 22, 200, 'c')
        c.box(wx, 196, wx + 26, ly1 + 2, 'K')
        m = ellipse_mask(wx + 13.5, 215.5, 8.5, 8.5)
        c.mask(boundary(m), 'K')
        inner = m - boundary(m)
        c.mask(inner, 'N')
        c.mask(boundary(inner), 'F')
        core = inner - boundary(inner)
        for (x, y) in core:
            if (x - wx - 13) + (y - 215) < -3:
                c.set(x, y, '7')
        if i == 1:      # one machine running: a blurple towel tumbling
            for (x, y) in core:
                if (x - wx - 13) ** 2 + (y - 218) ** 2 < 12 and y > 215:
                    c.set(x, y, 'U')
    c.box(lx0, ly0, lx1, ly1, 'K')
    protect_rect(lx0 + 1, ly0 + 1, lx1 - 1, ly1 + 2)
    c.rect(lx0, ly1 + 1, lx1, WALL, 'N')
    c.box(lx0, ly1 + 1, lx1, WALL, 'K')
    door(c, 606, 172, 636, WALL, glass='g', frame='I')
    protect_rect(609, 175, 633, 211)
    # apartment entrance
    c.rect(650, 166, 694, WALL, 'N')
    c.box(650, 166, 694, WALL, 'K')
    c.rect(655, 170, 689, 176, 'A')
    protect_rect(655, 160, 689, 176)
    c.box(655, 170, 689, 176, 'K')
    for x in range(661, 689, 6):
        c.vline(x, 170, 176, 'K')
    door(c, 658, 180, 686, WALL - 5, glass='5', frame='B')
    c.rect(652, WALL - 4, 692, WALL - 2, 'D')
    c.rect(648, WALL - 1, 696, WALL, 'E')
    c.hline(652, 692, WALL - 4, 'F')
    c.box(648, WALL - 4, 696, WALL, 'K')
    # bare bulb + warm spill
    c.rect(670, 160, 674, 162, 'K')
    c.rect(671, 163, 673, 164, 'Y')
    radial(c, 672, 166, 40, 34, WARM, 0.8, 640, 700, 146, 200)
    c.set(672, 163, 'W')
    # buzzer panel
    c.rect(689, 196, 692, 206, 'D')
    c.box(689, 196, 692, 206, 'K')
    c.vline(x1, 0, WALL, 'K')


def building_E(c):
    x0, x1 = 701, 858
    top = 106
    panels(c, x0, top, x1, WALL, '7', 'I', 'g', pw=26)
    cornice(c, x0, x1, top - 9)
    # roof units
    c.rect(718, top - 22, 748, top - 10, 'D')
    for x in range(722, 745, 3):
        c.vline(x, top - 19, top - 13, 'E')
    c.box(718, top - 22, 748, top - 10, 'K')
    c.hline(719, 747, top - 21, 'g')
    c.vline(820, top - 40, top - 10, 'K')
    c.line(820, top - 40, 832, top - 30, 'K')
    c.line(820, top - 32, 810, top - 24, 'K')
    c.set(820, top - 41, 'R')
    # upper windows
    window(c, 716, top + 8, 752, top + 32, 'warm')
    # cat silhouette on the sill
    cat = ["X...X...", "XXXXX...", "XXXXX...", ".XXXX...", ".XXXXX..", ".XXXXXX.", ".XXXXXXX", "XXXXXXXX"]
    c.stamp(cat, 738, top + 24, {'X': 'K'})
    c.set(739, top + 26, 'Y')
    window(c, 806, top + 8, 842, top + 32, 'dark')
    # sign
    c.rect(708, 146, 851, 164, 'N')
    c.box(708, 146, 851, 164, 'K')
    c.hline(709, 850, 147, 'I')
    txt = 'PAWN SHOP'
    tw = text_width(txt, F57, scale=1)
    tx = 708 + (144 - tw) // 2
    c.text(tx, 152, txt, F57, 'Y', shadow=('A', 1, 1))
    wx = tx + 12          # the W is dead
    c.recolor(wx, 152, wx + 6, 159, {'Y': '5', 'A': 'N'})
    protect_rect(709, 147, 850, 163)
    # display window with security bars
    wx0, wy0, wx1, wy1 = 712, 172, 800, 230
    c.rect(wx0, wy0, wx1, wy1, 'N')
    c.hline(wx0 + 1, wx1 - 1, 200, 'B')
    c.hline(wx0 + 1, wx1 - 1, 201, 'M')
    # guitar
    g = ["..X..", "..X..", "..X..", "..X..", "..X..", ".XXX.", "XXXXX", "XXKXX", ".XXX.", "XXXXX", "XXXXX", ".XXX."]
    c.stamp(g, 718, 186, {'X': 'w', 'K': 'K'})
    # old TVs, the middle one shows the chat mascot
    for (tx0, st) in ((730, 'static'), (756, 'mascot'), (782, 'static')):
        c.rect(tx0, 186, tx0 + 20, 199, 'E')
        c.box(tx0, 186, tx0 + 20, 199, 'K')
        c.rect(tx0 + 2, 188, tx0 + 17, 197, '7')
        c.box(tx0 + 2, 188, tx0 + 17, 197, 'K')
        c.set(tx0 + 19, 190, 'R')
        if st == 'static':
            for y in range(189, 197):
                for x in range(tx0 + 3, tx0 + 17):
                    h = hsh(x, y, tx0)
                    c.set(x, y, 'g' if h > 0.7 else ('7' if h > 0.3 else 'I'))
        else:
            c.rect(tx0 + 3, 189, tx0 + 16, 196, 'I')
            m = ["..XXXXXX..", ".XXXXXXXX.", "XX.XXXX.XX", "XX.XXXX.XX", "XXXXXXXXXX", ".XXX..XXX."]
            c.stamp(m, tx0 + 5, 190, {'X': 'U', '.': None})
            for (ex, ey) in ((tx0 + 7, 192), (tx0 + 7, 193), (tx0 + 12, 192), (tx0 + 12, 193)):
                c.set(ex, ey, 'W')
        radial(c, tx0 + 10, 206, 14, 8, {'N': 'I', 'M': 'V', 'B': 'M'}, 0.6, wx0 + 1, wx1 - 1, 200, wy1 - 1)
    protect_rect(730, 186, 802, 199)
    # shelf items
    for (sx, k_) in ((722, 'A'), (740, 'g'), (762, 'R'), (786, 'D')):
        c.rect(sx, 212, sx + 8, 226, k_)
        c.box(sx, 212, sx + 8, 226, 'K')
    c.box(wx0, wy0, wx1, wy1, 'K')
    for x in range(wx0 + 4, wx1, 6):
        c.vline(x, wy0 + 1, wy1 - 1, 'K')
        c.vline(x + 1, wy0 + 1, wy1 - 1, 'E') if (x // 6) % 2 == 0 else None
    c.hline(wx0, wx1, wy0 + 3, 'K')
    c.hline(wx0, wx1, wy1 - 3, 'K')
    c.rect(wx0, wy1 + 1, wx1, WALL, 'I')
    c.box(wx0, wy1 + 1, wx1, WALL, 'K')
    # door with BRB sign
    door(c, 814, 172, 844, WALL, glass='N', frame='I')
    c.rect(821, 184, 837, 194, 'P')
    c.box(821, 184, 837, 194, 'K')
    c.vline(825, 180, 183, 'K')
    c.vline(833, 180, 183, 'K')
    c.text(824, 187, 'BRB', F35, 'N', spacing=1)
    c.vline(x1, top - 9, WALL, 'K')
