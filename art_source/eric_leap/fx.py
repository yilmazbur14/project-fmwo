"""Procedural helpers for white smear / impact shapes (hand-tuned afterwards via .seg overlays)."""
import math
from lib import *


def arc_smear(g, cx, cy, a0, a1, r_out, r_in0, r_in1, ch='w', gaps=()):
    """Filled crescent between angle a0 (tail) and a1 (lead), degrees, CCW positive (screen y up).
    Inner radius goes r_in0 at the tail -> r_in1 at the lead. gaps: list of (r_lo, r_hi, a_until) cut-outs
    near the tail to break it into streaks."""
    for y in range(FS):
        for x in range(FS):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            r = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx))
            # unwrap into [a0, a0+360)
            while a < a0:
                a += 360
            while a >= a0 + 360:
                a -= 360
            if a > a1:
                continue
            t = (a - a0) / (a1 - a0)
            rin = r_in0 + (r_in1 - r_in0) * t
            if rin <= r <= r_out:
                cut = False
                for lo, hi, until in gaps:
                    if lo <= r <= hi and a <= until:
                        cut = True
                if not cut:
                    g[y][x] = ch


def disc(g, cx, cy, r, ch='w', only_empty=False):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if 0 <= x < FS and 0 <= y < FS and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                if not only_empty or g[y][x] == '.':
                    g[y][x] = ch


def smear2(g, cx, cy, a_lead, a_tail, r_out, r_in_lead, r_in_tail, gaps=(), empty_only=False, ch='w', r_out_tail=None):
    """Crescent smear from a_lead (thick) to a_tail (thin). Angles in degrees, CCW (screen y up), any order.
    gaps: (r_lo, r_hi, t_from, t_to) with t in [0,1] from lead to tail -> streak separations."""
    if r_out_tail is None:
        r_out_tail = r_out
    span = a_tail - a_lead
    for y in range(FS):
        for x in range(FS):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            r = math.hypot(dx, dy)
            if r > max(r_out, r_out_tail) + 1:
                continue
            a = math.degrees(math.atan2(dy, dx))
            # parameter t along the sweep
            d = a - a_lead
            if span > 0:
                d %= 360
            else:
                d = -((-d) % 360)
            t = d / span
            if not (0 <= t <= 1):
                continue
            rin = r_in_lead + (r_in_tail - r_in_lead) * t
            ro = r_out + (r_out_tail - r_out) * t
            if rin <= r <= ro:
                if any(lo <= r <= hi and t0 <= t <= t1 for lo, hi, t0, t1 in gaps):
                    continue
                if empty_only and g[y][x] != '.':
                    continue
                g[y][x] = ch
