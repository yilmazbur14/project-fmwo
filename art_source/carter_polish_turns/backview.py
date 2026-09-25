"""The back view these sheets stand on: carter_akuma frame 2, the polished back, from the polish rig's
own module (art_source/carter_polish/back.py - read-only, never redrawn here).

    body()      back.body(): the whole figure from behind with the 天 at rest, no aura
    headless()  the same, stopped before the head and the earring - the look-back puts its own
                turning head on it, and nothing else about him moves
    host()      the gi's pixels: the only cloth the mark's glow may light (sigil_bloom's host)
    check()     back.body() + the approved aura == carter_akuma.png frame 2 pixel for pixel, and
                headless() + the approved head == back.body()

The 天 sits at x 32..62, y 53..67 in all of them (mark.ten_back), where carter_mark_glow.png is
registered (CarterArtLayout.FINAL_MARK_GLOW offset (16, 32)).
"""
import os

from lib import Canvas, amap
import back as BK
import lower as LO
import arms as AR
import faces as FC
import mark as MK
import rig


def body():
    return BK.body()


def headless():
    """back.body()'s own stamps, in its order, up to the head."""
    cv = Canvas()
    cv.stamp(LO.shins())
    cv.stamp(amap(BK.BACK_FOOT_L, 26, 88), outline=False)
    cv.stamp(amap(BK.BACK_FOOT_R, 54, 88), outline=False)
    cv.stamp(LO.trousers())
    cv.stamp(AR.arm_l(), outline=False)
    cv.stamp(AR.arm_r(), outline=False)
    cv.stamp(BK.jacket_back())
    cv.stamp(MK.ten_back(), outline=False)
    cv.stamp(LO.belt(), outline=False)
    cv.stamp(amap(BK.BACK_FIST, 18, 71), outline=False)
    cv.stamp(amap(BK.BACK_FIST, 68, 71), outline=False)
    return cv


def head_back():
    return FC.back_head_part()


def earring_back():
    return FC.back_earring_part()


_HOST = None


def host():
    global _HOST
    if _HOST is None:
        _HOST = set(BK.jacket_back())
    return set(_HOST)


def check():
    from PIL import Image
    from imgdiff import pixel_diff
    errs = []
    shipped = Image.open(os.path.join(rig.ASSETS, 'carter_akuma.png')).convert('RGBA').crop((192, 0, 288, 96))
    d = pixel_diff(BK.build().image(), shipped)
    if d:
        errs.append('back.build() is no longer carter_akuma frame 2: ' + d)
    cv = headless()
    cv.stamp(head_back(), outline=False)
    cv.stamp(earring_back(), outline=False)
    if cv.px != body().px:
        errs.append('headless() + head != back.body()')
    missing = rig.MARK - set(k for k, v in body().px.items() if v in 'yY')
    if missing:
        errs.append('the 天 is not whole on the back: %d px missing' % len(missing))
    return errs or None
