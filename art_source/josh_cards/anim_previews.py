"""Approval previews for Josh's animation set: one GIF per animation, a 6x contact sheet of every
frame, and two 1920x1080 arena mockups (glide and recovery) with the player at 2x for scale.

Usage: python anim_previews.py <out_dir>
The arena background must already be rendered into <out_dir>/arena/ by Godot's movie writer:
  Godot.exe --path <project> --write-movie <out>/arena/frame.png --fixed-fps 30 --quit-after 3 \
            res://Scenes/Core/ArenaScene.tscn
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import W, H
from pngio import read_png, write_png
import anims
import apreview as AP
from mockup import label, blit_scaled

ASSET = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
GROUND = 915                       # the arena scene's own player stands with his feet here

# frame delays in ms (see the report for the frame-by-frame contract)
DELAYS = {
    'josh_idle': [150, 150, 150, 150],
    'josh_intro': [110, 150, 110, 260, 160, 420],
    'josh_lay_card': [140, 220, 300],
    'josh_glide': [110, 110, 110, 110],
    'josh_mount': [160, 130, 200],
    'josh_dismount': [120, 160, 240],
    'josh_drop_bomb': [90, 80, 130],
    'josh_throw': [140, 70, 110, 130],
    'josh_show_card': [130, 200, 200],
    'josh_recovery': [190, 190, 190, 190],
    'josh_hit': [70, 120],
    'josh_defeat': [130, 110, 110, 130, 180, 600],
}


def dashed_card(img, cx, cy, w, h, col=(255, 236, 140, 255), step=10):
    """Placeholder outline for the giant card Josh rides - drawn by the other artist."""
    x0, y0, x1, y1 = cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2
    for x in range(x0, x1):
        if (x // step) % 2 == 0:
            for y in (y0, y1):
                for k in range(3):
                    img[y + k][x] = col
    for y in range(y0, y1):
        if (y // step) % 2 == 0:
            for x in (x0, x1):
                for k in range(3):
                    img[y][x + k] = col


def arena_mockup(path, bgpath, title, items, notes):
    bw, bh, bg = read_png(bgpath)
    img = [[p[:3] + (255,) for p in row] for row in bg]
    pw, ph, ppx = read_png(ASSET + 'MainPlayer/player_4dir_sheet.png')
    for x in range(160, 1780):                          # dashed floor line
        if x % 10 < 5:
            for y in (GROUND, GROUND + 1):
                img[y][x] = (255, 240, 180, 255)
    blit_scaled(img, ppx, pw, ph, 0, 0, 32, 32, 300, GROUND - 32 * 2, 2)
    label(img, 276, GROUND + 18, 'PLAYER 2X', sc=3)
    for it in items:
        src, idx, ox, feet, flip, cap, card = it
        w, h, px = read_png(src)
        top = feet - 80 * 3                             # feet = screen row of local y 80
        if card:
            dashed_card(img, ox + 40 * 3, feet - card[1], card[0], 26)
            label(img, ox + 40 * 3 - 150, feet + 4, 'GIANT CARD GOES HERE', sc=2)
        blit_scaled(img, px, w, h, idx * W, 0, W, H, ox, top, 3, flip=flip)
        label(img, ox + 6, GROUND + 18, cap, sc=3)
    label(img, 260, 150, title, sc=6)
    for k, n in enumerate(notes):
        label(img, 260, 215 + k * 34, n, sc=3)
    write_png(path, bw, bh, img)
    print('   arena %-28s %dx%d' % (os.path.basename(path), bw, bh))


if __name__ == '__main__':
    OUT = sys.argv[1].rstrip('/\\')
    J = ASSET + 'Josh/'
    built = {k: anims.sheet(k) for k in anims.ANIMS}

    for name, cs in built.items():
        AP.anim_gif(os.path.join(OUT, name + '.gif'), cs, DELAYS[name], f=5)

    AP.contact(os.path.join(OUT, 'josh_contact_6x.png'),
               [(k.replace('josh_', '').upper(), v) for k, v in built.items()],
               f=6, title='JOSH BOSS ANIMATION SET  80X80  FEET ROW 79')

    bg = os.path.join(OUT, 'arena', 'frame00000002.png')
    if os.path.exists(bg):
        arena_mockup(os.path.join(OUT, 'arena_glide.png'), bg, 'JOSH GLIDE 3X',
                     [(J + 'josh_glide.png', 0, 620, GROUND - 260, False, 'GLIDE F0', (300, 12)),
                      (J + 'josh_glide.png', 2, 1120, GROUND - 190, False, 'GLIDE F2', (300, 12)),
                      (J + 'josh_drop_bomb.png', 1, 1520, GROUND - 150, False, 'DROP BOMB F1', (300, 12))],
                     ['80X80 FRAMES, 3X IN SCENE. SOLES ON ROW 75, SO THE CARD TOP BELONGS AT LOCAL Y 76',
                      'UNFLIPPED FACES RIGHT. THE CARD ITSELF IS NOT DRAWN HERE'])
        arena_mockup(os.path.join(OUT, 'arena_recovery.png'), bg, 'JOSH RECOVERY 3X',
                     [(J + 'josh_recovery.png', 0, 620, GROUND, False, 'RECOVERY F0', None),
                      (J + 'josh_recovery.png', 2, 900, GROUND, False, 'RECOVERY F2', None),
                      (J + 'josh_idle.png', 0, 1220, GROUND, True, 'IDLE F0', None),
                      (J + 'josh_throw.png', 1, 1500, GROUND, False, 'THROW F1', None)],
                     ['PUNISH WINDOW: HANDS ON KNEES, CAP KNOCKED BACK, DECK SPILLING',
                      '80X80 FRAMES, 3X IN SCENE, FEET ON ROW 79'])
    else:
        print('   (no arena background at %s - skipped the mockups)' % bg)
