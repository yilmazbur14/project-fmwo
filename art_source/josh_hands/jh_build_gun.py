"""APPROVAL PASS (2026-09-29): Josh's card hands as finger guns in his Wild Cards, cut to the addendum's
art contract (scratchpad josh_hands/PLAN_addendum_gun.md). NOTHING here ships: `python jh_build_gun.py
--write` writes into art_source/josh_hands/approval_gun/ only, behind the same guard as jh_build.py (no
write outside this folder, the scratchpad or temp, none under Assets/, no process but Aseprite). A bare
run prints this and writes nothing.

  approval_gun/  josh_hand_gun_{form,idle,charge,fire}.png (+ _glow), josh_gun_beam_{start,tile,end}.png,
                 josh_gun_beam_glow.png, josh_gun_flash.png, josh_gun_charge_fx.png - each with its
                 .aseprite (frame times + a tag, round-trip checked) - the contact sheet, three mocks, the
                 GIF, and contract.json (GUN_MUZZLE, GUN_BOX_TEXELS, times, telegraph colours, posts).
"""
import json
import os
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jh_lib as H            # noqa: E402

OUT = os.path.join(HERE, 'approval_gun')


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    H.install_guard()
    from jh_build import write_sprite
    import jh_gun_sheets as GS
    import jh_gun_previews as GP
    tmp = tempfile.mkdtemp(prefix='jh_build_gun_')
    if not os.path.isdir(OUT):
        os.mkdir(OUT)
    written, audits = [], {}
    for spec in GS.all_sheets():
        p = write_sprite(tmp, OUT, spec['name'], spec['image'], spec['frames'], spec['fw'], spec['times'],
                         spec['tag'], spec['layer'])
        written.append(os.path.basename(p))
        audits[spec['name']] = GS.audit(spec)
        print('wrote', written[-1], spec['image'].size, audits[spec['name']])
    for path in GP.build_all(OUT):
        written.append(os.path.basename(path))
        print('wrote', written[-1])
    contract = GS.contract()
    contract['audit'] = audits
    contract['files'] = written
    with open(os.path.join(OUT, 'contract.json'), 'w') as f:
        json.dump(contract, f, indent=1)
    print('wrote contract.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
