"""Burak's charge aura: flames hugging his own silhouette, rising, three strengths (bars 1-2, 3-4, 5). Additive, drawn
BEHIND him. A 64x64 cell with his 48 cell at (8, 8), so drawn centred on MainPlayer's origin it sits on him exactly."""
import math
import numpy as np
from PIL import Image
from common import *
from energy import RAMPS, rgba, rng

TAU = math.tau
CELL = 64
PAD = 8


def _dist(mask):
    ys, xs = np.nonzero(mask)
    pts = np.stack([xs, ys], 1).astype(np.float32)
    gy, gx = np.mgrid[0:CELL, 0:CELL].astype(np.float32)
    d = np.full((CELL, CELL), 99.0, np.float32)
    for x, y in pts:
        d = np.minimum(d, np.hypot(gx - x, gy - y))
    return d


def aura_for(pose_img, take, t, level, frames=3):
    a = np.zeros((CELL, CELL), bool)
    a[PAD:PAD + 48, PAD:PAD + 48] = np.asarray(pose_img)[..., 3] > 0
    D = _dist(a)
    base = [1.6, 2.6, 3.6][level]
    shell = D <= base
    H = [5, 9, 14][level]
    r = rng(40 + level)
    seeds = r.uniform(0, TAU, CELL)
    out = np.zeros((CELL, CELL, 4), np.uint8)
    ramp = [c for _, c in RAMPS[take]]
    tongue_k = np.zeros((CELL, CELL), np.float32)
    for x in range(CELL):
        f = 0.5 + 0.5 * math.sin(seeds[x] + TAU * t / frames + x * 0.7)
        h = int(round(H * f ** 2))
        col = shell[:, x]
        for k in range(1, h + 1):
            up = np.zeros(CELL, bool)
            up[:-k] = col[k:]
            new = up & ~shell[:, x] & (tongue_k[:, x] == 0)
            tongue_k[new, x] = k / max(h, 1)
    tongue = tongue_k > 0
    layers = [
        (tongue & (tongue_k > 0.66), ramp[5], 0.40),
        (tongue & (tongue_k <= 0.66), ramp[4], 0.55),
        (shell & (D > 1.2), ramp[3], 0.65),
        (shell & (D <= 1.2), ramp[1], 0.80),
    ]
    for m, c, al in layers:
        cc = rgba(c)
        out[m & ~a] = (cc[0], cc[1], cc[2], int(255 * al))
    # sparks lifting off
    rr = rng(70 + level * 7 + t)
    for k in range(3 + 3 * level):
        x = int(rr.integers(10, 54))
        y = int(rr.integers(4, 30))
        if not a[y, x]:
            cc = rgba(ramp[rr.integers(0, 3)])
            out[y, x] = (cc[0], cc[1], cc[2], 230)
    return Image.fromarray(out, "RGBA")
