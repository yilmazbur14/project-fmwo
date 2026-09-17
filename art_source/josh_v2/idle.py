"""Josh v2 idle (frame 0). Layered build: traced silhouettes + height-field cel shading + hand-drawn detail."""
import sys
from jlib import *
from jlib import _norm
import parts as P

SKIN = 'gfdsa1'


def hcap(px, py, ax, ay, bx, by, r0, r1, amp=1.0):
    t, qx, qy = seg_t(px, py, ax, ay, bx, by)
    r = r0 + (r1 - r0) * t
    d = math.hypot(px - qx, py - qy)
    return amp * math.sqrt(max(0.0, r * r - d * d))


def hdome(px, py, cx, cy, rx, ry, amp):
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    return amp * math.sqrt(max(0.0, 1 - d2))


def hbump(px, py, cx, cy, rl, rr, rt, rb, amp, power=1.0):
    rx = rl if px < cx else rr
    ry = rt if py < cy else rb
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    if d2 >= 1:
        return 0.0
    return amp * (1 - d2) ** power


def hplat(px, py, cx, cy, rl, rr, rt, rb, amp, k=4.0, dome=0.35):
    """Plateau muscle: gentle dome on top, steep ~1px edge -> crisp cel separations."""
    rx = rl if px < cx else rr
    ry = rt if py < cy else rb
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    if d2 >= 1:
        return 0.0
    return amp * (dome * (1 - d2) + (1 - dome) * min(1.0, (1 - d2) * k))


def hf_shade(c, mask, hfn, ramp, th, crease=None, crease_th=None, zscale=1.0, outline=True):
    vals = hf_values(mask, hfn, eps=0.5, zscale=zscale)
    under = copy(c)
    for (x, y), (lam, lap, h0) in vals.items():
        ch = quant(lam, ramp, th)
        if crease is not None and lap > crease_th:
            i = ramp.index(ch)
            ch = ramp[max(0, min(i, crease) - 1)]
        c[y][x] = ch
    if outline:
        ol, pruned = outline_pixels(mask)
        for y in range(H):
            for x in range(W):
                if ol[y][x]:
                    c[y][x] = '#'
        for (x, y) in pruned:
            c[y][x] = under[y][x]
    return vals


def draw_boot(c, poly, shaft, toe):
    """Black wrestling boot: lit left edge, dark right edge, padded top rim, toe-cap highlight."""
    m = poly_mask(poly)
    under = copy(c)
    top = min(y for y in range(H) for x in range(W) if m[y][x])
    bot = max(y for y in range(H) for x in range(W) if m[y][x])
    for y in range(H):
        xs = [x for x in range(W) if m[y][x]]
        if not xs:
            continue
        xl, xr = min(xs), max(xs)
        for x in xs:
            col, rcol = x - xl, xr - x
            if y == top + 1:
                ch = 'V' if rcol > 3 else 'v'
            elif y >= toe[1] - 1:     # foot / toe cap
                ch = 'X'
                if y == toe[1] - 1 and col >= 1 and rcol >= 1:
                    ch = 'v'
                if abs(x - toe[0]) <= 1 and y == toe[1] - 1:
                    ch = 'V'
                if y == bot - 1:
                    ch = 'x'
                if rcol <= 1:
                    ch = 'x'
            else:                      # shaft
                ch = 'X'
                if col == 1:
                    ch = 'v'
                if col == 2 and y < toe[1] - 2:
                    ch = 'X'
                if rcol <= 2:
                    ch = 'x'
            c[y][x] = ch
    ol, pruned = outline_pixels(m)
    for y in range(H):
        for x in range(W):
            if ol[y][x]:
                c[y][x] = '#'
    for (x, y) in pruned:
        c[y][x] = under[y][x]


G = dict(
    head=[(24, 5), (28, 3), (37, 3), (41, 5), (43, 8), (44, 13), (44, 18), (43, 22), (40, 25), (36, 27),
          (30, 27), (26, 25), (23, 22), (22, 18), (22, 13), (22, 8)],
    near_ear=[(22, 12), (20, 12), (19, 14), (19, 18), (21, 20), (23, 20)],
    hair=[(21, 15), (20, 11), (20, 7), (22, 4), (25, 2), (29, 1), (33, 0), (38, 0), (42, 2), (45, 5),
          (46, 9), (45, 13), (44, 14), (44, 10), (41, 9), (37, 9), (31, 9), (26, 10), (23, 11), (23, 15)],
    body=[(27, 21), (25, 23), (21, 24), (17, 25), (14, 26), (11, 28), (10, 32), (12, 35), (15, 37),
          (18, 40), (21, 44), (23, 47), (43, 47), (44, 44), (45, 40), (47, 37), (50, 35), (53, 31),
          (52, 28), (49, 25), (45, 24), (41, 23), (39, 21)],
    n_upper=[(16, 25), (14, 22), (10, 22), (8, 24), (5, 28), (4, 32), (6, 35), (10, 36), (14, 35), (16, 32)],
    n_fore=[(4, 29), (4, 24), (6, 19), (8, 16), (13, 16), (13, 19), (11, 24), (10, 29), (8, 32), (5, 32)],
    n_fist=[(3, 17), (3, 12), (5, 9), (11, 9), (13, 11), (13, 16), (11, 18), (5, 18)],
    f_upper=[(47, 27), (52, 27), (54, 30), (56, 35), (56, 40), (54, 43), (52, 42), (50, 37), (48, 33)],
    f_fore=[(52, 38), (56, 40), (55, 44), (52, 48), (49, 50), (46, 47), (50, 43)],
    f_fist=[(42, 44), (47, 43), (50, 45), (50, 49), (47, 51), (42, 50)],
    speedo=[(21, 45), (33, 46), (45, 45), (46, 47), (42, 50), (37, 52), (30, 52), (25, 50), (20, 47)],
    n_leg=[(20, 46), (32, 50), (31, 54), (29, 57), (18, 57), (17, 52), (18, 48)],
    f_leg=[(34, 50), (45, 46), (47, 49), (49, 53), (49, 57), (39, 57), (36, 54)],
    n_boot=[(16, 54), (29, 54), (29, 63), (11, 63), (11, 61), (14, 59), (16, 58)],
    f_boot=[(38, 54), (50, 54), (50, 58), (53, 60), (55, 62), (55, 63), (38, 63)],
)


def torso_h(px, py):
    h = hdome(px, py, 32.5, 34, 22, 20, 6.0)
    h += hbump(px, py, 21, 25, 6, 5, 3, 3, 1.4)
    h += hbump(px, py, 45, 25, 5, 5, 3, 3, 1.2)
    h = max(h, hdome(px, py, 15, 30.5, 6, 6, 6.2) + 1.0)
    h = max(h, hdome(px, py, 50, 30, 4.8, 5.5, 5.4) + 0.6)
    # pecs: plateau slabs with a crisp lower edge
    h += hplat(px, py, 25.0, 30.0, 9.0, 7.5, 5.5, 5.0, 2.2, k=3.5, dome=0.5)
    h += hplat(px, py, 39.5, 30.0, 6.5, 7.0, 5.5, 5.0, 2.0, k=3.5, dome=0.5)
    # abs 2x3 plateaus
    for ay in (37.6, 40.5, 43.4):
        h += hplat(px, py, 29.6, ay, 3.1, 2.7, 1.5, 1.5, 0.8, k=3.0, dome=0.3)
        h += hplat(px, py, 36.3, ay, 2.7, 2.9, 1.5, 1.5, 0.75, k=3.0, dome=0.3)
    h += hbump(px, py, 19.5, 39.5, 3, 3, 3, 3, 0.8)
    h += hbump(px, py, 45, 39.5, 2.5, 2.5, 3, 3, 0.6)
    return h


# ------------------------------------------------------------------ hand-drawn head detail
SUNGLASSES = [  # x 22.., y 3..
    "..########...#######..",   # 3
    ".#CcBBBBbb###cBBBbbb#.",   # 4
    ".#cBBBbbbb#.#BBbbbbb#.",   # 5
    "..########...######...",   # 6
]

FACE_FEATURES = {  # (x, y): rows ; '.' = keep
    'near_brow': (25, 10, [
        "...hkkkh",
        ".kkkkkkk",
        "kkh.....",
    ]),
    'far_brow': (37, 10, [
        "hkkkh..",
        "kkkkkkh",
        "......k",
    ]),
    'near_eye': (26, 13, [
        ".####.",
        "#eeew#",
        ".dssd.",
    ]),
    'far_eye': (38, 13, [
        ".####",
        "#eew#",
        ".dsd.",
    ]),
    'nose': (33, 15, [
        ".a..",
        ".sd.",
        "asdf",
        ".ff.",
    ]),
    'blush_n': (24, 16, ["rrr"]),
    'blush_f': (41, 16, ["rr"]),
    'mustache': (29, 19, [
        ".hkkkh.hkkkh",
    ]),
    'grin': (28, 20, [
        "##############",
        "#wwwWwwwWwwwW#",
        ".#wwwwwwwwww#.",
        "..##########..",
    ]),
    'goatee': (34, 24, [
        "hkh",
        "khk",
        "hkh",
    ]),
}


def build(variant='A'):
    c = blank()
    TH_LIMB = [0.0, 0.35, 0.6, 0.85, 0.98]
    hf_shade(c, poly_mask(G['n_leg']), lambda px, py: hcap(px, py, 25, 48, 23, 57, 6.5, 5.5), SKIN, TH_LIMB)
    hf_shade(c, poly_mask(G['f_leg']), lambda px, py: hcap(px, py, 41, 48, 44, 57, 6.0, 5.2), SKIN, TH_LIMB)
    draw_boot(c, G['n_boot'], shaft=(16, 29), toe=(14, 61))
    draw_boot(c, G['f_boot'], shaft=(38, 50), toe=(52, 61))
    body_m = poly_mask(G['body'])
    hf_shade(c, body_m, torso_h, SKIN, [0.05, 0.4, 0.66, 0.88, 0.985], crease=3, crease_th=1.1, zscale=0.9)
    print('torso despeckled', despeckle(c, region=body_m))
    block(c, *P.SPEEDO)
    hf_shade(c, poly_mask(G['f_upper']), lambda px, py: max(hcap(px, py, 50, 29, 54, 40, 5, 3.8), hdome(px, py, 50, 30, 4.5, 5, 5)), SKIN, TH_LIMB)
    hf_shade(c, poly_mask(G['f_fore']), lambda px, py: hcap(px, py, 54, 41, 48, 47, 3.5, 3.0), SKIN, TH_LIMB)
    block(c, *P.FAR_FIST)

    def n_up_h(px, py):
        h = hcap(px, py, 15, 30, 7, 31, 5.5, 4.5)
        h = max(h, hdome(px, py, 12, 26.5, 5.5, 5, 6))
        h = max(h, hdome(px, py, 15, 30.5, 5.5, 5.5, 5.5))
        return h
    hf_shade(c, poly_mask(G['n_upper']), n_up_h, SKIN, TH_LIMB)
    hf_shade(c, poly_mask(G['n_fore']), lambda px, py: hcap(px, py, 7, 30, 10, 17, 4.0, 3.2), SKIN, TH_LIMB)
    block(c, *P.NEAR_FIST)
    # head
    import head
    head.build_head(c, variant)
    # shift down 1 so the boots stand on the bottom edge (row 63)
    assert all(ch == '.' for ch in c[63]), 'row 63 not empty before shift'
    c = [['.'] * W] + c[:63]
    import patch_idle
    patch_idle.apply(c, block)
    return c


if __name__ == '__main__':
    variant = sys.argv[1] if len(sys.argv) > 1 else 'A'
    tag = 'idle_' + variant
    c = build(variant)
    save_png(c, os.path.join(OUT, tag + '.png'))
    preview(c, os.path.join(OUT, tag + '_8x.png'))
    open(os.path.join(OUT, tag + '.txt'), 'w').write(to_text(c))
    print('ok')
