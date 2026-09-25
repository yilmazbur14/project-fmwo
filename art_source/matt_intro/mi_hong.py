"""Hong: Matt's stress toy, "just a regular male doll". An original, generic little figure (no toy
brand): short dark hair with a straight fringe, a blank face (two dot eyes, nothing else), a plain
white tee with short sleeves, charcoal trousers and black shoes. 19 texels tall, 12 wide, so about
a fifth of Matt's height in his fist and readable at game scale. Every colour is one of Matt's
approved palette keys (hair ramp, skin ramp, whites, charcoal); keylined like everything else, lit
from the upper left.

Each pose is (rows, grip): grip is the (col, row) of the doll pixel his fist closes round (his
thighs, so the head and tee stay in view), which the doll frames place on the fist's centre.

    python mi_hong.py        # check widths, render every pose (and in the fist) at 12x
"""
import mi_base as B

# standing / dangling: arms down at his sides, legs together
STAND = ([
    # 0123456789ab
    "...kkkkkk...",   # 0
    "..kjjiiiik..",   # 1  hair, lit on the left
    ".kjiiiiiihk.",   # 2
    ".kiikkkkihk.",   # 3  the fringe's straight edge
    ".kh122223hk.",   # 4
    ".kh1k22k3hk.",   # 5  dot eyes
    ".k12222233k.",   # 6
    "..k222233k..",   # 7  chin
    "..kkkkkkkk..",   # 8
    ".kWWWWWWWXk.",   # 9  plain tee, short sleeves
    "k1kWWWWWXk3k",   # 10 arms at his sides
    "k2kWWWWXXk4k",   # 11
    "k2kXXXXXxk4k",   # 12
    "k2kkkkkkkk4k",   # 13 hands; hem
    ".kkNNMMLLkk.",   # 14 trousers
    "..kNMkkMLk..",   # 15
    "..kNMkkLKk..",   # 16
    ".kKKKkkKKKk.",   # 17 shoes
    ".kkkkkkkkkk.",   # 18
], (5, 16))

# shaken: arms flung up, legs kicked apart
FLAIL_A = ([
    # 0123456789abcd
    ".k..........k.",  # -  fingertips' keyline
    "k2k.kkkkkk.k4k",  # 0  hands up past his head
    "k1kkjjiiiikk3k",  # 1
    "k1kjiiiiiihk3k",  # 2
    ".kkiikkkkihkk.",  # 3
    "..kh122223hk..",  # 4
    "..khk22k33hk..",  # 5  eyes squeezed to lines by the shaking
    "..k12222233k..",  # 6
    "...k222233k...",  # 7
    "...kkkkkkkk...",  # 8
    "..kWWWWWWWXk..",  # 9  sleeves up with the arms
    "...kWWWWWXk...",  # 10
    "...kWWWWXXk...",  # 11
    "...kXXXXXxk...",  # 12
    "...kkkkkkkk...",  # 13 hem
    "..kkNNMMLLkk..",  # 14
    ".kNMkk..kkLKk.",  # 15 legs flung apart
    "kNMk......kLKk",  # 16
    "kKKk......kKKk",  # 17 shoes
    "kkk........kkk",  # 18
], (6, 16))

# shaken the other way: arms thrown out flat, legs swung to one side
FLAIL_B = ([
    # 0123456789abcd
    "....kkkkkk....",  # 0
    "...kjjiiiik...",  # 1
    "..kjiiiiiihk..",  # 2
    "..kiikkkkihk..",  # 3
    "..kh122223hk..",  # 4
    "..kh1k22k3hk..",  # 5
    "..k12222233k..",  # 6
    "...k222233k...",  # 7
    "kkkkkkkkkkkkkk",  # 8  arms out flat
    "k12kWWWWWWXk3k",  # 9
    "kkkkWWWWWXXkkk",  # 10
    "...kWWWWXXxk..",  # 11
    "...kXXXXXxxk..",  # 12
    "...kkkkkkkkk..",  # 13 hem
    "...kNNMMLLk...",  # 14
    "....kNMkMLKk..",  # 15 legs swung to his left
    ".....kNMkLKk..",  # 16
    ".....kKKKkKKk.",  # 17
    ".....kkkkkkkk.",  # 18
], (7, 15))

POSES = {'STAND': STAND, 'FLAIL_A': FLAIL_A, 'FLAIL_B': FLAIL_B}

# He holds Hong up by the legs in his raised fist (mi_hands.FIST_UP_R, the approved fist turned
# over): the legs go into the top of the fist and everything from the trousers' waistband up stands
# clear above it. LEG_ROW is the doll row that sits on the fist's top keyline.
LEG_ROW = 14


def check():
    bad = []
    for n, (rows, g) in POSES.items():
        rs = B.rows_of(rows)
        bad += B.check_map(rows, len(rs[0]), n)
    return bad


def held(pose, fist_top_left):
    """Hong standing in the raised fist: the doll part (frame coordinates), placed so its LEG_ROW
    sits on the fist's top keyline and it is centred over the fist's 14 columns."""
    rows, _ = POSES[pose] if isinstance(pose, str) else pose
    w = len(B.rows_of(rows)[0])
    fx, fy = fist_top_left
    x0 = fx + (14 - w) // 2
    return B.amap(rows, x0, fy - LEG_ROW)


if __name__ == '__main__':
    import mi_view as V
    for line in check():
        print(line)
    ims = []
    for n, (rows, g) in POSES.items():
        w = len(B.rows_of(rows)[0]) + 2
        im = B.image(B.amap(rows, 1, 1), w, len(rows) + 2)
        ims.append(V.label(V.up(im, 12), n))
        import mi_hands as H
        cv = B.Canvas(24, 30)
        cv.stamp(held(n, (5, 17)), outline=False)
        cv.stamp(B.amap(H.FIST_UP_R[0], 5, 17), outline=False)
        ims.append(V.label(V.up(B.image(cv.px, 24, 30), 12), n + ' held'))
    print(V.save(V.row(ims), 'hong_12x.png'))
