"""Rebuild ONLY the three spotlight textures, and nothing else from build_fx.

    python build_spotlight.py [check_dir]

build_fx.main() rewrites the whole Demon set - clones, lights, impacts, the
darkness, the finish.  The spotlight fix (stage.SH 224 -> 248, closing the
pool's ellipse) touches none of those, so they are left alone rather than
regenerated.  With a check_dir holding the previous files, every texel of the
old canvas is compared against the new one: the fix only adds rows at the
bottom, so the old 224 rows must come back byte for byte.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import stage
from pngio import read_png

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..',
                                   'Assets', 'Characters', 'Carter', 'Demon'))
FILES = [('demon_spotlight.png', stage.spotlight),
         ('demon_spotlight_pool.png', stage.pool_only),
         ('demon_spotlight_cone.png', stage.cone_only)]


def main(check=None):
    bad = 0
    for name, fn in FILES:
        path = os.path.join(OUT, name).replace('\\', '/')
        fn().save(path)
        w, h, px = read_png(path)
        last = max((y for y in range(h) for x in range(w) if px[y][x][3]),
                   default=-1)
        line = '%-26s %dx%d  anchor (%d,%d)  last lit row %d  bottom row clear: %s' % (
            name, w, h, stage.PX, stage.PY, last, 'yes' if last < h - 1 else 'NO')
        if check:
            ow, oh, old = read_png(os.path.join(check, name))
            diff = sum(1 for y in range(oh) for x in range(ow)
                       if tuple(old[y][x]) != tuple(px[y][x]))
            line += '  old %dx%d texels changed: %d' % (ow, oh, diff)
            bad += diff
        if last >= h - 1:
            bad += 1
        print(line)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1] if len(sys.argv) > 1 else None) else 0)
