"""brawl_arrow.png: the hook tell over Greyson's head. 8 frames of 28x28, one strip, static.
  frame = direction * 4 + state
  direction   0 LEFT, 1 RIGHT: the way to dodge
  state       0 pop, 1 live, 2 answered, 3 missed

MATT'S GLASS ROW BADGE, REBUILT, NOT REUSED. matt_boom_arrow.png's right is green and its LEFT IS RED
(#C6463D), and in this fight red means parry: the straight's badge is the shared red ParryTell. A red
left arrow would say "parry" and "dodge left" at once. So this is the same badge - Matt's own arrow glyph
(mfx_arrow.UP, imported, not copied), his 22-texel disc, his 2-texel ring, his dark rim, his top-left
light - in the game's DODGE colour: the shared dodge tell's gold (#FFC21E, tint #FFE45C, light #FFFCE0,
shade #D68A12), which already means "don't parry this, dodge it". Left and right are told apart by the
arrow alone, which survives colourblindness; dodge and parry are told apart by colour AND by silhouette
(round badge with an arrow against the red diamond with a "!"). The disc is Greyson's darkest trunk
purple, #391555, where Matt's is his lavender.

  pop       frame 0, the first one shown and the biggest: the badge at full size with its arrow already
            fully drawn and brightened a step, a white ring, and a burst ring round it. Like ParryTell it
            is legible on its first frame, so the pop costs no reaction time. Hold it ~0.05 s.
  live      the hold, for as long as the tell is up. It never pulses: a tell that flickers is re-read.
  answered  the dodge landed: arrow and ring white, edged in the tint, a gold glow round the disc in two
            alpha steps. Hold ~0.10 s, then fade out as ParryTell's badges do.
  missed    the hook landed: the arrow in Greyson's cool grey, the ring dead and broken in four places. No
            red X, unlike Matt's cracked state, because red is the parry.
THE PIVOT IS (14, 25): the bottom of the disc, so the badge stands on ParryTell's anchor exactly as the red
diamond and the yellow ring do, and all three tells come up in one spot over his head.
"""
import math
import os
import sys

import gb_pal as pal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'matt_fx'))
import mfx_arrow            # noqa: E402  (Matt's arrow glyph)

W = H = 28
C = 14.0
PIVOT = (14, 25)
DIRECTIONS = ('left', 'right')
STATES = ('pop', 'live', 'answered', 'missed')


def arrow_mask(direction):
    """Matt's up arrow in its 14x14 box, turned in exact 90 degree steps about the frame centre"""
    box = 7                                     # (28 - 14) / 2
    pts = {(box + x, box + y) for y, row in enumerate(mfx_arrow.UP) for x, k in enumerate(row) if k == '#'}
    turns = {'left': 3, 'right': 1}[direction]
    for _ in range(turns):
        pts = {(W - 1 - y, x) for (x, y) in pts}
    return pts


def frame(direction, state):
    g = pal.blank(W, H)
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - C, y + 0.5 - C)
            if d <= 11.0:
                g[y][x] = 'P'
                if 8.0 < d <= 10.0:
                    ring = {'pop': 'W', 'live': 'G', 'answered': 'W' if d <= 9.0 else 'H', 'missed': 'U'}[state]
                    if state == 'missed':
                        a = math.degrees(math.atan2(y + 0.5 - C, x + 0.5 - C)) % 360
                        if any(abs((a - c + 180) % 360 - 180) < 9 for c in (38, 128, 212, 305)):
                            ring = 'P'
                    g[y][x] = ring
                elif d > 10.0 and state in ('answered', 'pop'):
                    g[y][x] = 'H'
            elif state == 'pop' and 12.2 < d <= 13.4:
                g[y][x] = 'H'                                   # the burst ring
            elif state == 'answered' and d <= 12.4:
                g[y][x] = 'i' if d <= 11.7 else 'j'
    m = arrow_mask(direction)
    for (x, y) in m:
        up_out = (x, y - 1) not in m
        left_out = (x - 1, y) not in m
        down_out = (x, y + 1) not in m
        right_out = (x + 1, y) not in m
        if state == 'live':
            k = 'H' if (up_out or left_out) else ('D' if (down_out or right_out) else 'G')
        elif state == 'pop':
            k = 'L' if (up_out or left_out) else ('G' if (down_out or right_out) else 'H')
        elif state == 'answered':
            k = 'H' if (down_out or right_out) else 'W'
        else:
            k = 'S' if (up_out or left_out) else ('U' if (down_out or right_out) else 'T')
        g[y][x] = k
    return pal.rows(g)


def frames():
    return [frame(d, s) for d in DIRECTIONS for s in STATES]
