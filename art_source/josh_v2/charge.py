"""Josh v2 charge key-pose (frame 1), facing RIGHT. Shoulder-first lunge."""
import sys
from jlib import *
from jlib import _norm
from idle import hcap, hdome, hbump, hplat, hf_shade, SKIN
import head as HD

TH_LIMB = [0.0, 0.35, 0.6, 0.85, 1.01]
import idle as IDL

ANG = 30.0
PIV = (33, 46)
OFF = (-5, 1)
HEAD_OFF = (8, 3)


def rot_pts(pts, deg=ANG, pivot=PIV, off=OFF):
    th = math.radians(deg); co, si = math.cos(th), math.sin(th)
    return [(dx * co - dy * si + pivot[0] + off[0], dx * si + dy * co + pivot[1] + off[1])
            for (dx, dy) in ((x - pivot[0], y - pivot[1]) for (x, y) in pts)]


def unrot(px, py, deg=ANG, pivot=PIV, off=OFF):
    th = math.radians(deg); co, si = math.cos(th), math.sin(th)
    dx, dy = px - pivot[0] - off[0], py - pivot[1] - off[1]
    return (dx * co + dy * si + pivot[0], -dx * si + dy * co + pivot[1])


def torso_h(px, py):
    return IDL.torso_h(*unrot(px, py))


G = dict(
    torso=rot_pts(IDL.G['body']),
    speedo=[(16, 41), (24, 44), (34, 48), (44, 50), (45, 53), (40, 55), (33, 57), (26, 55), (19, 51), (15, 46)],
    # trailing arm (his right) flung back from the rear delt ~(20,24)
    t_upper=[(25, 20), (19, 16), (13, 15), (10, 17), (10, 23), (15, 26), (23, 30)],
    t_fore=[(13, 16), (8, 16), (5, 18), (5, 23), (9, 25), (14, 24)],
    t_fist=(4, 21),
    # leading arm (his left): delt ram at ~(51,42), forearm tucked, fist forward-low
    l_delt=(51.0, 41.0, 6.5, 6.5),
    l_fore=[(44, 43), (51, 43), (56, 45), (57, 50), (50, 51), (43, 49)],
    l_fist=(57, 48),
    # legs: split stride
    f_thigh=[(36, 50), (44, 51), (51, 52), (54, 56), (51, 59), (45, 57), (37, 56)],
    f_shin=[(46, 55), (53, 54), (54, 58), (53, 60), (47, 60), (46, 58)],
    f_boot=[(45, 58), (53, 58), (56, 60), (61, 61), (62, 64), (45, 64)],
    r_thigh=[(18, 46), (27, 49), (25, 54), (17, 57), (11, 59), (8, 56), (13, 51)],
    r_boot=[(2, 55), (9, 53), (12, 58), (15, 61), (16, 64), (3, 64), (0, 60)],
)


def draw_boot_tilted(c, poly):
    m = poly_mask(poly)
    under = copy(c)
    bot = max(y for y in range(H) for x in range(W) if m[y][x])
    for y in range(H):
        xs = [x for x in range(W) if m[y][x]]
        if not xs:
            continue
        xl, xr = min(xs), max(xs)
        for x in xs:
            ch = 'X'
            if x - xl <= 1:
                ch = 'v'
            if xr - x <= 1 or y == bot - 1:
                ch = 'x'
            c[y][x] = ch
    ol, pruned = outline_pixels(m)
    for y in range(H):
        for x in range(W):
            if ol[y][x]:
                c[y][x] = '#'
    for (x, y) in pruned:
        c[y][x] = under[y][x]


FIST_FAR = [  # trailing fist, knuckles back
    "..####..",
    ".#asss#.",
    "#aassdd#",
    "#asdsdf#",
    "#ssdfdf#",
    ".#ddff#.",
    "..####..",
]
FIST_LEAD = [  # lead fist, knuckles forward (same style as the idle hip fist)
    "..#####..",
    ".#ssaass#",
    "#ssssssd#",
    "#sdsdsdf#",
    "#dfdfdff#",
    ".#######.",
]
FIST_NEAR = [  # tucked fist under the delt
    ".#####.",
    "#assdd#",
    "#sdsdf#",
    "#dfdff#",
    ".#####.",
]


SPEED_B = [  # alternate speed-line set for the 2nd charge frame (shimmer)
    (2, 14, ["yZzzzzzzZy"]),
    (0, 33, ["yZzzzzzzzzZy"]),
    (4, 40, ["yZzzzzZy"]),
    (1, 47, ["yZzzzzzZy"]),
    (26, 6, ["yZzzzZy"]),
    (22, 62, ["yZzzzzzZy"]),
]
DUST_KICK = [
    "..lll..",
    ".lUuUl.",
    "lUuUiil",
    ".lIIIl.",
]
SPEED = [  # (x, y, rows) pale speed lines trailing left, no outline (house FX style)
    (0, 11, ["yZzzzzzzzZy"]),
    (3, 30, ["yZzzzzzZy"]),
    (0, 36, ["yZZzzzzzzzZy"]),
    (2, 43, ["yZzzzzZy"]),
    (22, 8, ["yZzzzzZy"]),
    (18, 62, ["yZzzzzzzZy"]),
]


def build(*args):
    fr = int(args[0]) if args and str(args[0]).isdigit() else 0
    body = blank()
    c = body
    FT = [0.0, 0.4, 0.66, 0.9, 1.01]
    # trailing arm behind
    hf_shade(c, poly_mask(G['t_upper']), lambda px, py: max(hcap(px, py, 23, 25, 12, 20, 5.0, 4.2), hdome(px, py, 16, 18, 5, 3.5, 4.5)), SKIN, FT)
    hf_shade(c, poly_mask(G['t_fore']), lambda px, py: hcap(px, py, 12, 20, 6, 21, 4.0, 3.4), SKIN, FT)
    block(c, G['t_fist'][0] - 4, G['t_fist'][1] - 3, FIST_FAR)
    # front leg + boot
    hf_shade(c, poly_mask(G['f_thigh']), lambda px, py: hcap(px, py, 38, 53, 51, 55, 5.0, 4.3), SKIN, TH_LIMB)
    hf_shade(c, poly_mask(G['f_shin']), lambda px, py: hcap(px, py, 50, 55, 50, 60, 4.0, 3.4), SKIN, TH_LIMB)
    draw_boot_tilted(c, G['f_boot'])
    # rear leg + boot (heel up)
    rl = blank()
    hf_shade(rl, poly_mask(G['r_thigh']), lambda px, py: hcap(px, py, 22, 50, 10, 58, 5.0, 3.6), SKIN, TH_LIMB)
    draw_boot_tilted(rl, G['r_boot'])
    if fr == 1:
        rl = shift_canvas(rl, 1, -3)   # rear foot kicks off the ground
    composite(c, rl)
    # torso (idle anatomy rotated 30deg)
    tm = poly_mask(G['torso'])
    hf_shade(c, tm, torso_h, SKIN, [0.05, 0.45, 0.70, 0.90, 0.99], crease=2, crease_th=1.2, zscale=0.9)
    despeckle(c, region=tm)
    merge_small_regions(c, tm, max_size=2)
    # speedo
    paint_part(c, poly_mask(G['speedo']), shade_normal(lambda x, y: sphere_normal(x, y, 24, 42, 24, 16), 'qPpOo', [0.0, 0.06, 0.34, 0.76]))
    # head
    hc = blank()
    HD.build_head(hc, 'CH', 'grit')
    composite(c, shift_canvas(hc, *HEAD_OFF))
    # leading arm: forearm + fist, then the delt ram on top
    hf_shade(c, poly_mask(G['l_fore']), lambda px, py: hcap(px, py, 45, 46, 55, 47, 4.5, 3.8), SKIN, TH_LIMB)
    block(c, G['l_fist'][0] - 4, G['l_fist'][1] - 4, FIST_LEAD)
    dx, dy, rx, ry = G['l_delt']
    hf_shade(c, ellipse_mask(dx, dy, rx, ry), lambda px, py: hdome(px, py, dx - 0.5, dy - 0.5, rx + 0.6, ry + 0.6, 7), SKIN, [0.0, 0.3, 0.55, 0.82, 0.975])
    out = blank()
    for (x, y, rows) in (SPEED if fr == 0 else SPEED_B):
        block(out, x, y, rows)
    if fr == 1:
        body = shift_canvas(body, 0, -1)   # airborne bob
        block(out, 2, 60, DUST_KICK)
    composite(out, body)
    return out


if __name__ == '__main__':
    c = build()
    save_png(c, os.path.join(OUT, 'charge_wip.png'))
    preview(c, os.path.join(OUT, 'charge_wip_8x.png'))
    open(os.path.join(OUT, 'charge_wip.txt'), 'w').write(to_text(c))
    print('ok')
