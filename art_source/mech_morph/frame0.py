"""Frame 0: phase-1-sized Greyson standing, Computah leaping onto his back."""
import math
import build as B
from build import *
from gbig import add_ramp, muscle, interior, mir

add_ramp('p1skin', ['fff0b0', 'f0d080', 'd0b060', 'a09050', '806c34', '605020'])
add_ramp('p1trunk', ['a58ad0', '8060b0', '7050a0', '604090', '402070', '2c1450'])
add_ramp('comp', ['dfe8ee', 'c4d2da', '9badb7', '847e87', '696a6a', '4a4b4d'])
add_ramp('p1sock', ['ffffff', 'ffffff', 'e8e8e8', 'b3b3b3', '8c8c8c', '666666'])
add_ramp('p1shoe', ['4a4a4a', '3a3a3a', '2a2a2a', '1a1a1a', '101010', '080808'])
PX = dict(B.PALC)
for k, v in {'1': 'f0d080', '2': 'd0b060', '3': 'a09050', '4': '605020', '5': '806c34',
             'y': 'd4cc2e', 'Y': '726e17', 'h': 'f4ec50', 'T': 'd95763', 'B': '639bff',
             'M': '4a1a1a', 'm': '9badb7', 'n': '847e87', 'e': '696a6a', 'X': 'ac3232',
             'q': 'c4d2da', 'O': 'e8566a', 'W': 'ffffff', 'x': '402070'}.items():
    PX[k] = hexc(v)
SAVED_PALC = dict(B.PALC)


def use_p1_palette(on=True):
    B.PALC.clear()
    B.PALC.update(PX if on else SAVED_PALC)


def LR(pts):
    m = poly_mask(pts)
    return m, mirror_mask(m)


# ---------------- small Greyson (feet on y95, axis 47.5) ----------------
torso = poly_mask(sym_poly([(48, 59.5), (45, 59.5), (44, 61.5), (40, 62.5), (36.5, 64), (34.5, 66.5), (34.5, 71), (36.5, 75), (39.5, 78), (41, 80), (48, 80)]))
delt = mir(rot_ell_mask(37.5, 66.5, 4.6, 3.8, -25))
uarm = mir(poly_mask(rot_rect(34.5, 72, 9, 5.6, 100, ch=1.5)))
farm = mir(poly_mask(rot_rect(36.5, 77.5, 8.5, 4.6, 35, ch=1.5)))
fist = mir(ell_mask(40.5, 80, 2.6, 2.6))
trunks = poly_mask(sym_poly([(48, 77.5), (40.5, 77.5), (38.5, 81), (37.5, 85.5), (42, 86), (45.5, 84), (48, 84)]))
leg = LR([(38, 83), (45.5, 83), (45.5, 87), (45, 94), (39.5, 94), (38.5, 90), (37.5, 86)])
sock = LR([(36, 89.5), (47, 89.5), (47, 94), (36, 94)])
shoe = LR([(38.5, 93.5), (45.5, 93.5), (46.5, 96), (37, 96)])
ear = LR([(43, 56.5), (44.5, 56.5), (44.5, 59), (43, 59)])

HEAD = """
..kkkk..
.kyhhyk.
kyhyyyyk
kyYTTYyk
kYB33BYk
k2y33y2k
k2yMMy2k
.k2yy2k.
"""

VLINE = "\n".join(["3"] * 16)


def U(a):
    return union(a[0], a[1])


def small_greyson():
    arms = union(U(uarm), U(farm), U(delt))
    render_part('leg', U(leg), 'p1skin', R=3, th=TH_SOFT)
    muscle(U(sock), U(leg), R=2, ramp='p1sock', crease=((0, -1),), crease_col='k', lift=1)
    render_part('shoe', U(shoe), 'p1shoe', R=1, th=TH_SOFT)
    render_part('torso', torso, 'p1skin', R=5, th=TH_SOFT)
    pec = mir(poly_mask([(47.5, 62), (42, 62), (37.5, 64), (36.5, 67), (39, 69.5), (43, 70), (47.5, 69)]))
    muscle(U(pec), torso, R=2, ramp='p1skin', crease=((0, 1),), crease_col='605020')
    stamp(VLINE, 47, 62)
    stamp(VLINE, 47, 62, mirror=True)
    for yy in (73, 76):
        stamp("..333", 42, yy)
        stamp("..333", 42, yy, mirror=True)
    render_part('trunks', trunks, 'p1trunk', R=2, th=TH_SOFT, shadow_below=1)
    render_part('arm', arms, 'p1skin', R=3, th=TH_SOFT)
    muscle(U(delt), arms, R=2, ramp='p1skin', crease=((0, 1), (1, 1)), crease_col='a09050')
    render_part('fist', U(fist), 'p1skin', R=2, th=TH_SOFT)
    render_part('ear', U(ear), 'p1skin', R=1, th=TH_SOFT)
    stamp(HEAD, 44, 53)


# ---------------- leaping Computah (rotated) ----------------
CX, CY, ANG = 29.0, 38.0, 32.0  # body centre, clockwise tilt in degrees


def rot(pts, ang=None, cx=None, cy=None):
    ang = ANG if ang is None else ang
    cx = CX if cx is None else cx
    cy = CY if cy is None else cy
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def rp(x, y):
    (px, py), = rot([(x, y)])
    return int(math.floor(px)), int(math.floor(py))


def put(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        B.canvas[y][x] = col


def line(x0, y0, x1, y1, col=BLACK):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / n
        put(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), col)


def circle_pts(r, n=28, ox=0, oy=0):
    return [(ox + r * math.cos(2 * math.pi * i / n), oy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def limb(pts, col=BLACK):
    wp = rot(pts)
    for (x0, y0), (x1, y1) in zip(wp, wp[1:]):
        line(x0, y0, x1, y1, col)


def joint(x, y):
    (px, py), = rot([(x, y)])
    ix, iy = int(round(px)), int(round(py))
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        put(ix + dx, iy + dy, BLACK)
    put(ix, iy, PX['e'])


def small_computah():
    limb([(-3, 6), (-5, 11), (-11, 13)])
    limb([(3, 6), (2, 12), (-4, 16)])
    joint(-5, 11)
    joint(2, 12)
    render_part('cfoot', union(poly_mask(rot([(-14, 11.5), (-10, 12), (-10, 14.5), (-14.5, 14)])),
                               poly_mask(rot([(-7, 15), (-3, 15), (-3, 17.5), (-7.5, 17)]))), 'comp', R=1, th=TH_SOFT)
    render_part('cbody', poly_mask(rot([(-5.5, -6), (5.5, -6), (5.5, 7), (-5.5, 7)])), 'comp', R=3, th=TH_SOFT)
    for (x, y, c) in [(-3, -3, 'k'), (-2, -2, 'k'), (-1, -2, 'n'), (0, -2, 'n'), (1, -2, 'k'), (2, -3, 'k'),
                      (-2, -3, 'n'), (-1, -3, 'n'), (0, -3, 'n'), (1, -3, 'n'), (-1, -1, 'k'), (0, -1, 'k')]:
        px, py = rp(x + 0.5, y + 0.5)
        put(px, py, BLACK if c == 'k' else PX[c])
    limb([(6, -4), (13, -7), (20, -3)])
    limb([(-5, -4), (2, -9), (10, -8)])
    joint(13, -7)
    joint(2, -9)
    h1 = rot([(21.5, -2.5)])[0]
    h2 = rot([(11.5, -7.5)])[0]
    render_part('chand', union(ell_mask(h1[0], h1[1], 2.2, 2.2), ell_mask(h2[0], h2[1], 2.2, 2.2)), 'comp', R=1, th=TH_SOFT)
    render_part('cneck', poly_mask(rot([(-2.5, -8.5), (2.5, -8.5), (2.5, -6), (-2.5, -6)])), 'comp', R=1, th=TH_SOFT)
    head = poly_mask(rot(circle_pts(6.4, 32, 0, -14.5)))
    render_part('chead', head, 'comp', R=4, th=TH_SOFT)
    for x in range(-4, 5):
        px, py = rp(x + 0.5, -11.5)
        put(px, py, PX['n'])
    for ex in (-2.5, 2.5):
        for ey in (-16, -15):
            px, py = rp(ex, ey + 0.5)
            put(px, py, PX['X'])
    limb([(0, -21), (1, -24), (3, -25)])
    px, py = rp(3.5, -25.5)
    put(px, py, PX['X'])
    put(px + 1, py, PX['X'])


def speed_lines():
    for (x0, y0, L) in [(8, 52, 9), (12, 58, 12), (5, 46, 6), (16, 62, 7), (2, 40, 5)]:
        for t in range(L):
            x = int(round(x0 + t * math.cos(math.radians(-50))))
            y = int(round(y0 + t * math.sin(math.radians(-50))))
            if 0 <= x < W and 0 <= y < H and B.canvas[y][x] is None:
                B.canvas[y][x] = PX['W'] if t > L * 0.6 else PX['r']


def clear():
    for y in range(H):
        for x in range(W):
            B.canvas[y][x] = None


def build():
    clear()
    use_p1_palette(True)
    small_computah()
    small_greyson()
    speed_lines()
    use_p1_palette(False)
    return [row[:] for row in B.canvas]


if __name__ == '__main__':
    build()
    save('f0.png')
    save('f0_8x.png', 8, (120, 160, 120, 255))
