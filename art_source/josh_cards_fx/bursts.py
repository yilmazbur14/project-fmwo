"""card_shatter.png     - a thrown card bursting when parried/blocked. 5 frames of 48x48.
   card_burst.png       - a planted card fanning out and snapping upward. 6 frames of 64x64.
   card_burst_rain.png  - the defeat variant: a deck raining down. 6 frames of 64x64.

The shatter is deliberately front-loaded: frame 0 is the brightest thing on screen, because it
is the reward for a parry and has to land on the exact frame of contact.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *
from cardlib import draw_card, flat_card, _outline_cells

# --------------------------------------------------------------------------- shatter
SHW = SHH = 48
SHC = 24.0

# 7 shards: direction, size scale.  Fewer and bigger, so each one still reads as a piece of
# card rather than as confetti.
SHARDS = [(-0.96, -0.28, 1.00), (-0.54, -0.84, 0.86), (0.08, -1.00, 0.94),
          (0.68, -0.73, 0.88), (1.00, -0.06, 0.96), (0.58, 0.62, 0.80),
          (-0.34, 0.80, 0.84)]


def star(c, cx, cy, arm, col='w', tip='F'):
    """A crisp 4-point spark - metal, not smoke."""
    for k in range(-arm, arm + 1):
        for (dx, dy) in ((k, 0), (0, k)):
            ch = col if abs(k) <= max(1, arm // 3) else tip
            c.set(int(cx) + dx, int(cy) + dy, ch)
    return c


def flash_rays(c, cx, cy, n, inner, outer, amp, phase=0.0):
    """Straight radiating spikes, white at the root and gold at the tip.  A soft disc bloom
    reads as smoke here; hard rays are what make a parry feel metallic."""
    ramp = ['A', 'D', 'F', 'Y', 'w']
    for k in range(n):
        a = phase + k * (math.tau / n)
        ca, sa = math.cos(a), math.sin(a)
        L = outer * (0.72 + 0.34 * ((k * 5) % 3) / 2.0)
        for s in range(int(inner), int(L)):
            t = (s - inner) / max(1.0, L - inner)
            half = max(0, int((1.0 - t) * 2.2))
            for w in range(-half, half + 1):
                x = int(round(cx + ca * s - sa * w))
                y = int(round(cy + sa * s + ca * w))
                if not c.inb(x, y):
                    continue
                v = amp * (1.0 - t) ** 0.8 * (1.0 - abs(w) / 3.2)
                k2 = int(v * len(ramp))
                if k2 > 0:
                    c.p[y][x] = ramp[min(k2 - 1, len(ramp) - 1)]
    return c


def shatter_frame(i):
    c = Cv(SHW, SHH)
    # core radius / ray amp / ray reach / shard travel / shard size / spark reach / sparks
    core, ramp_amp, reach, travel, size, sreach, nsp = [
        (9.0, 1.00, 24.0, 0.0, 1.00, 0.0, 0),
        (5.5, 1.00, 23.0, 14.0, 0.96, 17.0, 6),
        (3.0, 0.62, 18.0, 22.0, 0.84, 24.0, 5),
        (0.0, 0.26, 11.0, 29.0, 0.66, 29.0, 4),
        (0.0, 0.00, 0.0, 35.0, 0.48, 34.0, 2)][i]

    if ramp_amp > 0.01:
        flash_rays(c, SHC, SHC, 8, core * 0.8 + 1, reach, ramp_amp, phase=i * 0.19)
    # a hard white core, blazing on the contact frame
    if core > 0.5:
        for y in range(SHH):
            for x in range(SHW):
                d = math.hypot(x + 0.5 - SHC, y + 0.5 - SHC)
                if d <= core:
                    c.p[y][x] = 'w' if d < core * 0.62 else 'Y'

    # --- frame 0: the card still whole, split by a blinding seam ------------
    if i == 0:
        for side in (-1, 1):
            draw_card(c, SHC + side * 5.0, SHC, 3.6, 10.5, side * 4.0, pip=None)
        # the flash is re-struck OVER the halves: on the contact frame the burst has to be the
        # brightest thing in the sprite, not something peeking out from behind the card
        flash_rays(c, SHC, SHC, 8, 3, 24.0, 1.0, phase=0.39)
        for y in range(int(SHC) - 14, int(SHC) + 14):     # the seam blade
            for dx in (-1, 0, 1):
                c.set(int(SHC) + dx, y, 'w')
        for y in range(SHH):
            for x in range(SHW):
                d = math.hypot(x + 0.5 - SHC, y + 0.5 - SHC)
                if d <= 6.5:
                    c.p[y][x] = 'w' if d < 4.2 else 'Y'
    else:
        for k, (ux, uy, sz) in enumerate(SHARDS):
            px = SHC + ux * travel
            py = SHC + uy * travel * 0.94
            if not (-5 < px < SHW + 5 and -5 < py < SHH + 5):
                continue
            ang = 26.0 * k + travel * 5.5
            sq = abs(math.cos(math.radians(ang * 1.4))) * 0.62 + 0.38
            h = 7.4 * sz * size
            draw_card(c, px, py, h * 0.58, h, ang, squash=sq, pip=None)

    # --- gold sparks thrown clear -------------------------------------------
    for k in range(nsp):
        a = (k / float(max(1, nsp))) * math.tau + i * 0.42 + 0.3
        r = sreach * (0.78 + hashf(k, i, 9) * 0.35)
        px, py = SHC + math.cos(a) * r, SHC + math.sin(a) * r * 0.92
        if 2 < px < SHW - 2 and 2 < py < SHH - 2:
            star(c, px, py, 3 if i <= 2 else 2, 'w' if i <= 2 else 'F', 'F' if i <= 2 else 'D')
    return c


def build_shatter():
    return [shatter_frame(i) for i in range(5)]


SHATTER_DURATIONS = [40, 50, 60, 70, 80]
SHATTER_TAGS = [('shatter', 0, 4)]


# --------------------------------------------------------------------------- burst
BW, BH = 64, 64
BPX, BPY = 32.0, 48.0          # pivot: on the ground line, where the card is planted

# 10 cards evenly round a ring, each with a small phase offset so they do not move as one.
# The ring is drawn as a GROUND ELLIPSE (y squashed to 0.38), which is what makes it read as a
# fan opening across the mat instead of a row of cards in a line.
FAN = [(0, 0.06), (36, 0.16), (72, 0.02), (108, 0.13), (144, 0.08),
       (180, 0.18), (216, 0.04), (252, 0.15), (288, 0.10), (324, 0.00)]
RING_SQUASH = 0.38


def ground_glow(c, amp, rad=16.0):
    # no 'K' in this ramp: on the green mat the darkest gold reads as mud, not as light
    ramp = ['A', 'D', 'F', 'Y']
    for y in range(BH):
        for x in range(BW):
            if c.p[y][x] != '.':
                continue
            dx, dy = x + 0.5 - BPX, (y + 0.5 - BPY) * 2.4
            d = math.hypot(dx, dy)
            v = amp * max(0.0, 1.0 - d / rad) ** 1.1
            if hashf(x, y, 23) < 0.30:
                v *= 0.55
            k = int(v * len(ramp))
            if k > 0:
                c.p[y][x] = ramp[min(k - 1, len(ramp) - 1)]
    return c


def burst_frame(i):
    """f0 a planted card, f1-f3 the fan opening across the ground, f4-f5 it snaps upward."""
    c = Cv(BW, BH)
    # spread radius, lift, card size, glow
    spread, lift, sz, glow = [(0.0, 0.0, 1.00, 0.55),
                              (11.0, 1.0, 0.98, 0.90),
                              (20.0, 3.0, 0.92, 1.00),
                              (26.5, 9.0, 0.86, 0.80),
                              (29.0, 20.0, 0.78, 0.50),
                              (30.0, 33.0, 0.68, 0.25)][i]
    ground_glow(c, glow)

    if i == 0:
        # one card planted upright in the mat, glowing
        draw_card(c, BPX, BPY - 11.0, 6.0, 11.0, 0.0, glow=0.9)
        return c

    # back half of the ring first, so the near cards overlap the far ones
    placed = []
    for k, (a, ph) in enumerate(FAN):
        rad = math.radians(a)
        r = spread * (0.80 + ph)
        px = BPX + math.cos(rad) * r
        py = BPY + math.sin(rad) * r * RING_SQUASH - 7.0 - lift * (0.65 + ph * 1.8)
        if not (-6 < px < BW + 6 and -6 < py < BH + 6):
            continue
        placed.append((py, k, a, px, ph))
    placed.sort()
    for (py, k, a, px, ph) in placed:
        # each card leans away from the centre, and spins up as it rises
        ang = -math.degrees(math.atan2(math.cos(math.radians(a)), 2.2)) + lift * 2.6 + k * 4.0
        sq = abs(math.cos(math.radians(ang * 1.25))) * 0.62 + 0.38
        h = 10.0 * sz
        draw_card(c, px, py, h * 0.62, h, ang, squash=sq, pip=None,
                  glow=0.5 if i <= 3 else 0.3)
    # gold streaks shooting up on the snap
    if i >= 3:
        for k in range(4):
            sx = BPX + (hashf(k, 0, 3) - 0.5) * 30
            top = BPY - 12 - (i - 2) * 10 - hashf(k, 1, 7) * 8
            for y in range(int(top), int(BPY - 6)):
                if c.inb(int(sx), y) and c.p[y][int(sx)] == '.':
                    v = 1.0 - (y - top) / max(1.0, (BPY - 6 - top))
                    c.p[y][int(sx)] = ramp_pick(['A', 'D', 'F', 'Y'], v * 0.9)
    return c


def build_burst():
    return [burst_frame(i) for i in range(6)]


BURST_DURATIONS = [90, 70, 70, 70, 80, 90]
BURST_TAGS = [('burst', 0, 5)]


# --------------------------------------------------------------------------- rain
# 11 cards, each with a start x, a fall phase and a landing x offset
RAIN = [(-26, 0.00, -27), (-17, 0.28, -19), (-9, 0.55, -11), (-2, 0.14, -3),
        (5, 0.42, 6), (12, 0.06, 14), (19, 0.62, 21), (25, 0.34, 26),
        (-22, 0.72, -24), (2, 0.86, 1), (16, 0.92, 17)]


def rain_frame(i):
    """The defeat variant: his deck bursts up out of frame and rains back down, the cards
    landing flat on the mat around him."""
    c = Cv(BW, BH)
    ground_glow(c, (0.85, 0.55, 0.35, 0.20, 0.10, 0.05)[i], rad=20.0)
    prog = i / 5.0
    for k, (sx, ph, lx) in enumerate(RAIN):
        t = (prog - ph * 0.55) / 0.55            # this card's own 0..1 fall
        if t < 0.0:
            continue
        if t >= 1.0:
            # landed: a flat card lying on the mat
            py = BPY - 5 + (k * 7) % 6
            flat_card(c, BPX + lx, py, 6.2, 2.8, pip=None)
            continue
        px = BPX + sx + (lx - sx) * t
        py = -8.0 + (BPY - 4.0 + 8.0) * (t * t)   # accelerating fall
        ang = 40.0 * k + t * 300.0
        sq = abs(math.cos(math.radians(ang))) * 0.80 + 0.20
        draw_card(c, px, py, 4.4, 7.0, ang, squash=sq, pip=None, glow=0.45)
    return c


def build_rain():
    return [rain_frame(i) for i in range(6)]


RAIN_DURATIONS = [80, 80, 80, 90, 100, 120]
RAIN_TAGS = [('rain', 0, 5)]
