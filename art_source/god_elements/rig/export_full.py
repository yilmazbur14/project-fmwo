"""The FULL SET into the stage folder scratchpad/god_elements/full/ (guard.py refuses the project):

    full/Puppets/liam/*      -> Assets/Characters/Jordan/Puppets/liam/
    full/Puppets/bixby/*     -> Assets/Characters/Jordan/Puppets/bixby/
    full/Wheel/*             -> Assets/Characters/Jordan/Wheel/
    full/Scripts/JordanPuppetHooks.gd  (an ADDITIVE replacement of the live file) + hooks.diff
    full/manifest.json, full/numbers.json, full/contract.json, full/contact/*.png

Every PNG gets its .aseprite (frames, durations, tags), checked to export back pixel-identical.
"""
import json
import hashlib
import shutil
import subprocess
import tempfile
import difflib
from ge_common import *
import le_build as LB
from imgdiff import pixel_diff
import liam_full as LF
import liam_build as LBD
import bixby_full as BF
import bixby_bite as BB
import wheel2 as W2

STAGE = os.path.join(GE, 'full')
ASE = C.ASEPRITE
LIVE_HOOKS = PROJECT + '/Scripts/JordanPuppetHooks.gd'
DEST = {'liam': 'Assets/Characters/Jordan/Puppets/liam/', 'bixby': 'Assets/Characters/Jordan/Puppets/bixby/',
        'wheel': 'Assets/Characters/Jordan/Wheel/'}
SUBDIR = {'liam': 'Puppets/liam', 'bixby': 'Puppets/bixby', 'wheel': 'Wheel'}
TMP = None
RECORD = {'files': {}, 'sheets': {}}


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def numbers(a):
    s = stats(a)
    return {'black_pct': round(100 * s['black'], 1), 'colours': s['colours'], 'semi_alpha_px': s['semi'],
            'opaque_px': s['opaque']}


def save(group, name, frames, durs, tags, layer, meta):
    d = os.path.join(STAGE, SUBDIR[group])
    os.makedirs(d, exist_ok=True)
    a = strip(frames)
    png = os.path.join(d, name + '.png')
    Image.fromarray(a, 'RGBA').save(png)
    ase = os.path.join(d, name + '.aseprite')
    lua = os.path.join(TMP, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LB.LUA)
    fw = frames[0].shape[1]
    durs = (list(durs) * len(frames))[:len(frames)] if len(durs) < len(frames) else durs
    tg = ';'.join('%s:%d:%d' % (t, i + 1, j + 1) for (t, i, j) in tags)
    subprocess.run([ASE, '-b', '--script-param', 'src=' + png, '--script-param', 'out=' + ase,
                    '--script-param', 'n=%d' % len(frames), '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%d' % round(t * 1000) for t in durs),
                    '--script-param', 'layer=' + layer, '--script-param', 'tags=' + tg, '--script', lua],
                   check=True, capture_output=True)
    back = os.path.join(TMP, name + '_rt.png')
    subprocess.run([ASE, '-b', ase, '--sheet', back, '--sheet-type', 'horizontal'], check=True, capture_output=True)
    dd = pixel_diff(Image.open(png), Image.open(back))
    if dd:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, dd))
    for p in (png, ase):
        rel = os.path.relpath(p, STAGE).replace(os.sep, '/')
        RECORD['files'][rel] = {'sha256': sha(p), 'ship_to': DEST[group] + os.path.basename(p)}
    meta = dict(meta, frames=len(frames), frame=[fw, frames[0].shape[0]], numbers=[numbers(f) for f in frames])
    RECORD['sheets'][SUBDIR[group] + '/' + name] = meta
    return a


def live_numbers(rel, fw):
    a = np.array(Image.open(CHARS + '/' + rel).convert('RGBA'))
    n = a.shape[1] // fw
    return numbers(a), n


# ------------------------------------------------------------------ Liam
def export_liam():
    backs = {}
    channel0 = None
    for name, fn, times in LF.AVATAR:
        frames, strips, infos = LBD.build_avatar_sheet(name, fn)
        probs = LBD.audit(frames, infos, 'avatar')
        if probs:
            raise SystemExit('liam %s: %s' % (name, probs))
        ln, lcount = live_numbers('Liam/Elements/liam_%s.png' % name, 96)
        if lcount != len(frames):
            raise SystemExit('liam %s: %d frames, live has %d' % (name, len(frames), lcount))
        save('liam', 'liam_' + name, frames, times, [(name, 0, len(frames) - 1)], 'liam_puppet',
             {'kind': 'avatar body (float, staff-less)', 'anchor': [48, 96], 'source': 'Liam/Elements/liam_%s.png' % name,
              'source_numbers': ln, 'times': times, 'body_numbers': [numbers(i['body']) for i in infos],
              'fx_px': [i['fx_px'] for i in infos], 'back': LBD.back_points(infos),
              'wrists_recorded': [[list(i['hooks'][k]) for k in ('wrist_l', 'wrist_r')] for i in infos],
              'rings': sorted(set().union(*[set(i.get('rings_drawn', [])) for i in infos]))})
        save('liam', 'liam_%s_avatar' % name, strips, times, [(name + '_avatar', 0, len(strips) - 1)], 'avatar_add',
             {'kind': 'ADDITIVE glow strip (eyes, arrow marks, open-mouth glow, 2-texel rim)', 'blend': 'add',
              'anchor': [48, 96]})
        backs['liam_' + name] = LBD.back_points(infos)
        if name == 'channel':
            channel0 = (infos[0]['body'], strips[0], infos[0]['frame_info'])
    for name, times in LF.PLAIN + [('juggle', [0.06, 0.08, 0.14, 0.08, 0.08, 0.08, 0.08, 0.07, 0.09, 0.14, 0.4, 0.4])]:
        frames, infos, jinfo = LBD.build_plain_sheet(name)
        probs = LBD.audit(frames, infos, 'plain')
        if probs:
            raise SystemExit('liam %s: %s' % (name, probs))
        fw = frames[0].shape[1]
        ln, lcount = live_numbers('Liam/Elements/liam_%s.png' % name, fw)
        if lcount != len(frames):
            raise SystemExit('liam %s: %d frames, live has %d' % (name, len(frames), lcount))
        tags = [('launch', 0, 1), ('tumble', 2, 6), ('crash', 7, 9), ('down', 10, 11)] if name == 'juggle' else \
            [(name, 0, len(frames) - 1)]
        bp = [None] * len(frames) if name == 'juggle' else LBD.back_points(infos)
        save('liam', 'liam_' + name, frames, times, tags, 'liam_puppet',
             {'kind': 'twin of the live pose, staff removed', 'anchor': [64, 95] if name == 'juggle' else [48, 96],
              'source': 'Liam/Elements/liam_%s.png' % name, 'source_numbers': ln, 'times': times, 'back': bp,
              'rings': sorted(set().union(*[set(i.get('rings_drawn', [])) for i in infos]))})
        backs['liam_' + name] = bp
    # the aura loop and the on / off extras
    ab, af = LBD.aura_loop(6)
    save('liam', 'liam_avatar_aura_back', ab, [0.12], [('aura_back', 0, 5)], 'aura_back',
         {'kind': 'the orbit, far half (behind him), 6-frame loop', 'cell': [128, 128],
          'centre_corner_on_float_pivot': [64, 64], 'body_cell_top_left_in_aura': [16, 8]})
    save('liam', 'liam_avatar_aura_front', af, [0.12], [('aura_front', 0, 5)], 'aura_front',
         {'kind': 'the orbit, near half (in front of him), 6-frame loop', 'cell': [128, 128]})
    body0, strip0, info0 = channel0
    on, off = LBD.avatar_on_off(body0, strip0, LBD.lens_pixels(info0))
    save('liam', 'liam_avatar_on', on, [0.06, 0.06, 0.08, 0.08, 0.12], [('avatar_on', 0, 4)], 'avatar_add',
         {'kind': 'ADDITIVE, on channel frame 0: the glow flares in, the eyes snap white', 'blend': 'add'})
    save('liam', 'liam_avatar_off', off, [0.08, 0.1, 0.12, 0.14], [('avatar_off', 0, 3)], 'avatar_add',
         {'kind': 'ADDITIVE, on channel frame 0: the glow bursts and gutters out', 'blend': 'add'})
    return backs


# ------------------------------------------------------------------ Bixby
BIX_TIMES = {'bixby_beast': [0.12], 'bixby_beast_fly': [0.1], 'bixby_beast_flyby': [0.08], 'bixby_perch': [0.13],
             'bixby_pound': [0.09, 0.12, 0.07, 0.08, 0.08, 0.12], 'bixby_beast_land': [0.1, 0.25, 0.34],
             'bixby_beast_recover': [0.15], 'bixby_beast_hit': [0.08, 0.16], 'bixby_juggle': [0.08]}


def export_bixby():
    backs = {}
    for sheet, (fw, fh, anims) in BF.SHEETS.items():
        frames, infos = BF.build_sheet(sheet)
        probs = BF.audit(frames, infos)
        if probs:
            raise SystemExit('bixby %s: %s' % (sheet, probs))
        ln, lcount = live_numbers('Bixby/%s.png' % sheet, fw)
        if lcount != len(frames):
            raise SystemExit('bixby %s: count %d vs live %d' % (sheet, len(frames), lcount))
        tags = [(k, v[0], v[-1]) for k, v in anims.items()]
        bp = BF.back_points(infos, sheet)
        save('bixby', sheet, frames, BIX_TIMES.get(sheet, [0.1]), tags, 'bixby_puppet',
             {'kind': 'ash-fur twin', 'anchor': [128, 200] if sheet == 'bixby_juggle' else [96, 151],
              'source': 'Bixby/%s.png' % sheet, 'source_numbers': ln, 'back': bp,
              'rings': sorted(set().union(*[set(i.get('rings_drawn', [])) for i in infos])),
              'fire_kept_px': [i['fire_px'] for i in infos], 'ember_eye_frames': [f for f, i in enumerate(infos) if i['ember']]})
        backs[sheet] = bp
    frames, infos, srcs = BB.build()
    probs = BF.audit(frames, infos)
    if probs:
        raise SystemExit('bixby_bite: %s' % probs)
    hover = np.array(Image.open(CHARS + '/Bixby/bixby_beast.png').convert('RGBA'))[:, :192]
    bp = BF.back_points(infos, 'bixby_bite')
    save('bixby', 'bixby_bite', frames, BB.TIMES, [('bite', 0, 4)], 'bixby_puppet',
         {'kind': 'NEW: rear, lunge start, lunge (jaws wide), SNAP (contact), recoil', 'anchor': [96, 151],
          'source': 'built on Bixby/bixby_beast.png frame 0', 'source_numbers': numbers(hover), 'times': BB.TIMES,
          'back': bp, 'jaws': [list(i['jaws']) for i in infos], 'snap_frame': 3,
          'rings': sorted(set().union(*[set(i.get('rings_drawn', [])) for i in infos]))})
    backs['bixby_bite'] = bp
    return backs


# ------------------------------------------------------------------ the wheel
def export_wheel():
    wf = W2.wheel_frames()
    save('wheel', 'element_wheel', wf, [0.05], [('sub%d' % i, i, i) for i in range(8)], 'wheel',
         {'kind': 'the disc turned 11.25 deg x frame CLOCKWISE; the code adds 90-degree turns', 'pivot_corner': [96, 96],
          'angles_deg': W2.SUB})
    lf = W2.lit_frames()
    save('wheel', 'element_wheel_lit', lf, [0.1], [(n, i, i) for i, n in enumerate(W2.LIT_NAMES)], 'wheel_lit',
         {'kind': 'stop states at REST orientation', 'order': W2.LIT_NAMES, 'pivot_corner': [96, 96]})
    pf, tips = W2.pointer_frames()
    save('wheel', 'element_wheel_pointer', pf, [0.1, 0.04, 0.1], [('rest', 0, 0), ('bump', 1, 1), ('lit', 2, 2)], 'pointer',
         {'kind': 'the TOP-RIGHT pointer, aimed at the hub', 'frame_top_left_in_wheel': list(W2.PTR_TL),
          'pivot': [W2.PTR_PIVOT[0], W2.PTR_PIVOT[1]], 'tip': [list(t) for t in tips]})
    ic = W2.icon_frames()
    save('wheel', 'element_icons', ic, [0.12], [('fire_pop', 0, 0), ('fire', 1, 1), ('air_pop', 2, 2), ('air', 3, 3),
                                                ('water_pop', 4, 4), ('water', 5, 5), ('earth_pop', 6, 6), ('earth', 7, 7)],
         'icons', {'kind': 'upright badges', 'pivot': [16, 16], 'order': ['fire_pop', 'fire', 'air_pop', 'air', 'water_pop',
                                                                        'water', 'earth_pop', 'earth']})
    save('wheel', 'element_wheel_blur', W2.blur_frames(), [0.04], [('blur', 0, 3)], 'blur',
         {'kind': 'soft: the disc at speed, 22.5-degree phases (with the code\'s quarter turns: 16 positions)',
          'pivot_corner': [96, 96]})
    save('wheel', 'element_wheel_form', W2.form_frames(), [0.08], [('form', 0, 5)], 'form',
         {'kind': 'soft: the wheel drawing itself (backward: the dissolve)', 'pivot_corner': [96, 96]})
    save('wheel', 'element_wheel_shatter', W2.shatter_frames(), [0.06, 0.06, 0.07, 0.08, 0.1, 0.12],
         [('shatter', 0, 5)], 'shatter', {'kind': 'soft: the crash', 'frame': [208, 208], 'pivot_corner': [104, 104]})


# ------------------------------------------------------------------ the hooks table, additively
def gd_value(p):
    return 'null' if p is None else 'Vector2(%d, %d)' % (p[0], p[1])


def hooks(liam_backs, bixby_backs):
    live = open(LIVE_HOOKS, encoding='utf-8').read()
    lines = live.split('\n')
    end = lines.index('}', lines.index('const BACK := {'))
    add = []
    for key, table in (('liam', liam_backs), ('bixby', bixby_backs)):
        if any(l.startswith('\t&"%s": {' % key) for l in lines):
            raise SystemExit('the live hooks table already has %s' % key)
        add.append('\t&"%s": {' % key)
        for sheet, pts in table.items():
            add.append('\t\t&"%s": [%s],' % (sheet, ', '.join(gd_value(p) for p in pts)))
        add.append('\t},')
    new = lines[:end] + add + lines[end:]
    text = '\n'.join(new)
    d = os.path.join(STAGE, 'Scripts')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'JordanPuppetHooks.gd')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    diff = ''.join(difflib.unified_diff(live.splitlines(True), text.splitlines(True),
                                        'Scripts/JordanPuppetHooks.gd (live)', 'Scripts/JordanPuppetHooks.gd (staged)'))
    with open(os.path.join(STAGE, 'hooks.diff'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(diff)
    # additive proof: every live line is still there, in order, unchanged
    old = live.split('\n')
    it = iter(new)
    assert all(any(l == m for m in it) for l in old), 'a live line changed'
    RECORD['files']['Scripts/JordanPuppetHooks.gd'] = {'sha256': sha(p), 'ship_to': 'Scripts/JordanPuppetHooks.gd',
                                                       'mode': 'REPLACE (additive)', 'live_sha256_expected': sha(LIVE_HOOKS)}
    return diff


def main():
    global TMP
    TMP = tempfile.mkdtemp(prefix='ge_full_')
    try:
        if os.path.isdir(STAGE):
            for sub in ('Puppets', 'Wheel', 'Scripts'):
                shutil.rmtree(os.path.join(STAGE, sub), ignore_errors=True)
        os.makedirs(STAGE, exist_ok=True)
        lb = export_liam()
        bb = export_bixby()
        export_wheel()
        diff = hooks(lb, bb)
        with open(os.path.join(STAGE, 'manifest.json'), 'w') as f:
            json.dump({'stage': STAGE.replace(os.sep, '/'), 'project': PROJECT, 'files': RECORD['files']}, f, indent=1)
        with open(os.path.join(STAGE, 'numbers.json'), 'w') as f:
            json.dump(RECORD['sheets'], f, indent=1)
        print('files', len(RECORD['files']), 'sheets', len(RECORD['sheets']))
        print(diff[:3000])
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == '__main__':
    main()
