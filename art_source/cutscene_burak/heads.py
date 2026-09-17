"""Hand-authored hooded heads (text grids). Origin = top-left of block."""
from blib import *

HEAD_GLOOM = """
.......########.........
....###AAAABBBB###......
..##AABBBBBBBBBBCC##....
.#ABBBBBBBBBBBBCCCCC#...
.#ABBBBBBBBBBBCCCCCCC#..
#ABBBBBBBBBCBBBBBBBBBB#.
#ABBBBBBBCB###########..
#ABBBBBBCB#FhhhHhhhHh#..
#ABBBBBCB#FhhHhhhhHhh#..
#BBBBBCCB#Fhhdhhhdhhfd#.
#BBBBCCCB#Fhfhddddhdds#.
#BBBCCCB#Fhfdkkkkkddss#.
#BBCCCCB#FhdddWikWdssss#
#BCCCCCB#Ffdssfffdssssa#
#CCCCCDB#Fffdssssssssf#.
#CCCCDDB#Fffddssssssss#.
#CCCCDDDB#Ffddsssssuus#.
#CCCDDDDB#Fffddssssdd#..
.#CCDDDDDB#Fgffffddf#...
.#CDDDDDDDB#Fg######....
..#DDDDDDDDB#F#L#.......
...#EDDDDDDDD##L#.......
....#EEEEEEEE##L#.......
..............#l#.......
...............#........
"""


def rows(t):
    r = blk_rows(t)
    wd = max(len(x) for x in r)
    for i, x in enumerate(r):
        if len(x) != wd:
            print('WARN row', i, 'len', len(x), 'expected', wd, repr(x))
    return r


if __name__ == '__main__':
    L = layer()
    blk(L, 20, 10, rows(HEAD_GLOOM))
    preview(L, 'heads_8x.png', s=10)
    print('ok')

HEAD_GLOOM_S = """
......#######........
...###AAABBBB###.....
..#AABBBBBBBBBCC#....
.#ABBBBBBBBBBCCCC#...
.#ABBBBBBBCCBBBBBB#..
#ABBBBBBCB#########..
#ABBBBBCB#FhhHhhHh#..
#ABBBBCB#FhhhhhHhhh#.
#BBBBCCB#Fhdhhdhhfd#.
#BBBCCB#Fhfkkkkfdds#.
#BBCCCB#Fhdwikwdssss#
#BCCCCB#Ffdsfffdsssa#
#CCCCDB#Fffdssssssf#.
#CCCDDB#Fffdssssuus#.
#CCDDDDB#Fffdssssd#..
.#CDDDDDB#Fgfffff#...
.#DDDDDDDB#Fg#####...
..#DDDDDDDB#F#L#.....
...#EDDDDDDD##L#.....
....#EEEEEEE##L#.....
.............#l#.....
..............#......
"""

# 3/4 front (turned toward camera). Eye area rows 9-11 left as skin; eyes stamped separately.
HEAD_TURN_BASE = """
......#######........
...###AAABBBB###.....
..#AABBBBBBBBBCC#....
.#ABBBBBBBBBBBCCC#...
.#ABBBBBBBBBBBBBCC#..
#ABBB##########BCCD#.
#ABB#FhhhHhhhhF#CCD#.
#AB#FhhHhhhhHhhF#CD#.
#AB#FhdhhdhhhdhH#CD#.
#AB#Ffdddddddddd#CD#.
#AB#Fddddddddddd#CD#.
#AB#Fddddddddddd#CD#.
#AB#Ffdsssssfssd#CD#.
#AB#Fffdsssssssd#CD#.
#AB#Fffdssuuusdd#CD#.
#ABB#Ffddssssdf#CCD#.
.#BBB#Fffdddf#FCCD#..
.#CBBB#F######FCD#...
..#CCCC#L#gg#L#D#....
...#DDD#L#FF#L#D#....
....#EE#l#..#l#E#....
........#....#.......
"""


def stamp_rows(base, x0, y0, patch):
    r = [list(s) for s in blk_rows(base)]
    for j, line in enumerate(patch):
        for i, ch in enumerate(line):
            if ch != '.':
                r[y0 + j][x0 + i] = ch
    return [''.join(s) for s in r]


TURN_EYES = {
    # patch at (x=5, y=9), 11 wide x 3 tall (face cols 5..15)
    'wide':  ["fkkkkddkkkd", "dWkkWdWkkdd", "dWikWdWikdd"],
    'wide2': ["fkkkkddkkkd", "dWWkWdWWkdd", "dfWWfddWWfd"],
    'open':  ["fkkkkddkkkd", "dkWikdkWikd", "dkiikdkiikd"],
    'open2': ["dkkkkddkkkd", "dWkiWdWkid.", "dfkkfddkkfd"],
    'blink': ["ddddddddddd", "dkkkkddkkkd", "dffffddfffd"],
}

# side-head expression patches: applied at (x=9, y=8), rows 8..13, cols 9..19 ('.' = keep base)
SIDE_EYES = {
    'gloom': None,
    'level': ["...........",
              ".kkkkkk....",
              "..WWik.....",
              "..WWkk.....",
              "..dfff.....",
              "..........."],
    'level2': ["...........",
               ".fkkkkf....",
               "..WWikd....",
               "..dWkkd....",
               "...fff.....",
               "..........."],
    'up': ["...........",
           ".kkkkkk....",
           "..WWkk.....",
           "..WWWi.....",
           "..dfff.....",
           "..........."],
    'det': ["..k........",
            ".dkkkkkk...",
            "..WikkW....",
            "..dffff....",
            "...........",
            "..........."],
    'det2': [".kk........",
             "..dkkkkk...",
             "..WkikWd...",
             "..dWkkfd...",
             "...ddd.....",
             "..........."],
    'det3': ["..kk.......",
             "...kkkk....",
             "..WWWkkk...",
             "..dWiWkd...",
             "...fff.....",
             "..........."],
}


def side_head(expr='gloom', mouth=None):
    r = [list(s) for s in blk_rows(HEAD_GLOOM_S)]
    p = SIDE_EYES.get(expr)
    if p:
        for j, line in enumerate(p):
            for i, ch in enumerate(line):
                if ch != '.':
                    r[8 + j][9 + i] = ch
    if mouth:
        for (x, y, ch) in mouth:
            r[y][x] = ch
    return [''.join(s) for s in r]


SIDE_MOUTHS = {
    'set': [(15, 13, 's'), (16, 13, 'u'), (17, 13, 'u'), (18, 13, 'u')],
    'open': [(16, 13, 'u'), (17, 13, 'U'), (17, 12, 'u'), (18, 13, 's')],
    'grit': [(15, 13, 'k'), (16, 13, 'W'), (17, 13, 'W'), (18, 13, 'k')],
}

TURN_EYES.update({
    'det': ["fkkkdddkkkd", "ddkkkdkkkdd", "dWikWdWkiWd"],
    'det2': ["fkkddddddkk", "ddkkkdkkkdd", "ddWiWdWiWdd"],
    'narrow': ["fdddddddddd", "dkkkkddkkkd", "dWikWdWkid."],
})


def turn_head(eyes='open', mouth=None):
    patch = [p.replace('.', 'd') for p in TURN_EYES[eyes]]
    r = stamp_rows(HEAD_TURN_BASE, 5, 9, patch)
    if mouth:
        r = [list(s) for s in r]
        for (x, y, ch) in mouth:
            r[y][x] = ch
        r = [''.join(s) for s in r]
    return r


TURN_MOUTHS = {
    'o': [(10, 14, 's'), (11, 14, 'u'), (12, 14, 's'), (11, 15, 'u')],
    'flat': [(10, 14, 'u'), (11, 14, 'u'), (12, 14, 'u')],
    'set': [(9, 14, 's'), (10, 14, 'u'), (11, 14, 'u'), (12, 14, 'u'), (13, 14, 's')],
}
