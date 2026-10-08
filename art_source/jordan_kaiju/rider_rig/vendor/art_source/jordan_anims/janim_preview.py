"""Previews of Jordan's fight animations. Writes ONLY into the preview folder (the session
scratchpad by default, or the folder given), never into Assets/.

    python janim_preview.py [out_dir] [sheet ...]

  contact_4x.png        every sheet, one row each, every frame labelled with its index and time
  <sheet>_3x.gif        each animation at game scale, at its intended timings
  <sheet>_6x.png        each sheet's frames at 6x, for looking closely
  game_scale_3x.png     every frame at 3x on the arena mat, beside the player and a funko
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

DEFAULT_OUT = os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\jordan_v2anims')
BG = (46, 49, 58, 255)
DARK = (18, 19, 24, 255)


def sheets():
    """[(name, module)] in fight order; each module has NAME, TIMES, LOOP and frames()."""
    import janim_idle
    mods = [janim_idle]
    for m in ('janim_summon', 'janim_taunt', 'janim_hit', 'janim_defeat'):
        try:
            mods.append(__import__(m))
        except ImportError:
            pass
    return [(m.NAME, m) for m in mods]


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def frame_images(mod):
    return [B.to_image(px) for px, _fx in mod.frames()]


def contact(mods, s=4, pad=8, label_h=16):
    rows = [(m.NAME, frame_images(m), m.TIMES, m.LOOP) for _n, m in mods]
    wmax = max(len(f) for _n, f, _t, _l in rows)
    cw, ch = 96 * s, 96 * s
    out = Image.new('RGBA', (pad + wmax * (cw + pad), len(rows) * (ch + label_h + pad) + pad), DARK)
    d = ImageDraw.Draw(out)
    y = pad
    for name, fr, times, loop in rows:
        for i, im in enumerate(fr):
            x = pad + i * (cw + pad)
            t = times[min(i, len(times) - 1)]
            d.text((x + 2, y + 2), '%s  f%d  %.2fs%s' % (name, i, t, '  loop' if loop and i == 0 else ''),
                   fill=(225, 225, 232, 255))
            out.alpha_composite(up(on_bg(im), s), (x, y + label_h))
        y += ch + label_h + pad
    return out


def gif(mod, path, s=3, hold_end=0.6):
    fr = frame_images(mod)
    times = mod.TIMES
    ims, durs = [], []
    for i, im in enumerate(fr):
        ims.append(up(on_bg(im), s).convert('RGB'))
        durs.append(int(round(1000 * times[min(i, len(times) - 1)])))
    if not mod.LOOP:
        durs[-1] += int(hold_end * 1000)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=1,
                optimize=False)


def closeup(mod, path, s=6):
    fr = frame_images(mod)
    out = Image.new('RGBA', (len(fr) * (96 * s + 8), 96 * s), DARK)
    for i, im in enumerate(fr):
        out.alpha_composite(up(on_bg(im), s), (i * (96 * s + 8), 0))
    out.save(path)


def game_scale(mods, path):
    """Every frame at the game's 3x on the arena mat, the player and a funko beside the first."""
    root = B.ROOT
    mat = Image.open(os.path.join(root, 'Assets', 'Environment', 'arena_mat.png')).convert('RGBA')
    player = Image.open(os.path.join(root, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
                        ).convert('RGBA').crop((0, 64, 32, 96))
    funko = Image.open(os.path.join(root, 'Assets', 'Characters', 'Jordan', 'Funkos', 'funko_plumber.png')
                       ).convert('RGBA').crop((24, 0, 48, 24))
    tiles = []
    for _n, m in mods:
        fr = frame_images(m)
        w = 96 * len(fr) + 70
        scene = Image.new('RGBA', (w, 100), (0, 0, 0, 255))
        for x in range(0, w, 200):
            scene.alpha_composite(mat.crop((140, 70, 340, 170)), (x, 0))
        for i, im in enumerate(fr):
            scene.alpha_composite(im, (96 * i, 100 - 96 - 2))
        scene.alpha_composite(funko, (96 * len(fr) + 4, 100 - 24 - 2))
        scene.alpha_composite(player, (96 * len(fr) + 34, 100 - 32 - 2))
        tiles.append(up(scene, 3))
    wmax = max(t.width for t in tiles)
    out = Image.new('RGBA', (wmax, sum(t.height + 6 for t in tiles)), DARK)
    y = 0
    for t in tiles:
        out.alpha_composite(t, (0, y))
        y += t.height + 6
    out.save(path)


def main(argv):
    out = os.path.abspath(argv[0]) if argv else DEFAULT_OUT
    os.makedirs(out, exist_ok=True)
    mods = sheets()
    if len(argv) > 1:
        mods = [(n, m) for n, m in mods if n in argv[1:]]
    contact(mods).save(os.path.join(out, 'contact_4x.png'))
    for name, m in mods:
        gif(m, os.path.join(out, name + '_3x.gif'))
        closeup(m, os.path.join(out, name + '_6x.png'))
    game_scale(mods, os.path.join(out, 'game_scale_3x.png'))
    print('previews in', out)


if __name__ == '__main__':
    main(sys.argv[1:])
