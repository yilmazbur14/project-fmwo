"""APPROVAL PASS (2026-09-29): PORTAL MONTE, Josh's third attack, cut to the plan's art contract
(scratchpad josh_hands/PLAN_portal_monte.md, "Art contract"). NOTHING here ships: `python jh_build_monte.py
--write` writes into art_source/josh_hands/approval_monte/ only, behind the same guard as jh_build.py (no
write outside this folder, the scratchpad or temp, none under Assets/, no process but Aseprite). A bare
run prints this and writes nothing.

  approval_monte/  josh_small_portal_{open,loop,burst,close}_{back,glow}.png, josh_dive.png,
                   josh_emerge.png (optional), josh_monte_slash.png, josh_monte_scatter.png (optional) -
                   each with its .aseprite (frame times + a tag, round-trip checked) - the contact sheet,
                   three mocks on the real arena, the GIF, and contract.json (every number the code needs).
"""
import json
import os
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jh_lib as H            # noqa: E402

OUT = os.path.join(HERE, 'approval_monte')


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    H.install_guard()
    from jh_build import write_sprite
    import jh_monte_sheets as MS
    import jh_monte_previews as MP
    tmp = tempfile.mkdtemp(prefix='jh_build_monte_')
    if not os.path.isdir(OUT):
        os.mkdir(OUT)
    written, audits, ships = [], {}, {}
    for spec in MS.all_sheets():
        p = write_sprite(tmp, OUT, spec['name'], spec['image'], spec['frames'], spec['fw'], spec['times'],
                         spec['tag'], spec['layer'])
        written.append(os.path.basename(p))
        audits[spec['name']] = MS.audit(spec)
        ships[spec['name'] + '.png'] = spec['ship'] + spec['name'] + '.png'
        print('wrote', written[-1], spec['image'].size, audits[spec['name']])
    for path in MP.build_all(OUT):
        written.append(os.path.basename(path))
        print('wrote', written[-1])
    contract = MS.contract()
    contract['audit'] = audits
    contract['ship_paths_after_approval'] = ships
    contract['files'] = written
    with open(os.path.join(OUT, 'contract.json'), 'w') as f:
        json.dump(contract, f, indent=1)
    print('wrote contract.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
