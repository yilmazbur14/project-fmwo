"""The four low-rank server members who carry Liam's throne.  32x32 frames, feet on row 31 (bottom-centre anchor
(16, 31)); every carrier grips the palanquin pole at rows 11-14 so any of them can stand under either pole.
Frame order in liam_carriers.png: 0 hoodie+headset, 1 cat-ear hoodie, 2 lanky energy-drink, 3 round beanie."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grid import Grid
from pal import *
from lib import Canvas
import view

POLE_Y0, POLE_Y1 = 11, 14

BASE = {
    'k': BLACK, 'W': WHITE,
    # skin (cast ramp)
    '1': L_SKIN[0], '2': L_SKIN[1], '3': L_SKIN[2], '4': L_SKIN[3], '5': L_SKIN[4],
    # sweat, blush, mouth
    'b': SWEAT[1], 'B': SWEAT[2], 'p': BLUSH, 'm': MOUTH[1], 'M': MOUTH[2],
    # grey role tag
    'v': ROLE_GREY[1], 'V': ROLE_GREY[2], 'u': ROLE_GREY[0],
}


def cm(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


# ------------------------------------------------------------------ C1 hoodie + headset (scrawny, squatting)
C1_MAP = cm(H=HAIR_BLACK[0], h=HAIR_BLACK[1], x=HAIR_BLACK[2],
            S=HEADSET[0], s=HEADSET[1], d=HEADSET[2], c=LED[1],
            G=HOODIE_GREEN[0], g=HOODIE_GREEN[1], t=HOODIE_GREEN[2], T=HOODIE_GREEN[3], D=HOODIE_GREEN[4],
            J=DENIM[0], j=DENIM[1], n=DENIM[2], N=DENIM[3],
            w=SNEAKER[1], z=SNEAKER[2])


def c1_grid():
    g = Grid(32, 32)
    for fx in (5, 22):
        g.put(fx + 1, 10, "kkk")
        g.put(fx, 11, "k122k")
        g.put(fx, 12, "k223k")
        g.put(fx, 13, "k334k")
        g.put(fx, 14, "kk4kk")
    # sleeves: wrist -> elbow (out) -> shoulder (in)
    g.put(5, 15, "kGgtk")
    g.put(4, 16, "kGgtk")
    g.put(3, 17, "kGgtk")
    g.put(3, 18, "kGgtk")
    g.put(2, 19, "kGggtk")
    g.put(3, 20, "kGgtTk")
    g.put(4, 21, "ktgtTk")
    g.put(5, 22, "ktgTTk")
    g.put(22, 15, "kGgtk")
    g.put(23, 16, "kGgtk")
    g.put(24, 17, "kGgtk")
    g.put(24, 18, "kGgtk")
    g.put(24, 19, "kGgtTk")
    g.put(23, 20, "kgttTk")
    g.put(22, 21, "ktgtTk")
    g.put(21, 22, "ktgTTk")
    # head + headset (band flattened under the pole)
    g.put(11, 14, "kkkkkkkkkk")
    g.put(10, 15, "kSSsssssssdk")
    g.put(9, 16, "kdhHhhHhhhxhdk")
    g.put(9, 17, "kdHhhHhhhhxhdk")
    g.put(8, 18, "kSshh22222hhhsdk")
    g.put(8, 19, "kSs2kk2222kk3sdk")
    g.put(8, 20, "kcs222k22k233ddk")
    g.put(9, 21, "kk2pkWWWWkp3kk")
    g.put(10, 22, "k333kkkk344k")
    g.put(11, 23, "kkkkkkkkkk")
    # torso (hoodie) + grey role pill
    g.put(6, 23, "ktgTg")
    g.put(21, 23, "gTTtk")
    g.put(8, 24, "kgGgTTTTTTTTgtTk")
    g.put(9, 25, "kGgWkkkkkkWttk")
    g.put(9, 26, "kGgkuvvvvVkttk")
    g.put(9, 27, "kgggkkkkkkgtTk")
    # legs (squat, knees out)
    g.put(9, 28, "kJjjjnkkJjjjnk")
    g.put(7, 29, "kJjjnk")
    g.put(19, 29, "kJjjnk")
    g.put(6, 30, "kWWwwzk")
    g.put(19, 30, "kWWwwzk")
    g.put(6, 31, "kkkkkkk")
    g.put(19, 31, "kkkkkkk")
    return g


# ------------------------------------------------------------------ C2 cat-ear hoodie girl (arms straight up)
C2_MAP = cm(A=HOODIE_PINK[0], a=HOODIE_PINK[1], c=HOODIE_PINK[2], C=HOODIE_PINK[3], D=HOODIE_PINK[4],
            H=HAIR_BROWN[0], h=HAIR_BROWN[1], x=HAIR_BROWN[2],
            L=DARKCLOTH[0], l=DARKCLOTH[1], n=DARKCLOTH[2], N=DARKCLOTH[3],
            w=SNEAKER[1], z=SNEAKER[2], e=MOUTH[0])


def c2_grid():
    g = Grid(32, 32)
    # sweater paws on the pole (fingertips peeking over)
    for fx in (6, 21):
        g.put(fx + 1, 10, "kkk")
        g.put(fx, 11, "k2k2k")
        g.put(fx, 12, "kAaak")
        g.put(fx, 13, "kaack")
        g.put(fx, 14, "kaaCk")
    # sleeves straight down to the shoulders
    for y in range(15, 23):
        g.put(6, y, "kAack")
        g.put(21, y, "kacCk")
    # cat ears standing up in front of the pole
    g.rows(10, 10, """
 k
 kk
 kek
 kAek
kAaaek""")
    g.rows(16, 10, """
     k
    kk
   keCk
  keCCk
 keccCk""")
    # hood + face
    g.put(10, 15, "kAaaaaaaacCk")
    g.put(10, 16, "kAaaaaaaacCk")
    g.put(10, 17, "kAaHHhhhhcCk")
    g.put(10, 18, "kaHh2hh2hxCk")
    g.put(10, 19, "ka2k2222k3Ck")
    g.put(10, 20, "ka22k22k23Ck")
    g.put(10, 21, "kcpk2222kpCk")
    g.put(10, 22, "kc322mm334Ck")
    g.put(10, 23, "kckkkkkkkkDk")
    # oversized hoodie (A-line) + grey role pill
    g.put(8, 23, "kAk")
    g.put(21, 23, "kCk")
    g.put(7, 24, "kAaaaaaaaaaaaacCk")
    g.put(7, 25, "kAaaakWvvvVkaacCk")
    g.put(7, 26, "kAaaaakkkkkkaacCk")
    g.put(6, 27, "kAaaaaaaaaaaaaacCk")
    g.put(6, 28, "kkkkkkkkkkkkkkkkkk")
    # leggings + sneakers
    g.put(10, 29, "kLlnk")
    g.put(17, 29, "kLlnk")
    g.put(9, 30, "kWWwzk")
    g.put(17, 30, "kWWwzk")
    g.put(9, 31, "kkkkkk")
    g.put(17, 31, "kkkkkk")
    return g


# ------------------------------------------------------------------ C3 tall lanky energy-drink guy (one hand on the pole)
C3_MAP = cm(H=HAIR_BLOND[0], h=HAIR_BLOND[1], x=HAIR_BLOND[2], X=HAIR_BLOND[3],
            O=TEE_ORANGE[0], o=TEE_ORANGE[1], r=TEE_ORANGE[2], R=TEE_ORANGE[3],
            Q=KHAKI[0], q=KHAKI[1], y=KHAKI[2], Y=KHAKI[3],
            G=CAN[0], g=CAN[1], t=CAN[2], T=CAN[3], s=L_STEEL[1],
            w=SNEAKER[1], z=SNEAKER[2])


def c3_grid():
    g = Grid(32, 32)
    # gripping hand + forearm up (the rear pole ends in his fist, coming in from the right)
    g.put(21, 10, "kkk")
    g.put(20, 11, "k122k")
    g.put(20, 12, "k223k")
    g.put(20, 13, "k334k")
    g.put(20, 14, "kk34k")
    g.put(20, 15, "k234k")
    g.put(19, 16, "kk234k")
    g.put(16, 17, "kOork34k")
    g.put(16, 18, "kkkkkkk")
    # messy blond mop, bored half-lidded eyes, sweat drop
    g.rows(7, 2, """
  k  kk
 kHk kHk k
kHHhkHhhkhk
kHhhhhhxhhk
kHhHhhxhhxhk
khhxhhhhxhxk
kh2h22h2hhxk
kx22222223xk
k2kkk22kkk3k
k2k2k22k2k3k
k222223223bk
k332kkkk334k
 k33333344k
  kk444kk""")
    # energy drink raised to the mouth
    g.put(3, 9, "kkkk")
    g.put(2, 10, "ksssk")
    g.put(2, 11, "kGgtk")
    g.put(2, 12, "kgkTk")
    g.put(1, 13, "k2gtTk")
    g.put(1, 14, "k23tTk")
    g.put(2, 15, "kGgtk")
    g.put(2, 16, "kkkkk")
    # can arm (elbow down)
    g.put(2, 17, "k23k")
    g.put(3, 18, "k34k")
    g.put(4, 19, "kOork")
    # tee
    g.put(8, 16, "kOooooork")
    g.put(7, 17, "kOoooooorRk")
    g.put(6, 18, "kOOoooooorRk")
    g.put(7, 19, "kOooookWvVkk")
    g.put(8, 20, "kOoookkkkRk")
    g.put(8, 21, "kOoooooorRk")
    g.put(8, 22, "kooooooorRk")
    g.put(8, 23, "kkkkkkkkkkk")
    # cargo shorts
    g.put(8, 24, "kQqqqkqqyYk")
    g.put(8, 25, "kqqyykkqyYk")
    g.put(8, 26, "kkkkk.kkkkk")
    # long legs, knees bent
    g.put(8, 27, "k23k")
    g.put(14, 27, "k34k")
    g.put(7, 28, "k23k")
    g.put(15, 28, "k34k")
    g.put(7, 29, "k23k")
    g.put(15, 29, "k34k")
    g.put(5, 30, "kWWwzk")
    g.put(14, 30, "kWWwzk")
    g.put(5, 31, "kkkkkk")
    g.put(14, 31, "kkkkkk")
    return g


# ------------------------------------------------------------------ C4 short round beanie guy (tiptoes, stubby arms up)
C4_MAP = cm(**{'1': SKIN_TAN[0], '2': SKIN_TAN[1], '3': SKIN_TAN[2], '4': SKIN_TAN[3], '5': SKIN_TAN[4]},
            R=BEANIE_RED[0], r=BEANIE_RED[1], d=BEANIE_RED[2], D=BEANIE_RED[3],
            Y=SHIRT_YELLOW[0], y=SHIRT_YELLOW[1], o=SHIRT_YELLOW[2], O=SHIRT_YELLOW[3],
            G=GREYSWEAT[0], g=GREYSWEAT[1], t=GREYSWEAT[2], T=GREYSWEAT[3],
            w=SNEAKER[1], z=SNEAKER[2], P=WHITE, e=SNEAKER[1])


def c4_grid():
    g = Grid(32, 32)
    # arms straight up to the pole, a gap of air between arms and head
    g.put(5, 10, "kkk")
    g.put(24, 10, "kkk")
    for y, s in ((11, "k122k"), (12, "k223k"), (13, "k233k")):
        g.put(4, y, s)
        g.put(23, y, s)
    for y in range(14, 23):
        g.put(4, y, "k123k")
        g.put(23, y, "k123k")
    g.put(4, 23, "kYyok")
    g.put(23, 23, "kyoOk")
    g.put(4, 24, "kYyok")
    g.put(23, 24, "kyoOk")
    # pom-pom poking up in front of the pole
    g.put(15, 8, "kk")
    g.put(14, 9, "kWWk")
    g.put(13, 10, "kWWWek")
    g.put(13, 11, "kWWWek")
    g.put(13, 12, "kWWeek")
    g.put(13, 13, "kWeeek")
    # beanie squashed under the pole, folded cuff
    g.put(11, 14, "kkkkkkkkkk")
    g.put(11, 15, "kRrrrrrrdk")
    g.put(11, 16, "kRrrrrrddk")
    g.put(11, 17, "kkkkkkkkkk")
    g.put(11, 18, "kRRrrrrrdk")
    g.put(10, 19, "kkkkkkkkkkkk")
    g.put(9, 19, "k")
    g.put(22, 19, "k")
    # big round face: squeezed eyes, puffed red cheeks, lips pressed
    g.put(9, 20, "k22k222222k23k")
    g.put(9, 21, "k222k2222k223k")
    g.put(9, 22, "kppk222222kppk")
    g.put(9, 23, "k2p22kkkk22p3k")
    g.put(9, 24, "kk3222222234kk")
    # round belly, yellow tee, grey role pill
    g.put(4, 25, "kYyyyykkkkkkkkkkkkyyyoOk")
    g.put(3, 26, "kYYyyyyyykWvvVkyyyyyyooOk")
    g.put(2, 27, "kYYyyyyyyykkkkkkyyyyyyyooOk")
    g.put(3, 28, "kyyyyyyyyyyyyyyyyyyyyyoOk")
    g.put(5, 29, "kkkkkkkkkkkkkkkkkkkkkk")
    # stubby legs on tiptoe
    g.put(10, 30, "kGgk")
    g.put(18, 30, "kgtk")
    g.put(10, 31, "kWzk")
    g.put(18, 31, "kWzk")
    # sweat flying
    g.put(29, 16, "b")
    g.put(29, 17, "B")
    g.put(2, 18, "b")
    return g


CARRIERS = [(c1_grid, C1_MAP), (c2_grid, C2_MAP), (c3_grid, C3_MAP), (c4_grid, C4_MAP)]


def build_all():
    return [f().canvas(m) for f, m in CARRIERS]


# ------------------------------------------------------------------ C1 march cycle (4 frames, fists locked to the pole)
def _c1_body(dy):
    """C1 without legs; the body (rows 15+) dropped by dy with the forearms stretched to keep the fists on the pole"""
    base = c1_grid()
    base.clear(0, 28, 31, 31)
    base.clear(6, 29, 25, 31)
    out = Grid(32, 32)
    for y in range(0, 15):
        for x in range(32):
            out.g[y][x] = base.g[y][x]
    for y in range(15, 32):
        for x in range(32):
            ch = base.get(x, y - dy) if y - dy >= 15 else '.'
            if ch != '.':
                out.g[y][x] = ch
    if dy:
        # stretched forearm rows directly under the fists
        out.put(5, 15, "kGgtk")
        out.put(22, 15, "kGgtk")
        out.clear(10, 14, 21, 14)
    return out


# legs per frame, drawn from the hip row down (hip row = 28 + dy)
WALK_LEGS = [
    # 0: contact, left foot planted forward, right heel lifted behind (body down 1)
    (1, [(9, 29, "kJjjjnkkJjjjnk"),
         (6, 30, "kWWwwzk"), (19, 30, "kJjnk"),
         (6, 31, "kkkkkkk"), (19, 31, "kWzkk")]),
    # 1: passing, right knee lifted, left leg straight (body up)
    (0, [(9, 28, "kJjjjnkkJjjjnk"),
         (8, 29, "kJjjnk"), (19, 29, "kWWwwzk"),
         (7, 30, "kWWwwzk"), (19, 30, "kkkkkkk"),
         (7, 31, "kkkkkkk")]),
    # 2: contact, right foot planted forward, left heel lifted behind (body down 1)
    (1, [(9, 29, "kJjjjnkkJjjjnk"),
         (8, 30, "kJjnk"), (19, 30, "kWWwwzk"),
         (8, 31, "kkWzk"), (19, 31, "kkkkkkk")]),
    # 3: passing, left knee lifted, right leg straight (body up)
    (0, [(9, 28, "kJjjjnkkJjjjnk"),
         (6, 29, "kWWwwzk"), (18, 29, "kJjjnk"),
         (6, 30, "kkkkkkk"), (18, 30, "kWWwwzk"),
         (18, 31, "kkkkkkk")]),
]


def c1_walk():
    frames = []
    for i, (dy, legs) in enumerate(WALK_LEGS):
        g = _c1_body(dy)
        for x, y, s in legs:
            g.put(x, y, s)
        # sweat flicks off on the up-beats
        if i == 1:
            g.put(27, 13, "b")
            g.put(28, 12, "B")
        if i == 3:
            g.put(3, 13, "b")
            g.put(2, 12, "B")
        frames.append(g.canvas(C1_MAP))
    return frames


def pole_preview(cv):
    """copy with a pole drawn behind the sprite at the grip rows (preview only)"""
    out = Canvas(cv.w, cv.h)
    for x in range(cv.w):
        out.put(x, POLE_Y0, BLACK)
        out.put(x, POLE_Y1, BLACK)
        out.put(x, POLE_Y0 + 1, WOOD[1])
        out.put(x, POLE_Y0 + 2, WOOD[2])
    out.blit(cv)
    return out


if __name__ == '__main__':
    cvs = build_all()
    view.row([pole_preview(c) for c in cvs], 10, 'carriers_10x.png')
    print('ok')
