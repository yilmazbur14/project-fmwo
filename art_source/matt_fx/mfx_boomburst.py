"""matt_boom_burst.png: a sonic boom breaking on the player. 8 frames of 64x64 at 0.05 s, one strip:
  frames 0-3   BLOCKED: an answered boom breaks on the braced player: the front flattens into a bright bow
               on them and splits, the two halves peeling up and away round them, breaking into dashes
  frames 4-7   SLAM: a missed boom hits: a white-hot core bursts, then a ring squashed toward the knock
               (down) spreads in the approved roar-ring style, speed lines driving down under it
THE PIVOT IS THE FRAME CENTRE (32, 32): put it on the player's hurtbox centre at impact (the boom's apex).
Never flipped. The approved ring style (#F2F3FF core, #C4C9FA flanks, #4F4D96 edge), no keyline, opaque.
"""
import math

import mfx_pal as pal

W = H = 64
CX = CY = 32.0
FRAME_SIZE = (64, 64)
NOTE = '8 frames at 0.05 s: f0-3 blocked, f4-7 slam; pivot = frame centre (32,32)'


def band(dd, core, flank, edge, ck='s'):
    a = abs(dd)
    if a <= core:
        return ck
    if a <= flank:
        return 'r'
    if a <= edge:
        return 'm'
    return None


def put(g, x, y, k):
    if 0 <= x < W and 0 <= y < H:
        cur = g[y][x]
        rank = {'.': 0, 'm': 1, 'r': 2, 's': 3}
        if rank[k] >= rank[cur]:
            g[y][x] = k


def ellipse_ring(g, rx, ry, oy, core, flank, edge, ck='s', dash=None, arc=None):
    """A ring round (CX, CY + oy) of radii rx, ry; arc=(a0, a1) degrees keeps only that part (0 = right,
    90 = down); dash=(count, on) breaks it."""
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY - oy
            ang = math.degrees(math.atan2(dy, dx)) % 360
            if arc and not (arc[0] <= ang <= arc[1] or arc[0] <= ang + 360 <= arc[1]):
                continue
            if dash and ((ang / 360.0 * dash[0]) % 1.0) > dash[1]:
                continue
            # distance to the ellipse, in texels, approximated by scaling to a circle of radius rx
            d = math.hypot(dx, dy * rx / ry)
            k = band((d - rx) * min(1.0, ry / rx * 1.6), core, flank, edge, ck)
            if k:
                put(g, x, y, k)


def bow(g, half_w, y0, lift, thick, ck, edge_k='m'):
    """A thick bow over the braced player's head, convex up, its ends dipping `lift` texels."""
    for x in range(W):
        dx = x + 0.5 - CX
        if abs(dx) > half_w:
            continue
        t = abs(dx) / half_w
        yc = y0 + lift * t * t                                   # the ends dip: a shield dome
        th = thick * (1.0 - 0.45 * t * t)
        for y in range(H):
            dd = abs(y + 0.5 - yc)
            if dd <= th * 0.5:
                put(g, x, y, ck if t < 0.85 else 'r')
            elif dd <= th * 0.5 + 1.0:
                put(g, x, y, 'r' if dd <= th * 0.5 + 0.5 else edge_k)


SPARKS = {
    0: [(-9, -6, 's'), (-3, -8, 's'), (4, -7, 's'), (10, -5, 's'), (-14, -3, 'r'), (15, -2, 'r')],
    1: [(-15, -10, 'r'), (-6, -12, 's'), (7, -11, 's'), (16, -9, 'r'), (-21, -5, 'r'), (22, -4, 'r')],
    2: [(-20, -13, 'm'), (-8, -15, 'r'), (9, -14, 'r'), (21, -12, 'm'), (-26, -7, 'm'), (27, -6, 'm')],
}


def sparks(g, f, y0):
    for dx, dy, k in SPARKS.get(f, []):
        x, y = int(CX + dx), int(y0 + dy)
        put(g, x, y, k)
        if k == 's':
            put(g, x, y + 1, 'r')


def blocked(f):
    """The boom breaks on the braced player: over their head (the pivot is their centre, their head about
    9 texels above it) it flattens into a bright shield bow throwing sparks up, then splits, the two
    halves peeling up and away, thinning into dashes."""
    g = pal.blank(W, H)
    y0 = CY - 10
    if f == 0:
        bow(g, 17, y0, 4.0, 3.2, 's')
        sparks(g, 0, y0)
    elif f == 1:
        ellipse_ring(g, 22, 12, -6, 0.9, 1.25, 2.1, arc=(196, 252))
        ellipse_ring(g, 22, 12, -6, 0.9, 1.25, 2.1, arc=(288, 344))
        for dx in (-1, 0):
            put(g, int(CX + dx), int(y0), 's')
            put(g, int(CX + dx), int(y0) + 1, 'r')
        sparks(g, 1, y0)
    elif f == 2:
        ellipse_ring(g, 27, 16, -8, 0.55, 0.8, 1.6, ck='r', arc=(192, 240), dash=(30, 0.7))
        ellipse_ring(g, 27, 16, -8, 0.55, 0.8, 1.6, ck='r', arc=(300, 348), dash=(30, 0.7))
        sparks(g, 2, y0)
    elif f == 3:
        ellipse_ring(g, 31, 19, -9, 0.0, 0.0, 0.95, ck='m', arc=(192, 228), dash=(24, 0.45))
        ellipse_ring(g, 31, 19, -9, 0.0, 0.0, 0.95, ck='m', arc=(312, 348), dash=(24, 0.45))
    return pal.rows(g)


def core_burst(g, r_in, r_out, spikes, spike_len, rot):
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - CX, (y + 0.5 - CY) * 1.15)
            if d <= r_in:
                put(g, x, y, 's')
            elif d <= r_out:
                put(g, x, y, 'r' if d <= r_out - 1.0 else 'm')
    for i in range(spikes):
        a = math.radians(rot + 360.0 * i / spikes)
        # longer spikes below: the knock is down
        length = spike_len * (1.35 if math.sin(a) > 0.3 else 0.8)
        s = r_out - 0.5
        while s <= length:
            x = int(math.floor(CX + math.cos(a) * s))
            y = int(math.floor(CY + math.sin(a) * s))
            put(g, x, y, 's' if s < r_out + 2.5 else ('r' if s < length - 1.5 else 'm'))
            s += 0.3


def speed_lines(g, n, top, length, spread, keys):
    for i in range(n):
        x = int(CX - spread + 2 * spread * (i + 0.5) / n)
        for j in range(length):
            y = top + j + (i % 2) * 2
            put(g, x, y, keys[min(len(keys) - 1, j * len(keys) // max(1, length))])


def slam(f):
    g = pal.blank(W, H)
    if f == 4:
        core_burst(g, 4.5, 7.0, 8, 13.0, 22.5)
    elif f == 5:
        ellipse_ring(g, 15, 11, 3, 1.2, 1.6, 2.6)
        core_burst(g, 2.0, 3.5, 0, 0, 0)
        speed_lines(g, 5, 44, 7, 12, 'srm')
    elif f == 6:
        ellipse_ring(g, 22, 15, 5, 0.75, 1.05, 1.85)
        ellipse_ring(g, 12, 8, 3, 0.55, 0.55, 1.45, ck='r')
        speed_lines(g, 6, 50, 9, 16, 'rrm')
    elif f == 7:
        ellipse_ring(g, 28, 19, 6, 0.55, 0.55, 1.45, ck='r', dash=(26, 0.55))
        ellipse_ring(g, 19, 12, 5, 0.0, 0.0, 0.95, ck='m', dash=(20, 0.45))
        speed_lines(g, 4, 56, 6, 14, 'mm')
    return pal.rows(g)


def frames():
    return [blocked(f) for f in range(4)] + [slam(f) for f in range(4, 8)]
