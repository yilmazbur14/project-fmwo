"""Demon-god Jordan as the puppet master: the approved A2 god (art_source/jordan_god, read only) with
posable arms and hands.

Everything except the arms is the approved rig's own code path, stamp for stamp, so the wings,
crown, mask, tail, legs, torso, pauldrons, cracks, core, rim light and embers are the shipped
pixels. build(pose, left, right) draws him with each arm at an ArmPose; build(pose) with no arms
draws the shipped hover arms through the rig's own code (the regression check compares that with
jg_lord.build, which must be identical).

Arms are posed in CANONICAL LEFT coordinates (screen-left, his right arm): the shoulder stays on
the approved joint (143, 118) and the elbow / wrist move. Every arm part (upper-arm tube, elbow
spike, vambrace, its three blades, the arm's two lava cracks) is carried from the approved arm
into the new bones by a bone-local transform, then re-lit, so the light stays upper-left. The
screen-right arm is built the same way and mirrored (x' = 319 - x) and re-lit, exactly as the
approved rig's both() does.

Nothing here writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
GOD_DIR = os.path.join(os.path.dirname(HERE), 'jordan_god')
if GOD_DIR not in sys.path:
    sys.path.insert(0, GOD_DIR)
import jg_base as B  # noqa: E402
import jg_body as Y  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_god as G  # noqa: E402
from jg_lord_pal import PAL_A2  # noqa: E402

W, H = L.W, L.H
AX = L.AX
ANCHOR = L.ANCHOR

# the approved arm, left side
SH = (143, 118)
EL = (132, 146)
WR = (127, 170)
HAND_AT = (127, 171)
FINGERS = ('index', 'middle', 'ring', 'little')     # j = 0..3, innermost (next to the thumb) first
DIGITS = ('thumb',) + FINGERS


def _dir(a):
    return (math.cos(a), math.sin(a))


def _add(p, v, s=1.0):
    return (p[0] + v[0] * s, p[1] + v[1] * s)


class Hand:
    """How a hand is held. Angles in radians; `down` is where the palm's long axis points.
    spread widens the finger fan (1 = approved); curl bends each finger at its middle joint and
    hook bends its claw (both toward the thumb, per finger); length shortens a finger (a finger
    curling toward the viewer foreshortens)."""

    def __init__(self, down=None, spread=1.0, curl=(0.18,) * 4, hook=(0.5,) * 4, length=(1.0,) * 4,
                 claw=5.0, thumb=1.1, thumb_len=1.0, palm=(3.0, 3.6), palm_off=3.0, fan=0.0,
                 droop=(0.0,) * 4, scale=1.0, thumb_hook=1.2, thumb_droop=0.0, flip=False):
        self.down = down            # None: continue the forearm plus the approved 2-degree wrist bend
        self.spread = spread
        self.curl = tuple(curl)
        self.hook = tuple(hook)
        self.length = tuple(length)
        self.claw = claw
        self.thumb = thumb          # angle of the thumb off the palm axis (approved 1.1)
        self.thumb_len = thumb_len
        self.palm = palm
        self.palm_off = palm_off
        self.fan = fan              # turns the whole finger fan (radians)
        self.droop = tuple(droop)   # 0..1 per finger: the far segment and claw swing toward straight
        #                             down (a spread hand whose fingertips hang toward the strings)
        self.scale = scale          # 1 = approved; above 1 = the hand thrust toward the viewer
        self.thumb_hook = thumb_hook
        self.thumb_droop = thumb_droop
        self.flip = flip            # a raised, palm-forward hand: the fan and thumb swap sides, so
        #                             the thumb stays on the inner side when the fingers point up


class Arm:
    """An arm pose in canonical-left coordinates. fore_len scales the forearm's parts along the
    bone (below 1 foreshortens a forearm that points at the viewer)."""

    def __init__(self, el, wr, hand, fore_width=1.0):
        self.el = el
        self.wr = wr
        self.hand = hand
        self.fore_width = fore_width


# ------------------------------------------------------------------ bone-local transforms

class Bone:
    """Maps points from an approved bone (a0 -> a1) onto a new bone (b0 -> b1): along-bone
    distances scale with the length ratio, across-bone distances keep (times `width`)."""

    def __init__(self, a0, a1, b0, b1, width=1.0):
        self.a0, self.b0 = a0, b0
        la = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
        lb = math.hypot(b1[0] - b0[0], b1[1] - b0[1])
        self.fa = ((a1[0] - a0[0]) / la, (a1[1] - a0[1]) / la)
        self.na = (-self.fa[1], self.fa[0])
        self.fb = ((b1[0] - b0[0]) / lb, (b1[1] - b0[1]) / lb)
        self.nb = (-self.fb[1], self.fb[0])
        self.s = lb / la
        self.w = width
        self.rot = math.atan2(self.fb[1], self.fb[0]) - math.atan2(self.fa[1], self.fa[0])
        # the approved bone maps onto itself exactly (no float drift at half-texel edges)
        self.identity = (tuple(a0) == tuple(b0) and tuple(a1) == tuple(b1) and width == 1.0)
        if self.identity:
            self.rot = 0.0

    def pt(self, p):
        if self.identity:
            return p
        dx, dy = p[0] - self.a0[0], p[1] - self.a0[1]
        u = dx * self.fa[0] + dy * self.fa[1]
        v = dx * self.na[0] + dy * self.na[1]
        u *= self.s
        v *= self.w
        return (self.b0[0] + self.fb[0] * u + self.nb[0] * v, self.b0[1] + self.fb[1] * u + self.nb[1] * v)

    def ang(self, a):
        return a + self.rot


# ------------------------------------------------------------------ the hand

def _rot_ellipse(cx, cy, rx, ry, ang):
    """Pixels inside an ellipse whose ry axis points along `ang` (radians)."""
    out = set()
    R = max(rx, ry) + 1
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(int(math.floor(cy - R)) - 1, int(math.ceil(cy + R)) + 2):
        for x in range(int(math.floor(cx - R)) - 1, int(math.ceil(cx + R)) + 2):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa          # along ang (ry)
            v = -dx * sa + dy * ca         # across (rx)
            if (v / rx) ** 2 + (u / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def hand(wrist, down, hp, side=-1):
    """A long clawed hand at `wrist` (canonical left, side -1), the approved lord_hand's anatomy:
    a narrow palm, four fingers in a fan, each in two segments with a hooked claw, and the thumb
    turned in. Returns (parts, claws, tips) with tips {digit: (x, y)} the claw points (floats)."""
    parts, claws, tips = [], [], {}
    s = hp.scale
    px_, py_ = wrist[0] + math.cos(down) * hp.palm_off * s, wrist[1] + math.sin(down) * hp.palm_off * s
    legacy = abs(down - math.radians(90 - side * 14)) < 1e-9 and hp.palm == (3.0, 3.6) and s == 1.0
    if legacy:
        palm = B.ellipse(px_, py_, 3.0, 3.6)
    else:
        palm = _rot_ellipse(px_, py_, hp.palm[0] * s, hp.palm[1] * s, down)
    parts.append(L.obsidian(palm, radius=3 * s))
    fr = [r * (1.0 + (s - 1.0) * 0.5) for r in (1.2, 1.0, 0.8)]     # fingers thicken half as fast as they grow
    vert = math.pi / 2
    sd = -side if hp.flip else side

    def toward_down(a, t):
        # swing an angle toward straight down by fraction t, the short way round
        d = (vert - a + math.pi) % (2 * math.pi) - math.pi
        return a + d * t

    for j, off in enumerate((-0.42, -0.14, 0.14, 0.42)):
        a = down + off * hp.spread * sd * -1 + hp.fan
        ln = (9.5 if j in (1, 2) else 8.0) * s
        b0 = (px_ + math.cos(a) * 2.6 * s, py_ + math.sin(a) * 2.6 * s)
        k1 = (b0[0] + math.cos(a) * ln * 0.5, b0[1] + math.sin(a) * ln * 0.5)
        a2 = a + sd * hp.curl[j]
        if hp.droop[j]:
            a2 = toward_down(a2, hp.droop[j])
        seg2 = ln * 0.5 * hp.length[j]
        k2 = (k1[0] + math.cos(a2) * seg2, k1[1] + math.sin(a2) * seg2)
        parts.append(L.obs_tube([b0, k1, k2], fr))
        a3 = a2 + sd * hp.hook[j]
        if hp.droop[j]:
            a3 = toward_down(a3, hp.droop[j] * 0.5)
        cl = hp.claw * s ** 0.5 * (0.6 + 0.4 * hp.length[j])
        tip = (k2[0] + math.cos(a3) * cl, k2[1] + math.sin(a3) * cl)
        claws.append(Y.limb([k2, tip], [1.0 * fr[0] / 1.2, 0.3], ('3', '4', '5'), cuts=[0.4, 0.78]))
        tips[FINGERS[j]] = tip
    ta = down + sd * hp.thumb
    t0 = (px_ + math.cos(ta) * 2.4 * s, py_ + math.sin(ta) * 2.4 * s)
    tb = ta - sd * 0.6
    if hp.thumb_droop:
        tb = toward_down(tb, hp.thumb_droop)
    t1 = (t0[0] + math.cos(tb) * 5 * hp.thumb_len * s, t0[1] + math.sin(tb) * 5 * hp.thumb_len * s)
    parts.append(L.obs_tube([t0, t1], [1.2 * fr[0] / 1.2, 0.9 * fr[0] / 1.2]))
    tc = ta - sd * hp.thumb_hook
    if hp.thumb_droop:
        tc = toward_down(tc, hp.thumb_droop)
    t2 = (t1[0] + math.cos(tc) * 3.5 * s ** 0.5, t1[1] + math.sin(tc) * 3.5 * s ** 0.5)
    claws.append(Y.limb([t1, t2], [0.9 * fr[0] / 1.2, 0.3], ('3', '4', '5'), cuts=[0.4, 0.78]))
    tips['thumb'] = t2
    return parts, claws, tips


# ------------------------------------------------------------------ the arm

def arm_parts(arm, crack_pts):
    """All of one arm's parts in stamping order, canonical left. crack_pts: the approved arm's two
    crack paths (vambrace, upper arm), carried into the new bones. Returns (parts, cracks, tips)."""
    up = Bone(SH, EL, SH, arm.el)
    fo = Bone(EL, WR, arm.el, arm.wr, width=arm.fore_width)
    upper = L.obs_tube([SH, ((SH[0] + arm.el[0]) / 2.0, (SH[1] + arm.el[1]) / 2.0), arm.el], [3.8, 3.2, 2.9])
    # the elbow spike rides between the two bones: its base on the forearm's root, its direction
    # halfway between the two bones' turns
    espike_base = fo.pt((131, 147))
    espike_dir = math.radians(165) + (up.rot + fo.rot) / 2.0
    elbow_spike = L.spike(espike_base, espike_dir, 8, 2.3, bend=1.0)
    vam = L.obsidian(B.poly([fo.pt(p) for p in [(131, 148), (135, 150), (131, 170), (126, 172), (125, 160)]]),
                     radius=3)
    blades = []
    for j, yy in enumerate((153, 159, 165)):
        blades.append(L.spike(fo.pt((127.5 - j * 0.6, yy)), fo.ang(math.radians(180 + 18)), 6 - j, 1.6, bend=1.2,
                              radius=1.6))
    # the wrist: where the approved hand hangs (127, 171), carried by the forearm
    wrist = fo.pt(HAND_AT)
    hp = arm.hand
    down = hp.down if hp.down is not None else math.radians(104) + fo.rot
    hparts, hclaws, tips = hand(wrist, down, hp)
    parts = [upper, elbow_spike, vam] + blades + hparts + hclaws
    cracks = [[fo.pt(p) for p in crack_pts[0]], [up.pt(p) for p in crack_pts[1]]]
    return parts, cracks, tips


IDLE = Arm(EL, WR, Hand())


def _relit_mirror(part, radius=None):
    m = L.mir(part)
    if all(k in L.OBS_KEYS for k in m.values()):
        m = L.obsidian(set(m), radius=radius)
    return m


# ------------------------------------------------------------------ build

def build(pose=None, left=None, right=None, legacy=False):
    """The god at `pose` (a jg_lord.Pose), his screen-left arm at `left` and screen-right arm at
    `right` (Arm, canonical-left coordinates; None = the approved hanging arm). legacy=True
    stamps the approved arm code verbatim (the regression path). Returns (px, tips) where tips is
    {'left': {digit: (x, y)}, 'right': {...}} in frame texels (floats, before any bob)."""
    pose = pose or L.STILL
    L.GLOW[0] = pose.glow
    C = B.Canvas(W, H + 16)
    rnd = __import__('random').Random(5)
    mir, mp, both, spike, obsidian, obs_tube = L.mir, L.mp, L.both, L.spike, L.obsidian, L.obs_tube
    crack_path, draw_crack, top_edge = L.crack_path, L.draw_crack, L.top_edge

    # 1. wings
    lpart, geom, veins = L.wing_left(pose)
    C.stamp(mir(lpart))
    C.stamp(lpart)
    for (p0, p1) in veins:
        for pts in (crack_path(p0, p1, rnd, jag=1.0), crack_path(mp(p0), mp(p1), rnd, jag=1.0)):
            draw_crack(C, pts, hot0=0.35, hot1=0.05, only=L.LEATHER_KEYS)
    bones, claws = L.wing_bones_left(geom)
    for b in bones + claws:
        both(C, b, radius=2.6)

    # 2. tail
    tail_ctrl = [(162, 152), (163, 172), (170, 190), (185, 203), (193, 212), (182, 218), (160, 218.5),
                 (141, 215), (130, 207), (129, 198), (134, 193)]
    if pose.tail_sway:
        tail_ctrl = [(x + pose.tail_sway * max(0.0, (i - 2) / 8.0) ** 1.2, y) for i, (x, y) in enumerate(tail_ctrl)]
    tail = Y.smooth_curve(tail_ctrl, n=10)
    radii = Y.taper(len(tail), 6.4, 1.2, power=1.0)
    tpart = obs_tube(tail, radii)
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(tail, tail[1:])]
    acc = 0.0
    rings = []
    for i, s in enumerate(seg):
        acc += s
        if acc >= 5.0:
            acc = 0.0
            (x0, y0), (x1, y1) = tail[i], tail[i + 1]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            r = radii[i]
            rings.append([(x1 + nx * r, y1 + ny * r), (x1 - nx * r, y1 - ny * r)])
    C.stamp(tpart)
    for a, b in rings:
        for q in B.line(a[0], a[1], b[0], b[1]):
            if q in tpart:
                C.px[q] = 'k'
    for i in range(12, len(tail) - 12, 9):
        (x0, y0), (x1, y1) = tail[i], tail[i + 1]
        ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
        base = (x1 + math.cos(ang) * radii[i] * 0.8, y1 + math.sin(ang) * radii[i] * 0.8)
        C.stamp(spike(base, ang, 4 + radii[i] * 0.6, 1.6, radius=1.8))
    if pose.tail_seam:
        seam = []
        for i in range(18, len(tail) - 14):
            (x0, y0), (x1, y1) = tail[i], tail[i + 1]
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            seam.append((x1 - nx * radii[i] * 0.35, y1 - ny * radii[i] * 0.35))
        n_ = len(seam)
        for j in range(0, n_ - 1, 1):
            a, b = seam[j], seam[j + 1]
            for q in B.line(a[0], a[1], b[0], b[1]):
                if C.px.get(q) in L.OBS_KEYS:
                    t = j / max(1, n_ - 1)
                    heat = (0.62 - 0.5 * t) * pose.glow
                    C.px[q] = 'V' if heat < 0.22 else 'R' if heat < 0.45 else 'T'

    # 3. legs
    hip, knee, ankle, toe = (153, 160), (150, 186), (152, 204), (153, 214)
    thigh = obs_tube([hip, ((hip[0] + knee[0]) / 2.0 - 0.5, (hip[1] + knee[1]) / 2.0), knee], [5.2, 4.6, 3.4])
    shin = obs_tube([knee, ((knee[0] + ankle[0]) / 2.0 - 0.8, (knee[1] + ankle[1]) / 2.0), ankle],
                    [3.4, 3.4, 2.2])
    for y in range(189, 203):
        x = int(round(149.4 + (y - 189) * 0.1))
        if (x, y) in shin:
            shin[(x, y)] = '5' if y < 197 else '4'
    foot = obsidian(B.poly([(149, 203), (155, 203), (156, 209), (153.5, 216), (150, 209)]), radius=2.5)
    toes = [spike((150.5, 210), math.radians(118), 5, 1.2, bend=0.8, radius=1.5),
            spike((155.5, 210), math.radians(70), 4, 1.1, bend=-0.6, radius=1.5)]
    tasset = top_edge(obsidian(B.poly([(145, 157), (157, 159), (155, 172), (150, 175), (146, 170)]), radius=4,
                               cuts=(0.24, 0.44, 0.64, 0.86)), '4')
    knee_cop = obsidian(B.ellipse(150, 185.5, 3.4, 3.0), radius=3)
    knee_spur = spike((147.5, 186), math.radians(196), 6, 1.8, bend=-1.0, radius=1.8)
    both(C, thigh)
    both(C, shin)
    for t in toes:
        both(C, t)
    both(C, foot)
    both(C, tasset)
    both(C, knee_spur)
    both(C, knee_cop)
    for (a, b) in (((153, 175), (151.5, 181)),):
        pts = crack_path(a, b, rnd, jag=0.6)
        draw_crack(C, pts, 0.4, 0.1)
        draw_crack(C, [mp(p) for p in pts], 0.4, 0.1)

    # 4. torso
    fauld = B.poly([(147, 148), (159.5, 149), (159.5, 166), (153, 160), (146, 156)])
    both(C, obsidian(fauld, radius=4))
    hipspike = spike((147, 153), math.radians(160), 8, 2.2)
    both(C, hipspike)
    for i, (y0, y1, hw0, hw1) in enumerate(((133, 138, 13, 12), (138, 143, 12, 10.5), (143, 149, 10.5, 9))):
        seg_l = B.poly([(159.5 - hw0, y0), (159.5, y0 + 1), (159.5, y1 + 1), (159.5 - hw1, y1)])
        sl = top_edge(obsidian(seg_l, radius=4, cuts=(0.24, 0.44, 0.64, 0.86)), '4')
        C.stamp(sl)
        C.stamp(top_edge(obsidian(set(mir(sl)), radius=4, cuts=(0.24, 0.44, 0.64, 0.86)), '3'))
    for base, ang, ln in (((145, 136), 172, 7), ((147, 142), 165, 6)):
        both(C, spike(base, math.radians(ang), ln, 1.8, bend=1.5, radius=1.8))
    pec = B.poly([(159.5, 112), (153, 109), (146, 111), (142, 118), (144, 127), (150, 133), (159.5, 134)])
    pl = top_edge(obsidian(pec, radius=8, cuts=(0.26, 0.46, 0.66, 0.86)), '5')
    C.stamp(pl)
    C.stamp(top_edge(obsidian(set(mir(pl)), radius=8, cuts=(0.26, 0.46, 0.66, 0.86)), '4'))

    # 5. arms
    tips = {}
    if legacy:
        sh, el, wr = (143, 118), (132, 146), (127, 170)
        upper = obs_tube([sh, ((sh[0] + el[0]) / 2.0, (sh[1] + el[1]) / 2.0), el], [3.8, 3.2, 2.9])
        both(C, upper)
        elbow_spike = spike((131, 147), math.radians(165), 8, 2.3, bend=1.0)
        both(C, elbow_spike)
        vam = obsidian(B.poly([(131, 148), (135, 150), (131, 170), (126, 172), (125, 160)]), radius=3)
        both(C, vam)
        for j, yy in enumerate((153, 159, 165)):
            blade = spike((127.5 - j * 0.6, yy), math.radians(180 + 18), 6 - j, 1.6, bend=1.2, radius=1.6)
            both(C, blade)
        hparts, hclaws = L.lord_hand((127, 171), -1)
        for hp in hparts + hclaws:
            both(C, hp)
        for a, b in (((129, 151), (128, 167)), ((140, 122), (135, 140))):
            pts = crack_path(a, b, rnd, jag=0.7)
            draw_crack(C, pts, 0.5, 0.1)
            draw_crack(C, [mp(p) for p in pts], 0.5, 0.1)
    else:
        # the approved crack paths, drawn from the same random stream in the same order, so every
        # crack after the arms (the chest's) is the approved one
        crack_pts = [crack_path(a, b, rnd, jag=0.7) for a, b in (((129, 151), (128, 167)), ((140, 122), (135, 140)))]
        lparts, lcracks, ltips = arm_parts(left or IDLE, crack_pts)
        rparts, rcracks, rtips = arm_parts(right or IDLE, crack_pts)
        for lp, rp in zip(lparts, rparts):
            C.stamp(lp)
            C.stamp(_relit_mirror(rp))
        for lc, rc in zip(lcracks, rcracks):
            draw_crack(C, lc, 0.5, 0.1)
            draw_crack(C, [mp(p) for p in rc], 0.5, 0.1)
        tips = {'left': ltips, 'right': {d: mp(p) for d, p in rtips.items()}}

    # 6. pauldrons
    pa = obsidian(B.poly([(131, 112), (138, 105), (148, 105), (152, 111), (149, 119), (140, 123), (132, 121)]),
                  radius=6, cuts=(0.26, 0.46, 0.66, 0.86))
    pb = obsidian(B.poly([(129, 118), (135, 116), (142, 122), (138, 128), (130, 126)]), radius=4)
    pb = top_edge(pb, '4')
    pa = top_edge(pa, '5')
    C.stamp(pb)
    C.stamp(top_edge(obsidian(set(mir(pb)), radius=4), '4'))
    C.stamp(pa)
    C.stamp(top_edge(obsidian(set(mir(pa)), radius=6, cuts=(0.26, 0.46, 0.66, 0.86)), '4'))
    for base, ang, ln, wd in (((136, 107), -118, 16, 3.0), ((131, 113), -150, 11, 2.6), ((144, 105), -97, 9, 2.2)):
        both(C, spike(base, math.radians(ang), ln, wd, bend=-1.5))

    # 7. collar spikes, neck, head
    both(C, spike((152, 108), math.radians(-105), 8, 2.0, bend=-0.8))
    neck = obs_tube([(159.5, 104), (159.5, 112)], [4.4, 4.8])
    C.stamp(neck)
    back, front = L.crown_horns(pose)
    for h in back:
        C.stamp(h)
    C.stamp(L.face_mask(pose.mouth_open), outline=False)
    C.stamp(L.hair_crown(), outline=False)
    for h in front:
        C.stamp(h)

    # 8. chest cracks
    for ang, ln in ((-150, 16), (-120, 12), (-35, 15), (-62, 11), (160, 13), (25, 13), (110, 20)):
        a = math.radians(ang)
        p0 = (L.CORE[0] + math.cos(a) * 4, L.CORE[1] + math.sin(a) * 4)
        p1 = (L.CORE[0] + math.cos(a) * ln, L.CORE[1] + math.sin(a) * ln)
        draw_crack(C, crack_path(p0, p1, rnd, jag=1.2, step=2.5), 0.95, 0.15)
    draw_crack(C, crack_path((159.5, 129), (159.5, 160), rnd, jag=0.6, step=3), 0.85, 0.2)

    # 9. the core
    core = {}
    cx, cy = L.CORE
    s = pose.core
    for (x, y) in B.ellipse(cx, cy, 6.0 * max(1.0, s), 6.0 * max(1.0, s)):
        dxx, dyy = abs(x - cx), abs(y - cy)
        d = math.hypot(dxx, dyy)
        if d < 1.2:
            k = 'w'
        elif (dxx < 0.6 and dyy < 5.5 * s) or (dyy < 0.6 and dxx < 5.5 * s):
            k = 'Y' if d < 4 * s else 'O'
        elif abs(dxx - dyy) < 0.8 and d < 3.6 * s:
            k = 'O'
        elif d < 2.6 * s:
            k = 'Y'
        elif 3.6 * s <= d < 5.0 * s:
            k = 'P' if (x + y) % 2 else 'Q'
        else:
            continue
        core[(x, y)] = k
    C.stamp(core, outline=False)
    px = L.rim_light(C.px)
    px = {p: ('k' if k == '1' else k) for p, k in px.items()}
    px = L.fill_pinholes(px)
    for (x, y, k) in pose.embers:
        if (x, y) not in px:
            px[(x, y)] = k
    return px, tips


def bobbed(px, bob):
    return {(x, y - bob): k for (x, y), k in px.items() if 0 <= y - bob < H}


def image(px):
    return B.image(px, W, H, PAL_A2)


if __name__ == '__main__':
    # regression: the rig's copy with the approved arms must equal the approved rig, pose for pose
    bad = 0
    for i in range(G.N):
        want = L.build('A2', G.pose(i), seat=False)
        got, _ = build(G.pose(i), legacy=True)
        got2, _ = build(G.pose(i))
        same = want == got
        same2 = want == got2
        diff2 = len(set(want.items()) ^ set(got2.items()))
        print('hover pose %d: legacy path %s; posable path with the idle arm %s (%d texels differ)'
              % (i, 'identical' if same else 'DIFFERENT', 'identical' if same2 else 'differs', diff2))
        bad += not same
    sys.exit(1 if bad else 0)
