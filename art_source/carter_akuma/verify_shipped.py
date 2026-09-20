"""Re-render every shipped Carter sheet in memory and compare it, pixel for
pixel, with the file on disk.  Writes nothing.

    python verify_shipped.py

Why this exists: on this machine the Python interpreter intermittently corrupts
its own memory - segfaults, and impossible errors on deterministic code such as
a list element turning into a range_iterator mid-comprehension.  A crash is the
lucky case.  The dangerous case is a run that completes and writes a subtly
wrong pixel, which the lints cannot catch if the colour happens to be on
palette.  The generators are fully deterministic, so a fresh render that
matches the file byte for byte proves the file is what the code means it to be.
Run it twice; two independent processes agreeing is the check.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import carter_scale
carter_scale.apply()
from lib import W, H
from pngio import read_png, blank, paste

A = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))


def strip(frames, fw, fh):
    s = blank(fw * len(frames), fh)
    for i, f in enumerate(frames):
        paste(s, f, i * fw, 0)
    return s


def compare(name, px):
    w, h, disk = read_png(os.path.join(A, name))
    if h != len(px) or w != len(px[0]):
        print('%-24s SIZE MISMATCH  disk %dx%d  render %dx%d'
              % (name, w, h, len(px[0]), len(px)))
        return 1
    d = sum(1 for y in range(h) for x in range(w)
            if tuple(disk[y][x]) != tuple(px[y][x]))
    print('%-24s %s' % (name, 'match' if d == 0 else '%d PIXELS DIFFER' % d))
    return 1 if d else 0


def render(name):
    """one sheet, rendered fresh - kept to a single sheet per process so a
    run is short, because the longer a process lives the likelier it is to
    be hit"""
    if name in ('carter_akuma.png', 'carter_akuma_pose.png'):
        import build
        if name == 'carter_akuma_pose.png':
            return build.frame1().rgba()
        return strip([build.frame0().rgba(), build.frame1().rgba(),
                      build.frame2().rgba()], W, H)
    if name in ('carter_intro.png', 'carter_mark_glow.png', 'carter_aura.png',
                'carter_intro_flash.png'):
        import build_intro as BI
        if name == 'carter_intro.png':
            return strip(BI.build_intro(), W, H)
        if name == 'carter_mark_glow.png':
            glow, box = BI.build_mark_glow()
            return strip(glow, box[2], box[3])
        if name == 'carter_aura.png':
            return strip(BI.build_aura(), W, H)
        return BI.build_flash()
    import build_combat as BC
    for nm, fn, n in BC.SHEETS:
        if nm == name:
            return strip([fn(i).rgba() for i in range(n)], W, H)
    raise KeyError(name)


ALL = ['carter_akuma.png', 'carter_akuma_pose.png', 'carter_intro.png',
       'carter_mark_glow.png', 'carter_aura.png', 'carter_intro_flash.png',
       'carter_idle.png', 'carter_eye_flash.png', 'carter_rush.png',
       'carter_rush_pass.png', 'carter_spent.png', 'carter_hit.png',
       'carter_defeat.png', 'carter_victory.png', 'carter_look_back.png']


if __name__ == '__main__':
    names = sys.argv[1:] or ALL
    bad = sum(compare(n, render(n)) for n in names)
    sys.exit(1 if bad else 0)
