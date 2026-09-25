"""Lint the MESSATSU sheets.  Exits non-zero on any failure.

    python check.py [sheet_dir]

What it holds the art to - every line is a requirement from the brief or a
promise the wiring numbers in the hand-off depend on:
  * sheet sizes: frame w x h x count, as briefed
  * every drawn pixel alpha 255 (the Demon FX convention; falloff is dither)
  * at most six colours a sheet (demon_parry_break.png measures six)
  * no red and no yellow in anything violet: ball, lock, beam, flare, head.
    Red is the parry cue and yellow the dodge cue; the surge's rim and his
    eyes are the only red in the attack
  * the beam: rows 8 and 127 are the band's edge line on every column of every
    frame, rows 8..127 are solid, and frame k+1 is frame k scrolled 8 texels
    (so the four frames loop and each tiles every 32)
  * nothing lit on the outer ring of a ball or lock frame, which the code
    scales and so would show a cut edge
"""
import colorsys
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(_HERE, '..', '..', 'Assets', 'Characters',
                                   'Carter', 'Messatsu'))

SIZES = {
    'messatsu_ball': (32, 32, 6),
    'messatsu_eyes': (16, 8, 2),
    'messatsu_lock': (32, 32, 6),
    'messatsu_beam': (32, 136, 4),
    'messatsu_flare': (64, 144, 4),
    'messatsu_head': (24, 144, 3),
    'messatsu_pulse': (20, 136, 3),
}
VIOLET = ('messatsu_ball', 'messatsu_lock', 'messatsu_beam', 'messatsu_flare',
          'messatsu_head')

fails = []


def fail(msg):
    fails.append(msg)
    print('FAIL', msg)


def pixels(im):
    flat = getattr(im, 'get_flattened_data', None)
    return list(flat() if flat else im.getdata())


def is_warm(rgb):
    """red, orange or yellow: hue under 70 or over 340 with some saturation"""
    r, g, b = [c / 255.0 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return s > 0.25 and 0.08 < l < 0.97 and (h * 360 < 70 or h * 360 > 340)


def main(d):
    for name, (fw, fh, n) in SIZES.items():
        path = os.path.join(d, name + '.png')
        if not os.path.exists(path):
            fail('%s missing' % name)
            continue
        im = Image.open(path).convert('RGBA')
        if im.size != (fw * n, fh):
            fail('%s is %s, want %dx%d' % (name, im.size, fw * n, fh))
            continue
        px = pixels(im)
        drawn = [p for p in px if p[3] > 0]
        cols = set(p[:3] for p in drawn)
        if any(p[3] != 255 for p in drawn):
            fail('%s has partial alpha' % name)
        if len(cols) > 6:
            fail('%s has %d colours' % (name, len(cols)))
        if name in VIOLET:
            warm = [c for c in cols if is_warm(c)]
            if warm:
                fail('%s has red/yellow: %s' % (name, warm))
        if name in ('messatsu_ball', 'messatsu_lock'):
            for i in range(n):
                fr = im.crop((i * fw, 0, i * fw + fw, fh)).load()
                for x in range(fw):
                    for y in range(fh):
                        if (x in (0, fw - 1) or y in (0, fh - 1)) and fr[x, y][3]:
                            fail('%s frame %d lit on its edge at %d,%d' % (name, i, x, y))
        print('%-15s %2d x %-3d x %d  %d colours  %s' % (
            name, fw, fh, n, len(cols), ' '.join('%02x%02x%02x' % c for c in sorted(cols))))

    # the beam's own promises
    im = Image.open(os.path.join(d, 'messatsu_beam.png')).convert('RGBA')
    fr = [im.crop((i * 32, 0, i * 32 + 32, 136)).load() for i in range(4)]
    edge = (0xe2, 0xa2, 0xf4, 255)
    for i in range(4):
        for x in range(32):
            for y in (8, 127):
                if fr[i][x, y] != edge:
                    fail('beam frame %d row %d col %d is not the band edge' % (i, y, x))
            for y in range(8, 128):
                if fr[i][x, y][3] != 255:
                    fail('beam frame %d has a hole in the band at %d,%d' % (i, x, y))
    for i in range(4):
        j = (i + 1) % 4
        for x in range(32):
            for y in range(8, 128):
                if fr[j][(x + 8) % 32, y] != fr[i][x, y]:
                    fail('beam frame %d -> %d is not an 8-texel scroll at %d,%d' % (i, j, x, y))
                    break
    print('beam: band rows 8..127 solid, edge rows 8/127 e2a2f4, 8-texel scroll loop checked')
    print('%d failure(s)' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else OUT))
