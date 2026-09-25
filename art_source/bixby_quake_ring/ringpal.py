"""Palette for beast Bixby's quake ring (bixby_quake_ring.png): 15 colours, every one measured from shipped Bixby art.

  hellfire ramp   the approved Inferno FX (art_source/bixby_inferno_fx/pal.py, from the redesign's throat fire):
                  r #570C18  n #9A2A10  N #E0561A  p #FF8C2E  P #FFC45A  Y #FFF2B0  W #FFFFFF
  quake browns    bixby_quake_wave.png's earth ramp, the existing quake art's: 0 #1B0F0D  1 #2C1810  2 #4A2818
                  3 #6A3C22  4 #8A5530
  charcoals       bixby_fire_scorch.png's, which the redesign's saddle ramp matches: b #26222C  c #3A3542  d #5C5868

It is an effect, so it follows the Bixby FX sheets' convention, measured on the Inferno sheets (flood, edge,
burst, impact, fireball, suction): 0.00% pure black, every texel alpha 255. No keyline, no semi-alpha.

A frame is a list of equal-length strings, one key per texel, '.' for clear.
"""
from PIL import Image


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


PAL = {
    # hellfire, dark to hot
    'r': hx('570C18'), 'n': hx('9A2A10'), 'N': hx('E0561A'), 'p': hx('FF8C2E'), 'P': hx('FFC45A'),
    'Y': hx('FFF2B0'), 'W': hx('FFFFFF'),
    # quake browns, dark to light
    '0': hx('1B0F0D'), '1': hx('2C1810'), '2': hx('4A2818'), '3': hx('6A3C22'), '4': hx('8A5530'),
    # charcoals
    'b': hx('26222C'), 'c': hx('3A3542'), 'd': hx('5C5868'),
}


def to_image(frame):
    h, w = len(frame), len(frame[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(frame):
        for x, k in enumerate(row):
            if k != '.':
                px[x, y] = PAL[k]
    return im


def sheet(rows_of_frames):
    fh, fw = len(rows_of_frames[0][0]), len(rows_of_frames[0][0][0])
    cols = max(len(r) for r in rows_of_frames)
    im = Image.new('RGBA', (fw * cols, fh * len(rows_of_frames)), (0, 0, 0, 0))
    for j, row in enumerate(rows_of_frames):
        for i, fr in enumerate(row):
            assert len(fr) == fh and all(len(s) == fw for s in fr), 'frame %d,%d is not %dx%d' % (i, j, fw, fh)
            im.alpha_composite(to_image(fr), (i * fw, j * fh))
    return im


def stats(im):
    """Opaque texels, distinct colours, pure-black share and semi-alpha count of an image."""
    im = im.convert('RGBA')
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)),
            'black%': round(100.0 * black / max(1, len(px)), 2),
            'semi': sum(1 for c in px if c[3] < 255)}
