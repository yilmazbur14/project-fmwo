"""Approval-pass outputs for Jordan SKINNIER in the tighter tee. Writes ONLY into this folder
(art_source/jordan_fit/skinny/); any other output path, and anything that resolves under Assets/, is
refused.

    python jsk_previews.py            # print this and exit
    python jsk_previews.py --write    # build every frame (jsk_frames.py, one process per rig), then
                                      # write the files below

  jordan_skinny_compare_3x.png   current fitted | skinny at GAME SCALE (3x, as the Sprite2D and the
                                 finale's StoryActors draw him): idle f0, summon f2 (the fist-pump),
                                 rage f0 (standing finale) and the seated friendly frame (seated f6)
  jordan_skinny_compare_6x.png   the same four pairs at 6x
  jordan_skinny_print_8x.png     the Peach print: fitted | skinny at 8x, the two cropped outline
                                 columns marked, and the print map with them struck through
  jordan_skinny_alt_whole_print.png   idle f0 at 3x and 6x: fitted | the whole-print alternative (17px
                                 chest) | the proposal (15px chest, print outline cropped)
  jordan_skinny_ingame_crop.png  current | skinny cropped round him from the two in-game captures, 1:1
                                 and 2x (needs jsk_capture.gd's two 1920x1080 PNGs; skipped without)
  jordan_skinny_idle_f0.png      the skinny art itself, 1x, each with its .aseprite beside it
  jordan_skinny_summon_f2.png      (round-tripped through Aseprite's CLI and compared pixel for pixel)
  jordan_skinny_rage_f0.png
  jordan_skinny_seated_f6.png    (128x128, the seated sheet's frame)
  jordan_skinny_idle_strip.png   all four skinny idle frames (384x96), which the in-game capture swaps in

The 1920x1080 in-game mock is jsk_capture.gd's (run through Godot; see its header).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(ART)
sys.path.insert(0, ART)
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
BG = (46, 49, 58, 255)
DARK = (14, 14, 18, 255)
INK = (225, 225, 232, 255)
DIM = (150, 152, 165, 255)
MARK = (255, 92, 92, 255)


def _font(size, bold=False):
    for name in (('segoeuib.ttf' if bold else 'segoeui.ttf'), 'arial.ttf'):
        try:
            return ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', name), size)
        except OSError:
            continue
    return ImageFont.load_default()


F_HEAD, F_CAP, F_SUB = _font(18, True), _font(15, True), _font(13)


def _under(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


def _guard(path):
    if _under(path, os.path.join(ROOT, 'Assets')) or not _under(path, HERE):
        raise SystemExit('refusing %s: outputs stay in art_source/jordan_fit/skinny/' % path)
    return path


#LAYOUT HELPERS (jordan_fit/jfit_previews.py's)

def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def tile(im, s, caption, sub='', min_w=0):
    big = up(im, s)
    pad = 44 if sub else 26
    w = max(big.width, min_w)
    out = Image.new('RGBA', (w, big.height + pad), DARK)
    out.paste(big, ((w - big.width) // 2, pad))
    d = ImageDraw.Draw(out)
    d.text((4, 3), caption, fill=INK, font=F_CAP)
    if sub:
        d.text((4, 23), sub, fill=DIM, font=F_SUB)
    return out


def hstack(ims, gap, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def vstack(ims, gap, bg=DARK):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new('RGBA', (w, h), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def framed(im, title, pad=16, note=''):
    top = 28 + (20 if note else 0)
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad + top), DARK)
    d = ImageDraw.Draw(out)
    d.text((pad, 8), title, fill=INK, font=F_HEAD)
    if note:
        d.text((pad, 32), note, fill=DIM, font=F_SUB)
    out.paste(im, (pad, pad + top))
    return out


def _pct(n):
    return 'black %.1f%%, %d colours' % (100 * n['black'], n['colours'])


#BUILDING THE FRAMES

def build_frames(tmp):
    """Run jsk_frames.py once per rig (and once more for the whole-print alternative) into `tmp`;
    returns ({name: image}, {name: numbers}, [other JSON lines])."""
    ims, nums, notes = {}, {}, []
    runs = [('fight', {}, 'p'), ('rage', {}, 'p'), ('seated', {}, 'p'), ('fight', {'JSK_VARIANT': 'whole'}, 'alt')]
    for fam, env, tag in runs:
        folder = os.path.join(tmp, tag + '_' + fam)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'jsk_frames.py'), fam, folder], capture_output=True,
                           text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', **env))
        if r.returncode:
            raise SystemExit('jsk_frames.py %s failed:\n%s%s' % (fam, r.stdout, r.stderr))
        for ln in r.stdout.splitlines():
            if not ln.startswith('{'):
                continue
            rec = json.loads(ln)
            if 'frame' in rec:
                nums[(tag, rec['frame'])] = rec
            else:
                notes.append((tag, fam, rec))
        for fn in os.listdir(folder):
            if fn.endswith('.png'):
                ims[(tag, fn[:-4])] = Image.open(os.path.join(folder, fn)).convert('RGBA')
    return ims, nums, notes


SHOTS = [('idle f0', 'idle_f0', 'jordan_idle.png f0'),
         ('summon f2 (the fist-pump)', 'summon_f2', 'jordan_summon.png f2'),
         ('rage f0 (standing finale)', 'rage_f0', 'jordan_rage.png f0'),
         ('seated f6 (friendly, shut)', 'seated_f6', 'Room/jordan_seated.png f6')]


def compare(ims, nums, s, title, rows):
    pairs = []
    for label, key, live in SHOTS:
        b, a = ims[('p', 'before_' + key)], ims[('p', 'after_' + key)]
        nb, na = nums[('p', 'before_' + key)], nums[('p', 'after_' + key)]
        tb = tile(b, s, 'CURRENT  ' + label, 'live, fitted: %s' % _pct(nb), min_w=300)
        ta = tile(a, s, 'SKINNIER  ' + label, 'proposal: %s' % _pct(na), min_w=300)
        pairs.append(hstack([tb, ta], 6))
    body = vstack([hstack(pairs[i:i + rows], 30) for i in range(0, len(pairs), rows)], 24)
    return framed(body, title, note='Left of each pair: Jordan as shipped (the fitted tee). Right: skinnier, the '
                                    'tighter tee. Same frame size, anchor and soles; every hand, crown and prop '
                                    'point unchanged.')


def print_closeup(ims):
    """The chest at 8x, fitted | skinny, the cropped outline columns marked; and the print map itself
    with the two columns struck through."""
    crop = (34, 40, 64, 66)                  # frame x 34-63: the chest, both sides of the print
    s = 8
    b = up(ims[('p', 'before_idle_f0')].crop(crop), s)
    a = up(ims[('p', 'after_idle_f0')].crop(crop), s)
    for im, cols in ((b, (41, 55)), (a, (41, 55))):  # the print's outline columns, frame x (build 42, 56)
        d = ImageDraw.Draw(im)
        for fx in cols:
            x0 = (fx - crop[0]) * s
            d.rectangle([x0, 0, x0 + s - 1, 5], fill=MARK)
            d.rectangle([x0, im.height - 6, x0 + s - 1, im.height - 1], fill=MARK)
    tb = tile(b, 1, 'CURRENT  the chest, 8x', 'print outline + 2px of red a side')
    ta = tile(a, 1, 'SKINNIER  the chest, 8x', 'outline columns (ticks) cropped')
    # the print map, before and after, as swatches
    sys.path.insert(0, os.path.join(ART, 'jordan_v2'))
    import jv2_base as V2B   # noqa: E402  (read-only: the palette and the approved rig's print)
    rows = V2B.rows_of(V2B.rig_torso.PRINT)
    pal = V2B.PAL

    def swatch(cropped):
        im = Image.new('RGBA', (15, len(rows)), (0, 0, 0, 0))
        for y, r in enumerate(rows):
            for x, k in enumerate(r):
                if k == '.' or (cropped and x in (0, 14)):
                    continue
                im.putpixel((x, y), pal[k])
        big = up(im, 12)
        if cropped:
            d = ImageDraw.Draw(big)
            for x in (0, 14):
                d.line([(x * 12, 0), (x * 12 + 11, big.height - 1)], fill=MARK, width=2)
                d.line([(x * 12 + 11, 0), (x * 12, big.height - 1)], fill=MARK, width=2)
        return big
    sa = tile(swatch(False), 1, 'the approved print', 'as it is, 12x')
    sb = tile(swatch(True), 1, 'on the skinny tee', 'side outline columns left off')
    return framed(hstack([tb, ta, sa, sb], 14), 'THE PEACH PRINT on the 15px chest',
                  note='Only its two side outline columns go (they would double the keyline). Face, crown, '
                       'hair and dress stay.')


def alt_panel(ims, nums):
    tiles = []
    for s in (3, 6):
        row = []
        for tag, key, cap, sub in (('p', 'before_idle_f0', 'CURRENT (fitted)', 'chest 19px, waist 19px'),
                                   ('alt', 'after_idle_f0', 'ALTERNATIVE: print whole', 'chest 17px, waist 15px'),
                                   ('p', 'after_idle_f0', 'PROPOSAL: print outline cropped', 'chest 15px, waist 13px')):
            n = nums[(tag, key)]
            row.append(tile(ims[(tag, key)], s, '%s  %dx' % (cap, s), '%s; %s' % (sub, _pct(n)), min_w=300))
        tiles.append(hstack(row, 10))
    return framed(vstack(tiles, 20), 'IF THE PRINT MUST STAY WHOLE: the chest can only come in to 17px',
                  note='Same arms, legs, sleeves and waist taper in both; only the chest width and the print\'s '
                       'side outline differ.')


def ingame_crop():
    paths = [os.path.join(HERE, n + '.png') for n in ('jordan_skinny_ingame_before_1920x1080',
                                                      'jordan_skinny_ingame_1920x1080')]
    if not all(os.path.exists(p) for p in paths):
        print('no in-game captures yet (run jsk_capture.gd), skipping the crop')
        return None
    box = (770, 196, 1150, 530)
    shots = [Image.open(p).convert('RGBA').crop(box) for p in paths]
    one = framed(hstack([tile(shots[0], 1, 'CURRENT  in the fight, 1:1 screen pixels', 'live jordan_idle.png f0 (fitted)'),
                         tile(shots[1], 1, 'SKINNIER  same frame', 'jordan_skinny_idle_strip.png f0 swapped in at runtime')], 8),
                 'IN GAME at play size (crops of the two 1920x1080 captures)')
    two = framed(hstack([tile(im, 2, c) for im, c in zip(shots, ('CURRENT, 2x', 'SKINNIER, 2x'))], 8),
                 'The same crops at 2x')
    return vstack([one, two], 10)


def write_art(name, im):
    """PNG + .aseprite (Aseprite CLI), built in a temp folder and moved into place, the .aseprite
    re-exported and compared with the PNG pixel for pixel where they landed."""
    png = _guard(os.path.join(HERE, name + '.png'))
    ase = _guard(os.path.join(HERE, name + '.aseprite'))
    tmp = tempfile.mkdtemp(prefix='jsk_')
    tpng, tase = os.path.join(tmp, name + '.png'), os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    subprocess.run([ASEPRITE, '-b', tpng, '--save-as', tase], check=True, capture_output=True)
    shutil.move(tpng, png)
    shutil.move(tase, ase)
    back = os.path.join(tmp, 'rt.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    shutil.rmtree(tmp, ignore_errors=True)
    return d


def main(argv):
    if argv[:1] != ['--write']:
        print(__doc__)
        return 2
    tmp = tempfile.mkdtemp(prefix='jsk_frames_')
    try:
        ims, nums, notes = build_frames(tmp)
    finally:
        pass
    for tag, fam, rec in notes:
        print('%s %s: %s' % (tag, fam, rec))
    bad = [k for k, n in nums.items() if n['gaps'] or n['lone'] or n['holes'] or n['keys'] or n['semi']]
    if bad:
        raise SystemExit('audit failures: %s' % bad)
    c3 = compare(ims, nums, 3, 'GAME SCALE: 3x, as his Sprite2D (the fight) and the StoryActors (the finale) draw him', 4)
    c3.save(_guard(os.path.join(HERE, 'jordan_skinny_compare_3x.png')))
    c6 = compare(ims, nums, 6, 'CLOSE-UP at 6x', 2)
    c6.save(_guard(os.path.join(HERE, 'jordan_skinny_compare_6x.png')))
    pc = print_closeup(ims)
    pc.save(_guard(os.path.join(HERE, 'jordan_skinny_print_8x.png')))
    ap = alt_panel(ims, nums)
    ap.save(_guard(os.path.join(HERE, 'jordan_skinny_alt_whole_print.png')))
    print('wrote compare_3x %s, compare_6x %s, print_8x %s, alt_whole_print %s' % (c3.size, c6.size, pc.size, ap.size))
    ic = ingame_crop()
    if ic is not None:
        ic.save(_guard(os.path.join(HERE, 'jordan_skinny_ingame_crop.png')))
        print('wrote jordan_skinny_ingame_crop.png', ic.size)
    for name, key in (('jordan_skinny_idle_f0', 'after_idle_f0'), ('jordan_skinny_summon_f2', 'after_summon_f2'),
                      ('jordan_skinny_rage_f0', 'after_rage_f0'), ('jordan_skinny_seated_f6', 'after_seated_f6'),
                      ('jordan_skinny_idle_strip', 'after_idle_strip')):
        d = write_art(name, ims[('p', key)])
        print('wrote %s.png %s + .aseprite, round trip: %s' % (name, ims[('p', key)].size, d or 'identical'))
    for (tag, frame), n in sorted(nums.items()):
        print('%-4s %-22s opaque %4d  black %5.2f%%  colours %2d  gaps %d lone %d holes %d'
              % (tag, frame, n['opaque'], 100 * n['black'], n['colours'], n['gaps'], n['lone'], n['holes']))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
