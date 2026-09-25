"""Inspection helpers. Writes ONLY to the folder in BURAK_WIP (default: a burak_boss_wip folder in the
system temp dir), never into Assets/ or the repo.

    python look.py head [tilt]         the head alone, 12x with a grid, and 3x / 6x
    python look.py frames              both frames at 5x and 3x, with their numbers
    python look.py zoom F x0 y0 x1 y1 [s]   a gridded crop of frame F
    python look.py dump F x0 y0 x1 y1       the keys of a region of frame F, for hand edits
"""
import os
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

WIP = os.environ.get('BURAK_WIP', os.path.join(tempfile.gettempdir(), 'burak_boss_wip'))


def save(im, name):
    os.makedirs(WIP, exist_ok=True)
    p = os.path.join(WIP, name)
    im.save(p)
    print('wrote', p)
    return p


def check_rows(rows, width, name):
    for i, r in enumerate(rows):
        s = r.replace(' ', '')
        if len(s) != width:
            print('%s row %d: width %d (want %d): %r' % (name, i, len(s), width, r))


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'head':
        import head
        check_rows(head.IDLE, 25, 'IDLE')
        check_rows(head.SHOT, 25, 'SHOT')
        tilt = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        ims = []
        for expr in ('idle', 'shot'):
            c = kit.Canvas()
            c.stamp(head.neck())
            l, r = head.ears()
            c.stamp(l)
            c.stamp(r)
            c.stamp(head.face_base())
            c.stamp(head.features(expr), outline=False)
            c.stamp(head.hair())
            c.stamp(head.hat(tilt), outline='soft')
            ims.append(kit.image(c.px).crop((20, 0, 76, 54)))
        save(kit.row([kit.grid(ims[0], 10, 20, 0), kit.grid(ims[1], 10, 20, 0)], gap=12), 'head_10x.png')
        save(kit.row([kit.up(ims[0], 3), kit.up(ims[1], 3), kit.up(ims[0], 6), kit.up(ims[1], 6)]), 'head_3x_6x.png')
    elif what == 'frames':
        import burak
        f0, f1 = burak.frames()
        save(kit.row([kit.up(f0, 5), kit.up(f1, 5)]), 'frames_5x.png')
        save(kit.row([kit.up(f0, 3), kit.up(f1, 3)]), 'frames_3x.png')
        for i, f in enumerate((f0, f1)):
            st = kit.stats(f)
            print('frame %d: opaque %d, colours %d, black %.1f%%, bbox %s'
                  % (i, st['opaque'], st['colours'], 100 * st['black'], f.getbbox()))
    elif what == 'zoom':
        import burak
        fi = int(sys.argv[2])
        x0, y0, x1, y1 = map(int, sys.argv[3:7])
        s = int(sys.argv[7]) if len(sys.argv) > 7 else 12
        im = kit.image(burak.frame_px(fi)).crop((x0, y0, x1 + 1, y1 + 1))
        save(kit.grid(im, s, x0, y0), 'zoom_f%d_%d_%d.png' % (fi, x0, y0))
    elif what == 'dump':
        import burak
        fi = int(sys.argv[2])
        x0, y0, x1, y1 = map(int, sys.argv[3:7])
        print(kit.dump(burak.frame_px(fi), x0, y0, x1, y1))
