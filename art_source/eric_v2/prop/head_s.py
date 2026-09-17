"""Head redrawn at head scale HS: region labels resampled, then face features re-placed by hand,
shading/outlines/strokes regenerated at the new size."""
import math
import scaled as SC
import lib
from lib import PALC, BLACK, empty, union, shade_idx, hexc, RAMPS
import headmap
import headrender
from headstrokes import STROKES

HS = SC.HS
A = (48.0, 40.0)                  # source neck anchor
A2 = SC.T(48.0, 40.0)             # where the body scale puts it


def HT(x, y):
    return (A2[0] + (x - A[0]) * HS, A2[1] + (y - A[1]) * HS)


def HTinv(X, Y):
    return (A[0] + (X - A2[0]) / HS, A[1] + (Y - A2[1]) / HS)


def resample_labels():
    g = headmap.grid
    X0, Y0 = headmap.X0, headmap.Y0
    lab = {}
    for Y in range(0, 96):
        for X in range(0, 96):
            sx, sy = HTinv(X + 0.5, Y + 0.5)
            c, r = int(math.floor(sx)) - X0, int(math.floor(sy)) - Y0
            if 0 <= r < len(g) and 0 <= c < len(g[0]):
                ch = g[r][c]
                if ch != '.':
                    lab[(X, Y)] = ch
    return lab


def bbox(lab):
    xs = [x for x, y in lab]
    ys = [y for x, y in lab]
    return min(xs), min(ys), max(xs), max(ys)


def to_rows(lab):
    x0, y0, x1, y1 = bbox(lab)
    rows = []
    for y in range(y0, y1 + 1):
        rows.append(''.join(lab.get((x, y), '.') for x in range(x0, x1 + 1)))
    return x0, y0, rows


# hand re-authored face region (local to the resampled bbox), applied after resampling
FACE_FIX = (34, 21, ['?' * 28] * 12 + [
    '??????nnffffffffffffnn??????',  # 12 brow outer ends
    '??????fnnnffffffffnnnf??????',  # 13 brows slope down toward the nose
    '??????fkkknnffffnnkkkf??????',  # 14 upper lids, brow inner ends dip to the eyes (glare)
    '??????feppkffffffkppef??????',  # 15 eye white + 2px pupils looking forward
    '??????fuuuffffffffuuuf??????',  # 16 under-eye crease
] + ['?' * 28] * 6 + [
    '??????????mkkkkkkm??????????',  # 23 grim closed mouth line under the moustache
])


def labels():
    lab = resample_labels()
    if FACE_FIX:
        x0, y0, rows = FACE_FIX
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                key = (x0 + c, y0 + r)
                if ch == '.':
                    lab.pop(key, None)
                elif ch != '?':
                    lab[key] = ch
    return lab


def _head_normals(mask, model):
    k = model[0]
    if k == 'sphere':
        _, cx, cy, rx, ry = model[:5]
        x, y = HT(cx, cy)
        model = ('sphere', x, y, rx * HS, ry * HS) + tuple(model[5:])
    return SC._orig_normals(mask, model)


def render(cv, strokes=True):
    lab = labels()
    regs = {}
    for (x, y), ch in lab.items():
        regs.setdefault(ch, empty())[y][x] = True
    saved = lib.normals
    lib.normals = _head_normals
    try:
        allm = union(*regs.values())
        for y in range(96):
            for x in range(96):
                if allm[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 96 and 0 <= yy < 96 and allm[yy][xx]:
                        cv.px[y][x] = BLACK
                        break
        for ch, m in regs.items():
            if ch in headrender.MODELS:
                ramp, model, th = headrender.MODELS[ch]
                idx = shade_idx(m, model, th)
                rp = [hexc(c) for c in RAMPS[ramp]]
                for y in range(96):
                    for x in range(96):
                        if m[y][x]:
                            cv.px[y][x] = rp[min(idx[y][x], len(rp) - 1)]
            else:
                cv.paint(m, PALC[headrender.FLAT[ch]])
        paint = []
        for (x, y), a in lab.items():
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                b = lab.get((x + dx, y + dy))
                if b is not None and b != a and headrender.LINE_ON.get((a, b)):
                    paint.append((x, y, headrender.LINE_ON[(a, b)]))
                    break
        for x, y, ch in paint:
            cv.set(x, y, ch)
        if strokes:
            rows = STROKES.split('\n')
            done = set()
            for r, row in enumerate(rows):
                for c, ch in enumerate(row):
                    if ch == '.':
                        continue
                    X, Y = HT(headmap.X0 + c + 0.5, headmap.Y0 + r + 0.5)
                    X, Y = int(math.floor(X)), int(math.floor(Y))
                    if (X, Y) in done or (X, Y) not in lab:
                        continue
                    if lab[(X, Y)] in ('e', 'p', 'k', 'n', 'o'):
                        continue
                    done.add((X, Y))
                    cur = cv.px[Y][X]
                    if cur is None or cur == BLACK:
                        continue
                    if ch == '-':
                        cv.px[Y][X] = lib._DARKER.get(cur, cur)
                    elif ch == '+':
                        cv.px[Y][X] = lib._LIGHTER.get(cur, cur)
                    else:
                        cv.px[Y][X] = PALC[ch]
    finally:
        lib.normals = saved
    return lab


if __name__ == '__main__':
    lab = resample_labels()
    x0, y0, rows = to_rows(lab)
    print('origin', x0, y0, 'size', len(rows[0]), len(rows))
    for i, r in enumerate(rows):
        print('%2d %s' % (i, r))
