"""Screen-space effects for the juggle frames, drawn in juggle-frame texels AFTER the body is turned, so
dust stays on the mat and streaks point the way he moves whatever angle he is at.

Built on the rig's own effects (rig_fx: dust, sweat, star4, star5, rays, pebbles, ground_flash,
ground_cracks, motion_arc) in the approved palette, plus the juggle's own: the uppercut's impact burst,
upward speed streaks, and the crash's flat dust wave. Solid things are keylined, light is not (the
rig's rule).
"""
import math

import numpy as np

import jcommon as C
import jrot
import rig_fx as FX
from pal import ellipse, fill
from shapes import edge, poly_line, recolor


class Canvas:
    """Frame-space effects canvas (no clipping until it is turned into an array)."""

    def __init__(self):
        self.px = {}
        self.w, self.h = C.W, C.H

    def stamp(self, part, outline=True, keep_line=False):
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body:
                        self.px[q] = 'k'
        for q, k in part.items():
            self.px[q] = k

    def put(self, pixels):
        self.px.update(pixels)

    def arr(self):
        return jrot.to_arr(self.px, C.W, C.H)


def apply(cv, *fxs):
    for f in fxs:
        f(cv, None)
    return cv


def impact(cx, cy, r=9, rays=10, ray_len=(14, 22), phase=0.0):
    """The uppercut landing: a keylined burst (white-hot core, gold, orange points) with light rays
    flying off it."""
    def f(cv, P):
        pts = []
        n = 8
        for i in range(2 * n):
            a = phase + math.pi * i / n
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.9))
        from pal import poly
        star = fill(poly(pts), 'P')
        core = ellipse(cx, cy, r * 0.42, r * 0.38)
        for q in core:
            if q in star:
                star[q] = 'Y'
        for q in ellipse(cx - 1, cy - 1, r * 0.2, r * 0.2):
            if q in star:
                star[q] = 'w'
        recolor(star, edge(star, 0, 1, 1) | edge(star, 1, 0, 1), 'p', only='P')
        cv.stamp(star)
        px = {}
        for i in range(rays):
            a = phase + 0.3 + 2 * math.pi * i / rays
            L0, L1 = ray_len if i % 2 == 0 else (ray_len[0] + 2, ray_len[1] - 4)
            seg = poly_line([(cx + math.cos(a) * L0, cy + math.sin(a) * L0 * 0.9),
                             (cx + math.cos(a) * L1, cy + math.sin(a) * L1 * 0.9)])
            for j, q in enumerate(seg):
                if q not in cv.px:
                    px[q] = 'Y' if j < len(seg) / 2 else 'P'
        cv.put(px)
    return f


def streaks(lines, key_tail='y', key_head='w'):
    """Vertical speed streaks: (x, y_top, y_bottom). The head (top) bright, the tail grey."""
    def f(cv, P):
        px = {}
        for x, y0, y1 in lines:
            n = max(1, y1 - y0)
            for y in range(y0, y1 + 1):
                if (x, y) not in cv.px:
                    px[(x, y)] = key_head if (y - y0) < n * 0.5 else key_tail
        cv.put(px)
    return f


def arc(cx, cy, rx, ry, a0, a1, key='w', thick=1):
    """A motion arc trailing a turn (degrees, screen, clockwise positive), drawn only on empty
    texels so it never paints over him."""
    def f(cv, P):
        px = {}
        steps = int(abs(math.radians(a1 - a0)) * max(rx, ry) * 1.5) + 2
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            for t in range(thick):
                q = (int(round(cx + math.cos(a) * (rx - t))), int(round(cy + math.sin(a) * (ry - t))))
                px[q] = key
        cv.put({q: k for q, k in px.items() if q not in cv.px})
    return f


def dust(x, size=2, drift=1, ground=None):
    return FX.dust(x, size, ground=C.FEET[1] if ground is None else ground, drift=drift)


def dust_at(x, y, size=2, drift=1):
    """A dust puff whose base sits on row y (for puffs thrown up off the mat)."""
    return FX.dust(x, size, ground=y, drift=drift)


def sweat(x, y, tilt=0):
    return FX.sweat(x, y, tilt)


def star(x, y, r=3):
    return FX.star4(x, y, r)


def pebbles(pts):
    return FX.pebbles(pts)


def flash(x, w=18, h=10, ground=None):
    return FX.ground_flash(x, ground=C.FEET[1] if ground is None else ground, w=w, h=h)


def cracks(x, spread=16, ground=None):
    return FX.ground_cracks(x, ground=C.FEET[1] if ground is None else ground, spread=spread)


def to_arr(fx_list):
    cv = Canvas()
    apply(cv, *fx_list)
    return cv.arr()


def over_where_empty(frame, fx_arr):
    """Effects that sit behind him: only where nothing is drawn yet."""
    out = frame.copy()
    m = (fx_arr > 0) & (out == 0)
    out[m] = fx_arr[m]
    return out


def over(frame, fx_arr):
    return jrot.over(frame, fx_arr)


def burst_lines(cx, cy, n=10, r0=40, r1=58, phase=0.0, key_near='w', key_far='y'):
    """Manga impact lines: thin strokes flying out from a hit, bright nearest it. Light, no keyline,
    drawn only on empty texels."""
    def f(cv, P):
        px = {}
        for i in range(n):
            a = phase + 2 * math.pi * i / n
            L1 = r1 if i % 2 == 0 else r1 - 8
            seg = poly_line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.85),
                             (cx + math.cos(a) * L1, cy + math.sin(a) * L1 * 0.85)])
            for j, q in enumerate(seg):
                if q not in cv.px:
                    px[q] = key_near if j < len(seg) * 0.5 else key_far
        cv.put(px)
    return f
