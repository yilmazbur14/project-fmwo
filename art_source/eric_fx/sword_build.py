from common import *
from fxdraw import *
N = 96; C = 48.0  # continuous centre of the 96x96 frame

def smear(rot):
    """white spin-smear for the frame whose sword angle is `rot` degrees (0 = tip right). cw spin."""
    g = [['.'] * N for _ in range(N)]
    # tip trail: a crescent, 2px thick right behind the tip, thinning to 1px, then a broken dash
    put(g, band_pixels(C, C, 26.0, 28.0, rot - 30, rot - 14), 'W')
    put(g, arc_pixels(C, C, 27.0, rot - 48, rot - 30), 'W')
    put(g, arc_pixels(C, C, 27.0, rot - 62, rot - 55), 'W')
    # inner echo arc swept by the blade edge
    put(g, arc_pixels(C, C, 22.0, rot - 40, rot - 20), 'W')
    # pommel trail
    put(g, arc_pixels(C, C, 28.0, rot + 180 - 30, rot + 180 - 8), 'W')
    put(g, arc_pixels(C, C, 28.0, rot + 180 - 43, rot + 180 - 37), 'W')
    return [''.join(r) for r in g]

def frames():
    s0 = load_grid('sword_000.txt'); s45 = load_grid('sword_045.txt')
    b0 = overlay(smear(0), s0); b45 = overlay(smear(45), s45)
    out = []
    a, b = b0, b45
    for k in range(4):
        out += [a, b]
        a, b = rot90cw(a), rot90cw(b)
    return out

if __name__ == '__main__':
    fr = frames()
    for f in fr:
        assert len(f) == 96 and all(len(r) == 96 for r in f)
    st = strip(fr)
    save_grid('eric_thrown_sword_grid.txt', st)
    write_grid_png('eric_thrown_sword.png', st)
    view('thrown_f01_8x.png', strip(fr[0:2]), 8)
    view('thrown_strip_3x.png', st, 3)
