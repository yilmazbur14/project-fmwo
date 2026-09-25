"""Carter's third attack, the Messatsu: carter_messatsu_charge.png (4 frames) and
carter_messatsu_fire.png (3 frames), 96x96, facing RIGHT, soles on row 95, in the approved polish.

Drawn with the polish rig's own parts, imported read-only (art_source/carter_polish, README: stable
names): rig34's limbs, feet, trousers, caps and band tones, faces.head_part for the front head (every
three-quarter sheet carries the polished front head, as the shipped rush does), the approved chest
map, knot and tails, and aura.flames. New here: the pose, the gi opened toward the camera, the
cupped and pushing hands, and the choreography.

THE POSE (Gou Hadou). Wide front stance, both feet pointing the way he fires; torso wound back - the
chest turned to the camera, the rear shoulder dropped back; both palms cupped together at his RIGHT
hip, which on a figure facing right is the rear hip, screen left: the rear arm's elbow juts back,
the lead arm crosses his belly; head forward, eyes burning. The torso is the three-quarter one
because the approved front torso is 55px across the caps - too wide for the lead hand to reach the
rear hip.

THE MUZZLE CONTRACT. The palm-cup centre is ONE texel, MUZZLE, on all four charge frames and on fire
frames 1 (recoil) and 2 (bracing hold); only fire frame 0 (the 0.05 s thrust) has the palms
elsewhere. He charges the ball at his rear hip, drives both palms forward through it (frame 0), and
the beam's kick shoves him back until his pushing palms sit exactly where the ball was (frames 1-2):
the beam leaves the texel the ball grew on, and the flare that fans forward from it has his body
behind it, not under it. So the charge stands SHOVE texels forward of the hold, and the hold stands
on the house anchor (48, 95): the jump into the charge happens in the dark (warp -> charge), and the
fire hands back to Recover without one.

    python messatsu.py             # build both sheets + checks into the scratchpad
    python messatsu.py --ship      # ...and write Assets/Characters/Carter/carter_messatsu_*.png/.aseprite
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlib                                                      # noqa: E402
import lib                                                       # noqa: E402
from lib import Canvas, grow, erode, capsule, ellipse, amap, patch, shift, poly  # noqa: E402
from lib import DARKER, LIGHTER                                  # noqa: E402
import rig34 as RG                                               # noqa: E402
import faces as FC                                               # noqa: E402
import aura as AU                                                # noqa: E402
import chest as CH                                               # noqa: E402
import lower as LO                                               # noqa: E402

F = 96
SKIN = set('stuvwW')
GI = set('abcdef')


def _unit(dx, dy):
    L = math.hypot(dx, dy) or 1.0
    return dx / L, dy / L, L


# ------------------------------------------------------------------ the gi, opened to the camera

def gi(p):
    """rig34.jacket with its front window moved: the rush turns his chest toward the way he runs, so
    its window sits on the forward side; wound back, his chest faces the camera, so the window is
    centred (`open` = its centre across the torso, as a fraction of the chest radius toward screen
    right) and runs down to the belt, as on the approved front view. Returns (gi part, window mask)."""
    (cx, cy), (ux, uy), (nx, ny), L = RG.torso_frame(p)
    cr, pr = p['chest'][2], p['pelvis'][2]
    shell = grow(capsule((cx, cy), p['pelvis'][:2], cr, pr), 1)
    mid_f = p.get('open', 0.15)
    close = p.get('close', 0.80)
    top = p.get('win_top', 0.02)          # where the opening starts, as t down the torso (0 = chest)
    part, window = {}, set()
    for (x, y) in shell:
        t = ((x - cx) * ux + (y - cy) * uy) / L
        s = (x - cx) * nx + (y - cy) * ny
        r = cr + (pr - cr) * max(0.0, min(1.0, t))
        if t > RG.BELT_T + 0.04:
            continue
        mid = mid_f * r
        f = max(0.0, (t - top) / (close - top))
        half = p.get('win', 0.62) * r * (1.0 - 0.55 * f) if t < close else -1
        lo, hi = mid - half, mid + half
        if top < t and lo < s < hi:
            window.add((x, y))
            continue
        lvl = -s / (r + 1.0) * 0.65 - t * 0.35
        k = 'b' if lvl > 0.30 else ('c' if lvl > -0.12 else ('d' if lvl > -0.45 else 'e'))
        if top < t < close and (lo - 2.2 <= s <= lo or hi <= s <= hi + 2.2):
            k = 'b' if (s < mid) else 'c'          # the lapels: the left one rolls toward the light
        part[(x, y)] = k
    return part, window


def chest_in(cv, window, at):
    """The approved chest (chest.CHEST: pecs, sternum groove, the ab grid) laid into the gi's window,
    its sternum on `at` - his own chest, not a new one."""
    c = CH.chest()
    ox, oy = at[0] - 47.5, at[1] - 55.0
    for (x, y), k in c.items():
        q = (int(round(x + ox)), int(round(y + oy)))
        if q in window and k != 'k':
            cv.px[q] = k


BEAD = ["kkkkkk", "kGGHHk", "kGHHIk", "kHHIJk", "kHIJJk", "kkkkkk"]


def beads(p, window, n=7):
    """The juzu: seven beads in a U from collar to collar, lowest on the sternum (chest.bead_centres),
    fitted to this torso's window."""
    (cx, cy), _, (nx, ny), L = RG.torso_frame(p)
    xs = [q[0] for q in window]
    ys = [q[1] for q in window]
    mid = (min(xs) + max(xs)) / 2.0
    top = min(ys) - 1.0
    ax = (max(xs) - min(xs)) / 2.0 + 1.5
    parts = []
    cs = CH.bead_centres(n=n, ax=ax, ay=7.0, top=top)
    cs = [(x - 47.5 + mid, y) for (x, y) in cs]
    for i in sorted(range(len(cs)), key=lambda i: cs[i][1]):
        bx, by = cs[i]
        parts.append(amap(BEAD, int(round(bx - 2.5)), int(round(by - 2.5))))
    return parts


def hung_beads(p, n=7):
    """Bead centres in a U slung from his neck: the ends under either side of the chin, the lowest
    on the sternum, pulled toward the side he faces (the three-quarter chest)."""
    hdx, hdy = p['head']
    chin = 51 + hdy                       # the head map's last row, moved
    (cx, cy), _, (nx, ny), _ = RG.torso_frame(p)
    mid = cx + 0.35 * p['chest'][2]
    ax = 0.62 * p['chest'][2]
    top = chin - 1.0
    return [(x - 47.5 + mid, y) for (x, y) in CH.bead_centres(n=n, ax=ax, ay=6.5, top=top)]


# ------------------------------------------------------------------ belt, knot and tails

def belt(p, knot_at=0.35):
    """rig34's rope round the hips (near level however he leans), with the approved knot (lower.KNOT)
    and its tails on the front of the hips: `knot_at` is how far round toward screen right it sits,
    as a fraction of the belt's half-length."""
    cx, cy, cr = p['pelvis']
    ax, ay, _ = p['chest']
    a = math.degrees(math.atan2(cy - ay, cx - ax)) + 90.0
    a = (a + 180.0) % 360.0 - 180.0
    if a > 90.0:
        a -= 180.0
    elif a < -90.0:
        a += 180.0
    ang = math.radians(a * 0.42)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    cyl = cy - 3.0
    half = cr + 2.2
    rope = {}
    for y in range(int(cyl - 8), int(cyl + 8)):
        for x in range(int(cx - half - 3), int(cx + half + 4)):
            t = (x - cx) * ux + (y - cyl) * uy
            s = (x - cx) * nx + (y - cyl) * ny
            if abs(t) <= half and -1.5 <= s <= 1.5:
                row = int(round(s + 1.5))
                rope[(x, y)] = ('nnop', 'nopq', 'opqr', 'opqr')[min(3, row)][(x + y) % 4]
    kx = cx + ux * half * knot_at
    ky = cyl + uy * half * knot_at
    knot = shift(amap(LO.KNOT, 42, 66), int(round(kx - 47.5)), int(round(ky - 69.5)))
    tails = shift(amap(LO.TAILS, 42, 74), int(round(kx - 47.5)), int(round(ky - 69.5)))
    return rope, knot, tails


# ------------------------------------------------------------------ hands

# The cup: both hands round the ball at his rear hip, drawn as one piece, its gap centred on MUZZLE
# (the '@' - a transparent marker, never drawn). The lead hand (his left) comes in from the right
# across his belly, palm down, the back of it wrapped, its bare fingers curling down on the far side;
# the rear hand (his right) comes in from the left, palm up, its fingers curling up on the near
# side - so the ball sits in a cradle the camera can read. Wraps lit on top (the light is upper left).
CUP = [
    # col: 0-4 5-9 10-14 15       row
    "....k kkkkk k....",          # 0
    "..kkh gghhh ikk..",          # 1   lead hand over the ball: the wrapped back, lit on top
    ".kthh hhiii ijjk.",          # 2
    "kttkk kkkkk kkkk.",          # 3   where its wrap stops; the fingers curl down the far side
    "kuuk. ..... .....",          # 4
    "kuvk. ..... ..kk.",          # 5
    "kvvk. ..@.. .kttk",          # 6   the gap the ball sits in; rear fingertips curl up
    ".kk.. ..... .kuuk",          # 7
    "..... ..... .kuvk",          # 8
    "..kkk kkkkk kkkk.",          # 9   where the rear hand's wrap stops
    ".khgg hhhii ijjk.",          # 10  rear hand under the ball: palm up, its wrapped back lit
    "kihhh iiijj llmk.",          # 11
    ".kkkk kkkkk kkk..",          # 12
]
def marker(rows, ch='@'):
    """Where the marker sits in an ASCII map, as (column, row) from its top-left."""
    for r, row in enumerate(rows):
        row = row.replace(' ', '')
        if ch in row:
            return (row.index(ch), r)
    raise ValueError('no marker')


def place(rows, m, ch='@', fill=None):
    """An ASCII map placed so its marker lands on texel m. '.' is transparent; the marker is too,
    unless `fill` names the key it is drawn in."""
    mx, my = marker(rows, ch)
    part = {}
    for r, row in enumerate(rows):
        row = row.replace(' ', '')
        for c, k in enumerate(row):
            if k == ch and fill:
                k = fill
            if k in '.' + ch:
                continue
            part[(m[0] - mx + c, m[1] - my + r)] = k
    return part


def cup(m):
    """The cupped hands, placed so the marked gap centre lands on texel m."""
    return place(CUP, m)


# The push: both palms driven out toward the target, heels together, the lead hand's fingers spread
# up and the rear hand's down - the Hadou's open 'C' - with the wraps on the wrists behind them. The
# '@' is the palm-cup centre between the heels, where the beam leaves.
PUSH = [
    # col: 0-4 5-9 10
    "..... kkk..",         # 0
    "....k tttk.",         # 1   lead fingers, spread up and forward
    "...kt uuvk.",         # 2
    "kkkkt uvk..",         # 3
    "khhik uuk..",         # 4   lead wrist wrap, the heel of the palm
    "kijlk k@...",         # 5   the heels together: the palm-cup centre
    "khhik vuk..",         # 6   rear wrist wrap, the heel of the palm
    "kkkkt uvk..",         # 7
    "...kt uvvk.",         # 8
    "....k vvwk.",         # 9   rear fingers, spread down and forward
    "..... kkk..",         # 10
]


def push(m):
    """The heels press together, so the palm-cup centre itself is the crease between them (keyline)
    - left open it was a one-pixel hole between the palms."""
    return place(PUSH, m, fill='k')


# ------------------------------------------------------------------ the figure

def draw(p):
    cv = Canvas()
    # rear leg: shin and foot, a step darker
    hip, knee, ank, deg = p['rear']
    cv.stamp(RG.limb([(knee, ank, 4.2, 3.6)], bias=1))
    cv.stamp(RG.foot(ank, deg, ln=9.5, hi=4.0, bias=1))
    # the rear arm (his right): drawn behind the torso; its hand comes later, in front of the hip.
    # Folded (the charge), the forearm is its own keylined part over the upper arm, as the approved
    # crossed arms (cross.py) stamp their forearms: a fold reads by the line where it overlaps.
    sh, el, wr = p['far']
    if p.get('fold'):
        cv.stamp(RG.limb([(sh, el, 5.0, 4.4)], bias=1))
        cv.stamp(RG.limb([(el, wr, 4.1, 3.6)], bias=0))
    else:
        cv.stamp(RG.limb([(sh, el, 5.0, 4.4), (el, wr, 4.4, 3.8)], bias=1))
    # lead leg
    hip, knee, ank, deg = p['lead']
    cv.stamp(RG.limb([(knee, ank, 4.8, 4.2)]))
    cv.stamp(RG.foot(ank, deg))
    # torso skin, the approved chest in the gi's window, trousers, the gi, beads, belt
    cx, cy, cr = p['chest']
    px_, py_, pr = p['pelvis']
    cv.stamp(RG.limb([((cx, cy), (px_, py_), cr, pr)], tones='stuvw'))
    jk, window = gi(p)
    chest_in(cv, window, p.get('sternum', (cx + 1.0, cy + 1.0)))
    tr = RG.trousers(p)
    for k in ('rear', 'seat', 'lead'):
        cv.stamp(tr[k])
    cv.stamp(jk)
    if p.get('far_front'):
        # pushing, the rear arm reaches round in front of his belly: its forearm over the gi
        sh, el, wr = p['far']
        cv.stamp(RG.limb([(el, wr, 4.1, 3.6)], bias=1))
    if p.get('beads34'):
        # the juzu on the unwound torso: rig34's bead (the rush's), seven of them in a U from his
        # neck to his sternum, hung from under the chin so they show below the beard
        for bx, by in hung_beads(p):
            cv.stamp(amap(RG.BEAD, int(round(bx)) - 1, int(round(by)) - 1), outline=False)
    else:
        for b in beads(p, window):
            cv.stamp(b, outline=False)
    rope, knot, tails = belt(p, p.get('knot_at', 0.35))
    cv.stamp(rope)
    cv.stamp(knot, outline=False)
    cv.stamp(tails, outline=False)
    # the lead arm across him, its cap, the rear cap
    sh, el, wr = p['near']
    r0, r1, r2 = p.get('near_r', (5.4, 4.8, 4.2))
    if p.get('fold'):
        cv.stamp(RG.limb([(sh, el, r0, r1)]))
        cv.stamp(RG.limb([(el, wr, r1 - 0.3, r2)]))
    else:
        cv.stamp(RG.limb([(sh, el, r0, r1), (el, wr, r1, r2)]))
    q = dict(p)
    q['near'] = p['near'] + (p['near'][2],)
    q['far'] = p['far'] + (p['far'][2],)
    for c in RG.caps(q):
        cv.stamp(c)
    # the neck, then the hands (in front of his neck and chest), then the head over both
    hdx, hdy = p['head']
    eye, jaw = p['face']
    cv.stamp(FC.neck_part(hdx, hdy, rows=5), outline=False)
    if p.get('hands') == 'cup':
        cv.stamp(cup(p['muzzle']), outline=False)
    elif p.get('hands') == 'push':
        cv.stamp(push(p['palms']), outline=False)
    cv.stamp(FC.head_part(eye, jaw, hdx, hdy), outline=False)
    cv.stamp(FC.earring_part(hdx, hdy), outline=False)
    return cv


# ------------------------------------------------------------------ poses (pixels, facing right)

MUZZLE = (54, 64)
MX, MY = MUZZLE


def _sh(p, dx):
    """a pose moved dx texels along x (joints, head and muzzle)"""
    q = dict(p)
    for k in ('far', 'near'):
        q[k] = tuple((a + dx, b) for (a, b) in p[k])
    for k in ('lead', 'rear'):
        h, n, a, d = p[k]
        q[k] = ((h[0] + dx, h[1]), (n[0] + dx, n[1]), (a[0] + dx, a[1]), d)
    for k in ('chest', 'pelvis'):
        q[k] = (p[k][0] + dx, p[k][1], p[k][2])
    q['head'] = (p['head'][0] + dx, p['head'][1])
    return q


CHARGE = _sh(dict(
    head=(12, 5), face=(1, 0), muzzle=MUZZLE, hands='cup', fold=True, beads34=True,
    chest=(56.5, 62.5, 10.2), pelvis=(62.0, 76.0, 8.4), open=-0.05, win=0.50, close=0.45,
    win_top=-0.55, knot_at=0.85,
    far=((48.5, 57.5), (32.0, 62.0), (45.5, 69.0)),          # rear arm: the elbow driven back
    near=((65.0, 56.5), (67.0, 66.5), (60.0, 60.5)),         # lead arm tucked across his front
    near_r=(4.8, 4.3, 3.7),
    lead=((67.0, 77.0), (77.5, 82.5), (80.0, 91.0), 0.0),
    rear=((58.0, 78.0), (48.0, 85.0), (41.5, 91.0), 6.0),
    aura=dict(level=0.55, heat=0.45, seed=0),
), 1)

# fire 0, the thrust: unwound to face the target and lunging, both palms driven all the way out.
# The flare erupts on MUZZLE this frame and covers everything forward of it, so the thrust is a
# 0.05 s flash of arms driven into the eruption. Its palms are the one place the contract lets go.
THRUST = dict(
    head=(13, 2), face=(2, 2), palms=(84, 61), hands='push', beads34=True,
    chest=(58.0, 61.0, 10.2), pelvis=(52.0, 75.5, 8.3), open=0.62, win=0.46, close=0.60,
    knot_at=0.95,
    far=((54.0, 58.5), (65.0, 63.5), (78.0, 63.5)),
    near=((63.0, 56.0), (73.0, 57.0), (79.5, 59.0)), near_r=(4.6, 4.1, 3.6),
    lead=((57.0, 77.0), (68.0, 81.5), (71.0, 91.0), 0.0),
    rear=((48.0, 78.0), (36.0, 84.0), (24.0, 91.5), 8.0),
    stream=dict(level=1.0, seed=5, heat=0.9),
)

# fire 1, the recoil: kicked back until his palms are on MUZZLE, arms buckled, torso and head
# rocked back, the lead foot dragged.
RECOIL = dict(
    head=(-13, 3), face=(2, 2), palms=MUZZLE, hands='push', beads34=True, far_front=True,
    chest=(37.0, 61.5, 10.2), pelvis=(41.0, 76.0, 8.3), open=0.62, win=0.46, close=0.60,
    knot_at=0.95,
    far=((32.5, 57.0), (40.5, 66.5), (49.5, 65.5)),
    near=((41.0, 56.0), (42.5, 63.0), (49.5, 63.0)), near_r=(4.6, 4.1, 3.6),
    lead=((46.0, 77.5), (57.0, 81.5), (61.0, 91.0), 0.0),
    rear=((37.0, 78.5), (27.0, 84.5), (18.0, 91.5), 8.0),
    stream=dict(level=0.9, seed=6, heat=0.7),
)

# fire 2, the bracing hold: dropped into a deep stance and leaning into it, the rear leg locked
# straight, both arms driven into the eruption with the palms on MUZZLE; he holds this all string.
HOLD = dict(
    head=(-7, 8), face=(1, 1), palms=MUZZLE, hands='push', beads34=True, far_front=True,
    chest=(41.0, 64.0, 10.0), pelvis=(37.0, 78.0, 8.3), open=0.70, win=0.30, close=0.50,
    knot_at=0.95,
    far=((36.0, 59.5), (41.5, 67.5), (49.5, 65.5)),
    near=((44.0, 58.5), (44.5, 64.5), (49.5, 63.0)), near_r=(4.6, 4.1, 3.6),
    lead=((42.0, 79.0), (54.0, 83.0), (57.0, 91.0), 0.0),
    rear=((32.0, 80.0), (21.0, 86.0), (10.0, 91.5), 10.0),
    stream=dict(level=0.85, seed=7, heat=0.6),
)


# ------------------------------------------------------------------ the aura

def aura(cv, p):
    """The approved tongues (aura.IDLE blended toward aura.FLARE, as stand.aura does) moved with him:
    the head's five with the head, the shoulders' pair with his shoulders. Behind him, never black."""
    import stand as ST
    a = p['aura']
    specs, order = ST.blend(a['level'])
    specs = ST.jitter(specs, a['seed'])
    hdx, hdy = p['head']
    moved = []
    for i, (ctrl, w0, w1) in enumerate(specs[:7]):
        if i <= 4:
            dx, dy = hdx, hdy
        else:
            sh = p['far'][0] if i == 5 else p['near'][0]
            base = (24.0, 56.0) if i == 5 else (71.0, 56.0)
            dx, dy = sh[0] - base[0] + (-3 if i == 5 else 3), sh[1] - base[1]
        moved.append(([(x + dx, y + dy) for (x, y) in ctrl], w0, w1))
    order = [i for i in order if i < 7]
    body = grow(set(cv.px), 1)
    cv.stamp(AU.flames(moved, body, order, heat=a['heat']), outline=False, under=True)
    return cv


def embers(cv, pts):
    """aura.embers (a point with a fading tail under it), behind him."""
    cv.stamp(AU.embers(pts), outline=False, under=True)


def frame(p):
    cv = draw(p)
    import fx34 as FX
    if p.get('tails'):
        FX.tails(cv, p)
    if p.get('aura'):
        aura(cv, p)
    if p.get('stream'):
        s = p['stream']
        FX.dash(cv, p, s['level'], seed=s['seed'])
    if p.get('embers'):
        embers(cv, p['embers'])
    return cv


# ------------------------------------------------------------------ the sheets

# The charge loops at 0.12 s. His body and the cup never move - MUZZLE and the eyes are the same
# texels on every frame, as the ball and the eye glints are drawn on them - so the loop lives in the
# aura: the tongues lick (stand.jitter seeds), it swells and burns hotter to a peak on frame 2, where
# the slits go white-hot, and embers climb off him.
CHARGE_BEATS = [
    dict(seed=0, level=0.55, heat=0.45, eye=1, embers=[(40, 14, True), (80, 26, False)]),
    dict(seed=1, level=0.62, heat=0.52, eye=1, embers=[(41, 11, False), (79, 22, True)]),
    dict(seed=2, level=0.72, heat=0.66, eye=2, embers=[(39, 8, True), (81, 18, False), (30, 40, False)]),
    dict(seed=3, level=0.62, heat=0.52, eye=1, embers=[(42, 18, False), (80, 14, True)]),
]


def charge_pose(i):
    b = CHARGE_BEATS[i]
    p = dict(CHARGE)
    p['aura'] = dict(level=b['level'], heat=b['heat'], seed=b['seed'])
    p['face'] = (b['eye'], 0)
    p['embers'] = b['embers']
    return p


FIRE = [THRUST, RECOIL, HOLD]
FIRE_TAILS = [(178.0, 18.0), (168.0, 20.0), (174.0, 16.0)]


def fire_pose(i):
    return dict(FIRE[i])


SHEETS = {
    'carter_messatsu_charge': (charge_pose, 4),
    'carter_messatsu_fire': (fire_pose, 3),
}


def sheet(name):
    from PIL import Image
    fn, n = SHEETS[name]
    out = Image.new('RGBA', (F * n, F), (0, 0, 0, 0))
    for i in range(n):
        out.alpha_composite(frame(fn(i)).image(), (i * F, 0))
    return out


def preview(p, name):
    from PIL import Image
    cv = frame(p)
    im = cv.image()
    sil = Image.new('RGBA', im.size, (0, 0, 0, 0))
    for (x, y), k in cv.px.items():
        if k not in 'xXyYzZPQRSTU':
            sil.putpixel((x, y), (10, 10, 10, 255))
    bg = (150, 170, 120, 255)
    out = Image.new('RGBA', (96 * 3 * 2 + 30 + 96 * 6 + 10, 96 * 6 + 20), (30, 32, 40, 255))
    a = Image.new('RGBA', im.size, bg)
    a.alpha_composite(sil)
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im)
    out.paste(xlib.upscale(a, 3), (10, 10))
    out.paste(xlib.upscale(b, 3), (96 * 3 + 20, 10))
    out.paste(lib.grid_view(im, 6, 0, 0, 95, 95), (96 * 6 + 30, 10))
    out.save(os.path.join(xlib.SCRATCH, 'work', name))
    return im


FXDIR = os.path.join(xlib.CARTER, 'Messatsu')
FLARE_PIVOT = (6, 72)          # carter_messatsu_fx/beam.py: the flare texel that goes on his palms


def with_fx(im, kind, at, f=0):
    """EVALUATION ONLY - never shipped: the FX artist's ball (additive, centred) or flare (painted,
    pivot on the palms) composited over a frame on a bigger canvas, as the game layers them."""
    from PIL import Image, ImageChops
    pad = 70
    big = Image.new('RGBA', (F + 2 * pad, F + 2 * pad), (0, 0, 0, 0))
    big.alpha_composite(im, (pad, pad))
    if kind == 'ball':
        sh = Image.open(os.path.join(FXDIR, 'messatsu_ball.png')).convert('RGBA')
        fr = sh.crop((32 * f, 0, 32 * f + 32, 32))
        layer = Image.new('RGBA', big.size, (0, 0, 0, 0))
        layer.alpha_composite(fr, (pad + at[0] - 16, pad + at[1] - 16))
        base = Image.new('RGBA', big.size, (150, 170, 120, 255))
        base.alpha_composite(big)
        r, g, b, a = layer.split()
        rgb = Image.merge('RGB', (ImageChops.multiply(r, a), ImageChops.multiply(g, a), ImageChops.multiply(b, a)))
        out = ImageChops.add(base.convert('RGB'), rgb).convert('RGBA')
        return out
    sh = Image.open(os.path.join(FXDIR, 'messatsu_flare.png')).convert('RGBA')
    fr = sh.crop((64 * f, 0, 64 * f + 64, 144))
    base = Image.new('RGBA', big.size, (150, 170, 120, 255))
    base.alpha_composite(big)
    base.alpha_composite(fr, (pad + at[0] - FLARE_PIVOT[0], pad + at[1] - FLARE_PIVOT[1]))
    return base


def sequence(poses, name, s=3):
    from PIL import Image
    ims = [frame(p).image() for p in poses]
    fx = [with_fx(im, 'ball' if p.get('hands') == 'cup' else 'flare', MUZZLE) for im, p in zip(ims, poses)]
    w = F * s
    cw = F + 40
    out = Image.new('RGBA', (len(ims) * (cw * s + 10) + 10, w + 20 + (F + 50) * s), (30, 32, 40, 255))
    for i, (im, f) in enumerate(zip(ims, fx)):
        b = Image.new('RGBA', im.size, (150, 170, 120, 255))
        b.alpha_composite(im)
        out.paste(xlib.upscale(b, s), (10 + i * (cw * s + 10), 10))
        crop = f.crop((70, 70 - 30, 70 + cw, 70 + F + 20))
        out.paste(xlib.upscale(crop, s), (10 + i * (cw * s + 10), w + 20))
    out.save(os.path.join(xlib.SCRATCH, 'work', name))
    return ims


# ------------------------------------------------------------------ checks

AURA_KEYS = set('xXyYzZPQRSTU')
PAL_RGB = {v[:3] for v in lib.PAL.values()}


def lint(name, im):
    """96px frames, binary alpha, every colour in lib.PAL, soles on row 95 with both feet on it, the
    aura never black (it keeps its dark-violet edge)."""
    errs = []
    n = im.width // F
    if im.height != F or im.width % F:
        errs.append('%s: size %s is not a strip of 96x96 frames' % (name, im.size))
    st = lib.stats(im)
    if st['alphas'] not in ([0, 255], [255]):
        errs.append('%s: non-binary alpha %s' % (name, st['alphas']))
    stray = {c[:3] for c in lib.flat(im) if c[3] and c[:3] not in PAL_RGB}
    if stray:
        errs.append('%s: %d colours outside lib.PAL' % (name, len(stray)))
    fn, _ = SHEETS[name]
    for f in range(n):
        fr = im.crop((f * F, 0, f * F + F, F))
        rows = [y for y in range(F) for x in range(F) if fr.getpixel((x, y))[3]]
        if max(rows) != 95:
            errs.append('%s f%d: lowest opaque row %d, not 95' % (name, f, max(rows)))
        p = fn(f)
        for key in ('lead', 'rear'):
            ax = p[key][2][0]
            if not any(fr.getpixel((x, 95))[:3] == (0, 0, 0) and fr.getpixel((x, 95))[3]
                       for x in range(int(ax) - 8, int(ax) + 12) if 0 <= x < F):
                errs.append('%s f%d: no %s sole on row 95' % (name, f, key))
    return errs


def muzzle_check():
    """The palm-cup centre is MUZZLE on every charge frame (the cup's gap) and on fire frames 1-2 (the
    push's heels); fire frame 0 is exempt. For each frame: where the hand map's '@' landed, and how
    many of the map's pixels survive in the finished frame (all of them: nothing covers the hands)."""
    out = []
    for name, (fn, n) in SHEETS.items():
        for f in range(n):
            p = fn(f)
            if p.get('hands') == 'cup':
                at = p['muzzle']
                part = cup(at)
            else:
                at = p['palms']
                part = push(at)
            px = frame(p).px
            kept = sum(1 for q, k in part.items() if px.get(q) == k)
            out.append((name, f, p.get('hands'), tuple(at), tuple(at) == MUZZLE, kept, len(part)))
    return out


def texels():
    """The eyes (both slits) and the crown on the charge frames, measured off the pixels."""
    from PIL import Image
    res = []
    for f in range(4):
        p = charge_pose(f)
        cv = draw(p)              # no aura: the head alone decides the crown
        glow = [(x, y) for (x, y), k in cv.px.items() if k in 'MOV78' and 36 <= y <= 50]
        left = [q for q in glow if q[0] < 60.5]
        right = [q for q in glow if q[0] >= 60.5]

        def box(qs):
            xs = [q[0] for q in qs]
            ys = [q[1] for q in qs]
            return (min(xs), min(ys), max(xs), max(ys))
        head = {q for q, k in FC.head_part(*p['face'], *p['head']).items()}
        crown = min(y for (x, y) in head)
        crown_x = [x for (x, y) in head if y == crown]
        res.append(dict(left=box(left), right=box(right), crown_row=crown,
                        crown_x=(min(crown_x), max(crown_x))))
    return res


def numbers():
    from PIL import Image
    rush = Image.open(os.path.join(xlib.CARTER, 'carter_rush.png')).convert('RGBA')
    r = xlib.measure(rush)
    print('carter_rush.png (reference)        %s' % xlib.fmt(r))
    lo_b, hi_b = r['black'] * 0.9, r['black'] * 1.1
    lo_c, hi_c = r['colours'] * 0.9, r['colours'] * 1.1
    print('  +-10%%: black %.1f..%.1f%%, colours %.1f..%.1f' % (100 * lo_b, 100 * hi_b, lo_c, hi_c))
    ok = True
    for name in SHEETS:
        im = sheet(name)
        m = xlib.measure(im)
        inb = lo_b <= m['black'] <= hi_b and lo_c <= m['colours'] <= hi_c
        ok &= inb
        print('%-34s %s  %s' % (name + '.png', xlib.fmt(m), 'in band' if inb else 'OUT OF BAND'))
        n = im.width // F
        for f in range(n):
            print('   frame %d %s' % (f, xlib.fmt(xlib.measure(im.crop((f * F, 0, f * F + F, F))))))
    return ok


def main(ship=False):
    out = os.path.join(xlib.SCRATCH, 'messatsu')
    os.makedirs(out, exist_ok=True)
    errs = []
    sheets = {}
    for name in SHEETS:
        im = sheet(name)
        sheets[name] = im
        errs += lint(name, im)
        im.save(os.path.join(out, name + '.png'))
    for e in errs:
        print('LINT:', e)
    ok = numbers()
    print('muzzle (palm-cup centre) per frame:')
    for name, f, hands, m, same, kept, total in muzzle_check():
        exempt = name.endswith('fire') and f == 0
        tag = 'MUZZLE' if same else ('exempt (the thrust)' if exempt else 'MISMATCH')
        print('   %-24s f%d %-5s @ %s  %-20s hand pixels intact %d/%d' % (name, f, hands, m, tag, kept, total))
        if (not same and not exempt) or kept != total:
            errs.append('muzzle/hands %s f%d' % (name, f))
    for f, t in enumerate(texels()):
        print('   charge f%d eyes: left slit x%d..%d y%d..%d, right slit x%d..%d y%d..%d; crown row %d at x%d..%d' % (
            f, t['left'][0], t['left'][2], t['left'][1], t['left'][3], t['right'][0], t['right'][2],
            t['right'][1], t['right'][3], t['crown_row'], t['crown_x'][0], t['crown_x'][1]))
    if errs:
        print('%d problems - not shipping' % len(errs))
        return 1
    if ship:
        for name, im in sheets.items():
            for p in xlib.ship(im, xlib.CARTER, name):
                print('shipped', p)
    return 0


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
