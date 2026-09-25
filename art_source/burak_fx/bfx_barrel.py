"""burak_barrel.png: Captain Burak's powder keg, at 2x the first draft (the user: "the barrels should be
bigger", then, shown 1.5x and 2x side by side, "lets do the 2x version"). 7 frames of 48x56, one strip:
  frame 0      intact
  frame 1      cracked once (after the first punch)
  frame 2      cracked twice (after the second punch; the third breaks it: burak_barrel_break)
  frames 3-6   THE LIT FUSE, an OVERLAY loop at 0.06 s: only the fuse's burning tip, its sparks and a wisp
               of smoke, on the same frame and pivot, so a second sprite over whichever damage frame is
               showing lights that barrel, cracked or not
THE PIVOT IS THE FLOOR POINT, the frame's bottom-centre edge (24, 56): as a centred Sprite2D, offset
(0, -28). It never flips (it is lit from the top left either way).

A wooden powder keg with iron hoops, in Burak's own colours (measured from burak_boss.png): walnut and warm
browns for the staves and lid, iron for the hoops, the darkest walnut for its edge (no keyline), a crimson
powder mark (an X) on the front. Lit from the top left as a cylinder; the hoops curve round it; the staves'
seams follow its bulge. Each crack takes a chip out of the silhouette; the second punches a hole through to
the black powder.

Drawn natively at any size: every measure below is the first draft's (24x28) in texels from the floor
point, multiplied by S and rasterised at the new resolution; nothing is upscaled. S = 2.0 ships (the
1.5x set it replaced is kept in scratch); build(S) draws any size.
"""
import math

import bfx_pal as pal

S_SHIP = 2.0
FRAME_SIZE = (48, 56)
NOTE = '7 frames of 48x56: f0 intact, f1 cracked once, f2 cracked twice, f3-6 lit-fuse overlay (0.06 s)'


class Keg:
    """The keg's geometry at scale S. Old-draft coordinates (ox, oy) map to this frame by at()."""

    def __init__(self, S):
        self.S = S
        self.W = int(round(24 * S))
        self.H = int(round(28 * S))
        self.CX = self.W / 2.0
        self.floor = float(self.H)
        self.lid_y = self.floor - 21.0 * S
        self.lid_ry = 2.6 * S
        self.bot_y = self.floor - 2.8 * S
        self.bot_ry = 2.2 * S
        self.r_end = 7.0 * S
        self.bulge = 1.3 * S
        self.hoop_tops = (self.floor - 19.4 * S, self.floor - 7.8 * S)
        self.hoop_depth = max(2, int(round(2 * S)))
        self.seams = (-0.64, -0.2, 0.26, 0.68) if S < 1.25 else (-0.72, -0.43, -0.14, 0.16, 0.45, 0.74)

    def at(self, ox, oy):
        """A point of the first draft (24x28 frame, floor at y 28, centre x 12) in this frame."""
        return self.CX + (ox - 12.0) * self.S, self.floor - (28.0 - oy) * self.S

    def half_width(self, y):
        t = min(1.0, max(0.0, (y - self.lid_y) / (self.bot_y - self.lid_y)))
        return self.r_end + self.bulge * math.sin(math.pi * t)

    def in_body(self, px, py):
        dx = px - self.CX
        if self.lid_y <= py <= self.bot_y:
            return abs(dx) <= self.half_width(py)
        if py > self.bot_y:
            return (dx / self.r_end) ** 2 + ((py - self.bot_y) / self.bot_ry) ** 2 <= 1.0
        return False

    def in_lid(self, px, py):
        return ((px - self.CX) / self.r_end) ** 2 + ((py - self.lid_y) / self.lid_ry) ** 2 <= 1.0

    def hoop_top(self, i, u):
        return self.hoop_tops[i] + 1.1 * self.S * math.sqrt(max(0.0, 1.0 - u * u))


def body_key(u):
    if u < -0.55:
        return 'E'
    if u < 0.1:
        return 'f'
    if u < 0.6:
        return 'F'
    if u < 0.86:
        return 'D'
    return 'n'


def line_texels(pts, step=0.15):
    """Texels along a polyline of continuous points, one per step, L-corners removed (pixel-perfect)."""
    run = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(n + 1):
            p = (int(math.floor(x0 + (x1 - x0) * i / n)), int(math.floor(y0 + (y1 - y0) * i / n)))
            if not run or run[-1] != p:
                run.append(p)
    out = list(run)
    i = 1
    while i < len(out) - 1:
        (ax, ay), (bx, by), (cx, cy) = out[i - 1], out[i], out[i + 1]
        if abs(ax - cx) == 1 and abs(ay - cy) == 1 and (ax == bx or ay == by):
            del out[i]
        else:
            i += 1
    return out


def keg(k):
    """The intact keg as a key grid, plus its mask."""
    W, H, S = k.W, k.H, k.S
    g = pal.blank(W, H)
    mask = set()
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            if k.in_body(px, py) or k.in_lid(px, py):
                mask.add((x, y))
    for (x, y) in mask:
        px, py = x + 0.5, y + 0.5
        if k.in_lid(px, py) and py <= k.lid_y + k.lid_ry:
            # the lid: lit planks, the rim a ring of iron
            dxn = (px - k.CX) / k.r_end
            dyn = (py - k.lid_y) / k.lid_ry
            r = math.hypot(dxn, dyn)
            if r > 0.8:
                key = 'i' if dxn < -0.2 and dyn < 0.3 else ('k' if dxn < 0.5 else 'K')
            else:
                plank = int((py - (k.lid_y - k.lid_ry)) / max(1.0, 1.2 * S)) % 2
                key = 'e' if (dxn + dyn) < -0.4 else ('E' if plank == 0 else 'f')
            g[y][x] = key
            continue
        w = k.half_width(min(max(py, k.lid_y), k.bot_y))
        u = (px - k.CX) / w
        key = body_key(u)
        for s in k.seams:
            if abs(px - (k.CX + s * w)) < 0.5:
                key = 'D' if key in 'Ef' else 'n'
        for i in range(2):
            top = k.hoop_top(i, max(-1.0, min(1.0, u)))
            if top <= py < top + k.hoop_depth:
                row = int(py - top)
                if u < -0.3:
                    key = ('s', 'i', 'i', 'k')[row]
                elif u < 0.45:
                    key = ('i', 'k', 'k', 'K')[row]
                else:
                    key = ('k', 'K', 'K', 'x')[row]
        g[y][x] = key
    # the crimson powder mark: an X on the front, upper strokes #D8434F, lower #B02436
    mx, my = k.at(11.5, 15.5)
    half = 2.2 * S + 0.3
    thick = 0.8 if S < 1.75 else 1.15              # about 2 texels wide at 1.5x, 2-3 at 2x
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - mx, y + 0.5 - my
            if max(abs(dx), abs(dy)) > half:
                continue
            if abs(dx - dy) <= thick or abs(dx + dy) <= thick:
                if (x, y) in mask:
                    g[y][x] = '2' if dy < 0 else '3'
    # the silhouette's edge in the darkest walnut
    for (x, y) in mask:
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            g[y][x] = 'O'
    # the fuse: a dark cord out of the lid, bending right; a highlight on its left
    cord = [k.at(12.5, 6.8), k.at(12.5, 5.2), k.at(13.4, 4.0), k.at(13.6, 3.2), k.at(14.4, 2.4)]
    for (x, y) in line_texels(cord):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = 'O'
            if S >= 1.75 and x + 1 < W:
                g[y][x + 1] = 'O'
    hx, hy = k.at(12.2, 4.8)
    g[int(hy)][int(hx) - (1 if S >= 1.75 else 0)] = 'D'
    return g, mask


def fuse_tip(k):
    x, y = k.at(14.4, 2.4)
    return int(math.floor(x)), int(math.floor(y))


# Cracks and chips, in the first draft's continuous coordinates.
CRACK_1 = [(14.5, 9.8), (14.8, 12.4), (15.3, 13.9), (14.6, 15.4), (15.4, 16.7), (15.1, 17.8), (14.6, 18.8)]
CRACK_1_BRANCH = [(14.9, 12.2), (16.4, 11.1), (17.6, 10.0)]
CHIP_1 = [(17.8, 8.6), (20.4, 8.6), (20.4, 12.2), (19.2, 12.2), (17.8, 10.8)]
SPLINTER_1 = [(18.2, 12.4), (20.0, 13.8)]
CRACK_2 = [(8.5, 10.8), (8.4, 12.7), (7.6, 13.6), (8.5, 14.8), (8.3, 15.9), (7.5, 16.6), (8.5, 17.6),
           (9.3, 18.6), (9.5, 20.0)]
CHIP_2 = [(3.4, 14.6), (5.0, 15.3), (5.9, 16.5), (5.0, 17.7), (3.4, 18.2)]
SPLINTERS_2 = [[(5.6, 12.2), (4.6, 11.2)], [(18.6, 16.2), (20.0, 17.4)]]
HOLE = ((15.5, 14.7), 1.75, 1.95)            # centre, rx, ry
DENT = (8.4, 21.2)


def in_poly(px, py, poly):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def crack(g, k, pts, lit_side=-1, heart=None):
    """A dark split with a lit (chipped) edge on one side; `heart` widens it by a texel between two old
    y values."""
    W, H = k.W, k.H
    cells = line_texels([k.at(*p) for p in pts])
    extra = []
    if heart:
        y0 = k.at(0, heart[0])[1]
        y1 = k.at(0, heart[1])[1]
        extra = [(x + 1, y) for (x, y) in cells if y0 <= y <= y1]
    for (x, y) in cells + extra:
        if 0 <= x < W and 0 <= y < H and g[y][x] != '.':
            g[y][x] = 'p'
    for (x, y) in cells:
        lx = x + lit_side
        if 0 <= lx < W and 0 <= y < H and g[y][lx] not in 'pOxk.':
            g[y][lx] = 'e'


def chip(g, k, poly):
    """Take a bite out of the silhouette and re-edge what's left round it."""
    W, H = k.W, k.H
    p2 = [k.at(*p) for p in poly]
    bitten = [(x, y) for y in range(H) for x in range(W) if in_poly(x + 0.5, y + 0.5, p2)]
    for (x, y) in bitten:
        g[y][x] = '.'
    for (x, y) in bitten:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and g[ny][nx] != '.':
                g[ny][nx] = 'O'


def splinter(g, k, pts):
    cells = line_texels([k.at(*p) for p in pts])
    for i, (x, y) in enumerate(cells):
        if 0 <= x < k.W and 0 <= y < k.H:
            g[y][x] = 'e' if i < len(cells) // 2 else 'E'


def hole(g, k):
    (ox, oy), rx, ry = HOLE
    cx, cy = k.at(ox, oy)
    rx, ry = rx * k.S, ry * k.S
    for y in range(k.H):
        for x in range(k.W):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1.0 and g[y][x] != '.':
                g[y][x] = 'x'
                if d < 0.45 and (x + y) % 3 == 0:
                    g[y][x] = 'k'                                       # black powder glinting inside
            elif d <= 1.0 + 1.6 / min(rx, ry) and g[y][x] not in '.O':
                g[y][x] = 'p'                                           # the broken plank ends round it


def cracked(k, level):
    g, mask = keg(k)
    chip(g, k, CHIP_1)
    crack(g, k, CRACK_1, heart=(12.0, 15.5))
    crack(g, k, CRACK_1_BRANCH)
    splinter(g, k, SPLINTER_1)
    if level >= 2:
        chip(g, k, CHIP_2)
        crack(g, k, CRACK_2, lit_side=1)
        hole(g, k)
        for sp in SPLINTERS_2:
            splinter(g, k, sp)
        # the lower hoop dented where the second crack meets it
        dx, dy = k.at(*DENT)
        for (ddx, ddy, key) in ((0, 0, 'K'), (1, 1, 'x'), (-1, 0, 'k'), (0, 1, 'x')):
            x, y = int(dx) + ddx, int(dy) + ddy
            if 0 <= x < k.W and 0 <= y < k.H and g[y][x] != '.':
                g[y][x] = key
    return g


# The lit fuse, overlay only: per frame the burning tip, its sparks and a wisp of smoke, as offsets from the
# tip in the first draft's texels (scaled out by S, sparks staying single texels).
FUSE_FRAMES = [
    [(0, 0, 'Q'), (1, 0, 'Y'), (0, -1, 'Y'), (-1, 0, 'G'), (2, -2, 'Y'), (3, 0, 'G'), (-2, -2, 'c')],
    [(0, 0, 'Q'), (1, -1, 'Y'), (0, 1, 'G'), (2, 1, 'Y'), (-2, -1, 'Y'), (1, -2, 'w'), (2, -1, 'c')],
    [(0, 0, 'Q'), (0, -1, 'Q'), (1, 0, 'Y'), (-1, -1, 'Y'), (3, -1, 'Y'), (-3, 1, 'G'), (0, -2, 'c')],
    [(0, 0, 'Q'), (-1, 0, 'Y'), (1, 1, 'G'), (2, -1, 'Y'), (-2, 0, 'G'), (4, -2, 'G'), (-1, -2, 'w')],
]


def fuse(k, f):
    g = pal.blank(k.W, k.H)
    tx, ty = fuse_tip(k)
    for (ox, oy, key) in FUSE_FRAMES[f]:
        x = tx + int(round(ox * k.S))
        y = ty + int(round(oy * k.S))
        if 0 <= x < k.W and 0 <= y < k.H:
            g[y][x] = key
            if key == 'Q' and k.S >= 1.4 and (ox, oy) == (0, 0):
                for (ax, ay) in ((1, 0), (0, 1), (1, 1)):             # a bigger burning tip
                    if 0 <= x + ax < k.W and 0 <= y + ay < k.H:
                        g[y + ay][x + ax] = 'Y' if (ax, ay) != (1, 1) else 'G'
    # the cord glowing just behind the tip
    gx, gy = k.at(13.6, 3.3)
    if 0 <= int(gy) < k.H:
        g[int(gy)][int(gx)] = 'G'
    return g


def build(S, intact_only=False):
    k = Keg(S)
    out = [pal.rows(keg(k)[0])]
    if intact_only:
        return out
    out += [pal.rows(cracked(k, 1)), pal.rows(cracked(k, 2))]
    out += [pal.rows(fuse(k, f)) for f in range(4)]
    return out


def frames():
    return build(S_SHIP)
