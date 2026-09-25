"""Matt's Glass Row and Deafening Yell sheets, on the approved rig.

matt_stomp: 4 frames, 0.15 0.30 0.08 hold. A sumo stomp: the knee rising, the knee high (the tell
    hold), the SLAM (his body drops six texels into a wide squat, "HUP!"), the recoil.
matt_fury: 4 frames at 0.08, looping. A furious stomping jig in the talk sheet's furious face:
    left foot up, left SLAM, right foot up, right SLAM.
matt_yell_up: 5 frames, 0.25 0.25, then f2-4 looping at 0.06. The head tips back on a huge breath,
    then he yells straight up at the ceiling, the loop shaking like the roar's.
"""
import mg_base as M
from mg_base import B, A, G, F, H, L, PZ, FF
import mg_faces as MF

# the crest tipped back with his head: every spike foreshortened, the centre (pointing back) most
SP_TIPPED = [(0, 8, 17, 6.4, 2.0, 0.0), (-46, 8, 21, 6.4, 2.0, 0.5), (-86, 9, 28, 7.2, 2.4, 1.0)]
SP_TIPPING = PZ.lerp_spikes(PZ.SP_IDLE, SP_TIPPED, 0.5)


def squat_legs(drop, stance):
    return lambda f: L.walk_legs(drop, (-stance, 0, -1.6), (stance, 0, 1.6), screen=True)


def slam_fig(drop=6, stance=6):
    arms = PZ.hang_pair(upper_rot=34, fore_rot=24, shoulder_dy=-1)
    face = G.face(G.BR_ANGRY, G.EY_ANGRY, FF.M_O)          # the round "HUP!" of a sumo stomp
    return F.Fig(arms=arms, legs=squat_legs(drop, stance), body=(0, drop), head=(0, drop + 1),
                 face=(face, G.X0, G.Y0), spikes=PZ.SP_ROAR)


def yell_up_fig(k=0):
    """One frame of the skyward yell loop (k = 0, 1, 2): the approved roar's shake, sideways."""
    dx = [0, 1, -1][k]
    return F.Fig(arms=PZ.hang_pair(upper_rot=22, fore_rot=4, shoulder_dy=-2, dx=dx), body=(dx, 0),
                 face=(MF.YELL_UP, G.X0, G.Y0), head=(dx, 3 + (1 if k == 1 else 0)), collar=False,
                 spikes=SP_TIPPED, stance=2)


# ------------------------------------------------------------------ the lifted leg (sumo stomp)
from mi_base import sh, details, moved as mv, capsule


def lifted_leg(knee, ankle, side=0):
    """A trouser leg lifted out to the side: the thigh from the hip up and out to a bent knee, the
    shin hanging from the knee to the hem, in the rig's trouser charcoal shaded as the rig shades its
    legs, then the approved sock and trainer hanging below the hem. side 0 = screen-left leg."""
    hip = (40.0, 73.0) if not side else (56.0, 73.0)
    thigh = capsule(hip, knee, 7.6, 7.0)
    shin = capsule(knee, ankle, 7.0, 6.8)
    cut = {p for p in (thigh | shin) if (not side and p[0] >= 48 and p[1] < 77) or (side and p[0] <= 48 and p[1] < 77)}
    upper = {p: 'L' for p in thigh - cut}
    lower_ = {p: 'L' for p in shin - cut if p not in upper}
    sh.cylinder(upper, hip, knee, 8.5, 'NMLK', (0.84, 0.62, 0.2))
    sh.cylinder(lower_, knee, ankle, 8.5, 'NMLK', (0.84, 0.62, 0.2))
    # thigh and shin are separate forms: stamped one after the other, each keylined, the bent knee
    # is drawn where the shin's top meets the thigh's end, as a sleeve meets its cuff
    shin_part = {p: k for p, k in lower_.items()}
    shin_part.update({p: upper[p] for p in upper if p in shin})
    sh.cylinder(shin_part, knee, ankle, 8.5, 'NMLK', (0.84, 0.62, 0.2))
    leg = (upper, shin_part)
    # the sock and trainer hang from the hem: the foot map's striped sock starts at the shin's end
    fx, fy = (ankle[0] - 35.5, ankle[1] + 6 - 85) if not side else (ankle[0] - 60.5, ankle[1] + 6 - 85)
    foot = L.foot(side, int(round(fx)), int(round(fy)))
    # the hem's keyline across the sock's top, where the shin does not already cover it
    top = min(y for (x, y), k in foot.items() if k in 'WXx')
    for (x, y), k in list(foot.items()):
        if y == top and k in 'WXxk':
            foot.setdefault((x, y - 1), 'k')
    return foot, leg


KNEE_CREASES = {1: [((35, 79), (36, 78), (37, 77))],
                2: [((25, 71), (26, 70), (27, 69)), ((30, 74), (31, 73), (32, 72))]}


def mirror(p):
    return (96 - p[0], p[1])


def stomp_legs(lift, stance=1, side=0):
    """One leg planted, the other lifted out to the side. side: the lifted leg (0 = screen-left,
    1 = screen-right, its knee and ankle the left one's mirrored). lift: 0 down, 1 rising, 2 high."""
    planted = 1 - side
    s = stance if planted else -stance

    def fn(f):
        parts = []
        parts.append((L.foot(planted, s, 0), False))
        parts.append((L.leg(planted, 0, s, 0, 0.0, screen=True), True))
        if lift == 0:
            parts.append((L.foot(side, -s, 0), False))
            parts.append((L.leg(side, 0, -s, 0, 0.0, screen=True), True))
        else:
            knee, ankle = {1: ((29, 68), (24, 74)), 2: ((22, 60), (15, 65))}[lift]
            creases = KNEE_CREASES[lift]
            if side:
                knee, ankle = mirror(knee), mirror(ankle)
                creases = [tuple(mirror(p) for p in c) for c in creases]
            foot, (thigh, shin) = lifted_leg(knee, ankle, side)
            # the trouser pulled round the bent knee: creases running up out of the knee pit across
            # the thigh's underside, each with its lit lip above
            for crease in creases:
                for (x, y) in crease:
                    if (x, y) in thigh:
                        thigh[(x, y)] = 'k'
                for (x, y) in crease:
                    q = (x, y - 1)
                    if q in thigh and thigh[q] != 'k' and q not in crease:
                        thigh[q] = B.LIGHTER.get(thigh[q], thigh[q])
            parts.append((foot, False))
            parts.append((thigh, True))
            parts.append((shin, True))
        return parts
    return fn


def stomp_figs():
    import mi_arms as AA
    import mi_hands as HH
    def balance_arm(lift):
        """His left arm thrown up and out for balance over the lifted leg."""
        if lift == 1:
            return AA.bent(0, (25, 56), (24, 57), (13, 57), (11, 49), hand=HH.FIST_UP_L)
        return AA.bent(0, (25, 55), (24, 56), (12, 51), (12, 42), hand=HH.FIST_UP_L)
    def armpit_fold(part):
        """The sweatshirt bunching under the arm thrown up: a short black fold in from the armpit,
        its lip lit above."""
        for (x, y) in ((33, 59), (34, 60), (35, 61), (36, 61)):
            if (x, y) in part:
                part[(x, y)] = 'k'
            if (x, y - 1) in part and part[(x, y - 1)] != 'k':
                part[(x, y - 1)] = B.LIGHTER[part[(x, y - 1)]] if part[(x, y - 1)] in B.LIGHTER else part[(x, y - 1)]
    rising = F.Fig(arms=[balance_arm(1), AA.hang(1, upper_rot=16, fore_rot=10, shoulder_dy=-1)], legs=stomp_legs(1),
                   torso_hook=armpit_fold,
                   body=(2, 0), head=(2, 0), face=(G.face(G.BR_ANGRY, G.EY_ANGRY, G.M_GRIT), G.X0, G.Y0),
                   spikes=PZ.SP_TENSE)
    high = F.Fig(arms=[balance_arm(2), AA.hang(1, upper_rot=28, fore_rot=20, shoulder_dy=-2)], legs=stomp_legs(2),
                 torso_hook=armpit_fold,
                 body=(3, -1), head=(3, -1), face=(G.face(G.BR_ANGRY, G.EY_ANGRY, G.M_GRIT), G.X0, G.Y0),
                 spikes=PZ.lerp_spikes(PZ.SP_TENSE, PZ.SP_ROAR, 0.4), neck=True)
    slam = slam_fig()
    recoil = F.Fig(arms=PZ.hang_pair(upper_rot=20, fore_rot=12, shoulder_dy=0), legs=squat_legs(3, 5),
                   body=(0, 3), head=(0, 3), face=(G.face(G.BR_ANGRY, G.EY_ANGRY, FF.M_PRESS), G.X0, G.Y0),
                   spikes=PZ.lerp_spikes(PZ.SP_ROAR, PZ.SP_TENSE, 0.5))
    return [rising, high, slam, recoil]


# ------------------------------------------------------------------ the furious jig
FISTS_UP = ((25, 56), (24, 57), (13, 57), (15, 47))      # the talk sheet's furious fists
FISTS_PUMP = ((25, 57), (24, 58), (13, 60), (15, 51))    # driven down with each slam
STEAM_SHUT = [('PUFF_B', 26, 28), ('PUFF_C', 22, 23), ('PUFF_B', 63, 28), ('PUFF_C', 70, 23)]
STEAM_OPEN = [('PUFF_C', 28, 30), ('PUFF_A', 19, 23), ('PUFF_C', 64, 30), ('PUFF_A', 68, 23)]


def fury_fig(k):
    """k 0: left foot up, 1: left SLAM, 2: right foot up, 3: right SLAM. The talk sheet's furious
    face throughout (flushed, blank-white eyes, fury brows, veins, steam off both ears), its two
    mouths alternating: "ENOUGH" bellowed as each knee comes up, teeth clenched as the foot lands.
    (The open mouth on the slams measured 26.3-26.8% black, over the 26.1% ceiling: the talk
    sheet's own open furious frame is already 26.1%, and a slam's squat only takes body away.)"""
    lift = k % 2 == 0
    side = 0 if k < 2 else 1
    sgn = 1 if side == 0 else -1
    if lift:
        # the weight goes over the planted leg; he rises a texel
        body = head = (2 * sgn, -1)
        legs = stomp_legs(1, 1, side)
        face = G.flushed(G.with_jaw(G.face(G.BR_FURY, G.EY_BLANK), G.ENOUGH_ROWS))
        arms = PZ.pair(*FISTS_UP, H.FIST_UP_L, H.FIST_UP_R)
        steam_spec, spikes = STEAM_OPEN, PZ.SP_BRISTLE
    else:
        # the stamping foot lands wide, the body drops onto it, fists driven down
        body, head = (-sgn, 2), (-sgn, 3)
        left, right = ((-5, 0, -1.6), (2, 0, 0.8)) if side == 0 else ((-2, 0, -0.8), (5, 0, 1.6))
        legs = (lambda l, r: (lambda f: L.walk_legs(2, l, r, screen=True)))(left, right)
        face = G.flushed(G.face(G.BR_FURY, G.EY_BLANK, G.M_GRIT))
        arms = PZ.pair(*FISTS_PUMP, H.FIST_UP_L, H.FIST_UP_R)
        steam_spec, spikes = STEAM_SHUT, PZ.lerp_spikes(PZ.SP_BRISTLE, PZ.SP_ROAR, 0.35)
    hx, hy = head
    steam = [(M.part(getattr(G, name), x + hx, y + hy), False, 'front') for name, x, y in steam_spec]
    veins = [(M.part(G.VEIN, 55 + hx, 20 + hy), False, 'front'),
             (M.part(G.VEIN, 32 + hx, 20 + hy), False, 'front')]
    f = F.Fig(arms=arms, legs=legs, body=body, head=head, face=(face, G.X0, G.Y0),
              parts=veins + steam, spikes=spikes)
    f.fx = set().union(*[set(p) for p, _, _ in steam])
    return f


def fury_figs():
    return [fury_fig(k) for k in range(4)]


# ------------------------------------------------------------------ the skyward yell
def yell_up_figs():
    """f0 he drags in a breath, eyes rolled up to the ceiling, the crest starting back; f1 the
    head thrown back, mouth shut on the breath; f2-4 the yell straight up (f3 is the approved
    frame), shaking a texel side to side like the roar's loop."""
    breath = F.Fig(arms=PZ.hang_pair(upper_rot=-4, fore_rot=-6, shoulder_dy=-3), body=(0, -1),
                   head=(0, 0), face=(G.face(G.BR_HIGH, MF.EY_UP, G.M_INHALE), G.X0, G.Y0),
                   spikes=SP_TIPPING, stance=2)
    tipped = F.Fig(arms=PZ.hang_pair(upper_rot=8, fore_rot=2, shoulder_dy=-3), body=(0, -1),
                   head=(0, 3), face=(MF.TIP_BACK, G.X0, G.Y0), spikes=SP_TIPPED, stance=2)
    return [breath, tipped] + [yell_up_fig(k) for k in range(3)]
