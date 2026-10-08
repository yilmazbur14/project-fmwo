"""Jordan's room - cutting the five layers into crumble pieces.

Pieces tile their layer exactly: every opaque pixel of a layer belongs to one
piece, and the pieces recomposed give the layer back pixel for pixel.

* Props, clutter and furniture: a whole prop is one piece. A Tracker watches
  the layer being drawn and records, pixel by pixel, which item drew it last
  (it only reads the canvas; the art is drawn exactly as before). Then:
    - items that draw over each other are joined into one piece, so nothing
      is left with a hole when its neighbour falls first (a laundry pile, a box
      standing in front of another);
    - a thin item (a string of fairy lights, a cable, the cabinet glass drawn
      over its figures) never joins anything: where it crosses another prop
      those pixels stay with that prop, as if the wire were printed on it;
    - light (the monitors' halo and pool) never joins anything either; it is
      chunked like the floor;
    - each piece is split into its connected parts, and crumbs (a few
      pixels, like packing peanuts or the glow dots round a fairy light) go to
      the piece they touch or sit nearest.
* Floor, walls and light: irregular chunks, a Voronoi cut on a jittered grid
  with its coordinates warped by noise so the edges come out ragged, then
  held to 16-40 texels a side (big cells split, slivers merged).
"""
import math
import random

import numpy as np

from jr_lib import W, H, T, hsh

# ---------------------------------------------------------------- the tracker


class Null:
    def begin(self, *a, **k):
        pass

    def end(self):
        pass


class Tracker:
    def __init__(self, canvas):
        self.c = canvas
        self.owner = np.full((H, W), -1, np.int32)
        self.items = []
        self.parent = []
        self.cur = None
        self.before = None

    def begin(self, name, thin=False, light=False, attach=False, group=None):
        assert self.cur is None, 'item %s still open' % self.items[self.cur]['name']
        self.before = self.c.a.copy()
        self.cur = len(self.items)
        self.items.append(dict(name=name, thin=thin, light=light, attach=attach, group=group))
        self.parent.append(self.cur)

    def end(self):
        i = self.cur
        it = self.items[i]
        changed = self.c.a != self.before
        prev = self.owner[changed]
        light = np.array([x['light'] for x in self.items] + [False], bool)   # [-1] -> False
        thin = np.array([x['thin'] for x in self.items] + [False], bool)
        if it['thin']:
            keep = (prev >= 0) & ~light[prev]
            self.owner[changed] = np.where(keep, prev, i)
        else:
            for p in np.unique(prev[prev >= 0]):
                if not (light[p] or thin[p]):
                    self.union(i, int(p))
            self.owner[changed] = i
        self.cur = None
        self.before = None

    # union-find
    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)

    def groups(self):
        """Item groups after joins and explicit groups: owner image of group roots."""
        by_group = {}
        for i, it in enumerate(self.items):
            if it['group'] is not None:
                if it['group'] in by_group:
                    self.union(i, by_group[it['group']])
                else:
                    by_group[it['group']] = i
        root = np.array([self.find(i) for i in range(len(self.items))] + [-1], np.int64)
        lab = np.where(self.owner >= 0, root[self.owner], -1)
        return lab


# ---------------------------------------------------------------- connectivity
def components(mask, diag=True):
    """Label connected parts of a bool mask. Returns (labels, n); labels -1 outside."""
    lab = np.full(mask.shape, -1, np.int32)
    n = 0
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0] != -1:
            continue
        stack = [(y0, x0)]
        lab[y0, x0] = n
        while stack:
            y, x = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    if not diag and dy != 0 and dx != 0:
                        continue
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] \
                            and lab[yy, xx] == -1:
                        lab[yy, xx] = n
                        stack.append((yy, xx))
        n += 1
    return lab, n


def _ring(mask):
    g = np.zeros_like(mask)
    g[1:, :] |= mask[:-1, :]
    g[:-1, :] |= mask[1:, :]
    g[:, 1:] |= mask[:, :-1]
    g[:, :-1] |= mask[:, 1:]
    g[1:, 1:] |= mask[:-1, :-1]
    g[1:, :-1] |= mask[:-1, 1:]
    g[:-1, 1:] |= mask[1:, :-1]
    g[:-1, :-1] |= mask[1:, 1:]
    return g & ~mask


def nearest_label(mask, lab, exclude, reach=40):
    """The label that most touches `mask`, growing outward until one is found."""
    m = mask.copy()
    for _ in range(reach):
        ring = _ring(m)
        vals = lab[ring]
        vals = vals[(vals >= 0) & (vals != exclude)]
        if len(vals):
            u, cnt = np.unique(vals, return_counts=True)
            return int(u[np.argmax(cnt)])
        m |= ring
    return None


def split_and_tidy(lab, never_alone=(), crumb=24):
    """Split every label into its connected parts; parts smaller than `crumb`
    pixels, and every part of a label in `never_alone`, join the label they touch
    or sit nearest. Returns a new label image with labels 0..n-1."""
    out = np.full(lab.shape, -1, np.int64)
    parts = []                      # (mask, alone_ok)
    for L in np.unique(lab[lab >= 0]):
        m = lab == L
        cl, n = components(m)
        sizes = [(cl == k).sum() for k in range(n)]
        for k in range(n):
            pm = cl == k
            alone_ok = (L not in never_alone) and sizes[k] >= crumb
            parts.append((pm, alone_ok))
    nid = 0
    pending = []
    for (pm, ok) in parts:
        if ok:
            out[pm] = nid
            nid += 1
        else:
            pending.append(pm)
    # merge the pending parts, biggest first, into what they touch
    pending.sort(key=lambda m: -int(m.sum()))
    for pm in pending:
        tgt = nearest_label(pm, out, -2)
        if tgt is None:
            out[pm] = nid
            nid += 1
        else:
            out[pm] = tgt
    return _renumber(out)


def _renumber(lab):
    out = np.full(lab.shape, -1, np.int64)
    u = np.unique(lab[lab >= 0])
    for i, L in enumerate(u):
        out[lab == L] = i
    return out


# ---------------------------------------------------------------- ragged chunks
def _walk(n, amp, rnd, step=1, phase=0):
    """A bounded random walk of n integers in [-amp, amp] that moves only every
    `step` samples (counted from `phase`)."""
    v = 0
    out = np.zeros(n, np.int64)
    for i in range(n):
        if (i - phase) % step == 0:
            v = max(-amp, min(amp, v + rnd.choice((-1, 0, 0, 1))))
        out[i] = v
    return out


class Brick:
    """A staggered brick grid with ragged seams, as a label function.

    rows: nominal y edges [y0, y1, ..., yn]; the inner ones wander by up to hjag
    texels along x. Each row band is cut every cell_w texels (odd rows offset by
    half a cell); each cut wanders by up to vjag texels along y, changing only
    every vstep rows from vphase (so the floor breaks board by board)."""

    def __init__(self, rows, cell_w, seed, vjag=2, hjag=1, vstep=1, vphase=0, x0=0, x1=W):
        rnd = random.Random(seed)
        self.rows = rows
        self.hb = [rows[i] + _walk(W, hjag, rnd) for i in range(1, len(rows) - 1)]
        self.cuts = []
        for r in range(len(rows) - 1):
            stagger = (r % 2) * cell_w / 2.0
            xs = []
            nominal = []
            x = x0 + cell_w - stagger
            while x < x1 - 14:
                if x > x0 + 14:
                    nominal.append(x)
                x += cell_w
            # the end cells take what is left; split them if that is too wide
            lim = cell_w + 2
            if nominal and nominal[0] - x0 > lim:
                nominal.insert(0, (x0 + nominal[0]) / 2.0)
            if nominal and x1 - nominal[-1] > lim:
                nominal.append((nominal[-1] + x1) / 2.0)
            xs = [int(round(v)) + _walk(H, vjag, rnd, vstep, vphase) for v in nominal]
            self.cuts.append(xs)

    def label(self, mask):
        ys, xs = np.nonzero(mask)
        row = np.zeros(len(xs), np.int64)
        for hb in self.hb:
            row += (ys >= hb[xs]).astype(np.int64)
        col = np.zeros(len(xs), np.int64)
        for r, cuts in enumerate(self.cuts):
            m = row == r
            for cut in cuts:
                col[m] += (xs[m] >= cut[ys[m]]).astype(np.int64)
        lab = np.full(mask.shape, -1, np.int64)
        lab[ys, xs] = row * 1000 + col
        return lab


def room_grid(floor_y=150, cell_w=36, seed=5, coarse=False):
    """The room's two grids: the wall above the base line, the floor (and the caps
    beside and below it) from the base line down. Returns label(mask). coarse=True
    doubles the cells (for the monitors' light, which is not floor or wall)."""
    if coarse:
        wall = Brick([0, 76, floor_y], cell_w * 2, seed + 2, vjag=2, hjag=1)
        ground = Brick([floor_y, floor_y + 80, floor_y + 160, H], cell_w * 2, seed + 3,
                       vjag=2, hjag=0, vstep=8, vphase=floor_y)
    else:
        wall = Brick([0, 38, 76, 114, floor_y], cell_w, seed, vjag=2, hjag=1)
        ground = Brick([floor_y, floor_y + 40, floor_y + 80, floor_y + 120, floor_y + 160,
                        floor_y + 200, H], cell_w, seed + 1, vjag=2, hjag=0, vstep=8,
                       vphase=floor_y)

    def label(mask):
        up = mask.copy()
        up[floor_y:, :] = False
        down = mask.copy()
        down[:floor_y, :] = False
        a = wall.label(up)
        b = ground.label(down)
        out = np.where(a >= 0, a, np.where(b >= 0, b + 100000, -1))
        return out
    return label


def cells(mask, grid):
    """Cut a mask on a grid by cell alone, connected or not (for a dithered glow,
    whose sparse edge pixels simply ride with the cell they fall in)."""
    return _renumber(grid(mask))


def chunk(mask, grid, crumb=60, max_dim=40):
    """Cut a bool mask on the room grid into ragged chunks; stray bits and specks
    under `crumb` pixels (a dithered glow's edge) join the chunk they touch most,
    as long as it still fits max_dim a side, else stay a small piece of their own."""
    lab = grid(mask)
    out = np.full(lab.shape, -1, np.int64)
    specks = []
    nid = 0
    for L in np.unique(lab[lab >= 0]):
        cl, n = components(lab == L)
        for k in range(n):
            pm = cl == k
            if pm.sum() >= crumb:
                out[pm] = nid
                nid += 1
            else:
                specks.append(pm)
    specks.sort(key=lambda m: -int(m.sum()))
    for pm in specks:
        m = pm.copy()
        placed = False
        for _ in range(6):
            ring = _ring(m)
            vals = out[ring]
            vals = vals[vals >= 0]
            if len(vals):
                u, cnt = np.unique(vals, return_counts=True)
                for tgt in u[np.argsort(-cnt)]:
                    by, bx = np.nonzero(pm | (out == tgt))
                    if bx.max() - bx.min() < max_dim and by.max() - by.min() < max_dim:
                        out[pm] = tgt
                        placed = True
                        break
            if placed:
                break
            m |= ring
        if not placed:
            out[pm] = nid
            nid += 1
    return _renumber(out)


# ---------------------------------------------------------------- pieces out
def pieces_from_labels(layer_rgba, lab):
    """[(label, x0, y0, rgba crop)] for every label; the crop keeps only that
    label's pixels."""
    out = []
    for L in np.unique(lab[lab >= 0]):
        m = lab == L
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        crop = np.zeros((y1 - y0 + 1, x1 - x0 + 1, 4), np.uint8)
        sub = m[y0:y1 + 1, x0:x1 + 1]
        crop[sub] = layer_rgba[y0:y1 + 1, x0:x1 + 1][sub]
        out.append((int(L), int(x0), int(y0), crop))
    out.sort(key=lambda p: (p[2], p[1]))
    return out


def recompose(pieces, size=(W, H)):
    """Paste pieces back; also returns how many pieces cover each pixel."""
    img = np.zeros((size[1], size[0], 4), np.uint8)
    cover = np.zeros((size[1], size[0]), np.int32)
    for (_, x0, y0, crop) in pieces:
        h, w = crop.shape[:2]
        m = crop[:, :, 3] > 0
        region = img[y0:y0 + h, x0:x0 + w]
        region[m] = crop[m]
        cover[y0:y0 + h, x0:x0 + w] += m
    return img, cover
