from common import *
W, H = 48, 16

def ell(w, h):
    rx, ry = w / 2, h / 2
    g = []
    for y in range(H):
        row = ''
        for x in range(W):
            # test slightly inside the pixel centre to avoid 1px nubs at the extremes
            v = ((x + 0.5 - 24) / rx) ** 2 + ((y + 0.5 - 8) / ry) ** 2
            row += 'K' if v <= 1.0 else '.'
        g.append(row)
    return g

if __name__ == '__main__':
    fr = [ell(44.6, 14.6), ell(34.6, 10.6), ell(24.6, 7.6)]
    for f in fr:
        for r in f: print(r)
        print()
        # symmetry checks
        assert all(r == r[::-1] for r in f)
        assert f == f[::-1]
    st = strip(fr)
    save_grid('eric_leap_shadow_grid.txt', st)
    write_grid_png('eric_leap_shadow.png', st)
    view('shadow_8x.png', st, 8)
