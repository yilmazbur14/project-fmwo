"""The puppet master's animations, drawn with jp_rig on the hover's own frame (320x224, anchor
(160, 223)).

The working pose holds both hands HIGH, at crown height: the arms raised up and out, the clawed
hands turned up, palms forward, the fingers fanned out with every claw hooked down. The strings
hang from those claw points, so they run DOWN to the puppets' back hooks (the build plan's hooks
sit at screen y 220-300, frame rows 96-123; the working claw points sit on rows 52-65). No frame
puts a claw point below row 150, so even the summon's dip stays above the rifts (rows 162-170).

  control      6 frames x 0.14 s, looping. Hover frame i's pose exactly (bob, wing breath, crown
               flicker, crack/core pulse, tail sway, embers), the hands pulling in turn (one rises
               as the other sinks) and a wave running across each hand's fingers.
  summon_*     7 frames, one shot. The hands open, plunge down toward the rifts, grip, and rip up
               over the crown: the pull that drags the puppets out of the floor. Then they let
               the puppets hang and settle back into the working pose. _both pulls with both hands
               (the plan's summon); _left / _right pull with one while the other keeps working.
               Wings coil on the dip and slam down on the yank; the core and cracks flare.
  yank_*       4 frames, one shot: one hand's quick, short pull (Danny's butt slam) while the other
               holds its working pose. _right is the plan's; _left is drawn too (a mirrored sprite
               would light him from the right and flip his crown).
  hit          2 frames, one shot: an uppercut's damage runs up the strings into him. The strings
               snatch both hands down and splay the claws, heat bursts through every crack, the
               core flares white, the grin opens; then he recoils.

Every frame yields its fingertips (the claw point texel of each digit) and a string tension per
hand (0 slack .. 1 taut). Nothing here writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import jp_rig as R  # noqa: E402
import jg_god as G  # noqa: E402
import jg_lord as L  # noqa: E402
import jg_base as B  # noqa: E402

W, H = R.W, R.H
ANCHOR = R.ANCHOR
CONTROL_N = G.N                      # 6: the hover's cycle
CONTROL_TIME = G.FRAME_TIME          # 0.14 s
HAND_SCALE = 1.3                     # the hands are drawn 1.3x: thrust toward the viewer
rad = math.radians

# the working pose (canonical left): upper arm out and up, forearm up, hand turned up at crown
# height, fingers hooked over. Raised in the picture plane the arm reads a little longer than the
# hover's hanging one; every pose keeps each limb within 1.15x of the approved length.
CTRL_EL = (120.0, 94.0)
CTRL_WR = (113.0, 68.0)


def claws_up(flex=(0.0, 0.0, 0.0, 0.0), spread=2.4, down=rad(-100), open_=0.0):
    """The raised working claw: palm forward, the fingers fanned up and out, each curving over so
    its claw hooks down. flex (0..1 per finger: index, middle, ring, little) curls a finger further
    down, pulling its string; open_ (0..1) straightens every finger (the wind-up)."""
    return R.Hand(down=down, spread=spread + 0.5 * open_,
                  curl=(0.0,) * 4,
                  hook=tuple(0.7 + 0.45 * f - 0.3 * open_ for f in flex),
                  droop=tuple(max(0.0, 0.5 + 0.2 * f - 0.35 * open_) for f in flex),
                  length=tuple(0.9 - 0.25 * f + 0.1 * open_ for f in flex),
                  thumb=1.0, thumb_droop=0.3 - 0.2 * open_, scale=HAND_SCALE, flip=True)


def finger_wave(i, phase):
    """Flex per finger at control frame i: a wave running little -> index across the hand, one
    finger at the top of its pull and a neighbour on its way, the rest resting."""
    out = []
    for j in range(4):
        c = math.cos(2 * math.pi * (i / float(CONTROL_N) - (3 - j) / 4.0 - phase))
        out.append(max(0.0, c) ** 2)
    return tuple(out)


def hand_lift(i, sign):
    """Rows the hand is raised at control frame i (the hands pull in turn)."""
    return sign * 2.0 * math.sin(2 * math.pi * i / CONTROL_N)


def ctrl_arm(i, sign, phase, drop=0.0):
    lift = hand_lift(i, sign) - drop
    el = (CTRL_EL[0], CTRL_EL[1] - 0.5 * lift)
    wr = (CTRL_WR[0], CTRL_WR[1] - lift)
    return R.Arm(el, wr, claws_up(finger_wave(i, phase)))


# the two hands work out of step: the right hand's lift and finger wave run half a cycle behind
LEFT = (1, 0.0)
RIGHT = (-1, 0.5)


def control_arms(i):
    return ctrl_arm(i, *LEFT), ctrl_arm(i, *RIGHT)


# ------------------------------------------------------------------ hands for the pulls

def tight(down=rad(92)):
    """The grip: the claw hooked hard, fingers short and curled under but still spread, so the
    strings leave it apart instead of as one bar; tips at the bottom."""
    return R.Hand(down=down, spread=2.3, curl=(0.0,) * 4, hook=(0.9,) * 4, droop=(0.6,) * 4,
                  length=(0.6,) * 4, thumb=1.25, thumb_droop=0.3, scale=HAND_SCALE)


def open_down(down=rad(96), spread=2.3, droop=0.2, hook=0.25):
    """A hand thrown open, fingers reaching down."""
    return R.Hand(down=down, spread=spread, curl=(0.0,) * 4, hook=(hook,) * 4, droop=(droop,) * 4,
                  length=(1.0,) * 4, thumb=1.1, thumb_droop=0.1, scale=HAND_SCALE)


# ------------------------------------------------------------------ the summon pull

# (name, elbow, wrist, hand) in canonical-left coordinates, before the bob
SUMMON_ARM = [
    ('ready', (120.0, 95.0), (112.0, 69.0), claws_up(open_=1.0)),                  # rises and opens: wind-up
    ('dip', (118.0, 110.0), (104.0, 128.0), open_down()),                           # plunges toward the rifts
    ('grip', (119.0, 112.0), (106.0, 130.0), tight(rad(94))),                        # clenches on the strings
    ('yank', (117.0, 104.0), (107.0, 96.0), tight(rad(84))),                         # ripping upward (smear)
    ('top', (122.0, 94.0), (114.0, 68.0), claws_up(flex=(0.8,) * 4, spread=2.0)),     # clenched over the crown
    ('hang', (120.0, 94.0), (112.0, 67.0), claws_up(spread=2.1)),                    # the puppets hang
    ('settle', (120.0, 93.0), (113.0, 66.0), claws_up()),                            # into the working pose
]
SUMMON_N = len(SUMMON_ARM)
SUMMON_TIMES = [0.10, 0.08, 0.16, 0.05, 0.14, 0.14, 0.10]
SUMMON_BOB = [1, 0, 0, 2, 3, 2, 1]
SUMMON_WING = [(-1.0, 0.02), (-2.0, 0.03), (-3.0, 0.04), (0.5, -0.01), (3.0, -0.05), (2.0, -0.035), (1.0, -0.02)]
SUMMON_GLOW = [1.0, 1.05, 1.15, 1.25, 1.3, 1.15, 1.05]
SUMMON_CORE = [1.0, 1.0, 1.08, 1.15, 1.2, 1.1, 1.0]
# the pulling hand's strings: slack as it dips, taut on the yank; a working hand's are 0.7
SUMMON_TENSION = [0.5, 0.0, 0.3, 1.0, 1.0, 0.85, 0.7]
CONTROL_TENSION = 0.7
# which control frame the other hand is on during summon frame k (it keeps working)
SUMMON_IDLE_FRAME = [0, 1, 2, 3, 4, 5, 0]


def _pose(k, wing, glow, core, mouth_open=False, embers_frame=None):
    ph = 2 * math.pi * (k % CONTROL_N) / CONTROL_N
    return L.Pose(wing_lift=wing[0], wing_spread=wing[1], flame=ph, glow=glow, core=core,
                  tail_sway=1.8 * math.sin(ph - 1.6), tail_seam=True, mouth_open=mouth_open,
                  embers=G.ember_specks((k if embers_frame is None else embers_frame) % CONTROL_N))


def summon_pose(k):
    return _pose(k, SUMMON_WING[k], SUMMON_GLOW[k], SUMMON_CORE[k])


def summon_arms(k, which):
    """which: 'left', 'right' or 'both' (the hands that pull)."""
    name, el, wr, hp = SUMMON_ARM[k]
    pull = R.Arm(el, wr, hp)
    li = SUMMON_IDLE_FRAME[k]
    left = pull if which in ('left', 'both') else ctrl_arm(li, *LEFT)
    right = pull if which in ('right', 'both') else ctrl_arm(li, *RIGHT)
    return left, right


# ------------------------------------------------------------------ the one-hand yank (Danny's slam)

YANK_ARM = [
    ('slack', (121.0, 102.0), (112.0, 79.0), claws_up(open_=0.8, spread=1.9)),     # the hand drops, fingers open
    ('pull', (120.0, 94.0), (114.0, 67.0), tight(rad(-60))),                         # snaps up past the crown
    ('hold', (120.0, 94.0), (114.0, 68.0), tight(rad(-70))),                         # held: the puppet is airborne
    ('return', (120.0, 93.0), (113.0, 66.0), claws_up(spread=2.0)),                  # back into the working pose
]
YANK_N = len(YANK_ARM)
YANK_TIMES = [0.06, 0.05, 0.12, 0.08]
YANK_BODY = [0, 1, 2, 3]            # the hover poses the body stays on (resume control at frame 4)
YANK_TENSION = [0.2, 1.0, 1.0, 0.8]


def yank_arms(k, which):
    name, el, wr, hp = YANK_ARM[k]
    pull = R.Arm(el, wr, hp)
    i = YANK_BODY[k]
    left = pull if which == 'left' else ctrl_arm(i, *LEFT)
    right = pull if which == 'right' else ctrl_arm(i, *RIGHT)
    return left, right


# ------------------------------------------------------------------ the hit (damage up the strings)

HIT_N = 2
HIT_TIMES = [0.08, 0.16]
HIT_BOB = [0, 2]
HIT_WING = [(-3.0, 0.05), (2.5, -0.03)]
HIT_GLOW = [1.6, 1.25]
HIT_CORE = [1.35, 1.15]
HIT_DROP = [11.0, 4.0]               # rows the strings snatch his hands down
HIT_TENSION = [1.0, 0.6]


def hit_arms(k):
    open_ = 1.0 if k == 0 else 0.5
    arms = []
    for sign, phase in (LEFT, RIGHT):
        a = ctrl_arm(0, sign, phase, drop=HIT_DROP[k])
        arms.append(R.Arm(a.el, a.wr, claws_up(open_=open_, spread=2.0)))
    return arms[0], arms[1]


HOTTER = {'V': 'R', 'R': 'T', 'T': 'r', 'r': 'O', 'O': 'Y', 'Y': 'w', 'P': 'Q', 'Q': 'w'}


def flare(px, steps=1):
    """Heat bursts through him: every lava, crack and core texel one step hotter."""
    out = dict(px)
    for _ in range(steps):
        out = {p: HOTTER.get(k, k) for p, k in out.items()}
    return out


# ------------------------------------------------------------------ speed lines on a pull

def yank_streaks(px, tips_side):
    """The smear: hot streaks trailing under a rising claw (effect texels, no keyline, only where
    nothing is drawn). tips_side: that hand's digit tips (after the bob)."""
    xs = sorted(t[0] for t in tips_side.values())
    ys = [t[1] for t in tips_side.values()]
    x0, x1 = xs[0], xs[-1]
    y0 = max(ys) + 2
    out = {}
    lanes = [x0 - 1.0, x0 + (x1 - x0) * 0.35, x0 + (x1 - x0) * 0.7, x1 + 1.0]
    lengths = [9, 14, 12, 7]
    for lx, ln in zip(lanes, lengths):
        x = int(round(lx))
        for dy in range(ln):
            y = int(round(y0 + dy))
            k = 'T' if dy < ln * 0.3 else 'R' if dy < ln * 0.65 else 'V'
            if (x, y) not in px and 0 <= x < W and 0 <= y < H:
                out[(x, y)] = k
    return out


# ------------------------------------------------------------------ frames

def _tip_texels(px, tips, bob):
    """Each digit's string point: the nearest opaque texel to the claw's float tip (moved by the
    bob), i.e. the last texel of its point."""
    out = {}
    for side, digits in tips.items():
        out[side] = {}
        for d, (x, y) in digits.items():
            y -= bob
            best = None
            for yy in range(int(round(y)) - 2, int(round(y)) + 3):
                for xx in range(int(round(x)) - 2, int(round(x)) + 3):
                    if (xx, yy) in px:
                        dd = (xx - x) ** 2 + (yy - y) ** 2
                        if best is None or dd < best[0]:
                            best = (dd, (xx, yy))
            out[side][d] = best[1]
    return out


def _frame(pose, left, right, bob, streak_sides=(), post=None):
    px, tips = R.build(pose, left, right)
    if post:
        px = post(px)
    px = R.bobbed(px, bob)
    tt = _tip_texels(px, tips, bob)
    fx = {(x, y - bob) for (x, y, k) in pose.embers}
    for side in streak_sides:
        streaks = yank_streaks(px, tt[side])
        px.update(streaks)
        fx |= set(streaks)
    return px, tt, fx


def control_frame(i):
    """(px, tips, tension, fx) for control frame i. tips: {'left'|'right': {digit: (x, y)}}."""
    left, right = control_arms(i)
    px, tt, fx = _frame(G.pose(i), left, right, G.BOB[i % CONTROL_N])
    return px, tt, {'left': CONTROL_TENSION, 'right': CONTROL_TENSION}, fx


def summon_frame(k, which):
    left, right = summon_arms(k, which)
    sides = [s for s in ('left', 'right') if which in (s, 'both')] if SUMMON_ARM[k][0] == 'yank' else []
    px, tt, fx = _frame(summon_pose(k), left, right, SUMMON_BOB[k], sides)
    ten = {s: (SUMMON_TENSION[k] if which in (s, 'both') else CONTROL_TENSION) for s in ('left', 'right')}
    return px, tt, ten, fx


def yank_frame(k, which):
    left, right = yank_arms(k, which)
    i = YANK_BODY[k]
    sides = [which] if YANK_ARM[k][0] == 'pull' else []
    px, tt, fx = _frame(G.pose(i), left, right, G.BOB[i], sides)
    ten = {s: (YANK_TENSION[k] if s == which else CONTROL_TENSION) for s in ('left', 'right')}
    return px, tt, ten, fx


def hit_frame(k):
    left, right = hit_arms(k)
    pose = _pose(0, HIT_WING[k], HIT_GLOW[k], HIT_CORE[k], mouth_open=True)
    post = (lambda p: flare(p, 1)) if k == 0 else None
    px, tt, fx = _frame(pose, left, right, HIT_BOB[k], post=post)
    return px, tt, {'left': HIT_TENSION[k], 'right': HIT_TENSION[k]}, fx


# ------------------------------------------------------------------ anims, as one table

def anims():
    """[(key, sheet stem, frames, times, loop, frame_fn(i), aura_phase_fn(i))]"""
    ctrl_phase = (lambda i: 2 * math.pi * i / CONTROL_N)
    sum_phase = (lambda k: 0.0 if SUMMON_CORE[k] > 1.05 else 2 * math.pi * (k % CONTROL_N) / CONTROL_N)
    out = [('control', 'jordan_god_puppeteer_control', CONTROL_N, [CONTROL_TIME] * CONTROL_N, True,
            control_frame, ctrl_phase)]
    for which in ('both', 'left', 'right'):
        out.append(('summon_' + which, 'jordan_god_puppeteer_summon_' + which, SUMMON_N, SUMMON_TIMES, False,
                    (lambda k, w=which: summon_frame(k, w)), sum_phase))
    for which in ('right', 'left'):
        out.append(('yank_' + which, 'jordan_god_puppeteer_yank_' + which, YANK_N, YANK_TIMES, False,
                    (lambda k, w=which: yank_frame(k, w)), (lambda k: ctrl_phase(YANK_BODY[k]))))
    out.append(('hit', 'jordan_god_hit', HIT_N, HIT_TIMES, False, hit_frame, (lambda k: 0.0)))
    return out


# ------------------------------------------------------------------ aura (additive), per frame

def aura_px(body, phase):
    """The approved aura's recipe (jg_god.aura_px) around any frame's silhouette."""
    solid = {(x + G.AURA_PAD, y) for (x, y) in body}
    extra = 1 if math.cos(phase) > 0.3 else 0
    rings = [('x', 2), ('y', 2 + extra), ('z', 2)]
    out = {}
    frontier = set(solid)
    seen = set(solid)
    for key, width in rings:
        for _ in range(width):
            nxt = set()
            for p in frontier:
                for q in B.neighbours8(p):
                    if q not in seen and 0 <= q[0] < G.AURA_W and 0 <= q[1] < G.AURA_H:
                        nxt.add(q)
            for q in nxt:
                if key == 'z' and (q[0] + q[1]) % 2:
                    continue
                out[q] = key
            seen |= nxt
            frontier = nxt
    return out
