"""Helpers for Carter's entrance: palette-safe tinting, the materialise
dissolve, the sigil flare, rim lights and the swept aura.

Everything here works on the same 96x96 Canvas the approved sheet uses, so the
entrance frames are guaranteed to share the shipped palette and feet plane.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, ring,
                 erode, poly, ell, PALC, PAL, BLACK, bayer, band, hexc, RAMPS)
import parts as P
import aura as AU

AXC = 47.5
MARK_C = (47.5, 52.0)          # centre of the sigil on the back
FEET = 95                      # feet plane, bottom row of the frame

# ---------------------------------------------------------------- palette

_PAL_LIST = [(k, c) for k, c in PALC.items()]


def nearest_pal(rgb):
    """snap an arbitrary RGB to the shipped Carter palette (keeps the
    colour count near the approved sheet's 55)."""
    best, bd = None, 1 << 30
    r, g, b = rgb[0], rgb[1], rgb[2]
    for _, c in _PAL_LIST:
        d = (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2
        if d < bd:
            bd, best = d, c
    return best


_SNAP_CACHE = {}


def _snap(rgb):
    key = (rgb[0], rgb[1], rgb[2])
    v = _SNAP_CACHE.get(key)
    if v is None:
        v = nearest_pal(key)
        _SNAP_CACHE[key] = v
    return v


def mixc(a, b, t):
    """blend two RGBA colours and snap back onto the palette."""
    if t <= 0:
        return a
    if t >= 1:
        return b
    return _snap((a[0] + (b[0] - a[0]) * t,
                  a[1] + (b[1] - a[1]) * t,
                  a[2] + (b[2] - a[2]) * t))


def tint(cv, mask, col, t, skip_black=False):
    for y in range(H):
        for x in range(W):
            if mask[y][x] and cv.px[y][x] is not None:
                if skip_black and cv.px[y][x] == BLACK:
                    continue
                cv.px[y][x] = mixc(cv.px[y][x], col, t)


# ---------------------------------------------------------------- noise

def _hash(x, y, s):
    n = (x * 374761393 + y * 668265263 + s * 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def blob_noise(seed=0, cell=5.0):
    """smooth value noise on a coarse grid - big soft blobs, not static."""
    g = [[0.0] * W for _ in range(H)]
    gw = int(W / cell) + 3
    gh = int(H / cell) + 3
    lat = [[_hash(i, j, seed) for i in range(gw)] for j in range(gh)]
    for y in range(H):
        fy = y / cell
        j = int(fy)
        ty = fy - j
        ty = ty * ty * (3 - 2 * ty)
        for x in range(W):
            fx = x / cell
            i = int(fx)
            tx = fx - i
            tx = tx * tx * (3 - 2 * tx)
            a = lat[j][i] + (lat[j][i + 1] - lat[j][i]) * tx
            b = lat[j + 1][i] + (lat[j + 1][i + 1] - lat[j + 1][i]) * tx
            g[y][x] = a + (b - a) * ty
    return g


_FIELD = None


def form_field():
    """0 at the mark, ~1 at the extremities: the Satsui no Hado knits his body
    together outward from the sigil, so the mark is literally the seed."""
    global _FIELD
    if _FIELD is not None:
        return _FIELD
    n1 = blob_noise(7, 6.5)
    n2 = blob_noise(19, 3.0)
    cx, cy = MARK_C
    f = [[0.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            d = math.hypot((x + 0.5 - cx) * 0.86, (y + 0.5 - cy) * 1.06) / 52.0
            # mostly radial so the reveal reads as one front travelling out
            # from the mark; the noise only roughens its edge
            f[y][x] = d * 0.90 + n1[y][x] * 0.19 + n2[y][x] * 0.06
    _FIELD = f
    return f


def field_mask(thr, inside=None):
    return field_band(-9.0, thr, inside)


def field_band(lo, hi, inside=None):
    f = form_field()
    m = empty()
    for y in range(H):
        for x in range(W):
            if lo <= f[y][x] < hi and (inside is None or inside[y][x]):
                m[y][x] = True
    return m


# ---------------------------------------------------------------- sigil

def sigil_bbox(pad=0):
    import poses as PO
    sg = PO.sigil()
    xs = [x for y in range(H) for x in range(W) if sg[y][x]]
    ys = [y for y in range(H) for x in range(W) if sg[y][x]]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def sigil_paint(cv, sg, level):
    """repaint the mark. level 0 = the approved dim ember, 1 = white-hot.

    The core ladder is chosen so at level 1 the sigil holds the only pure
    white in the frame - it must be the brightest thing on screen."""
    core = erode(sg, 1)
    edge = sub(sg, core)
    if level < 0.18:
        cmid, cedge, cout = PALC['Y'], PALC['z'], PALC['9']
    elif level < 0.42:
        cmid, cedge, cout = PALC['y'], PALC['Y'], PALC['z']
    elif level < 0.70:
        cmid, cedge, cout = PALC['X'], PALC['y'], PALC['Y']
    elif level < 0.90:
        cmid, cedge, cout = PALC['x'], PALC['X'], PALC['y']
    else:
        cmid, cedge, cout = PALC['M'], PALC['x'], PALC['X']
    # Past half flare the contour goes DARK instead of climbing the ramp with
    # the fill.  A hot contour dissolves into the bloom and the emblem turns
    # into a white blob at exactly the beat the player is meant to read it;
    # a near-black edge keeps the silhouette cut out of the glow.
    if level >= 0.55:
        cout = PALC['9'] if level >= 0.80 else PALC['z']
    cv.paint(sg, cedge)
    cv.paint(core, cmid)
    if level >= 0.90:
        # keep the hottest white off the emblem's own edge so the stroke
        # shapes stay distinct rather than fusing into one mass
        cv.paint(erode(sg, 2), PALC['M'])
    cv.outline(sg, cout)
    return core, edge


def sigil_bloom(cv, sg, level, host=None):
    """light spilling off the mark across the cloth it is painted on."""
    if level <= 0.02:
        return
    reach = 2 + int(round(level * 7))
    # start at ring 2: ring 1 belongs to the emblem's dark contour, and a bloom
    # laid over that contour is what let the glow eat the shape
    prev = grow(sg, 1)
    for i in range(2, reach + 2):
        rg = sub(grow(sg, i), prev)
        prev = grow(sg, i)
        if host is not None:
            rg = inter(rg, host)
        fall = max(0.0, 1.0 - (i - 1) / float(reach))
        lvl = int(round(16 * fall * (0.35 + 0.65 * level)))
        if lvl <= 0:
            continue
        d = bayer(rg, min(16, lvl), i)
        hot = PALC['y'] if fall > 0.62 else (PALC['Y'] if fall > 0.3 else PALC['z'])
        tint(cv, d, hot, 0.55 + 0.45 * level, skip_black=False)


def glow_halo(cv, sg, level, reach=13):
    """Free-air bloom for the ADDITIVE overlay: unlike sigil_bloom, which only
    relights cloth that is already there, this paints light onto empty pixels."""
    if level <= 0.02:
        return
    R = 3 + int(round(level * reach))
    # ring 1 is left clear for the emblem's dark contour, same as sigil_bloom
    prev = grow(sg, 1)
    for i in range(2, R + 2):
        rg = sub(grow(sg, i), prev)
        prev = grow(sg, i)
        fall = max(0.0, 1.0 - (i - 1) / float(R))
        lvl = int(round(16 * fall * fall * (0.30 + 0.70 * level)))
        if lvl <= 0:
            continue
        # the halo stays orange right up against the mark: filling the ring's
        # negative space with cream would eat the shape at the exact moment it
        # is supposed to be the hero
        col = (PALC['X'] if fall > 0.62 else
               PALC['y'] if fall > 0.34 else PALC['Y'])
        d = bayer(rg, min(16, lvl), i)
        for y in range(H):
            for x in range(W):
                if d[y][x] and cv.px[y][x] is None:
                    cv.px[y][x] = col


ROPE_SET = set(hexc(c) for c in RAMPS['rope'])


def wrap_bands(cv, mask, a, b, bands=(0.50, 0.74), knuckles=True):
    """Bind a hand wrap so it stops reading as a pale bread roll.

    A flat cream capsule has no information in it; two darker bands across the
    forearm, a shaded underside and a few knuckle highlights give it direction
    and tell you it is cloth wound round a fist.  Only rope-ramp pixels are
    touched, so this is safe to run over a finished canvas."""
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1.0
    band_c, crease_c, knuck_c = PALC['j'], PALC['l'], PALC['g']
    cols = {}
    for y in range(H):
        for x in range(W):
            if not mask[y][x] or cv.px[y][x] not in ROPE_SET:
                continue
            t = ((x + 0.5 - ax) * dx + (y + 0.5 - ay) * dy) / L2
            for bt in bands:
                if abs(t - bt) < 0.055:
                    cv.px[y][x] = band_c
            cols.setdefault(x, []).append((y, t))
    # shaded underside: the lowest cloth pixel in each column
    for x, ys in cols.items():
        ys.sort()
        y = ys[-1][0]
        if cv.px[y][x] in ROPE_SET or cv.px[y][x] == band_c:
            cv.px[y][x] = crease_c
    if not knuckles:
        return
    # knuckle nubs on the far end of the fist
    far = [(x, y) for y in range(H) for x in range(W)
           if mask[y][x] and cv.px[y][x] in ROPE_SET
           and ((x + 0.5 - ax) * dx + (y + 0.5 - ay) * dy) / L2 > 0.94]
    far.sort(key=lambda p: p[1])
    for i, (x, y) in enumerate(far[:9]):
        if i % 3 == 0:
            cv.px[y][x] = knuck_c


def wrap_bands_both(cv, mask, a, b, **kw):
    """same, for a mask that already carries both arms"""
    left = [[mask[y][x] and x < 48 for x in range(W)] for y in range(H)]
    right = [[mask[y][x] and x >= 48 for x in range(W)] for y in range(H)]
    wrap_bands(cv, left, a, b, **kw)
    wrap_bands(cv, right, (95.0 - a[0], a[1]), (95.0 - b[0], b[1]), **kw)


def rim_light(cv, body, level, seed_mask=None, reach=30.0):
    """warm bounce on the silhouette edge nearest the mark - sells the fact
    that the glow is a real light source sitting on his back."""
    if level <= 0.05:
        return
    cx, cy = MARK_C
    edge = sub(body, erode(body, 1))
    inner = sub(erode(body, 1), erode(body, 2))
    for m, amt in ((edge, 1.0), (inner, 0.45)):
        for y in range(H):
            for x in range(W):
                if not m[y][x] or cv.px[y][x] is None or cv.px[y][x] == BLACK:
                    continue
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                f = max(0.0, 1.0 - d / reach)
                a = f * amt * level
                if a < 0.12:
                    continue
                hot = PALC['x'] if a > 0.62 else (PALC['X'] if a > 0.34 else PALC['y'])
                cv.px[y][x] = mixc(cv.px[y][x], hot, min(0.85, a))


def ground_glow(cv, level, cx=47.5, row=94, span=30.0):
    """the floor catching the flare, kept inside the frame."""
    if level <= 0.25:
        return
    t = (level - 0.25) / 0.75
    for dy in range(0, 5):
        y = row - dy
        if y < 0 or y >= H:
            continue
        wdt = span * t * (1.0 - dy * 0.17)
        for x in range(W):
            if cv.px[y][x] is not None:
                continue
            d = abs(x + 0.5 - cx)
            if d > wdt:
                continue
            f = 1.0 - d / max(1e-6, wdt)
            lvl = int(round(16 * f * t * (1.0 - dy * 0.22)))
            if lvl <= 0:
                continue
            if bayer(_ONE, lvl, dy)[y][x]:
                cv.px[y][x] = PALC['Y'] if f > 0.55 else PALC['z']


_ONE = [[True] * W for _ in range(H)]


# ---------------------------------------------------------------- aura

# ---------------------------------------------------------------- entrance aura
# The shipped sheet's wisps are a vertical crown, which at 3x reads as horns or
# a jester's hat.  The entrance uses its own set instead: fewer, longer, curling
# strands that sweep OUTWARD along the body rather than spiking up off the
# skull, and the wedge straight above his head is deliberately left empty so the
# bald silhouette stays clean.  Each entry is (spine, base width, tip width).

# Each strand is a ROOT, an outward angle, a length, a curl and a base width.
# Generating the spine from a curl rather than listing straight control points
# is the whole difference between flame and a sunburst: laid out as straight
# rays at even angles this read as a cartoon sun. The angles are deliberately
# uneven and the lengths deliberately mismatched for the same reason.
ENTR_SEEDS = [
    # x, y, angle(deg, outward), length, curl, base width
    # The two upper strands lean hard OUTWARD rather than up. At a steeper
    # angle their mirrored pair stood over the skull like a set of horns, which
    # is the exact read this aura was rebuilt to get rid of. Two of them per
    # side, well apart, keeps the dome clear and stops either one looking like
    # a single spike.
    (39.0, 20.0, -150.0, 28.0, -0.45, 6.4),  # out past the temple, bowing away
    (28.0, 32.0, -128.0, 24.0, -0.38, 5.6),  # steeper, but further out again
    (32.5, 38.0, -164.0, 24.0, 0.44, 6.0),   # out past the jaw
    (22.5, 47.0,  171.0, 35.0, 0.60, 8.4),   # shoulder: the heaviest root
    (19.5, 62.0,  158.0, 25.0, -0.52, 6.8),  # arm
    (27.5, 77.0,  151.0, 22.0, 0.46, 5.6),   # hip
    (30.5, 90.0,  174.0, 15.0, -0.36, 4.4),  # ankle, low and lazy
]


def entr_specs(k, scale=1.0, reach=1.0, lean=0.0, curl=1.0):
    """Mirrored entrance aura for flicker step k.  Strands leave the body as
    fat wedges and bend away along an S, so they read as heat coming off him."""
    out = []
    for side in (0, 1):
        for i, (rx, ry, ang, ln, cu, w0) in enumerate(ENTR_SEEDS):
            a = math.radians(ang)
            ca, sa = math.cos(a), math.sin(a)
            px, py = -sa, ca          # perpendicular to the strand
            L = ln * reach
            ph = k * math.pi / 2 + i * 1.27 + side * 0.9
            cur = cu * curl * (1.0 + 0.16 * math.sin(ph))
            pts = []
            for f in (0.0, 0.33, 0.68, 1.0):
                along = L * f
                # one full bend and back: a peak near two thirds gives an S
                off = cur * L * math.sin(f * math.pi * 1.12)
                flick = math.sin(ph + f * 2.1) * 2.6 * f
                nx = rx + ca * along + px * (off + flick)
                ny = ry + sa * along + py * (off + flick) - 1.8 * f * f
                nx += lean * f * f
                pts.append((95.0 - nx, ny) if side else (nx, ny))
            out.append((pts, w0 * scale, 1.0))
    return out


def entr_sparks(k):
    pts = []
    for i, (bx, by) in enumerate(((14.0, 10.0), (8.0, 34.0), (3.0, 56.0),
                                  (11.0, 74.0), (26.0, 2.0))):
        ph = k * 0.8 + i * 1.6
        x = bx + math.sin(ph) * 2.5
        y = by + math.cos(ph * 0.7) * 3.0
        for xx in (x, 95.0 - x):
            if 1.0 < xx < W - 1 and 1.0 < y < H - 1:
                pts.append((xx + 0.5, y + 0.5))
    return pts


def dist_index(body, maxr):
    """ring index out from the body: 0 inside, 1..maxr walking outward."""
    idx = [[maxr + 1] * W for _ in range(H)]
    prev = body
    for i in range(1, maxr + 1):
        g = grow(body, i)
        for y in range(H):
            for x in range(W):
                if g[y][x] and not prev[y][x] and idx[y][x] > i:
                    idx[y][x] = i
        prev = g
    for y in range(H):
        for x in range(W):
            if body[y][x]:
                idx[y][x] = 0
    return idx


def block_dither(mask, level, block=2, seed=0):
    """Chunky dissolve. A 4x4 Bayer pattern at 3x game scale reads as TV
    static; quantising to 2x2 blocks with hash thresholds reads as particles."""
    m = empty()
    for y in range(H):
        for x in range(W):
            if not mask[y][x]:
                continue
            if _hash(x // block, y // block, seed) * 16.0 < level:
                m[y][x] = True
    return m


def soften(cv, body, near=9, far=40, block=2, seed=3):
    """Break the wisp ends up so the aura dissolves into heat instead of
    ending in hard spikes: solid at the roots, particles at the tips."""
    idx = dist_index(body, far)
    for y in range(H):
        for x in range(W):
            if cv.px[y][x] is None or body[y][x]:
                continue
            d = idx[y][x]
            if d <= near:
                continue
            t = min(1.0, (d - near) / float(max(1, far - near)))
            keep = 16.0 * (1.0 - t) ** 1.35
            if _hash(x // block, y // block, seed) * 16.0 >= keep:
                cv.px[y][x] = None


def jitter(specs, k, amp=1.3, grow_w=0.0):
    """the flicker used by the approved preview, with an optional width push."""
    out = []
    for i, (ctrl, w0, w1) in enumerate(specs):
        nc = []
        for j, (x, y) in enumerate(ctrl):
            t = j / max(1, len(ctrl) - 1)
            ph = k * math.pi / 2 + i * 1.1 + j * 0.7
            nc.append((x + math.sin(ph) * amp * t,
                       y - abs(math.cos(ph)) * amp * 0.9 * t))
        out.append((nc, w0 * (1.0 + 0.06 * math.sin(k * 1.6 + i) + grow_w), w1))
    return out


def sweep(specs, lean, droop=0.0):
    """drag the wisps sideways so the aura trails the turn."""
    out = []
    for ctrl, w0, w1 in specs:
        nc = []
        for j, (x, y) in enumerate(ctrl):
            t = j / max(1, len(ctrl) - 1)
            nc.append((x + lean * t * t, y + droop * t * t))
        out.append((nc, w0, w1))
    return out


def squeeze_specs(specs, s, cx=AXC):
    """narrow the aura with the body when he turns edge-on."""
    return [([(cx + (x - cx) * s, y) for x, y in ctrl], w0 * (0.55 + 0.45 * s), w1)
            for ctrl, w0, w1 in specs]


def scale_w(specs, f, reach=1.0, cx=AXC, cy=52.0):
    """shrink the wisps toward their roots - lets one spec set cover a whole
    pulse without the tendril count popping between frames."""
    out = []
    for ctrl, w0, w1 in specs:
        bx, by = ctrl[0]
        nc = [(bx + (x - bx) * reach, by + (y - by) * reach) for x, y in ctrl]
        out.append((nc, max(1.6, w0 * f), w1))
    return out


def blend_specs(a, b, t):
    """cross-fade two spec lists by pulling the shorter set's extras in."""
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b
    out = []
    for i, (ctrl, w0, w1) in enumerate(b):
        if i < len(a):
            ca, wa, _ = a[i]
            n = min(len(ca), len(ctrl))
            nc = [(ca[j][0] + (ctrl[j][0] - ca[j][0]) * t,
                   ca[j][1] + (ctrl[j][1] - ca[j][1]) * t) for j in range(n)]
            out.append((nc, wa + (w0 - wa) * t, w1))
        else:
            out.append((ctrl, max(1.5, w0 * t), w1))
    return out


def compose(body_cv, specs, sparks, haze_in=5, haze_out=0, off=0, hot=True):
    """aura behind, body in front - the order build.py uses."""
    cv = Canvas()
    bm = body_cv.mask_of()
    if specs:
        AU.paint(cv, specs, sparks, bm, hot=hot)
    AU.haze(cv, bm, haze_in, haze_out, off)
    for y in range(H):
        row = body_cv.px[y]
        for x in range(W):
            if row[x] is not None:
                cv.px[y][x] = row[x]
    return cv


def aura_heat(cv, body, level):
    """push the wisps up the ember ramp as the mark flares."""
    if level <= 0.05:
        return
    near = grow(body, 12)
    step1 = {PALC['T']: PALC['Z'], PALC['U']: PALC['Z'], PALC['S']: PALC['z'],
             PALC['R']: PALC['Y'], PALC['Y']: PALC['y'], PALC['y']: PALC['X'],
             PALC['X']: PALC['x']}
    lvl = int(round(16 * min(1.0, level)))
    d = bayer(near, lvl, 1)
    for y in range(H):
        for x in range(W):
            if not d[y][x] or not near[y][x]:
                continue
            c = cv.px[y][x]
            if c in step1 and not body[y][x]:
                cv.px[y][x] = step1[c]
    if level > 0.7:
        d2 = bayer(grow(body, 7), int(round(16 * (level - 0.7) / 0.3)), 2)
        for y in range(H):
            for x in range(W):
                if d2[y][x] and not body[y][x]:
                    c = cv.px[y][x]
                    if c in step1:
                        cv.px[y][x] = step1[c]


# ---------------------------------------------------------------- transforms

HEAD_LO, HEAD_HI = 40, 50        # rows the skull hands over to the shoulders


def turn_scale(s, keep_head=True):
    """Per-row squeeze for a body turning away from the camera.

    A skull is about as deep as it is wide, so it barely narrows as it turns -
    squeezing it by the same factor as the ribcage crushes the face and the
    character stops looking like himself.  The shoulders, chest and arms are
    what actually foreshorten."""
    if not keep_head:
        return lambda y: s
    sh = min(1.0, 0.92 + 0.08 * s)

    def f(y):
        if y <= HEAD_LO:
            return sh
        if y >= HEAD_HI:
            return s
        t = (y - HEAD_LO) / float(HEAD_HI - HEAD_LO)
        return sh * (1.0 - t) + s * t
    return f


def hsq_mask(mask, s, cx=AXC, keep_head=False):
    """forward-scatter horizontal squeeze: never leaves holes."""
    sfun = s if callable(s) else turn_scale(s, keep_head)
    out = empty()
    for y in range(H):
        sy = sfun(y)
        for x in range(W):
            if mask[y][x]:
                xo = int(round(cx + (x + 0.5 - cx) * sy - 0.5))
                if 0 <= xo < W:
                    out[y][xo] = True
    return out


def hsq_canvas(cv, s, cx=AXC, reoutline=True, keep_head=True):
    """Foreshorten a finished body canvas. The alpha is scattered forward so
    the silhouette keeps its full extent, then each surviving pixel samples the
    nearest source pixel on its row, and the outline is redrawn 1px clean."""
    sfun = s if callable(s) else turn_scale(s, keep_head)
    src = cv.px
    out = Canvas()
    tgt = hsq_mask(cv.mask_of(), sfun, cx)
    for y in range(H):
        xs = [x for x in range(W) if src[y][x] is not None]
        if not xs:
            continue
        sy = sfun(y)
        for x in range(W):
            if not tgt[y][x]:
                continue
            u = cx + (x + 0.5 - cx) / sy - 0.5
            best, bd = None, 1e9
            for sx in xs:
                d = abs(sx - u)
                if d < bd:
                    bd, best = d, sx
            out.px[y][x] = src[y][best]
    if reoutline:
        out.outline(out.mask_of())
    return out


def shift_canvas(cv, dx, dy=0):
    out = Canvas()
    for y in range(H):
        for x in range(W):
            if cv.px[y][x] is None:
                continue
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H:
                out.px[yy][xx] = cv.px[y][x]
    return out


def edge_shade(cv, side, amt=0.55, col=None, rows=(10, 96)):
    """darken the trailing edge of a turning body so the far side reads as
    curving away.  side = -1 shades the left edge, +1 the right."""
    m = cv.mask_of()
    edge = sub(m, erode(m, 1))
    inner = sub(erode(m, 1), erode(m, 2))
    col = col or PALC['T']
    for y in range(rows[0], min(rows[1], H)):
        xs = [x for x in range(W) if m[y][x]]
        if not xs:
            continue
        lim = max(xs) if side > 0 else min(xs)
        for x in range(W):
            if cv.px[y][x] is None or cv.px[y][x] == BLACK:
                continue
            d = abs(x - lim)
            if d > 2:
                continue
            if not (edge[y][x] or inner[y][x]):
                continue
            a = amt * (1.0 - d / 3.0)
            cv.px[y][x] = mixc(cv.px[y][x], col, a)


def rim_edge(cv, side, col='X', amt=0.6, rows=(10, 96)):
    """a 1px lit rim on the leading edge."""
    m = cv.mask_of()
    c = PALC[col]
    for y in range(rows[0], min(rows[1], H)):
        xs = [x for x in range(W) if m[y][x]]
        if not xs:
            continue
        lim = max(xs) if side > 0 else min(xs)
        x = lim - side  # one step inside the black outline
        if 0 <= x < W and cv.px[y][x] is not None and cv.px[y][x] != BLACK:
            cv.px[y][x] = mixc(cv.px[y][x], c, amt)
