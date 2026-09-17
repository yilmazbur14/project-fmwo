"""card_bomb.png - 12 frames of 32x32.

  0-3   fall  : the card tumbling down, loops while it is airborne
  4     land  : it slaps flat on the mat, small dust
  5-7   tick  : looping arm cycle, a red glow ramping up under the card
  8-11  boom  : gold-and-red burst with card shrapnel

Everything is drawn around a fixed ground line so the card does not appear to hop between the
fall, the tick and the blast.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *
from cardlib import draw_card, flat_card, card_glow, _outline_cells

FW = FH = 32
GROUND = 23              # the row the landed card's centre sits on
CX = 16.0

FALL = [(-18, 1.00, 5.0), (26, 0.52, 3.0), (72, 0.14, 1.0), (118, 0.62, -1.0)]


def frame_fall(i):
    c = Cv(FW, FH)
    ang, sq, dy = FALL[i]
    draw_card(c, CX, GROUND - 4 + dy, 5.5, 8.0, ang, squash=sq, glow=0.55)
    return c


def frame_land():
    import giant
    c = Cv(FW, FH)
    # dust squirting out both sides as it slaps down - same rounded lobes as the giant slam
    lobes = []
    for side in (-1, 1):
        for k, (dx, dy, r) in enumerate(((7.5, 1.0, 3.0), (11.0, -0.5, 2.2), (14.0, 0.5, 1.5))):
            lobes.append((CX + side * dx, GROUND + dy, r))
    giant.puff_cloud(c, lobes)
    outline(c)
    flat_card(c, CX, GROUND, 9.0, 5.0)
    return c


def frame_tick(i):
    """3 looping frames: the glow under the card ramps, the card lifts a hair, sparks pop."""
    c = Cv(FW, FH)
    lvl = (0.32, 0.66, 1.00)[i]
    lift = (0.0, 0.0, -1.0)[i]
    # Red danger bloom hugging the CARD'S FOOTPRINT, not a disc centred on it - a radial falloff
    # from the centre puts all its brightness under the card, where nothing can see it.
    ramp = ['L', 'q', 'Q', 'R', 'E']
    reach = 5.0 + lvl * 6.0
    for y in range(FH):
        for x in range(FW):
            if c.p[y][x] != '.':
                continue
            du = max(0.0, abs(x + 0.5 - CX) - 9.5)
            dv = max(0.0, abs(y + 0.5 - (GROUND + 1)) - 5.0) * 1.55
            d = math.hypot(du, dv)
            val = (0.55 + lvl * 0.68) * max(0.0, 1.0 - d / reach) ** 0.80
            if (x * 7 + y * 13) % 5 == 0:
                val *= 0.74
            k = int(val * len(ramp))
            if k > 0:
                c.p[y][x] = ramp[min(k - 1, len(ramp) - 1)]
    flat_card(c, CX, GROUND + lift, 9.0, 5.0,
              rim='E' if lvl > 0.9 else 'D', pip='E' if lvl > 0.6 else 'R')
    # sparks spitting off the top edge as the fuse runs out
    if lvl > 0.5:
        for k in range(int(lvl * 6)):
            a = hashf(k, i, 3)
            px = int(CX + (a - 0.5) * 17)
            py = int(GROUND - 5 - a * 5 - lvl * 3)
            c.set(px, py, 'F' if a > 0.4 else 'E')
    return c


# --------------------------------------------------------------------------- boom
SHRAPNEL = [(-0.95, -0.30), (-0.62, -0.78), (-0.15, -1.00), (0.38, -0.92),
            (0.80, -0.58), (0.99, -0.06), (0.72, 0.42), (0.20, 0.62),
            (-0.40, 0.55), (-0.85, 0.22)]


RAMP_FIRE = ['q', 'Q', 'R', 'S', 'D', 'F', 'Y', 'w']


def frame_boom(i):
    """f8 white-hot flash, f9 full gold fireball, f10-f11 the shell blows out into a ring."""
    c = Cv(FW, FH)
    cy = 19.0                       # blast centre, kept high enough that rad 15 stays in frame
    # radius, hollow fraction, heat gain, shrapnel distance, shrapnel spin
    rad, hollow, gain, shard, spin = [(11.0, 0.00, 1.35, 10.5, 0.0),
                                      (13.0, 0.00, 1.00, 12.0, 40.0),
                                      (15.0, 0.50, 0.74, 12.5, 85.0),
                                      (15.5, 0.74, 0.48, 13.5, 130.0)][i]
    for y in range(FH):
        for x in range(FW):
            dx, dy = x + 0.5 - CX, (y + 0.5 - cy) * 1.12
            d = math.hypot(dx, dy)
            if d < 0.3:
                d = 0.3
            th = math.atan2(dy, dx)
            # a ragged star edge - a perfect circle reads as a ball, not a blast
            R = rad * (1.0 + 0.15 * math.sin(5 * th + i * 1.1) + 0.09 * math.sin(9 * th + 2.0))
            q = d / R
            if q > 1.0:
                continue
            if hollow > 0.0:
                heat = 1.0 - abs(q - 0.76) / 0.34      # a shell, hottest at the ring
                if q < hollow:
                    continue
            else:
                heat = (1.0 - q) ** 0.62               # a filled fireball
            heat = heat * gain + (hashf(x, y, 7 + i * 31) - 0.5) * 0.16
            k = int(max(0.0, min(0.999, heat)) * len(RAMP_FIRE))
            if k <= 0:
                continue
            c.p[y][x] = RAMP_FIRE[min(k, len(RAMP_FIRE) - 1)]
    # card shrapnel: real little cards, tumbling outward
    for k, (ux, uy) in enumerate(SHRAPNEL):
        if i == 0 and k % 3:
            continue                    # only a few chips are clear of the flash yet
        px = CX + ux * shard
        py = cy + uy * shard * 0.86
        if not (-3 < px < FW + 3 and -3 < py < FH + 3):
            continue
        sq = abs(math.cos(math.radians(spin + k * 47))) * 0.8 + 0.2
        sz = 2.9 - i * 0.28
        draw_card(c, px, py, sz * 0.70, sz, spin + k * 47, squash=sq, pip=None)
    # smoke wisps once the flash is gone
    if i >= 2:
        import giant
        lobes = []
        for k, (ax, ay, ar) in enumerate(((-0.72, 0.15, 1.5), (-0.26, -0.55, 2.2),
                                          (0.20, 0.10, 1.7), (0.66, -0.45, 2.4),
                                          (0.95, 0.35, 1.3))):
            lobes.append((CX + ax * 10.5, cy - 10 + ay * 4 - (i - 2) * 4, ar))
        giant.puff_cloud(c, lobes, ramp=('i', 'U', 'u', 'N'))
    return c


def build():
    fr = [frame_fall(i) for i in range(4)]
    fr.append(frame_land())
    fr += [frame_tick(i) for i in range(3)]
    fr += [frame_boom(i) for i in range(4)]
    return fr


# frame durations in ms and the tags a coder can rely on
DURATIONS = [70, 70, 70, 70, 90, 150, 150, 150, 50, 60, 70, 90]
TAGS = [('fall', 0, 3), ('land', 4, 4), ('tick', 5, 7), ('boom', 8, 11)]
