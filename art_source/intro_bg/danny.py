"""Danny slumped at the desk, head in hands. Local sprite coords; origin placed at ORIGIN."""
import math
from canvas import poly_mask, func_mask, boundary, line_pts

ORIGIN = (258, 36)
HAND = 'D'
HAND_POS = (30, 64)
SW, SH = 132, 112
CX = 65.5                 # symmetry axis (local)


def mirror_set(s):
    return {(131 - x, y) for (x, y) in s}


def mirror_lines(lines):
    return [line[::-1] for line in lines]


def stamp(px, lines, x0, y0):
    for j, line in enumerate(lines):
        for i, ch in enumerate(line):
            if ch in '. ':
                continue
            px[(x0 + i, y0 + j)] = ch


def stamp_mirror(px, lines, x0, y0):
    stamp(px, mirror_lines(lines), 131 - x0 - len(lines[0]) + 1, y0)


def capsule_fn(ax, ay, bx, by, r):
    def fn(px_, py_):
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = max(0.0, min(1.0, ((px_ - ax) * vx + (py_ - ay) * vy) / L2))
        qx, qy = ax + t * vx, ay + t * vy
        return (px_ - qx, py_ - qy)
    return fn


def capsule(ax, ay, bx, by, r):
    off = capsule_fn(ax, ay, bx, by, r)
    x0 = int(min(ax, bx) - r - 1)
    x1 = int(max(ax, bx) + r + 1)
    y0 = int(min(ay, by) - r - 1)
    y1 = int(max(ay, by) + r + 1)
    return func_mask(lambda a, b: sum(c * c for c in off(a, b)) <= r * r, x0, y0, x1, y1)


def norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


LIGHT = norm((-0.55, -0.5, 0.67))


def lambert(nx, ny):
    nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


# half-width of the head (beanie + face) by row, sampled from the painting
HEAD_HW = [
    (1.9, 0.0), (2.4, 2.2), (3.2, 4.8), (4.2, 7.4), (6.0, 11.0), (8.0, 14.3), (11.0, 18.0),
    (14.0, 21.0), (18.0, 24.5), (24.0, 28.0), (30.0, 30.8), (36.0, 32.0), (46.0, 32.2),
    (58.0, 32.0), (64.0, 31.3), (70.0, 29.8), (76.0, 27.4), (82.0, 24.2), (88.0, 20.0),
    (92.0, 16.6), (95.0, 13.0), (97.0, 9.5), (98.2, 5.5), (98.8, 0.0),
]


def hw_at(y):
    pts = HEAD_HW
    if y <= pts[0][0]:
        return pts[0][1]
    for (y0, h0), (y1, h1) in zip(pts, pts[1:]):
        if y0 <= y <= y1:
            return h0 + (y - y0) / (y1 - y0) * (h1 - h0)
    return 0.0


def head_pts():
    left = [(CX - hw, y) for (y, hw) in HEAD_HW]
    right = [(CX + hw, y) for (y, hw) in reversed(HEAD_HW)]
    return left + right


def face_top_y(x):
    t = (x - CX) / 32.0
    return 30.0 + 10.5 * t * t


def cuff_top_y(x):
    t = (x - CX) / 31.0
    return 17.0 + 8.5 * t * t


SLEEVE_L = [
    (35.5, 47.0), (30.0, 48.0), (24.0, 49.5), (18.5, 52.5), (13.5, 57.0), (9.5, 62.5),
    (6.8, 68.0), (5.2, 74.0), (5.0, 77.2), (23.0, 75.6), (29.0, 71.5), (34.0, 67.0),
    (37.5, 63.0),
]
UPPER_L = (11.0, 70.0, 12.6, 99.0, 6.4)
FORE_L = (15.0, 99.5, 37.0, 87.0, 5.6)


def mirror_capsule(c):
    ax, ay, bx, by, r = c
    return (131.0 - ax, ay, 131.0 - bx, by, r)


def shade_capsule(px, mask, cap, ramp=('s', 'd', 'w'), t1=0.42, t2=0.05):
    off = capsule_fn(*cap)
    r = cap[4]
    for (x, y) in mask:
        dx, dy = off(x + 0.5, y + 0.5)
        I = lambert(dx / (r + 0.6), dy / (r + 0.6))
        px[(x, y)] = ramp[0] if I > t1 else (ramp[1] if I > t2 else ramp[2])


def edge_normal(mask, x, y, rad=2):
    """Outward normal estimated from which nearby pixels fall outside the mask (None if interior)."""
    nx = ny = 0.0
    hit = False
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            if (dx or dy) and (x + dx, y + dy) not in mask:
                w = 1.0 / (dx * dx + dy * dy)
                nx += dx * w
                ny += dy * w
                hit = True
    if not hit:
        return None
    l = math.hypot(nx, ny)
    if l < 1e-6:
        return None
    return nx / l, ny / l


def sleeve_key(mask, x, y, head):
    n = edge_normal(mask, x, y, 2)
    k = 'R'
    if n is not None:
        d = n[0] * -0.74 + n[1] * -0.67
        if d > 0.45:
            k = 'r'
        elif d < -0.35:
            k = 'B'
    # the big head blocks light from the upper-left: shadow falls on the right shoulder
    if (x - 3, y - 2) in head and (x - 1, y) not in head:
        k = {'r': 'R', 'R': 'B', 'B': 'B'}[k]
    return k


def despeckle(px, layer, passes=2, protect_layers=('chain',)):
    """Replace pixels that share no colour with any 8-neighbour by the dominant neighbour colour."""
    for _ in range(passes):
        changes = {}
        for (x, y), k in px.items():
            if k == 'K' or layer.get((x, y)) in protect_layers:
                continue
            same = False
            counts = {}
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if not (dx or dy):
                        continue
                    q = px.get((x + dx, y + dy))
                    if q == k:
                        same = True
                        break
                    if q is not None and q != 'K' and layer.get((x + dx, y + dy)) == layer.get((x, y)):
                        wgt = 2 if (dx == 0 or dy == 0) else 1
                        counts[q] = counts.get(q, 0) + wgt
                if same:
                    break
            if not same and counts:
                changes[(x, y)] = max(counts.items(), key=lambda t: t[1])[0]
        if not changes:
            break
        px.update(changes)


def build():
    px = {}
    layer = {}          # which body part owns the pixel (for shadows / debugging)

    def outline(mask):
        for p in boundary(mask, True, SW, SH):
            px[p] = 'K'

    # ------------------------------------------------ masks
    sleeve_l = poly_mask(SLEEVE_L, SW, SH)
    sleeve_r = mirror_set(sleeve_l)
    upper_l = capsule(*UPPER_L)
    fore_l = capsule(*FORE_L)
    upper_r = capsule(*mirror_capsule(UPPER_L))
    fore_r = capsule(*mirror_capsule(FORE_L))
    import hands
    palm_l = hands.capsule_mask(hands.PALM_L)
    palm_r = hands.capsule_mask(hands.mirror_c(hands.PALM_L))
    fingers_l = [hands.capsule_mask(c) for c in hands.FINGERS_L]
    fingers_r = [hands.capsule_mask(hands.mirror_c(c)) for c in hands.FINGERS_L]
    head = poly_mask(head_pts(), SW, SH)
    beanie = {(x, y) for (x, y) in head if y + 0.5 < face_top_y(x + 0.5)}
    face = head - beanie
    crown = {(x, y) for (x, y) in beanie if y + 0.5 < cuff_top_y(x + 0.5)}
    cuff = beanie - crown
    SLEEVES = ((sleeve_l, None), (sleeve_r, None))

    def paint_sleeve(s, c):
        for (x, y) in s:
            px[(x, y)] = sleeve_key(s, x, y, head)
            layer[(x, y)] = 'sleeve'
        outline(s)

    # ------------------------------------------------ sleeves (behind everything)
    for s, c in SLEEVES:
        paint_sleeve(s, c)

    # ------------------------------------------------ arms
    for upper, fore, ucap, fcap in ((upper_l, fore_l, UPPER_L, FORE_L),
                                    (upper_r, fore_r, mirror_capsule(UPPER_L), mirror_capsule(FORE_L))):
        shade_capsule(px, upper, ucap)
        shade_capsule(px, fore - upper, fcap)
        for p in upper | fore:
            layer[p] = 'arm'
        outline(upper | fore)
    # sleeve re-covers the top of the upper arm
    for s, c in SLEEVES:
        paint_sleeve(s, c)
    # elbow crease: dark wedge where forearm folds against upper arm
    for (x, y) in [(17, 97), (17, 96), (18, 95), (18, 94), (19, 93)]:
        px[(x, y)] = 'K'
        px[(131 - x, y)] = 'K'

    # ------------------------------------------------ beanie
    N = 16
    for (x, y) in beanie:
        cx, cy = x + 0.5, y + 0.5
        hw = max(1.0, hw_at(cy))
        u = max(-1.0, min(1.0, (cx - CX) / hw))
        theta = math.asin(u)
        f = theta / (math.pi / N) + 0.5
        frac = f - math.floor(f)
        grey = (int(math.floor(f)) % 2 == 0) and 0.12 < frac < 0.88
        nx = (cx - CX) / 34.0
        if (x, y) in crown:
            ny = (cy - 38.0) / 40.0
            I = lambert(nx, ny)
        else:
            top = cuff_top_y(cx)
            bot = face_top_y(cx)
            v = (cy - top) / max(1.0, bot - top)
            I = lambert(nx, -0.30) - 0.30 * max(0.0, v - 0.55)
        if grey:
            k = 'g' if I > 0.50 else ('F' if I > 0.12 else 'D')
        else:
            k = 'W' if I > 0.50 else ('P' if I > 0.12 else 'g')
        px[(x, y)] = k
        layer[(x, y)] = 'head'

    # ------------------------------------------------ face
    for (x, y) in face:
        cx, cy = x + 0.5, y + 0.5
        nx = (cx - CX) / 34.0
        ny = (cy - 60.0) / 42.0
        I = lambert(nx, ny)
        k = 's' if I > 0.26 else ('d' if I > -0.12 else 'w')
        if cy < face_top_y(cx) + 2.4 and k == 's':
            k = 'd'
        px[(x, y)] = k
        layer[(x, y)] = 'head'
    DARKER = {'W': 'P', 'P': 'g', 'g': 'F', 'F': 'D', 'D': 'D'}
    for (x, y) in beanie:
        # the folded cuff overhangs the crown: one-step shadow on the crown just above the fold
        if (x, y) in crown and (x, y + 1) in crown and (x, y + 2) in cuff:
            px[(x, y)] = DARKER.get(px[(x, y)], px[(x, y)])
    for (x, y) in beanie:
        if (x, y) in crown and (x, y + 1) in cuff:
            px[(x, y)] = 'K'
        if (x, y + 1) in face:
            px[(x, y)] = 'K'
    outline(head)

    # ------------------------------------------------ gold chain, hanging below the chin
    chain = [
        "YK..............KY",
        "KYA............AYK",
        ".KYA..........AYK.",
        "..KYYA......AYYK..",
        "...KKYAYAYAYAYKK..",
        ".....KKKKKKKKKK...",
    ]
    tmp = {}
    stamp(tmp, chain, 57, 97)
    for p, k in tmp.items():
        if p not in head:
            px[p] = k
            layer[p] = 'chain'

    # ------------------------------------------------ face features
    brow_l = [
        "...........KK",
        "........KKKKK",
        ".....KKKK....",
        "..KKKK.......",
        "KKK..........",
    ]
    stamp(px, brow_l, 45, 44)
    stamp_mirror(px, brow_l, 45, 44)
    eye_l = [
        ".....ddddddddd.",
        "...KKKKKKKKKKKK",
        "..KKKKKKKKKKKKK",
        "KKdd.......ddd.",
        "....ddddddd....",
    ]
    stamp(px, eye_l, 43, 50)
    stamp_mirror(px, eye_l, 43, 50)
    nose = [
        ".......d.....",
        ".......d.....",
        ".......dd....",
        "........d....",
        "........d....",
        "........dd...",
        ".........d...",
        ".........d...",
        ".........dd..",
        "..K.......d..",
        "...KK...KKd..",
        ".....d.K.dd..",
        "......ddd....",
    ]
    stamp(px, nose, 59, 57)
    mouth = [
        ".......KKKKK........",
        ".....KK.....KKK.....",
        "...KK..........KK...",
        "..K..ddddddddd...K..",
        ".K......ddddd.....K.",
    ]
    stamp(px, mouth, 56, 79)
    fold_l = [
        "d...",
        ".d..",
        ".dd.",
        "..d.",
        "..d.",
        "..d.",
        ".dd.",
        ".d..",
    ]
    stamp(px, fold_l, 51, 64)
    stamp_mirror(px, fold_l, 51, 64)

    # ------------------------------------------------ hands (palm + curled fingers over the cheek)
    for palm, fingers, fore, pcap, fcaps in (
            (palm_l, fingers_l, fore_l, hands.PALM_L, hands.FINGERS_L),
            (palm_r, fingers_r, fore_r, hands.mirror_c(hands.PALM_L), [hands.mirror_c(c) for c in hands.FINGERS_L])):
        # occlusion on the cheek right around the hand
        grow = set()
        for (x, y) in palm | set().union(*fingers):
            for dx in (-1, 0, 1, 2):
                for dy in (0, 1, 2):
                    grow.add((x + dx, y + dy))
        for p in grow:
            if layer.get(p) == 'head' and px.get(p) in ('s', 'd') and p in face:
                px[p] = 'd' if px[p] == 's' else 'w'
        shade_capsule(px, palm, pcap, t1=0.30, t2=-0.05)
        edge = boundary(palm | fore, True, SW, SH)
        for p in palm:
            layer[p] = 'hand'
            if p in edge:
                px[p] = 'K'
        # fingers from little (back) to index (front)
        for fm, fc in reversed(list(zip(fingers, fcaps))):
            shade_capsule(px, fm, fc, t1=0.30, t2=-0.10)
            for p in fm:
                layer[p] = 'hand'
            for p in boundary(fm, True, SW, SH):
                px[p] = 'K'
    despeckle(px, layer)
    return px, layer


def shadow_offsets(layer):
    """Cast shadow onto the desk: parts at different heights shift by different amounts."""
    sh = set()
    for (x, y), name in layer.items():
        d = {'arm': (2, 2), 'hand': (3, 3), 'chain': (1, 1), 'sleeve': (4, 3)}.get(name, (5, 4))
        sh.add((x + d[0], y + d[1]))
    return sh


def to_canvas(cv, built, origin=ORIGIN):
    px, layer = built
    ox, oy = origin
    for (x, y) in shadow_offsets(layer):
        if (x, y) in px:
            continue
        gx, gy = ox + x, oy + y
        k = cv.get(gx, gy)
        if k == 'w':
            cv.set(gx, gy, 'B')
        elif k == 'B':
            cv.set(gx, gy, 'M')
    for (x, y), k in px.items():
        cv.set(ox + x, oy + y, k)


if __name__ == '__main__':
    from bg import build_background
    cv, _, _ = build_background()
    to_canvas(cv, build())
    cv.save('stage2.png')
    from pngio import read_png, write_png, scale, crop
    w, h, rows = read_png('stage2.png')
    write_png('stage2_danny_6x.png', scale(crop(rows, 250, 30, 400, 150), 6))
