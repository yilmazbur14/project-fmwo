"""The live beast sheets, built from rig poses.

    python anims.py                 # SAFE: every sheet into the scratchpad (all_sheets/), + previews
    python anims.py hover fly       # just these
    python anims.py --write         # ALSO writes Assets/Characters/Bixby/<sheet>.png + .aseprite
                                    # (each PNG in one save), round-trip checked with imgdiff

Frame order, counts and sizes follow Scripts/BixbyBeastArtLayout.gd; the timings for the GIFs are
read from there too (as literals copied below).
"""
import os
import subprocess
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import rig  # noqa: E402
import view  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
BIXBY = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby')
ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
OUT = os.path.join(view.SCRATCH, 'all_sheets')

SHEETS = {}          # name -> (file name, frame size, builder returning a list of frame images)
TIMES = {}           # name -> per-frame seconds for the GIF (from BixbyBeastArtLayout.ANIMS)
SEQUENCE = {}        # name -> frame order the fight plays, when it isn't just 0..n-1


def sheet(name, fname, size=(192, 160), times=(0.12,), sequence=None):
    def deco(fn):
        SHEETS[name] = (fname, size, fn)
        TIMES[name] = list(times)
        if sequence:
            SEQUENCE[name] = list(sequence)
        return fn
    return deco


def _poses(name):
    import rig_poses as RP
    return [rig.build(P).image() for P in getattr(RP, name)()]


@sheet('hover', 'bixby_beast.png', times=(0.12,))
def hover():
    return _poses('hover')


@sheet('fly', 'bixby_beast_fly.png', times=(0.09, 0.07, 0.08))
def fly():
    return _poses('fly')


@sheet('takeoff', 'bixby_beast_takeoff.png', times=(0.22, 0.12, 0.15))
def takeoff():
    return _poses('takeoff')


@sheet('land', 'bixby_beast_land.png', times=(0.2, 0.14, 0.35))
def land():
    return _poses('land')


@sheet('roar', 'bixby_beast_roar.png', times=(0.34, 0.07), sequence=[0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2])
def roar():
    return _poses('roar')


@sheet('recover', 'bixby_beast_recover.png', times=(0.18, 0.14, 0.18, 0.16))
def recover():
    return _poses('recover')


@sheet('hit', 'bixby_beast_hit.png', times=(0.08, 0.14))
def hit():
    return _poses('hit')


@sheet('dizzy', 'bixby_dizzy.png', times=(0.13,))
def dizzy():
    return _poses('dizzy')


@sheet('pound', 'bixby_pound.png', times=(0.09, 0.12, 0.07, 0.08, 0.08, 0.12),
       sequence=[0, 1, 2, 3, 4, 5, 2, 3, 4, 5])
def pound():
    return _poses('pound')


@sheet('firebreath', 'bixby_beast_firebreath.png', size=(192, 256), times=(0.6, 0.5, 0.8))
def firebreath():
    import rig_fire
    return rig_fire.frames()


@sheet('spin', 'bixby_spin.png', times=(0.11, 0.09, 0.1, 0.1, 0.1, 0.1, 0.2, 0.3),
       sequence=[0, 1, 2, 3, 4, 5, 2, 3, 4, 5, 6, 7])
def spin():
    import rig_spin
    return rig_spin.frames()


@sheet('shadow', 'bixby_beast_shadow.png', size=(192, 48), times=(0.12,))
def shadow():
    import rig_shadow
    return rig_shadow.air_frames()


@sheet('shadow_ground', 'bixby_beast_shadow_ground.png', size=(192, 48), times=(0.4,))
def shadow_ground():
    import rig_shadow
    return rig_shadow.ground_frames()


#WRITING

def strip(frames, size):
    fw, fh = size
    out = Image.new('RGBA', (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        if f.size != (fw, fh):
            g = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
            g.alpha_composite(f, (0, 0))
            f = g
        out.alpha_composite(f, (i * fw, 0))
    return out


def numbers(im):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    cnt = Counter(px)
    return dict(opaque=len(px), colours=len(cnt), black=round(100.0 * cnt.get((0, 0, 0, 255), 0) / max(1, len(px)), 2),
                semi=sum(1 for c in px if c[3] < 255))


def gif(frames, times, path, s=2, bg=(46, 49, 58), sequence=None):
    order = sequence or list(range(len(frames)))
    ims = []
    for i in order:
        f = frames[i]
        g = Image.new('RGBA', f.size, bg + (255,))
        g.alpha_composite(f)
        ims.append(g.convert('RGB').resize((f.width * s, f.height * s), Image.NEAREST))
    durs = [int(1000 * times[min(i, len(times) - 1)]) for i in range(len(ims))]
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=2)


def aseprite_roundtrip(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
    back = os.path.join(OUT, '_roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True)
    return pixel_diff(Image.open(png), Image.open(back))


def run(names, write=False):
    os.makedirs(OUT, exist_ok=True)
    results = {}
    for name in names:
        fname, size, fn = SHEETS[name]
        frames = fn()
        sh = strip(frames, size)
        scratch = os.path.join(OUT, fname)
        sh.save(scratch)
        gif(frames, TIMES[name], os.path.join(OUT, name + '.gif'), s=2, sequence=SEQUENCE.get(name))
        n = numbers(sh)
        line = '%-11s %-32s %2d x %dx%d  opaque %6d  colours %2d  black %5.2f%%  semi %d' % (
            name, fname, len(frames), size[0], size[1], n['opaque'], n['colours'], n['black'], n['semi'])
        if write:
            png = os.path.join(BIXBY, fname)
            sh.save(png)                                   # one save per sheet
            ase = os.path.splitext(png)[0] + '.aseprite'
            d = aseprite_roundtrip(png, ase)
            line += '  -> written, aseprite round trip: ' + (d or 'pixel-exact')
        print(line)
        results[name] = (frames, sh, n)
    return results


def contact(results, s=3):
    """Every sheet as a labelled row, on the arena mat's green, at s x (plus a 1x copy)."""
    from PIL import ImageDraw
    rows = [(name, results[name][1]) for name in SHEETS if name in results]
    gap, label = 6, 12
    W = max(sh.width for _, sh in rows)
    H = sum(sh.height + gap + label for _, sh in rows)
    out = Image.new('RGBA', (W, H), (118, 160, 96, 255))
    d = ImageDraw.Draw(out)
    y = 0
    for name, sh in rows:
        d.text((2, y), '%s  (%s)' % (name, SHEETS[name][0]), fill=(20, 24, 20, 255))
        y += label
        out.alpha_composite(sh, (0, y))
        y += sh.height + gap
    out.save(os.path.join(OUT, 'contact_1x.png'))
    out.resize((W * s, H * s), Image.NEAREST).save(os.path.join(OUT, 'contact_%dx.png' % s))
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    res = run(args or list(SHEETS), write='--write' in sys.argv)
    if not args:
        contact(res)
