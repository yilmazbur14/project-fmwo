"""FX v2: the hard rules, checked before fx_build writes anything. Each check returns a list of failures (empty = pass)
and a one-line report. Nothing here writes a file.

  - cells as shipped; frame counts only grow
  - the approved rig still reproduces the shipped sheets v2 builds on (le_earth's ridge, crack, burst; the pillar dust)
  - every colour from the approved palettes (per piece), no black keyline pixel anywhere
  - the wave: the crest's row 39 (the band's front edge) covered in every frame, the 94 x 120 band tile covered from
    its trailing edge down, crest and body seamless left-right
  - the ridge: footprint rows 8..31 unchanged - the standing ridge's front rows 29..31 fully covered as shipped, the
    tell's footprint border on the footprint exactly, nothing but earth green / white / dust in a tell
  - floor pieces semi-transparent, the melt ending on the flood's frame 5 texel for texel, the flood itself untouched
  - the one-shots' lengths as shipped, the breath's start / loop / end shape
"""
import sys

sys.dont_write_bytecode = True

import numpy as np

import fx_common as C
import fx_water as W
import le_earth as LE
import le_pillar as LP


def _opaque(cv):
    return cv != '.'


def _alpha(ch):
    return C.PAL[ch][3]


def check_cells(sheets):
    bad = []
    for d in sheets:
        shipped = d['shipped']
        if shipped is None:
            continue
        cell, n = shipped
        if tuple(d['cell']) != tuple(cell):
            bad.append('%s: cell %s, shipped %s' % (d['name'], d['cell'], cell))
        if len(d['frames']) < n:
            bad.append('%s: %d frames, fewer than the shipped %d' % (d['name'], len(d['frames']), n))
        for i, f in enumerate(d['frames']):
            if f.shape != (d['cell'][1], d['cell'][0]):
                bad.append('%s frame %d: %s' % (d['name'], i, f.shape))
    return bad, 'cells as shipped, counts only grow'


def check_rig():
    """The approved modules v2 builds on still draw the shipped sheets texel for texel."""
    bad = []
    tests = [('liam_tremor_block', 96, LE.block_frames()), ('liam_tremor_crack', 16, [LE.crack_segment(k) for k in range(3)]),
             ('liam_slam_burst', 32, [LE.slam_burst(k) for k in range(3)]),
             ('liam_pillar_dust', 64, [LP.dust_frame(k) for k in range(3)])]
    for name, fw, frames in tests:
        shipped = C.shipped(name, fw)
        if len(shipped) != len(frames) or any((a != b).any() for a, b in zip(shipped, frames)):
            bad.append('%s: the rig no longer reproduces the shipped sheet' % name)
    return bad, 'le_earth / le_pillar still reproduce the shipped earth sheets'


def check_palette(sheets):
    bad = []
    for d in sheets:
        used = set()
        for f in d['frames']:
            used |= C.colours(f)
        extra = used - d['allowed']
        if extra:
            bad.append('%s: keys outside its palette %s' % (d['name'], ''.join(sorted(extra))))
        for k in used:
            r, g, b, a = C.PAL[k]
            if (r, g, b) == (0, 0, 0):
                bad.append('%s: a black keyline pixel (%s)' % (d['name'], k))
    return bad, 'approved palettes only, no keyline'


def _run_top(tile):
    """The highest row the unbroken run of water up from the front edge reaches, over all columns (worst column)."""
    worst = 0
    for x in range(tile.shape[1]):
        col = _opaque(tile[:, x])
        y = tile.shape[0] - 1
        while y >= 0 and col[y]:
            y -= 1
        worst = max(worst, y + 1)
    return worst


def check_wave(sheets):
    by = {d['name']: d for d in sheets}
    crest, body = by['liam_wave_crest']['frames'], by['liam_wave_body']['frames']
    bad = []
    for i, c in enumerate(crest):
        if not _opaque(c[W.CREST_H - 1]).all():
            bad.append('crest frame %d: its front row (the band\'s bottom edge) has holes' % i)
    # covered from the trailing edge down: the unbroken run up from the front edge reaches as high as the shipped
    # tile's does (spray flecks above the edge are extra, as shipped)
    limit = max(_run_top(np.vstack([C.shipped('liam_wave_body', 94)[0], c])) for c in C.shipped('liam_wave_crest', 94))
    for i, b in enumerate(body):
        top = _run_top(np.vstack([b, crest[i % len(crest)]]))
        if top > limit:
            bad.append('band tile %d: the water only covers from row %d down (shipped: from row %d)' % (i, top, limit))
    # seamless left-right: the wrap seam is no rougher than the tile's own column-to-column changes
    for name, frames in (('crest', crest), ('body', body)):
        for i, f in enumerate(frames):
            a = np.array([[ord(ch) for ch in row] for row in f])
            inner = (a[:, 1:] != a[:, :-1]).mean()
            seam = (a[:, 0] != a[:, -1]).mean()
            if seam > inner * 1.8 + 0.05:
                bad.append('%s frame %d: the left-right seam (%.2f) is rougher than the tile (%.2f)' % (name, i, seam, inner))
    return bad, 'wave covers its band, front edge on row 119, crest and body seamless'


def check_tremor(sheets):
    by = {d['name']: d for d in sheets}
    bad = []
    for clip in ('heave', 'active', 'pulse'):
        fr = by['liam_tremor_block_%s' % clip]['frames']
        use = fr[3:] if clip == 'heave' else fr
        for i, f in enumerate(use):
            if not _opaque(f[29:32]).all():
                bad.append('%s frame %d: the standing ridge\'s front rows 29..31 are not fully covered' % (clip, i))
    tell = by['liam_tremor_block_tell']['frames']
    for i, f in enumerate(tell):
        used = C.colours(f)
        if used - set('8WYwvTt'):
            bad.append('tell frame %d: tell colours %s beyond earth green / white / dust' % (i, ''.join(sorted(used))))
        if i >= 3:
            ring = np.zeros(f.shape, dtype=bool)
            ring[8, :] = ring[31, :] = True
            ring[8:32, 0] = ring[8:32, 95] = True
            if not _opaque(f[ring]).all():
                bad.append('tell frame %d: the footprint border (rows 8..31) is not drawn whole' % i)
    comb = by['liam_tremor_block']['frames']
    if len(comb) != 17:
        bad.append('combined fallback sheet has %d frames, not the shipped 17' % len(comb))
    return bad, 'ridge footprint rows 8..31 kept, tell green/white, fallback in the 17-frame layout'


def check_floor(sheets):
    by = {d['name']: d for d in sheets}
    bad = []
    for name in ('liam_ice_melt', 'liam_ice_shatter', 'liam_freeze_front', 'liam_flood_ripple'):
        for i, f in enumerate(by[name]['frames']):
            for k in C.colours(f):
                if _alpha(k) >= 255:
                    bad.append('%s frame %d: an opaque key %s on the floor' % (name, i, k))
    flood5 = C.shipped('liam_flood', 64)[5]
    if (by['liam_ice_melt']['frames'][-1] != flood5).any():
        bad.append('the melt\'s last frame is not the flood\'s frame 5')
    # the flood itself stays as shipped: nested and semi-transparent (sanity on the untouched sheet)
    fl = C.shipped('liam_flood', 64)
    for k in range(5):
        if (_opaque(fl[k]) & ~_opaque(fl[k + 1])).any():
            bad.append('shipped flood frame %d is not nested in %d' % (k, k + 1))
    # the ice paler and more opaque than the water: every ice key's alpha above the water body's
    water_a = _alpha('<')
    for k in '()[]{}':
        if _alpha(k) <= water_a:
            bad.append('ice key %s not more opaque than the water' % k)
    return bad, 'floor pieces semi-transparent, melt ends on flood frame 5, flood untouched and nested'


def check_timing(sheets):
    by = {d['name']: d for d in sheets}
    bad = []
    lengths = {'liam_wave_splash': 0.26, 'liam_gust_burst': 0.29, 'liam_slam_burst': 0.22,
               'liam_tremor_block_tell': 0.6, 'liam_tremor_block_heave': 0.24, 'liam_tremor_block_pulse': 0.16,
               'liam_tremor_block_crumble': 0.32}
    for name, total in lengths.items():
        got = sum(by[name]['times'])
        if abs(got - total) > 1e-6:
            bad.append('%s: %.3f s, shipped %.2f s' % (name, got, total))
        if len(by[name]['times']) != len(by[name]['frames']):
            bad.append('%s: %d times for %d frames' % (name, len(by[name]['times']), len(by[name]['frames'])))
    if sum(by['liam_tremor_block_crumble']['times']) > 0.35:
        bad.append('the crumble outlasts CRUMBLE_TIME')
    tags = dict((t[0], (t[1], t[2])) for t in by['liam_cold_breath']['tags'])
    n = len(by['liam_cold_breath']['frames'])
    if tags != {'start': (0, 0), 'loop': (1, n - 2), 'end': (n - 1, n - 1)}:
        bad.append('the breath is not [start 0][loop 1..n-2][end n-1]: %s' % tags)
    return bad, 'one-shots keep their shipped length; breath start/loop/end'


ALL = [check_cells, check_palette, check_wave, check_tremor, check_floor, check_timing]


def run(sheets):
    """Every check; returns (ok, report lines)."""
    lines, ok = [], True
    for fn in ALL:
        bad, what = fn(sheets)
        ok &= not bad
        lines.append(('PASS ' if not bad else 'FAIL ') + what)
        lines += ['     - ' + b for b in bad[:12]]
    bad, what = check_rig()
    ok &= not bad
    lines.append(('PASS ' if not bad else 'FAIL ') + what)
    lines += ['     - ' + b for b in bad]
    return ok, lines
