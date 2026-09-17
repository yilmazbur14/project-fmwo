"""Procedural FX drawn straight into rig.canvas (mirrored pairs optional)."""
import math
import rig
from rig import PALC, W, H

def _put(x, y, ch, mirror=False):
    if mirror:
        x = 95 - x
    if 0 <= x < W and 0 <= y < H:
        rig.canvas[y][x] = PALC[ch]

def cloud(circles, pair=True, light=('5', '6', '7'), rim='8'):
    """union of circles, shaded top-left light, rim outline."""
    def draw():
        m = {}
        for y in range(H):
            for x in range(W):
                best = None
                for cx, cy, r in circles:
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d <= r:
                        k = (x + 0.5 - cx) / r * -0.55 + (y + 0.5 - cy) / r * -0.8
                        if best is None or k > best:
                            best = k
                if best is not None:
                    m[(x, y)] = best
        for (x, y), k in m.items():
            edge = any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            ch = rim if edge else (light[0] if k > 0.25 else (light[1] if k > -0.35 else light[2]))
            for mir in ((False, True) if pair else (False,)):
                _put(x, y, ch, mir)
    return draw

def burst(cx, cy, r, spikes=8, phase=0.0, pair=True, cols=('0', '1', '2', '3')):
    def draw():
        for y in range(H):
            for x in range(W):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                spike = 0.55 + 0.45 * abs(math.cos(a * spikes / 2 + phase)) ** 6
                rr = r * spike
                if d <= rr:
                    t = d / max(rr, 0.01)
                    ch = cols[0] if t < 0.35 else (cols[1] if t < 0.6 else (cols[2] if t < 0.85 else cols[3]))
                    for mir in ((False, True) if pair else (False,)):
                        _put(x, y, ch, mir)
    return draw

def pixels(pts, pair=True):
    """pts: list of (x, y, ch)"""
    def draw():
        for x, y, ch in pts:
            for mir in ((False, True) if pair else (False,)):
                _put(x, y, ch, mir)
    return draw

def lines(segs, ch, pair=True):
    """segs: (x0,y0,x1,y1) 1px lines"""
    def draw():
        for x0, y0, x1, y1 in segs:
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for i in range(n):
                t = i / max(n - 1, 1)
                x = round(x0 + (x1 - x0) * t); y = round(y0 + (y1 - y0) * t)
                for mir in ((False, True) if pair else (False,)):
                    _put(x, y, ch, mir)
    return draw

def plume(x0, y0, height, w0, phase=0.0, amp=2.0, pair=False, cols=('7', '8', '9'), top='6', gaps=True):
    """wavy tapered smoke column rising from (x0, y0), soft (no black) edges."""
    def draw():
        pts = {}
        for i in range(int(height)):
            y = y0 - i
            t = i / height
            wdt = max(1.0, w0 * (1 - 0.55 * t) + 0.8 * math.sin(t * 9 + phase))
            cx = x0 + amp * math.sin(t * 5.5 + phase)
            if gaps and t > 0.7 and (i % 3 == 0):
                continue
            for x in range(int(cx - wdt / 2 - 1), int(cx + wdt / 2 + 2)):
                u = (x + 0.5 - cx) / (wdt / 2)
                if abs(u) <= 1.0:
                    if abs(u) > 0.7:
                        ch = cols[2]
                    elif u < -0.1:
                        ch = top if t > 0.5 else cols[0]
                    else:
                        ch = cols[1]
                    pts[(x, y)] = ch
        for (x, y), ch in pts.items():
            for mir in ((False, True) if pair else (False,)):
                _put(x, y, ch, mir)
    return draw

import build as _B

def cloud2(circles, pair=False, ramp=('5', '6', '7', '8', '9'), rim='9', R=4.0):
    """union of circles shaded as ONE volume (height field), rim outline."""
    def draw():
        m = [[False] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                for cx, cy, r in circles:
                    if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                        m[y][x] = True
                        break
        idx = _B.shade_part(m, R, [9, 0.95, 0.8, 0.6, 0.4], 0.35)
        for y in range(H):
            for x in range(W):
                if not m[y][x]:
                    continue
                edge = any(not (0 <= x + dx < W and 0 <= y + dy < H) or not m[y + dy][x + dx]
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                ch = rim if edge else ramp[max(0, min(len(ramp) - 1, idx[y][x] - 1))]
                for mir in ((False, True) if pair else (False,)):
                    _put(x, y, ch, mir)
    return draw
