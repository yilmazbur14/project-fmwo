"""Jordan's funko minions - generator entry point (design pass, 2026-09-17).

Outputs (horizontal strips, alpha 0/255 only, pure-black outlines, shown in game at scale 3):
  Assets/Characters/Jordan/Funkos/funko_<fig>.png      8 x 24x24: chase 0-3, fuse 4-5, punched 6-7
                                                       fig = plumber | hedgehog | mascot | gamer
  Assets/Characters/Jordan/Funkos/funko_spawn_pop.png  4 x 32x32
  Assets/Characters/Jordan/Funkos/funko_explosion.png  6 x 64x64 (smoke ring at ~30 art px = 90 screen px)
Per-frame PNGs go to <FUNKO_WORK>/frames/ for rebuilding the matching .aseprite files
(one frame per cell, tags chase/fuse/punched, pop, explode).

Usage:
  python build.py           write the six PNG sheets into the project + per-frame PNGs
  python build.py --check   rebuild in memory and compare with the PNGs already in the project (no writes)
  python previews.py        design sheet, contract sheet, GIFs  -> FUNKO_PREVIEW
  python mockup.py          1920x1080 arena mockup (needs the arena render below)
  python mockup_gif.py      animated chase scene
Arena render (writes nothing to the project), from the project folder:
  "C:/Users/theyi/Downloads/Godot_v4.6.3-stable_win64.exe/Godot.exe.exe" --path <project>
      --write-movie <FUNKO_WORK>/arena/frame.png --fixed-fps 30 --quit-after 3 res://Scenes/Core/ArenaScene.tscn

Module map: lib/pngio/gifio/font = helpers; rig = head+torso+role-coloured body poses;
figures = the four designs (masters, palettes, torso blocks, role colours); chase/fuse/punched = figure
animations; pop/explosion = shared effects."""
import sys
import os
from figures import FIGURES
from chase import chase_frames, DUST
from fuse import fuse_frames
from punched import punched_frames
from pop import pop_frames
from explosion import explosion_frames
from lib import *

FRAMES_DIR = WORK + 'frames/'
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(OUT_ASSETS, exist_ok=True)


def figure_frames(fig):
    return chase_frames(fig) + fuse_frames(fig) + punched_frames(fig)


def check_frames(name, frames):
    ok = True
    for i, f in enumerate(frames):
        ok &= audit(f, '%s[%d]' % (name, i)) if False else not (set(p[3] for r in f for p in r) - {0, 255})
    return ok


def write_all(to_assets=True):
    results = {}
    for fig in FIGURES:
        fr = figure_frames(fig)
        assert all(size(f) == (24, 24) for f in fr)
        sheet = hstack(fr)
        assert check_frames(fig.name, fr)
        name = 'funko_%s' % fig.name
        if to_assets:
            save(sheet, OUT_ASSETS + name + '.png')
        for i, f in enumerate(fr):
            save(f, FRAMES_DIR + '%s_%d.png' % (name, i))
        results[name] = fr
    pop = pop_frames()
    assert check_frames('pop', pop)
    exp = explosion_frames()
    assert check_frames('explosion', exp)
    for name, fr in (('funko_spawn_pop', pop), ('funko_explosion', exp)):
        if to_assets:
            save(hstack(fr), OUT_ASSETS + name + '.png')
        for i, f in enumerate(fr):
            save(f, FRAMES_DIR + '%s_%d.png' % (name, i))
        results[name] = fr
    return results


def check():
    res = write_all(to_assets=False)
    bad = 0
    for name, fr in res.items():
        w, h, px = read_png(OUT_ASSETS + name + '.png')
        sheet = hstack(fr)
        same = size(sheet) == (w, h) and all(
            (sheet[y][x] == px[y][x]) or (sheet[y][x][3] == 0 and px[y][x][3] == 0)
            for y in range(h) for x in range(w))
        print('%-20s %s' % (name, 'identical' if same else 'DIFFERS'))
        bad += 0 if same else 1
    return bad


if __name__ == '__main__':
    if '--check' in sys.argv:
        raise SystemExit(check())
    res = write_all(to_assets=True)
    for k, v in res.items():
        cols = set(p[:3] for f in v for r in f for p in r if p[3])
        print('%-20s frames=%d size=%dx%d colours=%d' % (k, len(v), len(v[0][0]), len(v[0]), len(cols)))
