"""Turning a key map: the juggle rig's turner (art_source/jordan_juggle/jj_rot.py, the approved juggle's
method), copied here rather than imported so the juggle rig never loads beside the fight rig.

Quarter turns are exact. Any other angle goes through RotSprite: Scale2x three times (never invents a
key), point-sampled backwards (never punches a hole), read back at 1x; the outer keyline is filled
with the colour inside it first, turned, and redrawn fresh on the turned silhouette.
"""
import math

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def quarter(px, q, pl, pf):
    """Exact turn by q quarter turns clockwise about corner pl, landing on corner pf."""
    q %= 4
    out = {}
    for (x, y), k in px.items():
        a, b = x + 0.5 - pl[0], y + 0.5 - pl[1]
        for _ in range(q):
            a, b = -b, a
        out[(int(math.floor(pf[0] + a)), int(math.floor(pf[1] + b)))] = k
    return out


def commonest(keys):
    return max(keys, key=lambda k: (keys.count(k), -keys.index(k)))


def fill_keyline(px):
    outer = {p for p, k in px.items() if k == 'k' and any((p[0] + dx, p[1] + dy) not in px for dx, dy in N4)}
    out = dict(px)
    todo = set(outer)
    while todo:
        done = []
        for (x, y) in sorted(todo):
            cands = [out[(x + dx, y + dy)] for dx, dy in N8
                     if (x + dx, y + dy) in out and out[(x + dx, y + dy)] != 'k' and (x + dx, y + dy) not in todo]
            if cands:
                out[(x, y)] = commonest(cands)
                done.append((x, y))
        if not done:
            break
        todo -= set(done)
    return out, outer


def reoutline(px):
    edge = [p for p in px if any((p[0] + dx, p[1] + dy) not in px for dx, dy in N4)]
    for p in edge:
        px[p] = 'k'
    return px


def despeckle(px, keep=()):
    for _ in range(2):
        drop = [p for p in px if p not in keep and sum((p[0] + dx, p[1] + dy) in px for dx, dy in N4) < 2]
        for p in drop:
            del px[p]
    return px


def fill_pinholes(px):
    if not px:
        return px
    x0, y0, x1, y1 = bbox(px)
    for _ in range(2):
        add = []
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x, y) in px:
                    continue
                n = [px.get((x + dx, y + dy)) for dx, dy in N4]
                if all(n):
                    c = [k for k in n if k != 'k']
                    add.append(((x, y), commonest(c) if c else 'k'))
        for p, k in add:
            px[p] = k
    return px


def _grid(px, margin=2):
    x0, y0, x1, y1 = bbox(px)
    x0 -= margin
    y0 -= margin
    w = x1 - x0 + 1 + margin
    h = y1 - y0 + 1 + margin
    return [[px.get((x0 + i, y0 + j)) for i in range(w)] for j in range(h)], x0, y0


def scale2x(g):
    h, w = len(g), len(g[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        row = g[y]
        up = g[y - 1] if y > 0 else [None] * w
        dn = g[y + 1] if y < h - 1 else [None] * w
        for x in range(w):
            P = row[x]
            A_ = up[x]
            B_ = row[x + 1] if x < w - 1 else None
            C_ = row[x - 1] if x > 0 else None
            D_ = dn[x]
            out[2 * y][2 * x] = A_ if (C_ == A_ and C_ != D_ and A_ != B_) else P
            out[2 * y][2 * x + 1] = B_ if (A_ == B_ and A_ != C_ and B_ != D_) else P
            out[2 * y + 1][2 * x] = C_ if (D_ == C_ and D_ != B_ and C_ != A_) else P
            out[2 * y + 1][2 * x + 1] = D_ if (B_ == D_ and B_ != A_ and D_ != C_) else P
    return out


def rotsprite(px, theta, pl, pf):
    """Turn a key map theta degrees clockwise about pl, landing pl on pf; the keyline redrawn."""
    filled, _ = fill_keyline(px)
    g, gx0, gy0 = _grid(filled)
    for _ in range(3):
        g = scale2x(g)
    gh, gw = len(g), len(g[0])
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    x0, y0, x1, y1 = bbox(filled)
    xs, ys = [], []
    for (u, v) in ((x0, y0), (x1 + 1, y0), (x0, y1 + 1), (x1 + 1, y1 + 1)):
        a, b = u - pl[0], v - pl[1]
        xs.append(pf[0] + a * c - b * s)
        ys.append(pf[1] + a * s + b * c)
    out = {}
    for Y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for X in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            dx, dy = X + 0.5 - pf[0], Y + 0.5 - pf[1]
            u = pl[0] + dx * c + dy * s
            v = pl[1] - dx * s + dy * c
            gi = int(math.floor((u - gx0) * 8))
            gj = int(math.floor((v - gy0) * 8))
            if 0 <= gi < gw and 0 <= gj < gh:
                k = g[gj][gi]
                if k is not None:
                    out[(X, Y)] = k
    despeckle(out)
    fill_pinholes(out)
    reoutline(out)
    return out


def turn(px, theta, pl, pf=None):
    pf = pf or pl
    q = theta / 90.0
    if abs(q - round(q)) < 1e-9:
        return quarter(px, int(round(q)), pl, pf)
    return rotsprite(px, theta, pl, pf)
