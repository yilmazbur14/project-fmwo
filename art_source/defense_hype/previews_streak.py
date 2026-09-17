"""Review previews for the parry streak art: GIFs, a 6x close-up and an in-fight x3 parry mockup.
  python previews_streak.py [mock] [gifs] [closeup]
Outputs go to DH_PREVIEWS (the scratchpad parry_streak folder)."""
import sys
sys.dont_write_bytecode = True
import math
from dh_common import *
from gifio import write_gif
import previews as PV
import parry_streak as PK

OUT = PREVIEWS.rstrip('/') + '/'
X1 = from_png(PROJ + 'Assets/UI/popup_parry.png')
X2 = from_png(PROJ + 'Assets/UI/popup_parry_x2.png')
X3 = from_png(PROJ + 'Assets/UI/popup_parry_x3.png')
BADGE = from_png(PROJ + 'Assets/UI/streak_badge.png')
DIGITS = from_png(PROJ + 'Assets/UI/streak_digits.png')
FLASH = from_png(PROJ + 'Assets/Effects/parry_flash.png')
FLASH_S = from_png(PROJ + 'Assets/Effects/parry_flash_strong.png')
SHATTER = from_png(PROJ + 'Assets/Effects/parry_shatter.png')
QUAKE = from_png(PROJ + 'Assets/Characters/Eric/eric_quake_projectile.png')

X1_F = [crop(X1, i * 72, 0, 72, 20) for i in range(2)]
X2_F = [crop(X2, i * 96, 0, 96, 20) for i in range(2)]
X3_F = [crop(X3, i * 112, 0, 112, 20) for i in range(2)]
BADGE_F = [[crop(BADGE, f * PK.BW, t * PK.BH, PK.BW, PK.BH) for f in range(4)] for t in range(3)]
DIGIT_F = [crop(DIGITS, i * 8, 0, 8, 13) for i in range(10)]
FLASH_F = [crop(FLASH, i * 64, 0, 64, 64) for i in range(5)]
FLASH_S_F = [crop(FLASH_S, i * 96, 0, 96, 96) for i in range(7)]
SHATTER_F = [crop(SHATTER, i * 32, 0, 32, 32) for i in range(4)]

# HUD: the streak badge sits left of the hype meter (hype frame 369x126 at (1539, 946))
BADGE_XY = (1371, 985)


def badge_with(tier, f, count):
    c = BADGE_F[tier][f].copy()
    text = str(count)
    if len(text) == 1:
        c.blit(DIGIT_F[int(text)], *PK.DIGIT_ONE)
    else:
        for k, ch in enumerate(text[-2:]):
            c.blit(DIGIT_F[int(ch)], *PK.DIGIT_TWO[k])
    return c


def draw_badge(img, tier, f, count, xy=BADGE_XY):
    PV.paste(img, badge_with(tier, f, count), xy[0], xy[1], 3)


# ------------------------------------------------------------------ x3 parry mockup (Eric's fight)
def mock_x3(f=0, badge_f=0):
    img, ptl, contact = PV.parry_scene()
    PV.paste(img, FLASH_S_F[f], contact[0] - 96, contact[1] - 96, 2)
    pop = X3_F[1 if f < 2 else 0]
    PV.paste(img, pop, ptl[0] + 40 - pop.w * 3 // 2, ptl[1] - 28 - 48, 3)
    PV.draw_hearts(img, 5)
    PV.draw_stamina(img, 0.86)
    PV.draw_hype(img, 0.95)
    draw_badge(img, 2, badge_f, 3)
    return img


def mocks():
    img = mock_x3(1, 0)
    PV.save(img, 'mockup_x3_parry_eric.png')
    PV.save(PV.region(img, 700, 330, 640, 360, 3), 'mockup_x3_parry_eric_zoom3x.png')
    PV.save(PV.region(img, 1280, 930, 640, 150, 2), 'mockup_x3_hud_badge_zoom2x.png')


# ------------------------------------------------------------------ GIFs
def gifs():
    # tier ladder: the three popups pulsing together, at the in-game 3x
    W_, H_ = 400, 210
    frames = []
    for k in range(8):
        img = PV.rgb(W_, H_, (70, 90, 60))
        for i, (fr, lbl) in enumerate(((X1_F, 'X1'), (X2_F, 'X2'), (X3_F, 'X3+'))):
            f = fr[k % 2]
            PV.paste(img, f, (W_ - f.w * 3) // 2, 14 + i * 66, 3)
        frames.append(img)
    write_gif(OUT + 'gif_streak_popup_tiers_3x.gif', frames, [9] * 8)
    print('wrote gif_streak_popup_tiers_3x.gif')
    # badge tiers with live counts, at 3x on the HUD's black band
    frames = []
    for k in range(8):
        img = PV.rgb(3 * (PK.BW * 3 + 24) + 24, PK.BH * 3 + 48, (0, 0, 0))
        for i, (tier, count) in enumerate(((0, 1), (1, 2), (2, 7))):
            PV.paste(img, badge_with(tier, k % 4, count), 24 + i * (PK.BW * 3 + 24), 24, 3)
        frames.append(img)
    write_gif(OUT + 'gif_streak_badge_3x.gif', frames, [9] * 8)
    print('wrote gif_streak_badge_3x.gif')
    # the x3+ flash beside the normal parry flash, both at the player's 2x
    frames, durs = [], []
    import fx_defense as FD
    for k in range(8):
        img = PV.rgb(2 * 96 * 2 + 60, 96 * 2 + 40, (136, 180, 99))
        if k < 5:
            PV.paste(img, FLASH_F[k], 20 + (96 - 64) * 2 // 2, 20 + (96 - 64) * 2 // 2, 2)
        if k < 7:
            PV.paste(img, FLASH_S_F[k], 40 + 96 * 2, 20, 2)
        frames.append(img)
        durs.append(max(2, PK.FLASH_DURATIONS_MS[min(k, 6)] // 10))
    frames.append(PV.rgb(2 * 96 * 2 + 60, 96 * 2 + 40, (136, 180, 99)))
    durs.append(40)
    write_gif(OUT + 'gif_parry_flash_normal_vs_strong_2x.gif', frames, durs)
    print('wrote gif_parry_flash_normal_vs_strong_2x.gif')
    # shatter on one of Eric's quake projectiles
    proj = crop(QUAKE, 0, 0, 80, 80)
    frames = []
    for k in range(6):
        img = PV.rgb(48 * 4, 48 * 4, (136, 180, 99))
        if k == 0:
            PV.paste(img, proj, (24 - 40) * 4, (24 - 40) * 4, 4)
        elif k <= 4:
            PV.paste(img, SHATTER_F[k - 1], 8 * 4, 8 * 4, 4)
        frames.append(img)
    write_gif(OUT + 'gif_parry_shatter_4x.gif', frames, [30, 4, 5, 6, 7, 40])
    print('wrote gif_parry_shatter_4x.gif')
    # the whole x3 moment in scene
    frames, durs = [], []
    for k in range(9):
        img = mock_x3(min(k, 6), k % 4)
        crop_img = [row[760:1440] for row in img[300:760]]
        frames.append([r[::2] for r in crop_img[::2]])
        durs.append(max(2, PK.FLASH_DURATIONS_MS[min(k, 6)] // 10) if k < 7 else 30)
    write_gif(OUT + 'gif_x3_parry_moment.gif', frames, durs)
    print('wrote gif_x3_parry_moment.gif')


# ------------------------------------------------------------------ 6x close-up
def closeup():
    S = 6
    rows = [('POPUP_PARRY (X1, ALREADY APPROVED) 2 X 72X20', X1_F),
            ('POPUP_PARRY_X2 2 X 96X20  80 MS', X2_F),
            ('POPUP_PARRY_X3 2 X 112X20  70 MS', X3_F),
            ('STREAK_BADGE TIER 1 / 2 / 3+  4 X 50X22  90 MS  (DIGITS DROPPED IN)',
             [badge_with(0, 0, 1), badge_with(0, 2, 1), badge_with(1, 0, 2), badge_with(1, 2, 2),
              badge_with(2, 0, 7), badge_with(2, 2, 12)]),
            ('STREAK_DIGITS 10 X 8X13  CELL (30,4) FOR ONE DIGIT, (26,4)+(35,4) FOR TWO', DIGIT_F),
            ('PARRY_SHATTER 4 X 32X32  PIVOT (16,16)  40/50/60/70 MS', SHATTER_F)]
    GAP, LBL = 14, 34
    W_ = max(sum(fr.w * S + GAP for fr in frames) for _, frames in rows) + GAP
    H_ = sum(frames[0].h * S + LBL + GAP * 2 for _, frames in rows) + GAP + 96 * S + LBL + GAP * 2
    img = PV.rgb(max(W_, 7 * (96 * S + GAP) + GAP), H_, (46, 46, 60))
    y = GAP
    for label, frames in rows:
        PV.text(img, label, GAP, y, 4, (235, 235, 245))
        yy = y + LBL
        x = GAP
        for fr in frames:
            for Y in range(fr.h * S):
                for X in range(fr.w * S):
                    img[yy + Y][x + X] = (70, 70, 90) if ((X // (S * 2)) + (Y // (S * 2))) % 2 else (62, 62, 80)
            PV.paste(img, fr, x, yy, S)
            x += fr.w * S + GAP
        y = yy + frames[0].h * S + GAP * 2
    PV.text(img, 'PARRY_FLASH_STRONG 7 X 96X96  PIVOT (48,48)  30/50/60/70/80/90/100 MS', GAP, y, 4, (235, 235, 245))
    yy = y + LBL
    for i, fr in enumerate(FLASH_S_F):
        x = GAP + i * (96 * S + GAP)
        for Y in range(96 * S):
            for X in range(96 * S):
                img[yy + Y][x + X] = (70, 70, 90) if ((X // (S * 2)) + (Y // (S * 2))) % 2 else (62, 62, 80)
        PV.paste(img, fr, x, yy, S)
    PV.save(img, 'closeup_parry_streak_6x.png')


if __name__ == '__main__':
    which = [a for a in sys.argv[1:] if not a.startswith('--')] or ['mock', 'gifs', 'closeup']
    if 'mock' in which:
        mocks()
    if 'gifs' in which:
        gifs()
    if 'closeup' in which:
        closeup()
