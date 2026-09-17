import math, json
from png import read_png, hx
from zoom import write_png, upscale

# ----- palette -------------------------------------------------------------
CREAM      = '#EEC39A'   # costume base            (portrait)
CREAM_HI   = '#FADCB8'   # costume highlight       (new - needed for volume)
CREAM_MID  = '#D6AA7C'   # costume mid shadow      (portrait)
CREAM_DEEP = '#AE8358'   # costume core shadow     (new - warm, not the grey #90765E)
FACE_LIT   = '#90765E'   # face, lit               (portrait)
FACE_SHAD  = '#7D5631'   # face, shadow            (portrait)
RED        = '#AC3232'   # comb                    (portrait)
RED_HI     = '#D95763'   # comb highlight / tongue (portrait)
YEL        = '#FBF236'   # beak ring + feet        (portrait)
YEL_MID    = '#D4CC2E'   # yellow shadow           (Greyson)
YEL_DEEP   = '#726E17'   # yellow deep shadow      (Greyson)
WHITE      = '#FFFFFF'
KHAKI      = '#A09050'   # trousers                (Greyson)
KHAKI_DK   = '#605020'   # trouser shadow          (Greyson)
BLACK      = '#000000'

W = H = 64
w, h, base = read_png('sil.png')
raw = [row[:] for row in base]          # exactly what Aseprite drew
# Aseprite's polyline rasteriser does not mirror perfectly even for mirrored
# input points, so force the silhouette symmetric off the left half first.
for y in range(H):
    for x in range(32):
        base[y][63 - x] = base[y][x]
px = {}
cream = {(x, y) for y in range(H) for x in range(W)
         if base[y][x][3] > 0 and hx(base[y][x]) == CREAM}

def put(x, y, c):
    if 0 <= x < W and 0 <= y < H: px[(x, y)] = c
def mput(x, y, c):
    put(x, y, c); put(63 - x, y, c)
def cur(x, y):
    return px.get((x, y), hx(base[y][x]) if base[y][x][3] else None)

# ----- 1. volume shading ---------------------------------------------------
LX, LY, LZ = -0.50, -0.62, 0.60
n = math.sqrt(LX*LX + LY*LY + LZ*LZ); LX, LY, LZ = LX/n, LY/n, LZ/n

def lum(x, y, cx, cy, r):
    nx, ny = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
    d2 = nx*nx + ny*ny
    if d2 > 1.0:
        s = math.sqrt(d2); nx, ny, nz = nx/s, ny/s, 0.0
    else:
        nz = math.sqrt(1.0 - d2)
    return nx*LX + ny*LY + nz*LZ

HOOD = (31.5, 20.0, 15.0)
BODY = (31.5, 42.0, 23.0)

def quantile_bands(vals, fracs):
    """Pick thresholds so each tone covers a set share of the surface.
    Hand-picked cutoffs kept missing the dark end entirely and the volume
    stayed flat; deriving them from the actual distribution guarantees a
    full ramp on every form."""
    s = sorted(vals); n = len(s); out = []; acc = 0.0
    for f in fracs:
        acc += f
        out.append(s[min(n - 1, int(n * (1.0 - acc)))])
    return out

def band(v, th):
    if v > th[0]: return CREAM_HI
    if v > th[1]: return CREAM
    if v > th[2]: return CREAM_MID
    return CREAM_DEEP

# wing root arc (right side); wing = cream pixels strictly right of it
ARC = {38: 51, 39: 50, 40: 49, 41: 49, 42: 49,
       43: 49, 44: 49, 45: 50, 46: 51, 47: 52}
def is_wing(x, y):
    if y in ARC:
        return x > ARC[y] or (63 - x) > ARC[y]
    return False

shade = {}
for (x, y) in cream:
    if y >= 53: continue                      # legs + feet handled below
    if is_wing(x, y):
        cx = 56.0 if x > 31.5 else 7.0
        grp, v = 'wing', lum(x, y, cx, 43.0, 7.0)
    elif y <= 29:
        grp, v = 'hood', lum(x, y, *HOOD)
    elif y >= 34:
        grp, v = 'body', lum(x, y, *BODY)
    else:
        t = (y - 29) / 5.0
        grp = 'body'
        v = lum(x, y, *HOOD) * (1 - t) + lum(x, y, *BODY) * t
    shade[(x, y)] = (grp, v)

TH = {}
for g, fr in (('hood', (0.17, 0.36, 0.32)), ('body', (0.15, 0.37, 0.33)),
              ('wing', (0.22, 0.40, 0.30))):
    vals = [v for (gg, v) in shade.values() if gg == g]
    TH[g] = quantile_bands(vals, fr)
for (x, y), (g, v) in shade.items():
    c = band(v, TH[g])
    if c != CREAM: put(x, y, c)

# The hood is a separate piece of the costume sitting over the body. A soft
# crescent under its lower edge (not a hard line) makes the head read as a head
# instead of the whole thing reading as one blob.
STEP = {CREAM_HI: CREAM, CREAM: CREAM_MID, CREAM_MID: CREAM_DEEP,
        CREAM_DEEP: CREAM_DEEP}
for x in range(19, 45):
    t = (x - 31.5) / 13.0
    if abs(t) > 1: continue
    sy = 31 + int(round(2.0 * math.sqrt(1 - t * t)))
    for dy, times in ((0, 1), (1, 1)):
        y = sy + dy
        if (x, y) in cream and not is_wing(x, y):
            c = cur(x, y)
            for _ in range(times):
                c = STEP.get(c, c)
            put(x, y, c)

# ----- 2. feather ticks ----------------------------------------------------
for (tx, ty) in [(20, 36), (17, 43), (24, 46), (14, 47), (22, 50), (26, 33),
                 (23, 41), (27, 48), (19, 39), (25, 37), (16, 48)]:
    for (dx, dy) in ((0, 0), (1, 1)):
        if (tx + dx, ty + dy) in cream:
            mput(tx + dx, ty + dy, CREAM_MID)

# ----- 3. wing roots -------------------------------------------------------
for y, ax in ARC.items():
    if (ax, y) in cream: mput(ax, y, BLACK)
    # Contact shadow on the body behind the wing. Light comes from the upper
    # left, so the right wing casts and the left wing barely does.
    if (ax - 1, y) in cream and not is_wing(ax - 1, y): put(ax - 1, y, CREAM_DEEP)
    lx = 63 - ax + 1
    if (lx, y) in cream and not is_wing(lx, y): put(lx, y, CREAM_MID)
# feather grooves in each wing tip
for (x, y) in [(56, 41), (57, 42), (55, 44), (56, 45)]:
    if (x, y) in cream: mput(x, y, CREAM_MID)

# ----- 4. legs -------------------------------------------------------------
for (x, y) in cream:
    if 53 <= y <= 56: put(x, y, KHAKI)
for y in range(53, 57):
    for x in (41, 40, 27, 26):
        if (x, y) in cream: put(x, y, KHAKI_DK if x in (41, 27) else KHAKI)
for y in range(53, 57):
    for x in (36, 22):
        if (x, y) in cream: put(x, y, KHAKI)

# ----- 5. feet -------------------------------------------------------------
LEGCOLS = set(range(36, 42)) | set(range(22, 28))
for (x, y) in cream:
    if y == 57: put(x, y, KHAKI if x in LEGCOLS else BLACK)
    elif y >= 58: put(x, y, YEL)
# three toes per foot: black splits, widening toward the ground
TOE_X = [(41, 46), (22, 17)]
for (a, b) in TOE_X:
    for x in (a, b):
        for y in range(59, 64):
            if (x, y) in cream: put(x, y, BLACK)
        if (x, 58) in cream: put(x, 58, YEL_DEEP)
# yellow volume on the feet
for (x, y) in cream:
    if y >= 58 and cur(x, y) == YEL:
        if y >= 62: put(x, y, YEL_MID)
        elif x >= 47 or x <= 16: put(x, y, YEL_MID)

# ----- 6. comb -------------------------------------------------------------
TOP = {21:7, 22:5, 23:4, 24:3, 25:3, 26:3, 27:4, 28:3, 29:2, 30:1, 31:1,
       32:1, 33:1, 34:2, 35:3, 36:4, 37:3, 38:3, 39:3, 40:4, 41:5, 42:7}
BOT = {21:10, 22:9, 23:9, 24:9, 25:8, 26:8, 27:8, 28:8, 29:7, 30:7, 31:7,
       32:7, 33:7, 34:7, 35:8, 36:8, 37:8, 38:8, 39:9, 40:9, 41:9, 42:10}
for x in TOP:
    assert TOP[x] == TOP[63 - x] and BOT[x] == BOT[63 - x], 'comb asymmetry %d' % x
for x, t in TOP.items():
    for y in range(t, BOT[x] + 1):
        put(x, y, BLACK if (y == t or y == BOT[x]) else RED)
for (x, y) in ((23, 5), (24, 4), (29, 3), (30, 2), (37, 5), (38, 4)):
    if px.get((x, y)) == RED: put(x, y, RED_HI)

# ----- 7. beak ring --------------------------------------------------------
OUT_L = {10:28, 11:26, 12:24, 13:23, 14:22, 15:21, 16:21, 17:21, 18:21, 19:21,
         20:21, 21:21, 22:21, 23:22, 24:22, 25:23, 26:23, 27:24, 28:25, 29:26,
         30:27}
IN_L  = {14:29, 15:27, 16:26, 17:26, 18:26, 19:26, 20:26, 21:26, 22:26, 23:27,
         24:27, 25:28, 26:29, 27:30}
ring = {(x, y) for y, l in OUT_L.items() for x in range(l, 63 - l + 1)}
face = {(x, y) for y, l in IN_L.items() for x in range(l, 63 - l + 1)}
for (x, y) in ring: put(x, y, YEL)
# yellow volume: mid tone low and to the right
for (x, y) in ring:
    if px.get((x, y)) == YEL and ((x - 31.5) + (y - 22) * 0.9) > 6: put(x, y, YEL_MID)
# black outline: outer edge only (the inner edge is handled by the face rim)
for (x, y) in ring:
    if any((x + dx, y + dy) not in ring for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
        put(x, y, BLACK)

# ----- 8. face inside the opening -----------------------------------------
for (x, y) in face:
    # lit from the upper left, like the rest of him; keep most of the face on
    # the lit tone or the surround reads as a beard rather than a face
    put(x, y, FACE_SHAD if ((x - 31.5) * 0.8 + (y - 20) * 0.55) > 3.0 else FACE_LIT)
# rim of the opening reads as the shadowed inside edge of the hood
rim = {(x, y) for (x, y) in face
       if any((x + dx, y + dy) not in face for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))}
for (x, y) in rim: put(x, y, BLACK)
inner = face - rim
def fput(x, y, c):
    if (x, y) in inner: put(x, y, c)
# bald scalp catching the light
for x in range(29, 35): fput(x, 15, CREAM_DEEP)
# brows sit a row clear of the eyes and use brown, not black - a black line
# right on top of the eyes reads as angry rather than excited
for x in list(range(28, 31)) + list(range(33, 36)): fput(x, 16, FACE_SHAD)
# wide eyes
for x in list(range(28, 31)) + list(range(33, 36)):
    for y in (17, 18, 19): fput(x, y, WHITE)
for y in (18, 19):
    fput(29, y, BLACK); fput(34, y, BLACK)
# big open grin
# stops at y=25 so rows 26-27 stay skin - run it lower and the mouth merges
# into the rim of the opening and he loses his chin
MOUTH = {22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}
for y, (a, b) in MOUTH.items():
    assert a + b == 63, 'mouth asymmetry row %d' % y
    for x in range(a, b + 1): fput(x, y, BLACK)
for x in range(29, 35): fput(x, 21, WHITE)      # upper teeth
for x in range(31, 33): fput(x, 24, RED_HI)     # tongue
# beak seam below the opening
for y in range(28, 31):
    for x in (31, 32):
        if px.get((x, y)) in (YEL, YEL_MID): put(x, y, BLACK)

# ----- 9. googly eyes ------------------------------------------------------
def googly(cx, cy, mark):
    disc = {(cx + dx, cy + dy) for dx in range(-6, 7) for dy in range(-6, 7)
            if dx * dx + dy * dy <= 28}
    for (x, y) in disc:
        if any((x + dx, y + dy) not in disc for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
            put(x, y, BLACK)
        else:
            put(x, y, WHITE)
    for (dx, dy) in mark: put(cx + dx, cy + dy + 1, BLACK)

googly(16, 19, [(0,-1),(0,0),(0,1),(-1,0),(1,0)])        # "+"  (matches portrait)
googly(47, 19, [(-1,-1),(1,-1),(0,0),(-1,1),(1,1)])      # "x"  (matches portrait)

# ----- compose + audit -----------------------------------------------------
out = [[list(base[y][x]) for x in range(W)] for y in range(H)]
for (x, y), c in px.items():
    out[y][x] = [int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 255]
write_png('mason_flat.png', W, H, out)

# Emit the diff against what Aseprite ACTUALLY exported (not the symmetrised
# copy), so replaying it over sil.png reproduces this image exactly.
ops, erases = [], 0
for y in range(H):
    for x in range(W):
        o, r = out[y][x], list(raw[y][x])
        if o == r: continue
        if o[3] == 0:
            ops.append({"x": x, "y": y, "color": "#00000000"}); erases += 1
        else:
            ops.append({"x": x, "y": y, "color": '#%02X%02X%02X' % tuple(o[:3])})
json.dump(ops, open('pixels.json', 'w'))
print('draw ops:', len(ops), ' of which erases:', erases)

cols = {}
for row in out:
    for p in row:
        if p[3] > 0:
            k = '#%02X%02X%02X' % tuple(p[:3]); cols[k] = cols.get(k, 0) + 1
print('changed pixels:', len(px), ' colours:', len(cols))
# SHAPE symmetry audit: opaque-vs-transparent must mirror exactly.
# (Tone is deliberately asymmetric - the light comes from the upper left.)
shape_asym = sum(1 for y in range(H) for x in range(32)
                 if (out[y][x][3] > 0) != (out[y][63 - x][3] > 0))
print('shape-asymmetric pairs:', shape_asym, '(must be 0)')
bb = [(x, y) for y in range(H) for x in range(W) if out[y][x][3] > 0]
print('bbox x %d-%d  y %d-%d' % (min(p[0] for p in bb), max(p[0] for p in bb),
                                 min(p[1] for p in bb), max(p[1] for p in bb)))
upscale('mason_flat.png', 'mason_flat_8x.png', 8)
