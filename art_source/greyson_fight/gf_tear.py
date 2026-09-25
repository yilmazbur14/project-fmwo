"""greyson_tear (5 frames): Greyson rips Computah's cannon arm off. PRE-CANNON look (both arms
flesh), approved rig (read-only, via gf_base), 112x112 frames, feet at (56, 111).

Staging (matches Computah's shipped computah_wrench and computah_arm_prop): Greyson stands to
Computah's RIGHT, where the cannon lies, and faces him (screen left). Computah's wrench f0 hauls the
arm up at -25 degrees toward Greyson; the prop's 'torn' frame continues that line. Greyson grips it
mid-barrel with his RIGHT hand (the screen-left arm) and tears it off one-handed; his left arm is
the one the cannon goes on, in greyson_attach.

  f0 grip     crouched a little, the right arm reaching down-left, fist round the barrel
  f1 strain   hips down, leaning back, the arm pulled straight, teeth clenched, tears
  f2 strain   further back; a sweat bead (the pair shakes, per the plan's "shake 3")
  f3 RIP      jerked back upright, the left arm flung out for balance, roaring
  f4 hold up  the torn arm raised overhead in his right fist, a double-biceps arm, raging

The gripping fist does not move from f0 to f3; each frame reports its centre as 'hand', measured
off its pixels (the prop's grip, (28, 25) in the prop's frame, goes there). Drawn facing screen-LEFT (Computah on his left);
flip together with Computah.

    python -B gf_tear.py      # prints each frame's numbers and audit; writes nothing
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
import gf_walk  # noqa: E402
import gf_limb  # noqa: E402
import gf_faces  # noqa: E402
import gf_faces_tk as FT  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face, gr_boots = B.K, B.gr_fig, B.gr_arms, B.gr_hands, \
    B.gr_face, B.gr_boots

FIST_ANCHOR = (18, 81)            # the approved fist's '@' texel for the gripping fist; its
                                  # centre (reported as 'hand') is where the prop's grip goes
WRIST = (18.5, 79.0)
UPPER_LEN = math.hypot(gf_limb.E0[0] - gf_limb.S0[0], gf_limb.E0[1] - gf_limb.S0[1])
LOWER_LEN = math.hypot(gf_limb.W0[0] - gf_limb.E0[0], gf_limb.W0[1] - gf_limb.E0[1])
CROWN, HIP = 26, 76


def ik(shoulder, wrist, bend=-1):
    """The elbow for a two-bone arm of the approved lengths from `shoulder` to `wrist`, bent to
    the outside (bend -1: the elbow on the left of the shoulder-wrist line, screen left)."""
    sx, sy = shoulder
    wx, wy = wrist
    d = math.hypot(wx - sx, wy - sy)
    d = min(d, UPPER_LEN + LOWER_LEN - 0.01)
    a = (UPPER_LEN ** 2 - LOWER_LEN ** 2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, UPPER_LEN ** 2 - a * a))
    ux, uy = (wx - sx) / d, (wy - sy) / d
    px, py = sx + ux * a, sy + uy * a
    nx, ny = -uy, ux
    e1 = (px + nx * h, py + ny * h)
    e2 = (px - nx * h, py - ny * h)
    return e1 if (e1[0] < e2[0]) == (bend < 0) else e2


def shear(part, lean, hip):
    """Lean the upper body back: each row above the hip slides right by up to `lean` px at the
    crown (nothing at the hip), so the body tilts without a redraw."""
    if not lean:
        return dict(part)
    out = {}
    for (x, y), k in part.items():
        t = max(0.0, min(1.0, (hip - y) / float(hip - CROWN)))
        out[(x + int(round(lean * t)), y)] = k
    return out


def slid(lean, y, hip):
    return lean * max(0.0, min(1.0, (hip - y) / float(hip - CROWN)))


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


# name, hip drop, lean, other arm, face, sweat
FRAMES = [
    ('grip', 2, -2, 'idle', 'rage', False),       # leaning in toward the arm
    ('strain', 4, 3, 'idle', 'rage', False),      # sitting back into the pull
    ('strain', 4, 5, 'idle', 'rage', True),
    ('rip', 1, 7, 'fling', 'roar_tears', True),   # jerked back as it comes away
    ('hold up', 0, 0, 'idle', 'rage_open', False),
]

# The roar with his tears (the approved flex brows and vein, gf_faces' roar mouth).
ROAR_TEARS = gf_faces.FLEX_UPPER[:8] + FT.RAGE_EYES + gf_faces.ROAR[15:]


def face_rows(name):
    return ROAR_TEARS if name == 'roar_tears' else FT.FACES[name]


def face_part(name):
    out = {}
    for r, row in enumerate(face_rows(name)):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FT.FX0 + c, FT.FY0 + r)] = ch
    return out


def frame(i):
    name, drop, lean, other, face, sweat = FRAMES[i]
    hip = HIP + drop
    cv = K.Canvas()
    # legs: the approved legs, hips dropped (the knees give); boots planted
    for side in (0, 1):
        cv.stamp(K.despeckle(gf_walk.posed_leg(side, drop, 0)))
    for side in (0, 1):
        cv.stamp(gr_boots.boot(side), outline=False)
    # the trunk leans back over the hips
    P = gr_fig.Pose('idle')
    cv.stamp(shear(moved(K.despeckle(gr_fig.torso(P)), 0, drop), lean, hip))
    cv.stamp(moved(gr_fig.trunks(), 0, drop))
    cv.stamp(moved(gr_fig.waistband(), 0, drop), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y + drop)] = 'k'
    # his left arm (screen right): at his side, or flung out for balance on the rip
    if other == 'idle':
        cv.stamp(shear(moved(K.despeckle(gr_arms.arm('idle', 1)), 0, drop), lean, hip))
        ofist = (gf_fig.mp((25.0, 84.5 + drop)))
        ofist = (ofist[0], ofist[1])
    else:
        # left-side coordinates, mirrored onto his left arm: the lean, which slides the trunk to
        # the RIGHT, is subtracted here so the mirrored shoulder moves right with it
        sl = slid(lean, 56 + drop, hip)
        sh = (30.0 - sl, 56.0 + drop)
        el, wr = (20.0 - sl, 63.0 + drop), (13.0 - sl, 71.0 + drop)
        cv.stamp(gf_limb.arm(sh, el, wr, 1))
        ofist = gf_fig.mp((wr[0] - 0.5, wr[1] + 2.5))
    # his right arm (screen left): the pull, or the trophy held high
    if name != 'hold up':
        sh = (30.0 + slid(lean, 56 + drop, hip), 56.0 + drop)
        el = ik(sh, WRIST)
        cv.stamp(gf_limb.arm(sh, el, WRIST, 0))
    else:
        cv.stamp(K.despeckle(gr_arms.arm('flex', 0)))
    # fists: his left fist under the head; the gripping fist too (it is low, by his thigh)
    cv.stamp(gr_hands.fist('idle', 1, gf_fig.mp(ofist)), outline=False)
    if name != 'hold up':
        grip = gr_hands.fist('idle', 0, FIST_ANCHOR)
        cv.stamp(grip, outline=False)
    # the head rides the lean as one block (no shear across the face)
    hx = int(round(slid(lean, 40 + drop, hip)))
    head = gr_face.mane()
    fp = face_part(face)
    head.update(fp)
    if sweat:
        head.update(gr_face.SWEAT)
    cv.stamp(moved(head, hx, drop), outline=False)
    if name == 'hold up':
        grip = gr_hands.fist('flex', 0, (15.0, 40.0))
        cv.stamp(grip, outline=False)
    keep = {(x + hx, y + drop) for (x, y) in fp}
    gf_fig.finish(cv, keep)
    info = {'name': name, 'drop': drop, 'lean': lean, 'hand': centre(grip)}
    if sweat:
        info['fx'] = {(x + hx, y + drop) for (x, y) in gr_face.SWEAT}
    return cv, info


def centre(part):
    """The middle of a placed fist, in continuous texel coordinates ((0, 0) is the frame's
    top-left corner; texel (i, j) covers [i, i+1) x [j, j+1)), measured off its pixels."""
    xs = [x for (x, y) in part]
    ys = [y for (x, y) in part]
    return ((min(xs) + max(xs) + 1) / 2.0, (min(ys) + max(ys) + 1) / 2.0)

if __name__ == '__main__':
    for i in range(len(FRAMES)):
        cv, info = frame(i)
        a = B.audit(cv.px, info.get('fx', ()))
        print(i, info['name'], K.stats(cv.image()), 'bbox', K.bbox(cv.px),
              'audit', {k: len(v) for k, v in a.items()})
