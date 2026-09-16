"""POO EXPLOSION generator: 5 frames x 48x48. Layered, back-to-front, every layer gets an
outside 1px black outline (house style). Emits ASCII grids for freezing/hand polish."""
import math
import sys
import fxpng

W = H = 48
FLOOR = (136, 180, 99)

PAL = {
    '.': None, 'K': '#000000',
    # poo browns (same ramp as the bomb)
    'a': '#3B1F1E', 'b': '#5C3326', 'c': '#7E4A2E', 'd': '#A0633A', 'e': '#C98A4E', 'f': '#F0CC98',
    # stink greens (yellow-olive: separates from the grass-green arena floor)
    's': '#4A5A1C', 't': '#6F8A24', 'u': '#A3BF34', 'v': '#CFE36A', 'w': '#EDF7B5',
    # flash
    'W': '#FFFFFF',
}

LIGHT = (-0.55, -0.65, 0.52)
_n = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _n for v in LIGHT)


class Frame:
    def __init__(self):
        self.g = [['.'] * W for _ in range(H)]

    def inside(self, x, y):
        return 0 <= x < W and 0 <= y < H

    def paint(self, tones, outline=True, outline_ch='K'):
        """tones: dict (x,y)->char. Fill, then outline OUTSIDE the mask."""
        for (x, y), ch in tones.items():
            if self.inside(x, y):
                self.g[y][x] = ch
        if outline:
            for (x, y) in tones:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in tones and self.inside(nx, ny):
                        self.g[ny][nx] = outline_ch


def disc(cx, cy, r):
    x0, x1 = int(math.floor(cx - r - 1)), int(math.ceil(cx + r + 1))
    y0, y1 = int(math.floor(cy - r - 1)), int(math.ceil(cy + r + 1))
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def puff_tones(cx, cy, r, ramp='stink', fade=False):
    """Cartoon cloud ball: base, lower-right shadow crescent, deep rim, lit cap, highlight."""
    m = disc(cx, cy, r)
    lit = disc(cx - 0.22 * r, cy - 0.26 * r, 0.62 * r)
    hi = disc(cx - 0.38 * r, cy - 0.42 * r, max(0.9, 0.24 * r))
    shade = disc(cx - 0.20 * r, cy - 0.22 * r, 0.92 * r)
    out = {}
    for p in m:
        if p in hi:
            ch = 'w'
        elif p in lit:
            ch = 'w' if fade else 'v'
        elif p in shade:
            ch = 'v' if fade else 'u'
        else:
            ch = 'u' if fade else 't'
        out[p] = ch
    # deep rim: shadow pixels on the very lower-right edge
    if not fade:
        for (x, y), ch in list(out.items()):
            if ch == 't' and ((x + 1, y) not in m or (x, y + 1) not in m):
                if (x + 0.5 - cx) + (y + 0.5 - cy) > 0.9 * r:
                    out[(x, y)] = 's'
    return out


def splat_mask(cx, cy, r0, spikes, sy=1.0, pw=28):
    """Polar splat: base radius r0 plus narrow spikes [(angle_deg, length)]; sy squashes Y."""
    reach = r0 + max([l for _, l in spikes] + [0]) + 2
    pts = {}
    for y in range(int(cy - reach * sy) - 2, int(cy + reach * sy) + 3):
        for x in range(int(cx - reach) - 2, int(cx + reach) + 3):
            dx = x + 0.5 - cx
            dy = (y + 0.5 - cy) / sy
            d = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            R = r0
            for ang, ln in spikes:
                c = math.cos(th - math.radians(ang))
                if c > 0:
                    R += ln * c ** pw
            if d <= R:
                pts[(x, y)] = (d / max(R, 0.01), th, d)
    return pts


def splat_tones(cx, cy, r0, spikes, sy=1.0, pw=28, glint=True):
    pts = splat_mask(cx, cy, r0, spikes, sy, pw)
    out = {}
    for (x, y), (rho, th, d) in pts.items():
        # flattened dome normal from the base radius (spikes read as thin raised splashes)
        k = min(1.0, d / (r0 * 1.08))
        nx, ny = math.cos(th) * k * 0.95, math.sin(th) * k * 0.95
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        v = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
        if d > r0 * 1.02:  # spike body: simple lit/shadow split
            ch = 'd' if v > 0.45 else 'c' if v > 0.1 else 'b'
        else:
            ch = 'e' if v > 0.86 else 'd' if v > 0.62 else 'c' if v > 0.25 else 'b' if v > -0.05 else 'a'
        out[(x, y)] = ch
    if glint:
        g = disc(cx - 0.42 * r0, cy - 0.45 * r0 * sy, max(0.9, 0.16 * r0))
        for p in g:
            if p in out:
                out[p] = 'f'
    return out


def chunk_tones(cx, cy, r):
    m = disc(cx, cy, r)
    out = {}
    for (x, y) in m:
        v = (x + 0.5 - cx) * LIGHT[0] + (y + 0.5 - cy) * LIGHT[1]
        out[(x, y)] = 'e' if v > 0.55 * r else 'c' if v > -0.35 * r else 'b'
    return out


def star_tones(cx, cy, r_in, r_axis, r_diag, n=8, rot=0.0, core=3.0, mid=5.5):
    out = {}
    reach = max(r_axis, r_diag) + 1
    for y in range(int(cy - reach) - 1, int(cy + reach) + 2):
        for x in range(int(cx - reach) - 1, int(cx + reach) + 2):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            th = (math.degrees(math.atan2(dy, dx)) - rot) % 360
            seg = 360.0 / n
            t = (th % seg) / seg  # 0..1 within a spike sector
            idx = int(th // seg)
            tipr = r_axis if idx % 2 == 0 else r_diag
            # triangle wave: spike tip at sector start/end, valley at the middle
            w_ = abs(t - 0.5) * 2  # 1 at tips, 0 at valley
            R = r_in + (tipr - r_in) * w_ ** 2.2
            if idx % 2 == 1:
                # odd sectors start at a diag tip and end at an axis tip
                R = r_in + ((r_diag if t < 0.5 else r_axis) - r_in) * w_ ** 2.2
            else:
                R = r_in + ((r_axis if t < 0.5 else r_diag) - r_in) * w_ ** 2.2
            if d <= R:
                out[(x, y)] = 'W' if d <= core else 'w' if d <= mid else 'v'
    return out


def ring(n, radius, start_deg, jitter=(), cx=24.0, cy=24.0):
    pts = []
    for i in range(n):
        a = math.radians(start_deg + i * 360.0 / n)
        rj = jitter[i % len(jitter)] if jitter else 0.0
        pts.append((cx + (radius + rj) * math.cos(a), cy + (radius + rj) * math.sin(a)))
    return pts


def snap(v):
    """Pixel-centre placement so half-integer radii rasterise as round discs."""
    return math.floor(v) + 0.5


# ---------------------------------------------------------------------------- frames
def frame0():
    f = Frame()
    f.paint(star_tones(24.0, 24.0, 4.2, 9.6, 7.2, rot=0.0, core=2.6, mid=5.0))
    for ang, rad in ((25, 9.5), (100, 10.0), (160, 9.0), (215, 10.5), (290, 9.5), (340, 10.0)):
        a = math.radians(ang)
        f.paint(chunk_tones(snap(24 + rad * math.cos(a)), snap(24 + rad * math.sin(a)), 1.5))
    return f


def frame1():
    f = Frame()
    for (x, y) in ring(7, 11.0, -100, jitter=(0.6, -0.4, 0.3, -0.2, 0.5, -0.5, 0.0)):
        f.paint(puff_tones(snap(x), snap(y), 5.5))
    spikes = [(-80, 5), (-35, 6), (10, 4.5), (55, 6), (100, 5), (145, 6), (190, 4.5), (235, 6)]
    f.paint(splat_tones(24.0, 24.0, 7.5, spikes))
    for ang, ln in spikes:
        a = math.radians(ang)
        rr = 7.5 + ln + 2.6
        f.paint(chunk_tones(snap(24 + rr * math.cos(a)), snap(24 + rr * math.sin(a)), 1.5))
    f.paint({p: 'W' for p in disc(22.5, 22.5, 1.5)} | {p: 'w' for p in disc(22.5, 22.5, 2.5) - disc(22.5, 22.5, 1.5)}, outline=False)
    return f


def frame2():
    f = Frame()
    for (x, y) in ring(7, 8.5, -60):
        f.paint(puff_tones(snap(x), snap(y), 5.5))
    for (x, y) in ring(10, 15.5, -90, jitter=(0.4, -0.3, 0.2, -0.4, 0.3)):
        f.paint(puff_tones(snap(x), snap(y), 6.5))
    spikes = [(-95, 6), (-50, 7.5), (-5, 6), (40, 8), (85, 6.5), (130, 7.5), (175, 6), (220, 8), (265, 5)]
    f.paint(splat_tones(24.0, 24.0, 9.0, spikes))
    for ang, rr in ((-70, 20.0), (-10, 20.5), (60, 20.0), (115, 20.5), (200, 20.0), (250, 19.5)):
        a = math.radians(ang)
        f.paint(chunk_tones(snap(24 + rr * math.cos(a)), snap(24 + rr * math.sin(a)), 2.5))
    return f


def frame3():
    f = Frame()
    spikes = [(-10, 3), (35, 2.5), (80, 2), (140, 3), (190, 3.5), (235, 2), (290, 2.5)]
    f.paint(splat_tones(24.0, 27.0, 10.5, spikes, sy=0.55, glint=True))
    for (x, y, r) in ((11.5, 17.5, 4.5), (36.5, 16.5, 4.5), (18.5, 9.5, 3.5), (30.5, 8.5, 3.5), (7.5, 27.5, 3.5), (40.5, 27.5, 3.5)):
        f.paint(puff_tones(x, y, r, fade=True))
    for (x, y) in ((12.5, 34.5), (36.5, 34.5), (24.5, 37.5)):
        f.paint(chunk_tones(x, y, 1.5))
    return f


def frame4():
    f = Frame()
    spikes = [(0, 2), (60, 1.5), (130, 2), (180, 2.5), (250, 1.5), (310, 2)]
    f.paint(splat_tones(24.0, 28.0, 7.5, spikes, sy=0.55, glint=True))
    # wavy stink lines rising
    for x0, phase, top, bot in ((17, 0.0, 9, 22), (24, 2.2, 5, 21), (31, 4.4, 10, 22)):
        line = {}
        for y in range(top, bot + 1):
            x = int(round(x0 + 1.4 * math.sin(y * 0.75 + phase)))
            line[(x, y)] = 'v' if y < (top + bot) / 2 else 'u'
        f.paint(line)
    return f


FRAMES = [frame0, frame1, frame2, frame3, frame4]


def to_px(grids):
    out = [[(0, 0, 0, 0)] * (W * len(grids)) for _ in range(H)]
    for i, g in enumerate(grids):
        for y in range(H):
            for x in range(W):
                c = PAL[g[y][x]]
                if c:
                    out[y][i * W + x] = fxpng.hexc(c)
    return out


def bbox(g):
    pts = [(x, y) for y in range(H) for x in range(W) if g[y][x] != '.']
    if not pts:
        return None
    return (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts))


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'e1'
    grids = [fn().g for fn in FRAMES]
    for i, g in enumerate(grids):
        print('frame', i, 'bbox', bbox(g))
    px = to_px(grids)
    fxpng.write_png('explo_%s.png' % tag, W * 5, H, px)
    a, b, o = fxpng.view(W * 5, H, px, 5, grid=(W, H))
    fxpng.write_png('explo_%s_5x.png' % tag, a, b, o)
    a, b, o = fxpng.view(W * 5, H, px, 3, bg=FLOOR, grid=(W, H), gridcol=(60, 90, 40, 255))
    fxpng.write_png('explo_%s_3x_floor.png' % tag, a, b, o)
    with open('explo_%s.txt' % tag, 'w') as fh:
        for i, g in enumerate(grids):
            fh.write('# frame %d\n' % i)
            for row in g:
                fh.write(''.join(row) + '\n')
