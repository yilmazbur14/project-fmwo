"""Three-quarter views for the turn, remapped from the approved front body - and the heads they wear.

A flat horizontal squeeze (what the approved sheet did) only makes him thinner: the face stays front-on
and the chest stays centred. A body turning ~50 degrees reads by its asymmetry, which this reproduces
with the torso as an ellipse (half-width 17, depth 0.45 of that) turned on the spot:
  * the sternum slides b*sin(theta) ~ 6 px toward the way he faces;
  * the near half of the chest keeps its width, the far half folds to under half of it;
  * the arms, at the sides, come in toward the body by cos(theta).
Each row of the front body is remapped piecewise-linearly on those numbers (nearest pixel, so every
colour stays an approved one), then the silhouette is keyed again. The head is never remapped: each
view carries its own drawn head.

    front34(px, theta, facing)  -> key dict: a front body (no head) turned theta degrees toward screen
                                   left (facing -1) or right (+1); the heads are turnheads.py's
"""
import math

from lib import edge

AXC = 47.5
A, B = 17.0, 0.45 * 17.0          # the torso as an ellipse: half-width, half-depth


FAR_FOLD = 0.6       # how much of its width the far half of the chest keeps
FAR_ARM = 0.8        # the far arm tucks in a little further than the near one


def segments(theta, facing):
    """Breakpoints (source offset, target offset) from the axis, sorted by source, over [-31, 31].
    facing -1: he has turned toward screen LEFT (his left side, screen right, comes round to us);
    facing +1: toward screen RIGHT."""
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    st = B * s * facing                                  # the sternum
    near_arm = (31.0 - A) * c
    far_arm = (31.0 - A) * c * FAR_ARM
    if facing < 0:
        return [(-31.0, st - A * FAR_FOLD - far_arm), (-A, st - A * FAR_FOLD), (0.0, st),
                (A, st + A), (31.0, st + A + near_arm)]
    return [(-31.0, st - A - near_arm), (-A, st - A), (0.0, st),
            (A, st + A * FAR_FOLD), (31.0, st + A * FAR_FOLD + far_arm)]


def _inverse(segs, xt):
    """source offset for a target offset, or None outside"""
    for (s0, t0), (s1, t1) in zip(segs, segs[1:]):
        lo, hi = min(t0, t1), max(t0, t1)
        if lo - 0.5 <= xt <= hi + 0.5 and t1 != t0:
            f = (xt - t0) / (t1 - t0)
            return s0 + (s1 - s0) * max(0.0, min(1.0, f))
    return None


def remap(px, segs, rows=range(0, 96)):
    """Remap every row of a key canvas horizontally (about x 47.5) by the piecewise map, nearest
    source pixel; the result's silhouette is keyed afresh."""
    out = {}
    by_row = {}
    for (x, y), k in px.items():
        by_row.setdefault(y, {})[x] = k
    for y, row in by_row.items():
        if y not in rows:
            for x, k in row.items():
                out[(x, y)] = k
            continue
        xs = sorted(row)
        # forward-scatter the row's extent so it keeps its full reach
        tmin = min(_fwd(segs, x + 0.5 - AXC) for x in xs)
        tmax = max(_fwd(segs, x + 0.5 - AXC) for x in xs)
        for xt in range(int(math.floor(AXC + tmin - 0.5)), int(math.ceil(AXC + tmax - 0.5)) + 1):
            src = _inverse(segs, xt + 0.5 - AXC)
            if src is None:
                continue
            sx = int(round(AXC + src - 0.5))
            if sx in row:
                out[(xt, y)] = row[sx]
    # key the silhouette: every opaque pixel on the outside edge goes black
    mask = set(out)
    for q in edge(mask):
        out[q] = 'k'
    return thin_keylines(out)


def thin_keylines(px):
    """Where the squeeze folded two interior keyline columns together (colour, k, k, colour), keep one
    line: the black nearer the lit side stays, the other takes its outer neighbour's colour."""
    out = dict(px)
    for (x, y), k in px.items():
        if k != 'k' or px.get((x + 1, y)) != 'k':
            continue
        a, b = px.get((x - 1, y)), px.get((x + 2, y))
        if a is None or b is None or a == 'k' or b == 'k':
            continue
        up, dn = px.get((x + 1, y - 1)), px.get((x + 1, y + 1))
        if up == 'k' and dn == 'k':
            continue                             # part of a longer vertical line: leave it
        out[(x + 1, y)] = b
    return out


def _fwd(segs, xs):
    for (s0, t0), (s1, t1) in zip(segs, segs[1:]):
        if s0 <= xs <= s1:
            return t0 + (t1 - t0) * (xs - s0) / (s1 - s0)
    return segs[0][1] if xs < segs[0][0] else segs[-1][1]


LEG_ROW = 79          # from the hem down the legs are two cylinders, not the torso's ellipse
LEG_SCALE = 0.8


def leg_segments(theta, facing):
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    st = B * s * facing * 0.5
    return [(-31.0, st - 31.0 * LEG_SCALE), (31.0, st + 31.0 * LEG_SCALE)]


def front34(px, theta, facing):
    """A front-view key canvas (no head) turned theta degrees toward screen left (facing -1) or right
    (facing +1): the torso on its ellipse down to the hem, the legs below on their own."""
    def leg(q):
        # the fists (rows 71-84, out at the sides) stay with the arms; the feet are all leg
        return q[1] >= LEG_ROW and (abs(q[0] + 0.5 - AXC) < 19.5 or q[1] >= 85)
    top = {q: k for q, k in px.items() if not leg(q)}
    low = {q: k for q, k in px.items() if leg(q)}
    out = remap(top, segments(theta, facing))
    out.update(remap(low, leg_segments(theta, facing)))
    return out
