"""Greyson's cannon-arm takeover sheets (PLAN.md sections 6 and 7), from the moment the cannon is on
until the barbell comes out: approved rig (read-only, via gf_base), 112x112, feet at (56, 111).
The cannon is gf_cannon's worn gauntlet on his LEFT arm (screen right), exactly as in the approved
fight idle; no barbell yet (it comes out in greyson_barbell_pull).

  greyson_walk_cannon (6)  gf_walk's stomp with the cannon arm swinging, the smug face: he walks
                           back to the top of the arena
  greyson_talk_cannon (4)  smug, shut then open, in two poses:
                             0-1 stance  the cannon hanging, his right fist at his side
                             2-3 show    fight pose B, the cannon flexed up beside his head
                           ("What Computah didn't know was that this cannon is fueled by the
                           crowd's energy..." / "Pal, you won't like what comes next.")
  greyson_roar (4)         0 inhale (chest up, eyes shut, lips pressed); 1-2 the ROAR, both arms
                           thrown up in a V, his fist on one side and the cannon thrust straight
                           up on the other (the approved spirit raise's cannon arm), jaw dropped;
                           2 is 1 jolted for the shake; 3 settle into the menacing grin
  greyson_barbell_pull (3) 0 the draw: his right fist over his shoulder on the bar's end, the rest
                           of the bar behind him; 1 the swing: the barbell comes over, the plate
                           high by his head; 2 the rest: the approved fight idle, exactly

    python -B gf_cannonset.py      # prints each frame's numbers and audit; writes nothing
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
import gf_walk  # noqa: E402
import gf_cannon  # noqa: E402
import gf_attach  # noqa: E402
import gf_arms  # noqa: E402
import gf_limb  # noqa: E402
import gf_barbell  # noqa: E402
import gf_faces  # noqa: E402
import gf_tear  # noqa: E402
import gf_faces_tk as FT  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face = B.K, B.gr_fig, B.gr_arms, B.gr_hands, B.gr_face
mp = gf_fig.mp


def cannon_left():
    """His left arm as the fight idle wears the cannon: the approved upper arm, the gauntlet
    hanging from the elbow, muzzle down and a little out."""
    upper = gf_fig.arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 1,
                             keep=('delt', 'upper', 'biceps'))
    gun = gf_cannon.cannon(mp(gf_walk.CANNON_ELBOW), mp(gf_walk.CANNON_MUZZLE),
                           face=gf_walk.CANNON_FACE)
    return K.despeckle(upper), gun


FT.FACES.setdefault('menace', gf_faces.MENACE)       # the approved fight idle's face, by name


def stance(face, right=None, extras=None, lat_flare=0.5):
    """The cannon stance: the approved legs, trunk and trunks; his right arm (`right`: a (part,
    fist anchor) pair, the approved idle arm when None); the cannon arm; a takeover face."""
    cv = K.Canvas()
    gf_fig.front_base(cv, lat_flare=lat_flare)
    if right is None:
        right = (K.despeckle(gr_arms.arm('idle', 0)), (25.0, 84.5))
    part, fist = right
    cv.stamp(part)
    upper, gun = cannon_left()
    cv.stamp(upper)
    cv.stamp(gun)
    cv.stamp(gr_hands.fist('idle', 0, fist), outline=False)
    head = FT.head(face)
    if extras:
        head.update(extras)
    cv.stamp(head, outline=False)
    return gf_fig.finish(cv, FT.face(face))


# ------------------------------------------------------------------------------------ walk

def walk_cannon(i):
    cv, info = gf_walk.frame(i, head=(FT.head('smug'), FT.face('smug')), cannon=True)
    mx, my = FT.MOUTH['smug']
    info['mouth'] = (mx, my + info['drop'])
    return cv, info


# ------------------------------------------------------------------------------------ talk

def show(face):
    """Fight pose B's body (the cannon flexed up), with a takeover face."""
    gf_attach.FACE_ROWS.setdefault(face, FT.FACES[face])
    return gf_attach.worn(face, gf_attach.UPRIGHT)


TALK = [('stance', 'smug'), ('stance open', 'smug_open'), ('show', 'smug'), ('show open', 'smug_open')]


def talk_cannon(i):
    name, face = TALK[i]
    cv = stance(face) if name.startswith('stance') else show(face)
    return cv, {'name': name, 'face': face, 'mouth': FT.MOUTH[face]}


# ------------------------------------------------------------------------------------ roar

V_ANGLE = 40.0                     # the right arm's V, degrees out from straight up


def v_arm(jolt=0.0):
    """His right arm thrown up and out in the V: (part, fist anchor)."""
    a = math.radians(V_ANGLE + jolt)
    d = (-math.sin(a), -math.cos(a))
    S = (30.0, 55.0)
    E = (S[0] + d[0] * gf_tear.UPPER_LEN, S[1] + d[1] * gf_tear.UPPER_LEN)
    W = (E[0] + d[0] * gf_tear.LOWER_LEN, E[1] + d[1] * gf_tear.LOWER_LEN)
    return gf_limb.arm(S, E, W, 0), (W[0], W[1] + 1.0)


def face_px(face):
    rows = FT.FACES.get(face) or gf_faces.FACES[face]
    out = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FT.FX0 + c, FT.FY0 + r)] = ch
    return out


def roaring(face, jolt=0.0):
    """Both arms thrown up in a V: his fist on one side, the cannon on the other, thrust straight
    up as in the approved spirit raise."""
    cv = K.Canvas()
    gf_fig.front_base(cv, lat_flare=1.5)
    arm, fist = v_arm(jolt)
    cv.stamp(arm)
    cv.stamp(K.despeckle(gf_fig.arm_layer(gf_arms.RAISED, gf_arms.RAISED_FORMS,
                                          gf_arms.RAISED_SPEC, 1)))
    ex, ey = gf_arms.RAISED_ELBOW
    cv.stamp(gf_cannon.cannon(mp((ex, ey + 1.5)), mp((ex + 0.4 - jolt * 0.25, 7.0)), face=0.5))
    cv.stamp(gr_hands.fist('flex', 0, fist), outline=False)
    head = gr_face.mane()
    fp = face_px(face)
    head.update(fp)
    cv.stamp(head, outline=False)
    return gf_fig.finish(cv, fp)


ROAR = [('inhale', 'inhale'), ('roar', 'roar'), ('roar', 'roar'), ('settle', 'menace')]


def roar(i):
    name, face = ROAR[i]
    if name == 'inhale':
        cv = stance('inhale', lat_flare=1.5)
    elif name == 'roar':
        cv = roaring('roar', jolt=0.0 if i == 1 else 4.0)
    else:
        cv = stance('menace')
    info = {'name': name, 'face': face}
    if name == 'roar':
        info['mouth'] = (56, 50)
    return cv, info


# ------------------------------------------------------------------------------------ barbell pull

DRAW_FIST = (27.0, 41.0)            # the 'flex' fist's anchor round the bar's end, over his shoulder
DRAW_ARM = ((30.0, 55.0), (17.0, 45.0), (27.0, 39.5))    # shoulder, elbow, wrist
SWING_PLATE = (24.7, 21.4)          # the plate coming over, high by his head


def draw_frame():
    """The draw, built in its own order: legs, boots, the bar (behind the trunk), trunk, trunks,
    the raised right arm, the cannon arm, the head, then the fist round the bar's end."""
    cv = K.Canvas()
    gf_fig.front_base(cv, lat_flare=0.5)
    body = dict(cv.px)
    bar = gf_barbell.bar((26.0, 29.5), (33.5, 56.0))
    behind = {}
    for (x, y) in bar:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in bar:
                behind[q] = 'k'
    behind.update(bar)
    cv.px = dict(behind)
    cv.px.update(body)
    S, E, W = DRAW_ARM
    cv.stamp(gf_limb.arm(S, E, W, 0))
    upper, gun = cannon_left()
    cv.stamp(upper)
    cv.stamp(gun)
    cv.stamp(gf_faces.head('menace'), outline=False)
    fist = gr_hands.fist('flex', 0, DRAW_FIST)
    cv.stamp(fist, outline=False)
    return gf_fig.finish(cv, gf_faces.face('menace')), gf_tear.centre(fist)


def pull(i):
    if i == 0:
        cv, hand = draw_frame()
        return cv, {'name': 'draw', 'hand': hand}
    if i == 1:
        # the swing: the carry arm (as the fight idle), the bar coming over with the plate high
        cv = K.Canvas()
        gf_fig.front_base(cv, lat_flare=0.5)
        cv.stamp(K.despeckle(gf_fig.arm_layer(gf_arms.CARRY, gf_arms.CARRY_FORMS,
                                              gf_arms.CARRY_SPEC, 0)))
        upper, gun = cannon_left()
        cv.stamp(upper)
        cv.stamp(gun)
        cv.stamp(gf_faces.head('menace'), outline=False)
        cv.stamp(gf_barbell.plate(SWING_PLATE))
        cv.stamp(gf_barbell.bar(SWING_PLATE, gf_fig.BAR_GRIP))
        cv.stamp(gr_hands.fist('idle', 0, (41.0, 55.0)), outline=False)
        gf_fig.finish(cv, gf_faces.face('menace'))
        return cv, {'name': 'swing', 'plate': SWING_PLATE, 'hand': gf_fig.BAR_GRIP}
    cv = gf_fig.idle()               # the approved fight idle, exactly
    return cv, {'name': 'rest', 'plate': gf_fig.PLATE_C, 'hand': gf_fig.BAR_GRIP}


if __name__ == '__main__':
    for sheet, fn, n in (('greyson_walk_cannon', walk_cannon, 6), ('greyson_talk_cannon', talk_cannon, 4),
                         ('greyson_roar', roar, 4), ('greyson_barbell_pull', pull, 3)):
        for i in range(n):
            cv, info = fn(i)
            a = B.audit(cv.px)
            print(sheet, i, info.get('name'), K.stats(cv.image()), 'bbox', K.bbox(cv.px),
                  'audit', {k: len(v) for k, v in a.items()})
