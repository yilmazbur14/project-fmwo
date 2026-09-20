"""Build, validate and install the Eric V2 UI art, with real multi-frame .aseprite files (frame durations,
tags) built by Aseprite in batch mode and round-trip checked against the PNGs.

  python ev2_export.py                  install into the project; refuses to overwrite any existing file
  python ev2_export.py --overwrite-own  also allow overwriting this script's own deliverables
  python ev2_export.py --out=DIR        write the same tree under DIR instead (a staging build)
  python ev2_export.py --check          rebuild and compare with the installed files, byte for byte (no writes)

HUD pieces go to Assets/UI/ as name.png (1x), name_3x.png (what the HUD draws, at scale 1) and
name.aseprite (1x, exports pixel-identical to name.png). The dodge tell and the sword landing mark are
world effects drawn at 3x, so they go to Assets/Effects/ as name.png + .aseprite only, next to
parry_tell.png: nothing outside Assets/UI/ gets a _3x copy.
A PNG with rows (qte_meter3_banked, qte_meter3_flash) is a grid, one row per bar; its .aseprite holds
every cell as a frame, row by row, with a tag per row, as the kit's streak_badge does."""
import filecmp
import os
import subprocess
import sys
sys.dont_write_bytecode = True
from ev2_common import *
from pngio import read_png
import break_gauge as BG
import mash_meter as MM
import tier_stamps as TS
import dodge_tell as DT
import sword_mark as SM

CHECK = '--check' in sys.argv
OVERWRITE_OWN = '--overwrite-own' in sys.argv
OUT_ROOT = next((a.split('=', 1)[1].replace(os.sep, '/').rstrip('/') + '/' for a in sys.argv
                 if a.startswith('--out=')), None)
ROOT = OUT_ROOT or PROJ
TMP = work('ase_frames/')
os.makedirs(TMP, exist_ok=True)
UI = 'Assets/UI/'
FX = 'Assets/Effects/'
GOLD_SET = set(GOLD) | {'000000'}

LUA = r'''
local specPath = app.params["spec"]
local lines = {}
for line in io.lines(specPath) do
  if #line > 0 then table.insert(lines, line) end
end
local function split(s, sep)
  local out = {}
  for piece in string.gmatch(s, "([^" .. sep .. "]+)") do table.insert(out, piece) end
  return out
end
local head = split(lines[1], "|")
local outPath, W, H = head[1], tonumber(head[2]), tonumber(head[3])
local layerNames = split(lines[2], ",")
local spr = Sprite(W, H, ColorMode.RGB)
local layers = {}
layers[1] = spr.layers[1]
layers[1].name = layerNames[1]
for i = 2, #layerNames do
  local l = spr:newLayer()
  l.name = layerNames[i]
  layers[i] = l
end
local frameLines, tagLines = {}, {}
for i = 3, #lines do
  if string.sub(lines[i], 1, 4) == "TAG|" then table.insert(tagLines, lines[i])
  else table.insert(frameLines, lines[i]) end
end
for f, fl in ipairs(frameLines) do
  local parts = split(fl, "|")
  local frame
  if f == 1 then frame = spr.frames[1] else frame = spr:newEmptyFrame() end
  frame.duration = tonumber(parts[1]) / 1000.0
  for li = 1, #layerNames do
    local p = parts[li + 1]
    if p and p ~= "-" then
      spr:newCel(layers[li], frame, Image{ fromFile = p }, Point(0, 0))
    end
  end
end
for _, tl in ipairs(tagLines) do
  local parts = split(tl, "|")
  local tag = spr:newTag(tonumber(parts[3]), tonumber(parts[4]))
  tag.name = parts[2]
end
spr:saveAs(outPath)
spr:close()
'''

DELIVERABLES = []


def lua_path():
    p = work('make_ase_ev2.lua')
    open(p, 'w').write(LUA)
    return p


def target(rel):
    return ROOT + rel


def may_write(path):
    if CHECK:
        return False
    if OUT_ROOT is None and os.path.exists(path) and not (OVERWRITE_OWN and path.replace(ROOT, '') in DELIVERABLES):
        raise SystemExit('REFUSING to overwrite existing file ' + path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return True


def emit(canvas, rel):
    """writes a PNG, or in --check re-encodes it and compares the bytes with the installed file"""
    DELIVERABLES.append(rel)
    path = target(rel)
    if CHECK:
        fresh = work('check_' + os.path.basename(rel))
        canvas.save(fresh)
        assert filecmp.cmp(fresh, path, shallow=False), 'differs from project, byte for byte: ' + rel
        return
    may_write(path)
    canvas.save(path)


def check_png(rel, allowed, expect):
    w, h, px = read_png(target(rel))
    assert (w, h) == (expect.w, expect.h), (rel, (w, h))
    assert {p[3] for row in px for p in row} <= {0, 255}, ('partial alpha', rel)
    cols = {'%02x%02x%02x' % p[:3] for row in px for p in row if p[3] == 255}
    assert cols <= set(allowed), (rel, cols - set(allowed))
    back = from_png(target(rel))
    assert back.p == expect.p, ('pixels differ after reading back', rel)


def build_ase(rel, w, h, layer_names, frame_layers, durations, tags=()):
    DELIVERABLES.append(rel)
    path = target(rel)
    key = os.path.splitext(os.path.basename(rel))[0]
    out = path if not CHECK else work(key + '_check.aseprite')
    if not CHECK:
        may_write(path)
    elif os.path.exists(out):
        os.remove(out)
    assert len(frame_layers) == len(durations), (rel, len(frame_layers), len(durations))
    lines = ['%s|%d|%d' % (out, w, h), ','.join(layer_names)]
    for fi, (lays, d) in enumerate(zip(frame_layers, durations)):
        parts = [str(d)]
        for li, c in enumerate(lays):
            if not c.colours():
                parts.append('-')
                continue
            fp = TMP + '%s_f%02d_l%d.png' % (key, fi, li)
            c.save(fp)
            parts.append(fp)
        lines.append('|'.join(parts))
    for name, a, b in tags:
        lines.append('TAG|%s|%d|%d' % (name, a, b))
    spec = TMP + key + '_spec.txt'
    open(spec, 'w').write('\n'.join(lines) + '\n')
    run = subprocess.run([ASEPRITE, '-b', '--script-param', 'spec=' + spec, '--script', lua_path()],
                         capture_output=True, text=True)
    assert os.path.exists(out), (out, run.stdout, run.stderr)
    comp = []
    for lays in frame_layers:
        c = Canvas(w, h)
        for l in lays:
            c.blit(l, 0, 0)
        comp.append(c)
    ref = strip(comp)
    for src in ([out, path] if CHECK else [out]):
        back = TMP + key + '_roundtrip.png'
        if os.path.exists(back):
            os.remove(back)
        subprocess.run([ASEPRITE, '-b', src, '--sheet', back, '--sheet-type', 'horizontal'],
                       capture_output=True, text=True)
        rt = from_png(back)
        assert (rt.w, rt.h) == (ref.w, ref.h) and rt.p == ref.p, ('.aseprite round trip mismatch', src)
    if CHECK:
        assert filecmp.cmp(out, path, shallow=False), ('.aseprite differs from a fresh build', rel)


def ui_asset(name, frames, durations, tags=None):
    s = strip(frames)
    emit(s, UI + name + '.png')
    check_png(UI + name + '.png', DB32, s)
    s3 = scale3(s)
    emit(s3, UI + name + '_3x.png')
    check_png(UI + name + '_3x.png', DB32, s3)
    if tags is None:
        tags = [('pulse' if len(frames) == 2 else 'loop', 1, len(frames))] if len(frames) > 1 else []
    build_ase(UI + name + '.aseprite', frames[0].w, frames[0].h, [name], [[f] for f in frames], durations, tags)


def ui_sheet(name, rows, durations, tags):
    sheet = grid_sheet(rows)
    emit(sheet, UI + name + '.png')
    check_png(UI + name + '.png', DB32, sheet)
    s3 = scale3(sheet)
    emit(s3, UI + name + '_3x.png')
    check_png(UI + name + '_3x.png', DB32, s3)
    flat = [f for row in rows for f in row]
    build_ase(UI + name + '.aseprite', flat[0].w, flat[0].h, [name], [[f] for f in flat], durations, tags)


def sanity(gauge, meter, stamps, tell, mark):
    # sizes the HUD layout depends on
    assert (gauge['break_gauge_frame'][0].w, gauge['break_gauge_frame'][0].h) == (BG.GW, BG.GH) == (128, 7)
    assert (gauge['break_gauge_fill'][0].w, gauge['break_gauge_fill'][0].h) == (BG.FILL_W, BG.FILL_H) == (114, 3)
    assert all((f.w, f.h) == (140, 7) for f in gauge['break_gauge_pulse'])
    assert all((f.w, f.h) == (114, 3) for f in gauge['break_gauge_fill_hot'])
    assert all((f.w, f.h) == (144, 31) for f in gauge['break_gauge_shatter'])
    assert all((f.w, f.h) == (72, 20) for f in gauge['break_text'])
    assert len(gauge['break_gauge_pulse']) == len(gauge['break_gauge_fill_hot']) == len(BG.PULSE_MS) == 4
    assert len(gauge['break_gauge_shatter']) == len(BG.SHATTER_MS) == 6
    # the fill sits wholly inside the channel, and the gold band starts at 80%
    assert BG.FILL_X == BG.PLATE_W and BG.FILL_X + BG.FILL_W == BG.GW - BG.PLATE_W
    assert BG.WHITE_GOLD_EDGES[-1] == round(BG.FILL_W * 0.8)
    # the 3-bar meter keeps today's footprint, and today's frame pixel for pixel outside the channel
    today = from_png(PROJ + UI + 'qte_meter_frame.png')
    f3 = meter['qte_meter3_frame'][0]
    assert (f3.w, f3.h) == (today.w, today.h) == (72, 16)
    for y in range(16):
        for x in range(72):
            if not (7 <= x <= 64 and 4 <= y <= 11):
                assert f3.p[y][x] == today.p[y][x], ('meter frame differs from qte_meter_frame at', x, y)
    assert (meter['qte_meter3_fill'][0].w, meter['qte_meter3_fill'][0].h) == (58, 6)
    assert [x - MM.FILL_X for x in MM.WINDOWS] == [0, 21, 42]
    for x0 in (16, 37):                                    # the struts' columns in the fill stay clear
        for x in range(x0, x0 + 5):
            assert all(meter['qte_meter3_fill'][0].p[y][x] is None for y in range(6))
    assert all(len(r) == len(MM.BANKED_MS) == 4 for r in meter['qte_meter3_banked'])
    assert all((f.w, f.h) == (96, 40) for r in meter['qte_meter3_flash'] for f in r)
    for n in ('qte_tier_1', 'qte_tier_2', 'qte_tier_3'):
        assert all((f.w, f.h) == (40, 22) for f in stamps[n])
    assert all((f.w, f.h) == (160, 20) for f in stamps['knight_breaker'])
    # the dodge tell: the red badge's canvas, and Carter's ring untouched on every frame
    assert all((f.w, f.h) == (32, 24) for f in tell)
    for i, src in enumerate([DT.IGNITE, DT.PEAK] + [DT.HOLD] * 4):
        ring = DT.carter_cell(src)
        for y in range(24):
            for x in range(24):
                if ring.p[y][x] is not None:
                    assert tell[i].p[y + DT.OFFSET[1]][x + DT.OFFSET[0]] == ring.p[y][x], ('ring changed', i, x, y)
    for f in tell[2:]:                                     # the ring's body never changes in the loop
        for y in range(24):
            for x in range(24):
                ring_px = DT.carter_cell(DT.HOLD).p[y][x]
                if ring_px is not None:
                    assert f.p[y + DT.OFFSET[1]][x + DT.OFFSET[0]] == ring_px
    # the sword mark: the frame count and durations EricSwordMark steps through, and a ring that
    # never runs off its own canvas
    assert all((f.w, f.h) == (SM.TW, SM.TH) for f in mark)
    assert len(mark) == len(SM.DURATIONS_MS) == SM.CLOSE_FRAMES + 1 + len(SM.IMPACT) == 12
    for i, f in enumerate(mark):
        x0, y0, x1, y1 = bbox(f)
        assert 0 < x0 and x1 < SM.TW - 1 and 0 < y0 and y1 < SM.TH - 1, ('mark touches its edge', i)
    # the target ring stands still under the closing one, and is the only thing left on the commit frame
    fixed = SM.target(Canvas(SM.TW, SM.TH))
    for i in range(SM.CLOSE_FRAMES):
        for (x, y) in fixed:
            assert mark[i].p[y][x] is not None, ('target ring broken on', i, x, y)
    assert bbox(mark[SM.CLOSE_FRAMES])[0] > bbox(mark[SM.CLOSE_FRAMES - 1])[0]


def main():
    gauge = BG.build()
    meter = MM.build()
    stamps = TS.build()
    tell = DT.build()['dodge_tell']
    mark = SM.build()['eric_sword_mark']
    sanity(gauge, meter, stamps, tell, mark)

    # ---------------- Break gauge
    # These five overwrite the approved GOTHIC daze meter with the brass originals: what ships is
    # hud_bars/export_gothic.py's remap of exactly these frames. Re-run that after this one.
    ui_asset('break_gauge_frame', gauge['break_gauge_frame'], [100])
    ui_asset('break_gauge_fill', gauge['break_gauge_fill'], [100])
    ui_asset('break_gauge_pulse', gauge['break_gauge_pulse'], BG.PULSE_MS, [('throb', 1, 4)])
    ui_asset('break_gauge_fill_hot', gauge['break_gauge_fill_hot'], BG.PULSE_MS, [('throb', 1, 4)])
    ui_asset('break_gauge_shatter', gauge['break_gauge_shatter'], BG.SHATTER_MS, [('shatter', 1, 6)])
    ui_asset('break_text', gauge['break_text'], BG.TEXT_MS, [('pulse', 1, 2)])

    # ---------------- 3-bar mash meter
    ui_asset('qte_meter3_frame', meter['qte_meter3_frame'], [100])
    ui_asset('qte_meter3_fill', meter['qte_meter3_fill'], [100])
    bars = [('bar%d' % (b + 1), 1 + 4 * b, 4 + 4 * b) for b in range(3)]
    ui_sheet('qte_meter3_banked', meter['qte_meter3_banked'], MM.BANKED_MS * 3, bars)
    ui_sheet('qte_meter3_flash', meter['qte_meter3_flash'], MM.FLASH_MS * 3, bars)
    ui_asset('qte_meter3_full', meter['qte_meter3_full'], [80, 80], [('full', 1, 2)])

    # ---------------- stamps
    for t in (1, 2, 3):
        ui_asset('qte_tier_%d' % t, stamps['qte_tier_%d' % t], TS.TIER_MS, [('pulse', 1, 2)])
    ui_asset('knight_breaker', stamps['knight_breaker'], TS.KB_MS, [('pulse', 1, 2)])

    # ---------------- yellow dodge tell (world effect, 1x, next to parry_tell.png)
    s = strip(tell)
    emit(s, FX + 'dodge_tell.png')
    check_png(FX + 'dodge_tell.png', GOLD_SET, s)
    build_ase(FX + 'dodge_tell.aseprite', 32, 24, ['dodge_tell'], [[f] for f in tell], DT.DURATIONS_MS,
              [('appear', 1, 2), ('loop', 3, 6)])

    # ---------------- Eric's red sword landing mark (world effect, 1x, on the fight's floor layer)
    m = strip(mark)
    emit(m, FX + 'eric_sword_mark.png')
    check_png(FX + 'eric_sword_mark.png', SM.PALETTE, m)
    build_ase(FX + 'eric_sword_mark.aseprite', SM.TW, SM.TH, ['eric_sword_mark'], [[f] for f in mark],
              SM.DURATIONS_MS, [('close', 1, SM.CLOSE_FRAMES), ('commit', SM.CLOSE_FRAMES + 1, SM.CLOSE_FRAMES + 1),
                                ('impact', SM.CLOSE_FRAMES + 2, len(mark))])

    print('CHECK OK: the installed files match a fresh build byte for byte' if CHECK else
          'exported + verified into ' + ROOT)
    for rel in DELIVERABLES:
        print('  ', rel, os.path.getsize(target(rel)))


if __name__ == '__main__':
    main()
