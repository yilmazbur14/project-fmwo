"""Greyson's full-meter beam in the dark maze (Jordan's attack 1): the redesign's approval pass.

A bare run writes nothing:

    python mb_build.py                                   # print this and exit
    python mb_build.py --check                           # build and audit both takes; write nothing
    python mb_build.py --write --capture DIR             # write the approval files into approval/
    python mb_build.py --write --capture DIR --out DIR2  # the same, into DIR2 (a folder OUTSIDE the project)

--capture is mb_capture.gd's output folder ("hide" run: frames with today's beam hidden); --before is
optionally a "show" run of it, for the before-and-after. --no-mocks writes the sheets and the
contract only.

It never writes under Assets/ or to project.godot, never inside the project but approval/ (every
target's real path, 8.3 names and links resolved, is checked first), never runs Godot and never
writes an .import file. It reads Greyson's puppet spirit sheet (for the overlay) and nothing else
from Assets/.

TWO TAKES of one beat (charge, release, trace, corners, impact, hold, break-up, scorch):
    a  HELLBOLT      the puppets' crimson ramp carried up to a searing white core; black lightning
                     coiled round it; a black spearhead leads it; the impact cracks open with it
    b  SOUL TORRENT  the puppets' own bone and ash ramp as ghost fire; screaming souls stream in it,
                     a howling skull leads it, a giant screaming face bursts out of the impact
Each take: beam_<t>_<sheet>.png (horizontal strips) + .aseprite (frame times and tags, built by the
Aseprite CLI from a Lua script, re-exported and compared pixel for pixel), the mocks on the real
capture (beam_<t>_mock.gif at game speed, beam_<t>_mock_slow.gif at quarter speed, four full-frame
stills and a strip of them), a contact sheet of every sheet, and contract.json for the code.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ART = os.path.join(ROOT, 'art_source')
if ART not in sys.path:
    sys.path.append(ART)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import mb_core as C  # noqa: E402
import mb_body as B  # noqa: E402
import mb_head as HD  # noqa: E402
import mb_bursts as X  # noqa: E402
import mb_diss as D  # noqa: E402
import mb_charge as Q  # noqa: E402
import mb_overlay as OV  # noqa: E402
import mb_takes as T  # noqa: E402
import mb_mock as M  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

APPROVAL = os.path.join(HERE, 'approval')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
TAKES = ('a', 'b')
TAKE_NAMES = {'a': 'HELLBOLT', 'b': 'SOUL TORRENT'}

# size (w, h) in texels, pivot (x, y) in texels, frame times (s), tags, how it plays
SPEC = {
    'charge':       dict(size=(Q.QW, Q.QW), pivot=(40, 40), times=[0.04] * 12,
                         tags=[('stage1', 0, 3), ('stage2', 4, 7), ('stage3', 8, 11)],
                         plays='each stage loops; stage by the charge clock', at='the spirit pose muzzle'),
    'charge_glow':  dict(size=(Q.QW, Q.QW), pivot=(40, 40), times=[0.04] * 12,
                         tags=[('stage1', 0, 3), ('stage2', 4, 7), ('stage3', 8, 11)], plays='with charge, additive',
                         at='the spirit pose muzzle'),
    'release':      dict(size=(Q.QW, Q.QW), pivot=(40, 40), times=[0.03] * 6, tags=[], plays='once',
                         at='the throw pose muzzle, as the trace starts'),
    'release_glow': dict(size=(Q.QW, Q.QW), pivot=(40, 40), times=[0.03] * 6, tags=[], plays='with release, additive',
                         at='the throw pose muzzle'),
    'body':         dict(size=(B.W, B.H), pivot=None, times=[0.04] * 8, tags=[], plays='loops (Line2D texture)',
                         at='the beam line'),
    'body_glow':    dict(size=(B.W, B.GH), pivot=None, times=[0.04] * 8, tags=[],
                         plays='loops with body (a second Line2D, additive)', at='the beam line'),
    'head':         dict(size=(HD.HW, HD.HH), pivot=HD.ATTACH, times=[0.03] * 6, tags=[], plays='loops',
                         at="the line's end while it traces"),
    'head_glow':    dict(size=(HD.HW, HD.HH), pivot=HD.ATTACH, times=[0.03] * 6, tags=[], plays='with head, additive',
                         at="the line's end"),
    'corner':       dict(size=(X.CW, X.CW), pivot=(32, 32), times=[0.03] * 6, tags=[], plays='once per joint',
                         at='each joint, as the head passes it'),
    'corner_glow':  dict(size=(X.CW, X.CW), pivot=(32, 32), times=[0.03] * 6, tags=[], plays='with corner, additive',
                         at='each joint'),
    'impact':       dict(size=(X.IW, X.IW), pivot=(56, 56), times=[0.04] * 10, tags=[], plays='once',
                         at="the line's end (the player's middle) on the hit"),
    'impact_glow':  dict(size=(X.IW, X.IW), pivot=(56, 56), times=[0.04] * 10, tags=[], plays='with impact, additive',
                         at="the line's end"),
    'ring':         dict(size=(X.RW, X.RH), pivot=(64, 24), times=[0.035] * 8, tags=[], plays='once, with impact',
                         at="the player's soles (the line's end + BEAM_HEIGHT down)"),
    'dissipate':    dict(size=(B.W, B.H), pivot=None, times=[0.05] * 8, tags=[],
                         plays='once (swap the line texture to it)', at='the beam line'),
    'ember':        dict(size=(D.EMBER, D.EMBER), pivot=(4, 4), times=[0.08] * 6, tags=[],
                         plays="once over each particle's life", at='particles off the line'),
    'smoke':        dict(size=(D.SMOKE, D.SMOKE), pivot=(8, 8), times=[0.1] * 6, tags=[],
                         plays="once over each particle's life", at='particles off the line'),
    'scorch':       dict(size=(D.SW, D.SH), pivot=None, times=[0.15, 0.2, 0.25, 0.4], tags=[],
                         plays='once, the last frame held until the lights are up', at='the floor line'),
    'overlay':      dict(size=(OV.FW, OV.FW), pivot='the puppet sprite\'s own', times=[0.06] * 8,
                         tags=[('spirit_f0', 0, 2), ('spirit_f1', 3, 5), ('throw', 6, 7)],
                         plays='frame by his pose and the charge stage', at="over Greyson's sprite"),
}
LINES = ('body', 'body_glow', 'dissipate', 'scorch')


# ------------------------------------------------------------------------------------------ guard

def _real(p):
    return os.path.normcase(os.path.realpath(p))


def _under(path, root):
    p, r = _real(path), _real(root)
    return p == r or p.startswith(r + os.sep)


def guard_dir(out_dir):
    if _under(out_dir, APPROVAL):
        return
    if _under(out_dir, ROOT):
        raise SystemExit('refusing: %s is inside the project but not art_source/jordan_maze_beam/approval/' % out_dir)


def guard_file(path, out_dir):
    if not _under(path, out_dir):
        raise SystemExit('refusing: %s is outside %s' % (path, out_dir))
    if _under(path, os.path.join(ROOT, 'Assets')) or _real(path) == _real(os.path.join(ROOT, 'project.godot')):
        raise SystemExit('refusing: %s' % path)
    if path.endswith('.import'):
        raise SystemExit('refusing to write an .import file: %s' % path)


# ------------------------------------------------------------------------------------------ audit

def build_all():
    return {take: T.build(take) for take in TAKES}


def audit(sheets):
    report, bad = [], []
    for take in TAKES:
        pal, gpal = T.palettes(take)
        for name, grids in sheets[take].items():
            spec = SPEC[name]
            p = gpal if T.SHEETS[name][3] else pal
            allowed = set(p.rgb[1:])
            w, h = spec['size']
            if len(grids) != len(spec['times']):
                bad.append('%s %s: %d frames, contract says %d' % (take, name, len(grids), len(spec['times'])))
            opaque, cols = 0, set()
            for i, g in enumerate(grids):
                if g.shape != (h, w):
                    bad.append('%s %s f%d: %s, not %dx%d' % (take, name, i, g.shape[::-1], w, h))
                im = np.array(p.image(g))
                a = im[..., 3]
                if ((a > 0) & (a < 255)).any():
                    bad.append('%s %s f%d: semi-alpha' % (take, name, i))
                px = set(map(tuple, im[a > 0][:, :3].tolist()))
                if not px <= allowed:
                    bad.append('%s %s f%d: colours off the palette %s' % (take, name, i, sorted(px - allowed)[:3]))
                opaque += int((a > 0).sum())
                cols |= px
            if name in LINES:
                for i, g in enumerate(grids):
                    seam = _seam_score(g)
                    # a real seam (a field that doesn't wrap) changes most rows at once; a thorn's back edge
                    # or a bolt crossing the edge is what any column pair inside the tile shows too
                    if seam is not None and seam[0] > 1.25 * seam[1] + 1:
                        bad.append('%s %s f%d: a seam at the tile edge (%.2f vs the worst inside %.2f)'
                                   % (take, name, i, seam[0], seam[1]))
            if name == 'body':
                for i, g in enumerate(grids):
                    holes = [x for x in range(B.W) if g[15, x] == 0 or g[16, x] == 0]
                    if holes:
                        bad.append('%s body f%d: the centre line has holes at %s' % (take, i, holes[:5]))
            report.append('  %s %-13s %dx%d x%-2d  opaque %6d  colours %2d' % (take, name, w, h, len(grids), opaque,
                                                                               len(cols)))
    return report, bad


def _seam_score(g):
    """How much the tile's wrap-around column pair differs, against the worst neighbouring pair
    inside the tile (both counted in texels that change)."""
    diffs = [(g[:, x] != g[:, x + 1]).sum() for x in range(g.shape[1] - 1)]
    if not diffs:
        return None
    return float((g[:, -1] != g[:, 0]).sum()), float(max(diffs))


# ------------------------------------------------------------------------------------------ .aseprite

LUA = r'''
local p = app.params
local n, w, h = tonumber(p.n), tonumber(p.w), tonumber(p.h)
local spr = Sprite(w, h, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = p.layer
for i = 2, n do spr:newEmptyFrame() end
for i = 1, n do
  local img = Image{ fromFile = p.dir .. "/f" .. (i - 1) .. ".png" }
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = tonumber(p["d" .. (i - 1)])
end
if p.tags ~= "-" then
  for spec in string.gmatch(p.tags, "[^;]+") do
    local name, a, b = spec:match("([^:]+):(%d+):(%d+)")
    local t = spr:newTag(tonumber(a) + 1, tonumber(b) + 1)
    t.name = name
  end
end
local cols = {}
for c in string.gmatch(p.pal, "[^,]+") do table.insert(cols, c) end
local pal = Palette(#cols + 1)
pal:setColor(0, Color{ r = 0, g = 0, b = 0, a = 0 })
for i, c in ipairs(cols) do
  pal:setColor(i, Color{ r = tonumber(c:sub(1, 2), 16), g = tonumber(c:sub(3, 4), 16), b = tonumber(c:sub(5, 6), 16), a = 255 })
end
spr:setPalette(pal)
spr:saveAs(p.out)
'''


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('aseprite failed: %s %s' % (r.stdout, r.stderr))
    return r


def build_aseprite(tmp, name, frames, p, times, tags):
    """frames: PIL RGBA frames. Returns (ase path, strip path)."""
    fdir = os.path.join(tmp, name + '_frames')
    os.makedirs(fdir)
    for i, im in enumerate(frames):
        im.save(os.path.join(fdir, 'f%d.png' % i))
    lua = os.path.join(tmp, 'build.lua')
    if not os.path.exists(lua):
        with open(lua, 'w', encoding='utf-8') as fh:
            fh.write(LUA)
    ase = os.path.join(tmp, name + '.aseprite')
    w, h = frames[0].size
    pal = ','.join(c.lstrip('#') for c in p.hexes())
    tagspec = ';'.join('%s:%d:%d' % t for t in tags) or '-'
    args = []
    for k, v in (('n', len(frames)), ('w', w), ('h', h), ('dir', fdir.replace('\\', '/')),
                 ('out', ase.replace('\\', '/')), ('pal', pal), ('tags', tagspec), ('layer', name)):
        args += ['--script-param', '%s=%s' % (k, v)]
    for i, t in enumerate(times):
        args += ['--script-param', 'd%d=%s' % (i, t)]
    aseprite(*(args + ['--script', lua]))
    strip = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        strip.paste(im, (i * w, 0))
    png = os.path.join(tmp, name + '.png')
    strip.save(png)
    back = os.path.join(tmp, name + '_rt.png')
    data = os.path.join(tmp, name + '_rt.json')
    aseprite(ase, '--sheet', back, '--sheet-type', 'horizontal', '--data', data, '--format', 'json-array',
             '--list-tags')
    d = pixel_diff(Image.open(png), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    with open(data, encoding='utf-8') as fh:
        meta = json.load(fh)
    durs = [fr['duration'] for fr in meta['frames']]
    want = [int(round(t * 1000)) for t in times]
    if durs != want:
        raise SystemExit('%s: frame durations %s, expected %s' % (name, durs, want))
    got_tags = [(t['name'], t['from'], t['to']) for t in meta['meta'].get('frameTags', [])]
    if got_tags != list(tags):
        raise SystemExit('%s: tags %s, expected %s' % (name, got_tags, tags))
    return ase, png


# ------------------------------------------------------------------------------------------ presentation

def contact(take, sheets, scale=3):
    """Every sheet of a take on black, each frame over its glow (glows added), labelled."""
    pal, gpal = T.palettes(take)
    rows = []
    glow_of = {'charge': 'charge_glow', 'release': 'release_glow', 'body': 'body_glow', 'head': 'head_glow',
               'corner': 'corner_glow', 'impact': 'impact_glow'}
    for name in ('charge', 'release', 'body', 'head', 'corner', 'impact', 'ring', 'dissipate', 'ember', 'smoke',
                 'scorch', 'overlay'):
        grids = sheets[name]
        glows = sheets.get(glow_of.get(name, ''), None)
        tiles = []
        for i, g in enumerate(grids):
            h, w = g.shape
            base = np.zeros((h if name not in ('body',) else B.GH, w, 3), np.int32)
            if glows is not None:
                gi = np.array(gpal.image(glows[i]))
                gh, gw = gi.shape[:2]
                oy, ox = (base.shape[0] - gh) // 2, (w - gw) // 2
                sub = base[max(0, oy):max(0, oy) + gh, max(0, ox):max(0, ox) + gw]
                gi = gi[max(0, -oy):max(0, -oy) + sub.shape[0], max(0, -ox):max(0, -ox) + sub.shape[1]]
                m = gi[..., 3] > 0
                sub[m] += gi[..., :3][m]
            im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
            if name == 'overlay':
                spirit = Image.open(OV.SPIRIT).convert('RGBA')
                k = [0, 0, 0, 1, 1, 1, 3, 3][i]
                im.alpha_composite(spirit.crop((k * OV.FW, 0, (k + 1) * OV.FW, OV.FW)))
            im.alpha_composite(pal.image(g), (0, (im.height - h) // 2))
            tiles.append(im)
        rows.append((name, tiles))
    pad = 6
    width = max(sum(t.width + pad for t in tiles) for _, tiles in rows) * scale + 160
    height = sum((max(t.height for t in tiles) * scale + 24) for _, tiles in rows) + 40
    height += 30
    sheet = Image.new('RGB', (width, height), (34, 32, 40))
    d = ImageDraw.Draw(sheet)
    big, mid = ImageFont.load_default(size=28), ImageFont.load_default(size=22)
    d.text((10, 10), 'Take %s  %s  -  every sheet at %dx on black, glows added under their sprites; the overlay '
                     'shown on Greyson' % (take.upper(), TAKE_NAMES[take], scale), fill=(235, 235, 235), font=big)
    y = 70
    for name, tiles in rows:
        d.text((10, y + 4), name, fill=(235, 235, 235), font=mid)
        x = 160
        for t in tiles:
            sheet.paste(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (x, y))
            x += (t.width + pad) * scale
        y += max(t.height for t in tiles) * scale + 24
    return sheet


def contract(sheets):
    L = M.TIMELINE
    out = {
        'about': "Greyson's full-meter beam in Jordan's dark maze (JordanComboMaze / JordanPathBeam): the redesign's "
                 "approval pass. Two takes, a (HELLBOLT) and b (SOUL TORRENT), with the same sizes, frame counts, times "
                 "and pivots, so either drops into the same code. Every size is in texels; every texel is 3 world px "
                 "(Sprite2D scale 3, Line2D width = texture height x 3), which the god fight's 2/3 view shows as 2 "
                 "screen px. Texture filter nearest (the project default). Glow sheets are opaque dark tones for "
                 "CanvasItemMaterial BLEND_MODE_ADD, drawn under their sprite.",
        'files': 'approval/beam_<take>_<sheet>.png (horizontal strips, frame 0 leftmost) + .aseprite beside each',
        'texel_world_px': 3,
        'view_zoom': 2.0 / 3.0,
        'palettes': {
            'a': {'colours': C.PAL_A, 'glow_add': C.GLOW_A,
                  'measured_from_puppets': ['#17111D', '#36091C', '#661127', '#9F1C2E', '#D2403A'],
                  'new': ['#FF4A57', '#FF9EA0', '#FFE4E4', '#FFFFFF', '#000000']},
            'b': {'colours': C.PAL_B, 'glow_add': C.GLOW_B,
                  'measured_from_puppets': ['#17111D', '#2C2434', '#4A4356', '#6E6A80', '#9893A5', '#CFC6B2', '#F1EAD4',
                                            '#D2403A', '#9F1C2E', '#661127'],
                  'new': ['#FFFFFF', '#000000']},
        },
        'timeline_s': {
            'charge': L['charge'], 'charge_stages': list(L['stage_times']),
            'trace': L['trace'], 'trace_speed': 'constant along the line (its length / trace)',
            'hitstop_suggested': L['hitstop'], 'flash_suggested': {'time': L['flash_time'], 'white_alpha': L['flash_alpha']},
            'hold': L['hold'], 'dissipate': L['dissipate'], 'lights_up': L['lights'],
            'scorch_frame_starts_from_dissipate': list(L['scorch_times']),
            'order': 'charge (0.72) -> release + trace (0.18) -> hit: impact + ring + hit-stop + flash + shake -> '
                     'hold (0.30, body keeps looping) -> dissipate (0.40, line texture -> dissipate frames, particles, '
                     'scorch appears) -> lights up (0.40, scorch cools on and fades with the dark)',
        },
        'line': {
            'body': {'sheet': 'body', 'frame': [B.W, B.H], 'frames': 8, 'frame_time': 0.04, 'loop': True,
                     'width_world_px': B.H * 3, 'tile_world_px': B.W * 3,
                     'centre_row': 'between rows 15 and 16 (the line runs through the texture\'s middle)',
                     'flow': 'content moves +x (from the muzzle towards the player) 12 texels a frame; frame 8 = frame 0',
                     'godot': 'Line2D, texture_mode LINE_TEXTURE_TILE, texture_repeat ENABLED, joint_mode SHARP, no caps; '
                              'swap line.texture per frame (cut each frame out of the strip, as JordanPathBeam does now)',
                     'note': 'a Line2D puts the texture\'s top row on the line\'s left, so runs going left show it upside '
                             'down and vertical runs sideways; take a is near-symmetric, take b\'s souls tumble (use per-run '
                             'Line2Ds with a V-flipped texture on left-going runs if they should stay upright)'},
            'body_glow': {'sheet': 'body_glow', 'frame': [B.W, B.GH], 'frames': 8, 'frame_time': 0.04,
                          'width_world_px': B.GH * 3, 'tile_world_px': B.W * 3, 'blend': 'add',
                          'godot': 'a second Line2D on the same points, drawn first, frame in step with the body'},
            'dissipate': {'sheet': 'dissipate', 'frame': [B.W, B.H], 'frames': 8, 'frame_time': 0.05, 'loop': False,
                          'width_world_px': B.H * 3, 'tile_world_px': B.W * 3,
                          'godot': 'the body Line2D, its texture swapped to these frames; the glow line off'},
            'scorch': {'sheet': 'scorch', 'frame': [D.SW, D.SH], 'frames': 4,
                       'frame_starts_s': list(L['scorch_times']), 'width_world_px': D.SH * 3,
                       'tile_world_px': D.SW * 3,
                       'points': 'the beam line\'s points but the first (the muzzle), each moved BEAM_HEIGHT (40) down onto '
                                 'the floor line',
                       'godot': 'a Line2D on the floor layer, lifted over the dark while it is down (its glowing seam is '
                                'what shows); fade its alpha with the lights coming up, or keep it to the wrap'},
        },
        'head': {'sheet': 'head', 'frame': [HD.HW, HD.HH], 'frames': 6, 'frame_time': 0.03, 'loop': True,
                 'attach_texel': list(HD.ATTACH), 'faces': 'right (+x)',
                 'godot': "Sprite2D, offset so the attach texel is on the line's end (centered=false, "
                          "offset = -attach); rotation = the current run's angle; flip_v when cos(angle) < 0 so it never "
                          "goes upside down on runs going left",
                 'glow': 'head_glow, same size, attach and transform, additive'},
        'corner': {'sheet': 'corner', 'frame': [X.CW, X.CW], 'frames': 6, 'frame_time': 0.03, 'loop': False,
                   'pivot_texel': [32, 32], 'at': 'each joint of the line (every point but the first and last), '
                                                  'when the head passes it',
                   'drawn_for': 'the turn running right then down: its splash thrown to the outer corner, up-right',
                   'flip_rule': 'outer = incoming unit - outgoing unit; flip_h if outer.x < 0, flip_v if outer.y > 0',
                   'glow': 'corner_glow, same pivot and flips, additive'},
        'impact': {'sheet': 'impact', 'frame': [X.IW, X.IW], 'frames': 10, 'frame_time': 0.04, 'loop': False,
                   'pivot_texel': [56, 56], 'at': "the line's end (the player's middle) as the head arrives",
                   'glow': 'impact_glow, same pivot, additive'},
        'ring': {'sheet': 'ring', 'frame': [X.RW, X.RH], 'frames': 8, 'frame_time': 0.035, 'loop': False,
                 'pivot_texel': [64, 24], 'at': "the player's soles: the line's end + (0, BEAM_HEIGHT)",
                 'z': 'under the impact (it runs along the floor)'},
        'charge': {'sheet': 'charge', 'frame': [Q.QW, Q.QW], 'frames': 12, 'frame_time': 0.04,
                   'stages': {'1': [0, 3], '2': [4, 7], '3': [8, 11]}, 'stage_starts_s': [0.0, 0.24, 0.48],
                   'pivot_texel': [40, 40], 'at': 'GreysonArtLayout.muzzle(&"spirit", frame): (82, 7) on his sheet, '
                                                   'world (846, 555) in the capture',
                   'glow': 'charge_glow, same frames and pivot, additive',
                   'note': 'it covers the right end of his meter (the raised muzzle sits on it)'},
        'release': {'sheet': 'release', 'frame': [Q.QW, Q.QW], 'frames': 6, 'frame_time': 0.03, 'loop': False,
                    'pivot_texel': [40, 40], 'at': 'the spirit_throw muzzle (66, 70) on his sheet, world (798, 744), '
                                                   'as the trace starts',
                    'drawn_for': 'firing down (+y); the first run from his muzzle to the goal is always near straight down',
                    'glow': 'release_glow, additive'},
        'particles': {
            'ember': {'sheet': 'ember', 'frame': [D.EMBER, D.EMBER], 'frames': 6, 'pivot_texel': [4, 4],
                      'emit': 'from the dissipate start, 2 per 26 world px of line, within 30 px of it, spread over 0.25 s',
                      'velocity_world_px_s': {'x': [-40, 40], 'y': [-200, -90]}, 'life_s': [0.30, 0.55],
                      'frames_over_life': True},
            'smoke': {'sheet': 'smoke', 'frame': [D.SMOKE, D.SMOKE], 'frames': 6, 'pivot_texel': [8, 8],
                      'emit': 'from the dissipate start, 1 per 47 world px of line (55% of every 26), within 24 px',
                      'velocity_world_px_s': {'x': [-15, 15], 'y': [-80, -40]}, 'life_s': [0.45, 0.70],
                      'frames_over_life': True},
        },
        'overlay': {'sheet': 'overlay', 'frame': [OV.FW, OV.FW], 'frames': 8,
                    'over': 'Assets/Characters/Jordan/Puppets/greyson/greyson_spirit.png, texel for texel',
                    'godot': "a child Sprite2D of the puppet's sprite with the same centring, offset and flip_h, drawn "
                             "above it",
                    'frames_map': {'spirit frame 0': [0, 1, 2], 'spirit frame 1': [3, 4, 5], 'spirit frame 3 (throw)': [6, 7]},
                    'pick': 'during the charge: 3 x (his spirit frame) + charge stage (0-2); through the trace and hold: '
                            '6 and 7 alternating every 0.05 s; off at the dissipate',
                    'optional': True},
        'sheets': {},
    }
    for name, spec in SPEC.items():
        w, h = spec['size']
        out['sheets'][name] = {'file': 'beam_<take>_%s.png' % name, 'frame': [w, h], 'frames': len(spec['times']),
                               'frame_times_s': spec['times'], 'strip_px': [w * len(spec['times']), h],
                               'pivot_texel': list(spec['pivot']) if isinstance(spec['pivot'], tuple) else spec['pivot'],
                               'tags': [{'name': t[0], 'from': t[1], 'to': t[2]} for t in spec['tags']],
                               'plays': spec['plays'], 'at': spec['at'],
                               'blend': 'add' if T.SHEETS[name][3] else 'mix'}
    return out


# ------------------------------------------------------------------------------------------ mocks

STILLS = (('1_charge', lambda s: s.t_charge + 0.62), ('2_trace', lambda s: s.t_release + 0.11),
          ('3_impact', lambda s: s.t_hold + 0.09), ('4_dissipate', lambda s: s.t_diss + 0.12))


def save_gif(path, rgb_frames, ms):
    frames = M.to_gif_frames(rgb_frames)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0, disposal=1)


def mocks(tmp, capture, before, sheets):
    cap = M.Capture(capture)
    staged = {}
    seqs = {}
    for take in TAKES:
        art = T.mock_art(take, sheets[take])
        seq = M.Sequence(cap, art)
        seqs[take] = seq
        fr = M.sequence_frames(seq)
        p = os.path.join(tmp, 'beam_%s_mock.gif' % take)
        save_gif(p, fr, int(1000 / M.FPS))
        staged[os.path.basename(p)] = p
        # the fast part at a quarter speed: from the release to the end of the break-up
        slow = M.sequence_frames(seq, fps=25, slow=4.0, t0=seq.t_release - 0.1,
                                 t1=seq.t_lights + 0.1)
        p = os.path.join(tmp, 'beam_%s_mock_slow.gif' % take)
        save_gif(p, slow, 40)
        staged[os.path.basename(p)] = p
        strip = []
        for label, when in STILLS:
            t = when(seq)
            full = Image.fromarray(seq.frame(t))
            p = os.path.join(tmp, 'beam_%s_still_%s.png' % (take, label))
            full.save(p)
            staged[os.path.basename(p)] = p
            strip.append((label, full.crop(M.CROP)))
        W = sum(im.width for _, im in strip) + 12 * (len(strip) - 1)
        s = Image.new('RGB', (W, strip[0][1].height + 28), (34, 32, 40))
        d = ImageDraw.Draw(s)
        x = 0
        for label, im in strip:
            s.paste(im, (x, 28))
            d.text((x + 6, 4), 'Take %s %s - %s (1:1 game pixels)' % (take.upper(), TAKE_NAMES[take], label[2:]),
                   fill=(235, 235, 235), font=ImageFont.load_default(size=18))
            x += im.width + 12
        p = os.path.join(tmp, 'beam_%s_stills.png' % take)
        s.save(p)
        staged[os.path.basename(p)] = p
    if before:
        capb = M.Capture(before)
        fr = M.before_frames(capb, seqs['a'])
        p = os.path.join(tmp, 'beam_before.gif')
        save_gif(p, fr, int(1000 / M.FPS))
        staged[os.path.basename(p)] = p
        # the hold side by side: today, take a, take b
        i_hold = capb.beats['HOLD'][6]
        today = Image.fromarray(capb.image(i_hold).astype(np.uint8)).crop(M.CROP)
        ims = [('TODAY (Computah laser, 0.45 s trace)', today)]
        for take in TAKES:
            seq = seqs[take]
            ims.append(('TAKE %s %s (0.18 s trace)' % (take.upper(), TAKE_NAMES[take]),
                        Image.fromarray(seq.frame(seq.t_hold + 0.09)).crop(M.CROP)))
        W = sum(im.width for _, im in ims) + 12 * (len(ims) - 1)
        s = Image.new('RGB', (W, ims[0][1].height + 28), (34, 32, 40))
        d = ImageDraw.Draw(s)
        x = 0
        for label, im in ims:
            s.paste(im, (x, 28))
            d.text((x + 6, 4), label, fill=(235, 235, 235), font=ImageFont.load_default(size=18))
            x += im.width + 12
        p = os.path.join(tmp, 'beam_compare_hit.png')
        s.save(p)
        staged[os.path.basename(p)] = p
    return staged


# ------------------------------------------------------------------------------------------ main

def write(out_dir, capture, before, with_mocks):
    guard_dir(out_dir)
    sheets = build_all()
    report, bad = audit(sheets)
    if bad:
        print('\n'.join(report))
        for b_ in bad:
            print('  FAIL ' + b_)
        raise SystemExit('audit FAILED: nothing written')
    tmp = tempfile.mkdtemp(prefix='mazebeam_')
    written = []
    try:
        staged = {}
        for take in TAKES:
            pal, gpal = T.palettes(take)
            for name, grids in sheets[take].items():
                p = gpal if T.SHEETS[name][3] else pal
                frames = [p.image(g) for g in grids]
                base = 'beam_%s_%s' % (take, name)
                ase, png = build_aseprite(tmp, base, frames, p, SPEC[name]['times'], SPEC[name]['tags'])
                staged[base + '.png'] = png
                staged[base + '.aseprite'] = ase
            sheet = contact(take, sheets[take])
            p = os.path.join(tmp, 'beam_%s_sheets.png' % take)
            sheet.save(p)
            staged[os.path.basename(p)] = p
        print('.aseprite: %d files, every one round-trips pixel for pixel with its PNG, frame times and tags as the '
              'contract' % len([k for k in staged if k.endswith('.aseprite')]))
        if with_mocks:
            staged.update(mocks(tmp, capture, before, sheets))
        cpath = os.path.join(tmp, 'contract.json')
        with open(cpath, 'w', encoding='utf-8') as fh:
            json.dump(contract(sheets), fh, indent=1)
        staged['contract.json'] = cpath
        os.makedirs(out_dir, exist_ok=True)
        for dst, src in sorted(staged.items()):
            target = os.path.join(out_dir, dst)
            guard_file(target, out_dir)
            shutil.copyfile(src, target)
            written.append(target)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return written


def main(argv):
    if not argv or argv[0] not in ('--check', '--write'):
        print(__doc__)
        return 2
    if argv[0] == '--check':
        sheets = build_all()
        report, bad = audit(sheets)
        print('\n'.join(report))
        for b_ in bad:
            print('  FAIL ' + b_)
        print('audit %s: nothing written' % ('FAILED' if bad else 'passed'))
        return 1 if bad else 0
    out = APPROVAL
    if '--out' in argv:
        out = argv[argv.index('--out') + 1]
    with_mocks = '--no-mocks' not in argv
    capture = argv[argv.index('--capture') + 1] if '--capture' in argv else None
    before = argv[argv.index('--before') + 1] if '--before' in argv else None
    if with_mocks and not capture:
        raise SystemExit('--write needs --capture DIR (mb_capture.gd\'s "hide" run), or --no-mocks')
    for p in write(out, capture, before, with_mocks):
        print('wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
