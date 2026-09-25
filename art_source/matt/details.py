"""Small parts drawn pixel by pixel: the crew collar, the shoulder speaker ports, the fists, the
striped socks and the trainers. Each map carries its own keylines and is stamped without an
outline. Left and right versions are drawn separately wherever the lighting differs, because a
mirror would move the upper-left light to the upper right.

Symmetric maps are written as a left half and a right half about column 48 (x' = 96 - x); run
this file to confirm every map's widths and that its keylines mirror.
"""
from pal import lib
from lib import amap


def halves(rows, x0):
    """rows of (left, right) strings; left runs x0 -> 48, right runs 49 -> 96 - x0.
    Returns full-width rows for amap."""
    out = []
    for l, r in rows:
        l, r = l.replace(' ', ''), r.replace(' ', '')
        assert len(l) == 49 - x0, (l, len(l))
        assert len(r) == 96 - x0 - 48, (r, len(r))
        out.append(l + r)
    return out


def check(rows, x0, name, ignore=()):
    """Widths, and keylines that are off-mirror within one map spanning the axis."""
    bad = []
    rows = [r.replace(' ', '') for r in rows]
    width = len(rows[0])
    for i, r in enumerate(rows):
        if len(r) != width:
            bad.append('%s row %d: width %d, not %d' % (name, i, len(r), width))
            continue
        if i in ignore:
            continue
        ks = {x0 + j for j, ch in enumerate(r) if ch == 'k'}
        off = sorted(x for x in ks if (96 - x) not in ks)
        if off:
            bad.append('%s row %d: unmirrored k at %s' % (name, i, off))
    return bad


def check_pair(left, lx0, right, rx0, name):
    """A left map and its separately drawn right twin: widths match, keylines mirror."""
    bad = []
    ls = [r.replace(' ', '') for r in left]
    rs = [r.replace(' ', '') for r in right]
    if len(ls) != len(rs):
        return ['%s: %d rows vs %d' % (name, len(ls), len(rs))]
    for i, (a, b) in enumerate(zip(ls, rs)):
        if len(a) != len(b) or len(a) != len(ls[0]):
            bad.append('%s row %d: widths %d / %d' % (name, i, len(a), len(b)))
            continue
        ka = {96 - (lx0 + j) for j, c in enumerate(a) if c == 'k'}
        kb = {rx0 + j for j, c in enumerate(b) if c == 'k'}
        if ka != kb:
            bad.append('%s row %d: keylines do not mirror' % (name, i))
    return bad


# ------------------------------------------------------------------ collar
# Crew collar: yellow ribbing in a U under the chin, lit along its top-left edge, darker to the
# right. The chin (drawn later) covers its middle. x 34-62, y 48-57.
COLLAR_X0, COLLAR_Y0 = 34, 48
COLLAR = halves([
    # left x 34-48       right x 49-62         y
    ("...kkk.........", "........kkk..."),     # 48
    ("..kbbck........", ".......kcddk.."),     # 49
    (".kbbccck.......", "......kcccddk."),     # 50
    (".kbcdcdck......", ".....kcdcddek."),     # 51
    ("..kbccccck.....", "....kcccddek.."),     # 52
    ("..kbbbbbbbbbbbb", "bbbbbccccdek.."),     # 53
    ("...kbcccccccccc", "cccccccddek..."),     # 54
    ("....kdddddddddd", "dddddddeek...."),     # 55
    (".....kkeeeeeeee", "eeeeeeekk....."),     # 56
    (".......kkkkkkkk", "kkkkkkk......."),     # 57
], COLLAR_X0)


# ------------------------------------------------------------------ shoulder ports
# Speaker ports: a thick yellow rim (lit top-left), a black cone, and the far inner wall catching a
# little light. Left x 20-29, right x 67-76 (mirror positions), y 53-62.
PORT_L_X0, PORT_R_X0, PORT_Y0 = 20, 67, 53
PORT_L = [
    # x: 20-24 25-29      y
    "..kkk kkk..",         # 53
    ".kaab bbck.",         # 54
    "kabkk kkcdk",         # 55
    "kbkKK KKkdk",         # 56
    "kbkKK KLkdk",         # 57
    "kckKK LMkdk",         # 58
    "kckKL MMkek",         # 59
    "kcdkk kkdek",         # 60
    ".kddd deek.",         # 61
    "..kkk kkk..",         # 62
]
PORT_R = [
    # x: 67-71 72-76      y
    "..kkk kkk..",         # 53
    ".kbbc cddk.",         # 54
    "kbckk kkdek",         # 55
    "kckKK KKkek",         # 56
    "kckKK KLkek",         # 57
    "kdkKK LMkek",         # 58
    "kdkKL MMkek",         # 59
    "kdekk kkeek",         # 60
    ".keee eeek.",         # 61
    "..kkk kkk..",         # 62
]


# ------------------------------------------------------------------ fists
# Toned by hand (too small for form shading to find the thumb): a chunky fist lit from the upper
# left, the thumb a lit pad closed off by keylines, three finger ticks along the bottom. The right
# fist mirrors the left's shape but keeps its light on the left. Left x 12-25, right x 71-84.
FIST_L_X0, FIST_R_X0, FIST_Y0 = 12, 71, 73
FIST_L = [
    # x: 12-16 17-21 22-25     y
    ".kkkk kkkkk kkk.",        # 73
    "k1112 22222 333k",        # 74  back of the hand
    "k1122 22222 334k",        # 75
    "k1222 22223 344k",        # 76
    "k1225 22523 534k",        # 77  knuckles
    "k222k 22k33 k44k",        # 78  curled fingers
    "k222k 23k33 k44k",        # 79
    "k233k 33k34 k45k",        # 80
    ".k33k 34k44 k5k.",        # 81
    "..kkk kkkkk kk..",        # 82
]
FIST_R = [
    # x: 71-75 76-80 81-84     y
    ".kkkk kkkkk kkk.",        # 73
    "k1122 22222 233k",        # 74
    "k1222 22222 334k",        # 75
    "k2222 22223 344k",        # 76
    "k2252 25235 344k",        # 77  knuckles
    "k22k2 2k23k 344k",        # 78
    "k22k2 3k33k 344k",        # 79
    "k23k3 3k33k 445k",        # 80
    ".k3k3 4k44k 45k.",        # 81
    "..kkk kkkkk kk..",        # 82
]


# ------------------------------------------------------------------ socks and trainers
# Structure: 'S' sock, 'U' trainer upper, 'Y' yellow laces, 'W' white rubber (a toe bumper split
# into three claws, Exploud's feet, and the sole). The black sock stripes and every seam are
# keylines. Left foot drawn (x 25-45); the right is its mirror, re-shaded in matt.feet().
FOOT_X0, FOOT_Y0 = 25, 85
FOOT = [
    # x: 25-29 30-34 35-39 40-44 45       y
    "....k SSSSS SSSSS SSk.. .",          # 85
    "....k kkkkk kkkkk kkk.. .",          # 86  stripe
    "....k SSSSS SSSSS SSk.. .",          # 87
    "....k kkkkk kkkkk kkk.. .",          # 88  stripe
    "...kk SSSSS SSSSS SSkk. .",          # 89
    "..kUU kkYkY kYkkU UUUUk .",          # 90  tongue and laces
    ".kUUU UkYkY kkUUU UUUUU k",          # 91
    "kUUUU UUkkk UUUUU UUUUU k",          # 92
    "kWWWk WWWWk WWWWk UUUUU k",          # 93  toe bumper, three claws
    "kWWWW WWWWW WWWWW WWWWW k",          # 94  sole
    ".kkkk kkkkk kkkkk kkkkk .",          # 95
]


# ------------------------------------------------------------------ accessors

def collar():
    return amap(COLLAR, COLLAR_X0, COLLAR_Y0)


def ports():
    return amap(PORT_L, PORT_L_X0, PORT_Y0), amap(PORT_R, PORT_R_X0, PORT_Y0)


def fists():
    return amap(FIST_L, FIST_L_X0, FIST_Y0), amap(FIST_R, FIST_R_X0, FIST_Y0)


def foot_structure(side):
    part = amap(FOOT, FOOT_X0, FOOT_Y0)
    if side:
        part = {(96 - x, y): k for (x, y), k in part.items()}
    return part


if __name__ == '__main__':
    problems = []
    problems += check(COLLAR, COLLAR_X0, 'collar')
    problems += check_pair(PORT_L, PORT_L_X0, PORT_R, PORT_R_X0, 'ports')
    problems += check_pair(FIST_L, FIST_L_X0, FIST_R, FIST_R_X0, 'fists')
    for line in problems:
        print(line)
    print('checked, %d problems' % len(problems))
