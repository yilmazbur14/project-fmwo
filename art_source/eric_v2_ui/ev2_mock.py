"""Game-scale mocks of the Eric V2 UI, composited into real captures of his fight (capture_layers.gd).

Every piece is placed the way the game places it:
  Break gauge    HUD, 3x art at scale 1, frame top-left at GAUGE_AT; fill at +(21, 6) px.
  Mash prompt    FinisherPromptUI: [left key 96x96][18][meter 216x48][18][right key], meter at y 24,
                 text slot 192x60 under the meter, the whole row 12 px under the player's feet
                 (PLAYER_FEET (0, 24) through the zoomed view), centred on them.
  Tells          ParryTell: 3x, pivot (16, 24) on the attack's head point (EricWhirlwind (126, 108),
                 EricEarthquake (136, 100)).
  Daze stars     FinisherArtLayout.FINAL_STARS on DAZE_HEAD_PIXEL (128, 112).
  Zoom           PlayerFinisher: focus = player.lerp(daze anchor, 0.35); plan 3.6 zoom 1.40 + 0.12 m_s.

    python ev2_mock.py            writes the mocks into EV2_MOCKS (default <work>/mocks); nothing goes
                                  into the project. Needs the captures (see ev2_mocklib).
"""
import os
import sys
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont
import ev2_mocklib as M
import break_gauge as BG
import mash_meter as MM
import tier_stamps as TS
import dodge_tell as DT
from ev2_common import Canvas, crop, from_png, cell, PROJ, work

OUT = (os.environ.get('EV2_MOCKS') or work('mocks')).replace(os.sep, '/')
os.makedirs(OUT, exist_ok=True)
GAUGE_AT = (768, 93)
ERIC = (960, 380)
UI = PROJ + 'Assets/UI/'
FX = PROJ + 'Assets/Effects/'

G = BG.build()
TM = TS.build()
TELL = DT.build()['dodge_tell']


def gauge_img(frac, pulse=None, locked=False):
    fill = G['break_gauge_fill_hot'][pulse] if pulse is not None else G['break_gauge_fill'][0]
    c = BG.composite(frac, fill=fill)
    if pulse is not None:
        big = Canvas(c.w + 2 * BG.PULSE_PAD, c.h)
        big.blit(c, BG.PULSE_PAD, 0)
        big.blit(G['break_gauge_pulse'][pulse], 0, 0)
        return M.canvas_img(big, 3), (GAUGE_AT[0] - 3 * BG.PULSE_PAD, GAUGE_AT[1])
    im = M.canvas_img(c, 3)
    if locked:
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a:
                    px[x, y] = (r // 2, g // 2, b // 2, a)
    return im, GAUGE_AT


def shatter_img(f):
    base = BG.composite(0.0)
    big = Canvas(BG.SW_, BG.SH_)
    big.blit(base, BG.SH_PAD_X, BG.SH_PAD_Y)
    big.blit(G['break_gauge_shatter'][f], 0, 0)
    return M.canvas_img(big, 3), (GAUGE_AT[0] - 3 * BG.SH_PAD_X, GAUGE_AT[1] - 3 * BG.SH_PAD_Y)


def tell_img(frame, red=False):
    if red:
        sheet = from_png(FX + 'parry_tell.png')
        return M.canvas_img(cell(sheet, frame, 32, 24), 3)
    return M.canvas_img(TELL[frame], 3)


def place_tell(layer, head_pixel, frame, red=False, flip=False):
    ax, ay = M.eric_point(head_pixel, ERIC, flip)
    # the anchor is the centre of the head pixel, as the states compute it (+0.5 texel), rounded
    ax, ay = round(ax), round(ay)
    M.place(layer, tell_img(frame, red), (ax - 16 * 3, ay - 24 * 3))


def stars(layer, head_pixel, frame=0, to_screen=None, zoom=1.0):
    s = M.img(FX + 'daze_stars.png').crop((frame * 48, 0, frame * 48 + 48, 24))
    p = M.eric_point(head_pixel, ERIC)
    return s, p


def key_img(side, lit):
    s = M.img(UI + 'qte_key_%s_3x.png' % side)
    return s.crop((96 if lit else 0, 0, 192 if lit else 96, 96))


def prompt(hud, feet_screen, meter_canvas, text_img, lit_side='left', pressed_side=None):
    """lays the prompt out exactly as FinisherPromptUI._build/_place do"""
    size = (444, 132)
    top = feet_screen[1] + 12
    left = feet_screen[0] - size[0] / 2.0
    left = min(max(left, 8), 1920 - size[0] - 8)
    top = min(max(top, 8), 1080 - size[1] - 8)
    x0, y0 = round(left), round(top)
    for side, kx in (('left', 0), ('right', 348)):
        drop = 2 if side == pressed_side else 0
        M.place(hud, key_img(side, side == lit_side), (x0 + kx, y0 + drop))
    meter_im = M.canvas_img(meter_canvas, 3)
    mx, my = x0 + 114, y0 + 24
    if meter_canvas.w == MM.MW:
        M.place(hud, meter_im, (mx, my))
    else:                                   # a flash frame, on its padded canvas
        M.place(hud, meter_im, (mx - 3 * MM.FL_PAD_X, my - 3 * MM.FL_PAD_Y))
    if text_img is not None:
        tx = x0 + 114 + (216 - text_img.width) / 2.0
        M.place(hud, text_img, (tx, my + 48))
    return (x0, y0)


def mash_text(frame=0):
    s = M.img(UI + 'qte_mash_text_3x.png')
    return s.crop((frame * 192, 0, frame * 192 + 192, 60))


def base(eric_frame, player_fn=None, gauge=None, extra_world=None):
    w = M.world()
    M.eric(w, eric_frame, ERIC)
    if player_fn:
        player_fn(w)
    if extra_world:
        extra_world(w)
    return w


def finish(w, hud_items):
    w.alpha_composite(M.hud())
    for im, at in hud_items:
        M.place(w, im, at)
    return w


def save(im, name):
    p = os.path.join(OUT, name)
    im.convert('RGB').save(p)
    print('wrote', os.path.abspath(p))
    return im


# ------------------------------------------------------------------ the scenes
def scene_fight():
    """Eric winds up the whirlwind (yellow: dodge it); the gauge is about half full."""
    w = base(13, lambda l: M.player4(l, 10, (905, 745)))
    place_tell(w, (126, 108), 3)
    return finish(w, [gauge_img(0.5)])


def scene_near_full():
    """Eric raises the slam (red: parry it), the gauge is past 80% and throbbing (hot frame)."""
    w = base(6, lambda l: M.player4(l, 10, (1010, 700)))
    place_tell(w, (136, 100), 2, red=True)
    return finish(w, [gauge_img(0.9, pulse=2)])


def scene_break():
    """The Break: the gauge shatters mid-frame under BREAK!, Eric reels."""
    w = base(27, lambda l: M.player4(l, 10, (1000, 690)))
    items = [shatter_img(2)]
    word = M.canvas_img(G['break_text'][1], 3)
    # centred under the gauge, on the mat
    items.append((word, (GAUGE_AT[0] + (384 - word.width) / 2.0, GAUGE_AT[1] + 21 + 6)))
    return finish(w, items)


def scene_mash(tier_shown, meter_value, banked, flash=None, eric_frame=29, zoom=1.57, stamp=None):
    """the mash, frozen fight, zoomed world, prompt under the player"""
    player = (1100, 542)
    wl = M.world()
    M.eric(wl, eric_frame, ERIC)
    M.player_up(wl, 1, player, flip=True)
    daze = M.eric_point((128, 112), ERIC)
    focus = (player[0] + 0.35 * (daze[0] - player[0]), player[1] + 0.35 * (daze[1] - player[1]))
    zw, to_screen = M.zoomed(wl, zoom, focus)
    # daze stars: a world sprite, so it zooms too
    st = M.img(FX + 'daze_stars.png').crop((96, 0, 144, 24))
    st = st.resize((round(48 * 3 * zoom), round(24 * 3 * zoom)), Image.NEAREST)
    sx, sy = to_screen((daze[0] - 24 * 3, daze[1] - 13 * 3))
    zw.alpha_composite(st, (round(sx), round(sy)))
    hud = M.hud()
    zw.alpha_composite(hud)
    gi, ga = gauge_img(0.0, locked=True)
    M.place(zw, gi, ga)
    if flash is not None:
        meter = MM.composite(meter_value, banked=[b for b in banked if b != flash[0]], flash=flash)
    else:
        meter = MM.composite(meter_value, banked=banked)
    feet = to_screen((player[0], player[1] + 24))
    text = M.canvas_img(TM['qte_tier_%d' % stamp][1], 3) if stamp else mash_text(0)
    prompt(zw, feet, meter, text, lit_side='right', pressed_side='left')
    return zw


def scene_knight_breaker():
    """Tier 3: the mash resolves at once and the special's name goes up over the fight."""
    player = (1100, 542)
    wl = M.world()
    M.eric(wl, 29, ERIC)
    M.player_up(wl, 5, player, flip=True, super_=True)
    daze = M.eric_point((128, 112), ERIC)
    focus = (player[0] + 0.35 * (daze[0] - player[0]), player[1] + 0.35 * (daze[1] - player[1]))
    zw, to_screen = M.zoomed(wl, 1.76, focus)
    zw.alpha_composite(M.hud())
    gi, ga = gauge_img(0.0, locked=True)
    M.place(zw, gi, ga)
    meter = MM.composite(3.0, banked=[0, 1, 2])
    feet = to_screen((player[0], player[1] + 24))
    prompt(zw, feet, meter, M.canvas_img(TM['qte_tier_3'][1], 3), lit_side=None)
    kb = M.canvas_img(TM['knight_breaker'][1], 3)
    M.place(zw, kb, ((1920 - kb.width) / 2.0, 150))
    return zw


# ------------------------------------------------------------------ detail sheet
def detail_sheet():
    W, H = 1920, 1500
    out = Image.new('RGBA', (W, H), (16, 14, 26, 255))
    f = ImageFont.truetype(M.FONT, 22)
    d = ImageDraw.Draw(out)
    y = 16

    def head(text):
        nonlocal y
        d.text((24, y), text, font=f, fill=(251, 242, 54))
        y += 34

    real = M.img(M.CAP + '/real_v1.png')
    strip_bg = real.crop((700, 60, 1220, 125))

    head('BREAK GAUGE at 1:1 on the real HUD strip: empty, 50%, 79%, 80% throb (rest, warm, hot, warm), 100%')
    states = [('0%', gauge_img(0.0)), ('50%', gauge_img(0.5)), ('79%', gauge_img(0.79))] + \
             [('80%%+ f%d' % k, gauge_img(0.93, pulse=k)) for k in range(4)] + [('100%', gauge_img(1.0)),
                                                                            ('locked', gauge_img(0.0, locked=True))]
    x = 24
    for i, (lab, (im, at)) in enumerate(states):
        tile = strip_bg.copy()
        tile.alpha_composite(im, (at[0] - 700, at[1] - 60))
        tile = tile.crop((40, 20, 480, 60))
        if x + tile.width > W - 20:
            x = 24
            y += 70
        out.alpha_composite(tile, (x, y))
        d.text((x, y + 44), lab, font=ImageFont.truetype(M.FONT, 16), fill=(203, 219, 252))
        x += tile.width + 16
    y += 80
    head('SHATTER, 6 frames (0.36 s) at 1:1, over the emptied gauge')
    x = 24
    for k in range(6):
        im, at = shatter_img(k)
        tile = real.crop((700, 30, 1220, 175)).copy()
        tile.alpha_composite(im, (at[0] - 700, at[1] - 30))
        tile = tile.crop((40, 20, 480, 140))
        if x + tile.width > W - 20:
            x = 24
            y += 130
        out.alpha_composite(tile, (x, y))
        x += tile.width + 16
    y += 140
    head('BREAK!  rest / pop, 1:1                         TIER STAMPS  1!  2!!  3!!!  rest / pop, 1:1')
    x = 24
    for fr in G['break_text']:
        im = M.canvas_img(fr, 3)
        out.alpha_composite(im, (x, y))
        x += im.width + 16
    x += 60
    for t in (1, 2, 3):
        for fr in TM['qte_tier_%d' % t]:
            im = M.canvas_img(fr, 3)
            out.alpha_composite(im, (x, y))
            x += im.width + 10
        x += 20
    y += 90
    head('KNIGHT BREAKER!  rest / pop, 1:1')
    x = 24
    for fr in TM['knight_breaker']:
        im = M.canvas_img(fr, 3)
        out.alpha_composite(im, (x, y))
        x += im.width + 24
    y += 80
    head('3-BAR METER at 1:1: today\'s meter, empty, bar 1 filling, 1 banked + bar 2, 2 banked + bar 3, all banked, full flash x2')
    import qte_ui as UIQ
    old = UIQ.meter_frame().copy()
    old.blit(UIQ.meter_fill(), 7, 5)
    full = MM.build()['qte_meter3_full']
    ms = [old, MM.composite(0.0), MM.composite(0.55), MM.composite(1.45, banked=[0]),
          MM.composite(2.3, banked=[0, 1], glint_frame=1), MM.composite(3.0, banked=[0, 1, 2])] + full
    x = 24
    for m in ms:
        im = M.canvas_img(m, 3)
        out.alpha_composite(im, (x, y))
        x += im.width + 18
    y += 70
    head('BANK FLASH, 4 frames per bar (bar 1, bar 2, bar 3), 1:1')
    x = 24
    for bar in range(3):
        for k in range(4):
            m = MM.composite(bar + 1.0, banked=list(range(bar)), flash=(bar, k))
            im = M.canvas_img(m, 2)
            if x + im.width > W - 20:
                x = 24
                y += im.height + 10
            out.alpha_composite(im, (x, y))
            x += im.width + 10
    y += 100
    head('TELLS at 3x game scale (1:1 px): red parry badge (existing, 6 frames) / yellow dodge badge (new: ignite, peak, loop x4)')
    x = 24
    for k in range(6):
        im = tell_img(k, red=True)
        bgt = Image.new('RGBA', im.size, (117, 156, 84, 255))
        bgt.alpha_composite(im)
        out.alpha_composite(bgt, (x, y))
        x += im.width + 8
    y += 80
    x = 24
    for k in range(6):
        im = tell_img(k)
        bgt = Image.new('RGBA', im.size, (117, 156, 84, 255))
        bgt.alpha_composite(im)
        out.alpha_composite(bgt, (x, y))
        x += im.width + 8
    y += 90
    return out.crop((0, 0, W, y + 10))


def placement_sheet():
    """the proposed slot on the top rope beside an off-rope fallback on the mat, 2x crops"""
    rows = []
    for label, at in (('PROPOSED: on the top rope, frame at (768, 93), exactly the rope band\'s 21 px', (768, 93)),
                      ('FALLBACK: under the rope, on the mat, frame at (768, 117)', (768, 117))):
        tiles = []
        for frac, pulse in ((0.3, None), (0.5, None), (0.9, 0), (0.9, 2)):
            w = base(21, lambda l: M.player4(l, 10, (1000, 700)))
            w.alpha_composite(M.hud())
            fill = G['break_gauge_fill_hot'][pulse] if pulse is not None else G['break_gauge_fill'][0]
            c = BG.composite(frac, fill=fill)
            big = Canvas(c.w + 2 * BG.PULSE_PAD, c.h)
            big.blit(c, BG.PULSE_PAD, 0)
            if pulse is not None:
                big.blit(G['break_gauge_pulse'][pulse], 0, 0)
            M.place(w, M.canvas_img(big, 3), (at[0] - 3 * BG.PULSE_PAD, at[1]))
            tiles.append(w.crop((730, 40, 1190, 150)).resize((920, 220), Image.NEAREST))
        rows.append((label, tiles))
    out = Image.new('RGBA', (920 * 2 + 30, (220 * 2 + 20) * 2 + 90), (16, 14, 26, 255))
    d = ImageDraw.Draw(out)
    f = ImageFont.truetype(M.FONT, 24)
    y = 10
    for label, tiles in rows:
        d.text((10, y), label + '   (30%, 50%, 90% rest, 90% hot; shown at 2x)', font=f, fill=(251, 242, 54))
        y += 36
        for i, t in enumerate(tiles):
            out.alpha_composite(t, (10 + (i % 2) * 930, y + (i // 2) * 230))
        y += 2 * 230 + 10
    return out.crop((0, 0, out.width, y))


def zoomed_panel(full, boxes, s, name):
    tiles = [M.zoom_crop(full, b, s) for b in boxes]
    W = max(t.width for t in tiles) + 20
    H = sum(t.height + 10 for t in tiles) + 10
    out = Image.new('RGBA', (W, H), (16, 14, 26, 255))
    y = 10
    for t in tiles:
        out.alpha_composite(t, (10, y))
        y += t.height + 10
    return save(out, name)


if __name__ == '__main__':
    a = save(scene_fight(), 'mock_1_fight_dodge_tell.png')
    b = save(scene_near_full(), 'mock_2_gauge_near_full.png')
    c = save(scene_break(), 'mock_3_break_shatter.png')
    d = save(scene_mash(1, 1.4, [0], stamp=1), 'mock_4_mash_one_bar.png')
    e = save(scene_mash(2, 2.35, [0, 1], stamp=2, zoom=1.64), 'mock_5_mash_two_bars.png')
    f = save(scene_knight_breaker(), 'mock_6_knight_breaker.png')
    save(detail_sheet(), 'mock_7_details.png')
