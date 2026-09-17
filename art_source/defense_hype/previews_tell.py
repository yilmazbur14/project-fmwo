"""Review previews for the parry tells: in-fight mockups at three boss sizes, GIFs and a 6x close-up.
  python previews_tell.py [mock] [gifs] [closeup]
Outputs go to DH_PREVIEWS (the scratchpad parry_tell folder)."""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *
from gifio import write_gif
import previews as PV

OUT = PREVIEWS.rstrip('/') + '/'
TELL = from_png(PROJ + 'Assets/Effects/parry_tell.png')
STRONG = from_png(PROJ + 'Assets/Effects/parry_tell_strong.png')
GLOW = from_png(PROJ + 'Assets/Effects/parry_glow.png')
TELL_F = [crop(TELL, i * 32, 0, 32, 24) for i in range(6)]
STRONG_F = [crop(STRONG, i * 48, 0, 48, 36) for i in range(6)]
GLOW_F = [crop(GLOW, i * 32, 0, 32, 32) for i in range(4)]
MASON = from_png(PROJ + 'Assets/Characters/Mason/mason.png')
MECH = from_png(PROJ + 'Assets/Characters/GreysonMech/greyson_mech.png')
QUAKE = from_png(PROJ + 'Assets/Characters/Eric/eric_quake_projectile.png')
BOMB = crop(from_png(PROJ + 'Assets/Characters/Mason/poo_bomb.png'), 0, 0, 32, 32)


def scale_canvas(c, k):
    o = Canvas(c.w * k, c.h * k)
    for y in range(o.h):
        for x in range(o.w):
            o.p[y][x] = c.p[y // k][x // k]
    return o

# boss placements (world px) and where the tell's bottom-centre pivot goes
ERIC_X, ERIC_FEET = 960, 640
ERIC_HEAD = (ERIC_X + (152 - 128) * 3, ERIC_FEET - (192 - 116) * 3)     # texel (152, 116) on the wind-up frames
MASON_X, MASON_FEET = 960, 620
MASON_HEAD = (MASON_X, MASON_FEET - 62 * 3 - 6)
MECH_X, MECH_FEET = 960, 660
MECH_HEAD = (MECH_X, MECH_FEET - 95 * 3 - 6)


def put_tell(img, frames, f, anchor, strong):
    fr = frames[f]
    pivot = (24, 36) if strong else (16, 24)
    PV.paste(img, fr, anchor[0] - pivot[0] * 3, anchor[1] - pivot[1] * 3, 3)


def clear_boss_bar(img):
    """Mason and the mech are not Eric: drop the boss bar band copied in for his fight"""
    w, h, px = read_png(PV.arena_png())
    for y in range(40, 96):
        for x in range(760, 1162):
            img[y][x] = px[y][x][:3]
    return img


def hud(img, stam=0.7, hype=0.45):
    PV.draw_hearts(img, 5)
    PV.draw_stamina(img, stam)
    PV.draw_hype(img, hype)


def mock_eric(f=0):
    img = PV.arena()
    PV.paste_eric(img, 12, ERIC_X, ERIC_FEET)                       # sword hoisted: the whirlwind wind-up
    PV.paste(img, PV.player_cell(2, 9), 1250, 560, 2)               # player blocking toward him
    put_tell(img, STRONG_F, f, ERIC_HEAD, True)
    hud(img, 0.62, 0.45)
    return img


def mock_mason(f=0):
    img = clear_boss_bar(PV.arena())
    PV.paste(img, MASON, MASON_X - 32 * 3, MASON_FEET - 63 * 3, 3)
    PV.paste(img, PV.player_cell(2, 9), 1180, 545, 2)
    put_tell(img, TELL_F, f, MASON_HEAD, False)
    hud(img, 0.78, 0.3)
    return img


def mock_mech(f=0):
    img = clear_boss_bar(PV.arena())
    PV.paste(img, MECH, MECH_X - 48 * 3, MECH_FEET - 95 * 3, 3)
    PV.paste(img, PV.player_cell(2, 9), 1290, 585, 2)
    put_tell(img, TELL_F, f, MECH_HEAD, False)
    hud(img, 0.5, 0.8)
    return img


def mocks():
    for name, fn, box in (('1_eric_whirlwind_windup_strong', mock_eric, (760, 220, 640, 360)),
                          ('2_mason_standard', mock_mason, (760, 260, 640, 360)),
                          ('3_mech_standard', mock_mech, (760, 200, 640, 360))):
        img = fn(0)
        PV.save(img, 'mockup_tell_%s.png' % name)
        PV.save(PV.region(img, box[0], box[1], box[2], box[3], 3), 'mockup_tell_%s_zoom3x.png' % name)


def gif_on_three_backgrounds(frames, name, durs, s=4):
    bgs = [(255, 255, 255), (136, 180, 99), (32, 32, 40)]
    fw, fh = frames[0].w, frames[0].h
    pad = 4
    W = len(bgs) * (fw + 2 * pad) * s
    H = (fh + 2 * pad) * s
    out = []
    for fr in frames:
        img = PV.rgb(W, H, (0, 0, 0))
        for k, bg in enumerate(bgs):
            x0 = k * (fw + 2 * pad) * s
            for y in range(H):
                for x in range((fw + 2 * pad) * s):
                    img[y][x0 + x] = bg
            PV.paste(img, fr, x0 + pad * s, pad * s, s)
        out.append(img)
    write_gif(OUT + name, out, [max(2, d // 10) for d in durs])
    print('wrote', name)


def gifs():
    import parry_tell as PT
    gif_on_three_backgrounds(TELL_F, 'gif_parry_tell_4x.gif', PT.TELL_DURATIONS_MS)
    gif_on_three_backgrounds(STRONG_F, 'gif_parry_tell_strong_4x.gif', PT.STRONG_DURATIONS_MS)
    # the aura behind a projectile, at the scale it is meant for: Mason's poo bomb (24 texels across)
    # needs the 32x32 aura at 2x, so the ring rings it instead of hiding behind it
    frames = []
    for f in range(4):
        img = PV.rgb(72 * 4, 72 * 4, (136, 180, 99))
        PV.paste(img, scale_canvas(GLOW_F[f], 2), 4 * 4, 4 * 4, 4)
        PV.paste(img, BOMB, (36 - 16) * 4, (36 - 16) * 4, 4)
        frames.append(img)
    write_gif(OUT + 'gif_parry_glow_on_projectile_4x.gif', frames, [9] * 4)
    print('wrote gif_parry_glow_on_projectile_4x.gif')
    # the strong tell looping over Eric's wind-up, in scene at 2x
    frames, durs = [], []
    for f in range(6):
        img = mock_eric(f)
        crop_img = [row[820:1300] for row in img[260:620]]
        frames.append([r[::2] for r in crop_img[::2]])
        durs.append(max(2, PT.STRONG_DURATIONS_MS[f] // 10))
    write_gif(OUT + 'gif_tell_on_eric_windup.gif', frames, durs)
    print('wrote gif_tell_on_eric_windup.gif')
    # the standard tell looping over Mason, in scene
    frames, durs = [], []
    for f in range(6):
        img = mock_mason(f)
        crop_img = [row[820:1300] for row in img[300:660]]
        frames.append([r[::2] for r in crop_img[::2]])
        durs.append(max(2, PT.TELL_DURATIONS_MS[f] // 10))
    write_gif(OUT + 'gif_tell_on_mason.gif', frames, durs)
    print('wrote gif_tell_on_mason.gif')


def closeup():
    S = 6
    rows = [('PARRY_TELL 6 X 32X24  PIVOT (16,24)  90/90/110/110/90/90 MS  LOOP', TELL_F),
            ('PARRY_TELL_STRONG 6 X 48X36  PIVOT (24,36)  70/70/80/80/70/70 MS  LOOP', STRONG_F),
            ('PARRY_GLOW 4 X 32X32  PIVOT (16,16)  90 MS  LOOP  (DRAWN BEHIND THE PROJECTILE)', GLOW_F)]
    GAP, LBL = 14, 34
    W_ = max(len(fr) * (fr[0].w * S + GAP) for _, fr in rows) + GAP
    H_ = sum(fr[0].h * S + LBL + GAP * 2 for _, fr in rows) + GAP
    img = PV.rgb(W_, H_, (46, 46, 60))
    y = GAP
    for label, frames in rows:
        PV.text(img, label, GAP, y, 4, (235, 235, 245))
        yy = y + LBL
        for i, fr in enumerate(frames):
            x = GAP + i * (fr.w * S + GAP)
            for Y in range(fr.h * S):
                for X in range(fr.w * S):
                    img[yy + Y][x + X] = (70, 70, 90) if ((X // (S * 2)) + (Y // (S * 2))) % 2 else (62, 62, 80)
            PV.paste(img, fr, x, yy, S)
        y = yy + frames[0].h * S + GAP * 2
    PV.save(img, 'closeup_parry_tells_6x.png')


if __name__ == '__main__':
    which = [a for a in sys.argv[1:] if not a.startswith('--')] or ['mock', 'gifs', 'closeup']
    if 'mock' in which:
        mocks()
    if 'gifs' in which:
        gifs()
    if 'closeup' in which:
        closeup()
