"""Compose the redesign's frames. 0: hover, wings up. 1: hover, wings down. 2: the signature snarl."""
import sys

from pal import BCanvas, both, mir, stats
import body
import heads
import midmaps
import sidemaps
import view
import wings

MID = dict(cx=95.5, cy=43, phi=0, s=1.0, theta=0)
SIDE = dict(cx=156, cy=70, phi=-28, s=0.7, theta=12)
SIDE_REF = (156, 74)          # where the side face maps were drawn


def xf(d, bob=0, dx=0, dy=0):
    return heads.Xf(cx=d['cx'] + dx, cy=d['cy'] + bob + dy, phi=d['phi'], s=d['s'], theta=d['theta'])


def side_head(bob=0, roar=False):
    """The right side head: projected ears, crest, ruff, collar and skull, then the hand-drawn face.
    Roaring, it rears up and out and its jaw drops, so its collar and ruff sit lower than its skull."""
    sdx, sdy = (2, -3) if roar else (0, 0)
    side = BCanvas()
    low = xf(SIDE, bob, sdx, sdy + (3 if roar else 0))
    heads.build(side, xf(SIDE, bob, sdx, sdy), tongue_flip=True, features=False, low=low)
    dx = int(round(SIDE['cx'] - SIDE_REF[0])) + sdx
    dy = int(round(SIDE['cy'] - SIDE_REF[1])) + bob + sdy
    for p in sidemaps.parts(dx, dy, roar):
        side.stamp(p, outline=False)
    return side


def body_parts(cv, bob, pose='up'):
    tp = 'down' if pose == 'down' else 'up'
    cv.stamp(body.tail(bob, tp))
    cv.stamp(body.tail_tip(bob, tp))
    for p in body.hind_leg(bob):
        cv.stamp(both(p))
    cv.stamp(both(body.paw_map(False, bob)), outline=False)
    cv.stamp(body.mantle(bob))
    cv.stamp(body.belly(bob))
    cv.stamp(body.chest(bob))
    for p in body.front_leg(bob):
        cv.stamp(both(p))
    cv.stamp(both(body.paw_map(True, bob)), outline=False)
    cv.stamp(both(body.side_neck(bob)))


def build(pose='up', bob=0):
    sig = pose == 'sig'
    cv = BCanvas()
    wings.build(cv, 'down' if pose == 'down' else 'up', mir)
    mid_dy = -2 if sig else 0
    mid = xf(MID, bob, 0, mid_dy)
    for t in heads.headband_tails(mid, wave=1 if pose == 'down' else 0):
        cv.stamp(t)
    body_parts(cv, bob, pose)
    side = side_head(bob, roar=sig)
    cv.px.update(mir(side.px))
    cv.px.update(side.px)
    if sig:
        # the inhale maps were drawn with the head 3 rows up from frame 0's; line them up with this one
        base = int(round(MID['cy'] - heads.HY)) + bob
        mdy = base + mid_dy + 3
        low = xf(MID, bob, 0, 3)
        heads.build(cv, mid, with_headband=True, features=False, low=low, brows=True)
        cv.stamp(midmaps.inhale_glow(0, mdy), outline=False)
        for p in midmaps.inhale_mouth(0, mdy):
            cv.stamp(p, outline=False)
        cv.stamp(midmaps.inhale_tongue(0, mdy), outline=False)
        for e in midmaps.eye_parts(0, base + mid_dy):
            cv.stamp(e, outline=False)
        for q, k in inhale_fx(mdy).items():
            cv.px[q] = k
    else:
        heads.build(cv, mid, with_headband=True)
        dy = int(round(mid.cy - heads.HY))
        cv.stamp(midmaps.mouth_part(0, dy), outline=False)
        cv.stamp(midmaps.tongue_part(0, dy), outline=False)
        for e in midmaps.eye_parts(0, dy):
            cv.stamp(e, outline=False)
    return cv


# Embers dragged up into the maw on the inhale: wisps curving in over the chest, each running from its
# cool tail to its hot head, 2px thick so they hold at game scale.
INHALE_STREAKS = [
    [(74, 124), (76, 116), (80, 109), (85, 104)],
    [(117, 124), (115, 116), (111, 109), (106, 104)],
    [(88, 132), (88, 124), (90, 116)],
    [(103, 132), (103, 124), (101, 116)],
]
INHALE_SPARKS = [(80, 121), (111, 121), (95, 126), (70, 110), (121, 110), (84, 113), (107, 113)]


def inhale_fx(bob=0):
    from shapes import poly_line
    out = {}
    for s in INHALE_STREAKS:
        pix = poly_line([(x, y + bob) for (x, y) in s])
        n = len(pix)
        for i, (x, y) in enumerate(pix):
            t = i / max(1, n - 1)
            k = 'u' if t < 0.3 else 'v' if t < 0.6 else 'P' if t < 0.85 else 'Y'
            out[(x, y)] = k
            if t >= 0.2:
                side = 1 if x < 96 else -1
                out[(x + side, y)] = 'u' if t < 0.6 else 'v'
    for (x, y) in INHALE_SPARKS:
        out[(x, y + bob)] = 'Y'
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + bob + dy)
            if q not in out:
                out[q] = 'P'
    return out


BOB = {'up': 0, 'down': -2, 'sig': 0}

if __name__ == '__main__':
    pose = sys.argv[1] if len(sys.argv) > 1 else 'up'
    cv = build(pose, BOB[pose])
    im = cv.image()
    im.save(view.SCRATCH + 'frame_%s.png' % pose)
    view.save(im, 'frame_%s_4x.png' % pose, 4)
    view.save(im, 'frame_%s_2x.png' % pose, 2)
    print(stats(im))
