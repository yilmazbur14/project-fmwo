"""Stances for the rig: legs by two-bone IK, paws planted on the ground line, the body dropped as one.

stance(drop, ...) returns pose fields (torso, heads, necks, legs, tail) for a body `drop` px lower
than the hover, with the paws where you put them. Planted paws sit on GROUND (y 151, the feet anchor).
"""
import math

import rig_body as RB

GROUND = 151
# bone lengths of the approved hover leg (rig_body.FRONT / HIND)
F_L1 = math.hypot(128 - 123, 119 - 108)          # arm_top -> elbow
F_L2 = math.hypot(124 - 128, 137 - 119)          # elbow -> wrist
H_L1 = math.hypot(152 - 136, 128 - 110)          # hip -> hock
H_L2 = math.hypot(152 - 152, 139 - 128)          # hock -> ankle


def ik(root, tip, l1, l2, bend):
    """Joint between root and tip for bones l1, l2, bending toward +x when bend > 0 (screen)."""
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    d = math.hypot(dx, dy)
    d = max(abs(l1 - l2) + 0.01, min(l1 + l2 - 0.01, d))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1)
    mx, my = root[0] + ux * a, root[1] + uy * a
    # the two solutions sit either side of the root-tip line; pick the one toward bend
    p1 = (mx - uy * h, my + ux * h)
    p2 = (mx + uy * h, my - ux * h)
    return p1 if (p1[0] - p2[0]) * bend > 0 else p2


def front_joints(shoulder, paw, bend=1, planted=True):
    """Right front leg joints from the shoulder point and the paw centre."""
    sx, sy = shoulder
    A = (sx + 4, sy + 8)
    wrist = (paw[0] + 1, paw[1] - 6)
    E = ik(A, wrist, F_L1, F_L2, bend)
    ex, ey = E
    ux, uy = wrist[0] - ex, wrist[1] - ey
    n = math.hypot(ux, uy) or 1
    return dict(shoulder=(sx, sy), sh_end=(sx + 5, sy + 10), arm_top=A, elbow=E,
                fore_top=(ex + ux / n * 2.2, ey + uy / n * 2.2), wrist=wrist, paw=paw)


def hind_joints(hip, paw, bend=1):
    ankle = (paw[0] - 1, paw[1] - 5)
    K = ik(hip, ankle, H_L1, H_L2, bend)
    return dict(hip=hip, hock=K, ankle=ankle, paw=paw)


def planted_front(x):
    """A front paw centre whose claw stubs sit on the ground line."""
    return (x, GROUND - (len(RB.FRONT_PAW_PLANTED) - 1) - RB.FRONT_PAW_OFF[1])


def planted_hind(x):
    return (x, GROUND - (len(RB.HIND_PAW_PLANTED) - 1) - RB.HIND_PAW_OFF[1])


def stance(drop=0, front_x=123, hind_x=153, front_planted=True, hind_planted=True,
           front_paw=None, hind_paw=None, shoulder=(119, 100), hip=(136, 110), head_dy=None,
           side_dx=0, side_dy=None, mid_dx=0, front_bend=1, hind_bend=1):
    """Pose fields for a body `drop` px below the hover. Heads follow the body unless told otherwise."""
    sh = (shoulder[0], shoulder[1] + drop)
    hp = (hip[0], hip[1] + drop)
    fpaw = front_paw or (planted_front(front_x) if front_planted else (front_x, 143 + drop))
    hpaw = hind_paw or (planted_hind(hind_x) if hind_planted else (hind_x, 144 + drop))
    hdy = drop if head_dy is None else head_dy
    sdy = hdy if side_dy is None else side_dy
    planted = tuple(k for k, v in (('front', front_planted), ('hind', hind_planted)) if v)
    return dict(
        torso=(0, drop),
        front=front_joints(sh, fpaw, front_bend),
        hind=hind_joints(hp, hpaw, hind_bend),
        planted=planted,
        neck=((118, 98 + drop), (142 + side_dx, 82 + sdy)),
        mid=dict(dx=mid_dx, dy=hdy),
        side=dict(dx=side_dx, dy=sdy),
    )
