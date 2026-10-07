"""Jordan's puppets: the TREATMENT that turns any frame of a boss into its undead-puppet version.

It is a pure function of (the source frame's pixels, the boss's recipe data in jp_bosses, a take in
jp_palette). Nothing here reads anything but the source PNGs and nothing here writes a file.

THE TWIN RULE (the build plan's contract): a puppet frame keeps its source's size, frame grid,
anchors and SILHOUETTE exactly, pure-black keylines stay black, there is no semi-alpha, and every
addition (glow, stitches, wounds, rings) is a recoloured pixel INSIDE the silhouette. Every pass below
obeys it and treat() audits it on every frame.

The passes, in order (treat()):
  1. RECOLOUR   every source colour -> (material, puppet key) by the boss's table (a second form, a
                prop, gets its own table by sheet path). Fully automatic on any frame drawn in the
                boss's palette; an unmapped colour is reported, never guessed.
  2. TRACK      each part box of the boss's KEY frame (its idle) is found again in the target frame by
                exact-colour template matching on the ORIGINAL pixels. A part is "found" when enough of
                its template matches; whatever rides a part that is not found is skipped and reported.
  2b. REGIONS   a prop drawn in a colour the body also uses gets its own mapping inside boxes that ride
                a tracked part (Captain Burak's brass flintlock, Liam's glare lenses).
  3. TATTER     automatic: V-notches cut up into cloth hems, keyed to the tracked torso so they ride
                with the garment. On the silhouette's edge the notch is inked black; over another
                material (trousers over socks) that material shows through.
  4. OVERLAYS   hand-drawn touches kept as DATA in key-frame coordinates (sockets and pupils, stitches,
                scars, jaw hinges, wounds), each riding one part and painting only the materials it names.
  5. HOOKS      string rings (screw eyes) at the head/crown, both wrists and both knees, each on its
                tracked part and snapped (within 2 texels) wholly inside the silhouette; the BACK point
                (between the shoulder blades) is recorded, never drawn: it is behind the body in every
                front view, so the engine draws that string under the sprite.
  6. KEYLINE    any non-black pixel left on the silhouette's edge turns pure black (an effect's detached
                motes keep their colour).
  7. AUDIT      palette-only keys, the twin rule, keyline gaps, new specks, new pinholes; and an account
                of every interior black pixel a pass recoloured, by cause.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
CHARS = os.path.join(ROOT, 'Assets', 'Characters')
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if ART not in sys.path:
    sys.path.append(ART)

import jp_palette as PAL  # noqa: E402

ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')


# ------------------------------------------------------------------ source frames (read only)

_SHEETS = {}


def sheet(rel):
    """A source sheet under Assets/Characters, RGBA, as a numpy array (cached). Never written."""
    if rel not in _SHEETS:
        _SHEETS[rel] = np.array(Image.open(os.path.join(CHARS, rel)).convert('RGBA'))
    return _SHEETS[rel]


def frame(rel, fw, fh, f):
    s = sheet(rel)
    n = s.shape[1] // fw
    if not 0 <= f < n:
        raise IndexError('%s has %d frames, asked for %d' % (rel, n, f))
    return s[0:fh, f * fw:(f + 1) * fw].copy()


def frames_in(rel, fw):
    return sheet(rel).shape[1] // fw


def hexof(c):
    return '%02X%02X%02X' % (int(c[0]), int(c[1]), int(c[2]))


# ------------------------------------------------------------------ the recipe tables

def table(text):
    """Parse a recipe table: one line per target, `material key HEX HEX ...` (# starts a comment).
    Returns {HEX: (material, key)}; a colour listed twice is an error."""
    out = {}
    for ln in text.splitlines():
        ln = ln.split('#', 1)[0].strip()
        if not ln:
            continue
        parts = ln.split()
        mat, key, cols = parts[0], parts[1], parts[2:]
        if key not in PAL.KEYS:
            raise ValueError('unknown puppet key %s in %r' % (key, ln))
        for c in cols:
            c = c.upper()
            if c in out:
                raise ValueError('colour %s listed twice (%s and %s)' % (c, out[c], (mat, key)))
            out[c] = (mat, key)
    return out


# Stamp characters -> puppet keys; '-' and '+' shade whatever is under them one ramp step darker /
# lighter (so a crack or a socket ring works on any skin tone under it); '.' leaves the pixel alone.
# 'H' is a ring's glint and 'S' stitch thread (aliases each take colours its own way). A stamp only
# ever RECOLOURS pixels inside the silhouette: it never adds a pixel over air or erases one (the twin
# rule: a puppet sheet keeps its source's silhouette, so every hitbox and anchor carries over).
STAMP = {
    'K': 'K', 'p': 'P1', 'd': 'D2', 'a': 'A2', 'm': 'A3', 'n': 'A4', 'l': 'A5', 'w': 'B1',
    '1': 'R1', '2': 'R2', '3': 'R3', '4': 'R4', 'i': 'I2', 'j': 'I3', 'g': 'G1', 'h': 'G2',
    'H': 'HG', 'S': 'ST',
}


def stamp(x0, y0, rows):
    """An ASCII stamp -> {(x, y): char} with its top-left at (x0, y0). Spaces are ignored inside a row
    only when the row is written with '|' delimiters; otherwise every character is a pixel."""
    out = {}
    lines = [r for r in rows.split('\n') if r.strip()]
    for dy, row in enumerate(lines):
        row = row.strip()
        if row.startswith('|') and row.endswith('|'):
            row = row[1:-1]
        for dx, ch in enumerate(row):
            if ch in ('.', ' '):
                continue
            out[(x0 + dx, y0 + dy)] = ch
    return out


def merge(*stamps):
    out = {}
    for s in stamps:
        out.update(s)
    return out


def mirror(st, axis2):
    """Mirror a stamp about x = axis2 / 2."""
    return {(axis2 - x, y): ch for (x, y), ch in st.items()}


# ------------------------------------------------------------------ tracking

def track(key_rgba, box, tgt_rgba, radius=10, prior=(0, 0)):
    """Find the key frame's `box` (x0, y0, x1, y1 inclusive) in the target frame. Returns
    (dx, dy, score): the offset with the most exactly-matching template pixels (only the template's
    opaque pixels count; landing on transparency counts as a miss), score = matched / opaque.
    Ties go to the smallest move from `prior`."""
    x0, y0, x1, y1 = box
    tpl = key_rgba[y0:y1 + 1, x0:x1 + 1]
    mask = tpl[:, :, 3] > 0
    n = int(mask.sum())
    if n == 0:
        return 0, 0, 0.0
    H, W = tgt_rgba.shape[:2]
    pad = radius + max(abs(prior[0]), abs(prior[1])) + 2
    big = np.zeros((H + 2 * pad, W + 2 * pad, 4), np.uint8)
    big[pad:pad + H, pad:pad + W] = tgt_rgba
    tpl32 = tpl.view(np.uint32).reshape(tpl.shape[:2])
    big32 = big.view(np.uint32).reshape(big.shape[:2])
    best = None
    h, w = tpl.shape[:2]
    for dy in range(prior[1] - radius, prior[1] + radius + 1):
        for dx in range(prior[0] - radius, prior[0] + radius + 1):
            yy, xx = pad + y0 + dy, pad + x0 + dx
            if yy < 0 or xx < 0 or yy + h > big32.shape[0] or xx + w > big32.shape[1]:
                continue
            win = big32[yy:yy + h, xx:xx + w]
            m = int(((win == tpl32) & mask).sum())
            cost = (dx - prior[0]) ** 2 + (dy - prior[1]) ** 2
            cand = (m, -cost, dx, dy)
            if best is None or cand > best:
                best = cand
    m, _c, dx, dy = best
    return dx, dy, m / n


# ------------------------------------------------------------------ the working frame

KEEP = 'KP'        # the key of a pixel kept exactly as its source (a keep region); never a palette key


class Work:
    """A frame being treated: `key` (puppet key or '' for air), `mat` (material or ''), and `new`
    (pixels the treatment added outside the source silhouette)."""

    def __init__(self, h, w):
        self.h, self.w = h, w
        self.key = np.full((h, w), '', dtype='<U2')
        self.mat = np.full((h, w), '', dtype='<U8')
        self.new = np.zeros((h, w), bool)
        self.notes = []
        self.unblack = {}          # cause -> how many black pixels it recoloured

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def opaque(self, x, y):
        return self.inside(x, y) and self.key[y, x] != ''

    def image(self, take):
        pal = PAL.colours(take)
        out = np.zeros((self.h, self.w, 4), np.uint8)
        for k, c in pal.items():
            out[self.key == k] = c
        # a KEEP pixel is someone else's, drawn into the frame (the player in Eric's bear hug): it keeps
        # its source pixel exactly
        kp = self.key == KEEP
        if kp.any():
            out[kp] = self.src[kp]
        return Image.fromarray(out, 'RGBA')


def recolour(src, tab, fallback=None):
    """Pass 1. Returns (Work, unknown colours {hex: count})."""
    h, w = src.shape[:2]
    wk = Work(h, w)
    wk.src = src
    unknown = {}
    a = src[:, :, 3]
    if ((a > 0) & (a < 255)).any():
        wk.notes.append('source has semi-alpha: %d px' % int(((a > 0) & (a < 255)).sum()))
    cache = {}
    for y in range(h):
        row = src[y]
        for x in range(w):
            c = row[x]
            if c[3] == 0:
                continue
            hx = cache.get(tuple(c))
            if hx is None:
                hx = cache[tuple(c)] = hexof(c)
            got = tab.get(hx)
            if got is None:
                unknown[hx] = unknown.get(hx, 0) + 1
                got = fallback(c) if fallback else ('?', 'K')
            wk.mat[y, x], wk.key[y, x] = got
    return wk, unknown


def paint(wk, st, dx, dy, on=None, off=None, tag='overlay'):
    """Passes 4-5. Lay a stamp at offset (dx, dy), recolouring pixels inside the silhouette only. `on`:
    only over these materials; `off`: never over these. Returns (changed, dropped): `dropped` counts
    the stamp's pixels that fell on air or off the frame and were left out."""
    n = dropped = 0
    for (x, y), ch in st.items():
        x, y = x + dx, y + dy
        if not wk.inside(x, y) or wk.key[y, x] == '':
            dropped += 1
            continue
        cur = wk.key[y, x]
        m = wk.mat[y, x]
        if cur == KEEP:                  # someone else's pixel: never painted over
            continue
        if on is not None and m not in on:
            continue
        if off is not None and m in off:
            continue
        if ch == '-':
            nk = PAL.DARKER.get(cur, cur)
        elif ch == '+':
            nk = PAL.LIGHTER.get(cur, cur)
        else:
            nk = STAMP[ch]
        if nk != cur:
            if cur == 'K':
                wk.unblack[tag] = wk.unblack.get(tag, 0) + 1
            wk.key[y, x] = nk
            n += 1
    return n, dropped


# ------------------------------------------------------------------ pass 4: tatter

def _notches(seed, span=160, spacing=(3, 7), depths=(1, 2, 2, 3, 3)):
    """A fixed, irregular run of V-notches: {relative x: depth}. One step per column on each side of
    a notch, so every cut edge is a clean diagonal stair."""
    rnd = np.random.RandomState(seed)
    depth = {}
    x = -span
    while x < span:
        x += int(rnd.randint(spacing[0], spacing[1]))
        d = int(rnd.choice(list(depths)))
        for k in range(-d + 1, d):
            dd = d - abs(k)
            depth[x + k] = max(depth.get(x + k, 0), dd)
    return depth


def tatter(wk, mats, centre_x, seed=7, max_depth=3, keep=3, rows=None, cols=None, inner=False,
           spacing=(3, 7), depths=(1, 2, 2, 3, 3)):
    """Cut V-notches up into the hems of `mats`: a column whose lowest cloth pixel has the keyline
    under it. The silhouette never changes (the twin rule): on the silhouette's edge (air under the
    keyline) the notch is inked in keyline black, which reads as a torn gap against the dark void;
    with `inner`, a hem that lies over another material (trousers over socks, trunks over thighs) is
    cut too and that material shows through the notch. The keyline always moves up into the cut, so
    every cut edge is a clean one-texel stair. `keep` cloth pixels always stay above a cut; `rows` /
    `cols` (inclusive ranges) limit where hems may be cut. Returns the number of columns cut."""
    pat = _notches(seed, spacing=spacing, depths=depths)
    cuts = 0
    for x in range(wk.w):
        if cols and not cols[0] <= x <= cols[1]:
            continue
        d = pat.get(x - centre_x, 0)
        if d <= 0:
            continue
        y = wk.h - 2
        while y > 0:
            if wk.mat[y, x] not in mats or wk.key[y + 1, x] != 'K':
                y -= 1
                continue
            below = wk.key[y + 2, x] if y + 2 < wk.h else ''
            if below == 'K' or (below != '' and not inner) or (rows and not rows[0] <= y <= rows[1]):
                y -= 1
                continue
            run = 0
            yy = y
            while yy >= 0 and wk.mat[yy, x] in mats:
                run += 1
                yy -= 1
            dd = min(d, max_depth, run - keep)
            if dd > 0:
                fk, fm = (wk.key[y + 2, x], wk.mat[y + 2, x]) if below != '' else ('K', 'line')
                if fk != 'K':
                    wk.unblack['tatter (the hem keyline moved up)'] = wk.unblack.get('tatter (the hem keyline moved up)', 0) + 1
                for yy in range(y - dd + 2, y + 2):
                    wk.key[yy, x], wk.mat[yy, x] = fk, fm
                wk.key[y - dd + 1, x], wk.mat[y - dd + 1, x] = 'K', 'line'
                cuts += 1
            # one cut per hem: carry on above this garment's run in the column
            y -= run
    return cuts


# ------------------------------------------------------------------ pass 6/7: keyline and lint

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def unify_keyline(wk, keep_fx=()):
    """Any opaque non-black pixel touching air (4-neighbour) becomes keyline, so the whole family
    carries one pure-black silhouette line. Pixels in `keep_fx` (source effect specks) are left."""
    n = 0
    k = wk.key
    air = np.pad(k == '', 1, constant_values=True)
    touch = air[:-2, 1:-1] | air[2:, 1:-1] | air[1:-1, :-2] | air[1:-1, 2:]
    sel = (k != '') & (k != 'K') & touch
    for (y, x) in zip(*np.nonzero(sel)):
        if (x, y) in keep_fx:
            continue
        k[y, x] = 'K'
        wk.mat[y, x] = 'line'
        n += 1
    return n


def lint(wk, fx=()):
    fx = set(fx)
    k = wk.key
    op = k != ''
    gaps, lone, holes = [], [], []
    H, W = k.shape
    P = np.pad(op, 1, constant_values=False)
    for (y, x) in zip(*np.nonzero(op)):
        if (x, y) in fx:
            continue
        if k[y, x] != 'K' and any(not (0 <= x + dx < W and 0 <= y + dy < H) or not op[y + dy, x + dx] for dx, dy in N4):
            gaps.append((int(x), int(y)))
        if not any(P[y + 1 + dy, x + 1 + dx] for dx, dy in N8):
            lone.append((int(x), int(y)))
    for (y, x) in zip(*np.nonzero(~op)):
        if 0 < x < W - 1 and 0 < y < H - 1 and all(op[y + dy, x + dx] for dx, dy in N4):
            holes.append((int(x), int(y)))
    bad = sorted(set(np.unique(k[op]).tolist()) - set(PAL.KEYS) - {KEEP})
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'bad_keys': bad}


def source_holes(src):
    op = src[:, :, 3] > 0
    H, W = op.shape
    return {(int(x), int(y)) for (y, x) in zip(*np.nonzero(~op))
            if 0 < x < W - 1 and 0 < y < H - 1 and op[y - 1, x] and op[y + 1, x] and op[y, x - 1] and op[y, x + 1]}


def source_lone(src, max_size=4):
    """The source's floating motes: detached 8-connected specks of at most `max_size` pixels (an aura's
    sparks). The twin rule keeps them, in colour and without a keyline."""
    op = src[:, :, 3] > 0
    H, W = op.shape
    seen = np.zeros_like(op)
    out = set()
    for (y0, x0) in zip(*np.nonzero(op)):
        if seen[y0, x0]:
            continue
        comp, stack = [], [(int(x0), int(y0))]
        seen[y0, x0] = True
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            if len(comp) > max_size:
                break
            for dx, dy in N8:
                u, v = x + dx, y + dy
                if 0 <= u < W and 0 <= v < H and op[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    stack.append((u, v))
        if len(comp) <= max_size and not stack:
            out.update(comp)
    return out


def twin_check(src, wk):
    """The twin rule: the puppet frame has exactly its source's silhouette, and every black pixel on
    the source's silhouette edge is still black. Also counts the source's interior black pixels that
    were recoloured (only eye glow is expected to do that)."""
    op_src = src[:, :, 3] > 0
    op_out = wk.key != ''
    sil = [(int(x), int(y)) for (y, x) in zip(*np.nonzero(op_src != op_out))]
    blk = op_src & (src[:, :, 0] == 0) & (src[:, :, 1] == 0) & (src[:, :, 2] == 0)
    air = np.pad(~op_src, 1, constant_values=True)
    edge = op_src & (air[:-2, 1:-1] | air[2:, 1:-1] | air[1:-1, :-2] | air[1:-1, 2:])
    lost_edge = [(int(x), int(y)) for (y, x) in zip(*np.nonzero(blk & edge & (wk.key != 'K')))]
    inner_black_recoloured = int((blk & ~edge & (wk.key != 'K')).sum())
    return {'silhouette': sil, 'edge_black_lost': lost_edge, 'inner_black_recoloured': inner_black_recoloured}


def stats_img(im):
    a = np.array(im.convert('RGBA'))
    op = a[:, :, 3] > 0
    semi = int(((a[:, :, 3] > 0) & (a[:, :, 3] < 255)).sum())
    cols = {tuple(c) for c in a[op].tolist()}
    black = int((op & (a[:, :, 0] == 0) & (a[:, :, 1] == 0) & (a[:, :, 2] == 0)).sum())
    return {'opaque': int(op.sum()), 'colours': len(cols), 'black': black / max(1, int(op.sum())), 'semi': semi}


# ------------------------------------------------------------------ the whole treatment

def treat(boss, src, take='A', key_src=None, sheet_rel=None, frame_no=None, report=None, skip_rings=()):
    """Treat one source frame (numpy RGBA) of `boss` (a jp_bosses.Boss). `key_src` is the boss's key
    frame (its idle) the parts are tracked from. Returns (PIL image, info dict)."""
    info = {'sheet': sheet_rel, 'frame': frame_no, 'take': take, 'parts': {}, 'skipped': [],
            'hooks': {}, 'unknown': {}}
    key_src = boss.key_frame() if key_src is None else key_src
    wk, unknown = recolour(src, boss.table_for(sheet_rel), boss.fallback)
    info['unknown'] = unknown
    # 2. track (a sheet's own data can pin a part's offset on a frame: hand-set, never guessed)
    fd = getattr(boss, 'frame_data', {}).get((sheet_rel or '').replace(chr(92), '/'), {})
    pinned = fd.get('parts', {}).get(frame_no, {})
    offs = {}
    for name, part in boss.parts.items():
        if name in pinned:
            offs[name] = pinned[name]
            info['parts'][name] = (pinned[name][0] if pinned[name] else 0, pinned[name][1] if pinned[name] else 0,
                                   'set by hand', pinned[name] is not None)
            continue
        dx, dy, sc = track(key_src, part['box'], src, radius=part.get('radius', 10))
        found = sc >= part.get('min', 0.6)
        offs[name] = (dx, dy) if found else None
        info['parts'][name] = (dx, dy, round(sc, 3), found)
    # 2b. regions: a prop drawn in a colour the body also uses (Captain Burak's brass flintlock shares
    # the coat's gold braid) gets its own mapping inside boxes that ride a tracked part
    for rg in getattr(boss, 'regions', []):
        # a sheet can give the prop's boxes in its own frame coordinates (the gun holstered, aimed...),
        # for the whole sheet (a list) or frame by frame (a dict; a frame it leaves out is tracked)
        sheet_boxes = fd.get('regions', {}).get(rg['name'])
        if isinstance(sheet_boxes, dict):
            sheet_boxes = sheet_boxes.get(frame_no)
        if sheet_boxes is None and not rg['boxes']:
            continue                     # a region that only exists where a sheet places it by hand
        o = (0, 0) if sheet_boxes is not None else offs.get(rg['part'])
        if o is None:
            info['skipped'].append('region:' + rg['name'])
            continue
        for (x0, y0, x1, y1) in (sheet_boxes if sheet_boxes is not None else rg['boxes']):
            for y in range(max(0, y0 + o[1]), min(wk.h, y1 + o[1] + 1)):
                for x in range(max(0, x0 + o[0]), min(wk.w, x1 + o[0] + 1)):
                    if src[y, x, 3] == 0:
                        continue
                    got = rg['table'].get(hexof(src[y, x]))
                    if got:
                        wk.mat[y, x], wk.key[y, x] = got
    # 2c. keep regions: someone else drawn into the frame (the player in Eric's bear hug) keeps his own
    # pixels exactly - inside the sheet's boxes for that frame, every pixel of one of his colours
    kept = set()
    kp = fd.get('keep', {}).get(frame_no)
    if kp:
        cols = {c.upper() for c in kp['colours']}
        for (x0, y0, x1, y1) in kp['boxes']:
            for y in range(max(0, y0), min(wk.h, y1 + 1)):
                for x in range(max(0, x0), min(wk.w, x1 + 1)):
                    if src[y, x, 3] == 0:
                        continue
                    hx = hexof(src[y, x])
                    if hx in cols and (x, y) not in kept:
                        wk.key[y, x], wk.mat[y, x] = KEEP, 'keep'
                        kept.add((x, y))
                        if hx in unknown:
                            unknown[hx] -= 1
                            if not unknown[hx]:
                                del unknown[hx]
        info['kept'] = len(kept)
    # 3. tatter (before the overlays, so a hook or a wound is never cut)
    for t in boss.tatter:
        o = offs.get(t.get('part', 'torso'))
        cx = t['centre_x'] + (o[0] if o else 0)
        dy = o[1] if o else 0
        dx = o[0] if o else 0
        info.setdefault('tatter', []).append(tatter(
            wk, t['mats'], cx, seed=t.get('seed', 7), max_depth=t.get('depth', 3), keep=t.get('keep', 3),
            rows=None if t.get('rows') is None else (t['rows'][0] + dy, t['rows'][1] + dy),
            cols=None if t.get('cols') is None else (t['cols'][0] + dx, t['cols'][1] + dx),
            inner=t.get('inner', False), spacing=t.get('spacing', (3, 7)), depths=t.get('depths', (1, 2, 2, 3, 3))))
    # 4. overlays (in order: the data lists them bottom to top)
    for ov in boss.overlays:
        o = offs.get(ov['part'])
        if o is None:
            info['skipped'].append(ov['name'])
            continue
        paint(wk, ov['px'], o[0], o[1], on=ov.get('on'), off=ov.get('off'), tag=ov['name'])
    # 4b. a sheet's own hand-drawn touches for one frame (a squashed face the idle's overlay cannot fit)
    for ov in fd.get('overlays', {}).get(frame_no, []):
        paint(wk, ov['px'], 0, 0, on=ov.get('on'), off=ov.get('off'), tag=ov['name'] + ' (by hand)')
    # 5. hooks: tracked on their part, else on a fallback part (the key-frame offset carried over and
    # the point pulled inside the silhouette), else placed by hand for that frame, else not placed
    by_hand = fd.get('hooks', {}).get(frame_no, {})
    for name, hk in boss.hooks.items():
        stamp = hk.get('stamp')
        if name in by_hand:
            placed = by_hand[name]
            if placed is None:
                info['skipped'].append('hook:' + name)
                continue
            (x, y), stamp = placed[0], placed[1]
            info.setdefault('hook_how', {})[name] = 'by hand'
        else:
            o = offs.get(hk['part'])
            how = 'tracked'
            if o is None:
                for fb in hk.get('fallback', ()):
                    if offs.get(fb) is not None:
                        o, how = offs[fb], 'via ' + fb
                        break
            if o is None:
                info['skipped'].append('hook:' + name)
                continue
            x, y = hk['at'][0] + o[0], hk['at'][1] + o[1]
            if not stamp and not wk.opaque(x, y):
                near = sorted(((dx * dx + dy * dy, dx, dy) for dy in range(-6, 7) for dx in range(-6, 7)
                               if wk.opaque(x + dx, y + dy)))
                if not near:
                    info['skipped'].append('hook:' + name)
                    continue
                x, y = x + near[0][1], y + near[0][2]
            info.setdefault('hook_how', {})[name] = how
        if stamp and name in skip_rings:
            stamp = None                       # the point is still recorded; the ring is not drawn
            info.setdefault('rings_left_off', []).append(name)
        if stamp:
            hk = dict(hk, stamp=stamp)
            # a ring must sit wholly inside the silhouette (the twin rule): where the tracked point
            # leaves part of it over air, snap it to the nearest spot within 2 texels where it fits
            fits = lambda cx, cy: all(wk.opaque(cx + sx, cy + sy) for (sx, sy) in hk['stamp'])
            if not fits(x, y):
                near = sorted(((dx * dx + dy * dy, dx, dy) for dy in range(-2, 3) for dx in range(-2, 3)
                               if (dx or dy) and fits(x + dx, y + dy)))
                if near:
                    x, y = x + near[0][1], y + near[0][2]
                    info.setdefault('nudged', []).append(name)
            st = {(x + sx, y + sy): ch for (sx, sy), ch in hk['stamp'].items()}
            _n, dropped = paint(wk, st, 0, 0, tag='rings')
            info.setdefault('rings_drawn', []).append(name)
            if dropped:
                info.setdefault('clipped', []).append('%s ring: %d px off the silhouette' % (name, dropped))
        info['hooks'][name] = (x, y)
    # 6. keyline: one pure-black silhouette line (an effect's lone floating motes keep their colour)
    n = unify_keyline(wk, keep_fx=set(boss.fx_specks) | source_lone(src) | kept)
    info['keyline_unified'] = n
    # 7. lint
    info['lint'] = lint(wk, fx=set(boss.fx_specks) | kept)
    info['lint'].update(twin_check(src, wk))
    info['unblack'] = dict(wk.unblack)
    # pinholes the source itself has (a torn cape's gaps) stay, by the twin rule: only new ones count
    kept = source_holes(src)
    info['lint']['source_holes_kept'] = len(kept & set(info['lint']['holes']))
    info['lint']['holes'] = [h for h in info['lint']['holes'] if h not in kept]
    motes = source_lone(src)
    info['lint']['source_specks_kept'] = len(motes & set(info['lint']['lone']))
    info['lint']['lone'] = [p for p in info['lint']['lone'] if p not in motes]
    info['lint']['gaps'] = [g for g in info['lint']['gaps'] if g not in motes]
    im = wk.image(take)
    info['stats'] = stats_img(im)
    info['work'] = wk
    return im, info


# ------------------------------------------------------------------ previews

BG = (46, 49, 58, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im.convert('RGBA'))
    return base.resize((im.width * s, im.height * s), Image.NEAREST)
