"""Build Carter's back-view and turn sheets on the polished body, and check them.

    python build_turns.py            # render, lint, measure, previews -> scratchpad only
    python build_turns.py --ship     # ... and write the three sheets to Assets/Characters/Carter,
                                     # each PNG whole (temp file + os.replace), its .aseprite beside it,
                                     # and a round trip through Aseprite checked with imgdiff.pixel_diff

Sheets (overwritten in place, same name, size, frame count and order - CarterArtLayout reads them):
    carter_intro.png      17 x 96x96     carter_look_back.png   6 x 96x96
    carter_victory.png     7 x 96x96

Checks (the build fails on any):
  * size and frame count; binary alpha; every colour in the polish palette; soles on row 95 wherever
    he is standing
  * the 天: in every frame the shipped sheet showed it, the mark's own pixels (placed as that frame
    placed them - squeezed on the turns) are identical, colour for colour, to the shipped frame
  * the hand-off: intro frame 16 is pixel-identical to carter_idle.png frame 0 (and frame0.build()),
    intro frame 14 to carter_akuma.png frame 1 (and frame1.build())
  * the back view is carter_akuma.png frame 2's (backview.check)
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import rig                                                                    # noqa: E402
from rig import L, fx, K, sq                                                  # noqa: E402
from PIL import Image, ImageDraw                                              # noqa: E402
from imgdiff import pixel_diff                                                # noqa: E402
import frames                                                                 # noqa: E402
import front                                                                  # noqa: E402
import backview                                                               # noqa: E402

ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
SCRATCH = os.environ.get('CARTER_TURNS_PREVIEWS', os.path.join(
    os.environ.get('TEMP', tempfile.gettempdir()), 'claude',
    'C--Users-theyi-OneDrive-Documents-new-game-project', 'a7fc2846-afef-472d-979b-e17143793a0f',
    'scratchpad', 'carter_polish', 'turns'))
F = 96
BG = (30, 32, 40, 255)
# the sheets as they shipped before this pass (copied here before the first --ship), for the mark
# check and the before/after; if absent, the live sheets are the reference
REF_DIR = os.path.join(SCRATCH, 'shipped_before')


def reference(name):
    p = os.path.join(REF_DIR, name + '.png')
    return Image.open(p if os.path.exists(p) else os.path.join(rig.ASSETS, name + '.png')).convert('RGBA')

# CarterArtLayout's timings, for the GIFs (seconds)
TIMES = {
    'carter_intro': [0.10, 0.10, 0.10, 0.12, 0.14, 0.09, 0.07, 0.07, 0.16, 0.11, 0.11, 0.11, 0.13,
                     0.20, 0.30, 0.14, 0.60],
}
PLAY = {
    'carter_intro': [(i, TIMES['carter_intro'][i]) for i in range(17)],
    'carter_look_back': [(0, 0.60), (1, 0.12), (2, 0.11), (3, 0.10)] + [(i, 0.2) for i in (4, 5, 3, 4, 5, 3)],
    'carter_victory': [(0, 0.09), (1, 0.07), (2, 0.07), (3, 0.14)] +
                      [(i, t) for i, t in ((4, 0.11), (5, 0.13), (6, 0.13))] * 3,
}

# frames of the shipped sheets that show the 天, and how each placed it
#   ('flat',)                       the mark where it is on the back
#   ('sq', s, keep_head, dx)        squeezed with the body by hsq_canvas
#   ('mat', k)                      the materialise squeeze of stage k


def mark_frames():
    s40 = sq(40.0)
    out = {'carter_intro': {}, 'carter_look_back': {}, 'carter_victory': {}}
    for k in (1, 2, 3):
        out['carter_intro'][k] = ('mat', k)
    for i in (4, 5, 6, 7, 8):
        out['carter_intro'][i] = ('flat',)
    out['carter_intro'][9] = ('sq', s40, True, int(round(4.0 * (1.0 - s40))))
    out['carter_intro'][10] = ('sq', 0.45, True, 0)
    for i in range(6):
        out['carter_look_back'][i] = ('flat',)
    out['carter_victory'][2] = ('sq', 0.45, True, 0)
    for i in (3, 4, 5, 6):
        out['carter_victory'][i] = ('flat',)
    return out


def mark_zone(how):
    """The pixels the mark lands on in a frame: a probe - the back view in one colour with the mark in
    another - sent through the same transform, and whatever comes out in the mark's colour."""
    if how[0] == 'flat':
        return set(rig.MARK)
    probe = {q: 'c' for q in backview.body().px}
    for q in rig.MARK:
        probe[q] = 'M'
    if how[0] == 'mat':
        st = K.mat[how[1]]
        out = fx.squeeze(probe, st['sq'], keep_head=False, reoutline=False)
    else:
        _, s, keep, dx = how
        out = fx.squeeze(probe, s, keep_head=keep, dx=dx, reoutline=False)
    return {q for q, k in out.items() if k == 'M'}


# ------------------------------------------------------------------ build

def build():
    sheets = {}
    for name, (fn, n) in frames.SHEETS.items():
        ims = []
        for i in range(n):
            ims.append(rig.image(fn(i)))
        strip = Image.new('RGBA', (F * n, F), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            strip.alpha_composite(im, (i * F, 0))
        sheets[name] = strip
    return sheets


# ------------------------------------------------------------------ checks

STANDING = {
    'carter_intro': [i for i in range(17) if i not in (0, 1)],
    'carter_look_back': list(range(6)),
    'carter_victory': list(range(7)),
}


def frame_of(im, i):
    return im.crop((i * F, 0, i * F + F, F))


def lint(name, im, n):
    errs = []
    if im.size != (F * n, F):
        errs.append('%s: size %s, want %s' % (name, im.size, (F * n, F)))
    st = L.stats(im)
    if st['alphas'] not in ([0, 255], [255]):
        errs.append('%s: non-binary alpha %s' % (name, st['alphas']))
    pal = {v[:3] for v in L.PAL.values()}
    stray = {c[:3] for c in L.flat(im) if c[3] and c[:3] not in pal}
    if stray:
        errs.append('%s: %d colours outside the polish palette' % (name, len(stray)))
    for i in STANDING[name]:
        fr = frame_of(im, i)
        rows = [y for y in range(F) for x in range(F) if fr.getpixel((x, y))[3]]
        if not rows or max(rows) != 95:
            errs.append('%s f%d: lowest opaque row %s, not 95' % (name, i, max(rows) if rows else None))
        for x0, x1 in ((24, 44), (52, 72)):
            if not any(fr.getpixel((x, 95))[:3] == (0, 0, 0) for x in range(x0, x1)) and \
                    not any(fr.getpixel((x, 95))[3] for x in range(x0, x1)):
                errs.append('%s f%d: nothing on row 95 in x %d..%d (a foot is off the floor)'
                            % (name, i, x0, x1))
    return errs


def mark_check(name, new):
    """Every mark pixel identical to the shipped frame's. Returns (errors, per-frame lines)."""
    old = reference(name)
    errs, lines = [], []
    for i, how in sorted(mark_frames()[name].items()):
        zone = mark_zone(how)
        a, b = frame_of(old, i), frame_of(new, i)
        bad = [q for q in zone if a.getpixel(q) != b.getpixel(q)]
        lines.append('   f%-2d %-24s %3d px   differing: %d' % (i, ' '.join(str(round(v, 3)) if isinstance(v, float) else str(v) for v in how), len(zone), len(bad)))
        if bad:
            errs.append('%s f%d: %d of the 天\'s %d px differ from the shipped frame (first %s)'
                        % (name, i, len(bad), len(zone), sorted(bad)[:3]))
    return errs, lines


def handoff_check(sheets):
    errs = []
    intro = sheets['carter_intro']
    idle = Image.open(os.path.join(rig.ASSETS, 'carter_idle.png')).convert('RGBA')
    akuma = Image.open(os.path.join(rig.ASSETS, 'carter_akuma.png')).convert('RGBA')
    for what, a, b in (('intro f16 vs carter_idle f0', frame_of(intro, 16), frame_of(idle, 0)),
                       ('intro f16 vs frame0.build()', frame_of(intro, 16), frame0_img()),
                       ('intro f14 vs carter_akuma f1', frame_of(intro, 14), frame_of(akuma, 1)),
                       ('intro f14 vs frame1.build()', frame_of(intro, 14), frame1_img())):
        d = pixel_diff(a, b)
        print('  %-30s %s' % (what, d or 'pixel-identical'))
        if d:
            errs.append(what + ': ' + d)
    return errs


def frame0_img():
    import frame0
    return frame0.build().image()


def frame1_img():
    import frame1
    return frame1.build().image()


def numbers(label, im):
    st = L.stats(im)
    print('  %-30s opaque %6d   colours %3d   pure black %5.1f%%' % (label, st['opaque'], st['colours'],
                                                                  100 * st['black']))
    return st


# ------------------------------------------------------------------ previews

def label(im, text, x, y, fill=(235, 235, 240, 255)):
    ImageDraw.Draw(im).text((x, y), text, fill=fill)


def on_bg(fr, bg=BG):
    out = Image.new('RGBA', fr.size, bg)
    out.alpha_composite(fr)
    return out


def contact(sheets, path, s=4):
    rows = []
    for name, (fn, n) in frames.SHEETS.items():
        rows.append((name, sheets[name], n))
    per = 9
    tiles = sum((n + per - 1) // per for _, _, n in rows)
    W = per * (F * s + 8) + 8
    H = tiles * (F * s + 24) + 8
    out = Image.new('RGBA', (W, H), BG)
    y = 8
    for name, im, n in rows:
        for j in range(n):
            if j and j % per == 0:
                y += F * s + 24
            x = 8 + (j % per) * (F * s + 8)
            fr = frame_of(im, j).resize((F * s, F * s), Image.NEAREST)
            tile = on_bg(fr, (46, 49, 58, 255))
            out.alpha_composite(tile, (x, y + 16))
            label(out, '%s  f%d' % (name.replace('carter_', ''), j), x, y + 2)
        y += F * s + 24
    out.save(path)


def gif(name, im, path, s=3):
    fr, durs = [], []
    for i, t in PLAY[name]:
        f = on_bg(frame_of(im, i).resize((F * s, F * s), Image.NEAREST), (46, 49, 58, 255))
        fr.append(f.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255))
        durs.append(int(round(t * 1000)))
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=durs, loop=0, disposal=1)


def before_after(sheets, path, s=6):
    pairs = [('carter_victory', 4, 'victory f4 - full burn (the bell)'),
             ('carter_look_back', 4, 'look_back f4 - the hold')]
    W = 2 * (F * s + 16) + 16
    H = len(pairs) * (F * s + 40) + 8
    out = Image.new('RGBA', (W, H), BG)
    y = 8
    for name, i, text in pairs:
        old = reference(name)
        for col, (im, tag) in enumerate(((old, 'BEFORE'), (sheets[name], 'AFTER'))):
            x = 16 + col * (F * s + 16)
            out.alpha_composite(on_bg(frame_of(im, i).resize((F * s, F * s), Image.NEAREST), (46, 49, 58, 255)), (x, y + 20))
            label(out, '%s  %s' % (tag, text), x, y + 4)
        y += F * s + 40
    out.save(path)


# ------------------------------------------------------------------ ship

def ship(name, im):
    png = os.path.join(rig.ASSETS, name + '.png')
    ase = os.path.join(rig.ASSETS, name + '.aseprite')
    part = png + '.part'
    im.save(part, format='PNG')
    os.replace(part, png)
    tmpd = tempfile.mkdtemp()
    tmp_ase = os.path.join(tmpd, name + '.aseprite')
    subprocess.run([ASEPRITE, '-b', png, '--save-as', tmp_ase], check=True, capture_output=True)
    os.replace(tmp_ase, ase) if os.path.splitdrive(tmp_ase)[0] == os.path.splitdrive(ase)[0] else shutil.move(tmp_ase, ase)
    back = os.path.join(tmpd, 'roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True, capture_output=True)
    d = pixel_diff(Image.open(png), Image.open(back))
    print('  wrote %s %s, %s; round trip: %s' % (png, im.size, os.path.basename(ase), d or 'identical'))
    return d


def main():
    errs = []
    chk = backview.check()
    if chk:
        errs += chk
    chk = front.check()
    if chk:
        errs += chk
    sheets = build()
    print('numbers (polish approval sheet first):')
    numbers('carter_polish.png', Image.open(os.path.join(rig.ASSETS, 'carter_polish.png')).convert('RGBA'))
    for name, (fn, n) in frames.SHEETS.items():
        im = sheets[name]
        errs += lint(name, im, n)
        numbers(name + '.png', im)
        for i in range(n):
            numbers('   f%d' % i, frame_of(im, i))
    print('the 天 against the shipped frames:')
    for name in frames.SHEETS:
        e, lines = mark_check(name, sheets[name])
        print(' ', name)
        print('\n'.join(lines))
        errs += e
    print('hand-offs:')
    errs += handoff_check(sheets)
    os.makedirs(SCRATCH, exist_ok=True)
    for name, im in sheets.items():
        im.save(os.path.join(SCRATCH, name + '.png'))
        gif(name, im, os.path.join(SCRATCH, name + '_3x.gif'))
    contact(sheets, os.path.join(SCRATCH, 'contact_4x.png'))
    before_after(sheets, os.path.join(SCRATCH, 'before_after_6x.png'))
    print('previews in', SCRATCH)
    for e in errs:
        print('ERROR:', e)
    if errs:
        return 1
    if '--ship' in sys.argv:
        bad = [n for n, im in sheets.items() if ship(n, im)]
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
