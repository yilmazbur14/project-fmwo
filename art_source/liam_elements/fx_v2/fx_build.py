"""FX v2 BUILD (approval pass, 2026-09-29): Liam's attack 1-2 elemental FX redrawn with more frames - the wave's rolling
barrels, spray and churning foam, the tell, collapse and splash; the gust, its trail and the cold breath; NEW the
downdraft; the freeze front, shatter and melt; the tremor ridge, crack, slam burst and pillar dust. NOTHING HERE SHIPS:
the sheets reach Assets/ only after the user approves them, copied by the coordinator.

  python fx_build.py            prints this and writes nothing
  python fx_build.py --write    writes into art_source/liam_elements/fx_v2/ ONLY

--write installs an audit hook before anything else runs. It refuses any file write, rename, removal or directory
creation outside fx_v2/ (its own .build_tmp/ scratch included, removed at the end), anything under Assets/, and any
process but Aseprite (whose arguments may not name Assets/). The hard-rule checks (fx_checks) run first and a failure
writes nothing. Every sheet is written as .png + .aseprite, the .aseprite exported back and checked pixel-exact against
the .png (art_source/imgdiff.py) before either is copied in.

Writes: the sheets (fx_v2/liam_*.png + .aseprite), contract.json, gifs/ab_*.gif (before/after at game scale on the real
mat), mocks/mock_*.png (in-fight), liam_fx_v2_contact.png.
Reads: approval/ (the shipped sheets, sha256-identical to Assets), the le_*.py rig (read only), the arena captures in
FX_V2_CAP (default: the session scratchpad's liam_elements/cap/).
"""
import sys

sys.dont_write_bytecode = True

import os                                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
TMP = os.path.join(HERE, '.build_tmp')

LUA = r'''
local src = app.params["src"]
local out = app.params["out"]
local n = tonumber(app.params["n"])
local fw = tonumber(app.params["fw"])
local durs = {}
for d in string.gmatch(app.params["durs"], "[^,]+") do table.insert(durs, tonumber(d)) end
local strip = Image{ fromFile = src }
local fh = strip.height
local spr = Sprite(fw, fh, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = app.params["layer"]
for i = 1, n do
  if i > 1 then spr:newEmptyFrame() end
  local img = Image(fw, fh, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0), 255, BlendMode.SRC)
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = durs[((i - 1) % #durs) + 1]
end
for t in string.gmatch(app.params["tags"], "[^;]+") do
  local name, a, b = string.match(t, "([^:]+):(%d+):(%d+)")
  local tag = spr:newTag(tonumber(a), tonumber(b))
  tag.name = name
end
spr:saveAs(out)
'''


# ------------------------------------------------------------------ the guard
def install_guard():
    root = os.path.normcase(os.path.realpath(HERE))
    project = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
    assets = os.path.normcase(os.path.realpath(os.path.join(project, 'Assets')))
    ase = os.path.normcase(os.path.realpath(ASEPRITE))

    def inside(p):
        rp = os.path.normcase(os.path.realpath(os.fsdecode(p) if isinstance(p, bytes) else os.fspath(p)))
        if rp == assets or rp.startswith(assets + os.sep):
            return False
        return rp == root or rp.startswith(root + os.sep)

    def hook(event, args):
        if event == 'open':
            path, mode, flags = args
            if path is None or isinstance(path, int):
                return
            writing = (mode is not None and any(c in str(mode) for c in 'wax+')) or \
                      (mode is None and isinstance(flags, int) and
                       flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
            if writing and not inside(path):
                raise PermissionError('guard: fx_build writes only into %s, not %s' % (HERE, path))
        elif event in ('os.remove', 'os.unlink', 'os.rename', 'os.replace', 'os.rmdir', 'os.mkdir', 'os.truncate',
                       'os.chmod', 'os.symlink', 'os.link', 'shutil.copyfile', 'shutil.copytree', 'shutil.move',
                       'shutil.rmtree', 'shutil.copymode', 'shutil.copystat'):
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and not inside(a):
                    raise PermissionError('guard: refusing %s on %s' % (event, a))
        elif event in ('os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.spawn'):
            raise PermissionError('guard: refusing %s' % event)
        elif event == 'subprocess.Popen':
            import subprocess
            argv = args[1]
            parts = [argv] if isinstance(argv, (str, bytes)) else [os.fspath(a) for a in argv]
            line = parts[0] if len(parts) == 1 else subprocess.list2cmdline(parts)
            first = parts[0] if len(parts) > 1 else (line[1:line.index('"', 1)] if line.startswith('"')
                                                     else line.split(' ')[0])
            if os.path.normcase(os.path.realpath(first)) != ase:
                raise PermissionError('guard: fx_build launches only Aseprite, not %s' % first)
            low = os.path.normcase(line)
            if assets in low or (os.sep + 'assets' + os.sep) in low:
                raise PermissionError('guard: an Aseprite argument under Assets')

    sys.addaudithook(hook)


# ------------------------------------------------------------------ sheets
def strip(frames):
    import fx_common as C
    from PIL import Image
    fh, fw = frames[0].shape
    out = Image.new('RGBA', (fw * len(frames), fh), (0, 0, 0, 0))
    for i, cv in enumerate(frames):
        assert cv.shape == (fh, fw), (cv.shape, (fh, fw))
        out.paste(Image.fromarray(C.rgba(cv), 'RGBA'), (i * fw, 0))
    return out


def write_sheet(d):
    import shutil
    import subprocess
    from PIL import Image
    from imgdiff import pixel_diff
    name = d['name']
    im = strip(d['frames'])
    n = len(d['frames'])
    fw = d['cell'][0]
    tpng = os.path.join(TMP, name + '.png')
    tase = os.path.join(TMP, name + '.aseprite')
    im.save(tpng)
    lua = os.path.join(TMP, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LUA)
    tags = ';'.join('%s:%d:%d' % (t, a + 1, b + 1) for (t, a, b) in d['tags'])
    subprocess.run([ASEPRITE, '-b', '--script-param', 'src=' + tpng, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % n, '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % max(1, round(t * 1000)) for t in d['times']),
                    '--script-param', 'layer=' + d['layer'], '--script-param', 'tags=' + tags,
                    '--script', lua], check=True, capture_output=True)
    back = os.path.join(TMP, name + '_rt.png')
    subprocess.run([ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    diff = pixel_diff(Image.open(tpng), Image.open(back))
    if diff:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, diff))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        shutil.copyfile(src, os.path.join(HERE, name + ext))
    return im


# ------------------------------------------------------------------ contract.json
def contract(sheets, check_lines, files):
    import fx_water as W
    import fx_air as A
    import fx_earth as E
    by = {d['name']: d for d in sheets}

    def times(name):
        return [round(t, 4) for t in by[name]['times']]

    entries = {}
    for d in sheets:
        e = {'file': d['name'] + '.png', 'cell': list(d['cell']), 'frames': len(d['frames']),
             'shipped_frames': d['shipped'][1] if d['shipped'] else None, 'pivot': list(d['pivot']) if d['pivot'] else None,
             'play': d['play'], 'times': times(d['name']), 'length_s': round(sum(d['times']), 4),
             'tags': {t: [a, b] for (t, a, b) in d['tags']}, 'palette': ''.join(sorted(d['allowed'])),
             'code': d['code'], 'notes': d['notes']}
        entries[d['name']] = e
    clips = {}
    for c in E.CLIPS:
        d = by['liam_tremor_block_%s' % c]
        clips[c] = {'file': d['name'] + '.png', 'frames': list(range(len(d['frames']))), 'times': times(d['name']),
                    'loop': c == 'active', 'length_s': round(sum(d['times']), 4)}
    return {
        'note': 'FX v2 APPROVAL PASS (2026-09-29). Not approved yet: nothing ships until the user approves. Texels at '
                'SCALE 3. Every cell, pivot, band and footprint is as shipped (approval/anchors.json); only frame '
                'counts grew and times changed. Built by fx_build.py from fx_*.py; the checks below all passed.',
        'hooks_reference': 'addendum 3 E.1/E.2 (frame counts off each sheet\'s width; one-shots keep their shipped '
                           'length, spread over the frames; loops keep their frame time unless set here; breath = frame '
                           '0 once, loop 1..n-2, end n-1; the ridge as per-clip strips). Copy only the times and the '
                           'new sheet names below into LiamArtLayout.',
        'layout_constants': {
            'WAVE_FRAME_TIME': W.FRAME_TIME,
            'WAVE_CREST_FRAMES (off the sheet)': W.NF,
            'WAVE_SPLASH_TIMES': times('liam_wave_splash'),
            'GUST_BURST_TIMES': times('liam_gust_burst'),
            'GUST_TRAIL_FRAME_TIME': A.TRAIL_TIME,
            'BREATH_FRAME_TIME': A.BREATH_TIME,
            'FROST_FRAME_TIME': by['liam_freeze_front']['times'][0],
            'TREMOR_CRACK_FRAME_TIME': E.CRACK_TIME,
            'SLAM_BURST_TIMES': times('liam_slam_burst'),
            'PILLAR_DUST_FRAME_TIME': E.DUST_TIME,
            'DOWNDRAFT_SHEET': 'liam_downdraft.png',
            'DOWNDRAFT_FRAME': [A.DRAFT_W, A.DRAFT_H],
            'DOWNDRAFT_PIVOT': list(A.DRAFT_PIVOT),
            'DOWNDRAFT_FRAME_TIME': A.DRAFT_TIME,
            'TREMOR_CLIPS (per-clip strips liam_tremor_block_<clip>.png)': clips,
        },
        'phase_maps': {
            'liam_tremor_block_<clip>.png (per-clip strips, preferred)': {
                c: {'file': clips[c]['file'], 'frames': '0-%d' % (len(clips[c]['frames']) - 1),
                    'length_s': clips[c]['length_s'], 'loop': clips[c]['loop']} for c in E.CLIPS},
            'liam_tremor_block.png (combined fallback, the shipped layout)': {
                'tell': [0, 3], 'heave': [4, 6], 'active': [7, 10], 'pulse': [11, 12], 'crumble': [13, 16],
                'cut_from_clips': {c: E.COMBINED_PICK[c] for c in E.CLIPS}},
            'liam_cold_breath': {'start': [0, 0], 'loop': [1, A.BREATH_FRAMES - 2],
                                 'end': [A.BREATH_FRAMES - 1, A.BREATH_FRAMES - 1]},
            'liam_wave_tell': {'rise': [0, W.TELL_RISE - 1], 'tremble': [W.TELL_RISE, W.TELL_FRAMES - 1]},
            'liam_wave_collapse': 'spread over wave_collapse_time: 0 cave-in + spray crown, 1 tower, 2 tear, 3-4 rain '
                                  '+ rings, 5-7 last foam',
            'liam_ice_melt': 'spread over melt_time; frame 5 = liam_flood frame 5',
            'liam_ice_shatter': 'spread over SHATTER_TIME: 0 cracks, 1 plates, 2 heave, 3 part, 4 break, 5-7 shards',
        },
        'downdraft': {
            'sheet': 'liam_downdraft.png', 'frame': [A.DRAFT_W, A.DRAFT_H], 'pivot': list(A.DRAFT_PIVOT),
            'frames': A.DRAFT_FRAMES, 'frame_time': A.DRAFT_TIME, 'play': 'loop in place; start each streak on a '
            'random frame', 'layer': 'FxLayer',
            'spawn': 'every 0.03 s at a random x on the row line (y 348), falling at downdraft_speed x 1.5 (1800 px/s) '
                     '(addendum 3 E.2.7)',
            'fade': 'suggested: full for the first 35% of its fall, then to 0 by the time its head (80 texels under '
                    'its tail pivot) reaches the bottom rope (tail at y 729); the GIF and mocks do exactly this',
            'window': 'from _breathe() to _heave() / interrupt(), as addendum 3 plans',
        },
        'code_hooks': [
            {'hook': 'frame counts off the sheets, one-shot times spread, breath start/loop/end, per-clip ridge strips, '
                     'the downdraft', 'status': 'addendum 3 step 1 (being built)'},
            {'hook': 'the times in layout_constants', 'status': 'copy when this is approved'},
            {'hook': 'wave body shimmer: step the body tiles\' region x by frame*94 on the crest\'s frame',
             'status': 'OPTIONAL, not planned; without it the body is frame 0, a drop-in static body'},
            {'hook': 'flood ripple overlay: liam_flood_ripple.png tiled as a child of water_sheet with '
                     'clip_children = CLIP_CHILDREN_AND_DRAW, 12 frames at 0.1 s',
             'status': 'OPTIONAL, not planned; without it the flood is exactly as shipped'},
            {'hook': 'wave tell: after one pass, loop frames %d-%d only' % (W.TELL_RISE, W.TELL_FRAMES - 1),
             'status': 'OPTIONAL; only matters if wave_tell is raised past 0.48 s'},
            {'hook': 'tremor crack: segment i shows frame (frame - i) mod n, so the spit travels out along the crack',
             'status': 'OPTIONAL'},
            {'hook': 'cold breath: play the end frame as the plume stops (the slam pose), then free it',
             'status': 'addendum 3 E.2.4 plays the last frame; confirm it plays on stop'},
        ],
        'unchanged': {'liam_flood.png': 'the six nested coverage frames, as shipped',
                      'liam_ice.png': 'as shipped (the melt and shatter start from it)',
                      'liam_wave_edge.png': 'not read by the code; untouched'},
        'sheets': entries,
        'checks': check_lines,
        'files': files,
    }


# ------------------------------------------------------------------ main
def main(argv):
    if argv != ['--write']:
        print(__doc__)
        return 2
    install_guard()
    import json
    import shutil
    import time
    t0 = time.time()
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))          # art_source (imgdiff)
    import fx_sheets as FS
    import fx_checks as K
    sheets = FS.all_sheets()
    ok, lines = K.run(sheets)
    print('\n'.join(lines))
    if not ok:
        raise SystemExit('checks failed: nothing written')
    import fx_scene as SC
    import fx_present as FP
    import fx_mocks as MK
    import fx_earth as E
    arena = SC.Arena()                       # fails here, before any write, if the captures are missing
    for d in (TMP, os.path.join(HERE, 'gifs'), os.path.join(HERE, 'mocks')):
        if not os.path.isdir(d):
            os.mkdir(d)
    files = []
    try:
        for d in sheets:
            im = write_sheet(d)
            files += [d['name'] + '.png', d['name'] + '.aseprite']
            print('wrote %-28s %4dx%-3d %2d frames' % (d['name'], im.width, im.height, len(d['frames'])))
    finally:
        if os.path.isdir(TMP):
            shutil.rmtree(TMP)
    nums = FS.gif_numbers(sheets)
    v2 = {d['name']: d['frames'] for d in sheets}
    v2['liam_tremor_block'] = E.block_frames()          # the GIFs and mocks play the per-clip strips in order
    P = FP.Pieces(v2, arena)
    for name, fn in FP.GIFS:
        frames, durs = fn(P, nums)
        FP.save_gif(frames, durs, os.path.join(HERE, 'gifs', name + '.gif'))
        files.append('gifs/%s.gif' % name)
        print('wrote gifs/%s.gif (%d frames)' % (name, len(frames)))
    for name, im in MK.build(P, nums):
        im.convert('RGB').save(os.path.join(HERE, 'mocks', name + '.png'))
        files.append('mocks/%s.png' % name)
        print('wrote mocks/%s.png' % name)
    FP.contact(sheets).save(os.path.join(HERE, 'liam_fx_v2_contact.png'))
    files.append('liam_fx_v2_contact.png')
    print('wrote liam_fx_v2_contact.png')
    with open(os.path.join(HERE, 'contract.json'), 'w') as f:
        json.dump(contract(sheets, lines, files + ['contract.json']), f, indent=1)
    print('wrote contract.json   (%.0f s)' % (time.time() - t0))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
