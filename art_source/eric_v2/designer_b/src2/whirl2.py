"""Part B v2 whirlwind 13-20 (256x192): Eric pivots through a full turn with the greatsword swung out at his side
at belt height (both hands on the grip at the belly, guard 12 px out, tip reaching 127.5 px from his axis).
The swing plane rises behind him so the blade clears his head in the back frames. White trailing arcs follow
the tip path (designer A's whirl smear style). Ends front-facing = the approved whirl-wide blockout."""
import math
from base2 import *
import views2
from sword2 import Sword2

AX, HANDS_Y = 128.0, 160.0
HANDS_R = 13.0
K = 26.0 / 121.0            # ground-plane compression (blockout smear ellipse)
GUARD_OUT = 12.0
REACH = GUARD_OUT + 115.5
RISE = 19.0                 # max upward tilt of the swing when the blade points away
SH_R, SH_Y, SH_K = 17.6, 155.0, 0.12
UPPER, FORE = 13.0, 12.5
ARC_R, ARC_SPAN = 121.0, 115.0

# frame -> (yaw, side, facing angle phi); sword angle theta = phi - 90 + LEAD (his left side, blade leading)
LEAD = 22.5
TABLE = {
    13: (45, -1, 135.0), 14: (90, -1, 180.0), 15: (135, -1, 225.0), 16: (180, 1, 270.0),
    17: (135, 1, 315.0), 18: (90, 1, 0.0), 19: (45, 1, 45.0), 20: (0, 1, 90.0),
}
SWORD_BEHIND = {13: False, 14: False, 15: True, 16: True, 17: True, 18: True, 19: False, 20: False}


def tilt(a_deg):
    s = math.sin(math.radians(a_deg))
    return math.radians(RISE) * (max(0.0, -s) ** 1.2)


def gp(r, a_deg, h=HANDS_Y):
    """point at radius r, ground angle a on the (rising) swing surface"""
    ar = math.radians(a_deg)
    b = tilt(a_deg)
    return (AX + r * math.cos(ar) * math.cos(b), h + K * r * math.sin(ar) * math.cos(b) - r * math.sin(b))


def proj_ground(gx, gz, h=HANDS_Y):
    """ground-plane offset (gx right, gz toward camera) from the axis -> screen, on the rising swing surface"""
    r = math.hypot(gx, gz)
    a = math.degrees(math.atan2(gz, gx))
    b = tilt(a) * min(1.0, r / 40.0)
    return (AX + gx * math.cos(b), h + K * gz * math.cos(b) - r * math.sin(b))


def arc_band(theta, part):
    """pixels (x, y) -> colour for the trailing arc behind blade angle theta. part 'back' / 'front'."""
    out = {}
    steps = int(ARC_SPAN / 0.35)
    for i in range(steps + 1):
        t = i / steps                                   # 0 at the blade .. 1 at the tail
        a = theta - ARC_SPAN * t
        front = math.sin(math.radians(a)) >= 0
        if (part == 'front') != front:
            continue
        thick = 0.34 * (1 - t) + 0.05
        s = 1.0
        while s >= 1.0 - thick:
            x, y = gp(ARC_R * s, a)
            q = (s - (1.0 - thick)) / thick
            if q > 0.6:
                col = 'W'
            elif q > 0.25:
                col = 'A' if t < 0.8 else None
            else:
                col = 'B' if t < 0.45 else None
            px, py = int(math.floor(x)), int(math.floor(y))
            if col and 0 <= px < FW and 0 <= py < FH:
                rank = {'W': 3, 'A': 2, 'B': 1}[col]
                cur = out.get((px, py))
                if cur is None or rank > cur[0]:
                    out[(px, py)] = (rank, col)
            s -= 0.004
    return {k: v[1] for k, v in out.items()}


def paint(fr, band, keep=None):
    for (x, y), ch in band.items():
        if keep and (x, y) in keep:
            continue
        fr.px[y][x] = PALC[ch]


def sword_mask(S):
    m = set()
    m |= S._mask(lambda a, b: abs(b) <= S.blade_hw(a, 1 if b >= 0 else -1), 4.5, 115.5, 14)
    m |= S._mask(lambda a, b: abs(a * S.sa) <= max(4.5 * S.sa, 2.5) and abs(b) <= 16.5, -6 / S.sa, 6 / S.sa, 17)
    return m


def whirl_frame(i):
    yaw, side, phi = TABLE[i]
    theta = phi - 90.0 + LEAD
    fr = R.Frame()
    wf()
    ph, th_ = math.radians(phi), math.radians(theta)
    hx, hz = HANDS_R * math.cos(ph), HANDS_R * math.sin(ph)
    hands = proj_ground(hx, hz)
    g = proj_ground(hx + GUARD_OUT * math.cos(th_), hz + GUARD_OUT * math.sin(th_))
    # blade direction on screen (rising surface): from guard toward the tip
    tip = proj_ground(hx + REACH * math.cos(th_), hz + REACH * math.sin(th_))
    ang = math.degrees(math.atan2(tip[1] - g[1], tip[0] - g[0]))
    length = math.hypot(tip[0] - g[0], tip[1] - g[1])
    S = Sword2(g, ang, sa=length / 115.5)
    grip_pts = [S.P(-9.0, 0), S.P(-18.0, 0)]
    horizontal = abs(math.cos(math.radians(ang))) > 0.7

    def sh(a):
        ar = math.radians(a)
        return (AX + SH_R * math.cos(ar), SH_Y + SH_K * SH_R * math.sin(ar))
    shoulders = [sh(phi + 90), sh(phi - 90)]
    near_idx = 0 if math.sin(math.radians(phi + 90)) >= math.sin(math.radians(phi - 90)) else 1

    import arms as BA

    def elbow(s_, h_):
        e1 = BA.solve_elbow(s_, h_, UPPER, FORE, 1)
        e2 = BA.solve_elbow(s_, h_, UPPER, FORE, -1)
        return max((e1, e2), key=lambda e: e[1] + 0.35 * abs(e[0] - AX))

    arms = []
    for k, s_ in enumerate(shoulders):
        h_ = grip_pts[0] if k == near_idx else grip_pts[1]
        arms.append((s_, elbow(s_, h_), h_, k == near_idx))

    def draw_arm(a, upper=True, fore=True):
        s_, e_, h_, near = a
        if upper:
            R.limb(fr, s_, e_, 9, ramp='chain')
        if fore:
            R.limb(fr, e_, h_, 9)
            R.cop(fr, e_, 4.6, 4.4)
        wf()

    back_mode = yaw >= 135
    behind = SWORD_BEHIND[i]
    paint(fr, arc_band(theta, 'back'))
    if behind:
        S.draw(fr.canvas())
        wf()
    if back_mode:
        for a in arms:
            draw_arm(a)
        for p in grip_pts:
            R.fist(fr, p[0], p[1], horizontal=horizontal)

    if yaw == 0:
        near_key = 'paulL'

        def hook_paul(fr_):
            for a in arms:
                draw_arm(a, fore=False)
        R.compose(fr, skip=('armR_front',), hooks={'paulL': hook_paul})
    else:
        V, L = views2.build(yaw, side)
        order = views2.order(yaw, side)
        near_key = 'paul_r'
        for name in order:
            if not back_mode and name == near_key:
                for a in arms:
                    if a[3]:
                        draw_arm(a, fore=False)
            fr.put96(layer_rgba(L[name]))
            if not back_mode and name == 'torso':
                for a in arms:
                    if not a[3]:
                        draw_arm(a)
    wf()
    paint(fr, arc_band(theta, 'front'), keep=sword_mask(S) if behind else None)
    if not behind:
        S.draw(fr.canvas())
        wf()
    if not back_mode:
        for a in arms:
            if a[3] or yaw == 0:
                draw_arm(a, upper=False)
        for p in grip_pts:
            R.fist(fr, p[0], p[1], horizontal=horizontal)
    return fr


if __name__ == '__main__':
    import sys
    idx = [int(a) for a in sys.argv[1].split(',')] if len(sys.argv) > 1 else list(range(13, 21))
    imgs = [whirl_frame(i).rgba() for i in idx]
    strip(imgs, 2, '../v2_whirl_2x.png')
