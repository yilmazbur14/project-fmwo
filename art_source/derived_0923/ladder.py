"""Splice one head into the Victory screen's rank ladder, Assets/UI/Screens/rank_icons.png (11 frames
of 40x40), and its .aseprite - that frame ONLY:
    python ladder.py matt [--ship]         frame 3, the grey '?' placeholder -> Matt
    python ladder.py computah [--ship]     frame 2, still Greyson in his mech -> the redesigned Computah
    python ladder.py burak_boss [--ship]   frame 0, the hooded cutscene Burak -> Captain Burak
Run matt first: the others' icons.py edits build on matt's (grid_cell).

The method is Jordan's (art_source/jordan_derived/ladder.py). THE CELL comes from
art_source/victory_screen/icons.py, which this script edits and nothing else does here:
  - REMAP[<name>]: every colour of the approved frame, by hand (icons_0923.REMAP_*), no nearest()
  - grid_cell() (matt's edit) and <name>_cell(): the half-scale head grid of icons_0923, coloured
    through that REMAP; icons_0923 says why half scale and measures the grid against the sprite
  - build() calling it; for computah also ORDER's 'mech' key -> 'computah' (Greyson's mech is out
    of the fight), and the docstring's frame list
Old REMAP entries stay, as the other characters' do.

THE RACE. Other artists work in this tree. So nothing is written without --ship; at --ship the live
PNG and .aseprite are re-read immediately before writing and must still agree with each other and
with what the build was proved against (or it rebuilds against the fresh copy); only the one frame
is replaced in that fresh copy; every other frame is proved byte-identical (raw RGBA bytes and a
sha256 per frame) before and after the write. The .aseprite has only that frame's cel swapped
(frame_splice.lua), and victory_screen/rtcheck.py must report 0 differing pixels between it and the
PNG. Before anything is written the live files are copied to the scratchpad (before_<name>/).
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
sys.path.insert(0, HERE)
import k923 as K                                                 # noqa: E402
import icons_0923 as I                                           # noqa: E402

VSD = os.path.join(K.ART, 'victory_screen')
ICONS_PY = os.path.join(VSD, 'icons.py')
SCREENS = os.path.join(K.ASSETS, 'UI', 'Screens')
PNG = os.path.join(SCREENS, 'rank_icons.png')
ASE = os.path.join(SCREENS, 'rank_icons.aseprite')

cv = I.import_cv()                                               # writers stubbed to raise
import slots                                                     # noqa: E402
from PIL import Image, ImageDraw                                 # noqa: E402

S = 40
NL = '\r\n'                                                      # icons.py is CRLF throughout
REMAP_END = NL + '}' + NL + NL + NL + 'def crop_icon('
ANCHOR = NL + NL + 'def build():' + NL


# ---------------------------------------------------------------------------------------- the edit
def py_dict_lines(d, indent, width=100):
    """"'k': V, 'k': V," wrapped at width, every line prefixed by indent."""
    items = ["'%s': %s" % (k, v) for k, v in d.items()]
    lines, cur = [], ''
    for it in items:
        piece = it + ', '
        if cur and len(indent) + len(cur) + len(piece.rstrip()) > width:
            lines.append(cur.rstrip())
            cur = ''
        cur += piece
    lines.append(cur.rstrip().rstrip(','))
    return [indent + ln for ln in lines]


def remap_entry(name, comment):
    """The REMAP[name] entry: dict(SKIN_MAP, **{...}) whose effect equals icons_0923's table."""
    h = I.HEADS[name]
    skin = {'f0b98e': 'SKIN', 'fbd6b0': 'SKIN', 'db976c': 'TAN', 'b86c4e': 'RUST', '84412f': 'BROWN',
            'f09c86': 'PINK', 'b58773': 'TAN', 'd9ab93': 'SKIN', 'fadcb8': 'SKIN', 'd6aa7c': 'TAN'}
    own = {k: v for k, v in h['remap'].items() if skin.get(k) != v}
    head = "    '%s': dict(SKIN_MAP, **{" % name
    body = py_dict_lines(own, ' ' * len(head))
    body[0] = head + body[0].lstrip()
    body[-1] += '}),'
    return NL.join(['    # ' + ln for ln in comment] + body)


def grid_lines(rows, indent='    '):
    return [indent + '"%s",' % r for r in rows]


def pal_line(var, pal):
    head = '%s = {' % var
    body = py_dict_lines({k: "'%s'" % v for k, v in pal.items()}, ' ' * len(head))
    body[0] = head + body[0].lstrip()
    body[-1] += '}'
    return body


GRID_CELL = [
    "# Matt (frame 3) and Computah (frame 2) are cut at HALF scale, not 1:1: the window is 27 px across,",
    "# Matt's five-spike crest is 54 and Computah's head with its ear pods 51, so at 1:1 neither his",
    "# yellow-tipped crest nor the robot's silhouette could be in it. Each grid below is the approved",
    "# frame taken 2:1 - one pixel per 2x2 block - in the sprite's own colours, keyed per hex, then",
    "# hand-cleaned where halving broke a keyline. art_source/derived_0923/icons_0923.py derives the",
    "# grids, measures how much of each is the sprite's own, and holds the reasoning.",
    "def grid_cell(key, rows, pal, ox, oy, col, shade):",
    '    """A half-scale head from a grid of its sprite\'s own colours (pal: grid key -> hex), coloured',
    '    through REMAP[key] as crop_icon colours a crop, with grid (0, 0) on cell (ox, oy)."""',
    "    rm = REMAP[key]",
    "    cv = Canvas(S, S)",
    "    for j, row in enumerate(rows):",
    "        for i, ch in enumerate(row):",
    "            if ch != '.' and in_win(ox + i, oy + j, PAD):",
    "                h = pal[ch]",
    "                cv.set(ox + i, oy + j, rm[h] if h in rm else h)",
    "    bg_disc(cv, col, shade)",
    "    return cv",
]

JOBS = {
    'matt': dict(
        frame_key='matt',
        remap_comment=[
            "Matt: the approved 2026-09-23 matt.png frame 0 (art_source/matt/pal.py), every colour of it",
            "by hand - see art_source/derived_0923/icons_0923.py. The dyed tips go WHITE, YEL, YEL, TAN,",
            "BRASS: a step brighter than Josh's gold, and not nearest()'s TAN for e2b13c, which is his skin",
            "shadow - on a half-scale head the yellow tips are what says Matt. The blue-black hair K, NAVY,",
            "INDIGO, INDIGO, where nearest() merges its deepest tone into the base and puts its sheen on",
            "greenish SLATE; the lavender crewneck PALE, BLURPLE, INDIGO; the charcoal NAVY to ASH.",
        ],
        block_lines=lambda: GRID_CELL + ['', ''] + [
            "# matt.png frame 0 from x20 y0, 2:1; keys as art_source/matt/pal.py names them.",
        ] + pal_line('MATT_PAL', I.MATT_PAL) + ['MATT_HEAD = ['] + grid_lines(I.MATT_HEAD) + [']', '', '',
            "def matt_cell():",
            '    """Matt\'s slot, from the approved 2026-09-23 matt.png frame 0 (the idle) at half scale: all',
            "    five spikes of the crest with their yellow tips - the outer pair's points under the ring -",
            "    over the brows, the eyes and the lopsided grin, the yellow collar at the foot of the disc.",
            '    Sky-blue disc, the complement the yellow tips stand out on."""',
            "    return grid_cell('matt', MATT_HEAD, MATT_PAL, %d, %d, %s, %s)" % (I.MATT_AT + I.MATT_DISC),
        ],
        swaps=[
            ("3 Matt (placeholder - no art yet)", "3 Matt"),
            ("    ic['matt'] = placeholder_icon(GREY, DASH)" + NL, "    ic['matt'] = matt_cell()" + NL),
        ],
        new_def='def matt_cell',
    ),
    'computah': dict(
        frame_key='computah',
        remap_comment=[
            "Computah: the redesigned robot of 2026-09-22, computah_idle.png frame 0, every colour of it",
            "by hand - see art_source/derived_0923/icons_0923.py. His keyline is #0C111A (the sheet has",
            "no pure black), which goes to K, the ladder's keyline. The lit dome a063dc is PURPLE, not",
            "nearest()'s BLURPLE, which turns the dome blue; its shade 592687 PLUM, not INDIGO; the",
            "visor's dark steels NAVY, not INDIGO or SLATE; the eyes' hot core PINK in a RED rim.",
        ],
        block_lines=lambda: [
            "# computah_idle.png frame 0 (the idle his fight plays) from x16 y5, 2:1; keyline #0C111A.",
        ] + pal_line('COMPUTAH_PAL', I.COMPUTAH_PAL) + ['COMPUTAH_HEAD = ['] + grid_lines(I.COMPUTAH_HEAD) + [
            ']', '', '',
            "def computah_cell():",
            '    """Computah\'s slot, from the redesigned robot of 2026-09-22 (computah_idle.png frame 0) at',
            "    half scale: the purple dome, the visor with its red eyes and grille, both ear pods, the chin",
            "    plate and the antenna stalk running off under the ring. The slot showed Greyson in the",
            "    retired mech until now. Lime disc: his charge green, the complement of his purple.\"\"\"",
            "    return grid_cell('computah', COMPUTAH_HEAD, COMPUTAH_PAL, %d, %d, %s, %s)"
            % (I.COMPUTAH_AT + I.COMPUTAH_DISC),
        ],
        swaps=[
            ("2 Greyson & Computah (mech)", "2 Computah"),
            ("ORDER = ['burak', 'eric', 'mech', 'matt',", "ORDER = ['burak', 'eric', 'computah', 'matt',"),
            ("    ic['mech'] = crop_icon('mech', CHAR + \"GreysonMech/greyson_mech.png\", 48, 24)" + NL +
             "    bg_disc(ic['mech'], PURPLE, PLUM)" + NL, "    ic['computah'] = computah_cell()" + NL),
        ],
        new_def='def computah_cell',
    ),
    'burak_boss': dict(
        frame_key='burak',
        remap_comment=[
            "Captain Burak: his approved boss design, burak_boss.png frame 0, every colour of it by hand -",
            "see art_source/derived_0923/icons_0923.py. The skin's base d79864 sits on TAN, its shadow",
            "ac714f on RUST, not nearest()'s olive BRASS; the hair K, PLUM, BROWN, RUST like Jordan's, not",
            "nearest()'s NAVY; the tricorn NAVY lit INDIGO, not SLATE and DASH; his gold trim is Josh's",
            "ramp exactly and maps as Josh's does; the coat's crimson as Josh's; the bandana PINK and RED.",
        ],
        block_lines=lambda: [
            "# burak_boss.png frame 0 (Captain Burak, the idle) from x22 y1, 2:1.",
        ] + pal_line('BURAK_PAL', I.BURAK_PAL) + ['BURAK_HEAD = ['] + grid_lines(I.BURAK_HEAD) + [
            ']', '', '',
            "def burak_boss_cell():",
            '    """Burak\'s slot, from his approved boss design (burak_boss.png frame 0, the idle) at half',
            "    scale: the tricorn's crown and its gold-trimmed brim sweeping down to the front point - the",
            "    upturned tips under the ring - over the curtain bangs parted on his forehead, the eyes, the",
            "    smirk rising to his right, and the red bandana tails at the ring. The slot showed the hooded",
            '    cutscene Burak until now; the cyan disc is the slot\'s own."""',
            "    return grid_cell('burak_boss', BURAK_HEAD, BURAK_PAL, %d, %d, %s, %s)" % (I.BURAK_AT + I.BURAK_DISC),
        ],
        swaps=[
            ("    ic['burak'] = crop_icon('burak', ASSETS + \"Cutscenes/Intro/burak_cutscene.png\", 166, 26)" + NL +
             "    bg_disc(ic['burak'], CYAN, STEEL)" + NL, "    ic['burak'] = burak_boss_cell()" + NL),
        ],
        new_def='def burak_boss_cell',
    ),
}


def pieces(job):
    j = JOBS[job]
    entry = remap_entry(job, j['remap_comment'])
    block = NL.join(j['block_lines']())
    return entry, block


def edited(text, job):
    """icons.py with the job's changes and nothing else. Idempotent: on an icons.py that already
    carries them exactly, it returns the text unchanged, so a re-run proves the shipped state."""
    j = JOBS[job]
    entry, block = pieces(job)
    # Each piece once, wherever a later job's edit has put its neighbours (computah's entry and block
    # land after matt's, so matt's no longer sit right before the anchors).
    done = [NL + entry + NL, NL + NL + block + NL + NL] + [new for _, new in j['swaps']]
    if all(text.count(p) == 1 for p in done):
        return text
    anchors = [REMAP_END, ANCHOR] + [old for old, _ in j['swaps']]
    for a in anchors:
        assert text.count(a) == 1, 'icons.py is not as this script expects: %r (x%d)' % (a[:70], text.count(a))
    assert j['new_def'] not in text, '%s already in icons.py, but not as this script writes it' % j['new_def']
    if job != 'matt':
        assert 'def grid_cell' in text, 'run ladder.py matt --ship first: %s needs its grid_cell()' % job
    out = text.replace(REMAP_END, NL + entry + REMAP_END).replace(ANCHOR, NL + NL + block + NL + ANCHOR)
    for old, new in j['swaps']:
        out = out.replace(old, new)
    assert out.count('\r\n') == out.count('\n'), 'line endings'
    return out


# ---------------------------------------------------------------------------------------- build
def load_icons(path, name):
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


def built(icons, job):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        cell = getattr(icons, job + '_cell')()
        strip = icons.strip(icons.build())
    notes = [ln for ln in out.getvalue().splitlines() if job in ln]
    return image(cell), image(strip), notes


def check_cell(cell, job, icons):
    """The cell the edited icons.py builds is exactly icons_0923's grid through its REMAP, on the disc."""
    h = I.HEADS[job]
    db = I.remapped(job)
    ox, oy = h['at']
    disc = {cv.rgba(getattr(cv, h['disc'][0])), cv.rgba(getattr(cv, h['disc'][1]))}
    px = cell.load()
    bad = 0
    for y in range(S):
        for x in range(S):
            inside = icons.in_win(x, y, icons.PAD)
            gx, gy = x - ox, y - oy
            want = db[gy][gx] if 0 <= gy < len(db) and 0 <= gx < len(db[0]) else None
            got = px[x, y]
            if not inside:
                bad += got[3] != 0
            elif want is not None:
                bad += got != cv.rgba(want)
            else:
                bad += got not in disc
    return bad


def frames(im):
    return [im.crop((i * S, 0, i * S + S, S)) for i in range(im.width // S)]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rtcheck(a, b):
    r = subprocess.run([sys.executable, os.path.join(VSD, 'rtcheck.py'), a, b], capture_output=True, text=True,
                       cwd=VSD, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    return r.stdout.strip() or r.stderr.strip()


def sheet_of(ase, out):
    K.aseprite([ase, '--sheet', out, '--sheet-type', 'horizontal'])
    return out


def ring_row(strip, state=1):
    ring = image(slots.build()[state])
    goal = image(slots.build()[4])
    row = Image.new('RGBA', (strip.width, S), (20, 20, 26, 255))
    for i, f in enumerate(frames(strip)):
        t = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        t.alpha_composite(f)
        t.alpha_composite(goal if i == 10 else ring)
        row.alpha_composite(t, (i * S, 0))
    return row


def preview(before, after, order, frame, job):
    rows = [K.up(ring_row(s), 6, bg=None) for s in (before, after)]
    out = Image.new('RGBA', (rows[0].width, rows[0].height * 2 + 30), (10, 10, 12, 255))
    out.paste(rows[0], (0, 0))
    out.paste(rows[1], (0, rows[0].height + 30))
    d = ImageDraw.Draw(out)
    x0 = frame * S * 6
    d.rectangle([x0, rows[0].height + 2, x0 + S * 6 - 1, rows[0].height + 27], fill=(240, 200, 80, 255))
    d.text((x0 + 6, rows[0].height + 8), 'frame %d (%s): the only change' % (frame, order[frame]), fill=(0, 0, 0, 255))
    p1 = K.preview(out, 'ladder_%s_before_after_6x.png' % job)
    states = [K.label(K.up(ring_row(after.crop((frame * S, 0, frame * S + S, S)), st), 8, bg=None), n)
              for st, n in ((1, 'cleared'), (2, 'current'), (3, 'current, pulse'))]
    p2 = K.preview(K.row(states), 'ladder_%s_cell_states_8x.png' % job)
    return p1, p2


def build_and_prove(work, text, live_png_bytes, live_ase, job):
    """Everything short of writing into the project, against the given live bytes / .aseprite."""
    tmp_icons = os.path.join(work, 'icons_edited.py')
    with open(tmp_icons, 'w', encoding='utf-8', newline='') as f:
        f.write(edited(text, job))
    icons = load_icons(tmp_icons, 'icons_edited_%s' % job)
    frame = icons.ORDER.index(JOBS[job]['frame_key'])
    cell, strip, notes = built(icons, job)
    print('%s cell: frame %d of %d; nearest() fallbacks: %s' % (job, frame, len(icons.ORDER), notes or 'none'))
    assert not notes, notes
    bad = check_cell(cell, job, icons)
    cols = {c[:3] for c in K.flat(cell) if c[3]}
    print('  the edited icons.py builds icons_0923\'s grid through its REMAP exactly: %s (%d px off); '
          '%d colours, all DB32: %s; alpha %s' % (bad == 0, bad, len(cols),
                                                 not ({'%02x%02x%02x' % c for c in cols} - cv.DB),
                                                 sorted({c[3] for c in K.flat(cell)})))
    assert bad == 0

    live = Image.open(io.BytesIO(live_png_bytes)).convert('RGBA')
    assert live.size == (S * 11, S), live.size
    fl, fb = frames(live), frames(strip)
    other = [i for i in range(11) if i != frame]
    same = [i for i in other if fl[i].tobytes() == fb[i].tobytes()]
    print('  edited icons.py, whole strip, vs the live strip: %d of %d other frames identical %s'
          % (len(same), len(other), '' if len(same) == len(other) else '(differs: %s)' % sorted(set(other) - set(same))))
    assert fb[frame].tobytes() == cell.tobytes()

    new = live.copy()
    new.paste(cell, (frame * S, 0))                              # replaces all 1600 px of the frame
    fn = frames(new)
    nbad = 0
    table = []
    for i in range(11):
        eq = fl[i].tobytes() == fn[i].tobytes()
        mark = 'CHANGED (%s)' % job if i == frame else ('byte-identical' if eq else 'DIFFERS')
        table.append('  frame %2d %-11s before %s  after %s  %s' % (i, icons.ORDER[i], sha(fl[i].tobytes())[:16],
                                                                   sha(fn[i].tobytes())[:16], mark))
        nbad += (i != frame and not eq)
    print('\n'.join(table))
    if nbad:
        raise SystemExit('%d other frames differ - refusing' % nbad)
    png = K.refuse_live(os.path.join(work, 'rank_icons.png'))
    new.save(png)
    assert Image.open(png).convert('RGBA').tobytes() == new.tobytes(), 'saved PNG does not read back'
    cell_png = os.path.join(work, '%s_cell.png' % job)
    cell.save(cell_png)

    ase = K.refuse_live(os.path.join(work, 'rank_icons.aseprite'))
    K.aseprite(['--script-param', 'in=' + live_ase, '--script-param', 'cell=' + cell_png,
                '--script-param', 'frame=%d' % (frame + 1), '--script-param', 'out=' + ase,
                '--script', os.path.join(HERE, 'frame_splice.lua')])
    ao = Image.open(sheet_of(live_ase, os.path.join(work, 'ase_before_sheet.png'))).convert('RGBA')
    an_path = os.path.join(work, 'ase_after_sheet.png')
    K.aseprite([ase, '--sheet', an_path, '--sheet-type', 'horizontal', '--data',
                os.path.join(work, 'ase_after.json'), '--format', 'json-array', '--list-layers', '--list-tags'])
    K.aseprite([live_ase, '--sheet', os.path.join(work, 'ase_before_sheet2.png'), '--sheet-type', 'horizontal',
                '--data', os.path.join(work, 'ase_before.json'), '--format', 'json-array', '--list-layers',
                '--list-tags'])
    an = Image.open(an_path).convert('RGBA')
    abad = 0
    for i, (a, b) in enumerate(zip(frames(ao), frames(an))):
        abad += (i != frame and K.pixel_diff(a, b) is not None) or (i == frame and K.pixel_diff(b, cell) is not None)
    ma, mb = (json.load(open(os.path.join(work, n))) for n in ('ase_before.json', 'ase_after.json'))
    meta_same = ([f['duration'] for f in ma['frames']] == [f['duration'] for f in mb['frames']]
                 and ma['meta'].get('layers') == mb['meta'].get('layers')
                 and ma['meta'].get('frameTags') == mb['meta'].get('frameTags'))
    print('rank_icons.aseprite, frame %d\'s cel swapped in place: the other %d frames identical to the live file: %s;'
          ' frames %d, durations/layers/tags unchanged: %s (layers %s)'
          % (frame + 1, len(other), not abad, len(mb['frames']), meta_same,
             [ly['name'] for ly in mb['meta'].get('layers', [])]))
    rt = rtcheck(png, an_path)
    print('  rtcheck.py (new PNG vs new .aseprite):', rt)
    if abad or not meta_same or ' 0 differing pixels' not in rt or K.pixel_diff(an, new):
        raise SystemExit('.aseprite check failed - refusing')
    return frame, cell, new, png, ase, live, icons.ORDER


def live_pair_ok(work, tag):
    p = sheet_of(ASE, os.path.join(work, 'live_pair_sheet_%s.png' % tag))
    r = rtcheck(PNG, p)
    return r, ' 0 differing pixels' in r


def main(job, ship=False):
    work = os.path.join(K.PREVIEWS, 'ladder_%s' % job)
    os.makedirs(work, exist_ok=True)
    text = open(ICONS_PY, encoding='utf-8', newline='').read()
    png_bytes, ase_bytes = K.read_bytes(PNG), K.read_bytes(ASE)
    r, ok = live_pair_ok(work, 'start')
    print('live pair before anything: rtcheck.py', r)
    if not ok:
        raise SystemExit('the live rank_icons.png and .aseprite disagree (another artist mid-splice?) - refusing')
    frame, cell, new, png, ase, live, order = build_and_prove(work, text, png_bytes, ASE, job)
    backup = os.path.join(K.PREVIEWS, 'before_%s' % job)
    before = (Image.open(os.path.join(backup, 'rank_icons.png')).convert('RGBA')
              if os.path.exists(os.path.join(backup, 'rank_icons.png')) else live)
    for p in preview(before, new, order, frame, job):
        print(p)
    if not ship:
        return 0

    # ---- ship. First a copy of everything about to be replaced, then icons.py (the source of the
    # cell), then the strip and its .aseprite, each re-read immediately before its write.
    os.makedirs(backup, exist_ok=True)
    for src, nm in ((ICONS_PY, 'icons.py'), (PNG, 'rank_icons.png'), (ASE, 'rank_icons.aseprite')):
        dst = os.path.join(backup, nm)
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
    if open(ICONS_PY, encoding='utf-8', newline='').read() != text:
        raise SystemExit('icons.py changed while this ran - refusing')
    new_text = edited(text, job)
    if new_text != text:
        with open(ICONS_PY, 'w', encoding='utf-8', newline='') as f:
            f.write(new_text)
        print('wrote', ICONS_PY)
    else:
        print('icons.py already carries the', job, 'edit')
    proved_png, proved_ase = png_bytes, ase_bytes
    for attempt in range(3):
        fresh_png, fresh_ase = K.read_bytes(PNG), K.read_bytes(ASE)
        if sha(fresh_png) == sha(proved_png) and sha(fresh_ase) == sha(proved_ase):
            break
        print('rank_icons changed since the proof - rebuilding against the fresh copy')
        r, ok = live_pair_ok(work, 'fresh%d' % attempt)
        if not ok:
            raise SystemExit('the live pair disagrees mid-ship (another splice in progress?) - refusing')
        proved_png, proved_ase = fresh_png, fresh_ase
        frame, cell, new, png, ase, live, order = build_and_prove(work, new_text, fresh_png, ASE, job)
    else:
        raise SystemExit('rank_icons kept changing under this script - refusing')
    read = Image.open(io.BytesIO(fresh_png)).convert('RGBA')
    shutil.copyfile(png, PNG)                                    # one write each, straight after the check
    shutil.copyfile(ase, ASE)
    for src, dst in ((png, PNG), (ase, ASE)):
        assert K.read_bytes(src) == K.read_bytes(dst), dst
        print('shipped', dst)

    landed = Image.open(PNG).convert('RGBA')
    fr, fl = frames(read), frames(landed)
    others = [i for i in range(11) if i != frame]
    ok = all(fr[i].tobytes() == fl[i].tobytes() for i in others)
    print('landed rank_icons.png: the other %d frames byte-identical to the copy read just before writing: %s;'
          ' frame %d is the new cell: %s' % (len(others), ok, frame, fl[frame].tobytes() == cell.tobytes()))
    for i in range(11):
        print('  frame %2d %-11s read %s  landed %s  %s' % (
            i, order[i], sha(fr[i].tobytes())[:16], sha(fl[i].tobytes())[:16],
            'NEW' if i == frame else ('byte-identical' if fr[i].tobytes() == fl[i].tobytes() else 'DIFFERS')))
    icons = load_icons(ICONS_PY, 'icons_written_%s' % job)
    c2, s2, notes = built(icons, job)
    print('icons.py as written, imported afresh: %s_cell() == shipped cell: %s; nearest() fallbacks: %s'
          % (job, c2.tobytes() == cell.tobytes(), notes or 'none'))
    r = rtcheck(PNG, sheet_of(ASE, os.path.join(work, 'landed_sheet.png')))
    print('landed pair: rtcheck.py', r)
    return 0 if ok and c2.tobytes() == cell.tobytes() and not notes and ' 0 differing pixels' in r else 1


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 1 or args[0] not in JOBS:
        raise SystemExit('usage: python ladder.py %s [--ship]' % '|'.join(JOBS))
    sys.exit(main(args[0], '--ship' in sys.argv))
