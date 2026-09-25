"""Jordan's juggle: the twelve frames (Mason's order, the contract's layout).

    0-1   HIT     the uppercut lands under his beard; he is knocked up off the mat
    2-6   TUMBLE  2 the apex hang, then 3-6 one full turn, a quarter a frame
    7-9   CRASH   flat on his back, the bounce, the settle
    10-11 DOWN    out cold on the mat, breathing

WHO HE IS IN THE AIR. The chase-edition box is his whole identity, so he never lets go of it. As
the blow lands he thrusts it up out of harm's way (the taunt's arm, the box held high) while his
head snaps back and his mouth drops open. At the top of the arc there is one beat of "uh oh" and
he hauls it down into a hug, and he goes round the whole loop curled over it, eyes screwed shut. He
lands flat on his back still hugging it, bounces, and lies there out cold, swirl-eyed, the box safe
on his chest, catching the light.

HE GOES OVER BACKWARDS. He faces screen-right in three-quarter view, so an uppercut to the chin
flips him head over heels backwards: the turn is counter-clockwise on his sheet (negative theta),
and he lands with his head to the left. When the game flips him to face left, the flip is still a
backflip, away from the fist.

Every frame is Jordan built upright in the rig's BUILD coordinates (jj_fig), lit for the turn it
will get (jj_light), then turned into the 192x144 juggle frame by jj_rot: exactly for the quarter
turns (the loop's -90, -180, -270 and every mat frame), by RotSprite for the launch's lean, the
apex and the loop's last frame.
"""
import jj_base as J
import jj_faces as FC
import jj_fig as F
import jj_light as L
import jj_parts as P
import jj_rot as R

# The pivot, BUILD: the centroid of his tumble pose (hugging the box, knees tucked), measured at
# (54.6, 51.9) on v2's thin body with the quiff knocked flat (v1's was (54.1, 52.4); v2 with the
# standing crest (54.7, 51.0)) and taken to the whole texel corner so the quarter turns stay exact.
# Turning about it, his middle stays put on every tumble frame (within half a texel) instead of
# orbiting the camera point.
PL = (55, 52)
# Frames placed by a landing point rather than re-centred on the pivot keep their places when it
# moves: their landing points below are the 09-24 ones carried over from the pivot (55, 51).
PL_MOVE = (PL[0] - 55, PL[1] - 51)
# Where the pivot hangs on the airborne frames: low, so the art rises only ~8 texels from the ground
# frame (Mason's rises ~10); the code does the lifting.
AIR = (96, 92)


class Frame:
    """One frame's spec: the figure, its turn, and where it lands (see mj_poses.Frame for Matt's)."""

    def __init__(self, name, fig, theta=0.0, pf=None, ground=False, hold=0.07, lift=0, seat=None,
                 flatten=1.0):
        self.name, self.fig, self.theta = name, fig, theta
        self.pf = pf or AIR
        self.ground = ground
        self.hold = hold
        self.lift = lift
        self.seat = seat
        self.flatten = flatten


def _turned(fr):
    cv = F.build(fr.fig, fr.theta)
    px = F.close_holes(cv.px, fr.fig.fx)
    if fr.theta % 360 == 0 and fr.ground:
        dx, dy = J.BUILD_TO_FRAME
        return J.moved(px, dx, dy - fr.lift), J.moved(cv.owner, dx, dy - fr.lift), True
    out, own = R.turn(px, cv.owner, fr.theta, PL, fr.pf)
    return out, own, False


def render(fr):
    out, own, placed = _turned(fr)
    if fr.ground and not placed:
        if fr.seat is not None:
            s_out, _, _ = _turned(fr.seat)
            d = J.FEET[1] - fr.seat.lift - J.bbox(s_out)[3]
        else:
            d = J.FEET[1] - fr.lift - J.bbox(out)[3]
        out, own = J.moved(out, 0, d), J.moved(own, 0, d)
        if fr.flatten < 1.0:
            out, own, _ = R.squash_rows(out, own, fr.flatten)
    return out, own


def fig(**kw):
    return F.JFig(**kw)


def head(name, tilt=0, dx=3, dy=2):
    return (FC.head(name), tilt, dx, dy)


def hugged(theta, box_at=P.HUG_BOX):
    """back and front callables for the hug, lit for theta."""
    def back(light):
        return P.hug(light, theta, box_at)[0]

    def front(light):
        return P.hug(light, theta, box_at)[1]
    return back, front


# ------------------------------------------------------------------------------ 0-1 the hit
def hit_contact():
    """The fist lands under his beard. His head snaps back, the jaw drops open on the blow, the quiff
    is knocked flat, the near arm flies off his hip; and the box goes straight up out of harm's way.
    His heels are still on the mat, legs rocked back."""
    th = 0

    def back(light):
        return P.far_arm_up(-3, light)

    def front(light):
        return P.near_arm_flung(0, light) + P.box_high(-3, light, th)
    f = fig(legs=P.leaning(3), back=back, body=(-3, -1), head=head('OW', -12, 2, 1), front=front)
    return Frame('hit_contact', f, th, ground=True, hold=0.06)


def hit_lift():
    """Off the mat and tipping back over, the box still held up high, the legs let go."""
    th = -15

    # the box a texel lower than the 09-24 -4: held where the shipped taunt holds it (2 texels
    # right) and turned -15 degrees, its top corner would otherwise rise past row 40
    def back(light):
        return P.far_arm_up(-3, light)

    def front(light):
        return P.near_arm_flung(-1, light) + P.box_high(-3, light, th)
    f = fig(legs=P.dangling(), back=back, body=(-2, 0), head=head('OW', -10, 2, 1), front=front)
    # (97, 96): v1's (96, 96) carried over to v2's pivot (55, 51) as (97, 95), and that to (55, 52),
    # so the lift lands where it did
    return Frame('hit_lift', f, th, pf=(97, 96), hold=0.08)


# ------------------------------------------------------------------------------ 2-6 the tumble
def hang():
    """The apex: "uh oh". Wall-eyed, jaw hanging, legs let go: and the box is already coming down
    into a hug."""
    th = -40
    back, front = hugged(th)
    f = fig(legs=P.dangling(), back=back, head=head('daze'), front=front)
    return Frame('hang', f, th, hold=0.14)


def tumble(th, face):
    back, front = hugged(th)
    f = fig(legs=P.tucked(), back=back, head=head(face), front=front)
    return Frame('tumble_%d' % -th, f, th, hold=0.07)


def tumble_a():
    return tumble(-90, 'AAH')


def tumble_b():
    return tumble(-180, 'PAIN')


def tumble_c():
    return tumble(-270, 'AAH')


def tumble_d():
    return tumble(-340, 'PAIN')


# ------------------------------------------------------------------------------ 7-11 on the mat
def crash():
    """Flat on his back, still hugging the box; the whole of him pancakes."""
    th = -90
    back, front = hugged(th)
    f = fig(legs=P.standing, back=back, head=head('PAIN'), front=front)
    return Frame('crash', f, th, pf=(96 + PL_MOVE[1], 116), ground=True, hold=0.06, flatten=0.86)


def bounce():
    th = -90
    back, front = hugged(th)
    f = fig(legs=P.dangling(), back=back, head=head('daze'), front=front)
    return Frame('bounce', f, th, pf=(96 + PL_MOVE[1], 112), ground=True, hold=0.08, lift=5)


def settle():
    th = -90
    back, front = hugged(th)
    f = fig(legs=P.standing, back=back, head=head('KO'), front=front)
    return Frame('settle', f, th, pf=(96 + PL_MOVE[1], 116), ground=True, hold=0.12, flatten=0.93)


def down(breath=0):
    """Out cold, swirl-eyed, jaw hanging, and still hugging the box: it rides on his chest, which is
    the upper side of him lying head-left (turned -90). Frame 11 is the breath: the box and the arms
    round it rise a texel while the side of him on the canvas stays put. Frame 10's box catches a
    glint (jj_fx): not a scratch on it."""
    th = -90
    back, front = hugged(th, box_at=(P.HUG_BOX[0] + breath, P.HUG_BOX[1]))
    f = fig(legs=P.standing, back=back, head=head('KO'), front=front)
    return Frame('down_%d' % breath, f, th, pf=(96 + PL_MOVE[1], 116), ground=True, hold=0.40,
                 seat=down(0) if breath else None)


FRAMES = [hit_contact, hit_lift, hang, tumble_a, tumble_b, tumble_c, tumble_d,
          crash, bounce, settle, lambda: down(0), lambda: down(1)]
