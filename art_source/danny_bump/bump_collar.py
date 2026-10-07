"""Take 2 of the belly-bump side view: the collar scrap showing under his jowl in profile (bump_rig.collar_band).

The user approved "the collar showing in profile" on 2026-09-30, but the shipped side view still hid it under the
double chin (Danny D measured it in game). This builds the same sheets with only the collar band switched on; the
silhouette, frame size, anchors, timings and every other texel outside the neck stay as they are, and the script
proves it (same texel set per frame, every changed texel within the neck box, anchors identical).

    python bump_collar.py              build, lint, compare, print the numbers. WRITES NOTHING.
    python bump_collar.py --preview    also the comparison still and the GIF, into the scratch folder
    python bump_collar.py --write      also the new take into approval/: danny_sumo_bump_collar.png + .aseprite
                                       (and the optional danny_sumo_back_collar.png + .aseprite), the 3x neck
                                       comparison and the GIF. It refuses to overwrite an existing file, and it
                                       never touches the approved/shipped takes, Assets or the project.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402

import bump_export as E  # noqa: E402  (its lint, numbers, guard and Aseprite round trip; its main() is not run)
import bump_rig as R  # noqa: E402
import bump_sheets as S  # noqa: E402

K = R.K
BG = (46, 49, 58, 255)
TAKES = {'danny_sumo_bump': 'danny_sumo_bump_collar', 'danny_sumo_back': 'danny_sumo_back_collar'}
COLLAR_RGB = {R.L.PAL['R'][:3], R.L.PAL['M'][:3]}          # (172,50,50) and (122,36,48), as Danny D counted


def with_band(spec):
    if 'side' not in spec:
        return spec
    sp = dict(spec)
    sp['side'] = dict(spec['side'], collar_band=True)
    return sp


def neck_box(sheet, spec, off):
    """The box the band may change: round the neck, in the sheet frame."""
    sp = dict(R.DEFAULT, **spec['side'])
    pz = R.SD.Pose({k: v for k, v in sp.items() if k in R.SD.DEFAULT})
    nx, ny = pz.neck((0.0, 0.0))
    return (int(nx) + off[0] - 40, int(ny) + off[1] - 40, int(nx) + off[0] + 40, int(ny) + off[1] + 40)


def collar_count(px):
    return sum(1 for k in px.values() if R.L.PAL[k][:3] in COLLAR_RGB)


def build(sheet):
    cfg = S.SHEETS[sheet]
    w, h = cfg['size']
    rows = []
    for i, (name, spec, ms) in enumerate(cfg['frames']):
        old, off, _ = S.frame_map(sheet, spec)
        new_spec = with_band(spec)
        new, off2, full = S.frame_map(sheet, new_spec)
        assert off == off2 and len(full) == len(new), (sheet, name, 'placement changed')
        changed = [q for q in new if new[q] != old.get(q)]
        box = neck_box(sheet, spec, off) if 'side' in spec else None
        stray = [q for q in changed if not (box and box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3])]
        rows.append(dict(i=i, name=name, spec=new_spec, ms=ms, old=old, new=new, off=off, same_set=set(old) == set(new),
                         changed=len(changed), stray=len(stray)))
    im = Image.new('RGBA', (w * len(rows), h), (0, 0, 0, 0))
    for r in rows:
        im.alpha_composite(R.FT.image_of(r['new'], w, h), (w * r['i'], 0))
    return rows, im


def neck_compare(sheet, rows, idx, s=3):
    """Old vs new at 3x on the neck, one frame a row."""
    w, h = S.SHEETS[sheet]['size']
    cw, ch = 80, 60
    out = Image.new('RGBA', (2 * (cw * s + 8) + 8, len(idx) * (ch * s + 24) + 8), (24, 25, 31, 255))
    d = ImageDraw.Draw(out)
    for j, i in enumerate(idx):
        r = rows[i]
        sp = dict(R.DEFAULT, **r['spec']['side'])
        pz = R.SD.Pose({k: v for k, v in sp.items() if k in R.SD.DEFAULT})
        nx, ny = pz.neck((0.0, 0.0))
        cx, cy = int(nx) + r['off'][0], int(ny) + r['off'][1]
        for col, (tag, px) in enumerate((('shipped', r['old']), ('collar take', r['new']))):
            cell = Image.new('RGBA', (w, h), BG)
            cell.alpha_composite(R.FT.image_of(px, w, h))
            crop = cell.crop((cx - 36, cy - 30, cx - 36 + cw, cy - 30 + ch)).resize((cw * s, ch * s), Image.NEAREST)
            x0, y0 = 8 + col * (cw * s + 8), 8 + j * (ch * s + 24) + 16
            out.alpha_composite(crop, (x0, y0))
            d.text((x0 + 2, y0 - 14), 'f%d %s  %s  collar reds %d' % (i, r['name'], tag, collar_count(px)),
                   fill=(230, 230, 235, 255))
    return out


def gif_windup_run(rows, path, save, s=2):
    w, h = S.SHEETS['danny_sumo_bump']['size']
    order = [0, 1, 2, 3, 4, 5, 6, 3, 4, 5, 6, 7]
    ims, durs = [], []
    for i in order:
        cell = Image.new('RGBA', (w, h), BG)
        cell.alpha_composite(R.FT.image_of(rows[i]['new'], w, h))
        ims.append(cell.resize((w * s, h * s), Image.NEAREST).convert('RGB').quantize(colors=255, dither=Image.Dither.NONE))
        durs.append(rows[i]['ms'])
    save(ims[0], path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1)


def main():
    args = sys.argv[1:]
    write, preview = '--write' in args, '--preview' in args
    src = E.approved_stats()
    fatal = 0
    built = {}
    for sheet in TAKES:
        rows, im = build(sheet)
        built[sheet] = (rows, im)
        print('\n%s -> %s' % (sheet, TAKES[sheet]))
        for r in rows:
            lint = E.lint_body(sheet, r['name'], r['spec'], r['new'], src)
            a_old = E.body_anchors(sheet, r['i'], r['name'], S.SHEETS[sheet]['frames'][r['i']][1], r['old'], r['off'])
            a_new = E.body_anchors(sheet, r['i'], r['name'], r['spec'], r['new'], r['off'])
            fails = list(lint['fails'])
            if not r['same_set']:
                fails.append('silhouette changed')
            if r['stray']:
                fails.append('%d changed texels outside the neck box' % r['stray'])
            if a_old != a_new:
                fails.append('anchors changed')
            fatal += len(fails)
            print('  f%-2d %-9s collar reds %3d -> %3d   changed %3d texels   black %5.1f%%  col %2d  %s' % (
                r['i'], r['name'], collar_count(r['old']), collar_count(r['new']), r['changed'], 100 * lint['black'],
                lint['colours'], '; '.join(fails) or 'clean'))
    print('\n%d fatal findings' % fatal)
    if fatal:
        raise SystemExit('nothing written')
    if not (write or preview):
        print('(nothing written: --preview for the scratch folder, --write for the approval folder)')
        return
    dest = E.APPROVAL if write else os.path.join(E.SCRATCH, 'collar')
    outs = {os.path.join(dest, 'collar_compare_3x.png'): None, os.path.join(dest, 'gif_bump_collar_windup_run.gif'): None}
    if write:
        for sheet, take in TAKES.items():
            for ext in ('.png', '.aseprite'):
                p = os.path.join(E.APPROVAL, take + ext)
                if os.path.exists(p):
                    raise SystemExit('REFUSED: %s exists (nothing overwritten)' % p)
        for p in outs:
            if os.path.exists(p):
                raise SystemExit('REFUSED: %s exists (nothing overwritten)' % p)
    rows_b = built['danny_sumo_bump'][0]
    E.save(neck_compare('danny_sumo_bump', rows_b, [0, 2, 7]), os.path.join(dest, 'collar_compare_3x.png'))
    gif_windup_run(rows_b, os.path.join(dest, 'gif_bump_collar_windup_run.gif'), E.save)
    if write:
        for sheet, take in TAKES.items():
            d2, d3 = E.write_sheet(built[sheet][1], take)
            print('wrote %s.png + .aseprite: .aseprite -> .png %s; written vs build %s' % (
                take, d2 or 'texel-identical', d3 or 'texel-identical'))
            if d2 or d3:
                raise SystemExit(1)
    else:
        for sheet, take in TAKES.items():
            E.save(built[sheet][1], os.path.join(dest, take + '.png'))
    print('written into', dest)


if __name__ == '__main__':
    main()
