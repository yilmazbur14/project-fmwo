"""Extended pose rig for the beast Bixby combat animations (fly / land / recover / hit / takeoff / roar / defeat).

Reuses the approved part functions from limbs.py / body.py / heads.py / collars.py unchanged and adds:
  * per-side limb, neck, collar, head and wing parameters (key + '_R', given in real sprite coords),
  * group offsets (torso_dx, mc_dx) so asymmetric / leaning poses are possible,
  * glow levels for the lava cracks, eyes, mouths and tail flame (2 = approved look, 1 = dimmed, 0 = dead),
  * face variants (eyes / mouths / lolling tongues) authored as ASCII stamps in faces2.py,
  * a claw-length scale for planted paws.
With default parameters build_body2(HOVER) is pixel-identical to beast.build_body(HOVER) (see rig_regress.py)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, RAMPC, BLACK
import beast as BS
import body as BD
import limbs as LM
import heads as HD
import faces as FC
import collars as CL
from body import line_px
import faces2 as F2

FW = 192
STATE = {'crack': 2, 'claw': 1.0}

# ------------------------------------------------------------------ patched helpers (approved look at defaults)
_ORIG_CRACK = BD.crack
_ORIG_PAW = LM.paw


def groove(c):
    """dark groove colour for a crack that no longer glows, chosen from the ramp under it"""
    if c in RAMPC['tan'] or c in RAMPC['ear']:
        return PALC['5']
    if c in RAMPC['fur']:
        return PALC['u']
    return PALC['Z']


def crack_lv(cv, path, clip, glow=True):
    lv = STATE['crack']
    if lv >= 2:
        return _ORIG_CRACK(cv, path, clip, glow)
    pts = line_px(path)
    L = len(pts)
    for i, q in enumerate(pts):
        if q not in clip:
            continue
        c = cv.get(*q)
        if c is None or c == BLACK:
            continue
        t = i / max(1, L - 1)
        if lv == 1:
            if 0.3 < t < 0.7 and glow:
                col = PALC['F'] if i % 3 == 0 else PALC['r']
            elif 0.12 < t < 0.88:
                col = PALC['r']
            else:
                col = groove(c)
        else:
            col = groove(c)
        cv.put(q[0], q[1], col)
    return pts


def paw_lv(cv, c, n_toes, spread, toe_r, pad_rx, pad_ry, claw_len, claw_w, side=1):
    return _ORIG_PAW(cv, c, n_toes, spread, toe_r, pad_rx, pad_ry, claw_len * STATE['claw'], claw_w, side)


BD.crack = crack_lv
LM.crack = crack_lv
LM.paw = paw_lv

HOVER = BS.HOVER
Y0 = BS.Y0

SIDE_KEYS = ('h_hip', 'h_knee', 'h_ankle', 'h_paw', 'f_sh', 'f_el', 'f_wr', 'f_paw', 'sn_base', 'sn_top', 'sh_c')
WING_KEYS = ('w_root', 'w_elbow', 'w_wrist', 'w_thumb', 'w_attach')


def pose(base=None, **kw):
    P = dict(base if base is not None else HOVER)
    P.update(kw)
    return P


def right_params(P):
    """parameter dict for the side = -1 call: '_R' overrides (real coords) are mirrored into the left-side frame"""
    Q = dict(P)
    for k in SIDE_KEYS + WING_KEYS:
        if k + '_R' in P:
            x, y = P[k + '_R']
            Q[k] = (192 - x, y)
    if 'w_tips_R' in P:
        Q['w_tips'] = [(192 - x, y) for x, y in P['w_tips_R']]
    if 'w_scallop_R' in P:
        Q['w_scallop'] = P['w_scallop_R']
    return Q


def shifted2(P, dx, dy):
    Q = dict(P)
    for k in WING_KEYS:
        for kk in (k, k + '_R'):
            if kk in P:
                Q[kk] = (P[kk][0] + dx, P[kk][1] + dy)
    for kk in ('w_tips', 'w_tips_R'):
        if kk in P:
            Q[kk] = [(x + dx, y + dy) for x, y in P[kk]]
    return Q

# ------------------------------------------------------------------ wings


def build_wings2(P, dx=0, dy=0):
    H = P.get('H', 160)
    lib.set_size(FW, H)
    cv = Canvas(FW, H)
    Q = shifted2(P, dx, dy)
    if P.get('wing_L', True):
        LM.wing(cv, Q, +1)
    if P.get('wing_R', True):
        LM.wing(cv, right_params(Q), -1)
    return cv

# ------------------------------------------------------------------ tail (limbs.tail with glow levels + curve centre)


TAIL_TIP_DIM = """
...................
...................
...................
...................
........kFk........
........kok........
.......kFoFk.......
.......kFoFk.......
......kFoOoFk......
.....kFFoOoFFk.....
....krFooOooFrk....
...krFFooOooFFrk...
..krrFFoooooFFrrk..
..krrFFFoooFFFrrk..
...krrFFFoFFFrrk...
....krrrFFFrrrk....
.....kkrrrkrrkk....
......kkkQkkk......
.........Q.........
........kQk........
"""

TAIL_TIP_DEAD = """
...................
...................
...................
...................
...................
...................
...................
...................
...................
........kk.........
.......kJJk........
......kDJJJk.......
.....kDJZJJJk......
.....kJJZZJJk......
......kJZZJk.......
.......kJJk........
........kk.........
.........k.........
.........Q.........
........kQk........
"""


def tail2(cv, P):
    lv = P.get('tail_glow', P.get('glow', 2))
    path = P['tail_path']
    radii = P['tail_r']
    m = tube(path, radii)
    sp = catmull(path, 8)
    L = len(sp)
    spikes = set()
    cxm, cym = P.get('tail_curve_c', (40, 128))
    for i in range(6, L - 10, 7):
        (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n
        if (sp[i][0] + nx - cxm) ** 2 + (sp[i][1] + ny - cym) ** 2 < (sp[i][0] - nx - cxm) ** 2 + (sp[i][1] - ny - cym) ** 2:
            nx, ny = -nx, -ny
        r = radii[0] + (radii[-1] - radii[0]) * i / L
        base = (sp[i][0] + nx * (r - 1.0), sp[i][1] + ny * (r - 1.0))
        tip = (base[0] + nx * 4.2 - dx / n * 2.0, base[1] + ny * 4.2 - dy / n * 2.0)
        spikes |= poly([(base[0] - dx / n * 2.2, base[1] - dy / n * 2.2), tip, (base[0] + dx / n * 2.2, base[1] + dy / n * 2.2)])
    cv.part(spikes, 'dark', ('dist', 1.5), TH_GLOSS)
    cv.part(m, 'dark', ('dist', 3.6, 0.05), TH_B)
    inner = erode(m, 1)
    for i in range(10, L - 4, 9):
        (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        nx, ny = dy / n, -dx / n
        r = radii[0] + (radii[-1] - radii[0]) * i / L + 1
        a = (sp[i][0] - nx * r - dx / n * 0.8, sp[i][1] - ny * r - dy / n * 0.8)
        b = (sp[i][0] + nx * r + dx / n * 0.8, sp[i][1] + ny * r + dy / n * 0.8)
        pts = line_px([a, sp[i], b])
        odd = (i // 9) % 2
        for k, q in enumerate(pts):
            if q in inner:
                if lv >= 2:
                    col = PALC['Z'] if odd else PALC['r']
                elif lv == 1:
                    col = PALC['Z'] if odd else PALC['S']
                else:
                    col = PALC['Z']
                cv.put(q[0], q[1], col)
        if not odd and lv >= 1:
            for q in pts[len(pts) // 3: 2 * len(pts) // 3]:
                if q in inner:
                    cv.put(q[0], q[1], PALC['F'] if lv >= 2 else PALC['r'])
    tx, ty = P['tail_tip']
    grid = {2: LM.TAIL_TIP, 1: TAIL_TIP_DIM, 0: TAIL_TIP_DEAD}[lv]
    rows = grid.strip('\n').split('\n')
    w = len(rows[0])
    for dy_, row in enumerate(rows):
        for dx_, ch in enumerate(row):
            if ch == '.':
                continue
            cv.put(int(tx - w // 2 + dx_), int(ty - len(rows) + 1 + dy_), PALC[ch])
    return m

# ------------------------------------------------------------------ heads


def middle_head2(cv, ox, oy, P):
    jd = P.get('mh_jaw', 0)
    base = HD.middle_head_base(cv, ox, oy, jd)
    F2.middle_face(cv, ox, oy, jd, P)
    HD.scorch(cv, base['earL'], oy + 47, seed=3)
    HD.scorch(cv, base['earR'], oy + 47, seed=5)
    if P.get('headband', True):
        HD.middle_headband(cv, ox, oy, base['head'])
    return base


def side_head2(cv, ox, oy, side, style, jaw_drop, P, which):
    base = HD.side_head_base(cv, ox, oy, side, jaw_drop)
    F2.side_face(cv, ox, oy, side, jaw_drop, P, which)
    HD.scorch(cv, base["ear"], oy + 38, seed=7 if side > 0 else 11)
    base['horns'] = HD.side_horns(cv, ox, oy, side, style)
    return base


def side_heads(cv, P):
    """both side heads (+ Liam's glasses on the left horn). P['side_rot'] = (deg_L, deg_R) tilts each head
    RotSprite-style about its neck joint (head box origin + (25, 40)); + = clockwise (left head snout up)."""
    sx, sy = P['sh']
    rx, ry = P.get('sh_R', (150 - sx, sy))
    jl = P.get('sh_jaw', 0)
    jr = P.get('sh_jaw_R', jl)
    fl = P.get('face_L', P.get('side_facing', 'out'))
    fr = P.get('face_R', P.get('side_facing', 'out'))
    rot = P.get('side_rot')
    layers = {}
    for which in P.get('side_order', ('L', 'R')):
        tgt = cv
        if rot:
            tgt = Canvas(cv.w, cv.h)
            layers[which] = tgt
        if which == 'L':
            side_head2(tgt, sx, sy, +1 if fl == 'out' else -1, 'spikes', jl, P, 'L')
        else:
            side_head2(tgt, rx, ry, -1 if fr == 'out' else +1, 'bull', jr, P, 'R')
    gtgt = layers.get('L', cv) if rot else cv
    if P.get('glasses_show', True):
        g = P.get('glasses_pos')
        if g is None:
            if fl == 'out':
                HD.glasses_on_horn(gtgt, sx + 35, sy - 20)
            else:
                HD.glasses_on_horn(gtgt, sx + 7 - 18, sy - 20, flip=True)
        else:
            HD.glasses_on_horn(gtgt, g[0], g[1], flip=g[2] if len(g) > 2 else False)
    if rot:
        import rotsprite as RS
        for which in P.get('side_order', ('L', 'R')):
            if which == 'L':
                piv = (sx + 25, sy + 40)
                cv.blit(RS.rotate(layers['L'], rot[0], piv), 0, 0)
            else:
                piv = (rx + 17, ry + 40)
                cv.blit(RS.rotate(layers['R'], rot[1], piv), 0, 0)


# ------------------------------------------------------------------ collar with optional flipped normal


def collar2(cv, a, b, thick, sag, n_spikes=3, spike_len=5.5, spike_w=2.4, studs=2, light_c=None, flip=False):
    """collars.collar, but flip=True makes the band thickness and spikes go toward -y (neck hanging downward)"""
    if not flip:
        return CL.collar(cv, a, b, thick, sag, n_spikes, spike_len, spike_w, studs, light_c)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    down = (-math.sin(ang), math.cos(ang))
    if down[1] > 0:
        down = (-down[0], -down[1])
    upper = CL.band_pts(a, b, sag, down)
    lower = [(x + down[0] * thick, y + down[1] * thick) for x, y in upper]
    band = poly(upper + list(reversed(lower)))
    for k in range(n_spikes):
        t = (k + 0.5) / n_spikes
        i = int(round(t * 16))
        bx, by = lower[i]
        bx -= down[0] * 1.2
        by -= down[1] * 1.2
        tang = (math.cos(ang), math.sin(ang))
        fan = (t - 0.5) * 1.1
        d = (down[0] + tang[0] * fan, down[1] + tang[1] * fan)
        CL.spike(cv, (bx, by), d, spike_len, spike_w)
    rp = RAMPC['collar']
    for (x, y) in band:
        best = min(upper, key=lambda p: (p[0] - x - 0.5) ** 2 + (p[1] - y - 0.5) ** 2)
        u = ((x + 0.5 - best[0]) * down[0] + (y + 0.5 - best[1]) * down[1]) / thick
        # light still comes from above: the edge nearest -y is the lit one
        idx = 3 if u < 0.22 else (2 if u < 0.40 else (1 if u < 0.78 else 0))
        cv.put(x, y, rp[idx])
    cv.outline(band)
    inner = erode(band, 1)
    for k in range(studs):
        t = (k + 1) / (studs + 1)
        i = int(round(t * 16))
        x = int(upper[i][0] + down[0] * thick * 0.5)
        y = int(upper[i][1] + down[1] * thick * 0.5)
        for (dx, dy, ch) in ((0, 0, 'x'), (1, 0, 'X'), (0, 1, 'X'), (1, 1, 'y')):
            if (x + dx, y + dy) in inner:
                cv.put(x + dx, y + dy, PALC[ch])
    return band


# ------------------------------------------------------------------ body


def build_body2(P):
    H = P.get('H', 160)
    lib.set_size(FW, H)
    cv = Canvas(FW, H)
    STATE['crack'] = P.get('crack_glow', P.get('glow', 2))
    STATE['claw'] = P.get('claw_scale', 1.0)
    PR = right_params(P)
    if P.get('show_tail', True):
        tail2(cv, P)
    LM.hind_leg(cv, P, +1)
    LM.hind_leg(cv, PR, -1)
    tdx = P.get('torso_dx', 0)
    if tdx:
        tmp = Canvas(FW, H)
        BD.torso(tmp, P)
        cv.blit(tmp, tdx, 0)
    else:
        BD.torso(cv, P)
    order = P.get('front_order', 'legs_first')
    if order == 'legs_first':
        LM.front_leg(cv, P, +1)
        LM.front_leg(cv, PR, -1)
        BD.shoulder(cv, P, +1)
        BD.shoulder(cv, PR, -1)
    else:
        BD.shoulder(cv, P, +1)
        BD.shoulder(cv, PR, -1)
        LM.front_leg(cv, P, +1)
        LM.front_leg(cv, PR, -1)
    BD.side_neck(cv, P, +1)
    BD.side_neck(cv, PR, -1)
    for side in (1, -1):
        a, b = P['sc_a'], P['sc_b']
        if side < 0:
            a, b = (192 - b[0], b[1]), (192 - a[0], a[1])
            if 'sc_a_R' in P:
                a, b = P['sc_a_R'], P['sc_b_R']
        flip = P.get('sc_flip_R' if side < 0 else 'sc_flip', False)
        collar2(cv, a, b, P['sc_thick'], P['sc_sag'], n_spikes=3, spike_len=5.5, spike_w=2.3, studs=2, flip=flip)
    ox, oy = P['mh']
    nc = P.get('neck_c', (ox, oy + 51))
    if P.get('neck_show', True):
        neck = ell(nc[0], nc[1], 21, 15)
        cv.part(neck, 'fur', ('sphere', nc[0] - 6, nc[1] - 1, 24, 14, 0.1), TH_B)
    if P.get('headband', True) and P.get('tails_show', True):
        HD.headband_tails(cv, ox, oy, P)
    if P.get('mid_first', False):
        mid_block(cv, P)
        side_heads(cv, P)
    else:
        side_heads(cv, P)
        mid_block(cv, P)
    return cv


def mid_block(cv, P):
    ox, oy = P['mh']
    mdx = P.get('mc_dx', 0)
    if P.get('mc_show', True):
        CL.collar(cv, (77 + mdx, P['mc_top']), (115 + mdx, P['mc_top']), P['mc_h'], P['mc_sag'], n_spikes=4, spike_len=7.0,
                  spike_w=2.8, studs=3, light_c=(88 + mdx, P['mc_top'] - 2))
    HD.middle_horns(cv, ox, oy, P)
    middle_head2(cv, ox, oy, P)

# ------------------------------------------------------------------ frame assembly


def render(P, dy=Y0, dx=0, wing_dy=None):
    """returns (wings, body) canvases (192 x H) already offset into frame space.
    P['rot'] = (degrees, pivot) rotates both layers RotSprite-style about pivot (frame coords, + = clockwise)."""
    H = P.get('H', 160)
    wd = dy if wing_dy is None else wing_dy
    wings = build_wings2(P, dx, wd)
    b = build_body2(P)
    body = Canvas(FW, H)
    body.blit(b, dx, dy)
    if P.get('rot'):
        import rotsprite as RS
        ang, pivot = P['rot']
        wings = RS.rotate(wings, ang, pivot)
        body = RS.rotate(body, ang, pivot)
    return wings, body


def compose(*layers, w=FW, h=160):
    out = Canvas(w, h)
    for L in layers:
        if L is not None:
            out.blit(L, 0, 0)
    return out
