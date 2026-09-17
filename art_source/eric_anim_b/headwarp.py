"""Turned heads: warp the approved head region map (headmap.py) + strokes around per-row cross-sections,
then render with the same region shading / boundary-line rules as headrender.py."""
import math
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, hexc, RAMPS
import headmap
import headstrokes
import headrender as HR

X0, Y0, HW, HH = headmap.X0, headmap.Y0, headmap.HW, headmap.HH   # 30, 3, 36, 52
GRID = headmap.grid
STROKES = headstrokes.STROKES.split('\n')
CX = 48.0   # head axis (screen x)


def row_extent(r):
    """half width of the head (no ears) at grid row r, about CX"""
    row = GRID[r]
    cols = [c for c, ch in enumerate(row) if ch not in '.r']
    if not cols:
        return None
    x0, x1 = X0 + min(cols), X0 + max(cols) + 1
    return max(CX - x0, x1 - CX)


def section(y):
    """(R, Df, Db, Zc) per screen row y (96-space)"""
    r = y - Y0
    R = row_extent(r)
    if R is None:
        return None
    if y <= 25:                      # cranium + face
        Df = R * 0.98
        Db = R * 1.12
        Zc = -1.0
    elif y <= 30:                    # jaw / sideburns into beard
        Df = R * 1.05
        Db = R * 0.95
        Zc = -0.5
    elif y <= 44:                    # beard body juts forward over the chest
        k = (y - 30) / 14.0
        Df = R * (1.05 + 0.18 * math.sin(k * math.pi)) + 2.0 * k
        Db = max(7.5, R * (0.72 - 0.25 * k))
        Zc = 1.0 + 3.0 * k
    else:                            # beard tip hangs forward and down
        k = (y - 44) / 8.0
        Df = max(3.0, R * 1.3)
        Db = max(2.0, R * 0.9)
        Zc = 4.0 + 6.0 * k
    return R, Df, Db, Zc


def nose_bump(y, X):
    if 20 <= y <= 26:
        h = {20: 0.6, 21: 1.0, 22: 1.4, 23: 1.8, 24: 2.3, 25: 2.6, 26: 1.2}[y]
        return h * max(0.0, 1.0 - abs(X) / 2.2)
    return 0.0


def warp(yaw, side=1):
    """returns region grid dict (x,y)->ch and strokes dict (x,y)->ch in 96-space"""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    reg, strokes = {}, {}
    for y in range(Y0, Y0 + HH):
        sec = section(y)
        if sec is None:
            continue
        R, Df, Db, Zc = sec
        best = {}
        nt = 720
        for i in range(nt):
            t = 2 * math.pi * i / nt
            ct, st = math.cos(t), math.sin(t)
            X = R * ct
            Z = Zc + (Df if st >= 0 else Db) * st
            if st > 0:
                Z += nose_bump(y, X)
            xo = X * c + Z * s
            d = -X * s + Z * c
            px = int(math.floor(CX + side * xo))
            if px not in best or d > best[px][0]:
                best[px] = (d, X, Z, st)
        for px, (d, X, Z, st) in best.items():
            if st >= 0 and yaw > 110 and y > 33:
                continue
            if st >= 0:
                col = int(math.floor(CX + X - X0))
                col = max(0, min(HW - 1, col))
                ch = GRID[y - Y0][col]
                if ch in '.r':
                    # silhouette sample landed on an ear/empty column of the front map: use nearest body region
                    for dc in (1, -1, 2, -2, 3, -3):
                        cc = col + (dc if X < 0 else -dc)
                        if 0 <= cc < HW and GRID[y - Y0][cc] not in '.r':
                            ch = GRID[y - Y0][cc]
                            break
                if ch in '.r':
                    continue
                reg[(px, y)] = ch
                sk = STROKES[y - Y0][col]
                if sk != '.':
                    strokes[(px, y)] = sk
            else:
                if y <= 28:
                    ch = 'h'
                elif y <= 33 and abs(X) > 9.5:
                    ch = 'd'
                elif y <= 30:
                    ch = 'h'
                else:
                    continue            # neck / beard behind the body: left to the gorget, pauldrons and cape
                reg[(px, y)] = ch
                if ch == 'h':
                    tdeg = math.degrees(math.atan2(Z, X)) % 360
                    band = (tdeg + (y - 4) * 1.3) % 24
                    if band < 1.6:
                        strokes[(px, y)] = '-'
                    elif band < 3.0 and y < 24:
                        strokes[(px, y)] = '+'
    # ears: flat-ish discs on the skull sides, rows 20-25; wider when they face the camera
    FLAT_W = [3, 4, 5, 5, 4, 3]
    EDGE_W = [2, 3, 3, 3, 3, 2]
    for sgn in (-1, 1):
        dface = -sgn * s * side * side
        if yaw == 0:
            dface = 0.0
        if dface < -0.25:
            continue
        k = max(0.0, min(1.0, dface))
        for i, y in enumerate(range(20, 26)):
            R = row_extent(y - Y0) or 13
            Xe, Ze = sgn * (R + 1.0), -1.5
            xo = Xe * c + Ze * s
            w = EDGE_W[i] + (FLAT_W[i] - EDGE_W[i]) * k
            xc = CX + side * xo
            # the ear hangs off the skull: shift its centre outward by half its width when edge-on
            out = side * sgn * c * (w / 2.0 - 0.5)
            xc += out
            for px in range(int(math.floor(xc - w / 2.0 + 0.5)), int(math.floor(xc + w / 2.0 + 0.5))):
                if reg.get((px, y)) in (None, 'h'):
                    reg[(px, y)] = 'r'
                    strokes.pop((px, y), None)
    return reg, strokes


MODELS = HR.MODELS


def regions(yaw, side=1):
    import headhand as HH
    if yaw in (90, 135, 180):
        rows, st = {90: HH.profile, 135: HH.back34, 180: HH.back}[yaw]()
        reg = HH.to_regions(rows)
        if side < 0:
            reg = {(95 - x, y): ch for (x, y), ch in reg.items()}
            st = {(95 - x, y): ch for (x, y), ch in st.items()}
        # strokes only on painted pixels of hair/beard/face regions
        st = {k: v for k, v in st.items() if k in reg and reg[k] in 'hdmfr'}
        return reg, st
    return warp(yaw, side)


def render(cv, yaw, side=1, extra_strokes=None):
    reg, strokes = regions(yaw, side)
    s = math.sin(math.radians(yaw)) * side
    shift = {'h': 0.0, 'f': 11.0, 'r': 0.0, 'd': 8.0, 'm': 10.0}
    regs = {}
    for (x, y), ch in reg.items():
        if 0 <= x < 96 and 0 <= y < 96:
            regs.setdefault(ch, lib.empty())[y][x] = True
    lab = [[None] * 96 for _ in range(96)]
    for (x, y), ch in reg.items():
        if 0 <= x < 96:
            lab[y][x] = ch
    allm = lib.union(*regs.values())
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
        if ch in MODELS:
            ramp, model, th = MODELS[ch]
            model = list(model)
            model[1] = model[1] + shift.get(ch, 0.0) * s
            if ch == 'r':
                model[1] = sum(x for y in range(96) for x in range(96) if m[y][x]) / max(1, sum(sum(r) for r in m)) - 1
            idx = lib.shade_idx(m, tuple(model), th)
            rp = [hexc(cc) for cc in RAMPS[ramp]]
            for y in range(96):
                for x in range(96):
                    if m[y][x]:
                        cv.px[y][x] = rp[min(idx[y][x], len(rp) - 1)]
        else:
            cv.paint(m, PALC[HR.FLAT[ch]])
    paint = []
    for y in range(96):
        for x in range(96):
            a = lab[y][x]
            if a is None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 96 and 0 <= yy < 96:
                    b = lab[yy][xx]
                    if b is not None and b != a and HR.LINE_ON.get((a, b)):
                        paint.append((x, y, HR.LINE_ON[(a, b)]))
                        break
    for x, y, ch in paint:
        cv.set(x, y, ch)
    allst = dict(strokes)
    if extra_strokes:
        allst.update(extra_strokes)
    for (x, y), ch in allst.items():
        if not (0 <= x < 96 and 0 <= y < 96):
            continue
        cur = cv.px[y][x]
        if cur is None:
            continue
        if ch == '-':
            cv.px[y][x] = _DARKER.get(cur, cur)
        elif ch == '+':
            cv.px[y][x] = _LIGHTER.get(cur, cur)
        else:
            cv.px[y][x] = PALC[ch]
    return reg
