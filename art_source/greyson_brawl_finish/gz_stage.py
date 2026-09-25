"""Staged previews of the finishing half, written ONLY to the scratch folder (never into Assets):

    python -B gz_stage.py

  finish_staged_zoom15.png  the brawl as the game frames it (PLAN_BRAWL.md section 4): his feet at
                            (960, 560), the player at 2x in front with soles at (960, 572), the
                            camera at zoom 1.5 on (960, 402). Four moments: dazed (the player's
                            guard), the uppercut CONTACT (the player's back-view uppercut f5, its
                            glove 50 texels above the soles, on his dazed chin), his snap (the
                            player at the uppercut's apex, f7), and the KO lying frame.
  greyson_brawl_ko.gif      the KO at its timings: f0 held through the finisher's arc (0.6 s),
                            f1-f3 at 0.15 s, f4 held.
  greyson_brawl_toss.gif    the toss at 0.13 s a frame, the barbell prop flying off to screen
                            left from the release point, then the approved guard.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gz_base as Z  # noqa: E402
import gz_sheets as S  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

K = Z.K
OUT = Z.SCRATCH
ROOT = Z.GB.G.B.ROOT
MAT = os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')
P2X = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_final_brawl_2x.png')
PUP = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_final_brawl_uppercut.png')
FEET_W, SOLES_W = (960, 560), (960, 572)
ZOOM, FOCUS = 1.5, (960, 402)
MAT_RGB = (133, 171, 102, 255)


def frames(name):
    return [(label, cv.image(), anc) for label, cv, anc in S.build_sheet(name)]


def player_2x(col, row=0):
    """player_final_brawl_2x.png: 10x4 cells of 64x96, soles on row 61, centre column 32."""
    sheet = Image.open(P2X).convert('RGBA')
    return sheet.crop((col * 64, row * 96, col * 64 + 64, row * 96 + 96)), 61


def player_uppercut(col):
    """player_final_brawl_uppercut.png: 10 cells of 64x128, soles on row 93, centre column 32."""
    sheet = Image.open(PUP).convert('RGBA')
    return sheet.crop((col * 64, 0, col * 64 + 64, 128)), 93


def world(greyson_im, player):
    """The whole screen at zoom 1.5 (1920x1080) around FOCUS; player = (cell, soles row)."""
    vw, vh = 1920 / ZOOM, 1080 / ZOOM
    wx0, wy0 = int(FOCUS[0] - vw / 2), int(FOCUS[1] - vh / 2)
    ww, wh = int(vw), int(vh)
    canvas = Image.new('RGBA', (ww, wh), (0, 0, 0, 255))
    mat = Image.open(MAT).convert('RGBA')
    mat3 = mat.resize((mat.width * 3, mat.height * 3), Image.NEAREST)
    for ty in range(-mat3.height, wh + mat3.height, mat3.height):
        for tx in range(-mat3.width, ww + mat3.width, mat3.width):
            canvas.paste(mat3, (tx - (wx0 % mat3.width), ty - (wy0 % mat3.height)))
    g3 = greyson_im.resize((336, 336), Image.NEAREST)
    canvas.alpha_composite(g3, (FEET_W[0] - 168 - wx0, FEET_W[1] - 336 - wy0))
    if player is not None:
        cell, soles = player
        p3 = cell.resize((cell.width * 3, cell.height * 3), Image.NEAREST)
        canvas.alpha_composite(p3, (SOLES_W[0] - 32 * 3 - wx0, SOLES_W[1] - (soles + 1) * 3 - wy0))
    return canvas.resize((1920, 1080), Image.NEAREST)


def crop_fighters(shot):
    cx0 = int((740 - (FOCUS[0] - 640)) * ZOOM)
    cy0 = int((190 - (FOCUS[1] - 360)) * ZOOM)
    return shot.crop((cx0, cy0, cx0 + 660, cy0 + 600))


def staged():
    dz = frames('greyson_brawl_dazed')
    up = frames('greyson_brawl_uppercut')
    ko = frames('greyson_brawl_ko')
    moments = [('dazed f0: the player in guard', dz[0][1], player_2x(0)),
               ('CONTACT: uppercut f5 on the dazed chin', dz[0][1], player_uppercut(5)),
               ('his snap: the player at the apex f7', up[0][1], player_uppercut(7)),
               ('KO f4: down', ko[4][1], None)]
    tiles = []
    for title, g, p in moments:
        t = crop_fighters(world(g, p))
        d = ImageDraw.Draw(t)
        d.rectangle([0, 0, t.width, 22], fill=(10, 10, 14, 230))
        d.text((6, 5), title, fill=(235, 235, 240, 255))
        tiles.append(t)
    out = Image.new('RGBA', (sum(t.width for t in tiles) + 8 * 3, tiles[0].height), (10, 10, 14, 255))
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + 8
    p = os.path.join(OUT, 'finish_staged_zoom15.png')
    out.save(p)
    return p


def on_mat(im, s=3, pad_left=0, w=None):
    w = w or im.width + pad_left
    b = Image.new('RGBA', (w, im.height), MAT_RGB)
    b.alpha_composite(im, (pad_left, 0))
    return b.resize((b.width * s, b.height * s), Image.NEAREST)


def gif(path, imgs, durations):
    pal = [i.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=64) for i in imgs]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations, loop=0, disposal=2)
    return path


def ko_gif():
    fs = frames('greyson_brawl_ko')
    imgs = [on_mat(im) for _, im, _ in fs]
    return gif(os.path.join(OUT, 'greyson_brawl_ko.gif'), imgs, [600, 150, 150, 150, 1400])


def toss_gif():
    fs = frames('greyson_brawl_toss')
    prop = frames('greyson_barbell_prop')[0][1]
    guard = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'Greyson',
                                    'greyson_brawl_guard.png')).convert('RGBA').crop((0, 0, 112, 112))
    pad = 150                                     # room on screen left for the flight
    imgs, durs = [], []
    for i, (_, im, _) in enumerate(fs[:2]):
        imgs.append(on_mat(im, pad_left=pad))
        durs.append(130)
    # the flight: the prop's grip starts on the release point, the barbell spinning as it goes
    rx, ry = S.RELEASE
    gx, gy = S.PROP_GRIP
    for j, t in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
        base = fs[2][2] if j < 3 else None
        frame = Image.new('RGBA', (112 + pad, 112), (0, 0, 0, 0))
        frame.alpha_composite(fs[2][1] if j < 3 else guard, (pad, 0))
        x = pad + rx - gx - 130 * t
        y = ry - gy - 40 * math.sin(math.pi * t) + 30 * t * t
        pr = prop.rotate(-200 * t, resample=Image.NEAREST, expand=True, center=(S.PROP_CM[0], S.PROP_CM[1]))
        frame.alpha_composite(pr, (int(x), int(y)))
        imgs.append(on_mat(frame))
        durs.append(90)
    imgs.append(on_mat(guard, pad_left=pad))
    durs.append(900)
    return gif(os.path.join(OUT, 'greyson_brawl_toss.gif'), imgs, durs)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    print(staged())
    print(ko_gif())
    print(toss_gif())
