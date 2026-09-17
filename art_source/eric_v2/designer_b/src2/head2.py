"""v2 turned heads: the v1 turned region maps (headwarp / headhand) resampled at head scale HS about the neck,
face features re-authored at the new size, rendered like designer A's head_s (scaled shading models)."""
import math
import lib
from lib import PALC, BLACK, empty, union, shade_idx, hexc, RAMPS
import headrender as HR
import headwarp as HW1

S, HS = 0.80, 0.84
A = (48.0, 40.0)
A2 = (48.0, 96 + (40 - 96) * S)


def HT(x, y):
    return (A2[0] + (x - A[0]) * HS, A2[1] + (y - A[1]) * HS)


def HTinv(X, Y):
    return (A[0] + (X - A2[0]) / HS, A[1] + (Y - A2[1]) / HS)


def resample(lab):
    out = {}
    for Y in range(96):
        for X in range(96):
            sx, sy = HTinv(X + 0.5, Y + 0.5)
            k = (int(math.floor(sx)), int(math.floor(sy)))
            if k in lab:
                out[(X, Y)] = lab[k]
    return out


def resample_strokes(st, lab):
    out = {}
    for (x, y), ch in st.items():
        X, Y = HT(x + 0.5, y + 0.5)
        k = (int(math.floor(X)), int(math.floor(Y)))
        if k in lab and k not in out:
            out[k] = ch
    return out


# face fixes for the right-facing views: {row: (x0, 'chars')}, '?' keeps, '.' clears
FIX = {
    45: {
        32: (47, "fffffffffffh"),
        33: (47, "nnfffffffnnf"),
        34: (47, "fnnnffffnnnf"),
        35: (47, "fkkknnffnkkk"),
        36: (47, "feppkfffkppf"),
        37: (47, "fuuufffffuuf"),
        38: (47, "ffffffffffffff"),
        39: (47, "fffffffffffffff"),
        43: (51, "mmmmmkkkkmmm"),
        44: (51, "mmmmmddddmmd"),
    },
    90: {},
}


def labels(yaw, side=1):
    reg, st = HW1.regions(yaw, 1)
    lab = resample(reg)
    for y, (x0, s) in FIX.get(yaw, {}).items():
        for i, ch in enumerate(s):
            k = (x0 + i, y)
            if ch == '.':
                lab.pop(k, None)
            elif ch != '?':
                lab[k] = ch
    strokes = resample_strokes(st, lab)
    if side < 0:
        lab = {(95 - x, y): ch for (x, y), ch in lab.items()}
        strokes = {(95 - x, y): ch for (x, y), ch in strokes.items()}
    return lab, strokes


SHIFT = {'h': 0.0, 'f': 11.0, 'r': 0.0, 'd': 8.0, 'm': 10.0}


def render(cv, yaw, side=1):
    lib.W = lib.H = 96
    lab, strokes = labels(yaw, side)
    s = math.sin(math.radians(yaw)) * side
    regs = {}
    for (x, y), ch in lab.items():
        if 0 <= x < 96 and 0 <= y < 96:
            regs.setdefault(ch, empty())[y][x] = True
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
        if ch in HR.MODELS:
            ramp, model, th = HR.MODELS[ch]
            cx, cy = model[1] + SHIFT.get(ch, 0.0) * s, model[2]
            X, Y = HT(cx, cy)
            mdl = ('sphere', X, Y, model[3] * HS, model[4] * HS) + tuple(model[5:])
            if ch == 'r':
                n = max(1, sum(sum(r) for r in m))
                mx = sum(x for y in range(96) for x in range(96) if m[y][x]) / n
                mdl = ('sphere', mx - 1, Y, model[3] * HS, model[4] * HS) + tuple(model[5:])
            idx = shade_idx(m, mdl, th)
            rp = [hexc(c) for c in RAMPS[ramp]]
            for y in range(96):
                for x in range(96):
                    if m[y][x]:
                        cv.px[y][x] = rp[min(idx[y][x], len(rp) - 1)]
        else:
            cv.paint(m, PALC[HR.FLAT[ch]])
    paint = []
    for (x, y), a in lab.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            b = lab.get((x + dx, y + dy))
            if b is not None and b != a and HR.LINE_ON.get((a, b)):
                paint.append((x, y, HR.LINE_ON[(a, b)]))
                break
    for x, y, ch in paint:
        cv.set(x, y, ch)
    for (x, y), ch in strokes.items():
        if lab.get((x, y)) in ('e', 'p', 'k', 'n', 'o', 'l', 'u'):
            continue
        cur = cv.px[y][x]
        if cur is None or cur == BLACK:
            continue
        if ch == '-':
            cv.px[y][x] = lib._DARKER.get(cur, cur)
        elif ch == '+':
            cv.px[y][x] = lib._LIGHTER.get(cur, cur)
        else:
            cv.px[y][x] = PALC[ch]
    return lab
