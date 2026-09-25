"""matt_mystic_bolt.png: Matt's Mystic Shot bolt. 12 frames of 40x40, one strip:
  frames 0-3    heading 22.5 degrees
  frames 4-7    heading 45 degrees
  frames 8-11   heading 67.5 degrees
4 flicker frames per heading at 0.05 s, looping.

Headings are Godot angles (y down): 0 is right, 90 is down, so all three fly right-and-down. The code
covers the other nine lattice headings with flips only: flip_h for a leftward heading (180 - t), flip_v
for an upward one (-t), both for (180 + t).

The pivot is the core: the design's origin, placed on a texel centre. PIVOTS below gives it per heading as
the texel whose centre it is. The 67.5 degree frames are the exact transpose of the 22.5 degree ones, so
their pivot is the transposed texel.

The design, in the bolt's own axes (u forward along the heading, v across it, in texels, origin at the core):
  head    a lancet spearhead 10.5 texels from the tip (u +4.5) back to u -6, 6 wide at its widest. A 3x2
          white-hot core just behind the tip; bands cool from the core out; the rim is the dark cyan
          (#0E7FB0) along the sides and back and lightens to a bright point at the front, so the leading
          point reads as the hottest part.
  trail   two strands spiralling round the axis from u -5 back to u -26: 4 texels wide where they leave
          the head, 1 at the end. Where a strand passes in front it is bright, behind it is dark, so the
          pair reads as curling and the wake cools from light to dark down its length. The last texels are
          the far-wisp blue (#0A4E78). The spiral turns a quarter per frame, so it streams backward.
  motes   two bright specks shed off the trail, drifting back.
Nothing in the head moves between frames except the flame licks at its back corners, so the core the hit
circle sits on never jumps.
"""
import math

import mfx_pal as pal

W = H = 40
HEADINGS = (22.5, 45.0, 67.5)
FRAMES = 4

# The core texel per drawn heading (its centre is the pivot). 67.5 is the transpose of 22.5.
CORE = {22.5: (29, 23), 45.0: (27, 27)}

# Head half-width along u (tip first), linearly interpolated.
HEAD_HW = [(4.6, 0.0), (4.0, 0.45), (3.0, 1.1), (2.0, 1.7), (1.0, 2.25), (0.0, 2.7), (-1.0, 2.95),
           (-2.0, 2.95), (-3.0, 2.75), (-4.0, 2.45), (-5.0, 2.15), (-6.2, 1.9)]
U_TIP, U_HEAD_END = 4.6, -6.2
U_TAIL = -26.0


def interp(table, u):
    if u >= table[0][0]:
        return table[0][1]
    for (u0, h0), (u1, h1) in zip(table, table[1:]):
        if u1 <= u <= u0:
            t = (u0 - u) / (u0 - u1)
            return h0 + (h1 - h0) * t
    return table[-1][1]


def axes(theta_deg):
    t = math.radians(theta_deg)
    d = (math.cos(t), math.sin(t))
    n = (-math.sin(t), math.cos(t))       # right of travel on screen (y down)
    return d, n


def uv(x, y, core, theta_deg):
    d, n = axes(theta_deg)
    px, py = x + 0.5 - (core[0] + 0.5), y + 0.5 - (core[1] + 0.5)
    return px * d[0] + py * d[1], px * n[0] + py * n[1]


def to_xy(u, v, core, theta_deg):
    d, n = axes(theta_deg)
    return core[0] + 0.5 + u * d[0] + v * n[0], core[1] + 0.5 + u * d[1] + v * n[1]


def head_mask(core, theta, f):
    """Texels inside the spearhead, plus this frame's flame licks at its back corners."""
    m = set()
    for y in range(H):
        for x in range(W):
            u, v = uv(x, y, core, theta)
            if U_HEAD_END <= u <= U_TIP and abs(v) <= interp(HEAD_HW, u):
                m.add((x, y))
    # Flame licks: one texel off each back corner, alternating sides and reach per frame.
    for side, uu, on in ((1, -3.6, f in (0, 1)), (-1, -4.4, f in (2, 3)), (1, -5.6, f in (1, 2)),
                         (-1, -5.2, f in (0, 3))):
        if on:
            hw = interp(HEAD_HW, uu) + 0.9
            xf, yf = to_xy(uu, side * hw, core, theta)
            m.add((int(math.floor(xf)), int(math.floor(yf))))
    return m


def rings(mask):
    """Erosion depth of every texel in a mask: 0 on the 4-connected edge, 1 inside that, and so on."""
    depth = {}
    cur = set(mask)
    r = 0
    while cur:
        edge = {(x, y) for (x, y) in cur
                if any((x + dx, y + dy) not in cur for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        for p in edge:
            depth[p] = r
        cur -= edge
        r += 1
    return depth


def paint_head(g, core, theta, f):
    m = head_mask(core, theta, f)
    dep = rings(m)
    for (x, y), r in dep.items():
        u, v = uv(x, y, core, theta)
        if r == 0:
            k = 'C' if u > 3.0 else ('B' if u > 1.6 else 'R')
        elif r == 1:
            k = 'D' if u > 2.2 else ('C' if u > -2.5 else 'B')
        else:
            k = 'D' if u > -3.2 else 'C'
        g[y][x] = k
    # The 3x2 white-hot core just behind the tip.
    for (x, y) in m:
        u, v = uv(x, y, core, theta)
        if -1.6 <= u <= 1.6 and abs(v) <= 0.85:
            g[y][x] = 'W'
    return m


def tail_s(u):
    return min(1.0, max(0.0, (-4.8 - u) / (-4.8 - U_TAIL)))


def tail_edges(u, f):
    """(upper, lower) edge of the wake at u, in v. The wake narrows from 4 texels at the head to 1 at the
    tail; each edge is one of the two strands and curls on its own wavelength, travelling back a quarter
    wave per frame, so the pair reads as twisting wisps."""
    s = tail_s(u)
    c = 0.4 * math.sin(math.pi * s) * math.sin(2 * math.pi * u / 12.0 + f * math.pi / 2)
    hw = 0.5 + 1.52 * (1.0 - s) ** 1.45
    curl = 0.15 + 0.62 * math.sin(math.pi * min(1.0, s * 1.1))      # peaks mid-tail, calm at the end
    up = c - hw - curl * math.sin(2 * math.pi * u / 7.0 + f * math.pi / 2)
    lo = c + hw + curl * math.sin(2 * math.pi * u / 5.5 + 2.2 + f * math.pi / 2)
    if lo - up < 0.9:                         # never pinch to nothing: keep a 1-texel wisp
        m = (up + lo) / 2
        up, lo = m - 0.45, m + 0.45
    return up, lo, c


def dash_gap(u, f):
    """Toward the tail the wake breaks into dashes that stream back each frame."""
    s = tail_s(u)
    if s < 0.66:
        return False
    return ((-u + 2.0 * f) % 5.0) < (1.0 if s < 0.84 else 2.0)


def paint_trail(g, head, core, theta, f):
    body = set()
    for y in range(H):
        for x in range(W):
            if (x, y) in head:
                continue
            u, v = uv(x, y, core, theta)
            if tail_s(u) <= FAR and U_TAIL - 0.5 <= u <= -4.3:
                up, lo, c = tail_edges(u, f)
                if up <= v <= lo:
                    body.add((x, y))
    dep = rings(body | head)
    for (x, y) in body:
        u, v = uv(x, y, core, theta)
        s = tail_s(u)
        up, lo, c = tail_edges(u, f)
        upper = v < c
        if s > 0.82:
            k = 'F'
        elif dep[(x, y)] == 0:
            if upper:
                k = 'C' if s < 0.4 else ('B' if s < 0.62 else 'R')
            else:
                k = 'R' if s < 0.7 else 'F'
        else:
            k = 'B' if s < 0.55 else 'R'
        g[y][x] = k
    # The far wisp: a single stepped line along the wake's path, broken into dashes that stream back,
    # with its L-corners removed so every step is a clean diagonal (the pixel-perfect rule).
    runs, cur = [], []
    u = U_TAIL
    while u <= -4.3:
        s = tail_s(u)
        if s > FAR and not dash_gap(u, f):
            up, lo, c = tail_edges(u, f)
            xf, yf = to_xy(u, (up + lo) / 2, core, theta)
            p = (int(math.floor(xf)), int(math.floor(yf)))
            if not cur or cur[-1][0] != p:
                cur.append((p, 'R' if s < 0.82 else 'F'))
        elif cur:
            runs.append(cur)
            cur = []
        u += 0.1
    if cur:
        runs.append(cur)
    for run in runs:
        for (x, y), k in pixel_perfect(run):
            if (x, y) not in body and (x, y) not in head:
                pal.put(g, x, y, k)


def pixel_perfect(run):
    """Drop the middle texel of every L-corner in a stepped line: A-B-C where A and C touch diagonally."""
    out = list(run)
    i = 1
    while i < len(out) - 1:
        (ax, ay), (bx, by), (cx, cy) = out[i - 1][0], out[i][0], out[i + 1][0]
        if abs(ax - cx) == 1 and abs(ay - cy) == 1 and (ax == bx or ay == by):
            del out[i]
        else:
            i += 1
    return out


FAR = 0.62


def paint_motes(g, core, theta, f):
    for u0, v0, col in ((-10.0, 3.6, 'D'), (-17.0, -3.4, 'C'), (-24.0, 2.6, 'R')):
        u = u0 - 2.5 * f
        if u < U_TAIL - 2:
            u += 12
        xf, yf = to_xy(u, v0, core, theta)
        x, y = int(math.floor(xf)), int(math.floor(yf))
        if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
            g[y][x] = col


def frame(theta, f):
    core = CORE[theta]
    g = pal.blank(W, H)
    head = paint_head(g, core, theta, f)
    paint_trail(g, head, core, theta, f)
    paint_motes(g, core, theta, f)
    return pal.rows(g)


def frames():
    """All 12 frames in sheet order."""
    out = []
    by = {}
    for theta in (22.5, 45.0):
        by[theta] = [frame(theta, f) for f in range(FRAMES)]
    by[67.5] = [pal.transpose(fr) for fr in by[22.5]]
    for theta in HEADINGS:
        out.extend(by[theta])
    return out


def pivots():
    """Heading -> the core texel (x, y); its centre (x + 0.5, y + 0.5) is the pivot."""
    c = dict(CORE)
    c[67.5] = (CORE[22.5][1], CORE[22.5][0])
    return c


if __name__ == '__main__':
    for fr in frames()[0:1] + frames()[4:5]:
        print('\n'.join(fr))
        print()
