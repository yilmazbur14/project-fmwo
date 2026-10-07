"""Gun-hand previews: three 1920x1080 mocks on a real capture of Josh's Wild Cards warning (5 clones and
their lanes, the gates, the HUD, the player; the resting hands hidden) and a GIF of the whole layer on
the addendum's clock: OUT 0.40 (gun_form while flying to the posts), SWEEP 1.50, STOP + CHARGE 1.00
(telegraph + yellow badge), FIRE 0.35, FADE 0.20, BACK 0.50 (gun_form reversed, flying home).
Posts and rows are computed from this art's GUN_BOX_TEXELS by the plan's rules (jh_gun_sheets)."""
import math
import os

from PIL import Image, ImageDraw

import jh_lib as H
import jh_anims as A
import jh_gun as GN
import jh_beam as B
import jh_gun_sheets as GS

ROOT = H.ROOT
CAP = os.path.join(H.SCRATCH, 'cap_gun')
S3 = 3
PLAYER_BODY = (900, 600)                     # where the capture's player stands
REST = {'left': (575, 440), 'right': (1345, 440)}
TELE_FILL = (0xC2, 0x28, 0x3A)
TELE_RIM = (0xE8, 0x60, 0x5A)
TELE_FLASH = (0xFF, 0xF3, 0xB0)

_cache = {}


def asset(name):
    if name in _cache:
        return _cache[name]
    if name == 'bg':
        im = Image.open(os.path.join(CAP, 'wild_bg.png')).convert('RGBA')
    elif name == 'player':
        bg = Image.open(os.path.join(CAP, 'wild_bg.png')).convert('RGBA')
        pl = Image.open(os.path.join(CAP, 'wild_player.png')).convert('RGBA')
        box = (PLAYER_BODY[0] - 60, PLAYER_BODY[1] - 60, PLAYER_BODY[0] + 60, PLAYER_BODY[1] + 60)
        a, b = bg.crop(box), pl.crop(box)
        out = Image.new('RGBA', a.size, (0, 0, 0, 0))
        pa, pb, po = a.load(), b.load(), out.load()
        for y in range(a.height):
            for x in range(a.width):
                if pa[x, y][:3] != pb[x, y][:3]:
                    po[x, y] = pb[x, y]
        im = (out, (box[0], box[1]))
    elif name == 'dodge':
        t = Image.open(os.path.join(ROOT, 'Assets', 'Effects', 'dodge_tell.png')).convert('RGBA')
        im = [t.crop((i * 32, 0, i * 32 + 32, 24)) for i in range(6)]
    else:
        raise KeyError(name)
    _cache[name] = im
    return im


def frames_of(clip):
    key = ('gun', clip)
    if key not in _cache:
        out = []
        for i, fr in enumerate(GN.clip_frames(clip)):
            px, gl = GN.render_any(clip, fr, i)
            out.append((H.to_image(px, GN.FW, GN.FH), H.to_image(gl, GN.FW, GN.FH, H.GLOW)))
        _cache[key] = out
    return _cache[key]


def hover_frames():
    if 'hover' not in _cache:
        out = []
        for fr in A.clip_frames('hover'):
            px, gl = A.render_frame(fr)
            out.append((H.to_image(px, A.FW, A.FH), H.to_image(gl, A.FW, A.FH, H.GLOW)))
        _cache['hover'] = out
    return _cache['hover']


def fx_frames(name):
    if name not in _cache:
        if name == 'flash':
            _cache[name] = [H.to_image(f, 48, 48) for f in B.flash_frames()]
        elif name == 'charge':
            _cache[name] = [H.to_image(f, 32, 32) for f in B.charge_frames()]
        elif name == 'beam':
            _cache[name] = dict(start=[H.to_image(f, 16, 20) for f in B.start_frames()],
                                tile=[H.to_image(f, 16, 20) for f in B.tile_frames()],
                                end=[H.to_image(f, 16, 20) for f in B.end_frames()],
                                glow=[H.to_image(f, 16, 32, H.GLOW) for f in B.glow_frames()])
    return _cache[name]


def big(im, flip=False):
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((im.width * S3, im.height * S3), Image.NEAREST)


def paste(canvas, im, x0, y0):
    x0, y0 = int(round(x0)), int(round(y0))
    cx0, cy0 = max(0, -x0), max(0, -y0)
    if cx0 >= im.width or cy0 >= im.height:
        return
    canvas.alpha_composite(im.crop((cx0, cy0, im.width, im.height)), (x0 + cx0, y0 + cy0))


def draw_at(canvas, im, pivot, at, flip=False, glow=None, alpha=1.0):
    w = im.width
    px_ = (w - pivot[0]) if flip else pivot[0]
    x0 = at[0] - px_ * S3
    y0 = at[1] - pivot[1] * S3
    if glow is not None:
        canvas = H.add_glow(canvas, big(glow, flip), (int(round(x0)), int(round(y0))))
    b = big(im, flip)
    if alpha < 1.0:
        a = b.getchannel('A').point(lambda v: int(v * alpha))
        b.putalpha(a)
    paste(canvas, b, x0, y0)
    return canvas


def draw_hand(canvas, pair, node, side):
    im, gl = pair
    return draw_at(canvas, im, (GN.PX, GN.PY), node, flip=(side == 'left'), glow=gl)


def muzzle_world(node, side):
    dx = (GN.MUZZLE[0] - GN.PX) * S3
    return (node[0] - dx, node[1]) if side == 'left' else (node[0] + dx, node[1])


def draw_player(canvas, body=PLAYER_BODY):
    cut, xy = asset('player')
    paste(canvas, cut, xy[0] + body[0] - PLAYER_BODY[0], xy[1] + body[1] - PLAYER_BODY[1])
    return canvas


def draw_telegraph(canvas, side, row, alpha, flash=False):
    """The code's telegraph, drawn here as the plan describes it: a crimson fill over the band and a rim
    of salmon on its two edges, from the muzzle to the far rope; white on the last 0.10 s."""
    pr = GS.posts_and_ranges(GS.gun_box())
    x0, x1 = pr['beam'][side]
    y0, y1 = int(row - 30), int(row + 30)
    over = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    fill = TELE_FLASH if flash else TELE_FILL
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill + (int(255 * alpha),))
    rim = TELE_FLASH if flash else TELE_RIM
    d.rectangle((x0, y0, x1 - 1, y0 + 2), fill=rim + (255,))
    d.rectangle((x0, y1 - 3, x1 - 1, y1 - 1), fill=rim + (255,))
    canvas.alpha_composite(over)
    return canvas


def draw_beam(canvas, side, row, f, alpha=1.0, glow=True):
    """start at the muzzle, tiles to the far rope, the end cap splashing on it (texels 3 px)."""
    pr = GS.posts_and_ranges(GS.gun_box())
    beam = fx_frames('beam')
    x_near = pr['muzzle_x'][side]
    x_far = 100 if side == 'right' else 1820
    y0 = row - 30
    flip = (side == 'left')
    pieces = []
    if side == 'right':
        pieces.append(('start', x_near - 48))
        x = x_near - 48
        while x - 48 > x_far + 48 - 1:
            x -= 48
            pieces.append(('tile', x))
        pieces.append(('end', x_far))
        # the gap between the last tile and the end cap, filled with one more tile clipped by the cap
        pieces.insert(-1, ('tile', x_far + 48 - 1 - 47 + 47))
    else:
        pieces.append(('start', x_near))
        x = x_near
        while x + 96 < x_far - 48 + 1:
            x += 48
            pieces.append(('tile', x))
        pieces.append(('tile', x_far - 96))
        pieces.append(('end', x_far - 48))
    if glow:
        for kind, x in pieces:
            canvas = H.add_glow(canvas, big(beam['glow'][f], flip), (int(x), int(y0 - 18)))
    for kind, x in pieces:
        b = big(beam[kind][f], flip)
        if alpha < 1.0:
            b.putalpha(b.getchannel('A').point(lambda v: int(v * alpha)))
        paste(canvas, b, x, y0)
    return canvas


def draw_badge(canvas, anchor, t):
    frames = asset('dodge')
    k = 2 + int(t / 0.11) % 4 if t > 0.09 else (0 if t < 0.05 else 1)
    im = frames[k].resize((96, 72), Image.NEAREST)
    paste(canvas, im, anchor[0] - 16 * S3, anchor[1] - 24 * S3)
    return canvas


def label(canvas, text, xy=(14, 6)):
    d = ImageDraw.Draw(canvas)
    d.rectangle((xy[0] - 6, xy[1] - 4, xy[0] + 7 * len(text) + 6, xy[1] + 16), fill=(0, 0, 0, 200))
    d.text(xy, text, fill=(255, 255, 255, 255))
    return canvas


def rows_for(center_y):
    """choose_rows() as the plan writes it, for the capture's player (the far hand aims)."""
    pr = GS.posts_and_ranges(GS.gun_box())
    aimer = 'right' if PLAYER_BODY[0] < 959 else 'left'
    other = 'left' if aimer == 'right' else 'right'
    lo, hi = pr['row_range'][aimer]
    aimed = min(max(center_y, lo), hi)
    sign = -1 if (aimed - 114) > (967 - aimed) else 1
    lo2, hi2 = pr['row_range'][other]
    cut = min(max(aimed + sign * 220, lo2), hi2)
    if abs(cut - aimed) < 141:
        cut = min(max(aimed - sign * 220, lo2), hi2)
    return {aimer: aimed, other: cut}, aimer


def nodes(rows):
    pr = GS.posts_and_ranges(GS.gun_box())
    return {s: (pr['node'][s], rows[s]) for s in ('left', 'right')}


# ------------------------------------------------------------------ the mocks

def mock_sweep():
    c = asset('bg').copy()
    c = draw_player(c)
    n = nodes({'left': 300, 'right': 700})
    for side in ('left', 'right'):
        c = draw_hand(c, frames_of('gun_idle')[0 if side == 'left' else 2], n[side], side)
    pr = GS.posts_and_ranges(GS.gun_box())
    return label(c, 'GUN MOCK 1 - SWEEP: posts x %d / %d (muzzles %d / %d), rows sweeping in opposite directions (here 300 and 700); '
                    'Wild Cards clones and lanes behind' % (pr['node']['left'], pr['node']['right'],
                                                            pr['muzzle_x']['left'], pr['muzzle_x']['right']))


def mock_charge():
    c = asset('bg').copy()
    rows, aimer = rows_for(PLAYER_BODY[1] + 1.5)
    for side in ('left', 'right'):
        c = draw_telegraph(c, side, rows[side], 0.25)
    c = draw_player(c)
    n = nodes(rows)
    for side in ('left', 'right'):
        c = draw_hand(c, frames_of('gun_charge')[2], n[side], side)
        m = muzzle_world(n[side], side)
        c = draw_at(c, fx_frames('charge')[2 if side == 'left' else 4], (16, 16), m, flip=(side == 'left'))
    c = draw_badge(c, (PLAYER_BODY[0], rows[aimer] - 30), 0.3)
    return label(c, 'GUN MOCK 2 - CHARGE: the %s hand aims at the player (row %d), the other cuts off row %d; '
                    'telegraph = crimson band (fill 0.25) + salmon rims, yellow dodge badge on the aimed band'
                 % (aimer, rows[aimer], rows['left' if aimer == 'right' else 'right']))


def mock_fire():
    c = asset('bg').copy()
    rows, aimer = rows_for(PLAYER_BODY[1] + 1.5)
    body = (PLAYER_BODY[0], PLAYER_BODY[1] + 92)          # stepped down out of the band
    c = draw_player(c, body)
    for side in ('left', 'right'):
        c = draw_beam(c, side, rows[side], 1)
    n = nodes(rows)
    for side in ('left', 'right'):
        c = draw_hand(c, frames_of('gun_fire')[1], n[side], side)
        m = muzzle_world(n[side], side)
        c = draw_at(c, fx_frames('flash')[1], (24, 24), m, flip=(side == 'left'))
    return label(c, 'GUN MOCK 3 - FIRE: both beams live (20 texels = the 60 px band), recoil + muzzle flash; '
                    'the player stepped out of the band')


# ------------------------------------------------------------------ the GIF

def _at(times, t, loop=False):
    total = sum(times)
    if loop:
        t = t % total
    acc = 0.0
    for i, d in enumerate(times):
        acc += d
        if t < acc - 1e-9:
            return i
    return len(times) - 1


def gif(path, dt=0.05, downscale=True):
    pr = GS.posts_and_ranges(GS.gun_box())
    rows, aimer = rows_for(PLAYER_BODY[1] + 1.5)
    mids = {s: (pr['row_range'][s][0] + pr['row_range'][s][1]) / 2.0 for s in ('left', 'right')}
    amps = {s: 0.8 * (pr['row_range'][s][1] - pr['row_range'][s][0]) / 2.0 for s in ('left', 'right')}
    phi = {'left': 0.0, 'right': math.pi}
    bg = asset('bg')
    frames, durs = [], []
    T_OUT, T_SWEEP, T_CHARGE, T_FIRE, T_FADE, T_BACK = 0.40, 1.50, 1.00, 0.35, 0.20, 0.50
    t_stop = T_OUT + T_SWEEP
    t_fire = t_stop + T_CHARGE
    t_back = t_fire + T_FIRE
    t_end = t_back + T_BACK
    n = int(round((t_end + 0.4) / dt))
    for k in range(n + 1):
        t = k * dt
        c = bg.copy()
        shake = 0
        # telegraph under the characters
        if t_stop <= t < t_fire:
            u = (t - t_stop) / T_CHARGE
            for side in ('left', 'right'):
                c = draw_telegraph(c, side, rows[side], 0.12 + 0.18 * u, flash=(t_fire - t) <= 0.10)
        c = draw_player(c)
        # beams
        if t_fire <= t < t_back + T_FADE:
            f = _at(B.BEAM_TIMES, t - t_fire, loop=True)
            a = 1.0 if t < t_back else max(0.0, 1.0 - (t - t_back) / T_FADE)
            for side in ('left', 'right'):
                c = draw_beam(c, side, rows[side], f, alpha=a, glow=a > 0.5)
            if t < t_fire + 0.1:
                shake = 6 if int((t - t_fire) / 0.025) % 2 == 0 else -6
        for side in ('left', 'right'):
            post = pr['node'][side]
            if t < T_OUT:
                u = t / T_OUT
                e = u * u * (3 - 2 * u)
                sx, sy = REST[side]
                x = sx + (post - sx) * e
                y = sy + (mids[side] - sy) * e - 40 * math.sin(math.pi * e)
                pair = frames_of('gun_form')[_at(GN.GUN_CLIPS['gun_form'], t)]
            elif t < t_stop:
                x = post
                y = mids[side] + amps[side] * math.sin(2 * math.pi * (t - T_OUT) / 1.0 + phi[side])
                pair = frames_of('gun_idle')[_at(GN.GUN_CLIPS['gun_idle'], t - T_OUT, loop=True)]
            elif t < t_fire:
                x = post
                y0 = mids[side] + amps[side] * math.sin(2 * math.pi * T_SWEEP / 1.0 + phi[side])
                g = min(1.0, (t - t_stop) / 0.15)
                g = g * g * (3 - 2 * g)
                y = y0 + (rows[side] - y0) * g
                pair = frames_of('gun_charge')[_at(GN.GUN_CLIPS['gun_charge'], t - t_stop, loop=True)]
            elif t < t_back:
                x, y = post, rows[side]
                pair = frames_of('gun_fire')[_at(GN.GUN_CLIPS['gun_fire'], t - t_fire)]
            elif t < t_end:
                u = (t - t_back) / T_BACK
                e = u * u * (3 - 2 * u)
                sx, sy = REST[side]
                x = post + (sx - post) * e
                y = rows[side] + (sy - rows[side]) * e - 40 * math.sin(math.pi * e)
                rev = list(reversed(frames_of('gun_form')))
                pair = rev[_at(list(reversed(GN.GUN_CLIPS['gun_form'])), (t - t_back) * 0.40 / T_BACK)]
            else:
                x, y = REST[side]
                pair = hover_frames()[_at(A.CLIPS['hover'], t - t_end, loop=True)]
            c = draw_hand(c, pair, (x, y), side)
            if t_stop + 0.15 <= t < t_fire:
                m = muzzle_world((x, y), side)
                c = draw_at(c, fx_frames('charge')[_at(B.CHARGE_TIMES, t - t_stop, loop=True)], (16, 16), m,
                            flip=(side == 'left'))
            if t_fire <= t < t_fire + sum(B.FLASH_TIMES):
                m = muzzle_world((x, y), side)
                c = draw_at(c, fx_frames('flash')[_at(B.FLASH_TIMES, t - t_fire)], (24, 24), m, flip=(side == 'left'))
        if t_stop + 0.15 <= t < t_fire:
            c = draw_badge(c, (PLAYER_BODY[0], rows[aimer] - 30), t - t_stop - 0.15)
        if shake:
            s = Image.new('RGBA', c.size, (0, 0, 0, 255))
            s.alpha_composite(c, (0, shake))
            c = s
        if downscale:
            c = c.resize((1280, 720), Image.NEAREST)
        frames.append(c.convert('RGB'))
        durs.append(int(round(dt * 1000)))
    durs[-1] = 600
    # one palette for every frame (taken from a montage of the sweep, the charge and the fire), so the
    # still arena is the same bytes in every frame and the GIF only stores what moves
    picks = [frames[int(len(frames) * f)] for f in (0.25, 0.6, 0.78)]
    mont = Image.new('RGB', (picks[0].width, picks[0].height * len(picks)))
    for i, p in enumerate(picks):
        mont.paste(p, (0, i * p.height))
    pal = mont.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=1, optimize=True)
    return path


def contact_sheet(path, scale=3):
    rows = []
    for clip in GN.GUN_ORDER:
        tiles = []
        for im, gl in frames_of(clip):
            t = Image.new('RGBA', im.size, (86, 128, 72, 255))
            t = H.add_glow(t, gl)
            t.alpha_composite(im)
            tiles.append(t)
        rows.append(('%s %s' % (clip, GN.GUN_CLIPS[clip]), tiles))
    bm = fx_frames('beam')
    for kind in ('start', 'tile', 'end'):
        tiles = []
        for im in bm[kind]:
            t = Image.new('RGBA', im.size, (86, 128, 72, 255))
            t.alpha_composite(im)
            tiles.append(t)
        rows.append(('beam %s %s' % (kind, B.BEAM_TIMES), tiles))
    for name, times in (('flash', B.FLASH_TIMES), ('charge', B.CHARGE_TIMES)):
        tiles = []
        for im in fx_frames(name):
            t = Image.new('RGBA', im.size, (86, 128, 72, 255))
            t.alpha_composite(im)
            tiles.append(t)
        rows.append(('%s %s' % (name, times), tiles))
    pad = 4
    W = max(sum(t.width + pad for t in tiles) for _, tiles in rows) * scale
    Hh = sum((max(t.height for t in tiles) + 12) for _, tiles in rows) * scale
    out = Image.new('RGBA', (W, Hh), (20, 20, 24, 255))
    d = ImageDraw.Draw(out)
    y = 0
    for name, tiles in rows:
        d.text((4, y + 2), name, fill=(235, 235, 235, 255))
        x = 0
        for t in tiles:
            out.alpha_composite(t.resize((t.width * scale, t.height * scale), Image.NEAREST), (x, y + 12 * scale))
            x += (t.width + pad) * scale
        y += (max(t.height for t in tiles) + 12) * scale
    out.save(path)
    return path


def build_all(out_dir):
    paths = [contact_sheet(os.path.join(out_dir, 'josh_gun_sheet.png'))]
    for fn, name in ((mock_sweep, 'mock_gun_1_sweep.png'), (mock_charge, 'mock_gun_2_charge.png'),
                     (mock_fire, 'mock_gun_3_fire.png')):
        p = os.path.join(out_dir, name)
        fn().save(p)
        paths.append(p)
    paths.append(gif(os.path.join(out_dir, 'gif_gun_sweep_charge_fire.gif')))
    return paths
