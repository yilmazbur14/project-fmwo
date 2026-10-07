"""The Flyby frames: Bixby in profile, flying right along the top of the ring.

  flyby_glide  frames 0-3: the wingbeat, jaws shut, no fire (entering before the rope, leaving after
               the column)
  flyby_breath frames 0-3: the same wingbeat frame for frame, jaws open, three streams going down

The wings, body, legs and tail are identical between the two clips on every frame index, so switching
clips never pops; only the jaws, tongues and fire differ.
"""
import fb_common  # noqa: F401  (puts the rig on sys.path, read-only)
import fb_body as B
import fb_head as H
import fb_fire as FF
from fb_common import Canvas

#THE WINGBEAT: the approved hover beat (rig_wings UP, MID, DOWN, MID_UP), mirrored so the wing reaches back
# from the shoulder (fb_body.approved_wing); the far wing is the same beat set back behind the body, one
# step darker. The body bobs with it as the hover's does.

FAR_WING_SHIFT = (-15, -2)
BOB = [0, -1, -2, -1]

#THE HEADS (level: the far head leads, the near head is drawn over the others; all three look down)

LEAD_X = 179            # the lead exit's column: the front of the fire, at the lead head's upper lip
LEAD_ROW = 84           # the lead exit's row at bob 0: where the fire leaves the maws (the top rope)
PITCH = 50.0
HEAD_S = 1.35
HEAD_STEP = (-13, 0)            # from one head's eye to the next one back (mid, then near)
LIP_FRONT = (19.0, 3.0)         # local: the upper lip's front under the nose, the fire's front edge
MAW = (15.0, 7.5)               # local: in the open maw, where the fire leaves (its row)


def head_eyes(bob=0):
    """Eyes (far/lead, mid, near): the lead head's lip front column on LEAD_X, its maw row on LEAD_ROW."""
    xf0 = H.HX(0, 0, PITCH, HEAD_S)
    lx, _ = xf0.p(*LIP_FRONT)
    _, my = xf0.p(*MAW)
    ex = LEAD_X - lx
    ey = LEAD_ROW - my + bob
    return [(ex + i * HEAD_STEP[0], ey + i * HEAD_STEP[1]) for i in range(3)]


def head_exit(eye):
    xf = H.HX(eye[0], eye[1], PITCH, HEAD_S)
    lx, _ = xf.p(*LIP_FRONT)
    _, my = xf.p(*MAW)
    return (int(round(lx)), int(round(my)))


BODY_K = 0.76           # the body's scale against the heads (the approved beast is all heads)
BODY_PIVOT = (126, 72)  # the neck base, in design units: the body shrinks toward it
BODY_AT = (114, 67)     # where the neck base sits in the frame
WING_K = 0.80           # the approved wings, a little smaller for the flight
WING_SHOULDER = (92, 68)  # where the wing roots, in design units


def body_xf(bob=0):
    return B.Body(k=BODY_K, pivot=BODY_PIVOT,
                  offset=(BODY_AT[0] - BODY_PIVOT[0], BODY_AT[1] - BODY_PIVOT[1]), bob=bob)


def build(i, breath=False, fire_t=None, jaw=None, glow=False):
    """Frame i of the glide (breath=False) or the breath. Returns (canvas, info). jaw overrides how far
    the jaws are open (an in-between for the preview GIF; no fire unless breath)."""
    bob = BOB[i]
    T = body_xf(bob)
    cv = Canvas()
    sh = T.p(WING_SHOULDER)
    near_wing = B.approved_wing(i, sh, WING_K)
    far_wing = B.approved_wing(i, (sh[0] + FAR_WING_SHIFT[0], sh[1] + FAR_WING_SHIFT[1]), WING_K)
    for p in far_wing:
        cv.stamp(B.darker(p))
    Tf = body_xf(bob - 3)                    # the far legs, a little higher behind the body
    for p in B.hind_leg(Tf, (52, 92), (36, 104), (20, 106), (10, 105)):
        cv.stamp(B.darker(p))
    for p in B.front_leg(Tf, (118, 96), (110, 110), (96, 108), (87, 104)):
        cv.stamp(B.darker(p))
    for p in B.tail(T, [(30, 74), (19, 70), (10, 66), (4, 59), (3, 52)], (4, 53)):
        cv.stamp(p)
    cv.stamp(B.torso(T))
    for p in B.hind_leg(T, (48, 94), (32, 108), (15, 111), (5, 111)):
        cv.stamp(p)
    cv.stamp(B.mane(T))
    for p in B.front_leg(T, (114, 98), (106, 114), (91, 113), (81, 110)):
        cv.stamp(p)
    for p in near_wing:
        cv.stamp(p)
    eyes = head_eyes(bob)
    exits = []
    head_mask = set()
    for idx in (0, 1, 2):
        xf = H.HX(eyes[idx][0], eyes[idx][1], PITCH, HEAD_S)
        nj = xf.p(-14, 5)
        base = T.p((118 + 3 * idx, 70 - 2 * idx))
        cv.stamp(B.neck(base, nj, 8.5, 7.5, rim=(idx == 2)))
        before = dict(cv.px)
        if idx == 1:
            # Liam's headband tails, off the knot under the middle head's ear, streaming back and up
            kx, ky = xf.p(*H.KNOT)
            w = 1 if i % 2 else -1
            path = [(kx - 6, ky - 3 + w), (kx - 13, ky - 5), (kx - 20, ky - 5 - w), (kx - 27, ky - 7)]
            for tl in H.headband_tails(xf, path):
                cv.stamp(tl)
        H.build(cv, xf, open_deg=(24.0 if breath else 0.0) if jaw is None else jaw, fire=breath or glow,
                with_headband=(idx == 1),
                dark=(idx == 0))
        head_mask |= {q for q, k in cv.px.items() if before.get(q) != k}
        exits.append(head_exit(eyes[idx]))
    fire = {}
    if breath:
        t = i if fire_t is None else fire_t
        fire = FF.streams(exits, LEAD_X, exits[0][1], t)
        for q, k in fire.items():
            cv.px[q] = k
    return cv, dict(exits=exits, origins=eyes, fire=set(fire), head_mask=head_mask)
