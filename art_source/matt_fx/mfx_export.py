"""Build Matt's attack effects, check them, and (only with --ship) ship them to Assets/Characters/Matt/FX.

  python mfx_export.py                 build every sheet into the scratchpad (OUT), print the numbers and the
                                       pivots and hit polygon; touches nothing in the project
  python mfx_export.py --ship          also copy each PNG into Assets/Characters/Matt/FX in one write, save
                                       its .aseprite beside it with the Aseprite CLI, and round-trip that
                                       .aseprite back to a PNG checked by art_source/imgdiff.py pixel_diff
  python mfx_export.py --ship --only NAME [NAME ...] --replace NAME [NAME ...]
                                       ship only the named sheets (file names), and allow replacing those
                                       already shipped; unnamed sheets are left alone

It never overwrites a file in Assets that isn't named on --replace, so a bare --ship can't clobber a
shipped sheet, and a bare run (no --ship) writes only into the scratchpad.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image  # noqa: E402

import mfx_pal as pal  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

ASSETS = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Matt/FX'
OUT = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/matt_fx/out'
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'


def sheets():
    """file name -> (frames, frame size, layout note). Imported lazily so a stage can ship alone."""
    out = {}
    import mfx_bolt
    import mfx_spark
    import mfx_wave
    out['matt_mystic_bolt.png'] = (mfx_bolt.frames(), (40, 40),
                                   '12 frames: 22.5 deg f0-3, 45 deg f4-7, 67.5 deg f8-11; 0.05 s')
    out['matt_mystic_spark.png'] = (mfx_spark.frames(), (24, 24),
                                    '12 frames: top rope f0-5, left rope f6-11; 0.04 s')
    out['matt_trueshot_wave.png'] = (mfx_wave.frames(), (96, 96),
                                     '20 frames: 0/22.5/45/67.5/90 deg x 4; 0.05 s')
    out['matt_trueshot_wave_mid.png'] = (mfx_wave.frames_mid(), (96, 96),
                                         '16 frames: 11.25/33.75/56.25/78.75 deg x 4; 0.05 s')
    for mod, name in (('mfx_launch', 'matt_trueshot_launch.png'), ('mfx_glow', 'matt_trueshot_glow.png'),
                      ('mfx_aimdot', 'matt_aim_dot.png'), ('mfx_teleport', 'matt_teleport_fx.png'),
                      ('mfx_rings', 'matt_yell_rings.png'), ('mfx_streak', 'matt_mystic_streak.png'),
                      # Attack 2, the Glass Row (matt_plan_glass.md 6.3)
                      ('mfx_boom', 'matt_boom.png'), ('mfx_arrow', 'matt_boom_arrow.png'),
                      ('mfx_glassfloor', 'matt_glass_floor.png'), ('mfx_boomburst', 'matt_boom_burst.png'),
                      ('mfx_glint', 'matt_glass_glint.png'), ('mfx_shard', 'matt_glass_shard.png'),
                      ('mfx_shadow', 'matt_glass_shadow.png'), ('mfx_glassland', 'matt_glass_land.png'),
                      ('mfx_shatter', 'matt_glass_shatter.png'), ('mfx_root', 'matt_root.png'),
                      ('mfx_dust', 'matt_stomp_dust.png'), ('mfx_puff', 'matt_fury_puff.png')):
        if os.path.exists(os.path.join(HERE, mod + '.py')):
            m = __import__(mod)
            out[name] = (m.frames(), m.FRAME_SIZE, m.NOTE)
            if mod == 'mfx_launch':
                out['matt_trueshot_launch_mid.png'] = (
                    m.frames_mid(), m.FRAME_SIZE, '20 frames: 11.25/33.75/56.25/78.75 deg x 5; 0.05 s, once')
    return out


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('aseprite %s failed: %s %s' % (args, r.stdout, r.stderr))


def names_after(argv, flag):
    if flag not in argv:
        return None
    out = []
    for a in argv[argv.index(flag) + 1:]:
        if a.startswith('--'):
            break
        out.append(a)
    return set(out)


def report_numbers():
    """Pivots and the hit polygon, printed for the coder."""
    import mfx_bolt
    import mfx_hitpoly
    lines = ['bolt pivots (core texel; its centre is the pivot): %s' % mfx_bolt.pivots()]
    poly, m, rep = mfx_hitpoly.polygon()
    lines.append('TRUESHOT_HIT_POLY (%d points, %s)' % (len(poly), rep))
    lines.append('  texels: ' + mfx_hitpoly.gd_literal(poly, 1))
    lines.append('  px(3x): ' + mfx_hitpoly.gd_literal(poly, 3))
    return '\n'.join(lines)


def main(argv):
    ship = '--ship' in argv
    replace = names_after(argv, '--replace') or set()
    only = names_after(argv, '--only')
    os.makedirs(OUT, exist_ok=True)
    built = sheets()
    for name, (frames, (fw, fh), note) in built.items():
        im = pal.strip(frames)
        assert im.size == (fw * len(frames), fh), (name, im.size)
        im.save(os.path.join(OUT, name))
        st = pal.stats(im)
        print('%-26s %5dx%-3d %2d frames of %dx%d  colours %2d  alphas %s  (%s)'
              % (name, im.width, im.height, len(frames), fw, fh, st['colours'], st['alphas'], note))
    numbers = report_numbers()
    print(numbers)
    with open(os.path.join(OUT, 'numbers.txt'), 'w') as fh_:
        fh_.write(numbers + '\n')
    if not ship:
        print('built into', OUT, '(pass --ship to ship)')
        return 0
    os.makedirs(ASSETS, exist_ok=True)
    bad = 0
    for name in built:
        if only is not None and name not in only:
            continue
        src = os.path.join(OUT, name)
        dst = os.path.join(ASSETS, name)
        ase = dst[:-4] + '.aseprite'
        for p in (dst, ase):
            if os.path.exists(p) and os.path.basename(p).replace('.aseprite', '.png') not in replace:
                print('REFUSED: %s exists; name it on --replace to overwrite' % p)
                return 1
        shutil.copyfile(src, dst)
        aseprite(dst, '--save-as', ase)
        rt = os.path.join(OUT, 'roundtrip_' + name)
        aseprite(ase, '--save-as', rt)
        diff = pixel_diff(Image.open(dst), Image.open(rt))
        same_src = pixel_diff(Image.open(src), Image.open(dst))
        print('%-26s shipped; .aseprite round trip: %s; copy check: %s'
              % (name, diff or 'identical', same_src or 'identical'))
        bad += bool(diff) + bool(same_src)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
