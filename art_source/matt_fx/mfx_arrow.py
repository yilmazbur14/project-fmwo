"""matt_boom_arrow.png: the direction badge a sonic boom carries. 12 frames of 24x24, one strip, static.
  frame = direction * 3 + state
  direction   0 up, 1 right, 2 down, 3 left
  state       0 live, 1 answered, 2 cracked
THE PIVOT IS THE FRAME CENTRE (12, 12): put it on the boom's leading apex. Symmetric, never flipped.

The plan's badge (matt_plan_glass.md 6.3): a 22-texel #332F68 disc (66 px at 3x), a ring in the
direction's colour and a chunky 14x14 arrow, in ARROW_COLORS below: up #FFD93D, right #38CE7F,
down #349BD7, left #C6463D (the adjusted, greyscale-safe set the coordinator chose over the plan's).
  live       the disc, its outermost texel left dark so every badge has a dark rim on the mat whatever its
             colour; a 2-texel ring in the direction colour; the arrow in the colour, with a 1-texel
             highlight on its top and left edges and a shade on its bottom and right edges (a tint and a
             shade of the same colour), lit from the top left whichever way it points.
  answered   the arrow and ring turn white, edged in the colour's tint, the rim takes the tint, and a
             glow of the colour rings the disc (the frame's outermost texels, two alpha steps).
  cracked    the arrow and ring in the dead grey #6E6A80, the ring broken in four places, and a red X
             across the arrow in Matt's approved reds (#FF4A58 with #CF1E38 on its lower edge).
The arrow is drawn once pointing up and turned in exact 90 degree steps for the others; the shading is
applied after the turn, so the light is always from the top left. Nothing is rotated in the engine.
"""
import math

import mfx_pal as pal

W = H = 24
C = 12.0
FRAME_SIZE = (24, 24)
NOTE = '12 frames: [up, right, down, left] x [live, answered, cracked]; frame = direction * 3 + state'

# The coordinator's ruling (2026-09-23): the adjusted, greyscale-safe palette replaces the plan's
# (#FFD93D #3DE08A #3DB8FF #FF5A4E), whose right and down were one grey (165 vs 155). Each colour keeps its
# hue and saturation and is darkened by value alone to a lightness ladder: L* 88 / 74 / 61 / 48, Rec.601
# grey 211 / 152 / 131 / 107. MattArtLayout.ARROW_COLORS must match these.
ARROW_COLORS = {'up': 'FFD93D', 'right': '38CE7F', 'down': '349BD7', 'left': 'C6463D'}
DIRECTIONS = ('up', 'right', 'down', 'left')
STATES = ('live', 'answered', 'cracked')

# The arrow, pointing up, in its 14x14 box (placed at texels 5..18 of the frame).
UP = [
    '......##......',
    '.....####.....',
    '....######....',
    '...########...',
    '..##########..',
    '.############.',
    '##############',
    '....######....',
    '....######....',
    '....######....',
    '....######....',
    '....######....',
    '....######....',
    '....######....',
]
BOX = 5


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# A tint for the highlight and a hue-shifted shade for the shadow side of each colour (derived here; the
# plan gives only the base colours): gold shades to orange, green to teal, blue to deep blue, red to crimson.
TINT = {'up': 'FFF2A6', 'right': 'A5E9C5', 'down': 'A4D2ED', 'left': 'E5ACA8'}
SHADE = {'up': 'E0A21F', 'right': '1E9660', 'down': '1F68A8', 'left': '8C2626'}


def keys_for(direction):
    """The badge's own colours: the direction colour, its tint and its shade, plus the shared ones."""
    base = rgb(ARROW_COLORS[direction])
    light = rgb(TINT[direction])
    dark = rgb(SHADE[direction])
    return {
        'A': base + (255,), 'T': light + (255,), 'Z': dark + (255,),
        'g': light + (176,), 'h': light + (96,),                    # the answered glow, two alpha steps
        'X': (0xFF, 0x4A, 0x58, 255), 'x': (0xCF, 0x1E, 0x38, 255),   # the cracked X (Matt's reds)
        'Q': (0x6E, 0x6A, 0x80, 255),                                 # the dead grey
    }


def arrow_mask(direction):
    pts = {(BOX + x, BOX + y) for y, row in enumerate(UP) for x, k in enumerate(row) if k == '#'}
    turn = DIRECTIONS.index(direction)
    for _ in range(turn):                       # 90 degrees clockwise about the frame centre
        pts = {(W - 1 - y, x) for (x, y) in pts}
    return pts


def frame(direction, state):
    g = pal.blank(W, H)
    # disc, rim, ring
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - C, y + 0.5 - C)
            if d <= 11.0:
                g[y][x] = 'l'
                if 8.0 < d <= 10.0:
                    ring = {'live': 'A', 'answered': 's' if d <= 9.0 else 'T', 'cracked': 'Q'}[state]
                    if state == 'cracked':
                        a = math.degrees(math.atan2(y + 0.5 - C, x + 0.5 - C)) % 360
                        if any(abs((a - c + 180) % 360 - 180) < 9 for c in (38, 128, 212, 305)):
                            ring = 'l'                                # the breaks
                    g[y][x] = ring
                elif d > 10.0 and state == 'answered':
                    g[y][x] = 'T'
            elif state == 'answered' and d <= 12.0:
                g[y][x] = 'g' if d <= 11.6 else 'h'
    # the arrow
    m = arrow_mask(direction)
    for (x, y) in m:
        up_out = (x, y - 1) not in m
        left_out = (x - 1, y) not in m
        down_out = (x, y + 1) not in m
        right_out = (x + 1, y) not in m
        if state == 'live':
            k = 'T' if (up_out or left_out) else ('Z' if (down_out or right_out) else 'A')
        elif state == 'answered':
            k = 'T' if (down_out or right_out) else 's'
        else:
            k = 'Q'
        g[y][x] = k
    if state == 'cracked':
        # a bold X over the arrow: each stroke two texels of bright red with a dark red edge under it
        bright, edge = set(), set()
        for i in range(12):
            for (x, y) in ((6 + i, 6 + i), (7 + i, 6 + i), (17 - i, 6 + i), (16 - i, 6 + i)):
                bright.add((x, y))
        for (x, y) in list(bright):
            if (x, y + 1) not in bright:
                edge.add((x, y + 1))
        for (x, y) in edge:
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = 'x'
        for (x, y) in bright:
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = 'X'
    rows = pal.rows(g)
    return pal.Frame(rows, keys_for(direction))


def frames():
    return [frame(d, s) for d in DIRECTIONS for s in STATES]
