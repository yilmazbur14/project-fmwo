"""Ship the approved redesign: Assets/Characters/Josh/josh_cards.png (2 frames of 80x80, feet on
row 79: 0 idle with the fan and a hand on his hip, 1 the signature gold card), the .aseprite beside
it, and a round-trip check that the .aseprite re-exports to exactly the same pixels.

    python export.py
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import josh3                                                     # noqa: E402
import lib                                                       # noqa: E402
from imgdiff import pixel_diff                                   # noqa: E402
from PIL import Image                                            # noqa: E402

ASSET = os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh', 'josh_cards')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')


def sheet():
    out = Image.new('RGBA', (160, 80), (0, 0, 0, 0))
    out.alpha_composite(josh3.build_frame(False).image(), (0, 0))
    out.alpha_composite(josh3.build_frame(True).image(), (80, 0))
    return out


def main():
    im = sheet()
    png = os.path.normpath(ASSET + '.png')
    ase = os.path.normpath(ASSET + '.aseprite')
    im.save(png)
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    back = os.path.join(tempfile.mkdtemp(), 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    st = lib.stats(im)
    print('wrote', png, im.size)
    print('round trip:', d or 'identical')
    print('opaque %d, colours %d, black %.1f%%' % (st['opaque'], st['colours'], 100 * st['black']))
    # feet on row 79 in both frames, nothing lower
    for f in range(2):
        rows = [y for y in range(80) for x in range(80 * f, 80 * f + 80) if im.getpixel((x, y))[3]]
        print('frame %d: rows %d..%d' % (f, min(rows), max(rows)))
    return 1 if d else 0


if __name__ == '__main__':
    sys.exit(main())
