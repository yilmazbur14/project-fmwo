"""player_guard_break: 3 frames x 4 rows of 32x32, rows in the player_4dir_sheet order (down, up, left, right).
Dazed and exhausted: head bowed, shoulders rolled forward, gloves dropped to the knees, knees buckled.
Frames: 0 sway left, 1 centre with the head nodding down 1 px, 2 sway right. Play 0,1,2,1 (ping-pong).
Only the player's own 7 colours. Left is the exact mirror of right (x' = 31 - x), as in the 4-dir sheet.
The feet stay on the sheet's ground rows (27-28) and inside the idle footprint so nothing hops or slides."""
import sys
sys.dont_write_bytecode = True
from dh_common import *

# parts: (x, y, rows) in 32x32 frame coords; b skin, d skin shadow, c black, e red, a blue, f dark blue, g light blue
SHORTS_FRONT = (11, 18, [
    ".aagagag..",
    "aaaaaaaaf.",
    "aaaaaaaaaf",
    "aaaaaaaaaf",
    "aaaaaaaaaf",
    "aaaa..aaaf",
    "aaa....aaf",
])
LEGS_FRONT = (9, 25, [
    "...bd......bd.",
    "..bd........bd",
    ".ccc.......ccc",
    "cccc.......cccc",
])
ARM_L = (8, 12, ["...bd", "...bd", "..bd.", "..bd.", "..bd.", ".bd..", ".bd..", ".bd..", ".bd..", ".bd..",
                 "gaa..", "aaf..", ".ff.."])
ARM_R = (19, 12, ["db...", "db...", ".db..", ".db..", ".db..", "..db.", "..db.", "..db.", "..db.", "..db.",
                  "..aag", "..faa", "..ff."])

DOWN = {
    'lower': [SHORTS_FRONT, LEGS_FRONT],
    'body': [(11, 11, [
        ".bb.....bb.",
        "bdbdbbbdbdb",
        "bbbdbdbdbbd",
        ".bbbbdbbbd.",
        "..bbbdbbb..",
        "..bbbbbbb..",
        "...bbbbb...",
    ]), ARM_L, ARM_R],
    'head': [(13, 7, [".ccc.", "ccccc", "ccccc", "eccce", "eecee", "bbebb", "bebeb"])],
}

UP = {
    'lower': [SHORTS_FRONT, LEGS_FRONT],
    'body': [(11, 11, [
        ".bb.....bb.",
        "bdbbbdbbbdb",
        "bbdbbdbbdbd",
        ".bbbbdbbbd.",
        "..bbbdbbb..",
        "..bbbdbbb..",
        "...bbbbb...",
    ]), ARM_L, ARM_R],
    # back of the bowed head: hair, headband, and the knot's tails hanging limp over the right shoulder
    'head': [(13, 7, [".ccc.", "ccccc", "ccccc", "eeeee", "ccccc", ".ccc."]), (16, 11, ["e.", ".e"])],
}

RIGHT = {
    'lower': [(8, 18, [
        "....fgagag....",
        "....faaaaaa...",
        "...faaaaaaaa..",
        "...faaaaaaaaa.",
        "..gaaaaffaaaa.",
        "..gaaaf..aaaaa",
        "..aggf...aaaaa",
        "..bd......dbb.",
        "..bd......db..",
        ".cc.......ccc.",
        "ccc.......ccccc",
    ])],
    'body': [
        (9, 13, ["..bd", "..bd", "..bd", ".bd.", ".bd.", ".bd.", ".bd.", ".bd.", "gaa.", "aaf.", "ff.."]),  # far arm
        (11, 11, [
            "...dbbbd...",
            "..dbbbbbbd.",
            "..dbbdbdbd.",
            "..dbdbdbdd.",
            "..dbbdbbd..",
            "...dbbbbd..",
            "....dbbb...",
        ]),
        (19, 13, ["bd...", "bd...", ".bd..", ".bd..", ".bd..", "..bd.", "..bd.", "..bd.", "..gaa", "..aaf", "...ff"]),
    ],
    'head': [(13, 6, ["..ccc...", ".ccccc..", "e.cceee.", "e.eeeeee", "..ceebbb", "...dbbb."])],
}

# (body dx, head dx, head dy) per frame
SWAY = [(-1, -1, 0), (0, 0, 1), (1, 1, 0)]


def compose(pose, f):
    bdx, hdx, hdy = SWAY[f]
    g = [['.'] * 32 for _ in range(32)]

    def put_parts(parts, dx, dy):
        for (x0, y0, rows) in parts:
            for j, r in enumerate(rows):
                for i, ch in enumerate(r):
                    if ch != '.':
                        g[y0 + j + dy][x0 + i + dx] = ch
    # lower body first, then the far arm / torso / near arm, then the head on top
    put_parts(pose['lower'], 0, 0)
    put_parts(pose['body'], bdx, 0)
    put_parts(pose['head'], hdx, hdy)
    return [''.join(r) for r in g]


def build_rows():
    down = [compose(DOWN, f) for f in range(3)]
    up = [compose(UP, f) for f in range(3)]
    right = [compose(RIGHT, f) for f in range(3)]
    left = [[r[::-1] for r in fr] for fr in right]
    return [down, up, left, right]


def build():
    return [[grid(fr, PC) for fr in row] for row in build_rows()]


DURATIONS_MS = [150, 150, 150]          # play 0,1,2,1 ping-pong -> a 0.6 s wobble


if __name__ == '__main__':
    rows = build()
    sheet = grid_sheet(rows)
    assert sheet.colours() <= set(PC.values()), sheet.colours() - set(PC.values())
    src = from_png(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png')
    ref_rows = []
    for r in range(4):
        ref_rows.append([cell(src, 0, 32, 32, r), cell(src, 9, 32, 32, r)] + rows[r])
    save_zoom(grid_sheet(ref_rows), work('gb_sheet_8x.png'), 8, bg=(136, 180, 99), grid=(32, 32))
    for fr in build_rows()[3]:
        for y, r in enumerate(fr):
            if 5 <= y <= 28:
                print('%2d %s' % (y, r))
        print()
