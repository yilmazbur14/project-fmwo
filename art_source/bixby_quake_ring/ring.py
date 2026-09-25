"""bixby_quake_ring.png: segments of beast Bixby's quake ring, one sheet row per screen-tangent bucket, four
frames of the crest churning in each (0.08 s a frame, looping).

A segment is a straight stretch of the ring's hurt band (36 px of floor either side of the ellipse), drawn on
the floor the way the arena draws it (ground.py): a hellfire crack down its centre line, the broken ground
either side of it heaved up, the magma glowing in it. On that, what the crack throws up (stamps.py): slab
shards and rocks tumbling, dirt, flame tongues and embers.

Rows (screen tangent, rising to the right; flip_h for the other diagonal):
  0 flat   1 1:4   2 1:2   3 1:1   4 2:1   5 4:1   6 vertical
Every frame is FRAME_W x FRAME_H. The pivot, on the crack's centre line on the floor (the ground point to
place on the ellipse and to y-sort by), is the frame's centre in every row.
"""
import math

import numpy as np

import ground as G
import segment as S
import stamps as T

FRAMES = 4
FRAME_TIME = 0.08

# name, screen period (dx, dy), chunks per side per period, chunk stretch along the band
ROWS = [
    ('flat', (16, 0), 4, 1.2),
    ('1:4', (16, -4), 4, 1.2),
    ('1:2', (14, -7), 5, 1.2),
    ('1:1', (11, -11), 5, 1.3),
    ('2:1', (7, -14), 6, 1.6),
    ('4:1', (4, -16), 6, 2.0),
    ('vertical', (0, -16), 6, 2.2),
]

# Working canvas, pivot at a texel corner.
CW, CH = 64, 72
CPX, CPY = 32, 50

# The sheet's frame. Every row's pivot is the frame's centre, (FRAME_W / 2, FRAME_H / 2): a centred Sprite2D
# with no offset puts it on the node's position, and flip_h mirrors about it.
FRAME_W, FRAME_H = 40, 32
PIVOT = (FRAME_W // 2, FRAME_H // 2)

KEEP = 3.5          # moving things stay this many texels inside a period's ends, along the band (= the
                    # overlap a neighbour draws over them)


class Crest:
    """What one row's crack throws up, frame by frame, placed on the row's crack.

    PLAN entries: (kind, where along the core -1..1, which side of the crack (-1 behind, 1 in front,
    0 in it), per-frame values, per-frame turn, per-frame x drift). For a shard the per-frame value is how
    far it has heaved up; for thrown pieces and embers, their height above the crack; for a flame, its size.
    Every row uses the same plan with its own pick of shards, so the crest reads the same all round."""

    PLAN = [
        ('shard', -0.55, -1, [0, 1, 2, 1], None, None),
        ('shard', 0.35, 1, [1, 2, 1, 0], None, None),
        # the flame flares at one spot for two frames, then another: neighbours play frames one apart, so
        # along the ring the flames fall A A B B, and don't beat out every segment
        ('flame', [-0.55, -0.55, 0.45, 0.45], 0, ['M', 'L', 'M', 'S'], [0, 0, 1, 1], None),
        ('shard_t', 0.7, 0, [4, 8, 10, 7], [0, 1, 0, 1], [0, 0, 1, 1]),
        ('rock', -0.8, 0, [9, 6, 3, 6], [1, 0, 1, 0], [0, -1, -1, 0]),
        ('clod', 0.05, 0, [6, 10, 9, 4], [0, 1, 1, 0], [0, 1, 1, 2]),
        ('pebble', -0.3, 0, [3, 7, 11, 9], [0, 1, 0, 1], [0, 0, -1, -1]),
        ('ember', -0.4, 0, [7, 10, 13, 16], None, [0, 0, 1, 1]),
        ('ember', 0.5, 0, [14, 5, 8, 11], None, [0, 1, 1, 0]),
    ]
    # the two upthrust shards each row uses
    PICKS = [('L1', 'S1'), ('W1', 'M1'), ('L2', 'S1'), ('L1', 'M1'), ('W1', 'S1'), ('L2', 'M1'), ('L1', 'S1')]

    def __init__(self, gr):
        self.gr = gr
        self.picks = self.PICKS[gr.index]
        dx, dy = ROWS[gr.index][1]
        self.phi = math.degrees(math.atan2(-dy, dx))

    def root(self, frac, side, half_w=3.5, drift=0):
        """Screen position (x, y) relative to the pivot of the crack (or its lip on `side`) at this fraction
        of the core, and the floor depth there (for sorting against the ground). A stamp half_w texels
        wide, drifting up to `drift` sideways, is kept KEEP texels clear of the period's ends."""
        gr = self.gr
        c, s = math.cos(math.radians(self.phi)), math.sin(math.radians(self.phi))
        reach = (half_w + drift) * c + 1.0 * s + 0.5       # the stamp's footprint along the band at its root
        t = frac * max(0.0, gr.ls / 2 - KEEP - reach) * gr.to_floor
        tt = np.array([t])
        cv = float(gr.meander(tt)[0] * gr.window(tt)[0])
        v = cv + side * (G.CRACK_W + 1.2)
        x, y = gr.to_screen(t, v, 0.0)
        fy = t * gr.u[1] + v * gr.n[1]
        return x, y, fy

    def draw(self, grid, depth, frame):
        shard_no = 0
        for kind, frac, side, values, turns, drift in self.PLAN:
            if isinstance(frac, list):
                frac = frac[frame]
            if kind == 'shard':
                w = len(T.SHARDS[self.picks[shard_no]][0])
            elif kind == 'flame':
                w = 7
            elif kind == 'ember':
                w = 1
            else:
                w = 4
            x, y, fy = self.root(frac, side, w / 2.0, max(abs(v) for v in drift) if drift else 0)
            cx = CPX + int(math.floor(x))
            cy = CPY + int(math.floor(y))
            val = values[frame]
            turn = turns[frame] if turns else 0
            dx = drift[frame] if drift else 0
            if kind == 'shard':
                shape = T.SHARDS[self.picks[shard_no]]
                shard_no += 1
                stamp(grid, depth, shape, cx, cy + 1 - val, fy)
            elif kind == 'flame':
                shape = {'S': T.FLAME_S, 'M': T.FLAME_M, 'L': T.FLAME_L}[val]
                stamp(grid, depth, shape, cx, cy + 1, fy, mirror=turn)
            elif kind == 'ember':
                put_if(grid, depth, cx + dx, cy - val, T.EMBERS[(frame + int(frac * 7)) % 3], fy)
            else:
                shape = T.THROWN[{'shard_t': 'shard'}.get(kind, kind)][turn]
                stamp(grid, depth, shape, cx + dx, cy - val, fy)


def stamp(grid, depth, shape, cx, by, fy, mirror=False):
    """A stamp with its bottom row at `by`, centred on column cx."""
    h, w = len(shape), len(shape[0])
    for j, row in enumerate(shape):
        for i, k in enumerate(row[::-1] if mirror else row):
            if k != '.':
                put_if(grid, depth, cx - w // 2 + i, by - (h - 1) + j, k, fy)


def put_if(grid, depth, x, y, k, fy):
    """A crest texel, unless the ground there is nearer the camera than the crest's root."""
    if not (0 <= y < CH and 0 <= x < CW):
        return
    if grid[y][x] != '.' and depth[y][x] > fy + 0.5:
        return
    grid[y][x] = k


def build_canvas(i):
    """A row's four frames on the working canvas, and its Ground."""
    name, period, seeds, stretch = ROWS[i]
    gr = G.Ground(i, period, seeds, stretch, overlap=3.5, allow=2.5)
    hit = gr.march(CW, CH, CPX, CPY)
    crest = Crest(gr)
    frames = []
    for f in range(FRAMES):
        g, _ = S.shade(gr, hit, CW, CH, f)
        depth = [[hit['y'][r, c] if g[r][c] != '.' else -99.0 for c in range(CW)] for r in range(CH)]
        crest.draw(g, depth, f)
        frames.append(g)
    return frames, gr


def bounds(frames):
    xs, ys = [], []
    for g in frames:
        for y, row in enumerate(g):
            for x, k in enumerate(row):
                if k != '.':
                    xs.append(x)
                    ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def layout():
    """Every row cut to FRAME_W x FRAME_H with its pivot at the frame's centre:
    [(frames as lists of strings, Ground)]."""
    out = []
    px, py = PIVOT
    for i in range(len(ROWS)):
        frames, gr = build_canvas(i)
        x0, x1, y0, y1 = bounds(frames)
        assert CPX - x0 <= px and x1 + 1 - CPX <= FRAME_W - px, 'row %d is too wide for the frame' % i
        assert CPY - y0 <= py and y1 + 1 - CPY <= FRAME_H - py, 'row %d is too tall for the frame' % i
        ox, oy = CPX - px, CPY - py
        cut = [[''.join(g[oy + r][ox:ox + FRAME_W]) for r in range(FRAME_H)] for g in frames]
        out.append((cut, gr))
    return out


def view(grids, scale, path, bg=(160, 196, 128, 255), gap=2):
    """Grids side by side at `scale` over mat green."""
    from PIL import Image
    from ringpal import to_image
    w = sum(len(g[0]) for g in grids) + gap * (len(grids) - 1)
    h = max(len(g) for g in grids)
    im = Image.new('RGBA', (w, h), bg)
    x = 0
    for g in grids:
        im.alpha_composite(to_image(g), (x, 0))
        x += len(g[0]) + gap
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)
    return path
