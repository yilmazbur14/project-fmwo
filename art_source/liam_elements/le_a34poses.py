"""Liam's poses for attacks 3 and 4 (DESIGN APPROVAL PASS): 96x96 cells, liam.png at (16, 32), anchor
(48, 96), built from his approved rig. On-pillar poses keep inside PERCH_BOX; ground poses may use the
whole cell. Each function returns [(canvas, points)] with points in cell texels.

  blow        3  inhale, BLOW (summoning the tornados), hold          on the pillar
  ignite      2  the orb catches fire, the flare                        on the pillar
  fade        3  into the steam (play backwards to reappear)            on the pillar
  lunge       4  ready, step, THRUST (bayonet, facing right), recover   ground
  impale      4  skewered, hoist, calling for Bixby x2 (staff high)     ground
  water_blast 2  aim, blast (washes the player to the bottom middle)    ground
  teleport    3  elements swirl, engulfed, gone (backwards = arrive)    ground
"""
import math

import numpy as np

import le_rig as R
import le_staff as S
import le_poses as P
import le_posedefs as D
import le_parts as X
import le_full as F

FW = FH = 96
B = F.B
lay = F.lay
comp = F.comp
add_fist = F.add_fist


def _blow_fx(cv, mouth, strength):
    """Wind streaks fanning down from his lips (his whites; inside the perch box)."""
    fx = lay()
    mx, my = mouth
    for i, ang in enumerate(range(55, 126, 14)):
        a = math.radians(ang)
        ln = strength * (0.8 + 0.2 * ((i * 7) % 3))
        for t in range(int(ln)):
            if t < 3 or (t // 3) % 3 == 2:
                continue
            x, y = mx + math.cos(a) * t, my + 2 + math.sin(a) * t
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < FW and 0 <= yi < FH:
                fx[yi, xi] = 'W' if t < ln * 0.5 else ('w' if t < ln * 0.8 else 'v')
    fx[:, :P.PERCH_BOX['left']] = '.'
    fx[:, P.PERCH_BOX['right'] + 1:] = '.'
    return comp([cv, fx])


def blow():
    out = []
    for k in range(3):
        A, st, fist, orb = F.far_staff_raised(orb='air')
        if k == 0:
            Hd, hdy, tdy, tl = X.head(X.PUFF, 'dim'), -2, -1, 'down'
        else:
            Hd, hdy, tdy, tl = X.head('blow', 'flash'), 0, 0, ('flick' if k == 1 else 'mid')
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 56, 37, 4.7, 4.0), fore=(56, 37, 60, 39, 3.8, 3.4), dy=tdy)
        cv = comp([D.tails(hdy, tl), P.place(P.legs_narrow()), P.body('torso', dy=tdy), N,
                   P.place(Hd, dy=hdy), st, A], staff=st)
        add_fist(cv, fist)
        add_fist(cv, B(61, 40 + tdy))
        mouth = B(27.5, 23 + hdy)
        if k == 0:
            fx = lay()
            for (x0, y0, x1, y1) in ((12, 22, 16, 23), (11, 25, 15, 25), (44, 22, 40, 23), (45, 25, 41, 25)):
                R.line(fx, *B(x0, y0 + hdy), *B(x1, y1 + hdy), 'w')
            cv = comp([cv, fx])
        else:
            cv = _blow_fx(cv, mouth, 30 if k == 1 else 22)
        out.append((cv, {'mouth': mouth, 'staff_tip': orb}))
    return out


def ignite():
    out = []
    for k in range(2):
        A, st, fist, orb = F.far_staff_raised(orb='fire')
        Hd = P.place(X.head('big' if k == 0 else 'shout', 'flash'), dy=-1)
        cv = comp([D.tails(-1, 'up' if k else 'mid'), P.place(P.legs_narrow()), P.body('torso'), P.body('near'), Hd,
                   st, A], staff=st)
        add_fist(cv, fist)
        ox, oy = orb
        fx = lay()
        # flames licking off the orb ring (his fire gem colours only: 6 n c W)
        n = 6 if k == 0 else 10
        for i in range(n):
            a = math.radians(200 + i * (140 / max(1, n - 1)))
            r0 = 7.5
            hgt = (3 if k == 0 else 5) + (i % 3)
            for t in range(hgt):
                x = ox + (r0 + t * 0.6) * math.cos(a)
                y = oy + (r0 + t) * math.sin(a) - t * 0.6
                xi, yi = int(round(x)), int(round(y))
                if P.PERCH_BOX['left'] <= xi <= P.PERCH_BOX['right'] and P.PERCH_BOX['top'] <= yi < FH:
                    fx[yi, xi] = ('W', 'c', '6', 'n')[min(3, t * 4 // hgt)]
        if k == 1:
            for (dx, dy) in ((-11, 2), (10, 3), (-8, 8), (9, 9)):
                xi, yi = int(ox + dx), int(oy + dy)
                if P.PERCH_BOX['left'] <= xi <= P.PERCH_BOX['right']:
                    fx[yi, xi] = '6'
                    fx[yi - 1, xi] = 'c'
        cv = comp([cv, fx])
        out.append((cv, {'staff_tip': orb}))
    return out


def fade():
    """The perch idle dissolving into steam: 0 steam curling up round him, 1 half gone (a dither), 2 all
    but gone. Played backwards it is his reappearance."""
    out = []
    base, pts = F.perch_idle()[0]
    X_, Y_ = np.meshgrid(np.arange(FW), np.arange(FH))
    for k in range(3):
        cv = base.copy()
        if k >= 1:
            keep = ((X_ + Y_) % 2 == 0) if k == 1 else (((X_ % 3) == 0) & ((Y_ % 3) == 0))
            cv[~keep & (cv != '.')] = '.'
        fx = lay()
        for (cx, cy, r) in ((34, 90, 4.0), (60, 91, 4.5), (26, 80, 3.0), (68, 82, 3.2), (47, 72, 3.6),
                            (36, 62, 3.0), (60, 58, 3.4))[:3 + k * 2]:
            D.puff(fx, cx, cy, r + k * 0.6)
        fx[:, :P.PERCH_BOX['left']] = '.'
        fx[:, P.PERCH_BOX['right'] + 1:] = '.'
        cv = comp([cv, fx]) if k else comp([fx, cv])
        out.append((cv, dict(pts)))
    return out


def lunge():
    """Facing right (mirror for left): 0 ready - crouched, staff levelled at the hip like a bayonet;
    1 the step in; 2 THRUST - fully extended, speed lines; 3 recover."""
    out = []
    specs = [  # (lean, squat, staff butt, staff head, near fist, far fist, mouth, lens, speed)
        (0, 3, (18.0, 44.0), (66.0, 44.0), (52, 44.5), (27, 44.5), X.TALK, 'flash', False),
        (2, 2, (16.0, 43.0), (64.0, 43.0), (50, 43.5), (25, 43.5), X.WINCE, 'flash', False),
        (4, 1, (23.0, 40.0), (71.0, 40.0), (57, 40.5), (33, 40.5), 'shout', 'flash', True),
        (1, 2, (19.0, 43.0), (67.0, 43.0), (53, 43.5), (28, 43.5), 'smirk', None, False),
    ]
    for (lean, sq, butt, head, nf, ff, mouth, lens, speed) in specs:
        legs = P.place(X.legs_squat(sq)) if sq else P.body('legs')
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 17, 39, 4.8, 4.2),
                  fore=(17, 39, ff[0] - lean, ff[1] - sq, 3.8, 3.5), dx=lean, dy=sq)
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 32, 55, 39, 4.7, 4.1),
                  fore=(55, 39, nf[0] - lean, nf[1] - sq, 3.8, 3.4), dx=lean, dy=sq)
        st = P.staff_line(butt, head, orb='neutral')
        Hd = P.place(X.head(mouth, lens), dx=lean + 1, dy=sq)
        cv = comp([D.tails(sq, 'flick' if speed else 'mid', dx=lean + 1), legs, P.body('torso', dx=lean, dy=sq), A,
                   Hd, st, N], staff=st)
        add_fist(cv, B(ff[0], ff[1]))
        add_fist(cv, B(nf[0], nf[1]))
        if speed:
            for (x0, y0, x1) in ((-6, 36, 6), (-4, 42, 10), (-8, 47, 4), (-2, 31, 8)):
                R.line(cv, *B(x0, y0), *B(x1, y0), 'w')
        if sq == 3:
            dust = lay()
            for (x, y, r) in ((14, 93, 3.4), (80, 93, 3.4), (8, 92, 2.2), (86, 92, 2.2)):
                D.puff(dust, x, y, r)
            cv = comp([dust, cv])
        hx, hy = B(head[0] + 0.5, head[1] + 0.5)
        out.append((cv, {'staff_tip': (hx, hy), 'point': (hx + 8, hy)}))
    return out


def impale():
    """0 skewered (the thrust, a hit spark on the point); 1 hoisting (staff swung up); 2-3 staff held high
    in both... one hand, the other cupped at his mouth, bellowing for Bixby. The player hangs on the
    staff's crown (reported as 'hang')."""
    out = []
    lunge_frames = lunge()
    cv, pts = lunge_frames[2]
    cv = cv.copy()
    hx, hy = pts['staff_tip']
    R.star(cv, int(hx) + 4, int(hy) - 1, 3, diag=1)
    out.append((cv, {'staff_tip': (hx, hy), 'hang': (hx + 8, hy)}))
    # hoist: the staff swinging up on the diagonal
    N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 56, 22, 4.6, 3.8), fore=(56, 22, 57, 12, 3.6, 3.2))
    A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 20, 34, 4.8, 4.2), fore=(20, 34, 40, 28, 3.8, 3.4))
    st = P.staff_line((36.0, 34.0), (66.0, -12.0), orb='neutral')
    cv = comp([D.tails(-1, 'up'), P.body('legs'), P.body('torso'), A, P.place(X.head(X.WINCE, 'flash'), dy=-1),
               st, N], staff=st)
    add_fist(cv, B(56.5, 10.5))
    add_fist(cv, B(42, 27))
    hx, hy = B(66.5, -11.5)
    out.append((cv, {'staff_tip': (hx, hy), 'hang': (hx, hy - 8)}))
    # calling: staff straight up in the near fist, far hand cupped at his mouth
    for k in range(2):
        hdy = -2 if k == 0 else -3
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 55, 20, 4.6, 3.8), fore=(55, 20, 55, 9, 3.6, 3.2))
        A = P.arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 9, 24, 4.6, 3.5), fore=(9, 24, 16, 21 + hdy, 3.4, 3.1))
        st = P.staff_line((55.0, 40.0), (55.0, -13.0), orb='fire')
        mouth = 'shout' if k == 0 else 'laugh'
        cv = comp([D.tails(hdy, 'flick' if k else 'up'), P.body('legs'), P.body('torso'),
                   P.place(X.head(mouth, 'flash'), dy=hdy), st, N, A], staff=st)
        add_fist(cv, B(55, 7))
        R.blk(cv, *B(13, 16 + hdy), X.BACKHAND)
        fx = lay()
        for (x0, y0, x1, y1) in ((10, 12, 6, 9), (8, 18, 3, 17), (46, 10, 49, 7)):
            R.line(fx, *B(x0, y0 + hdy), *B(x1, y1 + hdy))
        cv = comp([cv, fx])
        hx, hy = B(55.5, -12.5)
        out.append((cv, {'staff_tip': (hx, hy), 'hang': (hx, hy - 8)}))
    return out


def water_blast():
    """0 aim - the staff swung down at the player (down and to the right), orb blue; 1 the blast - a burst
    of water off the orb (the jet itself is liam_water_jet)."""
    out = []
    for k in range(2):
        N = P.arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 55, 40, 4.7, 4.1), fore=(55, 40, 60, 45, 3.8, 3.4))
        A = P.arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 20, 38, 4.8, 4.2), fore=(20, 38, 34, 36, 3.8, 3.4))
        st = P.staff_line((28.0, 30.0), (70.0, 56.0 - k), orb='water')
        cv = comp([D.tails(0, 'mid'), P.body('legs'), P.body('torso'), A, P.place(X.head('shout' if k else 'smirk', 'flash')),
                   st, N], staff=st)
        add_fist(cv, B(59.5, 46.5))
        add_fist(cv, B(36, 35.5))
        hx, hy = B(70.5, 56.5 - k)
        drip = lay()
        for (dx, dy) in ((-3, 6), (2, 7), (5, 5), (-1, 9)):
            if 0 <= int(hx + dx) < FW and 0 <= int(hy + dy) < FH:
                drip[int(hy + dy), int(hx + dx)] = 'l'
                if int(hy + dy) + 1 < FH:
                    drip[int(hy + dy) + 1, int(hx + dx)] = 'b'
        cv = comp([cv, drip])
        if k == 1:
            fx = lay()
            for i in range(8):
                a = math.radians(-40 + i * 12)
                for t in range(2, 6):
                    x, y = hx + t * math.cos(a) * 1.4, hy + t * math.sin(a)
                    if 0 <= int(x) < FW and 0 <= int(y) < FH:
                        fx[int(y), int(x)] = 'W' if t < 4 else 'l'
            cv = comp([cv, fx])
        out.append((cv, {'staff_tip': (hx, hy)}))
    return out


def teleport():
    """0 the four elements whirl up round him (water, earth, fire, air ribbons); 1 they engulf him (his
    figure breaking up); 2 gone - a last glitter of the four colours. Backwards = arriving."""
    out = []
    base = comp([D.tails(0), P.body('legs'), P.body('torso'), P.body('near')])
    A, st, fist, orb = F.far_staff_side(orb='neutral')
    base = comp([base, P.place(X.head('smirk', 'dim')), st, A], staff=st)
    add_fist(base, fist)
    X_, Y_ = np.meshgrid(np.arange(FW), np.arange(FH))
    cols = ('b', '8', '6', 'W')
    for k in range(3):
        if k == 0:
            cv = base.copy()
        elif k == 1:
            cv = base.copy()
            cv[((X_ + Y_) % 2 == 1) & (cv != '.')] = '.'
        else:
            cv = lay()
        fx = lay()
        for j, ch in enumerate(cols):
            ph = j * math.pi / 2 + k * 0.9
            for i in range(80):
                u = i / 79
                a = ph + u * math.pi * 3
                rr = 28 - u * (10 if k < 2 else 2)
                x = 48 + rr * math.cos(a)
                y = 94 - u * (58 if k < 2 else 30) + rr * 0.22 * math.sin(a)
                if math.sin(a) < 0 and k == 0:
                    continue
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < FW and 0 <= yi < FH and ((i % 4) != 3 or k == 1):
                    fx[yi, xi] = ch
        if k == 2:
            for i, (x, y) in enumerate(((30, 50), (62, 46), (40, 36), (56, 64), (34, 72), (66, 80), (48, 28))):
                fx[y, x] = cols[i % 4]
        cv = comp([cv, fx])
        out.append((cv, {}))
    return out


ALL = [('blow', blow, [0.35, 0.12, 0.25], True), ('ignite', ignite, [0.15, 0.3], True),
       ('fade', fade, [0.12, 0.12, 0.12], True), ('lunge', lunge, [0.25, 0.06, 0.18, 0.2], False),
       ('impale', impale, [0.1, 0.15, 0.3, 0.3], False), ('water_blast', water_blast, [0.15, 0.35], False),
       ('teleport', teleport, [0.1, 0.1, 0.12], False)]
