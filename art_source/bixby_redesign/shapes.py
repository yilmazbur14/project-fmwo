"""Shape helpers shared by every part: capsules, chains, symmetric halves, part recolouring."""
import math

from pal import AX, ellipse, line, poly


def capsule(p0, p1, r0, r1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, r0, r0) | ellipse(x1, y1, r1, r1)


def chain(pts, r0, r1):
    out = set()
    n = len(pts) - 1
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        out |= capsule(a, b, ra, rb)
    return out


def half(pts):
    """A symmetric polygon from its right half (top centre first, bottom centre last)."""
    left = [(2 * AX - x, y) for (x, y) in reversed(pts)]
    return pts + left


def spt(pts, dx, dy):
    return [(x + dx, y + dy) for (x, y) in pts]


def edge(part, dx, dy, depth=1):
    """Pixels of `part` within `depth` steps of its edge in direction (dx, dy)."""
    body = set(part)
    out = set()
    for (x, y) in body:
        for d in range(1, depth + 1):
            if (x + dx * d, y + dy * d) not in body:
                out.add((x, y))
                break
    return out


def recolor(part, pixels, key, only=None):
    for p in pixels:
        if p in part and (only is None or part[p] in only):
            part[p] = key


def below_line(pixels, p0, p1):
    """Pixels on or below the infinite line p0->p1 (larger y)."""
    (x0, y0), (x1, y1) = p0, p1
    out = set()
    for (x, y) in pixels:
        # y of the line at x
        if x1 == x0:
            continue
        ly = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        if y >= ly:
            out.add((x, y))
    return out


def poly_line(pts):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        out += line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    return out
