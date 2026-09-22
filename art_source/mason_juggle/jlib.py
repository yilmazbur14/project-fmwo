"""Juggle-frame machinery for Mason.

Mason's approved look lives in art_source/mason/rig.py, which renders him at
64x64 in his own upright frame and is checked against mason.png pixel for pixel.
Nothing here redraws him: the rig renders the torso and head, and this module
*places* that render into the bigger juggle frame under a 2x2 matrix, so a pose
can be rotated and squashed without ever hand-redrawing the hood ring, the comb,
the googly eyes or the beard.

Two rules make a rotated pixel sprite stay clean:

  1. Never resample the outer keyline.  The source's outer black pixels are
     filled with the interior colour next to them first (`fill_keyline`), the
     rotation samples that, and the keyline is drawn fresh at exactly 1px from
     the rotated silhouette (`reoutline`).  A resampled outline goes 2px thick on
     one side and breaks on the other; a regenerated one cannot.
  2. Inverse-map, never forward-map.  Every destination pixel asks the source
     what is under it, so a rotation can never punch holes.

Two things are done in the juggle frame rather than in his own:

  * `relight` turns the key light back to the frame's upper left, because
    rotating a sprite rotates its shading with it and the cast's light does not
    move; and
  * the wings are drawn where they point ON SCREEN, because a limp arm hangs the
    way gravity points, not the way the body happens to be lying.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mason'))

import rig                                                          # noqa: E402
import props                                                        # noqa: E402
from rig import (BLACK, WHITE, CREAM, CREAM_HI, CREAM_MID, CREAM_DEEP,  # noqa: E402,F401
                 RED, YEL, KHAKI, hex2rgba)

# ---------------------------------------------------------------- frame ------
# 128x96: twice as wide and half again as tall as Mason's own 64x64 frame, the
# same expansion Eric's sheet took (128x128 -> 256x192) when his poses started
# to sprawl.  See REPORT notes in build.py for the measurements behind it.
W, H = 128, 96
FEET = (64, 95)          # bottom middle, the row his feet stand on
# His middle in the air, which the finisher's camera follows: the measured
# centroid of the drawn tumble figure.  It is the belly, because his belly is
# where his mass is -- see poses.COM for why that matters.
TUMBLE_CENTRE = (64, 52)
SRC = 64                 # the rig's own frame size
# The local canvas the rig renders onto.  It has to be BIGGER than the rig's own
# 64x64: raster() seeds its flood fill from the canvas border, so a silhouette
# that so much as touches the edge lets the outside leak in and the whole
# interior comes back empty -- the symptom is a pose that renders as a floating
# comb, face and arms with no body at all.  A posed foot at y=65 is enough to do
# it.  16px of slack on the right and bottom, with 0,0 unchanged, keeps every
# rig coordinate meaning exactly what it means in mason.png.
LOCAL = 96

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

CLEAR = (0, 0, 0, 0)


def blank():
    return [[CLEAR] * W for _ in range(H)]


def put(g, x, y, col):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = hex2rgba(col) if isinstance(col, str) else col


def get(g, x, y):
    if 0 <= x < W and 0 <= y < H:
        return g[y][x]
    return CLEAR


def opaque(g, x, y):
    return get(g, x, y)[3] > 0


# ------------------------------------------------------- the rig, locally ----
def render_local(pose):
    """Mason in his own upright frame, exactly as the approved rig draws him.

    The shading thresholds are frozen at 64x64 with the rig's own mirror fold, so
    they stay the ones mason.png was approved with; only the canvas grows.
    """
    if rig.TH is None:
        rig.W = rig.H = SRC
        rig.freeze_thresholds()
    rig.W = rig.H = LOCAL
    g = rig.render(pose)
    if bbox_of(g)[3] >= LOCAL or bbox_of(g)[2] >= LOCAL:
        raise SystemExit('pose touches the local canvas edge; the fill will leak')
    return g


def label_local(pose):
    """Which part of him owns each pixel of the local canvas ('hood', 'body',
    'leg_r', 'foot_l' ...).  The rig's own classifier, which is a pure function of
    the coordinates, so it can be sampled through the same transform as the art."""
    c = rig.make_ctx(pose)
    owner = rig.owner_fn(c)
    return [[owner(x, y) for x in range(LOCAL)] for y in range(LOCAL)]


def figure(g):
    """His body: the largest 8-connected run of opaque pixels.  Effects -- dust,
    speed lines, motion arcs -- are their own islands, so measurements of where HE
    is are not thrown off by a mote drifting past his head."""
    seen = [[False] * W for _ in range(H)]
    best = []
    for y in range(H):
        for x in range(W):
            if not g[y][x][3] or seen[y][x]:
                continue
            stack, part = [(x, y)], []
            seen[y][x] = True
            while stack:
                a, b = stack.pop()
                part.append((a, b))
                for dx, dy in N8:
                    u, v = a + dx, b + dy
                    if 0 <= u < W and 0 <= v < H and g[v][u][3] and not seen[v][u]:
                        seen[v][u] = True
                        stack.append((u, v))
            if len(part) > len(best):
                best = part
    return best


def bbox_of(g):
    n, m = len(g), len(g[0])
    xs = [x for y in range(n) for x in range(m) if g[y][x][3]]
    ys = [y for y in range(n) for x in range(m) if g[y][x][3]]
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def fill_keyline(src):
    """Replace the outer black keyline with the interior colour beside it.

    The rotation samples this, so the silhouette stays solid but carries no
    outline of its own; `reoutline` then draws one at 1px on the rotated shape.
    Interior black (the hood ring, the face, the mouth) is left alone.
    """
    blk = hex2rgba(BLACK)
    n = len(src)
    m = len(src[0])

    def op(x, y):
        return 0 <= x < m and 0 <= y < n and src[y][x][3] > 0

    outer = {(x, y) for y in range(n) for x in range(m)
             if src[y][x][3] > 0 and src[y][x][:3] == blk[:3]
             and any(not op(x + dx, y + dy) for dx, dy in N4)}
    out = [row[:] for row in src]
    # Grow the interior outwards one ring at a time until every outer-black
    # pixel has been given a colour.
    todo = set(outer)
    while todo:
        done = []
        for (x, y) in todo:
            cands = [src[y + dy][x + dx] for dx, dy in N8
                     if op(x + dx, y + dy) and (x + dx, y + dy) not in outer]
            cands += [out[y + dy][x + dx] for dx, dy in N8
                      if op(x + dx, y + dy) and (x + dx, y + dy) in outer
                      and out[y + dy][x + dx][:3] != blk[:3]]
            cands = [c for c in cands if c[:3] != blk[:3]]
            if cands:
                out[y][x] = max(cands, key=cands.count)
                done.append((x, y))
        if not done:
            break
        todo -= set(done)
    return out


# ------------------------------------------------------------ placement ------
def matrix(angle_deg, sx=1.0, sy=1.0, post_sx=1.0, post_sy=1.0):
    """Local scale, then rotation (clockwise positive on screen), then a frame-space
    scale -- the last one is how a body flattens against the mat whatever its lean."""
    t = math.radians(angle_deg)
    c, s = math.cos(t), math.sin(t)
    # rotation applied to the locally scaled point
    a, b = c * sx, -s * sy
    d, e = s * sx, c * sy
    return (a * post_sx, b * post_sx, d * post_sy, e * post_sy)


def _inverse(M):
    a, b, c, d = M
    det = a * d - b * c
    return (d / det, -b / det, -c / det, a / det)


def place(dst, src, M, psrc, pdst):
    """dst = M . (src - psrc) + pdst, sampled backwards so it cannot make holes.

    Returns the local coordinate behind every frame pixel, which is what lets the
    relight ask the rig where on his body a pixel sits.
    """
    umap = [[None] * W for _ in range(H)]
    src = fill_keyline(src)
    n, m = len(src), len(src[0])
    Mi = _inverse(M)
    # destination bounding box from the four transformed corners
    xs, ys = [], []
    for (u, v) in ((0, 0), (m, 0), (0, n), (m, n)):
        du, dv = u - psrc[0], v - psrc[1]
        xs.append(M[0] * du + M[1] * dv + pdst[0])
        ys.append(M[2] * du + M[3] * dv + pdst[1])
    x0, x1 = int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 1
    y0, y1 = int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 1
    for Y in range(max(0, y0), min(H, y1)):
        for X in range(max(0, x0), min(W, x1)):
            dx, dy = X + 0.5 - pdst[0], Y + 0.5 - pdst[1]
            u = Mi[0] * dx + Mi[1] * dy + psrc[0]
            v = Mi[2] * dx + Mi[3] * dy + psrc[1]
            sx, sy = int(math.floor(u)), int(math.floor(v))
            if 0 <= sx < m and 0 <= sy < n and src[sy][sx][3]:
                dst[Y][X] = src[sy][sx]
                umap[Y][X] = (sx, sy)
    return umap


def place_labels(src, M, psrc, pdst):
    """The same backwards sampling as `place`, for the ownership map."""
    n, m = len(src), len(src[0])
    Mi = _inverse(M)
    out = [[None] * W for _ in range(H)]
    for Y in range(H):
        for X in range(W):
            dx, dy = X + 0.5 - pdst[0], Y + 0.5 - pdst[1]
            u = Mi[0] * dx + Mi[1] * dy + psrc[0]
            v = Mi[2] * dx + Mi[3] * dy + psrc[1]
            sx, sy = int(math.floor(u)), int(math.floor(v))
            if 0 <= sx < m and 0 <= sy < n:
                out[Y][X] = src[sy][sx]
    return out


# ------------------------------------------------------------- relighting ---
# The four-tone skin ramp, by value, so a pass can tell his volumes apart from
# his costume without re-deriving the palette.
RAMP_NAME = {hex2rgba(c)[:3]: c for c in (CREAM_HI, CREAM, CREAM_MID, CREAM_DEEP)}
CREAM_RAMP = list(RAMP_NAME)


def _normal(x, y, cx, cy, rx, ry):
    """rig.lum's geometry with the dot product left off: the surface normal of the
    volume at a point, so the caller can turn the LIGHT instead of the body."""
    nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 > 1.0:
        s = math.sqrt(d2)
        return nx / s, ny / s, 0.0
    return nx, ny, math.sqrt(1.0 - d2)


def _body_normal(c, o, x, y):
    """The rig's own shade_value, returning the normal.  Because both the hood/body
    blend and the dot with the light are linear, blending normals and then dotting
    gives exactly the value shade_value would have produced -- so at zero rotation
    this reproduces the approved shading pixel for pixel."""
    hx_, hy_ = c.head
    vh = _normal(x - hx_, y - hy_, 31.5, 20.0, 15.0, 15.0)
    if o == 'hood':
        return 'hood', vh
    vb = _normal(x - c.bdx - c.shear * 11, y - c.bdy,
                 31.5, 53 + (42 - 53) * c.sy, 23.0 * c.sx, 23.0 * c.sy)
    ly = y - hy_
    if ly >= 34:
        return 'body', vb
    t = (ly - 29) / 5.0
    return 'body', tuple(vh[i] * (1 - t) + vb[i] * t for i in range(3))


def relight(g, umap, ctx, angle):
    """Turn the key light back to the frame's upper left.

    Rotating a sprite rotates its shading with it, so a tumbling Mason ends up lit
    from below and reads flat and wrong-way-up beside the rest of the cast.  This
    keeps the rig's volume -- the same belly sphere and hood sphere it always used,
    queried at the pixel's own place on his body -- and rotates only the NORMAL, so
    the light stays where the cast's light is.  At angle 0 it is a no-op.
    """
    owner = rig.owner_fn(ctx)
    t = math.radians(angle)
    ca, sa = math.cos(t), math.sin(t)
    for y in range(H):
        for x in range(W):
            p = g[y][x]
            if not p[3] or p[:3] not in RAMP_NAME or umap[y][x] is None:
                continue
            u, v = umap[y][x]
            who, (nx, ny, nz) = _body_normal(ctx, owner(u, v), u, v)
            lit = ((nx * ca - ny * sa) * rig.LX + (nx * sa + ny * ca) * rig.LY
                   + nz * rig.LZ)
            g[y][x] = hex2rgba(rig.band(lit, rig.TH[who]))


def ticks(g, M, psrc, pdst, ctx):
    """Mason's feather flecks, restamped after the re-light: the rig's own TICKS,
    both sides, carried through the placement so they land on the same part of the
    belly they always land on."""
    for (tx, ty) in rig.TICKS:
        for base in ((tx, ty), (63 - tx, ty)):
            for (dx, dy) in ((0, 0), (1, 1)):
                fx, fy = frame_point(M, psrc, pdst, rig.tb(ctx, base))
                x, y = int(round(fx)) + dx, int(round(fy)) + dy
                cur = get(g, x, y)
                if cur[3] and cur[:3] in RAMP_NAME:
                    put(g, x, y, rig.STEP[RAMP_NAME[cur[:3]]])


def frame_point(M, psrc, pdst, p):
    """Where a point of the local 64x64 frame lands in the juggle frame."""
    dx, dy = p[0] - psrc[0], p[1] - psrc[1]
    return (M[0] * dx + M[1] * dy + pdst[0], M[2] * dx + M[3] * dy + pdst[1])


# ---------------------------------------------------------- limbs, in frame --
def limb(g, pts, radii, colour=None, grooves=()):
    """A capsule chain drawn straight into the juggle frame, cylinder-shaded and
    outlined in black -- the rig's own limb, freed from its 64x64 canvas."""
    colour = colour or props.wing_colour
    mask = props.limb_mask(pts, radii)
    inter = set()
    for (x, y), val in mask.items():
        if any((x + dx, y + dy) not in mask for dx, dy in N4):
            put(g, x, y, BLACK)
        else:
            col = colour(x, y, val)
            if col:
                put(g, x, y, col)
            inter.add((x, y))
    for (x, y) in grooves:
        if (x, y) in inter:
            put(g, x, y, CREAM_MID)
    return inter


def sole_foot(g, heel, toes, span=3.6):
    """A chicken foot seen sole-on, three toes fanned -- the KO foot, in frame space."""
    m = {}
    for tip in toes:
        mm = props.limb_mask([heel, tip], [2.7, 2.0])
        for k, v in mm.items():
            if k not in m or v[0] < m[k][0]:
                m[k] = v
    pad = props.limb_mask([heel, (heel[0], heel[1] + 0.5)], [span, span])
    for k, v in pad.items():
        if k not in m or v[0] < m[k][0]:
            m[k] = v
    for (x, y), val in m.items():
        if any((x + dx, y + dy) not in m for dx, dy in N4):
            put(g, x, y, BLACK)
        else:
            put(g, x, y, props.yellow_colour(x, y, val))


# Mason's wing.  On his sheet it is an 11x9 ball on the body's side, so this is a
# short stub that swells into a ball at the tip, shaded as a SPHERE about that
# tip.  Two things follow from that and both matter: it stays attached to the
# body whatever bearing it is thrown at (a free-floating ball reads as a
# detached limb), and a sphere looks the same whichever way the body is lying,
# so the wings need no re-lighting to keep reading as his wings at every angle.
WING_RADII = [3.2, 4.4, 5.0]
WING_CREASE = ((0, -2), (1, -1), (-1, 1), (0, 2))


def wing_arm(g, root, tip, flip=False, r=6.2):
    tx, ty = int(round(tip[0])), int(round(tip[1]))
    mid = ((root[0] + tx) / 2.0, (root[1] + ty) / 2.0)
    mask = props.limb_mask([root, mid, (tx, ty)], WING_RADII)
    inter = set()
    for (x, y) in mask:
        if any((x + dx, y + dy) not in mask for dx, dy in N4):
            put(g, x, y, BLACK)
        else:
            put(g, x, y, rig.band(rig.lum(x, y, tx + 0.5, ty + 0.5, r, r), rig.TH['wing']))
            inter.add((x, y))
    sx = -1 if flip else 1
    for (u, v) in WING_CREASE:
        if (tx + sx * u, ty + v) in inter:
            put(g, tx + sx * u, ty + v, CREAM_MID)
    return inter


def poly(g, pts, shade):
    """A separately outlined piece: closed polygon, Bresenham edge, flood fill."""
    rig.W, rig.H = W, H
    line, inter = rig.raster([(int(round(x)), int(round(y))) for (x, y) in pts])
    rig.W = rig.H = LOCAL
    for (x, y) in inter:
        col = shade(x, y)
        if col:
            put(g, x, y, col)
    for (x, y) in line:
        put(g, x, y, BLACK)
    return inter


# ------------------------------------------------------------- clean-up ------
def despeckle(g):
    """Drop rotation crumbs: opaque pixels with fewer than two opaque 4-neighbours."""
    for _ in range(2):
        drop = [(x, y) for y in range(H) for x in range(W)
                if opaque(g, x, y)
                and sum(opaque(g, x + dx, y + dy) for dx, dy in N4) < 2]
        for (x, y) in drop:
            g[y][x] = CLEAR


def fill_pinholes(g):
    """Close single transparent pixels surrounded by the body, which rotation opens up."""
    blk = hex2rgba(BLACK)
    for _ in range(2):
        add = []
        for y in range(H):
            for x in range(W):
                if opaque(g, x, y):
                    continue
                n = [get(g, x + dx, y + dy) for dx, dy in N4]
                if all(p[3] for p in n):
                    cands = [p for p in n if p[:3] != blk[:3]]
                    add.append((x, y, max(cands, key=cands.count) if cands else blk))
        for (x, y, c) in add:
            g[y][x] = c


def reoutline(g):
    """Every opaque pixel on the silhouette edge becomes the 1px black keyline."""
    blk = hex2rgba(BLACK)
    edge = [(x, y) for y in range(H) for x in range(W)
            if opaque(g, x, y) and any(not opaque(g, x + dx, y + dy) for dx, dy in N4)]
    for (x, y) in edge:
        g[y][x] = blk


# Where HIS body ended up on the frame that was finished last.  Recorded here
# because every measurement that matters -- is he centred, how high does he
# reach, where is his middle -- has to be of him and not of the dust and motion
# arcs drawn after him, which touch him and merge into the same blob.
LAST_FIGURE = None


def finish(g):
    global LAST_FIGURE
    despeckle(g)
    fill_pinholes(g)
    reoutline(g)
    LAST_FIGURE = bbox_of(g)


# ---------------------------------------------------------------- effects ----
def lines(g, segs, col=BLACK):
    for seg in segs:
        for i in range(len(seg) - 1):
            for p in rig.bres(int(seg[i][0]), int(seg[i][1]),
                              int(seg[i + 1][0]), int(seg[i + 1][1])):
                put(g, p[0], p[1], col)


def arc(g, cx, cy, r, a0, a1, col=WHITE, ry=None, thick=1):
    """A motion streak: the trail the body has just swept, outlined so it reads at 3x."""
    ry = r if ry is None else ry
    pts = []
    steps = max(8, int(abs(a1 - a0) * 1.6))
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((int(round(cx + r * math.cos(a))), int(round(cy + ry * math.sin(a)))))
    body = set()
    for i in range(len(pts) - 1):
        for p in rig.bres(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]):
            body.add(p)
            if thick > 1:
                body.add((p[0], p[1] + 1))
    for (x, y) in body:
        if not opaque(g, x, y):
            put(g, x, y, col)


def puff(g, cx, cy, r, col=WHITE, edge=CREAM_MID):
    """A round dust ball with a black rim -- the mat kicking up."""
    disc = {(cx + dx, cy + dy) for dx in range(-r - 1, r + 2) for dy in range(-r - 1, r + 2)
            if dx * dx + dy * dy <= r * r + r * 0.5}
    for (x, y) in disc:
        if any((x + dx, y + dy) not in disc for dx, dy in N4):
            put(g, x, y, BLACK)
        else:
            put(g, x, y, edge if (x - cx) + (y - cy) > r * 0.6 else col)


def speck(g, pts, col=CREAM_MID):
    for (x, y) in pts:
        put(g, x, y, col)


# ------------------------------------------------------------------ export ---
def bbox(g):
    xs = [x for y in range(H) for x in range(W) if g[y][x][3]]
    ys = [y for y in range(H) for x in range(W) if g[y][x][3]]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


def centroid(g, predicate=None):
    tx = ty = n = 0
    for y in range(H):
        for x in range(W):
            p = g[y][x]
            if p[3] and (predicate is None or predicate(p)):
                tx += x
                ty += y
                n += 1
    return (round(tx / n, 1), round(ty / n, 1)) if n else None
