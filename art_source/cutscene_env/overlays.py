"""Animated overlays.

rain_overlay.png  : 4 x 640x360 frames in a horizontal strip (hframes=4), transparent, screen-space.
sign_flicker.png  : 3 frames of the NOODLES blade sign, placed at SIGN_POS in street_buildings.png space.
"""
import random
from lib import Canvas, line_pts

FW, FH, NF = 640, 360, 4


def rain_frame(seed):
    c = Canvas(FW, FH)
    rnd = random.Random(seed)
    # far drizzle: short, dim
    for _ in range(150):
        x, y = rnd.randrange(FW), rnd.randrange(FH)
        L = rnd.randint(3, 5)
        for (px, py) in line_pts(x, y, x - L // 3, y + L):
            c.set(px % FW, py % FH, 'F')
    # near streaks: longer, lighter
    for _ in range(55):
        x, y = rnd.randrange(FW), rnd.randrange(FH)
        L = rnd.randint(7, 11)
        pts = line_pts(x, y, x - L // 4, y + L)
        for i, (px, py) in enumerate(pts):
            c.set(px % FW, py % FH, 'P' if i == len(pts) - 1 else 'g')
    return c


def rain_strip():
    strip = Canvas(FW * NF, FH)
    frames = []
    for f in range(NF):
        fr = rain_frame(100 + f * 17)
        frames.append(fr)
        strip.blit(fr, f * FW, 0)
    return strip, frames


SIGN_POS = (352, 38)        # top-left of the blade sign board in street_buildings.png
SIGN_W, SIGN_H = 21, 70


def sign_strip():
    from lib import Canvas as C
    st = C.load('out/street_buildings.png')
    base = st.crop(SIGN_POS[0], SIGN_POS[1], SIGN_W, SIGN_H)
    frames = [base]
    off = base.crop(0, 0, SIGN_W, SIGN_H)
    for y in range(1, SIGN_H - 1):
        for x in range(1, 16):
            k = off.p[y][x]
            if k in ('r', 'R'):
                off.p[y][x] = 'M'
            elif k == 'V':
                off.p[y][x] = 'N'
    frames.append(off)
    # stutter frame: only the N and the last letter hold
    half = base.crop(0, 0, SIGN_W, SIGN_H)
    for y in range(22, SIGN_H - 1):
        for x in range(1, 16):
            if 57 <= y <= 65:
                continue
            k = half.p[y][x]
            if k in ('r', 'R'):
                half.p[y][x] = 'M'
            elif k == 'V':
                half.p[y][x] = 'N'
    frames.append(half)
    strip = C(SIGN_W * len(frames), SIGN_H)
    for i, fr in enumerate(frames):
        strip.blit(fr, i * SIGN_W, 0)
    return strip, frames


if __name__ == '__main__':
    s, fr = rain_strip()
    s.save('out/rain_overlay.png')
    s2, fr2 = sign_strip()
    s2.save('out/sign_flicker.png')
    s2.save('view/sign_flicker_6x.png', 6, bg='checker')
    fr[0].save('view/rain_f0_2x.png', 2, bg=(34, 32, 52, 255))
