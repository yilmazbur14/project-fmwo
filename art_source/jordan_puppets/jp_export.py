"""Jordan's puppets: the approval-pass writer. Builds every puppet with the recipe (jp_core.treat on
jp_bosses' data under both takes of jp_palette), audits them and writes the approval files.

A bare run writes nothing:

    python jp_export.py                       # print this and exit
    python jp_export.py --check               # build + audit everything, write nothing
    python jp_export.py --write               # write into art_source/jordan_puppets/approval/
    python jp_export.py --write --out DIR     # write into DIR instead (a scratch folder)
    python jp_export.py ... --only greyson,matt

It refuses any output folder inside Assets/ (realpath, so 8.3 short names cannot slip past) and any
folder in the project outside art_source/jordan_puppets/. Every sprite PNG gets an .aseprite beside it
(Aseprite CLI, batch mode), re-exported and compared pixel for pixel with the PNG (imgdiff.pixel_diff).

Nothing is written unless every idle frame passes the audit: the puppet palette only, no semi-alpha,
the TWIN RULE (the silhouette identical to the source's, every black pixel on its edge still black),
no keyline gaps, no new specks or pinholes, the frame size unchanged, every colour in the boss's table,
and every overlay, region and hook placed (a hook's ring wholly inside the silhouette).

What it writes, per boss in approval/<boss>/ (the sumo Danny, an extra, in approval/danny_sumo/):
  <boss>_before_1x / _after_A_1x / _after_B_1x      the idle key frame at the source frame size
  <boss>_before_6x / _after_A_6x / _after_B_6x      the same at 6x
  <boss>_compare_6x.png                               before | take A | take B, labelled
  <boss>_idle_A / _idle_B                             the finale idle frames, treated, as a strip
  <boss>_hooks.json                                   hook texels per idle frame, and per carry frame
  <boss>_carry_A.png                                  the recipe run on his fight sheets (source above)
and in approval/:
  puppets_lineup_3x.png            the nine at game scale on the void: before, take A, take B
  puppets_mock_A_1920x1080.png     the in-game mock, take A; puppets_mock_B_1920x1080.png, take B
  puppets_palette.png, report.txt
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jp_bosses as B  # noqa: E402
import jp_core as C  # noqa: E402
import jp_palette as PAL  # noqa: E402
import jp_present as PR  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

# The nine the finale disintegrated, in ladder order (the lineup), and the extra form built beside them.
LADDER = ['captain_burak', 'eric', 'greyson', 'matt', 'mason', 'josh', 'danny', 'carter', 'liam']
EXTRAS = ['danny_sumo']
DEFAULT_OUT = os.path.join(HERE, 'approval')
AUDITED = ('gaps', 'lone', 'holes', 'bad_keys', 'silhouette', 'edge_black_lost')


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def guard(out):
    if _under(out, os.path.join(C.ROOT, 'Assets')):
        raise SystemExit('refusing: %s is inside Assets' % out)
    if _under(out, C.ROOT) and not _under(out, HERE):
        raise SystemExit('refusing: %s is in the project but not in art_source/jordan_puppets' % out)


# ------------------------------------------------------------------ building

def build(boss):
    """The key frame before/after and the idle strip under both takes, with hooks and the audit."""
    r = {'boss': boss, 'frames': {}, 'hooks': {}, 'problems': []}
    key = boss.key_frame()
    r['before'] = Image.fromarray(key, 'RGBA')
    for take in ('A', 'B'):
        # the idle frames the finale plays, in order (the strip is hframes = len(idle), frame 0 left)
        strip = Image.new('RGBA', (len(boss.idle) * boss.fw, boss.fh), (0, 0, 0, 0))
        for i, f in enumerate(boss.idle):
            src = boss.src(f)
            im, info = C.treat(boss, src, take, key_src=key, sheet_rel=boss.sheet, frame_no=f)
            strip.alpha_composite(im, (i * boss.fw, 0))
            r['frames'][(take, f)] = (im, info)
            if take == 'A':
                r['hooks'][f] = info['hooks']
            lint = info['lint']
            for kind in AUDITED:
                if lint[kind]:
                    r['problems'].append('%s f%d take %s: %d %s %s' % (boss.name, f, take, len(lint[kind]), kind, lint[kind][:6]))
            for c in info.get('clipped', []):
                r['problems'].append('%s f%d take %s: %s' % (boss.name, f, take, c))
            if info['unknown']:
                r['problems'].append('%s f%d: colours not in the table %s' % (boss.name, f, info['unknown']))
            if info['skipped']:
                r['problems'].append('%s f%d take %s: not placed: %s' % (boss.name, f, take, info['skipped']))
            if im.size != (boss.fw, boss.fh):
                r['problems'].append('%s f%d: frame size changed' % (boss.name, f))
        r['strip_' + take] = strip
    r['after_A'] = r['frames'][('A', boss.idle[0])][0]
    r['after_B'] = r['frames'][('B', boss.idle[0])][0]
    return r


def _grid(ims, s, per_row=8, gap=4):
    rows = [ims[i:i + per_row] for i in range(0, len(ims), per_row)]
    return PR.vstack([PR.hstack([C.up(im, s) for im in row], gap=gap) for row in rows], gap=gap)


def carry(boss, take='A'):
    """The recipe run on every frame of the boss's fight sheets (boss.carry). Returns the contact
    image (per sheet: source frames above, puppet frames below), one summary line per sheet, the
    per-frame notes, and the tracked hook texels per sheet per frame (None where not found).
    A carry entry (sheet, frame width, 'prop') is a prop: recoloured only, no overlays or hooks."""
    key = boss.key_frame()
    blocks, summary, notes, hooks = [], [], [], {}
    for entry in boss.carry:
        rel, fw = entry[0], entry[1]
        prop = len(entry) > 2 and entry[2] == 'prop'
        b = boss
        if prop:
            b = B.Boss(boss.name, boss.title, boss.sheet, (boss.fw, boss.fh), boss.feet, boss.idle, '')
            b.table = boss.table_for(rel)
        fh = C.sheet(rel).shape[0]
        n = C.frames_in(rel, fw)
        tops, bots = [], []
        unknown, dirty, placed_ov, placed_hk = {}, 0, {}, {}
        hooks[rel] = {}
        for f in range(n):
            src = C.frame(rel, fw, fh, f)
            im, info = C.treat(b, src, take, key_src=key, sheet_rel=rel, frame_no=f)
            tops.append(Image.fromarray(src, 'RGBA'))
            bots.append(im)
            for h, k in info['unknown'].items():
                unknown[h] = unknown.get(h, 0) + k
            bad = {k: len(v) for k, v in info['lint'].items() if k in AUDITED and v}
            if bad or info.get('clipped'):
                dirty += 1
            for ov in b.overlays:
                placed_ov[ov['name']] = placed_ov.get(ov['name'], 0) + (ov['name'] not in info['skipped'])
            for hn in b.hooks:
                placed_hk[hn] = placed_hk.get(hn, 0) + (hn in info['hooks'])
            hooks[rel][str(f)] = {hn: (list(info['hooks'][hn]) if hn in info['hooks'] else None) for hn in b.hooks}
            notes.append('%s f%d: not placed %s; lint %s' % (
                os.path.basename(rel), f, info['skipped'] or '-', bad or 'clean'))
        s = 3 if fw <= 112 else 2
        shown = 12                           # the contact sheet shows the first 12; the audit ran on all
        blocks.append(PR.label(PR.vstack([_grid(tops[:shown], s), _grid(bots[:shown], s)], gap=6),
                               '%s  (%d frames of %dx%d; source above, take %s puppet below)%s' % (
                                   rel, n, fw, fh, take, '  PROP: recolour only' if prop else '')))
        line = '%s: %d frames, %s, twin rule %s' % (
            rel, n, 'every colour mapped' if not unknown else 'UNMAPPED %s' % unknown,
            'clean on every frame' if not dirty else 'broken on %d frames' % dirty)
        if not prop:
            line += '; overlays placed %s; hooks found %s' % (
                ', '.join('%s %d/%d' % (k, v, n) for k, v in placed_ov.items()) or '-',
                ', '.join('%s %d/%d' % (k, v, n) for k, v in placed_hk.items()))
        summary.append(line)
    img = PR.vstack(blocks, gap=16) if blocks else None
    return img, summary, notes, hooks


def palette_card():
    """The palette swatches with their hexes and roles, both takes."""
    keys = PAL.KEYS
    sw = 26
    im = Image.new('RGBA', (860, 44 + len(keys) * (sw + 4)), PR.DARK)
    d = ImageDraw.Draw(im)
    d.text((8, 6), 'PUPPET PALETTE  (16 colours per take; take A Blood & Ash | take B Rune; HG and ST are aliases)',
           fill=PR.LABEL)
    for i, k in enumerate(keys):
        y = 30 + i * (sw + 4)
        for j, take in enumerate(('A', 'B')):
            c = PAL.TAKES[take][k]
            d.rectangle((8 + j * (sw + 70), y, 8 + j * (sw + 70) + sw, y + sw), fill=c, outline=(80, 80, 90, 255))
            d.text((8 + j * (sw + 70) + sw + 4, y + 8), '#%02X%02X%02X' % c[:3], fill=PR.LABEL)
        d.text((200, y + 8), '%-3s %s' % (k, PAL.ROLE[k]), fill=PR.LABEL)
    return im


# The mock: attack 1's pair in front (Greyson, Matt), attack 2's pair behind (Captain Burak and the
# sumo Danny, whose sheets the butt slams use). Each string: (hook, hand, claw index).
MOCK = [
    ('captain_burak', (300, 1010), [('back', 'L', 0), ('head', 'L', 1), ('wrist_l', 'L', 2), ('wrist_r', 'L', 3)]),
    ('danny_sumo', (1610, 1010), [('back', 'R', 3), ('head', 'R', 2), ('wrist_l', 'R', 1), ('wrist_r', 'R', 0)]),
    ('greyson', (690, 1040), [('back', 'L', 0), ('head', 'L', 1), ('wrist_l', 'L', 2), ('wrist_r', 'L', 3),
                               ('knee_l', 'L', 1), ('knee_r', 'L', 2)]),
    ('matt', (1210, 1040), [('back', 'R', 3), ('head', 'R', 2), ('wrist_l', 'R', 1), ('wrist_r', 'R', 0),
                            ('knee_l', 'R', 2), ('knee_r', 'R', 1)]),
]


def mock_image(results, take):
    puppets = []
    for name, at, strings in MOCK:
        if name not in results:
            continue
        r = results[name]
        b = r['boss']
        puppets.append({'boss': b, 'image': r['after_' + take], 'hooks': r['hooks'][b.idle[0]], 'at': at,
                        'strings': strings})
    return PR.mock(puppets, take=take)


def lineup_image(results):
    names = [n for n in LADDER if n in results]
    bosses = {n: results[n]['boss'] for n in names}
    rows = [('before', {n: results[n]['before'] for n in names}),
            ('take A  Blood & Ash (ember)', {n: results[n]['after_A'] for n in names}),
            ('take B  Rune (blue)', {n: results[n]['after_B'] for n in names})]
    return PR.lineup(rows, bosses)


# ------------------------------------------------------------------ files

def aseprite(*args):
    subprocess.run([C.ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def save_sprite(im, path, tmp):
    """PNG + .aseprite beside it, the .aseprite round-tripped and compared pixel for pixel."""
    base = os.path.splitext(os.path.basename(path))[0]
    tpng = os.path.join(tmp, base + '.png')
    tase = os.path.join(tmp, base + '.aseprite')
    back = os.path.join(tmp, base + '_rt.png')
    im.save(tpng)
    aseprite(tpng, '--save-as', tase)
    aseprite(tase, '--save-as', back)
    d = pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (base, d))
    os.replace(tpng, path)
    os.replace(tase, os.path.splitext(path)[0] + '.aseprite')


def hooks_json(r):
    b = r['boss']
    return {
        'boss': b.name, 'sheet': 'res://Assets/Characters/' + b.sheet, 'frame': [b.fw, b.fh],
        'feet': list(b.feet), 'idle_frames': b.idle,
        'note': 'Texels on the frame, (0,0) its top-left; a ring hook is its hole, the texel the string '
                'ties to. "back" sits between the shoulder blades, behind the body on every front view: '
                'draw its string UNDER the sprite. "_l"/"_r" are screen left/right on the unflipped sheet '
                '(mirror x as frame_width - 1 - x when flipped). relative_to_feet = texel - feet. '
                'carry_frames: the same points tracked onto his fight sheets; null = not found there, '
                'to be filled by hand.',
        'frames': {str(f): {k: list(v) for k, v in hk.items()} for f, hk in r['hooks'].items()},
        'relative_to_feet': {str(f): {k: [v[0] - b.feet[0], v[1] - b.feet[1]] for k, v in hk.items()}
                             for f, hk in r['hooks'].items()},
        'carry_frames': r.get('carry_hooks', {}),
    }


def write(results, out, lines):
    guard(out)
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='jpup_')
    written = []
    try:
        for name, r in results.items():
            b = r['boss']
            d = os.path.join(out, name)
            guard(d)
            os.makedirs(d, exist_ok=True)
            for tag, im in (('before', r['before']), ('after_A', r['after_A']), ('after_B', r['after_B'])):
                save_sprite(im, os.path.join(d, '%s_%s_1x.png' % (name, tag)), tmp)
                save_sprite(C.up(im, 6, bg=(0, 0, 0, 0)), os.path.join(d, '%s_%s_6x.png' % (name, tag)), tmp)
                written += ['%s/%s_%s_1x.png+.aseprite' % (name, name, tag), '%s/%s_%s_6x.png+.aseprite' % (name, name, tag)]
            PR.compare(r['before'], r['after_A'], r['after_B'], b.title).save(os.path.join(d, '%s_compare_6x.png' % name))
            written.append('%s/%s_compare_6x.png' % (name, name))
            for take in ('A', 'B'):
                save_sprite(r['strip_' + take], os.path.join(d, '%s_idle_%s.png' % (name, take)), tmp)
                written.append('%s/%s_idle_%s.png+.aseprite' % (name, name, take))
            with open(os.path.join(d, '%s_hooks.json' % name), 'w', encoding='utf-8') as fh:
                json.dump(hooks_json(r), fh, indent=1)
            written.append('%s/%s_hooks.json' % (name, name))
            if r.get('carry_img') is not None:
                r['carry_img'].save(os.path.join(d, '%s_carry_A.png' % name))
                written.append('%s/%s_carry_A.png' % (name, name))
        if all(n in results for n in LADDER):
            lineup_image(results).save(os.path.join(out, 'puppets_lineup_3x.png'))
            written.append('puppets_lineup_3x.png')
        for take in ('A', 'B'):
            mock_image(results, take).save(os.path.join(out, 'puppets_mock_%s_1920x1080.png' % take))
            written.append('puppets_mock_%s_1920x1080.png' % take)
        palette_card().save(os.path.join(out, 'puppets_palette.png'))
        written.append('puppets_palette.png')
        with open(os.path.join(out, 'report.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
        written.append('report.txt')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return written


def report(results):
    lines, ok = [], True
    lines.append('PALETTE (16 colours per take)')
    for k in PAL.KEYS:
        lines.append('  %-3s A %s  B %s  %s' % (k, PAL.hexes('A')[k], PAL.hexes('B')[k], PAL.ROLE[k]))
    for name, r in results.items():
        b = r['boss']
        src = C.stats_img(r['before'])
        lines.append('')
        for take in ('A', 'B'):
            st = C.stats_img(r['after_' + take])
            lines.append('%-14s take %s: %dx%d, feet %s | black %.1f%% (source %.1f%%), colours %d (source %d), semi %d' % (
                name, take, b.fw, b.fh, b.feet, st['black'] * 100, src['black'] * 100, st['colours'], src['colours'], st['semi']))
        for f in b.idle:
            info = r['frames'][('A', f)][1]
            lint = info['lint']
            lines.append('   f%d hooks %s | tatter cuts %s | interior black recoloured %d %s | source pinholes kept %d, specks kept %d' % (
                f, info['hooks'], info.get('tatter', []), lint['inner_black_recoloured'], info.get('unblack', {}),
                lint['source_holes_kept'], lint['source_specks_kept']))
        for p in r['problems']:
            ok = False
            lines.append('   PROBLEM ' + p)
        for s in r.get('carry_summary', []):
            lines.append('   carry: ' + s)
    return ok, lines


def main(argv):
    if not argv or argv[0] not in ('--check', '--write'):
        print(__doc__)
        return 2
    out = DEFAULT_OUT
    only = None
    if '--out' in argv:
        out = os.path.abspath(argv[argv.index('--out') + 1])
    if '--only' in argv:
        only = argv[argv.index('--only') + 1].split(',')
    guard(out)
    names = [n for n in LADDER + EXTRAS if n in B.BOSSES and (only is None or n in only)]
    results = {}
    for n in names:
        r = build(B.BOSSES[n])
        img, summary, notes, hooks = carry(B.BOSSES[n])
        r['carry_img'], r['carry_summary'], r['carry_notes'], r['carry_hooks'] = img, summary, notes, hooks
        results[n] = r
    ok, lines = report(results)
    for ln in lines:
        print(ln)
    if not ok:
        print('audit FAILED: nothing written')
        return 1
    if argv[0] == '--write':
        for w in write(results, out, lines):
            print('wrote', w)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
