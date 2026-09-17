"""Part B whirlwind 13-20: Eric pivots through a full turn, greatsword swung out horizontally (hammer-throw grip,
both hands on the grip in front of his belly), blade leading his facing by LEAD degrees, white trailing arcs.

Ground-plane angles (screen, y down): 0 = right, 90 = toward camera, 180 = left, 270 = away.
A point at radius r, angle a, height h projects to (64 + r cos a, h + K r sin a)."""
import math
from base import *
import views
from sword import AffineSword

K = 0.36           # ground-plane compression for the swing
LEAD = 22.5
AX, HANDS_Y, SH_Y = 64.0, 91.0, 82.0
HANDS_R, SH_R = 27.0, 22.0
SH_K = 0.12       # shoulders sit on the pauldrons, which use the body tilt
TIP_R_EXTRA = 101.0      # grip point to tip
# trailing arcs: (span deg, radius, thickness at tail, thickness at blade)
ARCS = [(115, 104, 1.0, 15), (90, 74, 0.8, 9), (60, 48, 0.5, 4)]

# frame -> (yaw, side, facing angle)
TABLE = {
    13: (45, -1, 135.0), 14: (90, -1, 180.0), 15: (135, -1, 225.0), 16: (180, 1, 270.0),
    17: (135, 1, 315.0), 18: (90, 1, 0.0), 19: (45, 1, 45.0), 20: (0, 1, 90.0),
}


def gp(r, a, h):
    ar = math.radians(a)
    return (AX + r * math.cos(ar), h + K * r * math.sin(ar))


def layer_rgba(px96):
    return [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in px96]


def smear(fr, theta, span, r, th0, th1, part, clip_front=None):
    """trailing crescent on the swing ellipse of radius r behind the blade angle theta.
    part: 'back' (away half), 'front' (camera half) or 'all'."""
    w128()
    a1 = theta
    a0 = theta - span
    c = cv(fr)
    band = bfx_band(c, r, K * r, a0, a1, th0, th1)
    for (x, y), col in band.items():
        ang = math.degrees(math.atan2((y + 0.5 - HANDS_Y) / K, x + 0.5 - AX))
        front = math.sin(math.radians(ang)) >= 0
        if part == 'all' or (part == 'front') == front:
            fr.px[y][x] = col


def bfx_band(c, rx, ry, a0, a1, th0, th1, cy=None):
    """ellipse band around (AX, HANDS_Y); angles a0->a1 (deg, increasing); thickness th0 (tail) -> th1 (head)
    measured inward. 3-tone banding like designer A's smear_arc (white rim, pale middle, soft inner)."""
    cy = HANDS_Y if cy is None else cy
    out = {}
    span = a1 - a0
    for y in range(128):
        for x in range(128):
            dx, dy = x + 0.5 - AX, y + 0.5 - cy
            rho = math.hypot(dx / rx, dy / ry)
            if rho > 1.0 or rho < 0.3:
                continue
            ang = math.degrees(math.atan2(dy / ry, dx / rx))
            t = None
            for kk in (-720, -360, 0, 360, 720):
                tt = (ang + kk - a0) / span
                if 0 <= tt <= 1:
                    t = tt
                    break
            if t is None:
                continue
            th = th0 + (th1 - th0) * t
            rloc = math.hypot(math.cos(math.radians(ang)) * rx, math.sin(math.radians(ang)) * ry)
            depth = (1 - rho) * rloc
            if depth > th:
                continue
            q = depth / max(th, 1e-6)
            if th < 2.2 or q < 0.34:
                col = PALC['W']
            elif q < 0.7:
                col = PALC['A']
            else:
                col = PALC['B'] if t > 0.3 else PALC['A']
            out[(x, y)] = col
    return out


def a_limit(S, margin=1):
    """largest blade coordinate a whose centre-line and edges stay inside the frame"""
    best = 91.0
    a = 0.0
    while a <= 91.0:
        for b in (0.0,):
            x, y = S.P(a, b)
            if not (margin <= x <= 127 - margin and 0 <= y <= 127):
                return a - 1.0
        a += 1.0
    return best


def draw_sword_whirl(fr, S):
    c = cv(fr)
    lim = a_limit(S)
    if lim >= 90.5:
        S.draw(c)
        return None
    cut = max(18.0, lim - 12.0)
    S.draw_blade(c, a_max=cut)
    S.draw_grip(c); S.draw_pommel(c); S.draw_guard(c)
    # ghost: the rest of the blade smeared into pale speed streaks, tapering toward the frame edge
    span = max(1.0, lim + 14 - cut)
    for y in range(128):
        for x in range(128):
            a, b = S.ab(x, y)
            if a < cut - 0.8 or a > lim + 14:
                continue
            f = (a - cut) / span
            hw = 10.5 * (1.0 - 0.55 * f)
            if abs(b) > hw:
                continue
            q = b * S.dark / hw           # -1 lit edge .. +1 dark edge
            if f > 0.55 and (int(a) // 3) % 2 == 1 and abs(q) < 0.6:
                continue
            if q < -0.55:
                col = 'W'
            elif q < 0.25:
                col = 'A'
            elif q < 0.7:
                col = 'B'
            else:
                col = 'C' if f < 0.3 else 'B'
            if f > 0.8 and abs(q) > 0.3:
                continue
            fr.px[y][x] = PALC[col]
    return cut


def whirl_frame(i, debug=False):
    yaw, side, phi = TABLE[i]
    theta = phi + LEAD
    V, L = views.build(yaw, side)
    fr = arig.Frame()

    hands = gp(HANDS_R, phi, HANDS_Y)
    def shp(a):
        ar = math.radians(a)
        return (AX + SH_R * math.cos(ar), SH_Y + SH_K * SH_R * math.sin(ar))
    sh_r = shp(phi + 90)     # his right shoulder
    sh_l = shp(phi - 90)     # his left shoulder
    near_is_right = math.sin(math.radians(phi + 90)) >= math.sin(math.radians(phi - 90))
    th = math.radians(theta)
    U = (math.cos(th), K * math.sin(th))
    lu = math.hypot(*U)
    ang = math.degrees(math.atan2(U[1], U[0]))
    grip_a = -10.0
    o = (hands[0] - U[0] * grip_a, hands[1] - U[1] * grip_a)
    S = Sword(o, ang, sa=lu, sb=1.0)      # billboarded: the flat always faces the viewer
    sword_behind = math.sin(th) < -0.25

    def elbow_for(sh):
        # bend outward from the body axis and a little down
        e1 = A_solve(sh, hands, 1)
        e2 = A_solve(sh, hands, -1)
        score = lambda e: e[1] + 0.35 * abs(e[0] - AX)
        return max((e1, e2), key=score)

    def A_solve(sh, h, bend):
        import arms as BA
        return BA.solve_elbow(sh, h, 16.0, 15.5, bend)

    arms = []
    for sh, is_right in ((sh_r, True), (sh_l, False)):
        near = (is_right == near_is_right)
        arms.append((sh, elbow_for(sh), near))

    def draw_arm(sh, el, upper_only=False, fore_only=False):
        if not fore_only:
            upper_arm(fr, sh, el)
        if not upper_only:
            fore_arm(fr, el, hands)

    back_mode = yaw >= 135
    # ---------------------------------------------------------------- behind everything
    for args in ARCS:
        smear(fr, theta, *args, 'back')
    if sword_behind:
        draw_sword_whirl(fr, S)
    if back_mode:
        for sh, el, near in arms:
            draw_arm(sh, el)
        fist(fr, hands)
    # ---------------------------------------------------------------- body
    order = views.order(yaw, side)
    near_key = 'paul_r' if near_is_right else 'paul_l'
    for name in order:
        if not back_mode and name == near_key:
            for sh, el, near in arms:
                if near:
                    draw_arm(sh, el, upper_only=True)
        fr.put(layer_rgba(L[name]))
        if not back_mode and name == 'torso':
            for sh, el, near in arms:
                if not near:
                    draw_arm(sh, el)
    # ---------------------------------------------------------------- in front
    for args in ARCS:
        smear(fr, theta, *args, 'front')
    if not sword_behind:
        draw_sword_whirl(fr, S)
    if not back_mode:
        for sh, el, near in arms:
            if near:
                draw_arm(sh, el, fore_only=True)
        fist(fr, hands, vertical=abs(U[1]) > abs(U[0]))
    return fr


if __name__ == '__main__':
    import sys
    idx = [int(a) for a in sys.argv[1].split(',')] if len(sys.argv) > 1 else list(range(13, 21))
    imgs = [whirl_frame(i).rgba() for i in idx]
    strip(imgs, 3, '../w_proto_3x.png')
    from pngio import blank, paste
    out = blank(4 * 130, 2 * 130, (40, 40, 40, 255))
    for k, im in enumerate(imgs):
        paste(out, rgba_on(im), (k % 4) * 130, (k // 4) * 130)
    zoom(out, 3, '../w_proto_grid_3x.png')
