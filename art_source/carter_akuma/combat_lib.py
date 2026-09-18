"""Shared helpers for Carter's combat set (idle / eye flash / rush / rush pass /
spent / hit / defeat).

Everything here works in the same vocabulary as the approved sheet: masks are
96x96 grids of bool, canvases are lib.Canvas, and every colour that lands on a
pixel comes out of lib.PAL.  Nothing in this file draws Carter - it only moves,
lights and roughs up what parts.py / render.py already know how to draw.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, ring,
                 erode, poly, ell, PALC, BLACK, bayer, band, hexc, RAMPS,
                 TH_HARD, TH_HARD2)
import parts as P
import intro_lib as IL
from intro_lib import mixc

FEET = 95          # floor plane: bottom row of every frame


def _S():
    import lib
    return lib.SCALE


def _T(x, y):
    import lib
    return lib.T(x, y)


def _Tp(x, y):
    import lib
    return lib.Tp(x, y)


def _Tinv(x, y):
    import lib
    ax, ay = lib.ANCHOR
    return ax + (x - ax) / lib.SCALE, ay + (y - ay) / lib.SCALE


def dpx(v):
    """a design-space delta as a whole number of pixels"""
    return int(round(v * _S()))
AXC = 47.5


# ---------------------------------------------------------------- transforms

def shift_mask(m, dx, dy):
    out = empty()
    for y in range(H):
        sy = y - dy
        if not (0 <= sy < H):
            continue
        row = m[sy]
        for x in range(W):
            sx = x - dx
            if 0 <= sx < W and row[sx]:
                out[y][x] = True
    return out


def shift_canvas(cv, dx, dy):
    out = Canvas()
    for y in range(H):
        sy = y - dy
        if not (0 <= sy < H):
            continue
        row = cv.px[sy]
        for x in range(W):
            sx = x - dx
            if 0 <= sx < W:
                out.px[y][x] = row[sx]
    return out


def scale_mask(m, sx, sy, cx, cy):
    """Nearest-neighbour resample of a MASK about (cx, cy).  Safe on masks in a
    way it would not be on finished pixels - nothing is blurred, the shape is
    just re-rasterised, and it is then shaded from scratch like any other part."""
    out = empty()
    for y in range(H):
        for x in range(W):
            sxx = int(round(cx + (x + 0.5 - cx) / sx - 0.5))
            syy = int(round(cy + (y + 0.5 - cy) / sy - 0.5))
            if 0 <= sxx < W and 0 <= syy < H and m[syy][sxx]:
                out[y][x] = True
    return out


def mask_bbox(m):
    xs = [x for y in range(H) for x in range(W) if m[y][x]]
    ys = [y for y in range(H) for x in range(W) if m[y][x]]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def rot_pts(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa,
             cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def warp_rows(cv, src_of):
    """Rebuild a canvas by pulling each output row from src_of(y).

    Used for breathing: a 1px lift of everything above the belt costs one
    duplicated row down in the flat navy of the trousers, where nobody can see
    it, and keeps the approved pixels everywhere else."""
    out = Canvas()
    for y in range(H):
        sy = src_of(y)
        if 0 <= sy < H:
            out.px[y] = cv.px[sy][:]
    return out


def breathe(cv, d, seam=74):
    """Lift everything above `seam` by d rows; the seam row is what doubles."""
    if d <= 0:
        return cv.copy()
    seam = int(round(_T(0.0, seam)[1]))
    return warp_rows(cv, lambda y: y + d if y < seam else
                     (seam if y < seam + d else y))


# ---------------------------------------------------------------- geometry

def cyl(a, b, r0, r1=None):
    return P.cyl(a, b, r0, r1)


def joint(c, r):
    return ell(c[0], c[1], r, r)


def limb(a, b, c, r0, r1, r2):
    """upper + lower segment with a rounded joint at the elbow / knee."""
    return union(union(cyl(a, b, r0, r1), cyl(b, c, r1, r2)), joint(b, r1))


def foot_at(ank, deg, ln=13.0, hi=4.6, heel=3.4):
    """A barefoot sole pointing `deg` (0 = toes to the right)."""
    pts = [(-heel, -hi * 0.55), (ln * 0.30, -hi), (ln * 0.80, -hi * 0.80),
           (ln, -hi * 0.18), (ln * 0.96, hi * 0.62), (ln * 0.30, hi * 0.92),
           (-heel * 0.82, hi * 0.80), (-heel * 1.05, hi * 0.12)]
    return poly(rot_pts([(ank[0] + x, ank[1] + y) for x, y in pts],
                        ank[0], ank[1], deg))


def hem_cut(lo, hi, step=3.0, x0=-2.0, x1=99.0):
    """everything below a horizontal zigzag - torn cloth still hangs down, even
    when the body wearing it is horizontal, so this stays axis aligned."""
    return P._hem_cut(lo, hi, step=step, x0=x0, x1=x1)


def cut_beyond(a, b, t, amp=2.2, step=3.0, reach=60.0):
    """Everything past a ragged line drawn square across a->b at fraction t.

    A trouser leg torn off round a thigh that is nearly horizontal cannot use a
    horizontal zigzag - the tear has to run round the limb, not across the
    screen."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    cx, cy = ax + dx * t, ay + dy * t
    pts = []
    s = -reach
    i = 0
    while s <= reach:
        off = amp if i % 2 == 0 else -amp
        pts.append((cx + nx * s + ux * off, cy + ny * s + uy * off))
        s += step
        i += 1
    pts.append((cx + nx * reach + ux * reach, cy + ny * reach + uy * reach))
    pts.append((cx - nx * reach + ux * reach, cy - ny * reach + uy * reach))
    return poly(pts)


def tail(root, ang, ln, w0, w1, curl=0.0, n=16):
    """A whipping strip of torn cloth: bezier spine, tapering width.  Same
    machinery as the aura tendrils so the shapes rhyme."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    px, py = -sa, ca
    ctrl = []
    for f in (0.0, 0.34, 0.70, 1.0):
        off = curl * ln * math.sin(f * math.pi * 1.05)
        ctrl.append((root[0] + ca * ln * f + px * off,
                     root[1] + sa * ln * f + py * off))
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        cx, cy = _bez(ctrl, t)
        ax, ay = _bez(ctrl, min(1.0, t + 0.03))
        bx, by = _bez(ctrl, max(0.0, t - 0.03))
        dx, dy = ax - bx, ay - by
        L = math.hypot(dx, dy) or 1.0
        qx, qy = -dy / L, dx / L
        wd = (w0 + (w1 - w0) * (t ** 0.8)) / 2.0
        left.append((cx + qx * wd, cy + qy * wd))
        right.append((cx - qx * wd, cy - qy * wd))
    return poly(left + list(reversed(right)))


def _bez(pts, t):
    p = list(pts)
    while len(p) > 1:
        p = [((1 - t) * p[i][0] + t * p[i + 1][0],
              (1 - t) * p[i][1] + t * p[i + 1][1]) for i in range(len(p) - 1)]
    return p[0]


# ---------------------------------------------------------------- light

def point_light(cv, body, cx, cy, level, reach=26.0, hot='x'):
    """Warm bounce radiating from an arbitrary source (the eyes, a fist).
    intro_lib.rim_light does this only from the back mark."""
    if level <= 0.04:
        return
    cx, cy = _T(cx, cy)
    reach = reach * _S()
    edge = sub(body, erode(body, 1))
    inner = sub(erode(body, 1), erode(body, 2))
    for m, amt in ((edge, 1.0), (inner, 0.5)):
        for y in range(H):
            for x in range(W):
                if not m[y][x] or cv.px[y][x] is None or cv.px[y][x] == BLACK:
                    continue
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                f = max(0.0, 1.0 - d / reach)
                a = f * amt * level
                if a < 0.12:
                    continue
                c = PALC[hot] if a > 0.62 else (PALC['X'] if a > 0.34 else PALC['y'])
                cv.px[y][x] = mixc(cv.px[y][x], c, min(0.88, a))


def face_bloom(cv, cx, cy, level, r=9.0):
    """White spill washing off the eye sockets across the surrounding skin."""
    if level <= 0.05:
        return
    for y in range(H):
        for x in range(W):
            c = cv.px[y][x]
            if c is None or c == BLACK:
                continue
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            f = max(0.0, 1.0 - d / r) ** 1.3
            a = f * level
            if a < 0.14:
                continue
            cv.px[y][x] = mixc(c, PALC['M'] if a > 0.66 else PALC['O'],
                               min(0.85, a))


def ground_pool(cv, level, cx=47.5, row=94, span=30.0, hot='Y', cool='z'):
    """floor lit from above - wider and flatter than intro_lib.ground_glow."""
    if level <= 0.06:
        return
    cx = _T(cx, 0.0)[0]
    row = int(round(_T(0.0, row)[1]))
    span = span * _S()
    for dy in range(0, 6):
        y = row - dy
        if not (0 <= y < H):
            continue
        wdt = span * level * (1.0 - dy * 0.15)
        for x in range(W):
            if cv.px[y][x] is not None:
                continue
            d = abs(x + 0.5 - cx)
            if d > wdt:
                continue
            f = 1.0 - d / max(1e-6, wdt)
            lvl = int(round(16 * f * level * (1.0 - dy * 0.20)))
            if lvl > 0 and bayer(_ONE, lvl, dy)[y][x]:
                cv.px[y][x] = PALC[hot] if f > 0.58 else PALC[cool]


_ONE = [[True] * W for _ in range(H)]


# ---------------------------------------------------------------- motion

def streaks(cv, body, rows, back=-1, ln=(10, 26), seed=0,
            ramp=('X', 'y', 'Y', 'z', 'Z')):
    """Wind lines trailing the way he came from.

    They have to LEAVE HIM: an evenly dashed line starting a few pixels clear
    of the silhouette reads as tracer fire, not speed.  So each line starts
    solid right off his trailing edge, steps down the ember ramp as it goes,
    and only breaks up in its last third."""
    rows = [int(round(_T(0.0, y)[1])) for y in rows]
    ln = (ln[0] * _S(), ln[1] * _S())
    for i, y0 in enumerate(rows):
        if not (0 <= y0 < H):
            continue
        xs = [x for x in range(W) if body[y0][x]]
        if not xs or (max(xs) - min(xs)) < 4:
            continue
        x0 = min(xs) if back < 0 else max(xs)
        L = int(ln[0] + (seed * 7 + i * 5) % max(1, int(ln[1] - ln[0])))
        for t in range(1, L):
            x = x0 + back * t
            if not (0 <= x < W) or cv.px[y0][x] is not None:
                continue
            f = t / float(L)
            if f > 0.62 and (t + i + seed) % 2:
                continue
            cv.px[y0][x] = PALC[ramp[min(len(ramp) - 1, int(f * len(ramp)))]]


def impact_arc(cv, cx, cy, r0, r1, a0, a1, ch='x', step=3):
    """A broken arc of light where a strike bites - lives on the sprite so the
    clones carry their own hit read even before the FX layer lands."""
    n = 64
    for i in range(n):
        t = i / (n - 1.0)
        a = math.radians(a0 + (a1 - a0) * t)
        for rr in range(int(r0), int(r1)):
            x = int(round(cx + math.cos(a) * rr))
            y = int(round(cy + math.sin(a) * rr))
            if not (0 <= x < W and 0 <= y < H):
                continue
            if cv.px[y][x] is not None:
                continue
            if (i + rr) % step:
                continue
            cv.px[y][x] = PALC[ch] if rr < (r0 + r1) / 2 else PALC['y']


def dust(cv, cx, row, level, span=16.0, seed=0):
    """scuffed floor grit kicked up under a plant or a skid."""
    if level <= 0.05:
        return
    cx = _T(cx, 0.0)[0]
    row = int(round(_T(0.0, row)[1]))
    span = span * _S()
    for i in range(26):
        ph = i * 2.39 + seed
        f = (i % 7) / 6.0
        x = int(round(cx + math.cos(ph) * span * (0.3 + f)))
        y = int(round(row - abs(math.sin(ph)) * 9.0 * level * (0.4 + f)))
        if not (0 <= x < W and 0 <= y < H) or cv.px[y][x] is not None:
            continue
        if (i * 3 + seed) % 3 == 0:
            cv.px[y][x] = PALC['T'] if f > 0.5 else PALC['S']


# ---------------------------------------------------------------- aura

def guttering(k, level, roots, scale=1.0):
    """Aura specs for a beaten Carter: short, low, drooping strands that fall
    off him rather than the confident crown of the standing sheet."""
    out = []
    for i, (rx, ry, ang, ln, w0) in enumerate(roots):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa, ca
        L = ln * (0.35 + 0.65 * level) * scale
        ph = k * math.pi / 2 + i * 1.31
        pts = []
        for f in (0.0, 0.34, 0.70, 1.0):
            off = math.sin(f * math.pi) * 3.0 * math.sin(ph) * level
            # gravity: the further out, the more it sags
            sag = 3.6 * f * f * (1.0 - level)
            pts.append((rx + ca * L * f + px * off,
                        ry + sa * L * f + py * off + sag))
        out.append((pts, max(1.8, w0 * (0.45 + 0.55 * level) * scale), 1.0))
    return out


SPENT_ROOTS = [
    (30.0, 58.0, -168.0, 15.0, 5.0),
    (24.0, 70.0,  172.0, 13.0, 4.4),
    (36.0, 48.0, -140.0, 13.0, 4.6),
    (62.0, 50.0,  -38.0, 14.0, 4.8),
    (70.0, 62.0,   -8.0, 13.0, 4.4),
    (54.0, 78.0,   22.0, 11.0, 3.8),
    (40.0, 82.0,  158.0, 11.0, 3.8),
]


def roots_from(body, rows=None, out=1.0):
    """Aura roots taken off the silhouette the pose actually has.

    A fixed root list written for the standing sheet puts every strand inside a
    kneeling body, where the aura painter subtracts it and nothing survives -
    which is how the punish window and the whole back half of the defeat ended
    up with no aura at all.  Sampling the edge means the wisps always leave him
    from his real outline, whatever shape he is in."""
    if rows is None:
        rows = (0.10, 0.30, 0.50, 0.72, 0.92)
    ys = [y for y in range(H) if any(body[y])]
    if not ys:
        return []
    # measured off the rasterised silhouette, so the seeds come back in PIXEL
    # space; guttering feeds them to the tendril builder, which is design
    # space, so they have to be mapped back or they get scaled twice
    y0, y1 = min(ys), max(ys)
    seeds = []
    for i, f in enumerate(rows):
        y = int(round(y0 + (y1 - y0) * f))
        xs = [x for x in range(W) if body[y][x]]
        if not xs:
            continue
        span = max(6, max(xs) - min(xs))
        w0 = 3.2 + 3.4 * (1.0 - abs(f - 0.35))
        ln = (9.0 + 12.0 * (1.0 - f)) * out
        # left root points out and down, right root mirrors it
        lx, ly = _Tinv(min(xs) + 0.5, y + 0.5)
        rx, ry = _Tinv(max(xs) - 0.5, y + 0.5)
        seeds.append((lx, ly, 170.0 + 18.0 * f, ln, w0))
        seeds.append((rx, ry, 10.0 - 18.0 * f, ln * 0.92, w0 * 0.92))
    return seeds


def sweat(cv, pts, ch='O'):
    for x, y in pts:
        if 0 <= x < W and 0 <= y < H and cv.px[y][x] is not None:
            cv.px[y][x] = PALC[ch]


# ---------------------------------------------------------------- checks

def bottom_row(cv):
    for y in range(H - 1, -1, -1):
        if any(p is not None for p in cv.px[y]):
            return y
    return -1


def solid_bbox(px):
    xs = [x for y in range(len(px)) for x in range(len(px[0])) if px[y][x][3]]
    ys = [y for y in range(len(px)) for x in range(len(px[0])) if px[y][x][3]]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)
