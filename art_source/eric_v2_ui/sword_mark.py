"""The red mark on the floor under the spot Eric's thrown greatsword is going to land on, so the throw
is still readable once the player has walked off it (Scripts/EricSwordMark.gd).

  eric_sword_mark  12 x 152x52, pivot (76, 26)
                   0-8   the fixed target ring, plus a second ring closing onto it from 1.8x its
                         radius to just outside it
                   9     the commit frame: the target ring lit hot, with ticks turned in on it
                   10-11 the impact flash, played once where the blade goes in

The ellipse is squashed to eric_leap_shadow.png's own ratio (its lowest frame is 44 x 14 texels), so
the mark lies on the same floor plane every shadow in the fight already does. Drawn at 3x like the
rest of this kit: the target ring's 40-texel radius is DefenseHypeArtLayout.SWORD_MARK_RADIUS, 120
screen px, the ground the sword can still reach the player on.

Its colours are parry_tell_strong.png's, the fight's "this one can be parried" red, and it is a closed
filled band where the yellow dodge tell is a hollow silhouette: neither can be mistaken for the other
with the colour taken away."""
import sys
sys.dont_write_bytecode = True
from ev2_common import *

TW, TH = 152, 52
# The ellipse sits on the boundary between the two middle texels, so the pivot is the canvas centre.
CX, CY = TW / 2.0 - 0.5, TH / 2.0 - 0.5
PIVOT = (TW // 2, TH // 2)

# eric_leap_shadow.png frame 0: 44 texels across, 14 tall.
SQUASH = 7.0 / 22.0
RX = 40.0
RY = RX * SQUASH

# Band thicknesses in texels. A band is the gap between the ellipse and the same one pulled this far
# in along both axes, rather than a scaled-down copy: a squashed ellipse's poles are so flat that a
# scaled copy leaves under a texel there and the ring breaks up.
TARGET_BAND = 3.0
CLOSING_BAND = 2.0
COMMIT_BAND = 4.0

CLOSE_FRAMES = 9
# The closing ring's radius, as a multiple of the target's: it stops a clear gap short of it, and the
# commit frame is where it arrives.
FROM_SCALE, TO_SCALE = 1.8, 1.15
# It heats up as it comes in, so the last frames before the commit already read as hot.
CLOSING_RAMP = ['E'] * 4 + ['e'] * 3 + ['S'] * 2

# How far the commit frame's ticks reach in, and the gap they leave the ring.
TICK_LEN, TICK_GAP = 6, 3

IMPACT = [
    # (radius multiple, band thickness, body, outer edge)
    (1.2, 6.0, 'W', 'S'),
    (1.5, 2.0, 'e', 'E'),
]

DURATIONS_MS = [50] * CLOSE_FRAMES + [240, 50, 70]
PALETTE = {C[ch] for ch in 'KEeSW'}


def inside(rx, ry):
    return {(x, y) for y in range(TH) for x in range(TW)
            if ((x - CX) / rx) ** 2 + ((y - CY) / ry) ** 2 <= 1.0}


def band(c, scale, thickness, body, edge):
    """a filled elliptical band `thickness` texels wide, on the ellipse at `scale` of the target's"""
    rx, ry = RX * scale, RY * scale
    outer = inside(rx, ry)
    ring = outer - inside(rx - thickness, ry - thickness)
    for (x, y) in ring:
        lit = any((x + dx, y + dy) not in outer for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        put(c, x, y, edge if lit else body)
    outline(c, ring, diag=False)
    return ring


def ticks(c, col):
    """short marks turned in off the ring's four poles, so the commit frame differs in silhouette too"""
    x0 = CX - RX + COMMIT_BAND + TICK_GAP
    y0 = CY - RY + COMMIT_BAND + TICK_GAP
    for k in range(TICK_LEN):
        for y in (CY - 0.5, CY + 0.5):
            put(c, x0 + k, y, col)
            put(c, TW - 1 - int(x0 + k), y, col)
    for k in range(TICK_LEN - 3):
        for x in (CX - 0.5, CX + 0.5):
            put(c, x, y0 + k, col)
            put(c, x, TH - 1 - int(y0 + k), col)


def target(c, thickness=TARGET_BAND, body='E', edge='e'):
    return band(c, 1.0, thickness, body, edge)


def frames():
    out = []
    for i in range(CLOSE_FRAMES):
        c = Canvas(TW, TH)
        scale = FROM_SCALE + (TO_SCALE - FROM_SCALE) * i / (CLOSE_FRAMES - 1)
        heat = CLOSING_RAMP[i]
        band(c, scale, CLOSING_BAND, heat, heat)
        target(c)
        out.append(c)
    commit = Canvas(TW, TH)
    target(commit, COMMIT_BAND, 'S', 'W')
    ticks(commit, C['W'])
    out.append(commit)
    for scale, thickness, body, edge in IMPACT:
        c = Canvas(TW, TH)
        band(c, scale, thickness, body, edge)
        out.append(c)
    return out


def build():
    return {'eric_sword_mark': frames()}


if __name__ == '__main__':
    F = frames()
    for i, f in enumerate(F):
        print(i, bbox(f), sorted(f.colours()))
    zoom(strip(F), 'eric_sword_mark_zoom.png', 3)
