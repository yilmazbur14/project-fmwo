"""Turning a key map into the juggle frame.

Quarter turns are exact: every pixel lands on exactly one pixel, so a figure turned 90, 180 or 270
degrees is the approved art moved, nothing resampled. The tumble loop and the mat frames use only
these, so the face, crest and ports on them are the rig's own pixels.

Any other angle goes through RotSprite's idea: the map is scaled 8x with Scale2x three times (which
rounds a staircase into a diagonal instead of blowing it into blocks, and never invents a key), that
is turned by point sampling, and the result is read back at 1x. Two rules from Mason's juggle
(art_source/mason_juggle/jlib.py) keep the silhouette clean:

  1. never resample the outer keyline: it is first filled with the colour inside it, the fill is
     turned, and a fresh 1px keyline is drawn on the turned silhouette; and
  2. sample backwards (every destination pixel asks the source what is under it), so a turn can
     never punch a hole.

Coordinates: `pl` is the pivot in the source (LOCAL) map, `pf` where it lands in the FRAME.
Pivots are pixel corners (whole numbers) so quarter turns stay exact.
"""
import math

import mj_base as J

N4 = J.N4
N8 = J.N8


# ------------------------------------------------------------------------------ quarter turns
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


def quarter_owner(owner, q, pl, pf):
    return quarter(owner, q, pl, pf)


# ------------------------------------------------------------------------------ keyline in / out
def commonest(keys):
    """The most frequent key; a tie goes to whichever came first in the (fixed) neighbour order.
    Never max(set(keys), key=keys.count): a set of strings iterates in an order Python randomises
    per process, so ties broke differently run to run and two builds of the same code differed."""
    return max(keys, key=lambda k: (keys.count(k), -keys.index(k)))


def opaque(px, x, y):
    return (x, y) in px


def fill_keyline(px):
    """The outer black keyline replaced by the interior colour beside it (Mason's jlib)."""
    outer = {p for p, k in px.items() if k == 'k'
             and any((p[0] + dx, p[1] + dy) not in px for dx, dy in N4)}
    out = dict(px)
    todo = set(outer)
    while todo:
        done = []
        for (x, y) in todo:
            cands = [out[(x + dx, y + dy)] for dx, dy in N8
                     if (x + dx, y + dy) in out and out[(x + dx, y + dy)] != 'k'
                     and ((x + dx, y + dy) not in todo)]
            if cands:
                out[(x, y)] = commonest(cands)
                done.append((x, y))
        if not done:
            break
        todo -= set(done)
    return out, outer


def reoutline(px):
    """Every pixel on the silhouette edge becomes the 1px keyline."""
    edge = [p for p in px if any((p[0] + dx, p[1] + dy) not in px for dx, dy in N4)]
    for p in edge:
        px[p] = 'k'
    return px


def despeckle(px, keep=()):
    """Rotation crumbs: opaque pixels with fewer than two opaque 4-neighbours."""
    for _ in range(2):
        drop = [p for p in px if p not in keep
                and sum((p[0] + dx, p[1] + dy) in px for dx, dy in N4) < 2]
        for p in drop:
            del px[p]
    return px


def fill_pinholes(px, key=None):
    """Transparent pixels boxed in on four sides: filled with the commonest non-black neighbour
    (or keyline, as mi_fig does, when key='k')."""
    if not px:
        return px
    x0, y0, x1, y1 = J.bbox(px)
    for _ in range(2):
        add = []
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x, y) in px:
                    continue
                n = [px.get((x + dx, y + dy)) for dx, dy in N4]
                if all(n):
                    if key:
                        add.append(((x, y), key))
                        continue
                    c = [k for k in n if k != 'k']
                    add.append(((x, y), commonest(c) if c else 'k'))
        for p, k in add:
            px[p] = k
    return px


# ------------------------------------------------------------------------------ RotSprite
def _grid(px, margin=2):
    x0, y0, x1, y1 = J.bbox(px)
    x0 -= margin
    y0 -= margin
    w = x1 - x0 + 1 + margin
    h = y1 - y0 + 1 + margin
    g = [[px.get((x0 + i, y0 + j)) for i in range(w)] for j in range(h)]
    return g, x0, y0


def scale2x(g):
    h, w = len(g), len(g[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        row = g[y]
        up = g[y - 1] if y > 0 else [None] * w
        dn = g[y + 1] if y < h - 1 else [None] * w
        o0 = out[2 * y]
        o1 = out[2 * y + 1]
        for x in range(w):
            P = row[x]
            A_ = up[x]
            B_ = row[x + 1] if x < w - 1 else None
            C_ = row[x - 1] if x > 0 else None
            D_ = dn[x]
            if C_ == A_ and C_ != D_ and A_ != B_:
                e0 = A_
            else:
                e0 = P
            if A_ == B_ and A_ != C_ and B_ != D_:
                e1 = B_
            else:
                e1 = P
            if D_ == C_ and D_ != B_ and C_ != A_:
                e2 = C_
            else:
                e2 = P
            if B_ == D_ and B_ != A_ and D_ != C_:
                e3 = D_
            else:
                e3 = P
            o0[2 * x] = e0
            o0[2 * x + 1] = e1
            o1[2 * x] = e2
            o1[2 * x + 1] = e3
    return out


def rotsprite(px, theta, pl, pf, sx=1.0, sy=1.0):
    """Turn a key map theta degrees clockwise (any angle) about pl, landing pl on pf, with an
    optional FRAME-space scale (sx, sy) about pf applied after the turn. The outer keyline is
    regenerated, never resampled."""
    filled, _ = fill_keyline(px)
    g, gx0, gy0 = _grid(filled)
    for _ in range(3):
        g = scale2x(g)
    gh, gw = len(g), len(g[0])
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    # destination box from the four turned corners
    x0, y0, x1, y1 = J.bbox(filled)
    corners = [(x0, y0), (x1 + 1, y0), (x0, y1 + 1), (x1 + 1, y1 + 1)]
    xs, ys = [], []
    for (u, v) in corners:
        a, b = u - pl[0], v - pl[1]
        xs.append(pf[0] + (a * c - b * s) * sx)
        ys.append(pf[1] + (a * s + b * c) * sy)
    out = {}
    for Y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for X in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            dx, dy = (X + 0.5 - pf[0]) / sx, (Y + 0.5 - pf[1]) / sy
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


def rotsprite_owner(owner, theta, pl, pf, sx=1.0, sy=1.0):
    """The same backwards sampling for the ownership map (nearest source pixel, no scaling)."""
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    x0, y0, x1, y1 = J.bbox(owner)
    corners = [(x0, y0), (x1 + 1, y0), (x0, y1 + 1), (x1 + 1, y1 + 1)]
    xs, ys = [], []
    for (u, v) in corners:
        a, b = u - pl[0], v - pl[1]
        xs.append(pf[0] + (a * c - b * s) * sx)
        ys.append(pf[1] + (a * s + b * c) * sy)
    out = {}
    for Y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for X in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            dx, dy = (X + 0.5 - pf[0]) / sx, (Y + 0.5 - pf[1]) / sy
            u = pl[0] + dx * c + dy * s
            v = pl[1] - dx * s + dy * c
            q = (int(math.floor(u)), int(math.floor(v)))
            if q in owner:
                out[(X, Y)] = owner[q]
    return out


def squash_rows(px, owner, k, protect_top=2, protect_bottom=3):
    """Flatten a figure that is already on the mat by taking whole rows OUT of it, never by
    resampling: n = round(height * (1 - k)) rows are dropped and everything above each dropped row
    comes down one, so the lowest row stays on the mat.

    Which rows: turned a quarter, almost all of his one-texel detail (sock stripes, belt edges, the
    eyes' lids, the teeth, the brows) runs across the rows, so a row can go without breaking any
    of it. Each row is costed by the detail that runs ALONG it (a pixel whose left or right
    neighbour carries the same key while the pixels above and below it do not: a horizontal line)
    plus the face, which is never thinned where it can be helped; the cheapest rows go, no two
    adjacent. The keyline is redrawn on the result, so a dropped silhouette edge closes again."""
    x0, y0, x1, y1 = J.bbox(px)
    h = y1 - y0 + 1
    n = int(round(h * (1.0 - k)))
    cost = {}
    for y in range(y0 + protect_top, y1 - protect_bottom + 1):
        c = 0
        for x in range(x0, x1 + 1):
            key = px.get((x, y))
            if key is None:
                continue
            up, dn = px.get((x, y - 1)), px.get((x, y + 1))
            lf, rt = px.get((x - 1, y)), px.get((x + 1, y))
            if (lf == key or rt == key) and up != key and dn != key:
                c += 3
            if up is None or dn is None:
                c += 2                      # a silhouette edge runs through this row here
            if owner.get((x, y)) == 'face':
                c += 2
        cost[y] = c
    chosen = []
    for y in sorted(cost, key=lambda r: (cost[r], r)):
        if len(chosen) >= n:
            break
        if any(abs(y - c) <= 1 for c in chosen):
            continue
        chosen.append(y)
    chosen.sort()
    out, own = {}, {}
    for (x, y), key in px.items():
        if y in chosen:
            continue
        d = sum(1 for c in chosen if c > y)
        out[(x, y + d)] = key
        if (x, y) in owner:
            own[(x, y + d)] = owner[(x, y)]
    fill_pinholes(out)
    reoutline(out)
    return out, own, chosen


def turn(px, owner, theta, pl, pf):
    """Quarter turns exactly, anything else by RotSprite. Returns (px, owner) in the frame."""
    q = theta / 90.0
    if abs(q - round(q)) < 1e-9:
        qi = int(round(q))
        return quarter(px, qi, pl, pf), quarter(owner, qi, pl, pf)
    return rotsprite(px, theta, pl, pf), rotsprite_owner(owner, theta, pl, pf)
