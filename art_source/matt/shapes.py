"""Shape helpers on top of the shared toolkit: mirroring about column 48, capsules, curved tufts."""
import math

import pal  # noqa: F401
from pal import lib
from lib import ellipse, poly

AX = 96          # mirror: x' = 96 - x, so column 48 is the axis (the frame's anchor column)


def mx(x):
    return AX - x


def sym(half):
    """A left-half outline from top centre round to bottom centre -> the whole closed outline."""
    right = [(AX - x, y) for (x, y) in reversed(half) if x != AX / 2]
    return half + right


def mir_set(px):
    return {(AX - x, y) for (x, y) in px}


def mir_part(part):
    return {(AX - x, y): k for (x, y), k in part.items()}


def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with radii r0 and r1."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, r0, r0) | ellipse(x1, y1, r1, r1)


def bez(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0],
            u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def tuft(base, tip, w0, w1, bend=0.0, n=14, flat=0.55):
    """A curved, tapering clump of hair from `base` to `tip`: half-width w0 at the base, w1 at the
    tip, bowed sideways by `bend` px, with a blunt rounded end (`flat` squashes the end cap, so it
    reads as a tube's blunt end rather than a needle).
    Returns (pixels, axis) where axis maps each pixel to its 0..1 position along the tuft."""
    mxp = ((base[0] + tip[0]) / 2.0, (base[1] + tip[1]) / 2.0)
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    c = (mxp[0] + nx * bend, mxp[1] + ny * bend)
    left, right, spine = [], [], []
    for i in range(n + 1):
        t = i / float(n)
        p = bez(base, c, tip, t)
        q = bez(base, c, tip, min(1.0, t + 0.01)) if t < 1 else p
        pp = bez(base, c, tip, max(0.0, t - 0.01))
        tx, ty = q[0] - pp[0], q[1] - pp[1]
        tl = math.hypot(tx, ty) or 1.0
        ox, oy = -ty / tl, tx / tl
        w = w0 + (w1 - w0) * t
        left.append((p[0] + ox * w, p[1] + oy * w))
        right.append((p[0] - ox * w, p[1] - oy * w))
        spine.append(p)
    # blunt end cap: a squashed half-ellipse beyond the tip
    ex, ey = dx / ln, dy / ln
    cap = []
    for j in range(1, 8):
        a = math.pi * j / 8.0
        cx = math.cos(a)
        sx = math.sin(a)
        cap.append((tip[0] - nx * w1 * cx + ex * w1 * flat * sx,
                    tip[1] - ny * w1 * cx + ey * w1 * flat * sx))
    # outline: up the left edge, round the end cap, back down the right edge
    pts = left + _cap_order(cap, left[-1]) + list(reversed(right))
    px = poly(pts)
    axis = {}
    for p in px:
        axis[p] = frame_at(p, spine, n, w0, w1)[0]
    return px, axis


def frame_at(p, spine, n, w0, w1):
    """(t, s, nx, ny) for pixel p: t its 0..1 position along the spine, s its signed offset across
    it in half-widths (-1..1, positive on the side of the normal (nx, ny))."""
    best, bi = 1e9, 0
    for i, sp in enumerate(spine):
        d = (p[0] - sp[0]) ** 2 + (p[1] - sp[1]) ** 2
        if d < best:
            best, bi = d, i
    a = spine[max(0, bi - 1)]
    b = spine[min(len(spine) - 1, bi + 1)]
    tx, ty = b[0] - a[0], b[1] - a[1]
    tl = math.hypot(tx, ty) or 1.0
    tx, ty = tx / tl, ty / tl
    nx, ny = -ty, tx
    t = bi / float(n)
    w = w0 + (w1 - w0) * t
    sp = spine[bi]
    s = ((p[0] - sp[0]) * nx + (p[1] - sp[1]) * ny) / max(0.5, w)
    return t, s, nx, ny


def tuft_frames(base, tip, w0, w1, bend=0.0, n=14, flat=0.55):
    """tuft() plus, for every pixel, (t, s, nx, ny) from frame_at()."""
    px, _ = tuft(base, tip, w0, w1, bend, n, flat)
    mxp = ((base[0] + tip[0]) / 2.0, (base[1] + tip[1]) / 2.0)
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    c = (mxp[0] + nx * bend, mxp[1] + ny * bend)
    spine = [bez(base, c, tip, i / float(n)) for i in range(n + 1)]
    # extend the spine past the tip so the end cap's pixels read t = 1
    spine.append((tip[0] + dx / ln * w1, tip[1] + dy / ln * w1))
    frames = {p: frame_at(p, spine, n, w0, w1) for p in px}
    return px, frames


def _cap_order(cap, start):
    """Order the cap points so they continue from `start` (the last left-edge point)."""
    if (cap[0][0] - start[0]) ** 2 + (cap[0][1] - start[1]) ** 2 <= \
            (cap[-1][0] - start[0]) ** 2 + (cap[-1][1] - start[1]) ** 2:
        return cap
    return list(reversed(cap))
