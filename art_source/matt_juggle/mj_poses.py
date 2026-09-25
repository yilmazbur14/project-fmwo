"""Matt's juggle: the twelve frames (Mason's order, the contract's layout).

    0-1   HIT     the uppercut lands under his chin; he is knocked up off the mat
    2-6   TUMBLE  2 the apex hang, then 3-6 one full clockwise turn, a quarter a frame
    7-9   CRASH   flat on his back, the bounce, the settle
    10-11 DOWN    out cold on the mat, breathing

Every frame is Matt built upright in his own LOCAL frame by mj_fig (the approved rig's parts, the
light turned for the body's final angle), then turned into the 192x144 juggle frame by mj_rot.
The tumble loop and the mat frames are whole quarter turns, so they are the rig's own pixels
moved; only the launch's lean and the apex hang are turned by RotSprite.

WHO HE IS IN THE AIR. Matt is the loud one: the Exploud. So the uppercut knocks his mouth open
into the approved roar and it stays open, screaming, all the way round the loop; his five-spike
crest flares out stiff on the hit and drags behind the spin. At the apex there is one beat of
silence (eyes popped, a little "o") before he goes over. On the mat he is out cold with the roar
still hanging open, his eyes swirling, and his tongue lolling out onto the canvas.
"""
import math

import mj_base as J
from mj_base import G, PZ
import mj_faces as FC
import mj_fig as MF
import mj_parts as P
import mj_rot as R

PL = (48, 50)            # the pivot, LOCAL: the centroid of his tumble poses, measured at (48.6, 49.8)
AIR = (96, 88)           # where the pivot hangs on the airborne frames: low, so the art rises
                         # only ~10 texels from the ground frame (as Mason's does); the code lifts him

# ------------------------------------------------------------------------------ crests
SP_FLARE = [(0, 8, 31, 6.4, 2.0, 0.0), (-44, 8, 32, 6.4, 2.0, 0.0), (-92, 9, 31, 7.2, 2.4, 0.0)]
SP_SPIN = [(0, 8, 28, 6.3, 1.95, 0.0), (-36, 8, 29, 6.3, 1.95, 1.0), (-76, 9, 29, 7.1, 2.3, 1.5)]
SP_SPLAT = [(0, 8, 25, 6.0, 1.9, 1.0), (-38, 8, 25, 6.0, 1.9, 3.0), (-80, 9, 25, 6.8, 2.1, 4.0)]
SP_KO = [(0, 8, 25, 6.0, 1.9, 2.0), (-37, 8, 24, 6.0, 1.9, 4.0), (-76, 9, 25, 6.8, 2.1, 5.5)]


class Frame:
    """One frame's spec: the figure, its turn, and where it lands.

    ground: stand the result on the mat (lowest drawn row on the feet row), `lift` rows above it.
    squash: a FRAME-space (sx, sy) about the pivot after the turn: a body pancaking on the mat.
    """

    def __init__(self, name, fig, theta=0.0, pf=None, ground=False, trail=0.0, hands_baked=None,
                 hold=0.07, squash=(1.0, 1.0), lift=0, seat=None, flatten=1.0):
        self.name, self.fig, self.theta = name, fig, theta
        # flatten: on the mat, take rows out of him (mj_rot.squash_rows) down to this share of
        # his height: a crisp pancake, nothing resampled
        self.flatten = flatten
        # seat: another Frame whose grounding this one reuses, so a breath moves only the chest
        self.seat = seat
        self.pf = pf or AIR
        self.ground = ground
        self.trail = trail
        self.hands_baked = hands_baked or {}
        self.hold = hold
        self.squash = squash
        self.lift = lift


def render(fr):
    """(px, owner) in the juggle frame."""
    cv = MF.build(fr.fig, fr.theta, trail=fr.trail, hands_baked=fr.hands_baked)
    px = MF.close_pinholes(cv.px, fr.fig.fx)
    if fr.theta % 360 == 0 and fr.ground and fr.squash == (1.0, 1.0):
        dx, dy = J.LOCAL_TO_FRAME
        return J.moved(px, dx, dy - fr.lift), J.moved(cv.owner, dx, dy - fr.lift)
    if fr.squash != (1.0, 1.0):
        sx, sy = fr.squash
        out = R.rotsprite(px, fr.theta, PL, fr.pf, sx, sy)
        own = R.rotsprite_owner(cv.owner, fr.theta, PL, fr.pf, sx, sy)
    else:
        out, own = R.turn(px, cv.owner, fr.theta, PL, fr.pf)
    if fr.ground:
        # stand him on the mat: his lowest drawn row on the feet row (or where `seat` stood him)
        d = seat_offset(fr.seat) if fr.seat is not None else J.FEET[1] - fr.lift - J.bbox(out)[3]
        out, own = J.moved(out, 0, d), J.moved(own, 0, d)
        if fr.flatten < 1.0:
            out, own, _ = R.squash_rows(out, own, fr.flatten)
    return out, own


def seat_offset(fr):
    cv = MF.build(fr.fig, fr.theta, trail=fr.trail, hands_baked=fr.hands_baked)
    px = MF.close_pinholes(cv.px, fr.fig.fx)
    out, _ = R.turn(px, cv.owner, fr.theta, PL, fr.pf)
    return J.FEET[1] - fr.lift - J.bbox(out)[3]


def fig(**kw):
    return MF.JFig(**kw)


# ------------------------------------------------------------------------------ 0-1 the hit
def hit_contact():
    """The fist lands under his chin. His head is snapped up off his shoulders, the approved roar
    knocked open, eyes screwed shut, the crest flaring out stiff, and his arms fly out wide with
    the fingers splayed. His feet are still on the mat."""
    arms, baked = P.arms(P.arm(0, 200, 215, 'open'), P.arm(1, 340, 325, 'open'))
    f = fig(face=(FC.HIT, FC.X0, FC.Y0), collar=False, neck=True, spikes=SP_FLARE,
            head=(0, -5), body=(0, -1), arms=arms,
            legs=P.legs((1, 0, 0.4), (-1, 0, -0.4)))
    return Frame('hit_contact', f, 0, ground=True, hands_baked=baked, hold=0.06)


def hit_lift():
    """A beat later he is off the mat and tipping back, the jaw still hanging, knees buckled and
    his feet trailing under him, arms dragged down by the lift."""
    arms, baked = P.arms(P.arm(0, 130, 105, 'open'), P.arm(1, 55, 80, 'open'))
    f = fig(face=(FC.HIT, FC.X0, FC.Y0), collar=False, neck=True, spikes=SP_FLARE, tilt=-6,
            head=(0, -4), arms=arms, legs=P.legs((0, -5, 0.5), (3, -2, 1.0)))
    return Frame('hit_lift', f, 20, pf=(96, 92), trail=1.5, hands_baked=baked, hold=0.08)


# ------------------------------------------------------------------------------ 2-6 the tumble
def hang():
    """The apex: one beat of silence. Eyes popped, a little "o", the crest standing on end; the
    low arm hangs plumb and the high one has flopped back past his head; the legs dangle."""
    arms, baked = P.arms(P.arm(0, 225, 185, 'open'), P.arm(1, 45, 60, 'open'))
    f = fig(face=(FC.GAPE, FC.X0, FC.Y0), spikes=PZ.SP_PERK, arms=arms,
            legs=P.legs((3, -1, 0.6), (5, 0, 1.0)))
    return Frame('hang', f, 50, pf=AIR, hands_baked=baked, hold=0.14)


# The turn is clockwise, so everything loose lags it counter-clockwise: the arms trail
# (screen-left arm swept down past the horizontal, screen-right arm swept up), the feet trail to
# the right, and the crest leans back against the spin. The same lag on every quarter keeps the
# spin reading one way; the elbows and knees vary so the loop is not a rigid pinwheel.
def tumble(th, face, arm_l, arm_r, leg_l, leg_r):
    arms, baked = P.arms(P.arm(0, *arm_l), P.arm(1, *arm_r))
    f = fig(face=(face, FC.X0, FC.Y0), collar=False, neck=True, spikes=SP_SPIN, tilt=-9,
            arms=arms, legs=P.legs(leg_l, leg_r))
    return Frame('tumble_%d' % th, f, th, pf=AIR, trail=2.0, hands_baked=baked, hold=0.07)


def tumble_a():
    return tumble(90, FC.YELL, (170, 150, 'open'), (320, 300, 'open'), (3, -2, 0.8), (7, -4, 1.4))


def tumble_b():
    return tumble(180, FC.YELL_BIG, (165, 135, 'open'), (315, 285, 'open'), (4, -5, 0.8), (6, -1, 1.2))


def tumble_c():
    return tumble(270, FC.YELL, (172, 150, 'open'), (325, 300, 'open'), (2, -3, 0.8), (7, -2, 1.4))


def tumble_d():
    """Coming back up toward the stall. Not a whole quarter: dead upright, with his feet under him,
    a man in the air reads as standing, so this one is 20 degrees short of upright (RotSprite),
    knees tucked and swept back."""
    return tumble(340, FC.YELL_BIG, (185, 230, 'open'), (315, 275, 'open'), (6, -8, 1.2), (9, -5, 1.8))


# ------------------------------------------------------------------------------ 7-9 the crash
# On the mat he lies on his back with his head to the right (turned 90): LOCAL left is the side
# of him away from the camera (up on screen), LOCAL right is the side on the canvas (down).
def crash():
    """Back first into the mat and the whole of him pancakes: squashed flat and spread, the top
    arm punched up out of the mass, the one underneath slapped along the canvas, legs splayed,
    the crest splattered, an "OOF"."""
    arms, baked = P.arms(P.arm(0, 200, 235, 'open'), P.arm(1, 330, 300, 'open'))
    f = fig(face=(FC.GRIT, FC.X0, FC.Y0), spikes=SP_SPLAT, arms=arms,
            legs=P.legs((-4, -2, -1.0), (4, -1, 1.0)))
    return Frame('crash', f, 90, pf=(96, 116), ground=True, hands_baked=baked, hold=0.06,
                 flatten=0.84)


def bounce():
    """The bounce: the whole of him pops a hand's width off the mat, every limb flopping up."""
    arms, baked = P.arms(P.arm(0, 215, 245, 'open'), P.arm(1, 310, 285, 'open'))
    f = fig(face=(FC.DAZED, FC.X0, FC.Y0), collar=False, neck=True, spikes=SP_SPLAT,
            arms=arms, legs=P.legs((-5, -4, -1.0), (2, -2, 0.5)))
    return Frame('bounce', f, 90, pf=(96, 112), ground=True, hands_baked=baked, hold=0.08,
                 lift=6)


def settle():
    """Down again, flatter than he landed, spread out, and the lights go out."""
    arms, baked = P.arms(P.arm(0, 220, 265, 'open'), P.arm(1, 320, 275, 'open'))
    f = fig(face=(FC.KO, FC.X0, FC.Y0), collar=False, spikes=SP_KO, arms=arms,
            legs=P.legs((-4, -1, -1.0), (4, 0, 1.0)))
    return Frame('settle', f, 90, pf=(96, 118), ground=True, hands_baked=baked, hold=0.12,
                 flatten=0.92)


# ------------------------------------------------------------------------------ 10-11 down
def down(breath=0):
    """Out cold: arms flopped up beside his head, the roar hanging open, swirl eyes, tongue out on
    the mat. Frame 11 is the same on a breath: the upper side of his chest (and the arm on it) lets
    out a texel while the side on the canvas stays put."""
    arms, baked = P.arms(P.arm(0, 222, 268, 'open', shift=(-breath, 0)), P.arm(1, 318, 272, 'open'))
    tongue = (FC.ko_tongue((0, 0)), False, 'front')
    rest = J.matt.Pose(False)
    f = fig(face=(FC.KO, FC.X0, FC.Y0), collar=False, spikes=SP_KO, arms=arms,
            torso_fn=lambda: P.breath_torso(rest, breath), hem_fn=lambda: P.breath_hem(rest, breath),
            legs=P.legs((-4, -1, -1.0), (4, 0, 1.0)), parts=[tongue])
    return Frame('down_%d' % breath, f, 90, pf=(96, 120), ground=True, hands_baked=baked,
                 hold=0.40, seat=down(0) if breath else None)


FRAMES = [hit_contact, hit_lift, hang, tumble_a, tumble_b, tumble_c, tumble_d,
          crash, bounce, settle, lambda: down(0), lambda: down(1)]
