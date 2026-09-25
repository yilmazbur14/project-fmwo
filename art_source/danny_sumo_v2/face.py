"""Danny's sumo face: cel-shaded base shapes plus hand-authored feature maps.

Identity carried over from danny.png: flat heavy-lidded slit eyes (a black bar under a heavy lid,
drooping at the outer corners), a small broad nose, the downturned frown. Added for the sumo: round
jowls, the sleep bubble blown from his left nostril (viewer's right). No cheek paint: E. Honda's
kabuki stripes were removed on 2026-09-17 because under the beanie flap they read as blood.
"""
from sumo_lib import ellipse, amap, band, MIR
import lib as jl

CX = 87.5


def _check(rows, name):
    w = {len(r.replace(' ', '')) for r in rows}
    assert len(w) == 1, (name, [len(r.replace(' ', '')) for r in rows])


def face_base(mask, dx=0, dy=0):
    """Cel shapes on the face mask: base, a lit left cheek, a shadowed right side and jaw.
    dx, dy move the shapes with a head that has been moved."""
    part = {p: '5' for p in mask}
    # lit left side: the cheek, and the plane beside the nose under the eye
    band(part, ellipse(71.5 + dx, 39 + dy, 10.5, 8.5), '6')
    band(part, ellipse(80 + dx, 29.5 + dy, 8, 2.8), '6')
    band(part, ellipse(69.5 + dx, 39.5 + dy, 4.5, 3.0), '7')
    # right side turning away: a band down the right cheek, deeper at the jaw corner
    for (x, y) in mask:
        u = (x - CX - dx) / 26.0
        v = (y - 37 - dy) / 17.0
        r = u * u + v * v
        if x - dx > 96 and r > 0.62:
            part[(x, y)] = '4'
        if x - dx > 101 and r > 0.95:
            part[(x, y)] = '3'
    # the jaw's underside, all the way round
    for (x, y) in mask:
        if (x, y + 1) not in mask or (x, y + 2) not in mask:
            part[(x, y)] = '4' if part[(x, y)] in '567' else '3'
    return part


def face_base_at(mask, dx, dy):
    return face_base(mask, dx, dy)


# The viewer's-left eye, outer corner on the left: a crease under the beanie's cuff, the heavy lid
# (lit), the lash as a black bar that droops at the outer corner, a tired bag under it.
EYE_L = [
    # x: 0-4   5-9   10-13
    "..333 33333 3...",    # 0 crease
    ".3566 67776 63..",    # 1 lid
    "k6666 66666 6kk.",    # 2 lid; the lash starts high at the inner corner
    "kkkkk kkkkk kkkk",    # 3 lash line
    ".kkkk kkkkk kkk.",    # 4 the slit: a heavy bar like danny.png's, tapering
    "..4kk kkkkk k4..",    # 5
    "...44 45554 4...",    # 6 bag
]
_check(EYE_L, 'EYE_L')

# The other eye is the mirror, one tone down: it is on the far side of the nose from the light.
DOWN = {'7': '6', '6': '5', '5': '4', '4': '3', '3': '3'}
EYE_R = [''.join(DOWN.get(c, c) for c in r.replace(' ', '')[::-1]) for r in EYE_L]

# A broad nose: lit bridge and tip, the wings, the nostrils, its shadow thrown to the right.
NOSE = [
    # x: 81-85 86-90 91-95
    "..... 65... .....",    # 0  y 31
    "..... 675.. .....",    # 1
    "..... 675.. .....",    # 2
    "..... 6754. .....",    # 3
    "....6 67754 .....",    # 4
    "...66 77765 4....",    # 5
    "..k66 77766 54k..",    # 6
    ".k665 66665 544k.",    # 7
    ".k6k2 k555k 2k4k.",    # 8  nostrils
    "..kk1 1kkk1 1kk..",    # 9
    "...kk kk.kk kk...",    # 10
]
_check(NOSE, 'NOSE')

# The frown from danny.png, bigger: a black arch with drooping corners, the lower lip pushed up
# under it in a sulk, and its shadow on the chin.
MOUTH = [
    # x: 78-82 83-87 88-92 93-97
    "..... 33333 333.. .....",    # 0  under the nose
    "..... kkkkk kkkkk .....",    # 1  arch top
    "...kk 55666 66554 kk...",    # 2
    "..k.4 55566 65554 ..k..",    # 3  corners down
    ".k... 44555 5544. ...k.",    # 4
    "..... .4444 444.. .....",    # 5
]
_check(MOUTH, 'MOUTH')


def bubble(cx, cy, r=4.6):
    """The sleep bubble: a pale disc with a white crescent upper left and a cool shade lower right.
    Returned without its keyline; stamp it with outline=True."""
    body = ellipse(cx, cy, r, r)
    part = {p: 'H' for p in body}
    jl.rim(part, 'h', 1, 1, depth=1)
    jl.rim(part, 'h', 1, 0, depth=1)
    jl.rim(part, 'W', -1, -1, depth=2)
    part[(int(round(cx - r * 0.35)), int(round(cy - r * 0.45)))] = 'W'
    return part


def features(cv, bubble_at=(99.5, 44.0), bubble_r=4.6):
    """Stamp the features onto a Canvas (face already drawn)."""
    for part in (amap(EYE_L, 66, 28), amap(EYE_R, 96, 28), amap(NOSE, 81, 31), amap(MOUTH, 78, 43)):
        for q, k in part.items():
            cv.px[q] = k
    if bubble_at:
        cv.stamp(bubble(*bubble_at, r=bubble_r))
