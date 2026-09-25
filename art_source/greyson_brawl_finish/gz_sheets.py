"""Greyson's brawl sheets, the FINISHING half: dazed, uppercut, recover, KO, toss (and the barbell
prop). Shaped like greyson_brawl/gb_sheets.py, so the brawl's shared gated exporter ships it:
SHEETS maps a sheet name to its frames [(label, builder, kwargs)], frame 0 leftmost, and each
builder returns (canvas, anchors).

Every frame is a front view (he faces the player), never flipped: his right fist on screen left,
the cannon gauntlet on screen right. Anchors, in cell texels (x right, y down, feet (56, 111)),
measured the brawl rig's way:
  crown     the top of his hair on the head's centre line
  chin      the jaw's keyline row + 2, on the head's centre line
  fist      his right fist's centre
  gauntlet  the cannon's striking end: the centre of its muzzle ring
  muzzle    the centre of the bore's dark face
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gz_base as Z  # noqa: E402
import gz_faces  # noqa: E402
import gz_ko as KO  # noqa: E402

K, G, P, F, BD, A = Z.K, Z.G, Z.P, Z.F, Z.BD, Z.A
gr_arms, gr_hands, gf_cannon = Z.gr_arms, Z.gr_hands, Z.gf_cannon
Canvas, moved, mp = Z.Canvas, Z.moved, Z.mp


# ------------------------------------------------------------------------------------ dazed

def dazed(d=6, head=(0, 13), lat=0.5, face='dazed0', sh_r=0.0, sh_l=0.0):
    """The approved dazed slump (gb_fig.dazed, which this reproduces exactly at the defaults) with
    the sway free: the head lolling `head` (dx, dy), the knees `d`, each hanging arm swung at the
    shoulder (degrees; positive swings the hand to screen left)."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=lat)
    arm = P.Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, P.I_SHOULDER, P.I_ELBOW, sh=sh_r)
    cv.stamp(moved(K.despeckle(P.arm_layer(arm, gr_arms.SPEC, 0)), 0, d))
    up = P.Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, P.I_SHOULDER, P.I_ELBOW, sh=sh_l)
    cv.stamp(moved(K.despeckle(P.arm_layer(up, gr_arms.SPEC, 1, keep=('delt', 'upper', 'biceps'))),
                   0, d))
    p0, p1 = mp(up.upper(P.CANNON_HANG[0])), mp(up.upper(P.CANNON_HANG[1]))
    p0, p1 = (p0[0], p0[1] + d), (p1[0], p1[1] + d)
    cn = gf_cannon.cannon(p0, p1, face=0.62)
    cv.stamp(cn)
    fp = arm.fore(P.IDLE_FIST)
    fist = gr_hands.fist('idle', 0, (fp[0], fp[1] + d))
    cv.stamp(fist, outline=False)
    hp, fpx = gz_faces.head(face, head[0], head[1])
    cv.stamp(hp, outline=False)
    P.finish(cv, fpx)
    return cv, F.anchors(head[1], head[0], F.fist_centre(fist), p1, cn)


# ------------------------------------------------------------------------------------ any pose

def pose(d=4, head=(0, 7), face='menace', extras=None, right=None, left=None,
         order='right_first', lat=1.0, fx=()):
    """One brawl frame (the brawl rig's gb_sheets.frame, with every rig's faces and this half's).
    right: None for the approved guard's right arm, else {'elbow', 'fist'} (+ 'fist_map'), or
           'hang' for the approved idle arm hanging (fist at the thigh).
    left:  None for the approved guard's cannon arm, else {'elbow', 'gauntlet'} (+ 'face').
    order: 'right_first' stamps the cannon arm last (in front), 'left_first' the fist arm.
    fx:    effect pixels (flying sweat) laid over everything, exempt from the orphan sweep."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=lat)
    hp, fpx = gz_faces.head(face, head[0], head[1], extras)
    cv.stamp(hp, outline=False)

    def do_right():
        if right is None:
            _, fist = F.guard_arm_right(cv, d, 6.0, -6.0, 'idle')
            return fist, F.fist_centre(fist)
        if right == 'hang':
            arm = P.Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, P.I_SHOULDER, P.I_ELBOW)
            cv.stamp(moved(K.despeckle(P.arm_layer(arm, gr_arms.SPEC, 0)), 0, d))
            fist = gr_hands.fist('idle', 0, (P.IDLE_FIST[0], P.IDLE_FIST[1] + d))
            return fist, F.fist_centre(fist)
        parts, fc = A.fist_arm(d, right['elbow'], right['fist'], right.get('fist_map', 'idle'))
        for part, ol in parts[:-1]:
            cv.stamp(part, outline=ol)
        return parts[-1][0], fc

    def do_left():
        if left is None:
            return Z.GS.guard_cannon(cv, d), Z.GS.GUARD_GAUNTLET
        parts, cn = A.cannon_arm(d, left['elbow'], left['gauntlet'], left.get('face', 0.3))
        for part, ol in parts:
            cv.stamp(part, outline=ol)
        return cn, left['gauntlet']

    if order == 'right_first':
        fist, fc = do_right()
        cv.stamp(fist, outline=False)
        cn, g = do_left()
    else:
        cn, g = do_left()
        fist, fc = do_right()
        cv.stamp(fist, outline=False)
    fx = dict(fx) if fx else {}
    cv.px.update(fx)
    P.finish(cv, set(fpx) | set(fx))
    return cv, anchors(face, head, fc, g, cn)


def anchors(face, head, fist, gauntlet, cn):
    """The brawl rig's anchors, with the chin measured on THIS face's own jaw (a face whose jaw
    drops, like the roar's, moves its chin with it)."""
    dx, dy = head
    return {'crown': P.crown_of(moved(Z.gr_face.mane(), dx, dy)),
            'chin': (56 + dx, gz_faces.jaw_row(face) + dy + 2),
            'fist': fist, 'gauntlet': Z.rnd(gauntlet), 'muzzle': F.bore_centre(cn)}


# flying sweat: the approved bead's shape (gr_face.SWEAT), knocked off his head
def bead(dx, dy):
    return moved(Z.gr_face.SWEAT, dx, dy)


# the tooth the killing uppercut knocks out (the gap is in the KO face's teeth), flying off
TOOTH = {(1, 0): 'k', (2, 0): 'k',
         (0, 1): 'k', (1, 1): 'W', (2, 1): 'X', (3, 1): 'k',
         (0, 2): 'k', (1, 2): 'X', (2, 2): 'x', (3, 2): 'k',
         (1, 3): 'k', (2, 3): 'k'}


def tooth(x, y):
    return {(x + dx, y + dy): k for (dx, dy), k in TOOTH.items()}


# ------------------------------------------------------------------------------------ the toss
# The barbell is the fight rig's (gf_barbell: the chrome bar, the one iron plate), at its approved
# size: the bar 44 texels from the grip to the plate's centre, the plate's radius 10.4.
BAR_LEN = 44.0
PLATE_R = 10.4


def barbell(grip, plate_c, squash=0.62, ang=None):
    """The barbell's parts, keylined: the plate at plate_c (its long axis across the bar, so it
    is seen three-quarters on) and the bar from the plate to the grip."""
    import math
    if ang is None:
        ang = math.degrees(math.atan2(grip[1] - plate_c[1], grip[0] - plate_c[0])) + 90.0
    return Z.gf_barbell.plate(plate_c, r=PLATE_R, squash=squash, ang=ang), \
        Z.gf_barbell.bar(plate_c, grip)


def open_arm(cv, d, elbow, wrist):
    """His right arm (screen left) flung out with the hand open: the brawl rig's upper arm and
    forearm (gb_arms), and the fight rig's approved open hand (the rear V's, fingers spread)."""
    cv.stamp(K.despeckle(A.upper_layer(0, d, elbow)))
    cv.stamp(K.despeckle(A.forearm_layer(elbow, wrist)))
    hand = Z.G.gf_hands.hand('open', 0, (wrist[0], wrist[1] - 2.0))
    cv.stamp(hand, outline=False)
    return F.fist_centre(hand)


def toss(stage, d=4):
    """greyson_brawl_toss. 'heave': the barbell swung up from the floor (where the main set's slam
    leaves it, the plate at his left) and cocked over his left shoulder, his right fist across
    his chest round the grip, teeth gritted; 'fling': the arm whipped out to screen left, the
    hand flung open, the barbell gone (greyson_barbell_prop flies from the hand), a yell, the
    cannon swung out for balance; 'guard': the fists coming up into the guard."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=1.0)
    face, head = {'heave': ('flex', (1, 7)), 'fling': ('roar', (-2, 3)), 'guard': ('menace', (0, 7))}[stage]
    hp, fpx = gz_faces.head(face, head[0], head[1])
    cv.stamp(hp, outline=False)
    anc = {}
    if stage == 'heave':
        parts, cn = A.cannon_arm(d, (94.0, 70.0), (98.0, 88.0), 0.5)
        for part, ol in parts:
            cv.stamp(part, outline=ol)
        grip, plate_c = (62.0, 67.0), (97.0, 42.0)     # the bar over his shoulder, clear of his face
        plate, bar = barbell(grip, plate_c)
        cv.stamp(plate)
        cv.stamp(bar)
        parts, fc = A.fist_arm(d, (40.0, 76.0), grip)
        for part, ol in parts[:-1]:
            cv.stamp(part, outline=ol)
        cv.stamp(parts[-1][0], outline=False)
        gauntlet = (98.0, 88.0)
        anc['plate'] = Z.rnd(plate_c)
        anc['grip'] = Z.rnd(grip)
    elif stage == 'fling':
        parts, cn = A.cannon_arm(d, (95.0, 60.0), (101.0, 72.0), 0.45)
        for part, ol in parts:
            cv.stamp(part, outline=ol)
        fc = open_arm(cv, d, (18.0, 55.0), (8.0, 52.0))
        gauntlet = (101.0, 72.0)
        anc['release'] = RELEASE
    else:
        parts, cn = A.cannon_arm(d, (89.0, 74.0), (80.0, 67.0), 0.4)
        parts2, fc = A.fist_arm(d, (22.0, 71.0), (35.0, 64.0))
        for part, ol in parts2[:-1]:
            cv.stamp(part, outline=ol)
        cv.stamp(parts2[-1][0], outline=False)
        for part, ol in parts:
            cv.stamp(part, outline=ol)
        gauntlet = (80.0, 67.0)
    P.finish(cv, fpx)
    out = anchors(face, head, fc, gauntlet, cn)
    out.update(anc)
    return cv, out


# where the prop takes over on the fling frame: the bar's grip end, in his cell's texels (the
# open hand's palm), with the bar pointing straight out to screen left, the plate leading
RELEASE = (6, 50)


# ------------------------------------------------------------------------------------ the prop
PROP = (64, 32)          # the prop's cell
PROP_GRIP = (57, 16)     # the bar's grip end in the prop's cell (put it on RELEASE)
PROP_PLATE = (13, 16)    # the plate's centre in the prop's cell (the heavy end; spin about here
                         # or about PROP_CM)


def prop():
    """greyson_barbell_prop: the barbell alone, for the toss's flight. Horizontal, the plate on the
    LEFT (it leads the fling to screen left), seen three-quarters on like the held barbell."""
    cv = Canvas(PROP[0], PROP[1])
    plate, bar = barbell(PROP_GRIP, PROP_PLATE, squash=0.62, ang=90.0)
    cv.stamp(plate)
    cv.stamp(bar)
    return cv, {'grip': PROP_GRIP, 'plate': PROP_PLATE, 'cm': PROP_CM}


PROP_CM = (22, 16)       # its centre of mass: most of the weight is the plate


# ------------------------------------------------------------------------------------ the sheets

SHEETS = {
    # a loop at 0.12 s: the approved slump, swaying. The head lolls right, bobs down, lolls left;
    # the hanging arms lag behind it; the pupils roll round behind the lenses. The chin stays
    # within a texel of (56, 65), where the player's uppercut glove arrives.
    'greyson_brawl_dazed': [
        ('slump', dazed, {}),
        ('loll right', dazed, dict(head=(1, 13), face='dazed1', sh_r=2.0, sh_l=-2.0)),
        ('bob', dazed, dict(d=7, head=(0, 14), face='dazed2')),
        ('loll left', dazed, dict(head=(-1, 13), face='dazed3', sh_r=-2.0, sh_l=2.0)),
    ],
    # the player's uppercut lands on the dazed chin: SNAP (jolted bolt upright out of the crouch,
    # the head thrown up, eyes squeezed shut, mouth wide, arms flung up and out, sweat knocked
    # off him), the REEL he holds while the finisher's arc plays (knocked silly, blank eyes), and
    # the SETTLE as his weight comes back down into the crouch
    'greyson_brawl_uppercut': [
        ('snap', pose, dict(d=0, head=(0, -4), face='snap', order='left_first',
                            right=dict(elbow=(19.0, 50.0), fist=(9.0, 35.0)),
                            left=dict(elbow=(93.0, 50.0), gauntlet=(101.0, 32.0), face=0.2),
                            fx=dict(list(bead(9, -9).items()) + list(bead(-29, -8).items())))),
        ('reel', pose, dict(d=1, head=(0, 1), face='reel',
                            right=dict(elbow=(17.0, 64.0), fist=(10.0, 80.0)),
                            left=dict(elbow=(95.0, 64.0), gauntlet=(101.0, 86.0), face=0.5))),
        ('settle', pose, dict(d=4, head=(0, 7), face='dazed1',
                              right=dict(elbow=(20.0, 72.0), fist=(17.0, 84.0)),
                              left=dict(elbow=(94.0, 72.0), gauntlet=(97.0, 90.0), face=0.5))),
    ],
    # from the reel back to the guard (end_recovery, 0.4 s): he shakes it off with his eyes
    # squeezed, gathers his fists as the scowl comes back, and is in his guard: the approved
    # guard's body exactly, still scowling, so the guard loop picks up without a jump
    'greyson_brawl_recover': [
        ('shake off', pose, dict(d=3, head=(-2, 5), face='wince',
                                 right=dict(elbow=(21.0, 70.0), fist=(27.0, 81.0)),
                                 left=dict(elbow=(91.0, 70.0), gauntlet=(87.0, 85.0), face=0.5))),
        ('gather', pose, dict(d=4, head=(1, 6), face='annoyed', order='left_first',
                              right=dict(elbow=(24.0, 73.0), fist=(36.0, 67.0)),
                              left=dict(elbow=(88.0, 75.0), gauntlet=(78.0, 69.0), face=0.4))),
        ('guard', pose, dict(d=4, head=(0, 7), face='annoyed')),
    ],
    # the toss, 0.4 s at the end of the debris cut: heave, fling, guard up (then the guard loop)
    'greyson_brawl_toss': [
        ('heave', toss, dict(stage='heave')),
        ('fling', toss, dict(stage='fling')),
        ('guard up', toss, dict(stage='guard')),
    ],
    'greyson_barbell_prop': [
        ('barbell', prop, {}),
    ],
    # the KO: f0 the killing uppercut's bigger snap (held through the finisher's arc), then he
    # topples backward up the screen about his heels (0.15 s each) and lands flat on his back,
    # soles to the player; f4 is the frame Defeated holds (gz_ko has the projection)
    'greyson_brawl_ko': [
        ('big snap', pose, dict(d=0, head=(0, -6), face='ko_snap', order='left_first',
                                right=dict(elbow=(19.0, 50.0), fist=(8.0, 38.0)),
                                left=dict(elbow=(93.0, 50.0), gauntlet=(102.0, 34.0), face=0.2),
                                fx=dict(list(bead(10, -13).items()) + list(bead(-31, -12).items())
                                        + list(tooth(66, 9).items())))),
        ('tipping', KO.falling, dict(theta=25, right=((19.0, 40.0), (9.0, 24.0)),
                                     left=((93.0, 40.0), (101.0, 20.0)))),
        ('going over', KO.falling, dict(theta=55, right=((18.0, 52.0), (9.0, 40.0)),
                                        left=((94.0, 52.0), (102.0, 38.0)), boots='tip')),
        ('nearly down', KO.falling, dict(theta=74, right=((16.0, 69.0), (7.0, 60.0)),
                                         left=((96.0, 69.0), (103.0, 58.0)), head='lying',
                                         boots='sole')),
        ('down', KO.lying, {}),
    ],
}

FRAME_SIZE = {'greyson_barbell_prop': PROP}
FEET = {'greyson_barbell_prop': None}
# the lying frames carry the same keylines over half the area (the body is flattened to half its
# height), so the KO runs darker than the standing frames; still inside the cast's 15-29% band
BLACK = {'greyson_barbell_prop': None, 'greyson_brawl_ko': (0.15, 0.27)}


# for the shared exporter (art_source/greyson_brawl/gb_export.py): the dazed sheet's frame 0 must
# stay the user-approved dazed frame, pixel for pixel
APPROVED = {('greyson_brawl_dazed', 0): os.path.join(Z.APPROVED_DIR, 'greyson_brawl_dazed_f0.png')}


def build_sheet(name):
    return [(label, *fn(**kw)) for label, fn, kw in SHEETS[name]]


def check_frame0():
    """The dazed sheet's frame 0 is the approved dazed frame, pixel for pixel."""
    cv, _ = dazed()
    d = Z.pixel_diff(cv.image(), Z.approved_png('greyson_brawl_dazed_f0'))
    if d:
        raise SystemExit('greyson_brawl_dazed f0 is not the approved dazed frame: %s' % d)


if __name__ == '__main__':
    check_frame0()
    for name in SHEETS:
        print(name)
        for label, cv, anc in build_sheet(name):
            st = K.stats(cv.image())
            au = G.audit(cv.px)
            print('   %-10s black %.1f%% colours %2d bbox %s %s %s' % (
                label, 100 * st['black'], st['colours'], K.bbox(cv.px), anc,
                'clean' if not any(au.values()) else {k: len(v) for k, v in au.items() if v}))
