"""Three key frames of the VS card's entrance, built on layout A.

Timeline the frames are sampled from (see the report for the full beat sheet):
  0.00 - 0.16  halves drive in from opposite edges, easing out       <- K1 @ 0.07
  0.16         they meet; the seam flashes white
  0.16 - 0.24  VS falls in from 1.6x, lands at 1.0 with a 3-frame
               camera shake and a radial burst                       <- K2 @ 0.18
  0.24 - 0.38  ERIC / @regular wipe in from behind the block edge
  0.38 - 1.75  hold                                                  <- K3 @ 0.60
  1.75 - 1.95  white flash out into the fight
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from card import *
from pxlib import hx, outline
import bust_burak, bust_eric

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
BH, BY, ST, SB = 132, 114, 350, 290


def halves(band):
    lm = mask_from_poly((NW, BH), [(0, 0), (ST, 0), (SB, BH), (0, BH)])
    rm = mask_from_poly((NW, BH), [(ST, 0), (NW, 0), (NW, BH), (SB, BH)])
    l = Image.new("RGBA", (NW, BH), (0, 0, 0, 0)); l.paste(band, (0, 0), lm)
    r = Image.new("RGBA", (NW, BH), (0, 0, 0, 0)); r.paste(band, (0, 0), rm)
    return l, r


def k1_slide(band, bg, dx=120):
    """Halves still driving in, with speed streaks trailing off their edges."""
    f = bg.copy()
    l, r = halves(band)
    d = ImageDraw.Draw(f)
    for i in range(16):                                   # streaks in the open wedge
        y = BY + 8 + i * 8
        d.line([(0, y), (random.Random(i).randint(60, 210), y)], fill=hx("#3A5BA8"), width=1)
        d.line([(NW, y + 3), (NW - random.Random(i + 99).randint(60, 210), y + 3)], fill=hx("#A3B1C2"), width=1)
    f.alpha_composite(l, (-dx, BY))
    f.alpha_composite(r, (dx, BY))
    d = ImageDraw.Draw(f)
    d.rectangle([0, BY, NW, BY + 2], fill=hx("#000000"))
    d.rectangle([0, BY + BH - 3, NW, BY + BH - 1], fill=hx("#000000"))
    return up(f)


def k2_slam(band, bg, shake=(-7, 5)):
    """The frame the VS lands on: seam flash, radial burst, oversized VS, shake."""
    f = bg.copy()
    f.alpha_composite(band, (0, BY))
    d = ImageDraw.Draw(f)
    for o in range(-3, 4):                                 # seam flash
        d.line([(ST + o, BY), (SB + o, BY + BH)], fill=hx("#FFFFFF"), width=2)
    img = up(f)

    cx, cy = int(seam_xm() * SCALE), (BY + BH // 2) * SCALE
    d = ImageDraw.Draw(img)
    for k in range(20):                                    # radial burst
        a = k * (math.pi * 2 / 20) + 0.14
        r0, r1 = 150, 150 + (330 if k % 2 == 0 else 200)
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], fill=hx("#FFFFFF"), width=7)
    d.ellipse([cx - 168, cy - 168, cx + 168, cy + 168], outline=hx("#FFFFFF"), width=9)
    put_text(img, (cx, cy), "VS", 260, anchor="cc", ol_w=13, sh=(0, 16))

    out = Image.new("RGBA", (SW, SH), hx("#000000"))       # camera shake
    out.alpha_composite(img, (shake[0] * SCALE, shake[1] * SCALE))
    return out


def seam_xm():
    return ST + (SB - ST) * 0.5 + 6


def k3_hold(band, bg):
    f = bg.copy()
    f.alpha_composite(band, (0, BY))
    img = up(f)
    put_text(img, (int(seam_xm()) * SCALE, (BY + BH // 2) * SCALE), "VS", 200, anchor="cc")
    rx = int(NW * 0.93) * SCALE
    put_text(img, (rx, (BY + BH - 14) * SCALE), "ERIC", 99, anchor="rb")
    put_text(img, (rx, (BY + BH - 14) * SCALE - 108), "@regular", 33, anchor="rb", fill="#F2C457")
    return img


if __name__ == "__main__":
    b = bust_burak.build(); outline(b)
    e = bust_eric.build(); outline(e)
    bg = backdrop(0.30)
    band = build_band(NW, BH, ST, SB, b, e, bx=86, by=14, ex=404, ey=14)

    frames = [("k1_slide", k1_slide(band, bg)),
              ("k2_slam", k2_slam(band, bg)),
              ("k3_hold", k3_hold(band, bg))]
    for n, im in frames:
        p = os.path.join(OUT, "vs_anim_%s.png" % n)
        im.convert("RGB").save(p)
        print(p)

    strip = Image.new("RGB", (SW // 2, (SH // 2) * 3 + 16), (12, 11, 18))
    for i, (n, im) in enumerate(frames):
        strip.paste(im.convert("RGB").resize((SW // 2, SH // 2), Image.NEAREST), (0, i * (SH // 2 + 8)))
    strip.save(os.path.join(OUT, "vs_anim_strip.png"))
    print("strip", strip.size)
