"""Build every RAGING DEMON effect into Assets/Characters/Carter/Demon/.

    python build_fx.py

Nothing here touches Carter's own sprites, the scenes or the scripts - the
other artist owns carter_akuma.png and the clone's rush pose, and this folder
only ever writes into Assets/Characters/Carter/Demon/.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import lights
import clone
import stage
import impacts
import finish

OUT = os.path.abspath(os.path.join('..', '..', 'Assets', 'Characters',
                                   'Carter', 'Demon'))


def p(name):
    return os.path.join(OUT, name).replace('\\', '/')


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    made = []
    made.append(lights.build(p('demon_light.png')))
    made.extend(clone.build(p('demon_clone.png'), p('demon_clone_ghost.png')))
    made.extend(stage.build(p('demon_spotlight.png'),
                            p('demon_spotlight_pool.png'),
                            p('demon_spotlight_cone.png'),
                            p('demon_darkness.png')))
    made.extend(impacts.build(p('demon_strike.png'), p('demon_parry_break.png')))
    made.append(finish.build(p('demon_finish.png')))

    from pngio import read_png
    for f in made:
        w, h, _ = read_png(f)
        print('%-28s %4d x %-4d  %6d bytes' % (os.path.basename(f), w, h,
                                               os.path.getsize(f)))
    return made


if __name__ == '__main__':
    main()
