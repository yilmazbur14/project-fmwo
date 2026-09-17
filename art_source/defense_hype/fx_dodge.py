"""perfect_dodge_trail: cyan afterimage GHOST frames of the player (not a streak), 4 frames x 4 rows of 32x32.
Rows follow player_4dir_sheet (down, up, left, right); each row is that direction's idle silhouette.
Frame 0 solid cyan ghost with a pale rim, 1 half dissolved (checker), 2 quarter dissolved and dimmer,
3 a few twinkles. Same pivot/centering as the player sprite, so a ghost spawned at the player's position
with the same facing lines up exactly. DB32 only."""
import sys
sys.dont_write_bytecode = True
from dh_common import *

SRC_COL = 0           # idle column of the 4-dir sheet

# player colour -> ghost colour (by value: light -> pale, mid -> cyan, dark -> blue)
TONE = {PC['b']: 'C', PC['g']: 'P', PC['a']: 'C', PC['d']: 'b', PC['e']: 'P', PC['f']: 'B', PC['c']: 'B'}


def ghost_frames(src, row):
    base = cell(src, SRC_COL, 32, 32, row)
    solid = {(x, y) for y in range(32) for x in range(32) if base.p[y][x]}
    edge = {(x, y) for (x, y) in solid
            if any((x + dx, y + dy) not in solid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    frames = []
    # 0: solid ghost, white-hot rim on the upper/left edges, pale elsewhere
    f0 = Canvas(32, 32)
    for (x, y) in solid:
        if (x, y) in edge:
            up_left = (x - 1, y) not in solid or (x, y - 1) not in solid
            f0.p[y][x] = C['W'] if up_left else C['P']
        else:
            f0.p[y][x] = C[TONE[base.p[y][x]]]
    frames.append(f0)
    # 1: checker dissolve inside, rim kept on alternate pixels
    f1 = Canvas(32, 32)
    for (x, y) in solid:
        if (x, y) in edge:
            if (x + y) % 2 == 0 or y < 10:
                f1.p[y][x] = C['P']
        elif (x + y) % 2 == 0:
            f1.p[y][x] = C[{'P': 'P', 'C': 'C', 'b': 'b', 'B': 'b'}[TONE[base.p[y][x]]]]
    frames.append(f1)
    # 2: sparse, dimmer
    f2 = Canvas(32, 32)
    for (x, y) in solid:
        if x % 2 == 0 and y % 2 == 0:
            f2.p[y][x] = C['b'] if (x, y) not in edge else C['C']
        elif (x, y) in edge and (x + 2 * y) % 5 == 0:
            f2.p[y][x] = C['C']
    frames.append(f2)
    # 3: twinkles where the ghost was
    f3 = Canvas(32, 32)
    ys = sorted({y for (_, y) in solid})
    xs = sorted({x for (x, _) in solid})
    cx = (xs[0] + xs[-1]) // 2
    spots = [(cx - 3, ys[0] + 3, 1), (cx + 4, ys[0] + 11, 0), (cx - 4, ys[0] + 17, 0), (cx + 2, ys[-1] - 4, 1)]
    for (x, y, big) in spots:
        f3.p[y][x] = C['W']
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                f3.p[y + dy][x + dx] = C['C']
    frames.append(f3)
    return frames


def build():
    src = from_png(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png')
    return [ghost_frames(src, r) for r in range(4)]


DURATIONS_MS = [50, 60, 70, 80]


if __name__ == '__main__':
    rows = build()
    sheet = grid_sheet(rows)
    print('non-DB32', sheet.colours() - DB32)
    save_zoom(sheet, work('dodge_trail_8x.png'), 8, bg=(136, 180, 99), grid=(32, 32))
