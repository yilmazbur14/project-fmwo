"""burak_slash_trail.png: the cutlass's swing trails. 9 frames of 128x112 at 0.04 s, one strip:
  frames 0-2   SIDE SLASH: down from the raised blade, across his chest, round and down on his right
  frames 3-5   BACKHAND: down his right side from the raised blade, then, from the crouched lunge, low across the
               front of his legs just under his sash to behind him on the left
  frames 6-8   OVERHEAD: from over his hat, round the right of his head, down to the floor in front
Each swing (the approved look): f0 the blade's leading arc and a short tail, f1 the whole arc (the strike
frame), f2 the arc fading. Start a swing's three frames on the body's strike frame (burak_slash f1, f4, f7):
f0 and f1 span its 0.08 s, f2 the first 0.04 s of the follow-through.
THE PIVOT IS HIS FEET, (64, 111), the same frame and origin as burak_slash (128x112, feet on row 111,
centre column 64): as a centred Sprite2D the same offset as the body, (0, -56). Drawn facing RIGHT like the
body; flip_h with it. Draw it over the body: the drawn cutlass is masked out of every frame (f0 and f1 round
the strike frame's blade, f2 round the follow-through's), so the blade always shows on top of its trail.

Re-anchored to the body artist's blade data (art_source/burak_boss_anims/sheets.py SLASH, plus each frame's
bob and the 16,16 frame offset): each arc's outer edge is the blade tip's path through its wind-up, strike and
follow-through tips; f0's head is the strike frame's tip. Between those poses the path is designed: the
side cut passes in front of his chest, below his face; the backhand sweeps low in front of his legs; the
overhead goes over his hat.

Burak's steel, bright enough to read as a blade at speed: a #FFFCF4 leading edge, #DCE3EE and #A6AFC1 body,
#6D7589 at the tail, and a thin #D8434F inner edge (his coat) so the trail is his. No keyline, opaque.
"""
import json
import math
import os

import bfx_pal as pal

W, H = 128, 112
FEET = (64, 111)
FRAME_SIZE = (128, 112)
NOTE = ('9 frames of 128x112 at 0.04 s: side f0-2, backhand f3-5, overhead f6-8, each started on the body\'s '
        'strike frame; pivot = feet (64,111), offset (0,-56) like burak_slash')

# The body's blade per burak_slash frame, (hand, tip) in 128x112 texels, and the exact texels of its sword:
# bfx_slash_anchor.json, written by bfx_slash_anchor.py from the body artist's poses (re-run it if they change).
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bfx_slash_anchor.json'), encoding='utf-8') as _f:
    ANCHOR = json.load(_f)
BLADES = [(tuple(h), tuple(t)) for (h, t) in ANCHOR['blades']]

# Each swing: the tip's path as waypoints through its three blade tips (keys = the waypoint indices of the
# wind-up, strike and follow-through tips) and the crescent's greatest thickness (as approved).
SWINGS = [
    dict(path=[(20, 28), (37, 62), (58, 80), (82, 82), (105, 72), (111, 87), (104, 102)], keys=(0, 4, 6), thick=11.0),
    dict(path=[(104, 50), (109, 76), (106, 103), (82, 108), (56, 108), (30, 103), (8, 94)], keys=(0, 2, 6), thick=10.0),
    dict(path=[(30, 7), (54, 2), (85, 15), (106, 49), (105, 87), (100, 99), (94, 109)], keys=(0, 4, 6), thick=12.0),
]
LEAD = 0.40             # f0's arc: this share of the whole swing, ending at the strike frame's blade tip
def catmull_rom(pts, per=40):
    """A centripetal Catmull-Rom curve through pts; returns (samples, index of each waypoint in samples)."""
    ext = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + list(pts) + \
          [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    out, idx = [], []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]

        def tj(ti, a, b):
            return ti + max(1e-6, math.hypot(b[0] - a[0], b[1] - a[1])) ** 0.5
        t0 = 0.0
        t1 = tj(t0, p0, p1)
        t2 = tj(t1, p1, p2)
        t3 = tj(t2, p2, p3)
        idx.append(len(out))
        for k in range(per):
            t = t1 + (t2 - t1) * k / per
            a1 = [((t1 - t) * p0[j] + (t - t0) * p1[j]) / (t1 - t0) for j in (0, 1)]
            a2 = [((t2 - t) * p1[j] + (t - t1) * p2[j]) / (t2 - t1) for j in (0, 1)]
            a3 = [((t3 - t) * p2[j] + (t - t2) * p3[j]) / (t3 - t2) for j in (0, 1)]
            b1 = [((t2 - t) * a1[j] + (t - t0) * a2[j]) / (t2 - t0) for j in (0, 1)]
            b2 = [((t3 - t) * a2[j] + (t - t1) * a3[j]) / (t3 - t1) for j in (0, 1)]
            out.append(tuple(((t2 - t) * b1[j] + (t - t1) * b2[j]) / (t2 - t1) for j in (0, 1)))
    idx.append(len(out))
    out.append(tuple(pts[-1]))
    return out, idx


def swing_samples(s):
    """Swing s's tip path, densely sampled and evened out by arc length (260 steps like the approved arcs),
    each sample with its hand (between the three poses by arc length); plus the strike tip's sample index."""
    sw = SWINGS[s]
    pts, idx = catmull_rom(sw['path'])
    keys = [idx[k] for k in sw['keys']]
    hands = [BLADES[3 * s + j][0] for j in range(3)]
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    total = cum[-1]
    steps = 260
    out, j = [], 0
    for n in range(steps + 1):
        d = total * n / steps
        while j < len(pts) - 2 and cum[j + 1] < d:
            j += 1
        u = (d - cum[j]) / max(1e-9, cum[j + 1] - cum[j])
        p = (pts[j][0] + (pts[j + 1][0] - pts[j][0]) * u, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * u)
        seg = 0 if d <= cum[keys[1]] else 1
        a, b = cum[keys[seg]], cum[keys[seg + 1]]
        v = (d - a) / max(1e-9, b - a)
        h0, h1 = hands[seg], hands[seg + 1]
        out.append((p, (h0[0] + (h1[0] - h0[0]) * v, h0[1] + (h1[1] - h0[1]) * v)))
    return out, cum[keys[1]] / total


def blade_mask(frame_i):
    """The exact texels of the body's cutlass, knuckle-bow and fist on that burak_slash frame (from
    bfx_slash_anchor.json): kept out of the trail, so the blade always shows on top of its smear."""
    return {tuple(p) for p in ANCHOR['sword'][frame_i]}


def crescent(g, samples, head, tail, thick, fade):
    """The approved crescent: fill the band between the tip's path and a path pulled in along the blade toward
    the hand (the inside of the swing), thick at the head (the blade's position) and thin at the tail. head/tail are
    progress fractions along the swing."""
    n0, n1 = int(round(tail * (len(samples) - 1))), int(round(head * (len(samples) - 1)))
    steps = max(1, n1 - n0)
    for i in range(steps + 1):
        (ox, oy), (hx, hy) = samples[n0 + i]
        bl = math.hypot(hx - ox, hy - oy) or 1.0
        ux, uy = (hx - ox) / bl, (hy - oy) / bl          # in along the blade, toward the swing's centre
        w = thick * (i / steps) ** 1.4 * (0.55 if fade else 1.0)
        depth = 0.0
        while depth <= w:
            x = int(math.floor(ox + ux * depth))
            y = int(math.floor(oy + uy * depth))
            if 0 <= x < W and 0 <= y < H:
                rel = depth / max(1.0, w)
                if fade:
                    k = 's' if rel < 0.5 else 'i'
                    if (i // 9) % 3 == 2:
                        k = '.'
                elif rel < 0.2:
                    k = 'W'
                elif rel < 0.5:
                    k = 'S'
                elif rel < 0.85:
                    k = 's'
                else:
                    k = '2'
                if i < steps * 0.25 and k in 'WS':
                    k = 's' if not fade else k                   # the tail end cools
                if i < steps * 0.12 and k != '.':
                    k = 'i'
                if k != '.':
                    g[y][x] = k
            depth += 0.5


def frame(swing, f):
    g = pal.blank(W, H)
    sw = SWINGS[swing]
    samples, strike = swing_samples(swing)
    if f == 0:
        crescent(g, samples, strike, max(0.0, strike - LEAD), sw['thick'], False)
    elif f == 1:
        crescent(g, samples, 1.0, 0.0, sw['thick'], False)
    else:
        crescent(g, samples, 1.0, 0.35, sw['thick'], True)
    body_frame = 3 * swing + (2 if f == 2 else 1)          # the body frame this trail frame plays over
    for (x, y) in blade_mask(body_frame):
        g[y][x] = '.'
    return pal.rows(g)


def frames():
    return [frame(s, f) for s in range(3) for f in range(3)]
