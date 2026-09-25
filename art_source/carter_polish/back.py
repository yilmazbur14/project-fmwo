"""The back view: carter_akuma frame 2. The standing silhouette of frame 0 seen from behind.

    body()        -> Canvas without the aura (for sheets that composite their own)
    build()       -> the finished frame, idle aura included

The 天 on his back is the mark artist's, placed exactly where the approved back view has it
(mark.ten_back: x 32..62, y 53..67) - carter_mark_glow.png is registered to those pixels, so the
jacket here is built to hold the whole mark and the mark is never moved.

Changed from the approved back view: the gi's back is one closed field with torn caps (the same caps
as the front), lit from the upper left with the spine and the shoulder blades folded into it; the
beard shows past his jaw as a solid lick under each ear (it was a dotted line that read as a chain);
the fists are the back of the wrapped hands; the feet are heels.
"""
from lib import Canvas, amap, poly, mirror_set, shade, n_sphere, stroke, grow
import jacket as JK
import lower as LO
import arms as AR
import faces as FC
import mark as MK
import stand as ST

TH = [0.99, 0.84, 0.60, 0.30, 0.02]


def jacket_back():
    """One navy field from the collar to the belt: the front's caps and torn teeth, the opening
    between the lapels closed, and a collar standing behind his neck."""
    m = JK.mask_l() | mirror_set(JK.mask_l())
    m |= {(x, y) for y in range(48, 69) for x in range(37, 59)}
    m |= poly([(38, 47), (57, 47), (58, 50), (37, 50)])
    part = {}
    caps = {q for q in m if q[1] <= 63 and (q[0] <= 32 or q[0] >= 63)}
    for side, cx in ((0, 27.0), (1, 68.0)):
        cap = {q for q in caps if (q[0] < 48) == (side == 0)}
        part.update(shade(cap, 'bcdef', n_sphere(cx, 55.5, 10.5, 9.5), TH[1:]))
        for (x, y) in cap:
            if y >= 61:
                part[(x, y)] = 'e' if part[(x, y)] in 'de' else 'd'
    panel = m - caps
    for (x, y) in panel:
        # lit from the upper left: the left shoulder blade takes the light, the right side and the
        # small of the back fall into shadow
        u = (x - 33) / 30.0
        v = (y - 48) / 20.0
        lvl = 0.55 * u + 0.45 * v
        part[(x, y)] = 'b' if lvl < 0.18 else ('c' if lvl < 0.55 else ('d' if lvl < 0.85 else 'e'))
    # the spine, a fold under each shoulder blade, and the collar's seam
    stroke(part, [(47, 51), (47, 60), (48, 67)], 'd')
    stroke(part, [(34, 52), (38, 56), (41, 58)], 'd', only='bc')
    stroke(part, [(61, 52), (57, 56), (54, 58)], 'e', only='cd')
    stroke(part, [(39, 50), (47, 51), (56, 50)], 'k')
    return part


# the back of the wrapped fist: the cloth right round, the knuckles as a ridge at the bottom
BACK_FIST = [
    # x: +0..+4 +5..+9      y
    "kkkkk kkkkk",          # 71  where the wrap starts on the forearm
    "khghh iijlk",          # 72
    "kihhi ijjlk",          # 73
    "kjjjl lllmk",          # 74  the next turn of cloth
    "khggh hijlk",          # 75
    "khghh iijlk",          # 76
    "kihhh ijjlk",          # 77
    "kiiii jjllk",          # 78
    "kiiij jlllk",          # 79
    "kjiij jjlmk",          # 80
    "kjjij jllmk",          # 81  the knuckles' ridge under the wrap
    "kljlj ljlmk",          # 82
    ".kkkk kkkk.",          # 83
]

# heels: the same footprint as the front feet, seen from behind
BACK_FOOT_L = [
    # x: 26-30 31-35 36-40 41     y
    "..... ktstu uuvwk .",        # 88  achilles
    "....k tsttu uuvvk .",        # 89
    "..kvk ttstu uuvvk .",        # 90  the heel, the outside of the foot beside it
    ".kuvk tsttu uvvwk .",        # 91
    ".kuvk ttuuu uvvwk .",        # 92
    ".kvwk tuuuu vvwwk .",        # 93
    ".kwWk uuvvv vwwWk .",        # 94
    "..kkk kkkkk kkkk. .",        # 95
]
BACK_FOOT_R = [
    # x: 54-58 59-63 64-68 69     y
    ".ktst uuuvw k.... .",        # 88
    ".ktst tuuuv vk... .",        # 89
    ".ktst tuuuv vkvk. .",        # 90
    ".ktst tuuuv vkvwk .",        # 91
    ".kttu uuuuv vkvwk .",        # 92
    ".ktuu uuuvv wkwwk .",        # 93
    ".kuvv vvvww Wkwwk .",        # 94
    "..kkk kkkkk kkkk. .",        # 95
]


def body():
    cv = Canvas()
    cv.stamp(LO.shins())
    cv.stamp(amap(BACK_FOOT_L, 26, 88), outline=False)
    cv.stamp(amap(BACK_FOOT_R, 54, 88), outline=False)
    cv.stamp(LO.trousers())
    cv.stamp(AR.arm_l(), outline=False)
    cv.stamp(AR.arm_r(), outline=False)
    jk = jacket_back()
    cv.stamp(jk)
    ten = MK.ten_back()
    missing = [q for q in ten if q not in jk]
    if missing:
        raise AssertionError('the back jacket does not hold the whole mark: %s' % missing[:5])
    cv.stamp(ten, outline=False)
    cv.stamp(LO.belt(), outline=False)
    cv.stamp(amap(BACK_FIST, 18, 71), outline=False)
    cv.stamp(amap(BACK_FIST, 68, 71), outline=False)
    cv.stamp(FC.back_head_part(), outline=False)
    cv.stamp(FC.back_earring_part(), outline=False)
    return cv


def build():
    cv = body()
    return ST.aura(cv)
