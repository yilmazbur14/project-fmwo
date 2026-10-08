"""Check and write matt_echo (Echo Roars body sheet, PLAN.md section 5). A bare run writes NOTHING:

    python ea_export.py <out_dir>            # matt_echo.png + .aseprite + _3x.png + numbers.json there
    python ea_export.py --ship [--replace]   # ONLY matt_echo.png + matt_echo.aseprite into
                                             # Assets/Characters/Matt/ (refuses to overwrite without --replace)

<out_dir> may not be inside the project. guard.py refuses every other write into the project, and any
process but Aseprite. Each .aseprite is round-tripped through Aseprite and compared with its PNG by
imgdiff.pixel_diff (alpha everywhere, colour wherever a pixel shows).

Checked before anything is written, per frame (the contract, PLAN.md section 5):
  - 96x96 in one horizontal strip of 6 (576x96), soles on row 95, nothing above row 1
  - only the approved sheet's 41 colours, black is pure #000000, no semi-alpha
  - no keyline gaps, lone texels or pinholes (B.audit)
  - black 24.7-25.5% (his fight set), every frame
  - crest top (MattArtLayout's CROWNS) at y <= 13
  - mouth within 2 texels of (48, 51) on f1, f2, f4, f5
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guard  # noqa: E402
import env  # noqa: E402
import ea_base as E  # noqa: E402,F401
from ea_base import B, F  # noqa: E402
import ea_echo as EC  # noqa: E402
import mi_anchors as AN  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

BLACK = (0.247, 0.255)
RING_MOUTH = (48, 51)
RING_FRAMES = (1, 2, 4, 5)


def sole_centres(px):
    out = []
    for side in (0, 1):
        xs = sorted(x for (x, y) in px if y == 95 and ((x < 48) if side == 0 else (x > 48)))
        out.append(((xs[0] + xs[-1]) / 2.0, 95))
    return out


def build():
    allowed = {c for c in B.flat(B.approved_sheet()) if c[3]}
    assert len(allowed) == 41, len(allowed)
    problems, rows, frames = [], [], []
    for i, f in enumerate(EC.figs()):
        px = F.px_of(f)
        frames.append(px)
        im = B.image(px)
        st = B.stats(im)
        cols = {c for c in B.flat(im) if c[3]}
        a = B.audit(px, f.fx)
        x0, y0, x1, y1 = B.bbox(px)
        anc = AN.anchors(f, px)
        tag = 'f%d %s' % (i, EC.LABELS[i])
        if cols - allowed:
            problems.append('%s: colours outside the approved 41' % tag)
        if {c for c in cols if c[:3] == (0, 0, 0)} - {(0, 0, 0, 255)}:
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: semi-alpha' % tag)
        if any(a.values()):
            problems.append('%s: audit %s' % (tag, {k: v[:5] for k, v in a.items() if v}))
        if y1 != 95 or y0 < 1:
            problems.append('%s: rows %d..%d' % (tag, y0, y1))
        if not BLACK[0] <= st['black'] <= BLACK[1]:
            problems.append('%s: black %.2f%%' % (tag, 100 * st['black']))
        if anc['crest_top'][1] > 13:
            problems.append('%s: crest top on row %d' % (tag, anc['crest_top'][1]))
        if i in RING_FRAMES:
            dx, dy = anc['mouth'][0] - RING_MOUTH[0], anc['mouth'][1] - RING_MOUTH[1]
            if max(abs(dx), abs(dy)) > 2:
                problems.append('%s: mouth %s, more than 2 texels off %s' % (tag, anc['mouth'], RING_MOUTH))
        rows.append({'frame': i, 'name': EC.LABELS[i], 'approval': i in EC.APPROVAL,
                     'black_pct': round(100 * st['black'], 2), 'colours': len(cols), 'opaque': st['opaque'],
                     'bbox': [x0, y0, x1, y1], 'crest_top': list(anc['crest_top']), 'dome_crown': list(anc['crown']),
                     'mouth': list(anc['mouth']), 'soles': sole_centres(px)})
    im = B.strip(frames)
    if im.size != (576, 96):
        problems.append('strip is %s' % (im.size,))
    st = B.stats(im)
    return im, rows, problems, {'sheet_black_pct': round(100 * st['black'], 2), 'sheet_colours': st['colours']}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    im, rows, problems, sheet = build()
    for r in rows:
        print('f%d %-20s black %.2f%%  colours %2d  bbox %s  crest_top %s  mouth %s  soles %s' % (
            r['frame'], r['name'], r['black_pct'], r['colours'], r['bbox'], r['crest_top'], r['mouth'], r['soles']))
    print('sheet: black %.2f%%, %d colours' % (sheet['sheet_black_pct'], sheet['sheet_colours']))
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    if argv[0] == '--ship':
        out = env.LIVE_MATT
        targets = [os.path.join(out, EC.NAME + ext) for ext in ('.png', '.aseprite')]
        if any(os.path.exists(t) for t in targets) and '--replace' not in argv:
            print('NOT WRITTEN: %s exists; pass --replace to overwrite' % targets)
            return 1
        guard.allow(targets)
        png, ase, rt = B.write_sheet(EC.NAME, im, out)
        print('shipped', png, ase, '| .aseprite round trip:', rt or 'identical')
        return 1 if rt else 0
    out = os.path.abspath(argv[0])
    real = os.path.normcase(os.path.realpath(out))
    if real == os.path.normcase(env.LIVE) or real.startswith(os.path.normcase(env.LIVE) + os.sep):
        print('NOT WRITTEN: %s is inside the project; use --ship for the live sheet' % out)
        return 1
    png, ase, rt = B.write_sheet(EC.NAME, im, out)
    on_disk = pixel_diff(im, Image.open(png))
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(out, EC.NAME + '_3x.png'))
    with open(os.path.join(out, EC.NAME + '_numbers.json'), 'w') as fh:
        json.dump({'frames': rows, 'sheet': sheet, 'aseprite_round_trip': rt or 'identical',
                   'png_on_disk': on_disk or 'identical'}, fh, indent=1)
    print('wrote', png, ase, '| .aseprite round trip:', rt or 'identical', '| png on disk:', on_disk or 'identical')
    return 1 if (rt or on_disk) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
