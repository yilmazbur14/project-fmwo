"""Toolkit for Danny's sumo redesign (v2): palette, form shading, cast shadows and a canvas.

Borrows the shape and hand-edit helpers from art_source/josh_redesign/lib.py by import (that file is
not edited). Adds what a 176x144 muscular figure needs on top:

  * shade(): directional light on a part's own inflated volume (a blurred copy of its mask stands
    in for height), quantised to a ramp. The light is upper-left-front like the rest of the cast, so
    every muscle gets a lit side and a shadow side instead of pillow shading.
  * Canvas.stamp(): keylines the part (1px black, cross dilation) over whatever is below it, which
    is where the black separations between muscle groups come from, and can drop the part's cast
    shadow one ramp step onto what is already there.

Keys are one character per colour. Ramps run dark -> light.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'josh_redesign'))
import lib as jl  # noqa: E402  (poly, ellipse, rect, line, amap, shift, mirror, dump, patch, grid...)

poly, ellipse, rect, line, amap, dump, patch = jl.poly, jl.ellipse, jl.rect, jl.line, jl.amap, jl.dump, jl.patch
upscale, on_bg = jl.upscale, jl.on_bg

W, H = 176, 144
AXIS = 87.5          # mirror axis: x' = 175 - x
MIR = 175


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ------------------------------------------------------------------ PALETTE
# Danny's own colours are DawnBringer-32 (measured off danny.png and the approved sumo sheets);
# the in-between tones are added only where a ramp needed a step.
PAL = {
    'k': hx('000000'),                                    # keyline, pure black as measured
    # skin, dark -> light (DB32 45283C 663931 8F563B D9A066 EEC39A; B67A4B added; FADCB8 is Mason's)
    '1': hx('45283C'), '2': hx('663931'), '3': hx('8F563B'), '4': hx('B67A4B'),
    '5': hx('D9A066'), '6': hx('EEC39A'), '7': hx('FADCB8'),
    # knit, light-blue stripe family, dark -> light (CBDBFC is the beanie's own)
    'u': hx('5B6EE1'), 'v': hx('97ABEF'), 'w': hx('CBDBFC'), 'x': hx('F0F5FF'),
    # knit, blue stripe family, dark -> light (5B6EE1 3F3F74 222034 are the beanie's own)
    'U': hx('222034'), 'V': hx('3F3F74'), 'B': hx('5B6EE1'), 'X': hx('7D90F0'),
    # red collar scrap (AC3232 D95763 are the shirt's own)
    'm': hx('45283C'), 'M': hx('7A2430'), 'R': hx('AC3232'), 'r': hx('D95763'),
    # gold (FBF236 DF7126 are the chain's own)
    'g': hx('8A4B1F'), 'O': hx('DF7126'), 'o': hx('F0B432'), 'Y': hx('FBF236'), 'y': hx('FFFBC4'),
    # white: wraps, eye glint, sleep bubble
    'h': hx('8595B8'), 'H': hx('CBDBFC'), 'W': hx('FFFFFF'),
    # apron print sky tone
    's': hx('639BFF'),
}

SKIN = '1234567'
LIGHT_KNIT = 'uvwx'
DARK_KNIT = 'UVBX'
RED = 'mMRr'
GOLD = 'gOoYy'
WHITE = 'hHW'
NAVY = 'UVB'

# One step darker, for cast shadows. Keys not listed are left alone (keyline, glints).
DARKER = {}
for ramp in (SKIN, LIGHT_KNIT, DARK_KNIT, RED, GOLD, WHITE):
    for i in range(1, len(ramp)):
        DARKER[ramp[i]] = ramp[i - 1]
DARKER['s'] = 'B'


# ------------------------------------------------------------------ SHAPES
def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with radii r0 and r1, as a pixel set."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, r0, r0) | ellipse(x1, y1, r1, r1)


def mirror_pts(pts):
    return [(MIR - x, y) for (x, y) in pts]


def mirror_px(px):
    return {(MIR - x, y): k for (x, y), k in px.items()}


def mirror_set(s):
    return {(MIR - x, y) for (x, y) in s}


def smooth_poly(pts, iters=2):
    """Chaikin corner cutting on a closed polygon: keeps a traced outline flowing."""
    for _ in range(iters):
        out = []
        n = len(pts)
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            out.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1))
            out.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        pts = out
    return pts


def spoly(pts, iters=2):
    return poly(smooth_poly(pts, iters))


# ------------------------------------------------------------------ SHADING
LIGHT = (-0.45, -0.58, 0.68)


def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


def _blur(a, sigma):
    r = max(1, int(3 * sigma + 1))
    xs = np.arange(-r, r + 1, dtype=float)
    k = np.exp(-(xs ** 2) / (2 * sigma * sigma))
    k /= k.sum()
    a = np.pad(a, r)
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 0, a)
    a = np.apply_along_axis(lambda m: np.convolve(m, k, mode='same'), 1, a)
    return a[r:-r, r:-r]


def intensity(pixels, sigma=None, tilt=(0.0, 0.0), bulge=1.0, light=LIGHT, height=None):
    """Light falling on a part: {(x, y): I}, I roughly 0..1, 0.68 for a surface facing the viewer.

    sigma sets how round the form is (bigger = rounder, the curvature reaches further in); tilt
    leans the whole surface (negative y faces it up, towards the light); bulge scales the slope.
    height, if given, is a function (x, y) -> extra height added before the slope is taken, for
    forms that are not simple domes (a belly that bellies lowest, a slab of pec)."""
    pixels = set(pixels)
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    x0, y0 = min(xs), min(ys)
    area = len(pixels)
    if sigma is None:
        sigma = max(1.4, 0.40 * math.sqrt(area / math.pi))
    pad = int(3 * sigma) + 3
    w = max(xs) - x0 + 1 + 2 * pad
    h = max(ys) - y0 + 1 + 2 * pad
    m = np.zeros((h, w))
    for (x, y) in pixels:
        m[y - y0 + pad, x - x0 + pad] = 1.0
    hf = _blur(m, sigma)
    if height is not None:
        for (x, y) in pixels:
            hf[y - y0 + pad, x - x0 + pad] += height(x, y)
    gy, gx = np.gradient(hf)
    s = 6.0 * sigma * bulge
    L = _norm(light)
    out = {}
    for (x, y) in pixels:
        i, j = y - y0 + pad, x - x0 + pad
        n = _norm((-gx[i, j] * s + tilt[0], -gy[i, j] * s + tilt[1], 1.0))
        out[(x, y)] = n[0] * L[0] + n[1] * L[1] + n[2] * L[2]
    return out


def quantise(inten, ramp, cuts):
    """cuts: ascending thresholds, one fewer than the ramp. I below cuts[0] -> ramp[0]."""
    out = {}
    for p, v in inten.items():
        k = 0
        while k < len(cuts) and v >= cuts[k]:
            k += 1
        out[p] = ramp[k]
    return out


SKIN_CUTS = (0.08, 0.26, 0.46, 0.64, 0.84, 0.95)

# Target share of each skin tone on a part in open light, dark -> light (1..7). A muscle in this
# light is mostly base, with a lit band upper-left, a small highlight, and its shadow on the
# lower-right edge; the deepest tone is kept for crevices and cast shadows.
SKIN_DIST = (0.0, 0.03, 0.10, 0.17, 0.40, 0.24, 0.06)


def quantise_pct(inten, ramp, dist, exposure=0.0):
    """Assign ramp keys by rank: the darkest dist[0] of the part's pixels get ramp[0], and so on.
    exposure > 0 pushes the whole part lighter, < 0 darker (a fraction of the part moved per step)."""
    items = sorted(inten.items(), key=lambda t: (t[1], t[0][1], t[0][0]))
    n = len(items)
    cum = []
    acc = 0.0
    for d in dist:
        acc += d
        cum.append(acc)
    total = cum[-1]
    cum = [c / total for c in cum]
    out = {}
    for i, (p, v) in enumerate(items):
        f = (i + 0.5) / n + exposure
        k = 0
        while k < len(cum) - 1 and f > cum[k]:
            k += 1
        out[p] = ramp[k]
    return out


def bumps(specs):
    """A height function: a sum of elliptical muscle bellies (cx, cy, rx, ry, amp). Added to a
    part's inflated mask, they put anatomy inside one keylined shape: valleys between them shade
    darker, their crowns catch the light."""
    def f(x, y):
        h = 0.0
        for (cx, cy, rx, ry, a) in specs:
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 9:
                h += a * math.exp(-d)
        return h
    return f


def domes(specs):
    """A height function from muscle domes (cx, cy, rx, ry, amp, power). power 0.5 is a
    hemisphere (a hard-edged muscle that turns sharply at its border), 1 a paraboloid, 2 soft.
    Overlapping domes add, so the light flows over one continuous surface."""
    def f(x, y):
        h = 0.0
        for spec in specs:
            cx, cy, rx, ry, a = spec[:5]
            p = spec[5] if len(spec) > 5 else 1.0
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1.0:
                h += a * (1.0 - d) ** p
        return h
    return f


def plateau(mask, sigma, amp=1.0, w=W, h=H):
    """A full-canvas height layer: a muscle's own outline, blurred into a flat-topped plateau.
    Summed with others and fed to intensity(height=...), it sculpts muscles as slabs whose edges
    turn, rather than balloons."""
    a = np.zeros((h, w))
    for (x, y) in mask:
        if 0 <= x < w and 0 <= y < h:
            a[y, x] = 1.0
    return _blur(a, sigma) * amp


def height_fn(*layers):
    total = sum(layers)

    def f(x, y):
        if 0 <= y < total.shape[0] and 0 <= x < total.shape[1]:
            return float(total[y, x])
        return 0.0
    return f


# Skin cuts on light wrapped by SKIN_WRAP: the deepest tones only where a surface turns right away
# (and in cast shadows and crevices); a face to the viewer is base, a face to the light lit.
CUTS = (-0.1, 0.25, 0.52, 0.69, 0.84, 0.94)
SKIN_WRAP = 0.45


def sculpt(mask, layers=(), sigma=None, bulge=0.7, exposure=0.0, cuts=CUTS, ramp=SKIN, tilt=(0.0, 0.0)):
    """Shade one form whose muscles are plateaus of their own outlines: layers are
    (pixels, blur sigma, amplitude). The light flows over the whole form."""
    hgt = height_fn(*[plateau(p, s, a) for (p, s, a) in layers]) if layers else None
    if sigma is None:
        sigma = max(2.5, 0.3 * math.sqrt(len(mask) / math.pi))
    return shade(mask, ramp=ramp, sigma=sigma, bulge=bulge, exposure=exposure, height=hgt, cuts=cuts,
                 tilt=tilt, wrap=SKIN_WRAP)


def lower_edge(mask_):
    """The pixels just under a mask, per column: the line along its lower turning edge."""
    bottom = {}
    for (x, y) in mask_:
        bottom[x] = max(bottom.get(x, y), y)
    return sorted((x, y + 1) for x, y in bottom.items())


def upper_edge(mask_):
    top = {}
    for (x, y) in mask_:
        top[x] = min(top.get(x, y), y)
    return sorted((x, y - 1) for x, y in top.items())


def crease(px, pixels, key='k', only=None, fade=None):
    """Put a line on canvas pixels. fade: {pixel: key} overrides (a taper to dark skin)."""
    for q in pixels:
        if only is not None and px.get(q) not in only:
            continue
        px[q] = fade.get(q, key) if fade else key


def mirror_domes(specs):
    return [(MIR - s[0],) + tuple(s[1:]) for s in specs]


def taper_line(px, pts, key='k', taper_key=None, taper=0, width=None, only=None):
    """Draw an open line along a polyline onto canvas dict px. The last `taper` pixels use
    taper_key (a dark skin tone) instead of black, so the line fades into the form instead of
    stopping dead. width: optional {index: 2} to double the line (downwards) at those points."""
    path = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
        if path and seg[0] == path[-1]:
            seg = seg[1:]
        path.extend(seg)
    n = len(path)
    for i, q in enumerate(path):
        if only is not None and px.get(q) not in only:
            continue
        k = taper_key if (taper and taper_key and i >= n - taper) else key
        px[q] = k
        if width and i < width:
            q2 = (q[0], q[1] + 1)
            if only is None or px.get(q2) in only:
                px[q2] = key
    return path


def mirror_bumps(specs):
    return [(MIR - cx, cy, rx, ry, a) for (cx, cy, rx, ry, a) in specs]


def rank(pixels, dist, exposure=0.0, wrap=0.3, **kw):
    """Tone index per pixel (0 = darkest) by the same ranking shade() uses, for parts drawn in a
    patterned material (knit stripes) where the index picks the tone inside each stripe's ramp."""
    kw.setdefault('bulge', 0.5)
    inten = intensity(pixels, **kw)
    inten = {p: (v + wrap) / (1 + wrap) for p, v in inten.items()}
    idx = quantise_pct(inten, list(range(len(dist))), dist, exposure)
    despeckle(idx)
    return idx


def knit(idx, pattern, stripe_of, ramps):
    """Stripe a ranked part: stripe_of(x, y) -> position along the knit, pattern[i] picks a ramp."""
    out = {}
    for (x, y), t in idx.items():
        fam = pattern[int(math.floor(stripe_of(x, y))) % len(pattern)]
        out[(x, y)] = ramps[fam][t]
    return out


def shade_pct(pixels, ramp=SKIN, dist=SKIN_DIST, exposure=0.0, wrap=0.3, clean=True, **kw):
    """Rank-based variant: every part gets the same ramp split whatever its shape."""
    kw.setdefault('bulge', 0.5)
    inten = intensity(pixels, **kw)
    inten = {p: (v + wrap) / (1 + wrap) for p, v in inten.items()}
    part = quantise_pct(inten, ramp, dist, exposure)
    if clean:
        despeckle(part)
    return part


# Thresholds on wrapped light for the skin ramp 1..7. A surface facing the viewer sits at 0.754, in
# the base tone, so a form reads flat-fronted with its turn into shadow at the edges: carved planes,
# not balloons.
SKIN_THR = (0.22, 0.43, 0.61, 0.715, 0.865, 0.952)


def shade(pixels, ramp=SKIN, cuts=SKIN_THR, exposure=0.0, wrap=0.3, clean=True, sigma=None, **kw):
    """Shade a part on its own volume: directional light from the upper left on an inflated copy
    of its mask. sigma defaults tight (0.6 of the part's natural radius) so muscle fronts stay
    planar; exposure > 0 lifts the whole part (it faces the light), < 0 sinks it (it is in shade)."""
    kw.setdefault('bulge', 0.72)
    if sigma is None:
        sigma = max(2.5, 0.24 * math.sqrt(len(pixels) / math.pi))
    inten = intensity(pixels, sigma=sigma, **kw)
    inten = {p: (v + wrap) / (1 + wrap) + exposure for p, v in inten.items()}
    part = quantise(inten, ramp, cuts)
    if clean:
        despeckle(part)
    return part


def despeckle(part, passes=2):
    """Remove single-pixel islands of a tone: a pixel none of whose 4 neighbours in the part share
    its key takes the most common neighbouring key. Keeps band edges clean."""
    for _ in range(passes):
        changes = {}
        for (x, y), k in part.items():
            nb = [part.get(q) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))]
            nb = [n for n in nb if n is not None]
            if nb and k not in nb:
                best = max(sorted(set(nb)), key=nb.count)   # sorted: string hashing is per-process
                changes[(x, y)] = best
        part.update(changes)
    return part


def band(part, pixels, key, only=None):
    """Recolour the part's pixels inside `pixels` (a clip). `only` limits to those keys."""
    for p in pixels:
        if p in part and (only is None or part[p] in only):
            part[p] = key


def darken(part, pixels, steps=1, only=None):
    for p in pixels:
        if p in part and (only is None or part[p] in only):
            k = part[p]
            for _ in range(steps):
                k = DARKER.get(k, k)
            part[p] = k


def lighten(part, pixels, ramp=SKIN, steps=1):
    for p in pixels:
        if p in part and part[p] in ramp:
            i = ramp.index(part[p])
            part[p] = ramp[min(len(ramp) - 1, i + steps)]


def edge(pixels):
    """Pixels of a set with a 4-neighbour outside it."""
    s = set(pixels)
    return {(x, y) for (x, y) in s
            if any(q not in s for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))}


def grow(pixels, n=1):
    s = set(pixels)
    for _ in range(n):
        s = s | {(x + dx, y + dy) for (x, y) in s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    return s


def shrink(pixels, n=1):
    s = set(pixels)
    for _ in range(n):
        s = s - edge(s)
    return s


def shift_set(s, dx, dy):
    return {(x + dx, y + dy) for (x, y) in s}


def clean_lone(px):
    """Fold into the line any pixel whose four neighbours are all keyline: a speck left where
    several stamped lines meet (an armpit, a wrap's corner) reads as dirt at 3x."""
    lone = [q for q, k in px.items() if k != 'k' and all(
        px.get(n) == 'k' for n in ((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1), (q[0], q[1] - 1)))]
    for q in lone:
        px[q] = 'k'
    return lone


# ------------------------------------------------------------------ CANVAS
class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}

    def inside(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, shadow=None, shadow_steps=1, line_key='k', under=0):
        """Stamp a part. With outline, a 1px keyline goes round it first, over anything below.
        shadow=(dx, dy) first darkens what is already on the canvas under the part's shifted
        silhouette (its cast shadow), one ramp step. under=n thickens the keyline by n px where
        it runs under the part onto something already drawn (an overhang's crevice); the outer
        silhouette stays 1px."""
        body = set(part)
        if shadow is not None:
            sh = shift_set(body, *shadow) - body
            for q in sh:
                k = self.px.get(q)
                if k is not None and k != 'k':
                    for _ in range(shadow_steps):
                        k = DARKER.get(k, k)
                    self.px[q] = k
        if outline:
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body and self.inside(q):
                        self.px[q] = line_key
            for (x, y) in body:
                if (x, y + 1) in body:
                    continue
                for d in range(2, under + 2):
                    q = (x, y + d)
                    if q in body or not self.inside(q):
                        break
                    below = (x, y + d + 1)
                    if q in self.px and below in self.px:
                        self.px[q] = line_key
        for q, k in part.items():
            if self.inside(q):
                self.px[q] = k

    def erase(self, pixels):
        for p in pixels:
            self.px.pop(p, None)

    def image(self):
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        put = im.load()
        for (x, y), k in self.px.items():
            if self.inside((x, y)):
                put[x, y] = PAL[k]
        return im


# ------------------------------------------------------------------ MEASURING / PREVIEW
def stats(im):
    f = getattr(im, 'get_flattened_data', None)
    px = [c for c in (f() if f else im.getdata()) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': round(100.0 * black / max(1, len(px)), 1)}


BG = (46, 49, 58, 255)


def grid(im, s, major=10):
    return jl.grid(im, s, major=major)


def view(im, s, path, bg=BG):
    upscale(on_bg(im, bg), s).save(path)
