"""python rtcheck.py <fry_trail.png>  - does fry_trail.aseprite still hold the art?

Pass the PNG Aseprite exported back out of the .aseprite; it is compared against
the fry_trail.png in this folder that the build wrote.  With no argument it says
what it expects.

Uses art_source/imgdiff.py, NOT a bare getbbox(): since Pillow 10,
Image.difference().getbbox() defaults to alpha_only and compares SILHOUETTES,
so it will call two frames identical when every coloured texel differs.  A fry
sheet is one silhouette with three yellows in it - exactly the case that check
cannot see.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from imgdiff import pixel_diff   # noqa: E402

PAIRS = ('fry_trail.png',)


def main():
    if len(sys.argv) < 2:
        print('expects a re-export of:', ', '.join(PAIRS))
        return 0
    bad = 0
    for other in sys.argv[1:]:
        # The re-export has to be named after the source it came from, so a
        # scratch file can never be mistaken for a passing check.
        src = os.path.join(HERE, os.path.basename(other))
        if not os.path.exists(src):
            print('%-18s no source of that name here; expected %s'
                  % (os.path.basename(other), ', '.join(PAIRS)))
            bad += 1
            continue
        d = pixel_diff(Image.open(src).convert('RGBA'),
                       Image.open(other).convert('RGBA'))
        bad += bool(d)
        print('%-18s %s' % (os.path.basename(src),
                            d or 'identical (alpha and colour, every texel)'))
    return bad


if __name__ == '__main__':
    sys.exit(main())
