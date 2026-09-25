"""Build the feint badge, and nothing else.

    python build_feint.py <out_dir>    a scratch build: <out_dir>/demon_feint.png
    python build_feint.py --ship       Assets/Characters/Carter/Demon/demon_feint.png

There is no default, and this script writes one file only. It is NOT build_fx.py, which rewrites every
Raging Demon sheet (demon_light.png among them) - never run that one bare (the memory note on art
exports run bare). After a --ship, re-save the PNG as .aseprite with the Aseprite CLI and round-trip it
through art_source/imgdiff.py pixel_diff.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

import feint                  # noqa: E402

SHIP = os.path.abspath(os.path.join(_HERE, '..', '..', 'Assets', 'Characters', 'Carter', 'Demon',
                                    'demon_feint.png'))


def main(path, ship=False):
    real = os.path.realpath(path).replace('\\', '/').lower()
    if not ship:
        assert '/assets/' not in real, 'only --ship writes into Assets: %s' % path
    else:
        assert real.endswith('/assets/characters/carter/demon/demon_feint.png'), real
    feint.build(path.replace('\\', '/'))
    print('wrote', path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('usage: python build_feint.py <out_dir> | --ship   (there is no default)')
    if sys.argv[1] == '--ship':
        main(SHIP, ship=True)
    else:
        os.makedirs(sys.argv[1], exist_ok=True)
        main(os.path.join(sys.argv[1], 'demon_feint.png'))
