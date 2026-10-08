"""Shared shape helpers for the demon-god rig: shaded tubes (limbs, bones, tail, fingers), a
Catmull-Rom smoother for curved paths, and a radius taper. Everything returns part dicts or
point lists; nothing is stamped or written here.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jg_base as B  # noqa: E402


def limb(pts, radii, ramp, light=B.LIGHT, cuts=None, bias=0.0, caps=True):
    """A shaded tube (arm, leg, finger, bone) along pts with per-point radii."""
    m = B.ribbon(pts, radii) if len(pts) > 2 else B.capsule(pts[0], pts[1], radii[0], radii[1])
    if caps:
        for p, r in zip(pts, radii):
            m |= B.ellipse(p[0], p[1], max(r, 0.6), max(r, 0.6))
    return B.tube_shade(pts, radii, ramp, light=light, cuts=cuts, bias=bias, mask=m)


def smooth_curve(pts, n=12):
    """Catmull-Rom through the points."""
    out = []
    P0 = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P0) - 2):
        p0, p1, p2, p3 = P0[i - 1], P0[i], P0[i + 1], P0[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def taper(n, r0, r1, power=1.0):
    return [r0 + (r1 - r0) * (i / max(1, n - 1)) ** power for i in range(n)]
