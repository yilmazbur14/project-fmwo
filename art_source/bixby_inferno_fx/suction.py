"""bixby_suction.png: air rushing into Bixby's mouths during the inhale. 3 rows x 4 frames of 24x24 texels.

Each streak FLIES toward its head (the thick bright end) at the frame's centre line:
  row 0   0 degrees    flying right (head on the right)
  row 1  45 degrees    flying down and right (head at the bottom right)
  row 2  90 degrees    flying down (head at the bottom)
Godot angles (y down). The other five directions are flips: 180 = row 0 flip_h; 135 = row 1 flip_h;
315 = row 1 flip_v; 225 = row 1 flip_h + flip_v; 270 = row 2 flip_v. Every streak is centred on the frame's
centre (12, 12), so a flip keeps it in place.

Pale air in the redesign's bone ramp (w head, x body, y tail, z the tail's last dashes), the underside one
step darker so it holds up over the mat's light patches. Across the 4 frames (0.05 s each) the tail's dashes
and a mote flow toward the head, so the air reads as moving while the code carries the sprite along.
"""
import math

W, H = 24, 24

# The main streak along its axis, t = 0 at the frame centre, + toward the head. Per texel: key, and whether
# the underside (one row below at 0 degrees) is filled too.
HEAD = [(9, 'w', True), (8, 'w', True), (7, 'w', True), (6, 'w', True), (5, 'w', True), (4, 'x', True),
        (3, 'x', True), (2, 'x', True), (1, 'x', True), (0, 'x', True), (-1, 'x', False), (-2, 'y', False)]
# The underside, one step darker all along, ending in the tail's darkest grey: a one-sided edge that holds
# the streak up over the mat's light patches and the smoulder's dark ones alike.
UNDER = {9: 'x', 8: 'x', 7: 'y', 6: 'y', 5: 'y', 4: 'y', 3: 'z', 2: 'z', 1: 'z', 0: 'z'}


def main_line(f):
    """(t, key, thick) for one frame: the fixed head, then a tail of dashes flowing toward the head."""
    out = list(HEAD)
    period = 4
    for t in range(-11, -2):
        phase = (t - 2 * f) % period
        if phase in (0, 1):
            out.append((t, 'y' if t > -7 else 'z', False))
    return out


def side_line(f):
    """A thinner, shorter streak beside the main one, flowing too: (t, key) at perpendicular offset -4."""
    out = [(4, 'x'), (3, 'x'), (2, 'y')]
    for t in range(-6, 2):
        if (t - 2 * f) % 3 == 0:
            out.append((t, 'y' if t > -3 else 'z'))
    return out


def motes(f):
    """Two specks riding the air: (t, perpendicular offset, key)."""
    return [((-9 + 3 * f) % 16 - 8, 3, 'x'), ((-4 + 3 * f) % 16 - 8, -6, 'y')]


def frame_0deg(f):
    g = [['.'] * W for _ in range(H)]

    def put(t, s, k):
        x, y = 12 + t, 11 + s
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = k

    for t, k, thick in main_line(f):
        put(t, 0, k)
        if thick:
            put(t, 1, UNDER.get(t, 'y'))
    for t, k in side_line(f):
        put(t, -4, k)
    for t, s, k in motes(f):
        put(t, s, k)
    return g


def frame_90deg(f):
    """The 0-degree frame transposed: flying right becomes flying down."""
    g0 = frame_0deg(f)
    return [[g0[x][y] for x in range(W)] for y in range(H)]


def frame_45deg(f):
    """The same streak laid on the pixel diagonal. A step along the diagonal is sqrt(2) texels long, so
    the pattern is sampled every sqrt(2) along its axis to keep the streak's length on screen."""
    g = [['.'] * W for _ in range(H)]
    r2 = math.sqrt(2.0)

    def put(x, y, k):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = k

    main = {t: (k, th) for t, k, th in main_line(f)}
    side = dict(side_line(f))
    for i in range(-8, 8):
        t = int(round(i * r2))
        for tt in (t, t + 1):
            if tt in main:
                k, th = main[tt]
                put(12 + i, 12 + i, k)
                if th:
                    # a step along the diagonal is only one texel wide: the thick part takes the texel
                    # beside it too, with the darker underside below that
                    put(12 + i + 1, 12 + i, k)
                    put(12 + i - 1, 12 + i, UNDER.get(tt, 'y'))
                break
        for tt in (t, t + 1):
            if tt in side:
                # perpendicular offset -4 at 0 degrees is up; on the diagonal that is up-right
                put(12 + i + 3, 12 + i - 3, side[tt])
                break
    for t, s, k in motes(f):
        i = int(round(t / r2))
        o = int(round(s / r2))
        put(12 + i - o, 12 + i + o, k)
    return g


def frames():
    return [[frame_0deg(f) for f in range(4)], [frame_45deg(f) for f in range(4)], [frame_90deg(f) for f in range(4)]]
