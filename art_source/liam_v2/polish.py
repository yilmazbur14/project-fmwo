"""Hand polish applied on top of frozen procedural layers.  Run: python polish.py"""
from lib import *

def load(name):
    return from_text(open('frozen/%s.txt' % name).read())

def blk(L, x0, y0, rows):
    wd = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == wd, 'row %d (y=%d) len %d != %d: %r' % (i, y0 + i, len(r), wd, r)
    overlay(L, x0, y0, '\n'.join(rows))

# ------------------------------------------------------------------ torso
def polish_torso(L):
    # re-fill jacket where the old procedural collar/tie/belt were, using neighbouring jacket tones
    # (rows are fully specified below where needed)
    # far collar wing  x 13..25, y 26..33
    blk(L, 13, 26, [
        "....#........",   # 26
        "....#W.......",   # 27
        "...#WWW......",   # 28
        "...#WWWWWww#.",   # 29
        "..#WWWwwwww##",   # 30
        "..#Wwwwv###..",   # 31
        ".#wvv###.....",   # 32
        ".####........",   # 33
    ])
    # near collar wing  x 31..46, y 24..33
    blk(L, 31, 24, [
        ".......##.......",   # 24
        "......#WW#......",   # 25
        ".....#WWW#......",   # 26
        "....#WWWWw#.....",   # 27
        "...#WWWWWww#....",   # 28
        "..#WWWWWwww#....",   # 29
        ".####WWwwwww#...",   # 30
        ".....###wwwvv#..",   # 31
        "........###vvv#.",   # 32
        "...........####.",   # 33
    ])
    # tie knot + blade  x 24..32, y 29..41
    blk(L, 24, 29, [
        ".#tTTTy#.",   # 29
        ".#TTTyy#.",   # 30
        "..#Tyy#..",   # 31
        "..#####..",   # 32
        "..#tTy#..",   # 33
        ".#tTTyy#.",   # 34
        ".#tTTyY#.",   # 35
        ".#tTTyY#.",   # 36
        ".#TTyyY#.",   # 37
        ".#TTyy#..",   # 38
        ".#Tyy#...",   # 39
        ".#yY#....",   # 40
        "..##.....",   # 41
    ])
    # under-the-beard row exposed when the head lifts 1px (chin-up frames)
    put(L, 20, 28, 'wwvv#ytTTyy#vw')
    # belt + raised steel buckle  x 11..48, y 41..46
    R = lambda *segs: ''.join(c * n for c, n in segs)
    blk(L, 11, 41, [
        R(('.', 14), ('#', 8), ('.', 16)),                                                     # 41
        R(('#', 15), ('m', 5), ('M', 1), ('#', 17)),                                           # 42
        R(('.', 1), ('#', 1), ('n', 12), ('#', 1), ('m', 1), ('M', 4), ('e', 1), ('#', 1), ('n', 15), ('#', 1)),  # 43
        R(('.', 2), ('#', 1), ('N', 11), ('#', 1), ('m', 1), ('M', 4), ('e', 1), ('#', 1), ('N', 14), ('#', 1), ('.', 1)),  # 44
        R(('.', 2), ('#', 1), ('N', 11), ('#', 1), ('M', 1), ('e', 4), ('E', 1), ('#', 1), ('N', 14), ('#', 1), ('.', 1)),  # 45
        R(('.', 3), ('#', 33), ('.', 2)),                                                      # 46
    ])
    return L

def fix_jacket_behind(L, frozen):
    """Where the old procedural collar/tie pixels were but the new art leaves '.', restore jacket tone."""
    pass

NEAR_FIST = [  # x 44..53, y 42..49
    "..####....",
    ".#aass##..",
    "#asssssd#.",
    "#ssssddf#.",
    "#sfdfdff#.",
    "#dsdsdff#.",
    ".#dfdff#..",
    "..#####...",
]
FAR_FIST = [  # x 3..10, y 47..54
    ".######.",
    "#aasssd#",
    "#assssd#",
    "#ssssdf#",
    "#fsfsdf#",
    "#dsdsff#",
    ".#dfff#.",
    "..####..",
]

def rows_from_segments(spec):
    """spec: {y: [(x, 'chars'), ...]} -> dict y -> 64-char row"""
    out = {}
    for y, segs in spec.items():
        row = ['.'] * 64
        for x, s in segs:
            for i, ch in enumerate(s):
                row[x + i] = ch
        out[y] = row
    return out

def build_legs_v2():
    fill = lambda pairs: ''.join(c * n for c, n in pairs)
    spec = {
        46: [(15, '#' * 33)],
        47: [(15, '#'), (16, fill([('p', 5), ('q', 8), ('Q', 3), ('q', 11), ('Q', 3), ('z', 1)])), (47, '#')],
        48: [(14, '#'), (15, fill([('p', 5), ('q', 9), ('Q', 4), ('q', 10), ('Q', 3), ('z', 1)])), (47, '#')],
        49: [(13, '#'), (14, fill([('p', 5), ('q', 9), ('Q', 2), ('z', 3), ('Q', 2), ('q', 8), ('Q', 3), ('z', 1)])), (47, '#')],
        50: [(12, '#'), (13, fill([('p', 5), ('q', 9), ('Q', 2), ('z', 2), ('Z', 1), ('z', 1), ('Q', 2), ('q', 9), ('Q', 3), ('z', 1)])), (48, '#')],
        51: [(12, '#'), (13, fill([('p', 5), ('q', 8), ('Q', 3), ('z', 2)])), (31, '#'),
             (32, fill([('z', 1), ('Q', 2), ('q', 2), ('p', 1), ('q', 6), ('Q', 3), ('z', 1)])), (48, '#')],
        52: [(11, '#'), (12, fill([('p', 5), ('q', 8), ('Q', 3), ('z', 2)])), (30, '#'), (32, '#'),
             (33, fill([('Q', 1), ('q', 3), ('p', 1), ('q', 6), ('Q', 3), ('z', 1)])), (48, '#')],
        53: [(11, '#'), (12, fill([('p', 5), ('q', 6), ('Q', 2), ('q', 2), ('Q', 2)])), (29, '#'), (33, '#'),
             (34, fill([('q', 3), ('p', 1), ('q', 6), ('Q', 3), ('z', 1)])), (48, '#')],
        54: [(10, '#'), (11, fill([('p', 5), ('q', 6), ('Q', 2), ('q', 2), ('Q', 2)])), (28, '#'), (34, '#'),
             (35, fill([('q', 2), ('p', 1), ('q', 7), ('Q', 3), ('z', 1)])), (49, '#')],
        55: [(10, '#'), (11, fill([('p', 4), ('q', 6), ('Q', 4), ('z', 2)])), (27, '#'), (35, '#'),
             (36, fill([('q', 1), ('p', 1), ('q', 7), ('Q', 3), ('z', 1)])), (49, '#')],
        56: [(9, '#'), (10, fill([('p', 5), ('q', 7), ('Q', 3), ('z', 2)])), (27, '#'), (35, '#'),
             (36, fill([('q', 1), ('p', 1), ('q', 8), ('Q', 3), ('z', 1)])), (50, '#')],
        57: [(6, '#' * 22), (35, '#' * 17)],
        58: [(5, '#'), (6, fill([('o', 3), ('O', 11), ('x', 7)])), (27, '#'),
             (35, '#'), (36, fill([('O', 9), ('o', 6)])), (51, '##')],
        59: [(3, '##'), (5, fill([('o', 4), ('O', 10), ('x', 8)])), (27, '#'),
             (35, '#'), (36, fill([('O', 8), ('o', 6), ('O', 3)])), (53, '##')],
        60: [(2, '#'), (3, fill([('o', 4), ('O', 11), ('x', 9)])), (27, '#'),
             (35, '#'), (36, fill([('O', 9), ('o', 3), ('O', 6)])), (54, '#')],
        61: [(2, '#'), (3, fill([('o', 3), ('O', 11), ('x', 10)])), (27, '#'),
             (35, '#'), (36, fill([('O', 14), ('x', 5)])), (55, '#')],
        62: [(2, '#'), (3, 'x' * 24), (27, '#'), (35, '#'), (36, 'x' * 19), (55, '#')],
        63: [(3, '#' * 24), (36, '#' * 19)],
    }
    rows = rows_from_segments(spec)
    L = [['.'] * 64 for _ in range(64)]
    for y, r in rows.items():
        L[y] = r
    return L

def build_arms_v2(Ls):
    import build
    near, _ = build.arm_poly(build.NEAR_ARM_POLY, (48.5, 30.5, 5.0), (49, 31.5, 58, 37.5, 4.6, 4.0), (58.5, 38.5), (51.5, 45.5), 1.0, cuff_w=2.5)
    far, _ = build.arm_poly(build.FAR_ARM_POLY, (10.5, 31.0, 5.0), (10, 32, 7.5, 41, 4.8, 4.2), (7.5, 40.5), (7, 48), 0.6, cuff_w=2.5)
    blk(near, 44, 42, NEAR_FIST)
    blk(far, 3, 47, FAR_FIST)
    Ls['near'] = near
    Ls['far'] = far

if __name__ == '__main__':
    import build
    Ls = {k: load(k) for k in ('tails', 'far', 'legs', 'torso', 'near', 'head')}
    polish_torso(Ls['torso'])
    build_arms_v2(Ls)
    Ls['legs'] = build_legs_v2()
    import os
    os.makedirs('layers', exist_ok=True)
    for k, v in Ls.items():
        open('layers/%s.txt' % k, 'w').write(to_text(v))
    cv = build.compose([Ls[k] for k in build.ORDER])
    open('out/base.txt', 'w').write(to_text(cv))
    write_png('out/base_wip.png', 64, 64, to_rgba(cv))
    preview(cv, 'out/base_8x.png')
    print('polished')
