"""Build Carter's combat set into Assets/Characters/Carter.

    python build_combat.py

Writes, all 96x96 frames on a horizontal strip, feet plane on row 95:

  carter_idle.png        4 frames, loops
  carter_eye_flash.png   4 frames, one shot
  carter_rush.png        4 frames, travelling RIGHT (code flips it)
  carter_rush_pass.png   3 frames, one shot
  carter_spent.png       4 frames, loops
  carter_hit.png         2 frames, one shot
  carter_defeat.png      6 frames, one shot, holds on the last
  carter_victory.png     7 frames, one shot into a loop from frame 4
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import carter_scale
carter_scale.apply()          # draw him at his reduced size
from lib import W, H
from pngio import write_png, blank, paste
import combat_poses as CP
import combat_rush as CR
import combat_victory as CVI

OUT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..', 'Assets', 'Characters', 'Carter'))

SHEETS = [
    ('carter_idle.png', CP.idle, 4),
    ('carter_eye_flash.png', CP.eye_flash, 4),
    ('carter_rush.png', CR.frame, 4),
    ('carter_rush_pass.png', CP.rush_pass, 3),
    ('carter_spent.png', CP.spent, 4),
    ('carter_hit.png', CP.hit, 2),
    ('carter_defeat.png', CP.defeat, 6),
    ('carter_victory.png', CVI.frame, CVI.N),
]

# milliseconds per frame, as quoted in the report
TIMINGS = {
    'carter_idle.png': [180, 180, 180, 180],
    'carter_eye_flash.png': [120, 90, 90, 260],
    'carter_rush.png': [50, 45, 60, 55],
    'carter_rush_pass.png': [45, 50, 70],
    'carter_spent.png': [200, 170, 170, 200],
    'carter_hit.png': [70, 90],
    'carter_defeat.png': [110, 110, 100, 130, 180, 700],
    'carter_victory.png': CVI.MS,
}


def build(name, fn, n):
    sheet = blank(W * n, H)
    for i in range(n):
        paste(sheet, fn(i).rgba(), i * W, 0)
    path = os.path.join(OUT, name)
    write_png(path, W * n, H, sheet)
    print('%-24s %4dx%-3d %d frames' % (name, W * n, H, n))
    return sheet


if __name__ == '__main__':
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name, fn, n in SHEETS:
        if only and only not in name:
            continue
        build(name, fn, n)
    print('wrote to', OUT)
