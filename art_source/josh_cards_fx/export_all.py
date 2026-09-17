"""Build every Josh card prop / effect into Assets/Characters/Josh/Cards/.

  python export_all.py                  write the PNGs and .aseprite files
  python export_all.py --overwrite      allow replacing this script's own previous output
  python export_all.py --check          rebuild and compare against what is on disk, no writes

Every sheet is validated before it ships: alpha strictly 0/255, and no colour outside the
project palette in fxlib.PAL.
"""
import os, sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *
import giant, bomb, projectile, specials, status, glider, bursts

CHECK = '--check' in sys.argv
OVERWRITE = '--overwrite' in sys.argv
MINE = set()


def may_write(path):
    if os.path.exists(path) and not OVERWRITE and path not in MINE:
        raise SystemExit('REFUSING to overwrite an existing file: ' + path)


def emit(canvas, name):
    path = OUT + name
    MINE.add(path)
    if CHECK:
        w, h, px = read_png(path)
        assert (w, h) == (canvas.w, canvas.h), (name, w, h, canvas.w, canvas.h)
        assert px == canvas.rgba(), 'pixels differ from disk: ' + name
        print('  check OK  %-26s %dx%d' % (name, w, h))
        return path
    may_write(path)
    canvas.save(path)
    check_png(path)
    print('  wrote %-26s %dx%d' % (name, canvas.w, canvas.h))
    return path


def ase(frames, name, durations, tags=()):
    path = OUT + name
    MINE.add(path)
    if CHECK:
        assert os.path.exists(path), 'missing ' + name
        print('  check OK  %-26s' % name)
        return path
    may_write(path)
    build_ase(path, frames, durations, tags)
    print('  wrote %-26s %d frames' % (name, len(frames)))
    return path


def main():
    if not CHECK:
        os.makedirs(OUT, exist_ok=True)

    print('giant card')
    card = giant.build()
    shadow = giant.build_shadow()
    imp = giant.build_impact()
    emit(card, 'card_giant.png')
    emit(shadow, 'card_giant_shadow.png')
    emit(sheet(imp), 'card_giant_impact.png')
    ase([card], 'card_giant.aseprite', [100])
    ase([shadow], 'card_giant_shadow.aseprite', [100])
    ase(imp, 'card_giant_impact.aseprite', [50, 50, 60, 70, 90], [('slam', 0, 4)])

    print('bomb card')
    bf = bomb.build()
    emit(sheet(bf, cols=len(bf)), 'card_bomb.png')
    ase(bf, 'card_bomb.aseprite', bomb.DURATIONS, bomb.TAGS)

    print('thrown card')
    pf = projectile.build()
    emit(sheet(pf), 'card_projectile.png')
    ase(pf, 'card_projectile.aseprite', projectile.DURATIONS, projectile.TAGS)

    print('phase-2 specials')
    sp = specials.build()
    emit(sp, 'card_specials.png')
    ase([sp], 'card_specials.aseprite', [100])

    print('glider + shadow')
    gl = glider.build()
    emit(sheet(gl), 'josh_glider.png')
    ase(gl, 'josh_glider.aseprite', glider.DURATIONS, glider.TAGS)
    sh = glider.build_shadow()
    emit(sheet(sh), 'josh_shadow.png')
    ase(sh, 'josh_shadow.aseprite', glider.SHADOW_DURATIONS, glider.SHADOW_TAGS)

    print('shatter + bursts')
    sf = bursts.build_shatter()
    emit(sheet(sf), 'card_shatter.png')
    ase(sf, 'card_shatter.aseprite', bursts.SHATTER_DURATIONS, bursts.SHATTER_TAGS)
    bu = bursts.build_burst()
    emit(sheet(bu), 'card_burst.png')
    ase(bu, 'card_burst.aseprite', bursts.BURST_DURATIONS, bursts.BURST_TAGS)
    ra = bursts.build_rain()
    emit(sheet(ra), 'card_burst_rain.png')
    ase(ra, 'card_burst_rain.aseprite', bursts.RAIN_DURATIONS, bursts.RAIN_TAGS)

    print('status icons')
    st = status.build()
    emit(st, 'status_icons.png')
    ase([st], 'status_icons.aseprite', [100])

    print('\n%d files %s' % (len(MINE), 'checked' if CHECK else 'written'))


if __name__ == '__main__':
    main()
