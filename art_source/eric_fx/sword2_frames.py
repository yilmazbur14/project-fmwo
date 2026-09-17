"""v2 thrown sword (8 x 128x128) and planted sword (2 x 64x128) for the redesigned greatsword."""
import math
from common import *
from fxdraw import arc_pixels, band_pixels, put, overlay
from stamps import S, stamp, crater, cloud, crack, polyline, blank, lines
import sword2

N = 128
R2 = math.sqrt(2)
V = sword2.build_up()                        # 29 x 118, tip up, axis col 14

# ---------------- 0 deg: tip right ----------------
def frame0():
    g = [['.'] * N for _ in range(N)]
    for r in range(118):
        for c in range(29):
            ch = V[r][c]
            if ch != '.':
                g[49 + c][122 - r] = ch
    return [''.join(row) for row in g]

# ---------------- 45 deg: tip down-right, hand-ruled on the diagonal lattice ----------------
PROFILE45 = "KABBA" + "C" * 17 + "DFFEEEFK"          # d = +15 .. -14 (light bevel .. thickness strip)
assert len(PROFILE45) == 30

def part45(x, y):
    s = x + y; d = x - y
    if 86 <= s <= 210 and -14 <= d <= 15 and x <= 105 and y <= 107:
        return 'blade'
    if 77 <= s <= 85 and -19 <= d <= 21 and not (s in (77, 85) and d in (-19, -18, 20, 21)):
        return 'guard'
    if 53 <= s <= 76 and -2 <= d <= 4:
        return 'grip'
    return None

def vsample(x, y):
    s = x + y; d = x - y
    rc = 58.5 - (s - 127) / R2
    cc = 14.5 - d / R2
    ri = math.floor(rc + 0.5); ci = math.floor(cc + 0.5)
    if 0 <= ri < 118 and 0 <= ci < 29:
        return V[ri][ci], ri, ci
    return '.', ri, ci

def frame45():
    P = [[None] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            p = part45(x, y)
            if p == 'blade':
                ch, ri, ci = vsample(x, y)
                d = x - y
                # keep the reference edge chips: body rows whose sample falls outside the blade
                if 10 <= ri <= 87 and ch == '.' and (d >= 13 or d <= -12):
                    p = None
            P[y][x] = p
    g = [['.'] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            p = P[y][x]
            if p is None:
                continue
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = P[y + dy][x + dx]
                if q is None or (p == 'guard' and q != 'guard') or (p == 'pommel' and q not in ('pommel', 'grip')):
                    edge = True
            if edge:
                g[y][x] = 'K'
    for y in range(N):
        for x in range(N):
            p = P[y][x]
            if p is None or g[y][x] == 'K':
                continue
            s = x + y; d = x - y
            ch, ri, ci = vsample(x, y)
            if p == 'blade':
                c = PROFILE45[15 - d]
                if c == 'C' and ch in ('A', 'D'):
                    c = ch                                   # forge pits / nicks from the reference
                # tip bevels: light along the x=105 edge, dark along the y=107 edge
                if x >= 104 and d > -12:
                    c = 'A' if x == 104 else c
                if x == 103 and d > -10 and s > 196:
                    c = 'B'
                if y >= 105 and d < 13:
                    c = 'F' if y == 106 else ('E' if y == 105 and c == 'C' else c)
                g[y][x] = c
            elif p == 'guard':
                row = {84: 1, 83: 2, 82: 3, 81: 3, 80: 4, 79: 5, 78: 5}[s]
                ci2 = min(27, max(1, ci))
                g[y][x] = sword2.GUARD[row][ci2] if sword2.GUARD[row][ci2] not in '.K' else 'C'
            elif p == 'grip':
                band = s % 8
                if d >= 3:
                    c = 'o'
                elif d >= 0:
                    c = 'r'
                else:
                    c = 'm'
                if band in (0, 1) and d <= 1:
                    c = 's' if d <= 0 else 'm'
                g[y][x] = c
            elif p == 'pommel':
                dd = d - 0.7; ss = s - 47.8
                if dd + ss > 3:
                    c = 'D' if dd + ss < 7 else 'E'
                elif dd - ss > 2:
                    c = 'B'
                else:
                    c = 'A'
                g[y][x] = c
    for dy, row in enumerate(POMMEL45):
        for dx, ch in enumerate(row):
            if ch != '.':
                g[20 + dy][20 + dx] = ch
    return [''.join(row) for row in g]

POMMEL45 = ["..KKKK..",
            ".KBBAAK.",
            "KBBAAADK",
            "KBAAADDK",
            "KAAADDEK",
            "KAADDEEK",
            ".KDDEEK.",
            "..KKKK.."]

# ---------------- white spin trail (Eric's white smear language), cw spin ----------------
C0 = 64.0
def smear(rot):
    g = [['.'] * N for _ in range(N)]
    put(g, band_pixels(C0, C0, 58.0, 60.5, rot - 24, rot - 7, N, N), 'W')
    put(g, arc_pixels(C0, C0, 59.3, rot - 40, rot - 24), 'W')
    put(g, arc_pixels(C0, C0, 59.3, rot - 51, rot - 45), 'W')
    put(g, arc_pixels(C0, C0, 47.0, rot - 30, rot - 11), 'W')
    put(g, arc_pixels(C0, C0, 38.5, rot - 22, rot - 12), 'W')
    put(g, arc_pixels(C0, C0, 59.0, rot + 180 - 24, rot + 180 - 7), 'W')
    put(g, arc_pixels(C0, C0, 59.0, rot + 180 - 34, rot + 180 - 29), 'W')
    return [''.join(r) for r in g]

def thrown_frames():
    a = overlay(smear(0), frame0())
    b = overlay(smear(45), frame45())
    out = []
    for k in range(4):
        out += [a, b]
        a, b = rot90cw(a), rot90cw(b)
    return out

# ---------------- planted: 64x128, tip buried, blade enters the ground at (31,112) ----------------
PW, PH = 64, 128
PCX, PCY = 31, 112

def v_down():
    body = V[10:88][::-1]
    tip = V[0:10][::-1]
    guard = sword2.GUARD
    grip = V[95:112]
    pommel = V[112:118]
    D = pommel + grip + guard + body + tip
    assert len(D) == 118
    return D

def planted_frame(impact):
    D = v_down()
    ground = blank(PW, PH); back = blank(PW, PH); sw = blank(PW, PH); lip = blank(PW, PH); front = blank(PW, PH)
    y0 = PCY - 105
    for r, row in enumerate(D):
        y = y0 + r
        if y > PCY + 1:
            break
        for c, ch in enumerate(row):
            if ch != '.':
                sw[y][c + 17] = ch
    # contact shadow where the blade sinks into the ground
    shade = {'C': 'D', 'A': 'C', 'B': 'A', 'E': 'F', 'D': 'E'}
    for x in range(PW):
        if sw[PCY][x] in shade:
            sw[PCY][x] = shade[sw[PCY][x]]
    # cracks radiating from the crater (flattened for the 3/4 view)
    long = not impact
    crack(ground, [(17, 113), (13, 112), (9, 113), (5, 112)] + ([(1, 113)] if long else []), thick=4)
    crack(ground, [(46, 113), (50, 112), (54, 113), (58, 112)] + ([(62, 113)] if long else []), thick=4)
    crack(ground, [(9, 113), (7, 116)], thick=0)
    crack(ground, [(54, 113), (56, 116)], thick=0)
    crack(ground, [(21, 116), (18, 119), (16, 122)] + ([(12, 124)] if long else []), thick=2)
    crack(ground, [(42, 116), (45, 119), (47, 122)] + ([(51, 124)] if long else []), thick=2)
    crack(ground, [(31, 117), (30, 121)] + ([(32, 125)] if long else []), thick=1)
    crack(ground, [(19, 109), (15, 106)] + ([(11, 105)] if long else []), thick=0)
    crack(ground, [(44, 109), (48, 106)] + ([(52, 105)] if long else []), thick=0)
    crater(ground, PCX + 0.5, PCY + 0.8, 15.5, 4.8)
    crater(lip, PCX + 0.5, PCY + 0.8, 15.5, 4.8)
    for y in range(PH):
        if y < PCY + 1:
            lip[y] = ['.'] * PW
    if impact:
        L = [(10.5, 112, 6.5), (17, 106.5, 6.0), (23, 100.5, 4.6), (6, 104.5, 4.0), (26, 95.5, 3.0), (5.5, 111, 3.4)]
        cloud(back, L + [(63 - x, y, r) for x, y, r in L])
        F = [(13, 119.5, 5.2), (22, 121.5, 4.8), (6, 118, 3.4)]
        cloud(front, F + [(63 - x, y, r) for x, y, r in F] + [(31.5, 122.5, 4.4)])
        for name, x, y in (('clod5', 2, 88), ('clod5', 56, 86), ('clod4', 11, 82), ('clod4', 49, 80),
                           ('pebble', 19, 78), ('pebble', 43, 76), ('pebble', 6, 96), ('pebble', 56, 97),
                           ('spark', 1, 99), ('spark', 60, 92), ('spark', 30, 84), ('dot', 14, 92), ('dot', 50, 90)):
            stamp(back, name, x, y)
        for name, x, y in (('clod4', 1, 122), ('clod4', 58, 121), ('pebble', 10, 124), ('pebble', 51, 124)):
            stamp(front, name, x, y)
    else:
        for name, x, y in (('pebble', 3, 108), ('pebble', 58, 109), ('pebble', 23, 121), ('pebble', 40, 122),
                           ('crumb', 12, 118), ('pebble', 47, 104)):
            if name == 'crumb':
                name = 'pebble'
            stamp(front, name, x, y)
    out = blank(PW, PH)
    for L_ in (ground, back, sw, lip, front):
        for y in range(PH):
            for x in range(PW):
                if L_[y][x] != '.':
                    out[y][x] = L_[y][x]
    return lines(out)

if __name__ == '__main__':
    fr = thrown_frames()
    st = strip(fr)
    save_grid('v2/eric_thrown_sword_grid.txt', st)
    write_grid_png('v2/eric_thrown_sword.png', st)
    view('v2/thrown_f0_8x.png', fr[0], 8)
    view('v2/thrown_f1_8x.png', fr[1], 8)
    view('v2/thrown_strip_3x.png', st, 3)
    pl = strip([planted_frame(True), planted_frame(False)])
    save_grid('v2/eric_sword_planted_grid.txt', pl)
    write_grid_png('v2/eric_sword_planted.png', pl)
    view('v2/planted_8x.png', pl, 8)
