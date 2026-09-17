"""Build, validate and export every uppercut-finisher asset, then build the .aseprite files (real frames,
layers, durations, tags) with Aseprite in batch mode and round-trip check them.

  python export_all.py                  write into the project; refuses to touch any existing file
  python export_all.py --overwrite-own  also allow overwriting the deliverables listed in DELIVERABLES
  python export_all.py --check          rebuild everything and compare with the files in the project (no writes)

Work files go to paths.WORK (outside the project)."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import *
from pngio import read_png
from paths import PROJ, ASEPRITE, work
import uppercut_build as UB
import impact as IM
import daze as DZ
import qte_ui as UI

CHECK = '--check' in sys.argv
OVERWRITE_OWN = '--overwrite-own' in sys.argv
TMP = work('ase_frames/')
os.makedirs(TMP, exist_ok=True)

UI_NAMES = ['qte_key_q', 'qte_key_w', 'qte_mash_text', 'qte_full_text', 'qte_meter_frame', 'qte_meter_fill',
            'qte_meter_full']
DELIVERABLES = (
    ['Assets/Characters/MainPlayer/player_uppercut.png', 'Assets/Characters/MainPlayer/player_uppercut.aseprite',
     'Assets/Effects/uppercut_impact.png', 'Assets/Effects/uppercut_impact.aseprite',
     'Assets/Effects/daze_stars.png', 'Assets/Effects/daze_stars.aseprite'] +
    ['Assets/UI/%s%s' % (n, ext) for n in UI_NAMES for ext in ('.png', '_3x.png', '.aseprite')])
DELIVERABLES = {PROJ + p for p in DELIVERABLES}

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


def lua_path():
    p = work('make_ase.lua')
    open(p, 'w').write(LUA)
    return p


def may_write(path):
    if CHECK:
        return False
    if os.path.exists(path) and not (OVERWRITE_OWN and path in DELIVERABLES):
        raise SystemExit('REFUSING to overwrite existing file ' + path)
    return True


def emit(canvas, path):
    if CHECK:
        disk = from_png(path)
        assert (disk.w, disk.h) == (canvas.w, canvas.h) and disk.p == canvas.p, 'differs from project: ' + path
        return
    may_write(path)
    canvas.save(path)


def scale3(c):
    o = Canvas(c.w * 3, c.h * 3)
    for y in range(o.h):
        for x in range(o.w):
            o.p[y][x] = c.p[y // 3][x // 3]
    return o


def check_png(path, allowed):
    w, h, px = read_png(path)
    assert {p[3] for row in px for p in row} <= {0, 255}, path
    cols = {'%02x%02x%02x' % p[:3] for row in px for p in row if p[3] == 255}
    assert cols <= allowed, (path, cols - allowed)


def build_ase(out_path, w, h, layer_names, frame_layers, durations, tags=()):
    key = os.path.splitext(os.path.basename(out_path))[0]
    target = out_path if not CHECK else work(key + '_check.aseprite')
    if not CHECK:
        may_write(out_path)
    lines = ['%s|%d|%d' % (target, w, h), ','.join(layer_names)]
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
    subprocess.run([ASEPRITE, '-b', '--script-param', 'spec=' + spec, '--script', lua_path()],
                   capture_output=True, text=True)
    assert os.path.exists(target), target
    comp = []
    for lays in frame_layers:
        c = Canvas(w, h)
        for l in lays:
            c.blit(l, 0, 0)
        comp.append(c)
    ref = strip(comp)
    for src in ([target, out_path] if CHECK else [target]):
        back = TMP + key + '_roundtrip.png'
        subprocess.run([ASEPRITE, '-b', src, '--sheet', back, '--sheet-type', 'horizontal'],
                       capture_output=True, text=True)
        rt = from_png(back)
        assert (rt.w, rt.h) == (ref.w, ref.h) and rt.p == ref.p, ('.aseprite round trip mismatch', src)


def main():
    # player_uppercut: body pixels only in the player's own palette, fx pixels only DB32
    frames, layers = UB.build_frames()
    assert len(frames) == 10 and all((f.w, f.h) == (48, 64) for f in frames)
    for i, (back, body, front) in enumerate(layers):
        assert body.colours() <= PLAYER_SET, i
        assert back.colours() <= DB32 and front.colours() <= DB32, i
    up = PROJ + 'Assets/Characters/MainPlayer/player_uppercut.png'
    emit(strip(frames), up)
    check_png(up, DB32 | PLAYER_SET)

    imp = IM.build()
    assert len(imp) == 6 and all((f.w, f.h) == (96, 96) for f in imp)
    ip = PROJ + 'Assets/Effects/uppercut_impact.png'
    emit(strip(imp), ip)
    check_png(ip, DB32)

    dz = DZ.build()
    assert len(dz) == 6 and all((f.w, f.h) == (48, 24) for f in dz)
    dp = PROJ + 'Assets/Effects/daze_stars.png'
    emit(strip(dz), dp)
    check_png(dp, DB32)

    ui = UI.build()
    assert set(ui) == set(UI_NAMES)
    assert not UI.check_nine_slice(ui['qte_meter_frame'][0], UI.ML, UI.MT, UI.MR, UI.MB)
    assert not UI.check_nine_slice(scale3(ui['qte_meter_frame'][0]), UI.ML * 3, UI.MT * 3, UI.MR * 3, UI.MB * 3)
    for name in UI_NAMES:
        s = strip(ui[name])
        p = PROJ + 'Assets/UI/%s.png' % name
        emit(s, p)
        check_png(p, DB32)
        p3 = PROJ + 'Assets/UI/%s_3x.png' % name
        emit(scale3(s), p3)
        check_png(p3, DB32)

    build_ase(up.replace('.png', '.aseprite'), 48, 64, ['fx_back', 'body', 'fx_front'], layers,
              UB.DURATIONS_MS, UB.TAGS)
    build_ase(ip.replace('.png', '.aseprite'), 96, 96, ['impact'], [[f] for f in imp],
              [40, 60, 60, 70, 80, 90], [('impact', 1, 6)])
    build_ase(dp.replace('.png', '.aseprite'), 48, 24, ['stars'], [[f] for f in dz], [100] * 6,
              [('daze_loop', 1, 6)])
    timing = {'qte_key_q': [100, 100], 'qte_key_w': [100, 100], 'qte_mash_text': [150, 150],
              'qte_full_text': [80, 80], 'qte_meter_frame': [100], 'qte_meter_fill': [100],
              'qte_meter_full': [80, 80]}
    for name in UI_NAMES:
        fr = ui[name]
        build_ase(PROJ + 'Assets/UI/%s.aseprite' % name, fr[0].w, fr[0].h, [name.replace('qte_', '')],
                  [[f] for f in fr], timing[name], [('pulse', 1, 2)] if len(fr) == 2 else [])
    print('CHECK OK: project files match a fresh build' if CHECK else 'exported + verified')


if __name__ == '__main__':
    main()
