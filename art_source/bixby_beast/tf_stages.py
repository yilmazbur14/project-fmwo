"""Creature stages for the transformation: the gulped normal Bixby, the growing crimson silhouettes built from
the beast rig, and the finished beast. Frame 320x256, Bixby's feet anchor (160, 251).

  normal Bixby (bixby.png, 64x64)  -> drawn at (128, 189), paws on the anchor
  beast (192x160)                  -> drawn at (64, 100 - lift), its own anchor (96,151) on the ground anchor
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pal import PALC, BLACK
from pngio import read_png
import anim_rig as AR
import beast_poses as BP
import small_art as SA
import tf_fx as TFX

TW, TH = 320, 256
AX, AY = 160, 251                      # ground anchor (Bixby's feet)
BIX = (128, 189)                       # bixby.png top-left so its paws sit on the anchor
BEAST = (64, 100)                      # beast frame top-left for lift 0
ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
SWALLOW = ASSETS + 'Liam/Entrance/bixby_swallow_keys.png'
HOVER_PNG = ASSETS + 'Bixby/bixby_beast.png'

# beast feature positions in beast-frame coords (measured on the approved hover frame)
EYES_MID = [(87, 43), (105, 43)]
EYES_L = [(37, 53), (50, 52)]
EYES_R = [(155, 53), (142, 52)]


def blank(w=TW, h=TH):
    lib.set_size(w, h)
    return Canvas(w, h)


def paste(dst, src, ox, oy):
    for y in range(src.h):
        for x in range(src.w):
            c = src.px[y][x]
            if c is not None:
                dst.put(ox + x, oy + y, c)


# ------------------------------------------------------------------ normal Bixby, as he is right after the gulp
def gulp_bixby():
    """bixby.png with the entrance's GULP edits (Liam's headband, gulped eyes, full belly, first lava glints).
    The '?' / '!' speech marks of the entrance frame are left out."""
    cv = SA.load(ASSETS + 'Bixby/bixby.png')
    w, h, g = read_png(SWALLOW)
    for y in range(64):
        for x in range(64):
            if y <= 16 and (x <= 6 or x >= 59):        # speech marks live here
                continue
            p = tuple(g[32 + y][256 + 4 + x])
            if p[3]:
                cv.px[y][x] = p
            elif cv.px[y][x] is not None and y <= 16 and 7 <= x <= 58:
                pass
    return cv


# eye stamps for the small sprite (bixby.png coords: middle eyes x24-28 / x34-38 rows 9-13)
EYE_SHRUNK = """
2kkk2
kWWWk
kW#Wk
kWWWk
2kkk2
"""
EYE_GLINT = """
2kkk2
kWWWk
kWFWk
kWWWk
2kkk2
"""
EYE_EMBER = """
2kkk2
kWkWk
kFoFk
kWkWk
2kkk2
"""
EYE_LIT = """
2kkk2
kkOkk
kOLOk
kkOkk
2kkk2
"""
EYE_BLAZE = """
kkkkk
kOLOk
kLWLk
kOLOk
kkkkk
"""
SIDE_SHRUNK = """
2k2
kWk
k#k
2k2
"""
SIDE_LIT = """
2k2
kOk
kLk
2k2
"""


def stamp(cv, grid, x, y):
    SA.stamp(cv, grid, x, y, SA.BPAL)


def bixby_eyes(cv, kind):
    g = dict(shrunk=EYE_SHRUNK, glint=EYE_GLINT, ember=EYE_EMBER, lit=EYE_LIT, blaze=EYE_BLAZE)[kind]
    stamp(cv, g, 24, 9)
    stamp(cv, g, 34, 9)
    s = SIDE_LIT if kind in ('lit', 'blaze', 'ember') else SIDE_SHRUNK
    stamp(cv, s, 10, 22)
    stamp(cv, s, 16, 22)
    stamp(cv, s, 45, 21)
    stamp(cv, s, 53, 21)


def row_squash(cv, drop, dup):
    """cheap squash/stretch: remove row `drop`, duplicate row `dup` (both in sprite coords, drop > dup)"""
    out = Canvas(cv.w, cv.h)
    rows = [cv.px[y][:] for y in range(cv.h)]
    rows.pop(drop)
    rows.insert(dup, rows[dup][:])
    for y in range(cv.h):
        out.px[y] = rows[y]
    return out


def bixby_stage(eyes='shrunk', cracks=0, singe=0, squash=0, glow=0):
    """the gulped dog at one point of the build-up. cracks/singe/glow are 0..3 levels."""
    cv = gulp_bixby()
    bixby_eyes(cv, eyes)
    m = cv.mask()
    if cracks:
        seeds = [(22, 46, 2.7), (40, 45, 0.5), (30, 52, 1.6), (12, 40, 2.2), (50, 40, 1.0)][:2 + cracks]
        TFX.crack_lines(cv, m, seeds, level=min(3, cracks), seed=17, length=6 + 4 * cracks)
    if singe:
        for (x0, x1) in ((18, 23), (40, 45)):
            for x in range(x0, x1):
                for k in range(singe + 1):
                    y = 34 - k
                    if (x, y) in m:
                        cv.put(x, y, PALC['e' if k < singe else 'o'])
    if glow:
        inner = erode(m, 1)
        for (x, y) in inner:
            c = cv.get(x, y)
            if c in (PALC['B'], PALC['D'], PALC['J'], PALC['Z'], PALC['G']):
                cv.put(x, y, PALC['S'] if glow < 2 else PALC['R'])
    if squash:
        cv = row_squash(cv, 58, 44)
    return cv


# ------------------------------------------------------------------ beast stages (rig-built silhouettes)
def wing_grow(P, g):
    """scale the wing geometry toward its root (g = 0 folded away, 1 full span)"""
    Q = dict(P)
    root = P['w_root']
    for k in ('w_elbow', 'w_wrist', 'w_thumb', 'w_attach'):
        x, y = P[k]
        Q[k] = (root[0] + (x - root[0]) * g, root[1] + (y - root[1]) * g)
    Q['w_tips'] = [(root[0] + (x - root[0]) * g, root[1] + (y - root[1]) * g) for x, y in P['w_tips']]
    return Q


def beast_pose(horns=(False, False, False), wings=0.0, jaw=0):
    P = AR.pose(BP.HOVER)
    P.update({k: v for k, v in BP.FLAP[0].items() if k != 'dy'})
    P['horns_mid'], P['horns_L'], P['horns_R'] = horns
    P['glasses_show'] = False
    P['mh_jaw'], P['sh_jaw'] = jaw, jaw
    if wings <= 0.01:
        P['wing_L'] = P['wing_R'] = False
    else:
        P = wing_grow(P, wings)
    return P


def beast_canvas(P):
    wings, body = AR.render(P, dy=BP.DY + 1)   # hover frame 0 body offset
    return AR.compose(wings, body)


def scale_mask(mask, f, ax, ay):
    """scale a mask about (ax, ay); forward mapping so no holes appear"""
    if abs(f - 1.0) < 1e-6:
        return set(mask)
    out = set()
    for (x, y) in mask:
        x0, x1 = (x - ax) * f + ax, (x + 1 - ax) * f + ax
        y0, y1 = (y - ay) * f + ay, (y + 1 - ay) * f + ay
        for ty in range(int(math.floor(y0)), max(int(math.floor(y0)) + 1, int(math.ceil(y1)))):
            for tx in range(int(math.floor(x0)), max(int(math.floor(x0)) + 1, int(math.ceil(x1)))):
                out.add((tx, ty))
    return out


def scale_pt(p, f, ax, ay):
    return (ax + (p[0] - ax) * f, ay + (p[1] - ay) * f)


CRIMSON_BANDS = [(200, 'P'), (150, 'Q'), (105, 'R'), (62, 'S'), (0, 'T')]
DARK_BANDS = [(150, 'S'), (80, 'T'), (0, 'Z')]


def tint(cv, dark=False):
    """recolour a rendered beast into transformation crimson (or near-black), keeping its internal structure"""
    out = Canvas(cv.w, cv.h)
    bands = DARK_BANDS if dark else CRIMSON_BANDS
    for y in range(cv.h):
        for x in range(cv.w):
            c = cv.px[y][x]
            if c is None:
                continue
            if c == BLACK:
                out.px[y][x] = PALC['Z'] if dark else PALC['T']
                continue
            lum = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            for th, ch in bands:
                if lum >= th:
                    out.px[y][x] = PALC[ch]
                    break
    return out


def beast_silhouette(scale, lift, horns=(False, False, False), wings=0.0, cracks=3, eyes='lit', jaw=0, seed=21,
                     dark=False):
    """the beast part-way through the change: rendered by the rig, recoloured to crimson and rescaled about his
    feet. Returns (canvas 320x256, mask, eye positions)."""
    import rotsprite as RS
    P = beast_pose(horns, wings, jaw)
    bc = tint(beast_canvas(P), dark=dark)
    if abs(scale - 1.0) > 1e-6:
        bc = RS.resample(bc, scale, (96, 151))
    cv = blank()
    ox, oy = AX - 96, AY - 151 - lift
    paste(cv, bc, ox, oy)
    mask = cv.mask()
    # bright rim so the silhouette keeps a readable edge against the arena
    for (x, y) in edge(mask):
        cv.put(x, y, PALC['S' if dark else 'Q'])
    for (x, y) in {q for q in edge(mask) if (q[0], q[1] - 1) not in mask or (q[0] - 1, q[1]) not in mask}:
        cv.put(x, y, PALC['T' if dark else 'P'])
    if cracks:
        cy = AY - lift - 60 * scale
        seeds = [(AX - 18 * scale, cy + 26 * scale, 2.6), (AX + 16 * scale, cy + 24 * scale, 0.6),
                 (AX, cy + 34 * scale, 1.57), (AX - 30 * scale, cy + 8 * scale, 2.9), (AX + 30 * scale, cy + 10 * scale, 0.2)]
        TFX.crack_lines(cv, mask, seeds[:2 + cracks], level=min(3, cracks), seed=seed, length=8 + 6 * scale * cracks)
    eye_pts = []
    for g in (EYES_MID, EYES_L, EYES_R):
        for p in g:
            q = scale_pt(p, scale, 96, 151)
            eye_pts.append((q[0] + ox, q[1] + oy))
    if eyes:
        for (ex, ey) in eye_pts:
            put_eye(cv, ex, ey, eyes, scale)
    return cv, mask, eye_pts


def put_eye(cv, ex, ey, kind, scale=1.0):
    x, y = int(round(ex)), int(round(ey))
    big = scale > 0.7
    if kind == 'lit':
        cv.put(x, y, PALC['L'])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.put(x + dx, y + dy, PALC['O'])
        if big:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                cv.put(x + dx, y + dy, PALC['o'])
    elif kind == 'ember':
        cv.put(x, y, PALC['o'])
        if big:
            cv.put(x + 1, y, PALC['F'])
    elif kind == 'blaze':
        cv.put(x, y, PALC['W'])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.put(x + dx, y + dy, PALC['L'])
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            cv.put(x + dx, y + dy, PALC['O'])


# ------------------------------------------------------------------ the finished beast
_hover = {}


def beast_frame0():
    """the approved hover frame 0 (192x160) as a canvas"""
    if 'f0' not in _hover:
        w, h, px = read_png(HOVER_PNG)
        cv = Canvas(192, 160)
        for y in range(160):
            for x in range(192):
                p = tuple(px[y][x])
                cv.px[y][x] = p if p[3] else None
        _hover['f0'] = cv
    return _hover['f0']


def unlit_eyes(cv, lift, heads=('M', 'L', 'R')):
    """stamp dark sockets over the approved beast's eyes (used while his eyes have not ignited yet)"""
    import faces2 as F2
    from faces import mid_tx, side_tx, put_grid
    ox, oy = BEAST[0], BEAST[1] - lift
    if 'M' in heads:
        L = mid_tx(96 + ox, 23 + oy)
        R = mid_tx(96 + ox, 23 + oy, mirror=True)
        put_grid(cv, F2.MID_EYE['unlit'], 16, 17, L)
        put_grid(cv, F2.MID_EYE['unlit'], 16, 17, R)
    for which, sx, side in (('L', 21, 1), ('R', 129, -1)):
        if which in heads:
            T = side_tx(sx + ox, 43 + oy, side)
            put_grid(cv, F2.SIDE_EYE_FAR['unlit'], 13, 9, T)
            put_grid(cv, F2.SIDE_EYE_NEAR['unlit'], 25, 7, T)


def beast_final(lift=40, eyes='on'):
    """the finished beast.
    'cold' = the rig-rendered new body before anything ignites (dark eyes, clenched jaws, dead tail flame)
    'mid'  = the approved art with only the side heads' eyes still dark
    'on'   = exactly bixby_beast.png frame 0"""
    cv = blank()
    if eyes == 'cold':
        P = AR.pose(BP.HOVER)
        P.update({k: v for k, v in BP.FLAP[0].items() if k != 'dy'})
        P['eyes_mid'] = P['eyes_side'] = 'unlit'
        P['mouth_mid'] = P['mouth_side'] = 'unlit'
        P['glow'] = 0
        paste(cv, beast_canvas(P), BEAST[0], BEAST[1] - lift)
        return cv
    paste(cv, beast_frame0(), BEAST[0], BEAST[1] - lift)
    if eyes == 'mid':
        unlit_eyes(cv, lift, heads=('L', 'R'))
    return cv
