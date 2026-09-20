"""The yellow "dodge, don't parry" tell, sized and anchored like the red parry tell (parry_tell.png: 32x24
frames, pivot (16, 24), drawn at 3x) so the two sit at exactly the same place over a boss's head.

  dodge_tell   6 x 32x24, pivot (16, 24)
               0 ignite, 1 peak (appear, played once), then 2-5 a loop

The ring is Carter's approved yellow light (Assets/Characters/Carter/Demon/demon_light.png, frames 4-6),
copied pixel for pixel, never redrawn: a hollow ring wider than it is tall, a dark bar across it, lit
gold with a black outline. It differs from the red diamond in silhouette, fill, glyph and polarity, so
it survives colour blindness. Its bottom edge sits a texel above the pivot, where the red diamond's tip
does.

Carter's own rule for it holds here: the ring's body never changes once it has peaked. A tell that
flickers during the reaction window gets re-read instead of acted on, and the body's brightness is
what separates it from the red one in greyscale. So the loop's pulse lives entirely OFF the ring:
two pairs of arcs step outward on either side of it and fade, like a ping. Sideways arcs also point
the way the answer goes: a step out of the line."""
import sys
sys.dont_write_bytecode = True
from ev2_common import *

TW, TH = 32, 24
PIVOT = (16, 24)
LIGHT = PROJ + 'Assets/Characters/Carter/Demon/demon_light.png'
CELL = 24
# Carter's yellow frames: 4 ignite, 5 peak, 6 hold
IGNITE, PEAK, HOLD = 4, 5, 6
# his 24x24 cell onto this canvas: ring centred on x 16, bottom edge (his row 21) on row 22
OFFSET = (4, 1)
DURATIONS_MS = [50, 40, 110, 110, 110, 110]


def carter_cell(i):
    sheet = from_png(LIGHT)
    return cell(sheet, i, CELL, CELL)


def seat(src):
    c = Canvas(TW, TH)
    c.blit(src, OFFSET[0], OFFSET[1])
    return c


# The arcs, as (dx, dy) from the ring's side, drawn mirrored left and right. Each is a short bracket
# a texel clear of the ring's outline. Step k moves them k texels further out.
ARC = [(0, -3), (1, -2), (1, -1), (1, 0), (1, 1), (0, 2)]
RING_LEFT, RING_RIGHT, RING_MID = 4, 27, 13      # ring's outline columns and middle row on this canvas


def _arc(c, step, col):
    for (dx, dy) in ARC:
        x = RING_LEFT - 2 - step - dx
        y = RING_MID + dy
        if 0 <= x < TW and c.get(x, y) is None:
            c.set(x, y, col)
        x2 = RING_RIGHT + 2 + step + dx
        if 0 <= x2 < TW and c.get(x2, y) is None:
            c.set(x2, y, col)


def frames():
    g = [h for h in GOLD]
    out = [seat(carter_cell(IGNITE)), seat(carter_cell(PEAK))]
    hold = carter_cell(HOLD)
    # loop: an inner pair of arcs appears, steps out, fades while the next pair starts
    loop = [
        [(0, g[0])],
        [(1, g[1]), ],
        [(2, g[2]), (0, g[1])],
        [(1, g[2])],
    ]
    for arcs in loop:
        c = seat(hold)
        for step, col in arcs:
            _arc(c, step, col)
        out.append(c)
    return out


def build():
    return {'dodge_tell': frames()}


if __name__ == '__main__':
    F = frames()
    for i, f in enumerate(F):
        print(i, bbox(f))
