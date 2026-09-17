"""Build, validate and export every defense / hype asset into the project, then build real multi-frame
.aseprite files (layers, frame durations, tags) with Aseprite in batch mode and round-trip check them.

  python export_all.py                  write into the project; refuses to overwrite any existing file
  python export_all.py --overwrite-own  also allow overwriting this script's own deliverables
  python export_all.py --check          rebuild everything and compare with the project files (no writes)
"""
import sys
sys.dont_write_bytecode = True
import subprocess
from dh_common import *
import stamina_ui as ST
import hype_ui as HY
import popups as PO
import fx_defense as FD
import fx_dodge as DG
import fx_super as FS
import player_guard_break as GB
import parry_tell as PT
import parry_streak as PK
import super_impact as SI

CHECK = '--check' in sys.argv
OVERWRITE_OWN = '--overwrite-own' in sys.argv
TMP = work('ase_frames/')
os.makedirs(TMP, exist_ok=True)

UI = 'Assets/UI/'
FX = 'Assets/Effects/'
PL = 'Assets/Characters/MainPlayer/'

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

DELIVERABLES = set()


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
    DELIVERABLES.add(path)
    if CHECK:
        disk = from_png(path)
        assert (disk.w, disk.h) == (canvas.w, canvas.h) and disk.p == canvas.p, 'differs from project: ' + path
        return
    may_write(path)
    canvas.save(path)


def check_png(path, allowed):
    w, h, px = read_png(path)
    assert {p[3] for row in px for p in row} <= {0, 255}, ('partial alpha', path)
    cols = {'%02x%02x%02x' % p[:3] for row in px for p in row if p[3] == 255}
    assert cols <= set(allowed), (path, cols - set(allowed))


def build_ase(out_path, w, h, layer_names, frame_layers, durations, tags=()):
    DELIVERABLES.add(out_path)
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
        if os.path.exists(back):
            os.remove(back)
        subprocess.run([ASEPRITE, '-b', src, '--sheet', back, '--sheet-type', 'horizontal'],
                       capture_output=True, text=True)
        rt = from_png(back)
        assert (rt.w, rt.h) == (ref.w, ref.h) and rt.p == ref.p, ('.aseprite round trip mismatch', src)


def ui_asset(name, frames, durations, tags=None):
    s = strip(frames)
    p = PROJ + UI + name + '.png'
    emit(s, p)
    check_png(p, DB32)
    p3 = PROJ + UI + name + '_3x.png'
    emit(scale3(s), p3)
    check_png(p3, DB32)
    if tags is None:
        tags = [('pulse' if len(frames) == 2 else 'loop', 1, len(frames))] if len(frames) > 1 else []
    build_ase(PROJ + UI + name + '.aseprite', frames[0].w, frames[0].h, [name], [[f] for f in frames],
              durations, tags)


def ui_sheet(name, rows, durations, tags):
    """UI asset whose PNG is a grid (rows x frames); the .aseprite gets every cell as a frame"""
    sheet = grid_sheet(rows)
    p = PROJ + UI + name + '.png'
    emit(sheet, p)
    check_png(p, DB32)
    emit(scale3(sheet), PROJ + UI + name + '_3x.png')
    check_png(PROJ + UI + name + '_3x.png', DB32)
    flat = [f for row in rows for f in row]
    build_ase(PROJ + UI + name + '.aseprite', flat[0].w, flat[0].h, [name], [[f] for f in flat], durations, tags)


def main():
    # ---------------- UI
    st = ST.build()
    fr = st['stamina_bar_frame'][0]
    assert (fr.w, fr.h) == (88, 15)
    assert not nine_slice_problems(fr, ST.ML, ST.MT, ST.MR, ST.MB)
    assert not nine_slice_problems(scale3(fr), ST.ML * 3, ST.MT * 3, ST.MR * 3, ST.MB * 3)
    ui_asset('stamina_bar_frame', st['stamina_bar_frame'], [100])
    ui_asset('stamina_bar_fill', st['stamina_bar_fill'], [100])
    ui_asset('stamina_bar_low', st['stamina_bar_low'], [120, 120], [('flash', 1, 2)])
    ui_asset('stamina_bar_broken', st['stamina_bar_broken'], [100, 100], [('flash', 1, 2)])

    hy = HY.build()
    assert (hy['hype_meter_frame'][0].w, hy['hype_meter_frame'][0].h) == (123, 42)
    ui_asset('hype_meter_frame', hy['hype_meter_frame'], [100])
    ui_asset('hype_meter_fill', hy['hype_meter_fill'], [100])
    ui_asset('hype_meter_full', hy['hype_meter_full'], [80, 80, 80, 80], [('full_loop', 1, 4)])
    ui_asset('hype_label', hy['hype_label'], [100, 100], [('normal', 1, 1), ('lit', 2, 2)])

    for name, frames in PO.build().items():
        ui_asset(name, frames, PO.DURATIONS_MS[name])

    streak = PK.popups()
    for name, frames in streak.items():
        ui_asset(name, frames, PK.POPUP_DURATIONS_MS[name])
    badge = PK.streak_badge()
    assert all((f.w, f.h) == (PK.BW, PK.BH) for row in badge for f in row)
    ui_sheet('streak_badge', badge, PK.BADGE_DURATIONS_MS * 3,
             [('streak_x1', 1, 4), ('streak_x2', 5, 8), ('streak_x3', 9, 12)])
    digits = PK.streak_digits()
    ui_asset('streak_digits', digits, [100] * 10, [('digits', 1, 10)])

    # ---------------- effects (1x only)
    fd = FD.build()
    specs = [('block_spark', fd['block_spark'], [40, 50, 60, 70], [('block', 1, 4)]),
             ('parry_flash', fd['parry_flash'], [30, 50, 60, 70, 80], [('parry', 1, 5)]),
             ('guard_break_stars', fd['guard_break_stars'], [100] * 6, [('dizzy_loop', 1, 6)]),
             ('uppercut_impact_super', FS.impact_super(), FS.IMPACT_DURATIONS_MS, [('impact', 1, 7)]),
             ('parry_tell', PT.parry_tell(), PT.TELL_DURATIONS_MS, [('tell_loop', 1, 6)]),
             ('parry_tell_strong', PT.parry_tell_strong(), PT.STRONG_DURATIONS_MS, [('tell_loop', 1, 6)]),
             ('parry_glow', PT.parry_glow(), PT.GLOW_DURATIONS_MS, [('glow_loop', 1, 4)]),
             ('parry_flash_strong', PK.parry_flash_strong(), PK.FLASH_DURATIONS_MS, [('parry_strong', 1, 7)]),
             ('parry_shatter', PK.parry_shatter(), PK.SHATTER_DURATIONS_MS, [('shatter', 1, 4)]),
             ('super_impact_rays', SI.super_impact_rays(), SI.RAY_DURATIONS_MS, [('rays', 1, 5)]),
             ('super_impact_ring', SI.super_impact_ring(), SI.RING_DURATIONS_MS, [('ring', 1, 6)])]
    for name, frames, durs, tags in specs:
        s = strip(frames)
        p = PROJ + FX + name + '.png'
        emit(s, p)
        check_png(p, DB32)
        build_ase(PROJ + FX + name + '.aseprite', frames[0].w, frames[0].h, [name], [[f] for f in frames], durs, tags)

    dodge = DG.build()                                  # 4 rows x 4 frames
    sheet = grid_sheet(dodge)
    p = PROJ + FX + 'perfect_dodge_trail.png'
    emit(sheet, p)
    check_png(p, DB32)
    flat = [f for row in dodge for f in row]
    names = ['down', 'up', 'left', 'right']
    build_ase(PROJ + FX + 'perfect_dodge_trail.aseprite', 32, 32, ['ghost'], [[f] for f in flat],
              DG.DURATIONS_MS * 4, [('ghost_' + n, 1 + 4 * i, 4 + 4 * i) for i, n in enumerate(names)])

    # ---------------- player
    frames, layers, durations, tags = FS.uppercut_super()
    assert len(frames) == 10 and all((f.w, f.h) == (48, 64) for f in frames)
    orig = from_png(PROJ + PL + 'player_uppercut.png')
    for i, (back, body, front) in enumerate(layers):
        assert body.colours() <= PLAYER_SET, i
        assert back.colours() <= DB32 and front.colours() <= DB32, i
    sup = strip(frames)
    assert (sup.w, sup.h) == (orig.w, orig.h)
    for y in range(sup.h):                              # only energy pixels may differ from the approved sheet
        for x in range(sup.w):
            if sup.p[y][x] != orig.p[y][x]:
                assert orig.p[y][x] in FS.ENERGY_MAP, ('non-energy pixel changed', x, y, orig.p[y][x])
            if orig.p[y][x] in PLAYER_SET:
                assert sup.p[y][x] == orig.p[y][x], ('body pixel changed', x, y)
    p = PROJ + PL + 'player_uppercut_super.png'
    emit(sup, p)
    check_png(p, DB32 | PLAYER_SET)
    build_ase(PROJ + PL + 'player_uppercut_super.aseprite', 48, 64, ['fx_back', 'body', 'fx_front'], layers,
              durations, tags)

    gb = GB.build()                                      # 4 rows x 3 frames
    sheet = grid_sheet(gb)
    assert sheet.colours() <= PLAYER_SET
    p = PROJ + PL + 'player_guard_break.png'
    emit(sheet, p)
    check_png(p, PLAYER_SET)
    flat = [f for row in gb for f in row]
    build_ase(PROJ + PL + 'player_guard_break.aseprite', 32, 32, ['body'], [[f] for f in flat],
              GB.DURATIONS_MS * 4, [('guard_break_' + n, 1 + 3 * i, 3 + 3 * i) for i, n in enumerate(names)])
    print('CHECK OK: project files match a fresh build' if CHECK else 'exported + verified')
    for d in sorted(DELIVERABLES):
        print('  ', d.replace(PROJ, ''))


if __name__ == '__main__':
    main()
