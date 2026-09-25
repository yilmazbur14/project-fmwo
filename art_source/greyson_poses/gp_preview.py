"""Previews of Greyson's pose sheets, written ONLY to the scratch folder (gp_base.SCRATCH):

    python -B gp_preview.py

    <sheet>_4x.png            each sheet's strip at 4x, frames labelled
    greyson_pose_a.gif ...    each pose's strike then its hold, at the plan's clock (0.3 s strike,
                              1.2 s hold: f1 f2 f1 at 0.4 s), 3x
    greyson_pose_hit.gif      knocked, then the annoyed hold, 3x
    greyson_spirit.gif        arm up, the hold, the grin, the throw (the gather shortened), 3x
    greyson_poses_cycle.gif   the whole posing cycle, A B C A B C, 3x
    greyson_poses_game_scale.png   every frame at 3x on the arena mat beside the player
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_base as G  # noqa: E402
import gp_fig as P  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

K = G.K
OUT = G.SCRATCH
BG = (46, 49, 58, 255)
MAT = os.path.join(G.B.ROOT, 'Assets', 'Environment', 'arena_mat.png')
PLAYER = os.path.join(G.B.ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')


def frames(name):
    return [(label, cv.image(), anc) for label, cv, anc in P.build_sheet(name)]


def up(im, s, bg=BG):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im)
    return b.resize((im.width * s, im.height * s), Image.NEAREST)


def labelled_strip(name, s=4):
    fr = frames(name)
    w = 112 * s
    out = Image.new('RGBA', (w * len(fr) + 6 * (len(fr) - 1), 112 * s + 22), (18, 18, 24, 255))
    d = ImageDraw.Draw(out)
    for i, (label, im, anc) in enumerate(fr):
        x = i * (w + 6)
        out.paste(up(im, s), (x, 22))
        d.text((x + 3, 5), '%s  f%d %s   muzzle %s  crown %s' % (name, i, label, anc['muzzle'], anc['crown']),
               fill=(230, 230, 236, 255))
    return out


def gif(ims, durations, path, s=3):
    pal = [up(im, s).convert('P', palette=Image.ADAPTIVE, colors=255) for im in ims]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations, loop=0, disposal=2)


def main():
    os.makedirs(OUT, exist_ok=True)
    written = []
    for name in P.SHEETS:
        p = os.path.join(OUT, name + '_4x.png')
        labelled_strip(name).save(p)
        written.append(p)
    # each pose: the strike, then the hold's breathing (f1 f2 f1), looping
    for name in ('greyson_pose_a', 'greyson_pose_b', 'greyson_pose_c'):
        ims = [im for _, im, _ in frames(name)]
        p = os.path.join(OUT, name + '.gif')
        gif([ims[0], ims[1], ims[2], ims[1]], [300, 400, 400, 400], p)
        written.append(p)
    hit = [im for _, im, _ in frames('greyson_pose_hit')]
    p = os.path.join(OUT, 'greyson_pose_hit.gif')
    gif(hit, [120, 1100], p)
    written.append(p)
    sp = [im for _, im, _ in frames('greyson_spirit')]
    p = os.path.join(OUT, 'greyson_spirit.gif')
    gif(sp, [500, 1500, 500, 900], p)
    written.append(p)
    # the whole posing cycle: A B C A B C at the plan's clock
    seq, dur = [], []
    for name in ('greyson_pose_a', 'greyson_pose_b', 'greyson_pose_c') * 2:
        ims = [im for _, im, _ in frames(name)]
        seq += [ims[0], ims[1], ims[2], ims[1]]
        dur += [300, 400, 400, 400]
    p = os.path.join(OUT, 'greyson_poses_cycle.gif')
    gif(seq, dur, p, s=2)
    written.append(p)
    # game scale: every frame at 3x on the mat, the player (32 px at 3x) standing by for scale
    mat = Image.open(MAT).convert('RGBA')
    player = Image.open(PLAYER).convert('RGBA').crop((0, 0, 32, 32))
    allf = [im for name in P.SHEETS for _, im, _ in frames(name)]
    cols = 8
    rows = (len(allf) + cols - 1) // cols
    cw, ch = 130, 124
    board = Image.new('RGBA', (cw * cols, ch * rows))
    for ty in range(0, board.height, mat.height):
        for tx in range(0, board.width, mat.width):
            board.paste(mat, (tx, ty))
    for i, im in enumerate(allf):
        x, y = (i % cols) * cw, (i // cols) * ch
        board.alpha_composite(im, (x + 2, y + 8))
        if i % cols == 0:
            board.alpha_composite(player, (x + 100, y + 8 + 111 - 28))
    big = board.resize((board.width * 3 // 2, board.height * 3 // 2), Image.NEAREST)
    p = os.path.join(OUT, 'greyson_poses_game_scale.png')
    board.resize((board.width * 3, board.height * 3), Image.NEAREST).save(p)
    written.append(p)
    for p in written:
        print(p)


if __name__ == '__main__':
    main()
