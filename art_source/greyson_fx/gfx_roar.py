"""Greyson's roar in the cutscene ("a gigantic roar that will shake the whole arena"). Two sheets:
  greyson_roar         6 frames of 176x128 at 0.06 s, once (loop f2-f5 to hold it): shout rings bursting out of
                       his mouth, thick and broken, three at a time, with force lines streaking out past them.
                       PIVOT: his mouth (88, 64). Never flipped.
  greyson_roar_screen  6 frames of 640x360 at 0.08 s, once: a screen-space layer at scale 3 (it fills 1920x1080),
                       drawn under the HUD. A shock ring rolls out across the whole mat from his feet at the top
                       of the arena (screen (960, 260)), raising a band of chalk dust as it goes, and dust shakes
                       off all four ropes. Pair it with a camera shake. PIVOT: top-left (0, 0).
Chalk and air whites (W w E e f), no keyline; the screen layer's dust thins in stepped alpha (176, 112).
"""
import math
import random

import gfx_pal as pal
import gfx_floor as fl

RW, RH = 176, 128
RCX, RCY = 88.0, 64.0
SW, SH = 640, 360
FEET = (320.0, 87.0)            # his feet at the top of the arena: screen (960, 260) px
ROPES = (31, 38, 609, 329)      # the rope art's box in texels: screen Rect2(92, 114, 1734, 874) px


def roar_frame(f):
    g = pal.blank(RW, RH)
    for n in range(3):
        age = f - n * 1.2
        if age < 0:
            continue
        r = 10 + age * 16
        if r > 84:
            continue
        thick = max(1, int(4 - age * 0.6))
        k = ['W', 'w', 'E', 'e'][min(3, int(age * 0.8))]
        count = int(2 * math.pi * r * 2)
        for i in range(count):
            a = 2 * math.pi * i / count
            if (a * 5 / math.pi + n * 0.7) % 2.0 > 1.55:
                continue                                   # broken into arcs
            for t in range(thick):
                x = int(RCX + (r + t) * math.cos(a))
                y = int(RCY + (r + t) * 0.7 * math.sin(a))
                if 0 <= x < RW and 0 <= y < RH:
                    g[y][x] = k
    # force lines streaking out past the rings
    rnd = random.Random(f)
    for i in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        r0 = 18 + f * 10 + rnd.uniform(0, 10)
        ln = rnd.uniform(6, 14)
        for s in range(int(ln)):
            x = int(RCX + (r0 + s) * math.cos(a))
            y = int(RCY + (r0 + s) * 0.7 * math.sin(a))
            if 0 <= x < RW and 0 <= y < RH and g[y][x] == '.':
                g[y][x] = 'E' if s < ln * 0.6 else 'e'
    return pal.rows(g)


def screen_frame(f):
    g = pal.blank(SW, SH)
    local = {}
    cx, cy = FEET
    rx = [40, 110, 190, 270, 350, 420][f]
    ry = rx * 0.36
    # the shock line on the mat, clipped to the ropes
    count = int(2 * math.pi * rx * 1.5)
    for i in range(count):
        a = 2 * math.pi * i / count
        x, y = int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a))
        if ROPES[0] < x < ROPES[2] and ROPES[1] < y < ROPES[3]:
            g[y][x] = 'W' if f < 3 else 'E'
            if y + 1 < SH:
                g[y + 1][x] = 'E' if f < 3 else 'e'
    # the band of dust it raises, puffs along the ring inside the ropes
    rnd = random.Random(5)
    for i in range(46):
        a = 2 * math.pi * i / 46 + rnd.uniform(-0.03, 0.03)
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a) - 3
        if ROPES[0] + 6 < x < ROPES[2] - 6 and ROPES[1] + 4 < y < ROPES[3] - 4:
            fl.puff(g, x, y, rnd.uniform(4, 7) * (1 + f * 0.1), shade=min(2, f // 2), squash=0.7)
    # dust shaking off the ropes, all four sides, from f1
    if f >= 1:
        for i in range(40):
            side = i % 4
            u = rnd.uniform(0.05, 0.95)
            if side == 0:
                x, y = ROPES[0] + (ROPES[2] - ROPES[0]) * u, ROPES[1] + 2
            elif side == 1:
                x, y = ROPES[0] + (ROPES[2] - ROPES[0]) * u, ROPES[3] - 2
            elif side == 2:
                x, y = ROPES[0] + 3, ROPES[1] + (ROPES[3] - ROPES[1]) * u
            else:
                x, y = ROPES[2] - 3, ROPES[1] + (ROPES[3] - ROPES[1]) * u
            fl.puff(g, x, y - f * 1.5, rnd.uniform(2.5, 4.5), shade=min(2, f // 2), squash=0.8)
    if f >= 3:
        m, local = pal.alpha_keys('WwEef', 176 if f < 5 else 112, 'ghjlp')
        for row in g:
            for x, k in enumerate(row):
                if k in m:
                    row[x] = m[k]
    return pal.Frame(pal.rows(g), local)


def roar_frames():
    return [roar_frame(f) for f in range(6)]


def screen_frames():
    return [screen_frame(f) for f in range(6)]


SHEETS = {'greyson_roar': (roar_frames, (RW, RH)), 'greyson_roar_screen': (screen_frames, (SW, SH))}
