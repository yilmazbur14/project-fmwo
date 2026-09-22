"""python rtcheck.py <a.png> <b.png> ...  - does each .aseprite still hold its art?

Pass the PNGs Aseprite exported back out; each is compared against the source PNG
of the same name in this folder.  With no arguments it just lists what it expects.

Uses art_source/imgdiff.py, NOT a bare getbbox(): Image.difference().getbbox()
compares silhouettes only and will call two frames identical when every coloured
pixel differs.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from imgdiff import pixel_diff   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = ('mason_juggle.png', 'mason_leap_shadow.png', 'mason_juggle_keys.png')


def main():
    if len(sys.argv) < 2:
        print('expects a re-export of each of:', ', '.join(PAIRS))
        return 0
    bad = 0
    for other in sys.argv[1:]:
        # The re-export has to be named after the source it came from, so a stray
        # scratch file can never be mistaken for a passing check.
        src = os.path.join(HERE, os.path.basename(other))
        if not os.path.exists(src):
            print('%-26s no source of that name here; expected one of %s'
                  % (os.path.basename(other), ', '.join(PAIRS)))
            bad += 1
            continue
        a = Image.open(src).convert('RGBA')
        b = Image.open(other).convert('RGBA')
        d = pixel_diff(a, b)
        bad += bool(d)
        print('%-26s %s' % (os.path.basename(src),
                            d or 'identical (alpha and colour, every pixel)'))
    return bad


if __name__ == '__main__':
    sys.exit(main())
