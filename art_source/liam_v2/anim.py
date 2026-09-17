"""Liam v2: glasses-push animation frames built from the polished base layers."""
import math, os
from lib import *
import build
from build import tcapsule_mask, tcapsule_normal, shade_fn, JACKET, layer, ribbon

def load_layer(name):
    return from_text(open('layers/%s.txt' % name).read())

def blk(L, x0, y0, rows):
    wd = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == wd, 'row %d (y=%d) len %d != %d: %r' % (i, y0 + i, len(r), wd, r)
    overlay(L, x0, y0, '\n'.join(rows))

def copy(L):
    return [r[:] for r in L]

# ------------------------------------------------------------------ arm pose builder
ARM_JTH = [0.25, 0.5, 0.78, 0.94]

def arm_pose(delt, up, fore, cuff=(0.8, 2.6), wrap_dir=0.9, draw_up=True, fore_on_top=True):
    """delt=(cx,cy,r); up=(ax,ay,bx,by,r0,r1) sleeve; fore=(ax,ay,bx,by,r0,r1) wrapped forearm (elbow->wrist).
    Sleeve (deltoid + upper arm) is painted and outlined, then the forearm is painted on top with its own outline."""
    L = layer()
    dcx, dcy, dr = delt
    m_delt = ellipse_mask(dcx, dcy, dr, dr)
    m_up = tcapsule_mask(*up)
    def jn(x, y):
        du = seg_dist(x + .5, y + .5, up[0], up[1], up[2], up[3])[0] / up[4]
        dd = math.hypot(x + .5 - dcx, y + .5 - dcy) / dr
        if dd < du:
            return sphere_normal(x, y, dcx, dcy, dr, dr)
        return tcapsule_normal(x, y, *up)
    if draw_up:
        paint_part(L, m_or(m_delt, m_up), shade_fn(jn, JACKET, ARM_JTH, wrap=0.3))
    ax, ay, bx, by, r0, r1 = fore
    flen = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / flen, (by - ay) / flen
    m_fore = tcapsule_mask(*fore)
    c0, c1 = cuff
    def ff(x, y):
        px, py = x + .5 - ax, y + .5 - ay
        al = px * ux + py * uy
        pe = -px * uy + py * ux
        v = lambert(tcapsule_normal(x, y, *fore))
        if al < c0:
            return 'J' if v > 0.5 else 'n'
        if al < c1:
            return 'i' if v > 0.8 else ('j' if v > 0.45 else 'J')
        if int(math.floor(al - c1 + pe * wrap_dir + 100)) % 3 == 2:
            return 'w' if v > 0.55 else 'v'
        return 'W' if v > 0.62 else ('w' if v > 0.3 else 'v')
    paint_part(L, m_fore, ff)
    # seam line between cuff and wraps
    for y in range(H):
        for x in range(W):
            if m_fore[y][x] and L[y][x] != '#':
                px, py = x + .5 - ax, y + .5 - ay
                al = px * ux + py * uy
                if c1 - 0.5 <= al < c1 + 0.5:
                    L[y][x] = '#'
    return L

# ------------------------------------------------------------------ head variants
LENS_FAR = [(x, y) for y in (14, 15, 16) for x in range(19, 24)]
LENS_NEAR = [(x, y) for y in (14, 15, 16) for x in range(27, 34)]

def head_dim_lenses(H_):
    """Dramatic dip: lenses catch a cool grey-blue reflection with a white diagonal streak (still opaque, no eyes)."""
    for (x, y) in LENS_FAR + LENS_NEAR:
        H_[y][x] = 'l'
    for (x, y) in [(20, 16), (21, 15), (22, 14), (29, 16), (30, 15), (31, 14), (32, 16), (33, 15)]:
        H_[y][x] = 'W'
    return H_

def head_flash_lenses(H_):
    for (x, y) in LENS_FAR + LENS_NEAR:
        H_[y][x] = 'W'
    return H_

SMIRK = [  # x 16..39, y 20..24 : tight smug smirk, a sliver of teeth on the near side; base silhouette edges kept
    "#hhHhhHHhkhHHhhk##hHhhh#",   # 20
    "#hHhhHhkhH#WWWWWW#hhHhh#",   # 21
    "#hhHhhkhHhh#WWWw#hHhhH#.",   # 22
    ".#hhHhHhhkhH####hHhhHh#.",   # 23
    ".#hHhhkhHhhHhhkhhhHhh#..",   # 24
]

def head_variant(base_head, mouth=None, lenses=None):
    H_ = copy(base_head)
    if lenses == 'dim':
        head_dim_lenses(H_)
    elif lenses == 'flash':
        head_flash_lenses(H_)
    if mouth == 'smirk':
        blk(H_, 16, 20, SMIRK)
    elif mouth == 'big':
        blk(H_, 16, 19, GRIN_BIG_ROWS)
    return H_

GRIN_BIG_ROWS = [  # x 16..39, y 19..25 : huge clenched grin, hooked corner; base silhouette edges kept
    "..................##....",   # 19  corner hook
    "#hhHhhHHhkhHHhhkhH#hHhh#",   # 20  mustache
    "#hH#WWWWWWWWWWWWWWW#hHh#",   # 21  upper teeth
    "#hhh#WWwWWwWWwWWwW#hHh#.",   # 22
    ".#hHh#############hHhh#.",   # 23  clench line
    ".#hHhh#WWwWWwWWW#hHhh#..",   # 24  lower teeth
    ".#hhHrH#########khHh#...",   # 25  lip line
]

# ------------------------------------------------------------------ FX
def star(L, cx, cy, arm, diag=0, core='W'):
    """4-point sparkle: long orthogonal rays of length `arm`, short diagonals `diag`. Outlined."""
    pts = {(cx, cy): core}
    for i in range(1, arm + 1):
        c = 'W' if i < arm else 'c'
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            pts[(cx + dx, cy + dy)] = c
    for i in range(1, diag + 1):
        for dx, dy in ((i, i), (-i, -i), (i, -i), (-i, i)):
            pts[(cx + dx, cy + dy)] = 'c'
    if arm >= 3:
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            pts[(cx + dx, cy + dy)] = 'W'
    # outline
    ol = set()
    for (x, y) in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pts:
                ol.add(q)
    for (x, y) in ol:
        if 0 <= x < W and 0 <= y < H:
            L[y][x] = '#'
    for (x, y), c in pts.items():
        if 0 <= x < W and 0 <= y < H:
            L[y][x] = c
    return L

# ------------------------------------------------------------------ compose
def compose(layers):
    cv = blank_chars()
    for l in layers:
        if l is not None:
            composite(cv, l)
    return cv

if __name__ == '__main__':
    os.makedirs('out/anim', exist_ok=True)
    B = {k: load_layer(k) for k in ('tails', 'legs', 'torso', 'far', 'near', 'head')}
    # push pose arm: high elbow beside the head, short wrapped forearm into the face
    push = arm_pose(delt=(11.5, 30.5, 5.2), up=(11, 31, 7, 25, 4.6, 3.5), fore=(7, 25, 17, 21, 3.4, 3.1), cuff=(0.4, 2.3))
    FIST_PUSH = [  # x 15..27, y 11..24 (head at dy=-1: bridge row y13)
        ".........##..",   # 11
        "........#as#.",   # 12
        "........#ad#.",   # 13
        "........#sd#.",   # 14
        "........#sd#.",   # 15
        ".......#fsd#.",   # 16
        "....####ssf#.",   # 17
        "...#aasssdf#.",   # 18
        "..#asssdddf#.",   # 19
        "..#sfsfsff#..",   # 20
        "..#ssdsddf#..",   # 21
        "..#dddfff#...",   # 22
        "...#ffff#....",   # 23
        "....####.....",   # 24
    ]
    blk(push, 15, 11, FIST_PUSH)
    head = shift(head_variant(B['head'], mouth='big', lenses='flash'), 0, -1)
    fx = layer()
    star(fx, 35, 12, 4, diag=1)
    cv = compose([B['tails'], B['legs'], B['torso'], B['near'], head, push, fx])
    open('out/anim/test_push.txt', 'w').write(to_text(cv))
    preview(cv, 'out/anim/test_push_8x.png')
    print('ok')
