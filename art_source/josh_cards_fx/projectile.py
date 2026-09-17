"""card_projectile.png - the parryable thrown card.  4 frames of 24x24, a seamless spin loop.

Drawn travelling RIGHT: the gold trail streams off the left edge.  Flip the sprite horizontally
for a card thrown to the left.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *
from cardlib import draw_card

FW = FH = 24
CX, CY = 15.0, 12.0          # pushed right of centre to leave room for the trail
HW, HH = 4.2, 6.0

# angle, squash - a full half-turn over 4 frames, so frame 3 -> frame 0 is seamless
SPIN = [(0, 1.00), (45, 0.58), (90, 0.16), (135, 0.60)]


def trail(c, i):
    """A short gold comet trail: a bright core streak that feathers out, tapering to a point."""
    ramp = ['A', 'D', 'F', 'Y', 'w']
    x0, x1 = 0, 11               # t reaches 1 right at the card's left edge
    for x in range(x0, x1):
        t = (x - x0) / float(x1 - x0)               # 0 at the tail tip, 1 at the card
        half = 0.2 + t * t * 3.6
        wob = math.sin(t * 4.0 + i * 1.57) * 1.1
        for dy in range(-int(half) - 1, int(half) + 2):
            y = int(round(CY + dy + wob))
            if not c.inb(x, y) or c.p[y][x] != '.':
                continue
            fall = 1.0 - abs(dy) / (half + 0.9)
            if fall <= 0:
                continue
            v = (0.35 + t * 0.75) * fall ** 0.7
            if (x * 3 + y * 5 + i * 7) % 5 == 0:     # shimmer, so the trail is alive
                v *= 0.62
            k = int(v * len(ramp))
            if k > 0:
                c.p[y][x] = ramp[min(k - 1, len(ramp) - 1)]
    return c


def frame(i):
    c = Cv(FW, FH)
    ang, sq = SPIN[i]
    trail(c, i)
    draw_card(c, CX, CY, HW, HH, ang, squash=sq, glow=0.6)
    # sparks shedding off the trailing edge
    for k in range(3):
        a = hashf(k, i, 11)
        c.set(int(4 + a * 7), int(CY + (k - 1) * (3 + a * 3)), 'F' if a > 0.4 else 'D')
    return c


def build():
    return [frame(i) for i in range(4)]


DURATIONS = [55, 55, 55, 55]
TAGS = [('spin', 0, 3)]
