"""Swallow: 3 key frames (bixby_swallow_keys.png), same 128x96 layout as the slap frames.
  0 LUNGE  middle head shoots out on a stretched neck, jaws gaping over a startled Liam
  1 CHOMP  jaws clamped on Liam, his chunky legs kicking out of the mouth (refines bixby_swallow_draft.png)
  2 GULP   head back in place, Liam-shaped lump sliding down the throat, glasses flipping away,
           the headband left snagged on the middle head (sets up the approved beast design)"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
from liamkit import *
import bixby_faces
from bixby_faces import BX as BXMAP
import poses
import fx
import view

FW, FH = 128, 96
BX, BY = 4, 32
LX, LY = 58, 32

MAW = ramp('ac3232', '6e1e22', '4a1420', '2a0a14')
EAR = B_EAR


def bixby():
    return from_png(BIX_PNG)


# ------------------------------------------------------------------ open-jaw head (local canvas 56x52)
def jaw_head():
    cv = Canvas(56, 52)
    src = bixby()
    cx = 28
    for side in (-1, 1):
        ear = poly([(cx + side * 9, 6), (cx + side * 17, 5), (cx + side * 27, 12), (cx + side * 26, 20),
                    (cx + side * 20, 24), (cx + side * 14, 20), (cx + side * 10, 14)])
        cv.part(ear, EAR, ('dist', 3, 0.3), [9.0, 0.8, 0.5, 0.2])
    jaw = ell(cx, 30, 15.5, 15) | ell(cx, 22, 13, 8)
    cv.part(jaw, B_TAN, ('sphere', cx - 4, 24, 20, 20, 0.2), [9.0, 0.82, 0.5, 0.2])
    chin = ell(cx, 38, 12, 7.5)
    cv.part(chin, B_FUR, ('sphere', cx - 3, 36, 14, 10, 0.2), [0.95, 0.72, 0.42, 0.15])
    maw = ell(cx, 30, 11.5, 10.5)
    for (x, y) in maw:
        d = math.hypot((x + 0.5 - cx) / 11.5, (y + 0.5 - 31) / 10.5)
        cv.put(x, y, MAW[3] if d < 0.45 else (MAW[2] if d < 0.72 else MAW[1]))
    for (x, y) in edge(maw):
        if y < 30:
            cv.put(x, y, MAW[0])
    cv.outline(dilate(maw, 1) - maw | edge(maw) & {(x, y) for (x, y) in maw if y >= 30})
    tongue = ell(cx + 1, 37, 7.5, 3.6)
    cv.part(tongue, B_TONGUE, ('sphere', cx - 1, 35.5, 9, 5), [0.9, 0.55, 0.2])
    cv.put(cx + 1, 36, B_TONGUE[2])
    cv.put(cx + 1, 37, B_TONGUE[2])
    fang_dn = "kkk\nkWk\nkWk\n.k."
    fang_up = ".k.\nkWk\nkWk\nkkk"
    for fxp in (cx - 9, cx + 7):
        cv.stamp(fang_dn, fxp, 20, BXMAP)
        cv.stamp(fang_up, fxp, 37, BXMAP)
    for tx in (cx - 5, cx - 2, cx + 1, cx + 4):
        cv.stamp("kWk\n.k.", tx, 20, BXMAP)
    for y in range(1, 18):
        for x in range(23, 41):
            c = src.get(x, y)
            if c is not None:
                cv.put(x - 31 + cx, y + 2, c)
    ox, oy = cx - 31, 2
    bixby_faces.clear_mid_eyes(cv, ox, oy)
    bixby_faces.st(cv, ox, oy, 23, 7, "kkk....\n.kkkkk.\n.kWWYk.\n..kkk..")
    bixby_faces.st(cv, ox, oy, 34, 7, "....kkk\n.kkkkk.\n.kYWWk.\n..kkk..")
    close_outline(cv)
    return cv


def neck(cv, pts, r0, r1):
    """curved neck: tan back fur on the upper side, white throat fur underneath"""
    m = tube(pts, (r0, r1))
    path = catmull(pts, 10)
    n = len(path)
    for (x, y) in m:
        k = min(range(n), key=lambda i: (path[i][0] - x - 0.5) ** 2 + (path[i][1] - y - 0.5) ** 2)
        i0, i1 = max(0, k - 1), min(n - 1, k + 1)
        tx, ty = path[i1][0] - path[i0][0], path[i1][1] - path[i0][1]
        nx, ny = ty, -tx
        side = (x + 0.5 - path[k][0]) * nx + (y + 0.5 - path[k][1]) * ny
        d = math.hypot(x + 0.5 - path[k][0], y + 0.5 - path[k][1])
        r = r0 + (r1 - r0) * k / n
        if side > 0.2:
            cv.put(x, y, B_TAN[1] if d < r * 0.55 else B_TAN[2])
        else:
            cv.put(x, y, B_FUR[1] if d < r * 0.45 else (B_FUR[2] if d < r * 0.8 else B_FUR[3]))
    cv.outline(m)
    return m


def collar_band(cv, p, ang, r):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    a = (p[0] - ca * r, p[1] - sa * r)
    b = (p[0] + ca * r, p[1] + sa * r)
    m = capsule(a, b, 2.6)
    cv.part(m, B_COLLAR, ('cyl', a, b, 2.8, 0.2), [9.0, 0.7, 0.3])
    for t in (0.25, 0.5, 0.75):
        cv.put(int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), B_IRON[0])


def bixby_headless():
    """bixby.png with the middle head, its ears and collar removed; the side heads get their far ears back"""
    cv = bixby()
    for y in range(0, 36):
        for x in range(18, 46):
            if y <= 28 or x <= 22 or x >= 40:
                cv.put(x, y, None)
    for pts in ([(15, 14), (21, 13), (23, 22), (21, 33), (16, 30)], [(47, 14), (41, 13), (39, 22), (41, 33), (46, 30)]):
        m = poly(pts)
        cv.part(m, EAR, ('dist', 2.5, 0.3), [9.0, 0.8, 0.5, 0.2])
    chest = ell(31, 34, 9, 6)
    cv.part(chest, B_FUR, ('sphere', 29, 32, 11, 8, 0.2), [0.95, 0.72, 0.42, 0.15])
    return cv


GASP = """
.kkkkkk.
kMMMMMMk
kMmmmmMk
.kkkkkk.
"""


def frame_lunge():
    cv = Canvas(FW, FH)
    cv.blit(bixby_headless(), BX, BY)
    li = Canvas(FW, FH)
    li.blit(load_liam(), LX + 3, LY)
    li.stamp(GASP, LX + 3 + 22, LY + 21, {'k': BLACK, 'M': L_MOUTH[1], 'm': L_MOUTH[0]})
    cv.blit(li)
    head = jaw_head()
    hx, hy = 36, -4
    neck(cv, [(BX + 31, BY + 36), (BX + 33, BY + 22), (BX + 42, BY + 12), (hx + 25, hy + 42)], 6.5, 7.5)
    collar_band(cv, (hx + 22, hy + 46), 35, 8)
    cv.blit(head, hx, hy)
    for (x0, y0) in ((24, 36), (20, 44), (28, 28)):
        fx.speed_line(cv, x0, y0, x0 + 9, y0 - 7, WHITE)
    fx.lettering(cv, '!', LX + 44, LY - 14, bounce=(0,))
    fx.lettering(cv, '!', LX + 49, LY - 12, bounce=(0,))
    fx.sweat(cv, LX + 44, LY + 6)
    fx.sweat(cv, LX + 8, LY + 18)
    return cv


# ------------------------------------------------------------------ CHOMP
PANTS_MAP = {'k': BLACK, 'p': L_PANTS[0], 'q': L_PANTS[1], 'Q': L_PANTS[2], 'z': L_PANTS[3],
             'o': L_SHOES[0], 'O': L_SHOES[1], 'x': L_SHOES[2], 'N': L_JACKET[4], 'm': L_STEEL[0], 'M': L_STEEL[1],
             'e': L_STEEL[2], 'T': L_TIE[1], 'y': L_TIE[2], 'W': WHITE, 'l': L_LENS[1]}

SOLE_L = """
.kkkkkkkk..
kxxxxxxxxk.
kOooooOOxxk
kOOoooOOOxk
.kkOOOOkkk.
...kkkk....
"""
SOLE_R = """
..kkkkkkkk.
.kxxxxxxxxk
kxxOOooooOk
kxOOOoooOOk
.kkkOOOOkk.
....kkkk...
"""
GLASSES = """
kkkkkkkkkkkkk
kWWWWkkkWWWlk
kWWWlk.kWWllk
.kkkk...kkkk.
"""


def sole(cv, cx, cy, ang):
    """big brown shoe seen sole-up: rounded rim, dark tread, heel break"""
    m = ell(cx, cy, 7.8, 4.6, ang)
    cv.part(m, L_SHOES, ('sphere', cx - 2, cy - 2, 9, 6), [9.0, 0.7, 0.3])
    tread = ell(cx, cy, 5.6, 2.4, ang)
    cv.fill(tread, L_SHOES[2])
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for t in (-1.5, -0.5, 0.5):
        cv.put(int(round(cx + ca * 2.2 - sa * t)), int(round(cy + sa * 2.2 + ca * t)), L_SHOES[0])
    return m


def pants_leg(cv, pts, r):
    m = tube(pts, (r, r - 0.4))
    cv.part(m, L_PANTS, ('dist', 3.2, 0.3), [9.0, 0.84, 0.56, 0.26, 0.05])
    return m


def frame_chomp():
    cv = Canvas(FW, FH)
    src = bixby()
    cv.blit(src, BX, BY)

    def st(x, y, g):
        bixby_faces.st(cv, BX, BY, x, y, g)
    # hamster-stuffed cheeks: Liam's whole top half is in there
    stuffed = ell(BX + 31.5, BY + 19, 15.5, 9.5)
    cv.part(stuffed, B_TAN, ('sphere', BX + 27, BY + 15, 19, 13, 0.1), [9.0, 0.84, 0.55, 0.22])
    muzzle = ell(BX + 31.5, BY + 21, 10.5, 6.5)
    cv.part(muzzle, B_FUR, ('sphere', BX + 29, BY + 19, 12, 9, 0.2), [0.95, 0.72, 0.42, 0.15])
    for y in range(13, 18):
        for x in range(28, 35):
            c = src.get(x, y)
            if c is not None:
                cv.put(BX + x, BY + y - 1, c)
    # lips pressed tight across the bulge
    st(24, 23, "kkkkkkkkkkkkkkkk")
    st(23, 22, "k")
    # squeezed eyes pushed up by the cheeks, effort sweat
    bixby_faces.clear_mid_eyes(cv, BX, BY)
    st(23, 8, "k....")
    st(23, 9, ".kkk.")
    st(23, 10, "....k")
    st(35, 8, "....k")
    st(35, 9, ".kkk.")
    st(35, 10, "k....")
    # headband tail poking out of the left corner
    cv.stamp("..kk\n.kTk\nkTyk\nkTk.\nkyk.\nkk..", BX + 13, BY + 21, PANTS_MAP)
    # legs kicking out of the right corner of the mouth, belt caught between the lips
    legs = Canvas(FW, FH)
    pants_leg(legs, [(BX + 42, BY + 22), (BX + 47, BY + 10), (BX + 48, BY - 4)], 5.0)
    pants_leg(legs, [(BX + 44, BY + 23), (BX + 56, BY + 15)], 5.0)
    pants_leg(legs, [(BX + 56, BY + 15), (BX + 67, BY + 8)], 4.6)
    sole(legs, BX + 48, BY - 9, -85)
    sole(legs, BX + 71, BY + 5, 30)
    legs.stamp("kkkkkkk\nkNmmMNk\nkkMekkk", BX + 37, BY + 21, PANTS_MAP)
    cv.blit(legs)
    # side heads: left smug, right startled
    st(10, 23, "kk.....kk")
    st(10, 24, "YY.....YY")
    st(5, 30, "kWkkkkkkkk")
    st(44, 21, ".kk.....kk.")
    st(44, 22, "kWWk...kWWk")
    st(44, 23, "kWkk...kkWk")
    st(44, 24, ".kk.....kk.")
    fx.motion_arc(cv, BX + 48, BY - 9, 12, 190, 270, 1, WHITE)
    fx.motion_arc(cv, BX + 71, BY + 5, 12, -60, 30, 1, WHITE)
    cv.stamp(GLASSES, LX + 20, LY + 38, PANTS_MAP)
    fx.speed_line(cv, LX + 18, LY + 34, LX + 12, LY + 28, WHITE)
    fx.speed_line(cv, LX + 35, LY + 34, LX + 41, LY + 28, WHITE)
    fx.sweat(cv, BX + 12, BY + 2)
    fx.sweat(cv, BX + 50, BY + 30)
    w = fx.text_width('CHOMP!')
    fx.lettering(cv, 'CHOMP!', 96 - w // 2, 8)
    return cv


# ------------------------------------------------------------------ GULP
HEADBAND_ON_BIX = """
..kkkkkkkkkkkkkkkkk.....
.kTTTTkmmmMMMMMkTTTTkkk.
kTyyyykmMMMMMMekyyyyTTTk
kkkkkkkMeeeeeeEkkkkkyyyk
......kkkkkkkkk....kkTyk
....................kTyk
...................kTyk.
..................kTyk..
..................kkk...
"""

GLASSES_FLIP = """
.kkkk.
kWWWlk
kWWllk
.kkkkk
.kWWlk
kWWWlk
.kkkk.
"""


def frame_gulp():
    cv = Canvas(FW, FH)
    cv.blit(bixby(), BX, BY)

    def st(x, y, g):
        bixby_faces.st(cv, BX, BY, x, y, g)
    bixby_faces.clear_mid_eyes(cv, BX, BY)
    st(24, 10, ".kk.")
    st(24, 11, "k..k")
    st(35, 10, ".kk.")
    st(35, 11, "k..k")
    st(28, 19, "wkkkkkv")
    st(28, 20, "vvvvvvv")
    lump = ell(BX + 31.5, BY + 42, 8.5, 7.5) | ell(BX + 31.5, BY + 34, 5.5, 4.5)
    cv.part(lump, B_FUR, ('sphere', BX + 29, BY + 39, 11, 11, 0.1), [0.95, 0.72, 0.42, 0.15])
    for (x0, y0, x1, y1) in ((BX + 20, BY + 38, BX + 15, BY + 36), (BX + 20, BY + 45, BX + 15, BY + 46),
                             (BX + 43, BY + 38, BX + 48, BY + 36), (BX + 43, BY + 45, BX + 48, BY + 46)):
        fx.speed_line(cv, x0, y0, x1, y1, BLACK)
    # first glowing cracks: the change is starting
    cracks = [[(2, 30), (3, 31), (3, 32), (4, 33), (4, 34)], [(2, 38), (3, 39), (4, 40), (5, 40)],
              [(47, 41), (48, 42), (49, 42), (50, 43)], [(52, 38), (53, 39), (54, 39)], [(9, 43), (10, 44), (11, 44)]]
    for cr in cracks:
        for i, (x, y) in enumerate(cr):
            c = cv.get(BX + x, BY + y)
            if c is not None and c != BLACK:
                cv.put(BX + x, BY + y, LAVA[3] if i in (0, len(cr) - 1) else LAVA[2])
    # side heads do a double take at the middle head
    st(10, 23, "kk.....kk")
    st(10, 24, "WY.....WY")
    st(44, 21, ".kk.....kk.")
    st(44, 22, "kYWk...kYWk")
    st(44, 23, "kWWk...kWWk")
    st(44, 24, ".kk.....kk.")
    fx.lettering(cv, '?', BX - 1, BY + 4, bounce=(0,), fill=(WHITE, WHITE, SWEAT[1]), shadow=SWEAT[2])
    fx.lettering(cv, '!', BX + 60, BY + 4, bounce=(0,), fill=(WHITE, WHITE, SWEAT[1]), shadow=SWEAT[2])
    tie = {'k': BLACK, 'T': L_TIE[1], 'y': L_TIE[2], 'm': L_STEEL[0], 'M': L_STEEL[1], 'e': L_STEEL[2], 'E': L_STEEL[3]}
    cv.stamp(HEADBAND_ON_BIX, BX + 20, BY + 2, tie)
    cv.stamp(GLASSES, LX + 16, LY - 6, PANTS_MAP)
    fx.motion_arc(cv, LX + 22, LY + 7, 11, 200, 262, 1, WHITE)
    fx.motion_arc(cv, LX + 22, LY + 7, 8, 208, 255, 1, WHITE, dashed=True)
    w = fx.text_width('GULP!')
    fx.lettering(cv, 'GULP!', 92 - w // 2, 8)
    return cv


def build():
    return [frame_lunge(), frame_chomp(), frame_gulp()]


if __name__ == '__main__':
    fr = build()
    view.row(fr, 4, 'swallow_keys_4x.png', panel=view.FLOOR)
    for i, f in enumerate(fr):
        view.zoom(f, 6, 'swallow_%d_6x.png' % i, bg=view.FLOOR)
    print('ok')
