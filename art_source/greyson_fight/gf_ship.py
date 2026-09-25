"""Ship Greyson's LIVE takeover sheets (scratchpad greyson_fight/PLAN.md sections 6 and 7), each a
horizontal strip of 112x112 frames with its .aseprite beside it. Nothing here is wired: the coder
wires them in Phase 3. A bare run writes nothing:

    python -B gf_ship.py                                  # prints this, writes nothing
    python -B gf_ship.py <scratch_dir> [--only NAME]      # writes there, for checking
    python -B gf_ship.py --ship [--only NAME] [--replace] # writes into Assets/Characters/Greyson/

Safety (a bare run of an old art_source exporter once clobbered shipped art in this project):
  - Only `--ship` writes into Assets, and only into Assets/Characters/Greyson/. A scratch folder
    that resolves anywhere under Assets is refused, compared by os.path.realpath (8.3 short names
    are on for this drive, so abspath alone can be fooled).
  - It only ever writes the sheet names in SHEETS below (.png and .aseprite). It never touches
    greyson_redesign.* (the design of record), greyson_fight_approval.* or portrait.*.
  - An existing file is never overwritten without --replace.
  - Each file is built in a temp folder and moved into place in one step, and the .aseprite is
    re-exported by Aseprite and compared with the PNG pixel for pixel (art_source/imgdiff), in the
    temp folder and again where it landed.
  - gf_base proves on import that the approved rig still draws the approved sprite exactly.

Checked before anything is written, per frame: 112x112; the lowest drawn row is 111 (his feet);
nothing on the frame's other three edges; every colour in the fight palette; pure-black keyline;
no semi-alpha; no keyline gaps, strays or pinholes; black within 15-29% (the cast's band).
Sheets whose frames stand on both feet are also checked to be centred on column 56.
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gf_base as B  # noqa: E402  (proves the approved rig on import)
import gf_takeover  # noqa: E402
import gf_tear  # noqa: E402
import gf_attach  # noqa: E402
import gf_cannonset  # noqa: E402
import gf_hurl  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

K = B.K
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.realpath(os.path.join(B.ROOT, 'Assets'))
SHIP_DIR = os.path.realpath(os.path.join(B.ROOT, 'Assets', 'Characters', 'Greyson'))
FW = FH = 112
FEET_ROW = 111
BLACK_RANGE = (0.15, 0.29)
PROTECTED = ('greyson_redesign', 'greyson_fight_approval', 'portrait')
CROWN_BAND = (40, 72)

# name: (frame function, frame count, centred on both feet?, timing note)
SHEETS = {
    'greyson_walk': (gf_takeover.walk, 6, False,
                     '6 x 0.10 s looping; 0 and 3 are the contacts (shake on those)'),
    'greyson_talk': (gf_takeover.talk, 6, True,
                     'pairs (shut, open) flapped at 0.12 s while a line types: 0-1 grief, '
                     '2-3 fond, 4-5 fury'),
    'greyson_tear': (gf_tear.frame, 5, True,
                     'f0 grip 0.25 s; f1/f2 strain alternated at 0.08 s under the shake; f3 RIP '
                     '0.15 s; f4 hold up to the end of the beat. Drawn with Computah on his LEFT'),
    'greyson_attach': (gf_attach.frame, 3, True,
                       'f0 0.30 s (the prop on his right fist); f1 CLANK 0.25 s under the shake and '
                       'the green flicker; f2 flex 0.45 s, then the cannon-arm set'),
    'greyson_walk_cannon': (gf_cannonset.walk_cannon, 6, False,
                            '6 x 0.10 s looping, as greyson_walk; 0 and 3 are the contacts'),
    'greyson_talk_cannon': (gf_cannonset.talk_cannon, 4, True,
                            'pairs (shut, open) flapped at 0.12 s: 0-1 the smug stance, 2-3 the '
                            'smug show (the cannon flexed)'),
    'greyson_roar': (gf_cannonset.roar, 4, True,
                     'f0 inhale 0.40 s; f1/f2 alternated at 0.06 s under the shake (1.2 s); '
                     'f3 settle held'),
    'greyson_barbell_pull': (gf_cannonset.pull, 3, True,
                             '0.15 / 0.15 / then f2 is the fight idle (greyson_idle f0 takes over)'),
    'greyson_hurl': (gf_hurl.frame, 4, True,
                     'f0 grab 0.30 s; f1 press 0.45 s (Computah held on the fist, drawn BEHIND '
                     'him); f2 heave 0.15 s (Computah launched on its first tick); f3 settle '
                     '0.35 s, then the cannon stance. Drawn throwing to screen-RIGHT, Computah '
                     'starting on his left; flip both for the left rope'),
}
for _n in SHEETS:
    assert not any(_n == p or _n.startswith(p + '.') for p in PROTECTED), _n


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def anchors(px, info):
    """The texels the coder needs, measured off the pixels: the crown (top of the head, at the
    middle of its top row), the soles (centre of each foot's run on row 111) and, when the frame
    reports them, the mouth and the hands."""
    # the crown is the top of his HEAD, so it is looked for only in the head's columns (a raised
    # cannon or fist can stand higher than the head; the tear's lean moves the head right by 5)
    band = [(x, y) for (x, y) in px if CROWN_BAND[0] <= x <= CROWN_BAND[1]]
    top = min(y for (x, y) in band)
    xs = sorted(x for (x, y) in band if y == top)
    out = {'crown': ((xs[0] + xs[-1]) / 2.0, top)}
    runs, run = [], []
    for x in sorted(x for (x, y) in px if y == FEET_ROW):
        if run and x != run[-1] + 1:
            runs.append(run)
            run = []
        run.append(x)
    if run:
        runs.append(run)
    out['soles'] = [((r[0] + r[-1]) / 2.0, FEET_ROW) for r in runs]
    for k in ('crown', 'mouth', 'hand', 'hands', 'muzzle', 'plate'):
        if k in info:
            out[k] = info[k]
    return out


def build(name):
    """-> (strip, rows, problems) for one sheet."""
    fn, n, centred, _ = SHEETS[name]
    frames, rows, problems = [], [], []
    pal_rgba = set(K.PAL.values())
    for i in range(n):
        cv, info = fn(i)
        px = cv.px
        im = B.image(px)
        tag = '%s f%d %s' % (name, i, info.get('name', ''))
        st = K.stats(im)
        cols = {c for c in K.flat(im) if c[3]}
        if cols - pal_rgba:
            problems.append('%s: colours off the palette: %s' % (tag, sorted(cols - pal_rgba)[:4]))
        if any(c[:3] == (0, 0, 0) and c != (0, 0, 0, 255) for c in cols):
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: %d semi-transparent pixels' % (tag, st['semi']))
        a = B.audit(px, info.get('fx', ()))
        if any(a.values()):
            problems.append('%s: audit %s' % (tag, {k: v[:4] for k, v in a.items() if v}))
        x0, y0, x1, y1 = K.bbox(px)
        if y1 != FEET_ROW:
            problems.append('%s: lowest drawn row %d, not %d' % (tag, y1, FEET_ROW))
        if x0 < 1 or x1 > FW - 2 or y0 < 1:
            problems.append('%s: drawn on the frame edge (cols %d..%d, top row %d)' % (tag, x0, x1, y0))
        if centred:
            feet = [x for (x, y) in px if y == FEET_ROW]
            mid = (min(feet) + max(feet)) / 2.0 if feet else None
            if mid is None or abs(mid - 56) > 1.0:
                problems.append('%s: the feet are not centred on column 56 (%s)' % (tag, mid))
        if not BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]:
            problems.append('%s: black %.1f%% outside %.0f-%.0f%%' % (
                tag, 100 * st['black'], 100 * BLACK_RANGE[0], 100 * BLACK_RANGE[1]))
        frames.append(im)
        rows.append((tag, st, len(cols), (x0, y0, x1, y1), anchors(px, info)))
    strip = Image.new('RGBA', (FW * len(frames), FH), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (FW * i, 0))
    return strip, rows, problems


def _aseprite(src, dst):
    subprocess.run([ASEPRITE, '-b', src, '--save-as', dst], check=True, capture_output=True)


def write(name, strip, out_dir, replace):
    png = os.path.join(out_dir, name + '.png')
    ase = os.path.join(out_dir, name + '.aseprite')
    for p in (png, ase):
        if os.path.exists(p) and not replace:
            raise SystemExit('%s exists; pass --replace to overwrite it' % p)
    tmp = tempfile.mkdtemp(prefix='greyson_ship_')
    try:
        t_png = os.path.join(tmp, name + '.png')
        t_ase = os.path.join(tmp, name + '.aseprite')
        strip.save(t_png)
        _aseprite(t_png, t_ase)
        back = os.path.join(tmp, 'roundtrip.png')
        _aseprite(t_ase, back)
        d = pixel_diff(Image.open(t_png), Image.open(back))
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
        d = pixel_diff(strip, Image.open(t_png))
        if d:
            raise SystemExit('%s: the PNG on disk differs from the build: %s' % (name, d))
        os.makedirs(out_dir, exist_ok=True)
        os.replace(t_png, png)
        os.replace(t_ase, ase)
        back2 = os.path.join(tmp, 'roundtrip_landed.png')
        _aseprite(ase, back2)
        landed = pixel_diff(Image.open(png), Image.open(back2)) or pixel_diff(strip, Image.open(png))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return png, ase, landed


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    replace = '--replace' in argv
    only = None
    args = []
    it = iter(argv)
    for a in it:
        if a == '--replace':
            continue
        if a == '--only':
            only = next(it, None)
            if only not in SHEETS:
                raise SystemExit('--only needs one of %s' % ', '.join(SHEETS))
            continue
        args.append(a)
    if args == ['--ship']:
        out_dir = SHIP_DIR
        if not os.path.isdir(out_dir):
            raise SystemExit('%s is missing; refusing to create a character folder' % out_dir)
    elif len(args) == 1 and not args[0].startswith('--'):
        out_dir = os.path.realpath(args[0])
        if _under(out_dir, ASSETS):
            raise SystemExit('refusing %s: it is under Assets. Only --ship writes there.' % out_dir)
    else:
        print(__doc__)
        return 2
    names = [only] if only else list(SHEETS)
    built, problems = [], []
    for name in names:
        strip, rows, probs = build(name)
        built.append((name, strip, rows))
        problems += probs
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    status = 0
    for name, strip, rows in built:
        png, ase, landed = write(name, strip, out_dir, replace)
        sheet = K.stats(strip)
        print('%s  %dx%d, %d frames of %dx%d, feet on row %d; %s' % (
            os.path.basename(png), strip.width, strip.height, len(rows), FW, FH, FEET_ROW,
            SHEETS[name][3]))
        for tag, st, ncol, bb, anc in rows:
            print('   %-28s colours %2d  black %.1f%%  rows %d..%d  cols %d..%d' % (
                tag, ncol, 100 * st['black'], bb[1], bb[3], bb[0], bb[2]))
            print('      anchors %s' % anc)
        print('   sheet: colours %d, black %.1f%%, semi-alpha %d' % (
            sheet['colours'], 100 * sheet['black'], sheet['semi']))
        print('   .aseprite round trip:', landed or 'identical')
        status |= 1 if landed else 0
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
