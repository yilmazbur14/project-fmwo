"""Shared drawing for Danny's worms and their slime: a worm is a thick wriggling tube lit from the top left
(pink ramp 1-5) with an earthworm's saddle band; a slime stain is a dark glossy blob on the floor with a
thin wet rim lit on its upper left (x 6 D, gloss 1 e). No keyline: the darkest tone of each does the edge.
"""
import math
import random


def wiggle(x0, y0, x1, y1, amp, waves, phase, n=48):
    """Points along the segment (x0,y0)->(x1,y1), bent by a sine of amp texels across it."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    out = []
    for i in range(n + 1):
        t = i / n
        s = amp * math.sin(2 * math.pi * waves * t + phase) * math.sin(math.pi * t) ** 0.4
        out.append((x0 + dx * t + nx * s, y0 + dy * t + ny * s))
    return out


def _seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy or 1e-9
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    qx, qy = ax + vx * t, ay + vy * t
    return math.hypot(px - qx, py - qy), t, qx, qy


def worm(g, pts, width=2.6, taper=True, clip=None, saddle=0.3, glint_every=9):
    """A worm along pts: a tube `width` texels thick; its lit side (toward the top left) 2, body 3, shadow
    side 4, tapered tips 4; a darker saddle band (the clitellum) at `saddle` along it; a 1 glint on the lit
    side every `glint_every` points. `clip`, if given, is a set of (x, y) it may draw on."""
    H, W = len(g), len(g[0])
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = int(min(xs) - width) - 1, int(max(xs) + width) + 2
    y0, y1 = int(min(ys) - width) - 1, int(max(ys) + width) + 2
    seglen = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seglen) or 1.0
    cum = [0.0]
    for s in seglen:
        cum.append(cum[-1] + s)
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            if clip is not None and (x, y) not in clip:
                continue
            px, py = x + 0.5, y + 0.5
            best = None
            for i in range(len(pts) - 1):
                d, t, qx, qy = _seg_dist(px, py, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
                if best is None or d < best[0]:
                    best = (d, i, t, qx, qy)
            d, i, t, qx, qy = best
            u = (cum[i] + seglen[i] * t) / total
            half = width / 2.0
            if taper:
                half *= min(1.0, 0.5 + 2.4 * min(u, 1.0 - u))
            if d > half:
                continue
            sx, sy = px - qx, py - qy
            side = (-sx - sy) / (d + 1e-6)
            if min(u, 1.0 - u) * total < 1.2:
                k = '4'
            elif d > half * 0.4 and side > 0.3:
                k = '2'
            elif d > half * 0.4 and side < -0.3:
                k = '4'
            else:
                k = '3'
            if abs(u - saddle) * total < 1.3 and k in '23':
                k = '4' if k == '3' else '3'
            g[y][x] = k
    if glint_every:
        for j in range(3, len(pts) - 3, glint_every):
            ax, ay = pts[j]
            bx, by = pts[j + 1]
            L = math.hypot(bx - ax, by - ay) or 1.0
            nx, ny = -(by - ay) / L, (bx - ax) / L
            if nx + ny > 0:
                nx, ny = -nx, -ny
            x, y = int(ax + nx * width * 0.3), int(ay + ny * width * 0.3)
            if 0 <= x < W and 0 <= y < H and g[y][x] == '2':
                g[y][x] = '1'


def blob_mask(W, H, cx, cy, rx, ry, seed, wob=0.07, drops=(), ks=(4, 5, 7)):
    """The texels of a slime stain: a lobed ellipse round (cx, cy) (low lobe counts make lemons and hulls,
    so its bumps are 4-7 to a turn), plus splatter drops (x, y, r, ry) round it. Returns (mask set, edge
    function of the main body)."""
    rnd = random.Random(seed)
    waves = [(k, rnd.uniform(0.5, 1.0), rnd.uniform(0, 6.28)) for k in ks]

    def edge(th):
        return 1.0 + wob * sum(a * math.sin(k * th + p) for (k, a, p) in waves) / max(1.0, len(waves) * 0.55)

    m = set()
    for y in range(H):
        for x in range(W):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if math.hypot(dx, dy) <= edge(math.atan2(dy, dx)):
                m.add((x, y))
            for (ox, oy, r, rr) in drops:
                if ((x + 0.5 - ox) / r) ** 2 + ((y + 0.5 - oy) / rr) ** 2 <= 1.0:
                    m.add((x, y))
    return m, edge


def stain(g, mask, light=(-0.6, -0.8)):
    """Shade a slime stain from its mask: body 6 with deeper x pockets toward the lower right, a 1-texel wet
    rim D where the edge faces the light (top left) and x where it faces away."""
    lx, ly = light
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    cx, cy = (min(xs) + max(xs) + 1) / 2.0, (min(ys) + max(ys) + 1) / 2.0
    for (x, y) in mask:
        nb = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        out = [(a - x, b - y) for (a, b) in nb if (a, b) not in mask]
        if out:
            fx = sum(o[0] for o in out)
            fy = sum(o[1] for o in out)
            g[y][x] = 'D' if fx * lx + fy * ly > 0 else 'x'
        else:
            g[y][x] = '6'
    # deeper slime pooled in the lower right: an ellipse offset that way, kept a texel or two off the rim
    rx, ry = (max(xs) - min(xs) + 1) / 2.0, (max(ys) - min(ys) + 1) / 2.0
    for (x, y) in mask:
        if g[y][x] != '6':
            continue
        inner = all((x + a, y + b) in mask for a in (-2, 0, 2) for b in (-1, 0, 1))
        ex = (x + 0.5 - (cx + 0.22 * rx)) / (0.62 * rx)
        ey = (y + 0.5 - (cy + 0.30 * ry)) / (0.55 * ry)
        if inner and ex * ex + ey * ey < 1.0:
            g[y][x] = 'x'


def gloss(g, pts, keys='1e'):
    """A short curved wet highlight along pts (texel points), on slime only."""
    for i, (x, y) in enumerate(pts):
        if 0 <= y < len(g) and 0 <= x < len(g[0]) and g[y][x] in ('6', 'x', 'D'):
            g[y][x] = keys[0] if i < len(pts) - 1 else keys[1]
