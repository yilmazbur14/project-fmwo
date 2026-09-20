"""Build, check and optionally install Eric's Broken / Juggle / Winded art.

    python build.py <out_dir> [--install] [--no-previews]

<out_dir>/png/<sheet>.png             horizontal strips (what ships)
<out_dir>/aseprite/<sheet>.aseprite   multi-frame sources (one layer, frame durations, tags) built by
                                      Aseprite in batch mode; each is exported back with --sheet and must
                                      match its PNG pixel for pixel
<out_dir>/gifs/*.gif                  previews (3x on the mat green; broken synced with the sword; the
                                      juggle replayed in context with the plan's tier-3 lift, shadow and shove)
<out_dir>/contact_sheet.png           every frame, labelled, with its duration
<out_dir>/points.json                 measured anchors, head / grip / sword / crater points, timings
--install                             copies the .png/.aseprite pairs into Assets/Characters/Eric/ after all
                                      checks pass; refuses to overwrite anything that is not one of them
"""
import os
import sys
import json
import shutil
import subprocess

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw, ImageFont   # noqa: E402

import sheets as SH                            # noqa: E402
import frames as F                             # noqa: E402
import keys as K                               # noqa: E402
import body                                    # noqa: E402

ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
ASSETS = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/'
ERIC = ASSETS + 'Characters/Eric/'
MAT = (0x7e, 0xa8, 0x5b, 255)
OWN = ['eric_broken', 'eric_broken_sword', 'eric_juggle', 'eric_winded', 'eric_crash_crater']

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
local spr = Sprite(W, H, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = lines[2]
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
  spr:newCel(layer, frame, Image{ fromFile = parts[2] }, Point(0, 0))
end
for _, tl in ipairs(tagLines) do
  local parts = split(tl, "|")
  local tag = spr:newTag(tonumber(parts[3]), tonumber(parts[4]))
  tag.name = parts[2]
end
spr:saveAs(outPath)
spr:close()
'''


def run_aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('aseprite failed %s\n%s\n%s' % (args, r.stdout, r.stderr))
    return r


def same_pixels(a, b):
    if a.size != b.size:
        return False, 'size %s vs %s' % (a.size, b.size)
    pa, pb = a.convert('RGBA').load(), b.convert('RGBA').load()
    bad = 0
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            p, q = pa[x, y], pb[x, y]
            if p[3] == 0 and q[3] == 0:
                continue
            if p != q:
                bad += 1
    return bad == 0, '%d differing pixels' % bad


def build_ase(name, frames, durations, tags, out_ase, work):
    os.makedirs(work, exist_ok=True)
    lua = os.path.join(work, 'make_ase.lua')
    open(lua, 'w', newline='\n').write(LUA)
    w, h = frames[0].size
    lines = ['%s|%d|%d' % (out_ase.replace('\\', '/'), w, h), name]
    for i, (f, d) in enumerate(zip(frames, durations)):
        fp = os.path.join(work, '%s_f%02d.png' % (name, i)).replace('\\', '/')
        f.save(fp)
        lines.append('%d|%s' % (d, fp))
    for tname, a, b in tags:
        lines.append('TAG|%s|%d|%d' % (tname, a + 1, b + 1))
    spec = os.path.join(work, name + '_spec.txt')
    open(spec, 'w', newline='\n').write('\n'.join(lines) + '\n')
    if os.path.exists(out_ase):
        os.remove(out_ase)
    run_aseprite('--script-param', 'spec=' + spec.replace('\\', '/'), '--script', lua.replace('\\', '/'))
    assert os.path.exists(out_ase), out_ase
    back = os.path.join(work, name + '_roundtrip.png')
    if os.path.exists(back):
        os.remove(back)
    run_aseprite(out_ase.replace('\\', '/'), '--sheet', back.replace('\\', '/'), '--sheet-type', 'horizontal')
    ok, why = same_pixels(Image.open(back), SH.strip(frames))
    return ok, why


# ------------------------------------------------------------------ measurements
def fist_centre(x, y):
    # rig2.fist: the 11x10 vertical fist stamp is placed at (round(x) - 5, round(y) - 5)
    return (round(x) - 5 + 5.0, round(y) - 5 + 4.5)


def measure(frames_by_sheet):
    pts = {}
    lows = {}
    for n, frs in frames_by_sheet.items():
        lows[n] = [f.getbbox()[3] - 1 if f.getbbox() else None for f in frs]
    pts['lowest_row_per_frame'] = lows
    heads = {}
    for i in (3, 4, 5, 6, 7):
        pose = F.BROKEN[i]()
        fr, L = body.render(pose)
        heads[i] = K.head_pixel(L['head'])
    pts['broken_head_crowns'] = {str(k): v for k, v in heads.items()}
    sl = [heads[i] for i in (5, 6, 7)]
    pts['BROKEN_HEAD_PIXEL'] = (round(sum(p[0] for p in sl) / 3.0), round(sum(p[1] for p in sl) / 3.0))
    pts['KNEEL_HEAD_PIXEL'] = (round((heads[3][0] + heads[4][0]) / 2.0), round((heads[3][1] + heads[4][1]) / 2.0))
    k4 = F.broken_4()['arms']['L']
    pts['kneel_grip_fist_centre_f4'] = fist_centre(k4['wrist'][0] + k4.get('hdx', 0), k4['wrist'][1] + k4.get('hdy', 0))
    k3 = F.broken_3()['arms']['L']
    pts['kneel_reaching_wrist_f3'] = k3['wrist']
    wg = []
    for fn in F.WINDED:
        a = fn()['arms']['L']
        wg.append(fist_centre(a['wrist'][0] + a.get('hdx', 0), a['wrist'][1] + a.get('hdy', 0)))
    pts['winded_grip_fist_centres'] = wg
    sw = frames_by_sheet['eric_broken_sword'][6]
    bb = sw.getbbox()
    pts['planted_sword'] = dict(blade_axis_x=F.PLANT_X, guard_centre=(F.PLANT_X, F.PLANT_GUARD_Y),
                                mat_entry_row=F.MOUND_GROUND, pommel_top_row=bb[1], hold_bbox=bb,
                                grip_rows=(F.PLANT_GUARD_Y - 29, F.PLANT_GUARD_Y - 5))
    # crash impact: where his crown meets the mat on juggle 6
    fr, L = body.render(F.juggle_frame(6))
    head = L['head']
    low = F.lowest_row(head)
    xs = [x for x in range(256) if head.px[low][x] is not None]
    pts['crash_impact_point'] = (round((min(xs) + max(xs)) / 2.0), low)
    pts['CRATER_PIVOT'] = (64, 25)
    pts['tumble_centre'] = F.TUMBLE_C
    pts['durations_ms'] = {n: SH.SHEETS[n]['durations'] for n in SH.SHEETS}
    pts['tags'] = {n: SH.SHEETS[n]['tags'] for n in SH.SHEETS}
    return pts


# ------------------------------------------------------------------ previews
def on_mat(img, scale=3, bg=MAT):
    b = Image.new('RGBA', img.size, bg)
    b.alpha_composite(img)
    return b.resize((img.size[0] * scale, img.size[1] * scale), Image.NEAREST)


def save_gif(path, frames, durations):
    """exact-colour GIF: one shared palette built from every frame's colours"""
    cols = {}
    rgb = [f.convert('RGB') for f in frames]
    for f in rgb:
        for c in f.getcolors(1 << 24) or []:
            cols[c[1]] = 1
    assert len(cols) <= 256, ('too many colours for a GIF', len(cols))
    pal = sorted(cols)
    pim = Image.new('P', (1, 1))
    flat = [v for c in pal for v in c] + [0] * (768 - 3 * len(pal))
    pim.putpalette(flat)
    ps = [f.quantize(palette=pim, dither=Image.Dither.NONE) for f in rgb]
    ps[0].save(path, save_all=True, append_images=ps[1:], duration=durations, loop=0, optimize=False,
               disposal=1)


def comp(canvas, img, x, y):
    """alpha_composite that accepts offsets partly outside the canvas"""
    x, y = int(x), int(y)
    sx, sy = max(0, -x), max(0, -y)
    w = min(img.size[0], canvas.size[0] - x) - sx
    h = min(img.size[1], canvas.size[1] - y) - sy
    if w <= 0 or h <= 0:
        return
    canvas.alpha_composite(img.crop((sx, sy, sx + w, sy + h)), (x + sx, y + sy))


def stars_frames():
    im = Image.open(ASSETS + 'Effects/daze_stars.png').convert('RGBA')
    return [im.crop((i * 48, 0, i * 48 + 48, 24)) for i in range(6)]


def timeline(durations, t, loop_from=None):
    """frame index of a strip at time t (ms); loops from `loop_from` after the end"""
    acc = 0
    for i, d in enumerate(durations):
        if t < acc + d:
            return i
        acc += d
    if loop_from is None:
        return len(durations) - 1
    period = sum(durations[loop_from:])
    t2 = (t - acc) % period
    acc = 0
    for i in range(loop_from, len(durations)):
        if t2 < acc + durations[i]:
            return i
        acc += durations[i]
    return len(durations) - 1


def gif_broken(frs, sword, path, head_px):
    """reel -> kneel -> slumped loop, with the sword sprite synced behind him and the daze stars on"""
    bd = SH.SHEETS['eric_broken']['durations']
    sd = SH.SHEETS['eric_broken_sword']['durations']
    stars = stars_frames()
    out, durs = [], []
    t, step, total = 0, 20, sum(bd[:5]) + 3 * sum(bd[5:])
    while t < total:
        b = timeline(bd, t, loop_from=5)
        s = timeline(sd, t)
        c = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
        c.alpha_composite(sword[s])
        c.alpha_composite(frs[b])
        if b >= 5:
            st = stars[(t // 100) % 6]
            c.alpha_composite(st, (int(head_px[0] - 24), int(head_px[1] - 13)))
        out.append(on_mat(c))
        durs.append(step)
        t += step
    save_gif(path, out, durs)


def gif_strip(frs, durations, path, loops=1, loop_from=0, tail_ms=0):
    out, durs = [], []
    order = list(range(len(frs)))
    seq = order[:loop_from] + order[loop_from:] * loops
    for i in seq:
        out.append(on_mat(frs[i], 3 if frs[0].size[0] > 200 else 5))
        durs.append(durations[i])
    if tail_ms:
        durs[-1] += tail_ms
    save_gif(path, out, durs)


def gif_juggle_context(juggle, sword, crater, path):
    """the plan's tier-3 juggle replayed on the mat: three uppercuts 0.55 s apart with hit-stops 0.10 /
    0.10 / 0.35 s, lifts from section 3.5 (gravity 2900 px/s^2), the last hit's 240 px shove, the leap
    shadow at 35%, the sword left planted where the Break happened and the crater where he lands."""
    shadow = Image.open(ERIC + 'eric_leap_shadow.png').convert('RGBA')
    shf = [shadow.crop((i * 48, 0, i * 48 + 48, 16)) for i in range(3)]
    for i, s in enumerate(shf):
        px = s.load()
        for y in range(s.size[1]):
            for x in range(s.size[0]):
                if px[x, y][3]:
                    px[x, y] = (0, 0, 0, 89)
    jd = SH.SHEETS['eric_juggle']['durations']
    cd = SH.SHEETS['eric_crash_crater']['durations']
    G = 2900.0
    arcs = [(0.0, 980.0, 0.55, 0.10), (100.0, 800.0, 0.55, 0.10), (100.0, 1100.0, None, 0.35)]
    W, H, S = 440, 214, 2
    base_x, feet_y = 100, 206          # frame origin (texels) of the Break spot; feet row in the canvas
    events = []                        # (t_ms, kind, data)
    t = 400.0                          # a moment of the slumped loop first
    for k, (h0, v0, dur, stop) in enumerate(arcs):
        events.append((t, 'stop', (h0, stop, k)))
        t += stop * 1000
        if dur is None:
            disc = v0 * v0 + 2 * G * h0
            dur = (v0 + disc ** 0.5) / G
        events.append((t, 'arc', (h0, v0, dur, k)))
        t += dur * 1000
    land = t
    frames_out, durs = [], []
    step = 20
    T = 0.0
    end = land + 280 + 1200
    broken = SH.render_frames('eric_broken')
    while T < end:
        c = Image.new('RGBA', (W * 1, H * 1), MAT)
        # decide Eric's state
        lift_px, shove_px, jf, pre = 0.0, 0.0, None, False
        if T < events[0][0]:
            pre = True
        else:
            for et, kind, data in events:
                if T >= et:
                    cur = (et, kind, data)
            et, kind, data = cur
            k = data[-1]
            if kind == 'stop':
                lift_px = data[0]
                jf = 0
                shove_px = 0.0
            else:
                h0, v0, dur, k = data
                tt = (T - et) / 1000.0
                lift_px = max(0.0, h0 + v0 * tt - 0.5 * G * tt * tt)
                shove_px = 240.0 * min(1.0, tt / dur) if k == 2 else 0.0
                seg = (T - et)
                jd_hit = jd[0] + jd[1]
                if seg < jd[0]:
                    jf = 0
                elif seg < jd_hit:
                    jf = 1
                else:
                    jf = 2 + int((seg - jd_hit) // jd[2]) % 4
            if T >= land:
                lift_px, shove_px = 0.0, 240.0
                d = T - land
                jf = 6 if d < jd[6] else 7 if d < jd[6] + jd[7] else 8 if d < jd[6] + jd[7] + jd[8] else 9
        ox = base_x + shove_px / 3.0
        oy = feet_y - 191
        # crater under the landing spot
        if T >= land:
            ci = timeline(cd, T - land)
            comp(c, crater[ci], round(ox + 128 - 64), oy + 191 - 25)
        # the sword stays where it was planted
        comp(c, sword[6], base_x, oy)
        if pre:
            bi = timeline(SH.SHEETS['eric_broken']['durations'][5:], T % 480)
            comp(c, broken[5 + bi], base_x, oy)
        else:
            if lift_px > 0.5 and T < land:
                si = min(2, int(lift_px / 100.0))
                comp(c, shf[si], round(ox + 128 - 24), oy + 189 - 8)
            comp(c, juggle[jf], round(ox), round(oy - lift_px / 3.0))
        frames_out.append(c.resize((W * S, H * S), Image.NEAREST))
        durs.append(step)
        T += step
    save_gif(path, frames_out, durs)


def contact_sheet(frames_by_sheet, path, sword_sync):
    try:
        font = ImageFont.load_default(size=18)
        small = ImageFont.load_default(size=14)
    except TypeError:
        font = small = ImageFont.load_default()
    rows = [('eric_broken', 'eric_broken.png  (8 x 256x192)  reel 0-2, kneel 3-4, slumped loop 5-7'),
            ('broken+sword', 'eric_broken over eric_broken_sword, synced as they play in game'),
            ('eric_broken_sword', 'eric_broken_sword.png  (7 x 256x192)  plunge 0-3, wobble 4-5, planted 6'),
            ('eric_juggle', 'eric_juggle.png  (10 x 256x192)  hit 0-1, tumble loop 2-5, crash 6-7, bounce 8, lying 9'),
            ('eric_winded', 'eric_winded.png  (4 x 256x192)  panting loop'),
            ('eric_crash_crater', 'eric_crash_crater.png  (4 x 128x48)  flash, crack, settle, held')]
    s = 2
    cellw = 256 * s
    pad = 8
    head = 26
    lab = 18
    maxn = 10
    Wd = pad + maxn * (cellw + pad)
    hts = []
    for key, _ in rows:
        fh = 48 * 3 if key == 'eric_crash_crater' else 192 * s
        hts.append(fh)
    Ht = pad + sum(head + lab + h + pad for h in hts)
    sheet = Image.new('RGBA', (Wd, Ht), (30, 30, 34, 255))
    d = ImageDraw.Draw(sheet)
    y = pad
    for (key, title), fh in zip(rows, hts):
        d.text((pad, y), title, fill=(255, 230, 120, 255), font=font)
        y += head
        if key == 'broken+sword':
            frs = sword_sync
            durs = SH.SHEETS['eric_broken']['durations']
        else:
            frs = frames_by_sheet[key]
            durs = SH.SHEETS[key]['durations']
        for i, f in enumerate(frs):
            x = pad + i * (cellw + pad)
            img = on_mat(f, 3 if key == 'eric_crash_crater' else s)
            if key == 'eric_crash_crater':
                x += (cellw - img.size[0]) // 2
            d.text((pad + i * (cellw + pad) + 2, y), 'f%d  %d ms' % (i, durs[i]), fill=(220, 220, 220, 255),
                   font=small)
            sheet.paste(img, (x, y + lab))
        y += lab + fh + pad
    sheet.save(path)


# ------------------------------------------------------------------ main
def main():
    out = os.path.abspath(sys.argv[1])
    install = '--install' in sys.argv
    previews = '--no-previews' not in sys.argv
    for sub in ('png', 'aseprite', 'gifs', 'work'):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    frames_by_sheet = {}
    report = {}
    all_ok = True
    for n in SH.SHEETS:
        frs = SH.render_frames(n)
        frames_by_sheet[n] = frs
        spec = SH.SHEETS[n]
        png = os.path.join(out, 'png', n + '.png')
        SH.strip(frs).save(png)
        alphas = set()
        for f in frs:
            alphas |= set(f.getchannel('A').getdata())
        ok_alpha = alphas <= {0, 255}
        ase = os.path.join(out, 'aseprite', n + '.aseprite')
        ok_rt, why = build_ase(n, frs, spec['durations'], spec['tags'], ase, os.path.join(out, 'work'))
        report[n] = dict(frames=len(frs), size=frs[0].size, hard_alpha=ok_alpha, aseprite_roundtrip=ok_rt,
                         detail=why)
        all_ok &= ok_alpha and ok_rt
        print('%-18s %2d x %s  alpha 0/255: %s  .aseprite -> png pixel-identical: %s (%s)' %
              (n, len(frs), frs[0].size, ok_alpha, ok_rt, why))
    pts = measure(frames_by_sheet)
    json.dump(dict(checks=report, points=pts), open(os.path.join(out, 'points.json'), 'w'), indent=1,
              default=list)
    if previews:
        sw = frames_by_sheet['eric_broken_sword']
        bd = SH.SHEETS['eric_broken']['durations']
        sd = SH.SHEETS['eric_broken_sword']['durations']
        sync, acc = [], 0
        for i, f in enumerate(frames_by_sheet['eric_broken']):
            c = Image.new('RGBA', f.size, (0, 0, 0, 0))
            c.alpha_composite(sw[timeline(sd, acc)])
            c.alpha_composite(f)
            sync.append(c)
            acc += bd[i]
        contact_sheet(frames_by_sheet, os.path.join(out, 'contact_sheet.png'), sync)
        g = os.path.join(out, 'gifs')
        gif_broken(frames_by_sheet['eric_broken'], sw, os.path.join(g, 'eric_broken_with_sword.gif'),
                   pts['BROKEN_HEAD_PIXEL'])
        gif_strip(sw, sd, os.path.join(g, 'eric_broken_sword.gif'), tail_ms=600)
        gif_strip(frames_by_sheet['eric_juggle'], SH.SHEETS['eric_juggle']['durations'],
                  os.path.join(g, 'eric_juggle_frames.gif'), loops=1, loop_from=10, tail_ms=600)
        jf = frames_by_sheet['eric_juggle']
        jd = SH.SHEETS['eric_juggle']['durations']
        seq = [0, 1] + [2, 3, 4, 5] * 3
        gif_strip([jf[i] for i in seq], [jd[i] for i in seq], os.path.join(g, 'eric_juggle_tumble_loop.gif'))
        gif_juggle_context(jf, sw, frames_by_sheet['eric_crash_crater'],
                           os.path.join(g, 'eric_juggle_in_context_tier3.gif'))
        gif_strip(frames_by_sheet['eric_winded'], SH.SHEETS['eric_winded']['durations'],
                  os.path.join(g, 'eric_winded.gif'), loops=4)
        gif_strip(frames_by_sheet['eric_crash_crater'], SH.SHEETS['eric_crash_crater']['durations'],
                  os.path.join(g, 'eric_crash_crater.gif'), tail_ms=400)
    if install:
        if not all_ok:
            raise SystemExit('checks failed: not installing')
        for n in OWN:
            for ext, src in (('.png', os.path.join(out, 'png', n + '.png')),
                             ('.aseprite', os.path.join(out, 'aseprite', n + '.aseprite'))):
                dst = ERIC + n + ext
                shutil.copyfile(src, dst)
                print('installed', dst)
    print('ALL CHECKS PASSED' if all_ok else 'CHECKS FAILED')


if __name__ == '__main__':
    main()
