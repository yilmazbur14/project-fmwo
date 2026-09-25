"""Captain Burak, the tutorial boss: the approval sprite. 2 frames of 96x96, feet on row 95, column 48
the anchor and the mirror axis (x' = 96 - x). Front view, lit from the upper left like the cast.

  frame 0  idle: the cocky stance. Cutlass resting on his right shoulder, the big flintlock hanging
           loosely from his left hand at the hip, weight on his left leg, the unimpressed smirk
  frame 1  the showy shot: the pistol arm thrust out at the viewer, a wink and a huge grin, a puff of
           smoke and a small cannonball leaving the bell muzzle (baked in for approval only)

Design: Burak's own face, hair, stubble, silver figaro chain and white tee (15-18.jpg) as a cocky
pirate captain, an original homage to a pirate-captain archetype: a black gold-trimmed tricorn
tilted back on his hair, an open crimson greatcoat with gold trim and buttons and its sleeves
pushed up, a red sash with a gold buckle, dark trousers, tall black boots, a brass-hilted cutlass
and an oversized bell-mouthed flintlock that fires cannonballs.

Build order is back to front. Parts stamped with an outline cut a 1px black keyline into whatever is
under their edge; that is where the interior separations come from.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import head as H  # noqa: E402
from kit import (Canvas, amap, capsule, cylinder, ellipse, ellipsoid, fill, image, line, lock,  # noqa: E402,F401
                 paint, poly, polyline, rect, rim, span, stroke)

AX = 96


def mir(pts):
    return [(AX - x, y) for (x, y) in pts]


def mirp(part):
    return {(AX - x, y): k for (x, y), k in part.items()}


def vshade(part, ramp, cuts, lo_hi=None):
    """Shade a part across each row like a cylinder facing the viewer, lit from the left: t runs 0..1
    across the row's span; cuts are ascending thresholds, one fewer than the ramp (light -> dark)."""
    for (x, y) in list(part):
        lo, hi = lo_hi if lo_hi else span(part, y)
        t = (x - lo) / max(1, hi - lo)
        k = ramp[-1]
        for kk, c in zip(ramp, cuts):
            if t < c:
                k = kk
                break
        part[(x, y)] = k


# ------------------------------------------------------------------ the coat

COAT_LEFT = [(41, 46), (37, 47.5), (33, 49.5), (30.5, 52), (29.5, 55), (30, 60), (31, 66), (31, 71),
             (30, 78), (29, 84), (28, 88.5), (37.5, 89), (39.5, 80), (42, 72), (42, 66), (41, 58),
             (41, 54), (42, 50), (43.5, 47.5)]


def sweep_pts(pts, sweep):
    """The skirt blown back by `sweep` px at the hem (0 at the waist), for a run. 0 leaves it as approved."""
    if not sweep:
        return pts
    return [(x - sweep * max(0.0, (y - 70) / 18.0) ** 1.3, y) for (x, y) in pts]


def coat_back(sweep=0.0):
    """The coat's back panel, seen between the parted skirts behind the legs: the dark lining."""
    p = fill(poly(sweep_pts([(42, 70), (54, 70), (58.5, 88.5), (37.5, 88.5)], sweep)), 'v')
    for (x, y) in list(p):
        if y >= 86:
            p[(x, y)] = 'V'
    return p


def coat_panel(side, flare=False, sweep=0.0):
    """One front panel with its sleeve-side shoulder, the skirt, gold trim down the opening and along
    the hem, and brass buttons. side 0 = screen left (lit), 1 = screen right (shade). flare: the skirt
    kicked out by the blast."""
    pts = COAT_LEFT if side == 0 else mir(COAT_LEFT)
    if flare:
        pts = [(x + 1.5 * max(0.0, (y - 70) / 18.0) ** 1.4 * 2, y - 1.2 * max(0.0, (y - 78) / 10.0))
               if x > 60 else (x, y) for (x, y) in pts]
    pts = sweep_pts(pts, sweep)
    p = fill(poly(pts), 'R')
    # the torso as a cylinder: lit near the left edge of the whole coat, dark at the right
    for (x, y) in list(p):
        t = (x - 29.0) / 38.0
        if y < 70:
            k = 'T' if t < 0.14 else ('R' if t < 0.62 else ('V' if t < 0.9 else 'v'))
        else:
            k = 'T' if t < 0.1 else ('R' if t < 0.66 else ('V' if t < 0.92 else 'v'))
        p[(x, y)] = k
    # skirt folds: long dark creases down from the hip
    folds = [[(34, 74), (33, 81), (32, 88)], [(38, 76), (37.5, 83), (37, 88)]]
    if side == 1:
        folds = [mir(f) for f in folds]
    folds = [sweep_pts(f, sweep) for f in folds]
    for f in folds:
        stroke(p, f, 'V' if side == 0 else 'v', only='TRV')
    # gold trim down the opening edge and along the hem (2px), keyline between comes from the stamp
    edge = [(43.5, 47.5), (42, 50), (41, 54), (41, 58), (42, 66), (42, 72), (39.5, 80), (37.5, 89)]
    if side == 1:
        edge = mir(edge)
    ex = {}
    for (x, y) in p:
        lo, hi = span(p, y)
        ex[(x, y)] = (lo, hi)
    for (x, y) in list(p):
        lo, hi = ex[(x, y)]
        inner = hi if side == 0 else lo
        d = abs(x - inner)
        if d == 0:
            p[(x, y)] = 'O' if side == 0 else 'o'
        elif d == 1:
            p[(x, y)] = 'G' if side == 0 else 'G'
        if y >= 88:
            p[(x, y)] = 'G' if side == 0 else 'g'        # the hem's gold band, rounded: lit on top
        if y == 87:
            p[(x, y)] = 'O' if side == 0 else 'o'
    # the hem trim's top edge gets a dark line so it reads as a band
    for (x, y) in list(p):
        if y == 86 and p[(x, y)] in 'TRVv':
            p[(x, y)] = 'v'
    # buttons: brass, in a row beside the trim
    bx = 38 if side == 0 else 58
    for by in (55, 60, 65):
        for q, k in (((bx, by), 'O'), ((bx + 1, by), 'o'), ((bx, by + 1), 'o'), ((bx + 1, by + 1), 'G')):
            if side == 1:
                k = {'O': 'o', 'o': 'G', 'G': 'g'}[k]
            if q in p:
                p[q] = k
    return p


def collar():
    """The coat's collar standing up round the back of his neck, gold-edged, behind the head."""
    p = fill(poly([(38, 48), (41, 44.5), (47, 43.5), (49, 43.5), (55, 44.5), (58, 48), (54, 49), (48, 47.5),
                   (42, 49)]), 'V')
    for (x, y) in list(p):
        if x < 44:
            p[(x, y)] = 'R'
        if x > 52:
            p[(x, y)] = 'v'
    rim(p, 'o', 0, -1)
    return p


# ------------------------------------------------------------------ the tee, the chain, the sash

def tee():
    """His white tee in the coat's opening, a crewneck round the neck."""
    p = fill(poly([(40, 48), (56, 48), (56, 71), (40, 71)]), 'w')
    for (x, y) in list(p):
        t = (x - 40) / 16.0
        k = 'W' if t < 0.3 else ('w' if t < 0.62 else 'e')
        if y >= 62 and k == 'w':
            k = 'e' if t > 0.5 else 'w'
        if y >= 66:
            k = 'e' if t < 0.7 else 'f'                  # in the sash's shadow
        p[(x, y)] = k
    # pecs: a soft shadow under each and down the breastbone
    for q in ((43, 57), (44, 57), (45, 57), (51, 57), (52, 57), (53, 57), (48, 53), (48, 54), (48, 55)):
        if q in p and p[q] in 'Ww':
            p[q] = 'e'
    return p


def tee_collar():
    """The crewneck's ribbed edge round the base of his neck."""
    pts = [(43, 49), (44, 50), (45, 51), (46, 51), (47, 51), (48, 51), (49, 51), (50, 51), (51, 51), (52, 50), (53, 49)]
    return {q: ('e' if q[0] > 49 else 'w') for q in pts}


def chain():
    """The silver figaro chain in a U on his chest: two bright links, one dark, repeating, with a
    shadow under it so it reads on the white tee."""
    path = [(44, 50), (44, 52), (45, 54), (46, 55), (47, 56), (48, 56), (49, 56), (50, 55), (51, 54), (52, 52), (52, 50)]
    px = polyline(path)
    out = {}
    for i, q in enumerate(px):
        out[q] = 'A' if i % 3 == 2 else 'B'
        if i % 3 == 2:
            out[q] = 'z'
    for q in px:
        below = (q[0], q[1] + 1)
        if below not in out:
            out[below] = 'e'
    out[(48, 57)] = 'Z'                                   # the clasp at the bottom of the U
    return out


def sash():
    """The red sash wound round his waist, a big gold buckle at the front, the knot's tails hanging
    over his right hip (screen left)."""
    band = fill(poly([(40, 66), (56, 66), (56, 71.5), (40, 71.5)]), 'X')
    for (x, y) in list(band):
        if y == 66:
            band[(x, y)] = 'y'
        elif y >= 71:
            band[(x, y)] = 'x'
        if x >= 54:
            band[(x, y)] = 'x' if y > 66 else 'X'
    # wraps: two soft diagonal folds
    stroke(band, [(41, 68), (43, 70)], 'x', only='X')
    stroke(band, [(52, 67), (54, 69)], 'x', only='X')
    tails = fill(poly([(40, 70), (44, 70), (44.5, 76), (43, 81), (41, 80.5), (40.5, 76)]), 'X')
    for (x, y) in list(tails):
        lo, hi = span(tails, y)
        tails[(x, y)] = 'y' if x == lo else ('x' if x == hi else 'X')
    stroke(tails, [(42, 72), (42, 79)], 'x', only='X')
    return band, tails


BUCKLE = [
    # x: 45-51          y
    "kkkkkkk",       # 65
    "kYOOOok",       # 66
    "kOkkkGk",       # 67
    "kOkqkGk",       # 68  the prong over the dark strap
    "kokkkgk",       # 69
    "koGGGgk",       # 70
    "kkkkkkk",       # 71
]


def ribbon(x0, y0, length, slope, amp, phase, w0, w1, wave=3.6):
    """A fluttering ribbon streaming right from (x0, y0): an S-waved centreline, tapering from w0 to
    w1, ending in a forked tip. Lit along its top edge, shaded under each crest."""
    pts = []
    for i in range(int(length * 4) + 1):
        t = i / (length * 4.0)
        x = x0 + length * t
        y = y0 + slope * length * t + amp * math.sin((x - x0) / wave + phase) * min(1.0, t * 3)
        pts.append((x, y, w0 + (w1 - w0) * t))
    shape = set()
    for (x, y, w) in pts:
        shape |= ellipse(x, y, max(0.6, w * 0.55), w)
    # the forked tip: a notch cut into the end
    ex, ey, _ = pts[-1]
    for q in list(shape):
        if q[0] >= ex - 1 and abs(q[1] - ey) < 0.6:
            shape.discard(q)
    p = {}
    for q in shape:
        # the centreline's y at this x
        cy = min(pts, key=lambda c: abs(c[0] - q[0]))[1]
        d = q[1] - cy
        slope_here = math.cos((q[0] - x0) / wave + phase)
        k = 'y' if d < -0.6 else ('X' if d < 0.7 else 'x')
        if slope_here < -0.5 and k == 'X':
            k = 'x'                                        # the ribbon turning under
        p[q] = k
    return p


def bandana_tails(flutter=0.0):
    """The player Burak's red headband, worn as a bandana under the tricorn: a sliver of the band
    under the brim, the knot behind his ear, and its two tails streaming out (as on bust_burak.png)."""
    band = {}
    for x in range(58, 66):
        band[(x, 14 if x < 62 else 15)] = 'X' if x < 63 else 'x'
    knot = {(63, 16): 'X', (64, 16): 'y', (65, 16): 'X', (63, 17): 'x', (64, 17): 'X', (65, 17): 'x',
            (64, 18): 'x'}
    t1 = ribbon(65, 15.2, 18 + flutter * 2, -0.22, 0.9, 0.0, 2.3, 1.3, wave=4.5)
    t2 = ribbon(65, 17.8, 15 + flutter * 2, 0.26, 0.9, 2.2, 2.1, 1.2, wave=4.5)
    return [t2, t1, band, knot]


def headset():
    """His gaming headset (15.jpg) slung round his neck: black over-ear cups resting on the coat's
    collar either side of his neck, the band behind, a boom mic hanging off the left cup."""
    left = amap([
        # x: 37-42
        ".kkkk.",      # 45
        "kturrk",      # 46  the cup's rim catches the light
        "ktrrqk",      # 47
        "krrqqk",      # 48
        "krqqqk",      # 49
        ".kkkk.",      # 50
    ], 37, 45)
    right = {(96 - x - 1, y): {'u': 't', 't': 'r', 'r': 'q', 'q': 'q', 'k': 'k'}[k] for (x, y), k in left.items()}
    mic = {(38, 51): 'k', (38, 52): 'k', (39, 53): 'k', (40, 54): 'k', (41, 54): 'k', (42, 55): 't', (42, 54): 'k',
           (43, 55): 'k', (42, 56): 'k'}
    return [left, right, mic]


# ------------------------------------------------------------------ legs and boots

def legs():
    """Dark trousers: his right leg (screen left) relaxed with the knee bent out, the weight on the
    straight left leg (screen right)."""
    near = poly([(41.5, 71), (48, 71), (47, 76), (44.5, 82), (39, 82), (39.5, 76)])
    far = poly([(48, 71), (55, 71), (56.5, 77), (57, 82), (51.5, 82), (50.5, 77)])
    p = fill(near | far, '9')
    for (x, y) in list(p):
        lo, hi = span(near if (x, y) in near else far, y)
        t = (x - lo) / max(1, hi - lo)
        p[(x, y)] = '0' if t < 0.18 else ('9' if t < 0.6 else ('8' if t < 0.88 else '7'))
    stroke(p, [(48, 71), (48, 75)], '7')                  # the crotch seam
    stroke(p, [(49, 75), (51, 79)], '7', only='90')       # far thigh in the near thigh's shadow
    return p


def boot(side):
    """A tall black boot with a flared cuff turned down at the knee. side 0 = screen left."""
    if side == 0:
        cuff = poly([(37, 80), (46.5, 80), (46, 84.5), (38, 84.5)])
        shaft = poly([(38.5, 84), (45.5, 84), (45, 90), (44, 92), (38.5, 92)])
        foot = poly([(38.5, 89.5), (44.5, 89.5), (45, 92.5), (44.5, 94), (33, 94), (32.5, 92.5), (35, 91)])
    else:
        cuff = poly([(50, 80), (59.5, 80), (58.5, 84.5), (50.5, 84.5)])
        shaft = poly([(51, 84), (58, 84), (58, 92), (51.5, 92)])
        foot = poly([(51.5, 89.5), (57.5, 89.5), (60.5, 91), (63, 92.5), (63, 94), (51.5, 94)])
    parts = []
    for shape, lit in ((shaft | foot, True), (cuff, True)):
        p = fill(shape, 'r')
        for (x, y) in list(p):
            lo, hi = span(p, y)
            t = (x - lo) / max(1, hi - lo)
            p[(x, y)] = 't' if t < 0.2 else ('r' if t < 0.6 else 'q')
        parts.append(p)
    boots, cuffp = parts
    for (x, y) in list(boots):                           # the sole
        if y == 94:
            boots[(x, y)] = 'q'
    for (x, y) in list(cuffp):                           # the cuff's rolled top edge catches the light
        if y == 80:
            cuffp[(x, y)] = 'u' if cuffp[(x, y)] == 't' else 't'
    for (x, y) in list(boots):                           # a glint down the lit side of the shaft
        lo, hi = span(boots, y)
        if x == lo + 1 and 85 <= y <= 90:
            boots[(x, y)] = 'u'
    return boots, cuffp


# ------------------------------------------------------------------ arms

def limb(segments, base, lit, shade, dark=None):
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= capsule(p0, p1, r0, r1)
    p = fill(shape, base)
    rim(p, lit, -1, 0)
    rim(p, lit, 0, -1, only=base)
    rim(p, shade, 1, 0)
    rim(p, shade, 0, 1, only=base)
    if dark:
        rim(p, dark, 1, 0, only=shade)
    return p


def sleeve(p0, p1, r0, r1, lit_side=True):
    """An upper arm in the coat sleeve, pushed up to the elbow where it bunches into a gold-edged cuff."""
    s = fill(capsule(p0, p1, r0, r1), 'R')
    cylinder(s, p0, p1, r0, 'TRVv', (0.55, 0.2, -0.25), tilt=0.2)
    if not lit_side:
        for q, k in list(s.items()):
            s[q] = {'T': 'R', 'R': 'V', 'V': 'v', 'v': 'v'}[k]
    return s


def cuff(center, w, h, lit=True):
    """The bunched, pushed-up sleeve: a crimson roll with gold trim at its lower edge."""
    cx, cy = center
    p = fill(poly([(cx - w, cy - h), (cx + w, cy - h), (cx + w + 0.5, cy + h), (cx - w - 0.5, cy + h)]), 'R')
    for (x, y) in list(p):
        lo, hi = span(p, y)
        t = (x - lo) / max(1, hi - lo)
        p[(x, y)] = ('T' if t < 0.3 else ('R' if t < 0.75 else 'V')) if lit else ('R' if t < 0.4 else 'V')
    ys = sorted({y for (_, y) in p})
    for (x, y) in list(p):
        if y == ys[-1]:
            p[(x, y)] = 'O' if (lit and x < cx) else 'o'
        elif y == ys[-2]:
            p[(x, y)] = 'G'
    return p


def cuff_d(center, axis, w, h):
    """The bunched, pushed-up sleeve on an angled arm: a crimson roll across the arm, gold-edged on
    the side toward the hand. axis: the arm's direction (toward the hand)."""
    cx, cy = center
    ax, ay = axis
    ln = math.hypot(ax, ay)
    ax, ay = ax / ln, ay / ln
    nx, ny = -ay, ax
    pts = [(cx - ax * w + nx * h, cy - ay * w + ny * h), (cx + ax * w + nx * h, cy + ay * w + ny * h),
           (cx + ax * w - nx * h, cy + ay * w - ny * h), (cx - ax * w - nx * h, cy - ay * w - ny * h)]
    p = fill(poly(pts), 'R')
    for (x, y) in list(p):
        along = (x - cx) * ax + (y - cy) * ay
        across = (x - cx) * nx + (y - cy) * ny
        p[(x, y)] = 'o' if along > w - 1.0 else ('R' if across < 0 else 'V')
    return p


def cuff_v(center, w, h):
    """The bunched, pushed-up sleeve on an outstretched arm: a crimson roll, gold-edged on its far side."""
    cx, cy = center
    p = fill(poly([(cx - w, cy - h), (cx + w, cy - h - 0.5), (cx + w, cy + h + 0.5), (cx - w, cy + h)]), 'R')
    for (x, y) in list(p):
        p[(x, y)] = 'R' if y < cy - h * 0.3 else 'V'
        if x >= cx + w - 0.5:
            p[(x, y)] = 'o' if y < cy else 'G'
    return p


# The fist round the cutlass grip, knuckles to the viewer: the thumb over the top, the fingers
# stacked below it, the brass knuckle-bow running down the outside from the shell guard to the pommel.
FIST_SWORD = [
    # x: 29-33 34-38 39      y
    "..kkk kkk.. .",      # 50
    ".kYOo oGk.. .",      # 51  the shell guard, where the blade leaves the hilt
    "kOkkk kkkkk .",      # 52
    "kOk22 2334k .",      # 53  the thumb over the top of the grip
    "kok33 4445k .",      # 54
    "kGk22 3345k .",      # 55  first finger
    "kok44 4555k .",      # 56
    "kGk33 3445k .",      # 57  second finger
    "kok44 555k. .",      # 58
    ".kGk. kkk.. .",      # 59  the bow meets the pommel
    "..kOo Gk... .",      # 60  pommel
    "...kk k.... .",      # 61
]


def cutlass(p_guard, p_tip, bow=2.5, w_base=2.6, w_max=4.0):
    """A curved cutlass blade from the guard to the tip, broad and widening toward the clipped point.
    `bow` > 0 curves it out to the left of guard->tip; the cutting edge runs along that convex side.
    Across the blade (back -> edge): the dark back, the steel flat, a bright bevel, the edge."""
    gx, gy = p_guard
    tx, ty = p_tip
    dx, dy = tx - gx, ty - gy
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux                                      # left of the direction: the convex, edge side
    back, edge, mids = [], [], []
    n = 30
    for i in range(n + 1):
        t = i / float(n)
        bend = bow * math.sin(math.pi * t)
        cx, cy = gx + dx * t + nx * bend, gy + dy * t + ny * bend
        w = w_base + (w_max - w_base) * min(1.0, t / 0.8)
        if t > 0.8:                                       # the clipped point
            w *= max(0.05, 1 - (t - 0.8) / 0.2)
        back.append((cx - nx * 1.0, cy - ny * 1.0))
        edge.append((cx + nx * (w - 1.0), cy + ny * (w - 1.0)))
        mids.append((cx, cy))
    blade = poly(back + [p_tip] + list(reversed(edge)))
    part = {}
    for q in blade:
        best, bi = 1e9, 0
        for i in range(n + 1):
            d = (q[0] - mids[i][0]) ** 2 + (q[1] - mids[i][1]) ** 2
            if d < best:
                best, bi = d, i
        sx, sy = back[bi]
        ex_, ey = edge[bi]
        w2 = (ex_ - sx) ** 2 + (ey - sy) ** 2 or 1
        s = ((q[0] - sx) * (ex_ - sx) + (q[1] - sy) * (ey - sy)) / w2
        k = 'z' if s < 0.22 else ('Z' if s < 0.5 else ('A' if s < 0.78 else 'B'))
        if k == 'B' and 0.25 < bi / n < 0.6:
            k = 'W'                                       # a glint running along the edge
        part[q] = k
    return part


# ------------------------------------------------------------------ the pistol

# The big flintlock, parts in profile. Every piece is keylined as it is stamped.

def pistol_parts(breech, barrel_dir, grip_dir, barrel_len=13.0, grip_len=8.0, bell_len=6.0,
                 r_bar=1.9, r_bell=4.6, mouth_tip=0.5):
    """A cartoon blunderbuss-pistol laid out from the breech point: a walnut grip running back along
    grip_dir to a brass butt cap, a steel lock with the hammer cocked over it, a brass-banded steel
    barrel along barrel_dir, a flared brass bell, and the mouth (a brass rim round a dark bore) turned
    `mouth_tip` of the way toward the viewer. Returns the parts back to front."""
    bx, by = breech
    ux, uy = barrel_dir
    ln = math.hypot(ux, uy)
    ux, uy = ux / ln, uy / ln
    gx, gy = grip_dir
    gl = math.hypot(gx, gy)
    gx, gy = gx / gl, gy / gl
    nx, ny = -uy, ux                                        # across the barrel

    def across(q, o, r):
        return ((q[0] - o[0]) * nx + (q[1] - o[1]) * ny) / r

    def along(q, o, L):
        return ((q[0] - o[0]) * ux + (q[1] - o[1]) * uy) / L

    def lit(s, keys):                                       # keys: light, mid, dark across the round
        return keys[0] if s < -0.25 else (keys[1] if s < 0.4 else keys[2])

    parts = []
    # the grip, back from the breech, thickening to the butt
    g1 = (bx + gx * grip_len, by + gy * grip_len)
    grip = capsule((bx, by), g1, 1.8, 2.3)
    parts.append({q: lit(((q[0] - bx) * -gy + (q[1] - by) * gx) / 2.1, '098') for q in grip})
    cap = ellipse(g1[0] + gx * 1.3, g1[1] + gy * 1.3, 2.3, 2.3)
    parts.append({q: ('O' if (q[0] - g1[0]) * -0.6 + (q[1] - g1[1]) * -0.8 > 0 else 'G') for q in cap})
    # the bell: flares from the barrel's end to the mouth
    e0 = (bx + ux * barrel_len, by + uy * barrel_len)
    e1 = (e0[0] + ux * bell_len, e0[1] + uy * bell_len)
    bell = poly([(e0[0] + nx * r_bar, e0[1] + ny * r_bar), (e1[0] + nx * r_bell, e1[1] + ny * r_bell),
                 (e1[0] - nx * r_bell, e1[1] - ny * r_bell), (e0[0] - nx * r_bar, e0[1] - ny * r_bar)])
    bp = {}
    for q in bell:
        a_ = max(0.0, min(1.0, along(q, e0, bell_len)))
        s = across(q, e0, r_bar + (r_bell - r_bar) * a_)
        bp[q] = 'Y' if (-0.7 < s < -0.3 and a_ > 0.25) else lit(s, 'Oog')
    parts.append(bp)
    # the barrel: steel, round, two brass bands
    bar = capsule((bx, by), e0, r_bar, r_bar)
    brp = {}
    for q in bar:
        s = across(q, (bx, by), r_bar)
        a_ = along(q, (bx, by), barrel_len)
        brp[q] = lit(s, 'OoG') if (0.28 < a_ < 0.42 or 0.7 < a_ < 0.84) else lit(s, 'BAz')
    parts.append(brp)
    # the mouth, a rim round the bore, set perpendicular to the barrel and tipped toward us
    ry = max(1.2, r_bell * mouth_tip)
    mp = {}
    for yy in range(int(e1[1]) - 7, int(e1[1]) + 8):
        for xx in range(int(e1[0]) - 7, int(e1[0]) + 8):
            s = across((xx, yy), e1, r_bell + 0.4)
            t = along((xx, yy), e1, ry)
            d = s * s + t * t
            if d <= 1.0:
                mp[(xx, yy)] = 'q' if d < 0.42 else ('O' if s < 0 else 'o')
    parts.append(mp)
    # the lock plate at the breech, the hammer cocked back over it
    lk = ellipse(bx, by, 2.4, 2.1)
    parts.append({q: ('B' if q[1] <= by - 1 else ('A' if q[1] <= by else 'z')) for q in lk})
    h0 = (bx - ux * 1.0 - nx * 1.6, by - uy * 1.0 - ny * 1.6)
    h1 = (bx - ux * 2.6 - nx * 4.2, by - uy * 2.6 - ny * 4.2)
    ham = capsule(h0, h1, 1.0, 1.3)
    parts.append({q: ('B' if q[1] < h1[1] + 1 else 'Z') for q in ham})
    return parts


def hand_pistol():
    """His left hand round the grip, knuckles to the viewer, the pistol hanging loose at the hip."""
    return amap([
        # x: 65-72
        "..kkkk..",     # 65
        ".k2233k.",     # 66  the back of the hand
        "k223334k",     # 67
        "k24345kk",     # 68  knuckles, the fingers curling round the grip
        "k334455k",     # 69
        ".k44555k",     # 70
        "..kkkkk.",     # 71
    ], 65, 65)


def hammer(x, y, flip=False):
    """The flintlock's hammer, cocked: a small steel hook."""
    pts = {(x, y): 'k', (x + 1, y): 'k', (x - 1, y + 1): 'k', (x, y + 1): 'B', (x + 1, y + 1): 'Z',
           (x + 2, y + 1): 'k', (x - 1, y + 2): 'k', (x, y + 2): 'A', (x + 1, y + 2): 'k',
           (x, y + 3): 'k'}
    return pts


# The shot: his left arm thrust out at the viewer, the pistol's bell turned almost fully toward us.
def fist_gun():
    """His left fist round the grip, knuckles to the viewer, the index finger on the trigger."""
    return amap([
        # x: 74-81
        "..kkkk..",     # 62
        ".k2233k.",     # 63
        "k2233334k",    # 64
        "k2434545k",    # 65  knuckles
        "k3344555k",    # 66
        ".k445555k",    # 67
        "..kkkkkk.",    # 68
    ], 74, 62)


def puff_cloud(puffs):
    """A chunky keylined cartoon smoke cloud from a few round lobes (cx, cy, r): bright white, a grey
    underside on each lobe's lower right, so the scalloped lobes read."""
    shape = set()
    for (cx, cy, r) in puffs:
        shape |= ellipse(cx, cy, r, r)
    p = fill(shape, 'W')
    for (cx, cy, r) in puffs:
        for q in ellipse(cx, cy, r, r):
            u, v = (q[0] - cx) / r, (q[1] - cy) / r
            if u * 0.62 + v * 0.78 > 0.55 and q in p and p[q] == 'W':
                p[q] = 'w'
    rim(p, 'e', 1, 0, only='w')
    rim(p, 'e', 0, 1, only='w')
    return p


def flash(cx, cy, s=1.0):
    """The muzzle flash: a fat star, four long rays and four short, white-hot at the core."""
    shape = ellipse(cx, cy, 2.9 * s, 2.9 * s)
    for i in range(8):
        a = math.radians(i * 45 - 90)
        L = (7.5 if i % 2 == 0 else 4.8) * s
        ux, uy = math.cos(a), math.sin(a)
        wb = 1.9 * s
        shape |= poly([(cx - uy * wb, cy + ux * wb), (cx + ux * L, cy + uy * L), (cx + uy * wb, cy - ux * wb)])
    p = {}
    for q in shape:
        d = math.hypot(q[0] - cx, q[1] - cy)
        p[q] = 'W' if d < 1.8 * s else ('Y' if d < 3.4 * s else ('O' if d < 5.2 * s else 'o'))
    return p


FIST_GUN = amap([
    # x: 74-83
    "..kkkkkk..",    # 54
    ".k222333k.",    # 55  the thumb over the grip
    "kk2223334k",    # 56  the wrist's crease
    "k3k434545k",    # 57  knuckles
    "k43344555k",    # 58
    ".kk445555k",    # 59
    "...kkkkkk.",    # 60
], 74, 54)


MUZZLE = (86, 70)                  # frame 1: the bell mouth's centre, where the cannonball spawns


def bell_wedge(exit_, mouth, r0, r1):
    """The barrel and bell in forced perspective: a flaring trumpet from the fist to the mouth.
    Steel near the fist with a brass band, then the brass bell; lit along its upper-left side."""
    ex, ey = exit_
    mx, my = mouth
    dx, dy = mx - ex, my - ey
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    shape = poly([(ex + nx * r0, ey + ny * r0), (mx + nx * r1, my + ny * r1),
                  (mx - nx * r1, my - ny * r1), (ex - nx * r0, ey - ny * r0)])
    p = {}
    for q in shape:
        a = ((q[0] - ex) * ux + (q[1] - ey) * uy) / L
        w = r0 + (r1 - r0) * max(0.0, min(1.0, a))
        s = ((q[0] - ex) * nx + (q[1] - ey) * ny) / max(0.6, w)
        if a < 0.3:
            k = 'B' if s > 0.3 else ('A' if s > -0.3 else 'z')
        elif a < 0.42:
            k = 'O' if s > 0.2 else ('o' if s > -0.4 else 'G')
        else:
            k = 'Y' if 0.35 < s < 0.7 else ('O' if s > -0.1 else ('o' if s > -0.6 else 'G'))
        p[q] = k
    return p


def bell_mouth(exit_, mouth, r_across, r_along, fire=True):
    """The bell's mouth facing us: a brass rim round the bore, white-hot with the blast when firing,
    dark when not."""
    ex, ey = exit_
    mx, my = mouth
    dx, dy = mx - ex, my - ey
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    p = {}
    for y in range(int(my) - 8, int(my) + 9):
        for x in range(int(mx) - 8, int(mx) + 9):
            s = ((x - mx) * nx + (y - my) * ny) / r_across
            t = ((x - mx) * ux + (y - my) * uy) / r_along
            d = s * s + t * t
            if d <= 1.0:
                if d > 0.5:
                    p[(x, y)] = 'o' if s > 0.3 else ('G' if s > -0.5 else 'g')
                elif d > 0.38:
                    p[(x, y)] = 'k'
                elif fire:
                    p[(x, y)] = 'o' if d > 0.26 else ('Y' if d > 0.1 else 'W')
                else:
                    p[(x, y)] = 'r' if d > 0.26 else 'q'
    return p


def flash_spikes(cx, cy, angles, lengths, r0=5.0, half=1.9):
    """Flame spikes bursting from the rim in the firing direction: white at the root, then yellow,
    orange-gold at the tips. angles in degrees (0 = right, 90 = down)."""
    parts = []
    for ang, L in zip(angles, lengths):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        b0 = (cx + ux * r0 - uy * half, cy + uy * r0 + ux * half)
        b1 = (cx + ux * r0 + uy * half, cy + uy * r0 - ux * half)
        tip = (cx + ux * (r0 + L), cy + uy * (r0 + L))
        sp = poly([b0, tip, b1])
        p = {}
        for q in sp:
            d = math.hypot(q[0] - cx, q[1] - cy)
            p[q] = 'Y' if d < r0 + L * 0.35 else ('O' if d < r0 + L * 0.7 else 'o')
        parts.append(p)
    return parts


def cannonball(cx, cy, r=3.2):
    b = ellipse(cx, cy, r, r)
    p = {}
    for q in b:
        u, v = (q[0] - cx) / r, (q[1] - cy) / r
        i = u * -0.55 + v * -0.62
        p[q] = 't' if i > 0.45 else ('r' if i > -0.1 else 'q')
    p[(int(round(cx - r * 0.45)), int(round(cy - r * 0.45)))] = 'W'
    return p


# ------------------------------------------------------------------ frames

def build(frame, fx=True):
    """fx=False leaves the shot's baked-in flash, smoke and cannonball out of frame 1."""
    cv = Canvas()

    def put(part, dx=0, dy=0, outline=True, owner=None):
        cv.stamp({(x + dx, y + dy): k for (x, y), k in part.items()} if (dx or dy) else part, outline, owner)

    shot = frame == 1
    hx, htilt = (-2, -0.06) if shot else (0, 0.0)          # the shot: head cocked, hat knocked rakish
    put(coat_back())
    put(legs())
    for b_, c_ in (boot(0), boot(1)):
        put(b_)
        put(c_)
    put(tee())
    band, tails = sash()
    put(band)
    put(amap(BUCKLE, 45, 65), outline=False)
    put(coat_panel(1, flare=shot))
    put(coat_panel(0))
    put(tails)
    put(collar(), dx=hx // 2)
    put(H.neck(), dx=hx)
    put(tee_collar(), dx=hx // 2, outline=False)
    put(chain(), dx=hx // 2, outline=False)
    if HEADSET:
        for p_ in headset():
            put(p_, dx=hx // 2, outline=False)
    if not shot:
        # the pistol arm (screen right), hanging at his side with a gap to the body, the big pistol
        # dangling from his hand, barrel down and out
        put(sleeve((64.5, 53), (68, 62), 4.6, 3.9, lit_side=False))
        put(cuff((68.5, 63.5), 3.8, 1.5, lit=False))
        put(limb([((69, 65.5), (69.5, 68), 2.7, 2.5)], '4', '3', '5', '6'))
        for part in pistol_parts((71.5, 70.5), (0.66, 1.0), (-1.0, 0.3), barrel_len=12.5, grip_len=5.0,
                                 bell_len=6.5, r_bar=2.2, r_bell=5.2, mouth_tip=0.5):
            put(part)
        put(hammer(70, 66))
        put(hand_pistol(), outline=False)
    else:
        # the shot: his left arm thrust out, the pistol pointed at the viewer in forced perspective:
        # the barrel flares from his fist to a big bell mouth facing us, fire in the bore; a flash
        # bursts toward us out of a billow of smoke, and the small cannonball flies out at the player
        if fx:
            put(puff_cloud([(84.5, 81.5, 4.2), (90, 80, 3.8), (87.5, 86.5, 3.2), (91, 73.5, 2.6)]))
        put(sleeve((64, 53), (70, 57.5), 4.5, 4.0, lit_side=False))
        put(cuff_d((71.8, 59), (0.8, 0.6), 1.5, 4.0))
        put(limb([((73.3, 60.5), (75, 61.8), 2.9, 2.8)], '4', '3', '5', '6'))
        exit_, mouth = (81, 63.5), MUZZLE
        put(bell_wedge(exit_, mouth, 2.3, 5.4))
        put(FIST_GUN, dy=4, outline=False)
        put(hammer(79, 54))
        if fx:
            for sp in flash_spikes(mouth[0], mouth[1], (8, 40, 70, 100, 135), (3.0, 5.0, 8.0, 7.0, 5.0)):
                put(sp)
        put(bell_mouth(exit_, mouth, 6.2, 3.9, fire=fx))
        if fx:
            put(cannonball(79.5, 88.5, 3.6))
            for (x0, y0, x1, y1) in ((82, 83, 83, 81), (78, 83, 78, 82)):
                for q in line(x0, y0, x1, y1):
                    cv.px[q] = 'W'
    # the head, the bandana's tails streaming out behind it
    if BANDANA:
        for t in bandana_tails(1.0 if shot else 0.0):
            put(t, dx=hx)
    l, r = H.ears()
    put(l, dx=hx)
    put(r, dx=hx)
    put(H.face_base(), dx=hx)
    put(H.features('shot' if shot else 'idle'), dx=hx, outline=False)
    if shot:
        # the manga "ting!": a sparkle off his grin
        put({(56, 36): 'W', (56, 37): 'W', (56, 38): 'Y', (56, 39): 'W', (56, 40): 'W', (54, 38): 'W',
             (55, 38): 'W', (57, 38): 'W', (58, 38): 'W'}, dx=hx, outline=False)
    put(H.hair(), dx=hx)
    put(H.flyaways(), dx=hx, outline=False)
    put(H.hat(htilt), dx=hx, outline='soft')
    # the sword arm (screen left): the elbow down and out, the forearm coming up to the fist at the
    # shoulder, the blade resting on the shoulder and rising behind it
    put(sleeve((31.5, 53), (28.5, 63), 4.6, 3.9))
    put(cuff((28.5, 64), 3.8, 1.5))
    put(limb([((29, 66), (34, 58), 2.8, 2.6)], '3', '2', '4', '5'))
    put(cutlass((31.5, 49.5), (9, 25), bow=2.4))
    put(amap(FIST_SWORD, 29, 50), outline=False)
    return cv


ANCHOR_SHIFT = 0
BANDANA = True
HEADSET = False     # tried: the cups hide behind his wide jaw, or read as shoulder pads lower down


# Palette tightening: colours that end up on fewer than ten pixels fold into their neighbours, so the
# sheet stays on a tight palette (38 colours): the 2px skin glint, the 6px of nostril / ear shadow
# (into the iris brown), the 6px of trouser / grip shadow.
MERGE = {'1': '2', '6': '9', '8': '7'}


def frame_px(frame, fx=True):
    return {(x + ANCHOR_SHIFT, y): MERGE.get(k, k) for (x, y), k in build(frame, fx).px.items()}


def frames():
    return image(frame_px(0)), image(frame_px(1))
