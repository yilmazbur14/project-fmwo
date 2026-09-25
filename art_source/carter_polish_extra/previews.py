"""Review images for this folder's deliverables, all written to the scratchpad (never to Assets).

    python previews.py

  portrait_6x_vs_sprite.png      the portrait at 6x beside the sprite's own head (the same crop at 6x,
                                 and at 9x so the two stand the same size)
  ladder_before_after_4x.png     rank_icons.png before (the pre-change snapshot) and after
  carter_messatsu_charge_4x.png  the charge sheet at 4x
  carter_messatsu_fire_4x.png    the fire sheet at 4x
  messatsu_charge_to_fire_3x.gif the charge loop (0.12 s) into the fire (0.05, 0.05, then held), 3x
  messatsu_in_game_fx_3x.gif     the same with the FX artist's current ball and flare composited on
                                 MUZZLE, as the game layers them (context only: their art, not mine)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlib                                                      # noqa: E402
import portrait as PT                                            # noqa: E402
import messatsu as M                                             # noqa: E402
from PIL import Image, ImageDraw                                 # noqa: E402

OUT = xlib.SCRATCH
BG = (30, 32, 40, 255)
TXT = (235, 235, 240, 255)
BEFORE = os.path.join(OUT, 'before')


def label(im, text, x, y):
    ImageDraw.Draw(im).text((x, y), text, fill=TXT)


def portrait_preview():
    por = Image.open(os.path.join(xlib.CARTER, 'portrait.png')).convert('RGBA')
    sp = Image.open(xlib.POLISH_PNG).convert('RGBA').crop((PT.SX0, PT.SY0, PT.SX0 + PT.N, PT.SY0 + PT.N))
    old = Image.open(os.path.join(BEFORE, 'portrait.png')).convert('RGBA') \
        if os.path.exists(os.path.join(BEFORE, 'portrait.png')) else None
    a = xlib.upscale(xlib.on_bg(sp), 6)
    b = xlib.upscale(xlib.on_bg(sp), 9)
    c = xlib.upscale(xlib.on_bg(por), 6)
    panels = [(a, "sprite head, carter_polish.png f0 x27-69 y19-61, 6x"),
              (b, "the same crop at 9x (= the portrait's size at 6x)"),
              (c, 'NEW portrait.png 64x64 at 6x')]
    if old is not None:
        panels.append((xlib.upscale(xlib.on_bg(old), 6), 'previous portrait.png at 6x'))
    w = sum(p.width for p, _ in panels) + 20 * (len(panels) + 1)
    h = max(p.height for p, _ in panels) + 40
    out = Image.new('RGBA', (w, h), BG)
    x = 20
    for p, t in panels:
        out.paste(p, (x, 30))
        label(out, t, x, 10)
        x += p.width + 20
    out.save(os.path.join(OUT, 'portrait_6x_vs_sprite.png'))


def ladder_preview():
    old = Image.open(os.path.join(BEFORE, 'rank_icons.png')).convert('RGBA')
    new = Image.open(os.path.join(xlib.ROOT, 'Assets', 'UI', 'Screens', 'rank_icons.png')).convert('RGBA')
    s = 4
    out = Image.new('RGBA', (old.width * s + 20, old.height * s * 2 + 50), BG)
    label(out, 'BEFORE  rank_icons.png (frame 7 = Carter)', 10, 4)
    out.paste(xlib.upscale(xlib.on_bg(old), s), (10, 18))
    label(out, 'AFTER  frame 7 re-framed on carter_polish.png - every other frame byte-identical', 10, 26 + old.height * s)
    out.paste(xlib.upscale(xlib.on_bg(new), s), (10, 40 + old.height * s))
    out.save(os.path.join(OUT, 'ladder_before_after_4x.png'))


def sheet_previews():
    for name in M.SHEETS:
        im = Image.open(os.path.join(xlib.CARTER, name + '.png')).convert('RGBA') \
            if os.path.exists(os.path.join(xlib.CARTER, name + '.png')) else M.sheet(name)
        xlib.upscale(xlib.on_bg(im, (46, 49, 58, 255)), 4).save(os.path.join(OUT, name + '_4x.png'))


def frames_in_order():
    """(image, pose, ms) for three charge loops then the fire."""
    ch = [(M.frame(M.charge_pose(i)).image(), M.charge_pose(i), 120) for i in range(4)]
    fi = [(M.frame(M.fire_pose(i)).image(), M.fire_pose(i), ms) for i, ms in enumerate((50, 50, 1400))]
    return ch * 3 + fi


def gif(path, frames, s=3, fx=False):
    imgs, durs = [], []
    for im, p, ms in frames:
        if fx:
            kind = 'ball' if p.get('hands') == 'cup' else 'flare'
            big = M.with_fx(im, kind, M.MUZZLE, f=len(imgs) % 4 if kind == 'flare' else len(imgs) % 6)
            fr = big.crop((70 - 10, 70 - 20, 70 + M.F + 60, 70 + M.F + 6))
        else:
            fr = xlib.on_bg(im, (150, 170, 120, 255))
        imgs.append(xlib.upscale(fr.convert('RGBA'), s).convert('RGB'))
        durs.append(ms)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durs, loop=0, disposal=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    portrait_preview()
    ladder_preview()
    sheet_previews()
    fr = frames_in_order()
    gif(os.path.join(OUT, 'messatsu_charge_to_fire_3x.gif'), fr)
    gif(os.path.join(OUT, 'messatsu_in_game_fx_3x.gif'), fr, fx=True)
    for f in sorted(os.listdir(OUT)):
        if f.endswith(('.png', '.gif')):
            print(os.path.join(OUT, f))


if __name__ == '__main__':
    main()
