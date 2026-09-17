"""Part B: throw_windup 32-33, throw_release 34-35, empty_wait 36-37, recall_catch 38-39."""
from base import *
import sword128

FRAMES = {}


def frame(i):
    def deco(fn):
        FRAMES[i] = fn
        return fn
    return deco


def head_edit(kind, edits):
    """copy of the head layer (96-space) with char edits [(x, y, 'chars')] ('.' = keep)."""
    key = ('headB', kind)
    if key in arig._CACHE:
        return arig._CACHE[key]
    img = [row[:] for row in arig.layers()['head']]
    for x0, y0, s in edits:
        for i, ch in enumerate(s):
            if ch != '.' and img[y0][x0 + i][3]:
                img[y0][x0 + i] = PALC[ch]
    arig._CACHE[key] = img
    return img


GRIT = [(45, 31, "eeeeee"), (45, 32, "kkkkkk")]
import sweep


def occupied(fr):
    return set((x, y) for y in range(128) for x in range(128) if fr.px[y][x] is not None)


def pose_at(hand, ang, sa, sb=1.0, grip_a=-10.0):
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    return ((hand[0] - u[0] * grip_a * sa, hand[1] - u[1] * grip_a * sa), ang, sa, sb)


def head_grit():
    return head_edit('grit', GRIT)


def head_look_left():
    return head_edit('lookL', [(40, 22, ".epp.e"), (50, 22, "..epp.")])


# ================================================================ windup
@frame(32)
def windup_heave():
    """heaves the slab back over his right shoulder: blade swings past vertical toward the far side"""
    fr = arig.Frame()
    U, S = (-1, 0), (0, 0)
    E, Hd = (20, 88), (25, 72)

    def under_paul(fr):
        upper_arm(fr, (40, 84), E)

    def first(fr):
        sweep.sweep(fr, pose_at((29, 92), -100, 0.97), pose_at(Hd, -56, 0.9), band=30.0, a_tip=80.0)
        w128()

    def before_head(fr):
        sword_at(fr, Hd, -56, sa=0.9, sb=1.0, grip_a=-10)
    body(fr, upper=U, shoulders=S, cape=(-0.8, 0.5, 0), skip=('head', 'armL_back'),
         hooks={'cape': first, 'paulL': under_paul, 'head': before_head}, off={'paulL': (0, -1)})
    head_put(fr, U, S)
    fore_arm(fr, E, Hd)
    fist(fr, Hd)
    return fr


@frame(33)
def windup_coil():
    """coiled: blade lies back over the shoulder behind his head, elbow cocked low, free fist pulled in"""
    fr = arig.Frame()
    U, S, Hx = (-1, 2), (0, 0), (-1, 1)
    E, Hd = (14, 92), (21, 78)
    E2, H2 = (116, 90), (106, 102)

    def under_paul(fr):
        upper_arm(fr, (40, 86), E)
        upper_arm(fr, (88, 86), E2)

    def before_head(fr):
        sword_at(fr, Hd, -33, sa=0.95, sb=1.0, grip_a=-10)
    body(fr, upper=U, shoulders=S, headx=Hx, cape=(-1.2, 1.0, 0), torso=(0.5, 0.5),
         skip=('head', 'armL_back', 'armR_back', 'armR_front'),
         hooks={'paulL': under_paul, 'head': before_head}, off={'paulL': (0, -2), 'paulR': (1, 1)})
    head_put(fr, U, S, Hx)
    fore_arm(fr, E, Hd)
    fist(fr, Hd, vertical=False)
    fore_arm(fr, E2, H2)
    fist(fr, H2)
    return fr


# ================================================================ release
LOB = dict(cxy=(56, 20), ang=-21, sa=0.86, sb=0.9)


@frame(34)
def release():
    """the arm whips up and over; the slab leaves his open hand, tumbling up and away"""
    fr = arig.Frame()
    U, S, Hx = (1, -2), (0, -1), (1, -1)
    E, Hd = (16, 70), (20, 51)
    E2, H2 = (112, 96), (108, 110)

    def under_paul(fr):
        upper_arm(fr, (40, 80), E)
        upper_arm(fr, (88, 84), E2)
    body(fr, upper=U, shoulders=S, headx=Hx, cape=(1.2, 0.5, 1.5),
         skip=('head', 'armL_back', 'armR_back', 'armR_front'),
         hooks={'paulL': under_paul}, off={'paulL': (0, -2)})
    head_put(fr, U, S, Hx, img=head_grit())
    cx, cy = LOB['cxy']
    ang = LOB['ang']
    sweep.sweep(fr, pose_at((34, 58), -44, 0.9, 0.9, grip_a=32), pose_at((cx, cy), ang, LOB['sa'], LOB['sb'], grip_a=32),
                band=110.0, a_tip=86.0, tail=0.35, recency=True, a_floor=-20.0, keep_out=occupied(fr))
    w128()
    sword_at(fr, (cx, cy), ang, sa=LOB['sa'], sb=LOB['sb'], grip_a=32)
    fore_arm(fr, E2, H2)
    fist(fr, H2)
    fore_arm(fr, E, Hd)
    hand(fr, 'open_up', Hd)
    return fr


@frame(35)
def follow_through():
    """empty-handed follow-through: arm swung down across his front, hand open, body bowed"""
    fr = arig.Frame()
    U, S, Hx = (2, 3), (0, 1), (1, 2)
    E, Hd = (30, 106), (46, 114)
    E2, H2 = (112, 88), (114, 72)

    def under_paul(fr):
        upper_arm(fr, (42, 88), E)
        upper_arm(fr, (88, 86), E2)

    def back(fr):
        c = cv(fr)
        bfx.crescent(c, 40, 80, 36, 40, 112, 262, 7, 0.5, dash_tail=0.0)
        w128()
    body(fr, upper=U, shoulders=S, headx=Hx, cape=(1.8, 1.0, 0.5),
         skip=('head', 'armL_back', 'armR_back', 'armR_front'),
         hooks={'cape': back, 'paulL': under_paul}, off={'paulL': (1, 1), 'paulR': (0, -1)})
    head_put(fr, U, S, Hx, img=head_grit())
    fore_arm(fr, E2, H2)
    fist(fr, H2)
    fore_arm(fr, E, Hd)
    hand(fr, 'open_fwd', Hd)
    return fr


# ================================================================ empty wait (loop)
def tremor(fr, k):
    for x, y in ([(2, 108), (124, 110)] if k == 0 else [(3, 112), (123, 107)]):
        for d in range(3):
            fr.set(x, y + d, 'W')


def wait(shake, bob, dust_left):
    fr = arig.Frame()
    U = (shake, 2 + bob)
    E, Hd = (20, 98 + bob), (30, 110 + bob)
    E2, H2 = (108, 98 + bob), (98, 110 + bob)

    def under_paul(fr):
        upper_arm(fr, (40 + shake, 88 + bob), (E[0] + shake, E[1]))
        upper_arm(fr, (88 + shake, 88 + bob), (E2[0] + shake, E2[1]))
    body(fr, upper=U, shoulders=(0, -1), headx=(0, 1), cape=(0.0, 1.5 + bob, 0),
         skip=('head', 'armL_back', 'armR_back', 'armR_front'), hooks={'paulL': under_paul},
         off={'legs': (shake, 0), 'flap': (shake, 0), 'tassets': (shake, 0)})
    head_put(fr, U, (0, -1), (0, 1), img=head_grit())
    fore_arm(fr, (E[0] + shake, E[1]), (Hd[0] + shake, Hd[1]))
    fist(fr, (Hd[0] + shake, Hd[1]))
    fore_arm(fr, (E2[0] + shake, E2[1]), (H2[0] + shake, H2[1]))
    fist(fr, (H2[0] + shake, H2[1]))
    if dust_left:
        afx.puff(fr, 4, 119)
        afx.puff(fr, 110, 122, small=True)
        afx.rock(fr, 20, 110, small=True)
        afx.rock(fr, 116, 106, small=True)
        tremor(fr, 0)
    else:
        afx.puff(fr, 114, 119)
        afx.puff(fr, 12, 122, small=True)
        afx.rock(fr, 106, 111, small=True)
        afx.rock(fr, 8, 104, small=True)
        tremor(fr, 1)
    return fr


@frame(36)
def wait0():
    return wait(0, 0, True)


@frame(37)
def wait1():
    return wait(1, 1, False)


# ================================================================ recall + catch
@frame(38)
def recall_reach():
    """raises his sword hand open to call the slab back"""
    fr = arig.Frame()
    U, S, Hx = (-1, -1), (0, 0), (-1, -1)
    E, Hd = (16, 72), (22, 52)

    def under_paul(fr):
        upper_arm(fr, (40, 82), E)
    body(fr, upper=U, shoulders=S, headx=Hx, cape=(-0.6, 0.5, 0),
         skip=('head', 'armL_back'), hooks={'paulL': under_paul}, off={'paulL': (0, -2)})
    head_put(fr, U, S, Hx, img=head_look_left())
    fore_arm(fr, E, Hd)
    hand(fr, 'open_up', Hd)
    return fr


CATCH = {}


def burst(fr, cx, cy):
    for ang, r0, ln, w in [(-150, 10, 15, 2.4), (-120, 12, 10, 1.8), (175, 10, 15, 2.4), (145, 10, 11, 1.8),
                           (-35, 12, 9, 1.6), (35, 11, 10, 1.8), (105, 9, 9, 1.6), (-80, 12, 8, 1.4)]:
        a = math.radians(ang)
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        p1 = (cx + math.cos(a) * (r0 + ln), cy + math.sin(a) * (r0 + ln))
        afx.ray(fr, p0, p1, w)
    for x, y in [(cx - 16, cy - 14), (cx + 14, cy - 12), (cx - 20, cy + 6)]:
        afx.sparkle(fr, x, y, 2)


@frame(39)
def recall_catch():
    """catches the returning slab: grip slaps into the fist with an impact burst, weight absorbs down"""
    fr = arig.Frame()
    body(fr, upper=(0, 2), cape=(-1.0, 1.5, 0))
    fdx, fdy = -1, -2
    fc = sword128.SW.P(-10.0, 0)
    cx, cy = int(round(fc[0])) + fdx, int(round(fc[1])) + fdy
    CATCH['fist_centre'] = (cx, cy)
    AW.draw(fr, dx=-1, dy=-3, arm_dx=0, arm_dy=1, fist_dx=fdx, fist_dy=fdy)
    burst(fr, cx, cy)
    return fr


def render(idx):
    return {i: FRAMES[i]().rgba() for i in idx}


if __name__ == '__main__':
    idx = [32, 33, 34, 35, 36, 37, 38, 39]
    imgs = render(idx)
    strip([approved_px()] + [imgs[i] for i in idx], 3, '../d_throw_3x.png')
    from pngio import blank, paste
    out = blank(4 * 132, 128, (40, 40, 40, 255))
    for k, i in enumerate([34, 35, 36, 39]):
        paste(out, rgba_on(imgs[i]), k * 132, 0)
    zoom(out, 4, '../d_throw_detail_4x.png')
