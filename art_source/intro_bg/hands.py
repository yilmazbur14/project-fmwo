"""Left hand built from capsules: palm/back of hand + four curled fingers pressing into the cheek.
Returns local-coordinate pixel dicts; right hand is produced by mirroring geometry (not lighting)."""
import math
from canvas import func_mask, boundary

VARIANTS = {}


def _capsule_off(ax, ay, bx, by):
    def fn(px_, py_):
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = max(0.0, min(1.0, ((px_ - ax) * vx + (py_ - ay) * vy) / L2))
        return (px_ - (ax + t * vx), py_ - (ay + t * vy))
    return fn


def capsule_mask(c):
    ax, ay, bx, by, r = c
    off = _capsule_off(ax, ay, bx, by)
    return func_mask(lambda a, b: sum(v * v for v in off(a, b)) <= r * r,
                     int(min(ax, bx) - r - 1), int(min(ay, by) - r - 1),
                     int(max(ax, bx) + r + 1), int(max(ay, by) + r + 1))


# Geometry for the viewer's-left hand (local sprite coords). Face lies to the right.
PALM_L = (36.0, 88.0, 38.5, 72.0, 6.2)
FINGERS_L = [
    # (ax, ay, bx, by, r) from knuckle toward the tip pressing the cheek; tips angle down
    (38.5, 68.4, 48.2, 71.6, 3.0),   # index
    (39.5, 73.9, 48.6, 76.9, 2.9),   # middle
    (39.5, 79.2, 47.0, 81.9, 2.8),   # ring
    (39.0, 84.2, 44.4, 86.2, 2.5),   # little
]


def mirror_c(c):
    ax, ay, bx, by, r = c
    return (131.0 - ax, ay, 131.0 - bx, by, r)
