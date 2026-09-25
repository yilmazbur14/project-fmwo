"""Captain Burak's juggle: 12 frames of 192x144 in Mason's order.

The read is the COCKY MAN UNDONE. The whole approved sprite is poise: a smirk, a cocked brow, a
cutlass lounging on his shoulder. The uppercut takes all of it at once, in the order a vain man
would mind most:

  0 contact   the smirk wiped off: eyes screwed shut, a howl; the tricorn pops off his head and his
              grip on both weapons goes. Feet still on the mat (a ground frame).
  1 lift      airborne and turning, stunned white eyes; the hat sails off the top with its red
              ribbons, the cutlass and pistol spin out of the frame. His own hair shows at last.
  2 hang      the apex: limp, surprised, a little "o". Held long, so it reads as a stall.
  3-6 tumble  one clockwise turn in quarter turns (exact, so the face stays crisp), dizzy swirl eyes,
              limbs dragged behind the spin. 2-6 loop.
  7 impact    flat on his back on the mat, squashed, grimacing; dust thrown sideways.
  8 bounce    the rebound; the hat and the cutlass coming back down out of the sky.
  9 settle    flat again; the cutlass lands point-down in the mat beside him, THUNK.
  10-11 down  out cold, X eyes, tongue out, his own tricorn landed over his hair and brow, dizzy stars.
              The breathing loop: his chest rises on 11.

Air frames keep his middle on TUMBLE_AT; ground frames stand his feet / lay his back on FEET's row.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jkit as J  # noqa: E402

PL = J.PIVOT_LOCAL
GROUND_PF = (PL[0] + J.GROUND_SHIFT[0], PL[1] + J.GROUND_SHIFT[1])     # upright, feet on the mat


def ang_pt(p, deg, r):
    a = math.radians(deg)
    return (p[0] + math.cos(a) * r, p[1] + math.sin(a) * r)


class Body:
    """The core placed in a frame, plus the joints its limbs hang from."""

    def __init__(self, cv, expr, angle, pf, sx=1.0, sy=1.0, head_dy=0, flare=False):
        self.cv, self.angle, self.pf, self.sx, self.sy = cv, angle, pf, sx, sy
        self.px, self.own = J.core(expr, head_dy=head_dy, flare=flare)
        self.head_dy = head_dy

    def pt(self, local):
        return J.body_point(local, self.angle, PL, self.pf, self.sx, self.sy)

    def boots(self, left, right):
        """left/right: (bearing, shaft length, foot bearing, foot length), bearings in the FRAME."""
        for knee, spec in ((J.KNEE_L, left), (J.KNEE_R, right)):
            if spec is None:
                continue
            k = self.pt(knee)
            a = ang_pt(k, spec[0], spec[1])
            t = ang_pt(a, spec[2], spec[3])
            J.boot(self.cv, k, a, t)

    def draw_core(self):
        P, O = J.placed(self.px, self.own, self.angle, PL, self.pf, self.sx, self.sy)
        self.cv.stamp(P, outline=False, owner='core')

    def hat_on_head(self, pull=0.0, tilt=0.0):
        """His tricorn sitting on his head in HIS frame (pulled down over his face by `pull` px,
        tipped by `tilt` degrees about its crown), carried through the body's own turn."""
        at = self.pt((48.0, 9.0 + pull + self.head_dy))
        J.hat_placed(self.cv, self.angle + tilt, at)

    def arms(self, left, right, hands=(None, None)):
        """left/right: (upper bearing, upper length, fore bearing, fore length), frame bearings."""
        for sh, spec, hand in ((J.SHOULDER_L, left, hands[0]), (J.SHOULDER_R, right, hands[1])):
            if spec is None:
                continue
            s = self.pt(sh)
            e = ang_pt(s, spec[0], spec[1])
            h = ang_pt(e, spec[2], spec[3])
            J.arm(self.cv, s, e, h, hand)


# ------------------------------------------------------------------ 0-1: the hit
def launch_contact():
    cv = J.frame_canvas()
    b = Body(cv, 'hit', 0, GROUND_PF, head_dy=-3)
    # up on his toes as the fist lands, heels off the mat, toes on the mat's row
    b.boots((108, 9.5, 170, 7.5), (72, 9.5, 10, 7.5))
    b.draw_core()
    # arms flung out and up, the grip gone: the cutlass and the pistol slipping out of his hands
    b.arms((215, 10.5, 235, 9.5), (-35, 10.5, -55, 9.5))
    J.cutlass(cv, (58, 72), (33, 58), bow=-2.0)
    J.pistol(cv, (137, 76), (0.9, -0.45), (-0.3, 1.0), barrel_len=9.0, grip_len=4.0, bell_len=5.0,
             r_bar=2.0, r_bell=4.4, mouth_tip=0.5)
    # the tricorn popped straight up off his hair
    J.hat_placed(cv, -14, (98, 38))
    # the uppercut connecting under his jaw: impact lines bursting out round his head
    J.lines(cv, [(78, 96, 70, 99), (114, 96, 122, 99), (80, 86, 72, 82), (112, 86, 120, 82),
                 (86, 106, 81, 112), (106, 106, 111, 112)])
    for (x, y, r) in ((70, 139, 3), (122, 139, 3), (61, 140, 2), (131, 140, 2)):
        J.puff(cv, x, y, r)
    J.drop(cv, 118, 60)
    J.drop(cv, 74, 62)
    return J.finish(cv)


def launch_lift():
    cv = J.frame_canvas()
    b = Body(cv, 'stunned', 22, J.TUMBLE_AT)
    b.boots((118, 12.5, 150, 7.0), (86, 12.5, 40, 7.0))
    b.draw_core()
    b.arms((200, 10.5, 250, 9.5), (-20, 10.5, -70, 9.5))
    # the hat sailing off the top of the frame, ribbons streaming; the weapons spinning away
    J.hat_placed(cv, 38, (160, 58))
    J.cutlass(cv, (40, 56), (19, 38), bow=2.0)
    J.pistol(cv, (166, 96), (0.2, 1.0), (-1.0, 0.3), barrel_len=8.0, grip_len=4.0, bell_len=4.5,
             r_bar=1.9, r_bell=4.2, mouth_tip=0.5)
    # the trail he has just left, straight up out of the mat
    J.lines(cv, [(84, 128, 84, 138), (96, 130, 96, 142), (108, 128, 108, 138)], 'W')
    J.arc(cv, 34, 52, 9, 100, 230)
    J.arc(cv, 168, 94, 9, -80, 60)
    return J.finish(cv)


# ------------------------------------------------------------------ 2-6: the tumble
def hang():
    cv = J.frame_canvas()
    b = Body(cv, 'surprised', 50, J.TUMBLE_AT)
    b.boots((110, 12.5, 140, 7.0), (70, 12.5, 100, 7.0))
    b.draw_core()
    # limp: the low arm hangs plumb, the high one flopped back over his head
    b.arms((215, 10.5, 250, 9.5), (80, 10.5, 95, 9.5))
    J.specks(cv, [(44, 46), (48, 40), (150, 42), (146, 50), (40, 112), (156, 108)])
    J.arc(cv, J.TUMBLE_AT[0], J.TUMBLE_AT[1], 56, -150, -115, ry=50)
    return J.finish(cv)


def _turn(angle, expr, arm_l, arm_r, boot_l, boot_r, arcs):
    cv = J.frame_canvas()
    b = Body(cv, expr, angle, J.TUMBLE_AT)
    b.boots(boot_l, boot_r)
    b.draw_core()
    b.arms(arm_l, arm_r)
    for (cx, cy, r, a0, a1, ry) in arcs:
        J.arc(cv, cx, cy, r, a0, a1, ry=ry)
    return J.finish(cv)


# Limbs dragged behind a clockwise spin: in his own frame the arms would stand out left (180) and right
# (0) and the boots hang down (90); each is swung back AGAINST the turn by LAG degrees, the forearms and
# feet by more, which is the secondary motion of a limp limb. Bearings are then turned with the body.
LAG_ARM, LAG_FORE, LAG_BOOT, LAG_FOOT = 38, 34, 32, 40


def _spin_limbs(angle):
    t = angle
    arm_l = (180 - LAG_ARM + t, 10.5, 180 - LAG_ARM - LAG_FORE + t, 9.5)
    arm_r = (0 - LAG_ARM + t, 10.5, 0 - LAG_ARM - LAG_FORE + t, 9.5)
    boot_l = (90 - LAG_BOOT + 6 + t, 12.5, 180 - LAG_FOOT + t, 7.0)
    boot_r = (90 - LAG_BOOT - 6 + t, 12.5, 0 - LAG_FOOT + t, 7.0)
    return arm_l, arm_r, boot_l, boot_r


def tumble_a():
    # a quarter turn on: lying across the air, head to the right
    return _turn(90, 'dizzy', *_spin_limbs(90),
                 [(J.TUMBLE_AT[0], J.TUMBLE_AT[1], 58, 100, 170, 52), (J.TUMBLE_AT[0], J.TUMBLE_AT[1], 52, -80, -20, 46)])


def tumble_b():
    # head down, turning fastest
    return _turn(180, 'dizzy', *_spin_limbs(180),
                 [(J.TUMBLE_AT[0], J.TUMBLE_AT[1], 58, 190, 262, 52), (J.TUMBLE_AT[0], J.TUMBLE_AT[1], 52, 10, 72, 46)])


def tumble_c():
    # head to the left, feet to the right
    return _turn(270, 'dizzy', *_spin_limbs(270),
                 [(J.TUMBLE_AT[0], J.TUMBLE_AT[1], 58, 280, 350, 52), (J.TUMBLE_AT[0], J.TUMBLE_AT[1], 52, 100, 160, 46)])


def tumble_d():
    # round to upright again and slowing into the next stall
    return _turn(360, 'dizzy', *_spin_limbs(360),
                 [(J.TUMBLE_AT[0], J.TUMBLE_AT[1], 58, 16, 80, 52)])


# ------------------------------------------------------------------ 7-9: the crash
LIE_ANGLE = 90                                   # on his back, head to the right


def lie_pf(lift=0, sy=1.0):
    """Lying: his back's lowest row just above the mat line (FEET's row), room left under him for
    the arm on the mat side. The core's half-width across the lie is about 20px, squashed by sy."""
    return (J.FEET[0] - 4, J.FEET[1] - 6 - int(round(20 * sy)) - lift)


def crash_impact():
    cv = J.frame_canvas()
    sy = 0.84
    b = Body(cv, 'pain', LIE_ANGLE, lie_pf(0, sy), sx=1.08, sy=sy)
    b.boots((195, 12.5, 245, 7.0), (170, 12.5, 125, 7.0))
    b.draw_core()
    b.arms((-100, 10.5, -60, 9.5), (8, 10.0, -6, 9.0))
    for (x, y, r) in ((40, 137, 5), (26, 138, 4), (152, 137, 5), (166, 138, 4), (14, 139, 3), (178, 139, 3)):
        J.puff(cv, x, y, r)
    J.lines(cv, [(30, 124, 18, 118), (44, 118, 36, 108), (148, 118, 156, 108), (162, 124, 174, 118),
                 (96, 100, 96, 90), (80, 102, 76, 92), (112, 102, 116, 92)])
    return J.finish(cv)


def crash_bounce():
    cv = J.frame_canvas()
    b = Body(cv, 'dizzy', 86, lie_pf(6, 1.0))
    b.boots((205, 12.5, 250, 7.0), (165, 12.5, 120, 7.0))
    b.draw_core()
    b.arms((-120, 10.5, -150, 9.5), (20, 10.0, -20, 9.0))
    # the hat and the cutlass coming back down out of the sky
    J.hat_placed(cv, 160, (124, 18))
    J.cutlass(cv, (48, 12), (46, 44), bow=1.5)
    for (x, y, r) in ((28, 132, 6), (164, 132, 6), (12, 138, 4), (180, 138, 4)):
        J.puff(cv, x, y, r)
    return J.finish(cv)


def crash_settle():
    cv = J.frame_canvas()
    sy = 0.94
    b = Body(cv, 'dizzy', LIE_ANGLE, lie_pf(0, sy), sx=1.02, sy=sy)
    b.boots((188, 12.5, 240, 7.0), (172, 12.5, 125, 7.0))
    b.draw_core()
    b.arms((-70, 10.0, -20, 9.0), (6, 10.0, -8, 9.0))
    # THUNK: the cutlass lands point-down in the mat beside him
    J.cutlass(cv, (38, 106), (40, 139), bow=1.2)
    J.lines(cv, [(30, 126, 26, 122), (50, 126, 54, 122), (32, 134, 27, 134), (48, 134, 53, 134)])
    # the hat just about to land back on his face
    b.hat_on_head(pull=4.0, tilt=40.0)
    for (x, y, r) in ((20, 139, 3), (172, 139, 3)):
        J.puff(cv, x, y, r)
    return J.finish(cv)


# ------------------------------------------------------------------ 10-11: down
def _down(chest):
    cv = J.frame_canvas()
    sy = 0.94
    b = Body(cv, 'ko', LIE_ANGLE, lie_pf(chest, sy), sx=1.02, sy=sy)
    b.boots((188, 12.5, 240, 7.0), (172, 12.5, 125, 7.0))
    b.draw_core()
    b.arms((-70, 10.0, -20, 9.0), (6, 10.0, -8, 9.0))
    J.cutlass(cv, (38, 106), (40, 139), bow=1.2)
    # his own tricorn, landed on his face: knocked down over one eye, askew
    b.hat_on_head(pull=12.0, tilt=22.0)
    for i, (x, y) in enumerate(((120, 86), (138, 80), (156, 86))):
        J.star(cv, x, y - (1 if (i + chest) % 2 else 0))
    return J.finish(cv)


def down_rest():
    return _down(0)


def down_breathe():
    return _down(1)


# name, builder, hold in seconds
FRAMES = [
    ('launch_contact', launch_contact, 0.06),
    ('launch_lift', launch_lift, 0.08),
    ('hang', hang, 0.16),
    ('tumble_a', tumble_a, 0.07),
    ('tumble_b', tumble_b, 0.06),
    ('tumble_c', tumble_c, 0.06),
    ('tumble_d', tumble_d, 0.07),
    ('crash_impact', crash_impact, 0.06),
    ('crash_bounce', crash_bounce, 0.08),
    ('crash_settle', crash_settle, 0.12),
    ('down_rest', down_rest, 0.4),
    ('down_breathe', down_breathe, 0.4),
]
assert len(FRAMES) == 12
AIR = (1, 2, 3, 4, 5, 6)
GROUND = (0, 7, 8, 9, 10, 11)
TAGS = {'launch': (0, 1, False), 'tumble': (2, 6, True), 'crash': (7, 9, False), 'down': (10, 11, True)}
