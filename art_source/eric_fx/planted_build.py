from common import *
from stamps import *
W, H = 64, 96
DX, DY = -15, -46          # frame-27 sheet coords -> this frame
CX, CY = 32, 80            # ground contact pixel (blade tip)

def sword_layer():
    g = blank(W, H)
    src = load_grid('planted_sword_src.txt')
    for y, row in enumerate(src):
        for x, c in enumerate(row):
            if c != '.':
                g[73 + y + DY][40 + x + DX] = c
    return g

def cracks(g, long=True):
    crack(g, [(24, 81), (21, 80), (18, 81), (15, 80)] + ([(11, 81), (9, 80)] if long else []))
    crack(g, [(18, 81), (16, 83)], thick=0)
    crack(g, [(41, 81), (44, 80), (47, 81), (50, 80)] + ([(54, 81), (56, 80)] if long else []))
    crack(g, [(47, 81), (49, 83)], thick=0)
    crack(g, [(27, 83), (25, 85), (24, 87)] + ([(21, 88)] if long else []), thick=2)
    crack(g, [(38, 83), (40, 85), (41, 87)] + ([(44, 88)] if long else []), thick=2)
    crack(g, [(33, 84), (32, 86)] + ([(33, 88)] if long else []), thick=1)
    crack(g, [(26, 79), (23, 77)] + ([(20, 77)] if long else []), thick=0)
    crack(g, [(39, 79), (42, 77)] + ([(45, 77)] if long else []), thick=0)

def gash(g):
    crater(g, 32.5, 81.3, 9.5, 3.4)

def lip(g):
    # redraw the front half of the crater over the blade tip so the blade reads as sunk
    tmp = blank(W, H); crater(tmp, 32.5, 81.3, 9.5, 3.4)
    for y in range(81, H):
        for x in range(W):
            if tmp[y][x] != '.': g[y][x] = tmp[y][x]

def compose(layers):
    out = blank(W, H)
    for L in layers:
        for y in range(H):
            for x in range(W):
                if L[y][x] != '.': out[y][x] = L[y][x]
    return out

def frame(impact):
    ground = blank(W, H); cracks(ground, long=not impact); gash(ground)
    back = blank(W, H); front = blank(W, H)
    if impact:
        # dust billowing out of the impact: two lobes behind the blade, a low band in front
        L = [(15, 77, 6), (21.5, 72, 5), (8.5, 81, 4.5), (11, 72.5, 3.2), (24.5, 67.5, 2.8), (17, 70, 3)]
        cloud(back, L + [(65 - x, y, r) for x, y, r in L])
        F = [(18.5, 86, 4.6), (26, 88, 4.2), (11.5, 88, 3.2)]
        cloud(front, F + [(65 - x, y, r) for x, y, r in F] + [(32.5, 89, 3.6)])
        # dirt and pebbles thrown up and out
        stamp(back, 'clod5', 2, 62); stamp(back, 'clod4', 57, 60); stamp(back, 'pebble', 13, 58)
        stamp(back, 'pebble', 48, 55); stamp(back, 'clod4', 24, 58); stamp(back, 'pebble', 39, 60)
        stamp(back, 'dot', 30, 54); stamp(back, 'dot', 6, 70); stamp(back, 'dot', 58, 71)
        stamp(back, 'spark', 34, 63); stamp(back, 'spark', 1, 75); stamp(back, 'spark', 60, 68)
        stamp(front, 'clod4', 4, 88); stamp(front, 'clod4', 56, 88); stamp(front, 'pebble', 12, 92)
        stamp(front, 'pebble', 50, 92)
    else:
        stamp(front, 'pebble', 13, 84); stamp(front, 'pebble', 48, 85); stamp(front, 'pebble', 38, 90)
        stamp(front, 'pebble', 22, 76)
    sw = sword_layer()
    lp = blank(W, H); lip(lp)
    return lines(compose([ground, back, sw, lp, front]))

if __name__ == '__main__':
    f0 = frame(True); f1 = frame(False)
    st = strip([f0, f1])
    save_grid('eric_sword_planted_grid.txt', st)
    write_grid_png('eric_sword_planted.png', st)
    view('planted_8x.png', st, 8)
