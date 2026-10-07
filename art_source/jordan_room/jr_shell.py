"""Jordan's room - the shell: floor boards (room_floor) and the walls (room_walls):
back wall with its doorway and the hallway seen through it, and the wall caps.

Break-away lines are drawn into the art: the floor is laid in three-row chunks
whose edges fall on board joints, and the wallpaper hangs in 62-texel strips.

Lighting is banded, not graded: every surface is flat inside a light level and
only the edge of a pool is dithered (ordered 4x4), the way the intro street
draws its shop-window glows.
"""
import random

import numpy as np

from jr_lib import Canvas, W, H, IDX, KEYS, bayer, band_index, DARKER, poly_mask
from jr_geom import (TOPCAP_Y1, WALL_Y0, FLOOR_Y, NEAR_Y, LX, RX, BASEBOARD_Y, LED_Y, PLANK,
                     DOOR_X0, DOOR_X1, DOOR_OPEN_X0, DOOR_OPEN_X1, DOOR_TOP, DOOR_OPEN_TOP,
                     MON_CX, MON_CY, monitor_wall, monitor_floor, hall_floor, pc_glow, _ell,
                     _sm)

# ---------------------------------------------------------------- floor looks
# roles: face, bevel (lit top edge of a board), gap (between rows), joint (board end),
#        hilite (lit lip after a joint), grain, knot
FLOOR_LOOKS = {
    'dark':  dict(face='M', bevel='B', gap='N', joint='N', hilite='B', grain='N', knot='N'),
    'cool':  dict(face='I', bevel='U', gap='N', joint='N', hilite='U', grain='M', knot='N'),
    'warm1': dict(face='B', bevel='w', gap='M', joint='M', hilite='w', grain='M', knot='M'),
    'warm2': dict(face='w', bevel='d', gap='B', joint='B', hilite='d', grain='B', knot='B'),
    'warm3': dict(face='d', bevel='s', gap='w', joint='w', hilite='s', grain='w', knot='w'),
}
WARM = ['dark', 'warm1', 'warm2', 'warm3']


def plank_layout(seed=11):
    """Rows of boards: [(row, y0, [[x0, x1, tone_off, seed]])]; x1 exclusive."""
    rnd = random.Random(seed)
    rows = []
    nrows = (NEAR_Y - FLOOR_Y) // PLANK
    for r in range(nrows):
        y0 = FLOOR_Y + r * PLANK
        x = LX - rnd.randrange(0, 90)
        boards = []
        while x < RX:
            ln = rnd.randrange(52, 128)
            x0, x1 = max(LX, x), min(RX, x + ln)
            if x1 - x0 >= 6:
                boards.append([x0, x1, rnd.choice((-1, 0, 0, 0, 1)), rnd.randrange(1 << 20)])
            elif boards:
                boards[-1][1] = x1          # never leave a sliver board
            x += ln
        boards[0][0] = LX                   # a leading sliver joins the first board
        for i in range(1, len(boards)):
            boards[i][0] = boards[i - 1][1]
        boards[-1][1] = RX
        rows.append((r, y0, boards))
    return rows


def floor_chunk_joints(rows, seed=5):
    """Pick, per group of three board rows, the joints the floor will break along
    (the second-stage crumble export uses these). Returns {row: set(joint_x)}."""
    rnd = random.Random(seed)
    cuts = {}
    groups = {}
    for (r, y0, boards) in rows:
        groups.setdefault(r // 3, []).append((r, boards))
    for g, members in sorted(groups.items()):
        targets = []
        t = LX + rnd.randrange(40, 110)
        while t < RX - 50:
            targets.append(t)
            t += rnd.randrange(86, 136)
        for (r, boards) in members:
            joints = [b[0] for b in boards[1:]]
            cuts[r] = set()
            for tx in targets:
                if joints:
                    j = min(joints, key=lambda jx: abs(jx - tx))
                    if abs(j - tx) < 60:
                        cuts[r].add(j)
    return cuts


def build_floor(hall=True, screens=True):
    """The boards, optionally lit by the doorway (hall) and by the screens and PC
    (screens). room_floor itself is the unlit version; the light pools travel with
    their sources (see jr_room)."""
    rows = plank_layout()
    hall = hall_floor() if hall else np.zeros((H, W))
    cool = np.maximum(monitor_floor(), pc_glow() * 0.8) if screens else np.zeros((H, W))
    c = Canvas()
    for (r, y0, boards) in rows:
        for bi, (x0, x1, off, bseed) in enumerate(boards):
            brnd = random.Random(bseed)
            streaks = []
            for _ in range(max(1, (x1 - x0) // (18 if off < 0 else 24))):
                sy = y0 + brnd.randrange(2, PLANK)
                sx = brnd.randrange(x0 + 2, max(x0 + 3, x1 - 3))
                streaks.append((sy, sx, sx + brnd.randrange(3, 12)))
            knot = None
            if brnd.random() < 0.2 and x1 - x0 > 20:
                knot = (brnd.randrange(x0 + 5, x1 - 5), y0 + brnd.randrange(3, PLANK - 2))
            for y in range(y0, y0 + PLANK):
                dy = y - y0
                for x in range(x0, x1):
                    hl = band_index(3, float(hall[y, x]) * 1.1, x, y, 0.2)
                    if hl > 0:
                        look = FLOOR_LOOKS[WARM[hl]]
                    else:
                        cl = band_index(2, float(cool[y, x]) * 0.62 + off * 0.03, x, y, 0.22)
                        look = FLOOR_LOOKS['cool' if cl >= 1 else 'dark']
                    if dy == 0:
                        role = 'gap'
                    elif x == x0 and x0 != LX:
                        role = 'joint'
                    elif dy == 1:
                        role = 'bevel' if (off >= 0 or bayer(x, y) < 0.5) else 'face'
                    elif x == x0 + 1 and x0 != LX and dy < 5:
                        role = 'hilite'
                    else:
                        role = 'face'
                        for (sy, sa, sb) in streaks:
                            if y == sy and sa <= x < sb:
                                role = 'grain'
                                break
                        if knot and y == knot[1] and abs(x - knot[0]) <= 1:
                            role = 'knot'
                    c.a[y, x] = IDX[look[role]]

    def dk(x, y):
        c.a[y, x] = IDX[DARKER[KEYS[c.a[y, x]]]]

    # contact shadow under the skirting board (not across the lit doorway)
    for x in range(LX, RX):
        if DOOR_OPEN_X0 <= x <= DOOR_OPEN_X1:
            continue
        dk(x, FLOOR_Y)
        if bayer(x, FLOOR_Y + 1) < 0.5:
            dk(x, FLOOR_Y + 1)
    # soft darkening along the side and near walls
    for y in range(FLOOR_Y, NEAR_Y):
        dk(LX, y)
        dk(RX - 1, y)
        if bayer(LX + 1, y) < 0.5:
            dk(LX + 1, y)
        if bayer(RX - 2, y) < 0.5:
            dk(RX - 2, y)
    for x in range(LX + 1, RX - 1):
        dk(x, NEAR_Y - 1)
        if bayer(x, NEAR_Y - 2) < 0.5:
            dk(x, NEAR_Y - 2)
    # the door sill: a worn strip across the opening
    for x in range(DOOR_OPEN_X0, DOOR_OPEN_X1 + 1):
        c.a[FLOOR_Y, x] = IDX['s' if x % 9 else 'd']
        c.a[FLOOR_Y + 1, x] = IDX['w']
    return c, rows


# ================================================================ back wall
STRIP_W = 62           # wallpaper strip width (620 / 10)
WALL_LOOKS = [dict(paper='N', stripe='N', seam='K'),
              dict(paper='I', stripe='N', seam='N'),
              dict(paper='U', stripe='I', seam='I')]
LED_COLOURS = ['8', 'V', 'U', 'c', 'U', 'V']          # the strip cycles along its length
LED_GLOW = {'8': 'V', 'V': 'V', 'U': 'I', 'c': '7'}


def strip_edges():
    xs = list(range(LX, RX, STRIP_W))
    if xs[-1] != RX:
        xs.append(RX)
    return xs


def wall_level(halo=True):
    """0 dark corners, 1 most of the wall, 2 the blurple halo round the monitors."""
    broad = 1.0 - _sm(0.5, 1.0, _ell(MON_CX - 50, 84, 340, 180))
    return 0.1 + 0.36 * broad + (0.5 * monitor_wall() if halo else 0.0)


def led_colour(x):
    seg = 84
    p = (x - LX) / seg
    i = int(p)
    f = p - i
    a = LED_COLOURS[i % len(LED_COLOURS)]
    b = LED_COLOURS[(i + 1) % len(LED_COLOURS)]
    if f > 0.8:          # a short dithered blend into the next colour
        return b if (f - 0.8) / 0.2 > bayer(x, 1) else a
    return a


def in_door(x, y):
    return DOOR_X0 <= x <= DOOR_X1 and y >= DOOR_TOP


def build_walls(halo=True):
    """Back wall + doorway + hallway view + all the caps. With room_floor it covers
    every pixel of the screen. halo=False leaves out the monitors' blurple halo,
    which room_furniture carries."""
    c = Canvas()
    lvl = wall_level(halo)
    seams = set(strip_edges()[1:-1])
    for y in range(WALL_Y0, FLOOR_Y):
        for x in range(LX, RX):
            li = band_index(2, float(lvl[y, x]), x, y, 0.18)
            look = WALL_LOOKS[li]
            if x in seams:
                k = look['seam']
            elif (x - LX) % 8 == 4:
                k = look['stripe']
            else:
                k = look['paper']
            c.a[y, x] = IDX[k]
    # crown moulding (y 4..6), RGB strip (y 7..8), its glow on the paper (y 9..16)
    for x in range(LX, RX):
        c.a[WALL_Y0, x] = IDX['K']
        c.a[WALL_Y0 + 1, x] = IDX['E']
        c.a[WALL_Y0 + 2, x] = IDX['N']
        lc = led_colour(x)
        c.a[LED_Y - 1, x] = IDX['W'] if (x % 6 == 0) else IDX[lc]
        c.a[LED_Y, x] = IDX[lc]
        c.a[LED_Y + 1, x] = IDX[LED_GLOW[lc]]
        for y in range(LED_Y + 2, LED_Y + 12):
            p = 1.0 - (y - LED_Y - 2) / 10.0
            if bayer(x, y) < p * 0.85 and KEYS[c.a[y, x]] in ('N', 'I', 'K'):
                c.a[y, x] = IDX[LED_GLOW[lc]]
    # skirting board: y 140..149
    for x in range(LX, RX):
        li = band_index(2, float(lvl[BASEBOARD_Y + 4, x]), x, BASEBOARD_Y + 4, 0.18)
        c.a[BASEBOARD_Y, x] = IDX['K']
        c.a[BASEBOARD_Y + 1, x] = IDX[['E', 'F', 'g'][li]]
        for y in range(BASEBOARD_Y + 2, FLOOR_Y - 2):
            c.a[y, x] = IDX[['6', 'E', 'F'][li]]
        c.a[FLOOR_Y - 2, x] = IDX[['N', '6', 'E'][li]]
        c.a[FLOOR_Y - 1, x] = IDX['K']
    for y in range(WALL_Y0, FLOOR_Y):
        c.a[y, LX] = IDX['K']
        c.a[y, RX - 1] = IDX['K']
    draw_doorway(c)
    draw_caps(c)
    return c


# ---------------------------------------------------------------- doorway + hallway
def draw_doorway(c):
    x0, x1 = DOOR_OPEN_X0, DOOR_OPEN_X1           # 45..99 clear opening
    y0, y1 = DOOR_OPEN_TOP, FLOOR_Y - 1           # 46..149
    vx, vy = (x0 + x1) / 2.0 + 3, 104.0           # vanishing point, a touch right
    fx0, fx1, fy0, fy1 = 62, 86, 72, 122          # the far end of the hallway
    # ceiling, side walls, far wall and floor of the hallway, one-point perspective
    ceil = poly_mask([(x0, y0), (x1 + 1, y0), (fx1 + 1, fy0), (fx0, fy0)])
    lwall = poly_mask([(x0, y0), (fx0, fy0), (fx0, fy1 + 1), (x0, y1 + 1)])
    rwall = poly_mask([(x1 + 1, y0), (x1 + 1, y1 + 1), (fx1 + 1, fy1 + 1), (fx1 + 1, fy0)])
    floor = poly_mask([(x0, y1 + 1), (fx0, fy1 + 1), (fx1 + 1, fy1 + 1), (x1 + 1, y1 + 1)])
    far = np.zeros((H, W), bool)
    far[fy0:fy1 + 1, fx0:fx1 + 1] = True
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if far[y, x]:
                k = 'd'
            elif ceil[y, x]:
                k = 's'
            elif floor[y, x]:
                # boards running away from us: lines towards the vanishing point
                u = (x - vx) / max(1.0, (y - vy))
                k = 'w' if abs(u * 5.0 - round(u * 5.0)) < 0.09 else 'd'
                if (y - fy1) in (4, 11, 21):
                    k = 'w'
            elif lwall[y, x]:
                k = 's' if y < 60 else 'd'
            elif rwall[y, x]:
                k = 'd'
            else:
                k = 'd'
            c.a[y, x] = IDX[k]
    # far wall details: a framed picture and a dado line
    c.rect(fx0 + 7, fy0 + 12, fx1 - 7, fy0 + 24, 'U')
    c.box(fx0 + 6, fy0 + 11, fx1 - 6, fy0 + 25, 'B')
    c.hline(fx0, fx1, fy0 + 36, 'w')
    c.hline(fx0, fx1, fy1, 'B')
    # the hallway ceiling lamp: a bright disc and a halo
    for y in range(y0, fy0 + 2):
        for x in range(x0, x1 + 1):
            d = ((x - (vx - 1)) / 11.0) ** 2 + ((y - (y0 + 9)) / 5.0) ** 2
            if d < 1.0 and bayer(x, y) < (1 - d) * 1.2:
                c.set(x, y, 'W')
    c.rect(int(vx) - 5, y0 + 7, int(vx) + 3, y0 + 10, 'W')
    c.hline(int(vx) - 4, int(vx) + 2, y0 + 11, 'P')
    # perspective edges of the hallway box
    for (a, b) in (((x0, y0), (fx0, fy0)), ((x1, y0), (fx1, fy0)),
                   ((x0, y1), (fx0, fy1)), ((x1, y1), (fx1, fy1))):
        c.line(a[0], a[1], b[0], b[1], 'w')
    c.box(fx0, fy0, fx1, fy1, 'w')
    # the door, swung open against the hallway's left wall, KEEP OUT sign on it
    leaf = poly_mask([(x0, y0 + 2), (x0 + 11, y0 + 11), (x0 + 11, y1 - 10), (x0, y1 + 1)])
    c.fill(leaf, 'g')
    for y in range(y0 + 2, y1 + 1):
        for x in range(x0, x0 + 12):
            if leaf[y, x] and x >= x0 + 9:
                c.set(x, y, 'F')
    sign = poly_mask([(x0 + 2, 84), (x0 + 9, 88), (x0 + 9, 100), (x0 + 2, 99)])
    c.fill(sign, 'R')
    c.fill(sign & poly_mask([(x0 + 2, 90), (x0 + 9, 93), (x0 + 9, 95), (x0 + 2, 93)]), 'Y')
    c.set(x0 + 9, 104, 'Y')                                    # the knob
    c.set(x0 + 9, 105, 'A')
    edge = leaf & ~np.roll(leaf, -1, axis=1)
    c.fill(edge, 'K')
    c.fill(poly_mask([(x0, y0 + 2), (x0 + 11, y0 + 11), (x0 + 11, y0 + 12),
                      (x0, y0 + 3)]) & leaf, 'K')
    # warm light spilling out over the jambs is handled on the floor; here the casing
    ca = 'B'
    c.rect(DOOR_X0, DOOR_TOP, DOOR_X1, DOOR_OPEN_TOP - 1, ca)          # head casing
    c.rect(DOOR_X0, DOOR_TOP, DOOR_OPEN_X0 - 1, FLOOR_Y - 1, ca)       # left jamb casing
    c.rect(DOOR_OPEN_X1 + 1, DOOR_TOP, DOOR_X1, FLOOR_Y - 1, ca)       # right jamb casing
    c.hline(DOOR_X0, DOOR_X1, DOOR_TOP, 'w')
    c.hline(DOOR_X0 + 1, DOOR_X1 - 1, DOOR_TOP + 1, 'd')
    c.vline(DOOR_X0 + 1, DOOR_TOP + 1, FLOOR_Y - 2, 'w')
    c.vline(DOOR_X1 - 1, DOOR_TOP + 2, FLOOR_Y - 2, 'M')
    c.vline(DOOR_OPEN_X0 - 1, DOOR_OPEN_TOP, FLOOR_Y - 1, 'M')      # inner edge in shade
    c.vline(DOOR_OPEN_X1 + 1, DOOR_OPEN_TOP, FLOOR_Y - 1, 'd')      # inner edge lit by the hall
    c.hline(DOOR_OPEN_X0 - 1, DOOR_OPEN_X1 + 1, DOOR_OPEN_TOP - 1, 'M')
    c.box(DOOR_X0 - 1, DOOR_TOP - 1, DOOR_X1 + 1, FLOOR_Y, 'K')
    c.box(DOOR_OPEN_X0 - 2, DOOR_OPEN_TOP - 2, DOOR_OPEN_X1 + 2, FLOOR_Y, 'K')
    # plinth blocks at the foot of the casing
    for (a, b) in ((DOOR_X0, DOOR_OPEN_X0 - 2), (DOOR_OPEN_X1 + 2, DOOR_X1)):
        c.rect(a, FLOOR_Y - 8, b, FLOOR_Y - 1, 'M')
        c.hline(a, b, FLOOR_Y - 8, 'K')
    # light from the hall grazing the wall beside the door
    for y in range(DOOR_TOP, FLOOR_Y):
        for x in range(DOOR_X1 + 2, DOOR_X1 + 7):
            if bayer(x, y) < 0.45 - (x - DOOR_X1 - 2) * 0.09 and KEYS[c.a[y, x]] in ('N', 'I'):
                c.a[y, x] = IDX['V' if y < BASEBOARD_Y else 'E']


# ---------------------------------------------------------------- caps
def draw_caps(c):
    """Top cap, side caps and the near cap: the tops of the walls, seen from above."""
    c.rect(0, 0, W - 1, TOPCAP_Y1, 'N')
    c.rect(0, 0, LX - 1, H - 1, 'N')
    c.rect(RX, 0, W - 1, H - 1, 'N')
    c.rect(0, NEAR_Y, W - 1, H - 1, 'N')
    c.hline(0, W - 1, 0, 'K')
    c.hline(0, W - 1, H - 1, 'K')
    c.vline(0, 0, H - 1, 'K')
    c.vline(W - 1, 0, H - 1, 'K')
    c.hline(LX - 1, RX, TOPCAP_Y1, 'K')
    c.hline(LX - 1, RX, NEAR_Y, 'K')
    c.vline(LX - 1, TOPCAP_Y1, NEAR_Y, 'K')
    c.vline(RX, TOPCAP_Y1, NEAR_Y, 'K')
    # the lit lip along each cap's inner edge
    c.vline(LX - 2, 1, NEAR_Y - 1, 'I')
    c.vline(RX + 1, 1, NEAR_Y - 1, 'I')
    c.hline(1, W - 2, TOPCAP_Y1 - 1, 'I')
    c.hline(LX - 2, RX + 1, NEAR_Y + 1, 'I')
