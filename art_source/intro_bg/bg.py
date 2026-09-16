"""Background: hallway floor, walls, ARENA #1 banners, desk."""
import math
import random
from canvas import (Canvas, poly_mask, func_mask, boundary, line_pts, polyline_pts,
                    pixel_perfect, dedupe, bayer)

W, H = 640, 360


def xl(y):
    """First floor pixel column on the left wall line (2:5 slope)."""
    return 146 - (2 * y) // 5


def xr(y):
    return W - 1 - xl(y)


# ------------------------------------------------------------------ text
# Stroke font, 8 wide x 14 tall, y up.
GLYPHS = {
    'A': [[(0, 0), (0, 11), (5, 16), (10, 11), (10, 0)], [(0, 7), (10, 7)]],
    'R': [[(0, 0), (0, 16), (7, 16), (10, 13), (10, 11), (7, 8), (0, 8)], [(5, 8), (10, 3), (10, 0)]],
    'E': [[(10, 16), (0, 16), (0, 0), (10, 0)], [(0, 8), (7, 8)]],
    'N': [[(0, 0), (0, 16), (10, 0), (10, 16)]],
    '#': [[(3, 1), (3, 15)], [(7, 1), (7, 15)], [(0, 5), (10, 5)], [(0, 11), (10, 11)]],
    '1': [[(5, 0), (5, 16), (2, 13)], [(2, 0), (8, 0)]],
}


def text_strokes():
    """Return list of font-space polylines for 'ARENA' over '#1'."""
    strokes = []
    adv = 14
    for i, ch in enumerate('ARENA'):
        for pl in GLYPHS[ch]:
            strokes.append([(x + i * adv, y) for (x, y) in pl])
    # second line, centred under ARENA (ARENA spans 0..66, '#1' spans 0..22)
    ox = 22
    oy = -23
    for i, ch in enumerate('#1'):
        for pl in GLYPHS[ch]:
            strokes.append([(x + ox + i * adv, y + oy) for (x, y) in pl])
    return strokes


BRUSH = [(0, 0), (1, 0), (0, 1), (1, 1)]


def text_pixels_left(Ox, Oy):
    """Text rotated 45deg CCW (reads up-right). Returns set of pixels."""
    pix = set()
    for pl in text_strokes():
        pts = [(Ox + fx - fy, Oy - fx - fy) for (fx, fy) in pl]
        for a, b in zip(pts, pts[1:]):
            seg = line_pts(a[0], a[1], b[0], b[1])
            dx = abs(b[0] - a[0])
            dy = abs(b[1] - a[1])
            for (x, y) in seg:
                for ox2, oy2 in BRUSH:
                    pix.add((x + ox2, y + oy2))
    return pix


def rotate_cw_about(pix, cx, cy):
    """Rotate pixel set 90deg clockwise (screen coords, y down) about (cx, cy)."""
    out = set()
    for (x, y) in pix:
        dx = x - cx
        dy = y - cy
        out.add((int(cx - dy), int(cy + dx)))
    return out


# ------------------------------------------------------------------ build

def build_background():
    cv = Canvas(W, H, 'F')
    rnd = random.Random(7)

    # ---- walls and wall/floor junction lines
    for y in range(H):
        a = xl(y)
        for x in range(0, max(0, a - 2)):
            cv.set(x, y, 'M')
        for x in range(max(0, a - 2), max(0, a)):
            cv.set(x, y, 'K')
        b = xr(y)
        for x in range(b + 3, W):
            cv.set(x, y, 'M')
        for x in range(b + 1, min(W, b + 3)):
            cv.set(x, y, 'K')

    # ---- floor texture: far end of the hallway falls off with a deliberate 4x4 Bayer ramp,
    #      plus sparse concrete speckle.
    for y in range(0, 22):
        t = 1.0 - y / 22.0          # 1 at top edge -> 0
        for x in range(xl(y), xr(y) + 1):
            if bayer(x, y) < t * 0.55:
                cv.set(x, y, 'D')
    for y in range(H):
        for x in range(xl(y) + 8, xr(y) - 6):
            h = _hash(x, y, 11)
            if h < 0.006:
                cv.set(x, y, 'D')

    # ---- wall base: ambient occlusion band on the wall side of the junction
    for y in range(H):
        a = xl(y) - 2
        for x in range(max(0, a - 3), max(0, a)):
            if x >= a - 2 or bayer(x, y) < 0.5:
                if cv.get(x, y) == 'M':
                    cv.set(x, y, 'N')
        b = xr(y) + 3
        for x in range(b, min(W, b + 3)):
            if x < b + 2 or bayer(x, y) < 0.5:
                if cv.get(x, y) == 'M':
                    cv.set(x, y, 'N')

    # ---- floor: cast shadow from the left wall (light from upper-left),
    #      thin contact shadow on the right wall.
    for y in range(H):
        a = xl(y)
        for x in range(a, a + 5):
            cv.set(x, y, 'D')
        for x in range(a + 5, a + 7):
            if bayer(x, y) < 0.5:
                cv.set(x, y, 'D')
        b = xr(y)
        cv.set(b, y, 'D')
        if bayer(b - 1, y) < 0.5:
            cv.set(b - 1, y, 'D')

    # ---- left banner
    def in_banner_left(x, y):
        return (x < 58 + 8.0 * y / 7.0) and (x > 0.875 * (y - 122)) and (x < xl(int(y)) - 2)

    ban = func_mask(in_banner_left, 0, 0, 160, 220)
    edge = boundary(ban)
    cv.paint_mask(ban, 'N')
    # trim: indigo band just inside the long edges
    trim = set()
    for (x, y) in ban:
        cx, cy = x + 0.5, y + 0.5
        d_top = (58 + 8.0 * cy / 7.0) - cx          # horizontal distance to top edge
        d_bot = cx - 0.875 * (cy - 122)
        if 3.0 <= d_top < 4.0 or 3.0 <= d_bot < 4.0:
            trim.add((x, y))
    cv.paint_mask(trim, 'I')
    cv.paint_mask(edge, 'K')

    # ---- right banner (mirror geometry)
    ban_r = {(W - 1 - x, y) for (x, y) in ban}
    edge_r = {(W - 1 - x, y) for (x, y) in edge}
    trim_r = {(W - 1 - x, y) for (x, y) in trim}
    cv.paint_mask(ban_r, 'N')
    cv.paint_mask(trim_r, 'I')
    cv.paint_mask(edge_r, 'K')

    # ---- text
    Ox, Oy = 21, 114
    tl = text_pixels_left(Ox, Oy)
    tl = {p for p in tl if p in ban}
    # right banner: mirror the block centre, then rotate glyphs clockwise
    # left block centre in screen coords
    cxl = sum(p[0] for p in tl) / len(tl)
    cyl = sum(p[1] for p in tl) / len(tl)
    tr = rotate_cw_about(tl, cxl, cyl)
    cxr = sum(p[0] for p in tr) / len(tr)
    cyr = sum(p[1] for p in tr) / len(tr)
    tx = int(round((W - 1 - cxl) - cxr))
    ty = int(round(cyl - cyr))
    tr = {(x + tx, y + ty) for (x, y) in tr}
    cv.paint_mask(tl, 'W')
    cv.paint_mask({p for p in tr if p in ban_r}, 'W')
    lost = len([p for p in tr if p not in ban_r])
    print('text px left', len(tl), 'right', len(tr), 'right px outside banner', lost)

    draw_desk(cv, rnd)
    return cv, ban, ban_r


DESK_TOP = [(190, 97), (450, 97), (458, 266), (182, 266)]
APRON = [(182, 266), (458, 266), (458, 273), (182, 273)]
LEG_L = [(183, 272), (191, 272), (209, 334), (201, 334)]
LEG_R = [(W - x, y) for (x, y) in LEG_L]


def desk_masks():
    top = poly_mask(DESK_TOP)
    apron = poly_mask(APRON)
    return top, apron


def _hash(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 4294967295.0


def _vnoise(x, s=0):
    """1D value noise, smooth."""
    i = math.floor(x)
    f = x - i
    a = _hash(i, 0, s)
    b = _hash(i + 1, 0, s)
    t = f * f * (3 - 2 * f)
    return a + (b - a) * t


# (cx, cy, width, amplitude) cathedral figures and (cx, cy, radius, strength) knots
CATHEDRALS = [(236, 214, 30.0, 2.6), (392, 162, 34.0, -2.4), (300, 120, 26.0, 1.4)]
KNOTS = [(356, 226, 5.5, 1.5), (214, 138, 4.5, 1.2)]
SPACING = 6.5


def grain_phase(x, y):
    ph = y / SPACING
    ph += 0.35 * math.sin(x / 41.0 + y / 23.0) + 0.25 * _vnoise(x / 37.0, int(y // 13))
    for (cx, cy, w, a) in CATHEDRALS:
        dx = (x - cx) / w
        dy = (y - cy) / 26.0
        ph += a * math.exp(-dx * dx) * math.exp(-dy * dy)
    for (cx, cy, r, s) in KNOTS:
        d2 = ((x - cx) ** 2 + ((y - cy) * 1.8) ** 2) / (r * r)
        ph += s * math.exp(-d2 * 0.35)
    return ph


def grain_lines(top, rnd):
    """Wood grain as contour lines of a flowing phase field (cathedrals + knots)."""
    pix = set()
    F = {}
    for (x, y) in top:
        F[(x, y)] = math.floor(grain_phase(x + 0.5, y + 0.5))
    for (x, y) in top:
        f = F[(x, y)]
        below = F.get((x, y + 1))
        right = F.get((x + 1, y))
        if (below is not None and below > f) or (right is not None and right != f and abs(grain_phase(x + 0.5, y + 0.5) % 1.0 - 0.5) > 0.3):
            # break the line into dashes along x
            if _vnoise((x + y * 3) / 9.0, 3) > 0.28:
                pix.add((x, y))
    return pix


def knot_pixels(top):
    """Elongated dark knot cores: B ellipse with an M centre."""
    outer, inner = set(), set()
    for (cx, cy, r, s) in KNOTS:
        for (x, y) in top:
            dx = (x + 0.5 - cx) / (r * 0.95)
            dy = (y + 0.5 - cy) / (r * 0.42)
            d = dx * dx + dy * dy
            if d <= 1.0:
                outer.add((x, y))
            if d <= 0.28:
                inner.add((x, y))
    return outer, inner


def draw_desk(cv, rnd):
    top, apron = desk_masks()
    leg_l = poly_mask(LEG_L)
    leg_r = poly_mask(LEG_R)

    # cast shadow on floor (light from upper-left -> offset down-right)
    shadow = set()
    for (x, y) in top | apron | leg_l | leg_r:
        shadow.add((x + 7, y + 9))
    for p in shadow:
        if cv.get(*p) == 'F':
            cv.set(p[0], p[1], 'D')

    # legs
    for leg in (leg_l, leg_r):
        cv.paint_mask(leg, 'B')
        rows = {}
        for (x, y) in leg:
            rows.setdefault(y, []).append(x)
        for y, xs in rows.items():
            cv.set(min(xs) + 1, y, 'w')
        cv.paint_mask(boundary(leg), 'K')

    # apron (front face of the top)
    cv.paint_mask(apron, 'B')
    for (x, y) in apron:
        if y == 267:
            cv.set(x, y, 'w')
    cv.paint_mask(boundary(apron), 'K')

    # top surface
    cv.paint_mask(top, 'w')
    cv.paint_mask(grain_lines(top, rnd), 'B')
    ko, ki = knot_pixels(top)
    cv.paint_mask(ko, 'B')
    cv.paint_mask(ki, 'M')
    edge = boundary(top)
    # lit bevel just inside the back and left edges (light from upper-left)
    for (x, y) in top:
        if (x, y) in edge:
            continue
        if (x, y - 1) in edge or (x - 1, y) in edge:
            if cv.get(x, y) in ('w', 'B'):
                cv.set(x, y, 'd')
    cv.paint_mask(edge, 'K')


if __name__ == '__main__':
    cv, _, _ = build_background()
    cv.save('stage1_bg.png')
    cv.save('stage1_bg_2x.png', 2)
