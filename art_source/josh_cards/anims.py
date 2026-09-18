"""Josh's fight animation set.

Every frame is 80x80 and is built from the approved rig: poses.build() runs body.py's drawing
calls on a pose that is a delta from the standing pose, jhead.build() places head.py's approved
head, and cards.py draws every card and every gold bloom.

Frame convention
    feet (sneaker soles) on row 79 for all ground animations
    the glide / mount / dismount set stands on the giant card: soles on row 76, so the card's
    top surface sits at local y=76, centred on x=40
    unflipped = acting toward OUR RIGHT (the code flips for facing)
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
import poses as PS
import jhead as JH
import cards as CD
from poses import A, L, foot, shift, bob, lean, arms, legs, with_

B = PS.BASE


# ---------------------------------------------------------------- card helpers
def tcard(c, cx, cy, ang, w=8, h=13, pip='spade', glow=0.0):
    """One trading card, drawn so it still reads as a CARD at 3x: a hard black edge, a bone face,
    a one-pixel inset border inside it, and a bold suit pip.  The old 6x12 blanks turned into a
    pale clump the moment two of them overlapped."""
    if glow:
        CD.card_glow(c, cx, cy, w, h, ang, amp=glow, reach=3.0)
    CD.draw_card(c, cx, cy, w, h, ang, face='n', shade='N', dark='u', outline='#')
    if w >= 7 and h >= 11:
        CD.draw_card(c, cx, cy, w - 3, h - 4, ang, face='n', shade='n', dark='n',
                     pip=(CD.SPADE5 if pip == 'spade' else CD.DIAMOND5),
                     pip_col=('#' if pip == 'spade' else 'Q'), outline='U')
    else:                                       # ribbon cards: too small for a pip, keep an edge
        CD.draw_card(c, cx, cy, w - 2, h - 2, ang, face='n', shade='n', dark='n', outline='U')


def fan(c, pivot, angles, radius=12.5, w=8, h=13, grip=True, spread=1.4):
    """Cards fanned about a fist.  `spread` opens the fan wider than it was authored so you can
    count the cards, and every card gets its own pip instead of only the front one."""
    px, py = pivot
    mean = sum(angles) / float(len(angles))
    for i, a0 in enumerate(angles):
        a = mean + (a0 - mean) * spread
        r = math.radians(a)
        tcard(c, px + radius * math.sin(r), py - radius * math.cos(r), a, w, h,
              pip='spade' if i % 2 == 0 else 'diamond')
    if grip:
        for (dx, dy) in ((-1, 1), (0, 1), (1, 1), (-1, 2), (0, 2), (1, 2), (0, 0)):
            if c[py + dy][px + dx] not in '.':
                put(c, px + dx, py + dy, 'Q' if (dx + dy) % 2 == 0 else 'q')


def spinner(c, cx, cy, ang, w=7, h=11, glow_amp=0.42):
    tcard(c, cx, cy, ang, w, h, pip='diamond', glow=glow_amp)


def hot_card(c, cx, cy, ang, w=8, h=14, amp=1.0, reach=7.0, ray=1.0, pip=None):
    """The signature blazing gold card: bloom, rays, white-hot face."""
    CD.card_glow(c, cx, cy, w, h, ang, amp=amp, reach=reach)
    if ray:
        CD.rays(c, cx, cy, [-90, -50, -14, 22, 60, 118, 160, 200],
                [max(2, int(v * ray)) for v in (6, 6, 8, 6, 7, 5, 5, 4)], gap=int(h * 0.5))
    CD.draw_card(c, cx, cy, w, h, ang, face='w', shade='Y', dark='F',
                 pip=pip or CD.SPADE5, pip_col='#', outline='#')


def sparks(c, pts):
    for (x, y, s) in pts:
        CD.spark(c, x, y, s)


def streak(c, pts, ramp='YFDA'):
    """A short motion trail of gold dashes: (x, y, tone index)."""
    for (x, y, i) in pts:
        if c[y][x] == '.':
            put(c, x, y, ramp[min(i, len(ramp) - 1)])


def glove(c, cx, cy, r=3.6):
    """A red fingerless glove drawn ON TOP of everything - for the hand that grips the cap brim,
    which the head layer would otherwise cover."""
    m = ellipse_mask(cx, cy, r, r * 1.05)
    under = copy(c)
    from body import paint, outline_only
    from rig import hdome, RED, TH_5
    paint(c, m, lambda px, py: hdome(px, py, cx, cy, r, r * 1.05, r * 1.05), RED, TH_5, 0.95)
    outline_only(c, m, under)
    return m


# ================================================================== 1. IDLE
IDLE_BOB = [0, -1, -1, 0]
IDLE_FAN = [(-78, -52, -26), (-74, -48, -22), (-80, -54, -28), (-76, -50, -24)]
IDLE_ORB = [(66, 45, 26), (67, 49, 44), (65, 53, 62), (64, 48, 8)]


def idle(i):
    n = i % 4
    c = blank()
    P = bob(B, IDLE_BOB[n])
    PS.build(c, P)
    JH.build(c, dy=IDLE_BOB[n], mouth='smirk')
    hx, hy = P['l_arm'][3]
    fan(c, (hx + 3, hy - 1), list(IDLE_FAN[n]), radius=11.0)
    CD.glow(c, [(hx - 7, hy - 4, 0.32), (hx - 5, hy - 8, 0.30), (hx - 2, hy - 11, 0.26)], 8.0)
    ox, oy, oa = IDLE_ORB[n]
    spinner(c, ox, oy, oa, glow_amp=0.42 + 0.04 * n)
    sparks(c, [(61, 36, 2 if n % 2 == 0 else 1), (70, 57, 1)] + ([(18, 54, 1)] if n == 1 else []))
    return c


# ================================================================== 2. INTRO
def _cascade(c, hi, lo, n, sag=1.0, w=6, h=10):
    """Waterfall shuffle: a ribbon of cards falling from the high hand into the low one.  The
    ribbon sags under gravity and runs from beside his head down across his chest, so it never
    crosses his face."""
    hx, hy = hi
    lx, ly = lo
    ang0 = math.degrees(math.atan2(lx - hx, -(ly - hy)))
    for k in range(n):
        t = k / float(max(1, n - 1))
        x = hx + (lx - hx) * t
        y = hy + (ly - hy) * t + 7.0 * sag * math.sin(math.pi * t)
        tcard(c, x, y, ang0 + 90 - 34 * (1 - t), w, h, pip='spade' if k % 2 else 'diamond')


def intro(i):
    c = blank()
    if i == 0:
        # deck raised beside his head, the first cards breaking away toward the catching hand
        P = arms(B,
                 front=A((29, 51), (25, 57), (23, 62), (23, 64), 5.2, 4.0, 3.2, 3.9),
                 back=A((51, 51), (57, 51), (60, 47), (61, 44), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, turn=2, eyes='squint', mouth='smirk')
        _cascade(c, (60, 47), (26, 61), 6, sag=0.45)
        tcard(c, 64, 42, -14, 8, 14, pip='diamond')
        CD.glow(c, [(62, 35, 0.30), (34, 55, 0.22)], 8.0)
    elif i == 1:
        # full waterfall: the ribbon pours from the high hand down across his chest
        P = arms(bob(B, -1),
                 front=A((29, 51), (24, 59), (21, 65), (20, 67), 5.2, 4.0, 3.2, 3.9),
                 back=A((51, 51), (59, 48), (63, 42), (64, 38), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dy=-1, turn=2, eyes='squint', mouth='smirk')
        _cascade(c, (64, 41), (23, 64), 8, sag=1.25)
        tcard(c, 65, 36, -20, 8, 13, pip='diamond')
        CD.glow(c, [(62, 30, 0.32), (52, 48, 0.24), (30, 60, 0.26)], 9.0)
        sparks(c, [(70, 28, 2), (56, 40, 1), (17, 58, 1)])
    elif i == 2:
        # ribbon collapsing into the low hand, deck squaring up
        P = arms(B,
                 front=A((29, 51), (25, 57), (23, 62), (23, 64), 5.2, 4.0, 3.2, 3.9),
                 back=A((51, 51), (57, 53), (58, 50), (58, 48), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, turn=2, eyes='squint', mouth='smirk')
        _cascade(c, (58, 50), (26, 61), 6, sag=0.7)
        tcard(c, 25, 62, 8, 8, 13, pip='diamond')
        CD.glow(c, [(42, 56, 0.26), (30, 58, 0.24)], 8.0)
    elif i == 3:
        # cap tip: glove on the brim, cap lifted and canted, head dipped, wink
        P = arms(B,
                 front=A((29, 51), (26, 44), (28, 37), (30, 33), 5.2, 4.0, 3.2, 3.4),
                 back=A((51, 51), (56, 57), (54, 63), (51, 66), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dy=2, rot=-6, eyes='wink', mouth='smirk',
                 cap_dy=-4, cap_dx=-2, cap_rot=-7)
        glove(c, 28, 30, 3.5)                       # fingers over the lifted brim
        fan(c, (54, 65), [-70, -44, -18], radius=10.0)
        CD.glow(c, [(46, 62, 0.26), (48, 58, 0.24)], 7.0)
        sparks(c, [(60, 28, 1), (20, 32, 1)])
    elif i == 4:
        # cap back on, one card pulled clear and cocked, smirk
        P = arms(B,
                 front=A((51, 51), (57, 55), (58, 60), (58, 62), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 51), (25, 58), (23, 64), (23, 67), 5.2, 4.0, 3.2, 3.9))
        P = lean(P, 1)
        PS.build(c, P)
        JH.build(c, turn=2, eyes='squint', mouth='smirk', brows='angry')
        fan(c, (26, 66), [-72, -46, -20], radius=10.0)
        hot_card(c, 63, 57, 20, w=7, h=12, amp=0.75, reach=5.0, ray=0.45, pip=CD.SPADE5)
        sparks(c, [(70, 48, 1), (54, 44, 1)])
    else:
        # the flick: hand snapped down and out, card buried in the floor, gold burst
        P = arms(B,
                 front=A((51, 52), (57, 58), (57, 65), (56, 68), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 51), (25, 58), (23, 64), (23, 67), 5.2, 4.0, 3.2, 3.9))
        P = lean(P, 2)
        PS.build(c, P)
        JH.build(c, turn=3, dy=1, rot=4, eyes='squint', mouth='smirk', brows='angry')
        fan(c, (26, 66), [-72, -46, -20], radius=10.0)
        streak(c, [(58, 70, 3), (59, 72, 2), (60, 73, 1), (61, 74, 0)])
        CD.card_glow(c, 63, 74, 7, 11, 14, amp=1.0, reach=6.0)
        CD.draw_card(c, 63, 74, 7, 11, 14, face='w', shade='Y', dark='F',
                     pip=CD.SPADE5, pip_col='#', outline='#')
        CD.rays(c, 63, 74, [-90, -55, -20, 20, 55], [7, 6, 5, 6, 5], gap=6)
        sparks(c, [(71, 66, 2), (54, 76, 1), (74, 78, 1)])
    return c


# ================================================================== 3. LAY CARD
def lay_card(i):
    c = blank()
    if i == 0:
        # knees breaking, card carried down and out to our right, clear of his legs
        P = legs(B,
                 l=L((34, 63), (32, 70), (31, 76), 5.4, 4.6, 4.0),
                 r=L((46, 64), (49, 70), (49, 76), 5.1, 4.4, 3.8))
        P = bob(P, 3)
        P = arms(P,
                 front=A((51, 54), (57, 59), (57, 65), (57, 68), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 54), (25, 60), (24, 66), (24, 69), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dy=3, rot=4, turn=3, eyes='squint', mouth='smirk')
        fan(c, (27, 68), [-72, -46, -20], radius=9.5)
        tcard(c, 62, 70, 54, 8, 13, pip='diamond')
        CD.card_glow(c, 62, 70, 8, 12, 54, amp=0.55, reach=4.0)
    elif i == 1:
        # deep crouch, the card set flat on the floor under his fingers
        P = legs(B,
                 l=L((33, 67), (28, 72), (29, 77), 5.6, 4.8, 4.0),
                 r=L((47, 68), (51, 72), (49, 77), 5.3, 4.6, 3.8),
                 lshoe=foot(29, 79, 11, 5, -1), rshoe=foot(49, 79, 11, 5, 1))
        P = bob(P, 8)
        P = arms(P,
                 front=A((51, 59), (57, 64), (60, 70), (61, 73), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 59), (24, 63), (23, 68), (23, 71), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dy=8, rot=6, turn=3, eyes='squint', mouth='smirk')
        fan(c, (26, 70), [-70, -44, -18], radius=9.0)
        CD.card_glow(c, 64, 76, 15, 5, 0, amp=0.85, reach=4.5)
        CD.draw_card(c, 64, 76, 15, 5, 0, face='n', shade='u', dark='U',
                     pip=CD.DIAMOND3, pip_col='Q')
        sparks(c, [(72, 71, 1), (56, 73, 1)])
    else:
        # stepped away and back up, watching it light
        P = legs(B,
                 l=L((32, 60), (29, 69), (28, 76), 5.4, 4.6, 4.0),
                 r=L((44, 61), (43, 69), (42, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(27, 79, 11, 6, -1), rshoe=foot(42, 79, 11, 6, 1))
        P = shift(P, -4, 0, keys=PS.UPPER)
        P = lean(P, -2)
        P = arms(P,
                 front=A((25, 51), (21, 58), (20, 64), (20, 67), 5.2, 4.0, 3.2, 3.9),
                 back=A((47, 51), (53, 55), (56, 60), (57, 63), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dx=-4, rot=5, turn=4, eyes='squint', mouth='smirk')
        fan(c, (23, 66), [-72, -46, -20], radius=10.0)
        CD.glow(c, [(62, 71, 0.52), (66, 75, 0.56), (59, 76, 0.46), (70, 73, 0.44)], 11.0)
        CD.rays(c, 64, 76, [-90, -58, -26, 26, 58], [9, 8, 7, 8, 7], gap=4)
        sparks(c, [(70, 64, 2), (55, 69, 1), (75, 71, 1)])
    return c


# ================================================================== 7. THROW
def throw(i):
    """0 wind-up, 1 release, 2 follow-through, 3 ready.  Loops 3 -> 0."""
    c = blank()
    if i == 0:
        # coiled: throwing hand dragged low across the belt, weight on the back foot
        P = legs(B,
                 l=L((33, 60), (31, 69), (30, 76), 5.4, 4.6, 4.0),
                 r=L((46, 61), (48, 69), (48, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(29, 79, 11, 6, -1))
        P = lean(P, -3)
        P = arms(P,
                 front=A((49, 52), (47, 59), (41, 58), (38, 57), 5.0, 4.0, 3.2, 3.8),
                 back=A((27, 51), (22, 57), (20, 63), (19, 66), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dx=-1, turn=3, rot=-3, eyes='squint', mouth='smirk', brows='angry')
        fan(c, (22, 65), [-74, -48, -22], radius=10.5)
        hot_card(c, 34, 55, -66, w=7, h=12, amp=0.75, reach=4.5, ray=0.45)
        sparks(c, [(40, 48, 1), (28, 50, 1)])
    elif i == 1:
        # release: arm snapped out to our right, card just off the fingertips
        P = legs(B,
                 l=L((34, 60), (32, 69), (31, 76), 5.4, 4.6, 4.0),
                 r=L((47, 61), (50, 69), (51, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(30, 79, 11, 6, -1), rshoe=foot(51, 79, 11, 6, 1))
        P = lean(P, 3)
        P = arms(P,
                 front=A((52, 51), (59, 51), (65, 50), (68, 49), 5.0, 4.0, 3.2, 3.8),
                 back=A((30, 51), (26, 58), (25, 64), (25, 67), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dx=1, turn=4, rot=3, eyes='open', mouth='smirk', brows='angry')
        fan(c, (28, 66), [-74, -48, -22], radius=10.5)
        streak(c, [(58, 58, 3), (53, 60, 2), (48, 62, 1), (43, 64, 0),
                   (62, 55, 3), (66, 53, 2)])
        hot_card(c, 73, 45, 74, w=7, h=12, amp=1.0, reach=6.0, ray=0.8)
        sparks(c, [(64, 37, 2), (60, 62, 1)])
    elif i == 2:
        # follow-through: hand open and dropping, the card already gone
        P = legs(B,
                 l=L((34, 60), (32, 69), (31, 76), 5.4, 4.6, 4.0),
                 r=L((47, 61), (50, 69), (51, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(30, 79, 11, 6, -1), rshoe=foot(51, 79, 11, 6, 1))
        P = lean(P, 4)
        P = arms(P,
                 front=A((52, 52), (59, 55), (64, 59), (66, 61), 5.0, 4.0, 3.2, 3.8),
                 back=A((30, 51), (27, 58), (26, 64), (26, 67), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dx=2, turn=4, rot=5, eyes='squint', mouth='smirk', brows='angry')
        fan(c, (29, 66), [-74, -48, -22], radius=10.5)
        streak(c, [(70, 42, 2), (74, 39, 1), (77, 36, 0), (66, 45, 3)])
        sparks(c, [(71, 52, 1), (57, 46, 1)])
    else:
        # ready: squared up again, next card already snapped into the fingers
        P = arms(B,
                 front=A((51, 51), (56, 57), (55, 62), (54, 64), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 51), (25, 58), (23, 64), (23, 67), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, turn=2, eyes='squint', mouth='smirk')
        fan(c, (26, 66), [-76, -50, -24], radius=11.0)
        tcard(c, 60, 60, -46, 8, 13, pip='diamond')
        CD.card_glow(c, 60, 60, 7, 11, -46, amp=0.55, reach=3.5)
        sparks(c, [(67, 51, 1), (20, 52, 1)])
    return c


# ================================================================== 8. SHOW CARD
def show_card(i):
    c = blank()
    P = arms(bob(B, -1 if i else 0),
             front=A((51, 51), (57, 46), (59, 39), (59, 35), 5.0, 4.0, 3.2, 3.8),
             back=A((29, 51), (25, 58), (23, 64), (22, 67), 5.2, 4.0, 3.2, 3.9))
    PS.build(c, P)
    JH.build(c, dy=-1 if i else 0, turn=2, eyes='squint' if i == 0 else 'open',
             mouth='smirk', brows='angry')
    fan(c, (25, 66), [-76, -50, -24], radius=11.0)
    amp = (0.7, 1.0, 1.2)[i]
    hot_card(c, 60, 27, 4, w=11, h=17, amp=amp, reach=5.0 + 3.0 * i, ray=0.6 + 0.35 * i)
    for (gx, gy) in ((58, 34), (60, 34), (59, 35)):
        if c[gy][gx] != '.':
            put(c, gx, gy, 'D')
    CD.rim_light(c, 'IiUuNn' + 'gfdsa1' + 'LqQRE' + 'xXvVz', (60, 27), reach=40.0)
    sparks(c, [(70, 18, 1 + i), (48, 16, 1), (72, 40, 1)][: 2 + (i > 0)])
    return c


# ================================================================== 10a. HIT
def hit(i):
    c = blank()
    if i == 0:
        # impact: head snapped away, shoulders hunched, one arm flung out, cards knocked loose
        P = legs(B,
                 l=L((33, 62), (29, 69), (27, 76), 5.4, 4.6, 4.0),
                 r=L((45, 63), (46, 70), (46, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(26, 79, 11, 6, -1))
        P = lean(P, -4)
        P = arms(P,
                 front=A((26, 53), (19, 57), (14, 60), (12, 62), 5.2, 4.0, 3.2, 3.9),
                 back=A((48, 53), (54, 58), (52, 63), (50, 65), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dx=-5, dy=2, rot=-15, turn=-2, eyes='wide', mouth='open', brows='pain',
                 cap_dx=-2, cap_dy=-2, cap_rot=-7)
        for (cx, cy, ang) in ((13, 40, -54), (24, 30, 34), (64, 44, 70), (70, 60, 16)):
            tcard(c, cx, cy, ang, 7, 11, pip='spade')
        sparks(c, [(19, 34, 2), (58, 36, 1), (33, 24, 1)])
    else:
        # settling back, still reeling, eyes screwed shut
        P = legs(B,
                 l=L((33, 61), (30, 69), (29, 76), 5.4, 4.6, 4.0),
                 r=L((46, 62), (47, 70), (47, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(28, 79, 11, 6, -1))
        P = lean(P, -2)
        P = arms(P,
                 front=A((28, 53), (22, 58), (19, 63), (18, 65), 5.2, 4.0, 3.2, 3.9),
                 back=A((50, 53), (56, 57), (55, 62), (54, 65), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dx=-3, dy=3, rot=-8, turn=-1, eyes='shut', mouth='open', brows='pain',
                 cap_dx=-1, cap_dy=-1, cap_rot=-4, sweat=1)
        for (cx, cy, ang) in ((12, 50, -40), (27, 36, 22), (66, 52, 58), (72, 66, 8)):
            tcard(c, cx, cy, ang, 7, 11, pip='spade')
        sparks(c, [(20, 42, 1), (59, 44, 1)])
    return c


# ================================================================== 4-6. ON THE CARD
# The glide set stands on the giant card: soles on row 76 so the card's top surface is at y=76.
DECK = 76


def wind(c, pts, tone='vVz'):
    """Speed streaks: a few long ones of varied length rather than a comb of short dashes.
    Each fades in at its leading (right) edge so it reads as motion, not as a dashed rule."""
    for (x, y, ln) in pts:
        for k in range(ln):
            X = x + k
            if 0 <= X < W and 0 <= y < H and c[y][X] == '.':
                put(c, X, y, tone[2 if k < ln - 4 else (1 if k < ln - 2 else 0)])


def _ride(dy=0, tail=0):
    """The shared riding stance: knees bent, weight forward over the front foot, soles on DECK,
    coat tails streaming back to our left.  dy lifts the upper body only."""
    P = legs(B,
             l=L((34, 62), (26, 67), (29, 72), 5.4, 4.8, 4.0),
             r=L((46, 63), (54, 67), (51, 72), 5.2, 4.6, 3.9),
             lshoe=[(23, 70), (34, 70), (35, 73), (33, DECK), (22, DECK), (20, 73)],
             rshoe=[(45, 70), (56, 70), (58, 73), (57, DECK), (45, DECK), (44, 73)])
    P = with_(P,
              torso=[(35, 44), (32, 46), (29, 48), (28, 52), (28, 56), (29, 60), (31, 64),
                     (36, 63), (41, 61), (46, 63), (51, 64), (52, 60), (52, 56), (52, 51),
                     (51, 47), (48, 45), (43, 44)],
              tee=[(35, 46), (45, 46), (46, 54), (43, 61), (37, 61), (34, 54)],
              collar_l=[(31, 44), (36, 47), (36, 54), (32, 54), (29, 50), (29, 45)],
              collar_r=[(49, 44), (44, 47), (44, 54), (48, 54), (51, 50), (51, 45)],
              collar_lining=[(34, 47, ["Qq"]), (34, 48, ["QQq"]), (35, 49, ["QQ"]), (35, 50, ["Qq"]),
                             (35, 51, ["Qq"]), (35, 52, ["qq"]),
                             (44, 47, ["qQ"]), (43, 48, ["qQQ"]), (43, 49, ["QQ"]), (43, 50, ["qQ"]),
                             (43, 51, ["qQ"]), (43, 52, ["qq"])],
              belt=(32, 48, 58),
              coat_lines=[(31, 54, ["u"]), (31, 55, ["U"]), (31, 56, ["U"]), (31, 57, ["u"]),
                          (49, 54, ["U"]), (49, 55, ["U"]), (49, 56, ["u"])],
              neck=[(36, 44), (44, 44), (45, 51), (35, 51)],
              neck_axis=((40, 44), (40, 52), 4.6, 4.2),
              tail_back=[TAILS[tail]],
              )
    P = PS.trunk(P)
    P = lean(P, 6, pivot=66)
    return shift(P, 2, dy, keys=PS.UPPER)


# The duster streaming off his back.  Kept BETWEEN the shoulder blade and the knee (y43..62) and
# out to our left, so the space under his soles stays empty for the giant card sprite.  Narrow,
# with a wavy trailing edge - the earlier version was a pale slab sitting exactly where the card
# has to go and read as a surfboard.
TAILS = [
    # A: snapped straight back, level with the hip
    [(34, 46), (28, 46), (21, 47), (14, 49), (7, 52), (5, 55), (5, 58), (9, 60), (15, 58),
     (21, 60), (27, 61), (34, 62)],
    # B: the wind dragging it down, tip curling under
    [(34, 48), (28, 49), (21, 51), (14, 54), (7, 58), (5, 61), (6, 64), (11, 65), (17, 62),
     (23, 63), (29, 64), (34, 64)],
    # C: whipped up behind his shoulder
    [(34, 44), (27, 41), (20, 39), (13, 40), (7, 43), (5, 46), (6, 49), (11, 51), (17, 49),
     (23, 52), (29, 54), (34, 56)],
]

# Leading arm reaches forward into the wind, trailing arm is swept back and DOWN behind his hip -
# an asymmetric silhouette, not the T-pose the first pass had.
GLIDE_ARMS = [
    (A((54, 48), (61, 46), (67, 45), (70, 44), 5.0, 4.0, 3.2, 3.8),
     A((31, 51), (25, 57), (20, 62), (18, 64), 5.2, 4.0, 3.2, 3.9)),
    (A((54, 47), (61, 44), (67, 42), (70, 41), 5.0, 4.0, 3.2, 3.8),
     A((31, 50), (25, 55), (21, 60), (19, 62), 5.2, 4.0, 3.2, 3.9)),
    (A((54, 49), (61, 48), (67, 47), (70, 46), 5.0, 4.0, 3.2, 3.8),
     A((31, 52), (25, 58), (19, 63), (17, 65), 5.2, 4.0, 3.2, 3.9)),
]
GLIDE_SEQ = [(0, 0, 0), (-1, 1, 1), (-1, 2, 2), (0, 1, 1)]
GLIDE_WIND = [[(0, 24, 17), (2, 34, 12), (0, 44, 21), (4, 56, 14)],
              [(0, 21, 20), (3, 32, 14), (0, 47, 17), (1, 58, 20)],
              [(2, 26, 14), (0, 36, 19), (1, 42, 12), (0, 54, 18)],
              [(0, 22, 18), (1, 38, 15), (2, 49, 20), (5, 60, 12)]]


def deck_light(c, y0=DECK - 1):
    """Gold bounce off the giant card: a warm rim on the sole row and a soft spill under him.
    The card itself is a separate sprite, so nothing solid is drawn here."""
    for x in range(W):
        for y in range(y0, min(H, y0 + 2)):
            if c[y][x] in 'XxvUuNn' and (y + 1 >= H or c[y + 1][x] in '.#'):
                c[y][x] = 'D' if (x % 3) else 'A'



def glide(i, hands=True):
    """4-frame ride loop.  The giant card is NOT drawn - its top surface belongs at y=76."""
    dy, tail, ar = GLIDE_SEQ[i % 4]
    c = blank()
    P = _ride(dy, tail)
    if hands:
        P = arms(P, front=GLIDE_ARMS[ar][0], back=GLIDE_ARMS[ar][1])
    else:
        P = arms(P, front=None, back=GLIDE_ARMS[ar][1])
    PS.build(c, P)
    JH.build(c, dx=3, dy=dy - 2, rot=5, turn=4, eyes='open', mouth='smirk', brows='angry')
    wind(c, [(x, y + dy, ln) for (x, y, ln) in GLIDE_WIND[i % 4]])
    deck_light(c)
    return c


def mount(i):
    """0 beside the card on the ground, 1 stepping up, 2 aboard and lifting."""
    c = blank()
    if i == 0:
        # weight back on the far foot, near heel already lifting, eyes down on the card
        P = legs(B,
                 l=L((34, 61), (31, 69), (30, 76), 5.4, 4.6, 4.0),
                 r=L((46, 62), (50, 68), (52, 74), 5.1, 4.4, 3.8),
                 lshoe=foot(29, 79, 11, 6, -1),
                 rshoe=[(46, 72), (57, 71), (59, 74), (58, 78), (47, 79), (45, 76)])
        P = bob(P, 2)
        P = lean(P, 3)
        P = arms(P,
                 front=A((51, 53), (58, 56), (63, 60), (65, 62), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 53), (24, 57), (21, 62), (20, 64), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dx=3, dy=3, rot=7, turn=5, eyes='squint', mouth='smirk', brows='angry')
        sparks(c, [(64, 71, 1), (40, 76, 1)])
    elif i == 1:
        # front foot up on the card, back foot still on the floor, body rising
        P = legs(B,
                 l=L((34, 59), (31, 68), (30, 76), 5.4, 4.6, 4.0),
                 r=L((46, 59), (51, 65), (53, 72), 5.2, 4.6, 3.9),
                 lshoe=foot(29, 79, 11, 6, -1),
                 rshoe=[(46, 70), (57, 70), (59, 73), (58, DECK), (46, DECK), (45, 73)])
        P = with_(P, tail_back=[TAILS[2]])
        P = lean(P, 3, pivot=64)
        P = arms(P,
                 front=A((52, 50), (60, 49), (66, 48), (69, 47), 5.0, 4.0, 3.2, 3.8),
                 back=A((30, 50), (23, 53), (17, 57), (14, 59), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dx=3, dy=-1, rot=5, turn=4, eyes='open', mouth='smirk', brows='angry')
        sparks(c, [(62, 70, 1), (34, 74, 1)])
    else:
        c = glide(0)
        sparks(c, [(20, 70, 2), (62, 70, 1)])
    return c


def dismount(i):
    """0 compressing on the card, 1 in the air with the legs tucked, 2 landed and absorbing."""
    c = blank()
    if i == 0:
        P = _ride(2, 1)
        P = arms(P,
                 front=A((52, 52), (58, 56), (61, 61), (62, 63), 5.0, 4.0, 3.2, 3.8),
                 back=A((30, 52), (24, 56), (20, 61), (19, 63), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dx=3, dy=1, rot=5, turn=4, eyes='open', mouth='smirk')
    elif i == 1:
        # airborne: knees tucked up, coat flaring
        P = legs(B,
                 l=L((34, 56), (29, 62), (33, 68), 5.4, 4.8, 4.0),
                 r=L((46, 57), (52, 62), (49, 68), 5.2, 4.6, 3.9),
                 lshoe=[(27, 65), (37, 65), (38, 68), (36, 71), (26, 71), (25, 68)],
                 rshoe=[(43, 65), (54, 65), (56, 68), (54, 71), (43, 71), (42, 68)])
        P = with_(P,
                  torso=[(35, 42), (32, 44), (29, 46), (28, 50), (28, 54), (29, 58), (31, 62),
                         (36, 61), (41, 59), (46, 61), (51, 62), (52, 58), (52, 54), (52, 49),
                         (51, 45), (48, 43), (43, 42)],
                  tee=[(35, 44), (45, 44), (46, 52), (43, 59), (37, 59), (34, 52)],
                  collar_l=[(31, 42), (36, 45), (36, 52), (32, 52), (29, 48), (29, 43)],
                  collar_r=[(49, 42), (44, 45), (44, 52), (48, 52), (51, 48), (51, 43)],
                  collar_lining=[(34, 45, ["Qq"]), (34, 46, ["QQq"]), (35, 47, ["QQ"]), (35, 48, ["Qq"]),
                                 (35, 49, ["Qq"]), (35, 50, ["qq"]),
                                 (44, 45, ["qQ"]), (43, 46, ["qQQ"]), (43, 47, ["QQ"]), (43, 48, ["qQ"]),
                                 (43, 49, ["qQ"]), (43, 50, ["qq"])],
                  belt=(32, 48, 56),
                  coat_lines=[(31, 52, ["u"]), (31, 53, ["U"]), (31, 54, ["U"]),
                              (49, 52, ["U"]), (49, 53, ["U"])],
                  neck=[(36, 42), (44, 42), (45, 49), (35, 49)],
                  neck_axis=((40, 42), (40, 50), 4.6, 4.2),
                  tail_back=[[(34, 46), (26, 44), (18, 43), (11, 45), (7, 50), (9, 56),
                             (16, 57), (24, 56), (30, 55), (35, 54)]])
        P = PS.trunk(P)
        P = arms(P,
                 front=A((52, 46), (59, 42), (64, 37), (66, 34), 5.0, 4.0, 3.2, 3.8),
                 back=A((30, 46), (23, 43), (17, 40), (14, 38), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dy=-2, turn=2, eyes='open', mouth='smirk', brows='up')
        wind(c, [(0, 52, 19), (3, 61, 14), (0, 69, 17)])
        sparks(c, [(24, 72, 1), (58, 70, 1)])
    else:
        # landed: deep absorb, hands low and out
        P = legs(B,
                 l=L((33, 64), (28, 71), (29, 77), 5.6, 4.8, 4.0),
                 r=L((47, 65), (52, 71), (51, 77), 5.3, 4.6, 3.9),
                 lshoe=foot(28, 79, 12, 5, -1), rshoe=foot(52, 79, 12, 5, 1))
        P = bob(P, 6)
        P = arms(P,
                 front=A((51, 57), (58, 61), (63, 66), (65, 68), 5.0, 4.0, 3.2, 3.8),
                 back=A((29, 57), (22, 61), (17, 66), (15, 68), 5.2, 4.0, 3.2, 3.9))
        PS.build(c, P)
        JH.build(c, dy=6, rot=3, turn=2, eyes='squint', mouth='smirk')
        CD.glow(c, [(30, 78, 0.34), (50, 78, 0.34)], 7.0)
        sparks(c, [(20, 74, 2), (62, 74, 2)])
    return c


def drop_bomb(i):
    """Flicking a bomb card downward from the glide.  Same ride silhouette, trailing arm works."""
    ar = [(A((53, 48), (61, 46), (68, 45), (71, 44), 5.0, 4.0, 3.2, 3.8),
           A((30, 47), (24, 42), (20, 37), (18, 34), 5.2, 4.0, 3.2, 3.8)),
          (A((53, 48), (61, 46), (68, 45), (71, 44), 5.0, 4.0, 3.2, 3.8),
           A((30, 49), (24, 54), (20, 60), (18, 63), 5.2, 4.0, 3.2, 3.8)),
          (A((53, 48), (61, 46), (68, 45), (71, 44), 5.0, 4.0, 3.2, 3.8),
           A((30, 50), (24, 57), (21, 64), (20, 67), 5.2, 4.0, 3.2, 3.8))][i]
    c = blank()
    P = arms(_ride([0, -1, 0][i], [0, 2, 1][i]), front=ar[0], back=ar[1])
    PS.build(c, P)
    JH.build(c, dx=3, dy=[-2, -3, -2][i], rot=5, turn=4, eyes='open',
             mouth='smirk', brows='angry')
    wind(c, [(0, 25, 18), (2, 36, 13), (0, 46, 20), (3, 57, 15)])
    if i == 0:
        hot_card(c, 17, 27, -18, w=7, h=12, amp=0.75, reach=4.5, ray=0.45)
    elif i == 1:
        streak(c, [(19, 52, 3), (18, 56, 2), (17, 60, 1)])
        hot_card(c, 16, 70, 8, w=7, h=12, amp=1.0, reach=6.0, ray=0.7)
    else:
        streak(c, [(19, 60, 3), (18, 63, 2), (17, 66, 1), (16, 69, 0)])
        CD.card_glow(c, 15, 73, 7, 11, 14, amp=0.9, reach=5.0)
        CD.draw_card(c, 15, 73, 7, 11, 14, face='w', shade='Y', dark='F',
                     pip=CD.SPADE5, pip_col='#', outline='#')
        sparks(c, [(24, 70, 1)])
    return c


# ================================================================== 9. RECOVERY
REC_SEQ = [(0, 1, 0), (-1, 2, 1), (-2, 3, 2), (-1, 2, 1)]


def recovery(i):
    """Doubled over, hands braced on his knees, shoulders hunched up around his sunken head, cap
    knocked back, deck spilling.  4-frame loop - the punish window."""
    dy, sweat, phase = REC_SEQ[i % 4]
    c = blank()
    P = legs(B,
             l=L((33, 64), (28, 71), (27, 77), 5.6, 4.8, 4.2),
             r=L((47, 65), (52, 71), (53, 77), 5.3, 4.6, 4.0),
             lshoe=foot(27, 79, 11, 6, -1), rshoe=foot(52, 79, 11, 6, 1))
    P = with_(P,
              # hunched: the shoulder line is up at y49 and the barrel is wider than his head
              torso=[(34, 49), (30, 50), (26, 53), (25, 58), (26, 63), (28, 68), (31, 71),
                     (36, 70), (41, 69), (46, 70), (51, 71), (54, 68), (55, 63), (56, 58),
                     (55, 53), (51, 50), (46, 49)],
              tee=[(35, 51), (45, 51), (46, 60), (43, 68), (37, 68), (34, 60)],
              collar_l=[(30, 48), (36, 51), (36, 58), (31, 58), (27, 54), (27, 49)],
              collar_r=[(50, 48), (44, 51), (44, 58), (49, 58), (53, 54), (53, 49)],
              collar_lining=[(34, 51, ["Qq"]), (34, 52, ["QQq"]), (35, 53, ["QQ"]), (35, 54, ["Qq"]),
                             (35, 55, ["qq"]),
                             (44, 51, ["qQ"]), (43, 52, ["qQQ"]), (43, 53, ["QQ"]), (43, 54, ["qQ"]),
                             (43, 55, ["qq"])],
              belt=(31, 49, 65),
              coat_lines=[(29, 58, ["u"]), (29, 59, ["U"]), (29, 60, ["U"]),
                          (51, 58, ["U"]), (51, 59, ["U"])],
              neck=[(36, 47), (44, 47), (45, 54), (35, 54)],
              neck_axis=((40, 47), (40, 55), 4.6, 4.2))
    P = PS.trunk(P)
    P = shift(P, 0, dy, keys=PS.UPPER)
    # elbows locked out wide, forearms dropping in onto the knees
    P = arms(P,
             front=A((28, 53 + dy), (19, 62), (24, 70), (27, 73), 5.2, 4.2, 3.4, 3.9),
             back=A((52, 53 + dy), (61, 62), (56, 70), (53, 73), 5.0, 4.0, 3.2, 3.8))
    PS.build(c, P)
    JH.build(c, dy=14 + dy, rot=-5, eyes='weary', mouth='pant', brows='pain', sweat=sweat,
             cap_dx=-3, cap_dy=-3, cap_rot=-8)
    # the deck spilling out of his coat, and two cards already down on the floor
    for (cx, cy, ang) in [((64, 56, 22), (68, 66, 46), (61, 72, 8)),
                          ((65, 59, 30), (69, 69, 54), (62, 75, 14)),
                          ((66, 62, 38), (70, 72, 62), (63, 77, 20))][phase]:
        tcard(c, cx, cy, ang, 7, 11, pip='spade')
    CD.draw_card(c, 15, 77, 11, 4, 0, pip=None)
    CD.draw_card(c, 22, 74, 9, 4, -12, pip=None)
    for (sx, sy) in [(58, 48), (12, 52)][: 1 + (phase > 1)]:
        put(c, sx, sy, 'C')
        put(c, sx + 1, sy + 1, 'y')
    return c


# ================================================================== 10b. DEFEAT
def defeat(i):
    c = blank()
    if i == 0:
        # staggering back, the deck starting to go
        P = legs(B,
                 l=L((33, 61), (28, 69), (25, 76), 5.4, 4.6, 4.0),
                 r=L((46, 62), (47, 70), (47, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(24, 79, 11, 6, -1))
        P = lean(P, -5)
        P = arms(P,
                 front=A((26, 52), (19, 49), (14, 45), (12, 42), 5.2, 4.0, 3.2, 3.9),
                 back=A((48, 52), (55, 49), (60, 46), (62, 43), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dx=-5, dy=1, rot=-13, eyes='wide', mouth='open', brows='pain',
                 cap_dx=-3, cap_dy=-2, cap_rot=-8)
        for (cx, cy, ang) in ((66, 58, 40), (71, 48, 14), (20, 62, -30)):
            tcard(c, cx, cy, ang, 7, 11, pip='spade')
        sparks(c, [(16, 36, 2), (62, 36, 1)])
    elif i == 1:
        # the deck bursts: cards spraying up out of the coat
        P = legs(B,
                 l=L((33, 63), (28, 70), (26, 76), 5.4, 4.6, 4.0),
                 r=L((47, 64), (50, 70), (51, 76), 5.1, 4.4, 3.8),
                 lshoe=foot(25, 79, 11, 6, -1), rshoe=foot(51, 79, 11, 6, 1))
        P = bob(P, 3)
        P = arms(P,
                 front=A((29, 55), (22, 50), (17, 44), (15, 40), 5.2, 4.0, 3.2, 3.9),
                 back=A((51, 55), (58, 50), (63, 44), (65, 40), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dy=4, rot=-6, eyes='wide', mouth='open', brows='pain',
                 cap_dx=-2, cap_dy=-3, cap_rot=-7, sweat=1)
        for (cx, cy, ang) in ((22, 26, -34), (33, 16, -12), (46, 14, 16), (58, 22, 40),
                              (68, 34, 62), (12, 38, -56), (70, 58, 82)):
            tcard(c, cx, cy, ang, 7, 11, pip='spade')
        CD.glow(c, [(40, 20, 0.30), (24, 28, 0.26), (58, 26, 0.26)], 10.0)
        sparks(c, [(40, 8, 2), (16, 20, 1), (64, 16, 1)])
    elif i == 2:
        # knees going, cards at the top of their arc
        P = legs(B,
                 l=L((33, 66), (28, 72), (27, 77), 5.6, 4.8, 4.0),
                 r=L((47, 67), (52, 72), (51, 77), 5.3, 4.6, 3.9),
                 lshoe=foot(27, 79, 12, 5, -1), rshoe=foot(51, 79, 12, 5, 1))
        P = bob(P, 7)
        P = arms(P,
                 front=A((29, 59), (22, 58), (16, 56), (14, 54), 5.2, 4.0, 3.2, 3.9),
                 back=A((51, 59), (58, 58), (63, 56), (65, 54), 5.0, 3.8, 3.1, 3.8))
        PS.build(c, P)
        JH.build(c, dy=8, rot=-3, eyes='shut', mouth='open', brows='pain',
                 cap_dx=-2, cap_dy=-4, cap_rot=-9, sweat=2)
        for (cx, cy, ang) in ((18, 18, -40), (30, 10, -16), (44, 8, 12), (56, 14, 34),
                              (66, 24, 58), (10, 30, -60), (72, 42, 78), (38, 26, 4)):
            tcard(c, cx, cy, ang, 7, 11, pip='spade')
        sparks(c, [(24, 6, 1), (60, 4, 1)])
    else:
        # down on his knees, cards raining; i=5 is the hold
        k = i - 3                                        # 0, 1, 2
        P = legs(B,
                 l=L((34, 67), (32, 74), (33, 77), 5.4, 5.0, 4.4),
                 r=L((46, 68), (48, 74), (47, 77), 5.2, 4.8, 4.2),
                 lshoe=[(24, 74), (34, 74), (35, 77), (33, 79), (23, 79), (22, 77)],
                 rshoe=[(45, 74), (55, 74), (57, 77), (55, 79), (45, 79), (44, 77)])
        P = with_(P,
                  torso=[(35, 52), (32, 54), (29, 56), (28, 60), (28, 64), (29, 68), (31, 71),
                         (36, 70), (41, 69), (46, 70), (51, 71), (52, 68), (52, 64), (52, 59),
                         (51, 55), (48, 53), (43, 52)],
                  tee=[(35, 54), (45, 54), (46, 61), (43, 68), (37, 68), (34, 61)],
                  collar_l=[(31, 52), (36, 55), (36, 62), (32, 62), (29, 58), (29, 53)],
                  collar_r=[(49, 52), (44, 55), (44, 62), (48, 62), (51, 58), (51, 53)],
                  collar_lining=[(34, 55, ["Qq"]), (34, 56, ["QQq"]), (35, 57, ["QQ"]), (35, 58, ["Qq"]),
                                 (35, 59, ["qq"]),
                                 (44, 55, ["qQ"]), (43, 56, ["qQQ"]), (43, 57, ["QQ"]), (43, 58, ["qQ"]),
                                 (43, 59, ["qq"])],
                  belt=(32, 48, 65),
                  coat_lines=[(31, 61, ["u"]), (31, 62, ["U"]), (31, 63, ["U"]),
                              (49, 61, ["U"]), (49, 62, ["U"])],
                  neck=[(36, 51), (44, 51), (45, 58), (35, 58)],
                  neck_axis=((40, 51), (40, 59), 4.6, 4.2))
        P = PS.trunk(P)
        P = shift(P, 0, k, keys=PS.UPPER)
        P = arms(P,
                 front=[A((30, 57), (24, 63), (22, 70), (22, 73), 5.2, 4.0, 3.2, 3.8),
                        A((30, 58), (24, 64), (23, 71), (24, 74), 5.2, 4.0, 3.2, 3.8),
                        A((30, 59), (25, 65), (25, 72), (26, 75), 5.2, 4.0, 3.2, 3.8)][k],
                 back=[A((50, 57), (56, 63), (58, 70), (58, 73), 5.0, 3.8, 3.1, 3.8),
                       A((50, 58), (56, 64), (57, 71), (56, 74), 5.0, 3.8, 3.1, 3.8),
                       A((50, 59), (55, 65), (55, 72), (54, 75), 5.0, 3.8, 3.1, 3.8)][k])
        PS.build(c, P)
        JH.build(c, dy=[11, 13, 14][k], rot=[-5, -8, -9][k],
                 eyes=['shut', 'beat', 'beat'][k], mouth=['open', 'grit', 'slack'][k],
                 brows='pain', sweat=[2, 3, 3][k],
                 cap_dx=-3, cap_dy=[-3, -2, -1][k], cap_rot=[-16, -18, -19][k])
        rain = [((14, 22, -34), (28, 16, -10), (44, 18, 16), (58, 26, 40), (68, 38, 64), (8, 44, -58)),
                ((16, 34, -28), (30, 28, -6), (46, 30, 20), (60, 38, 44), (70, 52, 68), (10, 56, -52)),
                ((18, 48, -22), (32, 44, -2), (48, 46, 24), (62, 54, 48), (72, 66, 70), (12, 68, -46))][k]
        for (cx, cy, ang) in rain:
            tcard(c, cx, cy, ang, 7, 11, pip='spade')
        if k == 2:
            CD.glow(c, [(40, 74, 0.26), (26, 76, 0.22), (56, 76, 0.22)], 8.0)
    return c


ANIMS = {
    'josh_idle': (idle, 4),
    'josh_intro': (intro, 6),
    'josh_lay_card': (lay_card, 3),
    'josh_glide': (glide, 4),
    'josh_mount': (mount, 3),
    'josh_dismount': (dismount, 3),
    'josh_drop_bomb': (drop_bomb, 3),
    'josh_throw': (throw, 4),
    'josh_show_card': (show_card, 3),
    'josh_recovery': (recovery, 4),
    'josh_hit': (hit, 2),
    'josh_defeat': (defeat, 6),
}


def sheet(name):
    fn, n = ANIMS[name]
    return [fn(i) for i in range(n)]
