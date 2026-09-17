"""The 360 spin for beast Bixby's pound + spin attack.

Rather than rotating a three-headed dragon per angle, the spinning mass is treated as a surface of
revolution about the sprite's vertical axis (x = 96):

  * spin_core()  renders the beast with the heads removed and everything tucked in;
  * revolve()    reads each row of that render, maps every pixel to an azimuth on the cylinder of that
                 row's radius, rotates it by the frame's spin angle and paints it back with a motion
                 smear proportional to the pixel's screen speed (r*sin(phi)). Each source pixel is
                 entered twice, at +phi and -phi, so the far side of the cylinder is covered as the
                 near side rotates away. Pixels nearest the viewer are painted last, so they win.
  * the three heads are drawn separately as comets orbiting an ellipse 120 degrees apart, the far
    half behind the body and the near half in front, with the same speed-based smear.

Frames: 0-1 lead-in (wings tuck, heads rise, glow builds), 2-5 the spin loop (30 degrees of a
120-degree period, so the 3 heads make it seamless), 6-7 wobble to a stop.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, RAMPC, BLACK, DARKER, LIGHTER
import anim_rig as AR
import beast_poses as BP
import body as BD
import limbs as LM
import collars as CL
import fx2 as FX
import heads as HD
import faces2 as F2
import quake_poses as QP
from body import line_px

FW, FH = 192, 160
AXIS = 96.0
DY = QP.DY
GY = 151                   # ground line, frame space

# heads orbit this ellipse (frame space)
HEAD_CX, HEAD_CY = 96.0, 68.0
HEAD_RX, HEAD_RY = 52.0, 14.0
TAIL_RX, TAIL_RY, TAIL_CY = 52.0, 10.0, 128.0

STEP = 30.0                # degrees between spin loop frames (4 frames = 120 = one head period)


# ==================================================================== tucked pose + core
TUCK = dict(
    # wings clamped over the flanks: half-folded so the crimson still reads in the blur
    w_root=(84, 92), w_elbow=(70, 74), w_wrist=(67, 104), w_thumb=(72, 96),
    w_tips=[(46, 86), (43, 114), (54, 134), (74, 142)], w_attach=(80, 124), w_scallop=0.26,
    # forelegs folded under the chest
    f_sh=(62, 101), f_el=(54, 116), f_wr=(60, 128), f_paw=(63, 134), claw_scale=0.75,
    # hind legs braced narrow
    h_hip=(82, 127), h_knee=(81, 136), h_ankle=(80, 143), h_paw=(79, 146),
    # tail wrapped tight round the hips (kept inside r = 40 so it smears into a ring, not a disc)
    tail_path=[(86, 128), (74, 137), (62, 142), (56, 137), (58, 129), (64, 125)],
    tail_r=[5.8, 5.2, 4.5, 3.8, 3.1, 2.5], tail_tip=(64, 124), tail_curve_c=(78, 132), tail_glow=0,
    mh=(96, 26), mc_top=78,
)
LOOSE = dict(
    w_root=(84, 90), w_elbow=(58, 60), w_wrist=(34, 22), w_thumb=(39, 12),
    w_tips=[(14, 34), (14, 66), (24, 98), (50, 114)], w_attach=(80, 114), w_scallop=0.38,
    f_sh=(62, 101), f_el=(50, 118), f_wr=(46, 130), f_paw=(45, 137), claw_scale=0.75,
    h_hip=(82, 127), h_knee=(80, 136), h_ankle=(79, 143), h_paw=(78, 146),
    tail_path=[(86, 128), (70, 138), (54, 145), (40, 143), (32, 135), (30, 126)],
    tail_r=[5.8, 5.2, 4.5, 3.8, 3.1, 2.5], tail_tip=(30, 125), tail_curve_c=(56, 130), tail_glow=1,
    mh=(96, 26), mc_top=78,
)


def tuck_pose(t=1.0, crouch=0):
    """t = 0 loose stance, t = 1 fully tucked for the spin"""
    kw = {}
    for k, v in TUCK.items():
        a = LOOSE[k]
        if isinstance(v, tuple):
            kw[k] = (a[0] + (v[0] - a[0]) * t, a[1] + (v[1] - a[1]) * t)
        elif isinstance(v, list) and v and isinstance(v[0], tuple):
            kw[k] = [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(a, v)]
        elif isinstance(v, list):
            kw[k] = list(v)
        elif isinstance(v, (int, float)):
            kw[k] = a + (v - a) * t
        else:
            kw[k] = v
    kw['tail_glow'] = 0 if t > 0.5 else 1
    kw['claw_scale'] = 0.75
    P = AR.pose(body_dy=crouch, **kw)
    P.update(BP.side_group((21 + 19 * t, 40 + 12 * t), (66, 97)))
    return P


def spin_core(t=1.0, crouch=0):
    """the tucked beast with no heads: the mass that smears into the spinning column"""
    P = tuck_pose(t, crouch)
    H = 160
    lib.set_size(FW, H)
    AR.STATE['crack'] = 2
    AR.STATE['claw'] = P.get('claw_scale', 1.0)
    PR = AR.right_params(P)
    cv = Canvas(FW, H)
    LM.wing(cv, P, +1)
    LM.wing(cv, PR, -1)
    AR.tail2(cv, P)
    LM.hind_leg(cv, P, +1)
    LM.hind_leg(cv, PR, -1)
    BD.torso(cv, P)
    LM.front_leg(cv, P, +1)
    LM.front_leg(cv, PR, -1)
    BD.shoulder(cv, P, +1)
    BD.shoulder(cv, PR, -1)
    BD.side_neck(cv, P, +1)
    BD.side_neck(cv, PR, -1)
    for side in (1, -1):
        a, b = P['sc_a'], P['sc_b']
        if side < 0:
            a, b = (192 - b[0], b[1]), (192 - a[0], a[1])
        AR.collar2(cv, a, b, P['sc_thick'], P['sc_sag'], n_spikes=3, spike_len=5.5, spike_w=2.3, studs=2)
    ox, oy = P['mh']
    neck = ell(ox, oy + 51, 20, 13)
    cv.part(neck, 'fur', ('sphere', ox - 6, oy + 50, 23, 13, 0.1), TH_B)
    CL.collar(cv, (77, P['mc_top']), (115, P['mc_top']), P['mc_h'], P['mc_sag'], n_spikes=4, spike_len=7.0,
              spike_w=2.8, studs=3, light_c=(88, P['mc_top'] - 2))
    out = Canvas(FW, H)
    out.blit(cv, 0, DY)
    return out


# ==================================================================== surface-of-revolution smear
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def revolve(cv, deg, axis=AXIS):
    """Turn cv by deg as a stack of cylinders. Inverse mapping: every output pixel asks its row where
    that surface point was before the turn, so nothing tears and nothing is left hollow. The source row
    is treated as symmetric about the axis (cos(-a) == cos(a)), which is true of this front-facing rig."""
    out = Canvas(cv.w, cv.h)
    ph = math.radians(deg)
    for y in range(cv.h):
        row = cv.px[y]
        xs = [x for x in range(cv.w) if row[x] is not None and row[x] != BLACK]
        if len(xs) < 2:
            continue
        r = max(axis - min(xs), max(xs) + 1 - axis)
        if r < 1.5:
            continue
        lo, hi = int(math.ceil(axis - r)), int(math.floor(axis + r - 0.001))
        for x in range(max(0, lo), min(cv.w, hi + 1)):
            u = max(-1.0, min(1.0, (x + 0.5 - axis) / r))
            sx = int(round(axis + r * math.cos(math.acos(u) - ph) - 0.5))
            c = row[sx] if 0 <= sx < cv.w else None
            if c is None or c == BLACK:
                c = row[min(xs, key=lambda q: abs(q - sx))]
            out.put(x, y, c)
    return out


def motion_blur(cv, k=0.55, step=STEP, axis=AXIS):
    """Smear each row by the screen speed of that point on the cylinder (r*sin(a)): a mode filter over
    the window the surface swept since the last frame. The silhouette edges barely move, so they stay
    crisp; the middle of the barrel, which is doing all the travelling, goes to long soft runs."""
    span = math.radians(step) * k
    out = cv.copy()
    for y in range(cv.h):
        row = cv.px[y]
        xs = [x for x in range(cv.w) if row[x] is not None]
        if len(xs) < 4:
            continue
        x0, x1 = min(xs), max(xs)
        r = max(axis - x0, x1 + 1 - axis)
        for x in range(x0, x1 + 1):
            c0 = row[x]
            if c0 is None or c0 == BLACK:
                continue
            u = max(-1.0, min(1.0, (x + 0.5 - axis) / r))
            n = int(round(r * math.sqrt(max(0.0, 1 - u * u)) * span))
            if n < 1:
                continue
            cnt = {}
            for q in range(max(x0, x - n), x + 1):
                c = row[q]
                if c is None or c == BLACK:
                    continue
                cnt[c] = cnt.get(c, 0) + 1
            if cnt:
                out.px[y][x] = max(cnt.items(), key=lambda kv: (kv[1], kv[0] == c0))[0]
    close_outline(out)
    lone_black_cleanup(out)
    return out


def streak_rows(cv, deg, n=8, seed=3, axis=AXIS):
    """bright speed lines racing across the spinning column"""
    R = FX.rng(seed)
    rows = [y for y in range(cv.h) if any(p is not None for p in cv.px[y])]
    if not rows:
        return
    ph = math.radians(deg)
    for i in range(n):
        y = rows[int(R() * len(rows)) % len(rows)]
        xs = [x for x in range(cv.w) if cv.px[y][x] is not None]
        r = max(axis - min(xs), max(xs) - axis)
        a = ph * 2.0 + R() * 2 * math.pi
        if math.sin(a) < 0.45:
            continue
        x0 = axis + r * math.cos(a)
        run = int(r * math.sin(a) * 0.5)
        for k in range(abs(run)):
            x = int(x0 + (k if run > 0 else -k))
            c = cv.get(x, y)
            if c is not None and c != BLACK:
                cv.put(x, y, LIGHTER.get(c, c) if k < abs(run) * 0.45 else c)


# ==================================================================== orbiting heads
_MINI = {}
MINI_BOX = (76, 84)
MINI_C = (34, 44)            # head centre inside the mini canvas


def mini_head(style='spikes', side=1, jaw=5, band=False):
    """one of Bixby's real side heads on its own canvas, jaws open and blazing, ready to be shrunk
    and flown round the orbit. side +1 faces LEFT, side -1 faces RIGHT."""
    key = (style, side, jaw, band)
    if key in _MINI:
        return _MINI[key]
    W, H = MINI_BOX
    lib.set_size(W, H)
    cv = Canvas(W, H)
    ox, oy = 15, 26
    P = dict(eyes_side='roar', mouth_side='roar')
    HD.side_head_base(cv, ox, oy, side, jaw)
    F2.side_face(cv, ox, oy, side, jaw, P, 'L')
    HD.side_horns(cv, ox, oy, side, style)
    if band:
        # Liam's headband plate, so the middle head still reads as itself in the blur
        T = (lambda lx, ly: (ox + lx, oy + ly)) if side > 0 else (lambda lx, ly: (ox + 41 - lx, oy + ly))
        for lx in range(14, 32):
            for k, ch in enumerate('hij'):
                c, r = T(lx, 4 + k)
                if cv.get(c, r) is not None:
                    cv.put(c, r, PALC[ch])
    _MINI[key] = cv
    return cv


def scaled_head(style, side, f, dark=0):
    key = ('s', style, side, round(f, 3), dark)
    if key in _MINI:
        return _MINI[key]
    import rotsprite as RS
    src = mini_head(style, side, band=(style == 'band'))
    cv = RS.resample(src, f, MINI_C)
    if dark:
        cv.darken(cv.mask(), dark)
        close_outline(cv)
    _MINI[key] = cv
    return cv


def smear_h(cv, n):
    """horizontal motion smear of a small canvas: repeat each pixel n px against its travel"""
    if not n:
        return cv
    d = 1 if n > 0 else -1
    out = cv.copy()
    for y in range(cv.h):
        for x in (range(cv.w - 1, -1, -1) if d > 0 else range(cv.w)):
            c = cv.px[y][x]
            if c is None or c == BLACK:
                continue
            for k in range(1, abs(n) + 1):
                q = x + d * k
                if 0 <= q < cv.w and (cv.px[y][q] is None or cv.px[y][q] == BLACK):
                    out.px[y][q] = c
    close_outline(out)
    return out


HEAD_STYLES = ['band', 'spikes', 'bull']


def head_comet(cv, deg, sc, near, trail=52.0, rx=None, ry=None):
    """the tapering blur trail behind a head, following the orbit ellipse"""
    n = 9
    RX = HEAD_RX if rx is None else rx
    RY = HEAD_RY if ry is None else ry
    pts = []
    for k in range(n):
        a = math.radians(deg - trail * (k + 1) / n)
        if (math.sin(a) >= 0) != near:
            break
        pts.append((HEAD_CX + RX * math.cos(a), HEAD_CY + RY * math.sin(a), 1 - (k + 1) / n))
    if len(pts) < 2:
        return
    ramp = RAMPC['tan']
    for k in range(len(pts) - 1):
        (x0, y0, t0), (x1, y1, t1) = pts[k], pts[k + 1]
        m = capsule((x0, y0), (x1, y1), max(0.8, 6.0 * sc * t0), max(0.7, 6.0 * sc * t1))
        idx = 1 if t0 > 0.74 else (2 if t0 > 0.45 else 3)
        if not near:
            idx = min(4, idx + 1)
        for q in m:
            cv.put(q[0], q[1], ramp[idx])


def neck_streak(cv, hx, hy, sc, near):
    """blurred neck tying a head back to the spinning column"""
    a = (96.0, 86.0)
    b = (hx + (96.0 - hx) * 0.18, hy + (86.0 - hy) * 0.18)
    m = capsule(a, b, 6.0, 4.0 * sc)
    cv.part(m, 'fur', ('cyl', (a[0] - 2, a[1] - 2), (b[0] - 2, b[1] - 2), 7, 0.1), TH_B,
            bias=2 if near else 3)


def heads_frame(back, front, deg, blur=1.0, scale=0.60, rx=None, ry=None):
    """all three heads at 120-degree spacing; returns [(deg, mouth_x, mouth_y, near)]"""
    out = []
    RX = HEAD_RX if rx is None else rx
    RY = HEAD_RY if ry is None else ry
    order = sorted(range(3), key=lambda k: math.sin(math.radians(deg + 120.0 * k)))
    for k in order:
        a = deg + 120.0 * k
        ar = math.radians(a)
        s, c = math.sin(ar), math.cos(ar)
        near = s >= 0
        cv = front if near else back
        sc = scale * (1.0 + 0.20 * s)
        x = HEAD_CX + HEAD_RX * c
        y = HEAD_CY + HEAD_RY * s
        neck_streak(cv, x, y, sc / scale, near)
        head_comet(cv, a, sc / scale * 1.0, near)
        side = 1 if c < 0 else -1                       # snout points radially outward
        h = scaled_head(HEAD_STYLES[k], side, sc, dark=0 if near else 1)
        n = int(round(-RX * s * math.radians(STEP) * 0.22 * blur))
        h = smear_h(h, n)
        cv.blit(h, int(round(x - MINI_C[0])), int(round(y - MINI_C[1])))
        mx = x + (-1 if side > 0 else 1) * 17.0 * sc
        out.append((a, mx, y + 7.0 * sc, near))
    return out


def tail_flame(back, front, deg):
    """the tail's flame tip drawing a ring of fire around him"""
    a = math.radians(deg + 200.0)
    s, c = math.sin(a), math.cos(a)
    cv = front if s >= 0 else back
    x, y = 96 + TAIL_RX * c, TAIL_CY + TAIL_RY * s
    n = 10
    for k in range(n):
        aa = math.radians(deg + 200.0 - 130.0 * k / n)
        if (math.sin(aa) >= 0) != (s >= 0):
            break
        t = 1 - k / n
        xx, yy = 96 + TAIL_RX * math.cos(aa), TAIL_CY + TAIL_RY * math.sin(aa)
        r = max(0.8, 4.2 * t)
        col = 'L' if t > 0.8 else ('O' if t > 0.55 else ('o' if t > 0.3 else 'F'))
        for q in ell(xx, yy, r, r * 0.85):
            cv.put(q[0], q[1], PALC[col])
    for q in ell(x, y, 4.4, 3.8):
        d = math.hypot((q[0] + 0.5 - x) / 4.4, (q[1] + 0.5 - y) / 3.8)
        cv.put(q[0], q[1], PALC['W' if d < 0.35 else ('L' if d < 0.7 else 'O')])


def speed_ring(cv_back, cv_front, cy, rx, ry, deg, color='x', span=150.0, dashes=3):
    """thin dashed ellipse arcs whipping around him"""
    for d in range(dashes):
        a0 = deg + 360.0 * d / dashes
        n = 16
        pts_f, pts_b = [], []
        for k in range(n + 1):
            a = math.radians(a0 + span * k / n)
            p = (96 + rx * math.cos(a), cy + ry * math.sin(a))
            (pts_f if math.sin(a) >= 0 else pts_b).append(p)
        for pts, cv in ((pts_f, cv_front), (pts_b, cv_back)):
            if len(pts) < 2:
                continue
            for q in line_px(pts):
                cv.put(q[0], q[1], PALC[color])


# ==================================================================== frames
LEAD_MS = [90, 80]
LOOP_MS = [50, 50, 50, 50]
END_MS = [90, 130]


def base_dust(back, front, deg, hard=1.0, seed=5):
    """floor dust skirt dragged round by the spin"""
    n = 12
    for i in range(n):
        a = math.radians(deg * 1.6 + 360.0 * i / n)
        s = math.sin(a)
        cv = front if s >= 0 else back
        x = 96 + (52 + 10 * hard) * math.cos(a)
        y = GY - 3 + 5 * s
        r = (2.6 + 2.4 * hard) * (0.7 + 0.4 * (s + 1) / 2)
        FX.puff(cv, x, y, r, seed=seed * 17 + i, kind='dust', holes=0.15)
    FX.embers(front, (30, GY - 42, 162, GY - 2), int(8 * hard) + 4, seed=seed * 3 + 1,
              hot_ratio=0.5, sizes=(1, 1, 2))


def spin_frame(i):
    """returns dict(fx_back=, body=, fx_front=) for frame i of bixby_spin.png"""
    back, front = Canvas(FW, FH), Canvas(FW, FH)
    if i == 0:
        # lead-in 1: crouch, wings clamping in, heads lifting, eyes and maws flaring
        P = QP.pound_pose(4)
        P = AR.pose(P, **{k: v for k, v in tuck_pose(0.45, crouch=4).items()
                          if k.startswith(('w_', 'f_', 'h_', 'tail'))})
        P.update(mh=(96, 26), mc_top=78, mh_jaw=3, sh_jaw=2, eyes_mid='roar', eyes_side='roar',
                 mouth_mid='roar', mouth_side='roar', tails=BP.TAILS_FLICK, side_rot=(10, -10))
        P.update(BP.side_group((22, 48), (66, 100)))
        wings, b = AR.render(P, dy=DY)
        body = Canvas(FW, FH)
        body.blit(wings, 0, 0)
        body.blit(b, 0, 0)
        FX.embers(front, (26, 40, 166, 140), 16, seed=71, hot_ratio=0.7, sizes=(1, 2, 2))
        base_dust(back, front, 0, hard=0.35, seed=9)
        return dict(fx_back=back, body=body, fx_front=front)
    if i == 1:
        # lead-in 2: fully tucked, heads thrown out sideways, the turn just starting to smear
        core = spin_core(0.85, crouch=2)
        body = motion_blur(revolve(core, -18), k=0.35)
        heads_frame(back, front, -20, blur=0.45, scale=0.64, rx=40, ry=12)
        speed_ring(back, front, 84, 56, 12, -30, 'x', span=100, dashes=2)
        base_dust(back, front, -20, hard=0.6, seed=13)
        FX.embers(front, (22, 34, 170, 144), 20, seed=17, hot_ratio=0.7, sizes=(1, 2, 3))
        return dict(fx_back=back, body=body, fx_front=front)
    if i in (2, 3, 4, 5):
        deg = (i - 2) * STEP
        core = spin_core(1.0, crouch=1)
        # the heads repeat every 120 degrees, the barrel (mirror-symmetric) every 180: turning the
        # barrel 1.5x as fast makes BOTH land back where they started after the 4 loop frames
        body = motion_blur(revolve(core, deg * 1.5))
        streak_rows(body, deg, n=9, seed=3 + i)
        heads_frame(back, front, deg)
        tail_flame(back, front, deg)
        speed_ring(back, front, 84, 58, 13, deg * 2.4, 'x', span=115, dashes=2)
        speed_ring(back, front, 124, 48, 11, deg * 2.4 + 70, 'x', span=100, dashes=2)
        base_dust(back, front, deg, hard=1.0, seed=5 + i)
        return dict(fx_back=back, body=body, fx_front=front)
    if i == 6:
        # wobble 1: still turning but slow enough that two heads separate out of the blur
        core = spin_core(0.9, crouch=3)
        body = motion_blur(revolve(core, 132), k=0.35)
        heads_frame(back, front, 132, blur=0.45, scale=0.64, rx=44, ry=13)
        speed_ring(back, front, 84, 54, 12, 150, 'x', span=85, dashes=2)
        base_dust(back, front, 132, hard=0.55, seed=23)
        return dict(fx_back=back, body=body, fx_front=front)
    # wobble 2: almost stopped, listing to one side, heads flopping outward
    core = spin_core(0.6, crouch=6)
    body = motion_blur(revolve(core, 168), k=0.15)
    import rotsprite as RS
    body = RS.rotate(body, -5, (96, GY))
    heads_frame(back, front, 172, blur=0.2, scale=0.68, rx=40, ry=12)
    base_dust(back, front, 168, hard=0.35, seed=29)
    return dict(fx_back=back, body=body, fx_front=front)


LAYERS = ['fx_back', 'body', 'fx_front']
N_FRAMES = 8
MS = LEAD_MS + LOOP_MS + END_MS


def flatten(fr):
    out = Canvas(FW, FH)
    for L in LAYERS:
        if fr.get(L) is not None:
            out.blit(fr[L], 0, 0)
    return out


def mouth_anchors(i):
    """(angle_deg, x, y, near) of each head's mouth for frame i -- where a sonic beam starts"""
    if i in (2, 3, 4, 5):
        deg = (i - 2) * STEP
    elif i == 1:
        deg = -20
    elif i == 6:
        deg = 132
    elif i == 7:
        deg = 172
    else:
        return []
    out = []
    for k in range(3):
        a = deg + 120.0 * k
        ar = math.radians(a)
        s, c = math.sin(ar), math.cos(ar)
        sc = 1.0 + 0.20 * s
        out.append((a, HEAD_CX + HEAD_RX * c - 12.0 * sc, HEAD_CY + HEAD_RY * s + 3.4 * sc, s >= 0))
    return out


if __name__ == '__main__':
    import anim_common as AC
    frs = [flatten(spin_frame(i)) for i in range(N_FRAMES)]
    AC.preview(AC.strip_of(frs), 'spin_draft.png', 3, guides=True)
    print('ok')
