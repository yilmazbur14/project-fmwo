"""The card-hands' floor pieces.

  josh_hand_mark       64x40, pivot (32, 20): the slam's mark under the player. Its rim is EXACTLY the
                       footprint ellipse (the hit area, to the pixel) on every frame; only the shadow
                       inside changes: the hand's own flat shape, dithered in black (no semi-alpha),
                       denser and bigger the lower the hand comes.
                       0-1 hover flicker (0.10 each), 2 high, 3 mid, 4 low, 5 landed.
  josh_hand_impact_fx  160x96, pivot (80, 48): the slam on the floor round the footprint: a shock ring,
                       dust, and chips of card kicked out. 4 frames, floor layer, under the hand.
                       (Optional in the contract; without it the code uses card_burst.png.)
"""
import math
import random

import jh_lib as H
import jh_anims as A

MW, MH = 64, 40
MPX, MPY = 32, 20
IW, IH = 160, 96
IPX, IPY = 80, 48

FP = A.best_footprint()
RX, RY = FP['rx'], FP['ry']
MARK_TIMES = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
IMPACT_FX_TIMES = [0.05, 0.06, 0.07, 0.1]


def ellipse(cx, cy, rx=None, ry=None):
    return A.ellipse_px(rx or RX, ry or RY, cx, cy)


def rim_of(E):
    return {q for q in E if any((q[0] + dx, q[1] + dy) not in E for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def hand_shape(scale):
    """The flat hand's shape (the contact frame's silhouette), scaled about the pivot, relative to it."""
    sil = A.contact_silhouette()
    cx, cy = A.PX - 0.5, A.PY - 0.5
    out = set()
    for (x, y) in sil:
        out.add((int(math.floor((x - cx) * scale + 0.5)), int(math.floor((y - cy) * scale + 0.5))))
    # close the holes scaling left
    filled = set(out)
    for (x, y) in out:
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            q = (x + dx, y + dy)
            if q not in out:
                n = sum((q[0] + a, q[1] + b) in out for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if n >= 3:
                    filled.add(q)
    return filled


DITHER = {
    0.25: lambda x, y: (x % 2 == 0 and y % 2 == 0),
    0.5: lambda x, y: (x + y) % 2 == 0,
    0.75: lambda x, y: not (x % 2 == 1 and y % 2 == 1),
}


def mark_frames():
    cx, cy = MPX - 0.5, MPY - 0.5
    E = ellipse(cx, cy)
    R = rim_of(E)
    frames = []
    spec = [('R', 0.66, 0.5), ('T', 0.66, 0.5), ('R', 0.74, 0.5), ('R', 0.86, 0.5), ('T', 0.98, 0.75),
            ('T', 1.0, 0.75)]
    for i, (rim_k, sc, dens) in enumerate(spec):
        px = {}
        shape = hand_shape(sc)
        for (x, y) in shape:
            X, Y = MPX + x, MPY + y
            if (X, Y) in E and (X, Y) not in R and DITHER[dens](X, Y):
                px[(X, Y)] = 'k'
        for q in R:
            px[q] = rim_k
        # the flicker frame and the low / landed frames get a second, inner ring of darker red
        if i in (1, 4, 5):
            inner = rim_of(E - R)
            for q in inner:
                if q not in px or px[q] == 'k':
                    px[q] = 'V'
        if i == 1:
            rnd = random.Random(7)
            for q in rnd.sample(sorted(R), 6):
                px[q] = 'W'
        frames.append(px)
    return frames


def impact_frames():
    cx, cy = IPX - 0.5, IPY - 0.5
    E0 = ellipse(cx, cy)
    frames = []
    rnd = random.Random(11)
    puffs = [(2 * math.pi * k / 9 + rnd.uniform(-0.2, 0.2), rnd.uniform(0.95, 1.12)) for k in range(9)]
    chips = [(rnd.uniform(-2.6, -0.5), rnd.uniform(0.95, 1.2), rnd.choice(('0', 'y'))) for _ in range(6)]
    for i, (grow, ring_keys, dust_k, dust_r) in enumerate(((1.12, ('W', 'Y'), '0', 2.6), (1.3, ('Y', 'O'), '9', 3.2),
                                                           (1.46, ('O', 'o'), '8', 3.4), (1.58, ('G', None), '7', 2.4))):
        px = {}
        rx, ry = RX * grow, RY * grow
        for a_i in range(900):
            a = 2 * math.pi * a_i / 900.0
            if i >= 2 and (a_i // 30) % 3 == 2:
                continue
            for t, k in ((0.0, ring_keys[0]), (1.0, ring_keys[1])):
                if k is None:
                    continue
                x = int(round(cx + math.cos(a) * (rx - t)))
                y = int(round(cy + math.sin(a) * (ry - t * 0.7)))
                if (x, y) not in E0:
                    px[(x, y)] = k
        for (a, f) in puffs:
            ex = cx + math.cos(a) * RX * f * (1.0 + 0.14 * i)
            ey = cy + math.sin(a) * RY * f * (1.0 + 0.14 * i) - i * 1.5
            r = dust_r * (1.0 if i < 3 else 0.7)
            for yy in range(int(ey - r) - 1, int(ey + r) + 2):
                for xx in range(int(ex - r) - 1, int(ex + r) + 2):
                    d = math.hypot(xx - ex, (yy - ey) * 1.35)
                    if d <= r and (xx, yy) not in E0:
                        edge = d > r - 1.0
                        px[(xx, yy)] = ('8' if dust_k in '09' else '7') if edge else dust_k
        if i >= 1:
            for j, (a, f, side_k) in enumerate(chips):
                d = (RX + 8) * f * (0.55 + 0.3 * i)
                x = int(round(cx + math.cos(a) * d * (1 if j % 2 else -1)))
                y = int(round(cy + math.sin(a) * d * 0.55 - 5 + 3.0 * i))
                chip = {}
                for dx in range(3):
                    for dy in range(4):
                        chip[(x + dx, y + dy)] = side_k
                if side_k == 'y':
                    chip[(x + 1, y + 1)] = 'o'
                else:
                    chip[(x + 1, y + 1)] = 'R'
                for q, k in H.keyline(chip).items():
                    px[q] = k
        frames.append({q: k for q, k in px.items() if 0 <= q[0] < IW and 0 <= q[1] < IH})
    return frames
