"""Mason animation rig.

Every rule here is ported from detail.py (the approved static sprite) but is
evaluated in the local frame of whichever part owns the pixel. At the neutral
pose all offsets are zero and the output must equal mason.png exactly - that is
checked in build.py before anything else is trusted.
"""
import math

W = H = 64

# ----- palette (approved) ----------------------------------------------------
CREAM      = '#EEC39A'
CREAM_HI   = '#FADCB8'
CREAM_MID  = '#D6AA7C'
CREAM_DEEP = '#AE8358'
FACE_LIT   = '#90765E'
FACE_SHAD  = '#7D5631'
RED        = '#AC3232'
RED_HI     = '#D95763'
YEL        = '#FBF236'
YEL_MID    = '#D4CC2E'
YEL_DEEP   = '#726E17'
WHITE      = '#FFFFFF'
KHAKI      = '#A09050'
KHAKI_DK   = '#605020'
BLACK      = '#000000'

WINGS = ('wing_r', 'wing_l')
LOWER = ('foot_r', 'foot_l', 'leg_r', 'leg_l')

def rh(v):
    return math.floor(v + 0.5)

# ----- rasteriser: proven identical to Aseprite draw_contour + fill_area ------
def bres(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts

def raster(poly):
    line = set()
    for i in range(len(poly)):
        a = poly[i]; b = poly[(i + 1) % len(poly)]
        line.update(bres(a[0], a[1], b[0], b[1]))
    ext = set()
    stack = [(x, y) for x in range(-1, W + 1) for y in (-1, H)] + \
            [(x, y) for y in range(-1, H + 1) for x in (-1, W)]
    while stack:
        p = stack.pop()
        if p in ext or p in line: continue
        x, y = p
        if not (-1 <= x <= W and -1 <= y <= H): continue
        ext.add(p)
        stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    inter = {(x, y) for x in range(W) for y in range(H)} - ext - line
    line = {(x, y) for (x, y) in line if 0 <= x < W and 0 <= y < H}
    return line, inter

# ----- neutral silhouette, right half then left half, clockwise ---------------
HOOD_R     = [(32,6),(36,6),(39,7),(42,9),(44,12),(45,16),(45,20),(44,24),(42,28),(41,30)]
SHOULDER_R = [(44,32),(47,34),(49,36),(51,39)]
WING_R     = [(55,39),(58,41),(60,44),(59,47),(56,48),(52,46)]
WING_R_OFF = [(52,43)]                       # body edge when the wing is elsewhere
BODYLOW_R  = [(52,48),(51,50),(49,51),(46,52),(43,53)]
LEGOUT_R   = [(42,53),(42,57)]
FOOT_R     = [(46,57),(49,58),(51,60),(51,63),(34,63),(34,58)]
LEGIN_R    = [(35,57),(35,53)]
CROTCH_R   = [(33,52),(32,52)]

def mirror(pts):
    return [(63 - x, y) for (x, y) in reversed(pts)]

CROTCH_L   = mirror(CROTCH_R)
LEGIN_L    = mirror(LEGIN_R)
FOOT_L     = mirror(FOOT_R)
LEGOUT_L   = mirror(LEGOUT_R)
BODYLOW_L  = mirror(BODYLOW_R)
WING_L     = mirror(WING_R)
WING_L_OFF = mirror(WING_R_OFF)
SHOULDER_L = mirror(SHOULDER_R)
HOOD_L     = mirror(HOOD_R)

# wing root arc (right wing); left wing uses the mirror
ARC = {38: 51, 39: 50, 40: 49, 41: 49, 42: 49, 43: 49, 44: 49, 45: 50, 46: 51, 47: 52}
TICKS = [(20, 36), (17, 43), (24, 46), (14, 47), (22, 50), (26, 33),
         (23, 41), (27, 48), (19, 39), (25, 37), (16, 48)]
COMB_TOP = {21:7, 22:5, 23:4, 24:3, 25:3, 26:3, 27:4, 28:3, 29:2, 30:1, 31:1,
            32:1, 33:1, 34:2, 35:3, 36:4, 37:3, 38:3, 39:3, 40:4, 41:5, 42:7}
COMB_BOT = {21:10, 22:9, 23:9, 24:9, 25:8, 26:8, 27:8, 28:8, 29:7, 30:7, 31:7,
            32:7, 33:7, 34:7, 35:8, 36:8, 37:8, 38:8, 39:9, 40:9, 41:9, 42:10}
RING_OUT_L = {10:28, 11:26, 12:24, 13:23, 14:22, 15:21, 16:21, 17:21, 18:21, 19:21,
              20:21, 21:21, 22:21, 23:22, 24:22, 25:23, 26:23, 27:24, 28:25, 29:26, 30:27}
FACE_IN_L  = {14:29, 15:27, 16:26, 17:26, 18:26, 19:26, 20:26, 21:26, 22:26, 23:27,
              24:27, 25:28, 26:29, 27:30}
PLUS = [(0,-1),(0,0),(0,1),(-1,0),(1,0)]
EX   = [(-1,-1),(1,-1),(0,0),(-1,1),(1,1)]

# ----- lighting (approved) -----------------------------------------------------
_L = (-0.50, -0.62, 0.60)
_n = math.sqrt(sum(c * c for c in _L))
LX, LY, LZ = _L[0] / _n, _L[1] / _n, _L[2] / _n

def lum(x, y, cx, cy, rx, ry):
    nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
    d2 = nx * nx + ny * ny
    if d2 > 1.0:
        s = math.sqrt(d2); nx, ny, nz = nx / s, ny / s, 0.0
    else:
        nz = math.sqrt(1.0 - d2)
    return nx * LX + ny * LY + nz * LZ

def band(v, th):
    if v > th[0]: return CREAM_HI
    if v > th[1]: return CREAM
    if v > th[2]: return CREAM_MID
    return CREAM_DEEP

STEP = {CREAM_HI: CREAM, CREAM: CREAM_MID, CREAM_MID: CREAM_DEEP, CREAM_DEEP: CREAM_DEEP}
TH = None          # frozen from the neutral pose on first render (see freeze_thresholds)

NEUTRAL = dict(
    body=(0, 0, 1.0, 1.0),   # dx, dy, scale x, scale y (about x=31.5, y=53)
    shear=0.0,               # upper-body lean: x += shear * (53 - y)
    head=(0, 0),             # relative to where the body carries it
    wing_r=(0, 0), wing_l=(0, 0),
    wing_r_mode='side', wing_l_mode='side',
    foot_r=(0, 0), foot_l=(0, 0),
    sym=True,
    face='grin',
    googly='normal',
    sections={},             # name -> absolute point list, replaces a section
    feet_detached=False,     # feet drawn as separate pieces (slumped poses)
    under=[],                # callables drawn before the head features
    over=[],                 # callables drawn last
)

# ------------------------------------------------------------------------------
class Ctx:
    pass

def make_ctx(pose):
    P = dict(NEUTRAL); P.update(pose)
    c = Ctx(); c.P = P
    bdx, bdy, sx, sy = P['body']
    c.bdx, c.bdy, c.sx, c.sy = bdx, bdy, sx, sy
    c.shear = P['shear']
    c.head = (bdx + rh(c.shear * 23) + P['head'][0], bdy + rh((30 - 53) * (sy - 1)) + P['head'][1])
    wroot = rh(20 * (sx - 1))
    wy = bdy + rh((43 - 53) * (sy - 1))
    wsh = rh(c.shear * 10)
    c.wing_r = (bdx + wroot + wsh + P['wing_r'][0], wy + P['wing_r'][1])
    c.wing_l = (bdx - wroot + wsh + P['wing_l'][0], wy + P['wing_l'][1])
    c.foot_r = P['foot_r']; c.foot_l = P['foot_l']
    return c

def tb(c, p):
    x = 31.5 + (p[0] - 31.5) * c.sx
    x = math.floor(x + 0.5) if x >= 31.5 else math.ceil(x - 0.5)
    y = rh(53 + (p[1] - 53) * c.sy)
    return (x + c.bdx + rh(c.shear * (53 - y)), y + c.bdy)

def tt(p, off):
    return (p[0] + off[0], p[1] + off[1])

def build_poly(c):
    P = c.P
    S = []   # (name, points)
    S.append(('hood_r', [tt(p, c.head) for p in HOOD_R]))
    S.append(('shoulder_r', [tb(c, p) for p in SHOULDER_R]))
    if P['wing_r_mode'] == 'side':
        S.append(('wing_r', [tt(p, c.wing_r) for p in WING_R]))
    else:
        S.append(('wing_r', [tb(c, p) for p in WING_R_OFF]))
    S.append(('bodylow_r', [tb(c, p) for p in BODYLOW_R]))
    if P['feet_detached']:
        S.append(('under', []))
    else:
        S.append(('leg_r', [tb(c, LEGOUT_R[0]), tt(LEGOUT_R[1], c.foot_r)]
                  + [tt(p, c.foot_r) for p in FOOT_R]
                  + [tt(LEGIN_R[0], c.foot_r), tb(c, LEGIN_R[1])]))
        S.append(('crotch', [tb(c, p) for p in CROTCH_R] + [tb(c, p) for p in CROTCH_L]))
        S.append(('leg_l', [tb(c, LEGIN_L[0]), tt(LEGIN_L[1], c.foot_l)]
                  + [tt(p, c.foot_l) for p in FOOT_L]
                  + [tt(LEGOUT_L[0], c.foot_l), tb(c, LEGOUT_L[1])]))
    S.append(('bodylow_l', [tb(c, p) for p in BODYLOW_L]))
    if P['wing_l_mode'] == 'side':
        S.append(('wing_l', [tt(p, c.wing_l) for p in WING_L]))
    else:
        S.append(('wing_l', [tb(c, p) for p in WING_L_OFF]))
    S.append(('shoulder_l', [tb(c, p) for p in SHOULDER_L]))
    S.append(('hood_l', [tt(p, c.head) for p in HOOD_L]))
    poly = []
    for name, pts in S:
        poly += P['sections'].get(name, pts)
    return poly

def owner_fn(c):
    P = c.P
    fr, fl = c.foot_r, c.foot_l
    hx_, hy_ = c.head
    wrx, wry = c.wing_r
    wlx, wly = c.wing_l
    mid = 31.5 + c.bdx
    det = P['feet_detached']
    def owner(x, y):
        if not det:
            if y - fr[1] >= 57 and x - fr[0] >= 32: return 'foot_r'
            if y - fl[1] >= 57 and x - fl[0] <= 31: return 'foot_l'
            if y >= 53 + c.bdy:
                if x >= mid and y <= 56 + fr[1]: return 'leg_r'
                if x < mid and y <= 56 + fl[1]: return 'leg_l'
        if P['wing_r_mode'] == 'side':
            ly = y - wry
            if ly in ARC and x - wrx > ARC[ly]: return 'wing_r'
        if P['wing_l_mode'] == 'side':
            ly = y - wly
            if ly in ARC and 63 - (x - wlx) > ARC[ly]: return 'wing_l'
        if y - hy_ <= 29: return 'hood'
        return 'body'
    return owner

def shade_value(c, o, x, y):
    hx_, hy_ = c.head
    if o == 'wing_r':
        return 'wing', lum(x - c.wing_r[0], y - c.wing_r[1], 56.0, 43.0, 7.0, 7.0)
    if o == 'wing_l':
        return 'wing', lum(x - c.wing_l[0], y - c.wing_l[1], 7.0, 43.0, 7.0, 7.0)
    vh = lum(x - hx_, y - hy_, 31.5, 20.0, 15.0, 15.0)
    if o == 'hood':
        return 'hood', vh
    vb = lum(x - c.bdx - c.shear * 11, y - c.bdy, 31.5, 53 + (42 - 53) * c.sy, 23.0 * c.sx, 23.0 * c.sy)
    ly = y - hy_
    if ly >= 34:
        return 'body', vb
    t = (ly - 29) / 5.0
    return 'body', vh * (1 - t) + vb * t

def freeze_thresholds():
    global TH
    c = make_ctx({})
    line, inter = raster(build_poly(c))
    inter = {(x, y) for (x, y) in inter if x <= 31} | {(63 - x, y) for (x, y) in inter if x <= 31}
    owner = owner_fn(c)
    vals = {'hood': [], 'body': [], 'wing': []}
    for (x, y) in inter:
        o = owner(x, y)
        if o in LOWER: continue
        g, v = shade_value(c, o, x, y)
        vals[g].append(v)
    def qb(vs, fracs):
        s = sorted(vs); n = len(s); out = []; acc = 0.0
        for f in fracs:
            acc += f
            out.append(s[min(n - 1, int(n * (1.0 - acc)))])
        return out
    TH = {'hood': qb(vals['hood'], (0.17, 0.36, 0.32)),
          'body': qb(vals['body'], (0.15, 0.37, 0.33)),
          'wing': qb(vals['wing'], (0.22, 0.40, 0.30))}
    return TH

# ------------------------------------------------------------------------------
def render(pose):
    if TH is None: freeze_thresholds()
    c = make_ctx(pose); P = c.P
    line, inter = raster(build_poly(c))
    if P['sym']:
        line = {(x, y) for (x, y) in line if x <= 31} | {(63 - x, y) for (x, y) in line if x <= 31}
        inter = {(x, y) for (x, y) in inter if x <= 31} | {(63 - x, y) for (x, y) in inter if x <= 31}
    base = {}
    for p in line: base[p] = BLACK
    for p in inter: base[p] = CREAM
    px = {}
    def put(x, y, col):
        if 0 <= x < W and 0 <= y < H: px[(x, y)] = col
    def cur(x, y):
        return px.get((x, y), base.get((x, y)))
    owner = owner_fn(c)
    own = {p: owner(*p) for p in inter}
    c.put, c.cur, c.inter, c.own, c.base, c.px = put, cur, inter, own, base, px
    hx_, hy_ = c.head

    # 1. volume shading
    for (x, y), o in own.items():
        if o in LOWER: continue
        g, v = shade_value(c, o, x, y)
        col = band(v, TH[g])
        if col != CREAM: put(x, y, col)

    # hood's soft shadow on the body
    for lx in range(19, 45):
        t = (lx - 31.5) / 13.0
        if abs(t) > 1: continue
        sy_ = 31 + int(round(2.0 * math.sqrt(1 - t * t)))
        for dy_ in (0, 1):
            x, y = lx + hx_, sy_ + dy_ + hy_
            if (x, y) in inter and own[(x, y)] not in WINGS:
                col = cur(x, y); put(x, y, STEP.get(col, col))

    # 2. feather ticks (body-local, mirrored)
    for (tx, ty) in TICKS:
        la = tb(c, (tx, ty)); ra = tb(c, (63 - tx, ty))
        for (dx_, dy_) in ((0, 0), (1, 1)):
            for (x, y) in ((la[0] + dx_, la[1] + dy_), (ra[0] - dx_, ra[1] + dy_)):
                if (x, y) in inter and own[(x, y)] == 'body':
                    put(x, y, CREAM_MID)

    # 3. wing roots, contact shadows, grooves
    for y_, ax in ARC.items():
        if P['wing_r_mode'] == 'side':
            x, y = ax + c.wing_r[0], y_ + c.wing_r[1]
            if (x, y) in inter: put(x, y, BLACK)
        if P['wing_l_mode'] == 'side':
            x, y = 63 - ax + c.wing_l[0], y_ + c.wing_l[1]
            if (x, y) in inter: put(x, y, BLACK)
        if P['wing_r_mode'] == 'side':
            x, y = ax - 1 + c.wing_r[0], y_ + c.wing_r[1]
            if (x, y) in inter and own[(x, y)] not in WINGS: put(x, y, CREAM_DEEP)
        if P['wing_l_mode'] == 'side':
            x, y = 63 - ax + 1 + c.wing_l[0], y_ + c.wing_l[1]
            if (x, y) in inter and own[(x, y)] not in WINGS: put(x, y, CREAM_MID)
    for (gx, gy) in [(56, 41), (57, 42), (55, 44), (56, 45)]:
        if P['wing_r_mode'] == 'side':
            x, y = gx + c.wing_r[0], gy + c.wing_r[1]
            if (x, y) in inter: put(x, y, CREAM_MID)
        if P['wing_l_mode'] == 'side':
            x, y = 63 - gx + c.wing_l[0], gy + c.wing_l[1]
            if (x, y) in inter: put(x, y, CREAM_MID)

    # 4. legs: khaki, shadow on each row's right-most pixel
    for side in ('leg_r', 'leg_l'):
        rows = {}
        for (x, y), o in own.items():
            if o == side: rows.setdefault(y, []).append(x)
        for y, xs in rows.items():
            for x in xs: put(x, y, KHAKI)
            put(max(xs), y, KHAKI_DK)

    # 5. feet
    if not P['feet_detached']:
        paint_feet(c)

    for fn in P['under']: fn(c)

    # 6-10. head: comb, beak ring, face, googly eyes
    paint_head(c)

    for fn in P['over']: fn(c)

    grid = [[(0, 0, 0, 0)] * W for _ in range(H)]
    grid = [row[:] for row in grid]
    for (x, y), col in base.items():
        grid[y][x] = hex2rgba(col)
    for (x, y), col in px.items():
        grid[y][x] = hex2rgba(col) if col is not None else (0, 0, 0, 0)
    return grid

def hex2rgba(h):
    if len(h) == 9:
        return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), int(h[7:9], 16))
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)

# ------------------------------------------------------------------------------
def paint_feet(c):
    put, cur, own = c.put, c.cur, c.own
    for side, f, legcols, toes, outer in (
            ('foot_r', c.foot_r, range(36, 42), (41, 46), lambda lx: lx >= 47),
            ('foot_l', c.foot_l, range(22, 28), (22, 17), lambda lx: lx <= 16)):
        for (x, y), o in own.items():
            if o != side: continue
            lx, ly = x - f[0], y - f[1]
            if ly == 57: put(x, y, KHAKI if lx in legcols else BLACK)
            elif ly >= 58: put(x, y, YEL)
        for tx in toes:
            for ly in range(59, 64):
                x, y = tx + f[0], ly + f[1]
                if own.get((x, y)) == side: put(x, y, BLACK)
            x, y = tx + f[0], 58 + f[1]
            if own.get((x, y)) == side: put(x, y, YEL_DEEP)
        for (x, y), o in own.items():
            if o != side: continue
            lx, ly = x - f[0], y - f[1]
            if ly >= 58 and cur(x, y) == YEL:
                if ly >= 62 or outer(lx): put(x, y, YEL_MID)

def paint_head(c):
    P = c.P; put = c.put
    hx_, hy_ = c.head
    # comb
    for x, t in COMB_TOP.items():
        b = COMB_BOT[x]
        for y in range(t, b + 1):
            put(x + hx_, y + hy_, BLACK if (y == t or y == b) else RED)
    for (x, y) in ((23, 5), (24, 4), (29, 3), (30, 2), (37, 5), (38, 4)):
        if c.px.get((x + hx_, y + hy_)) == RED: put(x + hx_, y + hy_, RED_HI)
    # beak ring
    ring = {(x, y) for y, l in RING_OUT_L.items() for x in range(l, 63 - l + 1)}
    face = {(x, y) for y, l in FACE_IN_L.items() for x in range(l, 63 - l + 1)}
    for (x, y) in ring: put(x + hx_, y + hy_, YEL)
    for (x, y) in ring:
        if c.px.get((x + hx_, y + hy_)) == YEL and ((x - 31.5) + (y - 22) * 0.9) > 6:
            put(x + hx_, y + hy_, YEL_MID)
    for (x, y) in ring:
        if any((x + dx, y + dy) not in ring for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
            put(x + hx_, y + hy_, BLACK)
    # face
    for (x, y) in face:
        put(x + hx_, y + hy_,
            FACE_SHAD if ((x - 31.5) * 0.8 + (y - 20) * 0.55) > 3.0 else FACE_LIT)
    rim = {(x, y) for (x, y) in face
           if any((x + dx, y + dy) not in face for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))}
    for (x, y) in rim: put(x + hx_, y + hy_, BLACK)
    inner = face - rim
    def fput(x, y, col):
        if (x, y) in inner: put(x + hx_, y + hy_, col)
    c.fput = fput; c.face_inner = inner
    EXPRESSIONS[P['face']](c, fput)
    for y in range(28, 31):
        for x in (31, 32):
            if c.px.get((x + hx_, y + hy_)) in (YEL, YEL_MID): put(x + hx_, y + hy_, BLACK)
    # googly eyes
    marks = GOOGLY[P['googly']]
    for (cx, cy, mark, moff) in ((16, 19, PLUS, marks[0]), (47, 19, EX, marks[1])):
        disc = {(cx + dx, cy + dy) for dx in range(-6, 7) for dy in range(-6, 7)
                if dx * dx + dy * dy <= 28}
        for (x, y) in disc:
            edge = any((x + dx, y + dy) not in disc for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))
            put(x + hx_, y + hy_, BLACK if edge else WHITE)
        for (dx, dy) in mark:
            put(cx + dx + moff[0] + hx_, cy + dy + 1 + moff[1] + hy_, BLACK)

# googly mark offsets (left "+", right "x") relative to the approved position.
# Googly pupils swing loose - that jiggle is the costume's secondary motion.
GOOGLY = {
    'normal':  ((0, 0), (0, 0)),
    'swing_l': ((-1, 0), (-1, 0)),     # head moved right, pupils lag left
    'swing_r': ((1, 0), (1, 0)),       # head moved left, pupils lag right
    'lag_up':  ((0, -1), (0, -1)),     # head dropped, pupils lag up
    'in':      ((1, 0), (-1, 0)),      # looking in at the food
    'right':   ((1, 0), (1, 0)),       # looking at the phone
    'knocked': ((-2, -1), (1, -2)),    # knocked askew by the hit
    'crossed': ((2, -1), (-1, -1)),    # dizzy
    'wall':    ((-1, 0), (1, 0)),      # KO, wall-eyed
}

def _googly_clean(mark, off):
    disc = {(dx, dy) for dx in range(-6, 7) for dy in range(-6, 7) if dx * dx + dy * dy <= 28}
    n4 = ((1,0),(-1,0),(0,1),(0,-1)); n8 = n4 + ((1,1),(1,-1),(-1,1),(-1,-1))
    rimset = {p for p in disc if any((p[0]+a, p[1]+b) not in disc for a, b in n4)}
    for (dx, dy) in mark:
        p = (dx + off[0], dy + 1 + off[1])
        if p not in disc or p in rimset: return False
        if any((p[0]+a, p[1]+b) in rimset for a, b in n8): return False
    return True
for _k, (_l, _r) in GOOGLY.items():
    assert _googly_clean(PLUS, _l) and _googly_clean(EX, _r), 'googly mark fuses into rim: ' + _k

# ----- expressions (head-local coords, clamped to the inside of the opening) --
def face_grin(c, fput):
    for x in range(29, 35): fput(x, 15, CREAM_DEEP)
    for x in list(range(28, 31)) + list(range(33, 36)): fput(x, 16, FACE_SHAD)
    for x in list(range(28, 31)) + list(range(33, 36)):
        for y in (17, 18, 19): fput(x, y, WHITE)
    for y in (18, 19):
        fput(29, y, BLACK); fput(34, y, BLACK)
    for y, (a, b) in {22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}.items():
        for x in range(a, b + 1): fput(x, y, BLACK)
    for x in range(29, 35): fput(x, 21, WHITE)
    for x in range(31, 33): fput(x, 24, RED_HI)

def _pts(fput, pts, col):
    for (x, y) in pts: fput(x, y, col)

def _eyes_open(fput, rows=(17, 18, 19), pupils=((29, 18), (29, 19), (34, 18), (34, 19))):
    for x in list(range(28, 31)) + list(range(33, 36)):
        for y in rows: fput(x, y, WHITE)
    _pts(fput, pupils, BLACK)

def _scalp(fput):
    for x in range(29, 35): fput(x, 15, CREAM_DEEP)

def face_strain(c, fput):
    # eyes screwed shut, brows knotted down to the middle, teeth clenched
    _scalp(fput)
    _pts(fput, [(27, 16), (28, 16), (29, 17), (30, 17), (36, 16), (35, 16), (34, 17), (33, 17)], BLACK)
    _pts(fput, [(28, 18), (29, 19), (30, 19), (28, 20), (35, 18), (34, 19), (33, 19), (35, 20)], BLACK)
    for x in range(28, 36): fput(x, 22, BLACK)
    for x in range(28, 36): fput(x, 23, WHITE)
    for x in range(28, 36): fput(x, 24, BLACK)
    _pts(fput, [(28, 23), (35, 23), (30, 23), (33, 23)], BLACK)
    for x in range(29, 35): fput(x, 25, FACE_SHAD)

def face_relief(c, fput):
    # blissful: eyes shut in bold arcs under lit lids (thin dark arcs vanish on
    # the dark face at game scale), mouth a relaxed "ahh"
    _scalp(fput)
    for x in list(range(28, 30)) + list(range(34, 36)): fput(x, 17, CREAM_DEEP)
    _pts(fput, [(27, 17), (28, 18), (29, 18), (30, 17), (33, 17), (34, 18), (35, 18), (36, 17)], BLACK)
    for y, (a, b) in {21: (30, 33), 22: (29, 34), 23: (29, 34), 24: (30, 33)}.items():
        for x in range(a, b + 1): fput(x, y, BLACK)
    _pts(fput, [(31, 23), (32, 23)], RED_HI)

def face_chomp_open(c, fput):
    # greedy: eyes wide on the food, jaw dropped as far as it goes
    _scalp(fput)
    _pts(fput, [(28, 15), (29, 15), (34, 15), (35, 15)], FACE_SHAD)
    _eyes_open(fput, rows=(16, 17, 18), pupils=((29, 18), (34, 18)))
    for y, (a, b) in {20: (28, 35), 21: (28, 35), 22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}.items():
        for x in range(a, b + 1): fput(x, y, BLACK)
    for x in range(29, 35): fput(x, 20, WHITE)
    _pts(fput, [(30, 24), (31, 24), (32, 24), (31, 25), (32, 25)], RED_HI)

def face_chomp_shut(c, fput):
    # mouth full: eyes still locked on the food (white keeps it readable on the
    # dark face), cheeks bulging, lips clamped in a munching line
    _scalp(fput)
    _pts(fput, [(28, 15), (29, 15), (34, 15), (35, 15)], FACE_SHAD)
    _eyes_open(fput, rows=(16, 17, 18), pupils=((29, 18), (34, 18)))
    for (x, y) in [(27, 20), (27, 21), (28, 21), (27, 22), (36, 20), (36, 21), (35, 21), (36, 22)]:
        fput(x, y, CREAM_DEEP)
    _pts(fput, [(28, 23), (29, 22), (30, 23), (31, 23), (32, 23), (33, 23), (34, 22), (35, 23)], BLACK)

def face_shout(c, fput):
    # yelling down the phone: brows slammed down, mouth wide open
    _scalp(fput)
    _pts(fput, [(27, 16), (28, 16), (29, 17), (30, 17), (36, 16), (35, 16), (34, 17), (33, 17)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)): fput(x, 18, WHITE)
    for x in list(range(28, 31)) + list(range(33, 36)): fput(x, 19, WHITE)
    _pts(fput, [(29, 19), (34, 19)], BLACK)
    for y, (a, b) in {21: (28, 35), 22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}.items():
        for x in range(a, b + 1): fput(x, y, BLACK)
    for x in range(29, 35): fput(x, 21, WHITE)
    _pts(fput, [(30, 24), (31, 24), (32, 24), (33, 24), (31, 25), (32, 25)], RED_HI)

def face_talk(c, fput):
    # between shouts: still scowling, mouth clamped in a frown
    _scalp(fput)
    _pts(fput, [(27, 16), (28, 16), (29, 17), (30, 17), (36, 16), (35, 16), (34, 17), (33, 17)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)): fput(x, 18, WHITE)
    for x in list(range(28, 31)) + list(range(33, 36)): fput(x, 19, WHITE)
    _pts(fput, [(29, 19), (34, 19)], BLACK)
    for x in range(29, 35): fput(x, 22, BLACK)
    _pts(fput, [(28, 23), (35, 23)], BLACK)
    for x in range(30, 34): fput(x, 23, FACE_SHAD)

def face_pain(c, fput):
    # struck: eyes squeezed, brows up in the middle, teeth bared
    _scalp(fput)
    _pts(fput, [(27, 17), (28, 17), (29, 16), (30, 16), (36, 17), (35, 17), (34, 16), (33, 16)], BLACK)
    _pts(fput, [(28, 18), (29, 19), (30, 19), (28, 20), (35, 18), (34, 19), (33, 19), (35, 20)], BLACK)
    for y, (a, b) in {22: (28, 35), 23: (28, 35), 24: (28, 35), 25: (29, 34)}.items():
        for x in range(a, b + 1): fput(x, y, BLACK)
    for x in range(29, 35): fput(x, 23, WHITE)
    _pts(fput, [(31, 23), (32, 23)], BLACK)

def face_dizzy(c, fput):
    # knocked silly: X eyes, jaw hanging, tongue lolling out
    _scalp(fput)
    _pts(fput, [(28, 17), (30, 17), (29, 18), (28, 19), (30, 19),
                (33, 17), (35, 17), (34, 18), (33, 19), (35, 19)], BLACK)
    for y, (a, b) in {21: (29, 34), 22: (29, 34), 23: (29, 34), 24: (30, 33)}.items():
        for x in range(a, b + 1): fput(x, y, BLACK)
    _pts(fput, [(31, 23), (32, 23), (33, 23), (31, 24), (32, 24), (33, 24), (32, 25), (33, 25)], RED_HI)
    _pts(fput, [(34, 24), (34, 25)], BLACK)

EXPRESSIONS = {'grin': face_grin, 'strain': face_strain, 'relief': face_relief,
               'chomp_open': face_chomp_open, 'chomp_shut': face_chomp_shut,
               'shout': face_shout, 'talk': face_talk, 'pain': face_pain,
               'dizzy': face_dizzy}

# ----- overlay helpers ----------------------------------------------------------
def draw_part(c, poly, shade):
    """A separately outlined piece drawn on top (raised wing, prop)."""
    line, inter = raster(poly)
    for (x, y) in inter:
        col = shade(x, y)
        if col: c.put(x, y, col)
    for (x, y) in line: c.put(x, y, BLACK)
    return line, inter

def wing_shader(cx, cy, rx, ry):
    """Same wing ramp and frozen thresholds as the approved side wings."""
    def s(x, y):
        return band(lum(x, y, cx, cy, rx, ry), TH['wing'])
    return s
