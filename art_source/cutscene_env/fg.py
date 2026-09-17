"""street_fg.png (1280x360, transparent): curbside props drawn IN FRONT of Burak.

Scroll factor 1.0 (they stand on the same pavement as the street layer, x-aligned with it).
"""
from lib import Canvas, bayer, hsh
from street2 import LAMPS

W, H = 1280, 360

LANTERN = [
    "......K......",
    ".....KNK.....",
    "....KNINK....",
    "...KKKKKKK...",
    "..KNNNNNNNK..",
    "..KdYYYYYdK..",
    "..KYYWWWYYK..",
    "..KYWWWWWYK..",
    "..KYWWWWWYK..",
    "..KYWWWWWYK..",
    "..KYYWWWYYK..",
    "..KdYYYYYdK..",
    "...KdYYYdK...",
    "....KKKKK....",
    ".....KNK.....",
    "....KNINK....",
    "...KNNINNK...",
    "...KKKKKKK...",
]

BASE = [
    "..KKKKKKK..",
    "..KNNINNK..",
    "...KNINK...",
    "...KNINK...",
    "..KKKKKKK..",
    "..KNNINNK..",
    ".KNNNINNNK.",
    ".KNNNINNNK.",
    "KNNNNINNNNK",
    "KKKKKKKKKKK",
]

HYDRANT = [
    ".....KKKK.....",
    "....KRrRMK....",
    "...KKKKKKKK...",
    "...KRrRRRMK...",
    "..KKKKKKKKKK..",
    "...KRrRRRMK...",
    "KKKKRrRRRMKKKK",
    "KMRRRrRRRMMMMK",
    "KMRRRrRRRMMMMK",
    "KKKKRrRRRMKKKK",
    "...KRrRRRMK...",
    "...KRrRRRMK...",
    "...KRrRRRMK...",
    "...KRRRRRMK...",
    "...KRRRRRMK...",
    "...KMRRRMMK...",
    "..KKKKKKKKKK..",
    "..KRRRRRRMMK..",
    ".KKKKKKKKKKKK.",
    ".KMMMMMMMMMMK.",
    ".KKKKKKKKKKKK.",
]

METER = [
    ".KKKKK.",
    "KEDgDEK",
    "KEgPgEK",
    "KEDgDEK",
    "KEEEEEK",
    ".KKKKK.",
    "..KEK..",
]

BIN = [
    "..KKKKKKKKKKKKKK..",
    ".KDDFFFFFFFFFDDEK.",
    ".KEEEEEEEEEEEEEEK.",
    "KKKKKKKKKKKKKKKKKK",
    ".K4I4K4I4K4I4K44K.",
    ".K494K494K494K49K.",
    ".K494K494K494K49K.",
    ".K494K494K494K45K.",
    ".K494K494K494K45K.",
    ".KKKKKKKKKKKKKKKK.",
    ".K494K494K494K45K.",
    ".K494K494K494K45K.",
    ".K494K494K494K45K.",
    ".K494K494K494K45K.",
    ".K454K454K454K55K.",
    ".KKKKKKKKKKKKKKKK.",
    ".K454K454K454K55K.",
    ".K454K454K454K55K.",
    ".K555K555K555K55K.",
    ".K555K555K555K55K.",
    ".KKKKKKKKKKKKKKKK.",
    "..KK..........KK..",
]

GROUND = 279   # bottom row of every curbside prop


def lamp(c, x, flicker_off=False):
    top = GROUND - 150
    lan = LANTERN
    if flicker_off:
        lan = [r.replace('W', 'N').replace('Y', 'I').replace('d', 'N') for r in LANTERN]
    # dithered halo first (only where the layer is still empty)
    if not flicker_off:
        cx, cy = x + 0.5, top + 8.5
        for yy in range(top - 12, top + 30):
            for xx in range(x - 20, x + 21):
                d = ((xx + 0.5 - cx) ** 2 + ((yy + 0.5 - cy) * 1.15) ** 2) ** 0.5
                if 7 < d < 19 and bayer(xx, yy) < 0.30 * (1 - (d - 7) / 12.0):
                    c.set(xx, yy, 'd' if d < 12 else 'A')
    c.stamp(lan, x - 6, top)
    post_top = top + len(LANTERN)
    base_top = GROUND - len(BASE) + 1
    for y in range(post_top, base_top):
        c.set(x - 2, y, 'K')
        c.set(x - 1, y, 'I')
        c.set(x, y, 'N')
        c.set(x + 1, y, 'N')
        c.set(x + 2, y, 'K')
    for ry in (post_top + 20, post_top + 72):
        c.stamp(["KKKKKKK", "KNNINNK", "KKKKKKK"], x - 3, ry)
    # little banner arm with a hanging pennant (city district flag)
    ay = post_top + 6
    c.hline(x + 3, x + 12, ay, 'K')
    c.stamp(["KKKKKKK", "KUUUUUK", "KUuUUUK", "KUUUUUK", "KUUUUUK", "KIUUUIK", ".KIUIK.", "..KIK..", "...K..."], x + 6, ay + 1)
    c.stamp(BASE, x - 5, base_top)


def build(flicker_off=False):
    c = Canvas(W, H)
    for i, lx in enumerate(LAMPS):
        lamp(c, lx, flicker_off=(flicker_off and i == 0))
    c.stamp(METER, 173, GROUND - 32)
    for y in range(GROUND - 25, GROUND + 1):
        c.set(175, y, 'K')
        c.set(176, y, 'E')
        c.set(177, y, 'K')
    c.stamp(BIN, 700, GROUND - len(BIN) + 1)
    c.stamp(HYDRANT, 1110, GROUND - len(HYDRANT) + 1)
    return c


if __name__ == '__main__':
    c = build()
    c.save('out/street_fg.png')
