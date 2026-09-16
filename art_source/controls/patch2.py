src = open('bg.py', encoding='utf-8').read()

# ---------------- gloves: wrist -> big fist, clear thumb lobe, spherical shading
gl_start = src.index('GLOVE = [')
gl_end = src.index('# ------------------------------------------------------------------ chalkboard')
gloves = '''GLOVE = [
    ".....#####......",
    "....#WcccC#.....",
    "....#cccCC#.....",
    "....#######.....",
    "....#hrrrd#.....",
    "...#hrrrrrd#....",
    "..#hhrrrrrd##...",
    "..#hrrrrrrd#t#..",
    ".#hrrrrrrrd#tt#.",
    ".#hrrrrrrrr#ttd#",
    "#hhsrrrrrrrr#td#",
    "#hssrrrrrrrrr#d#",
    "#hhrrrrrrrrrrr##",
    "#hrrrrrrrrrrrrd#",
    "#rrrrrrrrrrrrrd#",
    "#rrrrrrrrrrrrdd#",
    "#drrrrrrrrrrrdd#",
    ".#drrrrrrrrrdd#.",
    ".#ddrrrrrrrddd#.",
    "..#dddddddddd#..",
    "...##dddddd##...",
    ".....######.....",
]
for _r in GLOVE:
    assert len(_r) == 16, (_r, len(_r))
GLOVE_MAP = {'#': K, 'W': G5, 'c': G4, 'C': G2, 'h': PK, 's': SK, 'r': RD, 'd': BR, 't': RD}


def draw_gloves(c):
    hx, hy = 561, 116
    c.rect(hx - 1, hy, hx + 1, hy + 3, K)
    c.set(hx, hy + 1, G3)
    back_map = dict(GLOVE_MAP)
    back_map.update({'W': G4, 'c': G2, 'C': G1, 'h': RD, 's': PK, 'r': BR, 'd': P0, 't': BR})
    mirrored = [r[::-1] for r in GLOVE]
    c.line(hx, hy + 3, 555, 131, G3)
    c.line(hx, hy + 3, 563, 135, G4)
    c.grid(547, 131, mirrored, back_map, skip='.')
    c.grid(555, 135, GLOVE, GLOVE_MAP, skip='.')


'''
src = src[:gl_start] + gloves + src[gl_end:]

# ---------------- towel: bend over seat edge, soft creases, straight slanted hem
tw_start = src.index('def towel_grid():')
tw_end = src.index('TOWEL_MAP = {')
towel = '''TOWEL = [
    "..#################..",
    ".#WWWWWWWWWWWWWWWWWg#.",
    "#WWwwwwwwwwwwwwwwwwgg#",
    "#WWWWWWWWWWWWWWWWWWWg#",
    "#Wwwwwwwwwwwwwwwwwwgg#",
    "#Wgggwwwwwwwwwwwggggg#",
    "#Wwwwwwwwgwwwwwwwwwwg#",
    "#Wwwwwwwwgwwwwwwwwwwg#",
    "#Wwwwwwwwwgwwwwwwwwwg#",
    "#Wwwwwwwwwgwwwwwwwwwg#",
    "#Wwwwwwwwwgwwwwwwwwwg#",
    "#Wwwwwwwwwgwwwwwwwwwg#",
    "#Wwwwwwwwwwgwwwwwwwwg#",
    "#prrrrrrrrrrrrrrrrrrR#",
    "#RRRRRRRRRRRRRRRRRRRR#",
    "#Wwwwwwwwwwgwwwwwwwwg#",
    "#prrrrrrrrrrrrrrrrrrR#",
    "#RRRRRRRRRRRRRRRRRRRR#",
    "#Wwwwwwwwwwwgwwwwwwwg#",
    "#Wwwwwwwwwwwgwwwwwwwg#",
    "#wwwwwwwwwwwgwwwwwwwg#",
    "#gwwwwwwwwwwgwwwwwwwg#",
    "#ggggwwwwwwwgwwwwwwgg#",
    ".####gggwwwwgwwwwwggg#",
    ".....####gggggwwwggg#.",
    ".........######ggg##..",
    "...............###....",
]
for _r in TOWEL:
    assert len(_r) == 21, (_r, len(_r))


def towel_grid():
    return TOWEL


'''
src = src[:tw_start] + towel + src[tw_end:]
src = src.replace("TOWEL_MAP = {'#': K, 'W': G5, 'w': G4, 'g': G2, 'r': RD, 'R': BR}",
                  "TOWEL_MAP = {'#': K, 'W': G5, 'w': G4, 'g': G2, 'r': RD, 'R': BR, 'p': PK}")
src = src.replace("c.grid(17, 213, towel_grid(), TOWEL_MAP, skip='.')",
                  "c.grid(18, 216, towel_grid(), TOWEL_MAP, skip='.')")
open('bg.py', 'w', encoding='utf-8').write(src)
print('patched')
