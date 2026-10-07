"""Fire helpers for the effect layers (no keyline, per the house rule for effects): a heat field
made of a downward body plus upward tongues, a smooth wobble so colour bands lick like flame, and
the heat-to-palette quantiser."""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FIRE = ('b', 'c', 'd', 'e', 'O', 'Y')


def fire_tail(cx, top, bottom, half_w, tongues, sway=3.0, period=9.0, core_bias=0.0):
    """A downward teardrop of fire from `top` to a point at `bottom` (swaying a little), hottest
    at its top, plus flame tongues licking UP from its top edge. tongues: (x, height, half_w,
    lean). Returns {pixel: heat}."""
    out = {}
    span = float(bottom - top)
    for y in range(top - 40, bottom + 1):
        for x in range(int(cx - half_w - 12), int(cx + half_w + 13)):
            best = -1.0
            if top <= y <= bottom and span > 0:
                t = (y - top) / span
                xc = cx + sway * math.sin((y - top) / period)
                w = half_w * (1.0 - t) ** 0.85
                if w > 0.4 and abs(x - xc) < w:
                    v = 1.0 - abs(x - xc) / w
                    best = max(best, v * 0.55 + (1.0 - t) * 0.55 + core_bias)
            for (tx, th, tw, lean) in tongues:
                u = (top + 3 - y) / th
                if u < 0 or u > 1:
                    continue
                xc = tx + lean * u * u
                half = tw * (1.0 - u) ** 0.8
                if half > 0.35 and abs(x - xc) < half:
                    v = 1.0 - abs(x - xc) / half
                    best = max(best, v * 0.5 + (1.0 - u) * 0.5)
            if best > 0:
                out[(x, y)] = best
    return out


def wobble(x, y, amp=0.10, seed=0.0):
    """Cheap smooth noise so the heat's iso-lines lick like flame instead of banding."""
    return amp * (math.sin(x * 0.83 + y * 0.31 + seed) + 0.8 * math.sin(x * 0.29 - y * 0.77 + 1.7 + seed)
                  + 0.6 * math.sin((x + y) * 0.53 + 2.9 + seed)) / 2.4


def colour_heat(field, ramp=FIRE, cuts=(0.12, 0.30, 0.48, 0.66, 0.84)):
    out = {}
    for p, heat in field.items():
        k = 0
        while k < len(cuts) and heat > cuts[k]:
            k += 1
        out[p] = ramp[k]
    return out
