"""render the head region map into a canvas"""
from lib import *
from lib import _LIGHTER, _DARKER
import headmap

MODELS = {
    'h': ('hair', ('sphere', 45, 11, 17, 13, 0.25), [0.97, 0.85, 0.55, 0.2, -0.1]),
    'f': ('skin', ('sphere', 45.5, 23, 13, 12, 0.6), [0.95, 0.66, 0.42, 0.15, -9]),
    'r': ('skin', ('sphere', 47.5, 22, 16, 6, 0.2), [9, 0.9, 0.6, 0.3, -9]),
    'd': ('hair', ('sphere', 44, 33, 19, 19, 0.3), [9, 0.9, 0.66, 0.36, 0.05]),
    'm': ('hair', ('sphere', 45, 27, 12, 6, 0.4), [0.99, 0.8, 0.5, 0.2, -9]),
}
FLAT = {'n': '5', 'e': 'e', 'p': 'b', 'o': '6', 'l': 'v', 'k': 'k', 'u': 'u'}
LINE_ON = {  # (a, b): paint line on pixel of region a when adjacent to region b
    ('h', 'f'): 'k', ('h', 'n'): 'k', ('d', 'f'): 'k', ('m', 'f'): 'k', ('h', 'r'): 'k',
    ('d', 'm'): '5', ('d', 'l'): '5', ('d', 'o'): 'k', ('m', 'o'): 'k', ('r', 'd'): 'k', ('d', 'r'): 'k',
    ('h', 'd'): None,
}


def region_masks():
    g = headmap.grid
    regs = {}
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            x, y = headmap.X0 + c, headmap.Y0 + r
            regs.setdefault(ch, empty())[y][x] = True
    return regs


def render_head(cv, overlay=None):
    regs = region_masks()
    lab = [[None] * W for _ in range(H)]
    for ch, m in regs.items():
        for y in range(H):
            for x in range(W):
                if m[y][x]:
                    lab[y][x] = ch
    allm = union(*regs.values())
    # outline outside silhouette
    for y in range(H):
        for x in range(W):
            if allm[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and allm[yy][xx]:
                    cv.px[y][x] = BLACK
                    break
    for ch, m in regs.items():
        if ch in MODELS:
            ramp, model, th = MODELS[ch]
            idx = shade_idx(m, model, th)
            rp = [hexc(c) for c in RAMPS[ramp]]
            for y in range(H):
                for x in range(W):
                    if m[y][x]:
                        cv.px[y][x] = rp[min(idx[y][x], len(rp) - 1)]
        else:
            cv.paint(m, PALC[FLAT[ch]])
    # internal boundary lines
    paint = []
    for y in range(H):
        for x in range(W):
            a = lab[y][x]
            if a is None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    b = lab[yy][xx]
                    if b is not None and b != a and LINE_ON.get((a, b)):
                        paint.append((x, y, LINE_ON[(a, b)]))
                        break
    for x, y, ch in paint:
        cv.set(x, y, ch)
    if overlay:
        cv.stamp(overlay, headmap.X0, headmap.Y0, over_only=True)
    return allm


if __name__ == '__main__':
    import sys
    from pngio import crop, scale, write_png
    FL = (136, 180, 99, 255)
    cv = Canvas()
    try:
        from headstrokes import STROKES
    except ImportError:
        STROKES = None
    render_head(cv, STROKES if '--strokes' in sys.argv else None)
    px = cv.rgba()
    z = scale(crop(px, 28, 1, 40, 56), 14, FL)
    write_png('head14x.png', len(z[0]), len(z), z)
    z = scale(crop(px, 28, 1, 40, 56), 3, FL)
    write_png('head3x.png', len(z[0]), len(z), z)
