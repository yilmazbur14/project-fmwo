"""void_mockup*.png: the REAL god-fight captures (capture_void.gd: the game's void, camera, god, strings, HUD and
player, the approval art placed at its real 3x world scale) with the boss-bar block outlined; plus one annotated
copy with the anchors in screen px (screen = (world + (480, 6)) / 1.5)."""
from ge_common import *
from PIL import ImageDraw

BAR = (720, 33, 480, 148)                 # the boss-bar block, screen px (the HUD keep-out the fight uses)
YEL = (255, 214, 64, 255)


def to_screen(w):
    return ((w[0] + 480) / 1.5, (w[1] + 6) / 1.5)


def dashed_rect(d, x, y, w, h, col, dash=10, width=3):
    for (a, b) in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
        L = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        for s in range(0, int(L), dash * 2):
            t0, t1 = s / L, min(1.0, (s + dash) / L)
            d.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)],
                   fill=col, width=width)


def outline_bar(im):
    d = ImageDraw.Draw(im)
    dashed_rect(d, *BAR, YEL)
    d.text((BAR[0] + BAR[2] + 8, BAR[1] + 2), 'boss-bar block (720,33 480x148)\nsee-through while Jordan is behind it', fill=YEL)
    return im


def cross(d, p, col, r=10, label=None):
    x, y = p
    d.line([(x - r, y), (x + r, y)], fill=col, width=2)
    d.line([(x, y - r), (x, y + r)], fill=col, width=2)
    if label:
        d.text((x + r + 4, y - 6), label, fill=col)


def main():
    pairs = [('void_capture_l0_b0_w0.png', 'void_mockup.png'),
             ('void_capture_l1_b1_w3.png', 'void_mockup_stopped_fire.png'),
             ('void_capture_l0_b1_w5.png', 'void_mockup_spin.png')]
    for src, dst in pairs:
        im = Image.open(os.path.join(LOOK, src)).convert('RGBA')
        outline_bar(im).save(os.path.join(OUT, dst))
    # the annotated copy
    im = Image.open(os.path.join(LOOK, pairs[0][0])).convert('RGBA')
    outline_bar(im)
    d = ImageDraw.Draw(im)
    C1, C2, C3 = (255, 90, 200, 255), (120, 255, 170, 255), (140, 200, 255, 255)
    piv = to_screen((960, 924))
    cross(d, piv, C1, 12, 'Liam float pivot = wheel centre\nscreen (960,620) / world (960,924)')
    d.ellipse([piv[0] - 181, piv[1] - 181, piv[0] + 181, piv[1] + 181], outline=C1, width=1)
    lb = to_screen((958.5, 925.5))
    cross(d, (lb[0] - 40, lb[1] + 30), C2, 0)
    bx = to_screen((1750.5, 943.5))
    cross(d, bx, C2, 8, 'Bixby back hook\nscreen (1487,633)')
    tl = to_screen((1437, 654))
    d.rectangle([tl[0], tl[1], tl[0] + 384, tl[1] + 320], outline=C3, width=1)
    d.text((tl[0], tl[1] + 324), 'Bixby frame 192x160 at 2 px a texel = 384x320 px', fill=C3)
    pl = to_screen((960, 1330))
    d.text((pl[0] + 20, pl[1] - 10), 'player (start, bottom centre)', fill=(230, 230, 230, 255))
    d.text((20, 360), 'Wheel radius 90.5 texels = 181 px (+4 texels of lit glow)\n'
                      'Strings: Liam on the LEFT hand inner pair, Bixby on the RIGHT hand outer pair,\n'
                      'drawn by the game (JordanStrings) to each back hook; the wheel sits UNDER the\n'
                      'strings layer (floor layer here) so they run over it to his back.', fill=(230, 230, 230, 255))
    im.save(os.path.join(OUT, 'void_mockup_annotated.png'))
    print('ok')


if __name__ == '__main__':
    main()
