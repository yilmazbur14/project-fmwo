"""Inspection. Writes ONLY to BURAK_AWIP (default: a burak_anims_wip folder in the system temp dir).

    python alook.py sheet NAME [s]            the sheet's frames in a row at scale s (default 4)
    python alook.py zoom NAME F x0 y0 x1 y1 [s]
    python alook.py dump NAME F x0 y0 x1 y1
"""
import os
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import akit as A  # noqa: E402
import kit  # noqa: E402
import sheets as S  # noqa: E402

WIP = os.environ.get('BURAK_AWIP', os.path.join(tempfile.gettempdir(), 'burak_anims_wip'))


def save(im, name):
    os.makedirs(WIP, exist_ok=True)
    p = os.path.join(WIP, name)
    im.save(p)
    print('wrote', p)


if __name__ == '__main__':
    what = sys.argv[1]
    name = sys.argv[2]
    frames = S.SHEETS[name]()
    if what == 'sheet':
        s = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        ims = [kit.label(kit.up(A.image(P), s), '%d %s %.2fs' % (i, n, h)) for i, (n, P, h) in enumerate(frames)]
        save(kit.row(ims, gap=8), '%s_%dx.png' % (name, s))
        save(kit.row([kit.up(A.image(P), 3) for (n, P, h) in frames], gap=6), '%s_3x.png' % name)
    elif what == 'zoom':
        fi = int(sys.argv[3])
        x0, y0, x1, y1 = map(int, sys.argv[4:8])
        s = int(sys.argv[8]) if len(sys.argv) > 8 else 8
        im = A.image(frames[fi][1]).crop((x0, y0, x1 + 1, y1 + 1))
        save(kit.grid(im, s, x0, y0), '%s_f%d_zoom.png' % (name, fi))
    elif what == 'dump':
        fi = int(sys.argv[3])
        x0, y0, x1, y1 = map(int, sys.argv[4:8])
        print(kit.dump(A.render(frames[fi][1]), x0, y0, x1, y1))
