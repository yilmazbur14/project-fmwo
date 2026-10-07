"""Checks every Flyby frame against the art contract's HARD numbers (the plan's section 13):

  1. frames are 192x160
  2. the lead exit holds one column on every frame (glide and breath); its row bobs at most +-2 and
     every exit sits in rows 78-112
  3. at rows >= 86 nothing is drawn right of the lead exit's column
  4. nothing is drawn below row 157
  5. fire drawn in the frame stays inside the curtain band (the 32 columns up to and including the lead
     exit) and below the exits
  6. the glide and breath wingbeats match frame for frame (everything that isn't jaw, tongue or fire is
     pixel-identical between glide frame i and breath frame i)
  7. palette: pure #000000 keyline, no semi-alpha, colour count and black share (reported)

run(frames) takes {'glide': [...], 'breath': [...]} lists of dicts with 'image', 'exits' (lead first),
'fire' (the set of fire pixels) and 'head_mask' (pixels that may differ between the clips), and returns
(ok, report_lines, numbers).
"""
import fb_common  # noqa: F401  (puts the rig on sys.path, read-only)
from collections import Counter

from fb_common import CURTAIN_TEXELS, EXIT_ROWS, FH, FLOOR_ROW, FW, LOWEST_ROW


def opaque(im):
    w, h = im.size
    px = im.load()
    return {(x, y) for y in range(h) for x in range(w) if px[x, y][3] > 0}


def palette_numbers(images):
    cnt = Counter()
    semi = 0
    for im in images:
        for c in (im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()):
            if c[3] > 0:
                cnt[c] += 1
                if c[3] < 255:
                    semi += 1
    total = sum(cnt.values())
    black = cnt.get((0, 0, 0, 255), 0)
    return dict(opaque=total, colours=len(cnt), black_pct=round(100.0 * black / max(1, total), 2), semi=semi)


def run(frames):
    lines = []
    ok = True

    def bad(msg):
        nonlocal ok
        ok = False
        lines.append('FAIL ' + msg)

    lead_cols = set()
    lead_rows = []
    for clip in ('glide', 'breath'):
        for i, f in enumerate(frames[clip]):
            im = f['image']
            if im.size != (FW, FH):
                bad('%s %d is %s, not 192x160' % (clip, i, im.size))
            px = opaque(im)
            lx, ly = f['exits'][0]
            lead_cols.add(lx)
            lead_rows.append(ly)
            for (ex, ey) in f['exits']:
                if not (EXIT_ROWS[0] <= ey <= EXIT_ROWS[1]):
                    bad('%s %d exit %s outside rows %d-%d' % (clip, i, (ex, ey), EXIT_ROWS[0], EXIT_ROWS[1]))
            ahead = sorted(q for q in px if q[1] >= FLOOR_ROW and q[0] > lx)
            if ahead:
                bad('%s %d: %d texels right of the lead exit column %d at rows >= %d, e.g. %s'
                    % (clip, i, len(ahead), lx, FLOOR_ROW, ahead[:4]))
            low = sorted(q for q in px if q[1] > LOWEST_ROW)
            if low:
                bad('%s %d: %d texels below row %d, e.g. %s' % (clip, i, len(low), LOWEST_ROW, low[:4]))
            fire = f.get('fire', set())
            band0 = lx - (CURTAIN_TEXELS - 1)
            out_band = [q for q in fire if q[0] < band0 or q[0] > lx]
            if out_band:
                bad('%s %d: %d fire texels outside the curtain band %d-%d' % (clip, i, len(out_band), band0, lx))
            min_exit_row = min(ey for (ex, ey) in f['exits'])
            above = [q for q in fire if q[1] < min_exit_row]
            if above:
                bad('%s %d: %d fire texels above the highest exit (row %d)' % (clip, i, len(above), min_exit_row))
            lines.append('%-6s %d  lead exit %s  exits %s  bbox %s' % (
                clip, i, (lx, ly), [(round(x, 1), round(y, 1)) for (x, y) in f['exits'][1:]],
                (min(x for x, y in px), min(y for x, y in px), max(x for x, y in px), max(y for x, y in px))))
    if len(lead_cols) != 1:
        bad('the lead exit column moves: %s' % sorted(lead_cols))
    if lead_rows and max(lead_rows) - min(lead_rows) > 4:
        bad('the lead exit row bobs more than +-2: %s' % lead_rows)
    # the wingbeats match: outside the head/fire mask, glide i == breath i pixel for pixel
    for i, (g, b) in enumerate(zip(frames['glide'], frames['breath'])):
        mask = g.get('head_mask', set()) | b.get('head_mask', set()) | b.get('fire', set())
        gp, bp = g['image'].load(), b['image'].load()
        diff = [(x, y) for y in range(FH) for x in range(FW) if (x, y) not in mask and gp[x, y] != bp[x, y]]
        if diff:
            bad('glide %d and breath %d differ outside the heads and fire at %d texels, e.g. %s'
                % (i, i, len(diff), diff[:4]))
    nums = palette_numbers([f['image'] for clip in ('glide', 'breath') for f in frames[clip]])
    if nums['semi']:
        bad('%d semi-alpha texels' % nums['semi'])
    lines.append('palette: %(opaque)d opaque, %(colours)d colours, %(black_pct).2f%% black, %(semi)d semi' % nums)
    return ok, lines, nums
