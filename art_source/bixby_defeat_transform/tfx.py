"""Effects for transformation frames 10-25, in the same language as the shipped sequence (light beams,
the glowing floor disc, flame spikes licking off the silhouette, ember swirls, the implosion streaks, the
detonation disc, the rim glow and the smoke ring), drawn in the redesign's fire ramp. Layers are dicts
{(x, y): key-or-RGBA}; alpha is 0/255 only.

The beams keep the white core the recoloured frames 8 and 9 already use (bixby.png's white), so the
handover from the dog to the beast has no colour jump.
"""
import math

import common as C
from common import Rng
from pal import ellipse, line
import fx

WHITE = (255, 255, 255, 255)
BEAM = (WHITE, 'Y', 'P')
SMOKE = fx.SMOKE


def _cap(cx, cy, dx, dy, W, H, margin):
    cap = 1e9
    for lim, d in ((margin - cx, dx), (W - 1 - margin - cx, dx), (margin - cy, dy), (H - 1 - margin - cy, dy)):
        if d != 0:
            t = lim / d
            if t > 0:
                cap = min(cap, t)
    return cap


def rays(layer, cx, cy, n, r0, r1, phase=0.0, width=0.075, colours=BEAM, seed=3, jitter=0.30, margin=4,
         W=C.TW, H=C.TH):
    """Wedge-shaped light beams with white cores, capped so none reaches the frame edge."""
    R = Rng(seed)
    beams = []
    for k in range(n):
        a = phase + 2 * math.pi * k / n + (R() - 0.5) * 0.12
        length = r1 * (1.0 - jitter * R())
        cap = _cap(cx, cy, math.cos(a), math.sin(a), W, H, margin)
        beams.append((a, max(r0 + 6, min(length, cap)), width * (0.7 + 0.6 * R())))
    for y in range(max(0, int(cy - r1 - 4)), min(H, int(cy + r1 + 5))):
        for x in range(max(0, int(cx - r1 - 4)), min(W, int(cx + r1 + 5))):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r < r0 or r > r1 + 2:
                continue
            ang = math.atan2(dy, dx)
            for (a, L, w) in beams:
                if r > L:
                    continue
                d = abs((ang - a + math.pi) % (2 * math.pi) - math.pi)
                ww = w * (0.55 + 0.45 * min(1.0, (r - r0) / max(1.0, L - r0))) * \
                    (1.0 - 0.92 * max(0.0, (r - L * 0.62) / max(1.0, L * 0.38)))
                if ww <= 0.004 or d > ww:
                    continue
                f = d / ww
                layer[(x, y)] = colours[0] if f < 0.34 else (colours[1] if f < 0.68 else colours[2])
                break


def ground_disc(layer, cx, cy, rx, ry, level=1.0):
    """The glowing floor disc under him."""
    m = ellipse(cx, cy, rx, ry)
    inner = ellipse(cx, cy, rx * 0.72, ry * 0.72)
    core = ellipse(cx, cy, rx * 0.4, ry * 0.42)
    for p in m:
        layer[p] = 'r' if level < 0.5 else 's'
    for p in inner:
        layer[p] = 'u' if level < 0.6 else 'v'
    if level > 0.45:
        for p in core:
            layer[p] = 'v' if level < 0.8 else 'P'
    for p in C.inner_edge(m):
        layer[p] = 'r'


def top_edge(mask):
    cols = {}
    for (x, y) in mask:
        if x not in cols or y < cols[x]:
            cols[x] = y
    return cols


def rim_flames(layer, mask, t, height=7, seed=3, dense=2, colours=('P', 'v', 'u')):
    """Flame spikes licking up off the silhouette's upper edge, hot at the root."""
    cols = top_edge(mask)
    R = Rng(seed)
    for x in sorted(cols):
        if x % dense:
            continue
        h = height * (0.45 + 0.75 * R()) * (1.0 + 0.25 * math.sin(t * 1.7 + x * 0.4))
        if h < 1.5:
            continue
        y0 = cols[x]
        lean = math.sin(t * 0.9 + x * 0.25) * 1.2
        for k in range(int(h)):
            u = k / max(1.0, h)
            q = (int(round(x + lean * u * u)), int(round(y0 - 1 - k)))
            if q not in mask and q not in layer:
                layer[q] = colours[0] if u < 0.35 else (colours[1] if u < 0.7 else colours[2])
            q2 = (q[0] + 1, q[1])
            if u < 0.3 and q2 not in mask and q2 not in layer and R() < 0.35:
                layer[q2] = colours[1]


def crack_lines(layer, mask, seeds, level=3, seed=11, length=16, branch=True):
    """Glowing cracks running through a silhouette."""
    R = Rng(seed)
    hot = {1: ('r', 'u', 'u'), 2: ('u', 'v', 'P'), 3: ('v', 'P', 'Y')}[level]

    def walk(x, y, ang, steps):
        pts = [(x, y)]
        for _ in range(int(steps)):
            ang += (R() - 0.5) * 1.1
            x += math.cos(ang) * 2.2
            y += math.sin(ang) * 2.2
            if (int(x), int(y)) not in mask:
                break
            pts.append((x, y))
        return pts, ang

    for (sx, sy, a0) in seeds:
        pts, ang = walk(float(sx), float(sy), a0, length)
        px = []
        for a, b in zip(pts, pts[1:]):
            px += line(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1])))
        for k, q in enumerate(px):
            if q in mask:
                u = k / max(1, len(px) - 1)
                layer[q] = hot[2] if u < 0.3 else (hot[1] if u < 0.7 else hot[0])
        if branch and len(px) > 6 and R() < 0.8:
            bx, by = px[len(px) // 2]
            bp, _ = walk(float(bx), float(by), ang + (1.1 if R() < 0.5 else -1.1), length * 0.45)
            for a, b in zip(bp, bp[1:]):
                for q in line(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))):
                    if q in mask:
                        layer[q] = hot[1] if R() < 0.5 else hot[0]


def ember_swirl(layer, cx, cy, t, n=20, rx=54, ry=30, seed=9):
    """Embers spiralling up round him."""
    R = Rng(seed)
    for k in range(n):
        ph = R() * 6.28
        h = R()
        a = ph + t * 0.55 + h * 2.2
        r = rx * (0.45 + 0.55 * h)
        x = cx + math.cos(a) * r
        y = cy - h * ry * 2.0 + math.sin(a) * ry * 0.22
        fx.ember(layer, x, y, 1 if R() < 0.7 else 2, hot=R() < 0.45)


def burst(layer, box, n, seed, hot_ratio=0.7, sizes=(1, 2, 3)):
    fx.embers(layer, box, n, seed, hot_ratio, sizes)


def implode_streaks(layer, cx, cy, r0, r1, n=22, seed=5, colours=('Y', 'P', 'v')):
    """Light sucked inward: tapered streaks pointing at the core, hot at the inner end."""
    R = Rng(seed)
    for k in range(n):
        a = 2 * math.pi * k / n + R() * 0.3
        rr1 = r1 * (0.7 + 0.5 * R())
        rr0 = r0 * (0.8 + 0.4 * R())
        p0 = (cx + math.cos(a) * rr0, cy + math.sin(a) * rr0 * 0.92)
        p1 = (cx + math.cos(a) * rr1, cy + math.sin(a) * rr1 * 0.92)
        pts = line(int(round(p0[0])), int(round(p0[1])), int(round(p1[0])), int(round(p1[1])))
        for i, q in enumerate(pts):
            u = i / max(1, len(pts) - 1)
            layer[q] = colours[0] if u < 0.25 else (colours[1] if u < 0.6 else colours[2])


def flash_disc(layer, cx, cy, r, spikes=18, phase=0.0, core=0.55, ring_w=0.16, sq=0.90, margin=3,
               W=C.TW, H=C.TH):
    """The detonation: a white core, a pale-gold ring, amber rim, ember spikes and a thin white edge."""
    for k in range(spikes):
        a = phase + 2 * math.pi * k / spikes
        L = r * (1.12 + 0.26 * (((k * 5) % 3) / 2.0))
        dx, dy = math.cos(a), math.sin(a) * sq
        L = min(L, _cap(cx, cy, dx, dy, W, H, margin))
        w = r * 0.085
        px_, py_ = -math.sin(a), math.cos(a) * sq
        start = r * 0.8
        if L <= start + 2:
            continue
        for s_ in range(int(start), int(L)):
            u = (s_ - start) / max(1.0, L - start)
            ww = max(0.5, w * (1.0 - u))
            ax, ay = cx + dx * s_, cy + dy * s_
            for t in range(-int(ww), int(ww) + 1):
                layer[(int(round(ax + px_ * t)), int(round(ay + py_ * t)))] = 'v' if u > 0.45 else 'P'
    outer = ellipse(cx, cy, r, r * sq)
    mid = ellipse(cx, cy, r * (1 - ring_w), r * sq * (1 - ring_w))
    inner = ellipse(cx, cy, r * core, r * sq * core)
    for p in outer:
        layer[p] = 'P'
    for p in mid:
        layer[p] = 'Y'
    for p in inner:
        layer[p] = WHITE
    for p in C.inner_edge(outer):
        layer[p] = WHITE


def rim_glow(layer, mask, colour, outer):
    """A 1px glow hugging the silhouette outside its keyline, a dimmer halo one step further out."""
    e1 = C.outer_edge(mask)
    for p in e1:
        layer[p] = colour
    for p in C.outer_edge(mask | e1):
        layer[p] = outer
    return e1


def smoke_ring(layer, cx, cy, rx, ry, r=6.0, n=9, seed=13, keep_out=None, thin=0.0):
    """Clusters of smoke round him, in the defeat cloud's colours. keep_out skips clusters centred on him;
    thin (0..1) drops the small trailing puffs as the smoke clears."""
    R = Rng(seed)
    puffs = []
    for k in range(n):
        a = 2 * math.pi * k / n + R() * 0.4
        x = cx + math.cos(a) * rx
        y = cy + math.sin(a) * ry
        if keep_out is not None and (int(x), int(y)) in keep_out:
            continue
        rr = r * (0.7 + 0.5 * R())
        puffs.append((x, y, rr))
        # a smaller puff trailing outward on each side, gone as the smoke thins
        for side in (-1, 1):
            if R() >= thin:
                ox = math.cos(a) * rr * 0.9 + side * rr * 0.8
                oy = math.sin(a) * rr * 0.5 + R.range(-1, 2)
                puffs.append((x + ox, y + oy, rr * R.range(0.5, 0.7)))
    puffs.sort(key=lambda p: p[1])
    fx.puff_cloud(layer, puffs)


def mint_flare(layer, x, y, arm=5):
    """An eye igniting: a four-point mint star, white at the heart, longer across than up."""
    x, y = int(round(x)), int(round(y))
    layer[(x, y)] = WHITE
    for d in range(1, arm + 1):
        k = 'W' if d == 1 else 'j' if d <= arm // 2 + 1 else 'i'
        layer[(x + d, y)] = k
        layer[(x - d, y)] = k
        if d <= arm - 2:
            layer[(x, y + d)] = k
            layer[(x, y - d)] = k
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        layer[(x + dx, y + dy)] = 'j'


#SCALING (RotSprite-style: Scale2x three times, then nearest sampling; keeps the palette exactly)

def scale2x(px, w, h):
    out = [[None] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        row = px[y]
        upr = px[y - 1] if y > 0 else row
        dnr = px[y + 1] if y < h - 1 else row
        for x in range(w):
            P = row[x]
            A = upr[x]
            D = dnr[x]
            Cc = row[x - 1] if x > 0 else P
            B = row[x + 1] if x < w - 1 else P
            e0 = e1 = e2 = e3 = P
            if Cc == A and Cc != D and A != B:
                e0 = A
            if A == B and A != Cc and B != D:
                e1 = B
            if D == Cc and D != B and Cc != A:
                e2 = Cc
            if B == D and B != A and D != Cc:
                e3 = D
            out[2 * y][2 * x] = e0
            out[2 * y][2 * x + 1] = e1
            out[2 * y + 1][2 * x] = e2
            out[2 * y + 1][2 * x + 1] = e3
    return out, w * 2, h * 2


def resample(keys, w, h, f, pivot):
    """Scale a key dict (w x h canvas) by f about pivot; returns a new key dict on the same canvas."""
    if abs(f - 1.0) < 1e-9:
        return dict(keys)
    px = [[keys.get((x, y)) for x in range(w)] for y in range(h)]
    ww, hh = w, h
    for _ in range(3):
        px, ww, hh = scale2x(px, ww, hh)
    out = {}
    p0x, p0y = pivot
    for y in range(h):
        for x in range(w):
            sx = (x + 0.5 - p0x) / f + p0x
            sy = (y + 0.5 - p0y) / f + p0y
            ix, iy = int(math.floor(sx * 8)), int(math.floor(sy * 8))
            if 0 <= ix < ww and 0 <= iy < hh:
                k = px[iy][ix]
                if k is not None:
                    out[(x, y)] = k
    return out
