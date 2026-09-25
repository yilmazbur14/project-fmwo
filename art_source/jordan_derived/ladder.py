"""Jordan's slot on the Victory screen's rank ladder, re-framed on the approved 2026-09-23 redesign and
spliced into Assets/UI/Screens/rank_icons.png - his frame ONLY (frame 9 of 11).

THE CELL comes from art_source/victory_screen/icons.py, which this script edits in three places:
  - REMAP['jordan'] extended by hand with every colour of the redesign inside his window, so nothing
    falls back to nearest() - which would put his second-darkest hair tone on NAVY and the quiff's
    greasy sheen on KHAKI green, and the olive skin's base tone on TAN, where it would swallow the
    shadows that make his tired eyes
  - a jordan_cell() beside carter_cell(): frame 0 of jordan_redesign.png at (49, 24), the collector
    box cleared from the disc's edge
  - build() calling it
The old REMAP['jordan'] entries stay, as the other characters' do.

THE RACE: Carter's artist splices his frame into the same strip. So at --ship the live PNG and
.aseprite are re-read immediately before writing, and must still agree with each other and with
what the build was proved against; only frame 9 is replaced in that fresh copy, and every other frame
is proved byte-identical to what was just read (raw RGBA bytes and a sha256 per frame), before and
after the write. The .aseprite has only frame 10's cel swapped (frame_splice.lua), and
victory_screen/rtcheck.py must report 0 differing pixels between it and the PNG.

    python ladder.py            # edit a scratch copy of icons.py, build, prove: nothing in the project written
    python ladder.py --ship     # ...then write icons.py, rank_icons.png and rank_icons.aseprite, one write each
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
VSD = os.path.join(ROOT, 'art_source', 'victory_screen')
ICONS_PY = os.path.join(VSD, 'icons.py')
SCREENS = os.path.join(ROOT, 'Assets', 'UI', 'Screens')
PNG = os.path.join(SCREENS, 'rank_icons.png')
ASE = os.path.join(SCREENS, 'rank_icons.aseprite')
PREVIEWS = os.environ.get(
    'JORDAN_DERIVED_PREVIEWS',
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\jordan_derived')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

sys.dont_write_bytecode = True
sys.path.insert(0, VSD)
import pngio                                                     # noqa: E402
import cv                                                        # noqa: E402


def _refuse(*a, **k):
    raise RuntimeError('ladder.py never lets the victory-screen pipeline write')


pngio.write_png = _refuse
cv.write_png = _refuse
import slots                                                     # noqa: E402
sys.path.insert(0, os.path.join(ROOT, 'art_source'))
from imgdiff import pixel_diff                                   # noqa: E402
from PIL import Image                                            # noqa: E402

S = 40
NL = '\r\n'                                                      # icons.py is CRLF throughout

REMAP_OLD = (
    "    'jordan': dict(SKIN_MAP, **{'7a2626': BROWN, 'b05e97': PURPLE, 'e49acd': ROSE, '8a4574': PURPLE," + NL +
    "                                'ae8358': RUST, '90765e': BROWN, 'f2c0df': PALE})," + NL)
REMAP_NEW = (
    "    # The approved 2026-09-23 redesign (art_source/jordan_redesign kit.PAL), every colour inside his" + NL +
    "    # window by hand. His light olive skin goes the way the other light skins do - the lit and base" + NL +
    "    # tones on SKIN, then TAN, RUST, BROWN - not nearest()'s TAN for the base, which would swallow the" + NL +
    "    # TAN shadows that make his tired eyes; the dark brown hair on K, PLUM, BROWN, RUST like Josh's, its" + NL +
    "    # second-darkest tone on PLUM rather than nearest()'s NAVY and the quiff's greasy sheen on TAN" + NL +
    "    # rather than nearest()'s KHAKI green; the lip PINK so it reads in the beard. The box's red header" + NL +
    "    # (cleared from the cell by jordan_cell) and the shirt's darks and collar trim below the chin go" + NL +
    "    # the way Josh's crimson does, for any re-frame." + NL +
    "    'jordan': dict(SKIN_MAP, **{'7a2626': BROWN, 'b05e97': PURPLE, 'e49acd': ROSE, '8a4574': PURPLE," + NL +
    "                                'ae8358': RUST, '90765e': BROWN, 'f2c0df': PALE," + NL +
    "                                'eccda5': SKIN, 'd5ad85': SKIN, 'b58a63': TAN, '876046': RUST," + NL +
    "                                '573a2b': BROWN, 'a8604f': PINK, '1a110d': K, '2b1c15': PLUM," + NL +
    "                                '432d21': PLUM, '5f412e': BROWN, '7f5b3e': RUST, 'a27b57': TAN," + NL +
    "                                'f3eee4': WHITE, 'c9293f': RED, 'ec5a5b': PINK, '8c1b2d': RED," + NL +
    "                                '4c0d1a': PLUM, '2c2f39': NAVY})," + NL)
BUILD_OLD = (
    "    ic['jordan'] = crop_icon('jordan', CHAR + \"Jordan/jordan.png\", 33, 17)" + NL +
    "    bg_disc(ic['jordan'], GREEN, TEAL)" + NL)
BUILD_NEW = "    ic['jordan'] = jordan_cell()" + NL
ANCHOR = NL + NL + 'def build():' + NL
JORDAN_CELL = NL.join([
    'def jordan_cell():',
    '    """Jordan\'s slot, cut from the approved 2026-09-23 redesign (jordan_redesign.png frame 0, the',
    '    idle). (49, 24) puts the window\'s centre on x48.5, between the back of his head and the tip of his',
    '    nose, and its top and bottom on the tip of the quiff (y9) and his chin (y38): the whole head, with',
    '    the heavy brows, the tired eyes and the lip in the patchy beard. The gold collector box he holds',
    '    up beside his face starts at x60, inside the disc\'s right edge, where a sliver of it read as a',
    '    stray dark stripe, so the crop stops at x59 and the disc shows through."""',
    '    cx, cy = 49, 24',
    '    cv = crop_icon(\'jordan\', CHAR + "Jordan/jordan_redesign.png", cx, cy)',
    '    for y in range(S):',
    '        for x in range(S):',
    '            if cx + x - 20 >= 60:',
    '                cv.set(x, y, None)',
    '    bg_disc(cv, GREEN, TEAL)',
    '    return cv',
])


def edited(text):
    """icons.py with the three changes, and nothing else. Idempotent: on an icons.py that already
    carries them exactly as written here, it returns the text unchanged, so a re-run proves the
    shipped state instead of refusing."""
    if all(text.count(p) == 1 for p in (REMAP_NEW, BUILD_NEW, JORDAN_CELL + NL + ANCHOR)):
        return text
    for piece in (REMAP_OLD, BUILD_OLD, ANCHOR):
        assert text.count(piece) == 1, 'icons.py is not as this script expects: %r' % piece[:60]
    assert 'def jordan_cell' not in text
    return (text.replace(REMAP_OLD, REMAP_NEW).replace(BUILD_OLD, BUILD_NEW)
            .replace(ANCHOR, NL + NL + JORDAN_CELL + NL + ANCHOR))


def load_icons(path, name):
    """Import an icons.py from `path` as a fresh module; its cv and slots come from victory_screen."""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def image(c):
    im = Image.new('RGBA', (c.w, c.h), (0, 0, 0, 0))
    for y in range(c.h):
        for x in range(c.w):
            h = c.get(x, y)
            if h is not None:
                assert h in cv.DB, h
                im.putpixel((x, y), cv.rgba(h))
    return im


def built(icons):
    """(the jordan cell, the whole strip icons.build() makes, anything crop_icon printed about jordan)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cell = icons.jordan_cell()
        strip = icons.strip(icons.build())
    notes = [ln for ln in out.getvalue().splitlines() if 'jordan' in ln]
    return image(cell), image(strip), notes


def frames(im):
    return [im.crop((i * S, 0, i * S + S, S)) for i in range(im.width // S)]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run_aseprite(args):
    subprocess.run([ASEPRITE, '-b'] + args, check=True, capture_output=True)


def rtcheck(a, b):
    r = subprocess.run([sys.executable, os.path.join(VSD, 'rtcheck.py'), a, b], capture_output=True, text=True,
                       cwd=VSD, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    return r.stdout.strip() or r.stderr.strip()


def sheet_of(ase, out):
    run_aseprite([ase, '--sheet', out, '--sheet-type', 'horizontal'])
    return Image.open(out).convert('RGBA')


def preview(before, after, order, frame):
    """The ladder strip before and after, each icon under the 'cleared' ring, at 6x, Jordan's marked."""
    sl = slots.build()
    ring = image(sl[1])
    rows = []
    for strip in (before, after):
        row = Image.new('RGBA', (strip.width, S), (20, 20, 26, 255))
        for i, f in enumerate(frames(strip)):
            t = Image.new('RGBA', (S, S), (0, 0, 0, 0))
            t.alpha_composite(f)
            t.alpha_composite(ring)
            row.alpha_composite(t, (i * S, 0))
        rows.append(row.resize((row.width * 6, S * 6), Image.NEAREST))
    out = Image.new('RGBA', (rows[0].width, rows[0].height * 2 + 30), (10, 10, 12, 255))
    out.paste(rows[0], (0, 0))
    out.paste(rows[1], (0, rows[0].height + 30))
    from PIL import ImageDraw
    d = ImageDraw.Draw(out)
    x0 = frame * S * 6
    d.rectangle([x0, rows[0].height + 2, x0 + S * 6 - 1, rows[0].height + 27], fill=(240, 200, 80, 255))
    d.text((x0 + 6, rows[0].height + 8), 'frame %d (%s): the only change' % (frame, order[frame]), fill=(0, 0, 0, 255))
    p = os.path.join(PREVIEWS, 'ladder_strip_before_after_6x.png')
    out.save(p)
    return p


def build_and_prove(work, text, live_png_bytes, live_ase):
    """Everything short of writing into the project, against the given live bytes / .aseprite."""
    tmp_icons = os.path.join(work, 'icons_edited.py')
    with open(tmp_icons, 'w', encoding='utf-8', newline='') as f:
        f.write(edited(text))
    icons = load_icons(tmp_icons, 'icons_edited')
    frame = icons.ORDER.index('jordan')
    cell, strip, notes = built(icons)
    print('jordan cell: frame %d of %d, nearest() fallbacks: %s' % (frame, len(icons.ORDER), notes or 'none'))
    assert not notes, notes
    cols = {c[:3] for c in cell.getdata() if c[3]}
    print('  %d colours, all DB32: %s, alpha values %s' % (
        len(cols), not ({'%02x%02x%02x' % c for c in cols} - cv.DB), sorted({c[3] for c in cell.getdata()})))

    live = Image.open(io.BytesIO(live_png_bytes)).convert('RGBA')
    assert live.size == (S * 11, S), live.size
    fl, fb = frames(live), frames(strip)
    other = [i for i in range(11) if i != frame]
    same = [i for i in other if fl[i].tobytes() == fb[i].tobytes()]
    print('edited icons.py build vs the live strip: %d of %d other frames identical %s'
          % (len(same), len(other), '' if len(same) == len(other) else '(differs: %s)' % sorted(set(other) - set(same))))
    assert fb[frame].tobytes() == cell.tobytes()

    new = live.copy()
    new.paste(cell, (frame * S, 0))                              # replaces all 1600 px of his frame
    fn = frames(new)
    bad = 0
    for i in range(11):
        eq = fl[i].tobytes() == fn[i].tobytes()
        mark = 'CHANGED (jordan)' if i == frame else ('byte-identical' if eq else 'DIFFERS')
        print('  frame %2d %-10s  before %s  after %s  %s' % (i, icons.ORDER[i], sha(fl[i].tobytes())[:16],
                                                             sha(fn[i].tobytes())[:16], mark))
        bad += (i != frame and not eq)
    if bad:
        raise SystemExit('%d other frames differ - refusing' % bad)
    png = os.path.join(work, 'rank_icons.png')
    new.save(png)
    assert Image.open(png).convert('RGBA').tobytes() == new.tobytes(), 'saved PNG does not read back'
    cell_png = os.path.join(work, 'jordan_cell.png')
    cell.save(cell_png)

    ase = os.path.join(work, 'rank_icons.aseprite')
    run_aseprite(['--script-param', 'in=' + live_ase, '--script-param', 'cell=' + cell_png,
                  '--script-param', 'frame=%d' % (frame + 1), '--script-param', 'out=' + ase,
                  '--script', os.path.join(HERE, 'frame_splice.lua')])
    ao = sheet_of(live_ase, os.path.join(work, 'ase_before_sheet.png'))
    an_path = os.path.join(work, 'ase_after_sheet.png')
    run_aseprite([ase, '--sheet', an_path, '--sheet-type', 'horizontal', '--data',
                  os.path.join(work, 'ase_after.json'), '--format', 'json-array', '--list-layers'])
    an = Image.open(an_path).convert('RGBA')
    abad = 0
    for i, (a, b) in enumerate(zip(frames(ao), frames(an))):
        d = pixel_diff(a, b)
        abad += (i != frame and d is not None) or (i == frame and pixel_diff(b, cell) is not None)
    meta = json.load(open(os.path.join(work, 'ase_after.json')))
    print('rank_icons.aseprite, frame %d\'s cel swapped in place: the other %d frames identical to the live file: %s;'
          ' frames %d, durations %s, layers %s' % (frame + 1, len(other), not abad, len(meta['frames']),
                                                   sorted({f['duration'] for f in meta['frames']}),
                                                   [ly['name'] for ly in meta['meta'].get('layers', [])]))
    rt = rtcheck(png, an_path)
    print('  rtcheck.py:', rt)
    if abad or ' 0 differing pixels' not in rt or pixel_diff(an, new):
        raise SystemExit('.aseprite check failed - refusing')
    return frame, cell, new, png, ase, live


def main(ship=False):
    if ship:
        raise SystemExit('SUPERSEDED: this spliced the 09-23 icon of the first redesign. Jordan v2 was approved '
                         '2026-09-24 and his icon is now re-cut by ladder_v2.py; this script refuses to ship.')
    work = os.path.join(PREVIEWS, 'ladder_build')
    os.makedirs(work, exist_ok=True)
    text = open(ICONS_PY, encoding='utf-8', newline='').read()
    png_bytes, ase_bytes = open(PNG, 'rb').read(), open(ASE, 'rb').read()
    pair = rtcheck(PNG, sheet_of(ASE, os.path.join(work, 'live_pair_sheet.png')) and
                   os.path.join(work, 'live_pair_sheet.png'))
    print('live pair before anything: rtcheck.py', pair)
    if ' 0 differing pixels' not in pair:
        raise SystemExit('the live rank_icons.png and .aseprite disagree (another artist mid-splice?) - refusing')
    frame, cell, new, png, ase, live = build_and_prove(work, text, png_bytes, ASE)
    print(preview(live, new, load_icons(os.path.join(work, 'icons_edited.py'), 'icons_order').ORDER, frame))
    if not ship:
        return 0

    # ---- ship. icons.py first (the source of the cell), then the strip and its .aseprite, each
    # re-read immediately before its write and refused if it moved since the proof above.
    if open(ICONS_PY, encoding='utf-8', newline='').read() != text:
        raise SystemExit('icons.py changed while this ran - refusing')
    with open(ICONS_PY, 'w', encoding='utf-8', newline='') as f:
        f.write(edited(text))
    print('wrote', ICONS_PY)
    proved_png, proved_ase = png_bytes, ase_bytes
    for attempt in range(3):
        fresh_png, fresh_ase = open(PNG, 'rb').read(), open(ASE, 'rb').read()
        if sha(fresh_png) == sha(proved_png) and sha(fresh_ase) == sha(proved_ase):
            break                                                # nothing moved since the proof
        # another artist shipped in between: rebuild and re-prove against what is there now
        print('rank_icons changed since the proof - rebuilding against the fresh copy')
        pair = rtcheck(PNG, sheet_of(ASE, os.path.join(work, 'live_pair_sheet.png')) and
                       os.path.join(work, 'live_pair_sheet.png'))
        if ' 0 differing pixels' not in pair:
            raise SystemExit('the live pair disagrees mid-ship (another splice in progress?) - refusing')
        proved_png, proved_ase = fresh_png, fresh_ase
        frame, cell, new, png, ase, live = build_and_prove(work, text, fresh_png, ASE)
    else:
        raise SystemExit('rank_icons kept changing under this script - refusing')
    read = Image.open(io.BytesIO(fresh_png)).convert('RGBA')
    shutil.copyfile(png, PNG)                                    # one write each, straight after the check
    shutil.copyfile(ase, ASE)
    for src, dst in ((png, PNG), (ase, ASE)):
        with open(src, 'rb') as a, open(dst, 'rb') as b:
            assert a.read() == b.read(), dst
        print('shipped', dst)

    # ---- what landed: every other frame byte-identical to what was read just before the write;
    # the written icons.py, imported afresh, builds exactly the cell that shipped
    landed = Image.open(PNG).convert('RGBA')
    fr, fl = frames(read), frames(landed)
    ok = all(fr[i].tobytes() == fl[i].tobytes() for i in range(11) if i != frame)
    print('landed rank_icons.png: the other 10 frames byte-identical to the copy read just before writing: %s;'
          ' frame %d is the new cell: %s' % (ok, frame, fl[frame].tobytes() == cell.tobytes()))
    icons = load_icons(ICONS_PY, 'icons_written')
    c2, s2, notes = built(icons)
    print('icons.py as written, imported afresh: jordan_cell() == shipped cell: %s; nearest() fallbacks: %s'
          % (c2.tobytes() == cell.tobytes(), notes or 'none'))
    print('landed pair: rtcheck.py', rtcheck(PNG, sheet_of(ASE, os.path.join(work, 'landed_sheet.png'))
                                         and os.path.join(work, 'landed_sheet.png')))
    return 0 if ok and c2.tobytes() == cell.tobytes() and not notes else 1


if __name__ == '__main__':
    sys.exit(main('--ship' in sys.argv))
