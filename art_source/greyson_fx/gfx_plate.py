"""Greyson's thrown weight plate, its bounce off the ropes and its vanish. Three sheets:
  greyson_plate         6 frames of 24x16, looping at 0.04 s: an iron tri-grip plate skimming flat across the
                        arena, spinning (its three grip holes and hub turn 20 degrees a frame; three-fold, so 6
                        frames make the loop). Seen from above at the floor's tilt: its top face an ellipse,
                        its rim's edge showing under it. PIVOT: the plate's centre (12, 7). Never rotated;
                        spin is in the frames, so it reads the same flying any way.
  greyson_plate_bounce  4 frames of 32x32 at 0.04 s, once: the clang where it hits the ropes: a white-gold
                        flash and sparks thrown out round it. PIVOT: the centre (16, 16), on the contact point.
  greyson_plate_vanish  5 frames of 32x32 at 0.05 s, once: after its third bounce the plate flashes, bursts
                        into a puff of gym chalk and a glint, and is gone (the chalk thins in stepped alpha).
                        PIVOT: the centre (16, 16), where the plate was.
Iron and steel from his boot greys and Computah's (S s F i k K), gold sparks from his hair (Y y G), chalk
white (W w E e). The parry uses the shared parry flash; nothing is drawn for it here. No keyline.
"""
import math
import random

import gfx_pal as pal

PW, PH = 24, 16
PCX, PCY = 12.0, 7.0
RX, RY = 9.5, 5.2              # the plate's top face: 19 texels across, flattened by the floor's tilt
EDGE = 2                        # its rim's edge showing under the face
BW = BH = 32


def plate_frame(f):
    g = pal.blank(PW, PH)
    rot = math.radians(20 * f)
    # the rim's edge, showing below the face: a darker band
    for y in range(PH):
        for x in range(PW):
            px, py = x + 0.5 - PCX, y + 0.5 - PCY
            top = (px / RX) ** 2 + (py / RY) ** 2 <= 1.0
            low = (px / RX) ** 2 + ((py - EDGE) / RY) ** 2 <= 1.0
            if low and not top and py > -1:
                g[y][x] = 'i' if px < -RX * 0.35 else ('k' if px < RX * 0.5 else 'K')
    for y in range(PH):
        for x in range(PW):
            px, py = x + 0.5 - PCX, y + 0.5 - PCY
            d = math.hypot(px / RX, py / RY)
            if d > 1.0:
                continue
            u, v = px / RX, py / RY                    # the unflattened disc, radius 1
            lit = (-px * 0.6 - py) > 0
            if d > 0.84:
                k = ('S' if lit and d > 0.92 else 's') if lit else ('F' if d > 0.92 else 'i')    # the raised rim
            elif d > 0.72:
                k = 'k'                                 # the groove inside the rim
            else:
                k = 'F' if lit else 'i'                 # the face
            # three curved grip slots between the rim and the hub, turning with the spin: each spans 60
            # degrees of a ring, its far wall lit (the slot's inside faces the light), its near wall dark
            r = math.hypot(u, v)
            ang = math.atan2(v, u)
            for n in range(3):
                c = rot + n * 2 * math.pi / 3
                dang = abs((ang - c + math.pi) % (2 * math.pi) - math.pi)
                if 0.42 < r < 0.64 and dang < math.radians(30):
                    k = 'K' if r < 0.58 else 'k'
            # the hub: a raised steel collar round the bar hole
            if d < 0.3:
                k = 'K' if d < 0.13 else ('S' if (u + v) < -0.05 else ('s' if d < 0.24 else 'F'))
            g[y][x] = k
    # a glint that travels round the rim with the spin
    a = rot * 1.5
    gx, gy = int(PCX + RX * 0.9 * math.cos(a + 3.6)), int(PCY + RY * 0.9 * math.sin(a + 3.6))
    if 0 <= gx < PW and 0 <= gy < PH and g[gy][gx] in 'sSF':
        g[gy][gx] = 'W'
    return pal.rows(g)


def bounce_frame(f):
    g = pal.blank(BW, BH)
    cx, cy = 16.0, 16.0
    r = [3.5, 6.0, 8.0, 9.0][f]
    if f < 3:
        # the flash: a squat starburst, white-hot at the heart, gold at its edge
        for y in range(BH):
            for x in range(BW):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                a = math.atan2(dy, dx)
                spike = 1.0 + 0.55 * max(0.0, math.cos(4 * a)) ** 4
                d = math.hypot(dx, dy * 1.3) / (r * spike * (0.7 if f == 2 else 1.0))
                if d <= 1.0:
                    g[y][x] = 'W' if d < 0.45 else ('Y' if d < 0.75 else 'y')
    # sparks thrown out, falling a little, 2 texels long
    rnd = random.Random(4)
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.2, 0.2)
        dist = [4, 8, 12, 14][f] * rnd.uniform(0.8, 1.1)
        x = cx + math.cos(a) * dist
        y = cy + math.sin(a) * dist * 0.8 + [0, 0.5, 1.5, 3.0][f]
        for s in range(2 if f < 3 else 1):
            xx, yy = int(x - math.cos(a) * s), int(y - math.sin(a) * s * 0.8)
            k = ('Y' if s == 0 else 'G') if f < 3 else 'G'
            pal.put(g, xx, yy, k)
    # a steel clang ring on the second and third frames
    if f in (1, 2):
        rr = [0, 10.5, 13.0][f]
        for i in range(90):
            a = 2 * math.pi * i / 90
            pal.put(g, int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr * 0.75), 'S' if f == 1 else 's')
    return pal.rows(g)


def vanish_frame(f):
    g = pal.blank(BW, BH)
    cx, cy = 16.0, 16.0
    local = {}
    if f == 0:
        # the plate flashes white where it was
        for y in range(BH):
            for x in range(BW):
                d = math.hypot((x + 0.5 - cx) / RX, (y + 0.5 - cy) / RY)
                if d <= 1.0:
                    g[y][x] = 'W' if d < 0.7 else 'E'
        return pal.rows(g)
    # a puff of gym chalk, billowing out and thinning, with a glint over it
    rnd = random.Random(7)
    for i in range(7):
        a = 2 * math.pi * i / 7 + rnd.uniform(-0.3, 0.3)
        spread = [4, 7, 9, 10][f - 1]
        x = cx + math.cos(a) * spread
        y = cy + math.sin(a) * spread * 0.6 - (f - 1) * 1.2
        r = [3.5, 4.5, 5.0, 5.0][f - 1] * rnd.uniform(0.8, 1.15)
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                dx, dy = xx + 0.5 - x, yy + 0.5 - y
                d = math.hypot(dx, dy)
                if d > r or not (0 <= xx < BW and 0 <= yy < BH):
                    continue
                k = 'W' if math.hypot(dx + 0.35 * r, dy + 0.4 * r) < 0.5 * r else ('E' if dx + dy < 0.4 * r else 'e')
                g[yy][xx] = k
    if f >= 3:
        m, local = pal.alpha_keys('WEe', 176 if f == 3 else 96, 'lpt')
        for row in g:
            for x, k in enumerate(row):
                if k in m:
                    row[x] = m[k]
    if f in (1, 2):
        # the glint: a four-point star over the puff
        gx, gy = 19, 11
        for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, -2), (0, 2)):
            pal.put(g, gx + dx, gy + dy, 'W' if abs(dx) + abs(dy) < 2 else 'Y')
    return pal.Frame(pal.rows(g), local)


def plate_frames():
    return [plate_frame(f) for f in range(6)]


def bounce_frames():
    return [bounce_frame(f) for f in range(4)]


def vanish_frames():
    return [vanish_frame(f) for f in range(5)]


SHEETS = {'greyson_plate': (plate_frames, (PW, PH)), 'greyson_plate_bounce': (bounce_frames, (BW, BH)),
          'greyson_plate_vanish': (vanish_frames, (BW, BH))}
